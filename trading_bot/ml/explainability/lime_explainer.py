"""
LIME (Local Interpretable Model-agnostic Explanations) for trading models
"""

import numpy as np
import pandas as pd
from typing import Any, Callable, Dict, List, Optional
import logging

logger = logging.getLogger(__name__)

try:
    from lime.lime_tabular import LimeTabularExplainer
    LIME_AVAILABLE = True
except ImportError:
    logger.warning("LIME not available. Install with: pip install lime")
    LIME_AVAILABLE = False


class LIMEExplainer:
    """
    LIME explainer for trading model predictions
    
    Provides local explanations by perturbing input features
    and observing model behavior.
    """
    
    def __init__(
        self,
        training_data: np.ndarray,
        feature_names: List[str],
        class_names: Optional[List[str]] = None,
        mode: str = 'regression'
    ):
        """
        Initialize LIME explainer
        
        Args:
            training_data: Training data for sampling [n_samples, n_features]
            feature_names: Names of features
            class_names: Names of classes (for classification)
            mode: 'regression' or 'classification'
        """
        if not LIME_AVAILABLE:
            raise ImportError("LIME not installed. Install with: pip install lime")
        
        self.feature_names = feature_names
        self.mode = mode
        
        self.explainer = LimeTabularExplainer(
            training_data,
            feature_names=feature_names,
            class_names=class_names,
            mode=mode,
            discretize_continuous=True
        )
        
        logger.info(f"LIME explainer initialized with {len(feature_names)} features")
    
    def explain_prediction(
        self,
        model: Any,
        instance: np.ndarray,
        num_features: int = 10,
        num_samples: int = 5000
    ) -> Dict[str, Any]:
        """
        Explain a single prediction
        
        Args:
            model: Model with predict or predict_proba method
            instance: Instance to explain [n_features]
            num_features: Number of top features to show
            num_samples: Number of samples for perturbation
            
        Returns:
            Dictionary with explanation details
        """
        # Get prediction function
        if self.mode == 'classification':
            predict_fn = model.predict_proba if hasattr(model, 'predict_proba') else model.predict
        else:
            predict_fn = model.predict
        
        # Generate explanation
        explanation = self.explainer.explain_instance(
            instance,
            predict_fn,
            num_features=num_features,
            num_samples=num_samples
        )
        
        # Extract feature importances
        feature_importance = dict(explanation.as_list())
        
        # Get local prediction
        if self.mode == 'classification':
            local_pred = explanation.predict_proba
        else:
            local_pred = explanation.predicted_value
        
        result = {
            'feature_importance': feature_importance,
            'local_prediction': local_pred,
            'intercept': explanation.intercept[0] if hasattr(explanation, 'intercept') else None,
            'score': explanation.score if hasattr(explanation, 'score') else None,
            'local_exp': explanation.local_exp
        }
        
        logger.debug(f"Generated LIME explanation with {len(feature_importance)} features")
        
        return result
    
    def explain_batch(
        self,
        model: Any,
        instances: np.ndarray,
        num_features: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Explain multiple predictions
        
        Args:
            model: Model to explain
            instances: Instances to explain [n_samples, n_features]
            num_features: Number of top features
            
        Returns:
            List of explanations
        """
        explanations = []
        
        for i, instance in enumerate(instances):
            try:
                exp = self.explain_prediction(model, instance, num_features)
                explanations.append(exp)
            except Exception as e:
                logger.error(f"Failed to explain instance {i}: {e}")
                explanations.append(None)
        
        return explanations
    
    def get_top_features(
        self,
        explanation: Dict[str, Any],
        n: int = 5
    ) -> List[tuple]:
        """
        Get top N most important features
        
        Args:
            explanation: Explanation dictionary
            n: Number of features
            
        Returns:
            List of (feature_name, importance) tuples
        """
        feature_importance = explanation['feature_importance']
        
        # Sort by absolute importance
        sorted_features = sorted(
            feature_importance.items(),
            key=lambda x: abs(x[1]),
            reverse=True
        )
        
        return sorted_features[:n]


class TradingLIMEExplainer(LIMEExplainer):
    """
    LIME explainer specialized for trading signals
    """
    
    def explain_trade_signal(
        self,
        model: Any,
        market_data: pd.DataFrame,
        feature_columns: List[str],
        num_features: int = 10
    ) -> Dict[str, Any]:
        """
        Explain a trading signal
        
        Args:
            model: Trading model
            market_data: Market data DataFrame
            feature_columns: Columns to use as features
            num_features: Number of features to show
            
        Returns:
            Explanation with trading context
        """
        # Extract features
        instance = market_data[feature_columns].iloc[-1].values
        
        # Get explanation
        explanation = self.explain_prediction(model, instance, num_features)
        
        # Add trading context
        top_features = self.get_top_features(explanation, num_features)
        
        # Categorize features
        bullish_features = [(f, v) for f, v in top_features if v > 0]
        bearish_features = [(f, v) for f, v in top_features if v < 0]
        
        explanation['bullish_factors'] = bullish_features
        explanation['bearish_factors'] = bearish_features
        explanation['net_sentiment'] = sum(v for _, v in top_features)
        
        return explanation
    
    def generate_explanation_text(
        self,
        explanation: Dict[str, Any]
    ) -> str:
        """
        Generate human-readable explanation
        
        Args:
            explanation: Explanation dictionary
            
        Returns:
            Text explanation
        """
        lines = ["Trading Signal Explanation:"]
        lines.append(f"Prediction: {explanation['local_prediction']:.4f}")
        lines.append(f"Net Sentiment: {explanation['net_sentiment']:.4f}")
        
        if explanation['bullish_factors']:
            lines.append("\nBullish Factors:")
            for feature, importance in explanation['bullish_factors']:
                lines.append(f"  • {feature}: +{importance:.4f}")
        
        if explanation['bearish_factors']:
            lines.append("\nBearish Factors:")
            for feature, importance in explanation['bearish_factors']:
                lines.append(f"  • {feature}: {importance:.4f}")
        
        return "\n".join(lines)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    # Test LIME explainer
    if LIME_AVAILABLE:
        from sklearn.ensemble import RandomForestRegressor
        
        # Generate sample data
        np.random.seed(42)
        X_train = np.random.randn(1000, 10)
        y_train = X_train[:, 0] * 2 + X_train[:, 1] * -1 + np.random.randn(1000) * 0.1
        
        # Train model
        model = RandomForestRegressor(n_estimators=10, random_state=42)
        model.fit(X_train, y_train)
        
        # Create explainer
        feature_names = [f'feature_{i}' for i in range(10)]
        explainer = LIMEExplainer(X_train, feature_names, mode='regression')
        
        # Explain prediction
        test_instance = np.random.randn(10)
        explanation = explainer.explain_prediction(model, test_instance)
        
        logger.info("\nLIME Explanation:")
        logger.info(f"Prediction: {explanation['local_prediction']:.4f}")
        logger.info("\nTop Features:")
        for feature, importance in explainer.get_top_features(explanation, 5):
            logger.info(f"  {feature}: {importance:.4f}")
        
        logger.info("\n✅ LIME explainer test passed!")
    else:
        logger.info("❌ LIME not available. Install with: pip install lime")
