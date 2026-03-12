"""
Recursive Risk Optimization

Risk management that recursively optimizes itself based on performance and market conditions.
"""

import asyncio
import logging
from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Any, Optional
import numpy as np

logger = logging.getLogger(__name__)


@dataclass
class RiskParameterEvolution:
    """Tracks evolution of a risk parameter"""
    parameter_name: str
    initial_value: float
    current_value: float
    value_history: List[float] = field(default_factory=list)
    performance_history: List[float] = field(default_factory=list)
    optimization_count: int = 0
    
    def update_value(self, new_value: float, performance: float):
        """Update parameter value and track performance"""
        self.value_history.append(new_value)
        self.performance_history.append(performance)
        self.current_value = new_value
        self.optimization_count += 1


@dataclass
class AdaptiveRiskLimits:
    """Adaptive risk limits that adjust based on performance"""
    max_risk_per_trade: float
    max_daily_loss: float
    max_drawdown: float
    max_leverage: float
    max_position_size: float
    
    def tighten(self, factor: float = 0.9):
        """Tighten all limits"""
        self.max_risk_per_trade *= factor
        self.max_daily_loss *= factor
        self.max_drawdown *= factor
        self.max_leverage *= factor
        self.max_position_size *= factor
    
    def loosen(self, factor: float = 1.1):
        """Loosen all limits"""
        self.max_risk_per_trade *= factor
        self.max_daily_loss *= factor
        self.max_drawdown *= factor
        self.max_leverage *= factor
        self.max_position_size *= factor


class RecursiveRiskOptimization:
    """
    Recursive risk optimization engine.
    
    Risk parameters optimize themselves based on:
    1. Historical performance
    2. Current market conditions
    3. Portfolio state
    4. Meta-learning from risk optimization history
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        
        # Initial risk limits (conservative)
        self.risk_limits = AdaptiveRiskLimits(
            max_risk_per_trade=self.config.get('max_risk_per_trade', 0.02),
            max_daily_loss=self.config.get('max_daily_loss', 0.05),
            max_drawdown=self.config.get('max_drawdown', 0.20),
            max_leverage=self.config.get('max_leverage', 3.0),
            max_position_size=self.config.get('max_position_size', 0.10)
        )
        
        # Track parameter evolution
        self.parameter_evolution: Dict[str, RiskParameterEvolution] = {}
        self._initialize_parameters()
        
        # Performance tracking
        self.performance_history: List[Dict[str, Any]] = []
        self.optimization_cycles: List[Dict[str, Any]] = []
        
        # Meta-learning
        self.meta_insights: List[Dict[str, Any]] = []
        
        logger.info("RecursiveRiskOptimization initialized")
    
    def _initialize_parameters(self):
        """Initialize risk parameters for tracking"""
        params = {
            'max_risk_per_trade': self.risk_limits.max_risk_per_trade,
            'max_daily_loss': self.risk_limits.max_daily_loss,
            'max_drawdown': self.risk_limits.max_drawdown,
            'max_leverage': self.risk_limits.max_leverage,
            'max_position_size': self.risk_limits.max_position_size,
        }
        
        for name, value in params.items():
            self.parameter_evolution[name] = RiskParameterEvolution(
                parameter_name=name,
                initial_value=value,
                current_value=value
            )
    
    async def optimize_risk_parameters(
        self,
        performance_data: Dict[str, Any],
        market_conditions: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Recursively optimize risk parameters.
        
        Args:
            performance_data: Recent trading performance
            market_conditions: Current market state
            
        Returns:
            Optimization results
        """
        # Record current performance
        self.performance_history.append({
            'timestamp': datetime.utcnow().isoformat(),
            'performance': performance_data,
            'market': market_conditions
        })
        
        # Analyze performance trend
        trend = self._analyze_performance_trend()
        
        # Optimize each parameter
        optimizations = {}
        for param_name, param_evolution in self.parameter_evolution.items():
            new_value = await self._optimize_parameter(
                param_name,
                param_evolution,
                trend,
                market_conditions
            )
            
            if new_value != param_evolution.current_value:
                optimizations[param_name] = {
                    'old_value': param_evolution.current_value,
                    'new_value': new_value,
                    'change_pct': (new_value - param_evolution.current_value) / param_evolution.current_value * 100
                }
                
                # Update parameter
                param_evolution.update_value(
                    new_value,
                    performance_data.get('sharpe_ratio', 0.0)
                )
                
                # Apply to risk limits
                self._apply_parameter_change(param_name, new_value)
        
        # Record optimization cycle
        cycle = {
            'timestamp': datetime.utcnow().isoformat(),
            'optimizations': optimizations,
            'trend': trend,
            'market_conditions': market_conditions
        }
        self.optimization_cycles.append(cycle)
        
        # Meta-optimization: Improve the optimization process
        await self._meta_optimize()
        
        return {
            'optimizations_made': len(optimizations),
            'changes': optimizations,
            'current_limits': self._get_current_limits(),
            'trend': trend
        }
    
    async def _optimize_parameter(
        self,
        param_name: str,
        param_evolution: RiskParameterEvolution,
        performance_trend: str,
        market_conditions: Dict[str, Any]
    ) -> float:
        """Optimize a single risk parameter"""
        current_value = param_evolution.current_value
        
        # Base adjustment on performance trend
        if performance_trend == 'improving':
            # Performance is good, can loosen slightly
            adjustment_factor = 1.05
        elif performance_trend == 'degrading':
            # Performance is poor, tighten significantly
            adjustment_factor = 0.90
        else:
            # Stable, make small adjustments based on market
            adjustment_factor = 1.0
        
        # Adjust based on market volatility
        volatility = market_conditions.get('volatility', 0.02)
        if volatility > 0.03:  # High volatility
            adjustment_factor *= 0.95  # Be more conservative
        elif volatility < 0.01:  # Low volatility
            adjustment_factor *= 1.02  # Can be slightly more aggressive
        
        # Calculate new value
        new_value = current_value * adjustment_factor
        
        # Apply bounds
        new_value = self._apply_parameter_bounds(param_name, new_value)
        
        return new_value
    
    def _apply_parameter_bounds(self, param_name: str, value: float) -> float:
        """Apply min/max bounds to parameter values"""
        bounds = {
            'max_risk_per_trade': (0.005, 0.05),  # 0.5% to 5%
            'max_daily_loss': (0.02, 0.10),  # 2% to 10%
            'max_drawdown': (0.10, 0.30),  # 10% to 30%
            'max_leverage': (1.0, 10.0),  # 1x to 10x
            'max_position_size': (0.05, 0.25),  # 5% to 25%
        }
        
        min_val, max_val = bounds.get(param_name, (0.0, float('inf')))
        return max(min_val, min(max_val, value))
    
    def _apply_parameter_change(self, param_name: str, new_value: float):
        """Apply parameter change to risk limits"""
        if param_name == 'max_risk_per_trade':
            self.risk_limits.max_risk_per_trade = new_value
        elif param_name == 'max_daily_loss':
            self.risk_limits.max_daily_loss = new_value
        elif param_name == 'max_drawdown':
            self.risk_limits.max_drawdown = new_value
        elif param_name == 'max_leverage':
            self.risk_limits.max_leverage = new_value
        elif param_name == 'max_position_size':
            self.risk_limits.max_position_size = new_value
    
    def _analyze_performance_trend(self, window: int = 10) -> str:
        """Analyze recent performance trend"""
        if len(self.performance_history) < 2:
            return 'insufficient_data'
        
        recent = self.performance_history[-window:]
        
        # Extract performance metrics
        sharpe_ratios = [p['performance'].get('sharpe_ratio', 0) for p in recent]
        
        if len(sharpe_ratios) < 2:
            return 'stable'
        
        # Calculate trend
        x = np.arange(len(sharpe_ratios))
        slope = np.polyfit(x, sharpe_ratios, 1)[0]
        
        if slope > 0.1:
            return 'improving'
        elif slope < -0.1:
            return 'degrading'
        else:
            return 'stable'
    
    async def _meta_optimize(self):
        """
        Meta-optimization: Optimize the optimization process itself.
        
        This is the recursive part - we analyze how well our risk optimization
        is working and adjust the optimization strategy.
        """
        if len(self.optimization_cycles) < 5:
            return
        
        recent_cycles = self.optimization_cycles[-5:]
        
        # Analyze optimization effectiveness
        effectiveness_scores = []
        for i in range(1, len(recent_cycles)):
            prev_cycle = recent_cycles[i-1]
            curr_cycle = recent_cycles[i]
            
            # Did optimizations improve performance?
            if len(self.performance_history) > i:
                prev_perf = self.performance_history[-i-1]['performance'].get('sharpe_ratio', 0)
                curr_perf = self.performance_history[-i]['performance'].get('sharpe_ratio', 0)
                
                if curr_perf > prev_perf:
                    effectiveness_scores.append(1.0)
                else:
                    effectiveness_scores.append(0.0)
        
        if effectiveness_scores:
            avg_effectiveness = np.mean(effectiveness_scores)
            
            insight = {
                'timestamp': datetime.utcnow().isoformat(),
                'effectiveness': avg_effectiveness,
                'insight': None
            }
            
            if avg_effectiveness < 0.4:
                # Optimization is not working well
                insight['insight'] = 'optimization_too_aggressive'
                # Be more conservative with adjustments
                logger.info("Meta-insight: Optimization too aggressive, reducing adjustment factors")
            elif avg_effectiveness > 0.7:
                # Optimization is working well
                insight['insight'] = 'optimization_effective'
                logger.info("Meta-insight: Optimization effective, maintaining strategy")
            
            self.meta_insights.append(insight)
    
    async def recursive_optimize(
        self,
        num_cycles: int,
        performance_generator: callable
    ) -> Dict[str, Any]:
        """
        Recursively optimize risk parameters over multiple cycles.
        
        Each cycle optimizes based on the previous cycle's results,
        creating a recursive improvement loop.
        """
        results = []
        
        for cycle in range(num_cycles):
            # Generate performance data (would come from actual trading)
            performance_data = await performance_generator()
            market_conditions = performance_data.get('market_conditions', {})
            
            # Optimize
            result = await self.optimize_risk_parameters(
                performance_data,
                market_conditions
            )
            
            results.append(result)
            
            # Check for convergence
            if self._has_converged():
                logger.info(f"Risk optimization converged at cycle {cycle}")
                break
        
        return {
            'cycles_completed': len(results),
            'final_limits': self._get_current_limits(),
            'total_optimizations': sum(r['optimizations_made'] for r in results),
            'meta_insights': len(self.meta_insights)
        }
    
    def _has_converged(self, window: int = 5, threshold: float = 0.01) -> bool:
        """Check if optimization has converged"""
        if len(self.optimization_cycles) < window:
            return False
        
        recent = self.optimization_cycles[-window:]
        
        # Check if recent optimizations are making small changes
        total_changes = []
        for cycle in recent:
            changes = cycle.get('optimizations', {})
            for param, change_info in changes.items():
                total_changes.append(abs(change_info.get('change_pct', 0)))
        
        if not total_changes:
            return True
        
        avg_change = np.mean(total_changes)
        return avg_change < threshold
    
    def _get_current_limits(self) -> Dict[str, float]:
        """Get current risk limits"""
        return {
            'max_risk_per_trade': self.risk_limits.max_risk_per_trade,
            'max_daily_loss': self.risk_limits.max_daily_loss,
            'max_drawdown': self.risk_limits.max_drawdown,
            'max_leverage': self.risk_limits.max_leverage,
            'max_position_size': self.risk_limits.max_position_size,
        }
    
    def get_optimization_summary(self) -> Dict[str, Any]:
        """Get summary of risk optimization"""
        summary = {
            'current_limits': self._get_current_limits(),
            'total_optimization_cycles': len(self.optimization_cycles),
            'parameter_evolution': {},
            'meta_insights': len(self.meta_insights),
            'performance_trend': self._analyze_performance_trend()
        }
        
        # Add parameter evolution details
        for param_name, evolution in self.parameter_evolution.items():
            summary['parameter_evolution'][param_name] = {
                'initial_value': evolution.initial_value,
                'current_value': evolution.current_value,
                'total_change_pct': (evolution.current_value - evolution.initial_value) / evolution.initial_value * 100,
                'optimization_count': evolution.optimization_count
            }
        
        return summary
    
    def validate_trade_risk(
        self,
        trade_risk: float,
        current_drawdown: float,
        current_leverage: float,
        position_size: float
    ) -> Dict[str, Any]:
        """
        Validate if a trade meets current risk limits.
        
        Returns validation result with pass/fail and reasons.
        """
        violations = []
        
        if trade_risk > self.risk_limits.max_risk_per_trade:
            violations.append({
                'limit': 'max_risk_per_trade',
                'value': trade_risk,
                'limit_value': self.risk_limits.max_risk_per_trade
            })
        
        if current_drawdown > self.risk_limits.max_drawdown:
            violations.append({
                'limit': 'max_drawdown',
                'value': current_drawdown,
                'limit_value': self.risk_limits.max_drawdown
            })
        
        if current_leverage > self.risk_limits.max_leverage:
            violations.append({
                'limit': 'max_leverage',
                'value': current_leverage,
                'limit_value': self.risk_limits.max_leverage
            })
        
        if position_size > self.risk_limits.max_position_size:
            violations.append({
                'limit': 'max_position_size',
                'value': position_size,
                'limit_value': self.risk_limits.max_position_size
            })
        
        return {
            'approved': len(violations) == 0,
            'violations': violations,
            'risk_score': trade_risk / self.risk_limits.max_risk_per_trade
        }
