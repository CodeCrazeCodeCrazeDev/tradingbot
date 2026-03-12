"""
Macro Regime Detection System
Institutional-Grade Economic Regime Classification

This module provides comprehensive macro regime detection:
- Fed policy cycle tracking (hawkish/dovish/neutral)
- Inflation regime classification (deflation/low/moderate/high)
- Growth regime detection (recession/slowdown/expansion/boom)
- Risk-on/Risk-off environment classification
- Interest rate cycle positioning
- Employment trend analysis
- Yield curve analysis (inversion detection)
- Global capital flow indicators

Economist + Portfolio Manager + Hedge Fund Analyst Perspective
"""

import numpy as np
import pandas as pd
from typing import Any, Dict, List, Optional, Tuple, Union
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import logging
from collections import deque
import warnings
import numpy
import pandas

warnings.filterwarnings('ignore')

logger = logging.getLogger(__name__)


class FedPolicyRegime(Enum):
    """Federal Reserve policy stance"""
    VERY_HAWKISH = "VERY_HAWKISH"  # Aggressive tightening
    HAWKISH = "HAWKISH"  # Tightening
    NEUTRAL = "NEUTRAL"  # On hold
    DOVISH = "DOVISH"  # Easing
    VERY_DOVISH = "VERY_DOVISH"  # Emergency easing


class InflationRegime(Enum):
    """Inflation environment"""
    DEFLATION = "DEFLATION"  # CPI < 0%
    LOW_INFLATION = "LOW_INFLATION"  # CPI 0-2%
    MODERATE_INFLATION = "MODERATE_INFLATION"  # CPI 2-4%
    HIGH_INFLATION = "HIGH_INFLATION"  # CPI 4-6%
    VERY_HIGH_INFLATION = "VERY_HIGH_INFLATION"  # CPI > 6%


class GrowthRegime(Enum):
    """Economic growth environment"""
    RECESSION = "RECESSION"  # GDP < 0%, contracting
    SLOWDOWN = "SLOWDOWN"  # GDP 0-2%, decelerating
    MODERATE_GROWTH = "MODERATE_GROWTH"  # GDP 2-3%
    STRONG_GROWTH = "STRONG_GROWTH"  # GDP 3-5%
    BOOM = "BOOM"  # GDP > 5%


class RiskRegime(Enum):
    """Risk appetite environment"""
    RISK_OFF_EXTREME = "RISK_OFF_EXTREME"  # Crisis mode
    RISK_OFF = "RISK_OFF"  # Defensive positioning
    NEUTRAL = "NEUTRAL"  # Balanced
    RISK_ON = "RISK_ON"  # Aggressive positioning
    RISK_ON_EXTREME = "RISK_ON_EXTREME"  # Euphoria


class YieldCurveRegime(Enum):
    """Yield curve shape"""
    DEEPLY_INVERTED = "DEEPLY_INVERTED"  # Strong recession signal
    INVERTED = "INVERTED"  # Recession warning
    FLAT = "FLAT"  # Transition period
    NORMAL = "NORMAL"  # Healthy economy
    STEEP = "STEEP"  # Recovery/expansion


class BusinessCycle(Enum):
    """Business cycle phase"""
    EARLY_CYCLE = "EARLY_CYCLE"  # Recovery from recession
    MID_CYCLE = "MID_CYCLE"  # Expansion
    LATE_CYCLE = "LATE_CYCLE"  # Peak approaching
    RECESSION = "RECESSION"  # Contraction


@dataclass
class MacroIndicators:
    """Current macro economic indicators"""
    # Fed Policy
    fed_funds_rate: float = 5.25  # Current Fed Funds rate
    fed_funds_change_6m: float = 0.0  # Change over 6 months
    fed_balance_sheet_change: float = 0.0  # QE/QT indicator
    
    # Inflation
    cpi_yoy: float = 3.0  # CPI year-over-year
    core_cpi_yoy: float = 3.5  # Core CPI (ex food/energy)
    pce_yoy: float = 2.8  # PCE (Fed's preferred measure)
    inflation_expectations: float = 2.5  # 5-year breakeven
    
    # Growth
    gdp_growth: float = 2.5  # Real GDP growth
    gdp_nowcast: float = 2.3  # Atlanta Fed GDPNow
    ism_manufacturing: float = 50.0  # ISM Manufacturing PMI
    ism_services: float = 52.0  # ISM Services PMI
    
    # Employment
    unemployment_rate: float = 3.8  # Unemployment rate
    nfp_3m_avg: float = 200000  # Non-farm payrolls 3-month avg
    initial_claims: float = 220000  # Weekly jobless claims
    jolts_openings: float = 9000000  # Job openings
    
    # Yield Curve
    us_2y_yield: float = 4.5  # 2-year Treasury yield
    us_10y_yield: float = 4.2  # 10-year Treasury yield
    us_30y_yield: float = 4.4  # 30-year Treasury yield
    
    # Risk Indicators
    vix: float = 18.0  # VIX index
    credit_spreads: float = 1.5  # High yield spread
    ted_spread: float = 0.2  # TED spread (credit stress)
    
    # Global
    dxy: float = 104.0  # Dollar index
    oil_price: float = 75.0  # WTI crude
    gold_price: float = 2000.0  # Gold price
    copper_gold_ratio: float = 0.004  # Growth indicator
    
    timestamp: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            'fed_funds_rate': self.fed_funds_rate,
            'cpi_yoy': self.cpi_yoy,
            'gdp_growth': self.gdp_growth,
            'unemployment_rate': self.unemployment_rate,
            'yield_curve_spread': self.us_10y_yield - self.us_2y_yield,
            'vix': self.vix,
            'timestamp': self.timestamp.isoformat()
        }


@dataclass
class MacroRegimeState:
    """Complete macro regime state"""
    timestamp: datetime
    fed_policy: FedPolicyRegime
    inflation: InflationRegime
    growth: GrowthRegime
    risk: RiskRegime
    yield_curve: YieldCurveRegime
    business_cycle: BusinessCycle
    
    # Composite scores (0-100)
    hawkishness_score: float = 50.0  # 0=very dovish, 100=very hawkish
    growth_score: float = 50.0  # 0=recession, 100=boom
    risk_appetite_score: float = 50.0  # 0=extreme fear, 100=extreme greed
    
    # Strategy recommendations
    equity_allocation: float = 0.6  # Recommended equity weight
    bond_allocation: float = 0.3  # Recommended bond weight
    cash_allocation: float = 0.1  # Recommended cash weight
    
    # Sector tilts
    sector_tilts: Dict[str, float] = field(default_factory=dict)
    
    # Confidence
    confidence: float = 0.8  # Regime classification confidence
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            'timestamp': self.timestamp.isoformat(),
            'fed_policy': self.fed_policy.value,
            'inflation': self.inflation.value,
            'growth': self.growth.value,
            'risk': self.risk.value,
            'yield_curve': self.yield_curve.value,
            'business_cycle': self.business_cycle.value,
            'hawkishness_score': round(self.hawkishness_score, 1),
            'growth_score': round(self.growth_score, 1),
            'risk_appetite_score': round(self.risk_appetite_score, 1),
            'equity_allocation': round(self.equity_allocation, 2),
            'bond_allocation': round(self.bond_allocation, 2),
            'cash_allocation': round(self.cash_allocation, 2),
            'sector_tilts': self.sector_tilts,
            'confidence': round(self.confidence, 2)
        }


@dataclass
class StrategyAdjustment:
    """Strategy adjustment based on macro regime"""
    strategy_name: str
    current_weight: float
    recommended_weight: float
    adjustment_reason: str
    urgency: str  # LOW, MEDIUM, HIGH, CRITICAL
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'strategy_name': self.strategy_name,
            'current_weight': round(self.current_weight, 2),
            'recommended_weight': round(self.recommended_weight, 2),
            'adjustment_reason': self.adjustment_reason,
            'urgency': self.urgency
        }


class MacroRegimeDetector:
    """
    Macro Regime Detection System
    
    Classifies the current macroeconomic environment and provides
    strategy allocation recommendations based on:
    
    1. Fed Policy Cycle
       - Tracks rate changes, balance sheet, forward guidance
       - Classifies: Very Hawkish → Very Dovish
    
    2. Inflation Regime
       - Monitors CPI, Core CPI, PCE, expectations
       - Classifies: Deflation → Very High Inflation
    
    3. Growth Regime
       - Tracks GDP, PMIs, employment
       - Classifies: Recession → Boom
    
    4. Risk Appetite
       - Monitors VIX, credit spreads, flows
       - Classifies: Risk-Off Extreme → Risk-On Extreme
    
    5. Yield Curve
       - Analyzes 2s10s spread, curve shape
       - Classifies: Deeply Inverted → Steep
    
    6. Business Cycle
       - Composite of all indicators
       - Classifies: Early → Mid → Late → Recession
    
    Strategy Implications:
    - Early Cycle: Overweight cyclicals, small caps
    - Mid Cycle: Balanced, quality growth
    - Late Cycle: Defensive, reduce risk
    - Recession: Cash, bonds, gold
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize macro regime detector
        
        Args:
            config: Configuration dictionary
        """
        try:
            self.config = config or {}
        
            # Thresholds
            self.inflation_thresholds = self.config.get('inflation_thresholds', {
                'deflation': 0.0,
                'low': 2.0,
                'moderate': 4.0,
                'high': 6.0
            })
        
            self.growth_thresholds = self.config.get('growth_thresholds', {
                'recession': 0.0,
                'slowdown': 2.0,
                'moderate': 3.0,
                'strong': 5.0
            })
        
            self.vix_thresholds = self.config.get('vix_thresholds', {
                'complacent': 12,
                'normal': 20,
                'elevated': 30,
                'fear': 40
            })
        
            # State tracking
            self.current_state: Optional[MacroRegimeState] = None
            self.previous_state: Optional[MacroRegimeState] = None
            self.state_history: deque = deque(maxlen=100)
        
            # Regime change tracking
            self.regime_changes: List[Dict[str, Any]] = []
        
            # Statistics
            self.updates = 0
            self.regime_transitions = 0
        
            logger.info("MacroRegimeDetector initialized")
        except Exception as e:
            logger.error(f"Error in __init__: {e}")
            raise
    
    def update(self, indicators: MacroIndicators) -> MacroRegimeState:
        """
        Update regime classification with new indicators
        
        Args:
            indicators: Current macro indicators
            
        Returns:
            MacroRegimeState with current classification
        """
        try:
            self.updates += 1
        
            # Classify each dimension
            fed_policy = self._classify_fed_policy(indicators)
            inflation = self._classify_inflation(indicators)
            growth = self._classify_growth(indicators)
            risk = self._classify_risk(indicators)
            yield_curve = self._classify_yield_curve(indicators)
            business_cycle = self._classify_business_cycle(
                fed_policy, inflation, growth, yield_curve
            )
        
            # Calculate composite scores
            hawkishness_score = self._calculate_hawkishness_score(indicators)
            growth_score = self._calculate_growth_score(indicators)
            risk_appetite_score = self._calculate_risk_appetite_score(indicators)
        
            # Calculate allocations
            allocations = self._calculate_allocations(
                business_cycle, risk, hawkishness_score, growth_score
            )
        
            # Calculate sector tilts
            sector_tilts = self._calculate_sector_tilts(business_cycle, inflation, growth)
        
            # Calculate confidence
            confidence = self._calculate_confidence(indicators)
        
            # Create state
            state = MacroRegimeState(
                timestamp=datetime.now(),
                fed_policy=fed_policy,
                inflation=inflation,
                growth=growth,
                risk=risk,
                yield_curve=yield_curve,
                business_cycle=business_cycle,
                hawkishness_score=hawkishness_score,
                growth_score=growth_score,
                risk_appetite_score=risk_appetite_score,
                equity_allocation=allocations['equity'],
                bond_allocation=allocations['bonds'],
                cash_allocation=allocations['cash'],
                sector_tilts=sector_tilts,
                confidence=confidence
            )
        
            # Check for regime change
            if self.current_state:
                self._check_regime_change(state)
        
            # Update state
            self.previous_state = self.current_state
            self.current_state = state
            self.state_history.append(state)
        
            return state
        except Exception as e:
            logger.error(f"Error in update: {e}")
            raise
    
    def _classify_fed_policy(self, indicators: MacroIndicators) -> FedPolicyRegime:
        """Classify Fed policy stance"""
        try:
            rate = indicators.fed_funds_rate
            rate_change = indicators.fed_funds_change_6m
            balance_sheet = indicators.fed_balance_sheet_change
        
            # Score based on rate level and changes
            score = 0
        
            # Rate level contribution
            if rate > 5.0:
                score += 30
            elif rate > 4.0:
                score += 20
            elif rate > 2.0:
                score += 10
            elif rate > 0.5:
                score += 0
            else:
                score -= 20
        
            # Rate change contribution
            if rate_change > 1.0:
                score += 30
            elif rate_change > 0.5:
                score += 20
            elif rate_change > 0:
                score += 10
            elif rate_change > -0.5:
                score -= 10
            else:
                score -= 30
        
            # Balance sheet contribution
            if balance_sheet < -0.1:  # QT
                score += 20
            elif balance_sheet > 0.1:  # QE
                score -= 20
        
            # Classify
            if score >= 60:
                return FedPolicyRegime.VERY_HAWKISH
            elif score >= 30:
                return FedPolicyRegime.HAWKISH
            elif score >= -30:
                return FedPolicyRegime.NEUTRAL
            elif score >= -60:
                return FedPolicyRegime.DOVISH
            else:
                return FedPolicyRegime.VERY_DOVISH
        except Exception as e:
            logger.error(f"Error in _classify_fed_policy: {e}")
            raise
    
    def _classify_inflation(self, indicators: MacroIndicators) -> InflationRegime:
        """Classify inflation regime"""
        # Use average of CPI and PCE
        try:
            inflation = (indicators.cpi_yoy + indicators.pce_yoy) / 2
        
            if inflation < self.inflation_thresholds['deflation']:
                return InflationRegime.DEFLATION
            elif inflation < self.inflation_thresholds['low']:
                return InflationRegime.LOW_INFLATION
            elif inflation < self.inflation_thresholds['moderate']:
                return InflationRegime.MODERATE_INFLATION
            elif inflation < self.inflation_thresholds['high']:
                return InflationRegime.HIGH_INFLATION
            else:
                return InflationRegime.VERY_HIGH_INFLATION
        except Exception as e:
            logger.error(f"Error in _classify_inflation: {e}")
            raise
    
    def _classify_growth(self, indicators: MacroIndicators) -> GrowthRegime:
        """Classify growth regime"""
        # Composite of GDP and PMIs
        try:
            gdp = indicators.gdp_growth
            pmi_avg = (indicators.ism_manufacturing + indicators.ism_services) / 2
        
            # PMI contribution (50 = neutral)
            pmi_growth_equiv = (pmi_avg - 50) * 0.1  # Rough conversion
        
            # Weighted average
            growth = 0.7 * gdp + 0.3 * pmi_growth_equiv
        
            if growth < self.growth_thresholds['recession']:
                return GrowthRegime.RECESSION
            elif growth < self.growth_thresholds['slowdown']:
                return GrowthRegime.SLOWDOWN
            elif growth < self.growth_thresholds['moderate']:
                return GrowthRegime.MODERATE_GROWTH
            elif growth < self.growth_thresholds['strong']:
                return GrowthRegime.STRONG_GROWTH
            else:
                return GrowthRegime.BOOM
        except Exception as e:
            logger.error(f"Error in _classify_growth: {e}")
            raise
    
    def _classify_risk(self, indicators: MacroIndicators) -> RiskRegime:
        """Classify risk appetite regime"""
        try:
            vix = indicators.vix
            credit_spreads = indicators.credit_spreads
        
            # VIX score (inverted - high VIX = risk off)
            if vix > self.vix_thresholds['fear']:
                vix_score = 0
            elif vix > self.vix_thresholds['elevated']:
                vix_score = 25
            elif vix > self.vix_thresholds['normal']:
                vix_score = 50
            elif vix > self.vix_thresholds['complacent']:
                vix_score = 75
            else:
                vix_score = 100
        
            # Credit spread score (inverted - high spreads = risk off)
            if credit_spreads > 5.0:
                credit_score = 0
            elif credit_spreads > 3.0:
                credit_score = 25
            elif credit_spreads > 2.0:
                credit_score = 50
            elif credit_spreads > 1.0:
                credit_score = 75
            else:
                credit_score = 100
        
            # Combined score
            risk_score = 0.6 * vix_score + 0.4 * credit_score
        
            if risk_score < 20:
                return RiskRegime.RISK_OFF_EXTREME
            elif risk_score < 40:
                return RiskRegime.RISK_OFF
            elif risk_score < 60:
                return RiskRegime.NEUTRAL
            elif risk_score < 80:
                return RiskRegime.RISK_ON
            else:
                return RiskRegime.RISK_ON_EXTREME
        except Exception as e:
            logger.error(f"Error in _classify_risk: {e}")
            raise
    
    def _classify_yield_curve(self, indicators: MacroIndicators) -> YieldCurveRegime:
        """Classify yield curve shape"""
        try:
            spread_2s10s = indicators.us_10y_yield - indicators.us_2y_yield
        
            if spread_2s10s < -0.5:
                return YieldCurveRegime.DEEPLY_INVERTED
            elif spread_2s10s < 0:
                return YieldCurveRegime.INVERTED
            elif spread_2s10s < 0.5:
                return YieldCurveRegime.FLAT
            elif spread_2s10s < 1.5:
                return YieldCurveRegime.NORMAL
            else:
                return YieldCurveRegime.STEEP
        except Exception as e:
            logger.error(f"Error in _classify_yield_curve: {e}")
            raise
    
    def _classify_business_cycle(self,
                                fed_policy: FedPolicyRegime,
                                inflation: InflationRegime,
                                growth: GrowthRegime,
                                yield_curve: YieldCurveRegime) -> BusinessCycle:
        """Classify business cycle phase"""
        # Score each indicator
        try:
            scores = {
                'early': 0,
                'mid': 0,
                'late': 0,
                'recession': 0
            }
        
            # Fed policy contribution
            if fed_policy in [FedPolicyRegime.VERY_DOVISH, FedPolicyRegime.DOVISH]:
                scores['early'] += 2
                scores['recession'] += 1
            elif fed_policy == FedPolicyRegime.NEUTRAL:
                scores['mid'] += 2
            else:
                scores['late'] += 2
        
            # Inflation contribution
            if inflation == InflationRegime.DEFLATION:
                scores['recession'] += 2
            elif inflation == InflationRegime.LOW_INFLATION:
                scores['early'] += 1
                scores['mid'] += 1
            elif inflation == InflationRegime.MODERATE_INFLATION:
                scores['mid'] += 2
            else:
                scores['late'] += 2
        
            # Growth contribution
            if growth == GrowthRegime.RECESSION:
                scores['recession'] += 3
            elif growth == GrowthRegime.SLOWDOWN:
                scores['late'] += 1
                scores['recession'] += 1
            elif growth == GrowthRegime.MODERATE_GROWTH:
                scores['mid'] += 2
            elif growth == GrowthRegime.STRONG_GROWTH:
                scores['early'] += 1
                scores['mid'] += 1
            else:
                scores['early'] += 2
        
            # Yield curve contribution
            if yield_curve in [YieldCurveRegime.DEEPLY_INVERTED, YieldCurveRegime.INVERTED]:
                scores['late'] += 1
                scores['recession'] += 2
            elif yield_curve == YieldCurveRegime.STEEP:
                scores['early'] += 2
            else:
                scores['mid'] += 1
        
            # Find highest score
            max_phase = max(scores, key=scores.get)
        
            if max_phase == 'early':
                return BusinessCycle.EARLY_CYCLE
            elif max_phase == 'mid':
                return BusinessCycle.MID_CYCLE
            elif max_phase == 'late':
                return BusinessCycle.LATE_CYCLE
            else:
                return BusinessCycle.RECESSION
        except Exception as e:
            logger.error(f"Error in _classify_business_cycle: {e}")
            raise
    
    def _calculate_hawkishness_score(self, indicators: MacroIndicators) -> float:
        """Calculate Fed hawkishness score (0-100)"""
        try:
            score = 50  # Start neutral
        
            # Rate level
            score += (indicators.fed_funds_rate - 2.5) * 10
        
            # Rate change
            score += indicators.fed_funds_change_6m * 20
        
            # Inflation pressure
            score += (indicators.cpi_yoy - 2.0) * 5
        
            return np.clip(score, 0, 100)
        except Exception as e:
            logger.error(f"Error in _calculate_hawkishness_score: {e}")
            raise
    
    def _calculate_growth_score(self, indicators: MacroIndicators) -> float:
        """Calculate growth score (0-100)"""
        try:
            score = 50  # Start neutral
        
            # GDP contribution
            score += indicators.gdp_growth * 10
        
            # PMI contribution
            score += (indicators.ism_manufacturing - 50) * 1
            score += (indicators.ism_services - 50) * 1
        
            # Employment contribution
            score -= (indicators.unemployment_rate - 4.0) * 5
        
            return np.clip(score, 0, 100)
        except Exception as e:
            logger.error(f"Error in _calculate_growth_score: {e}")
            raise
    
    def _calculate_risk_appetite_score(self, indicators: MacroIndicators) -> float:
        """Calculate risk appetite score (0-100)"""
        try:
            score = 50  # Start neutral
        
            # VIX contribution (inverted)
            score -= (indicators.vix - 20) * 2
        
            # Credit spreads (inverted)
            score -= (indicators.credit_spreads - 1.5) * 10
        
            return np.clip(score, 0, 100)
        except Exception as e:
            logger.error(f"Error in _calculate_risk_appetite_score: {e}")
            raise
    
    def _calculate_allocations(self,
                              business_cycle: BusinessCycle,
                              risk: RiskRegime,
                              hawkishness: float,
                              growth: float) -> Dict[str, float]:
        """Calculate recommended asset allocations"""
        
        # Base allocations by business cycle
        try:
            base_allocations = {
                BusinessCycle.EARLY_CYCLE: {'equity': 0.70, 'bonds': 0.20, 'cash': 0.10},
                BusinessCycle.MID_CYCLE: {'equity': 0.60, 'bonds': 0.30, 'cash': 0.10},
                BusinessCycle.LATE_CYCLE: {'equity': 0.45, 'bonds': 0.35, 'cash': 0.20},
                BusinessCycle.RECESSION: {'equity': 0.30, 'bonds': 0.40, 'cash': 0.30}
            }
        
            allocations = base_allocations[business_cycle].copy()
        
            # Adjust for risk regime
            if risk == RiskRegime.RISK_OFF_EXTREME:
                allocations['equity'] -= 0.15
                allocations['cash'] += 0.15
            elif risk == RiskRegime.RISK_OFF:
                allocations['equity'] -= 0.10
                allocations['cash'] += 0.10
            elif risk == RiskRegime.RISK_ON:
                allocations['equity'] += 0.05
                allocations['cash'] -= 0.05
            elif risk == RiskRegime.RISK_ON_EXTREME:
                allocations['equity'] += 0.10
                allocations['cash'] -= 0.10
        
            # Ensure allocations sum to 1 and are non-negative
            total = sum(allocations.values())
            allocations = {k: max(0, v / total) for k, v in allocations.items()}
        
            return allocations
        except Exception as e:
            logger.error(f"Error in _calculate_allocations: {e}")
            raise
    
    def _calculate_sector_tilts(self,
                               business_cycle: BusinessCycle,
                               inflation: InflationRegime,
                               growth: GrowthRegime) -> Dict[str, float]:
        """Calculate sector tilts based on regime"""
        
        # Base tilts (0 = neutral, positive = overweight, negative = underweight)
        try:
            tilts = {
                'technology': 0.0,
                'healthcare': 0.0,
                'financials': 0.0,
                'energy': 0.0,
                'consumer_discretionary': 0.0,
                'consumer_staples': 0.0,
                'industrials': 0.0,
                'materials': 0.0,
                'utilities': 0.0,
                'real_estate': 0.0
            }
        
            # Business cycle adjustments
            if business_cycle == BusinessCycle.EARLY_CYCLE:
                tilts['financials'] += 0.10
                tilts['consumer_discretionary'] += 0.10
                tilts['industrials'] += 0.10
                tilts['materials'] += 0.05
                tilts['utilities'] -= 0.10
                tilts['consumer_staples'] -= 0.10
        
            elif business_cycle == BusinessCycle.MID_CYCLE:
                tilts['technology'] += 0.10
                tilts['healthcare'] += 0.05
                tilts['industrials'] += 0.05
        
            elif business_cycle == BusinessCycle.LATE_CYCLE:
                tilts['energy'] += 0.10
                tilts['materials'] += 0.05
                tilts['consumer_staples'] += 0.05
                tilts['technology'] -= 0.05
                tilts['consumer_discretionary'] -= 0.10
        
            elif business_cycle == BusinessCycle.RECESSION:
                tilts['utilities'] += 0.15
                tilts['consumer_staples'] += 0.15
                tilts['healthcare'] += 0.10
                tilts['technology'] -= 0.10
                tilts['financials'] -= 0.15
                tilts['consumer_discretionary'] -= 0.15
        
            # Inflation adjustments
            if inflation in [InflationRegime.HIGH_INFLATION, InflationRegime.VERY_HIGH_INFLATION]:
                tilts['energy'] += 0.10
                tilts['materials'] += 0.05
                tilts['real_estate'] -= 0.10
                tilts['utilities'] -= 0.05
        
            return tilts
        except Exception as e:
            logger.error(f"Error in _calculate_sector_tilts: {e}")
            raise
    
    def _calculate_confidence(self, indicators: MacroIndicators) -> float:
        """Calculate regime classification confidence"""
        # Higher confidence when indicators are consistent
        # Lower confidence during transitions
        
        try:
            confidence = 0.8  # Base confidence
        
            # Check for conflicting signals
            # High growth + inverted curve = conflicting
            if indicators.gdp_growth > 2.5 and (indicators.us_10y_yield - indicators.us_2y_yield) < 0:
                confidence -= 0.1
        
            # Low VIX + high credit spreads = conflicting
            if indicators.vix < 15 and indicators.credit_spreads > 3.0:
                confidence -= 0.1
        
            # High inflation + low rates = conflicting
            if indicators.cpi_yoy > 4.0 and indicators.fed_funds_rate < 2.0:
                confidence -= 0.1
        
            return np.clip(confidence, 0.5, 1.0)
        except Exception as e:
            logger.error(f"Error in _calculate_confidence: {e}")
            raise
    
    def _check_regime_change(self, new_state: MacroRegimeState):
        """Check for regime changes and log them"""
        try:
            changes = []
        
            if self.current_state.business_cycle != new_state.business_cycle:
                changes.append({
                    'type': 'BUSINESS_CYCLE',
                    'from': self.current_state.business_cycle.value,
                    'to': new_state.business_cycle.value,
                    'timestamp': datetime.now().isoformat()
                })
                self.regime_transitions += 1
        
            if self.current_state.risk != new_state.risk:
                changes.append({
                    'type': 'RISK_REGIME',
                    'from': self.current_state.risk.value,
                    'to': new_state.risk.value,
                    'timestamp': datetime.now().isoformat()
                })
        
            if self.current_state.fed_policy != new_state.fed_policy:
                changes.append({
                    'type': 'FED_POLICY',
                    'from': self.current_state.fed_policy.value,
                    'to': new_state.fed_policy.value,
                    'timestamp': datetime.now().isoformat()
                })
        
            if changes:
                self.regime_changes.extend(changes)
                for change in changes:
                    logger.warning(f"Regime change detected: {change['type']} "
                                 f"{change['from']} -> {change['to']}")
        except Exception as e:
            logger.error(f"Error in _check_regime_change: {e}")
            raise
    
    def get_strategy_adjustments(self,
                                current_strategies: Dict[str, float]) -> List[StrategyAdjustment]:
        """
        Get recommended strategy adjustments based on current regime
        
        Args:
            current_strategies: Dict of {strategy_name: current_weight}
            
        Returns:
            List of StrategyAdjustment recommendations
        """
        try:
            if not self.current_state:
                return []
        
            adjustments = []
            cycle = self.current_state.business_cycle
            risk = self.current_state.risk
        
            # Strategy recommendations by regime
            regime_weights = {
                BusinessCycle.EARLY_CYCLE: {
                    'momentum': 0.25,
                    'value': 0.20,
                    'mean_reversion': 0.15,
                    'trend_following': 0.25,
                    'carry': 0.15
                },
                BusinessCycle.MID_CYCLE: {
                    'momentum': 0.20,
                    'value': 0.15,
                    'mean_reversion': 0.20,
                    'trend_following': 0.20,
                    'carry': 0.25
                },
                BusinessCycle.LATE_CYCLE: {
                    'momentum': 0.15,
                    'value': 0.25,
                    'mean_reversion': 0.25,
                    'trend_following': 0.15,
                    'carry': 0.20
                },
                BusinessCycle.RECESSION: {
                    'momentum': 0.10,
                    'value': 0.30,
                    'mean_reversion': 0.30,
                    'trend_following': 0.20,
                    'carry': 0.10
                }
            }
        
            recommended = regime_weights.get(cycle, {})
        
            for strategy, current_weight in current_strategies.items():
                if strategy in recommended:
                    rec_weight = recommended[strategy]
                
                    # Adjust for risk regime
                    if risk in [RiskRegime.RISK_OFF_EXTREME, RiskRegime.RISK_OFF]:
                        if strategy in ['momentum', 'trend_following']:
                            rec_weight *= 0.7
                        elif strategy in ['mean_reversion', 'value']:
                            rec_weight *= 1.2
                
                    diff = abs(rec_weight - current_weight)
                
                    if diff > 0.05:
                        urgency = 'HIGH' if diff > 0.15 else 'MEDIUM' if diff > 0.10 else 'LOW'
                    
                        adjustments.append(StrategyAdjustment(
                            strategy_name=strategy,
                            current_weight=current_weight,
                            recommended_weight=rec_weight,
                            adjustment_reason=f"Business cycle: {cycle.value}, Risk: {risk.value}",
                            urgency=urgency
                        ))
        
            return adjustments
        except Exception as e:
            logger.error(f"Error in get_strategy_adjustments: {e}")
            raise
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get detector statistics"""
        return {
            'updates': self.updates,
            'regime_transitions': self.regime_transitions,
            'current_state': self.current_state.to_dict() if self.current_state else None,
            'recent_changes': self.regime_changes[-10:] if self.regime_changes else [],
            'history_length': len(self.state_history)
        }


# Example usage
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    # Create detector
    detector = MacroRegimeDetector()
    
    # Current market conditions (example)
    indicators = MacroIndicators(
        fed_funds_rate=5.25,
        fed_funds_change_6m=0.25,
        fed_balance_sheet_change=-0.05,
        cpi_yoy=3.2,
        core_cpi_yoy=3.8,
        pce_yoy=2.9,
        inflation_expectations=2.4,
        gdp_growth=2.8,
        gdp_nowcast=2.5,
        ism_manufacturing=48.5,
        ism_services=52.0,
        unemployment_rate=3.9,
        nfp_3m_avg=180000,
        initial_claims=215000,
        jolts_openings=8500000,
        us_2y_yield=4.6,
        us_10y_yield=4.3,
        us_30y_yield=4.5,
        vix=16,
        credit_spreads=1.4,
        ted_spread=0.15,
        dxy=103,
        oil_price=78,
        gold_price=2050,
        copper_gold_ratio=0.0042
    )
    
    # Update regime
    state = detector.update(indicators)
    
    logger.info("\n=== Macro Regime Analysis ===")
    logger.info(f"\nBusiness Cycle: {state.business_cycle.value}")
    logger.info(f"Fed Policy: {state.fed_policy.value}")
    logger.info(f"Inflation: {state.inflation.value}")
    logger.info(f"Growth: {state.growth.value}")
    logger.info(f"Risk Appetite: {state.risk.value}")
    logger.info(f"Yield Curve: {state.yield_curve.value}")
    
    logger.info(f"\n=== Composite Scores ===")
    logger.info(f"Hawkishness: {state.hawkishness_score:.1f}/100")
    logger.info(f"Growth: {state.growth_score:.1f}/100")
    logger.info(f"Risk Appetite: {state.risk_appetite_score:.1f}/100")
    logger.info(f"Confidence: {state.confidence:.1%}")
    
    logger.info(f"\n=== Recommended Allocations ===")
    logger.info(f"Equity: {state.equity_allocation:.1%}")
    logger.info(f"Bonds: {state.bond_allocation:.1%}")
    logger.info(f"Cash: {state.cash_allocation:.1%}")
    
    logger.info(f"\n=== Sector Tilts ===")
    for sector, tilt in sorted(state.sector_tilts.items(), key=lambda x: -x[1]):
        direction = "OW" if tilt > 0 else "UW" if tilt < 0 else "N"
        logger.info(f"  {sector}: {direction} {abs(tilt):.1%}")
    
    # Get strategy adjustments
    current_strategies = {
        'momentum': 0.25,
        'value': 0.15,
        'mean_reversion': 0.20,
        'trend_following': 0.25,
        'carry': 0.15
    }
    
    adjustments = detector.get_strategy_adjustments(current_strategies)
    
    logger.info(f"\n=== Strategy Adjustments ===")
    for adj in adjustments:
        print(f"  {adj.strategy_name}: {adj.current_weight:.1%} -> {adj.recommended_weight:.1%} "
              f"[{adj.urgency}]")
        logger.info(f"    Reason: {adj.adjustment_reason}")
