#!/usr/bin/env python
"""Bounded model-engineering search — the CSC's AutoML loop.

Searches a DECLARED hyperparameter neighborhood around the proven
rv-blend task (the only model family whose save-gate passed). Each
variant trains to a scratch checkpoint, is scored by the SAME
contiguous-fold walk-forward protocol that admitted the incumbent
(rv_walkforward_eval.py), and is archived honestly — winners and
losers alike.

Promotion discipline: a variant that beats the incumbent's recorded
walk-forward rv16 R² by --margin becomes
var/rv_blend_forecaster_candidate.pt — a CANDIDATE file, never an
auto-deploy. The live checkpoint is untouched; swapping it remains
an operator decision (same gate as everything else).

Honest scope: this is hyperparameter search, not architecture
search — feature sets and model classes are fixed. v1 proves the
loop; widening the search space is a deliberate later decision.

Usage (hermes env — trainers need torch):
    python scripts/model_engineering_search.py --dry-run
    python scripts/model_engineering_search.py --max-variants 4
"""

import argparse
import itertools
import json
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
VAR = ROOT / "var"
SEARCH = VAR / "me_search"
HERMES_PY = (Path.home() / "AppData" / "Local" / "hermes"
             / "hermes-agent" / "venv" / "Scripts" / "python.exe")
PY = str(HERMES_PY) if HERMES_PY.exists() else sys.executable

# Declared search space — incumbent (blend_w=0.5, hidden=64,
# seq=32, lr=1e-3) is the center; grid excludes it (the baseline
# to beat). blend_w is genuine architecture (GRU/ridge mix).
GRID = {
    "blend_w": [0.3, 0.7],
    "hidden": [32, 128],
    "seq": [16, 64],
    "lr": [3e-4, 3e-3],
}


def _rv16_ckpt_r2(report: dict, symbol: str = "EURUSD") -> float:
    """Flat-key schema: symbols.<SYM>.summary['rv16.ckpt_r2'] —
    the blend checkpoint's own walk-forward score."""
    try:
        v = report["symbols"][symbol]["summary"]["rv16.ckpt_r2"]
        return float(v["mean"] if isinstance(v, dict) else v)
    except Exception:
        return float("-inf")


def _incumbent_score() -> float:
    """Incumbent's recorded EURUSD rv16 ckpt R² — the bar."""
    try:
        w = json.loads((VAR / "rv_walkforward.json").read_text())
        return _rv16_ckpt_r2(w)
    except Exception:
        return 0.0


def _run(cmd: list, timeout_s: int, log: Path) -> dict:
    try:
        with open(log, "w", encoding="utf-8") as fh:
            r = subprocess.run(cmd, cwd=ROOT, stdout=fh,
                               stderr=subprocess.STDOUT,
                               timeout=timeout_s, text=True)
        return {"rc": r.returncode}
    except subprocess.TimeoutExpired:
        return {"rc": None, "error": f"timeout {timeout_s}s"}
    except Exception as e:
        return {"rc": None, "error": f"{type(e).__name__}: {e}"}


def _eval_score(wf_json: Path) -> float:
    """EURUSD rv16 ckpt R² from a variant's walkforward report —
    same field the incumbent bar uses, apples-to-apples."""
    try:
        return _rv16_ckpt_r2(json.loads(wf_json.read_text()))
    except Exception:
        return float("-inf")


# Feature-ablation presets (trainer --ablate): which obs signals
# carry the vol-forecast skill? Tested at incumbent hyperparams.
ABLATE_PRESETS = ["none", "no_hour", "no_mom", "no_volz",
                  "no_rng", "price_only", "vol_only"]
_ABLATE_MAP = {"no_hour": "hour", "no_mom": "mom8",
               "no_volz": "vol_z", "no_rng": "rng"}


def variants(max_variants: int):
    import random
    keys = list(GRID)
    combos = [dict(zip(keys, c), ablate="none")
              for c in itertools.product(*(GRID[k] for k in keys))]
    # seeded sample so small budgets cover every dimension
    if len(combos) > max_variants:
        combos = random.Random(42).sample(combos, max_variants)
    for c in combos:
        yield c
    # dedicated ablation variants at incumbent hyperparams —
    # guaranteed coverage regardless of hyperparam budget
    inc = {"blend_w": 0.5, "hidden": 64, "seq": 32, "lr": 0.001}
    for preset in ABLATE_PRESETS[1:]:
        v = dict(inc)
        v["ablate"] = _ABLATE_MAP.get(preset, preset)
        yield v


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--max-variants", type=int, default=4)
    ap.add_argument("--margin", type=float, default=0.02,
                    help="required improvement over incumbent rv16 R²")
    ap.add_argument("--train-timeout", type=int, default=1800)
    ap.add_argument("--eval-timeout", type=int, default=900)
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    SEARCH.mkdir(parents=True, exist_ok=True)
    incumbent = _incumbent_score()
    report = {"ran_at": datetime.now(timezone.utc).isoformat(
        timespec="seconds"), "incumbent_rv16_r2": incumbent,
        "margin": args.margin, "variants": []}

    plist = list(variants(args.max_variants))
    print(f"incumbent rv16 R²={incumbent:.4f}  "
          f"variants={len(plist)}  margin={args.margin}")
    if args.dry_run:
        for v in plist:
            print("  ", v)
        print(json.dumps(report, indent=2)[:400])
        return 0

    best = {"score": incumbent, "variant": None, "ckpt": None}
    for i, v in enumerate(plist):
        tag = (f"v{i}_w{v['blend_w']}_h{v['hidden']}"
               f"_s{v['seq']}_lr{v['lr']}"
               f"_ab{v.get('ablate', 'none')}")
        ckpt = SEARCH / f"{tag}.pt"
        wfout = SEARCH / f"{tag}_wf.json"
        rec = {"variant": v, "tag": tag}
        tr = _run([PY, str(ROOT / "scripts" / "train_rv_forecaster.py"),
                   "--ratio", "--blend",
                   "--blend-w", str(v["blend_w"]),
                   "--hidden", str(v["hidden"]),
                   "--seq", str(v["seq"]),
                   "--lr", str(v["lr"]),
                   "--ablate", str(v.get("ablate", "none")),
                   "--out", str(ckpt.relative_to(ROOT))],
                  args.train_timeout, SEARCH / f"{tag}_train.log")
        rec["train_rc"] = tr.get("rc")
        if tr.get("rc") != 0:
            rec["status"] = "train_failed"
        elif not ckpt.exists():
            # training completed but the save gate rejected it — a
            # valid negative result, not a crashed run
            rec["status"] = "gate_rejected"
            report["variants"].append(rec)
            print(f"[{i}] {tag}: train failed {tr}")
            continue
        ev = _run([PY, str(ROOT / "scripts" / "rv_walkforward_eval.py"),
                   "--ckpt", str(ckpt.relative_to(ROOT)),
                   "--out", str(wfout.relative_to(ROOT))],
                  args.eval_timeout, SEARCH / f"{tag}_eval.log")
        score = _eval_score(wfout) if wfout.exists() else float("-inf")
        rec.update({"eval_rc": ev.get("rc"), "rv16_r2": score})
        report["variants"].append(rec)
        print(f"[{i}] {tag}: rv16 R²={score:.4f} "
              f"(incumbent {incumbent:.4f})")
        if score > best["score"]:
            best = {"score": score, "variant": v, "ckpt": ckpt}

    cand = None
    if best["variant"] and best["score"] > incumbent + args.margin:
        cand = VAR / "rv_blend_forecaster_candidate.pt"
        shutil.copy2(best["ckpt"], cand)
        report["candidate"] = {"file": cand.name,
                               "variant": best["variant"],
                               "rv16_r2": best["score"],
                               "note": "candidate only — operator "
                                       "decision to promote"}
        print(f"CANDIDATE: {best['variant']} rv16 R²="
              f"{best['score']:.4f} -> {cand.name}")
    else:
        report["candidate"] = None
        print("no variant beat incumbent + margin — honest null")

    (VAR / "model_engineering_report.json").write_text(
        json.dumps(report, indent=2))
    with open(VAR / "model_engineering_ledger.jsonl", "a",
              encoding="utf-8") as f:
        f.write(json.dumps({"ts": report["ran_at"],
                            "incumbent": incumbent,
                            "best": best["score"],
                            "candidate": bool(report["candidate"]),
                            "n_variants": len(plist)}) + "\n")
    print(f"report -> var/model_engineering_report.json")
    return 0


if __name__ == "__main__":
    sys.exit(main())
