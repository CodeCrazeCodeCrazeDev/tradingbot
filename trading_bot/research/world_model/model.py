"""
World Model Subsystem for Research OS.
Learns latent market structures, hidden regime states, volatility clustering, and transition matrices.
"""

from typing import Dict, Any, List
import numpy as np
import logging
from trading_bot.research.core.interfaces import WorldModel, StandardizedDataset

logger = logging.getLogger(__name__)


class MarkovRegimeSwitchingWorldModel(WorldModel):
    """
    Learns and predicts latent market regimes using a statistical hidden state model.
    Models volatility clustering and regime transition probability matrices.
    """

    def predict_latent_states(self, dataset: StandardizedDataset) -> Dict[str, np.ndarray]:
        symbol = dataset.symbols[0]
        close_col = f"{symbol}_close"
        if close_col not in dataset.data:
            return {}

        prices = dataset.data[close_col]
        returns = np.zeros_like(prices)
        returns[1:] = np.diff(prices) / prices[:-1]

        # Simple rolling standard deviation to identify high/medium/low volatility states
        window = 15
        rolling_vols = np.zeros_like(prices)
        for i in range(window, len(prices)):
            rolling_vols[i] = np.std(returns[i-window:i])

        # Classify states:
        # State 0: Low Volatility (stationary, mean-reverting)
        # State 1: Medium Volatility (normal random walk)
        # State 2: High Volatility (breakout, momentum, clustering)
        v_clean = rolling_vols[window:]
        if len(v_clean) < 10:
            latent_states = np.zeros_like(prices, dtype=int)
            transition_matrix = np.eye(3)
        else:
            q33, q66 = np.percentile(v_clean, [33.3, 66.6])

            latent_states = np.zeros_like(prices, dtype=int)
            for i in range(len(prices)):
                v = rolling_vols[i]
                if v <= q33:
                    latent_states[i] = 0
                elif v <= q66:
                    latent_states[i] = 1
                else:
                    latent_states[i] = 2

            # 2. Learn Empirical Transition Probability Matrix
            # T_ij = count(State_t == i and State_{t+1} == j) / count(State_t == i)
            transition_matrix = np.zeros((3, 3))
            for t in range(len(latent_states) - 1):
                i = latent_states[t]
                j = latent_states[t+1]
                transition_matrix[i, j] += 1.0

            for i in range(3):
                row_sum = np.sum(transition_matrix[i, :])
                if row_sum > 0:
                    transition_matrix[i, :] /= row_sum
                else:
                    transition_matrix[i, i] = 1.0

        logger.info(f"World Model State Transition probabilities learned: \n{transition_matrix}")

        return {
            "latent_states": latent_states,
            "transition_matrix": transition_matrix,
            "rolling_volatility": rolling_vols
        }
