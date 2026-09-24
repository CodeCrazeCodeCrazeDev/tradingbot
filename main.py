"""
AlphaAlgo UCA-2026 - Unified Trading Bot entry point.

ONE bot, ONE brain: every module layer (memory, verification, governance,
execution, telemetry, evolution, human oversight) runs as a service under the
CognitiveSystemController via ``trading_bot.unified_bot.UnifiedTradingBot``.

Observation sources:
    default      real historical bars from market_data.db (grounded)
    --synthetic  deterministic synthetic feed (Ornstein-Uhlenbeck, seeded)
                 — labeled stand-in, never presented as real evidence

Run:
    python main.py --symbol EURUSD --cycles 100
    python main.py --synthetic --symbol BTC/USDT --interval 5 --cycles 10
"""

import argparse
import asyncio
import logging
import math
import random
import sqlite3
import sys
from pathlib import Path
from typing import Any, Dict, Iterator

from trading_bot.unified_bot import UnifiedTradingBot

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
    handlers=[logging.FileHandler("uca_brain.log"), logging.StreamHandler()],
    force=True,
)
logger = logging.getLogger("UCA-2026")

DB_PATH = Path(__file__).resolve().parent / "market_data.db"


def replay_observations(db_path: Path, symbol: str) -> Iterator[Dict[str, Any]]:
    """Deterministic replay of real market data (grounding requirement)."""
    con = sqlite3.connect(str(db_path))
    try:
        rows = con.execute(
            "SELECT timestamp, symbol, open, high, low, close, volume "
            "FROM market_data WHERE symbol = ? ORDER BY timestamp",
            (symbol,),
        ).fetchall()
    finally:
        con.close()

    if not rows:
        raise RuntimeError(f"No market data found for symbol '{symbol}' in {db_path}")

    for ts, sym, open_, high, low, close, volume in rows:
        yield {
            "timestamp": ts,
            "symbol": sym,
            "price": close,
            "open": open_,
            "high": high,
            "low": low,
            "close": close,
            "volume": volume,
        }


def synthetic_observations(symbol: str, seed: int, base_price: float) -> Iterator[Dict[str, Any]]:
    """Deterministic synthetic market feed (Ornstein-Uhlenbeck), seeded."""
    rng = random.Random(seed)
    theta = 0.15
    sigma = 0.004
    t = 0
    while True:
        price = base_price * math.exp(
            math.sin(t * theta) * sigma * 10 + rng.gauss(0, sigma)
        )
        yield {
            "timestamp": t,
            "symbol": symbol,
            "price": round(price, 5),
            "volatility": abs(rng.gauss(0.02, 0.005)),
            "volume": abs(rng.gauss(1.2e6, 2e5)),
            "sentiment": max(-1.0, min(1.0, rng.gauss(0.0, 0.3))),
            "exposure": 0.01,
        }
        t += 1


async def main():
    args = parse_args()

    logger.info("=" * 60)
    logger.info("ALPHAALGO UCA-2026: UNIFIED TRADING BOT")
    logger.info("=" * 60)

    bot = UnifiedTradingBot({
        "latent_dim": 256,
        "max_exposure": args.max_exposure,
        "max_quantity": args.max_quantity,
        "trading_enabled": args.mode != "analysis",
        "max_spread_bps": args.max_spread_bps,
    })

    if args.synthetic:
        source = synthetic_observations(args.symbol, args.seed, args.base_price)
    else:
        source = replay_observations(DB_PATH, args.symbol)

    try:
        await bot.run(source, cycles=args.cycles, interval=args.interval)
    except KeyboardInterrupt:
        logger.info("Shutdown requested.")


def parse_args():
    parser = argparse.ArgumentParser(description="AlphaAlgo UCA-2026 Unified Trading Bot")
    parser.add_argument("--symbol", type=str, default="EURUSD", help="Primary trading symbol")
    parser.add_argument("--interval", type=float, default=1.0, help="Seconds between observations")
    parser.add_argument("--cycles", type=int, default=0, help="Max loop cycles (0 = run forever)")
    parser.add_argument("--mode", choices=["paper", "analysis"], default="paper")
    parser.add_argument("--seed", type=int, default=42, help="Synthetic feed seed")
    parser.add_argument("--base-price", type=float, default=50000.0)
    parser.add_argument("--max-exposure", type=float, default=0.05)
    parser.add_argument("--max-quantity", type=float, default=10.0)
    parser.add_argument("--max-spread-bps", type=float, default=None,
                        help="Immutable Shield spread guard: veto entries when live spread exceeds this (bps)")
    parser.add_argument("--synthetic", action="store_true",
                        help="Use the labeled synthetic feed instead of real market_data.db replay")
    return parser.parse_args()


if __name__ == "__main__":
    asyncio.run(main())
