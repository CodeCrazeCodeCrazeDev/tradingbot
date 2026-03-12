"""
Tier 9: Meta-Learning & Ensemble Intelligence
Combines all signals and continuously improves
"""

import numpy as np
import pandas as pd
from typing import Any, Dict, List, Optional, Tuple
import logging
from dataclasses import dataclass
from datetime import datetime, timedelta
import joblib
from sklearn.ensemble import GradientBoostingRegressor
import xgboost as xgb

from trading_bot.brain.tier_structure import (
    TierBase, MarketStateVector, OrderFlowIntelligence, 
    MarketGeometryModel, RegimeContextVector, SentimentVector, 
    MacroContext, RiskParameters, ExecutionIntelligence, EliteBrainSignal
)

logger = logging.getLogger(__name__)


@dataclass
class ModelWeights:
    """Model weights for ensemble"""
    technical: float
    orderflow: float
    structure: float
    regime: float
    sentiment: float
    macro: float
    risk: float
    execution: float


class MetaLearningSystem:
    """Meta-learning system for model improvement"""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self.learning_rate = self.config.get('learning_rate', 0.01)
        self.model = None
        self.feature_importance = {}
        self.performance_history = []
    
    def update(self, features: Dict[str, float], 
               outcome: float, confidence: float) -> None:
        """
        Update meta-learning system
        
        Args:
            features: Dictionary of features
            outcome: Actual outcome (-1 to 1)
            confidence: Prediction confidence
        """
        try:
            # Convert features to array
            X = np.array([[v for v in features.values()]])
            y = np.array([outcome])
            
            # Initialize model if needed
            if self.model is None:
                self.model = GradientBoostingRegressor(
                    n_estimators=100,
                    learning_rate=self.learning_rate,
                    max_depth=3
                )
                self.model.fit(X, y)
            else:
                # Partial fit (online learning)
                sample_weight = np.array([confidence])
                self.model = self.model.fit(X, y, sample_weight=sample_weight)
            
            # Update feature importance
            importance = dict(zip(features.keys(), self.model.feature_importances_))
            
            # Exponential moving average of importance
            alpha = 0.1
            for feature, imp in importance.items():
                if feature in self.feature_importance:
                    self.feature_importance[feature] = (
                        alpha * imp + 
                        (1 - alpha) * self.feature_importance[feature]
                    )
                else:
                    self.feature_importance[feature] = imp
            
            # Update performance history
            self.performance_history.append({
                'timestamp': datetime.now(),
                'features': features,
                'outcome': outcome,
                'confidence': confidence
            })
            
        except Exception as e:
            logger.error(f"Error updating meta-learner: {str(e)}")
    
    def predict(self, features: Dict[str, float]) -> Dict[str, float]:
        """
        Generate prediction from meta-learner
        
        Args:
            features: Dictionary of features
            
        Returns:
            Dictionary with prediction and confidence
        """
        try:
            if self.model is None:
                return {
                    'prediction': 0.0,
                    'confidence': 0.0
                }
            
            # Convert features to array
            X = np.array([[v for v in features.values()]])
            
            # Get prediction
            prediction = self.model.predict(X)[0]
            
            # Calculate confidence based on feature importance
            weighted_confidence = 0.0
            total_weight = 0.0
            
            for feature, value in features.items():
                importance = self.feature_importance.get(feature, 0.0)
                weighted_confidence += abs(value) * importance
                total_weight += importance
            
            confidence = weighted_confidence / total_weight if total_weight > 0 else 0.0
            
            return {
                'prediction': prediction,
                'confidence': min(confidence, 1.0)
            }
            
        except Exception as e:
            logger.error(f"Error in meta-learner prediction: {str(e)}")
            return {
                'prediction': 0.0,
                'confidence': 0.0
            }


class AdaptiveEnsembleBlending:
    """Adaptive ensemble blending of multiple models"""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self.weights = ModelWeights(
            technical=0.2,
            orderflow=0.15,
            structure=0.15,
            regime=0.1,
            sentiment=0.1,
            macro=0.1,
            risk=0.1,
            execution=0.1
        )
        self.model = xgb.XGBRegressor(
            n_estimators=100,
            learning_rate=0.01,
            max_depth=3
        )
        self.performance_history = []
    
    def blend_signals(self, signals: Dict[str, float], 
                     confidences: Dict[str, float]) -> Dict[str, float]:
        """
        Blend multiple signals into a single prediction
        
        Args:
            signals: Dictionary of signals from each component
            confidences: Dictionary of confidence scores
            
        Returns:
            Dictionary with blended signal and confidence
        """
        try:
            # Get weights for each component
            weights = {
                'technical': self.weights.technical,
                'orderflow': self.weights.orderflow,
                'structure': self.weights.structure,
                'regime': self.weights.regime,
                'sentiment': self.weights.sentiment,
                'macro': self.weights.macro,
                'risk': self.weights.risk,
                'execution': self.weights.execution
            }
            
            # Calculate confidence-adjusted weights
            adjusted_weights = {}
            total_weight = 0.0
            
            for component, weight in weights.items():
                if component in signals and component in confidences:
                    adjusted_weight = weight * confidences[component]
                    adjusted_weights[component] = adjusted_weight
                    total_weight += adjusted_weight
            
            if total_weight == 0:
                return {
                    'signal': 0.0,
                    'confidence': 0.0
                }
            
            # Normalize weights
            for component in adjusted_weights:
                adjusted_weights[component] /= total_weight
            
            # Calculate weighted signal
            weighted_signal = 0.0
            for component, weight in adjusted_weights.items():
                weighted_signal += signals[component] * weight
            
            # Calculate blended confidence
            blended_confidence = sum(
                confidences[c] * w for c, w in adjusted_weights.items()
            )
            
            return {
                'signal': weighted_signal,
                'confidence': blended_confidence
            }
            
        except Exception as e:
            logger.error(f"Error blending signals: {str(e)}")
            return {
                'signal': 0.0,
                'confidence': 0.0
            }
    
    def update_weights(self, performance: Dict[str, float]) -> None:
        """
        Update component weights based on performance
        
        Args:
            performance: Dictionary of component performance metrics
        """
        try:
            # Calculate new weights based on performance
            total_performance = sum(max(0, p) for p in performance.values())
            
            if total_performance > 0:
                new_weights = {}
                for component, perf in performance.items():
                    new_weights[component] = max(0, perf) / total_performance
                
                # Update weights with smoothing
                alpha = 0.1  # Smoothing factor
                self.weights = ModelWeights(
                    technical=alpha * new_weights.get('technical', 0.2) + (1 - alpha) * self.weights.technical,
                    orderflow=alpha * new_weights.get('orderflow', 0.15) + (1 - alpha) * self.weights.orderflow,
                    structure=alpha * new_weights.get('structure', 0.15) + (1 - alpha) * self.weights.structure,
                    regime=alpha * new_weights.get('regime', 0.1) + (1 - alpha) * self.weights.regime,
                    sentiment=alpha * new_weights.get('sentiment', 0.1) + (1 - alpha) * self.weights.sentiment,
                    macro=alpha * new_weights.get('macro', 0.1) + (1 - alpha) * self.weights.macro,
                    risk=alpha * new_weights.get('risk', 0.1) + (1 - alpha) * self.weights.risk,
                    execution=alpha * new_weights.get('execution', 0.1) + (1 - alpha) * self.weights.execution
                )
            
            # Update performance history
            self.performance_history.append({
                'timestamp': datetime.now(),
                'performance': performance,
                'weights': self.weights.__dict__
            })
            
        except Exception as e:
            logger.error(f"Error updating weights: {str(e)}")


class SignalCoherenceAnalyzer:
    """Analyzes coherence between signals across timeframes"""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self.timeframes = self.config.get('timeframes', ['1m', '5m', '15m', '1h', '4h'])
    
    def analyze_coherence(self, signals: Dict[str, Dict[str, float]]) -> Dict[str, Any]:
        """
        Analyze signal coherence across timeframes
        
        Args:
            signals: Dictionary of signals per timeframe
            
        Returns:
            Dictionary with coherence analysis
        """
        try:
            # Calculate signal agreement
            agreements = {}
            for tf1 in signals:
                for tf2 in signals:
                    if tf1 < tf2:
                        sig1 = signals[tf1].get('signal', 0)
                        sig2 = signals[tf2].get('signal', 0)
                        agreements[f"{tf1}-{tf2}"] = np.sign(sig1) == np.sign(sig2)
            
            # Calculate coherence score
            if agreements:
                coherence = sum(agreements.values()) / len(agreements)
            else:
                coherence = 0.0
            
            # Calculate signal strength correlation
            strengths = [signals[tf].get('signal', 0) for tf in signals]
            if len(strengths) > 1:
                strength_corr = np.corrcoef(strengths)[0, 1]
            else:
                strength_corr = 0.0
            
            # Determine alignment type
            if coherence > 0.8:
                alignment = 'strong'
            elif coherence > 0.5:
                alignment = 'moderate'
            else:
                alignment = 'weak'
            
            return {
                'coherence_score': coherence,
                'strength_correlation': strength_corr,
                'alignment': alignment,
                'agreements': agreements
            }
            
        except Exception as e:
            logger.error(f"Error analyzing coherence: {str(e)}")
            return {
                'coherence_score': 0.0,
                'strength_correlation': 0.0,
                'alignment': 'weak',
                'agreements': {}
            }


class Tier9MetaLearning(TierBase):
    """
    Tier 9: Meta-Learning & Ensemble Intelligence
    
    Combines all signals and continuously improves:
    - Meta-Learning System
    - Adaptive Ensemble Blending
    - Signal Coherence Analysis
    - Confidence Scoring
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__("Tier 9: Meta-Learning", config)
        self.meta_learner = None
        self.ensemble = None
        self.coherence = None
    
    def _initialize_components(self) -> None:
        """Initialize tier-specific components"""
        self.meta_learner = MetaLearningSystem(self.config.get('meta', {}))
        self.ensemble = AdaptiveEnsembleBlending(self.config.get('ensemble', {}))
        self.coherence = SignalCoherenceAnalyzer(self.config.get('coherence', {}))
    
    def process(self, market_data: pd.DataFrame, 
               previous_tier_output: Optional[ExecutionIntelligence] = None,
               additional_inputs: Optional[Dict[str, Any]] = None) -> EliteBrainSignal:
        """
        Process all signals and generate final decision
        
        Args:
            market_data: DataFrame with OHLCV data
            previous_tier_output: Output from Tier 8 (ExecutionIntelligence)
            additional_inputs: Dictionary with all tier outputs and timeframe data
            
        Returns:
            EliteBrainSignal with final trading decision
        """
        if not self.validate_input(market_data):
            logger.error("Invalid input data for Tier 9")
            return None
        try:
        
            # Get tier outputs
            tier_outputs = additional_inputs.get('tier_outputs', {})
            timeframe_data = additional_inputs.get('timeframe_data', {})
            
            # Extract signals and confidences
            signals = {
                'technical': tier_outputs.get('tier1', {}).get('signal_value', 0),
                'orderflow': tier_outputs.get('tier2', {}).get('signal_value', 0),
                'structure': tier_outputs.get('tier3', {}).get('signal_value', 0),
                'regime': tier_outputs.get('tier4', {}).get('signal_value', 0),
                'sentiment': tier_outputs.get('tier5', {}).get('signal_value', 0),
                'macro': tier_outputs.get('tier6', {}).get('signal_value', 0),
                'risk': tier_outputs.get('tier7', {}).get('signal_value', 0),
                'execution': tier_outputs.get('tier8', {}).get('signal_value', 0)
            }
            
            confidences = {
                'technical': tier_outputs.get('tier1', {}).get('confidence', 0),
                'orderflow': tier_outputs.get('tier2', {}).get('confidence', 0),
                'structure': tier_outputs.get('tier3', {}).get('confidence', 0),
                'regime': tier_outputs.get('tier4', {}).get('confidence', 0),
                'sentiment': tier_outputs.get('tier5', {}).get('confidence', 0),
                'macro': tier_outputs.get('tier6', {}).get('confidence', 0),
                'risk': tier_outputs.get('tier7', {}).get('confidence', 0),
                'execution': tier_outputs.get('tier8', {}).get('confidence', 0)
            }
            
            # Analyze signal coherence across timeframes
            coherence = self.coherence.analyze_coherence(timeframe_data)
            
            # Get meta-learning prediction
            meta_features = {
                **signals,
                **confidences,
                'coherence': coherence['coherence_score']
            }
            meta_prediction = self.meta_learner.predict(meta_features)
            
            # Blend signals
            ensemble = self.ensemble.blend_signals(signals, confidences)
            
            # Calculate final signal
            # Weight meta-learning and ensemble predictions
            meta_weight = min(len(self.meta_learner.performance_history) / 1000, 0.5)
            ensemble_weight = 1 - meta_weight
            
            final_signal = (
                meta_weight * meta_prediction['prediction'] +
                ensemble_weight * ensemble['signal']
            )
            
            # Calculate uncertainty
            uncertainty = 1.0 - min(
                meta_prediction['confidence'],
                ensemble['confidence'],
                coherence['coherence_score']
            )
            
            # Determine position type
            if abs(final_signal) < 0.1:
                position_type = 'none'
            elif final_signal > 0:
                position_type = 'long'
            else:
                position_type = 'short'
            
            # Create explanation
            explanation = {
                'meta_learning': {
                    'prediction': meta_prediction['prediction'],
                    'confidence': meta_prediction['confidence'],
                    'feature_importance': self.meta_learner.feature_importance
                },
                'ensemble': {
                    'weights': self.ensemble.weights.__dict__,
                    'signal': ensemble['signal'],
                    'confidence': ensemble['confidence']
                },
                'coherence': coherence,
                'shap_values': {
                    feature: importance
                    for feature, importance in 
                    sorted(self.meta_learner.feature_importance.items(),
                          key=lambda x: abs(x[1]),
                          reverse=True)
                }
            }
            
            # Create elite brain signal
            signal = EliteBrainSignal(
                timestamp=market_data.index[-1],
                signal_value=final_signal,
                confidence=1.0 - uncertainty,
                final_decision='BUY' if final_signal > 0.1 else 'SELL' if final_signal < -0.1 else 'HOLD',
                position_type=position_type,
                ensemble_weights=self.ensemble.weights.__dict__,
                uncertainty=uncertainty,
                coherence_score=coherence['coherence_score'],
                explanation=explanation
            )
            
            self.last_output = signal
            return signal
            
        except Exception as e:
            logger.error(f"Error processing Tier 9: {str(e)}")
            return None
    
    def update_from_feedback(self, trade_result: Dict[str, Any]) -> None:
        """
        Update models from trade feedback
        
        Args:
            trade_result: Dictionary with trade outcome information
        """
        try:
            # Extract features and outcome
            features = trade_result.get('features', {})
            outcome = trade_result.get('pnl', 0)
            confidence = trade_result.get('confidence', 0)
            
            # Normalize outcome to -1 to 1
            max_expected_pnl = 0.02  # 2% max expected return
            normalized_outcome = min(max(outcome / max_expected_pnl, -1), 1)
            
            # Update meta-learner
            self.meta_learner.update(features, normalized_outcome, confidence)
            
            # Update ensemble weights
            component_performance = trade_result.get('component_performance', {})
            if component_performance:
                self.ensemble.update_weights(component_performance)
            
        except Exception as e:
            logger.error(f"Error updating from feedback: {str(e)}")


# Example usage
if __name__ == "__main__":
    # Configure logging
    logging.basicConfig(level=logging.INFO, 
                      format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    
    # Create sample data
    dates = pd.date_range('2024-01-01', periods=250, freq='1H')
    np.random.seed(42)
    
    df = pd.DataFrame({
        'open': np.random.randn(250).cumsum() + 100,
        'high': np.random.randn(250).cumsum() + 102,
        'low': np.random.randn(250).cumsum() + 98,
        'close': np.random.randn(250).cumsum() + 100,
        'volume': np.random.randint(1000, 10000, 250)
    }, index=dates)
    
    # Create sample tier outputs
    tier_outputs = {
        'tier1': {'signal_value': 0.5, 'confidence': 0.8},
        'tier2': {'signal_value': 0.3, 'confidence': 0.7},
        'tier3': {'signal_value': 0.4, 'confidence': 0.6},
        'tier4': {'signal_value': 0.2, 'confidence': 0.9},
        'tier5': {'signal_value': 0.1, 'confidence': 0.5},
        'tier6': {'signal_value': 0.3, 'confidence': 0.6},
        'tier7': {'signal_value': 0.4, 'confidence': 0.7},
        'tier8': {'signal_value': 0.2, 'confidence': 0.8}
    }
    
    # Create sample timeframe data
    timeframe_data = {
        '1m': {'signal': 0.3, 'confidence': 0.6},
        '5m': {'signal': 0.4, 'confidence': 0.7},
        '15m': {'signal': 0.3, 'confidence': 0.8},
        '1h': {'signal': 0.5, 'confidence': 0.7},
        '4h': {'signal': 0.4, 'confidence': 0.6}
    }
    
    # Create sample additional inputs
    additional_inputs = {
        'tier_outputs': tier_outputs,
        'timeframe_data': timeframe_data
    }
    
    # Initialize and process
    tier9 = Tier9MetaLearning()
    tier9.initialize()
    result = tier9.process(df, additional_inputs=additional_inputs)
    
    # Print results
    logger.info("\n=== Tier 9: Meta-Learning Results ===")
    logger.info(f"Signal: {result.signal_value:.4f}")
    logger.info(f"Confidence: {result.confidence:.2%}")
    logger.info(f"Decision: {result.final_decision}")
    logger.info(f"Position Type: {result.position_type}")
    logger.info(f"Uncertainty: {result.uncertainty:.2%}")
    logger.info(f"Coherence Score: {result.coherence_score:.2%}")
    logger.info("\nEnsemble Weights:")
    for component, weight in result.ensemble_weights.items():
        logger.info(f"- {component}: {weight:.2%}")
    logger.info("\nTop SHAP Values:")
    for feature, value in list(result.explanation['shap_values'].items())[:5]:
        logger.info(f"- {feature}: {value:.4f}")
