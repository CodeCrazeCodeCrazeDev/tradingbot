"""Read-only MT5 demo preflight — runs the full authorization checklist.

This script is the single gate between "credentials supplied" and "adapter
may trade". It is intentionally incapable of placing an order: it only
calls ``connect()`` (which itself hard-fails on any non-DEMO account),
reads account/symbol metadata, enumerates open positions, and reconciles
against the durable ledger.

Usage (hermes interpreter — MetaTrader5 SDK must be installed):

    python scripts/mt5_preflight.py --authorize-connect

Credentials are resolved by the canonical credential provider
(MT5_LOGIN / MT5_PASSWORD / MT5_SERVER by default). They must be
*rotated, demo-only* credentials — the previously committed credential
material (login/password/investor for the MetaQuotes-Demo account) is
burned and must never be reused.

Checks (all must pass before a demo soak is authorized):
  1. credentials resolvable through the provider (no env fallback hacks)
  2. terminal initialize + login
  3. account trade_mode == DEMO        (adapter enforces, fail-closed)
  4. account currency == USD           (configurable, defaults USD)
  5. margin mode discovered            (netting or hedging — reported)
  6. symbol exists with exact name     (no suffix aliases)
  7. symbol trade_mode == FULL
  8. volume grid valid (min/max/step)  + contract size
  9. open positions enumerable         (read-only)
 10. ledger reconciliation             (read-only; mismatch reported, not fixed)
 11. M15 bars retrievable              (market-data availability)

A JSON report is written to --out (default var/mt5_preflight_<ts>.json).
Exit code 0 only when every check passes.
"""

from __future__ import annotations

import argparse
import asyncio
import json
import sys
import time
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))


def _result(name: str, ok: bool, detail: str = "", **extra) -> dict:
    return {"check": name, "ok": bool(ok), "detail": detail, **extra}


async def run_preflight(args) -> int:
    from trading_bot.brokers.mt5_demo import MT5DemoAdapter, MT5AdapterError
    from trading_bot.persistence.repositories import SqliteTradingRepository

    results = []

    adapter = MT5DemoAdapter(config={
        "symbol": args.symbol,
        "timeframe": args.timeframe,
        "account_currency": args.account_currency,
        "login_env": args.login_env,
        "password_env": args.password_env,
        "server_env": args.server_env,
        "terminal_path": args.terminal_path or None,
    })

    # -- 1-8: connect() runs credential resolution, login, and all
    # account/symbol validations (demo-only, currency, margin mode,
    # exact-symbol, FULL trade mode, volume grid).
    try:
        await adapter.connect()
    except MT5AdapterError as exc:
        results.append(_result("connect_and_validate", False, str(exc)))
        report = {"passed": False, "results": results,
                  "checked_at": time.time()}
        _write_report(args, report)
        print(json.dumps(report, indent=2))
        return 1
    except Exception as exc:  # noqa: BLE001 - fail closed on anything
        results.append(_result("connect_and_validate", False,
                               f"{type(exc).__name__}: {exc}"))
        report = {"passed": False, "results": results,
                  "checked_at": time.time()}
        _write_report(args, report)
        print(json.dumps(report, indent=2))
        return 1

    results.append(_result(
        "connect_and_validate", True,
        f"login={adapter.account_login} mode={adapter.account_mode} "
        f"session={getattr(adapter, 'session_mode', 'credentials')}",
        account_login=adapter.account_login,
        account_mode=adapter.account_mode,
        session_mode=getattr(adapter, "session_mode", "credentials"),
    ))

    client = adapter._client  # read-only introspection only
    try:
        # -- account identity details (read-only)
        info = client.account_info()
        results.append(_result(
            "account_identity", info is not None,
            f"login={getattr(info, 'login', '?')} "
            f"server={getattr(info, 'server', '?')} "
            f"currency={getattr(info, 'currency', '?')} "
            f"balance={getattr(info, 'balance', '?')} "
            f"equity={getattr(info, 'equity', '?')} "
            f"trade_allowed={getattr(info, 'trade_allowed', '?')}"))

        # -- symbol contract details
        sinfo = client.symbol_info(args.symbol)
        results.append(_result(
            "symbol_contract", sinfo is not None,
            f"name={getattr(sinfo, 'name', '?')} "
            f"vol_min={adapter._volume_min} vol_max={adapter._volume_max} "
            f"vol_step={adapter._volume_step} "
            f"contract_size={adapter._contract_size} "
            f"spread={getattr(sinfo, 'spread', '?')}pts "
            f"digits={getattr(sinfo, 'digits', '?')}"))

        # -- open positions (read-only)
        positions = await adapter.get_positions()
        results.append(_result(
            "positions_enumerable", True,
            f"{len(positions)} open position(s)",
            positions=[{
                "symbol": p.instrument.symbol,
                "quantity": p.quantity,
                "average_price": p.average_price,
            } for p in positions]))

        # -- ledger reconciliation (read-only — reports mismatch, does not fix)
        repo = SqliteTradingRepository(args.state_db)
        try:
            snapshot = await repo.snapshot(account_id="preflight")
            recon = await adapter.reconcile(snapshot)
            results.append(_result(
                "reconcile_vs_ledger", recon.matched,
                f"matched={recon.matched} "
                f"differences={recon.position_differences}"))
        finally:
            repo.close()

        # -- M15 bar availability (read-only)
        tf = getattr(client, "TIMEFRAME_M15", None)
        rates = client.copy_rates_from_pos(args.symbol, tf, 0, 5) if tf is not None else None
        results.append(_result(
            "m15_data_available", bool(rates is not None and len(rates) >= 1),
            f"{0 if rates is None else len(rates)} recent M15 bars retrieved"))
    finally:
        await adapter.disconnect()

    report = {
        "passed": all(r["ok"] for r in results),
        "account_login": adapter.account_login,
        "account_mode": adapter.account_mode,
        "symbol": args.symbol,
        "timeframe": args.timeframe,
        "results": results,
        "checked_at": time.time(),
    }
    _write_report(args, report)
    print(json.dumps(report, indent=2, default=str))
    return 0 if report["passed"] else 1


def _write_report(args, report: dict) -> None:
    out = Path(args.out) if args.out else (
        Path("var") / f"mt5_preflight_{int(report['checked_at'])}.json")
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, indent=2, default=str), encoding="utf-8")
    print(f"\nReport written to {out}", file=sys.stderr)


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--authorize-connect", action="store_true",
                        help="required acknowledgement that demo-only, rotated "
                             "credentials are provisioned")
    parser.add_argument("--symbol", default="EURUSD")
    parser.add_argument("--timeframe", default="M15")
    parser.add_argument("--account-currency", default="USD")
    parser.add_argument("--login-env", default="MT5_LOGIN")
    parser.add_argument("--password-env", default="MT5_PASSWORD")
    parser.add_argument("--server-env", default="MT5_SERVER")
    parser.add_argument("--terminal-path", default=None,
                        help="path to terminal64.exe; auto-detected when omitted")
    parser.add_argument("--state-db",
                        default="var/mt5_demo/trading_state.db",
                        help="durable ledger for the selected MT5 demo state "
                             "directory (must match the runner's --state-dir)")
    parser.add_argument("--out", default=None)
    args = parser.parse_args(argv)

    if not args.authorize_connect:
        print("Refusing to connect without --authorize-connect. This flag "
              "asserts that: (1) previously exposed credentials are rotated, "
              "(2) the provisioned credentials are for a DEMO account only.",
              file=sys.stderr)
        return 2

    if not args.terminal_path:
        for candidate in (
            r"C:\Program Files\MetaTrader 5\terminal64.exe",
            r"C:\Program Files (x86)\MetaTrader 5\terminal64.exe",
        ):
            if Path(candidate).exists():
                args.terminal_path = candidate
                break

    return asyncio.run(run_preflight(args))


if __name__ == "__main__":
    sys.exit(main())
