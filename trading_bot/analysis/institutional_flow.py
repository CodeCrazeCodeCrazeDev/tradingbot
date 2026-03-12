"""
Institutional Flow Tracker

Tracks and analyzes institutional trading activity:
- 13F filings analysis
- Institutional ownership changes
- Hedge fund position tracking
- Smart money flow detection
- Whale alert system
"""

import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Set, Tuple
from dataclasses import dataclass, field
from enum import Enum
from collections import defaultdict
import statistics

logger = logging.getLogger(__name__)


class InstitutionType(Enum):
    """Types of institutional investors."""
    HEDGE_FUND = "hedge_fund"
    MUTUAL_FUND = "mutual_fund"
    PENSION_FUND = "pension_fund"
    INSURANCE = "insurance"
    BANK = "bank"
    SOVEREIGN_WEALTH = "sovereign_wealth"
    FAMILY_OFFICE = "family_office"
    ENDOWMENT = "endowment"
    OTHER = "other"


class PositionChange(Enum):
    """Types of position changes."""
    NEW_POSITION = "new_position"
    INCREASED = "increased"
    DECREASED = "decreased"
    CLOSED = "closed"
    UNCHANGED = "unchanged"


class FlowSignal(Enum):
    """Institutional flow signals."""
    STRONG_ACCUMULATION = "strong_accumulation"
    ACCUMULATION = "accumulation"
    NEUTRAL = "neutral"
    DISTRIBUTION = "distribution"
    STRONG_DISTRIBUTION = "strong_distribution"


@dataclass
class Institution:
    """Represents an institutional investor."""
    cik: str  # SEC Central Index Key
    name: str
    institution_type: InstitutionType
    aum: float = 0.0  # Assets Under Management
    filing_date: Optional[datetime] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'cik': self.cik,
            'name': self.name,
            'type': self.institution_type.value,
            'aum': self.aum
        }


@dataclass
class InstitutionalHolding:
    """Represents an institutional holding from 13F filing."""
    institution: Institution
    symbol: str
    shares: int
    value: float
    filing_date: datetime
    report_date: datetime  # Quarter end date
    previous_shares: int = 0
    previous_value: float = 0.0
    
    @property
    def share_change(self) -> int:
        return self.shares - self.previous_shares
    
    @property
    def share_change_pct(self) -> float:
        try:
            if self.previous_shares > 0:
                return (self.shares - self.previous_shares) / self.previous_shares
            return 1.0 if self.shares > 0 else 0.0
        except Exception as e:
            logger.error(f"Error in share_change_pct: {e}")
            raise
    
    @property
    def position_change(self) -> PositionChange:
        try:
            if self.previous_shares == 0 and self.shares > 0:
                return PositionChange.NEW_POSITION
            elif self.shares == 0 and self.previous_shares > 0:
                return PositionChange.CLOSED
            elif self.shares > self.previous_shares:
                return PositionChange.INCREASED
            elif self.shares < self.previous_shares:
                return PositionChange.DECREASED
            else:
                return PositionChange.UNCHANGED
        except Exception as e:
            logger.error(f"Error in position_change: {e}")
            raise
    
    @property
    def is_significant_change(self) -> bool:
        return abs(self.share_change_pct) > 0.1 or abs(self.share_change) > 100000
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'institution': self.institution.name,
            'institution_type': self.institution.institution_type.value,
            'symbol': self.symbol,
            'shares': self.shares,
            'value': self.value,
            'previous_shares': self.previous_shares,
            'share_change': self.share_change,
            'share_change_pct': self.share_change_pct,
            'position_change': self.position_change.value,
            'filing_date': self.filing_date.isoformat(),
            'report_date': self.report_date.isoformat()
        }


@dataclass
class WhaleAlert:
    """Alert for significant institutional activity."""
    timestamp: datetime
    symbol: str
    institution: Institution
    alert_type: str
    shares: int
    value: float
    change_pct: float
    description: str
    significance: str  # 'HIGH', 'MEDIUM', 'LOW'
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'timestamp': self.timestamp.isoformat(),
            'symbol': self.symbol,
            'institution': self.institution.name,
            'alert_type': self.alert_type,
            'shares': self.shares,
            'value': self.value,
            'change_pct': self.change_pct,
            'description': self.description,
            'significance': self.significance
        }


@dataclass
class InstitutionalFlowSignal:
    """Institutional flow trading signal."""
    symbol: str
    signal: FlowSignal
    confidence: float
    total_institutional_shares: int
    total_institutional_value: float
    institution_count: int
    net_share_change: int
    buyers: int
    sellers: int
    new_positions: int
    closed_positions: int
    top_buyers: List[Dict[str, Any]]
    top_sellers: List[Dict[str, Any]]
    smart_money_flow: float  # Weighted by institution quality
    analysis: str
    generated_at: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'symbol': self.symbol,
            'signal': self.signal.value,
            'confidence': self.confidence,
            'total_institutional_shares': self.total_institutional_shares,
            'total_institutional_value': self.total_institutional_value,
            'institution_count': self.institution_count,
            'net_share_change': self.net_share_change,
            'buyers': self.buyers,
            'sellers': self.sellers,
            'new_positions': self.new_positions,
            'closed_positions': self.closed_positions,
            'top_buyers': self.top_buyers,
            'top_sellers': self.top_sellers,
            'smart_money_flow': self.smart_money_flow,
            'analysis': self.analysis,
            'generated_at': self.generated_at.isoformat()
        }


# Notable institutions to track (smart money)
NOTABLE_INSTITUTIONS = {
    "BERKSHIRE HATHAWAY": {"weight": 2.0, "type": InstitutionType.HEDGE_FUND},
    "BRIDGEWATER": {"weight": 1.8, "type": InstitutionType.HEDGE_FUND},
    "RENAISSANCE TECHNOLOGIES": {"weight": 1.9, "type": InstitutionType.HEDGE_FUND},
    "CITADEL": {"weight": 1.7, "type": InstitutionType.HEDGE_FUND},
    "TWO SIGMA": {"weight": 1.7, "type": InstitutionType.HEDGE_FUND},
    "DE SHAW": {"weight": 1.6, "type": InstitutionType.HEDGE_FUND},
    "MILLENNIUM": {"weight": 1.6, "type": InstitutionType.HEDGE_FUND},
    "POINT72": {"weight": 1.5, "type": InstitutionType.HEDGE_FUND},
    "TIGER GLOBAL": {"weight": 1.5, "type": InstitutionType.HEDGE_FUND},
    "COATUE": {"weight": 1.4, "type": InstitutionType.HEDGE_FUND},
    "VANGUARD": {"weight": 1.2, "type": InstitutionType.MUTUAL_FUND},
    "BLACKROCK": {"weight": 1.2, "type": InstitutionType.MUTUAL_FUND},
    "STATE STREET": {"weight": 1.1, "type": InstitutionType.MUTUAL_FUND},
    "FIDELITY": {"weight": 1.2, "type": InstitutionType.MUTUAL_FUND},
    "T ROWE PRICE": {"weight": 1.1, "type": InstitutionType.MUTUAL_FUND},
}


class InstitutionClassifier:
    """Classifies and scores institutions."""
    
    def __init__(self):
        try:
            self.notable = NOTABLE_INSTITUTIONS
        except Exception as e:
            logger.error(f"Error in __init__: {e}")
            raise
    
    def get_weight(self, institution: Institution) -> float:
        """Get institution weight for smart money calculation."""
        # Check if notable
        try:
            for name, info in self.notable.items():
                if name.lower() in institution.name.lower():
                    return info["weight"]
        
            # Default weights by type
            type_weights = {
                InstitutionType.HEDGE_FUND: 1.3,
                InstitutionType.FAMILY_OFFICE: 1.2,
                InstitutionType.SOVEREIGN_WEALTH: 1.1,
                InstitutionType.MUTUAL_FUND: 1.0,
                InstitutionType.PENSION_FUND: 0.9,
                InstitutionType.INSURANCE: 0.8,
                InstitutionType.BANK: 0.8,
                InstitutionType.ENDOWMENT: 0.9,
                InstitutionType.OTHER: 0.7,
            }
        
            return type_weights.get(institution.institution_type, 1.0)
        except Exception as e:
            logger.error(f"Error in get_weight: {e}")
            raise
    
    def is_smart_money(self, institution: Institution) -> bool:
        """Check if institution is considered smart money."""
        try:
            for name in self.notable:
                if name.lower() in institution.name.lower():
                    return True
            return institution.institution_type == InstitutionType.HEDGE_FUND
        except Exception as e:
            logger.error(f"Error in is_smart_money: {e}")
            raise


class InstitutionalFlowTracker:
    """
    Tracks and analyzes institutional trading flow.
    """
    
    def __init__(self, config: Optional[Dict] = None):
        try:
            self.config = config or {}
            self.classifier = InstitutionClassifier()
        
            # Storage
            self.holdings: Dict[str, List[InstitutionalHolding]] = defaultdict(list)
            self.institutions: Dict[str, Institution] = {}
            self.alerts: List[WhaleAlert] = []
        
            # Alert thresholds
            self.new_position_threshold = self.config.get('new_position_threshold', 1000000)
            self.change_threshold = self.config.get('change_threshold', 0.25)
        
            logger.info("InstitutionalFlowTracker initialized")
        except Exception as e:
            logger.error(f"Error in __init__: {e}")
            raise
    
    def add_institution(self, institution: Institution):
        """Register an institution."""
        try:
            self.institutions[institution.cik] = institution
        except Exception as e:
            logger.error(f"Error in add_institution: {e}")
            raise
    
    def add_holding(self, holding: InstitutionalHolding):
        """
        Add or update an institutional holding.
        
        Args:
            holding: Institutional holding to add
        """
        try:
            symbol = holding.symbol
        
            # Store holding
            self.holdings[symbol].append(holding)
        
            # Check for whale alerts
            self._check_whale_alert(holding)
        except Exception as e:
            logger.error(f"Error in add_holding: {e}")
            raise
    
    def _check_whale_alert(self, holding: InstitutionalHolding):
        """Check if holding change warrants a whale alert."""
        try:
            alerts = []
        
            # New large position
            if holding.position_change == PositionChange.NEW_POSITION:
                if holding.value >= self.new_position_threshold:
                    alerts.append(WhaleAlert(
                        timestamp=datetime.now(),
                        symbol=holding.symbol,
                        institution=holding.institution,
                        alert_type="NEW_LARGE_POSITION",
                        shares=holding.shares,
                        value=holding.value,
                        change_pct=1.0,
                        description=f"{holding.institution.name} opened new position: {holding.shares:,} shares (${holding.value:,.0f})",
                        significance="HIGH" if holding.value >= 10000000 else "MEDIUM"
                    ))
        
            # Large increase
            elif holding.position_change == PositionChange.INCREASED:
                if holding.share_change_pct >= self.change_threshold:
                    alerts.append(WhaleAlert(
                        timestamp=datetime.now(),
                        symbol=holding.symbol,
                        institution=holding.institution,
                        alert_type="LARGE_INCREASE",
                        shares=holding.share_change,
                        value=holding.value - holding.previous_value,
                        change_pct=holding.share_change_pct,
                        description=f"{holding.institution.name} increased position by {holding.share_change_pct:.0%}",
                        significance="HIGH" if holding.share_change_pct >= 0.5 else "MEDIUM"
                    ))
        
            # Large decrease
            elif holding.position_change == PositionChange.DECREASED:
                if abs(holding.share_change_pct) >= self.change_threshold:
                    alerts.append(WhaleAlert(
                        timestamp=datetime.now(),
                        symbol=holding.symbol,
                        institution=holding.institution,
                        alert_type="LARGE_DECREASE",
                        shares=abs(holding.share_change),
                        value=abs(holding.value - holding.previous_value),
                        change_pct=holding.share_change_pct,
                        description=f"{holding.institution.name} decreased position by {abs(holding.share_change_pct):.0%}",
                        significance="HIGH" if abs(holding.share_change_pct) >= 0.5 else "MEDIUM"
                    ))
        
            # Position closed
            elif holding.position_change == PositionChange.CLOSED:
                if holding.previous_value >= self.new_position_threshold:
                    alerts.append(WhaleAlert(
                        timestamp=datetime.now(),
                        symbol=holding.symbol,
                        institution=holding.institution,
                        alert_type="POSITION_CLOSED",
                        shares=holding.previous_shares,
                        value=holding.previous_value,
                        change_pct=-1.0,
                        description=f"{holding.institution.name} closed entire position",
                        significance="HIGH"
                    ))
        
            # Add alerts
            self.alerts.extend(alerts)
        
            # Log significant alerts
            for alert in alerts:
                if alert.significance == "HIGH":
                    logger.warning(f"WHALE ALERT: {alert.description}")
        except Exception as e:
            logger.error(f"Error in _check_whale_alert: {e}")
            raise
    
    def generate_signal(self, symbol: str) -> InstitutionalFlowSignal:
        """
        Generate institutional flow signal for a symbol.
        
        Args:
            symbol: Stock symbol
            
        Returns:
            InstitutionalFlowSignal with analysis
        """
        try:
            holdings = self.holdings.get(symbol, [])
        
            if not holdings:
                return InstitutionalFlowSignal(
                    symbol=symbol,
                    signal=FlowSignal.NEUTRAL,
                    confidence=0.0,
                    total_institutional_shares=0,
                    total_institutional_value=0.0,
                    institution_count=0,
                    net_share_change=0,
                    buyers=0,
                    sellers=0,
                    new_positions=0,
                    closed_positions=0,
                    top_buyers=[],
                    top_sellers=[],
                    smart_money_flow=0.0,
                    analysis="No institutional data available"
                )
        
            # Get most recent holdings per institution
            latest_holdings = self._get_latest_holdings(holdings)
        
            # Calculate metrics
            total_shares = sum(h.shares for h in latest_holdings)
            total_value = sum(h.value for h in latest_holdings)
            institution_count = len(latest_holdings)
        
            # Categorize changes
            buyers = [h for h in latest_holdings if h.position_change in [PositionChange.NEW_POSITION, PositionChange.INCREASED]]
            sellers = [h for h in latest_holdings if h.position_change in [PositionChange.CLOSED, PositionChange.DECREASED]]
            new_positions = [h for h in latest_holdings if h.position_change == PositionChange.NEW_POSITION]
            closed_positions = [h for h in latest_holdings if h.position_change == PositionChange.CLOSED]
        
            # Net share change
            net_change = sum(h.share_change for h in latest_holdings)
        
            # Smart money flow (weighted by institution quality)
            smart_money_flow = 0.0
            for h in latest_holdings:
                weight = self.classifier.get_weight(h.institution)
                smart_money_flow += h.share_change * weight
        
            # Top buyers and sellers
            top_buyers = sorted(buyers, key=lambda x: x.share_change, reverse=True)[:5]
            top_sellers = sorted(sellers, key=lambda x: x.share_change)[:5]
        
            # Determine signal
            signal, confidence = self._determine_signal(
                len(buyers), len(sellers), net_change, smart_money_flow, total_shares
            )
        
            # Generate analysis
            analysis = self._generate_analysis(
                len(buyers), len(sellers), net_change, smart_money_flow,
                len(new_positions), len(closed_positions)
            )
        
            return InstitutionalFlowSignal(
                symbol=symbol,
                signal=signal,
                confidence=confidence,
                total_institutional_shares=total_shares,
                total_institutional_value=total_value,
                institution_count=institution_count,
                net_share_change=net_change,
                buyers=len(buyers),
                sellers=len(sellers),
                new_positions=len(new_positions),
                closed_positions=len(closed_positions),
                top_buyers=[h.to_dict() for h in top_buyers],
                top_sellers=[h.to_dict() for h in top_sellers],
                smart_money_flow=smart_money_flow,
                analysis=analysis
            )
        except Exception as e:
            logger.error(f"Error in generate_signal: {e}")
            raise
    
    def _get_latest_holdings(self, holdings: List[InstitutionalHolding]) -> List[InstitutionalHolding]:
        """Get most recent holding per institution."""
        try:
            latest: Dict[str, InstitutionalHolding] = {}
        
            for h in holdings:
                key = h.institution.cik
                if key not in latest or h.filing_date > latest[key].filing_date:
                    latest[key] = h
        
            return list(latest.values())
        except Exception as e:
            logger.error(f"Error in _get_latest_holdings: {e}")
            raise
    
    def _determine_signal(
        self,
        buyers: int,
        sellers: int,
        net_change: int,
        smart_money_flow: float,
        total_shares: int
    ) -> Tuple[FlowSignal, float]:
        """Determine signal and confidence."""
        try:
            confidence = 0.5
        
            # Buyer/seller ratio
            total = buyers + sellers
            if total > 0:
                buyer_ratio = buyers / total
            else:
                buyer_ratio = 0.5
        
            # Net change ratio
            if total_shares > 0:
                change_ratio = net_change / total_shares
            else:
                change_ratio = 0
        
            # Smart money direction
            smart_direction = 1 if smart_money_flow > 0 else -1 if smart_money_flow < 0 else 0
        
            # Determine signal
            if buyer_ratio > 0.7 and change_ratio > 0.05:
                signal = FlowSignal.STRONG_ACCUMULATION
                confidence = min(1.0, buyer_ratio)
            elif buyer_ratio > 0.55 and change_ratio > 0:
                signal = FlowSignal.ACCUMULATION
                confidence = min(0.8, buyer_ratio)
            elif buyer_ratio < 0.3 and change_ratio < -0.05:
                signal = FlowSignal.STRONG_DISTRIBUTION
                confidence = min(1.0, 1 - buyer_ratio)
            elif buyer_ratio < 0.45 and change_ratio < 0:
                signal = FlowSignal.DISTRIBUTION
                confidence = min(0.8, 1 - buyer_ratio)
            else:
                signal = FlowSignal.NEUTRAL
                confidence = 0.5
        
            # Adjust confidence based on smart money alignment
            if smart_direction != 0:
                if (signal in [FlowSignal.ACCUMULATION, FlowSignal.STRONG_ACCUMULATION] and smart_direction > 0) or \
                   (signal in [FlowSignal.DISTRIBUTION, FlowSignal.STRONG_DISTRIBUTION] and smart_direction < 0):
                    confidence = min(1.0, confidence + 0.1)
        
            return signal, confidence
        except Exception as e:
            logger.error(f"Error in _determine_signal: {e}")
            raise
    
    def _generate_analysis(
        self,
        buyers: int,
        sellers: int,
        net_change: int,
        smart_money_flow: float,
        new_positions: int,
        closed_positions: int
    ) -> str:
        """Generate analysis text."""
        try:
            parts = []
        
            parts.append(f"Buyers: {buyers}, Sellers: {sellers}")
        
            if net_change > 0:
                parts.append(f"Net buying: {net_change:,} shares")
            elif net_change < 0:
                parts.append(f"Net selling: {abs(net_change):,} shares")
        
            if smart_money_flow > 0:
                parts.append("Smart money: BUYING")
            elif smart_money_flow < 0:
                parts.append("Smart money: SELLING")
        
            if new_positions > 0:
                parts.append(f"New positions: {new_positions}")
            if closed_positions > 0:
                parts.append(f"Closed positions: {closed_positions}")
        
            return " | ".join(parts)
        except Exception as e:
            logger.error(f"Error in _generate_analysis: {e}")
            raise
    
    def get_whale_alerts(
        self,
        symbol: Optional[str] = None,
        hours: int = 24,
        significance: Optional[str] = None
    ) -> List[WhaleAlert]:
        """Get recent whale alerts."""
        try:
            cutoff = datetime.now() - timedelta(hours=hours)
        
            alerts = [a for a in self.alerts if a.timestamp >= cutoff]
        
            if symbol:
                alerts = [a for a in alerts if a.symbol == symbol]
        
            if significance:
                alerts = [a for a in alerts if a.significance == significance]
        
            return sorted(alerts, key=lambda x: x.timestamp, reverse=True)
        except Exception as e:
            logger.error(f"Error in get_whale_alerts: {e}")
            raise
    
    def get_smart_money_positions(self, symbol: str) -> List[InstitutionalHolding]:
        """Get positions held by smart money institutions."""
        try:
            holdings = self.holdings.get(symbol, [])
            latest = self._get_latest_holdings(holdings)
        
            return [h for h in latest if self.classifier.is_smart_money(h.institution)]
        except Exception as e:
            logger.error(f"Error in get_smart_money_positions: {e}")
            raise
    
    def get_status(self) -> Dict[str, Any]:
        """Get tracker status."""
        return {
            'symbols_tracked': len(self.holdings),
            'institutions_tracked': len(self.institutions),
            'total_holdings': sum(len(h) for h in self.holdings.values()),
            'pending_alerts': len(self.alerts),
            'timestamp': datetime.now().isoformat()
        }


# Factory function
def create_institutional_tracker(config: Optional[Dict] = None) -> InstitutionalFlowTracker:
    """Create InstitutionalFlowTracker instance."""
    return InstitutionalFlowTracker(config)


# Example usage
if __name__ == "__main__":
    tracker = create_institutional_tracker()
    
    # Create sample institutions
    institutions = [
        Institution("0001", "BERKSHIRE HATHAWAY INC", InstitutionType.HEDGE_FUND, 700000000000),
        Institution("0002", "VANGUARD GROUP INC", InstitutionType.MUTUAL_FUND, 8000000000000),
        Institution("0003", "BLACKROCK INC", InstitutionType.MUTUAL_FUND, 10000000000000),
        Institution("0004", "RENAISSANCE TECHNOLOGIES LLC", InstitutionType.HEDGE_FUND, 130000000000),
        Institution("0005", "CITADEL ADVISORS LLC", InstitutionType.HEDGE_FUND, 50000000000),
    ]
    
    for inst in institutions:
        tracker.add_institution(inst)
    
    # Add sample holdings
    symbol = "AAPL"
    
    for i, inst in enumerate(institutions):
        # Previous quarter
        prev_shares = 1000000 + i * 500000
        
        # Current quarter (simulate changes)
        if i < 3:  # Buyers
            curr_shares = int(prev_shares * 1.2)
        else:  # Sellers
            curr_shares = int(prev_shares * 0.8)
        
        holding = InstitutionalHolding(
            institution=inst,
            symbol=symbol,
            shares=curr_shares,
            value=curr_shares * 150,
            filing_date=datetime.now(),
            report_date=datetime.now() - timedelta(days=45),
            previous_shares=prev_shares,
            previous_value=prev_shares * 145
        )
        
        tracker.add_holding(holding)
    
    # Generate signal
    signal = tracker.generate_signal(symbol)
    
    print("=" * 60)
    print("INSTITUTIONAL FLOW ANALYSIS")
    print("=" * 60)
    print(f"\nSymbol: {signal.symbol}")
    print(f"Signal: {signal.signal.value}")
    print(f"Confidence: {signal.confidence:.1%}")
    print(f"\nInstitution Count: {signal.institution_count}")
    print(f"Total Shares: {signal.total_institutional_shares:,}")
    print(f"Total Value: ${signal.total_institutional_value:,.0f}")
    print(f"Net Change: {signal.net_share_change:,}")
    print(f"Buyers: {signal.buyers}, Sellers: {signal.sellers}")
    print(f"Smart Money Flow: {signal.smart_money_flow:,.0f}")
    
    print(f"\nTop Buyers:")
    for buyer in signal.top_buyers[:3]:
        print(f"  {buyer['institution']}: +{buyer['share_change']:,} shares")
    
    print(f"\nTop Sellers:")
    for seller in signal.top_sellers[:3]:
        print(f"  {seller['institution']}: {seller['share_change']:,} shares")
    
    print(f"\nAnalysis: {signal.analysis}")
    
    # Whale alerts
    print("\n" + "=" * 60)
    print("WHALE ALERTS")
    print("=" * 60)
    
    for alert in tracker.get_whale_alerts():
        print(f"\n[{alert.significance}] {alert.alert_type}")
        print(f"  {alert.description}")
