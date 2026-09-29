# Live-enablement checklist

The canonical graph (`ModularMonolithRuntime → UnifiedTradingBot → CSC → risk →
governance → shield → bus → execution`) is hardened and test-enforced. No live
capital path exists today — every live-capable legacy surface refuses or warns.
Enabling live trading is a deliberate, gated procedure. Do these in order.

## 1. Testnet first (never skip)

- [ ] Provision **paper/testnet broker credentials** only — MT5 demo account or
      Alpaca paper API keys. Never a funded account on first run.
- [ ] Store credentials via `SecureCredentialVault` (`trading_bot/security/
      credential_vault.py`) — `rotate_key` is fixed and tested; do NOT commit
      credentials or put them in config files. Use env vars → vault.
- [ ] Select the broker adapter explicitly:
      `CanonicalExecutionService(adapter=MT5BrokerAdapter(...))` — the adapter
      warns `DeprecationWarning` on construction by design (explicit opt-in).
- [ ] Run ≥ 1 week on testnet and reconcile fills/positions nightly against
      `SqliteTradingRepository.list_fills()` / `snapshot()`.

## 2. Governance wiring for live

- [ ] Construct the approval gate with `trading_mode='live'` (or
      `set_trading_mode('live')`): `get_approval_gate({'trading_mode': 'live'})`.
      In live mode, STANDARD actions (`execute_trade`, `open_position`,
      `place_order`, `modify_position`) block until a human approves —
      de-risking (`close_position`, `cancel_order`) stays AUTO by design.
- [ ] Operator approval path is ready: `python scripts/approve.py list`
      / `approve <id>` / `reject <id> --reason …` — the gate polls
      `human_layer/decision_<id>.json` (~1s). Tested end-to-end.
- [ ] Decide CRITICAL actions (risk-limit/strategy/broker changes, deploys,
      live-enable) — these wait with no timeout; an operator must be reachable.

## 3. Risk configuration to real capital

- [ ] Set `initial_equity` in `UnifiedTradingBot` config to the real funded
      amount — `PortfolioStateProvider` derives live exposure/drawdown from
      persisted fills; wrong equity silently distorts every risk check.
- [ ] Review limits: `max_exposure` (default 0.05), `max_quantity` (10.0),
      `max_drawdown` (0.25), symbol allowlist, `max_spread_bps`.
- [ ] Confirm `ImmutableShield` denylist/floors for the intended instruments.

## 4. Operations hardening

- [ ] Durable audit: `UnifiedDecisionBus` vetoes shielded actions if the audit
      path is unwritable — pick a persistent volume, verify at startup.
- [ ] Health/monitoring read-only surfaces are runnable (dashboards, monitors).
- [ ] Alerting: wire `human_layer/alerts.py` notification callbacks so approval
      requests reach an operator (email/webhook), not just the CLI.
- [ ] Backup/restore drill for `alphaalgo_data/trading_state.db`.

## 5. Go-live gate (all must be true)

- [ ] `tests/architecture` + `tests/foundation` green (CI job enforces).
- [ ] 1+ week clean testnet reconciliation.
- [ ] Human approval loop exercised end-to-end at least once (request →
      `scripts/approve.py approve` → fill executes).
- [ ] Kill-path drill: `close_position`/`cancel_order` work with broker down.
- [ ] Signed decision recorded: who enabled live, when, at what equity/limits.

## Do NOT

- Do not un-quarantine legacy launchers or run `scripts/launchers/*`,
  `install_service.py`, `live_trading_system.py`, `mt5_brain_trader.py`, etc.
  They are parallel capital paths; the canonical runtime is the only boundary.
- Do not relax `ACTION_LEVELS` — `modify_approval_levels` is FORBIDDEN.
- Do not point `initial_equity` at a number larger than funded capital.
