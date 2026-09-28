"""Package launcher backing the ``trading-bot`` console script.

Delegates to the canonical repository ``main.py`` (the single UCA-2026
paper/analysis entry point) so the installed CLI and the source-tree
launcher can never diverge. Run ``trading-bot --help`` for options.
"""

from __future__ import annotations

import asyncio
import sys
from pathlib import Path


def main() -> None:
    repo_root = Path(__file__).resolve().parents[1]
    launcher = repo_root / "main.py"
    if not launcher.is_file():
        raise SystemExit(
            "trading-bot: canonical launcher 'main.py' was not found beside "
            "the installed package; run from a source checkout."
        )
    sys.path.insert(0, str(repo_root))
    import main as repo_main  # noqa: E402 -- deferred until repo root is on sys.path

    asyncio.run(repo_main.main())


if __name__ == "__main__":
    main()
