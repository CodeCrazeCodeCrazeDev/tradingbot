"""Minimal local fallback for `loguru` when external dependency is unavailable.

This shim provides a subset of the API used in this repository so imports like
`from loguru import logger` keep working in constrained/offline environments.
"""

from __future__ import annotations

import logging
from typing import Any


class _FallbackLogger:
    def __init__(self) -> None:
        self._logger = logging.getLogger("loguru_fallback")
        if not logging.getLogger().handlers:
            logging.basicConfig(level=logging.INFO)

    def _log(self, level: int, message: Any, *args: Any, **kwargs: Any) -> None:
        text = str(message)
        if args or kwargs:
            try:
                text = text.format(*args, **kwargs)
            except Exception:
                text = f"{text} | args={args} kwargs={kwargs}"
        self._logger.log(level, text)

    def debug(self, message: Any, *args: Any, **kwargs: Any) -> None:
        self._log(logging.DEBUG, message, *args, **kwargs)

    def info(self, message: Any, *args: Any, **kwargs: Any) -> None:
        self._log(logging.INFO, message, *args, **kwargs)

    def warning(self, message: Any, *args: Any, **kwargs: Any) -> None:
        self._log(logging.WARNING, message, *args, **kwargs)

    def error(self, message: Any, *args: Any, **kwargs: Any) -> None:
        self._log(logging.ERROR, message, *args, **kwargs)

    def critical(self, message: Any, *args: Any, **kwargs: Any) -> None:
        self._log(logging.CRITICAL, message, *args, **kwargs)

    def exception(self, message: Any, *args: Any, **kwargs: Any) -> None:
        text = str(message)
        if args or kwargs:
            try:
                text = text.format(*args, **kwargs)
            except Exception:
                text = f"{text} | args={args} kwargs={kwargs}"
        self._logger.exception(text)

    def success(self, message: Any, *args: Any, **kwargs: Any) -> None:
        # map loguru's SUCCESS to INFO in fallback mode
        self._log(logging.INFO, message, *args, **kwargs)

    def bind(self, **_: Any) -> "_FallbackLogger":
        return self

    def add(self, *_: Any, **__: Any) -> int:
        # no-op sink registration
        return 0

    def remove(self, *_: Any, **__: Any) -> None:
        # no-op sink removal
        return None


logger = _FallbackLogger()
