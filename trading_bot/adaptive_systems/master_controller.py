import logging
logger = logging.getLogger(__name__)
"""Master Controller for Self-Improving Trading Bot.

This module orchestrates all adaptive systems and self-improvement capabilities
to create a unified, continuously evolving trading intelligence.
"""

import asyncio
import threading
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional
from dataclasses import dataclass, field
from loguru import logger
import pandas as pd

from .market_regime import MarketRegimeDetector, MarketRegime
from .adaptive_risk import AdaptiveRiskManager
from .strategy_selector import StrategySelector, StrategyType
from .parameter_optimizer import ParameterOptimizer
from .self_improvement import SelfImprovementEngine, ModificationStatus
from .adaptive_learning import AdaptiveLearningEngine, ModelType
from .feedback_loops import PerformanceFeedbackSystem
from .meta_learning import MetaLearningEngine
from .system_health import SystemHealthMonitor
from .advanced_pattern_recognition import AdvancedPatternRecognizer
from .real_time_sentiment import RealTimeSentimentEngine
from .market_microstructure import MarketMicrostructureAnalyzer
from .ensemble_learning import EnsembleLearningSystem, StrategyPrediction, StrategyType as EnsembleStrategyType

# Import self-improvement code generation system
from .knowledge_acquisition.knowledge_base import KnowledgeBase
from .code_generation.self_modification_engine import SelfModificationEngine


@dataclass
class TradingDecision:
    """Comprehensive trading decision with all adaptive inputs."""
    symbol: str
    action: str  # 'buy', 'sell', 'hold', 'close'
    confidence: float
    position_size: float
    stop_loss: float
    take_profit: float
    strategy: StrategyType
    regime: MarketRegime
    risk_score: float
    sentiment_score: float
    pattern_signals: List[Any] = field(default_factory=list)
    microstructure_score: float = 0.0
    adaptive_adjustments: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.now)


class AdaptiveTradingMaster:
    """Master controller that orchestrates all adaptive systems."""
    
    def __init__(self, config: Optional[Dict] = None, enable_self_improvement: bool = False, 
                 self_improvement_config: Optional[Dict] = None):
        """Initialize the master adaptive trading system.
        
        Args:
            config: Configuration dictionary for adaptive systems
            enable_self_improvement: Whether to enable self-improvement capabilities
            self_improvement_config: Configuration for self-improvement system
        """
        self.config = config or {}
        self.enable_self_improvement = enable_self_improvement
        self.self_improvement_config = self_improvement_config or {}
        
        # Initialize all adaptive systems
        self.regime_detector = MarketRegimeDetector(config.get('regime_detection', {}))
        self.risk_manager = AdaptiveRiskManager(config.get('risk_management', {}))
        self.strategy_selector = StrategySelector(config.get('strategy_selection', {}))
        self.parameter_optimizer = ParameterOptimizer(config.get('parameter_optimization', {}))
        self.self_improvement = SelfImprovementEngine(config.get('self_improvement', {}))
        self.adaptive_learning = AdaptiveLearningEngine(config.get('adaptive_learning', {}))
        self.feedback_system = PerformanceFeedbackSystem(config.get('feedback_system', {}))
        self.meta_learning = MetaLearningEngine(config.get('meta_learning', {}))
        self.health_monitor = SystemHealthMonitor(config.get('health_monitor', {}))
        
        # Advanced analysis systems
        self.pattern_recognizer = AdvancedPatternRecognizer(config.get('pattern_recognition', {}))
        self.sentiment_engine = RealTimeSentimentEngine(config.get('sentiment_engine', {}))
        self.microstructure_analyzer = MarketMicrostructureAnalyzer(config.get('microstructure', {}))
        
        # Ensemble learning system
        self.ensemble_system = EnsembleLearningSystem(config.get('ensemble_learning', {}))
        
        # System state
        self.current_regime = None
        self.current_strategy = None
        self.system_active = False
        self.learning_active = True
        
        # Performance tracking
        self.trade_history = []
        self.learning_history = []
        self.system_metrics = {}
        
        # Initialize self-improvement system if enabled
        self.self_improvement_engine = None
        if self.enable_self_improvement:
            self._init_self_improvement()
            logger.info("AdaptiveTradingMaster initialized with full self-improvement capabilities")
        else:
            logger.info("AdaptiveTradingMaster initialized with adaptive capabilities")
    
    def _init_self_improvement(self):
        """Initialize the self-improvement system."""
        try:
            # Create knowledge base directory if it doesn't exist
            import os
            kb_dir = self.self_improvement_config.get('knowledge_base_dir', 'knowledge_base')
            os.makedirs(kb_dir, exist_ok=True)
            
            # Initialize knowledge base
            kb_path = os.path.join(kb_dir, 'knowledge_base.db')
            self.knowledge_base = KnowledgeBase(kb_path)
            
            # Get API keys from config
            api_keys = self.self_improvement_config.get('api_keys', {})
            
            # Initialize self-modification engine
            self.self_improvement_engine = SelfModificationEngine(
                self.knowledge_base,
                api_keys=api_keys,
                config_path=self.self_improvement_config.get('engine_config_path')
            )
            
            logger.info("Self-improvement system initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize self-improvement system: {e}")
            self.self_improvement_engine = None
    
    async def start_system(self):
        """Start all adaptive systems."""
        logger.info("Starting adaptive trading master system")
        
        # Start health monitoring
        self.health_monitor.start_monitoring()
        
        # Start background learning processes
        await self._start_learning_processes()
        
        # Start self-improvement engine if enabled
        if self.enable_self_improvement and self.self_improvement_engine:
            self.self_improvement_engine.start_processing()
            logger.info("Self-improvement engine started")
        
        self.system_active = True
        logger.info("Adaptive trading master system fully operational")
    
    async def stop_system(self):
        """Stop all adaptive systems."""
        logger.info("Stopping adaptive trading master system")
        
        self.system_active = False
        self.learning_active = False
        
        # Stop health monitoring
        self.health_monitor.stop_monitoring()
        
        # Stop self-improvement engine if enabled
        if self.enable_self_improvement and self.self_improvement_engine:
            self.self_improvement_engine.stop_processing()
            logger.info("Self-improvement engine stopped")
        
        logger.info("Adaptive trading master system stopped")
    
    async def _start_learning_processes(self):
        """Start background learning and optimization processes."""
        # Start continuous learning in background
        asyncio.create_task(self._continuous_learning_loop())
        asyncio.create_task(self._meta_learning_loop())
        asyncio.create_task(self._system_optimization_loop())
        
        # Start self-improvement scheduling if enabled
        if self.enable_self_improvement and self.self_improvement_engine:
            asyncio.create_task(self._self_improvement_scheduling_loop())
    
    async def _continuous_learning_loop(self):
        """Continuous learning background process."""
        while self.learning_active:
            try:
                # Process any queued learning tasks
                if len(self.trade_history) >= 10:
                    recent_trades = self.trade_history[-10:]
                    
                    # Learn from recent trades
                    for trade in recent_trades:
                        self.self_improvement.learn_from_trade(trade)
                        self.feedback_system.process_trade_feedback(trade)
                    
                    # Update learning models
                    await self._update_learning_models(recent_trades)
                
                await asyncio.sleep(300)  # Run every 5 minutes
                
            except Exception as e:
                logger.error(f"Error in continuous learning loop: {e}")
                await asyncio.sleep(60)
    
    async def _meta_learning_loop(self):
        """Meta-learning background process."""
        while self.learning_active:
            try:
                if len(self.trade_history) >= 100:
                    # Discover new strategies
                    new_strategies = self.meta_learning.discover_new_strategies(self.trade_history)
                    
                    if new_strategies:
                        logger.info(f"Meta-learning discovered {len(new_strategies)} new strategies")
                    
                    # Optimize learning process
                    self.meta_learning.optimize_learning_process(self.learning_history)
                
                await asyncio.sleep(3600)  # Run every hour
                
            except Exception as e:
                logger.error(f"Error in meta-learning loop: {e}")
                await asyncio.sleep(300)
    
    async def _system_optimization_loop(self):
        """System-wide optimization background process."""
        while self.learning_active:
            try:
                # Get improvement recommendations
                recommendations = self.self_improvement.get_improvement_recommendations()
                
                if recommendations:
                    logger.info(f"System generated {len(recommendations)} improvement recommendations")
                    await self._apply_system_improvements(recommendations)
                
                # Update system health metrics
                self._update_system_metrics()
                
                await asyncio.sleep(1800)  # Run every 30 minutes
                
            except Exception as e:
                logger.error(f"Error in system optimization loop: {e}")
                await asyncio.sleep(300)
    
    async def _self_improvement_scheduling_loop(self):
        """Schedule and manage self-improvement tasks."""
        if not self.self_improvement_engine:
            return
            
        # Wait for initial trading data to accumulate
        await asyncio.sleep(3600)  # Wait 1 hour before starting self-improvement
        
        while self.learning_active and self.enable_self_improvement:
            try:
                # Check if it's time to schedule improvements
                schedule_improvements = self._should_schedule_improvements()
                
                if schedule_improvements:
                    await self._schedule_improvement_tasks()
                
                # Process any pending approvals
                await self._process_pending_approvals()
                
                # Wait before next check
                await asyncio.sleep(900)  # Check every 15 minutes
                
            except Exception as e:
                logger.error(f"Error in self-improvement scheduling loop: {e}")
                await asyncio.sleep(300)
    
    async def _update_learning_models(self, trades: List[Dict[str, Any]]):
        """Update machine learning models with new trade data."""
        for trade in trades:
            # Extract features for different model types
            features = self._extract_trade_features(trade)
            
            # Update price prediction model
            if 'price_change' in trade:
                self.adaptive_learning.add_training_sample(
                    ModelType.PRICE_PREDICTOR,
                    features,
                    trade['price_change']
                )
            
            # Update regime classifier
            if 'regime' in trade:
                regime_features = features[:10]  # Use subset for regime classification
                regime_target = list(MarketRegime).index(MarketRegime(trade['regime']))
                self.adaptive_learning.add_training_sample(
                    ModelType.REGIME_CLASSIFIER,
                    regime_features,
                    regime_target
                )
            
            # Update risk estimator
            if 'max_drawdown' in trade:
                self.adaptive_learning.add_training_sample(
                    ModelType.RISK_ESTIMATOR,
                    features,
                    trade['max_drawdown']
                )
    
    def _extract_trade_features(self, trade: Dict[str, Any]) -> List[float]:
        """Extract feature vector from trade data."""
        features = [
            trade.get('entry_confidence', 0.5),
            trade.get('sentiment_score', 0.0),
            trade.get('volatility', 0.02),
            trade.get('trend_strength', 0.0),
            trade.get('risk_reward_ratio', 1.0),
            trade.get('position_size', 0.01),
            trade.get('hold_time_minutes', 60) / 1440,  # Normalize to days
            1.0 if trade.get('regime') == 'trending_bull' else 0.0,
            1.0 if trade.get('regime') == 'trending_bear' else 0.0,
            1.0 if trade.get('regime') == 'ranging' else 0.0,
            1.0 if trade.get('regime') == 'high_volatility' else 0.0,
            trade.get('volume_ratio', 1.0),
            trade.get('news_impact', 0.0),
            trade.get('correlation_score', 0.0),
            trade.get('market_stress', 0.0)
        ]
        return features
    
    async def _apply_system_improvements(self, recommendations: List[Dict[str, Any]]):
        """Apply system improvement recommendations."""
        for rec in recommendations[:3]:  # Apply top 3 recommendations
            try:
                if rec['type'] == 'fix_mistake':
                    await self._apply_mistake_fix(rec)
                elif rec['type'] == 'amplify_success':
                    await self._apply_success_amplification(rec)
                
            except Exception as e:
                logger.error(f"Error applying improvement recommendation: {e}")
    
    async def _apply_mistake_fix(self, recommendation: Dict[str, Any]):
        """Apply a mistake-fixing recommendation."""
        description = recommendation.get('description', '')
        
        if 'overconfidence' in description.lower():
            # Reduce confidence thresholds
            current_params = self.parameter_optimizer.current_parameters
            current_params['entry_confidence'] *= 0.9
            logger.info("Applied overconfidence fix: reduced entry confidence threshold")
            
        elif 'risk' in description.lower():
            # Tighten risk management
            current_params = self.parameter_optimizer.current_parameters
            current_params['risk_per_trade'] *= 0.8
            logger.info("Applied risk management fix: reduced risk per trade")
    
    async def _apply_success_amplification(self, recommendation: Dict[str, Any]):
        """Apply a success amplification recommendation."""
        description = recommendation.get('description', '')
        
        if 'sentiment' in description.lower():
            # Increase sentiment weight
            current_params = self.parameter_optimizer.current_parameters
            current_params['sentiment_weight'] *= 1.1
            logger.info("Applied success amplification: increased sentiment weight")
    
    def _update_system_metrics(self):
        """Update comprehensive system metrics."""
        self.system_metrics = {
            'regime_detection_accuracy': self._calculate_regime_accuracy(),
            'strategy_selection_effectiveness': self._calculate_strategy_effectiveness(),
            'risk_management_performance': self._calculate_risk_performance(),
            'learning_progress': self._calculate_learning_progress(),
            'system_health_score': self._calculate_system_health(),
            'adaptation_rate': self._calculate_adaptation_rate()
        }
    
    def _calculate_regime_accuracy(self) -> float:
        """Calculate regime detection accuracy."""
        if len(self.trade_history) < 10:
            return 0.5
        
        recent_trades = self.trade_history[-50:]
        correct_predictions = 0
        
        for trade in recent_trades:
            predicted_regime = trade.get('predicted_regime')
            actual_regime = trade.get('actual_regime')
            if predicted_regime == actual_regime:
                correct_predictions += 1
        
        return correct_predictions / len(recent_trades) if recent_trades else 0.5
    
    def _calculate_strategy_effectiveness(self) -> float:
        """Calculate strategy selection effectiveness."""
        return self.strategy_selector.get_strategy_summary().get('average_performance', 0.5)
    
    def _calculate_risk_performance(self) -> float:
        """Calculate risk management performance."""
        risk_summary = self.risk_manager.get_risk_summary()
        return 1.0 - risk_summary.get('current_drawdown', 0.0)
    
    def _calculate_learning_progress(self) -> float:
        """Calculate overall learning progress."""
        improvement_summary = self.self_improvement.get_learning_summary()
        return improvement_summary.get('recent_performance', 0.0) / 100.0 + 0.5
    
    def _calculate_system_health(self) -> float:
        """Calculate overall system health score."""
        health_summary = self.health_monitor.get_health_summary()
        status = health_summary.get('overall_status', 'healthy')
        
        health_scores = {
            'healthy': 1.0,
            'warning': 0.7,
            'critical': 0.4,
            'emergency': 0.1
        }
        
        return health_scores.get(status, 0.5)
    
    def _calculate_adaptation_rate(self) -> float:
        """Calculate how quickly the system adapts to changes."""
        if len(self.learning_history) < 5:
            return 0.5
        
        recent_adaptations = self.learning_history[-10:]
        successful_adaptations = sum(1 for a in recent_adaptations if a.get('improvement', 0) > 0)
        
        return successful_adaptations / len(recent_adaptations)
    
    async def make_trading_decision(self, market_data: Dict[str, Any]) -> TradingDecision:
        """Make comprehensive trading decision using all adaptive systems.
        
        Args:
            market_data: Dictionary containing market data and analysis
                Required keys:
                - symbol: Trading symbol
                - price_data: DataFrame with OHLCV data
                - current_price: Current market price
                Optional keys:
                - sentiment_score: Market sentiment score
                - news_sentiment: News sentiment analysis
                - volatility: Market volatility
                - volume_ratio: Volume analysis
                
        Returns:
            TradingDecision with comprehensive analysis
        """
        """Make comprehensive trading decision using all adaptive systems."""
        try:
            # Extract required data
            symbol = market_data['symbol']
            price_data = market_data['price_data']
            
            # Get current market regime
            regime_signal = await self.regime_detector.detect_regime_async(price_data)
            self.current_regime = regime_signal.regime
            
            # Get strategy recommendation
            strategy_signal = await self.strategy_selector.select_strategy_async(
                regime_signal.regime, price_data
            )
            self.current_strategy = strategy_signal.strategy
            
            # Get risk parameters
            risk_params = await self.risk_manager.calculate_risk_async(
                symbol, price_data, regime_signal.regime
            )
            
            # Get advanced analysis
            pattern_signal = await self.pattern_recognizer.analyze_patterns_async(price_data)
            
            # Use provided sentiment if available, otherwise fetch it
            sentiment_data = market_data.get('news_sentiment', None)
            if not sentiment_data:
                sentiment_data = await self.sentiment_engine.get_market_sentiment_async(symbol)
            
            microstructure_signal = await self.microstructure_analyzer.analyze_microstructure_async(price_data)
            
            # Create strategy predictions for ensemble
            strategy_predictions = [
                StrategyPrediction(
                    strategy_type=EnsembleStrategyType.TREND_FOLLOWING,
                    prediction=1.0 if strategy_signal.strategy == StrategyType.AGGRESSIVE else 0.0,
                    confidence=strategy_signal.confidence,
                    features={'regime': regime_signal.regime.value}
                ),
                StrategyPrediction(
                    strategy_type=EnsembleStrategyType.MEAN_REVERSION,
                    prediction=pattern_signal.strength,
                    confidence=pattern_signal.confidence,
                    features={'pattern_count': len(pattern_signal.patterns)}
                ),
                StrategyPrediction(
                    strategy_type=EnsembleStrategyType.MOMENTUM,
                    prediction=sentiment_data.overall_sentiment,
                    confidence=sentiment_data.confidence,
                    features={'sentiment': sentiment_data.overall_sentiment}
                ),
                StrategyPrediction(
                    strategy_type=EnsembleStrategyType.ARBITRAGE,
                    prediction=microstructure_signal.liquidity_score,
                    confidence=microstructure_signal.confidence,
                    features={'liquidity': microstructure_signal.liquidity_score}
                )
            ]
            
            # Get ensemble prediction
            ensemble_prediction = await self.ensemble_system.predict_async(strategy_predictions)
            
            # Combine all signals for decision (including ensemble)
            confidence = self._calculate_combined_confidence([
                regime_signal.confidence,
                strategy_signal.confidence,
                pattern_signal.confidence,
                sentiment_data.confidence,
                microstructure_signal.confidence,
                ensemble_prediction.confidence
            ])
            
            # Determine action based on combined analysis and ensemble
            action = self._determine_action_with_ensemble(
                strategy_signal, pattern_signal, sentiment_data, 
                microstructure_signal, ensemble_prediction
            )
            
            # Calculate position size with risk management and ensemble weighting
            base_position_size = risk_params.max_position_size * confidence
            ensemble_adjusted_size = base_position_size * ensemble_prediction.final_prediction
            position_size = max(0.0, min(ensemble_adjusted_size, risk_params.max_position_size))
            
            decision = TradingDecision(
                symbol=symbol,
                action=action,
                confidence=confidence,
                position_size=position_size,
                stop_loss=risk_params.stop_loss,
                take_profit=risk_params.take_profit,
                regime=regime_signal.regime,
                strategy=strategy_signal.strategy,
                risk_score=risk_params.risk_score,
                pattern_signals=[pattern_signal],
                sentiment_score=sentiment_data.overall_sentiment,
                microstructure_score=microstructure_signal.liquidity_score,
                timestamp=datetime.now()
            )
            
            # Log decision for learning
            await self._log_decision(decision)
            
            # Update ensemble system with decision for learning
            await self.ensemble_system.update_performance_async(
                strategy_predictions, ensemble_prediction, confidence
            )
            
            return decision
            
        except Exception as e:
            logger.error(f"Error making trading decision: {e}")
            # Return safe default decision
            return TradingDecision(
                symbol=symbol,
                action='hold',
                confidence=0.0,
                position_size=0.0,
                stop_loss=0.0,
                take_profit=0.0,
                regime=MarketRegime.SIDEWAYS,
                strategy=StrategyType.CONSERVATIVE,
                risk_score=1.0,
                pattern_signals=[],
                sentiment_score=0.0,
                microstructure_score=0.0,
                timestamp=datetime.now()
            )
    
    def _determine_action_with_ensemble(self, strategy_signal, pattern_signal, 
                                       sentiment_data, microstructure_signal, 
                                       ensemble_prediction) -> str:
        """Determine trading action incorporating ensemble prediction."""
        # Base action from ensemble prediction
        if ensemble_prediction.final_prediction > 0.6:
            base_action = 'buy'
        elif ensemble_prediction.final_prediction < -0.6:
            base_action = 'sell'
        else:
            base_action = 'hold'
        
        # Apply additional filters
        if sentiment_data.overall_sentiment < -0.7:
            return 'sell' if base_action != 'hold' else 'hold'
        elif sentiment_data.overall_sentiment > 0.7:
            return 'buy' if base_action != 'hold' else 'hold'
        
        return base_action
    
    async def record_trade_outcome(self, decision: TradingDecision, outcome: Dict[str, Any]):
        """Record the outcome of a trading decision for learning."""
        trade_record = {
            'decision': decision,
            'outcome': outcome,
            'pnl': outcome.get('pnl', 0.0),
            'duration_minutes': outcome.get('duration_minutes', 0),
            'max_drawdown': outcome.get('max_drawdown', 0.0),
            'regime': decision.regime.value,
            'strategy': decision.strategy.value,
            'timestamp': datetime.now()
        }
        
        self.trade_history.append(trade_record)
        
        # Update all learning systems
        self.self_improvement.learn_from_trade(trade_record)
        self.feedback_system.process_trade_feedback(trade_record)
        self.strategy_selector.update_strategy_performance(decision.strategy, trade_record)
        self.parameter_optimizer.update_performance(trade_record)
        self.risk_manager.update_performance(trade_record)
        
        # Update ensemble system with actual outcome
        if hasattr(self, 'ensemble_system'):
            await self.ensemble_system.record_actual_outcome_async(
                trade_record['decision'], outcome.get('pnl', 0.0)
            )
    
    async def _log_decision(self, decision: TradingDecision):
        """Log trading decision for analysis and learning."""
        log_entry = {
            'timestamp': decision.timestamp,
            'symbol': decision.symbol,
            'action': decision.action,
            'confidence': decision.confidence,
            'position_size': decision.position_size,
            'regime': decision.regime.value,
            'strategy': decision.strategy.value,
            'sentiment_score': decision.sentiment_score,
            'microstructure_score': decision.microstructure_score
        }
        
        logger.info(f"Trading Decision: {log_entry}")
        
    def _calculate_combined_confidence(self, confidences: List[float]) -> float:
        """Calculate combined confidence from multiple sources."""
        if not confidences:
            return 0.0
        
        # Use weighted average with higher weight for more reliable sources
        weights = [0.25, 0.20, 0.20, 0.15, 0.15, 0.05]  # Adjust based on source reliability
        weights = weights[:len(confidences)]
        
        if len(weights) != len(confidences):
            # Normalize weights if different number of sources
            weights = [1.0 / len(confidences)] * len(confidences)
        
        combined = sum(c * w for c, w in zip(confidences, weights))
        return max(0.0, min(1.0, combined))  # Clamp to [0, 1]
    
    def _should_schedule_improvements(self) -> bool:
        """Determine if it's time to schedule improvements."""
        # Check if we have enough trading history
        if len(self.trade_history) < 20:
            return False
            
        # Check if performance is below threshold
        recent_trades = self.trade_history[-20:]
        win_rate = sum(1 for t in recent_trades if t.get('pnl', 0) > 0) / len(recent_trades)
        
        
        # Schedule improvements if win rate is below threshold or randomly for exploration
        import random
        return win_rate < 0.5 or random.random() < 0.1  # 10% chance for random improvement
    
    async def _schedule_improvement_tasks(self):
        """Schedule improvement tasks based on system performance."""
        if not self.self_improvement_engine:
            return
        try:
            
            # Identify components that need improvement
            components_to_improve = self._identify_components_for_improvement()
            
            for component in components_to_improve:
                # Create improvement task
                task_id = self.self_improvement_engine.create_task(
                    target_file=component['file_path'],
                    purpose=component['improvement_purpose'],
                    knowledge_query=component['knowledge_query'],
                    knowledge_tags=component['knowledge_tags'],
                    priority=component['priority'],
                    metadata={
                        "modification_type": "update",
                        "component": component['name'],
                        "performance_metrics": component['metrics']
                    }
                )
                
                logger.info(f"Scheduled improvement task {task_id} for {component['name']}")
                
        except Exception as e:
            logger.error(f"Error scheduling improvement tasks: {e}")
    
    def _identify_components_for_improvement(self) -> List[Dict[str, Any]]:
        """Identify components that need improvement based on performance."""
        components = []
        
        # Check strategy performance
        strategy_summary = self.strategy_selector.get_strategy_summary()
        if strategy_summary.get('average_performance', 0.5) < 0.6:
            components.append({
                'name': 'strategy_selector',
                'file_path': 'trading_bot/adaptive_systems/strategy_selector.py',
                'improvement_purpose': 'Improve strategy selection logic for better performance',
                'knowledge_query': 'trading strategy selection optimization',
                'knowledge_tags': ['strategy', 'selection', 'optimization'],
                'priority': 1,
                'metrics': strategy_summary
            })
        
        # Check risk management
        risk_summary = self.risk_manager.get_risk_summary()
        if risk_summary.get('current_drawdown', 0) > 0.1:  # 10% drawdown
            components.append({
                'name': 'risk_manager',
                'file_path': 'trading_bot/adaptive_systems/adaptive_risk.py',
                'improvement_purpose': 'Enhance risk management to reduce drawdowns',
                'knowledge_query': 'trading risk management drawdown reduction',
                'knowledge_tags': ['risk', 'drawdown', 'position sizing'],
                'priority': 1,
                'metrics': risk_summary
            })
        
        # Add more components as needed
        
        return components
    
    async def _process_pending_approvals(self):
        """Process pending approval tasks."""
        if not self.self_improvement_engine:
            return
            
        # Get tasks pending approval
        pending_tasks = self.self_improvement_engine.get_tasks(ModificationStatus.APPROVAL_PENDING)
        
        for task in pending_tasks:
            # Auto-approve tasks if configured
            if self.self_improvement_config.get('auto_approve', False):
                self.self_improvement_engine.approve_task(task.task_id)
                logger.info(f"Auto-approved task {task.task_id}: {task.purpose}")
            else:
                # Log that manual approval is needed
                logger.info(f"Task {task.task_id} requires manual approval: {task.purpose}")
    
    def get_system_status(self) -> Dict[str, Any]:
        """Get comprehensive system status."""
        status = {
            "system_active": self.system_active,
            "learning_active": self.learning_active,
            "current_regime": self.current_regime.value if self.current_regime else None,
            "current_strategy": self.current_strategy.value if self.current_strategy else None,
            "system_metrics": self.system_metrics,
            "trade_count": len(self.trade_history),
            "learning_insights": len(self.self_improvement.insights),
            "discovered_strategies": len(self.meta_learning.discovered_strategies),
            "health_status": self.health_monitor.get_health_summary(),
            "adaptation_summary": {
                "regime_detection": self.regime_detector.get_regime_statistics(),
                "strategy_performance": self.strategy_selector.get_strategy_summary(),
                "risk_management": self.risk_manager.get_risk_summary(),
                "parameter_optimization": self.parameter_optimizer.get_optimization_summary(),
                "learning_progress": self.self_improvement.get_learning_summary(),
                "feedback_system": self.feedback_system.get_feedback_summary(),
                "meta_learning": self.meta_learning.get_meta_learning_insights()
            }
        }
        
        # Add self-improvement status if enabled
        if self.enable_self_improvement and self.self_improvement_engine:
            status["self_improvement"] = {
                "active": self.enable_self_improvement,
                "engine_status": self.self_improvement_engine.get_stats(),
                "knowledge_base": self.knowledge_base.get_stats() if hasattr(self, 'knowledge_base') else {}
            }
        
        return status
