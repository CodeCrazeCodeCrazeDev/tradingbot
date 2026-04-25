"""
Distributed Evaluation Framework

Provides distributed backtesting capabilities for massive parallel strategy evaluation.
Uses Redis for task queue and result storage.
"""

from typing import List, Dict, Optional, Any, Callable, Tuple
from dataclasses import dataclass, field
from datetime import datetime
import pickle
import hashlib
import logging
from concurrent.futures import ProcessPoolExecutor, as_completed
from multiprocessing import cpu_count
import json

import numpy as np
import pandas as pd

from ..alpha_evolve.strategy_genome import StrategyGenome
from ..alpha_evolve.backtesting_engine import LeakageFreeBacktester, BacktestResult
from ..alpha_evolve.fitness_evaluator import FitnessScore

logger = logging.getLogger(__name__)


@dataclass
class EvaluationTask:
    """Task for distributed evaluation"""
    task_id: str
    genome: StrategyGenome
    market_data_hash: str
    config_hash: str
    priority: int = 0
    created_at: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict:
        """Serialize task to dictionary"""
        return {
            'task_id': self.task_id,
            'genome': pickle.dumps(self.genome).hex(),
            'market_data_hash': self.market_data_hash,
            'config_hash': self.config_hash,
            'priority': self.priority,
            'created_at': self.created_at.isoformat()
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'EvaluationTask':
        """Deserialize task from dictionary"""
        return cls(
            task_id=data['task_id'],
            genome=pickle.loads(bytes.fromhex(data['genome'])),
            market_data_hash=data['market_data_hash'],
            config_hash=data['config_hash'],
            priority=data.get('priority', 0),
            created_at=datetime.fromisoformat(data['created_at'])
        )


@dataclass
class EvaluationResult:
    """Result from distributed evaluation"""
    task_id: str
    success: bool
    backtest_result: Optional[BacktestResult] = None
    fitness_score: Optional[FitnessScore] = None
    error_message: Optional[str] = None
    execution_time_ms: float = 0.0
    worker_id: str = ""
    completed_at: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict:
        """Serialize result to dictionary"""
        return {
            'task_id': self.task_id,
            'success': self.success,
            'backtest_result': pickle.dumps(self.backtest_result).hex() if self.backtest_result else None,
            'fitness_score': pickle.dumps(self.fitness_score).hex() if self.fitness_score else None,
            'error_message': self.error_message,
            'execution_time_ms': self.execution_time_ms,
            'worker_id': self.worker_id,
            'completed_at': self.completed_at.isoformat()
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'EvaluationResult':
        """Deserialize result from dictionary"""
        return cls(
            task_id=data['task_id'],
            success=data['success'],
            backtest_result=pickle.loads(bytes.fromhex(data['backtest_result'])) if data.get('backtest_result') else None,
            fitness_score=pickle.loads(bytes.fromhex(data['fitness_score'])) if data.get('fitness_score') else None,
            error_message=data.get('error_message'),
            execution_time_ms=data.get('execution_time_ms', 0.0),
            worker_id=data.get('worker_id', ''),
            completed_at=datetime.fromisoformat(data['completed_at'])
        )


class BacktestCache:
    """
    LRU cache for backtest results to avoid redundant computations.
    
    Features:
    - Hash-based key generation for strategies
    - Configurable size limits
    - Hit rate tracking
    - TTL support
    """
    
    def __init__(self, max_size: int = 1000, ttl_seconds: Optional[int] = None):
        """
        Initialize backtest cache.
        
        Args:
            max_size: Maximum number of cached results
            ttl_seconds: Time-to-live for cache entries (None = no expiry)
        """
        self.max_size = max_size
        self.ttl_seconds = ttl_seconds
        self._cache: Dict[str, Tuple[BacktestResult, datetime]] = {}
        self._access_order: List[str] = []
        self.hit_count = 0
        self.miss_count = 0
        
        logger.info(f"BacktestCache initialized (max_size={max_size}, ttl={ttl_seconds})")
    
    def _generate_key(self, genome: StrategyGenome, market_data: pd.DataFrame) -> str:
        """Generate cache key from genome and market data"""
        genome_str = str(genome.__dict__)
        data_hash = hashlib.md5(market_data.to_json().encode()).hexdigest()[:16]
        key = hashlib.sha256(f"{genome_str}_{data_hash}".encode()).hexdigest()
        return key
    
    def get(self, genome: StrategyGenome, market_data: pd.DataFrame) -> Optional[BacktestResult]:
        """Get cached result if available"""
        key = self._generate_key(genome, market_data)
        
        if key in self._cache:
            result, timestamp = self._cache[key]
            
            # Check TTL
            if self.ttl_seconds:
                age = (datetime.now() - timestamp).total_seconds()
                if age > self.ttl_seconds:
                    del self._cache[key]
                    self._access_order.remove(key)
                    self.miss_count += 1
                    return None
            
            # Update access order (LRU)
            self._access_order.remove(key)
            self._access_order.append(key)
            
            self.hit_count += 1
            return result
        
        self.miss_count += 1
        return None
    
    def put(self, genome: StrategyGenome, market_data: pd.DataFrame, 
            result: BacktestResult) -> None:
        """Store result in cache"""
        key = self._generate_key(genome, market_data)
        
        # Evict oldest if at capacity
        if len(self._cache) >= self.max_size and key not in self._cache:
            oldest_key = self._access_order.pop(0)
            del self._cache[oldest_key]
        
        # Store new result
        self._cache[key] = (result, datetime.now())
        
        if key not in self._access_order:
            self._access_order.append(key)
    
    def get_hit_rate(self) -> float:
        """Calculate cache hit rate"""
        total = self.hit_count + self.miss_count
        if total == 0:
            return 0.0
        return self.hit_count / total
    
    def clear(self) -> None:
        """Clear all cached results"""
        self._cache.clear()
        self._access_order.clear()
        logger.info("BacktestCache cleared")
    
    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        return {
            'size': len(self._cache),
            'max_size': self.max_size,
            'hit_count': self.hit_count,
            'miss_count': self.miss_count,
            'hit_rate': self.get_hit_rate(),
            'ttl_seconds': self.ttl_seconds
        }


class ParallelEvaluator:
    """
    Parallel evaluation engine for strategy backtesting.
    
    Features:
    - Process pool execution
    - Configurable worker count
    - Progress tracking
    - Error handling
    """
    
    def __init__(self, max_workers: Optional[int] = None, 
                 cache: Optional[BacktestCache] = None):
        """
        Initialize parallel evaluator.
        
        Args:
            max_workers: Number of parallel workers (default: CPU count)
            cache: Optional backtest cache
        """
        self.max_workers = max_workers or cpu_count()
        self.cache = cache or BacktestCache()
        self._executor: Optional[ProcessPoolExecutor] = None
        
        logger.info(f"ParallelEvaluator initialized (workers={self.max_workers})")
    
    def start(self) -> None:
        """Start the process pool"""
        self._executor = ProcessPoolExecutor(max_workers=self.max_workers)
        logger.info("ParallelEvaluator started")
    
    def stop(self) -> None:
        """Stop the process pool"""
        if self._executor:
            self._executor.shutdown(wait=True)
            self._executor = None
            logger.info("ParallelEvaluator stopped")
    
    def evaluate_batch(self, 
                       genomes: List[StrategyGenome],
                       market_data: pd.DataFrame,
                       progress_callback: Optional[Callable[[int, int], None]] = None
                       ) -> List[Tuple[StrategyGenome, Optional[BacktestResult]]]:
        """
        Evaluate a batch of genomes in parallel.
        
        Args:
            genomes: List of strategy genomes to evaluate
            market_data: Market data for backtesting
            progress_callback: Optional callback(current, total)
            
        Returns:
            List of (genome, result) tuples
        """
        if not self._executor:
            self.start()
        
        results = []
        cached_count = 0
        
        # Check cache first
        to_evaluate = []
        for genome in genomes:
            cached = self.cache.get(genome, market_data)
            if cached:
                results.append((genome, cached))
                cached_count += 1
            else:
                to_evaluate.append(genome)
        
        # Submit parallel tasks
        if to_evaluate:
            futures = {
                self._executor.submit(self._evaluate_single, genome, market_data): genome
                for genome in to_evaluate
            }
            
            completed = 0
            for future in as_completed(futures):
                genome = futures[future]
                try:
                    result = future.result()
                    if result:
                        self.cache.put(genome, market_data, result)
                    results.append((genome, result))
                except Exception as e:
                    logger.error(f"Evaluation failed for {genome.get_genome_id()}: {e}")
                    results.append((genome, None))
                
                completed += 1
                if progress_callback:
                    progress_callback(completed + cached_count, len(genomes))
        
        logger.info(f"Batch evaluation complete: {len(results)} total, {cached_count} from cache")
        return results
    
    @staticmethod
    def _evaluate_single(genome: StrategyGenome, 
                        market_data: pd.DataFrame) -> Optional[BacktestResult]:
        """Static method for process pool evaluation"""
        try:
            backtester = LeakageFreeBacktester(market_data)
            return backtester.backtest(genome)
        except Exception as e:
            logger.error(f"Backtest failed: {e}")
            return None
    
    def get_stats(self) -> Dict[str, Any]:
        """Get evaluator statistics"""
        return {
            'max_workers': self.max_workers,
            'cache_stats': self.cache.get_stats()
        }


class DistributedEvaluationFramework:
    """
    Framework for distributed strategy evaluation across multiple workers.
    
    This is a simplified implementation that works on a single machine
    using process pools. For true distributed evaluation, this would be
    extended with Redis/RabbitMQ for cross-machine coordination.
    
    Features:
    - Task queue management
    - Result aggregation
    - Worker coordination
    - Fault tolerance
    """
    
    def __init__(self, 
                 max_workers: int = 4,
                 cache_size: int = 1000,
                 use_redis: bool = False):
        """
        Initialize distributed evaluation framework.
        
        Args:
            max_workers: Number of evaluation workers
            cache_size: Size of backtest cache
            use_redis: Whether to use Redis for distributed coordination
        """
        self.max_workers = max_workers
        self.use_redis = use_redis
        
        # Components
        self.cache = BacktestCache(max_size=cache_size)
        self.parallel_evaluator = ParallelEvaluator(
            max_workers=max_workers,
            cache=self.cache
        )
        
        # State
        self.pending_tasks: Dict[str, EvaluationTask] = {}
        self.completed_results: Dict[str, EvaluationResult] = {}
        self.failed_tasks: Dict[str, str] = {}  # task_id -> error
        
        # Statistics
        self.stats = {
            'tasks_submitted': 0,
            'tasks_completed': 0,
            'tasks_failed': 0,
            'total_execution_time': 0.0
        }
        
        logger.info(f"DistributedEvaluationFramework initialized (workers={max_workers})")
    
    def start(self) -> None:
        """Start the evaluation framework"""
        self.parallel_evaluator.start()
        logger.info("DistributedEvaluationFramework started")
    
    def stop(self) -> None:
        """Stop the evaluation framework"""
        self.parallel_evaluator.stop()
        logger.info("DistributedEvaluationFramework stopped")
    
    def submit_task(self, genome: StrategyGenome, 
                   market_data: pd.DataFrame,
                   priority: int = 0) -> str:
        """
        Submit a strategy for evaluation.
        
        Args:
            genome: Strategy genome to evaluate
            market_data: Market data for backtesting
            priority: Task priority (higher = more important)
            
        Returns:
            Task ID
        """
        task_id = f"task_{genome.get_genome_id()}_{datetime.now().timestamp()}"
        
        # Generate hashes
        data_hash = hashlib.md5(market_data.to_json().encode()).hexdigest()
        config_hash = hashlib.md5(str(priority).encode()).hexdigest()
        
        task = EvaluationTask(
            task_id=task_id,
            genome=genome,
            market_data_hash=data_hash,
            config_hash=config_hash,
            priority=priority
        )
        
        self.pending_tasks[task_id] = task
        self.stats['tasks_submitted'] += 1
        
        logger.debug(f"Task submitted: {task_id}")
        return task_id
    
    def submit_batch(self, 
                    genomes: List[StrategyGenome],
                    market_data: pd.DataFrame,
                    priority: int = 0) -> List[str]:
        """Submit multiple tasks"""
        return [self.submit_task(g, market_data, priority) for g in genomes]
    
    def execute_pending(self, market_data: pd.DataFrame) -> List[EvaluationResult]:
        """
        Execute all pending tasks.
        
        Args:
            market_data: Market data for backtesting
            
        Returns:
            List of evaluation results
        """
        if not self.pending_tasks:
            return []
        
        # Get genomes from pending tasks
        genomes = [task.genome for task in self.pending_tasks.values()]
        
        # Execute in parallel
        batch_results = self.parallel_evaluator.evaluate_batch(genomes, market_data)
        
        # Create evaluation results
        results = []
        for (genome, backtest_result), task_id in zip(batch_results, self.pending_tasks.keys()):
            if backtest_result:
                result = EvaluationResult(
                    task_id=task_id,
                    success=True,
                    backtest_result=backtest_result
                )
                self.completed_results[task_id] = result
                self.stats['tasks_completed'] += 1
            else:
                result = EvaluationResult(
                    task_id=task_id,
                    success=False,
                    error_message="Evaluation failed"
                )
                self.failed_tasks[task_id] = "Evaluation failed"
                self.stats['tasks_failed'] += 1
            
            results.append(result)
        
        # Clear pending
        self.pending_tasks.clear()
        
        return results
    
    def get_result(self, task_id: str) -> Optional[EvaluationResult]:
        """Get result for a completed task"""
        return self.completed_results.get(task_id)
    
    def get_all_results(self) -> Dict[str, EvaluationResult]:
        """Get all completed results"""
        return self.completed_results.copy()
    
    def get_stats(self) -> Dict[str, Any]:
        """Get framework statistics"""
        return {
            **self.stats,
            'pending_count': len(self.pending_tasks),
            'completed_count': len(self.completed_results),
            'failed_count': len(self.failed_tasks),
            'cache': self.cache.get_stats()
        }
    
    def reset(self) -> None:
        """Reset framework state"""
        self.pending_tasks.clear()
        self.completed_results.clear()
        self.failed_tasks.clear()
        self.stats = {
            'tasks_submitted': 0,
            'tasks_completed': 0,
            'tasks_failed': 0,
            'total_execution_time': 0.0
        }
        logger.info("DistributedEvaluationFramework reset")


# Convenience function for batch evaluation
def evaluate_population(
    genomes: List[StrategyGenome],
    market_data: pd.DataFrame,
    max_workers: int = 4,
    use_cache: bool = True
) -> List[Tuple[StrategyGenome, Optional[BacktestResult]]]:
    """
    Convenience function for batch population evaluation.
    
    Args:
        genomes: Population of strategy genomes
        market_data: Market data for backtesting
        max_workers: Number of parallel workers
        use_cache: Whether to use result caching
        
    Returns:
        List of (genome, result) tuples
    """
    cache = BacktestCache() if use_cache else None
    evaluator = ParallelEvaluator(max_workers=max_workers, cache=cache)
    
    try:
        evaluator.start()
        results = evaluator.evaluate_batch(genomes, market_data)
        return results
    finally:
        evaluator.stop()
