"""
Free Wealth Management System ($0 Budget)
Uses free data sources and open-source libraries
"""

import numpy as np
from typing import Dict, List
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
import numpy

import logging
logger = logging.getLogger(__name__)



class FreeRiskProfile(Enum):
    """Free risk profiles"""
    CONSERVATIVE = "conservative"
    MODERATE = "moderate"
    AGGRESSIVE = "aggressive"


@dataclass
class FreeClient:
    """Free client profile"""
    client_id: str
    name: str
    risk_profile: FreeRiskProfile
    initial_capital: float
    target_return: float


class FreeTaxOptimizer:
    """Free tax optimization using public tax rules"""
    
    def __init__(self):
        try:
            self.tax_brackets = {
                'low': 0.12,
                'medium': 0.22,
                'high': 0.32
            }
        except Exception as e:
            logger.error(f"Error in __init__: {e}")
            raise
        
    def calculate_tax_loss_harvest(self, positions: List[Dict]) -> Dict:
        """Calculate free tax loss harvesting opportunities"""
        
        try:
            opportunities = []
            total_loss = 0
        
            for pos in positions:
                unrealized_pnl = pos.get('unrealized_pnl', 0)
            
                if unrealized_pnl < -100:  # Loss threshold
                    tax_benefit = abs(unrealized_pnl) * 0.22  # Assume 22% bracket
                    opportunities.append({
                        'symbol': pos.get('symbol'),
                        'loss': abs(unrealized_pnl),
                        'tax_benefit': tax_benefit,
                        'action': 'sell_and_replace'
                    })
                    total_loss += abs(unrealized_pnl)
        
            return {
                'opportunities': opportunities,
                'total_loss': total_loss,
                'estimated_tax_savings': total_loss * 0.22,
                'cost': 0  # Free analysis
            }
        except Exception as e:
            logger.error(f"Error in calculate_tax_loss_harvest: {e}")
            raise
    
    def optimize_holding_period(self, trade: Dict) -> Dict:
        """Optimize holding period for tax efficiency"""
        
        try:
            entry_date = trade.get('entry_date', datetime.now())
            days_held = (datetime.now() - entry_date).days
        
            # Long-term capital gains after 365 days
            if days_held < 365:
                days_to_ltcg = 365 - days_held
                potential_savings = trade.get('unrealized_pnl', 0) * 0.15  # 15% savings
            
                return {
                    'recommendation': 'hold',
                    'days_to_ltcg': days_to_ltcg,
                    'potential_savings': potential_savings,
                    'reason': 'qualify_for_long_term_gains'
                }
        
            return {
                'recommendation': 'flexible',
                'reason': 'already_long_term',
                'tax_rate': 0.15  # Long-term rate
            }
        except Exception as e:
            logger.error(f"Error in optimize_holding_period: {e}")
            raise


class FreeESGScorer:
    """Free ESG scoring using public data"""
    
    def __init__(self):
        # Free ESG scores from public sources
        try:
            self.esg_database = {
                'AAPL': {'e': 85, 's': 80, 'g': 90, 'overall': 85},
                'TSLA': {'e': 90, 's': 70, 'g': 60, 'overall': 73},
                'MSFT': {'e': 88, 's': 85, 'g': 95, 'overall': 89},
                'GOOGL': {'e': 82, 's': 78, 'g': 85, 'overall': 82},
                'AMZN': {'e': 75, 's': 72, 'g': 80, 'overall': 76},
            }
        except Exception as e:
            logger.error(f"Error in __init__: {e}")
            raise
        
    def score_asset(self, symbol: str) -> Dict:
        """Get free ESG score"""
        
        try:
            if symbol in self.esg_database:
                return self.esg_database[symbol]
        
            # Default score for unknown assets
            return {'e': 50, 's': 50, 'g': 50, 'overall': 50}
        except Exception as e:
            logger.error(f"Error in score_asset: {e}")
            raise
    
    def score_portfolio(self, positions: List[Dict]) -> Dict:
        """Calculate portfolio ESG score"""
        
        try:
            if not positions:
                return {'overall': 0, 'breakdown': {}}
        
            total_value = sum(p.get('value', 0) for p in positions)
            weighted_score = 0
        
            for pos in positions:
                symbol = pos.get('symbol')
                value = pos.get('value', 0)
                weight = value / total_value if total_value > 0 else 0
            
                esg = self.score_asset(symbol)
                weighted_score += esg['overall'] * weight
        
            # Rating
            if weighted_score >= 80:
                rating = 'A'
            elif weighted_score >= 60:
                rating = 'B'
            else:
                rating = 'C'
        
            return {
                'overall': weighted_score,
                'rating': rating,
                'cost': 0  # Free scoring
            }
        except Exception as e:
            logger.error(f"Error in score_portfolio: {e}")
            raise
    
    def filter_by_esg(self, symbols: List[str], min_score: float = 70) -> List[str]:
        """Filter assets by ESG score"""
        
        try:
            filtered = []
            for symbol in symbols:
                score = self.score_asset(symbol)
                if score['overall'] >= min_score:
                    filtered.append(symbol)
        
            return filtered
        except Exception as e:
            logger.error(f"Error in filter_by_esg: {e}")
            raise


class FreePortfolioAnalyzer:
    """Free portfolio analysis"""
    
    def calculate_performance(self, returns: np.ndarray) -> Dict:
        """Calculate free performance metrics"""
        
        try:
            if len(returns) == 0:
                return {}
        
            # Total return
            total_return = np.sum(returns)
        
            # Annualized return (assume daily returns)
            annualized_return = np.mean(returns) * 252
        
            # Volatility
            volatility = np.std(returns) * np.sqrt(252)
        
            # Sharpe ratio (assume 0% risk-free rate)
            sharpe = annualized_return / volatility if volatility > 0 else 0
        
            # Max drawdown
            cumulative = np.cumprod(1 + returns)
            running_max = np.maximum.accumulate(cumulative)
            drawdown = (cumulative - running_max) / running_max
            max_drawdown = np.min(drawdown)
        
            # Win rate
            win_rate = np.sum(returns > 0) / len(returns)
        
            return {
                'total_return': total_return,
                'annualized_return': annualized_return,
                'volatility': volatility,
                'sharpe_ratio': sharpe,
                'max_drawdown': max_drawdown,
                'win_rate': win_rate,
                'num_periods': len(returns)
            }
        except Exception as e:
            logger.error(f"Error in calculate_performance: {e}")
            raise
    
    def calculate_risk_metrics(self, returns: np.ndarray, confidence: float = 0.95) -> Dict:
        """Calculate free risk metrics"""
        
        try:
            if len(returns) == 0:
                return {}
        
            # Value at Risk (VaR)
            var = np.percentile(returns, (1 - confidence) * 100)
        
            # Conditional VaR (CVaR)
            cvar = np.mean(returns[returns <= var])
        
            # Sortino ratio (downside deviation)
            downside_returns = returns[returns < 0]
            downside_std = np.std(downside_returns) if len(downside_returns) > 0 else 0
            sortino = np.mean(returns) * 252 / (downside_std * np.sqrt(252)) if downside_std > 0 else 0
        
            return {
                'var_95': var,
                'cvar_95': cvar,
                'sortino_ratio': sortino,
                'downside_deviation': downside_std
            }
        except Exception as e:
            logger.error(f"Error in calculate_risk_metrics: {e}")
            raise


class FreeWealthManager:
    """Free unified wealth management system"""
    
    def __init__(self):
        try:
            self.tax_optimizer = FreeTaxOptimizer()
            self.esg_scorer = FreeESGScorer()
            self.portfolio_analyzer = FreePortfolioAnalyzer()
            self.clients: Dict[str, FreeClient] = {}
        except Exception as e:
            logger.error(f"Error in __init__: {e}")
            raise
        
    def register_client(
        self,
        name: str,
        risk_profile: str,
        initial_capital: float,
        target_return: float = 0.10
    ) -> str:
        """Register new client (free)"""
        
        try:
            client_id = f"client_{len(self.clients) + 1}"
        
            client = FreeClient(
                client_id=client_id,
                name=name,
                risk_profile=FreeRiskProfile(risk_profile),
                initial_capital=initial_capital,
                target_return=target_return
            )
        
            self.clients[client_id] = client
            return client_id
        except Exception as e:
            logger.error(f"Error in register_client: {e}")
            raise
    
    def generate_client_report(
        self,
        client_id: str,
        positions: List[Dict],
        returns: np.ndarray
    ) -> Dict:
        """Generate free client report"""
        
        try:
            if client_id not in self.clients:
                return {'error': 'Client not found'}
        
            client = self.clients[client_id]
        
            # 1. Performance analysis
            performance = self.portfolio_analyzer.calculate_performance(returns)
            risk_metrics = self.portfolio_analyzer.calculate_risk_metrics(returns)
        
            # 2. Tax optimization
            tax_harvest = self.tax_optimizer.calculate_tax_loss_harvest(positions)
        
            # 3. ESG scoring
            esg_score = self.esg_scorer.score_portfolio(positions)
        
            # 4. Risk profile compliance
            target_vol = {
                FreeRiskProfile.CONSERVATIVE: 0.10,
                FreeRiskProfile.MODERATE: 0.15,
                FreeRiskProfile.AGGRESSIVE: 0.25
            }
        
            compliant = performance.get('volatility', 0) <= target_vol[client.risk_profile]
        
            # 5. Recommendations
            recommendations = []
        
            if not compliant:
                recommendations.append("Reduce volatility to match risk profile")
        
            if performance.get('sharpe_ratio', 0) < 1.0:
                recommendations.append("Improve risk-adjusted returns")
        
            if tax_harvest['total_loss'] > 1000:
                recommendations.append(f"Harvest ${tax_harvest['total_loss']:.0f} in tax losses")
        
            if esg_score['overall'] < 70 and client.risk_profile != FreeRiskProfile.AGGRESSIVE:
                recommendations.append("Consider higher ESG-rated assets")
        
            return {
                'client': {
                    'name': client.name,
                    'risk_profile': client.risk_profile.value,
                    'target_return': client.target_return
                },
                'performance': performance,
                'risk_metrics': risk_metrics,
                'tax_optimization': tax_harvest,
                'esg_score': esg_score,
                'risk_compliant': compliant,
                'recommendations': recommendations,
                'cost': 0,  # $0 budget
                'timestamp': datetime.now()
            }
        except Exception as e:
            logger.error(f"Error in generate_client_report: {e}")
            raise
    
    def get_asset_allocation(self, risk_profile: str) -> Dict:
        """Get free asset allocation recommendation"""
        
        try:
            allocations = {
                'conservative': {
                    'stocks': 0.30,
                    'bonds': 0.50,
                    'cash': 0.20
                },
                'moderate': {
                    'stocks': 0.60,
                    'bonds': 0.30,
                    'cash': 0.10
                },
                'aggressive': {
                    'stocks': 0.80,
                    'bonds': 0.15,
                    'cash': 0.05
                }
            }
        
            return allocations.get(risk_profile, allocations['moderate'])
        except Exception as e:
            logger.error(f"Error in get_asset_allocation: {e}")
            raise


# Example usage
if __name__ == '__main__':
    # Initialize free wealth manager
    wealth_manager = FreeWealthManager()
    
    # Register client
    client_id = wealth_manager.register_client(
        name='John Doe',
        risk_profile='moderate',
        initial_capital=10000,
        target_return=0.12
    )
    
    # Portfolio positions
    positions = [
        {'symbol': 'AAPL', 'value': 3000, 'unrealized_pnl': 300},
        {'symbol': 'TSLA', 'value': 2000, 'unrealized_pnl': -200},
        {'symbol': 'MSFT', 'value': 2500, 'unrealized_pnl': 150},
        {'symbol': 'GOOGL', 'value': 1500, 'unrealized_pnl': 100},
        {'symbol': 'AMZN', 'value': 1000, 'unrealized_pnl': -50}
    ]
    
    # Generate returns (mock data)
    np.random.seed(42)
    returns = np.random.randn(252) * 0.01  # Daily returns
    
    # Generate report
    report = wealth_manager.generate_client_report(client_id, positions, returns)
    
    logger.info("Free Wealth Management Report:")
    logger.info(f"Client: {report['client']['name']}")
    logger.info(f"Risk Profile: {report['client']['risk_profile']}")
    logger.info(f"\nPerformance:")
    logger.info(f"  Total Return: {report['performance']['total_return']:.2%}")
    logger.info(f"  Sharpe Ratio: {report['performance']['sharpe_ratio']:.2f}")
    logger.info(f"  Max Drawdown: {report['performance']['max_drawdown']:.2%}")
    logger.info(f"\nTax Optimization:")
    logger.info(f"  Potential Savings: ${report['tax_optimization']['estimated_tax_savings']:.2f}")
    logger.info(f"\nESG Score: {report['esg_score']['overall']:.1f} ({report['esg_score']['rating']})")
    logger.info(f"\nRecommendations: {len(report['recommendations'])}")
    for rec in report['recommendations']:
        logger.info(f"  - {rec}")
    logger.info(f"\nCost: ${report['cost']}")
