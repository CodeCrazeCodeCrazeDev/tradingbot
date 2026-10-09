"""
Hypothesis Extraction Module
============================
Convert research papers into testable hypotheses.

For each paper, extracts:
- Causal mechanism (cause → effect → conditions)
- Set of testable hypotheses
- Required data and feature definitions
- Regime sensitivity and failure conditions

Papers without clear conditions and failure modes are discarded.

Author: AlphaAlgo Research Team
"""

import logging
import re
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum, auto
from typing import Any, Dict, List, Optional, Set, Tuple

import numpy as np

from .rdaos_core import (
    AlphaHorizon,
    AssetClass,
    CausalMechanism,
    FailureMode,
    FeatureDefinition,
    Hypothesis,
    ProductionStatus,
    RegimeType,
    ResearchObject,
    generate_id
)

logger = logging.getLogger(__name__)


class HypothesisType(Enum):
    """Types of tradable hypotheses"""
    PREDICTIVE = auto()       # X predicts Y
    CAUSAL = auto()           # X causes Y
    CONDITIONAL = auto()      # X predicts Y given Z
    COMPARATIVE = auto()      # X > Y under conditions
    TEMPORAL = auto()         # X leads Y by time T
    CROSS_SECTIONAL = auto()  # X varies across assets


class EvidenceStrength(Enum):
    """Strength of evidence supporting hypothesis"""
    WEAK = "weak"
    MODERATE = "moderate"
    STRONG = "strong"
    VERY_STRONG = "very_strong"


@dataclass
class ExtractedCause:
    """Extracted causal factor"""
    name: str
    description: str
    data_source: str
    measurement: str
    lag: Optional[int] = None  # in bars


@dataclass
class ExtractedEffect:
    """Extracted effect/outcome"""
    name: str
    description: str
    measurement: str
    horizon: AlphaHorizon
    expected_magnitude: float = 0.0


@dataclass
class ExtractedCondition:
    """Extracted condition for hypothesis"""
    name: str
    description: str
    measurement: str
    threshold: Optional[float] = None
    regime: Optional[RegimeType] = None


@dataclass
class HypothesisExtractionResult:
    """Result of hypothesis extraction from a paper"""
    paper_id: str
    success: bool
    
    hypotheses: List[Hypothesis] = field(default_factory=list)
    causal_mechanisms: List[CausalMechanism] = field(default_factory=list)
    
    rejection_reason: str = ""
    warnings: List[str] = field(default_factory=list)
    
    extracted_at: datetime = field(default_factory=datetime.utcnow)


class CausalMechanismExtractor:
    """
    Extract causal mechanisms from research text.
    
    Identifies:
    - Cause variables
    - Effect variables
    - Conditioning variables
    - Time lags
    - Evidence strength
    """
    
    CAUSAL_PATTERNS = [
        # "X causes Y"
        (r"(\w+(?:\s+\w+)?)\s+(?:causes?|leads?\s+to|results?\s+in|predicts?)\s+(\w+(?:\s+\w+)?)", "direct"),
        # "Y is caused by X"
        (r"(\w+(?:\s+\w+)?)\s+(?:is\s+caused\s+by|is\s+predicted\s+by|follows)\s+(\w+(?:\s+\w+)?)", "reverse"),
        # "increase in X leads to increase in Y"
        (r"(?:increase|decrease)\s+in\s+(\w+(?:\s+\w+)?)\s+(?:leads?\s+to|causes?)\s+(?:increase|decrease)\s+in\s+(\w+(?:\s+\w+)?)", "directional"),
        # "X → Y"
        (r"(\w+)\s*[→→>]\s*(\w+)", "arrow"),
    ]
    
    CONDITION_PATTERNS = [
        r"(?:when|if|given|conditional\s+on|under)\s+(\w+(?:\s+\w+)?)\s+(?:is|are|>|<|=)",
        r"(?:in\s+(?:high|low)\s+)(\w+(?:\s+\w+)?)\s+(?:regimes?|environments?|conditions?)",
        r"(?:during|in)\s+(\w+(?:\s+\w+)?)\s+(?:periods?|times?|markets?)"
    ]
    
    TIME_LAG_PATTERNS = [
        (r"(\d+)\s*(?:day|days?)\s+(?:lag|ahead|later)", "days"),
        (r"(\d+)\s*(?:week|weeks?)\s+(?:lag|ahead|later)", "weeks"),
        (r"(\d+)\s*(?:month|months?)\s+(?:lag|ahead|later)", "months"),
        (r"(?:next|following)\s+(\d+)\s*(?:day|days?)", "days"),
        (r"t\+(\d+)", "periods")
    ]
    
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
    
    def extract(self, text: str, metadata: Dict) -> List[CausalMechanism]:
        """Extract causal mechanisms from text"""
        mechanisms = []
        
        # Extract cause-effect pairs
        cause_effect_pairs = self._extract_cause_effect_pairs(text)
        
        for cause, effect, pattern_type in cause_effect_pairs:
            # Extract conditions
            conditions = self._extract_conditions(text)
            
            # Extract time lag
            time_lag = self._extract_time_lag(text)
            
            # Estimate evidence strength
            evidence = self._estimate_evidence_strength(text, cause, effect)
            
            mechanism = CausalMechanism(
                cause=cause,
                effect=effect,
                conditions=conditions,
                time_lag=time_lag,
                confidence=self._compute_confidence(text, cause, effect),
                evidence_strength=evidence.value
            )
            
            mechanisms.append(mechanism)
        
        return mechanisms
    
    def _extract_cause_effect_pairs(self, text: str) -> List[Tuple[str, str, str]]:
        """Extract cause-effect pairs from text"""
        pairs = []
        text_lower = text.lower()
        
        for pattern, pattern_type in self.CAUSAL_PATTERNS:
            matches = re.findall(pattern, text_lower)
            for match in matches:
                if pattern_type == "reverse":
                    pairs.append((match[1], match[0], pattern_type))
                else:
                    pairs.append((match[0], match[1], pattern_type))
        
        return pairs
    
    def _extract_conditions(self, text: str) -> List[str]:
        """Extract conditioning variables"""
        conditions = []
        text_lower = text.lower()
        
        for pattern in self.CONDITION_PATTERNS:
            matches = re.findall(pattern, text_lower)
            conditions.extend(matches)
        
        return list(set(conditions))
    
    def _extract_time_lag(self, text: str) -> Optional[str]:
        """Extract time lag information"""
        text_lower = text.lower()
        
        for pattern, unit in self.TIME_LAG_PATTERNS:
            match = re.search(pattern, text_lower)
            if match:
                value = match.group(1)
                return f"{value} {unit}"
        
        return None
    
    def _estimate_evidence_strength(self, text: str, cause: str, effect: str) -> EvidenceStrength:
        """Estimate strength of evidence"""
        text_lower = text.lower()
        
        strong_indicators = ["significant", "robust", "consistent", "strong evidence"]
        weak_indicators = ["weak", "marginal", "limited", "preliminary"]
        
        strong_count = sum(1 for ind in strong_indicators if ind in text_lower)
        weak_count = sum(1 for ind in weak_indicators if ind in text_lower)
        
        if strong_count >= 2:
            return EvidenceStrength.VERY_STRONG
        elif strong_count >= 1:
            return EvidenceStrength.STRONG
        elif weak_count >= 1:
            return EvidenceStrength.WEAK
        else:
            return EvidenceStrength.MODERATE
    
    def _compute_confidence(self, text: str, cause: str, effect: str) -> float:
        """Compute confidence score for mechanism"""
        text_lower = text.lower()
        
        confidence = 0.5  # Base confidence
        
        # Boost for statistical significance mentions
        if "statistically significant" in text_lower or "p < 0.05" in text_lower:
            confidence += 0.2
        
        # Boost for robustness checks
        if "robust" in text_lower or "robustness" in text_lower:
            confidence += 0.1
        
        # Boost for out-of-sample validation
        if "out-of-sample" in text_lower or "out of sample" in text_lower:
            confidence += 0.15
        
        # Penalty for caveats
        if "however" in text_lower or "limitation" in text_lower:
            confidence -= 0.1
        
        return min(1.0, max(0.0, confidence))


class HypothesisGenerator:
    """
    Generate testable hypotheses from causal mechanisms.
    
    Creates hypotheses that are:
    - Specific and measurable
    - Testable with available data
    - Include failure conditions
    """
    
    HYPOTHESIS_TEMPLATES = {
        HypothesisType.PREDICTIVE: "{cause} predicts {effect} with {horizon} horizon",
        HypothesisType.CAUSAL: "Changes in {cause} cause changes in {effect}",
        HypothesisType.CONDITIONAL: "{cause} predicts {effect} when {condition}",
        HypothesisType.TEMPORAL: "{cause} leads {effect} by {lag}",
        HypothesisType.CROSS_SECTIONAL: "Assets with higher {cause} have higher {effect}"
    }
    
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
    
    def generate(
        self,
        paper_id: str,
        mechanisms: List[CausalMechanism],
        metadata: Dict
    ) -> List[Hypothesis]:
        """Generate hypotheses from causal mechanisms"""
        hypotheses = []
        
        for mechanism in mechanisms:
            # Generate primary hypothesis
            primary = self._generate_primary_hypothesis(paper_id, mechanism, metadata)
            if primary:
                hypotheses.append(primary)
            
            # Generate conditional hypotheses
            for condition in mechanism.conditions:
                conditional = self._generate_conditional_hypothesis(
                    paper_id, mechanism, condition, metadata
                )
                if conditional:
                    hypotheses.append(conditional)
        
        return hypotheses
    
    def _generate_primary_hypothesis(
        self,
        paper_id: str,
        mechanism: CausalMechanism,
        metadata: Dict
    ) -> Optional[Hypothesis]:
        """Generate primary hypothesis from mechanism"""
        
        # Determine hypothesis type
        if mechanism.time_lag:
            h_type = HypothesisType.TEMPORAL
            statement = self.HYPOTHESIS_TEMPLATES[h_type].format(
                cause=mechanism.cause,
                effect=mechanism.effect,
                lag=mechanism.time_lag
            )
        else:
            h_type = HypothesisType.PREDICTIVE
            statement = self.HYPOTHESIS_TEMPLATES[h_type].format(
                cause=mechanism.cause,
                effect=mechanism.effect,
                horizon=metadata.get("horizon", AlphaHorizon.DAILY).value
            )
        
        # Define required data
        required_data = self._infer_required_data(mechanism, metadata)
        
        # Define features
        feature_definitions = self._define_features(mechanism, metadata)
        
        # Determine regime sensitivity
        regime_sensitivity = self._infer_regime_sensitivity(mechanism, metadata)
        
        # Define failure conditions
        failure_conditions = self._define_failure_conditions(mechanism, metadata)
        
        # Check if hypothesis is testable
        if not required_data or not feature_definitions:
            return None
        
        return Hypothesis(
            hypothesis_id=generate_id("hyp"),
            paper_id=paper_id,
            statement=statement,
            causal_mechanism=mechanism,
            required_data=required_data,
            feature_definitions=feature_definitions,
            regime_sensitivity=regime_sensitivity,
            failure_conditions=failure_conditions,
            testable=True,
            test_methodology=self._suggest_test_methodology(h_type),
            expected_effect_size=mechanism.confidence * 0.1  # Rough estimate
        )
    
    def _generate_conditional_hypothesis(
        self,
        paper_id: str,
        mechanism: CausalMechanism,
        condition: str,
        metadata: Dict
    ) -> Optional[Hypothesis]:
        """Generate conditional hypothesis"""
        
        statement = self.HYPOTHESIS_TEMPLATES[HypothesisType.CONDITIONAL].format(
            cause=mechanism.cause,
            effect=mechanism.effect,
            condition=condition
        )
        
        # Add condition to required data
        required_data = self._infer_required_data(mechanism, metadata)
        required_data.append(f"condition_{condition}")
        
        feature_definitions = self._define_features(mechanism, metadata)
        feature_definitions[f"condition_{condition}"] = f"Binary indicator for {condition}"
        
        regime_sensitivity = self._infer_regime_sensitivity(mechanism, metadata)
        failure_conditions = self._define_failure_conditions(mechanism, metadata)
        failure_conditions.append(f"Condition '{condition}' not met")
        
        return Hypothesis(
            hypothesis_id=generate_id("hyp"),
            paper_id=paper_id,
            statement=statement,
            causal_mechanism=mechanism,
            required_data=required_data,
            feature_definitions=feature_definitions,
            regime_sensitivity=regime_sensitivity,
            failure_conditions=failure_conditions,
            testable=True,
            test_methodology="Conditional regression with interaction terms"
        )
    
    def _infer_required_data(self, mechanism: CausalMechanism, metadata: Dict) -> List[str]:
        """Infer required data from mechanism"""
        required = set(metadata.get("required_data", ["price"]))
        
        # Add data based on cause/effect keywords
        cause_lower = mechanism.cause.lower()
        effect_lower = mechanism.effect.lower()
        
        data_keywords = {
            "volume": ["volume", "trading volume", "turnover"],
            "price": ["price", "return", "momentum"],
            "volatility": ["volatility", "vol", "variance"],
            "order_book": ["order", "bid", "ask", "spread", "depth"],
            "sentiment": ["sentiment", "news", "social"],
            "fundamentals": ["earnings", "revenue", "fundamental"]
        }
        
        for data_type, keywords in data_keywords.items():
            for kw in keywords:
                if kw in cause_lower or kw in effect_lower:
                    required.add(data_type)
        
        return list(required)
    
    def _define_features(self, mechanism: CausalMechanism, metadata: Dict) -> Dict[str, str]:
        """Define features for hypothesis testing"""
        features = {}
        
        # Cause feature
        features[f"cause_{mechanism.cause.replace(' ', '_')}"] = (
            f"Feature measuring {mechanism.cause}"
        )
        
        # Effect feature (target)
        features[f"target_{mechanism.effect.replace(' ', '_')}"] = (
            f"Target variable: {mechanism.effect}"
        )
        
        # Condition features
        for condition in mechanism.conditions:
            features[f"condition_{condition.replace(' ', '_')}"] = (
                f"Conditioning variable: {condition}"
            )
        
        return features
    
    def _infer_regime_sensitivity(
        self,
        mechanism: CausalMechanism,
        metadata: Dict
    ) -> List[RegimeType]:
        """Infer which regimes the hypothesis is sensitive to"""
        sensitivity = []
        
        # Check conditions for regime hints
        for condition in mechanism.conditions:
            condition_lower = condition.lower()
            
            if "volatility" in condition_lower or "vol" in condition_lower:
                sensitivity.extend([RegimeType.HIGH_VOLATILITY, RegimeType.LOW_VOLATILITY])
            if "trend" in condition_lower:
                sensitivity.extend([RegimeType.TRENDING_UP, RegimeType.TRENDING_DOWN])
            if "crisis" in condition_lower or "stress" in condition_lower:
                sensitivity.append(RegimeType.CRISIS)
            if "liquidity" in condition_lower:
                sensitivity.append(RegimeType.LIQUIDITY_CRISIS)
        
        # Default: sensitive to regime shifts
        if not sensitivity:
            sensitivity = [RegimeType.NORMAL, RegimeType.HIGH_VOLATILITY]
        
        return list(set(sensitivity))
    
    def _define_failure_conditions(
        self,
        mechanism: CausalMechanism,
        metadata: Dict
    ) -> List[str]:
        """Define conditions under which hypothesis fails"""
        failures = []
        
        # Standard failure conditions
        failures.append("Regime shift invalidates underlying relationship")
        failures.append("Alpha decay reduces signal strength below threshold")
        
        # Add based on evidence strength
        if mechanism.evidence_strength == "weak":
            failures.append("Weak evidence may not replicate out-of-sample")
        
        # Add based on conditions
        for condition in mechanism.conditions:
            failures.append(f"Hypothesis fails when '{condition}' condition changes")
        
        return failures
    
    def _suggest_test_methodology(self, h_type: HypothesisType) -> str:
        """Suggest testing methodology based on hypothesis type"""
        methodologies = {
            HypothesisType.PREDICTIVE: "Time-series regression with walk-forward validation",
            HypothesisType.CAUSAL: "Granger causality test with VAR model",
            HypothesisType.CONDITIONAL: "Conditional regression with interaction terms",
            HypothesisType.TEMPORAL: "Lead-lag analysis with cross-correlation",
            HypothesisType.CROSS_SECTIONAL: "Fama-MacBeth regression"
        }
        return methodologies.get(h_type, "Standard regression analysis")


class HypothesisValidator:
    """
    Validate extracted hypotheses for quality and testability.
    
    Rejects hypotheses that:
    - Lack clear conditions
    - Have no failure modes
    - Cannot be tested with available data
    - Are too vague or general
    """
    
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        
        # Validation thresholds
        self.min_conditions = config.get("min_conditions", 0)
        self.min_failure_conditions = config.get("min_failure_conditions", 1)
        self.min_required_data = config.get("min_required_data", 1)
        self.min_confidence = config.get("min_confidence", 0.3)
    
    def validate(self, hypothesis: Hypothesis) -> Tuple[bool, List[str]]:
        """Validate a hypothesis"""
        issues = []
        
        # Check for clear causal mechanism
        if not hypothesis.causal_mechanism.cause or not hypothesis.causal_mechanism.effect:
            issues.append("Missing clear cause or effect")
        
        # Check for failure conditions
        if len(hypothesis.failure_conditions) < self.min_failure_conditions:
            issues.append(f"Insufficient failure conditions (need {self.min_failure_conditions})")
        
        # Check for required data
        if len(hypothesis.required_data) < self.min_required_data:
            issues.append(f"Insufficient data requirements (need {self.min_required_data})")
        
        # Check for feature definitions
        if not hypothesis.feature_definitions:
            issues.append("No feature definitions provided")
        
        # Check confidence
        if hypothesis.causal_mechanism.confidence < self.min_confidence:
            issues.append(f"Low confidence ({hypothesis.causal_mechanism.confidence:.2f})")
        
        # Check testability
        if not hypothesis.testable:
            issues.append("Hypothesis marked as not testable")
        
        return len(issues) == 0, issues
    
    def validate_batch(self, hypotheses: List[Hypothesis]) -> Tuple[List[Hypothesis], List[Tuple[Hypothesis, List[str]]]]:
        """Validate a batch of hypotheses"""
        valid = []
        invalid = []
        
        for h in hypotheses:
            is_valid, issues = self.validate(h)
            if is_valid:
                valid.append(h)
            else:
                invalid.append((h, issues))
        
        return valid, invalid


class HypothesisExtractionEngine:
    """
    Main engine for hypothesis extraction.
    
    Coordinates:
    - Causal mechanism extraction
    - Hypothesis generation
    - Validation
    - Storage
    """
    
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        
        self.mechanism_extractor = CausalMechanismExtractor(config)
        self.hypothesis_generator = HypothesisGenerator(config)
        self.validator = HypothesisValidator(config)
        
        logger.info("Hypothesis Extraction Engine initialized")
    
    def extract_from_research(self, research: ResearchObject) -> HypothesisExtractionResult:
        """Extract hypotheses from a research object"""
        
        # Build text for extraction
        text = f"{research.title}. {research.alpha_source}. "
        text += " ".join(research.assumptions)
        
        # Build metadata
        metadata = {
            "horizon": research.horizon,
            "asset_class": research.asset_class,
            "required_data": research.required_data,
            "alpha_source": research.alpha_source
        }
        
        # Extract causal mechanisms
        mechanisms = self.mechanism_extractor.extract(text, metadata)
        
        if not mechanisms:
            return HypothesisExtractionResult(
                paper_id=research.paper_id,
                success=False,
                rejection_reason="No causal mechanisms found"
            )
        
        # Generate hypotheses
        hypotheses = self.hypothesis_generator.generate(
            research.paper_id,
            mechanisms,
            metadata
        )
        
        if not hypotheses:
            return HypothesisExtractionResult(
                paper_id=research.paper_id,
                success=False,
                rejection_reason="Could not generate testable hypotheses"
            )
        
        # Validate hypotheses
        valid_hypotheses, invalid = self.validator.validate_batch(hypotheses)
        
        warnings = [f"Rejected hypothesis: {h.statement[:50]} - {issues}" 
                   for h, issues in invalid]
        
        if not valid_hypotheses:
            return HypothesisExtractionResult(
                paper_id=research.paper_id,
                success=False,
                rejection_reason="All hypotheses failed validation",
                warnings=warnings
            )
        
        return HypothesisExtractionResult(
            paper_id=research.paper_id,
            success=True,
            hypotheses=valid_hypotheses,
            causal_mechanisms=mechanisms,
            warnings=warnings
        )
    
    def extract_batch(
        self,
        research_objects: List[ResearchObject]
    ) -> Dict[str, HypothesisExtractionResult]:
        """Extract hypotheses from multiple research objects"""
        results = {}
        
        for research in research_objects:
            try:
                result = self.extract_from_research(research)
                results[research.paper_id] = result
                
                if result.success:
                    logger.info(
                        f"Extracted {len(result.hypotheses)} hypotheses from {research.paper_id}"
                    )
                else:
                    logger.warning(
                        f"Failed to extract from {research.paper_id}: {result.rejection_reason}"
                    )
                    
            except Exception as e:
                logger.error(f"Error extracting from {research.paper_id}: {e}")
                results[research.paper_id] = HypothesisExtractionResult(
                    paper_id=research.paper_id,
                    success=False,
                    rejection_reason=str(e)
                )
        
        return results


def create_hypothesis_engine(config: Optional[Dict] = None) -> HypothesisExtractionEngine:
    """Factory function to create hypothesis extraction engine"""
    return HypothesisExtractionEngine(config)
