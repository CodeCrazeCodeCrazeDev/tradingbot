"""
AlphaAlgo Offline RL Integration

Integrates continuous learning system with AlphaAlgo trading bot.

This module:
1. Connects to live trading data stream
2. Feeds data to continuous learning orchestrator
3. Deploys best policies automatically
4. Monitors performance and rolls back if needed
5. Logs all actions for audit trail
"""

import os
import sys
import logging
import numpy as np
from typing import Any, Dict, List, Optional
import time
from datetime import datetime, timedelta
import threading
import signal

# Add trading_bot to path
sys.path.insert(0, os.path.dirname(__file__))

from trading_bot.ml.offline_rl import ContinuousLearningOrchestrator

logger = logging.getLogger(__name__)


class AlphaAlgoOfflineRLIntegration:
    """
    Integration layer between AlphaAlgo and Offline RL system.
    
    Handles:
    - State extraction from market data
    - Action mapping to trading decisions
    - Reward calculation from trade outcomes
    - Automatic training scheduling
    - Performance monitoring
    """
    
    def __init__(
        self,
        state_features: List[str],
        action_space: List[str] = ['hold', 'buy', 'sell'],
        training_interval_hours: int = 24,
        min_buffer_size: int = 10000,
        buffer_size: int = 100000,
        safety_thresholds: Optional[Dict[str, float]] = None,
        log_dir: str = "logs/alphaalgo_offline_rl"
    ):
        """
        Initialize integration.
        
        Args:
            state_features: List of feature names for state representation
            action_space: List of possible actions
            training_interval_hours: Hours between training cycles
            min_buffer_size: Minimum data before first training
            buffer_size: Maximum buffer size
            safety_thresholds: Safety criteria for policy deployment
            log_dir: Directory for logs
        """
        self.state_features = state_features
        self.action_space = action_space
        self.training_interval_hours = training_interval_hours
        
        state_dim = len(state_features)
        action_dim = len(action_space)
        
        # Initialize orchestrator
        self.orchestrator = ContinuousLearningOrchestrator(
            state_dim=state_dim,
            action_dim=action_dim,
            buffer_size=buffer_size,
            min_buffer_size=min_buffer_size,
            training_interval_hours=training_interval_hours,
            evaluation_window=100,
            safety_thresholds=safety_thresholds,
            log_dir=log_dir
        )
        
        # Training scheduler
        self.last_training_time = datetime.now()
        self.training_thread = None
        self.is_running = False
        
        # Current trade tracking
        self.current_position = None
        self.entry_price = None
        self.entry_time = None
        
        # Statistics
        self.total_trades = 0
        self.successful_trades = 0
        self.total_pnl = 0.0
        
        logger.info("="*80)
        logger.info("ALPHAALGO OFFLINE RL INTEGRATION INITIALIZED")
        logger.info("="*80)
        logger.info(f"State features: {state_features}")
        logger.info(f"Action space: {action_space}")
        logger.info(f"Training interval: {training_interval_hours}h")
        logger.info("="*80)
    
    def extract_state(self, market_data: Dict[str, Any]) -> np.ndarray:
        """
        Extract state vector from market data.
        
        Args:
            market_data: Dictionary of market data
        
        Returns:
            State vector
        """
        state = []
        
        for feature in self.state_features:
            value = market_data.get(feature, 0.0)
            
            # Normalize if needed
            if isinstance(value, (int, float)):
                state.append(float(value))
            else:
                state.append(0.0)
        
        return np.array(state, dtype=np.float32)
    
    def map_action_to_trading_decision(self, action: int) -> str:
        """
        Map action index to trading decision.
        
        Args:
            action: Action index
        
        Returns:
            Trading decision string
        """
        if 0 <= action < len(self.action_space):
            return self.action_space[action]
        else:
            logger.warning(f"Invalid action {action}, defaulting to 'hold'")
            return 'hold'
    
    def calculate_reward(
        self,
        action: str,
        current_price: float,
        next_price: float,
        position_closed: bool = False
    ) -> float:
        """
        Calculate reward for action.
        
        Args:
            action: Action taken
            current_price: Price when action taken
            next_price: Price at next step
            position_closed: Whether position was closed
        
        Returns:
            Reward value
        """
        reward = 0.0
        
        if action == 'buy':
            if self.current_position is None:
                # Open long position
                self.current_position = 'long'
                self.entry_price = current_price
                self.entry_time = datetime.now()
                reward = -0.001  # Small penalty for transaction cost
            
        elif action == 'sell':
            if self.current_position is None:
                # Open short position
                self.current_position = 'short'
                self.entry_price = current_price
                self.entry_time = datetime.now()
                reward = -0.001  # Small penalty for transaction cost
            
            elif self.current_position == 'long':
                # Close long position
                pnl = (current_price - self.entry_price) / self.entry_price
                reward = pnl
                self._record_trade(pnl)
                self.current_position = None
                self.entry_price = None
        
        elif action == 'hold':
            # Holding position
            if self.current_position == 'long':
                # Unrealized PnL
                unrealized_pnl = (next_price - self.entry_price) / self.entry_price
                reward = unrealized_pnl * 0.1  # Small reward for unrealized gains
            
            elif self.current_position == 'short':
                unrealized_pnl = (self.entry_price - next_price) / self.entry_price
                reward = unrealized_pnl * 0.1
        
        # Penalty for holding too long (>24 hours)
        if self.current_position and self.entry_time:
            holding_time = (datetime.now() - self.entry_time).total_seconds() / 3600
            if holding_time > 24:
                reward -= 0.01 * (holding_time - 24)
        
        return reward
    
    def _record_trade(self, pnl: float):
        """Record completed trade."""
        self.total_trades += 1
        self.total_pnl += pnl
        
        if pnl > 0:
            self.successful_trades += 1
        
        win_rate = self.successful_trades / self.total_trades if self.total_trades > 0 else 0.0
        
        logger.info(f"📊 Trade #{self.total_trades}: PnL={pnl:+.4f}, Total PnL={self.total_pnl:+.4f}, Win Rate={win_rate:.2%}")
    
    def process_market_update(
        self,
        market_data: Dict[str, Any],
        execute_action: bool = True
    ) -> Optional[str]:
        """
        Process market update and optionally execute action.
        
        Args:
            market_data: Current market data
            execute_action: Whether to execute the action
        
        Returns:
            Action to take (if execute_action=True)
        """
        # Extract state
        state = self.extract_state(market_data)
        
        # Get action from deployed policy
        action_idx = self.orchestrator.get_action(state)
        action = self.map_action_to_trading_decision(action_idx)
        
        # Calculate reward (for previous action)
        current_price = market_data.get('close', 0.0)
        next_price = market_data.get('close', 0.0)  # Will be updated on next tick
        
        reward = self.calculate_reward(action, current_price, next_price)
        
        # Collect experience
        next_state = state  # Will be updated on next tick
        done = False  # Episode done flag
        
        self.orchestrator.collect_experience(
            state=state,
            action=action_idx,
            reward=reward,
            next_state=next_state,
            done=done
        )
        
        # Monitor performance
        if not self.orchestrator.monitor_performance(reward):
            logger.error("⚠️ PERFORMANCE DEGRADATION DETECTED - INITIATING ROLLBACK")
            self.orchestrator.rollback_policy()
        
        # Check if training needed
        self._check_training_schedule()
        
        if execute_action:
            return action
        else:
            return None
    
    def _check_training_schedule(self):
        """Check if training cycle should run."""
        time_since_last_training = datetime.now() - self.last_training_time
        
        if time_since_last_training.total_seconds() / 3600 >= self.training_interval_hours:
            if self.orchestrator.can_train():
                logger.info("⏰ Training interval reached - scheduling training cycle")
                self._schedule_training()
            else:
                logger.info("⏰ Training interval reached but insufficient data")
    
    def _schedule_training(self):
        """Schedule training in background thread."""
        if self.training_thread and self.training_thread.is_alive():
            logger.warning("Training already in progress")
            return
        
        def training_worker():
            try:
                self.orchestrator.run_training_cycle(n_epochs=50)
                self.last_training_time = datetime.now()
            except Exception as e:
                logger.error(f"Training cycle failed: {e}", exc_info=True)
        
        self.training_thread = threading.Thread(target=training_worker, daemon=True)
        self.training_thread.start()
        
        logger.info("🚀 Training cycle started in background")
    
    def force_training_cycle(self, n_epochs: int = 50):
        """Force immediate training cycle."""
        logger.info("🔧 Forcing training cycle...")
        
        if not self.orchestrator.can_train():
            logger.error("Cannot train: insufficient data")
            return
        
        self.orchestrator.run_training_cycle(n_epochs=n_epochs)
        self.last_training_time = datetime.now()
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get system statistics."""
        win_rate = self.successful_trades / self.total_trades if self.total_trades > 0 else 0.0
        
        return {
            'total_trades': self.total_trades,
            'successful_trades': self.successful_trades,
            'win_rate': win_rate,
            'total_pnl': self.total_pnl,
            'buffer_size': len(self.orchestrator.data_buffer['states']),
            'deployed_policy': self.orchestrator.deployed_policy_name,
            'deployment_time': self.orchestrator.deployment_timestamp.isoformat() if self.orchestrator.deployment_timestamp else None,
            'last_training_time': self.last_training_time.isoformat(),
            'current_position': self.current_position
        }
    
    def save_state(self):
        """Save integration state."""
        self.orchestrator.save_state()
        
        # Save integration-specific state
        state = {
            'total_trades': self.total_trades,
            'successful_trades': self.successful_trades,
            'total_pnl': self.total_pnl,
            'last_training_time': self.last_training_time.isoformat(),
            'current_position': self.current_position,
            'entry_price': self.entry_price,
            'entry_time': self.entry_time.isoformat() if self.entry_time else None
        }
        
        import json
        with open(self.orchestrator.log_dir / "integration_state.json", 'w') as f:
            json.dump(state, f, indent=2)
        
        logger.info("💾 Integration state saved")
    
    def shutdown(self):
        """Graceful shutdown."""
        logger.info("🛑 Shutting down AlphaAlgo Offline RL Integration...")
        
        self.is_running = False
        
        # Wait for training thread
        if self.training_thread and self.training_thread.is_alive():
            logger.info("Waiting for training to complete...")
            self.training_thread.join(timeout=60)
        
        # Save state
        self.save_state()
        
        logger.info("✅ Shutdown complete")


def main():
    """Main entry point for standalone testing."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    print("\n" + "="*80)
    print("ALPHAALGO OFFLINE RL INTEGRATION - STANDALONE TEST")
    print("="*80)
    
    # Define state features
    state_features = [
        'close', 'open', 'high', 'low', 'volume',
        'rsi', 'macd', 'macd_signal', 'bb_upper', 'bb_lower',
        'atr', 'adx', 'cci', 'stoch_k', 'stoch_d',
        'obv', 'mfi', 'willr', 'roc', 'trix'
    ]
    
    # Initialize integration
    integration = AlphaAlgoOfflineRLIntegration(
        state_features=state_features,
        action_space=['hold', 'buy', 'sell'],
        training_interval_hours=1,  # Short interval for testing
        min_buffer_size=500,
        buffer_size=10000
    )
    
    # Simulate market data stream
    print("\nSimulating market data stream...")
    
    for i in range(1000):
        # Generate fake market data
        market_data = {
            'close': 1.0 + np.random.randn() * 0.01,
            'open': 1.0 + np.random.randn() * 0.01,
            'high': 1.01 + np.random.randn() * 0.01,
            'low': 0.99 + np.random.randn() * 0.01,
            'volume': 1000 + np.random.randn() * 100,
            'rsi': 50 + np.random.randn() * 10,
            'macd': np.random.randn() * 0.001,
            'macd_signal': np.random.randn() * 0.001,
            'bb_upper': 1.02,
            'bb_lower': 0.98,
            'atr': 0.01,
            'adx': 25 + np.random.randn() * 5,
            'cci': np.random.randn() * 50,
            'stoch_k': 50 + np.random.randn() * 20,
            'stoch_d': 50 + np.random.randn() * 20,
            'obv': 10000 + np.random.randn() * 1000,
            'mfi': 50 + np.random.randn() * 10,
            'willr': -50 + np.random.randn() * 20,
            'roc': np.random.randn() * 0.01,
            'trix': np.random.randn() * 0.001
        }
        
        # Process update
        action = integration.process_market_update(market_data, execute_action=True)
        
        if i % 100 == 0:
            stats = integration.get_statistics()
            print(f"\n📊 Step {i}: Action={action}, Buffer={stats['buffer_size']}, Trades={stats['total_trades']}")
    
    # Force training cycle
    print("\nForcing training cycle...")
    integration.force_training_cycle(n_epochs=10)
    
    # Get final statistics
    stats = integration.get_statistics()
    
    print("\n" + "="*80)
    print("FINAL STATISTICS")
    print("="*80)
    print(f"Total Trades: {stats['total_trades']}")
    print(f"Win Rate: {stats['win_rate']:.2%}")
    print(f"Total PnL: {stats['total_pnl']:+.4f}")
    print(f"Buffer Size: {stats['buffer_size']}")
    print(f"Deployed Policy: {stats['deployed_policy']}")
    print("="*80)
    
    # Shutdown
    integration.shutdown()
    
    print("\n✅ TEST COMPLETE!")


if __name__ == "__main__":
    main()
