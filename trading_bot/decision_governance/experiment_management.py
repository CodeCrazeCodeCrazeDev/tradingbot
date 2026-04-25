"""
Experiment Management System for Decision Validation
====================================================

Manages controlled experiments for validating decision strategies.
Implements multi-stage evaluation pipeline with resource management.

Features:
- Multi-stage evaluation (exploration → verification → validation)
- Resource and time limits
- Parallel execution management
- Result persistence and analysis
- A/B testing framework
- Bandit-style adaptive allocation

Based on evaluation infrastructure patterns from ASI-Evolve research.
"""

import asyncio
import hashlib
import json
import logging
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum, auto
from typing import Any, Callable, Dict, List, Optional, Tuple, Set
from collections import defaultdict
from pathlib import Path

logger = logging.getLogger(__name__)


class ExperimentStage(Enum):
    """Stages of experiment evaluation"""
    EXPLORATION = "exploration"
    VERIFICATION = "verification"
    VALIDATION = "validation"
    COMPLETED = "completed"
    FAILED = "failed"
    REJECTED = "rejected"


class ExperimentType(Enum):
    """Types of experiments"""
    BACKTEST = "backtest"
    PAPER_TRADE = "paper_trade"
    SHADOW_TRADE = "shadow_trade"
    A_B_TEST = "a_b_test"
    BANDIT = "bandit"
    SANDBOX = "sandbox"


@dataclass
class ResourceLimits:
    """Resource limits for an experiment"""
    max_runtime_seconds: float = 300.0
    max_cpu_percent: float = 80.0
    max_memory_mb: float = 1024.0
    max_disk_mb: float = 100.0
    
    def check_within_limits(self, current: Dict[str, float]) -> Tuple[bool, List[str]]:
        """Check if current usage is within limits"""
        violations = []
        
        if current.get('runtime', 0) > self.max_runtime_seconds:
            violations.append(f"Runtime {current['runtime']:.1f}s exceeds limit {self.max_runtime_seconds}s")
        
        if current.get('cpu', 0) > self.max_cpu_percent:
            violations.append(f"CPU {current['cpu']:.1f}% exceeds limit {self.max_cpu_percent}%")
        
        if current.get('memory', 0) > self.max_memory_mb:
            violations.append(f"Memory {current['memory']:.1f}MB exceeds limit {self.max_memory_mb}MB")
        
        return len(violations) == 0, violations


@dataclass
class StageResult:
    """Result from a single evaluation stage"""
    stage: ExperimentStage
    passed: bool
    metrics: Dict[str, float]
    artifacts: Dict[str, Any] = field(default_factory=dict)
    runtime_seconds: float = 0.0
    timestamp: datetime = field(default_factory=datetime.utcnow)
    rejection_reason: Optional[str] = None


@dataclass
class Experiment:
    """A single experiment definition"""
    id: str
    name: str
    experiment_type: ExperimentType
    hypothesis: str
    decision_strategy: Dict[str, Any]
    resource_limits: ResourceLimits
    stages_to_run: List[ExperimentStage] = field(default_factory=lambda: [
        ExperimentStage.EXPLORATION, ExperimentStage.VERIFICATION, ExperimentStage.VALIDATION
    ])
    
    # Results
    stage_results: Dict[ExperimentStage, StageResult] = field(default_factory=dict)
    final_score: float = 0.0
    status: ExperimentStage = ExperimentStage.EXPLORATION
    
    # Metadata
    created_at: datetime = field(default_factory=datetime.utcnow)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    parent_experiment: Optional[str] = None
    variant_id: Optional[str] = None  # For A/B tests
    
    def __post_init__(self):
        if not self.id:
            self.id = str(uuid.uuid4())
    
    def compute_hash(self) -> str:
        """Compute unique hash for deduplication"""
        content = f"{self.name}:{self.hypothesis}:{json.dumps(self.decision_strategy, sort_keys=True)}"
        return hashlib.sha256(content.encode()).hexdigest()[:16]


@dataclass
class ABTestConfig:
    """Configuration for A/B testing"""
    variant_a: Experiment
    variant_b: Experiment
    traffic_split: float = 0.5  # Traffic to variant A
    min_samples: int = 100
    significance_level: float = 0.05
    primary_metric: str = "sharpe_ratio"
    stopping_criteria: Dict[str, float] = field(default_factory=lambda: {
        'min_effect_size': 0.1,
        'max_samples': 1000
    })


@dataclass
class ABTestResult:
    """Result of A/B test"""
    test_id: str
    variant_a_id: str
    variant_b_id: str
    winner: Optional[str]  # 'A', 'B', or None for tie
    confidence: float
    primary_metric_delta: float
    statistical_significance: bool
    samples_a: int
    samples_b: int
    metrics_comparison: Dict[str, Tuple[float, float]]  # metric -> (A_value, B_value)
    recommendation: str


@dataclass
class BanditArm:
    """Arm in a multi-armed bandit experiment"""
    experiment_id: str
    pulls: int = 0
    rewards: float = 0.0
    last_selected: Optional[datetime] = None
    
    @property
    def estimated_value(self) -> float:
        if self.pulls == 0:
            return float('inf')  # Prioritize unexplored arms
        return self.rewards / self.pulls


class ExperimentManager:
    """
    Experiment Management System
    
    Coordinates multi-stage evaluation, resource management,
    and result persistence for decision validation.
    """
    
    def __init__(
        self,
        max_parallel_experiments: int = 4,
        storage_path: str = "experiments",
        enable_early_rejection: bool = True
    ):
        self.max_parallel = max_parallel_experiments
        self.storage_path = Path(storage_path)
        self.storage_path.mkdir(parents=True, exist_ok=True)
        self.enable_early_rejection = enable_early_rejection
        
        # Active experiments
        self.experiments: Dict[str, Experiment] = {}
        self.running_tasks: Dict[str, asyncio.Task] = {}
        
        # A/B tests
        self.ab_tests: Dict[str, ABTestConfig] = {}
        self.ab_results: Dict[str, ABTestResult] = {}
        
        # Bandit experiments
        self.bandit_arms: Dict[str, List[BanditArm]] = {}
        
        # Statistics
        self.stats = {
            'experiments_created': 0,
            'experiments_completed': 0,
            'experiments_failed': 0,
            'early_rejections': 0,
            'total_runtime_seconds': 0.0
        }
    
    async def create_experiment(
        self,
        name: str,
        experiment_type: ExperimentType,
        hypothesis: str,
        decision_strategy: Dict[str, Any],
        resource_limits: Optional[ResourceLimits] = None,
        parent_id: Optional[str] = None
    ) -> str:
        """
        Create a new experiment.
        
        Returns experiment ID.
        """
        experiment = Experiment(
            id=str(uuid.uuid4()),
            name=name,
            experiment_type=experiment_type,
            hypothesis=hypothesis,
            decision_strategy=decision_strategy,
            resource_limits=resource_limits or ResourceLimits(),
            parent_experiment=parent_id
        )
        
        # Check for duplicates
        experiment_hash = experiment.compute_hash()
        for existing in self.experiments.values():
            if existing.compute_hash() == experiment_hash:
                logger.warning(f"Duplicate experiment detected: {experiment.name}")
        
        self.experiments[experiment.id] = experiment
        self.stats['experiments_created'] += 1
        
        logger.info(f"Created experiment {experiment.id}: {name}")
        
        return experiment.id
    
    async def run_experiment(self, experiment_id: str) -> Experiment:
        """
        Run a complete experiment through all stages.
        """
        experiment = self.experiments.get(experiment_id)
        if not experiment:
            raise ValueError(f"Experiment {experiment_id} not found")
        
        experiment.started_at = datetime.utcnow()
        
        try:
            for stage in experiment.stages_to_run:
                experiment.status = stage
                
                # Run stage
                result = await self._run_stage(experiment, stage)
                experiment.stage_results[stage] = result
                
                # Check for early rejection
                if self.enable_early_rejection and not result.passed:
                    experiment.status = ExperimentStage.REJECTED
                    self.stats['early_rejections'] += 1
                    logger.info(f"Early rejection at stage {stage.value} for {experiment_id}")
                    break
            
            # Compute final score if all stages passed
            if experiment.status != ExperimentStage.REJECTED:
                experiment.final_score = self._compute_final_score(experiment)
                experiment.status = ExperimentStage.COMPLETED
                self.stats['experiments_completed'] += 1
            
            experiment.completed_at = datetime.utcnow()
            
            # Update runtime stats
            runtime = (experiment.completed_at - experiment.started_at).total_seconds()
            self.stats['total_runtime_seconds'] += runtime
            
            # Persist results
            await self._persist_experiment(experiment)
            
        except Exception as e:
            logger.error(f"Experiment {experiment_id} failed: {e}")
            experiment.status = ExperimentStage.FAILED
            self.stats['experiments_failed'] += 1
        
        return experiment
    
    async def _run_stage(self, experiment: Experiment, stage: ExperimentStage) -> StageResult:
        """Run a single evaluation stage"""
        start_time = datetime.utcnow()
        
        # Stage-specific evaluation
        evaluators = {
            ExperimentStage.EXPLORATION: self._exploration_eval,
            ExperimentStage.VERIFICATION: self._verification_eval,
            ExperimentStage.VALIDATION: self._validation_eval
        }
        
        evaluator = evaluators.get(stage)
        if not evaluator:
            return StageResult(
                stage=stage,
                passed=False,
                metrics={},
                rejection_reason=f"No evaluator for stage {stage}"
            )
        
        # Run evaluation with timeout
        try:
            metrics = await asyncio.wait_for(
                evaluator(experiment),
                timeout=experiment.resource_limits.max_runtime_seconds
            )
            
            passed = self._check_stage_gates(stage, metrics)
            
            runtime = (datetime.utcnow() - start_time).total_seconds()
            
            return StageResult(
                stage=stage,
                passed=passed,
                metrics=metrics,
                runtime_seconds=runtime
            )
            
        except asyncio.TimeoutError:
            return StageResult(
                stage=stage,
                passed=False,
                metrics={},
                rejection_reason=f"Timeout after {experiment.resource_limits.max_runtime_seconds}s",
                runtime_seconds=experiment.resource_limits.max_runtime_seconds
            )
    
    async def _exploration_eval(self, experiment: Experiment) -> Dict[str, float]:
        """Quick exploration evaluation"""
        # Simulate quick backtest on limited data
        await asyncio.sleep(0.05)  # Simulated work
        
        # Generate pseudo-random but deterministic metrics
        seed = int(experiment.id[:8], 16)
        
        return {
            'sharpe_ratio': 0.3 + (seed % 100) / 200,
            'max_drawdown': 0.05 + (seed % 50) / 500,
            'win_rate': 0.45 + (seed % 20) / 100,
            'profit_factor': 1.0 + (seed % 50) / 100,
            'sample_size': 100,
            'confidence': 0.6
        }
    
    async def _verification_eval(self, experiment: Experiment) -> Dict[str, float]:
        """Verification on more data"""
        await asyncio.sleep(0.15)
        
        exploration = experiment.stage_results.get(ExperimentStage.EXPLORATION, StageResult(
            stage=ExperimentStage.EXPLORATION,
            passed=True,
            metrics={}
        ))
        
        seed = int(experiment.id[:8], 16)
        
        # Build on exploration with some variance
        return {
            'sharpe_ratio': exploration.metrics.get('sharpe_ratio', 0.5) * (0.9 + (seed % 20) / 100),
            'max_drawdown': exploration.metrics.get('max_drawdown', 0.05) * (1.0 + (seed % 30) / 100),
            'win_rate': exploration.metrics.get('win_rate', 0.5),
            'profit_factor': 1.1 + (seed % 80) / 200,
            'sample_size': 500,
            'confidence': 0.75
        }
    
    async def _validation_eval(self, experiment: Experiment) -> Dict[str, float]:
        """Final validation"""
        await asyncio.sleep(0.25)
        
        verification = experiment.stage_results.get(ExperimentStage.VERIFICATION, StageResult(
            stage=ExperimentStage.VERIFICATION,
            passed=True,
            metrics={}
        ))
        
        v_metrics = verification.metrics
        
        # Compute composite score
        score = (
            v_metrics.get('sharpe_ratio', 0) * 0.35 +
            (1 - v_metrics.get('max_drawdown', 0)) * 0.25 +
            v_metrics.get('win_rate', 0) * 0.20 +
            (v_metrics.get('profit_factor', 1) - 1) * 0.20
        )
        
        return {
            'sharpe_ratio': v_metrics.get('sharpe_ratio', 0),
            'max_drawdown': v_metrics.get('max_drawdown', 0),
            'win_rate': v_metrics.get('win_rate', 0),
            'profit_factor': v_metrics.get('profit_factor', 1),
            'final_score': score,
            'sample_size': 1000,
            'confidence': 0.9,
            'passed': score > 0.5
        }
    
    def _check_stage_gates(self, stage: ExperimentStage, metrics: Dict[str, float]) -> bool:
        """Check if metrics pass stage gates"""
        if stage == ExperimentStage.EXPLORATION:
            return (
                metrics.get('sharpe_ratio', 0) > 0.3 and
                metrics.get('max_drawdown', 1) < 0.15 and
                metrics.get('win_rate', 0) > 0.4
            )
        elif stage == ExperimentStage.VERIFICATION:
            return (
                metrics.get('sharpe_ratio', 0) > 0.4 and
                metrics.get('max_drawdown', 1) < 0.12
            )
        elif stage == ExperimentStage.VALIDATION:
            return metrics.get('passed', False)
        return True
    
    def _compute_final_score(self, experiment: Experiment) -> float:
        """Compute final score from all stages"""
        validation = experiment.stage_results.get(ExperimentStage.VALIDATION)
        if validation:
            return validation.metrics.get('final_score', 0)
        
        # Fallback to verification
        verification = experiment.stage_results.get(ExperimentStage.VERIFICATION)
        if verification:
            return verification.metrics.get('sharpe_ratio', 0) * 0.5
        
        return 0.0
    
    async def run_experiments_parallel(
        self,
        experiment_ids: List[str],
        max_parallel: Optional[int] = None
    ) -> List[Experiment]:
        """Run multiple experiments in parallel"""
        max_parallel = max_parallel or self.max_parallel
        semaphore = asyncio.Semaphore(max_parallel)
        
        async def run_with_semaphore(exp_id: str) -> Experiment:
            async with semaphore:
                return await self.run_experiment(exp_id)
        
        tasks = [run_with_semaphore(eid) for eid in experiment_ids]
        return await asyncio.gather(*tasks)
    
    async def setup_ab_test(self, config: ABTestConfig) -> str:
        """Set up an A/B test"""
        test_id = str(uuid.uuid4())
        self.ab_tests[test_id] = config
        
        # Mark experiments as variants
        config.variant_a.variant_id = 'A'
        config.variant_b.variant_id = 'B'
        
        logger.info(f"Set up A/B test {test_id}: {config.variant_a.name} vs {config.variant_b.name}")
        
        return test_id
    
    async def run_ab_test(self, test_id: str) -> ABTestResult:
        """Run A/B test and determine winner"""
        config = self.ab_tests.get(test_id)
        if not config:
            raise ValueError(f"A/B test {test_id} not found")
        
        # Run both experiments
        results = await self.run_experiments_parallel([
            config.variant_a.id,
            config.variant_b.id
        ])
        
        result_a, result_b = results
        
        # Compare primary metric
        metric_a = result_a.final_score
        metric_b = result_b.final_score
        
        # Simple comparison (would use proper statistical test in production)
        delta = metric_b - metric_a
        
        # Determine winner
        winner = None
        confidence = 0.5
        
        if abs(delta) > config.stopping_criteria['min_effect_size']:
            winner = 'B' if delta > 0 else 'A'
            confidence = min(0.95, 0.5 + abs(delta))
        
        # Build metrics comparison
        comparison = {}
        for key in ['sharpe_ratio', 'max_drawdown', 'win_rate', 'profit_factor']:
            val_a = result_a.stage_results.get(ExperimentStage.VALIDATION, StageResult(
                stage=ExperimentStage.VALIDATION,
                passed=True,
                metrics={}
            )).metrics.get(key, 0)
            val_b = result_b.stage_results.get(ExperimentStage.VALIDATION, StageResult(
                stage=ExperimentStage.VALIDATION,
                passed=True,
                metrics={}
            )).metrics.get(key, 0)
            comparison[key] = (val_a, val_b)
        
        result = ABTestResult(
            test_id=test_id,
            variant_a_id=config.variant_a.id,
            variant_b_id=config.variant_b.id,
            winner=winner,
            confidence=confidence,
            primary_metric_delta=delta,
            statistical_significance=confidence > 0.8,
            samples_a=1000,  # Would be actual sample count
            samples_b=1000,
            metrics_comparison=comparison,
            recommendation=f"Deploy variant {winner}" if winner else "No significant difference detected"
        )
        
        self.ab_results[test_id] = result
        return result
    
    def select_bandit_arm(self, experiment_group: str) -> Optional[str]:
        """Select experiment using UCB1 algorithm"""
        arms = self.bandit_arms.get(experiment_group, [])
        if not arms:
            return None
        
        total_pulls = sum(arm.pulls for arm in arms)
        
        def ucb_score(arm: BanditArm) -> float:
            if arm.pulls == 0:
                return float('inf')
            exploitation = arm.estimated_value
            exploration = (2 * (total_pulls ** 0.5) / arm.pulls) ** 0.5
            return exploitation + exploration
        
        best_arm = max(arms, key=ucb_score)
        return best_arm.experiment_id
    
    def update_bandit_arm(
        self,
        experiment_group: str,
        experiment_id: str,
        reward: float
    ):
        """Update bandit arm with observed reward"""
        if experiment_group not in self.bandit_arms:
            self.bandit_arms[experiment_group] = []
        
        # Find or create arm
        arm = None
        for a in self.bandit_arms[experiment_group]:
            if a.experiment_id == experiment_id:
                arm = a
                break
        
        if not arm:
            arm = BanditArm(experiment_id=experiment_id)
            self.bandit_arms[experiment_group].append(arm)
        
        arm.pulls += 1
        arm.rewards += reward
        arm.last_selected = datetime.utcnow()
    
    async def _persist_experiment(self, experiment: Experiment):
        """Persist experiment results to storage"""
        file_path = self.storage_path / f"{experiment.id}.json"
        
        data = {
            'id': experiment.id,
            'name': experiment.name,
            'type': experiment.experiment_type.value,
            'hypothesis': experiment.hypothesis,
            'status': experiment.status.value,
            'final_score': experiment.final_score,
            'stage_results': {
                stage.value: {
                    'passed': result.passed,
                    'metrics': result.metrics,
                    'runtime': result.runtime_seconds,
                    'timestamp': result.timestamp.isoformat()
                }
                for stage, result in experiment.stage_results.items()
            },
            'created_at': experiment.created_at.isoformat(),
            'completed_at': experiment.completed_at.isoformat() if experiment.completed_at else None
        }
        
        with open(file_path, 'w') as f:
            json.dump(data, f, indent=2)
    
    def get_experiment(self, experiment_id: str) -> Optional[Experiment]:
        """Get experiment by ID"""
        return self.experiments.get(experiment_id)
    
    def get_best_experiments(self, k: int = 5) -> List[Tuple[Experiment, float]]:
        """Get top k experiments by final score"""
        completed = [
            (exp, exp.final_score)
            for exp in self.experiments.values()
            if exp.status == ExperimentStage.COMPLETED
        ]
        completed.sort(key=lambda x: x[1], reverse=True)
        return completed[:k]
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get experiment manager statistics"""
        return {
            **self.stats,
            'active_experiments': len(self.running_tasks),
            'total_experiments': len(self.experiments),
            'ab_tests': len(self.ab_tests),
            'bandit_groups': len(self.bandit_arms),
            'success_rate': (
                self.stats['experiments_completed'] / max(1, self.stats['experiments_created'])
            ),
            'average_runtime': (
                self.stats['total_runtime_seconds'] / max(1, self.stats['experiments_completed'])
            )
        }


def create_experiment_manager(
    max_parallel: int = 4,
    storage_path: str = "experiments"
) -> ExperimentManager:
    """Factory function to create experiment manager"""
    return ExperimentManager(
        max_parallel_experiments=max_parallel,
        storage_path=storage_path
    )
