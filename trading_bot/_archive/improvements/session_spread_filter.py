"""
Session & Spread Filter
=======================

Filters trades based on:
1. Trading session (London, New York, Asian)
2. Current spread conditions
3. Time-of-day optimization

Target: Avoid low-probability trading times and high-cost conditions
"""

import logging
from typing import Any, Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime, time, timezone
from enum import Enum

logger = logging.getLogger(__name__)


class TradingSession(Enum):
    """Trading session classification"""
    ASIAN = "asian"           # Tokyo session
    LONDON = "london"         # London session
    NEW_YORK = "new_york"     # New York session
    OVERLAP_LN = "overlap_ln" # London-New York overlap (best)
    OFF_HOURS = "off_hours"   # Weekend/low liquidity


@dataclass
class SessionInfo:
    """Information about current trading session"""
    session: TradingSession
    is_optimal: bool
    liquidity_score: float  # 0-1
    volatility_expected: str  # 'low', 'medium', 'high'
    recommended_pairs: List[str]
    avoid_pairs: List[str]
    reason: str


@dataclass
class SpreadInfo:
    """Information about current spread conditions"""
    symbol: str
    current_spread: float
    average_spread: float
    max_acceptable: float
    is_acceptable: bool
    spread_score: float  # 0-1 (1 = very tight)
    reason: str


class SessionFilter:
    """
    Filters trades based on trading session.
    
    PRINCIPLE: Trade when liquidity is highest for your pairs.
    """
    
    # Session times in UTC
    SESSIONS = {
        TradingSession.ASIAN: {
            'start': time(0, 0),   # 00:00 UTC
            'end': time(9, 0),     # 09:00 UTC
            'best_pairs': ['USDJPY', 'EURJPY', 'GBPJPY', 'AUDJPY', 'NZDJPY'],
            'liquidity': 0.6,
            'volatility': 'low'
        },
        TradingSession.LONDON: {
            'start': time(7, 0),   # 07:00 UTC
            'end': time(16, 0),    # 16:00 UTC
            'best_pairs': ['EURUSD', 'GBPUSD', 'EURGBP', 'EURJPY', 'GBPJPY'],
            'liquidity': 0.9,
            'volatility': 'high'
        },
        TradingSession.NEW_YORK: {
            'start': time(12, 0),  # 12:00 UTC
            'end': time(21, 0),    # 21:00 UTC
            'best_pairs': ['EURUSD', 'GBPUSD', 'USDCAD', 'USDCHF', 'USDJPY'],
            'liquidity': 0.85,
            'volatility': 'high'
        },
        TradingSession.OVERLAP_LN: {
            'start': time(12, 0),  # 12:00 UTC
            'end': time(16, 0),    # 16:00 UTC
            'best_pairs': ['EURUSD', 'GBPUSD', 'USDCHF', 'USDJPY'],
            'liquidity': 1.0,
            'volatility': 'high'
        }
    }
    
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        
        # Whether to strictly enforce session rules
        self.strict_mode = self.config.get('strict_mode', False)
        
        # Minimum liquidity score to trade
        self.min_liquidity = self.config.get('min_liquidity', 0.5)
        
        # Allow trading during Asian session
        self.allow_asian = self.config.get('allow_asian', True)
        
        logger.info(f"SessionFilter initialized: strict={self.strict_mode}")
    
    def get_current_session(self, utc_time: Optional[datetime] = None) -> SessionInfo:
        """Get information about the current trading session"""
        if utc_time is None:
            utc_time = datetime.now(timezone.utc)
        
        current_time = utc_time.time()
        weekday = utc_time.weekday()
        
        # Check for weekend
        if weekday >= 5:  # Saturday or Sunday
            return SessionInfo(
                session=TradingSession.OFF_HOURS,
                is_optimal=False,
                liquidity_score=0.0,
                volatility_expected='low',
                recommended_pairs=[],
                avoid_pairs=['ALL'],
                reason="Weekend - markets closed"
            )
        
        # Check for London-New York overlap (best time)
        overlap = self.SESSIONS[TradingSession.OVERLAP_LN]
        if overlap['start'] <= current_time <= overlap['end']:
            return SessionInfo(
                session=TradingSession.OVERLAP_LN,
                is_optimal=True,
                liquidity_score=overlap['liquidity'],
                volatility_expected=overlap['volatility'],
                recommended_pairs=overlap['best_pairs'],
                avoid_pairs=[],
                reason="London-New York overlap - optimal trading time"
            )
        
        # Check London session
        london = self.SESSIONS[TradingSession.LONDON]
        if london['start'] <= current_time <= london['end']:
            return SessionInfo(
                session=TradingSession.LONDON,
                is_optimal=True,
                liquidity_score=london['liquidity'],
                volatility_expected=london['volatility'],
                recommended_pairs=london['best_pairs'],
                avoid_pairs=['AUDUSD', 'NZDUSD'],
                reason="London session - good for EUR/GBP pairs"
            )
        
        # Check New York session
        ny = self.SESSIONS[TradingSession.NEW_YORK]
        if ny['start'] <= current_time <= ny['end']:
            return SessionInfo(
                session=TradingSession.NEW_YORK,
                is_optimal=True,
                liquidity_score=ny['liquidity'],
                volatility_expected=ny['volatility'],
                recommended_pairs=ny['best_pairs'],
                avoid_pairs=['EURGBP'],
                reason="New York session - good for USD pairs"
            )
        
        # Check Asian session
        asian = self.SESSIONS[TradingSession.ASIAN]
        if asian['start'] <= current_time <= asian['end']:
            return SessionInfo(
                session=TradingSession.ASIAN,
                is_optimal=not self.strict_mode,
                liquidity_score=asian['liquidity'],
                volatility_expected=asian['volatility'],
                recommended_pairs=asian['best_pairs'],
                avoid_pairs=['EURUSD', 'GBPUSD'],
                reason="Asian session - best for JPY pairs, ranging for others"
            )
        
        # Off hours
        return SessionInfo(
            session=TradingSession.OFF_HOURS,
            is_optimal=False,
            liquidity_score=0.3,
            volatility_expected='low',
            recommended_pairs=[],
            avoid_pairs=['ALL'],
            reason="Off hours - low liquidity"
        )
    
    def should_trade(
        self,
        symbol: str,
        utc_time: Optional[datetime] = None
    ) -> Tuple[bool, str]:
        """
        Check if trading is recommended for the symbol at current time.
        
        Returns:
            Tuple of (should_trade, reason)
        """
        session_info = self.get_current_session(utc_time)
        
        # Check if session is optimal
        if not session_info.is_optimal and self.strict_mode:
            return False, f"Not optimal session: {session_info.reason}"
        
        # Check liquidity
        if session_info.liquidity_score < self.min_liquidity:
            return False, f"Low liquidity ({session_info.liquidity_score:.2f})"
        
        # Check if symbol is in avoid list
        if 'ALL' in session_info.avoid_pairs:
            return False, session_info.reason
        
        # Extract base and quote currencies
        base = symbol[:3] if len(symbol) >= 6 else symbol
        quote = symbol[3:6] if len(symbol) >= 6 else ''
        
        for avoid in session_info.avoid_pairs:
            if avoid in symbol:
                return False, f"{symbol} not recommended during {session_info.session.value}"
        
        # Check if symbol is recommended
        is_recommended = any(rec in symbol for rec in session_info.recommended_pairs)
        
        if is_recommended:
            return True, f"Optimal time for {symbol} ({session_info.session.value})"
        
        # Allow but note it's not optimal
        return True, f"Acceptable time for {symbol} ({session_info.session.value})"
    
    def get_best_pairs_now(self, utc_time: Optional[datetime] = None) -> List[str]:
        """Get the best pairs to trade right now"""
        session_info = self.get_current_session(utc_time)
        return session_info.recommended_pairs


class SpreadFilter:
    """
    Filters trades based on spread conditions.
    
    PRINCIPLE: Don't trade when spread eats into profit potential.
    """
    
    # Maximum acceptable spreads in pips
    DEFAULT_MAX_SPREADS = {
        'EURUSD': 1.5,
        'GBPUSD': 2.0,
        'USDJPY': 1.5,
        'USDCHF': 2.0,
        'AUDUSD': 2.0,
        'NZDUSD': 2.5,
        'USDCAD': 2.0,
        'EURGBP': 2.0,
        'EURJPY': 2.5,
        'GBPJPY': 3.0,
        'XAUUSD': 35.0,  # Gold in cents
        'BTCUSD': 50.0,  # Bitcoin
    }
    
    # Average spreads for scoring
    AVERAGE_SPREADS = {
        'EURUSD': 0.8,
        'GBPUSD': 1.2,
        'USDJPY': 0.9,
        'USDCHF': 1.2,
        'AUDUSD': 1.2,
        'NZDUSD': 1.5,
        'USDCAD': 1.3,
        'EURGBP': 1.2,
        'EURJPY': 1.5,
        'GBPJPY': 2.0,
    }
    
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        
        # Custom max spreads
        self.max_spreads = {**self.DEFAULT_MAX_SPREADS}
        self.max_spreads.update(self.config.get('max_spreads', {}))
        
        # Spread multiplier for high volatility
        self.volatility_multiplier = self.config.get('volatility_multiplier', 1.5)
        
        # Default max spread for unknown symbols
        self.default_max = self.config.get('default_max', 3.0)
        
        logger.info(f"SpreadFilter initialized: {len(self.max_spreads)} symbols configured")
    
    def check_spread(
        self,
        symbol: str,
        current_spread: float,
        is_high_volatility: bool = False
    ) -> SpreadInfo:
        """
        Check if current spread is acceptable.
        
        Args:
            symbol: Trading symbol
            current_spread: Current spread in pips
            is_high_volatility: Whether market is in high volatility mode
        
        Returns:
            SpreadInfo with analysis
        """
        max_spread = self.max_spreads.get(symbol, self.default_max)
        avg_spread = self.AVERAGE_SPREADS.get(symbol, max_spread * 0.6)
        
        # Adjust for high volatility
        if is_high_volatility:
            max_spread *= self.volatility_multiplier
        
        is_acceptable = current_spread <= max_spread
        
        # Calculate spread score (1 = very tight, 0 = too wide)
        if current_spread <= avg_spread:
            spread_score = 1.0
        elif current_spread <= max_spread:
            spread_score = 1.0 - ((current_spread - avg_spread) / (max_spread - avg_spread)) * 0.5
        else:
            spread_score = max(0.0, 0.5 - ((current_spread - max_spread) / max_spread) * 0.5)
        
        if is_acceptable:
            if current_spread <= avg_spread:
                reason = f"Excellent spread ({current_spread:.1f} pips)"
            else:
                reason = f"Acceptable spread ({current_spread:.1f} pips)"
        else:
            reason = f"Spread too wide ({current_spread:.1f} > {max_spread:.1f} pips)"
        
        return SpreadInfo(
            symbol=symbol,
            current_spread=current_spread,
            average_spread=avg_spread,
            max_acceptable=max_spread,
            is_acceptable=is_acceptable,
            spread_score=spread_score,
            reason=reason
        )
    
    def should_trade(
        self,
        symbol: str,
        current_spread: float,
        is_high_volatility: bool = False
    ) -> Tuple[bool, str]:
        """
        Check if spread conditions allow trading.
        
        Returns:
            Tuple of (should_trade, reason)
        """
        spread_info = self.check_spread(symbol, current_spread, is_high_volatility)
        return spread_info.is_acceptable, spread_info.reason
    
    def get_spread_adjusted_tp(
        self,
        symbol: str,
        current_spread: float,
        base_tp_pips: float
    ) -> float:
        """
        Adjust take profit to account for spread.
        
        Returns:
            Adjusted TP in pips
        """
        # TP should be at least 2x the spread to be profitable
        min_tp = current_spread * 2.5
        return max(base_tp_pips, min_tp)
    
    def calculate_breakeven_pips(
        self,
        symbol: str,
        current_spread: float
    ) -> float:
        """Calculate pips needed to break even after spread"""
        return current_spread * 1.1  # Add 10% buffer


class TradingTimeFilter:
    """
    Combined session and spread filter for optimal trading times.
    """
    
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        
        self.session_filter = SessionFilter(self.config.get('session', {}))
        self.spread_filter = SpreadFilter(self.config.get('spread', {}))
        
        logger.info("TradingTimeFilter initialized")
    
    def should_trade(
        self,
        symbol: str,
        current_spread: float,
        utc_time: Optional[datetime] = None,
        is_high_volatility: bool = False
    ) -> Tuple[bool, List[str]]:
        """
        Check if trading conditions are favorable.
        
        Returns:
            Tuple of (should_trade, list of reasons)
        """
        reasons = []
        
        # Check session
        session_ok, session_reason = self.session_filter.should_trade(symbol, utc_time)
        reasons.append(session_reason)
        
        # Check spread
        spread_ok, spread_reason = self.spread_filter.should_trade(
            symbol, current_spread, is_high_volatility
        )
        reasons.append(spread_reason)
        
        should_trade = session_ok and spread_ok
        
        return should_trade, reasons
    
    def get_trading_score(
        self,
        symbol: str,
        current_spread: float,
        utc_time: Optional[datetime] = None
    ) -> float:
        """
        Get overall trading conditions score (0-1).
        """
        session_info = self.session_filter.get_current_session(utc_time)
        spread_info = self.spread_filter.check_spread(symbol, current_spread)
        
        # Weighted average
        session_weight = 0.4
        spread_weight = 0.6
        
        score = (
            session_info.liquidity_score * session_weight +
            spread_info.spread_score * spread_weight
        )
        
        return score
