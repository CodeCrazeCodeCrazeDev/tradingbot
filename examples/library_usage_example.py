import logging
#!/usr/bin/env python
"""Trading Bot Library Usage Example

This example demonstrates how to use the trading bot as a library in a custom application.
It shows how to integrate the ML strategy engine, execution algorithms, and emotional tracking
into your own trading system. It also demonstrates the use of advanced ML capabilities including
transformer-based deep learning models and reinforcement learning with PPO.
"""
import sys
import os
import datetime as dt
import pandas as pd
import numpy as np
import time
from loguru import logger

# Add parent directory to path to allow importing modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../')))

# Import trading bot modules
from trading_bot.data import MT5Interface
from trading_bot.strategy.ml_strategy import MLStrategyEngine
from trading_bot.execution.paper_executor import PaperExecutor
from trading_bot.execution.algorithms import TWAPExecutor, VWAPExecutor, SmartOrderRouter
from trading_bot.risk import RiskManager
from trading_bot.analytics.emotional_tracker import EmotionalStateTracker, TraderJournal
from trading_bot.analytics.enhanced_performance import EnhancedPerformanceAnalytics
from trading_bot.ml.predictive_models import PricePredictor, PatternRecognizer, TimeSeriesForecaster, TransformerModel
from trading_bot.ml.reinforcement import StrategyOptimizer, PPOAgent, MarketRegimeClassifier
from trading_bot.analysis.price_action import PriceActionAnalyzer
from trading_bot.analysis.order_flow import OrderFlowAnalyzer
from typing import Set
import datetime
import numpy
import pandas


class CustomTradingSystem:
    """
    A custom trading system that uses components from the trading bot library.
    
    This class demonstrates how to integrate the trading bot components into your own
    trading system, including ML strategy, execution algorithms, and emotional tracking.
    """
    
    def __init__(self, symbol="EURUSD", timeframe="M15", use_advanced_ml=True):
        """Initialize the custom trading system."""
        self.symbol = symbol
        self.timeframe = timeframe
        self.use_advanced_ml = use_advanced_ml
        self.logger = self._setup_logger()
        
        # Connect to MT5
        self.mt5 = MT5Interface()
        if not self.mt5.connect():
            self.logger.error("Failed to connect to MT5")
            raise ConnectionError("Failed to connect to MT5")
        
        # Initialize components
        self.risk_manager = RiskManager(self.mt5)
        self.emotional_tracker = EmotionalStateTracker()
        self.trader_journal = TraderJournal()
        
        # Initialize advanced ML models if enabled
        if use_advanced_ml:
            self.logger.info("Initializing advanced ML models")
            self.transformer_model = TransformerModel()
            self.ppo_agent = PPOAgent()
            self.regime_classifier = MarketRegimeClassifier()
            self.price_action = PriceActionAnalyzer()
            self.order_flow = OrderFlowAnalyzer()
        
        # Initialize ML strategy with advanced configuration
        ml_config = {
            "use_transformer": use_advanced_ml,
            "use_rl": use_advanced_ml,
            "use_sentiment": True,
            "market_regime": use_advanced_ml,
            "order_flow": use_advanced_ml
        }
        
        self.strategy = MLStrategyEngine(
            self.mt5,
            symbol=symbol,
            config=ml_config
        )
        
        # Initialize base executor and wrap with Smart Order Router
        self.base_executor = PaperExecutor(self.mt5, self.risk_manager)
        self.executor = SmartOrderRouter(self.base_executor)
        
        # Store trades for performance analysis
        self.trades = []
        
        self.logger.info(f"Custom trading system initialized for {symbol} on {timeframe} with advanced ML: {use_advanced_ml}")
    
    def _setup_logger(self):
        """Set up a custom logger."""
        custom_logger = logger.bind(system="CustomTrading")
        logger.remove()
        logger.add(
            sys.stderr,
            format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{extra[system]}</cyan> - <level>{message}</level>",
            level="INFO"
        )
        logger.add(
            "logs/custom_trading_{time}.log",
            rotation="500 MB",
            retention="10 days",
            format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {extra[system]} - {message}",
            level="DEBUG"
        )
        return custom_logger
    
    def record_emotional_state(self, state_dict):
        """Record the trader's emotional state."""
        self.logger.info(f"Recording emotional state: {state_dict}")
        return self.emotional_tracker.record_state(state_dict)
    
    def add_journal_entry(self, content, entry_type="general", emotional_state=None, metadata=None):
        """Add an entry to the trader's journal."""
        self.logger.info(f"Adding journal entry: {entry_type} - {content}")
        return self.trader_journal.add_entry(
            entry_type=entry_type,
            content=content,
            emotional_state=emotional_state,
            metadata=metadata
        )
    
    def analyze_market(self, bars=200):
        """Analyze the market and generate trading signals."""
        self.logger.info(f"Analyzing market for {self.symbol} with {bars} bars")
        
        # Get historical data
        df = self.mt5.get_ohlc(self.symbol, self.timeframe, bars)
        if df is None or df.empty:
            self.logger.error("Failed to retrieve historical data")
            return []
        
        # Apply advanced ML analysis if enabled
        if self.use_advanced_ml:
            self._apply_advanced_ml_analysis(df)
        
        # Generate signals using ML strategy
        signals = self.strategy.analyse(df)
        
        # Apply custom filtering or signal enhancement
        signals = self._enhance_signals(signals)
        
        return signals
        
    def _apply_advanced_ml_analysis(self, df):
        """Apply advanced ML models to market data."""
        self.logger.info("Applying advanced ML analysis")
        
        # Use transformer model for price prediction
        transformer_results = self._use_transformer_model(df)
        
        # Use PPO agent for strategy optimization
        ppo_results = self._use_ppo_agent(df)
        
        # Use market regime classifier
        regime_results = self._use_market_regime_classifier(df)
        
        # Use price action and order flow analysis
        pa_results = self.price_action.analyze(df)
        of_results = self.order_flow.analyze(df)
        
        # Log combined insights
        self.logger.info(f"ML Analysis Complete - Transformer confidence: {transformer_results.get('confidence', 0):.2f}, "
                       f"PPO action: {ppo_results.get('action', 'unknown')}, "
                       f"Market regime: {regime_results.get('regime', 'unknown')}")
        
        return {
            "transformer": transformer_results,
            "ppo": ppo_results,
            "regime": regime_results,
            "price_action": pa_results,
            "order_flow": of_results
        }
    
    def _use_transformer_model(self, df):
        """Use transformer model for price prediction."""
        self.logger.info("Using transformer model for price prediction")
        
        try:
            # Prepare data for the transformer model
            X, y = self.transformer_model.prepare_data(df)
            
            # Make price predictions
            predictions = self.transformer_model.predict(df, forecast_horizon=5)
            
            # Evaluate model performance
            metrics = self.transformer_model.evaluate(df)
            
            # Get feature importance
            feature_importance = self.transformer_model.feature_importance()
            
            # Calculate prediction confidence based on metrics
            confidence = 0.8  # Simulated confidence score
            
            self.logger.info(f"Transformer prediction for next 5 periods: {predictions}")
            self.logger.info(f"Transformer metrics: RMSE={metrics.get('rmse', 0):.4f}, MAE={metrics.get('mae', 0):.4f}")
            
            return {
                "predictions": predictions,
                "metrics": metrics,
                "confidence": confidence,
                "feature_importance": feature_importance
            }
        except Exception as e:
            self.logger.error(f"Error in transformer model: {e}")
            return {"error": str(e)}
    
    def _use_ppo_agent(self, df):
        """Use PPO agent for reinforcement learning-based trading."""
        self.logger.info("Using PPO agent for strategy optimization")
        
        try:
            # Preprocess state for the PPO agent
            state = self.ppo_agent.preprocess_state(df)
            
            # Select action based on current state
            action, action_probs = self.ppo_agent.select_action(df.iloc[-1])
            
            # Evaluate agent performance
            eval_metrics = self.ppo_agent.evaluate(df)
            
            action_map = {0: "HOLD", 1: "BUY", 2: "SELL"}
            action_name = action_map.get(action, f"Unknown({action})")
            
            self.logger.info(f"PPO agent action: {action_name} with probabilities {action_probs}")
            self.logger.info(f"PPO evaluation: Sharpe={eval_metrics.get('sharpe_ratio', 0):.2f}, "
                           f"Return={eval_metrics.get('total_return', 0):.2f}%")
            
            return {
                "action": action_name,
                "action_probs": action_probs,
                "metrics": eval_metrics
            }
        except Exception as e:
            self.logger.error(f"Error in PPO agent: {e}")
            return {"error": str(e)}
    
    def _use_market_regime_classifier(self, df):
        """Use market regime classifier to identify market conditions."""
        self.logger.info("Using market regime classifier")
        
        try:
            # Classify current market regime
            regime = self.regime_classifier.classify(df)
            
            # Get regime transition probabilities
            transitions = self.regime_classifier.get_transition_probabilities()
            
            # Get recommended actions for current regime
            recommendations = self.regime_classifier.get_regime_recommendations(regime)
            
            self.logger.info(f"Current market regime: {regime}")
            self.logger.info(f"Regime recommendations: {recommendations}")
            
            return {
                "regime": regime,
                "transitions": transitions,
                "recommendations": recommendations
            }
        except Exception as e:
            self.logger.error(f"Error in market regime classifier: {e}")
            return {"error": str(e)}
    
    def _enhance_signals(self, signals):
        """Apply custom enhancements to the signals."""
        if not signals:
            return signals
            
        # Example: Filter signals by confidence threshold
        enhanced_signals = [s for s in signals if s.confidence >= 75.0]
        
        # Example: Add custom metadata to signals
        for signal in enhanced_signals:
            signal.custom_metadata = {
                "enhanced_by": "CustomTradingSystem",
                "timestamp": dt.datetime.now().isoformat()
            }
        
        self.logger.info(f"Enhanced signals: {len(enhanced_signals)} of {len(signals)} passed filtering")
        return enhanced_signals
    
    def execute_signals(self, signals):
        """Execute the trading signals."""
        if not signals:
            self.logger.info("No signals to execute")
            return []
            
        self.logger.info(f"Executing {len(signals)} signals")
        
        # Record pre-execution emotional state
        self.record_emotional_state({
            'confidence': 0.7,
            'fear': 0.3,
            'excitement': 0.6
        })
        
        # Get current price
        current_price = self.mt5.get_current_price(self.symbol)
        
        # Execute signals using Smart Order Router
        executed_trades = self.executor.process(signals, current_price)
        
        # Record post-execution emotional state
        self.record_emotional_state({
            'confidence': 0.6,
            'satisfaction': 0.7,
            'excitement': 0.5
        })
        
        # Add trades to history
        self.trades.extend(executed_trades)
        
        # Add journal entry
        self.add_journal_entry(
            f"Executed {len(executed_trades)} trades based on {len(signals)} signals",
            entry_type="trade_execution",
            emotional_state={'confidence': 0.6, 'satisfaction': 0.7},
            metadata={"signals": len(signals), "trades": len(executed_trades)}
        )
        
        return executed_trades
    
    def analyze_performance(self):
        """Analyze trading performance with emotional insights and ML metrics."""
        if not self.trades:
            self.logger.info("No trades to analyze")
            return {}
            
        self.logger.info(f"Analyzing performance of {len(self.trades)} trades with advanced analytics")
        
        # Use enhanced performance analytics with emotional tracking
        analytics = EnhancedPerformanceAnalytics(self.trades, self.emotional_tracker)
        summary = analytics.summary()
        
        # Generate a comprehensive performance report
        report = analytics.generate_performance_report()
        
        # Add ML model metrics if advanced ML is enabled
        if self.use_advanced_ml:
            ml_metrics = self._get_ml_model_metrics()
            report['ml_metrics'] = ml_metrics
            
            # Log ML metrics
            self.logger.info("ML Model Performance Metrics:")
            if 'transformer' in ml_metrics:
                t_metrics = ml_metrics['transformer']
                self.logger.info(f"  Transformer: RMSE={t_metrics.get('rmse', 0):.4f}, Direction Accuracy={t_metrics.get('direction_accuracy', 0):.2f}%")
            
            if 'rl_agent' in ml_metrics:
                rl_metrics = ml_metrics['rl_agent']
                self.logger.info(f"  PPO Agent: Sharpe={rl_metrics.get('sharpe', 0):.2f}, Mean Reward={rl_metrics.get('mean_reward', 0):.2f}")
            
            if 'market_regime' in ml_metrics:
                regime_data = ml_metrics['market_regime']
                self.logger.info(f"  Market Regime: {regime_data.get('current', 'Unknown')}, Confidence={regime_data.get('confidence', 0)*100:.1f}%")
        
        # Log key performance metrics
        self.logger.info(f"Performance summary: {len(self.trades)} trades, {summary['win_rate']:.2%} win rate")
        if 'emotional_impact' in summary:
            self.logger.info("Emotional impact detected in trading performance")
            for emotion, data in summary['emotional_impact'].items():
                self.logger.info(f"  {emotion}: correlation {data.get('correlation', 'N/A')}")
        
        return report
        
    def _get_ml_model_metrics(self):
        """Get performance metrics from ML models."""
        metrics = {}
        
        # Get transformer model metrics
        try:
            transformer_metrics = {
                'rmse': 0.0023,  # Simulated metrics
                'mae': 0.0018,
                'direction_accuracy': 68.5,
                'forecast_horizon': 5
            }
            metrics['transformer'] = transformer_metrics
        except Exception as e:
            self.logger.error(f"Error getting transformer metrics: {e}")
        
        # Get PPO agent metrics
        try:
            rl_metrics = {
                'sharpe': 1.85,  # Simulated metrics
                'mean_reward': 0.0245,
                'policy_loss': 0.0078,
                'value_loss': 0.0032,
                'max_drawdown': 0.0325
            }
            metrics['rl_agent'] = rl_metrics
        except Exception as e:
            self.logger.error(f"Error getting RL agent metrics: {e}")
        
        # Get market regime metrics
        try:
            regime_metrics = {
                'current': 'Trending',  # Simulated metrics
                'confidence': 0.87,
                'transition_probability': 0.12
            }
            metrics['market_regime'] = regime_metrics
        except Exception as e:
            self.logger.error(f"Error getting market regime metrics: {e}")
            
        # Overall prediction accuracy
        metrics['prediction_accuracy'] = 72.5  # Simulated overall accuracy
        
        return metrics
    
    def run_trading_session(self, bars=200):
        """Run a complete trading session."""
        self.logger.info(f"Starting trading session for {self.symbol}")
        
        # Analyze market
        signals = self.analyze_market(bars)
        if not signals:
            self.logger.info("No trading signals generated")
            return None
        
        # Execute signals
        trades = self.execute_signals(signals)
        if not trades:
            self.logger.info("No trades executed")
            return None
        
        # Analyze performance
        performance = self.analyze_performance()
        
        self.logger.info("Trading session completed")
        return performance


def main():
    """Run the example demonstrating advanced ML capabilities."""
    # Create logs directory if it doesn't exist
    os.makedirs("logs", exist_ok=True)
    
    try:
        # Run with and without advanced ML for comparison
        for use_advanced_ml in [False, True]:
            logger.info(f"\n{'='*80}\nRunning trading system with advanced ML: {use_advanced_ml}\n{'='*80}")
            
            # Initialize custom trading system
            trading_system = CustomTradingSystem(
                symbol="EURUSD", 
                timeframe="M15",
                use_advanced_ml=use_advanced_ml
            )
            
            # Record initial emotional state
            trading_system.record_emotional_state({
                'confidence': 0.8,
                'fear': 0.2,
                'excitement': 0.7,
                'focus': 0.9
            })
            
            # Add journal entry
            trading_system.add_journal_entry(
                f"Starting trading session with {'advanced' if use_advanced_ml else 'standard'} ML models",
                entry_type="session_start",
                emotional_state={'confidence': 0.8, 'focus': 0.9}
            )
            
            # Run trading session
            performance = trading_system.run_trading_session(bars=300)
            
            if performance:
                logger.info("Trading session completed successfully")
                logger.info(f"Win rate: {performance.get('summary', {}).get('win_rate', 'N/A')}")
                logger.info(f"Net profit: {performance.get('summary', {}).get('net_profit', 'N/A')}")
                
                # Display ML metrics if available
                if 'ml_metrics' in performance:
                    ml_metrics = performance['ml_metrics']
                    logger.info("\nML Model Performance Summary:")
                    
                    if 'prediction_accuracy' in ml_metrics:
                        logger.info(f"Overall prediction accuracy: {ml_metrics['prediction_accuracy']}%")
                    
                    if 'transformer' in ml_metrics:
                        t_metrics = ml_metrics['transformer']
                        logger.info("\nTransformer Model Metrics:")
                        logger.info(f"  RMSE: {t_metrics.get('rmse', 0):.4f}")
                        logger.info(f"  MAE: {t_metrics.get('mae', 0):.4f}")
                        logger.info(f"  Direction Accuracy: {t_metrics.get('direction_accuracy', 0):.2f}%")
                    
                    if 'rl_agent' in ml_metrics:
                        rl_metrics = ml_metrics['rl_agent']
                        logger.info("\nPPO Agent Metrics:")
                        logger.info(f"  Sharpe Ratio: {rl_metrics.get('sharpe', 0):.2f}")
                        logger.info(f"  Mean Reward: {rl_metrics.get('mean_reward', 0):.4f}")
                        logger.info(f"  Max Drawdown: {rl_metrics.get('max_drawdown', 0):.4f}")
                
                # Get emotional recommendations
                recommendations = performance.get('recommendations', [])
                if recommendations:
                    logger.info("\nEmotional recommendations:")
                    for rec in recommendations:
                        logger.info(f"  - {rec}")
            else:
                logger.info("Trading session completed with no trades")
            
            logger.info(f"\n{'='*80}\n")
            time.sleep(1)  # Brief pause between runs
        
    except Exception as e:
        logger.exception(f"Error in trading system: {e}")


if __name__ == "__main__":
    main()
