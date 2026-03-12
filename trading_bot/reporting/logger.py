from __future__ import annotations
import logging
logger = logging.getLogger(__name__)
from pathlib import Path
"""Centralised Loguru configuration helper.

Call `init_logger()` **once** at application start to configure both console and
file sinks. Subsequent `logger.add()` calls can be used for module‐specific sinks.
"""

import datetime as _dt
import pathlib
import sys
from typing import Any

from loguru import logger

from trading_bot.config import get
import datetime

# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def init_logger(level: str | None = None, *, log_dir: str | pathlib.Path | None = None) -> None:
    """Configure *Loguru* sinks.

    Args:
        level: Logging level. If *None*, falls back to config value or "INFO".
        log_dir: Directory for log files. Defaults to `./logs` relative to CWD.
    """
    # Resolve defaults from YAML config
    try:
        level = level or str(get("reporting.log_level", "INFO")).upper()
        log_dir = pathlib.Path(log_dir or "logs").expanduser()
        log_dir.mkdir(parents=True, exist_ok=True)

        timestamp = _dt.datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        file_path = log_dir / f"run_{timestamp}.log"

        # Remove any preconfigured handlers added by other libs
        logger.remove()

        logger.add(sys.stderr, level=level, colorize=True, backtrace=True, diagnose=False)
        logger.add(
            file_path,
            level=level,
            rotation="10 MB",
            retention="14 days",
            compression="zip",
            enqueue=True,
            encoding="utf-8",
        )

        logger.success("Logger initialised → level={}, file={}.", level, file_path)
    except Exception as e:
        logger.error(f"Error in init_logger: {e}")
        raise
