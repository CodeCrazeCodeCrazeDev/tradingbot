"""
Market Opportunity Discovery Engine
=====================================

Autonomous engine that discovers new market opportunities.
Continuously scans markets, analyzes patterns, and proposes trading opportunities.

Features:
1. Multi-market scanning
2. Pattern recognition
3. Anomaly detection
4. Alpha signal generation
5. Opportunity scoring and ranking

Author: AlphaAlgo Trading System
"""

import asyncio
import json
import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone, timedelta
from enum import Enum, auto
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Set, Tuple
import uuid
import random

logger = logging.getLogger(__name__)


class OpportunityType(Enum):
    """Types of market opportunities."""
    MOMENTUM = "momentum"              # Momentum-based opportunity
    MEAN_REVERSION = "mean_reversion"  # Mean reversion opportunity
    BREAKOUT = "breakout"              # Breakout opportunity
    ARBITRAGE = "arbitrage"            # Arbitrage opportunity
    VOLATILITY = "volatility"          # Volatility-based opportunity
    SENTIMENT = "sentiment"            # Sentiment-driven opportunity
    STRUCTURAL = "structural"          # Market structure opportunity
    SEASONAL = "seasonal"              # Seasonal/calendar opportunity
    CORRELATION = "correlation"        # Correlation-based opportunity
    LIQUIDITY = "liquidity"            # Liquidity-based opportunity


class OpportunityStatus(Enum):
    """Status of an opportunity."""
    DETECTED = auto()        # Just detected
    ANALYZING = auto()       # Under analysis
    VALIDATED = auto()       # Validated as real
    REJECTED = auto()        # Rejected as false positive
    PROPOSED = auto()        # Proposed for trading
    ACTIVE = auto()          # Currently being traded
    EXPIRED = auto()         # Opportunity expired
    COMPLETED = auto()       # Trading completed


class MarketType(Enum):
    """Types of markets."""
    EQUITY = "equity"
    FOREX = "forex"
    CRYPTO = "crypto"
    COMMODITY = "commodity"
    FIXED_INCOME = "fixed_income"
    DERIVATIVES = "derivatives"


@dataclass
class MarketSignal:
    """A market signal detected by the discovery engine."""
    signal_id: str
    signal_type: str
    symbol: str
    market_type: MarketType
    
    # Signal Details
    direction: str  # 'long', 'short', 'neutral'
    strength: float  # 0.0 to 1.0
    confidence: float  # 0.0 to 1.0
    
    # Timing
    detected_at: datetime
    expected_duration: Optional[timedelta] = None
    expiry: Optional[datetime] = None
    
    # Evidence
    indicators: Dict[str, float] = field(default_factory=dict)
    supporting_data: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'signal_id': self.signal_id,
            'signal_type': self.signal_type,
            'symbol': self.symbol,
            'market_type': self.market_type.value,
            'direction': self.direction,
            'strength': self.strength,
            'confidence': self.confidence,
            'detected_at': self.detected_at.isoformat(),
            'expected_duration': str(self.expected_duration) if self.expected_duration else None,
            'expiry': self.expiry.isoformat() if self.expiry else None,
            'indicators': self.indicators,
        }


@dataclass
class Opportunity:
    """A market opportunity discovered by the engine."""
    opportunity_id: str
    opportunity_type: OpportunityType
    
    # Market Details
    symbols: List[str]
    market_type: MarketType
    
    # Opportunity Details
    description: str
    thesis: str
    direction: str  # 'long', 'short', 'spread', 'neutral'
    
    # Scoring
    score: float  # Overall opportunity score (0-100)
    confidence: float  # Confidence level (0-1)
    expected_return: float  # Expected return percentage
    expected_risk: float  # Expected risk (max drawdown)
    sharpe_estimate: float  # Estimated Sharpe ratio
    
    # Timing
    discovered_at: datetime
    valid_until: Optional[datetime] = None
    optimal_entry_window: Optional[Tuple[datetime, datetime]] = None
    
    # Status
    status: OpportunityStatus = OpportunityStatus.DETECTED
    
    # Supporting Evidence
    signals: List[MarketSignal] = field(default_factory=list)
    analysis: Dict[str, Any] = field(default_factory=dict)
    
    # Trading Parameters
    suggested_position_size: float = 0.0
    suggested_entry_price: Optional[float] = None
    suggested_stop_loss: Optional[float] = None
    suggested_take_profit: Optional[float] = None
    
    # Tracking
    experiment_id: Optional[str] = None
    trade_ids: List[str] = field(default_factory=list)
    actual_return: Optional[float] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'opportunity_id': self.opportunity_id,
            'opportunity_type': self.opportunity_type.value,
            'symbols': self.symbols,
            'market_type': self.market_type.value,
            'description': self.description,
            'thesis': self.thesis,
            'direction': self.direction,
            'score': self.score,
            'confidence': self.confidence,
            'expected_return': self.expected_return,
            'expected_risk': self.expected_risk,
            'sharpe_estimate': self.sharpe_estimate,
            'discovered_at': self.discovered_at.isoformat(),
            'valid_until': self.valid_until.isoformat() if self.valid_until else None,
            'status': self.status.name,
            'signals_count': len(self.signals),
            'suggested_position_size': self.suggested_position_size,
        }
    
    def is_valid(self) -> bool:
        """Check if opportunity is still valid."""
        if self.valid_until and datetime.now(timezone.utc) > self.valid_until:
            return False
        return self.status in [
            OpportunityStatus.DETECTED,
            OpportunityStatus.ANALYZING,
            OpportunityStatus.VALIDATED,
            OpportunityStatus.PROPOSED,
        ]


@dataclass
class DiscoveryConfig:
    """Configuration for opportunity discovery."""
    # Scanning
    scan_interval_seconds: int = 60
    markets_to_scan: List[MarketType] = field(default_factory=lambda: [
        MarketType.EQUITY, MarketType.FOREX, MarketType.CRYPTO
    ])
    
    # Thresholds
    min_confidence: float = 0.6
    min_score: float = 50.0
    min_expected_return: float = 0.02  # 2%
    max_expected_risk: float = 0.10    # 10%
    min_sharpe_estimate: float = 1.0
    
    # Limits
    max_active_opportunities: int = 20
    max_opportunities_per_symbol: int = 3
    opportunity_expiry_hours: float = 24.0
    
    # Analysis
    lookback_periods: List[int] = field(default_factory=lambda: [5, 10, 20, 50, 100, 200])
    correlation_threshold: float = 0.7
    volatility_lookback: int = 20
    
    # Storage
    storage_path: str = "opportunity_discovery"


class PatternDetector:
    """Detects patterns in market data."""
    
    def __init__(self):
        self._patterns = {}
    
    async def detect_momentum(
        self,
        symbol: str,
        prices: List[float],
        volumes: Optional[List[float]] = None,
    ) -> Optional[MarketSignal]:
        """Detect momentum patterns."""
        if len(prices) < 20:
            return None
        
        # Calculate momentum indicators
        returns = [(prices[i] - prices[i-1]) / prices[i-1] for i in range(1, len(prices))]
        
        # Simple momentum: recent returns vs historical
        recent_return = sum(returns[-5:]) / 5 if len(returns) >= 5 else 0
        historical_return = sum(returns[-20:-5]) / 15 if len(returns) >= 20 else 0
        
        momentum_strength = abs(recent_return - historical_return)
        
        if momentum_strength > 0.02:  # 2% threshold
            direction = 'long' if recent_return > historical_return else 'short'
            
            return MarketSignal(
                signal_id=f"SIG-{uuid.uuid4().hex[:8]}",
                signal_type='momentum',
                symbol=symbol,
                market_type=MarketType.EQUITY,
                direction=direction,
                strength=min(1.0, momentum_strength * 10),
                confidence=0.6 + min(0.3, momentum_strength * 5),
                detected_at=datetime.now(timezone.utc),
                indicators={
                    'recent_return': recent_return,
                    'historical_return': historical_return,
                    'momentum_strength': momentum_strength,
                },
            )
        
        return None
    
    async def detect_mean_reversion(
        self,
        symbol: str,
        prices: List[float],
    ) -> Optional[MarketSignal]:
        """Detect mean reversion opportunities."""
        if len(prices) < 50:
            return None
        
        # Calculate z-score
        mean_price = sum(prices[-50:]) / 50
        std_price = (sum((p - mean_price) ** 2 for p in prices[-50:]) / 50) ** 0.5
        
        if std_price == 0:
            return None
        
        current_price = prices[-1]
        z_score = (current_price - mean_price) / std_price
        
        if abs(z_score) > 2.0:  # 2 standard deviations
            direction = 'short' if z_score > 0 else 'long'
            
            return MarketSignal(
                signal_id=f"SIG-{uuid.uuid4().hex[:8]}",
                signal_type='mean_reversion',
                symbol=symbol,
                market_type=MarketType.EQUITY,
                direction=direction,
                strength=min(1.0, abs(z_score) / 3),
                confidence=0.5 + min(0.4, abs(z_score) / 5),
                detected_at=datetime.now(timezone.utc),
                indicators={
                    'z_score': z_score,
                    'mean_price': mean_price,
                    'std_price': std_price,
                    'current_price': current_price,
                },
            )
        
        return None
    
    async def detect_breakout(
        self,
        symbol: str,
        prices: List[float],
        volumes: Optional[List[float]] = None,
    ) -> Optional[MarketSignal]:
        """Detect breakout patterns."""
        if len(prices) < 20:
            return None
        
        # Calculate range
        high_20 = max(prices[-20:])
        low_20 = min(prices[-20:])
        range_20 = high_20 - low_20
        
        current_price = prices[-1]
        
        # Check for breakout
        if current_price > high_20 * 0.99:  # Breaking above resistance
            direction = 'long'
            strength = (current_price - high_20) / range_20 if range_20 > 0 else 0
        elif current_price < low_20 * 1.01:  # Breaking below support
            direction = 'short'
            strength = (low_20 - current_price) / range_20 if range_20 > 0 else 0
        else:
            return None
        
        # Volume confirmation
        volume_strength = 1.0
        if volumes and len(volumes) >= 20:
            avg_volume = sum(volumes[-20:]) / 20
            current_volume = volumes[-1]
            volume_strength = min(2.0, current_volume / avg_volume) if avg_volume > 0 else 1.0
        
        return MarketSignal(
            signal_id=f"SIG-{uuid.uuid4().hex[:8]}",
            signal_type='breakout',
            symbol=symbol,
            market_type=MarketType.EQUITY,
            direction=direction,
            strength=min(1.0, strength * volume_strength),
            confidence=0.5 + min(0.4, strength * volume_strength * 0.5),
            detected_at=datetime.now(timezone.utc),
            indicators={
                'high_20': high_20,
                'low_20': low_20,
                'current_price': current_price,
                'volume_strength': volume_strength,
            },
        )


class OpportunityAnalyzer:
    """Analyzes and scores opportunities."""
    
    def __init__(self, config: DiscoveryConfig):
        self.config = config
    
    async def analyze_opportunity(
        self,
        signals: List[MarketSignal],
        market_data: Dict[str, Any],
    ) -> Optional[Opportunity]:
        """Analyze signals and create opportunity if valid."""
        if not signals:
            return None
        
        # Aggregate signals
        primary_signal = max(signals, key=lambda s: s.strength * s.confidence)
        
        # Determine opportunity type
        opp_type = self._determine_opportunity_type(signals)
        
        # Calculate scores
        confidence = self._calculate_confidence(signals)
        expected_return = self._estimate_return(signals, market_data)
        expected_risk = self._estimate_risk(signals, market_data)
        
        if expected_risk == 0:
            sharpe_estimate = 0
        else:
            sharpe_estimate = expected_return / expected_risk
        
        # Calculate overall score
        score = self._calculate_score(
            confidence=confidence,
            expected_return=expected_return,
            expected_risk=expected_risk,
            sharpe_estimate=sharpe_estimate,
            signal_count=len(signals),
        )
        
        # Check thresholds
        if score < self.config.min_score:
            return None
        if confidence < self.config.min_confidence:
            return None
        if expected_return < self.config.min_expected_return:
            return None
        if expected_risk > self.config.max_expected_risk:
            return None
        
        # Create opportunity
        opportunity = Opportunity(
            opportunity_id=f"OPP-{uuid.uuid4().hex[:12]}",
            opportunity_type=opp_type,
            symbols=[s.symbol for s in signals],
            market_type=primary_signal.market_type,
            description=self._generate_description(signals, opp_type),
            thesis=self._generate_thesis(signals, opp_type),
            direction=primary_signal.direction,
            score=score,
            confidence=confidence,
            expected_return=expected_return,
            expected_risk=expected_risk,
            sharpe_estimate=sharpe_estimate,
            discovered_at=datetime.now(timezone.utc),
            valid_until=datetime.now(timezone.utc) + timedelta(hours=self.config.opportunity_expiry_hours),
            signals=signals,
            analysis={
                'signal_types': [s.signal_type for s in signals],
                'avg_strength': sum(s.strength for s in signals) / len(signals),
                'market_data_summary': {k: str(v)[:100] for k, v in market_data.items()},
            },
        )
        
        # Calculate trading parameters
        opportunity.suggested_position_size = self._calculate_position_size(opportunity)
        
        return opportunity
    
    def _determine_opportunity_type(self, signals: List[MarketSignal]) -> OpportunityType:
        """Determine opportunity type from signals."""
        signal_types = [s.signal_type for s in signals]
        
        if 'momentum' in signal_types:
            return OpportunityType.MOMENTUM
        elif 'mean_reversion' in signal_types:
            return OpportunityType.MEAN_REVERSION
        elif 'breakout' in signal_types:
            return OpportunityType.BREAKOUT
        else:
            return OpportunityType.STRUCTURAL
    
    def _calculate_confidence(self, signals: List[MarketSignal]) -> float:
        """Calculate overall confidence from signals."""
        if not signals:
            return 0.0
        
        # Weighted average by strength
        total_weight = sum(s.strength for s in signals)
        if total_weight == 0:
            return 0.0
        
        weighted_confidence = sum(s.confidence * s.strength for s in signals) / total_weight
        
        # Bonus for multiple confirming signals
        confirmation_bonus = min(0.1, len(signals) * 0.02)
        
        return min(1.0, weighted_confidence + confirmation_bonus)
    
    def _estimate_return(self, signals: List[MarketSignal], market_data: Dict) -> float:
        """Estimate expected return."""
        # Simple estimation based on signal strength
        avg_strength = sum(s.strength for s in signals) / len(signals)
        
        # Base return estimate
        base_return = avg_strength * 0.05  # Up to 5% for max strength
        
        return base_return
    
    def _estimate_risk(self, signals: List[MarketSignal], market_data: Dict) -> float:
        """Estimate expected risk (max drawdown)."""
        # Simple risk estimation
        avg_confidence = sum(s.confidence for s in signals) / len(signals)
        
        # Higher confidence = lower risk estimate
        base_risk = 0.10 * (1 - avg_confidence * 0.5)
        
        return base_risk
    
    def _calculate_score(
        self,
        confidence: float,
        expected_return: float,
        expected_risk: float,
        sharpe_estimate: float,
        signal_count: int,
    ) -> float:
        """Calculate overall opportunity score (0-100)."""
        score = 0.0
        
        # Confidence contribution (0-30)
        score += confidence * 30
        
        # Return/Risk contribution (0-30)
        if expected_risk > 0:
            risk_adjusted = expected_return / expected_risk
            score += min(30, risk_adjusted * 10)
        
        # Sharpe contribution (0-25)
        score += min(25, sharpe_estimate * 10)
        
        # Signal confirmation (0-15)
        score += min(15, signal_count * 5)
        
        return min(100, score)
    
    def _generate_description(self, signals: List[MarketSignal], opp_type: OpportunityType) -> str:
        """Generate opportunity description."""
        symbols = list(set(s.symbol for s in signals))
        direction = signals[0].direction if signals else 'neutral'
        
        return f"{opp_type.value.replace('_', ' ').title()} opportunity in {', '.join(symbols)} ({direction})"
    
    def _generate_thesis(self, signals: List[MarketSignal], opp_type: OpportunityType) -> str:
        """Generate investment thesis."""
        if opp_type == OpportunityType.MOMENTUM:
            return "Strong momentum detected with confirming signals suggesting continuation"
        elif opp_type == OpportunityType.MEAN_REVERSION:
            return "Price deviation from mean suggests reversion opportunity"
        elif opp_type == OpportunityType.BREAKOUT:
            return "Price breaking key levels with volume confirmation"
        else:
            return "Multiple signals indicate trading opportunity"
    
    def _calculate_position_size(self, opportunity: Opportunity) -> float:
        """Calculate suggested position size."""
        # Risk-based position sizing
        base_size = 0.02  # 2% base
        
        # Adjust for confidence
        confidence_factor = opportunity.confidence
        
        # Adjust for risk
        risk_factor = 1 - min(1, opportunity.expected_risk * 5)
        
        return base_size * confidence_factor * risk_factor


class MarketOpportunityDiscovery:
    """
    Autonomous market opportunity discovery engine.
    
    Continuously scans markets, detects patterns, and discovers
    trading opportunities. All discoveries are validated and
    scored before being proposed for trading.
    """
    
    def __init__(self, config: Optional[DiscoveryConfig] = None):
        """
        Initialize the discovery engine.
        
        Args:
            config: Discovery configuration
        """
        self.config = config or DiscoveryConfig()
        
        self._pattern_detector = PatternDetector()
        self._analyzer = OpportunityAnalyzer(self.config)
        
        # Opportunities
        self._opportunities: Dict[str, Opportunity] = {}
        self._signals: Dict[str, MarketSignal] = {}
        
        # Indices
        self._by_status: Dict[OpportunityStatus, Set[str]] = {s: set() for s in OpportunityStatus}
        self._by_symbol: Dict[str, Set[str]] = {}
        self._by_type: Dict[OpportunityType, Set[str]] = {t: set() for t in OpportunityType}
        
        # Callbacks
        self._discovery_callbacks: List[Callable] = []
        
        # Running state
        self._is_running = False
        self._scan_task: Optional[asyncio.Task] = None
        
        # Statistics
        self._stats = {
            'total_scans': 0,
            'signals_detected': 0,
            'opportunities_created': 0,
            'opportunities_validated': 0,
        }
        
        # Storage
        self._storage_path = Path(self.config.storage_path)
        self._storage_path.mkdir(parents=True, exist_ok=True)
        
        logger.info("MarketOpportunityDiscovery initialized")
    
    async def start(self):
        """Start the discovery engine."""
        self._is_running = True
        self._scan_task = asyncio.create_task(self._scan_loop())
        logger.info("MarketOpportunityDiscovery started")
    
    async def stop(self):
        """Stop the discovery engine."""
        self._is_running = False
        if self._scan_task:
            self._scan_task.cancel()
            try:
                await self._scan_task
            except asyncio.CancelledError:
                pass
        logger.info("MarketOpportunityDiscovery stopped")
    
    async def _scan_loop(self):
        """Main scanning loop."""
        while self._is_running:
            try:
                await self._perform_scan()
                await self._cleanup_expired()
                await asyncio.sleep(self.config.scan_interval_seconds)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Scan error: {e}")
                await asyncio.sleep(60)
    
    async def _perform_scan(self):
        """Perform a market scan."""
        self._stats['total_scans'] += 1
        
        # Get market data (simulated for now)
        market_data = await self._get_market_data()
        
        # Detect signals
        signals = []
        
        for symbol, data in market_data.items():
            prices = data.get('prices', [])
            volumes = data.get('volumes')
            
            # Run pattern detectors
            momentum_signal = await self._pattern_detector.detect_momentum(symbol, prices, volumes)
            if momentum_signal:
                signals.append(momentum_signal)
                self._signals[momentum_signal.signal_id] = momentum_signal
            
            reversion_signal = await self._pattern_detector.detect_mean_reversion(symbol, prices)
            if reversion_signal:
                signals.append(reversion_signal)
                self._signals[reversion_signal.signal_id] = reversion_signal
            
            breakout_signal = await self._pattern_detector.detect_breakout(symbol, prices, volumes)
            if breakout_signal:
                signals.append(breakout_signal)
                self._signals[breakout_signal.signal_id] = breakout_signal
        
        self._stats['signals_detected'] += len(signals)
        
        # Group signals by symbol
        signals_by_symbol: Dict[str, List[MarketSignal]] = {}
        for signal in signals:
            if signal.symbol not in signals_by_symbol:
                signals_by_symbol[signal.symbol] = []
            signals_by_symbol[signal.symbol].append(signal)
        
        # Analyze and create opportunities
        for symbol, symbol_signals in signals_by_symbol.items():
            # Check limits
            existing = len(self._by_symbol.get(symbol, set()))
            if existing >= self.config.max_opportunities_per_symbol:
                continue
            
            if len(self._by_status[OpportunityStatus.DETECTED]) >= self.config.max_active_opportunities:
                continue
            
            # Analyze
            opportunity = await self._analyzer.analyze_opportunity(
                symbol_signals,
                market_data.get(symbol, {}),
            )
            
            if opportunity:
                await self._register_opportunity(opportunity)
    
    async def _get_market_data(self) -> Dict[str, Dict]:
        """Get market data for scanning (simulated)."""
        # In production, this would fetch real market data
        symbols = ['AAPL', 'GOOGL', 'MSFT', 'AMZN', 'TSLA', 'BTC-USD', 'ETH-USD', 'EUR-USD']
        
        market_data = {}
        for symbol in symbols:
            # Generate simulated price data
            base_price = random.uniform(100, 500)
            prices = [base_price]
            
            for _ in range(99):
                change = random.gauss(0, 0.02)
                prices.append(prices[-1] * (1 + change))
            
            volumes = [random.uniform(1000000, 10000000) for _ in range(100)]
            
            market_data[symbol] = {
                'prices': prices,
                'volumes': volumes,
                'timestamp': datetime.now(timezone.utc).isoformat(),
            }
        
        return market_data
    
    async def _register_opportunity(self, opportunity: Opportunity):
        """Register a new opportunity."""
        self._opportunities[opportunity.opportunity_id] = opportunity
        
        # Update indices
        self._by_status[OpportunityStatus.DETECTED].add(opportunity.opportunity_id)
        self._by_type[opportunity.opportunity_type].add(opportunity.opportunity_id)
        
        for symbol in opportunity.symbols:
            if symbol not in self._by_symbol:
                self._by_symbol[symbol] = set()
            self._by_symbol[symbol].add(opportunity.opportunity_id)
        
        self._stats['opportunities_created'] += 1
        
        # Notify callbacks
        for callback in self._discovery_callbacks:
            try:
                await callback(opportunity)
            except Exception as e:
                logger.error(f"Discovery callback error: {e}")
        
        # Persist
        await self._persist_opportunity(opportunity)
        
        logger.info(
            f"Discovered opportunity: {opportunity.opportunity_id} - "
            f"{opportunity.opportunity_type.value} in {opportunity.symbols} "
            f"(score={opportunity.score:.1f})"
        )
    
    async def validate_opportunity(
        self,
        opportunity_id: str,
        validation_results: Dict[str, Any],
    ) -> bool:
        """
        Validate an opportunity.
        
        Args:
            opportunity_id: Opportunity ID
            validation_results: Validation results
        
        Returns:
            True if validated successfully
        """
        opportunity = self._opportunities.get(opportunity_id)
        if not opportunity:
            return False
        
        passed = validation_results.get('passed', False)
        
        if passed:
            await self._update_status(opportunity_id, OpportunityStatus.VALIDATED)
            self._stats['opportunities_validated'] += 1
        else:
            await self._update_status(opportunity_id, OpportunityStatus.REJECTED)
        
        opportunity.analysis['validation'] = validation_results
        
        return passed
    
    async def propose_opportunity(self, opportunity_id: str) -> bool:
        """Propose an opportunity for trading."""
        opportunity = self._opportunities.get(opportunity_id)
        if not opportunity:
            return False
        
        if opportunity.status != OpportunityStatus.VALIDATED:
            return False
        
        await self._update_status(opportunity_id, OpportunityStatus.PROPOSED)
        
        return True
    
    async def _update_status(self, opportunity_id: str, new_status: OpportunityStatus):
        """Update opportunity status."""
        opportunity = self._opportunities.get(opportunity_id)
        if not opportunity:
            return
        
        old_status = opportunity.status
        
        self._by_status[old_status].discard(opportunity_id)
        self._by_status[new_status].add(opportunity_id)
        
        opportunity.status = new_status
    
    async def _cleanup_expired(self):
        """Clean up expired opportunities."""
        now = datetime.now(timezone.utc)
        
        for opp_id, opportunity in list(self._opportunities.items()):
            if opportunity.valid_until and now > opportunity.valid_until:
                if opportunity.status not in [OpportunityStatus.ACTIVE, OpportunityStatus.COMPLETED]:
                    await self._update_status(opp_id, OpportunityStatus.EXPIRED)
    
    async def _persist_opportunity(self, opportunity: Opportunity):
        """Persist opportunity to disk."""
        try:
            opp_file = self._storage_path / f"{opportunity.opportunity_id}.json"
            with open(opp_file, 'w') as f:
                json.dump(opportunity.to_dict(), f, indent=2)
        except Exception as e:
            logger.error(f"Failed to persist opportunity: {e}")
    
    def get_opportunity(self, opportunity_id: str) -> Optional[Opportunity]:
        """Get opportunity by ID."""
        return self._opportunities.get(opportunity_id)
    
    def get_opportunities_by_status(self, status: OpportunityStatus) -> List[Opportunity]:
        """Get opportunities by status."""
        return [self._opportunities[oid] for oid in self._by_status.get(status, set())]
    
    def get_opportunities_by_type(self, opp_type: OpportunityType) -> List[Opportunity]:
        """Get opportunities by type."""
        return [self._opportunities[oid] for oid in self._by_type.get(opp_type, set())]
    
    def get_top_opportunities(self, limit: int = 10) -> List[Opportunity]:
        """Get top opportunities by score."""
        valid_opps = [
            opp for opp in self._opportunities.values()
            if opp.is_valid()
        ]
        
        return sorted(valid_opps, key=lambda o: o.score, reverse=True)[:limit]
    
    def register_discovery_callback(self, callback: Callable):
        """Register callback for new discoveries."""
        self._discovery_callbacks.append(callback)
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get discovery statistics."""
        status_counts = {s.name: len(ids) for s, ids in self._by_status.items()}
        type_counts = {t.value: len(ids) for t, ids in self._by_type.items()}
        
        return {
            **self._stats,
            'total_opportunities': len(self._opportunities),
            'total_signals': len(self._signals),
            'by_status': status_counts,
            'by_type': type_counts,
            'unique_symbols': len(self._by_symbol),
        }
