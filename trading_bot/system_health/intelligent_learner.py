"""
AlphaAlgo Intelligent Self-Improvement
PHASE 4: Learning from losses and continuous improvement.
"""

import logging
import json
from typing import Dict, List, Any
from datetime import datetime
from pathlib import Path
from collections import defaultdict
import asyncio

logger = logging.getLogger(__name__)


class IntelligentLearner:
    """
    PHASE 4: Intelligent Self-Improvement
    Records trade losses and learns to improve over time.
    """
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize intelligent learner."""
        self.config = config
        
        # Paths
        self.log_dir = Path(config.get('log_dir', 'diagnostics/system_health'))
        self.performance_log = self.log_dir / 'performance_tracker.json'
        self.learning_log = self.log_dir / 'learning_history.json'
        
        # Learning data
        self.loss_causes = defaultdict(int)
        self.strategy_weights = config.get('initial_strategy_weights', {
            'trend_following': 0.3,
            'mean_reversion': 0.2,
            'momentum': 0.2,
            'breakout': 0.15,
            'volatility': 0.15
        })
        
        # Load existing performance data
        self.performance_history = self._load_performance_history()
        
        logger.info("IntelligentLearner initialized")
    
    async def record_trade_loss(self, trade: Dict[str, Any]) -> Dict[str, Any]:
        """
        Record a losing trade and analyze cause.
        
        Args:
            trade: Trade data including entry, exit, indicators, etc.
            
        Returns:
            Learning result with cause analysis
        """
        logger.info(f"Recording loss for trade {trade.get('id', 'unknown')}")
        
        # Analyze cause of loss
        cause_analysis = self._analyze_loss_cause(trade)
        
        # Store context
        learning_entry = {
            'timestamp': datetime.now().isoformat(),
            'trade_id': trade.get('id'),
            'symbol': trade.get('symbol'),
            'pnl': trade.get('pnl'),
            'cause': cause_analysis['primary_cause'],
            'indicators': trade.get('indicators', {}),
            'confidence_score': trade.get('confidence', 0),
            'order_size': trade.get('size', 0),
            'entry_price': trade.get('entry_price'),
            'exit_price': trade.get('exit_price'),
            'stop_loss': trade.get('stop_loss'),
            'take_profit': trade.get('take_profit'),
            'market_conditions': trade.get('market_conditions', {})
        }
        
        # Update loss cause statistics
        self.loss_causes[cause_analysis['primary_cause']] += 1
        
        # Adjust strategy weights based on learning
        weight_adjustments = self._calculate_weight_adjustments(cause_analysis)
        self._update_strategy_weights(weight_adjustments)
        
        # Save learning entry
        self._save_learning_entry(learning_entry)
        
        # Update performance tracker
        self._update_performance_tracker(trade, cause_analysis)
        
        logger.info(f"  Cause: {cause_analysis['primary_cause']}")
        logger.info(f"  Confidence: {cause_analysis['confidence']:.2f}")
        logger.info(f"  Weight adjustments applied")
        
        return {
            'cause_analysis': cause_analysis,
            'weight_adjustments': weight_adjustments,
            'new_weights': self.strategy_weights.copy()
        }
    
    def _analyze_loss_cause(self, trade: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze the cause of a trade loss."""
        causes = []
        
        # Check for trend misread
        if trade.get('market_conditions', {}).get('trend_strength', 0) < 0.3:
            causes.append({
                'cause': 'weak_trend',
                'confidence': 0.8,
                'description': 'Trend was too weak for trend-following strategy'
            })
        
        # Check for volatility spike
        if trade.get('market_conditions', {}).get('volatility_spike', False):
            causes.append({
                'cause': 'volatility_spike',
                'confidence': 0.9,
                'description': 'Unexpected volatility spike during trade'
            })
        
        # Check for TP/SL error
        entry = trade.get('entry_price', 0)
        sl = trade.get('stop_loss', 0)
        tp = trade.get('take_profit', 0)
        
        if entry and sl and tp:
            risk = abs(entry - sl)
            reward = abs(tp - entry)
            if reward / risk < 1.5:
                causes.append({
                    'cause': 'poor_risk_reward',
                    'confidence': 0.7,
                    'description': f'Risk/reward ratio {reward/risk:.2f} too low'
                })
        
        # Check for low confidence entry
        if trade.get('confidence', 0) < 0.6:
            causes.append({
                'cause': 'low_confidence',
                'confidence': 0.85,
                'description': f"Entry confidence {trade.get('confidence', 0):.2f} below threshold"
            })
        
        # Check for indicator divergence
        indicators = trade.get('indicators', {})
        if indicators.get('rsi_divergence') or indicators.get('macd_divergence'):
            causes.append({
                'cause': 'indicator_divergence',
                'confidence': 0.75,
                'description': 'Indicators showed divergence'
            })
        
        # Select primary cause (highest confidence)
        if causes:
            primary = max(causes, key=lambda x: x['confidence'])
            return {
                'primary_cause': primary['cause'],
                'confidence': primary['confidence'],
                'description': primary['description'],
                'all_causes': causes
            }
        else:
            return {
                'primary_cause': 'unknown',
                'confidence': 0.5,
                'description': 'Could not determine specific cause',
                'all_causes': []
            }
    
    def _calculate_weight_adjustments(self, cause_analysis: Dict[str, Any]) -> Dict[str, float]:
        """Calculate strategy weight adjustments based on loss cause."""
        adjustments = {}
        cause = cause_analysis['primary_cause']
        
        # Adjust weights based on cause
        if cause == 'weak_trend':
            adjustments['trend_following'] = -0.05
            adjustments['mean_reversion'] = +0.03
            adjustments['momentum'] = +0.02
        
        elif cause == 'volatility_spike':
            adjustments['volatility'] = -0.05
            adjustments['trend_following'] = +0.03
            adjustments['breakout'] = +0.02
        
        elif cause == 'poor_risk_reward':
            # Reduce all weights slightly, increase conservative strategies
            adjustments['mean_reversion'] = +0.05
        
        elif cause == 'low_confidence':
            # Reduce weight of strategy that generated the signal
            # In production: identify which strategy and reduce it
            pass
        
        elif cause == 'indicator_divergence':
            adjustments['momentum'] = -0.03
            adjustments['mean_reversion'] = +0.03
        
        return adjustments
    
    def _update_strategy_weights(self, adjustments: Dict[str, float]):
        """Update strategy weights with adjustments."""
        for strategy, adjustment in adjustments.items():
            if strategy in self.strategy_weights:
                self.strategy_weights[strategy] += adjustment
        
        # Normalize weights to sum to 1.0
        total = sum(self.strategy_weights.values())
        if total > 0:
            for strategy in self.strategy_weights:
                self.strategy_weights[strategy] /= total
    
    def _save_learning_entry(self, entry: Dict[str, Any]):
        """Save learning entry to log file."""
        # Load existing entries
        entries = []
        if self.learning_log.exists():
            with open(self.learning_log, 'r') as f:
                try:
                    entries = json.load(f)
                except Exception:
                    entries = []
        
        # Add new entry
        entries.append(entry)
        
        # Keep last 1000 entries
        entries = entries[-1000:]
        
        # Save
        with open(self.learning_log, 'w') as f:
            json.dump(entries, f, indent=2)
    
    def _update_performance_tracker(self, trade: Dict[str, Any], cause_analysis: Dict[str, Any]):
        """Update performance tracker JSON."""
        tracker = self.performance_history
        
        # Update statistics
        tracker['total_trades'] = tracker.get('total_trades', 0) + 1
        tracker['total_losses'] = tracker.get('total_losses', 0) + 1
        tracker['total_pnl'] = tracker.get('total_pnl', 0) + trade.get('pnl', 0)
        
        # Update cause statistics
        if 'loss_causes' not in tracker:
            tracker['loss_causes'] = {}
        
        cause = cause_analysis['primary_cause']
        tracker['loss_causes'][cause] = tracker['loss_causes'].get(cause, 0) + 1
        
        # Update strategy weights history
        if 'strategy_weights_history' not in tracker:
            tracker['strategy_weights_history'] = []
        
        tracker['strategy_weights_history'].append({
            'timestamp': datetime.now().isoformat(),
            'weights': self.strategy_weights.copy()
        })
        
        # Keep last 100 weight updates
        tracker['strategy_weights_history'] = tracker['strategy_weights_history'][-100:]
        
        # Save
        with open(self.performance_log, 'w') as f:
            json.dump(tracker, f, indent=2)
        
        self.performance_history = tracker
    
    def _load_performance_history(self) -> Dict[str, Any]:
        """Load existing performance history."""
        if self.performance_log.exists():
            try:
                with open(self.performance_log, 'r') as f:
                    return json.load(f)
            except Exception:
                pass
        
        return {
            'total_trades': 0,
            'total_losses': 0,
            'total_pnl': 0,
            'loss_causes': {},
            'strategy_weights_history': []
        }
    
    def get_current_weights(self) -> Dict[str, float]:
        """Get current strategy weights."""
        return self.strategy_weights.copy()
    
    def get_performance_summary(self) -> Dict[str, Any]:
        """Get performance summary."""
        return {
            'total_trades': self.performance_history.get('total_trades', 0),
            'total_losses': self.performance_history.get('total_losses', 0),
            'total_pnl': self.performance_history.get('total_pnl', 0),
            'loss_causes': dict(self.loss_causes),
            'current_weights': self.strategy_weights.copy()
        }
