"""
Market Student Orchestrator - Master Controller
================================================

The master controller that coordinates:
- Market Teacher (lessons from the market)
- Student AI (learning and proposing improvements)
- Learning Cycle (continuous feedback loop)
- Lesson Database (persistent knowledge)
- Evolution Engine (safe improvements)
- Reward System (immutable compass)

This is the entry point for the "AI as Student, Market as Teacher" system.

Version: 1.0.0
"""

from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any, Callable, Dict, List, Optional
import logging
import asyncio
import json
from pathlib import Path

from .reward_system import ImmutableRewardSystem, get_reward_system
from .market_teacher import MarketTeacher, MarketLesson, LessonType
from .student_ai import StudentAI, ImprovementProposal, LearningState
from .learning_cycle import AlphaLearningCycle, CyclePhase, CycleResult
from .lesson_database import LessonDatabase, LessonQuery
from .evolution_engine import SafeEvolutionEngine, EvolutionProposal

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


# =============================================================================
# ORCHESTRATOR CONFIG
# =============================================================================

@dataclass
class OrchestratorConfig:
    """Configuration for the Market Student Orchestrator"""
    
    # Mode
    mode: str = 'paper'  # 'paper', 'live', 'backtest'
    
    # Storage
    storage_path: str = 'market_student_data'
    
    # Learning
    cycle_interval_seconds: int = 60
    auto_learn: bool = True
    min_confidence_threshold: float = 0.6
    
    # Evolution
    auto_propose: bool = True
    require_approval: bool = True
    max_proposals_per_day: int = 10
    
    # Database
    db_path: str = 'market_student_data/lessons.db'
    
    # Logging
    log_level: str = 'INFO'


# =============================================================================
# MARKET STUDENT ORCHESTRATOR
# =============================================================================

class MarketStudentOrchestrator:
    """
    Master orchestrator for the Market Student system.
    
    Coordinates all components:
    - Observes market through MarketTeacher
    - Learns through StudentAI
    - Runs continuous learning cycles
    - Stores lessons in database
    - Manages safe evolution
    - Enforces reward system
    
    The AI learns from every market movement, proposes improvements,
    but NEVER implements changes without human approval.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = OrchestratorConfig(**config) if config else OrchestratorConfig()
        
        # Initialize storage
        self._storage_path = Path(self.config.storage_path)
        self._storage_path.mkdir(parents=True, exist_ok=True)
        
        # Initialize components
        self._reward_system = get_reward_system()
        
        self._teacher = MarketTeacher({
            'volatility_threshold': 1.5,
            'volume_threshold': 2.0,
        })
        
        self._student = StudentAI({
            'storage_path': str(self._storage_path / 'student'),
        })
        
        self._learning_cycle = AlphaLearningCycle(
            market_teacher=self._teacher,
            student_ai=self._student,
            config={
                'cycle_interval_seconds': self.config.cycle_interval_seconds,
            }
        )
        
        self._lesson_db = LessonDatabase({
            'db_path': self.config.db_path,
        })
        
        self._evolution_engine = SafeEvolutionEngine({
            'backup_path': str(self._storage_path / 'backups'),
        })
        
        # Running state
        self._is_running = False
        self._background_tasks: List[asyncio.Task] = []
        
        # Statistics
        self._stats = {
            'started_at': None,
            'total_cycles': 0,
            'total_lessons': 0,
            'total_proposals': 0,
            'total_evolutions': 0,
        }
        
        logger.info("MarketStudentOrchestrator initialized")
        logger.info(f"  Storage: {self._storage_path}")
        logger.info(f"  Auto-learn: {self.config.auto_learn}")
        logger.info(f"  Require approval: {self.config.require_approval}")
    
    async def start(self):
        """Start the Market Student system"""
        if self._is_running:
            logger.warning("System already running")
            return
        
        self._is_running = True
        self._stats['started_at'] = datetime.now()
        
        logger.info("Starting Market Student system...")
        
        # Start background tasks
        if self.config.auto_learn:
            task = asyncio.create_task(self._continuous_learning_loop())
            self._background_tasks.append(task)
        
        logger.info("Market Student system started")
    
    async def stop(self):
        """Stop the Market Student system"""
        if not self._is_running:
            return
        
        self._is_running = False
        
        # Cancel background tasks
        for task in self._background_tasks:
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass
        
        self._background_tasks.clear()
        
        # Save state
        self._student.save_state()
        
        logger.info("Market Student system stopped")
    
    async def process_market_data(
        self,
        symbol: str,
        market_data: Dict[str, Any],
        signal: Optional[Dict[str, Any]] = None,
        trade_result: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Process market data through the learning system.
        
        This is the main entry point for feeding data to the system.
        
        Args:
            symbol: Trading symbol
            market_data: OHLCV and indicator data
            signal: Signal that was generated (if any)
            trade_result: Result of trade (if any)
            
        Returns:
            Processing result with lessons and proposals
        """
        result = {
            'symbol': symbol,
            'timestamp': datetime.now().isoformat(),
            'lessons': [],
            'insights': [],
            'proposals': [],
            'cycle_result': None,
        }
        
        try:
            # Run learning cycle
            cycle_result = await self._learning_cycle.run_cycle(
                symbol=symbol,
                market_data=market_data,
                signal=signal,
                trade_result=trade_result
            )
            
            result['cycle_result'] = cycle_result.to_dict()
            result['lessons'] = cycle_result.lessons_extracted
            result['proposals'] = cycle_result.proposals_generated
            
            self._stats['total_cycles'] += 1
            self._stats['total_lessons'] += len(cycle_result.lessons_extracted)
            self._stats['total_proposals'] += len(cycle_result.proposals_generated)
            
            # Store lessons in database
            for lesson in self._teacher.get_recent_lessons(limit=10):
                self._lesson_db.store_lesson(lesson)
            
            # Get actionable insights
            result['insights'] = self._teacher.get_actionable_insights(limit=5)
            
            # Create evolutions for high-priority proposals
            for proposal in self._student.get_pending_proposals():
                if proposal.priority in ['critical', 'high']:
                    evolution = self._evolution_engine.create_evolution(proposal)
                    self._evolution_engine.validate_evolution(evolution.evolution_id)
                    self._stats['total_evolutions'] += 1
            
        except Exception as e:
            logger.error(f"Error processing market data: {e}", exc_info=True)
            result['error'] = str(e)
        
        return result
    
    async def process_trade_outcome(
        self,
        symbol: str,
        trade: Dict[str, Any],
        market_data: Dict[str, Any],
        signal: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Process a trade outcome for learning.
        
        Args:
            symbol: Trading symbol
            trade: Trade data (entry, exit, pnl, etc.)
            market_data: Market data at trade time
            signal: The signal that triggered the trade
            
        Returns:
            Learning result
        """
        result = {
            'symbol': symbol,
            'trade_id': trade.get('id'),
            'pnl': trade.get('pnl', 0),
            'lessons': [],
            'insights': [],
        }
        
        try:
            # Get lessons from the trade
            lessons = self._teacher.observe_trade_outcome(
                symbol=symbol,
                trade=trade,
                market_data=market_data,
                signal=signal
            )
            
            # Learn from each lesson
            for lesson in lessons:
                learning_result = self._student.learn_from_lesson(lesson)
                self._lesson_db.store_lesson(lesson)
                result['lessons'].append(lesson.lesson_id)
            
            # Get insights
            result['insights'] = [l.actionable_insight for l in lessons]
            
            # Evaluate against reward system
            rewards, penalties = self._reward_system.evaluate_behavior(
                'trade',
                {
                    'pnl': trade.get('pnl', 0),
                    'risk_taken': trade.get('risk', 0),
                    'slippage': trade.get('slippage', 0),
                    'execution_time_ms': trade.get('execution_time_ms', 0),
                }
            )
            
            result['reward_score'] = sum(r.magnitude for r in rewards)
            result['penalty_score'] = sum(p.magnitude for p in penalties)
            
        except Exception as e:
            logger.error(f"Error processing trade outcome: {e}", exc_info=True)
            result['error'] = str(e)
        
        return result
    
    def get_pending_proposals(self) -> List[Dict[str, Any]]:
        """Get all pending improvement proposals"""
        proposals = self._student.get_pending_proposals()
        return [p.to_dict() for p in proposals]
    
    def get_pending_evolutions(self) -> List[Dict[str, Any]]:
        """Get all pending evolutions"""
        evolutions = self._evolution_engine.get_pending_evolutions()
        return [e.to_dict() for e in evolutions]
    
    def approve_proposal(self, proposal_id: str, approver: str, notes: Optional[str] = None) -> bool:
        """
        Approve an improvement proposal (HUMAN ACTION).
        
        Args:
            proposal_id: ID of the proposal
            approver: Name of the human approver
            notes: Optional notes
            
        Returns:
            True if approved successfully
        """
        return self._student.approve_proposal(proposal_id, approver, notes)
    
    def reject_proposal(self, proposal_id: str, reason: str) -> bool:
        """
        Reject an improvement proposal (HUMAN ACTION).
        
        Args:
            proposal_id: ID of the proposal
            reason: Reason for rejection
            
        Returns:
            True if rejected successfully
        """
        return self._student.reject_proposal(proposal_id, reason)
    
    def approve_evolution(self, evolution_id: str, approver: str) -> bool:
        """
        Approve an evolution for implementation (HUMAN ACTION).
        
        Args:
            evolution_id: ID of the evolution
            approver: Name of the human approver
            
        Returns:
            True if approved successfully
        """
        return self._evolution_engine.approve_evolution(evolution_id, approver)
    
    def implement_evolution(self, evolution_id: str) -> Dict[str, Any]:
        """
        Implement an approved evolution.
        
        Args:
            evolution_id: ID of the evolution
            
        Returns:
            Implementation result
        """
        return self._evolution_engine.implement_evolution(evolution_id)
    
    def get_learning_state(self) -> Dict[str, Any]:
        """Get current learning state"""
        return self._student.get_learning_summary()
    
    def get_lesson_statistics(self) -> Dict[str, Any]:
        """Get lesson database statistics"""
        return self._lesson_db.get_statistics()
    
    def get_recent_lessons(self, limit: int = 20) -> List[Dict[str, Any]]:
        """Get recent lessons"""
        lessons = self._lesson_db.get_recent_lessons(hours=24, limit=limit)
        return [
            {
                'lesson_id': l.lesson_id,
                'lesson_type': l.lesson_type,
                'severity': l.severity,
                'description': l.description,
                'lesson_learned': l.lesson_learned,
                'actionable_insight': l.actionable_insight,
                'confidence': l.confidence,
                'impact_score': l.impact_score,
                'symbol': l.symbol,
                'timestamp': l.timestamp.isoformat(),
            }
            for l in lessons
        ]
    
    def get_high_impact_lessons(self, min_impact: float = 0.7) -> List[Dict[str, Any]]:
        """Get high-impact lessons"""
        lessons = self._lesson_db.get_high_impact_lessons(min_impact=min_impact)
        return [
            {
                'lesson_id': l.lesson_id,
                'lesson_type': l.lesson_type,
                'lesson_learned': l.lesson_learned,
                'actionable_insight': l.actionable_insight,
                'impact_score': l.impact_score,
            }
            for l in lessons
        ]
    
    def get_active_weaknesses(self) -> List[Dict[str, Any]]:
        """Get active system weaknesses"""
        return self._lesson_db.get_active_weaknesses()
    
    def get_reward_status(self) -> Dict[str, Any]:
        """Get reward system status"""
        return self._reward_system.get_status()
    
    def get_risk_limits(self) -> Dict[str, float]:
        """Get immutable risk limits"""
        return self._reward_system.get_risk_limits()
    
    def get_system_status(self) -> Dict[str, Any]:
        """Get complete system status"""
        return {
            'is_running': self._is_running,
            'started_at': self._stats['started_at'].isoformat() if self._stats['started_at'] else None,
            'uptime_seconds': (
                (datetime.now() - self._stats['started_at']).total_seconds()
                if self._stats['started_at'] else 0
            ),
            'statistics': self._stats,
            'learning_state': self._student.get_learning_state().to_dict(),
            'cycle_statistics': self._learning_cycle.get_cycle_statistics(),
            'lesson_statistics': self._lesson_db.get_statistics(),
            'evolution_statistics': self._evolution_engine.get_statistics(),
            'reward_status': self._reward_system.get_status(),
            'pending_proposals': len(self._student.get_pending_proposals()),
            'pending_evolutions': len(self._evolution_engine.get_pending_evolutions()),
        }
    
    async def _continuous_learning_loop(self):
        """Background loop for continuous learning"""
        logger.info("Starting continuous learning loop")
        
        while self._is_running:
            try:
                # In a real implementation, this would get live market data
                # For now, we just wait for the next cycle
                await asyncio.sleep(self.config.cycle_interval_seconds)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in continuous learning loop: {e}")
                await asyncio.sleep(5)
        
        logger.info("Continuous learning loop stopped")
    
    def export_knowledge(self, filepath: str):
        """Export all learned knowledge to a file"""
        self._lesson_db.export_lessons(filepath)
        logger.info(f"Knowledge exported to {filepath}")
    
    def get_actionable_insights(self, limit: int = 10) -> List[str]:
        """Get top actionable insights"""
        return self._teacher.get_actionable_insights(limit=limit)


# =============================================================================
# QUICK START
# =============================================================================

async def quick_start(config: Optional[Dict[str, Any]] = None) -> MarketStudentOrchestrator:
    """
    Quick start the Market Student system.
    
    Args:
        config: Optional configuration
        
    Returns:
        Running MarketStudentOrchestrator
    """
    orchestrator = MarketStudentOrchestrator(config)
    await orchestrator.start()
    return orchestrator


# =============================================================================
# EXAMPLE USAGE
# =============================================================================

async def main():
    """Example usage of the Market Student system"""
    
    print("=" * 60)
    logger.info("MARKET STUDENT SYSTEM")
    logger.info("AI becomes the student, Market becomes the teacher")
    print("=" * 60)
    
    # Initialize
    orchestrator = await quick_start({
        'auto_learn': True,
        'require_approval': True,
    })
    
    # Simulate market data
    market_data = {
        'open': [100, 101, 102, 103, 104],
        'high': [101, 102, 103, 104, 105],
        'low': [99, 100, 101, 102, 103],
        'close': [100.5, 101.5, 102.5, 103.5, 104.5],
        'volume': [1000, 1200, 1100, 1300, 1500],
        'indicators': {
            'atr': [1.0, 1.1, 1.2, 1.3, 1.4],
            'rsi': [50, 55, 60, 65, 70],
        },
        'regime': 'trending',
        'volatility': 'normal',
    }
    
    # Simulate a signal
    signal = {
        'direction': 'long',
        'confidence': 0.75,
        'entry_price': 104.5,
        'stop_loss': 102.5,
        'take_profit': 108.5,
    }
    
    # Process market data
    logger.info("\n1. Processing market data...")
    result = await orchestrator.process_market_data(
        symbol='EURUSD',
        market_data=market_data,
        signal=signal
    )
    logger.info(f"   Lessons extracted: {len(result['lessons'])}")
    logger.info(f"   Insights: {result['insights'][:2]}")
    
    # Simulate a losing trade
    logger.info("\n2. Processing losing trade...")
    trade_result = {
        'id': 'trade_001',
        'pnl': -50,
        'risk': 0.02,
        'slippage': 0.001,
        'stop_hit': True,
        'signal_confidence': 0.75,
    }
    
    trade_learning = await orchestrator.process_trade_outcome(
        symbol='EURUSD',
        trade=trade_result,
        market_data=market_data,
        signal=signal
    )
    logger.info(f"   Lessons: {trade_learning['lessons']}")
    logger.info(f"   Insights: {trade_learning['insights']}")
    
    # Check pending proposals
    logger.info("\n3. Checking pending proposals...")
    proposals = orchestrator.get_pending_proposals()
    logger.info(f"   Pending proposals: {len(proposals)}")
    for p in proposals[:3]:
        logger.info(f"   - {p['title']}")
    
    # Get system status
    logger.info("\n4. System status...")
    status = orchestrator.get_system_status()
    logger.info(f"   Total cycles: {status['statistics']['total_cycles']}")
    logger.info(f"   Total lessons: {status['statistics']['total_lessons']}")
    logger.info(f"   Reward score: {status['reward_status']['cumulative_score']:.2f}")
    
    # Get risk limits (immutable)
    logger.info("\n5. Risk limits (IMMUTABLE)...")
    limits = orchestrator.get_risk_limits()
    for key, value in limits.items():
        logger.info(f"   {key}: {value}")
    
    # Stop
    await orchestrator.stop()
    print("\n" + "=" * 60)
    logger.info("Market Student system stopped")
    print("=" * 60)


if __name__ == '__main__':
    asyncio.run(main())
