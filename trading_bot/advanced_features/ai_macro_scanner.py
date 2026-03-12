import logging
logger = logging.getLogger(__name__)
"""AI Macro Scanner - Advanced Economic Analysis System.

This module provides comprehensive macroeconomic analysis capabilities including:
- Central bank report analysis
- FOMC minutes parsing
- Economic release impact assessment
- Policy move anticipation
- Geopolitical risk monitoring
"""

import asyncio
import json
import re
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
import pandas as pd
import numpy as np
from loguru import logger
try:
    import aiohttp
except ImportError:
    aiohttp = None
import sqlite3
from pathlib import Path
import numpy
import pandas


class PolicyStance(Enum):
    """Central bank policy stance."""
    HAWKISH = "hawkish"
    DOVISH = "dovish"
    NEUTRAL = "neutral"
    UNCERTAIN = "uncertain"


class EconomicImpact(Enum):
    """Economic event impact level."""
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    NEGLIGIBLE = "negligible"


class GeopoliticalRisk(Enum):
    """Geopolitical risk levels."""
    CRITICAL = "critical"
    HIGH = "high"
    ELEVATED = "elevated"
    MODERATE = "moderate"
    LOW = "low"


@dataclass
class MacroEvent:
    """Macroeconomic event data."""
    event_type: str
    timestamp: datetime
    country: str
    currency: str
    actual_value: Optional[float]
    forecast_value: Optional[float]
    previous_value: Optional[float]
    impact_level: EconomicImpact
    surprise_index: float
    market_reaction: Dict[str, float]
    policy_implications: Dict[str, Any]


@dataclass
class PolicyAnalysis:
    """Central bank policy analysis."""
    bank_name: str
    meeting_date: datetime
    policy_stance: PolicyStance
    rate_decision: Optional[float]
    statement_sentiment: float
    key_phrases: List[str]
    forward_guidance: str
    market_expectations: Dict[str, float]
    confidence_score: float


@dataclass
class GeopoliticalEvent:
    """Geopolitical event analysis."""
    event_type: str
    timestamp: datetime
    affected_regions: List[str]
    risk_level: GeopoliticalRisk
    market_impact: Dict[str, float]
    duration_estimate: str
    affected_currencies: List[str]
    safe_haven_flows: Dict[str, float]


class AIMacroScanner:
    """Advanced AI-powered macroeconomic scanner and analysis system."""
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize the AI Macro Scanner.
        
        Args:
            config: Configuration dictionary
        """
        self.config = config
        self.db_path = Path(config.get('db_path', 'data/macro_analysis.db'))
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        
        # API configurations
        self.news_api_key = config.get('news_api_key', 'demo_key')
        self.economic_api_key = config.get('economic_api_key', 'demo_key')
        
        # Analysis parameters
        self.lookback_days = config.get('lookback_days', 30)
        self.update_interval = config.get('update_interval', 3600)  # 1 hour
        
        # Initialize database
        self._init_database()
        
        # Central bank keywords for policy analysis
        self.hawkish_keywords = [
            'inflation', 'tighten', 'raise rates', 'aggressive', 'combat',
            'restrictive', 'cooling', 'overheating', 'price pressures'
        ]
        
        self.dovish_keywords = [
            'accommodation', 'stimulus', 'support', 'lower rates', 'easing',
            'growth concerns', 'employment', 'dovish', 'patient', 'gradual'
        ]
        
        # Geopolitical risk keywords
        self.geopolitical_keywords = {
            'war': 3.0, 'conflict': 2.5, 'sanctions': 2.0, 'election': 1.5,
            'trade war': 2.5, 'brexit': 2.0, 'terrorism': 3.0, 'coup': 3.0,
            'nuclear': 3.5, 'cyber attack': 2.0, 'pandemic': 3.0
        }
        
        logger.info("AI Macro Scanner initialized")
    
    def _init_database(self):
        """Initialize SQLite database for macro data storage."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute('''
                CREATE TABLE IF NOT EXISTS macro_events (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    event_type TEXT NOT NULL,
                    timestamp DATETIME NOT NULL,
                    country TEXT NOT NULL,
                    currency TEXT NOT NULL,
                    actual_value REAL,
                    forecast_value REAL,
                    previous_value REAL,
                    impact_level TEXT NOT NULL,
                    surprise_index REAL NOT NULL,
                    market_reaction TEXT NOT NULL,
                    policy_implications TEXT NOT NULL,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            conn.execute('''
                CREATE TABLE IF NOT EXISTS policy_analysis (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    bank_name TEXT NOT NULL,
                    meeting_date DATETIME NOT NULL,
                    policy_stance TEXT NOT NULL,
                    rate_decision REAL,
                    statement_sentiment REAL NOT NULL,
                    key_phrases TEXT NOT NULL,
                    forward_guidance TEXT NOT NULL,
                    market_expectations TEXT NOT NULL,
                    confidence_score REAL NOT NULL,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            conn.execute('''
                CREATE TABLE IF NOT EXISTS geopolitical_events (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    event_type TEXT NOT NULL,
                    timestamp DATETIME NOT NULL,
                    affected_regions TEXT NOT NULL,
                    risk_level TEXT NOT NULL,
                    market_impact TEXT NOT NULL,
                    duration_estimate TEXT NOT NULL,
                    affected_currencies TEXT NOT NULL,
                    safe_haven_flows TEXT NOT NULL,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            conn.commit()
    
    async def scan_economic_calendar(self) -> List[MacroEvent]:
        """Scan and analyze upcoming economic events.
        
        Returns:
            List of analyzed macro events
        """
        try:
            # Mock implementation - in production, this would connect to economic APIs
            events = []
            
            # Generate mock economic events
            event_types = [
                'CPI', 'NFP', 'GDP', 'Retail Sales', 'PMI', 'Unemployment',
                'Interest Rate Decision', 'Trade Balance', 'Consumer Confidence'
            ]
            
            countries = ['US', 'EU', 'UK', 'JP', 'CA', 'AU', 'NZ', 'CH']
            currencies = ['USD', 'EUR', 'GBP', 'JPY', 'CAD', 'AUD', 'NZD', 'CHF']
            
            for i in range(10):  # Generate 10 mock events
                event_type = np.random.choice(event_types)
                country = np.random.choice(countries)
                currency = np.random.choice(currencies)
                
                # Generate realistic values
                actual = np.random.normal(2.5, 1.0)
                forecast = actual + np.random.normal(0, 0.3)
                previous = actual + np.random.normal(0, 0.5)
                
                # Calculate surprise index
                surprise_index = (actual - forecast) / abs(forecast) if forecast != 0 else 0
                
                # Determine impact level
                if abs(surprise_index) > 0.5:
                    impact = EconomicImpact.HIGH
                elif abs(surprise_index) > 0.2:
                    impact = EconomicImpact.MEDIUM
                else:
                    impact = EconomicImpact.LOW
                
                # Mock market reaction
                market_reaction = {
                    'currency_impact': surprise_index * 0.5,
                    'bond_yield_impact': surprise_index * 0.3,
                    'equity_impact': -surprise_index * 0.2
                }
                
                # Policy implications
                policy_implications = {
                    'rate_probability_change': surprise_index * 0.1,
                    'policy_stance_shift': surprise_index * 0.05
                }
                
                event = MacroEvent(
                    event_type=event_type,
                    timestamp=datetime.now() + timedelta(hours=i),
                    country=country,
                    currency=currency,
                    actual_value=actual,
                    forecast_value=forecast,
                    previous_value=previous,
                    impact_level=impact,
                    surprise_index=surprise_index,
                    market_reaction=market_reaction,
                    policy_implications=policy_implications
                )
                
                events.append(event)
            
            # Store events in database
            await self._store_macro_events(events)
            
            logger.info(f"Scanned {len(events)} economic events")
            return events
            
        except Exception as e:
            logger.error(f"Error scanning economic calendar: {e}")
            return []
    
    async def analyze_central_bank_communications(self, bank: str) -> PolicyAnalysis:
        """Analyze central bank communications and policy stance.
        
        Args:
            bank: Central bank name (e.g., 'FED', 'ECB', 'BOE')
            
        Returns:
            Policy analysis results
        """
        try:
            # Mock implementation - in production, this would parse actual CB communications
            
            # Generate mock policy analysis
            policy_stances = list(PolicyStance)
            stance = np.random.choice(policy_stances)
            
            # Mock sentiment analysis of statements
            if stance == PolicyStance.HAWKISH:
                sentiment = np.random.uniform(0.3, 0.8)
                key_phrases = ['inflation concerns', 'tightening policy', 'rate increases']
                rate_change_prob = 0.7
            elif stance == PolicyStance.DOVISH:
                sentiment = np.random.uniform(-0.8, -0.3)
                key_phrases = ['support growth', 'accommodative policy', 'patient approach']
                rate_change_prob = 0.3
            else:
                sentiment = np.random.uniform(-0.2, 0.2)
                key_phrases = ['data dependent', 'monitor conditions', 'balanced approach']
                rate_change_prob = 0.5
            
            # Mock forward guidance
            guidance_options = [
                'Data-dependent approach to future policy decisions',
                'Gradual adjustment of monetary policy stance',
                'Committed to price stability mandate',
                'Monitoring economic developments closely'
            ]
            forward_guidance = np.random.choice(guidance_options)
            
            # Mock market expectations
            market_expectations = {
                'next_meeting_rate_change_prob': rate_change_prob,
                'year_end_rate_expectation': np.random.uniform(2.0, 5.0),
                'policy_uncertainty_index': np.random.uniform(0.2, 0.8)
            }
            
            analysis = PolicyAnalysis(
                bank_name=bank,
                meeting_date=datetime.now(),
                policy_stance=stance,
                rate_decision=np.random.choice([None, 0.25, -0.25, 0.5]),
                statement_sentiment=sentiment,
                key_phrases=key_phrases,
                forward_guidance=forward_guidance,
                market_expectations=market_expectations,
                confidence_score=np.random.uniform(0.6, 0.9)
            )
            
            # Store analysis in database
            await self._store_policy_analysis(analysis)
            
            logger.info(f"Analyzed {bank} policy stance: {stance.value}")
            return analysis
            
        except Exception as e:
            logger.error(f"Error analyzing central bank communications: {e}")
            return None
    
    async def monitor_geopolitical_risks(self) -> List[GeopoliticalEvent]:
        """Monitor and analyze geopolitical risk events.
        
        Returns:
            List of geopolitical events with risk assessment
        """
        try:
            events = []
            
            # Mock geopolitical events
            event_types = [
                'Election', 'Trade Dispute', 'Military Conflict', 'Sanctions',
                'Natural Disaster', 'Cyber Attack', 'Political Crisis', 'Brexit Update'
            ]
            
            regions = [
                ['US'], ['EU'], ['UK'], ['China'], ['Russia'], ['Middle East'],
                ['Asia Pacific'], ['Latin America'], ['Africa']
            ]
            
            for i in range(5):  # Generate 5 mock events
                event_type = np.random.choice(event_types)
                affected_regions = np.random.choice(regions)
                
                # Determine risk level based on event type
                risk_scores = {
                    'Military Conflict': GeopoliticalRisk.CRITICAL,
                    'Cyber Attack': GeopoliticalRisk.HIGH,
                    'Election': GeopoliticalRisk.ELEVATED,
                    'Trade Dispute': GeopoliticalRisk.ELEVATED,
                    'Sanctions': GeopoliticalRisk.HIGH,
                    'Natural Disaster': GeopoliticalRisk.MODERATE,
                    'Political Crisis': GeopoliticalRisk.HIGH,
                    'Brexit Update': GeopoliticalRisk.MODERATE
                }
                
                risk_level = risk_scores.get(event_type, GeopoliticalRisk.MODERATE)
                
                # Mock market impact
                impact_magnitude = {
                    GeopoliticalRisk.CRITICAL: 0.8,
                    GeopoliticalRisk.HIGH: 0.6,
                    GeopoliticalRisk.ELEVATED: 0.4,
                    GeopoliticalRisk.MODERATE: 0.2,
                    GeopoliticalRisk.LOW: 0.1
                }[risk_level]
                
                market_impact = {
                    'vix_impact': impact_magnitude * np.random.uniform(0.5, 1.5),
                    'safe_haven_demand': impact_magnitude * np.random.uniform(0.3, 1.0),
                    'risk_asset_impact': -impact_magnitude * np.random.uniform(0.2, 0.8)
                }
                
                # Affected currencies
                region_currencies = {
                    'US': ['USD'], 'EU': ['EUR'], 'UK': ['GBP'], 'China': ['CNY'],
                    'Russia': ['RUB'], 'Asia Pacific': ['JPY', 'AUD', 'NZD'],
                    'Middle East': ['USD'], 'Latin America': ['BRL', 'MXN'],
                    'Africa': ['ZAR']
                }
                
                affected_currencies = []
                for region in affected_regions:
                    affected_currencies.extend(region_currencies.get(region, ['USD']))
                
                # Safe haven flows
                safe_haven_flows = {
                    'USD': impact_magnitude * 0.6,
                    'JPY': impact_magnitude * 0.4,
                    'CHF': impact_magnitude * 0.3,
                    'Gold': impact_magnitude * 0.8
                }
                
                event = GeopoliticalEvent(
                    event_type=event_type,
                    timestamp=datetime.now() - timedelta(hours=np.random.randint(1, 24)),
                    affected_regions=affected_regions,
                    risk_level=risk_level,
                    market_impact=market_impact,
                    duration_estimate=f"{np.random.randint(1, 30)} days",
                    affected_currencies=affected_currencies,
                    safe_haven_flows=safe_haven_flows
                )
                
                events.append(event)
            
            # Store events in database
            await self._store_geopolitical_events(events)
            
            logger.info(f"Monitored {len(events)} geopolitical events")
            return events
            
        except Exception as e:
            logger.error(f"Error monitoring geopolitical risks: {e}")
            return []
    
    async def get_macro_outlook(self, currency: str, timeframe: str = '1M') -> Dict[str, Any]:
        """Get comprehensive macro outlook for a currency.
        
        Args:
            currency: Currency code (e.g., 'USD', 'EUR')
            timeframe: Analysis timeframe ('1W', '1M', '3M', '6M', '1Y')
            
        Returns:
            Comprehensive macro outlook
        """
        try:
            # Get recent events and analysis
            recent_events = await self._get_recent_events(currency, timeframe)
            policy_analysis = await self._get_recent_policy_analysis(currency)
            geopolitical_risks = await self._get_geopolitical_risks(currency)
            
            # Calculate overall macro score
            macro_score = self._calculate_macro_score(
                recent_events, policy_analysis, geopolitical_risks
            )
            
            # Generate outlook
            outlook = {
                'currency': currency,
                'timeframe': timeframe,
                'macro_score': macro_score,
                'policy_stance': policy_analysis.policy_stance.value if policy_analysis else 'neutral',
                'key_events': len(recent_events),
                'geopolitical_risk_level': self._assess_overall_geopolitical_risk(geopolitical_risks),
                'economic_surprises': self._calculate_surprise_index(recent_events),
                'policy_uncertainty': policy_analysis.market_expectations.get('policy_uncertainty_index', 0.5) if policy_analysis else 0.5,
                'recommendations': self._generate_recommendations(macro_score, policy_analysis, geopolitical_risks),
                'risk_factors': self._identify_risk_factors(recent_events, geopolitical_risks),
                'opportunities': self._identify_opportunities(recent_events, policy_analysis),
                'confidence_level': self._calculate_confidence_level(recent_events, policy_analysis)
            }
            
            logger.info(f"Generated macro outlook for {currency}: score={macro_score:.2f}")
            return outlook
            
        except Exception as e:
            logger.error(f"Error generating macro outlook: {e}")
            return {}
    
    async def _store_macro_events(self, events: List[MacroEvent]):
        """Store macro events in database."""
        with sqlite3.connect(self.db_path) as conn:
            for event in events:
                conn.execute('''
                    INSERT INTO macro_events 
                    (event_type, timestamp, country, currency, actual_value, 
                     forecast_value, previous_value, impact_level, surprise_index,
                     market_reaction, policy_implications)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    event.event_type, event.timestamp, event.country, event.currency,
                    event.actual_value, event.forecast_value, event.previous_value,
                    event.impact_level.value, event.surprise_index,
                    json.dumps(event.market_reaction), json.dumps(event.policy_implications)
                ))
            conn.commit()
    
    async def _store_policy_analysis(self, analysis: PolicyAnalysis):
        """Store policy analysis in database."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute('''
                INSERT INTO policy_analysis 
                (bank_name, meeting_date, policy_stance, rate_decision,
                 statement_sentiment, key_phrases, forward_guidance,
                 market_expectations, confidence_score)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                analysis.bank_name, analysis.meeting_date, analysis.policy_stance.value,
                analysis.rate_decision, analysis.statement_sentiment,
                json.dumps(analysis.key_phrases), analysis.forward_guidance,
                json.dumps(analysis.market_expectations), analysis.confidence_score
            ))
            conn.commit()
    
    async def _store_geopolitical_events(self, events: List[GeopoliticalEvent]):
        """Store geopolitical events in database."""
        with sqlite3.connect(self.db_path) as conn:
            for event in events:
                conn.execute('''
                    INSERT INTO geopolitical_events 
                    (event_type, timestamp, affected_regions, risk_level,
                     market_impact, duration_estimate, affected_currencies, safe_haven_flows)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    event.event_type, event.timestamp, json.dumps(event.affected_regions),
                    event.risk_level.value, json.dumps(event.market_impact),
                    event.duration_estimate, json.dumps(event.affected_currencies),
                    json.dumps(event.safe_haven_flows)
                ))
            conn.commit()
    
    async def _get_recent_events(self, currency: str, timeframe: str) -> List[MacroEvent]:
        """Get recent macro events for currency."""
        # Mock implementation - return empty list for now
        return []
    
    async def _get_recent_policy_analysis(self, currency: str) -> Optional[PolicyAnalysis]:
        """Get recent policy analysis for currency."""
        # Mock implementation - return None for now
        return None
    
    async def _get_geopolitical_risks(self, currency: str) -> List[GeopoliticalEvent]:
        """Get geopolitical risks affecting currency."""
        # Mock implementation - return empty list for now
        return []
    
    def _calculate_macro_score(self, events: List[MacroEvent], 
                              policy: Optional[PolicyAnalysis],
                              geo_risks: List[GeopoliticalEvent]) -> float:
        """Calculate overall macro score."""
        score = 0.0
        
        # Event impact
        for event in events:
            if event.impact_level == EconomicImpact.HIGH:
                score += event.surprise_index * 0.3
            elif event.impact_level == EconomicImpact.MEDIUM:
                score += event.surprise_index * 0.2
            else:
                score += event.surprise_index * 0.1
        
        # Policy stance impact
        if policy:
            if policy.policy_stance == PolicyStance.HAWKISH:
                score += 0.2
            elif policy.policy_stance == PolicyStance.DOVISH:
                score -= 0.2
        
        # Geopolitical risk impact
        for risk in geo_risks:
            if risk.risk_level == GeopoliticalRisk.CRITICAL:
                score -= 0.5
            elif risk.risk_level == GeopoliticalRisk.HIGH:
                score -= 0.3
            elif risk.risk_level == GeopoliticalRisk.ELEVATED:
                score -= 0.1
        
        return np.clip(score, -1.0, 1.0)
    
    def _assess_overall_geopolitical_risk(self, risks: List[GeopoliticalEvent]) -> str:
        """Assess overall geopolitical risk level."""
        if not risks:
            return 'low'
        
        max_risk = max(risk.risk_level for risk in risks)
        return max_risk.value
    
    def _calculate_surprise_index(self, events: List[MacroEvent]) -> float:
        """Calculate average economic surprise index."""
        if not events:
            return 0.0
        
        surprises = [event.surprise_index for event in events if event.surprise_index is not None]
        return np.mean(surprises) if surprises else 0.0
    
    def _generate_recommendations(self, macro_score: float, 
                                policy: Optional[PolicyAnalysis],
                                geo_risks: List[GeopoliticalEvent]) -> List[str]:
        """Generate trading recommendations based on macro analysis."""
        recommendations = []
        
        if macro_score > 0.3:
            recommendations.append("Bullish macro environment - consider long positions")
        elif macro_score < -0.3:
            recommendations.append("Bearish macro environment - consider short positions")
        else:
            recommendations.append("Neutral macro environment - range trading strategies")
        
        if policy and policy.policy_stance == PolicyStance.HAWKISH:
            recommendations.append("Hawkish central bank stance supports currency strength")
        elif policy and policy.policy_stance == PolicyStance.DOVISH:
            recommendations.append("Dovish central bank stance may weaken currency")
        
        if any(risk.risk_level in [GeopoliticalRisk.CRITICAL, GeopoliticalRisk.HIGH] for risk in geo_risks):
            recommendations.append("High geopolitical risk - consider safe haven assets")
        
        return recommendations
    
    def _identify_risk_factors(self, events: List[MacroEvent], 
                              geo_risks: List[GeopoliticalEvent]) -> List[str]:
        """Identify key risk factors."""
        risks = []
        
        high_impact_events = [e for e in events if e.impact_level == EconomicImpact.HIGH]
        if high_impact_events:
            risks.append(f"{len(high_impact_events)} high-impact economic events pending")
        
        critical_geo_risks = [r for r in geo_risks if r.risk_level == GeopoliticalRisk.CRITICAL]
        if critical_geo_risks:
            risks.append(f"{len(critical_geo_risks)} critical geopolitical risks")
        
        return risks
    
    def _identify_opportunities(self, events: List[MacroEvent], 
                               policy: Optional[PolicyAnalysis]) -> List[str]:
        """Identify trading opportunities."""
        opportunities = []
        
        positive_surprises = [e for e in events if e.surprise_index > 0.5]
        if positive_surprises:
            opportunities.append("Positive economic surprises creating momentum")
        
        if policy and policy.confidence_score > 0.8:
            opportunities.append("High confidence in policy direction")
        
        return opportunities
    
    def _calculate_confidence_level(self, events: List[MacroEvent], 
                                   policy: Optional[PolicyAnalysis]) -> float:
        """Calculate overall confidence level in analysis."""
        confidence_factors = []
        
        if events:
            avg_event_confidence = np.mean([0.8 for _ in events])  # Mock confidence
            confidence_factors.append(avg_event_confidence)
        
        if policy:
            confidence_factors.append(policy.confidence_score)
        
        return np.mean(confidence_factors) if confidence_factors else 0.5
