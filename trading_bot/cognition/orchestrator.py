"""Canonical Orchestrator for AlphaAlgo Cognitive Intelligence System.

Consolidates legacy monolithic entry points into a clean, modular cognitive loop.
"""

import time
import logging
from typing import Dict, Any, Optional, List

from trading_bot.cognition.perception import PerceptionEngine, Observation
from trading_bot.cognition.perception.drift import DriftMonitor
from trading_bot.cognition.state import StateEstimator, MarketState
from trading_bot.cognition.memory import HierarchicalMemoryEngine, MemoryTier
from trading_bot.cognition.simulation import CounterfactualSimulator, SimulationRequest
from trading_bot.cognition.reasoning import ModelRouter, TaskRequest, TaskCategory
from trading_bot.cognition.hypotheses import HypothesisEngine
from trading_bot.cognition.verification import AdversarialSubsystem
from trading_bot.cognition.decision import DecisionIntelligenceEngine, RiskGatekeeper, CognitiveAction, RiskGateResult
from trading_bot.cognition.learning.calibration import ProbabilityCalibrator

logger = logging.getLogger("alphaalgo.cognition.orchestrator")


class AlphaAlgoCognitiveBrain:
    """Canonical Unified Cognitive Trading Intelligence System for AlphaAlgo."""

    def __init__(
        self,
        perception: Optional[PerceptionEngine] = None,
        state_estimator: Optional[StateEstimator] = None,
        memory: Optional[HierarchicalMemoryEngine] = None,
        simulator: Optional[CounterfactualSimulator] = None,
        router: Optional[ModelRouter] = None,
        hypothesis_engine: Optional[HypothesisEngine] = None,
        adversary: Optional[AdversarialSubsystem] = None,
        decision_engine: Optional[DecisionIntelligenceEngine] = None,
        risk_gatekeeper: Optional[RiskGatekeeper] = None,
    ):
        self.perception = perception or PerceptionEngine()
        self.state_estimator = state_estimator or StateEstimator()
        self.memory = memory or HierarchicalMemoryEngine()
        self.simulator = simulator or CounterfactualSimulator()
        self.router = router or ModelRouter()
        self.hypothesis_engine = hypothesis_engine or HypothesisEngine()
        self.adversary = adversary or AdversarialSubsystem()
        self.decision_engine = decision_engine or DecisionIntelligenceEngine()
        self.risk_gatekeeper = risk_gatekeeper or RiskGatekeeper()

        # Phase-4 hardening: probability calibration + distribution-drift detection
        self.calibrator = ProbabilityCalibrator()
        self.drift_monitor = DriftMonitor()
        self.monte_carlo_paths = 256  # fat-tailed MC in the simulator

        # Register engines into the single authoritative registry so every
        # component in the brain is discoverable in one place.
        try:
            from trading_bot.core.unified_registry import get_registry
            from trading_bot.system_interfaces import SystemLayer
            reg = get_registry()
            reg.register("cognitive_brain", self, component_type="cognitive_brain", layer=SystemLayer.ORCHESTRATION)
            reg.register("perception_engine", self.perception, component_type="perception", layer=SystemLayer.INTELLIGENCE_CORE)
            reg.register("state_estimator", self.state_estimator, component_type="state_estimation", layer=SystemLayer.INTELLIGENCE_CORE)
            reg.register("hierarchical_memory", self.memory, component_type="memory", layer=SystemLayer.INTELLIGENCE_CORE)
            reg.register("counterfactual_simulator", self.simulator, component_type="simulation", layer=SystemLayer.INTELLIGENCE_CORE)
            reg.register("adversarial_subsystem", self.adversary, component_type="verification", layer=SystemLayer.RISK_SAFETY)
            reg.register("decision_engine", self.decision_engine, component_type="decision", layer=SystemLayer.INTELLIGENCE_CORE)
            reg.register("risk_gatekeeper", self.risk_gatekeeper, component_type="risk_gate", layer=SystemLayer.RISK_SAFETY)
        except Exception:
            pass  # registry unavailable — brain still functions standalone

    def process_cycle(
        self,
        instrument: str,
        raw_market_data: Dict[str, Dict[str, Any]],
        proposed_trade_signal: str = "NEUTRAL",
        stop_loss_price: Optional[float] = None,
        current_time: Optional[float] = None,
        lob_snapshot: Optional[Any] = None,
    ) -> Dict[str, Any]:
        """Executes one end-to-end cognitive trading loop."""
        ts = current_time or time.time()
        cycle_id = f"cog_{instrument}_{int(ts*1000)}"

        # 1. PERCEPTION (+ drift detection on the primary timeframe)
        observations = {}
        primary_tf = "M15" if "M15" in raw_market_data else next(iter(raw_market_data), None)
        drift_detected = False
        for tf, data in raw_market_data.items():
            obs = self.perception.process_raw_market_data(
                instrument=instrument,
                timeframe=tf,
                ohlcv=data,
                timestamp=ts,
                current_time=ts
            )
            observations[tf] = obs
            self.memory.store_working_observation(f"{instrument}_{tf}", data)
            if tf == primary_tf:
                o, c = data.get("open"), data.get("close")
                if isinstance(o, (int, float)) and isinstance(c, (int, float)) and o:
                    drift_detected = self.drift_monitor.update(instrument, c / o - 1.0)

        # 2. STATE ESTIMATION
        market_state = self.state_estimator.estimate_state(instrument, observations, current_time=ts)

        # 3. REASONING & HYPOTHESIS
        reasoning_task = TaskRequest(
            task_id=f"reason_{cycle_id}",
            category=TaskCategory.STRUCTURED_REASONING,
            payload={"topic": "market_regime", "state": market_state.get_dominant_regime()}
        )
        reasoning_resp = self.router.route_and_execute(reasoning_task)

        # 4. COUNTERFACTUAL SIMULATION (fat-tailed Monte Carlo)
        sim_req = SimulationRequest(
            request_id=f"sim_{cycle_id}",
            current_state=market_state,
            proposed_action=proposed_trade_signal if proposed_trade_signal in ("BUY", "SELL") else "HOLD",
            position_size=1.0,
            time_horizon_bars=5,
            monte_carlo_paths=self.monte_carlo_paths,
        )
        sim_res = self.simulator.simulate(sim_req)

        # 5. ADVERSARIAL ATTACK
        adv_report = self.adversary.attack_trade_hypothesis(
            hypothesis_id=f"hyp_{cycle_id}",
            proposed_action=proposed_trade_signal,
            market_state=market_state,
            simulation_result=sim_res
        )

        # 6. DECISION INTELLIGENCE (with probability calibration)
        self.decision_engine.calibrator = self.calibrator
        proposal = self.decision_engine.synthesize_decision(
            decision_id=f"dec_{cycle_id}",
            market_state=market_state,
            simulation_result=sim_res,
            adversarial_report=adv_report,
            raw_signal=proposed_trade_signal
        )
        proposal.stop_loss = stop_loss_price

        # 7. RISK GATEKEEPER
        risk_result: RiskGateResult = self.risk_gatekeeper.evaluate_proposal(proposal)

        # 8. MEMORY & GOVERNANCE RECORDING
        self.memory.store_episodic_event(
            event_id=cycle_id,
            content={
                "proposal": proposal,
                "risk_result": risk_result,
                "regime": market_state.get_dominant_regime()
            },
            source="AlphaAlgoCognitiveBrain",
            provenance={"cycle_id": cycle_id, "timestamp": ts}
        )

        return {
            "cycle_id": cycle_id,
            "instrument": instrument,
            "authorized_action": risk_result.authorized_action.value,
            "authorized_size": risk_result.authorized_size,
            "risk_authorized": risk_result.authorized,
            "market_state": {
                "regime": market_state.get_dominant_regime(),
                "trend": market_state.trend_direction,
                "uncertainty": market_state.uncertainty
            },
            "adversarial_passed": adv_report.attack_passed,
            "rejection_reason": risk_result.rejection_reason or proposal.contradicting_evidence,
            "drift_detected": drift_detected,
            "calibrated_probability": proposal.calibrated_probability,
            "raw_win_probability": sim_res.win_probability,
            "mc_p95_drawdown": sim_res.mc_p95_drawdown,
            "microstructure": (
                lob_snapshot.features() if hasattr(lob_snapshot, "features") else None
            ),
        }

    def record_outcome(self, raw_probability: float, outcome_was_correct: bool) -> None:
        """Feed a realized outcome back into the calibrator (Platt→isotonic)."""
        self.calibrator.update(raw_probability, 1.0 if outcome_was_correct else 0.0)
