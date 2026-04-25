"""
COS Core — The Recursive Loop Orchestrator
============================================

This is the central nervous system of the Cognitive Operating System.
It orchestrates the closed recurrent recursive loop:

    ┌──────────┐     ┌───────────┐     ┌──────────┐
    │  RECALL  │────▶│  SIMULATE │────▶│  DECIDE  │
    │ (knowledge)│   │  (dream)  │     │ (support) │
    └────▲──────┘     └─────┬─────┘     └─────┬────┘
         │                  │                  │
         │                  │                  ▼
         │           ┌──────▼──────┐    ┌──────────┐
         │           │  VALIDATE   │◀───│  EXECUTE  │
         │           │  (reality)  │    │  (feed)   │
         │           └──────┬──────┘    └──────────┘
         │                  │
         └──────────────────┘  ← CORRECT MODEL

Each cycle:
    1. RECALL:    Retrieve relevant knowledge from Cognition Store
    2. GENERATE:  Produce new ideas from knowledge + context
    3. SIMULATE:  Dream-test ideas in Calibrated Simulation Engine
    4. EVALUATE:  Score ideas by confidence, risk/reward, agreement
    5. DECIDE:    Convert top ideas into decision traces
    6. EXECUTE:   Feed decisions to the trading execution layer
    7. CHECK:     Compare predictions against reality
    8. CORRECT:   Generate and apply calibration deltas
    9. UPDATE:    Knowledge base + simulation model updated → smarter next cycle

The loop is:
    - CLOSED:    Step 9 feeds back into Step 1
    - RECURRENT: State persists across cycles (cognition store, calibration)
    - RECURSIVE: Meta-cognitive insights improve the loop itself

Integration with the full trading bot system:
    - trading_bot.cognitive_architecture  → market perception
    - trading_bot.world_model             → simulation engines
    - trading_bot.decision_layer          → decision concepts
    - trading_bot.feedback                → reality signal
    - trading_bot.brain                   → execution layer
"""

from __future__ import annotations

import asyncio
import logging
import time
from collections import defaultdict
from datetime import datetime
from typing import Any, Callable, Dict, List, Optional, Tuple

import numpy as np

from .types import (
    CalibrationDelta,
    COSConfig,
    COSCycleReport,
    DecisionTrace,
    Idea,
    IdeaStatus,
    KnowledgeCategory,
    KnowledgeNode,
    RealityCheck,
    SimulationFidelity,
    SimulationResult,
)
from .cognition_store import CognitionStore
from .simulation_engine import CalibratedSimulationEngine
from .decision_support import DecisionSupportSystem
from .feedback_loop import RealityCalibrationLoop

logger = logging.getLogger(__name__)


class CognitiveOperatingSystem:
    """
    The Externalized Intelligence Core of the trading bot.

    A system that:
      - STRUCTURES knowledge  → CognitionStore
      - EVALUATES ideas       → DecisionSupportSystem
      - SUPPORTS decisions    → CalibratedSimulationEngine
      - FEEDS execution       → Decision traces → execution layer
      - EVOLVES with feedback → RealityCalibrationLoop

    Usage:
        cos = CognitiveOperatingSystem(COSConfig())
        cos.initialize()

        # Run one cycle
        report = cos.run_cycle(market_context={...})

        # Run continuously
        cos.start_loop()

        # Feed reality back
        cos.feed_reality(trace_id="...", actual_pnl=0.05, actual_risk=0.02)
    """

    def __init__(self, config: Optional[COSConfig] = None):
        self.config = config or COSConfig()

        # Core components
        self.cognition_store = CognitionStore(self.config)
        self.simulation_engine = CalibratedSimulationEngine(
            self.config, cognition_store=self.cognition_store
        )
        self.decision_support = DecisionSupportSystem(
            self.config,
            cognition_store=self.cognition_store,
            simulation_engine=self.simulation_engine,
        )
        self.feedback_loop = RealityCalibrationLoop(
            self.config,
            cognition_store=self.cognition_store,
            simulation_engine=self.simulation_engine,
            decision_support=self.decision_support,
        )

        # Cross-link components
        self.simulation_engine.cognition_store = self.cognition_store
        self.decision_support.cognition_store = self.cognition_store
        self.decision_support.simulation_engine = self.simulation_engine
        self.feedback_loop.cognition_store = self.cognition_store
        self.feedback_loop.simulation_engine = self.simulation_engine
        self.feedback_loop.decision_support = self.decision_support

        # Loop state
        self._cycle_count = 0
        self._is_running = False
        self._last_cycle_report: Optional[COSCycleReport] = None
        self._cycle_reports: List[COSCycleReport] = []

        # Execution callback — how decisions are fed to the trading system
        self._execution_callback: Optional[Callable[[DecisionTrace], None]] = None

        # External system references (lazy-connected)
        self._cognitive_core = None
        self._world_model_orchestrator = None
        self._decision_engine = None
        self._feedback_analyzer = None

        # Pending decisions awaiting reality feedback
        self._pending_decisions: Dict[str, DecisionTrace] = {}

        logger.info("CognitiveOperatingSystem initialized")

    # ── Initialization ────────────────────────────────────────────────────

    def initialize(self):
        """
        Full initialization: load persisted state, connect to external systems.
        """
        # Load persisted knowledge
        self.cognition_store.load()

        # Seed with domain priors if store is empty
        if len(self.cognition_store._nodes) == 0:
            self._seed_domain_priors()

        # Try to connect to existing trading bot systems
        self._auto_connect()

        logger.info(
            f"COS initialized | knowledge_nodes={len(self.cognition_store._nodes)} | "
            f"config={self.config.storage_path}"
        )

    def _seed_domain_priors(self):
        """
        Seed the Cognition Store with foundational trading knowledge.

        These are the "domain priors" — basic truths that the system
        starts with before it learns anything from experience.
        """
        priors = [
            KnowledgeNode(
                category=KnowledgeCategory.DOMAIN_PRIOR,
                title="Risk-Reward Fundamental",
                content="Higher expected returns generally come with higher risk. "
                        "Risk-adjusted returns (Sharpe) matter more than raw returns.",
                structured_data={"risk_reward_tradeoff": True, "sharpe_importance": 0.9},
                source="domain_prior",
                salience=0.8,
            ),
            KnowledgeNode(
                category=KnowledgeCategory.MARKET_REGIME,
                title="Market Regime Types",
                content="Markets alternate between trending, mean-reverting, volatile, "
                        "and calm regimes. Strategy effectiveness is regime-dependent.",
                structured_data={
                    "regimes": ["trending_up", "trending_down", "volatile", "calm", "normal"],
                    "regime_dependence": True,
                },
                source="domain_prior",
                salience=0.9,
            ),
            KnowledgeNode(
                category=KnowledgeCategory.RISK_INSIGHT,
                title="Drawdown Control",
                content="Maximum drawdown is the primary risk metric. Recovery from "
                        "large drawdowns requires exponentially larger gains.",
                structured_data={
                    "max_acceptable_drawdown": 0.15,
                    "recovery_formula": "gain_to_recover = dd / (1 - dd)",
                },
                source="domain_prior",
                salience=0.85,
            ),
            KnowledgeNode(
                category=KnowledgeCategory.CAUSAL_RELATION,
                title="Volatility-Opportunity Link",
                content="Volatility creates opportunity but also risk. "
                        "Optimal strategy adjusts position size inversely with volatility.",
                structured_data={
                    "volatility_opportunity_correlation": 0.6,
                    "position_sizing_rule": "inverse_volatility",
                },
                source="domain_prior",
                salience=0.7,
            ),
            KnowledgeNode(
                category=KnowledgeCategory.EXECUTION_LESSON,
                title="Slippage and Market Impact",
                content="Execution costs reduce theoretical returns. Larger positions "
                        "have proportionally larger market impact.",
                structured_data={
                    "typical_slippage_bps": 5,
                    "impact_scaling": "square_root",
                },
                source="domain_prior",
                salience=0.6,
            ),
            KnowledgeNode(
                category=KnowledgeCategory.TEMPORAL_PATTERN,
                title="Mean Reversion Tendency",
                content="Over short timeframes, prices exhibit mean-reverting behavior. "
                        "Over longer timeframes, trending dominates.",
                structured_data={
                    "short_horizon_reversion": True,
                    "long_horizon_trending": True,
                    "crossover_minutes": 30,
                },
                source="domain_prior",
                salience=0.7,
            ),
            KnowledgeNode(
                category=KnowledgeCategory.META_COGNITIVE,
                title="COS Self-Awareness",
                content="The Cognitive Operating System learns from its own prediction "
                        "errors. Calibration improves over time as reality checks accumulate.",
                structured_data={
                    "learning_mechanism": "calibration_loop",
                    "improvement_rate": "logarithmic_with_samples",
                },
                source="meta_cognitive",
                salience=0.5,
            ),
        ]

        for prior in priors:
            self.cognition_store.ingest(prior)

        logger.info(f"Seeded {len(priors)} domain priors")

    def _auto_connect(self):
        """Attempt to auto-connect to existing trading bot systems."""
        # Each import is wrapped individually so a broken module
        # in one subsystem doesn't prevent connecting others.
        for module_path, attr_name in [
            ("trading_bot.world_model.simulation_orchestrator", "SimulationOrchestrator"),
            ("trading_bot.feedback.analyzer", "FeedbackAnalyzer"),
            ("trading_bot.decision_layer.innovative_decision_engine", "InnovativeDecisionEngine"),
            ("trading_bot.cognitive_architecture.cognitive_core", "AlphaAlgoCognitiveCore"),
        ]:
            try:
                __import__(module_path, fromlist=[attr_name])
            except Exception:
                pass

    # ── Main Loop ─────────────────────────────────────────────────────────

    def run_cycle(self, market_context: Optional[Dict[str, Any]] = None) -> COSCycleReport:
        """
        Execute one complete COS loop cycle.

        The cycle:
            1. RECALL:    Retrieve relevant knowledge
            2. GENERATE:  Produce new ideas from knowledge + context
            3. SIMULATE:  Dream-test ideas
            4. EVALUATE:  Score and rank ideas
            5. DECIDE:    Convert top ideas to decision traces
            6. CHECK:     Run reality checks on resolved decisions
            7. CORRECT:   Generate and apply calibration deltas
            8. UPDATE:    Consolidate knowledge store

        Returns a COSCycleReport with full cycle metrics.
        """
        cycle_start = time.time()
        report = COSCycleReport(cycle_number=self._cycle_count)
        context = market_context or {}

        # ── Phase 1: RECALL ──────────────────────────────────────────────
        t0 = time.time()

        # Retrieve knowledge relevant to current market context
        regime = context.get("regime", "normal")
        query_emb = self._context_to_embedding(context)
        relevant_nodes = self.cognition_store.recall(
            query_emb, top_k=20, min_salience=0.1
        )

        report.nodes_retrieved = len(relevant_nodes)
        report.knowledge_retrieval_ms = (time.time() - t0) * 1000

        # ── Phase 2: GENERATE ────────────────────────────────────────────
        t0 = time.time()

        # Generate ideas from knowledge + context
        ideas = self.decision_support.generate_ideas_from_knowledge(context)
        report.ideas_generated = len(ideas)
        report.idea_generation_ms = (time.time() - t0) * 1000

        # ── Phase 3: SIMULATE ────────────────────────────────────────────
        t0 = time.time()

        simulated_count = 0
        for idea in ideas:
            if idea.status == IdeaStatus.CANDIDATE:
                self.simulation_engine.simulate_idea(idea)
                simulated_count += 1

        report.ideas_simulated = simulated_count
        report.simulation_ms = (time.time() - t0) * 1000

        # ── Phase 4: EVALUATE ────────────────────────────────────────────
        t0 = time.time()

        validated_ideas = self.decision_support.evaluate_ideas()

        report.decision_ms = (time.time() - t0) * 1000

        # ── Phase 5: DECIDE ──────────────────────────────────────────────
        t0 = time.time()

        decisions = []
        for idea in validated_ideas:
            trace = self.decision_support.decide(idea, context)
            decisions.append(trace)

            # Register for reality checking
            self.feedback_loop.register_decision(trace)
            self._pending_decisions[trace.trace_id] = trace

            # Feed to execution layer
            if self._execution_callback is not None:
                self._execution_callback(trace)

        report.decisions_made = len(decisions)
        report.execution_ms = (time.time() - t0) * 1000

        # ── Phase 6: CHECK (reality checks on resolved decisions) ────────
        t0 = time.time()

        # Process any resolved decisions that have reality data
        checks = self._process_pending_reality()
        report.reality_checks = len(checks)
        report.feedback_ms = (time.time() - t0) * 1000

        # ── Phase 7: CORRECT ─────────────────────────────────────────────
        t0 = time.time()

        deltas = self.feedback_loop.run_calibration_cycle()
        report.calibration_deltas = len(deltas)
        report.calibration_ms = (time.time() - t0) * 1000

        # ── Phase 8: UPDATE ──────────────────────────────────────────────
        # Consolidate knowledge store periodically
        if self._cycle_count % 10 == 0:
            self.cognition_store.consolidate()

        # Auto-save periodically
        if self._cycle_count % self.config.auto_save_interval_cycles == 0:
            self.cognition_store.save()

        # ── Report ────────────────────────────────────────────────────────
        report.total_cycle_ms = (time.time() - cycle_start) * 1000
        report.knowledge_store_size = len(self.cognition_store._nodes)
        report.pending_ideas = len(self.decision_support._active_ideas)
        report.avg_simulation_fidelity = self._avg_fidelity()
        report.avg_prediction_quality = self.feedback_loop._global_calibration_score
        report.calibration_score = self.feedback_loop._global_calibration_score

        self._cycle_count += 1
        self._last_cycle_report = report
        self._cycle_reports.append(report)

        # Keep only last 100 reports
        if len(self._cycle_reports) > 100:
            self._cycle_reports = self._cycle_reports[-100:]

        logger.info(
            f"COS Cycle {report.cycle_number} | "
            f"nodes={report.nodes_retrieved} ideas={report.ideas_generated} "
            f"simulated={report.ideas_simulated} decisions={report.decisions_made} "
            f"checks={report.reality_checks} deltas={report.calibration_deltas} | "
            f"time={report.total_cycle_ms:.0f}ms | "
            f"calibration={report.calibration_score:.2f}"
        )

        return report

    async def run_cycle_async(self, market_context: Optional[Dict[str, Any]] = None) -> COSCycleReport:
        """Async wrapper for run_cycle."""
        return self.run_cycle(market_context)

    def start_loop(self, context_provider: Optional[Callable] = None):
        """
        Start the continuous COS loop.

        Args:
            context_provider: Optional callable that returns market context dict
                              each cycle. If None, uses empty context.
        """
        self._is_running = True
        logger.info("COS loop started")

        try:
            while self._is_running:
                context = {}
                if context_provider is not None:
                    context = context_provider()

                self.run_cycle(context)

                # Sleep for the configured interval
                time.sleep(self.config.cycle_interval_seconds)
        except KeyboardInterrupt:
            logger.info("COS loop stopped by user")
        finally:
            self._is_running = False

    async def start_loop_async(self, context_provider: Optional[Callable] = None):
        """Async version of start_loop."""
        self._is_running = True
        logger.info("COS async loop started")

        try:
            while self._is_running:
                context = {}
                if context_provider is not None:
                    result = context_provider()
                    if asyncio.iscoroutine(result):
                        context = await result
                    else:
                        context = result

                await self.run_cycle_async(context)

                await asyncio.sleep(self.config.cycle_interval_seconds)
        except asyncio.CancelledError:
            logger.info("COS async loop cancelled")
        finally:
            self._is_running = False

    def stop_loop(self):
        """Stop the continuous COS loop."""
        self._is_running = False
        logger.info("COS loop stop requested")

    # ── Reality Feeding ────────────────────────────────────────────────────

    def feed_reality(
        self,
        trace_id: str,
        actual_pnl: float,
        actual_risk: float,
        actual_regime: str = "",
    ) -> Optional[RealityCheck]:
        """
        Feed reality data back into the COS for a specific decision.

        This is how the loop closes — the execution layer reports
        actual outcomes, which are compared against predictions.
        """
        check = self.feedback_loop.check_reality(
            trace_id=trace_id,
            actual_pnl=actual_pnl,
            actual_risk=actual_risk,
            actual_regime=actual_regime,
        )

        if check is not None:
            # Generate and apply calibration delta immediately
            if check.prediction_quality < 0.8:
                delta = self.feedback_loop.generate_calibration_delta(check)
                self.feedback_loop.apply_calibration_delta(delta)

            self._pending_decisions.pop(trace_id, None)

        return check

    def feed_reality_batch(self, outcomes: List[Dict[str, Any]]) -> List[RealityCheck]:
        """
        Feed multiple reality outcomes at once.

        Args:
            outcomes: List of dicts with keys: trace_id, actual_pnl, actual_risk, actual_regime
        """
        checks = self.feedback_loop.check_reality_batch(outcomes)

        # Generate and apply deltas for low-quality predictions
        for check in checks:
            if check.prediction_quality < 0.8:
                delta = self.feedback_loop.generate_calibration_delta(check)
                self.feedback_loop.apply_calibration_delta(delta)

        return checks

    # ── Execution Callback ────────────────────────────────────────────────

    def set_execution_callback(self, callback: Callable[[DecisionTrace], None]):
        """
        Set the callback that receives decision traces for execution.

        The callback is invoked every time the COS makes a decision.
        It's the bridge between "thinking" and "doing".
        """
        self._execution_callback = callback
        logger.info("Execution callback set")

    # ── External System Connections ────────────────────────────────────────

    def connect_cognitive_core(self, core):
        """
        Connect to the existing AlphaAlgoCognitiveCore.

        This allows the COS to receive market state from the
        cognitive architecture's perception layer.
        """
        self._cognitive_core = core
        logger.info("Connected CognitiveCore")

    def connect_world_model(self, orchestrator):
        """
        Connect to the existing SimulationOrchestrator.

        This upgrades the COS's simulation from statistical
        to full world-model-based simulation.
        """
        self._world_model_orchestrator = orchestrator
        self.simulation_engine.connect_world_model(orchestrator)
        logger.info("Connected WorldModel orchestrator")

    def connect_decision_engine(self, engine):
        """
        Connect to the existing InnovativeDecisionEngine.

        This allows the COS to leverage the 110 decision concepts
        for richer decision-making.
        """
        self._decision_engine = engine
        self.decision_support.connect_decision_engine(engine)
        logger.info("Connected InnovativeDecisionEngine")

    def connect_feedback_analyzer(self, analyzer):
        """
        Connect to the existing FeedbackAnalyzer.

        This allows the COS to automatically ingest trade
        performance data for reality checking.
        """
        self._feedback_analyzer = analyzer
        self.feedback_loop.connect_feedback_analyzer(analyzer)
        logger.info("Connected FeedbackAnalyzer")

    def connect_all(
        self,
        cognitive_core=None,
        world_model=None,
        decision_engine=None,
        feedback_analyzer=None,
    ):
        """Connect all external systems at once."""
        if cognitive_core is not None:
            self.connect_cognitive_core(cognitive_core)
        if world_model is not None:
            self.connect_world_model(world_model)
        if decision_engine is not None:
            self.connect_decision_engine(decision_engine)
        if feedback_analyzer is not None:
            self.connect_feedback_analyzer(feedback_analyzer)

    # ── Knowledge Ingestion ────────────────────────────────────────────────

    def ingest_knowledge(self, node: KnowledgeNode) -> str:
        """Directly ingest a knowledge node into the Cognition Store."""
        return self.cognition_store.ingest(node)

    def ingest_knowledge_batch(self, nodes: List[KnowledgeNode]) -> List[str]:
        """Ingest multiple knowledge nodes."""
        return self.cognition_store.ingest_batch(nodes)

    def ingest_trade_result(
        self,
        strategy: str,
        symbol: str,
        pnl: float,
        risk: float,
        regime: str,
        insights: Optional[str] = None,
    ):
        """
        Ingest a trade result as knowledge.

        Creates a structured knowledge node from a trade outcome
        and stores it in the Cognition Store.
        """
        node = KnowledgeNode(
            category=KnowledgeCategory.STRATEGY_PERFORMANCE,
            title=f"Trade: {strategy} on {symbol}",
            content=f"PnL={pnl:.4f}, Risk={risk:.4f}, Regime={regime}. "
                    f"{insights or ''}",
            structured_data={
                "strategy": strategy,
                "symbol": symbol,
                "pnl": pnl,
                "risk": risk,
                "regime": regime,
                "profitable": pnl > 0,
            },
            source="real_trade",
            salience=0.7 if pnl > 0 else 0.9,  # losses are more salient (lesson potential)
        )
        return self.cognition_store.ingest(node)

    # ── Query Interface ────────────────────────────────────────────────────

    def query_knowledge(
        self,
        query: str,
        top_k: int = 5,
        category: Optional[KnowledgeCategory] = None,
    ) -> List[Tuple[KnowledgeNode, float]]:
        """
        Query the Cognition Store by text.

        Uses a simple embedding of the query text to find
        semantically relevant knowledge.
        """
        query_emb = self._text_to_embedding(query)
        return self.cognition_store.recall(
            query_emb, top_k=top_k, category=category
        )

    def get_decision_trace(self, trace_id: str) -> Optional[DecisionTrace]:
        """Retrieve a specific decision trace by ID."""
        return self.decision_support._decision_history.get(trace_id)

    # ── Persistence ────────────────────────────────────────────────────────

    def save(self):
        """Persist the entire COS state."""
        self.cognition_store.save()
        logger.info("COS state saved")

    def load(self):
        """Load the COS state from persistence."""
        self.cognition_store.load()
        logger.info(f"COS state loaded | nodes={len(self.cognition_store._nodes)}")

    # ── Diagnostics ────────────────────────────────────────────────────────

    def health_check(self) -> Dict[str, Any]:
        """Comprehensive health check of all COS components."""
        return {
            "cycle_count": self._cycle_count,
            "is_running": self._is_running,
            "cognition_store": self.cognition_store.stats(),
            "simulation_engine": self.simulation_engine.stats(),
            "decision_support": self.decision_support.stats(),
            "feedback_loop": self.feedback_loop.stats(),
            "pending_decisions": len(self._pending_decisions),
            "execution_callback_set": self._execution_callback is not None,
            "external_connections": {
                "cognitive_core": self._cognitive_core is not None,
                "world_model": self._world_model_orchestrator is not None,
                "decision_engine": self._decision_engine is not None,
                "feedback_analyzer": self._feedback_analyzer is not None,
            },
        }

    def get_cycle_history(self, last_n: int = 10) -> List[Dict[str, Any]]:
        """Get the last N cycle reports as dicts."""
        reports = self._cycle_reports[-last_n:]
        return [
            {
                "cycle": r.cycle_number,
                "total_ms": r.total_cycle_ms,
                "ideas_generated": r.ideas_generated,
                "decisions_made": r.decisions_made,
                "reality_checks": r.reality_checks,
                "calibration_score": r.calibration_score,
                "knowledge_size": r.knowledge_store_size,
            }
            for r in reports
        ]

    # ── Internal Helpers ──────────────────────────────────────────────────

    def _context_to_embedding(self, context: Dict[str, Any]) -> np.ndarray:
        """
        Convert market context to an embedding vector for knowledge retrieval.

        Uses a deterministic hash-based projection. In production,
        this would use a trained encoder.
        """
        regime = context.get("regime", "normal")
        volatility = context.get("volatility", 0.01)
        trend = context.get("trend", 0.0)

        # Create a simple feature vector from context
        text = f"{regime} {volatility:.4f} {trend:.4f}"
        rng = np.random.RandomState(hash(text) % (2**31))
        emb = rng.randn(self.config.embedding_dim).astype(np.float32)
        emb /= (np.linalg.norm(emb) + 1e-8)
        return emb

    def _text_to_embedding(self, text: str) -> np.ndarray:
        """Convert text to embedding for knowledge queries."""
        rng = np.random.RandomState(hash(text) % (2**31))
        emb = rng.randn(self.config.embedding_dim).astype(np.float32)
        emb /= (np.linalg.norm(emb) + 1e-8)
        return emb

    def _process_pending_reality(self) -> List[RealityCheck]:
        """
        Check if any pending decisions have reality data available.

        In a live system, this would poll the execution layer for
        trade outcomes. Here we check the feedback analyzer.
        """
        checks = []

        if self._feedback_analyzer is not None:
            try:
                # Pull recent trade performances from the feedback analyzer
                recent = self._feedback_analyzer.get_recent_performance(limit=10)
                self.feedback_loop.ingest_trade_performance(recent)
            except Exception as e:
                logger.debug(f"Could not pull feedback data: {e}")

        return checks

    def _avg_fidelity(self) -> float:
        """Compute average simulation fidelity across all regimes."""
        fidelities = self.simulation_engine._regime_fidelity
        if not fidelities:
            return 0.0
        return float(np.mean([f.value for f in fidelities.values()]))
