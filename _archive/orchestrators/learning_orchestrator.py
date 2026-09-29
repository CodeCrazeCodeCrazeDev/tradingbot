"""
Learning Orchestrator - Master Controller for 2-Hour Autonomous Learning Session

Coordinates all learning components:
- Internet research
- Knowledge building
- Self-testing with evolving difficulty
- Knowledge transfer to bot
- Progress monitoring
"""

import asyncio
import json
import sqlite3
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum, auto
from typing import Any, Dict, List, Optional, Callable
from pathlib import Path
import logging
import time
import hashlib

from .internet_researcher import InternetResearcher, DifficultyLevel, LearningResource
from .knowledge_builder import KnowledgeBuilder, TradingConcept
from .self_tester import SelfTester, TestDifficulty, TestSession
from .knowledge_transfer import KnowledgeTransfer, TransferType
from .learning_monitor import LearningMonitor, LearningPhase

logger = logging.getLogger(__name__)


class LearningMode(Enum):
    """Learning modes"""
    INTENSIVE = auto()  # Fast-paced, aggressive learning
    BALANCED = auto()   # Mix of learning and testing
    THOROUGH = auto()   # Deep understanding, more testing


@dataclass
class LearningSessionConfig:
    """Configuration for a learning session"""
    duration_hours: float = 2.0
    mode: LearningMode = LearningMode.BALANCED
    start_level: int = 1
    target_level: int = 7
    min_accuracy_to_advance: float = 1.0  # 100% required - FULL MASTERY
    tests_per_level: int = 3
    resources_per_topic: int = 3
    auto_transfer: bool = True
    require_all_tests_pass: bool = True  # ALL tests must pass, not just average
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'duration_hours': self.duration_hours,
            'mode': self.mode.name,
            'start_level': self.start_level,
            'target_level': self.target_level,
            'min_accuracy_to_advance': self.min_accuracy_to_advance,
            'tests_per_level': self.tests_per_level,
            'resources_per_topic': self.resources_per_topic,
            'auto_transfer': self.auto_transfer,
            'require_all_tests_pass': self.require_all_tests_pass,
        }


@dataclass
class LearningSessionResult:
    """Result of a learning session"""
    session_id: str
    start_time: datetime
    end_time: datetime
    config: LearningSessionConfig
    final_level: int
    resources_studied: int
    concepts_learned: int
    tests_taken: int
    tests_passed: int
    knowledge_transferred: int
    final_accuracy: float
    evolution_cycles: int
    success: bool
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'session_id': self.session_id,
            'start_time': self.start_time.isoformat(),
            'end_time': self.end_time.isoformat(),
            'duration': str(self.end_time - self.start_time),
            'config': self.config.to_dict(),
            'final_level': self.final_level,
            'resources_studied': self.resources_studied,
            'concepts_learned': self.concepts_learned,
            'tests_taken': self.tests_taken,
            'tests_passed': self.tests_passed,
            'knowledge_transferred': self.knowledge_transferred,
            'final_accuracy': self.final_accuracy,
            'evolution_cycles': self.evolution_cycles,
            'success': self.success,
        }


class LearningOrchestrator:
    """
    Master orchestrator for autonomous learning sessions.
    
    Runs a complete learning cycle:
    1. Research topics from internet
    2. Build structured knowledge
    3. Test understanding (easy -> super hard)
    4. Transfer knowledge to bot
    5. Evolve and improve
    """
    
    def __init__(self, data_dir: str = "autonomous_learner_data"):
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        
        # Initialize components
        self.researcher = InternetResearcher(str(self.data_dir))
        self.knowledge_builder = KnowledgeBuilder(str(self.data_dir))
        self.tester = SelfTester(str(self.data_dir))
        self.transfer = KnowledgeTransfer(str(self.data_dir))
        self.monitor = LearningMonitor(str(self.data_dir))
        
        self.session_id: Optional[str] = None
        self.config: Optional[LearningSessionConfig] = None
        self.is_running = False
        self.should_stop = False
        
        # Progress tracking
        self.current_level = 1
        self.evolution_cycles = 0
        
        logger.info("LearningOrchestrator initialized")
    
    async def run_learning_session(self, config: LearningSessionConfig = None) -> LearningSessionResult:
        """Run a complete learning session"""
        if config is None:
            config = LearningSessionConfig()
        
        self.config = config
        self.session_id = hashlib.md5(f"{datetime.now().isoformat()}".encode()).hexdigest()[:12]
        self.is_running = True
        self.should_stop = False
        self.current_level = config.start_level
        
        start_time = datetime.now()
        end_time = start_time + timedelta(hours=config.duration_hours)
        
        logger.info(f"Starting {config.duration_hours}-hour learning session")
        logger.info(f"Session ID: {self.session_id}")
        logger.info(f"Target: Level {config.start_level} -> Level {config.target_level}")
        
        self.monitor.transition_phase(LearningPhase.INITIALIZATION, "Session started")
        
        try:
            # Main learning loop
            while datetime.now() < end_time and not self.should_stop:
                remaining = (end_time - datetime.now()).total_seconds() / 3600
                logger.info(f"Time remaining: {remaining:.2f} hours")
                
                # Phase 1: Research and Learn
                await self._learning_phase()
                
                if self.should_stop or datetime.now() >= end_time:
                    break
                
                # Phase 2: Test Understanding
                await self._testing_phase()
                
                if self.should_stop or datetime.now() >= end_time:
                    break
                
                # Phase 3: Transfer Knowledge
                await self._transfer_phase()
                
                if self.should_stop or datetime.now() >= end_time:
                    break
                
                # Phase 4: Evolve
                await self._evolution_phase()
                
                # Print status
                self.monitor.print_status()
                
                # Check if we've reached target - but continue learning to reinforce
                if self.current_level >= config.target_level:
                    logger.info("Target level reached! Continuing to reinforce learning...")
                    # Don't break - continue learning and testing to reinforce knowledge
                
                # Small delay between cycles
                await asyncio.sleep(1)
            
        except Exception as e:
            logger.error(f"Learning session error: {e}")
            raise
        finally:
            self.is_running = False
            await self.researcher.close()
        
        # Generate result
        actual_end_time = datetime.now()
        metrics = self.monitor.metrics
        
        result = LearningSessionResult(
            session_id=self.session_id,
            start_time=start_time,
            end_time=actual_end_time,
            config=config,
            final_level=self.current_level,
            resources_studied=metrics.resources_studied,
            concepts_learned=metrics.concepts_learned,
            tests_taken=metrics.tests_taken,
            tests_passed=metrics.tests_passed,
            knowledge_transferred=metrics.transfers_completed,
            final_accuracy=sum(metrics.accuracy_trend[-5:]) / 5 if len(metrics.accuracy_trend) >= 5 else 0,
            evolution_cycles=self.evolution_cycles,
            success=self.current_level >= config.target_level,
        )
        
        # Save result
        self._save_session_result(result)
        
        logger.info("="*60)
        logger.info("LEARNING SESSION COMPLETE")
        logger.info(f"Final Level: {result.final_level}")
        logger.info(f"Concepts Learned: {result.concepts_learned}")
        logger.info(f"Tests Passed: {result.tests_passed}/{result.tests_taken}")
        logger.info(f"Knowledge Transferred: {result.knowledge_transferred}")
        logger.info("="*60)
        
        return result
    
    async def _learning_phase(self):
        """Phase 1: Research and learn from internet"""
        self.monitor.transition_phase(
            LearningPhase.BASIC_LEARNING if self.current_level <= 2 
            else LearningPhase.INTERMEDIATE_LEARNING if self.current_level <= 4
            else LearningPhase.ADVANCED_LEARNING,
            f"Learning at level {self.current_level}"
        )
        
        # Map current level to difficulty
        difficulty_map = {
            1: DifficultyLevel.BEGINNER,
            2: DifficultyLevel.ELEMENTARY,
            3: DifficultyLevel.INTERMEDIATE,
            4: DifficultyLevel.UPPER_INTERMEDIATE,
            5: DifficultyLevel.ADVANCED,
            6: DifficultyLevel.EXPERT,
            7: DifficultyLevel.MASTER,
        }
        
        difficulty = difficulty_map.get(self.current_level, DifficultyLevel.BEGINNER)
        
        logger.info(f"📚 Learning Phase: {difficulty.name}")
        
        try:
            # Research topics at current level
            result = await self.researcher.learn_curriculum_level(difficulty)
            
            self.monitor.log_event('resource_studied', {
                'level': difficulty.name,
                'resources': result['resources_found'],
            })
            
            # Study concepts from knowledge builder
            concepts = self.knowledge_builder.get_concepts_by_level(self.current_level)
            for concept in concepts[:5]:  # Study up to 5 concepts
                study_result = self.knowledge_builder.study_concept(concept.id)
                self.monitor.log_event('concept_learned', {
                    'concept': concept.name,
                    'mastery': study_result.get('mastery_score', 0),
                })
            
            logger.info(f"Studied {result['resources_found']} resources, {len(concepts)} concepts")
            
        except Exception as e:
            logger.error(f"Learning phase error: {e}")
            # Continue with built-in knowledge
            concepts = self.knowledge_builder.get_concepts_by_level(self.current_level)
            for concept in concepts[:5]:
                self.knowledge_builder.study_concept(concept.id)
                self.monitor.log_event('concept_learned', {
                    'concept': concept.name,
                    'mastery': 0.5,
                })
    
    async def _testing_phase(self):
        """Phase 2: Test understanding with evolving difficulty"""
        self.monitor.transition_phase(LearningPhase.TESTING, "Testing knowledge")
        
        # Map current level to test difficulty
        test_difficulty_map = {
            1: TestDifficulty.EASY,
            2: TestDifficulty.MEDIUM,
            3: TestDifficulty.HARD,
            4: TestDifficulty.VERY_HARD,
            5: TestDifficulty.EXPERT,
            6: TestDifficulty.MASTER,
            7: TestDifficulty.SUPER_HARD,
        }
        
        test_difficulty = test_difficulty_map.get(self.current_level, TestDifficulty.EASY)
        
        logger.info(f"📝 Testing Phase: {test_difficulty.name}")
        
        # Take multiple tests at current level - MUST PASS ALL WITH 100%
        passed_tests = 0
        total_score = 0
        all_perfect = True  # Track if ALL tests are 100%
        
        for i in range(self.config.tests_per_level):
            session = self.tester.take_test(test_difficulty, num_questions=5)
            
            self.monitor.log_event('test_completed', {
                'difficulty': test_difficulty.name,
                'score': session.score,
                'passed': session.passed,
                'attempt': i + 1,
            })
            
            total_score += session.score
            if session.passed and session.score >= 1.0:  # Must be 100%
                passed_tests += 1
            else:
                all_perfect = False
            
            if session.score >= 1.0:
                logger.info(f"Test {i+1}: Score {session.score:.1%} - PERFECT! [100%]")
            else:
                logger.info(f"Test {i+1}: Score {session.score:.1%} - FAILED (Need 100%)")
            
            await asyncio.sleep(0.5)
        
        avg_score = total_score / self.config.tests_per_level
        
        # STRICT ADVANCEMENT: ALL tests must be 100% to advance
        # Both conditions must be met:
        # 1. Average score must be 100% (min_accuracy_to_advance)
        # 2. ALL individual tests must pass with 100% (require_all_tests_pass)
        can_advance = (
            avg_score >= self.config.min_accuracy_to_advance and
            (not self.config.require_all_tests_pass or all_perfect)
        )
        
        if can_advance:
            self.current_level = min(self.current_level + 1, 7)
            self.monitor.log_event('level_advanced', {
                'level': self.current_level,
                'avg_score': avg_score,
                'all_tests_perfect': all_perfect,
            })
            logger.info(f"[MASTERY ACHIEVED] Advanced to Level {self.current_level}! All tests passed with 100%!")
        else:
            # Identify gaps - need more study
            gaps = self.tester.get_knowledge_gaps()
            for gap in gaps[:3]:
                self.monitor.log_event('gap_identified', {
                    'topic': gap['topic'],
                    'accuracy': gap['accuracy'],
                })
            logger.info(f"[MASTERY NOT ACHIEVED] Need 100% on ALL tests. Current: {avg_score:.1%} avg, {passed_tests}/{self.config.tests_per_level} perfect")
    
    async def _transfer_phase(self):
        """Phase 3: Transfer learned knowledge to the bot"""
        self.monitor.transition_phase(LearningPhase.KNOWLEDGE_TRANSFER, "Transferring knowledge")
        
        logger.info("🔄 Transfer Phase")
        
        if not self.config.auto_transfer:
            logger.info("Auto-transfer disabled, skipping")
            return
        
        # Get concepts ready for transfer
        concepts = self.knowledge_builder.get_concepts_by_level(self.current_level)
        
        transfers_created = 0
        for concept in concepts[:3]:  # Transfer up to 3 concepts per cycle
            # Determine transfer type based on category
            if 'indicator' in concept.category.name.lower():
                transfer = self.transfer.create_indicator_transfer(
                    concept.id, 
                    {
                        'description': concept.description,
                        'code_template': concept.code_template,
                        'sources': concept.sources,
                    }
                )
            elif 'risk' in concept.category.name.lower():
                transfer = self.transfer.create_risk_rule_transfer(
                    concept.id,
                    {
                        'description': concept.description,
                        'code_template': concept.code_template,
                        'sources': concept.sources,
                    }
                )
            else:
                transfer = self.transfer.create_strategy_transfer(
                    concept.id,
                    {
                        'description': concept.description,
                        'sources': concept.sources,
                    }
                )
            
            # Validate and execute transfer
            if self.transfer.validate_transfer(transfer):
                if self.transfer.execute_transfer(transfer):
                    transfers_created += 1
                    self.monitor.log_event('transfer_completed', {
                        'name': transfer.name,
                        'type': transfer.transfer_type.name,
                    })
        
        logger.info(f"Transferred {transfers_created} knowledge items to bot")
    
    async def _evolution_phase(self):
        """Phase 4: Evolve and improve learning"""
        self.monitor.transition_phase(LearningPhase.EVOLUTION, "Evolving")
        
        logger.info("🧬 Evolution Phase")
        
        self.evolution_cycles += 1
        
        # Analyze performance and adapt
        stats = self.tester.get_test_statistics()
        gaps = self.tester.get_knowledge_gaps()
        
        # Get recommendations
        recommendations = self.monitor.get_recommendations()
        
        logger.info(f"Evolution cycle {self.evolution_cycles}")
        logger.info(f"Pass rate: {stats.get('pass_rate', 0):.1%}")
        logger.info(f"Knowledge gaps: {len(gaps)}")
        
        for rec in recommendations:
            logger.info(f"  → {rec}")
        
        # Save metrics snapshot
        self.monitor.save_metrics_snapshot()
        
        await asyncio.sleep(0.5)
    
    def _save_session_result(self, result: LearningSessionResult):
        """Save session result to file"""
        result_file = self.data_dir / f"session_{result.session_id}.json"
        with open(result_file, 'w') as f:
            json.dump(result.to_dict(), f, indent=2)
        logger.info(f"Session result saved to {result_file}")
    
    def stop(self):
        """Stop the learning session"""
        self.should_stop = True
        logger.info("Stop requested")
    
    def get_status(self) -> Dict[str, Any]:
        """Get current status"""
        return {
            'is_running': self.is_running,
            'session_id': self.session_id,
            'current_level': self.current_level,
            'evolution_cycles': self.evolution_cycles,
            'progress': self.monitor.get_progress_report() if self.monitor else {},
        }


async def run_2_hour_learning_session():
    """Convenience function to run a 2-hour learning session"""
    config = LearningSessionConfig(
        duration_hours=2.0,
        mode=LearningMode.BALANCED,
        start_level=1,
        target_level=7,
        min_accuracy_to_advance=0.7,
        tests_per_level=3,
        auto_transfer=True,
    )
    
    orchestrator = LearningOrchestrator()
    result = await orchestrator.run_learning_session(config)
    
    return result


def quick_start():
    """Quick start function for running the learning session"""
    return asyncio.run(run_2_hour_learning_session())
