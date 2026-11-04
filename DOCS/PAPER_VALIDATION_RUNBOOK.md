# Signed paper recovery and one-hour validation

This workflow uses saved BTC candles and the canonical paper runtime. It
does not connect to a broker, promote a strategy, or change risk limits.
Do not paste lists of pause/resume/estop commands as a startup sequence.

## 1. Operator approval (run this yourself)

Stop the runner first. In PowerShell, from the repository root:

```powershell
& .\.venv\Scripts\python.exe scripts/operator_cli.py --state-dir var/hl_run --user peterson --reason "Reviewed accidental operator stop; approve one-hour BTC paper validation" reset-emergency --interactive
```

Review the displayed database, emergency-incident digest, reason, and
15-minute expiry. Type `RESET PAPER` only if you approve.

On first use this confirmation enrolls a separate operator Ed25519 key
under `%LOCALAPPDATA%\alphaalgo\operator_keys\<state-path-hash>`.
Its private material is encrypted with Windows DPAPI; the public key is
pinned in the same external directory. No key material is printed or
stored in the repository. The CLI signs and immediately verifies the
approval, then commits the consumed nonce, audit receipt, and cleared
emergency flag in one SQLite transaction. It leaves pause state intact.
The runtime has not started yet.

The signed document is bound to the canonical database path, paper mode,
current persisted incident, issuer, reason, timestamps, and nonce. It
cannot be reused for another incident or run. Invalid or expired signatures
leave the stop in place; audit-write failure rolls back the entire reset.
Queued unsigned `reset_emergency` commands are rejected and audited.

Existing externally provisioned signers can use `--approval-file` instead
of `--interactive`, with the same payload/signature envelope and pinned
public key. The approval cannot supply its own trusted key.

The OS file lock prevents reset while this version of `paper_runner.py`
is active, and prevents concurrent runners sharing the same state.
Older runner versions do not participate in that lock and must be stopped
before upgrading or resetting. Pending control commands block recovery.
This interface is restricted to offline paper recovery; it is not a
live-account reset mechanism.

Local custody does not isolate keys from other code running as the same
Windows user. HSM/remote custody remains a separate deployment concern.

## 2. Start the supervised run after approval

The full runtime needs the Hermes interpreter:

```powershell
& "$env:LOCALAPPDATA\hermes\hermes-agent\venv\Scripts\python.exe" scripts/paper_validation.py --state-dir var/hl_run --db-path hl_data.db --duration-seconds 3600
```

Keep this terminal open. The supervisor refuses active/unknown emergency
or pause states and pending commands. It records a heartbeat and start,
deadline, stop, and exit information in `var/hl_run/validation_run.json`.
The one-hour clock includes startup and advisory warmup. At the deadline
it requests cancellation; after up to 30 seconds of cleanup grace it
terminates an unresponsive paper process tree on Windows. A forced stop
is explicitly labeled and may leave the last cycle incomplete.
An early exit or crash is not labeled a completed one-hour run.

The child uses BTC `15m`, UTC timestamps, explicit 64-bar prior warmup,
and then replays from bar 65. An explicit seed request replaces old
close history rather than mixing the previous replay's tail into an
earlier window. Existing learned checkpoints are retained: this is
operational validation, not an untouched out-of-sample profitability test.

Logs: `var/hl_run/validation.stdout.log` and `validation.stderr.log`.
These append across sessions; use the recorded start time to delimit a run.
The supervisor never resets an emergency stop. A new stop ends the replay.

## 3. Dashboard and evidence

Open http://localhost:8080. If the dashboard server is not running, use a
separate terminal:

```powershell
& .\.venv\Scripts\python.exe scripts/dashboard.py --state-dir var/hl_run --port 8080
```

The dashboard is localhost-only and GET-only. Trading permission and
emergency state come from the saved snapshot; the capture time and age
are shown. Snapshots older than 60 seconds are labeled STALE, which can
also mean a long cycle. Missing evidence is UNKNOWN. The supervisor
heartbeat is separate; an old heartbeat does not establish process health.
After an offline reset, the old snapshot can still show the old emergency
until the runner publishes a new one; the reset receipt is authoritative
for the offline operation.

For final validation inspect both the snapshot and durable
`trading_state.db`: count BTC terminal decisions separately from PREFLIGHT,
then orders, fills, positions, and PAPER_SETTLEMENT events. A WAIT decision
explains no order; it does not prove the simulator's economic judgment.
Controlled execution tests must be reported separately from AI-selected
trades. Do not infer profitability from a successful process run.

## Focused regression checks

```powershell
& .\.venv\Scripts\python.exe -m pytest tests/interfaces/test_operator_controls.py tests/foundation/test_recovery_plan.py -q --no-cov -p no:cacheprovider
```
