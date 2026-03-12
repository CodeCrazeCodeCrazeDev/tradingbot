"""
Tier 8: Execution & Post-Trade Intelligence
Optimizes trade execution and analyzes performance
"""

import numpy as np
import pandas as pd
from typing import Any, Dict, List, Optional, Tuple
import logging
from dataclasses import dataclass
from datetime import datetime, timedelta

from trading_bot.brain.tier_structure import (
    TierBase, MarketStateVector, OrderFlowIntelligence, 
    MarketGeometryModel, RegimeContextVector, SentimentVector, 
    MacroContext, RiskParameters, ExecutionIntelligence
)

logger = logging.getLogger(__name__)


@dataclass
class VenueMetrics:
    """Execution venue performance metrics"""
    name: str
    fill_rate: float
    avg_slippage: float
    avg_latency: float
    cost_score: float
    reliability: float


class SmartOrderRouter:
    """Smart Order Routing (SOR) system"""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self.min_fill_rate = self.config.get('min_fill_rate', 0.8)
        self.max_slippage = self.config.get('max_slippage', 0.001)
    
    def select_venue(self, venues: List[VenueMetrics], 
                    order_size: float,
                    urgency: float) -> Dict[str, Any]:
        """
        Select optimal execution venue
        
        Args:
            venues: List of venue metrics
            order_size: Size of the order
            urgency: Execution urgency (0-1)
            
        Returns:
            Dictionary with venue selection and routing plan
        """
        try:
            # Filter venues by minimum requirements
            valid_venues = [
                v for v in venues
                if v.fill_rate >= self.min_fill_rate and
                v.avg_slippage <= self.max_slippage
            ]
            
            if not valid_venues:
                valid_venues = venues  # Use all venues if none meet criteria
            
            # Calculate venue scores
            venue_scores = []
            for venue in valid_venues:
                # Base score on fill rate and slippage
                score = (
                    0.4 * venue.fill_rate +
                    0.3 * (1 - venue.avg_slippage / self.max_slippage) +
                    0.2 * venue.reliability +
                    0.1 * (1 - venue.cost_score)
                )
                
                # Adjust for urgency
                if urgency > 0.8:
                    # Prioritize fill rate and latency for urgent orders
                    score *= (venue.fill_rate * (1 - venue.avg_latency/1000))
                
                venue_scores.append((venue, score))
            
            # Sort venues by score
            sorted_venues = sorted(venue_scores, key=lambda x: x[1], reverse=True)
            
            # Select primary and backup venues
            primary = sorted_venues[0][0]
            backup = sorted_venues[1][0] if len(sorted_venues) > 1 else None
            
            # Calculate order splits based on venue capacity
            splits = self._calculate_splits(order_size, [v[0] for v in sorted_venues[:3]])
            
            return {
                'primary_venue': primary.name,
                'backup_venue': backup.name if backup else None,
                'venue_splits': splits,
                'expected_fill_rate': primary.fill_rate,
                'expected_slippage': primary.avg_slippage,
                'expected_latency': primary.avg_latency
            }
            
        except Exception as e:
            logger.error(f"Error selecting venue: {str(e)}")
            return {
                'primary_venue': venues[0].name if venues else None,
                'backup_venue': None,
                'venue_splits': {venues[0].name: 1.0} if venues else {},
                'expected_fill_rate': 0.0,
                'expected_slippage': 0.0,
                'expected_latency': 0.0
            }
    
    def _calculate_splits(self, order_size: float, 
                         venues: List[VenueMetrics]) -> Dict[str, float]:
        """Calculate optimal order splits across venues"""
        total_score = sum(v.fill_rate * (1 - v.avg_slippage) for v in venues)
        
        if total_score == 0:
            return {venues[0].name: 1.0} if venues else {}
        
        splits = {}
        for venue in venues:
            score = venue.fill_rate * (1 - venue.avg_slippage)
            splits[venue.name] = score / total_score
        
        return splits


class SlippageMonitor:
    """Real-time slippage monitoring"""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self.slippage_threshold = self.config.get('slippage_threshold', 0.001)
        self.window_size = self.config.get('window_size', 100)
        self.history: List[Dict] = []
    
    def analyze_slippage(self, execution_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze execution slippage
        
        Args:
            execution_data: Dictionary with execution details
            
        Returns:
            Dictionary with slippage analysis
        """
        try:
            # Calculate slippage
            expected_price = execution_data.get('expected_price', 0)
            actual_price = execution_data.get('actual_price', 0)
            
            if expected_price == 0:
                return {
                    'slippage': 0.0,
                    'is_adverse': False,
                    'severity': 'none',
                    'trend': 'stable'
                }
            
            slippage = (actual_price - expected_price) / expected_price
            
            # Update history
            self.history.append({
                'timestamp': execution_data.get('timestamp', datetime.now()),
                'slippage': slippage,
                'venue': execution_data.get('venue', 'unknown')
            })
            
            # Keep history within window
            if len(self.history) > self.window_size:
                self.history = self.history[-self.window_size:]
            
            # Calculate metrics
            avg_slippage = np.mean([h['slippage'] for h in self.history])
            std_slippage = np.std([h['slippage'] for h in self.history])
            
            # Determine severity
            if abs(slippage) > self.slippage_threshold * 2:
                severity = 'high'
            elif abs(slippage) > self.slippage_threshold:
                severity = 'medium'
            else:
                severity = 'low'
            
            # Analyze trend
            recent_avg = np.mean([h['slippage'] for h in self.history[-10:]])
            old_avg = np.mean([h['slippage'] for h in self.history[:-10]])
            
            if recent_avg > old_avg * 1.1:
                trend = 'increasing'
            elif recent_avg < old_avg * 0.9:
                trend = 'decreasing'
            else:
                trend = 'stable'
            
            return {
                'slippage': slippage,
                'is_adverse': slippage > 0,
                'severity': severity,
                'trend': trend,
                'metrics': {
                    'average': avg_slippage,
                    'std_dev': std_slippage,
                    'max': max(h['slippage'] for h in self.history),
                    'min': min(h['slippage'] for h in self.history)
                }
            }
            
        except Exception as e:
            logger.error(f"Error analyzing slippage: {str(e)}")
            return {
                'slippage': 0.0,
                'is_adverse': False,
                'severity': 'none',
                'trend': 'stable'
            }


class ExecutionFrictionIndex:
    """Execution Friction Index (EFI) calculator"""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
    
    def calculate_efi(self, market_data: pd.DataFrame, 
                     execution_data: Dict[str, Any]) -> Dict[str, float]:
        """
        Calculate Execution Friction Index
        
        Args:
            market_data: OHLCV DataFrame
            execution_data: Dictionary with execution details
            
        Returns:
            Dictionary with EFI metrics
        """
        try:
            # Calculate market impact
            price = execution_data.get('price', 0)
            size = execution_data.get('size', 0)
            side = execution_data.get('side', 'buy')
            
            if price == 0 or size == 0:
                return {
                    'efi': 0.0,
                    'market_impact': 0.0,
                    'timing_cost': 0.0
                }
            
            # Calculate average daily volume
            adv = market_data['volume'].mean()
            
            # Calculate participation rate
            participation = size / adv if adv > 0 else 0
            
            # Calculate price impact
            pre_price = market_data['close'].iloc[-2]
            post_price = market_data['close'].iloc[-1]
            
            if side == 'buy':
                price_impact = (post_price - pre_price) / pre_price
            else:
                price_impact = (pre_price - post_price) / pre_price
            
            # Calculate timing cost
            vwap = (market_data['close'] * market_data['volume']).sum() / market_data['volume'].sum()
            timing_cost = abs(price - vwap) / vwap
            
            # Calculate EFI
            # Higher EFI means more friction/cost
            efi = (
                0.4 * abs(price_impact) +
                0.3 * timing_cost +
                0.3 * participation
            )
            
            return {
                'efi': efi,
                'market_impact': price_impact,
                'timing_cost': timing_cost,
                'participation_rate': participation,
                'price_to_vwap': price / vwap - 1
            }
            
        except Exception as e:
            logger.error(f"Error calculating EFI: {str(e)}")
            return {
                'efi': 0.0,
                'market_impact': 0.0,
                'timing_cost': 0.0,
                'participation_rate': 0.0,
                'price_to_vwap': 0.0
            }


class PostTradeAnalytics:
    """Post-trade analytics dashboard"""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
    
    def analyze_execution(self, execution_data: Dict[str, Any],
                         market_data: pd.DataFrame) -> Dict[str, Any]:
        """
        Analyze execution quality
        
        Args:
            execution_data: Dictionary with execution details
            market_data: OHLCV DataFrame
            
        Returns:
            Dictionary with execution analytics
        """
        try:
            # Calculate execution metrics
            fill_time = (execution_data.get('end_time', datetime.now()) - 
                        execution_data.get('start_time', datetime.now())).total_seconds()
            
            fill_rate = execution_data.get('filled_size', 0) / execution_data.get('order_size', 1)
            
            # Calculate price improvement
            limit_price = execution_data.get('limit_price', 0)
            executed_price = execution_data.get('average_price', 0)
            
            if limit_price > 0:
                if execution_data.get('side') == 'buy':
                    price_improvement = (limit_price - executed_price) / limit_price
                else:
                    price_improvement = (executed_price - limit_price) / limit_price
            else:
                price_improvement = 0.0
            
            # Calculate implementation shortfall
            arrival_price = execution_data.get('arrival_price', 0)
            if arrival_price > 0:
                shortfall = abs(executed_price - arrival_price) / arrival_price
            else:
                shortfall = 0.0
            
            # Calculate spread capture
            spread = market_data['high'].iloc[-1] - market_data['low'].iloc[-1]
            if spread > 0:
                spread_capture = abs(executed_price - arrival_price) / spread
            else:
                spread_capture = 0.0
            
            return {
                'execution_speed': fill_time,
                'fill_rate': fill_rate,
                'price_improvement': price_improvement,
                'implementation_shortfall': shortfall,
                'spread_capture': spread_capture,
                'metrics': {
                    'arrival_price': arrival_price,
                    'executed_price': executed_price,
                    'limit_price': limit_price,
                    'filled_size': execution_data.get('filled_size', 0),
                    'order_size': execution_data.get('order_size', 0)
                }
            }
            
        except Exception as e:
            logger.error(f"Error analyzing execution: {str(e)}")
            return {
                'execution_speed': 0.0,
                'fill_rate': 0.0,
                'price_improvement': 0.0,
                'implementation_shortfall': 0.0,
                'spread_capture': 0.0
            }


class Tier8ExecutionIntelligence(TierBase):
    """
    Tier 8: Execution & Post-Trade Intelligence
    
    Optimizes trade execution and analyzes performance:
    - Smart Order Routing (SOR)
    - Real-Time Slippage Monitor
    - Execution Friction Index (EFI)
    - Post-Trade Analytics
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__("Tier 8: Execution Intelligence", config)
        self.router = None
        self.slippage_monitor = None
        self.friction_index = None
        self.analytics = None
    
    def _initialize_components(self) -> None:
        """Initialize tier-specific components"""
        self.router = SmartOrderRouter(self.config.get('router', {}))
        self.slippage_monitor = SlippageMonitor(self.config.get('slippage', {}))
        self.friction_index = ExecutionFrictionIndex(self.config.get('friction', {}))
        self.analytics = PostTradeAnalytics(self.config.get('analytics', {}))
    
    def process(self, market_data: pd.DataFrame, 
               previous_tier_output: Optional[RiskParameters] = None,
               additional_inputs: Optional[Dict[str, Any]] = None) -> ExecutionIntelligence:
        """
        Process market data and optimize execution
        
        Args:
            market_data: DataFrame with OHLCV data
            previous_tier_output: Output from Tier 7 (RiskParameters)
            additional_inputs: Dictionary with venue metrics and execution data
            
        Returns:
            ExecutionIntelligence with execution optimization
        """
        if not self.validate_input(market_data):
            logger.error("Invalid input data for Tier 8")
            return None
        try:
        
            # Get additional data
            venue_metrics = additional_inputs.get('venue_metrics', [])
            execution_data = additional_inputs.get('execution_data', {})
            
            # Get position size and urgency from previous tier
            position_size = previous_tier_output.position_size if previous_tier_output else 0.0
            urgency = 0.8 if previous_tier_output and previous_tier_output.confidence > 0.8 else 0.5
            
            # Select optimal venue
            venue_selection = self.router.select_venue(
                venue_metrics, position_size, urgency
            )
            
            # Monitor slippage
            slippage = self.slippage_monitor.analyze_slippage(execution_data)
            
            # Calculate friction index
            friction = self.friction_index.calculate_efi(market_data, execution_data)
            
            # Analyze execution quality
            analytics = self.analytics.analyze_execution(execution_data, market_data)
            
            # Calculate optimal venue based on metrics
            optimal_venue = venue_selection['primary_venue']
            
            # Select execution algorithm based on market conditions
            if friction['market_impact'] > 0.001 or position_size > 0.1:
                execution_algo = 'VWAP'
            elif urgency > 0.8:
                execution_algo = 'IS'  # Implementation Shortfall
            else:
                execution_algo = 'TWAP'
            
            # Calculate expected slippage
            expected_slippage = venue_selection['expected_slippage']
            
            # Calculate execution cost
            execution_cost = (
                0.4 * friction['efi'] +
                0.3 * slippage['slippage'] +
                0.3 * analytics['implementation_shortfall']
            )
            
            # Calculate fill probability
            fill_prob = venue_selection['expected_fill_rate'] * (1 - friction['participation_rate'])
            
            # Calculate performance metrics
            performance = {
                'fill_rate': analytics['fill_rate'],
                'price_improvement': analytics['price_improvement'],
                'execution_speed': analytics['execution_speed'],
                'spread_capture': analytics['spread_capture']
            }
            
            # Calculate signal value (-1 to 1)
            # Based on execution quality
            signal_value = (
                0.4 * (1 - min(execution_cost * 100, 1)) +
                0.3 * (fill_prob - 0.5) * 2 +
                0.3 * (analytics['price_improvement'] * 10)
            )
            
            # Calculate confidence (0 to 1)
            confidence_factors = [
                fill_prob,
                1 - min(execution_cost * 10, 1),
                analytics['fill_rate']
            ]
            confidence = np.mean(confidence_factors)
            
            # Create metadata
            metadata = {
                'venue_selection': venue_selection,
                'slippage': slippage,
                'friction': friction,
                'analytics': analytics
            }
            
            # Create execution intelligence
            execution = ExecutionIntelligence(
                timestamp=market_data.index[-1],
                signal_value=signal_value,
                confidence=confidence,
                optimal_venue=optimal_venue,
                execution_algorithm=execution_algo,
                expected_slippage=expected_slippage,
                execution_cost=execution_cost,
                fill_probability=fill_prob,
                performance_metrics=performance,
                metadata=metadata
            )
            
            self.last_output = execution
            return execution
            
        except Exception as e:
            logger.error(f"Error processing Tier 8: {str(e)}")
            return None


# Example usage
if __name__ == "__main__":
    # Configure logging
    logging.basicConfig(level=logging.INFO, 
                      format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    
    # Create sample data
    dates = pd.date_range('2024-01-01', periods=250, freq='1H')
    np.random.seed(42)
    
    df = pd.DataFrame({
        'open': np.random.randn(250).cumsum() + 100,
        'high': np.random.randn(250).cumsum() + 102,
        'low': np.random.randn(250).cumsum() + 98,
        'close': np.random.randn(250).cumsum() + 100,
        'volume': np.random.randint(1000, 10000, 250)
    }, index=dates)
    
    # Create sample venue metrics
    venue_metrics = [
        VenueMetrics('Venue1', 0.95, 0.0002, 50, 0.3, 0.98),
        VenueMetrics('Venue2', 0.90, 0.0003, 30, 0.4, 0.95),
        VenueMetrics('Venue3', 0.85, 0.0004, 20, 0.5, 0.92)
    ]
    
    # Create sample execution data
    execution_data = {
        'venue': 'Venue1',
        'start_time': datetime.now() - timedelta(minutes=5),
        'end_time': datetime.now(),
        'order_size': 1000,
        'filled_size': 950,
        'limit_price': 100.5,
        'average_price': 100.48,
        'arrival_price': 100.45,
        'side': 'buy'
    }
    
    # Create sample additional inputs
    additional_inputs = {
        'venue_metrics': venue_metrics,
        'execution_data': execution_data
    }
    
    # Initialize and process
    tier8 = Tier8ExecutionIntelligence()
    tier8.initialize()
    result = tier8.process(df, additional_inputs=additional_inputs)
    
    # Print results
    logger.info("\n=== Tier 8: Execution Intelligence Results ===")
    logger.info(f"Signal: {result.signal_value:.4f}")
    logger.info(f"Confidence: {result.confidence:.2%}")
    logger.info(f"Optimal Venue: {result.optimal_venue}")
    logger.info(f"Execution Algorithm: {result.execution_algorithm}")
    logger.info(f"Expected Slippage: {result.expected_slippage:.4%}")
    logger.info(f"Execution Cost: {result.execution_cost:.4%}")
    logger.info(f"Fill Probability: {result.fill_probability:.2%}")
    logger.info("\nPerformance Metrics:")
    for metric, value in result.performance_metrics.items():
        logger.info(f"- {metric}: {value:.4f}")
