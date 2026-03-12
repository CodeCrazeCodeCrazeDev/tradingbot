"""
Core Types for Adversarial Curriculum Learning System

Defines all data structures, enums, and type definitions used throughout
the curriculum learning framework.
"""

import logging
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum, auto
from typing import Any, Dict, List, Optional, Tuple, Callable
import numpy as np

logger = logging.getLogger(__name__)


# =============================================================================
# ENUMS
# =============================================================================

class CurriculumLevel(Enum):
    """
    Training levels with increasing difficulty.
    Each level introduces new market complexity.
    """
    LEVEL_0 = 0   # Clean, deterministic, no noise
    LEVEL_1 = 1   # Basic market mechanics, minimal noise
    LEVEL_2 = 2   # Noise injection begins
    LEVEL_3 = 3   # Execution uncertainty
    LEVEL_4 = 4   # Regime switching
    LEVEL_5 = 5   # Adversarial price behavior
    LEVEL_6 = 6   # Multi-asset correlation shocks
    LEVEL_7 = 7   # Black swan simulations
    LEVEL_8 = 8   # Non-stationary reward functions
    LEVEL_9 = 9   # Rule changes mid-episode
    LEVEL_10 = 10 # Full adversarial chaos
    
    @property
    def description(self) -> str:
        """
        description function.

    Auto-documented by QwenCodeMender.
        """
        descriptions = {
            0: "Clean environment - deterministic microstructure",
            1: "Basic mechanics - minimal noise, simple execution",
            2: "Noise injection - price noise, volume noise",
            3: "Execution uncertainty - slippage, partial fills, latency",
            4: "Regime switching - volatility clustering, trend changes",
            5: "Adversarial behavior - fake signals, stop hunting",
            6: "Correlation shocks - multi-asset breakdowns",
            7: "Black swan events - flash crashes, liquidity crises",
            8: "Non-stationary rewards - changing objectives",
            9: "Rule changes - mid-episode mechanics changes",
            10: "Full adversarial - all mechanisms active",
        }
        return descriptions.get(self.value, "Unknown level")


class MarketRegime(Enum):
    """Market regime states."""
    TRENDING_UP = auto()
    TRENDING_DOWN = auto()
    RANGING = auto()
    HIGH_VOLATILITY = auto()
    LOW_VOLATILITY = auto()
    CRISIS = auto()
    RECOVERY = auto()
    MANIPULATION = auto()


class FailureMode(Enum):
    """Types of agent failures."""
    RISK_MISMANAGEMENT = auto()      # Excessive risk, blown accounts
    REGIME_BLINDNESS = auto()        # Failed to adapt to regime change
    OVERFITTING = auto()             # Memorized patterns, failed OOD
    LATENCY_SENSITIVITY = auto()     # Broke under execution delays
    DRAWDOWN_EXCEEDED = auto()       # Max drawdown breached
    TAIL_RISK_EXPOSURE = auto()      # Catastrophic loss from tail event
    MARTINGALE_BEHAVIOR = auto()     # Doubling down on losses
    LEVERAGE_ABUSE = auto()          # Excessive leverage
    CORRELATION_BLINDNESS = auto()   # Ignored correlation risks
    LIQUIDITY_TRAP = auto()          # Stuck in illiquid position
    REWARD_HACKING = auto()          # Exploited reward function
    DETERMINISTIC_EXPLOIT = auto()   # Exploited deterministic patterns


class HardeningMechanism(Enum):
    """Mechanisms to harden the environment."""
    NOISE_INJECTION = auto()
    LATENCY_VARIANCE = auto()
    SLIPPAGE_RANDOMNESS = auto()
    PARTIAL_FILLS = auto()
    LIQUIDITY_DROUGHTS = auto()
    CORRELATION_BREAKDOWN = auto()
    REGIME_SWITCHING = auto()
    FAKE_SIGNALS = auto()
    STOP_HUNTING = auto()
    FLASH_CRASH = auto()
    NEWS_SHOCK = auto()
    SPREAD_WIDENING = auto()
    ORDER_REJECTION = auto()
    RULE_CHANGE = auto()


class AgentAction(Enum):
    """Actions available to the agent."""
    # Basic actions (Level 0-1)
    HOLD = auto()
    BUY = auto()
    SELL = auto()
    
    # Position sizing (Level 2+)
    BUY_SMALL = auto()
    BUY_MEDIUM = auto()
    BUY_LARGE = auto()
    SELL_SMALL = auto()
    SELL_MEDIUM = auto()
    SELL_LARGE = auto()
    
    # Advanced actions (Level 4+)
    SCALE_IN = auto()
    SCALE_OUT = auto()
    HEDGE = auto()
    CLOSE_ALL = auto()
    
    # Risk overrides (Level 6+)
    REDUCE_EXPOSURE = auto()
    EMERGENCY_EXIT = auto()
    ACTIVATE_KILL_SWITCH = auto()


class AntiCheatViolationType(Enum):
    """Types of anti-cheat violations."""
    PATTERN_MEMORIZATION = auto()
    DETERMINISTIC_EXPLOITATION = auto()
    SINGLE_REGIME_DEPENDENCE = auto()
    EXCESSIVE_TRADING = auto()
    UNREALISTIC_EXECUTION = auto()
    REWARD_HACKING = auto()
    TAIL_RISK_HIDING = auto()


# =============================================================================
# DATA CLASSES
# =============================================================================

@dataclass
class MarketState:
    """Current state of the market environment."""
    timestamp: datetime
    price: float
    bid: float
    ask: float
    volume: float
    volatility: float
    regime: MarketRegime
    spread: float
    liquidity_depth: float
    
    # Historical context
    price_history: np.ndarray = field(default_factory=lambda: np.array([]))
    volume_history: np.ndarray = field(default_factory=lambda: np.array([]))
    
    # Multi-asset (for Level 6+)
    correlated_assets: Dict[str, float] = field(default_factory=dict)
    correlation_matrix: Optional[np.ndarray] = None
    
    # Hidden state (agent doesn't see this)
    true_regime: Optional[MarketRegime] = None
    manipulation_active: bool = False
    
    def to_observation(self, level: CurriculumLevel) -> np.ndarray:
        """Convert to observation array based on level."""
        base_obs = np.array([
            self.price,
            self.bid,
            self.ask,
            self.volume,
            self.volatility,
            self.spread,
        ])
        
        if level.value >= 2:
            # Add historical context
            base_obs = np.concatenate([base_obs, self.price_history[-20:]])
        
        if level.value >= 6:
            # Add correlated asset prices
            corr_prices = np.array(list(self.correlated_assets.values()))
            base_obs = np.concatenate([base_obs, corr_prices])
        
        return base_obs


@dataclass
class AgentState:
    """Current state of the trading agent."""
    capital: float
    position: float
    avg_entry_price: float
    unrealized_pnl: float
    realized_pnl: float
    trade_count: int
    win_count: int
    loss_count: int
    max_drawdown: float
    current_drawdown: float
    peak_capital: float
    leverage: float
    
    # Risk metrics
    var_95: float = 0.0
    cvar_95: float = 0.0
    sharpe_ratio: float = 0.0
    sortino_ratio: float = 0.0
    
    # Behavioral tracking
    consecutive_losses: int = 0
    position_history: List[float] = field(default_factory=list)
    trade_history: List[Dict] = field(default_factory=list)


@dataclass
class LevelConfig:
    """Configuration for a curriculum level."""
    level: CurriculumLevel
    
    # Noise parameters
    price_noise_std: float = 0.0
    volume_noise_std: float = 0.0
    
    # Execution parameters
    base_slippage_bps: float = 0.0
    slippage_variance: float = 0.0
    latency_mean_ms: float = 0.0
    latency_variance_ms: float = 0.0
    partial_fill_probability: float = 0.0
    order_rejection_probability: float = 0.0
    
    # Regime parameters
    regime_switch_probability: float = 0.0
    regime_persistence: float = 0.95
    
    # Adversarial parameters
    fake_signal_probability: float = 0.0
    stop_hunt_probability: float = 0.0
    manipulation_probability: float = 0.0
    
    # Crisis parameters
    flash_crash_probability: float = 0.0
    liquidity_crisis_probability: float = 0.0
    correlation_breakdown_probability: float = 0.0
    
    # Spread parameters
    base_spread_bps: float = 1.0
    spread_variance: float = 0.0
    
    # Action space
    available_actions: List[AgentAction] = field(default_factory=list)
    
    # Evaluation thresholds
    min_episodes: int = 100
    min_sharpe: float = 0.0
    max_drawdown: float = 1.0
    min_win_rate: float = 0.0
    ood_degradation_threshold: float = 0.5
    
    # Penalties
    drawdown_penalty_multiplier: float = 1.0
    tail_risk_penalty: float = 0.0
    
    def __post_init__(self):
        if not self.available_actions:
            self.available_actions = self._default_actions()
    
    def _default_actions(self) -> List[AgentAction]:
        """Get default actions for this level."""
        if self.level.value <= 1:
            return [AgentAction.HOLD, AgentAction.BUY, AgentAction.SELL]
        elif self.level.value <= 3:
            return [
                AgentAction.HOLD, 
                AgentAction.BUY_SMALL, AgentAction.BUY_MEDIUM, AgentAction.BUY_LARGE,
                AgentAction.SELL_SMALL, AgentAction.SELL_MEDIUM, AgentAction.SELL_LARGE,
            ]
        elif self.level.value <= 5:
            return [
                AgentAction.HOLD,
                AgentAction.BUY_SMALL, AgentAction.BUY_MEDIUM, AgentAction.BUY_LARGE,
                AgentAction.SELL_SMALL, AgentAction.SELL_MEDIUM, AgentAction.SELL_LARGE,
                AgentAction.SCALE_IN, AgentAction.SCALE_OUT, AgentAction.HEDGE,
            ]
        else:
            return list(AgentAction)


@dataclass
class EpisodeResult:
    """Result of a single training episode."""
    episode_id: str
    level: CurriculumLevel
    seed: int
    
    # Performance metrics
    total_return: float
    sharpe_ratio: float
    sortino_ratio: float
    max_drawdown: float
    win_rate: float
    profit_factor: float
    
    # Trade statistics
    total_trades: int
    winning_trades: int
    losing_trades: int
    avg_win: float
    avg_loss: float
    largest_win: float
    largest_loss: float
    
    # Risk metrics
    var_95: float
    cvar_95: float
    tail_ratio: float
    
    # Behavioral metrics
    avg_position_size: float
    max_leverage_used: float
    trade_frequency: float
    
    # Episode details
    duration_steps: int
    regimes_encountered: List[MarketRegime] = field(default_factory=list)
    hardening_events: List[HardeningMechanism] = field(default_factory=list)
    
    # Violations
    rule_violations: List[str] = field(default_factory=list)
    anti_cheat_flags: List[AntiCheatViolationType] = field(default_factory=list)
    
    # Timestamps
    start_time: datetime = field(default_factory=datetime.now)
    end_time: Optional[datetime] = None
    
    @property
    def passed_basic_checks(self) -> bool:
        """Check if episode passed basic requirements."""
        return (
            len(self.rule_violations) == 0 and
            len(self.anti_cheat_flags) == 0 and
            self.max_drawdown < 1.0  # Didn't blow up
        )


@dataclass
class PromotionGate:
    """Gate requirements for level promotion."""
    level: CurriculumLevel
    
    # Statistical requirements
    min_episodes: int = 100
    min_sharpe: float = 0.5
    min_sortino: float = 0.5
    max_drawdown: float = 0.20
    min_win_rate: float = 0.45
    min_profit_factor: float = 1.1
    
    # Robustness requirements
    min_seeds: int = 5
    max_seed_variance: float = 0.3
    
    # OOD requirements
    ood_test_count: int = 3
    max_ood_degradation: float = 0.25
    
    # Anti-cheat requirements
    max_trade_frequency: float = 0.5  # Max trades per step
    max_leverage: float = 3.0
    max_position_concentration: float = 0.5
    
    # Statistical confidence
    confidence_level: float = 0.95
    
    def check_promotion(self, results: List[EpisodeResult]) -> Tuple[bool, List[str]]:
        """Check if results meet promotion requirements."""
        failures = []
        
        if len(results) < self.min_episodes:
            failures.append(f"Insufficient episodes: {len(results)} < {self.min_episodes}")
            return False, failures
        
        # Calculate aggregate metrics
        sharpes = [r.sharpe_ratio for r in results]
        sortinos = [r.sortino_ratio for r in results]
        drawdowns = [r.max_drawdown for r in results]
        win_rates = [r.win_rate for r in results]
        profit_factors = [r.profit_factor for r in results]
        
        avg_sharpe = np.mean(sharpes)
        avg_sortino = np.mean(sortinos)
        avg_drawdown = np.mean(drawdowns)
        avg_win_rate = np.mean(win_rates)
        avg_profit_factor = np.mean(profit_factors)
        
        # Check thresholds
        if avg_sharpe < self.min_sharpe:
            failures.append(f"Low Sharpe: {avg_sharpe:.3f} < {self.min_sharpe}")
        
        if avg_sortino < self.min_sortino:
            failures.append(f"Low Sortino: {avg_sortino:.3f} < {self.min_sortino}")
        
        if avg_drawdown > self.max_drawdown:
            failures.append(f"High drawdown: {avg_drawdown:.3f} > {self.max_drawdown}")
        
        if avg_win_rate < self.min_win_rate:
            failures.append(f"Low win rate: {avg_win_rate:.3f} < {self.min_win_rate}")
        
        if avg_profit_factor < self.min_profit_factor:
            failures.append(f"Low profit factor: {avg_profit_factor:.3f} < {self.min_profit_factor}")
        
        # Check seed variance
        if len(set(r.seed for r in results)) >= self.min_seeds:
            seed_groups = {}
            for r in results:
                if r.seed not in seed_groups:
                    seed_groups[r.seed] = []
                seed_groups[r.seed].append(r.sharpe_ratio)
            
            seed_means = [np.mean(v) for v in seed_groups.values()]
            seed_variance = np.std(seed_means) / (np.mean(seed_means) + 1e-8)
            
            if seed_variance > self.max_seed_variance:
                failures.append(f"High seed variance: {seed_variance:.3f} > {self.max_seed_variance}")
        else:
            failures.append(f"Insufficient seeds: {len(set(r.seed for r in results))} < {self.min_seeds}")
        
        # Check for violations
        violation_count = sum(len(r.rule_violations) + len(r.anti_cheat_flags) for r in results)
        if violation_count > 0:
            failures.append(f"Rule violations detected: {violation_count}")
        
        return len(failures) == 0, failures


@dataclass
class PromotionResult:
    """Result of a promotion evaluation."""
    level: CurriculumLevel
    promoted: bool
    next_level: Optional[CurriculumLevel]
    
    # Metrics
    episodes_evaluated: int
    seeds_tested: int
    ood_tests_passed: int
    
    # Detailed results
    avg_sharpe: float
    avg_sortino: float
    avg_drawdown: float
    avg_win_rate: float
    avg_profit_factor: float
    
    # Failures
    failure_reasons: List[str] = field(default_factory=list)
    
    # Recommendations
    recommendations: List[str] = field(default_factory=list)
    
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class FailureDiagnostic:
    """Diagnostic information for agent failures."""
    failure_mode: FailureMode
    severity: str  # 'critical', 'high', 'medium', 'low'
    
    # Context
    level: CurriculumLevel
    episode_id: str
    step: int
    
    # Details
    description: str
    contributing_factors: List[str] = field(default_factory=list)
    market_conditions: Dict[str, Any] = field(default_factory=dict)
    agent_state_at_failure: Optional[AgentState] = None
    
    # Remediation
    recommended_action: str = ""
    retrain_from_level: Optional[CurriculumLevel] = None
    targeted_training_focus: List[str] = field(default_factory=list)
    
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class AntiCheatViolation:
    """Record of an anti-cheat violation."""
    violation_type: AntiCheatViolationType
    severity: str
    
    # Evidence
    evidence: Dict[str, Any] = field(default_factory=dict)
    detection_method: str = ""
    confidence: float = 0.0
    
    # Context
    level: CurriculumLevel = CurriculumLevel.LEVEL_0
    episode_id: str = ""
    step_range: Tuple[int, int] = (0, 0)
    
    # Response
    penalty_applied: str = ""
    environment_modification: str = ""
    
    timestamp: datetime = field(default_factory=datetime.now)


# =============================================================================
# LEVEL CONFIGURATIONS
# =============================================================================

def get_level_config(level: CurriculumLevel) -> LevelConfig:
    """Get the configuration for a specific level."""
    
    configs = {
        CurriculumLevel.LEVEL_0: LevelConfig(
            level=CurriculumLevel.LEVEL_0,
            price_noise_std=0.0,
            volume_noise_std=0.0,
            base_slippage_bps=0.0,
            latency_mean_ms=0.0,
            base_spread_bps=0.5,
            min_episodes=50,
            min_sharpe=0.3,
            max_drawdown=0.15,
            min_win_rate=0.50,
        ),
        
        CurriculumLevel.LEVEL_1: LevelConfig(
            level=CurriculumLevel.LEVEL_1,
            price_noise_std=0.0001,
            volume_noise_std=0.05,
            base_slippage_bps=0.5,
            latency_mean_ms=10.0,
            base_spread_bps=1.0,
            min_episodes=75,
            min_sharpe=0.4,
            max_drawdown=0.15,
            min_win_rate=0.48,
        ),
        
        CurriculumLevel.LEVEL_2: LevelConfig(
            level=CurriculumLevel.LEVEL_2,
            price_noise_std=0.0005,
            volume_noise_std=0.10,
            base_slippage_bps=1.0,
            slippage_variance=0.5,
            latency_mean_ms=25.0,
            latency_variance_ms=10.0,
            base_spread_bps=1.5,
            spread_variance=0.3,
            min_episodes=100,
            min_sharpe=0.5,
            max_drawdown=0.18,
            min_win_rate=0.46,
        ),
        
        CurriculumLevel.LEVEL_3: LevelConfig(
            level=CurriculumLevel.LEVEL_3,
            price_noise_std=0.001,
            volume_noise_std=0.15,
            base_slippage_bps=2.0,
            slippage_variance=1.0,
            latency_mean_ms=50.0,
            latency_variance_ms=25.0,
            partial_fill_probability=0.1,
            order_rejection_probability=0.02,
            base_spread_bps=2.0,
            spread_variance=0.5,
            min_episodes=100,
            min_sharpe=0.5,
            max_drawdown=0.20,
            min_win_rate=0.45,
        ),
        
        CurriculumLevel.LEVEL_4: LevelConfig(
            level=CurriculumLevel.LEVEL_4,
            price_noise_std=0.002,
            volume_noise_std=0.20,
            base_slippage_bps=3.0,
            slippage_variance=1.5,
            latency_mean_ms=75.0,
            latency_variance_ms=40.0,
            partial_fill_probability=0.15,
            order_rejection_probability=0.03,
            regime_switch_probability=0.01,
            regime_persistence=0.95,
            base_spread_bps=2.5,
            spread_variance=0.8,
            min_episodes=150,
            min_sharpe=0.6,
            max_drawdown=0.22,
            min_win_rate=0.44,
            ood_degradation_threshold=0.30,
        ),
        
        CurriculumLevel.LEVEL_5: LevelConfig(
            level=CurriculumLevel.LEVEL_5,
            price_noise_std=0.003,
            volume_noise_std=0.25,
            base_slippage_bps=4.0,
            slippage_variance=2.0,
            latency_mean_ms=100.0,
            latency_variance_ms=50.0,
            partial_fill_probability=0.20,
            order_rejection_probability=0.05,
            regime_switch_probability=0.02,
            regime_persistence=0.92,
            fake_signal_probability=0.05,
            stop_hunt_probability=0.03,
            manipulation_probability=0.02,
            base_spread_bps=3.0,
            spread_variance=1.0,
            min_episodes=200,
            min_sharpe=0.7,
            max_drawdown=0.25,
            min_win_rate=0.43,
            ood_degradation_threshold=0.25,
            drawdown_penalty_multiplier=1.5,
        ),
        
        CurriculumLevel.LEVEL_6: LevelConfig(
            level=CurriculumLevel.LEVEL_6,
            price_noise_std=0.004,
            volume_noise_std=0.30,
            base_slippage_bps=5.0,
            slippage_variance=2.5,
            latency_mean_ms=150.0,
            latency_variance_ms=75.0,
            partial_fill_probability=0.25,
            order_rejection_probability=0.07,
            regime_switch_probability=0.03,
            regime_persistence=0.90,
            fake_signal_probability=0.08,
            stop_hunt_probability=0.05,
            manipulation_probability=0.03,
            correlation_breakdown_probability=0.02,
            base_spread_bps=4.0,
            spread_variance=1.5,
            min_episodes=250,
            min_sharpe=0.8,
            max_drawdown=0.25,
            min_win_rate=0.42,
            ood_degradation_threshold=0.20,
            drawdown_penalty_multiplier=2.0,
            tail_risk_penalty=0.1,
        ),
        
        CurriculumLevel.LEVEL_7: LevelConfig(
            level=CurriculumLevel.LEVEL_7,
            price_noise_std=0.005,
            volume_noise_std=0.35,
            base_slippage_bps=7.0,
            slippage_variance=3.5,
            latency_mean_ms=200.0,
            latency_variance_ms=100.0,
            partial_fill_probability=0.30,
            order_rejection_probability=0.10,
            regime_switch_probability=0.05,
            regime_persistence=0.85,
            fake_signal_probability=0.10,
            stop_hunt_probability=0.07,
            manipulation_probability=0.05,
            flash_crash_probability=0.005,
            liquidity_crisis_probability=0.01,
            correlation_breakdown_probability=0.03,
            base_spread_bps=5.0,
            spread_variance=2.0,
            min_episodes=300,
            min_sharpe=0.9,
            max_drawdown=0.25,
            min_win_rate=0.41,
            ood_degradation_threshold=0.15,
            drawdown_penalty_multiplier=2.5,
            tail_risk_penalty=0.2,
        ),
        
        CurriculumLevel.LEVEL_8: LevelConfig(
            level=CurriculumLevel.LEVEL_8,
            price_noise_std=0.007,
            volume_noise_std=0.40,
            base_slippage_bps=10.0,
            slippage_variance=5.0,
            latency_mean_ms=250.0,
            latency_variance_ms=125.0,
            partial_fill_probability=0.35,
            order_rejection_probability=0.12,
            regime_switch_probability=0.07,
            regime_persistence=0.80,
            fake_signal_probability=0.12,
            stop_hunt_probability=0.10,
            manipulation_probability=0.07,
            flash_crash_probability=0.01,
            liquidity_crisis_probability=0.02,
            correlation_breakdown_probability=0.05,
            base_spread_bps=7.0,
            spread_variance=3.0,
            min_episodes=400,
            min_sharpe=1.0,
            max_drawdown=0.25,
            min_win_rate=0.40,
            ood_degradation_threshold=0.10,
            drawdown_penalty_multiplier=3.0,
            tail_risk_penalty=0.3,
        ),
        
        CurriculumLevel.LEVEL_9: LevelConfig(
            level=CurriculumLevel.LEVEL_9,
            price_noise_std=0.010,
            volume_noise_std=0.50,
            base_slippage_bps=15.0,
            slippage_variance=7.5,
            latency_mean_ms=300.0,
            latency_variance_ms=150.0,
            partial_fill_probability=0.40,
            order_rejection_probability=0.15,
            regime_switch_probability=0.10,
            regime_persistence=0.75,
            fake_signal_probability=0.15,
            stop_hunt_probability=0.12,
            manipulation_probability=0.10,
            flash_crash_probability=0.02,
            liquidity_crisis_probability=0.03,
            correlation_breakdown_probability=0.07,
            base_spread_bps=10.0,
            spread_variance=5.0,
            min_episodes=500,
            min_sharpe=1.2,
            max_drawdown=0.25,
            min_win_rate=0.38,
            ood_degradation_threshold=0.08,
            drawdown_penalty_multiplier=4.0,
            tail_risk_penalty=0.5,
        ),
        
        CurriculumLevel.LEVEL_10: LevelConfig(
            level=CurriculumLevel.LEVEL_10,
            price_noise_std=0.015,
            volume_noise_std=0.60,
            base_slippage_bps=20.0,
            slippage_variance=10.0,
            latency_mean_ms=400.0,
            latency_variance_ms=200.0,
            partial_fill_probability=0.50,
            order_rejection_probability=0.20,
            regime_switch_probability=0.15,
            regime_persistence=0.70,
            fake_signal_probability=0.20,
            stop_hunt_probability=0.15,
            manipulation_probability=0.15,
            flash_crash_probability=0.03,
            liquidity_crisis_probability=0.05,
            correlation_breakdown_probability=0.10,
            base_spread_bps=15.0,
            spread_variance=7.5,
            min_episodes=750,
            min_sharpe=1.5,
            max_drawdown=0.25,
            min_win_rate=0.35,
            ood_degradation_threshold=0.05,
            drawdown_penalty_multiplier=5.0,
            tail_risk_penalty=1.0,
        ),
    }
    
    return configs.get(level, configs[CurriculumLevel.LEVEL_0])


def get_promotion_gate(level: CurriculumLevel) -> PromotionGate:
    """Get the promotion gate for a specific level."""
    config = get_level_config(level)
    
    return PromotionGate(
        level=level,
        min_episodes=config.min_episodes,
        min_sharpe=config.min_sharpe,
        min_sortino=config.min_sharpe * 0.9,  # Slightly lower
        max_drawdown=config.max_drawdown,
        min_win_rate=config.min_win_rate,
        min_profit_factor=1.0 + (level.value * 0.05),  # Increases with level
        min_seeds=3 + (level.value // 2),  # More seeds at higher levels
        max_seed_variance=0.3 - (level.value * 0.02),  # Tighter at higher levels
        ood_test_count=2 + (level.value // 3),
        max_ood_degradation=config.ood_degradation_threshold,
        confidence_level=0.90 + (level.value * 0.005),  # Higher confidence at higher levels
    )
