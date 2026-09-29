"""
Military-Grade Protocols for Perplexity Trading Architecture
============================================================

Implements military-style command structure for AlphaAlgo:
- Tactical mission planning
- Strategic intelligence gathering
- Operational security (OPSEC)
- Combat readiness levels
- Rules of engagement (ROE)
- After-action review (AAR)
"""

import logging
import asyncio
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Set, Callable, Tuple
from enum import Enum
import hashlib
import json

logger = logging.getLogger(__name__)


# ============================================================
# COMBAT READINESS & ALERT LEVELS
# ============================================================

class CombatReadiness(Enum):
    """Combat readiness levels"""
    CONDITION_1 = "GENERAL_QUARTERS"    # Maximum readiness, all stations manned
    CONDITION_2 = "MODIFIED_GQ"         # High readiness, key stations manned
    CONDITION_3 = "WARTIME_CRUISING"    # Normal wartime readiness
    CONDITION_4 = "PEACETIME_CRUISING"  # Normal peacetime operations
    CONDITION_5 = "STANDDOWN"           # Maintenance/rest period


class AlertStatus(Enum):
    """Alert status levels"""
    GREEN = "green"       # Normal operations
    YELLOW = "yellow"     # Elevated awareness
    ORANGE = "orange"     # High alert
    RED = "red"           # Imminent action
    BLACK = "black"       # Emergency/crisis


class IntelligenceLevel(Enum):
    """Intelligence classification levels"""
    UNCLASSIFIED = 0
    FOUO = 1              # For Official Use Only
    CONFIDENTIAL = 2
    SECRET = 3
    TOP_SECRET = 4
    SCI = 5               # Sensitive Compartmented Information


# ============================================================
# TACTICAL OPERATIONS
# ============================================================

class TacticalObjective(Enum):
    """Tactical objectives for trading operations"""
    RECONNAISSANCE = "recon"           # Market intelligence gathering
    OFFENSIVE_STRIKE = "strike"        # Quick profit capture
    SUSTAINED_ASSAULT = "assault"      # Position building
    DEFENSIVE_POSTURE = "defense"      # Risk management
    STRATEGIC_WITHDRAWAL = "withdraw"  # Exit positions
    FLANKING_MANEUVER = "flank"       # Contrarian plays
    AMBUSH = "ambush"                  # Limit order traps
    SIEGE = "siege"                    # Long-term accumulation


@dataclass
class TacticalOrder:
    """A tactical order for execution"""
    order_id: str
    objective: TacticalObjective
    target: str  # Symbol
    
    # Execution parameters
    entry_zone: Tuple[float, float] = (0.0, 0.0)  # Price range
    target_zone: Tuple[float, float] = (0.0, 0.0)
    retreat_line: float = 0.0  # Stop loss
    
    # Force allocation
    force_size: float = 0.0  # Position size
    reserve_force: float = 0.0  # Additional capital for scaling
    
    # Timing
    h_hour: Optional[datetime] = None
    max_duration_hours: float = 24.0
    
    # Rules
    rules_of_engagement: Dict[str, Any] = field(default_factory=dict)
    
    # Status
    status: str = "pending"  # pending, active, completed, aborted
    created_at: datetime = field(default_factory=datetime.utcnow)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'order_id': self.order_id,
            'objective': self.objective.value,
            'target': self.target,
            'entry_zone': self.entry_zone,
            'target_zone': self.target_zone,
            'retreat_line': self.retreat_line,
            'force_size': self.force_size,
            'status': self.status,
        }


# ============================================================
# INTELLIGENCE OPERATIONS
# ============================================================

@dataclass
class IntelligenceReport:
    """Intelligence report on market conditions"""
    report_id: str
    classification: IntelligenceLevel
    timestamp: datetime = field(default_factory=datetime.utcnow)
    
    # Source assessment
    source_reliability: str = "B"  # A=Completely reliable, F=Cannot be judged
    information_credibility: str = "2"  # 1=Confirmed, 6=Cannot be judged
    
    # Intelligence content
    subject: str = ""
    summary: str = ""
    details: Dict[str, Any] = field(default_factory=dict)
    
    # Assessment
    threat_indicators: List[str] = field(default_factory=list)
    opportunity_indicators: List[str] = field(default_factory=list)
    recommended_actions: List[str] = field(default_factory=list)
    
    # Validity
    valid_until: Optional[datetime] = None
    
    def get_reliability_code(self) -> str:
        """Get NATO-style reliability code"""
        return f"{self.source_reliability}{self.information_credibility}"


class IntelligenceCell:
    """Intelligence gathering and analysis cell"""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self.reports: List[IntelligenceReport] = []
        self.active_collection_targets: Set[str] = set()
    
    def collect_sigint(self, market_data: Dict[str, Any]) -> IntelligenceReport:
        """Collect signals intelligence from market data"""
        report_id = f"SIGINT_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"
        
        # Analyze price signals
        ohlcv = market_data.get('ohlcv', [])
        threat_indicators = []
        opportunity_indicators = []
        
        if ohlcv and len(ohlcv) >= 20:
            closes = [bar.get('close', 0) for bar in ohlcv[-20:]]
            volumes = [bar.get('volume', 0) for bar in ohlcv[-20:]]
            
            # Volume spike detection
            avg_vol = sum(volumes[:-1]) / len(volumes[:-1]) if len(volumes) > 1 else 1
            if volumes[-1] > avg_vol * 2:
                threat_indicators.append("VOLUME_SPIKE_DETECTED")
            
            # Price momentum
            if closes[-1] > closes[-5] > closes[-10]:
                opportunity_indicators.append("BULLISH_MOMENTUM")
            elif closes[-1] < closes[-5] < closes[-10]:
                threat_indicators.append("BEARISH_MOMENTUM")
        
        report = IntelligenceReport(
            report_id=report_id,
            classification=IntelligenceLevel.CONFIDENTIAL,
            source_reliability="B",
            information_credibility="2",
            subject="Market Signals Intelligence",
            summary=f"SIGINT collection on market data",
            details={'ohlcv_bars': len(ohlcv) if ohlcv else 0},
            threat_indicators=threat_indicators,
            opportunity_indicators=opportunity_indicators,
            valid_until=datetime.utcnow() + timedelta(hours=1),
        )
        
        self.reports.append(report)
        return report
    
    def collect_humint(self, sentiment_data: Dict[str, Any]) -> IntelligenceReport:
        """Collect human intelligence from sentiment sources"""
        report_id = f"HUMINT_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"
        
        threat_indicators = []
        opportunity_indicators = []
        
        # Analyze sentiment
        overall_sentiment = sentiment_data.get('overall_score', 0)
        fear_greed = sentiment_data.get('fear_greed_index', 50)
        
        if fear_greed > 80:
            threat_indicators.append("EXTREME_GREED_CONTRARIAN_SIGNAL")
        elif fear_greed < 20:
            opportunity_indicators.append("EXTREME_FEAR_CONTRARIAN_SIGNAL")
        
        if overall_sentiment > 0.5:
            opportunity_indicators.append("BULLISH_SENTIMENT")
        elif overall_sentiment < -0.5:
            threat_indicators.append("BEARISH_SENTIMENT")
        
        report = IntelligenceReport(
            report_id=report_id,
            classification=IntelligenceLevel.SECRET,
            source_reliability="C",
            information_credibility="3",
            subject="Market Sentiment Intelligence",
            summary=f"HUMINT from sentiment sources. Fear/Greed: {fear_greed}",
            details=sentiment_data,
            threat_indicators=threat_indicators,
            opportunity_indicators=opportunity_indicators,
            valid_until=datetime.utcnow() + timedelta(hours=4),
        )
        
        self.reports.append(report)
        return report
    
    def produce_intelligence_estimate(self) -> Dict[str, Any]:
        """Produce consolidated intelligence estimate"""
        valid_reports = [
            r for r in self.reports
            if r.valid_until is None or r.valid_until > datetime.utcnow()
        ]
        
        all_threats = []
        all_opportunities = []
        
        for report in valid_reports[-10:]:  # Last 10 valid reports
            all_threats.extend(report.threat_indicators)
            all_opportunities.extend(report.opportunity_indicators)
        
        # Count occurrences
        threat_counts = {}
        for t in all_threats:
            threat_counts[t] = threat_counts.get(t, 0) + 1
        
        opportunity_counts = {}
        for o in all_opportunities:
            opportunity_counts[o] = opportunity_counts.get(o, 0) + 1
        
        return {
            'timestamp': datetime.utcnow().isoformat(),
            'reports_analyzed': len(valid_reports),
            'primary_threats': sorted(threat_counts.items(), key=lambda x: x[1], reverse=True)[:5],
            'primary_opportunities': sorted(opportunity_counts.items(), key=lambda x: x[1], reverse=True)[:5],
            'overall_assessment': 'FAVORABLE' if len(all_opportunities) > len(all_threats) else 'UNFAVORABLE',
        }


# ============================================================
# RULES OF ENGAGEMENT (ROE)
# ============================================================

@dataclass
class MilitaryROE:
    """Military-grade Rules of Engagement"""
    
    # FORCE AUTHORIZATION
    max_force_deployment: float = 0.10      # 10% max position
    max_simultaneous_engagements: int = 5   # Max concurrent positions
    reserve_requirement: float = 0.30       # 30% must stay in reserve
    
    # ENGAGEMENT CRITERIA
    min_intel_confidence: float = 0.7       # Minimum intelligence confidence
    min_signal_strength: float = 0.5        # Minimum signal strength
    required_confirmations: int = 2         # Number of confirming signals
    
    # RISK PARAMETERS
    max_acceptable_loss: float = 0.02       # 2% max loss per engagement
    max_daily_casualties: float = 0.05      # 5% max daily loss
    max_drawdown_tolerance: float = 0.15    # 15% max drawdown
    
    # TIMING RESTRICTIONS
    no_engagement_periods: List[str] = field(default_factory=lambda: [
        "FOMC", "NFP", "ECB_RATE", "BOE_RATE", "BOJ_RATE"
    ])
    preferred_engagement_hours: List[int] = field(default_factory=lambda: [
        8, 9, 10, 11, 12, 13, 14, 15, 16  # London/NY overlap
    ])
    
    # ESCALATION RULES
    escalate_after_losses: int = 3          # Escalate after 3 consecutive losses
    require_command_approval_above: float = 0.05  # Approval for >5% risk
    
    # WITHDRAWAL CRITERIA
    mandatory_retreat_at_loss: float = 0.03  # Mandatory exit at 3% loss
    profit_protection_threshold: float = 0.02  # Protect profits above 2%
    
    def validate_engagement(self, engagement: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """Validate engagement against ROE"""
        violations = []
        
        # Check force size
        if engagement.get('position_size', 0) > self.max_force_deployment:
            violations.append(f"Force size {engagement['position_size']:.1%} exceeds max {self.max_force_deployment:.1%}")
        
        # Check risk
        if engagement.get('risk_percent', 0) > self.max_acceptable_loss:
            violations.append(f"Risk {engagement['risk_percent']:.1%} exceeds max {self.max_acceptable_loss:.1%}")
        
        # Check confidence
        if engagement.get('confidence', 0) < self.min_intel_confidence:
            violations.append(f"Intel confidence {engagement['confidence']:.1%} below min {self.min_intel_confidence:.1%}")
        
        # Check signal strength
        if engagement.get('signal_strength', 0) < self.min_signal_strength:
            violations.append(f"Signal strength {engagement['signal_strength']:.1%} below min {self.min_signal_strength:.1%}")
        
        # Check timing
        current_hour = datetime.utcnow().hour
        if current_hour not in self.preferred_engagement_hours:
            violations.append(f"Current hour {current_hour} not in preferred engagement window")
        
        # Check for restricted events
        upcoming_events = engagement.get('upcoming_events', [])
        for event in upcoming_events:
            if event in self.no_engagement_periods:
                violations.append(f"Engagement restricted due to {event}")
        
        return len(violations) == 0, violations


# ============================================================
# COMMAND & CONTROL
# ============================================================

class CommandLevel(Enum):
    """Command levels"""
    STRATEGIC = "strategic"     # High-level portfolio decisions
    OPERATIONAL = "operational" # Campaign-level decisions
    TACTICAL = "tactical"       # Individual trade decisions


@dataclass
class CommandDirective:
    """A command directive from higher authority"""
    directive_id: str
    level: CommandLevel
    issuer: str
    timestamp: datetime = field(default_factory=datetime.utcnow)
    
    # Content
    subject: str = ""
    orders: List[str] = field(default_factory=list)
    constraints: Dict[str, Any] = field(default_factory=dict)
    
    # Validity
    effective_from: datetime = field(default_factory=datetime.utcnow)
    effective_until: Optional[datetime] = None
    
    # Status
    acknowledged: bool = False
    executed: bool = False


class StrategicCommand:
    """Strategic command center for Perplexity Trading"""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        
        # Current state
        self.combat_readiness = CombatReadiness.CONDITION_4
        self.alert_status = AlertStatus.GREEN
        
        # ROE
        self.roe = MilitaryROE()
        
        # Intelligence
        self.intel_cell = IntelligenceCell(config)
        
        # Active directives
        self.active_directives: List[CommandDirective] = []
        
        # Tactical orders
        self.tactical_orders: Dict[str, TacticalOrder] = {}
        
        # After-action reports
        self.aar_history: List[Dict[str, Any]] = []
        
        # Callbacks
        self.on_alert_change: Optional[Callable[[AlertStatus], None]] = None
    
    def set_combat_readiness(self, level: CombatReadiness, reason: str = "") -> None:
        """Set combat readiness level"""
        old_level = self.combat_readiness
        self.combat_readiness = level
        
        logger.warning(f"COMBAT READINESS: {old_level.name} -> {level.name}. Reason: {reason}")
        
        # Adjust alert status based on readiness
        if level == CombatReadiness.CONDITION_1:
            self.set_alert_status(AlertStatus.RED, "General Quarters")
        elif level == CombatReadiness.CONDITION_2:
            self.set_alert_status(AlertStatus.ORANGE, "Modified GQ")
        elif level == CombatReadiness.CONDITION_3:
            self.set_alert_status(AlertStatus.YELLOW, "Wartime Cruising")
        else:
            self.set_alert_status(AlertStatus.GREEN, "Normal Operations")
    
    def set_alert_status(self, status: AlertStatus, reason: str = "") -> None:
        """Set alert status"""
        old_status = self.alert_status
        self.alert_status = status
        
        logger.info(f"ALERT STATUS: {old_status.value} -> {status.value}. Reason: {reason}")
        
        if self.on_alert_change:
            self.on_alert_change(status)
    
    def issue_tactical_order(
        self,
        objective: TacticalObjective,
        target: str,
        entry_zone: Tuple[float, float],
        target_zone: Tuple[float, float],
        retreat_line: float,
        force_size: float,
    ) -> TacticalOrder:
        """Issue a tactical order"""
        order_id = f"TACORD_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}_{target}"
        
        order = TacticalOrder(
            order_id=order_id,
            objective=objective,
            target=target,
            entry_zone=entry_zone,
            target_zone=target_zone,
            retreat_line=retreat_line,
            force_size=force_size,
            rules_of_engagement=self.roe.__dict__,
        )
        
        self.tactical_orders[order_id] = order
        logger.info(f"Tactical order issued: {order_id} - {objective.value} on {target}")
        
        return order
    
    def validate_tactical_order(self, order: TacticalOrder) -> Tuple[bool, List[str]]:
        """Validate tactical order against ROE"""
        engagement = {
            'position_size': order.force_size,
            'risk_percent': abs(order.entry_zone[0] - order.retreat_line) / order.entry_zone[0] if order.entry_zone[0] > 0 else 0,
            'confidence': 0.8,  # Default
            'signal_strength': 0.7,  # Default
        }
        
        return self.roe.validate_engagement(engagement)
    
    def gather_intelligence(self, market_data: Dict[str, Any]) -> Dict[str, Any]:
        """Gather all intelligence"""
        # SIGINT from market data
        sigint = self.intel_cell.collect_sigint(market_data)
        
        # HUMINT from sentiment
        sentiment = market_data.get('sentiment', {})
        humint = self.intel_cell.collect_humint(sentiment)
        
        # Produce estimate
        estimate = self.intel_cell.produce_intelligence_estimate()
        
        return {
            'sigint': sigint.get_reliability_code(),
            'humint': humint.get_reliability_code(),
            'estimate': estimate,
            'threat_indicators': sigint.threat_indicators + humint.threat_indicators,
            'opportunity_indicators': sigint.opportunity_indicators + humint.opportunity_indicators,
        }
    
    def conduct_aar(self, trade_result: Dict[str, Any]) -> Dict[str, Any]:
        """Conduct After-Action Review"""
        aar = {
            'timestamp': datetime.utcnow().isoformat(),
            'trade_id': trade_result.get('trade_id', 'unknown'),
            'symbol': trade_result.get('symbol', ''),
            'outcome': 'SUCCESS' if trade_result.get('pnl', 0) > 0 else 'FAILURE',
            'pnl': trade_result.get('pnl', 0),
            'pnl_percent': trade_result.get('pnl_percent', 0),
            
            # Analysis
            'what_was_planned': trade_result.get('planned_action', ''),
            'what_happened': trade_result.get('actual_action', ''),
            'what_went_well': [],
            'what_went_wrong': [],
            'lessons_learned': [],
            'recommendations': [],
        }
        
        # Analyze outcome
        if trade_result.get('pnl', 0) > 0:
            aar['what_went_well'].append("Profitable outcome achieved")
            if trade_result.get('hit_target', False):
                aar['what_went_well'].append("Target reached")
        else:
            aar['what_went_wrong'].append("Loss incurred")
            if trade_result.get('hit_stop', False):
                aar['what_went_wrong'].append("Stop loss triggered")
                aar['lessons_learned'].append("Review stop placement methodology")
        
        # Entry analysis
        entry_slippage = trade_result.get('entry_slippage', 0)
        if entry_slippage > 0.0002:
            aar['what_went_wrong'].append(f"High entry slippage: {entry_slippage}")
            aar['recommendations'].append("Use limit orders for entry")
        
        # Timing analysis
        hold_time = trade_result.get('hold_time_hours', 0)
        if hold_time > 48 and trade_result.get('pnl', 0) < 0:
            aar['lessons_learned'].append("Extended hold time correlated with loss")
            aar['recommendations'].append("Consider tighter time-based exits")
        
        self.aar_history.append(aar)
        return aar
    
    def get_sitrep(self) -> Dict[str, Any]:
        """Get situation report"""
        return {
            'timestamp': datetime.utcnow().isoformat(),
            'combat_readiness': self.combat_readiness.name,
            'alert_status': self.alert_status.value,
            'active_orders': len(self.tactical_orders),
            'intel_reports': len(self.intel_cell.reports),
            'roe_summary': {
                'max_force': self.roe.max_force_deployment,
                'max_risk': self.roe.max_acceptable_loss,
                'max_daily_loss': self.roe.max_daily_casualties,
            },
            'recent_aar': len(self.aar_history),
        }


# ============================================================
# MILITARY PERPLEXITY INTEGRATION
# ============================================================

class MilitaryPerplexityOrchestrator:
    """
    Military-grade Perplexity Trading Orchestrator.
    
    Integrates:
    - Strategic command
    - Intelligence operations
    - Tactical execution
    - Rules of engagement
    - After-action review
    """
    
    def __init__(self, orchestrator, config: Optional[Dict[str, Any]] = None):
        self.orchestrator = orchestrator
        self.command = StrategicCommand(config)
        self.config = config or {}
        
        # Mission tracking
        self.active_mission: Optional[str] = None
        self.missions_executed = 0
        self.missions_successful = 0
    
    async def execute_tactical_mission(
        self,
        symbol: str,
        market_data: Dict[str, Any],
        objective: TacticalObjective = TacticalObjective.RECONNAISSANCE,
    ) -> Dict[str, Any]:
        """Execute a tactical trading mission"""
        
        # Phase 1: Intelligence Gathering
        logger.info(f"Phase 1: Intelligence gathering for {symbol}")
        intel = self.command.gather_intelligence(market_data)
        
        # Assess threat level
        threat_count = len(intel.get('threat_indicators', []))
        if threat_count >= 3:
            self.command.set_alert_status(AlertStatus.RED, f"{threat_count} threat indicators")
            if objective != TacticalObjective.DEFENSIVE_POSTURE:
                return {
                    'success': False,
                    'action': 'ABORT',
                    'reason': f'High threat environment ({threat_count} indicators)',
                    'intel': intel,
                }
        
        # Phase 2: Mission Planning
        logger.info(f"Phase 2: Mission planning - {objective.value}")
        
        # Get Perplexity analysis
        decision = await self.orchestrator.analyze(
            query=f"Analyze {symbol} for {objective.value} opportunity",
            symbol=symbol,
            require_approval=False,
        )
        
        # Phase 3: ROE Validation
        logger.info("Phase 3: ROE validation")
        
        engagement = {
            'position_size': decision.position_size / 10000 if decision.position_size else 0.05,
            'risk_percent': 0.02,  # Default 2%
            'confidence': decision.confidence,
            'signal_strength': abs(decision.direction.to_numeric()) if hasattr(decision, 'direction') else 0.5,
            'upcoming_events': market_data.get('upcoming_events', []),
        }
        
        roe_valid, violations = self.command.roe.validate_engagement(engagement)
        
        if not roe_valid:
            logger.warning(f"ROE violations: {violations}")
            if self.command.alert_status in [AlertStatus.RED, AlertStatus.BLACK]:
                return {
                    'success': False,
                    'action': 'ABORT',
                    'reason': f'ROE violations in high-alert environment',
                    'violations': violations,
                    'intel': intel,
                }
        
        # Phase 4: Tactical Order Generation
        logger.info("Phase 4: Tactical order generation")
        
        if decision.action in ['BUY', 'SELL']:
            current_price = market_data.get('current_price', decision.entry_price or 0)
            
            tactical_order = self.command.issue_tactical_order(
                objective=objective,
                target=symbol,
                entry_zone=(current_price * 0.999, current_price * 1.001),
                target_zone=(decision.take_profit or current_price * 1.02, decision.take_profit or current_price * 1.03),
                retreat_line=decision.stop_loss or current_price * 0.98,
                force_size=engagement['position_size'],
            )
            
            # Validate order
            order_valid, order_violations = self.command.validate_tactical_order(tactical_order)
            
            if not order_valid:
                tactical_order.status = 'rejected'
                return {
                    'success': False,
                    'action': 'REJECT',
                    'reason': 'Tactical order failed validation',
                    'violations': order_violations,
                }
            
            tactical_order.status = 'approved'
            self.active_mission = tactical_order.order_id
            self.missions_executed += 1
        else:
            tactical_order = None
        
        # Phase 5: Generate SITREP
        sitrep = self.command.get_sitrep()
        
        return {
            'success': True,
            'action': decision.action,
            'decision': decision.to_dict() if hasattr(decision, 'to_dict') else str(decision),
            'tactical_order': tactical_order.to_dict() if tactical_order else None,
            'intel': intel,
            'roe_valid': roe_valid,
            'roe_violations': violations,
            'sitrep': sitrep,
            'alert_status': self.command.alert_status.value,
            'combat_readiness': self.command.combat_readiness.name,
        }
    
    def record_mission_outcome(self, trade_result: Dict[str, Any]) -> Dict[str, Any]:
        """Record mission outcome and conduct AAR"""
        aar = self.command.conduct_aar(trade_result)
        
        if trade_result.get('pnl', 0) > 0:
            self.missions_successful += 1
        
        self.active_mission = None
        
        return aar
    
    def get_combat_status(self) -> Dict[str, Any]:
        """Get overall combat status"""
        return {
            'combat_readiness': self.command.combat_readiness.name,
            'alert_status': self.command.alert_status.value,
            'missions_executed': self.missions_executed,
            'mission_success_rate': self.missions_successful / self.missions_executed if self.missions_executed > 0 else 0,
            'active_mission': self.active_mission,
            'roe_active': True,
            'intel_reports': len(self.command.intel_cell.reports),
            'aar_conducted': len(self.command.aar_history),
        }
    
    def issue_standing_order(self, order_type: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Issue a standing order"""
        directive = CommandDirective(
            directive_id=f"SO_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}",
            level=CommandLevel.OPERATIONAL,
            issuer="STRATEGIC_COMMAND",
            subject=order_type,
            orders=[f"Execute {order_type} with params: {params}"],
            constraints=params,
        )
        
        self.command.active_directives.append(directive)
        
        return {
            'directive_id': directive.directive_id,
            'type': order_type,
            'status': 'issued',
        }
