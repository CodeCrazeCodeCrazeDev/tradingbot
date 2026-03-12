"""
Backtest Parity Tool
Compares signal performance between historical and live data
"""

import numpy as np
import pandas as pd
from typing import Any, Dict, List, Optional, Tuple
from datetime import datetime, timedelta
import logging
import json
from pathlib import Path
import matplotlib.pyplot as plt
import asyncio
from dataclasses import dataclass

from trading_bot.models.data_models import MarketTick, OHLCBar, TradingSignal
from trading_bot.models.schema_integration import SchemaValidator
from trading_bot.database.data_normalizer import DataNormalizer
import numpy
import pandas

# Evolution: Added retry decorator
def retry(max_attempts=3, delay=1.0):
    """Retry decorator for resilient operations"""
    def decorator(func):
        async def wrapper(*args, **kwargs):
            last_error = None
            for attempt in range(max_attempts):
                try:
                    return await func(*args, **kwargs)
                except Exception as e:
                    last_error = e
                    if attempt < max_attempts - 1:
                        await asyncio.sleep(delay * (attempt + 1))
            raise last_error
        return wrapper
    return decorator



logger = logging.getLogger(__name__)

@dataclass
class ParityMetrics:
    """Metrics for backtest-live parity analysis"""
    signal_type: str
    backtest_signals: int = 0
    live_signals: int = 0
    matching_signals: int = 0
    recall: float = 0.0  # % of backtest signals found in live
    precision: float = 0.0  # % of live signals that match backtest
    backtest_win_rate: float = 0.0
    live_win_rate: float = 0.0
    win_rate_delta: float = 0.0
    backtest_avg_return: float = 0.0
    live_avg_return: float = 0.0
    return_delta: float = 0.0
    backtest_avg_slippage: float = 0.0
    live_avg_slippage: float = 0.0
    slippage_delta: float = 0.0

class BacktestParityAnalyzer:
    """
    Analyzes parity between backtest and live trading
    Features:
    - Signal recall and precision
    - Win rate comparison
    - Return comparison
    - Slippage analysis
    - Performance visualization
    """
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.backtest_signals: Dict[str, List[Dict[str, Any]]] = {}
        self.live_signals: Dict[str, List[Dict[str, Any]]] = {}
        self.backtest_trades: Dict[str, List[Dict[str, Any]]] = {}
        self.live_trades: Dict[str, List[Dict[str, Any]]] = {}
        
        # Matching parameters
        self.time_tolerance = config.get('time_tolerance', 60)  # seconds
        self.price_tolerance = config.get('price_tolerance', 0.0001)  # 1 pip
        
        # Create data directory
        Path("data/parity").mkdir(parents=True, exist_ok=True)
        
        logger.info("Backtest parity analyzer initialized")
    
    async def load_historical_data(self, symbol: str, start_date: datetime, end_date: datetime) -> pd.DataFrame:
        """Load historical data for backtesting"""
        # This would typically load from a database or file
        # For this example, we'll create a simple method
        
        logger.info(f"Loading historical data for {symbol} from {start_date} to {end_date}")
        
        # Check if we have cached data
        cache_file = f"data/parity/{symbol}_{start_date.strftime('%Y%m%d')}_{end_date.strftime('%Y%m%d')}.parquet"
        
        if Path(cache_file).exists():
            logger.info(f"Loading cached data from {cache_file}")
            return pd.read_parquet(cache_file)
        
        # In a real implementation, this would load from your historical database
        # For now, we'll create synthetic data
        
        # Create date range
        date_range = pd.date_range(start=start_date, end=end_date, freq='1min')
        
        # Create synthetic OHLC data
        data = []
        base_price = 1.2000 if symbol.startswith('EUR') else 100.50
        
        for timestamp in date_range:
            # Simple random walk
            price_change = np.random.normal(0, 0.0002)
            base_price += price_change
            
            # Create OHLC bar
            bar = {
                'timestamp': timestamp,
                'symbol': symbol,
                'open': base_price,
                'high': base_price * (1 + abs(np.random.normal(0, 0.0001))),
                'low': base_price * (1 - abs(np.random.normal(0, 0.0001))),
                'close': base_price + np.random.normal(0, 0.0001),
                'volume': np.random.randint(1, 100)
            }
            
            # Normalize data
            bar = DataNormalizer.normalize_ohlc_data(bar)
            data.append(bar)
        
        # Convert to DataFrame
        df = pd.DataFrame(data)
        
        # Save to cache
        df.to_parquet(cache_file)
        
        logger.info(f"Generated synthetic data with {len(df)} bars")
        return df
    
    async def run_backtest(self, symbol: str, start_date: datetime, end_date: datetime, analyzer):
        """
        Run backtest using historical data
        
        Args:
            symbol: Symbol to backtest
            start_date: Start date for backtest
            end_date: End date for backtest
            analyzer: Market analyzer instance
        """
        logger.info(f"Running backtest for {symbol} from {start_date} to {end_date}")
        
        # Load historical data
        historical_data = await self.load_historical_data(symbol, start_date, end_date)
        
        # Initialize analyzer
        await analyzer.initialize()
        
        # Process historical data
        signals = []
        trades = []
        
        for _, row in historical_data.iterrows():
            # Convert row to dict
            bar_data = row.to_dict()
            
            # Process through analyzer
            signal = await analyzer.process_tick(symbol, bar_data)
            
            if signal:
                # Validate signal
                signal_data = SchemaValidator.validate_trading_signal(signal)
                signals.append(signal_data)
                
                # Simulate trade execution
                trade = self._simulate_trade_execution(signal_data, bar_data)
                trades.append(trade)
        
        # Store results
        self.backtest_signals[symbol] = signals
        self.backtest_trades[symbol] = trades
        
        logger.info(f"Backtest completed with {len(signals)} signals and {len(trades)} trades")
    
    def _simulate_trade_execution(self, signal: Dict[str, Any], bar_data: Dict[str, Any]) -> Dict[str, Any]:
        """Simulate trade execution for backtest"""
        # Extract signal details
        entry_price = signal['entry_price']
        stop_loss = signal['stop_loss']
        take_profit = signal['take_profit']
        direction = signal['direction']
        
        # Simulate slippage
        slippage = np.random.normal(0, self.config.get('backtest_slippage', 0.0001))
        executed_price = entry_price * (1 + slippage)
        
        # Create trade
        trade = {
            'signal_id': signal.get('id', f"backtest_{datetime.now().timestamp()}"),
            'symbol': signal['symbol'],
            'direction': direction,
            'entry_time': signal['timestamp'],
            'entry_price': executed_price,
            'stop_loss': stop_loss,
            'take_profit': take_profit,
            'size': signal.get('size', 1.0),
            'slippage': executed_price - entry_price,
            'status': 'closed',
            'exit_time': signal['timestamp'] + timedelta(minutes=np.random.randint(5, 60)),
            'exit_price': 0,
            'pnl': 0,
            'exit_reason': ''
        }
        
        # Simulate outcome (simplified)
        if direction == 'buy':
            # 60% chance of hitting take profit, 40% chance of hitting stop loss
            if np.random.random() < 0.6:
                trade['exit_price'] = take_profit
                trade['pnl'] = (take_profit - executed_price) * trade['size']
                trade['exit_reason'] = 'take_profit'
            else:
                trade['exit_price'] = stop_loss
                trade['pnl'] = (stop_loss - executed_price) * trade['size']
                trade['exit_reason'] = 'stop_loss'
        else:  # sell
            if np.random.random() < 0.6:
                trade['exit_price'] = take_profit
                trade['pnl'] = (executed_price - take_profit) * trade['size']
                trade['exit_reason'] = 'take_profit'
            else:
                trade['exit_price'] = stop_loss
                trade['pnl'] = (executed_price - stop_loss) * trade['size']
                trade['exit_reason'] = 'stop_loss'
        
        return trade
    
    def record_live_signal(self, signal: Dict[str, Any]):
        """Record a live trading signal"""
        # Validate signal
        signal_data = SchemaValidator.validate_trading_signal(signal)
        
        # Get symbol
        symbol = signal_data['symbol']
        
        # Initialize if needed
        if symbol not in self.live_signals:
            self.live_signals[symbol] = []
        
        # Store signal
        self.live_signals[symbol].append(signal_data)
        
        logger.debug(f"Recorded live signal for {symbol}")
    
    def record_live_trade(self, trade: Dict[str, Any]):
        """Record a live trade execution"""
        # Get symbol
        symbol = trade['symbol']
        
        # Initialize if needed
        if symbol not in self.live_trades:
            self.live_trades[symbol] = []
        
        # Store trade
        self.live_trades[symbol].append(trade)
        
        logger.debug(f"Recorded live trade for {symbol}")
    
    def analyze_parity(self, symbol: str) -> ParityMetrics:
        """
        Analyze parity between backtest and live trading
        
        Args:
            symbol: Symbol to analyze
            
        Returns:
            Parity metrics
        """
        logger.info(f"Analyzing parity for {symbol}")
        
        # Check if we have data
        if (symbol not in self.backtest_signals or not self.backtest_signals[symbol] or
            symbol not in self.live_signals or not self.live_signals[symbol]):
            logger.warning(f"Insufficient data for parity analysis of {symbol}")
            return ParityMetrics(signal_type=symbol)
        
        # Get signals
        backtest_signals = self.backtest_signals[symbol]
        live_signals = self.live_signals[symbol]
        
        # Get trades
        backtest_trades = self.backtest_trades.get(symbol, [])
        live_trades = self.live_trades.get(symbol, [])
        
        # Match signals
        matching_signals = self._match_signals(backtest_signals, live_signals)
        
        # Calculate metrics
        metrics = ParityMetrics(signal_type=symbol)
        metrics.backtest_signals = len(backtest_signals)
        metrics.live_signals = len(live_signals)
        metrics.matching_signals = len(matching_signals)
        
        # Calculate recall and precision
        metrics.recall = len(matching_signals) / len(backtest_signals) if backtest_signals else 0
        metrics.precision = len(matching_signals) / len(live_signals) if live_signals else 0
        
        # Calculate win rates
        backtest_wins = sum(1 for t in backtest_trades if t.get('pnl', 0) > 0)
        live_wins = sum(1 for t in live_trades if t.get('pnl', 0) > 0)
        
        metrics.backtest_win_rate = backtest_wins / len(backtest_trades) if backtest_trades else 0
        metrics.live_win_rate = live_wins / len(live_trades) if live_trades else 0
        metrics.win_rate_delta = metrics.live_win_rate - metrics.backtest_win_rate
        
        # Calculate average returns
        metrics.backtest_avg_return = np.mean([t.get('pnl', 0) for t in backtest_trades]) if backtest_trades else 0
        metrics.live_avg_return = np.mean([t.get('pnl', 0) for t in live_trades]) if live_trades else 0
        metrics.return_delta = metrics.live_avg_return - metrics.backtest_avg_return
        
        # Calculate average slippage
        metrics.backtest_avg_slippage = np.mean([abs(t.get('slippage', 0)) for t in backtest_trades]) if backtest_trades else 0
        metrics.live_avg_slippage = np.mean([abs(t.get('slippage', 0)) for t in live_trades]) if live_trades else 0
        metrics.slippage_delta = metrics.live_avg_slippage - metrics.backtest_avg_slippage
        
        logger.info(f"Parity analysis for {symbol}: Recall={metrics.recall:.2f}, Precision={metrics.precision:.2f}")
        return metrics
    
    def _match_signals(self, backtest_signals: List[Dict[str, Any]], live_signals: List[Dict[str, Any]]) -> List[Tuple[Dict[str, Any], Dict[str, Any]]]:
        """Match backtest signals with live signals"""
        matches = []
        
        for bt_signal in backtest_signals:
            bt_time = bt_signal['timestamp']
            bt_price = bt_signal['entry_price']
            bt_direction = bt_signal['direction']
            
            # Find matching live signals
            for live_signal in live_signals:
                live_time = live_signal['timestamp']
                live_price = live_signal['entry_price']
                live_direction = live_signal['direction']
                
                # Check if signals match
                time_diff = abs((live_time - bt_time).total_seconds())
                price_diff = abs(live_price - bt_price)
                
                if (time_diff <= self.time_tolerance and
                    price_diff <= self.price_tolerance and
                    bt_direction == live_direction):
                    matches.append((bt_signal, live_signal))
                    break  # Match found, move to next backtest signal
        
        return matches
    
    def generate_parity_report(self, symbols: List[str]):
        """Generate parity report for multiple symbols"""
        logger.info(f"Generating parity report for {len(symbols)} symbols")
        
        # Create report directory
        Path("reports/parity").mkdir(parents=True, exist_ok=True)
        
        # Analyze parity for each symbol
        metrics = {}
        for symbol in symbols:
            metrics[symbol] = self.analyze_parity(symbol)
        
        # Generate plots
        self._generate_parity_plots(metrics)
        
        # Generate summary report
        self._generate_parity_summary(metrics)
        
        logger.info("Parity report generated")
    
    def _generate_parity_plots(self, metrics: Dict[str, ParityMetrics]):
        """Generate parity visualization plots"""
        # Create figure with subplots
        fig, axs = plt.subplots(2, 2, figsize=(15, 12))
        
        # Get symbols
        symbols = list(metrics.keys())
        
        # Plot 1: Recall and Precision
        ax1 = axs[0, 0]
        recalls = [metrics[s].recall for s in symbols]
        precisions = [metrics[s].precision for s in symbols]
        
        x = np.arange(len(symbols))
        width = 0.35
        
        ax1.bar(x - width/2, recalls, width, label='Recall')
        ax1.bar(x + width/2, precisions, width, label='Precision')
        
        ax1.set_title('Signal Recall and Precision')
        ax1.set_ylabel('Score')
        ax1.set_xticks(x)
        ax1.set_xticklabels(symbols)
        ax1.set_ylim(0, 1)
        ax1.legend()
        ax1.grid(axis='y')
        
        # Plot 2: Win Rate Comparison
        ax2 = axs[0, 1]
        bt_win_rates = [metrics[s].backtest_win_rate for s in symbols]
        live_win_rates = [metrics[s].live_win_rate for s in symbols]
        
        ax2.bar(x - width/2, bt_win_rates, width, label='Backtest')
        ax2.bar(x + width/2, live_win_rates, width, label='Live')
        
        ax2.set_title('Win Rate Comparison')
        ax2.set_ylabel('Win Rate')
        ax2.set_xticks(x)
        ax2.set_xticklabels(symbols)
        ax2.set_ylim(0, 1)
        ax2.legend()
        ax2.grid(axis='y')
        
        # Plot 3: Average Return Comparison
        ax3 = axs[1, 0]
        bt_returns = [metrics[s].backtest_avg_return for s in symbols]
        live_returns = [metrics[s].live_avg_return for s in symbols]
        
        ax3.bar(x - width/2, bt_returns, width, label='Backtest')
        ax3.bar(x + width/2, live_returns, width, label='Live')
        
        ax3.set_title('Average Return Comparison')
        ax3.set_ylabel('Return')
        ax3.set_xticks(x)
        ax3.set_xticklabels(symbols)
        ax3.legend()
        ax3.grid(axis='y')
        
        # Plot 4: Slippage Comparison
        ax4 = axs[1, 1]
        bt_slippage = [metrics[s].backtest_avg_slippage for s in symbols]
        live_slippage = [metrics[s].live_avg_slippage for s in symbols]
        
        ax4.bar(x - width/2, bt_slippage, width, label='Backtest')
        ax4.bar(x + width/2, live_slippage, width, label='Live')
        
        ax4.set_title('Average Slippage Comparison')
        ax4.set_ylabel('Slippage')
        ax4.set_xticks(x)
        ax4.set_xticklabels(symbols)
        ax4.legend()
        ax4.grid(axis='y')
        
        # Adjust layout and save
        plt.tight_layout()
        plt.savefig("reports/parity/parity_comparison.png")
        plt.close()
    
    def _generate_parity_summary(self, metrics: Dict[str, ParityMetrics]):
        """Generate parity summary report"""
        # Calculate average metrics
        avg_recall = np.mean([m.recall for m in metrics.values()])
        avg_precision = np.mean([m.precision for m in metrics.values()])
        avg_win_rate_delta = np.mean([m.win_rate_delta for m in metrics.values()])
        avg_return_delta = np.mean([m.return_delta for m in metrics.values()])
        avg_slippage_delta = np.mean([m.slippage_delta for m in metrics.values()])
        
        # Create summary
        summary = {
            'timestamp': datetime.now(),
            'symbols_analyzed': list(metrics.keys()),
            'average_metrics': {
                'recall': avg_recall,
                'precision': avg_precision,
                'win_rate_delta': avg_win_rate_delta,
                'return_delta': avg_return_delta,
                'slippage_delta': avg_slippage_delta
            },
            'symbol_metrics': {
                symbol: {
                    'recall': m.recall,
                    'precision': m.precision,
                    'backtest_win_rate': m.backtest_win_rate,
                    'live_win_rate': m.live_win_rate,
                    'win_rate_delta': m.win_rate_delta,
                    'backtest_avg_return': m.backtest_avg_return,
                    'live_avg_return': m.live_avg_return,
                    'return_delta': m.return_delta,
                    'backtest_avg_slippage': m.backtest_avg_slippage,
                    'live_avg_slippage': m.live_avg_slippage,
                    'slippage_delta': m.slippage_delta
                }
                for symbol, m in metrics.items()
            }
        }
        
        # Save summary
        with open('reports/parity/parity_summary.json', 'w') as f:
            json.dump(summary, f, indent=2, default=str)
        
        # Generate markdown report
        md_report = f"""# Backtest-Live Parity Report
Generated: {datetime.now()}

## Overall Metrics
- Average Recall: {avg_recall:.2%}
- Average Precision: {avg_precision:.2%}
- Average Win Rate Delta: {avg_win_rate_delta:.2%}
- Average Return Delta: {avg_return_delta:.4f}
- Average Slippage Delta: {avg_slippage_delta:.6f}

## Symbol Analysis
"""
        
        # Add symbol metrics
        for symbol, m in metrics.items():
            md_report += f"""
### {symbol}
- Signal Recall: {m.recall:.2%}
- Signal Precision: {m.precision:.2%}
- Backtest Win Rate: {m.backtest_win_rate:.2%}
- Live Win Rate: {m.live_win_rate:.2%}
- Win Rate Delta: {m.win_rate_delta:.2%}
- Backtest Avg Return: {m.backtest_avg_return:.4f}
- Live Avg Return: {m.live_avg_return:.4f}
- Return Delta: {m.return_delta:.4f}
- Backtest Avg Slippage: {m.backtest_avg_slippage:.6f}
- Live Avg Slippage: {m.live_avg_slippage:.6f}
- Slippage Delta: {m.slippage_delta:.6f}
"""
        
        # Add interpretation
        md_report += """
## Interpretation Guide

### Recall and Precision
- **Recall**: Percentage of backtest signals that were also generated in live trading
- **Precision**: Percentage of live signals that match backtest signals
- *Target*: Both should be >80% for reliable strategy transfer

### Win Rate Delta
- Difference between live and backtest win rates
- *Target*: Should be within ±5% for reliable performance

### Return Delta
- Difference between live and backtest average returns
- *Target*: Should be within ±10% of backtest returns

### Slippage Delta
- Difference between live and backtest average slippage
- *Target*: Should be within 1-2 pips for FX instruments
"""
        
        # Save markdown report
        with open('reports/parity/parity_report.md', 'w') as f:
            f.write(md_report)
