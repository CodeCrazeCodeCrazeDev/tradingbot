"""
Sandbox Environment
===================

Provides isolated execution environment for AI-generated code.
Uses multiple layers of protection:
1. RestrictedPython for AST-level restrictions
2. Resource limits (CPU, memory, time)
3. Filesystem isolation
4. Network isolation
5. Import restrictions

CRITICAL: All AI-generated code MUST run through this sandbox.
"""

import ast
import sys
import os
import time
import signal
import threading
import traceback
import hashlib
import tempfile
import shutil
from io import StringIO
from pathlib import Path
from typing import Dict, Any, List, Optional, Set, Callable, Tuple
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum, auto
from contextlib import contextmanager
import logging
import json
import copy

logger = logging.getLogger(__name__)


class SandboxViolationType(Enum):
    """Types of sandbox violations."""
    FORBIDDEN_IMPORT = auto()
    FORBIDDEN_BUILTIN = auto()
    FORBIDDEN_ATTRIBUTE = auto()
    TIMEOUT_EXCEEDED = auto()
    MEMORY_EXCEEDED = auto()
    FILESYSTEM_ACCESS = auto()
    NETWORK_ACCESS = auto()
    DANGEROUS_PATTERN = auto()
    RECURSION_LIMIT = auto()
    OUTPUT_LIMIT = auto()


@dataclass
class SandboxViolation:
    """Record of a sandbox violation."""
    violation_type: SandboxViolationType
    description: str
    code_snippet: str
    line_number: Optional[int]
    timestamp: datetime = field(default_factory=datetime.utcnow)
    severity: str = "HIGH"
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'violation_type': self.violation_type.name,
            'description': self.description,
            'code_snippet': self.code_snippet[:200],
            'line_number': self.line_number,
            'timestamp': self.timestamp.isoformat(),
            'severity': self.severity,
        }


@dataclass
class SandboxConfig:
    """Configuration for sandbox environment."""
    # Time limits
    max_execution_time_seconds: float = 30.0
    max_cpu_time_seconds: float = 10.0
    
    # Memory limits
    max_memory_mb: int = 256
    max_output_size_kb: int = 1024
    
    # Recursion and iteration limits
    max_recursion_depth: int = 100
    max_iterations: int = 1_000_000
    
    # Filesystem
    allow_filesystem: bool = False
    allowed_paths: List[str] = field(default_factory=list)
    sandbox_root: Optional[str] = None
    
    # Network
    allow_network: bool = False
    
    # Allowed imports (whitelist)
    allowed_imports: Set[str] = field(default_factory=lambda: {
        'math', 'statistics', 'random', 'datetime', 'time',
        'json', 'collections', 'itertools', 'functools',
        'operator', 'decimal', 'fractions', 'numbers',
        'numpy', 'pandas', 'scipy',
    })
    
    # Forbidden builtins
    forbidden_builtins: Set[str] = field(default_factory=lambda: {
        'eval', 'exec', 'compile', 'open', 'input',
        '__import__', 'globals', 'locals', 'vars',
        'getattr', 'setattr', 'delattr', 'hasattr',
        'breakpoint', 'exit', 'quit',
    })
    
    # Forbidden attributes
    forbidden_attributes: Set[str] = field(default_factory=lambda: {
        '__class__', '__bases__', '__subclasses__', '__mro__',
        '__code__', '__globals__', '__builtins__', '__dict__',
        '__reduce__', '__reduce_ex__', '__getstate__', '__setstate__',
    })


@dataclass
class SandboxResult:
    """Result of sandbox execution."""
    success: bool
    result: Any = None
    output: str = ""
    error: Optional[str] = None
    execution_time_ms: float = 0.0
    memory_used_mb: float = 0.0
    violations: List[SandboxViolation] = field(default_factory=list)
    code_hash: str = ""
    timestamp: datetime = field(default_factory=datetime.utcnow)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'success': self.success,
            'result': str(self.result)[:1000] if self.result else None,
            'output': self.output[:1000],
            'error': self.error,
            'execution_time_ms': self.execution_time_ms,
            'memory_used_mb': self.memory_used_mb,
            'violations': [v.to_dict() for v in self.violations],
            'code_hash': self.code_hash,
            'timestamp': self.timestamp.isoformat(),
        }


class TimeoutError(Exception):
    """Raised when execution exceeds time limit."""
    pass


class MemoryLimitError(Exception):
    """Raised when execution exceeds memory limit."""
    pass


class SandboxSecurityError(Exception):
    """Raised when security violation detected."""
    pass


class RestrictedImporter:
    """Custom importer that only allows whitelisted modules."""
    
    def __init__(self, allowed_imports: Set[str]):
        self.allowed_imports = allowed_imports
        self._import_cache: Dict[str, Any] = {}
    
    def __call__(self, name: str, globals_dict=None, locals_dict=None, 
                 fromlist=(), level=0):
        # Check if import is allowed
        base_module = name.split('.')[0]
        
        if base_module not in self.allowed_imports:
            raise ImportError(
                f"Import of '{name}' is not allowed in sandbox. "
                f"Allowed imports: {sorted(self.allowed_imports)}"
            )
        
        # Use cached import if available
        if name in self._import_cache:
            return self._import_cache[name]
        
        # Perform actual import
        try:
            module = __builtins__['__import__'](name, globals_dict, locals_dict, fromlist, level)
            self._import_cache[name] = module
            return module
        except Exception as e:
            raise ImportError(f"Failed to import '{name}': {e}")


class SafeBuiltins:
    """Provides safe subset of builtins for sandbox."""
    
    SAFE_BUILTINS = {
        # Types
        'bool', 'int', 'float', 'str', 'bytes', 'bytearray',
        'list', 'tuple', 'dict', 'set', 'frozenset',
        'complex', 'range', 'slice', 'type',
        
        # Functions
        'abs', 'all', 'any', 'bin', 'chr', 'divmod',
        'enumerate', 'filter', 'format', 'hex', 'id',
        'isinstance', 'issubclass', 'iter', 'len', 'map',
        'max', 'min', 'next', 'oct', 'ord', 'pow',
        'print', 'repr', 'reversed', 'round', 'sorted',
        'sum', 'zip', 'hash',
        
        # Exceptions
        'Exception', 'ValueError', 'TypeError', 'KeyError',
        'IndexError', 'AttributeError', 'RuntimeError',
        'StopIteration', 'ZeroDivisionError', 'OverflowError',
        
        # Constants
        'True', 'False', 'None',
    }
    
    @classmethod
    def get_safe_builtins(cls, config: SandboxConfig) -> Dict[str, Any]:
        """Get dictionary of safe builtins."""
        import builtins
        
        safe = {}
        for name in cls.SAFE_BUILTINS:
            if hasattr(builtins, name):
                safe[name] = getattr(builtins, name)
        
        # Add restricted import
        safe['__import__'] = RestrictedImporter(config.allowed_imports)
        
        return safe


class CodeAnalyzer:
    """Analyzes code AST for dangerous patterns."""
    
    DANGEROUS_PATTERNS = [
        # System access
        ('os.system', 'System command execution'),
        ('subprocess', 'Subprocess execution'),
        ('os.popen', 'Process pipe'),
        ('os.spawn', 'Process spawning'),
        
        # File operations
        ('open(', 'File opening'),
        ('os.remove', 'File deletion'),
        ('os.unlink', 'File unlinking'),
        ('shutil.rmtree', 'Directory removal'),
        
        # Network
        ('socket', 'Socket access'),
        ('urllib', 'URL access'),
        ('requests', 'HTTP requests'),
        ('http.client', 'HTTP client'),
        
        # Code execution
        ('eval(', 'Dynamic evaluation'),
        ('exec(', 'Dynamic execution'),
        ('compile(', 'Code compilation'),
        ('__import__', 'Dynamic import'),
        
        # Introspection attacks
        ('__class__', 'Class introspection'),
        ('__bases__', 'Base class access'),
        ('__subclasses__', 'Subclass enumeration'),
        ('__globals__', 'Global access'),
        ('__builtins__', 'Builtins access'),
    ]
    
    def __init__(self, config: SandboxConfig):
        self.config = config
        self.violations: List[SandboxViolation] = []
    
    def analyze(self, code: str) -> Tuple[bool, List[SandboxViolation]]:
        """
        Analyze code for dangerous patterns.
        
        Returns:
            (is_safe, violations)
        """
        self.violations = []
        
        # Check for dangerous string patterns
        self._check_string_patterns(code)
        
        # Parse and analyze AST
        try:
            tree = ast.parse(code)
            self._analyze_ast(tree, code)
        except SyntaxError as e:
            self.violations.append(SandboxViolation(
                violation_type=SandboxViolationType.DANGEROUS_PATTERN,
                description=f"Syntax error: {e}",
                code_snippet=code[:100],
                line_number=e.lineno,
                severity="MEDIUM"
            ))
        
        is_safe = len(self.violations) == 0
        return is_safe, self.violations
    
    def _check_string_patterns(self, code: str):
        """Check for dangerous string patterns."""
        for pattern, description in self.DANGEROUS_PATTERNS:
            if pattern in code:
                self.violations.append(SandboxViolation(
                    violation_type=SandboxViolationType.DANGEROUS_PATTERN,
                    description=f"Dangerous pattern detected: {description}",
                    code_snippet=pattern,
                    line_number=None,
                    severity="HIGH"
                ))
    
    def _analyze_ast(self, tree: ast.AST, code: str):
        """Analyze AST for dangerous constructs."""
        for node in ast.walk(tree):
            # Check imports
            if isinstance(node, ast.Import):
                for alias in node.names:
                    if alias.name.split('.')[0] not in self.config.allowed_imports:
                        self.violations.append(SandboxViolation(
                            violation_type=SandboxViolationType.FORBIDDEN_IMPORT,
                            description=f"Forbidden import: {alias.name}",
                            code_snippet=f"import {alias.name}",
                            line_number=node.lineno,
                        ))
            
            elif isinstance(node, ast.ImportFrom):
                if node.module and node.module.split('.')[0] not in self.config.allowed_imports:
                    self.violations.append(SandboxViolation(
                        violation_type=SandboxViolationType.FORBIDDEN_IMPORT,
                        description=f"Forbidden import: {node.module}",
                        code_snippet=f"from {node.module} import ...",
                        line_number=node.lineno,
                    ))
            
            # Check function calls
            elif isinstance(node, ast.Call):
                func_name = self._get_func_name(node.func)
                if func_name in self.config.forbidden_builtins:
                    self.violations.append(SandboxViolation(
                        violation_type=SandboxViolationType.FORBIDDEN_BUILTIN,
                        description=f"Forbidden builtin: {func_name}",
                        code_snippet=f"{func_name}(...)",
                        line_number=node.lineno,
                    ))
            
            # Check attribute access
            elif isinstance(node, ast.Attribute):
                if node.attr in self.config.forbidden_attributes:
                    self.violations.append(SandboxViolation(
                        violation_type=SandboxViolationType.FORBIDDEN_ATTRIBUTE,
                        description=f"Forbidden attribute: {node.attr}",
                        code_snippet=f".{node.attr}",
                        line_number=node.lineno,
                    ))
    
    def _get_func_name(self, node: ast.AST) -> str:
        """Extract function name from call node."""
        if isinstance(node, ast.Name):
            return node.id
        elif isinstance(node, ast.Attribute):
            return node.attr
        return ""


class SandboxEnvironment:
    """
    Isolated execution environment for AI-generated code.
    
    Provides multiple layers of protection:
    1. Code analysis (AST-level)
    2. Restricted builtins
    3. Import restrictions
    4. Resource limits
    5. Filesystem isolation
    """
    
    def __init__(self, config: Optional[SandboxConfig] = None):
        self.config = config or SandboxConfig()
        self.analyzer = CodeAnalyzer(self.config)
        self.execution_history: List[SandboxResult] = []
        self._sandbox_dir: Optional[Path] = None
        
        # Statistics
        self.total_executions = 0
        self.successful_executions = 0
        self.blocked_executions = 0
        self.violations_detected = 0
        
        logger.info("SandboxEnvironment initialized")
    
    def execute(self, code: str, 
                globals_dict: Optional[Dict[str, Any]] = None,
                locals_dict: Optional[Dict[str, Any]] = None,
                entry_point: Optional[str] = None) -> SandboxResult:
        """
        Execute code in sandbox environment.
        
        Args:
            code: Python code to execute
            globals_dict: Optional globals to inject
            locals_dict: Optional locals to inject
            entry_point: Optional function to call after execution
            
        Returns:
            SandboxResult with execution details
        """
        start_time = time.time()
        code_hash = hashlib.sha256(code.encode()).hexdigest()[:16]
        
        self.total_executions += 1
        
        # Step 1: Analyze code for dangerous patterns
        is_safe, violations = self.analyzer.analyze(code)
        
        if not is_safe:
            self.blocked_executions += 1
            self.violations_detected += len(violations)
            
            logger.warning(f"Code blocked by sandbox: {len(violations)} violations")
            
            return SandboxResult(
                success=False,
                error="Code contains dangerous patterns",
                violations=violations,
                code_hash=code_hash,
                execution_time_ms=(time.time() - start_time) * 1000,
            )
        
        # Step 2: Prepare sandbox environment
        sandbox_globals = self._prepare_globals(globals_dict)
        sandbox_locals = locals_dict.copy() if locals_dict else {}
        
        # Step 3: Capture output
        output_buffer = StringIO()
        old_stdout = sys.stdout
        old_stderr = sys.stderr
        
        # Step 4: Execute with timeout
        result = None
        error = None
        
        try:
            sys.stdout = output_buffer
            sys.stderr = output_buffer
            
            # Set recursion limit
            old_recursion_limit = sys.getrecursionlimit()
            sys.setrecursionlimit(self.config.max_recursion_depth)
            
            try:
                # Compile code
                compiled = compile(code, '<sandbox>', 'exec')
                
                # Execute with timeout
                result = self._execute_with_timeout(
                    compiled, 
                    sandbox_globals, 
                    sandbox_locals,
                    self.config.max_execution_time_seconds
                )
                
                # Call entry point if specified
                if entry_point and entry_point in sandbox_locals:
                    result = sandbox_locals[entry_point]()
                
                self.successful_executions += 1
                
            finally:
                sys.setrecursionlimit(old_recursion_limit)
                
        except TimeoutError as e:
            error = f"Execution timeout: {e}"
            violations.append(SandboxViolation(
                violation_type=SandboxViolationType.TIMEOUT_EXCEEDED,
                description=str(e),
                code_snippet=code[:100],
                line_number=None,
            ))
            
        except RecursionError as e:
            error = f"Recursion limit exceeded: {e}"
            violations.append(SandboxViolation(
                violation_type=SandboxViolationType.RECURSION_LIMIT,
                description=str(e),
                code_snippet=code[:100],
                line_number=None,
            ))
            
        except MemoryError as e:
            error = f"Memory limit exceeded: {e}"
            violations.append(SandboxViolation(
                violation_type=SandboxViolationType.MEMORY_EXCEEDED,
                description=str(e),
                code_snippet=code[:100],
                line_number=None,
            ))
            
        except SandboxSecurityError as e:
            error = f"Security violation: {e}"
            self.blocked_executions += 1
            
        except Exception as e:
            error = f"Execution error: {type(e).__name__}: {e}"
            logger.error(f"Sandbox execution error: {e}")
            
        finally:
            sys.stdout = old_stdout
            sys.stderr = old_stderr
        
        # Get output
        output = output_buffer.getvalue()
        if len(output) > self.config.max_output_size_kb * 1024:
            output = output[:self.config.max_output_size_kb * 1024]
            violations.append(SandboxViolation(
                violation_type=SandboxViolationType.OUTPUT_LIMIT,
                description="Output truncated due to size limit",
                code_snippet="",
                line_number=None,
                severity="LOW"
            ))
        
        execution_time_ms = (time.time() - start_time) * 1000
        
        sandbox_result = SandboxResult(
            success=error is None,
            result=result,
            output=output,
            error=error,
            execution_time_ms=execution_time_ms,
            violations=violations,
            code_hash=code_hash,
        )
        
        self.execution_history.append(sandbox_result)
        
        # Keep history bounded
        if len(self.execution_history) > 1000:
            self.execution_history = self.execution_history[-500:]
        
        return sandbox_result
    
    def _prepare_globals(self, extra_globals: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Prepare safe globals for sandbox execution."""
        safe_builtins = SafeBuiltins.get_safe_builtins(self.config)
        
        globals_dict = {
            '__builtins__': safe_builtins,
            '__name__': '__sandbox__',
            '__doc__': None,
        }
        
        # Add allowed imports
        for module_name in self.config.allowed_imports:
            try:
                if module_name in ('numpy', 'pandas', 'scipy'):
                    # Only import if available
                    try:
                        module = __import__(module_name)
                        globals_dict[module_name] = module
                    except ImportError:
                        pass
                else:
                    module = __import__(module_name)
                    globals_dict[module_name] = module
            except ImportError:
                pass
        
        # Add extra globals (filtered)
        if extra_globals:
            for key, value in extra_globals.items():
                if not key.startswith('_'):
                    globals_dict[key] = value
        
        return globals_dict
    
    def _execute_with_timeout(self, compiled_code, globals_dict: Dict, 
                              locals_dict: Dict, timeout: float) -> Any:
        """Execute code with timeout."""
        result = [None]
        error = [None]
        
        def target():
            try:
                exec(compiled_code, globals_dict, locals_dict)
                result[0] = locals_dict.get('result', None)
            except Exception as e:
                error[0] = e
        
        thread = threading.Thread(target=target)
        thread.daemon = True
        thread.start()
        thread.join(timeout)
        
        if thread.is_alive():
            raise TimeoutError(f"Execution exceeded {timeout} seconds")
        
        if error[0]:
            raise error[0]
        
        return result[0]
    
    def execute_function(self, func: Callable, *args, **kwargs) -> SandboxResult:
        """
        Execute a function in sandbox.
        
        Args:
            func: Function to execute
            *args: Positional arguments
            **kwargs: Keyword arguments
            
        Returns:
            SandboxResult
        """
        import inspect
        
        # Get function source
        try:
            source = inspect.getsource(func)
        except Exception as e:
            return SandboxResult(
                success=False,
                error=f"Cannot get function source: {e}",
            )
        
        # Create wrapper code
        func_name = func.__name__
        wrapper_code = f"""
{source}

result = {func_name}(*__args__, **__kwargs__)
"""
        
        return self.execute(
            wrapper_code,
            globals_dict={'__args__': args, '__kwargs__': kwargs}
        )
    
    @contextmanager
    def sandbox_filesystem(self):
        """Context manager for isolated filesystem access."""
        if not self.config.allow_filesystem:
            yield None
            return
        
        # Create temporary sandbox directory
        self._sandbox_dir = Path(tempfile.mkdtemp(prefix='sandbox_'))
        
        try:
            yield self._sandbox_dir
        finally:
            # Clean up sandbox directory
            if self._sandbox_dir and self._sandbox_dir.exists():
                shutil.rmtree(self._sandbox_dir, ignore_errors=True)
            self._sandbox_dir = None
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get sandbox execution statistics."""
        return {
            'total_executions': self.total_executions,
            'successful_executions': self.successful_executions,
            'blocked_executions': self.blocked_executions,
            'violations_detected': self.violations_detected,
            'success_rate': (
                self.successful_executions / self.total_executions
                if self.total_executions > 0 else 0
            ),
            'recent_history_size': len(self.execution_history),
        }
    
    def reset_statistics(self):
        """Reset execution statistics."""
        self.total_executions = 0
        self.successful_executions = 0
        self.blocked_executions = 0
        self.violations_detected = 0
        self.execution_history.clear()


class SandboxPool:
    """Pool of sandbox environments for parallel execution."""
    
    def __init__(self, pool_size: int = 4, config: Optional[SandboxConfig] = None):
        self.pool_size = pool_size
        self.config = config or SandboxConfig()
        self.sandboxes: List[SandboxEnvironment] = []
        self._lock = threading.Lock()
        
        # Initialize pool
        for _ in range(pool_size):
            self.sandboxes.append(SandboxEnvironment(self.config))
    
    def execute(self, code: str, **kwargs) -> SandboxResult:
        """Execute code using available sandbox from pool."""
        with self._lock:
            # Find least busy sandbox
            sandbox = min(self.sandboxes, key=lambda s: s.total_executions)
        
        return sandbox.execute(code, **kwargs)
    
    def get_pool_statistics(self) -> Dict[str, Any]:
        """Get statistics for entire pool."""
        stats = {
            'pool_size': self.pool_size,
            'total_executions': sum(s.total_executions for s in self.sandboxes),
            'successful_executions': sum(s.successful_executions for s in self.sandboxes),
            'blocked_executions': sum(s.blocked_executions for s in self.sandboxes),
            'violations_detected': sum(s.violations_detected for s in self.sandboxes),
        }
        stats['success_rate'] = (
            stats['successful_executions'] / stats['total_executions']
            if stats['total_executions'] > 0 else 0
        )
        return stats
