"""
Task Distributor
================

Distributed task execution across multiple workers.
"""

import asyncio
import logging
import uuid
import time
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Dict, List, Optional, Any, Callable, Awaitable
from collections import deque
import threading
import multiprocessing as mp
from concurrent.futures import ProcessPoolExecutor, ThreadPoolExecutor, as_completed
import pickle

logger = logging.getLogger(__name__)


class TaskStatus(Enum):
    """Task execution status"""
    PENDING = "pending"
    QUEUED = "queued"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    TIMEOUT = "timeout"


class TaskPriority(Enum):
    """Task priority levels"""
    CRITICAL = 0
    HIGH = 1
    NORMAL = 2
    LOW = 3
    BACKGROUND = 4


@dataclass
class DistributedTask:
    """Distributed task definition"""
    task_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = ""
    func: Optional[Callable] = None
    args: tuple = field(default_factory=tuple)
    kwargs: Dict[str, Any] = field(default_factory=dict)
    priority: TaskPriority = TaskPriority.NORMAL
    timeout: float = 300.0  # seconds
    retries: int = 3
    created_at: datetime = field(default_factory=datetime.now)
    status: TaskStatus = TaskStatus.PENDING
    worker_id: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'task_id': self.task_id,
            'name': self.name,
            'priority': self.priority.value,
            'timeout': self.timeout,
            'retries': self.retries,
            'created_at': self.created_at.isoformat(),
            'status': self.status.value,
            'worker_id': self.worker_id
        }


@dataclass
class TaskResult:
    """Task execution result"""
    task_id: str
    status: TaskStatus
    result: Any = None
    error: Optional[str] = None
    execution_time: float = 0.0
    worker_id: Optional[str] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    retries_used: int = 0


@dataclass
class WorkerNode:
    """Worker node information"""
    worker_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = ""
    host: str = "localhost"
    port: int = 0
    max_tasks: int = 4
    current_tasks: int = 0
    is_active: bool = True
    last_heartbeat: datetime = field(default_factory=datetime.now)
    total_tasks_completed: int = 0
    total_tasks_failed: int = 0
    avg_execution_time: float = 0.0
    
    @property
    def is_available(self) -> bool:
        return self.is_active and self.current_tasks < self.max_tasks
        
    @property
    def load(self) -> float:
        return self.current_tasks / self.max_tasks if self.max_tasks > 0 else 1.0


class TaskQueue:
    """Priority task queue"""
    
    def __init__(self, max_size: int = 10000):
        self.max_size = max_size
        self._queues: Dict[TaskPriority, deque] = {
            p: deque() for p in TaskPriority
        }
        self._lock = threading.Lock()
        self._task_count = 0
        
    def put(self, task: DistributedTask) -> bool:
        """Add task to queue"""
        with self._lock:
            if self._task_count >= self.max_size:
                return False
            self._queues[task.priority].append(task)
            self._task_count += 1
            task.status = TaskStatus.QUEUED
            return True
            
    def get(self) -> Optional[DistributedTask]:
        """Get highest priority task"""
        with self._lock:
            for priority in TaskPriority:
                if self._queues[priority]:
                    self._task_count -= 1
                    return self._queues[priority].popleft()
            return None
            
    def peek(self) -> Optional[DistributedTask]:
        """Peek at highest priority task without removing"""
        with self._lock:
            for priority in TaskPriority:
                if self._queues[priority]:
                    return self._queues[priority][0]
            return None
            
    def size(self) -> int:
        """Get total queue size"""
        return self._task_count
        
    def size_by_priority(self) -> Dict[str, int]:
        """Get queue size by priority"""
        with self._lock:
            return {p.name: len(q) for p, q in self._queues.items()}


class LocalWorkerPool:
    """Local process/thread pool for task execution"""
    
    def __init__(
        self,
        num_workers: int = None,
        use_processes: bool = True
    ):
        self.num_workers = num_workers or mp.cpu_count()
        self.use_processes = use_processes
        self._executor = None
        self._running_tasks: Dict[str, Any] = {}
        self._lock = threading.Lock()
        
    def start(self):
        """Start worker pool"""
        if self.use_processes:
            self._executor = ProcessPoolExecutor(max_workers=self.num_workers)
        else:
            self._executor = ThreadPoolExecutor(max_workers=self.num_workers)
        logger.info(f"Started {'process' if self.use_processes else 'thread'} pool with {self.num_workers} workers")
        
    def stop(self):
        """Stop worker pool"""
        if self._executor:
            self._executor.shutdown(wait=True)
            self._executor = None
            
    def submit(self, task: DistributedTask) -> TaskResult:
        """Submit task for execution"""
        if not self._executor:
            return TaskResult(
                task_id=task.task_id,
                status=TaskStatus.FAILED,
                error="Worker pool not started"
            )
            
        start_time = time.time()
        task.status = TaskStatus.RUNNING
        
        try:
            future = self._executor.submit(task.func, *task.args, **task.kwargs)
            
            with self._lock:
                self._running_tasks[task.task_id] = future
                
            result = future.result(timeout=task.timeout)
            
            return TaskResult(
                task_id=task.task_id,
                status=TaskStatus.COMPLETED,
                result=result,
                execution_time=time.time() - start_time,
                started_at=datetime.now() - timedelta(seconds=time.time() - start_time),
                completed_at=datetime.now()
            )
            
        except TimeoutError:
            return TaskResult(
                task_id=task.task_id,
                status=TaskStatus.TIMEOUT,
                error=f"Task timed out after {task.timeout}s",
                execution_time=time.time() - start_time
            )
        except Exception as e:
            return TaskResult(
                task_id=task.task_id,
                status=TaskStatus.FAILED,
                error=str(e),
                execution_time=time.time() - start_time
            )
        finally:
            with self._lock:
                self._running_tasks.pop(task.task_id, None)
                
    async def submit_async(self, task: DistributedTask) -> TaskResult:
        """Submit task asynchronously"""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self.submit, task)
        
    def cancel(self, task_id: str) -> bool:
        """Cancel a running task"""
        with self._lock:
            future = self._running_tasks.get(task_id)
            if future:
                return future.cancel()
            return False
            
    @property
    def active_tasks(self) -> int:
        """Get number of active tasks"""
        with self._lock:
            return len(self._running_tasks)


class TaskDistributor:
    """
    Distributed task execution system.
    
    Features:
    - Priority-based task queue
    - Local process/thread pool execution
    - Task retry with backoff
    - Timeout handling
    - Result caching
    - Statistics tracking
    """
    
    def __init__(
        self,
        num_workers: int = None,
        use_processes: bool = True,
        max_queue_size: int = 10000
    ):
        self.queue = TaskQueue(max_queue_size)
        self.worker_pool = LocalWorkerPool(num_workers, use_processes)
        self._results: Dict[str, TaskResult] = {}
        self._callbacks: Dict[str, List[Callable]] = {}
        self._running = False
        self._processor_task = None
        self._lock = threading.Lock()
        
        # Statistics
        self._stats = {
            'total_submitted': 0,
            'total_completed': 0,
            'total_failed': 0,
            'total_timeout': 0,
            'total_retried': 0,
            'avg_execution_time': 0.0,
            'avg_queue_time': 0.0
        }
        
    def start(self):
        """Start the task distributor"""
        self.worker_pool.start()
        self._running = True
        logger.info("TaskDistributor started")
        
    def stop(self):
        """Stop the task distributor"""
        self._running = False
        self.worker_pool.stop()
        logger.info("TaskDistributor stopped")
        
    def submit(
        self,
        func: Callable,
        *args,
        name: str = "",
        priority: TaskPriority = TaskPriority.NORMAL,
        timeout: float = 300.0,
        retries: int = 3,
        callback: Optional[Callable] = None,
        **kwargs
    ) -> str:
        """
        Submit a task for execution.
        
        Args:
            func: Function to execute
            *args: Positional arguments
            name: Task name
            priority: Task priority
            timeout: Timeout in seconds
            retries: Number of retries
            callback: Callback on completion
            **kwargs: Keyword arguments
            
        Returns:
            Task ID
        """
        task = DistributedTask(
            name=name or func.__name__,
            func=func,
            args=args,
            kwargs=kwargs,
            priority=priority,
            timeout=timeout,
            retries=retries
        )
        
        if callback:
            self._callbacks[task.task_id] = [callback]
            
        if self.queue.put(task):
            self._stats['total_submitted'] += 1
            logger.debug(f"Task {task.task_id} submitted: {task.name}")
            return task.task_id
        else:
            logger.error("Task queue full")
            return ""
            
    async def submit_async(
        self,
        func: Callable,
        *args,
        **kwargs
    ) -> str:
        """Submit task asynchronously"""
        return self.submit(func, *args, **kwargs)
        
    def execute_sync(
        self,
        func: Callable,
        *args,
        timeout: float = 300.0,
        **kwargs
    ) -> TaskResult:
        """Execute task synchronously and wait for result"""
        task = DistributedTask(
            name=func.__name__,
            func=func,
            args=args,
            kwargs=kwargs,
            timeout=timeout
        )
        
        result = self.worker_pool.submit(task)
        self._update_stats(result)
        return result
        
    async def execute_async(
        self,
        func: Callable,
        *args,
        timeout: float = 300.0,
        **kwargs
    ) -> TaskResult:
        """Execute task asynchronously and wait for result"""
        task = DistributedTask(
            name=func.__name__,
            func=func,
            args=args,
            kwargs=kwargs,
            timeout=timeout
        )
        
        result = await self.worker_pool.submit_async(task)
        self._update_stats(result)
        return result
        
    async def process_queue(self):
        """Process tasks from queue"""
        while self._running:
            task = self.queue.get()
            
            if task is None:
                await asyncio.sleep(0.1)
                continue
                
            # Execute task with retries
            retries_left = task.retries
            result = None
            
            while retries_left >= 0:
                result = await self.worker_pool.submit_async(task)
                
                if result.status == TaskStatus.COMPLETED:
                    break
                    
                retries_left -= 1
                if retries_left >= 0:
                    self._stats['total_retried'] += 1
                    await asyncio.sleep(2 ** (task.retries - retries_left))  # Exponential backoff
                    
            result.retries_used = task.retries - retries_left
            
            # Store result
            with self._lock:
                self._results[task.task_id] = result
                
            # Update stats
            self._update_stats(result)
            
            # Call callbacks
            if task.task_id in self._callbacks:
                for callback in self._callbacks[task.task_id]:
                    try:
                        if asyncio.iscoroutinefunction(callback):
                            await callback(result)
                        else:
                            callback(result)
                    except Exception as e:
                        logger.error(f"Callback error: {e}")
                del self._callbacks[task.task_id]
                
    def _update_stats(self, result: TaskResult):
        """Update statistics"""
        if result.status == TaskStatus.COMPLETED:
            self._stats['total_completed'] += 1
        elif result.status == TaskStatus.FAILED:
            self._stats['total_failed'] += 1
        elif result.status == TaskStatus.TIMEOUT:
            self._stats['total_timeout'] += 1
            
        # Update average execution time
        total = self._stats['total_completed'] + self._stats['total_failed']
        if total > 0:
            self._stats['avg_execution_time'] = (
                (self._stats['avg_execution_time'] * (total - 1) + result.execution_time) / total
            )
            
    def get_result(self, task_id: str) -> Optional[TaskResult]:
        """Get task result"""
        with self._lock:
            return self._results.get(task_id)
            
    def cancel(self, task_id: str) -> bool:
        """Cancel a task"""
        return self.worker_pool.cancel(task_id)
        
    def get_stats(self) -> Dict[str, Any]:
        """Get distributor statistics"""
        return {
            **self._stats,
            'queue_size': self.queue.size(),
            'queue_by_priority': self.queue.size_by_priority(),
            'active_tasks': self.worker_pool.active_tasks,
            'num_workers': self.worker_pool.num_workers
        }
        
    def map(
        self,
        func: Callable,
        items: List[Any],
        **kwargs
    ) -> List[str]:
        """
        Map function over items (parallel map).
        
        Args:
            func: Function to apply
            items: List of items
            **kwargs: Additional task options
            
        Returns:
            List of task IDs
        """
        task_ids = []
        for item in items:
            task_id = self.submit(func, item, **kwargs)
            if task_id:
                task_ids.append(task_id)
        return task_ids
        
    async def map_async(
        self,
        func: Callable,
        items: List[Any],
        timeout: float = 300.0
    ) -> List[TaskResult]:
        """
        Map function over items and wait for all results.
        
        Args:
            func: Function to apply
            items: List of items
            timeout: Timeout per task
            
        Returns:
            List of TaskResults
        """
        tasks = [
            self.execute_async(func, item, timeout=timeout)
            for item in items
        ]
        return await asyncio.gather(*tasks)


def create_task_distributor(
    num_workers: int = None,
    use_processes: bool = True
) -> TaskDistributor:
    """Factory function to create TaskDistributor"""
    distributor = TaskDistributor(num_workers, use_processes)
    distributor.start()
    return distributor


# Example task functions
def compute_heavy_task(n: int) -> int:
    """Example CPU-intensive task"""
    result = 0
    for i in range(n):
        result += i ** 2
    return result


def fetch_data_task(symbol: str) -> Dict[str, Any]:
    """Example I/O task"""
    time.sleep(0.5)  # Simulate network delay
    return {'symbol': symbol, 'price': 100.0}


if __name__ == "__main__":
    async def main():
        print("=== Task Distributor Demo ===\n")
        
        distributor = create_task_distributor(num_workers=4, use_processes=False)
        
        try:
            # Single task execution
            print("1. Single task execution:")
            result = await distributor.execute_async(compute_heavy_task, 100000)
            print(f"   Result: {result.result}, Time: {result.execution_time:.3f}s")
            
            # Parallel map
            print("\n2. Parallel map:")
            items = [10000, 20000, 30000, 40000, 50000]
            results = await distributor.map_async(compute_heavy_task, items)
            for i, r in enumerate(results):
                print(f"   Item {items[i]}: {r.result}, Time: {r.execution_time:.3f}s")
                
            # Statistics
            print("\n3. Statistics:")
            stats = distributor.get_stats()
            print(f"   Total completed: {stats['total_completed']}")
            print(f"   Avg execution time: {stats['avg_execution_time']:.3f}s")
            
        finally:
            distributor.stop()
            
    asyncio.run(main())
