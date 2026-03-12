"""
ULTIMATE ALPHAALGO - All Phases Combined
Phase 2: Advanced ML ✅
Phase 3: Deep Learning ✅
Phase 4: Aggressive Trading ✅
Phase 5: Multi-Strategy Ensemble ✅
"""

import asyncio
import pandas as pd
import numpy as np
from datetime import datetime
from typing import Dict, Optional, List
import logging
import json
from pathlib import Path
import sys
import os

# Add parent directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

# Import components
try:
    from perfect_bot.data_fetcher import EnhancedDataFetcher
    from perfect_bot.advanced_ml_models import AdvancedMLEnsemble
except ImportError:
    # Fallback imports
    sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'perfect_bot'))
    from data_fetcher import EnhancedDataFetcher
    from advanced_ml_models import AdvancedMLEnsemble

from aggressive_strategy import AggressiveStrategy
from deep_learning_models import SimpleDeepLearning, PYTORCH_AVAILABLE

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class UltimateAlphaAlgo:
    """
    The Ultimate AlphaAlgo - All Phases Combined
    
    Features:
    ✅ Phase 2: Advanced ML (XGBoost, LightGBM, Random Forest)
    ✅ Phase 3: Deep Learning (LSTM/Simple DL)
    ✅ Phase 4: Aggressive Strategy (More trades)
    ✅ Phase 5: Multi-Model Ensemble
    ✅ Relaxed trading filters (Strategy OR ML)
    ✅ Lower confidence threshold (55%)
    ✅ More frequent signals
    """
    
    def __init__(self, config: Dict = None):
        self.config = config or {
            'symbols': ['EURUSD', 'GBPUSD', 'USDJPY', 'AUDUSD'],
            'initial_capital': 10000,
            'risk_per_trade': 0.02,
            'max_positions': 5,
            'paper_trading': True,
            'update_interval': 10,
            'aggressive_mode': True,
            'min_ml_confidence': 0.55,  # Lowered from 0.60
        }
        
        self.data_fetcher = None
        self.aggressive_strategy = AggressiveStrategy()
        self.ml_ensemble = AdvancedMLEnsemble()
        self.deep_learning = SimpleDeepLearning()
        
        self.capital = self.config['initial_capital']
        self.positions = {}
        self.trades_history = []
        self.equity_curve = [self.capital]
        
        self.log_dir = Path('logs')
        self.log_dir.mkdir(exist_ok=True)
        
        logger.info("🚀 ULTIMATE ALPHAALGO INITIALIZED")
        logger.info(f"   Mode: {'AGGRESSIVE' if self.config['aggressive_mode'] else 'CONSERVATIVE'}")
        logger.info(f"   ML Confidence: {self.config['min_ml_confidence']*100:.0f}%")
        logger.info(f"   Max Positions: {self.config['max_positions']}")
    
    async def initialize(self):
        """Initialize all components"""
        logger.info("="*70)
        logger.info("INITIALIZING ULTIMATE ALPHAALGO")
        logger.info("="*70)
        
        # Initialize data fetcher
        self.data_fetcher = EnhancedDataFetcher()
        await self.data_fetcher.__aenter__()
        
        # Fetch initial data
        logger.info(f"Fetching data for {len(self.config['symbols'])} symbols...")
        self.market_data = await self.data_fetcher.fetch_multiple_symbols(self.config['symbols'])
        
        if not self.market_data:
            logger.error("Failed to fetch market data!")
            return
        
        logger.info(f"✅ Fetched data for {len(self.market_data)} symbols")
        
        # Train ML models
        logger.info("Training ML ensemble...")
        sample_symbol = list(self.market_data.keys())[0]
        sample_data = self.market_data[sample_symbol]
        
        X, y, _ = self.ml_ensemble.prepare_data(sample_data)
        split_idx = int(len(X) * 0.8)
        self.ml_ensemble.train_ensemble(X.iloc[:split_idx], y.iloc[:split_idx])
        logger.info("✅ ML ensemble trained")
        
        # Train deep learning
        logger.info("Training deep learning model...")
        X_dl, y_dl = self.deep_learning.prepare_features(sample_data)
        split_idx = int(len(X_dl) * 0.8)
        self.deep_learning.train(X_dl[:split_idx], y_dl[:split_idx])
        logger.info("✅ Deep learning model trained")
        
        logger.info("="*70)
        logger.info("🎉 ULTIMATE ALPHAALGO READY!")
        logger.info("="*70)
    
    async def shutdown(self):
        """Shutdown gracefully"""
        logger.info("Shutting down Ultimate AlphaAlgo...")
        
        if self.data_fetcher:
            await self.data_fetcher.__aexit__(None, None, None)
        
        self.save_results()
        logger.info("Shutdown complete")
    
    def analyze_symbol(self, symbol: str, data: pd.DataFrame) -> Dict:
        """
        Analyze symbol with ALL models
        
        Returns combined analysis from:
        - Aggressive Strategy
        - Advanced ML Ensemble
        - Deep Learning
        """
        # Calculate indicators
        data_with_indicators = self.aggressive_strategy.calculate_indicators(data)
        
        # Get aggressive strategy signal
        strategy_signals = self.aggressive_strategy.generate_signals(data)
        strategy_signal = strategy_signals.iloc[-1]
        
        # Get ML ensemble prediction
        X_ml, y_ml, _ = self.ml_ensemble.prepare_data(data)
        if len(X_ml) > 0:
            ml_prediction = self.ml_ensemble.predict(X_ml.iloc[[-1]])[0]
            ml_probability = self.ml_ensemble.predict_proba(X_ml.iloc[[-1]])[0]
            ml_confidence = float(ml_probability[ml_prediction])
        else:
            ml_prediction = 0
            ml_confidence = 0.5
        
        # Get deep learning prediction
        X_dl, y_dl = self.deep_learning.prepare_features(data)
        if len(X_dl) > 0:
            dl_prediction = self.deep_learning.predict(X_dl[[-1]])[0]
            dl_proba = self.deep_learning.predict_proba(X_dl[[-1]])[0]
            dl_confidence = float(dl_proba[dl_prediction])
        else:
            dl_prediction = 0
            dl_confidence = 0.5
        
        # ENSEMBLE DECISION: Majority vote
        votes = [
            1 if strategy_signal == 1 else 0,
            ml_prediction,
            dl_prediction
        ]
        
        # Combined signal: majority vote
        buy_votes = sum(votes)
        if buy_votes >= 2:  # At least 2 models agree on buy
            combined_signal = 1
        elif buy_votes == 0:  # All models say sell/hold
            combined_signal = -1 if strategy_signal == -1 else 0
        else:
            combined_signal = 0
        
        # Average confidence
        avg_confidence = (ml_confidence + dl_confidence) / 2
        
        # AGGRESSIVE MODE: Accept if strategy OR ML agrees
        if self.config['aggressive_mode']:
            should_trade = self.aggressive_strategy.should_trade(
                int(strategy_signal), 
                ml_prediction, 
                ml_confidence
            )
        else:
            # Conservative: both must agree
            should_trade = (strategy_signal != 0 and ml_prediction == 1 and 
                          avg_confidence > self.config['min_ml_confidence'])
        
        # Calculate stops
        stop_loss_pct, take_profit_pct = self.aggressive_strategy.calculate_dynamic_stops(
            data_with_indicators, combined_signal
        )
        
        return {
            'symbol': symbol,
            'current_price': data['close'].iloc[-1],
            'strategy_signal': int(strategy_signal),
            'ml_prediction': int(ml_prediction),
            'ml_confidence': ml_confidence,
            'dl_prediction': int(dl_prediction),
            'dl_confidence': dl_confidence,
            'combined_signal': combined_signal,
            'avg_confidence': avg_confidence,
            'should_trade': should_trade,
            'stop_loss_pct': float(stop_loss_pct),
            'take_profit_pct': float(take_profit_pct),
            'timestamp': datetime.now().isoformat()
        }
    
    def execute_trade(self, analysis: Dict):
        """Execute trade based on analysis"""
        symbol = analysis['symbol']
        
        # Check if already have position
        if symbol in self.positions:
            return
        
        # Check max positions
        if len(self.positions) >= self.config['max_positions']:
            return
        
        # Check if should trade
        if not analysis['should_trade']:
            return
        
        # Determine direction
        if analysis['combined_signal'] == 1:
            direction = 'long'
        elif analysis['combined_signal'] == -1:
            direction = 'short'
        else:
            return
        
        # Calculate position size
        position_size = self.config['risk_per_trade']
        
        # Open position
        self.positions[symbol] = {
            'entry_price': analysis['current_price'],
            'entry_time': datetime.now(),
            'direction': direction,
            'size': position_size,
            'stop_loss': analysis['current_price'] * (1 - analysis['stop_loss_pct']) if direction == 'long'
                        else analysis['current_price'] * (1 + analysis['stop_loss_pct']),
            'take_profit': analysis['current_price'] * (1 + analysis['take_profit_pct']) if direction == 'long'
                          else analysis['current_price'] * (1 - analysis['take_profit_pct']),
            'ml_confidence': analysis['avg_confidence']
        }
        
        logger.info(f"🔥 OPENED {direction.upper()} {symbol} @ {analysis['current_price']:.5f} "
                   f"(Confidence: {analysis['avg_confidence']:.1%})")
    
    def check_positions(self):
        """Check and manage open positions"""
        for symbol in list(self.positions.keys()):
            if symbol not in self.market_data:
                continue
            
            position = self.positions[symbol]
            current_price = self.market_data[symbol]['close'].iloc[-1]
            
            # Check stop loss and take profit
            if position['direction'] == 'long':
                if current_price <= position['stop_loss']:
                    self.close_position(symbol, current_price, 'stop_loss')
                elif current_price >= position['take_profit']:
                    self.close_position(symbol, current_price, 'take_profit')
            else:
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
            'reason': reason,
            'ml_confidence': position['ml_confidence']
        }
        
        self.trades_history.append(trade)
        self.equity_curve.append(self.capital)
        
        profit_emoji = "💰" if pnl > 0 else "📉"
        logger.info(f"{profit_emoji} CLOSED {position['direction'].upper()} {symbol} @ {exit_price:.5f} | "
                   f"P&L: ${pnl:.2f} ({pnl_pct*100:.2f}%) | {reason}")
        
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
        
        if len(self.equity_curve) > 1:
            returns = pd.Series(self.equity_curve).pct_change().dropna()
            sharpe = np.sqrt(252) * returns.mean() / returns.std() if returns.std() > 0 else 0
        else:
            sharpe = 0
        
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
        """Save results"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        trades_file = self.log_dir / f'ultimate_trades_{timestamp}.json'
        with open(trades_file, 'w') as f:
            json.dump(self.trades_history, f, indent=2)
        
        metrics = self.get_performance_metrics()
        metrics_file = self.log_dir / f'ultimate_metrics_{timestamp}.json'
        with open(metrics_file, 'w') as f:
            json.dump(metrics, f, indent=2)
        
        logger.info(f"Results saved to {self.log_dir}")
    
    async def run_single_iteration(self):
        """Run one iteration"""
        # Update market data
        self.market_data = await self.data_fetcher.fetch_multiple_symbols(self.config['symbols'])
        
        # Check existing positions
        self.check_positions()
        
        # Analyze each symbol
        for symbol, data in self.market_data.items():
            if len(data) < 100:
                continue
            
            analysis = self.analyze_symbol(symbol, data)
            
            logger.info(f"📊 {symbol}: Strategy={analysis['strategy_signal']}, "
                       f"ML={analysis['ml_prediction']}({analysis['ml_confidence']:.0%}), "
                       f"DL={analysis['dl_prediction']}({analysis['dl_confidence']:.0%}), "
                       f"Combined={analysis['combined_signal']}, "
                       f"Trade={'YES' if analysis['should_trade'] else 'NO'}")
            
            # Execute trade
            if analysis['should_trade']:
                self.execute_trade(analysis)
        
        # Log performance
        metrics = self.get_performance_metrics()
        if 'total_return' in metrics:
            logger.info(f"💼 Performance: Return={metrics['total_return']:.2f}%, "
                       f"Trades={metrics['total_trades']}, "
                       f"Win Rate={metrics['win_rate']:.1f}%, "
                       f"Open={metrics['open_positions']}")
    
    async def run(self, iterations: int = None):
        """Run the ultimate bot"""
        await self.initialize()
        
        try:
            iteration = 0
            while iterations is None or iteration < iterations:
                await self.run_single_iteration()
                
                iteration += 1
                if iterations:
                    logger.info(f"⏱️  Iteration {iteration}/{iterations}")
                
                await asyncio.sleep(self.config['update_interval'])
                
        except KeyboardInterrupt:
            logger.info("Received shutdown signal")
        finally:
            await self.shutdown()


async def main():
    """Main function"""
    # Set UTF-8 encoding
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    
    print("="*70)
    print("🚀 ULTIMATE ALPHAALGO - ALL PHASES COMBINED")
    print("="*70)
    print("\n✅ Phase 2: Advanced ML (XGBoost, LightGBM, RF)")
    print("✅ Phase 3: Deep Learning (LSTM/Simple DL)")
    print("✅ Phase 4: Aggressive Strategy")
    print("✅ Phase 5: Multi-Model Ensemble")
    print("\n🔥 AGGRESSIVE MODE:")
    print("   - Strategy OR ML (not both required)")
    print("   - ML Confidence: 55% (lowered from 60%)")
    print("   - More frequent signals")
    print("   - Tighter stops, faster exits")
    print("\n" + "="*70)
    
    bot = UltimateAlphaAlgo(config={
        'symbols': ['EURUSD', 'GBPUSD', 'USDJPY', 'AUDUSD'],
        'initial_capital': 10000,
        'aggressive_mode': True,
        'min_ml_confidence': 0.55,
        'max_positions': 5,
        'update_interval': 5,
    })
    
    await bot.run(iterations=20)
    
    # Display results
    print("\n" + "="*70)
    print("FINAL RESULTS")
    print("="*70)
    
    metrics = bot.get_performance_metrics()
    if 'total_return' in metrics:
        print(f"\n💰 Total Return:     {metrics['total_return']:.2f}%")
        print(f"💵 Current Capital:  ${metrics['current_capital']:.2f}")
        print(f"📊 Total Trades:     {metrics['total_trades']}")
        print(f"✅ Winning Trades:   {metrics['winning_trades']}")
        print(f"❌ Losing Trades:    {metrics['losing_trades']}")
        print(f"🎯 Win Rate:         {metrics['win_rate']:.1f}%")
        print(f"💎 Profit Factor:    {metrics['profit_factor']:.2f}")
        print(f"📈 Sharpe Ratio:     {metrics['sharpe_ratio']:.2f}")
        print(f"📉 Max Drawdown:     {metrics['max_drawdown']:.2f}%")
        
        if metrics['total_trades'] > 0:
            print("\n🎉 TRADES EXECUTED!")
        if metrics['win_rate'] > 50:
            print("🏆 WIN RATE > 50%!")
    
    print("\n" + "="*70)


if __name__ == "__main__":
    asyncio.run(main())
