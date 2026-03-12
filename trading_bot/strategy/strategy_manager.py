"""
Strategy Manager - Unified interface for strategy management

This module provides a centralized StrategyManager class that coordinates
all trading strategy operations, selection, and execution.

Author: AlphaAlgo Trading System
"""

import logging
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum, auto
from typing import Any, Callable, Dict, List, Optional, Union

import pandas as pd
import numpy as np

logger = logging.getLogger(__name__)


class StrategyStatus(Enum):
    """Strategy execution status"""
    INACTIVE = auto()
    ACTIVE = auto()
    PAUSED = auto()
    DISABLED = auto()


class SignalType(Enum):
    """Trading signal types"""
    BUY = auto()
    SELL = auto()
    HOLD = auto()
    CLOSE_LONG = auto()
    CLOSE_SHORT = auto()


@dataclass
class StrategySignal:
    """Represents a trading signal from a strategy"""
    strategy_name: str
    symbol: str
    signal_type: SignalType
    confidence: float
    price: float
    timestamp: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'strategy_name': self.strategy_name,
            'symbol': self.symbol,
            'signal_type': self.signal_type.name,
            'confidence': self.confidence,
            'price': self.price,
            'timestamp': self.timestamp.isoformat(),
            'metadata': self.metadata
        }


@dataclass
class StrategyPerformance:
    """Performance metrics for a strategy"""
    strategy_name: str
    total_trades: int = 0
    winning_trades: int = 0
    losing_trades: int = 0
    total_pnl: float = 0.0
    win_rate: float = 0.0
    avg_win: float = 0.0
    avg_loss: float = 0.0
    sharpe_ratio: float = 0.0
    max_drawdown: float = 0.0
    
    def update_metrics(self) -> None:
        """Recalculate derived metrics"""
        if self.total_trades > 0:
            self.win_rate = self.winning_trades / self.total_trades
        
        if self.winning_trades > 0 and self.losing_trades > 0:
            profit_factor = abs(self.avg_win * self.winning_trades / (self.avg_loss * self.losing_trades))
        else:
            profit_factor = 0.0
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'strategy_name': self.strategy_name,
            'total_trades': self.total_trades,
            'winning_trades': self.winning_trades,
            'losing_trades': self.losing_trades,
            'total_pnl': self.total_pnl,
            'win_rate': self.win_rate,
            'avg_win': self.avg_win,
            'avg_loss': self.avg_loss,
            'sharpe_ratio': self.sharpe_ratio,
            'max_drawdown': self.max_drawdown
        }


@dataclass
class StrategyConfig:
    """Configuration for StrategyManager"""
    enabled_strategies: List[str] = field(default_factory=list)
    strategy_weights: Dict[str, float] = field(default_factory=dict)
    min_confidence: float = 0.6
    max_strategies_per_symbol: int = 3
    ensemble_mode: str = "weighted_vote"
    performance_tracking: bool = True


class StrategyManager:
    """
    Unified Strategy Manager for coordinating all trading strategies.
    
    This class provides:
    - Strategy registration and lifecycle management
    - Signal generation and aggregation
    - Strategy performance tracking
    - Ensemble strategy coordination
    - Strategy selection and weighting
    """
    
    def __init__(self, config: Optional[Union[StrategyConfig, Dict[str, Any]]] = None):
        """
        Initialize the Strategy Manager.
        
        Args:
            config: Configuration object or dictionary
        """
        if isinstance(config, dict):
            self.config = StrategyConfig(**config)
        elif config is None:
            self.config = StrategyConfig()
        else:
            self.config = config
        
        self.strategies: Dict[str, Any] = {}
        self.strategy_status: Dict[str, StrategyStatus] = {}
        self.performance: Dict[str, StrategyPerformance] = {}
        self.signal_history: List[StrategySignal] = []
        self._initialized = False
        
        logger.info("StrategyManager initialized")
    
    def register_strategy(
        self,
        name: str,
        strategy: Any,
        weight: float = 1.0,
        auto_activate: bool = True
    ) -> bool:
        """
        Register a new strategy.
        
        Args:
            name: Strategy name
            strategy: Strategy instance
            weight: Strategy weight for ensemble
            auto_activate: Automatically activate the strategy
        
        Returns:
            True if registered successfully
        """
        try:
            self.strategies[name] = strategy
            self.strategy_status[name] = StrategyStatus.ACTIVE if auto_activate else StrategyStatus.INACTIVE
            self.performance[name] = StrategyPerformance(strategy_name=name)
            
            if name not in self.config.strategy_weights:
                self.config.strategy_weights[name] = weight
            
            logger.info(f"Registered strategy: {name} (weight={weight})")
            return True
            
        except Exception as e:
            logger.error(f"Failed to register strategy {name}: {e}")
            return False
    
    def activate_strategy(self, name: str) -> bool:
        """Activate a strategy"""
        if name in self.strategies:
            self.strategy_status[name] = StrategyStatus.ACTIVE
            logger.info(f"Activated strategy: {name}")
            return True
        return False
    
    def deactivate_strategy(self, name: str) -> bool:
        """Deactivate a strategy"""
        if name in self.strategies:
            self.strategy_status[name] = StrategyStatus.INACTIVE
            logger.info(f"Deactivated strategy: {name}")
            return True
        return False
    
    def generate_signals(
        self,
        symbol: str,
        data: pd.DataFrame,
        strategies: Optional[List[str]] = None
    ) -> List[StrategySignal]:
        """
        Generate signals from active strategies.
        
        Args:
            symbol: Trading symbol
            data: Market data
            strategies: Optional list of specific strategies to use
        
        Returns:
            List of generated signals
        """
        signals = []
        
        # Determine which strategies to use
        strategy_names = strategies or [
            name for name, status in self.strategy_status.items()
            if status == StrategyStatus.ACTIVE
        ]
        
        for name in strategy_names:
            if name not in self.strategies:
                continue
            try:
            
                strategy = self.strategies[name]
                
                # Generate signal from strategy
                signal = self._generate_strategy_signal(name, strategy, symbol, data)
                
                if signal and signal.confidence >= self.config.min_confidence:
                    signals.append(signal)
                    self.signal_history.append(signal)
                    
            except Exception as e:
                logger.error(f"Error generating signal from {name}: {e}")
        
        return signals
    
    def _generate_strategy_signal(
        self,
        name: str,
        strategy: Any,
        symbol: str,
        data: pd.DataFrame
    ) -> Optional[StrategySignal]:
        """Generate a signal from a specific strategy"""
        try:
            # Try different strategy interfaces
            if hasattr(strategy, 'generate_signal'):
                result = strategy.generate_signal(symbol, data)
            elif hasattr(strategy, 'analyze'):
                result = strategy.analyze(data)
            elif hasattr(strategy, 'get_signal'):
                result = strategy.get_signal(symbol, data)
            elif callable(strategy):
                result = strategy(symbol, data)
            else:
                logger.warning(f"Strategy {name} has no recognized signal interface")
                return None
            
            # Parse result into StrategySignal
            if result is None:
                return None
            
            if isinstance(result, dict):
                return StrategySignal(
                    strategy_name=name,
                    symbol=symbol,
                    signal_type=SignalType[result.get('signal', 'HOLD').upper()],
                    confidence=result.get('confidence', 0.5),
                    price=result.get('price', data['close'].iloc[-1] if 'close' in data.columns else 0),
                    metadata=result.get('metadata', {})
                )
            
            return result
            
        except Exception as e:
            logger.error(f"Error in strategy {name}: {e}")
            return None
    
    def combine_signals(
        self,
        signals: List[StrategySignal],
        method: Optional[str] = None
    ) -> Optional[StrategySignal]:
        """
        Combine multiple signals into a single signal.
        
        Args:
            signals: List of signals to combine
            method: Combination method (weighted_vote, majority, highest_confidence)
        
        Returns:
            Combined signal or None
        """
        if not signals:
            return None
        
        if len(signals) == 1:
            return signals[0]
        
        method = method or self.config.ensemble_mode
        
        if method == "weighted_vote":
            return self._weighted_vote_combine(signals)
        elif method == "majority":
            return self._majority_vote_combine(signals)
        elif method == "highest_confidence":
            return max(signals, key=lambda s: s.confidence)
        else:
            logger.warning(f"Unknown combination method: {method}")
            return signals[0]
    
    def _weighted_vote_combine(self, signals: List[StrategySignal]) -> StrategySignal:
        """Combine signals using weighted voting"""
        signal_votes: Dict[SignalType, float] = {}
        
        for signal in signals:
            weight = self.config.strategy_weights.get(signal.strategy_name, 1.0)
            vote_value = signal.confidence * weight
            
            if signal.signal_type not in signal_votes:
                signal_votes[signal.signal_type] = 0
            signal_votes[signal.signal_type] += vote_value
        
        # Find winning signal type
        winning_type = max(signal_votes.keys(), key=lambda t: signal_votes[t])
        
        # Get signals of winning type
        winning_signals = [s for s in signals if s.signal_type == winning_type]
        
        # Calculate combined confidence
        total_weight = sum(self.config.strategy_weights.get(s.strategy_name, 1.0) for s in winning_signals)
        combined_confidence = sum(
            s.confidence * self.config.strategy_weights.get(s.strategy_name, 1.0)
            for s in winning_signals
        ) / total_weight if total_weight > 0 else 0
        
        # Use most recent signal as base
        base_signal = max(winning_signals, key=lambda s: s.timestamp)
        
        return StrategySignal(
            strategy_name="ensemble",
            symbol=base_signal.symbol,
            signal_type=winning_type,
            confidence=combined_confidence,
            price=base_signal.price,
            metadata={
                'combined_from': [s.strategy_name for s in signals],
                'vote_weights': {k.name: v for k, v in signal_votes.items()}
            }
        )
    
    def _majority_vote_combine(self, signals: List[StrategySignal]) -> StrategySignal:
        """Combine signals using majority voting"""
        signal_counts: Dict[SignalType, int] = {}
        
        for signal in signals:
            if signal.signal_type not in signal_counts:
                signal_counts[signal.signal_type] = 0
            signal_counts[signal.signal_type] += 1
        
        winning_type = max(signal_counts.keys(), key=lambda t: signal_counts[t])
        winning_signals = [s for s in signals if s.signal_type == winning_type]
        
        return max(winning_signals, key=lambda s: s.confidence)
    
    def record_trade_result(
        self,
        strategy_name: str,
        pnl: float,
        is_win: bool
    ) -> None:
        """
        Record a trade result for performance tracking.
        
        Args:
            strategy_name: Name of the strategy
            pnl: Profit/loss amount
            is_win: Whether the trade was profitable
        """
        if not self.config.performance_tracking:
            return
        
        if strategy_name not in self.performance:
            self.performance[strategy_name] = StrategyPerformance(strategy_name=strategy_name)
        
        perf = self.performance[strategy_name]
        perf.total_trades += 1
        perf.total_pnl += pnl
        
        if is_win:
            perf.winning_trades += 1
            perf.avg_win = (perf.avg_win * (perf.winning_trades - 1) + pnl) / perf.winning_trades
        else:
            perf.losing_trades += 1
            perf.avg_loss = (perf.avg_loss * (perf.losing_trades - 1) + abs(pnl)) / perf.losing_trades
        
        perf.update_metrics()
    
    def get_performance(self, strategy_name: Optional[str] = None) -> Union[StrategyPerformance, Dict[str, StrategyPerformance]]:
        """
        Get performance metrics.
        
        Args:
            strategy_name: Optional specific strategy name
        
        Returns:
            Performance metrics for one or all strategies
        """
        if strategy_name:
            return self.performance.get(strategy_name)
        return self.performance
    
    def get_best_strategies(self, metric: str = "win_rate", top_n: int = 5) -> List[str]:
        """
        Get the best performing strategies.
        
        Args:
            metric: Metric to rank by
            top_n: Number of strategies to return
        
        Returns:
            List of strategy names
        """
        sorted_strategies = sorted(
            self.performance.items(),
            key=lambda x: getattr(x[1], metric, 0),
            reverse=True
        )
        
        return [name for name, _ in sorted_strategies[:top_n]]
    
    def get_stats(self) -> Dict[str, Any]:
        """Get StrategyManager statistics"""
        active_count = sum(1 for s in self.strategy_status.values() if s == StrategyStatus.ACTIVE)
        
        return {
            'total_strategies': len(self.strategies),
            'active_strategies': active_count,
            'total_signals_generated': len(self.signal_history),
            'performance_tracked': self.config.performance_tracking,
            'ensemble_mode': self.config.ensemble_mode
        }


# Factory function
def create_strategy_manager(config: Optional[Dict[str, Any]] = None) -> StrategyManager:
    """Create a configured StrategyManager instance"""
    return StrategyManager(config)


# Singleton instance
_strategy_manager: Optional[StrategyManager] = None


def get_strategy_manager() -> StrategyManager:
    """Get the global StrategyManager instance"""
    global _strategy_manager
    if _strategy_manager is None:
        _strategy_manager = StrategyManager()
    return _strategy_manager
