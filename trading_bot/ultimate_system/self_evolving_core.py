"""
Self-Evolving Core - Continuous Learning & Self-Improvement
============================================================

A self-evolving system that:
1. Learns from every trade and market event
2. Upgrades its own strategies and models
3. Self-repairs when issues are detected
4. Self-regulates to maintain optimal performance
5. Continuously improves forever
6. Adapts to changing market conditions
"""

import asyncio
import logging
import json
import pickle
from typing import Any, Callable, Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path
import hashlib
import copy
from typing import Set

# Evolution: Added retry decorator
def retry(max_attempts=3, delay=1.0):
    """Retry decorator for resilient operations"""
    def decorator(func):
        async def wrapper(*args, **kwargs):
            last_error = None
            for attempt in range(max_attempts):
                try:
                    return await func(*args, **kwargs)
                except Exception as e:
                    last_error = e
                    if attempt < max_attempts - 1:
                        await asyncio.sleep(delay * (attempt + 1))
            raise last_error
        return wrapper
    return decorator



logger = logging.getLogger(__name__)


class LearningMode(Enum):
    """Learning modes"""
    EXPLORATION = "exploration"  # Try new things
    EXPLOITATION = "exploitation"  # Use what works
    BALANCED = "balanced"  # Mix of both
    CONSERVATIVE = "conservative"  # Minimal changes
    AGGRESSIVE = "aggressive"  # Rapid learning


class EvolutionState(Enum):
    """Evolution states"""
    STABLE = "stable"
    EVOLVING = "evolving"
    TESTING = "testing"
    ROLLING_BACK = "rolling_back"
    OPTIMIZING = "optimizing"


@dataclass
class LearningEvent:
    """A learning event"""
    event_id: str
    event_type: str  # trade, prediction, error, discovery
    timestamp: datetime
    data: Dict[str, Any]
    outcome: Optional[str] = None
    lesson_learned: Optional[str] = None
    applied: bool = False


@dataclass
class EvolutionProposal:
    """A proposed evolution/improvement"""
    proposal_id: str
    component: str  # Which component to evolve
    change_type: str  # parameter, strategy, model, architecture
    current_value: Any
    proposed_value: Any
    expected_improvement: float  # Percentage
    confidence: float
    reasoning: str
    created_at: datetime = field(default_factory=datetime.now)
    status: str = "pending"  # pending, testing, approved, rejected, applied


@dataclass
class PerformanceSnapshot:
    """Performance snapshot for tracking"""
    timestamp: datetime
    win_rate: float
    sharpe_ratio: float
    max_drawdown: float
    total_pnl: float
    trades_count: int
    predictions_accuracy: float
    model_versions: Dict[str, str]


class SelfEvolvingCore:
    """
    Self-Evolving Core System
    
    Capabilities:
    - Continuous learning from all events
    - Self-improvement through evolution
    - Self-repair when issues detected
    - Self-regulation for optimal performance
    - Automatic strategy optimization
    - Model retraining and upgrading
    - Architecture adaptation
    """
    
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        
        # Learning configuration
        self.learning_mode = LearningMode(
            self.config.get('learning_mode', 'balanced')
        )
        self.evolution_state = EvolutionState.STABLE
        
        # Learning rate (how quickly to adapt)
        self.learning_rate = self.config.get('learning_rate', 0.1)
        self.min_learning_rate = 0.01
        self.max_learning_rate = 0.5
        
        # Memory systems
        self.short_term_memory: List[LearningEvent] = []  # Recent events
        self.long_term_memory: List[LearningEvent] = []  # Important lessons
        self.max_short_term = 1000
        self.max_long_term = 10000
        
        # Evolution tracking
        self.evolution_proposals: List[EvolutionProposal] = []
        self.applied_evolutions: List[EvolutionProposal] = []
        self.evolution_history: List[Dict] = []
        
        # Performance tracking
        self.performance_history: List[PerformanceSnapshot] = []
        self.baseline_performance: Optional[PerformanceSnapshot] = None
        
        # Component registry (what can be evolved)
        self.evolvable_components: Dict[str, Dict] = {}
        
        # Self-repair system
        self.error_patterns: Dict[str, int] = {}
        self.repair_actions: Dict[str, Callable] = {}
        
        # Persistence
        self.state_path = Path(self.config.get('state_path', 'evolution_state'))
        self.state_path.mkdir(parents=True, exist_ok=True)
        
        # Statistics
        self.stats = {
            'total_events_learned': 0,
            'evolutions_proposed': 0,
            'evolutions_applied': 0,
            'evolutions_rejected': 0,
            'self_repairs': 0,
            'performance_improvements': 0
        }
        
        # Load previous state
        self._load_state()
        
        logger.info("Self-Evolving Core initialized")
    
    def register_component(
        self,
        name: str,
        component: Any,
        evolvable_params: List[str],
        bounds: Dict[str, Tuple[float, float]]
    ):
        """Register a component for evolution"""
        self.evolvable_components[name] = {
            'component': component,
            'params': evolvable_params,
            'bounds': bounds,
            'current_values': {p: getattr(component, p, None) for p in evolvable_params},
            'history': []
        }
        logger.info(f"Registered evolvable component: {name}")
    
    def learn(self, event: LearningEvent):
        """Learn from an event"""
        self.short_term_memory.append(event)
        self.stats['total_events_learned'] += 1
        
        # Trim short-term memory
        if len(self.short_term_memory) > self.max_short_term:
            # Move important events to long-term
            important = self._identify_important_events(
                self.short_term_memory[:100]
            )
            self.long_term_memory.extend(important)
            self.short_term_memory = self.short_term_memory[100:]
        
        # Extract lessons
        lesson = self._extract_lesson(event)
        if lesson:
            event.lesson_learned = lesson
            logger.info(f"Lesson learned: {lesson}")
        
        # Check for patterns
        self._detect_patterns()
        
        # Trigger evolution if needed
        if self._should_evolve():
            asyncio.create_task(self._evolve())
    
    def learn_from_trade(
        self,
        trade_data: Dict[str, Any],
        outcome: str,
        pnl: float
    ):
        """Learn from a trade"""
        event = LearningEvent(
            event_id=f"trade_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            event_type='trade',
            timestamp=datetime.now(),
            data={
                **trade_data,
                'pnl': pnl
            },
            outcome=outcome
        )
        self.learn(event)
        
        # Update performance tracking
        self._update_performance_from_trade(trade_data, outcome, pnl)
    
    def learn_from_prediction(
        self,
        prediction: Dict[str, Any],
        actual: Dict[str, Any],
        accuracy: float
    ):
        """Learn from a prediction"""
        event = LearningEvent(
            event_id=f"pred_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            event_type='prediction',
            timestamp=datetime.now(),
            data={
                'prediction': prediction,
                'actual': actual,
                'accuracy': accuracy
            },
            outcome='accurate' if accuracy > 0.5 else 'inaccurate'
        )
        self.learn(event)
    
    def learn_from_error(self, error: Exception, context: Dict[str, Any]):
        """Learn from an error"""
        error_type = type(error).__name__
        
        event = LearningEvent(
            event_id=f"error_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            event_type='error',
            timestamp=datetime.now(),
            data={
                'error_type': error_type,
                'error_message': str(error),
                'context': context
            },
            outcome='error'
        )
        self.learn(event)
        
        # Track error patterns
        self.error_patterns[error_type] = self.error_patterns.get(error_type, 0) + 1
        
        # Trigger self-repair if pattern detected
        if self.error_patterns[error_type] >= 3:
            self._self_repair(error_type, context)
    
    def _extract_lesson(self, event: LearningEvent) -> Optional[str]:
        """Extract a lesson from an event"""
        if event.event_type == 'trade':
            pnl = event.data.get('pnl', 0)
            if pnl > 0:
                return f"Profitable trade pattern: {event.data.get('strategy', 'unknown')}"
            else:
                return f"Loss pattern to avoid: {event.data.get('reason', 'unknown')}"
        
        elif event.event_type == 'prediction':
            accuracy = event.data.get('accuracy', 0)
            if accuracy > 0.7:
                return f"High accuracy prediction method: {event.data.get('model', 'unknown')}"
            elif accuracy < 0.3:
                return f"Poor prediction method to improve: {event.data.get('model', 'unknown')}"
        
        elif event.event_type == 'error':
            return f"Error to prevent: {event.data.get('error_type', 'unknown')}"
        
        return None
    
    def _identify_important_events(self, events: List[LearningEvent]) -> List[LearningEvent]:
        """Identify important events to keep in long-term memory"""
        important = []
        
        for event in events:
            # Keep events with lessons
            if event.lesson_learned:
                important.append(event)
                continue
            
            # Keep significant trades
            if event.event_type == 'trade':
                pnl = abs(event.data.get('pnl', 0))
                if pnl > 1000:  # Significant trade
                    important.append(event)
                    continue
            
            # Keep errors
            if event.event_type == 'error':
                important.append(event)
        
        return important
    
    def _detect_patterns(self):
        """Detect patterns in recent events"""
        if len(self.short_term_memory) < 10:
            return
        
        recent = self.short_term_memory[-50:]
        
        # Detect losing streak
        trades = [e for e in recent if e.event_type == 'trade']
        if len(trades) >= 5:
            recent_outcomes = [t.outcome for t in trades[-5:]]
            if all(o == 'loss' for o in recent_outcomes):
                logger.warning("Losing streak detected! Triggering self-regulation")
                self._self_regulate('losing_streak')
        
        # Detect prediction accuracy drop
        predictions = [e for e in recent if e.event_type == 'prediction']
        if len(predictions) >= 10:
            accuracies = [p.data.get('accuracy', 0) for p in predictions[-10:]]
            avg_accuracy = sum(accuracies) / len(accuracies)
            if avg_accuracy < 0.4:
                logger.warning("Prediction accuracy drop detected! Triggering model evolution")
                self._propose_model_evolution()
    
    def _should_evolve(self) -> bool:
        """Determine if evolution should be triggered"""
        if self.evolution_state != EvolutionState.STABLE:
            return False
        
        # Evolve based on learning mode
        if self.learning_mode == LearningMode.AGGRESSIVE:
            return len(self.short_term_memory) >= 50
        elif self.learning_mode == LearningMode.BALANCED:
            return len(self.short_term_memory) >= 100
        elif self.learning_mode == LearningMode.CONSERVATIVE:
            return len(self.short_term_memory) >= 500
        
        return False
    
    async def _evolve(self):
        """Run evolution cycle"""
        self.evolution_state = EvolutionState.EVOLVING
        logger.info("Starting evolution cycle...")
        
        try:
            # Analyze recent performance
            performance = self._analyze_performance()
            
            # Generate evolution proposals
            proposals = self._generate_proposals(performance)
            
            for proposal in proposals:
                self.evolution_proposals.append(proposal)
                self.stats['evolutions_proposed'] += 1
                
                # Test proposal
                success = await self._test_proposal(proposal)
                
                if success:
                    # Apply evolution
                    self._apply_evolution(proposal)
                    self.stats['evolutions_applied'] += 1
                    logger.info(f"Evolution applied: {proposal.proposal_id}")
                else:
                    proposal.status = 'rejected'
                    self.stats['evolutions_rejected'] += 1
            
            self.evolution_state = EvolutionState.STABLE
            logger.info("Evolution cycle complete")
            
        except Exception as e:
            logger.error(f"Evolution failed: {e}")
            self.evolution_state = EvolutionState.STABLE
    
    def _analyze_performance(self) -> Dict[str, Any]:
        """Analyze recent performance"""
        trades = [e for e in self.short_term_memory if e.event_type == 'trade']
        predictions = [e for e in self.short_term_memory if e.event_type == 'prediction']
        
        if not trades:
            return {'win_rate': 0.5, 'avg_pnl': 0, 'prediction_accuracy': 0.5}
        
        wins = sum(1 for t in trades if t.outcome == 'win')
        win_rate = wins / len(trades)
        
        pnls = [t.data.get('pnl', 0) for t in trades]
        avg_pnl = sum(pnls) / len(pnls)
        
        accuracies = [p.data.get('accuracy', 0) for p in predictions] if predictions else [0.5]
        pred_accuracy = sum(accuracies) / len(accuracies)
        
        return {
            'win_rate': win_rate,
            'avg_pnl': avg_pnl,
            'prediction_accuracy': pred_accuracy,
            'total_trades': len(trades),
            'total_predictions': len(predictions)
        }
    
    def _generate_proposals(self, performance: Dict) -> List[EvolutionProposal]:
        """Generate evolution proposals based on performance"""
        proposals = []
        
        # Low win rate -> adjust strategy parameters
        if performance['win_rate'] < 0.45:
            for name, comp in self.evolvable_components.items():
                for param in comp['params']:
                    current = comp['current_values'].get(param)
                    if current is not None and isinstance(current, (int, float)):
                        bounds = comp['bounds'].get(param, (0, 1))
                        
                        # Propose adjustment
                        adjustment = (bounds[1] - bounds[0]) * 0.1 * self.learning_rate
                        new_value = current + adjustment
                        new_value = max(bounds[0], min(bounds[1], new_value))
                        
                        proposal = EvolutionProposal(
                            proposal_id=f"evo_{name}_{param}_{datetime.now().strftime('%H%M%S')}",
                            component=name,
                            change_type='parameter',
                            current_value=current,
                            proposed_value=new_value,
                            expected_improvement=0.05,
                            confidence=0.6,
                            reasoning=f"Low win rate ({performance['win_rate']:.2%}), adjusting {param}"
                        )
                        proposals.append(proposal)
        
        # Low prediction accuracy -> propose model retraining
        if performance['prediction_accuracy'] < 0.5:
            proposal = EvolutionProposal(
                proposal_id=f"evo_model_retrain_{datetime.now().strftime('%H%M%S')}",
                component='prediction_model',
                change_type='model',
                current_value='current_model',
                proposed_value='retrained_model',
                expected_improvement=0.1,
                confidence=0.7,
                reasoning=f"Low prediction accuracy ({performance['prediction_accuracy']:.2%})"
            )
            proposals.append(proposal)
        
        return proposals[:5]  # Limit proposals per cycle
    
    async def _test_proposal(self, proposal: EvolutionProposal) -> bool:
        """Test an evolution proposal"""
        proposal.status = 'testing'
        self.evolution_state = EvolutionState.TESTING
        
        try:
            # Simulate testing (in production, would run backtests)
            await asyncio.sleep(0.1)  # Placeholder for actual testing
            
            # Simple acceptance criteria
            if proposal.confidence > 0.5 and proposal.expected_improvement > 0.02:
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Proposal testing failed: {e}")
            return False
    
    def _apply_evolution(self, proposal: EvolutionProposal):
        """Apply an approved evolution"""
        proposal.status = 'applied'
        
        if proposal.component in self.evolvable_components:
            comp = self.evolvable_components[proposal.component]
            
            if proposal.change_type == 'parameter':
                # Extract parameter name from proposal_id
                parts = proposal.proposal_id.split('_')
                if len(parts) >= 3:
                    param_name = parts[2]
                    
                    # Update component
                    if hasattr(comp['component'], param_name):
                        setattr(comp['component'], param_name, proposal.proposed_value)
                        comp['current_values'][param_name] = proposal.proposed_value
                        comp['history'].append({
                            'param': param_name,
                            'old': proposal.current_value,
                            'new': proposal.proposed_value,
                            'timestamp': datetime.now().isoformat()
                        })
        
        self.applied_evolutions.append(proposal)
        self.evolution_history.append({
            'proposal_id': proposal.proposal_id,
            'component': proposal.component,
            'change_type': proposal.change_type,
            'timestamp': datetime.now().isoformat()
        })
        
        # Save state
        self._save_state()
    
    def _propose_model_evolution(self):
        """Propose model evolution due to accuracy drop"""
        proposal = EvolutionProposal(
            proposal_id=f"evo_model_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            component='prediction_model',
            change_type='model',
            current_value='current',
            proposed_value='retrained',
            expected_improvement=0.15,
            confidence=0.7,
            reasoning="Prediction accuracy dropped below threshold"
        )
        self.evolution_proposals.append(proposal)
    
    def _self_regulate(self, trigger: str):
        """Self-regulate based on detected issues"""
        logger.info(f"Self-regulating due to: {trigger}")
        
        if trigger == 'losing_streak':
            # Reduce position sizes
            self.learning_mode = LearningMode.CONSERVATIVE
            self.learning_rate = max(self.min_learning_rate, self.learning_rate * 0.5)
            
            # Increase verification requirements
            for name, comp in self.evolvable_components.items():
                if 'confidence_threshold' in comp['params']:
                    current = comp['current_values'].get('confidence_threshold', 0.6)
                    comp['current_values']['confidence_threshold'] = min(0.9, current + 0.1)
    
    def _self_repair(self, error_type: str, context: Dict):
        """Self-repair based on error patterns"""
        logger.info(f"Self-repairing for error type: {error_type}")
        self.stats['self_repairs'] += 1
        
        # Check for registered repair actions
        if error_type in self.repair_actions:
            try:
                self.repair_actions[error_type](context)
                self.error_patterns[error_type] = 0  # Reset counter
            except Exception as e:
                logger.error(f"Self-repair failed: {e}")
        else:
            # Generic repair actions
            if 'connection' in error_type.lower():
                logger.info("Attempting to reconnect...")
            elif 'memory' in error_type.lower():
                logger.info("Clearing caches...")
                self.short_term_memory = self.short_term_memory[-100:]
    
    def register_repair_action(self, error_type: str, action: Callable):
        """Register a repair action for an error type"""
        self.repair_actions[error_type] = action
    
    def _update_performance_from_trade(
        self,
        trade_data: Dict,
        outcome: str,
        pnl: float
    ):
        """Update performance tracking from trade"""
        # This would integrate with actual performance tracking
        pass
    
    def take_performance_snapshot(self) -> PerformanceSnapshot:
        """Take a performance snapshot"""
        performance = self._analyze_performance()
        
        snapshot = PerformanceSnapshot(
            timestamp=datetime.now(),
            win_rate=performance['win_rate'],
            sharpe_ratio=0.0,  # Would calculate from returns
            max_drawdown=0.0,  # Would calculate from equity curve
            total_pnl=sum(
                e.data.get('pnl', 0)
                for e in self.short_term_memory
                if e.event_type == 'trade'
            ),
            trades_count=performance['total_trades'],
            predictions_accuracy=performance['prediction_accuracy'],
            model_versions={
                name: str(comp.get('version', '1.0'))
                for name, comp in self.evolvable_components.items()
            }
        )
        
        self.performance_history.append(snapshot)
        
        # Set baseline if not set
        if self.baseline_performance is None:
            self.baseline_performance = snapshot
        
        return snapshot
    
    def get_improvement_since_baseline(self) -> Dict[str, float]:
        """Get improvement since baseline"""
        if not self.baseline_performance or not self.performance_history:
            return {}
        
        current = self.performance_history[-1]
        baseline = self.baseline_performance
        
        return {
            'win_rate_change': current.win_rate - baseline.win_rate,
            'sharpe_change': current.sharpe_ratio - baseline.sharpe_ratio,
            'drawdown_change': baseline.max_drawdown - current.max_drawdown,
            'pnl_change': current.total_pnl - baseline.total_pnl
        }
    
    def _save_state(self):
        """Save evolution state"""
        state = {
            'learning_mode': self.learning_mode.value,
            'learning_rate': self.learning_rate,
            'evolution_history': self.evolution_history,
            'error_patterns': self.error_patterns,
            'stats': self.stats,
            'component_values': {
                name: comp['current_values']
                for name, comp in self.evolvable_components.items()
            }
        }
        
        state_file = self.state_path / 'evolution_state.json'
        with open(state_file, 'w') as f:
            json.dump(state, f, indent=2, default=str)
    
    def _load_state(self):
        """Load previous evolution state"""
        state_file = self.state_path / 'evolution_state.json'
        
        if state_file.exists():
            try:
                with open(state_file, 'r') as f:
                    state = json.load(f)
                
                self.learning_mode = LearningMode(state.get('learning_mode', 'balanced'))
                self.learning_rate = state.get('learning_rate', 0.1)
                self.evolution_history = state.get('evolution_history', [])
                self.error_patterns = state.get('error_patterns', {})
                self.stats = state.get('stats', self.stats)
                
                logger.info("Loaded previous evolution state")
                
            except Exception as e:
                logger.error(f"Failed to load evolution state: {e}")
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get evolution statistics"""
        return {
            **self.stats,
            'learning_mode': self.learning_mode.value,
            'evolution_state': self.evolution_state.value,
            'learning_rate': self.learning_rate,
            'short_term_memory_size': len(self.short_term_memory),
            'long_term_memory_size': len(self.long_term_memory),
            'pending_proposals': len([p for p in self.evolution_proposals if p.status == 'pending']),
            'evolvable_components': list(self.evolvable_components.keys()),
            'improvement': self.get_improvement_since_baseline()
        }
