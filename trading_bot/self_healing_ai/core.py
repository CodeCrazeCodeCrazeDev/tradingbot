"""
Core Self-Healing AI Framework - Base classes and utilities
"""

import asyncio
import hashlib
import json
import logging
import threading
import traceback
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Tuple
import sqlite3

logger = logging.getLogger(__name__)


class ValidationSeverity(Enum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


class ValidationCategory(Enum):
    SYSTEM_ARCHITECTURE = "system_architecture"
    DATA_INTEGRITY = "data_integrity"
    MARKET_MICROSTRUCTURE = "market_microstructure"
    STRATEGY_LIFECYCLE = "strategy_lifecycle"
    ML_MODELS = "ml_models"
    RISK_MANAGEMENT = "risk_management"
    INFRASTRUCTURE = "infrastructure"
    BACKTESTING = "backtesting"
    RESEARCH_PRODUCTION = "research_production"
    SELF_MODIFICATION = "self_modification"
    SECURITY = "security"
    CONFIGURATION = "configuration"
    MONITORING = "monitoring"
    KILL_SWITCHES = "kill_switches"
    REGULATORY = "regulatory"
    CAPITAL_SCALABILITY = "capital_scalability"


class RemediationStatus(Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    REQUIRES_HUMAN = "requires_human"
    SKIPPED = "skipped"


class SystemHealth(Enum):
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    CRITICAL = "critical"
    UNKNOWN = "unknown"


IMMUTABLE_LIMITS = {
    'max_risk_per_trade': 0.02,
    'max_daily_loss': 0.05,
    'max_drawdown': 0.20,
    'max_leverage': 5.0,
    'max_position_size': 0.10,
    'max_correlation_exposure': 0.30,
    'min_liquidity_ratio': 0.5,
    'max_latency_ms': 100,
    'min_data_quality_score': 0.8,
}


@dataclass
class ValidationIssue:
    issue_id: str
    question_id: int
    category: ValidationCategory
    severity: ValidationSeverity
    title: str
    description: str
    affected_components: List[str]
    detected_at: datetime = field(default_factory=datetime.utcnow)
    remediation_available: bool = False
    remediation_action: Optional[str] = None
    auto_remediate: bool = False
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'issue_id': self.issue_id,
            'question_id': self.question_id,
            'category': self.category.value,
            'severity': self.severity.value,
            'title': self.title,
            'description': self.description,
            'affected_components': self.affected_components,
            'detected_at': self.detected_at.isoformat(),
            'remediation_available': self.remediation_available,
            'remediation_action': self.remediation_action,
            'auto_remediate': self.auto_remediate,
            'metadata': self.metadata,
        }


@dataclass
class RemediationAction:
    action_id: str
    issue_id: str
    action_type: str
    description: str
    status: RemediationStatus = RemediationStatus.PENDING
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    result: Optional[str] = None
    rollback_available: bool = False
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'action_id': self.action_id,
            'issue_id': self.issue_id,
            'action_type': self.action_type,
            'description': self.description,
            'status': self.status.value,
            'started_at': self.started_at.isoformat() if self.started_at else None,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None,
            'result': self.result,
        }


@dataclass
class ValidationReport:
    report_id: str
    generated_at: datetime
    system_health: SystemHealth
    total_checks: int
    passed_checks: int
    failed_checks: int
    issues: List[ValidationIssue]
    remediations: List[RemediationAction]
    category_scores: Dict[str, float]
    recommendations: List[str]
    execution_time_ms: float
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'report_id': self.report_id,
            'generated_at': self.generated_at.isoformat(),
            'system_health': self.system_health.value,
            'total_checks': self.total_checks,
            'passed_checks': self.passed_checks,
            'failed_checks': self.failed_checks,
            'pass_rate': self.passed_checks / self.total_checks if self.total_checks > 0 else 0,
            'issues': [i.to_dict() for i in self.issues],
            'remediations': [r.to_dict() for r in self.remediations],
            'category_scores': self.category_scores,
            'recommendations': self.recommendations,
            'execution_time_ms': self.execution_time_ms,
        }
    
    def get_critical_issues(self) -> List[ValidationIssue]:
        return [i for i in self.issues if i.severity == ValidationSeverity.CRITICAL]


@dataclass
class SystemState:
    positions: Dict[str, Any] = field(default_factory=dict)
    orders: Dict[str, Any] = field(default_factory=dict)
    capital: float = 0.0
    equity: float = 0.0
    drawdown: float = 0.0
    daily_pnl: float = 0.0
    active_strategies: List[str] = field(default_factory=list)
    connected_brokers: List[str] = field(default_factory=list)
    data_sources: Dict[str, Any] = field(default_factory=dict)
    last_heartbeat: Dict[str, datetime] = field(default_factory=dict)
    error_counts: Dict[str, int] = field(default_factory=dict)
    latency_metrics: Dict[str, float] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'positions': self.positions,
            'orders': self.orders,
            'capital': self.capital,
            'equity': self.equity,
            'drawdown': self.drawdown,
            'daily_pnl': self.daily_pnl,
            'active_strategies': self.active_strategies,
            'connected_brokers': self.connected_brokers,
            'last_heartbeat': {k: v.isoformat() for k, v in self.last_heartbeat.items()},
            'error_counts': self.error_counts,
            'latency_metrics': self.latency_metrics,
        }


class BaseValidator(ABC):
    def __init__(self, category: ValidationCategory):
        self.category = category
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
        self._checks: List[Tuple[Callable, List[int]]] = []
        self._remediations: Dict[str, Callable] = {}
        self._register_checks()
    
    @abstractmethod
    
    def add_check(self, check_func: Callable, question_ids: List[int]):
        self._checks.append((check_func, question_ids))
    
    def add_remediation(self, issue_type: str, remediation_func: Callable):
        self._remediations[issue_type] = remediation_func
    
    async def validate(self, state: SystemState) -> List[ValidationIssue]:
        issues = []
        for check_func, question_ids in self._checks:
            try:
                check_issues = await self._run_check(check_func, state)
                issues.extend(check_issues)
            except Exception as e:
                self.logger.error(f"Check {check_func.__name__} failed: {e}")
                issues.append(ValidationIssue(
                    issue_id=self._generate_issue_id(check_func.__name__, str(e)),
                    question_id=question_ids[0] if question_ids else 0,
                    category=self.category,
                    severity=ValidationSeverity.HIGH,
                    title=f"Validation check failed: {check_func.__name__}",
                    description=f"Check threw exception: {str(e)}",
                    affected_components=[self.__class__.__name__],
                    metadata={'exception': str(e), 'traceback': traceback.format_exc()}
                ))
        return issues
    
    async def _run_check(self, check_func: Callable, state: SystemState) -> List[ValidationIssue]:
        if asyncio.iscoroutinefunction(check_func):
            return await check_func(state)
        return check_func(state)
    
    async def remediate(self, issue: ValidationIssue) -> RemediationAction:
        action = RemediationAction(
            action_id=self._generate_action_id(issue.issue_id),
            issue_id=issue.issue_id,
            action_type=issue.remediation_action or "unknown",
            description=f"Remediation for: {issue.title}",
        )
        
        if not issue.remediation_available:
            action.status = RemediationStatus.REQUIRES_HUMAN
            action.result = "No automatic remediation available"
            return action
        
        remediation_func = self._remediations.get(issue.remediation_action)
        if not remediation_func:
            action.status = RemediationStatus.REQUIRES_HUMAN
            action.result = f"No remediation handler for: {issue.remediation_action}"
            return action
        try:
        
            action.started_at = datetime.utcnow()
            action.status = RemediationStatus.IN_PROGRESS
            if asyncio.iscoroutinefunction(remediation_func):
                result = await remediation_func(issue)
            else:
                result = remediation_func(issue)
            action.completed_at = datetime.utcnow()
            action.status = RemediationStatus.COMPLETED
            action.result = str(result)
        except Exception as e:
            action.completed_at = datetime.utcnow()
            action.status = RemediationStatus.FAILED
            action.result = f"Remediation failed: {str(e)}"
        
        return action
    
    def _generate_issue_id(self, check_name: str, detail: str) -> str:
        content = f"{self.category.value}:{check_name}:{detail}:{datetime.utcnow().isoformat()}"
        return hashlib.sha256(content.encode()).hexdigest()[:16]
    
    def _generate_action_id(self, issue_id: str) -> str:
        content = f"action:{issue_id}:{datetime.utcnow().isoformat()}"
        return hashlib.sha256(content.encode()).hexdigest()[:16]


class StateManager:
    _instance = None
    _lock = threading.Lock()
    
    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        self._initialized = True
        self._state = SystemState()
        self._state_lock = threading.RLock()
        self._db_path = Path("trading_bot/self_healing_ai/state.db")
        self._init_db()
    
    def _init_db(self):
        self._db_path.parent.mkdir(parents=True, exist_ok=True)
        conn = sqlite3.connect(str(self._db_path))
        cursor = conn.cursor()
        cursor.execute('''CREATE TABLE IF NOT EXISTS validation_issues (
            id INTEGER PRIMARY KEY, issue_id TEXT UNIQUE, question_id INTEGER,
            category TEXT, severity TEXT, title TEXT, description TEXT,
            detected_at TEXT, resolved_at TEXT)''')
        cursor.execute('''CREATE TABLE IF NOT EXISTS remediation_actions (
            id INTEGER PRIMARY KEY, action_id TEXT UNIQUE, issue_id TEXT,
            action_type TEXT, status TEXT, started_at TEXT, completed_at TEXT, result TEXT)''')
        conn.commit()
        conn.close()
    
    def get_state(self) -> SystemState:
        with self._state_lock:
            return self._state
    
    def update_state(self, **kwargs):
        with self._state_lock:
            for key, value in kwargs.items():
                if hasattr(self._state, key):
                    setattr(self._state, key, value)
    
    def record_issue(self, issue: ValidationIssue):
        conn = sqlite3.connect(str(self._db_path))
        cursor = conn.cursor()
        cursor.execute('''INSERT OR REPLACE INTO validation_issues 
            (issue_id, question_id, category, severity, title, description, detected_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)''',
            (issue.issue_id, issue.question_id, issue.category.value,
             issue.severity.value, issue.title, issue.description, issue.detected_at.isoformat()))
        conn.commit()
        conn.close()
