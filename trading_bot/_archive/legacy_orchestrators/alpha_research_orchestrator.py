"""
from typing import Dict, List, Optional, Set, Tuple
Alpha Research Orchestrator
===========================
Master orchestrator integrating all alpha research components.

Integrates:
- Self-Evolving Researcher
- Feature Mining System
- Market State Classifier
- Smart Order Router
- Dynamic Risk Matrix
- Unified AlphaBrain
- Ensemble Meta-Learner
- Alpha Fusion Graph
- Trust & Safety Layer
- Market Impact & Predator Detection

Author: AlphaAlgo Research Team
"""

import asyncio
import logging
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum, auto
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
import threading

import numpy as np
import pandas as pd

# Import all components
from .self_evolving_researcher import SelfEvolvingResearcher, StrategyCandidate
from .feature_mining_system import FeatureMiningSystem, FeatureMiningResult
from .market_state_classifier import MarketStateClassifier, MarketState, MarketRegime
from .smart_order_router import SmartOrderRouter, ExecutionResult, OrderType, ExecutionUrgency
from .dynamic_risk_matrix import DynamicRiskMatrix, RiskState, RiskFactors
from .unified_alpha_brain import UnifiedAlphaBrain, StrategySignal, CollectiveDecision, SignalStrength
from .ensemble_meta_learner import EnsembleMetaLearner, EnsemblePrediction, RegimeType
from .alpha_fusion_graph import AlphaFusionGraph, FusedAlpha
from .trust_safety_layer import TrustSafetyLayer, TradeAudit, QuarantineReason
from .market_impact_predator import MarketImpactPredatorSystem, MarketImpactEstimate

logger = logging.getLogger(__name__)


class SystemMode(Enum):
    """System operating modes"""
    RESEARCH = auto()      # Strategy research and backtesting
    PAPER = auto()         # Paper trading
    LIVE = auto()          # Live trading
    DEFENSIVE = auto()     # Reduced risk mode
    EMERGENCY = auto()     # Emergency shutdown mode


@dataclass
class TradingSignal:
    """Complete trading signal from orchestrator"""
    signal_id: str
    timestamp: datetime
    symbol: str
    
    # Direction and strength
    direction: str  # 'long', 'short', 'neutral'
    strength: float  # 0-1
    confidence: float  # 0-1
    
    # Entry/Exit
    entry_price: float = 0.0
    stop_loss: float = 0.0
    take_profit: float = 0.0
    position_size: float = 0.0
    
    # Risk parameters
    risk_score: float = 0.0
    max_leverage: float = 1.0
    
    # Execution
    recommended_algo: str = "ADAPTIVE"
    execution_urgency: str = "MEDIUM"
    
    # Context
    market_regime: str = ""
    alpha_components: Dict[str, float] = field(default_factory=dict)
    
    # Validation
    approved: bool = False
    approval_reason: str = ""


@dataclass
class SystemStatus:
    """Current system status"""
    mode: SystemMode
    timestamp: datetime
    
    # Component status
    researcher_status: str = "idle"
    classifier_status: str = "ready"
    risk_status: str = "normal"
    
    # Performance
    signals_generated: int = 0
    trades_executed: int = 0
    win_rate: float = 0.0
    
    # Risk
    current_drawdown: float = 0.0
    risk_level: str = "moderate"
    
    # Alerts
    active_alerts: List[str] = field(default_factory=list)
    quarantined_modules: List[str] = field(default_factory=list)


class AlphaResearchOrchestrator:
    """
    Master orchestrator for the Alpha Research System.
    
    Coordinates all components:
    1. Self-Evolving Researcher - Strategy generation and evolution
    2. Feature Mining System - Automatic feature discovery
    3. Market State Classifier - Regime detection
    4. Smart Order Router - Intelligent execution
    5. Dynamic Risk Matrix - Real-time risk adjustment
    6. Unified AlphaBrain - Shared memory across strategies
    7. Ensemble Meta-Learner - Model combination
    8. Alpha Fusion Graph - Signal fusion
    9. Trust & Safety Layer - Audit and compliance
    10. Market Impact & Predator Detection - Protection
    """
    
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        
        # System mode
        self.mode = SystemMode[self.config.get('mode', 'PAPER').upper()]
        
        # Initialize all components
        logger.info("Initializing Alpha Research Orchestrator...")
        
        self.researcher = SelfEvolvingResearcher(config)
        self.feature_miner = FeatureMiningSystem(config)
        self.market_classifier = MarketStateClassifier(config)
        self.order_router = SmartOrderRouter(config)
        self.risk_matrix = DynamicRiskMatrix(config)
        self.alpha_brain = UnifiedAlphaBrain(config)
        self.ensemble = EnsembleMetaLearner(config)
        self.fusion_graph = AlphaFusionGraph(config)
        self.trust_safety = TrustSafetyLayer(config)
        self.impact_system = MarketImpactPredatorSystem(config)
        
        # State
        self.current_market_state: Optional[MarketState] = None
        self.current_risk_state: Optional[RiskState] = None
        self.running = False
        self._lock = threading.Lock()
        
        # Performance tracking
        self.signals_generated = 0
        self.trades_executed = 0
        self.total_pnl = 0.0
        
        logger.info("Alpha Research Orchestrator initialized")
    
    async def start(self):
        """Start the orchestrator"""
        self.running = True
        logger.info(f"Orchestrator started in {self.mode.name} mode")
        
        # Start background tasks
        asyncio.create_task(self._market_monitoring_loop())
        asyncio.create_task(self._risk_monitoring_loop())
    
    async def stop(self):
        """Stop the orchestrator"""
        self.running = False
        logger.info("Orchestrator stopped")
    
    async def generate_signal(
        self,
        symbol: str,
        market_data: pd.DataFrame,
        lob_data: Optional[Dict] = None,
        sentiment_data: Optional[Dict] = None,
        macro_data: Optional[Dict] = None
    ) -> TradingSignal:
        """Generate a complete trading signal"""
        
        import uuid
        signal_id = str(uuid.uuid4())[:8]
        
        # Step 1: Classify market state
        self.market_classifier.fit(market_data)
        market_state = self.market_classifier.classify(
            market_data,
            vix=macro_data.get('vix') if macro_data else None
        )
        self.current_market_state = market_state
        
        # Step 2: Update risk state
        risk_factors = self._create_risk_factors(market_data, market_state)
        risk_state = self.risk_matrix.update(risk_factors, capital=100000)
        self.current_risk_state = risk_state
        
        # Step 3: Generate alpha fusion
        fused_alpha = self.fusion_graph.generate_and_fuse(
            market_data, symbol, lob_data, sentiment_data, macro_data
        )
        
        # Step 4: Get ensemble prediction
        features = self._extract_features(market_data)
        if len(features) > 0:
            # Set regime for ensemble
            regime_map = {
                MarketRegime.TRENDING_UP: RegimeType.TRENDING_UP,
                MarketRegime.TRENDING_DOWN: RegimeType.TRENDING_DOWN,
                MarketRegime.RANGING: RegimeType.RANGING,
                MarketRegime.HIGH_VOLATILITY: RegimeType.HIGH_VOLATILITY,
            }
            ensemble_regime = regime_map.get(market_state.regime, RegimeType.RANGING)
            self.ensemble.set_regime(ensemble_regime)
            
            ensemble_pred = self.ensemble.predict(features, regime=ensemble_regime)
        else:
            ensemble_pred = None
        
        # Step 5: Combine signals
        direction, strength, confidence = self._combine_signals(
            fused_alpha, ensemble_pred, market_state
        )
        
        # Step 6: Get position parameters from risk matrix
        current_price = market_data['close'].iloc[-1]
        position_params = self.risk_matrix.get_position_parameters(
            symbol, direction, current_price, capital=100000
        )
        
        # Step 7: Check market safety
        safe_to_trade, safety_reason = self.impact_system.should_trade(symbol)
        
        # Step 8: Create signal
        signal = TradingSignal(
            signal_id=signal_id,
            timestamp=datetime.now(),
            symbol=symbol,
            direction=direction,
            strength=strength,
            confidence=confidence,
            entry_price=current_price,
            stop_loss=position_params['stop_loss'] or current_price * 0.98,
            take_profit=position_params['take_profit'] or current_price * 1.04,
            position_size=position_params['position_size'],
            risk_score=risk_state.risk_score,
            max_leverage=position_params['max_leverage'],
            recommended_algo=self._get_recommended_algo(market_state, risk_state),
            execution_urgency=self._get_execution_urgency(market_state),
            market_regime=market_state.regime.name,
            alpha_components={
                'trend': fused_alpha.trend_component,
                'momentum': fused_alpha.momentum_component,
                'volume': fused_alpha.volume_component,
                'sentiment': fused_alpha.sentiment_component
            },
            approved=safe_to_trade and confidence > 0.5,
            approval_reason=safety_reason if not safe_to_trade else "Signal approved"
        )
        
        # Step 9: Submit to AlphaBrain
        brain_signal = StrategySignal(
            signal_id=signal_id,
            strategy_name="orchestrator",
            timestamp=datetime.now(),
            symbol=symbol,
            direction=direction,
            strength=SignalStrength.STRONG if strength > 0.7 else SignalStrength.MODERATE,
            confidence=confidence,
            entry_price=signal.entry_price,
            stop_loss=signal.stop_loss,
            take_profit=signal.take_profit
        )
        self.alpha_brain.submit_signal(brain_signal)
        
        self.signals_generated += 1
        
        return signal
    
    async def execute_signal(
        self,
        signal: TradingSignal,
        order_book: Any = None
    ) -> ExecutionResult:
        """Execute a trading signal"""
        
        if not signal.approved:
            return ExecutionResult(
                order_id=signal.signal_id,
                success=False,
                error_message=f"Signal not approved: {signal.approval_reason}"
            )
        
        # Check if module is quarantined
        if self.trust_safety.is_module_quarantined("orchestrator"):
            return ExecutionResult(
                order_id=signal.signal_id,
                success=False,
                error_message="Orchestrator is quarantined"
            )
        
        # Get execution parameters
        urgency = ExecutionUrgency[signal.execution_urgency]
        algo = OrderType[signal.recommended_algo] if hasattr(OrderType, signal.recommended_algo) else OrderType.ADAPTIVE
        
        # Create mock order book if not provided
        if order_book is None:
            from .smart_order_router import OrderBook, OrderBookLevel
            order_book = OrderBook(
                symbol=signal.symbol,
                timestamp=datetime.now(),
                bids=[OrderBookLevel(price=signal.entry_price * 0.999, size=10000)],
                asks=[OrderBookLevel(price=signal.entry_price * 1.001, size=10000)]
            )
        
        # Execute through smart order router
        result = await self.order_router.route_order(
            symbol=signal.symbol,
            side='buy' if signal.direction == 'long' else 'sell',
            quantity=signal.position_size,
            order_book=order_book,
            urgency=urgency,
            algorithm=algo,
            price_limit=signal.entry_price * 1.005 if signal.direction == 'long' else signal.entry_price * 0.995
        )
        
        # Audit the trade
        if result.success:
            self.trust_safety.audit_trade(
                trade_id=signal.signal_id,
                symbol=signal.symbol,
                side='buy' if signal.direction == 'long' else 'sell',
                quantity=result.filled_quantity,
                price=result.avg_price,
                signal_source="orchestrator",
                signal_confidence=signal.confidence,
                strategy_name="alpha_research",
                risk_score=signal.risk_score,
                position_size_pct=signal.position_size / 100000,  # Assuming 100k capital
                slippage=result.slippage_bps / 10000,
                execution_time_ms=result.execution_time_ms,
                venue="smart_router"
            )
            
            self.trades_executed += 1
        
        return result
    
    async def run_research_cycle(
        self,
        market_data: pd.DataFrame,
        generations: int = 5
    ) -> List[StrategyCandidate]:
        """Run strategy research cycle"""
        
        logger.info("Starting research cycle...")
        
        # Mine features first
        feature_result = await self.feature_miner.mine_features(market_data)
        logger.info(f"Mined {feature_result.final_features_selected} features")
        
        # Run strategy evolution
        strategies = await self.researcher.run_research_cycle(market_data, generations)
        logger.info(f"Evolved {len(strategies)} strategies")
        
        # Audit the evolution
        self.trust_safety.audit_evolution_cycle(
            cycle_id=str(hash(datetime.now()))[:8],
            changes_made=[{'type': 'strategy_evolution', 'count': len(strategies)}],
            performance_before={},
            performance_after={'strategies': len(strategies)}
        )
        
        return strategies
    
    def _create_risk_factors(
        self,
        market_data: pd.DataFrame,
        market_state: MarketState
    ) -> RiskFactors:
        """Create risk factors from market data"""
        
        close = market_data['close']
        returns = close.pct_change()
        
        volatility = returns.iloc[-20:].std() * np.sqrt(252) if len(returns) >= 20 else 0.15
        
        return RiskFactors(
            volatility=volatility,
            volatility_regime=market_state.volatility_regime.name.lower(),
            trend_strength=market_state.trend_direction,
            market_regime=market_state.regime.name.lower(),
            current_drawdown=0.0,  # Would need portfolio data
            portfolio_heat=0.0,
            correlation_risk=0.0,
            concentration_risk=0.0,
            recent_win_rate=0.5,
            recent_profit_factor=1.0,
            sharpe_ratio=0.0,
            vix_level=market_state.vix_level,
            news_sentiment=0.0,
            economic_calendar_risk=0.0
        )
    
    def _extract_features(self, market_data: pd.DataFrame) -> np.ndarray:
        """Extract features for ensemble prediction"""
        
        close = market_data['close']
        
        if len(close) < 50:
            return np.array([])
        
        features = []
        
        # Returns
        features.append(close.pct_change().iloc[-1])
        features.append(close.pct_change(5).iloc[-1])
        features.append(close.pct_change(20).iloc[-1])
        
        # Volatility
        features.append(close.pct_change().iloc[-20:].std())
        
        # Trend
        sma_20 = close.rolling(20).mean().iloc[-1]
        sma_50 = close.rolling(50).mean().iloc[-1]
        features.append((close.iloc[-1] - sma_20) / sma_20)
        features.append((sma_20 - sma_50) / sma_50)
        
        # RSI
        delta = close.diff()
        gain = (delta.where(delta > 0, 0)).rolling(14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(14).mean()
        rs = gain / (loss + 1e-10)
        rsi = 100 - (100 / (1 + rs))
        features.append((rsi.iloc[-1] - 50) / 50)
        
        # Volume if available
        if 'volume' in market_data.columns:
            vol_sma = market_data['volume'].rolling(20).mean()
            features.append(market_data['volume'].iloc[-1] / vol_sma.iloc[-1] - 1)
        else:
            features.append(0)
        
        # Padding
        while len(features) < 10:
            features.append(0)
        
        return np.array(features[:10]).reshape(1, -1)
    
    def _combine_signals(
        self,
        fused_alpha: FusedAlpha,
        ensemble_pred: Optional[EnsemblePrediction],
        market_state: MarketState
    ) -> Tuple[str, float, float]:
        """Combine signals from different sources"""
        
        # Alpha fusion signal
        alpha_direction = fused_alpha.direction
        alpha_strength = abs(fused_alpha.alpha_value)
        alpha_confidence = fused_alpha.confidence
        
        # Ensemble signal
        if ensemble_pred and hasattr(ensemble_pred, 'prediction'):
            pred = ensemble_pred.prediction
            if isinstance(pred, np.ndarray) and len(pred) > 0:
                ensemble_direction = 'long' if pred[0] == 1 else 'short'
                ensemble_confidence = ensemble_pred.confidence
            else:
                ensemble_direction = 'neutral'
                ensemble_confidence = 0.5
        else:
            ensemble_direction = 'neutral'
            ensemble_confidence = 0.5
        
        # Market state adjustment
        state_multiplier = 1.0
        if market_state.regime == MarketRegime.HIGH_VOLATILITY:
            state_multiplier = 0.7
        elif market_state.regime == MarketRegime.CRASH:
            state_multiplier = 0.3
        
        # Combine
        if alpha_direction == ensemble_direction:
            # Agreement - higher confidence
            direction = alpha_direction
            strength = alpha_strength * state_multiplier
            confidence = (alpha_confidence + ensemble_confidence) / 2 * 1.2
        elif alpha_direction == 'neutral' or ensemble_direction == 'neutral':
            # One neutral - use the other
            direction = alpha_direction if alpha_direction != 'neutral' else ensemble_direction
            strength = alpha_strength * state_multiplier * 0.8
            confidence = max(alpha_confidence, ensemble_confidence) * 0.8
        else:
            # Disagreement - reduce confidence
            direction = alpha_direction if alpha_confidence > ensemble_confidence else ensemble_direction
            strength = alpha_strength * state_multiplier * 0.5
            confidence = abs(alpha_confidence - ensemble_confidence) * 0.5
        
        return direction, min(strength, 1.0), min(confidence, 1.0)
    
    def _get_recommended_algo(
        self,
        market_state: MarketState,
        risk_state: RiskState
    ) -> str:
        """Get recommended execution algorithm"""
        
        if market_state.regime == MarketRegime.HIGH_VOLATILITY:
            return "SNIPER"
        elif market_state.volume_shock:
            return "ICEBERG"
        elif risk_state.risk_score > 0.7:
            return "TWAP"
        else:
            return "ADAPTIVE"
    
    def _get_execution_urgency(self, market_state: MarketState) -> str:
        """Get execution urgency"""
        
        if market_state.regime == MarketRegime.CRASH:
            return "CRITICAL"
        elif market_state.regime == MarketRegime.HIGH_VOLATILITY:
            return "HIGH"
        elif market_state.regime in [MarketRegime.TRENDING_UP, MarketRegime.TRENDING_DOWN]:
            return "MEDIUM"
        else:
            return "LOW"
    
    async def _market_monitoring_loop(self):
        """Background market monitoring"""
        while self.running:
            try:
                # Would monitor market conditions here
                await asyncio.sleep(60)
            except Exception as e:
                logger.error(f"Market monitoring error: {e}")
    
    async def _risk_monitoring_loop(self):
        """Background risk monitoring"""
        while self.running:
            try:
                # Check if should reduce exposure
                if self.current_risk_state:
                    should_reduce, reason, amount = self.risk_matrix.should_reduce_exposure()
                    if should_reduce:
                        logger.warning(f"Risk alert: {reason}")
                
                await asyncio.sleep(30)
            except Exception as e:
                logger.error(f"Risk monitoring error: {e}")
    
    def get_status(self) -> SystemStatus:
        """Get current system status"""
        
        return SystemStatus(
            mode=self.mode,
            timestamp=datetime.now(),
            researcher_status=self.researcher.get_status().get('running', False) and 'running' or 'idle',
            classifier_status='ready',
            risk_status=self.current_risk_state.risk_level.name if self.current_risk_state else 'unknown',
            signals_generated=self.signals_generated,
            trades_executed=self.trades_executed,
            win_rate=0.5,  # Would calculate from history
            current_drawdown=0.0,
            risk_level=self.current_risk_state.risk_level.name if self.current_risk_state else 'moderate',
            active_alerts=[],
            quarantined_modules=[m.module_name for m in self.trust_safety.quarantine_manager.get_quarantined_modules()]
        )


# Factory function
def create_orchestrator(config: Optional[Dict] = None) -> AlphaResearchOrchestrator:
    """Create and return an AlphaResearchOrchestrator instance"""
    return AlphaResearchOrchestrator(config)


# Quick start
async def quick_start(config: Optional[Dict] = None) -> AlphaResearchOrchestrator:
    """Quick start the orchestrator"""
    orchestrator = create_orchestrator(config)
    await orchestrator.start()
    return orchestrator
