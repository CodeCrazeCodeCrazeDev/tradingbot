"""Integration tests for emotional tracking and enhanced performance analytics."""
import unittest
from datetime import datetime
from typing import Optional
import pytest
from typing import Set

# Skip this module if emotional tracking is not available
pytest.importorskip("trading_bot.analytics.emotional_tracker")

from trading_bot.analytics.emotional_tracker import EmotionalStateTracker as EmotionalTracker

# Try to import risk_metrics, skip if not available
try:
    from trading_bot.analytics.risk_metrics import RiskMetrics, PerformanceAnalytics
except ImportError:
    RiskMetrics = None
    PerformanceAnalytics = None


class TestEmotionalTracking(unittest.TestCase):
    """Test cases for emotional tracking functionality."""

    def setUp(self):
        """Set up test fixtures."""
        self.tracker = EmotionalTracker()
        
        # Create sample emotional states
        self.sample_state = {
            'fear': 0.7,
            'greed': 0.2,
            'confidence': 0.5,
            'doubt': 0.6,
            'excitement': 0.8,
            'frustration': 0.3
        }
        
        # Create sample trades
        self.trades = [
            {
                'ticket': 1,
                'symbol': "EURUSD",
                'direction': "buy",
                'lot': 0.1,
                'entry_price': 1.1000,
                'exit_price': 1.1050,
                'entry_time': datetime.now().timestamp() - 3600,  # 1 hour ago
                'exit_time': datetime.now().timestamp() - 1800,   # 30 minutes ago
                'profit': 50.0
            },
            {
                'ticket': 2,
                'symbol': "GBPUSD",
                'direction': "sell",
                'lot': 0.2,
                'entry_price': 1.2500,
                'exit_price': 1.2450,
                'entry_time': datetime.now().timestamp() - 7200,  # 2 hours ago
                'exit_time': datetime.now().timestamp() - 5400,   # 1.5 hours ago
                'profit': 100.0
            },
            {
                'ticket': 3,
                'symbol': "USDJPY",
                'direction': "buy",
                'lot': 0.1,
                'entry_price': 110.00,
                'exit_price': 109.50,
                'entry_time': datetime.now().timestamp() - 10800,  # 3 hours ago
                'exit_time': datetime.now().timestamp() - 9000,    # 2.5 hours ago
                'profit': -50.0
            }
        ]

    def test_emotional_state_recording(self):
        """Test recording emotional states."""
        state_record = self.tracker.record_state(self.sample_state)
        self.assertIsInstance(state_record, dict)
        self.assertIn('timestamp', state_record)
        self.assertIn('state', state_record)
        self.assertEqual(state_record['state'], self.sample_state)
        
        # Check that the state was added to history
        history = self.tracker.get_state_history(hours=1)
        self.assertGreaterEqual(len(history), 1)
        
    def test_emotion_detection_from_actions(self):
        """Test detecting emotions from trading actions."""
        actions = [
            {
                'action': 'order_entry',
                'symbol': 'EURUSD',
                'direction': 'buy',
                'lot': 0.1,
                'price': 1.1000,
                'timestamp': datetime.now().timestamp() - 60,
                'metadata': {
                    'hesitation_time': 45,  # seconds between signal and execution
                    'modified_times': 3,    # number of times order was modified
                    'cancelled_orders': 2   # number of cancelled orders before execution
                }
            }
        ]
        
        detected_state = self.tracker.detect_state_from_actions(actions)
        self.assertIsInstance(detected_state, dict)
        self.assertGreaterEqual(len(detected_state), 1)
        
    def test_emotional_impact_analysis(self):
        """Test analyzing emotional impact on trading performance."""
        # Record emotional states for trades
        for trade in self.trades:
            trade_id = str(trade['ticket'])
            
            # Entry emotion - different for each trade
            if trade['ticket'] == 1:
                entry_emotion = {'confidence': 0.8, 'fear': 0.2}
            elif trade['ticket'] == 2:
                entry_emotion = {'confidence': 0.9, 'greed': 0.7}
            else:
                entry_emotion = {'doubt': 0.8, 'fear': 0.7}
                
            # Exit emotion - different for each trade
            if trade['ticket'] == 1:
                exit_emotion = {'excitement': 0.8, 'greed': 0.6}
            elif trade['ticket'] == 2:
                exit_emotion = {'satisfaction': 0.9, 'confidence': 0.8}
            else:
                exit_emotion = {'frustration': 0.9, 'doubt': 0.7}
                
            # Record emotions
            self.tracker.trade_emotions[f"{trade_id}_entry"] = entry_emotion
            self.tracker.trade_emotions[f"{trade_id}_exit"] = exit_emotion
        
        # Prepare trade results for analysis
        trade_results = []
        for trade in self.trades:
            trade_id = str(trade['ticket'])
            
            # Get emotional states for this trade
            entry_emotions = self.tracker.trade_emotions.get(f"{trade_id}_entry", {})
            exit_emotions = self.tracker.trade_emotions.get(f"{trade_id}_exit", {})
            
            # Combine with trade data
            trade_result = {
                'id': trade_id,
                'profit': trade['profit'],
                'result': 'profit' if trade['profit'] > 0 else 'loss',
                'direction': trade['direction'],
                'entry_time': datetime.fromtimestamp(trade['entry_time']),
                'exit_time': datetime.fromtimestamp(trade['exit_time']),
                'entry_emotions': entry_emotions,
                'exit_emotions': exit_emotions
            }
            
            trade_results.append(trade_result)
        
        # Analyze impact
        impact = self.tracker.analyze_impact(trade_results)
        self.assertIsInstance(impact, dict)
        self.assertIn('correlations', impact)
        self.assertIn('recommendations', impact)


class TestEnhancedPerformanceAnalytics(unittest.TestCase):
    """Test cases for enhanced performance analytics."""

    def setUp(self):
        """Set up test fixtures."""
        # Create sample trades
        self.trades = [
            {
                'ticket': 1,
                'symbol': "EURUSD",
                'direction': "buy",
                'lot': 0.1,
                'entry_price': 1.1000,
                'exit_price': 1.1050,
                'entry_time': datetime.now().timestamp() - 3600,
                'exit_time': datetime.now().timestamp() - 1800,
                'profit': 50.0
            },
            {
                'ticket': 2,
                'symbol': "GBPUSD",
                'direction': "sell",
                'lot': 0.2,
                'entry_price': 1.2500,
                'exit_price': 1.2450,
                'entry_time': datetime.now().timestamp() - 7200,
                'exit_time': datetime.now().timestamp() - 5400,
                'profit': 100.0
            },
            {
                'ticket': 3,
                'symbol': "USDJPY",
                'direction': "buy",
                'lot': 0.1,
                'entry_price': 110.00,
                'exit_price': 109.50,
                'entry_time': datetime.now().timestamp() - 10800,
                'exit_time': datetime.now().timestamp() - 9000,
                'profit': -50.0
            }
        ]
        
        # Create emotional tracker
        self.tracker = EmotionalTracker()
        
        # Create enhanced performance analytics
        self.enhanced_analytics = PerformanceAnalytics(
            self.trades, 
            self.tracker
        )
        
        # Record emotional states for trades
        for trade in self.trades:
            trade_id = str(trade['ticket'])
            
            # Entry emotion - different for each trade
            if trade['ticket'] == 1:
                entry_emotion = {'confidence': 0.8, 'fear': 0.2}
            elif trade['ticket'] == 2:
                entry_emotion = {'confidence': 0.9, 'greed': 0.7}
            else:
                entry_emotion = {'doubt': 0.8, 'fear': 0.7}
                
            # Exit emotion - different for each trade
            if trade['ticket'] == 1:
                exit_emotion = {'excitement': 0.8, 'greed': 0.6}
            elif trade['ticket'] == 2:
                exit_emotion = {'satisfaction': 0.9, 'confidence': 0.8}
            else:
                exit_emotion = {'frustration': 0.9, 'doubt': 0.7}
                
            # Record emotions
            self.tracker.trade_emotions[f"{trade_id}_entry"] = entry_emotion
            self.tracker.trade_emotions[f"{trade_id}_exit"] = exit_emotion

    def test_enhanced_summary(self):
        """Test enhanced performance summary with emotional insights."""
        summary = self.enhanced_analytics.summary()
        self.assertIsInstance(summary, dict)
        
        # Check base metrics
        self.assertIn('trades', summary)
        self.assertIn('win_rate', summary)
        self.assertIn('net_profit', summary)
        
        # Check emotional insights
        self.assertIn('emotional_impact', summary)
        self.assertIn('recommendations', summary)
        
    def test_emotional_metrics_calculation(self):
        """Test calculation of emotional metrics."""
        metrics = self.tracker.calculate_emotional_metrics(self.trades)
        self.assertIsInstance(metrics, dict)
        
        # Check for emotion metrics
        for emotion in ['confidence', 'fear', 'doubt']:
            if emotion in metrics:
                self.assertIn('win_rate', metrics[emotion])
                self.assertIn('avg_profit', metrics[emotion])
                
    def test_performance_report_generation(self):
        """Test generating comprehensive performance report."""
        report = self.enhanced_analytics.generate_performance_report()
        self.assertIsInstance(report, dict)
        
        # Check report sections
        self.assertIn('summary', report)
        self.assertIn('equity_data', report)
        self.assertIn('emotional_data', report)
        self.assertIn('recommendations', report)


if __name__ == '__main__':
    unittest.main()
