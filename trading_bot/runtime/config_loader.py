from __future__ import annotations

import os
from copy import deepcopy
from pathlib import Path
from typing import Any, Dict, Optional

import yaml


def _deep_merge(base: Dict[str, Any], override: Dict[str, Any]) -> Dict[str, Any]:
    merged = deepcopy(base)
    for key, value in override.items():
        if isinstance(value, dict) and isinstance(merged.get(key), dict):
            merged[key] = _deep_merge(merged[key], value)
        else:
            merged[key] = value
    return merged


def _apply_env_overrides(config: Dict[str, Any]) -> Dict[str, Any]:
    trading = config.setdefault("trading", {})
    logging = config.setdefault("logging", {})
    account = config.setdefault("account", {})

    trading["mode"] = os.getenv("TRADING_MODE", trading.get("mode", "paper"))
    symbols_env = os.getenv("TRADING_SYMBOLS")
    if symbols_env:
        trading["symbols"] = [s.strip() for s in symbols_env.split(",") if s.strip()]

    logging["level"] = os.getenv("LOG_LEVEL", logging.get("level", "INFO"))

    if os.getenv("MT5_LOGIN"):
        account["mt5_login"] = os.getenv("MT5_LOGIN")
    if os.getenv("MT5_PASSWORD"):
        account["mt5_password"] = os.getenv("MT5_PASSWORD")
    if os.getenv("MT5_SERVER"):
        account["mt5_server"] = os.getenv("MT5_SERVER")

    monitoring = config.setdefault("monitoring", {})
    monitoring["health_port"] = int(os.getenv("HEALTH_PORT", monitoring.get("health_port", 8080)))
    monitoring["status_interval"] = int(os.getenv("STATUS_INTERVAL", monitoring.get("status_interval", 60)))

    return config


def load_runtime_config(config_path: Optional[str] = None, env: Optional[str] = None) -> Dict[str, Any]:
    """Load base config + environment override + env vars."""
    root = Path(__file__).resolve().parents[2]

    if config_path:
        with open(config_path, "r", encoding="utf-8") as fh:
            raw = yaml.safe_load(fh) or {}
        return _apply_env_overrides(raw)

    env_name = env or os.getenv("BOT_ENV", os.getenv("ENV", "development"))
    base_file = root / "config" / "base.yaml"
    env_file = root / "config" / "environments" / f"{env_name}.yaml"

    with open(base_file, "r", encoding="utf-8") as fh:
        base = yaml.safe_load(fh) or {}

    if env_file.exists():
        with open(env_file, "r", encoding="utf-8") as fh:
            override = yaml.safe_load(fh) or {}
    else:
        override = {}

    return _apply_env_overrides(_deep_merge(base, override))
