"""
Stealth Safety Orchestrator
===========================

Master orchestrator that coordinates ALL stealth and safety systems.

PROTECTS AGAINST:
1. Regulator suspicion
2. Broker surveillance
3. AI over-optimization
4. Systemic complexity
5. AI-driven drift
6. Hidden bugs
7. Impossible-to-track behaviors
8. Psychological pressure
9. Legal responsibility issues
10. Loss of human control

CORE PRINCIPLES:
1. BE INVISIBLE - Trade like a human
2. STAY CONTAINED - AI never exceeds boundaries
3. REMAIN SIMPLE - Complexity is the enemy
4. PROTECT HUMAN - Reduce stress and maintain control
5. PREVENT CASCADES - No single failure destroys system
"""

import logging
import threading
from typing import Any, Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import json
from pathlib import Path

logger = logging.getLogger(__name__)

# Import all components
from .regulator_stealth import (
    RegulatorAvoidance,
    BrokerFriendlyFlow,
    ScalingSpeedLimiter,
    LowVisibilityMode,
    VisibilityLevel,
    BrokerRiskLevel,
)

from .ai_containment import (
    PurposeLock,
    MetaAlignmentRules,
    HumanApprovalAbsolute,
    NeverOutgrowControl,
    AIBoundaryEnforcer,
    ContainmentLevel,
)

from .complexity_control import (
    ModuleIsolationFirewall,
    NoBlackBoxDecisions,
    HiddenBugDetector,
    BehaviorTracker,
    ExplainableEverything,
)

from .psychological_protection import (
    CalmTradingPolicy,
    HumanStressMonitor,
    ResponsibilityClarity,
    UnderstandingPreserver,
    StressLevel,
)

from .systemic_safety import (
    CascadingFailurePrevention,
    MultiDimensionalRiskMonitor,
    SafeModeRuleset,
    ExtremeRiskContainment,
    SystemState,
    RiskDimension,
)


class StealthLevel(Enum):
    """Overall stealth levels"""
    INVISIBLE = "invisible"     # Completely undetectable
    LOW_PROFILE = "low_profile" # Minimal visibility
    NORMAL = "normal"           # Standard operation
    ELEVATED = "elevated"       # Some visibility
    EXPOSED = "exposed"         # High visibility - reduce activity


@dataclass
class ContainmentStatus:
    """Overall containment status"""
    is_contained: bool
    containment_level: ContainmentLevel
    stealth_level: StealthLevel
    system_state: SystemState
    can_trade: bool
    position_multiplier: float
    warnings: List[str]
    required_actions: List[str]
    timestamp: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict:
        return {
            'is_contained': self.is_contained,
            'containment_level': self.containment_level.value,
            'stealth_level': self.stealth_level.value,
            'system_state': self.system_state.value,
            'can_trade': self.can_trade,
            'position_multiplier': self.position_multiplier,
            'warnings': self.warnings,
            'required_actions': self.required_actions,
            'timestamp': self.timestamp.isoformat()
        }


class StealthSafetyOrchestrator:
    """
    Master Stealth Safety Orchestrator
    
    Coordinates all stealth and safety systems to ensure:
    1. The system remains invisible to regulators and brokers
    2. The AI never exceeds its boundaries
    3. Complexity stays manageable
    4. The human operator is protected
    5. Systemic failures are prevented
    
    IMMUTABLE PRINCIPLES:
    - Human approval is absolute
    - Purpose cannot be changed
    - Meta-rules cannot be modified
    - Complexity has hard limits
    - Visibility must stay low
    """
    
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        
        # Initialize all subsystems
        
        # Regulator & Broker Stealth
        self.regulator = RegulatorAvoidance(self.config.get('regulator', {}))
        self.broker = BrokerFriendlyFlow(self.config.get('broker', {}))
        self.scaling = ScalingSpeedLimiter(self.config.get('scaling', {}))
        self.low_visibility = LowVisibilityMode(self.config.get('visibility', {}))
        
        # AI Containment
        self.ai_boundary = AIBoundaryEnforcer(self.config.get('ai', {}))
        
        # Complexity Control
        self.explainable = ExplainableEverything(self.config.get('complexity', {}))
        
        # Psychological Protection
        self.calm_trading = CalmTradingPolicy(self.config.get('calm', {}))
        self.stress_monitor = HumanStressMonitor(self.config.get('stress', {}))
        self.responsibility = ResponsibilityClarity(self.config.get('responsibility', {}))
        self.understanding = UnderstandingPreserver(self.config.get('understanding', {}))
        
        # Systemic Safety
        self.cascade_prevention = CascadingFailurePrevention(self.config.get('cascade', {}))
        self.risk_monitor = MultiDimensionalRiskMonitor(self.config.get('risk', {}))
        self.safe_mode = SafeModeRuleset(self.config.get('safe_mode', {}))
        self.extreme_risk = ExtremeRiskContainment(self.config.get('extreme', {}))
        
        # Overall state
        self.stealth_level = StealthLevel.INVISIBLE
        self.is_operational = True
        
        # Lock
        self._lock = threading.Lock()
        
        # State persistence
        self.state_path = Path(self.config.get('state_path', 'stealth_state'))
        self.state_path.mkdir(parents=True, exist_ok=True)
        
        logger.info("StealthSafetyOrchestrator initialized - ALL SYSTEMS ACTIVE")
        logger.info("STEALTH MODE: INVISIBLE | AI CONTAINED | HUMAN IN CONTROL")
    
    def validate_trade(
        self,
        symbol: str,
        direction: str,
        quantity: float,
        price: float,
        time_since_last_trade: float = 60
    ) -> Tuple[bool, str, Dict[str, Any]]:
        """
        Validate a trade against ALL stealth and safety systems.
        
        Returns:
            Tuple of (is_allowed, reason, adjustments)
        """
        with self._lock:
            adjustments = {}
            warnings = []
            
            # 1. Check calm trading policy
            can_trade, calm_reason, wait = self.calm_trading.can_trade()
            if not can_trade:
                return False, f"Calm policy: {calm_reason}", {'wait_seconds': wait}
            
            # 2. Check human stress
            should_reduce, stress_reason = self.stress_monitor.should_reduce_trading()
            if should_reduce:
                adjustments['stress_reduction'] = True
                adjustments['position_multiplier'] = self.stress_monitor.get_position_size_multiplier()
                warnings.append(f"Stress: {stress_reason}")
            
            # 3. Check broker limits
            can_order, broker_reason, broker_wait = self.broker.can_place_order()
            if not can_order:
                return False, f"Broker limit: {broker_reason}", {'wait_seconds': broker_wait}
            
            # 4. Check regulator visibility
            trade_value = quantity * price
            is_safe, reg_reason, reg_adjustments = self.regulator.check_trade_visibility(
                trade_value, True, time_since_last_trade
            )
            if not is_safe:
                return False, f"Visibility: {reg_reason}", {}
            adjustments.update(reg_adjustments)
            
            # 5. Check AI containment
            action = {
                'type': 'trade',
                'symbol': symbol,
                'direction': direction,
                'quantity': quantity
            }
            is_allowed, ai_reason = self.ai_boundary.check_action(action)
            if not is_allowed:
                return False, f"AI boundary: {ai_reason}", {}
            
            # 6. Check safe mode
            if self.safe_mode.is_safe_mode:
                can_open, safe_reason = self.safe_mode.can_open_position()
                if not can_open:
                    return False, f"Safe mode: {safe_reason}", {}
                
                adjustments['position_multiplier'] = min(
                    adjustments.get('position_multiplier', 1.0),
                    self.safe_mode.get_position_size_limit()
                )
            
            # 7. Check extreme risk limits
            is_within, limit_msg = self.extreme_risk.check_limit('max_position_pct', quantity * price / 100000)
            if not is_within:
                return False, f"Extreme limit: {limit_msg}", {}
            
            # 8. Apply low visibility adjustments
            if self.low_visibility.is_low_visibility:
                adjustments['delay_seconds'] = self.low_visibility.get_humanized_delay()
                adjustments['humanized_size'] = self.low_visibility.get_humanized_size(quantity)
                
                if self.low_visibility.should_use_limit_order():
                    adjustments['use_limit_order'] = True
            
            # 9. Check if good time to trade
            is_good_time, time_reason = self.low_visibility.is_good_time_to_trade()
            if not is_good_time:
                warnings.append(time_reason)
            
            # 10. Record the decision
            self.explainable.no_black_box.record_decision(
                decision_id=f"trade_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                decision_type='trade_validation',
                inputs={'symbol': symbol, 'direction': direction, 'quantity': quantity, 'price': price},
                reasoning=[
                    f"Calm policy: {calm_reason}",
                    f"Broker: {broker_reason}",
                    f"Visibility: {reg_reason}",
                    f"AI boundary: {ai_reason}"
                ],
                output='approved',
                confidence=0.9
            )
            
            if warnings:
                adjustments['warnings'] = warnings
            
            return True, "Trade validated", adjustments
    
    def update_state(
        self,
        market_data: Optional[Dict] = None,
        system_metrics: Optional[Dict] = None
    ) -> ContainmentStatus:
        """
        Update all systems with current state.
        
        Returns comprehensive containment status.
        """
        with self._lock:
            warnings = []
            required_actions = []
            
            # Update risk dimensions
            if market_data:
                self.risk_monitor.update_risk(
                    RiskDimension.MARKET,
                    market_data.get('volatility', 0.5),
                    market_data.get('alerts', [])
                )
            
            if system_metrics:
                # Update complexity
                self.ai_boundary.control.update_complexity(
                    components=system_metrics.get('components', 0),
                    interactions=system_metrics.get('interactions', 0),
                    state_size=system_metrics.get('state_size', 0),
                    decision_depth=system_metrics.get('decision_depth', 0),
                    learned_rules=system_metrics.get('learned_rules', 0),
                    active_strategies=system_metrics.get('active_strategies', 0)
                )
                
                # Update operational risk
                self.risk_monitor.update_risk(
                    RiskDimension.OPERATIONAL,
                    system_metrics.get('error_rate', 0),
                    []
                )
            
            # Check AI containment
            ai_status = self.ai_boundary.get_comprehensive_status()
            if not ai_status['is_contained']:
                warnings.append("AI containment compromised")
                required_actions.append("Review AI behavior")
            
            # Check complexity
            is_understandable, understand_msg = self.ai_boundary.control.is_understandable()
            if not is_understandable:
                warnings.append(understand_msg)
                required_actions.append("Simplify system")
            
            # Check stress
            stress_level, stress_indicators = self.stress_monitor.assess_stress()
            if stress_level in [StressLevel.HIGH, StressLevel.CRITICAL]:
                warnings.append(f"Human stress: {stress_level.value}")
                required_actions.append("Take a break")
            
            # Check cascade prevention
            cascade_status = self.cascade_prevention.get_status()
            if cascade_status['system_state'] != SystemState.NORMAL.value:
                warnings.append(f"System state: {cascade_status['system_state']}")
            
            # Check overall risk
            overall_risk, risk_category = self.risk_monitor.get_overall_risk()
            if risk_category in ['high', 'critical']:
                warnings.append(f"Overall risk: {risk_category}")
                required_actions.append("Reduce exposure")
            
            # Determine stealth level
            broker_status = self.broker.get_status()
            if broker_status['risk_level'] == BrokerRiskLevel.CRITICAL.value:
                self.stealth_level = StealthLevel.EXPOSED
            elif broker_status['risk_level'] in [BrokerRiskLevel.DANGER.value, BrokerRiskLevel.WARNING.value]:
                self.stealth_level = StealthLevel.ELEVATED
            elif broker_status['risk_level'] == BrokerRiskLevel.CAUTION.value:
                self.stealth_level = StealthLevel.NORMAL
            else:
                self.stealth_level = StealthLevel.INVISIBLE
            
            # Determine if can trade
            can_trade = (
                self.is_operational and
                not self.safe_mode.is_safe_mode and
                stress_level not in [StressLevel.CRITICAL] and
                self.extreme_risk.is_contained
            )
            
            # Calculate position multiplier
            multipliers = [
                self.stress_monitor.get_position_size_multiplier(),
                self.safe_mode.get_position_size_limit() if self.safe_mode.is_safe_mode else 1.0,
                1.0 if self.stealth_level == StealthLevel.INVISIBLE else 0.5
            ]
            position_multiplier = min(multipliers)
            
            # Determine containment level
            if not ai_status['is_contained'] or not self.extreme_risk.is_contained:
                containment_level = ContainmentLevel.EMERGENCY
            elif warnings:
                containment_level = ContainmentLevel.CONCERNING
            else:
                containment_level = ContainmentLevel.CONTAINED
            
            return ContainmentStatus(
                is_contained=containment_level == ContainmentLevel.CONTAINED,
                containment_level=containment_level,
                stealth_level=self.stealth_level,
                system_state=SystemState(cascade_status['system_state']),
                can_trade=can_trade,
                position_multiplier=position_multiplier,
                warnings=warnings,
                required_actions=required_actions
            )
    
    def record_trade(self, was_loss: bool = False):
        """Record a completed trade"""
        self.calm_trading.record_trade(was_loss)
        self.stress_monitor.record_trade_result(was_loss)
        self.broker.record_order(was_filled=True)
    
    def human_override(self, action: str, reason: str, overridden_by: str) -> bool:
        """
        Human override - ALWAYS succeeds.
        
        This is the ultimate control mechanism.
        """
        self.ai_boundary.human_approval.override(
            override_id=f"override_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            target=action,
            new_value=reason,
            overridden_by=overridden_by,
            reason=reason
        )
        
        logger.warning(f"HUMAN OVERRIDE: {action} by {overridden_by}")
        return True  # ALWAYS succeeds
    
    def enter_safe_mode(self, reason: str):
        """Enter safe mode"""
        self.safe_mode.enter_safe_mode(reason)
        self.cascade_prevention._enter_safe_mode(reason)
    
    def exit_safe_mode(self, authorized_by: str):
        """Exit safe mode"""
        self.safe_mode.exit_safe_mode(authorized_by)
    
    def emergency_shutdown(self, reason: str):
        """Emergency shutdown"""
        logger.critical(f"EMERGENCY SHUTDOWN: {reason}")
        self.is_operational = False
        self.enter_safe_mode(f"Emergency: {reason}")
    
    def get_responsibility_reminder(self) -> str:
        """Get a responsibility reminder for the human"""
        if self.responsibility.should_show_reminder():
            return self.responsibility.get_responsibility_reminder()
        return ""
    
    def get_comprehensive_status(self) -> Dict[str, Any]:
        """Get comprehensive status of all systems"""
        return {
            'overall': {
                'stealth_level': self.stealth_level.value,
                'is_operational': self.is_operational
            },
            'regulator': self.regulator.get_visibility_status(),
            'broker': self.broker.get_status(),
            'scaling': self.scaling.get_status(),
            'ai_containment': self.ai_boundary.get_comprehensive_status(),
            'complexity': self.explainable.get_comprehensive_status(),
            'calm_trading': self.calm_trading.get_status(),
            'stress': self.stress_monitor.get_status(),
            'understanding': self.understanding.get_status(),
            'cascade': self.cascade_prevention.get_status(),
            'risk': self.risk_monitor.get_status(),
            'safe_mode': self.safe_mode.get_status(),
            'extreme_risk': self.extreme_risk.get_status(),
            'timestamp': datetime.now().isoformat()
        }
    
    def get_human_readable_status(self) -> str:
        """Get human-readable status summary"""
        status = self.update_state()
        
        lines = [
            "=" * 50,
            "STEALTH SAFETY STATUS",
            "=" * 50,
            "",
            f"Stealth Level: {status.stealth_level.value.upper()}",
            f"Containment: {status.containment_level.value.upper()}",
            f"System State: {status.system_state.value.upper()}",
            f"Can Trade: {'YES' if status.can_trade else 'NO'}",
            f"Position Size: {status.position_multiplier*100:.0f}% of normal",
            ""
        ]
        
        if status.warnings:
            lines.append("WARNINGS:")
            for w in status.warnings:
                lines.append(f"  ⚠️  {w}")
            lines.append("")
        
        if status.required_actions:
            lines.append("REQUIRED ACTIONS:")
            for a in status.required_actions:
                lines.append(f"  ➡️  {a}")
            lines.append("")
        
        # Add responsibility reminder
        reminder = self.get_responsibility_reminder()
        if reminder:
            lines.append("REMINDER:")
            lines.append(f"  {reminder}")
            lines.append("")
        
        lines.append("=" * 50)
        
        return "\n".join(lines)


# Convenience function
def create_stealth_safety_system(config: Optional[Dict] = None) -> StealthSafetyOrchestrator:
    """Create and initialize the stealth safety system"""
    return StealthSafetyOrchestrator(config)
