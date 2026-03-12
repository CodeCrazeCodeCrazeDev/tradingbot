"""
Advanced Alternative Data Module
=================================

Comprehensive alternative data processing:
- Web Traffic & App Usage Data
- Satellite Imagery Analysis
- Job Posting & Hiring Data
- Credit Card Transaction Data
- Supply Chain Data
"""

import numpy as np
import pandas as pd
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Tuple
from collections import deque
import logging
from datetime import datetime, timedelta
from abc import ABC, abstractmethod
import json

logger = logging.getLogger(__name__)

# Try importing CV libraries
try:
    import cv2
    CV_AVAILABLE = True
except ImportError:
    CV_AVAILABLE = False


class AltDataSource(Enum):
    """Alternative data sources"""
    WEB_TRAFFIC = "web_traffic"
    APP_USAGE = "app_usage"
    SATELLITE = "satellite"
    JOB_POSTINGS = "job_postings"
    CREDIT_CARD = "credit_card"
    SUPPLY_CHAIN = "supply_chain"
    FOOT_TRAFFIC = "foot_traffic"


class SignalStrength(Enum):
    """Signal strength levels"""
    STRONG_BULLISH = "strong_bullish"
    BULLISH = "bullish"
    WEAK_BULLISH = "weak_bullish"
    NEUTRAL = "neutral"
    WEAK_BEARISH = "weak_bearish"
    BEARISH = "bearish"
    STRONG_BEARISH = "strong_bearish"


@dataclass
class AltDataSignal:
    """Signal from alternative data"""
    timestamp: datetime
    source: AltDataSource
    symbol: str
    signal_strength: SignalStrength
    score: float  # -100 to +100
    confidence: float  # 0 to 1
    lead_time_days: int  # How many days ahead of earnings
    description: str
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class WebTrafficData:
    """Web traffic data point"""
    timestamp: datetime
    domain: str
    visits: int
    unique_visitors: int
    page_views: int
    avg_visit_duration: float  # seconds
    bounce_rate: float
    traffic_sources: Dict[str, float]  # source -> percentage


@dataclass
class SatelliteData:
    """Satellite imagery data"""
    timestamp: datetime
    location: str
    image_type: str  # 'parking_lot', 'oil_storage', 'construction', 'agriculture'
    measurement: float  # Occupancy %, fill level, etc.
    baseline: float
    deviation_pct: float


@dataclass
class JobPostingData:
    """Job posting data"""
    timestamp: datetime
    company: str
    total_postings: int
    new_postings_7d: int
    removed_postings_7d: int
    avg_salary: float
    top_skills: List[str]
    geographic_expansion: List[str]


class WebTrafficAnalyzer:
    """
    Analyzes web traffic data for trading signals
    
    Use cases:
    - Revenue prediction for retail/e-commerce
    - Early detection of trends
    - Cross-verification of company guidance
    """
    
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        
        # Historical data
        self.traffic_history: Dict[str, deque] = {}  # domain -> history
        
        # Baselines
        self.baselines: Dict[str, Dict[str, float]] = {}
        
        # Symbol to domain mapping
        self.symbol_domains: Dict[str, List[str]] = {
            'AMZN': ['amazon.com', 'aws.amazon.com'],
            'GOOGL': ['google.com', 'youtube.com'],
            'META': ['facebook.com', 'instagram.com'],
            'NFLX': ['netflix.com'],
            'SHOP': ['shopify.com'],
            'WMT': ['walmart.com'],
            'TGT': ['target.com'],
            'HD': ['homedepot.com'],
            'LOW': ['lowes.com'],
        }
    
    def add_data(self, data: WebTrafficData):
        """Add web traffic data point"""
        domain = data.domain
        
        if domain not in self.traffic_history:
            self.traffic_history[domain] = deque(maxlen=365)
        
        self.traffic_history[domain].append(data)
        
        # Update baseline
        self._update_baseline(domain)
    
    def _update_baseline(self, domain: str):
        """Update baseline for domain"""
        history = list(self.traffic_history.get(domain, []))
        
        if len(history) < 30:
            return
        
        # Calculate rolling averages
        visits = [d.visits for d in history[-90:]]
        unique = [d.unique_visitors for d in history[-90:]]
        
        self.baselines[domain] = {
            'avg_visits': np.mean(visits),
            'std_visits': np.std(visits),
            'avg_unique': np.mean(unique),
            'std_unique': np.std(unique),
        }
    
    def analyze(self, symbol: str) -> Optional[AltDataSignal]:
        """Analyze web traffic for symbol"""
        domains = self.symbol_domains.get(symbol, [])
        
        if not domains:
            return None
        
        signals = []
        
        for domain in domains:
            if domain not in self.traffic_history:
                continue
            
            history = list(self.traffic_history[domain])
            if len(history) < 7:
                continue
            
            baseline = self.baselines.get(domain, {})
            if not baseline:
                continue
            
            # Calculate recent metrics
            recent = history[-7:]
            recent_visits = np.mean([d.visits for d in recent])
            
            # Calculate deviation
            if baseline['std_visits'] > 0:
                z_score = (recent_visits - baseline['avg_visits']) / baseline['std_visits']
            else:
                z_score = 0
            
            # YoY comparison (if available)
            yoy_growth = 0
            if len(history) >= 365:
                year_ago = history[-365:-358]
                year_ago_visits = np.mean([d.visits for d in year_ago])
                if year_ago_visits > 0:
                    yoy_growth = (recent_visits - year_ago_visits) / year_ago_visits * 100
            
            signals.append({
                'domain': domain,
                'z_score': z_score,
                'yoy_growth': yoy_growth,
                'recent_visits': recent_visits,
            })
        
        if not signals:
            return None
        
        # Aggregate signals
        avg_z_score = np.mean([s['z_score'] for s in signals])
        avg_yoy = np.mean([s['yoy_growth'] for s in signals])
        
        # Determine signal strength
        combined_score = avg_z_score * 20 + avg_yoy * 0.5
        combined_score = np.clip(combined_score, -100, 100)
        
        if combined_score > 50:
            strength = SignalStrength.STRONG_BULLISH
        elif combined_score > 20:
            strength = SignalStrength.BULLISH
        elif combined_score > 5:
            strength = SignalStrength.WEAK_BULLISH
        elif combined_score > -5:
            strength = SignalStrength.NEUTRAL
        elif combined_score > -20:
            strength = SignalStrength.WEAK_BEARISH
        elif combined_score > -50:
            strength = SignalStrength.BEARISH
        else:
            strength = SignalStrength.STRONG_BEARISH
        
        return AltDataSignal(
            timestamp=datetime.now(),
            source=AltDataSource.WEB_TRAFFIC,
            symbol=symbol,
            signal_strength=strength,
            score=combined_score,
            confidence=min(len(signals) / len(domains), 1.0) * 0.7,
            lead_time_days=14,  # Web traffic typically leads by 2 weeks
            description=f"Web traffic z-score: {avg_z_score:.2f}, YoY: {avg_yoy:.1f}%",
            metadata={
                'domains_analyzed': len(signals),
                'avg_z_score': avg_z_score,
                'yoy_growth': avg_yoy,
            },
        )


class SatelliteImageryAnalyzer:
    """
    Analyzes satellite imagery for trading signals
    
    Applications:
    - Parking lot occupancy (retail activity)
    - Oil storage tank levels (energy markets)
    - Construction activity (industrial/materials)
    - Agricultural yield estimation (commodities)
    """
    
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        
        # Historical data
        self.satellite_history: Dict[str, deque] = {}  # location -> history
        
        # Location to symbol mapping
        self.location_symbols: Dict[str, str] = {}
        
        # Baselines
        self.baselines: Dict[str, Dict[str, float]] = {}
    
    def add_data(self, data: SatelliteData):
        """Add satellite data point"""
        location = data.location
        
        if location not in self.satellite_history:
            self.satellite_history[location] = deque(maxlen=365)
        
        self.satellite_history[location].append(data)
        self._update_baseline(location)
    
    def _update_baseline(self, location: str):
        """Update baseline for location"""
        history = list(self.satellite_history.get(location, []))
        
        if len(history) < 30:
            return
        
        measurements = [d.measurement for d in history[-90:]]
        
        self.baselines[location] = {
            'mean': np.mean(measurements),
            'std': np.std(measurements),
            'min': np.min(measurements),
            'max': np.max(measurements),
        }
    
    def analyze_parking_lots(self, symbol: str, locations: List[str]) -> Optional[AltDataSignal]:
        """Analyze parking lot occupancy for retail"""
        signals = []
        
        for location in locations:
            if location not in self.satellite_history:
                continue
            
            history = list(self.satellite_history[location])
            if len(history) < 7:
                continue
            
            baseline = self.baselines.get(location, {})
            if not baseline:
                continue
            
            # Recent occupancy
            recent = history[-7:]
            recent_occupancy = np.mean([d.measurement for d in recent])
            
            # Deviation from baseline
            if baseline['std'] > 0:
                z_score = (recent_occupancy - baseline['mean']) / baseline['std']
            else:
                z_score = 0
            
            signals.append({
                'location': location,
                'occupancy': recent_occupancy,
                'z_score': z_score,
            })
        
        if not signals:
            return None
        
        avg_z_score = np.mean([s['z_score'] for s in signals])
        avg_occupancy = np.mean([s['occupancy'] for s in signals])
        
        # Higher occupancy = more foot traffic = bullish for retail
        score = avg_z_score * 25
        score = np.clip(score, -100, 100)
        
        strength = self._score_to_strength(score)
        
        return AltDataSignal(
            timestamp=datetime.now(),
            source=AltDataSource.SATELLITE,
            symbol=symbol,
            signal_strength=strength,
            score=score,
            confidence=0.75,
            lead_time_days=21,  # Satellite data typically leads by 3 weeks
            description=f"Parking lot occupancy: {avg_occupancy:.1f}%, z-score: {avg_z_score:.2f}",
            metadata={
                'locations_analyzed': len(signals),
                'avg_occupancy': avg_occupancy,
                'avg_z_score': avg_z_score,
            },
        )
    
    def analyze_oil_storage(self, locations: List[str]) -> Optional[AltDataSignal]:
        """Analyze oil storage tank levels"""
        signals = []
        
        for location in locations:
            if location not in self.satellite_history:
                continue
            
            history = list(self.satellite_history[location])
            if len(history) < 7:
                continue
            
            baseline = self.baselines.get(location, {})
            if not baseline:
                continue
            
            # Recent fill level
            recent = history[-7:]
            recent_fill = np.mean([d.measurement for d in recent])
            
            # Week-over-week change
            if len(history) >= 14:
                prev_week = history[-14:-7]
                prev_fill = np.mean([d.measurement for d in prev_week])
                wow_change = recent_fill - prev_fill
            else:
                wow_change = 0
            
            signals.append({
                'location': location,
                'fill_level': recent_fill,
                'wow_change': wow_change,
            })
        
        if not signals:
            return None
        
        avg_fill = np.mean([s['fill_level'] for s in signals])
        avg_change = np.mean([s['wow_change'] for s in signals])
        
        # Inventory buildup = bearish for oil prices
        # Inventory drawdown = bullish for oil prices
        score = -avg_change * 10  # Invert: drawdown is bullish
        score = np.clip(score, -100, 100)
        
        strength = self._score_to_strength(score)
        
        return AltDataSignal(
            timestamp=datetime.now(),
            source=AltDataSource.SATELLITE,
            symbol='CL',  # Crude oil
            signal_strength=strength,
            score=score,
            confidence=0.8,
            lead_time_days=7,
            description=f"Oil storage fill: {avg_fill:.1f}%, WoW change: {avg_change:+.1f}%",
            metadata={
                'locations_analyzed': len(signals),
                'avg_fill_level': avg_fill,
                'wow_change': avg_change,
            },
        )
    
    def _score_to_strength(self, score: float) -> SignalStrength:
        """Convert score to signal strength"""
        if score > 50:
            return SignalStrength.STRONG_BULLISH
        elif score > 20:
            return SignalStrength.BULLISH
        elif score > 5:
            return SignalStrength.WEAK_BULLISH
        elif score > -5:
            return SignalStrength.NEUTRAL
        elif score > -20:
            return SignalStrength.WEAK_BEARISH
        elif score > -50:
            return SignalStrength.BEARISH
        else:
            return SignalStrength.STRONG_BEARISH


class JobPostingAnalyzer:
    """
    Analyzes job posting data for trading signals
    
    Indicators:
    - Company hiring velocity (growth/contraction)
    - Salary trends (margin pressure)
    - Skill requirements (strategic pivots)
    - Geographic expansion
    """
    
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        
        # Historical data
        self.posting_history: Dict[str, deque] = {}  # company -> history
        
        # Baselines
        self.baselines: Dict[str, Dict[str, float]] = {}
    
    def add_data(self, data: JobPostingData):
        """Add job posting data"""
        company = data.company
        
        if company not in self.posting_history:
            self.posting_history[company] = deque(maxlen=52)  # Weekly data for 1 year
        
        self.posting_history[company].append(data)
        self._update_baseline(company)
    
    def _update_baseline(self, company: str):
        """Update baseline for company"""
        history = list(self.posting_history.get(company, []))
        
        if len(history) < 12:
            return
        
        postings = [d.total_postings for d in history]
        salaries = [d.avg_salary for d in history if d.avg_salary > 0]
        
        self.baselines[company] = {
            'avg_postings': np.mean(postings),
            'std_postings': np.std(postings),
            'avg_salary': np.mean(salaries) if salaries else 0,
        }
    
    def analyze(self, symbol: str, company: str) -> Optional[AltDataSignal]:
        """Analyze job postings for company"""
        if company not in self.posting_history:
            return None
        
        history = list(self.posting_history[company])
        if len(history) < 4:
            return None
        
        baseline = self.baselines.get(company, {})
        
        # Recent data
        recent = history[-4:]  # Last 4 weeks
        
        # Hiring velocity
        recent_postings = np.mean([d.total_postings for d in recent])
        net_new = sum(d.new_postings_7d - d.removed_postings_7d for d in recent)
        
        # Compare to baseline
        if baseline and baseline['std_postings'] > 0:
            z_score = (recent_postings - baseline['avg_postings']) / baseline['std_postings']
        else:
            z_score = 0
        
        # Salary trend
        salaries = [d.avg_salary for d in history if d.avg_salary > 0]
        if len(salaries) >= 12:
            recent_salary = np.mean(salaries[-4:])
            older_salary = np.mean(salaries[-12:-4])
            salary_change = (recent_salary - older_salary) / older_salary * 100 if older_salary > 0 else 0
        else:
            salary_change = 0
        
        # Geographic expansion
        recent_expansion = set()
        for d in recent:
            recent_expansion.update(d.geographic_expansion)
        expansion_score = len(recent_expansion) * 5
        
        # Combined score
        # Aggressive hiring = bullish growth signal
        # But high salary increases = margin pressure (slightly bearish)
        score = z_score * 20 + net_new * 0.5 + expansion_score - salary_change * 0.3
        score = np.clip(score, -100, 100)
        
        strength = self._score_to_strength(score)
        
        return AltDataSignal(
            timestamp=datetime.now(),
            source=AltDataSource.JOB_POSTINGS,
            symbol=symbol,
            signal_strength=strength,
            score=score,
            confidence=0.65,
            lead_time_days=30,  # Job data typically leads by 1 month
            description=f"Hiring velocity z-score: {z_score:.2f}, net new: {net_new}, salary change: {salary_change:.1f}%",
            metadata={
                'z_score': z_score,
                'net_new_postings': net_new,
                'salary_change_pct': salary_change,
                'geographic_expansion': list(recent_expansion),
            },
        )
    
    def _score_to_strength(self, score: float) -> SignalStrength:
        """Convert score to signal strength"""
        if score > 50:
            return SignalStrength.STRONG_BULLISH
        elif score > 20:
            return SignalStrength.BULLISH
        elif score > 5:
            return SignalStrength.WEAK_BULLISH
        elif score > -5:
            return SignalStrength.NEUTRAL
        elif score > -20:
            return SignalStrength.WEAK_BEARISH
        elif score > -50:
            return SignalStrength.BEARISH
        else:
            return SignalStrength.STRONG_BEARISH


class CreditCardAnalyzer:
    """
    Analyzes credit card transaction data
    
    Use cases:
    - Consumer spending trends
    - Retail revenue prediction
    - Category-level insights
    """
    
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        
        # Historical data
        self.transaction_history: Dict[str, deque] = {}  # merchant -> history
        
        # Baselines
        self.baselines: Dict[str, Dict[str, float]] = {}
    
    def add_data(self, merchant: str, timestamp: datetime, 
                transaction_count: int, total_spend: float,
                avg_ticket: float):
        """Add credit card transaction data"""
        if merchant not in self.transaction_history:
            self.transaction_history[merchant] = deque(maxlen=365)
        
        self.transaction_history[merchant].append({
            'timestamp': timestamp,
            'transaction_count': transaction_count,
            'total_spend': total_spend,
            'avg_ticket': avg_ticket,
        })
        
        self._update_baseline(merchant)
    
    def _update_baseline(self, merchant: str):
        """Update baseline for merchant"""
        history = list(self.transaction_history.get(merchant, []))
        
        if len(history) < 30:
            return
        
        spend = [d['total_spend'] for d in history[-90:]]
        tickets = [d['avg_ticket'] for d in history[-90:]]
        
        self.baselines[merchant] = {
            'avg_spend': np.mean(spend),
            'std_spend': np.std(spend),
            'avg_ticket': np.mean(tickets),
        }
    
    def analyze(self, symbol: str, merchant: str) -> Optional[AltDataSignal]:
        """Analyze credit card data for merchant"""
        if merchant not in self.transaction_history:
            return None
        
        history = list(self.transaction_history[merchant])
        if len(history) < 14:
            return None
        
        baseline = self.baselines.get(merchant, {})
        if not baseline:
            return None
        
        # Recent metrics
        recent = history[-7:]
        recent_spend = np.mean([d['total_spend'] for d in recent])
        recent_ticket = np.mean([d['avg_ticket'] for d in recent])
        
        # Z-score
        if baseline['std_spend'] > 0:
            z_score = (recent_spend - baseline['avg_spend']) / baseline['std_spend']
        else:
            z_score = 0
        
        # YoY comparison
        if len(history) >= 365:
            year_ago = history[-365:-358]
            yoy_spend = np.mean([d['total_spend'] for d in year_ago])
            yoy_growth = (recent_spend - yoy_spend) / yoy_spend * 100 if yoy_spend > 0 else 0
        else:
            yoy_growth = 0
        
        # Ticket size trend
        ticket_change = (recent_ticket - baseline['avg_ticket']) / baseline['avg_ticket'] * 100
        
        # Combined score
        score = z_score * 20 + yoy_growth * 0.5 + ticket_change * 0.3
        score = np.clip(score, -100, 100)
        
        strength = self._score_to_strength(score)
        
        return AltDataSignal(
            timestamp=datetime.now(),
            source=AltDataSource.CREDIT_CARD,
            symbol=symbol,
            signal_strength=strength,
            score=score,
            confidence=0.8,
            lead_time_days=7,
            description=f"Spend z-score: {z_score:.2f}, YoY: {yoy_growth:.1f}%, ticket change: {ticket_change:.1f}%",
            metadata={
                'z_score': z_score,
                'yoy_growth': yoy_growth,
                'ticket_change': ticket_change,
            },
        )
    
    def _score_to_strength(self, score: float) -> SignalStrength:
        """Convert score to signal strength"""
        if score > 50:
            return SignalStrength.STRONG_BULLISH
        elif score > 20:
            return SignalStrength.BULLISH
        elif score > 5:
            return SignalStrength.WEAK_BULLISH
        elif score > -5:
            return SignalStrength.NEUTRAL
        elif score > -20:
            return SignalStrength.WEAK_BEARISH
        elif score > -50:
            return SignalStrength.BEARISH
        else:
            return SignalStrength.STRONG_BEARISH


class ComprehensiveAltDataProcessor:
    """
    Comprehensive alternative data processor
    
    Aggregates signals from all alternative data sources
    """
    
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        
        # Initialize analyzers
        self.web_traffic = WebTrafficAnalyzer(config.get('web_traffic', {}))
        self.satellite = SatelliteImageryAnalyzer(config.get('satellite', {}))
        self.job_postings = JobPostingAnalyzer(config.get('job_postings', {}))
        self.credit_card = CreditCardAnalyzer(config.get('credit_card', {}))
        
        # Source weights
        self.source_weights = {
            AltDataSource.WEB_TRAFFIC: 0.25,
            AltDataSource.SATELLITE: 0.25,
            AltDataSource.JOB_POSTINGS: 0.20,
            AltDataSource.CREDIT_CARD: 0.30,
        }
        
        # Signal history
        self.signal_history: Dict[str, deque] = {}
    
    def get_aggregated_signal(self, symbol: str, 
                             company: str = None,
                             locations: List[str] = None) -> Dict[str, Any]:
        """
        Get aggregated alternative data signal
        
        Args:
            symbol: Trading symbol
            company: Company name for job postings
            locations: Locations for satellite analysis
            
        Returns:
            Aggregated signal dictionary
        """
        signals = []
        
        # Web traffic
        web_signal = self.web_traffic.analyze(symbol)
        if web_signal:
            signals.append(web_signal)
        
        # Satellite (parking lots for retail)
        if locations:
            sat_signal = self.satellite.analyze_parking_lots(symbol, locations)
            if sat_signal:
                signals.append(sat_signal)
        
        # Job postings
        if company:
            job_signal = self.job_postings.analyze(symbol, company)
            if job_signal:
                signals.append(job_signal)
        
        # Credit card (would need merchant mapping)
        # credit_signal = self.credit_card.analyze(symbol, merchant)
        
        if not signals:
            return {
                'symbol': symbol,
                'composite_score': 0,
                'confidence': 0,
                'signal_count': 0,
                'recommendation': 'neutral',
            }
        
        # Weighted aggregation
        total_weight = 0
        weighted_score = 0
        
        for signal in signals:
            weight = self.source_weights.get(signal.source, 0.2) * signal.confidence
            weighted_score += signal.score * weight
            total_weight += weight
        
        if total_weight > 0:
            composite_score = weighted_score / total_weight
        else:
            composite_score = 0
        
        # Determine recommendation
        if composite_score > 30:
            recommendation = 'bullish'
            position_adjustment = 1.1 + (composite_score - 30) / 100
        elif composite_score < -30:
            recommendation = 'bearish'
            position_adjustment = 0.9 - (abs(composite_score) - 30) / 100
        else:
            recommendation = 'neutral'
            position_adjustment = 1.0
        
        # Store signal
        if symbol not in self.signal_history:
            self.signal_history[symbol] = deque(maxlen=100)
        
        result = {
            'symbol': symbol,
            'timestamp': datetime.now(),
            'composite_score': composite_score,
            'confidence': total_weight / len(signals) if signals else 0,
            'signal_count': len(signals),
            'recommendation': recommendation,
            'position_adjustment': position_adjustment,
            'individual_signals': [
                {
                    'source': s.source.value,
                    'score': s.score,
                    'confidence': s.confidence,
                    'lead_time_days': s.lead_time_days,
                    'description': s.description,
                }
                for s in signals
            ],
        }
        
        self.signal_history[symbol].append(result)
        
        return result
    
    def get_trading_recommendation(self, symbol: str) -> Dict[str, Any]:
        """
        Get trading recommendation based on alternative data
        
        Returns:
            Recommendation with position sizing adjustment
        """
        signal = self.get_aggregated_signal(symbol)
        
        return {
            'symbol': symbol,
            'direction': signal['recommendation'],
            'position_multiplier': signal['position_adjustment'],
            'confidence': signal['confidence'],
            'reasoning': f"Alt data composite score: {signal['composite_score']:.1f} from {signal['signal_count']} sources",
        }
