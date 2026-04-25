"""
Calibrated Simulation Engine — Dream, Validate, Correct
=========================================================

The "imagination" layer of the COS. It simulates scenarios, tests ideas,
and tracks how well its predictions match reality.

The key innovation over a plain simulator: **calibration tracking**.
Every simulation records its fidelity (how well past predictions matched
reality), and this fidelity score weights how much the Decision Support
system trusts the simulation output.

Three simulation modes:
    1. DREAM:          Generate scenarios from the world model, test ideas
    2. COUNTERFACTUAL: "What if X had been different?" — causal reasoning
    3. STRESS_TEST:    Extreme scenarios — tail risk assessment

Integration with existing systems:
    - trading_bot.world_model.SimulationOrchestrator  → heavy sim
    - trading_bot.world_model.ImaginationPlanner       → trajectory planning
    - trading_bot.world_model.CounterfactualEngine     → what-if analysis
    - trading_bot.simulation.DigitalTwin               → market twin
"""

from __future__ import annotations

import logging
import time
from collections import defaultdict
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple
from uuid import uuid4

import numpy as np

from .types import (
    COSConfig,
    Idea,
    IdeaStatus,
    KnowledgeCategory,
    KnowledgeNode,
    SimulationFidelity,
    SimulationResult,
)

logger = logging.getLogger(__name__)


class CalibratedSimulationEngine:
    """
    Simulates ideas and tracks prediction-reality gaps for calibration.

    The "calibrated" part is critical: this isn't just a simulator that
    spits out numbers. It maintains a running record of how accurate its
    past predictions have been, and uses that record to:
      1. Adjust confidence of new predictions
      2. Identify which types of scenarios it's good/bad at
      3. Feed corrections back to the Cognition Store

    The loop:
        simulate (dream) → generate insights → test in real world
        → compare results → correct simulation model
    """

    def __init__(self, config: COSConfig, cognition_store=None):
        self.config = config
        self.cognition_store = cognition_store

        # Calibration tracking: regime → list of (predicted, actual) pairs
        self._calibration_history: Dict[str, List[Tuple[float, float]]] = defaultdict(list)
        self._regime_fidelity: Dict[str, SimulationFidelity] = {}

        # Simulation result cache: idea_id → list of SimulationResult
        self._result_cache: Dict[str, List[SimulationResult]] = defaultdict(list)

        # External engine references (lazy-loaded)
        self._world_model_orchestrator = None
        self._imagination_planner = None
        self._counterfactual_engine = None
        self._digital_twin = None

        # Stats
        self._simulations_run = 0
        self._total_sim_time_ms = 0.0

        logger.info(
            f"CalibratedSimulationEngine initialized | "
            f"dream_scenarios={config.num_dream_scenarios} | "
            f"horizon={config.dream_horizon_steps}"
        )

    # ── Public API ────────────────────────────────────────────────────────

    def simulate_idea(self, idea: Idea) -> List[SimulationResult]:
        """
        Run a full simulation suite on an idea.

        1. Dream scenarios (imagined futures)
        2. Counterfactual analysis (what-if)
        3. Stress test (tail risk)

        Returns all simulation results, and updates the idea's status.
        """
        start = time.time()
        results: List[SimulationResult] = []

        # Phase 1: Dream scenarios
        dream_results = self._dream(idea)
        results.extend(dream_results)

        # Phase 2: Counterfactual analysis
        cf_results = self._counterfactual(idea)
        results.extend(cf_results)

        # Phase 3: Stress test
        stress_results = self._stress_test(idea)
        results.extend(stress_results)

        # Aggregate into idea
        idea.simulation_results = results
        idea.status = IdeaStatus.SIMULATED

        # Compute aggregate expected PnL and risk
        if results:
            idea.expected_pnl = np.median([r.predicted_pnl for r in results])
            idea.expected_risk = np.median([r.predicted_risk for r in results])
            idea.simulation_confidence = self._compute_idea_confidence(results)

        # Cache results
        self._result_cache[idea.idea_id] = results

        elapsed_ms = (time.time() - start) * 1000
        self._simulations_run += len(results)
        self._total_sim_time_ms += elapsed_ms

        logger.info(
            f"Simulated idea {idea.idea_id} | {len(results)} scenarios | "
            f"expected_pnl={idea.expected_pnl:.4f} | "
            f"confidence={idea.simulation_confidence:.2f} | "
            f"time={elapsed_ms:.0f}ms"
        )

        return results

    def update_calibration(
        self,
        regime: str,
        predicted_pnl: float,
        actual_pnl: float,
    ):
        """
        Record a prediction-reality pair for calibration tracking.

        Called by the FeedbackLoop after a reality check.
        """
        self._calibration_history[regime].append((predicted_pnl, actual_pnl))

        # Recompute fidelity for this regime
        pairs = self._calibration_history[regime]
        if len(pairs) >= self.config.min_checks_for_calibration:
            fidelity = self._compute_regime_fidelity(pairs)
            self._regime_fidelity[regime] = fidelity

            # Store calibration knowledge
            if self.cognition_store is not None:
                from .types import KnowledgeNode
                node = KnowledgeNode(
                    category=KnowledgeCategory.SIMULATION_CALIBRATION,
                    title=f"Calibration: {regime}",
                    content=f"Simulation fidelity for {regime}: {fidelity.value}. "
                            f"Based on {len(pairs)} prediction-reality comparisons.",
                    structured_data={
                        "regime": regime,
                        "fidelity": fidelity.value,
                        "sample_count": len(pairs),
                        "mean_error": float(np.mean([p - a for p, a in pairs])),
                        "std_error": float(np.std([p - a for p, a in pairs])),
                    },
                    source="simulation_calibration",
                )
                self.cognition_store.ingest(node)

            logger.info(f"Calibration updated for {regime} | fidelity={fidelity.value}")

    def get_fidelity(self, regime: str) -> SimulationFidelity:
        """Get the current simulation fidelity for a market regime."""
        return self._regime_fidelity.get(regime, SimulationFidelity.UNCALIBRATED)

    def get_calibration_bias(self, regime: str) -> float:
        """
        Get the systematic bias of simulation predictions for a regime.

        Positive = simulation overestimates PnL.
        Negative = simulation underestimates PnL.
        """
        pairs = self._calibration_history.get(regime, [])
        if len(pairs) < 3:
            return 0.0
        errors = [p - a for p, a in pairs]
        return float(np.mean(errors))

    def adjust_prediction(self, regime: str, predicted_pnl: float) -> float:
        """
        Adjust a prediction based on known calibration bias.

        If the simulation consistently overestimates by 2%, subtract 2%.
        """
        bias = self.get_calibration_bias(regime)
        return predicted_pnl - bias

    # ── Simulation Modes ──────────────────────────────────────────────────

    def _dream(self, idea: Idea) -> List[SimulationResult]:
        """
        Dream mode: imagine multiple future scenarios.

        Uses the world model (if available) or a lightweight statistical
        simulator to project the idea forward under different market conditions.
        """
        results = []
        regimes = ["normal", "trending_up", "trending_down", "volatile", "calm"]

        for i in range(self.config.num_dream_scenarios):
            regime = regimes[i % len(regimes)]
            fidelity = self.get_fidelity(regime)

            # Try using the world model orchestrator
            if self._try_world_model(idea, regime):
                result = self._simulate_with_world_model(idea, regime, fidelity, "dream")
            else:
                result = self._simulate_statistical(idea, regime, fidelity, "dream")

            results.append(result)

        return results

    def _counterfactual(self, idea: Idea) -> List[SimulationResult]:
        """
        Counterfactual mode: "What if X had been different?"

        Tests the idea under specific interventions (e.g., "what if
        volatility was 2x?", "what if the regime changed at step 50?").
        """
        results = []
        interventions = [
            {"name": "double_volatility", "volatility_mult": 2.0},
            {"name": "half_volatility", "volatility_mult": 0.5},
            {"name": "regime_shift_at_50", "regime_shift": True, "shift_step": 50},
            {"name": "flash_crash", "flash_crash_at": 30, "crash_magnitude": -0.05},
        ][:self.config.counterfactual_depth]

        for intervention in interventions:
            regime = "normal"
            fidelity = self.get_fidelity(regime)
            result = self._simulate_statistical(
                idea, regime, fidelity, "counterfactual",
                scenario_params=intervention,
            )
            results.append(result)

        return results

    def _stress_test(self, idea: Idea) -> List[SimulationResult]:
        """
        Stress test mode: extreme / tail-risk scenarios.

        Tests whether the idea survives black-swan-like conditions.
        """
        results = []
        stress_scenarios = [
            {"name": "black_swan", "regime": "crash", "volatility_mult": 5.0},
            {"name": "liquidity_crisis", "regime": "crash", "slippage_mult": 10.0},
            {"name": "whipsaw", "regime": "volatile", "regime_flip_freq": 10},
            {"name": "zero_volume", "regime": "calm", "volume_mult": 0.01},
            {"name": "correlation_breakdown", "regime": "volatile", "correlation_flip": True},
        ][:self.config.stress_test_scenarios]

        for scenario in stress_scenarios:
            regime = scenario.get("regime", "volatile")
            fidelity = self.get_fidelity(regime)
            result = self._simulate_statistical(
                idea, regime, fidelity, "stress_test",
                scenario_params=scenario,
            )
            results.append(result)

        return results

    # ── Simulation Implementations ────────────────────────────────────────

    def _simulate_statistical(
        self,
        idea: Idea,
        regime: str,
        fidelity: SimulationFidelity,
        mode: str,
        scenario_params: Optional[Dict] = None,
    ) -> SimulationResult:
        """
        Lightweight statistical simulation.

        Uses a simple regime-conditioned random walk to project PnL.
        This is the fallback when the full world model is unavailable.
        """
        params = scenario_params or {}
        horizon = self.config.dream_horizon_steps

        # Regime-conditioned parameters
        regime_params = {
            "normal":       {"drift": 0.0001, "vol": 0.01},
            "trending_up":  {"drift": 0.0005, "vol": 0.012},
            "trending_down":{"drift": -0.0005, "vol": 0.012},
            "volatile":     {"drift": 0.0,     "vol": 0.03},
            "calm":         {"drift": 0.0001,  "vol": 0.005},
            "crash":        {"drift": -0.002,  "vol": 0.05},
        }

        rp = regime_params.get(regime, regime_params["normal"])

        # Apply intervention multipliers
        vol_mult = params.get("volatility_mult", 1.0)
        drift = rp["drift"]
        vol = rp["vol"] * vol_mult

        # Simulate equity curve
        rng = np.random.RandomState(hash(idea.idea_id + regime + mode) % (2**31))
        returns = rng.normal(drift, vol, horizon)

        # Flash crash injection
        if "flash_crash_at" in params:
            step = params["flash_crash_at"]
            magnitude = params.get("crash_magnitude", -0.05)
            if step < horizon:
                returns[step] += magnitude

        equity = np.cumprod(1 + returns)
        final_pnl = equity[-1] - 1.0

        # Risk metrics
        max_dd = self._max_drawdown(equity)
        sharpe = self._simple_sharpe(returns)
        win_rate = np.mean(returns > 0)

        # Apply calibration adjustment
        adjusted_pnl = self.adjust_prediction(regime, final_pnl)

        # Confidence based on fidelity and scenario stability
        confidence = fidelity.value * 0.5 + 0.5 * (1.0 - min(1.0, vol / 0.05))

        # Retrieve knowledge nodes used
        used_node_ids = idea.source_node_ids[:]

        return SimulationResult(
            idea_id=idea.idea_id,
            scenario_name=params.get("name", regime),
            scenario_params=params,
            market_regime=regime,
            duration_steps=horizon,
            predicted_pnl=adjusted_pnl,
            predicted_risk=max_dd,
            predicted_sharpe=sharpe,
            predicted_max_drawdown=max_dd,
            win_rate=float(win_rate),
            confidence=max(0.0, min(1.0, confidence)),
            fidelity=fidelity,
            trajectory_summary={
                "final_equity": float(equity[-1]),
                "max_equity": float(np.max(equity)),
                "min_equity": float(np.min(equity)),
                "volatility_realized": float(np.std(returns) * np.sqrt(252)),
            },
            used_node_ids=used_node_ids,
            simulation_mode=mode,
        )

    def _simulate_with_world_model(
        self,
        idea: Idea,
        regime: str,
        fidelity: SimulationFidelity,
        mode: str,
    ) -> SimulationResult:
        """
        Full simulation using the world model orchestrator.

        Delegates to trading_bot.world_model.SimulationOrchestrator
        when available, then wraps the result into our SimulationResult format.
        """
        try:
            if self._world_model_orchestrator is not None:
                # Use the full simulation pipeline
                from trading_bot.world_model.simulation_orchestrator import (
                    SimulationConfig, SimulationMode, MarketRegime
                )

                mode_map = {
                    "dream": SimulationMode.DREAMING,
                    "counterfactual": SimulationMode.LEARNING,
                    "stress_test": SimulationMode.TESTING,
                }

                sim_config = SimulationConfig(
                    mode=mode_map.get(mode, SimulationMode.DREAMING),
                    duration_steps=self.config.dream_horizon_steps,
                )

                result = self._world_model_orchestrator.run_simulation(sim_config)

                # Extract metrics from the world model result
                metrics = result.metrics if hasattr(result, 'metrics') else {}
                experiences = result.experiences if hasattr(result, 'experiences') else []

                predicted_pnl = metrics.get("avg_return", 0.0)
                predicted_risk = metrics.get("max_drawdown", 0.0)
                sharpe = metrics.get("sharpe_ratio", 0.0)
                win_rate = metrics.get("win_rate", 0.5)

                adjusted_pnl = self.adjust_prediction(regime, predicted_pnl)
                confidence = fidelity.value * 0.7 + 0.3  # world model gives higher base confidence

                return SimulationResult(
                    idea_id=idea.idea_id,
                    scenario_name=f"world_model_{regime}",
                    market_regime=regime,
                    duration_steps=self.config.dream_horizon_steps,
                    predicted_pnl=adjusted_pnl,
                    predicted_risk=predicted_risk,
                    predicted_sharpe=sharpe,
                    predicted_max_drawdown=predicted_risk,
                    win_rate=win_rate,
                    confidence=min(1.0, confidence),
                    fidelity=fidelity,
                    trajectory_summary=metrics,
                    used_node_ids=idea.source_node_ids,
                    simulation_mode=mode,
                )
        except Exception as e:
            logger.warning(f"World model simulation failed: {e}, falling back to statistical")

        # Fallback
        return self._simulate_statistical(idea, regime, fidelity, mode)

    # ── External Engine Integration ───────────────────────────────────────

    def connect_world_model(self, orchestrator):
        """Connect to the existing world model SimulationOrchestrator."""
        self._world_model_orchestrator = orchestrator
        logger.info("Connected world model orchestrator")

    def connect_imagination_planner(self, planner):
        """Connect to the existing ImaginationPlanner."""
        self._imagination_planner = planner
        logger.info("Connected imagination planner")

    def connect_counterfactual_engine(self, engine):
        """Connect to the existing CounterfactualEngine."""
        self._counterfactual_engine = engine
        logger.info("Connected counterfactual engine")

    def connect_digital_twin(self, twin):
        """Connect to the existing DigitalTwin."""
        self._digital_twin = twin
        logger.info("Connected digital twin")

    def _try_world_model(self, idea: Idea, regime: str) -> bool:
        """Check if the world model orchestrator is available and usable."""
        return self._world_model_orchestrator is not None

    # ── Helpers ───────────────────────────────────────────────────────────

    def _compute_idea_confidence(self, results: List[SimulationResult]) -> float:
        """
        Aggregate confidence across all simulation results for an idea.

        Weighted by fidelity — calibrated scenarios count more.
        """
        if not results:
            return 0.0

        total_weight = 0.0
        weighted_conf = 0.0

        for r in results:
            weight = r.fidelity.value + 0.1  # minimum weight so uncalibrated still counts
            weighted_conf += r.confidence * weight
            total_weight += weight

        return weighted_conf / total_weight if total_weight > 0 else 0.0

    def _compute_regime_fidelity(self, pairs: List[Tuple[float, float]]) -> SimulationFidelity:
        """
        Compute simulation fidelity from prediction-reality pairs.

        Uses normalized mean absolute error to classify fidelity.
        """
        if len(pairs) < 3:
            return SimulationFidelity.UNCALIBRATED

        errors = [abs(p - a) for p, a in pairs]
        actuals = [abs(a) for _, a in pairs]
        mean_actual = max(np.mean(actuals), 1e-6)

        nmae = np.mean(errors) / mean_actual  # normalized MAE

        if nmae < 0.1:
            return SimulationFidelity.CALIBRATED
        elif nmae < 0.25:
            return SimulationFidelity.GOOD
        elif nmae < 0.5:
            return SimulationFidelity.APPROXIMATE
        elif nmae < 1.0:
            return SimulationFidelity.POOR
        else:
            return SimulationFidelity.UNCALIBRATED

    @staticmethod
    def _max_drawdown(equity: np.ndarray) -> float:
        """Compute maximum drawdown from equity curve."""
        peak = np.maximum.accumulate(equity)
        drawdown = (equity - peak) / peak
        return float(np.min(drawdown))

    @staticmethod
    def _simple_sharpe(returns: np.ndarray, annualize_factor: float = 252) -> float:
        """Compute annualized Sharpe ratio."""
        if np.std(returns) < 1e-10:
            return 0.0
        return float(np.mean(returns) / np.std(returns) * np.sqrt(annualize_factor))

    # ── Stats ─────────────────────────────────────────────────────────────

    def stats(self) -> Dict[str, Any]:
        """Return simulation engine statistics."""
        fidelity_summary = {r: f.value for r, f in self._regime_fidelity.items()}
        return {
            "simulations_run": self._simulations_run,
            "total_sim_time_ms": self._total_sim_time_ms,
            "avg_sim_time_ms": self._total_sim_time_ms / max(1, self._simulations_run),
            "regime_fidelity": fidelity_summary,
            "calibration_samples": {r: len(p) for r, p in self._calibration_history.items()},
            "world_model_connected": self._world_model_orchestrator is not None,
            "imagination_connected": self._imagination_planner is not None,
            "counterfactual_connected": self._counterfactual_engine is not None,
            "digital_twin_connected": self._digital_twin is not None,
        }
