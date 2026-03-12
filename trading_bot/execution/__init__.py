"""
Execution Module
============================================================

Auto-generated integration file.
"""

# advanced_algorithms
try:
    from .advanced_algorithms import (
        ExecutionEngine,
    )
except ImportError as e:
    # advanced_algorithms not available
    pass

# advanced_order_management
try:
    from .advanced_order_management import (
        AdvancedOrderManager,
        OrderNotificationSystem,
        OrderQueueManager,
        OrderTimeoutManager,
    )
except ImportError as e:
    # advanced_order_management not available
    pass

# complete_execution_system
try:
    from .complete_execution_system import (
        CompleteExecutionSystem,
    )
except ImportError as e:
    # complete_execution_system not available
    pass

# order_confirmation
try:
    from .order_confirmation import (
        OrderConfirmationSystem,
    )
except ImportError as e:
    # order_confirmation not available
    pass

# order_manager
try:
    from .order_manager import (
        OrderManager,
    )
except ImportError as e:
    # order_manager not available
    pass

# order_state_machine
try:
    from .order_state_machine import (
        BracketOrderManager,
        OCOOrderManager,
    )
except ImportError as e:
    # order_state_machine not available
    pass

# orderexecutionmanager
try:
    from .orderexecutionmanager import (
        OrderExecutionManager,
        OrderExecutionManagerConfig,
    )
except ImportError as e:
    # orderexecutionmanager not available
    pass

# ordermanager
try:
    from .ordermanager import (
        OrderManager,
        OrderManagerConfig,
    )
except ImportError as e:
    # ordermanager not available
    pass

# position_manager
try:
    from .position_manager import (
        PositionManager,
    )
except ImportError as e:
    # position_manager not available
    pass

# smart_execution
try:
    from .smart_execution import (
        SmartExecutionEngine,
    )
except ImportError as e:
    # smart_execution not available
    pass

__all__ = [
    'AdvancedOrderManager',
    'BracketOrderManager',
    'CompleteExecutionSystem',
    'ExecutionEngine',
    'OCOOrderManager',
    'OrderConfirmationSystem',
    'OrderExecutionManager',
    'OrderExecutionManagerConfig',
    'OrderManager',
    'OrderManagerConfig',
    'OrderNotificationSystem',
    'OrderQueueManager',
    'OrderTimeoutManager',
    'PositionManager',
    'SmartExecutionEngine',
]
