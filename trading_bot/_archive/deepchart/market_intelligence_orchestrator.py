"""
DeepChart Market Intelligence Orchestrator

Master coordinator integrating all 15 mandatory concepts into ONE coherent system.

UNIFIED CONCEPTS:
1. Market Micro-Friction Map
2. Latent Market State Background
3. Time-to-Move Predictor
4. Synthetic Liquidity Shadows
5. Volume Entropy Tracker
6. Market Memory Decay Map
7. Execution Quality Forecast Layer
8. Micro-Trend Vectors
9. Liquidity Vacuum Detector
10. Model Disagreement Heatmap
11. Price Response Curvature Map
12. Learned Support/Resistance
13. Information Flow Speedometer
14. Strategy-Specific Views
15. Confidence-Weighted Overlays

PERFORMANCE BUDGET:
- Max inference latency: <5ms per symbol
- Max RAM per symbol: <500KB
- Max storage per day: <20MB
- ONNX exportable, CPU-first

Author: AlphaAlgo Market Intelligence System
"""

import numpy as np
from dataclasses import dataclass
from typing import Dict, List, Optional, Any
import time
import logging

from .market_intelligence_core import (
    UnifiedMarketIntelligence,
    MarketIntelligenceConfig,
    StrategyLens,
    MarketRegime,
)

from .friction_engine import MicroFrictionEngine
from .latent_state_engine import LatentStateEngine
from .time_to_move_engine import TimeToMovePredictor
from .liquidity_entropy_engine import (
    SyntheticLiquidityEngine,
    VolumeEntropyTracker,
    LiquidityVacuumDetector,
)
from .execution_forecast_engine import (
    ExecutionQualityForecaster,
    PriceResponseCurveEngine,
)
from .memory_sr_engine import (
    MarketMemoryEngine,
    LearnedSREngine,
    MicroTrendVectorEngine,
)
from .confidence_overlay_engine import (
    ModelDisagreementTracker,
    InformationFlowEngine,
    StrategyViewEngine,
    ConfidenceOverlayEngine,
)

logger = logging.getLogger(__name__)


@dataclass
class PerformanceMetrics:
    """Performance metrics for the orchestrator."""
    total_latency_ms: float = 0.0
    feature_extraction_ms: float = 0.0
    model_inference_ms: float = 0.0
    overlay_generation_ms: float = 0.0
    memory_usage_kb: float = 0.0
    update_count: int = 0


class MarketIntelligenceOrchestrator:
    """
    Master orchestrator for the unified market intelligence system.
    
    Integrates all 15 concepts into a coherent system that:
    - Extracts hidden structure from cheap data (L1 + aggregated L2)
    - Infers microstructure, regime, execution risk
    - Produces actionable, confidence-weighted visual overlays
    - Evolves safely through offline retraining
    
    Usage:
        orchestrator = MarketIntelligenceOrchestrator()
        
        # Update with market data
        intelligence = orchestrator.update(
            symbol="BTCUSDT",
            price=50000.0,
            volume=100.0,
            bid=49995.0,
            ask=50005.0,
        )
        
        # Access unified intelligence
        print(f"Regime: {intelligence.latent_state.regime}")
        print(f"Time to breakout: {intelligence.time_to_move.bars_to_breakout}")
        print(f"Execution risk: {intelligence.execution_forecast.execution_risk}")
    """
    
    def __init__(self, config: Optional[MarketIntelligenceConfig] = None):
        self.config = config or MarketIntelligenceConfig()
        
        # Initialize all engines
        self._init_engines()
        
        # Symbol state
        self._symbols: Dict[str, Dict[str, Any]] = {}
        
        # Performance tracking
        self._metrics = PerformanceMetrics()
        
        # Feature buffer for model input
        self._feature_dim = 32
        
        logger.info("MarketIntelligenceOrchestrator initialized")
    
    def _init_engines(self):
        """Initialize all component engines."""
        # Concept 1: Micro-Friction Map
        self.friction_engine = MicroFrictionEngine(self.config)
        
        # Concept 2: Latent Market State
        self.latent_engine = LatentStateEngine(self.config)
        
        # Concept 3: Time-to-Move Predictor
        self.ttm_engine = TimeToMovePredictor(self.config)
        
        # Concept 4: Synthetic Liquidity
        self.liquidity_engine = SyntheticLiquidityEngine(self.config)
        
        # Concept 5: Volume Entropy
        self.entropy_engine = VolumeEntropyTracker(self.config)
        
        # Concept 6: Market Memory
        self.memory_engine = MarketMemoryEngine(self.config)
        
        # Concept 7: Execution Quality
        self.execution_engine = ExecutionQualityForecaster(self.config)
        
        # Concept 8: Micro-Trend Vectors
        self.trend_engine = MicroTrendVectorEngine(self.config)
        
        # Concept 9: Liquidity Vacuum
        self.vacuum_engine = LiquidityVacuumDetector(self.config)
        
        # Concept 10: Model Disagreement
        self.disagreement_engine = ModelDisagreementTracker(self.config)
        
        # Concept 11: Price Response Curvature
        self.response_engine = PriceResponseCurveEngine(self.config)
        
        # Concept 12: Learned S/R
        self.sr_engine = LearnedSREngine(self.config)
        
        # Concept 13: Information Flow
        self.flow_engine = InformationFlowEngine(self.config)
        
        # Concept 14: Strategy Views
        self.strategy_engine = StrategyViewEngine(self.config)
        
        # Concept 15: Confidence Overlays
        self.overlay_engine = ConfidenceOverlayEngine(self.config)
    
    def add_symbol(self, symbol: str) -> bool:
        """
        Add a symbol to track.
        
        Args:
            symbol: Symbol identifier
            
        Returns:
            True if added successfully
        """
        if symbol in self._symbols:
            return True
        
        self._symbols[symbol] = {
            'update_count': 0,
            'last_price': 0.0,
            'last_update': 0.0,
            'last_intelligence': None,
        }
        
        logger.info(f"Added symbol: {symbol}")
        return True
    
    def update(self, symbol: str, price: float, volume: float,
               bid: float, ask: float,
               timestamp: Optional[float] = None) -> UnifiedMarketIntelligence:
        """
        Update market intelligence with new data.
        
        This is the main entry point. All 15 concepts are updated
        and unified into a single intelligence output.
        
        Args:
            symbol: Symbol identifier
            price: Current price
            volume: Trade volume
            bid: Best bid price
            ask: Best ask price
            timestamp: Optional timestamp (uses current time if not provided)
            
        Returns:
            UnifiedMarketIntelligence with all 15 concepts
        """
        start_time = time.perf_counter()
        
        if symbol not in self._symbols:
            self.add_symbol(symbol)
        
        timestamp = timestamp or time.time()
        state = self._symbols[symbol]
        state['update_count'] += 1
        
        # Calculate price change for entropy
        price_change = price - state['last_price'] if state['last_price'] > 0 else 0
        state['last_price'] = price
        
        # =====================================================================
        # PHASE 1: Feature Extraction (all 15 concepts)
        # =====================================================================
        feature_start = time.perf_counter()
        
        # Concept 1: Micro-Friction Map
        friction_map = self.friction_engine.update(price, volume, bid, ask, timestamp)
        
        # Concept 4: Synthetic Liquidity
        liquidity_map = self.liquidity_engine.update(price, volume, bid, ask)
        
        # Concept 5: Volume Entropy
        volume_entropy = self.entropy_engine.update(volume, price_change)
        
        # Concept 6: Market Memory
        memory_levels = self.memory_engine.update(price, volume)
        
        # Concept 8: Micro-Trend Vectors
        micro_trends = self.trend_engine.update(price)
        
        # Concept 9: Liquidity Vacuum
        vacuums = self.vacuum_engine.update(price, volume)
        
        # Concept 11: Price Response Curvature
        price_response = self.response_engine.update(price, volume, abs(price_change))
        
        # Concept 12: Learned S/R
        learned_sr = self.sr_engine.update(price, volume)
        
        # Concept 13: Information Flow
        info_flow = self.flow_engine.update(price, volume)
        
        feature_time = (time.perf_counter() - feature_start) * 1000
        
        # =====================================================================
        # PHASE 2: Model Inference
        # =====================================================================
        inference_start = time.perf_counter()
        
        # Build feature vector for latent state model
        features = self._build_feature_vector(
            price, volume, bid, ask,
            friction_map, liquidity_map, volume_entropy,
            memory_levels, micro_trends
        )
        
        # Concept 2: Latent Market State
        latent_state = self.latent_engine.update(features)
        
        # Concept 3: Time-to-Move
        time_to_move = self.ttm_engine.update(price, volume)
        
        # Concept 7: Execution Quality
        execution_forecast = self.execution_engine.update(
            price, bid, ask, volume, liquidity_map
        )
        
        # Concept 10: Model Disagreement
        model_predictions = self._get_model_predictions(
            latent_state, time_to_move, execution_forecast
        )
        model_disagreement = self.disagreement_engine.update(model_predictions)
        
        inference_time = (time.perf_counter() - inference_start) * 1000
        
        # =====================================================================
        # PHASE 3: Strategy Views & Overlays
        # =====================================================================
        overlay_start = time.perf_counter()
        
        # Concept 14: Strategy Views
        strategy_views = self.strategy_engine.update(
            price, volume, latent_state, memory_levels
        )
        
        # Concept 15: Confidence-Weighted Overlays
        self.overlay_engine.clear_overlays()
        overlays = self._generate_overlays(
            latent_state, friction_map, memory_levels,
            learned_sr, vacuums, model_disagreement
        )
        
        overlay_time = (time.perf_counter() - overlay_start) * 1000
        
        # =====================================================================
        # PHASE 4: Aggregate Metrics
        # =====================================================================
        
        # Overall confidence
        overall_confidence = self._calculate_overall_confidence(
            latent_state, model_disagreement, volume_entropy
        )
        
        # Market quality score
        market_quality = self._calculate_market_quality(
            liquidity_map, volume_entropy, execution_forecast
        )
        
        # Tradability score
        tradability = self._calculate_tradability(
            execution_forecast, vacuums, model_disagreement
        )
        
        # Total latency
        total_time = (time.perf_counter() - start_time) * 1000
        
        # Update metrics
        self._metrics.total_latency_ms = total_time
        self._metrics.feature_extraction_ms = feature_time
        self._metrics.model_inference_ms = inference_time
        self._metrics.overlay_generation_ms = overlay_time
        self._metrics.update_count += 1
        
        # Create unified intelligence
        intelligence = UnifiedMarketIntelligence(
            symbol=symbol,
            timestamp=timestamp,
            friction_map=friction_map,
            latent_state=latent_state,
            time_to_move=time_to_move,
            liquidity_map=liquidity_map,
            volume_entropy=volume_entropy,
            memory_levels=memory_levels,
            execution_forecast=execution_forecast,
            micro_trends=micro_trends,
            liquidity_vacuums=vacuums,
            model_disagreement=model_disagreement,
            price_response=price_response,
            learned_sr=learned_sr,
            information_flow=info_flow,
            strategy_views=strategy_views,
            overlays=overlays,
            overall_confidence=overall_confidence,
            market_quality_score=market_quality,
            tradability_score=tradability,
            inference_latency_ms=total_time,
            feature_staleness_ms=0.0
        )
        
        state['last_intelligence'] = intelligence
        state['last_update'] = timestamp
        
        # Log if latency exceeds budget
        if total_time > self.config.max_inference_ms:
            logger.warning(f"Latency {total_time:.2f}ms exceeds budget {self.config.max_inference_ms}ms")
        
        return intelligence
    
    def _build_feature_vector(self, price: float, volume: float,
                             bid: float, ask: float,
                             friction_map, liquidity_map, volume_entropy,
                             memory_levels, micro_trends) -> np.ndarray:
        """
        Build 32-dim feature vector for latent state model.
        
        Features are normalized and clipped for stability.
        """
        features = np.zeros(self._feature_dim)
        
        # Price features (0-3)
        spread = ask - bid
        features[0] = np.log1p(price) / 10  # Log price
        features[1] = spread / price * 1000  # Spread in bps
        features[2] = volume / 1000  # Normalized volume
        features[3] = np.log1p(volume)  # Log volume
        
        # Friction features (4-7)
        if friction_map:
            avg_friction = np.mean([fp.friction_coefficient for fp in friction_map])
            avg_slippage = np.mean([fp.slippage_estimate_bps for fp in friction_map])
            features[4] = avg_friction
            features[5] = avg_slippage / 20  # Normalize
            features[6] = len(friction_map) / 50  # Number of levels
            features[7] = np.std([fp.friction_coefficient for fp in friction_map]) if len(friction_map) > 1 else 0
        
        # Liquidity features (8-11)
        features[8] = liquidity_map.asymmetry_score
        features[9] = liquidity_map.hidden_bid_estimate
        features[10] = liquidity_map.hidden_ask_estimate
        features[11] = liquidity_map.iceberg_probability
        
        # Entropy features (12-15)
        features[12] = volume_entropy.entropy / np.log(10)  # Normalize
        features[13] = volume_entropy.information_ratio
        features[14] = volume_entropy.informed_trading_prob
        features[15] = volume_entropy.volume_clustering
        
        # Memory features (16-19)
        if memory_levels:
            supports = [l for l in memory_levels if l.level_type == 'support']
            resistances = [l for l in memory_levels if l.level_type == 'resistance']
            features[16] = len(supports) / 20
            features[17] = len(resistances) / 20
            features[18] = np.mean([l.current_strength for l in memory_levels]) if memory_levels else 0
            features[19] = np.mean([l.reaction_probability for l in memory_levels]) if memory_levels else 0.5
        
        # Trend features (20-23)
        if micro_trends:
            recent = micro_trends[-1]
            features[20] = recent.direction
            features[21] = recent.magnitude
            features[22] = recent.acceleration
            features[23] = recent.divergence
        
        # Price action features (24-27)
        features[24] = (price - bid) / (ask - bid + 1e-8)  # Position in spread
        features[25] = 0  # Reserved
        features[26] = 0  # Reserved
        features[27] = 0  # Reserved
        
        # Reserved (28-31)
        features[28] = 0
        features[29] = 0
        features[30] = 0
        features[31] = 0
        
        # Clip outliers
        features = np.clip(features, -5, 5)
        
        return features
    
    def _get_model_predictions(self, latent_state, time_to_move, execution_forecast) -> Dict[str, float]:
        """Get predictions from different models for disagreement tracking."""
        return {
            'regime_confidence': latent_state.regime_confidence,
            'breakout_confidence': time_to_move.confidence_breakout,
            'reversion_confidence': time_to_move.confidence_reversion,
            'execution_confidence': execution_forecast.confidence,
            'transition_prob': latent_state.transition_probability,
        }
    
    def _generate_overlays(self, latent_state, friction_map, memory_levels,
                          learned_sr, vacuums, disagreement) -> List:
        """Generate confidence-weighted overlays."""
        overlays = []
        
        # Regime background overlay
        overlays.append(self.overlay_engine.create_overlay(
            overlay_type='regime_background',
            data={
                'regime': latent_state.regime.name,
                'color': latent_state.regime_color,
                'duration': latent_state.regime_duration_bars,
            },
            confidence=latent_state.regime_confidence,
            z_index=-10
        ))
        
        # Friction zones overlay
        if friction_map:
            overlays.append(self.overlay_engine.create_overlay(
                overlay_type='friction_zones',
                data={
                    'zones': [
                        {
                            'price': fp.price_level,
                            'friction': fp.friction_coefficient,
                            'type': fp.zone_type.name,
                        }
                        for fp in friction_map[:10]  # Top 10
                    ]
                },
                confidence=np.mean([fp.confidence for fp in friction_map]) if friction_map else 0,
                z_index=-5
            ))
        
        # Memory levels overlay
        if memory_levels:
            overlays.append(self.overlay_engine.create_overlay(
                overlay_type='memory_levels',
                data={
                    'levels': [
                        {
                            'price': ml.price,
                            'strength': ml.current_strength,
                            'type': ml.level_type,
                            'decay': ml.strength_decay,
                        }
                        for ml in memory_levels[:10]
                    ]
                },
                confidence=np.mean([ml.current_strength for ml in memory_levels]),
                z_index=5
            ))
        
        # Learned S/R overlay
        if learned_sr:
            overlays.append(self.overlay_engine.create_overlay(
                overlay_type='learned_sr',
                data={
                    'levels': [
                        {
                            'price': sr.price,
                            'reaction_prob': sr.reaction_probability,
                            'type': sr.level_type,
                        }
                        for sr in learned_sr[:10]
                    ]
                },
                confidence=np.mean([sr.confidence for sr in learned_sr]),
                z_index=6
            ))
        
        # Vacuum zones overlay
        if vacuums:
            overlays.append(self.overlay_engine.create_overlay(
                overlay_type='liquidity_vacuums',
                data={
                    'vacuums': [
                        {
                            'start': v.price_start,
                            'end': v.price_end,
                            'strength': v.vacuum_strength,
                            'jump_risk': v.jump_risk,
                        }
                        for v in vacuums
                    ]
                },
                confidence=np.mean([v.vacuum_strength for v in vacuums]),
                z_index=-3
            ))
        
        # Disagreement heatmap overlay
        overlays.append(self.overlay_engine.create_overlay(
            overlay_type='disagreement_heatmap',
            data={
                'disagreement': disagreement.disagreement_score,
                'variance': disagreement.variance,
                'predictions': disagreement.model_predictions,
            },
            confidence=disagreement.confidence_adjusted,
            z_index=10
        ))
        
        return overlays
    
    def _calculate_overall_confidence(self, latent_state, disagreement, entropy) -> float:
        """Calculate overall confidence in the intelligence."""
        # Weighted average of component confidences
        regime_conf = latent_state.regime_confidence
        disagreement_adj = disagreement.confidence_adjusted
        info_ratio = entropy.information_ratio
        
        return (regime_conf * 0.4 + disagreement_adj * 0.3 + info_ratio * 0.3)
    
    def _calculate_market_quality(self, liquidity_map, entropy, execution) -> float:
        """Calculate overall market quality score."""
        # Good market = balanced liquidity, low noise, low slippage
        liquidity_balance = 1 - abs(liquidity_map.asymmetry_score)
        info_quality = entropy.information_ratio
        execution_quality = execution.fill_probability * (1 - execution.expected_slippage_bps / 20)
        
        return (liquidity_balance * 0.3 + info_quality * 0.3 + execution_quality * 0.4)
    
    def _calculate_tradability(self, execution, vacuums, disagreement) -> float:
        """Calculate tradability score."""
        # Tradable = low execution risk, no vacuums, low disagreement
        exec_score = 1 - (execution.expected_slippage_bps / 20)
        vacuum_score = 1 - (len(vacuums) / 10) if vacuums else 1
        agreement_score = disagreement.confidence_adjusted
        
        return max(0, min(1, exec_score * 0.4 + vacuum_score * 0.3 + agreement_score * 0.3))
    
    def get_intelligence(self, symbol: str) -> Optional[UnifiedMarketIntelligence]:
        """Get last intelligence for symbol."""
        if symbol not in self._symbols:
            return None
        return self._symbols[symbol].get('last_intelligence')
    
    def get_metrics(self) -> PerformanceMetrics:
        """Get performance metrics."""
        return self._metrics
    
    def reset(self, symbol: Optional[str] = None):
        """Reset state for symbol or all symbols."""
        if symbol:
            if symbol in self._symbols:
                del self._symbols[symbol]
        else:
            self._symbols.clear()
        
        # Reset all engines
        self.friction_engine.reset()
        self.latent_engine.reset()
        self.ttm_engine.reset()
        self.liquidity_engine.reset()
        self.entropy_engine.reset()
        self.memory_engine.reset()
        self.execution_engine.reset()
        self.trend_engine.reset()
        self.vacuum_engine.reset()
        self.disagreement_engine.reset()
        self.response_engine.reset()
        self.sr_engine.reset()
        self.flow_engine.reset()
        self.strategy_engine.reset()
        self.overlay_engine.reset()


def create_market_intelligence(config: Optional[MarketIntelligenceConfig] = None) -> MarketIntelligenceOrchestrator:
    """Factory function to create market intelligence orchestrator."""
    return MarketIntelligenceOrchestrator(config)


def quick_start(symbol: str = "BTCUSDT") -> MarketIntelligenceOrchestrator:
    """Quick start with default configuration."""
    orchestrator = MarketIntelligenceOrchestrator()
    orchestrator.add_symbol(symbol)
    return orchestrator
