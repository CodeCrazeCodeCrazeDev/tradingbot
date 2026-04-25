"""
Distributed Compute Orchestrator for Massive Parallel Search.

Enables distributed evolution across multiple workers/machines for
faster strategy discovery and evaluation.
"""

from typing import List, Dict, Optional, Callable, Any
import numpy as np
import pandas as pd
from dataclasses import dataclass, field
from datetime import datetime
import logging
import json
from pathlib import Path
from concurrent.futures import ProcessPoolExecutor, ThreadPoolExecutor, as_completed
import multiprocessing as mp
from queue import Queue
import time

from .strategy_genome import StrategyGenome, SearchSpace
from .evolution_engine import Individual, EvolutionConfig


logger = logging.getLogger(__name__)


@dataclass
class WorkerTask:
    """Task for a worker to execute"""
    task_id: str
    task_type: str
    genome: StrategyGenome
    parameters: Dict[str, Any]
    priority: int = 0
    
    created_at: datetime = field(default_factory=datetime.now)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    
    result: Optional[Any] = None
    error: Optional[str] = None


@dataclass
class WorkerStatus:
    """Status of a worker"""
    worker_id: str
    is_active: bool
    current_task: Optional[str] = None
    tasks_completed: int = 0
    tasks_failed: int = 0
    
    cpu_usage: float = 0.0
    memory_usage: float = 0.0
    
    last_heartbeat: datetime = field(default_factory=datetime.now)


@dataclass
class ComputeCluster:
    """Cluster of compute workers"""
    cluster_id: str
    workers: List[WorkerStatus]
    
    total_capacity: int
    active_workers: int
    
    tasks_queued: int
    tasks_running: int
    tasks_completed: int
    
    throughput: float


class DistributedComputeOrchestrator:
    """
    Orchestrate distributed computation for strategy evolution.
    
    Features:
    - Task queue management
    - Worker pool coordination
    - Load balancing
    - Fault tolerance
    - Result aggregation
    """
    
    def __init__(
        self,
        num_workers: int = None,
        use_multiprocessing: bool = True,
        max_queue_size: int = 1000,
        task_timeout: int = 300
    ):
        """
        Initialize distributed compute orchestrator.
        
        Args:
            num_workers: Number of worker processes (default: CPU count)
            use_multiprocessing: Use multiprocessing vs threading
            max_queue_size: Maximum task queue size
            task_timeout: Task timeout in seconds
        """
        self.num_workers = num_workers or mp.cpu_count()
        self.use_multiprocessing = use_multiprocessing
        self.max_queue_size = max_queue_size
        self.task_timeout = task_timeout
        
        self.task_queue: List[WorkerTask] = []
        self.active_tasks: Dict[str, WorkerTask] = {}
        self.completed_tasks: Dict[str, WorkerTask] = {}
        
        self.workers: List[WorkerStatus] = []
        self.executor: Optional[Any] = None
        
        self._initialize_workers()
    
    def _initialize_workers(self):
        """Initialize worker pool"""
        logger.info(f"Initializing {self.num_workers} workers...")
        
        for i in range(self.num_workers):
            worker = WorkerStatus(
                worker_id=f"worker_{i}",
                is_active=True
            )
            self.workers.append(worker)
        
        if self.use_multiprocessing:
            self.executor = ProcessPoolExecutor(max_workers=self.num_workers)
        else:
            self.executor = ThreadPoolExecutor(max_workers=self.num_workers)
        
        logger.info(f"Workers initialized: {len(self.workers)}")
    
    def submit_task(self, task: WorkerTask) -> str:
        """
        Submit a task to the queue.
        
        Args:
            task: Task to submit
        
        Returns:
            Task ID
        """
        if len(self.task_queue) >= self.max_queue_size:
            raise RuntimeError(f"Task queue full (max: {self.max_queue_size})")
        
        self.task_queue.append(task)
        
        self.task_queue.sort(key=lambda t: t.priority, reverse=True)
        
        return task.task_id
    
    def submit_batch(self, tasks: List[WorkerTask]) -> List[str]:
        """Submit multiple tasks as a batch"""
        task_ids = []
        for task in tasks:
            task_id = self.submit_task(task)
            task_ids.append(task_id)
        
        return task_ids
    
    def execute_parallel(
        self,
        genomes: List[StrategyGenome],
        evaluation_func: Callable,
        **kwargs
    ) -> List[Any]:
        """
        Execute evaluation function on genomes in parallel.
        
        Args:
            genomes: List of genomes to evaluate
            evaluation_func: Function to evaluate each genome
            **kwargs: Additional arguments for evaluation function
        
        Returns:
            List of evaluation results
        """
        logger.info(f"Executing {len(genomes)} evaluations in parallel...")
        
        tasks = []
        for i, genome in enumerate(genomes):
            task = WorkerTask(
                task_id=f"eval_{i}_{datetime.now().timestamp()}",
                task_type="evaluation",
                genome=genome,
                parameters=kwargs
            )
            tasks.append(task)
        
        futures = {}
        for task in tasks:
            future = self.executor.submit(
                self._execute_task,
                task,
                evaluation_func
            )
            futures[future] = task
            
            task.started_at = datetime.now()
            self.active_tasks[task.task_id] = task
        
        results = []
        for future in as_completed(futures, timeout=self.task_timeout):
            task = futures[future]
            
            try:
                result = future.result()
                task.result = result
                task.completed_at = datetime.now()
                results.append(result)
                
                self.completed_tasks[task.task_id] = task
                del self.active_tasks[task.task_id]
                
            except Exception as e:
                logger.error(f"Task {task.task_id} failed: {e}")
                task.error = str(e)
                task.completed_at = datetime.now()
                results.append(None)
        
        logger.info(f"Completed {len(results)} evaluations")
        return results
    
    @staticmethod
    def _execute_task(task: WorkerTask, func: Callable) -> Any:
        """Execute a single task"""
        try:
            result = func(task.genome, **task.parameters)
            return result
        except Exception as e:
            logger.error(f"Error executing task {task.task_id}: {e}")
            raise
    
    def get_cluster_status(self) -> ComputeCluster:
        """Get current cluster status"""
        active_workers = sum(1 for w in self.workers if w.is_active)
        
        tasks_completed = len(self.completed_tasks)
        tasks_running = len(self.active_tasks)
        tasks_queued = len(self.task_queue)
        
        if tasks_completed > 0:
            total_time = sum(
                (t.completed_at - t.started_at).total_seconds()
                for t in self.completed_tasks.values()
                if t.completed_at and t.started_at
            )
            throughput = tasks_completed / (total_time / 3600) if total_time > 0 else 0
        else:
            throughput = 0
        
        return ComputeCluster(
            cluster_id="main_cluster",
            workers=self.workers,
            total_capacity=self.num_workers,
            active_workers=active_workers,
            tasks_queued=tasks_queued,
            tasks_running=tasks_running,
            tasks_completed=tasks_completed,
            throughput=throughput
        )
    
    def shutdown(self):
        """Shutdown the compute cluster"""
        logger.info("Shutting down compute cluster...")
        
        if self.executor:
            self.executor.shutdown(wait=True)
        
        for worker in self.workers:
            worker.is_active = False
        
        logger.info("Cluster shutdown complete")
    
    def __enter__(self):
        """Context manager entry"""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        self.shutdown()


class DistributedEvolutionEngine:
    """
    Distributed version of evolution engine for massive parallel search.
    
    Scales evolution across multiple workers for faster convergence.
    """
    
    def __init__(
        self,
        config: EvolutionConfig,
        search_space: SearchSpace,
        market_data: pd.DataFrame,
        num_workers: int = None
    ):
        """
        Initialize distributed evolution engine.
        
        Args:
            config: Evolution configuration
            search_space: Search space
            market_data: Market data
            num_workers: Number of parallel workers
        """
        self.config = config
        self.search_space = search_space
        self.market_data = market_data
        
        self.orchestrator = DistributedComputeOrchestrator(
            num_workers=num_workers or config.parallel_workers
        )
        
        self.population: List[Individual] = []
        self.generation = 0
    
    def evolve_distributed(
        self,
        evaluation_func: Callable,
        generations: int = None
    ) -> List[Individual]:
        """
        Run distributed evolution.
        
        Args:
            evaluation_func: Function to evaluate genomes
            generations: Number of generations (default: from config)
        
        Returns:
            Final population
        """
        generations = generations or self.config.max_generations
        
        logger.info(f"Starting distributed evolution for {generations} generations")
        logger.info(f"Using {self.orchestrator.num_workers} workers")
        
        self._initialize_population()
        
        for gen in range(generations):
            self.generation = gen
            
            logger.info(f"\nGeneration {gen + 1}/{generations}")
            
            genomes = [ind.genome for ind in self.population]
            
            results = self.orchestrator.execute_parallel(
                genomes=genomes,
                evaluation_func=evaluation_func,
                market_data=self.market_data
            )
            
            for ind, result in zip(self.population, results):
                if result:
                    ind.fitness = result.get('fitness')
                    ind.backtest_result = result.get('backtest_result')
            
            self._log_generation_stats()
            
            self._breed_next_generation()
            
            cluster_status = self.orchestrator.get_cluster_status()
            logger.info(f"Cluster throughput: {cluster_status.throughput:.2f} evals/hour")
        
        logger.info("Distributed evolution complete")
        return self.population
    
    def _initialize_population(self):
        """Initialize random population"""
        self.population = []
        for _ in range(self.config.population_size):
            genome = self.search_space.random_genome()
            self.population.append(Individual(genome=genome))
    
    def _log_generation_stats(self):
        """Log generation statistics"""
        fitnesses = [ind.fitness.total_fitness for ind in self.population if ind.fitness]
        
        if fitnesses:
            logger.info(f"  Best fitness:  {max(fitnesses):.4f}")
            logger.info(f"  Avg fitness:   {np.mean(fitnesses):.4f}")
            logger.info(f"  Worst fitness: {min(fitnesses):.4f}")
    
    def _breed_next_generation(self):
        """Breed next generation (simplified for distributed)"""
        from .genetic_operators import GeneticOperators
        
        genetic_ops = GeneticOperators(self.search_space)
        
        population_with_fitness = [
            (ind, ind.fitness.total_fitness if ind.fitness else 0)
            for ind in self.population
        ]
        
        elite = genetic_ops.elitism_selection(
            population_with_fitness,
            self.config.elite_size
        )
        
        next_gen = [Individual(genome=g.clone()) for g in elite]
        
        while len(next_gen) < self.config.population_size:
            parent = genetic_ops.tournament_selection(
                population_with_fitness,
                self.config.tournament_size
            )
            
            mutated = genetic_ops.mutate(parent)
            next_gen.append(Individual(genome=mutated))
        
        self.population = next_gen
    
    def shutdown(self):
        """Shutdown distributed engine"""
        self.orchestrator.shutdown()
