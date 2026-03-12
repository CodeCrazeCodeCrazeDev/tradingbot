"""
Wealth Management System
Implements personalized client portals, tax optimization, ESG scoring, risk profiles
"""

import numpy as np
from typing import Dict, List, Optional
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum
import asyncio
import numpy

import logging

# Evolution: Added retry decorator
def retry(max_attempts=3, delay=1.0):
    """Retry decorator for resilient operations"""
    def decorator(func):
        async def wrapper(*args, **kwargs):
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


logger = logging.getLogger(__name__)



class RiskProfile(Enum):
    """Client risk profiles"""
    CONSERVATIVE = "conservative"
    MODERATE = "moderate"
    AGGRESSIVE = "aggressive"
    VERY_AGGRESSIVE = "very_aggressive"


@dataclass
class ClientProfile:
    """Individual client profile"""
    client_id: str
    name: str
    risk_profile: RiskProfile
    investment_horizon: int  # years
    tax_bracket: float  # 0-1
    esg_preference: float  # 0-1 (0=none, 1=strict)
    liquidity_needs: float  # % of portfolio
    target_return: float
    max_drawdown: float
    preferences: Dict


@dataclass
class TaxEvent:
    """Tax event for optimization"""
    event_type: str  # 'capital_gain', 'dividend', 'interest'
    amount: float
    tax_rate: float
    date: datetime
    asset: str


@dataclass
class ESGScore:
    """ESG (Environmental, Social, Governance) score"""
    asset: str
    environmental: float  # 0-100
    social: float  # 0-100
    governance: float  # 0-100
    overall: float  # 0-100
    controversies: List[str]


class TaxOptimizationEngine:
    """Advanced tax optimization for trading"""
    
    def __init__(self):
        self.tax_events: List[TaxEvent] = []
        self.tax_loss_harvest_opportunities: List[Dict] = []
        
    async def optimize_tax_strategy(
        self,
        portfolio: Dict,
        client: ClientProfile,
        year: int = 2024
    ) -> Dict:
        """Optimize tax strategy for client"""
        
        # 1. Tax loss harvesting
        harvest_opportunities = self._identify_tax_loss_harvest(portfolio)
        
        # 2. Asset location optimization
        asset_location = self._optimize_asset_location(portfolio, client)
        
        # 3. Capital gains management
        gains_strategy = self._manage_capital_gains(portfolio, client)
        
        # 4. Dividend timing
        dividend_strategy = self._optimize_dividend_timing(portfolio, client)
        
        # Calculate tax savings
        total_savings = self._calculate_tax_savings(
            harvest_opportunities,
            asset_location,
            gains_strategy,
            client.tax_bracket
        )
        
        return {
            'tax_loss_harvesting': harvest_opportunities,
            'asset_location': asset_location,
            'capital_gains_strategy': gains_strategy,
            'dividend_strategy': dividend_strategy,
            'estimated_savings': total_savings,
            'effective_tax_rate': self._calculate_effective_rate(client),
            'recommendations': self._generate_recommendations(client)
        }
    
    def _identify_tax_loss_harvest(self, portfolio: Dict) -> List[Dict]:
        """Identify tax loss harvesting opportunities"""
        opportunities = []
        
        positions = portfolio.get('positions', [])
        for pos in positions:
            unrealized_loss = pos.get('unrealized_pnl', 0)
            
            if unrealized_loss < -100:  # Minimum loss threshold
                opportunities.append({
                    'asset': pos.get('symbol'),
                    'loss': abs(unrealized_loss),
                    'tax_benefit': abs(unrealized_loss) * 0.3,  # Assume 30% tax rate
                    'replacement_asset': self._find_replacement(pos.get('symbol')),
                    'wash_sale_date': datetime.now() + timedelta(days=31)
                })
        
        return opportunities
    
    def _find_replacement(self, asset: str) -> str:
        """Find replacement asset to avoid wash sale"""
        # Simplified - would use correlation analysis
        replacements = {
            'SPY': 'VOO',  # S&P 500 ETFs
            'QQQ': 'ONEQ',  # Nasdaq ETFs
            'IWM': 'VB',  # Small cap ETFs
        }
        return replacements.get(asset, f"{asset}_ALT")
    
    def _optimize_asset_location(
        self,
        portfolio: Dict,
        client: ClientProfile
    ) -> Dict:
        """Optimize which assets go in taxable vs tax-advantaged accounts"""
        
        # Tax-inefficient assets (high turnover, dividends) -> tax-advantaged
        # Tax-efficient assets (low turnover, growth) -> taxable
        
        return {
            'taxable_account': [
                'index_funds',
                'municipal_bonds',
                'growth_stocks'
            ],
            'tax_deferred_account': [
                'bonds',
                'reits',
                'high_dividend_stocks'
            ],
            'roth_account': [
                'high_growth_potential',
                'alternatives'
            ]
        }
    
    def _manage_capital_gains(
        self,
        portfolio: Dict,
        client: ClientProfile
    ) -> Dict:
        """Manage capital gains realization"""
        
        short_term_gains = portfolio.get('short_term_gains', 0)
        long_term_gains = portfolio.get('long_term_gains', 0)
        
        # Strategy: Defer short-term, realize long-term
        return {
            'defer_short_term': short_term_gains > 0,
            'realize_long_term': long_term_gains > 10000,
            'target_holding_period': 366,  # > 1 year for long-term rates
            'estimated_savings': short_term_gains * (client.tax_bracket - 0.15)
        }
    
    def _optimize_dividend_timing(
        self,
        portfolio: Dict,
        client: ClientProfile
    ) -> Dict:
        """Optimize dividend capture timing"""
        
        return {
            'strategy': 'qualified_dividends',
            'holding_period': 61,  # Days for qualified dividend treatment
            'estimated_benefit': portfolio.get('annual_dividends', 0) * 0.15
        }
    
    def _calculate_tax_savings(
        self,
        harvest: List[Dict],
        location: Dict,
        gains: Dict,
        tax_bracket: float
    ) -> float:
        """Calculate total tax savings"""
        
        harvest_savings = sum(opp['tax_benefit'] for opp in harvest)
        gains_savings = gains.get('estimated_savings', 0)
        
        # Estimate location savings (5-10% of portfolio)
        location_savings = 5000  # Simplified
        
        return harvest_savings + gains_savings + location_savings
    
    def _calculate_effective_rate(self, client: ClientProfile) -> float:
        """Calculate effective tax rate after optimization"""
        # Simplified calculation
        return client.tax_bracket * 0.7  # 30% reduction through optimization
    
    def _generate_recommendations(self, client: ClientProfile) -> List[str]:
        """Generate tax optimization recommendations"""
        recommendations = []
        
        if client.tax_bracket > 0.3:
            recommendations.append("Consider municipal bonds for tax-free income")
            recommendations.append("Maximize tax-loss harvesting opportunities")
        
        if client.investment_horizon > 10:
            recommendations.append("Focus on long-term capital gains")
            recommendations.append("Use Roth conversions during low-income years")
        
        recommendations.append("Review asset location annually")
        recommendations.append("Coordinate with tax advisor before year-end")
        
        return recommendations


class ESGScoringSystem:
    """ESG (Environmental, Social, Governance) scoring and integration"""
    
    def __init__(self):
        self.esg_database: Dict[str, ESGScore] = {}
        self._initialize_esg_data()
        
    def _initialize_esg_data(self):
        """Initialize ESG scores for common assets"""
        # Simplified ESG scores
        self.esg_database = {
            'TSLA': ESGScore('TSLA', 90, 70, 60, 73, []),
            'AAPL': ESGScore('AAPL', 85, 80, 90, 85, []),
            'XOM': ESGScore('XOM', 30, 60, 70, 53, ['fossil_fuels']),
            'MSFT': ESGScore('MSFT', 88, 85, 95, 89, []),
            'SPY': ESGScore('SPY', 65, 70, 75, 70, []),
        }
    
    async def score_asset(self, asset: str) -> ESGScore:
        """Get ESG score for asset"""
        if asset in self.esg_database:
            return self.esg_database[asset]
        
        # Default score for unknown assets
        return ESGScore(
            asset=asset,
            environmental=50,
            social=50,
            governance=50,
            overall=50,
            controversies=[]
        )
    
    async def score_portfolio(self, portfolio: Dict) -> Dict:
        """Calculate portfolio-level ESG score"""
        positions = portfolio.get('positions', [])
        
        if not positions:
            return {'overall': 50, 'breakdown': {}}
        
        total_value = sum(p.get('value', 0) for p in positions)
        weighted_scores = {'environmental': 0, 'social': 0, 'governance': 0}
        
        for pos in positions:
            asset = pos.get('symbol')
            value = pos.get('value', 0)
            weight = value / total_value if total_value > 0 else 0
            
            esg = await self.score_asset(asset)
            weighted_scores['environmental'] += esg.environmental * weight
            weighted_scores['social'] += esg.social * weight
            weighted_scores['governance'] += esg.governance * weight
        
        overall = sum(weighted_scores.values()) / 3
        
        return {
            'overall': overall,
            'breakdown': weighted_scores,
            'rating': self._get_esg_rating(overall),
            'controversies': self._aggregate_controversies(positions)
        }
    
    def _get_esg_rating(self, score: float) -> str:
        """Convert score to rating"""
        if score >= 80:
            return 'AAA'
        elif score >= 70:
            return 'AA'
        elif score >= 60:
            return 'A'
        elif score >= 50:
            return 'BBB'
        elif score >= 40:
            return 'BB'
        else:
            return 'B'
    
    def _aggregate_controversies(self, positions: List[Dict]) -> List[str]:
        """Aggregate controversies across portfolio"""
        controversies = set()
        for pos in positions:
            asset = pos.get('symbol')
            if asset in self.esg_database:
                controversies.update(self.esg_database[asset].controversies)
        return list(controversies)
    
    async def filter_by_esg(
        self,
        assets: List[str],
        min_score: float = 60
    ) -> List[str]:
        """Filter assets by minimum ESG score"""
        filtered = []
        
        for asset in assets:
            esg = await self.score_asset(asset)
            if esg.overall >= min_score:
                filtered.append(asset)
        
        return filtered


class RiskProfileManager:
    """Customizable risk profile management"""
    
    def __init__(self):
        self.profiles = {
            RiskProfile.CONSERVATIVE: {
                'equity_allocation': 0.3,
                'max_volatility': 0.10,
                'max_drawdown': 0.10,
                'target_sharpe': 0.8
            },
            RiskProfile.MODERATE: {
                'equity_allocation': 0.6,
                'max_volatility': 0.15,
                'max_drawdown': 0.15,
                'target_sharpe': 1.0
            },
            RiskProfile.AGGRESSIVE: {
                'equity_allocation': 0.8,
                'max_volatility': 0.20,
                'max_drawdown': 0.20,
                'target_sharpe': 1.2
            },
            RiskProfile.VERY_AGGRESSIVE: {
                'equity_allocation': 1.0,
                'max_volatility': 0.30,
                'max_drawdown': 0.30,
                'target_sharpe': 1.5
            }
        }
    
    def get_allocation(self, client: ClientProfile) -> Dict:
        """Get asset allocation for client risk profile"""
        profile_config = self.profiles[client.risk_profile]
        equity_pct = profile_config['equity_allocation']
        
        # Adjust for age (rule of thumb: 100 - age = equity %)
        age_adjustment = 1.0  # Would calculate from client data
        
        return {
            'equities': equity_pct * age_adjustment,
            'bonds': (1 - equity_pct) * 0.7,
            'alternatives': (1 - equity_pct) * 0.2,
            'cash': (1 - equity_pct) * 0.1,
            'constraints': profile_config
        }
    
    def check_compliance(
        self,
        portfolio: Dict,
        client: ClientProfile
    ) -> Dict:
        """Check if portfolio complies with risk profile"""
        profile_config = self.profiles[client.risk_profile]
        
        current_volatility = portfolio.get('volatility', 0)
        current_drawdown = portfolio.get('max_drawdown', 0)
        
        violations = []
        
        if current_volatility > profile_config['max_volatility']:
            violations.append({
                'type': 'volatility',
                'limit': profile_config['max_volatility'],
                'actual': current_volatility
            })
        
        if current_drawdown > profile_config['max_drawdown']:
            violations.append({
                'type': 'drawdown',
                'limit': profile_config['max_drawdown'],
                'actual': current_drawdown
            })
        
        return {
            'compliant': len(violations) == 0,
            'violations': violations,
            'risk_score': self._calculate_risk_score(portfolio, profile_config)
        }
    
    def _calculate_risk_score(self, portfolio: Dict, config: Dict) -> float:
        """Calculate risk score relative to profile"""
        vol_ratio = portfolio.get('volatility', 0) / config['max_volatility']
        dd_ratio = portfolio.get('max_drawdown', 0) / config['max_drawdown']
        
        risk_score = (vol_ratio + dd_ratio) / 2
        return min(risk_score, 2.0)  # Cap at 2x over limit


class ClientPortalManager:
    """Personalized client portal management"""
    
    def __init__(self):
        self.clients: Dict[str, ClientProfile] = {}
        self.tax_engine = TaxOptimizationEngine()
        self.esg_system = ESGScoringSystem()
        self.risk_manager = RiskProfileManager()
        
    async def create_client_report(
        self,
        client_id: str,
        portfolio: Dict
    ) -> Dict:
        """Generate comprehensive client report"""
        
        if client_id not in self.clients:
            return {'error': 'Client not found'}
        
        client = self.clients[client_id]
        
        # 1. Performance metrics
        performance = self._calculate_performance(portfolio)
        
        # 2. Tax optimization
        tax_strategy = await self.tax_engine.optimize_tax_strategy(
            portfolio, client
        )
        
        # 3. ESG scoring
        esg_score = await self.esg_system.score_portfolio(portfolio)
        
        # 4. Risk compliance
        risk_compliance = self.risk_manager.check_compliance(portfolio, client)
        
        # 5. Recommendations
        recommendations = self._generate_client_recommendations(
            client, portfolio, performance, risk_compliance
        )
        
        return {
            'client': client,
            'performance': performance,
            'tax_strategy': tax_strategy,
            'esg_score': esg_score,
            'risk_compliance': risk_compliance,
            'recommendations': recommendations,
            'timestamp': datetime.now()
        }
    
    def _calculate_performance(self, portfolio: Dict) -> Dict:
        """Calculate portfolio performance metrics"""
        returns = portfolio.get('returns', [])
        
        if not returns:
            return {'error': 'No return data'}
        
        returns_array = np.array(returns)
        
        return {
            'total_return': float(np.sum(returns_array)),
            'annualized_return': float(np.mean(returns_array) * 252),
            'volatility': float(np.std(returns_array) * np.sqrt(252)),
            'sharpe_ratio': float(np.mean(returns_array) / np.std(returns_array) * np.sqrt(252)) if np.std(returns_array) > 0 else 0,
            'max_drawdown': float(self._calculate_max_drawdown(returns_array)),
            'win_rate': float(np.sum(returns_array > 0) / len(returns_array))
        }
    
    def _calculate_max_drawdown(self, returns: np.ndarray) -> float:
        """Calculate maximum drawdown"""
        cumulative = np.cumprod(1 + returns)
        running_max = np.maximum.accumulate(cumulative)
        drawdown = (cumulative - running_max) / running_max
        return float(np.min(drawdown))
    
    def _generate_client_recommendations(
        self,
        client: ClientProfile,
        portfolio: Dict,
        performance: Dict,
        risk_compliance: Dict
    ) -> List[str]:
        """Generate personalized recommendations"""
        recommendations = []
        
        # Performance-based
        if performance.get('sharpe_ratio', 0) < 1.0:
            recommendations.append("Consider rebalancing to improve risk-adjusted returns")
        
        # Risk-based
        if not risk_compliance['compliant']:
            recommendations.append("Portfolio exceeds risk limits - reduce exposure")
        
        # Tax-based
        if client.tax_bracket > 0.3:
            recommendations.append("Implement tax-loss harvesting strategy")
        
        # ESG-based
        if client.esg_preference > 0.7:
            recommendations.append("Increase allocation to high-ESG assets")
        
        return recommendations
    
    def register_client(self, client: ClientProfile):
        """Register new client"""
        self.clients[client.client_id] = client
