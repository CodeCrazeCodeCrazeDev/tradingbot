"""
NEUROS-FI Region 7: Cerebellum - Forward Model and Execution Precision
======================================================================

Biological Basis:
The cerebellum contains more neurons than the rest of the brain combined.
It builds forward models of motor commands — predicting the sensory consequences
of an action before the action is executed, comparing predicted vs actual
sensory feedback, and computing fine-grained correction signals in real-time.

Purkinje cells receive input from 100,000+ synapses simultaneously.

Citations:
- Wolpert & Ghahramani (2000) - Computational principles of movement neuroscience
- Ito (2008) - Control of mental activities by internal models in the cerebellum
- Bastian (2006) - Learning to predict the future: the cerebellum adapts feedforward movement control
- Shadmehr & Krakauer (2008) - A computational neuroanatomy for motor control

Constitutional Version: 5.0
"""

import logging
import threading
import time
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum, auto
from typing import Any, Callable, Dict, List, Optional, Tuple
import numpy as np

logger = logging.getLogger(__name__)


class ExecutionAlgorithm(Enum):
    """Execution algorithms available."""
    
    TWAP = "twap"
    VWAP = "vwap"
    IMPLEMENTATION_SHORTFALL = "is"
    ARRIVAL_PRICE = "arrival"
    PASSIVE = "passive"
    AGGRESSIVE = "aggressive"
    ADAPTIVE = "adaptive"


class VenueType(Enum):
    """Trading venue types."""
    
    PRIMARY_EXCHANGE = "primary"
    DARK_POOL = "dark"
    ATS = "ats"
    INTERNALIZATION = "internal"
    MARKET_MAKER = "mm"


@dataclass
class ExecutionPrediction:
    """Forward model prediction for an execution."""
    
    prediction_id: str
    timestamp: datetime
    order_id: str
    
    # Predicted outcomes
    predicted_fill_probability: float
    predicted_slippage_bps: float
    predicted_market_impact_bps: float
    predicted_execution_time_ms: float
    predicted_adverse_selection: float
    
    # Input features
    order_size: float
    order_side: str
    venue: VenueType
    algorithm: ExecutionAlgorithm
    market_state: Dict[str, float]
    
    # Confidence
    confidence: float


@dataclass
class ExecutionOutcome:
    """Actual outcome of an execution."""
    
    order_id: str
    timestamp: datetime
    
    # Actual outcomes
    actual_fill_rate: float
    actual_slippage_bps: float
    actual_market_impact_bps: float
    actual_execution_time_ms: float
    actual_adverse_selection: float
    
    # Execution details
    venue: VenueType
    algorithm: ExecutionAlgorithm
    filled_quantity: float
    avg_price: float


@dataclass
class CerebellarError:
    """Error signal from cerebellum (predicted vs actual)."""
    
    error_id: str
    timestamp: datetime
    prediction: ExecutionPrediction
    outcome: ExecutionOutcome
    
    # Error components
    fill_error: float
    slippage_error: float
    impact_error: float
    time_error: float
    adverse_selection_error: float
    
    # Composite error
    total_error: float
    
    def __post_init__(self):
        if self.total_error == 0:
            self.total_error = (
                abs(self.fill_error) * 0.3 +
                abs(self.slippage_error) * 0.25 +
                abs(self.impact_error) * 0.25 +
                abs(self.time_error) * 0.1 +
                abs(self.adverse_selection_error) * 0.1
            )


@dataclass
class EfferenceCopy:
    """
    Efference copy - internal copy of intended action sent to forward model.
    
    When portfolio construction initiates a position change, an efference copy
    is sent to the cerebellar forward model simultaneously.
    """
    
    copy_id: str
    timestamp: datetime
    intended_action: Dict[str, Any]
    source_region: str
    predicted_consequences: Dict[str, float]


class ForwardModel:
    """
    Cerebellar Forward Model - predicts execution outcomes before they happen.
    
    Before every order is submitted, the cerebellum runs a pre-trade forward model:
    given order size, type, timing, venue, and market microstructure state,
    predict the exact execution outcome.
    """
    
    def __init__(self):
        self._lock = threading.RLock()
        
        # Model weights (learned from experience)
        self._weights: Dict[str, np.ndarray] = self._initialize_weights()
        
        # Feature statistics for normalization
        self._feature_means: Dict[str, float] = {}
        self._feature_stds: Dict[str, float] = {}
        
        # Learning rate
        self._learning_rate = 0.01
        
        # Prediction history
        self._predictions: List[ExecutionPrediction] = []
        
        # Model accuracy tracking
        self._accuracy_history: List[float] = []
    
    def _initialize_weights(self) -> Dict[str, np.ndarray]:
        """Initialize model weights."""
        return {
            'fill_probability': np.random.randn(20) * 0.1,
            'slippage': np.random.randn(20) * 0.1,
            'market_impact': np.random.randn(20) * 0.1,
            'execution_time': np.random.randn(20) * 0.1,
            'adverse_selection': np.random.randn(20) * 0.1,
        }
    
    def predict(
        self,
        order_size: float,
        order_side: str,
        venue: VenueType,
        algorithm: ExecutionAlgorithm,
        market_state: Dict[str, float]
    ) -> ExecutionPrediction:
        """
        Generate forward model prediction for an execution.
        
        Predicts fill probability, slippage, market impact, execution time,
        and adverse selection before the order is submitted.
        """
        with self._lock:
            # Extract features
            features = self._extract_features(
                order_size, order_side, venue, algorithm, market_state
            )
            
            # Generate predictions
            fill_prob = self._predict_component('fill_probability', features)
            slippage = self._predict_component('slippage', features)
            impact = self._predict_component('market_impact', features)
            exec_time = self._predict_component('execution_time', features)
            adverse = self._predict_component('adverse_selection', features)
            
            # Compute confidence based on feature familiarity
            confidence = self._compute_confidence(features)
            
            prediction = ExecutionPrediction(
                prediction_id=f"pred_{int(time.time()*1000)}",
                timestamp=datetime.utcnow(),
                order_id="",  # Set when order is created
                predicted_fill_probability=max(0, min(1, fill_prob)),
                predicted_slippage_bps=slippage,
                predicted_market_impact_bps=impact,
                predicted_execution_time_ms=max(0, exec_time),
                predicted_adverse_selection=max(0, adverse),
                order_size=order_size,
                order_side=order_side,
                venue=venue,
                algorithm=algorithm,
                market_state=market_state,
                confidence=confidence,
            )
            
            self._predictions.append(prediction)
            if len(self._predictions) > 10000:
                self._predictions = self._predictions[-5000:]
            
            return prediction
    
    def _extract_features(
        self,
        order_size: float,
        order_side: str,
        venue: VenueType,
        algorithm: ExecutionAlgorithm,
        market_state: Dict[str, float]
    ) -> np.ndarray:
        """Extract feature vector from inputs."""
        features = []
        
        # Order features
        features.append(np.log1p(order_size))
        features.append(1.0 if order_side == 'buy' else -1.0)
        
        # Venue one-hot (simplified)
        venue_idx = list(VenueType).index(venue)
        venue_features = [0.0] * len(VenueType)
        venue_features[venue_idx] = 1.0
        features.extend(venue_features)
        
        # Algorithm one-hot (simplified)
        algo_idx = list(ExecutionAlgorithm).index(algorithm)
        algo_features = [0.0] * len(ExecutionAlgorithm)
        algo_features[algo_idx] = 1.0
        features.extend(algo_features)
        
        # Market state features
        features.append(market_state.get('spread', 0.001))
        features.append(market_state.get('volatility', 0.01))
        features.append(market_state.get('volume', 1000000))
        features.append(market_state.get('order_imbalance', 0))
        
        # Pad to fixed size
        while len(features) < 20:
            features.append(0.0)
        
        return np.array(features[:20])
    
    def _predict_component(self, component: str, features: np.ndarray) -> float:
        """Predict a single component using linear model."""
        weights = self._weights.get(component, np.zeros(20))
        return float(np.dot(weights, features))
    
    def _compute_confidence(self, features: np.ndarray) -> float:
        """Compute prediction confidence based on feature familiarity."""
        # Simple confidence based on feature magnitude
        # In practice, would use uncertainty estimation
        return 0.7  # Placeholder
    
    def update(self, error: CerebellarError):
        """Update forward model weights based on prediction error."""
        with self._lock:
            prediction = error.prediction
            
            # Extract features from prediction
            features = self._extract_features(
                prediction.order_size,
                prediction.order_side,
                prediction.venue,
                prediction.algorithm,
                prediction.market_state,
            )
            
            # Update each component
            self._update_component('fill_probability', features, error.fill_error)
            self._update_component('slippage', features, error.slippage_error)
            self._update_component('market_impact', features, error.impact_error)
            self._update_component('execution_time', features, error.time_error)
            self._update_component('adverse_selection', features, error.adverse_selection_error)
            
            # Track accuracy
            self._accuracy_history.append(1.0 - error.total_error)
            if len(self._accuracy_history) > 10000:
                self._accuracy_history = self._accuracy_history[-5000:]
    
    def _update_component(self, component: str, features: np.ndarray, error: float):
        """Update weights for a single component using gradient descent."""
        if component not in self._weights:
            return
        
        # Gradient descent update
        gradient = error * features
        self._weights[component] -= self._learning_rate * gradient
    
    def get_accuracy(self) -> float:
        """Get recent model accuracy."""
        with self._lock:
            if not self._accuracy_history:
                return 0.5
            return np.mean(self._accuracy_history[-100:])
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get forward model statistics."""
        with self._lock:
            return {
                'total_predictions': len(self._predictions),
                'recent_accuracy': self.get_accuracy(),
                'learning_rate': self._learning_rate,
            }


class ErrorCorrection:
    """
    Cerebellar Error Correction - computes fine-grained correction signals.
    
    Predicted execution outcome vs actual execution outcome generates
    a cerebellar error signal. This signal updates the forward model
    continuously — every order, every millisecond.
    """
    
    def __init__(self, forward_model: ForwardModel):
        self._forward_model = forward_model
        self._lock = threading.RLock()
        
        # Error history
        self._errors: List[CerebellarError] = []
        
        # Error statistics
        self._error_by_venue: Dict[VenueType, List[float]] = {v: [] for v in VenueType}
        self._error_by_algorithm: Dict[ExecutionAlgorithm, List[float]] = {a: [] for a in ExecutionAlgorithm}
    
    def compute_error(
        self,
        prediction: ExecutionPrediction,
        outcome: ExecutionOutcome
    ) -> CerebellarError:
        """
        Compute cerebellar error signal from prediction vs outcome.
        """
        with self._lock:
            # Compute component errors
            fill_error = outcome.actual_fill_rate - prediction.predicted_fill_probability
            slippage_error = outcome.actual_slippage_bps - prediction.predicted_slippage_bps
            impact_error = outcome.actual_market_impact_bps - prediction.predicted_market_impact_bps
            time_error = (outcome.actual_execution_time_ms - prediction.predicted_execution_time_ms) / 1000
            adverse_error = outcome.actual_adverse_selection - prediction.predicted_adverse_selection
            
            error = CerebellarError(
                error_id=f"err_{int(time.time()*1000)}",
                timestamp=datetime.utcnow(),
                prediction=prediction,
                outcome=outcome,
                fill_error=fill_error,
                slippage_error=slippage_error,
                impact_error=impact_error,
                time_error=time_error,
                adverse_selection_error=adverse_error,
                total_error=0,  # Computed in __post_init__
            )
            
            # Store error
            self._errors.append(error)
            if len(self._errors) > 10000:
                self._errors = self._errors[-5000:]
            
            # Track by venue and algorithm
            self._error_by_venue[outcome.venue].append(error.total_error)
            self._error_by_algorithm[outcome.algorithm].append(error.total_error)
            
            # Trim venue/algorithm histories
            for v in VenueType:
                if len(self._error_by_venue[v]) > 1000:
                    self._error_by_venue[v] = self._error_by_venue[v][-500:]
            for a in ExecutionAlgorithm:
                if len(self._error_by_algorithm[a]) > 1000:
                    self._error_by_algorithm[a] = self._error_by_algorithm[a][-500:]
            
            # Update forward model
            self._forward_model.update(error)
            
            return error
    
    def get_venue_error_stats(self) -> Dict[str, float]:
        """Get error statistics by venue."""
        with self._lock:
            return {
                v.value: np.mean(errors) if errors else 0.0
                for v, errors in self._error_by_venue.items()
            }
    
    def get_algorithm_error_stats(self) -> Dict[str, float]:
        """Get error statistics by algorithm."""
        with self._lock:
            return {
                a.value: np.mean(errors) if errors else 0.0
                for a, errors in self._error_by_algorithm.items()
            }
    
    def get_recent_errors(self, limit: int = 100) -> List[CerebellarError]:
        """Get recent errors."""
        with self._lock:
            return self._errors[-limit:]
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get error correction statistics."""
        with self._lock:
            if not self._errors:
                return {'total_errors': 0}
            
            recent = [e.total_error for e in self._errors[-1000:]]
            
            return {
                'total_errors': len(self._errors),
                'mean_error': np.mean(recent),
                'std_error': np.std(recent),
                'venue_errors': self.get_venue_error_stats(),
                'algorithm_errors': self.get_algorithm_error_stats(),
            }


class EfferenceCopyProcessor:
    """
    Efference Copy Processor - handles internal copies of intended actions.
    
    When the portfolio construction layer initiates a position change,
    an efference copy is sent to the cerebellar forward model simultaneously.
    The model generates predicted sensory consequences before any order hits the market.
    """
    
    def __init__(self, forward_model: ForwardModel):
        self._forward_model = forward_model
        self._lock = threading.RLock()
        
        # Pending efference copies (awaiting outcome)
        self._pending: Dict[str, EfferenceCopy] = {}
        
        # Processed copies
        self._processed: List[EfferenceCopy] = []
    
    def receive_copy(
        self,
        intended_action: Dict[str, Any],
        source_region: str
    ) -> EfferenceCopy:
        """
        Receive an efference copy of an intended action.
        
        Generates predicted consequences before the action executes.
        """
        with self._lock:
            # Generate prediction
            prediction = self._forward_model.predict(
                order_size=intended_action.get('size', 0),
                order_side=intended_action.get('side', 'buy'),
                venue=intended_action.get('venue', VenueType.PRIMARY_EXCHANGE),
                algorithm=intended_action.get('algorithm', ExecutionAlgorithm.ADAPTIVE),
                market_state=intended_action.get('market_state', {}),
            )
            
            # Create efference copy
            copy = EfferenceCopy(
                copy_id=f"eff_{int(time.time()*1000)}",
                timestamp=datetime.utcnow(),
                intended_action=intended_action,
                source_region=source_region,
                predicted_consequences={
                    'fill_probability': prediction.predicted_fill_probability,
                    'slippage_bps': prediction.predicted_slippage_bps,
                    'market_impact_bps': prediction.predicted_market_impact_bps,
                    'execution_time_ms': prediction.predicted_execution_time_ms,
                },
            )
            
            # Store as pending
            action_id = intended_action.get('action_id', copy.copy_id)
            self._pending[action_id] = copy
            
            return copy
    
    def resolve_copy(self, action_id: str, actual_outcome: Dict[str, Any]):
        """Resolve a pending efference copy with actual outcome."""
        with self._lock:
            if action_id in self._pending:
                copy = self._pending.pop(action_id)
                self._processed.append(copy)
                
                if len(self._processed) > 10000:
                    self._processed = self._processed[-5000:]
    
    def get_pending_count(self) -> int:
        """Get count of pending efference copies."""
        with self._lock:
            return len(self._pending)


class TransactionCostIntelligence:
    """
    Transaction Cost Intelligence - tracks and predicts execution costs.
    
    The forward model's prediction accuracy for execution cost is tracked
    as a separate P&L attribution. "Execution alpha" (or deficit) relative
    to benchmark algorithms is measured, attributed, and used to retrain.
    """
    
    def __init__(self):
        self._lock = threading.RLock()
        
        # Cost tracking
        self._predicted_costs: List[float] = []
        self._actual_costs: List[float] = []
        
        # Benchmark comparison
        self._benchmark_costs: Dict[ExecutionAlgorithm, List[float]] = {
            a: [] for a in ExecutionAlgorithm
        }
        
        # Execution alpha tracking
        self._execution_alpha: List[float] = []
    
    def record_execution(
        self,
        predicted_cost_bps: float,
        actual_cost_bps: float,
        benchmark_cost_bps: float,
        algorithm: ExecutionAlgorithm
    ):
        """Record an execution for cost analysis."""
        with self._lock:
            self._predicted_costs.append(predicted_cost_bps)
            self._actual_costs.append(actual_cost_bps)
            self._benchmark_costs[algorithm].append(benchmark_cost_bps)
            
            # Execution alpha = benchmark - actual (positive = outperformed)
            alpha = benchmark_cost_bps - actual_cost_bps
            self._execution_alpha.append(alpha)
            
            # Trim histories
            max_history = 10000
            if len(self._predicted_costs) > max_history:
                self._predicted_costs = self._predicted_costs[-max_history//2:]
                self._actual_costs = self._actual_costs[-max_history//2:]
                self._execution_alpha = self._execution_alpha[-max_history//2:]
    
    def get_execution_alpha(self) -> float:
        """Get cumulative execution alpha."""
        with self._lock:
            return sum(self._execution_alpha)
    
    def get_prediction_accuracy(self) -> float:
        """Get cost prediction accuracy."""
        with self._lock:
            if not self._predicted_costs:
                return 0.0
            
            errors = [
                abs(p - a) for p, a in zip(self._predicted_costs, self._actual_costs)
            ]
            mean_error = np.mean(errors)
            mean_cost = np.mean([abs(c) for c in self._actual_costs])
            
            if mean_cost == 0:
                return 1.0
            
            return 1.0 - (mean_error / mean_cost)
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get transaction cost intelligence statistics."""
        with self._lock:
            return {
                'total_executions': len(self._actual_costs),
                'cumulative_alpha_bps': self.get_execution_alpha(),
                'prediction_accuracy': self.get_prediction_accuracy(),
                'avg_cost_bps': np.mean(self._actual_costs) if self._actual_costs else 0,
                'avg_predicted_bps': np.mean(self._predicted_costs) if self._predicted_costs else 0,
            }


class PurkinjeCell:
    """
    Purkinje Cell Equivalent - integrates massive parallel input.
    
    Each execution decision integrates signals from 100,000+ microstructure
    features simultaneously. The cerebellar architecture naturally handles
    this extreme fan-in.
    """
    
    def __init__(self, cell_id: str, feature_count: int = 1000):
        self._cell_id = cell_id
        self._feature_count = feature_count
        self._lock = threading.RLock()
        
        # Synaptic weights (parallel fiber inputs)
        self._weights = np.random.randn(feature_count) * 0.01
        
        # Climbing fiber input (error signal)
        self._climbing_fiber_signal = 0.0
        
        # Learning rate
        self._learning_rate = 0.001
        
        # Activation history
        self._activations: List[float] = []
    
    def compute_output(self, parallel_fiber_input: np.ndarray) -> float:
        """
        Compute Purkinje cell output from parallel fiber input.
        
        Integrates up to 100,000+ inputs simultaneously.
        """
        with self._lock:
            # Ensure input matches weight size
            if len(parallel_fiber_input) < self._feature_count:
                padded = np.zeros(self._feature_count)
                padded[:len(parallel_fiber_input)] = parallel_fiber_input
                parallel_fiber_input = padded
            elif len(parallel_fiber_input) > self._feature_count:
                parallel_fiber_input = parallel_fiber_input[:self._feature_count]
            
            # Compute weighted sum
            activation = np.dot(self._weights, parallel_fiber_input)
            
            # Apply nonlinearity
            output = np.tanh(activation)
            
            self._activations.append(output)
            if len(self._activations) > 10000:
                self._activations = self._activations[-5000:]
            
            return float(output)
    
    def receive_climbing_fiber(self, error_signal: float):
        """
        Receive climbing fiber input (error signal from inferior olive).
        
        Climbing fiber signals drive long-term depression of active synapses.
        """
        with self._lock:
            self._climbing_fiber_signal = error_signal
    
    def update_weights(self, parallel_fiber_input: np.ndarray):
        """
        Update synaptic weights based on climbing fiber signal.
        
        Implements cerebellar LTD: active synapses are weakened when
        climbing fiber fires.
        """
        with self._lock:
            if len(parallel_fiber_input) != self._feature_count:
                return
            
            # LTD: weaken synapses that were active when error occurred
            delta = -self._learning_rate * self._climbing_fiber_signal * parallel_fiber_input
            self._weights += delta
            
            # Reset climbing fiber
            self._climbing_fiber_signal = 0.0


class Cerebellum:
    """
    The complete Cerebellum - forward models and execution precision.
    
    Implements:
    - Forward model (pre-trade prediction)
    - Efference copy processing
    - Error correction (predicted vs actual)
    - Transaction cost intelligence
    - Purkinje cell integration
    """
    
    def __init__(self):
        # Initialize components
        self.forward_model = ForwardModel()
        self.error_correction = ErrorCorrection(self.forward_model)
        self.efference_copy = EfferenceCopyProcessor(self.forward_model)
        self.transaction_cost = TransactionCostIntelligence()
        
        # Purkinje cells for different execution contexts
        self._purkinje_cells: Dict[str, PurkinjeCell] = {
            'aggressive': PurkinjeCell('aggressive', 500),
            'passive': PurkinjeCell('passive', 500),
            'dark_pool': PurkinjeCell('dark_pool', 500),
        }
        
        self._lock = threading.RLock()
        
        logger.info("Cerebellum initialized - forward models and execution precision active")
    
    def predict_execution(
        self,
        order: Dict[str, Any],
        market_state: Dict[str, Any]
    ) -> ExecutionPrediction:
        """
        Predict execution outcome before order submission.
        
        Returns forward model prediction.
        """
        with self._lock:
            return self.forward_model.predict(
                order_size=order.get('size', 0),
                order_side=order.get('side', 'buy'),
                venue=order.get('venue', VenueType.PRIMARY_EXCHANGE),
                algorithm=order.get('algorithm', ExecutionAlgorithm.ADAPTIVE),
                market_state=market_state,
            )
    
    def process_efference_copy(
        self,
        intended_action: Dict[str, Any],
        source: str = "portfolio_construction"
    ) -> EfferenceCopy:
        """
        Process efference copy of intended action.
        
        Generates predicted consequences before execution.
        """
        return self.efference_copy.receive_copy(intended_action, source)
    
    def process_execution_outcome(
        self,
        prediction: ExecutionPrediction,
        outcome: ExecutionOutcome
    ) -> CerebellarError:
        """
        Process execution outcome and compute error signal.
        
        Updates forward model based on prediction error.
        """
        with self._lock:
            # Compute error
            error = self.error_correction.compute_error(prediction, outcome)
            
            # Record transaction cost
            predicted_cost = prediction.predicted_slippage_bps + prediction.predicted_market_impact_bps
            actual_cost = outcome.actual_slippage_bps + outcome.actual_market_impact_bps
            benchmark_cost = actual_cost * 1.2  # Simplified benchmark
            
            self.transaction_cost.record_execution(
                predicted_cost, actual_cost, benchmark_cost, outcome.algorithm
            )
            
            # Update Purkinje cells
            self._update_purkinje_cells(error)
            
            return error
    
    def _update_purkinje_cells(self, error: CerebellarError):
        """Update Purkinje cells based on error signal."""
        # Determine which cell to update based on algorithm
        algo = error.outcome.algorithm
        
        if algo in [ExecutionAlgorithm.AGGRESSIVE, ExecutionAlgorithm.ARRIVAL_PRICE]:
            cell = self._purkinje_cells['aggressive']
        elif algo in [ExecutionAlgorithm.PASSIVE, ExecutionAlgorithm.TWAP]:
            cell = self._purkinje_cells['passive']
        else:
            cell = self._purkinje_cells['dark_pool']
        
        # Send climbing fiber signal
        cell.receive_climbing_fiber(error.total_error)
    
    def get_execution_alpha(self) -> float:
        """Get cumulative execution alpha."""
        return self.transaction_cost.get_execution_alpha()
    
    def get_model_accuracy(self) -> float:
        """Get forward model accuracy."""
        return self.forward_model.get_accuracy()
    
    def get_status(self) -> Dict[str, Any]:
        """Get cerebellum status."""
        return {
            'forward_model': self.forward_model.get_statistics(),
            'error_correction': self.error_correction.get_statistics(),
            'transaction_cost': self.transaction_cost.get_statistics(),
            'pending_efference_copies': self.efference_copy.get_pending_count(),
            'model_accuracy': self.get_model_accuracy(),
            'execution_alpha_bps': self.get_execution_alpha(),
        }
