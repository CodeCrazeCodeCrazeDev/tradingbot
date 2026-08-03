"""
SHAP (SHapley Additive exPlanations) Explainer for Trading Decisions

Paper: "A Unified Approach to Interpreting Model Predictions"
Lundberg & Lee (NeurIPS 2017)

Provides feature attribution for:
- Individual trade decisions
- Model predictions
- Policy actions
- Risk assessments
"""

import numpy as np
import pandas as pd
from typing import Any, Callable, Dict, List, Optional, Tuple
from dataclasses import dataclass
import logging
try:
    import torch
except ImportError:
    torch = None
import torch.nn as nn
import numpy
import pandas

logger = logging.getLogger(__name__)


@dataclass
class SHAPExplanation:
    """SHAP explanation for a prediction."""
    base_value: float
    shap_values: np.ndarray
    feature_names: List[str]
    feature_values: np.ndarray
    prediction: float
    
    def get_top_features(self, n: int = 10) -> List[Tuple[str, float, float]]:
        """Get top N most important features."""
        abs_values = np.abs(self.shap_values)
        top_indices = np.argsort(abs_values)[-n:][:-1]
        
        return [
            (self.feature_names[i], self.shap_values[i], self.feature_values[i])
            for i in top_indices
        ]
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'base_value': self.base_value,
            'prediction': self.prediction,
            'shap_values': dict(zip(self.feature_names, self.shap_values.tolist())),
            'feature_values': dict(zip(self.feature_names, self.feature_values.tolist())),
            'top_features': self.get_top_features()
        }


class KernelSHAP:
    """
    Kernel SHAP implementation for model-agnostic explanations.
    
    Uses weighted linear regression to estimate Shapley values.
    """
    
    def __init__(
        self,
        model: Callable,
        background_data: np.ndarray,
        feature_names: Optional[List[str]] = None,
        num_samples: int = 1000
    ):
        """
        Initialize Kernel SHAP.
        
        Args:
            model: Model to explain (callable that takes features and returns predictions)
            background_data: Background dataset for sampling
            feature_names: Names of features
            num_samples: Number of samples for estimation
        """
        self.model = model
        self.background_data = background_data
        self.num_samples = num_samples
        
        if feature_names is None:
            self.feature_names = [f"feature_{i}" for i in range(background_data.shape[1])]
        else:
            self.feature_names = feature_names
        
        self.num_features = len(self.feature_names)
        
        # Precompute background mean
        self.background_mean = background_data.mean(axis=0)
        
        logger.info(f"Kernel SHAP initialized: {self.num_features} features, {num_samples} samples")
    
    def explain(self, instance: np.ndarray) -> SHAPExplanation:
        """
        Explain a single prediction.
        
        Args:
            instance: Feature vector to explain
        
        Returns:
            SHAP explanation
        """
        # Get base prediction (all features at background mean)
        base_prediction = self.model(self.background_mean.reshape(1, -1))[0]
        
        # Get instance prediction
        instance_prediction = self.model(instance.reshape(1, -1))[0]
        
        # Generate coalition samples
        coalitions, weights = self._generate_coalitions()
        
        # Evaluate model on coalitions
        coalition_predictions = self._evaluate_coalitions(instance, coalitions)
        
        # Solve weighted linear regression
        shap_values = self._solve_regression(coalitions, coalition_predictions, weights)
        
        return SHAPExplanation(
            base_value=base_prediction,
            shap_values=shap_values,
            feature_names=self.feature_names,
            feature_values=instance,
            prediction=instance_prediction
        )
    
    def _generate_coalitions(self) -> Tuple[np.ndarray, np.ndarray]:
        """Generate random feature coalitions."""
        coalitions = np.random.binomial(1, 0.5, (self.num_samples, self.num_features))
        
        # Compute Shapley kernel weights
        num_present = coalitions.sum(axis=1)
        weights = np.zeros(self.num_samples)
        
        for i in range(self.num_samples):
            m = num_present[i]
            if m == 0 or m == self.num_features:
                weights[i] = 1000  # High weight for empty and full coalitions
            else:
                weights[i] = (self.num_features - 1) / (
                    self._binomial_coefficient(self.num_features, m) * m * (self.num_features - m)
                )
        
        return coalitions, weights
    
    def _evaluate_coalitions(
        self,
        instance: np.ndarray,
        coalitions: np.ndarray
    ) -> np.ndarray:
        """Evaluate model on feature coalitions."""
        predictions = np.zeros(len(coalitions))
        
        for i, coalition in enumerate(coalitions):
            # Create instance with coalition features
            x = np.where(
                coalition.reshape(1, -1),
                instance.reshape(1, -1),
                self.background_mean.reshape(1, -1)
            )
            predictions[i] = self.model(x)[0]
        
        return predictions
    
    def _solve_regression(
        self,
        coalitions: np.ndarray,
        predictions: np.ndarray,
        weights: np.ndarray
    ) -> np.ndarray:
        """Solve weighted linear regression for SHAP values."""
        # Weighted least squares
        W = np.diag(weights)
        X = coalitions
        y = predictions
        
        # Solve: (X^T W X)^-1 X^T W y
        try:
            shap_values = np.linalg.solve(X.T @ W @ X, X.T @ W @ y)
        except np.linalg.LinAlgError:
            # Fallback to pseudo-inverse
            shap_values = np.linalg.pinv(X.T @ W @ X) @ X.T @ W @ y
        
        return shap_values
    
    def _binomial_coefficient(self, n: int, k: int) -> int:
        """Compute binomial coefficient."""
        if k > n or k < 0:
            return 0
        if k == 0 or k == n:
            return 1
        
        # Use symmetry
        k = min(k, n - k)
        
        result = 1
        for i in range(k):
            result = result * (n - i) // (i + 1)
        
        return result


class DeepSHAP:
    """
    Deep SHAP for neural networks.
    
    Faster than Kernel SHAP by using backpropagation.
    """
    
    def __init__(
        self,
        model: nn.Module,
        background_data: torch.Tensor,
        feature_names: Optional[List[str]] = None
    ):
        """
        Initialize Deep SHAP.
        
        Args:
            model: PyTorch model to explain
            background_data: Background dataset (tensor)
            feature_names: Names of features
        """
        self.model = model
        self.background_data = background_data
        
        if feature_names is None:
            self.feature_names = [f"feature_{i}" for i in range(background_data.shape[1])]
        else:
            self.feature_names = feature_names
        
        self.num_features = len(self.feature_names)
        
        logger.info(f"Deep SHAP initialized: {self.num_features} features")
    
    def explain(self, instance: torch.Tensor) -> SHAPExplanation:
        """
        Explain a single prediction using gradient-based method.
        
        Args:
            instance: Feature tensor to explain
        
        Returns:
            SHAP explanation
        """
        self.model.eval()
        
        # Get base prediction
        with torch.no_grad():
            base_prediction = self.model(self.background_data.mean(dim=0, keepdim=True)).item()
            instance_prediction = self.model(instance.unsqueeze(0)).item()
        
        # Compute gradients
        instance_requires_grad = instance.clone().detach().requires_grad_(True)
        output = self.model(instance_requires_grad.unsqueeze(0))
        
        # Backpropagate
        output.backward()
        
        # SHAP values = gradient * (instance - background_mean)
        gradients = instance_requires_grad.grad.detach()
        background_mean = self.background_data.mean(dim=0)
        shap_values = gradients * (instance - background_mean)
        
        return SHAPExplanation(
            base_value=base_prediction,
            shap_values=shap_values.cpu().numpy(),
            feature_names=self.feature_names,
            feature_values=instance.cpu().numpy(),
            prediction=instance_prediction
        )


class TradingSHAPExplainer:
    """
    SHAP explainer specialized for trading decisions.
    
    Provides explanations for:
    - Trade entry/exit decisions
    - Position sizing
    - Risk assessments
    """
    
    def __init__(
        self,
        model: Callable,
        background_data: np.ndarray,
        feature_names: List[str],
        use_deep_shap: bool = False
    ):
        """
        Initialize trading SHAP explainer.
        
        Args:
            model: Trading model to explain
            background_data: Historical market data
            feature_names: Names of features
            use_deep_shap: Use Deep SHAP if model is PyTorch
        """
        self.feature_names = feature_names
        
        if use_deep_shap and isinstance(model, nn.Module):
            self.explainer = DeepSHAP(
                model,
                torch.FloatTensor(background_data),
                feature_names
            )
            self.use_deep = True
        else:
            self.explainer = KernelSHAP(
                model,
                background_data,
                feature_names
            )
            self.use_deep = False
        
        # Track explanations
        self.explanation_history = []
        
        logger.info(f"Trading SHAP explainer initialized: {'Deep' if use_deep_shap else 'Kernel'} SHAP")
    
    def explain_trade(
        self,
        market_state: np.ndarray,
        trade_action: str,
        trade_size: float
    ) -> Dict[str, Any]:
        """
        Explain a trading decision.
        
        Args:
            market_state: Current market features
            trade_action: Action taken ('buy', 'sell', 'hold')
            trade_size: Size of trade
        
        Returns:
            Explanation dictionary
        """
        # Get SHAP explanation
        if self.use_deep:
            explanation = self.explainer.explain(torch.FloatTensor(market_state))
        else:
            explanation = self.explainer.explain(market_state)
        
        # Get top features
        top_features = explanation.get_top_features(n=10)
        
        # Categorize features
        bullish_features = [(name, val, fval) for name, val, fval in top_features if val > 0]
        bearish_features = [(name, val, fval) for name, val, fval in top_features if val < 0]
        
        # Generate explanation text
        explanation_text = self._generate_explanation_text(
            trade_action,
            trade_size,
            bullish_features,
            bearish_features
        )
        
        result = {
            'action': trade_action,
            'size': trade_size,
            'prediction': explanation.prediction,
            'base_value': explanation.base_value,
            'top_features': top_features,
            'bullish_features': bullish_features,
            'bearish_features': bearish_features,
            'explanation_text': explanation_text,
            'full_explanation': explanation.to_dict()
        }
        
        # Store in history
        self.explanation_history.append(result)
        
        return result
    
    def _generate_explanation_text(
        self,
        action: str,
        size: float,
        bullish: List[Tuple[str, float, float]],
        bearish: List[Tuple[str, float, float]]
    ) -> str:
        """Generate human-readable explanation."""
        lines = [f"Trade Decision: {action.upper()} (size: {size:.2f})"]
        lines.append("")
        
        if bullish:
            lines.append("Bullish Factors:")
            for name, shap_val, feature_val in bullish[:5]:
                lines.append(f"  • {name}: {feature_val:.4f} (impact: +{shap_val:.4f})")
        
        if bearish:
            lines.append("")
            lines.append("Bearish Factors:")
            for name, shap_val, feature_val in bearish[:5]:
                lines.append(f"  • {name}: {feature_val:.4f} (impact: {shap_val:.4f})")
        
        return "\n".join(lines)
    
    def explain_why_failed(
        self,
        failed_trades: List[Dict],
        successful_trades: List[Dict]
    ) -> Dict[str, Any]:
        """
        Analyze why trades failed vs succeeded.
        
        Args:
            failed_trades: List of failed trade data
            successful_trades: List of successful trade data
        
        Returns:
            Analysis of failure factors
        """
        # Extract features
        failed_features = np.array([t['features'] for t in failed_trades])
        success_features = np.array([t['features'] for t in successful_trades])
        
        # Get SHAP values for both groups
        failed_shap = []
        success_shap = []
        
        for features in failed_features:
            if self.use_deep:
                exp = self.explainer.explain(torch.FloatTensor(features))
            else:
                exp = self.explainer.explain(features)
            failed_shap.append(exp.shap_values)
        
        for features in success_features:
            if self.use_deep:
                exp = self.explainer.explain(torch.FloatTensor(features))
            else:
                exp = self.explainer.explain(features)
            success_shap.append(exp.shap_values)
        
        failed_shap = np.array(failed_shap)
        success_shap = np.array(success_shap)
        
        # Compute mean SHAP values
        failed_mean = failed_shap.mean(axis=0)
        success_mean = success_shap.mean(axis=0)
        
        # Find differentiating features
        diff = failed_mean - success_mean
        diff_indices = np.argsort(np.abs(diff))[:-1]
        
        differentiating_features = [
            {
                'feature': self.feature_names[i],
                'failed_impact': failed_mean[i],
                'success_impact': success_mean[i],
                'difference': diff[i]
            }
            for i in diff_indices[:10]
        ]
        
        return {
            'num_failed': len(failed_trades),
            'num_successful': len(successful_trades),
            'differentiating_features': differentiating_features,
            'failed_mean_shap': dict(zip(self.feature_names, failed_mean)),
            'success_mean_shap': dict(zip(self.feature_names, success_mean))
        }
    
    def get_feature_importance_summary(self) -> pd.DataFrame:
        """Get summary of feature importance across all explanations."""
        if not self.explanation_history:
            return pd.DataFrame()
        
        # Aggregate SHAP values
        all_shap = []
        for exp in self.explanation_history:
            shap_dict = exp['full_explanation']['shap_values']
            all_shap.append([shap_dict[name] for name in self.feature_names])
        
        all_shap = np.array(all_shap)
        
        # Compute statistics
        summary = pd.DataFrame({
            'feature': self.feature_names,
            'mean_abs_shap': np.abs(all_shap).mean(axis=0),
            'mean_shap': all_shap.mean(axis=0),
            'std_shap': all_shap.std(axis=0),
            'min_shap': all_shap.min(axis=0),
            'max_shap': all_shap.max(axis=0)
        })
        
        return summary.sort_values('mean_abs_shap', ascending=False)


if __name__ == "__main__":
    # Demo
    logging.basicConfig(level=logging.INFO)
    
    print("\n" + "="*80)
    logger.info("SHAP EXPLAINER DEMO")
    print("="*80)
    
    # Create dummy model
    def dummy_model(x):
        # Simple linear model
        weights = np.array([0.5, -0.3, 0.8, 0.2, -0.1])
        return (x @ weights[:x.shape[1]]).flatten()
    
    # Create background data
    background = np.random.randn(100, 5)
    feature_names = ['price_momentum', 'rsi', 'volume', 'volatility', 'trend']
    
    # Create explainer
    explainer = TradingSHAPExplainer(
        model=dummy_model,
        background_data=background,
        feature_names=feature_names
    )
    
    # Explain a trade
    logger.info("\n[1] Explaining a BUY trade...")
    market_state = np.array([0.5, 45, 1.2, 0.02, 0.3])
    
    explanation = explainer.explain_trade(
        market_state=market_state,
        trade_action='buy',
        trade_size=1.0
    )
    
    print(explanation['explanation_text'])
    
    # Explain multiple trades
    logger.info("\n[2] Explaining multiple trades...")
    for i in range(5):
        state = np.random.randn(5)
        action = np.random.choice(['buy', 'sell', 'hold'])
        explainer.explain_trade(state, action, 1.0)
    
    # Get feature importance summary
    logger.info("\n[3] Feature importance summary...")
    summary = explainer.get_feature_importance_summary()
    print(summary)
    
    print("\n" + "="*80)
    logger.info("DEMO COMPLETE")
    print("="*80)
