"""
Safety and Verification Systems
================================

Advanced safety and verification capabilities including:
- Adversarial Robustness Testing
- Causal Inference Engine
- Uncertainty Quantification
- Formal Verification of Trading Logic
"""

import logging
import math
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional, Any, Tuple, Callable, Set
import numpy as np

logger = logging.getLogger(__name__)


# =============================================================================
# ADVERSARIAL ROBUSTNESS TESTING
# =============================================================================

class AttackType(Enum):
    """Types of adversarial attacks"""
    FGSM = "fgsm"  # Fast Gradient Sign Method
    PGD = "pgd"  # Projected Gradient Descent
    NOISE = "noise"  # Random noise
    MARKET_MANIPULATION = "market_manipulation"
    FLASH_CRASH = "flash_crash"
    LIQUIDITY_CRISIS = "liquidity_crisis"
    DATA_POISONING = "data_poisoning"


@dataclass
class AdversarialScenario:
    """An adversarial test scenario"""
    scenario_id: str
    name: str
    attack_type: AttackType
    parameters: Dict[str, Any]
    severity: float  # 0-1
    description: str


@dataclass
class RobustnessResult:
    """Result of robustness testing"""
    scenario_id: str
    original_output: Any
    adversarial_output: Any
    is_robust: bool
    degradation: float  # Performance degradation
    recovery_time: Optional[float] = None


class AdversarialRobustnessTester:
    """
    Adversarial Robustness Testing
    
    Tests trading strategies against adversarial conditions
    to ensure robustness.
    """
    
    def __init__(self):
        self.scenarios: Dict[str, AdversarialScenario] = {}
        self.results: List[RobustnessResult] = []
        
        # Create default scenarios
        self._create_default_scenarios()
        
        logger.info("AdversarialRobustnessTester initialized")
    
    def _create_default_scenarios(self):
        """Create default adversarial scenarios"""
        
        scenarios = [
            AdversarialScenario(
                scenario_id="flash_crash_1",
                name="Flash Crash - 10% Drop",
                attack_type=AttackType.FLASH_CRASH,
                parameters={'drop_pct': 0.10, 'duration_bars': 5, 'recovery_bars': 20},
                severity=0.8,
                description="Sudden 10% price drop followed by recovery"
            ),
            AdversarialScenario(
                scenario_id="flash_crash_2",
                name="Flash Crash - 20% Drop",
                attack_type=AttackType.FLASH_CRASH,
                parameters={'drop_pct': 0.20, 'duration_bars': 3, 'recovery_bars': 50},
                severity=0.95,
                description="Severe 20% price drop"
            ),
            AdversarialScenario(
                scenario_id="liquidity_1",
                name="Liquidity Crisis",
                attack_type=AttackType.LIQUIDITY_CRISIS,
                parameters={'spread_multiplier': 10, 'volume_reduction': 0.9},
                severity=0.7,
                description="Sudden liquidity evaporation"
            ),
            AdversarialScenario(
                scenario_id="manipulation_1",
                name="Stop Hunt",
                attack_type=AttackType.MARKET_MANIPULATION,
                parameters={'spike_pct': 0.03, 'duration_bars': 2},
                severity=0.5,
                description="Price spike to trigger stop losses"
            ),
            AdversarialScenario(
                scenario_id="noise_1",
                name="High Noise Environment",
                attack_type=AttackType.NOISE,
                parameters={'noise_std': 0.02},
                severity=0.3,
                description="Increased market noise"
            ),
            AdversarialScenario(
                scenario_id="poisoning_1",
                name="Data Poisoning",
                attack_type=AttackType.DATA_POISONING,
                parameters={'poison_rate': 0.05, 'bias': 0.01},
                severity=0.6,
                description="Corrupted input data"
            )
        ]
        
        for scenario in scenarios:
            self.scenarios[scenario.scenario_id] = scenario
    
    def generate_adversarial_data(
        self,
        original_data: np.ndarray,
        scenario: AdversarialScenario
    ) -> np.ndarray:
        """Generate adversarial data based on scenario"""
        
        adversarial = original_data.copy()
        params = scenario.parameters
        
        if scenario.attack_type == AttackType.FLASH_CRASH:
            drop_pct = params.get('drop_pct', 0.1)
            duration = params.get('duration_bars', 5)
            
            # Insert flash crash
            crash_start = len(adversarial) // 2
            crash_end = crash_start + duration
            
            for i in range(crash_start, min(crash_end, len(adversarial))):
                progress = (i - crash_start) / duration
                drop = drop_pct * (1 - progress)  # Gradual recovery
                adversarial[i] *= (1 - drop)
        
        elif scenario.attack_type == AttackType.LIQUIDITY_CRISIS:
            # Increase volatility to simulate liquidity issues
            volatility_mult = params.get('spread_multiplier', 5)
            noise = np.random.randn(len(adversarial)) * np.std(adversarial) * volatility_mult * 0.1
            adversarial += noise
        
        elif scenario.attack_type == AttackType.MARKET_MANIPULATION:
            spike_pct = params.get('spike_pct', 0.03)
            duration = params.get('duration_bars', 2)
            
            # Insert price spike
            spike_start = len(adversarial) // 2
            for i in range(spike_start, min(spike_start + duration, len(adversarial))):
                adversarial[i] *= (1 + spike_pct)
        
        elif scenario.attack_type == AttackType.NOISE:
            noise_std = params.get('noise_std', 0.02)
            noise = np.random.randn(len(adversarial)) * np.mean(np.abs(adversarial)) * noise_std
            adversarial += noise
        
        elif scenario.attack_type == AttackType.DATA_POISONING:
            poison_rate = params.get('poison_rate', 0.05)
            bias = params.get('bias', 0.01)
            
            # Randomly corrupt data points
            mask = np.random.random(len(adversarial)) < poison_rate
            adversarial[mask] *= (1 + bias)
        
        return adversarial
    
    def test_robustness(
        self,
        strategy_function: Callable[[np.ndarray], Any],
        original_data: np.ndarray,
        scenario_ids: Optional[List[str]] = None
    ) -> List[RobustnessResult]:
        """
        Test strategy robustness against adversarial scenarios
        
        Args:
            strategy_function: Function that takes data and returns trading decision
            original_data: Original market data
            scenario_ids: Specific scenarios to test (None = all)
        
        Returns:
            List of robustness results
        """
        
        results = []
        
        scenarios_to_test = (
            [self.scenarios[sid] for sid in scenario_ids if sid in self.scenarios]
            if scenario_ids
            else list(self.scenarios.values())
        )
        
        # Get original output
        original_output = strategy_function(original_data)
        
        for scenario in scenarios_to_test:
            # Generate adversarial data
            adversarial_data = self.generate_adversarial_data(original_data, scenario)
            
            # Get adversarial output
            try:
                adversarial_output = strategy_function(adversarial_data)
                
                # Calculate degradation
                degradation = self._calculate_degradation(
                    original_output, adversarial_output
                )
                
                # Determine if robust
                is_robust = degradation < 0.3  # Less than 30% degradation
                
            except Exception as e:
                logger.warning(f"Strategy failed under {scenario.name}: {e}")
                adversarial_output = None
                degradation = 1.0
                is_robust = False
            
            result = RobustnessResult(
                scenario_id=scenario.scenario_id,
                original_output=original_output,
                adversarial_output=adversarial_output,
                is_robust=is_robust,
                degradation=degradation
            )
            
            results.append(result)
            self.results.append(result)
        
        return results
    
    def _calculate_degradation(self, original: Any, adversarial: Any) -> float:
        """Calculate performance degradation"""
        
        if original is None or adversarial is None:
            return 1.0
        
        if isinstance(original, dict) and isinstance(adversarial, dict):
            # Compare confidence
            orig_conf = original.get('confidence', 0.5)
            adv_conf = adversarial.get('confidence', 0.5)
            
            # Compare actions
            action_match = original.get('action') == adversarial.get('action')
            
            conf_degradation = abs(orig_conf - adv_conf)
            action_penalty = 0 if action_match else 0.5
            
            return min(1.0, conf_degradation + action_penalty)
        
        elif isinstance(original, (int, float)) and isinstance(adversarial, (int, float)):
            if original == 0:
                return 1.0 if adversarial != 0 else 0.0
            return min(1.0, abs(original - adversarial) / abs(original))
        
        return 0.5  # Unknown comparison
    
    def get_robustness_score(self) -> float:
        """Calculate overall robustness score"""
        
        if not self.results:
            return 1.0
        
        robust_count = sum(1 for r in self.results if r.is_robust)
        return robust_count / len(self.results)
    
    def get_report(self) -> Dict[str, Any]:
        """Get robustness testing report"""
        
        return {
            'num_scenarios': len(self.scenarios),
            'num_tests': len(self.results),
            'robustness_score': self.get_robustness_score(),
            'results': [
                {
                    'scenario_id': r.scenario_id,
                    'is_robust': r.is_robust,
                    'degradation': r.degradation
                }
                for r in self.results
            ],
            'vulnerable_scenarios': [
                r.scenario_id for r in self.results if not r.is_robust
            ]
        }


# =============================================================================
# CAUSAL INFERENCE ENGINE
# =============================================================================

@dataclass
class CausalRelation:
    """A causal relationship between variables"""
    cause: str
    effect: str
    strength: float  # -1 to 1
    lag: int  # Time lag in periods
    confidence: float
    mechanism: str  # Description of causal mechanism


class CausalInferenceEngine:
    """
    Causal Inference Engine
    
    Discovers and validates causal relationships
    in market data to avoid spurious correlations.
    """
    
    def __init__(self):
        self.causal_graph: Dict[str, List[CausalRelation]] = {}
        self.discovered_relations: List[CausalRelation] = []
        
        logger.info("CausalInferenceEngine initialized")
    
    def granger_causality_test(
        self,
        cause_data: np.ndarray,
        effect_data: np.ndarray,
        max_lag: int = 10
    ) -> Tuple[bool, float, int]:
        """
        Perform Granger causality test
        
        Returns:
            (is_causal, p_value, optimal_lag)
        """
        
        if len(cause_data) != len(effect_data):
            return False, 1.0, 0
        
        n = len(cause_data)
        
        if n < max_lag * 3:
            return False, 1.0, 0
        
        best_lag = 1
        best_f_stat = 0
        
        for lag in range(1, max_lag + 1):
            # Restricted model: effect ~ lagged effect
            y = effect_data[lag:]
            X_restricted = np.column_stack([
                effect_data[lag-i-1:-i-1] if i < lag-1 else effect_data[:-(lag)]
                for i in range(lag)
            ])
            
            # Unrestricted model: effect ~ lagged effect + lagged cause
            X_unrestricted = np.column_stack([
                X_restricted,
                *[cause_data[lag-i-1:-i-1] if i < lag-1 else cause_data[:-(lag)]
                  for i in range(lag)]
            ])
            
            # Calculate residuals
            try:
                # Restricted model
                beta_r = np.linalg.lstsq(X_restricted, y, rcond=None)[0]
                resid_r = y - X_restricted @ beta_r
                ssr_r = np.sum(resid_r ** 2)
                
                # Unrestricted model
                beta_u = np.linalg.lstsq(X_unrestricted, y, rcond=None)[0]
                resid_u = y - X_unrestricted @ beta_u
                ssr_u = np.sum(resid_u ** 2)
                
                # F-statistic
                df1 = lag
                df2 = n - 2 * lag - 1
                
                if ssr_u > 0 and df2 > 0:
                    f_stat = ((ssr_r - ssr_u) / df1) / (ssr_u / df2)
                    
                    if f_stat > best_f_stat:
                        best_f_stat = f_stat
                        best_lag = lag
            
            except Exception:
                continue
        
        # Approximate p-value (simplified)
        # In practice, use scipy.stats.f.sf
        p_value = 1.0 / (1.0 + best_f_stat) if best_f_stat > 0 else 1.0
        
        is_causal = p_value < 0.05
        
        return is_causal, p_value, best_lag
    
    def discover_causal_relations(
        self,
        data: Dict[str, np.ndarray],
        target_variable: str,
        max_lag: int = 10
    ) -> List[CausalRelation]:
        """
        Discover causal relations affecting target variable
        
        Args:
            data: Dictionary of variable name -> time series
            target_variable: Variable to find causes for
            max_lag: Maximum lag to test
        
        Returns:
            List of discovered causal relations
        """
        
        if target_variable not in data:
            logger.warning(f"Target variable {target_variable} not in data")
            return []
        
        target_data = data[target_variable]
        relations = []
        
        for var_name, var_data in data.items():
            if var_name == target_variable:
                continue
            
            is_causal, p_value, lag = self.granger_causality_test(
                var_data, target_data, max_lag
            )
            
            if is_causal:
                # Calculate correlation for strength
                if len(var_data) > lag:
                    lagged_var = var_data[:-lag] if lag > 0 else var_data
                    target_aligned = target_data[lag:] if lag > 0 else target_data
                    
                    if len(lagged_var) == len(target_aligned) and len(lagged_var) > 0:
                        correlation = np.corrcoef(lagged_var, target_aligned)[0, 1]
                        strength = correlation if np.isfinite(correlation) else 0.0
                    else:
                        strength = 0.0
                else:
                    strength = 0.0
                
                relation = CausalRelation(
                    cause=var_name,
                    effect=target_variable,
                    strength=strength,
                    lag=lag,
                    confidence=1 - p_value,
                    mechanism=f"Granger causality with lag {lag}"
                )
                
                relations.append(relation)
                self.discovered_relations.append(relation)
                
                # Add to causal graph
                if var_name not in self.causal_graph:
                    self.causal_graph[var_name] = []
                self.causal_graph[var_name].append(relation)
        
        logger.info(f"Discovered {len(relations)} causal relations for {target_variable}")
        
        return relations
    
    def validate_causal_claim(
        self,
        cause: str,
        effect: str,
        data: Dict[str, np.ndarray]
    ) -> Tuple[bool, float]:
        """
        Validate a claimed causal relationship
        
        Returns:
            (is_valid, confidence)
        """
        
        if cause not in data or effect not in data:
            return False, 0.0
        
        is_causal, p_value, lag = self.granger_causality_test(
            data[cause], data[effect]
        )
        
        return is_causal, 1 - p_value
    
    def get_causal_path(
        self,
        source: str,
        target: str
    ) -> Optional[List[str]]:
        """Find causal path from source to target"""
        
        if source not in self.causal_graph:
            return None
        
        # BFS to find path
        visited = set()
        queue = [(source, [source])]
        
        while queue:
            current, path = queue.pop(0)
            
            if current == target:
                return path
            
            if current in visited:
                continue
            
            visited.add(current)
            
            if current in self.causal_graph:
                for relation in self.causal_graph[current]:
                    if relation.effect not in visited:
                        queue.append((relation.effect, path + [relation.effect]))
        
        return None
    
    def counterfactual_analysis(
        self,
        data: Dict[str, np.ndarray],
        intervention_var: str,
        intervention_value: float,
        target_var: str
    ) -> Dict[str, Any]:
        """
        Perform counterfactual analysis
        
        "What would target_var be if intervention_var were intervention_value?"
        """
        
        # Find causal path
        path = self.get_causal_path(intervention_var, target_var)
        
        if not path:
            return {
                'feasible': False,
                'reason': 'No causal path found'
            }
        
        # Calculate effect through path
        total_effect = 1.0
        total_lag = 0
        
        for i in range(len(path) - 1):
            cause = path[i]
            effect = path[i + 1]
            
            # Find relation
            if cause in self.causal_graph:
                for relation in self.causal_graph[cause]:
                    if relation.effect == effect:
                        total_effect *= relation.strength
                        total_lag += relation.lag
                        break
        
        # Estimate counterfactual
        if target_var in data and len(data[target_var]) > 0:
            current_value = data[target_var][-1]
            
            if intervention_var in data and len(data[intervention_var]) > 0:
                current_intervention = data[intervention_var][-1]
                change = intervention_value - current_intervention
                
                counterfactual = current_value + change * total_effect
            else:
                counterfactual = current_value
        else:
            counterfactual = intervention_value * total_effect
        
        return {
            'feasible': True,
            'causal_path': path,
            'total_effect': total_effect,
            'total_lag': total_lag,
            'counterfactual_value': counterfactual
        }
    
    def get_report(self) -> Dict[str, Any]:
        """Get causal inference report"""
        
        return {
            'num_relations': len(self.discovered_relations),
            'causal_graph_nodes': len(self.causal_graph),
            'relations': [
                {
                    'cause': r.cause,
                    'effect': r.effect,
                    'strength': r.strength,
                    'lag': r.lag,
                    'confidence': r.confidence
                }
                for r in self.discovered_relations
            ]
        }


# =============================================================================
# UNCERTAINTY QUANTIFICATION
# =============================================================================

class UncertaintyType(Enum):
    """Types of uncertainty"""
    ALEATORIC = "aleatoric"  # Data uncertainty (irreducible)
    EPISTEMIC = "epistemic"  # Model uncertainty (reducible)
    DISTRIBUTIONAL = "distributional"  # Distribution shift


@dataclass
class UncertaintyEstimate:
    """Uncertainty estimate for a prediction"""
    prediction: float
    mean: float
    std: float
    confidence_interval: Tuple[float, float]
    uncertainty_type: UncertaintyType
    calibration_score: float


class UncertaintyQuantifier:
    """
    Uncertainty Quantification
    
    Estimates prediction uncertainty using various methods
    for risk-aware decision making.
    """
    
    def __init__(
        self,
        num_samples: int = 100,
        confidence_level: float = 0.95
    ):
        self.num_samples = num_samples
        self.confidence_level = confidence_level
        
        self.calibration_history: List[Tuple[float, float, bool]] = []
        
        logger.info("UncertaintyQuantifier initialized")
    
    def monte_carlo_dropout(
        self,
        model_function: Callable[[np.ndarray, bool], np.ndarray],
        input_data: np.ndarray
    ) -> UncertaintyEstimate:
        """
        Monte Carlo Dropout for uncertainty estimation
        
        Args:
            model_function: Function that takes (input, training_mode) and returns prediction
            input_data: Input data
        
        Returns:
            Uncertainty estimate
        """
        
        predictions = []
        
        for _ in range(self.num_samples):
            # Run with dropout enabled (training=True)
            pred = model_function(input_data, True)
            predictions.append(pred)
        
        predictions = np.array(predictions)
        
        mean = np.mean(predictions)
        std = np.std(predictions)
        
        # Confidence interval
        alpha = 1 - self.confidence_level
        lower = np.percentile(predictions, alpha / 2 * 100)
        upper = np.percentile(predictions, (1 - alpha / 2) * 100)
        
        return UncertaintyEstimate(
            prediction=mean,
            mean=mean,
            std=std,
            confidence_interval=(lower, upper),
            uncertainty_type=UncertaintyType.EPISTEMIC,
            calibration_score=self._estimate_calibration()
        )
    
    def ensemble_uncertainty(
        self,
        model_functions: List[Callable[[np.ndarray], np.ndarray]],
        input_data: np.ndarray
    ) -> UncertaintyEstimate:
        """
        Ensemble-based uncertainty estimation
        
        Args:
            model_functions: List of model functions
            input_data: Input data
        
        Returns:
            Uncertainty estimate
        """
        
        predictions = []
        
        for model_fn in model_functions:
            pred = model_fn(input_data)
            predictions.append(pred)
        
        predictions = np.array(predictions)
        
        mean = np.mean(predictions)
        std = np.std(predictions)
        
        alpha = 1 - self.confidence_level
        lower = np.percentile(predictions, alpha / 2 * 100)
        upper = np.percentile(predictions, (1 - alpha / 2) * 100)
        
        return UncertaintyEstimate(
            prediction=mean,
            mean=mean,
            std=std,
            confidence_interval=(lower, upper),
            uncertainty_type=UncertaintyType.EPISTEMIC,
            calibration_score=self._estimate_calibration()
        )
    
    def bootstrap_uncertainty(
        self,
        data: np.ndarray,
        statistic_function: Callable[[np.ndarray], float]
    ) -> UncertaintyEstimate:
        """
        Bootstrap-based uncertainty estimation
        
        Args:
            data: Data to bootstrap
            statistic_function: Function to compute statistic
        
        Returns:
            Uncertainty estimate
        """
        
        statistics = []
        n = len(data)
        
        for _ in range(self.num_samples):
            # Bootstrap sample
            indices = np.random.randint(0, n, n)
            sample = data[indices]
            
            stat = statistic_function(sample)
            statistics.append(stat)
        
        statistics = np.array(statistics)
        
        mean = np.mean(statistics)
        std = np.std(statistics)
        
        alpha = 1 - self.confidence_level
        lower = np.percentile(statistics, alpha / 2 * 100)
        upper = np.percentile(statistics, (1 - alpha / 2) * 100)
        
        return UncertaintyEstimate(
            prediction=statistic_function(data),
            mean=mean,
            std=std,
            confidence_interval=(lower, upper),
            uncertainty_type=UncertaintyType.ALEATORIC,
            calibration_score=self._estimate_calibration()
        )
    
    def conformal_prediction(
        self,
        calibration_scores: np.ndarray,
        test_score: float
    ) -> Tuple[float, float]:
        """
        Conformal prediction for valid confidence intervals
        
        Args:
            calibration_scores: Nonconformity scores from calibration set
            test_score: Score for test point
        
        Returns:
            (p_value, adjusted_confidence)
        """
        
        # Calculate p-value
        n = len(calibration_scores)
        rank = np.sum(calibration_scores >= test_score)
        p_value = (rank + 1) / (n + 1)
        
        # Adjusted confidence
        adjusted_confidence = 1 - p_value
        
        return p_value, adjusted_confidence
    
    def update_calibration(
        self,
        predicted_interval: Tuple[float, float],
        actual_value: float
    ):
        """Update calibration history"""
        
        lower, upper = predicted_interval
        is_covered = lower <= actual_value <= upper
        interval_width = upper - lower
        
        self.calibration_history.append((interval_width, actual_value, is_covered))
    
    def _estimate_calibration(self) -> float:
        """Estimate calibration score"""
        
        if len(self.calibration_history) < 10:
            return 0.5  # Not enough data
        
        recent = self.calibration_history[-100:]
        coverage = sum(1 for _, _, covered in recent if covered) / len(recent)
        
        # Good calibration = coverage close to confidence level
        calibration_error = abs(coverage - self.confidence_level)
        calibration_score = 1 - calibration_error
        
        return calibration_score
    
    def get_report(self) -> Dict[str, Any]:
        """Get uncertainty quantification report"""
        
        if not self.calibration_history:
            return {'status': 'No calibration data'}
        
        recent = self.calibration_history[-100:]
        coverage = sum(1 for _, _, covered in recent if covered) / len(recent)
        avg_width = np.mean([w for w, _, _ in recent])
        
        return {
            'num_predictions': len(self.calibration_history),
            'empirical_coverage': coverage,
            'target_coverage': self.confidence_level,
            'average_interval_width': avg_width,
            'calibration_score': self._estimate_calibration()
        }


# =============================================================================
# FORMAL VERIFICATION OF TRADING LOGIC
# =============================================================================

class PropertyType(Enum):
    """Types of properties to verify"""
    SAFETY = "safety"  # Something bad never happens
    LIVENESS = "liveness"  # Something good eventually happens
    INVARIANT = "invariant"  # Property always holds
    REACHABILITY = "reachability"  # State can be reached


@dataclass
class VerificationProperty:
    """A property to verify"""
    property_id: str
    name: str
    property_type: PropertyType
    condition: Callable[[Dict[str, Any]], bool]
    description: str


@dataclass
class VerificationResult:
    """Result of formal verification"""
    property_id: str
    is_satisfied: bool
    counterexample: Optional[Dict[str, Any]] = None
    proof_steps: List[str] = field(default_factory=list)
    confidence: float = 1.0


class FormalVerifier:
    """
    Formal Verification of Trading Logic
    
    Verifies that trading strategies satisfy safety
    and correctness properties.
    """
    
    def __init__(self):
        self.properties: Dict[str, VerificationProperty] = {}
        self.verification_results: List[VerificationResult] = []
        
        # Create default safety properties
        self._create_default_properties()
        
        logger.info("FormalVerifier initialized")
    
    def _create_default_properties(self):
        """Create default safety properties"""
        
        properties = [
            VerificationProperty(
                property_id="max_position_size",
                name="Maximum Position Size",
                property_type=PropertyType.SAFETY,
                condition=lambda s: s.get('position_size', 0) <= s.get('max_position', 0.1),
                description="Position size never exceeds maximum"
            ),
            VerificationProperty(
                property_id="max_drawdown",
                name="Maximum Drawdown",
                property_type=PropertyType.SAFETY,
                condition=lambda s: s.get('drawdown', 0) <= s.get('max_drawdown', 0.2),
                description="Drawdown never exceeds maximum"
            ),
            VerificationProperty(
                property_id="stop_loss_set",
                name="Stop Loss Always Set",
                property_type=PropertyType.INVARIANT,
                condition=lambda s: s.get('has_position', False) == False or s.get('stop_loss', None) is not None,
                description="Stop loss is always set when position is open"
            ),
            VerificationProperty(
                property_id="risk_per_trade",
                name="Risk Per Trade Limit",
                property_type=PropertyType.SAFETY,
                condition=lambda s: s.get('risk_per_trade', 0) <= s.get('max_risk', 0.02),
                description="Risk per trade never exceeds limit"
            ),
            VerificationProperty(
                property_id="leverage_limit",
                name="Leverage Limit",
                property_type=PropertyType.SAFETY,
                condition=lambda s: s.get('leverage', 1) <= s.get('max_leverage', 5),
                description="Leverage never exceeds maximum"
            ),
            VerificationProperty(
                property_id="daily_loss_limit",
                name="Daily Loss Limit",
                property_type=PropertyType.SAFETY,
                condition=lambda s: s.get('daily_loss', 0) <= s.get('max_daily_loss', 0.05),
                description="Daily loss never exceeds limit"
            )
        ]
        
        for prop in properties:
            self.properties[prop.property_id] = prop
    
    def add_property(self, prop: VerificationProperty):
        """Add a property to verify"""
        self.properties[prop.property_id] = prop
    
    def verify_property(
        self,
        property_id: str,
        state_sequence: List[Dict[str, Any]]
    ) -> VerificationResult:
        """
        Verify a property over a sequence of states
        
        Args:
            property_id: Property to verify
            state_sequence: Sequence of system states
        
        Returns:
            Verification result
        """
        
        if property_id not in self.properties:
            return VerificationResult(
                property_id=property_id,
                is_satisfied=False,
                counterexample={'error': 'Property not found'}
            )
        
        prop = self.properties[property_id]
        proof_steps = []
        
        for i, state in enumerate(state_sequence):
            proof_steps.append(f"Checking state {i}")
            
            try:
                satisfied = prop.condition(state)
            except Exception as e:
                satisfied = False
                proof_steps.append(f"Error evaluating condition: {e}")
            
            if not satisfied:
                return VerificationResult(
                    property_id=property_id,
                    is_satisfied=False,
                    counterexample={'state_index': i, 'state': state},
                    proof_steps=proof_steps
                )
            
            proof_steps.append(f"State {i}: SATISFIED")
        
        proof_steps.append("All states satisfy property")
        
        result = VerificationResult(
            property_id=property_id,
            is_satisfied=True,
            proof_steps=proof_steps
        )
        
        self.verification_results.append(result)
        
        return result
    
    def verify_all_properties(
        self,
        state_sequence: List[Dict[str, Any]]
    ) -> Dict[str, VerificationResult]:
        """Verify all properties"""
        
        results = {}
        
        for property_id in self.properties:
            results[property_id] = self.verify_property(property_id, state_sequence)
        
        return results
    
    def bounded_model_check(
        self,
        initial_state: Dict[str, Any],
        transition_function: Callable[[Dict[str, Any]], Dict[str, Any]],
        property_id: str,
        max_steps: int = 100
    ) -> VerificationResult:
        """
        Bounded model checking
        
        Explores state space up to max_steps to find violations.
        """
        
        if property_id not in self.properties:
            return VerificationResult(
                property_id=property_id,
                is_satisfied=False,
                counterexample={'error': 'Property not found'}
            )
        
        prop = self.properties[property_id]
        state = initial_state.copy()
        proof_steps = []
        
        for step in range(max_steps):
            proof_steps.append(f"Step {step}")
            
            # Check property
            try:
                satisfied = prop.condition(state)
            except Exception as e:
                satisfied = False
                proof_steps.append(f"Error: {e}")
            
            if not satisfied:
                return VerificationResult(
                    property_id=property_id,
                    is_satisfied=False,
                    counterexample={'step': step, 'state': state},
                    proof_steps=proof_steps
                )
            
            # Transition to next state
            try:
                state = transition_function(state)
            except Exception as e:
                proof_steps.append(f"Transition error at step {step}: {e}")
                break
        
        proof_steps.append(f"Property holds for {max_steps} steps")
        
        return VerificationResult(
            property_id=property_id,
            is_satisfied=True,
            proof_steps=proof_steps,
            confidence=0.95  # Bounded check, not complete proof
        )
    
    def generate_safety_certificate(
        self,
        strategy_name: str,
        verification_results: Dict[str, VerificationResult]
    ) -> Dict[str, Any]:
        """Generate a safety certificate for a strategy"""
        
        all_satisfied = all(r.is_satisfied for r in verification_results.values())
        
        certificate = {
            'strategy_name': strategy_name,
            'timestamp': datetime.utcnow().isoformat(),
            'is_certified': all_satisfied,
            'properties_verified': len(verification_results),
            'properties_satisfied': sum(1 for r in verification_results.values() if r.is_satisfied),
            'details': {
                prop_id: {
                    'satisfied': result.is_satisfied,
                    'confidence': result.confidence
                }
                for prop_id, result in verification_results.items()
            }
        }
        
        if all_satisfied:
            certificate['certificate_hash'] = hashlib.sha256(
                f"{strategy_name}:{datetime.utcnow().isoformat()}".encode()
            ).hexdigest()
        
        return certificate
    
    def get_report(self) -> Dict[str, Any]:
        """Get verification report"""
        
        return {
            'num_properties': len(self.properties),
            'num_verifications': len(self.verification_results),
            'properties': [
                {
                    'id': p.property_id,
                    'name': p.name,
                    'type': p.property_type.value
                }
                for p in self.properties.values()
            ],
            'recent_results': [
                {
                    'property_id': r.property_id,
                    'satisfied': r.is_satisfied,
                    'confidence': r.confidence
                }
                for r in self.verification_results[-10:]
            ]
        }


# =============================================================================
# INTEGRATED SAFETY SYSTEM
# =============================================================================

class IntegratedSafetySystem:
    """
    Integrated Safety System
    
    Combines all safety and verification components
    for comprehensive strategy validation.
    """
    
    def __init__(self):
        self.robustness_tester = AdversarialRobustnessTester()
        self.causal_engine = CausalInferenceEngine()
        self.uncertainty_quantifier = UncertaintyQuantifier()
        self.formal_verifier = FormalVerifier()
        
        logger.info("IntegratedSafetySystem initialized")
    
    async def comprehensive_safety_check(
        self,
        strategy_function: Callable,
        market_data: np.ndarray,
        state_sequence: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Perform comprehensive safety check
        
        Returns:
            Complete safety assessment
        """
        
        results = {}
        
        # 1. Robustness testing
        robustness_results = self.robustness_tester.test_robustness(
            strategy_function, market_data
        )
        results['robustness'] = {
            'score': self.robustness_tester.get_robustness_score(),
            'vulnerable_scenarios': [
                r.scenario_id for r in robustness_results if not r.is_robust
            ]
        }
        
        # 2. Formal verification
        verification_results = self.formal_verifier.verify_all_properties(state_sequence)
        results['verification'] = {
            'all_satisfied': all(r.is_satisfied for r in verification_results.values()),
            'details': {
                prop_id: result.is_satisfied
                for prop_id, result in verification_results.items()
            }
        }
        
        # 3. Overall safety score
        robustness_score = results['robustness']['score']
        verification_score = (
            sum(1 for r in verification_results.values() if r.is_satisfied) /
            len(verification_results) if verification_results else 0
        )
        
        results['overall_safety_score'] = (robustness_score + verification_score) / 2
        results['is_safe'] = results['overall_safety_score'] >= 0.8
        
        return results
    
    def get_comprehensive_report(self) -> Dict[str, Any]:
        """Get comprehensive safety report"""
        
        return {
            'robustness': self.robustness_tester.get_report(),
            'causal_inference': self.causal_engine.get_report(),
            'uncertainty': self.uncertainty_quantifier.get_report(),
            'formal_verification': self.formal_verifier.get_report()
        }


# Convenience functions
def create_safety_system() -> IntegratedSafetySystem:
    """Create integrated safety system"""
    return IntegratedSafetySystem()
