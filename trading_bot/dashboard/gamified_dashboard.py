import logging
logger = logging.getLogger(__name__)
"""Gamified Dashboard System.

This module implements a gamified trading dashboard with achievements,
scoring systems, and performance tracking like a trading game.
"""

import numpy as np
from enum import Enum, auto
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
from datetime import datetime, timedelta
import json
from loguru import logger
import numpy


class AchievementType(Enum):
    """Types of trading achievements."""
    WIN_STREAK = auto()
    PROFIT_TARGET = auto()
    CONSISTENCY = auto()
    RISK_MANAGEMENT = auto()
    ACCURACY = auto()
    VOLUME = auto()
    MILESTONE = auto()
    SPECIAL = auto()


class BadgeLevel(Enum):
    """Badge levels for achievements."""
    BRONZE = 1
    SILVER = 2
    GOLD = 3
    PLATINUM = 4
    DIAMOND = 5


@dataclass
class Achievement:
    """Trading achievement with requirements and rewards."""
    id: str
    name: str
    description: str
    achievement_type: AchievementType
    badge_level: BadgeLevel
    requirements: Dict[str, Any]
    points: int
    unlocked: bool = False
    unlock_date: Optional[datetime] = None
    progress: float = 0.0  # 0.0 to 1.0


@dataclass
class TradingStats:
    """Current trading statistics."""
    total_trades: int = 0
    winning_trades: int = 0
    losing_trades: int = 0
    current_streak: int = 0
    best_streak: int = 0
    worst_streak: int = 0
    total_profit: float = 0.0
    total_loss: float = 0.0
    max_drawdown: float = 0.0
    current_drawdown: float = 0.0
    sharpe_ratio: float = 0.0
    profit_factor: float = 0.0
    
    @property
    def win_rate(self) -> float:
        """Calculate win rate percentage."""
        return (self.winning_trades / self.total_trades * 100) if self.total_trades > 0 else 0.0
    
    @property
    def net_profit(self) -> float:
        """Calculate net profit."""
        return self.total_profit + self.total_loss


class GamifiedDashboard:
    """Gamified trading dashboard with achievements and scoring.
    
    Features:
    - Achievement system with badges
    - Performance scoring
    - Streak tracking
    - Level progression
    - Leaderboard functionality
    """
    
    def __init__(self, config: Optional[Dict] = None):
        """Initialize the gamified dashboard.
        
        Args:
            config: Configuration dictionary
        """
        try:
            self.config = config or {}
            self.stats = TradingStats()
            self.achievements = self._initialize_achievements()
            self.total_points = 0
            self.level = 1
            self.experience = 0
            self.trade_history = []
            logger.info("GamifiedDashboard initialized")
        except Exception as e:
            logger.error(f"Error in __init__: {e}")
            raise
    
    def _initialize_achievements(self) -> List[Achievement]:
        """Initialize the achievement system."""
        try:
            achievements = [
                # Win Streak Achievements
                Achievement(
                    id="first_win",
                    name="First Victory",
                    description="Win your first trade",
                    achievement_type=AchievementType.WIN_STREAK,
                    badge_level=BadgeLevel.BRONZE,
                    requirements={"winning_trades": 1},
                    points=10
                ),
                Achievement(
                    id="win_streak_5",
                    name="Hot Streak",
                    description="Win 5 trades in a row",
                    achievement_type=AchievementType.WIN_STREAK,
                    badge_level=BadgeLevel.SILVER,
                    requirements={"win_streak": 5},
                    points=50
                ),
                Achievement(
                    id="win_streak_10",
                    name="Unstoppable",
                    description="Win 10 trades in a row",
                    achievement_type=AchievementType.WIN_STREAK,
                    badge_level=BadgeLevel.GOLD,
                    requirements={"win_streak": 10},
                    points=100
                ),
            
                # Profit Target Achievements
                Achievement(
                    id="profit_100",
                    name="First Hundred",
                    description="Earn $100 in profit",
                    achievement_type=AchievementType.PROFIT_TARGET,
                    badge_level=BadgeLevel.BRONZE,
                    requirements={"net_profit": 100},
                    points=25
                ),
                Achievement(
                    id="profit_1000",
                    name="Four Figures",
                    description="Earn $1,000 in profit",
                    achievement_type=AchievementType.PROFIT_TARGET,
                    badge_level=BadgeLevel.SILVER,
                    requirements={"net_profit": 1000},
                    points=100
                ),
                Achievement(
                    id="profit_10000",
                    name="Five Figures",
                    description="Earn $10,000 in profit",
                    achievement_type=AchievementType.PROFIT_TARGET,
                    badge_level=BadgeLevel.GOLD,
                    requirements={"net_profit": 10000},
                    points=500
                ),
            
                # Accuracy Achievements
                Achievement(
                    id="accuracy_70",
                    name="Sharpshooter",
                    description="Maintain 70% win rate over 20+ trades",
                    achievement_type=AchievementType.ACCURACY,
                    badge_level=BadgeLevel.SILVER,
                    requirements={"win_rate": 70, "min_trades": 20},
                    points=75
                ),
                Achievement(
                    id="accuracy_80",
                    name="Sniper",
                    description="Maintain 80% win rate over 50+ trades",
                    achievement_type=AchievementType.ACCURACY,
                    badge_level=BadgeLevel.GOLD,
                    requirements={"win_rate": 80, "min_trades": 50},
                    points=200
                ),
            
                # Risk Management Achievements
                Achievement(
                    id="low_drawdown",
                    name="Risk Master",
                    description="Keep max drawdown under 5% over 100+ trades",
                    achievement_type=AchievementType.RISK_MANAGEMENT,
                    badge_level=BadgeLevel.GOLD,
                    requirements={"max_drawdown": 5, "min_trades": 100},
                    points=150
                ),
            
                # Volume Achievements
                Achievement(
                    id="trades_100",
                    name="Centurion",
                    description="Complete 100 trades",
                    achievement_type=AchievementType.VOLUME,
                    badge_level=BadgeLevel.SILVER,
                    requirements={"total_trades": 100},
                    points=50
                ),
                Achievement(
                    id="trades_1000",
                    name="Veteran Trader",
                    description="Complete 1,000 trades",
                    achievement_type=AchievementType.VOLUME,
                    badge_level=BadgeLevel.GOLD,
                    requirements={"total_trades": 1000},
                    points=200
                ),
            
                # Special Achievements
                Achievement(
                    id="perfect_week",
                    name="Perfect Week",
                    description="Win every trade in a week (min 5 trades)",
                    achievement_type=AchievementType.SPECIAL,
                    badge_level=BadgeLevel.PLATINUM,
                    requirements={"weekly_perfect": True},
                    points=300
                )
            ]
        
            return achievements
        except Exception as e:
            logger.error(f"Error in _initialize_achievements: {e}")
            raise
    
    def update_trade_result(self, trade_data: Dict[str, Any]):
        """Update dashboard with new trade result.
        
        Args:
            trade_data: Dictionary with trade information
        """
        # Extract trade information
        try:
            pnl = trade_data.get('pnl', 0.0)
            is_winner = pnl > 0
        
            # Update basic stats
            self.stats.total_trades += 1
        
            if is_winner:
                self.stats.winning_trades += 1
                self.stats.total_profit += pnl
                self.stats.current_streak = max(0, self.stats.current_streak) + 1
            else:
                self.stats.losing_trades += 1
                self.stats.total_loss += pnl  # pnl is negative for losses
                self.stats.current_streak = min(0, self.stats.current_streak) - 1
        
            # Update streak records
            if self.stats.current_streak > 0:
                self.stats.best_streak = max(self.stats.best_streak, self.stats.current_streak)
            else:
                self.stats.worst_streak = min(self.stats.worst_streak, self.stats.current_streak)
        
            # Update drawdown (simplified calculation)
            if self.stats.net_profit > 0:
                self.stats.current_drawdown = 0.0
            else:
                self.stats.current_drawdown = abs(self.stats.net_profit)
                self.stats.max_drawdown = max(self.stats.max_drawdown, self.stats.current_drawdown)
        
            # Calculate profit factor
            if self.stats.total_loss < 0:
                self.stats.profit_factor = abs(self.stats.total_profit / self.stats.total_loss)
        
            # Add to trade history
            self.trade_history.append({
                'timestamp': datetime.now(),
                'pnl': pnl,
                'is_winner': is_winner,
                'cumulative_pnl': self.stats.net_profit
            })
        
            # Check for achievements
            self._check_achievements()
        
            # Update experience and level
            self._update_experience(trade_data)
        
            logger.info(f"Updated dashboard: Trade #{self.stats.total_trades}, "
                       f"P&L: {pnl:.2f}, Win Rate: {self.stats.win_rate:.1f}%")
        except Exception as e:
            logger.error(f"Error in update_trade_result: {e}")
            raise
    
    def _check_achievements(self):
        """Check and unlock achievements based on current stats."""
        try:
            for achievement in self.achievements:
                if achievement.unlocked:
                    continue
            
                # Check if requirements are met
                if self._meets_requirements(achievement):
                    self._unlock_achievement(achievement)
        except Exception as e:
            logger.error(f"Error in _check_achievements: {e}")
            raise
    
    def _meets_requirements(self, achievement: Achievement) -> bool:
        """Check if achievement requirements are met."""
        try:
            reqs = achievement.requirements
        
            # Win streak requirements
            if "win_streak" in reqs:
                if self.stats.current_streak < reqs["win_streak"]:
                    return False
        
            # Winning trades requirement
            if "winning_trades" in reqs:
                if self.stats.winning_trades < reqs["winning_trades"]:
                    return False
        
            # Net profit requirement
            if "net_profit" in reqs:
                if self.stats.net_profit < reqs["net_profit"]:
                    return False
        
            # Win rate requirement
            if "win_rate" in reqs:
                min_trades = reqs.get("min_trades", 1)
                if self.stats.total_trades < min_trades:
                    return False
                if self.stats.win_rate < reqs["win_rate"]:
                    return False
        
            # Max drawdown requirement
            if "max_drawdown" in reqs:
                min_trades = reqs.get("min_trades", 1)
                if self.stats.total_trades < min_trades:
                    return False
                drawdown_percent = (self.stats.max_drawdown / max(abs(self.stats.net_profit), 1)) * 100
                if drawdown_percent > reqs["max_drawdown"]:
                    return False
        
            # Total trades requirement
            if "total_trades" in reqs:
                if self.stats.total_trades < reqs["total_trades"]:
                    return False
        
            # Special weekly perfect requirement
            if "weekly_perfect" in reqs:
                if not self._check_weekly_perfect():
                    return False
        
            return True
        except Exception as e:
            logger.error(f"Error in _meets_requirements: {e}")
            raise
    
    def _unlock_achievement(self, achievement: Achievement):
        """Unlock an achievement and award points."""
        try:
            achievement.unlocked = True
            achievement.unlock_date = datetime.now()
            achievement.progress = 1.0
        
            self.total_points += achievement.points
            self.experience += achievement.points
        
            logger.info(f"🏆 ACHIEVEMENT UNLOCKED: {achievement.name} (+{achievement.points} points)")
        except Exception as e:
            logger.error(f"Error in _unlock_achievement: {e}")
            raise
    
    def _update_experience(self, trade_data: Dict[str, Any]):
        """Update experience points and level."""
        # Base experience for completing a trade
        try:
            base_exp = 1
        
            # Bonus experience for winning
            if trade_data.get('pnl', 0) > 0:
                base_exp += 2
        
            # Bonus for maintaining streaks
            if self.stats.current_streak >= 3:
                base_exp += self.stats.current_streak
        
            self.experience += base_exp
        
            # Check for level up
            required_exp = self._calculate_required_experience(self.level)
            if self.experience >= required_exp:
                self.level += 1
                logger.info(f"🎉 LEVEL UP! You are now level {self.level}")
        except Exception as e:
            logger.error(f"Error in _update_experience: {e}")
            raise
    
    def _calculate_required_experience(self, level: int) -> int:
        """Calculate experience required for a given level."""
        return level * 100 + (level - 1) * 50
    
    def _check_weekly_perfect(self) -> bool:
        """Check if the last week had perfect trades."""
        try:
            if len(self.trade_history) < 5:
                return False
        
            # Get trades from the last 7 days
            week_ago = datetime.now() - timedelta(days=7)
            recent_trades = [t for t in self.trade_history if t['timestamp'] >= week_ago]
        
            if len(recent_trades) < 5:
                return False
        
            # Check if all recent trades were winners
            return all(t['is_winner'] for t in recent_trades)
        except Exception as e:
            logger.error(f"Error in _check_weekly_perfect: {e}")
            raise
    
    def get_dashboard_data(self) -> Dict[str, Any]:
        """Get comprehensive dashboard data.
        
        Returns:
            Dictionary with all dashboard information
        """
        # Calculate progress for locked achievements
        try:
            for achievement in self.achievements:
                if not achievement.unlocked:
                    achievement.progress = self._calculate_achievement_progress(achievement)
        
            # Get recent achievements (last 5)
            recent_achievements = [
                a for a in self.achievements 
                if a.unlocked and a.unlock_date
            ]
            recent_achievements.sort(key=lambda x: x.unlock_date, reverse=True)
            recent_achievements = recent_achievements[:5]
        
            # Calculate next level progress
            current_level_exp = self._calculate_required_experience(self.level - 1) if self.level > 1 else 0
            next_level_exp = self._calculate_required_experience(self.level)
            level_progress = (self.experience - current_level_exp) / (next_level_exp - current_level_exp)
        
            return {
                'stats': {
                    'total_trades': self.stats.total_trades,
                    'winning_trades': self.stats.winning_trades,
                    'losing_trades': self.stats.losing_trades,
                    'win_rate': self.stats.win_rate,
                    'current_streak': self.stats.current_streak,
                    'best_streak': self.stats.best_streak,
                    'worst_streak': self.stats.worst_streak,
                    'net_profit': self.stats.net_profit,
                    'total_profit': self.stats.total_profit,
                    'total_loss': self.stats.total_loss,
                    'max_drawdown': self.stats.max_drawdown,
                    'current_drawdown': self.stats.current_drawdown,
                    'profit_factor': self.stats.profit_factor
                },
                'gamification': {
                    'level': self.level,
                    'experience': self.experience,
                    'total_points': self.total_points,
                    'level_progress': level_progress,
                    'next_level_exp': next_level_exp
                },
                'achievements': {
                    'total': len(self.achievements),
                    'unlocked': len([a for a in self.achievements if a.unlocked]),
                    'recent': [
                        {
                            'name': a.name,
                            'description': a.description,
                            'badge_level': a.badge_level.name,
                            'points': a.points,
                            'unlock_date': a.unlock_date.isoformat() if a.unlock_date else None
                        }
                        for a in recent_achievements
                    ],
                    'in_progress': [
                        {
                            'name': a.name,
                            'description': a.description,
                            'progress': a.progress,
                            'badge_level': a.badge_level.name,
                            'points': a.points
                        }
                        for a in self.achievements 
                        if not a.unlocked and a.progress > 0
                    ]
                }
            }
        except Exception as e:
            logger.error(f"Error in get_dashboard_data: {e}")
            raise
    
    def _calculate_achievement_progress(self, achievement: Achievement) -> float:
        """Calculate progress towards an achievement (0.0 to 1.0)."""
        try:
            reqs = achievement.requirements
            progress = 0.0
        
            if "win_streak" in reqs:
                progress = max(progress, min(1.0, max(0, self.stats.current_streak) / reqs["win_streak"]))
        
            if "winning_trades" in reqs:
                progress = max(progress, min(1.0, self.stats.winning_trades / reqs["winning_trades"]))
        
            if "net_profit" in reqs:
                progress = max(progress, min(1.0, max(0, self.stats.net_profit) / reqs["net_profit"]))
        
            if "total_trades" in reqs:
                progress = max(progress, min(1.0, self.stats.total_trades / reqs["total_trades"]))
        
            if "win_rate" in reqs:
                min_trades = reqs.get("min_trades", 1)
                if self.stats.total_trades >= min_trades:
                    progress = max(progress, min(1.0, self.stats.win_rate / reqs["win_rate"]))
                else:
                    progress = max(progress, self.stats.total_trades / min_trades * 0.5)
        
            return progress
        except Exception as e:
            logger.error(f"Error in _calculate_achievement_progress: {e}")
            raise
    
    def get_leaderboard_entry(self) -> Dict[str, Any]:
        """Get entry for leaderboard comparison.
        
        Returns:
            Dictionary with leaderboard data
        """
        return {
            'level': self.level,
            'total_points': self.total_points,
            'win_rate': self.stats.win_rate,
            'net_profit': self.stats.net_profit,
            'total_trades': self.stats.total_trades,
            'best_streak': self.stats.best_streak,
            'achievements_unlocked': len([a for a in self.achievements if a.unlocked]),
            'profit_factor': self.stats.profit_factor
        }
