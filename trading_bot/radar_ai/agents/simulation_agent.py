"""
Simulation Agent - World-Model Simulator
=========================================

Runs 10,000+ forward scenario simulations before any execution.

CRITICAL: Rule 4 - Simulation happens BEFORE execution
"""

import asyncio
import logging
import random
import math
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
import uuid

logger = logging.getLogger(__name__)


@dataclass
class ScenarioRun:
    """A single scenario simulation run"""
    run_id: str
    scenario_type: str
    final_pnl: float
    max_drawdown: float
    win_rate: float
    sharpe_ratio: float
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'run_id': self.run_id,
            'scenario_type': self.scenario_type,
            'final_pnl': self.final_pnl,
            'max_drawdown': self.max_drawdown,
            'win_rate': self.win_rate,
            'sharpe_ratio': self.sharpe_ratio,
        }


@dataclass
class SimulationResult:
    """Complete simulation result with 10k+ scenarios"""
    simulation_id: str
    timestamp: datetime
    num_scenarios: int
    scenarios_run: List[ScenarioRun]
    
    # Aggregated statistics
    expected_pnl: float
    median_pnl: float
    best_case_pnl: float
    worst_case_pnl: float
    probability_of_profit: float
    expected_max_drawdown: float
    var_95: float
    cvar_95: float
    
    # Verdict
    simulation_verdict: str  # 'favorable', 'neutral', 'unfavorable'
    proceed_to_execution: bool
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'simulation_id': self.simulation_id,
            'timestamp': self.timestamp.isoformat(),
            'num_scenarios': self.num_scenarios,
            'expected_pnl': self.expected_pnl,
            'median_pnl': self.median_pnl,
            'best_case_pnl': self.best_case_pnl,
            'worst_case_pnl': self.worst_case_pnl,
            'probability_of_profit': self.probability_of_profit,
            'expected_max_drawdown': self.expected_max_drawdown,
            'var_95': self.var_95,
            'cvar_95': self.cvar_95,
            'simulation_verdict': self.simulation_verdict,
            'proceed_to_execution': self.proceed_to_execution,
        }


class SimulationAgent:
    """
    Simulation Agent - World-Model Simulator
    
    Runs 10,000+ forward scenario simulations.
    
    ENFORCES RULE 4: Simulation happens BEFORE execution
    """
    
    def __init__(self, meta_orchestrator: Any):
        self.agent_id = f"SIM-{uuid.uuid4().hex[:8]}"
        self.meta_orchestrator = meta_orchestrator
        
        # Register with orchestrator
        self.meta_orchestrator.register_agent("SimulationAgent", self)
        
        # Simulation history
        self.simulations: List[SimulationResult] = []
        
        # Metrics
        self.total_simulations = 0
        self.total_scenarios_run = 0
        
        logger.info(f"SimulationAgent initialized: {self.agent_id}")
    
    async def run_world_model_simulation(
        self,
        strategy_analysis: Dict[str, Any],
        market_picture: Dict[str, Any],
        num_scenarios: int = 10000,
        experiment_id: Optional[str] = None,
    ) -> SimulationResult:
        """
        Run 10,000+ forward scenario simulations.
        
        This MUST complete before execution is allowed.
        """
        # Submit request to orchestrator
        request = await self.meta_orchestrator.submit_request(
            agent_name="SimulationAgent",
            request_type="run_simulation",
            payload={
                'num_scenarios': num_scenarios,
                'experiment_id': experiment_id or f"EXP-{uuid.uuid4().hex[:8]}",
            },
            requires_approval=False,
        )
        
        logger.info(f"Starting world-model simulation: {num_scenarios} scenarios")
        
        # Extract strategy parameters
        symbol = strategy_analysis.get('symbol', 'UNKNOWN')
        action = strategy_analysis.get('recommended_action', 'hold')
        expected_return = strategy_analysis.get('expected_return', 0.0)
        
        # Extract market parameters
        price = market_picture.get('prices', {}).get(symbol, 100)
        volatility = market_picture.get('macro_indicators', {}).get('vix', 15) / 100
        
        # Run scenarios
        scenarios = []
        
        for i in range(num_scenarios):
            scenario = await self._run_single_scenario(
                action=action,
                initial_price=price,
                expected_return=expected_return,
                volatility=volatility,
                scenario_num=i,
            )
            scenarios.append(scenario)
        
        # Calculate aggregated statistics
        pnls = [s.final_pnl for s in scenarios]
        pnls.sort()
        
        expected_pnl = sum(pnls) / len(pnls)
        median_pnl = pnls[len(pnls) // 2]
        best_case = pnls[-1]
        worst_case = pnls[0]
        
        prob_profit = sum(1 for p in pnls if p > 0) / len(pnls)
        
        # VaR and CVaR
        var_95_idx = int(0.05 * len(pnls))
        var_95 = abs(pnls[var_95_idx])
        cvar_95 = abs(sum(pnls[:var_95_idx]) / var_95_idx) if var_95_idx > 0 else 0
        
        # Max drawdown
        drawdowns = [s.max_drawdown for s in scenarios]
        expected_dd = sum(drawdowns) / len(drawdowns)
        
        # Determine verdict
        if prob_profit > 0.65 and expected_pnl > 0 and expected_dd < 0.15:
            verdict = 'favorable'
            proceed = True
        elif prob_profit < 0.45 or expected_pnl < 0 or expected_dd > 0.25:
            verdict = 'unfavorable'
            proceed = False
        else:
            verdict = 'neutral'
            proceed = True  # Allow with caution
        
        result = SimulationResult(
            simulation_id=f"SIM-{uuid.uuid4().hex[:8]}",
            timestamp=datetime.now(timezone.utc),
            num_scenarios=num_scenarios,
            scenarios_run=scenarios[:100],  # Store sample
            expected_pnl=expected_pnl,
            median_pnl=median_pnl,
            best_case_pnl=best_case,
            worst_case_pnl=worst_case,
            probability_of_profit=prob_profit,
            expected_max_drawdown=expected_dd,
            var_95=var_95,
            cvar_95=cvar_95,
            simulation_verdict=verdict,
            proceed_to_execution=proceed,
        )
        
        self.simulations.append(result)
        self.total_simulations += 1
        self.total_scenarios_run += num_scenarios
        
        logger.info(f"Simulation complete: {verdict} (P(profit)={prob_profit:.0%}, E[PnL]={expected_pnl:.2f})")
        
        return result
    
    async def _run_single_scenario(
        self,
        action: str,
        initial_price: float,
        expected_return: float,
        volatility: float,
        scenario_num: int,
    ) -> ScenarioRun:
        """Run a single scenario simulation"""
        # Simulate price path (252 trading days)
        num_days = 252
        dt = 1 / 252
        
        price = initial_price
        prices = [price]
        
        # Random walk with drift
        for _ in range(num_days):
            drift = (expected_return - 0.5 * volatility ** 2) * dt
            diffusion = volatility * math.sqrt(dt) * random.gauss(0, 1)
            price = price * math.exp(drift + diffusion)
            prices.append(price)
        
        # Calculate PnL based on action
        if action == 'buy':
            pnl = (prices[-1] - initial_price) / initial_price
        elif action == 'sell':
            pnl = (initial_price - prices[-1]) / initial_price
        else:
            pnl = 0
        
        # Calculate max drawdown
        peak = prices[0]
        max_dd = 0
        for p in prices:
            if p > peak:
                peak = p
            dd = (peak - p) / peak
            max_dd = max(max_dd, dd)
        
        # Calculate win rate (simplified)
        positive_days = sum(1 for i in range(1, len(prices)) if prices[i] > prices[i-1])
        win_rate = positive_days / (len(prices) - 1)
        
        # Calculate Sharpe (simplified)
        returns = [(prices[i] - prices[i-1]) / prices[i-1] for i in range(1, len(prices))]
        avg_return = sum(returns) / len(returns)
        std_return = (sum((r - avg_return) ** 2 for r in returns) / len(returns)) ** 0.5
        sharpe = (avg_return / std_return * math.sqrt(252)) if std_return > 0 else 0
        
        return ScenarioRun(
            run_id=f"RUN-{scenario_num}",
            scenario_type='monte_carlo',
            final_pnl=pnl,
            max_drawdown=max_dd,
            win_rate=win_rate,
            sharpe_ratio=sharpe,
        )
    
    def get_latest_simulation(self) -> Optional[SimulationResult]:
        """Get the most recent simulation result"""
        return self.simulations[-1] if self.simulations else None
    
    def get_status(self) -> Dict[str, Any]:
        """Get agent status"""
        return {
            'agent_id': self.agent_id,
            'total_simulations': self.total_simulations,
            'total_scenarios_run': self.total_scenarios_run,
            'latest_verdict': self.simulations[-1].simulation_verdict if self.simulations else None,
        }
