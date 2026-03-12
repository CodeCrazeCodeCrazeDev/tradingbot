"""
PERFECT BOT - AlphaAlgo Complete Integration
Combines: Enhanced Data + Optimized Strategy + Advanced ML + Paper Trading
"""

import asyncio
import pandas as pd
import numpy as np
from datetime import datetime
from typing import Dict, Optional
import logging
import json
from pathlib import Path

# Import our modules
from data_fetcher import EnhancedDataFetcher
from optimized_strategy import OptimizedStrategy
from advanced_ml_models import AdvancedMLEnsemble

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class PerfectBot:
    """
    The Perfect AlphaAlgo Bot
    
    Features:
    - Multi-source data fetching with fallbacks
    - Optimized strategy with >50% win rate target
    - Advanced ML ensemble (RF, XGBoost, LightGBM)
    - Paper trading mode
    - Real-time performance tracking
    """
    
    def __init__(self, config: Dict = None):
        self.config = config or {
            'symbols': ['EURUSD', 'GBPUSD', 'USDJPY'],
            'initial_capital': 10000,
            'risk_per_trade': 0.02,  # 2% risk per trade
            'max_positions': 3,
            'paper_trading': True,
            'update_interval': 60,  # seconds
        }
        
        self.data_fetcher = None
        self.strategy = OptimizedStrategy()
        self.ml_ensemble = AdvancedMLEnsemble()
        
        self.capital = self.config['initial_capital']
        self.positions = {}
        self.trades_history = []
        self.equity_curve = [self.capital]
        
        # Create logs directory
        self.log_dir = Path('logs')
        self.log_dir.mkdir(exist_ok=True)
        
        logger.info("Perfect Bot initialized")
    
    async def initialize(self):
        """Initialize bot components"""
        logger.info("Initializing Perfect Bot...")
        
        # Initialize data fetcher
        self.data_fetcher = EnhancedDataFetcher()
        await self.data_fetcher.__aenter__()
        
        # Fetch initial data for all symbols
        logger.info(f"Fetching initial data for {len(self.config['symbols'])} symbols...")
        self.market_data = await self.data_fetcher.fetch_multiple_symbols(self.config['symbols'])
        
        # Train ML models on historical data
        if self.market_data:
            sample_symbol = list(self.market_data.keys())[0]
            sample_data = self.market_data[sample_symbol]
            
            logger.info("Training ML ensemble...")
            X, y, _ = self.ml_ensemble.prepare_data(sample_data)
            
            # Use 80% for training
            split_idx = int(len(X) * 0.8)
            self.ml_ensemble.train_ensemble(X.iloc[:split_idx], y.iloc[:split_idx])
            
            logger.info("ML ensemble trained successfully")
        
        logger.info("Perfect Bot ready!")
    
    async def shutdown(self):
        """Shutdown bot gracefully"""
        logger.info("Shutting down Perfect Bot...")
        
        if self.data_fetcher:
            await self.data_fetcher.__aexit__(None, None, None)
        
        # Save trading history
        self.save_results()
        
        logger.info("Perfect Bot shutdown complete")
    
    def analyze_symbol(self, symbol: str, data: pd.DataFrame) -> Dict:
        """
        Analyze a symbol using both strategy and ML
        
        Returns:
            Dictionary with analysis results
        """
        # Calculate indicators first
        data_with_indicators = self.strategy.calculate_indicators(data)
        
        # Get strategy signals
        strategy_signals = self.strategy.generate_signals(data)
        current_signal = strategy_signals.iloc[-1]
        
        # Get ML prediction
        X, y, _ = self.ml_ensemble.prepare_data(data)
        if len(X) > 0:
            ml_prediction = self.ml_ensemble.predict(X.iloc[[-1]])[0]
            ml_probability = self.ml_ensemble.predict_proba(X.iloc[[-1]])[0]
        else:
            ml_prediction = 0
            ml_probability = [0.5, 0.5]
        
        # Combine signals (both must agree)
        combined_signal = 0
        if current_signal == 1 and ml_prediction == 1:
            combined_signal = 1  # Buy
        elif current_signal == -1 and ml_prediction == 0:
            combined_signal = -1  # Sell
        
        # Calculate dynamic stops using data with indicators
        stop_loss_pct, take_profit_pct = self.strategy.calculate_dynamic_stops(data_with_indicators, combined_signal)
        
        return {
            'symbol': symbol,
            'current_price': data['close'].iloc[-1],
            'strategy_signal': int(current_signal),
            'ml_prediction': int(ml_prediction),
            'ml_confidence': float(ml_probability[ml_prediction]),
            'combined_signal': combined_signal,
            'stop_loss_pct': float(stop_loss_pct),
            'take_profit_pct': float(take_profit_pct),
            'timestamp': datetime.now().isoformat()
        }
    
    def execute_trade(self, analysis: Dict):
        """Execute trade based on analysis (paper trading)"""
        symbol = analysis['symbol']
        signal = analysis['combined_signal']
        
        # Check if we already have a position
        if symbol in self.positions:
            logger.info(f"Already have position in {symbol}")
            return
        
        # Check max positions
        if len(self.positions) >= self.config['max_positions']:
            logger.info(f"Max positions ({self.config['max_positions']}) reached")
            return
        
        if signal != 0:
            # Calculate position size
            position_size = self.strategy.get_position_size(
                self.capital, 
                self.config['risk_per_trade']
            )
            
            # Open position (paper trading)
            self.positions[symbol] = {
                'entry_price': analysis['current_price'],
                'entry_time': datetime.now(),
                'direction': 'long' if signal == 1 else 'short',
                'size': position_size,
                'stop_loss': analysis['current_price'] * (1 - analysis['stop_loss_pct']) if signal == 1 
                            else analysis['current_price'] * (1 + analysis['stop_loss_pct']),
                'take_profit': analysis['current_price'] * (1 + analysis['take_profit_pct']) if signal == 1
                              else analysis['current_price'] * (1 - analysis['take_profit_pct']),
            }
            
            logger.info(f"OPENED {self.positions[symbol]['direction'].upper()} position in {symbol} at {analysis['current_price']:.5f}")
    
    def check_positions(self):
        """Check and manage open positions"""
        for symbol in list(self.positions.keys()):
            if symbol not in self.market_data:
                continue
            
            position = self.positions[symbol]
            current_price = self.market_data[symbol]['close'].iloc[-1]
            
            # Check stop loss
            if position['direction'] == 'long':
                if current_price <= position['stop_loss']:
                    self.close_position(symbol, current_price, 'stop_loss')
                elif current_price >= position['take_profit']:
                    self.close_position(symbol, current_price, 'take_profit')
            else:  # short
                if current_price >= position['stop_loss']:
                    self.close_position(symbol, current_price, 'stop_loss')
                elif current_price <= position['take_profit']:
                    self.close_position(symbol, current_price, 'take_profit')
    
    def close_position(self, symbol: str, exit_price: float, reason: str):
        """Close a position"""
        position = self.positions[symbol]
        
        # Calculate P&L
        if position['direction'] == 'long':
            pnl_pct = (exit_price - position['entry_price']) / position['entry_price']
        else:
            pnl_pct = (position['entry_price'] - exit_price) / position['entry_price']
        
        pnl = self.capital * position['size'] * pnl_pct
        self.capital += pnl
        
        # Record trade
        trade = {
            'symbol': symbol,
            'direction': position['direction'],
            'entry_price': position['entry_price'],
            'exit_price': exit_price,
            'entry_time': position['entry_time'].isoformat(),
            'exit_time': datetime.now().isoformat(),
            'pnl': pnl,
            'pnl_pct': pnl_pct * 100,
            'reason': reason
        }
        
        self.trades_history.append(trade)
        self.equity_curve.append(self.capital)
        
        logger.info(f"CLOSED {position['direction'].upper()} {symbol} at {exit_price:.5f} | P&L: ${pnl:.2f} ({pnl_pct*100:.2f}%) | Reason: {reason}")
        
        # Remove position
        del self.positions[symbol]
    
    def get_performance_metrics(self) -> Dict:
        """Calculate performance metrics"""
        if len(self.trades_history) == 0:
            return {'status': 'No trades yet'}
        
        winning_trades = [t for t in self.trades_history if t['pnl'] > 0]
        losing_trades = [t for t in self.trades_history if t['pnl'] <= 0]
        
        total_return = (self.capital / self.config['initial_capital'] - 1) * 100
        win_rate = len(winning_trades) / len(self.trades_history) * 100
        
        avg_win = np.mean([t['pnl'] for t in winning_trades]) if winning_trades else 0
        avg_loss = np.mean([t['pnl'] for t in losing_trades]) if losing_trades else 0
        
        profit_factor = abs(sum([t['pnl'] for t in winning_trades]) / sum([t['pnl'] for t in losing_trades])) if losing_trades else float('inf')
        
        # Sharpe ratio
        if len(self.equity_curve) > 1:
            returns = pd.Series(self.equity_curve).pct_change().dropna()
            sharpe = np.sqrt(252) * returns.mean() / returns.std() if returns.std() > 0 else 0
        else:
            sharpe = 0
        
        # Max drawdown
        equity_series = pd.Series(self.equity_curve)
        running_max = equity_series.expanding().max()
        drawdown = (equity_series - running_max) / running_max
        max_drawdown = drawdown.min() * 100
        
        return {
            'total_return': total_return,
            'current_capital': self.capital,
            'total_trades': len(self.trades_history),
            'winning_trades': len(winning_trades),
            'losing_trades': len(losing_trades),
            'win_rate': win_rate,
            'avg_win': avg_win,
            'avg_loss': avg_loss,
            'profit_factor': profit_factor,
            'sharpe_ratio': sharpe,
            'max_drawdown': max_drawdown,
            'open_positions': len(self.positions)
        }
    
    def save_results(self):
        """Save trading results to file"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        # Save trades history
        trades_file = self.log_dir / f'trades_{timestamp}.json'
        with open(trades_file, 'w') as f:
            json.dump(self.trades_history, f, indent=2)
        
        # Save performance metrics
        metrics = self.get_performance_metrics()
        metrics_file = self.log_dir / f'metrics_{timestamp}.json'
        with open(metrics_file, 'w') as f:
            json.dump(metrics, f, indent=2)
        
        logger.info(f"Results saved to {self.log_dir}")
    
    async def run_single_iteration(self):
        """Run one iteration of the trading loop"""
        # Update market data
        self.market_data = await self.data_fetcher.fetch_multiple_symbols(self.config['symbols'])
        
        # Check existing positions
        self.check_positions()
        
        # Analyze each symbol
        for symbol, data in self.market_data.items():
            if len(data) < 100:  # Need enough data
                continue
            
            analysis = self.analyze_symbol(symbol, data)
            
            logger.info(f"{symbol}: Signal={analysis['combined_signal']}, ML Confidence={analysis['ml_confidence']:.2%}")
            
            # Execute trade if signal is strong
            if analysis['combined_signal'] != 0 and analysis['ml_confidence'] > 0.6:
                self.execute_trade(analysis)
        
        # Log performance
        metrics = self.get_performance_metrics()
        if 'total_return' in metrics:
            logger.info(f"Performance: Return={metrics['total_return']:.2f}%, Win Rate={metrics['win_rate']:.1f}%, Sharpe={metrics['sharpe_ratio']:.2f}")
    
    async def run(self, iterations: int = None):
        """
        Run the perfect bot
        
        Args:
            iterations: Number of iterations (None for infinite)
        """
        await self.initialize()
        
        try:
            iteration = 0
            while iterations is None or iteration < iterations:
                await self.run_single_iteration()
                
                iteration += 1
                if iterations:
                    logger.info(f"Iteration {iteration}/{iterations}")
                
                # Wait before next iteration
                await asyncio.sleep(self.config['update_interval'])
                
        except KeyboardInterrupt:
            logger.info("Received shutdown signal")
        finally:
            await self.shutdown()


async def main():
    """Run the Perfect Bot"""
    print("="*70)
    print("PERFECT BOT - AlphaAlgo Complete System")
    print("="*70)
    print("\nFeatures:")
    print("- Enhanced data fetching with Alpha Vantage")
    print("- Optimized strategy (target: >50% win rate)")
    print("- Advanced ML ensemble (RF + XGBoost + LightGBM)")
    print("- Paper trading mode")
    print("- Real-time performance tracking")
    print("\n" + "="*70)
    
    # Create and run bot
    bot = PerfectBot(config={
        'symbols': ['EURUSD', 'GBPUSD'],
        'initial_capital': 10000,
        'paper_trading': True,
        'update_interval': 5,  # 5 seconds for testing
    })
    
    # Run for 10 iterations (for testing)
    await bot.run(iterations=10)
    
    # Display final results
    print("\n" + "="*70)
    print("FINAL RESULTS")
    print("="*70)
    
    metrics = bot.get_performance_metrics()
    if 'total_return' in metrics:
        print(f"\nTotal Return:     {metrics['total_return']:.2f}%")
        print(f"Current Capital:  ${metrics['current_capital']:.2f}")
        print(f"Total Trades:     {metrics['total_trades']}")
        print(f"Win Rate:         {metrics['win_rate']:.1f}%")
        print(f"Profit Factor:    {metrics['profit_factor']:.2f}")
        print(f"Sharpe Ratio:     {metrics['sharpe_ratio']:.2f}")
        print(f"Max Drawdown:     {metrics['max_drawdown']:.2f}%")
        
        if metrics['win_rate'] > 50:
            print("\nSUCCESS: Win rate > 50%!")
        
        if metrics['sharpe_ratio'] > 1.0:
            print("SUCCESS: Sharpe ratio > 1.0!")
    
    print("\n" + "="*70)
    print("PERFECT BOT TEST COMPLETE!")
    print("="*70)


if __name__ == "__main__":
    asyncio.run(main())
