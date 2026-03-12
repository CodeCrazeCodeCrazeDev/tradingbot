"""
Profit Maximizer Core System - Part 1
=====================================
If I were this trading bot, here's EXACTLY how I would maximize profits.
"""

import numpy as np
import pandas as pd
from typing import Any, Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import logging
import math
from collections import deque

logger = logging.getLogger(__name__)


class ConfluenceLevel(Enum):
    WEAK = 1
    MODERATE = 2
    STRONG = 3
    VERY_STRONG = 4


class EntryQuality(Enum):
    POOR = 1
    FAIR = 2
    GOOD = 3
    EXCELLENT = 4


class SessionQuality(Enum):
    DEAD = 0
    LOW = 1
    NORMAL = 2
    HIGH = 3
    PEAK = 4


class RecoveryMode(Enum):
    NORMAL = 0
    CAUTIOUS = 1
    DEFENSIVE = 2
    MINIMAL = 3
    STOPPED = 4


class StreakMode(Enum):
    COLD = 0
    NORMAL = 1
    WARM = 2
    HOT = 3
    ON_FIRE = 4


@dataclass
class ConfluenceSignal:
    direction: str
    base_confidence: float
    confluence_score: int
    confluence_level: ConfluenceLevel
    confirmations: List[str]
    conflicts: List[str]
    adjusted_confidence: float = 0.0
    should_trade: bool = False
    recommended_size_multiplier: float = 1.0


@dataclass
class EntryTiming:
    current_price: float
    ideal_entry: float
    entry_quality: EntryQuality
    pullback_percent: float
    wait_for_pullback: bool
    max_wait_bars: int
    entry_zone_low: float
    entry_zone_high: float
    should_enter_now: bool = False
    reason: str = ""


@dataclass
class ProfitTarget:
    entry_price: float
    stop_loss: float
    take_profit_1: float
    take_profit_2: float
    take_profit_3: float
    trailing_start: float
    trailing_distance: float
    risk_reward_ratio: float
    volatility_adjusted: bool = True
    momentum_extended: bool = False


@dataclass
class SessionQualityResult:
    current_session: str
    session_quality: SessionQuality
    hours_until_better_session: float
    volatility_percentile: float
    spread_percentile: float
    should_trade: bool = True
    size_multiplier: float = 1.0
    reason: str = ""


@dataclass
class RecoveryState:
    consecutive_losses: int
    daily_loss_percent: float
    recovery_mode: RecoveryMode
    size_multiplier: float
    trades_until_reset: int
    should_trade: bool = True
    reason: str = ""


@dataclass
class StreakState:
    consecutive_wins: int
    consecutive_losses: int
    streak_mode: StreakMode
    size_multiplier: float
    recent_win_rate: float
    should_increase_size: bool = False


@dataclass
class TradeDecision:
    should_trade: bool
    direction: str
    entry_price: float
    stop_loss: float
    take_profit: float
    position_size_multiplier: float
    confidence: float
    confluence_score: int
    entry_quality: EntryQuality
    session_quality: SessionQuality
    recovery_mode: RecoveryMode
    streak_mode: StreakMode
    reasons_to_trade: List[str]
    reasons_not_to_trade: List[str]
    profit_targets: ProfitTarget = None
    timestamp: datetime = field(default_factory=datetime.now)


class SignalConfluenceScorer:
    """Require MULTIPLE confirmations before trading"""
    
    def __init__(self, min_confluence: int = 4):
        try:
            self.min_confluence = min_confluence
            logger.info(f"Signal Confluence Scorer initialized (min: {min_confluence})")
        except Exception as e:
            logger.error(f"Error in __init__: {e}")
            raise
    
    def score_signal(self, direction: str, market_data: pd.DataFrame,
                     base_confidence: float, additional_data: Optional[Dict] = None) -> ConfluenceSignal:
        try:
            confirmations = []
            conflicts = []
            additional_data = additional_data or {}
        
            # Check trend alignment
            trend = self._check_trend(direction, market_data)
            if trend['aligned']:
                confirmations.append(f"Trend: {trend['reason']}")
            else:
                conflicts.append(f"Trend: {trend['reason']}")
        
            # Check momentum
            momentum = self._check_momentum(direction, market_data)
            if momentum['confirmed']:
                confirmations.append(f"Momentum: {momentum['reason']}")
            else:
                conflicts.append(f"Momentum: {momentum['reason']}")
        
            # Check volume
            volume = self._check_volume(market_data)
            if volume['confirmed']:
                confirmations.append(f"Volume: {volume['reason']}")
            else:
                conflicts.append(f"Volume: {volume['reason']}")
        
            # Check S/R
            sr = self._check_sr(direction, market_data)
            if sr['favorable']:
                confirmations.append(f"S/R: {sr['reason']}")
            else:
                conflicts.append(f"S/R: {sr['reason']}")
        
            # Check volatility
            vol = self._check_volatility(market_data)
            if vol['favorable']:
                confirmations.append(f"Volatility: {vol['reason']}")
            else:
                conflicts.append(f"Volatility: {vol['reason']}")
        
            # HTF check if available
            htf_data = additional_data.get('htf_data')
            if htf_data is not None:
                htf = self._check_htf(direction, htf_data)
                if htf['aligned']:
                    confirmations.append(f"HTF: {htf['reason']}")
                else:
                    conflicts.append(f"HTF: {htf['reason']}")
        
            confluence_score = len(confirmations)
        
            if confluence_score >= 7:
                level = ConfluenceLevel.VERY_STRONG
                size_mult = 1.25
            elif confluence_score >= 5:
                level = ConfluenceLevel.STRONG
                size_mult = 1.0
            elif confluence_score >= 3:
                level = ConfluenceLevel.MODERATE
                size_mult = 0.75
            else:
                level = ConfluenceLevel.WEAK
                size_mult = 0.5
        
            adjusted_confidence = min(0.95, max(0.1,
                base_confidence + (confluence_score - self.min_confluence) * 0.03 - len(conflicts) * 0.05))
        
            should_trade = (confluence_score >= self.min_confluence and 
                           len(conflicts) <= 2 and adjusted_confidence >= 0.5)
        
            return ConfluenceSignal(
                direction=direction, base_confidence=base_confidence,
                confluence_score=confluence_score, confluence_level=level,
                confirmations=confirmations, conflicts=conflicts,
                adjusted_confidence=adjusted_confidence, should_trade=should_trade,
                recommended_size_multiplier=size_mult if should_trade else 0.0
            )
        except Exception as e:
            logger.error(f"Error in score_signal: {e}")
            raise
    
    def _ema(self, data: np.ndarray, period: int) -> np.ndarray:
        try:
            alpha = 2 / (period + 1)
            ema = np.zeros_like(data, dtype=float)
            ema[0] = data[0]
            for i in range(1, len(data)):
                ema[i] = alpha * data[i] + (1 - alpha) * ema[i-1]
            return ema
        except Exception as e:
            logger.error(f"Error in _ema: {e}")
            raise
    
    def _check_trend(self, direction: str, data: pd.DataFrame) -> Dict:
        try:
            close = data['close'].values
            ema_20 = self._ema(close, 20)
            ema_50 = self._ema(close, 50)
        
            if direction == 'BUY':
                aligned = close[-1] > ema_20[-1] > ema_50[-1]
                reason = "Uptrend" if aligned else "Not in uptrend"
            else:
                aligned = close[-1] < ema_20[-1] < ema_50[-1]
                reason = "Downtrend" if aligned else "Not in downtrend"
            return {'aligned': aligned, 'reason': reason}
        except Exception as e:
            logger.error(f"Error in _check_trend: {e}")
            raise
    
    def _check_momentum(self, direction: str, data: pd.DataFrame) -> Dict:
        try:
            close = data['close'].values
            deltas = np.diff(close)
            gains = np.where(deltas > 0, deltas, 0)
            losses = np.where(deltas < 0, -deltas, 0)
            avg_gain = np.mean(gains[-14:])
            avg_loss = np.mean(losses[-14:])
            rsi = 100 - (100 / (1 + avg_gain / avg_loss)) if avg_loss > 0 else 100
        
            if direction == 'BUY':
                confirmed = 30 < rsi < 70
                reason = f"RSI={rsi:.0f} OK" if confirmed else f"RSI={rsi:.0f} extreme"
            else:
                confirmed = 30 < rsi < 70
                reason = f"RSI={rsi:.0f} OK" if confirmed else f"RSI={rsi:.0f} extreme"
            return {'confirmed': confirmed, 'reason': reason}
        except Exception as e:
            logger.error(f"Error in _check_momentum: {e}")
            raise
    
    def _check_volume(self, data: pd.DataFrame) -> Dict:
        try:
            if 'volume' not in data.columns:
                return {'confirmed': True, 'reason': 'No volume data'}
            volume = data['volume'].values
            avg_vol = np.mean(volume[-20:])
            ratio = volume[-1] / avg_vol if avg_vol > 0 else 1.0
            confirmed = ratio > 0.8
            return {'confirmed': confirmed, 'reason': f"Vol {ratio:.1f}x avg"}
        except Exception as e:
            logger.error(f"Error in _check_volume: {e}")
            raise
    
    def _check_sr(self, direction: str, data: pd.DataFrame) -> Dict:
        try:
            high = data['high'].values
            low = data['low'].values
            close = data['close'].values[-1]
            recent_high = np.max(high[-20:])
            recent_low = np.min(low[-20:])
            range_size = recent_high - recent_low
        
            if direction == 'BUY':
                dist = (close - recent_low) / range_size if range_size > 0 else 0.5
                favorable = dist < 0.4
                reason = f"{dist:.0%} from support" if favorable else "Far from support"
            else:
                dist = (recent_high - close) / range_size if range_size > 0 else 0.5
                favorable = dist < 0.4
                reason = f"{dist:.0%} from resistance" if favorable else "Far from resistance"
            return {'favorable': favorable, 'reason': reason}
        except Exception as e:
            logger.error(f"Error in _check_sr: {e}")
            raise
    
    def _check_volatility(self, data: pd.DataFrame) -> Dict:
        try:
            close = data['close'].values
            returns = np.diff(close) / close[:-1]
            current_vol = np.std(returns[-20:])
            hist_vol = np.std(returns) if len(returns) > 20 else current_vol
            ratio = current_vol / hist_vol if hist_vol > 0 else 1.0
            favorable = 0.5 < ratio < 2.0
            return {'favorable': favorable, 'reason': f"Vol ratio {ratio:.1f}x"}
        except Exception as e:
            logger.error(f"Error in _check_volatility: {e}")
            raise
    
    def _check_htf(self, direction: str, htf_data: pd.DataFrame) -> Dict:
        try:
            close = htf_data['close'].values
            ema_20 = self._ema(close, 20)
            if direction == 'BUY':
                aligned = close[-1] > ema_20[-1]
            else:
                aligned = close[-1] < ema_20[-1]
            return {'aligned': aligned, 'reason': "HTF aligned" if aligned else "HTF conflict"}
        except Exception as e:
            logger.error(f"Error in _check_htf: {e}")
            raise


class SmartEntryTimer:
    """Wait for PULLBACKS instead of chasing price"""
    
    def __init__(self, pullback_percent: float = 0.3, max_wait_bars: int = 5):
        try:
            self.pullback_percent = pullback_percent
            self.max_wait_bars = max_wait_bars
            logger.info(f"Smart Entry Timer initialized")
        except Exception as e:
            logger.error(f"Error in __init__: {e}")
            raise
    
    def calculate_entry(self, direction: str, market_data: pd.DataFrame,
                       signal_price: float) -> EntryTiming:
        try:
            close = market_data['close'].values
            high = market_data['high'].values
            low = market_data['low'].values
        
            current_price = close[-1]
            recent_high = np.max(high[-10:])
            recent_low = np.min(low[-10:])
            recent_range = recent_high - recent_low
        
            # Calculate ATR
            tr = np.maximum(high[1:] - low[1:], np.maximum(
                np.abs(high[1:] - close[:-1]), np.abs(low[1:] - close[:-1])))
            atr = np.mean(tr[-14:])
        
            if direction == 'BUY':
                ideal_entry = current_price - (recent_range * self.pullback_percent)
                entry_zone_low = ideal_entry - atr * 0.5
                entry_zone_high = ideal_entry + atr * 0.5
                pullback = (recent_high - current_price) / recent_range if recent_range > 0 else 0
            
                if pullback >= self.pullback_percent:
                    quality = EntryQuality.GOOD
                    should_enter = True
                    reason = f"Good pullback ({pullback:.0%})"
                elif current_price <= entry_zone_high:
                    quality = EntryQuality.EXCELLENT
                    should_enter = True
                    reason = "In entry zone"
                else:
                    quality = EntryQuality.POOR
                    should_enter = False
                    reason = f"Wait for pullback to {ideal_entry:.5f}"
            else:
                ideal_entry = current_price + (recent_range * self.pullback_percent)
                entry_zone_low = ideal_entry - atr * 0.5
                entry_zone_high = ideal_entry + atr * 0.5
                pullback = (current_price - recent_low) / recent_range if recent_range > 0 else 0
            
                if pullback >= self.pullback_percent:
                    quality = EntryQuality.GOOD
                    should_enter = True
                    reason = f"Good pullback ({pullback:.0%})"
                elif current_price >= entry_zone_low:
                    quality = EntryQuality.EXCELLENT
                    should_enter = True
                    reason = "In entry zone"
                else:
                    quality = EntryQuality.POOR
                    should_enter = False
                    reason = f"Wait for pullback to {ideal_entry:.5f}"
        
            return EntryTiming(
                current_price=current_price, ideal_entry=ideal_entry,
                entry_quality=quality, pullback_percent=pullback,
                wait_for_pullback=not should_enter, max_wait_bars=self.max_wait_bars,
                entry_zone_low=entry_zone_low, entry_zone_high=entry_zone_high,
                should_enter_now=should_enter, reason=reason
            )
        except Exception as e:
            logger.error(f"Error in calculate_entry: {e}")
            raise


class DynamicProfitTargets:
    """Dynamic R:R based on market conditions"""
    
    def __init__(self, base_rr: float = 2.0, min_rr: float = 1.5, max_rr: float = 5.0):
        try:
            self.base_rr = base_rr
            self.min_rr = min_rr
            self.max_rr = max_rr
            logger.info(f"Dynamic Profit Targets initialized")
        except Exception as e:
            logger.error(f"Error in __init__: {e}")
            raise
    
    def calculate_targets(self, direction: str, entry_price: float,
                         stop_loss: float, market_data: pd.DataFrame,
                         market_regime: Optional[str] = None) -> ProfitTarget:
        try:
            risk = abs(entry_price - stop_loss)
        
            # Volatility multiplier
            close = market_data['close'].values
            returns = np.diff(close) / close[:-1]
            current_vol = np.std(returns[-20:])
            hist_vol = np.std(returns) if len(returns) > 20 else current_vol
            vol_ratio = current_vol / hist_vol if hist_vol > 0 else 1.0
            vol_mult = 1.3 if vol_ratio > 1.5 else (0.85 if vol_ratio < 0.7 else 1.0)
        
            # Regime multiplier
            if market_regime == 'TRENDING':
                regime_mult = 1.5
            elif market_regime == 'RANGING':
                regime_mult = 0.75
            else:
                regime_mult = 1.0
        
            adjusted_rr = max(self.min_rr, min(self.max_rr, self.base_rr * vol_mult * regime_mult))
        
            if direction == 'BUY':
                tp1 = entry_price + risk * 1.0
                tp2 = entry_price + risk * adjusted_rr * 0.7
                tp3 = entry_price + risk * adjusted_rr
                trailing_start = entry_price + risk * 1.5
            else:
                tp1 = entry_price - risk * 1.0
                tp2 = entry_price - risk * adjusted_rr * 0.7
                tp3 = entry_price - risk * adjusted_rr
                trailing_start = entry_price - risk * 1.5
        
            return ProfitTarget(
                entry_price=entry_price, stop_loss=stop_loss,
                take_profit_1=tp1, take_profit_2=tp2, take_profit_3=tp3,
                trailing_start=trailing_start, trailing_distance=risk * 0.5,
                risk_reward_ratio=adjusted_rr
            )
        except Exception as e:
            logger.error(f"Error in calculate_targets: {e}")
            raise


class SessionFilter:
    """Trade only during HIGH-PROBABILITY sessions"""
    
    def __init__(self, timezone_offset: int = 0):
        try:
            self.timezone_offset = timezone_offset
            self.dead_hours = [(22, 24), (0, 2), (5, 7), (11, 12), (17, 18)]
            logger.info("Session Filter initialized")
        except Exception as e:
            logger.error(f"Error in __init__: {e}")
            raise
    
    def assess_session(self, current_time: Optional[datetime] = None,
                       market_data: Optional[pd.DataFrame] = None) -> SessionQualityResult:
        try:
            if current_time is None:
                current_time = datetime.utcnow()
        
            hour = (current_time.hour + self.timezone_offset) % 24
        
            # Check dead hours
            in_dead = any(start <= hour < end for start, end in self.dead_hours)
        
            # Determine session
            if 13 <= hour < 16:
                session = 'OVERLAP'
                quality = SessionQuality.PEAK
                size_mult = 1.25
                reason = "London/NY overlap - best time"
            elif 8 <= hour < 16:
                session = 'LONDON'
                quality = SessionQuality.HIGH
                size_mult = 1.0
                reason = "London session"
            elif 13 <= hour < 21:
                session = 'NY'
                quality = SessionQuality.HIGH
                size_mult = 1.0
                reason = "NY session"
            else:
                session = 'ASIAN'
                quality = SessionQuality.LOW
                size_mult = 0.75
                reason = "Asian session - reduced size"
        
            if in_dead:
                quality = SessionQuality.DEAD
                size_mult = 0.0
                reason = "Dead trading hours"
        
            return SessionQualityResult(
                current_session=session, session_quality=quality,
                hours_until_better_session=0, volatility_percentile=50,
                spread_percentile=50, should_trade=not in_dead,
                size_multiplier=size_mult, reason=reason
            )
        except Exception as e:
            logger.error(f"Error in assess_session: {e}")
            raise


class LossRecoveryMode:
    """Strategic position sizing after losses"""
    
    def __init__(self, max_daily_loss_percent: float = 5.0):
        try:
            self.max_daily_loss = max_daily_loss_percent
            self.loss_steps = [1.0, 0.75, 0.5, 0.25, 0.0]
            self.consecutive_losses = 0
            self.daily_loss_percent = 0.0
            self.last_reset = datetime.now().date()
            logger.info(f"Loss Recovery Mode initialized")
        except Exception as e:
            logger.error(f"Error in __init__: {e}")
            raise
    
    def update_state(self, trade_result: Dict) -> RecoveryState:
        try:
            if datetime.now().date() != self.last_reset:
                self.daily_loss_percent = 0.0
                self.last_reset = datetime.now().date()
        
            pnl = trade_result.get('pnl_percent', 0)
            is_win = trade_result.get('is_win', pnl > 0)
        
            self.daily_loss_percent += min(0, pnl)
        
            if is_win:
                self.consecutive_losses = max(0, self.consecutive_losses - 1)
            else:
                self.consecutive_losses += 1
        
            return self.get_current_state()
        except Exception as e:
            logger.error(f"Error in update_state: {e}")
            raise
    
    def get_current_state(self) -> RecoveryState:
        try:
            if abs(self.daily_loss_percent) >= self.max_daily_loss:
                mode = RecoveryMode.STOPPED
                size_mult = 0.0
                should_trade = False
                reason = f"Daily loss limit ({self.daily_loss_percent:.1f}%)"
            elif self.consecutive_losses >= 5:
                mode = RecoveryMode.MINIMAL
                size_mult = 0.25
                should_trade = True
                reason = f"{self.consecutive_losses} losses - minimal"
            elif self.consecutive_losses >= 3:
                mode = RecoveryMode.DEFENSIVE
                size_mult = 0.5
                should_trade = True
                reason = f"{self.consecutive_losses} losses - defensive"
            elif self.consecutive_losses >= 1:
                mode = RecoveryMode.CAUTIOUS
                size_mult = 0.75
                should_trade = True
                reason = f"{self.consecutive_losses} losses - cautious"
            else:
                mode = RecoveryMode.NORMAL
                size_mult = 1.0
                should_trade = True
                reason = "Normal trading"
        
            return RecoveryState(
                consecutive_losses=self.consecutive_losses,
                daily_loss_percent=self.daily_loss_percent,
                recovery_mode=mode, size_multiplier=size_mult,
                trades_until_reset=self.consecutive_losses * 2,
                should_trade=should_trade, reason=reason
            )
        except Exception as e:
            logger.error(f"Error in get_current_state: {e}")
            raise


class WinStreakOptimizer:
    """Capitalize on winning streaks"""
    
    def __init__(self, max_size_increase: float = 1.5):
        try:
            self.max_size_increase = max_size_increase
            self.consecutive_wins = 0
            self.consecutive_losses = 0
            self.recent_trades: deque = deque(maxlen=10)
            logger.info(f"Win Streak Optimizer initialized")
        except Exception as e:
            logger.error(f"Error in __init__: {e}")
            raise
    
    def update_state(self, trade_result: Dict) -> StreakState:
        try:
            is_win = trade_result.get('is_win', trade_result.get('pnl_percent', 0) > 0)
            self.recent_trades.append(trade_result)
        
            if is_win:
                self.consecutive_wins += 1
                self.consecutive_losses = 0
            else:
                self.consecutive_losses += 1
                self.consecutive_wins = 0
        
            return self.get_current_state()
        except Exception as e:
            logger.error(f"Error in update_state: {e}")
            raise
    
    def get_current_state(self) -> StreakState:
        try:
            win_rate = sum(1 for t in self.recent_trades 
                          if t.get('is_win', t.get('pnl_percent', 0) > 0)) / max(1, len(self.recent_trades))
        
            if self.consecutive_losses >= 3:
                mode = StreakMode.COLD
                size_mult = 0.75
            elif self.consecutive_wins >= 6:
                mode = StreakMode.ON_FIRE
                size_mult = min(self.max_size_increase, 1.4)
            elif self.consecutive_wins >= 4:
                mode = StreakMode.HOT
                size_mult = 1.25
            elif self.consecutive_wins >= 2:
                mode = StreakMode.WARM
                size_mult = 1.1
            else:
                mode = StreakMode.NORMAL
                size_mult = 1.0
        
            return StreakState(
                consecutive_wins=self.consecutive_wins,
                consecutive_losses=self.consecutive_losses,
                streak_mode=mode, size_multiplier=size_mult,
                recent_win_rate=win_rate,
                should_increase_size=mode in [StreakMode.WARM, StreakMode.HOT, StreakMode.ON_FIRE]
            )
        except Exception as e:
            logger.error(f"Error in get_current_state: {e}")
            raise


class ProfitMaximizerSystem:
    """Master Profit Maximizer - integrates all 6 components"""
    
    def __init__(self, config: Optional[Dict] = None):
        try:
            config = config or {}
        
            self.confluence_scorer = SignalConfluenceScorer(config.get('min_confluence', 4))
            self.entry_timer = SmartEntryTimer(config.get('pullback_percent', 0.3))
            self.profit_targets = DynamicProfitTargets(config.get('base_rr', 2.0))
            self.session_filter = SessionFilter(config.get('timezone_offset', 0))
            self.loss_recovery = LossRecoveryMode(config.get('max_daily_loss', 5.0))
            self.streak_optimizer = WinStreakOptimizer(config.get('max_size_increase', 1.5))
        
            self.stats = {'signals_received': 0, 'signals_passed': 0, 'signals_rejected': 0}
            logger.info("[OK] Profit Maximizer System initialized")
        except Exception as e:
            logger.error(f"Error in __init__: {e}")
            raise
    
    def evaluate_signal(self, direction: str, entry_price: float, stop_loss: float,
                       base_confidence: float, market_data: pd.DataFrame,
                       additional_data: Optional[Dict] = None) -> TradeDecision:
        try:
            self.stats['signals_received'] += 1
            reasons_to_trade = []
            reasons_not_to_trade = []
        
            # 1. Confluence
            confluence = self.confluence_scorer.score_signal(direction, market_data, base_confidence, additional_data)
            if confluence.should_trade:
                reasons_to_trade.append(f"Confluence: {confluence.confluence_score} confirmations")
            else:
                reasons_not_to_trade.append(f"Low confluence: {confluence.confluence_score}")
        
            # 2. Entry timing
            entry = self.entry_timer.calculate_entry(direction, market_data, entry_price)
            if entry.should_enter_now:
                reasons_to_trade.append(f"Entry: {entry.reason}")
            else:
                reasons_not_to_trade.append(f"Entry: {entry.reason}")
        
            # 3. Session
            session = self.session_filter.assess_session(market_data=market_data)
            if session.should_trade:
                reasons_to_trade.append(f"Session: {session.reason}")
            else:
                reasons_not_to_trade.append(f"Session: {session.reason}")
        
            # 4. Recovery
            recovery = self.loss_recovery.get_current_state()
            if not recovery.should_trade:
                reasons_not_to_trade.append(f"Recovery: {recovery.reason}")
        
            # 5. Streak
            streak = self.streak_optimizer.get_current_state()
            if streak.should_increase_size:
                reasons_to_trade.append(f"Streak: {streak.consecutive_wins} wins")
        
            # 6. Size multiplier
            size_mult = (confluence.recommended_size_multiplier * session.size_multiplier *
                        recovery.size_multiplier * streak.size_multiplier)
            size_mult = max(0.25, min(1.5, size_mult))
        
            # 7. Targets
            targets = self.profit_targets.calculate_targets(
                direction, entry.ideal_entry if entry.should_enter_now else entry_price,
                stop_loss, market_data)
        
            # 8. Final decision
            should_trade = (confluence.should_trade and entry.should_enter_now and
                           session.should_trade and recovery.should_trade and size_mult >= 0.25)
        
            if should_trade:
                self.stats['signals_passed'] += 1
            else:
                self.stats['signals_rejected'] += 1
        
            confidence = min(0.95, max(0.1, confluence.adjusted_confidence *
                                       (1.1 if entry.entry_quality == EntryQuality.EXCELLENT else 1.0)))
        
            return TradeDecision(
                should_trade=should_trade, direction=direction,
                entry_price=entry.ideal_entry if entry.should_enter_now else entry_price,
                stop_loss=stop_loss, take_profit=targets.take_profit_2,
                position_size_multiplier=size_mult, confidence=confidence,
                confluence_score=confluence.confluence_score,
                entry_quality=entry.entry_quality, session_quality=session.session_quality,
                recovery_mode=recovery.recovery_mode, streak_mode=streak.streak_mode,
                reasons_to_trade=reasons_to_trade, reasons_not_to_trade=reasons_not_to_trade,
                profit_targets=targets
            )
        except Exception as e:
            logger.error(f"Error in evaluate_signal: {e}")
            raise
    
    def record_trade_result(self, trade_result: Dict):
        try:
            self.loss_recovery.update_state(trade_result)
            self.streak_optimizer.update_state(trade_result)
        except Exception as e:
            logger.error(f"Error in record_trade_result: {e}")
            raise
    
    def get_statistics(self) -> Dict:
        try:
            rate = self.stats['signals_passed'] / max(1, self.stats['signals_received']) * 100
            return {**self.stats, 'pass_rate': f"{rate:.1f}%",
                    'recovery': self.loss_recovery.get_current_state(),
                    'streak': self.streak_optimizer.get_current_state()}
        except Exception as e:
            logger.error(f"Error in get_statistics: {e}")
            raise


def quick_start(config: Optional[Dict] = None) -> ProfitMaximizerSystem:
    return ProfitMaximizerSystem(config)
