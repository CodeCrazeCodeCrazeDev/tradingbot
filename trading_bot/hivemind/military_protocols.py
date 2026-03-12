"""
Military-Grade Command Protocols for Hivemind
============================================================

Implements military-style command and control structure:
- Strict chain of command
- Operational security levels
- Threat assessment and response
- Mission planning and execution
- Rules of engagement
- Battle damage assessment
"""

import logging
import asyncio
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Set, Callable
from enum import Enum
import hashlib
import json

logger = logging.getLogger(__name__)


# ============================================================
# OPERATIONAL SECURITY LEVELS (OPSEC)
# ============================================================

class SecurityClearance(Enum):
    """Security clearance levels"""
    UNCLASSIFIED = 0      # Public information
    CONFIDENTIAL = 1      # Internal use only
    SECRET = 2            # Restricted access
    TOP_SECRET = 3        # Need-to-know basis
    COSMIC_TOP_SECRET = 4 # Highest classification


class ThreatLevel(Enum):
    """Threat condition levels (THREATCON)"""
    ALPHA = "alpha"       # General threat, increased vigilance
    BRAVO = "bravo"       # Elevated threat, enhanced security
    CHARLIE = "charlie"   # Imminent threat, maximum security
    DELTA = "delta"       # Attack in progress, lockdown


class DefenseCondition(Enum):
    """Defense readiness condition (DEFCON)"""
    DEFCON_5 = 5  # Normal peacetime readiness
    DEFCON_4 = 4  # Increased intelligence watch
    DEFCON_3 = 3  # Increase force readiness above normal
    DEFCON_2 = 2  # Further increase in force readiness
    DEFCON_1 = 1  # Maximum force readiness (war imminent)


class OperationalMode(Enum):
    """Operational modes"""
    STANDBY = "standby"           # Monitoring only
    RECONNAISSANCE = "recon"      # Intelligence gathering
    PATROL = "patrol"             # Active monitoring
    ENGAGEMENT = "engagement"     # Active trading
    DEFENSIVE = "defensive"       # Risk reduction mode
    OFFENSIVE = "offensive"       # Aggressive alpha capture
    RETREAT = "retreat"           # Exit all positions
    LOCKDOWN = "lockdown"         # No new positions, hold


# ============================================================
# CHAIN OF COMMAND
# ============================================================

class Rank(Enum):
    """Military ranks for node hierarchy"""
    PRIVATE = 1           # Basic node
    CORPORAL = 2          # Experienced node
    SERGEANT = 3          # Squad leader
    LIEUTENANT = 4        # Platoon leader
    CAPTAIN = 5           # Company commander
    MAJOR = 6             # Battalion staff
    COLONEL = 7           # Regiment commander
    GENERAL = 8           # Division commander
    COMMANDER_IN_CHIEF = 9  # Supreme commander


@dataclass
class CommandAuthority:
    """Command authority for a unit"""
    rank: Rank
    unit_id: str
    clearance: SecurityClearance
    authorized_actions: Set[str] = field(default_factory=set)
    subordinates: List[str] = field(default_factory=list)
    superior: Optional[str] = None
    
    def can_authorize(self, action: str) -> bool:
        """Check if this authority can authorize an action"""
        return action in self.authorized_actions or self.rank.value >= Rank.COLONEL.value
    
    def outranks(self, other: 'CommandAuthority') -> bool:
        """Check if this authority outranks another"""
        return self.rank.value > other.rank.value


# ============================================================
# MISSION PLANNING
# ============================================================

class MissionType(Enum):
    """Types of trading missions"""
    RECONNAISSANCE = "recon"          # Market analysis
    STRIKE = "strike"                 # Quick entry/exit
    SUSTAINED_OPERATION = "sustained" # Position building
    DEFENSIVE = "defensive"           # Risk management
    EXTRACTION = "extraction"         # Exit positions
    SUPPORT = "support"               # Hedging operations


class MissionPriority(Enum):
    """Mission priority levels"""
    ROUTINE = 1
    PRIORITY = 2
    IMMEDIATE = 3
    FLASH = 4
    FLASH_OVERRIDE = 5  # Highest priority


@dataclass
class MissionObjective:
    """Single mission objective"""
    id: str
    description: str
    target: str  # Symbol or asset
    success_criteria: Dict[str, Any]
    priority: MissionPriority = MissionPriority.ROUTINE
    deadline: Optional[datetime] = None
    status: str = "pending"  # pending, in_progress, completed, failed, aborted


@dataclass
class MissionPlan:
    """Complete mission plan"""
    id: str
    codename: str
    mission_type: MissionType
    classification: SecurityClearance
    commander: str
    objectives: List[MissionObjective] = field(default_factory=list)
    
    # Timing
    h_hour: Optional[datetime] = None  # Execution time
    duration_hours: float = 24.0
    
    # Resources
    allocated_capital: float = 0.0
    max_risk_percent: float = 0.02
    
    # Rules of engagement
    roe: Dict[str, Any] = field(default_factory=dict)
    
    # Status
    status: str = "planning"  # planning, approved, executing, completed, aborted
    created_at: datetime = field(default_factory=datetime.utcnow)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': self.id,
            'codename': self.codename,
            'mission_type': self.mission_type.value,
            'classification': self.classification.name,
            'status': self.status,
            'objectives': len(self.objectives),
        }


# ============================================================
# RULES OF ENGAGEMENT (ROE)
# ============================================================

@dataclass
class RulesOfEngagement:
    """Rules of engagement for trading operations"""
    # Position limits
    max_position_size: float = 0.05      # 5% of capital
    max_single_trade_risk: float = 0.02  # 2% risk per trade
    max_daily_loss: float = 0.05         # 5% daily loss limit
    max_drawdown: float = 0.15           # 15% max drawdown
    
    # Entry rules
    min_confidence: float = 0.6          # Minimum signal confidence
    min_consensus: float = 0.5           # Minimum hivemind consensus
    require_confirmation: bool = True     # Require signal confirmation
    
    # Exit rules
    mandatory_stop_loss: bool = True
    max_hold_time_hours: float = 168.0   # 1 week max hold
    
    # Engagement conditions
    allowed_sessions: List[str] = field(default_factory=lambda: ['london', 'new_york'])
    forbidden_events: List[str] = field(default_factory=lambda: ['FOMC', 'NFP', 'ECB'])
    
    # Escalation
    escalate_on_loss_streak: int = 3     # Escalate after 3 consecutive losses
    require_approval_above: float = 0.03  # Require approval for >3% risk
    
    def validate_engagement(self, trade: Dict[str, Any]) -> tuple:
        """Validate if a trade meets ROE"""
        violations = []
        
        if trade.get('risk_percent', 0) > self.max_single_trade_risk:
            violations.append(f"Risk {trade['risk_percent']:.1%} exceeds max {self.max_single_trade_risk:.1%}")
        
        if trade.get('position_size_percent', 0) > self.max_position_size:
            violations.append(f"Position size exceeds max {self.max_position_size:.1%}")
        
        if trade.get('confidence', 0) < self.min_confidence:
            violations.append(f"Confidence {trade['confidence']:.1%} below min {self.min_confidence:.1%}")
        
        if self.mandatory_stop_loss and not trade.get('stop_loss'):
            violations.append("Stop loss is mandatory")
        
        return len(violations) == 0, violations


# ============================================================
# THREAT ASSESSMENT
# ============================================================

@dataclass
class ThreatAssessment:
    """Market threat assessment"""
    timestamp: datetime = field(default_factory=datetime.utcnow)
    threat_level: ThreatLevel = ThreatLevel.ALPHA
    
    # Threat factors
    volatility_threat: float = 0.0       # 0-1
    liquidity_threat: float = 0.0        # 0-1
    correlation_threat: float = 0.0      # 0-1
    event_threat: float = 0.0            # 0-1
    drawdown_threat: float = 0.0         # 0-1
    
    # Identified threats
    active_threats: List[str] = field(default_factory=list)
    
    # Recommendations
    recommended_action: str = "continue"
    reduce_exposure_by: float = 0.0
    
    @property
    def composite_threat(self) -> float:
        """Calculate composite threat score"""
        weights = {
            'volatility': 0.25,
            'liquidity': 0.20,
            'correlation': 0.15,
            'event': 0.25,
            'drawdown': 0.15,
        }
        return (
            self.volatility_threat * weights['volatility'] +
            self.liquidity_threat * weights['liquidity'] +
            self.correlation_threat * weights['correlation'] +
            self.event_threat * weights['event'] +
            self.drawdown_threat * weights['drawdown']
        )
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'threat_level': self.threat_level.value,
            'composite_threat': self.composite_threat,
            'volatility_threat': self.volatility_threat,
            'liquidity_threat': self.liquidity_threat,
            'event_threat': self.event_threat,
            'drawdown_threat': self.drawdown_threat,
            'active_threats': self.active_threats,
            'recommended_action': self.recommended_action,
        }


class ThreatAssessor:
    """Assesses market threats"""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self.threat_history: List[ThreatAssessment] = []
    
    def assess(self, market_data: Dict[str, Any], portfolio_state: Dict[str, Any]) -> ThreatAssessment:
        """Perform threat assessment"""
        assessment = ThreatAssessment()
        
        # Volatility threat
        vol_ratio = market_data.get('volatility_ratio', 1.0)
        assessment.volatility_threat = min((vol_ratio - 1) / 2, 1.0) if vol_ratio > 1 else 0
        if assessment.volatility_threat > 0.5:
            assessment.active_threats.append("HIGH_VOLATILITY")
        
        # Liquidity threat
        liquidity = market_data.get('liquidity_score', 0.8)
        assessment.liquidity_threat = max(0, 1 - liquidity)
        if assessment.liquidity_threat > 0.5:
            assessment.active_threats.append("LOW_LIQUIDITY")
        
        # Event threat
        events_24h = market_data.get('high_impact_events_24h', 0)
        assessment.event_threat = min(events_24h / 3, 1.0)
        if events_24h > 0:
            assessment.active_threats.append(f"EVENTS_PENDING_{events_24h}")
        
        # Drawdown threat
        current_dd = portfolio_state.get('current_drawdown', 0)
        max_dd = self.config.get('max_drawdown', 0.15)
        assessment.drawdown_threat = current_dd / max_dd if max_dd > 0 else 0
        if assessment.drawdown_threat > 0.5:
            assessment.active_threats.append("DRAWDOWN_WARNING")
        
        # Correlation threat
        correlation_exposure = portfolio_state.get('correlation_exposure', 0)
        assessment.correlation_threat = min(correlation_exposure / 0.8, 1.0)
        if assessment.correlation_threat > 0.6:
            assessment.active_threats.append("HIGH_CORRELATION")
        
        # Determine threat level
        composite = assessment.composite_threat
        if composite > 0.8:
            assessment.threat_level = ThreatLevel.DELTA
            assessment.recommended_action = "LOCKDOWN"
            assessment.reduce_exposure_by = 1.0
        elif composite > 0.6:
            assessment.threat_level = ThreatLevel.CHARLIE
            assessment.recommended_action = "DEFENSIVE"
            assessment.reduce_exposure_by = 0.5
        elif composite > 0.4:
            assessment.threat_level = ThreatLevel.BRAVO
            assessment.recommended_action = "REDUCE_RISK"
            assessment.reduce_exposure_by = 0.25
        else:
            assessment.threat_level = ThreatLevel.ALPHA
            assessment.recommended_action = "CONTINUE"
            assessment.reduce_exposure_by = 0.0
        
        self.threat_history.append(assessment)
        return assessment


# ============================================================
# BATTLE DAMAGE ASSESSMENT (BDA)
# ============================================================

@dataclass
class BattleDamageAssessment:
    """Post-trade damage assessment"""
    trade_id: str
    symbol: str
    timestamp: datetime = field(default_factory=datetime.utcnow)
    
    # Outcome
    pnl: float = 0.0
    pnl_percent: float = 0.0
    was_successful: bool = False
    
    # Analysis
    entry_quality: float = 0.0    # 0-1, how good was entry
    exit_quality: float = 0.0     # 0-1, how good was exit
    timing_score: float = 0.0     # 0-1, timing accuracy
    
    # Lessons learned
    what_worked: List[str] = field(default_factory=list)
    what_failed: List[str] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)
    
    # Impact
    account_impact: float = 0.0   # Impact on account equity
    confidence_impact: float = 0.0  # Impact on system confidence


# ============================================================
# MILITARY COMMAND CENTER
# ============================================================

class MilitaryCommandCenter:
    """
    Central command and control for the Hivemind.
    
    Implements military-grade protocols:
    - Chain of command
    - Mission planning
    - Rules of engagement
    - Threat assessment
    - Battle damage assessment
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        
        # Current state
        self.defcon = DefenseCondition.DEFCON_5
        self.operational_mode = OperationalMode.STANDBY
        self.threat_level = ThreatLevel.ALPHA
        
        # Command structure
        self.command_authorities: Dict[str, CommandAuthority] = {}
        self.chain_of_command: List[str] = []
        
        # Mission management
        self.active_missions: Dict[str, MissionPlan] = {}
        self.mission_history: List[MissionPlan] = []
        
        # Rules of engagement
        self.roe = RulesOfEngagement()
        
        # Threat assessment
        self.threat_assessor = ThreatAssessor(config)
        self.current_threat: Optional[ThreatAssessment] = None
        
        # Battle damage
        self.bda_history: List[BattleDamageAssessment] = []
        
        # Callbacks
        self.on_defcon_change: Optional[Callable[[DefenseCondition], None]] = None
        self.on_threat_change: Optional[Callable[[ThreatAssessment], None]] = None
        
        # Initialize command structure
        self._initialize_command_structure()
    
    def _initialize_command_structure(self) -> None:
        """Initialize the chain of command"""
        # Supreme Commander (Orchestrator)
        self.command_authorities['SUPREME_COMMANDER'] = CommandAuthority(
            rank=Rank.COMMANDER_IN_CHIEF,
            unit_id='SUPREME_COMMANDER',
            clearance=SecurityClearance.COSMIC_TOP_SECRET,
            authorized_actions={'ALL'},
        )
        
        # Division Commanders (Swarm Leaders)
        divisions = ['TECHNICAL', 'FUNDAMENTAL', 'SENTIMENT', 'RISK', 'EXECUTION', 'QUANT']
        for div in divisions:
            self.command_authorities[f'{div}_COMMANDER'] = CommandAuthority(
                rank=Rank.GENERAL,
                unit_id=f'{div}_COMMANDER',
                clearance=SecurityClearance.TOP_SECRET,
                authorized_actions={'ANALYZE', 'RECOMMEND', 'ALERT'},
                superior='SUPREME_COMMANDER',
            )
        
        self.chain_of_command = ['SUPREME_COMMANDER'] + [f'{d}_COMMANDER' for d in divisions]
    
    def set_defcon(self, level: DefenseCondition, reason: str = "") -> None:
        """Set defense condition"""
        old_level = self.defcon
        self.defcon = level
        
        logger.warning(f"DEFCON CHANGE: {old_level.name} -> {level.name}. Reason: {reason}")
        
        # Adjust operational mode based on DEFCON
        if level == DefenseCondition.DEFCON_1:
            self.operational_mode = OperationalMode.LOCKDOWN
        elif level == DefenseCondition.DEFCON_2:
            self.operational_mode = OperationalMode.DEFENSIVE
        elif level == DefenseCondition.DEFCON_3:
            self.operational_mode = OperationalMode.PATROL
        elif level == DefenseCondition.DEFCON_4:
            self.operational_mode = OperationalMode.RECONNAISSANCE
        else:
            self.operational_mode = OperationalMode.STANDBY
        
        if self.on_defcon_change:
            self.on_defcon_change(level)
    
    def assess_threat(self, market_data: Dict[str, Any], portfolio_state: Dict[str, Any]) -> ThreatAssessment:
        """Perform threat assessment"""
        assessment = self.threat_assessor.assess(market_data, portfolio_state)
        self.current_threat = assessment
        self.threat_level = assessment.threat_level
        
        # Auto-adjust DEFCON based on threat
        if assessment.threat_level == ThreatLevel.DELTA:
            self.set_defcon(DefenseCondition.DEFCON_1, "DELTA threat level")
        elif assessment.threat_level == ThreatLevel.CHARLIE:
            self.set_defcon(DefenseCondition.DEFCON_2, "CHARLIE threat level")
        elif assessment.threat_level == ThreatLevel.BRAVO:
            self.set_defcon(DefenseCondition.DEFCON_3, "BRAVO threat level")
        
        if self.on_threat_change:
            self.on_threat_change(assessment)
        
        return assessment
    
    def create_mission(
        self,
        codename: str,
        mission_type: MissionType,
        objectives: List[Dict[str, Any]],
        commander: str = "SUPREME_COMMANDER",
        classification: SecurityClearance = SecurityClearance.SECRET,
    ) -> MissionPlan:
        """Create a new mission plan"""
        mission_id = hashlib.md5(f"{codename}{datetime.utcnow().isoformat()}".encode()).hexdigest()[:12]
        
        mission_objectives = [
            MissionObjective(
                id=f"{mission_id}_obj_{i}",
                description=obj.get('description', ''),
                target=obj.get('target', ''),
                success_criteria=obj.get('success_criteria', {}),
                priority=MissionPriority(obj.get('priority', 1)),
            )
            for i, obj in enumerate(objectives)
        ]
        
        mission = MissionPlan(
            id=mission_id,
            codename=codename,
            mission_type=mission_type,
            classification=classification,
            commander=commander,
            objectives=mission_objectives,
            roe=self.roe.__dict__,
        )
        
        self.active_missions[mission_id] = mission
        logger.info(f"Mission {codename} ({mission_id}) created with {len(objectives)} objectives")
        
        return mission
    
    def approve_mission(self, mission_id: str, approver: str) -> bool:
        """Approve a mission for execution"""
        if mission_id not in self.active_missions:
            return False
        
        mission = self.active_missions[mission_id]
        
        # Check authority
        if approver not in self.command_authorities:
            logger.warning(f"Unknown approver: {approver}")
            return False
        
        authority = self.command_authorities[approver]
        if authority.rank.value < Rank.COLONEL.value:
            logger.warning(f"Insufficient rank to approve mission: {authority.rank.name}")
            return False
        
        mission.status = "approved"
        mission.h_hour = datetime.utcnow()
        
        logger.info(f"Mission {mission.codename} approved by {approver}")
        return True
    
    def validate_engagement(self, trade: Dict[str, Any]) -> tuple:
        """Validate trade against ROE"""
        # Check operational mode
        if self.operational_mode == OperationalMode.LOCKDOWN:
            return False, ["LOCKDOWN mode - no new positions allowed"]
        
        if self.operational_mode == OperationalMode.RETREAT:
            return False, ["RETREAT mode - only exits allowed"]
        
        if self.operational_mode == OperationalMode.DEFENSIVE:
            if trade.get('direction') != 'close':
                return False, ["DEFENSIVE mode - only risk reduction allowed"]
        
        # Check ROE
        roe_valid, roe_violations = self.roe.validate_engagement(trade)
        
        # Check threat level
        if self.threat_level == ThreatLevel.DELTA:
            return False, ["DELTA threat level - no engagement"]
        
        if self.threat_level == ThreatLevel.CHARLIE:
            if trade.get('risk_percent', 0) > self.roe.max_single_trade_risk * 0.5:
                roe_violations.append("CHARLIE threat - reduced risk limits")
        
        return roe_valid and len(roe_violations) == 0, roe_violations
    
    def record_bda(self, trade_result: Dict[str, Any]) -> BattleDamageAssessment:
        """Record battle damage assessment"""
        bda = BattleDamageAssessment(
            trade_id=trade_result.get('trade_id', 'unknown'),
            symbol=trade_result.get('symbol', ''),
            pnl=trade_result.get('pnl', 0),
            pnl_percent=trade_result.get('pnl_percent', 0),
            was_successful=trade_result.get('pnl', 0) > 0,
        )
        
        # Analyze entry quality
        if trade_result.get('entry_slippage', 0) < 0.0001:
            bda.entry_quality = 0.9
            bda.what_worked.append("Good entry execution")
        else:
            bda.entry_quality = 0.6
            bda.what_failed.append("Entry slippage")
        
        # Analyze exit quality
        if trade_result.get('hit_target', False):
            bda.exit_quality = 0.9
            bda.what_worked.append("Target reached")
        elif trade_result.get('hit_stop', False):
            bda.exit_quality = 0.5
            bda.what_failed.append("Stop loss hit")
        
        # Generate recommendations
        if not bda.was_successful:
            bda.recommendations.append("Review entry criteria")
            if trade_result.get('hold_time_hours', 0) > 48:
                bda.recommendations.append("Consider shorter hold times")
        
        self.bda_history.append(bda)
        return bda
    
    def get_sitrep(self) -> Dict[str, Any]:
        """Get situation report (SITREP)"""
        return {
            'timestamp': datetime.utcnow().isoformat(),
            'defcon': self.defcon.name,
            'operational_mode': self.operational_mode.value,
            'threat_level': self.threat_level.value,
            'threat_assessment': self.current_threat.to_dict() if self.current_threat else None,
            'active_missions': len(self.active_missions),
            'chain_of_command': self.chain_of_command,
            'roe_summary': {
                'max_risk': self.roe.max_single_trade_risk,
                'max_position': self.roe.max_position_size,
                'max_daily_loss': self.roe.max_daily_loss,
            },
        }
    
    def issue_order(self, order_type: str, params: Dict[str, Any], issuer: str) -> Dict[str, Any]:
        """Issue a command order"""
        # Validate issuer authority
        if issuer not in self.command_authorities:
            return {'success': False, 'error': 'Unknown issuer'}
        
        authority = self.command_authorities[issuer]
        
        order = {
            'id': hashlib.md5(f"{order_type}{datetime.utcnow().isoformat()}".encode()).hexdigest()[:8],
            'type': order_type,
            'params': params,
            'issuer': issuer,
            'issuer_rank': authority.rank.name,
            'timestamp': datetime.utcnow().isoformat(),
            'classification': authority.clearance.name,
        }
        
        logger.info(f"Order {order['id']} issued: {order_type} by {issuer}")
        
        return {'success': True, 'order': order}


# ============================================================
# MILITARY GRADE HIVEMIND INTEGRATION
# ============================================================

class MilitaryHiveMind:
    """
    Military-grade Hivemind with command and control protocols.
    
    Integrates:
    - Chain of command
    - Mission planning
    - Rules of engagement
    - Threat assessment
    - Battle damage assessment
    """
    
    def __init__(self, hivemind, config: Optional[Dict[str, Any]] = None):
        self.hivemind = hivemind
        self.command_center = MilitaryCommandCenter(config)
        self.config = config or {}
        
        # Mission tracking
        self.current_mission: Optional[MissionPlan] = None
        
        # Performance metrics
        self.missions_completed = 0
        self.missions_successful = 0
    
    async def execute_mission(
        self,
        symbol: str,
        market_data: Dict[str, Any],
        mission_type: MissionType = MissionType.RECONNAISSANCE,
    ) -> Dict[str, Any]:
        """Execute a trading mission with military protocols"""
        
        # Step 1: Threat Assessment
        portfolio_state = market_data.get('portfolio', {})
        threat = self.command_center.assess_threat(market_data, portfolio_state)
        
        if threat.threat_level == ThreatLevel.DELTA:
            return {
                'success': False,
                'action': 'ABORT',
                'reason': 'DELTA threat level - mission aborted',
                'threat': threat.to_dict(),
            }
        
        # Step 2: Create Mission
        mission = self.command_center.create_mission(
            codename=f"OP_{symbol}_{datetime.utcnow().strftime('%H%M')}",
            mission_type=mission_type,
            objectives=[{
                'description': f"Analyze {symbol} for trading opportunity",
                'target': symbol,
                'success_criteria': {'min_confidence': 0.6},
                'priority': 2,
            }],
        )
        
        # Step 3: Approve Mission
        self.command_center.approve_mission(mission.id, 'SUPREME_COMMANDER')
        self.current_mission = mission
        
        # Step 4: Execute Analysis (Hivemind)
        decision = await self.hivemind.analyze(symbol, market_data)
        
        # Step 5: Validate Against ROE
        trade_params = {
            'direction': decision.action,
            'confidence': decision.confidence,
            'risk_percent': market_data.get('risk_percent', 0.02),
            'position_size_percent': market_data.get('position_size_percent', 0.05),
            'stop_loss': decision.stop_loss,
        }
        
        roe_valid, violations = self.command_center.validate_engagement(trade_params)
        
        # Step 6: Generate Orders
        if decision.action in ['BUY', 'SELL'] and roe_valid:
            order = self.command_center.issue_order(
                order_type='EXECUTE_TRADE',
                params={
                    'symbol': symbol,
                    'action': decision.action,
                    'entry': decision.entry_price,
                    'stop_loss': decision.stop_loss,
                    'take_profit': decision.take_profit,
                    'size': decision.position_size,
                },
                issuer='SUPREME_COMMANDER',
            )
            
            mission.status = 'executing'
        else:
            order = None
            mission.status = 'completed' if decision.action == 'HOLD' else 'aborted'
        
        # Step 7: Generate SITREP
        sitrep = self.command_center.get_sitrep()
        
        return {
            'success': True,
            'mission': mission.to_dict(),
            'decision': decision.to_dict(),
            'threat': threat.to_dict(),
            'roe_valid': roe_valid,
            'roe_violations': violations,
            'order': order,
            'sitrep': sitrep,
        }
    
    def record_mission_outcome(self, trade_result: Dict[str, Any]) -> BattleDamageAssessment:
        """Record mission outcome"""
        bda = self.command_center.record_bda(trade_result)
        
        self.missions_completed += 1
        if bda.was_successful:
            self.missions_successful += 1
        
        if self.current_mission:
            self.current_mission.status = 'completed'
            self.command_center.mission_history.append(self.current_mission)
            self.current_mission = None
        
        return bda
    
    def get_combat_readiness(self) -> Dict[str, Any]:
        """Get combat readiness report"""
        return {
            'defcon': self.command_center.defcon.name,
            'operational_mode': self.command_center.operational_mode.value,
            'threat_level': self.command_center.threat_level.value,
            'missions_completed': self.missions_completed,
            'mission_success_rate': self.missions_successful / self.missions_completed if self.missions_completed > 0 else 0,
            'active_missions': len(self.command_center.active_missions),
            'chain_of_command_status': 'OPERATIONAL',
        }
