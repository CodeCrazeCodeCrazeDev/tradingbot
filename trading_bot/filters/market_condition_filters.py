"""
Market Condition Filters for Trade Filtering.

This module implements:
- Volatility filters
- Trend strength filters
- Volume filters
- Time-based filters
- Correlation filters
- Regime filters
- News/Event filters
- Liquidity filters
"""

import numpy as np
import pandas as pd
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional, Tuple
from enum import Enum
from datetime import datetime, time
import logging
import numpy
import pandas

logger = logging.getLogger(__name__)


class FilterResult(Enum):
    """Filter result status."""
    PASS = "pass"
    FAIL = "fail"
    WARNING = "warning"
    SKIP = "skip"


class MarketCondition(Enum):
    """Market condition types."""
    TRENDING = "trending"
    RANGING = "ranging"
    VOLATILE = "volatile"
    QUIET = "quiet"
    BREAKOUT = "breakout"
    REVERSAL = "reversal"
    CHOPPY = "choppy"


class TradingSession(Enum):
    """Trading sessions."""
    ASIAN = "asian"
    LONDON = "london"
    NEW_YORK = "new_york"
    OVERLAP_LONDON_NY = "overlap_london_ny"
    OFF_HOURS = "off_hours"


@dataclass
class FilterCheck:
    """Result of a single filter check."""
    filter_name: str
    result: FilterResult
    value: float
    threshold: float
    message: str
    weight: float = 1.0
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class FilterReport:
    """Complete filter report."""
    passed: bool
    score: float
    checks: List[FilterCheck]
    market_condition: MarketCondition
    trading_session: TradingSession
    recommendations: List[str]
    timestamp: datetime = field(default_factory=datetime.now)


class VolatilityFilter:
    """
    Filter trades based on volatility conditions.
    """
    
    def __init__(
        self,
        min_atr_percentile: float = 20,
        max_atr_percentile: float = 80,
        vix_threshold: float = 30,
        atr_period: int = 14
    ):
        try:
            self.min_atr_percentile = min_atr_percentile
            self.max_atr_percentile = max_atr_percentile
            self.vix_threshold = vix_threshold
            self.atr_period = atr_period
        except Exception as e:
            logger.error(f"Error in __init__: {e}")
            raise
        
    def calculate_atr(self, df: pd.DataFrame) -> pd.Series:
        """Calculate Average True Range."""
        try:
            high = df['high']
            low = df['low']
            close = df['close']
        
            tr1 = high - low
            tr2 = abs(high - close.shift(1))
            tr3 = abs(low - close.shift(1))
        
            tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
            atr = tr.rolling(window=self.atr_period).mean()
        
            return atr
        except Exception as e:
            logger.error(f"Error in calculate_atr: {e}")
            raise
    
    def check_volatility(
        self,
        df: pd.DataFrame,
        vix: Optional[float] = None
    ) -> FilterCheck:
        """Check if volatility is within acceptable range."""
        try:
            atr = self.calculate_atr(df)
            current_atr = atr.iloc[-1]
        
            # Calculate ATR percentile
            atr_percentile = (atr < current_atr).mean() * 100
        
            # Check VIX if provided
            vix_ok = vix is None or vix < self.vix_threshold
        
            # Determine result
            if atr_percentile < self.min_atr_percentile:
                result = FilterResult.FAIL
                message = f"Volatility too low (percentile: {atr_percentile:.1f}%)"
            elif atr_percentile > self.max_atr_percentile:
                result = FilterResult.WARNING
                message = f"Volatility high (percentile: {atr_percentile:.1f}%)"
            elif not vix_ok:
                result = FilterResult.WARNING
                message = f"VIX elevated ({vix:.1f})"
            else:
                result = FilterResult.PASS
                message = f"Volatility acceptable (percentile: {atr_percentile:.1f}%)"
        
            return FilterCheck(
                filter_name="volatility",
                result=result,
                value=atr_percentile,
                threshold=self.max_atr_percentile,
                message=message
            )
        except Exception as e:
            logger.error(f"Error in check_volatility: {e}")
            raise


class TrendFilter:
    """
    Filter trades based on trend strength.
    """
    
    def __init__(
        self,
        min_adx: float = 20,
        strong_trend_adx: float = 40,
        ema_periods: List[int] = None
    ):
        try:
            self.min_adx = min_adx
            self.strong_trend_adx = strong_trend_adx
            self.ema_periods = ema_periods or [20, 50, 200]
        except Exception as e:
            logger.error(f"Error in __init__: {e}")
            raise
        
    def calculate_adx(self, df: pd.DataFrame, period: int = 14) -> pd.Series:
        """Calculate Average Directional Index."""
        try:
            high = df['high']
            low = df['low']
            close = df['close']
        
            # Calculate +DM and -DM
            plus_dm = high.diff()
            minus_dm = -low.diff()
        
            plus_dm[plus_dm < 0] = 0
            minus_dm[minus_dm < 0] = 0
        
            # Where +DM > -DM, -DM = 0 and vice versa
            plus_dm[(plus_dm < minus_dm)] = 0
            minus_dm[(minus_dm < plus_dm)] = 0
        
            # Calculate TR
            tr1 = high - low
            tr2 = abs(high - close.shift(1))
            tr3 = abs(low - close.shift(1))
            tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)
        
            # Smooth
            atr = tr.rolling(window=period).mean()
            plus_di = 100 * (plus_dm.rolling(window=period).mean() / atr)
            minus_di = 100 * (minus_dm.rolling(window=period).mean() / atr)
        
            # Calculate DX and ADX
            dx = 100 * abs(plus_di - minus_di) / (plus_di + minus_di + 1e-10)
            adx = dx.rolling(window=period).mean()
        
            return adx
        except Exception as e:
            logger.error(f"Error in calculate_adx: {e}")
            raise
    
    def check_ema_alignment(self, df: pd.DataFrame) -> Tuple[bool, str]:
        """Check if EMAs are properly aligned."""
        try:
            close = df['close']
        
            emas = {}
            for period in self.ema_periods:
                emas[period] = close.ewm(span=period, adjust=False).mean().iloc[-1]
        
            sorted_periods = sorted(self.ema_periods)
        
            # Check bullish alignment (shorter EMAs above longer)
            bullish = all(emas[sorted_periods[i]] > emas[sorted_periods[i+1]] 
                         for i in range(len(sorted_periods)-1))
        
            # Check bearish alignment
            bearish = all(emas[sorted_periods[i]] < emas[sorted_periods[i+1]] 
                         for i in range(len(sorted_periods)-1))
        
            if bullish:
                return True, "bullish"
            elif bearish:
                return True, "bearish"
            else:
                return False, "mixed"
        except Exception as e:
            logger.error(f"Error in check_ema_alignment: {e}")
            raise
    
    def check_trend(self, df: pd.DataFrame) -> FilterCheck:
        """Check trend strength and direction."""
        try:
            adx = self.calculate_adx(df)
            current_adx = adx.iloc[-1]
        
            aligned, direction = self.check_ema_alignment(df)
        
            if current_adx < self.min_adx:
                result = FilterResult.FAIL
                message = f"Weak trend (ADX: {current_adx:.1f})"
            elif not aligned:
                result = FilterResult.WARNING
                message = f"EMAs not aligned (ADX: {current_adx:.1f})"
            elif current_adx >= self.strong_trend_adx:
                result = FilterResult.PASS
                message = f"Strong {direction} trend (ADX: {current_adx:.1f})"
            else:
                result = FilterResult.PASS
                message = f"Moderate {direction} trend (ADX: {current_adx:.1f})"
        
            return FilterCheck(
                filter_name="trend",
                result=result,
                value=current_adx,
                threshold=self.min_adx,
                message=message
            )
        except Exception as e:
            logger.error(f"Error in check_trend: {e}")
            raise


class VolumeFilter:
    """
    Filter trades based on volume conditions.
    """
    
    def __init__(
        self,
        min_volume_ratio: float = 0.5,
        high_volume_ratio: float = 2.0,
        lookback: int = 20
    ):
        try:
            self.min_volume_ratio = min_volume_ratio
            self.high_volume_ratio = high_volume_ratio
            self.lookback = lookback
        except Exception as e:
            logger.error(f"Error in __init__: {e}")
            raise
        
    def check_volume(self, df: pd.DataFrame) -> FilterCheck:
        """Check if volume is sufficient."""
        try:
            volume = df['volume']
        
            avg_volume = volume.rolling(window=self.lookback).mean()
            current_volume = volume.iloc[-1]
            volume_ratio = current_volume / (avg_volume.iloc[-1] + 1e-10)
        
            if volume_ratio < self.min_volume_ratio:
                result = FilterResult.FAIL
                message = f"Low volume ({volume_ratio:.2f}x average)"
            elif volume_ratio > self.high_volume_ratio:
                result = FilterResult.PASS
                message = f"High volume ({volume_ratio:.2f}x average)"
            else:
                result = FilterResult.PASS
                message = f"Normal volume ({volume_ratio:.2f}x average)"
        
            return FilterCheck(
                filter_name="volume",
                result=result,
                value=volume_ratio,
                threshold=self.min_volume_ratio,
                message=message
            )
        except Exception as e:
            logger.error(f"Error in check_volume: {e}")
            raise


class TimeFilter:
    """
    Filter trades based on time conditions.
    """
    
    def __init__(
        self,
        allowed_sessions: List[TradingSession] = None,
        blocked_hours: List[int] = None,
        avoid_news_minutes: int = 30
    ):
        try:
            self.allowed_sessions = allowed_sessions or [
                TradingSession.LONDON,
                TradingSession.NEW_YORK,
                TradingSession.OVERLAP_LONDON_NY
            ]
            self.blocked_hours = blocked_hours or []
            self.avoid_news_minutes = avoid_news_minutes
        
            # Session times (UTC)
            self.session_times = {
                TradingSession.ASIAN: (time(0, 0), time(8, 0)),
                TradingSession.LONDON: (time(8, 0), time(16, 0)),
                TradingSession.NEW_YORK: (time(13, 0), time(21, 0)),
                TradingSession.OVERLAP_LONDON_NY: (time(13, 0), time(16, 0)),
                TradingSession.OFF_HOURS: (time(21, 0), time(0, 0))
            }
        except Exception as e:
            logger.error(f"Error in __init__: {e}")
            raise
        
    def get_current_session(self, current_time: datetime) -> TradingSession:
        """Determine current trading session."""
        try:
            t = current_time.time()
        
            # Check overlap first
            overlap_start, overlap_end = self.session_times[TradingSession.OVERLAP_LONDON_NY]
            if overlap_start <= t <= overlap_end:
                return TradingSession.OVERLAP_LONDON_NY
        
            # Check other sessions
            for session, (start, end) in self.session_times.items():
                if session == TradingSession.OVERLAP_LONDON_NY:
                    continue
                if start <= t <= end:
                    return session
        
            return TradingSession.OFF_HOURS
        except Exception as e:
            logger.error(f"Error in get_current_session: {e}")
            raise
    
    def check_time(
        self,
        current_time: datetime,
        upcoming_news: Optional[datetime] = None
    ) -> FilterCheck:
        """Check if current time is suitable for trading."""
        try:
            session = self.get_current_session(current_time)
            hour = current_time.hour
        
            # Check blocked hours
            if hour in self.blocked_hours:
                return FilterCheck(
                    filter_name="time",
                    result=FilterResult.FAIL,
                    value=float(hour),
                    threshold=0,
                    message=f"Hour {hour} is blocked"
                )
        
            # Check session
            if session not in self.allowed_sessions:
                return FilterCheck(
                    filter_name="time",
                    result=FilterResult.FAIL,
                    value=0,
                    threshold=0,
                    message=f"Session {session.value} not allowed"
                )
        
            # Check upcoming news
            if upcoming_news:
                minutes_to_news = (upcoming_news - current_time).total_seconds() / 60
                if 0 < minutes_to_news < self.avoid_news_minutes:
                    return FilterCheck(
                        filter_name="time",
                        result=FilterResult.WARNING,
                        value=minutes_to_news,
                        threshold=self.avoid_news_minutes,
                        message=f"News in {minutes_to_news:.0f} minutes"
                    )
        
            return FilterCheck(
                filter_name="time",
                result=FilterResult.PASS,
                value=float(hour),
                threshold=0,
                message=f"Trading in {session.value} session"
            )
        except Exception as e:
            logger.error(f"Error in check_time: {e}")
            raise


class CorrelationFilter:
    """
    Filter trades based on correlation with existing positions.
    """
    
    def __init__(
        self,
        max_correlation: float = 0.7,
        lookback: int = 50
    ):
        try:
            self.max_correlation = max_correlation
            self.lookback = lookback
        except Exception as e:
            logger.error(f"Error in __init__: {e}")
            raise
        
    def calculate_correlation(
        self,
        returns1: pd.Series,
        returns2: pd.Series
    ) -> float:
        """Calculate correlation between two return series."""
        try:
            if len(returns1) < self.lookback or len(returns2) < self.lookback:
                return 0.0
        
            r1 = returns1.iloc[-self.lookback:]
            r2 = returns2.iloc[-self.lookback:]
        
            return float(r1.corr(r2))
        except Exception as e:
            logger.error(f"Error in calculate_correlation: {e}")
            raise
    
    def check_correlation(
        self,
        new_symbol_returns: pd.Series,
        existing_positions_returns: Dict[str, pd.Series]
    ) -> FilterCheck:
        """Check correlation with existing positions."""
        try:
            if not existing_positions_returns:
                return FilterCheck(
                    filter_name="correlation",
                    result=FilterResult.PASS,
                    value=0,
                    threshold=self.max_correlation,
                    message="No existing positions"
                )
        
            max_corr = 0.0
            max_corr_symbol = ""
        
            for symbol, returns in existing_positions_returns.items():
                corr = abs(self.calculate_correlation(new_symbol_returns, returns))
                if corr > max_corr:
                    max_corr = corr
                    max_corr_symbol = symbol
        
            if max_corr > self.max_correlation:
                return FilterCheck(
                    filter_name="correlation",
                    result=FilterResult.FAIL,
                    value=max_corr,
                    threshold=self.max_correlation,
                    message=f"High correlation ({max_corr:.2f}) with {max_corr_symbol}"
                )
        
            return FilterCheck(
                filter_name="correlation",
                result=FilterResult.PASS,
                value=max_corr,
                threshold=self.max_correlation,
                message=f"Correlation acceptable ({max_corr:.2f})"
            )
        except Exception as e:
            logger.error(f"Error in check_correlation: {e}")
            raise


class SpreadFilter:
    """
    Filter trades based on spread/liquidity conditions.
    """
    
    def __init__(
        self,
        max_spread_pips: float = 3.0,
        max_spread_percent: float = 0.1
    ):
        try:
            self.max_spread_pips = max_spread_pips
            self.max_spread_percent = max_spread_percent
        except Exception as e:
            logger.error(f"Error in __init__: {e}")
            raise
        
    def check_spread(
        self,
        bid: float,
        ask: float,
        pip_value: float = 0.0001
    ) -> FilterCheck:
        """Check if spread is acceptable."""
        try:
            spread = ask - bid
            spread_pips = spread / pip_value
            spread_percent = (spread / bid) * 100
        
            if spread_pips > self.max_spread_pips:
                return FilterCheck(
                    filter_name="spread",
                    result=FilterResult.FAIL,
                    value=spread_pips,
                    threshold=self.max_spread_pips,
                    message=f"Spread too wide ({spread_pips:.1f} pips)"
                )
        
            if spread_percent > self.max_spread_percent:
                return FilterCheck(
                    filter_name="spread",
                    result=FilterResult.WARNING,
                    value=spread_percent,
                    threshold=self.max_spread_percent,
                    message=f"Spread high ({spread_percent:.3f}%)"
                )
        
            return FilterCheck(
                filter_name="spread",
                result=FilterResult.PASS,
                value=spread_pips,
                threshold=self.max_spread_pips,
                message=f"Spread acceptable ({spread_pips:.1f} pips)"
            )
        except Exception as e:
            logger.error(f"Error in check_spread: {e}")
            raise


class MarketConditionFilterSystem:
    """
    Complete market condition filtering system.
    
    Combines all filters for comprehensive trade filtering.
    """
    
    def __init__(
        self,
        volatility_filter: Optional[VolatilityFilter] = None,
        trend_filter: Optional[TrendFilter] = None,
        volume_filter: Optional[VolumeFilter] = None,
        time_filter: Optional[TimeFilter] = None,
        correlation_filter: Optional[CorrelationFilter] = None,
        spread_filter: Optional[SpreadFilter] = None,
        min_pass_score: float = 0.6
    ):
        try:
            self.volatility_filter = volatility_filter or VolatilityFilter()
            self.trend_filter = trend_filter or TrendFilter()
            self.volume_filter = volume_filter or VolumeFilter()
            self.time_filter = time_filter or TimeFilter()
            self.correlation_filter = correlation_filter or CorrelationFilter()
            self.spread_filter = spread_filter or SpreadFilter()
            self.min_pass_score = min_pass_score
        
            # Filter weights
            self.weights = {
                'volatility': 1.0,
                'trend': 1.0,
                'volume': 0.8,
                'time': 1.0,
                'correlation': 0.7,
                'spread': 0.9
            }
        except Exception as e:
            logger.error(f"Error in __init__: {e}")
            raise
        
    def determine_market_condition(self, df: pd.DataFrame) -> MarketCondition:
        """Determine current market condition."""
        # Calculate indicators
        try:
            atr = self.volatility_filter.calculate_atr(df)
            adx = self.trend_filter.calculate_adx(df)
        
            current_atr = atr.iloc[-1]
            avg_atr = atr.mean()
            current_adx = adx.iloc[-1]
        
            # Determine condition
            if current_adx > 40:
                return MarketCondition.TRENDING
            elif current_adx < 20:
                if current_atr > avg_atr * 1.5:
                    return MarketCondition.CHOPPY
                else:
                    return MarketCondition.RANGING
            elif current_atr > avg_atr * 2:
                return MarketCondition.VOLATILE
            elif current_atr < avg_atr * 0.5:
                return MarketCondition.QUIET
            else:
                return MarketCondition.RANGING
        except Exception as e:
            logger.error(f"Error in determine_market_condition: {e}")
            raise
    
    def run_all_filters(
        self,
        df: pd.DataFrame,
        current_time: Optional[datetime] = None,
        bid: Optional[float] = None,
        ask: Optional[float] = None,
        vix: Optional[float] = None,
        existing_positions_returns: Optional[Dict[str, pd.Series]] = None,
        upcoming_news: Optional[datetime] = None
    ) -> FilterReport:
        """Run all filters and generate report."""
        try:
            checks = []
        
            # Volatility filter
            vol_check = self.volatility_filter.check_volatility(df, vix)
            vol_check.weight = self.weights['volatility']
            checks.append(vol_check)
        
            # Trend filter
            trend_check = self.trend_filter.check_trend(df)
            trend_check.weight = self.weights['trend']
            checks.append(trend_check)
        
            # Volume filter
            vol_check = self.volume_filter.check_volume(df)
            vol_check.weight = self.weights['volume']
            checks.append(vol_check)
        
            # Time filter
            if current_time:
                time_check = self.time_filter.check_time(current_time, upcoming_news)
                time_check.weight = self.weights['time']
                checks.append(time_check)
        
            # Correlation filter
            if existing_positions_returns:
                returns = df['close'].pct_change()
                corr_check = self.correlation_filter.check_correlation(
                    returns, existing_positions_returns
                )
                corr_check.weight = self.weights['correlation']
                checks.append(corr_check)
        
            # Spread filter
            if bid is not None and ask is not None:
                spread_check = self.spread_filter.check_spread(bid, ask)
                spread_check.weight = self.weights['spread']
                checks.append(spread_check)
        
            # Calculate score
            total_weight = sum(c.weight for c in checks)
            passed_weight = sum(
                c.weight for c in checks 
                if c.result in [FilterResult.PASS, FilterResult.WARNING]
            )
            score = passed_weight / total_weight if total_weight > 0 else 0
        
            # Determine if passed
            has_fail = any(c.result == FilterResult.FAIL for c in checks)
            passed = not has_fail and score >= self.min_pass_score
        
            # Get market condition
            market_condition = self.determine_market_condition(df)
        
            # Get trading session
            trading_session = self.time_filter.get_current_session(
                current_time or datetime.now()
            )
        
            # Generate recommendations
            recommendations = []
            for check in checks:
                if check.result == FilterResult.FAIL:
                    recommendations.append(f"Address {check.filter_name}: {check.message}")
                elif check.result == FilterResult.WARNING:
                    recommendations.append(f"Monitor {check.filter_name}: {check.message}")
        
            return FilterReport(
                passed=passed,
                score=score,
                checks=checks,
                market_condition=market_condition,
                trading_session=trading_session,
                recommendations=recommendations
            )
        except Exception as e:
            logger.error(f"Error in run_all_filters: {e}")
            raise
    
    def should_trade(
        self,
        df: pd.DataFrame,
        **kwargs
    ) -> Tuple[bool, str]:
        """Quick check if trading conditions are met."""
        try:
            report = self.run_all_filters(df, **kwargs)
        
            if report.passed:
                return True, f"Conditions met (score: {report.score:.2f})"
            else:
                failed = [c.filter_name for c in report.checks if c.result == FilterResult.FAIL]
                return False, f"Failed filters: {', '.join(failed)}"
        except Exception as e:
            logger.error(f"Error in should_trade: {e}")
            raise


# Convenience functions
def check_market_conditions(df: pd.DataFrame) -> Dict[str, Any]:
    """Quick market condition check."""
    try:
        system = MarketConditionFilterSystem()
        report = system.run_all_filters(df)
    
        return {
            'passed': report.passed,
            'score': report.score,
            'condition': report.market_condition.value,
            'recommendations': report.recommendations
        }
    except Exception as e:
        logger.error(f"Error in check_market_conditions: {e}")
        raise


def is_good_trading_time(current_time: datetime = None) -> Tuple[bool, str]:
    """Check if current time is good for trading."""
    try:
        time_filter = TimeFilter()
        check = time_filter.check_time(current_time or datetime.now())
    
        return check.result == FilterResult.PASS, check.message
    except Exception as e:
        logger.error(f"Error in is_good_trading_time: {e}")
        raise


def get_market_condition(df: pd.DataFrame) -> MarketCondition:
    """Get current market condition."""
    try:
        system = MarketConditionFilterSystem()
        return system.determine_market_condition(df)
    except Exception as e:
        logger.error(f"Error in get_market_condition: {e}")
        raise
