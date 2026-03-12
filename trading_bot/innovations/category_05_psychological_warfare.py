"""
CATEGORY 5: PSYCHOLOGICAL WARFARE & MIND GAMES (Ideas 161-200)
Trading strategies based on psychological manipulation, game theory, and mental models.
"""

import numpy as np
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple, Any
from enum import Enum, auto
from datetime import datetime
from collections import deque
import hashlib


import logging

logger = logging.getLogger(__name__)

class PsychologicalState(Enum):
    CONFIDENT = auto()
    FEARFUL = auto()
    GREEDY = auto()
    PANICKED = auto()
    EUPHORIC = auto()
    DEPRESSED = auto()
    RATIONAL = auto()
    IRRATIONAL = auto()


@dataclass
class MindState:
    confidence: float
    fear: float
    greed: float
    patience: float
    discipline: float
    cognitive_load: float


class CrowdPsychologyManipulator:
    """IDEA 161: Exploits crowd psychology patterns."""
    
    def __init__(self):
        try:
            self.crowd_sentiment: deque = deque(maxlen=1000)
            self.manipulation_history: List[Dict] = []
        except Exception as e:
            import logging as _log
            _log.getLogger(__name__).error(f"Error in __init__: {e}")
            raise
        
    def analyze_crowd(self, sentiment_data: List[float], volume_data: np.ndarray) -> Dict:
        try:
            if not sentiment_data:
                return {'crowd_state': 'UNKNOWN'}
            
            avg_sentiment = np.mean(sentiment_data)
            sentiment_std = np.std(sentiment_data)
            volume_surge = volume_data[-1] / np.mean(volume_data) if len(volume_data) > 1 else 1
        
            if avg_sentiment > 0.7 and sentiment_std < 0.1:
                crowd_state = 'EUPHORIC_CONSENSUS'
                contrarian_signal = 'SELL'
            elif avg_sentiment < -0.7 and sentiment_std < 0.1:
                crowd_state = 'PANIC_CONSENSUS'
                contrarian_signal = 'BUY'
            elif sentiment_std > 0.5:
                crowd_state = 'CONFUSED'
                contrarian_signal = 'WAIT'
            else:
                crowd_state = 'NEUTRAL'
                contrarian_signal = 'NEUTRAL'
            
            return {
                'crowd_state': crowd_state,
                'contrarian_signal': contrarian_signal,
                'herd_strength': 1 - sentiment_std,
                'volume_confirmation': volume_surge > 1.5
            }
        except Exception as e:
            import logging as _log
            _log.getLogger(__name__).error(f"Error in analyze_crowd: {e}")
            raise
    
    def predict_crowd_behavior(self, current_state: str) -> Dict:
        try:
            transitions = {
                'EUPHORIC_CONSENSUS': ('PANIC_CONSENSUS', 0.3),
                'PANIC_CONSENSUS': ('EUPHORIC_CONSENSUS', 0.2),
                'CONFUSED': ('NEUTRAL', 0.5),
                'NEUTRAL': ('CONFUSED', 0.3)
            }
        
            next_state, probability = transitions.get(current_state, ('NEUTRAL', 0.5))
            return {'predicted_state': next_state, 'probability': probability}
        except Exception as e:
            import logging as _log
            _log.getLogger(__name__).error(f"Error in predict_crowd_behavior: {e}")
            raise


class FearGreedExploiter:
    """IDEA 162: Exploits fear and greed cycles."""
    
    def __init__(self):
        try:
            self.fear_index = 50
            self.greed_index = 50
        except Exception as e:
            import logging as _log
            _log.getLogger(__name__).error(f"Error in __init__: {e}")
            raise
        
    def calculate_indices(self, volatility: float, momentum: float, 
                         volume_ratio: float, put_call_ratio: float) -> Dict:
        try:
            self.fear_index = min(100, max(0, 
                volatility * 200 + 
                (1 - momentum) * 30 + 
                put_call_ratio * 20
            ))
        
            self.greed_index = min(100, max(0,
                (1 - volatility) * 100 +
                momentum * 50 +
                volume_ratio * 20
            ))
        
            composite = (100 - self.fear_index + self.greed_index) / 2
        
            if composite > 80:
                signal = 'EXTREME_GREED_SELL'
            elif composite > 60:
                signal = 'GREED_CAUTION'
            elif composite < 20:
                signal = 'EXTREME_FEAR_BUY'
            elif composite < 40:
                signal = 'FEAR_OPPORTUNITY'
            else:
                signal = 'NEUTRAL'
            
            return {
                'fear_index': self.fear_index,
                'greed_index': self.greed_index,
                'composite': composite,
                'signal': signal
            }
        except Exception as e:
            import logging as _log
            _log.getLogger(__name__).error(f"Error in calculate_indices: {e}")
            raise


class CognitiveDissonanceTrader:
    """IDEA 163: Trades on cognitive dissonance in market."""
    
    def detect_dissonance(self, price_action: Dict, sentiment: Dict, 
                         fundamentals: Dict) -> Dict:
        try:
            dissonance_score = 0
            conflicts = []
        
            if price_action.get('trend') == 'UP' and sentiment.get('overall') < -0.3:
                dissonance_score += 0.3
                conflicts.append('PRICE_VS_SENTIMENT')
            
            if price_action.get('trend') == 'UP' and fundamentals.get('value') == 'OVERVALUED':
                dissonance_score += 0.3
                conflicts.append('PRICE_VS_FUNDAMENTALS')
            
            if sentiment.get('overall') > 0.5 and fundamentals.get('value') == 'OVERVALUED':
                dissonance_score += 0.2
                conflicts.append('SENTIMENT_VS_FUNDAMENTALS')
            
            resolution_prediction = 'PRICE_CORRECTION' if dissonance_score > 0.5 else 'CONTINUATION'
        
            return {
                'dissonance_score': dissonance_score,
                'conflicts': conflicts,
                'resolution_prediction': resolution_prediction,
                'trade_signal': 'FADE' if dissonance_score > 0.5 else 'FOLLOW'
            }
        except Exception as e:
            import logging as _log
            _log.getLogger(__name__).error(f"Error in detect_dissonance: {e}")
            raise


class AnchoringBiasExploiter:
    """IDEA 164: Exploits anchoring bias in traders."""
    
    def __init__(self):
        try:
            self.anchors: Dict[str, float] = {}
        except Exception as e:
            import logging as _log
            _log.getLogger(__name__).error(f"Error in __init__: {e}")
            raise
        
    def identify_anchors(self, prices: np.ndarray) -> List[Dict]:
        try:
            anchors = []
        
            all_time_high = np.max(prices)
            all_time_low = np.min(prices)
            recent_high = np.max(prices[-20:]) if len(prices) > 20 else all_time_high
            recent_low = np.min(prices[-20:]) if len(prices) > 20 else all_time_low
            round_numbers = [round(prices[-1], -2), round(prices[-1], -1)]
        
            anchors.append({'type': 'ATH', 'level': all_time_high, 'strength': 0.9})
            anchors.append({'type': 'ATL', 'level': all_time_low, 'strength': 0.9})
            anchors.append({'type': 'RECENT_HIGH', 'level': recent_high, 'strength': 0.7})
            anchors.append({'type': 'RECENT_LOW', 'level': recent_low, 'strength': 0.7})
        
            for rn in round_numbers:
                anchors.append({'type': 'ROUND_NUMBER', 'level': rn, 'strength': 0.5})
            
            return anchors
        except Exception as e:
            import logging as _log
            _log.getLogger(__name__).error(f"Error in identify_anchors: {e}")
            raise
    
    def predict_anchor_effect(self, current_price: float, anchors: List[Dict]) -> Dict:
        try:
            nearest_anchor = min(anchors, key=lambda a: abs(a['level'] - current_price))
            distance = (current_price - nearest_anchor['level']) / current_price
        
            if abs(distance) < 0.02:
                effect = 'STRONG_RESISTANCE' if distance > 0 else 'STRONG_SUPPORT'
            elif abs(distance) < 0.05:
                effect = 'MODERATE_INFLUENCE'
            else:
                effect = 'WEAK_INFLUENCE'
            
            return {
                'nearest_anchor': nearest_anchor,
                'distance': distance,
                'effect': effect
            }
        except Exception as e:
            import logging as _log
            _log.getLogger(__name__).error(f"Error in predict_anchor_effect: {e}")
            raise


class LossAversionTrader:
    """IDEA 165: Exploits loss aversion behavior."""
    
    def __init__(self):
        try:
            self.loss_aversion_coefficient = 2.5
        except Exception as e:
            import logging as _log
            _log.getLogger(__name__).error(f"Error in __init__: {e}")
            raise
        
    def calculate_prospect_value(self, gain_or_loss: float) -> float:
        try:
            if gain_or_loss >= 0:
                return gain_or_loss ** 0.88
            else:
                return -self.loss_aversion_coefficient * ((-gain_or_loss) ** 0.88)
        except Exception as e:
            import logging as _log
            _log.getLogger(__name__).error(f"Error in calculate_prospect_value: {e}")
            raise
    
    def predict_behavior(self, unrealized_pnl: float, position_size: float) -> Dict:
        try:
            prospect_value = self.calculate_prospect_value(unrealized_pnl)
        
            if unrealized_pnl > 0:
                behavior = 'LIKELY_TO_TAKE_PROFIT_EARLY'
                exploitation = 'FADE_PROFIT_TAKING'
            else:
                behavior = 'LIKELY_TO_HOLD_LOSERS'
                exploitation = 'EXPECT_DELAYED_SELLING'
            
            return {
                'prospect_value': prospect_value,
                'predicted_behavior': behavior,
                'exploitation_strategy': exploitation,
                'pain_level': abs(prospect_value) if unrealized_pnl < 0 else 0
            }
        except Exception as e:
            import logging as _log
            _log.getLogger(__name__).error(f"Error in predict_behavior: {e}")
            raise


class ConfirmationBiasDetector:
    """IDEA 166: Detects and exploits confirmation bias."""
    
    def analyze_bias(self, trader_positions: List[Dict], 
                    news_sentiment: List[Dict]) -> Dict:
        try:
            long_traders = sum(1 for p in trader_positions if p.get('direction') == 'LONG')
            short_traders = len(trader_positions) - long_traders
        
            bullish_news = sum(1 for n in news_sentiment if n.get('sentiment') > 0)
            bearish_news = len(news_sentiment) - bullish_news
        
            long_ratio = long_traders / len(trader_positions) if trader_positions else 0.5
            bullish_ratio = bullish_news / len(news_sentiment) if news_sentiment else 0.5
        
            bias_alignment = abs(long_ratio - bullish_ratio)
        
            if bias_alignment < 0.1:
                bias_state = 'STRONG_CONFIRMATION_BIAS'
                contrarian_opportunity = True
            else:
                bias_state = 'MIXED_VIEWS'
                contrarian_opportunity = False
            
            return {
                'bias_state': bias_state,
                'long_ratio': long_ratio,
                'bullish_news_ratio': bullish_ratio,
                'contrarian_opportunity': contrarian_opportunity
            }
        except Exception as e:
            import logging as _log
            _log.getLogger(__name__).error(f"Error in analyze_bias: {e}")
            raise


class HerdingBehaviorPredictor:
    """IDEA 167: Predicts herding behavior."""
    
    def __init__(self):
        try:
            self.herd_threshold = 0.7
        except Exception as e:
            import logging as _log
            _log.getLogger(__name__).error(f"Error in __init__: {e}")
            raise
        
    def measure_herding(self, individual_trades: List[Dict]) -> Dict:
        try:
            if not individual_trades:
                return {'herding_coefficient': 0}
            
            directions = [t.get('direction', 'NEUTRAL') for t in individual_trades]
            buy_ratio = sum(1 for d in directions if d == 'BUY') / len(directions)
        
            herding_coefficient = abs(buy_ratio - 0.5) * 2
        
            if herding_coefficient > self.herd_threshold:
                herd_direction = 'BULLISH' if buy_ratio > 0.5 else 'BEARISH'
                stampede_risk = herding_coefficient > 0.9
            else:
                herd_direction = 'NONE'
                stampede_risk = False
            
            return {
                'herding_coefficient': herding_coefficient,
                'herd_direction': herd_direction,
                'stampede_risk': stampede_risk,
                'contrarian_signal': 'SELL' if herd_direction == 'BULLISH' else 'BUY' if herd_direction == 'BEARISH' else 'NEUTRAL'
            }
        except Exception as e:
            import logging as _log
            _log.getLogger(__name__).error(f"Error in measure_herding: {e}")
            raise


class RecencyBiasExploiter:
    """IDEA 168: Exploits recency bias in market participants."""
    
    def analyze_recency_effect(self, prices: np.ndarray, lookback: int = 5) -> Dict:
        try:
            if len(prices) < lookback + 20:
                return {'recency_bias': 0}
            
            recent_trend = np.mean(np.diff(prices[-lookback:])) / prices[-lookback]
            historical_trend = np.mean(np.diff(prices[-50:-lookback])) / prices[-50]
        
            recency_bias = recent_trend - historical_trend
        
            if abs(recency_bias) > 0.01:
                overreaction = True
                mean_reversion_signal = -np.sign(recency_bias)
            else:
                overreaction = False
                mean_reversion_signal = 0
            
            return {
                'recency_bias': recency_bias,
                'recent_trend': recent_trend,
                'historical_trend': historical_trend,
                'overreaction': overreaction,
                'mean_reversion_signal': mean_reversion_signal
            }
        except Exception as e:
            import logging as _log
            _log.getLogger(__name__).error(f"Error in analyze_recency_effect: {e}")
            raise


class OverconfidenceExploiter:
    """IDEA 169: Exploits overconfidence in traders."""
    
    def detect_overconfidence(self, prediction_accuracy: List[float],
                             confidence_levels: List[float]) -> Dict:
        try:
            if not prediction_accuracy or not confidence_levels:
                return {'overconfidence': 0}
            
            avg_accuracy = np.mean(prediction_accuracy)
            avg_confidence = np.mean(confidence_levels)
        
            overconfidence = avg_confidence - avg_accuracy
        
            if overconfidence > 0.2:
                state = 'HIGHLY_OVERCONFIDENT'
                exploitation = 'FADE_CONFIDENT_TRADES'
            elif overconfidence > 0.1:
                state = 'MODERATELY_OVERCONFIDENT'
                exploitation = 'CAUTIOUS_FADE'
            elif overconfidence < -0.1:
                state = 'UNDERCONFIDENT'
                exploitation = 'FOLLOW_HESITANT_TRADES'
            else:
                state = 'CALIBRATED'
                exploitation = 'NO_EDGE'
            
            return {
                'overconfidence': overconfidence,
                'state': state,
                'exploitation': exploitation
            }
        except Exception as e:
            import logging as _log
            _log.getLogger(__name__).error(f"Error in detect_overconfidence: {e}")
            raise


class GameTheoryTrader:
    """IDEA 170: Uses game theory for trading decisions."""
    
    def __init__(self):
        try:
            self.payoff_matrix: Dict[str, Dict[str, float]] = {}
        except Exception as e:
            import logging as _log
            _log.getLogger(__name__).error(f"Error in __init__: {e}")
            raise
        
    def calculate_nash_equilibrium(self, strategies: List[str],
                                   payoffs: np.ndarray) -> Dict:
        try:
            n = len(strategies)
        
            best_responses = {}
            for i, strat in enumerate(strategies):
                best_response_idx = np.argmax(payoffs[i, :])
                best_responses[strat] = strategies[best_response_idx]
            
            equilibria = []
            for i, strat1 in enumerate(strategies):
                for j, strat2 in enumerate(strategies):
                    if best_responses.get(strat1) == strat2:
                        equilibria.append((strat1, strat2))
                    
            return {
                'best_responses': best_responses,
                'nash_equilibria': equilibria,
                'recommended_strategy': equilibria[0][0] if equilibria else strategies[0]
            }
        except Exception as e:
            import logging as _log
            _log.getLogger(__name__).error(f"Error in calculate_nash_equilibrium: {e}")
            raise
    
    def prisoners_dilemma_trading(self, my_action: str, 
                                  opponent_action: str) -> float:
        try:
            payoffs = {
                ('COOPERATE', 'COOPERATE'): 3,
                ('COOPERATE', 'DEFECT'): 0,
                ('DEFECT', 'COOPERATE'): 5,
                ('DEFECT', 'DEFECT'): 1
            }
            return payoffs.get((my_action, opponent_action), 0)
        except Exception as e:
            import logging as _log
            _log.getLogger(__name__).error(f"Error in prisoners_dilemma_trading: {e}")
            raise


class BluffDetector:
    """IDEA 171: Detects market bluffs and fake moves."""
    
    def detect_bluff(self, price_move: float, volume: float,
                    avg_volume: float, order_flow: Dict) -> Dict:
        try:
            volume_ratio = volume / avg_volume if avg_volume > 0 else 1
        
            bluff_indicators = 0
        
            if abs(price_move) > 0.02 and volume_ratio < 0.5:
                bluff_indicators += 1
            
            if order_flow.get('large_orders', 0) < order_flow.get('small_orders', 0) * 0.1:
                bluff_indicators += 1
            
            if order_flow.get('cancelled_orders', 0) > order_flow.get('executed_orders', 0):
                bluff_indicators += 1
            
            is_bluff = bluff_indicators >= 2
        
            return {
                'is_bluff': is_bluff,
                'bluff_score': bluff_indicators / 3,
                'recommendation': 'FADE_MOVE' if is_bluff else 'FOLLOW_MOVE'
            }
        except Exception as e:
            import logging as _log
            _log.getLogger(__name__).error(f"Error in detect_bluff: {e}")
            raise


class EmotionalContagionTracker:
    """IDEA 172: Tracks emotional contagion in markets."""
    
    def __init__(self):
        try:
            self.emotion_history: deque = deque(maxlen=1000)
        except Exception as e:
            import logging as _log
            _log.getLogger(__name__).error(f"Error in __init__: {e}")
            raise
        
    def track_contagion(self, social_sentiment: List[float],
                       price_volatility: float) -> Dict:
        try:
            if not social_sentiment:
                return {'contagion_level': 0}
            
            sentiment_velocity = np.diff(social_sentiment) if len(social_sentiment) > 1 else [0]
            contagion_speed = np.mean(np.abs(sentiment_velocity))
        
            sentiment_uniformity = 1 - np.std(social_sentiment)
        
            contagion_level = contagion_speed * sentiment_uniformity * (1 + price_volatility * 10)
        
            if contagion_level > 0.7:
                state = 'VIRAL_EMOTION'
                risk = 'HIGH'
            elif contagion_level > 0.4:
                state = 'SPREADING'
                risk = 'MEDIUM'
            else:
                state = 'CONTAINED'
                risk = 'LOW'
            
            return {
                'contagion_level': contagion_level,
                'state': state,
                'risk': risk,
                'dominant_emotion': 'FEAR' if np.mean(social_sentiment) < 0 else 'GREED'
            }
        except Exception as e:
            import logging as _log
            _log.getLogger(__name__).error(f"Error in track_contagion: {e}")
            raise


class MentalAccountingExploiter:
    """IDEA 173: Exploits mental accounting biases."""
    
    def analyze_mental_accounts(self, portfolio: Dict) -> Dict:
        try:
            accounts = {
                'house_money': portfolio.get('unrealized_gains', 0),
                'sacred_capital': portfolio.get('initial_capital', 0),
                'play_money': portfolio.get('bonus_capital', 0)
            }
        
            total = sum(accounts.values())
        
            if accounts['house_money'] > accounts['sacred_capital'] * 0.5:
                behavior = 'RISK_SEEKING_WITH_GAINS'
                exploitation = 'EXPECT_AGGRESSIVE_BETS'
            elif accounts['house_money'] < 0:
                behavior = 'RISK_AVERSE_WITH_LOSSES'
                exploitation = 'EXPECT_CONSERVATIVE_BEHAVIOR'
            else:
                behavior = 'NEUTRAL'
                exploitation = 'NO_CLEAR_EDGE'
            
            return {
                'accounts': accounts,
                'predicted_behavior': behavior,
                'exploitation': exploitation
            }
        except Exception as e:
            import logging as _log
            _log.getLogger(__name__).error(f"Error in analyze_mental_accounts: {e}")
            raise


class SunkCostExploiter:
    """IDEA 174: Exploits sunk cost fallacy."""
    
    def detect_sunk_cost_behavior(self, position_history: List[Dict]) -> Dict:
        try:
            if not position_history:
                return {'sunk_cost_risk': 0}
            
            losing_positions = [p for p in position_history if p.get('pnl', 0) < 0]
            avg_hold_time_losers = np.mean([p.get('hold_time', 0) for p in losing_positions]) if losing_positions else 0
        
            winning_positions = [p for p in position_history if p.get('pnl', 0) > 0]
            avg_hold_time_winners = np.mean([p.get('hold_time', 0) for p in winning_positions]) if winning_positions else 0
        
            sunk_cost_ratio = avg_hold_time_losers / avg_hold_time_winners if avg_hold_time_winners > 0 else 1
        
            if sunk_cost_ratio > 2:
                behavior = 'STRONG_SUNK_COST_FALLACY'
                exploitation = 'EXPECT_LATE_CAPITULATION'
            elif sunk_cost_ratio > 1.5:
                behavior = 'MODERATE_SUNK_COST_FALLACY'
                exploitation = 'WATCH_FOR_FORCED_EXITS'
            else:
                behavior = 'RATIONAL'
                exploitation = 'NO_EDGE'
            
            return {
                'sunk_cost_ratio': sunk_cost_ratio,
                'behavior': behavior,
                'exploitation': exploitation
            }
        except Exception as e:
            import logging as _log
            _log.getLogger(__name__).error(f"Error in detect_sunk_cost_behavior: {e}")
            raise


class DispositionEffectTrader:
    """IDEA 175: Trades on disposition effect patterns."""
    
    def analyze_disposition(self, realized_gains: List[float],
                           realized_losses: List[float],
                           unrealized_gains: float,
                           unrealized_losses: float) -> Dict:
        try:
            gain_realization_rate = len(realized_gains) / (len(realized_gains) + 1) if unrealized_gains > 0 else 0
            loss_realization_rate = len(realized_losses) / (len(realized_losses) + 1) if unrealized_losses < 0 else 0
        
            disposition_effect = gain_realization_rate - loss_realization_rate
        
            if disposition_effect > 0.3:
                pattern = 'STRONG_DISPOSITION_EFFECT'
                prediction = 'WINNERS_SOLD_EARLY_LOSERS_HELD'
            elif disposition_effect > 0.1:
                pattern = 'MODERATE_DISPOSITION_EFFECT'
                prediction = 'SOME_EARLY_PROFIT_TAKING'
            else:
                pattern = 'WEAK_OR_NO_EFFECT'
                prediction = 'RATIONAL_BEHAVIOR'
            
            return {
                'disposition_effect': disposition_effect,
                'pattern': pattern,
                'prediction': prediction
            }
        except Exception as e:
            import logging as _log
            _log.getLogger(__name__).error(f"Error in analyze_disposition: {e}")
            raise


class NarrativeFallacyDetector:
    """IDEA 176: Detects narrative fallacy in market stories."""
    
    def analyze_narrative(self, news_stories: List[str],
                         price_action: np.ndarray) -> Dict:
        try:
            story_count = len(news_stories)
            price_volatility = np.std(price_action) / np.mean(price_action) if len(price_action) > 0 else 0
        
            narrative_intensity = story_count / 10
        
            if narrative_intensity > 1 and price_volatility < 0.02:
                fallacy_detected = True
                warning = 'NARRATIVE_EXCEEDS_REALITY'
            elif narrative_intensity < 0.5 and price_volatility > 0.05:
                fallacy_detected = True
                warning = 'REALITY_EXCEEDS_NARRATIVE'
            else:
                fallacy_detected = False
                warning = 'ALIGNED'
            
            return {
                'narrative_intensity': narrative_intensity,
                'price_volatility': price_volatility,
                'fallacy_detected': fallacy_detected,
                'warning': warning
            }
        except Exception as e:
            import logging as _log
            _log.getLogger(__name__).error(f"Error in analyze_narrative: {e}")
            raise


class AvailabilityHeuristicTrader:
    """IDEA 177: Exploits availability heuristic."""
    
    def analyze_availability(self, recent_events: List[Dict],
                            historical_frequency: Dict) -> Dict:
        try:
            event_types = [e.get('type') for e in recent_events]
        
            overweighted = []
            underweighted = []
        
            for event_type, hist_freq in historical_frequency.items():
                recent_freq = event_types.count(event_type) / len(event_types) if event_types else 0
            
                if recent_freq > hist_freq * 1.5:
                    overweighted.append(event_type)
                elif recent_freq < hist_freq * 0.5:
                    underweighted.append(event_type)
                
            return {
                'overweighted_events': overweighted,
                'underweighted_events': underweighted,
                'trading_implication': 'FADE_OVERWEIGHTED' if overweighted else 'NEUTRAL'
            }
        except Exception as e:
            import logging as _log
            _log.getLogger(__name__).error(f"Error in analyze_availability: {e}")
            raise


class RepresentativenessTrader:
    """IDEA 178: Exploits representativeness heuristic."""
    
    def detect_pattern_matching_error(self, current_pattern: np.ndarray,
                                      historical_patterns: List[np.ndarray]) -> Dict:
        try:
            if not historical_patterns:
                return {'error_probability': 0}
            
            similarities = []
            for hist_pattern in historical_patterns:
                if len(hist_pattern) == len(current_pattern):
                    corr = np.corrcoef(current_pattern, hist_pattern)[0, 1]
                    if not np.isnan(corr):
                        similarities.append(corr)
                    
            if not similarities:
                return {'error_probability': 0}
            
            max_similarity = max(similarities)
        
            if max_similarity > 0.9:
                error_probability = 0.3
                warning = 'HIGH_SIMILARITY_MAY_BE_COINCIDENCE'
            elif max_similarity > 0.7:
                error_probability = 0.2
                warning = 'MODERATE_SIMILARITY'
            else:
                error_probability = 0.1
                warning = 'LOW_SIMILARITY'
            
            return {
                'max_similarity': max_similarity,
                'error_probability': error_probability,
                'warning': warning
            }
        except Exception as e:
            import logging as _log
            _log.getLogger(__name__).error(f"Error in detect_pattern_matching_error: {e}")
            raise


class StatusQuoBiasExploiter:
    """IDEA 179: Exploits status quo bias."""
    
    def detect_status_quo_bias(self, position_changes: List[Dict],
                              market_changes: List[Dict]) -> Dict:
        try:
            if not position_changes or not market_changes:
                return {'bias_level': 0}
            
            position_change_rate = len([p for p in position_changes if p.get('changed', False)]) / len(position_changes)
            market_volatility = np.std([m.get('change', 0) for m in market_changes])
        
            expected_change_rate = min(1, market_volatility * 10)
        
            bias_level = max(0, expected_change_rate - position_change_rate)
        
            if bias_level > 0.3:
                state = 'STRONG_STATUS_QUO_BIAS'
                opportunity = 'EXPECT_DELAYED_REACTIONS'
            else:
                state = 'NORMAL'
                opportunity = 'NO_CLEAR_EDGE'
            
            return {
                'bias_level': bias_level,
                'state': state,
                'opportunity': opportunity
            }
        except Exception as e:
            import logging as _log
            _log.getLogger(__name__).error(f"Error in detect_status_quo_bias: {e}")
            raise


class EndowmentEffectTrader:
    """IDEA 180: Exploits endowment effect."""
    
    def calculate_endowment_premium(self, holding_period: float,
                                   position_size: float,
                                   emotional_attachment: float) -> Dict:
        try:
            base_premium = 0.1
            time_factor = min(1, holding_period / 30)
            size_factor = min(1, position_size / 10000)
        
            endowment_premium = base_premium * (1 + time_factor + size_factor + emotional_attachment)
        
            return {
                'endowment_premium': endowment_premium,
                'fair_value_adjustment': -endowment_premium,
                'recommendation': 'ACCOUNT_FOR_PREMIUM_IN_EXIT'
            }
        except Exception as e:
            import logging as _log
            _log.getLogger(__name__).error(f"Error in calculate_endowment_premium: {e}")
            raise


# IDEAS 181-200: Additional Psychological Innovations

class FOMODetector:
    """IDEA 181: Detects Fear Of Missing Out."""
    def detect(self, price_momentum: float, social_buzz: float, volume_surge: float) -> Dict:
        try:
            fomo_score = (price_momentum + social_buzz + volume_surge) / 3
            return {'fomo_score': fomo_score, 'fomo_active': fomo_score > 0.7}
        except Exception as e:
            import logging as _log
            _log.getLogger(__name__).error(f"Error in detect: {e}")
            raise


class RegretAversionTrader:
    """IDEA 182: Trades on regret aversion patterns."""
    def analyze(self, missed_opportunities: List[Dict]) -> Dict:
        try:
            if not missed_opportunities:
                return {'regret_level': 0}
            total_missed = sum(m.get('potential_gain', 0) for m in missed_opportunities)
            return {'regret_level': min(1, total_missed / 10000), 'likely_to_chase': total_missed > 5000}
        except Exception as e:
            import logging as _log
            _log.getLogger(__name__).error(f"Error in analyze: {e}")
            raise


class OptimismBiasExploiter:
    """IDEA 183: Exploits optimism bias."""
    def analyze(self, forecasts: List[float], actuals: List[float]) -> Dict:
        try:
            if not forecasts or not actuals:
                return {'optimism_bias': 0}
            bias = np.mean(forecasts) - np.mean(actuals)
            return {'optimism_bias': bias, 'overoptimistic': bias > 0.1}
        except Exception as e:
            import logging as _log
            _log.getLogger(__name__).error(f"Error in analyze: {e}")
            raise


class PessimismBiasExploiter:
    """IDEA 184: Exploits pessimism bias."""
    def analyze(self, forecasts: List[float], actuals: List[float]) -> Dict:
        try:
            if not forecasts or not actuals:
                return {'pessimism_bias': 0}
            bias = np.mean(actuals) - np.mean(forecasts)
            return {'pessimism_bias': bias, 'overpessimistic': bias > 0.1}
        except Exception as e:
            import logging as _log
            _log.getLogger(__name__).error(f"Error in analyze: {e}")
            raise


class HindsightBiasDetector:
    """IDEA 185: Detects hindsight bias in analysis."""
    def detect(self, pre_event_predictions: List[float], post_event_claims: List[float]) -> Dict:
        try:
            if not pre_event_predictions or not post_event_claims:
                return {'hindsight_bias': 0}
            bias = np.mean(post_event_claims) - np.mean(pre_event_predictions)
            return {'hindsight_bias': abs(bias), 'revision_detected': abs(bias) > 0.2}
        except Exception as e:
            import logging as _log
            _log.getLogger(__name__).error(f"Error in detect: {e}")
            raise


class SelfServingBiasTrader:
    """IDEA 186: Exploits self-serving attribution bias."""
    def analyze(self, win_attributions: List[str], loss_attributions: List[str]) -> Dict:
        try:
            internal_wins = sum(1 for a in win_attributions if 'skill' in a.lower())
            external_losses = sum(1 for a in loss_attributions if 'luck' in a.lower() or 'market' in a.lower())
            bias = (internal_wins / len(win_attributions) if win_attributions else 0) + \
                   (external_losses / len(loss_attributions) if loss_attributions else 0)
            return {'self_serving_bias': bias / 2, 'overconfident': bias > 1}
        except Exception as e:
            import logging as _log
            _log.getLogger(__name__).error(f"Error in analyze: {e}")
            raise


class BandwagonEffectTrader:
    """IDEA 187: Trades on bandwagon effect."""
    def detect(self, adoption_rate: np.ndarray) -> Dict:
        try:
            if len(adoption_rate) < 5:
                return {'bandwagon': False}
            acceleration = np.diff(np.diff(adoption_rate))
            return {'bandwagon': np.mean(acceleration) > 0, 'acceleration': np.mean(acceleration)}
        except Exception as e:
            import logging as _log
            _log.getLogger(__name__).error(f"Error in detect: {e}")
            raise


class SnobEffectTrader:
    """IDEA 188: Trades on snob effect (contrarian luxury)."""
    def detect(self, popularity: float, price: float) -> Dict:
        try:
            snob_indicator = price / (popularity + 1)
            return {'snob_effect': snob_indicator > 100, 'exclusivity_premium': snob_indicator}
        except Exception as e:
            import logging as _log
            _log.getLogger(__name__).error(f"Error in detect: {e}")
            raise


class VeblenEffectTrader:
    """IDEA 189: Trades on Veblen goods effect."""
    def detect(self, price_changes: np.ndarray, demand_changes: np.ndarray) -> Dict:
        try:
            if len(price_changes) != len(demand_changes):
                return {'veblen': False}
            correlation = np.corrcoef(price_changes, demand_changes)[0, 1]
            return {'veblen_effect': correlation > 0.5, 'correlation': correlation}
        except Exception as e:
            import logging as _log
            _log.getLogger(__name__).error(f"Error in detect: {e}")
            raise


class FramingEffectTrader:
    """IDEA 190: Exploits framing effects."""
    def analyze(self, positive_frame_response: float, negative_frame_response: float) -> Dict:
        try:
            framing_sensitivity = abs(positive_frame_response - negative_frame_response)
            return {'framing_sensitivity': framing_sensitivity, 'exploitable': framing_sensitivity > 0.3}
        except Exception as e:
            import logging as _log
            _log.getLogger(__name__).error(f"Error in analyze: {e}")
            raise


class DecoyEffectTrader:
    """IDEA 191: Uses decoy effect in positioning."""
    def create_decoy(self, target_position: Dict, competitor_position: Dict) -> Dict:
        try:
            decoy = target_position.copy()
            decoy['size'] = target_position['size'] * 0.8
            decoy['expected_return'] = target_position['expected_return'] * 0.7
            return {'decoy': decoy, 'makes_target_attractive': True}
        except Exception as e:
            import logging as _log
            _log.getLogger(__name__).error(f"Error in create_decoy: {e}")
            raise


class PrimingEffectTrader:
    """IDEA 192: Exploits priming effects."""
    def detect_priming(self, recent_news: List[str], trading_behavior: Dict) -> Dict:
        try:
            bullish_words = sum(1 for n in recent_news if any(w in n.lower() for w in ['bull', 'up', 'gain', 'profit']))
            bearish_words = sum(1 for n in recent_news if any(w in n.lower() for w in ['bear', 'down', 'loss', 'crash']))
            priming_direction = 'BULLISH' if bullish_words > bearish_words else 'BEARISH'
            return {'priming_direction': priming_direction, 'strength': abs(bullish_words - bearish_words)}
        except Exception as e:
            import logging as _log
            _log.getLogger(__name__).error(f"Error in detect_priming: {e}")
            raise


class PeakEndRuleTrader:
    """IDEA 193: Exploits peak-end rule in memory."""
    def analyze(self, experience_timeline: List[float]) -> Dict:
        try:
            if not experience_timeline:
                return {'remembered_value': 0}
            peak = max(experience_timeline, key=abs)
            end = experience_timeline[-1]
            remembered = (peak + end) / 2
            return {'remembered_value': remembered, 'peak': peak, 'end': end}
        except Exception as e:
            import logging as _log
            _log.getLogger(__name__).error(f"Error in analyze: {e}")
            raise


class ZeroRiskBiasTrader:
    """IDEA 194: Exploits zero-risk bias."""
    def detect(self, risk_preferences: List[Dict]) -> Dict:
        try:
            zero_risk_seekers = sum(1 for p in risk_preferences if p.get('preferred_risk', 1) == 0)
            ratio = zero_risk_seekers / len(risk_preferences) if risk_preferences else 0
            return {'zero_risk_bias': ratio, 'premium_for_certainty': ratio * 0.1}
        except Exception as e:
            import logging as _log
            _log.getLogger(__name__).error(f"Error in detect: {e}")
            raise


class UnitBiasTrader:
    """IDEA 195: Exploits unit bias in position sizing."""
    def detect(self, position_sizes: List[float]) -> Dict:
        try:
            round_positions = sum(1 for p in position_sizes if p == round(p))
            ratio = round_positions / len(position_sizes) if position_sizes else 0
            return {'unit_bias': ratio, 'exploitable': ratio > 0.7}
        except Exception as e:
            import logging as _log
            _log.getLogger(__name__).error(f"Error in detect: {e}")
            raise


class DenominationEffectTrader:
    """IDEA 196: Exploits denomination effect."""
    def analyze(self, large_trades: int, small_trades: int) -> Dict:
        try:
            ratio = small_trades / (large_trades + 1)
            return {'denomination_effect': ratio > 5, 'small_trade_preference': ratio}
        except Exception as e:
            import logging as _log
            _log.getLogger(__name__).error(f"Error in analyze: {e}")
            raise


class MoneyIllusionTrader:
    """IDEA 197: Exploits money illusion."""
    def detect(self, nominal_returns: float, real_returns: float) -> Dict:
        try:
            illusion = nominal_returns - real_returns
            return {'money_illusion': illusion, 'inflation_adjusted': real_returns}
        except Exception as e:
            import logging as _log
            _log.getLogger(__name__).error(f"Error in detect: {e}")
            raise


class HotHandFallacyTrader:
    """IDEA 198: Exploits hot hand fallacy."""
    def detect(self, win_streak: int, historical_win_rate: float) -> Dict:
        try:
            expected_streak_prob = historical_win_rate ** win_streak
            perceived_prob = min(0.99, historical_win_rate + win_streak * 0.05)
            fallacy = perceived_prob - expected_streak_prob
            return {'hot_hand_fallacy': fallacy, 'streak': win_streak}
        except Exception as e:
            import logging as _log
            _log.getLogger(__name__).error(f"Error in detect: {e}")
            raise


class GamblersFallacyTrader:
    """IDEA 199: Exploits gambler's fallacy."""
    def detect(self, loss_streak: int, historical_loss_rate: float) -> Dict:
        try:
            true_prob = historical_loss_rate
            perceived_prob = max(0.01, historical_loss_rate - loss_streak * 0.05)
            fallacy = true_prob - perceived_prob
            return {'gamblers_fallacy': fallacy, 'streak': loss_streak}
        except Exception as e:
            import logging as _log
            _log.getLogger(__name__).error(f"Error in detect: {e}")
            raise


class IllusionOfControlTrader:
    """IDEA 200: Exploits illusion of control."""
    def detect(self, active_decisions: int, passive_decisions: int, outcomes: List[float]) -> Dict:
        try:
            activity_ratio = active_decisions / (passive_decisions + 1)
            outcome_variance = np.var(outcomes) if outcomes else 0
            illusion = activity_ratio / (outcome_variance + 1)
            return {'illusion_of_control': min(1, illusion), 'overactive': activity_ratio > 2}
        except Exception as e:
            import logging as _log
            _log.getLogger(__name__).error(f"Error in detect: {e}")
            raise


__all__ = [
    'CrowdPsychologyManipulator', 'FearGreedExploiter', 'CognitiveDissonanceTrader',
    'AnchoringBiasExploiter', 'LossAversionTrader', 'ConfirmationBiasDetector',
    'HerdingBehaviorPredictor', 'RecencyBiasExploiter', 'OverconfidenceExploiter',
    'GameTheoryTrader', 'BluffDetector', 'EmotionalContagionTracker',
    'MentalAccountingExploiter', 'SunkCostExploiter', 'DispositionEffectTrader',
    'NarrativeFallacyDetector', 'AvailabilityHeuristicTrader', 'RepresentativenessTrader',
    'StatusQuoBiasExploiter', 'EndowmentEffectTrader', 'FOMODetector',
    'RegretAversionTrader', 'OptimismBiasExploiter', 'PessimismBiasExploiter',
    'HindsightBiasDetector', 'SelfServingBiasTrader', 'BandwagonEffectTrader',
    'SnobEffectTrader', 'VeblenEffectTrader', 'FramingEffectTrader',
    'DecoyEffectTrader', 'PrimingEffectTrader', 'PeakEndRuleTrader',
    'ZeroRiskBiasTrader', 'UnitBiasTrader', 'DenominationEffectTrader',
    'MoneyIllusionTrader', 'HotHandFallacyTrader', 'GamblersFallacyTrader',
    'IllusionOfControlTrader'
]
