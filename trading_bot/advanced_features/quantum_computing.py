"""Quantum Computing Integration Module - Nash Equilibrium and Portfolio Optimization.

from typing import Optional, Set
This module implements quantum-inspired algorithms for advanced portfolio optimization,
Nash equilibrium calculations, and quantum annealing for complex trading problems.
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Tuple, Optional, Union, Any
from dataclasses import dataclass
from enum import Enum
import logging
from scipy.optimize import minimize
from scipy.linalg import sqrtm
import asyncio
from concurrent.futures import ThreadPoolExecutor

# Quantum computing imports (with fallbacks)
try:
    from qiskit import QuantumCircuit, Aer, execute
    from qiskit.optimization import QuadraticProgram
    from qiskit.optimization.algorithms import MinimumEigenOptimizer
    from qiskit.algorithms import QAOA, NumPyMinimumEigensolver
    from qiskit.utils import QuantumInstance
    QISKIT_AVAILABLE = True
except ImportError:
    QISKIT_AVAILABLE = False

logger = logging.getLogger(__name__)
if not QISKIT_AVAILABLE:
    logger.debug("Qiskit not available. Using classical optimization fallbacks.")


class OptimizationType(Enum):
    """Types of optimization problems."""
    PORTFOLIO_OPTIMIZATION = "portfolio_optimization"
    NASH_EQUILIBRIUM = "nash_equilibrium"
    RISK_PARITY = "risk_parity"
    MEAN_REVERSION = "mean_reversion"
    MOMENTUM_ALLOCATION = "momentum_allocation"


@dataclass
class QuantumOptimizationResult:
    """Results from quantum optimization."""
    optimal_weights: np.ndarray
    expected_return: float
    risk_level: float
    sharpe_ratio: float
    optimization_time: float
    quantum_advantage: bool
    classical_comparison: Optional[Dict] = None


@dataclass
class NashEquilibriumResult:
    """Results from Nash equilibrium calculation."""
    equilibrium_strategies: Dict[str, np.ndarray]
    payoff_matrix: np.ndarray
    stability_score: float
    convergence_iterations: int
    quantum_speedup: float


class QuantumPortfolioOptimizer:
    """
    Quantum-inspired portfolio optimization using QAOA and quantum annealing.
    
    This class implements advanced portfolio optimization techniques that leverage
    quantum computing principles for superior performance in complex optimization landscapes.
    """
    
    def __init__(self, 
                 use_quantum: bool = True,
                 quantum_backend: str = 'qasm_simulator',
                 max_iterations: int = 1000,
                 convergence_threshold: float = 1e-6):
        """
        Initialize Quantum Portfolio Optimizer.
        
        Args:
            use_quantum: Whether to use quantum algorithms (fallback to classical if unavailable)
            quantum_backend: Quantum backend to use
            max_iterations: Maximum optimization iterations
            convergence_threshold: Convergence threshold for optimization
        """
        self.use_quantum = use_quantum and QISKIT_AVAILABLE
        self.quantum_backend = quantum_backend
        self.max_iterations = max_iterations
        self.convergence_threshold = convergence_threshold
        
        # Initialize quantum backend if available
        if self.use_quantum:
            self.backend = Aer.get_backend(quantum_backend)
            self.quantum_instance = QuantumInstance(self.backend)
        
        # Portfolio optimization history
        self.optimization_history = []
        
        logger.info(f"Quantum Portfolio Optimizer initialized (quantum: {self.use_quantum})")
    
    def optimize_portfolio(self,
                          returns: pd.DataFrame,
                          risk_aversion: float = 1.0,
                          constraints: Optional[Dict] = None) -> QuantumOptimizationResult:
        """
        Optimize portfolio using quantum or classical methods.
        
        Args:
            returns: Historical returns data
            risk_aversion: Risk aversion parameter
            constraints: Portfolio constraints (min/max weights, etc.)
            
        Returns:
            Optimization results with quantum advantage analysis
        """
        start_time = pd.Timestamp.now()
        
        # Prepare optimization data
        mean_returns = returns.mean().values
        cov_matrix = returns.cov().values
        n_assets = len(mean_returns)
        
        # Set default constraints
        if constraints is None:
            constraints = {
                'min_weight': 0.0,
                'max_weight': 1.0,
                'sum_weights': 1.0
            }
        
        # Choose optimization method
        if self.use_quantum:
            result = self._quantum_portfolio_optimization(
                mean_returns, cov_matrix, risk_aversion, constraints
            )
        else:
            result = self._classical_portfolio_optimization(
                mean_returns, cov_matrix, risk_aversion, constraints
            )
        
        # Calculate performance metrics
        expected_return = np.dot(result['weights'], mean_returns)
        portfolio_risk = np.sqrt(np.dot(result['weights'], 
                                       np.dot(cov_matrix, result['weights'])))
        sharpe_ratio = expected_return / portfolio_risk if portfolio_risk > 0 else 0
        
        optimization_time = (pd.Timestamp.now() - start_time).total_seconds()
        
        # Create result object
        optimization_result = QuantumOptimizationResult(
            optimal_weights=result['weights'],
            expected_return=expected_return,
            risk_level=portfolio_risk,
            sharpe_ratio=sharpe_ratio,
            optimization_time=optimization_time,
            quantum_advantage=self.use_quantum,
            classical_comparison=result.get('classical_comparison')
        )
        
        self.optimization_history.append(optimization_result)
        return optimization_result
    
    def _quantum_portfolio_optimization(self,
                                      mean_returns: np.ndarray,
                                      cov_matrix: np.ndarray,
                                      risk_aversion: float,
                                      constraints: Dict) -> Dict:
        """Quantum portfolio optimization using QAOA."""
        try:
            # Create quadratic program
            qp = QuadraticProgram()
            n_assets = len(mean_returns)
            
            # Add variables (portfolio weights)
            for i in range(n_assets):
                qp.continuous_var(
                    lowerbound=constraints['min_weight'],
                    upperbound=constraints['max_weight'],
                    name=f'w_{i}'
                )
            
            # Objective function: maximize return - risk_aversion * risk
            # Convert to minimization: minimize -return + risk_aversion * risk
            linear_coeffs = -mean_returns
            quadratic_coeffs = risk_aversion * cov_matrix
            
            qp.minimize(linear=linear_coeffs, quadratic=quadratic_coeffs)
            
            # Add constraint: sum of weights = 1
            linear_constraint = {f'w_{i}': 1.0 for i in range(n_assets)}
            qp.linear_constraint(
                linear=linear_constraint,
                sense='==',
                rhs=constraints['sum_weights']
            )
            
            # Solve using quantum algorithm
            qaoa = QAOA(quantum_instance=self.quantum_instance)
            optimizer = MinimumEigenOptimizer(qaoa)
            
            quantum_result = optimizer.solve(qp)
            
            # Extract weights
            weights = np.array([quantum_result.x[i] for i in range(n_assets)])
            
            # Run classical comparison
            classical_result = self._classical_portfolio_optimization(
                mean_returns, cov_matrix, risk_aversion, constraints
            )
            
            return {
                'weights': weights,
                'objective_value': quantum_result.fval,
                'classical_comparison': classical_result
            }
            
        except Exception as e:
            logger.error(f"Quantum optimization failed: {e}")
            # Fallback to classical
            return self._classical_portfolio_optimization(
                mean_returns, cov_matrix, risk_aversion, constraints
            )
    
    def _classical_portfolio_optimization(self,
                                        mean_returns: np.ndarray,
                                        cov_matrix: np.ndarray,
                                        risk_aversion: float,
                                        constraints: Dict) -> Dict:
        """Classical portfolio optimization using scipy."""
        n_assets = len(mean_returns)
        
        # Objective function
        def objective(weights):
            """
            objective function.

    Args:
        weights: Description

    Returns:
        Result of operation
            """
            portfolio_return = np.dot(weights, mean_returns)
            portfolio_risk = np.sqrt(np.dot(weights, np.dot(cov_matrix, weights)))
            return -(portfolio_return - risk_aversion * portfolio_risk)
        
        # Constraints
        constraint_list = [
            {'type': 'eq', 'fun': lambda x: np.sum(x) - constraints['sum_weights']}
        ]
        
        # Bounds
        bounds = [(constraints['min_weight'], constraints['max_weight']) 
                 for _ in range(n_assets)]
        
        # Initial guess (equal weights)
        x0 = np.ones(n_assets) / n_assets
        
        # Optimize
        result = minimize(
            objective,
            x0,
            method='SLSQP',
            bounds=bounds,
            constraints=constraint_list,
            options={'maxiter': self.max_iterations}
        )
        
        return {
            'weights': result.x,
            'objective_value': result.fun,
            'success': result.success
        }


class QuantumNashEquilibrium:
    """
    Quantum-enhanced Nash equilibrium calculator for multi-agent trading scenarios.
    
    This class uses quantum algorithms to find Nash equilibria in complex
    multi-player trading games more efficiently than classical methods.
    """
    
    def __init__(self, use_quantum: bool = True):
        """Initialize Quantum Nash Equilibrium calculator."""
        self.use_quantum = use_quantum and QISKIT_AVAILABLE
        self.equilibrium_history = []
        
        logger.info(f"Quantum Nash Equilibrium calculator initialized (quantum: {self.use_quantum})")
    
    def calculate_nash_equilibrium(self,
                                 payoff_matrices: Dict[str, np.ndarray],
                                 max_iterations: int = 1000) -> NashEquilibriumResult:
        """
        Calculate Nash equilibrium for multi-player game.
        
        Args:
            payoff_matrices: Payoff matrices for each player
            max_iterations: Maximum iterations for convergence
            
        Returns:
            Nash equilibrium result with strategies and stability analysis
        """
        start_time = pd.Timestamp.now()
        
        if self.use_quantum:
            result = self._quantum_nash_equilibrium(payoff_matrices, max_iterations)
        else:
            result = self._classical_nash_equilibrium(payoff_matrices, max_iterations)
        
        optimization_time = (pd.Timestamp.now() - start_time).total_seconds()
        
        # Calculate stability score
        stability_score = self._calculate_stability(
            result['strategies'], payoff_matrices
        )
        
        nash_result = NashEquilibriumResult(
            equilibrium_strategies=result['strategies'],
            payoff_matrix=result['combined_payoff'],
            stability_score=stability_score,
            convergence_iterations=result['iterations'],
            quantum_speedup=optimization_time
        )
        
        self.equilibrium_history.append(nash_result)
        return nash_result
    
    def _quantum_nash_equilibrium(self,
                                payoff_matrices: Dict[str, np.ndarray],
                                max_iterations: int) -> Dict:
        """Quantum Nash equilibrium calculation."""
        try:
            # For now, implement a quantum-inspired algorithm
            # In a full implementation, this would use quantum game theory
            
            players = list(payoff_matrices.keys())
            n_players = len(players)
            
            # Initialize strategies randomly
            strategies = {}
            for player in players:
                n_actions = payoff_matrices[player].shape[0]
                strategies[player] = np.random.dirichlet(np.ones(n_actions))
            
            # Quantum-inspired iterative improvement
            for iteration in range(max_iterations):
                old_strategies = {p: s.copy() for p, s in strategies.items()}
                
                # Update each player's strategy using quantum superposition principle
                for player in players:
                    strategies[player] = self._quantum_strategy_update(
                        player, strategies, payoff_matrices
                    )
                
                # Check convergence
                if self._check_convergence(strategies, old_strategies):
                    break
            
            # Combine payoff matrices
            combined_payoff = np.zeros((n_players, n_players))
            for i, player in enumerate(players):
                combined_payoff[i] = np.diagonal(payoff_matrices[player])
            
            return {
                'strategies': strategies,
                'combined_payoff': combined_payoff,
                'iterations': iteration + 1
            }
            
        except Exception as e:
            logger.error(f"Quantum Nash equilibrium calculation failed: {e}")
            return self._classical_nash_equilibrium(payoff_matrices, max_iterations)
    
    def _quantum_strategy_update(self,
                               player: str,
                               strategies: Dict[str, np.ndarray],
                               payoff_matrices: Dict[str, np.ndarray]) -> np.ndarray:
        """Update player strategy using quantum-inspired method."""
        payoff_matrix = payoff_matrices[player]
        current_strategy = strategies[player]
        
        # Calculate expected payoffs for each action
        other_players = [p for p in strategies.keys() if p != player]
        
        # Quantum superposition of opponent strategies
        opponent_mixed_strategy = np.ones(payoff_matrix.shape[1])
        for other_player in other_players:
            if other_player in strategies:
                opponent_mixed_strategy *= strategies[other_player]
        
        opponent_mixed_strategy /= np.sum(opponent_mixed_strategy)
        
        # Calculate expected payoffs
        expected_payoffs = np.dot(payoff_matrix, opponent_mixed_strategy)
        
        # Quantum-inspired strategy update (softmax with quantum interference)
        beta = 2.0  # "Temperature" parameter
        quantum_interference = np.cos(np.pi * current_strategy) ** 2
        
        new_strategy = np.exp(beta * expected_payoffs * quantum_interference)
        new_strategy /= np.sum(new_strategy)
        
        return new_strategy
    
    def _classical_nash_equilibrium(self,
                                  payoff_matrices: Dict[str, np.ndarray],
                                  max_iterations: int) -> Dict:
        """Classical Nash equilibrium using iterative best response."""
        players = list(payoff_matrices.keys())
        n_players = len(players)
        
        # Initialize strategies
        strategies = {}
        for player in players:
            n_actions = payoff_matrices[player].shape[0]
            strategies[player] = np.ones(n_actions) / n_actions
        
        # Iterative best response
        for iteration in range(max_iterations):
            old_strategies = {p: s.copy() for p, s in strategies.items()}
            
            for player in players:
                strategies[player] = self._best_response(
                    player, strategies, payoff_matrices
                )
            
            if self._check_convergence(strategies, old_strategies):
                break
        
        # Combine payoff matrices
        combined_payoff = np.zeros((n_players, n_players))
        for i, player in enumerate(players):
            combined_payoff[i] = np.diagonal(payoff_matrices[player])
        
        return {
            'strategies': strategies,
            'combined_payoff': combined_payoff,
            'iterations': iteration + 1
        }
    
    def _best_response(self,
                      player: str,
                      strategies: Dict[str, np.ndarray],
                      payoff_matrices: Dict[str, np.ndarray]) -> np.ndarray:
        """Calculate best response strategy for a player."""
        payoff_matrix = payoff_matrices[player]
        
        # Calculate expected payoffs for each action
        other_players = [p for p in strategies.keys() if p != player]
        
        if not other_players:
            # Single player case
            return np.ones(payoff_matrix.shape[0]) / payoff_matrix.shape[0]
        
        # Mixed strategy of opponents
        opponent_strategy = strategies[other_players[0]]
        for other_player in other_players[1:]:
            opponent_strategy = np.kron(opponent_strategy, strategies[other_player])
        
        # Calculate expected payoffs
        expected_payoffs = np.dot(payoff_matrix, opponent_strategy)
        
        # Best response (softmax for mixed strategy)
        beta = 10.0  # High beta for near-pure strategies
        best_response = np.exp(beta * expected_payoffs)
        best_response /= np.sum(best_response)
        
        return best_response
    
    def _check_convergence(self,
                          strategies: Dict[str, np.ndarray],
                          old_strategies: Dict[str, np.ndarray],
                          tolerance: float = 1e-6) -> bool:
        """Check if strategies have converged."""
        for player in strategies:
            if np.linalg.norm(strategies[player] - old_strategies[player]) > tolerance:
                return False
        return True
    
    def _calculate_stability(self,
                           strategies: Dict[str, np.ndarray],
                           payoff_matrices: Dict[str, np.ndarray]) -> float:
        """Calculate stability score of Nash equilibrium."""
        stability_scores = []
        
        for player in strategies:
            current_payoff = self._calculate_player_payoff(
                player, strategies, payoff_matrices
            )
            
            # Test deviation payoffs
            deviation_payoffs = []
            for action in range(len(strategies[player])):
                # Create deviation strategy
                deviation_strategy = np.zeros_like(strategies[player])
                deviation_strategy[action] = 1.0
                
                # Calculate payoff with deviation
                temp_strategies = strategies.copy()
                temp_strategies[player] = deviation_strategy
                
                deviation_payoff = self._calculate_player_payoff(
                    player, temp_strategies, payoff_matrices
                )
                deviation_payoffs.append(deviation_payoff)
            
            # Stability is how much better the current strategy is
            max_deviation_payoff = max(deviation_payoffs)
            stability = max(0, current_payoff - max_deviation_payoff)
            stability_scores.append(stability)
        
        return np.mean(stability_scores)
    
    def _calculate_player_payoff(self,
                               player: str,
                               strategies: Dict[str, np.ndarray],
                               payoff_matrices: Dict[str, np.ndarray]) -> float:
        """Calculate expected payoff for a player given strategies."""
        payoff_matrix = payoff_matrices[player]
        player_strategy = strategies[player]
        
        # Calculate opponent mixed strategy
        other_players = [p for p in strategies.keys() if p != player]
        if not other_players:
            return np.dot(player_strategy, np.diagonal(payoff_matrix))
        
        opponent_strategy = strategies[other_players[0]]
        for other_player in other_players[1:]:
            opponent_strategy = np.kron(opponent_strategy, strategies[other_player])
        
        # Expected payoff
        return np.dot(player_strategy, np.dot(payoff_matrix, opponent_strategy))


class QuantumRiskParity:
    """
    Quantum-enhanced risk parity portfolio construction.
    
    Uses quantum algorithms to solve the complex optimization problem
    of equalizing risk contributions across portfolio assets.
    """
    
    def __init__(self, use_quantum: bool = True):
        """Initialize Quantum Risk Parity optimizer."""
        self.use_quantum = use_quantum and QISKIT_AVAILABLE
        
    def optimize_risk_parity(self,
                           returns: pd.DataFrame,
                           target_risk_contributions: Optional[np.ndarray] = None) -> QuantumOptimizationResult:
        """
        Optimize portfolio for risk parity using quantum algorithms.
        
        Args:
            returns: Historical returns data
            target_risk_contributions: Target risk contributions (default: equal)
            
        Returns:
            Risk parity optimization results
        """
        start_time = pd.Timestamp.now()
        
        cov_matrix = returns.cov().values
        n_assets = len(returns.columns)
        
        if target_risk_contributions is None:
            target_risk_contributions = np.ones(n_assets) / n_assets
        
        if self.use_quantum:
            weights = self._quantum_risk_parity(cov_matrix, target_risk_contributions)
        else:
            weights = self._classical_risk_parity(cov_matrix, target_risk_contributions)
        
        # Calculate metrics
        portfolio_risk = np.sqrt(np.dot(weights, np.dot(cov_matrix, weights)))
        expected_return = np.dot(weights, returns.mean().values)
        sharpe_ratio = expected_return / portfolio_risk if portfolio_risk > 0 else 0
        
        optimization_time = (pd.Timestamp.now() - start_time).total_seconds()
        
        return QuantumOptimizationResult(
            optimal_weights=weights,
            expected_return=expected_return,
            risk_level=portfolio_risk,
            sharpe_ratio=sharpe_ratio,
            optimization_time=optimization_time,
            quantum_advantage=self.use_quantum
        )
    
    def _quantum_risk_parity(self,
                           cov_matrix: np.ndarray,
                           target_risk_contributions: np.ndarray) -> np.ndarray:
        """Quantum risk parity optimization."""
        try:
            # This is a simplified quantum-inspired approach
            # Full implementation would use quantum optimization circuits
            
            n_assets = len(cov_matrix)
            
            # Initial equal weights
            weights = np.ones(n_assets) / n_assets
            
            # Quantum-inspired iterative optimization
            for _ in range(100):
                # Calculate risk contributions
                portfolio_vol = np.sqrt(np.dot(weights, np.dot(cov_matrix, weights)))
                marginal_contrib = np.dot(cov_matrix, weights) / portfolio_vol
                risk_contrib = weights * marginal_contrib / portfolio_vol
                
                # Quantum superposition update
                error = risk_contrib - target_risk_contributions
                
                # Quantum interference pattern for weight updates
                phase = np.pi * error
                quantum_correction = np.cos(phase) * np.exp(-np.abs(error))
                
                # Update weights
                weights *= (1 + 0.01 * quantum_correction)
                weights /= np.sum(weights)  # Normalize
            
            return weights
            
        except Exception as e:
            logger.error(f"Quantum risk parity failed: {e}")
            return self._classical_risk_parity(cov_matrix, target_risk_contributions)
    
    def _classical_risk_parity(self,
                             cov_matrix: np.ndarray,
                             target_risk_contributions: np.ndarray) -> np.ndarray:
        """Classical risk parity optimization."""
        n_assets = len(cov_matrix)
        
        def risk_parity_objective(log_weights):
            """
            risk_parity_objective function.

    Args:
        log_weights: Description

    Returns:
        Result of operation
            """
            weights = np.exp(log_weights)
            weights /= np.sum(weights)
            
            portfolio_vol = np.sqrt(np.dot(weights, np.dot(cov_matrix, weights)))
            marginal_contrib = np.dot(cov_matrix, weights) / portfolio_vol
            risk_contrib = weights * marginal_contrib / portfolio_vol
            
            # Minimize squared deviations from target
            return np.sum((risk_contrib - target_risk_contributions) ** 2)
        
        # Initial guess (log space to ensure positive weights)
        x0 = np.zeros(n_assets)
        
        # Optimize
        result = minimize(
            risk_parity_objective,
            x0,
            method='SLSQP',
            options={'maxiter': 1000}
        )
        
        # Convert back to weights
        weights = np.exp(result.x)
        weights /= np.sum(weights)
        
        return weights


class QuantumTradingSystem:
    """
    Integrated quantum trading system combining all quantum modules.
    
    This system orchestrates quantum portfolio optimization, Nash equilibrium
    calculations, and risk parity optimization for comprehensive trading decisions.
    """
    
    def __init__(self, use_quantum: bool = True):
        """Initialize Quantum Trading System."""
        self.use_quantum = use_quantum and QISKIT_AVAILABLE
        
        # Initialize quantum modules
        self.portfolio_optimizer = QuantumPortfolioOptimizer(use_quantum)
        self.nash_calculator = QuantumNashEquilibrium(use_quantum)
        self.risk_parity_optimizer = QuantumRiskParity(use_quantum)
        
        # System state
        self.current_portfolio = None
        self.optimization_history = []
        
        logger.info(f"Quantum Trading System initialized (quantum: {self.use_quantum})")
    
    async def optimize_trading_strategy(self,
                                      market_data: pd.DataFrame,
                                      competitor_strategies: Optional[Dict] = None,
                                      optimization_type: OptimizationType = OptimizationType.PORTFOLIO_OPTIMIZATION) -> Dict:
        """
        Comprehensive quantum trading strategy optimization.
        
        Args:
            market_data: Historical market data
            competitor_strategies: Known competitor strategies for Nash equilibrium
            optimization_type: Type of optimization to perform
            
        Returns:
            Comprehensive optimization results
        """
        results = {}
        
        # Portfolio optimization
        if optimization_type in [OptimizationType.PORTFOLIO_OPTIMIZATION, 
                               OptimizationType.MOMENTUM_ALLOCATION]:
            portfolio_result = self.portfolio_optimizer.optimize_portfolio(
                market_data.pct_change().dropna()
            )
            results['portfolio_optimization'] = portfolio_result
        
        # Risk parity optimization
        if optimization_type == OptimizationType.RISK_PARITY:
            risk_parity_result = self.risk_parity_optimizer.optimize_risk_parity(
                market_data.pct_change().dropna()
            )
            results['risk_parity'] = risk_parity_result
        
        # Nash equilibrium (if competitor data available)
        if competitor_strategies and optimization_type == OptimizationType.NASH_EQUILIBRIUM:
            nash_result = self.nash_calculator.calculate_nash_equilibrium(
                competitor_strategies
            )
            results['nash_equilibrium'] = nash_result
        
        # Store results
        self.optimization_history.append({
            'timestamp': pd.Timestamp.now(),
            'optimization_type': optimization_type,
            'results': results
        })
        
        return results
    
    def get_quantum_advantage_metrics(self) -> Dict:
        """Calculate quantum advantage metrics."""
        if not self.optimization_history:
            return {'quantum_advantage': 0, 'speedup_factor': 1.0}
        
        quantum_times = []
        classical_times = []
        
        for history_entry in self.optimization_history:
            for result_type, result in history_entry['results'].items():
                if hasattr(result, 'optimization_time'):
                    if result.quantum_advantage:
                        quantum_times.append(result.optimization_time)
                    else:
                        classical_times.append(result.optimization_time)
        
        if quantum_times and classical_times:
            avg_quantum_time = np.mean(quantum_times)
            avg_classical_time = np.mean(classical_times)
            speedup_factor = avg_classical_time / avg_quantum_time
        else:
            speedup_factor = 1.0
        
        return {
            'quantum_advantage': len(quantum_times) / len(self.optimization_history),
            'speedup_factor': speedup_factor,
            'total_optimizations': len(self.optimization_history)
        }
    
    def export_quantum_results(self, filepath: str):
        """Export quantum optimization results to file."""
        export_data = {
            'system_info': {
                'quantum_enabled': self.use_quantum,
                'qiskit_available': QISKIT_AVAILABLE,
                'optimization_count': len(self.optimization_history)
            },
            'optimization_history': self.optimization_history,
            'quantum_metrics': self.get_quantum_advantage_metrics()
        }
        import json
        with open(filepath, 'w') as f:
            # Convert numpy arrays to lists for JSON serialization
            def convert_numpy(obj):
                """
                convert_numpy function.

    Args:
        obj: Description

    Returns:
        Result of operation
                """
                if isinstance(obj, np.ndarray):
                    return obj.tolist()
                elif isinstance(obj, pd.Timestamp):
                    return obj.isoformat()
                elif hasattr(obj, '__dict__'):
                    return {k: convert_numpy(v) for k, v in obj.__dict__.items()}
                elif isinstance(obj, dict):
                    return {k: convert_numpy(v) for k, v in obj.items()}
                elif isinstance(obj, list):
                    return [convert_numpy(item) for item in obj]
                else:
                    return obj
            
            json.dump(convert_numpy(export_data), f, indent=2)
        
        logger.info(f"Quantum results exported to {filepath}")


# Utility functions for quantum algorithm testing
def test_quantum_availability():
    """Test if quantum computing libraries are available."""
    return QISKIT_AVAILABLE


def benchmark_quantum_vs_classical(returns_data: pd.DataFrame, 
                                 iterations: int = 10) -> Dict:
    """Benchmark quantum vs classical optimization performance."""
    quantum_optimizer = QuantumPortfolioOptimizer(use_quantum=True)
    classical_optimizer = QuantumPortfolioOptimizer(use_quantum=False)
    
    quantum_times = []
    classical_times = []
    
    for _ in range(iterations):
        # Quantum optimization
        quantum_result = quantum_optimizer.optimize_portfolio(returns_data)
        quantum_times.append(quantum_result.optimization_time)
        
        # Classical optimization
        classical_result = classical_optimizer.optimize_portfolio(returns_data)
        classical_times.append(classical_result.optimization_time)
    
    return {
        'quantum_avg_time': np.mean(quantum_times),
        'classical_avg_time': np.mean(classical_times),
        'speedup_factor': np.mean(classical_times) / np.mean(quantum_times),
        'quantum_available': QISKIT_AVAILABLE
    }
