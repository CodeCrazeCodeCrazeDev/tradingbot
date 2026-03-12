"""
Self Learner - Continuous Learning and Improvement System
=========================================================

This module implements a self-learning system that continuously
improves the trading system based on:

1. Trade outcome analysis
2. Strategy performance tracking
3. Market regime adaptation
4. Parameter optimization
5. Pattern discovery
6. Mistake analysis

Goal: Learn from every trade and continuously improve performance.
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from collections import deque, defaultdict
import logging
import json
from pathlib import Path
import hashlib

logger = logging.getLogger(__name__)


class LearningType(Enum):
    """Types of learning"""
    TRADE_OUTCOME = "trade_outcome"
    STRATEGY_PERFORMANCE = "strategy_performance"
    MARKET_REGIME = "market_regime"
    PARAMETER_OPTIMIZATION = "parameter_optimization"
    PATTERN_DISCOVERY = "pattern_discovery"
    MISTAKE_ANALYSIS = "mistake_analysis"


@dataclass
class TradeLesson:
    """Lesson learned from a trade"""
    lesson_id: str
    timestamp: datetime
    trade_id: str
    symbol: str
    direction: str
    outcome: str  # win, loss, breakeven
    pnl: float
    pnl_percent: float
    entry_reason: str
    exit_reason: str
    market_regime: str
    lessons: List[str]
    improvements: List[str]
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class StrategyInsight:
    """Insight about strategy performance"""
    strategy_name: str
    total_trades: int
    win_rate: float
    avg_win: float
    avg_loss: float
    profit_factor: float
    best_regime: str
    worst_regime: str
    optimal_conditions: Dict[str, Any]
    avoid_conditions: Dict[str, Any]


@dataclass
class MarketPattern:
    """Discovered market pattern"""
    pattern_id: str
    pattern_type: str
    description: str
    conditions: Dict[str, Any]
    expected_outcome: str
    confidence: float
    occurrences: int
    success_rate: float


class TradeAnalyzer:
    """
    Analyze individual trades to extract lessons
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        
        # Trade history for analysis
        self.trades: List[Dict[str, Any]] = []
        self.lessons: List[TradeLesson] = []
    
    def analyze_trade(self, trade: Any) -> TradeLesson:
        """Analyze a completed trade and extract lessons"""
        # Determine outcome
        if trade.pnl > 0:
            outcome = "win"
        elif trade.pnl < 0:
            outcome = "loss"
        else:
            outcome = "breakeven"
        
        lessons = []
        improvements = []
        
        # Analyze based on outcome
        if outcome == "win":
            lessons.extend(self._analyze_winning_trade(trade))
        elif outcome == "loss":
            lessons.extend(self._analyze_losing_trade(trade))
            improvements.extend(self._suggest_improvements(trade))
        
        # Create lesson record
        lesson = TradeLesson(
            lesson_id=hashlib.md5(f"{trade.execution_id}_{datetime.now()}".encode()).hexdigest()[:8],
            timestamp=datetime.now(),
            trade_id=trade.execution_id,
            symbol=trade.symbol,
            direction=trade.direction,
            outcome=outcome,
            pnl=trade.pnl,
            pnl_percent=trade.pnl_percent if hasattr(trade, 'pnl_percent') else 0,
            entry_reason=trade.metadata.get('entry_reason', 'unknown'),
            exit_reason=trade.exit_reason,
            market_regime=trade.metadata.get('market_regime', 'unknown'),
            lessons=lessons,
            improvements=improvements,
            metadata=trade.metadata,
        )
        
        self.lessons.append(lesson)
        return lesson
    
    def _analyze_winning_trade(self, trade: Any) -> List[str]:
        """Extract lessons from winning trade"""
        lessons = []
        
        # Check if hit take profit
        if trade.exit_reason == "take_profit":
            lessons.append("Take profit target was appropriate")
        
        # Check holding time
        if hasattr(trade, 'holding_time') and trade.holding_time:
            if trade.holding_time < timedelta(hours=1):
                lessons.append("Quick win - market moved in our favor rapidly")
            elif trade.holding_time > timedelta(days=1):
                lessons.append("Patient holding paid off")
        
        # Check if exceeded expectations
        if hasattr(trade, 'pnl_percent') and trade.pnl_percent > 0.02:
            lessons.append("Trade exceeded 2% target - consider trailing stops")
        
        return lessons
    
    def _analyze_losing_trade(self, trade: Any) -> List[str]:
        """Extract lessons from losing trade"""
        lessons = []
        
        # Check if hit stop loss
        if trade.exit_reason == "stop_loss" or trade.exit_reason == "stopped_out":
            lessons.append("Stop loss was hit - position sizing was appropriate")
        
        # Check if loss exceeded stop
        if hasattr(trade, 'pnl_percent') and trade.pnl_percent < -0.03:
            lessons.append("Loss exceeded 3% - review stop loss placement")
        
        # Check holding time
        if hasattr(trade, 'holding_time') and trade.holding_time:
            if trade.holding_time < timedelta(minutes=30):
                lessons.append("Quick loss - entry timing may need improvement")
        
        return lessons
    
    def _suggest_improvements(self, trade: Any) -> List[str]:
        """Suggest improvements based on losing trade"""
        improvements = []
        
        # Entry improvements
        if trade.metadata.get('confidence', 1) < 0.7:
            improvements.append("Consider waiting for higher confidence signals")
        
        # Exit improvements
        if trade.exit_reason == "stopped_out":
            improvements.append("Review stop loss placement relative to ATR")
        
        # Timing improvements
        if hasattr(trade, 'holding_time') and trade.holding_time:
            if trade.holding_time < timedelta(minutes=15):
                improvements.append("Consider wider stops or better entry timing")
        
        return improvements
    
    def get_recent_lessons(self, n: int = 10) -> List[TradeLesson]:
        """Get most recent lessons"""
        return self.lessons[-n:]
    
    def get_lessons_by_outcome(self, outcome: str) -> List[TradeLesson]:
        """Get lessons filtered by outcome"""
        return [l for l in self.lessons if l.outcome == outcome]


class StrategyTracker:
    """
    Track and analyze strategy performance
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        
        # Strategy performance data
        self.strategy_trades: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
        self.strategy_insights: Dict[str, StrategyInsight] = {}
    
    def record_trade(self, strategy_name: str, trade: Dict[str, Any]):
        """Record a trade for a strategy"""
        self.strategy_trades[strategy_name].append(trade)
        
        # Update insights
        self._update_insight(strategy_name)
    
    def _update_insight(self, strategy_name: str):
        """Update insight for a strategy"""
        trades = self.strategy_trades[strategy_name]
        
        if len(trades) < 5:
            return
        
        # Calculate metrics
        wins = [t for t in trades if t.get('pnl', 0) > 0]
        losses = [t for t in trades if t.get('pnl', 0) < 0]
        
        win_rate = len(wins) / len(trades) if trades else 0
        avg_win = np.mean([t['pnl'] for t in wins]) if wins else 0
        avg_loss = abs(np.mean([t['pnl'] for t in losses])) if losses else 0
        profit_factor = (sum(t['pnl'] for t in wins) / abs(sum(t['pnl'] for t in losses))) if losses else float('inf')
        
        # Analyze by regime
        regime_performance = defaultdict(list)
        for trade in trades:
            regime = trade.get('market_regime', 'unknown')
            regime_performance[regime].append(trade.get('pnl', 0))
        
        regime_win_rates = {
            regime: len([p for p in pnls if p > 0]) / len(pnls) if pnls else 0
            for regime, pnls in regime_performance.items()
        }
        
        best_regime = max(regime_win_rates, key=regime_win_rates.get) if regime_win_rates else "unknown"
        worst_regime = min(regime_win_rates, key=regime_win_rates.get) if regime_win_rates else "unknown"
        
        # Create insight
        self.strategy_insights[strategy_name] = StrategyInsight(
            strategy_name=strategy_name,
            total_trades=len(trades),
            win_rate=win_rate,
            avg_win=avg_win,
            avg_loss=avg_loss,
            profit_factor=profit_factor,
            best_regime=best_regime,
            worst_regime=worst_regime,
            optimal_conditions={'regime': best_regime},
            avoid_conditions={'regime': worst_regime} if regime_win_rates.get(worst_regime, 0) < 0.4 else {},
        )
    
    def get_insight(self, strategy_name: str) -> Optional[StrategyInsight]:
        """Get insight for a strategy"""
        return self.strategy_insights.get(strategy_name)
    
    def get_all_insights(self) -> Dict[str, StrategyInsight]:
        """Get all strategy insights"""
        return self.strategy_insights
    
    def get_best_strategies(self, n: int = 3) -> List[str]:
        """Get top performing strategies"""
        sorted_strategies = sorted(
            self.strategy_insights.items(),
            key=lambda x: x[1].profit_factor if x[1].profit_factor != float('inf') else 100,
            reverse=True
        )
        return [s[0] for s in sorted_strategies[:n]]
    
    def get_strategy_recommendations(self, market_regime: str) -> List[str]:
        """Get strategy recommendations for current market regime"""
        recommendations = []
        
        for name, insight in self.strategy_insights.items():
            if insight.best_regime == market_regime and insight.win_rate > 0.5:
                recommendations.append(name)
        
        return recommendations


class PatternDiscovery:
    """
    Discover patterns in market data and trading outcomes
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        
        # Discovered patterns
        self.patterns: Dict[str, MarketPattern] = {}
        
        # Pattern templates
        self.pattern_templates = [
            'trend_continuation',
            'trend_reversal',
            'breakout',
            'mean_reversion',
            'momentum_exhaustion',
        ]
    
    def analyze_conditions(self, trade: Any, market_data: pd.DataFrame) -> List[str]:
        """Analyze market conditions at trade entry"""
        conditions = []
        
        if market_data is None or market_data.empty:
            return conditions
        
        # Get indicators at entry
        current = market_data.iloc[-1] if len(market_data) > 0 else None
        
        if current is None:
            return conditions
        
        # Trend conditions
        if 'sma_20' in market_data.columns and 'sma_50' in market_data.columns:
            if current.get('close', 0) > current.get('sma_20', 0) > current.get('sma_50', 0):
                conditions.append('uptrend')
            elif current.get('close', 0) < current.get('sma_20', 0) < current.get('sma_50', 0):
                conditions.append('downtrend')
            else:
                conditions.append('ranging')
        
        # Volatility conditions
        if 'atr' in market_data.columns:
            atr_pct = current.get('atr', 0) / current.get('close', 1)
            if atr_pct > 0.02:
                conditions.append('high_volatility')
            elif atr_pct < 0.005:
                conditions.append('low_volatility')
            else:
                conditions.append('normal_volatility')
        
        # RSI conditions
        if 'rsi' in market_data.columns:
            rsi = current.get('rsi', 50)
            if rsi > 70:
                conditions.append('overbought')
            elif rsi < 30:
                conditions.append('oversold')
            else:
                conditions.append('neutral_rsi')
        
        return conditions
    
    def record_pattern(self, conditions: List[str], outcome: str, pnl: float):
        """Record a pattern occurrence"""
        pattern_key = '_'.join(sorted(conditions))
        
        if pattern_key not in self.patterns:
            self.patterns[pattern_key] = MarketPattern(
                pattern_id=hashlib.md5(pattern_key.encode()).hexdigest()[:8],
                pattern_type='discovered',
                description=f"Pattern with conditions: {', '.join(conditions)}",
                conditions={'features': conditions},
                expected_outcome='unknown',
                confidence=0.5,
                occurrences=0,
                success_rate=0.5,
            )
        
        pattern = self.patterns[pattern_key]
        pattern.occurrences += 1
        
        # Update success rate
        is_success = pnl > 0
        alpha = 1 / pattern.occurrences
        pattern.success_rate = alpha * (1 if is_success else 0) + (1 - alpha) * pattern.success_rate
        
        # Update confidence based on occurrences
        pattern.confidence = min(0.9, 0.5 + pattern.occurrences * 0.01)
        
        # Update expected outcome
        if pattern.success_rate > 0.6:
            pattern.expected_outcome = 'bullish' if outcome == 'win' else 'bearish'
        elif pattern.success_rate < 0.4:
            pattern.expected_outcome = 'bearish' if outcome == 'win' else 'bullish'
        else:
            pattern.expected_outcome = 'neutral'
    
    def get_pattern_prediction(self, conditions: List[str]) -> Optional[Tuple[str, float]]:
        """Get prediction based on current conditions"""
        pattern_key = '_'.join(sorted(conditions))
        
        if pattern_key in self.patterns:
            pattern = self.patterns[pattern_key]
            if pattern.occurrences >= 10 and pattern.confidence > 0.6:
                return pattern.expected_outcome, pattern.confidence
        
        return None
    
    def get_high_confidence_patterns(self, min_confidence: float = 0.7) -> List[MarketPattern]:
        """Get patterns with high confidence"""
        return [p for p in self.patterns.values() 
                if p.confidence >= min_confidence and p.occurrences >= 10]


class ParameterOptimizer:
    """
    Optimize trading parameters based on performance
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        
        # Parameter history
        self.parameter_history: Dict[str, List[Tuple[Any, float]]] = defaultdict(list)
        
        # Current optimal parameters
        self.optimal_parameters: Dict[str, Any] = {}
    
    def record_performance(self, parameter_name: str, value: Any, performance: float):
        """Record parameter performance"""
        self.parameter_history[parameter_name].append((value, performance))
        
        # Update optimal if better
        if parameter_name not in self.optimal_parameters:
            self.optimal_parameters[parameter_name] = value
        else:
            # Check if this value performs better
            history = self.parameter_history[parameter_name]
            value_performances = [p for v, p in history if v == value]
            optimal_performances = [p for v, p in history if v == self.optimal_parameters[parameter_name]]
            
            if value_performances and optimal_performances:
                if np.mean(value_performances) > np.mean(optimal_performances):
                    self.optimal_parameters[parameter_name] = value
    
    def get_optimal(self, parameter_name: str) -> Optional[Any]:
        """Get optimal value for a parameter"""
        return self.optimal_parameters.get(parameter_name)
    
    def suggest_adjustment(self, parameter_name: str, current_value: Any) -> Optional[Any]:
        """Suggest parameter adjustment"""
        if parameter_name not in self.parameter_history:
            return None
        
        history = self.parameter_history[parameter_name]
        
        if len(history) < 10:
            return None
        
        # Find best performing value
        value_performances = defaultdict(list)
        for value, performance in history:
            value_performances[value].append(performance)
        
        avg_performances = {v: np.mean(p) for v, p in value_performances.items()}
        best_value = max(avg_performances, key=avg_performances.get)
        
        if best_value != current_value:
            return best_value
        
        return None


class SelfLearner:
    """
    Main Self-Learning System
    
    Coordinates all learning components for continuous improvement
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        
        # Initialize components
        self.trade_analyzer = TradeAnalyzer(config)
        self.strategy_tracker = StrategyTracker(config)
        self.pattern_discovery = PatternDiscovery(config)
        self.parameter_optimizer = ParameterOptimizer(config)
        
        # Learning state
        self.total_lessons = 0
        self.last_update = datetime.now()
        
        # Data storage
        self.data_dir = Path(self.config.get('data_dir', 'learning_data'))
        self.data_dir.mkdir(parents=True, exist_ok=True)
        
        # Load previous learning
        self._load_state()
        
        logger.info("Self Learner initialized")
    
    async def learn_from_trade(self, trade: Any):
        """Learn from a completed trade"""
        # Analyze trade
        lesson = self.trade_analyzer.analyze_trade(trade)
        self.total_lessons += 1
        
        # Track strategy performance
        strategy_name = trade.metadata.get('strategy', 'unknown')
        self.strategy_tracker.record_trade(strategy_name, {
            'pnl': trade.pnl,
            'pnl_percent': trade.pnl_percent if hasattr(trade, 'pnl_percent') else 0,
            'market_regime': trade.metadata.get('market_regime', 'unknown'),
            'timestamp': datetime.now(),
        })
        
        # Discover patterns
        conditions = trade.metadata.get('conditions', [])
        if conditions:
            self.pattern_discovery.record_pattern(
                conditions,
                lesson.outcome,
                trade.pnl
            )
        
        # Optimize parameters
        for param_name, param_value in trade.metadata.items():
            if param_name.startswith('param_'):
                self.parameter_optimizer.record_performance(
                    param_name,
                    param_value,
                    trade.pnl
                )
        
        logger.info(f"Learned from trade {trade.execution_id}: {lesson.outcome}")
    
    async def update(self):
        """Periodic learning update"""
        self.last_update = datetime.now()
        
        # Save state periodically
        self._save_state()
    
    def get_recommendations(self, market_regime: str) -> Dict[str, Any]:
        """Get trading recommendations based on learning"""
        recommendations = {
            'strategies': self.strategy_tracker.get_strategy_recommendations(market_regime),
            'best_strategies': self.strategy_tracker.get_best_strategies(),
            'patterns': [p.description for p in self.pattern_discovery.get_high_confidence_patterns()],
            'parameter_suggestions': {},
        }
        
        # Add parameter suggestions
        for param_name in self.parameter_optimizer.optimal_parameters:
            optimal = self.parameter_optimizer.get_optimal(param_name)
            if optimal is not None:
                recommendations['parameter_suggestions'][param_name] = optimal
        
        return recommendations
    
    def get_strategy_insight(self, strategy_name: str) -> Optional[StrategyInsight]:
        """Get insight for a specific strategy"""
        return self.strategy_tracker.get_insight(strategy_name)
    
    def get_recent_lessons(self, n: int = 10) -> List[TradeLesson]:
        """Get recent lessons"""
        return self.trade_analyzer.get_recent_lessons(n)
    
    def get_learning_stats(self) -> Dict[str, Any]:
        """Get learning statistics"""
        return {
            'total_lessons': self.total_lessons,
            'strategies_tracked': len(self.strategy_tracker.strategy_insights),
            'patterns_discovered': len(self.pattern_discovery.patterns),
            'parameters_optimized': len(self.parameter_optimizer.optimal_parameters),
            'last_update': self.last_update.isoformat(),
        }
    
    def _save_state(self):
        """Save learning state to disk"""
        state = {
            'total_lessons': self.total_lessons,
            'last_update': self.last_update.isoformat(),
            'strategy_insights': {
                name: {
                    'strategy_name': insight.strategy_name,
                    'total_trades': insight.total_trades,
                    'win_rate': insight.win_rate,
                    'profit_factor': insight.profit_factor,
                    'best_regime': insight.best_regime,
                }
                for name, insight in self.strategy_tracker.strategy_insights.items()
            },
            'optimal_parameters': self.parameter_optimizer.optimal_parameters,
        }
        
        state_file = self.data_dir / 'learning_state.json'
        with open(state_file, 'w') as f:
            json.dump(state, f, indent=2, default=str)
    
    def _load_state(self):
        """Load learning state from disk"""
        state_file = self.data_dir / 'learning_state.json'
        
        if state_file.exists():
            try:
                with open(state_file, 'r') as f:
                    state = json.load(f)
                    self.total_lessons = state.get('total_lessons', 0)
                    self.parameter_optimizer.optimal_parameters = state.get('optimal_parameters', {})
                    logger.info(f"Loaded learning state: {self.total_lessons} lessons")
            except Exception as e:
                logger.warning(f"Could not load learning state: {e}")
