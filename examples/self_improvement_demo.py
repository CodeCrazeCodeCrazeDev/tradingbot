"""Self-Improvement System Demo.

from typing import Tuple
from typing import Set
This script demonstrates the self-improvement capabilities of the trading bot,
showing how it can learn from various sources and rewrite its own code.
"""

import os
import sys
import asyncio
import logging
import json
from datetime import datetime
from pathlib import Path

# Add parent directory to path to import trading_bot
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from trading_bot.adaptive_systems.knowledge_acquisition.knowledge_base import KnowledgeBase, KnowledgeItem, KnowledgeType, KnowledgeStatus
from trading_bot.adaptive_systems.knowledge_acquisition.book_knowledge import BookKnowledgeAcquisition, BookSource
from trading_bot.adaptive_systems.knowledge_acquisition.human_knowledge import HumanKnowledgeAcquisition, FeedbackSource
from trading_bot.adaptive_systems.knowledge_acquisition.ai_knowledge import AIKnowledgeAcquisition, AISource
from trading_bot.adaptive_systems.knowledge_acquisition.algorithm_knowledge import AlgorithmKnowledgeAcquisition, AlgorithmSource

from trading_bot.adaptive_systems.code_generation.code_generator import CodeGenerator, GeneratedCode, CodeGenerationConfig
from trading_bot.adaptive_systems.code_generation.code_validator import CodeValidator, ValidationLevel
from trading_bot.adaptive_systems.code_generation.code_modifier import CodeModifier, ModificationType
from trading_bot.adaptive_systems.code_generation.safety_checker import SafetyChecker, SafetyLevel
from trading_bot.adaptive_systems.code_generation.code_repository import CodeRepository
from trading_bot.adaptive_systems.code_generation.self_modification_engine import SelfModificationEngine, ModificationTask, ModificationStatus

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('self_improvement_demo.log')
    ]
)

logger = logging.getLogger(__name__)


class SelfImprovementDemo:
    """Demo for the self-improvement system."""
    
    def __init__(self, api_keys_path: str = None):
        """Initialize the demo.
        
        Args:
            api_keys_path: Path to API keys file
        """
        self.api_keys = self._load_api_keys(api_keys_path)
        
        # Initialize components
        self.knowledge_base = KnowledgeBase("demo_knowledge_base.db")
        self.engine = SelfModificationEngine(self.knowledge_base, self.api_keys)
        
        # Set approval callback
        self.engine.set_approval_callback(self._approval_callback)
        
        # Demo files directory
        self.demo_dir = os.path.join(os.path.dirname(__file__), "demo_files")
        os.makedirs(self.demo_dir, exist_ok=True)
        
        logger.info("Self-improvement demo initialized")
    
    def _load_api_keys(self, api_keys_path: str) -> dict:
        """Load API keys from file.
        
        Args:
            api_keys_path: Path to API keys file
            
        Returns:
            Dictionary of API keys
        """
        if not api_keys_path or not os.path.exists(api_keys_path):
            logger.warning("API keys file not found, using empty keys")
            return {}
        
        try:
            with open(api_keys_path, 'r') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Error loading API keys: {e}")
            return {}
    
    async def run_demo(self):
        """Run the self-improvement demo."""
        logger.info("Starting self-improvement demo")
        
        # Step 1: Add knowledge from various sources
        await self._add_knowledge()
        
        # Step 2: Start the self-modification engine
        self.engine.start_processing()
        
        # Step 3: Create a simple trading strategy file to improve
        strategy_file = self._create_simple_strategy()
        
        # Step 4: Create a task to improve the strategy
        task_id = self.engine.create_task(
            target_file=strategy_file,
            purpose="Improve the simple trading strategy with advanced features",
            knowledge_query="trading strategy improvement",
            knowledge_tags=["trading", "strategy", "improvement"],
            metadata={"modification_type": "update"}
        )
        
        logger.info(f"Created improvement task: {task_id}")
        
        # Step 5: Wait for task to complete or require approval
        await self._wait_for_task(task_id)
        
        # Step 6: Create a new strategy from scratch
        new_strategy_file = os.path.join(self.demo_dir, "advanced_strategy.py")
        
        task_id = self.engine.create_task(
            target_file=new_strategy_file,
            purpose="Create an advanced trading strategy with machine learning",
            knowledge_query="machine learning trading strategy",
            knowledge_tags=["machine learning", "trading", "strategy"],
            metadata={"modification_type": "replace"}
        )
        
        logger.info(f"Created new strategy task: {task_id}")
        
        # Step 7: Wait for task to complete or require approval
        await self._wait_for_task(task_id)
        
        # Step 8: Display statistics
        self._display_stats()
        
        # Step 9: Stop the engine
        self.engine.stop_processing()
        
        logger.info("Self-improvement demo completed")
    
    async def _add_knowledge(self):
        """Add knowledge from various sources."""
        logger.info("Adding knowledge from various sources")
        
        # Add book knowledge
        book_acquisition = BookKnowledgeAcquisition(self.knowledge_base)
        book_text = """
        # Advanced Trading Strategies
        
        ## Mean Reversion Strategy
        
        Mean reversion is a mathematical methodology sometimes used for stock investing, but it can be applied to other processes. In general terms the idea is that both a stock's high and low prices are temporary, and that a stock's price tends to have an average price over time.
        
        Mean reversion involves first identifying the trading range for a stock, and then computing the average price using analytical techniques taking into account considerations such as earnings, etc.
        
        When the current market price is less than the average price, the stock is considered attractive for purchase, with the expectation that the price will rise. When the current market price is above the average price, the market price is expected to fall. In other words, deviations from the average price are expected to revert to the average.
        
        ### Implementation
        
        A basic mean reversion strategy can be implemented as follows:
        
        1. Calculate the moving average of the price over a specific period (e.g., 20 days)
        2. Calculate the standard deviation of the price over the same period
        3. Buy when the price is 2 standard deviations below the moving average
        4. Sell when the price returns to the moving average
        
        ## Momentum Strategy
        
        Momentum investing is a system of buying stocks or other securities that have had high returns over the past three to twelve months, and selling those that have had poor returns over the same period.
        
        While no consensus exists about the validity of this strategy, economists have trouble reconciling this strategy with the efficient-market hypothesis.
        
        ### Implementation
        
        A basic momentum strategy can be implemented as follows:
        
        1. Calculate the return of each stock over the past N months (e.g., 6 months)
        2. Rank the stocks based on their returns
        3. Buy the top X% of stocks (e.g., top 10%)
        4. Rebalance the portfolio every M months (e.g., every month)
        
        ## Machine Learning in Trading
        
        Machine learning algorithms can be used to predict stock prices or market movements. Some common algorithms used in trading include:
        
        1. Linear Regression
        2. Random Forest
        3. Support Vector Machines
        4. Neural Networks
        5. Gradient Boosting Machines
        
        ### Implementation
        
        A basic machine learning trading strategy can be implemented as follows:
        
        1. Collect historical price data and relevant features
        2. Preprocess the data (normalization, feature engineering, etc.)
        3. Split the data into training and testing sets
        4. Train a machine learning model on the training data
        5. Evaluate the model on the testing data
        6. Use the model to make predictions for trading decisions
        """
        
        book_items = book_acquisition.extract_from_text(
            book_text,
            "Advanced Trading Strategies",
            BookSource.TRADING_BOOK,
            "Trading Expert"
        )
        
        book_ids = book_acquisition.store_knowledge_items(book_items)
        logger.info(f"Added {len(book_ids)} book knowledge items")
        
        # Add human knowledge
        human_acquisition = HumanKnowledgeAcquisition(self.knowledge_base)
        
        human_id = human_acquisition.record_expert_consultation(
            content="""
            When implementing a trading strategy, it's crucial to include proper risk management.
            Always use stop losses to limit potential losses, and never risk more than 1-2% of your
            capital on a single trade. Position sizing is also important - it should be based on
            the distance to your stop loss, not a fixed percentage of your portfolio.
            
            For machine learning strategies, be careful of overfitting. Always use cross-validation
            and ensure your model generalizes well to unseen data. Feature engineering is often more
            important than the choice of algorithm.
            """,
            expert_name="Risk Management Expert",
            expertise_area="Trading Risk Management",
            tags=["risk management", "position sizing", "stop loss", "machine learning"]
        )
        
        logger.info(f"Added human knowledge item: {human_id}")
        
        # Add algorithm knowledge
        algorithm_acquisition = AlgorithmKnowledgeAcquisition(self.knowledge_base)
        
        algorithm_code = """
        def calculate_bollinger_bands(prices, window=20, num_std=2):
            \"\"\"
            Calculate Bollinger Bands for a price series.
            
            Args:
                prices: List or array of prices
                window: Window size for moving average
                num_std: Number of standard deviations for bands
                
            Returns:
                Tuple of (middle_band, upper_band, lower_band)
            \"\"\"
            import numpy as np
            import pandas as pd
            
            # Convert to pandas Series if not already
            if not isinstance(prices, pd.Series):
                prices = pd.Series(prices)
            
            # Calculate middle band (simple moving average)
            middle_band = prices.rolling(window=window).mean()
            
            # Calculate standard deviation
            std = prices.rolling(window=window).std()
            
            # Calculate upper and lower bands
            upper_band = middle_band + (std * num_std)
            lower_band = middle_band - (std * num_std)
            
            return middle_band, upper_band, lower_band
        
        def bollinger_band_strategy(prices, window=20, num_std=2):
            \"\"\"
            Simple Bollinger Band trading strategy.
            
            Args:
                prices: List or array of prices
                window: Window size for moving average
                num_std: Number of standard deviations for bands
                
            Returns:
                List of signals (1 for buy, -1 for sell, 0 for hold)
            \"\"\"
            
            # Calculate Bollinger Bands
            middle_band, upper_band, lower_band = calculate_bollinger_bands(prices, window, num_std)
            
            # Generate signals
            signals = np.zeros(len(prices))
            
            for i in range(window, len(prices)):
                # Buy signal: price crosses below lower band
                if prices[i] < lower_band[i] and prices[i-1] >= lower_band[i-1]:
                    signals[i] = 1
                
                # Sell signal: price crosses above upper band
                elif prices[i] > upper_band[i] and prices[i-1] <= upper_band[i-1]:
                    signals[i] = -1
            
            return signals
        """
        
        algorithm_items = algorithm_acquisition.extract_from_code(
            algorithm_code,
            "Bollinger Band Strategy",
            AlgorithmSource.TRADING_STRATEGY,
            "Trading Algorithm Expert"
        )
        
        algorithm_ids = algorithm_acquisition.store_knowledge_items(algorithm_items)
        logger.info(f"Added {len(algorithm_ids)} algorithm knowledge items")
        
        # Add AI knowledge (simulated since we don't have API keys)
        ai_acquisition = AIKnowledgeAcquisition(self.knowledge_base, self.api_keys)
        
        # Simulate AI knowledge
        ai_knowledge = """
        # Machine Learning for Trading Strategy Improvement
        
        When improving a trading strategy with machine learning, consider the following approaches:
        
        1. **Feature Engineering**: Create meaningful features from raw price data, such as:
           - Technical indicators (RSI, MACD, Bollinger Bands)
           - Price patterns (support/resistance, chart patterns)
           - Volatility measures
           - Volume indicators
           - Market sentiment features
        
        2. **Model Selection**: Choose appropriate models based on your data and objectives:
           - Linear models for interpretability (Linear Regression, Logistic Regression)
           - Tree-based models for capturing non-linear relationships (Random Forest, XGBoost)
           - Neural networks for complex pattern recognition (LSTM, CNN)
        
        3. **Ensemble Methods**: Combine multiple models to improve performance:
           - Bagging (Random Forest)
           - Boosting (AdaBoost, XGBoost)
           - Stacking (combining predictions from multiple models)
        
        4. **Hyperparameter Optimization**: Use techniques like:
           - Grid search
           - Random search
           - Bayesian optimization
        
        5. **Validation Strategies**:
           - Walk-forward validation
           - Time-series cross-validation
           - Out-of-sample testing
        
        6. **Risk Management Integration**:
           - Position sizing based on prediction confidence
           - Dynamic stop-loss and take-profit levels
           - Portfolio optimization using predicted risk-reward
        
        Remember that machine learning models should complement traditional trading strategies, not replace them entirely. The best approaches often combine domain knowledge with data-driven insights.
        """
        
        # Create AI knowledge item directly
        ai_item = KnowledgeItem(
            id="ai_knowledge_1",
            title="Machine Learning for Trading Strategy Improvement",
            content=ai_knowledge,
            knowledge_type=KnowledgeType.AI,
            source="simulated_ai",
            tags=["machine learning", "trading", "strategy", "improvement"],
            confidence=0.9,
            acquisition_date=datetime.now(),
            status=KnowledgeStatus.VERIFIED,
            metadata={"model": "simulated"}
        )
        
        ai_id = self.knowledge_base.add_item(ai_item)
        logger.info(f"Added simulated AI knowledge item: {ai_id}")
    
    def _create_simple_strategy(self) -> str:
        """Create a simple trading strategy file.
        
        Returns:
            Path to the created file
        """
        file_path = os.path.join(self.demo_dir, "simple_strategy.py")
        
        code = """
        \"\"\"Simple Moving Average Crossover Strategy.

        This module implements a basic moving average crossover strategy.
        \"\"\"

from typing import List


        class SimpleMAStrategy:
            \"\"\"Simple Moving Average Crossover Strategy.\"\"\"
            
            def __init__(self, short_window=20, long_window=50):
                \"\"\"Initialize the strategy.
                
                Args:
                    short_window: Short moving average window
                    long_window: Long moving average window
                \"\"\"
                self.short_window = short_window
                self.long_window = long_window
            
            def generate_signals(self, prices):
                \"\"\"Generate trading signals.
                
                Args:
                    prices: DataFrame with price data
                    
                Returns:
                    DataFrame with signals
                \"\"\"
                signals = pd.DataFrame(index=prices.index)
                signals['signal'] = 0.0
                
                # Create short and long moving averages
                signals['short_ma'] = prices['close'].rolling(window=self.short_window).mean()
                signals['long_ma'] = prices['close'].rolling(window=self.long_window).mean()
                
                # Generate signals
                signals['signal'][self.long_window:] = np.where(
                    signals['short_ma'][self.long_window:] > signals['long_ma'][self.long_window:],
                    1.0, 0.0
                )
                
                # Generate trading orders
                signals['positions'] = signals['signal'].diff()
                
                return signals


        def backtest_strategy(prices, short_window=20, long_window=50):
            \"\"\"Backtest the strategy.
            
            Args:
                prices: DataFrame with price data
                short_window: Short moving average window
                long_window: Long moving average window
                
            Returns:
                DataFrame with backtest results
            \"\"\"
            strategy = SimpleMAStrategy(short_window, long_window)
            signals = strategy.generate_signals(prices)
            
            # Calculate returns
            signals['returns'] = prices['close'].pct_change()
            signals['strategy_returns'] = signals['positions'] * signals['returns']
            
            return signals
        """
        
        with open(file_path, 'w') as f:
            f.write(code.strip())
        
        logger.info(f"Created simple strategy file: {file_path}")
        return file_path
    
    def _approval_callback(self, task: ModificationTask):
        """Callback for task approval.
        
        Args:
            task: Task requiring approval
        """
        logger.info(f"Task {task.task_id} requires approval")
        logger.info(f"Purpose: {task.purpose}")
        logger.info(f"Target file: {task.target_file}")
        
        # In a real application, this would show a UI for approval
        # For the demo, we'll automatically approve after displaying info
        logger.info("Automatically approving task for demo purposes")
        self.engine.approve_task(task.task_id)
    
    async def _wait_for_task(self, task_id: str, timeout: int = 60):
        """Wait for a task to complete.
        
        Args:
            task_id: Task ID to wait for
            timeout: Timeout in seconds
        """
        start_time = datetime.now()
        
        while True:
            task = self.engine.get_task(task_id)
            
            if not task:
                logger.error(f"Task {task_id} not found")
                return
            
            if task.status in [ModificationStatus.COMPLETED, ModificationStatus.FAILED, ModificationStatus.REJECTED]:
                logger.info(f"Task {task_id} finished with status: {task.status.value}")
                
                if task.status == ModificationStatus.COMPLETED:
                    logger.info(f"Task completed successfully: {task.target_file}")
                    
                    # Display file content
                    try:
                        with open(task.target_file, 'r') as f:
                            content = f.read()
                        logger.info(f"File content preview (first 500 chars):\n{content[:500]}...")
                    except Exception as e:
                        logger.error(f"Error reading file: {e}")
                
                elif task.status == ModificationStatus.FAILED:
                    logger.error(f"Task failed: {task.error_message}")
                
                return
            
            # Check timeout
            elapsed = (datetime.now() - start_time).total_seconds()
            if elapsed > timeout:
                logger.warning(f"Timeout waiting for task {task_id}")
                return
            
            # Wait a bit before checking again
            await asyncio.sleep(2)
            logger.info(f"Waiting for task {task_id}, current status: {task.status.value}")
    
    def _display_stats(self):
        """Display statistics about the self-improvement system."""
        logger.info("Self-improvement system statistics:")
        
        # Knowledge base stats
        kb_stats = self.knowledge_base.get_stats()
        logger.info(f"Knowledge base: {kb_stats['total_items']} items")
        logger.info(f"By type: {kb_stats['by_type']}")
        logger.info(f"By status: {kb_stats['by_status']}")
        
        # Engine stats
        engine_stats = self.engine.get_stats()
        logger.info(f"Tasks: {engine_stats['total_tasks']}")
        logger.info(f"By status: {engine_stats['by_status']}")
        
        # Code repository stats
        repo_stats = self.engine.code_repository.get_stats()
        logger.info(f"Repository: {repo_stats['total_files']} files, {repo_stats['total_versions']} versions")


async def main():
    """Run the self-improvement demo."""
    # Path to API keys file (create this file with your API keys)
    api_keys_path = "api_keys.json"
    
    demo = SelfImprovementDemo(api_keys_path)
    await demo.run_demo()


if __name__ == "__main__":
    asyncio.run(main())
