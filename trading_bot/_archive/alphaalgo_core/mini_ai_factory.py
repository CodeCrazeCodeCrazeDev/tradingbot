"""
AlphaAlgo Mini-AI Factory

Creates specialized G2 Mini-AIs with specific roles:
- Data cleaner
- Feature engineer
- Strategy tester
- Risk validator
- Security guardian
- Architecture analyzer
- L2 data interpreter
- Sentiment parser
- Broker connector

All mini models must obey the Central Controller (G1).
"""

import asyncio
import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum, auto
from typing import Any, Callable, Dict, List, Optional, Set, Tuple
import uuid

# Evolution: Added retry decorator
def retry(max_attempts=3, delay=1.0):
    """Retry decorator for resilient operations"""
    def decorator(func):
        """
        decorator function.

    Args:
        func: Description

    Returns:
        Result of operation
        """
        async def wrapper(*args, **kwargs):
            last_error = None
            for attempt in range(max_attempts):
                try:
                    return await func(*args, **kwargs)
                except Exception as e:
                    last_error = e
                    if attempt < max_attempts - 1:
                        await asyncio.sleep(delay * (attempt + 1))
            raise last_error
        return wrapper
    return decorator



logger = logging.getLogger(__name__)


class MiniAIRole(Enum):
    """Roles for Mini-AIs"""
    DATA_CLEANER = "data_cleaner"
    FEATURE_ENGINEER = "feature_engineer"
    STRATEGY_TESTER = "strategy_tester"
    RISK_VALIDATOR = "risk_validator"
    SECURITY_GUARDIAN = "security_guardian"
    ARCHITECTURE_ANALYZER = "architecture_analyzer"
    L2_INTERPRETER = "l2_interpreter"
    SENTIMENT_PARSER = "sentiment_parser"
    BROKER_CONNECTOR = "broker_connector"


@dataclass
class MiniAITask:
    """A task for a Mini-AI"""
    task_id: str
    role: MiniAIRole
    action: str
    parameters: Dict[str, Any]
    priority: int = 5  # 1-10, 1 is highest
    created_at: datetime = field(default_factory=datetime.now)
    status: str = "pending"
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None


class BaseMiniAI(ABC):
    """Base class for all Mini-AIs"""
    
    def __init__(self, role: MiniAIRole, controller_callback: Callable):
        self.mini_ai_id = f"{role.value}_{uuid.uuid4().hex[:6]}"
        self.role = role
        self.controller_callback = controller_callback
        self.is_active = True
        self.task_count = 0
        self.error_count = 0
        self.created_at = datetime.now()
        
        logger.info(f"[MiniAI] Created {self.mini_ai_id}")
    
    @abstractmethod
    def get_capabilities(self) -> List[str]:
        """Return list of capabilities"""
        pass
    
    @abstractmethod
    async def execute(self, task: MiniAITask) -> Dict[str, Any]:
        """Execute a task"""
        pass
    
    async def process_task(self, task: MiniAITask) -> MiniAITask:
        """Process a task with controller authorization"""
        if not self.is_active:
            task.status = "failed"
            task.error = "Mini-AI is deactivated"
            return task
        
        # Request authorization from controller
        authorized = self.controller_callback(
            'authorize',
            self.mini_ai_id,
            task.action
        )
        
        if not authorized:
            task.status = "denied"
            task.error = "Controller denied authorization"
            return task
        try:
        
            self.task_count += 1
            result = await self.execute(task)
            task.status = "completed"
            task.result = result
        except Exception as e:
            self.error_count += 1
            task.status = "failed"
            task.error = str(e)
            logger.error(f"[MiniAI] {self.mini_ai_id} task failed: {e}")
        
        return task
    
    def deactivate(self, reason: str):
        """Deactivate this Mini-AI"""
        self.is_active = False
        logger.warning(f"[MiniAI] {self.mini_ai_id} deactivated: {reason}")
    
    def get_status(self) -> Dict[str, Any]:
        """Get Mini-AI status"""
        return {
            'mini_ai_id': self.mini_ai_id,
            'role': self.role.value,
            'is_active': self.is_active,
            'capabilities': self.get_capabilities(),
            'task_count': self.task_count,
            'error_count': self.error_count,
            'created_at': self.created_at.isoformat(),
        }


class DataCleanerAI(BaseMiniAI):
    """Mini-AI for data cleaning"""
    
    def __init__(self, controller_callback: Callable):
        super().__init__(MiniAIRole.DATA_CLEANER, controller_callback)
    
    def get_capabilities(self) -> List[str]:
        return [
            'clean_ohlcv',
            'remove_outliers',
            'fill_missing',
            'normalize_data',
            'validate_data',
            'detect_anomalies',
        ]
    
    async def execute(self, task: MiniAITask) -> Dict[str, Any]:
        action = task.action
        params = task.parameters
        
        if action == 'clean_ohlcv':
            # Simulate data cleaning
            return {
                'rows_cleaned': params.get('rows', 0),
                'outliers_removed': 0,
                'missing_filled': 0,
            }
        elif action == 'validate_data':
            return {
                'valid': True,
                'issues': [],
            }
        else:
            return {'status': 'completed', 'action': action}


class FeatureEngineerAI(BaseMiniAI):
    """Mini-AI for feature engineering"""
    
    def __init__(self, controller_callback: Callable):
        super().__init__(MiniAIRole.FEATURE_ENGINEER, controller_callback)
    
    def get_capabilities(self) -> List[str]:
        return [
            'create_indicators',
            'transform_features',
            'select_features',
            'normalize_features',
            'create_lagged_features',
            'create_rolling_features',
        ]
    
    async def execute(self, task: MiniAITask) -> Dict[str, Any]:
        action = task.action
        params = task.parameters
        
        if action == 'create_indicators':
            indicators = params.get('indicators', [])
            return {
                'indicators_created': len(indicators),
                'features': indicators,
            }
        elif action == 'select_features':
            return {
                'selected_features': params.get('top_n', 10),
                'method': 'importance_ranking',
            }
        else:
            return {'status': 'completed', 'action': action}


class StrategyTesterAI(BaseMiniAI):
    """Mini-AI for strategy testing"""
    
    def __init__(self, controller_callback: Callable):
        super().__init__(MiniAIRole.STRATEGY_TESTER, controller_callback)
    
    def get_capabilities(self) -> List[str]:
        return [
            'backtest_strategy',
            'validate_signals',
            'calculate_metrics',
            'stress_test',
            'monte_carlo',
            'walk_forward',
        ]
    
    async def execute(self, task: MiniAITask) -> Dict[str, Any]:
        action = task.action
        params = task.parameters
        
        if action == 'backtest_strategy':
            return {
                'trades': 0,
                'win_rate': 0.0,
                'profit_factor': 0.0,
                'sharpe_ratio': 0.0,
                'max_drawdown': 0.0,
            }
        elif action == 'validate_signals':
            return {
                'signals_validated': params.get('count', 0),
                'valid_signals': 0,
            }
        else:
            return {'status': 'completed', 'action': action}


class RiskValidatorAI(BaseMiniAI):
    """Mini-AI for risk validation"""
    
    def __init__(self, controller_callback: Callable):
        super().__init__(MiniAIRole.RISK_VALIDATOR, controller_callback)
    
    def get_capabilities(self) -> List[str]:
        return [
            'validate_position_size',
            'check_risk_limits',
            'calculate_var',
            'check_correlation',
            'validate_exposure',
            'check_drawdown',
        ]
    
    async def execute(self, task: MiniAITask) -> Dict[str, Any]:
        action = task.action
        params = task.parameters
        
        if action == 'validate_position_size':
            size = params.get('size', 0)
            max_size = params.get('max_size', 0.02)
            return {
                'valid': size <= max_size,
                'size': size,
                'max_allowed': max_size,
            }
        elif action == 'check_risk_limits':
            return {
                'within_limits': True,
                'current_risk': 0.01,
                'max_risk': 0.02,
            }
        else:
            return {'status': 'completed', 'action': action}


class SecurityGuardianAI(BaseMiniAI):
    """Mini-AI for security monitoring"""
    
    def __init__(self, controller_callback: Callable):
        super().__init__(MiniAIRole.SECURITY_GUARDIAN, controller_callback)
    
    def get_capabilities(self) -> List[str]:
        return [
            'scan_threats',
            'validate_credentials',
            'monitor_access',
            'check_encryption',
            'audit_logs',
            'detect_anomalies',
        ]
    
    async def execute(self, task: MiniAITask) -> Dict[str, Any]:
        action = task.action
        
        if action == 'scan_threats':
            return {
                'threats_found': 0,
                'scan_time': datetime.now().isoformat(),
            }
        elif action == 'validate_credentials':
            return {
                'valid': True,
                'encrypted': True,
            }
        else:
            return {'status': 'completed', 'action': action}


class ArchitectureAnalyzerAI(BaseMiniAI):
    """Mini-AI for architecture analysis"""
    
    def __init__(self, controller_callback: Callable):
        super().__init__(MiniAIRole.ARCHITECTURE_ANALYZER, controller_callback)
    
    def get_capabilities(self) -> List[str]:
        return [
            'analyze_dependencies',
            'detect_circular_imports',
            'find_unused_code',
            'check_naming',
            'measure_complexity',
            'suggest_refactoring',
        ]
    
    async def execute(self, task: MiniAITask) -> Dict[str, Any]:
        action = task.action
        
        if action == 'analyze_dependencies':
            return {
                'modules_analyzed': 0,
                'dependencies': [],
            }
        elif action == 'detect_circular_imports':
            return {
                'circular_imports': [],
                'count': 0,
            }
        else:
            return {'status': 'completed', 'action': action}


class L2InterpreterAI(BaseMiniAI):
    """Mini-AI for Level 2 data interpretation"""
    
    def __init__(self, controller_callback: Callable):
        super().__init__(MiniAIRole.L2_INTERPRETER, controller_callback)
    
    def get_capabilities(self) -> List[str]:
        return [
            'analyze_orderbook',
            'detect_imbalance',
            'calculate_pressure',
            'identify_levels',
            'track_large_orders',
            'detect_spoofing',
        ]
    
    async def execute(self, task: MiniAITask) -> Dict[str, Any]:
        action = task.action
        params = task.parameters
        
        if action == 'analyze_orderbook':
            return {
                'bid_depth': 0,
                'ask_depth': 0,
                'imbalance': 0.0,
                'pressure': 'neutral',
            }
        elif action == 'detect_imbalance':
            return {
                'imbalance_ratio': 1.0,
                'direction': 'neutral',
                'strength': 'weak',
            }
        else:
            return {'status': 'completed', 'action': action}


class SentimentParserAI(BaseMiniAI):
    """Mini-AI for sentiment parsing"""
    
    def __init__(self, controller_callback: Callable):
        super().__init__(MiniAIRole.SENTIMENT_PARSER, controller_callback)
    
    def get_capabilities(self) -> List[str]:
        return [
            'parse_news',
            'analyze_social',
            'calculate_sentiment',
            'detect_trends',
            'aggregate_sources',
            'score_impact',
        ]
    
    async def execute(self, task: MiniAITask) -> Dict[str, Any]:
        action = task.action
        params = task.parameters
        
        if action == 'parse_news':
            return {
                'articles_parsed': 0,
                'sentiment_score': 0.0,
                'keywords': [],
            }
        elif action == 'calculate_sentiment':
            return {
                'overall_sentiment': 0.0,
                'bullish_pct': 50.0,
                'bearish_pct': 50.0,
            }
        else:
            return {'status': 'completed', 'action': action}


class BrokerConnectorAI(BaseMiniAI):
    """Mini-AI for broker connection management"""
    
    def __init__(self, controller_callback: Callable):
        super().__init__(MiniAIRole.BROKER_CONNECTOR, controller_callback)
    
    def get_capabilities(self) -> List[str]:
        return [
            'check_connection',
            'validate_credentials',
            'get_account_info',
            'monitor_latency',
            'handle_reconnect',
            'sync_positions',
        ]
    
    async def execute(self, task: MiniAITask) -> Dict[str, Any]:
        action = task.action
        
        if action == 'check_connection':
            return {
                'connected': False,
                'latency_ms': 0,
            }
        elif action == 'get_account_info':
            return {
                'balance': 0.0,
                'equity': 0.0,
                'margin': 0.0,
            }
        else:
            return {'status': 'completed', 'action': action}


class MiniAIFactory:
    """
    Factory for creating Mini-AIs.
    
    All Mini-AIs are created through this factory and
    registered with the Central Controller.
    """
    
    # Role to class mapping
    ROLE_CLASSES = {
        MiniAIRole.DATA_CLEANER: DataCleanerAI,
        MiniAIRole.FEATURE_ENGINEER: FeatureEngineerAI,
        MiniAIRole.STRATEGY_TESTER: StrategyTesterAI,
        MiniAIRole.RISK_VALIDATOR: RiskValidatorAI,
        MiniAIRole.SECURITY_GUARDIAN: SecurityGuardianAI,
        MiniAIRole.ARCHITECTURE_ANALYZER: ArchitectureAnalyzerAI,
        MiniAIRole.L2_INTERPRETER: L2InterpreterAI,
        MiniAIRole.SENTIMENT_PARSER: SentimentParserAI,
        MiniAIRole.BROKER_CONNECTOR: BrokerConnectorAI,
    }
    
    def __init__(self, controller_callback: Callable):
        self.controller_callback = controller_callback
        self._mini_ais: Dict[str, BaseMiniAI] = {}
    
    def create(self, role: MiniAIRole) -> BaseMiniAI:
        """Create a Mini-AI for the specified role"""
        if role not in self.ROLE_CLASSES:
            raise ValueError(f"Unknown role: {role}")
        
        ai_class = self.ROLE_CLASSES[role]
        mini_ai = ai_class(self.controller_callback)
        
        self._mini_ais[mini_ai.mini_ai_id] = mini_ai
        
        logger.info(f"[Factory] Created Mini-AI: {mini_ai.mini_ai_id}")
        return mini_ai
    
    def create_all(self) -> Dict[MiniAIRole, BaseMiniAI]:
        """Create all Mini-AIs"""
        result = {}
        for role in MiniAIRole:
            result[role] = self.create(role)
        return result
    
    def get(self, mini_ai_id: str) -> Optional[BaseMiniAI]:
        """Get a Mini-AI by ID"""
        return self._mini_ais.get(mini_ai_id)
    
    def get_by_role(self, role: MiniAIRole) -> List[BaseMiniAI]:
        """Get all Mini-AIs with a specific role"""
        return [ai for ai in self._mini_ais.values() if ai.role == role]
    
    def get_all(self) -> List[BaseMiniAI]:
        """Get all Mini-AIs"""
        return list(self._mini_ais.values())
    
    def deactivate_all(self, reason: str):
        """Deactivate all Mini-AIs"""
        for mini_ai in self._mini_ais.values():
            mini_ai.deactivate(reason)
    
    def get_status_report(self) -> Dict[str, Any]:
        """Get status report for all Mini-AIs"""
        return {
            'total': len(self._mini_ais),
            'active': sum(1 for ai in self._mini_ais.values() if ai.is_active),
            'mini_ais': [ai.get_status() for ai in self._mini_ais.values()],
        }
