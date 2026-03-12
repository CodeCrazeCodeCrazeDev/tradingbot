from __future__ import annotations
import logging
logger = logging.getLogger(__name__)
"""Enhanced performance analytics with emotional state tracking."""

import datetime as _dt
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple
import pandas as pd
import numpy as np
from loguru import logger

from trading_bot.analytics.performance import PerformanceAnalytics, Trade
from trading_bot.analytics.emotional_tracker import EmotionalStateTracker, TraderJournal
import datetime
import numpy
import pandas


class EnhancedPerformanceAnalytics(PerformanceAnalytics):
    """Enhanced performance analytics with emotional state tracking."""

    def __init__(self, trades: List[Trade], emotional_tracker: Optional[EmotionalStateTracker] = None) -> None:
        """Initialize enhanced performance analytics.
        
        Args:
            trades: List of executed trades
            emotional_tracker: Optional emotional state tracker
        """
        try:
            super().__init__(trades)
            self.emotional_tracker = emotional_tracker or EmotionalStateTracker()
            self.trader_journal = TraderJournal()
        
            # Associate trades with emotional states if available
            self._associate_trades_with_emotions()
        
            logger.info("EnhancedPerformanceAnalytics initialized with {} trades", len(trades))
        except Exception as e:
            logger.error(f"Error in __init__: {e}")
            raise
    
    def summary(self) -> Dict[str, Any]:
        """Return key metrics dict with emotional insights.
        
        Returns:
            Dictionary with performance metrics and emotional insights
        """
        # Get base summary
        try:
            base_summary = super().summary()
        
            if not base_summary:
                return {}
        
            # Add emotional insights
            emotional_insights = self._emotional_insights()
        
            # Combine summaries
            enhanced_summary = {**base_summary, **emotional_insights}
        
            return enhanced_summary
        except Exception as e:
            logger.error(f"Error in summary: {e}")
            raise
    
    def record_emotional_state(self, state: Dict[str, float], trade_id: Optional[str] = None) -> Dict[str, Any]:
        """Record the current emotional state.
        
        Args:
            state: Dictionary with emotional state values (0.0-1.0)
            trade_id: Optional ID of associated trade
            
        Returns:
            Dictionary with recorded state details
        """
        return self.emotional_tracker.record_state(state, trade_id)
    
    def add_journal_entry(self, entry_type: str, content: str, 
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
        return self.trader_journal.add_entry(entry_type, content, emotional_state, trade_id, metadata)
    
    def detect_emotional_state_from_actions(self, actions: List[Dict[str, Any]]) -> Dict[str, float]:
        """Detect emotional state from trading actions.
        
        Args:
            actions: List of recent trading actions
            
        Returns:
            Dictionary with detected emotional state
        """
        return self.emotional_tracker.detect_state_from_actions(actions)
    
    def get_emotional_state_history(self, hours: int = 24) -> List[Dict[str, Any]]:
        """Get emotional state history for the specified period.
        
        Args:
            hours: Number of hours to look back
            
        Returns:
            List of state records
        """
        return self.emotional_tracker.get_state_history(hours)
    
    def get_journal_entries(self, entry_type: Optional[str] = None, 
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
        return self.trader_journal.get_entries(entry_type, days, trade_id)
    
    def analyze_journal_patterns(self) -> Dict[str, Any]:
        """Analyze patterns in journal entries and emotional states.
        
        Returns:
            Dictionary with analysis results
        """
        return self.trader_journal.analyze_patterns()
    
    def _associate_trades_with_emotions(self) -> None:
        """Associate trades with emotional states if available."""
        try:
            for trade in self.trades:
                # Convert trade ID to string format
                trade_id = str(trade.ticket)
            
                # Get emotional state at trade entry time
                entry_time = _dt.datetime.fromtimestamp(trade.entry_time)
                exit_time = _dt.datetime.fromtimestamp(trade.exit_time)
            
                # Find closest emotional states
                states = self.emotional_tracker.get_state_history(hours=24)
            
                entry_state = None
                exit_state = None
            
                for state in states:
                    state_time = state.get('timestamp')
                    if state_time:
                        # Find closest state to entry time
                        if abs((state_time - entry_time).total_seconds()) < 300:  # Within 5 minutes
                            entry_state = state.get('state', {})
                    
                        # Find closest state to exit time
                        if abs((state_time - exit_time).total_seconds()) < 300:  # Within 5 minutes
                            exit_state = state.get('state', {})
            
                # Record states if found
                if entry_state:
                    self.emotional_tracker.trade_emotions[f"{trade_id}_entry"] = entry_state
            
                if exit_state:
                    self.emotional_tracker.trade_emotions[f"{trade_id}_exit"] = exit_state
        except Exception as e:
            logger.error(f"Error in _associate_trades_with_emotions: {e}")
            raise
    
    def _emotional_insights(self) -> Dict[str, Any]:
        """Generate emotional insights from trades and emotional states.
        
        Returns:
            Dictionary with emotional insights
        """
        try:
            insights = {
                'emotional_impact': {},
                'recommendations': []
            }
        
            # Check if we have enough data
            if not self.trades or not self.emotional_tracker.trade_emotions:
                return insights
        
            # Prepare trade results for analysis
            trade_results = []
            for trade in self.trades:
                trade_id = str(trade.ticket)
            
                # Get emotional states for this trade
                entry_emotions = self.emotional_tracker.trade_emotions.get(f"{trade_id}_entry", {})
                exit_emotions = self.emotional_tracker.trade_emotions.get(f"{trade_id}_exit", {})
            
                # Combine with trade data
                trade_result = {
                    'id': trade_id,
                    'profit': trade.profit,
                    'result': 'profit' if trade.profit > 0 else 'loss',
                    'direction': trade.direction,
                    'entry_time': _dt.datetime.fromtimestamp(trade.entry_time),
                    'exit_time': _dt.datetime.fromtimestamp(trade.exit_time),
                    'entry_emotions': entry_emotions,
                    'exit_emotions': exit_emotions,
                    'max_drawdown_pct': 0.01,  # Placeholder
                }
            
                trade_results.append(trade_result)
        
            # Analyze emotional impact
            if trade_results:
                impact_analysis = self.emotional_tracker.analyze_impact(trade_results)
                insights['emotional_impact'] = impact_analysis
            
                # Add recommendations
                if 'recommendations' in impact_analysis:
                    insights['recommendations'].extend(impact_analysis['recommendations'])
        
            # Add journal pattern insights
            journal_analysis = self.trader_journal.analyze_patterns()
            if 'recommendations' in journal_analysis:
                insights['recommendations'].extend(journal_analysis['recommendations'])
        
            # Add emotional correlation metrics
            insights['emotional_metrics'] = self._calculate_emotional_metrics()
        
            return insights
        except Exception as e:
            logger.error(f"Error in _emotional_insights: {e}")
            raise
    
    def _calculate_emotional_metrics(self) -> Dict[str, Any]:
        """Calculate metrics correlating emotions with performance.
        
        Returns:
            Dictionary with emotional metrics
        """
        try:
            metrics = {}
        
            # Check if we have enough data
            if not self.trades or not self.emotional_tracker.trade_emotions:
                return metrics
        
            # Get dominant emotions for each trade
            trade_emotions = {}
            for trade in self.trades:
                trade_id = str(trade.ticket)
                entry_emotions = self.emotional_tracker.trade_emotions.get(f"{trade_id}_entry", {})
            
                if entry_emotions:
                    # Find dominant emotion
                    dominant_emotion, intensity = max(entry_emotions.items(), key=lambda x: x[1])
                
                    if intensity > 0.3:  # Only consider significant emotions
                        trade_emotions[trade_id] = {
                            'dominant_emotion': dominant_emotion,
                            'intensity': intensity,
                            'profit': trade.profit,
                            'is_win': trade.profit > 0
                        }
        
            # Group trades by dominant emotion
            emotion_groups = {}
            for trade_id, data in trade_emotions.items():
                emotion = data['dominant_emotion']
                if emotion not in emotion_groups:
                    emotion_groups[emotion] = []
                emotion_groups[emotion].append(data)
        
            # Calculate metrics for each emotion
            for emotion, trades in emotion_groups.items():
                if len(trades) < 3:  # Need at least 3 trades for meaningful metrics
                    continue
            
                win_rate = sum(1 for t in trades if t['is_win']) / len(trades) * 100
                avg_profit = sum(t['profit'] for t in trades) / len(trades)
                avg_intensity = sum(t['intensity'] for t in trades) / len(trades)
            
                metrics[emotion] = {
                    'trade_count': len(trades),
                    'win_rate': round(win_rate, 2),
                    'avg_profit': round(avg_profit, 2),
                    'avg_intensity': round(avg_intensity, 2)
                }
        
            return metrics
        except Exception as e:
            logger.error(f"Error in _calculate_emotional_metrics: {e}")
            raise
    
    def generate_performance_report(self) -> Dict[str, Any]:
        """Generate a comprehensive performance report with emotional insights.
        
        Returns:
            Dictionary with performance report
        """
        # Get base summary
        try:
            summary = self.summary()
        
            # Get equity curve
            equity_df = self.equity_curve()
        
            # Get emotional state history
            emotional_history = self.get_emotional_state_history(hours=24*7)  # Last 7 days
        
            # Get journal entries
            journal_entries = self.get_journal_entries(days=7)
        
            # Create report
            report = {
                'summary': summary,
                'equity_data': {
                    'times': equity_df['time'].tolist() if not equity_df.empty else [],
                    'equity': equity_df['equity'].tolist() if not equity_df.empty else []
                },
                'emotional_data': {
                    'times': [e['timestamp'].timestamp() for e in emotional_history],
                    'states': [e['state'] for e in emotional_history]
                },
                'journal_entries': journal_entries,
                'recommendations': summary.get('recommendations', []),
                'timestamp': _dt.datetime.now().isoformat()
            }
        
            logger.info("Generated performance report with {} trades and {} emotional states",
                       len(self.trades), len(emotional_history))
        
            return report
        except Exception as e:
            logger.error(f"Error in generate_performance_report: {e}")
            raise
