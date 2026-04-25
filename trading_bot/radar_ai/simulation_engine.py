"""
Simulation Engine - Computer Simulation for Financial Intelligence
===================================================================

Advanced simulation capabilities for understanding market dynamics:
- Monte Carlo Simulation: Probabilistic outcome modeling
- Scenario Analysis: What-if analysis for strategic planning
- Digital Twin: Real-time market replica for testing
- Agent-Based Modeling: Emergent market behavior simulation
"""

import asyncio
import logging
import math
import random
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from enum import Enum, auto
from typing import Any, Callable, Dict, List, Optional, Tuple
import uuid

logger = logging.getLogger(__name__)


class SimulationType(Enum):
    """Types of simulations"""
    MONTE_CARLO = "monte_carlo"
    SCENARIO = "scenario"
    DIGITAL_TWIN = "digital_twin"
    AGENT_BASED = "agent_based"
    STRESS_TEST = "stress_test"
    HISTORICAL_REPLAY = "historical_replay"


class ScenarioType(Enum):
    """Types of market scenarios"""
    BULL_MARKET = "bull_market"
    BEAR_MARKET = "bear_market"
    CRASH = "crash"
    RECOVERY = "recovery"
    HIGH_VOLATILITY = "high_volatility"
    LOW_VOLATILITY = "low_volatility"
    LIQUIDITY_CRISIS = "liquidity_crisis"
    RATE_HIKE = "rate_hike"
    RATE_CUT = "rate_cut"
    GEOPOLITICAL_SHOCK = "geopolitical_shock"
    CUSTOM = "custom"


@dataclass
class SimulationResult:
    """Result of a simulation run"""
    simulation_id: str
    simulation_type: SimulationType
    timestamp: datetime
    parameters: Dict[str, Any]
    outcomes: List[Dict[str, Any]]
    statistics: Dict[str, float]
    insights: List[str]
    confidence_intervals: Dict[str, Tuple[float, float]] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'simulation_id': self.simulation_id,
            'simulation_type': self.simulation_type.value,
            'timestamp': self.timestamp.isoformat(),
            'parameters': self.parameters,
            'outcomes': self.outcomes,
            'statistics': self.statistics,
            'insights': self.insights,
            'confidence_intervals': self.confidence_intervals,
        }


@dataclass
class ScenarioResult:
    """Result of a scenario analysis"""
    scenario_id: str
    scenario_type: ScenarioType
    scenario_name: str
    probability: float
    impact: Dict[str, float]
    portfolio_effect: float
    risk_metrics: Dict[str, float]
    recommended_actions: List[str]
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'scenario_id': self.scenario_id,
            'scenario_type': self.scenario_type.value,
            'scenario_name': self.scenario_name,
            'probability': self.probability,
            'impact': self.impact,
            'portfolio_effect': self.portfolio_effect,
            'risk_metrics': self.risk_metrics,
            'recommended_actions': self.recommended_actions,
        }


class MonteCarloSimulator:
    """
    Monte Carlo simulation for probabilistic outcome modeling.
    
    Uses random sampling to understand the probability distribution
    of possible outcomes for trading strategies and portfolios.
    """
    
    def __init__(self, num_simulations: int = 10000, time_horizon: int = 252):
        self.num_simulations = num_simulations
        self.time_horizon = time_horizon  # Trading days
        self.results_cache: Dict[str, SimulationResult] = {}
    
    async def simulate_price_paths(
        self,
        initial_price: float,
        expected_return: float,
        volatility: float,
        num_paths: Optional[int] = None,
    ) -> SimulationResult:
        """Simulate price paths using Geometric Brownian Motion"""
        num_paths = num_paths or self.num_simulations
        dt = 1 / 252  # Daily time step
        
        paths = []
        final_prices = []
        
        for _ in range(num_paths):
            path = [initial_price]
            price = initial_price
            
            for _ in range(self.time_horizon):
                # GBM: dS = μSdt + σSdW
                drift = (expected_return - 0.5 * volatility ** 2) * dt
                diffusion = volatility * math.sqrt(dt) * random.gauss(0, 1)
                price = price * math.exp(drift + diffusion)
                path.append(price)
            
            paths.append(path)
            final_prices.append(price)
        
        # Calculate statistics
        final_prices.sort()
        mean_price = sum(final_prices) / len(final_prices)
        
        # Percentiles
        p5 = final_prices[int(0.05 * len(final_prices))]
        p25 = final_prices[int(0.25 * len(final_prices))]
        p50 = final_prices[int(0.50 * len(final_prices))]
        p75 = final_prices[int(0.75 * len(final_prices))]
        p95 = final_prices[int(0.95 * len(final_prices))]
        
        # Returns
        returns = [(p - initial_price) / initial_price for p in final_prices]
        mean_return = sum(returns) / len(returns)
        
        # Probability of profit
        prob_profit = sum(1 for r in returns if r > 0) / len(returns)
        
        # VaR and CVaR
        var_95 = initial_price - p5
        cvar_95 = initial_price - sum(final_prices[:int(0.05 * len(final_prices))]) / int(0.05 * len(final_prices))
        
        statistics = {
            'mean_price': mean_price,
            'median_price': p50,
            'mean_return': mean_return,
            'prob_profit': prob_profit,
            'var_95': var_95,
            'cvar_95': cvar_95,
            'min_price': final_prices[0],
            'max_price': final_prices[-1],
        }
        
        insights = []
        if prob_profit > 0.6:
            insights.append(f"High probability of profit ({prob_profit:.1%})")
        elif prob_profit < 0.4:
            insights.append(f"Low probability of profit ({prob_profit:.1%})")
        
        if var_95 / initial_price > 0.2:
            insights.append(f"High downside risk: 95% VaR is {var_95/initial_price:.1%}")
        
        return SimulationResult(
            simulation_id=f"MC-{uuid.uuid4().hex[:8]}",
            simulation_type=SimulationType.MONTE_CARLO,
            timestamp=datetime.now(timezone.utc),
            parameters={
                'initial_price': initial_price,
                'expected_return': expected_return,
                'volatility': volatility,
                'num_paths': num_paths,
                'time_horizon': self.time_horizon,
            },
            outcomes=[{'path_index': i, 'final_price': p} for i, p in enumerate(final_prices[:100])],
            statistics=statistics,
            insights=insights,
            confidence_intervals={
                'price_90': (p5, p95),
                'price_50': (p25, p75),
            },
        )
    
    async def simulate_portfolio(
        self,
        positions: List[Dict[str, Any]],
        correlation_matrix: Optional[List[List[float]]] = None,
    ) -> SimulationResult:
        """Simulate portfolio value evolution"""
        num_assets = len(positions)
        
        # Default to no correlation if not provided
        if correlation_matrix is None:
            correlation_matrix = [[1.0 if i == j else 0.3 for j in range(num_assets)] for i in range(num_assets)]
        
        # Cholesky decomposition for correlated random numbers
        L = self._cholesky_decomposition(correlation_matrix)
        
        portfolio_values = []
        
        for _ in range(self.num_simulations):
            # Generate correlated random numbers
            z = [random.gauss(0, 1) for _ in range(num_assets)]
            correlated_z = [sum(L[i][j] * z[j] for j in range(i + 1)) for i in range(num_assets)]
            
            # Simulate each position
            total_value = 0
            for i, pos in enumerate(positions):
                initial_value = pos.get('value', 0)
                expected_return = pos.get('expected_return', 0.08)
                volatility = pos.get('volatility', 0.2)
                
                # Annual return
                return_i = expected_return + volatility * correlated_z[i]
                final_value = initial_value * (1 + return_i)
                total_value += final_value
            
            portfolio_values.append(total_value)
        
        # Statistics
        portfolio_values.sort()
        initial_portfolio = sum(p.get('value', 0) for p in positions)
        
        returns = [(v - initial_portfolio) / initial_portfolio for v in portfolio_values]
        
        statistics = {
            'initial_value': initial_portfolio,
            'mean_value': sum(portfolio_values) / len(portfolio_values),
            'median_value': portfolio_values[len(portfolio_values) // 2],
            'mean_return': sum(returns) / len(returns),
            'var_95': initial_portfolio - portfolio_values[int(0.05 * len(portfolio_values))],
            'prob_profit': sum(1 for r in returns if r > 0) / len(returns),
        }
        
        return SimulationResult(
            simulation_id=f"MC-PORT-{uuid.uuid4().hex[:8]}",
            simulation_type=SimulationType.MONTE_CARLO,
            timestamp=datetime.now(timezone.utc),
            parameters={
                'num_positions': num_assets,
                'initial_portfolio': initial_portfolio,
            },
            outcomes=[{'sim_index': i, 'portfolio_value': v} for i, v in enumerate(portfolio_values[:100])],
            statistics=statistics,
            insights=[],
            confidence_intervals={
                'value_90': (portfolio_values[int(0.05 * len(portfolio_values))],
                            portfolio_values[int(0.95 * len(portfolio_values))]),
            },
        )
    
    def _cholesky_decomposition(self, matrix: List[List[float]]) -> List[List[float]]:
        """Cholesky decomposition for correlation matrix"""
        n = len(matrix)
        L = [[0.0] * n for _ in range(n)]
        
        for i in range(n):
            for j in range(i + 1):
                s = sum(L[i][k] * L[j][k] for k in range(j))
                if i == j:
                    L[i][j] = math.sqrt(max(0, matrix[i][i] - s))
                else:
                    L[i][j] = (matrix[i][j] - s) / L[j][j] if L[j][j] != 0 else 0
        
        return L


class ScenarioAnalyzer:
    """
    Scenario analysis for strategic planning.
    
    Evaluates portfolio performance under various market scenarios
    to understand risks and opportunities.
    """
    
    def __init__(self):
        self.scenario_library: Dict[ScenarioType, Dict[str, Any]] = self._build_scenario_library()
    
    def _build_scenario_library(self) -> Dict[ScenarioType, Dict[str, Any]]:
        """Build library of predefined scenarios"""
        return {
            ScenarioType.BULL_MARKET: {
                'name': 'Bull Market Rally',
                'probability': 0.25,
                'equity_impact': 0.20,
                'bond_impact': -0.05,
                'volatility_change': -0.3,
                'duration_months': 12,
            },
            ScenarioType.BEAR_MARKET: {
                'name': 'Bear Market Decline',
                'probability': 0.15,
                'equity_impact': -0.25,
                'bond_impact': 0.05,
                'volatility_change': 0.5,
                'duration_months': 9,
            },
            ScenarioType.CRASH: {
                'name': 'Market Crash',
                'probability': 0.05,
                'equity_impact': -0.40,
                'bond_impact': 0.10,
                'volatility_change': 2.0,
                'duration_months': 3,
            },
            ScenarioType.RECOVERY: {
                'name': 'Market Recovery',
                'probability': 0.20,
                'equity_impact': 0.15,
                'bond_impact': -0.02,
                'volatility_change': -0.2,
                'duration_months': 6,
            },
            ScenarioType.HIGH_VOLATILITY: {
                'name': 'High Volatility Regime',
                'probability': 0.15,
                'equity_impact': -0.05,
                'bond_impact': 0.02,
                'volatility_change': 1.0,
                'duration_months': 4,
            },
            ScenarioType.LIQUIDITY_CRISIS: {
                'name': 'Liquidity Crisis',
                'probability': 0.03,
                'equity_impact': -0.30,
                'bond_impact': -0.10,
                'volatility_change': 3.0,
                'duration_months': 2,
            },
            ScenarioType.RATE_HIKE: {
                'name': 'Interest Rate Hike Cycle',
                'probability': 0.20,
                'equity_impact': -0.10,
                'bond_impact': -0.15,
                'volatility_change': 0.3,
                'duration_months': 12,
            },
            ScenarioType.RATE_CUT: {
                'name': 'Interest Rate Cut Cycle',
                'probability': 0.15,
                'equity_impact': 0.12,
                'bond_impact': 0.08,
                'volatility_change': -0.2,
                'duration_months': 12,
            },
            ScenarioType.GEOPOLITICAL_SHOCK: {
                'name': 'Geopolitical Shock',
                'probability': 0.10,
                'equity_impact': -0.15,
                'bond_impact': 0.05,
                'volatility_change': 1.5,
                'duration_months': 3,
            },
        }
    
    async def analyze_scenario(
        self,
        scenario_type: ScenarioType,
        portfolio: Dict[str, Any],
        custom_params: Optional[Dict[str, Any]] = None,
    ) -> ScenarioResult:
        """Analyze portfolio under a specific scenario"""
        scenario = self.scenario_library.get(scenario_type, {})
        if custom_params:
            scenario = {**scenario, **custom_params}
        
        # Calculate portfolio impact
        positions = portfolio.get('positions', [])
        total_value = sum(p.get('value', 0) for p in positions)
        
        impact = {}
        portfolio_effect = 0
        
        for pos in positions:
            asset_type = pos.get('asset_type', 'equity')
            value = pos.get('value', 0)
            
            if asset_type == 'equity':
                pos_impact = scenario.get('equity_impact', 0)
            elif asset_type == 'bond':
                pos_impact = scenario.get('bond_impact', 0)
            else:
                pos_impact = scenario.get('equity_impact', 0) * 0.5
            
            impact[pos.get('symbol', 'unknown')] = pos_impact
            portfolio_effect += value * pos_impact
        
        portfolio_effect_pct = portfolio_effect / total_value if total_value > 0 else 0
        
        # Risk metrics
        risk_metrics = {
            'expected_loss': -portfolio_effect if portfolio_effect < 0 else 0,
            'expected_gain': portfolio_effect if portfolio_effect > 0 else 0,
            'volatility_impact': scenario.get('volatility_change', 0),
            'duration_months': scenario.get('duration_months', 6),
            'probability_weighted_loss': -portfolio_effect * scenario.get('probability', 0.1) if portfolio_effect < 0 else 0,
        }
        
        # Recommendations
        recommendations = []
        if portfolio_effect_pct < -0.15:
            recommendations.append("Consider hedging strategies to reduce downside exposure")
            recommendations.append("Review position sizing and concentration risk")
        if scenario.get('volatility_change', 0) > 0.5:
            recommendations.append("Reduce leverage to account for increased volatility")
        if scenario_type == ScenarioType.LIQUIDITY_CRISIS:
            recommendations.append("Ensure adequate cash reserves for margin requirements")
            recommendations.append("Avoid illiquid positions")
        
        return ScenarioResult(
            scenario_id=f"SCEN-{uuid.uuid4().hex[:8]}",
            scenario_type=scenario_type,
            scenario_name=scenario.get('name', 'Custom Scenario'),
            probability=scenario.get('probability', 0.1),
            impact=impact,
            portfolio_effect=portfolio_effect_pct,
            risk_metrics=risk_metrics,
            recommended_actions=recommendations,
        )
    
    async def run_all_scenarios(
        self,
        portfolio: Dict[str, Any],
    ) -> List[ScenarioResult]:
        """Run all predefined scenarios"""
        tasks = [
            self.analyze_scenario(scenario_type, portfolio)
            for scenario_type in self.scenario_library.keys()
        ]
        
        results = await asyncio.gather(*tasks)
        return list(results)
    
    async def stress_test(
        self,
        portfolio: Dict[str, Any],
        stress_factors: Dict[str, float],
    ) -> ScenarioResult:
        """Run a custom stress test"""
        custom_params = {
            'name': 'Custom Stress Test',
            'probability': 1.0,  # Deterministic
            'equity_impact': stress_factors.get('equity_shock', -0.20),
            'bond_impact': stress_factors.get('bond_shock', -0.05),
            'volatility_change': stress_factors.get('volatility_spike', 1.0),
            'duration_months': stress_factors.get('duration', 1),
        }
        
        return await self.analyze_scenario(ScenarioType.CUSTOM, portfolio, custom_params)


class DigitalTwin:
    """
    Digital Twin of the market for real-time testing.
    
    Creates a virtual replica of market conditions that can be used
    to test strategies without real capital at risk.
    """
    
    def __init__(self):
        self.twin_id = f"TWIN-{uuid.uuid4().hex[:8]}"
        self.market_state: Dict[str, Any] = {}
        self.order_book: Dict[str, List[Dict]] = {}
        self.executed_trades: List[Dict] = []
        self.is_synced = False
    
    async def sync_with_market(self, market_data: Dict[str, Any]):
        """Synchronize twin with real market data"""
        self.market_state = {
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'prices': market_data.get('prices', {}),
            'volumes': market_data.get('volumes', {}),
            'spreads': market_data.get('spreads', {}),
            'volatilities': market_data.get('volatilities', {}),
        }
        
        # Initialize order books
        for symbol in market_data.get('prices', {}).keys():
            if symbol not in self.order_book:
                self.order_book[symbol] = []
        
        self.is_synced = True
        logger.info(f"Digital twin synced: {self.twin_id}")
    
    async def simulate_order(
        self,
        symbol: str,
        side: str,
        quantity: float,
        order_type: str = 'market',
        limit_price: Optional[float] = None,
    ) -> Dict[str, Any]:
        """Simulate order execution"""
        if not self.is_synced:
            return {'success': False, 'error': 'Twin not synced with market'}
        
        current_price = self.market_state.get('prices', {}).get(symbol, 0)
        spread = self.market_state.get('spreads', {}).get(symbol, 0.001)
        
        if current_price == 0:
            return {'success': False, 'error': f'No price data for {symbol}'}
        
        # Calculate execution price with slippage
        if order_type == 'market':
            slippage = spread * 0.5 * (1 if side == 'buy' else -1)
            execution_price = current_price * (1 + slippage)
        else:
            if limit_price is None:
                return {'success': False, 'error': 'Limit price required'}
            
            # Check if limit order would fill
            if side == 'buy' and limit_price >= current_price:
                execution_price = min(limit_price, current_price * (1 + spread * 0.5))
            elif side == 'sell' and limit_price <= current_price:
                execution_price = max(limit_price, current_price * (1 - spread * 0.5))
            else:
                return {'success': False, 'error': 'Limit order would not fill'}
        
        # Record trade
        trade = {
            'trade_id': f"SIM-{uuid.uuid4().hex[:8]}",
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'symbol': symbol,
            'side': side,
            'quantity': quantity,
            'price': execution_price,
            'value': quantity * execution_price,
            'slippage': (execution_price - current_price) / current_price,
        }
        
        self.executed_trades.append(trade)
        
        return {'success': True, 'trade': trade}
    
    async def simulate_strategy(
        self,
        strategy: Callable,
        duration_minutes: int = 60,
        tick_interval_seconds: int = 1,
    ) -> Dict[str, Any]:
        """Simulate a trading strategy over time"""
        results = {
            'trades': [],
            'pnl': 0,
            'positions': {},
        }
        
        num_ticks = (duration_minutes * 60) // tick_interval_seconds
        
        for tick in range(num_ticks):
            # Update market state with simulated price movement
            await self._simulate_price_tick()
            
            # Get strategy decision
            try:
                decision = await strategy(self.market_state)
                
                if decision and decision.get('action') in ('buy', 'sell'):
                    trade_result = await self.simulate_order(
                        symbol=decision.get('symbol'),
                        side=decision.get('action'),
                        quantity=decision.get('quantity', 1),
                    )
                    
                    if trade_result.get('success'):
                        results['trades'].append(trade_result['trade'])
                        
                        # Update positions
                        symbol = decision.get('symbol')
                        if symbol not in results['positions']:
                            results['positions'][symbol] = 0
                        
                        qty = decision.get('quantity', 1)
                        if decision.get('action') == 'buy':
                            results['positions'][symbol] += qty
                        else:
                            results['positions'][symbol] -= qty
            
            except Exception as e:
                logger.warning(f"Strategy error at tick {tick}: {e}")
        
        # Calculate final PnL
        for symbol, qty in results['positions'].items():
            current_price = self.market_state.get('prices', {}).get(symbol, 0)
            results['pnl'] += qty * current_price
        
        return results
    
    async def _simulate_price_tick(self):
        """Simulate price movement for one tick"""
        for symbol in self.market_state.get('prices', {}).keys():
            current_price = self.market_state['prices'][symbol]
            volatility = self.market_state.get('volatilities', {}).get(symbol, 0.02)
            
            # Random walk with drift
            change = random.gauss(0, volatility / math.sqrt(252 * 6.5 * 60))
            self.market_state['prices'][symbol] = current_price * (1 + change)
    
    def get_status(self) -> Dict[str, Any]:
        """Get twin status"""
        return {
            'twin_id': self.twin_id,
            'is_synced': self.is_synced,
            'market_state': self.market_state,
            'executed_trades': len(self.executed_trades),
        }


class AgentBasedModel:
    """
    Agent-Based Model for emergent market behavior simulation.
    
    Simulates markets as collections of interacting agents with
    different strategies and behaviors.
    """
    
    def __init__(self, num_agents: int = 100):
        self.num_agents = num_agents
        self.agents: List[Dict[str, Any]] = []
        self.market_price = 100.0
        self.price_history: List[float] = [self.market_price]
        self.order_flow: List[Dict] = []
        
        self._initialize_agents()
    
    def _initialize_agents(self):
        """Initialize diverse market agents"""
        agent_types = [
            ('fundamentalist', 0.3),
            ('chartist', 0.3),
            ('noise_trader', 0.2),
            ('market_maker', 0.1),
            ('arbitrageur', 0.1),
        ]
        
        for i in range(self.num_agents):
            # Randomly assign agent type based on distribution
            r = random.random()
            cumulative = 0
            agent_type = 'noise_trader'
            
            for atype, prob in agent_types:
                cumulative += prob
                if r < cumulative:
                    agent_type = atype
                    break
            
            agent = {
                'agent_id': f"ABM-{i}",
                'type': agent_type,
                'wealth': random.uniform(10000, 100000),
                'position': 0,
                'fundamental_value': 100 + random.gauss(0, 10),
                'momentum_window': random.randint(5, 20),
                'risk_tolerance': random.uniform(0.1, 0.5),
            }
            
            self.agents.append(agent)
    
    async def simulate(self, num_steps: int = 1000) -> SimulationResult:
        """Run the agent-based simulation"""
        for step in range(num_steps):
            orders = []
            
            for agent in self.agents:
                order = self._agent_decision(agent)
                if order:
                    orders.append(order)
            
            # Clear market
            self._clear_market(orders)
            
            # Record price
            self.price_history.append(self.market_price)
        
        # Calculate statistics
        returns = [(self.price_history[i] - self.price_history[i-1]) / self.price_history[i-1]
                   for i in range(1, len(self.price_history))]
        
        statistics = {
            'final_price': self.market_price,
            'price_change': (self.market_price - 100) / 100,
            'volatility': (sum(r**2 for r in returns) / len(returns)) ** 0.5 if returns else 0,
            'max_price': max(self.price_history),
            'min_price': min(self.price_history),
            'total_orders': len(self.order_flow),
        }
        
        # Analyze emergent patterns
        insights = []
        if statistics['volatility'] > 0.02:
            insights.append("High volatility regime emerged from agent interactions")
        
        # Check for bubbles/crashes
        max_drawdown = 0
        peak = self.price_history[0]
        for price in self.price_history:
            if price > peak:
                peak = price
            drawdown = (peak - price) / peak
            max_drawdown = max(max_drawdown, drawdown)
        
        if max_drawdown > 0.2:
            insights.append(f"Crash pattern detected: {max_drawdown:.1%} drawdown")
        
        return SimulationResult(
            simulation_id=f"ABM-{uuid.uuid4().hex[:8]}",
            simulation_type=SimulationType.AGENT_BASED,
            timestamp=datetime.now(timezone.utc),
            parameters={
                'num_agents': self.num_agents,
                'num_steps': num_steps,
            },
            outcomes=[{'step': i, 'price': p} for i, p in enumerate(self.price_history[::10])],
            statistics=statistics,
            insights=insights,
        )
    
    def _agent_decision(self, agent: Dict[str, Any]) -> Optional[Dict]:
        """Generate order based on agent type"""
        agent_type = agent['type']
        
        if agent_type == 'fundamentalist':
            # Trade towards fundamental value
            diff = agent['fundamental_value'] - self.market_price
            if abs(diff) > 2:
                return {
                    'agent_id': agent['agent_id'],
                    'side': 'buy' if diff > 0 else 'sell',
                    'quantity': min(abs(diff) * 0.1, agent['wealth'] * 0.01 / self.market_price),
                }
        
        elif agent_type == 'chartist':
            # Follow momentum
            if len(self.price_history) >= agent['momentum_window']:
                momentum = self.price_history[-1] - self.price_history[-agent['momentum_window']]
                if abs(momentum) > 1:
                    return {
                        'agent_id': agent['agent_id'],
                        'side': 'buy' if momentum > 0 else 'sell',
                        'quantity': min(abs(momentum) * 0.05, agent['wealth'] * 0.01 / self.market_price),
                    }
        
        elif agent_type == 'noise_trader':
            # Random trading
            if random.random() < 0.1:
                return {
                    'agent_id': agent['agent_id'],
                    'side': 'buy' if random.random() > 0.5 else 'sell',
                    'quantity': agent['wealth'] * 0.005 / self.market_price,
                }
        
        elif agent_type == 'market_maker':
            # Provide liquidity
            return {
                'agent_id': agent['agent_id'],
                'side': 'buy' if random.random() > 0.5 else 'sell',
                'quantity': agent['wealth'] * 0.02 / self.market_price,
            }
        
        return None
    
    def _clear_market(self, orders: List[Dict]):
        """Clear market and update price"""
        if not orders:
            return
        
        buy_volume = sum(o['quantity'] for o in orders if o['side'] == 'buy')
        sell_volume = sum(o['quantity'] for o in orders if o['side'] == 'sell')
        
        # Price impact
        imbalance = buy_volume - sell_volume
        price_impact = imbalance * 0.001  # Simple linear impact
        
        self.market_price = max(1, self.market_price * (1 + price_impact))
        
        # Record orders
        self.order_flow.extend(orders)


class SimulationEngine:
    """
    Master simulation engine that coordinates all simulation types.
    """
    
    def __init__(self):
        self.engine_id = f"SIM-{uuid.uuid4().hex[:8]}"
        self.monte_carlo = MonteCarloSimulator()
        self.scenario_analyzer = ScenarioAnalyzer()
        self.digital_twin = DigitalTwin()
        self.agent_model = AgentBasedModel()
        
        self.simulation_history: List[SimulationResult] = []
        
        logger.info(f"SimulationEngine initialized: {self.engine_id}")
    
    async def run_comprehensive_analysis(
        self,
        portfolio: Dict[str, Any],
        market_data: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Run comprehensive simulation analysis"""
        results = {}
        
        # Monte Carlo simulation
        positions = portfolio.get('positions', [])
        if positions:
            mc_result = await self.monte_carlo.simulate_portfolio(positions)
            results['monte_carlo'] = mc_result.to_dict()
            self.simulation_history.append(mc_result)
        
        # Scenario analysis
        scenario_results = await self.scenario_analyzer.run_all_scenarios(portfolio)
        results['scenarios'] = [s.to_dict() for s in scenario_results]
        
        # Digital twin sync
        await self.digital_twin.sync_with_market(market_data)
        results['digital_twin'] = self.digital_twin.get_status()
        
        # Agent-based model
        abm_result = await self.agent_model.simulate(num_steps=100)
        results['agent_based'] = abm_result.to_dict()
        self.simulation_history.append(abm_result)
        
        return results
    
    def get_status(self) -> Dict[str, Any]:
        """Get engine status"""
        return {
            'engine_id': self.engine_id,
            'simulations_run': len(self.simulation_history),
            'digital_twin_synced': self.digital_twin.is_synced,
        }
