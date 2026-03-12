"""Lightweight real-time trading bot runner.

Connects directly to MT5 for real-time data and runs the trading loop
without loading all 185+ optional modules (which can hang on import).

Usage:
    py run_realtime.py
    py run_realtime.py --symbol GBPUSD --timeframe M5
    py run_realtime.py --symbol EURUSD --timeframe M15 --use-ml
"""
from __future__ import annotations

import sys
import asyncio
import argparse
import signal
from datetime import datetime

# Fix Windows console encoding
if sys.platform == 'win32':
    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
        sys.stderr.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        pass

import pandas as pd
import numpy as np
from loguru import logger

# Configure loguru
logger.remove()
logger.add(
    sys.stderr,
    format="<green>{time:HH:mm:ss}</green> | <level>{level: <7}</level> | <level>{message}</level>",
    level="INFO",
    colorize=True,
)

# Core imports only
from trading_bot.data.mt5_interface import MT5Interface
from trading_bot.strategy import StrategyEngine, MLStrategyEngine
from trading_bot.execution.paper_executor import PaperExecutor
from trading_bot.risk import RiskManager
from trading_bot.utils.safe_access import safe_get


def parse_args():
    p = argparse.ArgumentParser(description="Real-time Trading Bot (lightweight)")
    p.add_argument("--symbol", default="EURUSD", help="Trading symbol (default: EURUSD)")
    p.add_argument("--timeframe", default="M15", help="Timeframe (M1,M5,M15,H1,H4,D1)")
    p.add_argument("--bars", type=int, default=200, help="Number of bars to fetch")
    p.add_argument("--use-ml", action="store_true", help="Use ML strategy engine")
    p.add_argument("--interval", type=int, default=5, help="Loop interval in seconds")
    return p.parse_args()


async def main():
    args = parse_args()
    symbol = args.symbol
    timeframe = args.timeframe
    bars = args.bars
    interval = args.interval

    logger.info("=" * 65)
    logger.info("  ALPHAALGO REAL-TIME TRADING BOT")
    logger.info("=" * 65)
    logger.info("Symbol: {} | Timeframe: {} | Bars: {}", symbol, timeframe, bars)
    logger.info("Strategy: {} | Mode: PAPER", "ML-Enhanced" if args.use_ml else "Technical")
    logger.info("=" * 65)

    # Connect to MT5
    logger.info("Connecting to MetaTrader 5...")
    with MT5Interface() as mt5i:
        # Show account info
        acct = mt5i.account_info()
        logger.success("Connected to MT5")
        logger.info("Account: {} | Server: {}", acct.login, acct.server)
        logger.info("Balance: ${:,.2f} | Equity: ${:,.2f}", acct.balance, acct.equity)

        # Get current price
        price = mt5i.get_current_price(symbol)
        logger.info("Current {}: Bid={:.5f} Ask={:.5f}", symbol, price['bid'], price['ask'])

        # Create strategy engine
        if args.use_ml:
            strategy = MLStrategyEngine(
                mt5i, symbol=symbol,
                use_price_prediction=True,
                use_pattern_recognition=True,
                use_sentiment=False,
            )
            logger.info("ML Strategy Engine initialized")
        else:
            strategy = StrategyEngine(mt5i, symbol=symbol)
            logger.info("Technical Strategy Engine initialized")

        # Create risk manager and executor
        risk_mgr = RiskManager(mt5i)
        executor = PaperExecutor(mt5i, risk_mgr)
        logger.info("Risk Manager and Paper Executor initialized")

        # Trading stats
        stats = {
            'cycles': 0, 'signals': 0, 'trades': 0,
            'skipped': 0, 'errors': 0, 'start_time': datetime.now(),
        }

        # Graceful shutdown
        shutdown = False

        def on_signal(signum, frame):
            nonlocal shutdown
            logger.warning("Shutdown signal received ({})", signum)
            shutdown = True

        signal.signal(signal.SIGINT, on_signal)
        signal.signal(signal.SIGTERM, on_signal)

        logger.info("")
        logger.info(">>> Trading loop STARTED - Press Ctrl+C to stop <<<")
        logger.info("")

        while not shutdown:
            stats['cycles'] += 1
            cycle = stats['cycles']

            try:
                # 1. Fetch real-time market data
                rates = mt5i.get_rates(symbol, timeframe=timeframe, count=bars)
                if rates is None or len(rates) == 0:
                    logger.warning("[Cycle {}] No market data - retrying in {}s", cycle, interval)
                    await asyncio.sleep(interval)
                    continue

                # Build DataFrame from numpy structured array
                df = pd.DataFrame(rates)
                # Rename columns if needed (MT5 returns: time,open,high,low,close,tick_volume,spread,real_volume)
                if 'tick_volume' in df.columns:
                    df.rename(columns={'tick_volume': 'volume'}, inplace=True)
                if 'time' in df.columns:
                    df['time'] = pd.to_datetime(df['time'], unit='s')
                    df.set_index("time", inplace=True)

                last_close = float(df['close'].iloc[-1])
                prev_close = float(df['close'].iloc[-2]) if len(df) > 1 else last_close
                change_pct = ((last_close - prev_close) / prev_close * 100) if prev_close else 0
                volatility = float(df['close'].pct_change().std()) if len(df) > 10 else 0.01

                # Get live bid/ask
                tick = mt5i.get_current_price(symbol)
                spread_pips = (tick['ask'] - tick['bid']) * 10000  # for 4/5 digit pairs

                # 2. Generate signals
                if hasattr(strategy, 'generate_signals'):
                    signals = await strategy.generate_signals()
                else:
                    signals = strategy.analyse(df)

                # 3. Evaluate signal confidence
                signal_confidence = 0.0
                signal_direction = "HOLD"

                def _get_attr(obj, key, default=0.0):
                    """Get attribute from dict or object."""
                    if isinstance(obj, dict):
                        return obj.get(key, default)
                    return getattr(obj, key, default)

                if isinstance(signals, dict):
                    signal_confidence = signals.get('confidence', signals.get('strength', 0.0))
                    signal_direction = signals.get('action', signals.get('direction', 'HOLD'))
                elif isinstance(signals, list) and signals:
                    best = max(signals, key=lambda s: _get_attr(s, 'confidence', 0))
                    signal_confidence = _get_attr(best, 'confidence', 0.0)
                    signal_direction = _get_attr(best, 'direction', _get_attr(best, 'action', 'HOLD'))
                    stop_loss_pips = _get_attr(best, 'stop_loss_pips', 20)

                # Normalize confidence: if > 1 assume 0-100 scale
                if signal_confidence > 1.0:
                    signal_confidence = signal_confidence / 100.0

                # 4. Log cycle info
                direction_icon = {"BUY": "^", "SELL": "v", "LONG": "^", "SHORT": "v"}.get(
                    str(signal_direction).upper(), "-"
                )
                logger.info(
                    "[Cycle {:>4}] {} Bid={:.5f} Ask={:.5f} Spread={:.1f}p | "
                    "Chg={:+.3f}% Vol={:.4f} | Signal: {} {:.0f}% {}",
                    cycle, symbol, tick['bid'], tick['ask'], spread_pips,
                    change_pct, volatility,
                    direction_icon, signal_confidence * 100,
                    signal_direction,
                )

                # 5. Trade if confidence is high enough
                MIN_CONFIDENCE = 0.6
                if signal_confidence >= MIN_CONFIDENCE and str(signal_direction).upper() in (
                    "BUY", "SELL", "LONG", "SHORT"
                ):
                    stats['signals'] += 1

                    # Position sizing
                    stop_loss_pips = 20
                    if isinstance(signals, dict):
                        stop_loss_pips = signals.get('stop_loss_pips', 20)
                    elif isinstance(signals, list) and signals:
                        stop_loss_pips = safe_get(signals[0], 'stop_loss_pips', 20)

                    try:
                        position = risk_mgr.calculate_position_size(
                            symbol=symbol, stop_loss_pips=stop_loss_pips
                        )
                        lot_size = getattr(position, 'lot', position) if position else 0
                        if lot_size and lot_size != 0:
                            direction = 1 if str(signal_direction).upper() in ("BUY", "LONG") else -1
                            await executor.execute_trade(
                                symbol=symbol,
                                direction=direction,
                                size=abs(lot_size) if not isinstance(lot_size, (int, float)) else abs(lot_size),
                            )
                            stats['trades'] += 1
                            logger.success(
                                "  >>> TRADE EXECUTED: {} {} {:.2f} lots @ {:.5f} (SL: {}p, Conf: {:.0f}%)",
                                "BUY" if direction > 0 else "SELL",
                                symbol, abs(lot_size) if isinstance(lot_size, (int, float)) else lot_size,
                                last_close, stop_loss_pips, signal_confidence * 100,
                            )
                        else:
                            stats['skipped'] += 1
                    except Exception as e:
                        logger.warning("  Position sizing error: {}", e)
                        stats['errors'] += 1
                else:
                    stats['skipped'] += 1

                # 6. Periodic stats
                if cycle % 20 == 0:
                    elapsed = (datetime.now() - stats['start_time']).total_seconds()
                    acct = mt5i.account_info()
                    logger.info("--- Stats after {} cycles ({:.0f}s) ---", cycle, elapsed)
                    logger.info("  Signals: {} | Trades: {} | Skipped: {} | Errors: {}",
                                stats['signals'], stats['trades'], stats['skipped'], stats['errors'])
                    logger.info("  Account: Balance=${:,.2f} Equity=${:,.2f} Margin=${:,.2f}",
                                acct.balance, acct.equity, acct.margin)

            except Exception as e:
                stats['errors'] += 1
                import traceback
                logger.error("[Cycle {}] Error: {}\n{}", cycle, e, traceback.format_exc())

            await asyncio.sleep(interval)

        # Shutdown summary
        elapsed = (datetime.now() - stats['start_time']).total_seconds()
        logger.info("")
        logger.info("=" * 65)
        logger.info("  TRADING SESSION COMPLETE")
        logger.info("=" * 65)
        logger.info("Duration: {:.0f}s | Cycles: {}", elapsed, stats['cycles'])
        logger.info("Signals: {} | Trades: {} | Skipped: {} | Errors: {}",
                    stats['signals'], stats['trades'], stats['skipped'], stats['errors'])
        acct = mt5i.account_info()
        logger.info("Final Balance: ${:,.2f} | Equity: ${:,.2f}", acct.balance, acct.equity)
        logger.info("=" * 65)


if __name__ == "__main__":
    asyncio.run(main())
