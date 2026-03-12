"""
Recursive Execution Optimization

Execution strategies that recursively optimize themselves to minimize slippage,
improve fill rates, and adapt to changing market microstructure.
"""

import asyncio
import logging
from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Any, Optional
import numpy as np

logger = logging.getLogger(__name__)


@dataclass
class ExecutionPatternLearning:
    """Learns patterns from execution history"""
    pattern_id: str
    pattern_type: str
    conditions: Dict[str, Any]
    avg_slippage: float
    fill_rate: float
    sample_count: int
    last_updated: datetime
    
    def update(self, slippage: float, filled: bool):
        """Update pattern with new execution"""
        self.avg_slippage = (self.avg_slippage * self.sample_count + slippage) / (self.sample_count + 1)
        self.fill_rate = (self.fill_rate * self.sample_count + (1.0 if filled else 0.0)) / (self.sample_count + 1)
        self.sample_count += 1
        self.last_updated = datetime.utcnow()


@dataclass
class SlippageMinimization:
    """Tracks slippage minimization strategies"""
    strategy_name: str
    avg_slippage: float
    min_slippage: float
    max_slippage: float
    execution_count: int
    improvement_rate: float
    
    def record_execution(self, slippage: float):
        """Record new execution"""
        old_avg = self.avg_slippage
        self.avg_slippage = (self.avg_slippage * self.execution_count + slippage) / (self.execution_count + 1)
        self.min_slippage = min(self.min_slippage, slippage)
        self.max_slippage = max(self.max_slippage, slippage)
        self.execution_count += 1
        
        if old_avg > 0:
            self.improvement_rate = (old_avg - self.avg_slippage) / old_avg


class RecursiveExecutionOptimization:
    """
    Recursive execution optimization engine.
    
    Learns from every execution to improve:
    1. Order timing
    2. Order sizing
    3. Venue selection
    4. Execution algorithm choice
    5. The optimization process itself (meta-recursion)
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        
        # Execution strategies
        self.strategies = {
            'market': {'slippage_target': 0.001, 'speed': 'instant'},
            'limit': {'slippage_target': 0.0, 'speed': 'patient'},
            'twap': {'slippage_target': 0.0005, 'speed': 'medium'},
            'vwap': {'slippage_target': 0.0003, 'speed': 'medium'},
            'iceberg': {'slippage_target': 0.0002, 'speed': 'slow'},
            'adaptive': {'slippage_target': 0.0001, 'speed': 'dynamic'},
        }
        
        # Learning components
        self.execution_patterns: Dict[str, ExecutionPatternLearning] = {}
        self.slippage_trackers: Dict[str, SlippageMinimization] = {}
        self.execution_history: List[Dict[str, Any]] = []
        
        # Meta-learning
        self.optimization_cycles: List[Dict[str, Any]] = []
        self.meta_insights: List[Dict[str, Any]] = []
        
        self._initialize_slippage_trackers()
        logger.info("RecursiveExecutionOptimization initialized")
    
    def _initialize_slippage_trackers(self):
        """Initialize slippage trackers for each strategy"""
        for strategy_name in self.strategies.keys():
            self.slippage_trackers[strategy_name] = SlippageMinimization(
                strategy_name=strategy_name,
                avg_slippage=0.001,
                min_slippage=float('inf'),
                max_slippage=0.0,
                execution_count=0,
                improvement_rate=0.0
            )
    
    async def optimize_execution(
        self,
        order: Dict[str, Any],
        market_conditions: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Recursively optimize execution for an order.
        
        Args:
            order: Order details (symbol, size, direction, urgency)
            market_conditions: Current market state
            
        Returns:
            Optimized execution plan
        """
        # Learn from similar past executions
        similar_patterns = self._find_similar_patterns(order, market_conditions)
        
        # Select best execution strategy
        strategy = await self._select_execution_strategy(
            order,
            market_conditions,
            similar_patterns
        )
        
        # Optimize strategy parameters
        optimized_params = await self._optimize_strategy_parameters(
            strategy,
            order,
            market_conditions
        )
        
        # Create execution plan
        execution_plan = {
            'strategy': strategy,
            'parameters': optimized_params,
            'expected_slippage': self._estimate_slippage(strategy, order, market_conditions),
            'expected_fill_rate': self._estimate_fill_rate(strategy, order, market_conditions),
            'timestamp': datetime.utcnow().isoformat()
        }
        
        return execution_plan
    
    def _find_similar_patterns(
        self,
        order: Dict[str, Any],
        market_conditions: Dict[str, Any]
    ) -> List[ExecutionPatternLearning]:
        """Find similar execution patterns from history"""
        similar = []
        
        for pattern in self.execution_patterns.values():
            similarity = self._calculate_similarity(
                order,
                market_conditions,
                pattern.conditions
            )
            
            if similarity > 0.7:
                similar.append(pattern)
        
        # Sort by performance
        similar.sort(key=lambda p: (p.fill_rate, -p.avg_slippage), reverse=True)
        
        return similar[:5]
    
    def _calculate_similarity(
        self,
        order: Dict[str, Any],
        market_conditions: Dict[str, Any],
        pattern_conditions: Dict[str, Any]
    ) -> float:
        """Calculate similarity between current conditions and pattern"""
        # Simple similarity based on key factors
        similarity_score = 0.0
        factors = 0
        
        # Compare order size
        if 'size' in order and 'size' in pattern_conditions:
            size_ratio = min(order['size'], pattern_conditions['size']) / max(order['size'], pattern_conditions['size'])
            similarity_score += size_ratio
            factors += 1
        
        # Compare volatility
        if 'volatility' in market_conditions and 'volatility' in pattern_conditions:
            vol_diff = abs(market_conditions['volatility'] - pattern_conditions['volatility'])
            similarity_score += max(0, 1 - vol_diff * 10)
            factors += 1
        
        # Compare liquidity
        if 'liquidity' in market_conditions and 'liquidity' in pattern_conditions:
            liq_ratio = min(market_conditions['liquidity'], pattern_conditions['liquidity']) / max(market_conditions['liquidity'], pattern_conditions['liquidity'])
            similarity_score += liq_ratio
            factors += 1
        
        return similarity_score / max(factors, 1)
    
    async def _select_execution_strategy(
        self,
        order: Dict[str, Any],
        market_conditions: Dict[str, Any],
        similar_patterns: List[ExecutionPatternLearning]
    ) -> str:
        """Select best execution strategy based on learned patterns"""
        # If we have similar patterns, use the best performing strategy
        if similar_patterns:
            best_pattern = similar_patterns[0]
            return best_pattern.pattern_type
        
        # Otherwise, select based on market conditions
        volatility = market_conditions.get('volatility', 0.02)
        liquidity = market_conditions.get('liquidity', 1.0)
        urgency = order.get('urgency', 'medium')
        
        if urgency == 'high':
            return 'market'
        elif volatility > 0.03:
            return 'iceberg'  # Hide in high volatility
        elif liquidity < 0.5:
            return 'twap'  # Spread out in low liquidity
        else:
            return 'adaptive'  # Default to adaptive
    
    async def _optimize_strategy_parameters(
        self,
        strategy: str,
        order: Dict[str, Any],
        market_conditions: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Optimize parameters for selected strategy"""
        base_params = self.strategies.get(strategy, {}).copy()
        
        # Recursively optimize based on market conditions
        if strategy == 'twap':
            # Optimize time slicing
            volatility = market_conditions.get('volatility', 0.02)
            base_params['num_slices'] = int(10 * (1 + volatility * 10))
            base_params['slice_interval'] = 60 / base_params['num_slices']
        
        elif strategy == 'vwap':
            # Optimize volume participation
            volume = market_conditions.get('volume', 1000000)
            order_size = order.get('size', 100)
            base_params['participation_rate'] = min(0.1, order_size / volume * 10)
        
        elif strategy == 'iceberg':
            # Optimize visible quantity
            order_size = order.get('size', 100)
            base_params['visible_qty'] = order_size * 0.1  # Show 10%
            base_params['refresh_threshold'] = 0.5
        
        elif strategy == 'adaptive':
            # Recursively adapt to all conditions
            base_params = await self._recursive_adapt(order, market_conditions)
        
        return base_params
    
    async def _recursive_adapt(
        self,
        order: Dict[str, Any],
        market_conditions: Dict[str, Any],
        depth: int = 0
    ) -> Dict[str, Any]:
        """
        Recursively adapt execution parameters.
        
        This is the core recursive optimization - parameters adapt based on
        market conditions, which themselves are analyzed recursively.
        """
        if depth > 3:
            return {'adapted': True, 'depth': depth}
        
        params = {}
        
        # Level 0: Basic adaptation
        volatility = market_conditions.get('volatility', 0.02)
        params['aggressiveness'] = 1.0 - volatility * 10
        
        # Level 1: Adapt to liquidity
        liquidity = market_conditions.get('liquidity', 1.0)
        if liquidity < 0.5:
            # Recurse to find optimal slicing
            sub_params = await self._recursive_adapt(
                order,
                {'volatility': volatility, 'liquidity': liquidity * 1.5},
                depth + 1
            )
            params['sub_strategy'] = sub_params
        
        # Level 2: Adapt to spread
        spread = market_conditions.get('spread', 0.001)
        params['limit_offset'] = spread * 0.5
        
        return params
    
    def _estimate_slippage(
        self,
        strategy: str,
        order: Dict[str, Any],
        market_conditions: Dict[str, Any]
    ) -> float:
        """Estimate expected slippage"""
        tracker = self.slippage_trackers.get(strategy)
        if tracker and tracker.execution_count > 0:
            base_slippage = tracker.avg_slippage
        else:
            base_slippage = self.strategies[strategy]['slippage_target']
        
        # Adjust for market conditions
        volatility = market_conditions.get('volatility', 0.02)
        liquidity = market_conditions.get('liquidity', 1.0)
        
        adjusted_slippage = base_slippage * (1 + volatility * 5) / liquidity
        
        return adjusted_slippage
    
    def _estimate_fill_rate(
        self,
        strategy: str,
        order: Dict[str, Any],
        market_conditions: Dict[str, Any]
    ) -> float:
        """Estimate expected fill rate"""
        # Market orders have high fill rate
        if strategy == 'market':
            return 0.99
        
        # Limit orders depend on market conditions
        liquidity = market_conditions.get('liquidity', 1.0)
        volatility = market_conditions.get('volatility', 0.02)
        
        base_fill_rate = 0.8
        fill_rate = base_fill_rate * liquidity * (1 - volatility * 2)
        
        return max(0.5, min(0.99, fill_rate))
    
    async def record_execution(
        self,
        execution: Dict[str, Any]
    ):
        """
        Record execution results and learn from them.
        
        This is where the recursive learning happens - we analyze the execution
        and use it to improve future executions.
        """
        strategy = execution.get('strategy')
        actual_slippage = execution.get('actual_slippage', 0.0)
        filled = execution.get('filled', False)
        
        # Update slippage tracker
        if strategy in self.slippage_trackers:
            self.slippage_trackers[strategy].record_execution(actual_slippage)
        
        # Create or update execution pattern
        pattern_id = self._create_pattern_id(execution)
        if pattern_id in self.execution_patterns:
            pattern = self.execution_patterns[pattern_id]
            pattern.update(actual_slippage, filled)
        else:
            pattern = ExecutionPatternLearning(
                pattern_id=pattern_id,
                pattern_type=strategy,
                conditions=execution.get('market_conditions', {}),
                avg_slippage=actual_slippage,
                fill_rate=1.0 if filled else 0.0,
                sample_count=1,
                last_updated=datetime.utcnow()
            )
            self.execution_patterns[pattern_id] = pattern
        
        # Add to history
        self.execution_history.append({
            'timestamp': datetime.utcnow().isoformat(),
            'execution': execution,
            'pattern_id': pattern_id
        })
        
        # Meta-learning: Improve the learning process
        await self._meta_learn_execution()
    
    def _create_pattern_id(self, execution: Dict[str, Any]) -> str:
        """Create unique pattern ID from execution characteristics"""
        strategy = execution.get('strategy', 'unknown')
        market = execution.get('market_conditions', {})
        
        vol_bucket = int(market.get('volatility', 0.02) * 100)
        liq_bucket = int(market.get('liquidity', 1.0) * 10)
        
        return f"{strategy}_vol{vol_bucket}_liq{liq_bucket}"
    
    async def _meta_learn_execution(self):
        """
        Meta-learning: Learn how to improve the execution optimization process.
        
        This is the highest level of recursion - we analyze how well our
        execution optimization is working and improve it.
        """
        if len(self.execution_history) < 10:
            return
        
        recent = self.execution_history[-10:]
        
        # Analyze which strategies are performing best
        strategy_performance = {}
        for exec_record in recent:
            strategy = exec_record['execution'].get('strategy')
            slippage = exec_record['execution'].get('actual_slippage', 0.0)
            
            if strategy not in strategy_performance:
                strategy_performance[strategy] = []
            strategy_performance[strategy].append(slippage)
        
        # Find best and worst strategies
        avg_slippage = {}
        for strategy, slippages in strategy_performance.items():
            avg_slippage[strategy] = np.mean(slippages)
        
        if avg_slippage:
            best_strategy = min(avg_slippage, key=avg_slippage.get)
            worst_strategy = max(avg_slippage, key=avg_slippage.get)
            
            insight = {
                'timestamp': datetime.utcnow().isoformat(),
                'best_strategy': best_strategy,
                'worst_strategy': worst_strategy,
                'best_slippage': avg_slippage[best_strategy],
                'worst_slippage': avg_slippage[worst_strategy],
                'recommendation': f"Prefer {best_strategy} over {worst_strategy}"
            }
            
            self.meta_insights.append(insight)
            logger.info(f"Meta-insight: {insight['recommendation']}")
    
    def get_optimization_summary(self) -> Dict[str, Any]:
        """Get summary of execution optimization"""
        summary = {
            'total_executions': len(self.execution_history),
            'patterns_learned': len(self.execution_patterns),
            'strategies': {},
            'meta_insights': len(self.meta_insights)
        }
        
        # Add strategy performance
        for strategy_name, tracker in self.slippage_trackers.items():
            if tracker.execution_count > 0:
                summary['strategies'][strategy_name] = {
                    'avg_slippage': tracker.avg_slippage,
                    'min_slippage': tracker.min_slippage,
                    'max_slippage': tracker.max_slippage,
                    'execution_count': tracker.execution_count,
                    'improvement_rate': tracker.improvement_rate
                }
        
        return summary
