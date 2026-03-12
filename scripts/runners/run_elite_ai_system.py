"""
Elite AI Trading System - Main Runner

This script runs the Elite Professional Trading and Advanced Market Analysis AI System
with automated Slow Inference for deep trading analysis.

Usage:
    python run_elite_ai_system.py [--symbol SYMBOL] [--mode MODE] [--depth DEPTH]

Arguments:
    --symbol: Trading symbol (default: EURUSD)
    --mode: Trading mode - paper, live, backtest (default: paper)
    --depth: Analysis depth - quick, standard, deep, exhaustive (default: deep)
    --continuous: Run in continuous mode
    --interval: Analysis interval in seconds (default: 60)
"""

import asyncio
import argparse
import logging
import sys
import signal
from datetime import datetime
from typing import Dict, Any, List
import numpy as np

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(f'elite_ai_system_{datetime.now().strftime("%Y%m%d")}.log')
    ]
)
logger = logging.getLogger(__name__)

# Import Elite AI System
try:
    from trading_bot.elite_ai_system import (
        EliteTradingOrchestrator,
        AnalysisDepth,
        SystemStatus
    )
    SYSTEM_AVAILABLE = True
except ImportError as e:
    logger.error(f"Failed to import Elite AI System: {e}")
    SYSTEM_AVAILABLE = False


def generate_sample_market_data(symbol: str, periods: int = 100) -> Dict[str, Any]:
    """Generate sample market data for testing"""
    np.random.seed(42)
    
    # Generate realistic price data
    base_price = 1.1000 if 'EUR' in symbol else 100.0
    returns = np.random.normal(0.0001, 0.001, periods)
    prices = [base_price]
    for r in returns:
        prices.append(prices[-1] * (1 + r))
    
    # Generate volume data
    base_volume = 1000000
    volumes = [base_volume * (1 + np.random.uniform(-0.3, 0.5)) for _ in range(len(prices))]
    
    # Generate indicators
    price_array = np.array(prices)
    indicators = {
        'rsi': 50 + np.random.uniform(-20, 20),
        'macd': {
            'macd': np.random.uniform(-0.001, 0.001),
            'signal': np.random.uniform(-0.001, 0.001),
            'histogram': np.random.uniform(-0.0005, 0.0005)
        },
        'ma_fast': np.mean(price_array[-10:]),
        'ma_slow': np.mean(price_array[-20:]),
        'atr': np.std(np.diff(price_array)) * 2
    }
    
    return {
        'symbol': symbol,
        'timeframe': 'H1',
        'prices': prices,
        'volumes': volumes,
        'indicators': indicators,
        'timestamp': datetime.now().isoformat()
    }


def generate_sample_context() -> Dict[str, Any]:
    """Generate sample context data"""
    return {
        'news_sentiment': np.random.uniform(-0.3, 0.3),
        'social_sentiment': np.random.uniform(-0.2, 0.2),
        'market_regime': np.random.choice(['trending_up', 'trending_down', 'ranging']),
        'correlations': {
            'strength': np.random.uniform(0.3, 0.8),
            'breakdown': False
        },
        'news': [],
        'upcoming_events': []
    }


async def run_single_analysis(
    orchestrator: EliteTradingOrchestrator,
    symbol: str,
    depth: AnalysisDepth
) -> Dict[str, Any]:
    """Run a single analysis cycle"""
    logger.info(f"Running {depth.value} analysis for {symbol}")
    
    # Generate market data
    market_data = generate_sample_market_data(symbol)
    context = generate_sample_context()
    
    # Run analysis
    decision = await orchestrator.analyze_and_decide(
        symbol=symbol,
        market_data=market_data,
        context=context,
        depth=depth
    )
    
    # Log results
    logger.info(f"Decision: {decision.action} with {decision.confidence:.2%} confidence")
    logger.info(f"Reasoning: {decision.reasoning_summary}")
    
    if decision.warnings:
        for warning in decision.warnings:
            logger.warning(f"Warning: {warning}")
    
    return decision.to_dict()


async def run_continuous(
    orchestrator: EliteTradingOrchestrator,
    symbol: str,
    depth: AnalysisDepth,
    interval: int
):
    """Run continuous analysis loop"""
    logger.info(f"Starting continuous analysis for {symbol} every {interval} seconds")
    
    await orchestrator.start()
    
    try:
        while orchestrator.is_running:
            try:
                result = await run_single_analysis(orchestrator, symbol, depth)
                
                # Print summary
                print("\n" + "="*60)
                print(f"ANALYSIS RESULT - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
                print("="*60)
                print(f"Symbol: {result['symbol']}")
                print(f"Action: {result['action']}")
                print(f"Confidence: {result['confidence']:.2%}")
                print(f"Entry: {result['entry_price']}")
                print(f"Stop Loss: {result['stop_loss']}")
                print(f"Take Profit: {result['take_profit']}")
                print(f"Position Size: {result['position_size_pct']:.2f}%")
                print(f"R:R Ratio: {result['risk_reward_ratio']:.2f}")
                print(f"Expected Value: {result['expected_value']:.4f}")
                print("-"*60)
                print(f"Reasoning: {result['reasoning_summary']}")
                print("="*60 + "\n")
                
                # Wait for next cycle
                await asyncio.sleep(interval)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Analysis error: {e}")
                await asyncio.sleep(interval)
                
    finally:
        await orchestrator.stop()


async def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description='Elite AI Trading System')
    parser.add_argument('--symbol', type=str, default='EURUSD', help='Trading symbol')
    parser.add_argument('--mode', type=str, default='paper', choices=['paper', 'live', 'backtest'])
    parser.add_argument('--depth', type=str, default='deep', 
                       choices=['quick', 'standard', 'deep', 'exhaustive'])
    parser.add_argument('--continuous', action='store_true', help='Run in continuous mode')
    parser.add_argument('--interval', type=int, default=60, help='Analysis interval in seconds')
    
    args = parser.parse_args()
    
    if not SYSTEM_AVAILABLE:
        logger.error("Elite AI System not available. Please check imports.")
        sys.exit(1)
    
    print("\n" + "="*60)
    print("ELITE AI TRADING SYSTEM")
    print("Professional Trading & Advanced Market Analysis")
    print("="*60)
    print(f"Symbol: {args.symbol}")
    print(f"Mode: {args.mode}")
    print(f"Analysis Depth: {args.depth}")
    print(f"Continuous: {args.continuous}")
    print("="*60 + "\n")
    
    # Initialize orchestrator
    config = {
        'trading_mode': args.mode,
        'default_depth': args.depth,
        'min_confidence': 0.7,
        'min_validation_score': 0.7,
        'inference': {
            'default_depth': args.depth,
            'min_confidence': 0.7,
            'monte_carlo_iterations': 1000
        },
        'growth': {
            'initial_capital': 10000,
            'base_risk_pct': 0.5,
            'max_risk_pct': 2.0
        },
        'emergency': {
            'volatility_critical': 0.05,
            'flash_crash_threshold': 0.05
        }
    }
    
    orchestrator = EliteTradingOrchestrator(config)
    depth = AnalysisDepth(args.depth)
    
    # Handle shutdown
    def signal_handler(sig, frame):
        logger.info("Shutdown signal received")
        orchestrator.is_running = False
    
    signal.signal(signal.SIGINT, signal_handler)
    
    try:
        if args.continuous:
            await run_continuous(orchestrator, args.symbol, depth, args.interval)
        else:
            result = await run_single_analysis(orchestrator, args.symbol, depth)
            
            print("\n" + "="*60)
            print("ANALYSIS RESULT")
            print("="*60)
            for key, value in result.items():
                if key != 'timestamp':
                    print(f"{key}: {value}")
            print("="*60 + "\n")
            
    except KeyboardInterrupt:
        logger.info("Interrupted by user")
    except Exception as e:
        logger.error(f"Error: {e}")
        raise


if __name__ == '__main__':
    asyncio.run(main())
