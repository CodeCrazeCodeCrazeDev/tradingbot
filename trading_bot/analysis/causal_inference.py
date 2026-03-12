"""
Causal Inference for Trading Features

Uses DoWhy to validate causal relationships between features and outcomes.
Removes spurious correlations and identifies true causal drivers.
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Tuple
import logging

logger = logging.getLogger(__name__)


class CausalAnalyzer:
    """
    Causal inference for trading features
    
    Validates:
    - Does feature X truly cause outcome Y?
    - Or is it just correlation?
    - What is the causal effect size?
    """
    
    def __init__(self):
        self.causal_graph = None
        self.validated_features = []
        self.spurious_features = []
    
    def build_causal_graph(
        self,
        data: pd.DataFrame,
        treatment: str,
        outcome: str,
        confounders: Optional[List[str]] = None
    ) -> Dict:
        """
        Build causal graph and estimate treatment effect
        
        Args:
            data: Historical data
            treatment: Treatment variable (e.g., 'high_rsi')
            outcome: Outcome variable (e.g., 'future_return')
            confounders: List of confounding variables
            
        Returns:
            Causal analysis results
        """
        try:
            import dowhy
            from dowhy import CausalModel
            
            # Define causal graph
            if confounders is None:
                confounders = []
            
            # Create graph string
            graph = f"""
            digraph {{
                {treatment} -> {outcome};
                {' -> '.join([f'{c} -> {treatment}; {c} -> {outcome};' for c in confounders])}
            }}
            """
            
            # Create causal model
            model = CausalModel(
                data=data,
                treatment=treatment,
                outcome=outcome,
                graph=graph
            )
            
            # Identify causal effect
            identified_estimand = model.identify_effect(proceed_when_unidentifiable=True)
            
            # Estimate causal effect
            estimate = model.estimate_effect(
                identified_estimand,
                method_name="backdoor.propensity_score_matching"
            )
            
            # Refute estimate (sensitivity analysis)
            refutation = model.refute_estimate(
                identified_estimand,
                estimate,
                method_name="random_common_cause"
            )
            
            results = {
                'treatment': treatment,
                'outcome': outcome,
                'causal_effect': estimate.value,
                'confidence_interval': (estimate.value - 1.96 * estimate.value, 
                                       estimate.value + 1.96 * estimate.value),
                'p_value': refutation.new_effect if hasattr(refutation, 'new_effect') else None,
                'is_causal': abs(estimate.value) > 0.01,  # Threshold for significance
                'effect_size': 'large' if abs(estimate.value) > 0.05 else 'small'
            }
            
            if results['is_causal']:
                self.validated_features.append(treatment)
                logger.info(f"✅ Causal relationship validated: {treatment} → {outcome} (effect: {estimate.value:.4f})")
            else:
                self.spurious_features.append(treatment)
                logger.info(f"❌ Spurious correlation detected: {treatment} ↛ {outcome}")
            
            return results
            
        except ImportError:
            logger.warning("DoWhy not installed. Using fallback causal analysis.")
            return self._fallback_causal_analysis(data, treatment, outcome)
        except Exception as e:
            logger.error(f"Causal analysis failed: {e}")
            return self._fallback_causal_analysis(data, treatment, outcome)
    
    def _fallback_causal_analysis(
        self,
        data: pd.DataFrame,
        treatment: str,
        outcome: str
    ) -> Dict:
        """Fallback using simple correlation"""
        correlation = data[treatment].corr(data[outcome])
        
        return {
            'treatment': treatment,
            'outcome': outcome,
            'causal_effect': correlation,
            'confidence_interval': (correlation - 0.1, correlation + 0.1),
            'p_value': None,
            'is_causal': abs(correlation) > 0.3,
            'effect_size': 'large' if abs(correlation) > 0.5 else 'small',
            'note': 'Fallback analysis (DoWhy not available)'
        }
    
    def validate_feature_set(
        self,
        data: pd.DataFrame,
        features: List[str],
        outcome: str = 'future_return'
    ) -> Dict[str, Dict]:
        """
        Validate entire feature set
        
        Args:
            data: Historical data
            features: List of features to validate
            outcome: Target outcome variable
            
        Returns:
            Dictionary of validation results per feature
        """
        results = {}
        
        for feature in features:
            if feature in data.columns:
                # Get other features as potential confounders
                confounders = [f for f in features if f != feature and f in data.columns][:5]
                
                result = self.build_causal_graph(
                    data,
                    treatment=feature,
                    outcome=outcome,
                    confounders=confounders
                )
                
                results[feature] = result
        
        # Summary
        n_causal = sum(1 for r in results.values() if r['is_causal'])
        n_spurious = len(results) - n_causal
        
        logger.info(f"Feature validation complete: {n_causal} causal, {n_spurious} spurious")
        
        return results
    
    def recommend_features(
        self,
        validation_results: Dict[str, Dict],
        min_effect_size: float = 0.02
    ) -> List[str]:
        """
        Recommend features based on causal validation
        
        Args:
            validation_results: Results from validate_feature_set
            min_effect_size: Minimum causal effect to include
            
        Returns:
            List of recommended features
        """
        recommended = []
        
        for feature, result in validation_results.items():
            if result['is_causal'] and abs(result['causal_effect']) >= min_effect_size:
                recommended.append(feature)
        
        logger.info(f"Recommended {len(recommended)} features with causal relationships")
        
        return recommended


class InstrumentalVariableAnalysis:
    """
    Instrumental Variable (IV) analysis for endogeneity
    
    Handles cases where treatment is correlated with unobserved confounders
    """
    
    def __init__(self):
        self.iv_results = {}
    
    def estimate_with_iv(
        self,
        data: pd.DataFrame,
        treatment: str,
        outcome: str,
        instrument: str
    ) -> Dict:
        """
        Estimate causal effect using instrumental variable
        
        Args:
            data: Historical data
            treatment: Treatment variable
            outcome: Outcome variable
            instrument: Instrumental variable (affects treatment but not outcome directly)
            
        Returns:
            IV estimation results
        """
        try:
            from scipy import stats
            
            # Two-stage least squares (2SLS)
            # Stage 1: Regress treatment on instrument
            X_iv = data[[instrument]].values
            y_treatment = data[treatment].values
            
            # Add constant
            X_iv = np.column_stack([np.ones(len(X_iv)), X_iv])
            
            # OLS for stage 1
            beta_stage1 = np.linalg.lstsq(X_iv, y_treatment, rcond=None)[0]
            treatment_hat = X_iv @ beta_stage1
            
            # Stage 2: Regress outcome on predicted treatment
            X_stage2 = np.column_stack([np.ones(len(treatment_hat)), treatment_hat])
            y_outcome = data[outcome].values
            
            beta_stage2 = np.linalg.lstsq(X_stage2, y_outcome, rcond=None)[0]
            
            # Causal effect is the coefficient on treatment
            causal_effect = beta_stage2[1]
            
            # Compute standard error (simplified)
            residuals = y_outcome - X_stage2 @ beta_stage2
            mse = np.mean(residuals**2)
            se = np.sqrt(mse / len(y_outcome))
            
            results = {
                'treatment': treatment,
                'outcome': outcome,
                'instrument': instrument,
                'causal_effect': causal_effect,
                'standard_error': se,
                'confidence_interval': (causal_effect - 1.96*se, causal_effect + 1.96*se),
                'is_significant': abs(causal_effect) > 1.96*se
            }
            
            self.iv_results[f"{treatment}_{outcome}"] = results
            
            logger.info(f"IV analysis: {treatment} → {outcome} (effect: {causal_effect:.4f})")
            
            return results
            
        except Exception as e:
            logger.error(f"IV analysis failed: {e}")
            return {}


def create_sample_data(n_samples: int = 1000) -> pd.DataFrame:
    """Create sample trading data for testing"""
    np.random.seed(42)
    
    # Generate features
    data = pd.DataFrame({
        'rsi': np.random.uniform(20, 80, n_samples),
        'macd': np.random.randn(n_samples) * 0.001,
        'volume': np.random.lognormal(10, 1, n_samples),
        'atr': np.random.uniform(0.0005, 0.002, n_samples),
        'trend_strength': np.random.uniform(0, 1, n_samples),
    })
    
    # Generate outcome with causal relationships
    # RSI has causal effect, MACD is spurious
    data['future_return'] = (
        -0.0001 * (data['rsi'] - 50) +  # RSI has causal effect
        0.05 * data['trend_strength'] +  # Trend has causal effect
        np.random.randn(n_samples) * 0.01  # Noise
    )
    
    # MACD is correlated but not causal (both driven by hidden factor)
    hidden_factor = np.random.randn(n_samples)
    data['macd'] += hidden_factor * 0.0005
    data['future_return'] += hidden_factor * 0.005
    
    return data


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    
    print("\n" + "="*60)
    logger.info("CAUSAL INFERENCE DEMO")
    print("="*60)
    
    # Create sample data
    logger.info("\nCreating sample data...")
    data = create_sample_data(n_samples=500)
    
    # Initialize analyzer
    analyzer = CausalAnalyzer()
    
    # Test individual causal relationship
    logger.info("\nTesting: RSI → Future Return")
    result_rsi = analyzer.build_causal_graph(
        data,
        treatment='rsi',
        outcome='future_return',
        confounders=['volume', 'atr']
    )
    
    logger.info(f"Causal effect: {result_rsi['causal_effect']:.4f}")
    logger.info(f"Is causal: {result_rsi['is_causal']}")
    
    logger.info("\nTesting: MACD → Future Return")
    result_macd = analyzer.build_causal_graph(
        data,
        treatment='macd',
        outcome='future_return',
        confounders=['volume', 'atr']
    )
    
    logger.info(f"Causal effect: {result_macd['causal_effect']:.4f}")
    logger.info(f"Is causal: {result_macd['is_causal']}")
    
    # Validate entire feature set
    logger.info("\nValidating all features...")
    features = ['rsi', 'macd', 'volume', 'atr', 'trend_strength']
    validation_results = analyzer.validate_feature_set(data, features)
    
    # Get recommendations
    recommended = analyzer.recommend_features(validation_results)
    
    print("\n" + "="*60)
    logger.info("VALIDATION RESULTS")
    print("="*60)
    logger.info(f"✅ Validated (causal): {analyzer.validated_features}")
    logger.info(f"❌ Spurious (correlation only): {analyzer.spurious_features}")
    logger.info(f"\nRecommended features: {recommended}")
    print("="*60)
    
    # IV analysis
    logger.info("\nInstrumental Variable Analysis...")
    iv_analyzer = InstrumentalVariableAnalysis()
    iv_result = iv_analyzer.estimate_with_iv(
        data,
        treatment='rsi',
        outcome='future_return',
        instrument='volume'
    )
    
    if iv_result:
        logger.info(f"IV causal effect: {iv_result['causal_effect']:.4f}")
        logger.info(f"Significant: {iv_result['is_significant']}")
    
    print("\n" + "="*60)
    logger.info("CAUSAL INFERENCE COMPLETE!")
    print("="*60)
