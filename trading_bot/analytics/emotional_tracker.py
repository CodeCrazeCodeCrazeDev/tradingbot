import logging
logger = logging.getLogger(__name__)
"""Emotional state tracking for trader performance monitoring.

This module implements emotional state tracking capabilities to monitor
trader psychology and its impact on trading decisions and performance.
"""

import numpy as np
import pandas as pd
from typing import Any, Dict, List, Optional, Tuple, Union
from datetime import datetime, timedelta
from loguru import logger
import numpy
import pandas


class EmotionalStateTracker:
    """Tracks trader emotional states and their impact on performance.
    
    Monitors emotional states during trading sessions and analyzes
    correlations between emotions and trading outcomes.
    """
    
    def __init__(self):
        """Initialize the emotional state tracker."""
        try:
            self.emotional_states = {
                'fear': 0.0,
                'greed': 0.0,
                'confidence': 0.0,
                'doubt': 0.0,
                'frustration': 0.0,
                'satisfaction': 0.0,
                'anxiety': 0.0,
                'excitement': 0.0
            }
            self.state_history = []
            self.trade_emotions = {}  # Maps trade IDs to emotional states
            logger.info("EmotionalStateTracker initialized")
        except Exception as e:
            logger.error(f"Error in __init__: {e}")
            raise
    
    def record_state(self, state: Dict[str, float], trade_id: Optional[str] = None) -> Dict[str, Any]:
        """Record the current emotional state.
        
        Args:
            state: Dictionary with emotional state values (0.0-1.0)
            trade_id: Optional ID of associated trade
            
        Returns:
            Dictionary with recorded state details
        """
        # Validate state values
        try:
            validated_state = {}
            for emotion, value in state.items():
                if emotion in self.emotional_states:
                    validated_state[emotion] = max(0.0, min(1.0, value))
        
            # Fill missing emotions with current values
            for emotion in self.emotional_states:
                if emotion not in validated_state:
                    validated_state[emotion] = self.emotional_states.get(emotion, 0.0)
                
            # Update current state
            self.emotional_states = validated_state.copy()
        
            # Create state record
            timestamp = datetime.now()
            state_record = {
                'timestamp': timestamp,
                'state': validated_state.copy(),
                'trade_id': trade_id
            }
        
            # Add to history
            self.state_history.append(state_record)
        
            # Associate with trade if provided
            if trade_id:
                self.trade_emotions[trade_id] = validated_state.copy()
            
            logger.debug(f"Recorded emotional state: fear={validated_state.get('fear', 0):.2f}, "
                        f"greed={validated_state.get('greed', 0):.2f}, "
                        f"confidence={validated_state.get('confidence', 0):.2f}")
        
            return {
                'timestamp': timestamp,
                'state': validated_state,
                'trade_id': trade_id
            }
        except Exception as e:
            logger.error(f"Error in record_state: {e}")
            raise
    
    def detect_state_from_actions(self, actions: List[Dict[str, Any]]) -> Dict[str, float]:
        """Detect emotional state from trading actions.
        
        Args:
            actions: List of recent trading actions
            
        Returns:
            Dictionary with detected emotional state
        """
        try:
            if not actions:
                return self.emotional_states
            
            # This is a placeholder for actual emotional state detection
            # In a real implementation, this would use more sophisticated analysis
        
            detected_state = self.emotional_states.copy()
        
            # Look for patterns indicating emotional states
            for action in actions:
                action_type = action.get('type', '')
                result = action.get('result', '')
            
                # Detect fear
                if action_type == 'exit' and result == 'loss' and action.get('time_held', 0) < action.get('planned_hold_time', float('inf')):
                    detected_state['fear'] = min(1.0, detected_state['fear'] + 0.2)
                
                # Detect greed
                if action_type == 'hold' and result == 'unrealized_gain' and action.get('time_held', 0) > action.get('planned_hold_time', 0):
                    detected_state['greed'] = min(1.0, detected_state['greed'] + 0.2)
                
                # Detect confidence
                if action_type == 'entry' and action.get('position_size', 0) > action.get('average_position_size', 0):
                    detected_state['confidence'] = min(1.0, detected_state['confidence'] + 0.1)
                
                # Detect doubt
                if action_type == 'cancel' or (action_type == 'entry' and action.get('position_size', 0) < action.get('planned_position_size', float('inf'))):
                    detected_state['doubt'] = min(1.0, detected_state['doubt'] + 0.2)
                
                # Detect frustration
                if action_type == 'entry' and action.get('attempts', 1) > 1:
                    detected_state['frustration'] = min(1.0, detected_state['frustration'] + 0.15)
                
                # Detect satisfaction
                if action_type == 'exit' and result == 'profit' and action.get('profit_pct', 0) >= action.get('target_pct', 0):
                    detected_state['satisfaction'] = min(1.0, detected_state['satisfaction'] + 0.2)
                
            # Apply decay to previous emotions (emotions fade over time)
            for emotion in detected_state:
                if emotion not in ['confidence', 'satisfaction']:  # These persist longer
                    detected_state[emotion] *= 0.9
                
            logger.debug("Detected emotional state from trading actions")
            return detected_state
        except Exception as e:
            logger.error(f"Error in detect_state_from_actions: {e}")
            raise
    
    def get_current_state(self) -> Dict[str, float]:
        """Get the current emotional state.
        
        Returns:
            Dictionary with current emotional state values
        """
        return self.emotional_states.copy()
    
    def get_dominant_emotion(self) -> Tuple[str, float]:
        """Get the dominant emotion in the current state.
        
        Returns:
            Tuple of (emotion_name, intensity)
        """
        try:
            if not self.emotional_states:
                return ('neutral', 0.0)
            
            dominant = max(self.emotional_states.items(), key=lambda x: x[1])
            return dominant
        except Exception as e:
            logger.error(f"Error in get_dominant_emotion: {e}")
            raise
    
    def get_state_history(self, hours: int = 24) -> List[Dict[str, Any]]:
        """Get emotional state history for the specified period.
        
        Args:
            hours: Number of hours to look back
            
        Returns:
            List of state records
        """
        try:
            cutoff_time = datetime.now() - timedelta(hours=hours)
            return [record for record in self.state_history if record['timestamp'] >= cutoff_time]
        except Exception as e:
            logger.error(f"Error in get_state_history: {e}")
            raise
    
    def analyze_impact(self, trade_results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze the impact of emotions on trading performance.
        
        Args:
            trade_results: List of trade result dictionaries
            
        Returns:
            Dictionary with analysis results
        """
        try:
            if not trade_results or not self.trade_emotions:
                return {'error': 'Insufficient data for analysis'}
            
            # This is a placeholder for actual impact analysis
            # In a real implementation, this would use more sophisticated analysis
        
            # Initialize analysis results
            analysis = {
                'emotion_correlations': {},
                'optimal_states': {},
                'problematic_states': {},
                'recommendations': []
            }
        
            # Group trades by emotional state
            emotion_trades = {emotion: [] for emotion in self.emotional_states}
        
            for trade in trade_results:
                trade_id = trade.get('id')
                if trade_id in self.trade_emotions:
                    emotions = self.trade_emotions[trade_id]
                    dominant_emotion, intensity = max(emotions.items(), key=lambda x: x[1])
                
                    if intensity > 0.3:  # Only consider significant emotions
                        if dominant_emotion not in emotion_trades:
                            emotion_trades[dominant_emotion] = []
                        emotion_trades[dominant_emotion].append(trade)
        
            # Calculate performance metrics by emotion
            for emotion, trades in emotion_trades.items():
                if not trades:
                    continue
                
                # Calculate win rate
                wins = sum(1 for t in trades if t.get('result', '') == 'profit')
                win_rate = wins / len(trades) if trades else 0
            
                # Calculate average profit
                profits = [t.get('profit_pct', 0) for t in trades]
                avg_profit = sum(profits) / len(profits) if profits else 0
            
                # Calculate risk-reward ratio
                risk_reward = sum(t.get('profit_pct', 0) / max(0.01, abs(t.get('max_drawdown_pct', 0.01))) for t in trades) / len(trades) if trades else 0
            
                # Store correlation data
                analysis['emotion_correlations'][emotion] = {
                    'trade_count': len(trades),
                    'win_rate': win_rate,
                    'avg_profit': avg_profit,
                    'risk_reward': risk_reward
                }
            
                # Identify optimal emotional states
                if win_rate > 0.6 and avg_profit > 0:
                    analysis['optimal_states'][emotion] = {
                        'win_rate': win_rate,
                        'avg_profit': avg_profit
                    }
                
                # Identify problematic emotional states
                if win_rate < 0.4 or avg_profit < 0:
                    analysis['problematic_states'][emotion] = {
                        'win_rate': win_rate,
                        'avg_profit': avg_profit
                    }
        
            # Generate recommendations
            if 'fear' in analysis['problematic_states']:
                analysis['recommendations'].append(
                    "Fear is negatively impacting your trading. Consider using strict stop-loss orders "
                    "to reduce emotional decision-making."
                )
            
            if 'greed' in analysis['problematic_states']:
                analysis['recommendations'].append(
                    "Greed is leading to suboptimal results. Implement take-profit orders "
                    "and stick to your trading plan."
                )
            
            if 'confidence' in analysis['optimal_states']:
                analysis['recommendations'].append(
                    "Trading with confidence is producing good results. Identify what creates "
                    "this confidence and try to replicate those conditions."
                )
            
            if 'doubt' in analysis['problematic_states']:
                analysis['recommendations'].append(
                    "Doubt is negatively affecting your trades. Consider reducing position sizes "
                    "until confidence is restored."
                )
            
            logger.info(f"Completed emotional impact analysis with {len(analysis['recommendations'])} recommendations")
            return analysis
        except Exception as e:
            logger.error(f"Error in analyze_impact: {e}")
            raise


class TraderJournal:
    """Trading journal with emotional state tracking.
    
    Records trading activities, decisions, and associated emotional states
    to provide insights for performance improvement.
    """
    
    def __init__(self):
        """Initialize the trader journal."""
        try:
            self.entries = []
            self.emotional_tracker = EmotionalStateTracker()
            logger.info("TraderJournal initialized")
        except Exception as e:
            logger.error(f"Error in __init__: {e}")
            raise
    
    def add_entry(self, entry_type: str, content: str, 
                 emotional_state: Optional[Dict[str, float]] = None,
                 trade_id: Optional[str] = None,
                 metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Add a journal entry with associated emotional state.
        
        Args:
            entry_type: Type of entry ('market_analysis', 'trade_entry', 'trade_exit', 'reflection')
            content: Text content of the entry
            emotional_state: Optional dictionary with emotional state values
            trade_id: Optional ID of associated trade
            metadata: Optional additional metadata
            
        Returns:
            Dictionary with entry details
        """
        try:
            timestamp = datetime.now()
        
            # Record emotional state if provided
            if emotional_state:
                recorded_state = self.emotional_tracker.record_state(emotional_state, trade_id)
            else:
                recorded_state = self.emotional_tracker.get_current_state()
            
            # Create entry
            entry = {
                'id': f"entry_{len(self.entries) + 1}",
                'timestamp': timestamp,
                'type': entry_type,
                'content': content,
                'emotional_state': recorded_state,
                'trade_id': trade_id,
                'metadata': metadata or {}
            }
        
            # Add to entries
            self.entries.append(entry)
        
            logger.info(f"Added {entry_type} journal entry: {content[:50]}...")
            return entry
        except Exception as e:
            logger.error(f"Error in add_entry: {e}")
            raise
    
    def get_entries(self, entry_type: Optional[str] = None, 
                   days: int = 7, 
                   trade_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get journal entries filtered by type, time period, or trade.
        
        Args:
            entry_type: Optional type to filter by
            days: Number of days to look back
            trade_id: Optional trade ID to filter by
            
        Returns:
            List of matching journal entries
        """
        try:
            cutoff_time = datetime.now() - timedelta(days=days)
        
            filtered_entries = []
            for entry in self.entries:
                if entry['timestamp'] < cutoff_time:
                    continue
                
                if entry_type and entry['type'] != entry_type:
                    continue
                
                if trade_id and entry.get('trade_id') != trade_id:
                    continue
                
                filtered_entries.append(entry)
            
            return filtered_entries
        except Exception as e:
            logger.error(f"Error in get_entries: {e}")
            raise
    
    def analyze_patterns(self) -> Dict[str, Any]:
        """Analyze patterns in journal entries and emotional states.
        
        Returns:
            Dictionary with analysis results
        """
        try:
            if not self.entries:
                return {'error': 'No journal entries to analyze'}
            
            # This is a placeholder for actual pattern analysis
            # In a real implementation, this would use more sophisticated analysis
        
            # Initialize analysis
            analysis = {
                'entry_counts': {},
                'emotional_trends': {},
                'content_themes': {},
                'recommendations': []
            }
        
            # Count entry types
            for entry in self.entries:
                entry_type = entry.get('type', 'unknown')
                if entry_type not in analysis['entry_counts']:
                    analysis['entry_counts'][entry_type] = 0
                analysis['entry_counts'][entry_type] += 1
            
            # Analyze emotional trends
            emotions_by_day = {}
            for entry in self.entries:
                date_str = entry.get('timestamp', datetime.now()).strftime('%Y-%m-%d')
                emotional_state = entry.get('emotional_state', {}).get('state', {})
            
                if date_str not in emotions_by_day:
                    emotions_by_day[date_str] = []
                emotions_by_day[date_str].append(emotional_state)
            
            # Calculate daily averages
            for date_str, states in emotions_by_day.items():
                if not states:
                    continue
                
                avg_state = {}
                for state in states:
                    for emotion, value in state.items():
                        if emotion not in avg_state:
                            avg_state[emotion] = 0
                        avg_state[emotion] += value
                    
                # Calculate averages
                for emotion in avg_state:
                    avg_state[emotion] /= len(states)
                
                analysis['emotional_trends'][date_str] = avg_state
            
            # Simple content analysis
            all_content = ' '.join(entry.get('content', '') for entry in self.entries)
        
            # Count common trading terms
            terms = [
                'trend', 'support', 'resistance', 'breakout', 'reversal',
                'bullish', 'bearish', 'entry', 'exit', 'stop', 'target',
                'risk', 'reward', 'pattern', 'indicator', 'signal',
                'confident', 'uncertain', 'mistake', 'lesson', 'improve'
            ]
        
            for term in terms:
                count = all_content.lower().count(term)
                if count > 0:
                    analysis['content_themes'][term] = count
                
            # Generate recommendations
            if analysis['entry_counts'].get('reflection', 0) < analysis['entry_counts'].get('trade_entry', 0) / 2:
                analysis['recommendations'].append(
                    "Consider adding more reflection entries to analyze your trading decisions."
                )
            
            if 'mistake' in analysis['content_themes'] and analysis['content_themes']['mistake'] > 3:
                analysis['recommendations'].append(
                    "You've noted several mistakes. Review these entries to identify patterns and create rules to avoid them."
                )
            
            logger.info(f"Completed journal pattern analysis with {len(analysis['recommendations'])} recommendations")
            return analysis
        except Exception as e:
            logger.error(f"Error in analyze_patterns: {e}")
            raise
