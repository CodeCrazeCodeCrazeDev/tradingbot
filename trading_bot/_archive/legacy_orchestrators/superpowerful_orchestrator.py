"""
SuperPowerful AI Orchestrator
==============================

Master orchestrator integrating all 6 intelligence systems end-to-end.

Integrates:
1. Self-Discovery Engine - Pattern recognition and market intelligence
2. Adaptive Intelligence - Real-time learning and adaptation
3. Predictive Intelligence - Multi-horizon forecasting
4. Strategic Intelligence - Meta-strategy selection
5. Autonomous Innovation - Strategy and feature generation
6. Strategic Self-Evolution - Continuous improvement

Provides unified interface for superpowerful AI trading.
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import logging
import asyncio

from .self_discovery_engine import SelfDiscoveryEngine, MarketRegime
from .adaptive_intelligence import AdaptiveIntelligence, AdaptationMode
from .predictive_intelligence import PredictiveIntelligence, ForecastHorizon
from .strategic_intelligence import StrategicIntelligence, StrategyType
from .autonomous_innovation import AutonomousInnovation
from .strategic_self_evolution import StrategicSelfEvolution

logger = logging.getLogger(__name__)


class AIMode(Enum):
    """AI operation modes"""
    CONSERVATIVE = "conservative"  # Careful, validated decisions
    BALANCED = "balanced"  # Balance between innovation and safety
    AGGRESSIVE = "aggressive"  # Maximum innovation and adaptation
    LEARNING = "learning"  # Focus on learning, minimal trading
    EVOLUTION = "evolution"  # Active self-improvement mode


@dataclass
class SuperPowerfulDecision:
    """Comprehensive AI decision"""
    decision_id: str
    timestamp: datetime
    
    # Market analysis
    discovered_patterns: List[Any]
    market_regime: MarketRegime
    detected_anomalies: List[Any]
    
    # Predictions
    price_forecasts: Dict[ForecastHorizon, Any]
    scenario_forecasts: List[Any]
    trend_prediction: Any
    
    # Strategy
    selected_strategy: StrategyType
    strategy_allocations: List[Any]
    optimal_parameters: Dict[str, float]
    
    # Innovation
    new_strategies: List[Any]
    new_features: List[Any]
    
    # Evolution
    performance_issues: List[Any]
    improvement_recommendations: List[Any]
    learning_insights: List[Any]
    
    # Final decision
    action: str  # 'buy', 'sell', 'hold', 'close'
    confidence: float
    position_size: float
    entry_price: Optional[float]
    stop_loss: Optional[float]
    take_profit: Optional[float]
    reasoning: List[str]
    
    # Metadata
    processing_time: float
    systems_used: List[str]


class SuperPowerfulAI:
    """
    Master AI orchestrator integrating all intelligence systems.
    
    Provides end-to-end superpowerful AI capabilities:
    - Discovers patterns autonomously
    - Adapts to changing conditions
    - Predicts future movements
    - Selects optimal strategies
    - Generates new strategies
    - Continuously self-improves
    """
    
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        
        # AI mode
        self.mode = AIMode(self.config.get('mode', 'balanced'))
        
        # Initialize all 6 intelligence systems
        logger.info("Initializing SuperPowerful AI systems...")
        
        self.self_discovery = SelfDiscoveryEngine(
            config=self.config.get('self_discovery', {})
        )
        
        self.adaptive_intelligence = AdaptiveIntelligence(
            config=self.config.get('adaptive', {})
        )
        
        self.predictive_intelligence = PredictiveIntelligence(
            config=self.config.get('predictive', {})
        )
        
        self.strategic_intelligence = StrategicIntelligence(
            config=self.config.get('strategic', {})
        )
        
        self.autonomous_innovation = AutonomousInnovation(
            config=self.config.get('innovation', {})
        )
        
        self.strategic_evolution = StrategicSelfEvolution(
            config=self.config.get('evolution', {})
        )
        
        # Decision history
        self.decision_history: List[SuperPowerfulDecision] = []
        self.trade_history: List[Dict[str, Any]] = []
        
        # Performance tracking
        self.total_decisions = 0
        self.successful_decisions = 0
        
        # Background tasks
        self.background_tasks = []
        self.evolution_interval = self.config.get('evolution_interval_hours', 6)
        self.innovation_interval = self.config.get('innovation_interval_hours', 12)
        
        logger.info(f"SuperPowerful AI initialized in {self.mode.value} mode")
        logger.info("All 6 intelligence systems active")
    
    async def analyze_and_decide(
        self,
        symbol: str,
        market_data: pd.DataFrame,
        current_position: Optional[Dict[str, Any]] = None
    ) -> SuperPowerfulDecision:
        """
        Comprehensive analysis and decision making using all AI systems.
        
        Args:
            symbol: Trading symbol
            market_data: Historical OHLCV data
            current_position: Current position info (if any)
        
        Returns:
            SuperPowerful AI decision
        """
        start_time = datetime.now()
        decision_id = f"decision_{self.total_decisions}_{start_time.strftime('%Y%m%d%H%M%S')}"
        
        try:
            logger.info(f"Starting SuperPowerful AI analysis for {symbol}")
            
            # ================================================================
            # PHASE 1: SELF-DISCOVERY
            # ================================================================
            logger.debug("Phase 1: Self-Discovery")
            
            # Discover patterns
            discovered_patterns = await self.self_discovery.discover_patterns(
                market_data=market_data,
                symbol=symbol,
                timeframe='M15'
            )
            
            # Detect market regime
            market_regime = await self.self_discovery.detect_regime(
                market_data=market_data,
                symbol=symbol
            )
            
            # Detect anomalies
            detected_anomalies = await self.self_discovery.detect_anomalies(
                market_data=market_data,
                symbol=symbol
            )
            
            # ================================================================
            # PHASE 2: PREDICTIVE INTELLIGENCE
            # ================================================================
            logger.debug("Phase 2: Predictive Intelligence")
            
            # Multi-horizon forecasts
            price_forecasts = await self.predictive_intelligence.forecast_price(
                market_data=market_data,
                symbol=symbol,
                horizons=[
                    ForecastHorizon.SHORT,
                    ForecastHorizon.MEDIUM,
                    ForecastHorizon.LONG
                ]
            )
            
            # Scenario forecasts
            scenario_forecasts = await self.predictive_intelligence.forecast_scenarios(
                market_data=market_data,
                symbol=symbol
            )
            
            # Trend reversal prediction
            trend_prediction = await self.predictive_intelligence.predict_trend_reversal(
                market_data=market_data,
                symbol=symbol
            )
            
            # ================================================================
            # PHASE 3: STRATEGIC INTELLIGENCE
            # ================================================================
            logger.debug("Phase 3: Strategic Intelligence")
            
            # Prepare market state
            market_state = {
                'volatility': market_regime.volatility,
                'trend_strength': market_regime.trend_strength,
                'momentum': market_regime.momentum,
                'regime': market_regime.regime.value
            }
            
            # Select optimal strategy
            strategic_decision = await self.strategic_intelligence.select_optimal_strategy(
                market_state=market_state
            )
            
            # Get optimal parameters
            optimal_parameters = await self.adaptive_intelligence.get_optimal_parameters(
                market_state=market_state,
                strategy_name=strategic_decision.primary_strategy.value
            )
            
            # ================================================================
            # PHASE 4: ADAPTIVE INTELLIGENCE
            # ================================================================
            logger.debug("Phase 4: Adaptive Intelligence")
            
            # Predict trade outcome
            trade_params = {
                'entry_confidence': strategic_decision.confidence,
                'position_size': optimal_parameters.get('position_size_multiplier', 1.0)
            }
            
            outcome_prediction = await self.adaptive_intelligence.predict_trade_outcome(
                market_state=market_state,
                trade_params=trade_params
            )
            
            # ================================================================
            # PHASE 5: DECISION SYNTHESIS
            # ================================================================
            logger.debug("Phase 5: Decision Synthesis")
            
            # Synthesize all intelligence into final decision
            decision = self._synthesize_decision(
                decision_id=decision_id,
                symbol=symbol,
                market_data=market_data,
                discovered_patterns=discovered_patterns,
                market_regime=market_regime,
                detected_anomalies=detected_anomalies,
                price_forecasts=price_forecasts,
                scenario_forecasts=scenario_forecasts,
                trend_prediction=trend_prediction,
                strategic_decision=strategic_decision,
                optimal_parameters=optimal_parameters,
                outcome_prediction=outcome_prediction,
                current_position=current_position
            )
            
            # ================================================================
            # PHASE 6: INNOVATION (if in aggressive/evolution mode)
            # ================================================================
            if self.mode in [AIMode.AGGRESSIVE, AIMode.EVOLUTION]:
                logger.debug("Phase 6: Autonomous Innovation")
                
                # Generate new strategies (occasionally)
                if self.total_decisions % 50 == 0:
                    new_strategy = await self.autonomous_innovation.generate_new_strategy(
                        market_data=market_data
                    )
                    decision.new_strategies = [new_strategy] if new_strategy else []
                
                # Generate new features (occasionally)
                if self.total_decisions % 30 == 0:
                    new_feature = await self.autonomous_innovation.generate_new_feature(
                        market_data=market_data
                    )
                    decision.new_features = [new_feature] if new_feature else []
            
            # Calculate processing time
            decision.processing_time = (datetime.now() - start_time).total_seconds()
            
            # Store decision
            self.decision_history.append(decision)
            self.total_decisions += 1
            
            # Keep only recent history
            if len(self.decision_history) > 1000:
                self.decision_history = self.decision_history[-1000:]
            
            logger.info(f"SuperPowerful AI decision complete: {decision.action} "
                       f"(confidence: {decision.confidence:.2f}, "
                       f"processing: {decision.processing_time:.2f}s)")
            
            return decision
            
        except Exception as e:
            logger.error(f"Error in SuperPowerful AI analysis: {e}")
            return self._get_default_decision(decision_id, symbol)
    
    def _synthesize_decision(
        self,
        decision_id: str,
        symbol: str,
        market_data: pd.DataFrame,
        discovered_patterns: List[Any],
        market_regime: Any,
        detected_anomalies: List[Any],
        price_forecasts: Dict[ForecastHorizon, Any],
        scenario_forecasts: List[Any],
        trend_prediction: Any,
        strategic_decision: Any,
        optimal_parameters: Dict[str, float],
        outcome_prediction: Dict[str, float],
        current_position: Optional[Dict[str, Any]]
    ) -> SuperPowerfulDecision:
        """Synthesize all intelligence into final decision"""
        
        try:
            current_price = market_data['close'].iloc[-1]
            
            # Determine action based on all intelligence
            action = 'hold'
            confidence = 0.5
            reasoning = []
            
            # Check for critical anomalies
            critical_anomalies = [a for a in detected_anomalies if a.severity > 0.8]
            if critical_anomalies:
                action = 'hold'
                confidence = 0.3
                reasoning.append(f"Critical anomalies detected: {len(critical_anomalies)}")
                reasoning.append("Waiting for market stability")
            else:
                # Get short-term forecast
                short_forecast = price_forecasts.get(ForecastHorizon.SHORT)
                medium_forecast = price_forecasts.get(ForecastHorizon.MEDIUM)
                
                # Bullish signals
                bullish_score = 0.0
                bearish_score = 0.0
                
                # Forecast signals
                if short_forecast and short_forecast.probability_up > 0.6:
                    bullish_score += 0.3
                    reasoning.append(f"Short-term forecast bullish ({short_forecast.probability_up:.1%})")
                elif short_forecast and short_forecast.probability_down > 0.6:
                    bearish_score += 0.3
                    reasoning.append(f"Short-term forecast bearish ({short_forecast.probability_down:.1%})")
                
                # Regime signals
                if market_regime.regime.value in ['trending_up', 'breakout']:
                    bullish_score += 0.2
                    reasoning.append(f"Market regime: {market_regime.regime.value}")
                elif market_regime.regime.value in ['trending_down']:
                    bearish_score += 0.2
                    reasoning.append(f"Market regime: {market_regime.regime.value}")
                
                # Trend prediction
                if trend_prediction.reversal_probability < 0.3:
                    if trend_prediction.current_trend == 'up':
                        bullish_score += 0.2
                        reasoning.append("Uptrend continuation likely")
                    elif trend_prediction.current_trend == 'down':
                        bearish_score += 0.2
                        reasoning.append("Downtrend continuation likely")
                
                # Outcome prediction
                if outcome_prediction.get('recommendation') == 'take_trade':
                    if outcome_prediction.get('predicted_profit', 0) > 0:
                        bullish_score += 0.3
                        reasoning.append("Adaptive AI recommends long trade")
                    else:
                        bearish_score += 0.3
                        reasoning.append("Adaptive AI recommends short trade")
                
                # Determine action
                if bullish_score > bearish_score and bullish_score >= 0.6:
                    action = 'buy'
                    confidence = min(bullish_score, 0.95)
                elif bearish_score > bullish_score and bearish_score >= 0.6:
                    action = 'sell'
                    confidence = min(bearish_score, 0.95)
                else:
                    action = 'hold'
                    confidence = 0.5
                    reasoning.append("Signals not strong enough for entry")
            
            # Position sizing
            base_position_size = 1.0
            position_size_multiplier = optimal_parameters.get('position_size_multiplier', 1.0)
            risk_multiplier = optimal_parameters.get('risk_multiplier', 1.0)
            
            position_size = base_position_size * position_size_multiplier * risk_multiplier
            
            # Adjust for confidence
            position_size *= confidence
            
            # Adjust for volatility
            if market_regime.volatility > 0.02:
                position_size *= 0.7
                reasoning.append("Position size reduced due to high volatility")
            
            # Calculate stop loss and take profit
            atr = self._calculate_atr(market_data)
            
            stop_loss_multiplier = optimal_parameters.get('stop_loss_multiplier', 1.0)
            take_profit_multiplier = optimal_parameters.get('take_profit_multiplier', 1.0)
            
            if action == 'buy':
                entry_price = current_price
                stop_loss = current_price - (atr * 2.0 * stop_loss_multiplier)
                take_profit = current_price + (atr * 3.0 * take_profit_multiplier)
            elif action == 'sell':
                entry_price = current_price
                stop_loss = current_price + (atr * 2.0 * stop_loss_multiplier)
                take_profit = current_price - (atr * 3.0 * take_profit_multiplier)
            else:
                entry_price = None
                stop_loss = None
                take_profit = None
            
            # Create decision
            decision = SuperPowerfulDecision(
                decision_id=decision_id,
                timestamp=datetime.now(),
                discovered_patterns=discovered_patterns,
                market_regime=market_regime.regime,
                detected_anomalies=detected_anomalies,
                price_forecasts=price_forecasts,
                scenario_forecasts=scenario_forecasts,
                trend_prediction=trend_prediction,
                selected_strategy=strategic_decision.primary_strategy,
                strategy_allocations=strategic_decision.allocations,
                optimal_parameters=optimal_parameters,
                new_strategies=[],
                new_features=[],
                performance_issues=[],
                improvement_recommendations=[],
                learning_insights=[],
                action=action,
                confidence=confidence,
                position_size=position_size,
                entry_price=entry_price,
                stop_loss=stop_loss,
                take_profit=take_profit,
                reasoning=reasoning,
                processing_time=0.0,
                systems_used=[
                    'self_discovery',
                    'adaptive_intelligence',
                    'predictive_intelligence',
                    'strategic_intelligence'
                ]
            )
            
            return decision
            
        except Exception as e:
            logger.error(f"Error synthesizing decision: {e}")
            return self._get_default_decision(decision_id, symbol)
    
    def _calculate_atr(self, market_data: pd.DataFrame, period: int = 14) -> float:
        """Calculate Average True Range"""
        try:
            high = market_data['high'].values
            low = market_data['low'].values
            close = market_data['close'].values
            
            tr = np.maximum(
                high - low,
                np.maximum(
                    np.abs(high - np.roll(close, 1)),
                    np.abs(low - np.roll(close, 1))
                )
            )
            
            atr = pd.Series(tr).rolling(period).mean().iloc[-1]
            
            return float(atr) if not np.isnan(atr) else 0.001
            
        except Exception:
            return 0.001
    
    def _get_default_decision(self, decision_id: str, symbol: str) -> SuperPowerfulDecision:
        """Get default decision in case of error"""
        
        return SuperPowerfulDecision(
            decision_id=decision_id,
            timestamp=datetime.now(),
            discovered_patterns=[],
            market_regime=MarketRegime.UNKNOWN,
            detected_anomalies=[],
            price_forecasts={},
            scenario_forecasts=[],
            trend_prediction=None,
            selected_strategy=StrategyType.TREND_FOLLOWING,
            strategy_allocations=[],
            optimal_parameters={},
            new_strategies=[],
            new_features=[],
            performance_issues=[],
            improvement_recommendations=[],
            learning_insights=[],
            action='hold',
            confidence=0.0,
            position_size=0.0,
            entry_price=None,
            stop_loss=None,
            take_profit=None,
            reasoning=["Error in analysis - defaulting to hold"],
            processing_time=0.0,
            systems_used=[]
        )
    
    async def learn_from_trade(
        self,
        trade_result: Dict[str, Any],
        market_state: Dict[str, Any]
    ):
        """
        Learn from completed trade across all systems.
        
        Args:
            trade_result: Trade outcome information
            market_state: Market conditions during trade
        """
        try:
            # Store in history
            self.trade_history.append({
                'timestamp': datetime.now(),
                'trade': trade_result,
                'market_state': market_state
            })
            
            # Update success rate
            if trade_result.get('profit', 0) > 0:
                self.successful_decisions += 1
            
            # Adaptive learning
            await self.adaptive_intelligence.learn_from_trade(
                trade_data=trade_result,
                market_state=market_state
            )
            
            # Update strategy performance
            strategy_type = trade_result.get('strategy_type')
            if strategy_type:
                await self.strategic_intelligence.update_strategy_performance(
                    strategy_type=strategy_type,
                    trade_result=trade_result
                )
            
            logger.debug("Learning from trade complete")
            
        except Exception as e:
            logger.error(f"Error learning from trade: {e}")
    
    async def run_evolution_cycle(self):
        """Run a complete evolution cycle"""
        try:
            logger.info("Starting evolution cycle")
            
            # Prepare current metrics
            current_metrics = self._calculate_current_metrics()
            
            # Run evolution
            cycle = await self.strategic_evolution.execute_evolution_cycle(
                trade_history=self.trade_history,
                current_metrics=current_metrics
            )
            
            logger.info(f"Evolution cycle complete: {cycle.improvements_implemented} improvements")
            
        except Exception as e:
            logger.error(f"Error in evolution cycle: {e}")
    
    def _calculate_current_metrics(self) -> Dict[str, float]:
        """Calculate current performance metrics"""
        
        if not self.trade_history:
            return {
                'win_rate': 0.5,
                'profit_factor': 1.0,
                'sharpe_ratio': 0.0,
                'max_drawdown': 0.0
            }
        
        recent_trades = self.trade_history[-100:]
        
        wins = sum(1 for t in recent_trades if t['trade'].get('profit', 0) > 0)
        total = len(recent_trades)
        
        win_rate = wins / total if total > 0 else 0.5
        
        total_profit = sum(t['trade'].get('profit', 0) for t in recent_trades if t['trade'].get('profit', 0) > 0)
        total_loss = abs(sum(t['trade'].get('profit', 0) for t in recent_trades if t['trade'].get('profit', 0) < 0))
        
        profit_factor = total_profit / total_loss if total_loss > 0 else 1.0
        
        return {
            'win_rate': win_rate,
            'profit_factor': profit_factor,
            'sharpe_ratio': 0.0,
            'max_drawdown': 0.0,
            'total_trades': total
        }
    
    async def start_background_tasks(self):
        """Start background evolution and innovation tasks"""
        
        async def evolution_task():
            while True:
                try:
                    await asyncio.sleep(self.evolution_interval * 3600)
                    await self.run_evolution_cycle()
                except Exception as e:
                    logger.error(f"Error in evolution task: {e}")
        
        async def innovation_task():
            while True:
                try:
                    await asyncio.sleep(self.innovation_interval * 3600)
                    # Generate innovations
                    if len(self.trade_history) >= 50:
                        market_data = pd.DataFrame()  # Would get from data source
                        await self.autonomous_innovation.generate_new_strategy(market_data)
                        await self.autonomous_innovation.generate_new_feature(market_data)
                except Exception as e:
                    logger.error(f"Error in innovation task: {e}")
        
        # Start tasks
        self.background_tasks.append(asyncio.create_task(evolution_task()))
        self.background_tasks.append(asyncio.create_task(innovation_task()))
        
        logger.info("Background tasks started")
    
    def get_comprehensive_statistics(self) -> Dict[str, Any]:
        """Get comprehensive statistics from all systems"""
        
        return {
            'superpowerful_ai': {
                'mode': self.mode.value,
                'total_decisions': self.total_decisions,
                'successful_decisions': self.successful_decisions,
                'success_rate': self.successful_decisions / self.total_decisions if self.total_decisions > 0 else 0.0,
                'total_trades': len(self.trade_history),
                'recent_decisions': [
                    {
                        'timestamp': d.timestamp.isoformat(),
                        'action': d.action,
                        'confidence': d.confidence,
                        'processing_time': d.processing_time
                    }
                    for d in self.decision_history[-5:]
                ]
            },
            'self_discovery': self.self_discovery.get_statistics(),
            'adaptive_intelligence': self.adaptive_intelligence.get_learning_statistics(),
            'predictive_intelligence': self.predictive_intelligence.get_prediction_statistics(),
            'strategic_intelligence': self.strategic_intelligence.get_strategic_statistics(),
            'autonomous_innovation': self.autonomous_innovation.get_innovation_statistics(),
            'strategic_evolution': self.strategic_evolution.get_evolution_statistics()
        }
