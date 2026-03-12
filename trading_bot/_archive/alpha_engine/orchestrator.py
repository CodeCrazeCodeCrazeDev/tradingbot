"""
AlphaEngine Orchestrator
=========================

Main orchestrator that integrates all AlphaEngine components:
- DC Core Engine
- Deep Learning Models
- RL Execution
- Sentiment Analysis
- Alternative Data
- Ensemble Meta-Learning
- Risk Management
- Execution Algorithms
- Multi-Brain Architecture
- Monitoring & Analytics
- Self-Analysis

Provides unified interface for trading decisions.
"""

import numpy as np
import pandas as pd
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Tuple
from collections import deque
import logging
from datetime import datetime, timedelta
from abc import ABC, abstractmethod
import asyncio
import json

logger = logging.getLogger(__name__)

# Import all components
from .dc_core import DirectionalChangeEngine, DCEvent
from .deep_learning import PricePredictionModel, DeepLOBPredictor, MultiScaleLSTM
from .rl_execution import RLExecutionAgent, MetaRLOptimizer, ExecutionState
from .sentiment_engine import SentimentAggregator, SentimentSignal
from .alternative_data import AlternativeDataProcessor
from .ensemble import EnsembleMetaLearner, ModelPrediction, ModelType
from .risk_management import MLRiskManager, VolatilityRegime
from .execution import SmartOrderRouter, IcebergExecutor, VWAPExecutor, ExecutionQualityMonitor
from .multi_brain import MultiBrainArchitecture, BrainCoordinator, MarketRegime
from .market_microstructure import OrderFlowAnalyzer, ToxicityDetector, LiquidityAnalyzer
from .monitoring import PerformanceDashboard, RiskMonitor, AlertSystem, TradeAnalytics
from .backtesting import AdvancedBacktester, MonteCarloSimulator, StressTestEngine
from .self_analysis import SelfAnalysisEngine, ContinuousImprover


class TradingMode(Enum):
    """Trading modes"""
    LIVE = "live"
    PAPER = "paper"
    BACKTEST = "backtest"
    SIMULATION = "simulation"


class SignalStrength(Enum):
    """Signal strength levels"""
    STRONG_BUY = "strong_buy"
    BUY = "buy"
    WEAK_BUY = "weak_buy"
    NEUTRAL = "neutral"
    WEAK_SELL = "weak_sell"
    SELL = "sell"
    STRONG_SELL = "strong_sell"


@dataclass
class TradingSignal:
    """Unified trading signal"""
    timestamp: datetime
    symbol: str
    direction: str  # 'long', 'short', 'neutral'
    strength: SignalStrength
    confidence: float
    
    # Position sizing
    recommended_size: float
    max_size: float
    
    # Entry/Exit levels
    entry_price: float
    stop_loss: float
    take_profit: float
    
    # Signal sources
    dc_signal: Optional[Dict[str, Any]] = None
    ml_signal: Optional[Dict[str, Any]] = None
    sentiment_signal: Optional[Dict[str, Any]] = None
    alt_data_signal: Optional[Dict[str, Any]] = None
    
    # Risk metrics
    risk_score: float = 0
    regime: str = "normal"
    
    # Execution recommendation
    execution_algo: str = "smart"
    urgency: str = "normal"
    
    # Metadata
    reasoning: str = ""
    model_weights: Dict[str, float] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'timestamp': self.timestamp.isoformat(),
            'symbol': self.symbol,
            'direction': self.direction,
            'strength': self.strength.value,
            'confidence': self.confidence,
            'recommended_size': self.recommended_size,
            'entry_price': self.entry_price,
            'stop_loss': self.stop_loss,
            'take_profit': self.take_profit,
            'risk_score': self.risk_score,
            'regime': self.regime,
            'reasoning': self.reasoning,
        }


@dataclass
class ExecutionPlan:
    """Execution plan for a signal"""
    signal: TradingSignal
    algorithm: str
    slices: List[Dict[str, Any]]
    venues: List[str]
    estimated_cost: float
    estimated_time: float
    risk_checks_passed: bool


class AlphaEngineOrchestrator:
    """
    Main orchestrator for AlphaEngine trading system
    """
    
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        self.mode = TradingMode(self.config.get('mode', 'paper'))
        
        # Initialize all components
        self._initialize_components()
        
        # State
        self.is_running = False
        self.current_positions: Dict[str, Dict[str, Any]] = {}
        self.pending_signals: deque = deque(maxlen=100)
        
        # Performance tracking
        self.signals_generated = 0
        self.trades_executed = 0
        self.start_time = datetime.now()
        
        logger.info(f"AlphaEngine Orchestrator initialized in {self.mode.value} mode")
    
    def _initialize_components(self):
        """Initialize all system components"""
        # Core DC Engine
        self.dc_engine = DirectionalChangeEngine(
            config={'thresholds': self.config.get('dc_thresholds', [0.005, 0.01, 0.02])}
        )
        
        # Deep Learning
        self.price_predictor = PricePredictionModel(self.config.get('deep_learning', {}))
        
        # RL Execution
        self.rl_executor = MetaRLOptimizer(self.config.get('rl_execution', {}))
        
        # Sentiment
        self.sentiment_aggregator = SentimentAggregator(self.config.get('sentiment', {}))
        
        # Alternative Data
        self.alt_data_processor = AlternativeDataProcessor(self.config.get('alt_data', {}))
        
        # Ensemble
        self.ensemble = EnsembleMetaLearner(self.config.get('ensemble', {}))
        
        # Risk Management
        self.risk_manager = MLRiskManager(self.config.get('risk', {}))
        
        # Execution
        self.order_router = SmartOrderRouter(self.config.get('execution', {}))
        self.iceberg_executor = IcebergExecutor(self.config.get('iceberg', {}))
        self.vwap_executor = VWAPExecutor(self.config.get('vwap', {}))
        self.execution_monitor = ExecutionQualityMonitor()
        
        # Multi-Brain
        self.multi_brain = MultiBrainArchitecture(self.config.get('multi_brain', {}))
        
        # Market Microstructure
        self.order_flow_analyzer = OrderFlowAnalyzer(self.config.get('microstructure', {}))
        self.toxicity_detector = ToxicityDetector(self.config.get('toxicity', {}))
        self.liquidity_analyzer = LiquidityAnalyzer()
        
        # Monitoring
        self.dashboard = PerformanceDashboard(self.config.get('dashboard', {}))
        self.risk_monitor = RiskMonitor(self.config.get('risk_monitor', {}))
        self.alert_system = AlertSystem(self.config.get('alerts', {}))
        self.trade_analytics = TradeAnalytics()
        
        # Self-Analysis
        self.self_analyzer = SelfAnalysisEngine(self.config.get('self_analysis', {}))
    
    async def start(self):
        """Start the orchestrator"""
        self.is_running = True
        self.start_time = datetime.now()
        
        logger.info("AlphaEngine Orchestrator started")
        
        # Start background tasks
        asyncio.create_task(self._monitoring_loop())
        asyncio.create_task(self._self_analysis_loop())
    
    async def stop(self):
        """Stop the orchestrator"""
        self.is_running = False
        logger.info("AlphaEngine Orchestrator stopped")
    
    async def process_market_data(self, data: Dict[str, Any]) -> Optional[TradingSignal]:
        """
        Process market data and generate trading signal
        
        Args:
            data: Market data dictionary with:
                - symbol: Trading symbol
                - price: Current price
                - volume: Current volume
                - timestamp: Data timestamp
                - ohlcv: OHLCV history
                - order_book: Order book data (optional)
                - news: Recent news (optional)
                
        Returns:
            TradingSignal if conditions met, None otherwise
        """
        symbol = data.get('symbol', '')
        price = data.get('price', 0)
        timestamp = data.get('timestamp', datetime.now())
        
        # Update components with new data
        self._update_components(data)
        
        # Generate signals from each component
        signals = await self._generate_component_signals(data)
        
        # Ensemble combination
        ensemble_prediction = self._combine_signals(signals)
        
        # Risk check
        risk_check = self.risk_manager.check_risk_limits()
        
        if not risk_check['should_trade']:
            logger.warning(f"Risk limits breached: {risk_check['breaches']}")
            return None
        
        # Generate final signal
        if ensemble_prediction['should_trade']:
            signal = self._create_trading_signal(
                symbol, price, timestamp, ensemble_prediction, signals, risk_check
            )
            
            self.signals_generated += 1
            self.pending_signals.append(signal)
            
            return signal
        
        return None
    
    def _update_components(self, data: Dict[str, Any]):
        """Update all components with new market data"""
        symbol = data.get('symbol', '')
        price = data.get('price', 0)
        volume = data.get('volume', 0)
        
        # Update DC Engine
        self.dc_engine.process_price(price, data.get('timestamp', datetime.now()))
        
        # Update sentiment with price for divergence
        self.sentiment_aggregator.update_price(symbol, price)
        
        # Update risk manager equity
        if 'equity' in data:
            self.risk_manager.update_equity(data['equity'])
        
        # Update order flow
        if 'trades' in data:
            for trade in data['trades']:
                self.order_flow_analyzer.process_trade(trade)
                self.toxicity_detector.process_trade(
                    trade.get('price', price),
                    trade.get('size', 0),
                    trade.get('side', 'buy')
                )
        
        # Update order book
        if 'order_book' in data:
            book = data['order_book']
            self.liquidity_analyzer.update_order_book(
                book.get('bids', []),
                book.get('asks', [])
            )
    
    async def _generate_component_signals(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Generate signals from each component"""
        symbol = data.get('symbol', '')
        prices = data.get('prices', [data.get('price', 0)])
        
        signals = {}
        
        # DC Signal
        dc_events = self.dc_engine.get_recent_events(10)
        if dc_events:
            latest_dc = dc_events[-1]
            signals['dc'] = {
                'direction': 'long' if latest_dc.direction == 'up' else 'short',
                'threshold': latest_dc.threshold,
                'overshoot': self.dc_engine.overshoot_calculator.calculate(latest_dc, data.get('price', 0)),
            }
        
        # ML Signal
        try:
            ml_prediction = self.price_predictor.predict({
                'prices': prices,
                'volumes': data.get('volumes', []),
            })
            signals['ml'] = ml_prediction
        except Exception as e:
            logger.error(f"ML prediction failed: {e}")
        
        # Sentiment Signal
        sentiment = self.sentiment_aggregator.get_trading_signal(symbol)
        signals['sentiment'] = sentiment
        
        # Alternative Data Signal
        alt_data = self.alt_data_processor.get_trading_recommendation(symbol)
        signals['alt_data'] = alt_data
        
        # Multi-Brain Signal
        brain_decision = await self.multi_brain.analyze_and_decide({
            'symbol': symbol,
            'prices': prices,
            'volumes': data.get('volumes', []),
            'timestamp': data.get('timestamp', datetime.now()),
        })
        signals['multi_brain'] = brain_decision
        
        # Order Flow Signal
        flow_signal = self.order_flow_analyzer.get_momentum_signal()
        signals['order_flow'] = flow_signal
        
        # Toxicity Check
        toxicity = self.toxicity_detector.get_toxicity_metrics()
        signals['toxicity'] = {
            'vpin': toxicity.vpin,
            'level': toxicity.toxicity_level.value,
            'recommendation': toxicity.recommendation,
        }
        
        # Liquidity Check
        liquidity_score = self.liquidity_analyzer.get_liquidity_score()
        signals['liquidity'] = {'score': liquidity_score}
        
        return signals
    
    def _combine_signals(self, signals: Dict[str, Any]) -> Dict[str, Any]:
        """Combine signals using ensemble"""
        predictions = []
        
        # Convert signals to ModelPredictions
        if 'dc' in signals:
            dc = signals['dc']
            predictions.append(ModelPrediction(
                model_type=ModelType.DC_ENGINE,
                timestamp=datetime.now(),
                symbol='',
                direction=dc.get('direction', 'neutral'),
                probability=0.7 if dc.get('direction') != 'neutral' else 0.5,
                confidence=0.8,
                magnitude=dc.get('overshoot', 0),
            ))
        
        if 'ml' in signals and signals['ml']:
            ml = signals['ml']
            predictions.append(ModelPrediction(
                model_type=ModelType.DEEP_LOB,
                timestamp=datetime.now(),
                symbol='',
                direction=ml.get('direction', 'neutral'),
                probability=ml.get('probability', 0.5),
                confidence=ml.get('confidence', 0.5),
                magnitude=ml.get('magnitude', 0),
            ))
        
        if 'sentiment' in signals:
            sent = signals['sentiment']
            predictions.append(ModelPrediction(
                model_type=ModelType.SENTIMENT,
                timestamp=datetime.now(),
                symbol='',
                direction=sent.get('sentiment_direction', 'neutral'),
                probability=abs(sent.get('sentiment_score', 0)) / 100,
                confidence=sent.get('confidence', 0.5),
                magnitude=0,
                metadata={'score': sent.get('sentiment_score', 0)},
            ))
        
        if 'multi_brain' in signals:
            brain = signals['multi_brain']
            predictions.append(ModelPrediction(
                model_type=ModelType.REGIME,
                timestamp=datetime.now(),
                symbol='',
                direction=brain.get('direction', 'neutral'),
                probability=brain.get('confidence', 0.5),
                confidence=brain.get('confidence', 0.5),
                magnitude=brain.get('strength', 0),
            ))
        
        # Get ensemble prediction
        if predictions:
            ensemble_pred = self.ensemble.predict(predictions)
            return {
                'direction': ensemble_pred.direction,
                'probability': ensemble_pred.probability,
                'confidence': ensemble_pred.confidence,
                'should_trade': ensemble_pred.should_trade,
                'size_multiplier': ensemble_pred.position_size_multiplier,
                'model_weights': ensemble_pred.model_weights,
                'reasoning': ensemble_pred.reason,
            }
        
        return {
            'direction': 'neutral',
            'probability': 0.5,
            'confidence': 0,
            'should_trade': False,
            'size_multiplier': 0,
            'model_weights': {},
            'reasoning': 'No signals available',
        }
    
    def _create_trading_signal(self, symbol: str, price: float, timestamp: datetime,
                              ensemble: Dict[str, Any], signals: Dict[str, Any],
                              risk_check: Dict[str, Any]) -> TradingSignal:
        """Create final trading signal"""
        direction = ensemble['direction']
        confidence = ensemble['confidence']
        
        # Determine signal strength
        if confidence > 0.8:
            if direction == 'long':
                strength = SignalStrength.STRONG_BUY
            else:
                strength = SignalStrength.STRONG_SELL
        elif confidence > 0.6:
            if direction == 'long':
                strength = SignalStrength.BUY
            else:
                strength = SignalStrength.SELL
        elif confidence > 0.4:
            if direction == 'long':
                strength = SignalStrength.WEAK_BUY
            else:
                strength = SignalStrength.WEAK_SELL
        else:
            strength = SignalStrength.NEUTRAL
        
        # Get position size recommendation
        position_rec = self.risk_manager.get_position_recommendation(
            symbol,
            {'win_prob': ensemble['probability'], 'confidence': confidence}
        )
        
        # Calculate entry/exit levels
        volatility = 0.02  # Default, should come from data
        if direction == 'long':
            stop_loss = price * (1 - volatility * 2)
            take_profit = price * (1 + volatility * 3)
        else:
            stop_loss = price * (1 + volatility * 2)
            take_profit = price * (1 - volatility * 3)
        
        # Determine execution algorithm
        toxicity = signals.get('toxicity', {})
        liquidity = signals.get('liquidity', {})
        
        if toxicity.get('level') == 'extreme':
            execution_algo = 'passive'
            urgency = 'low'
        elif liquidity.get('score', 1) < 0.5:
            execution_algo = 'iceberg'
            urgency = 'normal'
        elif confidence > 0.8:
            execution_algo = 'aggressive'
            urgency = 'high'
        else:
            execution_algo = 'smart'
            urgency = 'normal'
        
        # Get regime
        regime = signals.get('multi_brain', {}).get('regime', 'normal')
        
        return TradingSignal(
            timestamp=timestamp,
            symbol=symbol,
            direction=direction,
            strength=strength,
            confidence=confidence,
            recommended_size=position_rec.adjusted_size,
            max_size=position_rec.max_allowed,
            entry_price=price,
            stop_loss=stop_loss,
            take_profit=take_profit,
            dc_signal=signals.get('dc'),
            ml_signal=signals.get('ml'),
            sentiment_signal=signals.get('sentiment'),
            alt_data_signal=signals.get('alt_data'),
            risk_score=risk_check.get('daily_pnl_pct', 0),
            regime=regime,
            execution_algo=execution_algo,
            urgency=urgency,
            reasoning=ensemble['reasoning'],
            model_weights=ensemble['model_weights'],
        )
    
    def create_execution_plan(self, signal: TradingSignal) -> ExecutionPlan:
        """Create execution plan for a signal"""
        # Route order
        from .execution import Order, OrderType as ExecOrderType
        
        order = Order(
            order_id=f"ORD_{datetime.now().strftime('%Y%m%d%H%M%S')}",
            symbol=signal.symbol,
            side='buy' if signal.direction == 'long' else 'sell',
            order_type=ExecOrderType.LIMIT,
            quantity=signal.recommended_size,
            price=signal.entry_price,
        )
        
        # Get routing
        routing = self.order_router.route_order(order)
        
        # Create slices based on algorithm
        if signal.execution_algo == 'vwap':
            slices = self.vwap_executor.create_schedule(order, duration_minutes=60)
        elif signal.execution_algo == 'iceberg':
            iceberg = self.iceberg_executor.create_iceberg(order, avg_volume_at_level=1000)
            slices = [{'quantity': iceberg['display_size'], 'type': 'iceberg'}]
        else:
            slices = [{'quantity': signal.recommended_size, 'type': 'single'}]
        
        # Estimate costs
        estimated_cost = signal.recommended_size * signal.entry_price * 0.001  # 10 bps
        
        return ExecutionPlan(
            signal=signal,
            algorithm=signal.execution_algo,
            slices=slices,
            venues=[v[0] for v in routing],
            estimated_cost=estimated_cost,
            estimated_time=60 if signal.execution_algo == 'vwap' else 5,
            risk_checks_passed=True,
        )
    
    def record_trade(self, trade: Dict[str, Any]):
        """Record completed trade"""
        self.trades_executed += 1
        
        # Update dashboard
        self.dashboard.record_trade(trade)
        
        # Update risk monitor
        self.risk_monitor.update_pnl(trade.get('pnl', 0))
        
        # Update analytics
        self.trade_analytics.record_trade(trade)
        
        # Update execution monitor
        self.execution_monitor.record_execution(
            trade.get('order'),
            trade.get('fills', []),
            trade.get('arrival_price', 0),
            trade.get('vwap', 0),
            trade.get('twap', 0),
        )
        
        # Update ensemble with outcome
        self.ensemble.record_outcome(
            trade.get('symbol', ''),
            trade.get('timestamp', datetime.now()),
            'long' if trade.get('pnl', 0) > 0 else 'short',
            trade.get('return', 0),
        )
        
        # Update multi-brain
        self.multi_brain.record_outcome(trade.get('return', 0))
        
        logger.info(f"Trade recorded: {trade.get('symbol')} P&L={trade.get('pnl', 0):.2f}")
    
    async def _monitoring_loop(self):
        """Background monitoring loop"""
        while self.is_running:
            try:
                # Check risk limits
                risk_status = self.risk_monitor.check_limits()
                
                for breach in risk_status:
                    self.alert_system.create_alert(
                        alert_type=self.alert_system.thresholds.keys().__iter__().__next__(),
                        severity=self.alert_system.AlertSeverity.CRITICAL if breach['severity'] == 'critical' else self.alert_system.AlertSeverity.WARNING,
                        message=f"Risk limit breach: {breach['type']}",
                        details=breach,
                    )
                
                await asyncio.sleep(60)  # Check every minute
                
            except Exception as e:
                logger.error(f"Monitoring loop error: {e}")
                await asyncio.sleep(60)
    
    async def _self_analysis_loop(self):
        """Background self-analysis loop"""
        while self.is_running:
            try:
                if self.self_analyzer.should_analyze():
                    trades = list(self.dashboard.trades)[-100:]
                    
                    report = self.self_analyzer.run_analysis(
                        trades=trades,
                        model_predictions={},
                        market_features={},
                    )
                    
                    # Log issues
                    for issue in report.issues:
                        logger.warning(f"Self-analysis issue: {issue.description}")
                    
                    # Update ensemble weights if needed
                    if any(i.issue_type.value == 'model_degradation' for i in report.issues):
                        self.ensemble.update_weights()
                
                await asyncio.sleep(3600)  # Run hourly
                
            except Exception as e:
                logger.error(f"Self-analysis loop error: {e}")
                await asyncio.sleep(3600)
    
    def get_status(self) -> Dict[str, Any]:
        """Get orchestrator status"""
        uptime = (datetime.now() - self.start_time).total_seconds()
        
        return {
            'mode': self.mode.value,
            'is_running': self.is_running,
            'uptime_seconds': uptime,
            'signals_generated': self.signals_generated,
            'trades_executed': self.trades_executed,
            'pending_signals': len(self.pending_signals),
            'active_positions': len(self.current_positions),
            'risk_status': self.risk_monitor.get_risk_status(),
            'active_alerts': len(self.alert_system.get_active_alerts()),
            'model_weights': self.ensemble.get_current_weights(),
            'multi_brain_status': self.multi_brain.get_status(),
        }
    
    def get_dashboard_data(self) -> Dict[str, Any]:
        """Get data for dashboard display"""
        return {
            'status': self.get_status(),
            'performance': self.dashboard.get_dashboard_data(),
            'risk': self.risk_monitor.get_risk_status(),
            'alerts': [a.to_dict() for a in self.alert_system.get_active_alerts()],
            'recent_signals': [s.to_dict() for s in list(self.pending_signals)[-10:]],
        }


# Convenience function for quick start
async def quick_start(config: Dict[str, Any] = None) -> AlphaEngineOrchestrator:
    """Quick start AlphaEngine"""
    orchestrator = AlphaEngineOrchestrator(config)
    await orchestrator.start()
    return orchestrator
