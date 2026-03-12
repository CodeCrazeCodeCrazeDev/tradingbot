"""
Auto-Repair Engine
===================
Takes diagnostic results and automatically fixes repairable issues:
- Installs missing Python packages
- Creates missing directories and files
- Generates default config values
- Creates .env templates
- Fixes database issues
- Rotates oversized logs
- Starts MT5 terminal
- Cleans up stale data
"""

from __future__ import annotations

import json
import logging
import os
import shutil
import sqlite3
import subprocess
import sys
import time
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

from .diagnostic_engine import (
    DiagnosticCategory,
    DiagnosticReport,
    DiagnosticResult,
    DiagnosticSeverity,
)

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Data Classes
# ---------------------------------------------------------------------------

class RepairStatus(Enum):
    SUCCESS = "success"
    FAILED = "failed"
    SKIPPED = "skipped"
    NEEDS_HUMAN = "needs_human"


@dataclass
class RepairAction:
    """A single repair action to execute."""
    action_id: str
    description: str
    category: DiagnosticCategory
    severity: DiagnosticSeverity
    hint: str
    details: Dict[str, Any] = field(default_factory=dict)


@dataclass
class RepairResult:
    """Result of a single repair attempt."""
    action: RepairAction
    status: RepairStatus
    message: str
    duration_ms: float = 0.0
    timestamp: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "action_id": self.action.action_id,
            "description": self.action.description,
            "status": self.status.value,
            "message": self.message,
            "duration_ms": self.duration_ms,
            "timestamp": self.timestamp.isoformat(),
        }


@dataclass
class RepairReport:
    """Aggregated repair results."""
    results: List[RepairResult] = field(default_factory=list)
    started_at: datetime = field(default_factory=datetime.now)
    finished_at: Optional[datetime] = None

    @property
    def success_count(self) -> int:
        return sum(1 for r in self.results if r.status == RepairStatus.SUCCESS)

    @property
    def failed_count(self) -> int:
        return sum(1 for r in self.results if r.status == RepairStatus.FAILED)

    @property
    def human_count(self) -> int:
        return sum(1 for r in self.results if r.status == RepairStatus.NEEDS_HUMAN)

    def summary(self) -> str:
        lines = [
            f"{'='*60}",
            f"  AUTO-REPAIR REPORT",
            f"  {self.started_at.strftime('%Y-%m-%d %H:%M:%S')}",
            f"{'='*60}",
            f"  Total Actions : {len(self.results)}",
            f"  Succeeded     : {self.success_count}",
            f"  Failed        : {self.failed_count}",
            f"  Needs Human   : {self.human_count}",
            f"{'='*60}",
        ]
        for r in self.results:
            icon = {"success": "✅", "failed": "❌", "skipped": "⏭️", "needs_human": "👤"}.get(r.status.value, "❓")
            lines.append(f"  {icon} {r.action.description}")
            lines.append(f"     {r.message} ({r.duration_ms:.0f}ms)")
        lines.append(f"{'='*60}")
        return "\n".join(lines)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "success_count": self.success_count,
            "failed_count": self.failed_count,
            "human_count": self.human_count,
            "started_at": self.started_at.isoformat(),
            "finished_at": self.finished_at.isoformat() if self.finished_at else None,
            "results": [r.to_dict() for r in self.results],
        }


# ---------------------------------------------------------------------------
# Default Config Template
# ---------------------------------------------------------------------------

DEFAULT_CONFIG_YAML = """\
mt5:
  path: "C:/Program Files/MetaTrader 5/terminal64.exe"
  server: "MetaQuotes-Demo"
  login: 0
  password: ""
  timeout: 60000
  symbols:
  - EURUSD
  - GBPUSD
  - USDJPY
  timeframes:
  - M15
  - H1
  - H4
  - D1
trading:
  mode: "paper"
  risk_per_trade: 0.01
  max_positions: 5
  position_sizing: risk_based
  stop_loss_atr_multiplier: 2.0
  take_profit_rr_ratio: 2.0
logging:
  level: INFO
  file: logs/trading_bot.log
  format: '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
  max_size: 10485760
  backup_count: 5
database:
  type: sqlite
  path: data/trading_bot.db
  backup_enabled: true
  backup_interval: 86400
risk:
  max_position_size: 0.01
  min_position_size: 0.01
  risk_per_trade_pct: 1.0
  max_drawdown_pct: 20.0
  position_size_rounding: 0.01
"""

DEFAULT_CONFIG_DEFAULTS = {
    "mt5.path": "C:/Program Files/MetaTrader 5/terminal64.exe",
    "mt5.server": "MetaQuotes-Demo",
    "trading.mode": "paper",
    "trading.risk_per_trade": 0.01,
    "trading.max_positions": 5,
    "logging.level": "INFO",
    "database.path": "data/trading_bot.db",
    "risk.max_drawdown_pct": 20.0,
}

ENV_TEMPLATE = """\
# ============================================================
# Trading Bot Environment Variables
# ============================================================
# Copy this file to .env and fill in your values.
# NEVER commit .env to version control!
# ============================================================

# --- MetaTrader 5 ---
MT5_LOGIN=
MT5_PASSWORD=
MT5_SERVER=MetaQuotes-Demo

# --- Data APIs (optional, for enhanced features) ---
NEWSAPI_KEY=
ALPHA_VANTAGE_KEY=
FRED_API_KEY=

# --- Notifications (optional) ---
TELEGRAM_BOT_TOKEN=
TELEGRAM_CHAT_ID=

# --- AI/ML (optional) ---
OPENAI_API_KEY=
"""

GITIGNORE_ENTRIES = """\
# Secrets
.env
.env.*

# Data
data/*.db
data/*.csv
*.log

# Python
__pycache__/
*.pyc
*.pyo
.eggs/
*.egg-info/

# IDE
.vscode/
.idea/

# OS
Thumbs.db
.DS_Store

# Diagnostics
.diag_write_test
"""


# ---------------------------------------------------------------------------
# Auto-Repair Engine
# ---------------------------------------------------------------------------

class AutoRepairEngine:
    """
    Executes repair actions based on diagnostic results.
    
    Repair strategies by category:
    - DEPENDENCY:    pip install missing packages
    - CONFIGURATION: generate/fix config.yaml keys
    - API_KEY:       create .env template, prompt user
    - DATA:          create DB, archive stale files, rotate logs
    - CONNECTIVITY:  start MT5 terminal
    - FILESYSTEM:    create missing dirs/files
    - SECURITY:      add .gitignore entries, move secrets
    """

    # Maximum packages to install in a single repair run
    MAX_PIP_INSTALLS = 20
    # Packages that are known to be problematic / very large
    SKIP_AUTO_INSTALL = {"tensorflow", "torch", "pytorch", "talib", "ta-lib"}

    def __init__(self, project_root: Optional[str] = None):
        if project_root:
            self.project_root = Path(project_root)
        else:
            p = Path(__file__).resolve()
            for parent in [p] + list(p.parents):
                if (parent / "main.py").exists():
                    self.project_root = parent
                    break
            else:
                self.project_root = Path.cwd()

        self._repair_log: List[RepairResult] = []
        self._repair_handlers: Dict[str, Callable] = {
            "pip install": self._repair_pip_install,
            "pip install --force-reinstall": self._repair_pip_reinstall,
            "generate_default_config": self._repair_generate_config,
            "regenerate_config": self._repair_generate_config,
            "add_config_key": self._repair_add_config_key,
            "set_config_default": self._repair_set_config_default,
            "set_config": self._repair_set_config,
            "find_mt5_path": self._repair_find_mt5_path,
            "create_env_template": self._repair_create_env_template,
            "create_env_file": self._repair_create_env_file,
            "prompt_api_key": self._repair_prompt_api_key,
            "create_database": self._repair_create_database,
            "recreate_database": self._repair_recreate_database,
            "archive_stale_data": self._repair_archive_stale_data,
            "rotate_logs": self._repair_rotate_logs,
            "create_directory": self._repair_create_directory,
            "create_file": self._repair_create_file,
            "start_mt5": self._repair_start_mt5,
            "restart_mt5": self._repair_start_mt5,
            "cleanup_disk": self._repair_cleanup_disk,
            "add_gitignore_env": self._repair_add_gitignore,
            "create_gitignore": self._repair_create_gitignore,
            "move_secret_to_env": self._repair_move_secret_to_env,
        }

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    async def repair_all(self, report: DiagnosticReport, dry_run: bool = False) -> RepairReport:
        """Attempt to repair all repairable issues from a diagnostic report."""
        repair_report = RepairReport()
        repairable = [r for r in report.results if r.repairable and not r.passed]

        # Sort: critical first
        severity_order = {
            DiagnosticSeverity.CRITICAL: 0,
            DiagnosticSeverity.HIGH: 1,
            DiagnosticSeverity.MEDIUM: 2,
            DiagnosticSeverity.LOW: 3,
        }
        repairable.sort(key=lambda r: severity_order.get(r.severity, 99))

        pip_count = 0
        for diag in repairable:
            action = RepairAction(
                action_id=diag.check_id,
                description=f"Fix: {diag.title}",
                category=diag.category,
                severity=diag.severity,
                hint=diag.repair_hint,
                details=diag.details,
            )

            if dry_run:
                repair_report.results.append(RepairResult(
                    action=action,
                    status=RepairStatus.SKIPPED,
                    message=f"Dry run: would execute '{diag.repair_hint}'",
                ))
                continue

            # Rate-limit pip installs
            if diag.repair_hint.startswith("pip install"):
                pip_name = diag.details.get("pip_name", "")
                if pip_name.lower() in self.SKIP_AUTO_INSTALL:
                    repair_report.results.append(RepairResult(
                        action=action,
                        status=RepairStatus.NEEDS_HUMAN,
                        message=f"Package '{pip_name}' is large/complex. Install manually.",
                    ))
                    continue
                if pip_count >= self.MAX_PIP_INSTALLS:
                    repair_report.results.append(RepairResult(
                        action=action,
                        status=RepairStatus.SKIPPED,
                        message="Max pip installs reached for this run.",
                    ))
                    continue
                pip_count += 1

            result = await self._execute_repair(action)
            repair_report.results.append(result)

        repair_report.finished_at = datetime.now()
        return repair_report

    async def repair_single(self, diag: DiagnosticResult) -> RepairResult:
        """Repair a single diagnostic issue."""
        action = RepairAction(
            action_id=diag.check_id,
            description=f"Fix: {diag.title}",
            category=diag.category,
            severity=diag.severity,
            hint=diag.repair_hint,
            details=diag.details,
        )
        return await self._execute_repair(action)

    # ------------------------------------------------------------------
    # Repair Dispatcher
    # ------------------------------------------------------------------

    async def _execute_repair(self, action: RepairAction) -> RepairResult:
        """Route a repair action to the appropriate handler."""
        start = time.monotonic()
        hint = action.hint

        try:
            # Match handler by prefix
            handler = None
            for prefix, fn in self._repair_handlers.items():
                if hint.startswith(prefix):
                    handler = fn
                    break

            if handler is None:
                return RepairResult(
                    action=action,
                    status=RepairStatus.NEEDS_HUMAN,
                    message=f"No auto-repair handler for hint: {hint}",
                    duration_ms=(time.monotonic() - start) * 1000,
                )

            result = await handler(action)
            result.duration_ms = (time.monotonic() - start) * 1000
            return result

        except Exception as e:
            return RepairResult(
                action=action,
                status=RepairStatus.FAILED,
                message=f"Repair exception: {e}",
                duration_ms=(time.monotonic() - start) * 1000,
            )

    # ------------------------------------------------------------------
    # Repair Handlers: Dependencies
    # ------------------------------------------------------------------

    async def _repair_pip_install(self, action: RepairAction) -> RepairResult:
        """Install a missing pip package."""
        pip_name = action.details.get("pip_name") or action.details.get("pip_line", "")
        if not pip_name:
            # Extract from hint: "pip install <pkg>"
            parts = action.hint.split()
            pip_name = parts[-1] if len(parts) >= 3 else ""

        if not pip_name:
            return RepairResult(action=action, status=RepairStatus.FAILED, message="No package name found.")

        logger.info(f"[AUTO-REPAIR] Installing: {pip_name}")
        try:
            result = subprocess.run(
                [sys.executable, "-m", "pip", "install", pip_name, "--quiet"],
                capture_output=True, text=True, timeout=120,
            )
            if result.returncode == 0:
                return RepairResult(action=action, status=RepairStatus.SUCCESS, message=f"Installed {pip_name}")
            else:
                return RepairResult(
                    action=action, status=RepairStatus.FAILED,
                    message=f"pip install failed: {result.stderr[:200]}",
                )
        except subprocess.TimeoutExpired:
            return RepairResult(action=action, status=RepairStatus.FAILED, message="pip install timed out (120s)")

    async def _repair_pip_reinstall(self, action: RepairAction) -> RepairResult:
        """Force-reinstall a broken package."""
        pip_name = action.details.get("pip_name", "")
        if not pip_name:
            return RepairResult(action=action, status=RepairStatus.FAILED, message="No package name.")

        logger.info(f"[AUTO-REPAIR] Reinstalling: {pip_name}")
        try:
            result = subprocess.run(
                [sys.executable, "-m", "pip", "install", "--force-reinstall", pip_name, "--quiet"],
                capture_output=True, text=True, timeout=180,
            )
            if result.returncode == 0:
                return RepairResult(action=action, status=RepairStatus.SUCCESS, message=f"Reinstalled {pip_name}")
            else:
                return RepairResult(action=action, status=RepairStatus.FAILED, message=result.stderr[:200])
        except subprocess.TimeoutExpired:
            return RepairResult(action=action, status=RepairStatus.FAILED, message="Reinstall timed out")

    # ------------------------------------------------------------------
    # Repair Handlers: Configuration
    # ------------------------------------------------------------------

    async def _repair_generate_config(self, action: RepairAction) -> RepairResult:
        """Generate a default config.yaml."""
        config_dir = self.project_root / "config"
        config_dir.mkdir(parents=True, exist_ok=True)
        config_path = config_dir / "config.yaml"

        # Backup existing if present
        if config_path.exists():
            backup = config_path.with_suffix(f".yaml.bak.{int(time.time())}")
            shutil.copy2(config_path, backup)
            logger.info(f"[AUTO-REPAIR] Backed up config to {backup.name}")

        config_path.write_text(DEFAULT_CONFIG_YAML, encoding="utf-8")
        return RepairResult(action=action, status=RepairStatus.SUCCESS, message="Generated default config.yaml")

    async def _repair_add_config_key(self, action: RepairAction) -> RepairResult:
        """Add a missing key to config.yaml with a default value."""
        dotted_key = action.hint.split(":", 1)[1] if ":" in action.hint else action.details.get("key", "")
        if not dotted_key:
            return RepairResult(action=action, status=RepairStatus.FAILED, message="No key specified.")

        default_val = DEFAULT_CONFIG_DEFAULTS.get(dotted_key, "")
        return await self._set_config_value(action, dotted_key, default_val)

    async def _repair_set_config_default(self, action: RepairAction) -> RepairResult:
        """Set a config key to its default value."""
        dotted_key = action.hint.split(":", 1)[1] if ":" in action.hint else action.details.get("key", "")
        default_val = DEFAULT_CONFIG_DEFAULTS.get(dotted_key, "")
        return await self._set_config_value(action, dotted_key, default_val)

    async def _repair_set_config(self, action: RepairAction) -> RepairResult:
        """Set a specific config value from hint like 'set_config:trading.mode=paper'."""
        if ":" not in action.hint:
            return RepairResult(action=action, status=RepairStatus.FAILED, message="Invalid hint format.")
        kv = action.hint.split(":", 1)[1]
        if "=" not in kv:
            return RepairResult(action=action, status=RepairStatus.FAILED, message="Invalid key=value format.")
        key, val = kv.split("=", 1)
        # Try to parse numeric values
        try:
            val = float(val) if "." in val else int(val)
        except (ValueError, TypeError):
            pass
        return await self._set_config_value(action, key, val)

    async def _set_config_value(self, action: RepairAction, dotted_key: str, value: Any) -> RepairResult:
        """Helper to set a nested key in config.yaml."""
        config_path = self.project_root / "config" / "config.yaml"
        if not config_path.exists():
            await self._repair_generate_config(action)

        try:
            import yaml
            with open(config_path, "r", encoding="utf-8") as f:
                cfg = yaml.safe_load(f) or {}

            parts = dotted_key.split(".")
            d = cfg
            for part in parts[:-1]:
                if part not in d or not isinstance(d[part], dict):
                    d[part] = {}
                d = d[part]
            d[parts[-1]] = value

            with open(config_path, "w", encoding="utf-8") as f:
                yaml.dump(cfg, f, default_flow_style=False, sort_keys=False)

            return RepairResult(
                action=action, status=RepairStatus.SUCCESS,
                message=f"Set {dotted_key}={value}",
            )
        except Exception as e:
            return RepairResult(action=action, status=RepairStatus.FAILED, message=str(e))

    async def _repair_find_mt5_path(self, action: RepairAction) -> RepairResult:
        """Search for MT5 terminal executable on the system."""
        search_paths = [
            Path("C:/Program Files/MetaTrader 5/terminal64.exe"),
            Path("C:/Program Files (x86)/MetaTrader 5/terminal64.exe"),
            Path(os.path.expanduser("~/AppData/Roaming/MetaQuotes/Terminal")),
        ]
        for p in search_paths:
            if p.exists() and p.is_file():
                return await self._set_config_value(action, "mt5.path", str(p))

        # Search common locations
        for drive in ["C:", "D:", "E:"]:
            mt5_glob = Path(drive + "/").glob("**/terminal64.exe")
            try:
                found = next(mt5_glob, None)
                if found:
                    return await self._set_config_value(action, "mt5.path", str(found))
            except (PermissionError, OSError):
                continue

        return RepairResult(
            action=action, status=RepairStatus.NEEDS_HUMAN,
            message="Could not find MT5 terminal. Install MetaTrader 5 and set mt5.path in config.",
        )

    # ------------------------------------------------------------------
    # Repair Handlers: API Keys
    # ------------------------------------------------------------------

    async def _repair_create_env_template(self, action: RepairAction) -> RepairResult:
        """Create .env file with template for the missing key."""
        return await self._repair_create_env_file(action)

    async def _repair_create_env_file(self, action: RepairAction) -> RepairResult:
        """Create .env template file."""
        env_path = self.project_root / ".env"
        if env_path.exists():
            return RepairResult(
                action=action, status=RepairStatus.SUCCESS,
                message=".env already exists. Add missing keys manually.",
            )
        env_path.write_text(ENV_TEMPLATE, encoding="utf-8")
        logger.info("[AUTO-REPAIR] Created .env template")
        return RepairResult(
            action=action, status=RepairStatus.SUCCESS,
            message="Created .env template. Fill in your API keys.",
        )

    async def _repair_prompt_api_key(self, action: RepairAction) -> RepairResult:
        """Cannot auto-fill API keys - mark as needs human."""
        env_var = action.hint.split(":", 1)[1] if ":" in action.hint else ""
        return RepairResult(
            action=action, status=RepairStatus.NEEDS_HUMAN,
            message=f"Set {env_var} in .env file with your actual API key.",
        )

    # ------------------------------------------------------------------
    # Repair Handlers: Data
    # ------------------------------------------------------------------

    async def _repair_create_database(self, action: RepairAction) -> RepairResult:
        """Create an empty SQLite database."""
        db_path = Path(action.details.get("path", str(self.project_root / "data" / "trading_bot.db")))
        db_path.parent.mkdir(parents=True, exist_ok=True)
        try:
            conn = sqlite3.connect(str(db_path))
            conn.execute("""CREATE TABLE IF NOT EXISTS trades (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                symbol TEXT, direction TEXT, size REAL, price REAL,
                timestamp TEXT, pnl REAL, status TEXT
            )""")
            conn.execute("""CREATE TABLE IF NOT EXISTS diagnostics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                run_time TEXT, health_score REAL, issues INTEGER,
                report_json TEXT
            )""")
            conn.execute("""CREATE TABLE IF NOT EXISTS repairs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                run_time TEXT, action_id TEXT, status TEXT, message TEXT
            )""")
            conn.commit()
            conn.close()
            return RepairResult(action=action, status=RepairStatus.SUCCESS, message=f"Created database at {db_path}")
        except Exception as e:
            return RepairResult(action=action, status=RepairStatus.FAILED, message=str(e))

    async def _repair_recreate_database(self, action: RepairAction) -> RepairResult:
        """Backup corrupted DB and create fresh one."""
        db_path = Path(action.details.get("path", str(self.project_root / "data" / "trading_bot.db")))
        if db_path.exists():
            backup = db_path.with_suffix(f".db.corrupt.{int(time.time())}")
            shutil.move(str(db_path), str(backup))
            logger.info(f"[AUTO-REPAIR] Moved corrupt DB to {backup.name}")
        return await self._repair_create_database(action)

    async def _repair_archive_stale_data(self, action: RepairAction) -> RepairResult:
        """Move stale CSV files to an archive directory."""
        data_dir = self.project_root / "data"
        archive_dir = data_dir / "archive"
        archive_dir.mkdir(exist_ok=True)
        moved = 0
        stale_files = action.details.get("stale_files", [])
        for fname in stale_files:
            src = data_dir / fname
            if src.exists():
                shutil.move(str(src), str(archive_dir / fname))
                moved += 1
        return RepairResult(
            action=action, status=RepairStatus.SUCCESS,
            message=f"Archived {moved} stale files to data/archive/",
        )

    async def _repair_rotate_logs(self, action: RepairAction) -> RepairResult:
        """Compress and rotate old log files."""
        logs_dir = self.project_root / "logs"
        if not logs_dir.exists():
            return RepairResult(action=action, status=RepairStatus.SKIPPED, message="No logs directory.")

        import gzip
        rotated = 0
        for log_file in sorted(logs_dir.glob("*.log")):
            if log_file.stat().st_size > 5 * 1024 * 1024:  # >5MB
                gz_path = log_file.with_suffix(f".log.{int(time.time())}.gz")
                try:
                    with open(log_file, "rb") as f_in:
                        with gzip.open(gz_path, "wb") as f_out:
                            shutil.copyfileobj(f_in, f_out)
                    # Truncate original
                    log_file.write_text("", encoding="utf-8")
                    rotated += 1
                except Exception:
                    continue

        return RepairResult(
            action=action, status=RepairStatus.SUCCESS,
            message=f"Rotated {rotated} log files.",
        )

    # ------------------------------------------------------------------
    # Repair Handlers: Connectivity
    # ------------------------------------------------------------------

    async def _repair_start_mt5(self, action: RepairAction) -> RepairResult:
        """Attempt to start MetaTrader 5 terminal."""
        try:
            import yaml
            config_path = self.project_root / "config" / "config.yaml"
            mt5_path = None
            if config_path.exists():
                with open(config_path, "r", encoding="utf-8") as f:
                    cfg = yaml.safe_load(f) or {}
                mt5_path = cfg.get("mt5", {}).get("path")

            if not mt5_path:
                mt5_path = "C:/Program Files/MetaTrader 5/terminal64.exe"

            if not Path(mt5_path).exists():
                return RepairResult(
                    action=action, status=RepairStatus.NEEDS_HUMAN,
                    message=f"MT5 not found at {mt5_path}. Install MetaTrader 5.",
                )

            subprocess.Popen([mt5_path], shell=False)
            # Wait a bit for it to start
            import asyncio
            await asyncio.sleep(5)

            return RepairResult(
                action=action, status=RepairStatus.SUCCESS,
                message=f"Started MT5 terminal: {mt5_path}",
            )
        except Exception as e:
            return RepairResult(action=action, status=RepairStatus.FAILED, message=str(e))

    # ------------------------------------------------------------------
    # Repair Handlers: Filesystem
    # ------------------------------------------------------------------

    async def _repair_create_directory(self, action: RepairAction) -> RepairResult:
        """Create a missing directory."""
        dir_name = action.hint.split(":", 1)[1] if ":" in action.hint else ""
        if not dir_name:
            return RepairResult(action=action, status=RepairStatus.FAILED, message="No directory name.")
        dir_path = self.project_root / dir_name
        dir_path.mkdir(parents=True, exist_ok=True)
        return RepairResult(action=action, status=RepairStatus.SUCCESS, message=f"Created {dir_name}/")

    async def _repair_create_file(self, action: RepairAction) -> RepairResult:
        """Create a missing required file."""
        file_rel = action.hint.split(":", 1)[1] if ":" in action.hint else ""
        if not file_rel:
            return RepairResult(action=action, status=RepairStatus.FAILED, message="No file path.")

        file_path = self.project_root / file_rel
        file_path.parent.mkdir(parents=True, exist_ok=True)

        if file_rel == "config/config.yaml":
            file_path.write_text(DEFAULT_CONFIG_YAML, encoding="utf-8")
        elif file_rel == "requirements.txt":
            file_path.write_text("# Auto-generated requirements\nnumpy\npandas\nloguru\nPyYAML\nMetaTrader5\nscikit-learn\nta\naiohttp\npsutil\n", encoding="utf-8")
        else:
            file_path.write_text("", encoding="utf-8")

        return RepairResult(action=action, status=RepairStatus.SUCCESS, message=f"Created {file_rel}")

    async def _repair_cleanup_disk(self, action: RepairAction) -> RepairResult:
        """Clean up temporary and cache files to free disk space."""
        cleaned = 0
        # Clean __pycache__
        for cache_dir in self.project_root.rglob("__pycache__"):
            try:
                shutil.rmtree(cache_dir)
                cleaned += 1
            except Exception:
                continue

        # Clean .pyc files
        for pyc in self.project_root.rglob("*.pyc"):
            try:
                pyc.unlink()
                cleaned += 1
            except Exception:
                continue

        return RepairResult(
            action=action, status=RepairStatus.SUCCESS,
            message=f"Cleaned {cleaned} cache items.",
        )

    # ------------------------------------------------------------------
    # Repair Handlers: Security
    # ------------------------------------------------------------------

    async def _repair_add_gitignore(self, action: RepairAction) -> RepairResult:
        """Add .env to existing .gitignore."""
        gitignore = self.project_root / ".gitignore"
        if gitignore.exists():
            content = gitignore.read_text(encoding="utf-8", errors="ignore")
            if ".env" not in content:
                with open(gitignore, "a", encoding="utf-8") as f:
                    f.write("\n# Secrets\n.env\n.env.*\n")
                return RepairResult(action=action, status=RepairStatus.SUCCESS, message="Added .env to .gitignore")
        return RepairResult(action=action, status=RepairStatus.SKIPPED, message=".env already in .gitignore")

    async def _repair_create_gitignore(self, action: RepairAction) -> RepairResult:
        """Create a .gitignore file."""
        gitignore = self.project_root / ".gitignore"
        if not gitignore.exists():
            gitignore.write_text(GITIGNORE_ENTRIES, encoding="utf-8")
            return RepairResult(action=action, status=RepairStatus.SUCCESS, message="Created .gitignore")
        return RepairResult(action=action, status=RepairStatus.SKIPPED, message=".gitignore already exists")

    async def _repair_move_secret_to_env(self, action: RepairAction) -> RepairResult:
        """Advise user to move secrets from config to .env."""
        return RepairResult(
            action=action, status=RepairStatus.NEEDS_HUMAN,
            message="Move secrets from config.yaml to .env file. Use os.environ.get() in code.",
        )
