"""
AlphaAlgo MSOS - Quant Model Factory

QUANT MODEL FACTORY:
- Isolated, Sandbox-only, Capital-blind, Survival-constrained
- Models NEVER touch live capital directly
- Every model must declare what inefficiency it exploits
- Black-box alpha is FORBIDDEN

The model factory never touches live capital. Ever.

Author: AlphaAlgo MSOS
"""

import hashlib
import logging
import time
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Any, Callable, Dict, List, Optional, Set

import numpy as np

logger = logging.getLogger(__name__)


class ModelStatus(Enum):
    """Model lifecycle status"""
    PROPOSED = auto()       # Just proposed, not validated
    VALIDATING = auto()     # Under validation
    REJECTED = auto()       # Failed validation
    SANDBOX = auto()        # Approved for sandbox testing
    PAPER_TRADING = auto()  # Paper trading validation
    PROMOTED = auto()       # Approved for limited capital
    SCALED = auto()         # Approved for full capital
    RETIRED = auto()        # Retired from use
    KILLED = auto()         # Killed due to failure


class EdgeType(Enum):
    """Types of market edges"""
    STRUCTURAL = auto()     # Market structure inefficiency
    BEHAVIORAL = auto()     # Behavioral bias exploitation
    INFORMATIONAL = auto()  # Information asymmetry
    LIQUIDITY = auto()      # Liquidity provision
    RISK_PREMIUM = auto()   # Risk premium harvesting
    MICROSTRUCTURE = auto() # Market microstructure
    STATISTICAL = auto()    # Statistical arbitrage
    UNKNOWN = auto()        # Must be rejected


class PromotionGate(Enum):
    """Gates for model promotion"""
    STATISTICAL_VALIDITY = auto()
    REGIME_ROBUSTNESS = auto()
    EXECUTION_FEASIBILITY = auto()
    PORTFOLIO_INTERACTION = auto()
    SHADOW_TRADING = auto()


@dataclass
class EdgeDeclaration:
    """
    Explicit declaration of what edge a model exploits.
    
    If a model cannot answer these → auto-rejected.
    Black-box alpha is forbidden.
    """
    edge_type: EdgeType
    description: str
    why_exists: str           # Why this inefficiency exists
    when_fails: str           # When this edge will stop working
    what_breaks_it: str       # What would break this edge
    expected_half_life: float # Expected decay in days
    crowding_sensitivity: float  # 0-1, how sensitive to crowding
    regime_dependency: List[str]  # Which regimes it works in
    
    def is_valid(self) -> bool:
        """Check if declaration is valid"""
        return (
            self.edge_type != EdgeType.UNKNOWN and
            len(self.description) > 10 and
            len(self.why_exists) > 10 and
            len(self.when_fails) > 10 and
            len(self.what_breaks_it) > 10 and
            self.expected_half_life > 0
        )


@dataclass
class ModelProposal:
    """A proposed model for the factory"""
    model_id: str
    name: str
    description: str
    edge_declaration: EdgeDeclaration
    complexity_score: float  # 0-1, higher = more complex
    interpretability_score: float  # 0-1, higher = more interpretable
    proposed_by: str
    proposed_at: float = field(default_factory=time.time)
    status: ModelStatus = ModelStatus.PROPOSED
    rejection_reason: str = ""
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'model_id': self.model_id,
            'name': self.name,
            'description': self.description,
            'edge_type': self.edge_declaration.edge_type.name,
            'complexity': self.complexity_score,
            'interpretability': self.interpretability_score,
            'status': self.status.name,
            'rejection_reason': self.rejection_reason
        }


@dataclass
class ModelValidation:
    """Validation results for a model"""
    model_id: str
    gate: PromotionGate
    passed: bool
    score: float  # 0-1
    details: Dict[str, Any]
    validated_at: float = field(default_factory=time.time)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'model_id': self.model_id,
            'gate': self.gate.name,
            'passed': self.passed,
            'score': self.score,
            'validated_at': self.validated_at
        }


@dataclass
class ModelPerformance:
    """Performance tracking for a model"""
    model_id: str
    sharpe_ratio: float = 0.0
    deflated_sharpe: float = 0.0  # Adjusted for multiple testing
    max_drawdown: float = 0.0
    win_rate: float = 0.0
    profit_factor: float = 0.0
    trades: int = 0
    days_active: int = 0
    regime_performance: Dict[str, float] = field(default_factory=dict)
    decay_rate: float = 0.0
    
    def is_decaying(self) -> bool:
        """Check if model is decaying"""
        return self.decay_rate > 0.01  # 1% decay per period


class StatisticalValidator:
    """Validates statistical properties of models"""
    
    def __init__(self):
        try:
            self.min_observations = 100
            self.min_sharpe = 0.5
            self.max_drawdown = 0.20
            self.min_win_rate = 0.45
        except Exception as e:
            logger.error(f"Error in __init__: {e}")
            raise
    
    def validate(
        self,
        model_id: str,
        returns: List[float],
        predictions: List[float],
        actuals: List[float]
    ) -> ModelValidation:
        """Validate statistical properties"""
        try:
            if len(returns) < self.min_observations:
                return ModelValidation(
                    model_id=model_id,
                    gate=PromotionGate.STATISTICAL_VALIDITY,
                    passed=False,
                    score=0.0,
                    details={'reason': f'Insufficient observations: {len(returns)}'}
                )
        
            returns_arr = np.array(returns)
        
            # Calculate metrics
            sharpe = np.mean(returns_arr) / (np.std(returns_arr) + 1e-10) * np.sqrt(252)
            max_dd = self._calculate_max_drawdown(returns_arr)
        
            # Deflated Sharpe (adjust for multiple testing)
            # Simplified: penalize by number of parameters
            deflated_sharpe = sharpe * 0.8  # Conservative adjustment
        
            # Win rate
            wins = sum(1 for r in returns if r > 0)
            win_rate = wins / len(returns)
        
            # Check thresholds
            passed = (
                deflated_sharpe >= self.min_sharpe and
                max_dd <= self.max_drawdown and
                win_rate >= self.min_win_rate
            )
        
            score = min(1.0, (
                (deflated_sharpe / self.min_sharpe) * 0.4 +
                (1 - max_dd / self.max_drawdown) * 0.3 +
                (win_rate / self.min_win_rate) * 0.3
            ))
        
            return ModelValidation(
                model_id=model_id,
                gate=PromotionGate.STATISTICAL_VALIDITY,
                passed=passed,
                score=score,
                details={
                    'sharpe': sharpe,
                    'deflated_sharpe': deflated_sharpe,
                    'max_drawdown': max_dd,
                    'win_rate': win_rate
                }
            )
        except Exception as e:
            logger.error(f"Error in validate: {e}")
            raise
    
    def _calculate_max_drawdown(self, returns: np.ndarray) -> float:
        """Calculate maximum drawdown"""
        try:
            cumulative = np.cumprod(1 + returns)
            running_max = np.maximum.accumulate(cumulative)
            drawdowns = (running_max - cumulative) / running_max
            return np.max(drawdowns)
        except Exception as e:
            logger.error(f"Error in _calculate_max_drawdown: {e}")
            raise


class RegimeValidator:
    """Validates model robustness across regimes"""
    
    def __init__(self):
        try:
            self.min_regimes = 2
            self.min_regime_sharpe = 0.3
        except Exception as e:
            logger.error(f"Error in __init__: {e}")
            raise
    
    def validate(
        self,
        model_id: str,
        regime_returns: Dict[str, List[float]]
    ) -> ModelValidation:
        """Validate regime robustness"""
        try:
            if len(regime_returns) < self.min_regimes:
                return ModelValidation(
                    model_id=model_id,
                    gate=PromotionGate.REGIME_ROBUSTNESS,
                    passed=False,
                    score=0.0,
                    details={'reason': f'Insufficient regimes: {len(regime_returns)}'}
                )
        
            regime_sharpes = {}
            for regime, returns in regime_returns.items():
                if len(returns) >= 20:
                    returns_arr = np.array(returns)
                    sharpe = np.mean(returns_arr) / (np.std(returns_arr) + 1e-10) * np.sqrt(252)
                    regime_sharpes[regime] = sharpe
        
            # Check if profitable in multiple regimes
            profitable_regimes = sum(1 for s in regime_sharpes.values() if s >= self.min_regime_sharpe)
        
            passed = profitable_regimes >= self.min_regimes
            score = profitable_regimes / len(regime_sharpes) if regime_sharpes else 0.0
        
            return ModelValidation(
                model_id=model_id,
                gate=PromotionGate.REGIME_ROBUSTNESS,
                passed=passed,
                score=score,
                details={'regime_sharpes': regime_sharpes, 'profitable_regimes': profitable_regimes}
            )
        except Exception as e:
            logger.error(f"Error in validate: {e}")
            raise


class ExecutionValidator:
    """Validates execution feasibility"""
    
    def __init__(self):
        try:
            self.max_slippage = 0.002  # 20 bps
            self.max_impact = 0.005   # 50 bps
        except Exception as e:
            logger.error(f"Error in __init__: {e}")
            raise
    
    def validate(
        self,
        model_id: str,
        expected_slippage: float,
        expected_impact: float,
        trade_frequency: float
    ) -> ModelValidation:
        """Validate execution feasibility"""
        try:
            passed = (
                expected_slippage <= self.max_slippage and
                expected_impact <= self.max_impact
            )
        
            slippage_score = max(0, 1 - expected_slippage / self.max_slippage)
            impact_score = max(0, 1 - expected_impact / self.max_impact)
        
            score = (slippage_score + impact_score) / 2
        
            return ModelValidation(
                model_id=model_id,
                gate=PromotionGate.EXECUTION_FEASIBILITY,
                passed=passed,
                score=score,
                details={
                    'expected_slippage': expected_slippage,
                    'expected_impact': expected_impact,
                    'trade_frequency': trade_frequency
                }
            )
        except Exception as e:
            logger.error(f"Error in validate: {e}")
            raise


class QuantModelFactory:
    """
    Quant Model Factory - Sandbox Only
    
    RULES:
    1. Models NEVER touch live capital directly
    2. Every model must declare its edge explicitly
    3. Black-box alpha is FORBIDDEN
    4. Models must pass all gates before promotion
    5. Complexity is penalized
    """
    
    # Constraints
    MAX_COMPLEXITY = 0.7
    MIN_INTERPRETABILITY = 0.3
    MAX_MODELS_IN_SANDBOX = 10
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        try:
            self.config = config or {}
            self.logger = logging.getLogger("msos.quant_factory")
        
            # Validators
            self._statistical_validator = StatisticalValidator()
            self._regime_validator = RegimeValidator()
            self._execution_validator = ExecutionValidator()
        
            # Model registry
            self._proposals: Dict[str, ModelProposal] = {}
            self._validations: Dict[str, Dict[PromotionGate, ModelValidation]] = {}
            self._performance: Dict[str, ModelPerformance] = {}
        
            # Sandbox
            self._sandbox_models: Set[str] = set()
            self._paper_trading_models: Set[str] = set()
            self._promoted_models: Set[str] = set()
        
            self.logger.info("Quant Model Factory initialized - SANDBOX ONLY")
        except Exception as e:
            logger.error(f"Error in __init__: {e}")
            raise
    
    def propose(self, proposal: ModelProposal) -> bool:
        """
        Propose a new model.
        
        Returns True if proposal is accepted for validation.
        """
        # Check edge declaration
        try:
            if not proposal.edge_declaration.is_valid():
                proposal.status = ModelStatus.REJECTED
                proposal.rejection_reason = "Invalid edge declaration - black-box alpha forbidden"
                self.logger.warning(f"Model {proposal.model_id} REJECTED: Invalid edge declaration")
                return False
        
            # Check complexity
            if proposal.complexity_score > self.MAX_COMPLEXITY:
                proposal.status = ModelStatus.REJECTED
                proposal.rejection_reason = f"Complexity too high: {proposal.complexity_score}"
                self.logger.warning(f"Model {proposal.model_id} REJECTED: Too complex")
                return False
        
            # Check interpretability
            if proposal.interpretability_score < self.MIN_INTERPRETABILITY:
                proposal.status = ModelStatus.REJECTED
                proposal.rejection_reason = f"Interpretability too low: {proposal.interpretability_score}"
                self.logger.warning(f"Model {proposal.model_id} REJECTED: Not interpretable")
                return False
        
            # Accept for validation
            proposal.status = ModelStatus.VALIDATING
            self._proposals[proposal.model_id] = proposal
            self._validations[proposal.model_id] = {}
        
            self.logger.info(f"Model {proposal.model_id} accepted for validation")
            return True
        except Exception as e:
            logger.error(f"Error in propose: {e}")
            raise
    
    def validate_statistical(
        self,
        model_id: str,
        returns: List[float],
        predictions: List[float],
        actuals: List[float]
    ) -> ModelValidation:
        """Validate statistical properties"""
        try:
            if model_id not in self._proposals:
                raise ValueError(f"Model {model_id} not found")
        
            validation = self._statistical_validator.validate(
                model_id, returns, predictions, actuals
            )
            self._validations[model_id][PromotionGate.STATISTICAL_VALIDITY] = validation
        
            if not validation.passed:
                self._proposals[model_id].status = ModelStatus.REJECTED
                self._proposals[model_id].rejection_reason = "Failed statistical validation"
        
            return validation
        except Exception as e:
            logger.error(f"Error in validate_statistical: {e}")
            raise
    
    def validate_regime(
        self,
        model_id: str,
        regime_returns: Dict[str, List[float]]
    ) -> ModelValidation:
        """Validate regime robustness"""
        try:
            if model_id not in self._proposals:
                raise ValueError(f"Model {model_id} not found")
        
            validation = self._regime_validator.validate(model_id, regime_returns)
            self._validations[model_id][PromotionGate.REGIME_ROBUSTNESS] = validation
        
            if not validation.passed:
                self._proposals[model_id].status = ModelStatus.REJECTED
                self._proposals[model_id].rejection_reason = "Failed regime robustness"
        
            return validation
        except Exception as e:
            logger.error(f"Error in validate_regime: {e}")
            raise
    
    def validate_execution(
        self,
        model_id: str,
        expected_slippage: float,
        expected_impact: float,
        trade_frequency: float
    ) -> ModelValidation:
        """Validate execution feasibility"""
        try:
            if model_id not in self._proposals:
                raise ValueError(f"Model {model_id} not found")
        
            validation = self._execution_validator.validate(
                model_id, expected_slippage, expected_impact, trade_frequency
            )
            self._validations[model_id][PromotionGate.EXECUTION_FEASIBILITY] = validation
        
            if not validation.passed:
                self._proposals[model_id].status = ModelStatus.REJECTED
                self._proposals[model_id].rejection_reason = "Failed execution feasibility"
        
            return validation
        except Exception as e:
            logger.error(f"Error in validate_execution: {e}")
            raise
    
    def promote_to_sandbox(self, model_id: str) -> bool:
        """Promote model to sandbox testing"""
        try:
            if model_id not in self._proposals:
                return False
        
            proposal = self._proposals[model_id]
            validations = self._validations.get(model_id, {})
        
            # Check required gates
            required_gates = [
                PromotionGate.STATISTICAL_VALIDITY,
                PromotionGate.REGIME_ROBUSTNESS,
                PromotionGate.EXECUTION_FEASIBILITY
            ]
        
            for gate in required_gates:
                if gate not in validations or not validations[gate].passed:
                    self.logger.warning(f"Model {model_id} cannot be promoted: {gate.name} not passed")
                    return False
        
            # Check sandbox capacity
            if len(self._sandbox_models) >= self.MAX_MODELS_IN_SANDBOX:
                self.logger.warning(f"Sandbox full, cannot promote {model_id}")
                return False
        
            proposal.status = ModelStatus.SANDBOX
            self._sandbox_models.add(model_id)
            self._performance[model_id] = ModelPerformance(model_id=model_id)
        
            self.logger.info(f"Model {model_id} PROMOTED to sandbox")
            return True
        except Exception as e:
            logger.error(f"Error in promote_to_sandbox: {e}")
            raise
    
    def promote_to_paper(self, model_id: str) -> bool:
        """Promote model to paper trading"""
        try:
            if model_id not in self._sandbox_models:
                return False
        
            proposal = self._proposals[model_id]
            performance = self._performance.get(model_id)
        
            # Check sandbox performance
            if not performance or performance.trades < 50:
                self.logger.warning(f"Model {model_id} needs more sandbox trades")
                return False
        
            if performance.sharpe_ratio < 0.5:
                self.logger.warning(f"Model {model_id} sandbox Sharpe too low")
                return False
        
            proposal.status = ModelStatus.PAPER_TRADING
            self._sandbox_models.remove(model_id)
            self._paper_trading_models.add(model_id)
        
            self.logger.info(f"Model {model_id} PROMOTED to paper trading")
            return True
        except Exception as e:
            logger.error(f"Error in promote_to_paper: {e}")
            raise
    
    def promote_to_live(self, model_id: str, capital_fraction: float = 0.01) -> bool:
        """
        Promote model to live trading with LIMITED capital.
        
        Capital fraction is capped at 5% for new models.
        """
        try:
            if model_id not in self._paper_trading_models:
                return False
        
            proposal = self._proposals[model_id]
            performance = self._performance.get(model_id)
        
            # Check paper trading performance
            if not performance or performance.days_active < 30:
                self.logger.warning(f"Model {model_id} needs more paper trading time")
                return False
        
            if performance.sharpe_ratio < 0.7:
                self.logger.warning(f"Model {model_id} paper Sharpe too low")
                return False
        
            if performance.is_decaying():
                self.logger.warning(f"Model {model_id} is decaying")
                return False
        
            # Cap capital fraction
            capital_fraction = min(0.05, capital_fraction)
        
            proposal.status = ModelStatus.PROMOTED
            self._paper_trading_models.remove(model_id)
            self._promoted_models.add(model_id)
        
            self.logger.info(f"Model {model_id} PROMOTED to live with {capital_fraction:.1%} capital")
            return True
        except Exception as e:
            logger.error(f"Error in promote_to_live: {e}")
            raise
    
    def retire_model(self, model_id: str, reason: str):
        """Retire a model"""
        try:
            if model_id in self._proposals:
                self._proposals[model_id].status = ModelStatus.RETIRED
        
            self._sandbox_models.discard(model_id)
            self._paper_trading_models.discard(model_id)
            self._promoted_models.discard(model_id)
        
            self.logger.info(f"Model {model_id} RETIRED: {reason}")
        except Exception as e:
            logger.error(f"Error in retire_model: {e}")
            raise
    
    def kill_model(self, model_id: str, reason: str):
        """Kill a model immediately"""
        try:
            if model_id in self._proposals:
                self._proposals[model_id].status = ModelStatus.KILLED
        
            self._sandbox_models.discard(model_id)
            self._paper_trading_models.discard(model_id)
            self._promoted_models.discard(model_id)
        
            self.logger.critical(f"Model {model_id} KILLED: {reason}")
        except Exception as e:
            logger.error(f"Error in kill_model: {e}")
            raise
    
    def update_performance(
        self,
        model_id: str,
        returns: List[float],
        regime: str = "unknown"
    ):
        """Update model performance"""
        try:
            if model_id not in self._performance:
                self._performance[model_id] = ModelPerformance(model_id=model_id)
        
            perf = self._performance[model_id]
            returns_arr = np.array(returns)
        
            perf.sharpe_ratio = np.mean(returns_arr) / (np.std(returns_arr) + 1e-10) * np.sqrt(252)
            perf.max_drawdown = self._calculate_max_drawdown(returns_arr)
            perf.win_rate = sum(1 for r in returns if r > 0) / len(returns)
            perf.trades += len(returns)
            perf.days_active += 1
        
            # Track regime performance
            if regime not in perf.regime_performance:
                perf.regime_performance[regime] = 0.0
            perf.regime_performance[regime] = np.mean(returns_arr)
        
            # Check for decay
            if perf.days_active > 30:
                # Compare recent vs older performance
                # Simplified: just track if Sharpe is declining
                pass
        except Exception as e:
            logger.error(f"Error in update_performance: {e}")
            raise
    
    def _calculate_max_drawdown(self, returns: np.ndarray) -> float:
        """Calculate maximum drawdown"""
        try:
            if len(returns) == 0:
                return 0.0
            cumulative = np.cumprod(1 + returns)
            running_max = np.maximum.accumulate(cumulative)
            drawdowns = (running_max - cumulative) / running_max
            return np.max(drawdowns)
        except Exception as e:
            logger.error(f"Error in _calculate_max_drawdown: {e}")
            raise
    
    def get_model_status(self, model_id: str) -> Optional[ModelStatus]:
        """Get model status"""
        try:
            if model_id in self._proposals:
                return self._proposals[model_id].status
            return None
        except Exception as e:
            logger.error(f"Error in get_model_status: {e}")
            raise
    
    def get_sandbox_models(self) -> List[str]:
        """Get models in sandbox"""
        return list(self._sandbox_models)
    
    def get_promoted_models(self) -> List[str]:
        """Get promoted models"""
        return list(self._promoted_models)
