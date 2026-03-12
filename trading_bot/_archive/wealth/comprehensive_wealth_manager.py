"""
from typing import List, Optional, Set, Tuple
Comprehensive Wealth Management System
Tax optimization, ESG integration, client portals, and portfolio analytics
"""

import logging
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime, date, timedelta
from enum import Enum
import json

logger = logging.getLogger(__name__)

try:
    import numpy as np
    import pandas as pd
    NUMPY_AVAILABLE = True
except ImportError:
    NUMPY_AVAILABLE = False


class AccountType(Enum):
    """Account types for tax purposes"""
    TAXABLE = "taxable"
    IRA = "ira"
    ROTH_IRA = "roth_ira"
    K401 = "401k"
    HSA = "hsa"
    TRUST = "trust"
    CORPORATE = "corporate"


class ESGCategory(Enum):
    """ESG categories"""
    ENVIRONMENTAL = "environmental"
    SOCIAL = "social"
    GOVERNANCE = "governance"


class RiskProfile(Enum):
    """Client risk profiles"""
    CONSERVATIVE = "conservative"
    MODERATE_CONSERVATIVE = "moderate_conservative"
    MODERATE = "moderate"
    MODERATE_AGGRESSIVE = "moderate_aggressive"
    AGGRESSIVE = "aggressive"


@dataclass
class TaxLot:
    """Tax lot for cost basis tracking"""
    lot_id: str
    symbol: str
    quantity: float
    cost_basis: float
    purchase_date: date
    account_type: AccountType
    wash_sale_disallowed: float = 0
    
    @property
    def is_long_term(self) -> bool:
        """Check if holding qualifies for long-term capital gains"""
        return (date.today() - self.purchase_date).days > 365
    
    @property
    def holding_period_days(self) -> int:
        return (date.today() - self.purchase_date).days


@dataclass
class ESGScore:
    """ESG score for an asset"""
    symbol: str
    environmental: float  # 0-100
    social: float  # 0-100
    governance: float  # 0-100
    controversy_score: float  # 0-100 (lower is better)
    carbon_intensity: float  # tons CO2 / $M revenue
    data_date: date
    
    @property
    def overall_score(self) -> float:
        """Calculate overall ESG score"""
        return (self.environmental + self.social + self.governance) / 3 - self.controversy_score * 0.1


@dataclass
class ClientProfile:
    """Client profile for wealth management"""
    client_id: str
    name: str
    risk_profile: RiskProfile
    investment_horizon_years: int
    tax_bracket: float
    state_tax_rate: float
    accounts: List[AccountType]
    esg_preferences: Dict[ESGCategory, float]  # Weight 0-1
    excluded_sectors: List[str]
    target_allocation: Dict[str, float]
    created_at: datetime = field(default_factory=datetime.now)


@dataclass
class TaxHarvestingOpportunity:
    """Tax loss harvesting opportunity"""
    symbol: str
    lots: List[TaxLot]
    unrealized_loss: float
    tax_savings: float
    replacement_symbol: Optional[str]
    wash_sale_risk: bool
    recommendation: str


class TaxOptimizer:
    """
    Tax optimization engine for wealth management
    """
    
    # Federal tax rates 2024
    FEDERAL_RATES = {
        'short_term': [0.10, 0.12, 0.22, 0.24, 0.32, 0.35, 0.37],
        'long_term': [0.0, 0.15, 0.20],
        'niit': 0.038  # Net Investment Income Tax
    }
    
    # Wash sale window
    WASH_SALE_DAYS = 30
    
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        self.tax_lots: Dict[str, List[TaxLot]] = {}
        self.recent_sales: List[Dict[str, Any]] = []
        
        logger.info("Tax optimizer initialized")
        
    def add_tax_lot(self, lot: TaxLot):
        """Add a tax lot"""
        if lot.symbol not in self.tax_lots:
            self.tax_lots[lot.symbol] = []
        self.tax_lots[lot.symbol].append(lot)
        
    def get_unrealized_gains_losses(self, current_prices: Dict[str, float]) -> Dict[str, Dict[str, float]]:
        """Calculate unrealized gains/losses by symbol"""
        results = {}
        
        for symbol, lots in self.tax_lots.items():
            price = current_prices.get(symbol, 0)
            
            short_term_gain = 0
            long_term_gain = 0
            short_term_loss = 0
            long_term_loss = 0
            
            for lot in lots:
                market_value = lot.quantity * price
                gain_loss = market_value - lot.cost_basis
                
                if lot.is_long_term:
                    if gain_loss > 0:
                        long_term_gain += gain_loss
                    else:
                        long_term_loss += abs(gain_loss)
                else:
                    if gain_loss > 0:
                        short_term_gain += gain_loss
                    else:
                        short_term_loss += abs(gain_loss)
                        
            results[symbol] = {
                'short_term_gain': short_term_gain,
                'long_term_gain': long_term_gain,
                'short_term_loss': short_term_loss,
                'long_term_loss': long_term_loss,
                'net': (short_term_gain + long_term_gain) - (short_term_loss + long_term_loss)
            }
            
        return results
    
    def find_tax_loss_harvesting_opportunities(
        self,
        current_prices: Dict[str, float],
        client: ClientProfile,
        min_loss: float = 1000
    ) -> List[TaxHarvestingOpportunity]:
        """Find tax loss harvesting opportunities"""
        opportunities = []
        
        for symbol, lots in self.tax_lots.items():
            price = current_prices.get(symbol, 0)
            if price == 0:
                continue
                
            loss_lots = []
            total_loss = 0
            
            for lot in lots:
                market_value = lot.quantity * price
                gain_loss = market_value - lot.cost_basis
                
                if gain_loss < 0:
                    loss_lots.append(lot)
                    total_loss += abs(gain_loss)
                    
            if total_loss >= min_loss:
                # Calculate tax savings
                if any(not lot.is_long_term for lot in loss_lots):
                    # Short-term losses offset short-term gains first
                    tax_rate = client.tax_bracket + client.state_tax_rate
                else:
                    tax_rate = 0.15 + client.state_tax_rate  # Long-term rate
                    
                tax_savings = total_loss * tax_rate
                
                # Check wash sale risk
                wash_sale_risk = self._check_wash_sale_risk(symbol)
                
                opportunities.append(TaxHarvestingOpportunity(
                    symbol=symbol,
                    lots=loss_lots,
                    unrealized_loss=total_loss,
                    tax_savings=tax_savings,
                    replacement_symbol=self._find_replacement(symbol),
                    wash_sale_risk=wash_sale_risk,
                    recommendation=self._generate_recommendation(total_loss, tax_savings, wash_sale_risk)
                ))
                
        return sorted(opportunities, key=lambda x: x.tax_savings, reverse=True)
    
    def _check_wash_sale_risk(self, symbol: str) -> bool:
        """Check if there's wash sale risk"""
        cutoff = date.today() - timedelta(days=self.WASH_SALE_DAYS)
        
        for sale in self.recent_sales:
            if sale['symbol'] == symbol and sale['date'] >= cutoff:
                return True
        return False
    
    def _find_replacement(self, symbol: str) -> Optional[str]:
        """Find a similar but not substantially identical security"""
        # Simplified - would use sector/industry data in production
        replacements = {
            'SPY': 'VOO',
            'VOO': 'IVV',
            'QQQ': 'QQQM',
            'VTI': 'ITOT',
            'AAPL': 'XLK',
            'MSFT': 'XLK',
            'GOOGL': 'XLC',
        }
        return replacements.get(symbol)
    
    def _generate_recommendation(self, loss: float, savings: float, wash_sale_risk: bool) -> str:
        """Generate recommendation text"""
        if wash_sale_risk:
            return f"WAIT: Wash sale risk. Loss: ${loss:,.2f}, Potential savings: ${savings:,.2f}"
        elif savings > 5000:
            return f"HARVEST NOW: High value opportunity. Loss: ${loss:,.2f}, Savings: ${savings:,.2f}"
        elif savings > 1000:
            return f"CONSIDER: Moderate opportunity. Loss: ${loss:,.2f}, Savings: ${savings:,.2f}"
        else:
            return f"OPTIONAL: Small opportunity. Loss: ${loss:,.2f}, Savings: ${savings:,.2f}"
    
    def optimize_lot_selection(
        self,
        symbol: str,
        shares_to_sell: float,
        current_price: float,
        client: ClientProfile,
        strategy: str = "tax_efficient"
    ) -> List[Tuple[TaxLot, float]]:
        """
        Select optimal lots for selling
        
        Strategies:
        - tax_efficient: Minimize tax impact
        - fifo: First in, first out
        - lifo: Last in, first out
        - hifo: Highest cost first
        - specific: Specific lot identification
        """
        lots = self.tax_lots.get(symbol, [])
        if not lots:
            return []
            
        remaining = shares_to_sell
        selected = []
        
        if strategy == "tax_efficient":
            # Sort by tax efficiency (losses first, then long-term gains, then short-term gains)
            def tax_efficiency(lot: TaxLot) -> float:
                gain_loss = (current_price - lot.cost_basis / lot.quantity) * lot.quantity
                if gain_loss < 0:
                    return -1000000 + gain_loss  # Losses first
                elif lot.is_long_term:
                    return gain_loss * 0.15  # Long-term tax
                else:
                    return gain_loss * client.tax_bracket  # Short-term tax
                    
            sorted_lots = sorted(lots, key=tax_efficiency)
            
        elif strategy == "fifo":
            sorted_lots = sorted(lots, key=lambda l: l.purchase_date)
        elif strategy == "lifo":
            sorted_lots = sorted(lots, key=lambda l: l.purchase_date, reverse=True)
        elif strategy == "hifo":
            sorted_lots = sorted(lots, key=lambda l: l.cost_basis / l.quantity, reverse=True)
        else:
            sorted_lots = lots
            
        for lot in sorted_lots:
            if remaining <= 0:
                break
                
            sell_qty = min(remaining, lot.quantity)
            selected.append((lot, sell_qty))
            remaining -= sell_qty
            
        return selected


class ESGAnalyzer:
    """
    ESG analysis and portfolio screening
    """
    
    # Sector exclusions by ESG category
    DEFAULT_EXCLUSIONS = {
        'tobacco': ['PM', 'MO', 'BTI'],
        'weapons': ['LMT', 'RTX', 'NOC', 'BA'],
        'gambling': ['MGM', 'WYNN', 'LVS'],
        'fossil_fuels': ['XOM', 'CVX', 'COP', 'OXY'],
        'private_prisons': ['GEO', 'CXW'],
    }
    
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        self.esg_scores: Dict[str, ESGScore] = {}
        
        logger.info("ESG analyzer initialized")
        
    def set_esg_score(self, score: ESGScore):
        """Set ESG score for a symbol"""
        self.esg_scores[score.symbol] = score
        
    def screen_portfolio(
        self,
        holdings: Dict[str, float],
        client: ClientProfile
    ) -> Dict[str, Any]:
        """Screen portfolio against ESG criteria"""
        violations = []
        scores = []
        
        for symbol, weight in holdings.items():
            # Check exclusions
            for sector, symbols in self.DEFAULT_EXCLUSIONS.items():
                if symbol in symbols and sector in client.excluded_sectors:
                    violations.append({
                        'symbol': symbol,
                        'reason': f"Excluded sector: {sector}",
                        'weight': weight
                    })
                    
            # Check ESG scores
            if symbol in self.esg_scores:
                score = self.esg_scores[symbol]
                scores.append({
                    'symbol': symbol,
                    'weight': weight,
                    'environmental': score.environmental,
                    'social': score.social,
                    'governance': score.governance,
                    'overall': score.overall_score
                })
                
                # Check minimum thresholds
                for category, min_score in client.esg_preferences.items():
                    if category == ESGCategory.ENVIRONMENTAL and score.environmental < min_score * 100:
                        violations.append({
                            'symbol': symbol,
                            'reason': f"Environmental score {score.environmental} below threshold {min_score * 100}",
                            'weight': weight
                        })
                        
        # Calculate portfolio ESG score
        portfolio_score = self._calculate_portfolio_esg(scores)
        
        return {
            'violations': violations,
            'scores': scores,
            'portfolio_esg': portfolio_score,
            'compliant': len(violations) == 0
        }
    
    def _calculate_portfolio_esg(self, scores: List[Dict]) -> Dict[str, float]:
        """Calculate weighted portfolio ESG score"""
        if not scores:
            return {'environmental': 0, 'social': 0, 'governance': 0, 'overall': 0}
            
        total_weight = sum(s['weight'] for s in scores)
        if total_weight == 0:
            return {'environmental': 0, 'social': 0, 'governance': 0, 'overall': 0}
            
        return {
            'environmental': sum(s['environmental'] * s['weight'] for s in scores) / total_weight,
            'social': sum(s['social'] * s['weight'] for s in scores) / total_weight,
            'governance': sum(s['governance'] * s['weight'] for s in scores) / total_weight,
            'overall': sum(s['overall'] * s['weight'] for s in scores) / total_weight
        }
    
    def suggest_esg_improvements(
        self,
        holdings: Dict[str, float],
        client: ClientProfile
    ) -> List[Dict[str, Any]]:
        """Suggest improvements to portfolio ESG"""
        suggestions = []
        
        for symbol, weight in holdings.items():
            if symbol not in self.esg_scores:
                continue
                
            score = self.esg_scores[symbol]
            
            if score.overall_score < 50:
                suggestions.append({
                    'symbol': symbol,
                    'current_score': score.overall_score,
                    'action': 'REDUCE',
                    'reason': f"Low ESG score ({score.overall_score:.1f})",
                    'impact': weight * (50 - score.overall_score) / 100
                })
            elif score.carbon_intensity > 500:
                suggestions.append({
                    'symbol': symbol,
                    'current_score': score.overall_score,
                    'action': 'REVIEW',
                    'reason': f"High carbon intensity ({score.carbon_intensity:.0f})",
                    'impact': weight * 0.1
                })
                
        return sorted(suggestions, key=lambda x: x['impact'], reverse=True)


class WealthManager:
    """
    Comprehensive wealth management system
    """
    
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        
        # Components
        self.tax_optimizer = TaxOptimizer(config)
        self.esg_analyzer = ESGAnalyzer(config)
        
        # Client data
        self.clients: Dict[str, ClientProfile] = {}
        self.portfolios: Dict[str, Dict[str, float]] = {}
        
        logger.info("Wealth manager initialized")
        
    def add_client(self, client: ClientProfile):
        """Add a client"""
        self.clients[client.client_id] = client
        self.portfolios[client.client_id] = {}
        
    def update_portfolio(self, client_id: str, holdings: Dict[str, float]):
        """Update client portfolio"""
        self.portfolios[client_id] = holdings
        
    def get_comprehensive_report(
        self,
        client_id: str,
        current_prices: Dict[str, float]
    ) -> Dict[str, Any]:
        """Generate comprehensive wealth report"""
        client = self.clients.get(client_id)
        if not client:
            return {'error': 'Client not found'}
            
        holdings = self.portfolios.get(client_id, {})
        
        # Tax analysis
        tax_opportunities = self.tax_optimizer.find_tax_loss_harvesting_opportunities(
            current_prices, client
        )
        
        # ESG analysis
        esg_report = self.esg_analyzer.screen_portfolio(holdings, client)
        esg_suggestions = self.esg_analyzer.suggest_esg_improvements(holdings, client)
        
        # Portfolio analysis
        total_value = sum(holdings.get(s, 0) * current_prices.get(s, 0) for s in holdings)
        
        return {
            'client_id': client_id,
            'client_name': client.name,
            'report_date': datetime.now().isoformat(),
            'portfolio': {
                'total_value': total_value,
                'holdings_count': len(holdings),
                'allocation': holdings
            },
            'tax': {
                'harvesting_opportunities': len(tax_opportunities),
                'potential_savings': sum(o.tax_savings for o in tax_opportunities),
                'opportunities': [
                    {
                        'symbol': o.symbol,
                        'loss': o.unrealized_loss,
                        'savings': o.tax_savings,
                        'recommendation': o.recommendation
                    }
                    for o in tax_opportunities[:5]
                ]
            },
            'esg': {
                'compliant': esg_report['compliant'],
                'violations': len(esg_report['violations']),
                'portfolio_score': esg_report['portfolio_esg'],
                'suggestions': esg_suggestions[:5]
            },
            'recommendations': self._generate_recommendations(client, tax_opportunities, esg_report)
        }
    
    def _generate_recommendations(
        self,
        client: ClientProfile,
        tax_opportunities: List[TaxHarvestingOpportunity],
        esg_report: Dict[str, Any]
    ) -> List[str]:
        """Generate actionable recommendations"""
        recommendations = []
        
        # Tax recommendations
        high_value_tax = [o for o in tax_opportunities if o.tax_savings > 5000]
        if high_value_tax:
            recommendations.append(
                f"Consider tax loss harvesting on {len(high_value_tax)} positions "
                f"for potential savings of ${sum(o.tax_savings for o in high_value_tax):,.2f}"
            )
            
        # ESG recommendations
        if not esg_report['compliant']:
            recommendations.append(
                f"Portfolio has {len(esg_report['violations'])} ESG violations. "
                f"Review excluded sectors and minimum score thresholds."
            )
            
        if esg_report['portfolio_esg']['overall'] < 60:
            recommendations.append(
                f"Portfolio ESG score ({esg_report['portfolio_esg']['overall']:.1f}) is below average. "
                f"Consider increasing allocation to high-ESG holdings."
            )
            
        # Risk recommendations
        if client.risk_profile == RiskProfile.CONSERVATIVE:
            recommendations.append(
                "As a conservative investor, ensure fixed income allocation is at least 40%."
            )
            
        return recommendations
