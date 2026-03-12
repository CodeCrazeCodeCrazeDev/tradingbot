"""
Trader Consciousness Module - Self-Learning and Adaptive Psychology System for Elite Trading Bot

This module implements advanced trader psychology and consciousness capabilities including:
- Self-Learning Trading Journal with Pattern Recognition
- Emotional State Tracking and Regulation
- Adaptive Neuro-Plasticity for Strategy Evolution
- Performance Psychology Analysis
- Cognitive Bias Detection and Mitigation
- Market Intuition Development System
"""

import logging
import numpy as np
from typing import Any, Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum
import math
from datetime import datetime, timedelta
from collections import defaultdict, deque
from pathlib import Path

try:
    from sklearn.cluster import KMeans
except ImportError:
    KMeans = None

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class EmotionalState(Enum):
    """Trader Emotional States"""
    EUPHORIC = "euphoric"
    CONFIDENT = "confident"
    NEUTRAL = "neutral"
    ANXIOUS = "anxious"
    FEARFUL = "fearful"
    GREEDY = "greedy"
    FRUSTRATED = "frustrated"
    DISCIPLINED = "disciplined"

class CognitiveBias(Enum):
    """Common Trading Cognitive Biases"""
    CONFIRMATION_BIAS = "confirmation_bias"
    ANCHORING_BIAS = "anchoring_bias"
    OVERCONFIDENCE = "overconfidence"
    LOSS_AVERSION = "loss_aversion"
    RECENCY_BIAS = "recency_bias"
    GAMBLERS_FALLACY = "gamblers_fallacy"
    HERD_MENTALITY = "herd_mentality"
    SUNK_COST_FALLACY = "sunk_cost_fallacy"

class LearningMode(Enum):
    """Learning Adaptation Modes"""
    EXPLORATION = "exploration"
    EXPLOITATION = "exploitation"
    BALANCED = "balanced"
    CONSERVATIVE = "conservative"
    AGGRESSIVE = "aggressive"

@dataclass
class TradeEntry:
    """Individual Trade Journal Entry"""
    trade_id: str
    symbol: str
    entry_time: datetime
    exit_time: Optional[datetime]
    entry_price: float
    exit_price: Optional[float]
    size: float
    direction: str  # 'long' or 'short'
    pnl: Optional[float]
    pnl_percent: Optional[float]
    
    # Psychology metrics
    emotional_state_entry: EmotionalState
    emotional_state_exit: Optional[EmotionalState]
    confidence_level: float  # 0-1
    stress_level: float      # 0-1
    
    # Strategy context
    strategy_used: str
    market_conditions: Dict[str, Any]
    setup_quality: float     # 0-1
    execution_quality: float # 0-1
    
    # Learning insights
    lessons_learned: List[str]
    mistakes_made: List[str]
    cognitive_biases: List[CognitiveBias]
    
    # Performance metrics
    risk_reward_ratio: Optional[float]
    hold_time: Optional[timedelta]
    max_favorable_excursion: Optional[float]
    max_adverse_excursion: Optional[float]

@dataclass
class PsychologyMetrics:
    """Trader Psychology Assessment"""
    overall_emotional_stability: float
    discipline_score: float
    patience_level: float
    risk_tolerance: float
    confidence_calibration: float
    bias_susceptibility: Dict[CognitiveBias, float]
    stress_resilience: float
    learning_rate: float
    adaptation_speed: float
    
class EmotionalTracker:
    """Advanced Emotional State Tracking and Analysis"""
    
    def __init__(self):
        self.emotion_history = []
        self.emotion_triggers = {}
        self.regulation_strategies = {}
        
    def analyze_emotional_state(self, market_data: Dict[str, Any], 
                              portfolio_status: Dict[str, Any]) -> EmotionalState:
        """Analyze current emotional state based on market and portfolio conditions"""
        
        # Calculate emotional indicators
        pnl_today = portfolio_status.get('pnl_today', 0.0)
        pnl_percent = portfolio_status.get('pnl_percent', 0.0)
        drawdown = portfolio_status.get('current_drawdown', 0.0)
        win_streak = portfolio_status.get('win_streak', 0)
        loss_streak = portfolio_status.get('loss_streak', 0)
        
        volatility = market_data.get('volatility', 0.02)
        market_trend = market_data.get('trend_strength', 0.0)
        
        # Emotional state logic
        if pnl_percent > 5.0 and win_streak > 3:
            return EmotionalState.EUPHORIC
        elif pnl_percent > 2.0 and win_streak > 1:
            return EmotionalState.CONFIDENT
        elif drawdown > 10.0 or loss_streak > 3:
            return EmotionalState.FEARFUL
        elif drawdown > 5.0 or loss_streak > 2:
            return EmotionalState.ANXIOUS
        elif pnl_percent < -2.0 and volatility > 0.05:
            return EmotionalState.FRUSTRATED
        elif pnl_percent > 3.0 and volatility < 0.02:
            return EmotionalState.GREEDY
        elif abs(pnl_percent) < 0.5 and drawdown < 2.0:
            return EmotionalState.DISCIPLINED
        else:
            return EmotionalState.NEUTRAL
    
    def detect_emotional_triggers(self, emotion_history: List[Tuple[datetime, EmotionalState]], 
                                market_events: List[Dict[str, Any]]) -> Dict[str, float]:
        """Detect what market events trigger emotional responses"""
        triggers = {}
        
        for i, (timestamp, emotion) in enumerate(emotion_history):
            # Find market events around this time
            relevant_events = [
                event for event in market_events 
                if abs((event['timestamp'] - timestamp).total_seconds()) < 3600  # 1 hour window
            ]
            
            for event in relevant_events:
                event_type = event.get('type', 'unknown')
                if event_type not in triggers:
                    triggers[event_type] = 0.0
                
                # Weight by emotional intensity
                intensity = self._get_emotional_intensity(emotion)
                triggers[event_type] += intensity
        
        # Normalize triggers
        max_trigger = max(triggers.values()) if triggers else 1.0
        triggers = {k: v / max_trigger for k, v in triggers.items()}
        
        return triggers
    
    def _get_emotional_intensity(self, emotion: EmotionalState) -> float:
        """Get emotional intensity score"""
        intensity_map = {
            EmotionalState.EUPHORIC: 0.9,
            EmotionalState.FEARFUL: 0.8,
            EmotionalState.GREEDY: 0.7,
            EmotionalState.FRUSTRATED: 0.7,
            EmotionalState.CONFIDENT: 0.6,
            EmotionalState.ANXIOUS: 0.6,
            EmotionalState.DISCIPLINED: 0.3,
            EmotionalState.NEUTRAL: 0.1
        }
        return intensity_map.get(emotion, 0.5)
    
    def suggest_regulation_strategy(self, current_emotion: EmotionalState) -> List[str]:
        """Suggest emotional regulation strategies"""
        strategies = {
            EmotionalState.EUPHORIC: [
                "Reduce position sizes to maintain discipline",
                "Review risk management rules",
                "Take partial profits to lock in gains",
                "Avoid overtrading due to overconfidence"
            ],
            EmotionalState.FEARFUL: [
                "Reduce position sizes until confidence returns",
                "Review successful past trades for confidence",
                "Focus on high-probability setups only",
                "Consider taking a break from trading"
            ],
            EmotionalState.GREEDY: [
                "Stick to predetermined profit targets",
                "Avoid adding to winning positions impulsively",
                "Review risk-reward ratios",
                "Practice gratitude for current profits"
            ],
            EmotionalState.FRUSTRATED: [
                "Step away from screens for 30 minutes",
                "Review trading plan and rules",
                "Analyze recent losses objectively",
                "Focus on process over outcomes"
            ],
            EmotionalState.ANXIOUS: [
                "Reduce position sizes",
                "Use tighter stop losses",
                "Focus on breathing and relaxation",
                "Review market analysis for clarity"
            ]
        }
        
        return strategies.get(current_emotion, ["Maintain current approach"])

class BiasDetector:
    """Cognitive Bias Detection and Mitigation System"""
    
    def __init__(self):
        self.bias_patterns = {}
        self.mitigation_strategies = {}
        
    def detect_confirmation_bias(self, trade_history: List[TradeEntry], 
                               analysis_history: List[Dict[str, Any]]) -> float:
        """Detect confirmation bias in trade selection"""
        if len(trade_history) < 10:
            return 0.0
        
        # Analyze if trader consistently ignores contrary signals
        bias_score = 0.0
        
        for trade in trade_history[-20:]:  # Last 20 trades
            # Check if trader took trades that confirmed existing bias
            market_conditions = trade.market_conditions
            trend_direction = market_conditions.get('trend_direction', 0)
            
            if trade.direction == 'long' and trend_direction > 0:
                bias_score += 0.1
            elif trade.direction == 'short' and trend_direction < 0:
                bias_score += 0.1
        
        return min(1.0, bias_score)
    
    def detect_overconfidence(self, trade_history: List[TradeEntry]) -> float:
        """Detect overconfidence bias"""
        if len(trade_history) < 10:
            return 0.0
        
        recent_trades = trade_history[-10:]
        
        # Check for increasing position sizes after wins
        overconfidence_score = 0.0
        
        for i in range(1, len(recent_trades)):
            prev_trade = recent_trades[i-1]
            curr_trade = recent_trades[i]
            
            if prev_trade.pnl and prev_trade.pnl > 0:  # Previous trade was profitable
                if curr_trade.size > prev_trade.size * 1.2:  # Increased size by 20%
                    overconfidence_score += 0.2
        
        return min(1.0, overconfidence_score)
    
    def detect_loss_aversion(self, trade_history: List[TradeEntry]) -> float:
        """Detect loss aversion bias"""
        if len(trade_history) < 10:
            return 0.0
        
        losing_trades = [t for t in trade_history if t.pnl and t.pnl < 0]
        winning_trades = [t for t in trade_history if t.pnl and t.pnl > 0]
        
        if not losing_trades or not winning_trades:
            return 0.0
        
        # Calculate average hold times
        avg_losing_hold = np.mean([t.hold_time.total_seconds() for t in losing_trades if t.hold_time])
        avg_winning_hold = np.mean([t.hold_time.total_seconds() for t in winning_trades if t.hold_time])
        
        # Loss aversion: holding losers too long, cutting winners too short
        if avg_losing_hold > avg_winning_hold * 1.5:
            return min(1.0, (avg_losing_hold / avg_winning_hold - 1.0) * 0.5)
        
        return 0.0
    
    def comprehensive_bias_analysis(self, trade_history: List[TradeEntry], 
                                  analysis_history: List[Dict[str, Any]]) -> Dict[CognitiveBias, float]:
        """Comprehensive cognitive bias analysis"""
        bias_scores = {}
        
        bias_scores[CognitiveBias.CONFIRMATION_BIAS] = self.detect_confirmation_bias(trade_history, analysis_history)
        bias_scores[CognitiveBias.OVERCONFIDENCE] = self.detect_overconfidence(trade_history)
        bias_scores[CognitiveBias.LOSS_AVERSION] = self.detect_loss_aversion(trade_history)
        
        # Additional bias detection (simplified)
        bias_scores[CognitiveBias.RECENCY_BIAS] = self._detect_recency_bias(trade_history)
        bias_scores[CognitiveBias.ANCHORING_BIAS] = self._detect_anchoring_bias(trade_history)
        
        return bias_scores
    
    def _detect_recency_bias(self, trade_history: List[TradeEntry]) -> float:
        """Detect recency bias - overweighting recent events"""
        if len(trade_history) < 15:
            return 0.0
        
        recent_trades = trade_history[-5:]
        older_trades = trade_history[-15:-5]
        
        recent_avg_size = np.mean([t.size for t in recent_trades])
        older_avg_size = np.mean([t.size for t in older_trades])
        
        # If recent performance affects position sizing dramatically
        recent_performance = np.mean([t.pnl_percent or 0 for t in recent_trades])
        
        if recent_performance > 2.0 and recent_avg_size > older_avg_size * 1.3:
            return 0.7
        elif recent_performance < -2.0 and recent_avg_size < older_avg_size * 0.7:
            return 0.7
        
        return 0.0
    
    def _detect_anchoring_bias(self, trade_history: List[TradeEntry]) -> float:
        """Detect anchoring bias - fixation on reference points"""
        # Simplified: check if stop losses are consistently at round numbers
        if len(trade_history) < 10:
            return 0.0
        
        round_number_stops = 0
        for trade in trade_history[-20:]:
            if hasattr(trade, 'stop_loss_price'):
                stop_price = getattr(trade, 'stop_loss_price', 0)
                if stop_price > 0:
                    # Check if stop is at round number (ending in 00, 50, etc.)
                    price_str = f"{stop_price:.4f}"
                    if price_str.endswith('0000') or price_str.endswith('5000'):
                        round_number_stops += 1
        
        return min(1.0, round_number_stops / min(20, len(trade_history)))

class LearningEngine:
    """Adaptive Learning and Strategy Evolution Engine"""
    
    def __init__(self):
        self.strategy_performance = {}
        self.market_regime_classifier = None
        self.adaptation_history = []
        self.learning_rate = 0.1
        
    def analyze_strategy_performance(self, trade_history: List[TradeEntry]) -> Dict[str, Dict[str, float]]:
        """Analyze performance by strategy and market conditions"""
        strategy_stats = {}
        
        for trade in trade_history:
            strategy = trade.strategy_used
            if strategy not in strategy_stats:
                strategy_stats[strategy] = {
                    'trades': [],
                    'win_rate': 0.0,
                    'avg_return': 0.0,
                    'sharpe_ratio': 0.0,
                    'max_drawdown': 0.0
                }
            
            strategy_stats[strategy]['trades'].append(trade)
        
        # Calculate metrics for each strategy
        for strategy, stats in strategy_stats.items():
            trades = stats['trades']
            if not trades:
                continue
            
            returns = [t.pnl_percent or 0 for t in trades if t.pnl_percent is not None]
            
            if returns:
                wins = [r for r in returns if r > 0]
                stats['win_rate'] = len(wins) / len(returns)
                stats['avg_return'] = np.mean(returns)
                
                if len(returns) > 1:
                    stats['sharpe_ratio'] = np.mean(returns) / np.std(returns) if np.std(returns) > 0 else 0
                
                # Calculate drawdown
                cumulative_returns = np.cumsum(returns)
                running_max = np.maximum.accumulate(cumulative_returns)
                drawdowns = running_max - cumulative_returns
                stats['max_drawdown'] = np.max(drawdowns) if len(drawdowns) > 0 else 0
        
        return strategy_stats
    
    def identify_market_regimes(self, market_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Identify different market regimes for adaptive learning"""
        if len(market_data) < 50:
            return {'regime': 'insufficient_data', 'confidence': 0.0}
        
        # Extract features for regime classification
        features = []
        for data in market_data:
            feature_vector = [
                data.get('volatility', 0.02),
                data.get('trend_strength', 0.0),
                data.get('volume_ratio', 1.0),
                data.get('momentum', 0.0),
                data.get('correlation', 0.5)
            ]
            features.append(feature_vector)
        
        features_array = np.array(features)
        
        # Use KMeans clustering to identify regimes
        if self.market_regime_classifier is None:
            self.market_regime_classifier = KMeans(n_clusters=4, random_state=42)
            self.market_regime_classifier.fit(features_array)
        
        # Classify current regime
        current_features = features_array[-1:] if len(features_array) > 0 else np.array([[0.02, 0, 1, 0, 0.5]])
        regime_id = self.market_regime_classifier.predict(current_features)[0]
        
        # Map regime ID to descriptive names
        regime_names = {0: 'low_volatility_trending', 1: 'high_volatility_ranging', 
                       2: 'moderate_volatility_trending', 3: 'crisis_mode'}
        
        regime_name = regime_names.get(regime_id, 'unknown')
        
        # Calculate confidence based on distance to cluster center
        distances = self.market_regime_classifier.transform(current_features)
        confidence = 1.0 / (1.0 + np.min(distances))  # Closer to center = higher confidence
        
        return {'regime': regime_name, 'confidence': confidence, 'regime_id': regime_id}
    
    def adapt_strategy_weights(self, strategy_performance: Dict[str, Dict[str, float]], 
                             current_regime: Dict[str, Any]) -> Dict[str, float]:
        """Adapt strategy weights based on performance and market regime"""
        if not strategy_performance:
            return {}
        
        adapted_weights = {}
        total_score = 0.0
        
        for strategy, performance in strategy_performance.items():
            # Calculate composite score
            win_rate = performance.get('win_rate', 0.5)
            avg_return = performance.get('avg_return', 0.0)
            sharpe_ratio = performance.get('sharpe_ratio', 0.0)
            max_drawdown = performance.get('max_drawdown', 0.0)
            
            # Composite scoring
            score = (win_rate * 0.3 + 
                    max(0, avg_return) * 0.3 + 
                    max(0, sharpe_ratio) * 0.2 + 
                    max(0, 1.0 - max_drawdown/10.0) * 0.2)
            
            adapted_weights[strategy] = max(0.1, score)  # Minimum 10% weight
            total_score += adapted_weights[strategy]
        
        # Normalize weights
        if total_score > 0:
            adapted_weights = {k: v/total_score for k, v in adapted_weights.items()}
        
        return adapted_weights
    
    def generate_learning_insights(self, trade_history: List[TradeEntry]) -> List[str]:
        """Generate actionable learning insights from trading history"""
        insights = []
        
        if len(trade_history) < 10:
            return ["Insufficient trade history for meaningful insights"]
        
        # Analyze win/loss patterns
        wins = [t for t in trade_history if t.pnl and t.pnl > 0]
        losses = [t for t in trade_history if t.pnl and t.pnl < 0]
        
        if wins and losses:
            avg_win = np.mean([t.pnl_percent or 0 for t in wins])
            avg_loss = abs(np.mean([t.pnl_percent or 0 for t in losses]))
            
            if avg_win < avg_loss:
                insights.append("Average wins are smaller than average losses - consider letting winners run longer")
            
            win_rate = len(wins) / len(trade_history)
            if win_rate < 0.4:
                insights.append("Win rate below 40% - focus on trade selection quality")
            elif win_rate > 0.7:
                insights.append("High win rate detected - ensure risk-reward ratios are adequate")
        
        # Analyze emotional patterns
        emotional_trades = [t for t in trade_history if hasattr(t, 'emotional_state_entry')]
        if emotional_trades:
            emotional_performance = {}
            for trade in emotional_trades:
                emotion = trade.emotional_state_entry
                if emotion not in emotional_performance:
                    emotional_performance[emotion] = []
                if trade.pnl_percent:
                    emotional_performance[emotion].append(trade.pnl_percent)
            
            for emotion, returns in emotional_performance.items():
                if len(returns) >= 3:
                    avg_return = np.mean(returns)
                    if avg_return < -1.0:
                        insights.append(f"Poor performance when {emotion.value} - consider emotional regulation")
        
        # Analyze time-based patterns
        if len(trade_history) >= 20:
            hourly_performance = {}
            for trade in trade_history:
                hour = trade.entry_time.hour
                if hour not in hourly_performance:
                    hourly_performance[hour] = []
                if trade.pnl_percent:
                    hourly_performance[hour].append(trade.pnl_percent)
            
            best_hours = []
            worst_hours = []
            for hour, returns in hourly_performance.items():
                if len(returns) >= 3:
                    avg_return = np.mean(returns)
                    if avg_return > 1.0:
                        best_hours.append(hour)
                    elif avg_return < -1.0:
                        worst_hours.append(hour)
            
            if best_hours:
                insights.append(f"Best performance during hours: {best_hours} - consider focusing trading during these times")
            if worst_hours:
                insights.append(f"Poor performance during hours: {worst_hours} - consider avoiding trading during these times")
        
        return insights

class TraderConsciousness:
    """Main Trader Consciousness System"""
    
    def __init__(self):
        self.emotional_tracker = EmotionalTracker()
        self.bias_detector = BiasDetector()
        self.learning_engine = LearningEngine()
        
        self.trade_journal: List[TradeEntry] = []
        self.psychology_metrics = None
        self.consciousness_level = 0.5  # 0-1 scale
        self.adaptation_rate = 0.1
        
    def record_trade(self, trade_entry: TradeEntry):
        """Record a trade in the consciousness journal"""
        self.trade_journal.append(trade_entry)
        
        # Update consciousness level based on learning
        if len(self.trade_journal) > 10:
            recent_performance = np.mean([
                t.pnl_percent or 0 for t in self.trade_journal[-10:] 
                if t.pnl_percent is not None
            ])
            
            # Increase consciousness with consistent performance
            if abs(recent_performance) < 2.0:  # Stable performance
                self.consciousness_level = min(1.0, self.consciousness_level + 0.01)
            else:
                self.consciousness_level = max(0.1, self.consciousness_level - 0.005)
        
        logger.info(f"Recorded trade: {trade_entry.symbol} P&L: {trade_entry.pnl_percent}%")
    
    def assess_current_psychology(self, market_data: Dict[str, Any], 
                                portfolio_status: Dict[str, Any]) -> PsychologyMetrics:
        """Assess current psychological state"""
        
        # Analyze emotional state
        current_emotion = self.emotional_tracker.analyze_emotional_state(market_data, portfolio_status)
        
        # Detect cognitive biases
        bias_scores = self.bias_detector.comprehensive_bias_analysis(self.trade_journal, [])
        
        # Calculate psychology metrics
        emotional_stability = 1.0 - self.emotional_tracker._get_emotional_intensity(current_emotion)
        
        # Discipline score based on rule following
        discipline_score = self._calculate_discipline_score()
        
        # Learning rate based on adaptation
        learning_rate = min(1.0, len(self.trade_journal) * 0.01)
        
        self.psychology_metrics = PsychologyMetrics(
            overall_emotional_stability=emotional_stability,
            discipline_score=discipline_score,
            patience_level=self._calculate_patience_level(),
            risk_tolerance=self._calculate_risk_tolerance(),
            confidence_calibration=self._calculate_confidence_calibration(),
            bias_susceptibility=bias_scores,
            stress_resilience=self._calculate_stress_resilience(),
            learning_rate=learning_rate,
            adaptation_speed=self.adaptation_rate
        )
        
        return self.psychology_metrics
    
    def generate_consciousness_report(self) -> Dict[str, Any]:
        """Generate comprehensive consciousness and learning report"""
        if not self.trade_journal:
            return {'status': 'No trading history available'}
        
        # Strategy performance analysis
        strategy_performance = self.learning_engine.analyze_strategy_performance(self.trade_journal)
        
        # Learning insights
        learning_insights = self.learning_engine.generate_learning_insights(self.trade_journal)
        
        # Emotional regulation suggestions
        current_emotion = EmotionalState.NEUTRAL
        if self.trade_journal:
            # Get most recent emotional state
            recent_trades = [t for t in self.trade_journal[-5:] if hasattr(t, 'emotional_state_entry')]
            if recent_trades:
                current_emotion = recent_trades[-1].emotional_state_entry
        
        regulation_suggestions = self.emotional_tracker.suggest_regulation_strategy(current_emotion)
        
        # Bias analysis
        bias_scores = self.bias_detector.comprehensive_bias_analysis(self.trade_journal, [])
        
        # Performance summary
        recent_trades = self.trade_journal[-20:] if len(self.trade_journal) >= 20 else self.trade_journal
        total_pnl = sum([t.pnl_percent or 0 for t in recent_trades if t.pnl_percent is not None])
        win_rate = len([t for t in recent_trades if t.pnl and t.pnl > 0]) / len(recent_trades) if recent_trades else 0
        
        return {
            'consciousness_level': self.consciousness_level,
            'total_trades': len(self.trade_journal),
            'recent_performance': {
                'total_pnl_percent': total_pnl,
                'win_rate': win_rate,
                'trade_count': len(recent_trades)
            },
            'psychology_state': {
                'current_emotion': current_emotion.value,
                'emotional_stability': self.psychology_metrics.overall_emotional_stability if self.psychology_metrics else 0.5,
                'discipline_score': self.psychology_metrics.discipline_score if self.psychology_metrics else 0.5
            },
            'cognitive_biases': {bias.value: score for bias, score in bias_scores.items()},
            'strategy_performance': strategy_performance,
            'learning_insights': learning_insights,
            'regulation_suggestions': regulation_suggestions,
            'adaptation_recommendations': self._generate_adaptation_recommendations()
        }
    
    def _calculate_discipline_score(self) -> float:
        """Calculate discipline score based on rule following"""
        if len(self.trade_journal) < 5:
            return 0.5
        
        # Analyze execution quality
        execution_scores = [t.execution_quality for t in self.trade_journal if hasattr(t, 'execution_quality')]
        
        if execution_scores:
            return np.mean(execution_scores)
        
        return 0.5
    
    def _calculate_patience_level(self) -> float:
        """Calculate patience level based on hold times"""
        if len(self.trade_journal) < 5:
            return 0.5
        
        hold_times = [t.hold_time.total_seconds() for t in self.trade_journal if t.hold_time]
        
        if not hold_times:
            return 0.5
        
        # Longer average hold times indicate more patience
        avg_hold_hours = np.mean(hold_times) / 3600
        patience_score = min(1.0, avg_hold_hours / 24.0)  # Normalize to 24 hours
        
        return patience_score
    
    def _calculate_risk_tolerance(self) -> float:
        """Calculate risk tolerance based on position sizing"""
        if len(self.trade_journal) < 5:
            return 0.5
        
        # Analyze position sizes relative to account
        sizes = [abs(t.size) for t in self.trade_journal]
        
        if sizes:
            avg_size = np.mean(sizes)
            # Normalize to typical range
            risk_tolerance = min(1.0, avg_size / 100000)  # Assuming 100k as reference
            return risk_tolerance
        
        return 0.5
    
    def _calculate_confidence_calibration(self) -> float:
        """Calculate how well confidence aligns with actual performance"""
        if len(self.trade_journal) < 10:
            return 0.5
        
        # Compare confidence levels with actual outcomes
        calibration_errors = []
        
        for trade in self.trade_journal:
            if hasattr(trade, 'confidence_level') and trade.pnl_percent is not None:
                confidence = trade.confidence_level
                success = 1.0 if trade.pnl_percent > 0 else 0.0
                error = abs(confidence - success)
                calibration_errors.append(error)
        
        if calibration_errors:
            avg_error = np.mean(calibration_errors)
            calibration_score = max(0.0, 1.0 - avg_error)
            return calibration_score
        
        return 0.5
    
    def _calculate_stress_resilience(self) -> float:
        """Calculate stress resilience based on performance under pressure"""
        if len(self.trade_journal) < 10:
            return 0.5
        
        # Identify high-stress periods (high volatility, drawdowns)
        stress_trades = []
        normal_trades = []
        
        for trade in self.trade_journal:
            volatility = trade.market_conditions.get('volatility', 0.02)
            if volatility > 0.04:  # High volatility threshold
                stress_trades.append(trade.pnl_percent or 0)
            else:
                normal_trades.append(trade.pnl_percent or 0)
        
        if stress_trades and normal_trades:
            stress_performance = np.mean(stress_trades)
            normal_performance = np.mean(normal_trades)
            
            # Resilience = how well performance holds up under stress
            if normal_performance > 0:
                resilience = max(0.0, 1.0 + stress_performance / normal_performance)
            else:
                resilience = 0.5
            
            return min(1.0, resilience)
        
        return 0.5
    
    def _generate_adaptation_recommendations(self) -> List[str]:
        """Generate recommendations for strategy adaptation"""
        recommendations = []
        
        if self.consciousness_level < 0.3:
            recommendations.append("Focus on building consistent trading habits")
            recommendations.append("Reduce position sizes until confidence improves")
        
        if self.psychology_metrics:
            if self.psychology_metrics.discipline_score < 0.5:
                recommendations.append("Implement stricter rule-following protocols")
            
            if self.psychology_metrics.overall_emotional_stability < 0.5:
                recommendations.append("Practice emotional regulation techniques")
            
            # Check for high bias susceptibility
            high_biases = [bias.value for bias, score in self.psychology_metrics.bias_susceptibility.items() if score > 0.6]
            if high_biases:
                recommendations.append(f"Address cognitive biases: {', '.join(high_biases)}")
        
        return recommendations

# Example usage and testing
if __name__ == "__main__":
    # Initialize Trader Consciousness
    consciousness = TraderConsciousness()
    
    logger.info("Trader Consciousness Module Testing")
    print("=" * 50)
    
    # Create sample trade entries
    sample_trades = [
        TradeEntry(
            trade_id="T001",
            symbol="EURUSD",
            entry_time=datetime.now() - timedelta(hours=2),
            exit_time=datetime.now() - timedelta(hours=1),
            entry_price=1.1000,
            exit_price=1.1020,
            size=100000,
            direction="long",
            pnl=200.0,
            pnl_percent=1.8,
            emotional_state_entry=EmotionalState.CONFIDENT,
            emotional_state_exit=EmotionalState.DISCIPLINED,
            confidence_level=0.8,
            stress_level=0.3,
            strategy_used="trend_following",
            market_conditions={"volatility": 0.025, "trend_strength": 0.7},
            setup_quality=0.8,
            execution_quality=0.9,
            lessons_learned=["Entry timing was good", "Exit could have been better"],
            mistakes_made=[],
            cognitive_biases=[],
            risk_reward_ratio=2.0,
            hold_time=timedelta(hours=1)
        ),
        TradeEntry(
            trade_id="T002",
            symbol="GBPUSD",
            entry_time=datetime.now() - timedelta(hours=1),
            exit_time=datetime.now(),
            entry_price=1.2500,
            exit_price=1.2480,
            size=75000,
            direction="long",
            pnl=-150.0,
            pnl_percent=-1.6,
            emotional_state_entry=EmotionalState.ANXIOUS,
            emotional_state_exit=EmotionalState.FRUSTRATED,
            confidence_level=0.6,
            stress_level=0.7,
            strategy_used="mean_reversion",
            market_conditions={"volatility": 0.045, "trend_strength": -0.3},
            setup_quality=0.6,
            execution_quality=0.7,
            lessons_learned=["Market conditions were not ideal"],
            mistakes_made=["Ignored high volatility warning"],
            cognitive_biases=[CognitiveBias.OVERCONFIDENCE],
            risk_reward_ratio=1.5,
            hold_time=timedelta(hours=1)
        )
    ]
    
    # Record trades
    for trade in sample_trades:
        consciousness.record_trade(trade)
    
    # Assess psychology
    market_data = {
        'volatility': 0.03,
        'trend_strength': 0.5,
        'volume_ratio': 1.2
    }
    
    portfolio_status = {
        'pnl_today': 50.0,
        'pnl_percent': 0.5,
        'current_drawdown': 2.0,
        'win_streak': 1,
        'loss_streak': 0
    }
    
    psychology = consciousness.assess_current_psychology(market_data, portfolio_status)
    logger.info(f"Emotional Stability: {psychology.overall_emotional_stability:.3f}")
    logger.info(f"Discipline Score: {psychology.discipline_score:.3f}")
    logger.info(f"Learning Rate: {psychology.learning_rate:.3f}")
    
    # Generate consciousness report
    logger.info("\nConsciousness Report:")
    report = consciousness.generate_consciousness_report()
    
    for key, value in report.items():
        if key not in ['strategy_performance', 'cognitive_biases']:
            logger.info(f"{key}: {value}")
    
    logger.info(f"\nCognitive Biases:")
    for bias, score in report['cognitive_biases'].items():
        logger.info(f"  {bias}: {score:.3f}")
    
    logger.info(f"\nLearning Insights:")
    for insight in report['learning_insights']:
        logger.info(f"  - {insight}")
    
    logger.info(f"\nRegulation Suggestions:")
    for suggestion in report['regulation_suggestions']:
        logger.info(f"  - {suggestion}")
    
    logger.info("\nTrader Consciousness test completed successfully!")
