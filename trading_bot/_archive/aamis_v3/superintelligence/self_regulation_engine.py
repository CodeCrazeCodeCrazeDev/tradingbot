"""
Self-Regulation Engine
Autonomous system monitoring, risk control, and behavioral governance
Prevents overtrading, manages drawdowns, and enforces safety limits
"""

import numpy as np
import pandas as pd
from typing import Any, Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import logging
from collections import deque, defaultdict
import numpy
import pandas

logger = logging.getLogger(__name__)


class RegulationLevel(Enum):
    """Regulation intensity levels"""
    NORMAL = "normal"
    CAUTIOUS = "cautious"
    RESTRICTED = "restricted"
    DEFENSIVE = "defensive"
    EMERGENCY = "emergency"
    SHUTDOWN = "shutdown"


class ViolationType(Enum):
    """Types of regulation violations"""
    MAX_DRAWDOWN = "max_drawdown"
    MAX_DAILY_LOSS = "max_daily_loss"
    MAX_POSITION_SIZE = "max_position_size"
    MAX_TRADES_PER_DAY = "max_trades_per_day"
    MAX_CONSECUTIVE_LOSSES = "max_consecutive_losses"
    OVERTRADING = "overtrading"
    EXCESSIVE_LEVERAGE = "excessive_leverage"
    CORRELATION_RISK = "correlation_risk"
    LIQUIDITY_RISK = "liquidity_risk"
    VOLATILITY_SPIKE = "volatility_spike"
    SYSTEM_OVERLOAD = "system_overload"


class HealthStatus(Enum):
    """System health status"""
    EXCELLENT = "excellent"
    GOOD = "good"
    FAIR = "fair"
    POOR = "poor"
    CRITICAL = "critical"


@dataclass
class RegulationRule:
    """A self-regulation rule"""
    rule_id: str
    rule_type: ViolationType
    threshold: float
    current_value: float
    
    # Actions
    action_on_breach: str  # reduce_size, stop_trading, alert, etc.
    severity: int  # 1-10
    
    # Status
    is_breached: bool = False
    breach_count: int = 0
    last_breach: Optional[datetime] = None
    
    # Metadata
    description: str = ""
    created_at: datetime = field(default_factory=datetime.now)


@dataclass
class RegulationAction:
    """Action taken by regulation system"""
    action_id: str
    action_type: str
    reason: str
    
    # Impact
    position_size_multiplier: float  # 0-1
    trading_allowed: bool
    max_trades_allowed: int
    
    # Details
    triggered_rules: List[str]
    severity: int
    
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class SystemHealth:
    """Overall system health assessment"""
    health_status: HealthStatus
    health_score: float  # 0-100
    
    # Metrics
    drawdown_health: float
    risk_health: float
    performance_health: float
    behavioral_health: float
    technical_health: float
    
    # Issues
    active_violations: List[str]
    warnings: List[str]
    
    # Recommendations
    recommended_actions: List[str]
    
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class TradingBehavior:
    """Trading behavior analysis"""
    # Frequency
    trades_per_day: float
    trades_per_hour: float
    
    # Win/Loss patterns
    consecutive_wins: int
    consecutive_losses: int
    win_rate: float
    
    # Position sizing
    avg_position_size: float
    max_position_size: float
    position_size_volatility: float
    
    # Timing
    avg_hold_time: float  # hours
    trades_in_rush_hours: int
    
    # Risk
    avg_risk_per_trade: float
    max_risk_taken: float
    
    # Behavioral flags
    is_overtrading: bool = False
    is_revenge_trading: bool = False
    is_chasing_losses: bool = False
    is_overconfident: bool = False
    
    timestamp: datetime = field(default_factory=datetime.now)


class DrawdownMonitor:
    """
    Monitors and controls drawdown
    """
    
    def __init__(self, max_drawdown: float = 0.20, warning_drawdown: float = 0.10):
        self.max_drawdown = max_drawdown
        self.warning_drawdown = warning_drawdown
        
        # Tracking
        self.peak_equity = 0.0
        self.current_equity = 0.0
        self.current_drawdown = 0.0
        
        # History
        self.drawdown_history: deque = deque(maxlen=1000)
        
        logger.info(f"Drawdown Monitor initialized: max={max_drawdown:.1%}, warning={warning_drawdown:.1%}")
    
    def update(self, current_equity: float) -> Dict[str, Any]:
        """Update drawdown calculation"""
        
        self.current_equity = current_equity
        
        # Update peak
        if current_equity > self.peak_equity:
            self.peak_equity = current_equity
        
        # Calculate drawdown
        if self.peak_equity > 0:
            self.current_drawdown = (self.peak_equity - current_equity) / self.peak_equity
        else:
            self.current_drawdown = 0.0
        
        # Store history
        self.drawdown_history.append({
            'timestamp': datetime.now(),
            'equity': current_equity,
            'peak': self.peak_equity,
            'drawdown': self.current_drawdown
        })
        
        # Determine status
        if self.current_drawdown >= self.max_drawdown:
            status = "CRITICAL"
            action = "STOP_TRADING"
        elif self.current_drawdown >= self.warning_drawdown:
            status = "WARNING"
            action = "REDUCE_RISK"
        else:
            status = "NORMAL"
            action = "NONE"
        
        return {
            'current_drawdown': self.current_drawdown,
            'peak_equity': self.peak_equity,
            'current_equity': current_equity,
            'status': status,
            'action': action,
            'is_breached': self.current_drawdown >= self.max_drawdown
        }


class OvertradingDetector:
    """
    Detects and prevents overtrading
    """
    
    def __init__(self, max_trades_per_day: int = 20, max_trades_per_hour: int = 5):
        self.max_trades_per_day = max_trades_per_day
        self.max_trades_per_hour = max_trades_per_hour
        
        # Tracking
        self.trades_today: List[datetime] = []
        self.trades_this_hour: List[datetime] = []
        
        logger.info(f"Overtrading Detector initialized: max_day={max_trades_per_day}, max_hour={max_trades_per_hour}")
    
    def record_trade(self, trade_time: datetime = None):
        """Record a trade"""
        
        if trade_time is None:
            trade_time = datetime.now()
        
        self.trades_today.append(trade_time)
        self.trades_this_hour.append(trade_time)
        
        # Clean old trades
        self._clean_old_trades()
    
    def check_overtrading(self) -> Dict[str, Any]:
        """Check if overtrading is occurring"""
        
        self._clean_old_trades()
        
        trades_today = len(self.trades_today)
        trades_this_hour = len(self.trades_this_hour)
        
        # Check limits
        is_overtrading_day = trades_today >= self.max_trades_per_day
        is_overtrading_hour = trades_this_hour >= self.max_trades_per_hour
        
        is_overtrading = is_overtrading_day or is_overtrading_hour
        
        # Calculate severity
        severity = 0
        if is_overtrading_hour:
            severity = min(10, int((trades_this_hour / self.max_trades_per_hour) * 10))
        elif is_overtrading_day:
            severity = min(10, int((trades_today / self.max_trades_per_day) * 10))
        
        return {
            'is_overtrading': is_overtrading,
            'trades_today': trades_today,
            'trades_this_hour': trades_this_hour,
            'max_trades_per_day': self.max_trades_per_day,
            'max_trades_per_hour': self.max_trades_per_hour,
            'severity': severity,
            'action': 'STOP_TRADING' if is_overtrading else 'NONE'
        }
    
    def _clean_old_trades(self):
        """Remove old trades from tracking"""
        
        now = datetime.now()
        
        # Keep only today's trades
        self.trades_today = [t for t in self.trades_today if t.date() == now.date()]
        
        # Keep only this hour's trades
        one_hour_ago = now - timedelta(hours=1)
        self.trades_this_hour = [t for t in self.trades_this_hour if t >= one_hour_ago]


class BehaviorAnalyzer:
    """
    Analyzes trading behavior for anomalies
    """
    
    def __init__(self):
        # Trade history
        self.trade_history: deque = deque(maxlen=1000)
        
        # Consecutive tracking
        self.consecutive_wins = 0
        self.consecutive_losses = 0
        
        logger.info("Behavior Analyzer initialized")
    
    def record_trade(self, trade: Dict[str, Any]):
        """Record a trade for behavior analysis"""
        
        self.trade_history.append(trade)
        
        # Update consecutive tracking
        outcome = trade.get('outcome', 'UNKNOWN')
        
        if outcome == 'WIN':
            self.consecutive_wins += 1
            self.consecutive_losses = 0
        elif outcome == 'LOSS':
            self.consecutive_losses += 1
            self.consecutive_wins = 0
    
    def analyze_behavior(self) -> TradingBehavior:
        """Analyze trading behavior"""
        
        if len(self.trade_history) < 10:
            return self._create_default_behavior()
        
        # Convert to list for analysis
        trades = list(self.trade_history)
        
        # Calculate metrics
        trades_per_day = self._calculate_trades_per_day(trades)
        trades_per_hour = self._calculate_trades_per_hour(trades)
        
        # Win rate
        wins = sum(1 for t in trades if t.get('outcome') == 'WIN')
        losses = sum(1 for t in trades if t.get('outcome') == 'LOSS')
        win_rate = wins / (wins + losses) if (wins + losses) > 0 else 0.0
        
        # Position sizing
        position_sizes = [t.get('position_size', 0.0) for t in trades]
        avg_position_size = np.mean(position_sizes) if position_sizes else 0.0
        max_position_size = max(position_sizes) if position_sizes else 0.0
        position_size_volatility = np.std(position_sizes) if len(position_sizes) > 1 else 0.0
        
        # Hold time
        hold_times = [t.get('hold_time', 0.0) for t in trades if 'hold_time' in t]
        avg_hold_time = np.mean(hold_times) if hold_times else 0.0
        
        # Risk
        risks = [t.get('risk', 0.0) for t in trades]
        avg_risk = np.mean(risks) if risks else 0.0
        max_risk = max(risks) if risks else 0.0
        
        # Detect behavioral issues
        is_overtrading = trades_per_day > 20 or trades_per_hour > 5
        is_revenge_trading = self.consecutive_losses >= 3 and trades_per_hour > 3
        is_chasing_losses = self.consecutive_losses >= 5
        is_overconfident = self.consecutive_wins >= 5 and avg_position_size > 1.5
        
        return TradingBehavior(
            trades_per_day=trades_per_day,
            trades_per_hour=trades_per_hour,
            consecutive_wins=self.consecutive_wins,
            consecutive_losses=self.consecutive_losses,
            win_rate=win_rate,
            avg_position_size=avg_position_size,
            max_position_size=max_position_size,
            position_size_volatility=position_size_volatility,
            avg_hold_time=avg_hold_time,
            trades_in_rush_hours=0,
            avg_risk_per_trade=avg_risk,
            max_risk_taken=max_risk,
            is_overtrading=is_overtrading,
            is_revenge_trading=is_revenge_trading,
            is_chasing_losses=is_chasing_losses,
            is_overconfident=is_overconfident
        )
    
    def _calculate_trades_per_day(self, trades: List[Dict[str, Any]]) -> float:
        """Calculate average trades per day"""
        
        if not trades:
            return 0.0
        
        # Get date range
        dates = [t.get('timestamp', datetime.now()) for t in trades]
        if not dates:
            return 0.0
        
        min_date = min(dates)
        max_date = max(dates)
        
        days = (max_date - min_date).days + 1
        
        return len(trades) / days if days > 0 else 0.0
    
    def _calculate_trades_per_hour(self, trades: List[Dict[str, Any]]) -> float:
        """Calculate average trades per hour"""
        
        if not trades:
            return 0.0
        
        # Get recent trades (last 24 hours)
        now = datetime.now()
        recent = [t for t in trades if (now - t.get('timestamp', now)).total_seconds() < 86400]
        
        if not recent:
            return 0.0
        
        hours = 24
        return len(recent) / hours
    
    def _create_default_behavior(self) -> TradingBehavior:
        """Create default behavior when insufficient data"""
        
        return TradingBehavior(
            trades_per_day=0.0,
            trades_per_hour=0.0,
            consecutive_wins=0,
            consecutive_losses=0,
            win_rate=0.0,
            avg_position_size=0.0,
            max_position_size=0.0,
            position_size_volatility=0.0,
            avg_hold_time=0.0,
            trades_in_rush_hours=0,
            avg_risk_per_trade=0.0,
            max_risk_taken=0.0
        )


class SelfRegulationEngine:
    """
    Complete self-regulation system
    Monitors, controls, and governs AI trading behavior
    """
    
    def __init__(self):
        # Sub-systems
        self.drawdown_monitor = DrawdownMonitor(max_drawdown=0.20, warning_drawdown=0.10)
        self.overtrading_detector = OvertradingDetector(max_trades_per_day=20, max_trades_per_hour=5)
        self.behavior_analyzer = BehaviorAnalyzer()
        
        # Regulation rules
        self.rules: Dict[str, RegulationRule] = {}
        self._initialize_rules()
        
        # Current regulation level
        self.regulation_level = RegulationLevel.NORMAL
        
        # Actions taken
        self.actions_history: List[RegulationAction] = []
        
        # System health
        self.current_health: Optional[SystemHealth] = None
        
        # Statistics
        self.total_violations = 0
        self.total_actions_taken = 0
        
        logger.info("🛡️ Self-Regulation Engine initialized")
    
    def _initialize_rules(self):
        """Initialize regulation rules"""
        
        # Drawdown rules
        self.rules['max_drawdown'] = RegulationRule(
            rule_id='max_drawdown',
            rule_type=ViolationType.MAX_DRAWDOWN,
            threshold=0.20,
            current_value=0.0,
            action_on_breach='stop_trading',
            severity=10,
            description='Maximum drawdown limit'
        )
        
        self.rules['warning_drawdown'] = RegulationRule(
            rule_id='warning_drawdown',
            rule_type=ViolationType.MAX_DRAWDOWN,
            threshold=0.10,
            current_value=0.0,
            action_on_breach='reduce_size',
            severity=7,
            description='Warning drawdown level'
        )
        
        # Daily loss limit
        self.rules['max_daily_loss'] = RegulationRule(
            rule_id='max_daily_loss',
            rule_type=ViolationType.MAX_DAILY_LOSS,
            threshold=0.05,
            current_value=0.0,
            action_on_breach='stop_trading',
            severity=9,
            description='Maximum daily loss limit'
        )
        
        # Overtrading rules
        self.rules['max_trades_per_day'] = RegulationRule(
            rule_id='max_trades_per_day',
            rule_type=ViolationType.MAX_TRADES_PER_DAY,
            threshold=20,
            current_value=0,
            action_on_breach='stop_trading',
            severity=6,
            description='Maximum trades per day'
        )
        
        # Consecutive losses
        self.rules['max_consecutive_losses'] = RegulationRule(
            rule_id='max_consecutive_losses',
            rule_type=ViolationType.MAX_CONSECUTIVE_LOSSES,
            threshold=5,
            current_value=0,
            action_on_breach='reduce_size',
            severity=8,
            description='Maximum consecutive losses'
        )
        
        logger.info(f"Initialized {len(self.rules)} regulation rules")
    
    def check_regulation(self, market_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Comprehensive regulation check
        """
        
        # 1. Check drawdown
        current_equity = market_data.get('current_equity', 100000)
        drawdown_status = self.drawdown_monitor.update(current_equity)
        
        # 2. Check overtrading
        overtrading_status = self.overtrading_detector.check_overtrading()
        
        # 3. Analyze behavior
        behavior = self.behavior_analyzer.analyze_behavior()
        
        # 4. Update rules
        self._update_rules(drawdown_status, overtrading_status, behavior)
        
        # 5. Check for violations
        violations = self._check_violations()
        
        # 6. Determine regulation level
        self.regulation_level = self._determine_regulation_level(violations)
        
        # 7. Take actions if needed
        actions = self._take_regulatory_actions(violations)
        
        # 8. Assess system health
        health = self._assess_system_health(drawdown_status, overtrading_status, behavior, violations)
        self.current_health = health
        
        logger.info(f"Regulation check: level={self.regulation_level.value}, "
                   f"violations={len(violations)}, health={health.health_status.value}")
        
        return {
            'regulation_level': self.regulation_level.value,
            'violations': violations,
            'actions': actions,
            'health': health,
            'drawdown': drawdown_status,
            'overtrading': overtrading_status,
            'behavior': behavior,
            'trading_allowed': self.is_trading_allowed(),
            'position_size_multiplier': self.get_position_size_multiplier()
        }
    
    def record_trade(self, trade: Dict[str, Any]):
        """Record a trade for regulation tracking"""
        
        # Record in overtrading detector
        self.overtrading_detector.record_trade(trade.get('timestamp', datetime.now()))
        
        # Record in behavior analyzer
        self.behavior_analyzer.record_trade(trade)
    
    def is_trading_allowed(self) -> bool:
        """Check if trading is currently allowed"""
        
        if self.regulation_level in [RegulationLevel.EMERGENCY, RegulationLevel.SHUTDOWN]:
            return False
        
        # Check for critical violations
        for rule in self.rules.values():
            if rule.is_breached and rule.action_on_breach == 'stop_trading':
                return False
        
        return True
    
    def get_position_size_multiplier(self) -> float:
        """Get position size multiplier based on regulation level"""
        
        multipliers = {
            RegulationLevel.NORMAL: 1.0,
            RegulationLevel.CAUTIOUS: 0.7,
            RegulationLevel.RESTRICTED: 0.5,
            RegulationLevel.DEFENSIVE: 0.3,
            RegulationLevel.EMERGENCY: 0.1,
            RegulationLevel.SHUTDOWN: 0.0
        }
        
        return multipliers.get(self.regulation_level, 1.0)
    
    def _update_rules(self, drawdown_status: Dict[str, Any],
                     overtrading_status: Dict[str, Any],
                     behavior: TradingBehavior):
        """Update rule current values"""
        
        # Update drawdown rules
        self.rules['max_drawdown'].current_value = drawdown_status['current_drawdown']
        self.rules['warning_drawdown'].current_value = drawdown_status['current_drawdown']
        
        # Update overtrading rules
        self.rules['max_trades_per_day'].current_value = overtrading_status['trades_today']
        
        # Update consecutive losses
        self.rules['max_consecutive_losses'].current_value = behavior.consecutive_losses
    
    def _check_violations(self) -> List[RegulationRule]:
        """Check for rule violations"""
        
        violations = []
        
        for rule in self.rules.values():
            if rule.current_value >= rule.threshold:
                if not rule.is_breached:
                    rule.is_breached = True
                    rule.breach_count += 1
                    rule.last_breach = datetime.now()
                    self.total_violations += 1
                    
                    logger.warning(f"⚠️ Regulation violation: {rule.rule_id} "
                                 f"(current={rule.current_value:.2f}, threshold={rule.threshold:.2f})")
                
                violations.append(rule)
            else:
                rule.is_breached = False
        
        return violations
    
    def _determine_regulation_level(self, violations: List[RegulationRule]) -> RegulationLevel:
        """Determine appropriate regulation level"""
        
        if not violations:
            return RegulationLevel.NORMAL
        
        # Calculate total severity
        total_severity = sum(v.severity for v in violations)
        max_severity = max(v.severity for v in violations)
        
        # Determine level
        if max_severity >= 10 or total_severity >= 20:
            return RegulationLevel.EMERGENCY
        elif max_severity >= 9 or total_severity >= 15:
            return RegulationLevel.DEFENSIVE
        elif max_severity >= 7 or total_severity >= 10:
            return RegulationLevel.RESTRICTED
        elif max_severity >= 5 or total_severity >= 7:
            return RegulationLevel.CAUTIOUS
        else:
            return RegulationLevel.NORMAL
    
    def _take_regulatory_actions(self, violations: List[RegulationRule]) -> List[RegulationAction]:
        """Take regulatory actions based on violations"""
        
        actions = []
        
        for violation in violations:
            # Determine action
            if violation.action_on_breach == 'stop_trading':
                action = RegulationAction(
                    action_id=f"action_{self.total_actions_taken}",
                    action_type='STOP_TRADING',
                    reason=f"Violation: {violation.description}",
                    position_size_multiplier=0.0,
                    trading_allowed=False,
                    max_trades_allowed=0,
                    triggered_rules=[violation.rule_id],
                    severity=violation.severity
                )
            elif violation.action_on_breach == 'reduce_size':
                action = RegulationAction(
                    action_id=f"action_{self.total_actions_taken}",
                    action_type='REDUCE_SIZE',
                    reason=f"Violation: {violation.description}",
                    position_size_multiplier=0.5,
                    trading_allowed=True,
                    max_trades_allowed=10,
                    triggered_rules=[violation.rule_id],
                    severity=violation.severity
                )
            else:
                action = RegulationAction(
                    action_id=f"action_{self.total_actions_taken}",
                    action_type='ALERT',
                    reason=f"Violation: {violation.description}",
                    position_size_multiplier=0.8,
                    trading_allowed=True,
                    max_trades_allowed=20,
                    triggered_rules=[violation.rule_id],
                    severity=violation.severity
                )
            
            actions.append(action)
            self.actions_history.append(action)
            self.total_actions_taken += 1
            
            logger.info(f"🛡️ Regulatory action: {action.action_type} - {action.reason}")
        
        return actions
    
    def _assess_system_health(self, drawdown_status: Dict[str, Any],
                             overtrading_status: Dict[str, Any],
                             behavior: TradingBehavior,
                             violations: List[RegulationRule]) -> SystemHealth:
        """Assess overall system health"""
        
        # Calculate component health scores (0-100)
        
        # Drawdown health
        drawdown_pct = drawdown_status['current_drawdown']
        drawdown_health = max(0, 100 - (drawdown_pct * 500))  # 20% DD = 0 health
        
        # Risk health (based on consecutive losses)
        risk_health = max(0, 100 - (behavior.consecutive_losses * 20))
        
        # Performance health (based on win rate)
        performance_health = behavior.win_rate * 100
        
        # Behavioral health
        behavioral_issues = sum([
            behavior.is_overtrading,
            behavior.is_revenge_trading,
            behavior.is_chasing_losses,
            behavior.is_overconfident
        ])
        behavioral_health = max(0, 100 - (behavioral_issues * 25))
        
        # Technical health (based on violations)
        technical_health = max(0, 100 - (len(violations) * 20))
        
        # Overall health score
        health_score = (
            drawdown_health * 0.3 +
            risk_health * 0.2 +
            performance_health * 0.2 +
            behavioral_health * 0.15 +
            technical_health * 0.15
        )
        
        # Determine health status
        if health_score >= 80:
            health_status = HealthStatus.EXCELLENT
        elif health_score >= 60:
            health_status = HealthStatus.GOOD
        elif health_score >= 40:
            health_status = HealthStatus.FAIR
        elif health_score >= 20:
            health_status = HealthStatus.POOR
        else:
            health_status = HealthStatus.CRITICAL
        
        # Collect active violations
        active_violations = [v.rule_id for v in violations]
        
        # Generate warnings
        warnings = []
        if drawdown_pct > 0.10:
            warnings.append(f"Drawdown at {drawdown_pct:.1%}")
        if behavior.consecutive_losses >= 3:
            warnings.append(f"{behavior.consecutive_losses} consecutive losses")
        if behavior.is_overtrading:
            warnings.append("Overtrading detected")
        if overtrading_status['is_overtrading']:
            warnings.append(f"Trade limit reached: {overtrading_status['trades_today']}/{overtrading_status['max_trades_per_day']}")
        
        # Generate recommendations
        recommendations = []
        if drawdown_pct > 0.15:
            recommendations.append("Stop trading until drawdown recovers")
        elif drawdown_pct > 0.10:
            recommendations.append("Reduce position sizes by 50%")
        
        if behavior.consecutive_losses >= 5:
            recommendations.append("Take a break - possible losing streak")
        elif behavior.consecutive_losses >= 3:
            recommendations.append("Review strategy - multiple losses detected")
        
        if behavior.is_overtrading:
            recommendations.append("Reduce trading frequency")
        
        if not recommendations:
            recommendations.append("System operating normally")
        
        return SystemHealth(
            health_status=health_status,
            health_score=health_score,
            drawdown_health=drawdown_health,
            risk_health=risk_health,
            performance_health=performance_health,
            behavioral_health=behavioral_health,
            technical_health=technical_health,
            active_violations=active_violations,
            warnings=warnings,
            recommended_actions=recommendations
        )
    
    def get_regulation_report(self) -> Dict[str, Any]:
        """Get comprehensive regulation report"""
        
        return {
            'regulation_level': self.regulation_level.value,
            'trading_allowed': self.is_trading_allowed(),
            'position_size_multiplier': self.get_position_size_multiplier(),
            'current_health': self.current_health,
            'total_violations': self.total_violations,
            'total_actions_taken': self.total_actions_taken,
            'active_rules': len([r for r in self.rules.values() if r.is_breached]),
            'recent_actions': self.actions_history[-5:] if self.actions_history else []
        }


# Example usage
if __name__ == "__main__":
    # Initialize self-regulation engine
    engine = SelfRegulationEngine()
    
    print("="*80)
    logger.info("🛡️ SELF-REGULATION ENGINE")
    print("="*80)
    
    # Simulate trading scenario
    market_data = {
        'current_equity': 95000  # Started with 100k, now at 95k (5% drawdown)
    }
    
    # Check regulation
    logger.info("\n1. Initial regulation check...")
    result = engine.check_regulation(market_data)
    
    logger.info(f"\nRegulation Level: {result['regulation_level'].upper()}")
    logger.info(f"Trading Allowed: {result['trading_allowed']}")
    logger.info(f"Position Size Multiplier: {result['position_size_multiplier']:.2f}x")
    
    health = result['health']
    logger.info(f"\nSystem Health: {health.health_status.value.upper()} ({health.health_score:.1f}/100)")
    logger.info(f"  Drawdown Health: {health.drawdown_health:.1f}")
    logger.info(f"  Risk Health: {health.risk_health:.1f}")
    logger.info(f"  Performance Health: {health.performance_health:.1f}")
    logger.info(f"  Behavioral Health: {health.behavioral_health:.1f}")
    
    if health.warnings:
        logger.info(f"\nWarnings:")
        for warning in health.warnings:
            logger.info(f"  ⚠️ {warning}")
    
    if health.recommended_actions:
        logger.info(f"\nRecommendations:")
        for rec in health.recommended_actions:
            logger.info(f"  • {rec}")
    
    # Simulate some trades
    logger.info("\n2. Simulating trades...")
    
    for i in range(25):  # Simulate 25 trades (will trigger overtrading)
        trade = {
            'timestamp': datetime.now(),
            'outcome': 'WIN' if i % 3 == 0 else 'LOSS',
            'position_size': 1.0,
            'risk': 0.02
        }
        engine.record_trade(trade)
    
    # Check regulation again
    logger.info("\n3. Regulation check after 25 trades...")
    result = engine.check_regulation(market_data)
    
    logger.info(f"\nRegulation Level: {result['regulation_level'].upper()}")
    logger.info(f"Trading Allowed: {result['trading_allowed']}")
    
    if result['violations']:
        logger.info(f"\nViolations Detected:")
        for violation in result['violations']:
            logger.info(f"  ⚠️ {violation.description}: {violation.current_value:.2f} >= {violation.threshold:.2f}")
    
    if result['actions']:
        logger.info(f"\nRegulatory Actions Taken:")
        for action in result['actions']:
            logger.info(f"  🛡️ {action.action_type}: {action.reason}")
    
    # Simulate critical drawdown
    logger.info("\n4. Simulating critical drawdown...")
    market_data['current_equity'] = 75000  # 25% drawdown
    
    result = engine.check_regulation(market_data)
    
    logger.info(f"\nRegulation Level: {result['regulation_level'].upper()}")
    logger.info(f"Trading Allowed: {result['trading_allowed']}")
    logger.info(f"Position Size Multiplier: {result['position_size_multiplier']:.2f}x")
    
    # Get final report
    logger.info("\n5. Final Regulation Report:")
    report = engine.get_regulation_report()
    
    logger.info(f"\nTotal Violations: {report['total_violations']}")
    logger.info(f"Total Actions Taken: {report['total_actions_taken']}")
    logger.info(f"Active Rules Breached: {report['active_rules']}")
    
    print("\n" + "="*80)
    logger.info("✅ SELF-REGULATION ENGINE OPERATIONAL")
    print("="*80)
