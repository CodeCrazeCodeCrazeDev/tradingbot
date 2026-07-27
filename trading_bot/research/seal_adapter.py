"""
SEAL: Self-Adapting Alpha Loop Framework
=========================================
Based on the MIT paper: "Self-Adapting Language Models" (SEAL) (arXiv:2506.10943).

This module implements the SEAL framework for quantitative alpha strategies:
1. Inner Update Loop: Generates a Strategy Self-Edit Directive consisting of synthetic data
   augmentation configs, optimization hyperparameters (learning rate, L2 weight decay, epochs),
   and performs persistent numerical/weight updates on the strategy parameter coefficients.
2. Outer RL Loop: Uses downstream task performance (out-of-sample Sharpe Ratio improvement)
   as the reward signal to optimize the policy that generates the Self-Edit Directives.
"""

import logging
import numpy as np
import pandas as pd
from typing import Dict, Any, List, Optional, Tuple, Callable
from dataclasses import dataclass, field

logger = logging.getLogger("AlphaAlgo.SEAL")

@dataclass
class SEALSelfEdit:
    """
    Strategy Self-Edit Directive (corresponds to LLM Self-Edit under the SEAL paper).
    Specifies how the strategy should restructure its training data, select its own tuning hyperparameters,
    and update its active parameter coefficients.
    """
    id: str
    synthetic_noise_std: float = 0.05
    synthetic_imbalance_scale: float = 1.0
    learning_rate: float = 0.01
    epochs: int = 5
    l2_regularization: float = 0.1
    adapted_weights: np.ndarray = field(default_factory=lambda: np.array([]))


class SEALInnerLoop:
    """
    Inner Adaptation Loop (Supervised Fine-Tuning analogue).
    Applies the self-generated data augmentation, configures the optimization,
    and executes persistent updates on the model parameter weights.
    """

    @staticmethod
    def generate_synthetic_data(train_returns: pd.Series, self_edit: SEALSelfEdit) -> pd.Series:
        """Generates synthetic fine-tuning dataset using self-edit augmentation directives."""
        # Restructure information with self-directed noise and scale modifications
        noise = np.random.normal(0, self_edit.synthetic_noise_std, size=len(train_returns))
        augmented_returns = (train_returns * self_edit.synthetic_imbalance_scale) + noise
        return pd.Series(augmented_returns, index=train_returns.index)

    @staticmethod
    def execute_persistent_update(base_weights: np.ndarray, train_returns: pd.Series,
                                  self_edit: SEALSelfEdit) -> np.ndarray:
        """
        Executes gradient-based/numerical SFT updates directly on strategy weight parameters.
        Adjusts weights to maximize returns adjusted for L2 regularization.
        """
        adapted = base_weights.copy()
        synthetic_data = SEALInnerLoop.generate_synthetic_data(train_returns, self_edit)

        # Mean return of the synthetic playbacks
        mean_ret = float(synthetic_data.mean())

        # Simple gradient ascent update rule with L2 regularization penalty
        # Target: maximize weights' alignment with mean_ret, penalized by L2 norm
        for _ in range(self_edit.epochs):
            # Gradient of: weights * mean_ret - 0.5 * l2 * sum(weights^2)
            gradient = mean_ret * np.ones_like(adapted) - self_edit.l2_regularization * adapted
            # Apply update directive
            adapted += self_edit.learning_rate * gradient

        return adapted


class SEALOuterLoop:
    """
    Outer Reinforcement Learning Loop.
    Learns to produce high-performing Self-Edit Directives by using downstream adapted-model
    OOS performance as the reward signal to update the policy parameters.
    """

    def __init__(self, action_dim: int = 5, learning_rate: float = 0.05) -> None:
        self.action_dim = action_dim
        self.lr = learning_rate
        # Policy parameters (mean values for generating self-edits: noise_std, imbalance, lr, epochs, l2_reg)
        self.policy_means = np.array([0.05, 1.0, 0.01, 5.0, 0.1])
        # Exploration standard deviations
        self.policy_stds = np.array([0.01, 0.1, 0.002, 1.0, 0.02])

    def sample_self_edit(self, edit_id: str) -> SEALSelfEdit:
        """Samples a candidate Self-Edit Directive from the current policy distribution (exploration)."""
        samples = np.random.normal(self.policy_means, self.policy_stds)
        # Enforce positive bounds on hyperparameters
        noise_std = max(samples[0], 0.005)
        imbalance = max(samples[1], 0.1)
        lr = max(samples[2], 0.0001)
        epochs = max(int(round(samples[3])), 1)
        l2_reg = max(samples[4], 0.001)

        return SEALSelfEdit(
            id=edit_id,
            synthetic_noise_std=noise_std,
            synthetic_imbalance_scale=imbalance,
            learning_rate=lr,
            epochs=epochs,
            l2_regularization=l2_reg
        )

    def evaluate_downstream_performance(self, adapted_weights: np.ndarray, oos_returns: pd.Series) -> float:
        """
        Downstream task evaluator (Downstream utility function).
        Computes Sharpe Ratio of adapted strategy on out-of-sample data.
        """
        # Strategy returns = weights * oos_returns
        strategy_rets = oos_returns * adapted_weights.mean()
        mean_ret = strategy_rets.mean()
        std_ret = strategy_rets.std()
        if std_ret == 0:
            return 0.0
        # Annualized Sharpe Ratio
        return float((mean_ret / std_ret) * np.sqrt(252))

    def update_policy(self, sampled_edits: List[SEALSelfEdit], rewards: List[float]) -> None:
        """
        Policy Gradient (REINFORCE) update.
        Adjusts the policy means to favor parameters that yielded higher downstream rewards.
        """
        if not sampled_edits or not rewards:
            return

        rewards_arr = np.array(rewards)
        # Standardize rewards (baselining)
        mean_r = rewards_arr.mean()
        std_r = rewards_arr.std()
        if std_r > 0:
            norm_rewards = (rewards_arr - mean_r) / std_r
        else:
            norm_rewards = rewards_arr - mean_r

        # REINFORCE update step
        for edit, reward in zip(sampled_edits, norm_rewards):
            # Reconstruct sample vector
            sample_vec = np.array([
                edit.synthetic_noise_std,
                edit.synthetic_imbalance_scale,
                edit.learning_rate,
                float(edit.epochs),
                edit.l2_regularization
            ])
            # Gradient of log Gaussian probability wrt mean: (sample - mean) / std^2
            gradient = (sample_vec - self.policy_means) / (self.policy_stds ** 2 + 1e-8)
            # Update policy parameters
            self.policy_means += self.lr * reward * gradient

        # Ensure parameters remain positive
        self.policy_means = np.clip(self.policy_means, [0.001, 0.01, 0.0001, 1.0, 0.001], [1.0, 10.0, 1.0, 100.0, 10.0])
        logger.info(f"SEAL: Policy updated. New means: {self.policy_means}")


class SEALSystem:
    """
    Authoritative SEAL Redesign Engine.
    Runs the dual inner/outer loops to persistently self-adapt alpha weight parameters.
    """

    def __init__(self, action_dim: int = 5) -> None:
        self.outer_loop = SEALOuterLoop(action_dim=action_dim)

    def self_adapt_alpha(self, base_weights: np.ndarray, train_returns: pd.Series,
                         oos_returns: pd.Series, num_iterations: int = 10) -> Tuple[np.ndarray, SEALSelfEdit]:
        """
        Runs the full SEAL adaptation protocol over multiple reinforcement learning trials.
        Selects the best self-adapted weights and updates the adaptation policy.
        """
        best_weights = base_weights.copy()
        best_edit = None
        best_reward = -float("inf")

        for iteration in range(num_iterations):
            sampled_edits = []
            rewards = []

            # Sample batch of candidate self-edits (exploration)
            for b in range(5):
                edit = self.outer_loop.sample_self_edit(f"se_{iteration}_{b}")

                # Inner SFT-style persistent update loop
                adapted_w = SEALInnerLoop.execute_persistent_update(base_weights, train_returns, edit)
                edit.adapted_weights = adapted_w

                # Downstream evaluation on out-of-sample task
                reward = self.outer_loop.evaluate_downstream_performance(adapted_w, oos_returns)

                sampled_edits.append(edit)
                rewards.append(reward)

                if reward > best_reward:
                    best_reward = reward
                    best_weights = adapted_w
                    best_edit = edit

            # Outer RL update loop: Train policy to generate better updates
            self.outer_loop.update_policy(sampled_edits, rewards)

        logger.info(f"SEAL: Self-adaptation complete. Downstream reward: {best_reward:.4f}")
        return best_weights, best_edit
