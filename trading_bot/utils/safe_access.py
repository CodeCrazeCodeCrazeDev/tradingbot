"""Utility helpers for safe attribute/dictionary access.

This module provides `safe_get`, which can be used as a drop-in replacement for
`dict.get` when the object might actually be an attr-based object. It is useful
when downstream code sometimes passes plain dictionaries and sometimes passes
custom data-class / object instances.
"""
from typing import Any

import logging
logger = logging.getLogger(__name__)



def safe_get(obj: Any, key: str, default: Any | None = None) -> Any:
    """Return *obj[key]* if *obj* behaves like a mapping, else *getattr(obj, key)*.

    Args:
        obj: Mapping or object instance.
        key: Attribute or key name to retrieve.
        default: Fallback value if *key* not present.

    Returns:
        The retrieved value or *default* if not present.
    """
    try:
        if isinstance(obj, dict):
            return obj.get(key, default)
        return getattr(obj, key, default)
    except Exception as e:
        logger.error(f"Error in safe_get: {e}")
        raise
