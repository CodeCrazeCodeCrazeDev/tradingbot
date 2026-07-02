import torch
import torch.nn as nn
from typing import Dict, List, Optional, Tuple

class FastRSSMModel(nn.Module):
    def __init__(self, latent_dim: int = 64, hidden_dim: int = 128, action_dim: int = 5):
        super().__init__()
        self.rnn = nn.GRU(latent_dim + action_dim, hidden_dim, num_layers=2, batch_first=True)
        self.prior = nn.Linear(hidden_dim, latent_dim * 2)
    def forward(self, latent: torch.Tensor, action: torch.Tensor, h: Optional[torch.Tensor] = None) -> Tuple[torch.Tensor, torch.Tensor, torch.Tensor]:
        x = torch.cat([latent, action], dim=-1).unsqueeze(1)
        out, h = self.rnn(x, h)
        mu, logvar = torch.chunk(self.prior(out[:, -1]), 2, dim=-1)
        return mu, logvar, h

class EnsembleWorldModel(nn.Module):
    def __init__(self, n_models: int = 5, latent_dim: int = 64, hidden_dim: int = 128, action_dim: int = 5):
        super().__init__()
        self.models = nn.ModuleList([FastRSSMModel(latent_dim, hidden_dim, action_dim) for _ in range(n_models)])
    def forward(self, latent: torch.Tensor, action: torch.Tensor, hiddens: Optional[List[torch.Tensor]] = None) -> Tuple[torch.Tensor, torch.Tensor, List[torch.Tensor], torch.Tensor]:
        preds, logvars, new_h = [], [], []
        for i, m in enumerate(self.models):
            mu, lv, h = m(latent, action, hiddens[i] if hiddens else None)
            preds.append(mu); logvars.append(lv); new_h.append(h)
        preds = torch.stack(preds)
        return preds.mean(0), torch.stack(logvars).mean(0), new_h, preds.var(0).mean(-1)
