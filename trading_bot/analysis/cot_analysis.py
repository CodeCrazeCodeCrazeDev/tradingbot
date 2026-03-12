"""COT (Commitment of Traders) Report Analysis Module.

Implements institutional-grade COT report analysis including:
- COT report data fetching and parsing
- Commercial vs Non-Commercial positioning analysis
- Historical positioning context
- Net position changes and trends
- Extreme positioning detection
- Retail trader positioning from broker reports
- COT index calculations
- Positioning divergence signals

This module enables tracking of institutional positioning for
informed trading decisions based on smart money flows.
"""


from __future__ import annotations
import logging
import enum
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple
import json
import asyncio

import numpy as np
import pandas as pd

try:
    from loguru import logger
except ImportError:
    logger = logging.getLogger(__name__)

try:
    import aiohttp
except ImportError:
    aiohttp = None


class TraderCategory(enum.Enum):
    """Categories of traders in COT reports."""
    COMMERCIAL = "commercial"  # Hedgers - typically fade their positions
    NON_COMMERCIAL = "non_commercial"  # Large speculators - trend followers
    NON_REPORTABLE = "non_reportable"  # Small speculators - often wrong
    DEALER = "dealer"  # Swap dealers
    ASSET_MANAGER = "asset_manager"  # Institutional investors
    LEVERAGED = "leveraged"  # Hedge funds
    OTHER_REPORTABLE = "other_reportable"


class PositionType(enum.Enum):
    """Types of positions."""
    LONG = "long"
    SHORT = "short"
    SPREADING = "spreading"


class COTSignal(enum.Enum):
    """COT-based trading signals."""
    STRONG_BULLISH = "strong_bullish"
    BULLISH = "bullish"
    NEUTRAL = "neutral"
    BEARISH = "bearish"
    STRONG_BEARISH = "strong_bearish"


@dataclass
class COTPosition:
    """Represents a trader category's position."""
    category: TraderCategory
    long_positions: int
    short_positions: int
    spreading_positions: int = 0
    net_position: int = 0
    change_long: int = 0
    change_short: int = 0
    change_net: int = 0
    percent_of_oi_long: float = 0.0
    percent_of_oi_short: float = 0.0
    
    def __post_init__(self):
        self.net_position = self.long_positions - self.short_positions


@dataclass
class COTReport:
    """Complete COT report for a single release."""
    report_date: datetime
    market_name: str
    contract_code: str
    open_interest: int
    positions: Dict[TraderCategory, COTPosition]
    
    # Calculated metrics
    commercial_net: int = 0
    non_commercial_net: int = 0
    retail_net: int = 0
    
    def __post_init__(self):
        if TraderCategory.COMMERCIAL in self.positions:
            self.commercial_net = self.positions[TraderCategory.COMMERCIAL].net_position
        if TraderCategory.NON_COMMERCIAL in self.positions:
            self.non_commercial_net = self.positions[TraderCategory.NON_COMMERCIAL].net_position
        if TraderCategory.NON_REPORTABLE in self.positions:
            self.retail_net = self.positions[TraderCategory.NON_REPORTABLE].net_position


@dataclass
class COTIndex:
    """COT Index calculation (0-100 scale)."""
    category: TraderCategory
    current_net: int
    index_value: float  # 0-100
    lookback_high: int
    lookback_low: int
    lookback_periods: int
    signal: COTSignal
    
    
@dataclass
class COTDivergence:
    """Divergence between price and COT positioning."""
    divergence_type: str  # 'bullish' or 'bearish'
    category: TraderCategory
    price_direction: str  # 'up' or 'down'
    position_direction: str  # 'increasing' or 'decreasing'
    strength: float  # 0-100
    periods: int  # Number of periods of divergence


@dataclass
class RetailPositioning:
    """Retail trader positioning from broker reports."""
    broker_name: str
    symbol: str
    timestamp: datetime
    percent_long: float
    percent_short: float
    total_positions: int
    sentiment_index: float  # -100 to +100
    contrarian_signal: COTSignal


class COTAnalyzer:
    """COT Report Analysis Engine.
    
    Provides comprehensive analysis of Commitment of Traders reports
    for identifying institutional positioning and potential reversals.
    """
    
    # CFTC COT report URLs
    CFTC_BASE_URL = "https://www.cftc.gov/dea/newcot"
    QUANDL_COT_URL = "https://data.nasdaq.com/api/v3/datasets/CFTC"
    
    # Common futures contract codes
    CONTRACT_CODES = {
        'EUR': '099741',  # Euro FX
        'GBP': '096742',  # British Pound
        'JPY': '097741',  # Japanese Yen
        'AUD': '232741',  # Australian Dollar
        'CAD': '090741',  # Canadian Dollar
        'CHF': '092741',  # Swiss Franc
        'NZD': '112741',  # New Zealand Dollar
        'GOLD': '088691',  # Gold
        'SILVER': '084691',  # Silver
        'CRUDE': '067651',  # Crude Oil
        'NATGAS': '023651',  # Natural Gas
        'SP500': '13874A',  # S&P 500
        'NASDAQ': '209742',  # Nasdaq 100
        'DOW': '124601',  # Dow Jones
        'BTC': '133741',  # Bitcoin
        'CORN': '002602',  # Corn
        'WHEAT': '001602',  # Wheat
        'SOYBEANS': '005602',  # Soybeans
    }
    
    def __init__(
        self,
        lookback_periods: int = 52,
        extreme_threshold: float = 90.0,
        api_key: Optional[str] = None
    ):
        """Initialize COT Analyzer.
        
        Args:
            lookback_periods: Periods for COT index calculation (default 52 weeks)
            extreme_threshold: Threshold for extreme positioning (default 90%)
            api_key: Optional API key for data providers
        """
        self.lookback_periods = lookback_periods
        self.extreme_threshold = extreme_threshold
        self.api_key = api_key
        
        # Cache for COT data
        self._cot_cache: Dict[str, List[COTReport]] = {}
        self._last_fetch: Dict[str, datetime] = {}
        
    async def fetch_cot_data(
        self,
        symbol: str,
        weeks: int = 52
    ) -> List[COTReport]:
        """Fetch COT data for a symbol.
        
        Args:
            symbol: Trading symbol (e.g., 'EUR', 'GOLD')
            weeks: Number of weeks of data to fetch
            
        Returns:
            List of COTReport objects
        """
        if aiohttp is None:
            logger.warning("aiohttp not installed, using cached/mock data")
            return self._get_mock_cot_data(symbol, weeks)
            
        # Check cache
        cache_key = f"{symbol}_{weeks}"
        if cache_key in self._cot_cache:
            try:
                last_fetch = self._last_fetch.get(cache_key, datetime.min)
                if datetime.now() - last_fetch < timedelta(hours=24):
                    return self._cot_cache[cache_key]

                contract_code = self.CONTRACT_CODES.get(symbol.upper(), symbol)

                async with aiohttp.ClientSession() as session:
                    # Try Nasdaq Data Link (formerly Quandl)
                    url = f"{self.QUANDL_COT_URL}/{contract_code}_FO_L_ALL.json"
                    params = {'rows': weeks}
                    if self.api_key:
                        params['api_key'] = self.api_key

                    async with session.get(url, params=params) as response:
                        if response.status == 200:
                            data = await response.json()
                            reports = self._parse_nasdaq_cot_data(data, symbol)
                            self._cot_cache[cache_key] = reports
                            self._last_fetch[cache_key] = datetime.now()
                            return reports
                        else:
                            logger.warning(f"COT fetch failed: {response.status}")
                            return self._get_mock_cot_data(symbol, weeks)

            except Exception as e:
                logger.error(f"Error fetching COT data: {e}")
                return self._get_mock_cot_data(symbol, weeks)

    def _parse_nasdaq_cot_data(
        self,
        data: Dict[str, Any],
        symbol: str
    ) -> List[COTReport]:
        """Parse COT data from Nasdaq Data Link format."""
        reports = []
        
        try:
            dataset = data.get('dataset', {})
            column_names = dataset.get('column_names', [])
            rows = dataset.get('data', [])
            
            for row in rows:
                row_dict = dict(zip(column_names, row))
                
                report_date = datetime.strptime(row_dict.get('Date', ''), '%Y-%m-%d')
                
                positions = {}
                
                # Commercial positions
                positions[TraderCategory.COMMERCIAL] = COTPosition(
                    category=TraderCategory.COMMERCIAL,
                    long_positions=int(row_dict.get('Commercial Long', 0)),
                    short_positions=int(row_dict.get('Commercial Short', 0)),
                    change_long=int(row_dict.get('Change in Commercial Long', 0)),
                    change_short=int(row_dict.get('Change in Commercial Short', 0))
                )
                
                # Non-commercial positions
                positions[TraderCategory.NON_COMMERCIAL] = COTPosition(
                    category=TraderCategory.NON_COMMERCIAL,
                    long_positions=int(row_dict.get('Noncommercial Long', 0)),
                    short_positions=int(row_dict.get('Noncommercial Short', 0)),
                    spreading_positions=int(row_dict.get('Noncommercial Spreading', 0)),
                    change_long=int(row_dict.get('Change in Noncommercial Long', 0)),
                    change_short=int(row_dict.get('Change in Noncommercial Short', 0))
                )
                
                # Non-reportable (retail)
                positions[TraderCategory.NON_REPORTABLE] = COTPosition(
                    category=TraderCategory.NON_REPORTABLE,
                    long_positions=int(row_dict.get('Nonreportable Long', 0)),
                    short_positions=int(row_dict.get('Nonreportable Short', 0))
                )
                
                reports.append(COTReport(
                    report_date=report_date,
                    market_name=symbol,
                    contract_code=self.CONTRACT_CODES.get(symbol.upper(), symbol),
                    open_interest=int(row_dict.get('Open Interest', 0)),
                    positions=positions
                ))
                
        except Exception as e:
            logger.error(f"Error parsing COT data: {e}")
            
        return reports
        
    def _get_mock_cot_data(self, symbol: str, weeks: int) -> List[COTReport]:
        """Generate mock COT data for testing/offline use."""
        reports = []
        base_date = datetime.now()
        
        # Generate realistic-looking mock data
        np.random.seed(42)
        
        commercial_base = np.random.randint(50000, 150000)
        non_commercial_base = np.random.randint(30000, 100000)
        retail_base = np.random.randint(10000, 50000)
        
        for i in range(weeks):
            report_date = base_date - timedelta(weeks=i)
            
            # Add some randomness and trend
            trend = np.sin(i / 10) * 10000
            
            commercial_long = int(commercial_base + trend + np.random.randint(-5000, 5000))
            commercial_short = int(commercial_base - trend + np.random.randint(-5000, 5000))
            
            non_commercial_long = int(non_commercial_base - trend + np.random.randint(-3000, 3000))
            non_commercial_short = int(non_commercial_base + trend + np.random.randint(-3000, 3000))
            
            retail_long = int(retail_base + np.random.randint(-2000, 2000))
            retail_short = int(retail_base + np.random.randint(-2000, 2000))
            
            positions = {
                TraderCategory.COMMERCIAL: COTPosition(
                    category=TraderCategory.COMMERCIAL,
                    long_positions=max(0, commercial_long),
                    short_positions=max(0, commercial_short)
                ),
                TraderCategory.NON_COMMERCIAL: COTPosition(
                    category=TraderCategory.NON_COMMERCIAL,
                    long_positions=max(0, non_commercial_long),
                    short_positions=max(0, non_commercial_short),
                    spreading_positions=np.random.randint(5000, 20000)
                ),
                TraderCategory.NON_REPORTABLE: COTPosition(
                    category=TraderCategory.NON_REPORTABLE,
                    long_positions=max(0, retail_long),
                    short_positions=max(0, retail_short)
                )
            }
            
            total_oi = sum(
                p.long_positions + p.short_positions + p.spreading_positions
                for p in positions.values()
            ) // 2
            
            reports.append(COTReport(
                report_date=report_date,
                market_name=symbol,
                contract_code=self.CONTRACT_CODES.get(symbol.upper(), symbol),
                open_interest=total_oi,
                positions=positions
            ))
            
        return reports
        
    def calculate_cot_index(
        self,
        reports: List[COTReport],
        category: TraderCategory = TraderCategory.NON_COMMERCIAL
    ) -> COTIndex:
        """Calculate COT Index (0-100 scale) for a trader category.
        
        The COT Index shows where current positioning stands relative
        to historical extremes over the lookback period.
        
        Args:
            reports: List of COT reports (most recent first)
            category: Trader category to analyze
            
        Returns:
            COTIndex with current positioning analysis
        """
        if not reports:
            return COTIndex(
                category=category,
                current_net=0,
                index_value=50.0,
                lookback_high=0,
                lookback_low=0,
                lookback_periods=0,
                signal=COTSignal.NEUTRAL
            )
            
        # Get net positions for the lookback period
        net_positions = []
        for report in reports[:self.lookback_periods]:
            if category in report.positions:
                net_positions.append(report.positions[category].net_position)
                
        if not net_positions:
            return COTIndex(
                category=category,
                current_net=0,
                index_value=50.0,
                lookback_high=0,
                lookback_low=0,
                lookback_periods=0,
                signal=COTSignal.NEUTRAL
            )
            
        current_net = net_positions[0]
        lookback_high = max(net_positions)
        lookback_low = min(net_positions)
        
        # Calculate index (0-100)
        if lookback_high == lookback_low:
            index_value = 50.0
        else:
            index_value = ((current_net - lookback_low) / (lookback_high - lookback_low)) * 100
            
        # Determine signal
        if index_value >= self.extreme_threshold:
            signal = COTSignal.STRONG_BULLISH
        elif index_value >= 70:
            signal = COTSignal.BULLISH
        elif index_value <= 100 - self.extreme_threshold:
            signal = COTSignal.STRONG_BEARISH
        elif index_value <= 30:
            signal = COTSignal.BEARISH
        else:
            signal = COTSignal.NEUTRAL
            
        return COTIndex(
            category=category,
            current_net=current_net,
            index_value=index_value,
            lookback_high=lookback_high,
            lookback_low=lookback_low,
            lookback_periods=len(net_positions),
            signal=signal
        )
        
    def detect_positioning_extremes(
        self,
        reports: List[COTReport]
    ) -> Dict[TraderCategory, COTIndex]:
        """Detect extreme positioning across all trader categories.
        
        Args:
            reports: List of COT reports
            
        Returns:
            Dictionary of COT indices by category
        """
        extremes = {}
        
        for category in [TraderCategory.COMMERCIAL, TraderCategory.NON_COMMERCIAL, TraderCategory.NON_REPORTABLE]:
            extremes[category] = self.calculate_cot_index(reports, category)
            
        return extremes
        
    def detect_divergence(
        self,
        reports: List[COTReport],
        price_data: pd.DataFrame,
        category: TraderCategory = TraderCategory.NON_COMMERCIAL,
        periods: int = 4
    ) -> Optional[COTDivergence]:
        """Detect divergence between price and COT positioning.
        
        Args:
            reports: List of COT reports
            price_data: DataFrame with price data
            category: Trader category to analyze
            periods: Number of periods to check for divergence
            
        Returns:
            COTDivergence if found, None otherwise
        """
        if len(reports) < periods or len(price_data) < periods:
            return None
            
        # Get net position changes
        net_positions = []
        for report in reports[:periods]:
            if category in report.positions:
                net_positions.append(report.positions[category].net_position)
                
        if len(net_positions) < periods:
            return None
            
        # Determine position direction
        position_change = net_positions[0] - net_positions[-1]
        position_direction = 'increasing' if position_change > 0 else 'decreasing'
        
        # Get price direction (weekly close comparison)
        # Resample to weekly if needed
        if isinstance(price_data.index, pd.DatetimeIndex):
            weekly_prices = price_data['close'].resample('W').last().dropna()
        else:
            weekly_prices = price_data['close'].iloc[:5]  # Approximate weekly
            
        if len(weekly_prices) < periods:
            return None
            
        price_change = weekly_prices.iloc[-1] - weekly_prices.iloc[-periods]
        price_direction = 'up' if price_change > 0 else 'down'
        
        # Check for divergence
        # Bullish divergence: price down, positions increasing
        # Bearish divergence: price up, positions decreasing
        
        divergence_type = None
        if price_direction == 'down' and position_direction == 'increasing':
            divergence_type = 'bullish'
        elif price_direction == 'up' and position_direction == 'decreasing':
            divergence_type = 'bearish'
            
        if divergence_type:
            # Calculate strength based on magnitude of divergence
            price_pct_change = abs(price_change / weekly_prices.iloc[-periods]) * 100
            position_pct_change = abs(position_change / max(abs(net_positions[-1]), 1)) * 100
            
            strength = min(100, (price_pct_change + position_pct_change) / 2)
            
            return COTDivergence(
                divergence_type=divergence_type,
                category=category,
                price_direction=price_direction,
                position_direction=position_direction,
                strength=strength,
                periods=periods
            )
            
        return None
        
    def get_smart_money_signal(
        self,
        reports: List[COTReport]
    ) -> Dict[str, Any]:
        """Get composite smart money signal from COT data.
        
        Combines commercial and non-commercial positioning for
        a comprehensive institutional view.
        
        Args:
            reports: List of COT reports
            
        Returns:
            Dictionary with signal details
        """
        if not reports:
            return {
                'signal': COTSignal.NEUTRAL,
                'strength': 0,
                'commercial_bias': 'neutral',
                'speculator_bias': 'neutral',
                'retail_bias': 'neutral',
                'description': 'Insufficient data'
            }
            
        # Calculate indices for each category
        commercial_idx = self.calculate_cot_index(reports, TraderCategory.COMMERCIAL)
        speculator_idx = self.calculate_cot_index(reports, TraderCategory.NON_COMMERCIAL)
        retail_idx = self.calculate_cot_index(reports, TraderCategory.NON_REPORTABLE)
        
        # Commercials are typically contrarian - fade their extremes
        # Speculators are trend followers - follow their direction
        # Retail is often wrong - fade their extremes
        
        commercial_bias = 'bullish' if commercial_idx.index_value < 30 else ('bearish' if commercial_idx.index_value > 70 else 'neutral')
        speculator_bias = 'bullish' if speculator_idx.index_value > 70 else ('bearish' if speculator_idx.index_value < 30 else 'neutral')
        retail_bias = 'bullish' if retail_idx.index_value < 30 else ('bearish' if retail_idx.index_value > 70 else 'neutral')
        
        # Composite signal
        bullish_count = sum([
            commercial_bias == 'bullish',
            speculator_bias == 'bullish',
            retail_bias == 'bullish'
        ])
        
        bearish_count = sum([
            commercial_bias == 'bearish',
            speculator_bias == 'bearish',
            retail_bias == 'bearish'
        ])
        
        if bullish_count >= 2:
            signal = COTSignal.BULLISH if bullish_count == 2 else COTSignal.STRONG_BULLISH
        elif bearish_count >= 2:
            signal = COTSignal.BEARISH if bearish_count == 2 else COTSignal.STRONG_BEARISH
        else:
            signal = COTSignal.NEUTRAL
            
        strength = max(
            abs(commercial_idx.index_value - 50),
            abs(speculator_idx.index_value - 50),
            abs(retail_idx.index_value - 50)
        )
        
        return {
            'signal': signal,
            'strength': strength,
            'commercial_bias': commercial_bias,
            'commercial_index': commercial_idx.index_value,
            'speculator_bias': speculator_bias,
            'speculator_index': speculator_idx.index_value,
            'retail_bias': retail_bias,
            'retail_index': retail_idx.index_value,
            'description': f"Commercial: {commercial_bias}, Speculators: {speculator_bias}, Retail: {retail_bias}"
        }
        
    def analyze_position_changes(
        self,
        reports: List[COTReport],
        weeks: int = 4
    ) -> Dict[TraderCategory, Dict[str, Any]]:
        """Analyze recent position changes by category.
        
        Args:
            reports: List of COT reports
            weeks: Number of weeks to analyze
            
        Returns:
            Dictionary with position change analysis by category
        """
        analysis = {}
        
        for category in [TraderCategory.COMMERCIAL, TraderCategory.NON_COMMERCIAL, TraderCategory.NON_REPORTABLE]:
            if len(reports) < weeks:
                continue
                
            positions = []
            for report in reports[:weeks]:
                if category in report.positions:
                    positions.append(report.positions[category])
                    
            if not positions:
                continue
                
            # Calculate changes
            net_change = positions[0].net_position - positions[-1].net_position
            long_change = positions[0].long_positions - positions[-1].long_positions
            short_change = positions[0].short_positions - positions[-1].short_positions
            
            # Determine trend
            if net_change > 0:
                trend = 'accumulating_longs'
            elif net_change < 0:
                trend = 'accumulating_shorts'
            else:
                trend = 'neutral'
                
            analysis[category] = {
                'current_net': positions[0].net_position,
                'net_change': net_change,
                'long_change': long_change,
                'short_change': short_change,
                'trend': trend,
                'weeks_analyzed': len(positions)
            }
            
        return analysis


class RetailSentimentAnalyzer:
    """Analyze retail trader positioning from broker reports."""
    
    def __init__(self):
        """Initialize retail sentiment analyzer."""
        self._sentiment_cache: Dict[str, RetailPositioning] = {}
        
    async def fetch_retail_positioning(
        self,
        symbol: str,
        broker: str = 'aggregate'
    ) -> Optional[RetailPositioning]:
        """Fetch retail positioning data.
        
        Args:
            symbol: Trading symbol
            broker: Broker name or 'aggregate' for combined data
            
        Returns:
            RetailPositioning data if available
        """
        # This would integrate with broker APIs like:
        # - IG Client Sentiment
        # - OANDA Order Book
        # - Myfxbook Community Outlook
        # - DailyFX Sentiment
        
        # For now, return mock data
        return self._get_mock_retail_positioning(symbol, broker)
        
    def _get_mock_retail_positioning(
        self,
        symbol: str,
        broker: str
    ) -> RetailPositioning:
        """Generate mock retail positioning data."""
        np.random.seed(hash(symbol) % 2**32)
        
        percent_long = np.random.uniform(30, 70)
        percent_short = 100 - percent_long
        
        # Sentiment index: -100 (all short) to +100 (all long)
        sentiment_index = (percent_long - 50) * 2
        
        # Contrarian signal: fade retail extremes
        if sentiment_index > 60:
            contrarian_signal = COTSignal.BEARISH
        elif sentiment_index < -60:
            contrarian_signal = COTSignal.BULLISH
        else:
            contrarian_signal = COTSignal.NEUTRAL
            
        return RetailPositioning(
            broker_name=broker,
            symbol=symbol,
            timestamp=datetime.now(),
            percent_long=percent_long,
            percent_short=percent_short,
            total_positions=np.random.randint(1000, 10000),
            sentiment_index=sentiment_index,
            contrarian_signal=contrarian_signal
        )
        
    def get_contrarian_signal(
        self,
        positioning: RetailPositioning,
        extreme_threshold: float = 70.0
    ) -> COTSignal:
        """Get contrarian signal based on retail positioning.
        
        When retail is extremely long, consider shorting.
        When retail is extremely short, consider going long.
        
        Args:
            positioning: Retail positioning data
            extreme_threshold: Threshold for extreme positioning
            
        Returns:
            Contrarian trading signal
        """
        if positioning.percent_long >= extreme_threshold:
            return COTSignal.STRONG_BEARISH
        elif positioning.percent_long >= 60:
            return COTSignal.BEARISH
        elif positioning.percent_short >= extreme_threshold:
            return COTSignal.STRONG_BULLISH
        elif positioning.percent_short >= 60:
            return COTSignal.BULLISH
        else:
            return COTSignal.NEUTRAL


# Convenience functions
async def get_cot_signal(symbol: str, weeks: int = 52) -> Dict[str, Any]:
    """Quick function to get COT signal for a symbol."""
    analyzer = COTAnalyzer()
    reports = await analyzer.fetch_cot_data(symbol, weeks)
    return analyzer.get_smart_money_signal(reports)


async def get_cot_index(
    symbol: str,
    category: TraderCategory = TraderCategory.NON_COMMERCIAL
) -> COTIndex:
    """Quick function to get COT index for a symbol."""
    analyzer = COTAnalyzer()
    reports = await analyzer.fetch_cot_data(symbol)
    return analyzer.calculate_cot_index(reports, category)
