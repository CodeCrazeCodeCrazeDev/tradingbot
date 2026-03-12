import logging
logger = logging.getLogger(__name__)
"""Performance Feedback Loops and Knowledge Base Expansion.

This module implements continuous feedback loops that enable the trading bot
to learn from its experiences and expand its knowledge base automatically.
"""

import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Set, Tuple
from dataclasses import dataclass, field
from enum import Enum
from loguru import logger
from collections import defaultdict, deque
import json
import sqlite3
from pathlib import Path
import numpy
import pandas


class FeedbackType(Enum):
    """Types of feedback loops."""
    PERFORMANCE_FEEDBACK = "performance_feedback"
    STRATEGY_FEEDBACK = "strategy_feedback"
    RISK_FEEDBACK = "risk_feedback"
    MARKET_FEEDBACK = "market_feedback"
    PARAMETER_FEEDBACK = "parameter_feedback"


@dataclass
class FeedbackLoop:
    """A feedback loop configuration."""
    loop_id: str
    feedback_type: FeedbackType
    trigger_condition: str
    action: str
    learning_rate: float
    active: bool = True
    trigger_count: int = 0
    last_triggered: Optional[datetime] = None
    effectiveness_score: float = 0.5


@dataclass
class KnowledgeEntry:
    """Entry in the knowledge base."""
    entry_id: str
    category: str
    content: Dict[str, Any]
    confidence: float
    source: str
    created_date: datetime
    last_updated: datetime
    usage_count: int = 0
    validation_score: float = 0.5


class PerformanceFeedbackSystem:
    """Comprehensive feedback loop and knowledge expansion system."""
    
    def __init__(self, config: Optional[Dict] = None):
        """Initialize the feedback system."""
        try:
            self.config = config or {}
            self.feedback_loops = {}
            self.knowledge_base = {}
            self.performance_buffer = deque(maxlen=1000)
            self.learning_history = []
        
            # Database for persistent storage
            self.db_path = self.config.get('db_path', 'data/knowledge_base.db')
            self._initialize_database()
        
            # Feedback parameters
            self.feedback_sensitivity = self.config.get('feedback_sensitivity', 0.1)
            self.knowledge_retention_days = self.config.get('knowledge_retention_days', 365)
            self.min_confidence_threshold = self.config.get('min_confidence_threshold', 0.6)
        
            # Initialize feedback loops
            self._initialize_feedback_loops()
        
            logger.info("PerformanceFeedbackSystem initialized")
        except Exception as e:
            logger.error(f"Error in __init__: {e}")
            raise
    
    def _initialize_database(self):
        """Initialize SQLite database for knowledge storage."""
        try:
            Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)
        
            with sqlite3.connect(self.db_path) as conn:
                conn.execute('''
                    CREATE TABLE IF NOT EXISTS knowledge_entries (
                        entry_id TEXT PRIMARY KEY,
                        category TEXT,
                        content TEXT,
                        confidence REAL,
                        source TEXT,
                        created_date TEXT,
                        last_updated TEXT,
                        usage_count INTEGER,
                        validation_score REAL
                    )
                ''')
            
                conn.execute('''
                    CREATE TABLE IF NOT EXISTS feedback_history (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        loop_id TEXT,
                        trigger_time TEXT,
                        conditions TEXT,
                        action_taken TEXT,
                        outcome TEXT
                    )
                ''')
        except Exception as e:
            logger.error(f"Error in _initialize_database: {e}")
            raise
    
    def _initialize_feedback_loops(self):
        """Initialize standard feedback loops."""
        # Performance degradation feedback
        try:
            self.feedback_loops['perf_degradation'] = FeedbackLoop(
                loop_id='perf_degradation',
                feedback_type=FeedbackType.PERFORMANCE_FEEDBACK,
                trigger_condition='win_rate < 0.4 for 10 trades',
                action='reduce_risk_and_analyze_patterns',
                learning_rate=0.2
            )
        
            # Strategy effectiveness feedback
            self.feedback_loops['strategy_effectiveness'] = FeedbackLoop(
                loop_id='strategy_effectiveness',
                feedback_type=FeedbackType.STRATEGY_FEEDBACK,
                trigger_condition='strategy_underperforming for 20 trades',
                action='rotate_strategy_and_learn_patterns',
                learning_rate=0.15
            )
        
            # Risk management feedback
            self.feedback_loops['risk_management'] = FeedbackLoop(
                loop_id='risk_management',
                feedback_type=FeedbackType.RISK_FEEDBACK,
                trigger_condition='large_loss > 5% or consecutive_losses > 3',
                action='tighten_risk_parameters',
                learning_rate=0.3
            )
        
            # Market regime feedback
            self.feedback_loops['market_regime'] = FeedbackLoop(
                loop_id='market_regime',
                feedback_type=FeedbackType.MARKET_FEEDBACK,
                trigger_condition='regime_detection_accuracy < 0.7',
                action='update_regime_parameters',
                learning_rate=0.1
            )
        
            # Parameter optimization feedback
            self.feedback_loops['parameter_optimization'] = FeedbackLoop(
                loop_id='parameter_optimization',
                feedback_type=FeedbackType.PARAMETER_FEEDBACK,
                trigger_condition='parameter_performance_decline > 0.1',
                action='trigger_parameter_reoptimization',
                learning_rate=0.05
            )
        except Exception as e:
            logger.error(f"Error in _initialize_feedback_loops: {e}")
            raise
    
    def process_trade_feedback(self, trade_result: Dict[str, Any]):
        """Process feedback from a completed trade."""
        try:
            self.performance_buffer.append({
                'timestamp': datetime.now(),
                'trade_result': trade_result,
                'pnl': trade_result.get('pnl', 0),
                'strategy': trade_result.get('strategy', 'unknown'),
                'regime': trade_result.get('regime', 'unknown'),
                'confidence': trade_result.get('confidence', 0.5)
            })
        
            # Check all feedback loops
            for loop in self.feedback_loops.values():
                if loop.active and self._evaluate_trigger_condition(loop, trade_result):
                    self._execute_feedback_action(loop, trade_result)
        
            # Extract knowledge from trade
            self._extract_trade_knowledge(trade_result)
        except Exception as e:
            logger.error(f"Error in process_trade_feedback: {e}")
            raise
    
    def _evaluate_trigger_condition(self, loop: FeedbackLoop, trade_result: Dict[str, Any]) -> bool:
        """Evaluate if a feedback loop should be triggered."""
        try:
            condition = loop.trigger_condition
            recent_trades = list(self.performance_buffer)[-20:]  # Last 20 trades
        
            if 'win_rate < 0.4 for 10 trades' in condition:
                if len(recent_trades) >= 10:
                    wins = sum(1 for t in recent_trades[-10:] if t['pnl'] > 0)
                    return wins / 10 < 0.4
        
            elif 'strategy_underperforming for 20 trades' in condition:
                if len(recent_trades) >= 20:
                    strategy = trade_result.get('strategy', 'unknown')
                    strategy_trades = [t for t in recent_trades if t['trade_result'].get('strategy') == strategy]
                    if len(strategy_trades) >= 10:
                        avg_pnl = np.mean([t['pnl'] for t in strategy_trades])
                        overall_avg = np.mean([t['pnl'] for t in recent_trades])
                        return avg_pnl < overall_avg * 0.8
        
            elif 'large_loss > 5%' in condition:
                return abs(trade_result.get('pnl', 0)) > 0.05
        
            elif 'consecutive_losses > 3' in condition:
                if len(recent_trades) >= 3:
                    return all(t['pnl'] < 0 for t in recent_trades[-3:])
        
            elif 'regime_detection_accuracy < 0.7' in condition:
                # This would be evaluated based on regime prediction accuracy
                return trade_result.get('regime_accuracy', 1.0) < 0.7
        
            elif 'parameter_performance_decline > 0.1' in condition:
                # This would be evaluated based on parameter performance tracking
                return trade_result.get('parameter_performance_decline', 0.0) > 0.1
        
            return False
        except Exception as e:
            logger.error(f"Error in _evaluate_trigger_condition: {e}")
            raise
    
    def _execute_feedback_action(self, loop: FeedbackLoop, trade_result: Dict[str, Any]):
        """Execute the action for a triggered feedback loop."""
        try:
            loop.trigger_count += 1
            loop.last_triggered = datetime.now()
        
            action = loop.action
            adjustments = {}
        
            if action == 'reduce_risk_and_analyze_patterns':
                adjustments = {
                    'risk_multiplier': 0.7,
                    'position_size_multiplier': 0.8,
                    'analyze_losing_patterns': True
                }
                self._analyze_losing_patterns()
        
            elif action == 'rotate_strategy_and_learn_patterns':
                adjustments = {
                    'force_strategy_rotation': True,
                    'learn_strategy_patterns': True
                }
                self._learn_strategy_patterns(trade_result.get('strategy', 'unknown'))
        
            elif action == 'tighten_risk_parameters':
                adjustments = {
                    'stop_loss_multiplier': 0.8,
                    'take_profit_multiplier': 0.9,
                    'max_positions_multiplier': 0.8
                }
        
            elif action == 'update_regime_parameters':
                adjustments = {
                    'regime_sensitivity_multiplier': 1.1,
                    'regime_confirmation_required': True
                }
        
            elif action == 'trigger_parameter_reoptimization':
                adjustments = {
                    'force_parameter_optimization': True,
                    'optimization_aggressiveness': 1.2
                }
        
            # Store feedback action in history
            self._store_feedback_history(loop, trade_result, adjustments)
        
            # Update loop effectiveness
            self._update_loop_effectiveness(loop, adjustments)
        
            logger.info(f"Executed feedback action: {action} (loop: {loop.loop_id})")
        except Exception as e:
            logger.error(f"Error in _execute_feedback_action: {e}")
            raise
    
    def _analyze_losing_patterns(self):
        """Analyze patterns in losing trades."""
        try:
            losing_trades = [t for t in self.performance_buffer if t['pnl'] < 0]
        
            if len(losing_trades) < 5:
                return
        
            # Group by common characteristics
            patterns = defaultdict(list)
        
            for trade in losing_trades[-20:]:  # Last 20 losing trades
                strategy = trade['trade_result'].get('strategy', 'unknown')
                regime = trade['trade_result'].get('regime', 'unknown')
                confidence = trade['confidence']
            
                # Group by strategy-regime combination
                key = f"{strategy}_{regime}"
                patterns[key].append(trade)
            
                # Group by confidence level
                conf_key = f"confidence_{int(confidence * 10) / 10}"
                patterns[conf_key].append(trade)
        
            # Identify significant patterns
            for pattern_key, trades in patterns.items():
                if len(trades) >= 3:  # Significant pattern
                    avg_loss = np.mean([t['pnl'] for t in trades])
                
                    knowledge_entry = KnowledgeEntry(
                        entry_id=f"losing_pattern_{pattern_key}_{int(datetime.now().timestamp())}",
                        category="losing_patterns",
                        content={
                            'pattern_key': pattern_key,
                            'frequency': len(trades),
                            'avg_loss': avg_loss,
                            'recommendation': f"Avoid or reduce exposure to {pattern_key}",
                            'confidence_adjustment': -0.1
                        },
                        confidence=min(1.0, len(trades) / 10.0),
                        source="feedback_analysis",
                        created_date=datetime.now(),
                        last_updated=datetime.now()
                    )
                
                    self._add_knowledge_entry(knowledge_entry)
        except Exception as e:
            logger.error(f"Error in _analyze_losing_patterns: {e}")
            raise
    
    def _learn_strategy_patterns(self, strategy: str):
        """Learn patterns specific to a strategy."""
        try:
            strategy_trades = [t for t in self.performance_buffer 
                              if t['trade_result'].get('strategy') == strategy]
        
            if len(strategy_trades) < 10:
                return
        
            # Analyze strategy performance by regime
            regime_performance = defaultdict(list)
            for trade in strategy_trades:
                regime = trade['trade_result'].get('regime', 'unknown')
                regime_performance[regime].append(trade['pnl'])
        
            # Identify best and worst regimes for this strategy
            for regime, pnls in regime_performance.items():
                if len(pnls) >= 3:
                    avg_pnl = np.mean(pnls)
                    win_rate = sum(1 for pnl in pnls if pnl > 0) / len(pnls)
                
                    knowledge_entry = KnowledgeEntry(
                        entry_id=f"strategy_regime_{strategy}_{regime}_{int(datetime.now().timestamp())}",
                        category="strategy_performance",
                        content={
                            'strategy': strategy,
                            'regime': regime,
                            'avg_pnl': avg_pnl,
                            'win_rate': win_rate,
                            'trade_count': len(pnls),
                            'effectiveness': 'high' if avg_pnl > 0 and win_rate > 0.5 else 'low'
                        },
                        confidence=min(1.0, len(pnls) / 20.0),
                        source="strategy_analysis",
                        created_date=datetime.now(),
                        last_updated=datetime.now()
                    )
                
                    self._add_knowledge_entry(knowledge_entry)
        except Exception as e:
            logger.error(f"Error in _learn_strategy_patterns: {e}")
            raise
    
    def _extract_trade_knowledge(self, trade_result: Dict[str, Any]):
        """Extract general knowledge from trade results."""
        # Market condition insights
        try:
            regime = trade_result.get('regime', 'unknown')
            pnl = trade_result.get('pnl', 0)
            confidence = trade_result.get('confidence', 0.5)
        
            # High confidence trades
            if confidence > 0.8:
                outcome = 'success' if pnl > 0 else 'failure'
            
                knowledge_entry = KnowledgeEntry(
                    entry_id=f"high_confidence_{outcome}_{int(datetime.now().timestamp())}",
                    category="confidence_outcomes",
                    content={
                        'confidence_level': confidence,
                        'outcome': outcome,
                        'pnl': pnl,
                        'regime': regime,
                        'lesson': f"High confidence in {regime} regime led to {outcome}"
                    },
                    confidence=0.8,
                    source="trade_extraction",
                    created_date=datetime.now(),
                    last_updated=datetime.now()
                )
            
                self._add_knowledge_entry(knowledge_entry)
        
            # Regime-specific performance
            if regime != 'unknown':
                regime_key = f"regime_performance_{regime}"
            
                if regime_key in self.knowledge_base:
                    # Update existing knowledge
                    entry = self.knowledge_base[regime_key]
                    content = entry.content
                    content['trade_count'] = content.get('trade_count', 0) + 1
                    content['total_pnl'] = content.get('total_pnl', 0) + pnl
                    content['avg_pnl'] = content['total_pnl'] / content['trade_count']
                    entry.last_updated = datetime.now()
                    entry.usage_count += 1
                else:
                    # Create new knowledge entry
                    knowledge_entry = KnowledgeEntry(
                        entry_id=regime_key,
                        category="regime_performance",
                        content={
                            'regime': regime,
                            'trade_count': 1,
                            'total_pnl': pnl,
                            'avg_pnl': pnl
                        },
                        confidence=0.5,
                        source="trade_extraction",
                        created_date=datetime.now(),
                        last_updated=datetime.now()
                    )
                
                    self._add_knowledge_entry(knowledge_entry)
        except Exception as e:
            logger.error(f"Error in _extract_trade_knowledge: {e}")
            raise
    
    def _add_knowledge_entry(self, entry: KnowledgeEntry):
        """Add or update a knowledge base entry."""
        try:
            self.knowledge_base[entry.entry_id] = entry
        
            # Store in database
            with sqlite3.connect(self.db_path) as conn:
                conn.execute('''
                    INSERT OR REPLACE INTO knowledge_entries 
                    (entry_id, category, content, confidence, source, created_date, 
                     last_updated, usage_count, validation_score)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    entry.entry_id,
                    entry.category,
                    json.dumps(entry.content),
                    entry.confidence,
                    entry.source,
                    entry.created_date.isoformat(),
                    entry.last_updated.isoformat(),
                    entry.usage_count,
                    entry.validation_score
                ))
        except Exception as e:
            logger.error(f"Error in _add_knowledge_entry: {e}")
            raise
    
    def _store_feedback_history(self, loop: FeedbackLoop, trade_result: Dict[str, Any], 
                               adjustments: Dict[str, Any]):
        """Store feedback action in history."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute('''
                    INSERT INTO feedback_history 
                    (loop_id, trigger_time, conditions, action_taken, outcome)
                    VALUES (?, ?, ?, ?, ?)
                ''', (
                    loop.loop_id,
                    datetime.now().isoformat(),
                    json.dumps(trade_result),
                    json.dumps(adjustments),
                    'pending'  # Outcome will be updated later
                ))
        except Exception as e:
            logger.error(f"Error in _store_feedback_history: {e}")
            raise
    
    def _update_loop_effectiveness(self, loop: FeedbackLoop, adjustments: Dict[str, Any]):
        """Update the effectiveness score of a feedback loop."""
        # This would be updated based on subsequent performance
        # For now, we'll use a simple heuristic
        try:
            recent_performance = list(self.performance_buffer)[-10:]
            if recent_performance:
                avg_recent_pnl = np.mean([t['pnl'] for t in recent_performance])
                if avg_recent_pnl > 0:
                    loop.effectiveness_score = min(1.0, loop.effectiveness_score + 0.1)
                else:
                    loop.effectiveness_score = max(0.0, loop.effectiveness_score - 0.05)
        except Exception as e:
            logger.error(f"Error in _update_loop_effectiveness: {e}")
            raise
    
    def get_knowledge_insights(self, category: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get insights from the knowledge base."""
        try:
            insights = []
        
            for entry in self.knowledge_base.values():
                if category and entry.category != category:
                    continue
            
                if entry.confidence >= self.min_confidence_threshold:
                    insights.append({
                        'entry_id': entry.entry_id,
                        'category': entry.category,
                        'content': entry.content,
                        'confidence': entry.confidence,
                        'usage_count': entry.usage_count,
                        'age_days': (datetime.now() - entry.created_date).days
                    })
        
            # Sort by confidence and usage
            insights.sort(key=lambda x: x['confidence'] * (1 + x['usage_count']), reverse=True)
        
            return insights
        except Exception as e:
            logger.error(f"Error in get_knowledge_insights: {e}")
            raise
    
    def apply_knowledge(self, current_conditions: Dict[str, Any]) -> Dict[str, Any]:
        """Apply relevant knowledge to current trading conditions."""
        try:
            applicable_knowledge = []
        
            regime = current_conditions.get('regime', 'unknown')
            strategy = current_conditions.get('strategy', 'unknown')
            confidence = current_conditions.get('confidence', 0.5)
        
            # Find applicable knowledge entries
            for entry in self.knowledge_base.values():
                if entry.confidence < self.min_confidence_threshold:
                    continue
            
                content = entry.content
            
                # Check regime match
                if content.get('regime') == regime:
                    applicable_knowledge.append(entry)
            
                # Check strategy match
                if content.get('strategy') == strategy:
                    applicable_knowledge.append(entry)
            
                # Check confidence level patterns
                if 'confidence_level' in content:
                    if abs(content['confidence_level'] - confidence) < 0.2:
                        applicable_knowledge.append(entry)
        
            # Generate recommendations
            recommendations = {}
        
            for entry in applicable_knowledge:
                content = entry.content
            
                if entry.category == 'losing_patterns':
                    recommendations['risk_adjustment'] = content.get('confidence_adjustment', 0)
                    recommendations['pattern_warning'] = content.get('recommendation', '')
            
                elif entry.category == 'strategy_performance':
                    if content.get('effectiveness') == 'low':
                        recommendations['strategy_warning'] = f"Low effectiveness for {strategy} in {regime}"
                    elif content.get('effectiveness') == 'high':
                        recommendations['strategy_boost'] = f"High effectiveness for {strategy} in {regime}"
            
                # Update usage count
                entry.usage_count += 1
        
            return recommendations
        except Exception as e:
            logger.error(f"Error in apply_knowledge: {e}")
            raise
    
    def get_feedback_summary(self) -> Dict[str, Any]:
        """Get comprehensive feedback system summary."""
        return {
            'active_loops': len([l for l in self.feedback_loops.values() if l.active]),
            'total_triggers': sum(l.trigger_count for l in self.feedback_loops.values()),
            'knowledge_entries': len(self.knowledge_base),
            'performance_buffer_size': len(self.performance_buffer),
            'loop_effectiveness': {
                loop_id: loop.effectiveness_score 
                for loop_id, loop in self.feedback_loops.items()
            },
            'knowledge_categories': list(set(entry.category for entry in self.knowledge_base.values())),
            'recent_insights': self.get_knowledge_insights()[:5]
        }
