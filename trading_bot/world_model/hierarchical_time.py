import torch
import torch.nn as nn
from typing import Dict, List, Optional, Tuple

class TemporalBlock(nn.Module):
    def __init__(self, latent_dim: int, hidden_dim: int, horizon_name: str):
        super().__init__()
        self.horizon_name = horizon_name
        self.gru = nn.GRU(latent_dim, hidden_dim, batch_first=True)
        self.output = nn.Linear(hidden_dim, latent_dim)

    def forward(self, x: torch.Tensor, h: Optional[torch.Tensor] = None) -> Tuple[torch.Tensor, torch.Tensor]:
        # x: [B, Seq, Dim]
        out, h = self.gru(x, h)
        return self.output(out[:, -1, :]), h

class HierarchicalTimeModel(nn.Module):
    """
    Hierarchical Time Model:
    Fast (ms) -> Medium (min) -> Slow (hours) -> Macro (days) -> Structural (regimes)
    """
    def __init__(self, latent_dim: int = 64, hidden_dim: int = 128):
        super().__init__()
        self.fast = TemporalBlock(latent_dim, hidden_dim, "fast")
        self.medium = TemporalBlock(latent_dim, hidden_dim, "medium")
        self.slow = TemporalBlock(latent_dim, hidden_dim, "slow")
        self.macro = TemporalBlock(latent_dim, hidden_dim, "macro")
        self.structural = TemporalBlock(latent_dim, hidden_dim, "structural")

    def forward(self, x: torch.Tensor, states: Optional[Dict[str, torch.Tensor]] = None) -> Tuple[Dict[str, torch.Tensor], Dict[str, torch.Tensor]]:
        states = states or {}
        outputs = {}
        new_states = {}

        # In a real implementation, we would downsample or aggregate sequences for higher layers
        # Here we show the structure
        outputs["fast"], new_states["fast"] = self.fast(x, states.get("fast"))
        outputs["medium"], new_states["medium"] = self.medium(x, states.get("medium"))
        outputs["slow"], new_states["slow"] = self.slow(x, states.get("slow"))
        outputs["macro"], new_states["macro"] = self.macro(x, states.get("macro"))
        outputs["structural"], new_states["structural"] = self.structural(x, states.get("structural"))

        return outputs, new_states
