import torch
import torch.nn as nn

class DiscoLoopCell(nn.Module):
    """
    DiscoLoop: Looping Discrete Embeddings and Continuous Hidden States.
    """
    def __init__(self, transformer_layer, embedding_layer, projection, vocab_size):
        super().__init__()
        self.layer = transformer_layer
        self.embedding = embedding_layer
        self.projection = projection
        self.output_layer = nn.Linear(transformer_layer.d_model if hasattr(transformer_layer, 'd_model') else 512, vocab_size)

    def forward(self, h, e):
        """
        Args:
            h: Continuous hidden state (B, T, D).
            e: Discrete embedding (B, T, D).
        """
        # Input to layer is fusion of continuous and discrete channels
        x = h + self.projection(e)

        # Transformer forward pass
        h_next = self.layer(x)

        # Extract next discrete representation (e.g., via argmax and embedding)
        logits = self.to_logits(h_next)
        tokens = torch.argmax(logits, dim=-1)
        e_next = self.embedding(tokens).detach() # Discrete channel

        return h_next, e_next

    def to_logits(self, h):
        return self.output_layer(h)
