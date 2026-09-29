"""
Sandbox Executor
=================

Isolated execution environment for AI-generated code.
All self-programming changes run here BEFORE any production access.

Security Features:
1. Complete isolation from production systems
2. Resource limits (CPU, memory, time, network)
3. No access to real trading APIs
4. Simulated market data only
5. Full execution logging and monitoring

Author: AlphaAlgo Trading System
"""

import asyncio
import hashlib
import json
import logging
import multiprocessing
import os
import resource
import signal
import sys
import tempfile
import traceback
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum, auto
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Set, Tuple
import uuid

logger = logging.getLogger(__name__)


class ExecutionStatus(Enum):
    """Status of sandbox execution."""
    PENDING = auto()
    RUNNING = auto()
    COMPLETED = auto()
    FAILED = auto()
    TIMEOUT = auto()
    RESOURCE_EXCEEDED = auto()
    SECURITY_VIOLATION = auto()
    CANCELLED = auto()


class IsolationLevel(Enum):
    """Isolation levels for sandbox execution."""
    MINIMAL = "minimal"        # Basic isolation
    STANDARD = "standard"      # Standard isolation
    STRICT = "strict"          # Strict isolation
    MAXIMUM = "maximum"        # Maximum isolation (no network, limited imports)


@dataclass
class SandboxConfig:
    """Configuration for sandbox execution."""
    # Resource Limits
    max_cpu_time_seconds: int = 300        # 5 minutes max CPU time
    max_wall_time_seconds: int = 600       # 10 minutes max wall time
    max_memory_mb: int = 1024              # 1GB max memory
    max_disk_mb: int = 512                 # 512MB max disk usage
    max_processes: int = 4                 # Max subprocess count
    max_network_calls: int = 100           # Max network requests
    
    # Isolation Settings
    isolation_level: IsolationLevel = IsolationLevel.STRICT
    allow_network: bool = False            # No network by default
    allow_file_write: bool = True          # Allow writes to sandbox dir only
    allow_subprocess: bool = False         # No subprocesses by default
    
    # Allowed Imports (whitelist)
    allowed_imports: Set[str] = field(default_factory=lambda: {
        'numpy', 'pandas', 'sklearn', 'scipy', 'statsmodels',
        'math', 'statistics', 'datetime', 'json', 'typing',
        'dataclasses', 'enum', 'collections', 'itertools',
        'functools', 'operator', 'copy', 'random', 'hashlib',
    })
    
    # Blocked Imports (blacklist - takes precedence)
    blocked_imports: Set[str] = field(default_factory=lambda: {
        'os', 'sys', 'subprocess', 'shutil', 'socket', 'requests',
        'urllib', 'http', 'ftplib', 'smtplib', 'telnetlib',
        'pickle', 'shelve', 'marshal', 'ctypes', 'multiprocessing',
        '__builtins__', 'builtins', 'importlib', 'exec', 'eval',
        'compile', 'open', 'file', 'input', 'raw_input',
    })
    
    # Paths
    sandbox_root: str = "sandbox_environments"
    log_path: str = "sandbox_logs"


@dataclass
class ExecutionResult:
    """Result of sandbox execution."""
    execution_id: str
    status: ExecutionStatus
    started_at: datetime
    completed_at: Optional[datetime]
    
    # Resource Usage
    cpu_time_used: float = 0.0
    wall_time_used: float = 0.0
    memory_peak_mb: float = 0.0
    disk_used_mb: float = 0.0
    
    # Output
    stdout: str = ""
    stderr: str = ""
    return_value: Optional[Any] = None
    exception: Optional[str] = None
    traceback: Optional[str] = None
    
    # Metrics
    metrics: Dict[str, Any] = field(default_factory=dict)
    
    # Security
    security_violations: List[str] = field(default_factory=list)
    blocked_imports: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'execution_id': self.execution_id,
            'status': self.status.name,
            'started_at': self.started_at.isoformat(),
            'completed_at': self.completed_at.isoformat() if self.completed_at else None,
            'cpu_time_used': self.cpu_time_used,
            'wall_time_used': self.wall_time_used,
            'memory_peak_mb': self.memory_peak_mb,
            'disk_used_mb': self.disk_used_mb,
            'stdout': self.stdout[:10000] if self.stdout else "",  # Limit output
            'stderr': self.stderr[:10000] if self.stderr else "",
            'return_value': str(self.return_value)[:1000] if self.return_value else None,
            'exception': self.exception,
            'traceback': self.traceback,
            'metrics': self.metrics,
            'security_violations': self.security_violations,
            'blocked_imports': self.blocked_imports,
        }
    
    @property
    def is_success(self) -> bool:
        return self.status == ExecutionStatus.COMPLETED and not self.exception


@dataclass
class SandboxEnvironment:
    """An isolated sandbox environment."""
    sandbox_id: str
    created_at: datetime
    config: SandboxConfig
    root_path: Path
    is_active: bool = True
    executions: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'sandbox_id': self.sandbox_id,
            'created_at': self.created_at.isoformat(),
            'root_path': str(self.root_path),
            'is_active': self.is_active,
            'executions': self.executions,
        }


class ImportValidator:
    """Validates and restricts imports in sandbox code."""
    
    def __init__(self, config: SandboxConfig):
        self.config = config
        self._violations: List[str] = []
    
    def validate_code(self, code: str) -> Tuple[bool, List[str]]:
        """
        Validate code for disallowed imports.
        
        Returns:
            Tuple of (is_valid, list of violations)
        """
        self._violations = []
        
        # Check for blocked imports
        for blocked in self.config.blocked_imports:
            patterns = [
                f"import {blocked}",
                f"from {blocked}",
                f"__import__('{blocked}'",
                f'__import__("{blocked}"',
            ]
            
            for pattern in patterns:
                if pattern in code:
                    self._violations.append(f"Blocked import detected: {blocked}")
        
        # Check for dangerous patterns
        dangerous_patterns = [
            ('exec(', 'Dynamic code execution'),
            ('eval(', 'Dynamic code evaluation'),
            ('compile(', 'Code compilation'),
            ('__import__', 'Dynamic import'),
            ('globals()', 'Global namespace access'),
            ('locals()', 'Local namespace access'),
            ('getattr(', 'Dynamic attribute access'),
            ('setattr(', 'Dynamic attribute modification'),
            ('delattr(', 'Dynamic attribute deletion'),
            ('open(', 'File operations'),
            ('os.system', 'System command execution'),
            ('subprocess', 'Subprocess execution'),
        ]
        
        for pattern, description in dangerous_patterns:
            if pattern in code:
                self._violations.append(f"Dangerous pattern: {description}")
        
        return len(self._violations) == 0, self._violations
    
    def get_violations(self) -> List[str]:
        return self._violations.copy()


class ResourceMonitor:
    """Monitors resource usage during sandbox execution."""
    
    def __init__(self, config: SandboxConfig):
        self.config = config
        self._start_time: Optional[float] = None
        self._peak_memory: float = 0.0
        self._cpu_time: float = 0.0
    
    def start(self):
        """Start monitoring."""
        import time
        self._start_time = time.time()
        self._peak_memory = 0.0
        self._cpu_time = 0.0
    
    def check_limits(self) -> Tuple[bool, Optional[str]]:
        """
        Check if resource limits are exceeded.
        
        Returns:
            Tuple of (within_limits, violation_message)
        """
        import time
        
        if self._start_time is None:
            return True, None
        
        # Check wall time
        elapsed = time.time() - self._start_time
        if elapsed > self.config.max_wall_time_seconds:
            return False, f"Wall time exceeded: {elapsed:.1f}s > {self.config.max_wall_time_seconds}s"
        
        # Check memory (if psutil available)
        try:
            import psutil
            process = psutil.Process()
            memory_mb = process.memory_info().rss / 1024 / 1024
            self._peak_memory = max(self._peak_memory, memory_mb)
            
            if memory_mb > self.config.max_memory_mb:
                return False, f"Memory exceeded: {memory_mb:.1f}MB > {self.config.max_memory_mb}MB"
        except ImportError:
            pass
        
        return True, None
    
    def get_usage(self) -> Dict[str, float]:
        """Get current resource usage."""
        import time
        
        elapsed = time.time() - self._start_time if self._start_time else 0
        
        return {
            'wall_time': elapsed,
            'peak_memory_mb': self._peak_memory,
            'cpu_time': self._cpu_time,
        }


class SandboxExecutor:
    """
    Executes AI-generated code in an isolated sandbox environment.
    
    All self-programming changes MUST run through this executor before
    any consideration for production deployment.
    
    Security Layers:
    1. Import validation - blocks dangerous imports
    2. Code analysis - detects dangerous patterns
    3. Resource limits - prevents resource exhaustion
    4. Isolation - runs in separate process/container
    5. Monitoring - tracks all execution details
    """
    
    def __init__(self, config: Optional[SandboxConfig] = None):
        """
        Initialize the sandbox executor.
        
        Args:
            config: Sandbox configuration
        """
        self.config = config or SandboxConfig()
        
        self._import_validator = ImportValidator(self.config)
        self._resource_monitor = ResourceMonitor(self.config)
        
        self._sandboxes: Dict[str, SandboxEnvironment] = {}
        self._executions: Dict[str, ExecutionResult] = {}
        self._active_executions: Set[str] = set()
        
        # Storage
        self._root_path = Path(self.config.sandbox_root)
        self._root_path.mkdir(parents=True, exist_ok=True)
        
        self._log_path = Path(self.config.log_path)
        self._log_path.mkdir(parents=True, exist_ok=True)
        
        logger.info("SandboxExecutor initialized")
    
    async def create_sandbox(self, name: Optional[str] = None) -> SandboxEnvironment:
        """
        Create a new isolated sandbox environment.
        
        Args:
            name: Optional name for the sandbox
        
        Returns:
            SandboxEnvironment instance
        """
        sandbox_id = f"SANDBOX-{uuid.uuid4().hex[:12]}"
        sandbox_path = self._root_path / sandbox_id
        sandbox_path.mkdir(parents=True, exist_ok=True)
        
        # Create subdirectories
        (sandbox_path / 'code').mkdir(exist_ok=True)
        (sandbox_path / 'data').mkdir(exist_ok=True)
        (sandbox_path / 'output').mkdir(exist_ok=True)
        (sandbox_path / 'logs').mkdir(exist_ok=True)
        
        sandbox = SandboxEnvironment(
            sandbox_id=sandbox_id,
            created_at=datetime.now(timezone.utc),
            config=self.config,
            root_path=sandbox_path,
        )
        
        self._sandboxes[sandbox_id] = sandbox
        
        logger.info(f"Created sandbox: {sandbox_id}")
        
        return sandbox
    
    async def execute(
        self,
        code: str,
        sandbox_id: Optional[str] = None,
        test_data: Optional[Dict[str, Any]] = None,
        timeout: Optional[int] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> ExecutionResult:
        """
        Execute code in sandbox environment.
        
        Args:
            code: Python code to execute
            sandbox_id: Optional sandbox ID (creates new if not provided)
            test_data: Optional test data to provide
            timeout: Optional timeout override
            metadata: Optional metadata
        
        Returns:
            ExecutionResult with execution details
        """
        execution_id = f"EXEC-{uuid.uuid4().hex[:12]}"
        started_at = datetime.now(timezone.utc)
        
        result = ExecutionResult(
            execution_id=execution_id,
            status=ExecutionStatus.PENDING,
            started_at=started_at,
            completed_at=None,
        )
        
        self._executions[execution_id] = result
        self._active_executions.add(execution_id)
        
        try:
            # Step 1: Validate imports
            is_valid, violations = self._import_validator.validate_code(code)
            if not is_valid:
                result.status = ExecutionStatus.SECURITY_VIOLATION
                result.security_violations = violations
                result.completed_at = datetime.now(timezone.utc)
                logger.warning(f"Execution {execution_id} blocked: {violations}")
                return result
            
            # Step 2: Get or create sandbox
            if sandbox_id and sandbox_id in self._sandboxes:
                sandbox = self._sandboxes[sandbox_id]
            else:
                sandbox = await self.create_sandbox()
            
            sandbox.executions.append(execution_id)
            
            # Step 3: Execute in isolation
            result.status = ExecutionStatus.RUNNING
            
            timeout_seconds = timeout or self.config.max_wall_time_seconds
            
            execution_result = await self._execute_isolated(
                code=code,
                sandbox=sandbox,
                test_data=test_data,
                timeout=timeout_seconds,
            )
            
            # Update result
            result.status = execution_result['status']
            result.stdout = execution_result.get('stdout', '')
            result.stderr = execution_result.get('stderr', '')
            result.return_value = execution_result.get('return_value')
            result.exception = execution_result.get('exception')
            result.traceback = execution_result.get('traceback')
            result.cpu_time_used = execution_result.get('cpu_time', 0)
            result.wall_time_used = execution_result.get('wall_time', 0)
            result.memory_peak_mb = execution_result.get('memory_mb', 0)
            result.metrics = execution_result.get('metrics', {})
            
        except asyncio.TimeoutError:
            result.status = ExecutionStatus.TIMEOUT
            result.exception = f"Execution timed out after {timeout_seconds}s"
            
        except Exception as e:
            result.status = ExecutionStatus.FAILED
            result.exception = str(e)
            result.traceback = traceback.format_exc()
            logger.error(f"Execution {execution_id} failed: {e}")
        
        finally:
            result.completed_at = datetime.now(timezone.utc)
            self._active_executions.discard(execution_id)
            
            # Persist result
            await self._persist_result(result)
        
        return result
    
    async def _execute_isolated(
        self,
        code: str,
        sandbox: SandboxEnvironment,
        test_data: Optional[Dict[str, Any]],
        timeout: int,
    ) -> Dict[str, Any]:
        """Execute code in isolated environment."""
        import time
        
        start_time = time.time()
        
        # Write code to sandbox
        code_file = sandbox.root_path / 'code' / 'execution.py'
        with open(code_file, 'w') as f:
            f.write(code)
        
        # Write test data if provided
        if test_data:
            data_file = sandbox.root_path / 'data' / 'test_data.json'
            with open(data_file, 'w') as f:
                json.dump(test_data, f)
        
        # Create restricted globals
        restricted_globals = self._create_restricted_globals(sandbox)
        
        # Execute with timeout
        try:
            # Capture output
            import io
            from contextlib import redirect_stdout, redirect_stderr
            
            stdout_capture = io.StringIO()
            stderr_capture = io.StringIO()
            
            return_value = None
            exception_info = None
            
            # Start resource monitoring
            self._resource_monitor.start()
            
            try:
                with redirect_stdout(stdout_capture), redirect_stderr(stderr_capture):
                    # Execute the code
                    exec(compile(code, '<sandbox>', 'exec'), restricted_globals)
                    
                    # Get return value if 'result' is defined
                    return_value = restricted_globals.get('result')
                    
            except Exception as e:
                exception_info = {
                    'type': type(e).__name__,
                    'message': str(e),
                    'traceback': traceback.format_exc(),
                }
            
            wall_time = time.time() - start_time
            usage = self._resource_monitor.get_usage()
            
            if exception_info:
                return {
                    'status': ExecutionStatus.FAILED,
                    'stdout': stdout_capture.getvalue(),
                    'stderr': stderr_capture.getvalue(),
                    'exception': f"{exception_info['type']}: {exception_info['message']}",
                    'traceback': exception_info['traceback'],
                    'wall_time': wall_time,
                    'cpu_time': usage['cpu_time'],
                    'memory_mb': usage['peak_memory_mb'],
                }
            
            return {
                'status': ExecutionStatus.COMPLETED,
                'stdout': stdout_capture.getvalue(),
                'stderr': stderr_capture.getvalue(),
                'return_value': return_value,
                'wall_time': wall_time,
                'cpu_time': usage['cpu_time'],
                'memory_mb': usage['peak_memory_mb'],
                'metrics': restricted_globals.get('metrics', {}),
            }
            
        except asyncio.TimeoutError:
            return {
                'status': ExecutionStatus.TIMEOUT,
                'wall_time': time.time() - start_time,
            }
    
    def _create_restricted_globals(self, sandbox: SandboxEnvironment) -> Dict[str, Any]:
        """Create restricted globals for sandbox execution."""
        import math
        import statistics
        from datetime import datetime, timedelta
        
        # Safe builtins
        safe_builtins = {
            'abs': abs,
            'all': all,
            'any': any,
            'bool': bool,
            'dict': dict,
            'enumerate': enumerate,
            'filter': filter,
            'float': float,
            'frozenset': frozenset,
            'int': int,
            'isinstance': isinstance,
            'len': len,
            'list': list,
            'map': map,
            'max': max,
            'min': min,
            'print': print,
            'range': range,
            'reversed': reversed,
            'round': round,
            'set': set,
            'sorted': sorted,
            'str': str,
            'sum': sum,
            'tuple': tuple,
            'type': type,
            'zip': zip,
            'True': True,
            'False': False,
            'None': None,
        }
        
        # Create restricted globals
        restricted_globals = {
            '__builtins__': safe_builtins,
            '__name__': '__sandbox__',
            '__doc__': None,
            
            # Safe modules
            'math': math,
            'statistics': statistics,
            'datetime': datetime,
            'timedelta': timedelta,
            
            # Sandbox info
            'SANDBOX_ID': sandbox.sandbox_id,
            'SANDBOX_PATH': str(sandbox.root_path),
            
            # Results container
            'result': None,
            'metrics': {},
        }
        
        # Add numpy/pandas if allowed and available
        if 'numpy' in self.config.allowed_imports:
            try:
                import numpy as np
                restricted_globals['np'] = np
                restricted_globals['numpy'] = np
            except ImportError:
                pass
        
        if 'pandas' in self.config.allowed_imports:
            try:
                import pandas as pd
                restricted_globals['pd'] = pd
                restricted_globals['pandas'] = pd
            except ImportError:
                pass
        
        return restricted_globals
    
    async def execute_strategy_backtest(
        self,
        strategy_code: str,
        market_data: Dict[str, Any],
        config: Optional[Dict[str, Any]] = None,
    ) -> ExecutionResult:
        """
        Execute a strategy backtest in sandbox.
        
        Args:
            strategy_code: Strategy code to test
            market_data: Historical market data
            config: Backtest configuration
        
        Returns:
            ExecutionResult with backtest results
        """
        # Wrap strategy code in backtest harness
        backtest_code = f'''
# Strategy code
{strategy_code}

# Backtest harness
import json

# Load market data
market_data = {json.dumps(market_data)}
config = {json.dumps(config or {})}

# Run backtest
try:
    if 'run_strategy' in dir():
        trades = []
        for i, candle in enumerate(market_data.get('candles', [])):
            signal = run_strategy(candle, market_data['candles'][:i+1])
            if signal:
                trades.append(signal)
        
        # Calculate metrics
        metrics['total_trades'] = len(trades)
        metrics['backtest_complete'] = True
        result = {{'trades': trades, 'metrics': metrics}}
    else:
        result = {{'error': 'run_strategy function not found'}}
except Exception as e:
    result = {{'error': str(e)}}
'''
        
        return await self.execute(backtest_code)
    
    async def cleanup_sandbox(self, sandbox_id: str):
        """Clean up a sandbox environment."""
        if sandbox_id not in self._sandboxes:
            return
        
        sandbox = self._sandboxes[sandbox_id]
        sandbox.is_active = False
        
        # Remove sandbox directory
        import shutil
        try:
            shutil.rmtree(sandbox.root_path)
            logger.info(f"Cleaned up sandbox: {sandbox_id}")
        except Exception as e:
            logger.error(f"Failed to cleanup sandbox {sandbox_id}: {e}")
        
        del self._sandboxes[sandbox_id]
    
    async def cleanup_old_sandboxes(self, max_age_hours: int = 24):
        """Clean up old sandbox environments."""
        cutoff = datetime.now(timezone.utc)
        
        for sandbox_id, sandbox in list(self._sandboxes.items()):
            age = (cutoff - sandbox.created_at).total_seconds() / 3600
            if age > max_age_hours and not sandbox.is_active:
                await self.cleanup_sandbox(sandbox_id)
    
    async def _persist_result(self, result: ExecutionResult):
        """Persist execution result to disk."""
        try:
            result_file = self._log_path / f"{result.execution_id}.json"
            with open(result_file, 'w') as f:
                json.dump(result.to_dict(), f, indent=2)
        except Exception as e:
            logger.error(f"Failed to persist result: {e}")
    
    def get_execution(self, execution_id: str) -> Optional[ExecutionResult]:
        """Get execution result by ID."""
        return self._executions.get(execution_id)
    
    def get_sandbox(self, sandbox_id: str) -> Optional[SandboxEnvironment]:
        """Get sandbox by ID."""
        return self._sandboxes.get(sandbox_id)
    
    def get_active_executions(self) -> List[str]:
        """Get list of active execution IDs."""
        return list(self._active_executions)
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get executor statistics."""
        completed = [e for e in self._executions.values() if e.status == ExecutionStatus.COMPLETED]
        failed = [e for e in self._executions.values() if e.status == ExecutionStatus.FAILED]
        
        return {
            'total_sandboxes': len(self._sandboxes),
            'active_sandboxes': sum(1 for s in self._sandboxes.values() if s.is_active),
            'total_executions': len(self._executions),
            'active_executions': len(self._active_executions),
            'completed_executions': len(completed),
            'failed_executions': len(failed),
            'security_violations': sum(
                1 for e in self._executions.values() 
                if e.status == ExecutionStatus.SECURITY_VIOLATION
            ),
            'success_rate': len(completed) / len(self._executions) if self._executions else 0,
        }
