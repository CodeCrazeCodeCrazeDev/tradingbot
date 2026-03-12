"""
distributed package
"""

try:
    from .parallel_backtester import (
        BacktestConfig,
        BacktestEngine,
        BacktestJob,
        BacktestResult,
        BacktestStatus,
        EXAMPLE_STRATEGY,
        ParallelBacktester,
        TradeRecord,
        create_parallel_backtester
    )
    from .task_distributor import (
        DistributedTask,
        LocalWorkerPool,
        TaskDistributor,
        TaskPriority,
        TaskQueue,
        TaskResult,
        TaskStatus,
        WorkerNode,
        compute_heavy_task,
        create_task_distributor,
        fetch_data_task
    )
except ImportError as e:
    import logging
    logging.getLogger(__name__).debug(f'Optional import failed in distributed: {e}')

__all__ = [
    'BacktestConfig',
    'BacktestEngine',
    'BacktestJob',
    'BacktestResult',
    'BacktestStatus',
    'DistributedTask',
    'EXAMPLE_STRATEGY',
    'LocalWorkerPool',
    'ParallelBacktester',
    'TaskDistributor',
    'TaskPriority',
    'TaskQueue',
    'TaskResult',
    'TaskStatus',
    'TradeRecord',
    'WorkerNode',
    'compute_heavy_task',
    'create_parallel_backtester',
    'create_task_distributor',
    'fetch_data_task',
]