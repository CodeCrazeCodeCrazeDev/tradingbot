"""
AADS MicroFish Swarm Intelligence

Inspired by the emergent behavior of fish schools. Instead of one monolithic
research agent, AADS operates as a swarm of hundreds of specialized micro-agents.

Key Principles:
- No central coordinator
- Emergent consensus via weighted voting
- Each fish has its own lifecycle (birth, growth, decline, death)
- Fish weights adapt based on recent accuracy
- Dissent detection reduces confidence when fish disagree

Swarm Architecture:
- Technical analysis micro-agents (momentum, mean reversion, breakout, volume)
- Fundamental micro-agents (earnings, revisions, short interest)
- Macro micro-agents (yield curve, dollar, VIX regime)
- Alternative data micro-agents (satellite, sentiment, options, darkpool)
- Prediction market micro-agents (Polymarket odds, liquidity)
"""

from dataclasses import dataclass, field
from typing import List, Dict, Optional, Callable, Any, Tuple
from datetime import datetime, timedelta
from enum import Enum
import numpy as np
import logging
from abc import ABC, abstractmethod
import uuid

logger = logging.getLogger(__name__)


class FishCategory(Enum):
    """Categories of micro-fish agents"""
    TECHNICAL = "technical"
    FUNDAMENTAL = "fundamental"
    MACRO = "macro"
    ALTERNATIVE = "alternative"
    PREDICTION_MARKET = "prediction_market"
    VISUAL = "visual"


class FishStatus(Enum):
    """Lifecycle status of a micro-fish"""
    SPAWNING = "spawning"       # Newly created, warming up
    ACTIVE = "active"           # Fully operational
    DECLINING = "declining"     # Weight decreasing
    DORMANT = "dormant"         # Temporarily inactive
    DEAD = "dead"               # Retired, no longer used


@dataclass
class FishMemory:
    """Memory store for fish accuracy tracking"""
    asset_accuracy: Dict[str, float] = field(default_factory=dict)
    regime_accuracy: Dict[str, float] = field(default_factory=dict)
    recent_signals: List[Tuple[datetime, float, float]] = field(default_factory=list)  # (time, signal, outcome)
    total_signals: int = 0
    correct_signals: int = 0
    
    def get_accuracy(self, asset: str, regime: str, lookback_days: int = 30) -> float:
        """Get accuracy for specific asset/regime combination"""
        # Filter recent signals
        cutoff = datetime.now() - timedelta(days=lookback_days)
        recent = [s for s in self.recent_signals if s[0] > cutoff]
        
        if not recent:
            return 0.5  # Default neutral accuracy
        
        # Calculate accuracy from recent signals
        correct = sum(1 for _, signal, outcome in recent if np.sign(signal) == np.sign(outcome))
        return correct / len(recent)
    
    def record_signal(self, signal: float, outcome: float) -> None:
        """Record a signal and its outcome"""
        self.recent_signals.append((datetime.now(), signal, outcome))
        self.total_signals += 1
        if np.sign(signal) == np.sign(outcome):
            self.correct_signals += 1
        
        # Keep only last 1000 signals
        if len(self.recent_signals) > 1000:
            self.recent_signals = self.recent_signals[-1000:]


@dataclass
class SwarmSignal:
    """Output signal from the swarm consensus"""
    direction: float              # -1 to 1 (short to long)
    strength: float               # 0 to 1 (confidence)
    dissent_ratio: float          # 0 to 1 (disagreement level)
    dominant_fish: str            # ID of most influential fish
    contributing_fish: List[str]  # IDs of fish that contributed
    bull_count: int               # Number of bullish fish
    bear_count: int               # Number of bearish fish
    neutral_count: int            # Number of neutral fish
    timestamp: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'direction': self.direction,
            'strength': self.strength,
            'dissent_ratio': self.dissent_ratio,
            'dominant_fish': self.dominant_fish,
            'contributing_fish': self.contributing_fish,
            'bull_count': self.bull_count,
            'bear_count': self.bear_count,
            'neutral_count': self.neutral_count,
            'timestamp': self.timestamp.isoformat()
        }


class MicroFish(ABC):
    """
    Base class for all micro-fish agents.
    
    Each fish is a specialized signal generator that:
    - Produces signals in [-1, 1] range
    - Tracks its own accuracy
    - Has a weight that adapts based on performance
    - Can be spawned, grow, decline, and die
    """
    
    def __init__(
        self,
        fish_id: str,
        category: FishCategory,
        signal_name: str,
        config: Dict[str, Any] = None
    ):
        self.fish_id = fish_id
        self.category = category
        self.signal_name = signal_name
        self.config = config or {}
        
        # Lifecycle
        self.status = FishStatus.SPAWNING
        self.created_at = datetime.now()
        self.last_signal_at: Optional[datetime] = None
        
        # Weight and performance
        self.initial_weight = 1.0
        self.current_weight = 1.0
        self.min_weight_threshold = 0.05  # Below this = death
        
        # Memory
        self.memory = FishMemory()
        
        # Warmup period
        self.warmup_signals = 10
        self.signals_generated = 0
    
    @abstractmethod
    def generate_signal(self, asset: str, market_state: Dict[str, Any]) -> float:
        """
        Generate a trading signal for the given asset.
        
        Args:
            asset: Asset identifier (ticker)
            market_state: Current market state dictionary
            
        Returns:
            Signal value in [-1, 1] range
        """
        pass
    
    def get_weighted_signal(self, asset: str, market_state: Dict[str, Any]) -> Tuple[float, float]:
        """
        Get signal weighted by fish accuracy.
        
        Returns:
            Tuple of (signal, weight)
        """
        if self.status == FishStatus.DEAD:
            return 0.0, 0.0
        
        signal = self.generate_signal(asset, market_state)
        self.signals_generated += 1
        self.last_signal_at = datetime.now()
        
        # Update status after warmup
        if self.status == FishStatus.SPAWNING and self.signals_generated >= self.warmup_signals:
            self.status = FishStatus.ACTIVE
        
        # Get accuracy-adjusted weight
        regime = market_state.get('regime', 'unknown')
        accuracy = self.memory.get_accuracy(asset, regime)
        adjusted_weight = self.current_weight * accuracy
        
        return signal, adjusted_weight
    
    def update_weight(self, outcome: float, signal: float) -> None:
        """
        Update fish weight based on signal outcome.
        
        Args:
            outcome: Actual market outcome
            signal: Signal that was generated
        """
        self.memory.record_signal(signal, outcome)
        
        # Adjust weight based on accuracy
        if np.sign(signal) == np.sign(outcome):
            # Correct prediction - increase weight
            self.current_weight *= 1.02
        else:
            # Wrong prediction - decrease weight
            self.current_weight *= 0.95
        
        # Clamp weight
        self.current_weight = max(self.min_weight_threshold, min(self.current_weight, 3.0))
        
        # Check for death
        if self.current_weight <= self.min_weight_threshold:
            self.status = FishStatus.DEAD
            logger.info(f"Fish {self.fish_id} died (weight below threshold)")
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'fish_id': self.fish_id,
            'category': self.category.value,
            'signal_name': self.signal_name,
            'status': self.status.value,
            'current_weight': self.current_weight,
            'signals_generated': self.signals_generated,
            'accuracy': self.memory.correct_signals / max(1, self.memory.total_signals),
            'created_at': self.created_at.isoformat()
        }


# ============================================================================
# Technical Analysis Fish
# ============================================================================

class MomentumFish(MicroFish):
    """Momentum-based signal fish"""
    
    def __init__(self, lookback: int = 20):
        super().__init__(
            fish_id=f"momentum_{lookback}_{uuid.uuid4().hex[:6]}",
            category=FishCategory.TECHNICAL,
            signal_name="price_momentum",
            config={'lookback': lookback}
        )
        self.lookback = lookback
    
    def generate_signal(self, asset: str, market_state: Dict[str, Any]) -> float:
        prices = market_state.get('prices', [])
        if len(prices) < self.lookback:
            return 0.0
        
        returns = (prices[-1] - prices[-self.lookback]) / prices[-self.lookback]
        # Normalize to [-1, 1]
        return np.tanh(returns * 10)


class MeanReversionFish(MicroFish):
    """Mean reversion signal fish"""
    
    def __init__(self, lookback: int = 20):
        super().__init__(
            fish_id=f"mean_reversion_{lookback}_{uuid.uuid4().hex[:6]}",
            category=FishCategory.TECHNICAL,
            signal_name="zscore_reversion",
            config={'lookback': lookback}
        )
        self.lookback = lookback
    
    def generate_signal(self, asset: str, market_state: Dict[str, Any]) -> float:
        prices = market_state.get('prices', [])
        if len(prices) < self.lookback:
            return 0.0
        
        recent = prices[-self.lookback:]
        mean = np.mean(recent)
        std = np.std(recent) + 1e-10
        zscore = (prices[-1] - mean) / std
        
        # Mean reversion: sell when high, buy when low
        return -np.tanh(zscore)


class BreakoutFish(MicroFish):
    """Volatility breakout signal fish"""
    
    def __init__(self, lookback: int = 20):
        super().__init__(
            fish_id=f"breakout_{lookback}_{uuid.uuid4().hex[:6]}",
            category=FishCategory.TECHNICAL,
            signal_name="volatility_breakout",
            config={'lookback': lookback}
        )
        self.lookback = lookback
    
    def generate_signal(self, asset: str, market_state: Dict[str, Any]) -> float:
        prices = market_state.get('prices', [])
        if len(prices) < self.lookback:
            return 0.0
        
        recent = prices[-self.lookback:]
        high = max(recent)
        low = min(recent)
        current = prices[-1]
        
        # Breakout above range = bullish, below = bearish
        range_size = high - low + 1e-10
        position = (current - low) / range_size
        
        if position > 0.9:  # Near top of range
            return 0.8
        elif position < 0.1:  # Near bottom
            return -0.8
        return 0.0


class VolumeFish(MicroFish):
    """Volume anomaly signal fish"""
    
    def __init__(self, lookback: int = 20):
        super().__init__(
            fish_id=f"volume_{lookback}_{uuid.uuid4().hex[:6]}",
            category=FishCategory.TECHNICAL,
            signal_name="volume_anomaly",
            config={'lookback': lookback}
        )
        self.lookback = lookback
    
    def generate_signal(self, asset: str, market_state: Dict[str, Any]) -> float:
        volumes = market_state.get('volumes', [])
        prices = market_state.get('prices', [])
        
        if len(volumes) < self.lookback or len(prices) < 2:
            return 0.0
        
        avg_volume = np.mean(volumes[-self.lookback:])
        current_volume = volumes[-1]
        price_change = prices[-1] - prices[-2]
        
        # High volume + price up = bullish, high volume + price down = bearish
        volume_ratio = current_volume / (avg_volume + 1e-10)
        if volume_ratio > 2.0:  # Significant volume
            return np.sign(price_change) * min(1.0, (volume_ratio - 1) / 3)
        return 0.0


# ============================================================================
# Fundamental Fish
# ============================================================================

class EarningsFish(MicroFish):
    """Earnings surprise signal fish"""
    
    def __init__(self):
        super().__init__(
            fish_id=f"earnings_{uuid.uuid4().hex[:6]}",
            category=FishCategory.FUNDAMENTAL,
            signal_name="earnings_surprise"
        )
    
    def generate_signal(self, asset: str, market_state: Dict[str, Any]) -> float:
        earnings = market_state.get('earnings', {})
        if not earnings:
            return 0.0
        
        actual = earnings.get('actual_eps', 0)
        estimate = earnings.get('estimate_eps', 0)
        
        if estimate == 0:
            return 0.0
        
        surprise = (actual - estimate) / abs(estimate)
        return np.tanh(surprise * 5)


class AnalystRevisionFish(MicroFish):
    """Analyst revision signal fish"""
    
    def __init__(self, lag_days: int = 3):
        super().__init__(
            fish_id=f"analyst_revision_{uuid.uuid4().hex[:6]}",
            category=FishCategory.FUNDAMENTAL,
            signal_name="analyst_revision",
            config={'lag_days': lag_days}
        )
    
    def generate_signal(self, asset: str, market_state: Dict[str, Any]) -> float:
        revisions = market_state.get('analyst_revisions', {})
        if not revisions:
            return 0.0
        
        upgrades = revisions.get('upgrades', 0)
        downgrades = revisions.get('downgrades', 0)
        total = upgrades + downgrades
        
        if total == 0:
            return 0.0
        
        return (upgrades - downgrades) / total


class ShortInterestFish(MicroFish):
    """Short squeeze risk signal fish"""
    
    def __init__(self, threshold_pct: float = 20.0):
        super().__init__(
            fish_id=f"short_interest_{uuid.uuid4().hex[:6]}",
            category=FishCategory.FUNDAMENTAL,
            signal_name="short_squeeze_risk",
            config={'threshold_pct': threshold_pct}
        )
        self.threshold = threshold_pct
    
    def generate_signal(self, asset: str, market_state: Dict[str, Any]) -> float:
        short_interest = market_state.get('short_interest_pct', 0)
        days_to_cover = market_state.get('days_to_cover', 0)
        
        if short_interest > self.threshold and days_to_cover > 5:
            # High short interest + hard to cover = squeeze potential
            return min(1.0, (short_interest - self.threshold) / 20)
        return 0.0


# ============================================================================
# Macro Fish
# ============================================================================

class YieldCurveFish(MicroFish):
    """Yield curve shape signal fish"""
    
    def __init__(self, segments: List[str] = None):
        super().__init__(
            fish_id=f"yield_curve_{uuid.uuid4().hex[:6]}",
            category=FishCategory.MACRO,
            signal_name="curve_shape",
            config={'segments': segments or ['2s10s', '5s30s']}
        )
    
    def generate_signal(self, asset: str, market_state: Dict[str, Any]) -> float:
        yields = market_state.get('yields', {})
        
        spread_2s10s = yields.get('10y', 0) - yields.get('2y', 0)
        
        # Inverted curve = bearish, steep curve = bullish
        if spread_2s10s < -0.5:
            return -0.8  # Strongly inverted
        elif spread_2s10s < 0:
            return -0.4  # Slightly inverted
        elif spread_2s10s > 1.5:
            return 0.6   # Steep curve
        return 0.0


class VIXRegimeFish(MicroFish):
    """VIX regime signal fish"""
    
    def __init__(self, thresholds: List[float] = None):
        super().__init__(
            fish_id=f"vix_regime_{uuid.uuid4().hex[:6]}",
            category=FishCategory.MACRO,
            signal_name="vol_regime",
            config={'thresholds': thresholds or [15, 25, 35]}
        )
        self.thresholds = thresholds or [15, 25, 35]
    
    def generate_signal(self, asset: str, market_state: Dict[str, Any]) -> float:
        vix = market_state.get('vix', 20)
        
        if vix < self.thresholds[0]:
            return 0.5   # Low vol = risk on
        elif vix < self.thresholds[1]:
            return 0.0   # Normal
        elif vix < self.thresholds[2]:
            return -0.5  # Elevated vol
        else:
            return -0.9  # Crisis vol


# ============================================================================
# Alternative Data Fish
# ============================================================================

class SentimentFish(MicroFish):
    """News sentiment signal fish"""
    
    def __init__(self, window: int = 5):
        super().__init__(
            fish_id=f"sentiment_{uuid.uuid4().hex[:6]}",
            category=FishCategory.ALTERNATIVE,
            signal_name="news_sentiment_zscore",
            config={'window': window}
        )
    
    def generate_signal(self, asset: str, market_state: Dict[str, Any]) -> float:
        sentiment = market_state.get('sentiment_score', 0)
        # Sentiment typically in [-1, 1] already
        return sentiment


class OptionsFlowFish(MicroFish):
    """Options flow skew signal fish"""
    
    def __init__(self):
        super().__init__(
            fish_id=f"options_flow_{uuid.uuid4().hex[:6]}",
            category=FishCategory.ALTERNATIVE,
            signal_name="options_flow_skew"
        )
    
    def generate_signal(self, asset: str, market_state: Dict[str, Any]) -> float:
        options = market_state.get('options', {})
        
        call_volume = options.get('call_volume', 0)
        put_volume = options.get('put_volume', 0)
        total = call_volume + put_volume
        
        if total == 0:
            return 0.0
        
        # Put/call ratio
        pcr = put_volume / (call_volume + 1e-10)
        
        # High put volume = bearish, high call volume = bullish
        if pcr > 1.5:
            return -0.6
        elif pcr < 0.7:
            return 0.6
        return 0.0


class DarkPoolFish(MicroFish):
    """Dark pool block trade signal fish"""
    
    def __init__(self, min_size_m: float = 10.0):
        super().__init__(
            fish_id=f"darkpool_{uuid.uuid4().hex[:6]}",
            category=FishCategory.ALTERNATIVE,
            signal_name="block_trade_delta",
            config={'min_size_m': min_size_m}
        )
    
    def generate_signal(self, asset: str, market_state: Dict[str, Any]) -> float:
        darkpool = market_state.get('darkpool', {})
        
        buy_blocks = darkpool.get('buy_volume_m', 0)
        sell_blocks = darkpool.get('sell_volume_m', 0)
        
        if buy_blocks + sell_blocks < self.config['min_size_m']:
            return 0.0
        
        delta = buy_blocks - sell_blocks
        total = buy_blocks + sell_blocks
        
        return np.tanh(delta / total * 2)


# ============================================================================
# Prediction Market Fish
# ============================================================================

class PolymarketOddsFish(MicroFish):
    """Polymarket odds vs model edge fish"""
    
    def __init__(self, min_edge: float = 0.05):
        super().__init__(
            fish_id=f"poly_odds_{uuid.uuid4().hex[:6]}",
            category=FishCategory.PREDICTION_MARKET,
            signal_name="poly_vs_model_edge",
            config={'min_edge': min_edge}
        )
    
    def generate_signal(self, asset: str, market_state: Dict[str, Any]) -> float:
        polymarket = market_state.get('polymarket', {})
        
        market_prob = polymarket.get('yes_price', 0.5)
        model_prob = polymarket.get('model_prob', 0.5)
        
        edge = model_prob - market_prob
        
        if abs(edge) < self.config['min_edge']:
            return 0.0
        
        return np.sign(edge) * min(1.0, abs(edge) * 5)


# ============================================================================
# Swarm Orchestrator
# ============================================================================

class MicroFishSwarm:
    """
    Orchestrates the swarm of micro-fish agents.
    
    Features:
    - Manages fish lifecycle (spawn, grow, decline, death)
    - Aggregates signals via weighted voting
    - Detects dissent and adjusts confidence
    - Spawns new fish for novel patterns
    """
    
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        self.fish: Dict[str, MicroFish] = {}
        self.fish_by_category: Dict[FishCategory, List[str]] = {cat: [] for cat in FishCategory}
        
        # Initialize default fish swarm
        self._initialize_default_swarm()
        
        logger.info(f"MicroFishSwarm initialized with {len(self.fish)} fish")
    
    def _initialize_default_swarm(self) -> None:
        """Initialize the default swarm of micro-fish"""
        # Technical fish with different lookbacks
        for lookback in [5, 10, 20, 60]:
            self._add_fish(MomentumFish(lookback))
        
        for lookback in [10, 20, 50]:
            self._add_fish(MeanReversionFish(lookback))
        
        for lookback in [20, 50]:
            self._add_fish(BreakoutFish(lookback))
        
        for lookback in [5, 20]:
            self._add_fish(VolumeFish(lookback))
        
        # Fundamental fish
        self._add_fish(EarningsFish())
        self._add_fish(AnalystRevisionFish())
        self._add_fish(ShortInterestFish())
        
        # Macro fish
        self._add_fish(YieldCurveFish())
        self._add_fish(VIXRegimeFish())
        
        # Alternative data fish
        self._add_fish(SentimentFish())
        self._add_fish(OptionsFlowFish())
        self._add_fish(DarkPoolFish())
        
        # Prediction market fish
        self._add_fish(PolymarketOddsFish())
    
    def _add_fish(self, fish: MicroFish) -> None:
        """Add a fish to the swarm"""
        self.fish[fish.fish_id] = fish
        self.fish_by_category[fish.category].append(fish.fish_id)
    
    def spawn_fish(self, fish: MicroFish) -> None:
        """Spawn a new fish into the swarm"""
        self._add_fish(fish)
        logger.info(f"Spawned new fish: {fish.fish_id} ({fish.signal_name})")
    
    def get_consensus(self, asset: str, market_state: Dict[str, Any]) -> SwarmSignal:
        """
        Get emergent consensus from the swarm.
        
        Each fish votes independently with no communication.
        Consensus is weighted by fish accuracy.
        
        Args:
            asset: Asset to generate signal for
            market_state: Current market state
            
        Returns:
            SwarmSignal with consensus direction and confidence
        """
        votes: Dict[str, Tuple[float, float]] = {}  # fish_id -> (signal, weight)
        
        # Collect votes from all active fish
        for fish_id, fish in self.fish.items():
            if fish.status in [FishStatus.ACTIVE, FishStatus.SPAWNING]:
                signal, weight = fish.get_weighted_signal(asset, market_state)
                if weight > 0:
                    votes[fish_id] = (signal, weight)
        
        if not votes:
            return SwarmSignal(
                direction=0.0,
                strength=0.0,
                dissent_ratio=0.0,
                dominant_fish="",
                contributing_fish=[],
                bull_count=0,
                bear_count=0,
                neutral_count=0
            )
        
        # Calculate weighted consensus
        total_weight = sum(w for _, w in votes.values())
        weighted_sum = sum(s * w for s, w in votes.values())
        raw_consensus = weighted_sum / total_weight if total_weight > 0 else 0
        
        # Calculate consensus strength
        abs_weights = sum(abs(s) * w for s, w in votes.values())
        consensus_strength = abs(weighted_sum) / (abs_weights + 1e-10)
        
        # Count bulls, bears, neutrals
        bull_count = sum(1 for s, _ in votes.values() if s > 0.3)
        bear_count = sum(1 for s, _ in votes.values() if s < -0.3)
        neutral_count = len(votes) - bull_count - bear_count
        
        # Calculate dissent ratio
        minority = min(bull_count, bear_count)
        majority = max(bull_count, bear_count)
        dissent_ratio = minority / majority if majority > 0 else 0
        
        # Apply confidence penalty for high dissent
        confidence_penalty = dissent_ratio * 0.3
        adjusted_strength = consensus_strength * (1 - confidence_penalty)
        
        # Find dominant fish
        dominant_fish = max(votes.keys(), key=lambda k: abs(votes[k][0] * votes[k][1]))
        
        return SwarmSignal(
            direction=np.sign(raw_consensus),
            strength=adjusted_strength,
            dissent_ratio=dissent_ratio,
            dominant_fish=dominant_fish,
            contributing_fish=list(votes.keys()),
            bull_count=bull_count,
            bear_count=bear_count,
            neutral_count=neutral_count
        )
    
    def update_fish_outcomes(self, asset: str, outcome: float) -> None:
        """
        Update all fish with the actual market outcome.
        
        Args:
            asset: Asset that was traded
            outcome: Actual price change (positive = up, negative = down)
        """
        for fish in self.fish.values():
            if fish.status in [FishStatus.ACTIVE, FishStatus.SPAWNING]:
                # Get the last signal this fish generated
                if fish.memory.recent_signals:
                    last_signal = fish.memory.recent_signals[-1][1]
                    fish.update_weight(outcome, last_signal)
    
    def cull_dead_fish(self) -> int:
        """Remove dead fish from the swarm"""
        dead_ids = [fid for fid, f in self.fish.items() if f.status == FishStatus.DEAD]
        
        for fid in dead_ids:
            fish = self.fish[fid]
            self.fish_by_category[fish.category].remove(fid)
            del self.fish[fid]
        
        if dead_ids:
            logger.info(f"Culled {len(dead_ids)} dead fish")
        
        return len(dead_ids)
    
    def get_swarm_stats(self) -> Dict[str, Any]:
        """Get statistics about the swarm"""
        active_count = sum(1 for f in self.fish.values() if f.status == FishStatus.ACTIVE)
        spawning_count = sum(1 for f in self.fish.values() if f.status == FishStatus.SPAWNING)
        
        category_counts = {
            cat.value: len(ids) for cat, ids in self.fish_by_category.items()
        }
        
        avg_weight = np.mean([f.current_weight for f in self.fish.values()]) if self.fish else 0
        avg_accuracy = np.mean([
            f.memory.correct_signals / max(1, f.memory.total_signals)
            for f in self.fish.values()
        ]) if self.fish else 0
        
        return {
            'total_fish': len(self.fish),
            'active_fish': active_count,
            'spawning_fish': spawning_count,
            'category_counts': category_counts,
            'avg_weight': avg_weight,
            'avg_accuracy': avg_accuracy
        }
    
    def to_dict(self) -> Dict[str, Any]:
        """Serialize swarm state"""
        return {
            'fish': {fid: f.to_dict() for fid, f in self.fish.items()},
            'stats': self.get_swarm_stats()
        }
