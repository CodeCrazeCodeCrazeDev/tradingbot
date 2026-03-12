"""
AlphaAlgo Institutional - Layer 3: Quantitative Research
=========================================================

The Quantitative Research Layer is responsible for:
- Designing quantitative models using cross-disciplinary inspiration
- Generating model hypotheses
- Mathematical formulation of trading strategies
- Expected failure mode analysis
- Model lifecycle management

This layer operates as the QUANTITATIVE RESEARCH LAB.

Model families inspired by:
- Mathematics: Probability, stochastic calculus, topology, graph theory, optimization
- Physics: Brownian motion, diffusion, entropy, phase transitions, chaos
- Biology: Evolution, mutation, predator-prey, neural adaptation, ecosystems
- Chemistry: Reaction kinetics, equilibrium, catalysts, inhibitors
- Nature & Complex Systems: Fractals, feedback loops, self-organization, emergence
- AI (Conservative): Bayesian inference, ensemble learning, anomaly detection
"""

import logging
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple, Callable
from enum import Enum
import numpy as np
from collections import defaultdict
import hashlib
import uuid

from .core_types import (
    ModelFamily, ModelStatus, ModelHypothesis, ModelPerformance,
    ModelDecision, MarketRegime, CommitteeType, CommitteeVote,
    CommitteeDecision, RiskLevel, SystemConstants
)

logger = logging.getLogger(__name__)


# =============================================================================
# MODEL TEMPLATES
# =============================================================================

@dataclass
class ModelTemplate:
    """Template for a quantitative model."""
    family: ModelFamily
    name: str
    description: str
    mathematical_basis: str
    parameters: Dict[str, Any]
    expected_sharpe: float
    expected_decay_days: int
    failure_modes: List[str]
    regime_suitability: List[MarketRegime]
    data_requirements: List[str]
    complexity_score: float  # 0-1, higher = more complex


@dataclass
class ModelInstance:
    """Instance of a quantitative model."""
    id: str = field(default_factory=lambda: str(uuid.uuid4())[:12])
    template: ModelTemplate = None
    parameters: Dict[str, Any] = field(default_factory=dict)
    status: ModelStatus = ModelStatus.HYPOTHESIS
    created_at: datetime = field(default_factory=datetime.utcnow)
    last_updated: datetime = field(default_factory=datetime.utcnow)
    performance: Optional[ModelPerformance] = None
    version: int = 1
    parent_id: Optional[str] = None
    
    def compute_hash(self) -> str:
        """Compute unique hash for model instance."""
        content = f"{self.template.name}{str(self.parameters)}{self.version}"
        return hashlib.sha256(content.encode()).hexdigest()[:16]


# =============================================================================
# MATHEMATICS-INSPIRED MODELS
# =============================================================================

class StochasticModelGenerator:
    """Generates stochastic calculus-based models."""
    
    def __init__(self):
        self.model_templates = self._create_templates()
    
    def _create_templates(self) -> List[ModelTemplate]:
        return [
            ModelTemplate(
                family=ModelFamily.STOCHASTIC,
                name="Ornstein-Uhlenbeck Mean Reversion",
                description="Mean-reverting process for spread trading",
                mathematical_basis="dX = θ(μ - X)dt + σdW",
                parameters={'theta': 0.5, 'mu': 0.0, 'sigma': 0.1},
                expected_sharpe=0.8,
                expected_decay_days=180,
                failure_modes=["Regime shift to trending", "Mean level shift", "Volatility explosion"],
                regime_suitability=[MarketRegime.CALM, MarketRegime.NORMAL],
                data_requirements=["price_series", "spread_series"],
                complexity_score=0.4
            ),
            ModelTemplate(
                family=ModelFamily.STOCHASTIC,
                name="Jump-Diffusion Model",
                description="Captures sudden price jumps with continuous diffusion",
                mathematical_basis="dS = μSdt + σSdW + JdN",
                parameters={'mu': 0.05, 'sigma': 0.2, 'lambda': 0.1, 'jump_mean': 0.0, 'jump_std': 0.05},
                expected_sharpe=0.6,
                expected_decay_days=120,
                failure_modes=["Jump clustering", "Volatility regime change", "Correlation breakdown"],
                regime_suitability=[MarketRegime.VOLATILE, MarketRegime.NORMAL],
                data_requirements=["price_series", "volume_series", "jump_indicators"],
                complexity_score=0.6
            ),
            ModelTemplate(
                family=ModelFamily.STOCHASTIC,
                name="Heston Stochastic Volatility",
                description="Stochastic volatility for options and volatility trading",
                mathematical_basis="dv = κ(θ - v)dt + ξ√v dW",
                parameters={'kappa': 2.0, 'theta': 0.04, 'xi': 0.3, 'rho': -0.7},
                expected_sharpe=0.7,
                expected_decay_days=150,
                failure_modes=["Vol-of-vol regime change", "Correlation instability", "Mean level shift"],
                regime_suitability=[MarketRegime.VOLATILE, MarketRegime.NORMAL, MarketRegime.CALM],
                data_requirements=["price_series", "implied_vol_surface", "realized_vol"],
                complexity_score=0.7
            )
        ]
    
    def generate_hypothesis(self, market_conditions: Dict[str, Any]) -> List[ModelHypothesis]:
        """Generate model hypotheses based on market conditions."""
        hypotheses = []
        
        for template in self.model_templates:
            # Check regime suitability
            current_regime = market_conditions.get('regime', MarketRegime.NORMAL)
            if current_regime not in template.regime_suitability:
                continue
            
            hypothesis = ModelHypothesis(
                name=template.name,
                family=template.family,
                description=template.description,
                mathematical_basis=template.mathematical_basis,
                expected_edge=template.expected_sharpe,
                expected_decay_rate=1.0 / template.expected_decay_days,
                failure_modes=template.failure_modes,
                regime_dependencies=template.regime_suitability,
                data_requirements=template.data_requirements
            )
            hypotheses.append(hypothesis)
        
        return hypotheses


class OptimizationModelGenerator:
    """Generates optimization-based models."""
    
    def __init__(self):
        self.model_templates = self._create_templates()
    
    def _create_templates(self) -> List[ModelTemplate]:
        return [
            ModelTemplate(
                family=ModelFamily.OPTIMIZATION,
                name="Mean-Variance Optimization",
                description="Markowitz portfolio optimization with constraints",
                mathematical_basis="max(μᵀw - λwᵀΣw) s.t. constraints",
                parameters={'risk_aversion': 2.0, 'max_weight': 0.1, 'min_weight': 0.0},
                expected_sharpe=0.5,
                expected_decay_days=90,
                failure_modes=["Estimation error", "Correlation breakdown", "Fat tails"],
                regime_suitability=[MarketRegime.CALM, MarketRegime.NORMAL],
                data_requirements=["returns_matrix", "covariance_matrix"],
                complexity_score=0.5
            ),
            ModelTemplate(
                family=ModelFamily.OPTIMIZATION,
                name="Risk Parity Optimization",
                description="Equal risk contribution portfolio",
                mathematical_basis="min Σ(RC_i - RC_target)² s.t. constraints",
                parameters={'target_vol': 0.10, 'leverage_limit': 2.0},
                expected_sharpe=0.6,
                expected_decay_days=180,
                failure_modes=["Correlation spike", "Volatility regime change", "Leverage constraints"],
                regime_suitability=[MarketRegime.CALM, MarketRegime.NORMAL, MarketRegime.VOLATILE],
                data_requirements=["returns_matrix", "covariance_matrix", "volatility_forecasts"],
                complexity_score=0.5
            ),
            ModelTemplate(
                family=ModelFamily.OPTIMIZATION,
                name="CVaR Optimization",
                description="Conditional Value-at-Risk minimization",
                mathematical_basis="min CVaR_α(portfolio) s.t. return >= target",
                parameters={'alpha': 0.05, 'target_return': 0.10},
                expected_sharpe=0.55,
                expected_decay_days=120,
                failure_modes=["Tail distribution change", "Scenario coverage", "Optimization instability"],
                regime_suitability=[MarketRegime.VOLATILE, MarketRegime.NORMAL],
                data_requirements=["returns_matrix", "scenario_matrix", "tail_estimates"],
                complexity_score=0.6
            )
        ]
    
    def generate_hypothesis(self, market_conditions: Dict[str, Any]) -> List[ModelHypothesis]:
        """Generate optimization model hypotheses."""
        hypotheses = []
        
        for template in self.model_templates:
            current_regime = market_conditions.get('regime', MarketRegime.NORMAL)
            if current_regime not in template.regime_suitability:
                continue
            
            hypothesis = ModelHypothesis(
                name=template.name,
                family=template.family,
                description=template.description,
                mathematical_basis=template.mathematical_basis,
                expected_edge=template.expected_sharpe,
                expected_decay_rate=1.0 / template.expected_decay_days,
                failure_modes=template.failure_modes,
                regime_dependencies=template.regime_suitability,
                data_requirements=template.data_requirements
            )
            hypotheses.append(hypothesis)
        
        return hypotheses


# =============================================================================
# PHYSICS-INSPIRED MODELS
# =============================================================================

class PhysicsModelGenerator:
    """Generates physics-inspired models."""
    
    def __init__(self):
        self.model_templates = self._create_templates()
    
    def _create_templates(self) -> List[ModelTemplate]:
        return [
            ModelTemplate(
                family=ModelFamily.ENTROPY,
                name="Entropy-Based Market State",
                description="Uses information entropy to detect market state changes",
                mathematical_basis="H(X) = -Σ p(x) log p(x)",
                parameters={'window': 20, 'entropy_threshold': 0.7},
                expected_sharpe=0.5,
                expected_decay_days=90,
                failure_modes=["Distribution shift", "Non-stationarity", "Sample size"],
                regime_suitability=[MarketRegime.NORMAL, MarketRegime.VOLATILE, MarketRegime.TRANSITION],
                data_requirements=["returns_distribution", "volume_distribution"],
                complexity_score=0.5
            ),
            ModelTemplate(
                family=ModelFamily.PHASE_TRANSITION,
                name="Phase Transition Detector",
                description="Detects critical transitions in market dynamics",
                mathematical_basis="Order parameter near critical point",
                parameters={'critical_threshold': 0.8, 'lookback': 60},
                expected_sharpe=0.7,
                expected_decay_days=60,
                failure_modes=["False positives", "Delayed detection", "Multiple transitions"],
                regime_suitability=[MarketRegime.TRANSITION, MarketRegime.VOLATILE],
                data_requirements=["volatility_series", "correlation_matrix", "volume_series"],
                complexity_score=0.7
            ),
            ModelTemplate(
                family=ModelFamily.CHAOS,
                name="Lyapunov Exponent Tracker",
                description="Measures chaos/predictability in price dynamics",
                mathematical_basis="λ = lim(1/t) ln|δZ(t)/δZ(0)|",
                parameters={'embedding_dim': 3, 'delay': 1},
                expected_sharpe=0.4,
                expected_decay_days=45,
                failure_modes=["Noise sensitivity", "Embedding choice", "Non-stationarity"],
                regime_suitability=[MarketRegime.VOLATILE, MarketRegime.TRENDING],
                data_requirements=["high_frequency_prices", "tick_data"],
                complexity_score=0.8
            ),
            ModelTemplate(
                family=ModelFamily.RESONANCE,
                name="Market Resonance Model",
                description="Detects resonance patterns in price oscillations",
                mathematical_basis="Fourier analysis with damping",
                parameters={'min_period': 5, 'max_period': 60, 'damping': 0.1},
                expected_sharpe=0.5,
                expected_decay_days=30,
                failure_modes=["Frequency drift", "Damping changes", "Noise interference"],
                regime_suitability=[MarketRegime.CALM, MarketRegime.NORMAL],
                data_requirements=["price_series", "volume_series"],
                complexity_score=0.6
            )
        ]
    
    def generate_hypothesis(self, market_conditions: Dict[str, Any]) -> List[ModelHypothesis]:
        """Generate physics-inspired model hypotheses."""
        hypotheses = []
        
        for template in self.model_templates:
            current_regime = market_conditions.get('regime', MarketRegime.NORMAL)
            if current_regime not in template.regime_suitability:
                continue
            
            hypothesis = ModelHypothesis(
                name=template.name,
                family=template.family,
                description=template.description,
                mathematical_basis=template.mathematical_basis,
                expected_edge=template.expected_sharpe,
                expected_decay_rate=1.0 / template.expected_decay_days,
                failure_modes=template.failure_modes,
                regime_dependencies=template.regime_suitability,
                data_requirements=template.data_requirements
            )
            hypotheses.append(hypothesis)
        
        return hypotheses


# =============================================================================
# BIOLOGY-INSPIRED MODELS
# =============================================================================

class BiologyModelGenerator:
    """Generates biology-inspired models."""
    
    def __init__(self):
        self.model_templates = self._create_templates()
    
    def _create_templates(self) -> List[ModelTemplate]:
        return [
            ModelTemplate(
                family=ModelFamily.EVOLUTIONARY,
                name="Evolutionary Strategy Selection",
                description="Evolves strategy population based on fitness",
                mathematical_basis="Fitness-proportionate selection with mutation",
                parameters={'population_size': 50, 'mutation_rate': 0.05, 'crossover_rate': 0.3},
                expected_sharpe=0.6,
                expected_decay_days=180,
                failure_modes=["Overfitting", "Premature convergence", "Fitness landscape shift"],
                regime_suitability=[MarketRegime.NORMAL, MarketRegime.CALM],
                data_requirements=["historical_returns", "strategy_parameters"],
                complexity_score=0.7
            ),
            ModelTemplate(
                family=ModelFamily.PREDATOR_PREY,
                name="Lotka-Volterra Market Dynamics",
                description="Models buyer/seller dynamics as predator-prey",
                mathematical_basis="dx/dt = αx - βxy, dy/dt = δxy - γy",
                parameters={'alpha': 0.1, 'beta': 0.02, 'delta': 0.01, 'gamma': 0.1},
                expected_sharpe=0.5,
                expected_decay_days=60,
                failure_modes=["Parameter instability", "External shocks", "Equilibrium shift"],
                regime_suitability=[MarketRegime.NORMAL, MarketRegime.VOLATILE],
                data_requirements=["order_flow", "buyer_seller_imbalance"],
                complexity_score=0.6
            ),
            ModelTemplate(
                family=ModelFamily.NEURAL,
                name="Hebbian Learning Adaptation",
                description="Adapts weights based on co-activation patterns",
                mathematical_basis="Δw = η * x * y (fire together, wire together)",
                parameters={'learning_rate': 0.01, 'decay': 0.001},
                expected_sharpe=0.55,
                expected_decay_days=90,
                failure_modes=["Catastrophic forgetting", "Overfitting", "Slow adaptation"],
                regime_suitability=[MarketRegime.NORMAL, MarketRegime.TRENDING],
                data_requirements=["feature_matrix", "target_returns"],
                complexity_score=0.6
            ),
            ModelTemplate(
                family=ModelFamily.ECOSYSTEM,
                name="Market Ecosystem Balance",
                description="Models market as ecosystem with multiple species",
                mathematical_basis="Multi-species Lotka-Volterra with carrying capacity",
                parameters={'n_species': 5, 'interaction_matrix': None},
                expected_sharpe=0.5,
                expected_decay_days=120,
                failure_modes=["Species extinction", "Cascade effects", "New species entry"],
                regime_suitability=[MarketRegime.NORMAL, MarketRegime.CALM],
                data_requirements=["participant_flows", "market_share_data"],
                complexity_score=0.8
            ),
            ModelTemplate(
                family=ModelFamily.SWARM,
                name="Swarm Intelligence Consensus",
                description="Uses swarm behavior for signal aggregation",
                mathematical_basis="Particle swarm optimization with social learning",
                parameters={'n_particles': 30, 'inertia': 0.7, 'cognitive': 1.5, 'social': 1.5},
                expected_sharpe=0.55,
                expected_decay_days=90,
                failure_modes=["Local optima", "Swarm collapse", "Parameter sensitivity"],
                regime_suitability=[MarketRegime.NORMAL, MarketRegime.VOLATILE],
                data_requirements=["multi_signal_matrix", "objective_function"],
                complexity_score=0.7
            )
        ]
    
    def generate_hypothesis(self, market_conditions: Dict[str, Any]) -> List[ModelHypothesis]:
        """Generate biology-inspired model hypotheses."""
        hypotheses = []
        
        for template in self.model_templates:
            current_regime = market_conditions.get('regime', MarketRegime.NORMAL)
            if current_regime not in template.regime_suitability:
                continue
            
            hypothesis = ModelHypothesis(
                name=template.name,
                family=template.family,
                description=template.description,
                mathematical_basis=template.mathematical_basis,
                expected_edge=template.expected_sharpe,
                expected_decay_rate=1.0 / template.expected_decay_days,
                failure_modes=template.failure_modes,
                regime_dependencies=template.regime_suitability,
                data_requirements=template.data_requirements
            )
            hypotheses.append(hypothesis)
        
        return hypotheses


# =============================================================================
# CHEMISTRY-INSPIRED MODELS
# =============================================================================

class ChemistryModelGenerator:
    """Generates chemistry-inspired models."""
    
    def __init__(self):
        self.model_templates = self._create_templates()
    
    def _create_templates(self) -> List[ModelTemplate]:
        return [
            ModelTemplate(
                family=ModelFamily.REACTION_KINETICS,
                name="Market Reaction Kinetics",
                description="Models price reactions as chemical kinetics",
                mathematical_basis="d[P]/dt = k[A][B] - k'[P]",
                parameters={'forward_rate': 0.1, 'reverse_rate': 0.05},
                expected_sharpe=0.5,
                expected_decay_days=60,
                failure_modes=["Rate constant shift", "Catalyst introduction", "Saturation"],
                regime_suitability=[MarketRegime.NORMAL, MarketRegime.VOLATILE],
                data_requirements=["order_flow", "price_impact_data"],
                complexity_score=0.5
            ),
            ModelTemplate(
                family=ModelFamily.EQUILIBRIUM,
                name="Market Equilibrium Model",
                description="Detects and trades deviations from equilibrium",
                mathematical_basis="K_eq = [Products]/[Reactants]",
                parameters={'equilibrium_constant': 1.0, 'tolerance': 0.1},
                expected_sharpe=0.6,
                expected_decay_days=90,
                failure_modes=["Equilibrium shift", "Non-equilibrium dynamics", "Multiple equilibria"],
                regime_suitability=[MarketRegime.CALM, MarketRegime.NORMAL],
                data_requirements=["spread_series", "fair_value_estimates"],
                complexity_score=0.4
            ),
            ModelTemplate(
                family=ModelFamily.CATALYST,
                name="Catalyst Event Detection",
                description="Identifies catalytic events that accelerate price moves",
                mathematical_basis="Rate enhancement from catalyst presence",
                parameters={'catalyst_threshold': 2.0, 'decay_time': 5},
                expected_sharpe=0.7,
                expected_decay_days=45,
                failure_modes=["False catalysts", "Delayed reaction", "Catalyst poisoning"],
                regime_suitability=[MarketRegime.VOLATILE, MarketRegime.TRENDING],
                data_requirements=["news_events", "volume_spikes", "price_acceleration"],
                complexity_score=0.6
            )
        ]
    
    def generate_hypothesis(self, market_conditions: Dict[str, Any]) -> List[ModelHypothesis]:
        """Generate chemistry-inspired model hypotheses."""
        hypotheses = []
        
        for template in self.model_templates:
            current_regime = market_conditions.get('regime', MarketRegime.NORMAL)
            if current_regime not in template.regime_suitability:
                continue
            
            hypothesis = ModelHypothesis(
                name=template.name,
                family=template.family,
                description=template.description,
                mathematical_basis=template.mathematical_basis,
                expected_edge=template.expected_sharpe,
                expected_decay_rate=1.0 / template.expected_decay_days,
                failure_modes=template.failure_modes,
                regime_dependencies=template.regime_suitability,
                data_requirements=template.data_requirements
            )
            hypotheses.append(hypothesis)
        
        return hypotheses


# =============================================================================
# COMPLEX SYSTEMS MODELS
# =============================================================================

class ComplexSystemsModelGenerator:
    """Generates complex systems-inspired models."""
    
    def __init__(self):
        self.model_templates = self._create_templates()
    
    def _create_templates(self) -> List[ModelTemplate]:
        return [
            ModelTemplate(
                family=ModelFamily.FRACTAL,
                name="Fractal Dimension Trading",
                description="Uses fractal dimension for regime detection",
                mathematical_basis="D = lim(log N(ε) / log(1/ε))",
                parameters={'min_scale': 5, 'max_scale': 100},
                expected_sharpe=0.5,
                expected_decay_days=60,
                failure_modes=["Scale dependence", "Non-stationarity", "Estimation error"],
                regime_suitability=[MarketRegime.NORMAL, MarketRegime.VOLATILE],
                data_requirements=["high_frequency_prices"],
                complexity_score=0.7
            ),
            ModelTemplate(
                family=ModelFamily.POWER_LAW,
                name="Power Law Tail Trading",
                description="Exploits power law distributions in returns",
                mathematical_basis="P(X > x) ~ x^(-α)",
                parameters={'alpha_threshold': 2.5, 'tail_percentile': 0.05},
                expected_sharpe=0.6,
                expected_decay_days=90,
                failure_modes=["Alpha instability", "Tail truncation", "Sample size"],
                regime_suitability=[MarketRegime.VOLATILE, MarketRegime.CRISIS],
                data_requirements=["returns_distribution", "tail_estimates"],
                complexity_score=0.6
            ),
            ModelTemplate(
                family=ModelFamily.FEEDBACK,
                name="Feedback Loop Detector",
                description="Identifies positive/negative feedback loops",
                mathematical_basis="System dynamics with feedback gain",
                parameters={'feedback_threshold': 0.5, 'loop_delay': 3},
                expected_sharpe=0.55,
                expected_decay_days=45,
                failure_modes=["Loop breakdown", "Delay changes", "External intervention"],
                regime_suitability=[MarketRegime.TRENDING, MarketRegime.VOLATILE],
                data_requirements=["price_series", "volume_series", "sentiment_data"],
                complexity_score=0.6
            ),
            ModelTemplate(
                family=ModelFamily.EMERGENCE,
                name="Emergent Pattern Recognition",
                description="Detects emergent patterns from micro-interactions",
                mathematical_basis="Agent-based emergence detection",
                parameters={'n_agents': 100, 'interaction_radius': 5},
                expected_sharpe=0.5,
                expected_decay_days=60,
                failure_modes=["Pattern instability", "Scale mismatch", "Noise interference"],
                regime_suitability=[MarketRegime.NORMAL, MarketRegime.TRANSITION],
                data_requirements=["order_book_data", 'trade_flow'],
                complexity_score=0.8
            )
        ]
    
    def generate_hypothesis(self, market_conditions: Dict[str, Any]) -> List[ModelHypothesis]:
        """Generate complex systems model hypotheses."""
        hypotheses = []
        
        for template in self.model_templates:
            current_regime = market_conditions.get('regime', MarketRegime.NORMAL)
            if current_regime not in template.regime_suitability:
                continue
            
            hypothesis = ModelHypothesis(
                name=template.name,
                family=template.family,
                description=template.description,
                mathematical_basis=template.mathematical_basis,
                expected_edge=template.expected_sharpe,
                expected_decay_rate=1.0 / template.expected_decay_days,
                failure_modes=template.failure_modes,
                regime_dependencies=template.regime_suitability,
                data_requirements=template.data_requirements
            )
            hypotheses.append(hypothesis)
        
        return hypotheses


# =============================================================================
# AI MODELS (CONSERVATIVE USE)
# =============================================================================

class AIModelGenerator:
    """Generates AI-based models (used conservatively)."""
    
    def __init__(self):
        self.model_templates = self._create_templates()
    
    def _create_templates(self) -> List[ModelTemplate]:
        return [
            ModelTemplate(
                family=ModelFamily.ENSEMBLE,
                name="Ensemble Model Aggregation",
                description="Combines multiple models with dynamic weighting",
                mathematical_basis="Weighted average with performance-based weights",
                parameters={'n_models': 10, 'weight_decay': 0.95},
                expected_sharpe=0.7,
                expected_decay_days=180,
                failure_modes=["Correlation among models", "Weight instability", "Model failure cascade"],
                regime_suitability=[MarketRegime.NORMAL, MarketRegime.CALM, MarketRegime.VOLATILE],
                data_requirements=["model_predictions", "model_performance"],
                complexity_score=0.5
            ),
            ModelTemplate(
                family=ModelFamily.BAYESIAN,
                name="Bayesian Model Averaging",
                description="Bayesian approach to model uncertainty",
                mathematical_basis="P(θ|D) ∝ P(D|θ)P(θ)",
                parameters={'prior_strength': 1.0, 'update_frequency': 'daily'},
                expected_sharpe=0.6,
                expected_decay_days=120,
                failure_modes=["Prior misspecification", "Likelihood misspecification", "Computational limits"],
                regime_suitability=[MarketRegime.NORMAL, MarketRegime.CALM],
                data_requirements=["model_predictions", 'historical_accuracy'],
                complexity_score=0.6
            ),
            ModelTemplate(
                family=ModelFamily.ANOMALY_DETECTION,
                name="Anomaly-Based Trading",
                description="Trades on detected market anomalies",
                mathematical_basis="Isolation Forest / One-Class SVM",
                parameters={'contamination': 0.05, 'n_estimators': 100},
                expected_sharpe=0.5,
                expected_decay_days=60,
                failure_modes=["Anomaly definition drift", "False positives", "Regime change"],
                regime_suitability=[MarketRegime.NORMAL, MarketRegime.VOLATILE],
                data_requirements=["feature_matrix", "historical_anomalies"],
                complexity_score=0.5
            ),
            ModelTemplate(
                family=ModelFamily.META_LEARNING,
                name="Meta-Learning Strategy Selector",
                description="Learns to select strategies based on market state",
                mathematical_basis="MAML-inspired fast adaptation",
                parameters={'meta_lr': 0.001, 'inner_lr': 0.01, 'n_inner_steps': 5},
                expected_sharpe=0.65,
                expected_decay_days=90,
                failure_modes=["Task distribution shift", "Overfitting to meta-task", "Slow adaptation"],
                regime_suitability=[MarketRegime.NORMAL, MarketRegime.TRANSITION],
                data_requirements=["strategy_performance", "market_features"],
                complexity_score=0.8
            )
        ]
    
    def generate_hypothesis(self, market_conditions: Dict[str, Any]) -> List[ModelHypothesis]:
        """Generate AI model hypotheses (conservative)."""
        hypotheses = []
        
        for template in self.model_templates:
            current_regime = market_conditions.get('regime', MarketRegime.NORMAL)
            if current_regime not in template.regime_suitability:
                continue
            
            hypothesis = ModelHypothesis(
                name=template.name,
                family=template.family,
                description=template.description,
                mathematical_basis=template.mathematical_basis,
                expected_edge=template.expected_sharpe,
                expected_decay_rate=1.0 / template.expected_decay_days,
                failure_modes=template.failure_modes,
                regime_dependencies=template.regime_suitability,
                data_requirements=template.data_requirements
            )
            hypotheses.append(hypothesis)
        
        return hypotheses


# =============================================================================
# QUANTITATIVE RESEARCH LAB
# =============================================================================

class QuantitativeResearchLab:
    """
    Internal committee responsible for quantitative model research.
    
    Designs models using cross-disciplinary inspiration:
    - Mathematics
    - Physics
    - Biology
    - Chemistry
    - Nature
    - Complex systems
    - AI (used conservatively)
    
    Produces:
    - Model hypotheses
    - Mathematical formulations
    - Expected failure modes
    
    NOT trades.
    """
    
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        self.committee_type = CommitteeType.QUANTITATIVE_RESEARCH
        
        # Initialize model generators
        self.generators = {
            'stochastic': StochasticModelGenerator(),
            'optimization': OptimizationModelGenerator(),
            'physics': PhysicsModelGenerator(),
            'biology': BiologyModelGenerator(),
            'chemistry': ChemistryModelGenerator(),
            'complex_systems': ComplexSystemsModelGenerator(),
            'ai': AIModelGenerator()
        }
        
        # Model registry
        self.hypotheses: Dict[str, ModelHypothesis] = {}
        self.instances: Dict[str, ModelInstance] = {}
        self.retired_models: List[str] = []
        
        # Research metrics
        self.hypotheses_generated = 0
        self.hypotheses_approved = 0
        self.hypotheses_killed = 0
        
        logger.info("QuantitativeResearchLab initialized")
    
    def generate_hypotheses(self, market_conditions: Dict[str, Any]) -> List[ModelHypothesis]:
        """
        Generate model hypotheses based on market conditions.
        
        Args:
            market_conditions: Current market state including regime
            
        Returns:
            List of ModelHypothesis objects
        """
        all_hypotheses = []
        
        for name, generator in self.generators.items():
            try:
                hypotheses = generator.generate_hypothesis(market_conditions)
                all_hypotheses.extend(hypotheses)
                logger.debug(f"Generated {len(hypotheses)} hypotheses from {name}")
            except Exception as e:
                logger.error(f"Error generating hypotheses from {name}: {e}")
        
        # Register hypotheses
        for hypothesis in all_hypotheses:
            self.hypotheses[hypothesis.id] = hypothesis
            self.hypotheses_generated += 1
        
        logger.info(f"Generated {len(all_hypotheses)} total hypotheses")
        return all_hypotheses
    
    def get_hypothesis(self, hypothesis_id: str) -> Optional[ModelHypothesis]:
        """Get a hypothesis by ID."""
        return self.hypotheses.get(hypothesis_id)
    
    def promote_to_development(self, hypothesis_id: str) -> Optional[ModelInstance]:
        """
        Promote a hypothesis to development status.
        
        Returns:
            ModelInstance if successful, None otherwise
        """
        hypothesis = self.hypotheses.get(hypothesis_id)
        if hypothesis is None:
            logger.warning(f"Hypothesis {hypothesis_id} not found")
            return None
        
        # Create model instance
        template = self._hypothesis_to_template(hypothesis)
        instance = ModelInstance(
            template=template,
            parameters=template.parameters.copy(),
            status=ModelStatus.DEVELOPMENT
        )
        
        self.instances[instance.id] = instance
        hypothesis.status = ModelStatus.DEVELOPMENT
        
        logger.info(f"Promoted hypothesis {hypothesis_id} to development as instance {instance.id}")
        return instance
    
    def update_model_status(self, instance_id: str, new_status: ModelStatus):
        """Update model instance status."""
        if instance_id in self.instances:
            self.instances[instance_id].status = new_status
            self.instances[instance_id].last_updated = datetime.utcnow()
            
            if new_status == ModelStatus.KILLED:
                self.hypotheses_killed += 1
                self.retired_models.append(instance_id)
            elif new_status == ModelStatus.LIVE:
                self.hypotheses_approved += 1
    
    def retire_model(self, instance_id: str, reason: str):
        """Retire a model."""
        if instance_id in self.instances:
            self.instances[instance_id].status = ModelStatus.RETIRED
            self.retired_models.append(instance_id)
            logger.info(f"Retired model {instance_id}: {reason}")
    
    def get_active_models(self) -> List[ModelInstance]:
        """Get all active (non-retired) models."""
        return [
            m for m in self.instances.values()
            if m.status not in [ModelStatus.RETIRED, ModelStatus.KILLED]
        ]
    
    def get_live_models(self) -> List[ModelInstance]:
        """Get all live models."""
        return [
            m for m in self.instances.values()
            if m.status == ModelStatus.LIVE
        ]
    
    def vote(self, hypothesis_id: str) -> CommitteeVote:
        """
        Cast a vote on a model hypothesis.
        
        Returns:
            CommitteeVote with research assessment
        """
        hypothesis = self.hypotheses.get(hypothesis_id)
        if hypothesis is None:
            return CommitteeVote(
                committee=self.committee_type,
                decision=CommitteeDecision.REJECT,
                confidence=1.0,
                rationale=f"Hypothesis {hypothesis_id} not found"
            )
        
        # Evaluate hypothesis quality
        quality_score = self._evaluate_hypothesis_quality(hypothesis)
        
        if quality_score >= 0.7:
            decision = CommitteeDecision.APPROVE
            rationale = f"Strong hypothesis: {hypothesis.name} (quality: {quality_score:.2f})"
        elif quality_score >= 0.5:
            decision = CommitteeDecision.CONDITIONAL
            rationale = f"Conditional approval: {hypothesis.name} (quality: {quality_score:.2f})"
        else:
            decision = CommitteeDecision.REJECT
            rationale = f"Weak hypothesis: {hypothesis.name} (quality: {quality_score:.2f})"
        
        conditions = []
        if hypothesis.expected_edge < 0.5:
            conditions.append("Requires additional edge validation")
        if len(hypothesis.failure_modes) > 3:
            conditions.append("Multiple failure modes - needs robust testing")
        
        return CommitteeVote(
            committee=self.committee_type,
            decision=decision,
            confidence=quality_score,
            rationale=rationale,
            conditions=conditions
        )
    
    def _evaluate_hypothesis_quality(self, hypothesis: ModelHypothesis) -> float:
        """Evaluate quality of a hypothesis."""
        score = 0.0
        
        # Expected edge contribution
        score += min(0.3, hypothesis.expected_edge * 0.3)
        
        # Mathematical basis clarity
        if hypothesis.mathematical_basis:
            score += 0.2
        
        # Failure mode awareness
        if hypothesis.failure_modes:
            score += min(0.2, len(hypothesis.failure_modes) * 0.05)
        
        # Data requirements clarity
        if hypothesis.data_requirements:
            score += 0.15
        
        # Regime awareness
        if hypothesis.regime_dependencies:
            score += 0.15
        
        return min(1.0, score)
    
    def _hypothesis_to_template(self, hypothesis: ModelHypothesis) -> ModelTemplate:
        """Convert hypothesis to model template."""
        return ModelTemplate(
            family=hypothesis.family,
            name=hypothesis.name,
            description=hypothesis.description,
            mathematical_basis=hypothesis.mathematical_basis,
            parameters={},
            expected_sharpe=hypothesis.expected_edge,
            expected_decay_days=int(1.0 / max(0.001, hypothesis.expected_decay_rate)),
            failure_modes=hypothesis.failure_modes,
            regime_suitability=hypothesis.regime_dependencies,
            data_requirements=hypothesis.data_requirements,
            complexity_score=0.5
        )
    
    def get_research_metrics(self) -> Dict[str, Any]:
        """Get research lab metrics."""
        return {
            'hypotheses_generated': self.hypotheses_generated,
            'hypotheses_approved': self.hypotheses_approved,
            'hypotheses_killed': self.hypotheses_killed,
            'survival_rate': self.hypotheses_approved / max(1, self.hypotheses_generated),
            'active_models': len(self.get_active_models()),
            'live_models': len(self.get_live_models()),
            'retired_models': len(self.retired_models)
        }


# =============================================================================
# QUANTITATIVE RESEARCH LAYER
# =============================================================================

class QuantitativeResearchLayer:
    """
    Layer 3: Quantitative Research Layer
    
    Responsible for:
    - Model hypothesis generation
    - Cross-disciplinary model design
    - Model lifecycle management
    - Research metrics tracking
    """
    
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        self.research_lab = QuantitativeResearchLab(self.config)
        
        # Layer state
        self.last_research_cycle: Optional[datetime] = None
        self.research_cycle_count = 0
        
        logger.info("QuantitativeResearchLayer initialized")
    
    def run_research_cycle(self, market_conditions: Dict[str, Any]) -> List[ModelHypothesis]:
        """
        Run a research cycle to generate new hypotheses.
        
        Args:
            market_conditions: Current market state
            
        Returns:
            List of generated hypotheses
        """
        hypotheses = self.research_lab.generate_hypotheses(market_conditions)
        self.last_research_cycle = datetime.utcnow()
        self.research_cycle_count += 1
        
        return hypotheses
    
    def evaluate_hypothesis(self, hypothesis_id: str) -> CommitteeVote:
        """Evaluate a hypothesis."""
        return self.research_lab.vote(hypothesis_id)
    
    def promote_hypothesis(self, hypothesis_id: str) -> Optional[ModelInstance]:
        """Promote a hypothesis to development."""
        return self.research_lab.promote_to_development(hypothesis_id)
    
    def get_active_models(self) -> List[ModelInstance]:
        """Get active models."""
        return self.research_lab.get_active_models()
    
    def get_live_models(self) -> List[ModelInstance]:
        """Get live models."""
        return self.research_lab.get_live_models()
    
    def retire_model(self, instance_id: str, reason: str):
        """Retire a model."""
        self.research_lab.retire_model(instance_id, reason)
    
    def update_model_status(self, instance_id: str, status: ModelStatus):
        """Update model status."""
        self.research_lab.update_model_status(instance_id, status)
    
    def get_layer_state(self) -> Dict[str, Any]:
        """Get current layer state."""
        return {
            'last_research_cycle': self.last_research_cycle.isoformat() if self.last_research_cycle else None,
            'research_cycle_count': self.research_cycle_count,
            'research_metrics': self.research_lab.get_research_metrics(),
            'model_families': list(self.research_lab.generators.keys())
        }
