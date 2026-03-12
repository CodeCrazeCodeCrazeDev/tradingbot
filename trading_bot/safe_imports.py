"""
Safe Imports Module
===================

Provides safe import utilities that handle missing dependencies gracefully.
This module ensures the trading bot can run even if some optional dependencies
are not installed.

Usage:
    from trading_bot.safe_imports import safe_import, require_module
    
    # Safe import with fallback
    numpy = safe_import('numpy', fallback=None)
    
    # Check if module is available
    if require_module('torch'):
        import torch
"""

import importlib
import logging
import sys
from typing import Any, Callable, Dict, List, Optional, Tuple, Type
from functools import wraps

logger = logging.getLogger(__name__)


# ============================================================================
# SAFE IMPORT UTILITIES
# ============================================================================

def safe_import(module_name: str, fallback: Any = None, 
                submodule: Optional[str] = None) -> Any:
    """
    Safely import a module with fallback.
    
    Args:
        module_name: Name of the module to import
        fallback: Value to return if import fails
        submodule: Specific attribute to get from the module
        
    Returns:
        The imported module/attribute or fallback value
    """
    try:
        module = importlib.import_module(module_name)
        if submodule:
            return getattr(module, submodule, fallback)
        return module
    except ImportError:
        logger.debug(f"Optional module '{module_name}' not available")
        return fallback
    except Exception as e:
        logger.debug(f"Error importing '{module_name}': {e}")
        return fallback


def require_module(module_name: str) -> bool:
    """
    Check if a module is available.
    
    Args:
        module_name: Name of the module to check
        
    Returns:
        True if module is available, False otherwise
    """
    try:
        importlib.import_module(module_name)
        return True
    except ImportError:
        return False


def safe_import_class(module_path: str, class_name: str, 
                      fallback_class: Optional[Type] = None) -> Type:
    """
    Safely import a class from a module.
    
    Args:
        module_path: Full path to the module
        class_name: Name of the class to import
        fallback_class: Class to return if import fails
        
    Returns:
        The imported class or fallback class
    """
    try:
        module = importlib.import_module(module_path)
        return getattr(module, class_name)
    except (ImportError, AttributeError) as e:
        logger.debug(f"Could not import {class_name} from {module_path}: {e}")
        if fallback_class:
            return fallback_class
        # Return a dummy class
        return type(class_name, (), {'__init__': lambda self, *args, **kwargs: None})


def lazy_import(module_name: str):
    """
    Decorator for lazy module imports.
    
    Usage:
        @lazy_import('numpy')
        def my_function(np):
            return np.array([1, 2, 3])
    """
    def decorator(func: Callable) -> Callable:
        """
        decorator function.

    Args:
        func: Description

    Returns:
        Result of operation
        """
        @wraps(func)
        def wrapper(*args, **kwargs):
            """
            wrapper function.

    Auto-documented by QwenCodeMender.
            """
            module = safe_import(module_name)
            if module is None:
                raise ImportError(f"Required module '{module_name}' not available")
            return func(module, *args, **kwargs)
        return wrapper
    return decorator


# ============================================================================
# OPTIONAL DEPENDENCY CHECKS
# ============================================================================

class OptionalDependencies:
    """Track and check optional dependencies"""
    
    # Core ML dependencies
    NUMPY = 'numpy'
    PANDAS = 'pandas'
    SCIPY = 'scipy'
    SKLEARN = 'sklearn'
    
    # Deep Learning
    TORCH = 'torch'
    TENSORFLOW = 'tensorflow'
    
    # Trading specific
    TALIB = 'talib'
    CCXT = 'ccxt'
    
    # Data
    REDIS = 'redis'
    KAFKA = 'kafka'
    CLICKHOUSE = 'clickhouse_driver'
    
    # Async
    AIOHTTP = 'aiohttp'
    WEBSOCKETS = 'websockets'
    
    # Visualization
    PLOTLY = 'plotly'
    MATPLOTLIB = 'matplotlib'
    
    # Quantum
    QISKIT = 'qiskit'
    
    # Blockchain
    WEB3 = 'web3'
    
    @classmethod
    def check_all(cls) -> Dict[str, bool]:
        """Check all optional dependencies"""
        deps = {}
        for attr in dir(cls):
            if attr.isupper() and not attr.startswith('_'):
                module_name = getattr(cls, attr)
                deps[module_name] = require_module(module_name)
        return deps
    
    @classmethod
    def get_available(cls) -> List[str]:
        """Get list of available dependencies"""
        return [name for name, available in cls.check_all().items() if available]
    
    @classmethod
    def get_missing(cls) -> List[str]:
        """Get list of missing dependencies"""
        return [name for name, available in cls.check_all().items() if not available]


# ============================================================================
# STUB CLASSES FOR MISSING DEPENDENCIES
# ============================================================================

class StubClass:
    """Stub class for missing dependencies"""
    
    def __init__(self, *args, **kwargs):
        """Auto-implemented init."""
        pass
    
    def __call__(self, *args, **kwargs):
        return self
    
    def __getattr__(self, name):
        return StubClass()


class StubModule:
    """Stub module for missing dependencies"""
    
    def __getattr__(self, name):
        return StubClass()


# ============================================================================
# COMMON IMPORTS WITH FALLBACKS
# ============================================================================

def get_numpy():
    """Get numpy with fallback"""
    np = safe_import('numpy')
    if np is None:
        logger.warning("NumPy not available - using stub")
        return StubModule()
    return np


def get_pandas():
    """Get pandas with fallback"""
    pd = safe_import('pandas')
    if pd is None:
        logger.warning("Pandas not available - using stub")
        return StubModule()
    return pd


def get_torch():
    """Get PyTorch with fallback"""
    torch = safe_import('torch')
    if torch is None:
        logger.debug("PyTorch not available")
        return None
    return torch


def get_sklearn():
    """Get scikit-learn with fallback"""
    sklearn = safe_import('sklearn')
    if sklearn is None:
        logger.debug("scikit-learn not available")
        return None
    return sklearn


# ============================================================================
# TRADING BOT SPECIFIC IMPORTS
# ============================================================================

def import_trading_module(module_path: str, class_name: str, 
                          config: Optional[Dict] = None) -> Tuple[Any, bool]:
    """
    Import a trading bot module safely.
    
    Args:
        module_path: Path to the module (e.g., 'trading_bot.alpha_engine.orchestrator')
        class_name: Name of the class to import
        config: Optional configuration to pass to the class
        
    Returns:
        Tuple of (instance or None, success boolean)
    """
    try:
        module = importlib.import_module(module_path)
        cls = getattr(module, class_name)
        
        if config is not None:
            instance = cls(config)
        else:
            try:
                instance = cls()
            except TypeError:
                instance = cls({})
        
        return instance, True
        
    except ImportError as e:
        logger.debug(f"Module not found: {module_path} - {e}")
        return None, False
    except AttributeError as e:
        logger.debug(f"Class not found: {class_name} in {module_path} - {e}")
        return None, False
    except Exception as e:
        logger.warning(f"Error instantiating {class_name}: {e}")
        return None, False


def batch_import_modules(modules: List[Dict]) -> Dict[str, Any]:
    """
    Import multiple modules in batch.
    
    Args:
        modules: List of dicts with 'path', 'class', and optional 'config'
        
    Returns:
        Dict mapping names to instances
    """
    results = {}
    
    for mod in modules:
        name = mod.get('name', mod['class'])
        instance, success = import_trading_module(
            mod['path'],
            mod['class'],
            mod.get('config')
        )
        if success:
            results[name] = instance
            logger.debug(f"Loaded: {name}")
        else:
            logger.debug(f"Failed: {name}")
    
    return results


# ============================================================================
# INITIALIZATION HELPERS
# ============================================================================

def check_core_dependencies() -> Tuple[bool, List[str]]:
    """
    Check if core dependencies are available.
    
    Returns:
        Tuple of (all_available, list of missing)
    """
    core = ['numpy', 'pandas']
    missing = [dep for dep in core if not require_module(dep)]
    return len(missing) == 0, missing


def check_ml_dependencies() -> Tuple[bool, List[str]]:
    """
    Check if ML dependencies are available.
    
    Returns:
        Tuple of (all_available, list of missing)
    """
    ml = ['numpy', 'pandas', 'scipy', 'sklearn']
    missing = [dep for dep in ml if not require_module(dep)]
    return len(missing) == 0, missing


def check_deep_learning_dependencies() -> Tuple[bool, List[str]]:
    """
    Check if deep learning dependencies are available.
    
    Returns:
        Tuple of (any_available, list of available)
    """
    dl = ['torch', 'tensorflow']
    available = [dep for dep in dl if require_module(dep)]
    return len(available) > 0, available


def print_dependency_status():
    """Print status of all dependencies"""
    print("\n" + "=" * 50)
    print("DEPENDENCY STATUS")
    print("=" * 50)
    
    deps = OptionalDependencies.check_all()
    
    available = [d for d, a in deps.items() if a]
    missing = [d for d, a in deps.items() if not a]
    
    print(f"\nAvailable ({len(available)}):")
    for dep in sorted(available):
        print(f"  ✓ {dep}")
    
    print(f"\nMissing ({len(missing)}):")
    for dep in sorted(missing):
        print(f"  ✗ {dep}")
    
    print("=" * 50)


# ============================================================================
# MODULE INITIALIZATION
# ============================================================================

# Pre-check core dependencies
_core_ok, _core_missing = check_core_dependencies()
if not _core_ok:
    logger.warning(f"Core dependencies missing: {_core_missing}")

# Export commonly used safe imports
np = get_numpy()
pd = get_pandas()


__all__ = [
    'safe_import',
    'require_module',
    'safe_import_class',
    'lazy_import',
    'OptionalDependencies',
    'StubClass',
    'StubModule',
    'get_numpy',
    'get_pandas',
    'get_torch',
    'get_sklearn',
    'import_trading_module',
    'batch_import_modules',
    'check_core_dependencies',
    'check_ml_dependencies',
    'check_deep_learning_dependencies',
    'print_dependency_status',
    'np',
    'pd'
]
