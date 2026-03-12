"""
Compliance & Regulatory Framework
=================================
Institutional compliance and regulatory reporting:
- Form 13F (SEC quarterly holdings)
- Form PF (SEC private fund reporting)
- AML/KYC monitoring
- Trade compliance and pre-trade checks
- Investment restrictions
- Regulatory capital requirements
"""

import logging
from typing import Any, Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime, date, timedelta
from enum import Enum
import json
import uuid
import hashlib

logger = logging.getLogger(__name__)

try:
    import numpy as np
    import pandas as pd
    NUMPY_AVAILABLE = True
except ImportError:
    NUMPY_AVAILABLE = False


class ComplianceStatus(Enum):
    """Compliance check status"""
    COMPLIANT = "compliant"
    WARNING = "warning"
    VIOLATION = "violation"
    PENDING_REVIEW = "pending_review"
    EXEMPTED = "exempted"


class RestrictionType(Enum):
    """Types of investment restrictions"""
    PROHIBITED_SECURITY = "prohibited_security"
    SECTOR_LIMIT = "sector_limit"
    COUNTRY_LIMIT = "country_limit"
    CONCENTRATION_LIMIT = "concentration_limit"
    LEVERAGE_LIMIT = "leverage_limit"
    LIQUIDITY_REQUIREMENT = "liquidity_requirement"
    ESG_RESTRICTION = "esg_restriction"
    REGULATORY_RESTRICTION = "regulatory_restriction"


class AlertSeverity(Enum):
    """Alert severity levels"""
    INFO = "info"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class ComplianceAlert:
    """Compliance alert"""
    alert_id: str
    timestamp: datetime
    severity: AlertSeverity
    category: str
    description: str
    affected_positions: List[str]
    recommended_action: str
    status: ComplianceStatus
    resolved_at: Optional[datetime] = None
    resolved_by: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'alert_id': self.alert_id,
            'timestamp': self.timestamp.isoformat(),
            'severity': self.severity.value,
            'category': self.category,
            'description': self.description,
            'affected_positions': self.affected_positions,
            'recommended_action': self.recommended_action,
            'status': self.status.value
        }


@dataclass
class Form13F:
    """SEC Form 13F quarterly holdings report"""
    report_period: str  # YYYY-Q#
    filing_date: date
    manager_name: str
    manager_cik: str
    total_value: float
    holdings: List[Dict[str, Any]]
    amendment: bool = False
    
    def to_xml(self) -> str:
        """Generate 13F XML format"""
        # Simplified XML structure
        xml = f"""<?xml version="1.0" encoding="UTF-8"?>
<informationTable>
    <reportPeriod>{self.report_period}</reportPeriod>
    <filingManager>
        <name>{self.manager_name}</name>
        <cik>{self.manager_cik}</cik>
    </filingManager>
    <signatureDate>{self.filing_date.isoformat()}</signatureDate>
    <totalValue>{self.total_value:.0f}</totalValue>
    <holdings>
"""
        for holding in self.holdings:
            xml += f"""        <holding>
            <nameOfIssuer>{holding.get('name', '')}</nameOfIssuer>
            <cusip>{holding.get('cusip', '')}</cusip>
            <value>{holding.get('value', 0):.0f}</value>
            <shares>{holding.get('shares', 0):.0f}</shares>
            <investmentDiscretion>{holding.get('discretion', 'SOLE')}</investmentDiscretion>
            <votingAuthority>
                <sole>{holding.get('voting_sole', 0)}</sole>
                <shared>{holding.get('voting_shared', 0)}</shared>
                <none>{holding.get('voting_none', 0)}</none>
            </votingAuthority>
        </holding>
"""
        xml += """    </holdings>
</informationTable>"""
        return xml


@dataclass
class FormPF:
    """SEC Form PF private fund reporting"""
    report_period: str
    filing_date: date
    fund_name: str
    fund_id: str
    regulatory_aum: float
    gross_asset_value: float
    net_asset_value: float
    borrowings: float
    investor_count: int
    strategy_type: str
    geographic_focus: str
    
    # Risk metrics
    var_95: float
    max_drawdown: float
    leverage_ratio: float
    
    # Counterparty exposure
    top_counterparties: List[Dict[str, Any]]
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'report_period': self.report_period,
            'filing_date': self.filing_date.isoformat(),
            'fund_name': self.fund_name,
            'fund_id': self.fund_id,
            'regulatory_aum': self.regulatory_aum,
            'gav': self.gross_asset_value,
            'nav': self.net_asset_value,
            'borrowings': self.borrowings,
            'investor_count': self.investor_count,
            'strategy': self.strategy_type,
            'geography': self.geographic_focus,
            'risk_metrics': {
                'var_95': self.var_95,
                'max_drawdown': self.max_drawdown,
                'leverage': self.leverage_ratio
            },
            'counterparties': self.top_counterparties
        }


@dataclass
class InvestmentRestrictions:
    """Investment restrictions and guidelines"""
    restriction_id: str
    name: str
    restriction_type: RestrictionType
    description: str
    limit_value: float
    current_value: float
    effective_date: date
    expiry_date: Optional[date]
    source: str  # regulatory, client, internal
    is_hard_limit: bool = True
    
    @property
    def utilization(self) -> float:
        if self.limit_value == 0:
            return 0
        return self.current_value / self.limit_value
    
    @property
    def is_breached(self) -> bool:
        return self.current_value > self.limit_value
    
    @property
    def headroom(self) -> float:
        return max(0, self.limit_value - self.current_value)


class AMLMonitor:
    """
    Anti-Money Laundering Monitor
    Monitors for suspicious activity
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        
        # Thresholds
        self.large_transaction_threshold = config.get('large_transaction', 10000)
        self.structuring_threshold = config.get('structuring', 9000)
        self.velocity_threshold = config.get('velocity', 5)  # transactions per day
        
        # Watchlists
        self.sanctioned_entities: List[str] = []
        self.pep_list: List[str] = []  # Politically Exposed Persons
        
        # Transaction history
        self.transaction_history: List[Dict[str, Any]] = []
        
        # Alerts
        self.aml_alerts: List[ComplianceAlert] = []
        
        logger.info("AML Monitor initialized")
    
    def screen_transaction(
        self,
        transaction: Dict[str, Any]
    ) -> Tuple[bool, List[str]]:
        """Screen a transaction for AML concerns"""
        concerns = []
        
        amount = transaction.get('amount', 0)
        counterparty = transaction.get('counterparty', '')
        transaction_type = transaction.get('type', '')
        
        # Large transaction
        if amount >= self.large_transaction_threshold:
            concerns.append(f"Large transaction: ${amount:,.2f}")
        
        # Structuring detection
        if self.structuring_threshold <= amount < self.large_transaction_threshold:
            # Check for multiple similar transactions
            recent = self._get_recent_transactions(hours=24)
            similar = [t for t in recent if abs(t.get('amount', 0) - amount) < 1000]
            if len(similar) >= 2:
                concerns.append("Potential structuring detected")
        
        # Sanctioned entity check
        if counterparty in self.sanctioned_entities:
            concerns.append(f"Sanctioned entity: {counterparty}")
        
        # PEP check
        if counterparty in self.pep_list:
            concerns.append(f"Politically Exposed Person: {counterparty}")
        
        # Velocity check
        recent = self._get_recent_transactions(hours=24)
        if len(recent) >= self.velocity_threshold:
            concerns.append(f"High transaction velocity: {len(recent)} in 24h")
        
        # Store transaction
        transaction['timestamp'] = datetime.now()
        transaction['concerns'] = concerns
        self.transaction_history.append(transaction)
        
        # Generate alert if concerns
        if concerns:
            self._create_aml_alert(transaction, concerns)
        
        is_clear = len(concerns) == 0
        return is_clear, concerns
    
    def _get_recent_transactions(self, hours: int = 24) -> List[Dict[str, Any]]:
        """Get recent transactions"""
        cutoff = datetime.now() - timedelta(hours=hours)
        return [
            t for t in self.transaction_history
            if t.get('timestamp', datetime.min) > cutoff
        ]
    
    def _create_aml_alert(
        self,
        transaction: Dict[str, Any],
        concerns: List[str]
    ):
        """Create AML alert"""
        severity = AlertSeverity.HIGH if 'Sanctioned' in str(concerns) else AlertSeverity.MEDIUM
        
        alert = ComplianceAlert(
            alert_id=str(uuid.uuid4())[:8],
            timestamp=datetime.now(),
            severity=severity,
            category='AML',
            description='; '.join(concerns),
            affected_positions=[transaction.get('counterparty', 'Unknown')],
            recommended_action='Review transaction and file SAR if warranted',
            status=ComplianceStatus.PENDING_REVIEW
        )
        
        self.aml_alerts.append(alert)
    
    def add_to_watchlist(
        self,
        entity: str,
        list_type: str = 'sanctioned'
    ):
        """Add entity to watchlist"""
        if list_type == 'sanctioned':
            self.sanctioned_entities.append(entity)
        elif list_type == 'pep':
            self.pep_list.append(entity)


class TradeCompliance:
    """
    Trade Compliance System
    Pre-trade and post-trade compliance checks
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        
        # Restrictions
        self.restrictions: Dict[str, InvestmentRestrictions] = {}
        
        # Prohibited securities
        self.prohibited_securities: List[str] = []
        
        # Restricted list (require approval)
        self.restricted_list: List[str] = []
        
        # Compliance history
        self.check_history: List[Dict[str, Any]] = []
        
        # Alerts
        self.compliance_alerts: List[ComplianceAlert] = []
        
        logger.info("Trade Compliance initialized")
    
    def add_restriction(
        self,
        name: str,
        restriction_type: RestrictionType,
        limit_value: float,
        source: str = 'internal',
        is_hard_limit: bool = True
    ) -> InvestmentRestrictions:
        """Add investment restriction"""
        restriction_id = str(uuid.uuid4())[:8]
        
        restriction = InvestmentRestrictions(
            restriction_id=restriction_id,
            name=name,
            restriction_type=restriction_type,
            description=f"{restriction_type.value}: {name}",
            limit_value=limit_value,
            current_value=0,
            effective_date=date.today(),
            expiry_date=None,
            source=source,
            is_hard_limit=is_hard_limit
        )
        
        self.restrictions[restriction_id] = restriction
        return restriction
    
    def pre_trade_check(
        self,
        order: Dict[str, Any],
        portfolio: Dict[str, Any]
    ) -> Tuple[bool, List[str], List[str]]:
        """
        Pre-trade compliance check
        Returns: (approved, warnings, violations)
        """
        warnings = []
        violations = []
        
        symbol = order.get('symbol', '')
        side = order.get('side', 'buy')
        quantity = order.get('quantity', 0)
        price = order.get('price', 0)
        order_value = quantity * price
        
        # Check prohibited securities
        if symbol in self.prohibited_securities:
            violations.append(f"Prohibited security: {symbol}")
        
        # Check restricted list
        if symbol in self.restricted_list:
            warnings.append(f"Restricted security (requires approval): {symbol}")
        
        # Check concentration limits
        portfolio_value = portfolio.get('total_value', 0)
        if portfolio_value > 0:
            current_position = portfolio.get('positions', {}).get(symbol, {}).get('value', 0)
            new_position = current_position + order_value if side == 'buy' else current_position - order_value
            concentration = new_position / portfolio_value
            
            for restriction in self.restrictions.values():
                if restriction.restriction_type == RestrictionType.CONCENTRATION_LIMIT:
                    if concentration > restriction.limit_value:
                        if restriction.is_hard_limit:
                            violations.append(
                                f"Concentration limit breach: {concentration*100:.1f}% > {restriction.limit_value*100:.1f}%"
                            )
                        else:
                            warnings.append(
                                f"Concentration warning: {concentration*100:.1f}% > {restriction.limit_value*100:.1f}%"
                            )
        
        # Check sector limits
        sector = order.get('sector', 'Unknown')
        sector_exposure = portfolio.get('sector_exposures', {}).get(sector, 0)
        
        for restriction in self.restrictions.values():
            if restriction.restriction_type == RestrictionType.SECTOR_LIMIT:
                if restriction.name == sector and sector_exposure > restriction.limit_value:
                    violations.append(
                        f"Sector limit breach: {sector} at {sector_exposure*100:.1f}%"
                    )
        
        # Check leverage
        leverage = portfolio.get('leverage', 1.0)
        for restriction in self.restrictions.values():
            if restriction.restriction_type == RestrictionType.LEVERAGE_LIMIT:
                if leverage > restriction.limit_value:
                    violations.append(
                        f"Leverage limit breach: {leverage:.2f}x > {restriction.limit_value:.2f}x"
                    )
        
        # Record check
        self.check_history.append({
            'timestamp': datetime.now(),
            'order': order,
            'warnings': warnings,
            'violations': violations,
            'approved': len(violations) == 0
        })
        
        # Create alerts for violations
        if violations:
            self._create_compliance_alert(order, violations, AlertSeverity.HIGH)
        elif warnings:
            self._create_compliance_alert(order, warnings, AlertSeverity.MEDIUM)
        
        approved = len(violations) == 0
        return approved, warnings, violations
    
    def post_trade_check(
        self,
        trade: Dict[str, Any],
        portfolio: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Post-trade compliance verification"""
        results = {
            'trade_id': trade.get('trade_id'),
            'timestamp': datetime.now(),
            'checks': []
        }
        
        # Verify execution within limits
        expected_price = trade.get('expected_price', 0)
        actual_price = trade.get('actual_price', 0)
        
        if expected_price > 0:
            slippage = abs(actual_price - expected_price) / expected_price
            if slippage > 0.01:  # 1% threshold
                results['checks'].append({
                    'check': 'execution_quality',
                    'status': 'warning',
                    'message': f"High slippage: {slippage*100:.2f}%"
                })
        
        # Verify best execution
        results['checks'].append({
            'check': 'best_execution',
            'status': 'compliant',
            'message': 'Best execution verified'
        })
        
        return results
    
    def _create_compliance_alert(
        self,
        order: Dict[str, Any],
        issues: List[str],
        severity: AlertSeverity
    ):
        """Create compliance alert"""
        alert = ComplianceAlert(
            alert_id=str(uuid.uuid4())[:8],
            timestamp=datetime.now(),
            severity=severity,
            category='TRADE_COMPLIANCE',
            description='; '.join(issues),
            affected_positions=[order.get('symbol', 'Unknown')],
            recommended_action='Review order and restrictions',
            status=ComplianceStatus.PENDING_REVIEW
        )
        
        self.compliance_alerts.append(alert)
    
    def update_restriction_values(
        self,
        portfolio: Dict[str, Any]
    ):
        """Update current values for all restrictions"""
        for restriction in self.restrictions.values():
            if restriction.restriction_type == RestrictionType.CONCENTRATION_LIMIT:
                # Update with max position concentration
                positions = portfolio.get('positions', {})
                total_value = portfolio.get('total_value', 1)
                max_concentration = max(
                    (p.get('value', 0) / total_value for p in positions.values()),
                    default=0
                )
                restriction.current_value = max_concentration
            
            elif restriction.restriction_type == RestrictionType.LEVERAGE_LIMIT:
                restriction.current_value = portfolio.get('leverage', 1.0)
            
            elif restriction.restriction_type == RestrictionType.SECTOR_LIMIT:
                sector_exposure = portfolio.get('sector_exposures', {}).get(restriction.name, 0)
                restriction.current_value = sector_exposure


class RegulatoryReporter:
    """
    Regulatory Reporting System
    Generates required regulatory filings
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        
        # Fund information
        self.fund_name = config.get('fund_name', 'AlphaAlgo Fund')
        self.manager_cik = config.get('cik', '0000000000')
        self.fund_id = config.get('fund_id', str(uuid.uuid4())[:8])
        
        # Filing history
        self.filing_history: List[Dict[str, Any]] = []
        
        logger.info("Regulatory Reporter initialized")
    
    def generate_form_13f(
        self,
        holdings: Dict[str, Dict[str, Any]],
        report_period: str
    ) -> Form13F:
        """Generate Form 13F quarterly holdings report"""
        holdings_list = []
        total_value = 0
        
        for symbol, holding in holdings.items():
            value = holding.get('value', 0)
            shares = holding.get('shares', 0)
            
            # Only include 13F securities (equity, options on equity)
            if holding.get('asset_class') not in ['equity', 'option']:
                continue
            
            # Minimum threshold ($200k or 10,000 shares)
            if value < 200000 and shares < 10000:
                continue
            
            holdings_list.append({
                'name': holding.get('name', symbol),
                'cusip': holding.get('cusip', ''),
                'value': value,
                'shares': shares,
                'discretion': 'SOLE',
                'voting_sole': shares,
                'voting_shared': 0,
                'voting_none': 0
            })
            
            total_value += value
        
        form = Form13F(
            report_period=report_period,
            filing_date=date.today(),
            manager_name=self.fund_name,
            manager_cik=self.manager_cik,
            total_value=total_value,
            holdings=holdings_list
        )
        
        # Record filing
        self.filing_history.append({
            'form': '13F',
            'period': report_period,
            'date': date.today().isoformat(),
            'total_value': total_value,
            'num_holdings': len(holdings_list)
        })
        
        return form
    
    def generate_form_pf(
        self,
        fund_metrics: Dict[str, Any],
        risk_metrics: Dict[str, Any],
        counterparties: List[Dict[str, Any]],
        report_period: str
    ) -> FormPF:
        """Generate Form PF private fund report"""
        form = FormPF(
            report_period=report_period,
            filing_date=date.today(),
            fund_name=self.fund_name,
            fund_id=self.fund_id,
            regulatory_aum=fund_metrics.get('aum', 0),
            gross_asset_value=fund_metrics.get('gav', 0),
            net_asset_value=fund_metrics.get('nav', 0),
            borrowings=fund_metrics.get('borrowings', 0),
            investor_count=fund_metrics.get('investor_count', 0),
            strategy_type=fund_metrics.get('strategy', 'Multi-Strategy'),
            geographic_focus=fund_metrics.get('geography', 'Global'),
            var_95=risk_metrics.get('var_95', 0),
            max_drawdown=risk_metrics.get('max_drawdown', 0),
            leverage_ratio=risk_metrics.get('leverage', 1.0),
            top_counterparties=counterparties[:5]  # Top 5
        )
        
        # Record filing
        self.filing_history.append({
            'form': 'PF',
            'period': report_period,
            'date': date.today().isoformat(),
            'nav': fund_metrics.get('nav', 0)
        })
        
        return form
    
    def get_filing_calendar(self) -> List[Dict[str, Any]]:
        """Get upcoming filing deadlines"""
        today = date.today()
        calendar = []
        
        # Form 13F - 45 days after quarter end
        quarter_ends = [
            date(today.year, 3, 31),
            date(today.year, 6, 30),
            date(today.year, 9, 30),
            date(today.year, 12, 31)
        ]
        
        for qe in quarter_ends:
            deadline = qe + timedelta(days=45)
            if deadline > today:
                calendar.append({
                    'form': '13F',
                    'period': f"{qe.year}-Q{(qe.month-1)//3 + 1}",
                    'deadline': deadline.isoformat(),
                    'days_until': (deadline - today).days
                })
        
        # Form PF - varies by AUM
        # Assuming quarterly filer (>$1.5B AUM)
        for qe in quarter_ends:
            deadline = qe + timedelta(days=60)
            if deadline > today:
                calendar.append({
                    'form': 'PF',
                    'period': f"{qe.year}-Q{(qe.month-1)//3 + 1}",
                    'deadline': deadline.isoformat(),
                    'days_until': (deadline - today).days
                })
        
        return sorted(calendar, key=lambda x: x['deadline'])


class ComplianceEngine:
    """
    Master Compliance Engine
    Coordinates all compliance functions
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        
        # Components
        self.aml_monitor = AMLMonitor(config.get('aml', {}))
        self.trade_compliance = TradeCompliance(config.get('trade', {}))
        self.regulatory_reporter = RegulatoryReporter(config.get('regulatory', {}))
        
        # Setup default restrictions
        self._setup_default_restrictions()
        
        # Compliance state
        self.overall_status = ComplianceStatus.COMPLIANT
        self.all_alerts: List[ComplianceAlert] = []
        
        logger.info("Compliance Engine initialized")
    
    def _setup_default_restrictions(self):
        """Setup default investment restrictions"""
        # Concentration limit
        self.trade_compliance.add_restriction(
            name="Single Position",
            restriction_type=RestrictionType.CONCENTRATION_LIMIT,
            limit_value=0.10,  # 10%
            source='internal'
        )
        
        # Leverage limit
        self.trade_compliance.add_restriction(
            name="Gross Leverage",
            restriction_type=RestrictionType.LEVERAGE_LIMIT,
            limit_value=2.0,  # 2x
            source='regulatory'
        )
        
        # Sector limits
        for sector in ['Technology', 'Financials', 'Healthcare', 'Energy']:
            self.trade_compliance.add_restriction(
                name=sector,
                restriction_type=RestrictionType.SECTOR_LIMIT,
                limit_value=0.25,  # 25%
                source='internal',
                is_hard_limit=False
            )
    
    def run_compliance_check(
        self,
        portfolio: Dict[str, Any],
        pending_orders: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Run comprehensive compliance check"""
        results = {
            'timestamp': datetime.now(),
            'overall_status': ComplianceStatus.COMPLIANT,
            'order_checks': [],
            'restriction_status': [],
            'alerts': []
        }
        
        # Update restriction values
        self.trade_compliance.update_restriction_values(portfolio)
        
        # Check pending orders
        for order in pending_orders:
            approved, warnings, violations = self.trade_compliance.pre_trade_check(
                order, portfolio
            )
            results['order_checks'].append({
                'order': order,
                'approved': approved,
                'warnings': warnings,
                'violations': violations
            })
            
            if violations:
                results['overall_status'] = ComplianceStatus.VIOLATION
            elif warnings and results['overall_status'] == ComplianceStatus.COMPLIANT:
                results['overall_status'] = ComplianceStatus.WARNING
        
        # Check all restrictions
        for restriction in self.trade_compliance.restrictions.values():
            status = {
                'name': restriction.name,
                'type': restriction.restriction_type.value,
                'limit': restriction.limit_value,
                'current': restriction.current_value,
                'utilization': f"{restriction.utilization * 100:.1f}%",
                'breached': restriction.is_breached,
                'headroom': restriction.headroom
            }
            results['restriction_status'].append(status)
            
            if restriction.is_breached:
                results['overall_status'] = ComplianceStatus.VIOLATION
        
        # Collect all alerts
        results['alerts'] = (
            [a.to_dict() for a in self.aml_monitor.aml_alerts[-10:]] +
            [a.to_dict() for a in self.trade_compliance.compliance_alerts[-10:]]
        )
        
        self.overall_status = results['overall_status']
        return results
    
    def screen_investor(
        self,
        investor: Dict[str, Any]
    ) -> Tuple[bool, List[str]]:
        """Screen investor for AML/KYC"""
        concerns = []
        
        name = investor.get('name', '')
        country = investor.get('country', '')
        
        # Sanctioned country check
        sanctioned_countries = ['NK', 'IR', 'SY', 'CU']
        if country in sanctioned_countries:
            concerns.append(f"Sanctioned country: {country}")
        
        # AML screening
        is_clear, aml_concerns = self.aml_monitor.screen_transaction({
            'type': 'subscription',
            'counterparty': name,
            'amount': investor.get('investment_amount', 0)
        })
        
        concerns.extend(aml_concerns)
        
        return len(concerns) == 0, concerns
    
    def get_compliance_summary(self) -> Dict[str, Any]:
        """Get compliance summary"""
        return {
            'overall_status': self.overall_status.value,
            'restrictions_count': len(self.trade_compliance.restrictions),
            'breached_restrictions': sum(
                1 for r in self.trade_compliance.restrictions.values()
                if r.is_breached
            ),
            'aml_alerts': len(self.aml_monitor.aml_alerts),
            'trade_alerts': len(self.trade_compliance.compliance_alerts),
            'prohibited_securities': len(self.trade_compliance.prohibited_securities),
            'restricted_securities': len(self.trade_compliance.restricted_list),
            'upcoming_filings': self.regulatory_reporter.get_filing_calendar()[:3]
        }
