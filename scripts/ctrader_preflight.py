"""Read-only cTrader demo preflight — runs the full authorization checklist.

This script is the single gate between "credentials supplied" and "adapter
may trade". It is intentionally incapable of placing an order: it only
calls ``connect()`` (which itself hard-pins the demo endpoint, verifies the
account's ``isLive`` flag is false, and validates access rights, currency,
and the symbol volume grid), reads account/symbol metadata, enumerates open
positions, and reconciles against the durable ledger.

Usage (hermes interpreter — ctrader-open-api must be installed):

    python scripts/ctrader_preflight.py --authorize-connect

Credentials are resolved by the canonical credential provider
(CTRADER_CLIENT_ID / CTRADER_CLIENT_SECRET / CTRADER_ACCESS_TOKEN /
CTRADER_ACCOUNT_ID by default). They must be for a *demo* application and a
*demo* account only.

Checks (all must pass before a demo soak is authorized):
  1. credentials resolvable through the provider (no env fallback hacks)
  2. TCP/TLS connect + application auth (demo endpoint, hard-pinned)
  3. account present in token list AND isLive == False   (fail-closed)
  4. account auth + accessRights == FULL_ACCESS
  5. account currency == configured (defaults USD) + accountType reported
  6. symbol exists with exact name, enabled, tradingMode == ENABLED
  7. volume grid valid (min/max/step units) + lotSize
  8. open positions enumerable            (read-only reconcile)
  9. ledger reconciliation                (read-only; mismatch reported)
 10. M15 trendbars retrievable            (market-data availability)

A JSON report is written to --out (default var/ctrader_preflight_<ts>.json).
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
    from trading_bot.brokers.ctrader_demo import (
        CTraderAdapterError, CTraderDemoAdapter, _messages)
    from trading_bot.persistence.repositories import SqliteTradingRepository

    results = []

    adapter = CTraderDemoAdapter(config={
        "symbol": args.symbol,
        "timeframe": args.timeframe,
        "account_currency": args.account_currency,
        "client_id_env": args.client_id_env,
        "client_secret_env": args.client_secret_env,
        "access_token_env": args.access_token_env,
        "account_id_env": args.account_id_env,
    })

    # -- 1-7: connect() runs credential resolution, demo-endpoint pinning,
    # application auth, isLive==False, account auth, FULL_ACCESS rights,
    # hedging/netting discovery, currency, exact-symbol, ENABLED trading
    # mode, and volume-grid validation.
    try:
        await adapter.connect()
    except CTraderAdapterError as exc:
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
        f"account={adapter.ctid_trader_account_id} "
        f"login={adapter.trader_login} mode={adapter.account_mode} "
        f"session={adapter.session_mode}",
        ctid_trader_account_id=adapter.ctid_trader_account_id,
        trader_login=adapter.trader_login,
        account_mode=adapter.account_mode,
        session_mode=adapter.session_mode,
    ))

    try:
        # -- trader identity details (read-only re-read via cached connect)
        results.append(_result(
            "account_identity", adapter.trader_login is not None,
            f"account_id={adapter.ctid_trader_account_id} "
            f"trader_login={adapter.trader_login} "
            f"deposit_asset_id={getattr(adapter, '_deposit_asset_id', '?')} "
            f"money_digits={adapter._money_digits} "
            f"account_mode={adapter.account_mode}"))

        # -- symbol contract details
        results.append(_result(
            "symbol_contract", adapter._symbol_id is not None,
            f"name={args.symbol} symbolId={adapter._symbol_id} "
            f"lotSize={adapter._lot_size} "
            f"vol_min={adapter._volume_min} vol_max={adapter._volume_max} "
            f"vol_step={adapter._volume_step} digits={adapter._digits}"))

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

        # -- M15 trendbar availability (read-only)
        bars = await _fetch_trendbars(adapter)
        results.append(_result(
            "m15_data_available", bool(bars),
            f"{len(bars)} recent M15 trendbars retrieved"))
    finally:
        await adapter.disconnect()

    report = {
        "passed": all(r["ok"] for r in results),
        "ctid_trader_account_id": adapter.ctid_trader_account_id,
        "account_mode": adapter.account_mode,
        "symbol": args.symbol,
        "timeframe": args.timeframe,
        "results": results,
        "checked_at": time.time(),
    }
    _write_report(args, report)
    print(json.dumps(report, indent=2, default=str))
    return 0 if report["passed"] else 1


async def _fetch_trendbars(adapter, count: int = 5) -> list:
    """Closed M15 trendbars via the read-only data path."""
    from trading_bot.brokers.ctrader_demo import _messages
    msgs = _messages()
    req = msgs.ProtoOAGetTrendbarsReq()
    req.ctidTraderAccountId = adapter.ctid_trader_account_id
    req.symbolId = adapter._symbol_id
    req.period = 7  # ProtoOATrendbarPeriod.M15
    now_ms = int(time.time() * 1000)
    req.toTimestamp = now_ms
    req.fromTimestamp = now_ms - 7 * 24 * 3600 * 1000
    req.count = count
    res = await adapter._request(req)
    return list(getattr(res, "trendbar", ()))


def _write_report(args, report: dict) -> None:
    out = Path(args.out) if args.out else (
        Path("var") / f"ctrader_preflight_{int(report['checked_at'])}.json")
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, indent=2, default=str), encoding="utf-8")
    print(f"\nReport written to {out}", file=sys.stderr)


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--authorize-connect", action="store_true",
                        help="required acknowledgement that demo-only "
                             "credentials are provisioned")
    parser.add_argument("--symbol", default="EURUSD")
    parser.add_argument("--timeframe", default="M15")
    parser.add_argument("--account-currency", default="USD")
    parser.add_argument("--client-id-env", default="CTRADER_CLIENT_ID")
    parser.add_argument("--client-secret-env", default="CTRADER_CLIENT_SECRET")
    parser.add_argument("--access-token-env", default="CTRADER_ACCESS_TOKEN")
    parser.add_argument("--account-id-env", default="CTRADER_ACCOUNT_ID")
    parser.add_argument("--state-db",
                        default="var/ctrader_demo/trading_state.db",
                        help="durable ledger for the selected cTrader demo "
                             "state directory (must match the runner's "
                             "--state-dir)")
    parser.add_argument("--out", default=None)
    args = parser.parse_args(argv)

    if not args.authorize_connect:
        print("Refusing to connect without --authorize-connect. This flag "
              "asserts that the provisioned credentials are for a DEMO "
              "application and DEMO account only.", file=sys.stderr)
        return 2

    return asyncio.run(run_preflight(args))


if __name__ == "__main__":
    sys.exit(main())
