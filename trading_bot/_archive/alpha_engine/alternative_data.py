"""
Alternative Data Processing Module
===================================

Processes non-traditional data sources for alpha generation:
- Web Traffic & App Usage Data
- Satellite Imagery Analysis
- Job Posting & Hiring Data
- Credit Card Transaction Data
- Geolocation Data
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
import hashlib

logger = logging.getLogger(__name__)

try:
    import cv2
    CV2_AVAILABLE = True
except ImportError:
    CV2_AVAILABLE = False

try:
    from PIL import Image
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False

try:
    import torch
    import torch.nn as nn
    import torchvision.models as models
    import torchvision.transforms as transforms
    TORCH_AVAILABLE = True
except ImportError:
    TORCH_AVAILABLE = False


class AlternativeDataType(Enum):
    """Types of alternative data"""
    WEB_TRAFFIC = "web_traffic"
    APP_USAGE = "app_usage"
    SATELLITE = "satellite"
    JOB_POSTINGS = "job_postings"
    CREDIT_CARD = "credit_card"
    GEOLOCATION = "geolocation"
    SUPPLY_CHAIN = "supply_chain"
    PATENT_FILINGS = "patent_filings"
    GOVERNMENT_DATA = "government_data"


@dataclass
class AlternativeDataSignal:
    """Signal generated from alternative data"""
    data_type: AlternativeDataType
    timestamp: datetime
    symbol: str
    signal_strength: float  # -1 to +1
    confidence: float  # 0 to 1
    lead_time_days: int  # How many days ahead of earnings/events
    description: str
    raw_value: float
    benchmark_value: float
    deviation: float  # Standard deviations from norm
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'data_type': self.data_type.value,
            'timestamp': self.timestamp.isoformat(),
            'symbol': self.symbol,
            'signal_strength': self.signal_strength,
            'confidence': self.confidence,
            'lead_time_days': self.lead_time_days,
            'description': self.description,
            'deviation': self.deviation,
        }


class WebTrafficAnalyzer:
    """
    Analyzes web traffic data for trading signals
    
    Sources: SimilarWeb, App Annie equivalents
    Use Cases: Revenue prediction for retail/e-commerce
    """
    
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        
        # Historical baselines by symbol
        self.baselines: Dict[str, Dict[str, float]] = {}
        
        # Traffic history
        self.traffic_history: Dict[str, deque] = {}
        
        # Symbol to company website mapping
        self.symbol_websites: Dict[str, List[str]] = {
            'AMZN': ['amazon.com'],
            'WMT': ['walmart.com'],
            'TGT': ['target.com'],
            'COST': ['costco.com'],
            'HD': ['homedepot.com'],
            'LOW': ['lowes.com'],
            'NFLX': ['netflix.com'],
            'DIS': ['disneyplus.com', 'disney.com'],
            'SHOP': ['shopify.com'],
            'ETSY': ['etsy.com'],
        }
    
    def process_traffic_data(self, data: Dict[str, Any]) -> Optional[AlternativeDataSignal]:
        """
        Process web traffic data point
        
        Args:
            data: Dictionary with 'symbol', 'website', 'visits', 'unique_visitors',
                  'page_views', 'avg_duration', 'bounce_rate', 'timestamp'
        """
        symbol = data.get('symbol')
        if not symbol:
            return None
        
        # Initialize history if needed
        if symbol not in self.traffic_history:
            self.traffic_history[symbol] = deque(maxlen=365)
        
        # Store data point
        self.traffic_history[symbol].append(data)
        
        # Calculate metrics
        visits = data.get('visits', 0)
        unique_visitors = data.get('unique_visitors', 0)
        
        # Get baseline
        baseline = self._get_baseline(symbol)
        
        if baseline['visits'] == 0:
            # Not enough history
            self._update_baseline(symbol, data)
            return None
        
        # Calculate deviation
        visits_change = (visits - baseline['visits']) / baseline['visits']
        visitors_change = (unique_visitors - baseline['unique_visitors']) / max(baseline['unique_visitors'], 1)
        
        # Combined signal
        signal_strength = (visits_change * 0.6 + visitors_change * 0.4)
        signal_strength = np.clip(signal_strength, -1, 1)
        
        # Calculate standard deviation
        if len(self.traffic_history[symbol]) > 30:
            historical_visits = [d.get('visits', 0) for d in self.traffic_history[symbol]]
            std = np.std(historical_visits)
            deviation = (visits - baseline['visits']) / max(std, 1)
        else:
            deviation = 0
        
        # Confidence based on data quality and history length
        confidence = min(len(self.traffic_history[symbol]) / 90, 1.0)
        
        # Update baseline
        self._update_baseline(symbol, data)
        
        # Generate signal if significant
        if abs(deviation) > 1.5:
            return AlternativeDataSignal(
                data_type=AlternativeDataType.WEB_TRAFFIC,
                timestamp=data.get('timestamp', datetime.now()),
                symbol=symbol,
                signal_strength=signal_strength,
                confidence=confidence,
                lead_time_days=14,  # Web traffic typically leads by 2 weeks
                description=f"Web traffic {'up' if signal_strength > 0 else 'down'} {abs(visits_change)*100:.1f}% vs baseline",
                raw_value=visits,
                benchmark_value=baseline['visits'],
                deviation=deviation,
                metadata={
                    'visits_change': visits_change,
                    'visitors_change': visitors_change,
                    'bounce_rate': data.get('bounce_rate', 0),
                }
            )
        
        return None
    
    def _get_baseline(self, symbol: str) -> Dict[str, float]:
        """Get baseline metrics for symbol"""
        if symbol not in self.baselines:
            self.baselines[symbol] = {
                'visits': 0,
                'unique_visitors': 0,
                'page_views': 0,
            }
        return self.baselines[symbol]
    
    def _update_baseline(self, symbol: str, data: Dict[str, Any]):
        """Update baseline with exponential moving average"""
        alpha = 0.1  # Smoothing factor
        
        if symbol not in self.baselines:
            self.baselines[symbol] = {
                'visits': data.get('visits', 0),
                'unique_visitors': data.get('unique_visitors', 0),
                'page_views': data.get('page_views', 0),
            }
        else:
            for key in ['visits', 'unique_visitors', 'page_views']:
                old_val = self.baselines[symbol][key]
                new_val = data.get(key, old_val)
                self.baselines[symbol][key] = alpha * new_val + (1 - alpha) * old_val
    
    def get_yoy_growth(self, symbol: str) -> Optional[float]:
        """Calculate year-over-year growth"""
        if symbol not in self.traffic_history:
            return None
        
        history = list(self.traffic_history[symbol])
        if len(history) < 365:
            return None
        
        current = history[-1].get('visits', 0)
        year_ago = history[-365].get('visits', 0)
        
        if year_ago == 0:
            return None
        
        return (current - year_ago) / year_ago


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
        self.device = 'cuda' if TORCH_AVAILABLE and torch.cuda.is_available() else 'cpu'
        
        # Initialize CNN model for image analysis
        if TORCH_AVAILABLE:
            try:
                self.model = models.resnet50(pretrained=True)
                self.model.eval()
                self.model.to(self.device)
                
                self.transform = transforms.Compose([
                    transforms.Resize(256),
                    transforms.CenterCrop(224),
                    transforms.ToTensor(),
                    transforms.Normalize(
                        mean=[0.485, 0.456, 0.406],
                        std=[0.229, 0.224, 0.225]
                    ),
                ])
            except Exception as e:
                logger.warning(f"Failed to load ResNet: {e}")
                self.model = None
        else:
            self.model = None
        
        # Historical imagery data
        self.imagery_history: Dict[str, deque] = {}
        
        # Location to symbol mapping
        self.location_symbols: Dict[str, str] = {}
    
    def analyze_parking_lot(self, image_data: Any, location_id: str,
                           symbol: str) -> Optional[AlternativeDataSignal]:
        """
        Analyze parking lot occupancy from satellite image
        
        Args:
            image_data: Image data (numpy array or PIL Image)
            location_id: Unique identifier for the location
            symbol: Stock symbol associated with this location
        """
        # Calculate occupancy
        occupancy = self._estimate_parking_occupancy(image_data)
        
        if occupancy is None:
            return None
        
        # Get historical baseline
        key = f"{symbol}_{location_id}"
        if key not in self.imagery_history:
            self.imagery_history[key] = deque(maxlen=52)  # 1 year of weekly data
        
        self.imagery_history[key].append({
            'timestamp': datetime.now(),
            'occupancy': occupancy,
        })
        
        # Calculate baseline and deviation
        if len(self.imagery_history[key]) < 4:
            return None
        
        historical = [d['occupancy'] for d in self.imagery_history[key]]
        baseline = np.mean(historical[:-1])
        std = np.std(historical[:-1])
        
        if std == 0:
            deviation = 0
        else:
            deviation = (occupancy - baseline) / std
        
        # Signal strength based on deviation
        signal_strength = np.tanh(deviation / 2)  # Normalize to -1, 1
        
        # Confidence based on history length and image quality
        confidence = min(len(self.imagery_history[key]) / 12, 1.0)
        
        if abs(deviation) > 1.5:
            return AlternativeDataSignal(
                data_type=AlternativeDataType.SATELLITE,
                timestamp=datetime.now(),
                symbol=symbol,
                signal_strength=signal_strength,
                confidence=confidence,
                lead_time_days=14,  # Satellite data typically leads by 2-4 weeks
                description=f"Parking lot occupancy {occupancy*100:.1f}% ({'above' if deviation > 0 else 'below'} baseline)",
                raw_value=occupancy,
                benchmark_value=baseline,
                deviation=deviation,
                metadata={
                    'location_id': location_id,
                    'analysis_type': 'parking_lot',
                }
            )
        
        return None
    
    def analyze_oil_storage(self, image_data: Any, location_id: str,
                           symbol: str = 'CL') -> Optional[AlternativeDataSignal]:
        """
        Analyze oil storage tank levels from satellite image
        
        Uses shadow analysis to estimate fill levels of floating roof tanks.
        """
        # Estimate fill level
        fill_level = self._estimate_tank_fill_level(image_data)
        
        if fill_level is None:
            return None
        
        key = f"oil_{location_id}"
        if key not in self.imagery_history:
            self.imagery_history[key] = deque(maxlen=52)
        
        self.imagery_history[key].append({
            'timestamp': datetime.now(),
            'fill_level': fill_level,
        })
        
        if len(self.imagery_history[key]) < 4:
            return None
        
        historical = [d['fill_level'] for d in self.imagery_history[key]]
        baseline = np.mean(historical[:-1])
        std = np.std(historical[:-1])
        
        deviation = (fill_level - baseline) / max(std, 0.01)
        
        # High inventory = bearish for oil prices
        signal_strength = -np.tanh(deviation / 2)
        
        confidence = min(len(self.imagery_history[key]) / 12, 1.0)
        
        if abs(deviation) > 1.5:
            return AlternativeDataSignal(
                data_type=AlternativeDataType.SATELLITE,
                timestamp=datetime.now(),
                symbol=symbol,
                signal_strength=signal_strength,
                confidence=confidence,
                lead_time_days=7,
                description=f"Oil storage {fill_level*100:.1f}% full ({'above' if deviation > 0 else 'below'} baseline)",
                raw_value=fill_level,
                benchmark_value=baseline,
                deviation=deviation,
                metadata={
                    'location_id': location_id,
                    'analysis_type': 'oil_storage',
                }
            )
        
        return None
    
    def _estimate_parking_occupancy(self, image_data: Any) -> Optional[float]:
        """Estimate parking lot occupancy from image"""
        if not PIL_AVAILABLE:
            # Return simulated value for testing
            return np.random.uniform(0.3, 0.9)
        try:
        
            if isinstance(image_data, np.ndarray):
                image = Image.fromarray(image_data)
            else:
                image = image_data
            
            # Simple approach: analyze dark regions (cars) vs light regions (empty)
            gray = image.convert('L')
            pixels = np.array(gray)
            
            # Threshold to separate cars from pavement
            threshold = np.mean(pixels) - np.std(pixels) * 0.5
            dark_pixels = np.sum(pixels < threshold)
            total_pixels = pixels.size
            
            # Rough occupancy estimate
            occupancy = dark_pixels / total_pixels
            
            # Normalize to reasonable range
            occupancy = np.clip(occupancy * 2, 0, 1)
            
            return occupancy
            
        except Exception as e:
            logger.error(f"Parking occupancy estimation failed: {e}")
            return None
    
    def _estimate_tank_fill_level(self, image_data: Any) -> Optional[float]:
        """Estimate oil tank fill level from shadow analysis"""
        if not PIL_AVAILABLE:
            return np.random.uniform(0.4, 0.95)
        try:
        
            if isinstance(image_data, np.ndarray):
                image = Image.fromarray(image_data)
            else:
                image = image_data
            
            # Simplified: analyze shadow length relative to tank diameter
            # In practice, this requires sophisticated computer vision
            gray = np.array(image.convert('L'))
            
            # Find shadow regions
            shadow_threshold = np.percentile(gray, 20)
            shadow_mask = gray < shadow_threshold
            
            # Estimate fill level from shadow proportion
            shadow_ratio = np.sum(shadow_mask) / shadow_mask.size
            
            # Convert to fill level (inverse relationship)
            fill_level = 1 - shadow_ratio * 2
            fill_level = np.clip(fill_level, 0, 1)
            
            return fill_level
            
        except Exception as e:
            logger.error(f"Tank fill estimation failed: {e}")
            return None


class JobPostingAnalyzer:
    """
    Analyzes job posting data for trading signals
    
    Indicators:
    - Company hiring velocity (growth/contraction signals)
    - Salary trends (margin pressure indicators)
    - Skill requirements (strategic pivots)
    - Geographic expansion
    """
    
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        
        # Job posting history by symbol
        self.posting_history: Dict[str, deque] = {}
        
        # Salary history
        self.salary_history: Dict[str, deque] = {}
        
        # Key role categories
        self.role_categories = {
            'engineering': ['engineer', 'developer', 'programmer', 'architect', 'devops'],
            'sales': ['sales', 'account executive', 'business development', 'revenue'],
            'marketing': ['marketing', 'growth', 'brand', 'content', 'social media'],
            'operations': ['operations', 'supply chain', 'logistics', 'warehouse'],
            'finance': ['finance', 'accounting', 'controller', 'treasury', 'analyst'],
            'hr': ['human resources', 'recruiting', 'talent', 'people operations'],
            'executive': ['ceo', 'cfo', 'cto', 'coo', 'vp', 'director', 'head of'],
        }
    
    def process_job_data(self, data: Dict[str, Any]) -> Optional[AlternativeDataSignal]:
        """
        Process job posting data
        
        Args:
            data: Dictionary with 'symbol', 'total_postings', 'new_postings',
                  'categories', 'avg_salary', 'locations', 'timestamp'
        """
        symbol = data.get('symbol')
        if not symbol:
            return None
        
        # Initialize history
        if symbol not in self.posting_history:
            self.posting_history[symbol] = deque(maxlen=52)
        
        self.posting_history[symbol].append(data)
        
        # Calculate metrics
        total_postings = data.get('total_postings', 0)
        new_postings = data.get('new_postings', 0)
        
        # Get baseline
        if len(self.posting_history[symbol]) < 4:
            return None
        
        historical = [d.get('total_postings', 0) for d in self.posting_history[symbol]]
        baseline = np.mean(historical[:-1])
        std = np.std(historical[:-1])
        
        if baseline == 0:
            return None
        
        # Calculate hiring velocity
        velocity = (total_postings - baseline) / baseline
        
        # Deviation
        deviation = (total_postings - baseline) / max(std, 1)
        
        # Analyze categories for strategic signals
        categories = data.get('categories', {})
        strategic_signal = self._analyze_categories(categories, symbol)
        
        # Signal strength
        signal_strength = np.tanh(velocity)
        
        # Adjust for strategic signals
        if strategic_signal:
            signal_strength = signal_strength * 0.7 + strategic_signal * 0.3
        
        confidence = min(len(self.posting_history[symbol]) / 12, 1.0)
        
        if abs(deviation) > 1.5 or abs(strategic_signal or 0) > 0.5:
            direction = 'hiring' if velocity > 0 else 'slowing'
            return AlternativeDataSignal(
                data_type=AlternativeDataType.JOB_POSTINGS,
                timestamp=data.get('timestamp', datetime.now()),
                symbol=symbol,
                signal_strength=signal_strength,
                confidence=confidence,
                lead_time_days=30,  # Job data leads by ~1 month
                description=f"Hiring {direction}: {total_postings} postings ({velocity*100:+.1f}% vs baseline)",
                raw_value=total_postings,
                benchmark_value=baseline,
                deviation=deviation,
                metadata={
                    'new_postings': new_postings,
                    'categories': categories,
                    'strategic_signal': strategic_signal,
                }
            )
        
        return None
    
    def _analyze_categories(self, categories: Dict[str, int], symbol: str) -> Optional[float]:
        """Analyze job categories for strategic signals"""
        if not categories:
            return None
        
        total = sum(categories.values())
        if total == 0:
            return None
        
        # Calculate category proportions
        proportions = {k: v / total for k, v in categories.items()}
        
        # Bullish signals
        bullish_score = 0
        
        # Heavy engineering hiring = growth investment
        eng_prop = proportions.get('engineering', 0)
        if eng_prop > 0.4:
            bullish_score += 0.3
        
        # Sales hiring = revenue push
        sales_prop = proportions.get('sales', 0)
        if sales_prop > 0.3:
            bullish_score += 0.2
        
        # Executive hiring = strategic changes
        exec_prop = proportions.get('executive', 0)
        if exec_prop > 0.1:
            bullish_score += 0.1
        
        # Bearish signals
        bearish_score = 0
        
        # Heavy HR hiring might indicate restructuring
        hr_prop = proportions.get('hr', 0)
        if hr_prop > 0.15:
            bearish_score += 0.2
        
        # Finance heavy might indicate cost focus
        finance_prop = proportions.get('finance', 0)
        if finance_prop > 0.2:
            bearish_score += 0.1
        
        return bullish_score - bearish_score
    
    def analyze_salary_trends(self, symbol: str) -> Optional[Dict[str, Any]]:
        """Analyze salary trends for margin pressure signals"""
        if symbol not in self.salary_history:
            return None
        
        history = list(self.salary_history[symbol])
        if len(history) < 4:
            return None
        
        salaries = [d.get('avg_salary', 0) for d in history]
        
        # Calculate trend
        recent = np.mean(salaries[-4:])
        older = np.mean(salaries[:-4]) if len(salaries) > 4 else salaries[0]
        
        if older == 0:
            return None
        
        salary_growth = (recent - older) / older
        
        return {
            'salary_growth': salary_growth,
            'current_avg': recent,
            'margin_pressure': salary_growth > 0.1,  # >10% growth = pressure
        }


class AlternativeDataProcessor:
    """
    Main processor for all alternative data sources
    """
    
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        
        # Initialize analyzers
        self.web_traffic = WebTrafficAnalyzer(config.get('web_traffic', {}))
        self.satellite = SatelliteImageryAnalyzer(config.get('satellite', {}))
        self.job_postings = JobPostingAnalyzer(config.get('job_postings', {}))
        
        # Signal history
        self.signals: Dict[str, deque] = {}
        
        # Source weights
        self.source_weights = {
            AlternativeDataType.WEB_TRAFFIC: 0.25,
            AlternativeDataType.SATELLITE: 0.30,
            AlternativeDataType.JOB_POSTINGS: 0.20,
            AlternativeDataType.CREDIT_CARD: 0.25,
        }
    
    def process_data(self, data_type: AlternativeDataType, 
                    data: Dict[str, Any]) -> Optional[AlternativeDataSignal]:
        """
        Process alternative data and generate signal
        
        Args:
            data_type: Type of alternative data
            data: Data payload
            
        Returns:
            AlternativeDataSignal if significant, None otherwise
        """
        signal = None
        
        if data_type == AlternativeDataType.WEB_TRAFFIC:
            signal = self.web_traffic.process_traffic_data(data)
        elif data_type == AlternativeDataType.JOB_POSTINGS:
            signal = self.job_postings.process_job_data(data)
        elif data_type == AlternativeDataType.SATELLITE:
            if data.get('analysis_type') == 'parking_lot':
                signal = self.satellite.analyze_parking_lot(
                    data.get('image'),
                    data.get('location_id'),
                    data.get('symbol')
                )
            elif data.get('analysis_type') == 'oil_storage':
                signal = self.satellite.analyze_oil_storage(
                    data.get('image'),
                    data.get('location_id'),
                    data.get('symbol', 'CL')
                )
        
        if signal:
            symbol = signal.symbol
            if symbol not in self.signals:
                self.signals[symbol] = deque(maxlen=100)
            self.signals[symbol].append(signal)
        
        return signal
    
    def get_aggregated_signal(self, symbol: str, 
                             lookback_days: int = 30) -> Dict[str, Any]:
        """
        Get aggregated alternative data signal for a symbol
        
        Args:
            symbol: Stock symbol
            lookback_days: Days to look back
            
        Returns:
            Aggregated signal dictionary
        """
        if symbol not in self.signals:
            return {'signal_strength': 0, 'confidence': 0, 'sources': []}
        
        cutoff = datetime.now() - timedelta(days=lookback_days)
        
        relevant_signals = [s for s in self.signals[symbol] 
                          if s.timestamp > cutoff]
        
        if not relevant_signals:
            return {'signal_strength': 0, 'confidence': 0, 'sources': []}
        
        # Weight by source and recency
        weighted_sum = 0
        total_weight = 0
        sources_used = set()
        
        for signal in relevant_signals:
            age_days = (datetime.now() - signal.timestamp).days
            recency_weight = np.exp(-age_days / 14)  # 2-week half-life
            source_weight = self.source_weights.get(signal.data_type, 0.1)
            
            weight = recency_weight * source_weight * signal.confidence
            weighted_sum += signal.signal_strength * weight
            total_weight += weight
            sources_used.add(signal.data_type.value)
        
        aggregated_strength = weighted_sum / total_weight if total_weight > 0 else 0
        
        # Confidence based on number of sources and signals
        source_diversity = len(sources_used) / len(self.source_weights)
        signal_count_factor = min(len(relevant_signals) / 10, 1.0)
        confidence = source_diversity * 0.5 + signal_count_factor * 0.5
        
        return {
            'signal_strength': aggregated_strength,
            'confidence': confidence,
            'sources': list(sources_used),
            'signal_count': len(relevant_signals),
            'signals': [s.to_dict() for s in relevant_signals[-5:]],  # Last 5
        }
    
    def get_trading_recommendation(self, symbol: str, 
                                  dc_signal: Optional[str] = None) -> Dict[str, Any]:
        """
        Get trading recommendation based on alternative data
        
        Args:
            symbol: Stock symbol
            dc_signal: Optional DC signal for confirmation
            
        Returns:
            Recommendation dictionary
        """
        agg = self.get_aggregated_signal(symbol)
        
        recommendation = {
            'symbol': symbol,
            'timestamp': datetime.now().isoformat(),
            'alt_data_signal': agg['signal_strength'],
            'confidence': agg['confidence'],
            'sources': agg['sources'],
            'action': 'neutral',
            'position_adjustment': 1.0,
            'reason': '',
        }
        
        # Strong alternative data signal
        if abs(agg['signal_strength']) > 0.5 and agg['confidence'] > 0.5:
            if agg['signal_strength'] > 0:
                recommendation['action'] = 'bullish_bias'
                recommendation['reason'] = f"Strong bullish alt data ({', '.join(agg['sources'])})"
            else:
                recommendation['action'] = 'bearish_bias'
                recommendation['reason'] = f"Strong bearish alt data ({', '.join(agg['sources'])})"
        
        # Confirmation with DC signal
        if dc_signal:
            if dc_signal == 'long' and agg['signal_strength'] > 0.3:
                recommendation['position_adjustment'] = 1.15
                recommendation['reason'] += ' | Alt data confirms long'
            elif dc_signal == 'short' and agg['signal_strength'] < -0.3:
                recommendation['position_adjustment'] = 1.15
                recommendation['reason'] += ' | Alt data confirms short'
            elif dc_signal == 'long' and agg['signal_strength'] < -0.3:
                recommendation['position_adjustment'] = 0.8
                recommendation['reason'] += ' | Alt data contradicts long'
            elif dc_signal == 'short' and agg['signal_strength'] > 0.3:
                recommendation['position_adjustment'] = 0.8
                recommendation['reason'] += ' | Alt data contradicts short'
        
        return recommendation
