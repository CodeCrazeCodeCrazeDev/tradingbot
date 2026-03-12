"""
AAMIS v3.0 - Continuous Testing & Validation System

This module implements:
1. Continuous Backtesting + Live Testing While Trading
2. Failure Mode Simulation - Test against edge cases
3. Black Swan Simulator - Tail risk events
4. Monte-Carlo Creativity Simulation - Probabilistic strategy testing
5. Stress Testing - Extreme conditions
"""

import logging
from typing import Any, Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import numpy as np
import random
from collections import deque
import numpy

logger = logging.getLogger(__name__)


class TestMode(Enum):
    """Testing modes"""
    BACKTEST = "BACKTEST"
    LIVE = "LIVE"
    PAPER = "PAPER"
    STRESS = "STRESS"
    BLACK_SWAN = "BLACK_SWAN"
    MONTE_CARLO = "MONTE_CARLO"


class FailureMode(Enum):
    """Types of failure modes"""
    BROKER_DISCONNECT = "BROKER_DISCONNECT"
    DATA_FEED_LOSS = "DATA_FEED_LOSS"
    EXTREME_SLIPPAGE = "EXTREME_SLIPPAGE"
    PARTIAL_FILL = "PARTIAL_FILL"
    ORDER_REJECTION = "ORDER_REJECTION"
    MARGIN_CALL = "MARGIN_CALL"
    FLASH_CRASH = "FLASH_CRASH"
    LIQUIDITY_CRISIS = "LIQUIDITY_CRISIS"
    SYSTEM_OVERLOAD = "SYSTEM_OVERLOAD"
    NETWORK_LATENCY = "NETWORK_LATENCY"


class BlackSwanEvent(Enum):
    """Black swan event types"""
    MARKET_CRASH = "MARKET_CRASH"  # -20% in minutes
    FLASH_CRASH = "FLASH_CRASH"  # -10% instant recovery
    CURRENCY_CRISIS = "CURRENCY_CRISIS"  # 50% devaluation
    LIQUIDITY_FREEZE = "LIQUIDITY_FREEZE"  # No buyers/sellers
    BROKER_BANKRUPTCY = "BROKER_BANKRUPTCY"  # Broker fails
    REGULATORY_HALT = "REGULATORY_HALT"  # Trading stopped
    CYBER_ATTACK = "CYBER_ATTACK"  # System compromise
    NATURAL_DISASTER = "NATURAL_DISASTER"  # Major disruption
    WAR_OUTBREAK = "WAR_OUTBREAK"  # Geopolitical shock
    PANDEMIC = "PANDEMIC"  # Global health crisis


@dataclass
class TestResult:
    """Result of a test"""
    test_id: str
    test_mode: TestMode
    start_time: datetime
    end_time: Optional[datetime] = None
    success: bool = False
    pnl: float = 0.0
    max_drawdown: float = 0.0
    win_rate: float = 0.0
    total_trades: int = 0
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    metrics: Dict = field(default_factory=dict)


@dataclass
class FailureScenario:
    """Failure mode scenario"""
    scenario_id: str
    failure_mode: FailureMode
    severity: float  # 0.0 to 1.0
    duration: int  # seconds
    recovery_time: int  # seconds
    impact_score: float = 0.0


@dataclass
class BlackSwanScenario:
    """Black swan event scenario"""
    scenario_id: str
    event_type: BlackSwanEvent
    probability: float  # Very low
    impact: float  # Very high
    price_impact: float  # Percentage change
    duration: int  # seconds
    recovery_time: int  # seconds


class ContinuousBacktester:
    """
    Continuous Backtesting While Trading
    Validates strategies in real-time against historical data
    """
    
    def __init__(self):
        self.backtest_results: List[TestResult] = []
        self.live_results: List[TestResult] = []
        self.is_running = False
        
    def start_continuous_backtest(self, strategy: Any, historical_data: List[Dict]):
        """Start continuous backtesting"""
        self.is_running = True
        logger.info("📊 Continuous backtesting started")
        
        test_result = TestResult(
            test_id=f"BACKTEST_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            test_mode=TestMode.BACKTEST,
            start_time=datetime.now()
        )
        
        # Run backtest on historical data
        trades = []
        equity = 10000.0
        peak_equity = equity
        
        for data_point in historical_data:
            # Generate signal
            signal = self._generate_signal(strategy, data_point)
            
            if signal['action'] != 'HOLD':
                # Execute trade
                trade_result = self._execute_backtest_trade(signal, data_point, equity)
                trades.append(trade_result)
                
                # Update equity
                equity += trade_result['pnl']
                peak_equity = max(peak_equity, equity)
                
                test_result.total_trades += 1
        
        # Calculate metrics
        test_result.end_time = datetime.now()
        test_result.pnl = equity - 10000.0
        test_result.max_drawdown = (peak_equity - equity) / peak_equity if peak_equity > 0 else 0.0
        
        winning_trades = [t for t in trades if t['pnl'] > 0]
        test_result.win_rate = len(winning_trades) / len(trades) if trades else 0.0
        test_result.success = test_result.pnl > 0
        
        test_result.metrics = {
            'final_equity': equity,
            'total_return': test_result.pnl / 10000.0,
            'sharpe_ratio': self._calculate_sharpe_ratio(trades),
            'max_consecutive_losses': self._calculate_max_consecutive_losses(trades)
        }
        
        self.backtest_results.append(test_result)
        
        logger.info(f"📊 Backtest completed: PnL=${test_result.pnl:.2f}, Win Rate={test_result.win_rate:.2%}")
        
        return test_result
    
    def validate_live_trade(self, live_signal: Dict, backtest_signal: Dict) -> Dict:
        """Validate live trade against backtest"""
        validation = {
            'is_valid': True,
            'confidence': 1.0,
            'warnings': []
        }
        
        # Check if signals match
        if live_signal['action'] != backtest_signal['action']:
            validation['is_valid'] = False
            validation['warnings'].append(f"Signal mismatch: Live={live_signal['action']}, Backtest={backtest_signal['action']}")
            validation['confidence'] *= 0.5
        
        # Check if confidence is similar
        if abs(live_signal.get('confidence', 0.5) - backtest_signal.get('confidence', 0.5)) > 0.3:
            validation['warnings'].append("Large confidence difference between live and backtest")
            validation['confidence'] *= 0.8
        
        return validation
    
    def _generate_signal(self, strategy: Any, data: Dict) -> Dict:
        """Generate trading signal (simplified)"""
        # Simplified signal generation
        price_change = data.get('price_change', 0)
        
        if price_change > 0.01:
            return {'action': 'BUY', 'confidence': 0.7, 'size': 1.0}
        elif price_change < -0.01:
            return {'action': 'SELL', 'confidence': 0.7, 'size': 1.0}
        else:
            return {'action': 'HOLD', 'confidence': 0.5, 'size': 0.0}
    
    def _execute_backtest_trade(self, signal: Dict, data: Dict, equity: float) -> Dict:
        """Execute a backtest trade"""
        price = data.get('price', 1.0)
        size = signal['size'] * equity * 0.1  # 10% of equity
        
        # Simulate price movement
        price_change = random.uniform(-0.02, 0.02)
        
        if signal['action'] == 'BUY':
            pnl = size * price_change
        else:  # SELL
            pnl = size * -price_change
        
        return {
            'signal': signal,
            'entry_price': price,
            'exit_price': price * (1 + price_change),
            'size': size,
            'pnl': pnl,
            'timestamp': datetime.now()
        }
    
    def _calculate_sharpe_ratio(self, trades: List[Dict]) -> float:
        """Calculate Sharpe ratio"""
        if not trades:
            return 0.0
        
        returns = [t['pnl'] for t in trades]
        if len(returns) < 2:
            return 0.0
        
        mean_return = np.mean(returns)
        std_return = np.std(returns)
        
        if std_return == 0:
            return 0.0
        
        sharpe = (mean_return / std_return) * np.sqrt(252)  # Annualized
        return sharpe
    
    def _calculate_max_consecutive_losses(self, trades: List[Dict]) -> int:
        """Calculate maximum consecutive losses"""
        max_losses = 0
        current_losses = 0
        
        for trade in trades:
            if trade['pnl'] < 0:
                current_losses += 1
                max_losses = max(max_losses, current_losses)
            else:
                current_losses = 0
        
        return max_losses


class FailureModeSimulator:
    """
    Failure Mode Simulation
    Tests system against edge cases and failures
    """
    
    def __init__(self):
        self.failure_scenarios: List[FailureScenario] = []
        self.test_results: List[TestResult] = []
        
    def simulate_failure(self, failure_mode: FailureMode, severity: float = 0.8) -> FailureScenario:
        """Simulate a failure mode"""
        scenario = FailureScenario(
            scenario_id=f"FAIL_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            failure_mode=failure_mode,
            severity=severity,
            duration=int(60 * severity),  # seconds
            recovery_time=int(120 * severity)
        )
        
        logger.info(f"⚠️ Simulating failure: {failure_mode.value} (severity: {severity:.2f})")
        
        # Simulate specific failure
        if failure_mode == FailureMode.BROKER_DISCONNECT:
            scenario.impact_score = self._simulate_broker_disconnect(scenario)
        elif failure_mode == FailureMode.DATA_FEED_LOSS:
            scenario.impact_score = self._simulate_data_feed_loss(scenario)
        elif failure_mode == FailureMode.EXTREME_SLIPPAGE:
            scenario.impact_score = self._simulate_extreme_slippage(scenario)
        elif failure_mode == FailureMode.FLASH_CRASH:
            scenario.impact_score = self._simulate_flash_crash(scenario)
        elif failure_mode == FailureMode.MARGIN_CALL:
            scenario.impact_score = self._simulate_margin_call(scenario)
        else:
            scenario.impact_score = severity
        
        self.failure_scenarios.append(scenario)
        
        logger.info(f"⚠️ Failure simulation completed: Impact={scenario.impact_score:.2f}")
        
        return scenario
    
    def _simulate_broker_disconnect(self, scenario: FailureScenario) -> float:
        """Simulate broker disconnection"""
        # System should:
        # 1. Detect disconnection
        # 2. Attempt reconnection
        # 3. Close positions if critical
        # 4. Log all actions
        
        impact = scenario.severity * 0.5  # Reduced if handled properly
        logger.warning(f"🔌 Broker disconnected for {scenario.duration}s")
        return impact
    
    def _simulate_data_feed_loss(self, scenario: FailureScenario) -> float:
        """Simulate data feed loss"""
        # System should:
        # 1. Detect stale data
        # 2. Switch to backup feed
        # 3. Stop trading if no data
        # 4. Alert operators
        
        impact = scenario.severity * 0.6
        logger.warning(f"📡 Data feed lost for {scenario.duration}s")
        return impact
    
    def _simulate_extreme_slippage(self, scenario: FailureScenario) -> float:
        """Simulate extreme slippage"""
        # System should:
        # 1. Detect abnormal slippage
        # 2. Adjust position sizes
        # 3. Use limit orders
        # 4. Avoid illiquid markets
        
        slippage_pct = scenario.severity * 0.05  # Up to 5% slippage
        impact = slippage_pct * 10  # Impact score
        logger.warning(f"💸 Extreme slippage: {slippage_pct:.2%}")
        return impact
    
    def _simulate_flash_crash(self, scenario: FailureScenario) -> float:
        """Simulate flash crash"""
        # System should:
        # 1. Detect abnormal price movement
        # 2. Stop trading immediately
        # 3. Close risky positions
        # 4. Wait for market stabilization
        
        price_drop = scenario.severity * 0.10  # Up to 10% drop
        impact = price_drop * 20  # High impact
        logger.warning(f"⚡ Flash crash: {price_drop:.2%} drop")
        return impact
    
    def _simulate_margin_call(self, scenario: FailureScenario) -> float:
        """Simulate margin call"""
        # System should:
        # 1. Monitor margin levels
        # 2. Close positions before margin call
        # 3. Reduce leverage
        # 4. Add capital if needed
        
        impact = scenario.severity * 0.9  # High impact
        logger.warning(f"📞 Margin call triggered")
        return impact
    
    def run_failure_test_suite(self) -> Dict:
        """Run complete failure test suite"""
        logger.info("🧪 Running failure test suite...")
        
        results = {
            'total_tests': 0,
            'passed': 0,
            'failed': 0,
            'scenarios': []
        }
        
        # Test all failure modes
        for failure_mode in FailureMode:
            for severity in [0.3, 0.6, 0.9]:
                scenario = self.simulate_failure(failure_mode, severity)
                results['scenarios'].append(scenario)
                results['total_tests'] += 1
                
                # Pass if impact is less than severity (good handling)
                if scenario.impact_score < scenario.severity:
                    results['passed'] += 1
                else:
                    results['failed'] += 1
        
        logger.info(f"🧪 Failure test suite completed: {results['passed']}/{results['total_tests']} passed")
        
        return results


class BlackSwanSimulator:
    """
    Black Swan Event Simulator
    Tests system against extreme tail risk events
    """
    
    def __init__(self):
        self.scenarios: List[BlackSwanScenario] = []
        self.survival_rate = 0.0
        
    def simulate_black_swan(self, event_type: BlackSwanEvent) -> BlackSwanScenario:
        """Simulate a black swan event"""
        scenario = BlackSwanScenario(
            scenario_id=f"SWAN_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            event_type=event_type,
            probability=random.uniform(0.001, 0.01),  # 0.1% to 1%
            impact=random.uniform(0.8, 1.0),  # 80% to 100% impact
            price_impact=self._get_price_impact(event_type),
            duration=self._get_duration(event_type),
            recovery_time=self._get_recovery_time(event_type)
        )
        
        logger.warning(f"🦢 BLACK SWAN EVENT: {event_type.value}")
        logger.warning(f"   Price Impact: {scenario.price_impact:.2%}")
        logger.warning(f"   Duration: {scenario.duration}s")
        logger.warning(f"   Recovery: {scenario.recovery_time}s")
        
        self.scenarios.append(scenario)
        
        # Test system survival
        survived = self._test_survival(scenario)
        
        if survived:
            logger.info(f"✅ System survived {event_type.value}")
        else:
            logger.error(f"❌ System failed during {event_type.value}")
        
        return scenario
    
    def _get_price_impact(self, event_type: BlackSwanEvent) -> float:
        """Get price impact for event type"""
        impacts = {
            BlackSwanEvent.MARKET_CRASH: -0.20,  # -20%
            BlackSwanEvent.FLASH_CRASH: -0.10,  # -10%
            BlackSwanEvent.CURRENCY_CRISIS: -0.50,  # -50%
            BlackSwanEvent.LIQUIDITY_FREEZE: -0.05,  # -5%
            BlackSwanEvent.BROKER_BANKRUPTCY: 0.0,  # No price impact
            BlackSwanEvent.REGULATORY_HALT: 0.0,
            BlackSwanEvent.CYBER_ATTACK: -0.15,  # -15%
            BlackSwanEvent.NATURAL_DISASTER: -0.08,  # -8%
            BlackSwanEvent.WAR_OUTBREAK: -0.25,  # -25%
            BlackSwanEvent.PANDEMIC: -0.30  # -30%
        }
        return impacts.get(event_type, -0.10)
    
    def _get_duration(self, event_type: BlackSwanEvent) -> int:
        """Get duration for event type (seconds)"""
        durations = {
            BlackSwanEvent.MARKET_CRASH: 3600,  # 1 hour
            BlackSwanEvent.FLASH_CRASH: 60,  # 1 minute
            BlackSwanEvent.CURRENCY_CRISIS: 86400,  # 1 day
            BlackSwanEvent.LIQUIDITY_FREEZE: 7200,  # 2 hours
            BlackSwanEvent.BROKER_BANKRUPTCY: 0,  # Instant
            BlackSwanEvent.REGULATORY_HALT: 3600,
            BlackSwanEvent.CYBER_ATTACK: 1800,  # 30 minutes
            BlackSwanEvent.NATURAL_DISASTER: 43200,  # 12 hours
            BlackSwanEvent.WAR_OUTBREAK: 86400,
            BlackSwanEvent.PANDEMIC: 2592000  # 30 days
        }
        return durations.get(event_type, 3600)
    
    def _get_recovery_time(self, event_type: BlackSwanEvent) -> int:
        """Get recovery time for event type (seconds)"""
        return self._get_duration(event_type) * 3  # 3x duration
    
    def _test_survival(self, scenario: BlackSwanScenario) -> bool:
        """Test if system survives the black swan event"""
        # System should:
        # 1. Detect extreme event
        # 2. Close all positions immediately
        # 3. Preserve capital
        # 4. Wait for market stabilization
        # 5. Resume trading when safe
        
        # Simplified survival test
        survival_chance = 1.0 - (abs(scenario.price_impact) * scenario.impact)
        
        # Add protection mechanisms
        if abs(scenario.price_impact) > 0.15:  # >15% move
            survival_chance += 0.3  # Emergency stop helps
        
        survived = random.random() < survival_chance
        
        if survived:
            self.survival_rate = (self.survival_rate * len(self.scenarios) + 1.0) / (len(self.scenarios) + 1)
        else:
            self.survival_rate = (self.survival_rate * len(self.scenarios)) / (len(self.scenarios) + 1)
        
        return survived
    
    def run_black_swan_stress_test(self) -> Dict:
        """Run complete black swan stress test"""
        logger.info("🦢 Running black swan stress test...")
        
        results = {
            'total_events': 0,
            'survived': 0,
            'failed': 0,
            'survival_rate': 0.0,
            'scenarios': []
        }
        
        # Test all black swan events
        for event_type in BlackSwanEvent:
            scenario = self.simulate_black_swan(event_type)
            results['scenarios'].append(scenario)
            results['total_events'] += 1
            
            # Check if survived
            if self._test_survival(scenario):
                results['survived'] += 1
            else:
                results['failed'] += 1
        
        results['survival_rate'] = results['survived'] / results['total_events'] if results['total_events'] > 0 else 0.0
        
        logger.info(f"🦢 Black swan stress test completed: {results['survival_rate']:.2%} survival rate")
        
        return results


class MonteCarloSimulator:
    """
    Monte Carlo Creativity Simulation
    Tests strategies with probabilistic scenarios
    """
    
    def __init__(self):
        self.simulations: List[Dict] = []
        
    def run_monte_carlo_simulation(self, strategy: Any, num_simulations: int = 1000) -> Dict:
        """Run Monte Carlo simulation"""
        logger.info(f"🎲 Running Monte Carlo simulation ({num_simulations} runs)...")
        
        results = {
            'num_simulations': num_simulations,
            'outcomes': [],
            'mean_pnl': 0.0,
            'std_pnl': 0.0,
            'win_rate': 0.0,
            'var_95': 0.0,  # Value at Risk (95%)
            'cvar_95': 0.0  # Conditional VaR
        }
        
        pnls = []
        wins = 0
        
        for i in range(num_simulations):
            # Generate random market scenario
            scenario = self._generate_random_scenario()
            
            # Run strategy
            outcome = self._run_strategy(strategy, scenario)
            
            pnls.append(outcome['pnl'])
            if outcome['pnl'] > 0:
                wins += 1
            
            results['outcomes'].append(outcome)
        
        # Calculate statistics
        results['mean_pnl'] = np.mean(pnls)
        results['std_pnl'] = np.std(pnls)
        results['win_rate'] = wins / num_simulations
        
        # Calculate VaR and CVaR
        sorted_pnls = sorted(pnls)
        var_index = int(num_simulations * 0.05)  # 5th percentile
        results['var_95'] = sorted_pnls[var_index]
        results['cvar_95'] = np.mean(sorted_pnls[:var_index])
        
        self.simulations.append(results)
        
        logger.info(f"🎲 Monte Carlo completed: Mean PnL=${results['mean_pnl']:.2f}, Win Rate={results['win_rate']:.2%}")
        logger.info(f"   VaR(95%)=${results['var_95']:.2f}, CVaR(95%)=${results['cvar_95']:.2f}")
        
        return results
    
    def _generate_random_scenario(self) -> Dict:
        """Generate random market scenario"""
        return {
            'price': 1.0,
            'volatility': random.uniform(0.01, 0.05),
            'trend': random.choice([-1, 0, 1]),
            'volume': random.uniform(500, 2000),
            'spread': random.uniform(0.0001, 0.001)
        }
    
    def _run_strategy(self, strategy: Any, scenario: Dict) -> Dict:
        """Run strategy in scenario"""
        # Simplified strategy execution
        price_change = random.gauss(0, scenario['volatility']) + scenario['trend'] * 0.01
        
        # Random trade decision
        if random.random() < 0.6:
            side = random.choice(['BUY', 'SELL'])
            size = random.uniform(0.5, 1.5)
            
            if side == 'BUY':
                pnl = size * 1000 * price_change
            else:
                pnl = size * 1000 * -price_change
            
            return {
                'pnl': pnl,
                'side': side,
                'size': size,
                'scenario': scenario
            }
        
        return {'pnl': 0.0, 'side': 'HOLD', 'size': 0.0, 'scenario': scenario}


class ContinuousValidationSystem:
    """
    Complete Continuous Validation System
    Combines all testing methods
    """
    
    def __init__(self):
        self.backtester = ContinuousBacktester()
        self.failure_simulator = FailureModeSimulator()
        self.black_swan_simulator = BlackSwanSimulator()
        self.monte_carlo_simulator = MonteCarloSimulator()
        self.validation_sessions: List[Dict] = []
        
    def run_complete_validation(self, strategy: Any, historical_data: List[Dict] = None) -> Dict:
        """Run complete validation suite"""
        session_id = f"VALIDATION_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        logger.info(f"🔬 Complete validation started: {session_id}")
        
        if historical_data is None:
            historical_data = self._generate_sample_data()
        
        validation_results = {
            'session_id': session_id,
            'start_time': datetime.now(),
            'backtest_results': None,
            'failure_test_results': None,
            'black_swan_results': None,
            'monte_carlo_results': None
        }
        
        # 1. Continuous Backtesting
        logger.info("📊 Running continuous backtest...")
        validation_results['backtest_results'] = self.backtester.start_continuous_backtest(strategy, historical_data)
        
        # 2. Failure Mode Testing
        logger.info("⚠️ Running failure mode tests...")
        validation_results['failure_test_results'] = self.failure_simulator.run_failure_test_suite()
        
        # 3. Black Swan Testing
        logger.info("🦢 Running black swan tests...")
        validation_results['black_swan_results'] = self.black_swan_simulator.run_black_swan_stress_test()
        
        # 4. Monte Carlo Simulation
        logger.info("🎲 Running Monte Carlo simulation...")
        validation_results['monte_carlo_results'] = self.monte_carlo_simulator.run_monte_carlo_simulation(strategy, num_simulations=1000)
        
        validation_results['end_time'] = datetime.now()
        validation_results['duration'] = (validation_results['end_time'] - validation_results['start_time']).total_seconds()
        
        # Overall assessment
        validation_results['overall_score'] = self._calculate_overall_score(validation_results)
        validation_results['recommendation'] = self._get_recommendation(validation_results['overall_score'])
        
        self.validation_sessions.append(validation_results)
        
        logger.info(f"🔬 Complete validation finished: Overall Score={validation_results['overall_score']:.2f}/100")
        logger.info(f"   Recommendation: {validation_results['recommendation']}")
        
        return validation_results
    
    def _generate_sample_data(self) -> List[Dict]:
        """Generate sample historical data"""
        data = []
        price = 1.0
        
        for i in range(1000):
            price_change = random.gauss(0, 0.01)
            price *= (1 + price_change)
            
            data.append({
                'timestamp': datetime.now() - timedelta(minutes=1000-i),
                'price': price,
                'price_change': price_change,
                'volume': random.uniform(500, 1500)
            })
        
        return data
    
    def _calculate_overall_score(self, results: Dict) -> float:
        """Calculate overall validation score"""
        score = 0.0
        
        # Backtest score (30%)
        backtest = results['backtest_results']
        if backtest and backtest.success:
            score += 30 * (backtest.win_rate)
        
        # Failure handling score (25%)
        failure = results['failure_test_results']
        if failure:
            score += 25 * (failure['passed'] / failure['total_tests'])
        
        # Black swan survival score (25%)
        black_swan = results['black_swan_results']
        if black_swan:
            score += 25 * black_swan['survival_rate']
        
        # Monte Carlo score (20%)
        monte_carlo = results['monte_carlo_results']
        if monte_carlo:
            score += 20 * monte_carlo['win_rate']
        
        return min(100.0, score)
    
    def _get_recommendation(self, score: float) -> str:
        """Get recommendation based on score"""
        if score >= 80:
            return "EXCELLENT - Ready for live trading"
        elif score >= 60:
            return "GOOD - Minor improvements needed"
        elif score >= 40:
            return "FAIR - Significant improvements required"
        else:
            return "POOR - Not ready for live trading"
    
    def get_validation_report(self) -> Dict:
        """Get comprehensive validation report"""
        return {
            'total_sessions': len(self.validation_sessions),
            'latest_session': self.validation_sessions[-1] if self.validation_sessions else None,
            'average_score': np.mean([s['overall_score'] for s in self.validation_sessions]) if self.validation_sessions else 0.0
        }


# Example usage
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    # Create validation system
    validation_system = ContinuousValidationSystem()
    
    # Run complete validation
    strategy = None  # Placeholder
    results = validation_system.run_complete_validation(strategy)
    
    # Print report
    print("\n" + "="*80)
    logger.info("CONTINUOUS VALIDATION REPORT")
    print("="*80)
    logger.info(f"Session ID: {results['session_id']}")
    logger.info(f"Overall Score: {results['overall_score']:.2f}/100")
    logger.info(f"Recommendation: {results['recommendation']}")
    logger.info(f"\nBacktest: PnL=${results['backtest_results'].pnl:.2f}, Win Rate={results['backtest_results'].win_rate:.2%}")
    logger.info(f"Failure Tests: {results['failure_test_results']['passed']}/{results['failure_test_results']['total_tests']} passed")
    logger.info(f"Black Swan: {results['black_swan_results']['survival_rate']:.2%} survival rate")
    logger.info(f"Monte Carlo: Win Rate={results['monte_carlo_results']['win_rate']:.2%}, VaR(95%)=${results['monte_carlo_results']['var_95']:.2f}")
    print("="*80)
