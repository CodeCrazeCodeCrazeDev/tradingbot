"""
Master Self-Learning Orchestrator

This module integrates all self-learning, self-evolving, and self-optimizing
capabilities into a unified system for maximum market analysis and profit generation.
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import asyncio
from collections import deque
import logging
import json

from .core_learning_engine import CoreLearningEngine, ModelType, LearningMode
from .strategy_evolution import StrategyEvolutionEngine, StrategyDNA
from .execution_optimizer import ExecutionOptimizer, ExecutionAction
from .self_healing_system import SelfHealingSystem, HealthStatus
from .distributed_learning import DistributedLearningSystem, LearningComponent, ComponentRole, KnowledgeType

logger = logging.getLogger(__name__)


class SystemMode(Enum):
    """Overall system operating modes"""
    LEARNING = "learning"           # Focus on learning, conservative trading
    OPTIMIZING = "optimizing"       # Actively optimizing strategies
    EXPLOITING = "exploiting"       # Using best strategies aggressively
    EXPLORING = "exploring"         # Discovering new opportunities
    DEFENSIVE = "defensive"         # Risk mitigation mode
    AUTONOMOUS = "autonomous"       # Fully autonomous operation


@dataclass
class TradingDecision:
    """Comprehensive trading decision with all learning insights"""
    decision_id: str
    symbol: str
    action: str  # 'buy', 'sell', 'hold'
    confidence: float
    position_size: float
    entry_price: float
    stop_loss: float
    take_profit: float
    
    # Learning insights
    strategy_id: str
    strategy_fitness: float
    predicted_profit: float
    predicted_probability: float
    execution_plan: Dict[str, Any]
    risk_score: float
    
    # Pattern insights
    matching_patterns: List[Dict[str, Any]]
    market_regime: str
    
    # Meta information
    learning_mode: str
    system_mode: str
    collective_confidence: float
    timestamp: datetime = field(default_factory=datetime.utcnow)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            'decision_id': self.decision_id,
            'symbol': self.symbol,
            'action': self.action,
            'confidence': self.confidence,
            'position_size': self.position_size,
            'entry_price': self.entry_price,
            'stop_loss': self.stop_loss,
            'take_profit': self.take_profit,
            'strategy_id': self.strategy_id,
            'strategy_fitness': self.strategy_fitness,
            'predicted_profit': self.predicted_profit,
            'predicted_probability': self.predicted_probability,
            'execution_plan': self.execution_plan,
            'risk_score': self.risk_score,
            'matching_patterns': self.matching_patterns,
            'market_regime': self.market_regime,
            'learning_mode': self.learning_mode,
            'system_mode': self.system_mode,
            'collective_confidence': self.collective_confidence,
            'timestamp': self.timestamp.isoformat()
        }


@dataclass
class PerformanceSnapshot:
    """System performance snapshot"""
    timestamp: datetime
    total_trades: int
    winning_trades: int
    total_profit: float
    sharpe_ratio: float
    max_drawdown: float
    learning_progress: float
    strategy_evolution_generation: int
    system_health_score: float
    active_strategies: int


class MasterSelfLearningOrchestrator:
    """
    Master orchestrator integrating all self-learning capabilities
    for optimal market analysis, prediction, and profit generation.
    """
    
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        
        # Initialize all subsystems
        self.learning_engine = CoreLearningEngine(config.get('learning', {}))
        self.strategy_evolution = StrategyEvolutionEngine(config.get('evolution', {}))
        self.execution_optimizer = ExecutionOptimizer(config.get('execution', {}))
        self.self_healing = SelfHealingSystem(config.get('healing', {}))
        self.distributed_learning = DistributedLearningSystem(config.get('distributed', {}))
        
        # System state
        self.system_mode = SystemMode.LEARNING
        self.is_initialized = False
        self.is_running = False
        self.start_time: Optional[datetime] = None
        
        # Performance tracking
        self.performance_history: deque = deque(maxlen=1000)
        self.decision_history: deque = deque(maxlen=1000)
        self.trade_results: deque = deque(maxlen=1000)
        
        # Statistics
        self.total_trades = 0
        self.winning_trades = 0
        self.total_profit = 0.0
        self.total_loss = 0.0
        
    async def initialize(self):
        """Initialize all subsystems"""
        logger.info("Initializing Master Self-Learning Orchestrator...")
        
        # Initialize strategy evolution
        await self.strategy_evolution.initialize()
        
        # Register components with distributed learning
        self._register_distributed_components()
        
        # Start self-healing monitoring
        asyncio.create_task(self.self_healing.start_monitoring(interval=60.0))
        
        # Start distributed learning
        await self.distributed_learning.start()
        
        self.is_initialized = True
        self.start_time = datetime.utcnow()
        
        logger.info("Master Self-Learning Orchestrator initialized successfully")
    
    def _register_distributed_components(self):
        """Register all components for distributed learning"""
        # Create learning components for each subsystem
        components = [
            ('learning_engine', ComponentRole.MARKET_ANALYZER),
            ('strategy_evolution', ComponentRole.STRATEGY_OPTIMIZER),
            ('execution_optimizer', ComponentRole.EXECUTION_ENGINE),
            ('risk_manager', ComponentRole.RISK_MANAGER),
            ('performance_tracker', ComponentRole.PERFORMANCE_TRACKER)
        ]
        
        for name, role in components:
            component = LearningComponent(
                component_name=name,
                role=role,
                knowledge_base=self.distributed_learning.knowledge_base,
                message_bus=self.distributed_learning.message_bus
            )
            self.distributed_learning.register_component(component)
    
    async def analyze_market(self, symbol: str, market_data: pd.DataFrame) -> TradingDecision:
        """
        Comprehensive market analysis using all learning systems
        to generate optimal trading decision.
        """
        if not self.is_initialized:
            await self.initialize()
        
        decision_id = f"decision_{symbol}_{datetime.utcnow().timestamp()}"
        
        try:
            # 1. Core Learning Engine - Predict market direction and profit
            price_direction, direction_conf = await self.learning_engine.predict(
                market_data, ModelType.PRICE_DIRECTION
            )
            profit_prob, profit_conf = await self.learning_engine.predict(
                market_data, ModelType.PROFIT_PROBABILITY
            )
            optimal_position, position_conf = await self.learning_engine.predict(
                market_data, ModelType.OPTIMAL_POSITION
            )
            
            # 2. Pattern Discovery - Find matching profitable patterns
            matching_patterns = await self.learning_engine.get_pattern_insights(market_data)
            
            # 3. Strategy Evolution - Get best active strategies
            active_strategies = self.strategy_evolution.get_active_strategies()
            best_strategy = active_strategies[0] if active_strategies else None
            
            # 4. Distributed Learning - Get collective prediction
            context = {
                'symbol': symbol,
                'price': market_data['close'].iloc[-1] if len(market_data) > 0 else 0,
                'volume': market_data['volume'].iloc[-1] if 'volume' in market_data.columns and len(market_data) > 0 else 0
            }
            collective_pred, collective_conf = await self.distributed_learning.get_collective_prediction(context)
            
            # 5. Determine action based on predictions
            action = 'hold'
            if price_direction > 0.6 and profit_prob > 0.6:
                action = 'buy'
            elif price_direction < 0.4 and profit_prob > 0.6:
                action = 'sell'
            
            # 6. Calculate position size
            base_position = abs(optimal_position) if optimal_position != 0 else 0.02
            confidence_multiplier = (direction_conf + profit_conf + collective_conf) / 3.0
            position_size = base_position * confidence_multiplier
            
            # Adjust based on system mode
            if self.system_mode == SystemMode.DEFENSIVE:
                position_size *= 0.5
            elif self.system_mode == SystemMode.EXPLOITING:
                position_size *= 1.5
            
            # 7. Calculate entry, stop loss, and take profit
            current_price = market_data['close'].iloc[-1] if len(market_data) > 0 else 0
            volatility = market_data['close'].std() if len(market_data) > 1 else current_price * 0.02
            
            entry_price = current_price
            if action == 'buy':
                stop_loss = current_price - (2 * volatility)
                take_profit = current_price + (3 * volatility)
            elif action == 'sell':
                stop_loss = current_price + (2 * volatility)
                take_profit = current_price - (3 * volatility)
            else:
                stop_loss = current_price
                take_profit = current_price
            
            # 8. Optimize execution
            order = {
                'symbol': symbol,
                'quantity': position_size,
                'urgency': 0.7 if self.system_mode == SystemMode.EXPLOITING else 0.5,
                'venues': ['default']
            }
            execution_plan = await self.execution_optimizer.optimize_execution(order, market_data)
            
            # 9. Calculate risk score
            risk_score = self._calculate_risk_score(
                position_size, volatility, direction_conf, profit_conf
            )
            
            # 10. Determine market regime
            market_regime = self._detect_market_regime(market_data)
            
            # 11. Create comprehensive decision
            decision = TradingDecision(
                decision_id=decision_id,
                symbol=symbol,
                action=action,
                confidence=(direction_conf + profit_conf + collective_conf) / 3.0,
                position_size=position_size,
                entry_price=entry_price,
                stop_loss=stop_loss,
                take_profit=take_profit,
                strategy_id=best_strategy.strategy_id if best_strategy else 'default',
                strategy_fitness=best_strategy.fitness if best_strategy else 0.0,
                predicted_profit=profit_prob,
                predicted_probability=profit_prob,
                execution_plan=execution_plan,
                risk_score=risk_score,
                matching_patterns=[p.__dict__ for p in matching_patterns[:3]],
                market_regime=market_regime,
                learning_mode=self.learning_engine.learning_mode.value,
                system_mode=self.system_mode.value,
                collective_confidence=collective_conf
            )
            
            # Store decision
            self.decision_history.append(decision)
            
            # Share knowledge with distributed system
            await self._share_decision_knowledge(decision, market_data)
            
            logger.info(f"Generated decision for {symbol}: {action} with {decision.confidence:.2%} confidence")
            
            return decision
        
        except Exception as e:
            logger.error(f"Error in analyze_market: {e}")
            self.self_healing.record_component_error('master_orchestrator', e, {'symbol': symbol})
            
            # Return safe default decision
            return self._create_safe_decision(symbol, market_data)
    
    async def learn_from_trade(self, decision: TradingDecision, trade_result: Dict[str, Any]):
        """Learn from trade execution and outcome"""
        try:
            # Extract outcomes
            profit = trade_result.get('profit', 0)
            success = profit > 0
            
            # 1. Update core learning engine
            outcomes = {
                'profit': profit,
                'success': 1.0 if success else 0.0,
                ModelType.PRICE_DIRECTION.value: 1.0 if success else 0.0,
                ModelType.PROFIT_PROBABILITY.value: profit,
                ModelType.OPTIMAL_POSITION.value: decision.position_size
            }
            
            market_data = trade_result.get('market_data')
            if market_data is not None:
                await self.learning_engine.learn_from_market(market_data, outcomes)
            
            # 2. Update strategy evolution
            await self.strategy_evolution.record_strategy_performance(
                decision.strategy_id,
                {
                    'profit': profit,
                    'market_condition': decision.market_regime
                }
            )
            
            # 3. Update execution optimizer
            execution_result = {
                'slippage': trade_result.get('slippage', 0),
                'fill_rate': trade_result.get('fill_rate', 1.0),
                'execution_time': trade_result.get('execution_time', 0),
                'market_impact': trade_result.get('market_impact', 0),
                'profit_improvement': profit,
                'done': True
            }
            await self.execution_optimizer.learn_from_execution(
                decision.execution_plan, execution_result
            )
            
            # 4. Update statistics
            self.total_trades += 1
            if success:
                self.winning_trades += 1
                self.total_profit += profit
            else:
                self.total_loss += abs(profit)
            
            # 5. Store trade result
            self.trade_results.append({
                'decision': decision.to_dict(),
                'result': trade_result,
                'timestamp': datetime.utcnow()
            })
            
            # 6. Share learning with distributed system
            await self._share_trade_learning(decision, trade_result)
            
            # 7. Adapt system mode based on performance
            await self._adapt_system_mode()
            
            # 8. Record metrics for self-healing
            self.self_healing.record_component_metrics('master_orchestrator', {
                'profit': profit,
                'confidence': decision.confidence,
                'success': 1.0 if success else 0.0
            })
            
            logger.info(f"Learned from trade: {decision.decision_id}, Profit: {profit:.4f}")
        
        except Exception as e:
            logger.error(f"Error in learn_from_trade: {e}")
            self.self_healing.record_component_error('master_orchestrator', e, 
                                                    {'decision_id': decision.decision_id})
    
    async def evolve_strategies(self):
        """Trigger strategy evolution"""
        await self.strategy_evolution.evolve()
        logger.info("Strategy evolution completed")
    
    async def synchronize_learning(self):
        """Synchronize learning across all components"""
        await self.distributed_learning.synchronize_learning()
        logger.info("Learning synchronized across all components")
    
    def _calculate_risk_score(self, position_size: float, volatility: float,
                             direction_conf: float, profit_conf: float) -> float:
        """Calculate risk score for decision"""
        # Higher position size = higher risk
        size_risk = position_size * 2.0
        
        # Higher volatility = higher risk
        vol_risk = min(volatility * 10, 1.0)
        
        # Lower confidence = higher risk
        conf_risk = 1.0 - ((direction_conf + profit_conf) / 2.0)
        
        risk_score = (size_risk + vol_risk + conf_risk) / 3.0
        return min(max(risk_score, 0.0), 1.0)
    
    def _detect_market_regime(self, market_data: pd.DataFrame) -> str:
        """Detect current market regime"""
        if len(market_data) < 20:
            return 'unknown'
        
        close = market_data['close'].values
        returns = np.diff(close) / close[:-1]
        
        volatility = np.std(returns)
        trend = np.mean(returns[-20:])
        
        if volatility > 0.03:
            return 'high_volatility'
        elif abs(trend) > 0.01:
            return 'trending_up' if trend > 0 else 'trending_down'
        else:
            return 'ranging'
    
    async def _share_decision_knowledge(self, decision: TradingDecision, market_data: pd.DataFrame):
        """Share decision knowledge with distributed system"""
        # Share pattern insights
        if decision.matching_patterns:
            knowledge_content = {
                'patterns': decision.matching_patterns,
                'market_regime': decision.market_regime,
                'confidence': decision.confidence
            }
            
            # This would be shared through a component, but for now we log it
            logger.debug(f"Sharing decision knowledge: {decision.decision_id}")
    
    async def _share_trade_learning(self, decision: TradingDecision, trade_result: Dict[str, Any]):
        """Share trade learning with distributed system"""
        logger.debug(f"Sharing trade learning: {decision.decision_id}")
    
    async def _adapt_system_mode(self):
        """Adapt system mode based on recent performance"""
        if len(self.trade_results) < 20:
            return
        
        recent_results = list(self.trade_results)[-20:]
        recent_profits = [r['result'].get('profit', 0) for r in recent_results]
        
        win_rate = sum(1 for p in recent_profits if p > 0) / len(recent_profits)
        avg_profit = np.mean(recent_profits)
        
        # Adapt mode
        if win_rate > 0.7 and avg_profit > 0:
            self.system_mode = SystemMode.EXPLOITING
        elif win_rate < 0.4:
            self.system_mode = SystemMode.DEFENSIVE
        elif avg_profit < 0:
            self.system_mode = SystemMode.LEARNING
        else:
            self.system_mode = SystemMode.OPTIMIZING
        
        logger.info(f"System mode adapted to: {self.system_mode.value}")
    
    def _create_safe_decision(self, symbol: str, market_data: pd.DataFrame) -> TradingDecision:
        """Create safe default decision on error"""
        current_price = market_data['close'].iloc[-1] if len(market_data) > 0 else 0
        
        return TradingDecision(
            decision_id=f"safe_{symbol}_{datetime.utcnow().timestamp()}",
            symbol=symbol,
            action='hold',
            confidence=0.0,
            position_size=0.0,
            entry_price=current_price,
            stop_loss=current_price,
            take_profit=current_price,
            strategy_id='safe_default',
            strategy_fitness=0.0,
            predicted_profit=0.0,
            predicted_probability=0.0,
            execution_plan={},
            risk_score=1.0,
            matching_patterns=[],
            market_regime='unknown',
            learning_mode='conservative',
            system_mode=self.system_mode.value,
            collective_confidence=0.0
        )
    
    def get_performance_snapshot(self) -> PerformanceSnapshot:
        """Get current performance snapshot"""
        win_rate = self.winning_trades / max(self.total_trades, 1)
        
        # Calculate Sharpe ratio
        if self.trade_results:
            profits = [r['result'].get('profit', 0) for r in self.trade_results]
            sharpe = np.mean(profits) / (np.std(profits) + 1e-6) if profits else 0
        else:
            sharpe = 0
        
        # Calculate max drawdown
        if self.trade_results:
            cumulative = np.cumsum([r['result'].get('profit', 0) for r in self.trade_results])
            running_max = np.maximum.accumulate(cumulative)
            drawdown = (cumulative - running_max) / (running_max + 1)
            max_drawdown = np.min(drawdown) if len(drawdown) > 0 else 0
        else:
            max_drawdown = 0
        
        # Learning progress
        learning_progress = min(len(self.trade_results) / 1000, 1.0)
        
        # System health
        health = self.self_healing.get_system_health()
        health_score = health.get('health_score', 0.5)
        
        return PerformanceSnapshot(
            timestamp=datetime.utcnow(),
            total_trades=self.total_trades,
            winning_trades=self.winning_trades,
            total_profit=self.total_profit,
            sharpe_ratio=sharpe,
            max_drawdown=max_drawdown,
            learning_progress=learning_progress,
            strategy_evolution_generation=self.strategy_evolution.population.generation,
            system_health_score=health_score,
            active_strategies=len(self.strategy_evolution.active_strategies)
        )
    
    def get_comprehensive_status(self) -> Dict[str, Any]:
        """Get comprehensive system status"""
        snapshot = self.get_performance_snapshot()
        
        return {
            'system_mode': self.system_mode.value,
            'is_initialized': self.is_initialized,
            'uptime': (datetime.utcnow() - self.start_time).total_seconds() if self.start_time else 0,
            'performance': {
                'total_trades': snapshot.total_trades,
                'win_rate': snapshot.winning_trades / max(snapshot.total_trades, 1),
                'total_profit': snapshot.total_profit,
                'sharpe_ratio': snapshot.sharpe_ratio,
                'max_drawdown': snapshot.max_drawdown,
                'learning_progress': snapshot.learning_progress
            },
            'learning_engine': self.learning_engine.get_learning_status(),
            'strategy_evolution': self.strategy_evolution.get_evolution_status(),
            'execution_optimizer': self.execution_optimizer.get_performance_summary(),
            'self_healing': self.self_healing.get_system_health(),
            'distributed_learning': self.distributed_learning.get_system_status()
        }
    
    async def save_state(self, directory: str = 'self_learning_state'):
        """Save complete system state"""
        import os
        os.makedirs(directory, exist_ok=True)
        
        # Save each subsystem
        await self.learning_engine.save_state(f"{directory}/learning_engine.json")
        await self.distributed_learning.save_state(f"{directory}/distributed_learning.json")
        
        # Save master state
        master_state = {
            'timestamp': datetime.utcnow().isoformat(),
            'system_mode': self.system_mode.value,
            'total_trades': self.total_trades,
            'winning_trades': self.winning_trades,
            'total_profit': self.total_profit,
            'performance_snapshot': self.get_performance_snapshot().__dict__
        }
        
        with open(f"{directory}/master_state.json", 'w') as f:
            json.dump(master_state, f, indent=2, default=str)
        
        logger.info(f"Complete system state saved to {directory}")


async def create_master_orchestrator(config: Optional[Dict] = None) -> MasterSelfLearningOrchestrator:
    """Factory function to create master orchestrator"""
    orchestrator = MasterSelfLearningOrchestrator(config)
    await orchestrator.initialize()
    logger.info("Master Self-Learning Orchestrator created and initialized")
    return orchestrator
