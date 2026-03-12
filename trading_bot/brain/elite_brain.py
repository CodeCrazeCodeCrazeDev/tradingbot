"""
from pathlib import Path
AlphaAlgo Elite Brain - Central Intelligence System
Integrates all tiers into a unified decision-making system
"""

import numpy as np
import pandas as pd
from typing import Any, Dict, List, Optional, Tuple, Union
import logging
import os
import json
from datetime import datetime
import matplotlib.pyplot as plt
import seaborn as sns

from trading_bot.brain.tier_structure import (
    AlphaBrain, SignalOutput, MarketStateVector, OrderFlowIntelligence,
    MarketGeometryModel, RegimeContextVector, SentimentVector, MacroContext,
    RiskParameters, ExecutionIntelligence, EliteBrainSignal
)

logger = logging.getLogger(__name__)


class EliteBrainController:
    """
    AlphaAlgo Elite Brain Controller
    
    High-level interface for the AlphaAlgo intelligence hierarchy
    """
    
    def __init__(self, config_path: Optional[str] = None):
        """
        Initialize the Elite Brain Controller
        
        Args:
            config_path: Path to configuration file
        """
        self.config = self._load_config(config_path)
        self.brain = None
        self.is_initialized = False
        self.last_decision = None
        self.decision_history = []
        
        logger.info("Elite Brain Controller initialized")
    
    def _load_config(self, config_path: Optional[str]) -> Dict[str, Any]:
        """Load configuration from file"""
        default_config = {
            'tier1': {
                'momentum': {
                    'rsi_period': 14,
                    'macd_fast': 12,
                    'macd_slow': 26,
                    'macd_signal': 9
                },
                'volatility': {
                    'atr_period': 14,
                    'bb_period': 20,
                    'bb_std': 2.0
                },
                'trend': {
                    'kama_period': 10,
                    'frama_period': 16,
                    'supertrend_period': 10,
                    'supertrend_mult': 3.0
                },
                'fractal': {
                    'hurst_lags': 100
                }
            },
            'tier2': {
                'basic_volume': {},
                'advanced_volume': {
                    'heatmap_bins': 50,
                    'cvd_timeframes': ['5T', '15T', '1H', '4H']
                },
                'pressure': {
                    'absorption_lookback': 20,
                    'tib_threshold': 1000
                },
                'institutional': {
                    'iceberg_volume_threshold': 2.0,
                    'iceberg_price_tolerance': 0.0001
                }
            },
            'tier3': {
                # Structure and liquidity settings
            },
            'tier4': {
                # Regime detection settings
            },
            'tier5': {
                # Sentiment analysis settings
            },
            'tier6': {
                # Macro analysis settings
            },
            'tier7': {
                # Risk management settings
            },
            'tier8': {
                # Execution settings
            },
            'tier9': {
                # Meta-learning settings
            }
        }
        
        if config_path and os.path.exists(config_path):
            try:
                with open(config_path, 'r') as f:
                    user_config = json.load(f)
                
                # Merge configs
                self._merge_configs(default_config, user_config)
                logger.info(f"Configuration loaded from {config_path}")
            except Exception as e:
                logger.error(f"Error loading config from {config_path}: {str(e)}")
                logger.info("Using default configuration")
        else:
            logger.info("Using default configuration")
        
        return default_config
    
    def _merge_configs(self, default_config: Dict, user_config: Dict) -> None:
        """Recursively merge user config into default config"""
        for key, value in user_config.items():
            if key in default_config and isinstance(default_config[key], dict) and isinstance(value, dict):
                self._merge_configs(default_config[key], value)
            else:
                default_config[key] = value
    
    def initialize(self) -> bool:
        """Initialize the Elite Brain"""
        try:
            # Create and initialize AlphaBrain
            self.brain = AlphaBrain(config=self.config)
            if not self.brain.initialize_tiers():
                logger.error("Failed to initialize AlphaBrain tiers")
                return False
            
            self.is_initialized = True
            logger.info("[OK] Elite Brain Controller initialized successfully")
            return True
        except Exception as e:
            logger.error(f"[ERROR] Failed to initialize Elite Brain: {str(e)}")
            return False
    
    def process_market_data(self, market_data: pd.DataFrame, 
                           additional_inputs: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Process market data and generate trading decision
        
        Args:
            market_data: DataFrame with OHLCV data
            additional_inputs: Additional inputs like news, sentiment, etc.
            
        Returns:
            Dictionary with trading decision and explanation
        """
        if not self.is_initialized:
            try:
                if not self.initialize():
                    logger.error("Failed to initialize Elite Brain")
                    return {"error": "Elite Brain not initialized"}

                # Process data through AlphaBrain
                decision = self.brain.process_market_data(market_data, additional_inputs)

                if decision is None:
                    logger.error("Failed to generate decision")
                    return {"error": "Failed to generate decision"}

                # Store decision
                self.last_decision = decision
                self.decision_history.append({
                    'timestamp': decision.timestamp,
                    'decision': decision.final_decision,
                    'confidence': decision.confidence,
                    'position_type': decision.position_type,
                    'signal_value': decision.signal_value
                })

                # Create decision summary
                decision_summary = {
                    'timestamp': decision.timestamp,
                    'decision': decision.final_decision,
                    'position_type': decision.position_type,
                    'confidence': decision.confidence,
                    'explanation': decision.explanation,
                    'ensemble_weights': decision.ensemble_weights,
                    'uncertainty': decision.uncertainty,
                    'coherence_score': decision.coherence_score
                }

                return decision_summary

            except Exception as e:
                logger.error(f"Error processing market data: {str(e)}")
                return {"error": f"Processing error: {str(e)}"}

    def get_explanation(self) -> Dict[str, Any]:
        """Get detailed explanation for the last decision"""
        if not self.last_decision:
            return {"error": "No decision has been made yet"}
        
        if not self.brain:
            return {"error": "Elite Brain not initialized"}
        
        return self.brain.get_explanation()
    
    def update_performance(self, trade_result: Dict[str, Any]) -> None:
        """
        Update performance metrics after a trade
        
        Args:
            trade_result: Dictionary with trade outcome information
        """
        if not self.brain:
            logger.error("Elite Brain not initialized")
            return
        
        self.brain.update_performance(trade_result)
        logger.info(f"Performance updated with trade result: {trade_result.get('pnl', 0)}")
    
    def visualize_decision(self, market_data: Optional[pd.DataFrame] = None, 
                          save_path: Optional[str] = None) -> None:
        """
        Visualize the last decision
        
        Args:
            market_data: DataFrame with OHLCV data
            save_path: Path to save the visualization
        """
        if not self.last_decision:
            logger.error("No decision to visualize")
            return
        try:
        
            # Create figure
            fig, axes = plt.subplots(3, 1, figsize=(12, 16), gridspec_kw={'height_ratios': [2, 1, 1]})
            
            # Plot price chart
            if market_data is not None:
                ax = axes[0]
                ax.set_title('Market Data and Decision', fontsize=14)
                
                # Plot OHLC
                ax.plot(market_data.index, market_data['close'], label='Close', color='blue')
                
                # Highlight decision
                decision_color = 'green' if self.last_decision.final_decision == 'BUY' else 'red'
                ax.axvline(x=self.last_decision.timestamp, color=decision_color, linestyle='--', 
                         alpha=0.7, label=f'Decision: {self.last_decision.final_decision}')
                
                ax.legend()
                ax.grid(True, alpha=0.3)
            
            # Plot confidence and signal
            ax = axes[1]
            ax.set_title('Decision Confidence and Signal', fontsize=14)
            
            # Create x-axis for decision history
            if self.decision_history:
                timestamps = [d['timestamp'] for d in self.decision_history]
                confidences = [d['confidence'] for d in self.decision_history]
                signals = [d['signal_value'] for d in self.decision_history]
                
                ax.plot(timestamps, confidences, label='Confidence', color='purple', marker='o')
                ax.plot(timestamps, signals, label='Signal', color='orange', marker='x')
                
                ax.axhline(y=0, color='black', linestyle='-', alpha=0.3)
                ax.axhline(y=0.7, color='green', linestyle='--', alpha=0.3, label='High Confidence')
                ax.axhline(y=0.3, color='red', linestyle='--', alpha=0.3, label='Low Confidence')
                
                ax.legend()
                ax.grid(True, alpha=0.3)
            
            # Plot SHAP values
            ax = axes[2]
            ax.set_title('Feature Importance (SHAP Values)', fontsize=14)
            
            # Get SHAP values
            explanation = self.get_explanation()
            shap_values = explanation.get('shap_values', {})
            
            if shap_values:
                # Sort by absolute value
                sorted_shap = sorted(shap_values.items(), key=lambda x: abs(x[1]), reverse=True)
                features = [x[0] for x in sorted_shap[:10]]  # Top 10 features
                values = [x[1] for x in sorted_shap[:10]]
                
                # Create horizontal bar chart
                colors = ['green' if v > 0 else 'red' for v in values]
                ax.barh(features, values, color=colors)
                ax.axvline(x=0, color='black', linestyle='-', alpha=0.3)
                ax.grid(True, alpha=0.3)
            
            plt.tight_layout()
            
            # Save or show
            if save_path:
                plt.savefig(save_path)
                logger.info(f"Visualization saved to {save_path}")
            else:
                plt.show()
            
        except Exception as e:
            logger.error(f"Error visualizing decision: {str(e)}")
    
    def save_brain_state(self, path: str) -> bool:
        """
        Save the current brain state
        
        Args:
            path: Path to save the brain state
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Create state dictionary
            state = {
                'timestamp': datetime.now().isoformat(),
                'decision_history': self.decision_history,
                'last_decision': {
                    'timestamp': self.last_decision.timestamp.isoformat() if self.last_decision else None,
                    'decision': self.last_decision.final_decision if self.last_decision else None,
                    'confidence': self.last_decision.confidence if self.last_decision else None,
                    'position_type': self.last_decision.position_type if self.last_decision else None
                }
            }
            
            # Save to file
            with open(path, 'w') as f:
                json.dump(state, f, indent=2)
            
            logger.info(f"Brain state saved to {path}")
            return True
        
        except Exception as e:
            logger.error(f"Error saving brain state: {str(e)}")
            return False
    
    def load_brain_state(self, path: str) -> bool:
        """
        Load brain state from file
        
        Args:
            path: Path to load the brain state from
            
        Returns:
            True if successful, False otherwise
        """
        try:
            if not os.path.exists(path):
                logger.error(f"Brain state file not found: {path}")
                return False
            
            # Load from file
            with open(path, 'r') as f:
                state = json.load(f)
            
            # Restore state
            self.decision_history = state.get('decision_history', [])
            
            logger.info(f"Brain state loaded from {path}")
            return True
        
        except Exception as e:
            logger.error(f"Error loading brain state: {str(e)}")
            return False


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
    
    # Initialize Elite Brain
    controller = EliteBrainController()
    controller.initialize()
    
    # Process market data
    decision = controller.process_market_data(df)
    
    # Print decision
    logger.info("\n=== Elite Brain Decision ===")
    logger.info(f"Decision: {decision['decision']}")
    logger.info(f"Position Type: {decision['position_type']}")
    logger.info(f"Confidence: {decision['confidence']:.2%}")
    logger.info(f"Coherence Score: {decision['coherence_score']:.2%}")
    logger.info(f"Uncertainty: {decision['uncertainty']:.2%}")
    
    # Get explanation
    explanation = controller.get_explanation()
    
    logger.info("\n=== Decision Explanation ===")
    logger.info("Top SHAP Values:")
    shap_values = explanation.get('shap_values', {})
    for feature, value in sorted(shap_values.items(), key=lambda x: abs(x[1]), reverse=True)[:5]:
        logger.info(f"- {feature}: {value:.4f}")
    
    # Visualize decision
    controller.visualize_decision(df)
