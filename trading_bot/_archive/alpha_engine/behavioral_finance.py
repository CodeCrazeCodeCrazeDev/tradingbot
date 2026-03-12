"""
Behavioral Finance Integration Module
======================================

Comprehensive behavioral finance analysis:
- Multi-Dimensional Emotion Detection
- Retail Trader Positioning (Fade the Crowd)
- Institutional Flow Detection (Smart Money)
- Sentiment Extremes and Contrarian Signals
"""

import numpy as np
import pandas as pd
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Tuple
from collections import deque
import logging
from datetime import datetime, timedelta
from abc import ABC, abstractmethod
import re
import numpy
import pandas

logger = logging.getLogger(__name__)


class EmotionType(Enum):
    """Types of market emotions"""
    FEAR = "fear"
    GREED = "greed"
    UNCERTAINTY = "uncertainty"
    CONFIDENCE = "confidence"
    ANGER = "anger"
    HOPE = "hope"
    PANIC = "panic"
    EUPHORIA = "euphoria"


class CrowdBehavior(Enum):
    """Crowd behavior states"""
    EXTREME_BULLISH = "extreme_bullish"
    BULLISH = "bullish"
    NEUTRAL = "neutral"
    BEARISH = "bearish"
    EXTREME_BEARISH = "extreme_bearish"


class SmartMoneyAction(Enum):
    """Smart money actions"""
    ACCUMULATING = "accumulating"
    DISTRIBUTING = "distributing"
    NEUTRAL = "neutral"


@dataclass
class EmotionProfile:
    """Market emotion profile"""
    timestamp: datetime
    symbol: str
    
    # Emotion scores (0-100)
    fear: float
    greed: float
    uncertainty: float
    confidence: float
    anger: float
    hope: float
    
    # Derived metrics
    dominant_emotion: EmotionType
    emotion_intensity: float
    
    # Trading implications
    contrarian_signal: Optional[str]
    position_adjustment: float


@dataclass
class RetailPositioning:
    """Retail trader positioning data"""
    timestamp: datetime
    symbol: str
    
    # Positioning
    long_ratio: float  # 0-1
    short_ratio: float
    net_position: float  # -1 to 1
    
    # Historical context
    percentile_rank: float  # Where current positioning ranks historically
    
    # Signal
    crowd_behavior: CrowdBehavior
    fade_signal: Optional[str]  # 'long' or 'short' to fade
    signal_strength: float


@dataclass
class InstitutionalFlow:
    """Institutional flow data"""
    timestamp: datetime
    symbol: str
    
    # Flow metrics
    block_trade_volume: float
    dark_pool_volume: float
    options_flow_score: float
    
    # Direction
    net_flow: float  # Positive = buying, negative = selling
    action: SmartMoneyAction
    
    # Confidence
    confidence: float
    
    # Signal
    follow_signal: Optional[str]
    signal_strength: float


class EmotionDetector:
    """
    Multi-Dimensional Emotion Detection
    
    Analyzes market emotions beyond simple positive/negative
    """
    
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        
        # Emotion keywords
        self.emotion_keywords = {
            EmotionType.FEAR: [
                'fear', 'scared', 'worried', 'panic', 'crash', 'collapse',
                'plunge', 'crisis', 'disaster', 'catastrophe', 'doom',
                'sell-off', 'bloodbath', 'carnage', 'meltdown',
            ],
            EmotionType.GREED: [
                'greed', 'fomo', 'moon', 'rocket', 'lambo', 'rich',
                'millionaire', 'all-in', 'yolo', 'diamond hands',
                'to the moon', 'buy the dip', 'never sell',
            ],
            EmotionType.UNCERTAINTY: [
                'uncertain', 'unclear', 'confused', 'mixed', 'volatile',
                'unpredictable', 'unknown', 'maybe', 'might', 'could',
                'possibly', 'depends', 'wait and see',
            ],
            EmotionType.CONFIDENCE: [
                'confident', 'certain', 'sure', 'bullish', 'strong',
                'solid', 'conviction', 'guaranteed', 'definitely',
                'no doubt', 'obvious', 'clear',
            ],
            EmotionType.ANGER: [
                'angry', 'furious', 'manipulation', 'rigged', 'scam',
                'fraud', 'cheated', 'unfair', 'corrupt', 'criminals',
                'revenge', 'fight back',
            ],
            EmotionType.HOPE: [
                'hope', 'hopeful', 'optimistic', 'recovery', 'rebound',
                'turnaround', 'bottom', 'opportunity', 'undervalued',
                'oversold', 'bargain',
            ],
        }
        
        # VIX correlation for fear
        self.vix_history: deque = deque(maxlen=100)
        
        # Emotion history
        self.emotion_history: Dict[str, deque] = {}
    
    def analyze_text(self, text: str) -> Dict[EmotionType, float]:
        """
        Analyze text for emotions
        
        Args:
            text: Text to analyze
            
        Returns:
            Dictionary of emotion scores
        """
        text_lower = text.lower()
        scores = {}
        
        for emotion, keywords in self.emotion_keywords.items():
            count = sum(1 for kw in keywords if kw in text_lower)
            # Normalize by text length
            word_count = len(text_lower.split())
            scores[emotion] = min(count / max(word_count, 1) * 100, 100)
        
        return scores
    
    def update_vix(self, vix: float):
        """Update VIX for fear calculation"""
        self.vix_history.append(vix)
    
    def get_emotion_profile(self, symbol: str, texts: List[str],
                           vix: float = None) -> EmotionProfile:
        """
        Get comprehensive emotion profile
        
        Args:
            symbol: Trading symbol
            texts: List of texts to analyze
            vix: Current VIX level
            
        Returns:
            EmotionProfile
        """
        # Aggregate text emotions
        aggregated = {e: 0 for e in EmotionType}
        
        for text in texts:
            scores = self.analyze_text(text)
            for emotion, score in scores.items():
                aggregated[emotion] += score
        
        # Normalize
        if texts:
            for emotion in aggregated:
                aggregated[emotion] /= len(texts)
        
        # Adjust fear based on VIX
        if vix is not None:
            self.update_vix(vix)
            
            if len(self.vix_history) > 0:
                vix_percentile = sum(1 for v in self.vix_history if v < vix) / len(self.vix_history)
                # High VIX = high fear
                aggregated[EmotionType.FEAR] = max(
                    aggregated[EmotionType.FEAR],
                    vix_percentile * 100
                )
        
        # Find dominant emotion
        dominant = max(aggregated, key=aggregated.get)
        intensity = aggregated[dominant]
        
        # Determine contrarian signal
        contrarian_signal = None
        position_adjustment = 1.0
        
        if aggregated[EmotionType.FEAR] > 70 or aggregated.get(EmotionType.PANIC, 0) > 50:
            contrarian_signal = 'buy'  # Extreme fear = contrarian buy
            position_adjustment = 0.7  # But reduce size due to volatility
        elif aggregated[EmotionType.GREED] > 70 or aggregated.get(EmotionType.EUPHORIA, 0) > 50:
            contrarian_signal = 'sell'  # Extreme greed = contrarian sell
            position_adjustment = 0.7
        elif aggregated[EmotionType.UNCERTAINTY] > 60:
            position_adjustment = 0.5  # Reduce exposure during uncertainty
        
        profile = EmotionProfile(
            timestamp=datetime.now(),
            symbol=symbol,
            fear=aggregated.get(EmotionType.FEAR, 0),
            greed=aggregated.get(EmotionType.GREED, 0),
            uncertainty=aggregated.get(EmotionType.UNCERTAINTY, 0),
            confidence=aggregated.get(EmotionType.CONFIDENCE, 0),
            anger=aggregated.get(EmotionType.ANGER, 0),
            hope=aggregated.get(EmotionType.HOPE, 0),
            dominant_emotion=dominant,
            emotion_intensity=intensity,
            contrarian_signal=contrarian_signal,
            position_adjustment=position_adjustment,
        )
        
        # Store
        if symbol not in self.emotion_history:
            self.emotion_history[symbol] = deque(maxlen=100)
        self.emotion_history[symbol].append(profile)
        
        return profile


class RetailPositionTracker:
    """
    Tracks retail trader positioning for contrarian signals
    
    "Fade the retail crowd" strategy
    """
    
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        
        # Positioning history
        self.positioning_history: Dict[str, deque] = {}
        
        # Thresholds
        self.extreme_long_threshold = self.config.get('extreme_long_threshold', 0.80)
        self.extreme_short_threshold = self.config.get('extreme_short_threshold', 0.20)
    
    def update_positioning(self, symbol: str, long_ratio: float):
        """
        Update retail positioning
        
        Args:
            symbol: Trading symbol
            long_ratio: Ratio of retail traders who are long (0-1)
        """
        if symbol not in self.positioning_history:
            self.positioning_history[symbol] = deque(maxlen=500)
        
        self.positioning_history[symbol].append({
            'timestamp': datetime.now(),
            'long_ratio': long_ratio,
        })
    
    def get_positioning_signal(self, symbol: str) -> Optional[RetailPositioning]:
        """
        Get retail positioning signal
        
        Args:
            symbol: Trading symbol
            
        Returns:
            RetailPositioning or None
        """
        if symbol not in self.positioning_history:
            return None
        
        history = list(self.positioning_history[symbol])
        if not history:
            return None
        
        current = history[-1]
        long_ratio = current['long_ratio']
        short_ratio = 1 - long_ratio
        net_position = long_ratio - short_ratio  # -1 to 1
        
        # Calculate percentile rank
        historical_ratios = [h['long_ratio'] for h in history]
        percentile = sum(1 for r in historical_ratios if r < long_ratio) / len(historical_ratios)
        
        # Determine crowd behavior
        if long_ratio > self.extreme_long_threshold:
            behavior = CrowdBehavior.EXTREME_BULLISH
            fade_signal = 'short'  # Fade the crowd
            signal_strength = (long_ratio - self.extreme_long_threshold) / (1 - self.extreme_long_threshold)
        elif long_ratio < self.extreme_short_threshold:
            behavior = CrowdBehavior.EXTREME_BEARISH
            fade_signal = 'long'  # Fade the crowd
            signal_strength = (self.extreme_short_threshold - long_ratio) / self.extreme_short_threshold
        elif long_ratio > 0.6:
            behavior = CrowdBehavior.BULLISH
            fade_signal = None
            signal_strength = 0
        elif long_ratio < 0.4:
            behavior = CrowdBehavior.BEARISH
            fade_signal = None
            signal_strength = 0
        else:
            behavior = CrowdBehavior.NEUTRAL
            fade_signal = None
            signal_strength = 0
        
        return RetailPositioning(
            timestamp=datetime.now(),
            symbol=symbol,
            long_ratio=long_ratio,
            short_ratio=short_ratio,
            net_position=net_position,
            percentile_rank=percentile,
            crowd_behavior=behavior,
            fade_signal=fade_signal,
            signal_strength=signal_strength,
        )


class InstitutionalFlowTracker:
    """
    Tracks institutional (smart money) flow
    
    "Follow the smart money" strategy
    """
    
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        
        # Flow history
        self.flow_history: Dict[str, deque] = {}
        
        # Block trade threshold
        self.block_threshold = self.config.get('block_threshold', 10000)
        
        # Options flow threshold
        self.options_threshold = self.config.get('options_threshold', 1000000)
    
    def record_block_trade(self, symbol: str, size: float, side: str, price: float):
        """
        Record a block trade
        
        Args:
            symbol: Trading symbol
            size: Trade size
            side: 'buy' or 'sell'
            price: Trade price
        """
        if symbol not in self.flow_history:
            self.flow_history[symbol] = deque(maxlen=1000)
        
        if size >= self.block_threshold:
            self.flow_history[symbol].append({
                'timestamp': datetime.now(),
                'type': 'block',
                'size': size,
                'side': side,
                'price': price,
                'value': size * price,
            })
    
    def record_dark_pool_print(self, symbol: str, size: float, price: float):
        """
        Record a dark pool print
        
        Args:
            symbol: Trading symbol
            size: Trade size
            price: Trade price
        """
        if symbol not in self.flow_history:
            self.flow_history[symbol] = deque(maxlen=1000)
        
        self.flow_history[symbol].append({
            'timestamp': datetime.now(),
            'type': 'dark_pool',
            'size': size,
            'price': price,
            'value': size * price,
        })
    
    def record_options_flow(self, symbol: str, call_volume: float, put_volume: float,
                           call_premium: float, put_premium: float):
        """
        Record options flow
        
        Args:
            symbol: Trading symbol
            call_volume: Call option volume
            put_volume: Put option volume
            call_premium: Total call premium
            put_premium: Total put premium
        """
        if symbol not in self.flow_history:
            self.flow_history[symbol] = deque(maxlen=1000)
        
        # Calculate put/call ratio
        pc_ratio = put_volume / call_volume if call_volume > 0 else 1
        
        # Premium flow
        net_premium = call_premium - put_premium
        
        self.flow_history[symbol].append({
            'timestamp': datetime.now(),
            'type': 'options',
            'call_volume': call_volume,
            'put_volume': put_volume,
            'pc_ratio': pc_ratio,
            'net_premium': net_premium,
        })
    
    def get_institutional_flow(self, symbol: str, 
                               lookback_hours: int = 24) -> Optional[InstitutionalFlow]:
        """
        Get institutional flow analysis
        
        Args:
            symbol: Trading symbol
            lookback_hours: Hours to look back
            
        Returns:
            InstitutionalFlow or None
        """
        if symbol not in self.flow_history:
            return None
        
        cutoff = datetime.now() - timedelta(hours=lookback_hours)
        recent = [f for f in self.flow_history[symbol] if f['timestamp'] > cutoff]
        
        if not recent:
            return None
        
        # Aggregate flows
        block_buy_volume = 0
        block_sell_volume = 0
        dark_pool_volume = 0
        options_score = 0
        
        for flow in recent:
            if flow['type'] == 'block':
                if flow.get('side') == 'buy':
                    block_buy_volume += flow['value']
                else:
                    block_sell_volume += flow['value']
            elif flow['type'] == 'dark_pool':
                dark_pool_volume += flow['value']
            elif flow['type'] == 'options':
                # Bullish if net premium positive (more call buying)
                options_score += flow.get('net_premium', 0)
        
        # Calculate net flow
        block_net = block_buy_volume - block_sell_volume
        total_block = block_buy_volume + block_sell_volume
        
        if total_block > 0:
            net_flow = block_net / total_block  # -1 to 1
        else:
            net_flow = 0
        
        # Determine action
        if net_flow > 0.3:
            action = SmartMoneyAction.ACCUMULATING
            follow_signal = 'long'
            signal_strength = min(net_flow, 1.0)
        elif net_flow < -0.3:
            action = SmartMoneyAction.DISTRIBUTING
            follow_signal = 'short'
            signal_strength = min(abs(net_flow), 1.0)
        else:
            action = SmartMoneyAction.NEUTRAL
            follow_signal = None
            signal_strength = 0
        
        # Adjust for options flow
        if options_score > self.options_threshold:
            if action == SmartMoneyAction.ACCUMULATING:
                signal_strength *= 1.2
            elif action == SmartMoneyAction.NEUTRAL:
                action = SmartMoneyAction.ACCUMULATING
                follow_signal = 'long'
                signal_strength = 0.3
        elif options_score < -self.options_threshold:
            if action == SmartMoneyAction.DISTRIBUTING:
                signal_strength *= 1.2
            elif action == SmartMoneyAction.NEUTRAL:
                action = SmartMoneyAction.DISTRIBUTING
                follow_signal = 'short'
                signal_strength = 0.3
        
        return InstitutionalFlow(
            timestamp=datetime.now(),
            symbol=symbol,
            block_trade_volume=total_block,
            dark_pool_volume=dark_pool_volume,
            options_flow_score=options_score,
            net_flow=net_flow,
            action=action,
            confidence=min(signal_strength + 0.3, 1.0),
            follow_signal=follow_signal,
            signal_strength=signal_strength,
        )


class BehavioralFinanceEngine:
    """
    Unified Behavioral Finance Engine
    
    Combines all behavioral analysis for trading signals
    """
    
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        
        # Initialize components
        self.emotion_detector = EmotionDetector(config.get('emotion', {}))
        self.retail_tracker = RetailPositionTracker(config.get('retail', {}))
        self.institutional_tracker = InstitutionalFlowTracker(config.get('institutional', {}))
        
        # Signal history
        self.signal_history: deque = deque(maxlen=1000)
    
    def get_behavioral_signal(self, symbol: str, texts: List[str] = None,
                             retail_long_ratio: float = None,
                             vix: float = None) -> Dict[str, Any]:
        """
        Get comprehensive behavioral signal
        
        Args:
            symbol: Trading symbol
            texts: Social media/news texts
            retail_long_ratio: Retail positioning
            vix: Current VIX
            
        Returns:
            Behavioral signal dictionary
        """
        signals = {}
        
        # Emotion analysis
        if texts:
            emotion = self.emotion_detector.get_emotion_profile(symbol, texts, vix)
            signals['emotion'] = {
                'dominant': emotion.dominant_emotion.value,
                'intensity': emotion.emotion_intensity,
                'fear': emotion.fear,
                'greed': emotion.greed,
                'contrarian_signal': emotion.contrarian_signal,
                'position_adjustment': emotion.position_adjustment,
            }
        
        # Retail positioning
        if retail_long_ratio is not None:
            self.retail_tracker.update_positioning(symbol, retail_long_ratio)
            retail = self.retail_tracker.get_positioning_signal(symbol)
            if retail:
                signals['retail'] = {
                    'long_ratio': retail.long_ratio,
                    'crowd_behavior': retail.crowd_behavior.value,
                    'fade_signal': retail.fade_signal,
                    'signal_strength': retail.signal_strength,
                }
        
        # Institutional flow
        institutional = self.institutional_tracker.get_institutional_flow(symbol)
        if institutional:
            signals['institutional'] = {
                'action': institutional.action.value,
                'net_flow': institutional.net_flow,
                'follow_signal': institutional.follow_signal,
                'signal_strength': institutional.signal_strength,
                'confidence': institutional.confidence,
            }
        
        # Combine signals
        combined_signal = self._combine_signals(signals)
        
        result = {
            'symbol': symbol,
            'timestamp': datetime.now(),
            'individual_signals': signals,
            'combined': combined_signal,
        }
        
        self.signal_history.append(result)
        
        return result
    
    def _combine_signals(self, signals: Dict[str, Any]) -> Dict[str, Any]:
        """Combine individual signals into unified signal"""
        direction_votes = {'long': 0, 'short': 0, 'neutral': 0}
        total_weight = 0
        position_adjustment = 1.0
        
        # Emotion signal (contrarian)
        if 'emotion' in signals:
            emotion = signals['emotion']
            if emotion['contrarian_signal'] == 'buy':
                direction_votes['long'] += 0.3
            elif emotion['contrarian_signal'] == 'sell':
                direction_votes['short'] += 0.3
            else:
                direction_votes['neutral'] += 0.3
            total_weight += 0.3
            position_adjustment *= emotion['position_adjustment']
        
        # Retail signal (contrarian - fade the crowd)
        if 'retail' in signals:
            retail = signals['retail']
            if retail['fade_signal'] == 'long':
                direction_votes['long'] += 0.3 * retail['signal_strength']
            elif retail['fade_signal'] == 'short':
                direction_votes['short'] += 0.3 * retail['signal_strength']
            else:
                direction_votes['neutral'] += 0.3
            total_weight += 0.3
        
        # Institutional signal (follow smart money)
        if 'institutional' in signals:
            inst = signals['institutional']
            if inst['follow_signal'] == 'long':
                direction_votes['long'] += 0.4 * inst['signal_strength']
            elif inst['follow_signal'] == 'short':
                direction_votes['short'] += 0.4 * inst['signal_strength']
            else:
                direction_votes['neutral'] += 0.4
            total_weight += 0.4
        
        # Determine direction
        if total_weight == 0:
            return {
                'direction': 'neutral',
                'strength': 0,
                'position_adjustment': 1.0,
                'confidence': 0,
            }
        
        # Normalize votes
        for d in direction_votes:
            direction_votes[d] /= total_weight
        
        direction = max(direction_votes, key=direction_votes.get)
        strength = direction_votes[direction]
        
        # Check for conflicting signals
        if direction_votes['long'] > 0.3 and direction_votes['short'] > 0.3:
            # Conflicting signals - reduce confidence
            confidence = 0.3
            position_adjustment *= 0.5
        else:
            confidence = strength
        
        return {
            'direction': direction,
            'strength': strength,
            'position_adjustment': position_adjustment,
            'confidence': confidence,
            'votes': direction_votes,
        }
