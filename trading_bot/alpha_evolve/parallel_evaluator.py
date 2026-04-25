"""
Parallel Strategy Evaluator
Distributes strategy evaluation across multiple processes for massive parallel search
"""

import asyncio
import multiprocessing as mp
import pickle
import time
import uuid
from concurrent.futures import ProcessPoolExecutor, ThreadPoolExecutor, as_completed
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple, Callable
from dataclasses import dataclass, asdict
import logging
import numpy as np
import pandas as pd
from pathlib import Path

from .strategy_genome import StrategyGenome
from .backtesting_engine import LeakageFreeBacktester, BacktestResult
from .fitness_evaluator import MultiObjectiveFitness, FitnessScore
from .walk_forward import WalkForwardValidator, WalkForwardResult
from .backtest_cache import BacktestCache

logger = logging.getLogger(__name__)


@dataclass
class EvaluationTask:
    """Task for strategy evaluation"""
    task_id: str
    genome: StrategyGenome
    market_data_hash: str
    backtest_config: Dict[str, Any]
    priority: int = 0
    created_at: datetime = None
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now()


@dataclass
class EvaluationResult:
    """Result of strategy evaluation"""
    task_id: str
    genome: StrategyGenome
    backtest_result: Optional[BacktestResult] = None
    fitness_score: Optional[FitnessScore] = None
    walkforward_result: Optional[WalkForwardResult] = None
    evaluation_time: float = 0.0
    error: Optional[str] = None
    worker_id: Optional[str] = None


class ParallelEvaluator:
    """
    Parallel strategy evaluator with distributed processing capabilities.
    
    Features:
    - Multi-process evaluation
    - Task queue with priorities
    - Result caching
    - Worker health monitoring
    - Load balancing
    - Asynchronous processing
    """
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        
        # Process pool configuration
        self.max_workers = config.get('max_workers', mp.cpu_count())
        self.use_processes = config.get('use_processes', True)
        self.chunk_size = config.get('chunk_size', 10)
        
        # Task management
        self.pending_tasks: Dict[str, EvaluationTask] = {}
        self.running_tasks: Dict[str, EvaluationTask] = {}
        self.completed_tasks: Dict[str, EvaluationResult] = {}
        
        # Performance tracking
        self.evaluation_times: List[float] = []
        self.worker_stats: Dict[str, Dict[str, Any]] = {}
        
        # Caching
        self.cache = BacktestCache(config.get('cache', {}))
        
        # Executors
        self.executor: Optional[ProcessPoolExecutor] = None
        self.thread_executor: Optional[ThreadPoolExecutor] = None
        
        # Synchronization
        self._shutdown = False
        self._task_lock = asyncio.Lock()
        
        logger.info(f"Parallel evaluator initialized: workers={self.max_workers}, "
                   f"processes={self.use_processes}")
    
    async def start(self) -> None:
        """Start the evaluator and initialize workers"""
        if self.use_processes:
            self.executor = ProcessPoolExecutor(
                max_workers=self.max_workers,
                mp_context=mp.get_context('spawn')  # Required for Windows
            )
            logger.info(f"Started process pool with {self.max_workers} workers")
        else:
            self.thread_executor = ThreadPoolExecutor(
                max_workers=self.max_workers
            )
            logger.info(f"Started thread pool with {self.max_workers} workers")
    
    async def stop(self) -> None:
        """Stop the evaluator and cleanup resources"""
        self._shutdown = True
        
        if self.executor:
            self.executor.shutdown(wait=True)
            logger.info("Process pool shutdown")
        
        if self.thread_executor:
            self.thread_executor.shutdown(wait=True)
            logger.info("Thread pool shutdown")
    
    async def evaluate_strategies(self,
                                 strategies: List[StrategyGenome],
                                 market_data: pd.DataFrame,
                                 backtest_config: Dict[str, Any]) -> List[EvaluationResult]:
        """
        Evaluate multiple strategies in parallel.
        
        Args:
            strategies: List of strategy genomes to evaluate
            market_data: Market data for backtesting
            backtest_config: Configuration for backtesting
            
        Returns:
            List of evaluation results
        """
        # Generate hash for market data
        market_data_hash = self._hash_market_data(market_data)
        
        # Create evaluation tasks
        tasks = []
        for i, strategy in enumerate(strategies):
            task = EvaluationTask(
                task_id=str(uuid.uuid4()),
                genome=strategy,
                market_data_hash=market_data_hash,
                backtest_config=backtest_config,
                priority=i  # Simple FIFO priority
            )
            tasks.append(task)
        
        # Submit tasks for evaluation
        results = await self._submit_tasks(tasks, market_data)
        
        return results
    
    async def evaluate_strategy(self,
                               strategy: StrategyGenome,
                               market_data: pd.DataFrame,
                               backtest_config: Dict[str, Any]) -> EvaluationResult:
        """
        Evaluate a single strategy.
        
        Args:
            strategy: Strategy genome to evaluate
            market_data: Market data for backtesting
            backtest_config: Configuration for backtesting
            
        Returns:
            Evaluation result
        """
        results = await self.evaluate_strategies([strategy], market_data, backtest_config)
        return results[0] if results else None
    
    async def _submit_tasks(self,
                           tasks: List[EvaluationTask],
                           market_data: pd.DataFrame) -> List[EvaluationResult]:
        """Submit tasks to workers and collect results"""
        # Check cache first
        cached_tasks = []
        uncached_tasks = []
        
        for task in tasks:
            cached_result = self.cache.get(
                task.genome,
                task.market_data_hash,
                task.backtest_config
            )
            
            if cached_result:
                # Create result from cache
                result = EvaluationResult(
                    task_id=task.task_id,
                    genome=task.genome,
                    backtest_result=cached_result,
                    evaluation_time=0.0,
                    worker_id='cache'
                )
                cached_tasks.append(result)
            else:
                uncached_tasks.append(task)
        
        logger.info(f"Cache hits: {len(cached_tasks)}, evaluating: {len(uncached_tasks)}")
        
        # Evaluate uncached strategies
        if uncached_tasks:
            # Prepare data for workers
            market_data_path = self._save_market_data(market_data)
            
            # Submit tasks in chunks
            chunk_results = []
            for i in range(0, len(uncached_tasks), self.chunk_size):
                chunk = uncached_tasks[i:i + self.chunk_size]
                chunk_results.extend(
                    await self._evaluate_chunk(chunk, market_data_path)
                )
            
            # Cache results
            for result in chunk_results:
                if result.backtest_result and not result.error:
                    self.cache.put(
                        result.genome,
                        tasks[0].market_data_hash,
                        tasks[0].backtest_config,
                        result.backtest_result
                    )
            
            uncached_tasks = chunk_results
        
        # Combine cached and evaluated results
        all_results = cached_tasks + uncached_tasks
        
        # Sort by original order
        task_order = {task.task_id: i for i, task in enumerate(tasks)}
        all_results.sort(key=lambda r: task_order.get(r.task_id, float('inf')))
        
        return all_results
    
    async def _evaluate_chunk(self,
                             tasks: List[EvaluationTask],
                             market_data_path: Path) -> List[EvaluationResult]:
        """Evaluate a chunk of tasks"""
        # Prepare arguments for workers
        worker_args = []
        for task in tasks:
            args = (
                task.task_id,
                task.genome,
                str(market_data_path),
                task.backtest_config
            )
            worker_args.append(args)
        
        # Submit to executor
        loop = asyncio.get_event_loop()
        
        if self.use_processes and self.executor:
            # Use process pool
            futures = [
                loop.run_in_executor(
                    self.executor,
                    _evaluate_strategy_worker,
                    *args
                )
                for args in worker_args
            ]
        else:
            # Use thread pool
            futures = [
                loop.run_in_executor(
                    self.thread_executor,
                    _evaluate_strategy_worker,
                    *args
                )
                for args in worker_args
            ]
        
        # Collect results
        results = []
        for future in asyncio.as_completed(futures):
            try:
                result = await future
                results.append(result)
            except Exception as e:
                logger.error(f"Task evaluation failed: {e}")
                # Create error result
                task_id = worker_args[len(results)][0]  # Approximate
                results.append(EvaluationResult(
                    task_id=task_id,
                    genome=None,
                    error=str(e)
                ))
        
        return results
    
    def _hash_market_data(self, market_data: pd.DataFrame) -> str:
        """Generate hash for market data"""
        # Use first and last rows plus shape for hashing
        sample_data = pd.concat([
            market_data.head(1),
            market_data.tail(1),
            pd.DataFrame({'shape': [market_data.shape]})
        ])
        
        data_hash = pd.util.hash_pandas_object(sample_data).sum()
        return str(abs(data_hash))
    
    def _save_market_data(self, market_data: pd.DataFrame) -> Path:
        """Save market data to temporary file for workers"""
        temp_dir = Path('./temp/evaluation_data')
        temp_dir.mkdir(parents=True, exist_ok=True)
        
        # Use timestamp for unique filename
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S_%f')
        file_path = temp_dir / f"market_data_{timestamp}.parquet"
        
        # Save as parquet for efficiency
        market_data.to_parquet(file_path)
        
        return file_path
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get evaluator statistics"""
        cache_stats = self.cache.get_statistics()
        
        return {
            'pending_tasks': len(self.pending_tasks),
            'running_tasks': len(self.running_tasks),
            'completed_tasks': len(self.completed_tasks),
            'avg_evaluation_time': np.mean(self.evaluation_times) if self.evaluation_times else 0,
            'total_evaluations': len(self.evaluation_times),
            'worker_count': self.max_workers,
            'cache': cache_stats
        }


def _evaluate_strategy_worker(task_id: str,
                             genome: StrategyGenome,
                             market_data_path: str,
                             backtest_config: Dict[str, Any]) -> EvaluationResult:
    """
    Worker function for evaluating a single strategy.
    Runs in a separate process.
    """
    start_time = time.time()
    worker_id = f"worker_{mp.current_process().pid}"
    
    try:
        # Load market data
        import pandas as pd
        market_data = pd.read_parquet(market_data_path)
        
        # Initialize backtester
        backtester = LeakageFreeBacktester(backtest_config)
        
        # Run backtest
        backtest_result = backtester.run_backtest(genome, market_data)
        
        # Calculate fitness
        fitness_evaluator = MultiObjectiveFitness(backtest_config.get('fitness', {}))
        fitness_score = fitness_evaluator.evaluate(backtest_result)
        
        # Run walk-forward validation if enabled
        walkforward_result = None
        if backtest_config.get('walk_forward', False):
            validator = WalkForwardValidator(backtest_config.get('walk_forward_config', {}))
            walkforward_result = validator.validate(genome, market_data)
        
        evaluation_time = time.time() - start_time
        
        return EvaluationResult(
            task_id=task_id,
            genome=genome,
            backtest_result=backtest_result,
            fitness_score=fitness_score,
            walkforward_result=walkforward_result,
            evaluation_time=evaluation_time,
            worker_id=worker_id
        )
        
    except Exception as e:
        logger.error(f"Worker {worker_id} failed: {e}")
        return EvaluationResult(
            task_id=task_id,
            genome=genome,
            evaluation_time=time.time() - start_time,
            error=str(e),
            worker_id=worker_id
        )


class DistributedEvaluator(ParallelEvaluator):
    """
    Extended evaluator for distributed computing across multiple machines.
    
    Features:
    - Redis task queue
    - Worker node management
    - Load balancing across nodes
    - Fault tolerance
    """
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        
        # Distributed configuration
        self.redis_host = config.get('redis_host', 'localhost')
        self.redis_port = config.get('redis_port', 6379)
        self.node_id = config.get('node_id', f"node_{uuid.uuid4().hex[:8]}")
        
        # Redis clients
        self.task_queue = None
        self.result_store = None
        self.worker_registry = None
        
        # Node management
        self.worker_nodes: Dict[str, Dict[str, Any]] = {}
        self.heartbeat_interval = config.get('heartbeat_interval', 30)
        
        logger.info(f"Distributed evaluator initialized: node_id={self.node_id}")
    
    async def start_distributed(self) -> None:
        """Start distributed evaluation components"""
        try:
            import redis
            
            # Initialize Redis clients
            self.task_queue = redis.Redis(
                host=self.redis_host,
                port=self.redis_port,
                db=0,
                decode_responses=False
            )
            
            self.result_store = redis.Redis(
                host=self.redis_host,
                port=self.redis_port,
                db=1,
                decode_responses=False
            )
            
            self.worker_registry = redis.Redis(
                host=self.redis_host,
                port=self.redis_port,
                db=2,
                decode_responses=True
            )
            
            # Register this node
            await self._register_node()
            
            # Start heartbeat
            asyncio.create_task(self._heartbeat_loop())
            
            logger.info("Distributed evaluator started")
            
        except Exception as e:
            logger.error(f"Failed to start distributed evaluator: {e}")
            raise
    
    async def _register_node(self) -> None:
        """Register this worker node"""
        node_info = {
            'node_id': self.node_id,
            'max_workers': self.max_workers,
            'current_load': 0,
            'last_heartbeat': datetime.now().isoformat(),
            'status': 'active'
        }
        
        self.worker_registry.hset(
            f"node:{self.node_id}",
            mapping=node_info
        )
    
    async def _heartbeat_loop(self) -> None:
        """Send periodic heartbeats"""
        while not self._shutdown:
            try:
                await self._register_node()
                await asyncio.sleep(self.heartbeat_interval)
            except Exception as e:
                logger.error(f"Heartbeat failed: {e}")
                await asyncio.sleep(5)
