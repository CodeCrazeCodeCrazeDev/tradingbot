"""
from pathlib import Path
Elite Trading Bot - MT5 Demo
Demonstrates the full integration of all advanced components with MT5
"""

import asyncio
import logging
import argparse
import os
import json
from datetime import datetime, timedelta
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns

from trading_bot.brain.mt5_brain_trader import MT5BrainTrader
from trading_bot.analysis.market_intelligence import MarketIntelligenceSystem
from trading_bot.ml.explainable_ai import ExplainableAI
from trading_bot.advanced_features.blockchain_validation import BlockchainValidationSystem
from trading_bot.advanced_features.quantum_computing import QuantumOptimizationEngine
from trading_bot.execution.smart_execution import SmartExecutionEngine
from trading_bot.ml.personalized_learning import PersonalizedLearningSystem
import pathlib
import numpy
import pandas

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("logs/mt5_elite_bot_demo.log", mode='w'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class MT5EliteBotDemo:
    """MT5 Elite Bot Demo with all advanced features"""
    
    def __init__(self, config_path='config/elite_mt5_config.yaml'):
        """Initialize the demo"""
        self.config_path = config_path
        self.trader = None
        self.market_intelligence = None
        self.explainable_ai = None
        self.blockchain_validator = None
        self.quantum_optimizer = None
        self.smart_execution = None
        self.personalized_learning = None
    
    async def initialize(self):
        """Initialize all components"""
        # Create directories
        os.makedirs('logs', exist_ok=True)
        os.makedirs('data', exist_ok=True)
        os.makedirs('visualizations', exist_ok=True)
        
        # Initialize MT5 Brain Trader
        self.trader = MT5BrainTrader(self.config_path)
        
        # Initialize Market Intelligence System
        self.market_intelligence = MarketIntelligenceSystem()
        
        # Initialize Explainable AI
        self.explainable_ai = ExplainableAI()
        
        # Initialize Blockchain Validator
        self.blockchain_validator = BlockchainValidationSystem()
        
        # Initialize Quantum Optimizer
        self.quantum_optimizer = QuantumOptimizationEngine()
        
        # Initialize Smart Execution Engine
        self.smart_execution = SmartExecutionEngine()
        
        # Initialize Personalized Learning System
        self.personalized_learning = PersonalizedLearningSystem()
        
        logger.info("All components initialized")
    
    async def run_live_trading(self, duration_minutes=60):
        """Run live trading with MT5"""
        logger.info(f"Starting live trading for {duration_minutes} minutes")
        
        # Start the trader
        trader_task = asyncio.create_task(self.trader.start())
        
        # Run for specified duration
        start_time = datetime.now()
        end_time = start_time + timedelta(minutes=duration_minutes)
        
        try:
            while datetime.now() < end_time:
                # Run periodic optimizations
                if datetime.now().minute % 15 == 0:  # Every 15 minutes
                    await self._run_optimizations()
                
                # Wait before next check
                await asyncio.sleep(60)
            
            # Stop the trader
            await self.trader.stop()
            await trader_task
            
            logger.info("Live trading completed")
            
        except KeyboardInterrupt:
            logger.info("Live trading stopped by user")
            await self.trader.stop()
            await trader_task
        except Exception as e:
            logger.error(f"Error in live trading: {e}")
            await self.trader.stop()
            await trader_task
    
    async def run_simulation(self, duration_minutes=30):
        """Run simulation mode"""
        logger.info(f"Starting simulation for {duration_minutes} minutes")
        
        # Initialize components
        await self.initialize()
        
        # Create simulated market data
        symbols = self.trader.symbols
        
        # Initialize market data
        market_data = {}
        for symbol in symbols:
            market_data[symbol] = {
                'price': 1.0 if 'USD' in symbol else 100.0,
                'trend': np.random.choice(['up', 'down', 'sideways']),
                'volatility': np.random.uniform(0.01, 0.05)
            }
        
        # Start dashboard
        self.trader.dashboard.start()
        
        # Simulation loop
        start_time = datetime.now()
        end_time = start_time + timedelta(minutes=duration_minutes)
        
        try:
            while datetime.now() < end_time:
                # Update market data
                for symbol in symbols:
                    # Simulate price movement
                    data = market_data[symbol]
                    trend = data['trend']
                    volatility = data['volatility']
                    
                    # Calculate price change
                    if trend == 'up':
                        change = np.random.normal(0.001, volatility)
                    elif trend == 'down':
                        change = np.random.normal(-0.001, volatility)
                    else:  # sideways
                        change = np.random.normal(0, volatility)
                    
                    # Update price
                    data['price'] *= (1 + change)
                    
                    # Occasionally change trend
                    if np.random.random() < 0.05:
                        data['trend'] = np.random.choice(['up', 'down', 'sideways'])
                    
                    # Update dashboard
                    self.trader.dashboard.update_metric(f"{symbol}_price", data['price'])
                    
                    # Generate trading decision
                    if np.random.random() < 0.1:  # 10% chance of decision
                        action = np.random.choice(['buy', 'sell', 'neutral'], p=[0.4, 0.4, 0.2])
                        confidence = np.random.uniform(0.5, 0.95)
                        
                        # Create explanation
                        explanation = self.explainable_ai.generate_explanation(
                            symbol=symbol,
                            action=action,
                            confidence=confidence,
                            market_data={'price': data['price'], 'trend': data['trend']}
                        )
                        
                        logger.info(f"Decision for {symbol}: {action} (confidence: {confidence:.2f})")
                        logger.info(f"Explanation: {explanation}")
                        
                        # Record with blockchain
                        await self.blockchain_validator.record_prediction(
                            symbol=symbol,
                            prediction={'action': action, 'confidence': confidence},
                            confidence=confidence
                        )
                
                # Run periodic optimizations
                if datetime.now().minute % 5 == 0:  # Every 5 minutes
                    await self._run_optimizations()
                
                # Wait before next update
                await asyncio.sleep(1)
            
            logger.info("Simulation completed")
            
        except KeyboardInterrupt:
            logger.info("Simulation stopped by user")
        except Exception as e:
            logger.error(f"Error in simulation: {e}")
    
    async def run_backtest(self, data_path='data/historical'):
        """Run backtest with historical data"""
        logger.info("Starting backtest")
        
        # Initialize components
        await self.initialize()
        
        try:
            # Load historical data
            logger.info(f"Loading historical data from {data_path}")
            
            # Check if historical data exists
            if not os.path.exists(data_path):
                logger.warning(f"Historical data path {data_path} does not exist")
                logger.info("Downloading sample historical data...")
                await self._download_sample_data(data_path)
            
            # Run backtest
            logger.info("Running backtest...")
            
            # Process each symbol
            for symbol in self.trader.symbols:
                # Load symbol data
                symbol_data = self._load_symbol_data(data_path, symbol)
                if symbol_data is None:
                    continue
                
                logger.info(f"Processing {symbol} with {len(symbol_data)} data points")
                
                # Process each bar
                decisions = []
                trades = []
                
                for i in range(100, len(symbol_data)):
                    # Get current bar
                    current_bar = symbol_data.iloc[i]
                    
                    # Create market data
                    market_data = {
                        'open': current_bar['open'],
                        'high': current_bar['high'],
                        'low': current_bar['low'],
                        'close': current_bar['close'],
                        'volume': current_bar['volume'] if 'volume' in current_bar else 0
                    }
                    
                    # Make decision
                    decision = await self._simulate_decision(symbol, market_data)
                    if decision:
                        decisions.append(decision)
                        
                        # Simulate trade execution
                        trade = await self._simulate_trade(decision, market_data)
                        if trade:
                            trades.append(trade)
                
                # Calculate performance metrics
                performance = self._calculate_performance(trades)
                
                # Log performance
                logger.info(f"Performance for {symbol}:")
                logger.info(f"  Total trades: {performance['total_trades']}")
                logger.info(f"  Win rate: {performance['win_rate']:.2f}%")
                logger.info(f"  Profit factor: {performance['profit_factor']:.2f}")
                logger.info(f"  Sharpe ratio: {performance['sharpe_ratio']:.2f}")
                logger.info(f"  Max drawdown: {performance['max_drawdown']:.2f}%")
                
                # Plot results
                self._plot_backtest_results(symbol, symbol_data, trades, performance)
            
            logger.info("Backtest completed")
            
        except Exception as e:
            logger.error(f"Error in backtest: {e}")
    
    async def _run_optimizations(self):
        """Run periodic optimizations"""
        logger.info("Running optimizations")
        
        try:
            # Portfolio optimization with quantum computing
            portfolio = await self.quantum_optimizer.optimize_portfolio(
                symbols=self.trader.symbols,
                constraints={'risk_level': 'moderate'}
            )
            
            logger.info("Portfolio optimization completed")
            logger.info("Recommended allocations:")
            for symbol, allocation in portfolio.items():
                logger.info(f"  {symbol}: {allocation:.2%}")
            
            # Update personalized learning system
            await self.personalized_learning.update_models()
            
            # Verify blockchain integrity
            verification = await self.blockchain_validator.verify_blockchain()
            logger.info(f"Blockchain verification: {verification['status']}")
            
        except Exception as e:
            logger.error(f"Error in optimizations: {e}")
    
    async def _simulate_decision(self, symbol, market_data):
        """Simulate trading decision"""
        # Use market intelligence to analyze data
        analysis = await self.market_intelligence.analyze_market(
            symbol=symbol,
            market_data=market_data
        )
        
        # Determine action based on analysis
        if analysis['bullish_score'] > 0.7:
            action = 'buy'
            confidence = analysis['bullish_score']
        elif analysis['bearish_score'] > 0.7:
            action = 'sell'
            confidence = analysis['bearish_score']
        else:
            action = 'neutral'
            confidence = max(1 - analysis['bullish_score'] - analysis['bearish_score'], 0.5)
        
        # Create decision
        decision = {
            'symbol': symbol,
            'timestamp': datetime.now(),
            'action': action,
            'confidence': confidence,
            'price': market_data['close'],
            'analysis': analysis
        }
        
        return decision
    
    async def _simulate_trade(self, decision, market_data):
        """Simulate trade execution"""
        if decision['action'] == 'neutral':
            return None
        
        # Calculate position size
        position_size = 0.01 * decision['confidence'] * 10000  # 1% of account * confidence
        
        # Calculate entry price with slippage
        slippage = 0.0001 * market_data['close']  # 1 pip slippage
        entry_price = market_data['close'] + slippage if decision['action'] == 'buy' else market_data['close'] - slippage
        
        # Calculate stop loss and take profit
        atr = (market_data['high'] - market_data['low']) * 0.5  # Simple ATR approximation
        if decision['action'] == 'buy':
            stop_loss = entry_price - (2 * atr)
            take_profit = entry_price + (4 * atr)
        else:
            stop_loss = entry_price + (2 * atr)
            take_profit = entry_price - (4 * atr)
        
        # Create trade
        trade = {
            'symbol': decision['symbol'],
            'timestamp': decision['timestamp'],
            'action': decision['action'],
            'entry_price': entry_price,
            'position_size': position_size,
            'stop_loss': stop_loss,
            'take_profit': take_profit,
            'exit_price': None,
            'exit_timestamp': None,
            'profit_loss': 0,
            'status': 'open'
        }
        
        return trade
    
    def _calculate_performance(self, trades):
        """Calculate performance metrics"""
        if not trades:
            return {
                'total_trades': 0,
                'win_rate': 0,
                'profit_factor': 0,
                'sharpe_ratio': 0,
                'max_drawdown': 0
            }
        
        # Calculate basic metrics
        total_trades = len(trades)
        winning_trades = sum(1 for t in trades if t['profit_loss'] > 0)
        losing_trades = sum(1 for t in trades if t['profit_loss'] < 0)
        
        win_rate = (winning_trades / total_trades) * 100 if total_trades > 0 else 0
        
        # Calculate profit factor
        gross_profit = sum(t['profit_loss'] for t in trades if t['profit_loss'] > 0)
        gross_loss = abs(sum(t['profit_loss'] for t in trades if t['profit_loss'] < 0))
        profit_factor = gross_profit / gross_loss if gross_loss > 0 else 0
        
        # Calculate Sharpe ratio
        returns = [t['profit_loss'] for t in trades]
        sharpe_ratio = np.mean(returns) / np.std(returns) if np.std(returns) > 0 else 0
        
        # Calculate max drawdown
        equity_curve = np.cumsum(returns)
        max_drawdown = 0
        peak = equity_curve[0]
        
        for value in equity_curve:
            if value > peak:
                peak = value
            drawdown = (peak - value) / peak * 100 if peak > 0 else 0
            max_drawdown = max(max_drawdown, drawdown)
        
        return {
            'total_trades': total_trades,
            'win_rate': win_rate,
            'profit_factor': profit_factor,
            'sharpe_ratio': sharpe_ratio,
            'max_drawdown': max_drawdown
        }
    
    def _plot_backtest_results(self, symbol, data, trades, performance):
        """Plot backtest results"""
        # Create visualizations directory
        os.makedirs('visualizations', exist_ok=True)
        
        # Plot price chart with trades
        plt.figure(figsize=(12, 8))
        
        # Plot price
        plt.subplot(2, 1, 1)
        plt.plot(data['close'], label='Close Price')
        
        # Plot trades
        buy_x = []
        buy_y = []
        sell_x = []
        sell_y = []
        
        for trade in trades:
            if trade['action'] == 'buy':
                buy_x.append(trade['timestamp'])
                buy_y.append(trade['entry_price'])
            else:
                sell_x.append(trade['timestamp'])
                sell_y.append(trade['entry_price'])
        
        plt.scatter(buy_x, buy_y, color='green', marker='^', label='Buy')
        plt.scatter(sell_x, sell_y, color='red', marker='v', label='Sell')
        
        plt.title(f'{symbol} Price Chart with Trades')
        plt.xlabel('Time')
        plt.ylabel('Price')
        plt.legend()
        plt.grid(True)
        
        # Plot equity curve
        plt.subplot(2, 1, 2)
        returns = [t['profit_loss'] for t in trades]
        equity_curve = np.cumsum(returns)
        plt.plot(equity_curve, label='Equity Curve')
        
        plt.title(f'Equity Curve - Win Rate: {performance["win_rate"]:.2f}%, Max DD: {performance["max_drawdown"]:.2f}%')
        plt.xlabel('Trades')
        plt.ylabel('Equity')
        plt.grid(True)
        plt.legend()
        
        plt.tight_layout()
        plt.savefig(f'visualizations/{symbol}_backtest.png')
        plt.close()
        
        logger.info(f"Backtest results for {symbol} saved to visualizations/{symbol}_backtest.png")
    
    def _load_symbol_data(self, data_path, symbol):
        """Load historical data for a symbol"""
        try:
            # Check for CSV file
            symbol_file = os.path.join(data_path, f"{symbol.replace('/', '_')}.csv")
            if os.path.exists(symbol_file):
                df = pd.read_csv(symbol_file)
                if 'time' in df.columns:
                    df['time'] = pd.to_datetime(df['time'])
                    df.set_index('time', inplace=True)
                return df
            
            logger.warning(f"No historical data found for {symbol}")
            return None
            
        except Exception as e:
            logger.error(f"Error loading data for {symbol}: {e}")
            return None
    
    async def _download_sample_data(self, data_path):
        """Download sample historical data"""
        try:
            # Create directory
            os.makedirs(data_path, exist_ok=True)
            
            # Generate sample data for each symbol
            for symbol in self.trader.symbols:
                # Generate random data
                start_date = datetime.now() - timedelta(days=365)
                dates = pd.date_range(start=start_date, periods=365, freq='D')
                
                # Initial price
                if 'USD' in symbol:
                    initial_price = 1.0 if 'EUR' in symbol or 'GBP' in symbol else 100.0
                else:
                    initial_price = 100.0
                
                # Generate OHLC data
                np.random.seed(42)  # For reproducibility
                
                # Generate returns with trend and volatility
                returns = np.random.normal(0.0002, 0.01, len(dates))
                prices = initial_price * (1 + np.cumsum(returns))
                
                # Generate OHLC
                high_factors = np.random.uniform(1.001, 1.02, len(dates))
                low_factors = np.random.uniform(0.98, 0.999, len(dates))
                
                close = prices
                open_prices = close * np.random.uniform(0.995, 1.005, len(dates))
                high = close * high_factors
                low = close * low_factors
                volume = np.random.uniform(1000, 10000, len(dates))
                
                # Create DataFrame
                df = pd.DataFrame({
                    'time': dates,
                    'open': open_prices,
                    'high': high,
                    'low': low,
                    'close': close,
                    'volume': volume
                })
                
                # Save to CSV
                symbol_file = os.path.join(data_path, f"{symbol.replace('/', '_')}.csv")
                df.to_csv(symbol_file, index=False)
                
                logger.info(f"Generated sample data for {symbol}: {len(df)} bars")
            
        except Exception as e:
            logger.error(f"Error downloading sample data: {e}")


async def main():
    """Main function"""
    # Parse command line arguments
    parser = argparse.ArgumentParser(description='MT5 Elite Bot Demo')
    parser.add_argument('--mode', choices=['live', 'simulation', 'backtest'], default='simulation',
                      help='Trading mode: live, simulation, or backtest')
    parser.add_argument('--config', default='config/elite_mt5_config.yaml',
                      help='Path to configuration file')
    parser.add_argument('--duration', type=int, default=30,
                      help='Duration in minutes for live or simulation mode')
    parser.add_argument('--data', default='data/historical',
                      help='Path to historical data for backtest mode')
    args = parser.parse_args()
    
    # Create demo
    demo = MT5EliteBotDemo(args.config)
    
    # Run in selected mode
    if args.mode == 'live':
        await demo.run_live_trading(args.duration)
    elif args.mode == 'simulation':
        await demo.run_simulation(args.duration)
    else:  # backtest
        await demo.run_backtest(args.data)


if __name__ == "__main__":
    asyncio.run(main())
