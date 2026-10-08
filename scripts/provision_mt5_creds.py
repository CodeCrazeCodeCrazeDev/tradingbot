"""Provision rotated demo-only MT5 credentials for the canonical provider.

The CanonicalCredentialProvider resolves MT5_LOGIN / MT5_PASSWORD /
MT5_SERVER from the process environment (or an encrypted store that is
opt-in). This helper sets the three values as *user-level* environment
variables on Windows (HKCU\\Environment via setx) so new shells and the
runner resolve them — values are read interactively or from a file and
are NEVER printed, logged, or written into the repository.

Usage:
    python scripts/provision_mt5_creds.py --interactive
    python scripts/provision_mt5_creds.py --from-file path/to/creds.env
    python scripts/provision_mt5_creds.py --check

creds.env format (kept outside the repo — .env IS gitignored but do not
leave credential files inside the tree anyway):
    MT5_LOGIN=12345678
    MT5_PASSWORD=...
    MT5_SERVER=MetaQuotes-Demo

After provisioning open a NEW terminal (setx does not affect running
processes) and run:
    python scripts/mt5_preflight.py --authorize-connect
"""

from __future__ import annotations

import argparse
import getpass
import os
import subprocess
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

NAMES = ("MT5_LOGIN", "MT5_PASSWORD", "MT5_SERVER")


def _read_file(path: Path) -> dict:
    values = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, _, v = line.partition("=")
        values[k.strip().upper()] = v.strip().strip('"').strip("'")
    return values


def _interactive() -> dict:
    values = {
        "MT5_LOGIN": input("MT5_LOGIN (demo account number): ").strip(),
        "MT5_PASSWORD": getpass.getpass("MT5_PASSWORD: "),
        "MT5_SERVER": input("MT5_SERVER (e.g. MetaQuotes-Demo): ").strip(),
    }
    return values


def _persist(name: str, value: str) -> bool:
    """setx writes HKCU\\Environment — user scope, new processes only."""
    r = subprocess.run(["setx", name, value], capture_output=True,
                       text=True)
    return r.returncode == 0


def _check() -> int:
    missing = [n for n in NAMES if not os.environ.get(n)]
    if missing:
        print(f"NOT provisioned in this session: {missing}")
        print("(setx values appear only in NEW terminals — "
              "reopen the shell after provisioning)")
        return 1
    print("MT5 env vars present: all three set")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--interactive", action="store_true")
    g.add_argument("--from-file", type=Path)
    g.add_argument("--check", action="store_true")
    args = ap.parse_args()

    if args.check:
        return _check()

    values = _read_file(args.from_file) if args.from_file \
        else _interactive()
    missing = [n for n in NAMES if not values.get(n)]
    if missing:
        print(f"ERROR: missing {missing} — all three are required")
        return 1

    # Guard rail: refuse obviously-burned or non-demo inputs
    server = values["MT5_SERVER"].lower()
    if "demo" not in server and "trial" not in server:
        print("WARNING: server name does not look demo-only "
              f"('{values['MT5_SERVER']}'). Rotated demo-only credentials "
              "are required — aborting. Re-run only after rotating.")
        return 1

    ok = all(_persist(n, values[n]) for n in NAMES)
    if ok:
        print("Provisioned MT5_LOGIN/MT5_PASSWORD/MT5_SERVER "
              "(user-level env). Open a NEW terminal, then:")
        print("  python scripts/mt5_preflight.py --authorize-connect")
        return 0
    print("setx failed — provision manually:")
    print("  setx MT5_LOGIN <login> && setx MT5_PASSWORD <pw> "
          "&& setx MT5_SERVER <server>")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
