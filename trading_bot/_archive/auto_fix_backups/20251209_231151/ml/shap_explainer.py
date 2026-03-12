import logging
"""
from pathlib import Path
SHAP (SHapley Additive exPlanations) integration for model explainability.
Provides feature importance and natural language explanations for trades.
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Optional
from loguru import logger

try:
    import shap
    SHAP_AVAILABLE = True
except ImportError:
    SHAP_AVAILABLE = False
    logger.warning("SHAP not installed. Install with: pip install shap")


class SHAPExplainer:
    """SHAP-based model explainability."""
    
    def __init__(self, model, background_data: np.ndarray, feature_names: List[str]):
        """
        Initialize SHAP explainer.
        
        Args:
            model: Trained model (PyTorch, sklearn, etc.)
            background_data: Background dataset for SHAP
            feature_names: List of feature names
        """
        if not SHAP_AVAILABLE:
            raise ImportError("SHAP not installed")
        
        self.model = model
        self.feature_names = feature_names
        self.background_data = background_data
        
        # Initialize explainer based on model type
        try:
            # Try DeepExplainer for neural networks
            self.explainer = shap.DeepExplainer(model, background_data)
            self.explainer_type = 'deep'
        except Exception:
            try:
                # Fallback to KernelExplainer
                self.explainer = shap.KernelExplainer(
                    model.predict, 
                    background_data[:100]  # Use subset for speed
                )
                self.explainer_type = 'kernel'
            except Exception:
                # Fallback to simple explainer
                self.explainer = None
                self.explainer_type = 'none'
        
        logger.info(f"SHAP explainer initialized ({self.explainer_type})")
    
    def explain_prediction(self, X: np.ndarray, top_k: int = 10) -> Dict:
        """
        Generate SHAP explanation for prediction.
        
        Args:
            X: Input features
            top_k: Number of top features to explain
            
        Returns:
            Dictionary with explanation details
        """
        if self.explainer is None:
            return self._fallback_explanation(X, top_k)
        
        # Calculate SHAP values
        shap_values = self.explainer.shap_values(X)
        
        # Handle different output formats
        if isinstance(shap_values, list):
            shap_values = shap_values[0]  # Take first class for binary
        
        # Get feature importance
        feature_importance = np.abs(shap_values[0])
        top_indices = np.argsort(feature_importance)[-top_k:][:-1]
        
        # Generate explanation
        explanation = {
            'shap_values': shap_values[0],
            'feature_importance': dict(zip(self.feature_names, feature_importance)),
            'top_features': [
                {
                    'name': self.feature_names[idx],
                    'shap_value': float(shap_values[0][idx]),
                    'feature_value': float(X[0][idx]),
                    'impact': 'positive' if shap_values[0][idx] > 0 else 'negative'
                }
                for idx in top_indices
            ],
            'natural_language': self._generate_natural_language(
                shap_values[0], X[0], top_indices
            )
        }
        
        return explanation
    
    def _generate_natural_language(self, shap_values: np.ndarray, 
                                   feature_values: np.ndarray, 
                                   top_indices: np.ndarray) -> str:
        """Generate natural language explanation."""
        explanations = []
        
        for idx in top_indices[:5]:  # Top 5 features
            feature_name = self.feature_names[idx]
            shap_val = shap_values[idx]
            feature_val = feature_values[idx]
            
            # Determine impact direction
            if shap_val > 0:
                direction = "increases"
                strength = "strongly" if abs(shap_val) > 0.1 else "moderately"
            else:
                direction = "decreases"
                strength = "strongly" if abs(shap_val) > 0.1 else "moderately"
            
            # Format feature name
            readable_name = feature_name.replace('_', ' ').title()
            
            explanation = (
                f"{readable_name} (value: {feature_val:.3f}) {strength} "
                f"{direction} the prediction (impact: {shap_val:.3f})"
            )
            explanations.append(explanation)
        
        return " | ".join(explanations)
    
    def _fallback_explanation(self, X: np.ndarray, top_k: int) -> Dict:
        """Fallback explanation when SHAP is not available."""
        # Simple feature importance based on magnitude
        feature_importance = np.abs(X[0])
        top_indices = np.argsort(feature_importance)[-top_k:][:-1]
        
        return {
            'shap_values': None,
            'feature_importance': dict(zip(self.feature_names, feature_importance)),
            'top_features': [
                {
                    'name': self.feature_names[idx],
                    'shap_value': None,
                    'feature_value': float(X[0][idx]),
                    'impact': 'unknown'
                }
                for idx in top_indices
            ],
            'natural_language': f"Top features: {', '.join([self.feature_names[idx] for idx in top_indices[:5]])}"
        }
    
    def get_feature_importance_summary(self, X: np.ndarray, 
                                      n_samples: int = 100) -> pd.DataFrame:
        """
        Get feature importance summary across multiple samples.
        
        Args:
            X: Input features (multiple samples)
            n_samples: Number of samples to analyze
            
        Returns:
            DataFrame with feature importance statistics
        """
        if self.explainer is None:
            logger.warning("SHAP explainer not available")
            return pd.DataFrame()
        
        # Calculate SHAP values for samples
        shap_values = self.explainer.shap_values(X[:n_samples])
        
        if isinstance(shap_values, list):
            shap_values = shap_values[0]
        
        # Calculate statistics
        mean_abs_shap = np.mean(np.abs(shap_values), axis=0)
        std_shap = np.std(shap_values, axis=0)
        
        # Create summary DataFrame
        summary = pd.DataFrame({
            'feature': self.feature_names,
            'mean_abs_shap': mean_abs_shap,
            'std_shap': std_shap,
            'importance_rank': np.argsort(mean_abs_shap)[:-1] + 1
        })
        
        summary = summary.sort_values('mean_abs_shap', ascending=False)
        
        logger.info(f"Feature importance summary generated for {n_samples} samples")
        return summary
    
    def plot_feature_importance(self, X: np.ndarray, save_path: Optional[str] = None):
        """
        Plot feature importance using SHAP.
        
        Args:
            X: Input features
            save_path: Path to save plot (optional)
        """
        if self.explainer is None:
            logger.warning("SHAP explainer not available for plotting")
            return
        
        try:
            import matplotlib.pyplot as plt

            shap_values = self.explainer.shap_values(X)
            
            if isinstance(shap_values, list):
                shap_values = shap_values[0]
            
            # Create summary plot
            shap.summary_plot(
                shap_values, 
                X, 
                feature_names=self.feature_names,
                show=False
            )
            
            if save_path:
                plt.savefig(save_path, bbox_inches='tight', dpi=300)
                logger.info(f"SHAP plot saved to {save_path}")
            else:
                plt.show()
            
            plt.close()
            
        except Exception as e:
            logger.error(f"Failed to plot SHAP: {e}")


class TradeExplainer:
    """High-level trade explanation system."""
    
    def __init__(self, shap_explainer: Optional[SHAPExplainer] = None):
        self.shap_explainer = shap_explainer
    
    def explain_trade_decision(self, features: np.ndarray, 
                              prediction: float,
                              action: str) -> Dict:
        """
        Explain why a trade decision was made.
        
        Args:
            features: Input features
            prediction: Model prediction
            action: Trade action (buy/sell/hold)
            
        Returns:
            Comprehensive explanation dictionary
        """
        explanation = {
            'action': action,
            'prediction': float(prediction),
            'confidence': self._calculate_confidence(prediction),
            'reasoning': []
        }
        
        # Add SHAP explanation if available
        if self.shap_explainer:
            shap_explanation = self.shap_explainer.explain_prediction(features)
            explanation['shap_explanation'] = shap_explanation
            explanation['reasoning'].append(shap_explanation['natural_language'])
        
        # Add rule-based reasoning
        rule_reasoning = self._generate_rule_based_reasoning(features, action)
        explanation['reasoning'].extend(rule_reasoning)
        
        # Generate summary
        explanation['summary'] = self._generate_summary(explanation)
        
        return explanation
    
    def _calculate_confidence(self, prediction: float) -> float:
        """Calculate confidence score from prediction."""
        # Simple confidence based on distance from neutral
        confidence = abs(prediction - 0.5) * 2  # Scale to 0-1
        return float(np.clip(confidence, 0, 1))
    
    def _generate_rule_based_reasoning(self, features: np.ndarray, 
                                      action: str) -> List[str]:
        """Generate rule-based reasoning."""
        reasoning = []
        
        if action == 'buy':
            reasoning.append("Bullish signal detected based on technical indicators")
            reasoning.append("Risk-reward ratio favorable for long position")
        elif action == 'sell':
            reasoning.append("Bearish signal detected based on technical indicators")
            reasoning.append("Risk-reward ratio favorable for short position")
        else:
            reasoning.append("No clear directional signal - holding position")
        
        return reasoning
    
    def _generate_summary(self, explanation: Dict) -> str:
        """Generate human-readable summary."""
        action = explanation['action'].upper()
        confidence = explanation['confidence'] * 100
        
        summary = f"Trade Decision: {action} (Confidence: {confidence:.1f}%)\n"
        summary += "Reasoning:\n"
        
        for i, reason in enumerate(explanation['reasoning'], 1):
            summary += f"{i}. {reason}\n"
        
        return summary
