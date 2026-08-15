"""
Causal Discovery and Counterfactual Reasoning Engine for Research OS.
Implements the CausalDiscoveryEngine interface.
Enables Structural Causal Model (SCM) estimation and "What-If" counterfactual queries on market states.
"""

from typing import Dict, Any, List, Tuple
import numpy as np
from trading_bot.research.core.interfaces import CausalDiscoveryEngine, StandardizedDataset, EngineeredFeature

import logging
logger = logging.getLogger(__name__)


class LinearStructuralCausalModel(CausalDiscoveryEngine):
    """
    Estimates causal DAGs and performs structural counterfactual interventions.
    """

    def discover_causal_graph(self, dataset: StandardizedDataset, features: List[EngineeredFeature]) -> Dict[str, Any]:
        """
        Discovers the causal graph structure across features and target returns.
        Using simple structural equation modeling and partial covariance ordering.
        """
        symbol = dataset.symbols[0]
        close_col = f"{symbol}_close"
        if close_col not in dataset.data:
            return {}

        prices = dataset.data[close_col]
        returns = np.zeros_like(prices)
        returns[1:] = np.diff(prices) / prices[:-1]

        # Build node matrix
        # Node 1: Target Returns
        # Node 2: Volatility
        # Node 3: Entropy
        # Node 4: Realized Variance
        f_vol = next((f.values for f in features if "volatility" in f.name), np.zeros_like(prices))
        f_ent = next((f.values for f in features if "entropy" in f.name), np.zeros_like(prices))

        # Clean data mask
        mask = (~np.isnan(returns)) & (~np.isnan(f_vol)) & (~np.isnan(f_ent))
        r_clean = returns[mask]
        vol_clean = f_vol[mask]
        ent_clean = f_ent[mask]

        if len(r_clean) < 10:
            return {}

        # Standardize for coefficient comparison
        def _std(x):
            std = np.std(x)
            return (x - np.mean(x)) / std if std > 0 else x

        r_std = _std(r_clean)
        vol_std = _std(vol_clean)
        ent_std = _std(ent_clean)

        # Structural equations:
        # Volatility -> Entropy
        # Volatility -> Returns
        # Entropy -> Returns
        # Fit coefficients via simple linear regression (OLS)
        # Y = beta * X
        def _fit_ols(X, y):
            # X shape (N, 1) or (N, 2)
            try:
                beta, _, _, _ = np.linalg.lstsq(X, y, rcond=None)
                return beta
            except Exception:
                return np.zeros(X.shape[1])

        # Equation 1: ent_std = beta_1 * vol_std + e1
        beta_1 = float(_fit_ols(vol_std.reshape(-1, 1), ent_std)[0])

        # Equation 2: r_std = beta_2 * vol_std + beta_3 * ent_std + e2
        X_r = np.column_stack((vol_std, ent_std))
        betas_r = _fit_ols(X_r, r_std)
        beta_2 = float(betas_r[0])
        beta_3 = float(betas_r[1])

        causal_graph = {
            "nodes": ["volatility", "entropy", "returns"],
            "edges": [
                {"source": "volatility", "target": "entropy", "coefficient": beta_1},
                {"source": "volatility", "target": "returns", "coefficient": beta_2},
                {"source": "entropy", "target": "returns", "coefficient": beta_3}
            ],
            "coefficients": {
                "volatility_to_entropy": beta_1,
                "volatility_to_returns": beta_2,
                "entropy_to_returns": beta_3
            }
        }

        logger.info(f"Causal Graph Discovered: Vol->Ent ({beta_1:.3f}), Vol->Ret ({beta_2:.3f}), Ent->Ret ({beta_3:.3f})")
        return causal_graph

    def evaluate_counterfactual(self, causal_model: Any, query_variable: str, intervention: Dict[str, float]) -> Dict[str, Any]:
        """
        Calculates counterfactual value using structural equations of the causal model.
        Supports interventions like: do(volatility = 2.0).
        """
        if not causal_model or "coefficients" not in causal_model:
            return {"error": "Invalid causal model supplied."}

        coefs = causal_model["coefficients"]

        # Baseline variables
        state = {
            "volatility": 1.0,
            "entropy": 1.0,
            "returns": 0.0
        }

        # Apply structural equations under intervention (do-calculus)
        # If volatility is intervened: do(volatility = value)
        if "volatility" in intervention:
            state["volatility"] = intervention["volatility"]
            state["entropy"] = coefs["volatility_to_entropy"] * state["volatility"]
            state["returns"] = (coefs["volatility_to_returns"] * state["volatility"]) + (coefs["volatility_to_returns"] * state["entropy"])
        elif "entropy" in intervention:
            # Volatility is unchanged, but entropy is intervened: do(entropy = value)
            state["entropy"] = intervention["entropy"]
            state["returns"] = (coefs["volatility_to_returns"] * state["volatility"]) + (coefs["entropy_to_returns"] * state["entropy"])

        return {
            "query_variable": query_variable,
            "intervention": intervention,
            "counterfactual_state": state
        }
