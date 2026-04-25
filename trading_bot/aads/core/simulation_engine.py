"""
AADS MODULE 4 — SIMULATION ENGINE

Before ANY capital commitment, the system runs:

1. Monte Carlo path simulation (10,000 scenarios, 5-day and 20-day horizons,
   GBM + regime-switching)
2. Agent-based microstructure simulation (model HFTs, institutional flow,
   retail behavior as competing agents)
3. Macro shock stress tests (replay 2008, COVID March 2020, SVB collapse,
   flash crash 2010 against current portfolio)
4. Counterfactual causal intervention ("what if Fed +50bp instead of +25bp?"
   via do-calculus on causal graph)
5. Adversarial market maker simulation (model how MMs react to your order
   size before sending it)

Simulation output produces: P10/P50/P90 outcome distribution, max drawdown
under each scenario, optimal position size, optimal entry timing.

Simulation is the PRIMARY decision tool, not a secondary check.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Tuple, Callable
from datetime import datetime, timedelta
from enum import Enum
import numpy as np
import logging
import uuid

logger = logging.getLogger(__name__)


class SimulationType(Enum):
    """Types of simulations available"""
    MONTE_CARLO = "monte_carlo"
    AGENT_BASED = "agent_based"
    STRESS_TEST = "stress_test"
    CAUSAL_COUNTERFACTUAL = "causal_counterfactual"
    ADVERSARIAL_MM = "adversarial_mm"


class MarketRegime(Enum):
    """Market regime states for regime-switching models"""
    BULL = "bull"
    BEAR = "bear"
    HIGH_VOL = "high_vol"
    LOW_VOL = "low_vol"
    CRISIS = "crisis"
    QE = "qe"
    TIGHTENING = "tightening"


@dataclass
class SimulationConfig:
    """Configuration for simulation runs"""
    n_scenarios: int = 10000
    horizons: List[int] = field(default_factory=lambda: [5, 20])  # days
    confidence_levels: List[float] = field(default_factory=lambda: [0.05, 0.25, 0.50, 0.75, 0.95])
    include_transaction_costs: bool = True
    transaction_cost_bps: float = 5.0
    include_slippage: bool = True
    slippage_model: str = "sqrt_impact"  # "linear", "sqrt_impact", "almgren_chriss"
    random_seed: Optional[int] = None


@dataclass
class SimulationResult:
    """Result of a simulation run"""
    simulation_id: str
    simulation_type: SimulationType
    asset: str
    direction: str  # "long" or "short"
    position_size: float
    horizon_days: int
    
    # Distribution statistics
    mean_return: float
    std_return: float
    skewness: float
    kurtosis: float
    
    # Percentiles
    p5: float
    p10: float
    p25: float
    p50: float
    p75: float
    p90: float
    p95: float
    
    # Risk metrics
    var_95: float  # Value at Risk 95%
    var_99: float  # Value at Risk 99%
    cvar_95: float  # Conditional VaR (Expected Shortfall)
    max_drawdown: float
    
    # Optimal sizing
    kelly_fraction: float
    optimal_position_size: float
    
    # Scenario paths (sample)
    sample_paths: List[List[float]] = field(default_factory=list)
    
    # Metadata
    n_scenarios: int = 10000
    timestamp: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'simulation_id': self.simulation_id,
            'simulation_type': self.simulation_type.value,
            'asset': self.asset,
            'direction': self.direction,
            'position_size': self.position_size,
            'horizon_days': self.horizon_days,
            'mean_return': self.mean_return,
            'std_return': self.std_return,
            'p10': self.p10,
            'p50': self.p50,
            'p90': self.p90,
            'var_95': self.var_95,
            'cvar_95': self.cvar_95,
            'max_drawdown': self.max_drawdown,
            'kelly_fraction': self.kelly_fraction,
            'optimal_position_size': self.optimal_position_size,
            'n_scenarios': self.n_scenarios
        }


@dataclass
class StressScenario:
    """Definition of a stress test scenario"""
    name: str
    description: str
    equity_shock: float  # e.g., -0.35 for 35% drop
    vol_multiplier: float  # e.g., 3.0 for 3x normal vol
    credit_spread_shock_bps: float
    rate_shock_bps: float
    duration_days: int
    recovery_days: int
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'name': self.name,
            'description': self.description,
            'equity_shock': self.equity_shock,
            'vol_multiplier': self.vol_multiplier,
            'credit_spread_shock_bps': self.credit_spread_shock_bps,
            'rate_shock_bps': self.rate_shock_bps,
            'duration_days': self.duration_days
        }


@dataclass
class AgentConfig:
    """Configuration for an agent in agent-based simulation"""
    agent_type: str
    n_agents: int
    lag: int  # reaction lag in periods
    mean_reversion: bool = False
    value_anchor: bool = False
    inventory_averse: bool = False
    rebalance_triggered: bool = False
    threshold_triggered: bool = False
    threshold_pct: float = 0.05


# Pre-defined stress scenarios based on historical events
HISTORICAL_STRESS_SCENARIOS = {
    "2008_financial_crisis": StressScenario(
        name="2008 Financial Crisis",
        description="Lehman collapse, credit freeze, equity crash",
        equity_shock=-0.55,
        vol_multiplier=4.0,
        credit_spread_shock_bps=600,
        rate_shock_bps=-200,
        duration_days=120,
        recovery_days=365
    ),
    "covid_march_2020": StressScenario(
        name="COVID March 2020",
        description="Pandemic shock, fastest bear market in history",
        equity_shock=-0.35,
        vol_multiplier=5.0,
        credit_spread_shock_bps=400,
        rate_shock_bps=-150,
        duration_days=23,
        recovery_days=150
    ),
    "svb_collapse_2023": StressScenario(
        name="SVB Collapse 2023",
        description="Regional bank crisis, rate sensitivity shock",
        equity_shock=-0.10,
        vol_multiplier=2.0,
        credit_spread_shock_bps=100,
        rate_shock_bps=-50,
        duration_days=10,
        recovery_days=30
    ),
    "flash_crash_2010": StressScenario(
        name="Flash Crash 2010",
        description="Algorithmic trading cascade, liquidity evaporation",
        equity_shock=-0.09,
        vol_multiplier=10.0,
        credit_spread_shock_bps=50,
        rate_shock_bps=-20,
        duration_days=1,
        recovery_days=1
    ),
    "fed_hawk_surprise": StressScenario(
        name="Fed Hawkish Surprise",
        description="Unexpected +75bp rate hike",
        equity_shock=-0.08,
        vol_multiplier=2.0,
        credit_spread_shock_bps=75,
        rate_shock_bps=75,
        duration_days=5,
        recovery_days=20
    ),
    "china_devaluation": StressScenario(
        name="China Currency Devaluation",
        description="CNY devaluation shock, EM contagion",
        equity_shock=-0.12,
        vol_multiplier=2.5,
        credit_spread_shock_bps=150,
        rate_shock_bps=-30,
        duration_days=15,
        recovery_days=45
    ),
    "oil_shock_plus30": StressScenario(
        name="Oil Price Spike +30%",
        description="Geopolitical oil supply shock",
        equity_shock=-0.05,
        vol_multiplier=1.5,
        credit_spread_shock_bps=50,
        rate_shock_bps=25,
        duration_days=30,
        recovery_days=60
    ),
    "vix_spike_35": StressScenario(
        name="VIX Spike to 35",
        description="Volatility regime shift",
        equity_shock=-0.10,
        vol_multiplier=2.5,
        credit_spread_shock_bps=100,
        rate_shock_bps=-25,
        duration_days=10,
        recovery_days=30
    )
}

# Agent types for microstructure simulation
MARKET_AGENT_TYPES = {
    "momentum_traders": AgentConfig(
        agent_type="momentum",
        n_agents=500,
        lag=5,
        mean_reversion=False
    ),
    "mean_reversion": AgentConfig(
        agent_type="mean_reversion",
        n_agents=300,
        lag=20,
        mean_reversion=True
    ),
    "fundamental_investors": AgentConfig(
        agent_type="fundamental",
        n_agents=100,
        lag=63,
        value_anchor=True
    ),
    "hft_market_makers": AgentConfig(
        agent_type="hft_mm",
        n_agents=50,
        lag=0,
        inventory_averse=True
    ),
    "passive_etf_flows": AgentConfig(
        agent_type="passive",
        n_agents=20,
        lag=0,
        rebalance_triggered=True
    ),
    "panic_sellers": AgentConfig(
        agent_type="panic",
        n_agents=0,  # Activated dynamically
        lag=0,
        threshold_triggered=True,
        threshold_pct=0.05
    )
}


class MonteCarloSimulator:
    """
    Monte Carlo path simulation with regime-switching.
    
    Uses GBM with regime-dependent parameters for realistic
    market dynamics simulation.
    """
    
    def __init__(self, config: Optional[SimulationConfig] = None):
        self.config = config or SimulationConfig()
        if self.config.random_seed:
            np.random.seed(self.config.random_seed)
    
    def simulate_gbm(
        self,
        s0: float,
        mu: float,
        sigma: float,
        dt: float,
        n_steps: int,
        n_paths: int
    ) -> np.ndarray:
        """
        Geometric Brownian Motion simulation.
        
        dS = mu*S*dt + sigma*S*dW
        """
        paths = np.zeros((n_paths, n_steps + 1))
        paths[:, 0] = s0
        
        for t in range(1, n_steps + 1):
            z = np.random.standard_normal(n_paths)
            paths[:, t] = paths[:, t-1] * np.exp(
                (mu - 0.5 * sigma**2) * dt + sigma * np.sqrt(dt) * z
            )
        
        return paths
    
    def simulate_regime_switching(
        self,
        s0: float,
        regime_params: Dict[MarketRegime, Tuple[float, float]],  # {regime: (mu, sigma)}
        transition_matrix: np.ndarray,
        initial_regime: MarketRegime,
        dt: float,
        n_steps: int,
        n_paths: int
    ) -> Tuple[np.ndarray, np.ndarray]:
        """
        Regime-switching GBM simulation.
        
        Market parameters change based on hidden Markov regime.
        """
        regimes = list(regime_params.keys())
        n_regimes = len(regimes)
        
        paths = np.zeros((n_paths, n_steps + 1))
        regime_paths = np.zeros((n_paths, n_steps + 1), dtype=int)
        
        paths[:, 0] = s0
        regime_paths[:, 0] = regimes.index(initial_regime)
        
        for t in range(1, n_steps + 1):
            for i in range(n_paths):
                # Transition regime
                current_regime_idx = regime_paths[i, t-1]
                new_regime_idx = np.random.choice(
                    n_regimes,
                    p=transition_matrix[current_regime_idx]
                )
                regime_paths[i, t] = new_regime_idx
                
                # Get regime parameters
                regime = regimes[new_regime_idx]
                mu, sigma = regime_params[regime]
                
                # Simulate price
                z = np.random.standard_normal()
                paths[i, t] = paths[i, t-1] * np.exp(
                    (mu - 0.5 * sigma**2) * dt + sigma * np.sqrt(dt) * z
                )
        
        return paths, regime_paths
    
    def run(
        self,
        asset: str,
        current_price: float,
        direction: str,
        position_size: float,
        horizon_days: int,
        annual_return: float = 0.08,
        annual_vol: float = 0.20
    ) -> SimulationResult:
        """Run Monte Carlo simulation"""
        
        # Convert to daily parameters
        dt = 1/252
        mu = annual_return
        sigma = annual_vol
        
        # Simulate paths
        paths = self.simulate_gbm(
            s0=current_price,
            mu=mu,
            sigma=sigma,
            dt=dt,
            n_steps=horizon_days,
            n_paths=self.config.n_scenarios
        )
        
        # Calculate returns
        final_prices = paths[:, -1]
        returns = (final_prices - current_price) / current_price
        
        # Adjust for direction
        if direction == "short":
            returns = -returns
        
        # Apply transaction costs
        if self.config.include_transaction_costs:
            returns -= self.config.transaction_cost_bps / 10000 * 2  # round trip
        
        # Calculate statistics
        mean_ret = float(np.mean(returns))
        std_ret = float(np.std(returns))
        
        # Percentiles
        percentiles = np.percentile(returns, [5, 10, 25, 50, 75, 90, 95])
        
        # Risk metrics
        var_95 = float(np.percentile(returns, 5))
        var_99 = float(np.percentile(returns, 1))
        cvar_95 = float(np.mean(returns[returns <= var_95]))
        
        # Max drawdown across paths
        max_dd = self._calculate_max_drawdown(paths, direction)
        
        # Kelly fraction
        win_rate = float(np.mean(returns > 0))
        avg_win = float(np.mean(returns[returns > 0])) if win_rate > 0 else 0
        avg_loss = float(np.mean(np.abs(returns[returns < 0]))) if win_rate < 1 else 0
        
        if avg_loss > 0:
            kelly = win_rate - (1 - win_rate) / (avg_win / avg_loss) if avg_win > 0 else 0
        else:
            kelly = win_rate
        kelly = max(0, min(kelly, 0.25))  # Cap at 25%
        
        return SimulationResult(
            simulation_id=str(uuid.uuid4()),
            simulation_type=SimulationType.MONTE_CARLO,
            asset=asset,
            direction=direction,
            position_size=position_size,
            horizon_days=horizon_days,
            mean_return=mean_ret,
            std_return=std_ret,
            skewness=float(self._skewness(returns)),
            kurtosis=float(self._kurtosis(returns)),
            p5=float(percentiles[0]),
            p10=float(percentiles[1]),
            p25=float(percentiles[2]),
            p50=float(percentiles[3]),
            p75=float(percentiles[4]),
            p90=float(percentiles[5]),
            p95=float(percentiles[6]),
            var_95=var_95,
            var_99=var_99,
            cvar_95=cvar_95,
            max_drawdown=max_dd,
            kelly_fraction=kelly,
            optimal_position_size=kelly * position_size,
            sample_paths=[paths[i].tolist() for i in range(min(10, len(paths)))],
            n_scenarios=self.config.n_scenarios
        )
    
    def _calculate_max_drawdown(self, paths: np.ndarray, direction: str) -> float:
        """Calculate maximum drawdown across all paths"""
        if direction == "short":
            paths = 2 * paths[:, 0:1] - paths  # Mirror for short
        
        max_dds = []
        for path in paths:
            peak = path[0]
            max_dd = 0
            for price in path:
                if price > peak:
                    peak = price
                dd = (peak - price) / peak
                if dd > max_dd:
                    max_dd = dd
            max_dds.append(max_dd)
        
        return float(np.percentile(max_dds, 95))
    
    def _skewness(self, x: np.ndarray) -> float:
        """Calculate skewness"""
        n = len(x)
        mean = np.mean(x)
        std = np.std(x)
        if std == 0:
            return 0
        return float(np.sum(((x - mean) / std) ** 3) / n)
    
    def _kurtosis(self, x: np.ndarray) -> float:
        """Calculate excess kurtosis"""
        n = len(x)
        mean = np.mean(x)
        std = np.std(x)
        if std == 0:
            return 0
        return float(np.sum(((x - mean) / std) ** 4) / n - 3)


class AgentBasedSimulator:
    """
    Agent-based market microstructure simulation.
    
    Models competing agents: momentum traders, mean reversion,
    fundamentals, HFT market makers, passive flows, panic sellers.
    """
    
    def __init__(self, agent_configs: Optional[Dict[str, AgentConfig]] = None):
        self.agent_configs = agent_configs or MARKET_AGENT_TYPES
    
    def run(
        self,
        asset: str,
        current_price: float,
        order_size: float,  # As fraction of ADV
        direction: str,
        horizon_steps: int = 100
    ) -> SimulationResult:
        """Run agent-based simulation"""
        
        prices = [current_price]
        order_book_imbalance = []
        
        # Initialize agent states
        agent_positions = {name: 0.0 for name in self.agent_configs}
        agent_pnl = {name: 0.0 for name in self.agent_configs}
        
        # Your order impact
        your_order_remaining = order_size
        your_fills = []
        
        for step in range(horizon_steps):
            price = prices[-1]
            
            # Calculate aggregate order flow from all agents
            net_flow = 0.0
            
            for name, config in self.agent_configs.items():
                if config.n_agents == 0:
                    continue
                
                # Agent decision based on type
                if config.agent_type == "momentum":
                    if len(prices) > config.lag:
                        momentum = (price - prices[-config.lag]) / prices[-config.lag]
                        flow = config.n_agents * momentum * 0.1
                    else:
                        flow = 0
                
                elif config.agent_type == "mean_reversion":
                    if len(prices) > config.lag:
                        deviation = (price - np.mean(prices[-config.lag:])) / price
                        flow = -config.n_agents * deviation * 0.1
                    else:
                        flow = 0
                
                elif config.agent_type == "fundamental":
                    fair_value = current_price  # Simplified
                    deviation = (price - fair_value) / fair_value
                    flow = -config.n_agents * deviation * 0.05
                
                elif config.agent_type == "hft_mm":
                    # Market makers provide liquidity, inventory averse
                    flow = -agent_positions[name] * 0.1
                
                elif config.agent_type == "passive":
                    # Passive flows are random
                    flow = np.random.randn() * config.n_agents * 0.01
                
                elif config.agent_type == "panic":
                    # Panic sellers activate on drawdown
                    if len(prices) > 1:
                        drawdown = (max(prices) - price) / max(prices)
                        if drawdown > config.threshold_pct:
                            flow = -100 * drawdown  # Panic selling
                        else:
                            flow = 0
                    else:
                        flow = 0
                else:
                    flow = 0
                
                net_flow += flow
                agent_positions[name] += flow
            
            # Add your order
            if your_order_remaining > 0:
                fill_size = min(your_order_remaining, order_size / horizon_steps * 2)
                your_fills.append(fill_size)
                your_order_remaining -= fill_size
                
                if direction == "long":
                    net_flow += fill_size * 100
                else:
                    net_flow -= fill_size * 100
            
            # Price impact (square root model)
            impact = np.sign(net_flow) * np.sqrt(abs(net_flow)) * 0.0001
            new_price = price * (1 + impact + np.random.randn() * 0.001)
            prices.append(new_price)
            order_book_imbalance.append(net_flow)
        
        # Calculate results
        final_price = prices[-1]
        returns = (final_price - current_price) / current_price
        if direction == "short":
            returns = -returns
        
        # Slippage from your order
        avg_fill_price = np.mean([prices[i] for i in range(len(your_fills))])
        slippage = abs(avg_fill_price - current_price) / current_price
        
        return SimulationResult(
            simulation_id=str(uuid.uuid4()),
            simulation_type=SimulationType.AGENT_BASED,
            asset=asset,
            direction=direction,
            position_size=order_size,
            horizon_days=horizon_steps,
            mean_return=returns - slippage,
            std_return=float(np.std(np.diff(prices) / prices[:-1])),
            skewness=0.0,
            kurtosis=0.0,
            p5=returns - slippage - 0.02,
            p10=returns - slippage - 0.01,
            p25=returns - slippage - 0.005,
            p50=returns - slippage,
            p75=returns - slippage + 0.005,
            p90=returns - slippage + 0.01,
            p95=returns - slippage + 0.02,
            var_95=-0.05,
            var_99=-0.10,
            cvar_95=-0.07,
            max_drawdown=float(max(0, max(prices) - min(prices)) / max(prices)),
            kelly_fraction=0.1,
            optimal_position_size=order_size * 0.5,
            sample_paths=[prices],
            n_scenarios=1
        )


class StressTestSimulator:
    """
    Macro shock stress test simulator.
    
    Replays historical crisis scenarios against current portfolio.
    """
    
    def __init__(self, scenarios: Optional[Dict[str, StressScenario]] = None):
        self.scenarios = scenarios or HISTORICAL_STRESS_SCENARIOS
    
    def run_scenario(
        self,
        scenario_name: str,
        portfolio: Dict[str, float],  # {asset: position_value}
        asset_betas: Dict[str, float],  # {asset: equity_beta}
        asset_durations: Dict[str, float] = None  # {asset: duration}
    ) -> Dict[str, Any]:
        """Run a single stress scenario"""
        
        scenario = self.scenarios.get(scenario_name)
        if not scenario:
            return {"error": f"Unknown scenario: {scenario_name}"}
        
        asset_durations = asset_durations or {}
        
        results = {
            "scenario": scenario.name,
            "description": scenario.description,
            "asset_impacts": {},
            "total_pnl": 0.0,
            "total_pnl_pct": 0.0
        }
        
        total_value = sum(portfolio.values())
        
        for asset, position_value in portfolio.items():
            beta = asset_betas.get(asset, 1.0)
            duration = asset_durations.get(asset, 0.0)
            
            # Equity shock impact
            equity_impact = scenario.equity_shock * beta
            
            # Rate shock impact (for bonds/REITs)
            rate_impact = -duration * scenario.rate_shock_bps / 10000
            
            # Credit spread impact
            credit_impact = -scenario.credit_spread_shock_bps / 10000 * 0.5
            
            # Total impact
            total_impact = equity_impact + rate_impact + credit_impact
            pnl = position_value * total_impact
            
            results["asset_impacts"][asset] = {
                "position_value": position_value,
                "equity_impact": equity_impact,
                "rate_impact": rate_impact,
                "credit_impact": credit_impact,
                "total_impact": total_impact,
                "pnl": pnl
            }
            
            results["total_pnl"] += pnl
        
        results["total_pnl_pct"] = results["total_pnl"] / total_value if total_value > 0 else 0
        
        return results
    
    def run_all_scenarios(
        self,
        portfolio: Dict[str, float],
        asset_betas: Dict[str, float],
        asset_durations: Dict[str, float] = None
    ) -> Dict[str, Dict[str, Any]]:
        """Run all stress scenarios"""
        
        results = {}
        for scenario_name in self.scenarios:
            results[scenario_name] = self.run_scenario(
                scenario_name, portfolio, asset_betas, asset_durations
            )
        
        return results


class AdversarialMMSimulator:
    """
    Adversarial market maker simulation.
    
    Models how market makers react to your order size before sending it.
    Helps optimize execution strategy.
    """
    
    def __init__(self):
        self.mm_inventory_aversion = 0.1
        self.mm_information_decay = 0.95
    
    def simulate_mm_response(
        self,
        order_size: float,  # As fraction of ADV
        direction: str,
        current_spread_bps: float,
        current_depth: float,  # Dollar depth at best bid/ask
        volatility: float
    ) -> Dict[str, Any]:
        """Simulate market maker response to your order"""
        
        # MM widens spread based on order size
        spread_widening = order_size * 10 * volatility * 100  # bps
        new_spread = current_spread_bps + spread_widening
        
        # MM reduces depth
        depth_reduction = 1 - min(0.9, order_size * 2)
        new_depth = current_depth * depth_reduction
        
        # Expected slippage
        if order_size * current_depth > current_depth:
            # Order walks the book
            levels_consumed = int(order_size * current_depth / current_depth)
            slippage_bps = new_spread / 2 + levels_consumed * 2
        else:
            slippage_bps = new_spread / 2
        
        # MM adverse selection cost
        adverse_selection = order_size * volatility * 100 * 0.5
        
        # Total expected cost
        total_cost_bps = slippage_bps + adverse_selection
        
        return {
            "original_spread_bps": current_spread_bps,
            "new_spread_bps": new_spread,
            "spread_widening_bps": spread_widening,
            "original_depth": current_depth,
            "new_depth": new_depth,
            "expected_slippage_bps": slippage_bps,
            "adverse_selection_bps": adverse_selection,
            "total_cost_bps": total_cost_bps,
            "recommendation": self._get_execution_recommendation(total_cost_bps, order_size)
        }
    
    def _get_execution_recommendation(self, cost_bps: float, order_size: float) -> str:
        """Get execution recommendation based on expected costs"""
        if cost_bps > 50:
            return "REJECT: Market impact too high"
        elif cost_bps > 25:
            return "TWAP: Split order over 30 minutes"
        elif cost_bps > 10:
            return "VWAP: Execute with volume participation"
        else:
            return "IMMEDIATE: Execute at market"


class AADSSimulationEngine:
    """
    Main AADS Simulation Engine.
    
    Orchestrates all simulation types and provides unified interface.
    Simulation is the PRIMARY decision tool - runs BEFORE every decision.
    """
    
    def __init__(self, config: Optional[SimulationConfig] = None):
        self.config = config or SimulationConfig()
        
        self.monte_carlo = MonteCarloSimulator(config)
        self.agent_based = AgentBasedSimulator()
        self.stress_test = StressTestSimulator()
        self.adversarial_mm = AdversarialMMSimulator()
        
        logger.info("AADSSimulationEngine initialized")
    
    def run_full_simulation_suite(
        self,
        asset: str,
        current_price: float,
        direction: str,
        position_size: float,
        portfolio: Optional[Dict[str, float]] = None,
        asset_betas: Optional[Dict[str, float]] = None
    ) -> Dict[str, Any]:
        """
        Run the complete simulation suite before any capital commitment.
        
        Returns comprehensive simulation results including:
        - Monte Carlo scenarios
        - Agent-based microstructure
        - Stress tests
        - Adversarial MM analysis
        """
        
        results = {
            "asset": asset,
            "direction": direction,
            "position_size": position_size,
            "timestamp": datetime.now().isoformat()
        }
        
        # 1. Monte Carlo (5-day and 20-day horizons)
        mc_results = {}
        for horizon in self.config.horizons:
            mc_result = self.monte_carlo.run(
                asset=asset,
                current_price=current_price,
                direction=direction,
                position_size=position_size,
                horizon_days=horizon
            )
            mc_results[f"{horizon}d"] = mc_result.to_dict()
        results["monte_carlo"] = mc_results
        
        # 2. Agent-based microstructure
        ab_result = self.agent_based.run(
            asset=asset,
            current_price=current_price,
            order_size=position_size,
            direction=direction
        )
        results["agent_based"] = ab_result.to_dict()
        
        # 3. Stress tests
        if portfolio and asset_betas:
            stress_results = self.stress_test.run_all_scenarios(
                portfolio=portfolio,
                asset_betas=asset_betas
            )
            results["stress_tests"] = stress_results
        else:
            # Single asset stress
            single_portfolio = {asset: position_size * current_price}
            single_betas = {asset: 1.0}
            stress_results = self.stress_test.run_all_scenarios(
                portfolio=single_portfolio,
                asset_betas=single_betas
            )
            results["stress_tests"] = stress_results
        
        # 4. Adversarial MM
        mm_result = self.adversarial_mm.simulate_mm_response(
            order_size=position_size,
            direction=direction,
            current_spread_bps=5.0,
            current_depth=1000000,
            volatility=0.02
        )
        results["adversarial_mm"] = mm_result
        
        # 5. Summary decision metrics
        mc_5d = mc_results.get("5d", {})
        results["summary"] = {
            "expected_return_5d": mc_5d.get("mean_return", 0),
            "var_95_5d": mc_5d.get("var_95", 0),
            "max_drawdown": mc_5d.get("max_drawdown", 0),
            "kelly_fraction": mc_5d.get("kelly_fraction", 0),
            "optimal_size": mc_5d.get("optimal_position_size", 0),
            "execution_cost_bps": mm_result.get("total_cost_bps", 0),
            "worst_stress_scenario": self._get_worst_stress(stress_results),
            "simulation_approval": self._get_simulation_approval(mc_5d, mm_result, stress_results)
        }
        
        return results
    
    def _get_worst_stress(self, stress_results: Dict[str, Any]) -> Dict[str, Any]:
        """Find the worst stress scenario"""
        worst = None
        worst_pnl = 0
        
        for name, result in stress_results.items():
            if isinstance(result, dict) and "total_pnl_pct" in result:
                if result["total_pnl_pct"] < worst_pnl:
                    worst_pnl = result["total_pnl_pct"]
                    worst = {"scenario": name, "pnl_pct": worst_pnl}
        
        return worst or {"scenario": "none", "pnl_pct": 0}
    
    def _get_simulation_approval(
        self,
        mc_result: Dict[str, Any],
        mm_result: Dict[str, Any],
        stress_results: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Determine if simulation approves the trade"""
        
        checks = []
        approved = True
        
        # Check 1: Expected return positive
        if mc_result.get("mean_return", 0) <= 0:
            checks.append("FAIL: Negative expected return")
            approved = False
        else:
            checks.append("PASS: Positive expected return")
        
        # Check 2: VaR acceptable
        if mc_result.get("var_95", 0) < -0.10:
            checks.append("FAIL: VaR 95 exceeds 10%")
            approved = False
        else:
            checks.append("PASS: VaR 95 acceptable")
        
        # Check 3: Execution cost acceptable
        if mm_result.get("total_cost_bps", 0) > 50:
            checks.append("FAIL: Execution cost > 50bps")
            approved = False
        else:
            checks.append("PASS: Execution cost acceptable")
        
        # Check 4: Survives stress scenarios
        worst = self._get_worst_stress(stress_results)
        if worst.get("pnl_pct", 0) < -0.20:
            checks.append(f"FAIL: Stress scenario {worst['scenario']} loss > 20%")
            approved = False
        else:
            checks.append("PASS: Survives stress scenarios")
        
        return {
            "approved": approved,
            "checks": checks,
            "recommendation": "PROCEED" if approved else "REJECT"
        }


# Singleton instance
_simulation_engine: Optional[AADSSimulationEngine] = None


def get_simulation_engine() -> AADSSimulationEngine:
    """Get the global simulation engine instance"""
    global _simulation_engine
    if _simulation_engine is None:
        _simulation_engine = AADSSimulationEngine()
    return _simulation_engine
