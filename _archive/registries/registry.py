"""
Module Registry - Central registry of all trading bot components
================================================================

This module provides a centralized registry of all available components,
making it easy to discover and use the right module for each task.

Usage:
    from trading_bot.registry import get_component, list_components
    
    # Get a specific component
    risk_manager = get_component('risk', 'MasterRiskManager')
    
    # List all components in a category
    components = list_components('execution')
"""

from typing import Any, Dict, List, Optional, Type
import logging

logger = logging.getLogger(__name__)

# Component registry organized by category
_REGISTRY: Dict[str, Dict[str, Any]] = {
    'risk': {
        'MasterRiskManager': ('trading_bot.risk', 'MasterRiskManager'),
        'RiskManager': ('trading_bot.risk', 'RiskManager'),  # Alias
        'PositionSizer': ('trading_bot.risk', 'PositionSizer'),
        'CircuitBreaker': ('trading_bot.risk', 'CircuitBreakerManager'),
        'VaREngine': ('trading_bot.risk', 'VaREngine'),
    },
    'execution': {
        'PaperExecutor': ('trading_bot.execution', 'PaperExecutor'),
        'LiveExecutor': ('trading_bot.execution', 'LiveExecutor'),
        'TWAPExecutor': ('trading_bot.execution', 'TWAPExecutor'),
        'VWAPExecutor': ('trading_bot.execution', 'VWAPExecutor'),
        'SmartOrderRouter': ('trading_bot.execution', 'SmartOrderRouter'),
        'FillTracker': ('trading_bot.execution', 'FillTracker'),
    },
    'strategy': {
        'StrategyEngine': ('trading_bot.strategy', 'StrategyEngine'),
        'MLStrategyEngine': ('trading_bot.strategy', 'MLStrategyEngine'),
        'BaseStrategy': ('trading_bot.strategy', 'BaseStrategy'),
    },
    'analysis': {
        'MarketStructureAnalyzer': ('trading_bot.analysis', 'MarketStructureAnalyzer'),
        'LiquidityAnalyzer': ('trading_bot.analysis', 'LiquidityAnalyzer'),
        'OrderFlowAnalyzer': ('trading_bot.analysis', 'OrderFlowAnalyzer'),
        'SentimentAnalyzer': ('trading_bot.analysis', 'SentimentAnalyzer'),
    },
    'data': {
        'MT5Interface': ('trading_bot.data', 'MT5Interface'),
        'MarketDataStream': ('trading_bot.data', 'MarketDataStream'),
        'TimeSeriesDB': ('trading_bot.data', 'TimeSeriesDB'),
    },
    'core': {
        'TradingSystem': ('trading_bot.core', 'TradingSystem'),
        'SurvivalCore': ('trading_bot.core', 'SurvivalCore'),
        'AnalysisOrchestrator': ('trading_bot.core', 'AnalysisOrchestrator'),
        'ExecutionManager': ('trading_bot.core', 'ExecutionManager'),
    },
    'orchestrator': {
        'MasterOrchestrator': ('trading_bot.orchestrator', 'MasterOrchestrator'),
        'ExecutionEngine': ('trading_bot.orchestrator', 'ExecutionEngine'),
        'PerformanceTracker': ('trading_bot.orchestrator', 'PerformanceTracker'),
    },
    'ml': {
        'PricePredictor': ('trading_bot.ml', 'PricePredictor'),
        'PatternRecognizer': ('trading_bot.ml', 'PatternRecognizer'),
        'OnlineLearner': ('trading_bot.ml', 'OnlineLearner'),
        'ExplainableAI': ('trading_bot.ml', 'ExplainableAI'),
    },
    'safety': {
        'EmergencyKillSwitch': ('trading_bot.safety', 'EmergencyKillSwitch'),
        'LatencyCircuitBreaker': ('trading_bot.safety', 'LatencyCircuitBreaker'),
        'ResourceWatchdog': ('trading_bot.safety', 'ResourceWatchdog'),
    },
    'monitoring': {
        'HealthMonitor': ('trading_bot.system_health', 'HealthMonitor'),
        'PerformanceMonitor': ('trading_bot.performance', 'PerformanceMonitor'),
    },
}


def get_component(category: str, name: str) -> Optional[Type]:
    """
    Get a component class by category and name.
    
    Args:
        category: Component category (risk, execution, strategy, etc.)
        name: Component name
        
    Returns:
        Component class or None if not found
    """
    if category not in _REGISTRY:
        logger.warning(f"Unknown category: {category}")
        return None
    
    if name not in _REGISTRY[category]:
        logger.warning(f"Unknown component: {name} in category {category}")
        return None
    
    module_path, class_name = _REGISTRY[category][name]
    
    try:
        import importlib
        module = importlib.import_module(module_path)
        return getattr(module, class_name, None)
    except ImportError as e:
        logger.error(f"Failed to import {module_path}.{class_name}: {e}")
        return None


def list_components(category: Optional[str] = None) -> Dict[str, List[str]]:
    """
    List available components.
    
    Args:
        category: Optional category to filter by
        
    Returns:
        Dictionary of category -> list of component names
    """
    if category:
        if category in _REGISTRY:
            return {category: list(_REGISTRY[category].keys())}
        return {}
    
    return {cat: list(components.keys()) for cat, components in _REGISTRY.items()}


def get_canonical_module(module_type: str) -> str:
    """
    Get the canonical module path for a given module type.
    
    This helps avoid using deprecated or duplicate modules.
    
    Args:
        module_type: Type of module (risk_manager, executor, etc.)
        
    Returns:
        Canonical module path
    """
    CANONICAL_MODULES = {
        'risk_manager': 'trading_bot.risk.MASTER_risk_manager',
        'executor': 'trading_bot.execution',
        'strategy': 'trading_bot.strategy.strategy_engine',
        'orchestrator': 'trading_bot.orchestrator.master_orchestrator',
        'data': 'trading_bot.data.mt5_interface',
        'analysis': 'trading_bot.analysis',
        'ml': 'trading_bot.ml',
        'safety': 'trading_bot.safety',
    }
    
    return CANONICAL_MODULES.get(module_type, f'trading_bot.{module_type}')


# Deprecated module warnings
DEPRECATED_MODULES = {
    'trading_bot.risk.risk_manager': 'Use trading_bot.risk.MASTER_risk_manager instead',
    'trading_bot.risk.unified_risk_manager': 'Use trading_bot.risk.MASTER_risk_manager instead',
    'trading_bot.risk.advanced_risk_manager': 'Use trading_bot.risk.MASTER_risk_manager instead',
    'trading_bot.risk.ml_risk_manager': 'Use trading_bot.risk.MASTER_risk_manager with ml_enabled=True',
}


def check_deprecated(module_path: str) -> Optional[str]:
    """
    Check if a module is deprecated and return migration advice.
    
    Args:
        module_path: Full module path
        
    Returns:
        Migration advice or None if not deprecated
    """
    return DEPRECATED_MODULES.get(module_path)


__all__ = [
    'get_component',
    'list_components', 
    'get_canonical_module',
    'check_deprecated',
]
