"""
AlphaAlgo Orchestrator

The Master Controller that coordinates all AlphaAlgo systems:
- G0/G1/G2 Governance Hierarchy
- Broker Hub
- Data Pipeline
- Security Core
- Fail-Safe System
- Self-Repair Engine
- Mini-AI Factory

IDENTITY: The AI is the student → The market is the teacher.
"""

import asyncio
import json
import logging
import os
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Tuple, Set

from .central_controller import CentralController, ActionType, ApprovalStatus
from .governance_system import GovernanceSystem, ChangeCategory, GovernanceLevel
from .broker_hub import BrokerHub, BrokerType, BrokerCredentials
from .data_pipeline import UnifiedDataPipeline, DataType, DataSourceConfig
from .security_core import SecurityCore, ThreatLevel
from .fail_safe import FailSafeSystem, TradingMode, SafetyCheck, SystemHealth
from .self_repair import SelfRepairEngine
from .mini_ai_factory import MiniAIFactory, MiniAIRole


@dataclass
class SafetyCheckResult:
    """Result of a safety check"""
    check: SafetyCheck
    passed: bool
    message: str
    value: Any = None

logger = logging.getLogger(__name__)


@dataclass
class AlphaAlgoConfig:
    """Configuration for AlphaAlgo"""
    data_path: str = "alphaalgo_data"
    root_path: str = "trading_bot"
    master_password: Optional[str] = None
    auto_connect_simulation: bool = True
    enable_self_repair: bool = True
    enable_mini_ais: bool = True


class AlphaAlgoOrchestrator:
    """
    AlphaAlgo Master Orchestrator
    
    Coordinates all systems following the governance hierarchy:
    G0 — Human Authority (approves/rejects major changes)
    G1 — Central Controller (coordinates modules, maintains stability)
    G2 — Mini-AIs (specialized helpers that obey G1)
    
    IDENTITY: The AI is the student → The market is the teacher.
    """
    
    def __init__(self, config: Optional[AlphaAlgoConfig] = None):
        try:
            self.config = config or AlphaAlgoConfig()
            self._initialized = False
        
            # Core systems
            self.controller = CentralController()
            self.governance = GovernanceSystem(
                f"{self.config.data_path}/governance.db"
            )
            self.broker_hub = BrokerHub(
                f"{self.config.data_path}/vault",
                require_approval=True
            )
            self.data_pipeline = UnifiedDataPipeline(
                f"{self.config.data_path}/data_pipeline.db"
            )
            self.security = SecurityCore(self.config.data_path)
            self.fail_safe = FailSafeSystem()
            self.self_repair = SelfRepairEngine(
                self.config.root_path,
                f"{self.config.data_path}/self_repair.db"
            )
        
            # Mini-AI Factory
            self.mini_ai_factory = MiniAIFactory(self._controller_callback)
        
            # Set up broker approval callback
            self.broker_hub.set_approval_callback(self._request_broker_approval)
        
            # Register fail-safe checks
            self._register_safety_checks()
        
            logger.info("[AlphaAlgo] Orchestrator created")
        except Exception as e:
            logger.error(f"Error in __init__: {e}")
            raise
    
    async def initialize(self, master_password: Optional[str] = None) -> Tuple[bool, str]:
        """
        Initialize AlphaAlgo system.
        
        Requires master password for security vault.
        """
        try:
            password = master_password or self.config.master_password
        
            if not password:
                return (False, "Master password required for initialization")
        
            # === FIRST: Analyze architecture, find issues, propose fixes ===
            logger.info("[AlphaAlgo] Running initial architecture analysis and repair proposal...")
            self.self_repair.scan_and_propose()
            logger.info("[AlphaAlgo] Architecture scan complete. Repair proposals ready.")

            # Initialize security
            if not self.security.initialize(password):
                return (False, "Failed to initialize security system")
        
            # Initialize broker vault
            if not self.broker_hub.initialize_vault(password):
                return (False, "Failed to initialize broker vault")
        
            # Create Mini-AIs if enabled
            if self.config.enable_mini_ais:
                self.mini_ai_factory.create_all()
        
            # Connect to simulation broker by default
            if self.config.auto_connect_simulation:
                await self.broker_hub.connect(BrokerType.SIMULATION)
        
            # Connect data sources
            await self.data_pipeline.connect_all()
        
            # Run initial safety checks
            await self.fail_safe.run_all_checks()
        
            self._initialized = True
            logger.info("[AlphaAlgo] System initialized successfully")
        
            return (True, "AlphaAlgo initialized successfully")
        except Exception as e:
            logger.error(f"Error in initialize: {e}")
            raise
    
    def _controller_callback(self, action: str, *args) -> Any:
        """Callback for Mini-AIs to communicate with controller"""
        try:
            if action == 'authorize':
                mini_ai_id, task_action = args
                return self.controller.authorize_mini_ai_action(mini_ai_id, task_action)
            return None
        except Exception as e:
            logger.error(f"Error in _controller_callback: {e}")
            raise
    
    def _request_broker_approval(self, action: str, details: Dict[str, Any]) -> str:
        """Request approval for broker connection"""
        try:
            request = self.controller.human_authority.request_approval(
                action_type=ActionType.CONNECT_LIVE_BROKER,
                description=f"Connect to {details.get('broker_type', 'unknown')} broker",
                details=details,
                requested_by="BrokerHub",
            )
            return request.request_id
        except Exception as e:
            logger.error(f"Error in _request_broker_approval: {e}")
            raise
    
    def _register_safety_checks(self):
        """Register safety check callbacks"""
        try:
            self.fail_safe.register_check(
                SafetyCheck.DATA_AVAILABLE,
                lambda: self._check_data_available()
            )
            self.fail_safe.register_check(
                SafetyCheck.BROKER_CONNECTED,
                lambda: self._check_broker_connected()
            )
            self.fail_safe.register_check(
                SafetyCheck.ARCHITECTURE_STABLE,
                lambda: self._check_architecture_stable()
            )
        except Exception as e:
            logger.error(f"Error in _register_safety_checks: {e}")
            raise
    
    def _check_data_available(self):
        """Check if data is available"""
        try:
            from .fail_safe import SafetyCheckResult
        
            status = self.data_pipeline.get_source_status()
            connected = sum(1 for s in status.values() if s['status'] == 'connected')
        
            return SafetyCheckResult(
                check=SafetyCheck.DATA_AVAILABLE,
                passed=connected > 0,
                message=f"{connected} data sources connected",
                value=connected,
            )
        except Exception as e:
            logger.error(f"Error in _check_data_available: {e}")
            raise
    
    def _check_broker_connected(self):
        """Check if broker is connected"""
        
        try:
            connections = self.broker_hub.get_all_connections()
            connected = any(c['status'] == 'connected' for c in connections.values())
        
            return SafetyCheckResult(
                check=SafetyCheck.BROKER_CONNECTED,
                passed=connected,
                message="Broker connected" if connected else "No broker connected",
            )
        except Exception as e:
            logger.error(f"Error in _check_broker_connected: {e}")
            raise
    
    def _check_architecture_stable(self):
        """Check if architecture is stable"""
        
        # Run quick analysis
        try:
            summary = self.self_repair.analyzer.get_summary()
            critical = summary.get('by_severity', {}).get('critical', 0)
        
            return SafetyCheckResult(
                check=SafetyCheck.ARCHITECTURE_STABLE,
                passed=critical == 0,
                message=f"Architecture stable" if critical == 0 else f"{critical} critical issues",
                value=critical,
            )
        except Exception as e:
            logger.error(f"Error in _check_architecture_stable: {e}")
            raise
    
    # ==================== PUBLIC API ====================
    
    async def can_trade(self) -> Tuple[bool, str]:
        """
        Check if trading is allowed.
        
        Returns (allowed, reason).
        """
        try:
            if not self._initialized:
                return (False, "System not initialized")
        
            # Run safety checks
            status = await self.fail_safe.run_all_checks()
        
            return self.fail_safe.can_trade()
        except Exception as e:
            logger.error(f"Error in can_trade: {e}")
            raise
    
    async def request_live_trading(self, reason: str) -> Tuple[bool, str]:
        """
        Request to enable live trading.
        
        Requires human approval.
        """
        try:
            allowed, result, request_id = self.controller.request_action(
                ActionType.ENABLE_LIVE_TRADING,
                f"Enable live trading: {reason}",
                {'reason': reason},
                "user"
            )
        
            if allowed:
                return (True, "Live trading enabled")
            else:
                return (False, result)
        except Exception as e:
            logger.error(f"Error in request_live_trading: {e}")
            raise
    
    def approve_request(self, request_id: str, approved_by: str) -> bool:
        """Human approves a pending request"""
        return self.controller.human_authority.approve(request_id, approved_by)
    
    def reject_request(self, request_id: str, rejected_by: str, reason: str) -> bool:
        """Human rejects a pending request"""
        return self.controller.human_authority.reject(request_id, rejected_by, reason)
    
    def get_pending_approvals(self) -> List[Dict[str, Any]]:
        """Get all pending approval requests"""
        return self.controller.get_pending_approvals()
    
    async def connect_broker(
        self,
        broker_type: BrokerType,
        credentials: Optional[BrokerCredentials] = None
    ) -> Tuple[bool, str]:
        """
        Connect to a broker.
        
        For live brokers, requires human approval.
        """
        try:
            if credentials:
                self.broker_hub.store_credentials(broker_type, credentials)
        
            return await self.broker_hub.connect(broker_type)
        except Exception as e:
            logger.error(f"Error in connect_broker: {e}")
            raise
    
    def get_broker_template(self, broker_type: BrokerType) -> Dict[str, str]:
        """Get credential template for human to fill"""
        return self.broker_hub.get_credential_template(broker_type)
    
    async def fetch_data(
        self,
        data_type: DataType,
        symbol: str
    ) -> Optional[Dict[str, Any]]:
        """Fetch market data"""
        try:
            data_point = await self.data_pipeline.fetch_data(data_type, symbol)
            if data_point:
                return data_point.data
            return None
        except Exception as e:
            logger.error(f"Error in fetch_data: {e}")
            raise
    
    def propose_change(
        self,
        category: ChangeCategory,
        title: str,
        description: str,
        rationale: str,
        expected_impact: str,
        risk_assessment: str,
        rollback_plan: str
    ) -> Dict[str, Any]:
        """
        Propose a change to the system.
        
        Follows: Propose → Test → Human Approve → Deploy
        """
        try:
            change = self.governance.propose_change(
                category=category,
                title=title,
                description=description,
                rationale=rationale,
                expected_impact=expected_impact,
                risk_assessment=risk_assessment,
                rollback_plan=rollback_plan,
            )
        
            return change.to_dict()
        except Exception as e:
            logger.error(f"Error in propose_change: {e}")
            raise
    
    def approve_change(self, change_id: str, approved_by: str) -> bool:
        """Human approves a proposed change"""
        return self.governance.approve_change(change_id, approved_by)
    
    def get_pending_changes(self) -> List[Dict[str, Any]]:
        """Get all pending changes"""
        return [c.to_dict() for c in self.governance.get_pending_changes()]
    
    def scan_architecture(self) -> Dict[str, Any]:
        """Scan architecture for issues"""
        try:
            proposals = self.self_repair.scan_and_propose()
            return {
                'summary': self.self_repair.analyzer.get_summary(),
                'proposals': [
                    {
                        'id': p.proposal_id,
                        'title': p.title,
                        'type': p.proposal_type.value,
                        'risk': p.risk_level,
                    }
                    for p in proposals
                ],
            }
        except Exception as e:
            logger.error(f"Error in scan_architecture: {e}")
            raise
    
    def get_repair_report(self) -> str:
        """Get human-readable repair report"""
        return self.self_repair.get_analysis_report()
    
    def emergency_stop(self, reason: str):
        """Emergency stop all trading"""
        try:
            self.controller.emergency_stop(reason)
            self.fail_safe.emergency_stop(reason)
            logger.critical(f"[AlphaAlgo] EMERGENCY STOP: {reason}")
        except Exception as e:
            logger.error(f"Error in emergency_stop: {e}")
            raise
    
    def get_system_status(self) -> Dict[str, Any]:
        """Get comprehensive system status"""
        try:
            fail_safe_status = self.fail_safe.get_status()
        
            return {
                'initialized': self._initialized,
                'timestamp': datetime.now().isoformat(),
                'governance': self.controller.get_governance_status(),
                'trading': {
                    'mode': fail_safe_status.trading_mode.value if fail_safe_status else 'unknown',
                    'health': fail_safe_status.health.value if fail_safe_status else 'unknown',
                    'can_trade': self.fail_safe.can_trade()[0] if fail_safe_status else False,
                    'issues': fail_safe_status.issues if fail_safe_status else [],
                },
                'brokers': self.broker_hub.get_all_connections(),
                'data_sources': self.data_pipeline.get_source_status(),
                'security': self.security.get_security_status(),
                'mini_ais': self.mini_ai_factory.get_status_report(),
                'pending_approvals': len(self.get_pending_approvals()),
                'pending_changes': len(self.get_pending_changes()),
            }
        except Exception as e:
            logger.error(f"Error in get_system_status: {e}")
            raise
    
    def get_identity(self) -> Dict[str, str]:
        """Get AlphaAlgo identity"""
        return {
            'name': 'AlphaAlgo',
            'role': 'Governed, Safe, Self-Evolving Trading Intelligence',
            'identity': 'The AI is the student → The market is the teacher',
            'governance': 'G0 (Human) → G1 (Controller) → G2 (Mini-AIs)',
            'principles': [
                'Propose → Test → Human Approve → Deploy',
                'Every change must be reversible, logged, explainable',
                'NO changes to risk without full explanation',
                'Improve slowly, safely, methodically',
                'I refuse to trade until conditions are safe',
            ],
        }


# Convenience functions
def create_alphaalgo(config: Optional[AlphaAlgoConfig] = None) -> AlphaAlgoOrchestrator:
    """Create AlphaAlgo orchestrator"""
    return AlphaAlgoOrchestrator(config)


async def quick_start(master_password: str) -> AlphaAlgoOrchestrator:
    """Quick start AlphaAlgo with default configuration"""
    try:
        alphaalgo = AlphaAlgoOrchestrator()
        await alphaalgo.initialize(master_password)
        return alphaalgo
    except Exception as e:
        logger.error(f"Error in quick_start: {e}")
        raise
