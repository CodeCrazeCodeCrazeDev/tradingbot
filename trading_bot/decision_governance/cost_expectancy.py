"""
Cost-Adjusted Expectancy Model

Calculates expected returns after accounting for all trading costs.
Includes explicit and implicit costs, slippage, market impact, and opportunity cost.
"""

from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


@dataclass
class TradingCosts:
    """Complete breakdown of trading costs"""
    explicit_commission: float  # Direct commission/fees
    explicit_fees: float  # Exchange fees, clearing fees
    bid_ask_spread: float  # Half-spread as cost
    estimated_slippage: float  # Execution slippage
    market_impact: float  # Price impact of order
    opportunity_cost: float  # Cost of delayed fills
    adverse_selection: float  # Cost from trading against informed flow
    total_costs: float  # Sum of all costs


@dataclass
class CostAdjustedExpectancy:
    """Expectancy after adjusting for costs"""
    symbol: str
    gross_expectancy: float  # Before costs
    net_expectancy: float  # After costs
    total_costs: float  # As percentage
    win_rate_required: float  # Win rate needed to break even
    edge_after_costs: float  # Remaining edge (expectancy - breakeven)
    viable: bool  # Is this trade viable after costs?
    cost_breakdown: TradingCosts
    recommendation: str


class CostAdjustedExpectancyModel:
    """
    Models complete trading costs and calculates cost-adjusted expectancy.
    
    Prevents trades where costs would eliminate all edge.
    """
    
    def __init__(
        self,
        default_commission_pct: float = 0.001,  # 10 bps
        min_viable_edge_bps: float = 5.0  # 5 bps minimum edge required
    ):
        self.default_commission = default_commission_pct
        self.min_viable_edge = min_viable_edge_bps / 10000  # Convert to decimal
        
        # Cost estimates by asset class
        self.cost_estimates: Dict[str, Dict] = {
            'large_cap_equity': {
                'spread_bps': 5,
                'slippage_bps': 2,
                'impact_bps_per_lot': 1
            },
            'small_cap_equity': {
                'spread_bps': 20,
                'slippage_bps': 10,
                'impact_bps_per_lot': 5
            },
            'liquid_etf': {
                'spread_bps': 3,
                'slippage_bps': 1,
                'impact_bps_per_lot': 0.5
            },
            'crypto_major': {
                'spread_bps': 10,
                'slippage_bps': 5,
                'impact_bps_per_lot': 2
            },
            'crypto_alt': {
                'spread_bps': 50,
                'slippage_bps': 30,
                'impact_bps_per_lot': 20
            }
        }
        
    def calculate_expectancy(
        self,
        symbol: str,
        direction: str,
        target_price: float,
        stop_loss: float,
        position_size: float,
        win_probability: float,
        asset_class: str = 'large_cap_equity',
        market_conditions: Optional[Dict] = None
    ) -> CostAdjustedExpectancy:
        """
        Calculate cost-adjusted expectancy for a trade.
        
        Args:
            symbol: Trading symbol
            direction: 'buy' or 'sell'
            target_price: Target exit price
            stop_loss: Stop loss price
            position_size: Position size in currency
            win_probability: Estimated probability of winning
            asset_class: Asset classification for cost estimates
            market_conditions: Current market conditions
            
        Returns:
            CostAdjustedExpectancy
        """
        # Calculate gross expectancy (before costs)
        current_price = market_conditions.get('current_price', target_price) if market_conditions else target_price
        
        if direction == 'buy':
            potential_gain = (target_price - current_price) / current_price
            potential_loss = (current_price - stop_loss) / current_price
        else:  # sell
            potential_gain = (current_price - target_price) / current_price
            potential_loss = (stop_loss - current_price) / current_price
            
        gross_expectancy = (win_probability * potential_gain) - ((1 - win_probability) * potential_loss)
        
        # Calculate all trading costs
        costs = self._calculate_costs(
            symbol, position_size, asset_class, market_conditions or {}
        )
        
        # Net expectancy after costs
        # Costs apply on both entry and exit (round trip)
        total_costs = costs.total_costs * 2  # Entry + exit
        net_expectancy = gross_expectancy - total_costs
        
        # Calculate required win rate to break even
        avg_win = potential_gain
        avg_loss = potential_loss + total_costs  # Include costs in loss
        
        if avg_win + avg_loss > 0:
            required_wr = avg_loss / (avg_win + avg_loss)
        else:
            required_wr = 0.5
            
        # Remaining edge
        edge = win_probability - required_wr
        
        # Determine viability
        viable = edge > self.min_viable_edge and net_expectancy > 0
        
        # Generate recommendation
        if viable:
            recommendation = f"Viable: Net expectancy {net_expectancy:.2%} after {total_costs:.3%} costs"
        elif net_expectancy > 0:
            recommendation = f"Marginal: Thin edge of {edge:.2%} - consider larger size or skip"
        else:
            recommendation = f"Not viable: Costs ({total_costs:.3%}) exceed expectancy ({gross_expectancy:.2%})"
            
        return CostAdjustedExpectancy(
            symbol=symbol,
            gross_expectancy=gross_expectancy,
            net_expectancy=net_expectancy,
            total_costs=total_costs,
            win_rate_required=required_wr,
            edge_after_costs=edge,
            viable=viable,
            cost_breakdown=costs,
            recommendation=recommendation
        )
    
    def _calculate_costs(
        self,
        symbol: str,
        position_size: float,
        asset_class: str,
        market_conditions: Dict
    ) -> TradingCosts:
        """Calculate complete trading costs"""
        
        # Get cost estimates for asset class
        estimates = self.cost_estimates.get(asset_class, self.cost_estimates['large_cap_equity'])
        
        # Explicit costs
        commission = self.default_commission
        fees = commission * 0.3  # Assume fees are 30% of commission
        
        # Spread cost (half-spread, paid on entry)
        spread_bps = market_conditions.get('spread_bps', estimates['spread_bps'])
        spread_cost = spread_bps / 10000 / 2  # Half spread
        
        # Slippage
        base_slippage = estimates['slippage_bps'] / 10000
        liquidity_factor = self._liquidity_factor(market_conditions)
        volatility_factor = market_conditions.get('volatility', 0.2) / 0.2  # Normalize
        slippage = base_slippage * liquidity_factor * volatility_factor
        
        # Market impact (square root model)
        avg_daily_volume = market_conditions.get('adv', position_size * 10)
        participation_rate = position_size / avg_daily_volume if avg_daily_volume > 0 else 0.01
        impact_bps = estimates['impact_bps_per_lot'] * (participation_rate ** 0.5) * 100
        impact = impact_bps / 10000
        
        # Opportunity cost (time value of unfilled orders)
        fill_time_hours = market_conditions.get('expected_fill_hours', 1)
        opp_cost = 0.0001 * fill_time_hours  # 1 bps per hour
        
        # Adverse selection (higher in toxic flow)
        toxicity = market_conditions.get('flow_toxicity', 0.3)
        adverse = toxicity * 0.0002  # Up to 2 bps
        
        total = commission + fees + spread_cost + slippage + impact + opp_cost + adverse
        
        return TradingCosts(
            explicit_commission=commission,
            explicit_fees=fees,
            bid_ask_spread=spread_cost,
            estimated_slippage=slippage,
            market_impact=impact,
            opportunity_cost=opp_cost,
            adverse_selection=adverse,
            total_costs=total
        )
    
    def _liquidity_factor(self, market_conditions: Dict) -> float:
        """Calculate liquidity adjustment factor"""
        
        # Higher liquidity = lower factor (better)
        depth_score = market_conditions.get('depth_score', 0.5)
        return 2.0 - depth_score  # 1.0 to 2.0 range
    
    def optimize_position_size_for_costs(
        self,
        symbol: str,
        asset_class: str,
        desired_size: float,
        market_conditions: Dict
    ) -> Tuple[float, float]:
        """
        Optimize position size to minimize cost impact.
        
        Returns:
            Tuple of (optimal_size, expected_costs)
        """
        
        adv = market_conditions.get('adv', desired_size * 10)
        
        # Optimal participation: typically 5-10% of ADV
        max_participation = 0.10
        optimal_size = min(desired_size, adv * max_participation)
        
        # Calculate costs at optimal size
        costs = self._calculate_costs(symbol, optimal_size, asset_class, market_conditions)
        
        return optimal_size, costs.total_costs * 2
    
    def get_cost_estimate_report(
        self,
        symbol: str,
        asset_class: str
    ) -> Dict[str, Any]:
        """Generate cost estimate report for an asset class"""
        
        estimates = self.cost_estimates.get(asset_class, {})
        
        # Calculate for sample sizes
        sample_sizes = [10000, 50000, 100000, 500000]
        size_costs = []
        
        for size in sample_sizes:
            costs = self._calculate_costs(
                symbol, size, asset_class, 
                {'adv': size * 20, 'depth_score': 0.6, 'volatility': 0.2}
            )
            size_costs.append({
                'size': size,
                'total_cost_pct': costs.total_costs * 2,  # Round trip
                'impact_pct': costs.market_impact * 2
            })
            
        return {
            'asset_class': asset_class,
            'base_costs': {
                'spread_bps': estimates.get('spread_bps', 0),
                'commission_bps': self.default_commission * 10000
            },
            'costs_by_size': size_costs,
            'recommendation': 'Larger trades have higher impact costs - consider breaking into smaller orders'
        }
    
    def generate_cost_breakeven_analysis(
        self,
        symbol: str,
        asset_class: str,
        position_size: float,
        target_gain_pct: float,
        stop_loss_pct: float
    ) -> Dict[str, Any]:
        """
        Generate breakeven analysis for a trade.
        
        Shows what win rate is needed at different cost levels.
        """
        
        # Calculate costs
        costs = self._calculate_costs(
            symbol, position_size, asset_class,
            {'adv': position_size * 20}
        )
        
        total_costs = costs.total_costs * 2
        
        # Breakeven calculation
        gross_win = target_gain_pct / 100
        gross_loss = stop_loss_pct / 100
        
        # With costs, loss is worse and win is reduced
        net_win = gross_win - total_costs
        net_loss = gross_loss + total_costs
        
        if net_win + net_loss > 0:
            breakeven_wr = net_loss / (net_win + net_loss)
        else:
            breakeven_wr = 0.5
            
        # Generate scenarios
        scenarios = []
        for wr in [0.4, 0.45, 0.5, 0.55, 0.6, 0.65, 0.7]:
            expectancy = (wr * net_win) - ((1 - wr) * net_loss)
            scenarios.append({
                'win_rate': wr,
                'net_expectancy': expectancy,
                'viable': expectancy > 0
            })
            
        return {
            'cost_summary': {
                'round_trip_costs': total_costs,
                'commission': costs.explicit_commission * 2,
                'spread_slippage': (costs.bid_ask_spread + costs.estimated_slippage) * 2,
                'market_impact': costs.market_impact * 2
            },
            'breakeven_analysis': {
                'required_win_rate': breakeven_wr,
                'required_win_rate_pct': f"{breakeven_wr:.1%}"
            },
            'win_rate_scenarios': scenarios,
            'recommendation': (
                f"Need {breakeven_wr:.1%} win rate to breakeven after costs"
            )
        }
