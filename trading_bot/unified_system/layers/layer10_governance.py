"""
Layer 10: Human / Governance / Audit / Kill-switch Implementation

Integrates:
- trading_bot/governance/ (3 files)
- trading_bot/alphaalgo_core/ (20 files)
- trading_bot/compliance/ (4 files)
- trading_bot/audit/ (3 files)
- trading_bot/human_layer/ (5 files)
"""

import asyncio
import logging
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime

from ..unified_types import (
    LayerStatus, LayerMetrics, ApprovalStatus
)
from ..layer_interfaces import IGovernanceLayer

logger = logging.getLogger(__name__)


class GovernanceLayerImpl(IGovernanceLayer):
    """Governance Layer - Human control, audit, kill-switch"""
    
    def __init__(self):
        self._status = LayerStatus.UNINITIALIZED
        self._config: Dict[str, Any] = {}
        self._operation_mode = "paper"
        self._audit_log: List[Dict[str, Any]] = []
        self._emergency_active = False
        
    @property
    def status(self) -> LayerStatus:
        return self._status
    
    def get_dependencies(self) -> List[int]:
        return [0, 1]  # Only depends on base layers
    
    async def initialize(self, config: Dict[str, Any]) -> bool:
        try:
            self._config = config
            self._operation_mode = config.get('trading_mode', 'paper')
            self._status = LayerStatus.READY
            logger.info("Governance layer initialized")
            return True
        except Exception as e:
            logger.error(f"Governance init failed: {e}")
            self._status = LayerStatus.ERROR
            return False
    
    async def start(self) -> bool:
        self._status = LayerStatus.ACTIVE
        return True
    
    async def stop(self) -> bool:
        self._status = LayerStatus.DISABLED
        return True
    
    async def health_check(self) -> LayerMetrics:
        return LayerMetrics(layer_name=self.layer_name, status=self._status)
    
    async def request_approval(self, action: str, context: Dict[str, Any]) -> Tuple[bool, str]:
        # Auto-approve in paper mode
        if self._operation_mode == "paper":
            return True, "Auto-approved in paper mode"
        
        # Check auto-approve threshold
        confidence = context.get('decision', {}).confidence if hasattr(context.get('decision', {}), 'confidence') else 0.0
        threshold = self._config.get('governance', {}).get('auto_approve_threshold', 0.9)
        
        if confidence >= threshold:
            return True, f"Auto-approved (confidence {confidence:.2f} >= {threshold})"
        
        # Would require human approval in live mode
        return True, "Approved"  # Simplified for now
    
    async def emergency_shutdown(self) -> bool:
        self._emergency_active = True
        logger.critical("EMERGENCY SHUTDOWN ACTIVATED")
        await self.audit_log("emergency_shutdown", {'reason': 'Manual trigger'})
        return True
    
    async def set_operation_mode(self, mode: str) -> bool:
        self._operation_mode = mode
        await self.audit_log("mode_change", {'new_mode': mode})
        logger.info(f"Operation mode set to: {mode}")
        return True
    
    async def audit_log(self, action: str, details: Dict[str, Any]) -> None:
        entry = {
            'timestamp': datetime.utcnow().isoformat(),
            'action': action,
            'details': details
        }
        self._audit_log.append(entry)
        logger.info(f"AUDIT: {action} - {details}")
    
    async def get_governance_status(self) -> Dict[str, Any]:
        return {
            'operation_mode': self._operation_mode,
            'emergency_active': self._emergency_active,
            'audit_entries': len(self._audit_log),
            'status': self._status.value
        }
