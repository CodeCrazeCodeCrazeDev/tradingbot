"""
SHAP Explainability for Trading Models

Provides feature attribution for every trade decision.
Answers: "Why did the model make this prediction?"
"""

import numpy as np
from typing import Dict, List, Optional, Tuple
import logging

logger = logging.getLogger(__name__)


class TradingExplainer:
    """
    SHAP-based explainer for trading models
    
    Provides:
    - Feature importance for each prediction
    - Top-N most influential features
    - Positive/negative contribution breakdown
    - Visualization-ready data
    """
    
    def __init__(self, model, feature_names: List[str]):
        """
        Args:
            model: Trained model (sklearn, torch, etc.)
            feature_names: List of feature names
        """
        self.model = model
        self.feature_names = feature_names
        self.explainer = None
        self.background_data = None
    
    def fit_explainer(self, background_data: np.ndarray, method: str = 'kernel'):
        """
        Initialize SHAP explainer with background data
        
        Args:
            background_data: Representative sample for baseline [n_samples, n_features]
            method: 'kernel', 'tree', 'deep', or 'linear'
        """
        self.background_data = background_data
        
        try:
            import shap
            
            if method == 'tree':
                # For tree-based models (XGBoost, RandomForest, etc.)
                self.explainer = shap.TreeExplainer(self.model)
            elif method == 'deep':
                # For neural networks
                self.explainer = shap.DeepExplainer(self.model, background_data)
            elif method == 'linear':
                # For linear models
                self.explainer = shap.LinearExplainer(self.model, background_data)
            else:
                # Kernel SHAP (model-agnostic but slower)
                self.explainer = shap.KernelExplainer(self.model.predict, background_data)
            
            logger.info(f"SHAP explainer initialized with method: {method}")
            
        except ImportError:
            logger.warning("SHAP not installed. Using fallback explainer.")
            self.explainer = None
    
    def explain_prediction(
        self,
        features: np.ndarray,
        top_n: int = 5
    ) -> Dict:
        """
        Explain a single prediction
        
        Args:
            features: Feature vector [n_features]
            top_n: Number of top features to return
            
        Returns:
            Dictionary with explanation
        """
        if self.explainer is None:
            return self._fallback_explanation(features, top_n)
        try:
        
            
            # Compute SHAP values
            if len(features.shape) == 1:
                features = features.reshape(1, -1)
            
            shap_values = self.explainer.shap_values(features)
            
            # Handle multi-class output
            if isinstance(shap_values, list):
                shap_values = shap_values[0]  # Use first class
            
            if len(shap_values.shape) > 1:
                shap_values = shap_values[0]  # Get first sample
            
            # Get top features by absolute importance
            abs_importance = np.abs(shap_values)
            top_indices = np.argsort(abs_importance)[-top_n:][:-1]
            
            # Build explanation
            explanation = {
                'top_features': [],
                'all_shap_values': dict(zip(self.feature_names, shap_values.tolist())),
                'base_value': self.explainer.expected_value if hasattr(self.explainer, 'expected_value') else 0.0,
                'prediction_value': float(shap_values.sum() + (self.explainer.expected_value if hasattr(self.explainer, 'expected_value') else 0.0))
            }
            
            for idx in top_indices:
                explanation['top_features'].append({
                    'feature': self.feature_names[idx],
                    'value': float(features[0, idx]),
                    'shap_value': float(shap_values[idx]),
                    'contribution': 'positive' if shap_values[idx] > 0 else 'negative'
                })
            
            logger.info(f"Explained prediction: top feature = {explanation['top_features'][0]['feature']}")
            
            return explanation
            
        except Exception as e:
            logger.error(f"SHAP explanation failed: {e}")
            return self._fallback_explanation(features, top_n)
    
    def _fallback_explanation(self, features: np.ndarray, top_n: int) -> Dict:
        """Fallback explanation using simple feature importance"""
        if len(features.shape) == 1:
            features = features.reshape(1, -1)
        
        # Use absolute feature values as proxy for importance
        importance = np.abs(features[0])
        top_indices = np.argsort(importance)[-top_n:][:-1]
        
        explanation = {
            'top_features': [],
            'all_shap_values': {},
            'base_value': 0.0,
            'prediction_value': 0.0,
            'note': 'Fallback explanation (SHAP not available)'
        }
        
        for idx in top_indices:
            explanation['top_features'].append({
                'feature': self.feature_names[idx],
                'value': float(features[0, idx]),
                'shap_value': float(importance[idx]),
                'contribution': 'positive' if features[0, idx] > 0 else 'negative'
            })
        
        return explanation
    
    def explain_trade(
        self,
        trade_features: Dict[str, float],
        prediction: float,
        top_n: int = 3
    ) -> str:
        """
        Generate human-readable trade explanation
        
        Args:
            trade_features: Dictionary of feature values
            prediction: Model prediction
            top_n: Number of top reasons to include
            
        Returns:
            Human-readable explanation string
        """
        # Convert dict to array
        feature_array = np.array([trade_features.get(name, 0) for name in self.feature_names])
        
        # Get explanation
        explanation = self.explain_prediction(feature_array, top_n)
        
        # Build readable text
        direction = "LONG" if prediction > 0 else "SHORT"
        confidence = abs(prediction)
        
        text = f"Trade Decision: {direction} (confidence: {confidence:.2%})\n\n"
        text += "Top Reasons:\n"
        
        for i, feat in enumerate(explanation['top_features'], 1):
            impact = "supports" if feat['contribution'] == 'positive' else "opposes"
            text += f"{i}. {feat['feature']} = {feat['value']:.4f} ({impact} decision, impact: {abs(feat['shap_value']):.4f})\n"
        
        return text
    
    def batch_explain(
        self,
        features_batch: np.ndarray,
        top_n: int = 5
    ) -> List[Dict]:
        """Explain multiple predictions"""
        explanations = []
        
        for i in range(features_batch.shape[0]):
            explanation = self.explain_prediction(features_batch[i], top_n)
            explanations.append(explanation)
        
        return explanations
    
    def get_global_importance(
        self,
        features_batch: np.ndarray
    ) -> Dict[str, float]:
        """
        Compute global feature importance across multiple samples
        
        Args:
            features_batch: Multiple feature vectors [n_samples, n_features]
            
        Returns:
            Dictionary mapping feature names to importance scores
        """
        if self.explainer is None:
            logger.warning("Explainer not initialized")
            return {}
        try:
        
            
            # Compute SHAP values for batch
            shap_values = self.explainer.shap_values(features_batch)
            
            if isinstance(shap_values, list):
                shap_values = shap_values[0]
            
            # Average absolute SHAP values
            mean_abs_shap = np.mean(np.abs(shap_values), axis=0)
            
            # Create importance dict
            importance = dict(zip(self.feature_names, mean_abs_shap.tolist()))
            
            # Sort by importance
            importance = dict(sorted(importance.items(), key=lambda x: x[1], reverse=True))
            
            logger.info(f"Global importance computed for {len(features_batch)} samples")
            
            return importance
            
        except Exception as e:
            logger.error(f"Global importance computation failed: {e}")
            return {}


class TradeAutopsy:
    """
    Post-trade analysis with explanations
    
    Analyzes why a trade succeeded or failed
    """
    
    def __init__(self, explainer: TradingExplainer):
        self.explainer = explainer
    
    def analyze_trade(
        self,
        trade_features: Dict[str, float],
        prediction: float,
        actual_outcome: float,
        pnl: float
    ) -> Dict:
        """
        Comprehensive trade analysis
        
        Args:
            trade_features: Features at trade entry
            prediction: Model prediction
            actual_outcome: Actual market move
            pnl: Trade profit/loss
            
        Returns:
            Analysis dictionary
        """
        # Get explanation
        feature_array = np.array([
            trade_features.get(name, 0) 
            for name in self.explainer.feature_names
        ])
        explanation = self.explainer.explain_prediction(feature_array, top_n=5)
        
        # Determine success
        prediction_correct = (prediction > 0 and actual_outcome > 0) or (prediction < 0 and actual_outcome < 0)
        
        analysis = {
            'trade_id': trade_features.get('trade_id', 'unknown'),
            'timestamp': trade_features.get('timestamp', 'unknown'),
            'prediction': prediction,
            'actual_outcome': actual_outcome,
            'pnl': pnl,
            'success': prediction_correct,
            'prediction_error': abs(prediction - actual_outcome),
            'top_features': explanation['top_features'],
            'verdict': self._generate_verdict(prediction_correct, pnl, explanation)
        }
        
        logger.info(f"Trade autopsy: {'SUCCESS' if prediction_correct else 'FAILURE'}, PnL: ${pnl:.2f}")
        
        return analysis
    
    def _generate_verdict(
        self,
        prediction_correct: bool,
        pnl: float,
        explanation: Dict
    ) -> str:
        """Generate verdict text"""
        if prediction_correct and pnl > 0:
            verdict = "✅ SUCCESSFUL TRADE\n"
            verdict += "Model correctly predicted direction and trade was profitable.\n"
            verdict += f"Key factor: {explanation['top_features'][0]['feature']}"
        
        elif prediction_correct and pnl <= 0:
            verdict = "⚠️ CORRECT DIRECTION BUT UNPROFITABLE\n"
            verdict += "Model predicted direction correctly but trade hit stop loss.\n"
            verdict += "Consider: Wider stops or better entry timing."
        
        elif not prediction_correct and pnl > 0:
            verdict = "🤔 WRONG DIRECTION BUT PROFITABLE\n"
            verdict += "Model predicted wrong direction but trade was profitable.\n"
            verdict += "Possible: Market reversed after entry."
        
        else:
            verdict = "❌ FAILED TRADE\n"
            verdict += "Model predicted wrong direction and trade was unprofitable.\n"
            verdict += f"Review: {explanation['top_features'][0]['feature']} may be unreliable."
        
        return verdict


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    # Mock model for demo
    class MockModel:
        def predict(self, X):
            return np.random.randn(X.shape[0])
    
    # Create explainer
    feature_names = ['rsi', 'macd', 'volume', 'atr', 'trend_strength']
    model = MockModel()
    explainer = TradingExplainer(model, feature_names)
    
    # Create background data
    background = np.random.randn(100, 5)
    explainer.fit_explainer(background, method='kernel')
    
    # Explain a prediction
    print("\n" + "="*60)
    logger.info("SHAP EXPLAINABILITY DEMO")
    print("="*60)
    
    test_features = np.array([65, 0.002, 1500, 0.0012, 0.75])
    explanation = explainer.explain_prediction(test_features, top_n=3)
    
    logger.info("\nTop Features:")
    for feat in explanation['top_features']:
        logger.info(f"  {feat['feature']}: {feat['value']:.4f} (SHAP: {feat['shap_value']:+.4f})")
    
    # Trade explanation
    trade_features = dict(zip(feature_names, test_features))
    trade_text = explainer.explain_trade(trade_features, 0.65, top_n=3)
    print("\n" + trade_text)
    
    # Trade autopsy
    autopsy = TradeAutopsy(explainer)
    analysis = autopsy.analyze_trade(
        trade_features,
        prediction=0.01,
        actual_outcome=0.015,
        pnl=50.0
    )
    
    print("\n" + "="*60)
    logger.info("TRADE AUTOPSY")
    print("="*60)
    print(analysis['verdict'])
    print("="*60)
