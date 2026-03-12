"""
Geopolitical Intelligence Engine
AI-driven policy analysis and geopolitical risk assessment
"""

import numpy as np
import pandas as pd
from typing import Any, Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime, timedelta
import logging
from collections import defaultdict
import re
import numpy
import pandas

logger = logging.getLogger(__name__)


class PolicyStance(Enum):
    """Central bank policy stance"""
    VERY_HAWKISH = "very_hawkish"
    HAWKISH = "hawkish"
    NEUTRAL = "neutral"
    DOVISH = "dovish"
    VERY_DOVISH = "very_dovish"


class GeopoliticalThreat(Enum):
    """Types of geopolitical threats"""
    WAR = "war"
    SANCTIONS = "sanctions"
    ELECTION = "election"
    COUP = "coup"
    TRADE_WAR = "trade_war"
    DEBT_CRISIS = "debt_crisis"
    SUPPLY_SHOCK = "supply_shock"
    CYBER_ATTACK = "cyber_attack"


@dataclass
class PolicyAnalysis:
    """Central bank policy analysis"""
    institution: str  # Fed, ECB, BoJ, etc.
    stance: PolicyStance
    hawkish_score: float  # -100 to +100
    key_phrases: List[str]
    rate_probability: Dict[str, float]  # Action -> probability
    forward_guidance_strength: float  # 0-1
    tone_shift: float  # Change from previous
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class GeopoliticalEvent:
    """Geopolitical event"""
    event_type: GeopoliticalThreat
    region: str
    severity: float  # 0-10
    market_impact: str  # HIGH, MEDIUM, LOW
    affected_assets: List[str]
    description: str
    escalation_probability: float  # 0-1
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class CommodityMacroLink:
    """Commodity-macro causality relationship"""
    commodity: str
    macro_variable: str
    correlation: float
    lag_periods: int
    mechanism: str
    strength: float  # 0-1
    current_signal: str  # BULLISH, BEARISH, NEUTRAL


class CentralBankAnalyzer:
    """Analyze central bank communications"""
    
    def __init__(self):
        self.hawkish_keywords = {
            'inflation', 'tighten', 'restrictive', 'raise', 'hike',
            'aggressive', 'combat', 'elevated', 'persistent', 'concern'
        }
        
        self.dovish_keywords = {
            'accommodative', 'supportive', 'patient', 'gradual', 'cut',
            'lower', 'ease', 'stimulus', 'growth', 'employment'
        }
        
        self.commitment_phrases = {
            'will continue': 0.9,
            'committed to': 0.95,
            'determined to': 0.95,
            'until': 0.8,
            'as long as': 0.8,
            'data dependent': 0.3,
            'monitor': 0.4,
            'assess': 0.4
        }
        
        self.statement_history: Dict[str, List[str]] = defaultdict(list)
        
    def analyze_statement(self, institution: str, 
                         statement: str,
                         previous_statement: Optional[str] = None) -> PolicyAnalysis:
        """Analyze central bank statement"""
        
        # Store in history
        self.statement_history[institution].append(statement)
        
        # Calculate hawkish/dovish score
        hawkish_score = self._calculate_policy_score(statement)
        
        # Determine stance
        stance = self._determine_stance(hawkish_score)
        
        # Extract key phrases
        key_phrases = self._extract_key_phrases(statement)
        
        # Calculate rate probabilities
        rate_prob = self._calculate_rate_probabilities(statement, hawkish_score)
        
        # Measure forward guidance strength
        fg_strength = self._measure_forward_guidance(statement)
        
        # Calculate tone shift
        tone_shift = 0.0
        if previous_statement:
            prev_score = self._calculate_policy_score(previous_statement)
            tone_shift = hawkish_score - prev_score
        
        return PolicyAnalysis(
            institution=institution,
            stance=stance,
            hawkish_score=hawkish_score,
            key_phrases=key_phrases,
            rate_probability=rate_prob,
            forward_guidance_strength=fg_strength,
            tone_shift=tone_shift
        )
    
    def _calculate_policy_score(self, statement: str) -> float:
        """Calculate hawkish/dovish score (-100 to +100)"""
        
        statement_lower = statement.lower()
        words = statement_lower.split()
        
        hawkish_count = sum(1 for word in words if word in self.hawkish_keywords)
        dovish_count = sum(1 for word in words if word in self.dovish_keywords)
        
        total = hawkish_count + dovish_count
        if total == 0:
            return 0.0
        
        # Score from -100 (dovish) to +100 (hawkish)
        score = ((hawkish_count - dovish_count) / total) * 100
        
        return score
    
    def _determine_stance(self, score: float) -> PolicyStance:
        """Determine policy stance from score"""
        
        if score > 50:
            return PolicyStance.VERY_HAWKISH
        elif score > 20:
            return PolicyStance.HAWKISH
        elif score > -20:
            return PolicyStance.NEUTRAL
        elif score > -50:
            return PolicyStance.DOVISH
        else:
            return PolicyStance.VERY_DOVISH
    
    def _extract_key_phrases(self, statement: str) -> List[str]:
        """Extract important phrases"""
        
        key_phrases = []
        
        # Look for commitment phrases
        for phrase in self.commitment_phrases:
            if phrase in statement.lower():
                # Extract sentence containing phrase
                sentences = statement.split('.')
                for sentence in sentences:
                    if phrase in sentence.lower():
                        key_phrases.append(sentence.strip())
                        break
        
        return key_phrases[:5]  # Top 5
    
    def _calculate_rate_probabilities(self, statement: str, 
                                     hawkish_score: float) -> Dict[str, float]:
        """Calculate probability of rate actions"""
        
        # Base probabilities from hawkish score
        if hawkish_score > 50:
            hike_prob = 0.8
            hold_prob = 0.15
            cut_prob = 0.05
        elif hawkish_score > 20:
            hike_prob = 0.6
            hold_prob = 0.35
            cut_prob = 0.05
        elif hawkish_score > -20:
            hike_prob = 0.2
            hold_prob = 0.6
            cut_prob = 0.2
        elif hawkish_score > -50:
            hike_prob = 0.05
            hold_prob = 0.35
            cut_prob = 0.6
        else:
            hike_prob = 0.05
            hold_prob = 0.15
            cut_prob = 0.8
        
        # Adjust based on explicit mentions
        if 'raise' in statement.lower() or 'hike' in statement.lower():
            hike_prob = min(hike_prob * 1.5, 0.95)
        if 'cut' in statement.lower() or 'lower' in statement.lower():
            cut_prob = min(cut_prob * 1.5, 0.95)
        
        # Normalize
        total = hike_prob + hold_prob + cut_prob
        
        return {
            'hike_25bps': hike_prob / total * 0.7,
            'hike_50bps': hike_prob / total * 0.3,
            'hold': hold_prob / total,
            'cut_25bps': cut_prob / total * 0.7,
            'cut_50bps': cut_prob / total * 0.3
        }
    
    def _measure_forward_guidance(self, statement: str) -> float:
        """Measure strength of forward guidance (0-1)"""
        
        statement_lower = statement.lower()
        
        total_strength = 0.0
        count = 0
        
        for phrase, strength in self.commitment_phrases.items():
            if phrase in statement_lower:
                total_strength += strength
                count += 1
        
        if count == 0:
            return 0.5  # Neutral
        
        return min(total_strength / count, 1.0)


class GeopoliticalRiskAnalyzer:
    """Analyze geopolitical risks and events"""
    
    def __init__(self):
        self.threat_keywords = {
            GeopoliticalThreat.WAR: ['war', 'conflict', 'invasion', 'military', 'troops'],
            GeopoliticalThreat.SANCTIONS: ['sanctions', 'embargo', 'restrictions', 'ban'],
            GeopoliticalThreat.ELECTION: ['election', 'vote', 'poll', 'campaign'],
            GeopoliticalThreat.TRADE_WAR: ['tariff', 'trade war', 'duties', 'protectionism'],
            GeopoliticalThreat.DEBT_CRISIS: ['debt', 'default', 'bankruptcy', 'fiscal'],
            GeopoliticalThreat.SUPPLY_SHOCK: ['shortage', 'disruption', 'supply chain']
        }
        
        self.severity_modifiers = {
            'major': 2.0,
            'significant': 1.5,
            'escalating': 1.8,
            'critical': 2.5,
            'minor': 0.5,
            'limited': 0.6
        }
        
        self.event_history: List[GeopoliticalEvent] = []
        
    def analyze_news(self, news_text: str, region: str = "Global") -> Optional[GeopoliticalEvent]:
        """Analyze news for geopolitical events"""
        
        news_lower = news_text.lower()
        
        # Detect event type
        event_type = None
        max_matches = 0
        
        for threat, keywords in self.threat_keywords.items():
            matches = sum(1 for keyword in keywords if keyword in news_lower)
            if matches > max_matches:
                max_matches = matches
                event_type = threat
        
        if event_type is None or max_matches == 0:
            return None
        
        # Calculate severity
        base_severity = max_matches * 2
        
        # Apply modifiers
        for modifier, multiplier in self.severity_modifiers.items():
            if modifier in news_lower:
                base_severity *= multiplier
        
        severity = min(base_severity, 10.0)
        
        # Determine market impact
        if severity > 7:
            market_impact = "HIGH"
        elif severity > 4:
            market_impact = "MEDIUM"
        else:
            market_impact = "LOW"
        
        # Identify affected assets
        affected = self._identify_affected_assets(event_type, region)
        
        # Calculate escalation probability
        escalation_prob = self._calculate_escalation_probability(news_text, event_type)
        
        event = GeopoliticalEvent(
            event_type=event_type,
            region=region,
            severity=severity,
            market_impact=market_impact,
            affected_assets=affected,
            description=news_text[:200],
            escalation_probability=escalation_prob
        )
        
        self.event_history.append(event)
        
        return event
    
    def _identify_affected_assets(self, event_type: GeopoliticalThreat, 
                                  region: str) -> List[str]:
        """Identify assets affected by event"""
        
        affected = []
        
        if event_type == GeopoliticalThreat.WAR:
            affected.extend(['Oil', 'Gold', 'Defense stocks', 'Safe haven currencies'])
            if 'middle east' in region.lower():
                affected.append('Oil (major impact)')
        
        elif event_type == GeopoliticalThreat.SANCTIONS:
            affected.extend(['Commodities', 'Emerging markets', 'Energy'])
        
        elif event_type == GeopoliticalThreat.ELECTION:
            affected.extend(['Local currency', 'Local equities', 'Bonds'])
        
        elif event_type == GeopoliticalThreat.TRADE_WAR:
            affected.extend(['Export-dependent stocks', 'Currencies', 'Commodities'])
        
        elif event_type == GeopoliticalThreat.DEBT_CRISIS:
            affected.extend(['Sovereign bonds', 'Currency', 'Banking sector'])
        
        elif event_type == GeopoliticalThreat.SUPPLY_SHOCK:
            affected.extend(['Affected commodity', 'Related industries', 'Inflation'])
        
        return affected
    
    def _calculate_escalation_probability(self, news_text: str, 
                                         event_type: GeopoliticalThreat) -> float:
        """Calculate probability of escalation"""
        
        escalation_keywords = ['escalate', 'worsen', 'intensify', 'spread', 'expand']
        deescalation_keywords = ['resolve', 'peace', 'negotiate', 'settle', 'calm']
        
        news_lower = news_text.lower()
        
        escalation_count = sum(1 for kw in escalation_keywords if kw in news_lower)
        deescalation_count = sum(1 for kw in deescalation_keywords if kw in news_lower)
        
        # Base probability by event type
        base_prob = {
            GeopoliticalThreat.WAR: 0.7,
            GeopoliticalThreat.SANCTIONS: 0.5,
            GeopoliticalThreat.ELECTION: 0.3,
            GeopoliticalThreat.TRADE_WAR: 0.6,
            GeopoliticalThreat.DEBT_CRISIS: 0.5,
            GeopoliticalThreat.SUPPLY_SHOCK: 0.4
        }.get(event_type, 0.5)
        
        # Adjust based on keywords
        adjustment = (escalation_count - deescalation_count) * 0.1
        
        return max(0.0, min(1.0, base_prob + adjustment))
    
    def calculate_geopolitical_tension_index(self) -> float:
        """Calculate overall geopolitical tension (0-10)"""
        
        if not self.event_history:
            return 0.0
        
        # Recent events (last 30 days)
        cutoff = datetime.now() - timedelta(days=30)
        recent = [e for e in self.event_history if e.timestamp > cutoff]
        
        if not recent:
            return 0.0
        
        # Weight by recency and severity
        total_tension = 0.0
        for event in recent:
            days_ago = (datetime.now() - event.timestamp).days
            recency_weight = np.exp(-days_ago / 10)  # Exponential decay
            total_tension += event.severity * recency_weight
        
        # Normalize
        return min(total_tension / len(recent), 10.0)


class CommodityMacroAnalyzer:
    """Analyze commodity-macro causality chains"""
    
    def __init__(self):
        self.relationships = self._build_causality_network()
        
    def _build_causality_network(self) -> List[CommodityMacroLink]:
        """Build network of commodity-macro relationships"""
        
        return [
            CommodityMacroLink(
                commodity="Oil",
                macro_variable="Inflation",
                correlation=0.7,
                lag_periods=2,
                mechanism="Energy costs pass through to CPI",
                strength=0.8,
                current_signal="NEUTRAL"
            ),
            CommodityMacroLink(
                commodity="Oil",
                macro_variable="USD",
                correlation=-0.6,
                lag_periods=0,
                mechanism="Petrodollar recycling and risk sentiment",
                strength=0.7,
                current_signal="NEUTRAL"
            ),
            CommodityMacroLink(
                commodity="Copper",
                macro_variable="Economic Growth",
                correlation=0.8,
                lag_periods=1,
                mechanism="Industrial demand proxy",
                strength=0.9,
                current_signal="NEUTRAL"
            ),
            CommodityMacroLink(
                commodity="Gold",
                macro_variable="Real Rates",
                correlation=-0.7,
                lag_periods=0,
                mechanism="Opportunity cost of holding gold",
                strength=0.8,
                current_signal="NEUTRAL"
            ),
            CommodityMacroLink(
                commodity="Grains",
                macro_variable="Food Inflation",
                correlation=0.6,
                lag_periods=1,
                mechanism="Direct input to food prices",
                strength=0.7,
                current_signal="NEUTRAL"
            )
        ]
    
    def analyze_commodity_signal(self, commodity: str, 
                                price_change: float) -> List[Dict[str, Any]]:
        """Analyze macro implications of commodity move"""
        
        implications = []
        
        for link in self.relationships:
            if link.commodity == commodity:
                # Calculate expected macro impact
                expected_impact = price_change * link.correlation * link.strength
                
                # Determine signal
                if abs(expected_impact) > 0.05:  # >5% impact
                    signal = "BULLISH" if expected_impact > 0 else "BEARISH"
                else:
                    signal = "NEUTRAL"
                
                implications.append({
                    'macro_variable': link.macro_variable,
                    'expected_impact': expected_impact,
                    'lag_periods': link.lag_periods,
                    'mechanism': link.mechanism,
                    'signal': signal,
                    'confidence': link.strength
                })
        
        return implications
    
    def trace_causality_chain(self, start_variable: str, 
                             end_variable: str) -> List[str]:
        """Trace causality chain from start to end variable"""
        
        # Simplified - in production use graph traversal
        chain = [start_variable]
        
        # Find direct links
        for link in self.relationships:
            if link.commodity == start_variable:
                chain.append(link.macro_variable)
                if link.macro_variable == end_variable:
                    return chain
        
        return chain


class GeopoliticalIntelligenceEngine:
    """
    Complete geopolitical intelligence system
    """
    
    def __init__(self):
        self.cb_analyzer = CentralBankAnalyzer()
        self.geo_analyzer = GeopoliticalRiskAnalyzer()
        self.commodity_analyzer = CommodityMacroAnalyzer()
        
    def analyze_central_bank(self, institution: str, 
                            statement: str) -> PolicyAnalysis:
        """Analyze central bank statement"""
        
        # Get previous statement if available
        prev = None
        if self.cb_analyzer.statement_history[institution]:
            prev = self.cb_analyzer.statement_history[institution][-1]
        
        return self.cb_analyzer.analyze_statement(institution, statement, prev)
    
    def analyze_geopolitical_event(self, news: str, 
                                  region: str = "Global") -> Optional[GeopoliticalEvent]:
        """Analyze geopolitical event"""
        return self.geo_analyzer.analyze_news(news, region)
    
    def get_tension_index(self) -> float:
        """Get current geopolitical tension index"""
        return self.geo_analyzer.calculate_geopolitical_tension_index()
    
    def analyze_commodity_move(self, commodity: str, 
                              price_change: float) -> List[Dict[str, Any]]:
        """Analyze macro implications of commodity price move"""
        return self.commodity_analyzer.analyze_commodity_signal(commodity, price_change)
    
    def comprehensive_analysis(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Comprehensive geopolitical analysis"""
        
        results = {
            'policy_analysis': {},
            'geopolitical_events': [],
            'tension_index': 0.0,
            'commodity_implications': {},
            'overall_risk': 'LOW',
            'recommendations': []
        }
        
        # Analyze central bank statements
        if 'cb_statements' in data:
            for institution, statement in data['cb_statements'].items():
                analysis = self.analyze_central_bank(institution, statement)
                results['policy_analysis'][institution] = analysis
        
        # Analyze geopolitical news
        if 'news' in data:
            for news_item in data['news']:
                event = self.analyze_geopolitical_event(
                    news_item.get('text', ''),
                    news_item.get('region', 'Global')
                )
                if event:
                    results['geopolitical_events'].append(event)
        
        # Calculate tension index
        results['tension_index'] = self.get_tension_index()
        
        # Analyze commodity moves
        if 'commodity_changes' in data:
            for commodity, change in data['commodity_changes'].items():
                implications = self.analyze_commodity_move(commodity, change)
                results['commodity_implications'][commodity] = implications
        
        # Determine overall risk
        if results['tension_index'] > 7:
            results['overall_risk'] = 'CRITICAL'
        elif results['tension_index'] > 5:
            results['overall_risk'] = 'HIGH'
        elif results['tension_index'] > 3:
            results['overall_risk'] = 'ELEVATED'
        else:
            results['overall_risk'] = 'LOW'
        
        # Generate recommendations
        results['recommendations'] = self._generate_recommendations(results)
        
        return results
    
    def _generate_recommendations(self, analysis: Dict[str, Any]) -> List[str]:
        """Generate trading recommendations"""
        
        recommendations = []
        
        # Based on tension index
        tension = analysis['tension_index']
        if tension > 7:
            recommendations.append("CRITICAL: Reduce risk exposure significantly")
            recommendations.append("Increase allocation to safe havens (Gold, CHF, JPY)")
        elif tension > 5:
            recommendations.append("HIGH RISK: Hedge portfolio with options")
            recommendations.append("Avoid emerging markets")
        
        # Based on policy analysis
        hawkish_count = sum(1 for p in analysis['policy_analysis'].values() 
                           if p.stance in [PolicyStance.HAWKISH, PolicyStance.VERY_HAWKISH])
        
        if hawkish_count >= 2:
            recommendations.append("Multiple CBs hawkish: Favor USD, reduce duration")
        
        # Based on geopolitical events
        high_severity_events = [e for e in analysis['geopolitical_events'] 
                               if e.severity > 7]
        
        if high_severity_events:
            recommendations.append(f"{len(high_severity_events)} high-severity events: Defensive positioning")
        
        return recommendations


# Example usage
if __name__ == "__main__":
    # Initialize engine
    engine = GeopoliticalIntelligenceEngine()
    
    # Sample data
    data = {
        'cb_statements': {
            'Fed': "Inflation remains elevated and persistent. We are committed to bringing inflation back to our 2% target and will continue to raise rates as necessary.",
            'ECB': "Economic growth is slowing but we remain data dependent. We will monitor conditions and assess the appropriate policy stance."
        },
        'news': [
            {
                'text': "Major escalation in Middle East conflict as military operations intensify",
                'region': "Middle East"
            },
            {
                'text': "Trade tensions rise as new tariffs announced on key exports",
                'region': "Global"
            }
        ],
        'commodity_changes': {
            'Oil': 0.15,  # 15% increase
            'Copper': -0.08,  # 8% decrease
            'Gold': 0.05  # 5% increase
        }
    }
    
    # Comprehensive analysis
    results = engine.comprehensive_analysis(data)
    
    logger.info(f"\n{'='*80}")
    logger.info(f"GEOPOLITICAL INTELLIGENCE ANALYSIS")
    logger.info(f"{'='*80}")
    logger.info(f"\nGeopolitical Tension Index: {results['tension_index']:.1f}/10")
    logger.info(f"Overall Risk Level: {results['overall_risk']}")
    
    logger.info(f"\n{'='*80}")
    logger.info(f"CENTRAL BANK POLICY ANALYSIS")
    logger.info(f"{'='*80}")
    
    for institution, analysis in results['policy_analysis'].items():
        logger.info(f"\n{institution}:")
        logger.info(f"  Stance: {analysis.stance.value}")
        logger.info(f"  Hawkish Score: {analysis.hawkish_score:+.1f}")
        logger.info(f"  Forward Guidance Strength: {analysis.forward_guidance_strength:.2f}")
        logger.info(f"  Rate Probabilities:")
        for action, prob in analysis.rate_probability.items():
            if prob > 0.1:
                logger.info(f"    {action}: {prob:.1%}")
    
    logger.info(f"\n{'='*80}")
    logger.info(f"GEOPOLITICAL EVENTS")
    logger.info(f"{'='*80}")
    
    for event in results['geopolitical_events']:
        logger.info(f"\n{event.event_type.value.upper()} - {event.region}")
        logger.info(f"  Severity: {event.severity:.1f}/10")
        logger.info(f"  Market Impact: {event.market_impact}")
        logger.info(f"  Escalation Probability: {event.escalation_probability:.1%}")
        logger.info(f"  Affected Assets: {', '.join(event.affected_assets)}")
    
    logger.info(f"\n{'='*80}")
    logger.info(f"COMMODITY-MACRO IMPLICATIONS")
    logger.info(f"{'='*80}")
    
    for commodity, implications in results['commodity_implications'].items():
        logger.info(f"\n{commodity}:")
        for impl in implications:
            logger.info(f"  → {impl['macro_variable']}: {impl['signal']}")
            logger.info(f"     Impact: {impl['expected_impact']:+.1%} (lag: {impl['lag_periods']} periods)")
            logger.info(f"     Mechanism: {impl['mechanism']}")
    
    logger.info(f"\n{'='*80}")
    logger.info(f"RECOMMENDATIONS")
    logger.info(f"{'='*80}")
    
    for i, rec in enumerate(results['recommendations'], 1):
        logger.info(f"{i}. {rec}")
