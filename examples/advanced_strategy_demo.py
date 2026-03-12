"""
Advanced Strategy Demo with Performance Tracking
"""

import asyncio
import logging
from datetime import datetime, timedelta
import pandas as pd
import numpy as np
import json
import os

from trading_bot.strategies.advanced_strategies import (
    AlternativeDataStrategy,
    MultiTimeframeRLStrategy,
    MarketRegimeStrategy
)
from trading_bot.dashboard.strategy_dashboard import StrategyDashboard
from typing import Any
import numpy
import pandas

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def run_strategy_demo():
    """Run advanced strategy demo with performance tracking"""
    
    # Initialize dashboard
    dashboard = StrategyDashboard({
        'port': 8050,
        'update_interval': 5,  # 5 seconds
        'anomaly_detector': {
            'z_score_threshold': 3.0,
            'min_history_points': 10
        }
    })
    
    # Start dashboard
    dashboard.start()
    
    # Initialize strategies
    strategies = {
        'AlternativeData': AlternativeDataStrategy({
            'symbols': ['AAPL', 'MSFT', 'GOOGL'],
            'timeframes': ['1h', '4h', '1d'],
            'account_size': 1000000,  # $1M account
            'risk_config': {
                'max_position_size': 0.1,  # 10% max position
                'max_risk_per_trade': 0.02  # 2% risk per trade
            }
        }),
        'MultiTimeframeRL': MultiTimeframeRLStrategy({
            'symbols': ['AAPL', 'MSFT', 'GOOGL'],
            'timeframes': ['5m', '15m', '1h', '4h'],
            'account_size': 1000000,
            'risk_config': {
                'max_position_size': 0.15,
                'max_risk_per_trade': 0.02
            }
        }),
        'MarketRegime': MarketRegimeStrategy({
            'symbols': ['AAPL', 'MSFT', 'GOOGL'],
            'timeframes': ['5m', '15m', '1h'],
            'account_size': 1000000,
            'risk_config': {
                'max_position_size': 0.12,
                'max_risk_per_trade': 0.02
            }
        })
    }
    
    # Add strategies to dashboard
    for name, strategy in strategies.items():
        dashboard.add_strategy(name)
    
    try:
        # Run strategies for demo period
        start_time = datetime.now()
        end_time = start_time + timedelta(minutes=30)  # 30-minute demo
        
        while datetime.now() < end_time:
            for name, strategy in strategies.items():
                try:
                    # Generate signals
                    signals = await strategy.generate_signals()
                    
                    # Process each signal
                    for signal in signals:
                        # Add signal to dashboard
                        dashboard.add_signal(name, signal.to_dict())
                        
                        # Simulate trade execution and outcome
                        trade_result = simulate_trade(signal)
                        
                        # Update strategy performance
                        strategy.update_performance(trade_result)
                        
                        # Update dashboard metrics
                        update_dashboard_metrics(dashboard, name, strategy, trade_result)
                    
                except Exception as e:
                    logger.error(f"Error in strategy {name}: {e}")
            
            # Wait before next iteration
            await asyncio.sleep(5)
        
        # Final performance update
        for name, strategy in strategies.items():
            final_metrics = calculate_final_metrics(strategy)
            dashboard.update_strategy(name, final_metrics)
        
        logger.info("Strategy demo completed successfully")
        
        # Keep dashboard running
        while True:
            await asyncio.sleep(1)
    
    except KeyboardInterrupt:
        logger.info("Demo stopped by user")
    except Exception as e:
        logger.error(f"Error in demo: {e}")
    finally:
        # Save performance data
        save_performance_data(strategies)


def simulate_trade(signal) -> dict:
    """
    Simulate trade execution and outcome
    
    In a real implementation, this would execute trades through a broker
    and track actual performance. Here we simulate outcomes for demo purposes.
    """
    # Simulate trade execution
    entry_price = signal.entry_price
    
    # Simulate price movement (random walk with drift based on signal)
    drift = 0.001 if signal.signal_type == 'long' else -0.001
    price_change = np.random.normal(drift, 0.002)  # 0.2% volatility
    
    # Calculate exit price
    exit_price = entry_price * (1 + price_change)
    
    # Calculate profit/loss
    profit = (exit_price - entry_price) * signal.size if signal.signal_type == 'long' else (entry_price - exit_price) * signal.size
    
    # Create trade result
    return {
        'symbol': signal.symbol,
        'entry_time': signal.timestamp,
        'exit_time': signal.timestamp + timedelta(minutes=5),
        'signal_type': signal.signal_type,
        'entry_price': entry_price,
        'exit_price': exit_price,
        'size': signal.size,
        'profit': profit,
        'return': profit / (entry_price * signal.size),
        'confidence': signal.confidence,
        'timeframe': signal.timeframe,
        'source': signal.source,
        'metadata': signal.metadata
    }


def update_dashboard_metrics(dashboard: StrategyDashboard, 
                           strategy_name: str, 
                           strategy: Any,
                           trade_result: dict):
    """Update dashboard with latest metrics"""
    # Get current metrics
    metrics = strategy.performance_metrics
    
    # Update equity and drawdown
    equity = metrics.get('equity', 1000000)  # Start with $1M
    equity += trade_result['profit']
    peak_equity = max(metrics.get('peak_equity', equity), equity)
    drawdown = (peak_equity - equity) / peak_equity if peak_equity > 0 else 0
    
    # Update dashboard
    dashboard.update_strategy(strategy_name, {
        'equity': equity,
        'drawdown': drawdown,
        'total_return': (equity - 1000000) / 1000000,
        'win_rate': metrics.get('win_rate', 0),
        'profit_factor': metrics.get('profit_factor', 0),
        'sharpe_ratio': metrics.get('sharpe_ratio', 0),
        'max_drawdown': metrics.get('max_drawdown', 0),
        'recovery_factor': metrics.get('recovery_factor', 0),
        'avg_trade': metrics.get('avg_trade', 0),
        'alpha': metrics.get('alpha', 0)
    })


def calculate_final_metrics(strategy: Any) -> dict:
    """Calculate final performance metrics for a strategy"""
    metrics = strategy.performance_metrics
    
    return {
        'total_return': metrics.get('total_return', 0),
        'sharpe_ratio': metrics.get('sharpe_ratio', 0),
        'win_rate': metrics.get('win_rate', 0),
        'profit_factor': metrics.get('profit_factor', 0),
        'max_drawdown': metrics.get('max_drawdown', 0),
        'recovery_factor': metrics.get('recovery_factor', 0),
        'avg_trade': metrics.get('avg_trade', 0),
        'alpha': metrics.get('alpha', 0),
        'total_trades': len(strategy.trades),
        'final_equity': metrics.get('equity', 1000000)
    }


def save_performance_data(strategies: dict):
    """Save performance data to file"""
    # Create data directory if it doesn't exist
    os.makedirs('data', exist_ok=True)
    
    # Save performance data for each strategy
    for name, strategy in strategies.items():
        data = {
            'trades': [t for t in strategy.trades if isinstance(t.get('timestamp'), str)],
            'metrics': strategy.performance_metrics,
            'signals': [s.to_dict() for s in strategy.signal_history]
        }
        
        file_path = f'data/{name.lower()}_performance.json'
        
        with open(file_path, 'w') as f:
            json.dump(data, f, indent=2)
        
        logger.info(f"Saved performance data for {name} to {file_path}")


if __name__ == "__main__":
    # Run demo
    asyncio.run(run_strategy_demo())
