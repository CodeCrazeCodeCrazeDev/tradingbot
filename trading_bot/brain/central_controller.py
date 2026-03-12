"""
Elite Trading Bot - Central Controller
Orchestrates the brain architecture and all trading bot components
"""

import asyncio
import logging
from typing import Dict, List, Any, Optional, Union, Tuple
from datetime import datetime, timedelta
import threading
import queue
import json
import os
import time

from trading_bot.brain.brain_architecture import EliteBrain, BrainDecision
from trading_bot.strategies.advanced_strategies import (
    AlternativeDataStrategy,
    MultiTimeframeRLStrategy,
    MarketRegimeStrategy
)
from trading_bot.dashboard.strategy_dashboard import StrategyDashboard
from trading_bot.execution.market_impact import MarketImpactModel

logger = logging.getLogger(__name__)


class CentralController:
    """
    Central Controller for Elite Trading Bot
    
    Orchestrates:
    - Brain Architecture (central intelligence)
    - Advanced Strategies
    - Execution System
    - Performance Tracking
    - System Health Monitoring
    """
    
    def __init__(self, config_path: str = 'config/elite_config.yaml'):
        # Load configuration
        self.config = self._load_config(config_path)
        
        # Initialize components
        self.brain = EliteBrain(self.config['brain_config'])
        self.dashboard = StrategyDashboard(self.config.get('dashboard_config'))
        
        # Initialize strategies
        self.strategies = {
            'AlternativeData': AlternativeDataStrategy(self.config.get('alternative_data_strategy_config')),
            'MultiTimeframeRL': MultiTimeframeRLStrategy(self.config.get('multi_timeframe_rl_strategy_config')),
            'MarketRegime': MarketRegimeStrategy(self.config.get('market_regime_strategy_config'))
        }
        
        # Market impact model for execution
        self.market_impact = MarketImpactModel(self.config.get('market_impact_config'))
        
        # Trading state
        self.active_symbols = self.config.get('symbols', ['AAPL', 'MSFT', 'GOOGL'])
        self.timeframes = self.config.get('timeframes', ['1m', '5m', '15m', '1h', '4h', '1d'])
        self.positions = {}
        self.orders = {}
        self.performance = {}
        
        # Control flags
        self.running = False
        self.paused = False
        self.emergency_stop = False
        
        # Execution queue
        self.execution_queue = queue.Queue()
        
        logger.info("Central Controller initialized")
    
    def _load_config(self, config_path: str) -> Dict[str, Any]:
        """Load configuration from file"""
        try:
            import yaml
            with open(config_path, 'r') as f:
                config = yaml.safe_load(f)
            logger.info(f"Configuration loaded from {config_path}")
            return config
        except Exception as e:
            logger.warning(f"Error loading configuration: {e}")
            return {}
    
    async def start(self):
        """Start the central controller"""
        if self.running:
            logger.warning("Central Controller is already running")
            return
        
        self.running = True
        self.paused = False
        self.emergency_stop = False
        
        # Start dashboard
        self.dashboard.start()
        
        # Start execution thread
        self.execution_thread = threading.Thread(target=self._execution_loop)
        self.execution_thread.daemon = True
        self.execution_thread.start()
        
        logger.info("Central Controller started")
        
        try:
            # Main control loop
            while self.running:
                if not self.paused and not self.emergency_stop:
                    # Process each symbol
                    for symbol in self.active_symbols:
                        await self._process_symbol(symbol)
                
                # Wait before next cycle
                await asyncio.sleep(self.config.get('cycle_interval_seconds', 60))
        
        except KeyboardInterrupt:
            logger.info("Central Controller stopped by user")
        except Exception as e:
            logger.error(f"Error in Central Controller: {e}")
        finally:
            await self.stop()
    
    async def _process_symbol(self, symbol: str):
        """Process a symbol"""
        try:
            # Get brain decision
            decision = await self.brain.make_decision(symbol, self.timeframes)
            
            if decision and decision.action != 'hold':
                # Queue for execution
                self.execution_queue.put(decision)
                
                # Log decision
                logger.info(f"Decision for {symbol}: {decision.action} {decision.size} @ {decision.price}")
                
                # Update dashboard
                self._update_dashboard(decision)
        except Exception as e:
            logger.error(f"Error processing symbol {symbol}: {e}")
    
    def _execution_loop(self):
        """Execution loop for processing decisions"""
        while self.running:
            try:
                try:
                    # Check if there's a decision to execute
                    decision = self.execution_queue.get(timeout=1)
                except queue.Empty:
                    time.sleep(0.1)
                    continue
                
                if self.emergency_stop:
                    logger.warning("Emergency stop active, skipping execution")
                    self.execution_queue.task_done()
                    continue
                
                # Execute decision
                self._execute_decision(decision)
                
                self.execution_queue.task_done()
            
            except Exception as e:
                logger.error(f"Error in execution loop: {e}")
                time.sleep(1)
    
    def _execute_decision(self, decision: BrainDecision):
        """Execute a trading decision"""
        try:
            symbol = decision.symbol
            action = decision.action
            size = decision.size
            price = decision.price
            
            # Check if we already have a position
            current_position = self.positions.get(symbol, 0)
            
            # Calculate order size
            if action == 'buy':
                if current_position < 0:  # Currently short
                    order_size = abs(current_position) + size  # Close short and open long
                else:
                    order_size = size
            elif action == 'sell':
                if current_position > 0:  # Currently long
                    order_size = current_position + size  # Close long and open short
                else:
                    order_size = size
            else:
                return
            
            # Estimate market impact
            impact = self.market_impact.estimate_market_impact(
                symbol=symbol,
                order_size=order_size,
                side=action,
                market_data={'price': price}
            )
            
            # Adjust execution if impact is too high
            if impact.get('market_impact_bps', 0) > 50:  # More than 50 bps impact
                # Use optimal execution strategy
                execution_plan = self.market_impact.optimize_execution(
                    symbol=symbol,
                    order_size=order_size,
                    side=action,
                    market_data={'price': price}
                )
                
                logger.info(f"Using optimal execution for {symbol}: {len(execution_plan['execution_schedule'])} chunks")
                
                # Execute each chunk
                for chunk in execution_plan['execution_schedule']:
                    # Simulate execution
                    self._execute_chunk(symbol, action, chunk['size'], price)
                    
                    # Wait between chunks
                    time.sleep(chunk['execution_time'] * 60)  # Convert hours to seconds
            else:
                # Execute order directly
                self._execute_chunk(symbol, action, order_size, price)
            
            # Update position
            if action == 'buy':
                self.positions[symbol] = current_position + size
            elif action == 'sell':
                self.positions[symbol] = current_position - size
            
            # Log execution
            logger.info(f"Executed {action} {order_size} {symbol} @ {price}")
            
            # Record order
            order_id = f"{symbol}-{datetime.now().strftime('%Y%m%d%H%M%S')}"
            self.orders[order_id] = {
                'symbol': symbol,
                'action': action,
                'size': order_size,
                'price': price,
                'timestamp': datetime.now(),
                'status': 'executed',
                'impact': impact
            }
            
            # Update performance
            self._update_performance(symbol, action, order_size, price)
        
        except Exception as e:
            logger.error(f"Error executing decision: {e}")
    
    def _execute_chunk(self, symbol: str, action: str, size: float, price: float):
        """Execute a chunk of an order"""
        # In a real implementation, this would send the order to a broker
        # Here we just simulate execution
        
        # Simulate slippage
        slippage = price * 0.0005  # 0.05% slippage
        executed_price = price + slippage if action == 'buy' else price - slippage
        
        logger.debug(f"Executed chunk: {action} {size} {symbol} @ {executed_price}")
    
    def _update_performance(self, symbol: str, action: str, size: float, price: float):
        """Update performance metrics"""
        if symbol not in self.performance:
            self.performance[symbol] = {
                'trades': [],
                'equity': 1000000,  # Initial equity
                'peak_equity': 1000000,
                'drawdown': 0,
                'win_count': 0,
                'loss_count': 0,
                'total_profit': 0,
                'total_loss': 0
            }
        
        # Add trade
        self.performance[symbol]['trades'].append({
            'timestamp': datetime.now(),
            'action': action,
            'size': size,
            'price': price
        })
        
        # Update equity (simplified)
        if len(self.performance[symbol]['trades']) >= 2:
            prev_trade = self.performance[symbol]['trades'][-2]
            current_trade = self.performance[symbol]['trades'][-1]
            
            if prev_trade['action'] != current_trade['action']:
                # Closed position
                if prev_trade['action'] == 'buy' and current_trade['action'] == 'sell':
                    # Long position
                    profit = (current_trade['price'] - prev_trade['price']) * prev_trade['size']
                elif prev_trade['action'] == 'sell' and current_trade['action'] == 'buy':
                    # Short position
                    profit = (prev_trade['price'] - current_trade['price']) * prev_trade['size']
                else:
                    profit = 0
                
                # Update performance
                self.performance[symbol]['equity'] += profit
                self.performance[symbol]['peak_equity'] = max(
                    self.performance[symbol]['peak_equity'],
                    self.performance[symbol]['equity']
                )
                self.performance[symbol]['drawdown'] = (
                    self.performance[symbol]['peak_equity'] - self.performance[symbol]['equity']
                ) / self.performance[symbol]['peak_equity']
                
                if profit > 0:
                    self.performance[symbol]['win_count'] += 1
                    self.performance[symbol]['total_profit'] += profit
                else:
                    self.performance[symbol]['loss_count'] += 1
                    self.performance[symbol]['total_loss'] += abs(profit)
    
    def _update_dashboard(self, decision: BrainDecision):
        """Update dashboard with decision"""
        # Update strategy dashboard
        for strategy_name in self.strategies:
            # Add signal to dashboard
            self.dashboard.add_signal(strategy_name, {
                'symbol': decision.symbol,
                'timestamp': decision.timestamp,
                'signal_type': decision.action,
                'confidence': decision.confidence,
                'price': decision.price,
                'size': decision.size,
                'success': True,  # Placeholder, will be updated later
                'return': 0.0     # Placeholder, will be updated later
            })
            
            # Update metrics
            if decision.symbol in self.performance:
                perf = self.performance[decision.symbol]
                
                win_rate = 0
                if perf['win_count'] + perf['loss_count'] > 0:
                    win_rate = perf['win_count'] / (perf['win_count'] + perf['loss_count'])
                
                profit_factor = 1.0
                if perf['total_loss'] > 0:
                    profit_factor = perf['total_profit'] / perf['total_loss']
                
                self.dashboard.update_strategy(strategy_name, {
                    'equity': perf['equity'],
                    'drawdown': perf['drawdown'],
                    'total_return': (perf['equity'] - 1000000) / 1000000,
                    'win_rate': win_rate,
                    'profit_factor': profit_factor,
                    'sharpe_ratio': 1.0,  # Placeholder
                    'max_drawdown': perf['drawdown'],
                    'recovery_factor': 1.0,  # Placeholder
                    'avg_trade': (perf['total_profit'] - perf['total_loss']) / len(perf['trades']) if perf['trades'] else 0,
                    'alpha': 0.02  # Placeholder
                })
    
    async def stop(self):
        """Stop the central controller"""
        if not self.running:
            return
        
        self.running = False
        
        # Stop brain
        self.brain.stop()
        
        # Wait for execution thread to finish
        if hasattr(self, 'execution_thread') and self.execution_thread.is_alive():
            self.execution_thread.join(timeout=5)
        
        # Save performance data
        self._save_performance()
        
        logger.info("Central Controller stopped")
    
    def pause(self):
        """Pause trading"""
        self.paused = True
        logger.info("Trading paused")
    
    def resume(self):
        """Resume trading"""
        self.paused = False
        logger.info("Trading resumed")
    
    def emergency_stop_trading(self):
        """Emergency stop all trading"""
        self.emergency_stop = True
        logger.warning("EMERGENCY STOP ACTIVATED")
        
        # Close all positions
        for symbol, position in self.positions.items():
            if position != 0:
                action = 'sell' if position > 0 else 'buy'
                size = abs(position)
                
                # Create decision
                decision = BrainDecision(
                    symbol=symbol,
                    timestamp=datetime.now(),
                    action=action,
                    confidence=1.0,
                    size=size,
                    price=None,  # Will be determined at execution
                    timeframe='1m',
                    reasoning=["Emergency stop"],
                    components={},
                    metadata={}
                )
                
                # Queue for execution
                self.execution_queue.put(decision)
                
                logger.warning(f"Emergency closing position: {action} {size} {symbol}")
    
    def _save_performance(self):
        """Save performance data to file"""
        try:
            # Create data directory if it doesn't exist
            os.makedirs('data', exist_ok=True)
            
            # Save performance data
            with open('data/performance.json', 'w') as f:
                json.dump(self.performance, f, indent=2, default=str)
            
            logger.info("Performance data saved")
        except Exception as e:
            logger.error(f"Error saving performance data: {e}")


# Example usage
if __name__ == "__main__":
    # Configure logging
    logging.basicConfig(level=logging.INFO)
    
    # Create controller
    controller = CentralController()
    
    # Run controller
    asyncio.run(controller.start())
