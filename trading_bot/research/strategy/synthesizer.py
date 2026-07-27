"""
Strategy Synthesizer for Research OS.
Converts verified AlphaSignals and feature sets into fully executable and traceable ResearchStrategy packages.
"""

from typing import Dict, Any, List, Optional
import numpy as np
import uuid
from trading_bot.research.core.interfaces import ResearchStrategy, StandardizedDataset, AlphaSignal


class StandardResearchStrategy(ResearchStrategy):
    """
    Executable research strategy containing code logic, configuration parameters,
    and a complete lineage/manifest of the scientific process that generated it.
    """

    def __init__(
        self,
        strategy_id: str,
        name: str,
        alpha_signal: AlphaSignal,
        threshold: float = 1.0,
        metadata: Dict[str, Any] = None
    ):
        self._strategy_id = strategy_id
        self._name = name
        self.alpha_signal = alpha_signal
        self.threshold = threshold
        self.metadata = metadata or {}

    @property
    def strategy_id(self) -> str:
        return self._strategy_id

    @property
    def name(self) -> str:
        return self._name

    def generate_signals(self, dataset: StandardizedDataset) -> np.ndarray:
        """
        Executes strategy decision logic.
        Generates buy (1), sell (-1), or cash (0) trading triggers.
        """
        symbol = dataset.symbols[0]
        close_col = f"{symbol}_close"
        prices = dataset.data[close_col]

        # In a real environment, we would re-run the engineered features pipeline
        # and model inference. For direct research execution, we scale the alpha signal
        # to generate bounded position signals.
        signals = np.zeros_like(prices)

        # If the length of the new dataset matches the original alpha signal, we can use it.
        # Otherwise, we simulate a moving average cross or simple z-score triggers.
        if len(self.alpha_signal.values) == len(prices):
            alpha_values = self.alpha_signal.values
        else:
            # Fallback inline calculation if running on a new/extended dataset
            # Simulates signals based on basic momentum triggers
            returns = np.zeros_like(prices)
            returns[1:] = np.diff(prices) / prices[:-1]
            alpha_values = np.convolve(returns, np.ones(5)/5, mode='same') * 100

        # Z-score thresholds for signals
        mean = np.mean(alpha_values)
        std = np.std(alpha_values)
        if std > 0:
            z_scores = (alpha_values - mean) / std
            signals[z_scores > self.threshold] = 1   # Long buy
            signals[z_scores < -self.threshold] = -1  # Short sell

        return signals

    def get_lineage(self) -> Dict[str, Any]:
        """
        Full scientific lineage manifest. No strategy should run without this documentation.
        """
        return {
            "strategy_id": self._strategy_id,
            "name": self._name,
            "hypothesis_id": self.alpha_signal.hypothesis_id,
            "lineage_feature_ids": self.alpha_signal.lineage_feature_ids,
            "alpha_signal_id": self.alpha_signal.alpha_id,
            "statistical_evidence": self.alpha_signal.metrics,
            "config": {
                "threshold": self.threshold,
                "version": "1.0.0",
                "asset_class": "Forex",
                "target_symbols": [self.alpha_signal.alpha_id.split("_")[1].upper()]
            },
            "risk_profile": {
                "max_leverage": 10.0,
                "hedged": False,
                "volatility_target": 0.15
            }
        }


class StrategySynthesizer:
    """
    Orchestrates the translation of AlphaSignals into StandardResearchStrategy containers.
    """

    def synthesize_strategy(self, alpha_signal: AlphaSignal, name_suffix: str = "Regime_Alpha") -> StandardResearchStrategy:
        strategy_id = f"strat_{uuid.uuid4().hex[:8]}"
        symbol = alpha_signal.alpha_id.split("_")[1].upper()
        strategy_name = f"{symbol}_{name_suffix}"

        # Optimize threshold based on signal variance or baseline values
        threshold = 1.0  # default 1.0 standard dev triggers

        return StandardResearchStrategy(
            strategy_id=strategy_id,
            name=strategy_name,
            alpha_signal=alpha_signal,
            threshold=threshold,
            metadata={
                "synthesized_at": datetime_to_iso(None),
                "author": "StrategySynthesizerV1",
                "framework_version": "UCA_V5_SUPERIOR"
            }
        )


def datetime_to_iso(dt: Optional[Any]) -> str:
    from datetime import datetime
    if dt is None:
        return datetime.utcnow().isoformat()
    return str(dt)
