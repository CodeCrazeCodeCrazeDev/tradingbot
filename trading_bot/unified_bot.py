"""
Unified Trading Bot — UCA-2026 single uniform system.

Consolidates the fragmented entry points (main_original.py, unified_main.py,
realtime_trading_core.py) into ONE bot: every module layer runs as a service
under a single decision authority — the CognitiveSystemController (CSC).

    market observation -> indicator enrichment (RSI etc.) -> CSC brain
        -> DiscoLoop -> PCA agents -> hypotheses -> verification swarm
        -> Immutable Shield -> LogAct consensus -> execution bridge
        -> evolution layer records the outcome

Layer modules (telemetry, evolution, human approval) are wired as services —
never as parallel decision-makers. Missing layers degrade gracefully.
"""

import asyncio
import logging
from collections import deque
from typing import Any, Dict, Iterator, Optional

import numpy as np

# Heavy layer imports (CSC, risk service, world model, execution) are deferred
# into start()/method bodies so `import trading_bot.unified_bot` stays cheap.
from trading_bot.core.immutable_shield import shield
from trading_bot.core.unified_event_bus import decision_bus
from trading_bot.core.unified_registry import registry
from trading_bot.data.normalizer import MarketDataNormalizer
from trading_bot.foundation.capability_registry import CapabilityRegistry
from trading_bot.strategies.registry import StrategyRegistry

logger = logging.getLogger(__name__)


def _rsi_signal(context: Dict[str, Any]) -> Dict[str, Any]:
    """RSI(14) momentum skill — Wilder smoothing via vectorized indicator."""
    rsi = context.get("rsi")
    if rsi is None:
        return {"action": "hold", "reason": "insufficient price history for RSI"}
    if rsi >= 70:
        return {"action": "sell_bias", "reason": f"RSI {rsi:.1f} overbought"}
    if rsi <= 30:
        return {"action": "buy_bias", "reason": f"RSI {rsi:.1f} oversold"}
    return {"action": "neutral", "reason": f"RSI {rsi:.1f} mid-range"}


class UnifiedTradingBot:
    """
    The single uniform trading bot. Composes all module layers under the CSC.

    Layers wired as services (fail-soft on import/availability):
      - telemetry   : metrics, health checks, tracing
      - evolution   : reward model + orchestrator (records trade experience)
      - human       : approval gate, alert manager, manual override
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self.execution_mode = str(
            self.config.get("execution_mode", self.config.get("mode", "paper"))
        ).lower()
        self._price_window: deque = deque(maxlen=int(self.config.get("rsi_window", 64)))
        self.data_normalizer = MarketDataNormalizer()
        self.strategy_registry = StrategyRegistry()
        self.capability_registry = CapabilityRegistry()
        self._shutdown = asyncio.Event()
        self.running = False
        self.layers: Dict[str, Any] = {}
        # Optional LOB feed (market_feeds.LOBFeed) — when wired, each cycle's
        # observation carries microstructure features the shield spread-guards on.
        self.lob_feed = self.config.get("lob_feed")

        # Set in start()
        self.hms: Optional[HierarchicalMemorySystem] = None
        self.world_model: Optional[WorldModelV2] = None
        self.skill_router: Optional[SkillRouter] = None
        self.verifier_swarm: Optional[VerificationSwarm] = None
        self.evolution_gate: Optional[EvolutionGate] = None
        self.risk_service: Optional[CanonicalRiskService] = None
        self.trading_repository: Optional[SqliteTradingRepository] = None
        self.execution_service: Optional[CanonicalExecutionService] = None
        self.bridge: Optional[PaperExecutionBridge] = None
        self.csc: Optional[CognitiveSystemController] = None

    async def start(self) -> None:
        """Boot all infrastructure and register components exactly once."""
        if self.running:
            return
        if self.execution_mode not in {"paper", "analysis"}:
            raise RuntimeError(
                f"Execution mode '{self.execution_mode}' is not wired to the canonical execution service; "
                "refusing to silently fall back to paper trading."
            )

        from trading_bot.core.csc.controller import CognitiveSystemController
        from trading_bot.core.csc.router import SkillRouter
        from trading_bot.core.execution_bridge import PaperExecutionBridge
        from trading_bot.core.hms.memory import HierarchicalMemorySystem
        from trading_bot.core.verification.swarm import VerificationSwarm
        from trading_bot.execution.service import CanonicalExecutionService
        from trading_bot.governance.evolution_gate import EvolutionGate
        from trading_bot.persistence.repositories import SqliteTradingRepository
        from trading_bot.risk.service import CanonicalRiskService, LegacyRiskPolicyAdapter
        from trading_bot.world_model.v2_core import WorldModelV2

        # 1. LogAct backbone
        await decision_bus.start()
        registry.register("decision_bus", decision_bus, "Infrastructure", overwrite=True)

        # 2. Hierarchical Memory System
        self.hms = HierarchicalMemorySystem(self.config)
        registry.register("hms", self.hms, "Core", overwrite=True)

        # 3. Immutable Shield — governance veto boundary
        shield.config.update({
            "max_exposure": self.config.get("max_exposure", 0.05),
            "max_quantity": self.config.get("max_quantity", 10.0),
            "trading_enabled": self.config.get("trading_enabled", True),
        })
        if self.config.get("max_spread_bps") is not None:
            shield.config["max_spread_bps"] = self.config["max_spread_bps"]
        registry.register("shield", shield, "Governance", overwrite=True)

        # 4. World model
        self.world_model = WorldModelV2(asset_dims={"FX": 64, "Equities": 128})
        registry.register("world_model", self.world_model, "Intelligence", overwrite=True)

        # 5. Data foundation and capability registries
        registry.register("market_data_normalizer", self.data_normalizer, "Data", overwrite=True)
        registry.register("strategy_registry", self.strategy_registry, "Strategy", overwrite=True)
        registry.register("capability_registry", self.capability_registry, "Intelligence", overwrite=True)
        self.skill_router = SkillRouter()
        self._register_signal_skills()
        registry.register("skill_router", self.skill_router, "Intelligence", overwrite=True)

        # 6. Governance + verification
        self.evolution_gate = EvolutionGate(validation_engine=None)
        self.verifier_swarm = VerificationSwarm()
        registry.register("evolution_gate", self.evolution_gate, "Governance", overwrite=True)
        registry.register("verification_swarm", self.verifier_swarm, "Governance", overwrite=True)
        if self.config.get("enable_debate_capability", False):
            from trading_bot.agents.capability_adapter import DebateCapabilityAdapter
            from trading_bot.agents.multi_agent_debate import MultiAgentDebateSystem

            debate_capability = DebateCapabilityAdapter(
                MultiAgentDebateSystem(self.config.get("debate_config", {}))
            )
            self.capability_registry.register(
                debate_capability,
                domain="debate",
                metadata={"advisory_only": True},
            )
            registry.register("debate_capability", debate_capability, "Intelligence", overwrite=True)

        # 7. Canonical portfolio risk authority
        self.risk_service = CanonicalRiskService({
            "max_exposure": self.config.get("max_exposure", 0.05),
            "max_quantity": self.config.get("max_quantity", 10.0),
            "max_drawdown": self.config.get("max_drawdown", 0.25),
        })
        if self.config.get("enable_legacy_risk_policies", False):
            from trading_bot.risk.pre_trade_checks import PreTradeChecksEngine

            legacy_policy = LegacyRiskPolicyAdapter(
                "pre_trade_checks",
                PreTradeChecksEngine(self.config.get("legacy_pre_trade_checks", {})),
            )
            self.risk_service.register_policy("pre_trade_checks", legacy_policy)
            registry.register("risk_policy_pre_trade_checks", legacy_policy, "Risk", overwrite=True)

            circuit_config = self.config.get("legacy_circuit_breaker")
            if circuit_config is not None:
                from trading_bot.risk.circuit_breaker import CircuitBreaker, CircuitBreakerConfig

                circuit_options = dict(circuit_config)
                initial_balance = float(circuit_options.pop("initial_balance", 0.0) or 0.0)
                breaker = CircuitBreaker(CircuitBreakerConfig(**circuit_options))
                if initial_balance <= 0:
                    raise ValueError("legacy_circuit_breaker.initial_balance must be positive")
                breaker.start_session(initial_balance)
                circuit_policy = LegacyRiskPolicyAdapter("circuit_breaker", breaker)
                self.risk_service.register_policy("circuit_breaker", circuit_policy)
                registry.register("risk_policy_circuit_breaker", circuit_policy, "Risk", overwrite=True)
        registry.register("portfolio_risk_service", self.risk_service, "Risk", overwrite=True)

        # 8. Authoritative typed repository, execution service, and compatibility bridge
        self.trading_repository = SqliteTradingRepository(
            self.config.get("trading_state_path", "alphaalgo_data/trading_state.db")
        )
        registry.register("trading_repository", self.trading_repository, "Persistence", overwrite=True)
        self.execution_service = CanonicalExecutionService(
            mode="paper", repository=self.trading_repository
        )
        registry.register("execution_service", self.execution_service, "Execution", overwrite=True)
        self.bridge = PaperExecutionBridge(execution_service=self.execution_service)
        self.bridge.attach(decision_bus)
        registry.register("execution_bridge", self.bridge, "Execution", overwrite=True)

        # 9. The One Brain
        self.csc = CognitiveSystemController(
            world_model=self.world_model,
            hms=self.hms,
            skill_router=self.skill_router,
            verifier_swarm=self.verifier_swarm,
            risk_engine=self.risk_service,
            consensus_engine=decision_bus,
            execution_planner=None,
            evolution_gate=self.evolution_gate,
            shield=shield,
        )
        registry.register("csc", self.csc, "Controller", overwrite=True)

        # 10. Module layers from the unified architecture (fail-soft)
        self._wire_optional_layers()

        self.running = True
        logger.info("UnifiedTradingBot: all core components initialized as one system")

    def _register_signal_skills(self) -> None:
        """Register indicator skills into the S2L/HASP router."""
        from trading_bot.core.csc.router import SkillArtifact, SkillType

        self.skill_router.register_skill(SkillArtifact(
            skill_id="rsi_signal",
            skill_type=SkillType.PROGRAM,
            version="1.0.0",
            executable=_rsi_signal,
            capabilities={"momentum", "mean_reversion", "signal"},
            metadata={"description": "RSI(14) momentum signal from observed prices"},
        ))

    def _wire_optional_layers(self) -> None:
        """Wire telemetry/evolution/human layers as services if importable."""
        try:
            from trading_bot.telemetry import get_metrics_collector, get_health_checker
            self.layers["telemetry"] = {
                "metrics": get_metrics_collector(),
                "health": get_health_checker(),
            }
            registry.register("telemetry_metrics", self.layers["telemetry"]["metrics"], "Observability", overwrite=True)
            registry.register("telemetry_health", self.layers["telemetry"]["health"], "Observability", overwrite=True)
        except Exception as exc:
            logger.warning(f"UnifiedTradingBot: telemetry layer unavailable: {exc}")

        try:
            from trading_bot.evolution_layer import (
                get_reward_model, get_evolution_orchestrator, record_trade_experience,
            )
            self.layers["evolution"] = {
                "reward_model": get_reward_model(),
                "orchestrator": get_evolution_orchestrator(self.config),
                "record_experience": record_trade_experience,
            }
            registry.register("evolution_reward_model", self.layers["evolution"]["reward_model"], "Learning", overwrite=True)
            registry.register("evolution_service", self.layers["evolution"]["orchestrator"], "Learning", overwrite=True)
        except Exception as exc:
            logger.warning(f"UnifiedTradingBot: evolution layer unavailable: {exc}")

        try:
            from trading_bot.governance.policy_adapter import HumanApprovalPolicy
            from trading_bot.human_layer import (
                get_approval_gate, get_alert_manager, is_trading_allowed,
            )
            self.layers["human"] = {
                "approval_gate": get_approval_gate(self.config),
                "alerts": get_alert_manager(self.config),
                "is_trading_allowed": is_trading_allowed,
            }
            registry.register("human_approval_gate", self.layers["human"]["approval_gate"], "Governance", overwrite=True)
            registry.register(
                "human_approval_policy",
                HumanApprovalPolicy(self.layers["human"]["approval_gate"]),
                "Governance",
                overwrite=True,
            )
            registry.register("human_alert_manager", self.layers["human"]["alerts"], "Observability", overwrite=True)
        except Exception as exc:
            logger.warning(f"UnifiedTradingBot: human layer unavailable: {exc}")

    def enrich_observation(self, obs: Dict[str, Any]) -> Dict[str, Any]:
        """Derive indicator features from the rolling price window."""
        price = obs.get("price", obs.get("close"))
        if price is not None:
            self._price_window.append(float(price))

        if len(self._price_window) >= 15:
            prices = np.asarray(self._price_window, dtype=np.float64)
            obs["rsi"] = float(rsi_fast(prices, period=14)[-1])
            obs["rsi_signal"] = _rsi_signal(obs)
            returns = np.diff(prices) / np.clip(prices[:-1], 1e-12, None)
            obs.setdefault("volatility", float(np.std(returns)))
            obs.setdefault("trend", "UP" if prices[-1] > prices[0] else ("DOWN" if prices[-1] < prices[0] else "FLAT"))
        return obs

    def trading_allowed(self) -> bool:
        human = self.layers.get("human")
        if human is None:
            return True
        try:
            return bool(human["is_trading_allowed"]())
        except Exception:
            return True

    def register_strategy_adapter(self, strategy: Any, *, metadata: Optional[Dict[str, Any]] = None) -> Any:
        """Register a signal-only strategy capability in the canonical graph."""
        registration = self.strategy_registry.register(strategy, metadata=metadata)
        registry.register(
            f"strategy_{registration.strategy_id}",
            strategy,
            "Strategy",
            metadata=dict(metadata or {}),
            overwrite=True,
        )
        return registration

    def component_graph(self) -> list:
        """Return the canonical modular-monolith component inventory."""
        return registry.list_components()

    async def health_check(self) -> Dict[str, Any]:
        """Return component health without creating a second lifecycle owner."""
        health = await registry.health_check_all()
        return {
            "running": self.running,
            "components": {
                name: {
                    "status": result.status.value,
                    "message": result.message,
                    "warnings": result.warnings,
                    "errors": result.errors,
                }
                for name, result in health.items()
            },
        }

    async def run_cycle(self, observation: Dict[str, Any]) -> Any:
        """One unified cycle: normalize -> enrich -> brain -> feedback."""
        raw_observation = dict(observation)
        try:
            market_event = self.data_normalizer.normalize(
                raw_observation,
                symbol=raw_observation.get("symbol") or self.config.get("symbol") or "UNKNOWN",
                source=self.config.get("data_source", "runtime"),
            )
        except (TypeError, ValueError) as exc:
            logger.warning("UnifiedTradingBot: invalid market observation: %s", exc)
            return None

        if market_event.quality.value == "invalid":
            logger.warning(
                "UnifiedTradingBot: rejecting invalid market event for %s",
                market_event.instrument.symbol,
            )
            return None

        obs = self.enrich_observation(raw_observation)
        obs["market_event_id"] = market_event.event_id
        obs["data_quality"] = market_event.quality.value

        # Attach live microstructure when a LOB feed is wired — the Immutable
        # Shield's spread guard reads spread_bps from this context.
        if self.lob_feed is not None:
            try:
                snap = await self.lob_feed.next()
                if snap is not None and hasattr(snap, "features"):
                    obs["microstructure"] = snap.features()
            except Exception as exc:
                logger.debug(f"UnifiedTradingBot: LOB feed unavailable this cycle: {exc}")

        strategy_id = self.config.get("strategy_id")
        if strategy_id:
            try:
                signals = await self.strategy_registry.generate_signals(strategy_id, obs)
                obs["strategy_signals"] = [signal.to_dict() for signal in signals]
                obs["strategy_advisory_only"] = True
            except Exception as exc:
                logger.warning("UnifiedTradingBot: strategy capability failed closed: %s", exc)
                obs["strategy_signals"] = []
                obs["strategy_advisory_only"] = True

        if not self.trading_allowed():
            logger.info("UnifiedTradingBot: trading paused by human override")
            return None

        decision = await self.csc.process_market_observation(obs)

        evolution = self.layers.get("evolution")
        if evolution is not None and decision is not None:
            try:
                evolution["record_experience"]({
                    "observation": obs,
                    "decision": getattr(decision, "outcome", decision),
                })
            except Exception as exc:
                logger.debug(f"UnifiedTradingBot: experience record failed: {exc}")

        return decision

    async def run(self, observations: Iterator[Dict[str, Any]],
                  cycles: int = 0, interval: float = 1.0) -> None:
        """Main loop over an observation source (replay, live feed, synthetic)."""
        await self.start()
        cycle = 0
        try:
            for obs in observations:
                if self._shutdown.is_set() or (0 < cycles <= cycle):
                    break
                decision = await self.run_cycle(obs)
                if decision is not None:
                    logger.info(
                        "Cycle %d decision: %s (%s)", cycle,
                        getattr(decision, "outcome", "?"),
                        getattr(decision, "dominant_rejection_reason", "") or "",
                    )
                cycle += 1
                if interval > 0:
                    await asyncio.sleep(interval)
        finally:
            await self.stop()

    async def stop(self) -> None:
        if not self.running:
            return
        self._shutdown.set()
        evolution = self.layers.get("evolution")
        if evolution is not None:
            try:
                await evolution["orchestrator"].stop()
            except Exception:
                pass
        if self.bridge is not None:
            logger.info("Paper execution summary: %s", self.bridge.get_summary())
        if self.trading_repository is not None:
            self.trading_repository.close()
        await decision_bus.stop()
        self.running = False
        logger.info("UnifiedTradingBot: shutdown complete")
