"""
Central Bank Policy Tracker - Dedicated CB Monitoring

Tracks central bank policy divergence and forward guidance for:
- Fed, ECB, BOJ, BOE, SNB, RBA, BOC, RBNZ
- Policy divergence scoring
- Forward guidance NLP analysis
- Rate decision impact prediction
- Monetary policy regime detection

Features:
- Real-time policy tracking
- Hawkish/Dovish sentiment scoring
- Rate path expectations
- Currency impact prediction
"""

import logging
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple
import numpy as np
from collections import deque
import re

logger = logging.getLogger(__name__)


class CentralBank(Enum):
    """Major central banks"""
    FED = "fed"          # Federal Reserve (USD)
    ECB = "ecb"          # European Central Bank (EUR)
    BOJ = "boj"          # Bank of Japan (JPY)
    BOE = "boe"          # Bank of England (GBP)
    SNB = "snb"          # Swiss National Bank (CHF)
    RBA = "rba"          # Reserve Bank of Australia (AUD)
    BOC = "boc"          # Bank of Canada (CAD)
    RBNZ = "rbnz"        # Reserve Bank of New Zealand (NZD)
    PBOC = "pboc"        # People's Bank of China (CNY)


class PolicyStance(Enum):
    """Monetary policy stance"""
    VERY_HAWKISH = "very_hawkish"
    HAWKISH = "hawkish"
    NEUTRAL = "neutral"
    DOVISH = "dovish"
    VERY_DOVISH = "very_dovish"


class PolicyAction(Enum):
    """Policy actions"""
    RATE_HIKE = "rate_hike"
    RATE_CUT = "rate_cut"
    HOLD = "hold"
    QE_INCREASE = "qe_increase"
    QE_DECREASE = "qe_decrease"
    QT_START = "qt_start"
    QT_END = "qt_end"
    FORWARD_GUIDANCE_HAWKISH = "forward_guidance_hawkish"
    FORWARD_GUIDANCE_DOVISH = "forward_guidance_dovish"


@dataclass
class PolicyDecision:
    """Central bank policy decision"""
    bank: CentralBank
    timestamp: datetime
    action: PolicyAction
    rate_change_bps: int  # Basis points
    new_rate: float
    statement_summary: str
    stance: PolicyStance
    hawkish_score: float  # -1 (dovish) to +1 (hawkish)
    surprise_factor: float  # How much it deviated from expectations
    
    def to_dict(self) -> Dict[str, Any]:
        """
        to_dict function.

    Auto-documented by QwenCodeMender.
        """
        return {
            'bank': self.bank.value,
            'timestamp': self.timestamp.isoformat(),
            'action': self.action.value,
            'rate_change_bps': self.rate_change_bps,
            'new_rate': self.new_rate,
            'statement_summary': self.statement_summary,
            'stance': self.stance.value,
            'hawkish_score': self.hawkish_score,
            'surprise_factor': self.surprise_factor
        }


@dataclass
class PolicyDivergence:
    """Policy divergence between two central banks"""
    bank1: CentralBank
    bank2: CentralBank
    rate_differential: float  # bank1 rate - bank2 rate
    stance_differential: float  # bank1 hawkish score - bank2 hawkish score
    divergence_score: float  # Combined divergence metric
    currency_pair: str
    expected_direction: str  # Which currency should strengthen
    confidence: float
    
    def to_dict(self) -> Dict[str, Any]:
        """
        to_dict function.

    Auto-documented by QwenCodeMender.
        """
        return {
            'bank1': self.bank1.value,
            'bank2': self.bank2.value,
            'rate_differential': self.rate_differential,
            'stance_differential': self.stance_differential,
            'divergence_score': self.divergence_score,
            'currency_pair': self.currency_pair,
            'expected_direction': self.expected_direction,
            'confidence': self.confidence
        }


@dataclass
class RateExpectation:
    """Market rate expectations"""
    bank: CentralBank
    current_rate: float
    expected_rate_3m: float
    expected_rate_6m: float
    expected_rate_12m: float
    probability_hike_next: float
    probability_cut_next: float
    terminal_rate: float
    
    def to_dict(self) -> Dict[str, Any]:
        """
        to_dict function.

    Auto-documented by QwenCodeMender.
        """
        return {
            'bank': self.bank.value,
            'current_rate': self.current_rate,
            'expected_rate_3m': self.expected_rate_3m,
            'expected_rate_6m': self.expected_rate_6m,
            'expected_rate_12m': self.expected_rate_12m,
            'probability_hike_next': self.probability_hike_next,
            'probability_cut_next': self.probability_cut_next,
            'terminal_rate': self.terminal_rate
        }


class StatementAnalyzer:
    """
    NLP analyzer for central bank statements
    
    Extracts hawkish/dovish sentiment from policy statements
    """
    
    # Hawkish keywords and phrases
    HAWKISH_TERMS = [
        'inflation', 'price stability', 'tightening', 'restrictive',
        'vigilant', 'determined', 'committed', 'strong', 'robust',
        'overheating', 'above target', 'upside risks', 'rate hike',
        'normalize', 'reduce accommodation', 'balance sheet reduction',
        'labor market tight', 'wage pressures', 'persistent inflation'
    ]
    
    # Dovish keywords and phrases
    DOVISH_TERMS = [
        'accommodative', 'supportive', 'patient', 'gradual',
        'downside risks', 'uncertainty', 'moderate', 'subdued',
        'below target', 'slack', 'weakness', 'rate cut',
        'stimulus', 'quantitative easing', 'asset purchases',
        'economic headwinds', 'global slowdown', 'disinflation'
    ]
    
    # Neutral/conditional terms
    NEUTRAL_TERMS = [
        'data dependent', 'monitor', 'assess', 'evaluate',
        'balanced', 'appropriate', 'meeting by meeting'
    ]
    
    def analyze_statement(self, statement: str) -> Tuple[float, PolicyStance, str]:
        """
        Analyze central bank statement
        
        Returns: (hawkish_score, stance, summary)
        """
        statement_lower = statement.lower()
        
        # Count term occurrences
        hawkish_count = sum(
            1 for term in self.HAWKISH_TERMS 
            if term in statement_lower
        )
        dovish_count = sum(
            1 for term in self.DOVISH_TERMS 
            if term in statement_lower
        )
        neutral_count = sum(
            1 for term in self.NEUTRAL_TERMS 
            if term in statement_lower
        )
        
        # Calculate score
        total = hawkish_count + dovish_count + 1  # +1 to avoid division by zero
        hawkish_score = (hawkish_count - dovish_count) / total
        
        # Adjust for neutral terms (reduce confidence)
        if neutral_count > 2:
            hawkish_score *= 0.7
        
        # Determine stance
        if hawkish_score > 0.5:
            stance = PolicyStance.VERY_HAWKISH
        elif hawkish_score > 0.2:
            stance = PolicyStance.HAWKISH
        elif hawkish_score < -0.5:
            stance = PolicyStance.VERY_DOVISH
        elif hawkish_score < -0.2:
            stance = PolicyStance.DOVISH
        else:
            stance = PolicyStance.NEUTRAL
        
        # Generate summary
        summary = self._generate_summary(hawkish_count, dovish_count, neutral_count, stance)
        
        return hawkish_score, stance, summary
    
    def _generate_summary(
        self,
        hawkish: int,
        dovish: int,
        neutral: int,
        stance: PolicyStance
    ) -> str:
        """Generate summary of statement analysis"""
        parts = []
        
        if stance in [PolicyStance.VERY_HAWKISH, PolicyStance.HAWKISH]:
            parts.append(f"Hawkish tone detected ({hawkish} hawkish vs {dovish} dovish terms)")
        elif stance in [PolicyStance.VERY_DOVISH, PolicyStance.DOVISH]:
            parts.append(f"Dovish tone detected ({dovish} dovish vs {hawkish} hawkish terms)")
        else:
            parts.append("Neutral/balanced tone")
        
        if neutral > 2:
            parts.append("High data-dependency indicated")
        
        return ". ".join(parts)


class CentralBankTracker:
    """
    Central Bank Policy Tracker
    
    Monitors central bank policies and calculates divergence
    for currency trading signals.
    """
    
    # Currency mappings
    BANK_CURRENCY = {
        CentralBank.FED: 'USD',
        CentralBank.ECB: 'EUR',
        CentralBank.BOJ: 'JPY',
        CentralBank.BOE: 'GBP',
        CentralBank.SNB: 'CHF',
        CentralBank.RBA: 'AUD',
        CentralBank.BOC: 'CAD',
        CentralBank.RBNZ: 'NZD',
        CentralBank.PBOC: 'CNY',
    }
    
    # Meeting schedules (approximate days between meetings)
    MEETING_FREQUENCY = {
        CentralBank.FED: 42,   # ~6 weeks
        CentralBank.ECB: 42,
        CentralBank.BOJ: 42,
        CentralBank.BOE: 42,
        CentralBank.SNB: 90,   # Quarterly
        CentralBank.RBA: 30,   # Monthly (except Jan)
        CentralBank.BOC: 42,
        CentralBank.RBNZ: 42,
        CentralBank.PBOC: 30,
    }
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        
        # Current rates
        self.current_rates: Dict[CentralBank, float] = {
            CentralBank.FED: 5.50,
            CentralBank.ECB: 4.50,
            CentralBank.BOJ: -0.10,
            CentralBank.BOE: 5.25,
            CentralBank.SNB: 1.75,
            CentralBank.RBA: 4.35,
            CentralBank.BOC: 5.00,
            CentralBank.RBNZ: 5.50,
            CentralBank.PBOC: 3.45,
        }
        
        # Current stances
        self.current_stances: Dict[CentralBank, float] = {
            bank: 0.0 for bank in CentralBank
        }
        
        # Decision history
        self.decisions: Dict[CentralBank, deque] = {
            bank: deque(maxlen=50) for bank in CentralBank
        }
        
        # Rate expectations
        self.expectations: Dict[CentralBank, RateExpectation] = {}
        
        # Statement analyzer
        self.analyzer = StatementAnalyzer()
        
        # Last update times
        self.last_updates: Dict[CentralBank, datetime] = {}
        
        logger.info("CentralBankTracker initialized")
    
    def update_rate(
        self,
        bank: CentralBank,
        new_rate: float,
        statement: str = "",
        expected_rate: Optional[float] = None
    ) -> PolicyDecision:
        """
        Update central bank rate and analyze decision
        """
        old_rate = self.current_rates.get(bank, new_rate)
        rate_change_bps = int((new_rate - old_rate) * 100)
        
        # Determine action
        if rate_change_bps > 0:
            action = PolicyAction.RATE_HIKE
        elif rate_change_bps < 0:
            action = PolicyAction.RATE_CUT
        else:
            action = PolicyAction.HOLD
        
        # Analyze statement
        if statement:
            hawkish_score, stance, summary = self.analyzer.analyze_statement(statement)
        else:
            hawkish_score = 0.0
            stance = PolicyStance.NEUTRAL
            summary = "No statement provided"
        
        # Calculate surprise factor
        if expected_rate is not None:
            surprise = abs(new_rate - expected_rate) / (abs(expected_rate) + 0.01)
        else:
            surprise = 0.0
        
        # Create decision
        decision = PolicyDecision(
            bank=bank,
            timestamp=datetime.now(),
            action=action,
            rate_change_bps=rate_change_bps,
            new_rate=new_rate,
            statement_summary=summary,
            stance=stance,
            hawkish_score=hawkish_score,
            surprise_factor=surprise
        )
        
        # Update state
        self.current_rates[bank] = new_rate
        self.current_stances[bank] = hawkish_score
        self.decisions[bank].append(decision)
        self.last_updates[bank] = datetime.now()
        
        logger.info(
            f"{bank.value.upper()}: Rate={new_rate:.2f}%, "
            f"Change={rate_change_bps}bps, Stance={stance.value}"
        )
        
        return decision
    
    def calculate_divergence(
        self,
        bank1: CentralBank,
        bank2: CentralBank
    ) -> PolicyDivergence:
        """
        Calculate policy divergence between two central banks
        """
        rate1 = self.current_rates.get(bank1, 0)
        rate2 = self.current_rates.get(bank2, 0)
        stance1 = self.current_stances.get(bank1, 0)
        stance2 = self.current_stances.get(bank2, 0)
        
        rate_diff = rate1 - rate2
        stance_diff = stance1 - stance2
        
        # Combined divergence score
        # Weight rate differential more heavily
        divergence_score = (rate_diff * 0.6 + stance_diff * 0.4)
        
        # Determine currency pair
        ccy1 = self.BANK_CURRENCY[bank1]
        ccy2 = self.BANK_CURRENCY[bank2]
        currency_pair = f"{ccy1}/{ccy2}"
        
        # Expected direction
        if divergence_score > 0.5:
            expected_direction = f"{ccy1} strength"
            confidence = min(0.9, 0.5 + abs(divergence_score) * 0.2)
        elif divergence_score < -0.5:
            expected_direction = f"{ccy2} strength"
            confidence = min(0.9, 0.5 + abs(divergence_score) * 0.2)
        else:
            expected_direction = "Neutral"
            confidence = 0.3
        
        return PolicyDivergence(
            bank1=bank1,
            bank2=bank2,
            rate_differential=rate_diff,
            stance_differential=stance_diff,
            divergence_score=divergence_score,
            currency_pair=currency_pair,
            expected_direction=expected_direction,
            confidence=confidence
        )
    
    def get_all_divergences(self) -> List[PolicyDivergence]:
        """Calculate divergence for all major pairs"""
        divergences = []
        
        # Major pairs
        pairs = [
            (CentralBank.FED, CentralBank.ECB),   # EUR/USD
            (CentralBank.FED, CentralBank.BOJ),   # USD/JPY
            (CentralBank.BOE, CentralBank.FED),   # GBP/USD
            (CentralBank.FED, CentralBank.SNB),   # USD/CHF
            (CentralBank.RBA, CentralBank.FED),   # AUD/USD
            (CentralBank.FED, CentralBank.BOC),   # USD/CAD
            (CentralBank.RBNZ, CentralBank.FED),  # NZD/USD
            (CentralBank.ECB, CentralBank.BOE),   # EUR/GBP
            (CentralBank.ECB, CentralBank.BOJ),   # EUR/JPY
            (CentralBank.BOE, CentralBank.BOJ),   # GBP/JPY
        ]
        
        for bank1, bank2 in pairs:
            div = self.calculate_divergence(bank1, bank2)
            divergences.append(div)
        
        # Sort by absolute divergence
        divergences.sort(key=lambda x: abs(x.divergence_score), reverse=True)
        
        return divergences
    
    def update_expectations(
        self,
        bank: CentralBank,
        expected_3m: float,
        expected_6m: float,
        expected_12m: float,
        prob_hike: float = 0.5,
        prob_cut: float = 0.5,
        terminal_rate: Optional[float] = None
    ) -> RateExpectation:
        """Update rate expectations for a central bank"""
        current = self.current_rates.get(bank, expected_3m)
        
        expectation = RateExpectation(
            bank=bank,
            current_rate=current,
            expected_rate_3m=expected_3m,
            expected_rate_6m=expected_6m,
            expected_rate_12m=expected_12m,
            probability_hike_next=prob_hike,
            probability_cut_next=prob_cut,
            terminal_rate=terminal_rate or max(expected_3m, expected_6m, expected_12m)
        )
        
        self.expectations[bank] = expectation
        
        return expectation
    
    def get_rate_path(self, bank: CentralBank) -> Dict[str, Any]:
        """Get expected rate path for a central bank"""
        current = self.current_rates.get(bank, 0)
        exp = self.expectations.get(bank)
        
        if exp:
            return {
                'bank': bank.value,
                'current': current,
                'path': {
                    'now': current,
                    '3m': exp.expected_rate_3m,
                    '6m': exp.expected_rate_6m,
                    '12m': exp.expected_rate_12m,
                    'terminal': exp.terminal_rate
                },
                'direction': 'hiking' if exp.expected_12m > current else 'cutting' if exp.expected_12m < current else 'holding',
                'next_meeting_prob': {
                    'hike': exp.probability_hike_next,
                    'cut': exp.probability_cut_next,
                    'hold': 1 - exp.probability_hike_next - exp.probability_cut_next
                }
            }
        else:
            return {
                'bank': bank.value,
                'current': current,
                'path': {'now': current},
                'direction': 'unknown'
            }
    
    def get_next_meetings(self, days_ahead: int = 30) -> List[Dict[str, Any]]:
        """Get upcoming central bank meetings"""
        meetings = []
        now = datetime.now()
        
        for bank in CentralBank:
            last_update = self.last_updates.get(bank, now - timedelta(days=30))
            freq = self.MEETING_FREQUENCY[bank]
            
            # Estimate next meeting
            days_since = (now - last_update).days
            days_to_next = freq - (days_since % freq)
            
            if days_to_next <= days_ahead:
                next_meeting = now + timedelta(days=days_to_next)
                
                # Get expectations
                exp = self.expectations.get(bank)
                
                meetings.append({
                    'bank': bank.value,
                    'currency': self.BANK_CURRENCY[bank],
                    'date': next_meeting.strftime('%Y-%m-%d'),
                    'days_away': days_to_next,
                    'current_rate': self.current_rates.get(bank, 0),
                    'expected_action': self._predict_action(bank),
                    'importance': self._get_importance(bank)
                })
        
        # Sort by date
        meetings.sort(key=lambda x: x['days_away'])
        
        return meetings
    
    def _predict_action(self, bank: CentralBank) -> str:
        """Predict next action based on stance and expectations"""
        stance = self.current_stances.get(bank, 0)
        exp = self.expectations.get(bank)
        
        if exp:
            if exp.probability_hike_next > 0.6:
                return "Likely Hike"
            elif exp.probability_cut_next > 0.6:
                return "Likely Cut"
        
        if stance > 0.3:
            return "Hawkish Hold / Possible Hike"
        elif stance < -0.3:
            return "Dovish Hold / Possible Cut"
        
        return "Hold Expected"
    
    def _get_importance(self, bank: CentralBank) -> str:
        """Get importance level of central bank"""
        high_importance = [CentralBank.FED, CentralBank.ECB, CentralBank.BOJ]
        medium_importance = [CentralBank.BOE, CentralBank.SNB, CentralBank.BOC]
        
        if bank in high_importance:
            return "HIGH"
        elif bank in medium_importance:
            return "MEDIUM"
        return "LOW"
    
    def get_trading_signals(self) -> List[Dict[str, Any]]:
        """Generate trading signals from policy divergence"""
        signals = []
        divergences = self.get_all_divergences()
        
        for div in divergences:
            if abs(div.divergence_score) > 0.5 and div.confidence > 0.5:
                signal = {
                    'pair': div.currency_pair,
                    'direction': 'BUY' if div.divergence_score > 0 else 'SELL',
                    'strength': abs(div.divergence_score),
                    'confidence': div.confidence,
                    'reasoning': div.expected_direction,
                    'rate_differential': div.rate_differential,
                    'stance_differential': div.stance_differential
                }
                signals.append(signal)
        
        return signals
    
    def get_summary(self) -> Dict[str, Any]:
        """Get summary of all central bank policies"""
        return {
            'rates': {bank.value: rate for bank, rate in self.current_rates.items()},
            'stances': {bank.value: stance for bank, stance in self.current_stances.items()},
            'most_hawkish': max(self.current_stances.items(), key=lambda x: x[1])[0].value,
            'most_dovish': min(self.current_stances.items(), key=lambda x: x[1])[0].value,
            'highest_rate': max(self.current_rates.items(), key=lambda x: x[1]),
            'lowest_rate': min(self.current_rates.items(), key=lambda x: x[1]),
            'upcoming_meetings': self.get_next_meetings(14),
            'top_divergences': [d.to_dict() for d in self.get_all_divergences()[:5]]
        }


# Factory function
def create_central_bank_tracker(config: Optional[Dict[str, Any]] = None) -> CentralBankTracker:
    """Create central bank tracker"""
    return CentralBankTracker(config)
