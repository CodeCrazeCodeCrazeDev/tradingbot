"""
Feature Synthesis Engine
========================
Translate hypotheses into feature families, not single features.

Each feature family must:
- Be calculable from real market data
- Be normalized across regimes
- Have a defined time horizon
- Include regime conditions
- Include risk controls

Examples: liquidity stress index, volatility convexity, flow imbalance persistence, trend fragility.

Author: AlphaAlgo Research Team
"""

import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum, auto
from typing import Any, Callable, Dict, List, Optional, Set, Tuple, Union

import numpy as np
import pandas as pd

from .rdaos_core import (
    AlphaHorizon,
    AssetClass,
    FeatureDefinition,
    FeatureFamily,
    Hypothesis,
    ProductionStatus,
    RegimeType,
    generate_id
)

logger = logging.getLogger(__name__)


class NormalizationMethod(Enum):
    """Feature normalization methods"""
    ZSCORE = "zscore"
    MINMAX = "minmax"
    RANK = "rank"
    PERCENTILE = "percentile"
    ROBUST = "robust"  # Median/IQR based
    NONE = "none"


class FeatureCategory(Enum):
    """Categories of features"""
    MOMENTUM = "momentum"
    MEAN_REVERSION = "mean_reversion"
    VOLATILITY = "volatility"
    LIQUIDITY = "liquidity"
    FLOW = "flow"
    SENTIMENT = "sentiment"
    MICROSTRUCTURE = "microstructure"
    FUNDAMENTAL = "fundamental"
    CROSS_SECTIONAL = "cross_sectional"
    REGIME = "regime"


@dataclass
class FeatureTemplate:
    """Template for generating features"""
    name: str
    category: FeatureCategory
    formula_template: str
    parameters: Dict[str, Any]
    
    required_data: List[str]
    default_lookback: int
    default_horizon: AlphaHorizon
    
    normalization: NormalizationMethod = NormalizationMethod.ZSCORE
    regime_sensitive: bool = True
    
    risk_controls: Dict[str, float] = field(default_factory=dict)


@dataclass
class SynthesizedFeature:
    """A synthesized feature ready for testing"""
    feature_id: str
    name: str
    family_id: str
    
    formula: str
    parameters: Dict[str, Any]
    
    lookback_period: int
    horizon: AlphaHorizon
    normalization: NormalizationMethod
    
    regime_conditions: List[RegimeType]
    risk_controls: Dict[str, float]
    
    compute_function: Optional[Callable] = None
    
    def compute(self, data: pd.DataFrame) -> pd.Series:
        """Compute feature values from data"""
        if self.compute_function:
            return self.compute_function(data, self.parameters)


class FeatureTemplateLibrary:
    """
    Library of feature templates organized by category.
    
    Contains templates for:
    - Momentum features
    - Mean reversion features
    - Volatility features
    - Liquidity features
    - Flow features
    - Microstructure features
    """
    
    def __init__(self):
        self.templates: Dict[str, FeatureTemplate] = {}
        self._load_default_templates()
    
    def _load_default_templates(self):
        """Load default feature templates"""
        
        # Momentum templates
        self.templates["momentum_roc"] = FeatureTemplate(
            name="Rate of Change",
            category=FeatureCategory.MOMENTUM,
            formula_template="(price[t] - price[t-{lookback}]) / price[t-{lookback}]",
            parameters={"lookback": [5, 10, 20, 60]},
            required_data=["price"],
            default_lookback=20,
            default_horizon=AlphaHorizon.DAILY,
            risk_controls={"max_exposure": 0.1}
        )
        
        self.templates["momentum_rsi"] = FeatureTemplate(
            name="Relative Strength Index",
            category=FeatureCategory.MOMENTUM,
            formula_template="100 - 100/(1 + avg_gain/avg_loss)",
            parameters={"period": [7, 14, 21]},
            required_data=["price"],
            default_lookback=14,
            default_horizon=AlphaHorizon.DAILY,
            risk_controls={"max_exposure": 0.1}
        )
        
        self.templates["momentum_macd"] = FeatureTemplate(
            name="MACD Signal",
            category=FeatureCategory.MOMENTUM,
            formula_template="EMA({fast}) - EMA({slow})",
            parameters={"fast": [8, 12], "slow": [21, 26], "signal": [9]},
            required_data=["price"],
            default_lookback=26,
            default_horizon=AlphaHorizon.DAILY,
            risk_controls={"max_exposure": 0.1}
        )
        
        # Mean reversion templates
        self.templates["mean_reversion_zscore"] = FeatureTemplate(
            name="Price Z-Score",
            category=FeatureCategory.MEAN_REVERSION,
            formula_template="(price - mean(price, {lookback})) / std(price, {lookback})",
            parameters={"lookback": [20, 60, 120]},
            required_data=["price"],
            default_lookback=60,
            default_horizon=AlphaHorizon.DAILY,
            risk_controls={"max_exposure": 0.1, "max_zscore": 3.0}
        )
        
        self.templates["mean_reversion_bollinger"] = FeatureTemplate(
            name="Bollinger Band Position",
            category=FeatureCategory.MEAN_REVERSION,
            formula_template="(price - lower_band) / (upper_band - lower_band)",
            parameters={"period": [20], "std_dev": [2.0]},
            required_data=["price"],
            default_lookback=20,
            default_horizon=AlphaHorizon.DAILY,
            risk_controls={"max_exposure": 0.1}
        )
        
        # Volatility templates
        self.templates["volatility_realized"] = FeatureTemplate(
            name="Realized Volatility",
            category=FeatureCategory.VOLATILITY,
            formula_template="std(returns, {lookback}) * sqrt(252)",
            parameters={"lookback": [5, 10, 20, 60]},
            required_data=["price"],
            default_lookback=20,
            default_horizon=AlphaHorizon.DAILY,
            risk_controls={"max_vol": 0.5}
        )
        
        self.templates["volatility_ratio"] = FeatureTemplate(
            name="Volatility Ratio",
            category=FeatureCategory.VOLATILITY,
            formula_template="vol({short}) / vol({long})",
            parameters={"short": [5, 10], "long": [20, 60]},
            required_data=["price"],
            default_lookback=60,
            default_horizon=AlphaHorizon.DAILY,
            risk_controls={"max_ratio": 2.0}
        )
        
        self.templates["volatility_convexity"] = FeatureTemplate(
            name="Volatility Convexity",
            category=FeatureCategory.VOLATILITY,
            formula_template="d2(vol)/d(price)^2",
            parameters={"lookback": [20, 60]},
            required_data=["price", "volatility"],
            default_lookback=60,
            default_horizon=AlphaHorizon.DAILY,
            regime_sensitive=True,
            risk_controls={"max_exposure": 0.05}
        )
        
        # Liquidity templates
        self.templates["liquidity_stress_index"] = FeatureTemplate(
            name="Liquidity Stress Index",
            category=FeatureCategory.LIQUIDITY,
            formula_template="composite(spread_zscore, volume_zscore, impact_zscore)",
            parameters={"lookback": [20, 60]},
            required_data=["price", "volume", "spread"],
            default_lookback=60,
            default_horizon=AlphaHorizon.DAILY,
            regime_sensitive=True,
            risk_controls={"max_stress": 2.0, "reduce_at": 1.5}
        )
        
        self.templates["liquidity_amihud"] = FeatureTemplate(
            name="Amihud Illiquidity",
            category=FeatureCategory.LIQUIDITY,
            formula_template="mean(abs(return) / volume, {lookback})",
            parameters={"lookback": [20, 60]},
            required_data=["price", "volume"],
            default_lookback=20,
            default_horizon=AlphaHorizon.DAILY,
            risk_controls={"max_illiquidity": 0.001}
        )
        
        # Flow templates
        self.templates["flow_imbalance"] = FeatureTemplate(
            name="Flow Imbalance",
            category=FeatureCategory.FLOW,
            formula_template="(buy_volume - sell_volume) / total_volume",
            parameters={"lookback": [5, 10, 20]},
            required_data=["volume", "trades"],
            default_lookback=10,
            default_horizon=AlphaHorizon.INTRADAY,
            risk_controls={"max_exposure": 0.1}
        )
        
        self.templates["flow_persistence"] = FeatureTemplate(
            name="Flow Imbalance Persistence",
            category=FeatureCategory.FLOW,
            formula_template="autocorr(flow_imbalance, {lag})",
            parameters={"lag": [1, 5, 10]},
            required_data=["volume", "trades"],
            default_lookback=20,
            default_horizon=AlphaHorizon.INTRADAY,
            risk_controls={"max_exposure": 0.1}
        )
        
        # Microstructure templates
        self.templates["microstructure_spread"] = FeatureTemplate(
            name="Bid-Ask Spread",
            category=FeatureCategory.MICROSTRUCTURE,
            formula_template="(ask - bid) / mid",
            parameters={"smoothing": [1, 5]},
            required_data=["order_book"],
            default_lookback=1,
            default_horizon=AlphaHorizon.MICROSTRUCTURE,
            risk_controls={"max_spread": 0.01}
        )
        
        self.templates["microstructure_depth_imbalance"] = FeatureTemplate(
            name="Order Book Depth Imbalance",
            category=FeatureCategory.MICROSTRUCTURE,
            formula_template="(bid_depth - ask_depth) / (bid_depth + ask_depth)",
            parameters={"levels": [1, 5, 10]},
            required_data=["order_book"],
            default_lookback=1,
            default_horizon=AlphaHorizon.MICROSTRUCTURE,
            risk_controls={"max_exposure": 0.05}
        )
        
        # Trend fragility
        self.templates["trend_fragility"] = FeatureTemplate(
            name="Trend Fragility Index",
            category=FeatureCategory.MOMENTUM,
            formula_template="1 - r_squared(price, time, {lookback})",
            parameters={"lookback": [10, 20, 60]},
            required_data=["price"],
            default_lookback=20,
            default_horizon=AlphaHorizon.DAILY,
            regime_sensitive=True,
            risk_controls={"max_fragility": 0.8}
        )
    
    def get_template(self, name: str) -> Optional[FeatureTemplate]:
        """Get a template by name"""
        return self.templates.get(name)
    
    def get_templates_by_category(self, category: FeatureCategory) -> List[FeatureTemplate]:
        """Get all templates in a category"""
        return [t for t in self.templates.values() if t.category == category]
    
    def get_templates_for_data(self, available_data: List[str]) -> List[FeatureTemplate]:
        """Get templates that can be computed with available data"""
        return [
            t for t in self.templates.values()
            if all(d in available_data for d in t.required_data)
        ]


class FeatureNormalizer:
    """
    Normalize features across regimes.
    
    Methods:
    - Z-score: (x - mean) / std
    - Min-max: (x - min) / (max - min)
    - Rank: percentile rank
    - Robust: (x - median) / IQR
    """
    
    def __init__(self, method: NormalizationMethod = NormalizationMethod.ZSCORE):
        self.method = method
        self._params: Dict[str, Any] = {}
    
    def fit(self, data: pd.Series, regime: Optional[RegimeType] = None):
        """Fit normalizer to data"""
        key = regime.value if regime else "all"
        
        if self.method == NormalizationMethod.ZSCORE:
            self._params[key] = {
                "mean": data.mean(),
                "std": data.std()
            }
        elif self.method == NormalizationMethod.MINMAX:
            self._params[key] = {
                "min": data.min(),
                "max": data.max()
            }
        elif self.method == NormalizationMethod.ROBUST:
            self._params[key] = {
                "median": data.median(),
                "iqr": data.quantile(0.75) - data.quantile(0.25)
            }
        elif self.method == NormalizationMethod.PERCENTILE:
            self._params[key] = {
                "values": data.sort_values().values
            }
    
    def transform(self, data: pd.Series, regime: Optional[RegimeType] = None) -> pd.Series:
        """Transform data using fitted parameters"""
        key = regime.value if regime else "all"
        params = self._params.get(key, self._params.get("all", {}))
        
        if self.method == NormalizationMethod.ZSCORE:
            mean = params.get("mean", data.mean())
            std = params.get("std", data.std())
            return (data - mean) / (std + 1e-10)
        
        elif self.method == NormalizationMethod.MINMAX:
            min_val = params.get("min", data.min())
            max_val = params.get("max", data.max())
            return (data - min_val) / (max_val - min_val + 1e-10)
        
        elif self.method == NormalizationMethod.ROBUST:
            median = params.get("median", data.median())
            iqr = params.get("iqr", data.quantile(0.75) - data.quantile(0.25))
            return (data - median) / (iqr + 1e-10)
        
        elif self.method == NormalizationMethod.RANK:
            return data.rank(pct=True)
        
        elif self.method == NormalizationMethod.PERCENTILE:
            return data.rank(pct=True) * 100
        
        return data
    
    def fit_transform(self, data: pd.Series, regime: Optional[RegimeType] = None) -> pd.Series:
        """Fit and transform in one step"""
        self.fit(data, regime)
        return self.transform(data, regime)


class FeatureSynthesizer:
    """
    Synthesize feature families from hypotheses.
    
    For each hypothesis:
    1. Identify relevant feature templates
    2. Generate parameter variations
    3. Create feature family with multiple features
    4. Add regime conditions and risk controls
    """
    
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        self.template_library = FeatureTemplateLibrary()
    
    def synthesize_from_hypothesis(self, hypothesis: Hypothesis) -> Optional[FeatureFamily]:
        """Synthesize a feature family from a hypothesis"""
        
        # Determine feature category from hypothesis
        category = self._infer_category(hypothesis)
        
        # Get relevant templates
        templates = self._get_relevant_templates(hypothesis, category)
        
        if not templates:
            logger.warning(f"No templates found for hypothesis {hypothesis.hypothesis_id}")
            return None
        
        # Generate features from templates
        features = []
        for template in templates:
            feature_variations = self._generate_variations(template, hypothesis)
            features.extend(feature_variations)
        
        if not features:
            return None
        
        # Create feature family
        family = FeatureFamily(
            family_id=generate_id("fam"),
            name=self._generate_family_name(hypothesis, category),
            hypothesis_id=hypothesis.hypothesis_id,
            features=features,
            alpha_source=hypothesis.causal_mechanism.cause,
            asset_class=AssetClass.MULTI_ASSET,  # Default
            time_horizon=self._infer_horizon(hypothesis),
            regime_conditions=hypothesis.regime_sensitivity,
            risk_controls=self._aggregate_risk_controls(features),
            capacity_limit_usd=self._estimate_capacity(hypothesis),
            expected_decay_days=self._estimate_decay(hypothesis),
            status=ProductionStatus.CANDIDATE
        )
        
        return family
    
    def _infer_category(self, hypothesis: Hypothesis) -> FeatureCategory:
        """Infer feature category from hypothesis"""
        cause_lower = hypothesis.causal_mechanism.cause.lower()
        effect_lower = hypothesis.causal_mechanism.effect.lower()
        
        category_keywords = {
            FeatureCategory.MOMENTUM: ["momentum", "trend", "continuation"],
            FeatureCategory.MEAN_REVERSION: ["reversion", "reversal", "contrarian"],
            FeatureCategory.VOLATILITY: ["volatility", "vol", "variance"],
            FeatureCategory.LIQUIDITY: ["liquidity", "spread", "depth"],
            FeatureCategory.FLOW: ["flow", "order", "trade"],
            FeatureCategory.SENTIMENT: ["sentiment", "news"],
            FeatureCategory.MICROSTRUCTURE: ["microstructure", "bid", "ask"]
        }
        
        for category, keywords in category_keywords.items():
            for kw in keywords:
                if kw in cause_lower or kw in effect_lower:
                    return category
        
        return FeatureCategory.MOMENTUM  # Default
    
    def _get_relevant_templates(
        self,
        hypothesis: Hypothesis,
        category: FeatureCategory
    ) -> List[FeatureTemplate]:
        """Get templates relevant to hypothesis"""
        # Get templates by category
        category_templates = self.template_library.get_templates_by_category(category)
        
        # Filter by available data
        available_data = hypothesis.required_data
        relevant = [
            t for t in category_templates
            if all(d in available_data or d == "price" for d in t.required_data)
        ]
        
        # If no category templates, try all templates with available data
        if not relevant:
            relevant = self.template_library.get_templates_for_data(available_data)
        
        return relevant[:5]  # Limit to 5 templates per hypothesis
    
    def _generate_variations(
        self,
        template: FeatureTemplate,
        hypothesis: Hypothesis
    ) -> List[FeatureDefinition]:
        """Generate feature variations from template"""
        features = []
        
        # Generate parameter combinations
        param_combinations = self._generate_param_combinations(template.parameters)
        
        for params in param_combinations[:3]:  # Limit variations
            feature = FeatureDefinition(
                feature_id=generate_id("feat"),
                name=f"{template.name}_{self._params_to_suffix(params)}",
                formula=template.formula_template.format(**params),
                parameters=params,
                time_horizon=template.default_horizon,
                lookback_period=params.get("lookback", template.default_lookback),
                normalization_method=template.normalization.value,
                regime_conditions=hypothesis.regime_sensitivity,
                risk_controls=template.risk_controls.copy()
            )
            features.append(feature)
        
        return features
    
    def _generate_param_combinations(self, parameters: Dict[str, List]) -> List[Dict]:
        """Generate parameter combinations"""
        if not parameters:
            return [{}]
        
        combinations = [{}]
        
        for param_name, param_values in parameters.items():
            new_combinations = []
            for combo in combinations:
                for value in param_values:
                    new_combo = combo.copy()
                    new_combo[param_name] = value
                    new_combinations.append(new_combo)
            combinations = new_combinations
        
        return combinations
    
    def _params_to_suffix(self, params: Dict) -> str:
        """Convert parameters to suffix string"""
        parts = [f"{k}{v}" for k, v in sorted(params.items())]
        return "_".join(parts)
    
    def _generate_family_name(self, hypothesis: Hypothesis, category: FeatureCategory) -> str:
        """Generate descriptive family name"""
        cause = hypothesis.causal_mechanism.cause.replace(" ", "_")[:20]
        return f"{category.value}_{cause}_family"
    
    def _infer_horizon(self, hypothesis: Hypothesis) -> AlphaHorizon:
        """Infer time horizon from hypothesis"""
        if hypothesis.causal_mechanism.time_lag:
            lag = hypothesis.causal_mechanism.time_lag.lower()
            if "day" in lag:
                return AlphaHorizon.DAILY
            elif "week" in lag:
                return AlphaHorizon.WEEKLY
            elif "month" in lag:
                return AlphaHorizon.MONTHLY
            elif "minute" in lag or "hour" in lag:
                return AlphaHorizon.INTRADAY
        return AlphaHorizon.DAILY
    
    def _aggregate_risk_controls(self, features: List[FeatureDefinition]) -> Dict[str, float]:
        """Aggregate risk controls from features"""
        controls = {}
        
        for feature in features:
            for key, value in feature.risk_controls.items():
                if key in controls:
                    controls[key] = min(controls[key], value)  # Use most conservative
                else:
                    controls[key] = value
        
        # Add default controls
        controls.setdefault("max_exposure", 0.1)
        controls.setdefault("max_drawdown", 0.05)
        
        return controls
    
    def _estimate_capacity(self, hypothesis: Hypothesis) -> float:
        """Estimate capacity limit in USD"""
        # Base capacity
        capacity = 10_000_000  # $10M default
        
        # Adjust based on horizon
        horizon_multipliers = {
            AlphaHorizon.TICK: 0.1,
            AlphaHorizon.MICROSTRUCTURE: 0.2,
            AlphaHorizon.INTRADAY: 0.5,
            AlphaHorizon.DAILY: 1.0,
            AlphaHorizon.WEEKLY: 2.0,
            AlphaHorizon.MONTHLY: 5.0
        }
        
        # Get horizon from time lag
        horizon = self._infer_horizon(hypothesis)
        multiplier = horizon_multipliers.get(horizon, 1.0)
        
        return capacity * multiplier
    
    def _estimate_decay(self, hypothesis: Hypothesis) -> int:
        """Estimate expected decay in days"""
        # Base decay
        decay = 90  # 90 days default
        
        # Adjust based on evidence strength
        strength = hypothesis.causal_mechanism.evidence_strength
        if strength == "weak":
            decay = 30
        elif strength == "moderate":
            decay = 60
        elif strength == "strong":
            decay = 120
        elif strength == "very_strong":
            decay = 180
        
        return decay


class FeatureSynthesisEngine:
    """
    Main engine for feature synthesis.
    
    Coordinates:
    - Feature synthesis from hypotheses
    - Normalization
    - Risk control assignment
    - Storage
    """
    
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        self.synthesizer = FeatureSynthesizer(config)
        
        logger.info("Feature Synthesis Engine initialized")
    
    def synthesize_from_hypotheses(
        self,
        hypotheses: List[Hypothesis]
    ) -> List[FeatureFamily]:
        """Synthesize feature families from hypotheses"""
        families = []
        
        for hypothesis in hypotheses:
            try:
                family = self.synthesizer.synthesize_from_hypothesis(hypothesis)
                if family:
                    families.append(family)
                    logger.info(
                        f"Synthesized family {family.family_id} with "
                        f"{len(family.features)} features from {hypothesis.hypothesis_id}"
                    )
                else:
                    logger.warning(
                        f"Could not synthesize family from {hypothesis.hypothesis_id}"
                    )
            except Exception as e:
                logger.error(f"Error synthesizing from {hypothesis.hypothesis_id}: {e}")
        
        return families
    
    def get_feature_count(self, families: List[FeatureFamily]) -> int:
        """Get total feature count across families"""
        return sum(len(f.features) for f in families)


def create_synthesis_engine(config: Optional[Dict] = None) -> FeatureSynthesisEngine:
    """Factory function to create feature synthesis engine"""
    return FeatureSynthesisEngine(config)
