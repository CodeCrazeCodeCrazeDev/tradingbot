"""
Informer: Beyond Efficient Transformer for Long Sequence Time-Series Forecasting

Based on: "Informer: Beyond Efficient Transformer for Long Sequence Time-Series Forecasting" (AAAI 2021)
arXiv: https://arxiv.org/abs/2012.07436

Key innovations:
- ProbSparse self-attention mechanism (O(L log L) complexity)
- Self-attention distilling for handling long sequences
- Generative style decoder for long-horizon forecasting
"""

try:
    import torch
except ImportError:
    torch = None
import torch.nn as nn
import torch.nn.functional as F
import numpy as np
from typing import Optional, Tuple
import math
import logging
import numpy

logger = logging.getLogger(__name__)


class ProbAttention(nn.Module):
    """
    ProbSparse Self-Attention Mechanism
    
    Reduces complexity from O(L^2) to O(L log L) by selecting top-u queries
    based on their sparsity measurement.
    """
    
    def __init__(
        self,
        mask_flag: bool = True,
        factor: int = 5,
        scale: Optional[float] = None,
        attention_dropout: float = 0.1
    ):
        super().__init__()
        self.factor = factor
        self.scale = scale
        self.mask_flag = mask_flag
        self.dropout = nn.Dropout(attention_dropout)
    
    def _prob_QK(self, Q, K, sample_k, n_top):
        """
        Calculate sparsity measurement M for queries
        
        Args:
            Q: Queries [B, H, L, D]
            K: Keys [B, H, S, D]
            sample_k: Number of keys to sample
            n_top: Number of top queries to select
            
        Returns:
            Q_reduce: Top queries
            M_top: Top query indices
        """
        B, H, L_Q, D = Q.shape
        _, _, L_K, _ = K.shape
        
        # Sample keys
        K_expand = K.unsqueeze(-3).expand(B, H, L_Q, L_K, D)
        index_sample = torch.randint(L_K, (L_Q, sample_k))
        K_sample = K_expand[:, :, torch.arange(L_Q).unsqueeze(1), index_sample, :]
        
        # Calculate Q_K^T
        Q_K_sample = torch.matmul(Q.unsqueeze(-2), K_sample.transpose(-2, -1)).squeeze(-2)
        
        # Find top-u queries with highest sparsity measurement
        M = Q_K_sample.max(-1)[0] - torch.div(Q_K_sample.sum(-1), L_K)
        M_top = M.topk(n_top, sorted=False)[1]
        
        # Reduce Q to top queries
        Q_reduce = Q[torch.arange(B)[:, None, None],
                     torch.arange(H)[None, :, None],
                     M_top, :]
        
        return Q_reduce, M_top
    
    def _get_initial_context(self, V, L_Q):
        """Get initial context for non-top queries"""
        B, H, L_V, D = V.shape
        
        if not self.mask_flag:
            # Mean pooling
            V_sum = V.mean(dim=-2)
            context = V_sum.unsqueeze(-2).expand(B, H, L_Q, V_sum.shape[-1]).clone()
        else:
            # Cumulative mean for causal masking
            assert L_Q == L_V
            context = V.cumsum(dim=-2)
        
        return context
    
    def _update_context(self, context_in, V, scores, index, L_Q):
        """Update context with attention from top queries"""
        B, H, L_V, D = V.shape
        
        if self.mask_flag:
            attn_mask = ProbMask(B, H, L_Q, index, scores, device=V.device)
            scores.masked_fill_(attn_mask.mask, -np.inf)
        
        attn = torch.softmax(scores, dim=-1)
        context_in[torch.arange(B)[:, None, None],
                   torch.arange(H)[None, :, None],
                   index, :] = torch.matmul(attn, V).type_as(context_in)
        
        return context_in
    
    def forward(self, queries, keys, values, attn_mask=None):
        """
        Forward pass
        
        Args:
            queries: [B, L_Q, H, D]
            keys: [B, L_K, H, D]
            values: [B, L_V, H, D]
            attn_mask: Attention mask
            
        Returns:
            Output and attention weights
        """
        B, L_Q, H, D = queries.shape
        _, L_K, _, _ = keys.shape
        
        queries = queries.transpose(2, 1)
        keys = keys.transpose(2, 1)
        values = values.transpose(2, 1)
        
        U_part = self.factor * np.ceil(np.log(L_K)).astype('int').item()
        u = self.factor * np.ceil(np.log(L_Q)).astype('int').item()
        
        U_part = U_part if U_part < L_K else L_K
        u = u if u < L_Q else L_Q
        
        scores_top, index = self._prob_QK(queries, keys, sample_k=U_part, n_top=u)
        
        # Add scale factor
        scale = self.scale or 1. / math.sqrt(D)
        if scale is not None:
            scores_top = scores_top * scale
        
        # Get context
        context = self._get_initial_context(values, L_Q)
        
        # Update context with top queries
        context = self._update_context(context, values, scores_top, index, L_Q)
        
        return context.transpose(2, 1).contiguous(), None


class ProbMask:
    """Masking for ProbSparse attention"""
    
    def __init__(self, B, H, L, index, scores, device="cpu"):
        _mask = torch.ones(L, scores.shape[-1], dtype=torch.bool).to(device).triu(1)
        _mask_ex = _mask[None, None, :].expand(B, H, L, scores.shape[-1])
        indicator = _mask_ex[torch.arange(B)[:, None, None],
                             torch.arange(H)[None, :, None],
                             index, :].to(device)
        self._mask = indicator.view(scores.shape).to(device)
    
    @property
    def mask(self):
        return self._mask


class AttentionLayer(nn.Module):
    """Attention layer wrapper"""
    
    def __init__(self, attention, d_model, n_heads, d_keys=None, d_values=None):
        super().__init__()
        
        d_keys = d_keys or (d_model // n_heads)
        d_values = d_values or (d_model // n_heads)
        
        self.inner_attention = attention
        self.query_projection = nn.Linear(d_model, d_keys * n_heads)
        self.key_projection = nn.Linear(d_model, d_keys * n_heads)
        self.value_projection = nn.Linear(d_model, d_values * n_heads)
        self.out_projection = nn.Linear(d_values * n_heads, d_model)
        self.n_heads = n_heads
    
    def forward(self, queries, keys, values, attn_mask=None):
        B, L, _ = queries.shape
        _, S, _ = keys.shape
        H = self.n_heads
        
        queries = self.query_projection(queries).view(B, L, H, -1)
        keys = self.key_projection(keys).view(B, S, H, -1)
        values = self.value_projection(values).view(B, S, H, -1)
        
        out, attn = self.inner_attention(queries, keys, values, attn_mask)
        out = out.view(B, L, -1)
        
        return self.out_projection(out), attn


class Distilling(nn.Module):
    """
    Distilling operation for reducing sequence length
    Uses 1D convolution with max pooling
    """
    
    def __init__(self, d_model):
        super().__init__()
        self.conv = nn.Conv1d(d_model, d_model, kernel_size=3, padding=1, padding_mode='circular')
        self.norm = nn.BatchNorm1d(d_model)
        self.activation = nn.ELU()
        self.maxpool = nn.MaxPool1d(kernel_size=3, stride=2, padding=1)
    
    def forward(self, x):
        x = self.conv(x.transpose(1, 2))
        x = self.norm(x)
        x = self.activation(x)
        x = self.maxpool(x)
        return x.transpose(1, 2)


class InformerEncoder(nn.Module):
    """Informer Encoder with distilling"""
    
    def __init__(
        self,
        attn_layers,
        conv_layers=None,
        norm_layer=None
    ):
        super().__init__()
        self.attn_layers = nn.ModuleList(attn_layers)
        self.conv_layers = nn.ModuleList(conv_layers) if conv_layers is not None else None
        self.norm = norm_layer
    
    def forward(self, x, attn_mask=None):
        attns = []
        
        if self.conv_layers is not None:
            for attn_layer, conv_layer in zip(self.attn_layers, self.conv_layers):
                x, attn = attn_layer(x, x, x, attn_mask=attn_mask)
                x = conv_layer(x)
                attns.append(attn)
            
            # Last attention layer without distilling
            x, attn = self.attn_layers[-1](x, x, x, attn_mask=attn_mask)
            attns.append(attn)
        else:
            for attn_layer in self.attn_layers:
                x, attn = attn_layer(x, x, x, attn_mask=attn_mask)
                attns.append(attn)
        
        if self.norm is not None:
            x = self.norm(x)
        
        return x, attns


class InformerDecoder(nn.Module):
    """Informer Decoder with generative inference"""
    
    def __init__(self, layers, norm_layer=None):
        super().__init__()
        self.layers = nn.ModuleList(layers)
        self.norm = norm_layer
    
    def forward(self, x, cross, x_mask=None, cross_mask=None):
        for layer in self.layers:
            x = layer(x, cross, x_mask=x_mask, cross_mask=cross_mask)
        
        if self.norm is not None:
            x = self.norm(x)
        
        return x


class InformerModel(nn.Module):
    """
    Complete Informer model for long-sequence forecasting
    
    Args:
        enc_in: Encoder input size
        dec_in: Decoder input size
        c_out: Output size
        seq_len: Input sequence length
        label_len: Start token length
        out_len: Prediction length
        factor: ProbSparse factor
        d_model: Model dimension
        n_heads: Number of attention heads
        e_layers: Number of encoder layers
        d_layers: Number of decoder layers
        d_ff: Feed-forward dimension
        dropout: Dropout rate
        attn: Attention type ('prob' or 'full')
        activation: Activation function
    """
    
    def __init__(
        self,
        enc_in: int,
        dec_in: int,
        c_out: int,
        seq_len: int = 96,
        label_len: int = 48,
        out_len: int = 24,
        factor: int = 5,
        d_model: int = 512,
        n_heads: int = 8,
        e_layers: int = 3,
        d_layers: int = 2,
        d_ff: int = 2048,
        dropout: float = 0.1,
        attn: str = 'prob',
        activation: str = 'gelu'
    ):
        super().__init__()
        self.pred_len = out_len
        self.label_len = label_len
        
        # Encoding
        self.enc_embedding = nn.Linear(enc_in, d_model)
        self.dec_embedding = nn.Linear(dec_in, d_model)
        
        # Attention
        Attn = ProbAttention if attn == 'prob' else nn.MultiheadAttention
        
        # Encoder
        self.encoder = InformerEncoder(
            [
                AttentionLayer(
                    Attn(False, factor, attention_dropout=dropout),
                    d_model, n_heads
                ) for _ in range(e_layers)
            ],
            [
                Distilling(d_model) for _ in range(e_layers - 1)
            ],
            norm_layer=nn.LayerNorm(d_model)
        )
        
        # Decoder
        self.decoder = InformerDecoder(
            [
                nn.TransformerDecoderLayer(
                    d_model, n_heads, d_ff, dropout,
                    activation=activation
                ) for _ in range(d_layers)
            ],
            norm_layer=nn.LayerNorm(d_model)
        )
        
        # Projection
        self.projection = nn.Linear(d_model, c_out, bias=True)
    
    def forward(
        self,
        x_enc: torch.Tensor,
        x_dec: torch.Tensor,
        enc_mask: Optional[torch.Tensor] = None,
        dec_mask: Optional[torch.Tensor] = None
    ) -> torch.Tensor:
        """
        Forward pass
        
        Args:
            x_enc: Encoder input [B, L, D]
            x_dec: Decoder input [B, L+pred_len, D]
            enc_mask: Encoder attention mask
            dec_mask: Decoder attention mask
            
        Returns:
            Predictions [B, pred_len, D]
        """
        # Encoding
        enc_out = self.enc_embedding(x_enc)
        enc_out, attns = self.encoder(enc_out, attn_mask=enc_mask)
        
        # Decoding
        dec_out = self.dec_embedding(x_dec)
        dec_out = self.decoder(dec_out, enc_out, x_mask=dec_mask, cross_mask=enc_mask)
        dec_out = self.projection(dec_out)
        
        return dec_out[:, -self.pred_len:, :]


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    # Test Informer model
    batch_size = 32
    seq_len = 96
    label_len = 48
    pred_len = 24
    enc_in = 7
    dec_in = 7
    c_out = 1
    
    model = InformerModel(
        enc_in=enc_in,
        dec_in=dec_in,
        c_out=c_out,
        seq_len=seq_len,
        label_len=label_len,
        out_len=pred_len,
        factor=5,
        d_model=512,
        n_heads=8,
        e_layers=2,
        d_layers=1,
        d_ff=2048,
        dropout=0.05,
        attn='prob',
        activation='gelu'
    )
    
    logger.info(f"Model parameters: {sum(p.numel() for p in model.parameters()):,}")
    
    # Test forward pass
    x_enc = torch.randn(batch_size, seq_len, enc_in)
    x_dec = torch.randn(batch_size, label_len + pred_len, dec_in)
    
    output = model(x_enc, x_dec)
    
    logger.info(f"Input shape: {x_enc.shape}")
    logger.info(f"Output shape: {output.shape}")
    logger.info(f"Expected shape: ({batch_size}, {pred_len}, {c_out})")
    
    assert output.shape == (batch_size, pred_len, c_out), "Output shape mismatch!"
    logger.info("\n✅ Informer model test passed!")
