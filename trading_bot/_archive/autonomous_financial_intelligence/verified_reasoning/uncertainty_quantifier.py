"""
Uncertainty Quantifier

Precise uncertainty quantification and propagation through reasoning chains.
Ensures confidence scores accurately reflect actual uncertainty.
"""

import asyncio
import math
import json
import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Set, Tuple
from dataclasses import dataclass, field
from pathlib import Path
from enum import Enum
import uuid

logger = logging.getLogger(__name__)


class UncertaintyType(Enum):
    """Types of uncertainty."""
    ALEATORY = "aleatory"
    EPISTEMIC = "epistemic"
    MODEL = "model"
    DATA = "data"
    PARAMETER = "parameter"
    STRUCTURAL = "structural"


class PropagationMethod(Enum):
    """Methods for propagating uncertainty."""
    LINEAR = "linear"
    MONTE_CARLO = "monte_carlo"
    BAYESIAN = "bayesian"
    INTERVAL = "interval"
    FUZZY = "fuzzy"


@dataclass
class UncertaintySource:
    """A source of uncertainty."""
    source_id: str
    source_name: str
    uncertainty_type: UncertaintyType
    magnitude: float
    confidence_interval: Tuple[float, float]
    description: str
    is_reducible: bool
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'source_id': self.source_id,
            'source_name': self.source_name,
            'uncertainty_type': self.uncertainty_type.value,
            'magnitude': self.magnitude,
            'confidence_interval': self.confidence_interval,
            'description': self.description,
            'is_reducible': self.is_reducible,
        }


@dataclass
class UncertaintyEstimate:
    """Estimate of uncertainty for a value or claim."""
    estimate_id: str
    value: float
    uncertainty: float
    confidence_level: float
    lower_bound: float
    upper_bound: float
    sources: List[UncertaintySource]
    method_used: PropagationMethod
    timestamp: datetime
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'estimate_id': self.estimate_id,
            'value': self.value,
            'uncertainty': self.uncertainty,
            'confidence_level': self.confidence_level,
            'lower_bound': self.lower_bound,
            'upper_bound': self.upper_bound,
            'sources': [s.to_dict() for s in self.sources],
            'method_used': self.method_used.value,
            'timestamp': self.timestamp.isoformat(),
            'metadata': self.metadata,
        }


@dataclass
class PropagatedUncertainty:
    """Uncertainty propagated through a reasoning chain."""
    propagation_id: str
    chain_id: str
    initial_uncertainty: float
    final_uncertainty: float
    uncertainty_growth: float
    step_uncertainties: List[Dict[str, Any]]
    dominant_sources: List[str]
    confidence_degradation: float
    is_acceptable: bool
    recommendations: List[str]
    timestamp: datetime
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'propagation_id': self.propagation_id,
            'chain_id': self.chain_id,
            'initial_uncertainty': self.initial_uncertainty,
            'final_uncertainty': self.final_uncertainty,
            'uncertainty_growth': self.uncertainty_growth,
            'step_uncertainties': self.step_uncertainties,
            'dominant_sources': self.dominant_sources,
            'confidence_degradation': self.confidence_degradation,
            'is_acceptable': self.is_acceptable,
            'recommendations': self.recommendations,
            'timestamp': self.timestamp.isoformat(),
        }


class UncertaintyQuantifier:
    """
    Quantifies and propagates uncertainty through reasoning.
    
    Provides:
    - Uncertainty estimation from multiple sources
    - Propagation through reasoning chains
    - Confidence interval calculation
    - Sensitivity analysis
    - Uncertainty reduction recommendations
    """
    
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        self.storage_path = Path(self.config.get('storage_path', 'uncertainty_data'))
        self.storage_path.mkdir(parents=True, exist_ok=True)
        
        self._estimates: Dict[str, UncertaintyEstimate] = {}
        self._propagations: Dict[str, PropagatedUncertainty] = {}
        
        self._uncertainty_config = {
            'default_confidence_level': 0.95,
            'maximum_acceptable_uncertainty': 0.3,
            'uncertainty_growth_factor': 1.1,
            'epistemic_weight': 1.2,
            'aleatory_weight': 1.0,
        }
        
        self._source_uncertainty_defaults = {
            'market_data': 0.02,
            'model_prediction': 0.15,
            'expert_opinion': 0.20,
            'historical_data': 0.05,
            'real_time_feed': 0.03,
            'aggregated_source': 0.08,
            'internal_calculation': 0.10,
        }
        
        logger.info("✅ Uncertainty Quantifier initialized")
    
    async def estimate_uncertainty(
        self,
        value: float,
        sources: List[Dict[str, Any]],
        confidence_level: Optional[float] = None,
    ) -> UncertaintyEstimate:
        """
        Estimate uncertainty for a value from multiple sources.
        
        Args:
            value: The value to estimate uncertainty for
            sources: List of uncertainty sources
            confidence_level: Desired confidence level (default 0.95)
        
        Returns:
            UncertaintyEstimate
        """
        estimate_id = f"UE-{uuid.uuid4().hex[:12]}"
        confidence_level = confidence_level or self._uncertainty_config['default_confidence_level']
        
        uncertainty_sources = []
        for source in sources:
            us = UncertaintySource(
                source_id=f"US-{uuid.uuid4().hex[:8]}",
                source_name=source.get('name', 'unknown'),
                uncertainty_type=UncertaintyType(source.get('type', 'epistemic')),
                magnitude=source.get('magnitude', self._get_default_uncertainty(source.get('name', ''))),
                confidence_interval=source.get('confidence_interval', (0.0, 1.0)),
                description=source.get('description', ''),
                is_reducible=source.get('is_reducible', True),
            )
            uncertainty_sources.append(us)
        
        combined_uncertainty = self._combine_uncertainties(uncertainty_sources)
        
        z_score = self._get_z_score(confidence_level)
        margin = combined_uncertainty * z_score
        
        lower_bound = value - margin
        upper_bound = value + margin
        
        estimate = UncertaintyEstimate(
            estimate_id=estimate_id,
            value=value,
            uncertainty=combined_uncertainty,
            confidence_level=confidence_level,
            lower_bound=lower_bound,
            upper_bound=upper_bound,
            sources=uncertainty_sources,
            method_used=PropagationMethod.LINEAR,
            timestamp=datetime.now(timezone.utc),
        )
        
        self._estimates[estimate_id] = estimate
        
        return estimate
    
    def _get_default_uncertainty(self, source_name: str) -> float:
        """Get default uncertainty for a source type."""
        source_lower = source_name.lower()
        
        for key, value in self._source_uncertainty_defaults.items():
            if key in source_lower:
                return value
        
        return 0.10
    
    def _combine_uncertainties(
        self,
        sources: List[UncertaintySource],
    ) -> float:
        """Combine uncertainties from multiple sources."""
        if not sources:
            return 0.0
        
        weighted_variances = []
        
        for source in sources:
            weight = (
                self._uncertainty_config['epistemic_weight']
                if source.uncertainty_type == UncertaintyType.EPISTEMIC
                else self._uncertainty_config['aleatory_weight']
            )
            
            variance = source.magnitude ** 2
            weighted_variances.append(variance * weight)
        
        combined_variance = sum(weighted_variances)
        combined_uncertainty = math.sqrt(combined_variance)
        
        return combined_uncertainty
    
    def _get_z_score(self, confidence_level: float) -> float:
        """Get z-score for a confidence level."""
        z_scores = {
            0.90: 1.645,
            0.95: 1.96,
            0.99: 2.576,
            0.999: 3.291,
        }
        
        closest = min(z_scores.keys(), key=lambda x: abs(x - confidence_level))
        return z_scores[closest]
    
    async def propagate_through_chain(
        self,
        chain_id: str,
        step_uncertainties: List[Dict[str, Any]],
        method: PropagationMethod = PropagationMethod.LINEAR,
    ) -> PropagatedUncertainty:
        """
        Propagate uncertainty through a reasoning chain.
        
        Args:
            chain_id: ID of the reasoning chain
            step_uncertainties: Uncertainty at each step
            method: Propagation method to use
        
        Returns:
            PropagatedUncertainty
        """
        propagation_id = f"PU-{uuid.uuid4().hex[:12]}"
        
        if not step_uncertainties:
            return PropagatedUncertainty(
                propagation_id=propagation_id,
                chain_id=chain_id,
                initial_uncertainty=0.0,
                final_uncertainty=0.0,
                uncertainty_growth=0.0,
                step_uncertainties=[],
                dominant_sources=[],
                confidence_degradation=0.0,
                is_acceptable=True,
                recommendations=[],
                timestamp=datetime.now(timezone.utc),
            )
        
        initial_uncertainty = step_uncertainties[0].get('uncertainty', 0.0)
        
        propagated_steps = []
        current_uncertainty = initial_uncertainty
        
        for i, step in enumerate(step_uncertainties):
            step_uncertainty = step.get('uncertainty', 0.0)
            
            if method == PropagationMethod.LINEAR:
                combined = math.sqrt(current_uncertainty**2 + step_uncertainty**2)
                combined *= self._uncertainty_config['uncertainty_growth_factor']
            elif method == PropagationMethod.BAYESIAN:
                combined = 1 - (1 - current_uncertainty) * (1 - step_uncertainty)
            else:
                combined = max(current_uncertainty, step_uncertainty) * 1.1
            
            propagated_steps.append({
                'step': i + 1,
                'input_uncertainty': current_uncertainty,
                'step_uncertainty': step_uncertainty,
                'output_uncertainty': combined,
                'sources': step.get('sources', []),
            })
            
            current_uncertainty = combined
        
        final_uncertainty = current_uncertainty
        uncertainty_growth = final_uncertainty - initial_uncertainty
        
        all_sources = []
        for step in step_uncertainties:
            all_sources.extend(step.get('sources', []))
        
        source_contributions = {}
        for source in all_sources:
            name = source.get('name', 'unknown')
            mag = source.get('magnitude', 0.0)
            source_contributions[name] = source_contributions.get(name, 0) + mag
        
        dominant_sources = sorted(
            source_contributions.keys(),
            key=lambda x: source_contributions[x],
            reverse=True
        )[:3]
        
        initial_confidence = 1 - initial_uncertainty
        final_confidence = 1 - min(final_uncertainty, 0.99)
        confidence_degradation = initial_confidence - final_confidence
        
        max_acceptable = self._uncertainty_config['maximum_acceptable_uncertainty']
        is_acceptable = final_uncertainty <= max_acceptable
        
        recommendations = self._generate_uncertainty_recommendations(
            final_uncertainty, dominant_sources, propagated_steps
        )
        
        propagation = PropagatedUncertainty(
            propagation_id=propagation_id,
            chain_id=chain_id,
            initial_uncertainty=initial_uncertainty,
            final_uncertainty=final_uncertainty,
            uncertainty_growth=uncertainty_growth,
            step_uncertainties=propagated_steps,
            dominant_sources=dominant_sources,
            confidence_degradation=confidence_degradation,
            is_acceptable=is_acceptable,
            recommendations=recommendations,
            timestamp=datetime.now(timezone.utc),
        )
        
        self._propagations[propagation_id] = propagation
        await self._persist_propagation(propagation)
        
        logger.info(f"Propagated uncertainty for chain {chain_id}: "
                   f"{initial_uncertainty:.3f} -> {final_uncertainty:.3f}")
        
        return propagation
    
    def _generate_uncertainty_recommendations(
        self,
        final_uncertainty: float,
        dominant_sources: List[str],
        steps: List[Dict[str, Any]],
    ) -> List[str]:
        """Generate recommendations for reducing uncertainty."""
        recommendations = []
        
        max_acceptable = self._uncertainty_config['maximum_acceptable_uncertainty']
        
        if final_uncertainty > max_acceptable:
            recommendations.append(
                f"Final uncertainty ({final_uncertainty:.1%}) exceeds acceptable threshold ({max_acceptable:.1%})"
            )
        
        if dominant_sources:
            recommendations.append(
                f"Focus on reducing uncertainty from: {', '.join(dominant_sources[:2])}"
            )
        
        high_growth_steps = [
            s for s in steps
            if s['output_uncertainty'] - s['input_uncertainty'] > 0.05
        ]
        if high_growth_steps:
            recommendations.append(
                f"Steps {[s['step'] for s in high_growth_steps]} show high uncertainty growth"
            )
        
        if final_uncertainty > 0.2:
            recommendations.append("Consider adding more evidence sources to reduce epistemic uncertainty")
        
        return recommendations
    
    async def sensitivity_analysis(
        self,
        estimate: UncertaintyEstimate,
        perturbation: float = 0.1,
    ) -> Dict[str, Any]:
        """
        Perform sensitivity analysis on an uncertainty estimate.
        
        Args:
            estimate: The estimate to analyze
            perturbation: Perturbation factor for analysis
        
        Returns:
            Sensitivity analysis results
        """
        sensitivities = {}
        
        for source in estimate.sources:
            original_magnitude = source.magnitude
            
            source.magnitude = original_magnitude * (1 + perturbation)
            increased_uncertainty = self._combine_uncertainties(estimate.sources)
            
            source.magnitude = original_magnitude * (1 - perturbation)
            decreased_uncertainty = self._combine_uncertainties(estimate.sources)
            
            source.magnitude = original_magnitude
            
            sensitivity = (increased_uncertainty - decreased_uncertainty) / (2 * perturbation * original_magnitude)
            
            sensitivities[source.source_name] = {
                'sensitivity': sensitivity,
                'impact_rank': 0,
                'original_magnitude': original_magnitude,
            }
        
        sorted_sources = sorted(
            sensitivities.keys(),
            key=lambda x: abs(sensitivities[x]['sensitivity']),
            reverse=True
        )
        
        for rank, source_name in enumerate(sorted_sources, 1):
            sensitivities[source_name]['impact_rank'] = rank
        
        return {
            'estimate_id': estimate.estimate_id,
            'sensitivities': sensitivities,
            'most_sensitive': sorted_sources[0] if sorted_sources else None,
            'perturbation_used': perturbation,
        }
    
    async def calibrate_confidence(
        self,
        predicted_confidence: float,
        actual_outcomes: List[bool],
        predictions: List[float],
    ) -> Dict[str, Any]:
        """
        Calibrate confidence scores against actual outcomes.
        
        Args:
            predicted_confidence: The predicted confidence level
            actual_outcomes: List of actual outcomes (True/False)
            predictions: List of predicted probabilities
        
        Returns:
            Calibration results
        """
        if not actual_outcomes or not predictions:
            return {
                'is_calibrated': False,
                'error': 'Insufficient data for calibration',
            }
        
        bins = [0.0, 0.2, 0.4, 0.6, 0.8, 1.0]
        bin_data = {i: {'predictions': [], 'outcomes': []} for i in range(len(bins) - 1)}
        
        for pred, outcome in zip(predictions, actual_outcomes):
            for i in range(len(bins) - 1):
                if bins[i] <= pred < bins[i + 1]:
                    bin_data[i]['predictions'].append(pred)
                    bin_data[i]['outcomes'].append(1 if outcome else 0)
                    break
        
        calibration_errors = []
        for i, data in bin_data.items():
            if data['predictions']:
                avg_pred = sum(data['predictions']) / len(data['predictions'])
                avg_outcome = sum(data['outcomes']) / len(data['outcomes'])
                calibration_errors.append(abs(avg_pred - avg_outcome))
        
        expected_calibration_error = sum(calibration_errors) / len(calibration_errors) if calibration_errors else 0
        
        is_calibrated = expected_calibration_error < 0.1
        
        if expected_calibration_error > 0:
            adjustment_factor = 1 - expected_calibration_error
        else:
            adjustment_factor = 1.0
        
        return {
            'is_calibrated': is_calibrated,
            'expected_calibration_error': expected_calibration_error,
            'adjustment_factor': adjustment_factor,
            'calibrated_confidence': predicted_confidence * adjustment_factor,
            'bin_statistics': {
                i: {
                    'count': len(data['predictions']),
                    'avg_prediction': sum(data['predictions']) / len(data['predictions']) if data['predictions'] else 0,
                    'avg_outcome': sum(data['outcomes']) / len(data['outcomes']) if data['outcomes'] else 0,
                }
                for i, data in bin_data.items()
            },
        }
    
    def get_estimate(self, estimate_id: str) -> Optional[UncertaintyEstimate]:
        """Get an uncertainty estimate by ID."""
        return self._estimates.get(estimate_id)
    
    def get_propagation(self, propagation_id: str) -> Optional[PropagatedUncertainty]:
        """Get a propagation result by ID."""
        return self._propagations.get(propagation_id)
    
    async def _persist_propagation(self, propagation: PropagatedUncertainty):
        """Persist propagation result to storage."""
        prop_file = self.storage_path / 'propagations' / f"{propagation.propagation_id}.json"
        prop_file.parent.mkdir(parents=True, exist_ok=True)
        
        with open(prop_file, 'w') as f:
            json.dump(propagation.to_dict(), f, indent=2)
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get quantifier statistics."""
        acceptable = [p for p in self._propagations.values() if p.is_acceptable]
        
        avg_growth = sum(p.uncertainty_growth for p in self._propagations.values()) / len(self._propagations) if self._propagations else 0
        
        return {
            'total_estimates': len(self._estimates),
            'total_propagations': len(self._propagations),
            'acceptable_propagations': len(acceptable),
            'average_uncertainty_growth': avg_growth,
            'config': self._uncertainty_config,
        }
