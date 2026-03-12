"""
Phase 7: Explainability - Feature Attribution
SHAP and Integrated Gradients for decision explanation
"""

import torch
import torch.nn as nn
from typing import Dict, List, Optional, Tuple
import numpy as np
import logging
from captum.attr import (
    IntegratedGradients,
    Saliency,
    DeepLift,
    NoiseTunnel,
    visualization
)

logger = logging.getLogger(__name__)


class FeatureAttributor:
    """
    Explains model decisions through feature attribution.
    Uses multiple attribution methods for robustness.
    """
    
    def __init__(self, model: nn.Module):
        self.model = model
        
        # Attribution methods
        self.integrated_gradients = IntegratedGradients(model)
        self.saliency = Saliency(model)
        self.deeplift = DeepLift(model)
        
        # Feature names for interpretability
        self.feature_names = {
            'price': [
                'open', 'high', 'low', 'close', 'volume',
                'sma_20', 'sma_50', 'rsi', 'macd',
                'volatility'
            ],
            'indicators': [
                'trend_strength', 'momentum', 'volatility',
                'volume_profile', 'support_resistance'
            ],
            'sentiment': [
                'news_sentiment', 'social_sentiment',
                'market_sentiment'
            ]
        }
        
        logger.info("✅ Feature Attributor initialized")
    
    def explain_decision(
        self,
        input_data: torch.Tensor,
        target_class: Optional[int] = None,
        method: str = 'integrated_gradients'
    ) -> Dict:
        """
        Generate feature attributions for model decision.
        
        Args:
            input_data: Input features
            target_class: Optional target class to explain
            method: Attribution method to use
        
        Returns:
            Dictionary with attributions and analysis
        """
        # Select attribution method
        if method == 'integrated_gradients':
            attributions = self._compute_integrated_gradients(
                input_data,
                target_class
            )
        elif method == 'saliency':
            attributions = self._compute_saliency(
                input_data,
                target_class
            )
        elif method == 'deeplift':
            attributions = self._compute_deeplift(
                input_data,
                target_class
            )
        else:
            raise ValueError(f"Unknown attribution method: {method}")
        
        # Analyze attributions
        analysis = self._analyze_attributions(attributions)
        
        return {
            'attributions': attributions,
            'analysis': analysis,
            'method': method
        }
    
    def _compute_integrated_gradients(
        self,
        input_data: torch.Tensor,
        target_class: Optional[int]
    ) -> torch.Tensor:
        """Compute Integrated Gradients attributions."""
        # Add noise tunnel for better attributions
        nt = NoiseTunnel(self.integrated_gradients)
        
        attributions = nt.attribute(
            input_data,
            target=target_class,
            n_samples=10,
            nt_type='smoothgrad',
            stdevs=0.2
        )
        
        return attributions
    
    def _compute_saliency(
        self,
        input_data: torch.Tensor,
        target_class: Optional[int]
    ) -> torch.Tensor:
        """Compute Saliency map attributions."""
        return self.saliency.attribute(
            input_data,
            target=target_class
        )
    
    def _compute_deeplift(
        self,
        input_data: torch.Tensor,
        target_class: Optional[int]
    ) -> torch.Tensor:
        """Compute DeepLift attributions."""
        return self.deeplift.attribute(
            input_data,
            target=target_class
        )
    
    def _analyze_attributions(
        self,
        attributions: torch.Tensor
    ) -> Dict:
        """
        Analyze feature attributions.
        
        Returns:
            Dictionary with attribution analysis
        """
        # Get absolute attributions
        attr_magnitude = torch.abs(attributions)
        
        # Find top features
        top_k = 5
        top_indices = torch.topk(
            attr_magnitude.view(-1),
            k=min(top_k, attr_magnitude.numel())
        ).indices
        
        # Map to feature names
        top_features = []
        for idx in top_indices:
            feature_type = self._get_feature_type(idx)
            feature_name = self._get_feature_name(idx, feature_type)
            importance = float(attr_magnitude.view(-1)[idx])
            
            top_features.append({
                'feature': feature_name,
                'type': feature_type,
                'importance': importance,
                'attribution': float(attributions.view(-1)[idx])
            })
        
        # Calculate importance by feature type
        importance_by_type = {}
        for feature_type in self.feature_names:
            indices = self._get_feature_indices(feature_type)
            importance = float(attr_magnitude[..., indices].sum())
            importance_by_type[feature_type] = importance
        
        return {
            'top_features': top_features,
            'importance_by_type': importance_by_type
        }
    
    def _get_feature_type(self, index: int) -> str:
        """Get feature type from index."""
        cumsum = 0
        for feature_type, features in self.feature_names.items():
            if index < cumsum + len(features):
                return feature_type
            cumsum += len(features)
        return 'unknown'
    
    def _get_feature_name(self, index: int, feature_type: str) -> str:
        """Get feature name from index and type."""
        cumsum = 0
        for ftype, features in self.feature_names.items():
            if ftype == feature_type:
                return features[index - cumsum]
            cumsum += len(features)
        return f'feature_{index}'
    
    def _get_feature_indices(self, feature_type: str) -> List[int]:
        """Get indices for feature type."""
        indices = []
        cumsum = 0
        for ftype, features in self.feature_names.items():
            if ftype == feature_type:
                indices.extend(range(cumsum, cumsum + len(features)))
            cumsum += len(features)
        return indices
    
    def generate_explanation(
        self,
        attributions: Dict,
        confidence: float
    ) -> str:
        """
        Generate human-readable explanation.
        
        Args:
            attributions: Attribution analysis
            confidence: Model confidence
        
        Returns:
            Natural language explanation
        """
        explanation = [
            f"Decision Explanation (Confidence: {confidence:.1%}):\n"
        ]
        
        # Explain top features
        explanation.append("Most influential features:")
        for feature in attributions['analysis']['top_features']:
            impact = "positive" if feature['attribution'] > 0 else "negative"
            explanation.append(
                f"- {feature['feature']}: {impact} impact "
                f"(importance: {feature['importance']:.3f})"
            )
        
        # Explain by feature type
        explanation.append("\nImportance by feature type:")
        importance = attributions['analysis']['importance_by_type']
        for ftype, score in importance.items():
            explanation.append(f"- {ftype}: {score:.3f}")
        
        # Attribution method
        explanation.append(f"\nMethod: {attributions['method']}")
        
        return "\n".join(explanation)
    
    def visualize_attributions(
        self,
        attributions: torch.Tensor,
        feature_names: Optional[List[str]] = None
    ) -> None:
        """
        Visualize feature attributions.
        Uses captum visualization.
        """
        if feature_names is None:
            feature_names = []
            for features in self.feature_names.values():
                feature_names.extend(features)
        
        visualization.visualize_text_attr(
            attributions,
            feature_names,
            title="Feature Attributions"
        )
    
    def compare_methods(
        self,
        input_data: torch.Tensor,
        target_class: Optional[int] = None
    ) -> Dict:
        """
        Compare different attribution methods.
        
        Returns:
            Dictionary with results from each method
        """
        methods = ['integrated_gradients', 'saliency', 'deeplift']
        results = {}
        
        for method in methods:
            results[method] = self.explain_decision(
                input_data,
                target_class,
                method
            )
        
        # Analyze agreement between methods
        agreement = self._analyze_method_agreement(results)
        
        return {
            'attributions': results,
            'agreement': agreement
        }
    
    def _analyze_method_agreement(
        self,
        results: Dict[str, Dict]
    ) -> Dict:
        """Analyze agreement between attribution methods."""
        # Get top features from each method
        top_features = {
            method: set(
                f['feature'] for f in result['analysis']['top_features']
            )
            for method, result in results.items()
        }
        
        # Calculate overlap
        agreement_scores = {}
        methods = list(results.keys())
        
        for i in range(len(methods)):
            for j in range(i + 1, len(methods)):
                method1, method2 = methods[i], methods[j]
                overlap = len(
                    top_features[method1] & top_features[method2]
                )
                union = len(
                    top_features[method1] | top_features[method2]
                )
                
                if union > 0:
                    agreement = overlap / union
                else:
                    agreement = 0.0
                
                agreement_scores[f"{method1}_vs_{method2}"] = agreement
        
        return {
            'pairwise_agreement': agreement_scores,
            'average_agreement': np.mean(list(agreement_scores.values()))
        }
    
    def save_attributions(self, filepath: str, attributions: Dict):
        """Save attribution results."""
        torch.save(attributions, filepath)
        logger.info(f"💾 Attributions saved to {filepath}")
    
    def load_attributions(self, filepath: str) -> Dict:
        """Load attribution results."""
        attributions = torch.load(filepath)
        logger.info(f"📂 Attributions loaded from {filepath}")
        return attributions
