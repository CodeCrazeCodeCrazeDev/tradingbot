"""
Economic Objective Functions
=============================

Comprehensive objective functions for trading systems.
Supports PNL, Sharpe, risk-adjusted returns, latency, throughput, and more.
"""

import numpy as np
from typing import Dict, List, Callable, Optional, Any
from dataclasses import dataclass
from datetime import datetime


@dataclass
class TradingMetrics:
    """Complete trading performance metrics"""
    # Profit/Loss
    pnl: float = 0.0
    pnl_pct: float = 0.0
    realized_pnl: float = 0.0
    unrealized_pnl: float = 0.0
    
    # Risk
    max_drawdown: float = 0.0
    max_drawdown_pct: float = 0.0
    volatility: float = 0.0
    var_95: float = 0.0  # Value at Risk
    cvar_95: float = 0.0  # Conditional VaR
    
    # Ratios
    sharpe_ratio: float = 0.0
    sortino_ratio: float = 0.0
    calmar_ratio: float = 0.0
    omega_ratio: float = 0.0
    
    # Performance
    win_rate: float = 0.0
    profit_factor: float = 0.0
    avg_win: float = 0.0
    avg_loss: float = 0.0
    win_loss_ratio: float = 0.0
    expectancy: float = 0.0
    
    # Operational
    latency_ms: float = 0.0
    throughput: float = 0.0  # Signals/trades per second
    uptime_pct: float = 100.0
    error_rate: float = 0.0
    slippage_bps: float = 0.0
    fill_rate: float = 1.0
    
    # Efficiency
    capital_utilization: float = 0.0
    turnover: float = 0.0
    fees_pct: float = 0.0
    
    # Meta
    timestamp: str = ""
    
    def to_dict(self) -> Dict[str, float]:
        return {
            'pnl': self.pnl,
            'pnl_pct': self.pnl_pct,
            'realized_pnl': self.realized_pnl,
            'unrealized_pnl': self.unrealized_pnl,
            'max_drawdown': self.max_drawdown,
            'max_drawdown_pct': self.max_drawdown_pct,
            'volatility': self.volatility,
            'var_95': self.var_95,
            'cvar_95': self.cvar_95,
            'sharpe_ratio': self.sharpe_ratio,
            'sortino_ratio': self.sortino_ratio,
            'calmar_ratio': self.calmar_ratio,
            'omega_ratio': self.omega_ratio,
            'win_rate': self.win_rate,
            'profit_factor': self.profit_factor,
            'avg_win': self.avg_win,
            'avg_loss': self.avg_loss,
            'win_loss_ratio': self.win_loss_ratio,
            'expectancy': self.expectancy,
            'latency_ms': self.latency_ms,
            'throughput': self.throughput,
            'uptime_pct': self.uptime_pct,
            'error_rate': self.error_rate,
            'slippage_bps': self.slippage_bps,
            'fill_rate': self.fill_rate,
            'capital_utilization': self.capital_utilization,
            'turnover': self.turnover,
            'fees_pct': self.fees_pct,
        }


class EconomicObjectiveLibrary:
    """Library of pre-built economic objective functions"""
    
    @staticmethod
    def comprehensive_trading_objective(
        pnl_weight: float = 0.25,
        sharpe_weight: float = 0.20,
        drawdown_penalty: float = 0.15,
        latency_penalty: float = 0.10,
        throughput_weight: float = 0.10,
        win_rate_weight: float = 0.10,
        reliability_weight: float = 0.10
    ) -> Callable[[Dict[str, Any]], float]:
        """
        Comprehensive trading objective balancing all key metrics.
        
        Weights should sum to ~1.0
        """
        def objective(metrics: Dict[str, Any]) -> float:
            # PNL component (normalize to annualized %)
            pnl_score = np.tanh(metrics.get('pnl_pct', 0) / 50)  # Soft cap at 50%
            
            # Sharpe ratio (excellent = 2+, good = 1+)
            sharpe = metrics.get('sharpe_ratio', 0)
            sharpe_score = np.tanh(sharpe / 2)  # Normalize
            
            # Drawdown penalty (lower is better)
            drawdown = metrics.get('max_drawdown_pct', 0)
            drawdown_score = max(0, 1 - drawdown / 0.20)  # 20% drawdown = 0 score
            
            # Latency penalty (lower is better, ms scale)
            latency = metrics.get('latency_ms', 100)
            latency_score = max(0, 1 - latency / 10)  # 10ms+ = 0 score
            
            # Throughput (signals per second)
            throughput = metrics.get('throughput', 0)
            throughput_score = np.tanh(throughput / 10)  # 10+/sec = good
            
            # Win rate
            win_rate = metrics.get('win_rate', 0.5)
            win_rate_score = (win_rate - 0.5) * 2  # Center at 0.5
            
            # Reliability (uptime - errors)
            reliability = metrics.get('uptime_pct', 100) / 100 - metrics.get('error_rate', 0)
            
            # Combined score
            score = (
                pnl_weight * pnl_score +
                sharpe_weight * sharpe_score -
                drawdown_penalty * (1 - drawdown_score) -
                latency_penalty * (1 - latency_score) +
                throughput_weight * throughput_score +
                win_rate_weight * win_rate_score +
                reliability_weight * reliability
            )
            
            return score
        
        return objective
    
    @staticmethod
    def high_frequency_trading_objective() -> Callable[[Dict[str, Any]], float]:
        """
        Optimized for HFT: latency > throughput > reliability > PNL
        """
        return EconomicObjectiveLibrary.comprehensive_trading_objective(
            pnl_weight=0.15,
            sharpe_weight=0.10,
            drawdown_penalty=0.05,
            latency_penalty=0.35,  # Heavy latency penalty
            throughput_weight=0.20,
            win_rate_weight=0.05,
            reliability_weight=0.10
        )
    
    @staticmethod
    def alpha_generation_objective() -> Callable[[Dict[str, Any]], float]:
        """
        Optimized for alpha strategies: Sharpe > PNL > Drawdown > other
        """
        return EconomicObjectiveLibrary.comprehensive_trading_objective(
            pnl_weight=0.20,
            sharpe_weight=0.30,  # High weight on Sharpe
            drawdown_penalty=0.20,
            latency_penalty=0.05,
            throughput_weight=0.10,
            win_rate_weight=0.10,
            reliability_weight=0.05
        )
    
    @staticmethod
    def risk_parity_objective() -> Callable[[Dict[str, Any]], float]:
        """
        Optimized for risk management: Drawdown > Sharpe > Reliability
        """
        return EconomicObjectiveLibrary.comprehensive_trading_objective(
            pnl_weight=0.15,
            sharpe_weight=0.20,
            drawdown_penalty=0.30,  # Heavy drawdown penalty
            latency_penalty=0.05,
            throughput_weight=0.10,
            win_rate_weight=0.10,
            reliability_weight=0.10
        )
    
    @staticmethod
    def throughput_maximizer() -> Callable[[Dict[str, Any]], float]:
        """
        Maximize processing throughput (for high-volume operations)
        """
        def objective(metrics: Dict[str, Any]) -> float:
            throughput = metrics.get('throughput', 0)
            latency = metrics.get('latency_ms', 100)
            error_rate = metrics.get('error_rate', 0)
            
            # Score: high throughput, low latency, low errors
            throughput_score = np.log1p(throughput) / 5  # Log scale
            latency_score = max(0, 1 - latency / 5)  # 5ms threshold
            reliability_score = 1 - error_rate
            
            return 0.5 * throughput_score + 0.3 * latency_score + 0.2 * reliability_score
        
        return objective
    
    @staticmethod
    def latency_minimizer(max_acceptable_ms: float = 5.0) -> Callable[[Dict[str, Any]], float]:
        """
        Minimize latency for millisecond-scale operations.
        
        Args:
            max_acceptable_ms: Latency threshold where score goes to 0
        """
        def objective(metrics: Dict[str, Any]) -> float:
            latency = metrics.get('latency_ms', max_acceptable_ms)
            error_rate = metrics.get('error_rate', 0)
            throughput = metrics.get('throughput', 0)
            
            # Exponential decay for latency
            latency_score = np.exp(-latency / (max_acceptable_ms / 3))
            
            # Reliability must be high
            reliability = 1 - error_rate
            
            # Some throughput required
            throughput_factor = min(1.0, throughput / 100)
            
            return 0.7 * latency_score + 0.2 * reliability + 0.1 * throughput_factor
        
        return objective
    
    @staticmethod
    def custom_objective(
        weights: Dict[str, float],
        thresholds: Optional[Dict[str, float]] = None
    ) -> Callable[[Dict[str, Any]], float]:
        """
        Create custom objective with specific weights and thresholds.
        
        Args:
            weights: Dict of metric -> weight (e.g., {'pnl': 0.5, 'sharpe': 0.3})
            thresholds: Dict of metric -> threshold for normalization
        """
        thresholds = thresholds or {}
        
        def objective(metrics: Dict[str, Any]) -> float:
            score = 0.0
            
            for metric, weight in weights.items():
                value = metrics.get(metric, 0)
                
                # Get threshold for this metric
                threshold = thresholds.get(metric, 1.0)
                
                # Handle negative metrics (costs/penalties)
                if metric in ['latency_ms', 'error_rate', 'max_drawdown', 'max_drawdown_pct', 
                             'slippage_bps', 'fees_pct', 'volatility']:
                    # Lower is better
                    normalized = max(0, 1 - value / threshold) if threshold > 0 else 0
                else:
                    # Higher is better
                    normalized = min(1, value / threshold) if threshold > 0 else value
                
                score += weight * normalized
            
            return score
        
        return objective
    
    @staticmethod
    def multi_objective_pareto(
        objectives: List[Callable[[Dict[str, Any]], float]],
        weights: Optional[List[float]] = None
    ) -> Callable[[Dict[str, Any]], float]:
        """
        Combine multiple objectives with Pareto weighting.
        
        Each sub-objective can be optimized independently,
        combined here with weights.
        """
        if weights is None:
            weights = [1.0 / len(objectives)] * len(objectives)
        
        def objective(metrics: Dict[str, Any]) -> float:
            scores = [obj(metrics) for obj in objectives]
            return sum(w * s for w, s in zip(weights, scores))
        
        return objective


class ObjectiveOptimizer:
    """Optimize and track objective function performance"""
    
    def __init__(self, objective_fn: Callable[[Dict[str, Any]], float]):
        self.objective_fn = objective_fn
        self.history: List[Dict[str, Any]] = []
        self.best_score = -float('inf')
        self.best_metrics: Optional[Dict[str, Any]] = None
    
    def evaluate(self, metrics: Dict[str, Any]) -> float:
        """Evaluate metrics and track history"""
        score = self.objective_fn(metrics)
        
        entry = {
            'timestamp': datetime.utcnow().isoformat(),
            'metrics': metrics,
            'score': score
        }
        
        self.history.append(entry)
        
        # Keep history bounded
        if len(self.history) > 10000:
            self.history = self.history[-5000:]
        
        # Track best
        if score > self.best_score:
            self.best_score = score
            self.best_metrics = metrics.copy()
        
        return score
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get objective statistics"""
        if not self.history:
            return {'samples': 0}
        
        scores = [h['score'] for h in self.history]
        
        return {
            'samples': len(self.history),
            'current_score': scores[-1],
            'best_score': self.best_score,
            'mean_score': np.mean(scores),
            'std_score': np.std(scores),
            'trend': 'improving' if len(scores) > 10 and 
                     np.mean(scores[-10:]) > np.mean(scores[:10]) else 'stable',
            'best_metrics': self.best_metrics
        }
    
    def is_improvement(self, metrics: Dict[str, Any], 
                      threshold: float = 0.01) -> bool:
        """Check if metrics represent meaningful improvement"""
        score = self.objective_fn(metrics)
        return score > self.best_score * (1 + threshold)


# Pre-built objective presets
OBJECTIVE_PRESETS = {
    'comprehensive': EconomicObjectiveLibrary.comprehensive_trading_objective,
    'hft': EconomicObjectiveLibrary.high_frequency_trading_objective,
    'alpha': EconomicObjectiveLibrary.alpha_generation_objective,
    'risk_parity': EconomicObjectiveLibrary.risk_parity_objective,
    'throughput': EconomicObjectiveLibrary.throughput_maximizer,
    'latency': EconomicObjectiveLibrary.latency_minimizer,
}


def get_objective(name: str, **kwargs) -> Callable[[Dict[str, Any]], float]:
    """Get a pre-built objective by name"""
    if name not in OBJECTIVE_PRESETS:
        raise ValueError(f"Unknown objective: {name}. Available: {list(OBJECTIVE_PRESETS.keys())}")
    
    return OBJECTIVE_PRESETS[name](**kwargs)


def create_trading_metrics_from_dict(data: Dict[str, Any]) -> TradingMetrics:
    """Create TradingMetrics from dictionary"""
    return TradingMetrics(
        pnl=data.get('pnl', 0.0),
        pnl_pct=data.get('pnl_pct', 0.0),
        realized_pnl=data.get('realized_pnl', 0.0),
        unrealized_pnl=data.get('unrealized_pnl', 0.0),
        max_drawdown=data.get('max_drawdown', 0.0),
        max_drawdown_pct=data.get('max_drawdown_pct', 0.0),
        volatility=data.get('volatility', 0.0),
        var_95=data.get('var_95', 0.0),
        cvar_95=data.get('cvar_95', 0.0),
        sharpe_ratio=data.get('sharpe_ratio', 0.0),
        sortino_ratio=data.get('sortino_ratio', 0.0),
        calmar_ratio=data.get('calmar_ratio', 0.0),
        omega_ratio=data.get('omega_ratio', 0.0),
        win_rate=data.get('win_rate', 0.0),
        profit_factor=data.get('profit_factor', 0.0),
        avg_win=data.get('avg_win', 0.0),
        avg_loss=data.get('avg_loss', 0.0),
        win_loss_ratio=data.get('win_loss_ratio', 0.0),
        expectancy=data.get('expectancy', 0.0),
        latency_ms=data.get('latency_ms', 0.0),
        throughput=data.get('throughput', 0.0),
        uptime_pct=data.get('uptime_pct', 100.0),
        error_rate=data.get('error_rate', 0.0),
        slippage_bps=data.get('slippage_bps', 0.0),
        fill_rate=data.get('fill_rate', 1.0),
        capital_utilization=data.get('capital_utilization', 0.0),
        turnover=data.get('turnover', 0.0),
        fees_pct=data.get('fees_pct', 0.0),
        timestamp=data.get('timestamp', datetime.utcnow().isoformat())
    )
