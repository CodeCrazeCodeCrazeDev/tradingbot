"""Runtime wrapper for the blended realized-volatility forecaster.

Shadow/advisory only: loads ``var/rv_blend_forecaster.pt`` (GRU + ridge,
50/50 blend, log-ratio targets) and produces a per-cycle forecast of the
expected volatility change over the next 4/8/16 bars. It has no
decision authority — consumers get ``rvf_*`` observation fields and an
append-only shadow log; nothing in the execution path reads them.

Fidelity contract with the training path (scripts/train_rv_forecaster.py):
- Same 64-dim featurization: ``WorldModelV2._obs_to_features`` on an
  observation dict shaped exactly like the trainer's ``to_obs`` —
  including its constants (rsi=50, uncertainty=0.2, trend/regime=FLAT),
  because that is the distribution the checkpoint trained on.
- Hour/session features come from the raw broker timestamp
  (``broker_timestamp``), matching the unshifted DB timestamps the
  model trained on — not the offset-adjusted ``timestamp``.
- Off-grid rows (the June-2026 second-feed splice) are skipped at the
  window level, same as the training-time ``on_grid`` filter.
- vol_z/volatility use the rolling row buffer rather than the training
  window's global stats — a mild, documented distribution difference.

torch/numpy are imported lazily inside __init__ so the lightweight
.venv can import this module safely; construction raises RuntimeError
when torch is absent so callers can degrade honestly.
"""

import json
import logging
import math
import re
from collections import deque
from pathlib import Path
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)

_TF_MIN = {"M": 1, "H": 60, "D": 1440}


def _grid_minutes(timeframe: str) -> int:
    m = re.match(r"^([MHD])(\d+)$", str(timeframe).upper())
    if not m:
        raise ValueError(f"unrecognized timeframe {timeframe!r}")
    return _TF_MIN[m.group(1)] * int(m.group(2))


def _on_grid(ts: str, step_min: int) -> bool:
    m = re.search(r"T(\d{2}):(\d{2}):(\d{2}(?:\.\d+)?)", str(ts))
    if m is None:
        return False
    h, mi, sec = int(m.group(1)), int(m.group(2)), float(m.group(3))
    return sec == 0.0 and (h * 60 + mi) % step_min == 0


class RVBlendForecaster:
    """Rolling-window GRU+ridge vol-change forecaster (advisory only)."""

    ROW_BUF = 64

    def __init__(self, ckpt_path, seq: int = 32, timeframe: str = "M15",
                 quantile_path=None):
        import numpy as np  # noqa: lazy runtime dep
        import torch  # noqa: lazy runtime dep
        from trading_bot.world_model.v2_core import WorldModelV2

        self._np = np
        self._torch = torch
        self.seq = int(seq)
        try:
            self._step = _grid_minutes(timeframe)
        except ValueError:
            self._step = 0  # unparseable label — cannot prove grid, allow

        blob = torch.load(str(ckpt_path), weights_only=True)
        hidden = int(blob["args"].get("hidden", 64))
        in_dim = 64
        out_dim = len(blob["horizons"])

        class _GRU(torch.nn.Module):
            def __init__(self):
                super().__init__()
                self.gru = torch.nn.GRU(in_dim, hidden, batch_first=True)
                self.head = torch.nn.Linear(hidden, out_dim)

            def forward(self, x):
                h, _ = self.gru(x)
                return self.head(h[:, -1, :])

        self.net = _GRU()
        self.net.load_state_dict(blob["state_dict"])
        self.net.eval()
        torch.set_num_threads(1)

        self.horizons = tuple(blob["horizons"])
        self.y_mu = np.asarray(blob["y_mean"], dtype=np.float64)
        self.y_sd = np.asarray(blob["y_std"], dtype=np.float64)
        self.blend_w = float(blob.get("blend_w", 0.5))
        self.ridge = {int(h): (np.asarray(m[0], dtype=np.float64).ravel(),
                               np.asarray(m[1], dtype=np.float64).ravel(),
                               np.asarray(m[2], dtype=np.float64).ravel())
                      for h, m in blob["ridge"].items()}
        # Optional GBM quantile heads (P50/P80/P95 of the same log-ratio
        # target). joblib/sklearn load lazily like torch; any failure
        # degrades honestly to mean-only output — no quantile fields is
        # information, not an error.
        self._quantile = None
        if quantile_path:
            try:
                import joblib
                blob_q = joblib.load(str(quantile_path))
                self._quantile = blob_q.get("models")
                logger.info("rv quantile heads loaded: %s", quantile_path)
            except Exception as exc:  # noqa: BLE001
                logger.warning("rv quantile artifact unusable (%s) — "
                               "running mean-only", exc)

        # Pure featurizer — never trained, never used for its own outputs.
        self._featurizer = WorldModelV2(asset_dims={"FX": 64,
                                                  "Equities": 128},
                                        latent_dim=256)
        self.rows = deque(maxlen=self.ROW_BUF)
        self.feats = deque(maxlen=self.seq)
        self.n_updates = 0
        self.n_skipped_offgrid = 0

    # ---- feature derivation (mirrors scripts/train_world_model.to_obs) ----

    def _bar_scalars(self):
        np = self._np
        rows = list(self.rows)
        c = np.array([r[4] for r in rows], dtype=np.float64)
        h = np.array([r[2] for r in rows], dtype=np.float64)
        lo = np.array([r[3] for r in rows], dtype=np.float64)
        v = np.array([r[5] for r in rows], dtype=np.float64)
        ret = np.diff(np.log(c), prepend=np.log(c[0]))
        i = len(rows) - 1
        return {
            "returns": float(ret[i]), "log_returns": float(ret[i]),
            "volatility": float(ret[max(0, i - 20):i + 1].std()),
            "volume_ratio": float((v[i] - v.mean()) / (v.std() + 1e-9)),
            "momentum": float(np.log(c[i] / c[i - 8])) if i >= 8 else 0.0,
            "atr": float((h[i] - lo[i]) / max(c[i], 1e-12)),
        }

    def _feat_dict(self, obs) -> Dict[str, Any]:
        ts = str(obs.get("broker_timestamp") or obs.get("timestamp") or "")
        try:
            from datetime import datetime
            hh = datetime.fromisoformat(ts.replace("Z", "+00:00")).hour
        except Exception:
            hh = 0
        s = self._bar_scalars()
        return {
            "timestamp": ts, "symbol": obs.get("symbol", ""),
            "open": obs["open"], "high": obs["high"], "low": obs["low"],
            "close": obs["close"], "price": obs["close"],
            "volume": obs["volume"],
            "volatility": s["volatility"],
            "volume_ratio": s["volume_ratio"],
            "returns": s["returns"], "log_returns": s["log_returns"],
            "momentum": s["momentum"], "session_hour": hh,
            "hour_sin": math.sin(hh / 24 * 2 * math.pi),
            "hour_cos": math.cos(hh / 24 * 2 * math.pi),
            "high_24h": obs["high"], "low_24h": obs["low"],
            "uncertainty": 0.2, "rsi": 50.0, "atr": s["atr"],
            "trend": "FLAT", "regime": "FLAT",
        }

    # ---- public API ----

    def update(self, obs: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Feed one raw observation; return a forecast dict or a status.

        Returns keys: ready, warming (bars until first forecast),
        skipped_offgrid, log_ratio {h: log vol-change}, vol_mult {h: exp()},
        and per-model components gru_/ridge_ log ratios for transparency.
        """
        req = ("open", "high", "low", "close", "volume")
        if any(obs.get(k) is None for k in req):
            return {"ready": False, "status": "missing_fields"}
        ts = str(obs.get("broker_timestamp") or obs.get("timestamp") or "")
        if self._step and ts and not _on_grid(ts, self._step):
            self.n_skipped_offgrid += 1
            return {"ready": False, "status": "off_grid",
                    "skipped_offgrid": self.n_skipped_offgrid}
        try:
            row = (ts, float(obs["open"]), float(obs["high"]),
                   float(obs["low"]), float(obs["close"]),
                   float(obs["volume"]))
        except (TypeError, ValueError):
            return {"ready": False, "status": "bad_fields"}
        self.rows.append(row)
        self.n_updates += 1

        try:
            feat = self._featurizer._obs_to_features(self._feat_dict(obs))
        except Exception as exc:  # noqa: BLE001
            logger.debug("rv forecaster featurization failed: %s", exc)
            return {"ready": False, "status": "featurize_error"}
        self.feats.append(feat)

        if len(self.feats) < self.seq:
            return {"ready": False, "status": "warming",
                    "warming": self.seq - len(self.feats)}

        torch, np = self._torch, self._np
        with torch.no_grad():
            win = torch.stack(list(self.feats)).unsqueeze(0).float()
            gru_pred = self.net(win).numpy()[0] * self.y_sd + self.y_mu
        x = self.feats[-1].numpy()
        ridge_pred = np.array([
            float(((x - mu) / sd) @ W)
            for h, (mu, sd, W) in sorted(self.ridge.items())])
        blend = self.blend_w * gru_pred + (1.0 - self.blend_w) * ridge_pred

        out = {"ready": True, "status": "ok",
               "skipped_offgrid": self.n_skipped_offgrid,
               "log_ratio": {}, "vol_mult": {},
               "gru": {}, "ridge": {}}
        for k, hh in enumerate(self.horizons):
            key = f"rv{hh}"
            out["log_ratio"][key] = float(blend[k])
            out["vol_mult"][key] = float(math.exp(float(blend[k])))
            out["gru"][key] = float(gru_pred[k])
            out["ridge"][key] = float(ridge_pred[k])

        if self._quantile is not None:
            out["quantile_log_ratio"] = {}
            out["quantile_mult"] = {}
            for k, hh in enumerate(self.horizons):
                key = f"rv{hh}"
                heads = self._quantile.get(str(hh)) or {}
                out["quantile_log_ratio"][key] = {}
                out["quantile_mult"][key] = {}
                for tag, g in heads.items():
                    q = float(g.predict(x[None, :])[0])
                    out["quantile_log_ratio"][key][tag] = q
                    out["quantile_mult"][key][tag] = float(math.exp(q))
        return out


def latest_snapshot_line(fc: Optional[Dict[str, Any]]) -> Optional[str]:
    """One-line human-readable summary for dashboards/logs."""
    if not fc or not fc.get("ready"):
        return None
    m = fc["vol_mult"]
    return ("rvfc x%.2f/x%.2f/x%.2f" %
            (m["rv4"], m["rv8"], m["rv16"]))
