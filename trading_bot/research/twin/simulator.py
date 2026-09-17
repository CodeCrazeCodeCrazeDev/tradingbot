"""
Digital Twin Market Simulator for Research OS.
Instantiates adversarial market environments (flash crashes, spread expansions, news shocks, and exchange outages)
to stress-test trading strategy adaptability and survival.
"""

from typing import Dict, Any, List
import numpy as np
import logging
from copy import deepcopy
from trading_bot.research.core.interfaces import DigitalTwin, StandardizedDataset

logger = logging.getLogger(__name__)


class AdversarialMarketDigitalTwin(DigitalTwin):
    """
    Simulates stressful, high-impact adversarial scenario environments
    using baseline historical or stochastic market price datasets.
    """

    def instantiate_scenario(self, scenario_type: str, baseline_dataset: StandardizedDataset) -> StandardizedDataset:
        """
        Clones baseline dataset and injects extreme adversarial events.
        """
        twin_dataset = deepcopy(baseline_dataset)
        twin_dataset.dataset_id = f"{baseline_dataset.dataset_id}_twin_{scenario_type}"

        symbol = twin_dataset.symbols[0]
        o_col = f"{symbol}_open"
        h_col = f"{symbol}_high"
        l_col = f"{symbol}_low"
        c_col = f"{symbol}_close"
        v_col = f"{symbol}_volume"

        opens = twin_dataset.data[o_col].copy()
        highs = twin_dataset.data[h_col].copy()
        lows = twin_dataset.data[l_col].copy()
        closes = twin_dataset.data[c_col].copy()
        volumes = twin_dataset.data[v_col].copy()

        num_points = len(closes)

        if scenario_type == "flash_crash":
            logger.info("[*] Digital Twin: Injecting synthetic Flash Crash event.")
            # Flash crash occurs at 75% point of dataset
            crash_idx = int(num_points * 0.75)
            # Sudden 8% drop
            closes[crash_idx] *= 0.92
            lows[crash_idx] *= 0.90
            # Volatility clustering immediately following
            for i in range(crash_idx + 1, min(num_points, crash_idx + 15)):
                vol_noise = np.random.normal(0, 0.02)
                closes[i] = closes[i-1] * (1.0 + vol_noise)
                opens[i] = closes[i-1]
                highs[i] = max(closes[i], opens[i]) * 1.01
                lows[i] = min(closes[i], opens[i]) * 0.99
                volumes[i] *= 4.0  # high panic volume

        elif scenario_type == "news_shock":
            logger.info("[*] Digital Twin: Injecting synthetic major News Shock event.")
            shock_idx = int(num_points * 0.50)
            # Sudden +5% price gap
            closes[shock_idx] *= 1.05
            highs[shock_idx] *= 1.06
            opens[shock_idx] = closes[shock_idx-1]
            volumes[shock_idx] *= 8.0  # massive institutional flow

        elif scenario_type == "liquidity_failure":
            logger.info("[*] Digital Twin: Injecting synthetic Liquidity Failure / Spread Expansion.")
            # Injects massive spreads throughout the latter half of the data
            failure_start = int(num_points * 0.60)
            for i in range(failure_start, num_points):
                # Spread expands by 20x (implied in high/low gaps)
                highs[i] *= 1.015
                lows[i] *= 0.985
                volumes[i] *= 0.05  # zero liquidity / extremely thin trading

        elif scenario_type == "exchange_outage":
            logger.info("[*] Digital Twin: Injecting synthetic Exchange Outage.")
            # Exchange freezes for 10 periods
            outage_start = int(num_points * 0.40)
            outage_end = min(num_points, outage_start + 10)
            for i in range(outage_start, outage_end):
                closes[i] = closes[outage_start - 1]
                opens[i] = closes[outage_start - 1]
                highs[i] = closes[outage_start - 1]
                lows[i] = closes[outage_start - 1]
                volumes[i] = 0.0  # absolute freeze

        else:
            logger.warning(f"Unknown scenario type: {scenario_type}. Returning baseline dataset unmodified.")

        twin_dataset.data[o_col] = opens
        twin_dataset.data[h_col] = highs
        twin_dataset.data[l_col] = lows
        twin_dataset.data[c_col] = closes
        twin_dataset.data[v_col] = volumes

        # Log twin properties
        twin_dataset.metadata["scenario_type"] = scenario_type
        twin_dataset.metadata["adversarial"] = True

        return twin_dataset
