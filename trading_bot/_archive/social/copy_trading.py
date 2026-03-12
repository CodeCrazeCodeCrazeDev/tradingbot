import logging
logger = logging.getLogger(__name__)
"""Social/Copy Trading Features Module

This module implements social trading functionality including strategy sharing,
performance tracking, leaderboards, and automated copy trading.
"""

import numpy as np
import pandas as pd
from typing import Any, Callable, Dict, List, Optional, Union
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum, auto
import uuid
import json
from loguru import logger
import numpy
import pandas


class StrategyStatus(Enum):
    """Status of a trading strategy."""
    ACTIVE = auto()
    PAUSED = auto()
    STOPPED = auto()
    ARCHIVED = auto()


class CopyMode(Enum):
    """Copy trading modes."""
    FULL_COPY = auto()        # Copy all trades
    PROPORTIONAL = auto()     # Copy with position sizing
    SELECTIVE = auto()        # Copy only certain symbols
    RISK_ADJUSTED = auto()    # Copy with risk adjustments


@dataclass
class StrategyPerformance:
    """Performance metrics for a trading strategy."""
    strategy_id: str
    total_return: float
    sharpe_ratio: float
    max_drawdown: float
    win_rate: float
    profit_factor: float
    total_trades: int
    avg_trade_duration: float  # hours
    volatility: float
    last_updated: datetime
    monthly_returns: List[float] = field(default_factory=list)
    daily_returns: List[float] = field(default_factory=list)


@dataclass
class TradingStrategy:
    """Represents a tradable strategy."""
    id: str
    name: str
    description: str
    creator_id: str
    creator_name: str
    status: StrategyStatus
    performance: StrategyPerformance
    risk_level: str  # 'low', 'medium', 'high'
    min_capital: float
    max_followers: int
    current_followers: int
    creation_date: datetime
    tags: List[str] = field(default_factory=list)
    symbols: List[str] = field(default_factory=list)
    is_public: bool = True
    subscription_fee: float = 0.0  # Monthly fee


@dataclass
class CopySettings:
    """Settings for copying a strategy."""
    strategy_id: str
    follower_id: str
    copy_mode: CopyMode
    allocation_amount: float
    risk_multiplier: float = 1.0
    max_position_size: float = 0.1  # 10% of capital
    symbols_filter: List[str] = field(default_factory=list)
    stop_loss_override: Optional[float] = None
    take_profit_override: Optional[float] = None
    is_active: bool = True
    start_date: datetime = field(default_factory=datetime.now)


@dataclass
class CopyTrade:
    """Represents a copied trade."""
    id: str
    original_trade_id: str
    strategy_id: str
    follower_id: str
    symbol: str
    side: str  # 'buy' or 'sell'
    original_size: float
    copied_size: float
    original_price: float
    copied_price: float
    timestamp: datetime
    status: str  # 'pending', 'executed', 'failed'


class SocialTradingPlatform:
    """Platform for social and copy trading functionality."""
    
    def __init__(self, config: Optional[Dict] = None):
        """Initialize the social trading platform.
        
        Args:
            config: Configuration dictionary
        """
        self.config = config or {}
        self._init_default_config()
        
        # Data storage
        self.strategies: Dict[str, TradingStrategy] = {}
        self.copy_settings: Dict[str, List[CopySettings]] = {}  # follower_id -> settings
        self.copy_trades: Dict[str, List[CopyTrade]] = {}  # strategy_id -> trades
        self.performance_history: Dict[str, List[StrategyPerformance]] = {}
        
        logger.info("SocialTradingPlatform initialized")
    
    def _init_default_config(self):
        """Initialize default configuration."""
        defaults = {
            "max_strategies_per_user": 10,
            "max_followers_per_strategy": 1000,
            "min_performance_period": 30,  # days
            "leaderboard_size": 50,
            "copy_delay_ms": 100,  # milliseconds
            "performance_update_interval": 3600,  # seconds
        }
        
        for key, value in defaults.items():
            if key not in self.config:
                self.config[key] = value
    
    def create_strategy(self,
                       name: str,
                       description: str,
                       creator_id: str,
                       creator_name: str,
                       risk_level: str = 'medium',
                       min_capital: float = 1000.0,
                       max_followers: int = 100,
                       tags: List[str] = None,
                       symbols: List[str] = None) -> str:
        """Create a new trading strategy.
        
        Args:
            name: Strategy name
            description: Strategy description
            creator_id: Creator user ID
            creator_name: Creator display name
            risk_level: Risk level ('low', 'medium', 'high')
            min_capital: Minimum capital required
            max_followers: Maximum number of followers
            tags: Strategy tags
            symbols: Supported symbols
            
        Returns:
            Strategy ID
        """
        strategy_id = str(uuid.uuid4())
        
        # Initialize performance metrics
        performance = StrategyPerformance(
            strategy_id=strategy_id,
            total_return=0.0,
            sharpe_ratio=0.0,
            max_drawdown=0.0,
            win_rate=0.0,
            profit_factor=0.0,
            total_trades=0,
            avg_trade_duration=0.0,
            volatility=0.0,
            last_updated=datetime.now()
        )
        
        # Create strategy
        strategy = TradingStrategy(
            id=strategy_id,
            name=name,
            description=description,
            creator_id=creator_id,
            creator_name=creator_name,
            status=StrategyStatus.ACTIVE,
            performance=performance,
            risk_level=risk_level,
            min_capital=min_capital,
            max_followers=max_followers,
            current_followers=0,
            creation_date=datetime.now(),
            tags=tags or [],
            symbols=symbols or []
        )
        
        self.strategies[strategy_id] = strategy
        self.copy_trades[strategy_id] = []
        self.performance_history[strategy_id] = []
        
        logger.info(f"Created strategy '{name}' with ID {strategy_id}")
        return strategy_id
    
    def follow_strategy(self,
                       strategy_id: str,
                       follower_id: str,
                       copy_settings: CopySettings) -> bool:
        """Follow a trading strategy.
        
        Args:
            strategy_id: Strategy to follow
            follower_id: Follower user ID
            copy_settings: Copy trading settings
            
        Returns:
            True if successful, False otherwise
        """
        if strategy_id not in self.strategies:
            logger.error(f"Strategy {strategy_id} not found")
            return False
        
        strategy = self.strategies[strategy_id]
        
        # Check if strategy can accept more followers
        if strategy.current_followers >= strategy.max_followers:
            logger.error(f"Strategy {strategy_id} has reached maximum followers")
            return False
        
        # Check minimum capital requirement
        if copy_settings.allocation_amount < strategy.min_capital:
            logger.error(f"Allocation amount below minimum capital requirement")
            return False
        
        # Add copy settings
        if follower_id not in self.copy_settings:
            self.copy_settings[follower_id] = []
        
        # Check if already following
        existing = [cs for cs in self.copy_settings[follower_id] if cs.strategy_id == strategy_id]
        if existing:
            logger.warning(f"User {follower_id} already following strategy {strategy_id}")
            return False
        
        self.copy_settings[follower_id].append(copy_settings)
        strategy.current_followers += 1
        
        logger.info(f"User {follower_id} now following strategy {strategy_id}")
        return True
    
    def unfollow_strategy(self, strategy_id: str, follower_id: str) -> bool:
        """Unfollow a trading strategy.
        
        Args:
            strategy_id: Strategy to unfollow
            follower_id: Follower user ID
            
        Returns:
            True if successful, False otherwise
        """
        if follower_id not in self.copy_settings:
            return False
        
        # Remove copy settings
        original_count = len(self.copy_settings[follower_id])
        self.copy_settings[follower_id] = [
            cs for cs in self.copy_settings[follower_id] 
            if cs.strategy_id != strategy_id
        ]
        
        if len(self.copy_settings[follower_id]) < original_count:
            # Update follower count
            if strategy_id in self.strategies:
                self.strategies[strategy_id].current_followers -= 1
            
            logger.info(f"User {follower_id} unfollowed strategy {strategy_id}")
            return True
        
        return False
    
    def execute_copy_trade(self,
                          strategy_id: str,
                          original_trade: Dict[str, Any]) -> List[CopyTrade]:
        """Execute copy trades for a strategy.
        
        Args:
            strategy_id: Strategy ID
            original_trade: Original trade information
            
        Returns:
            List of executed copy trades
        """
        if strategy_id not in self.strategies:
            return []
        
        copy_trades = []
        
        # Find all followers of this strategy
        for follower_id, settings_list in self.copy_settings.items():
            for settings in settings_list:
                if settings.strategy_id == strategy_id and settings.is_active:
                    # Check symbol filter
                    if settings.symbols_filter and original_trade['symbol'] not in settings.symbols_filter:
                        continue
                    
                    # Calculate copy size based on mode
                    copied_size = self._calculate_copy_size(original_trade, settings)
                    
                    if copied_size > 0:
                        copy_trade = CopyTrade(
                            id=str(uuid.uuid4()),
                            original_trade_id=original_trade.get('id', ''),
                            strategy_id=strategy_id,
                            follower_id=follower_id,
                            symbol=original_trade['symbol'],
                            side=original_trade['side'],
                            original_size=original_trade['size'],
                            copied_size=copied_size,
                            original_price=original_trade['price'],
                            copied_price=original_trade['price'],  # Assuming same price
                            timestamp=datetime.now(),
                            status='pending'
                        )
                        
                        copy_trades.append(copy_trade)
                        
                        # Store copy trade
                        if strategy_id not in self.copy_trades:
                            self.copy_trades[strategy_id] = []
                        self.copy_trades[strategy_id].append(copy_trade)
        
        logger.info(f"Generated {len(copy_trades)} copy trades for strategy {strategy_id}")
        return copy_trades
    
    def _calculate_copy_size(self,
                           original_trade: Dict[str, Any],
                           settings: CopySettings) -> float:
        """Calculate the size for a copy trade.
        
        Args:
            original_trade: Original trade information
            settings: Copy settings
            
        Returns:
            Calculated copy size
        """
        if settings.copy_mode == CopyMode.FULL_COPY:
            # Copy exact size (adjusted by risk multiplier)
            return original_trade['size'] * settings.risk_multiplier
        
        elif settings.copy_mode == CopyMode.PROPORTIONAL:
            # Calculate proportional size based on allocation
            # This would need access to strategy's total capital
            # For now, use a simple percentage
            return original_trade['size'] * 0.1 * settings.risk_multiplier
        
        elif settings.copy_mode == CopyMode.RISK_ADJUSTED:
            # Adjust size based on risk level and allocation
            base_size = settings.allocation_amount * 0.02  # 2% per trade
            return min(base_size, settings.max_position_size * settings.allocation_amount)
        
        else:  # SELECTIVE mode
            return original_trade['size'] * settings.risk_multiplier
    
    def update_strategy_performance(self,
                                  strategy_id: str,
                                  trades_data: List[Dict[str, Any]]) -> bool:
        """Update performance metrics for a strategy.
        
        Args:
            strategy_id: Strategy ID
            trades_data: List of trade data
            
        Returns:
            True if successful, False otherwise
        """
        if strategy_id not in self.strategies:
            return False
        
        strategy = self.strategies[strategy_id]
        
        if not trades_data:
            return True
        
        # Calculate performance metrics
        returns = [trade.get('return', 0.0) for trade in trades_data]
        
        # Total return
        total_return = sum(returns)
        
        # Win rate
        winning_trades = [r for r in returns if r > 0]
        win_rate = len(winning_trades) / len(returns) if returns else 0.0
        
        # Profit factor
        gross_profit = sum(winning_trades) if winning_trades else 0.0
        gross_loss = abs(sum([r for r in returns if r < 0]))
        profit_factor = gross_profit / gross_loss if gross_loss > 0 else float('inf')
        
        # Sharpe ratio (simplified)
        if len(returns) > 1:
            avg_return = np.mean(returns)
            std_return = np.std(returns)
            sharpe_ratio = avg_return / std_return if std_return > 0 else 0.0
        else:
            sharpe_ratio = 0.0
        
        # Max drawdown (simplified)
        cumulative_returns = np.cumsum(returns)
        running_max = np.maximum.accumulate(cumulative_returns)
        drawdowns = cumulative_returns - running_max
        max_drawdown = abs(np.min(drawdowns)) if len(drawdowns) > 0 else 0.0
        
        # Average trade duration
        durations = [trade.get('duration_hours', 0.0) for trade in trades_data]
        avg_duration = np.mean(durations) if durations else 0.0
        
        # Volatility
        volatility = np.std(returns) if len(returns) > 1 else 0.0
        
        # Update performance
        strategy.performance.total_return = total_return
        strategy.performance.sharpe_ratio = sharpe_ratio
        strategy.performance.max_drawdown = max_drawdown
        strategy.performance.win_rate = win_rate
        strategy.performance.profit_factor = profit_factor
        strategy.performance.total_trades = len(trades_data)
        strategy.performance.avg_trade_duration = avg_duration
        strategy.performance.volatility = volatility
        strategy.performance.last_updated = datetime.now()
        
        # Store historical performance
        if strategy_id not in self.performance_history:
            self.performance_history[strategy_id] = []
        
        # Create a copy for history
        historical_performance = StrategyPerformance(
            strategy_id=strategy_id,
            total_return=total_return,
            sharpe_ratio=sharpe_ratio,
            max_drawdown=max_drawdown,
            win_rate=win_rate,
            profit_factor=profit_factor,
            total_trades=len(trades_data),
            avg_trade_duration=avg_duration,
            volatility=volatility,
            last_updated=datetime.now(),
            daily_returns=returns[-30:] if len(returns) >= 30 else returns  # Last 30 days
        )
        
        self.performance_history[strategy_id].append(historical_performance)
        
        logger.info(f"Updated performance for strategy {strategy_id}")
        return True
    
    def get_leaderboard(self,
                       sort_by: str = 'total_return',
                       time_period: int = 30,  # days
                       min_trades: int = 10) -> List[Dict[str, Any]]:
        """Get strategy leaderboard.
        
        Args:
            sort_by: Metric to sort by
            time_period: Time period in days
            min_trades: Minimum number of trades required
            
        Returns:
            List of top strategies
        """
        leaderboard = []
        
        for strategy in self.strategies.values():
            # Filter by minimum trades and time period
            if strategy.performance.total_trades < min_trades:
                continue
            
            days_active = (datetime.now() - strategy.creation_date).days
            if days_active < self.config["min_performance_period"]:
                continue
            
            # Calculate score based on sort criteria
            perf = strategy.performance
            
            if sort_by == 'total_return':
                score = perf.total_return
            elif sort_by == 'sharpe_ratio':
                score = perf.sharpe_ratio
            elif sort_by == 'win_rate':
                score = perf.win_rate
            elif sort_by == 'profit_factor':
                score = perf.profit_factor
            else:
                score = perf.total_return  # Default
            
            leaderboard.append({
                'strategy_id': strategy.id,
                'name': strategy.name,
                'creator_name': strategy.creator_name,
                'score': score,
                'total_return': perf.total_return,
                'sharpe_ratio': perf.sharpe_ratio,
                'max_drawdown': perf.max_drawdown,
                'win_rate': perf.win_rate,
                'total_trades': perf.total_trades,
                'current_followers': strategy.current_followers,
                'risk_level': strategy.risk_level,
                'tags': strategy.tags
            })
        
        # Sort by score (descending)
        leaderboard.sort(key=lambda x: x['score'], reverse=True)
        
        # Return top N
        return leaderboard[:self.config["leaderboard_size"]]
    
    def search_strategies(self,
                         query: str = '',
                         risk_level: str = '',
                         tags: List[str] = None,
                         min_return: float = None,
                         max_drawdown: float = None) -> List[Dict[str, Any]]:
        """Search for trading strategies.
        
        Args:
            query: Text search query
            risk_level: Risk level filter
            tags: Tag filters
            min_return: Minimum return filter
            max_drawdown: Maximum drawdown filter
            
        Returns:
            List of matching strategies
        """
        results = []
        
        for strategy in self.strategies.values():
            # Skip inactive strategies
            if strategy.status != StrategyStatus.ACTIVE:
                continue
            
            # Text search
            if query:
                search_text = f"{strategy.name} {strategy.description} {strategy.creator_name}".lower()
                if query.lower() not in search_text:
                    continue
            
            # Risk level filter
            if risk_level and strategy.risk_level != risk_level:
                continue
            
            # Tags filter
            if tags:
                if not any(tag in strategy.tags for tag in tags):
                    continue
            
            # Performance filters
            if min_return is not None and strategy.performance.total_return < min_return:
                continue
            
            if max_drawdown is not None and strategy.performance.max_drawdown > max_drawdown:
                continue
            
            results.append({
                'strategy_id': strategy.id,
                'name': strategy.name,
                'description': strategy.description,
                'creator_name': strategy.creator_name,
                'risk_level': strategy.risk_level,
                'performance': {
                    'total_return': strategy.performance.total_return,
                    'sharpe_ratio': strategy.performance.sharpe_ratio,
                    'max_drawdown': strategy.performance.max_drawdown,
                    'win_rate': strategy.performance.win_rate,
                    'total_trades': strategy.performance.total_trades
                },
                'current_followers': strategy.current_followers,
                'max_followers': strategy.max_followers,
                'min_capital': strategy.min_capital,
                'tags': strategy.tags,
                'symbols': strategy.symbols
            })
        
        return results
    
    def get_strategy_details(self, strategy_id: str) -> Optional[Dict[str, Any]]:
        """Get detailed information about a strategy.
        
        Args:
            strategy_id: Strategy ID
            
        Returns:
            Strategy details or None if not found
        """
        if strategy_id not in self.strategies:
            return None
        
        strategy = self.strategies[strategy_id]
        
        # Get recent copy trades
        recent_trades = []
        if strategy_id in self.copy_trades:
            recent_trades = self.copy_trades[strategy_id][-20:]  # Last 20 trades
        
        # Get performance history
        performance_history = self.performance_history.get(strategy_id, [])
        
        return {
            'strategy': {
                'id': strategy.id,
                'name': strategy.name,
                'description': strategy.description,
                'creator_name': strategy.creator_name,
                'status': strategy.status.name,
                'risk_level': strategy.risk_level,
                'min_capital': strategy.min_capital,
                'current_followers': strategy.current_followers,
                'max_followers': strategy.max_followers,
                'creation_date': strategy.creation_date.isoformat(),
                'tags': strategy.tags,
                'symbols': strategy.symbols,
                'subscription_fee': strategy.subscription_fee
            },
            'performance': {
                'total_return': strategy.performance.total_return,
                'sharpe_ratio': strategy.performance.sharpe_ratio,
                'max_drawdown': strategy.performance.max_drawdown,
                'win_rate': strategy.performance.win_rate,
                'profit_factor': strategy.performance.profit_factor,
                'total_trades': strategy.performance.total_trades,
                'avg_trade_duration': strategy.performance.avg_trade_duration,
                'volatility': strategy.performance.volatility,
                'last_updated': strategy.performance.last_updated.isoformat()
            },
            'recent_trades': [
                {
                    'id': trade.id,
                    'symbol': trade.symbol,
                    'side': trade.side,
                    'size': trade.copied_size,
                    'price': trade.copied_price,
                    'timestamp': trade.timestamp.isoformat(),
                    'status': trade.status
                }
                for trade in recent_trades
            ],
            'performance_history': [
                {
                    'date': perf.last_updated.isoformat(),
                    'total_return': perf.total_return,
                    'sharpe_ratio': perf.sharpe_ratio,
                    'max_drawdown': perf.max_drawdown,
                    'total_trades': perf.total_trades
                }
                for perf in performance_history[-30:]  # Last 30 updates
            ]
        }
    
    def get_user_following(self, user_id: str) -> List[Dict[str, Any]]:
        """Get strategies that a user is following.
        
        Args:
            user_id: User ID
            
        Returns:
            List of followed strategies
        """
        if user_id not in self.copy_settings:
            return []
        
        following = []
        
        for settings in self.copy_settings[user_id]:
            if settings.strategy_id in self.strategies:
                strategy = self.strategies[settings.strategy_id]
                
                following.append({
                    'strategy_id': strategy.id,
                    'strategy_name': strategy.name,
                    'creator_name': strategy.creator_name,
                    'copy_mode': settings.copy_mode.name,
                    'allocation_amount': settings.allocation_amount,
                    'risk_multiplier': settings.risk_multiplier,
                    'is_active': settings.is_active,
                    'start_date': settings.start_date.isoformat(),
                    'performance': {
                        'total_return': strategy.performance.total_return,
                        'win_rate': strategy.performance.win_rate,
                        'total_trades': strategy.performance.total_trades
                    }
                })
        
        return following
