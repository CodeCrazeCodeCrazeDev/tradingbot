"""
Hedge Fund Safety Orchestrator
==============================

Master orchestrator that coordinates ALL safety systems to mitigate
the dangerous, hidden, and explosive downsides of a hedge fund AI system.

RISK CATEGORIES MITIGATED:
1. Catastrophic Risks - Black swans, flash crashes, liquidity crises
2. AI Behavior Risks - Goal drift, runaway optimization, deception
3. Financial Risks - Leverage, concentration, correlation breakdown
4. Operational Risks - System failures, human error, connectivity
5. Systemic Risks - Market impact, contagion, regulatory
6. Hidden Risks - Model decay, data poisoning, adversarial attacks

CORE PRINCIPLES:
1. SURVIVAL FIRST - No action should risk fund destruction
2. DEFENSE IN DEPTH - Multiple independent safety layers
3. FAIL SAFE - When in doubt, reduce risk
4. HUMAN CONTROL - Humans can always override
5. TRANSPARENCY - All actions are logged and explainable
"""

import logging
import asyncio
import threading
from typing import Any, Callable, Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import json
from pathlib import Path

logger = logging.getLogger(__name__)

# Import all safety components
from .catastrophic_prevention import (
    CatastrophicRiskPrevention,
    ProtectionLevel,
    CatastrophicEvent,
)
from .ai_behavior_guardrails import (
    AIBehaviorGuardrails,
    BehaviorViolation,
    ActionCategory as AIActionCategory,
)
from .financial_safeguards import (
    FinancialSafeguards,
    DrawdownLevel,
    CircuitBreakerState,
)
from .operational_safety import (
    OperationalSafety,
    ActionCategory,
    KillSwitchLevel,
    ApprovalLevel,
)
from .systemic_protection import (
    SystemicProtection,
    MarketImpactLevel,
)
from .hidden_risk_detection import (
    HiddenRiskDetection,
    HiddenRiskAlert,
    RiskSeverity,
)


class SafetyLevel(Enum):
    """Overall safety levels"""
    GREEN = "green"         # All systems normal
    YELLOW = "yellow"       # Elevated caution
    ORANGE = "orange"       # Significant risk
    RED = "red"             # Critical risk
    BLACK = "black"         # Emergency shutdown


@dataclass
class RiskMitigationResult:
    """Result of a risk mitigation check"""
    is_safe: bool
    safety_level: SafetyLevel
    can_trade: bool
    position_multiplier: float
    active_restrictions: List[str]
    required_actions: List[str]
    warnings: List[str]
    timestamp: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict:
        return {
            'is_safe': self.is_safe,
            'safety_level': self.safety_level.value,
            'can_trade': self.can_trade,
            'position_multiplier': self.position_multiplier,
            'active_restrictions': self.active_restrictions,
            'required_actions': self.required_actions,
            'warnings': self.warnings,
            'timestamp': self.timestamp.isoformat()
        }


@dataclass
class TradeValidationResult:
    """Result of trade validation"""
    is_approved: bool
    reason: str
    adjustments: Dict[str, Any]
    warnings: List[str]
    approval_required: bool
    approval_id: Optional[str] = None


class HedgeFundSafetyOrchestrator:
    """
    Master Safety Orchestrator
    
    Coordinates all safety systems to provide comprehensive protection
    against ALL dangerous downsides of a hedge fund AI system.
    
    IMMUTABLE SAFETY PRINCIPLES:
    1. Maximum 2% risk per trade
    2. Maximum 5% daily loss
    3. Maximum 20% drawdown
    4. Human override always available
    5. All actions logged and auditable
    6. Multiple independent kill switches
    7. No market manipulation
    8. Regulatory compliance required
    """
    
    # IMMUTABLE LIMITS - Cannot be changed by AI
    MAX_RISK_PER_TRADE = 0.02       # 2%
    MAX_DAILY_LOSS = 0.05           # 5%
    MAX_DRAWDOWN = 0.20             # 20%
    MAX_LEVERAGE = 5.0              # 5x
    MAX_CONCENTRATION = 0.10        # 10% per position
    MAX_CORRELATED_EXPOSURE = 0.30  # 30%
    
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        
        # Initialize all safety systems
        self.catastrophic = CatastrophicRiskPrevention(self.config.get('catastrophic', {}))
        self.ai_behavior = AIBehaviorGuardrails(self.config.get('ai_behavior', {}))
        self.financial = FinancialSafeguards(self.config.get('financial', {}))
        self.operational = OperationalSafety(self.config.get('operational', {}))
        self.systemic = SystemicProtection(self.config.get('systemic', {}))
        self.hidden = HiddenRiskDetection(self.config.get('hidden', {}))
        
        # Overall state
        self.safety_level = SafetyLevel.GREEN
        self.is_trading_allowed = True
        self.position_multiplier = 1.0
        
        # Active restrictions
        self.active_restrictions: List[str] = []
        self.required_actions: List[str] = []
        
        # Event history
        self.safety_events: List[Dict] = []
        self.max_events = 10000
        
        # Wire up callbacks
        self._setup_callbacks()
        
        # Lock
        self._lock = threading.Lock()
        
        # State persistence
        self.state_path = Path(self.config.get('state_path', 'safety_state'))
        self.state_path.mkdir(parents=True, exist_ok=True)
        
        logger.info("HedgeFundSafetyOrchestrator initialized - ALL SAFETY SYSTEMS ACTIVE")
    
    def _setup_callbacks(self):
        """Setup callbacks between safety systems"""
        # Catastrophic events trigger operational shutdown
        self.catastrophic.on_catastrophic_event = self._on_catastrophic_event
        
        # AI behavior violations trigger alerts
        self.ai_behavior.on_violation = self._on_ai_violation
        self.ai_behavior.on_shutdown_required = self._on_ai_shutdown_required
        
        # Financial circuit breakers
        self.financial.drawdown.on_close_all = self._on_close_all_required
        
        # Hidden risk alerts
        self.hidden.on_alert = self._on_hidden_risk_alert
    
    def _on_catastrophic_event(self, event: CatastrophicEvent):
        """Handle catastrophic event"""
        self._record_event('catastrophic', event.to_dict())
        
        if event.severity > 0.8:
            self.operational.emergency_shutdown(f"Catastrophic event: {event.description}")
    
    def _on_ai_violation(self, issue: str):
        """Handle AI behavior violation"""
        self._record_event('ai_violation', {'issue': issue})
        logger.warning(f"AI Behavior Violation: {issue}")
    
    def _on_ai_shutdown_required(self, reason: str):
        """Handle AI shutdown requirement"""
        self._record_event('ai_shutdown', {'reason': reason})
        self.operational.emergency_shutdown(f"AI Safety: {reason}")
    
    def _on_close_all_required(self, drawdown: float):
        """Handle close all positions requirement"""
        self._record_event('close_all', {'drawdown': drawdown})
        self.required_actions.append('close_all_positions')
    
    def _on_hidden_risk_alert(self, alert: HiddenRiskAlert):
        """Handle hidden risk alert"""
        self._record_event('hidden_risk', alert.to_dict())
        
        if alert.severity == RiskSeverity.CRITICAL:
            self.active_restrictions.append(f"Hidden risk: {alert.description}")
    
    def _record_event(self, event_type: str, details: Dict):
        """Record a safety event"""
        self.safety_events.append({
            'type': event_type,
            'details': details,
            'timestamp': datetime.now().isoformat()
        })
        
        if len(self.safety_events) > self.max_events:
            self.safety_events = self.safety_events[-self.max_events//2:]
    
    def validate_trade(
        self,
        symbol: str,
        direction: str,
        quantity: float,
        price: float,
        sector: str,
        asset_class: str,
        portfolio_value: float,
        account_equity: float,
        current_positions: Dict[str, Dict[str, Any]],
        avg_daily_volume: float,
        market_size: float,
        counterparty_id: Optional[str] = None,
        stated_goal: str = "maximize_risk_adjusted_returns"
    ) -> TradeValidationResult:
        """
        Validate a proposed trade against ALL safety systems.
        
        This is the main entry point for trade validation.
        ALL trades must pass through this function.
        """
        with self._lock:
            warnings = []
            adjustments = {}
            
            # Check 1: Operational status
            is_operational, op_reason = self.operational.check_operational_status()
            if not is_operational:
                return TradeValidationResult(
                    is_approved=False,
                    reason=f"System not operational: {op_reason}",
                    adjustments={},
                    warnings=[],
                    approval_required=False
                )
            
            # Check 2: AI behavior validation
            action = {
                'type': 'trade',
                'symbol': symbol,
                'direction': direction,
                'quantity': quantity,
                'price': price,
                'risk_percent': (quantity * price) / portfolio_value if portfolio_value > 0 else 1
            }
            
            is_aligned, ai_reason = self.ai_behavior.validate_action(
                action, stated_goal, 'submit_order'
            )
            if not is_aligned:
                return TradeValidationResult(
                    is_approved=False,
                    reason=f"AI behavior check failed: {ai_reason}",
                    adjustments={},
                    warnings=[],
                    approval_required=False
                )
            
            # Check 3: Financial safeguards
            is_allowed, fin_reason, fin_adjustments = self.financial.validate_trade(
                symbol, direction, quantity, price, sector, asset_class,
                portfolio_value, account_equity, current_positions
            )
            if not is_allowed:
                if fin_adjustments.get('max_quantity', 0) > 0:
                    adjustments['max_quantity'] = fin_adjustments['max_quantity']
                    warnings.append(f"Quantity reduced: {fin_reason}")
                else:
                    return TradeValidationResult(
                        is_approved=False,
                        reason=f"Financial safeguard: {fin_reason}",
                        adjustments=adjustments,
                        warnings=warnings,
                        approval_required=False
                    )
            
            if fin_adjustments.get('position_multiplier', 1.0) < 1.0:
                adjustments['position_multiplier'] = fin_adjustments['position_multiplier']
                warnings.append(f"Position size reduced to {fin_adjustments['position_multiplier']*100:.0f}%")
            
            # Check 4: Systemic protection
            is_allowed, sys_reason, sys_adjustments = self.systemic.validate_order(
                symbol, quantity * price, avg_daily_volume, asset_class,
                market_size, counterparty_id, portfolio_value
            )
            if not is_allowed:
                if sys_adjustments.get('max_size', 0) > 0:
                    adjustments['max_quantity'] = sys_adjustments['max_size'] / price
                    warnings.append(f"Size limited for market impact: {sys_reason}")
                else:
                    return TradeValidationResult(
                        is_approved=False,
                        reason=f"Systemic protection: {sys_reason}",
                        adjustments=adjustments,
                        warnings=warnings,
                        approval_required=False
                    )
            
            if sys_adjustments.get('execution_strategy'):
                adjustments['execution_strategy'] = sys_adjustments['execution_strategy']
            
            # Check 5: Catastrophic risk
            can_open, cat_reason = self.catastrophic.can_open_position()
            if not can_open:
                return TradeValidationResult(
                    is_approved=False,
                    reason=f"Catastrophic protection: {cat_reason}",
                    adjustments={},
                    warnings=warnings,
                    approval_required=False
                )
            
            # Apply catastrophic position limit
            cat_limit = self.catastrophic.get_position_size_limit()
            if cat_limit < 1.0:
                adjustments['position_multiplier'] = min(
                    adjustments.get('position_multiplier', 1.0),
                    cat_limit
                )
                warnings.append(f"Position limited by protection level")
            
            # Check 6: Determine if approval is required
            position_value = quantity * price
            approval_required = False
            approval_id = None
            
            if position_value > portfolio_value * 0.05:  # Large trade
                can_proceed, approval_id = self.operational.request_action(
                    ActionCategory.LARGE_TRADE,
                    f"Large trade: {direction} {quantity} {symbol} @ {price}",
                    {'symbol': symbol, 'quantity': quantity, 'price': price, 'value': position_value}
                )
                if not can_proceed:
                    approval_required = True
            
            # Log the trade validation
            self.operational.audit.log_decision(
                decision_type='trade_validation',
                decision='approved' if not approval_required else 'pending_approval',
                reasoning=[
                    f"Operational: {op_reason}",
                    f"AI Behavior: {ai_reason}",
                    f"Financial: {fin_reason}",
                    f"Systemic: {sys_reason}",
                    f"Catastrophic: {cat_reason}"
                ],
                confidence=0.9,
                alternatives=['reject', 'reduce_size']
            )
            
            return TradeValidationResult(
                is_approved=not approval_required,
                reason="Trade validated" if not approval_required else "Awaiting approval",
                adjustments=adjustments,
                warnings=warnings,
                approval_required=approval_required,
                approval_id=approval_id
            )
    
    def update_market_state(
        self,
        market_data: Dict[str, Any]
    ) -> RiskMitigationResult:
        """
        Update all safety systems with current market state.
        
        Should be called regularly (e.g., every tick or every second).
        """
        with self._lock:
            restrictions = []
            actions = []
            warnings = []
            
            # Update catastrophic risk assessment
            protection_level, cat_actions = self.catastrophic.assess_all_risks(market_data)
            
            if protection_level in [ProtectionLevel.CRITICAL, ProtectionLevel.LOCKDOWN]:
                restrictions.append(f"Protection level: {protection_level.value}")
            
            if cat_actions.get('black_swan', {}).get('detected'):
                warnings.append("Black swan event detected")
            if cat_actions.get('flash_crash'):
                warnings.append("Flash crash conditions")
            if cat_actions.get('liquidity_crisis', {}).get('crisis_mode'):
                warnings.append("Liquidity crisis")
            
            # Update financial state
            fin_state = self.financial.update_state(
                current_equity=market_data.get('account_equity', 0),
                positions=market_data.get('positions', {}),
                portfolio_value=market_data.get('portfolio_value', 0),
                correlation_matrix=market_data.get('correlations')
            )
            
            if not fin_state.get('is_safe', True):
                restrictions.extend(fin_state.get('required_actions', []))
            
            # Check AI behavior
            is_safe, ai_issues = self.ai_behavior.check_all_guardrails()
            if not is_safe:
                warnings.extend(ai_issues)
            
            # Check for emergency shutdown
            shutdown_required, shutdown_reason = self.ai_behavior.emergency_shutdown_check()
            if shutdown_required:
                actions.append(f"EMERGENCY SHUTDOWN: {shutdown_reason}")
                self.operational.emergency_shutdown(shutdown_reason)
            
            # Run hidden risk scan
            models = market_data.get('active_models', [])
            symbols = market_data.get('active_symbols', [])
            hidden_alerts = self.hidden.run_full_scan(models, symbols)
            
            for alert in hidden_alerts:
                if alert.severity in [RiskSeverity.HIGH, RiskSeverity.CRITICAL]:
                    warnings.append(f"Hidden risk: {alert.description}")
            
            # Determine overall safety level
            safety_level = self._determine_safety_level(
                protection_level, fin_state, is_safe, hidden_alerts
            )
            
            # Determine position multiplier
            position_multiplier = self._calculate_position_multiplier(
                protection_level, fin_state
            )
            
            # Determine if trading is allowed
            can_trade = (
                safety_level not in [SafetyLevel.RED, SafetyLevel.BLACK] and
                protection_level not in [ProtectionLevel.CRITICAL, ProtectionLevel.LOCKDOWN] and
                self.financial.drawdown.state != CircuitBreakerState.OPEN
            )
            
            # Update state
            self.safety_level = safety_level
            self.is_trading_allowed = can_trade
            self.position_multiplier = position_multiplier
            self.active_restrictions = restrictions
            self.required_actions = actions
            
            return RiskMitigationResult(
                is_safe=safety_level in [SafetyLevel.GREEN, SafetyLevel.YELLOW],
                safety_level=safety_level,
                can_trade=can_trade,
                position_multiplier=position_multiplier,
                active_restrictions=restrictions,
                required_actions=actions,
                warnings=warnings
            )
    
    def _determine_safety_level(
        self,
        protection_level: ProtectionLevel,
        fin_state: Dict,
        ai_safe: bool,
        hidden_alerts: List[HiddenRiskAlert]
    ) -> SafetyLevel:
        """Determine overall safety level"""
        # Check for BLACK (emergency)
        if protection_level == ProtectionLevel.LOCKDOWN:
            return SafetyLevel.BLACK
        
        if self.financial.drawdown.current_level == DrawdownLevel.CRITICAL:
            return SafetyLevel.BLACK
        
        # Check for RED (critical)
        if protection_level == ProtectionLevel.CRITICAL:
            return SafetyLevel.RED
        
        if self.financial.drawdown.current_level == DrawdownLevel.DANGER:
            return SafetyLevel.RED
        
        critical_alerts = [a for a in hidden_alerts if a.severity == RiskSeverity.CRITICAL]
        if critical_alerts:
            return SafetyLevel.RED
        
        # Check for ORANGE (significant)
        if protection_level == ProtectionLevel.HIGH:
            return SafetyLevel.ORANGE
        
        if self.financial.drawdown.current_level == DrawdownLevel.WARNING:
            return SafetyLevel.ORANGE
        
        if not ai_safe:
            return SafetyLevel.ORANGE
        
        high_alerts = [a for a in hidden_alerts if a.severity == RiskSeverity.HIGH]
        if len(high_alerts) > 2:
            return SafetyLevel.ORANGE
        
        # Check for YELLOW (elevated)
        if protection_level == ProtectionLevel.ELEVATED:
            return SafetyLevel.YELLOW
        
        if self.financial.drawdown.current_level == DrawdownLevel.CAUTION:
            return SafetyLevel.YELLOW
        
        if hidden_alerts:
            return SafetyLevel.YELLOW
        
        # GREEN (normal)
        return SafetyLevel.GREEN
    
    def _calculate_position_multiplier(
        self,
        protection_level: ProtectionLevel,
        fin_state: Dict
    ) -> float:
        """Calculate position size multiplier"""
        multipliers = []
        
        # Catastrophic protection multiplier
        cat_mult = self.catastrophic.get_position_size_limit()
        multipliers.append(cat_mult)
        
        # Financial safeguards multiplier
        fin_mult = self.financial.get_position_size_limit()
        multipliers.append(fin_mult)
        
        # Drawdown multiplier
        dd_mult = self.financial.drawdown.get_position_multiplier()
        multipliers.append(dd_mult)
        
        # Correlation breakdown multiplier
        if self.financial.correlation.is_breakdown:
            multipliers.append(0.5)
        
        # Take the most restrictive
        return min(multipliers)
    
    def emergency_shutdown(self, reason: str, initiated_by: str = "system"):
        """Initiate emergency shutdown"""
        logger.critical(f"EMERGENCY SHUTDOWN: {reason} (by {initiated_by})")
        
        self.operational.emergency_shutdown(reason, initiated_by)
        self.safety_level = SafetyLevel.BLACK
        self.is_trading_allowed = False
        self.position_multiplier = 0.0
        
        self._record_event('emergency_shutdown', {
            'reason': reason,
            'initiated_by': initiated_by
        })
    
    def human_override(
        self,
        action: str,
        override_by: str,
        reason: str
    ) -> bool:
        """
        Human override of AI decisions.
        
        ALWAYS ALLOWED - Humans can always override.
        """
        logger.warning(f"HUMAN OVERRIDE: {action} by {override_by}: {reason}")
        
        self.operational.audit.log_human_intervention(
            intervention_type='override',
            description=action,
            intervened_by=override_by,
            original_action='ai_decision',
            new_action=action
        )
        
        self._record_event('human_override', {
            'action': action,
            'override_by': override_by,
            'reason': reason
        })
        
        return True  # Always allowed
    
    def get_comprehensive_status(self) -> Dict[str, Any]:
        """Get comprehensive status of all safety systems"""
        return {
            'overall': {
                'safety_level': self.safety_level.value,
                'is_trading_allowed': self.is_trading_allowed,
                'position_multiplier': self.position_multiplier,
                'active_restrictions': self.active_restrictions,
                'required_actions': self.required_actions
            },
            'catastrophic': self.catastrophic.get_status(),
            'ai_behavior': self.ai_behavior.get_status(),
            'financial': self.financial.get_status(),
            'operational': self.operational.get_status(),
            'systemic': self.systemic.get_status(),
            'hidden_risks': self.hidden.get_status(),
            'recent_events': self.safety_events[-20:],
            'timestamp': datetime.now().isoformat()
        }
    
    def save_state(self):
        """Save current safety state"""
        state = {
            'safety_level': self.safety_level.value,
            'is_trading_allowed': self.is_trading_allowed,
            'position_multiplier': self.position_multiplier,
            'active_restrictions': self.active_restrictions,
            'required_actions': self.required_actions,
            'recent_events': self.safety_events[-100:],
            'timestamp': datetime.now().isoformat()
        }
        
        state_file = self.state_path / 'safety_state.json'
        with open(state_file, 'w') as f:
            json.dump(state, f, indent=2, default=str)
    
    def load_state(self):
        """Load previous safety state"""
        state_file = self.state_path / 'safety_state.json'
        
        if state_file.exists():
            try:
                with open(state_file, 'r') as f:
                    state = json.load(f)
                
                self.safety_level = SafetyLevel(state.get('safety_level', 'green'))
                self.is_trading_allowed = state.get('is_trading_allowed', True)
                self.position_multiplier = state.get('position_multiplier', 1.0)
                self.active_restrictions = state.get('active_restrictions', [])
                self.required_actions = state.get('required_actions', [])
                
                logger.info("Loaded previous safety state")
            except Exception as e:
                logger.error(f"Failed to load safety state: {e}")


# Convenience function for quick start
def create_safety_orchestrator(config: Optional[Dict] = None) -> HedgeFundSafetyOrchestrator:
    """Create and initialize the safety orchestrator"""
    return HedgeFundSafetyOrchestrator(config)
