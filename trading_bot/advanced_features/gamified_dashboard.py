import logging
logger = logging.getLogger(__name__)
"""Gamified Trading Dashboard System.

Advanced performance tracking with gamification elements including:
- XP points and level system
- Achievement badges
- Win streaks and combo multipliers
- Performance scoring
- Leaderboards and challenges
"""

import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
import sqlite3
from pathlib import Path
from loguru import logger
import json
import asyncio
import numpy
import pandas

# Evolution: Added retry decorator
def retry(max_attempts=3, delay=1.0):
    """Retry decorator for resilient operations"""
    def decorator(func):
        """
        decorator function.

    Args:
        func: Description

    Returns:
        Result of operation
        """
        async def wrapper(*args, **kwargs):
            """
            wrapper function.

    Auto-documented by QwenCodeMender.
            """
            last_error = None
            for attempt in range(max_attempts):
                try:
                    return await func(*args, **kwargs)
                except Exception as e:
                    last_error = e
                    if attempt < max_attempts - 1:
                        await asyncio.sleep(delay * (attempt + 1))
            raise last_error
        return wrapper
    return decorator




class AchievementType(Enum):
    """Types of trading achievements."""
    WIN_STREAK = "win_streak"
    PROFIT_MILESTONE = "profit_milestone"
    RISK_MANAGEMENT = "risk_management"
    CONSISTENCY = "consistency"
    VOLUME_MILESTONE = "volume_milestone"
    ACCURACY_MILESTONE = "accuracy_milestone"
    DRAWDOWN_RECOVERY = "drawdown_recovery"
    STRATEGY_MASTERY = "strategy_mastery"


class BadgeLevel(Enum):
    """Badge achievement levels."""
    BRONZE = "bronze"
    SILVER = "silver"
    GOLD = "gold"
    PLATINUM = "platinum"
    DIAMOND = "diamond"


@dataclass
class Achievement:
    """Trading achievement badge."""
    id: str
    name: str
    description: str
    achievement_type: AchievementType
    badge_level: BadgeLevel
    xp_reward: int
    unlock_criteria: Dict[str, Any]
    unlocked: bool = False
    unlock_date: Optional[datetime] = None


@dataclass
class TradingStats:
    """Comprehensive trading statistics."""
    total_trades: int
    winning_trades: int
    losing_trades: int
    win_rate: float
    total_pnl: float
    max_drawdown: float
    sharpe_ratio: float
    profit_factor: float
    avg_win: float
    avg_loss: float
    current_streak: int
    max_win_streak: int
    max_loss_streak: int
    total_volume: float
    accuracy_score: float


@dataclass
class PlayerProfile:
    """Gamified player profile."""
    player_id: str
    username: str
    level: int
    total_xp: int
    current_xp: int
    xp_to_next_level: int
    rank: str
    achievements: List[Achievement]
    current_streak: int
    max_streak: int
    total_score: float
    trading_stats: TradingStats


class GamifiedDashboard:
    """Advanced gamified trading dashboard system."""
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize gamified dashboard.
        
        Args:
            config: Configuration dictionary
        """
        self.config = config
        self.db_path = Path(config.get('db_path', 'data/gamified_dashboard.db'))
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Gamification parameters
        self.base_xp_per_level = config.get('base_xp_per_level', 1000)
        self.xp_multiplier = config.get('xp_multiplier', 1.2)
        self.streak_bonus_multiplier = config.get('streak_bonus_multiplier', 0.1)
        
        # Player state
        self.current_player = None
        self.active_challenges = []
        
        # Initialize database
        self._init_database()
        
        # Initialize achievements
        self.achievements = self._create_achievements()
        
        logger.info("Gamified Dashboard initialized")
    
    def _init_database(self):
        """Initialize SQLite database for dashboard data."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute('''
                CREATE TABLE IF NOT EXISTS player_profiles (
                    player_id TEXT PRIMARY KEY,
                    username TEXT NOT NULL,
                    level INTEGER NOT NULL DEFAULT 1,
                    total_xp INTEGER NOT NULL DEFAULT 0,
                    current_xp INTEGER NOT NULL DEFAULT 0,
                    rank TEXT NOT NULL DEFAULT 'Novice',
                    current_streak INTEGER NOT NULL DEFAULT 0,
                    max_streak INTEGER NOT NULL DEFAULT 0,
                    total_score REAL NOT NULL DEFAULT 0,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            conn.execute('''
                CREATE TABLE IF NOT EXISTS trading_sessions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    player_id TEXT NOT NULL,
                    session_date DATE NOT NULL,
                    trades_count INTEGER NOT NULL,
                    winning_trades INTEGER NOT NULL,
                    total_pnl REAL NOT NULL,
                    max_drawdown REAL NOT NULL,
                    xp_earned INTEGER NOT NULL,
                    score REAL NOT NULL,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (player_id) REFERENCES player_profiles (player_id)
                )
            ''')
            
            conn.execute('''
                CREATE TABLE IF NOT EXISTS achievements_unlocked (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    player_id TEXT NOT NULL,
                    achievement_id TEXT NOT NULL,
                    unlock_date DATETIME NOT NULL,
                    xp_reward INTEGER NOT NULL,
                    FOREIGN KEY (player_id) REFERENCES player_profiles (player_id)
                )
            ''')
            
            conn.execute('''
                CREATE TABLE IF NOT EXISTS leaderboard (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    player_id TEXT NOT NULL,
                    metric_type TEXT NOT NULL,
                    metric_value REAL NOT NULL,
                    rank_position INTEGER NOT NULL,
                    period TEXT NOT NULL,
                    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (player_id) REFERENCES player_profiles (player_id)
                )
            ''')
            
            conn.commit()
    
    def _create_achievements(self) -> List[Achievement]:
        """Create achievement definitions."""
        achievements = [
            # Win Streak Achievements
            Achievement(
                id="win_streak_5",
                name="Hot Streak",
                description="Win 5 trades in a row",
                achievement_type=AchievementType.WIN_STREAK,
                badge_level=BadgeLevel.BRONZE,
                xp_reward=100,
                unlock_criteria={"win_streak": 5}
            ),
            Achievement(
                id="win_streak_10",
                name="On Fire",
                description="Win 10 trades in a row",
                achievement_type=AchievementType.WIN_STREAK,
                badge_level=BadgeLevel.SILVER,
                xp_reward=250,
                unlock_criteria={"win_streak": 10}
            ),
            Achievement(
                id="win_streak_20",
                name="Unstoppable",
                description="Win 20 trades in a row",
                achievement_type=AchievementType.WIN_STREAK,
                badge_level=BadgeLevel.GOLD,
                xp_reward=500,
                unlock_criteria={"win_streak": 20}
            ),
            
            # Profit Milestones
            Achievement(
                id="profit_1000",
                name="First Thousand",
                description="Reach $1,000 in total profit",
                achievement_type=AchievementType.PROFIT_MILESTONE,
                badge_level=BadgeLevel.BRONZE,
                xp_reward=200,
                unlock_criteria={"total_profit": 1000}
            ),
            Achievement(
                id="profit_10000",
                name="Five Figures",
                description="Reach $10,000 in total profit",
                achievement_type=AchievementType.PROFIT_MILESTONE,
                badge_level=BadgeLevel.SILVER,
                xp_reward=500,
                unlock_criteria={"total_profit": 10000}
            ),
            Achievement(
                id="profit_100000",
                name="Six Figures",
                description="Reach $100,000 in total profit",
                achievement_type=AchievementType.PROFIT_MILESTONE,
                badge_level=BadgeLevel.GOLD,
                xp_reward=1000,
                unlock_criteria={"total_profit": 100000}
            ),
            
            # Risk Management
            Achievement(
                id="risk_master",
                name="Risk Master",
                description="Keep max drawdown under 5% for 100 trades",
                achievement_type=AchievementType.RISK_MANAGEMENT,
                badge_level=BadgeLevel.GOLD,
                xp_reward=750,
                unlock_criteria={"max_drawdown": 0.05, "trade_count": 100}
            ),
            
            # Accuracy
            Achievement(
                id="accuracy_80",
                name="Sharpshooter",
                description="Maintain 80% win rate over 50 trades",
                achievement_type=AchievementType.ACCURACY_MILESTONE,
                badge_level=BadgeLevel.SILVER,
                xp_reward=400,
                unlock_criteria={"win_rate": 0.8, "trade_count": 50}
            ),
            Achievement(
                id="accuracy_90",
                name="Sniper Elite",
                description="Maintain 90% win rate over 30 trades",
                achievement_type=AchievementType.ACCURACY_MILESTONE,
                badge_level=BadgeLevel.PLATINUM,
                xp_reward=800,
                unlock_criteria={"win_rate": 0.9, "trade_count": 30}
            ),
            
            # Volume Milestones
            Achievement(
                id="volume_1m",
                name="Million Dollar Trader",
                description="Trade $1,000,000 in total volume",
                achievement_type=AchievementType.VOLUME_MILESTONE,
                badge_level=BadgeLevel.SILVER,
                xp_reward=300,
                unlock_criteria={"total_volume": 1000000}
            ),
            
            # Consistency
            Achievement(
                id="consistent_30",
                name="Steady Eddie",
                description="30 consecutive profitable days",
                achievement_type=AchievementType.CONSISTENCY,
                badge_level=BadgeLevel.GOLD,
                xp_reward=600,
                unlock_criteria={"profitable_days_streak": 30}
            )
        ]
        
        return achievements
    
    async def create_player_profile(self, player_id: str, username: str) -> PlayerProfile:
        """Create new player profile.
        
        Args:
            player_id: Unique player identifier
            username: Player display name
            
        Returns:
            Created player profile
        """
        with sqlite3.connect(self.db_path) as conn:
            conn.execute('''
                INSERT OR REPLACE INTO player_profiles 
                (player_id, username, level, total_xp, current_xp, rank, 
                 current_streak, max_streak, total_score)
                VALUES (?, ?, 1, 0, 0, 'Novice', 0, 0, 0)
            ''', (player_id, username))
            conn.commit()
        
        # Create trading stats
        trading_stats = TradingStats(
            total_trades=0, winning_trades=0, losing_trades=0, win_rate=0.0,
            total_pnl=0.0, max_drawdown=0.0, sharpe_ratio=0.0, profit_factor=0.0,
            avg_win=0.0, avg_loss=0.0, current_streak=0, max_win_streak=0,
            max_loss_streak=0, total_volume=0.0, accuracy_score=0.0
        )
        
        profile = PlayerProfile(
            player_id=player_id,
            username=username,
            level=1,
            total_xp=0,
            current_xp=0,
            xp_to_next_level=self.base_xp_per_level,
            rank="Novice",
            achievements=[],
            current_streak=0,
            max_streak=0,
            total_score=0.0,
            trading_stats=trading_stats
        )
        
        self.current_player = profile
        logger.info(f"Created player profile: {username}")
        return profile
    
    async def record_trade_result(self, player_id: str, trade_result: Dict[str, Any]) -> Dict[str, Any]:
        """Record trade result and update player stats.
        
        Args:
            player_id: Player identifier
            trade_result: Trade outcome data
            
        Returns:
            Updated stats and rewards
        """
        try:
            # Load player profile
            profile = await self.get_player_profile(player_id)
            if not profile:
                logger.error(f"Player profile not found: {player_id}")
                return {}
            
            # Update trading stats
            is_win = trade_result.get('pnl', 0) > 0
            pnl = trade_result.get('pnl', 0)
            
            profile.trading_stats.total_trades += 1
            if is_win:
                profile.trading_stats.winning_trades += 1
                profile.current_streak += 1
                profile.max_streak = max(profile.max_streak, profile.current_streak)
            else:
                profile.trading_stats.losing_trades += 1
                profile.current_streak = 0
            
            profile.trading_stats.total_pnl += pnl
            profile.trading_stats.win_rate = (
                profile.trading_stats.winning_trades / profile.trading_stats.total_trades
            )
            
            # Calculate XP earned
            base_xp = 10  # Base XP per trade
            win_bonus = 20 if is_win else 0
            streak_bonus = int(profile.current_streak * self.streak_bonus_multiplier * base_xp)
            total_xp = base_xp + win_bonus + streak_bonus
            
            # Update XP and level
            profile.total_xp += total_xp
            profile.current_xp += total_xp
            
            # Check for level up
            level_ups = 0
            while profile.current_xp >= profile.xp_to_next_level:
                profile.current_xp -= profile.xp_to_next_level
                profile.level += 1
                level_ups += 1
                profile.xp_to_next_level = int(self.base_xp_per_level * (self.xp_multiplier ** profile.level))
            
            # Update rank
            profile.rank = self._calculate_rank(profile.level)
            
            # Check for achievements
            new_achievements = await self._check_achievements(profile)
            
            # Calculate session score
            session_score = self._calculate_session_score(trade_result, profile)
            profile.total_score += session_score
            
            # Save updated profile
            await self._save_player_profile(profile)
            
            # Record trading session
            await self._record_trading_session(player_id, trade_result, total_xp, session_score)
            
            result = {
                'xp_earned': total_xp,
                'level_ups': level_ups,
                'new_level': profile.level,
                'new_achievements': new_achievements,
                'current_streak': profile.current_streak,
                'session_score': session_score,
                'total_score': profile.total_score,
                'rank': profile.rank
            }
            
            logger.info(f"Trade recorded for {profile.username}: +{total_xp} XP, Level {profile.level}")
            return result
            
        except Exception as e:
            logger.error(f"Error recording trade result: {e}")
            return {}
    
    async def get_player_profile(self, player_id: str) -> Optional[PlayerProfile]:
        """Get player profile by ID.
        
        Args:
            player_id: Player identifier
            
        Returns:
            Player profile or None
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute('''
                    SELECT player_id, username, level, total_xp, current_xp, rank,
                           current_streak, max_streak, total_score
                    FROM player_profiles WHERE player_id = ?
                ''', (player_id,))
                
                row = cursor.fetchone()
                if not row:
                    return None
                
                # Get trading stats (mock for now)
                trading_stats = TradingStats(
                    total_trades=100, winning_trades=65, losing_trades=35, win_rate=0.65,
                    total_pnl=5000.0, max_drawdown=0.08, sharpe_ratio=1.5, profit_factor=1.8,
                    avg_win=150.0, avg_loss=-80.0, current_streak=row[6], max_win_streak=row[7],
                    max_loss_streak=5, total_volume=500000.0, accuracy_score=0.75
                )
                
                # Get achievements
                achievements = await self._get_player_achievements(player_id)
                
                profile = PlayerProfile(
                    player_id=row[0],
                    username=row[1],
                    level=row[2],
                    total_xp=row[3],
                    current_xp=row[4],
                    xp_to_next_level=int(self.base_xp_per_level * (self.xp_multiplier ** row[2])),
                    rank=row[5],
                    achievements=achievements,
                    current_streak=row[6],
                    max_streak=row[7],
                    total_score=row[8],
                    trading_stats=trading_stats
                )
                
                return profile
                
        except Exception as e:
            logger.error(f"Error getting player profile: {e}")
            return None
    
    async def get_leaderboard(self, metric: str = 'total_score', period: str = 'all_time', 
                            limit: int = 10) -> List[Dict[str, Any]]:
        """Get leaderboard rankings.
        
        Args:
            metric: Metric to rank by ('total_score', 'total_xp', 'win_rate', etc.)
            period: Time period ('daily', 'weekly', 'monthly', 'all_time')
            limit: Number of top players to return
            
        Returns:
            List of top players
        """
        try:
            # Mock leaderboard data
            leaderboard = []
            
            for i in range(min(limit, 10)):
                leaderboard.append({
                    'rank': i + 1,
                    'username': f"Player_{i+1}",
                    'level': np.random.randint(5, 50),
                    'total_score': np.random.uniform(1000, 50000),
                    'win_rate': np.random.uniform(0.5, 0.9),
                    'total_trades': np.random.randint(50, 1000),
                    'achievements_count': np.random.randint(3, 15)
                })
            
            # Sort by metric
            if metric in ['total_score', 'win_rate', 'total_trades']:
                leaderboard.sort(key=lambda x: x[metric], reverse=True)
            
            return leaderboard
            
        except Exception as e:
            logger.error(f"Error getting leaderboard: {e}")
            return []
    
    async def get_dashboard_data(self, player_id: str) -> Dict[str, Any]:
        """Get comprehensive dashboard data.
        
        Args:
            player_id: Player identifier
            
        Returns:
            Dashboard data
        """
        try:
            profile = await self.get_player_profile(player_id)
            if not profile:
                return {}
            
            # Get recent performance
            recent_sessions = await self._get_recent_sessions(player_id, days=30)
            
            # Calculate performance metrics
            daily_pnl = [session.get('total_pnl', 0) for session in recent_sessions]
            daily_scores = [session.get('score', 0) for session in recent_sessions]
            
            dashboard_data = {
                'player_profile': {
                    'username': profile.username,
                    'level': profile.level,
                    'rank': profile.rank,
                    'total_xp': profile.total_xp,
                    'current_xp': profile.current_xp,
                    'xp_to_next_level': profile.xp_to_next_level,
                    'progress_percentage': (profile.current_xp / profile.xp_to_next_level) * 100
                },
                'trading_stats': {
                    'total_trades': profile.trading_stats.total_trades,
                    'win_rate': profile.trading_stats.win_rate,
                    'total_pnl': profile.trading_stats.total_pnl,
                    'current_streak': profile.current_streak,
                    'max_streak': profile.max_streak,
                    'sharpe_ratio': profile.trading_stats.sharpe_ratio,
                    'max_drawdown': profile.trading_stats.max_drawdown
                },
                'achievements': {
                    'unlocked': len(profile.achievements),
                    'total_available': len(self.achievements),
                    'recent_unlocks': [a for a in profile.achievements if a.unlocked][-3:],
                    'next_targets': self._get_next_achievement_targets(profile)
                },
                'performance_charts': {
                    'daily_pnl': daily_pnl,
                    'daily_scores': daily_scores,
                    'equity_curve': self._generate_equity_curve(daily_pnl)
                },
                'leaderboard_position': await self._get_player_rank(player_id),
                'challenges': await self._get_active_challenges(player_id)
            }
            
            return dashboard_data
            
        except Exception as e:
            logger.error(f"Error getting dashboard data: {e}")
            return {}
    
    def _calculate_rank(self, level: int) -> str:
        """Calculate player rank based on level."""
        if level < 5:
            return "Novice"
        elif level < 10:
            return "Apprentice"
        elif level < 20:
            return "Trader"
        elif level < 35:
            return "Expert"
        elif level < 50:
            return "Master"
        else:
            return "Grandmaster"
    
    async def _check_achievements(self, profile: PlayerProfile) -> List[Achievement]:
        """Check for newly unlocked achievements."""
        new_achievements = []
        
        for achievement in self.achievements:
            if achievement.unlocked:
                continue
            
            # Check unlock criteria
            criteria_met = True
            for criterion, required_value in achievement.unlock_criteria.items():
                
                if criterion == "win_streak":
                    if profile.current_streak < required_value:
                        criteria_met = False
                        break
                elif criterion == "total_profit":
                    if profile.trading_stats.total_pnl < required_value:
                        criteria_met = False
                        break
                elif criterion == "win_rate":
                    if (profile.trading_stats.win_rate < required_value or 
                        profile.trading_stats.total_trades < achievement.unlock_criteria.get("trade_count", 1)):
                        criteria_met = False
                        break
                elif criterion == "total_volume":
                    if profile.trading_stats.total_volume < required_value:
                        criteria_met = False
                        break
            
            if criteria_met:
                achievement.unlocked = True
                achievement.unlock_date = datetime.now()
                profile.total_xp += achievement.xp_reward
                profile.achievements.append(achievement)
                new_achievements.append(achievement)
                
                # Store achievement unlock
                await self._store_achievement_unlock(profile.player_id, achievement)
        
        return new_achievements
    
    def _calculate_session_score(self, trade_result: Dict[str, Any], profile: PlayerProfile) -> float:
        """Calculate session performance score."""
        base_score = 10
        
        # PnL component
        pnl = trade_result.get('pnl', 0)
        pnl_score = max(0, pnl / 100)  # 1 point per $100 profit
        
        # Risk management component
        risk_score = 0
        if trade_result.get('max_drawdown', 0) < 0.02:  # Less than 2% drawdown
            risk_score = 5
        
        # Streak bonus
        streak_bonus = min(20, profile.current_streak * 2)
        
        total_score = base_score + pnl_score + risk_score + streak_bonus
        return round(total_score, 2)
    
    async def _save_player_profile(self, profile: PlayerProfile):
        """Save player profile to database."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute('''
                UPDATE player_profiles 
                SET level = ?, total_xp = ?, current_xp = ?, rank = ?,
                    current_streak = ?, max_streak = ?, total_score = ?,
                    updated_at = CURRENT_TIMESTAMP
                WHERE player_id = ?
            ''', (
                profile.level, profile.total_xp, profile.current_xp, profile.rank,
                profile.current_streak, profile.max_streak, profile.total_score,
                profile.player_id
            ))
            conn.commit()
    
    async def _record_trading_session(self, player_id: str, trade_result: Dict[str, Any], 
                                    xp_earned: int, score: float):
        """Record trading session data."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute('''
                INSERT INTO trading_sessions 
                (player_id, session_date, trades_count, winning_trades, 
                 total_pnl, max_drawdown, xp_earned, score)
                VALUES (?, ?, 1, ?, ?, ?, ?, ?)
            ''', (
                player_id, datetime.now().date(),
                1 if trade_result.get('pnl', 0) > 0 else 0,
                trade_result.get('pnl', 0),
                trade_result.get('max_drawdown', 0),
                xp_earned, score
            ))
            conn.commit()
    
    async def _get_player_achievements(self, player_id: str) -> List[Achievement]:
        """Get player's unlocked achievements."""
        # Mock implementation - return empty list for now
        return []
    
    async def _get_recent_sessions(self, player_id: str, days: int = 30) -> List[Dict[str, Any]]:
        """Get recent trading sessions."""
        # Mock implementation
        sessions = []
        for i in range(days):
            sessions.append({
                'date': datetime.now() - timedelta(days=i),
                'total_pnl': np.random.uniform(-200, 500),
                'score': np.random.uniform(10, 100),
                'trades_count': np.random.randint(1, 10)
            })
        return sessions
    
    def _generate_equity_curve(self, daily_pnl: List[float]) -> List[float]:
        """Generate cumulative equity curve."""
        if not daily_pnl:
            return []
        
        equity_curve = []
        cumulative = 10000  # Starting balance
        
        for pnl in daily_pnl:
            cumulative += pnl
            equity_curve.append(cumulative)
        
        return equity_curve
    
    def _get_next_achievement_targets(self, profile: PlayerProfile) -> List[Dict[str, Any]]:
        """Get next achievement targets for player."""
        targets = []
        
        for achievement in self.achievements:
            if not achievement.unlocked:
                progress = self._calculate_achievement_progress(achievement, profile)
                targets.append({
                    'name': achievement.name,
                    'description': achievement.description,
                    'progress': progress,
                    'xp_reward': achievement.xp_reward,
                    'badge_level': achievement.badge_level.value
                })
        
        # Sort by progress (closest to completion first)
        targets.sort(key=lambda x: x['progress'], reverse=True)
        return targets[:5]  # Return top 5 closest achievements
    
    def _calculate_achievement_progress(self, achievement: Achievement, profile: PlayerProfile) -> float:
        """Calculate progress towards achievement."""
        # Mock progress calculation
        return np.random.uniform(0.1, 0.9)
    
    async def _get_player_rank(self, player_id: str) -> Dict[str, Any]:
        """Get player's leaderboard position."""
        return {
            'overall_rank': np.random.randint(1, 100),
            'total_players': 1000,
            'percentile': np.random.uniform(0.8, 0.99)
        }
    
    async def _get_active_challenges(self, player_id: str) -> List[Dict[str, Any]]:
        """Get active challenges for player."""
        return [
            {
                'name': "Weekly Profit Challenge",
                'description': "Earn $1,000 profit this week",
                'progress': 0.6,
                'reward': "500 XP + Gold Badge",
                'expires': datetime.now() + timedelta(days=3)
            },
            {
                'name': "Consistency Challenge",
                'description': "5 profitable days in a row",
                'progress': 0.4,
                'reward': "300 XP + Achievement",
                'expires': datetime.now() + timedelta(days=7)
            }
        ]
    
    async def _store_achievement_unlock(self, player_id: str, achievement: Achievement):
        """Store achievement unlock in database."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute('''
                INSERT INTO achievements_unlocked 
                (player_id, achievement_id, unlock_date, xp_reward)
                VALUES (?, ?, ?, ?)
            ''', (
                player_id, achievement.id, achievement.unlock_date, achievement.xp_reward
            ))
            conn.commit()
