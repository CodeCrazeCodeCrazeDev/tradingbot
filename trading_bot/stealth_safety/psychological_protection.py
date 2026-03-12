"""
Psychological Protection System
===============================

Protects the HUMAN operator from:
1. Psychological pressure from trading
2. Stress from AI complexity
3. Anxiety from responsibility
4. Overwhelm from information
5. Fear of losing control

LEGAL RESPONSIBILITY FALLS ON YOU - This system helps you manage that.

PRINCIPLE: The human must remain calm, informed, and in control.
"""

import logging
from typing import Any, Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from collections import deque

logger = logging.getLogger(__name__)


class StressLevel(Enum):
    """Human stress levels"""
    CALM = "calm"
    MILD = "mild"
    MODERATE = "moderate"
    HIGH = "high"
    CRITICAL = "critical"


class TradingMood(Enum):
    """Trading environment mood"""
    PEACEFUL = "peaceful"
    NORMAL = "normal"
    TENSE = "tense"
    STRESSFUL = "stressful"
    CHAOTIC = "chaotic"


@dataclass
class StressIndicator:
    """Indicator of potential stress"""
    indicator_type: str
    value: float
    threshold: float
    is_concerning: bool
    recommendation: str


class CalmTradingPolicy:
    """
    Enforces calm, measured trading.
    
    PREVENTS:
    1. Panic trading
    2. Revenge trading
    3. FOMO-driven decisions
    4. Overtrading
    5. Emotional reactions
    
    ENFORCES:
    - Minimum time between trades
    - Maximum trades per day
    - Cooling off after losses
    - Gradual position building
    - Measured responses
    """
    
    # Calm trading limits
    MIN_TIME_BETWEEN_TRADES_MINUTES = 5
    MAX_TRADES_PER_HOUR = 5
    MAX_TRADES_PER_DAY = 20
    COOLING_OFF_AFTER_LOSS_MINUTES = 15
    MAX_CONSECUTIVE_TRADES = 3
    
    def __init__(self, config: Optional[Dict] = None):
        try:
            self.config = config or {}
        
            # Trading history
            self.trades_today: List[Dict] = []
            self.last_trade_time: Optional[datetime] = None
            self.consecutive_trades = 0
            self.last_loss_time: Optional[datetime] = None
        
            # State
            self.is_cooling_off = False
            self.trading_mood = TradingMood.PEACEFUL
        
            logger.info("CalmTradingPolicy initialized - CALM TRADING ENFORCED")
        except Exception as e:
            logger.error(f"Error in __init__: {e}")
            raise
    
    def can_trade(self) -> Tuple[bool, str, int]:
        """
        Check if trading is allowed under calm policy.
        
        Returns:
            Tuple of (can_trade, reason, wait_seconds)
        """
        try:
            now = datetime.now()
        
            # Check cooling off period
            if self.is_cooling_off and self.last_loss_time:
                cooling_end = self.last_loss_time + timedelta(minutes=self.COOLING_OFF_AFTER_LOSS_MINUTES)
                if now < cooling_end:
                    wait = int((cooling_end - now).total_seconds())
                    return False, "Cooling off after loss - take a breath", wait
                else:
                    self.is_cooling_off = False
        
            # Check minimum time between trades
            if self.last_trade_time:
                min_next = self.last_trade_time + timedelta(minutes=self.MIN_TIME_BETWEEN_TRADES_MINUTES)
                if now < min_next:
                    wait = int((min_next - now).total_seconds())
                    return False, "Too soon since last trade - patience", wait
        
            # Check hourly limit
            hour_ago = now - timedelta(hours=1)
            trades_this_hour = [t for t in self.trades_today if t['time'] > hour_ago]
            if len(trades_this_hour) >= self.MAX_TRADES_PER_HOUR:
                return False, "Hourly trade limit reached - slow down", 3600
        
            # Check daily limit
            if len(self.trades_today) >= self.MAX_TRADES_PER_DAY:
                return False, "Daily trade limit reached - enough for today", 0
        
            # Check consecutive trades
            if self.consecutive_trades >= self.MAX_CONSECUTIVE_TRADES:
                return False, "Too many consecutive trades - take a break", 300
        
            return True, "Trading allowed - stay calm", 0
        except Exception as e:
            logger.error(f"Error in can_trade: {e}")
            raise
    
    def record_trade(self, was_loss: bool = False):
        """Record a trade"""
        try:
            now = datetime.now()
        
            self.trades_today.append({
                'time': now,
                'was_loss': was_loss
            })
        
            self.last_trade_time = now
            self.consecutive_trades += 1
        
            if was_loss:
                self.last_loss_time = now
                self.is_cooling_off = True
                self.consecutive_trades = 0  # Reset after loss
                logger.info("Loss recorded - cooling off period started")
        except Exception as e:
            logger.error(f"Error in record_trade: {e}")
            raise
    
    def record_break(self):
        """Record that human took a break"""
        try:
            self.consecutive_trades = 0
            logger.info("Break recorded - consecutive trade counter reset")
        except Exception as e:
            logger.error(f"Error in record_break: {e}")
            raise
    
    def reset_daily(self):
        """Reset daily counters"""
        try:
            self.trades_today = []
            self.consecutive_trades = 0
            self.is_cooling_off = False
        except Exception as e:
            logger.error(f"Error in reset_daily: {e}")
            raise
    
    def get_trading_mood(self) -> TradingMood:
        """Assess current trading mood"""
        try:
            trades_count = len(self.trades_today)
        
            if trades_count == 0:
                return TradingMood.PEACEFUL
            elif trades_count < 5:
                return TradingMood.NORMAL
            elif trades_count < 10:
                return TradingMood.TENSE
            elif trades_count < 15:
                return TradingMood.STRESSFUL
            else:
                return TradingMood.CHAOTIC
        except Exception as e:
            logger.error(f"Error in get_trading_mood: {e}")
            raise
    
    def get_calm_recommendation(self) -> str:
        """Get recommendation for staying calm"""
        try:
            mood = self.get_trading_mood()
        
            recommendations = {
                TradingMood.PEACEFUL: "Perfect conditions. Trade mindfully.",
                TradingMood.NORMAL: "Good pace. Stay focused.",
                TradingMood.TENSE: "Consider slowing down. Quality over quantity.",
                TradingMood.STRESSFUL: "Take a break. Step away from the screen.",
                TradingMood.CHAOTIC: "STOP. You're overtrading. Walk away."
            }
        
            return recommendations.get(mood, "Stay calm.")
        except Exception as e:
            logger.error(f"Error in get_calm_recommendation: {e}")
            raise
    
    def get_status(self) -> Dict[str, Any]:
        """Get calm trading status"""
        try:
            can_trade, reason, wait = self.can_trade()
        
            return {
                'can_trade': can_trade,
                'reason': reason,
                'wait_seconds': wait,
                'trades_today': len(self.trades_today),
                'consecutive_trades': self.consecutive_trades,
                'is_cooling_off': self.is_cooling_off,
                'trading_mood': self.get_trading_mood().value,
                'recommendation': self.get_calm_recommendation()
            }
        except Exception as e:
            logger.error(f"Error in get_status: {e}")
            raise


class HumanStressMonitor:
    """
    Monitors indicators of human stress.
    
    STRESS INDICATORS:
    1. Trading frequency (overtrading)
    2. Loss patterns (revenge trading)
    3. Time of day (fatigue)
    4. Session length (burnout)
    5. Decision speed (panic)
    
    RESPONSES:
    - Suggest breaks
    - Reduce position sizes
    - Simplify information
    - Encourage stepping away
    - Automatic safeguards
    """
    
    # Stress thresholds
    MAX_SESSION_HOURS = 4
    MAX_LOSSES_BEFORE_BREAK = 3
    FATIGUE_HOURS = [0, 1, 2, 3, 4, 5, 23]  # Late night/early morning
    MIN_DECISION_TIME_SECONDS = 10
    
    def __init__(self, config: Optional[Dict] = None):
        try:
            self.config = config or {}
        
            # Session tracking
            self.session_start: Optional[datetime] = None
            self.consecutive_losses = 0
            self.decision_times: deque = deque(maxlen=20)
        
            # Stress state
            self.stress_level = StressLevel.CALM
            self.stress_indicators: List[StressIndicator] = []
        
            logger.info("HumanStressMonitor initialized")
        except Exception as e:
            logger.error(f"Error in __init__: {e}")
            raise
    
    def start_session(self):
        """Start a trading session"""
        try:
            self.session_start = datetime.now()
            self.consecutive_losses = 0
            self.decision_times.clear()
            logger.info("Trading session started")
        except Exception as e:
            logger.error(f"Error in start_session: {e}")
            raise
    
    def record_decision(self, decision_time_seconds: float):
        """Record time taken for a decision"""
        try:
            self.decision_times.append(decision_time_seconds)
        except Exception as e:
            logger.error(f"Error in record_decision: {e}")
            raise
    
    def record_trade_result(self, was_loss: bool):
        """Record a trade result"""
        try:
            if was_loss:
                self.consecutive_losses += 1
            else:
                self.consecutive_losses = 0
        except Exception as e:
            logger.error(f"Error in record_trade_result: {e}")
            raise
    
    def assess_stress(self) -> Tuple[StressLevel, List[StressIndicator]]:
        """
        Assess current stress level.
        
        Returns:
            Tuple of (stress_level, indicators)
        """
        try:
            indicators = []
            stress_score = 0
        
            # Check session length
            if self.session_start:
                session_hours = (datetime.now() - self.session_start).total_seconds() / 3600
            
                if session_hours > self.MAX_SESSION_HOURS:
                    indicators.append(StressIndicator(
                        indicator_type="session_length",
                        value=session_hours,
                        threshold=self.MAX_SESSION_HOURS,
                        is_concerning=True,
                        recommendation="Take a break - you've been trading too long"
                    ))
                    stress_score += 2
        
            # Check consecutive losses
            if self.consecutive_losses >= self.MAX_LOSSES_BEFORE_BREAK:
                indicators.append(StressIndicator(
                    indicator_type="consecutive_losses",
                    value=self.consecutive_losses,
                    threshold=self.MAX_LOSSES_BEFORE_BREAK,
                    is_concerning=True,
                    recommendation="Step away - losses can trigger revenge trading"
                ))
                stress_score += 3
        
            # Check time of day
            current_hour = datetime.now().hour
            if current_hour in self.FATIGUE_HOURS:
                indicators.append(StressIndicator(
                    indicator_type="fatigue_hours",
                    value=current_hour,
                    threshold=0,
                    is_concerning=True,
                    recommendation="Trading late/early - judgment may be impaired"
                ))
                stress_score += 2
        
            # Check decision speed
            if self.decision_times:
                avg_decision_time = sum(self.decision_times) / len(self.decision_times)
                if avg_decision_time < self.MIN_DECISION_TIME_SECONDS:
                    indicators.append(StressIndicator(
                        indicator_type="decision_speed",
                        value=avg_decision_time,
                        threshold=self.MIN_DECISION_TIME_SECONDS,
                        is_concerning=True,
                        recommendation="Slow down - quick decisions may be impulsive"
                    ))
                    stress_score += 2
        
            # Determine stress level
            if stress_score == 0:
                self.stress_level = StressLevel.CALM
            elif stress_score <= 2:
                self.stress_level = StressLevel.MILD
            elif stress_score <= 4:
                self.stress_level = StressLevel.MODERATE
            elif stress_score <= 6:
                self.stress_level = StressLevel.HIGH
            else:
                self.stress_level = StressLevel.CRITICAL
        
            self.stress_indicators = indicators
        
            return self.stress_level, indicators
        except Exception as e:
            logger.error(f"Error in assess_stress: {e}")
            raise
    
    def should_reduce_trading(self) -> Tuple[bool, str]:
        """Check if trading should be reduced due to stress"""
        try:
            level, indicators = self.assess_stress()
        
            if level in [StressLevel.HIGH, StressLevel.CRITICAL]:
                reasons = [i.recommendation for i in indicators if i.is_concerning]
                return True, "; ".join(reasons)
        
            return False, "Stress levels acceptable"
        except Exception as e:
            logger.error(f"Error in should_reduce_trading: {e}")
            raise
    
    def get_position_size_multiplier(self) -> float:
        """Get position size multiplier based on stress"""
        try:
            multipliers = {
                StressLevel.CALM: 1.0,
                StressLevel.MILD: 0.9,
                StressLevel.MODERATE: 0.7,
                StressLevel.HIGH: 0.5,
                StressLevel.CRITICAL: 0.0
            }
            return multipliers.get(self.stress_level, 1.0)
        except Exception as e:
            logger.error(f"Error in get_position_size_multiplier: {e}")
            raise
    
    def get_status(self) -> Dict[str, Any]:
        """Get stress monitoring status"""
        try:
            level, indicators = self.assess_stress()
        
            return {
                'stress_level': level.value,
                'position_multiplier': self.get_position_size_multiplier(),
                'indicators': [
                    {
                        'type': i.indicator_type,
                        'concerning': i.is_concerning,
                        'recommendation': i.recommendation
                    }
                    for i in indicators
                ],
                'consecutive_losses': self.consecutive_losses,
                'session_active': self.session_start is not None
            }
        except Exception as e:
            logger.error(f"Error in get_status: {e}")
            raise


class ResponsibilityClarity:
    """
    Maintains clarity about legal and financial responsibility.
    
    LEGAL RESPONSIBILITY FALLS ON YOU:
    1. The AI is a tool - you are responsible
    2. All trades are your decisions
    3. Losses are your losses
    4. Regulatory compliance is your duty
    5. Tax obligations are yours
    
    THIS SYSTEM:
    - Reminds you of responsibility
    - Documents your decisions
    - Creates audit trails
    - Provides disclaimers
    - Maintains transparency
    """
    
    # Responsibility reminders
    RESPONSIBILITY_STATEMENTS = [
        "You are legally responsible for all trading decisions.",
        "The AI provides suggestions - you make the final call.",
        "All profits and losses are yours.",
        "Regulatory compliance is your responsibility.",
        "Tax obligations from trading are yours to fulfill.",
        "You can stop the system at any time.",
        "You are in control - the AI is just a tool."
    ]
    
    def __init__(self, config: Optional[Dict] = None):
        try:
            self.config = config or {}
        
            # Acknowledgments
            self.acknowledgments: List[Dict] = []
            self.last_reminder: Optional[datetime] = None
        
            # Reminder frequency
            self.reminder_interval_hours = config.get('reminder_hours', 4)
        
            logger.info("ResponsibilityClarity initialized")
        except Exception as e:
            logger.error(f"Error in __init__: {e}")
            raise
    
    def get_responsibility_reminder(self) -> str:
        """Get a responsibility reminder"""
        try:
            import random
            reminder = random.choice(self.RESPONSIBILITY_STATEMENTS)
            self.last_reminder = datetime.now()
            return reminder
        except Exception as e:
            logger.error(f"Error in get_responsibility_reminder: {e}")
            raise
    
    def should_show_reminder(self) -> bool:
        """Check if a reminder should be shown"""
        try:
            if not self.last_reminder:
                return True
        
            hours_since = (datetime.now() - self.last_reminder).total_seconds() / 3600
            return hours_since >= self.reminder_interval_hours
        except Exception as e:
            logger.error(f"Error in should_show_reminder: {e}")
            raise
    
    def acknowledge_responsibility(self, acknowledged_by: str):
        """Record acknowledgment of responsibility"""
        try:
            self.acknowledgments.append({
                'acknowledged_by': acknowledged_by,
                'timestamp': datetime.now().isoformat(),
                'statement': "I understand that I am legally responsible for all trading decisions."
            })
            logger.info(f"Responsibility acknowledged by {acknowledged_by}")
        except Exception as e:
            logger.error(f"Error in acknowledge_responsibility: {e}")
            raise
    
    def get_disclaimer(self) -> str:
        """Get full disclaimer text"""
        return """
TRADING DISCLAIMER AND RESPONSIBILITY NOTICE

By using this AI trading system, you acknowledge and agree that:

1. LEGAL RESPONSIBILITY: You are solely responsible for all trading 
   decisions made using this system. The AI provides analysis and 
   suggestions, but all final decisions are yours.

2. FINANCIAL RISK: Trading involves substantial risk of loss. You 
   may lose some or all of your invested capital. Only trade with 
   money you can afford to lose.

3. NO GUARANTEES: Past performance does not guarantee future results.
   The AI's suggestions are not financial advice and should not be 
   treated as such.

4. REGULATORY COMPLIANCE: You are responsible for ensuring your 
   trading activities comply with all applicable laws and regulations
   in your jurisdiction.

5. TAX OBLIGATIONS: You are responsible for reporting and paying 
   any taxes owed on trading profits.

6. SYSTEM LIMITATIONS: The AI system may have bugs, make errors, 
   or behave unexpectedly. You should monitor all trading activity.

7. CONTROL: You maintain full control over the system and can 
   stop it at any time. The AI cannot override your decisions.

By continuing to use this system, you confirm that you have read,
understood, and accepted these terms.
"""
    
    def get_status(self) -> Dict[str, Any]:
        """Get responsibility clarity status"""
        return {
            'acknowledgments_count': len(self.acknowledgments),
            'last_acknowledgment': self.acknowledgments[-1] if self.acknowledgments else None,
            'reminder_due': self.should_show_reminder(),
            'last_reminder': self.last_reminder.isoformat() if self.last_reminder else None
        }


class UnderstandingPreserver:
    """
    Ensures the human always understands what the AI is doing.
    
    THE AI MAY OUTGROW YOUR UNDERSTANDING IF:
    1. It becomes too complex
    2. It uses unexplainable methods
    3. It develops emergent behaviors
    4. It operates too fast to follow
    5. It makes decisions you can't verify
    
    THIS SYSTEM:
    - Simplifies explanations
    - Provides summaries
    - Highlights key decisions
    - Alerts on complexity
    - Maintains human comprehension
    """
    
    # Understanding thresholds
    MAX_EXPLANATION_LENGTH = 500  # Characters
    MAX_ACTIVE_COMPONENTS = 10
    MAX_DECISION_FACTORS = 5
    
    def __init__(self, config: Optional[Dict] = None):
        try:
            self.config = config or {}
        
            # Understanding tracking
            self.complexity_warnings: List[Dict] = []
            self.simplification_requests: int = 0
        
            logger.info("UnderstandingPreserver initialized")
        except Exception as e:
            logger.error(f"Error in __init__: {e}")
            raise
    
    def simplify_explanation(self, complex_explanation: str) -> str:
        """Simplify a complex explanation for human understanding"""
        # If already simple, return as is
        try:
            if len(complex_explanation) <= self.MAX_EXPLANATION_LENGTH:
                return complex_explanation
        
            # Truncate and add summary indicator
            simplified = complex_explanation[:self.MAX_EXPLANATION_LENGTH - 50]
            simplified += "\n\n[Simplified - ask for full details if needed]"
        
            self.simplification_requests += 1
        
            return simplified
        except Exception as e:
            logger.error(f"Error in simplify_explanation: {e}")
            raise
    
    def create_summary(self, details: Dict[str, Any]) -> str:
        """Create a human-readable summary"""
        try:
            lines = ["=== SUMMARY ===", ""]
        
            # Key metrics only
            if 'decision' in details:
                lines.append(f"Decision: {details['decision']}")
        
            if 'confidence' in details:
                lines.append(f"Confidence: {details['confidence']*100:.0f}%")
        
            if 'risk' in details:
                lines.append(f"Risk Level: {details['risk']}")
        
            if 'action' in details:
                lines.append(f"Action: {details['action']}")
        
            lines.append("")
            lines.append("Ask for details if you need more information.")
        
            return "\n".join(lines)
        except Exception as e:
            logger.error(f"Error in create_summary: {e}")
            raise
    
    def check_understandability(
        self,
        num_components: int,
        num_decision_factors: int,
        explanation_length: int
    ) -> Tuple[bool, str]:
        """
        Check if the system is still understandable.
        
        Returns:
            Tuple of (is_understandable, message)
        """
        try:
            issues = []
        
            if num_components > self.MAX_ACTIVE_COMPONENTS:
                issues.append(f"Too many components ({num_components})")
        
            if num_decision_factors > self.MAX_DECISION_FACTORS:
                issues.append(f"Too many decision factors ({num_decision_factors})")
        
            if explanation_length > self.MAX_EXPLANATION_LENGTH * 2:
                issues.append("Explanations too complex")
        
            if issues:
                warning = {
                    'issues': issues,
                    'timestamp': datetime.now().isoformat()
                }
                self.complexity_warnings.append(warning)
            
                return False, f"Understanding at risk: {'; '.join(issues)}"
        
            return True, "System remains understandable"
        except Exception as e:
            logger.error(f"Error in check_understandability: {e}")
            raise
    
    def get_understanding_score(self) -> float:
        """
        Get understanding score (0-1).
        
        1.0 = Fully understandable
        0.0 = Too complex to understand
        """
        # Based on recent warnings
        try:
            recent_warnings = [
                w for w in self.complexity_warnings
                if datetime.fromisoformat(w['timestamp']) > datetime.now() - timedelta(hours=1)
            ]
        
            if not recent_warnings:
                return 1.0
        
            # Reduce score based on warnings
            return max(0.0, 1.0 - (len(recent_warnings) * 0.2))
        except Exception as e:
            logger.error(f"Error in get_understanding_score: {e}")
            raise
    
    def get_status(self) -> Dict[str, Any]:
        """Get understanding preservation status"""
        return {
            'understanding_score': self.get_understanding_score(),
            'complexity_warnings': len(self.complexity_warnings),
            'simplification_requests': self.simplification_requests,
            'is_understandable': self.get_understanding_score() > 0.5
        }
