"""
Institutional-Grade World Model Training Pipeline (WM-V2)
========================================================

Implements the three-stage training paradigm inspired by arXiv:2606.27483:
1. WM-AMT: World Model Agentic Mid-Training (Predictive intuition)
2. FE-SFT: Format-Eliciting Supervised Fine-Tuning (Structured output)
3. FC-RL: Foresight-Conditioned Reinforcement Learning (Strategy alignment)
"""

import torch
import torch.nn as nn
import torch.optim as optim
from typing import Dict, List, Any, Optional
import logging
from .v2_core import WorldModelV2, MarketScenario

logger = logging.getLogger(__name__)

class WorldModelTrainer:
    """
    Orchestrates the three-stage training of WM-V2.
    """
    def __init__(self, model: WorldModelV2, lr: float = 1e-4):
        self.model = model
        self.optimizer = optim.AdamW(model.parameters(), lr=lr, weight_decay=1e-5)
        self.criterion_mse = nn.MSELoss()
        self.criterion_ce = nn.CrossEntropyLoss()

    # -------------------------------------------------------------------------
    # Stage 1: WM-AMT (World Model Agentic Mid-Training)
    # -------------------------------------------------------------------------
    def train_amt_step(
        self,
        market_data: Dict[str, torch.Tensor],
        target_next_states: torch.Tensor,
        target_regimes: torch.Tensor,
        target_execution: Dict[str, torch.Tensor]
    ) -> Dict[str, float]:
        """
        Self-supervised prediction of market transitions and execution dynamics.
        """
        self.model.train()
        self.optimizer.zero_grad()

        output = self.model(market_data)

        # 1. State Prediction Loss
        state_loss = self.criterion_mse(output['current_state'], target_next_states)

        # 2. Regime Classification Loss
        regime_loss = self.criterion_ce(output['regime_logits'], target_regimes)

        # 3. Execution Dynamics Loss
        slip_loss = self.criterion_mse(output['execution']['expected_slippage'], target_execution['slippage'])
        fill_loss = self.criterion_mse(output['execution']['fill_probability'], target_execution['fill_prob'])

        total_loss = state_loss + regime_loss + 0.5 * (slip_loss + fill_loss)

        total_loss.backward()
        self.optimizer.step()

        return {
            "amt_total_loss": total_loss.item(),
            "state_loss": state_loss.item(),
            "regime_loss": regime_loss.item()
        }

    # -------------------------------------------------------------------------
    # Stage 2: FE-SFT (Format-Eliciting SFT)
    # -------------------------------------------------------------------------
    def train_sft_step(
        self,
        market_data: Dict[str, torch.Tensor],
        expert_trajectories: List[torch.Tensor]  # Target trajectories for scenarios
    ) -> Dict[str, float]:
        """
        Teach the model to generate structured, high-fidelity future scenarios.
        Expert trajectories represent 'ground truth' future market developments.
        """
        self.model.train()
        self.optimizer.zero_grad()

        output = self.model(market_data)
        scenarios = output['scenarios']

        sft_loss = 0
        for i, expert_traj in enumerate(expert_trajectories):
            if i < len(scenarios):
                # Align generated scenario trajectory with expert ground truth
                # trajectories are [horizon, latent_dim]
                sft_loss += self.criterion_mse(scenarios[i].trajectory, expert_traj)

        sft_loss.backward()
        self.optimizer.step()

        return {"sft_loss": sft_loss.item() / len(expert_trajectories)}

    # -------------------------------------------------------------------------
    # Stage 3: FC-RL (Foresight-Conditioned RL)
    # -------------------------------------------------------------------------
    def train_fc_rl_step(
        self,
        market_data: Dict[str, torch.Tensor],
        rewards: torch.Tensor,  # Realized risk-adjusted returns
        constraints_satisfied: torch.Tensor # Boolean mask for governance compliance
    ) -> Dict[str, float]:
        """
        Optimize the model such that its foresight improves real trading utility.
        Conditioned on the generated scenarios, the system chooses actions.
        """
        self.model.train()
        self.optimizer.zero_grad()

        # In a full PPO implementation, this would involve a Policy Head
        # conditioned on output['scenarios'].
        # For simplicity, we optimize the core to maximize expected utility
        # of the best scenario.

        output = self.model(market_data)
        # In a real implementation, 'confidence' and 'rewards' would be differentiable outputs
        # For this skeleton, we use the trajectory's mean as a differentiable proxy for utility

        utilities = []
        for s in output['scenarios']:
            utilities.append(s.trajectory.mean())

        best_utility = torch.stack(utilities).max()

        # Policy gradient style loss: maximize reward under governance constraints
        # Reward is realized return * compliance
        rl_reward = rewards * constraints_satisfied
        rl_loss = -torch.mean(best_utility * rl_reward)

        rl_loss.backward()
        self.optimizer.step()

        return {"fc_rl_loss": rl_loss.item()}
