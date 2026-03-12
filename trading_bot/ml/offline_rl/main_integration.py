"""
Main.py Integration for AlphaAlgo Offline RL System

Provides seamless integration with main.py for autonomous trading.
"""

import logging
import numpy as np
import pandas as pd
from typing import Any, Dict, List, Optional
import asyncio
from datetime import datetime

logger = logging.getLogger(__name__)

from .alphaalgo_autonomous_system import AlphaAlgoAutonomousSystem, create_alphaalgo_system
from .state_builder import MarketStateBuilder, ActionMapper, RewardCalculator


class AlphaAlgoTradingIntegration:
    """
    Integration layer between AlphaAlgo Offline RL and main trading system.
    
    Handles:
    - Market data conversion to RL states
    - Action mapping to trading orders
    - Reward calculation from trade results
    - Autonomous learning loop
    """
    
    def __init__(
        self,
        mt5_interface,
        symbol: str = "EURUSD",
        config: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize AlphaAlgo trading integration.
        
        Args:
            mt5_interface: MT5 interface for market data and execution
            symbol: Trading symbol
            config: Configuration dictionary
        """
        self.mt5 = mt5_interface
        self.symbol = symbol
        self.config = config or {}
        
        # Initialize components
        self.state_builder = MarketStateBuilder(
            lookback_window=self.config.get('lookback_window', 50),
            normalize=True
        )
        
        self.action_mapper = ActionMapper(
            action_space=self.config.get('action_space', 'simple')
        )
        
        self.reward_calculator = RewardCalculator(
            reward_type=self.config.get('reward_type', 'sharpe')
        )
        
        # Initialize autonomous system
        state_dim = self.state_builder.get_state_dim()
        action_dim = self.action_mapper.get_action_dim()
        
        self.autonomous_system = create_alphaalgo_system(
            state_dim=state_dim,
            action_dim=action_dim,
            config=self.config.get('autonomous_config', {})
        )
        
        # Trading state
        self.current_position = 0.0
        self.last_state = None
        self.last_action = None
        self.entry_price = None
        self.trade_history = []
        
        logger.info(f"AlphaAlgo integration initialized for {symbol}")
        logger.info(f"State dim: {state_dim}, Action dim: {action_dim}")
    
    async def start(self):
        """Start the autonomous system."""
        self.autonomous_system.start()
        logger.info("✅ AlphaAlgo autonomous system started")
    
    def stop(self):
        """Stop the autonomous system."""
        self.autonomous_system.stop()
        logger.info("✅ AlphaAlgo autonomous system stopped")
    
    async def get_trading_signal(
        self,
        market_data: pd.DataFrame,
        account_info: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """
        Get trading signal from AlphaAlgo.
        
        Args:
            market_data: Current market data with OHLCV and indicators
            account_info: Account information
        
        Returns:
            Trading signal dictionary
        """
        try:
            # Build state
            state = self.state_builder.build_state(
                market_data=market_data,
                current_position=self.current_position,
                account_info=account_info
            )
            
            # Get action from autonomous system
            action_idx = self.autonomous_system.get_action(state)
            
            # Map to trading action
            trading_action = self.action_mapper.map_action(action_idx)
            
            # Store for experience collection
            self.last_state = state
            self.last_action = action_idx
            
            # Create signal
            signal = {
                'type': trading_action['type'],
                'size': trading_action['size'],
                'symbol': self.symbol,
                'timestamp': datetime.now(),
                'state': state,
                'action': action_idx,
                'confidence': 1.0  # Could be enhanced with policy uncertainty
            }
            
            logger.debug(f"Signal generated: {signal['type']} size={signal['size']:.2f}")
            
            return signal
            
        except Exception as e:
            logger.error(f"Error generating signal: {e}", exc_info=True)
            return {'type': 'hold', 'size': 0.0}
    
    async def process_trade_result(
        self,
        trade_result: Dict[str, Any],
        market_data: pd.DataFrame
    ):
        """
        Process trade result and collect experience.
        
        Args:
            trade_result: Trade execution result
            market_data: Current market data
        """
        try:
            if self.last_state is None or self.last_action is None:
                return
            
            # Calculate PnL
            pnl = trade_result.get('pnl', 0.0)
            
            # Calculate transaction cost
            transaction_cost = trade_result.get('commission', 0.0) + trade_result.get('swap', 0.0)
            
            # Calculate reward
            position_change = abs(trade_result.get('position_change', 0.0))
            reward = self.reward_calculator.calculate_reward(
                pnl=pnl,
                position_change=position_change,
                transaction_cost=transaction_cost
            )
            
            # Build next state
            next_state = self.state_builder.build_state(
                market_data=market_data,
                current_position=self.current_position,
                account_info=trade_result.get('account_info')
            )
            
            # Check if episode done (e.g., large loss, end of day)
            done = (
                abs(pnl) > self.config.get('max_loss_per_trade', 1000) or
                trade_result.get('forced_close', False)
            )
            
            # Collect experience
            self.autonomous_system.collect_trade_experience(
                state=self.last_state,
                action=self.last_action,
                reward=reward,
                next_state=next_state,
                done=done,
                info=trade_result
            )
            
            # Update position
            self.current_position = trade_result.get('current_position', 0.0)
            
            # Store trade history
            self.trade_history.append({
                'timestamp': datetime.now(),
                'pnl': pnl,
                'reward': reward,
                'action': self.last_action,
                'done': done
            })
            
            logger.debug(f"Experience collected: PnL={pnl:.2f}, Reward={reward:.4f}, Done={done}")
            
        except Exception as e:
            logger.error(f"Error processing trade result: {e}", exc_info=True)
    
    def get_status(self) -> Dict[str, Any]:
        """
        Get current status.
        
        Returns:
            Status dictionary
        """
        system_status = self.autonomous_system.get_status()
        
        return {
            'symbol': self.symbol,
            'current_position': self.current_position,
            'trades_count': len(self.trade_history),
            'system_status': system_status,
            'last_update': datetime.now().isoformat()
        }
    
    def force_training(self) -> bool:
        """
        Force immediate training cycle.
        
        Returns:
            True if training successful
        """
        return self.autonomous_system.force_training()
    
    def export_metrics(self) -> pd.DataFrame:
        """
        Export metrics.
        
        Returns:
            Metrics DataFrame
        """
        return self.autonomous_system.export_metrics()


async def create_alphaalgo_trader(
    mt5_interface,
    symbol: str = "EURUSD",
    config: Optional[Dict[str, Any]] = None
) -> AlphaAlgoTradingIntegration:
    """
    Create and start AlphaAlgo trader.
    
    Args:
        mt5_interface: MT5 interface
        symbol: Trading symbol
        config: Configuration
    
    Returns:
        AlphaAlgo trading integration
    """
    trader = AlphaAlgoTradingIntegration(
        mt5_interface=mt5_interface,
        symbol=symbol,
        config=config
    )
    
    await trader.start()
    
    return trader


# Example usage in main.py:
"""
# In main.py, add this to argument parser:
parser.add_argument(
    "--alphaalgo-offline-rl",
    action="store_true",
    help="Enable AlphaAlgo autonomous Offline RL system.",
    default=False,
)

# In main() function:
if args.alphaalgo_offline_rl:
    from trading_bot.ml.offline_rl import create_alphaalgo_trader
import numpy
import pandas
    
    # Create AlphaAlgo trader
    alphaalgo_config = {
        'lookback_window': 50,
        'action_space': 'simple',  # 'simple', 'extended', or 'continuous'
        'reward_type': 'sharpe',  # 'simple', 'sharpe', or 'sortino'
        'autonomous_config': {
            'buffer_size': 100000,
            'min_buffer_size': 10000,
            'training_interval_hours': 24,
            'training_epochs': 50,
            'safety_thresholds': {
                'min_mean_return': 0.0,
                'max_cvar': -0.15,
                'min_sharpe': 0.3,
                'max_drawdown': -0.25
            }
        }
    }
    
    alphaalgo_trader = await create_alphaalgo_trader(
        mt5_interface=mt5i,
        symbol=args.symbol,
        config=alphaalgo_config
    )
    
    logger.info("AlphaAlgo Offline RL system activated")
    
    # In trading loop:
    # Get signal
    signal = await alphaalgo_trader.get_trading_signal(
        market_data=market_df,
        account_info=account_info
    )
    
    # Execute trade based on signal
    if signal['type'] != 'hold':
        # Execute trade...
        trade_result = await execute_trade(signal)
        
        # Process result
        await alphaalgo_trader.process_trade_result(
            trade_result=trade_result,
            market_data=market_df
        )
    
    # Get status
    status = alphaalgo_trader.get_status()
    logger.info(f"AlphaAlgo Status: {status}")
"""


if __name__ == "__main__":
    # Demo
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    print("\n" + "="*80)
    logger.info("ALPHAALGO MAIN INTEGRATION DEMO")
    print("="*80)
    
    # Mock MT5 interface
    class MockMT5:
        pass
    
    async def demo():
        # Create trader
        trader = AlphaAlgoTradingIntegration(
            mt5_interface=MockMT5(),
            symbol="EURUSD"
        )
        
        await trader.start()
        
        # Simulate trading
        for i in range(100):
            # Create mock market data
            market_data = pd.DataFrame({
                'close': np.random.randn(100).cumsum() + 100,
                'volume': np.random.randint(1000, 10000, 100),
                'rsi': np.random.uniform(30, 70, 100),
                'macd': np.random.randn(100),
                'atr': np.random.uniform(0.5, 2.0, 100)
            })
            
            # Get signal
            signal = await trader.get_trading_signal(market_data)
            
            # Simulate trade result
            if signal['type'] != 'hold':
                trade_result = {
                    'pnl': np.random.randn() * 10,
                    'commission': 0.5,
                    'swap': 0.1,
                    'position_change': signal['size'],
                    'current_position': signal['size'] if signal['type'] == 'buy' else -signal['size'],
                    'forced_close': False
                }
                
                await trader.process_trade_result(trade_result, market_data)
        
        # Get status
        status = trader.get_status()
        logger.info("\nFinal Status:")
        for key, value in status.items():
            logger.info(f"  {key}: {value}")
        
        # Stop
        trader.stop()
    
    asyncio.run(demo())
    
    print("\n" + "="*80)
    logger.info("DEMO COMPLETE!")
    print("="*80)
