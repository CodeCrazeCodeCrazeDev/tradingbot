"""
Diagnostic Engine - Core detection system
==========================================
Scans for missing dependencies, bad configurations, missing API keys,
data health issues, connectivity problems, and structural issues.
"""

from __future__ import annotations

import asyncio
import importlib
import importlib.util
import json
import logging
import os
import platform
import shutil
import socket
import sqlite3
import subprocess
import sys
import time
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Enums & Data Classes
# ---------------------------------------------------------------------------

class DiagnosticCategory(Enum):
    DEPENDENCY = "dependency"
    CONFIGURATION = "configuration"
    API_KEY = "api_key"
    DATA = "data"
    CONNECTIVITY = "connectivity"
    FILESYSTEM = "filesystem"
    RUNTIME = "runtime"
    SECURITY = "security"


class DiagnosticSeverity(Enum):
    CRITICAL = "critical"      # Bot cannot run
    HIGH = "high"              # Major feature broken
    MEDIUM = "medium"          # Degraded functionality
    LOW = "low"                # Nice-to-have missing
    INFO = "info"              # Informational


@dataclass
class DiagnosticResult:
    """Single diagnostic finding."""
    check_id: str
    category: DiagnosticCategory
    severity: DiagnosticSeverity
    title: str
    message: str
    repairable: bool = False
    repair_hint: str = ""
    details: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.now)

    @property
    def passed(self) -> bool:
        return self.severity == DiagnosticSeverity.INFO

    def to_dict(self) -> Dict[str, Any]:
        return {
            "check_id": self.check_id,
            "category": self.category.value,
            "severity": self.severity.value,
            "title": self.title,
            "message": self.message,
            "repairable": self.repairable,
            "repair_hint": self.repair_hint,
            "details": self.details,
            "timestamp": self.timestamp.isoformat(),
        }


@dataclass
class DiagnosticReport:
    """Aggregated report from a full diagnostic run."""
    results: List[DiagnosticResult] = field(default_factory=list)
    started_at: datetime = field(default_factory=datetime.now)
    finished_at: Optional[datetime] = None
    system_info: Dict[str, Any] = field(default_factory=dict)

    @property
    def critical_count(self) -> int:
        return sum(1 for r in self.results if r.severity == DiagnosticSeverity.CRITICAL)

    @property
    def high_count(self) -> int:
        return sum(1 for r in self.results if r.severity == DiagnosticSeverity.HIGH)

    @property
    def repairable_count(self) -> int:
        return sum(1 for r in self.results if r.repairable and not r.passed)

    @property
    def total_issues(self) -> int:
        return sum(1 for r in self.results if not r.passed)

    @property
    def health_score(self) -> float:
        """0-100 health score."""
        if not self.results:
            return 100.0
        weights = {
            DiagnosticSeverity.CRITICAL: 20,
            DiagnosticSeverity.HIGH: 10,
            DiagnosticSeverity.MEDIUM: 5,
            DiagnosticSeverity.LOW: 2,
            DiagnosticSeverity.INFO: 0,
        }
        total_penalty = sum(weights.get(r.severity, 0) for r in self.results if not r.passed)
        return max(0.0, 100.0 - total_penalty)

    @property
    def is_runnable(self) -> bool:
        return self.critical_count == 0

    def summary(self) -> str:
        lines = [
            f"{'='*60}",
            f"  SELF-DIAGNOSTIC REPORT",
            f"  {self.started_at.strftime('%Y-%m-%d %H:%M:%S')}",
            f"{'='*60}",
            f"  Health Score : {self.health_score:.0f}/100",
            f"  Runnable     : {'YES' if self.is_runnable else 'NO'}",
            f"  Total Issues : {self.total_issues}",
            f"    Critical   : {self.critical_count}",
            f"    High       : {self.high_count}",
            f"    Repairable : {self.repairable_count}",
            f"{'='*60}",
        ]
        for r in self.results:
            if not r.passed:
                icon = {"critical": "🔴", "high": "🟠", "medium": "🟡", "low": "🔵"}.get(r.severity.value, "⚪")
                fix = " [AUTO-FIX]" if r.repairable else ""
                lines.append(f"  {icon} [{r.severity.value.upper()}] {r.title}{fix}")
                lines.append(f"     {r.message}")
        lines.append(f"{'='*60}")
        return "\n".join(lines)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "health_score": self.health_score,
            "is_runnable": self.is_runnable,
            "total_issues": self.total_issues,
            "critical_count": self.critical_count,
            "repairable_count": self.repairable_count,
            "started_at": self.started_at.isoformat(),
            "finished_at": self.finished_at.isoformat() if self.finished_at else None,
            "system_info": self.system_info,
            "results": [r.to_dict() for r in self.results],
        }


# ---------------------------------------------------------------------------
# Dependency Registry
# ---------------------------------------------------------------------------

# (import_name, pip_name, severity, description)
CORE_DEPENDENCIES: List[Tuple[str, str, DiagnosticSeverity, str]] = [
    ("numpy", "numpy", DiagnosticSeverity.CRITICAL, "Numerical computing"),
    ("pandas", "pandas", DiagnosticSeverity.CRITICAL, "Data manipulation"),
    ("MetaTrader5", "MetaTrader5", DiagnosticSeverity.CRITICAL, "MT5 broker connection"),
    ("loguru", "loguru", DiagnosticSeverity.CRITICAL, "Logging framework"),
    ("yaml", "PyYAML", DiagnosticSeverity.CRITICAL, "Config file parsing"),
    ("sklearn", "scikit-learn", DiagnosticSeverity.HIGH, "Machine learning"),
    ("tensorflow", "tensorflow", DiagnosticSeverity.MEDIUM, "Deep learning"),
    ("torch", "torch", DiagnosticSeverity.MEDIUM, "PyTorch deep learning"),
    ("scipy", "scipy", DiagnosticSeverity.HIGH, "Scientific computing"),
    ("statsmodels", "statsmodels", DiagnosticSeverity.HIGH, "Statistical models"),
    ("ta", "ta", DiagnosticSeverity.HIGH, "Technical analysis indicators"),
    ("aiohttp", "aiohttp", DiagnosticSeverity.HIGH, "Async HTTP client"),
    ("httpx", "httpx", DiagnosticSeverity.MEDIUM, "HTTP client"),
    ("psutil", "psutil", DiagnosticSeverity.HIGH, "System monitoring"),
    ("cryptography", "cryptography", DiagnosticSeverity.MEDIUM, "Encryption"),
    ("websockets", "websockets", DiagnosticSeverity.MEDIUM, "WebSocket support"),
    ("yfinance", "yfinance", DiagnosticSeverity.MEDIUM, "Yahoo Finance data"),
    ("faiss", "faiss-cpu", DiagnosticSeverity.LOW, "Vector similarity search"),
    ("plotly", "plotly", DiagnosticSeverity.LOW, "Interactive charts"),
    ("dash", "dash", DiagnosticSeverity.LOW, "Dashboard framework"),
    ("nltk", "nltk", DiagnosticSeverity.LOW, "NLP / sentiment"),
    ("gym", "gymnasium", DiagnosticSeverity.LOW, "RL environments"),
    ("redis", "redis", DiagnosticSeverity.LOW, "Redis cache"),
    ("celery", "celery", DiagnosticSeverity.LOW, "Task queue"),
]

# Config keys that should exist in config.yaml
REQUIRED_CONFIG_KEYS = {
    "mt5.path": DiagnosticSeverity.CRITICAL,
    "mt5.server": DiagnosticSeverity.HIGH,
    "trading.mode": DiagnosticSeverity.CRITICAL,
    "trading.risk_per_trade": DiagnosticSeverity.HIGH,
    "trading.max_positions": DiagnosticSeverity.HIGH,
    "logging.level": DiagnosticSeverity.MEDIUM,
    "database.path": DiagnosticSeverity.MEDIUM,
    "risk.max_drawdown_pct": DiagnosticSeverity.HIGH,
}

# API keys / env vars the bot may need
API_KEY_REGISTRY: List[Tuple[str, str, DiagnosticSeverity, str]] = [
    ("MT5_LOGIN", "mt5.login", DiagnosticSeverity.MEDIUM, "MT5 account login"),
    ("MT5_PASSWORD", "mt5.password", DiagnosticSeverity.MEDIUM, "MT5 account password"),
    ("MT5_SERVER", "mt5.server", DiagnosticSeverity.MEDIUM, "MT5 server name"),
    ("NEWSAPI_KEY", None, DiagnosticSeverity.LOW, "NewsAPI for sentiment"),
    ("ALPHA_VANTAGE_KEY", None, DiagnosticSeverity.LOW, "Alpha Vantage market data"),
    ("FRED_API_KEY", None, DiagnosticSeverity.LOW, "FRED economic data"),
    ("TELEGRAM_BOT_TOKEN", None, DiagnosticSeverity.LOW, "Telegram notifications"),
    ("OPENAI_API_KEY", None, DiagnosticSeverity.LOW, "OpenAI for NLP features"),
]

# Required directories
REQUIRED_DIRS = [
    "logs",
    "data",
    "models",
    "metrics",
    "alerts",
    "config",
    "backups",
]

# Required files
REQUIRED_FILES = [
    ("config/config.yaml", DiagnosticSeverity.CRITICAL),
    ("requirements.txt", DiagnosticSeverity.HIGH),
]


# ---------------------------------------------------------------------------
# Diagnostic Engine
# ---------------------------------------------------------------------------

class DiagnosticEngine:
    """
    Core engine that runs all diagnostic checks across 8 categories:
    1. Dependencies   - Python packages installed & importable
    2. Configuration  - config.yaml keys present & valid
    3. API Keys       - env vars / config credentials available
    4. Data           - database, data dirs, MT5 data access
    5. Connectivity   - internet, MT5 terminal, broker
    6. Filesystem     - required dirs/files exist, permissions ok
    7. Runtime        - Python version, memory, disk, CPU
    8. Security       - .env not committed, secrets not hardcoded
    """

    def __init__(self, project_root: Optional[str] = None):
        self.project_root = Path(project_root or self._detect_project_root())
        self._config_cache: Optional[Dict] = None

    @staticmethod
    def _detect_project_root() -> str:
        """Walk up from this file to find the project root (contains main.py)."""
        p = Path(__file__).resolve()
        for parent in [p] + list(p.parents):
            if (parent / "main.py").exists():
                return str(parent)
        return str(Path.cwd())

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    async def run_all(self) -> DiagnosticReport:
        """Run every diagnostic check and return a full report."""
        report = DiagnosticReport(system_info=self._collect_system_info())
        checkers = [
            self._check_dependencies,
            self._check_configuration,
            self._check_api_keys,
            self._check_data,
            self._check_connectivity,
            self._check_filesystem,
            self._check_runtime,
            self._check_security,
        ]
        for checker in checkers:
            try:
                results = await checker()
                report.results.extend(results)
            except Exception as e:
                report.results.append(DiagnosticResult(
                    check_id=f"engine.{checker.__name__}",
                    category=DiagnosticCategory.RUNTIME,
                    severity=DiagnosticSeverity.HIGH,
                    title=f"Diagnostic checker failed: {checker.__name__}",
                    message=str(e),
                ))
        report.finished_at = datetime.now()
        return report

    async def run_category(self, category: DiagnosticCategory) -> List[DiagnosticResult]:
        """Run checks for a single category."""
        mapping = {
            DiagnosticCategory.DEPENDENCY: self._check_dependencies,
            DiagnosticCategory.CONFIGURATION: self._check_configuration,
            DiagnosticCategory.API_KEY: self._check_api_keys,
            DiagnosticCategory.DATA: self._check_data,
            DiagnosticCategory.CONNECTIVITY: self._check_connectivity,
            DiagnosticCategory.FILESYSTEM: self._check_filesystem,
            DiagnosticCategory.RUNTIME: self._check_runtime,
            DiagnosticCategory.SECURITY: self._check_security,
        }
        checker = mapping.get(category)
        if checker:
            return await checker()
        return []

    # ------------------------------------------------------------------
    # 1. Dependency Checks
    # ------------------------------------------------------------------

    async def _check_dependencies(self) -> List[DiagnosticResult]:
        results = []
        for import_name, pip_name, severity, desc in CORE_DEPENDENCIES:
            check_id = f"dep.{import_name}"
            spec = importlib.util.find_spec(import_name)
            if spec is not None:
                # Verify it actually imports
                try:
                    importlib.import_module(import_name)
                    results.append(DiagnosticResult(
                        check_id=check_id,
                        category=DiagnosticCategory.DEPENDENCY,
                        severity=DiagnosticSeverity.INFO,
                        title=f"{import_name} installed",
                        message=f"{desc} package is available.",
                    ))
                except Exception as e:
                    results.append(DiagnosticResult(
                        check_id=check_id,
                        category=DiagnosticCategory.DEPENDENCY,
                        severity=severity,
                        title=f"{import_name} import fails",
                        message=f"Package found but import error: {e}",
                        repairable=True,
                        repair_hint=f"pip install --force-reinstall {pip_name}",
                        details={"pip_name": pip_name, "error": str(e)},
                    ))
            else:
                results.append(DiagnosticResult(
                    check_id=check_id,
                    category=DiagnosticCategory.DEPENDENCY,
                    severity=severity,
                    title=f"{import_name} missing",
                    message=f"{desc} package is not installed.",
                    repairable=True,
                    repair_hint=f"pip install {pip_name}",
                    details={"pip_name": pip_name},
                ))

        # Check requirements.txt sync
        req_file = self.project_root / "requirements.txt"
        if req_file.exists():
            try:
                installed = self._get_installed_packages()
                with open(req_file, "r", encoding="utf-8", errors="ignore") as f:
                    for line in f:
                        line = line.strip()
                        if not line or line.startswith("#") or line.startswith("-"):
                            continue
                        pkg = line.split("==")[0].split(">=")[0].split("<=")[0].split("~=")[0].strip().lower()
                        if pkg and pkg not in installed:
                            results.append(DiagnosticResult(
                                check_id=f"dep.req.{pkg}",
                                category=DiagnosticCategory.DEPENDENCY,
                                severity=DiagnosticSeverity.MEDIUM,
                                title=f"requirements.txt: {pkg} not installed",
                                message=f"Listed in requirements.txt but not found.",
                                repairable=True,
                                repair_hint=f"pip install {line}",
                                details={"pip_line": line},
                            ))
            except Exception as e:
                logger.warning(f"Could not parse requirements.txt: {e}")

        return results

    @staticmethod
    def _get_installed_packages() -> Set[str]:
        """Get set of installed package names (lowercase)."""
        try:
            result = subprocess.run(
                [sys.executable, "-m", "pip", "list", "--format=json"],
                capture_output=True, text=True, timeout=30,
            )
            if result.returncode == 0:
                pkgs = json.loads(result.stdout)
                return {p["name"].lower().replace("-", "_") for p in pkgs}
        except Exception:
            pass
        return set()

    # ------------------------------------------------------------------
    # 2. Configuration Checks
    # ------------------------------------------------------------------

    async def _check_configuration(self) -> List[DiagnosticResult]:
        results = []
        config_path = self.project_root / "config" / "config.yaml"

        if not config_path.exists():
            results.append(DiagnosticResult(
                check_id="cfg.file_missing",
                category=DiagnosticCategory.CONFIGURATION,
                severity=DiagnosticSeverity.CRITICAL,
                title="config.yaml missing",
                message=f"Configuration file not found at {config_path}",
                repairable=True,
                repair_hint="generate_default_config",
            ))
            return results

        cfg = self._load_config()
        if cfg is None:
            results.append(DiagnosticResult(
                check_id="cfg.parse_error",
                category=DiagnosticCategory.CONFIGURATION,
                severity=DiagnosticSeverity.CRITICAL,
                title="config.yaml parse error",
                message="Could not parse config.yaml - invalid YAML syntax.",
                repairable=True,
                repair_hint="regenerate_config",
            ))
            return results

        # Check required keys
        for dotted_key, severity in REQUIRED_CONFIG_KEYS.items():
            parts = dotted_key.split(".")
            val = cfg
            found = True
            for part in parts:
                if isinstance(val, dict) and part in val:
                    val = val[part]
                else:
                    found = False
                    break

            if not found:
                results.append(DiagnosticResult(
                    check_id=f"cfg.key.{dotted_key}",
                    category=DiagnosticCategory.CONFIGURATION,
                    severity=severity,
                    title=f"Config key missing: {dotted_key}",
                    message=f"Required configuration key '{dotted_key}' not found.",
                    repairable=True,
                    repair_hint=f"add_config_key:{dotted_key}",
                    details={"key": dotted_key},
                ))
            elif val is None or (isinstance(val, str) and not val.strip()):
                results.append(DiagnosticResult(
                    check_id=f"cfg.empty.{dotted_key}",
                    category=DiagnosticCategory.CONFIGURATION,
                    severity=DiagnosticSeverity.MEDIUM if severity != DiagnosticSeverity.CRITICAL else severity,
                    title=f"Config key empty: {dotted_key}",
                    message=f"Configuration key '{dotted_key}' is empty.",
                    repairable=True,
                    repair_hint=f"set_config_default:{dotted_key}",
                    details={"key": dotted_key, "current_value": val},
                ))
            else:
                results.append(DiagnosticResult(
                    check_id=f"cfg.key.{dotted_key}",
                    category=DiagnosticCategory.CONFIGURATION,
                    severity=DiagnosticSeverity.INFO,
                    title=f"Config OK: {dotted_key}",
                    message=f"Key present with value.",
                ))

        # Validate trading mode
        mode = self._get_nested(cfg, "trading.mode")
        if mode and mode not in ("paper", "live", "backtest"):
            results.append(DiagnosticResult(
                check_id="cfg.invalid.trading_mode",
                category=DiagnosticCategory.CONFIGURATION,
                severity=DiagnosticSeverity.HIGH,
                title="Invalid trading mode",
                message=f"trading.mode='{mode}' is not valid. Must be paper/live/backtest.",
                repairable=True,
                repair_hint="set_config:trading.mode=paper",
            ))

        # Validate risk limits
        risk_per_trade = self._get_nested(cfg, "trading.risk_per_trade")
        if risk_per_trade is not None:
            try:
                rpt = float(risk_per_trade)
                if rpt > 0.05:
                    results.append(DiagnosticResult(
                        check_id="cfg.risk.too_high",
                        category=DiagnosticCategory.CONFIGURATION,
                        severity=DiagnosticSeverity.HIGH,
                        title="Risk per trade too high",
                        message=f"risk_per_trade={rpt} (>{0.05}). Dangerously high.",
                        repairable=True,
                        repair_hint="set_config:trading.risk_per_trade=0.01",
                    ))
            except (ValueError, TypeError):
                pass

        # Validate MT5 path exists
        mt5_path = self._get_nested(cfg, "mt5.path")
        if mt5_path and not Path(mt5_path).exists():
            results.append(DiagnosticResult(
                check_id="cfg.mt5_path_invalid",
                category=DiagnosticCategory.CONFIGURATION,
                severity=DiagnosticSeverity.HIGH,
                title="MT5 terminal path invalid",
                message=f"MT5 path '{mt5_path}' does not exist.",
                repairable=True,
                repair_hint="find_mt5_path",
                details={"configured_path": mt5_path},
            ))

        return results

    # ------------------------------------------------------------------
    # 3. API Key Checks
    # ------------------------------------------------------------------

    async def _check_api_keys(self) -> List[DiagnosticResult]:
        results = []
        cfg = self._load_config() or {}

        for env_var, config_key, severity, desc in API_KEY_REGISTRY:
            check_id = f"api.{env_var.lower()}"
            env_val = os.environ.get(env_var, "")
            cfg_val = ""
            if config_key:
                cfg_val = str(self._get_nested(cfg, config_key) or "")

            has_value = bool(env_val.strip()) or bool(cfg_val.strip())

            if has_value:
                # Check if it looks like a placeholder
                placeholders = {"your_key_here", "xxx", "changeme", "TODO", "REPLACE_ME", "0"}
                actual = (env_val.strip() or cfg_val.strip()).lower()
                if actual in placeholders:
                    results.append(DiagnosticResult(
                        check_id=check_id,
                        category=DiagnosticCategory.API_KEY,
                        severity=severity,
                        title=f"{env_var}: placeholder value",
                        message=f"{desc} has a placeholder value, not a real key.",
                        repairable=True,
                        repair_hint=f"prompt_api_key:{env_var}",
                        details={"env_var": env_var, "config_key": config_key},
                    ))
                else:
                    results.append(DiagnosticResult(
                        check_id=check_id,
                        category=DiagnosticCategory.API_KEY,
                        severity=DiagnosticSeverity.INFO,
                        title=f"{env_var}: configured",
                        message=f"{desc} key is set.",
                    ))
            else:
                results.append(DiagnosticResult(
                    check_id=check_id,
                    category=DiagnosticCategory.API_KEY,
                    severity=severity,
                    title=f"{env_var}: not set",
                    message=f"{desc} key is missing. Set via env var {env_var}" +
                            (f" or config key {config_key}" if config_key else ""),
                    repairable=True,
                    repair_hint=f"create_env_template:{env_var}",
                    details={"env_var": env_var, "config_key": config_key},
                ))

        # Check for .env file
        env_file = self.project_root / ".env"
        if not env_file.exists():
            results.append(DiagnosticResult(
                check_id="api.env_file_missing",
                category=DiagnosticCategory.API_KEY,
                severity=DiagnosticSeverity.MEDIUM,
                title=".env file missing",
                message="No .env file found. API keys should be stored in .env for safety.",
                repairable=True,
                repair_hint="create_env_file",
            ))

        return results

    # ------------------------------------------------------------------
    # 4. Data Checks
    # ------------------------------------------------------------------

    async def _check_data(self) -> List[DiagnosticResult]:
        results = []

        # Check database
        cfg = self._load_config() or {}
        db_path_str = self._get_nested(cfg, "database.path") or "data/trading_bot.db"
        db_path = self.project_root / db_path_str

        if db_path.exists():
            try:
                conn = sqlite3.connect(str(db_path))
                cursor = conn.cursor()
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
                tables = [row[0] for row in cursor.fetchall()]
                conn.close()
                results.append(DiagnosticResult(
                    check_id="data.db_ok",
                    category=DiagnosticCategory.DATA,
                    severity=DiagnosticSeverity.INFO,
                    title="Database accessible",
                    message=f"SQLite DB has {len(tables)} tables: {', '.join(tables[:10])}",
                    details={"tables": tables, "path": str(db_path)},
                ))
            except Exception as e:
                results.append(DiagnosticResult(
                    check_id="data.db_corrupt",
                    category=DiagnosticCategory.DATA,
                    severity=DiagnosticSeverity.HIGH,
                    title="Database corrupted",
                    message=f"Cannot read database: {e}",
                    repairable=True,
                    repair_hint="recreate_database",
                    details={"path": str(db_path), "error": str(e)},
                ))
        else:
            results.append(DiagnosticResult(
                check_id="data.db_missing",
                category=DiagnosticCategory.DATA,
                severity=DiagnosticSeverity.MEDIUM,
                title="Database not found",
                message=f"Database file not found at {db_path}. Will be created on first run.",
                repairable=True,
                repair_hint="create_database",
                details={"path": str(db_path)},
            ))

        # Check data directory for stale files
        data_dir = self.project_root / "data"
        if data_dir.exists():
            total_size = sum(f.stat().st_size for f in data_dir.rglob("*") if f.is_file())
            file_count = sum(1 for f in data_dir.rglob("*") if f.is_file())
            results.append(DiagnosticResult(
                check_id="data.dir_stats",
                category=DiagnosticCategory.DATA,
                severity=DiagnosticSeverity.INFO,
                title="Data directory stats",
                message=f"{file_count} files, {total_size / 1024 / 1024:.1f} MB total.",
                details={"file_count": file_count, "total_bytes": total_size},
            ))

            # Check for very old data files (>30 days)
            stale_cutoff = datetime.now() - timedelta(days=30)
            stale_files = []
            for f in data_dir.rglob("*.csv"):
                if datetime.fromtimestamp(f.stat().st_mtime) < stale_cutoff:
                    stale_files.append(str(f.name))
            if stale_files:
                results.append(DiagnosticResult(
                    check_id="data.stale_files",
                    category=DiagnosticCategory.DATA,
                    severity=DiagnosticSeverity.LOW,
                    title=f"{len(stale_files)} stale data files",
                    message="CSV files older than 30 days found in data/.",
                    repairable=True,
                    repair_hint="archive_stale_data",
                    details={"stale_files": stale_files[:20]},
                ))

        # Check logs directory size
        logs_dir = self.project_root / "logs"
        if logs_dir.exists():
            log_size = sum(f.stat().st_size for f in logs_dir.rglob("*") if f.is_file())
            if log_size > 100 * 1024 * 1024:  # >100MB
                results.append(DiagnosticResult(
                    check_id="data.logs_large",
                    category=DiagnosticCategory.DATA,
                    severity=DiagnosticSeverity.MEDIUM,
                    title="Log directory too large",
                    message=f"Logs directory is {log_size / 1024 / 1024:.0f} MB. Consider rotation.",
                    repairable=True,
                    repair_hint="rotate_logs",
                    details={"size_mb": log_size / 1024 / 1024},
                ))

        # Check models directory
        models_dir = self.project_root / "models"
        if models_dir.exists():
            model_count = sum(1 for f in models_dir.rglob("*") if f.is_file())
            results.append(DiagnosticResult(
                check_id="data.models",
                category=DiagnosticCategory.DATA,
                severity=DiagnosticSeverity.INFO,
                title=f"Models directory: {model_count} files",
                message="Model storage accessible.",
            ))

        return results

    # ------------------------------------------------------------------
    # 5. Connectivity Checks
    # ------------------------------------------------------------------

    async def _check_connectivity(self) -> List[DiagnosticResult]:
        results = []

        # Internet connectivity
        internet_ok = await self._check_internet()
        if internet_ok:
            results.append(DiagnosticResult(
                check_id="conn.internet",
                category=DiagnosticCategory.CONNECTIVITY,
                severity=DiagnosticSeverity.INFO,
                title="Internet connected",
                message="Can reach external hosts.",
            ))
        else:
            results.append(DiagnosticResult(
                check_id="conn.internet",
                category=DiagnosticCategory.CONNECTIVITY,
                severity=DiagnosticSeverity.MEDIUM,
                title="Internet check inconclusive",
                message="Could not verify internet via HTTP. MT5 may still connect directly.",
                repairable=False,
            ))

        # MT5 terminal running
        mt5_running = self._check_process_running("terminal64.exe")
        if mt5_running:
            results.append(DiagnosticResult(
                check_id="conn.mt5_process",
                category=DiagnosticCategory.CONNECTIVITY,
                severity=DiagnosticSeverity.INFO,
                title="MT5 terminal running",
                message="MetaTrader 5 terminal process detected.",
            ))
        else:
            results.append(DiagnosticResult(
                check_id="conn.mt5_process",
                category=DiagnosticCategory.CONNECTIVITY,
                severity=DiagnosticSeverity.HIGH,
                title="MT5 terminal not running",
                message="MetaTrader 5 terminal is not running. Start it for live data.",
                repairable=True,
                repair_hint="start_mt5",
            ))

        # MT5 API status (passive check - do NOT call mt5.initialize/shutdown
        # as that would kill the main bot's active connection)
        if mt5_running:
            results.append(DiagnosticResult(
                check_id="conn.mt5_api",
                category=DiagnosticCategory.CONNECTIVITY,
                severity=DiagnosticSeverity.INFO,
                title="MT5 API: terminal process active",
                message="MT5 terminal is running. API assumed available.",
            ))
        else:
            results.append(DiagnosticResult(
                check_id="conn.mt5_api",
                category=DiagnosticCategory.CONNECTIVITY,
                severity=DiagnosticSeverity.HIGH,
                title="MT5 API: terminal not running",
                message="MT5 terminal process not found. Start it for data access.",
                repairable=True,
                repair_hint="start_mt5",
            ))

        return results

    # ------------------------------------------------------------------
    # 6. Filesystem Checks
    # ------------------------------------------------------------------

    async def _check_filesystem(self) -> List[DiagnosticResult]:
        results = []

        # Required directories
        for dir_name in REQUIRED_DIRS:
            dir_path = self.project_root / dir_name
            if dir_path.exists():
                results.append(DiagnosticResult(
                    check_id=f"fs.dir.{dir_name}",
                    category=DiagnosticCategory.FILESYSTEM,
                    severity=DiagnosticSeverity.INFO,
                    title=f"Directory exists: {dir_name}/",
                    message="OK",
                ))
            else:
                results.append(DiagnosticResult(
                    check_id=f"fs.dir.{dir_name}",
                    category=DiagnosticCategory.FILESYSTEM,
                    severity=DiagnosticSeverity.MEDIUM,
                    title=f"Directory missing: {dir_name}/",
                    message=f"Required directory '{dir_name}' does not exist.",
                    repairable=True,
                    repair_hint=f"create_directory:{dir_name}",
                ))

        # Required files
        for file_rel, severity in REQUIRED_FILES:
            file_path = self.project_root / file_rel
            if file_path.exists():
                results.append(DiagnosticResult(
                    check_id=f"fs.file.{file_rel}",
                    category=DiagnosticCategory.FILESYSTEM,
                    severity=DiagnosticSeverity.INFO,
                    title=f"File exists: {file_rel}",
                    message="OK",
                ))
            else:
                results.append(DiagnosticResult(
                    check_id=f"fs.file.{file_rel}",
                    category=DiagnosticCategory.FILESYSTEM,
                    severity=severity,
                    title=f"File missing: {file_rel}",
                    message=f"Required file '{file_rel}' not found.",
                    repairable=True,
                    repair_hint=f"create_file:{file_rel}",
                ))

        # Disk space
        try:
            usage = shutil.disk_usage(str(self.project_root))
            free_gb = usage.free / (1024 ** 3)
            if free_gb < 1.0:
                results.append(DiagnosticResult(
                    check_id="fs.disk_low",
                    category=DiagnosticCategory.FILESYSTEM,
                    severity=DiagnosticSeverity.HIGH,
                    title="Low disk space",
                    message=f"Only {free_gb:.1f} GB free. Bot needs space for data/logs.",
                    repairable=True,
                    repair_hint="cleanup_disk",
                    details={"free_gb": free_gb},
                ))
            else:
                results.append(DiagnosticResult(
                    check_id="fs.disk_ok",
                    category=DiagnosticCategory.FILESYSTEM,
                    severity=DiagnosticSeverity.INFO,
                    title="Disk space OK",
                    message=f"{free_gb:.1f} GB free.",
                ))
        except Exception:
            pass

        # Write permission test
        test_file = self.project_root / ".diag_write_test"
        try:
            test_file.write_text("test")
            test_file.unlink()
            results.append(DiagnosticResult(
                check_id="fs.writable",
                category=DiagnosticCategory.FILESYSTEM,
                severity=DiagnosticSeverity.INFO,
                title="Project directory writable",
                message="OK",
            ))
        except Exception as e:
            results.append(DiagnosticResult(
                check_id="fs.writable",
                category=DiagnosticCategory.FILESYSTEM,
                severity=DiagnosticSeverity.CRITICAL,
                title="Project directory not writable",
                message=f"Cannot write to project root: {e}",
            ))

        return results

    # ------------------------------------------------------------------
    # 7. Runtime Checks
    # ------------------------------------------------------------------

    async def _check_runtime(self) -> List[DiagnosticResult]:
        results = []

        # Python version
        ver = sys.version_info
        results.append(DiagnosticResult(
            check_id="rt.python_version",
            category=DiagnosticCategory.RUNTIME,
            severity=DiagnosticSeverity.INFO if ver >= (3, 10) else DiagnosticSeverity.HIGH,
            title=f"Python {ver.major}.{ver.minor}.{ver.micro}",
            message="OK" if ver >= (3, 10) else "Python 3.10+ recommended.",
            details={"version": f"{ver.major}.{ver.minor}.{ver.micro}"},
        ))

        # Memory
        try:
            import psutil
            mem = psutil.virtual_memory()
            avail_gb = mem.available / (1024 ** 3)
            total_gb = mem.total / (1024 ** 3)
            if avail_gb < 1.0:
                sev = DiagnosticSeverity.HIGH
            elif avail_gb < 2.0:
                sev = DiagnosticSeverity.MEDIUM
            else:
                sev = DiagnosticSeverity.INFO
            results.append(DiagnosticResult(
                check_id="rt.memory",
                category=DiagnosticCategory.RUNTIME,
                severity=sev,
                title=f"Memory: {avail_gb:.1f}/{total_gb:.1f} GB available",
                message="Low memory may cause OOM." if sev != DiagnosticSeverity.INFO else "OK",
                details={"available_gb": avail_gb, "total_gb": total_gb, "percent_used": mem.percent},
            ))

            # CPU
            cpu_pct = psutil.cpu_percent(interval=0.5)
            results.append(DiagnosticResult(
                check_id="rt.cpu",
                category=DiagnosticCategory.RUNTIME,
                severity=DiagnosticSeverity.INFO if cpu_pct < 80 else DiagnosticSeverity.MEDIUM,
                title=f"CPU: {cpu_pct:.0f}% used",
                message="OK" if cpu_pct < 80 else "High CPU usage may slow trading.",
                details={"cpu_percent": cpu_pct, "cpu_count": psutil.cpu_count()},
            ))
        except ImportError:
            results.append(DiagnosticResult(
                check_id="rt.psutil_missing",
                category=DiagnosticCategory.RUNTIME,
                severity=DiagnosticSeverity.MEDIUM,
                title="psutil not available",
                message="Cannot check system resources without psutil.",
                repairable=True,
                repair_hint="pip install psutil",
            ))

        # OS info
        results.append(DiagnosticResult(
            check_id="rt.os",
            category=DiagnosticCategory.RUNTIME,
            severity=DiagnosticSeverity.INFO,
            title=f"OS: {platform.system()} {platform.release()}",
            message=f"{platform.platform()}",
        ))

        return results

    # ------------------------------------------------------------------
    # 8. Security Checks
    # ------------------------------------------------------------------

    async def _check_security(self) -> List[DiagnosticResult]:
        results = []

        # Check .gitignore includes .env
        gitignore = self.project_root / ".gitignore"
        if gitignore.exists():
            content = gitignore.read_text(encoding="utf-8", errors="ignore")
            if ".env" not in content:
                results.append(DiagnosticResult(
                    check_id="sec.gitignore_env",
                    category=DiagnosticCategory.SECURITY,
                    severity=DiagnosticSeverity.HIGH,
                    title=".env not in .gitignore",
                    message="API keys in .env could be committed to git.",
                    repairable=True,
                    repair_hint="add_gitignore_env",
                ))
        else:
            results.append(DiagnosticResult(
                check_id="sec.no_gitignore",
                category=DiagnosticCategory.SECURITY,
                severity=DiagnosticSeverity.MEDIUM,
                title="No .gitignore file",
                message="Consider adding .gitignore to protect secrets.",
                repairable=True,
                repair_hint="create_gitignore",
            ))

        # Scan config for hardcoded secrets
        config_path = self.project_root / "config" / "config.yaml"
        if config_path.exists():
            content = config_path.read_text(encoding="utf-8", errors="ignore")
            secret_patterns = ["api_key:", "secret:", "token:", "password:"]
            for pattern in secret_patterns:
                for line in content.splitlines():
                    stripped = line.strip().lower()
                    if stripped.startswith(pattern):
                        val = line.split(":", 1)[1].strip().strip('"').strip("'")
                        if val and val not in ("", "null", "~", '""', "''", "0"):
                            results.append(DiagnosticResult(
                                check_id=f"sec.hardcoded.{pattern.rstrip(':')}",
                                category=DiagnosticCategory.SECURITY,
                                severity=DiagnosticSeverity.HIGH,
                                title=f"Possible hardcoded secret: {pattern}",
                                message="Secrets should be in .env, not config.yaml.",
                                repairable=True,
                                repair_hint="move_secret_to_env",
                            ))
                            break

        # Check if running as admin (risky)
        try:
            import ctypes
            is_admin = ctypes.windll.shell32.IsUserAnAdmin() != 0
            if is_admin:
                results.append(DiagnosticResult(
                    check_id="sec.admin",
                    category=DiagnosticCategory.SECURITY,
                    severity=DiagnosticSeverity.MEDIUM,
                    title="Running as administrator",
                    message="Running as admin is unnecessary and risky.",
                ))
        except Exception:
            pass

        if not results:
            results.append(DiagnosticResult(
                check_id="sec.ok",
                category=DiagnosticCategory.SECURITY,
                severity=DiagnosticSeverity.INFO,
                title="Security checks passed",
                message="No obvious security issues found.",
            ))

        return results

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _load_config(self) -> Optional[Dict]:
        if self._config_cache is not None:
            return self._config_cache
        config_path = self.project_root / "config" / "config.yaml"
        if not config_path.exists():
            return None
        try:
            import yaml
            with open(config_path, "r", encoding="utf-8") as f:
                self._config_cache = yaml.safe_load(f) or {}
            return self._config_cache
        except Exception:
            return None

    @staticmethod
    def _get_nested(d: Dict, dotted_key: str) -> Any:
        parts = dotted_key.split(".")
        val = d
        for part in parts:
            if isinstance(val, dict) and part in val:
                val = val[part]
            else:
                return None
        return val

    @staticmethod
    async def _check_internet() -> bool:
        # Try HTTP first (more reliable through firewalls)
        import urllib.request
        urls = ["http://www.google.com", "http://www.microsoft.com", "http://httpbin.org/get"]
        for url in urls:
            try:
                req = urllib.request.Request(url, method="HEAD")
                urllib.request.urlopen(req, timeout=5)
                return True
            except Exception:
                continue
        # Fallback to raw socket
        hosts = [("8.8.8.8", 53), ("1.1.1.1", 53)]
        for host, port in hosts:
            try:
                sock = socket.create_connection((host, port), timeout=3)
                sock.close()
                return True
            except OSError:
                continue
        return False

    @staticmethod
    def _check_process_running(name: str) -> bool:
        try:
            import psutil
            for proc in psutil.process_iter(["name"]):
                if proc.info["name"] and proc.info["name"].lower() == name.lower():
                    return True
        except Exception:
            pass
        return False

    def _collect_system_info(self) -> Dict[str, Any]:
        info = {
            "python_version": f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}",
            "platform": platform.platform(),
            "project_root": str(self.project_root),
            "timestamp": datetime.now().isoformat(),
        }
        try:
            import psutil
            mem = psutil.virtual_memory()
            info["memory_total_gb"] = round(mem.total / (1024 ** 3), 1)
            info["memory_available_gb"] = round(mem.available / (1024 ** 3), 1)
            info["cpu_count"] = psutil.cpu_count()
        except ImportError:
            pass
        return info
