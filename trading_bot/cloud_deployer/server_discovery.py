"""Server Discovery - Find free cloud servers and hosting platforms.

Scans the internet for free hosting options, tests their availability,
and ranks them by suitability for running a Python trading bot.
"""

from __future__ import annotations

import asyncio
import json
import os
import platform
import shutil
import subprocess
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional
from datetime import datetime

from loguru import logger


class ServerCapability(Enum):
    """What a server can do."""
    BACKGROUND_WORKER = "background_worker"      # Long-running process
    WEB_SERVICE = "web_service"                   # HTTP endpoints
    CRON_JOB = "cron_job"                         # Scheduled tasks
    DOCKER = "docker"                             # Container support
    PERSISTENT_STORAGE = "persistent_storage"     # Data survives restarts
    WEBSOCKET = "websocket"                       # Real-time connections
    GPU = "gpu"                                   # ML acceleration


@dataclass
class FreeServer:
    """Represents a discovered free hosting platform."""
    name: str
    url: str
    free_tier: str
    capabilities: List[ServerCapability]
    max_ram_mb: int = 512
    max_cpu_cores: float = 1.0
    max_storage_gb: float = 1.0
    max_runtime_hours: int = 750
    sleep_after_minutes: int = 0          # 0 = never sleeps
    requires_credit_card: bool = False
    requires_github: bool = True
    deploy_method: str = "git_push"       # git_push, cli, docker, api
    cli_tool: str = ""                    # e.g. "flyctl", "railway"
    score: float = 0.0                    # Computed suitability score
    available: bool = False               # Whether we can reach it
    latency_ms: float = 0.0
    notes: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "url": self.url,
            "free_tier": self.free_tier,
            "capabilities": [c.value for c in self.capabilities],
            "max_ram_mb": self.max_ram_mb,
            "max_runtime_hours": self.max_runtime_hours,
            "sleep_after_minutes": self.sleep_after_minutes,
            "requires_credit_card": self.requires_credit_card,
            "deploy_method": self.deploy_method,
            "score": round(self.score, 2),
            "available": self.available,
            "latency_ms": round(self.latency_ms, 1),
        }


# ============================================================================
# Pre-configured free hosting platforms (as of 2025)
# ============================================================================

FREE_PLATFORMS = [
    FreeServer(
        name="Railway",
        url="https://railway.app",
        free_tier="$5 credit/month, 500 execution hours",
        capabilities=[
            ServerCapability.BACKGROUND_WORKER,
            ServerCapability.WEB_SERVICE,
            ServerCapability.DOCKER,
            ServerCapability.PERSISTENT_STORAGE,
            ServerCapability.WEBSOCKET,
        ],
        max_ram_mb=512,
        max_cpu_cores=1.0,
        max_storage_gb=1.0,
        max_runtime_hours=500,
        sleep_after_minutes=0,
        requires_credit_card=False,
        requires_github=True,
        deploy_method="git_push",
        cli_tool="railway",
        notes="Best for always-on workers. $5 free credit covers ~500 hours of a small service.",
    ),
    FreeServer(
        name="Render",
        url="https://render.com",
        free_tier="750 hours/month for web services, background workers on paid only",
        capabilities=[
            ServerCapability.WEB_SERVICE,
            ServerCapability.CRON_JOB,
            ServerCapability.DOCKER,
            ServerCapability.PERSISTENT_STORAGE,
        ],
        max_ram_mb=512,
        max_cpu_cores=0.5,
        max_storage_gb=0.5,
        max_runtime_hours=750,
        sleep_after_minutes=15,
        requires_credit_card=False,
        requires_github=True,
        deploy_method="git_push",
        cli_tool="",
        notes="Free web services sleep after 15 min inactivity. Use cron-job.org to ping and keep alive.",
    ),
    FreeServer(
        name="Fly.io",
        url="https://fly.io",
        free_tier="3 shared-cpu-1x VMs, 256MB RAM each, 3GB storage",
        capabilities=[
            ServerCapability.BACKGROUND_WORKER,
            ServerCapability.WEB_SERVICE,
            ServerCapability.DOCKER,
            ServerCapability.PERSISTENT_STORAGE,
            ServerCapability.WEBSOCKET,
        ],
        max_ram_mb=256,
        max_cpu_cores=1.0,
        max_storage_gb=3.0,
        max_runtime_hours=2160,
        sleep_after_minutes=0,
        requires_credit_card=True,
        requires_github=False,
        deploy_method="cli",
        cli_tool="flyctl",
        notes="Requires credit card for verification but free tier is generous. Best for Docker deployments.",
    ),
    FreeServer(
        name="Koyeb",
        url="https://koyeb.com",
        free_tier="1 nano instance (256MB RAM, 0.1 vCPU), always-on",
        capabilities=[
            ServerCapability.BACKGROUND_WORKER,
            ServerCapability.WEB_SERVICE,
            ServerCapability.DOCKER,
            ServerCapability.WEBSOCKET,
        ],
        max_ram_mb=256,
        max_cpu_cores=0.1,
        max_storage_gb=0.5,
        max_runtime_hours=730,
        sleep_after_minutes=0,
        requires_credit_card=False,
        requires_github=True,
        deploy_method="git_push",
        cli_tool="koyeb",
        notes="Always-on free tier. Good for lightweight bots. No sleep/spin-down.",
    ),
    FreeServer(
        name="PythonAnywhere",
        url="https://www.pythonanywhere.com",
        free_tier="1 web app, 1 scheduled task/day, 512MB storage",
        capabilities=[
            ServerCapability.WEB_SERVICE,
            ServerCapability.CRON_JOB,
            ServerCapability.PERSISTENT_STORAGE,
        ],
        max_ram_mb=512,
        max_cpu_cores=0.5,
        max_storage_gb=0.5,
        max_runtime_hours=730,
        sleep_after_minutes=0,
        requires_credit_card=False,
        requires_github=False,
        deploy_method="api",
        cli_tool="",
        notes="Python-specific hosting. Free tier allows 1 scheduled task per day and always-on web app.",
    ),
    FreeServer(
        name="Hugging Face Spaces",
        url="https://huggingface.co/spaces",
        free_tier="Free CPU instances, 16GB RAM, persistent storage",
        capabilities=[
            ServerCapability.WEB_SERVICE,
            ServerCapability.PERSISTENT_STORAGE,
        ],
        max_ram_mb=16384,
        max_cpu_cores=2.0,
        max_storage_gb=50.0,
        max_runtime_hours=730,
        sleep_after_minutes=48 * 60,
        requires_credit_card=False,
        requires_github=False,
        deploy_method="git_push",
        cli_tool="",
        notes="Great for ML-heavy bots. Generous RAM. Sleeps after 48h inactivity on free tier.",
    ),
    FreeServer(
        name="Google Cloud Run (Free Tier)",
        url="https://cloud.google.com/run",
        free_tier="2M requests/month, 360k vCPU-seconds, 180k GiB-seconds",
        capabilities=[
            ServerCapability.WEB_SERVICE,
            ServerCapability.DOCKER,
            ServerCapability.WEBSOCKET,
        ],
        max_ram_mb=512,
        max_cpu_cores=1.0,
        max_storage_gb=0.0,
        max_runtime_hours=100,
        sleep_after_minutes=0,
        requires_credit_card=True,
        requires_github=False,
        deploy_method="cli",
        cli_tool="gcloud",
        notes="Serverless - scales to zero. Best for API/webhook-triggered trading, not always-on.",
    ),
    FreeServer(
        name="Oracle Cloud Free Tier",
        url="https://cloud.oracle.com/free",
        free_tier="2 AMD VMs (1GB RAM each) or 4 ARM VMs (24GB total), always free",
        capabilities=[
            ServerCapability.BACKGROUND_WORKER,
            ServerCapability.WEB_SERVICE,
            ServerCapability.DOCKER,
            ServerCapability.PERSISTENT_STORAGE,
            ServerCapability.WEBSOCKET,
        ],
        max_ram_mb=1024,
        max_cpu_cores=1.0,
        max_storage_gb=200.0,
        max_runtime_hours=8760,
        sleep_after_minutes=0,
        requires_credit_card=True,
        requires_github=False,
        deploy_method="cli",
        cli_tool="oci",
        notes="BEST free tier - full VMs that never expire. Requires credit card for verification only.",
    ),
]


class ServerDiscovery:
    """Discovers and ranks free cloud servers for hosting the trading bot."""

    def __init__(self):
        self.platforms: List[FreeServer] = [
            FreeServer(**{k: v for k, v in p.__dict__.items()})
            for p in FREE_PLATFORMS
        ]
        self._discovery_time: Optional[datetime] = None

    async def discover_all(self) -> List[FreeServer]:
        """Scan all known platforms, test connectivity, and rank them."""
        logger.info("Discovering free cloud hosting platforms...")

        tasks = [self._test_platform(p) for p in self.platforms]
        await asyncio.gather(*tasks, return_exceptions=True)

        # Score and rank
        for p in self.platforms:
            p.score = self._compute_score(p)

        self.platforms.sort(key=lambda p: p.score, reverse=True)
        self._discovery_time = datetime.now()

        available = [p for p in self.platforms if p.available]
        logger.info("Discovery complete: {}/{} platforms reachable", len(available), len(self.platforms))
        return self.platforms

    async def _test_platform(self, platform: FreeServer) -> None:
        """Test if a platform is reachable."""
        import aiohttp

        try:
            start = time.monotonic()
            async with aiohttp.ClientSession() as session:
                async with session.get(platform.url, timeout=aiohttp.ClientTimeout(total=10)) as resp:
                    platform.available = resp.status < 500
                    platform.latency_ms = (time.monotonic() - start) * 1000
        except Exception as e:
            platform.available = False
            platform.latency_ms = 99999
            logger.debug("Platform {} unreachable: {}", platform.name, e)

    def _compute_score(self, p: FreeServer) -> float:
        """Score a platform for trading bot suitability (0-100)."""
        if not p.available:
            return 0.0

        score = 0.0

        # Background worker support is critical for a trading bot
        if ServerCapability.BACKGROUND_WORKER in p.capabilities:
            score += 30
        elif ServerCapability.WEB_SERVICE in p.capabilities:
            score += 15

        # Always-on is important (no sleep)
        if p.sleep_after_minutes == 0:
            score += 20
        elif p.sleep_after_minutes > 60:
            score += 10

        # RAM (trading bot needs ~200-500MB)
        if p.max_ram_mb >= 512:
            score += 15
        elif p.max_ram_mb >= 256:
            score += 8

        # Runtime hours (need 730 for full month)
        if p.max_runtime_hours >= 730:
            score += 15
        elif p.max_runtime_hours >= 500:
            score += 10
        elif p.max_runtime_hours >= 100:
            score += 5

        # No credit card required is a plus
        if not p.requires_credit_card:
            score += 10

        # Docker support
        if ServerCapability.DOCKER in p.capabilities:
            score += 5

        # Persistent storage
        if ServerCapability.PERSISTENT_STORAGE in p.capabilities:
            score += 5

        # Latency penalty
        if p.latency_ms > 5000:
            score -= 10
        elif p.latency_ms > 2000:
            score -= 5

        return max(0, min(100, score))

    def get_best_platform(self) -> Optional[FreeServer]:
        """Return the highest-scored available platform."""
        available = [p for p in self.platforms if p.available and p.score > 0]
        return available[0] if available else None

    def get_no_credit_card_platforms(self) -> List[FreeServer]:
        """Return platforms that don't require a credit card."""
        return [p for p in self.platforms if p.available and not p.requires_credit_card]

    def check_local_tools(self) -> Dict[str, bool]:
        """Check which CLI tools are installed locally."""
        tools = {
            "git": False,
            "docker": False,
            "python": False,
            "flyctl": False,
            "railway": False,
            "gcloud": False,
            "oci": False,
            "koyeb": False,
        }
        for tool in tools:
            tools[tool] = shutil.which(tool) is not None
        return tools

    def get_report(self) -> str:
        """Generate a human-readable discovery report."""
        lines = [
            "=" * 70,
            "FREE CLOUD HOSTING DISCOVERY REPORT",
            f"Generated: {self._discovery_time or 'Not yet run'}",
            f"System: {platform.system()} {platform.release()}",
            "=" * 70,
            "",
        ]

        # Local tools
        tools = self.check_local_tools()
        lines.append("LOCAL TOOLS:")
        for tool, installed in tools.items():
            status = "INSTALLED" if installed else "NOT FOUND"
            lines.append(f"  {tool:12s} : {status}")
        lines.append("")

        # Platforms ranked by score
        lines.append("PLATFORMS (ranked by suitability):")
        lines.append("-" * 70)
        for i, p in enumerate(self.platforms, 1):
            status = "ONLINE" if p.available else "OFFLINE"
            cc = " (credit card required)" if p.requires_credit_card else ""
            lines.append(f"  #{i} {p.name} - Score: {p.score:.0f}/100 [{status}]{cc}")
            lines.append(f"     Free tier: {p.free_tier}")
            lines.append(f"     RAM: {p.max_ram_mb}MB | Runtime: {p.max_runtime_hours}h/mo | Sleep: {'never' if p.sleep_after_minutes == 0 else f'{p.sleep_after_minutes}min'}")
            lines.append(f"     Deploy: {p.deploy_method} | Latency: {p.latency_ms:.0f}ms")
            if p.notes:
                lines.append(f"     Note: {p.notes}")
            lines.append("")

        # Recommendation
        best = self.get_best_platform()
        if best:
            lines.append("=" * 70)
            lines.append(f"RECOMMENDATION: Deploy to {best.name} ({best.url})")
            lines.append(f"  Score: {best.score:.0f}/100")
            lines.append(f"  Free tier: {best.free_tier}")
            lines.append(f"  Deploy method: {best.deploy_method}")
            if best.cli_tool:
                lines.append(f"  CLI tool: {best.cli_tool}")
            lines.append("=" * 70)
        else:
            lines.append("No suitable free platforms found. Run locally instead.")

        return "\n".join(lines)

    def save_report(self, path: str = "cloud_discovery_report.txt") -> str:
        """Save discovery report to file."""
        report = self.get_report()
        with open(path, "w", encoding="utf-8") as f:
            f.write(report)
        logger.info("Discovery report saved to {}", path)
        return path


async def quick_discover() -> ServerDiscovery:
    """Quick helper to run discovery and return results."""
    discovery = ServerDiscovery()
    await discovery.discover_all()
    return discovery
