"""
AlphaAlgo Central Controller - The G0/G1/G2 Governance Hierarchy

G0 — Human Authority: Approves/rejects all major changes
G1 — Central Controller: Coordinates modules, maintains stability
G2 — Mini-AIs: Specialized helper models that obey G1

The AI is the student → The market is the teacher.
"""

import asyncio
import hashlib
import json
import logging
import os
import sqlite3
import threading
import uuid
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum, auto
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Set, Tuple

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


class GovernanceLevel(Enum):
    """Governance hierarchy levels"""
    G0_HUMAN = 0      # Human authority - ultimate control
    G1_CONTROLLER = 1  # Central AI controller
    G2_MINI_AI = 2     # Specialized mini-AIs


class ActionType(Enum):
    """Types of actions requiring governance"""
    # G0 Required (Human must approve)
    DEPLOY_CODE = auto()
    MODIFY_RISK_PARAMS = auto()
    CHANGE_POSITION_SIZING = auto()
    MODIFY_ORDER_EXECUTION = auto()
    CONNECT_LIVE_BROKER = auto()
    ENABLE_LIVE_TRADING = auto()
    CHANGE_GOVERNANCE_RULES = auto()
    DELETE_DATA = auto()
    EXTERNAL_COMMUNICATION = auto()
    
    # G1 Can Approve
    CREATE_MINI_AI = auto()
    MODIFY_STRATEGY_PARAMS = auto()
    UPDATE_DATA_SOURCES = auto()
    RUN_BACKTEST = auto()
    GENERATE_REPORT = auto()
    OPTIMIZE_PARAMETERS = auto()
    
    # G2 Can Execute
    CLEAN_DATA = auto()
    ENGINEER_FEATURES = auto()
    VALIDATE_SIGNALS = auto()
    ANALYZE_ARCHITECTURE = auto()
    PARSE_SENTIMENT = auto()
    INTERPRET_L2_DATA = auto()


class ApprovalStatus(Enum):
    """Status of approval requests"""
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    EXPIRED = "expired"
    CANCELLED = "cancelled"


@dataclass
class ApprovalRequest:
    """Request for human approval"""
    request_id: str
    action_type: ActionType
    description: str
    details: Dict[str, Any]
    requested_by: str
    requested_at: datetime
    status: ApprovalStatus = ApprovalStatus.PENDING
    reviewed_by: Optional[str] = None
    reviewed_at: Optional[datetime] = None
    review_notes: Optional[str] = None
    expires_at: Optional[datetime] = None
    reversible: bool = True
    rollback_plan: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'request_id': self.request_id,
            'action_type': self.action_type.name,
            'description': self.description,
            'details': self.details,
            'requested_by': self.requested_by,
            'requested_at': self.requested_at.isoformat(),
            'status': self.status.value,
            'reviewed_by': self.reviewed_by,
            'reviewed_at': self.reviewed_at.isoformat() if self.reviewed_at else None,
            'review_notes': self.review_notes,
            'expires_at': self.expires_at.isoformat() if self.expires_at else None,
            'reversible': self.reversible,
            'rollback_plan': self.rollback_plan,
        }


class G0_HumanAuthority:
    """
    G0 - Human Authority Layer
    
    The ultimate authority. All major changes require human approval.
    Cannot be overridden by any AI component.
    """
    
    def __init__(self, db_path: str = "alphaalgo_data/governance.db"):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_database()
        self._pending_requests: Dict[str, ApprovalRequest] = {}
        self._lock = threading.Lock()
        
        # Actions that ALWAYS require human approval
        self.g0_required_actions: Set[ActionType] = {
            ActionType.DEPLOY_CODE,
            ActionType.MODIFY_RISK_PARAMS,
            ActionType.CHANGE_POSITION_SIZING,
            ActionType.MODIFY_ORDER_EXECUTION,
            ActionType.CONNECT_LIVE_BROKER,
            ActionType.ENABLE_LIVE_TRADING,
            ActionType.CHANGE_GOVERNANCE_RULES,
            ActionType.DELETE_DATA,
            ActionType.EXTERNAL_COMMUNICATION,
        }
        
        logger.info("G0 Human Authority initialized - All major changes require human approval")
    
    def _init_database(self):
        """Initialize SQLite database for approval tracking"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS approval_requests (
                    request_id TEXT PRIMARY KEY,
                    action_type TEXT NOT NULL,
                    description TEXT NOT NULL,
                    details TEXT NOT NULL,
                    requested_by TEXT NOT NULL,
                    requested_at TEXT NOT NULL,
                    status TEXT NOT NULL,
                    reviewed_by TEXT,
                    reviewed_at TEXT,
                    review_notes TEXT,
                    expires_at TEXT,
                    reversible INTEGER,
                    rollback_plan TEXT
                )
            """)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS approval_audit_log (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    request_id TEXT NOT NULL,
                    action TEXT NOT NULL,
                    actor TEXT NOT NULL,
                    timestamp TEXT NOT NULL,
                    details TEXT
                )
            """)
            conn.commit()
    
    def request_approval(
        self,
        action_type: ActionType,
        description: str,
        details: Dict[str, Any],
        requested_by: str = "G1_Controller",
        expires_hours: int = 24,
        reversible: bool = True,
        rollback_plan: Optional[str] = None
    ) -> ApprovalRequest:
        """
        Submit a request for human approval.
        
        All G0-level actions MUST go through this.
        """
        request_id = str(uuid.uuid4())[:8]
        now = datetime.now()
        
        request = ApprovalRequest(
            request_id=request_id,
            action_type=action_type,
            description=description,
            details=details,
            requested_by=requested_by,
            requested_at=now,
            expires_at=now + timedelta(hours=expires_hours),
            reversible=reversible,
            rollback_plan=rollback_plan,
        )
        
        with self._lock:
            self._pending_requests[request_id] = request
            self._save_request(request)
            self._log_audit(request_id, "REQUEST_CREATED", requested_by, description)
        
        logger.info(f"[G0] Approval request created: {request_id} - {description}")
        return request
    
    def approve(
        self,
        request_id: str,
        reviewed_by: str,
        notes: Optional[str] = None
    ) -> bool:
        """Human approves a request"""
        with self._lock:
            if request_id not in self._pending_requests:
                logger.warning(f"[G0] Request {request_id} not found")
                return False
            
            request = self._pending_requests[request_id]
            
            if request.status != ApprovalStatus.PENDING:
                logger.warning(f"[G0] Request {request_id} already processed: {request.status}")
                return False
            
            if request.expires_at and datetime.now() > request.expires_at:
                request.status = ApprovalStatus.EXPIRED
                self._save_request(request)
                logger.warning(f"[G0] Request {request_id} has expired")
                return False
            
            request.status = ApprovalStatus.APPROVED
            request.reviewed_by = reviewed_by
            request.reviewed_at = datetime.now()
            request.review_notes = notes
            
            self._save_request(request)
            self._log_audit(request_id, "APPROVED", reviewed_by, notes or "")
            
            logger.info(f"[G0] Request {request_id} APPROVED by {reviewed_by}")
            return True
    
    def reject(
        self,
        request_id: str,
        reviewed_by: str,
        reason: str
    ) -> bool:
        """Human rejects a request"""
        with self._lock:
            if request_id not in self._pending_requests:
                logger.warning(f"[G0] Request {request_id} not found")
                return False
            
            request = self._pending_requests[request_id]
            request.status = ApprovalStatus.REJECTED
            request.reviewed_by = reviewed_by
            request.reviewed_at = datetime.now()
            request.review_notes = reason
            
            self._save_request(request)
            self._log_audit(request_id, "REJECTED", reviewed_by, reason)
            
            logger.info(f"[G0] Request {request_id} REJECTED by {reviewed_by}: {reason}")
            return True
    
    def is_approved(self, request_id: str) -> bool:
        """Check if a request has been approved"""
        with self._lock:
            if request_id in self._pending_requests:
                return self._pending_requests[request_id].status == ApprovalStatus.APPROVED
            return False
    
    def get_pending_requests(self) -> List[ApprovalRequest]:
        """Get all pending approval requests"""
        with self._lock:
            return [r for r in self._pending_requests.values() 
                    if r.status == ApprovalStatus.PENDING]
    
    def requires_approval(self, action_type: ActionType) -> bool:
        """Check if an action requires G0 human approval"""
        return action_type in self.g0_required_actions
    
    def _save_request(self, request: ApprovalRequest):
        """Save request to database"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                INSERT OR REPLACE INTO approval_requests
                (request_id, action_type, description, details, requested_by,
                 requested_at, status, reviewed_by, reviewed_at, review_notes,
                 expires_at, reversible, rollback_plan)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                request.request_id,
                request.action_type.name,
                request.description,
                json.dumps(request.details),
                request.requested_by,
                request.requested_at.isoformat(),
                request.status.value,
                request.reviewed_by,
                request.reviewed_at.isoformat() if request.reviewed_at else None,
                request.review_notes,
                request.expires_at.isoformat() if request.expires_at else None,
                1 if request.reversible else 0,
                request.rollback_plan,
            ))
            conn.commit()
    
    def _log_audit(self, request_id: str, action: str, actor: str, details: str):
        """Log audit trail"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                INSERT INTO approval_audit_log
                (request_id, action, actor, timestamp, details)
                VALUES (?, ?, ?, ?, ?)
            """, (request_id, action, actor, datetime.now().isoformat(), details))
            conn.commit()


class G2_MiniAI:
    """
    G2 - Mini-AI Helper
    
    Specialized helper AI with a specific role.
    Must obey the Central Controller (G1).
    Cannot make decisions outside its role.
    """
    
    def __init__(
        self,
        mini_ai_id: str,
        role: str,
        capabilities: List[str],
        controller: 'G1_Controller'
    ):
        self.mini_ai_id = mini_ai_id
        self.role = role
        self.capabilities = set(capabilities)
        self.controller = controller
        self.is_active = True
        self.created_at = datetime.now()
        self.task_count = 0
        self.error_count = 0
        
        logger.info(f"[G2] Mini-AI created: {mini_ai_id} - Role: {role}")
    
    def can_execute(self, action: str) -> bool:
        """Check if this mini-AI can execute an action"""
        return action in self.capabilities and self.is_active
    
    async def execute_task(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a task within capabilities"""
        if not self.is_active:
            return {'success': False, 'error': 'Mini-AI is deactivated'}
        
        action = task.get('action')
        if not self.can_execute(action):
            return {'success': False, 'error': f'Action {action} not in capabilities'}
        
        # Report to controller before execution
        if not self.controller.authorize_mini_ai_action(self.mini_ai_id, action):
            return {'success': False, 'error': 'Controller denied action'}
        try:
        
            self.task_count += 1
            result = await self._do_task(task)
            return {'success': True, 'result': result}
        except Exception as e:
            self.error_count += 1
            logger.error(f"[G2] {self.mini_ai_id} error: {e}")
            return {'success': False, 'error': str(e)}
    
    async def _do_task(self, task: Dict[str, Any]) -> Any:
        """Override in subclasses for specific functionality"""
        return {'status': 'completed', 'task': task}
    
    def deactivate(self, reason: str):
        """Deactivate this mini-AI"""
        self.is_active = False
        logger.warning(f"[G2] {self.mini_ai_id} deactivated: {reason}")
    
    def get_status(self) -> Dict[str, Any]:
        """Get mini-AI status"""
        return {
            'mini_ai_id': self.mini_ai_id,
            'role': self.role,
            'is_active': self.is_active,
            'capabilities': list(self.capabilities),
            'task_count': self.task_count,
            'error_count': self.error_count,
            'created_at': self.created_at.isoformat(),
        }


class G1_Controller:
    """
    G1 - Central Controller
    
    Coordinates all modules, maintains stability, prevents dangerous changes.
    Reports to G0 (Human Authority) for major decisions.
    Commands G2 (Mini-AIs) for specialized tasks.
    """
    
    def __init__(self, human_authority: Optional[G0_HumanAuthority] = None):
        self.human_authority = human_authority or G0_HumanAuthority()
        self.mini_ais: Dict[str, G2_MiniAI] = {}
        self.system_state = {
            'mode': 'SAFE',  # SAFE, PAPER, LIVE
            'trading_enabled': False,
            'data_connected': False,
            'broker_connected': False,
            'risk_engine_ok': True,
            'architecture_stable': True,
        }
        self._lock = threading.Lock()
        self._action_log: List[Dict[str, Any]] = []
        
        # Actions G1 can approve without G0
        self.g1_allowed_actions: Set[ActionType] = {
            ActionType.CREATE_MINI_AI,
            ActionType.MODIFY_STRATEGY_PARAMS,
            ActionType.UPDATE_DATA_SOURCES,
            ActionType.RUN_BACKTEST,
            ActionType.GENERATE_REPORT,
            ActionType.OPTIMIZE_PARAMETERS,
        }
        
        logger.info("[G1] Central Controller initialized")
    
    def request_action(
        self,
        action_type: ActionType,
        description: str,
        details: Dict[str, Any],
        requester: str = "system"
    ) -> Tuple[bool, str, Optional[str]]:
        """
        Request to perform an action.
        
        Returns: (allowed, message, request_id if pending approval)
        """
        # Check if G0 approval required
        if self.human_authority.requires_approval(action_type):
            request = self.human_authority.request_approval(
                action_type=action_type,
                description=description,
                details=details,
                requested_by=requester,
            )
            return (
                False,
                f"Action requires human approval. Request ID: {request.request_id}",
                request.request_id
            )
        
        # G1 can approve these actions
        if action_type in self.g1_allowed_actions:
            self._log_action(action_type, description, requester, "G1_APPROVED")
            return (True, "Action approved by G1 Controller", None)
        
        # G2-level actions - delegate to mini-AIs
        self._log_action(action_type, description, requester, "G2_DELEGATED")
        return (True, "Action delegated to Mini-AI", None)
    
    def check_approval_status(self, request_id: str) -> ApprovalStatus:
        """Check status of a pending approval"""
        if request_id in self.human_authority._pending_requests:
            return self.human_authority._pending_requests[request_id].status
        return ApprovalStatus.EXPIRED
    
    def create_mini_ai(
        self,
        role: str,
        capabilities: List[str]
    ) -> Optional[G2_MiniAI]:
        """Create a new Mini-AI helper"""
        mini_ai_id = f"mini_ai_{role}_{uuid.uuid4().hex[:6]}"
        
        mini_ai = G2_MiniAI(
            mini_ai_id=mini_ai_id,
            role=role,
            capabilities=capabilities,
            controller=self
        )
        
        with self._lock:
            self.mini_ais[mini_ai_id] = mini_ai
        
        logger.info(f"[G1] Created Mini-AI: {mini_ai_id}")
        return mini_ai
    
    def authorize_mini_ai_action(self, mini_ai_id: str, action: str) -> bool:
        """Authorize a Mini-AI to perform an action"""
        with self._lock:
            if mini_ai_id not in self.mini_ais:
                return False
            
            mini_ai = self.mini_ais[mini_ai_id]
            if not mini_ai.is_active:
                return False
            
            # Check system state
            if not self.system_state['architecture_stable']:
                logger.warning(f"[G1] Denying {action} - architecture unstable")
                return False
            
            return True
    
    def update_system_state(self, updates: Dict[str, Any]):
        """Update system state"""
        with self._lock:
            for key, value in updates.items():
                if key in self.system_state:
                    old_value = self.system_state[key]
                    self.system_state[key] = value
                    if old_value != value:
                        logger.info(f"[G1] System state: {key} = {value}")
    
    def get_system_state(self) -> Dict[str, Any]:
        """Get current system state"""
        with self._lock:
            return self.system_state.copy()
    
    def is_safe_to_trade(self) -> Tuple[bool, List[str]]:
        """Check if system is safe to trade"""
        issues = []
        
        with self._lock:
            if not self.system_state['trading_enabled']:
                issues.append("Trading is disabled")
            if not self.system_state['data_connected']:
                issues.append("Data feed not connected")
            if not self.system_state['broker_connected']:
                issues.append("Broker not connected")
            if not self.system_state['risk_engine_ok']:
                issues.append("Risk engine has issues")
            if not self.system_state['architecture_stable']:
                issues.append("Architecture is unstable")
        
        return (len(issues) == 0, issues)
    
    def emergency_stop(self, reason: str):
        """Emergency stop all trading"""
        with self._lock:
            self.system_state['trading_enabled'] = False
            self.system_state['mode'] = 'SAFE'
            
            # Deactivate all mini-AIs
            for mini_ai in self.mini_ais.values():
                mini_ai.deactivate(f"Emergency stop: {reason}")
        
        logger.critical(f"[G1] EMERGENCY STOP: {reason}")
        
        # Log to G0
        self.human_authority.request_approval(
            action_type=ActionType.ENABLE_LIVE_TRADING,
            description=f"Emergency stop triggered: {reason}. Re-enable requires approval.",
            details={'reason': reason, 'timestamp': datetime.now().isoformat()},
            requested_by="G1_Controller",
        )
    
    def _log_action(
        self,
        action_type: ActionType,
        description: str,
        requester: str,
        decision: str
    ):
        """Log action for audit"""
        self._action_log.append({
            'timestamp': datetime.now().isoformat(),
            'action_type': action_type.name,
            'description': description,
            'requester': requester,
            'decision': decision,
        })
    
    def get_pending_approvals(self) -> List[Dict[str, Any]]:
        """Get all pending human approvals"""
        return [r.to_dict() for r in self.human_authority.get_pending_requests()]
    
    def get_mini_ai_status(self) -> List[Dict[str, Any]]:
        """Get status of all Mini-AIs"""
        with self._lock:
            return [ai.get_status() for ai in self.mini_ais.values()]


class CentralController(G1_Controller):
    """
    Main entry point for the AlphaAlgo governance system.
    
    Inherits from G1_Controller and provides the complete
    G0/G1/G2 hierarchy interface.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        super().__init__()
        
        # Initialize default Mini-AIs
        self._init_default_mini_ais()
        
        logger.info("[AlphaAlgo] Central Controller fully initialized")
    
    def _init_default_mini_ais(self):
        """Create default Mini-AI helpers"""
        default_roles = [
            ('data_cleaner', ['CLEAN_DATA', 'VALIDATE_DATA', 'DETECT_ANOMALIES']),
            ('feature_engineer', ['ENGINEER_FEATURES', 'TRANSFORM_DATA', 'SELECT_FEATURES']),
            ('strategy_tester', ['RUN_BACKTEST', 'VALIDATE_STRATEGY', 'ANALYZE_RESULTS']),
            ('risk_validator', ['VALIDATE_RISK', 'CHECK_LIMITS', 'CALCULATE_EXPOSURE']),
            ('security_guardian', ['SCAN_THREATS', 'VALIDATE_CREDENTIALS', 'MONITOR_ACCESS']),
            ('architecture_analyzer', ['ANALYZE_ARCHITECTURE', 'DETECT_ISSUES', 'SUGGEST_FIXES']),
            ('l2_interpreter', ['INTERPRET_L2_DATA', 'ANALYZE_ORDERBOOK', 'DETECT_IMBALANCE']),
            ('sentiment_parser', ['PARSE_SENTIMENT', 'ANALYZE_NEWS', 'SCORE_SENTIMENT']),
            ('broker_connector', ['CONNECT_BROKER', 'VALIDATE_CONNECTION', 'MONITOR_STATUS']),
        ]
        
        for role, capabilities in default_roles:
            self.create_mini_ai(role, capabilities)
    
    def propose_change(
        self,
        change_type: str,
        description: str,
        details: Dict[str, Any],
        rollback_plan: str
    ) -> ApprovalRequest:
        """
        Propose a change following the governance rules:
        Propose → Test → Human Approve → Deploy
        """
        # Map change type to action type
        action_map = {
            'risk': ActionType.MODIFY_RISK_PARAMS,
            'position_sizing': ActionType.CHANGE_POSITION_SIZING,
            'execution': ActionType.MODIFY_ORDER_EXECUTION,
            'code': ActionType.DEPLOY_CODE,
            'broker': ActionType.CONNECT_LIVE_BROKER,
            'trading': ActionType.ENABLE_LIVE_TRADING,
        }
        
        action_type = action_map.get(change_type, ActionType.DEPLOY_CODE)
        
        return self.human_authority.request_approval(
            action_type=action_type,
            description=description,
            details=details,
            requested_by="AlphaAlgo",
            reversible=True,
            rollback_plan=rollback_plan,
        )
    
    def get_governance_status(self) -> Dict[str, Any]:
        """Get complete governance status"""
        return {
            'g0_pending_approvals': len(self.human_authority.get_pending_requests()),
            'g1_system_state': self.get_system_state(),
            'g2_mini_ais': len(self.mini_ais),
            'g2_active_mini_ais': sum(1 for ai in self.mini_ais.values() if ai.is_active),
            'safe_to_trade': self.is_safe_to_trade(),
        }


# Convenience function
def create_alphaalgo_controller(config: Optional[Dict[str, Any]] = None) -> CentralController:
    """Create and return the AlphaAlgo Central Controller"""
    return CentralController(config)
