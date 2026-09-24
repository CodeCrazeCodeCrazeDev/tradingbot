"""Walk-forward evaluation harness — out-of-sample honesty for the brain.

Protocol:
  1. Chronological split of real OHLCV history (TRAIN | TEST).
  2. TRAIN warmup: cycles run normally; realized outcomes feed the
     calibrator (in-sample fit of Platt/isotonic).
  3. TEST: strict out-of-sample. For every authorized trade a position is
     simulated (entry at bar close, exit at horizon close or intrabar
     stop, whichever comes first). The realized outcome is scored
     against the cycle's predicted probability *before* it is fed into
     the calibrator — so ECE measures pre-update calibration honestly.
  4. Report: win rate, mean/total return, max drawdown of the equity
     curve, abstain rate, drift events, raw-vs-calibrated ECE.

No synthetic paths: all prices come from the supplied DataFrame.
"""

import logging
import sqlite3
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Tuple

import numpy as np
import pandas as pd

from trading_bot.cognition.orchestrator import AlphaAlgoCognitiveBrain

logger = logging.getLogger(__name__)

DEFAULT_DB = Path(__file__).resolve().parents[2] / "market_data.db"


@dataclass
class TradeRecord:
    bar_index: int
    action: str
    entry: float
    exit: float
    ret: float            # signed simple return
    raw_prob: float       # simulator win probability at decision time
    cal_prob: float       # calibrated probability at decision time
    stopped_out: bool
    correct: bool         # ret > 0 for BUY, < 0 for SELL


@dataclass
class EvaluationReport:
    symbol: str
    split: str
    cycles: int = 0
    trades: int = 0
    abstain_rate: float = 0.0
    win_rate: float = 0.0
    mean_return: float = 0.0
    total_return: float = 0.0
    max_drawdown: float = 0.0
    ece_raw: float = 0.0
    ece_calibrated: float = 0.0
    drift_events: int = 0
    records: List[TradeRecord] = field(default_factory=list)

    def summary(self) -> str:
        return (
            f"[{self.split}] {self.symbol}: {self.cycles} cycles, {self.trades} trades "
            f"(abstain {self.abstain_rate:.0%}) | win {self.win_rate:.0%} "
            f"| mean {self.mean_return:+.4%} | total {self.total_return:+.2%} "
            f"| maxDD {self.max_drawdown:.2%} | ECE raw {self.ece_raw:.3f} "
            f"cal {self.ece_calibrated:.3f} | drift {self.drift_events}"
        )


def _ece(pairs: Sequence[Tuple[float, bool]], n_bins: int = 10) -> float:
    """Expected calibration error over (predicted_prob, realized) pairs."""
    if not pairs:
        return 0.0
    bins: List[List[Tuple[float, bool]]] = [[] for _ in range(n_bins)]
    for p, y in pairs:
        bins[min(int(p * n_bins), n_bins - 1)].append((p, y))
    ece = 0.0
    for b in bins:
        if not b:
            continue
        conf = np.mean([p for p, _ in b])
        acc = np.mean([1.0 if y else 0.0 for _, y in b])
        ece += (len(b) / len(pairs)) * abs(acc - conf)
    return float(ece)


def _h1_aggregate(m15_rows: List[Dict[str, float]]) -> Dict[str, float]:
    """Aggregate 4 M15 bars into one H1 bar (same convention as the feed)."""
    return {
        "open": m15_rows[0]["open"],
        "high": max(r["high"] for r in m15_rows),
        "low": min(r["low"] for r in m15_rows),
        "close": m15_rows[-1]["close"],
        "volume": sum(r["volume"] for r in m15_rows),
    }


class WalkForwardEvaluator:
    """Replays real history through AlphaAlgoCognitiveBrain, measures honestly."""

    def __init__(
        self,
        brain: Optional[AlphaAlgoCognitiveBrain] = None,
        horizon_bars: int = 4,
        train_frac: float = 0.7,
        signal: str = "AUTO",
    ):
        self.brain = brain or AlphaAlgoCognitiveBrain()
        self.horizon = horizon_bars
        self.train_frac = train_frac
        self.signal = signal  # 'AUTO' = propose the estimated trend direction

    @staticmethod
    def load_ohlcv(db_path: Path = DEFAULT_DB, symbol: str = "EURUSD") -> pd.DataFrame:
        con = sqlite3.connect(str(db_path))
        try:
            df = pd.read_sql_query(
                "SELECT timestamp, open, high, low, close, volume "
                "FROM market_data WHERE symbol = ? ORDER BY timestamp",
                con, params=(symbol,),
            )
        finally:
            con.close()
        if df.empty:
            raise RuntimeError(f"No rows for {symbol} in {db_path}")
        return df

    def _propose(self, res: Dict[str, Any]) -> str:
        if self.signal != "AUTO":
            return self.signal
        trend = (res.get("market_state") or {}).get("trend", "NEUTRAL")
        return {"BULLISH": "BUY", "BEARISH": "SELL"}.get(trend, "NEUTRAL")

    def _simulate_trade(
        self, df: pd.DataFrame, i: int, action: str, stop_loss: Optional[float]
    ) -> Optional[Tuple[float, float, bool]]:
        """Return (exit_price, signed_ret, stopped_out) or None if past end."""
        entry = float(df["close"].iloc[i])
        end = min(i + self.horizon, len(df) - 1)
        if end <= i:
            return None
        direction = 1.0 if action == "BUY" else -1.0
        stopped = False
        exit_px = float(df["close"].iloc[end])
        if stop_loss is not None:
            for j in range(i + 1, end + 1):
                lo, hi = float(df["low"].iloc[j]), float(df["high"].iloc[j])
                hit = lo <= stop_loss if direction > 0 else hi >= stop_loss
                if hit:
                    exit_px, stopped = stop_loss, True
                    break
        ret = direction * (exit_px / entry - 1.0)
        return exit_px, ret, stopped

    def _run_split(self, df: pd.DataFrame, symbol: str, split: str,
                   feed_calibration: bool) -> EvaluationReport:
        rep = EvaluationReport(symbol=symbol, split=split)
        m15_tail: List[Dict[str, float]] = []
        raw_pairs: List[Tuple[float, bool]] = []
        cal_pairs: List[Tuple[float, bool]] = []
        equity = [1.0]
        peak = 1.0

        for i in range(len(df)):
            row = df.iloc[i]
            bar = {"open": float(row["open"]), "high": float(row["high"]),
                   "low": float(row["low"]), "close": float(row["close"]),
                   "volume": float(row["volume"])}
            m15_tail.append(bar)
            m15_tail = m15_tail[-4:]
            raw = {"M15": bar}
            if len(m15_tail) == 4:
                raw["H1"] = _h1_aggregate(m15_tail)

            # propose from prior cycle's trend, then run the full cycle
            proposal = self._propose(getattr(self, "_last", {})) or "NEUTRAL"
            if proposal == "BUY":
                stop = bar["close"] * 0.995
            elif proposal == "SELL":
                stop = bar["close"] * 1.005
            else:
                stop = None
            res = self.brain.process_cycle(
                instrument=symbol,
                raw_market_data=raw,
                proposed_trade_signal=proposal,
                stop_loss_price=stop,
            )
            self._last = res
            rep.cycles += 1
            if res.get("drift_detected"):
                rep.drift_events += 1

            action = res["authorized_action"]
            if action not in ("BUY", "SELL"):
                continue
            sim = self._simulate_trade(df, i, action, stop if action == proposal else None)
            if sim is None:
                continue
            exit_px, ret, stopped = sim
            correct = ret > 0
            raw_p = res.get("raw_win_probability") or 0.5
            cal_p = res.get("calibrated_probability") or raw_p
            raw_pairs.append((raw_p, correct))
            cal_pairs.append((cal_p, correct))
            rep.records.append(TradeRecord(
                bar_index=i, action=action, entry=float(bar["close"]),
                exit=exit_px, ret=ret, raw_prob=raw_p, cal_prob=cal_p,
                stopped_out=stopped, correct=correct,
            ))
            if feed_calibration:
                self.brain.record_outcome(raw_p, correct)

            equity.append(equity[-1] * (1.0 + ret * 0.01))  # 1% fixed fractional
            peak = max(peak, equity[-1])
            rep.max_drawdown = max(rep.max_drawdown, 1.0 - equity[-1] / peak)

        rep.trades = len(rep.records)
        rep.abstain_rate = 1.0 - rep.trades / max(rep.cycles, 1)
        if rep.records:
            rets = [r.ret for r in rep.records]
            rep.win_rate = float(np.mean([r > 0 for r in rets]))
            rep.mean_return = float(np.mean(rets))
            rep.total_return = float(np.sum(rets))
        rep.ece_raw = _ece(raw_pairs)
        rep.ece_calibrated = _ece(cal_pairs)
        return rep

    def run(self, db_path: Path = DEFAULT_DB, symbol: str = "EURUSD"
            ) -> Dict[str, EvaluationReport]:
        df = self.load_ohlcv(db_path, symbol)
        cut = int(len(df) * self.train_frac)
        train_df, test_df = df.iloc[:cut].reset_index(drop=True), df.iloc[cut:].reset_index(drop=True)
        logger.info("Walk-forward: %d bars total | train %d | test %d", len(df), len(train_df), len(test_df))
        train = self._run_split(train_df, symbol, "TRAIN(warmup)", feed_calibration=True)
        test = self._run_split(test_df, symbol, "TEST(OOS)", feed_calibration=True)
        return {"train": train, "test": test}


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, force=True)
    reports = WalkForwardEvaluator().run()
    for r in reports.values():
        print(r.summary())
