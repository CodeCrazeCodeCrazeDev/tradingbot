"""
Master Trading Orchestrator
Coordinates all trading systems to maximize profitability
"""

import asyncio
import numpy as np
import pandas as pd
from typing import Any, Dict, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
import logging
from datetime import datetime, timedelta
from collections import deque
import json
import threading
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor
import numpy
import pandas

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

class TradingMode(Enum):
    """Trading modes for different market conditions"""
    AGGRESSIVE = "aggressive"
    BALANCED = "balanced"
    CONSERVATIVE = "conservative"
    DEFENSIVE = "defensive"
    SCALPING = "scalping"
    SWING = "swing"
    POSITION = "position"

@dataclass
class TradingDecision:
    """Represents a trading decision"""
    decision_id: str
    timestamp: datetime
    opportunity_ids: List[str]
    action: str  # BUY/SELL/HOLD
    symbols: List[str]
    allocation: Dict[str, float]
    risk_score: float
    expected_return: float
    confidence: float
    execution_plan: Dict[str, Any]
    metadata: Dict[str, Any]

class MasterOrchestrator:
    """
    Master orchestrator that coordinates all trading systems
    Ensures optimal decision making and execution
    """
    
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        self.trading_mode = TradingMode.BALANCED
        
        # Portfolio management
        self.total_capital = self.config.get('capital', 100000)
        self.max_risk_per_trade = self.config.get('max_risk_per_trade', 0.02)
        self.max_portfolio_risk = self.config.get('max_portfolio_risk', 0.06)
        self.max_correlation = self.config.get('max_correlation', 0.7)
        
        # Active positions
        self.active_positions = {}
        self.pending_orders = {}
        self.position_limits = {}
        
        # Performance tracking
        self.performance_history = deque(maxlen=1000)
        self.win_rate = 0
        self.sharpe_ratio = 0
        self.max_drawdown = 0
        
        # System components (will be initialized with actual systems)
        self.opportunity_scanner = None
        self.risk_manager = None
        self.execution_engine = None
        self.ml_predictor = None
        
        # Threading for parallel processing
        self.executor = ThreadPoolExecutor(max_workers=10)
        
        # Decision queue
        self.decision_queue = asyncio.Queue()
        self.execution_queue = asyncio.Queue()
        
        logger.info("Master Orchestrator initialized")
    
    async def orchestrate_trading(self, market_data: Dict) -> List[TradingDecision]:
        """
        Main orchestration logic that coordinates all systems
        """
        logger.info("Starting trading orchestration...")
        
        # Step 1: Gather all opportunities from all scanners
        all_opportunities = await self._gather_opportunities(market_data)
        
        # Step 2: Filter based on current mode and risk
        filtered_opportunities = self._filter_by_mode_and_risk(all_opportunities)
        
        # Step 3: Predict success rates using ML
        scored_opportunities = await self._score_opportunities(filtered_opportunities)
        
        # Step 4: Check correlations and dependencies
        uncorrelated_opportunities = self._remove_correlated_trades(scored_opportunities)
        
        # Step 5: Optimize portfolio allocation
        optimal_allocation = self._optimize_allocation(uncorrelated_opportunities)
        
        # Step 6: Generate trading decisions
        decisions = self._generate_decisions(optimal_allocation, market_data)
        
        # Step 7: Validate decisions against risk limits
        validated_decisions = await self._validate_decisions(decisions)
        
        # Step 8: Queue for execution
        await self._queue_for_execution(validated_decisions)
        
        logger.info(f"Generated {len(validated_decisions)} trading decisions")
        
        return validated_decisions
    
    async def _gather_opportunities(self, market_data: Dict) -> List[Dict]:
        """
        Gather opportunities from all scanning systems
        """
        if not self.opportunity_scanner:
            return []
        
        # Run all scanners in parallel
        opportunities = await self.opportunity_scanner.scan_all_opportunities(market_data)
        
        # Add timestamp and unique IDs
        for opp in opportunities:
            opp['gathered_at'] = datetime.now()
            opp['unique_id'] = f"{opp['type']}_{opp.get('symbol', 'multi')}_{datetime.now().timestamp()}"
        
        return opportunities
    
    def _filter_by_mode_and_risk(self, opportunities: List[Dict]) -> List[Dict]:
        """
        Filter opportunities based on current trading mode and risk appetite
        """
        filtered = []
        
        for opp in opportunities:
            # Check if opportunity matches current mode
            if not self._matches_trading_mode(opp):
                continue
            
            # Check risk level
            risk = opp.get('risk', opp.get('risk_score', 0.5))
            
            if self.trading_mode == TradingMode.AGGRESSIVE:
                max_risk = 0.8
            elif self.trading_mode == TradingMode.CONSERVATIVE:
                max_risk = 0.3
            else:
                max_risk = 0.5
            
            if risk <= max_risk:
                filtered.append(opp)
        
        return filtered
    
    def _matches_trading_mode(self, opportunity: Dict) -> bool:
        """
        Check if opportunity matches current trading mode
        """
        opp_type = opportunity['type']
        
        mode_preferences = {
            TradingMode.SCALPING: ['ARBITRAGE', 'MARKET_MAKING', 'MICROSTRUCTURE'],
            TradingMode.SWING: ['MOMENTUM', 'BREAKOUT', 'TREND_ACCELERATION'],
            TradingMode.POSITION: ['NEWS', 'EVENT', 'CORRELATION'],
            TradingMode.AGGRESSIVE: ['MOMENTUM', 'BREAKOUT', 'VOLATILITY'],
            TradingMode.CONSERVATIVE: ['ARBITRAGE', 'MARKET_MAKING', 'PAIRS_TRADE'],
            TradingMode.BALANCED: 'ALL'
        }
        
        preferred_types = mode_preferences.get(self.trading_mode, 'ALL')
        
        if preferred_types == 'ALL':
            return True
        
        return opp_type in preferred_types
    
    async def _score_opportunities(self, opportunities: List[Dict]) -> List[Dict]:
        """
        Use ML to predict success probability for each opportunity
        """
        if not self.ml_predictor:
            # Use simple scoring if ML not available
            for opp in opportunities:
                opp['ml_score'] = opp.get('confidence', 0.5)
            return opportunities
        
        # Prepare features for ML model
        features = self._extract_ml_features(opportunities)
        
        # Get predictions
        predictions = await self.ml_predictor.predict_batch(features)
        
        # Add scores to opportunities
        for opp, pred in zip(opportunities, predictions):
            # Handle both dict and dataclass PredictionResult
            if hasattr(pred, 'success_probability'):
                opp['ml_score'] = pred.success_probability
                opp['expected_return_ml'] = pred.expected_return
                opp['risk_adjusted_score'] = pred.sharpe_ratio
            else:
                opp['ml_score'] = pred.get('success_probability', 0.5)
                opp['expected_return_ml'] = pred.get('expected_return', 0)
                opp['risk_adjusted_score'] = pred.get('sharpe_ratio', 0)
        
        return opportunities
    
    def _extract_ml_features(self, opportunities: List[Dict]) -> List[Dict]:
        """
        Extract features for ML prediction
        """
        features = []
        
        for opp in opportunities:
            feature_dict = {
                'type': opp['type'],
                'confidence': opp.get('confidence', 0.5),
                'volatility': opp.get('volatility', 0.2),
                'volume': opp.get('volume', 100000),
                'spread': opp.get('spread', 0.001),
                'momentum': opp.get('momentum', 0),
                'time_of_day': datetime.now().hour,
                'day_of_week': datetime.now().weekday()
            }
            features.append(feature_dict)
        
        return features
    
    def _remove_correlated_trades(self, opportunities: List[Dict]) -> List[Dict]:
        """
        Remove highly correlated opportunities to avoid concentration risk
        """
        if len(opportunities) <= 1:
            return opportunities
        
        # Group by symbol
        by_symbol = {}
        for opp in opportunities:
            symbol = opp.get('symbol', 'unknown')
            if symbol not in by_symbol:
                by_symbol[symbol] = []
            by_symbol[symbol].append(opp)
        
        # Keep only best opportunity per symbol
        uncorrelated = []
        for symbol, opps in by_symbol.items():
            # Sort by score and keep best
            best = max(opps, key=lambda x: x.get('ml_score', 0))
            uncorrelated.append(best)
        
        # Additional correlation check for different symbols
        final_opportunities = []
        correlation_groups = []
        
        for opp in uncorrelated:
            # Check if correlated with existing groups
            is_correlated = False
            
            for group in correlation_groups:
                if self._are_correlated(opp, group):
                    is_correlated = True
                    # Add to group if score is better
                    if opp.get('ml_score', 0) > group[0].get('ml_score', 0):
                        group[0] = opp
                    break
            
            if not is_correlated:
                correlation_groups.append([opp])
                final_opportunities.append(opp)
        
        return final_opportunities
    
    def _are_correlated(self, opp1: Dict, group: List[Dict]) -> bool:
        """
        Check if opportunity is correlated with a group
        """
        # Simplified correlation check
        # In production, use actual correlation matrix
        
        opp1_type = opp1['type']
        
        for opp2 in group:
            # Same type opportunities are often correlated
            if opp1_type == opp2['type']:
                return True
            
            # Check for known correlations
            correlated_types = {
                'MOMENTUM': ['BREAKOUT', 'TREND_ACCELERATION'],
                'ARBITRAGE': ['MARKET_MAKING'],
                'NEWS': ['SENTIMENT_SURGE', 'EVENT']
            }
            
            if opp1_type in correlated_types:
                if opp2['type'] in correlated_types[opp1_type]:
                    return True
        
        return False
    
    def _optimize_allocation(self, opportunities: List[Dict]) -> Dict[str, float]:
        """
        Optimize capital allocation across opportunities
        Modern Portfolio Theory + Kelly Criterion
        """
        if not opportunities:
            return {}
        
        n = len(opportunities)
        allocations = {}
        
        # Calculate expected returns and risks
        returns = []
        risks = []
        scores = []
        
        for opp in opportunities:
            expected_return = opp.get('expected_return_ml', opp.get('expected_return', 0.01))
            risk = opp.get('risk', 0.5)
            score = opp.get('ml_score', 0.5)
            
            returns.append(expected_return)
            risks.append(risk)
            scores.append(score)
        
        # Simple allocation based on scores (Kelly-inspired)
        total_score = sum(scores)
        
        available_capital = self._get_available_capital()
        
        for i, opp in enumerate(opportunities):
            # Base allocation proportional to score
            base_allocation = (scores[i] / total_score) if total_score > 0 else 1/n
            
            # Apply Kelly criterion adjustment
            kelly_fraction = self._calculate_kelly_fraction(
                returns[i], risks[i], scores[i]
            )
            
            # Final allocation
            allocation = base_allocation * kelly_fraction * available_capital
            
            # Apply position limits
            max_position = self._get_max_position_size(opp)
            allocation = min(allocation, max_position)
            
            opp_id = opp['unique_id']
            allocations[opp_id] = allocation
        
        return allocations
    
    def _calculate_kelly_fraction(self, expected_return: float, risk: float, 
                                 win_probability: float) -> float:
        """
        Calculate Kelly fraction for position sizing
        """
        if risk == 0:
            return 0
        
        # Kelly formula: f = (p*b - q) / b
        # where p = win probability, q = lose probability, b = win/loss ratio
        
        q = 1 - win_probability
        b = expected_return / risk  # Simplified win/loss ratio
        
        if b == 0:
            return 0
        
        kelly = (win_probability * b - q) / b
        
        # Apply Kelly fraction cap (never bet more than 25% on single trade)
        kelly = max(0, min(0.25, kelly))
        
        return kelly
    
    def _get_available_capital(self) -> float:
        """
        Calculate available capital for new positions
        """
        # Total capital minus current positions
        used_capital = sum(pos.get('value', 0) for pos in self.active_positions.values())
        
        # Reserve for risk management
        risk_reserve = self.total_capital * 0.1
        
        available = self.total_capital - used_capital - risk_reserve
        
        return max(0, available)
    
    def _get_max_position_size(self, opportunity: Dict) -> float:
        """
        Get maximum position size for an opportunity
        """
        # Risk-based position sizing
        max_risk = self.total_capital * self.max_risk_per_trade
        
        # Adjust for opportunity type
        type_multipliers = {
            'ARBITRAGE': 2.0,  # Lower risk, can be larger
            'MOMENTUM': 0.5,   # Higher risk, smaller size
            'NEWS': 0.7,
            'CORRELATION': 1.0
        }
        
        multiplier = type_multipliers.get(opportunity['type'], 1.0)
        
        return max_risk * multiplier
    
    def _generate_decisions(self, allocations: Dict[str, float], 
                          market_data: Dict) -> List[TradingDecision]:
        """
        Generate executable trading decisions
        """
        decisions = []
        
        for opp_id, allocation in allocations.items():
            if allocation <= 0:
                continue
            
            # Find opportunity details
            opportunity = self._find_opportunity_by_id(opp_id)
            
            if not opportunity:
                continue
            
            # Create execution plan
            execution_plan = self._create_execution_plan(opportunity, allocation, market_data)
            
            # Generate decision
            decision = TradingDecision(
                decision_id=f"DEC_{datetime.now().timestamp()}",
                timestamp=datetime.now(),
                opportunity_ids=[opp_id],
                action=self._determine_action(opportunity),
                symbols=self._extract_symbols(opportunity),
                allocation={opp_id: allocation},
                risk_score=opportunity.get('risk', 0.5),
                expected_return=opportunity.get('expected_return_ml', 0.01),
                confidence=opportunity.get('ml_score', 0.5),
                execution_plan=execution_plan,
                metadata={
                    'opportunity_type': opportunity['type'],
                    'trading_mode': self.trading_mode.value
                }
            )
            
            decisions.append(decision)
        
        return decisions
    
    def _find_opportunity_by_id(self, opp_id: str) -> Optional[Dict]:
        """
        Find opportunity by ID from last scored/filter opportunity list.
        """
        if hasattr(self, '_last_opportunities') and self._last_opportunities:
            for opp in self._last_opportunities:
                if opp.get('unique_id') == opp_id:
                    return opp
        logger.error(f"Opportunity with ID {opp_id} not found in cache")
        return None
    
    def _determine_action(self, opportunity: Dict) -> str:
        """
        Determine trading action based on opportunity
        """
        direction = opportunity.get('direction', 'BUY')
        
        if direction in ['BUY', 'LONG']:
            return 'BUY'
        elif direction in ['SELL', 'SHORT']:
            return 'SELL'
        else:
            return 'HOLD'
    
    def _extract_symbols(self, opportunity: Dict) -> List[str]:
        """
        Extract trading symbols from opportunity
        """
        if 'symbol' in opportunity:
            return [opportunity['symbol']]
        elif 'symbols' in opportunity:
            return opportunity['symbols']
        elif 'pair' in opportunity:
            return list(opportunity['pair'])
        else:
            return []
    
    def _create_execution_plan(self, opportunity: Dict, allocation: float, 
                              market_data: Dict) -> Dict[str, Any]:
        """
        Create detailed execution plan
        """
        plan = {
            'allocation': allocation,
            'entry_method': self._determine_entry_method(opportunity),
            'entry_price': opportunity.get('entry_price'),
            'stop_loss': opportunity.get('stop_loss'),
            'take_profit': opportunity.get('targets', []),
            'time_limit': opportunity.get('time_horizon', 24),
            'execution_algo': self._select_execution_algo(opportunity, market_data),
            'slippage_limit': 0.002,
            'urgency': self._calculate_urgency(opportunity)
        }
        
        return plan
    
    def _determine_entry_method(self, opportunity: Dict) -> str:
        """
        Determine best entry method
        """
        opp_type = opportunity['type']
        
        if opp_type in ['ARBITRAGE', 'LATENCY']:
            return 'IMMEDIATE'
        elif opp_type in ['MOMENTUM', 'BREAKOUT']:
            return 'MARKET'
        elif opp_type in ['MARKET_MAKING']:
            return 'LIMIT'
        else:
            return 'ADAPTIVE'
    
    def _select_execution_algo(self, opportunity: Dict, market_data: Dict) -> str:
        """
        Select optimal execution algorithm
        """
        # Based on opportunity type and market conditions
        if opportunity['type'] == 'ARBITRAGE':
            return 'SMART_ROUTE'
        elif opportunity.get('size', 0) > 10000:
            return 'ICEBERG'
        elif market_data.get('volatility', 0) > 0.3:
            return 'ADAPTIVE'
        else:
            return 'TWAP'
    
    def _calculate_urgency(self, opportunity: Dict) -> float:
        """
        Calculate execution urgency (0-1)
        """
        opp_type = opportunity['type']
        
        urgency_map = {
            'ARBITRAGE': 1.0,
            'LATENCY': 1.0,
            'MOMENTUM': 0.8,
            'NEWS': 0.7,
            'BREAKOUT': 0.7,
            'MARKET_MAKING': 0.3,
            'CORRELATION': 0.4
        }
        
        return urgency_map.get(opp_type, 0.5)
    
    async def _validate_decisions(self, decisions: List[TradingDecision]) -> List[TradingDecision]:
        """
        Validate decisions against risk limits and constraints
        """
        validated = []
        
        for decision in decisions:
            # Check portfolio risk
            if not self._check_portfolio_risk(decision):
                logger.warning(f"Decision {decision.decision_id} exceeds portfolio risk")
                continue
            
            # Check position limits
            if not self._check_position_limits(decision):
                logger.warning(f"Decision {decision.decision_id} exceeds position limits")
                continue
            
            # Check correlation limits
            if not self._check_correlation_limits(decision):
                logger.warning(f"Decision {decision.decision_id} exceeds correlation limits")
                continue
            
            validated.append(decision)
        
        return validated
    
    def _check_portfolio_risk(self, decision: TradingDecision) -> bool:
        """
        Check if decision fits within portfolio risk limits
        """
        # Calculate current portfolio risk
        current_risk = self._calculate_portfolio_risk()
        
        # Estimate additional risk from this decision
        decision_risk = decision.risk_score * sum(decision.allocation.values()) / self.total_capital
        
        # Check if within limits
        total_risk = current_risk + decision_risk
        
        return total_risk <= self.max_portfolio_risk
    
    def _calculate_portfolio_risk(self) -> float:
        """
        Calculate current portfolio risk (simplified VaR)
        """
        if not self.active_positions:
            return 0
        
        total_exposure = sum(pos.get('value', 0) for pos in self.active_positions.values())
        
        if self.total_capital == 0:
            return 0
        
        # Simplified risk calculation
        return total_exposure / self.total_capital * 0.1  # Assume 10% volatility
    
    def _check_position_limits(self, decision: TradingDecision) -> bool:
        """
        Check position limits per symbol
        """
        for symbol in decision.symbols:
            current_exposure = self._get_symbol_exposure(symbol)
            additional_exposure = sum(decision.allocation.values())
            
            max_exposure = self.total_capital * 0.2  # Max 20% per symbol
            
            if current_exposure + additional_exposure > max_exposure:
                return False
        
        return True
    
    def _get_symbol_exposure(self, symbol: str) -> float:
        """
        Get current exposure to a symbol
        """
        exposure = 0
        
        for pos_id, position in self.active_positions.items():
            if symbol in position.get('symbols', []):
                exposure += position.get('value', 0)
        
        return exposure
    
    def _check_correlation_limits(self, decision: TradingDecision) -> bool:
        """
        Check correlation with existing positions
        """
        # Simplified check - in production use correlation matrix
        return True
    
    async def _queue_for_execution(self, decisions: List[TradingDecision]):
        """
        Queue validated decisions for execution
        """
        for decision in decisions:
            await self.execution_queue.put(decision)
            logger.info(f"Queued decision {decision.decision_id} for execution")
    
    async def execute_decisions(self):
        """
        Execute queued trading decisions
        """
        while True:
            try:
                decision = await self.execution_queue.get()
                
                if self.execution_engine:
                    # Execute through execution engine
                    result = await self.execution_engine.execute(decision)
                    
                    # Track execution
                    self._track_execution(decision, result)
                else:
                    logger.warning("No execution engine available")
                
            except Exception as e:
                logger.error(f"Error executing decision: {e}")
    
    def _track_execution(self, decision: TradingDecision, result: Dict):
        """
        Track execution results
        """
        self.performance_history.append({
            'decision_id': decision.decision_id,
            'timestamp': datetime.now(),
            'result': result,
            'profit': result.get('profit', 0),
            'success': result.get('success', False)
        })
        
        # Update metrics
        self._update_performance_metrics()
    
    def _update_performance_metrics(self):
        """
        Update performance metrics
        """
        if not self.performance_history:
            return
        
        # Calculate win rate
        wins = sum(1 for p in self.performance_history if p['success'])
        self.win_rate = wins / len(self.performance_history)
        
        # Calculate Sharpe ratio (simplified)
        returns = [p['profit'] for p in self.performance_history]
        if returns:
            avg_return = np.mean(returns)
            std_return = np.std(returns)
            self.sharpe_ratio = avg_return / std_return if std_return > 0 else 0
        
        # Calculate max drawdown
        cumulative = np.cumsum([p['profit'] for p in self.performance_history])
        if len(cumulative) > 0:
            peak = np.maximum.accumulate(cumulative)
            drawdown = (cumulative - peak) / peak
            self.max_drawdown = np.min(drawdown)
    
    def get_performance_summary(self) -> Dict:
        """
        Get performance summary
        """
        return {
            'win_rate': self.win_rate,
            'sharpe_ratio': self.sharpe_ratio,
            'max_drawdown': self.max_drawdown,
            'active_positions': len(self.active_positions),
            'total_capital': self.total_capital,
            'available_capital': self._get_available_capital(),
            'current_mode': self.trading_mode.value
        }
    
    def adjust_trading_mode(self, market_conditions: Dict):
        """
        Dynamically adjust trading mode based on market conditions
        """
        volatility = market_conditions.get('volatility', 0.2)
        trend_strength = market_conditions.get('trend_strength', 0.5)
        volume = market_conditions.get('volume', 'normal')
        
        # Rule-based mode selection
        if volatility > 0.4:
            self.trading_mode = TradingMode.DEFENSIVE
        elif volatility < 0.1:
            self.trading_mode = TradingMode.AGGRESSIVE
        elif trend_strength > 0.7:
            self.trading_mode = TradingMode.SWING
        elif volume == 'high' and volatility < 0.2:
            self.trading_mode = TradingMode.SCALPING
        else:
            self.trading_mode = TradingMode.BALANCED
        
        logger.info(f"Adjusted trading mode to: {self.trading_mode.value}")
