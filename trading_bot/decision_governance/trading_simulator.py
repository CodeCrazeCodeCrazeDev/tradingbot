"""
Intelligent Trading Simulator for Self-Testing

Provides a realistic market simulation environment where the unified financial
intelligence system can safely test its strategies, validate improvements,
and practice trading without risking real capital.

Key Features:
- Realistic market simulation with multiple regimes
- Scenario-based testing (crashes, volatility, trends)
- Safe self-testing of new capabilities
- Performance measurement under various conditions
- Integration with the self-inspection and evolution systems
"""

from typing import Dict, List, Optional, Any, Tuple, Callable
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum
from collections import deque
import numpy as np
import asyncio
import logging

logger = logging.getLogger(__name__)


class MarketRegime(Enum):
    """Market regime types for simulation"""
    BULL_TREND = "bull_trend"
    BEAR_TREND = "bear_trend"
    HIGH_VOLATILITY = "high_volatility"
    LOW_VOLATILITY = "low_volatility"
    SIDEWAYS = "sideways"
    CRASH = "crash"
    RECOVERY = "recovery"
    FLASH_CRASH = "flash_crash"
    BUBBLE = "bubble"
    MEAN_REVERSION = "mean_reversion"


@dataclass
class SimulatedTrade:
    """Record of a simulated trade"""
    trade_id: str
    timestamp: datetime
    symbol: str
    direction: str  # 'long' or 'short'
    entry_price: float
    size: float
    stop_loss: Optional[float] = None
    take_profit: Optional[float] = None
    exit_price: Optional[float] = None
    exit_time: Optional[datetime] = None
    pnl: Optional[float] = None
    pnl_percent: Optional[float] = None
    exit_reason: Optional[str] = None  # 'stop_loss', 'take_profit', 'signal', 'manual'
    
    @property
    def is_open(self) -> bool:
        return self.exit_price is None


@dataclass
class SimulationState:
    """Current state of the simulation"""
    current_time: datetime
    current_regime: MarketRegime
    price: float
    volatility: float
    volume: float
    trend_strength: float
    available_capital: float
    open_trades: List[SimulatedTrade] = field(default_factory=list)
    closed_trades: List[SimulatedTrade] = field(default_factory=list)
    
    # Performance tracking
    total_trades: int = 0
    winning_trades: int = 0
    losing_trades: int = 0
    total_pnl: float = 0.0
    max_drawdown: float = 0.0
    peak_capital: float = 0.0


@dataclass
class ScenarioConfig:
    """Configuration for a market scenario"""
    name: str
    description: str
    duration_days: int
    regime_sequence: List[Tuple[MarketRegime, int]]  # (regime, days)
    initial_price: float
    volatility_range: Tuple[float, float]
    trend_magnitude: float
    shock_events: Optional[List[Tuple[int, str, float]]] = None  # (day, event_type, magnitude)


class MarketSimulator:
    """
    Realistic market simulator for safe self-testing
    
    Generates synthetic price data with realistic characteristics:
    - Regime changes
    - Volatility clustering
    - Mean reversion and trending behavior
    - Flash crashes and recovery patterns
    """
    
    def __init__(
        self,
        initial_capital: float = 100000.0,
        seed: Optional[int] = None
    ):
        self.initial_capital = initial_capital
        self.rng = np.random.RandomState(seed)
        
        # Simulation state
        self.state: Optional[SimulationState] = None
        self.price_history: deque = deque(maxlen=1000)
        self.regime_history: deque = deque(maxlen=100)
        
        # Current regime parameters
        self.regime_params: Dict[str, Any] = {}
        
        logger.info(f"MarketSimulator initialized with ${initial_capital:,.2f} capital")
    
    def start_simulation(
        self,
        start_time: Optional[datetime] = None,
        initial_price: float = 100.0,
        initial_regime: MarketRegime = MarketRegime.SIDEWAYS
    ) -> SimulationState:
        """Start a new simulation"""
        start_time = start_time or datetime.utcnow()
        
        self.state = SimulationState(
            current_time=start_time,
            current_regime=initial_regime,
            price=initial_price,
            volatility=0.02,
            volume=1000000,
            trend_strength=0.0,
            available_capital=self.initial_capital,
            open_trades=[],
            closed_trades=[],
            peak_capital=self.initial_capital
        )
        
        self.price_history.append(initial_price)
        self.regime_history.append((start_time, initial_regime))
        
        self._set_regime_parameters(initial_regime)
        
        logger.info(f"Simulation started: {initial_regime.value} at ${initial_price:.2f}")
        return self.state
    
    def step(self, hours: int = 1) -> SimulationState:
        """Advance simulation by N hours"""
        if not self.state:
            raise RuntimeError("Simulation not started. Call start_simulation() first.")
        
        for _ in range(hours):
            self._update_price()
            self._check_trades()
            self.state.current_time += timedelta(hours=1)
        
        return self.state
    
    def _update_price(self):
        """Update price based on current regime"""
        current_price = self.state.price
        
        # Regime-specific drift
        drift = self.regime_params.get('drift', 0.0)
        
        # Volatility with clustering
        base_vol = self.regime_params.get('volatility', 0.02)
        vol_cluster = self.state.volatility * 0.7 + base_vol * 0.3
        
        # Mean reversion component
        mean_reversion = self.regime_params.get('mean_reversion', 0.0)
        if mean_reversion > 0 and len(self.price_history) > 20:
            moving_avg = np.mean(list(self.price_history)[-20:])
            reversion_force = (moving_avg - current_price) / current_price * mean_reversion
            drift += reversion_force
        
        # Generate price change
        price_change = drift + vol_cluster * self.rng.normal()
        new_price = current_price * (1 + price_change)
        
        # Update state
        self.state.price = max(0.01, new_price)  # Floor at $0.01
        self.state.volatility = vol_cluster
        self.price_history.append(self.state.price)
    
    def _set_regime_parameters(self, regime: MarketRegime):
        """Set parameters for a market regime"""
        params = {
            MarketRegime.BULL_TREND: {
                'drift': 0.0005,  # 0.05% per hour
                'volatility': 0.015,
                'mean_reversion': 0.0,
                'trend_persistence': 0.95
            },
            MarketRegime.BEAR_TREND: {
                'drift': -0.0005,
                'volatility': 0.02,
                'mean_reversion': 0.0,
                'trend_persistence': 0.95
            },
            MarketRegime.HIGH_VOLATILITY: {
                'drift': 0.0,
                'volatility': 0.04,
                'mean_reversion': 0.1,
                'trend_persistence': 0.7
            },
            MarketRegime.LOW_VOLATILITY: {
                'drift': 0.0001,
                'volatility': 0.008,
                'mean_reversion': 0.3,
                'trend_persistence': 0.8
            },
            MarketRegime.SIDEWAYS: {
                'drift': 0.0,
                'volatility': 0.015,
                'mean_reversion': 0.2,
                'trend_persistence': 0.5
            },
            MarketRegime.CRASH: {
                'drift': -0.005,
                'volatility': 0.06,
                'mean_reversion': 0.0,
                'trend_persistence': 0.3
            },
            MarketRegime.RECOVERY: {
                'drift': 0.002,
                'volatility': 0.025,
                'mean_reversion': 0.0,
                'trend_persistence': 0.9
            },
            MarketRegime.FLASH_CRASH: {
                'drift': -0.01,
                'volatility': 0.08,
                'mean_reversion': 0.0,
                'trend_persistence': 0.1
            },
            MarketRegime.BUBBLE: {
                'drift': 0.003,
                'volatility': 0.03,
                'mean_reversion': -0.1,  # Negative = away from mean
                'trend_persistence': 0.98
            },
            MarketRegime.MEAN_REVERSION: {
                'drift': 0.0,
                'volatility': 0.02,
                'mean_reversion': 0.4,
                'trend_persistence': 0.3
            }
        }
        
        self.regime_params = params.get(regime, params[MarketRegime.SIDEWAYS])
        self.state.current_regime = regime
        self.state.trend_strength = self.regime_params.get('trend_persistence', 0.5)
        
        logger.debug(f"Regime changed to {regime.value}")
    
    def change_regime(self, new_regime: MarketRegime):
        """Change the current market regime"""
        self._set_regime_parameters(new_regime)
        self.regime_history.append((self.state.current_time, new_regime))
        logger.info(f"Regime transition: {new_regime.value}")
    
    def _check_trades(self):
        """Check if any open trades hit stops or targets"""
        current_price = self.state.price
        
        for trade in self.state.open_trades[:]:
            if trade.direction == 'long':
                # Check stop loss
                if trade.stop_loss and current_price <= trade.stop_loss:
                    self._close_trade(trade, current_price, 'stop_loss')
                # Check take profit
                elif trade.take_profit and current_price >= trade.take_profit:
                    self._close_trade(trade, current_price, 'take_profit')
            else:  # short
                # Check stop loss
                if trade.stop_loss and current_price >= trade.stop_loss:
                    self._close_trade(trade, current_price, 'stop_loss')
                # Check take profit
                elif trade.take_profit and current_price <= trade.take_profit:
                    self._close_trade(trade, current_price, 'take_profit')
    
    def _close_trade(
        self,
        trade: SimulatedTrade,
        exit_price: float,
        reason: str
    ):
        """Close a trade and update performance"""
        trade.exit_price = exit_price
        trade.exit_time = self.state.current_time
        trade.exit_reason = reason
        
        # Calculate PnL
        if trade.direction == 'long':
            trade.pnl = (exit_price - trade.entry_price) * trade.size
            trade.pnl_percent = (exit_price - trade.entry_price) / trade.entry_price
        else:
            trade.pnl = (trade.entry_price - exit_price) * trade.size
            trade.pnl_percent = (trade.entry_price - exit_price) / trade.entry_price
        
        # Update state
        self.state.available_capital += trade.pnl
        self.state.total_pnl += trade.pnl
        self.state.total_trades += 1
        
        if trade.pnl > 0:
            self.state.winning_trades += 1
        else:
            self.state.losing_trades += 1
        
        # Update drawdown
        if self.state.available_capital > self.state.peak_capital:
            self.state.peak_capital = self.state.available_capital
        
        drawdown = (self.state.peak_capital - self.state.available_capital) / self.state.peak_capital
        self.state.max_drawdown = max(self.state.max_drawdown, drawdown)
        
        # Move to closed trades
        self.state.open_trades.remove(trade)
        self.state.closed_trades.append(trade)
        
        logger.debug(f"Trade closed: {trade.trade_id} {reason} PnL: ${trade.pnl:,.2f}")
    
    def place_trade(
        self,
        symbol: str,
        direction: str,
        size: float,
        stop_loss: Optional[float] = None,
        take_profit: Optional[float] = None
    ) -> SimulatedTrade:
        """Place a new simulated trade"""
        if not self.state:
            raise RuntimeError("Simulation not started")
        
        trade_id = f"trade_{self.state.total_trades + len(self.state.open_trades)}_{datetime.utcnow().strftime('%H%M%S')}"
        
        trade = SimulatedTrade(
            trade_id=trade_id,
            timestamp=self.state.current_time,
            symbol=symbol,
            direction=direction,
            entry_price=self.state.price,
            size=size,
            stop_loss=stop_loss,
            take_profit=take_profit
        )
        
        self.state.open_trades.append(trade)
        
        logger.info(f"Trade placed: {direction} {size} @ ${self.state.price:.2f}")
        return trade
    
    def close_all_trades(self, reason: str = 'manual'):
        """Close all open trades"""
        for trade in self.state.open_trades[:]:
            self._close_trade(trade, self.state.price, reason)
    
    def get_performance_summary(self) -> Dict[str, Any]:
        """Get performance summary of simulation"""
        if not self.state:
            return {'error': 'Simulation not started'}
        
        total_trades = self.state.total_trades
        win_rate = self.state.winning_trades / total_trades if total_trades > 0 else 0
        
        pnls = [t.pnl for t in self.state.closed_trades if t.pnl is not None]
        avg_win = np.mean([p for p in pnls if p > 0]) if any(p > 0 for p in pnls) else 0
        avg_loss = np.mean([p for p in pnls if p < 0]) if any(p < 0 for p in pnls) else 0
        
        profit_factor = abs(sum(p for p in pnls if p > 0) / sum(p for p in pnls if p < 0)) if any(p < 0 for p in pnls) else float('inf')
        
        return {
            'total_trades': total_trades,
            'winning_trades': self.state.winning_trades,
            'losing_trades': self.state.losing_trades,
            'win_rate': win_rate,
            'total_pnl': self.state.total_pnl,
            'total_pnl_percent': self.state.total_pnl / self.initial_capital,
            'max_drawdown': self.state.max_drawdown,
            'avg_win': avg_win,
            'avg_loss': avg_loss,
            'profit_factor': profit_factor,
            'open_trades': len(self.state.open_trades),
            'current_capital': self.state.available_capital,
            'current_price': self.state.price,
            'current_regime': self.state.current_regime.value,
            'simulation_time': self.state.current_time.isoformat()
        }


class TradingSimulatorIntegration:
    """
    Integration between the Unified Financial Intelligence System and the market simulator.
    
    Enables safe self-testing:
    - Test new capabilities in simulation before live deployment
    - Validate strategy improvements under various market conditions
    - Measure performance of innovations in controlled scenarios
    - Provide realistic feedback to the evolution system
    """
    
    def __init__(
        self,
        unified_system: Any,  # UnifiedFinancialIntelligenceSystem
        initial_capital: float = 100000.0
    ):
        self.unified_system = unified_system
        self.simulator = MarketSimulator(initial_capital=initial_capital)
        
        # Scenario library
        self.scenarios: Dict[str, ScenarioConfig] = self._initialize_scenarios()
        
        # Test results storage
        self.test_results: List[Dict[str, Any]] = []
        
        logger.info("TradingSimulatorIntegration initialized")
    
    def _initialize_scenarios(self) -> Dict[str, ScenarioConfig]:
        """Initialize predefined test scenarios"""
        return {
            'bull_trend': ScenarioConfig(
                name='Bull Trend',
                description='Extended bull market with 20% trend',
                duration_days=30,
                regime_sequence=[
                    (MarketRegime.BULL_TREND, 30)
                ],
                initial_price=100.0,
                volatility_range=(0.01, 0.025),
                trend_magnitude=0.20
            ),
            
            'bear_trend': ScenarioConfig(
                name='Bear Trend',
                description='Extended bear market with -15% trend',
                duration_days=30,
                regime_sequence=[
                    (MarketRegime.BEAR_TREND, 30)
                ],
                initial_price=100.0,
                volatility_range=(0.015, 0.03),
                trend_magnitude=-0.15
            ),
            
            'market_crash': ScenarioConfig(
                name='Market Crash',
                description='Sudden crash followed by recovery',
                duration_days=20,
                regime_sequence=[
                    (MarketRegime.SIDEWAYS, 5),
                    (MarketRegime.CRASH, 3),
                    (MarketRegime.FLASH_CRASH, 1),
                    (MarketRegime.RECOVERY, 11)
                ],
                initial_price=100.0,
                volatility_range=(0.02, 0.10),
                trend_magnitude=-0.30,
                shock_events=[(5, 'crash_start', -0.10), (8, 'flash_crash', -0.15)]
            ),
            
            'high_volatility': ScenarioConfig(
                name='High Volatility',
                description='Extended high volatility period',
                duration_days=30,
                regime_sequence=[
                    (MarketRegime.HIGH_VOLATILITY, 30)
                ],
                initial_price=100.0,
                volatility_range=(0.03, 0.06),
                trend_magnitude=0.0
            ),
            
            'sideways_chop': ScenarioConfig(
                name='Sideways Chop',
                description='Range-bound market with mean reversion',
                duration_days=30,
                regime_sequence=[
                    (MarketRegime.SIDEWAYS, 15),
                    (MarketRegime.MEAN_REVERSION, 15)
                ],
                initial_price=100.0,
                volatility_range=(0.01, 0.02),
                trend_magnitude=0.0
            ),
            
            'bubble_pop': ScenarioConfig(
                name='Bubble and Pop',
                description='Bubble formation followed by crash',
                duration_days=45,
                regime_sequence=[
                    (MarketRegime.BULL_TREND, 10),
                    (MarketRegime.BUBBLE, 15),
                    (MarketRegime.CRASH, 5),
                    (MarketRegime.RECOVERY, 15)
                ],
                initial_price=100.0,
                volatility_range=(0.02, 0.08),
                trend_magnitude=0.40
            ),
            
            'mixed_regimes': ScenarioConfig(
                name='Mixed Regimes',
                description='Various market conditions over time',
                duration_days=60,
                regime_sequence=[
                    (MarketRegime.BULL_TREND, 10),
                    (MarketRegime.HIGH_VOLATILITY, 10),
                    (MarketRegime.SIDEWAYS, 10),
                    (MarketRegime.BEAR_TREND, 10),
                    (MarketRegime.MEAN_REVERSION, 10),
                    (MarketRegime.RECOVERY, 10)
                ],
                initial_price=100.0,
                volatility_range=(0.01, 0.05),
                trend_magnitude=0.10
            ),
            
            'stress_test': ScenarioConfig(
                name='Stress Test',
                description='Extreme conditions and rapid regime changes',
                duration_days=15,
                regime_sequence=[
                    (MarketRegime.HIGH_VOLATILITY, 3),
                    (MarketRegime.CRASH, 2),
                    (MarketRegime.RECOVERY, 3),
                    (MarketRegime.FLASH_CRASH, 1),
                    (MarketRegime.RECOVERY, 2),
                    (MarketRegime.HIGH_VOLATILITY, 4)
                ],
                initial_price=100.0,
                volatility_range=(0.04, 0.12),
                trend_magnitude=-0.15
            )
        }
    
    async def run_scenario(
        self,
        scenario_name: str,
        strategy: Optional[Callable] = None,
        record_decisions: bool = True
    ) -> Dict[str, Any]:
        """
        Run a complete scenario simulation
        
        Args:
            scenario_name: Name of predefined scenario
            strategy: Optional strategy function to use
            record_decisions: Whether to record decisions to memory
        """
        scenario = self.scenarios.get(scenario_name)
        if not scenario:
            raise ValueError(f"Unknown scenario: {scenario_name}")
        
        logger.info(f"Starting scenario: {scenario.name}")
        
        # Initialize simulation
        self.simulator.start_simulation(
            start_time=datetime.utcnow(),
            initial_price=scenario.initial_price,
            initial_regime=scenario.regime_sequence[0][0]
        )
        
        # Run through regime sequence
        total_hours = 0
        for regime, days in scenario.regime_sequence:
            hours = days * 24
            
            # Change regime
            self.simulator.change_regime(regime)
            
            # Run simulation for this regime period
            for hour in range(hours):
                self.simulator.step(1)
                total_hours += 1
                
                # Strategy decision point (every 4 hours)
                if hour % 4 == 0 and strategy:
                    decision = strategy(self.simulator.state)
                    if decision:
                        await self._execute_strategy_decision(decision, record_decisions)
                
                # Apply shock events
                if scenario.shock_events:
                    current_day = total_hours // 24
                    for shock_day, event_type, magnitude in scenario.shock_events:
                        if current_day == shock_day and hour == 0:
                            await self._apply_shock_event(event_type, magnitude)
        
        # Close all remaining trades
        self.simulator.close_all_trades('scenario_end')
        
        # Get results
        results = self.simulator.get_performance_summary()
        results['scenario_name'] = scenario.name
        results['scenario_description'] = scenario.description
        results['regimes_tested'] = [r[0].value for r in scenario.regime_sequence]
        
        # Store results
        self.test_results.append(results)
        
        # Report to unified system if available
        if self.unified_system:
            await self._report_results_to_system(results)
        
        logger.info(f"Scenario complete: PnL ${results['total_pnl']:,.2f} ({results['total_pnl_percent']:.1%})")
        
        return results
    
    async def _execute_strategy_decision(
        self,
        decision: Dict[str, Any],
        record: bool = True
    ):
        """Execute a strategy decision in the simulator"""
        action = decision.get('action')
        
        if action == 'enter_long':
            self.simulator.place_trade(
                symbol=decision.get('symbol', 'SIM'),
                direction='long',
                size=decision.get('size', 100),
                stop_loss=decision.get('stop_loss'),
                take_profit=decision.get('take_profit')
            )
        elif action == 'enter_short':
            self.simulator.place_trade(
                symbol=decision.get('symbol', 'SIM'),
                direction='short',
                size=decision.get('size', 100),
                stop_loss=decision.get('stop_loss'),
                take_profit=decision.get('take_profit')
            )
        elif action == 'close_all':
            self.simulator.close_all_trades('strategy_signal')
    
    async def _apply_shock_event(self, event_type: str, magnitude: float):
        """Apply a shock event to the simulation"""
        if event_type == 'crash_start':
            # Instant price drop
            current = self.simulator.state.price
            self.simulator.state.price = current * (1 + magnitude)
            logger.warning(f"Shock event: {event_type} {magnitude:.1%}")
        elif event_type == 'flash_crash':
            # More severe instant drop
            current = self.simulator.state.price
            self.simulator.state.price = current * (1 + magnitude)
            logger.warning(f"Shock event: {event_type} {magnitude:.1%}")
    
    async def _report_results_to_system(self, results: Dict[str, Any]):
        """Report simulation results to the unified system"""
        # This would integrate with the system's memory and evaluation
        pass
    
    def run_strategy_comparison(
        self,
        strategies: Dict[str, Callable],
        scenario_names: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Compare multiple strategies across scenarios
        
        Returns:
            Comparison results with rankings
        """
        scenario_names = scenario_names or list(self.scenarios.keys())
        
        results = {}
        
        for strategy_name, strategy in strategies.items():
            strategy_results = []
            
            for scenario_name in scenario_names:
                # Run scenario with this strategy
                result = asyncio.run(self.run_scenario(scenario_name, strategy))
                strategy_results.append(result)
            
            # Calculate aggregate metrics
            total_pnl = sum(r['total_pnl'] for r in strategy_results)
            avg_win_rate = np.mean([r['win_rate'] for r in strategy_results])
            avg_drawdown = np.mean([r['max_drawdown'] for r in strategy_results])
            
            results[strategy_name] = {
                'scenarios_run': len(scenario_names),
                'total_pnl': total_pnl,
                'avg_win_rate': avg_win_rate,
                'avg_max_drawdown': avg_drawdown,
                'scenario_results': strategy_results
            }
        
        # Rank strategies by total PnL
        ranked = sorted(results.items(), key=lambda x: x[1]['total_pnl'], reverse=True)
        
        return {
            'strategy_results': results,
            'rankings': [
                {'rank': i+1, 'strategy': name, 'total_pnl': data['total_pnl']}
                for i, (name, data) in enumerate(ranked)
            ]
        }
    
    def get_scenario_list(self) -> List[Dict[str, Any]]:
        """Get list of available scenarios"""
        return [
            {
                'name': s.name,
                'id': id,
                'description': s.description,
                'duration_days': s.duration_days,
                'regimes': [r[0].value for r in s.regime_sequence]
            }
            for id, s in self.scenarios.items()
        ]
    
    def get_test_history(self) -> List[Dict[str, Any]]:
        """Get history of all test runs"""
        return self.test_results


# Factory function
def create_trading_simulator_integration(
    unified_system: Optional[Any] = None,
    initial_capital: float = 100000.0
) -> TradingSimulatorIntegration:
    """Factory function to create trading simulator integration"""
    return TradingSimulatorIntegration(
        unified_system=unified_system,
        initial_capital=initial_capital
    )
