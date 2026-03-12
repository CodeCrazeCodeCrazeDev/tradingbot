"""
Quantitative & Statistical Edge Decisions (Concepts 101-110)

Advanced quantitative methods for extracting statistical edges from market data.
These concepts use mathematical models, information theory, entropy analysis,
fractal geometry, and regime-aware statistics to make trading decisions.
"""

import math
import random
import statistics
from collections import deque
from typing import Dict, List, Optional, Tuple

from .core_types import (
    DecisionConcept, DecisionContext, DecisionResult,
    DecisionCategory, DecisionAction, DecisionUrgency
)


class EntropyEdgeDecision(DecisionConcept):
    """
    Concept 101: Entropy Edge - Information-theoretic market analysis.
    
    Uses Shannon entropy to measure market disorder. Low entropy = predictable
    regime (trend-follow). High entropy = chaotic regime (mean-revert or sit out).
    Tracks entropy changes to detect regime transitions before they happen.
    """
    
    def __init__(self):
        super().__init__(101, "Entropy Edge", DecisionCategory.QUANTITATIVE_EDGE)
        self.entropy_history: deque = deque(maxlen=50)
        self.signal_history: deque = deque(maxlen=50)
    
    def decide(self, context: DecisionContext) -> DecisionResult:
        # Estimate market entropy from available signals
        signals = [context.trend, context.momentum, context.sentiment]
        
        # Convert to probability distribution (normalize to positive)
        shifted = [s + 1.0 for s in signals]  # shift to [0, 2]
        total = sum(shifted) + 1e-10
        probs = [s / total for s in shifted]
        
        # Shannon entropy: H = -sum(p * log2(p))
        entropy = 0.0
        for p in probs:
            if p > 1e-10:
                entropy -= p * math.log2(p)
        
        # Normalize entropy to [0, 1] (max entropy for 3 symbols = log2(3) ~ 1.585)
        max_entropy = math.log2(len(signals))
        normalized_entropy = entropy / max_entropy if max_entropy > 0 else 0.5
        
        self.entropy_history.append(normalized_entropy)
        
        # Entropy rate of change (entropy momentum)
        if len(self.entropy_history) >= 5:
            recent_entropy = list(self.entropy_history)[-5:]
            entropy_trend = recent_entropy[-1] - recent_entropy[0]
        else:
            entropy_trend = 0.0
        
        # Decision logic
        base_signal = context.trend * 0.5 + context.momentum * 0.5
        
        if normalized_entropy < 0.4:
            # Low entropy = ordered market = trend-follow with high confidence
            signal = base_signal * 1.3
            confidence = 0.8 - normalized_entropy
            reasoning = f"Low entropy ({normalized_entropy:.2f}): ordered market, trend-follow"
        elif normalized_entropy > 0.8:
            # High entropy = chaotic = reduce exposure or mean-revert
            signal = -base_signal * 0.3  # Fade the move
            confidence = 0.4
            reasoning = f"High entropy ({normalized_entropy:.2f}): chaotic, fading signal"
        else:
            # Medium entropy = normal conditions
            signal = base_signal
            confidence = 0.6
            reasoning = f"Medium entropy ({normalized_entropy:.2f}): normal conditions"
        
        # Entropy transition bonus: falling entropy = market ordering = opportunity
        if entropy_trend < -0.1:
            confidence *= 1.2
            reasoning += " | Entropy falling (ordering)"
        elif entropy_trend > 0.1:
            confidence *= 0.8
            reasoning += " | Entropy rising (disordering)"
        
        self.signal_history.append(signal)
        
        return self._create_result(
            action=self._signal_to_action(signal),
            confidence=min(confidence, 1.0),
            urgency=DecisionUrgency.HIGH if abs(entropy_trend) > 0.15 else DecisionUrgency.NORMAL,
            reasoning=reasoning,
            factors={
                'entropy': normalized_entropy,
                'entropy_trend': entropy_trend,
                'base_signal': base_signal,
                'final_signal': signal
            }
        )


class FractalDimensionDecision(DecisionConcept):
    """
    Concept 102: Fractal Dimension - Hurst exponent approximation.
    
    Estimates the fractal dimension of price action to determine if the market
    is trending (H > 0.5), mean-reverting (H < 0.5), or random walk (H ~ 0.5).
    Uses rescaled range analysis on available signals.
    """
    
    def __init__(self):
        super().__init__(102, "Fractal Dimension", DecisionCategory.QUANTITATIVE_EDGE)
        self.price_memory: deque = deque(maxlen=100)
        self.hurst_history: deque = deque(maxlen=30)
    
    def decide(self, context: DecisionContext) -> DecisionResult:
        self.price_memory.append(context.price)
        
        # Estimate Hurst exponent from signal persistence
        if len(self.price_memory) >= 20:
            hurst = self._estimate_hurst(list(self.price_memory))
        else:
            # Fallback: infer from trend/momentum agreement
            agreement = 1.0 if (context.trend > 0) == (context.momentum > 0) else 0.0
            hurst = 0.3 + agreement * 0.4  # Map to [0.3, 0.7]
        
        self.hurst_history.append(hurst)
        
        base_signal = context.trend * 0.5 + context.momentum * 0.5
        
        if hurst > 0.6:
            # Persistent / trending: follow the trend
            signal = base_signal * (1.0 + (hurst - 0.5) * 2)
            confidence = min(hurst, 0.95)
            strategy = "trend-follow"
        elif hurst < 0.4:
            # Anti-persistent / mean-reverting: fade the move
            signal = -base_signal * (1.0 + (0.5 - hurst) * 2)
            confidence = min(1.0 - hurst, 0.85)
            strategy = "mean-revert"
        else:
            # Random walk: low conviction
            signal = base_signal * 0.3
            confidence = 0.3
            strategy = "random-walk"
        
        # Hurst regime change detection
        if len(self.hurst_history) >= 10:
            recent = list(self.hurst_history)[-5:]
            older = list(self.hurst_history)[-10:-5]
            hurst_shift = statistics.mean(recent) - statistics.mean(older)
        else:
            hurst_shift = 0.0
        
        if abs(hurst_shift) > 0.1:
            confidence *= 0.7  # Reduce confidence during regime change
            strategy += " (regime-shifting)"
        
        return self._create_result(
            action=self._signal_to_action(signal),
            confidence=min(confidence, 1.0),
            urgency=DecisionUrgency.HIGH if abs(hurst_shift) > 0.15 else DecisionUrgency.NORMAL,
            reasoning=f"Hurst={hurst:.2f} ({strategy})",
            factors={
                'hurst': hurst,
                'hurst_shift': hurst_shift,
                'strategy': strategy,
                'signal': signal
            }
        )
    
    def _estimate_hurst(self, prices: List[float]) -> float:
        """Simplified Hurst exponent estimation using R/S analysis"""
        n = len(prices)
        if n < 10:
            return 0.5
        
        # Calculate returns
        returns = [(prices[i] - prices[i-1]) / prices[i-1] if prices[i-1] != 0 else 0 
                   for i in range(1, n)]
        
        if not returns:
            return 0.5
        
        # R/S for different window sizes
        rs_values = []
        for window in [5, 10, 15, 20]:
            if window > len(returns):
                continue
            
            chunk = returns[-window:]
            mean_r = statistics.mean(chunk)
            deviations = [r - mean_r for r in chunk]
            cumulative = []
            running = 0
            for d in deviations:
                running += d
                cumulative.append(running)
            
            if not cumulative:
                continue
            
            R = max(cumulative) - min(cumulative)
            S = statistics.stdev(chunk) if len(chunk) > 1 else 1e-10
            
            if S > 1e-10:
                rs_values.append((math.log(window), math.log(R / S + 1e-10)))
        
        if len(rs_values) < 2:
            return 0.5
        
        # Linear regression slope = Hurst exponent
        x_vals = [v[0] for v in rs_values]
        y_vals = [v[1] for v in rs_values]
        x_mean = statistics.mean(x_vals)
        y_mean = statistics.mean(y_vals)
        
        numerator = sum((x - x_mean) * (y - y_mean) for x, y in zip(x_vals, y_vals))
        denominator = sum((x - x_mean) ** 2 for x in x_vals)
        
        if abs(denominator) < 1e-10:
            return 0.5
        
        hurst = numerator / denominator
        return max(0.0, min(1.0, hurst))


class ZScoreRegimedDecision(DecisionConcept):
    """
    Concept 103: Z-Score Regime Detection - Statistical deviation trading.
    
    Tracks rolling z-scores of price, volume, and volatility. Extreme z-scores
    signal mean-reversion opportunities. Moderate z-scores in trending regimes
    signal continuation. Adapts thresholds based on current regime.
    """
    
    def __init__(self):
        super().__init__(103, "Z-Score Regime", DecisionCategory.QUANTITATIVE_EDGE)
        self.trend_buffer: deque = deque(maxlen=50)
        self.momentum_buffer: deque = deque(maxlen=50)
        self.vol_buffer: deque = deque(maxlen=50)
    
    def decide(self, context: DecisionContext) -> DecisionResult:
        self.trend_buffer.append(context.trend)
        self.momentum_buffer.append(context.momentum)
        self.vol_buffer.append(context.volatility)
        
        # Calculate z-scores
        trend_z = self._zscore(list(self.trend_buffer))
        momentum_z = self._zscore(list(self.momentum_buffer))
        vol_z = self._zscore(list(self.vol_buffer))
        
        # Composite z-score
        composite_z = trend_z * 0.4 + momentum_z * 0.4 + vol_z * 0.2
        
        # Regime-adaptive thresholds
        if context.regime == 'trending':
            # In trends, z-scores can stay elevated longer
            extreme_threshold = 2.5
            entry_threshold = 1.0
        elif context.regime == 'volatile':
            # In volatile markets, wider thresholds
            extreme_threshold = 3.0
            entry_threshold = 1.5
        else:
            # Normal conditions
            extreme_threshold = 2.0
            entry_threshold = 1.0
        
        # Decision logic
        if abs(composite_z) > extreme_threshold:
            # Extreme deviation: mean-revert
            signal = -composite_z * 0.3  # Fade the extreme
            confidence = min(abs(composite_z) / extreme_threshold * 0.7, 0.9)
            urgency = DecisionUrgency.HIGH
            reasoning = f"Extreme z={composite_z:.2f}: mean-reversion"
        elif abs(composite_z) > entry_threshold:
            # Moderate deviation: follow if trending, fade if ranging
            if context.regime == 'trending':
                signal = composite_z * 0.4  # Follow
                reasoning = f"Moderate z={composite_z:.2f}: trend continuation"
            else:
                signal = -composite_z * 0.2  # Fade
                reasoning = f"Moderate z={composite_z:.2f}: range fade"
            confidence = 0.6
            urgency = DecisionUrgency.NORMAL
        else:
            # Normal range: weak signal
            signal = composite_z * 0.1
            confidence = 0.3
            urgency = DecisionUrgency.LOW
            reasoning = f"Normal z={composite_z:.2f}: no edge"
        
        # Volatility z-score penalty
        if vol_z > 2.0:
            confidence *= 0.7
            reasoning += " | High vol z-score"
        
        return self._create_result(
            action=self._signal_to_action(signal),
            confidence=min(confidence, 1.0),
            urgency=urgency,
            reasoning=reasoning,
            factors={
                'trend_z': trend_z,
                'momentum_z': momentum_z,
                'vol_z': vol_z,
                'composite_z': composite_z,
                'signal': signal
            }
        )
    
    def _zscore(self, values: List[float]) -> float:
        """Calculate z-score of the latest value"""
        if len(values) < 5:
            return 0.0
        mean = statistics.mean(values)
        std = statistics.stdev(values) if len(values) > 1 else 1e-10
        if std < 1e-10:
            return 0.0
        return (values[-1] - mean) / std


class KellyFractionDecision(DecisionConcept):
    """
    Concept 104: Kelly Fraction Optimizer - Optimal bet sizing as signal.
    
    Uses the Kelly Criterion to determine not just position size but also
    signal strength. A high Kelly fraction means the edge is strong enough
    to bet aggressively. A negative Kelly means the edge is negative.
    """
    
    def __init__(self):
        super().__init__(104, "Kelly Fraction", DecisionCategory.QUANTITATIVE_EDGE)
        self.outcome_history: deque = deque(maxlen=100)
        self.return_history: deque = deque(maxlen=100)
    
    def decide(self, context: DecisionContext) -> DecisionResult:
        # Estimate win probability and payoff ratio
        win_prob = context.win_rate
        
        # Estimate average win/loss ratio from context
        if context.volatility > 0:
            # Higher trend alignment = better payoff ratio
            alignment = abs(context.trend * context.momentum)
            avg_win = 1.5 + alignment  # 1.5x to 2.5x
            avg_loss = 1.0
        else:
            avg_win = 1.5
            avg_loss = 1.0
        
        # Kelly fraction: f* = (bp - q) / b
        # where b = avg_win/avg_loss, p = win_prob, q = 1 - win_prob
        b = avg_win / avg_loss if avg_loss > 0 else 1.5
        p = win_prob
        q = 1.0 - p
        
        kelly = (b * p - q) / b if b > 0 else 0.0
        
        # Half-Kelly for safety
        half_kelly = kelly * 0.5
        
        # Base signal from market data
        base_signal = context.trend * 0.4 + context.momentum * 0.4 + context.sentiment * 0.2
        
        # Kelly-weighted signal
        if kelly > 0.1:
            # Positive edge: trade in signal direction, sized by Kelly
            signal = base_signal * (1.0 + kelly)
            confidence = min(kelly * 2, 0.95)
            reasoning = f"Kelly={kelly:.2%}: positive edge, sizing up"
        elif kelly > 0:
            # Small edge: trade cautiously
            signal = base_signal * 0.5
            confidence = 0.4
            reasoning = f"Kelly={kelly:.2%}: marginal edge"
        elif kelly > -0.1:
            # No edge: sit out
            signal = 0.0
            confidence = 0.2
            reasoning = f"Kelly={kelly:.2%}: no edge"
        else:
            # Negative edge: the opposite direction might work
            signal = -base_signal * 0.3
            confidence = 0.3
            reasoning = f"Kelly={kelly:.2%}: negative edge, fading"
        
        # Drawdown adjustment: reduce Kelly when in drawdown
        if context.drawdown > 0.1:
            drawdown_factor = max(0.3, 1.0 - context.drawdown * 2)
            signal *= drawdown_factor
            confidence *= drawdown_factor
            reasoning += f" | DD adj: {drawdown_factor:.2f}"
        
        return self._create_result(
            action=self._signal_to_action(signal),
            confidence=min(confidence, 1.0),
            urgency=DecisionUrgency.HIGH if kelly > 0.2 else DecisionUrgency.NORMAL,
            reasoning=reasoning,
            factors={
                'kelly': kelly,
                'half_kelly': half_kelly,
                'win_prob': win_prob,
                'payoff_ratio': b,
                'signal': signal
            }
        )


class MeanReversionZoneDecision(DecisionConcept):
    """
    Concept 105: Mean Reversion Zone Detector - Bollinger-inspired statistical zones.
    
    Divides the signal space into statistical zones based on rolling mean and
    standard deviation. Identifies when price/signal is in extreme zones and
    calculates the probability of reversion based on historical zone transitions.
    """
    
    def __init__(self):
        super().__init__(105, "Mean Reversion Zone", DecisionCategory.QUANTITATIVE_EDGE)
        self.signal_buffer: deque = deque(maxlen=60)
        self.zone_transitions: deque = deque(maxlen=200)
        self.last_zone: Optional[int] = None
    
    def decide(self, context: DecisionContext) -> DecisionResult:
        # Composite signal
        composite = context.trend * 0.5 + context.momentum * 0.3 + context.sentiment * 0.2
        self.signal_buffer.append(composite)
        
        if len(self.signal_buffer) < 10:
            return self._create_result(
                DecisionAction.HOLD, 0.2, DecisionUrgency.LOW,
                "Insufficient data for zone detection",
                {'zone': 0, 'composite': composite}
            )
        
        # Calculate rolling statistics
        values = list(self.signal_buffer)
        mean = statistics.mean(values)
        std = statistics.stdev(values) if len(values) > 1 else 0.1
        
        if std < 1e-10:
            std = 0.1
        
        # Determine zone (-3 to +3 standard deviations)
        z = (composite - mean) / std
        zone = max(-3, min(3, round(z)))
        
        # Track zone transitions
        if self.last_zone is not None:
            self.zone_transitions.append((self.last_zone, zone))
        self.last_zone = zone
        
        # Calculate reversion probability from transition history
        reversion_prob = self._calculate_reversion_probability(zone)
        
        # Decision based on zone
        if zone >= 2:
            # Upper extreme: high reversion probability
            signal = -0.5 * (1 + (zone - 2) * 0.3)
            confidence = min(0.5 + reversion_prob * 0.4, 0.9)
            reasoning = f"Zone +{zone}: overbought, reversion prob={reversion_prob:.0%}"
        elif zone <= -2:
            # Lower extreme: high reversion probability
            signal = 0.5 * (1 + (abs(zone) - 2) * 0.3)
            confidence = min(0.5 + reversion_prob * 0.4, 0.9)
            reasoning = f"Zone {zone}: oversold, reversion prob={reversion_prob:.0%}"
        elif zone == 1:
            # Mildly bullish zone
            signal = 0.2
            confidence = 0.4
            reasoning = f"Zone +1: mildly bullish"
        elif zone == -1:
            # Mildly bearish zone
            signal = -0.2
            confidence = 0.4
            reasoning = f"Zone -1: mildly bearish"
        else:
            # Neutral zone
            signal = composite * 0.2
            confidence = 0.3
            reasoning = f"Zone 0: neutral"
        
        # Volatility regime adjustment
        if context.volatility > 0.3:
            confidence *= 0.8
            reasoning += " | High vol dampening"
        
        return self._create_result(
            action=self._signal_to_action(signal),
            confidence=min(confidence, 1.0),
            urgency=DecisionUrgency.HIGH if abs(zone) >= 3 else DecisionUrgency.NORMAL,
            reasoning=reasoning,
            factors={
                'zone': zone,
                'z_score': z,
                'reversion_prob': reversion_prob,
                'mean': mean,
                'std': std,
                'signal': signal
            }
        )
    
    def _calculate_reversion_probability(self, current_zone: int) -> float:
        """Calculate probability of reverting toward mean from current zone"""
        if not self.zone_transitions:
            # Prior: extreme zones revert ~70% of the time
            return 0.5 + abs(current_zone) * 0.1
        
        # Count transitions from similar zones
        similar_transitions = [
            (from_z, to_z) for from_z, to_z in self.zone_transitions
            if from_z == current_zone
        ]
        
        if not similar_transitions:
            return 0.5 + abs(current_zone) * 0.1
        
        # Count how many reverted (moved toward 0)
        reversions = sum(
            1 for from_z, to_z in similar_transitions
            if abs(to_z) < abs(from_z)
        )
        
        return reversions / len(similar_transitions)


class VolatilityRegimeClusterDecision(DecisionConcept):
    """
    Concept 106: Volatility Regime Clustering - K-means inspired vol regimes.
    
    Clusters historical volatility into distinct regimes (low, normal, high, extreme)
    and adapts trading strategy based on which cluster the current volatility
    belongs to. Each cluster has its own optimal signal weighting.
    """
    
    def __init__(self):
        super().__init__(106, "Volatility Regime Cluster", DecisionCategory.QUANTITATIVE_EDGE)
        self.vol_history: deque = deque(maxlen=200)
        # Cluster centroids (will adapt over time)
        self.centroids = [0.05, 0.15, 0.30, 0.50]  # low, normal, high, extreme
        self.cluster_weights = {
            0: {'trend': 0.6, 'momentum': 0.3, 'sentiment': 0.1, 'aggression': 1.2},
            1: {'trend': 0.4, 'momentum': 0.4, 'sentiment': 0.2, 'aggression': 1.0},
            2: {'trend': 0.3, 'momentum': 0.3, 'sentiment': 0.1, 'aggression': 0.6},
            3: {'trend': 0.2, 'momentum': 0.2, 'sentiment': 0.0, 'aggression': 0.3},
        }
        self.cluster_names = ['low_vol', 'normal_vol', 'high_vol', 'extreme_vol']
    
    def decide(self, context: DecisionContext) -> DecisionResult:
        self.vol_history.append(context.volatility)
        
        # Assign to nearest cluster
        cluster = self._assign_cluster(context.volatility)
        weights = self.cluster_weights[cluster]
        
        # Update centroids (online k-means step)
        if len(self.vol_history) >= 20:
            self._update_centroids()
        
        # Calculate signal using cluster-specific weights
        signal = (
            weights['trend'] * context.trend +
            weights['momentum'] * context.momentum +
            weights['sentiment'] * context.sentiment
        )
        signal *= weights['aggression']
        
        # Confidence based on cluster stability
        cluster_stability = self._calculate_cluster_stability()
        base_confidence = abs(signal) * 0.8
        confidence = base_confidence * cluster_stability
        
        # Cluster transition detection
        if len(self.vol_history) >= 5:
            prev_cluster = self._assign_cluster(list(self.vol_history)[-5])
            if prev_cluster != cluster:
                confidence *= 0.6  # Reduce confidence during transitions
                reasoning = f"Cluster transition: {self.cluster_names[prev_cluster]} -> {self.cluster_names[cluster]}"
            else:
                reasoning = f"Cluster: {self.cluster_names[cluster]} (stable)"
        else:
            reasoning = f"Cluster: {self.cluster_names[cluster]}"
        
        reasoning += f" | Aggression: {weights['aggression']:.1f}x"
        
        return self._create_result(
            action=self._signal_to_action(signal),
            confidence=min(confidence, 1.0),
            urgency=DecisionUrgency.HIGH if cluster >= 2 else DecisionUrgency.NORMAL,
            reasoning=reasoning,
            factors={
                'cluster': cluster,
                'cluster_name': self.cluster_names[cluster],
                'aggression': weights['aggression'],
                'stability': cluster_stability,
                'signal': signal
            }
        )
    
    def _assign_cluster(self, volatility: float) -> int:
        """Assign volatility to nearest cluster"""
        distances = [abs(volatility - c) for c in self.centroids]
        return distances.index(min(distances))
    
    def _update_centroids(self):
        """Online update of cluster centroids"""
        vol_list = list(self.vol_history)
        assignments = [self._assign_cluster(v) for v in vol_list]
        
        for k in range(4):
            cluster_vals = [v for v, a in zip(vol_list, assignments) if a == k]
            if cluster_vals:
                new_centroid = statistics.mean(cluster_vals)
                # Smooth update
                self.centroids[k] = 0.9 * self.centroids[k] + 0.1 * new_centroid
    
    def _calculate_cluster_stability(self) -> float:
        """How stable is the current cluster assignment"""
        if len(self.vol_history) < 10:
            return 0.5
        
        recent = list(self.vol_history)[-10:]
        clusters = [self._assign_cluster(v) for v in recent]
        
        # Stability = fraction of recent points in same cluster
        most_common = max(set(clusters), key=clusters.count)
        stability = clusters.count(most_common) / len(clusters)
        
        return stability


class InformationRatioDecision(DecisionConcept):
    """
    Concept 107: Information Ratio Signal - Risk-adjusted alpha detection.
    
    Calculates a rolling information ratio (excess return / tracking error)
    to determine if the current signal has genuine alpha or is just noise.
    Only trades when the information ratio exceeds a threshold.
    """
    
    def __init__(self):
        super().__init__(107, "Information Ratio", DecisionCategory.QUANTITATIVE_EDGE)
        self.signal_returns: deque = deque(maxlen=50)
        self.benchmark_returns: deque = deque(maxlen=50)
        self.prev_signal: Optional[float] = None
    
    def decide(self, context: DecisionContext) -> DecisionResult:
        # Current signal
        current_signal = context.trend * 0.4 + context.momentum * 0.4 + context.sentiment * 0.2
        
        # Track signal "returns" (change in signal value)
        if self.prev_signal is not None:
            signal_return = current_signal - self.prev_signal
            benchmark_return = 0.0  # Benchmark = doing nothing
            
            self.signal_returns.append(signal_return)
            self.benchmark_returns.append(benchmark_return)
        
        self.prev_signal = current_signal
        
        # Calculate Information Ratio
        if len(self.signal_returns) >= 10:
            excess_returns = [
                s - b for s, b in zip(self.signal_returns, self.benchmark_returns)
            ]
            
            mean_excess = statistics.mean(excess_returns)
            tracking_error = statistics.stdev(excess_returns) if len(excess_returns) > 1 else 1e-10
            
            if tracking_error > 1e-10:
                info_ratio = mean_excess / tracking_error
            else:
                info_ratio = 0.0
            
            # Annualize (approximate)
            info_ratio_annualized = info_ratio * math.sqrt(252)
        else:
            info_ratio = 0.0
            info_ratio_annualized = 0.0
        
        # Decision based on information ratio
        if info_ratio_annualized > 1.5:
            # Strong alpha signal
            signal = current_signal * 1.3
            confidence = min(0.5 + info_ratio_annualized * 0.15, 0.95)
            reasoning = f"IR={info_ratio_annualized:.2f}: strong alpha detected"
        elif info_ratio_annualized > 0.5:
            # Moderate alpha
            signal = current_signal
            confidence = 0.5 + info_ratio_annualized * 0.1
            reasoning = f"IR={info_ratio_annualized:.2f}: moderate alpha"
        elif info_ratio_annualized > -0.5:
            # No alpha: weak signal
            signal = current_signal * 0.3
            confidence = 0.3
            reasoning = f"IR={info_ratio_annualized:.2f}: no alpha, noise"
        else:
            # Negative alpha: fade
            signal = -current_signal * 0.3
            confidence = 0.4
            reasoning = f"IR={info_ratio_annualized:.2f}: negative alpha, fading"
        
        return self._create_result(
            action=self._signal_to_action(signal),
            confidence=min(confidence, 1.0),
            urgency=DecisionUrgency.HIGH if info_ratio_annualized > 2.0 else DecisionUrgency.NORMAL,
            reasoning=reasoning,
            factors={
                'info_ratio': info_ratio,
                'info_ratio_annualized': info_ratio_annualized,
                'current_signal': current_signal,
                'signal': signal
            }
        )


class TailRiskHarvesterDecision(DecisionConcept):
    """
    Concept 108: Tail Risk Harvester - Profit from fat-tailed distributions.
    
    Detects when the market is exhibiting fat-tailed behavior (kurtosis > 3)
    and positions to either harvest tail risk premium or protect against
    tail events. Uses rolling kurtosis and skewness to assess distribution shape.
    """
    
    def __init__(self):
        super().__init__(108, "Tail Risk Harvester", DecisionCategory.QUANTITATIVE_EDGE)
        self.return_buffer: deque = deque(maxlen=100)
        self.prev_price: Optional[float] = None
    
    def decide(self, context: DecisionContext) -> DecisionResult:
        # Track returns
        if self.prev_price is not None and self.prev_price > 0:
            ret = (context.price - self.prev_price) / self.prev_price
            self.return_buffer.append(ret)
        self.prev_price = context.price
        
        if len(self.return_buffer) < 20:
            return self._create_result(
                DecisionAction.HOLD, 0.2, DecisionUrgency.LOW,
                "Insufficient data for tail analysis",
                {'kurtosis': 0, 'skewness': 0}
            )
        
        returns = list(self.return_buffer)
        
        # Calculate distribution moments
        mean_r = statistics.mean(returns)
        std_r = statistics.stdev(returns) if len(returns) > 1 else 1e-10
        
        if std_r < 1e-10:
            std_r = 1e-10
        
        # Skewness
        n = len(returns)
        skewness = sum(((r - mean_r) / std_r) ** 3 for r in returns) / n
        
        # Excess kurtosis (normal = 0)
        kurtosis = sum(((r - mean_r) / std_r) ** 4 for r in returns) / n - 3.0
        
        base_signal = context.trend * 0.5 + context.momentum * 0.5
        
        # Decision logic based on distribution shape
        if kurtosis > 3.0:
            # Very fat tails: high risk of extreme moves
            if skewness > 0.5:
                # Positive skew: upside tail risk, be cautious long
                signal = base_signal * 0.4
                confidence = 0.5
                reasoning = f"Fat tails (K={kurtosis:.1f}), +skew: cautious upside"
            elif skewness < -0.5:
                # Negative skew: downside tail risk, protect
                signal = -abs(base_signal) * 0.3
                confidence = 0.6
                reasoning = f"Fat tails (K={kurtosis:.1f}), -skew: downside protection"
            else:
                # Symmetric fat tails: reduce exposure
                signal = base_signal * 0.2
                confidence = 0.4
                reasoning = f"Fat tails (K={kurtosis:.1f}), symmetric: reduce exposure"
            urgency = DecisionUrgency.HIGH
        elif kurtosis > 1.0:
            # Moderately fat tails
            signal = base_signal * 0.7
            confidence = 0.5
            urgency = DecisionUrgency.NORMAL
            reasoning = f"Moderate tails (K={kurtosis:.1f}): slightly cautious"
        elif kurtosis < -0.5:
            # Thin tails (platykurtic): safe to be more aggressive
            signal = base_signal * 1.3
            confidence = 0.7
            urgency = DecisionUrgency.NORMAL
            reasoning = f"Thin tails (K={kurtosis:.1f}): safe to be aggressive"
        else:
            # Near-normal distribution
            signal = base_signal
            confidence = 0.5
            urgency = DecisionUrgency.NORMAL
            reasoning = f"Normal tails (K={kurtosis:.1f}): standard approach"
        
        return self._create_result(
            action=self._signal_to_action(signal),
            confidence=min(confidence, 1.0),
            urgency=urgency,
            reasoning=reasoning,
            factors={
                'kurtosis': kurtosis,
                'skewness': skewness,
                'mean_return': mean_r,
                'std_return': std_r,
                'signal': signal
            }
        )


class CrossCorrelationDecision(DecisionConcept):
    """
    Concept 109: Cross-Correlation Decay - Signal correlation lifecycle.
    
    Tracks the rolling correlation between trend and momentum signals.
    When correlation is high, signals are redundant (lower confidence).
    When correlation breaks down, it signals a regime change.
    Uses correlation decay rate to predict signal reliability.
    """
    
    def __init__(self):
        super().__init__(109, "Cross-Correlation Decay", DecisionCategory.QUANTITATIVE_EDGE)
        self.trend_buffer: deque = deque(maxlen=50)
        self.momentum_buffer: deque = deque(maxlen=50)
        self.correlation_history: deque = deque(maxlen=30)
    
    def decide(self, context: DecisionContext) -> DecisionResult:
        self.trend_buffer.append(context.trend)
        self.momentum_buffer.append(context.momentum)
        
        if len(self.trend_buffer) < 10:
            signal = context.trend * 0.5 + context.momentum * 0.5
            return self._create_result(
                self._signal_to_action(signal), 0.3, DecisionUrgency.LOW,
                "Building correlation history",
                {'correlation': 0, 'signal': signal}
            )
        
        # Calculate rolling correlation
        trends = list(self.trend_buffer)
        momentums = list(self.momentum_buffer)
        correlation = self._pearson_correlation(trends, momentums)
        self.correlation_history.append(correlation)
        
        # Correlation decay rate
        if len(self.correlation_history) >= 5:
            recent_corr = list(self.correlation_history)[-5:]
            corr_slope = (recent_corr[-1] - recent_corr[0]) / 5
        else:
            corr_slope = 0.0
        
        base_signal = context.trend * 0.5 + context.momentum * 0.5
        
        # Decision logic
        if correlation > 0.8:
            # High correlation: signals agree but are redundant
            signal = base_signal * 0.8
            confidence = 0.6
            reasoning = f"High corr ({correlation:.2f}): signals aligned but redundant"
        elif correlation > 0.3:
            # Moderate correlation: healthy signal diversity
            signal = base_signal * 1.1
            confidence = 0.7
            reasoning = f"Moderate corr ({correlation:.2f}): healthy signal mix"
        elif correlation > -0.3:
            # Low correlation: signals are independent (good for diversification)
            # Weight by individual strength
            if abs(context.trend) > abs(context.momentum):
                signal = context.trend * 0.7 + context.momentum * 0.3
            else:
                signal = context.trend * 0.3 + context.momentum * 0.7
            confidence = 0.5
            reasoning = f"Low corr ({correlation:.2f}): independent signals"
        else:
            # Negative correlation: signals disagree = uncertainty
            signal = base_signal * 0.3
            confidence = 0.3
            reasoning = f"Negative corr ({correlation:.2f}): signal conflict"
        
        # Correlation breakdown detection (rapid decay)
        if corr_slope < -0.1:
            confidence *= 0.7
            reasoning += f" | Corr breaking down (slope={corr_slope:.3f})"
        elif corr_slope > 0.1:
            confidence *= 1.1
            reasoning += f" | Corr strengthening (slope={corr_slope:.3f})"
        
        return self._create_result(
            action=self._signal_to_action(signal),
            confidence=min(confidence, 1.0),
            urgency=DecisionUrgency.HIGH if abs(corr_slope) > 0.15 else DecisionUrgency.NORMAL,
            reasoning=reasoning,
            factors={
                'correlation': correlation,
                'corr_slope': corr_slope,
                'signal': signal
            }
        )
    
    def _pearson_correlation(self, x: List[float], y: List[float]) -> float:
        """Calculate Pearson correlation coefficient"""
        n = min(len(x), len(y))
        if n < 3:
            return 0.0
        
        x = x[-n:]
        y = y[-n:]
        
        mean_x = statistics.mean(x)
        mean_y = statistics.mean(y)
        
        numerator = sum((xi - mean_x) * (yi - mean_y) for xi, yi in zip(x, y))
        denom_x = sum((xi - mean_x) ** 2 for xi in x)
        denom_y = sum((yi - mean_y) ** 2 for yi in y)
        
        denominator = math.sqrt(denom_x * denom_y)
        
        if denominator < 1e-10:
            return 0.0
        
        return numerator / denominator


class BayesianSurpriseDecision(DecisionConcept):
    """
    Concept 110: Bayesian Surprise - Trade on unexpected information.
    
    Maintains a Bayesian prior over market direction and updates it with
    each new observation. When the posterior diverges significantly from
    the prior (high KL divergence = surprise), it signals a trading opportunity.
    Surprise in the direction of the trend = strong signal.
    """
    
    def __init__(self):
        super().__init__(110, "Bayesian Surprise", DecisionCategory.QUANTITATIVE_EDGE)
        # Prior: probability of [down, neutral, up]
        self.prior = [0.33, 0.34, 0.33]
        self.surprise_history: deque = deque(maxlen=30)
        self.learning_rate = 0.15
    
    def decide(self, context: DecisionContext) -> DecisionResult:
        # Observe current market state
        composite = context.trend * 0.4 + context.momentum * 0.4 + context.sentiment * 0.2
        
        # Convert observation to likelihood
        if composite > 0.2:
            likelihood = [0.1, 0.2, 0.7]  # Likely up
        elif composite < -0.2:
            likelihood = [0.7, 0.2, 0.1]  # Likely down
        else:
            likelihood = [0.25, 0.50, 0.25]  # Neutral
        
        # Bayesian update: posterior = prior * likelihood (normalized)
        unnormalized = [p * l for p, l in zip(self.prior, likelihood)]
        total = sum(unnormalized) + 1e-10
        posterior = [u / total for u in unnormalized]
        
        # Calculate KL divergence (surprise)
        kl_divergence = 0.0
        for post, pri in zip(posterior, self.prior):
            if post > 1e-10 and pri > 1e-10:
                kl_divergence += post * math.log(post / pri)
        
        self.surprise_history.append(kl_divergence)
        
        # Average surprise level
        if len(self.surprise_history) >= 5:
            avg_surprise = statistics.mean(list(self.surprise_history))
        else:
            avg_surprise = kl_divergence
        
        # Determine direction of surprise
        surprise_direction = posterior[2] - posterior[0]  # up_prob - down_prob
        
        # Decision logic
        if kl_divergence > avg_surprise * 1.5 and kl_divergence > 0.1:
            # High surprise: significant new information
            signal = surprise_direction * (1.0 + kl_divergence)
            confidence = min(0.5 + kl_divergence * 0.5, 0.9)
            urgency = DecisionUrgency.HIGH
            reasoning = f"Bayesian surprise={kl_divergence:.3f}: unexpected info, dir={surprise_direction:.2f}"
        elif kl_divergence > 0.05:
            # Moderate surprise
            signal = surprise_direction * 0.7
            confidence = 0.5
            urgency = DecisionUrgency.NORMAL
            reasoning = f"Moderate surprise={kl_divergence:.3f}"
        else:
            # No surprise: market behaving as expected
            signal = surprise_direction * 0.3
            confidence = 0.3
            urgency = DecisionUrgency.LOW
            reasoning = f"No surprise={kl_divergence:.3f}: as expected"
        
        # Update prior (slow adaptation)
        self.prior = [
            (1 - self.learning_rate) * p + self.learning_rate * post
            for p, post in zip(self.prior, posterior)
        ]
        # Normalize
        total = sum(self.prior)
        self.prior = [p / total for p in self.prior]
        
        return self._create_result(
            action=self._signal_to_action(signal),
            confidence=min(confidence, 1.0),
            urgency=urgency,
            reasoning=reasoning,
            factors={
                'kl_divergence': kl_divergence,
                'surprise_direction': surprise_direction,
                'posterior_up': posterior[2],
                'posterior_down': posterior[0],
                'posterior_neutral': posterior[1],
                'signal': signal
            }
        )


# Export all concepts in this category
QUANTITATIVE_EDGE_CONCEPTS = [
    EntropyEdgeDecision,
    FractalDimensionDecision,
    ZScoreRegimedDecision,
    KellyFractionDecision,
    MeanReversionZoneDecision,
    VolatilityRegimeClusterDecision,
    InformationRatioDecision,
    TailRiskHarvesterDecision,
    CrossCorrelationDecision,
    BayesianSurpriseDecision,
]
