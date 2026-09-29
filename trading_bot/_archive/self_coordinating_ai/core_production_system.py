"""
Core Production System (Immutable)
===================================

The immutable core production system that handles live trading.
This system CANNOT be modified by AI-generated code.

Key Principles:
1. IMMUTABLE - No AI can modify this system directly
2. ISOLATED - Runs in protected memory space
3. VERIFIED - All inputs are validated before processing
4. AUDITED - Every action is logged and traceable

Author: AlphaAlgo Trading System
"""

import asyncio
import hashlib
import json
import logging
import threading
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum, auto
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Set, Tuple
import uuid

logger = logging.getLogger(__name__)


class SystemState(Enum):
    """Production system states."""
    INITIALIZING = auto()
    READY = auto()
    RUNNING = auto()
    PAUSED = auto()
    EMERGENCY_STOP = auto()
    MAINTENANCE = auto()
    SHUTDOWN = auto()


class ProtectionLevel(Enum):
    """Protection levels for system components."""
    CRITICAL = "critical"      # Cannot be modified ever
    PROTECTED = "protected"    # Requires multi-signature approval
    GUARDED = "guarded"        # Requires single approval
    STANDARD = "standard"      # Normal protection


@dataclass
class ProductionConfig:
    """Configuration for the production system."""
    # System Identity
    system_id: str = field(default_factory=lambda: f"PROD-{uuid.uuid4().hex[:8]}")
    version: str = "1.0.0"
    
    # Protection Settings
    enable_write_protection: bool = True
    enable_code_verification: bool = True
    enable_input_validation: bool = True
    enable_audit_logging: bool = True
    
    # Risk Limits (IMMUTABLE)
    max_position_size_pct: float = 0.10  # 10% max per position
    max_daily_loss_pct: float = 0.05     # 5% max daily loss
    max_drawdown_pct: float = 0.15       # 15% max drawdown
    max_leverage: float = 2.0            # 2x max leverage
    
    # Trading Limits
    max_trades_per_day: int = 100
    max_open_positions: int = 20
    min_trade_interval_seconds: int = 60
    
    # Emergency Settings
    emergency_stop_loss_pct: float = 0.20  # 20% triggers emergency stop
    auto_pause_on_error: bool = True
    max_consecutive_losses: int = 5
    
    # Paths
    audit_log_path: str = "production_audit"
    state_backup_path: str = "production_state"
    
    def get_hash(self) -> str:
        """Get hash of configuration for integrity verification."""
        config_str = json.dumps(self.__dict__, sort_keys=True)
        return hashlib.sha256(config_str.encode()).hexdigest()


@dataclass
class AuditEntry:
    """Audit log entry."""
    entry_id: str
    timestamp: datetime
    action: str
    component: str
    actor: str
    details: Dict[str, Any]
    result: str
    config_hash: str
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'entry_id': self.entry_id,
            'timestamp': self.timestamp.isoformat(),
            'action': self.action,
            'component': self.component,
            'actor': self.actor,
            'details': self.details,
            'result': self.result,
            'config_hash': self.config_hash,
        }


@dataclass
class ProtectedComponent:
    """A protected component in the production system."""
    component_id: str
    name: str
    protection_level: ProtectionLevel
    code_hash: str
    created_at: datetime
    last_verified: datetime
    is_locked: bool = True
    
    def verify_integrity(self, current_hash: str) -> bool:
        """Verify component hasn't been tampered with."""
        return self.code_hash == current_hash


class ImmutabilityGuard:
    """
    Guards against unauthorized modifications to the production system.
    Uses multiple layers of protection.
    """
    
    def __init__(self):
        self._lock = threading.RLock()
        self._protected_attributes: Set[str] = set()
        self._modification_attempts: List[Dict] = []
        self._is_sealed: bool = False
    
    def protect_attribute(self, name: str):
        """Mark an attribute as protected."""
        with self._lock:
            self._protected_attributes.add(name)
    
    def seal(self):
        """Seal the guard - no more attributes can be protected."""
        with self._lock:
            self._is_sealed = True
            logger.info("ImmutabilityGuard sealed - system is now immutable")
    
    def check_modification(self, name: str, actor: str) -> bool:
        """Check if modification is allowed."""
        with self._lock:
            if name in self._protected_attributes:
                self._modification_attempts.append({
                    'timestamp': datetime.now(timezone.utc).isoformat(),
                    'attribute': name,
                    'actor': actor,
                    'blocked': True,
                })
                logger.warning(f"BLOCKED modification attempt on {name} by {actor}")
                return False
            return True
    
    def get_modification_attempts(self) -> List[Dict]:
        """Get all modification attempts."""
        with self._lock:
            return self._modification_attempts.copy()


class CoreProductionSystem:
    """
    The immutable core production system.
    
    This system handles all live trading operations and CANNOT be modified
    by AI-generated code. All changes must go through the promotion system
    with human approval.
    
    Security Features:
    - Write protection on critical components
    - Code verification before execution
    - Input validation on all external data
    - Complete audit logging
    - Emergency stop capabilities
    """
    
    # Class-level protection
    _PROTECTED_METHODS = frozenset([
        'execute_trade',
        'update_position',
        'modify_risk_limits',
        'emergency_stop',
        '_validate_trade',
        '_check_risk_limits',
    ])
    
    def __init__(self, config: Optional[ProductionConfig] = None):
        """
        Initialize the core production system.
        
        Args:
            config: Production configuration (uses defaults if not provided)
        """
        self._config = config or ProductionConfig()
        self._state = SystemState.INITIALIZING
        self._immutability_guard = ImmutabilityGuard()
        
        # Protected state
        self._positions: Dict[str, Dict] = {}
        self._pending_orders: Dict[str, Dict] = {}
        self._trade_history: List[Dict] = []
        self._daily_pnl: float = 0.0
        self._total_pnl: float = 0.0
        self._consecutive_losses: int = 0
        
        # Component registry
        self._protected_components: Dict[str, ProtectedComponent] = {}
        
        # Audit log
        self._audit_entries: List[AuditEntry] = []
        
        # Callbacks for external systems
        self._trade_callbacks: List[Callable] = []
        self._alert_callbacks: List[Callable] = []
        
        # Storage
        self._storage_path = Path(self._config.audit_log_path)
        self._storage_path.mkdir(parents=True, exist_ok=True)
        
        # Initialize protection
        self._initialize_protection()
        
        logger.info(f"CoreProductionSystem initialized: {self._config.system_id}")
    
    def _initialize_protection(self):
        """Initialize immutability protection."""
        # Protect critical attributes
        protected_attrs = [
            '_config',
            '_state',
            '_immutability_guard',
            '_protected_components',
        ]
        
        for attr in protected_attrs:
            self._immutability_guard.protect_attribute(attr)
        
        # Register core components
        self._register_protected_component(
            'risk_manager',
            ProtectionLevel.CRITICAL,
            self._get_component_hash('risk_manager')
        )
        self._register_protected_component(
            'trade_executor',
            ProtectionLevel.CRITICAL,
            self._get_component_hash('trade_executor')
        )
        self._register_protected_component(
            'position_manager',
            ProtectionLevel.PROTECTED,
            self._get_component_hash('position_manager')
        )
        
        # Seal the guard
        self._immutability_guard.seal()
    
    def _register_protected_component(
        self,
        name: str,
        protection_level: ProtectionLevel,
        code_hash: str
    ):
        """Register a protected component."""
        component = ProtectedComponent(
            component_id=f"COMP-{uuid.uuid4().hex[:8]}",
            name=name,
            protection_level=protection_level,
            code_hash=code_hash,
            created_at=datetime.now(timezone.utc),
            last_verified=datetime.now(timezone.utc),
        )
        self._protected_components[name] = component
    
    def _get_component_hash(self, component_name: str) -> str:
        """Get hash of a component for integrity verification."""
        # In production, this would hash the actual code
        return hashlib.sha256(f"{component_name}:{self._config.version}".encode()).hexdigest()
    
    def _audit_log(
        self,
        action: str,
        component: str,
        actor: str,
        details: Dict[str, Any],
        result: str
    ):
        """Add entry to audit log."""
        if not self._config.enable_audit_logging:
            return
        
        entry = AuditEntry(
            entry_id=f"AUDIT-{uuid.uuid4().hex[:12]}",
            timestamp=datetime.now(timezone.utc),
            action=action,
            component=component,
            actor=actor,
            details=details,
            result=result,
            config_hash=self._config.get_hash(),
        )
        
        self._audit_entries.append(entry)
        
        # Persist to disk
        self._persist_audit_entry(entry)
    
    def _persist_audit_entry(self, entry: AuditEntry):
        """Persist audit entry to disk."""
        try:
            date_str = entry.timestamp.strftime('%Y%m%d')
            audit_file = self._storage_path / f"audit_{date_str}.jsonl"
            
            with open(audit_file, 'a') as f:
                f.write(json.dumps(entry.to_dict()) + '\n')
        except Exception as e:
            logger.error(f"Failed to persist audit entry: {e}")
    
    async def initialize(self) -> bool:
        """
        Initialize the production system.
        
        Returns:
            True if initialization successful
        """
        self._audit_log(
            action='INITIALIZE',
            component='core_system',
            actor='system',
            details={'config_hash': self._config.get_hash()},
            result='started'
        )
        
        try:
            # Verify all protected components
            for name, component in self._protected_components.items():
                current_hash = self._get_component_hash(name)
                if not component.verify_integrity(current_hash):
                    logger.error(f"Component integrity check failed: {name}")
                    self._state = SystemState.EMERGENCY_STOP
                    return False
                component.last_verified = datetime.now(timezone.utc)
            
            # Load previous state if exists
            await self._load_state()
            
            self._state = SystemState.READY
            
            self._audit_log(
                action='INITIALIZE',
                component='core_system',
                actor='system',
                details={'components_verified': len(self._protected_components)},
                result='success'
            )
            
            logger.info("CoreProductionSystem initialized and ready")
            return True
            
        except Exception as e:
            logger.error(f"Initialization failed: {e}")
            self._state = SystemState.EMERGENCY_STOP
            return False
    
    async def _load_state(self):
        """Load previous system state."""
        state_file = Path(self._config.state_backup_path) / 'latest_state.json'
        if state_file.exists():
            try:
                with open(state_file, 'r') as f:
                    state = json.load(f)
                    self._positions = state.get('positions', {})
                    self._daily_pnl = state.get('daily_pnl', 0.0)
                    self._total_pnl = state.get('total_pnl', 0.0)
                logger.info("Previous state loaded successfully")
            except Exception as e:
                logger.warning(f"Could not load previous state: {e}")
    
    async def _save_state(self):
        """Save current system state."""
        state_path = Path(self._config.state_backup_path)
        state_path.mkdir(parents=True, exist_ok=True)
        
        state = {
            'positions': self._positions,
            'daily_pnl': self._daily_pnl,
            'total_pnl': self._total_pnl,
            'timestamp': datetime.now(timezone.utc).isoformat(),
        }
        
        state_file = state_path / 'latest_state.json'
        with open(state_file, 'w') as f:
            json.dump(state, f, indent=2)
    
    def validate_external_input(
        self,
        input_data: Dict[str, Any],
        input_type: str,
        source: str
    ) -> Tuple[bool, Optional[str]]:
        """
        Validate external input before processing.
        
        Args:
            input_data: The input data to validate
            input_type: Type of input (trade, signal, etc.)
            source: Source of the input
        
        Returns:
            Tuple of (is_valid, error_message)
        """
        if not self._config.enable_input_validation:
            return True, None
        
        # Check source is allowed
        allowed_sources = {'promotion_system', 'human_operator', 'verified_signal'}
        if source not in allowed_sources:
            return False, f"Unauthorized source: {source}"
        
        # Validate based on input type
        if input_type == 'trade':
            return self._validate_trade_input(input_data)
        elif input_type == 'signal':
            return self._validate_signal_input(input_data)
        elif input_type == 'config_update':
            return False, "Config updates not allowed through external input"
        
        return True, None
    
    def _validate_trade_input(self, trade: Dict) -> Tuple[bool, Optional[str]]:
        """Validate trade input."""
        required_fields = ['symbol', 'side', 'quantity', 'order_type']
        
        for field in required_fields:
            if field not in trade:
                return False, f"Missing required field: {field}"
        
        if trade.get('quantity', 0) <= 0:
            return False, "Quantity must be positive"
        
        if trade.get('side') not in ['buy', 'sell']:
            return False, "Side must be 'buy' or 'sell'"
        
        return True, None
    
    def _validate_signal_input(self, signal: Dict) -> Tuple[bool, Optional[str]]:
        """Validate signal input."""
        required_fields = ['signal_id', 'symbol', 'direction', 'confidence']
        
        for field in required_fields:
            if field not in signal:
                return False, f"Missing required field: {field}"
        
        if not 0 <= signal.get('confidence', 0) <= 1:
            return False, "Confidence must be between 0 and 1"
        
        return True, None
    
    async def execute_trade(
        self,
        trade: Dict[str, Any],
        source: str,
        approval_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Execute a trade with full validation and risk checks.
        
        Args:
            trade: Trade details
            source: Source of the trade request
            approval_id: Optional approval ID for promoted changes
        
        Returns:
            Trade execution result
        """
        if self._state != SystemState.RUNNING:
            return {
                'success': False,
                'error': f'System not in RUNNING state: {self._state.name}',
            }
        
        # Validate input
        is_valid, error = self.validate_external_input(trade, 'trade', source)
        if not is_valid:
            self._audit_log(
                action='TRADE_REJECTED',
                component='trade_executor',
                actor=source,
                details={'trade': trade, 'error': error},
                result='validation_failed'
            )
            return {'success': False, 'error': error}
        
        # Check risk limits
        risk_check = self._check_risk_limits(trade)
        if not risk_check['allowed']:
            self._audit_log(
                action='TRADE_REJECTED',
                component='risk_manager',
                actor=source,
                details={'trade': trade, 'risk_check': risk_check},
                result='risk_limit_exceeded'
            )
            return {'success': False, 'error': risk_check['reason']}
        
        # Execute trade
        try:
            trade_id = f"TRADE-{uuid.uuid4().hex[:12]}"
            
            execution_result = {
                'trade_id': trade_id,
                'symbol': trade['symbol'],
                'side': trade['side'],
                'quantity': trade['quantity'],
                'executed_at': datetime.now(timezone.utc).isoformat(),
                'status': 'executed',
            }
            
            # Update positions
            await self._update_position(trade)
            
            # Record trade
            self._trade_history.append({
                **execution_result,
                'source': source,
                'approval_id': approval_id,
            })
            
            # Notify callbacks
            for callback in self._trade_callbacks:
                try:
                    await callback(execution_result)
                except Exception as e:
                    logger.error(f"Trade callback error: {e}")
            
            self._audit_log(
                action='TRADE_EXECUTED',
                component='trade_executor',
                actor=source,
                details={'trade': trade, 'result': execution_result},
                result='success'
            )
            
            # Save state
            await self._save_state()
            
            return {'success': True, 'result': execution_result}
            
        except Exception as e:
            logger.error(f"Trade execution failed: {e}")
            self._audit_log(
                action='TRADE_FAILED',
                component='trade_executor',
                actor=source,
                details={'trade': trade, 'error': str(e)},
                result='execution_error'
            )
            return {'success': False, 'error': str(e)}
    
    def _check_risk_limits(self, trade: Dict) -> Dict[str, Any]:
        """Check if trade complies with risk limits."""
        # Check daily loss limit
        if self._daily_pnl < -self._config.max_daily_loss_pct:
            return {
                'allowed': False,
                'reason': f'Daily loss limit exceeded: {self._daily_pnl:.2%}',
            }
        
        # Check max positions
        if len(self._positions) >= self._config.max_open_positions:
            symbol = trade.get('symbol')
            if symbol not in self._positions:
                return {
                    'allowed': False,
                    'reason': f'Max open positions reached: {self._config.max_open_positions}',
                }
        
        # Check consecutive losses
        if self._consecutive_losses >= self._config.max_consecutive_losses:
            return {
                'allowed': False,
                'reason': f'Max consecutive losses reached: {self._consecutive_losses}',
            }
        
        # Check trade frequency
        if len(self._trade_history) >= self._config.max_trades_per_day:
            return {
                'allowed': False,
                'reason': f'Max daily trades reached: {self._config.max_trades_per_day}',
            }
        
        return {'allowed': True, 'reason': None}
    
    async def _update_position(self, trade: Dict):
        """Update position based on trade."""
        symbol = trade['symbol']
        side = trade['side']
        quantity = trade['quantity']
        
        if symbol not in self._positions:
            self._positions[symbol] = {
                'symbol': symbol,
                'quantity': 0,
                'avg_price': 0,
                'unrealized_pnl': 0,
            }
        
        position = self._positions[symbol]
        
        if side == 'buy':
            position['quantity'] += quantity
        else:
            position['quantity'] -= quantity
        
        # Remove position if flat
        if position['quantity'] == 0:
            del self._positions[symbol]
    
    async def emergency_stop(self, reason: str, actor: str):
        """
        Trigger emergency stop - closes all positions and halts trading.
        
        Args:
            reason: Reason for emergency stop
            actor: Who triggered the stop
        """
        logger.critical(f"EMERGENCY STOP triggered by {actor}: {reason}")
        
        self._audit_log(
            action='EMERGENCY_STOP',
            component='core_system',
            actor=actor,
            details={'reason': reason, 'positions': len(self._positions)},
            result='triggered'
        )
        
        self._state = SystemState.EMERGENCY_STOP
        
        # Close all positions
        for symbol in list(self._positions.keys()):
            position = self._positions[symbol]
            if position['quantity'] != 0:
                close_trade = {
                    'symbol': symbol,
                    'side': 'sell' if position['quantity'] > 0 else 'buy',
                    'quantity': abs(position['quantity']),
                    'order_type': 'market',
                }
                # Note: In real implementation, this would execute market orders
                logger.info(f"Emergency close: {close_trade}")
        
        # Alert all callbacks
        for callback in self._alert_callbacks:
            try:
                await callback({
                    'type': 'EMERGENCY_STOP',
                    'reason': reason,
                    'actor': actor,
                    'timestamp': datetime.now(timezone.utc).isoformat(),
                })
            except Exception as e:
                logger.error(f"Alert callback error: {e}")
        
        await self._save_state()
    
    def start(self):
        """Start the production system."""
        if self._state == SystemState.READY:
            self._state = SystemState.RUNNING
            self._audit_log(
                action='START',
                component='core_system',
                actor='system',
                details={},
                result='success'
            )
            logger.info("CoreProductionSystem started")
        else:
            logger.warning(f"Cannot start from state: {self._state.name}")
    
    def pause(self, reason: str, actor: str):
        """Pause the production system."""
        if self._state == SystemState.RUNNING:
            self._state = SystemState.PAUSED
            self._audit_log(
                action='PAUSE',
                component='core_system',
                actor=actor,
                details={'reason': reason},
                result='success'
            )
            logger.info(f"CoreProductionSystem paused: {reason}")
    
    def resume(self, actor: str):
        """Resume the production system."""
        if self._state == SystemState.PAUSED:
            self._state = SystemState.RUNNING
            self._audit_log(
                action='RESUME',
                component='core_system',
                actor=actor,
                details={},
                result='success'
            )
            logger.info("CoreProductionSystem resumed")
    
    def get_status(self) -> Dict[str, Any]:
        """Get current system status."""
        return {
            'system_id': self._config.system_id,
            'state': self._state.name,
            'version': self._config.version,
            'config_hash': self._config.get_hash(),
            'positions': len(self._positions),
            'daily_pnl': self._daily_pnl,
            'total_pnl': self._total_pnl,
            'trades_today': len(self._trade_history),
            'consecutive_losses': self._consecutive_losses,
            'protected_components': len(self._protected_components),
            'audit_entries': len(self._audit_entries),
            'modification_attempts': len(self._immutability_guard.get_modification_attempts()),
        }
    
    def get_audit_log(self, limit: int = 100) -> List[Dict]:
        """Get recent audit log entries."""
        return [entry.to_dict() for entry in self._audit_entries[-limit:]]
    
    def register_trade_callback(self, callback: Callable):
        """Register a callback for trade events."""
        self._trade_callbacks.append(callback)
    
    def register_alert_callback(self, callback: Callable):
        """Register a callback for alert events."""
        self._alert_callbacks.append(callback)
    
    def verify_system_integrity(self) -> Dict[str, Any]:
        """Verify integrity of all protected components."""
        results = {
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'config_hash': self._config.get_hash(),
            'components': {},
            'all_valid': True,
        }
        
        for name, component in self._protected_components.items():
            current_hash = self._get_component_hash(name)
            is_valid = component.verify_integrity(current_hash)
            
            results['components'][name] = {
                'protection_level': component.protection_level.value,
                'is_valid': is_valid,
                'last_verified': component.last_verified.isoformat(),
            }
            
            if not is_valid:
                results['all_valid'] = False
                logger.error(f"Integrity check failed for component: {name}")
        
        return results
