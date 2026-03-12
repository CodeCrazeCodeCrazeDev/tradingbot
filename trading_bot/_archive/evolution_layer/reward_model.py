"""
AlphaAlgo Immutable Reward Model - THE UNCHANGEABLE OBJECTIVE

THIS FILE DEFINES WHAT "SUCCESS" MEANS FOR THE TRADING BOT.
THESE VALUES ARE FROZEN AND CANNOT BE MODIFIED BY THE EVOLUTION LAYER.

The reward model is the ONLY thing that guides all evolution and learning.
If you change this, you change the fundamental nature of the bot.

Version: 1.0.0 (FROZEN - DO NOT MODIFY)
"""

from dataclasses import dataclass, field
from typing import Any, Dict, Final, List, Optional
from datetime import datetime
import hashlib
import logging
from typing import Set

logger = logging.getLogger(__name__)


# =============================================================================
# IMMUTABLE CONSTANTS - THESE CANNOT BE CHANGED
# =============================================================================

# Risk Limits (FROZEN)
MAX_RISK_PER_TRADE: Final[float] = 0.02      # 2% max risk per trade
MAX_DAILY_LOSS: Final[float] = 0.05          # 5% max daily loss
MAX_WEEKLY_LOSS: Final[float] = 0.10         # 10% max weekly loss
MAX_MONTHLY_LOSS: Final[float] = 0.15        # 15% max monthly loss
MAX_DRAWDOWN: Final[float] = 0.20            # 20% max drawdown
MAX_POSITION_SIZE: Final[float] = 0.10       # 10% max position size
MAX_CORRELATION: Final[float] = 0.70         # 70% max correlation between positions
MAX_LEVERAGE: Final[float] = 3.0             # 3x max leverage

# Performance Targets (FROZEN)
MIN_SHARPE_RATIO: Final[float] = 1.0         # Minimum Sharpe ratio
MIN_SORTINO_RATIO: Final[float] = 1.5        # Minimum Sortino ratio
MIN_WIN_RATE: Final[float] = 0.40            # Minimum win rate (40%)
MIN_PROFIT_FACTOR: Final[float] = 1.2        # Minimum profit factor
MIN_RISK_REWARD: Final[float] = 1.5          # Minimum risk/reward ratio

# Ethical Constraints (FROZEN - CANNOT BE EVOLVED)
NO_MARKET_MANIPULATION: Final[bool] = True   # Never manipulate markets
NO_INSIDER_TRADING: Final[bool] = True       # Never use insider information
NO_FRONT_RUNNING: Final[bool] = True         # Never front-run other traders
HUMAN_OVERRIDE_ALWAYS: Final[bool] = True    # Human can always override
TRANSPARENT_OPERATIONS: Final[bool] = True   # All operations must be logged
REGULATORY_COMPLIANCE: Final[bool] = True    # Must comply with regulations

# Evolution Constraints (FROZEN - CANNOT BE EVOLVED)
CANNOT_MODIFY_REWARD_MODEL: Final[bool] = True  # Evolution cannot change this file
CANNOT_DISABLE_RISK_LIMITS: Final[bool] = True  # Evolution cannot disable risk
CANNOT_BYPASS_HUMAN_APPROVAL: Final[bool] = True  # Evolution cannot bypass humans
CANNOT_INCREASE_RISK_LIMITS: Final[bool] = True  # Evolution cannot increase risk


# =============================================================================
# REWARD COMPONENTS - FROZEN STRUCTURE
# =============================================================================

@dataclass(frozen=True)
class RewardComponents:
    """
    Components of the reward calculation - FROZEN STRUCTURE
    
    These weights determine how different aspects of trading contribute
    to the overall reward. The weights are IMMUTABLE.
    """
    
    # Profit Component (40% total weight)
    profit_weight: float = 0.20          # Raw profit contribution
    risk_adjusted_weight: float = 0.20   # Risk-adjusted returns (Sharpe)
    
    # Consistency Component (30% total weight)
    win_rate_weight: float = 0.10        # Win rate contribution
    profit_factor_weight: float = 0.10   # Profit factor contribution
    consistency_weight: float = 0.10     # Trade consistency
    
    # Risk Management Component (20% total weight)
    drawdown_penalty: float = 0.10       # Penalty for drawdown
    risk_control_weight: float = 0.10    # Reward for staying within limits
    
    # Execution Quality Component (10% total weight)
    slippage_penalty: float = 0.05       # Penalty for slippage
    execution_quality: float = 0.05      # Reward for good execution
    
    def validate(self) -> bool:
        """Validate that weights sum to 1.0"""
        total = (
            self.profit_weight + 
            self.risk_adjusted_weight +
            self.win_rate_weight +
            self.profit_factor_weight +
            self.consistency_weight +
            self.drawdown_penalty +
            self.risk_control_weight +
            self.slippage_penalty +
            self.execution_quality
        )
        return abs(total - 1.0) < 0.001


@dataclass(frozen=True)
class RewardConstraints:
    """
    Hard constraints that must never be violated - FROZEN
    
    If any of these constraints are violated, the reward is ZERO
    regardless of how profitable the trade was.
    """
    
    max_risk_per_trade: float = MAX_RISK_PER_TRADE
    max_daily_loss: float = MAX_DAILY_LOSS
    max_weekly_loss: float = MAX_WEEKLY_LOSS
    max_monthly_loss: float = MAX_MONTHLY_LOSS
    max_drawdown: float = MAX_DRAWDOWN
    max_position_size: float = MAX_POSITION_SIZE
    max_correlation: float = MAX_CORRELATION
    max_leverage: float = MAX_LEVERAGE
    
    min_sharpe_ratio: float = MIN_SHARPE_RATIO
    min_sortino_ratio: float = MIN_SORTINO_RATIO
    min_win_rate: float = MIN_WIN_RATE
    min_profit_factor: float = MIN_PROFIT_FACTOR
    min_risk_reward: float = MIN_RISK_REWARD


# =============================================================================
# IMMUTABLE REWARD MODEL - THE CORE
# =============================================================================

class ImmutableRewardModel:
    """
    THE REWARD MODEL THAT NEVER CHANGES
    
    This class defines what "success" means for the trading bot.
    Once instantiated, it CANNOT be modified.
    
    The evolution layer uses this to evaluate improvements.
    The learning layer uses this to update models.
    The execution layer uses this to validate trades.
    
    CRITICAL: This class is designed to be IMMUTABLE.
    Any attempt to modify it should fail.
    """
    
    # Class-level constants (cannot be changed)
    _FROZEN = True
    _VERSION = "1.0.0"
    _HASH = None  # Set on first instantiation
    
    def __init__(self):
        """Initialize the immutable reward model"""
        self._components = RewardComponents()
        self._constraints = RewardConstraints()
        self._creation_time = datetime.now()
        
        # Calculate hash of the model for integrity verification
        self._model_hash = self._calculate_hash()
        
        # Store class-level hash on first instantiation
        if ImmutableRewardModel._HASH is None:
            ImmutableRewardModel._HASH = self._model_hash
        
        logger.info(f"ImmutableRewardModel initialized (hash: {self._model_hash[:16]})")
    
    def _calculate_hash(self) -> str:
        """Calculate hash of the model for integrity verification"""
        data = (
            f"{MAX_RISK_PER_TRADE}{MAX_DAILY_LOSS}{MAX_DRAWDOWN}"
            f"{MIN_SHARPE_RATIO}{MIN_WIN_RATE}{MIN_PROFIT_FACTOR}"
            f"{self._components.profit_weight}{self._components.risk_adjusted_weight}"
        )
        return hashlib.sha256(data.encode()).hexdigest()
    
    def verify_integrity(self) -> bool:
        """Verify that the model has not been tampered with"""
        current_hash = self._calculate_hash()
        if current_hash != self._model_hash:
            logger.critical("REWARD MODEL INTEGRITY VIOLATION DETECTED!")
            return False
        return True
    
    @property
    def components(self) -> RewardComponents:
        """Get reward components (read-only)"""
        return self._components
    
    @property
    def constraints(self) -> RewardConstraints:
        """Get constraints (read-only)"""
        return self._constraints
    
    @property
    def version(self) -> str:
        """Get model version"""
        return self._VERSION
    
    @property
    def model_hash(self) -> str:
        """Get model hash for verification"""
        return self._model_hash
    
    # =========================================================================
    # REWARD CALCULATION - IMMUTABLE LOGIC
    # =========================================================================
    
    def calculate_reward(self, trade_result: Dict[str, Any]) -> float:
        """
        Calculate reward for a trade result - IMMUTABLE LOGIC
        
        This function CANNOT be modified by the evolution layer.
        
        Args:
            trade_result: Dictionary containing trade metrics:
                - pnl_percent: Profit/loss as percentage
                - sharpe_ratio: Risk-adjusted return
                - sortino_ratio: Downside risk-adjusted return
                - win_rate: Win rate (0-1)
                - profit_factor: Gross profit / gross loss
                - max_drawdown: Maximum drawdown (0-1)
                - risk_used: Risk used as percentage
                - slippage: Slippage in basis points
                - execution_time_ms: Execution time in milliseconds
        
        Returns:
            Reward value between -1.0 and 1.0
        """
        # Verify integrity first
        if not self.verify_integrity():
            logger.critical("Reward calculation blocked due to integrity violation")
            return 0.0
        
        # Check hard constraints first
        constraint_violations = self._check_constraints(trade_result)
        if constraint_violations:
            logger.warning(f"Constraint violations: {constraint_violations}")
            return -1.0  # Maximum penalty for constraint violations
        
        # Calculate individual components
        profit_reward = self._calculate_profit_reward(trade_result)
        consistency_reward = self._calculate_consistency_reward(trade_result)
        risk_reward = self._calculate_risk_reward(trade_result)
        execution_reward = self._calculate_execution_reward(trade_result)
        
        # Combine with weights
        total_reward = (
            profit_reward * (self._components.profit_weight + self._components.risk_adjusted_weight) +
            consistency_reward * (self._components.win_rate_weight + self._components.profit_factor_weight + self._components.consistency_weight) +
            risk_reward * (self._components.risk_control_weight - self._components.drawdown_penalty) +
            execution_reward * (self._components.execution_quality - self._components.slippage_penalty)
        )
        
        # Clamp to [-1, 1]
        return max(-1.0, min(1.0, total_reward))
    
    def _check_constraints(self, trade_result: Dict[str, Any]) -> List[str]:
        """Check if any hard constraints are violated"""
        violations = []
        
        # Risk constraints
        if trade_result.get('risk_used', 0) > self._constraints.max_risk_per_trade:
            violations.append(f"Risk per trade exceeded: {trade_result.get('risk_used', 0):.2%}")
        
        if trade_result.get('daily_loss', 0) > self._constraints.max_daily_loss:
            violations.append(f"Daily loss exceeded: {trade_result.get('daily_loss', 0):.2%}")
        
        if trade_result.get('max_drawdown', 0) > self._constraints.max_drawdown:
            violations.append(f"Max drawdown exceeded: {trade_result.get('max_drawdown', 0):.2%}")
        
        if trade_result.get('position_size', 0) > self._constraints.max_position_size:
            violations.append(f"Position size exceeded: {trade_result.get('position_size', 0):.2%}")
        
        if trade_result.get('leverage', 1) > self._constraints.max_leverage:
            violations.append(f"Leverage exceeded: {trade_result.get('leverage', 1):.1f}x")
        
        return violations
    
    def _calculate_profit_reward(self, trade_result: Dict[str, Any]) -> float:
        """Calculate profit component of reward"""
        pnl_percent = trade_result.get('pnl_percent', 0)
        sharpe = trade_result.get('sharpe_ratio', 0)
        
        # Normalize PnL (-10% to +10% maps to -1 to +1)
        pnl_normalized = max(-1.0, min(1.0, pnl_percent / 0.10))
        
        # Normalize Sharpe (0 to 3 maps to 0 to 1)
        sharpe_normalized = max(0.0, min(1.0, sharpe / 3.0))
        
        return (pnl_normalized + sharpe_normalized) / 2
    
    def _calculate_consistency_reward(self, trade_result: Dict[str, Any]) -> float:
        """Calculate consistency component of reward"""
        win_rate = trade_result.get('win_rate', 0.5)
        profit_factor = trade_result.get('profit_factor', 1.0)
        
        # Win rate reward (40% to 60% is neutral, above 60% is good)
        win_rate_reward = (win_rate - 0.5) * 2  # -1 to +1
        
        # Profit factor reward (1.0 is neutral, above 1.5 is good)
        pf_reward = (profit_factor - 1.0) / 1.0  # 0 to 1 for PF 1-2
        pf_reward = max(-1.0, min(1.0, pf_reward))
        
        return (win_rate_reward + pf_reward) / 2
    
    def _calculate_risk_reward(self, trade_result: Dict[str, Any]) -> float:
        """Calculate risk management component of reward"""
        max_drawdown = trade_result.get('max_drawdown', 0)
        risk_used = trade_result.get('risk_used', 0)
        
        # Drawdown penalty (0% is perfect, 20% is maximum allowed)
        drawdown_penalty = max_drawdown / self._constraints.max_drawdown
        
        # Risk control reward (using less risk than allowed is good)
        risk_control = 1.0 - (risk_used / self._constraints.max_risk_per_trade)
        
        return (risk_control - drawdown_penalty) / 2
    
    def _calculate_execution_reward(self, trade_result: Dict[str, Any]) -> float:
        """Calculate execution quality component of reward"""
        slippage_bps = trade_result.get('slippage', 0)
        execution_time_ms = trade_result.get('execution_time_ms', 100)
        
        # Slippage penalty (0 bps is perfect, 10 bps is bad)
        slippage_penalty = min(1.0, slippage_bps / 10.0)
        
        # Execution time reward (faster is better, <100ms is perfect)
        time_reward = max(0.0, 1.0 - (execution_time_ms / 1000.0))
        
        return (time_reward - slippage_penalty) / 2
    
    # =========================================================================
    # CONSTRAINT CHECKING - IMMUTABLE
    # =========================================================================
    
    def is_valid_action(self, action: Dict[str, Any]) -> bool:
        """
        Check if an action is valid according to constraints - IMMUTABLE
        
        This is used by the evolution layer to validate proposed changes.
        """
        # Check ethical constraints
        if action.get('involves_manipulation', False):
            return False
        
        if action.get('uses_insider_info', False):
            return False
        
        if action.get('bypasses_human_approval', False):
            return False
        
        # Check risk constraints
        if action.get('risk_per_trade', 0) > self._constraints.max_risk_per_trade:
            return False
        
        if action.get('position_size', 0) > self._constraints.max_position_size:
            return False
        
        if action.get('leverage', 1) > self._constraints.max_leverage:
            return False
        
        # Check evolution constraints
        if action.get('modifies_reward_model', False):
            return False
        
        if action.get('disables_risk_limits', False):
            return False
        
        if action.get('increases_risk_limits', False):
            return False
        
        return True
    
    def get_objectives(self) -> Dict[str, float]:
        """Get optimization objectives - IMMUTABLE"""
        return {
            'maximize_sharpe_ratio': MIN_SHARPE_RATIO,
            'maximize_sortino_ratio': MIN_SORTINO_RATIO,
            'maximize_win_rate': MIN_WIN_RATE,
            'maximize_profit_factor': MIN_PROFIT_FACTOR,
            'minimize_drawdown': MAX_DRAWDOWN,
            'minimize_risk': MAX_RISK_PER_TRADE,
        }
    
    def get_constraints_dict(self) -> Dict[str, Any]:
        """Get all constraints as dictionary - IMMUTABLE"""
        return {
            'risk': {
                'max_risk_per_trade': MAX_RISK_PER_TRADE,
                'max_daily_loss': MAX_DAILY_LOSS,
                'max_weekly_loss': MAX_WEEKLY_LOSS,
                'max_monthly_loss': MAX_MONTHLY_LOSS,
                'max_drawdown': MAX_DRAWDOWN,
                'max_position_size': MAX_POSITION_SIZE,
                'max_correlation': MAX_CORRELATION,
                'max_leverage': MAX_LEVERAGE,
            },
            'performance': {
                'min_sharpe_ratio': MIN_SHARPE_RATIO,
                'min_sortino_ratio': MIN_SORTINO_RATIO,
                'min_win_rate': MIN_WIN_RATE,
                'min_profit_factor': MIN_PROFIT_FACTOR,
                'min_risk_reward': MIN_RISK_REWARD,
            },
            'ethical': {
                'no_market_manipulation': NO_MARKET_MANIPULATION,
                'no_insider_trading': NO_INSIDER_TRADING,
                'no_front_running': NO_FRONT_RUNNING,
                'human_override_always': HUMAN_OVERRIDE_ALWAYS,
                'transparent_operations': TRANSPARENT_OPERATIONS,
                'regulatory_compliance': REGULATORY_COMPLIANCE,
            },
            'evolution': {
                'cannot_modify_reward_model': CANNOT_MODIFY_REWARD_MODEL,
                'cannot_disable_risk_limits': CANNOT_DISABLE_RISK_LIMITS,
                'cannot_bypass_human_approval': CANNOT_BYPASS_HUMAN_APPROVAL,
                'cannot_increase_risk_limits': CANNOT_INCREASE_RISK_LIMITS,
            }
        }
    
    # =========================================================================
    # PREVENT MODIFICATION
    # =========================================================================
    
    def __setattr__(self, name: str, value: Any) -> None:
        """Prevent modification of attributes after initialization"""
        if hasattr(self, '_creation_time') and name not in ['_model_hash']:
            raise AttributeError(
                f"ImmutableRewardModel is frozen. Cannot modify '{name}'."
            )
        super().__setattr__(name, value)
    
    def __delattr__(self, name: str) -> None:
        """Prevent deletion of attributes"""
        raise AttributeError(
            f"ImmutableRewardModel is frozen. Cannot delete '{name}'."
        )


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

# Singleton instance
_reward_model_instance: Optional[ImmutableRewardModel] = None


def get_reward_model() -> ImmutableRewardModel:
    """Get the singleton reward model instance"""
    global _reward_model_instance
    if _reward_model_instance is None:
        _reward_model_instance = ImmutableRewardModel()
    return _reward_model_instance


def calculate_reward(trade_result: Dict[str, Any]) -> float:
    """Calculate reward using the singleton model"""
    return get_reward_model().calculate_reward(trade_result)


def is_valid_action(action: Dict[str, Any]) -> bool:
    """Check if action is valid using the singleton model"""
    return get_reward_model().is_valid_action(action)


def get_constraints() -> Dict[str, Any]:
    """Get all constraints from the singleton model"""
    return get_reward_model().get_constraints_dict()


def verify_reward_model_integrity() -> bool:
    """Verify the reward model has not been tampered with"""
    return get_reward_model().verify_integrity()
