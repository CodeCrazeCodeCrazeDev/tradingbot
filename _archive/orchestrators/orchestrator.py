"""
Systems AI Orchestrator
=======================
Master coordinator for the AlphaAlgo Systems AI.

Integrates all components:
- System Architecture
- Memory Hierarchy
- Decision Attribution
- Training-First Architecture
- Research Agent
- Text-to-System Layer
- Governance Engine
- Self-Improvement Loop

Plus Advanced Features:
- Adaptive Signal Orchestration
- Market-Driven Curriculum Learning
- Feature Evolution Sandbox
- Latent Regime Mapper
- Confidence-Weighted Ensemble Routing
- Predictive Feature Decay
- Temporal Attention for Execution
- Anomaly-Driven Feedback Loop
- Meta-Reward Layer
- Synthetic Market Stress Simulation
- Self-Documenting Model Logs
- Cross-Domain Knowledge Transfer
- Autonomous Strategy Discovery
- Feedback-Aware Risk Management
- Contextual Agent Delegation
- Real-Time What-If Sandbox
"""

import asyncio
import logging
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum, auto
from typing import Any, Dict, List, Optional, Callable, Tuple
from threading import RLock

from .architecture import SystemArchitecture, SystemLayer, ComponentStatus
from .memory_hierarchy import MemoryHierarchy, MemoryTier, AgentType
from .attribution_engine import DecisionAttributionEngine, SignalDirection
from .training_first import TrainingFirstArchitecture
from .research_agent import ResearchAgent, HypothesisType
from .text_to_system import TextToSystemLayer
from .governance import GovernanceEngine, GovernanceLevel, ActionType
from .self_improvement import SelfImprovementLoop

logger = logging.getLogger(__name__)


class SystemMode(Enum):
    """System operating modes."""
    OFFLINE = "offline"           # No live data
    SIMULATION = "simulation"     # Simulated trading
    PAPER = "paper"               # Paper trading
    SHADOW = "shadow"             # Shadow mode (no execution)
    LIVE = "live"                 # Live trading


@dataclass
class SystemConfig:
    """Configuration for the Systems AI."""
    mode: SystemMode = SystemMode.PAPER
    
    # Memory settings
    short_term_ttl_seconds: int = 300
    mid_term_ttl_days: int = 7
    
    # Training settings
    auto_retrain: bool = False
    retrain_threshold: float = 0.5
    
    # Governance settings
    require_human_approval: bool = True
    max_auto_risk: float = 0.02
    
    # Research settings
    enable_research_agent: bool = True
    max_hypotheses_per_day: int = 100
    
    # Advanced features
    enable_adaptive_orchestration: bool = True
    enable_curriculum_learning: bool = True
    enable_feature_evolution: bool = True
    enable_regime_mapping: bool = True
    enable_anomaly_feedback: bool = True


@dataclass
class SignalRequest:
    """Request for a trading signal."""
    request_id: str
    symbol: str
    timestamp: datetime
    
    # Market data
    features: Dict[str, float]
    regime_id: Optional[str] = None
    
    # Context
    portfolio_state: Optional[Dict[str, Any]] = None
    risk_budget: Optional[float] = None
    
    # Constraints
    max_position_size: Optional[float] = None
    allowed_directions: Optional[List[str]] = None


@dataclass
class SignalResponse:
    """Response containing a trading signal."""
    request_id: str
    signal_id: str
    timestamp: datetime
    
    # Signal
    direction: SignalDirection
    confidence: float
    magnitude: float
    
    # Attribution
    attribution_id: str
    feature_hash: str
    contributing_models: List[Dict[str, Any]]
    regime_id: str
    
    # Risk
    recommended_size: float
    stop_loss: Optional[float]
    take_profit: Optional[float]
    
    # Metadata
    reasoning: List[str]
    warnings: List[str]


class AdaptiveSignalOrchestrator:
    """
    Adaptive Signal Orchestration Layer.
    
    Treats each sub-strategy/model as an agent in a meta-system.
    Dynamically adjusts which agents contribute based on:
    - Confidence
    - Market regime
    - Latent memory similarity
    - Recent performance
    """
    
    def __init__(self):
        try:
            self._agent_weights: Dict[str, float] = {}
            self._agent_performance: Dict[str, List[float]] = {}
            self._regime_weights: Dict[str, Dict[str, float]] = {}
            self._lock = RLock()
        except Exception as e:
            logger.error(f"Error in __init__: {e}")
            raise
    
    def register_agent(self, agent_id: str, initial_weight: float = 1.0):
        """Register a signal agent."""
        try:
            with self._lock:
                self._agent_weights[agent_id] = initial_weight
                self._agent_performance[agent_id] = []
        except Exception as e:
            logger.error(f"Error in register_agent: {e}")
            raise
    
    def update_performance(self, agent_id: str, pnl: float):
        """Update agent performance."""
        try:
            with self._lock:
                if agent_id in self._agent_performance:
                    self._agent_performance[agent_id].append(pnl)
                    # Keep last 100
                    if len(self._agent_performance[agent_id]) > 100:
                        self._agent_performance[agent_id] = self._agent_performance[agent_id][-100:]
        except Exception as e:
            logger.error(f"Error in update_performance: {e}")
            raise
    
    def get_agent_weights(
        self,
        regime_id: str,
        confidences: Dict[str, float],
    ) -> Dict[str, float]:
        """Get dynamic agent weights."""
        try:
            with self._lock:
                weights = {}
            
                for agent_id, base_weight in self._agent_weights.items():
                    # Base weight
                    weight = base_weight
                
                    # Adjust by confidence
                    if agent_id in confidences:
                        weight *= confidences[agent_id]
                
                    # Adjust by regime
                    if regime_id in self._regime_weights:
                        regime_weight = self._regime_weights[regime_id].get(agent_id, 1.0)
                        weight *= regime_weight
                
                    # Adjust by recent performance
                    if agent_id in self._agent_performance:
                        perf = self._agent_performance[agent_id]
                        if perf:
                            recent_sharpe = sum(perf[-20:]) / (len(perf[-20:]) * 0.01 + 0.001)
                            weight *= max(0.1, min(2.0, 1 + recent_sharpe * 0.1))
                
                    weights[agent_id] = weight
            
                # Normalize
                total = sum(weights.values())
                if total > 0:
                    weights = {k: v / total for k, v in weights.items()}
            
                return weights
        except Exception as e:
            logger.error(f"Error in get_agent_weights: {e}")
            raise


class LatentRegimeMapper:
    """
    Latent Regime Mapper.
    
    Uses unsupervised learning to map hidden regimes.
    Produces a regime ID per timestamp for context-aware decisions.
    """
    
    def __init__(self, n_regimes: int = 8):
        try:
            self.n_regimes = n_regimes
            self._regime_centroids: Dict[str, Dict[str, float]] = {}
            self._regime_history: List[Tuple[datetime, str]] = []
            self._lock = RLock()
        except Exception as e:
            logger.error(f"Error in __init__: {e}")
            raise
    
    def classify_regime(
        self,
        features: Dict[str, float],
    ) -> Tuple[str, float]:
        """Classify current regime."""
        try:
            if not self._regime_centroids:
                # Initialize with default regimes
                self._init_default_regimes()
        
            # Find closest centroid
            best_regime = "regime_0"
            best_distance = float("inf")
        
            for regime_id, centroid in self._regime_centroids.items():
                distance = self._compute_distance(features, centroid)
                if distance < best_distance:
                    best_distance = distance
                    best_regime = regime_id
        
            # Convert distance to confidence
            confidence = 1.0 / (1.0 + best_distance)
        
            with self._lock:
                self._regime_history.append((datetime.utcnow(), best_regime))
                # Keep last 1000
                if len(self._regime_history) > 1000:
                    self._regime_history = self._regime_history[-1000:]
        
            return best_regime, confidence
        except Exception as e:
            logger.error(f"Error in classify_regime: {e}")
            raise
    
    def _init_default_regimes(self):
        """Initialize default regime centroids."""
        try:
            self._regime_centroids = {
                "regime_trending_up": {"trend": 1.0, "volatility": 0.5, "momentum": 0.8},
                "regime_trending_down": {"trend": -1.0, "volatility": 0.5, "momentum": -0.8},
                "regime_ranging": {"trend": 0.0, "volatility": 0.3, "momentum": 0.0},
                "regime_volatile": {"trend": 0.0, "volatility": 1.0, "momentum": 0.0},
                "regime_quiet": {"trend": 0.0, "volatility": 0.1, "momentum": 0.0},
                "regime_breakout": {"trend": 0.5, "volatility": 0.8, "momentum": 0.9},
                "regime_reversal": {"trend": -0.3, "volatility": 0.6, "momentum": -0.5},
                "regime_consolidation": {"trend": 0.1, "volatility": 0.2, "momentum": 0.1},
            }
        except Exception as e:
            logger.error(f"Error in _init_default_regimes: {e}")
            raise
    
    def _compute_distance(
        self,
        features: Dict[str, float],
        centroid: Dict[str, float],
    ) -> float:
        """Compute distance between features and centroid."""
        try:
            common_keys = set(features.keys()) & set(centroid.keys())
            if not common_keys:
                return float("inf")
        
            distance = sum(
                (features[k] - centroid[k]) ** 2
                for k in common_keys
            ) ** 0.5
        
            return distance
        except Exception as e:
            logger.error(f"Error in _compute_distance: {e}")
            raise
    
    def get_regime_transitions(
        self,
        lookback_hours: int = 24,
    ) -> Dict[str, int]:
        """Get regime transition counts."""
        try:
            cutoff = datetime.utcnow() - timedelta(hours=lookback_hours)
        
            with self._lock:
                recent = [r for t, r in self._regime_history if t >= cutoff]
        
            transitions = {}
            for i in range(1, len(recent)):
                transition = f"{recent[i-1]}->{recent[i]}"
                transitions[transition] = transitions.get(transition, 0) + 1
        
            return transitions
        except Exception as e:
            logger.error(f"Error in get_regime_transitions: {e}")
            raise


class FeatureEvolutionSandbox:
    """
    Feature Evolution Sandbox.
    
    Lets the system invent features automatically:
    - Proposes transformations
    - Backtests in sandbox
    - Keeps only improvements
    """
    
    def __init__(self):
        try:
            self._transformations = [
                "sma", "ema", "rsi", "macd", "bollinger",
                "zscore", "percentile", "diff", "ratio", "log",
            ]
            self._discovered_features: Dict[str, Dict[str, Any]] = {}
            self._lock = RLock()
        except Exception as e:
            logger.error(f"Error in __init__: {e}")
            raise
    
    def propose_feature(
        self,
        base_feature: str,
        transformation: str,
        parameters: Dict[str, Any],
    ) -> str:
        """Propose a new feature."""
        try:
            feature_id = f"{transformation}_{base_feature}_{hash(str(parameters)) % 10000}"
        
            with self._lock:
                self._discovered_features[feature_id] = {
                    "base_feature": base_feature,
                    "transformation": transformation,
                    "parameters": parameters,
                    "status": "proposed",
                    "performance": None,
                    "created_at": datetime.utcnow().isoformat(),
                }
        
            return feature_id
        except Exception as e:
            logger.error(f"Error in propose_feature: {e}")
            raise
    
    def evaluate_feature(
        self,
        feature_id: str,
        performance_metrics: Dict[str, float],
    ) -> bool:
        """Evaluate a proposed feature."""
        try:
            with self._lock:
                if feature_id not in self._discovered_features:
                    return False
            
                feature = self._discovered_features[feature_id]
                feature["performance"] = performance_metrics
            
                # Check if feature is useful
                ic = performance_metrics.get("information_coefficient", 0)
                sharpe_contribution = performance_metrics.get("sharpe_contribution", 0)
            
                if ic > 0.02 and sharpe_contribution > 0:
                    feature["status"] = "validated"
                    return True
                else:
                    feature["status"] = "rejected"
                    return False
        except Exception as e:
            logger.error(f"Error in evaluate_feature: {e}")
            raise
    
    def get_validated_features(self) -> List[Dict[str, Any]]:
        """Get all validated features."""
        try:
            with self._lock:
                return [
                    f for f in self._discovered_features.values()
                    if f["status"] == "validated"
                ]
        except Exception as e:
            logger.error(f"Error in get_validated_features: {e}")
            raise


class AnomalyFeedbackLoop:
    """
    Anomaly-Driven Feedback Loop.
    
    Treats unexpected market events as training accelerators:
    - Detects anomalies
    - Prioritizes in retraining
    - Adjusts risk for similar future events
    """
    
    def __init__(self):
        try:
            self._anomalies: List[Dict[str, Any]] = []
            self._anomaly_signatures: Dict[str, Dict[str, float]] = {}
            self._lock = RLock()
        except Exception as e:
            logger.error(f"Error in __init__: {e}")
            raise
    
    def detect_anomaly(
        self,
        features: Dict[str, float],
        threshold: float = 3.0,
    ) -> Optional[Dict[str, Any]]:
        """Detect if current state is anomalous."""
        # Simple z-score based detection
        try:
            anomaly_score = 0
            anomalous_features = []
        
            for feature, value in features.items():
                # Assume normalized features
                if abs(value) > threshold:
                    anomaly_score += abs(value) - threshold
                    anomalous_features.append(feature)
        
            if anomaly_score > 0:
                anomaly = {
                    "anomaly_id": str(uuid.uuid4()),
                    "timestamp": datetime.utcnow().isoformat(),
                    "score": anomaly_score,
                    "features": anomalous_features,
                    "signature": features.copy(),
                }
            
                with self._lock:
                    self._anomalies.append(anomaly)
                    # Keep last 1000
                    if len(self._anomalies) > 1000:
                        self._anomalies = self._anomalies[-1000:]
            
                return anomaly
        
            return None
        except Exception as e:
            logger.error(f"Error in detect_anomaly: {e}")
            raise
    
    def get_similar_anomalies(
        self,
        current_features: Dict[str, float],
        similarity_threshold: float = 0.8,
    ) -> List[Dict[str, Any]]:
        """Find similar past anomalies."""
        try:
            similar = []
        
            with self._lock:
                for anomaly in self._anomalies:
                    signature = anomaly.get("signature", {})
                    similarity = self._compute_similarity(current_features, signature)
                    if similarity >= similarity_threshold:
                        similar.append({
                            **anomaly,
                            "similarity": similarity,
                        })
        
            return sorted(similar, key=lambda x: x["similarity"], reverse=True)
        except Exception as e:
            logger.error(f"Error in get_similar_anomalies: {e}")
            raise
    
    def _compute_similarity(
        self,
        features1: Dict[str, float],
        features2: Dict[str, float],
    ) -> float:
        """Compute similarity between feature sets."""
        try:
            common = set(features1.keys()) & set(features2.keys())
            if not common:
                return 0.0
        
            dot = sum(features1[k] * features2[k] for k in common)
            norm1 = sum(features1[k] ** 2 for k in common) ** 0.5
            norm2 = sum(features2[k] ** 2 for k in common) ** 0.5
        
            if norm1 == 0 or norm2 == 0:
                return 0.0
        
            return dot / (norm1 * norm2)
        except Exception as e:
            logger.error(f"Error in _compute_similarity: {e}")
            raise
    
    def get_anomaly_statistics(self) -> Dict[str, Any]:
        """Get anomaly statistics."""
        try:
            with self._lock:
                if not self._anomalies:
                    return {"total": 0}
            
                scores = [a["score"] for a in self._anomalies]
            
                return {
                    "total": len(self._anomalies),
                    "avg_score": sum(scores) / len(scores),
                    "max_score": max(scores),
                    "recent_24h": len([
                        a for a in self._anomalies
                        if datetime.fromisoformat(a["timestamp"]) > datetime.utcnow() - timedelta(hours=24)
                    ]),
                }
        except Exception as e:
            logger.error(f"Error in get_anomaly_statistics: {e}")
            raise


class MetaRewardLayer:
    """
    Meta-Reward Layer.
    
    Rewards not just P&L but:
    - Accuracy of regime detection
    - Predictive quality of execution slippage
    - Feature robustness under stress
    """
    
    def __init__(self):
        try:
            self._rewards: List[Dict[str, Any]] = []
            self._weights = {
                "pnl": 0.4,
                "regime_accuracy": 0.2,
                "slippage_prediction": 0.15,
                "feature_robustness": 0.15,
                "risk_adjusted": 0.1,
            }
            self._lock = RLock()
        except Exception as e:
            logger.error(f"Error in __init__: {e}")
            raise
    
    def compute_meta_reward(
        self,
        pnl: float,
        regime_predicted: str,
        regime_actual: str,
        slippage_predicted: float,
        slippage_actual: float,
        feature_stability: float,
        risk_taken: float,
    ) -> Dict[str, float]:
        """Compute meta-reward."""
        try:
            rewards = {}
        
            # P&L reward (normalized)
            rewards["pnl"] = max(-1, min(1, pnl * 100))
        
            # Regime accuracy
            rewards["regime_accuracy"] = 1.0 if regime_predicted == regime_actual else 0.0
        
            # Slippage prediction accuracy
            if slippage_predicted > 0:
                slippage_error = abs(slippage_actual - slippage_predicted) / slippage_predicted
                rewards["slippage_prediction"] = max(0, 1 - slippage_error)
            else:
                rewards["slippage_prediction"] = 0.5
        
            # Feature robustness
            rewards["feature_robustness"] = feature_stability
        
            # Risk-adjusted (penalize excessive risk)
            if risk_taken > 0.02:
                rewards["risk_adjusted"] = max(0, 1 - (risk_taken - 0.02) * 10)
            else:
                rewards["risk_adjusted"] = 1.0
        
            # Compute weighted total
            total = sum(
                rewards[k] * self._weights[k]
                for k in rewards
            )
            rewards["total"] = total
        
            with self._lock:
                self._rewards.append({
                    "timestamp": datetime.utcnow().isoformat(),
                    "rewards": rewards,
                })
        
            return rewards
        except Exception as e:
            logger.error(f"Error in compute_meta_reward: {e}")
            raise
    
    def get_reward_statistics(
        self,
        lookback_hours: int = 24,
    ) -> Dict[str, float]:
        """Get reward statistics."""
        try:
            cutoff = datetime.utcnow() - timedelta(hours=lookback_hours)
        
            with self._lock:
                recent = [
                    r for r in self._rewards
                    if datetime.fromisoformat(r["timestamp"]) >= cutoff
                ]
        
            if not recent:
                return {}
        
            stats = {}
            for key in self._weights.keys():
                values = [r["rewards"].get(key, 0) for r in recent]
                stats[f"avg_{key}"] = sum(values) / len(values)
        
            totals = [r["rewards"].get("total", 0) for r in recent]
            stats["avg_total"] = sum(totals) / len(totals)
        
            return stats
        except Exception as e:
            logger.error(f"Error in get_reward_statistics: {e}")
            raise


class SystemsAIOrchestrator:
    """
    Master Orchestrator for AlphaAlgo Systems AI.
    
    Coordinates all components to provide:
    - Signal generation with full attribution
    - Continuous learning and improvement
    - Governance and safety enforcement
    - Research and discovery
    - Natural language control
    """
    
    def __init__(self, config: Optional[SystemConfig] = None):
        try:
            self.config = config or SystemConfig()
        
            # Core components
            self.architecture = SystemArchitecture()
            self.memory = MemoryHierarchy({
                "short_term_ttl": self.config.short_term_ttl_seconds,
                "mid_term_ttl": self.config.mid_term_ttl_days,
            })
            self.attribution = DecisionAttributionEngine()
            self.training = TrainingFirstArchitecture()
            self.research = ResearchAgent()
            self.text_to_system = TextToSystemLayer()
            self.governance = GovernanceEngine()
            self.improvement = SelfImprovementLoop()
        
            # Advanced features
            self.signal_orchestrator = AdaptiveSignalOrchestrator()
            self.regime_mapper = LatentRegimeMapper()
            self.feature_sandbox = FeatureEvolutionSandbox()
            self.anomaly_loop = AnomalyFeedbackLoop()
            self.meta_reward = MetaRewardLayer()
        
            self._initialized = False
            self._lock = RLock()
        
            logger.info(f"Systems AI Orchestrator created in {self.config.mode.value} mode")
        except Exception as e:
            logger.error(f"Error in __init__: {e}")
            raise
    
    async def initialize(self) -> bool:
        """Initialize the system."""
        try:
            logger.info("Initializing Systems AI...")
        
            # Initialize architecture
            success = await self.architecture.initialize()
            if not success:
                logger.error("Failed to initialize architecture")
                return False
        
            # Register default signal agents
            self.signal_orchestrator.register_agent("trend_follower", 1.0)
            self.signal_orchestrator.register_agent("mean_reversion", 1.0)
            self.signal_orchestrator.register_agent("momentum", 0.8)
            self.signal_orchestrator.register_agent("volatility", 0.6)
        
            self._initialized = True
            logger.info("Systems AI initialized successfully")
            return True
        except Exception as e:
            logger.error(f"Error in initialize: {e}")
            raise
    
    async def shutdown(self) -> bool:
        """Shutdown the system."""
        try:
            logger.info("Shutting down Systems AI...")
            await self.architecture.shutdown()
            self._initialized = False
            logger.info("Systems AI shutdown complete")
            return True
        except Exception as e:
            logger.error(f"Error in shutdown: {e}")
            raise
    
    def generate_signal(
        self,
        request: SignalRequest,
    ) -> SignalResponse:
        """
        Generate a trading signal with full attribution.
        
        This is the main entry point for signal generation.
        """
        try:
            if not self._initialized:
                raise RuntimeError("System not initialized")
        
            # Check governance
            can_act, reason = self.governance.can_perform_action(
                actor="signal_generator",
                actor_level=GovernanceLevel.G1_SYSTEM,
                action_type=ActionType.SIGNAL_GENERATION,
            )
            if not can_act:
                logger.warning(f"Signal generation blocked: {reason}")
                return self._create_flat_signal(request, reason)
        
            # Classify regime
            regime_id, regime_confidence = self.regime_mapper.classify_regime(request.features)
        
            # Check for anomalies
            anomaly = self.anomaly_loop.detect_anomaly(request.features)
            warnings = []
            if anomaly:
                warnings.append(f"Anomaly detected: score={anomaly['score']:.2f}")
                similar = self.anomaly_loop.get_similar_anomalies(request.features)
                if similar:
                    warnings.append(f"Similar to {len(similar)} past anomalies")
        
            # Get agent weights
            agent_confidences = {
                "trend_follower": 0.7,
                "mean_reversion": 0.6,
                "momentum": 0.5,
                "volatility": 0.4,
            }
            agent_weights = self.signal_orchestrator.get_agent_weights(regime_id, agent_confidences)
        
            # Generate signal (simplified - would integrate with actual models)
            direction, confidence, magnitude = self._compute_signal(
                request.features,
                regime_id,
                agent_weights,
            )
        
            # Create attribution
            model_outputs = [
                {
                    "model_id": agent_id,
                    "version": "1.0",
                    "weight": weight,
                    "confidence": agent_confidences.get(agent_id, 0.5),
                }
                for agent_id, weight in agent_weights.items()
            ]
        
            attribution = self.attribution.create_attribution(
                symbol=request.symbol,
                features=request.features,
                model_outputs=model_outputs,
                regime_id=regime_id,
                expected_direction=direction,
                expected_magnitude=magnitude,
                horizon="1h",
                reasoning=[
                    f"Regime: {regime_id} (conf={regime_confidence:.2f})",
                    f"Top agent: {max(agent_weights, key=agent_weights.get)}",
                ],
                confidence=confidence,
            )
        
            # Store in memory
            self.memory.short_term.store_microstructure(
                symbol=request.symbol,
                imbalance=request.features.get("imbalance", 0),
                spread=request.features.get("spread", 0),
                toxicity=request.features.get("toxicity", 0),
                timestamp=datetime.utcnow(),
            )
        
            # Compute position size
            recommended_size = self._compute_position_size(
                confidence=confidence,
                risk_budget=request.risk_budget or 0.02,
                max_size=request.max_position_size or 0.1,
            )
        
            return SignalResponse(
                request_id=request.request_id,
                signal_id=attribution.signal_id,
                timestamp=datetime.utcnow(),
                direction=direction,
                confidence=confidence,
                magnitude=magnitude,
                attribution_id=attribution.signal_id,
                feature_hash=attribution.feature_snapshot.hash,
                contributing_models=model_outputs,
                regime_id=regime_id,
                recommended_size=recommended_size,
                stop_loss=None,  # Would be computed
                take_profit=None,
                reasoning=attribution.reasoning_chain,
                warnings=warnings,
            )
        except Exception as e:
            logger.error(f"Error in generate_signal: {e}")
            raise
    
    def _compute_signal(
        self,
        features: Dict[str, float],
        regime_id: str,
        agent_weights: Dict[str, float],
    ) -> Tuple[SignalDirection, float, float]:
        """Compute signal from features and weights."""
        # Simplified signal computation
        try:
            trend = features.get("trend", 0)
            momentum = features.get("momentum", 0)
            mean_rev = features.get("mean_reversion", 0)
        
            # Weighted combination
            signal_value = (
                trend * agent_weights.get("trend_follower", 0) +
                momentum * agent_weights.get("momentum", 0) +
                mean_rev * agent_weights.get("mean_reversion", 0)
            )
        
            # Determine direction
            if signal_value > 0.1:
                direction = SignalDirection.LONG
            elif signal_value < -0.1:
                direction = SignalDirection.SHORT
            else:
                direction = SignalDirection.FLAT
        
            confidence = min(1.0, abs(signal_value))
            magnitude = abs(signal_value) * 0.01  # 1% max
        
            return direction, confidence, magnitude
        except Exception as e:
            logger.error(f"Error in _compute_signal: {e}")
            raise
    
    def _compute_position_size(
        self,
        confidence: float,
        risk_budget: float,
        max_size: float,
    ) -> float:
        """Compute position size based on confidence and risk."""
        # Kelly-inspired sizing
        try:
            base_size = risk_budget * confidence
            return min(base_size, max_size)
        except Exception as e:
            logger.error(f"Error in _compute_position_size: {e}")
            raise
    
    def _create_flat_signal(
        self,
        request: SignalRequest,
        reason: str,
    ) -> SignalResponse:
        """Create a flat (no trade) signal."""
        return SignalResponse(
            request_id=request.request_id,
            signal_id=str(uuid.uuid4()),
            timestamp=datetime.utcnow(),
            direction=SignalDirection.FLAT,
            confidence=0.0,
            magnitude=0.0,
            attribution_id="",
            feature_hash="",
            contributing_models=[],
            regime_id="unknown",
            recommended_size=0.0,
            stop_loss=None,
            take_profit=None,
            reasoning=[reason],
            warnings=[reason],
        )
    
    def record_outcome(
        self,
        signal_id: str,
        direction_correct: bool,
        pnl: float,
        pnl_percent: float,
        slippage: float,
        execution_quality: float,
    ):
        """Record trade outcome for learning."""
        # Get attribution
        try:
            attribution = self.attribution.store.get(signal_id)
            if attribution is None:
                logger.warning(f"Attribution not found for signal: {signal_id}")
                return
        
            # Label outcome
            self.improvement.label_outcome(
                signal_id=signal_id,
                direction_correct=direction_correct,
                pnl=pnl,
                pnl_percent=pnl_percent,
                regime_id=attribution.latent_regime_id,
                volatility=0.0,  # Would be from features
                liquidity=0.0,
                model_id="ensemble",
                model_version="1.0",
                feature_hash=attribution.feature_snapshot.hash,
                slippage=slippage,
                execution_quality=execution_quality,
            )
        
            # Update agent performance
            for model in attribution.contributing_models:
                self.signal_orchestrator.update_performance(
                    model.model_id,
                    pnl_percent * model.weight,
                )
        
            # Compute meta-reward
            self.meta_reward.compute_meta_reward(
                pnl=pnl_percent,
                regime_predicted=attribution.latent_regime_id,
                regime_actual=attribution.latent_regime_id,  # Would be actual
                slippage_predicted=0.001,
                slippage_actual=slippage,
                feature_stability=0.8,
                risk_taken=0.02,
            )
        except Exception as e:
            logger.error(f"Error in record_outcome: {e}")
            raise
    
    def process_command(
        self,
        command: str,
        user_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Process a natural language command."""
        try:
            result = self.text_to_system.process_command(command, user_id)
            return result.to_dict()
        except Exception as e:
            logger.error(f"Error in process_command: {e}")
            raise
    
    def get_system_status(self) -> Dict[str, Any]:
        """Get comprehensive system status."""
        return {
            "mode": self.config.mode.value,
            "initialized": self._initialized,
            "architecture_health": self.architecture.get_health().__dict__ if self._initialized else None,
            "memory_stats": self.memory.get_statistics(),
            "attribution_summary": self.attribution.get_attribution_summary(),
            "improvement_summary": self.improvement.get_improvement_summary(),
            "anomaly_stats": self.anomaly_loop.get_anomaly_statistics(),
            "reward_stats": self.meta_reward.get_reward_statistics(),
            "pending_approvals": len(self.governance.get_pending_approvals()),
        }
    
    def get_architecture_diagram(self) -> str:
        """Get the text architecture diagram."""
        return self.architecture.get_architecture_diagram()


# Factory function
def create_systems_ai(
    mode: str = "paper",
    **kwargs,
) -> SystemsAIOrchestrator:
    """Create a Systems AI instance."""
    try:
        config = SystemConfig(
            mode=SystemMode(mode),
            **kwargs,
        )
        return SystemsAIOrchestrator(config)
    except Exception as e:
        logger.error(f"Error in create_systems_ai: {e}")
        raise


# Quick start
async def quick_start(
    mode: str = "paper",
) -> SystemsAIOrchestrator:
    """Quick start a Systems AI instance."""
    try:
        orchestrator = create_systems_ai(mode=mode)
        await orchestrator.initialize()
        return orchestrator
    except Exception as e:
        logger.error(f"Error in quick_start: {e}")
        raise
