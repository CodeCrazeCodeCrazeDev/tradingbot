"""Auto Deployer - Deploy the trading bot to free cloud platforms.

Handles the full deployment lifecycle:
1. Discover best free platform
2. Prepare deployment artifacts
3. Deploy via git push, CLI, or API
4. Monitor deployment health
5. Auto-migrate if platform goes down
"""

from __future__ import annotations

import asyncio
import json
import os
import shutil
import subprocess
import sys
import tempfile
import time
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional
from datetime import datetime

from loguru import logger


class CloudPlatform(Enum):
    """Supported cloud platforms."""
    RAILWAY = "railway"
    RENDER = "render"
    FLY_IO = "fly_io"
    KOYEB = "koyeb"
    PYTHONANYWHERE = "pythonanywhere"
    HUGGINGFACE = "huggingface"
    GOOGLE_CLOUD_RUN = "google_cloud_run"
    ORACLE_CLOUD = "oracle_cloud"
    LOCAL = "local"


class DeploymentStatus(Enum):
    """Deployment lifecycle states."""
    NOT_STARTED = "not_started"
    PREPARING = "preparing"
    DEPLOYING = "deploying"
    RUNNING = "running"
    SLEEPING = "sleeping"
    FAILED = "failed"
    MIGRATING = "migrating"


@dataclass
class DeploymentResult:
    """Result of a deployment attempt."""
    platform: CloudPlatform
    status: DeploymentStatus
    url: str = ""
    deploy_time: float = 0.0
    error: str = ""
    logs: List[str] = field(default_factory=list)
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())

    def to_dict(self) -> Dict[str, Any]:
        return {
            "platform": self.platform.value,
            "status": self.status.value,
            "url": self.url,
            "deploy_time": round(self.deploy_time, 2),
            "error": self.error,
            "timestamp": self.timestamp,
        }


class CloudAutoDeployer:
    """Automatically deploys the trading bot to free cloud platforms."""

    def __init__(self, project_root: Optional[str] = None):
        self.project_root = Path(project_root or os.getcwd())
        self.deployments: List[DeploymentResult] = []
        self._current_platform: Optional[CloudPlatform] = None
        self._health_check_interval = 60  # seconds

    # ------------------------------------------------------------------
    # Main deployment flow
    # ------------------------------------------------------------------

    async def auto_deploy(self, prefer_no_credit_card: bool = True) -> DeploymentResult:
        """Automatically find the best free platform and deploy.

        This is the main entry point. It will:
        1. Discover available platforms
        2. Pick the best one
        3. Deploy the bot
        4. Return the result
        """
        from trading_bot.cloud_deployer.server_discovery import ServerDiscovery

        logger.info("=" * 60)
        logger.info("AUTO-DEPLOY: Finding best free cloud platform...")
        logger.info("=" * 60)

        # Step 1: Discover platforms
        discovery = ServerDiscovery()
        await discovery.discover_all()

        # Step 2: Pick best platform
        if prefer_no_credit_card:
            candidates = discovery.get_no_credit_card_platforms()
        else:
            candidates = [p for p in discovery.platforms if p.available]

        if not candidates:
            logger.error("No suitable free platforms found!")
            return DeploymentResult(
                platform=CloudPlatform.LOCAL,
                status=DeploymentStatus.FAILED,
                error="No free cloud platforms available. Run locally instead.",
            )

        best = candidates[0]
        logger.info("Best platform: {} (score: {}/100)", best.name, best.score)

        # Step 3: Map to CloudPlatform enum
        platform_map = {
            "Railway": CloudPlatform.RAILWAY,
            "Render": CloudPlatform.RENDER,
            "Fly.io": CloudPlatform.FLY_IO,
            "Koyeb": CloudPlatform.KOYEB,
            "PythonAnywhere": CloudPlatform.PYTHONANYWHERE,
            "Hugging Face Spaces": CloudPlatform.HUGGINGFACE,
            "Google Cloud Run (Free Tier)": CloudPlatform.GOOGLE_CLOUD_RUN,
            "Oracle Cloud Free Tier": CloudPlatform.ORACLE_CLOUD,
        }
        target = platform_map.get(best.name, CloudPlatform.RAILWAY)

        # Step 4: Deploy
        result = await self.deploy_to(target)

        # Save report
        discovery.save_report(str(self.project_root / "cloud_discovery_report.txt"))
        self._save_deployment_state(result)

        return result

    async def deploy_to(self, platform: CloudPlatform) -> DeploymentResult:
        """Deploy to a specific platform."""
        logger.info("Deploying to {}...", platform.value)
        start = time.monotonic()

        deployers = {
            CloudPlatform.RAILWAY: self._deploy_railway,
            CloudPlatform.RENDER: self._deploy_render,
            CloudPlatform.FLY_IO: self._deploy_fly,
            CloudPlatform.KOYEB: self._deploy_koyeb,
            CloudPlatform.PYTHONANYWHERE: self._deploy_pythonanywhere,
            CloudPlatform.HUGGINGFACE: self._deploy_huggingface,
            CloudPlatform.LOCAL: self._deploy_local,
        }

        deployer = deployers.get(platform, self._deploy_generic)

        try:
            result = await deployer()
            result.deploy_time = time.monotonic() - start
            self._current_platform = platform
            self.deployments.append(result)
            logger.info("Deployment to {} completed in {:.1f}s - Status: {}",
                        platform.value, result.deploy_time, result.status.value)
            return result
        except Exception as e:
            result = DeploymentResult(
                platform=platform,
                status=DeploymentStatus.FAILED,
                error=str(e),
                deploy_time=time.monotonic() - start,
            )
            self.deployments.append(result)
            logger.error("Deployment to {} failed: {}", platform.value, e)
            return result

    # ------------------------------------------------------------------
    # Platform-specific deployers
    # ------------------------------------------------------------------

    async def _deploy_railway(self) -> DeploymentResult:
        """Deploy to Railway.app via CLI or git push."""
        result = DeploymentResult(platform=CloudPlatform.RAILWAY, status=DeploymentStatus.PREPARING)

        # Check if Railway CLI is installed
        if shutil.which("railway"):
            result.logs.append("Railway CLI found, deploying via CLI...")
            try:
                proc = subprocess.run(
                    ["railway", "up", "--detach"],
                    cwd=str(self.project_root),
                    capture_output=True, text=True, timeout=300,
                )
                if proc.returncode == 0:
                    result.status = DeploymentStatus.RUNNING
                    result.logs.append(proc.stdout)
                    # Try to extract URL
                    if "https://" in proc.stdout:
                        for word in proc.stdout.split():
                            if word.startswith("https://"):
                                result.url = word.strip()
                                break
                else:
                    result.status = DeploymentStatus.FAILED
                    result.error = proc.stderr
            except subprocess.TimeoutExpired:
                result.status = DeploymentStatus.FAILED
                result.error = "Railway deploy timed out after 300s"
        else:
            # Provide manual instructions
            result.status = DeploymentStatus.NOT_STARTED
            result.logs.append("Railway CLI not found. Install it:")
            result.logs.append("  npm install -g @railway/cli")
            result.logs.append("  railway login")
            result.logs.append("  railway init")
            result.logs.append("  railway up")
            result.logs.append("")
            result.logs.append("OR deploy via GitHub:")
            result.logs.append("  1. Push code to GitHub")
            result.logs.append("  2. Go to railway.app -> New Project -> Deploy from GitHub")
            result.logs.append("  3. Select your repo")
            result.logs.append("  4. Railway will auto-detect Dockerfile and deploy")
            self._ensure_railway_config()

        return result

    async def _deploy_render(self) -> DeploymentResult:
        """Deploy to Render.com via git push (render.yaml)."""
        result = DeploymentResult(platform=CloudPlatform.RENDER, status=DeploymentStatus.PREPARING)

        # Ensure render.yaml exists
        render_yaml = self.project_root / "render.yaml"
        if render_yaml.exists():
            result.logs.append("render.yaml found")
        else:
            result.logs.append("render.yaml not found - creating it")
            self._ensure_render_config()

        result.status = DeploymentStatus.NOT_STARTED
        result.logs.append("")
        result.logs.append("Deploy to Render.com:")
        result.logs.append("  1. Push code to GitHub (git push origin main)")
        result.logs.append("  2. Go to render.com -> New -> Blueprint")
        result.logs.append("  3. Connect your GitHub repo")
        result.logs.append("  4. Render reads render.yaml and deploys automatically")
        result.logs.append("")
        result.logs.append("IMPORTANT: Free tier web services sleep after 15 min inactivity.")
        result.logs.append("Use https://cron-job.org to ping your /health endpoint every 14 min.")

        return result

    async def _deploy_fly(self) -> DeploymentResult:
        """Deploy to Fly.io via flyctl CLI."""
        result = DeploymentResult(platform=CloudPlatform.FLY_IO, status=DeploymentStatus.PREPARING)

        if shutil.which("flyctl") or shutil.which("fly"):
            fly_cmd = "flyctl" if shutil.which("flyctl") else "fly"
            result.logs.append(f"{fly_cmd} CLI found, deploying...")

            # Ensure fly.toml exists
            self._ensure_fly_config()

            try:
                proc = subprocess.run(
                    [fly_cmd, "deploy", "--now"],
                    cwd=str(self.project_root),
                    capture_output=True, text=True, timeout=600,
                )
                if proc.returncode == 0:
                    result.status = DeploymentStatus.RUNNING
                    result.logs.append(proc.stdout)
                else:
                    result.status = DeploymentStatus.FAILED
                    result.error = proc.stderr
            except subprocess.TimeoutExpired:
                result.status = DeploymentStatus.FAILED
                result.error = "Fly.io deploy timed out after 600s"
        else:
            result.status = DeploymentStatus.NOT_STARTED
            result.logs.append("Fly.io CLI not found. Install it:")
            result.logs.append("  Windows: powershell -Command \"iwr https://fly.io/install.ps1 -useb | iex\"")
            result.logs.append("  Then: flyctl auth login")
            result.logs.append("  Then: flyctl launch  (from project root)")
            result.logs.append("  Then: flyctl deploy")
            self._ensure_fly_config()

        return result

    async def _deploy_koyeb(self) -> DeploymentResult:
        """Deploy to Koyeb via CLI or git push."""
        result = DeploymentResult(platform=CloudPlatform.KOYEB, status=DeploymentStatus.PREPARING)

        if shutil.which("koyeb"):
            result.logs.append("Koyeb CLI found")
            try:
                proc = subprocess.run(
                    ["koyeb", "app", "create", "alphaalgo-bot",
                     "--docker", ".",
                     "--instance-type", "free",
                     "--region", "was"],
                    cwd=str(self.project_root),
                    capture_output=True, text=True, timeout=300,
                )
                if proc.returncode == 0:
                    result.status = DeploymentStatus.RUNNING
                    result.logs.append(proc.stdout)
                else:
                    result.status = DeploymentStatus.FAILED
                    result.error = proc.stderr
            except subprocess.TimeoutExpired:
                result.status = DeploymentStatus.FAILED
                result.error = "Koyeb deploy timed out"
        else:
            result.status = DeploymentStatus.NOT_STARTED
            result.logs.append("Deploy to Koyeb:")
            result.logs.append("  1. Go to koyeb.com and create a free account")
            result.logs.append("  2. New Service -> GitHub -> Select your repo")
            result.logs.append("  3. Instance type: Free (nano)")
            result.logs.append("  4. Build: Dockerfile")
            result.logs.append("  5. Deploy")
            result.logs.append("")
            result.logs.append("Koyeb free tier is always-on (no sleep)!")

        return result

    async def _deploy_pythonanywhere(self) -> DeploymentResult:
        """Deploy to PythonAnywhere via API."""
        result = DeploymentResult(platform=CloudPlatform.PYTHONANYWHERE, status=DeploymentStatus.PREPARING)

        result.status = DeploymentStatus.NOT_STARTED
        result.logs.append("Deploy to PythonAnywhere:")
        result.logs.append("  1. Create free account at pythonanywhere.com")
        result.logs.append("  2. Open a Bash console")
        result.logs.append("  3. git clone <your-repo-url>")
        result.logs.append("  4. cd trading_bot && pip install -r requirements.txt")
        result.logs.append("  5. Set up a Scheduled Task (1 per day on free tier):")
        result.logs.append("     Command: cd /home/<username>/trading_bot && python main.py --mode paper")
        result.logs.append("")
        result.logs.append("NOTE: Free tier only allows 1 scheduled task per day.")
        result.logs.append("For always-on, upgrade to $5/month Hacker plan.")

        return result

    async def _deploy_huggingface(self) -> DeploymentResult:
        """Deploy to Hugging Face Spaces."""
        result = DeploymentResult(platform=CloudPlatform.HUGGINGFACE, status=DeploymentStatus.PREPARING)

        result.status = DeploymentStatus.NOT_STARTED
        result.logs.append("Deploy to Hugging Face Spaces:")
        result.logs.append("  1. Create account at huggingface.co")
        result.logs.append("  2. New Space -> Docker -> Blank template")
        result.logs.append("  3. Clone the space repo")
        result.logs.append("  4. Copy your trading bot files into it")
        result.logs.append("  5. Push to deploy")
        result.logs.append("")
        result.logs.append("Great for ML-heavy bots (16GB RAM free).")
        result.logs.append("Sleeps after 48h inactivity on free tier.")

        return result

    async def _deploy_local(self) -> DeploymentResult:
        """Run locally as a background process."""
        result = DeploymentResult(platform=CloudPlatform.LOCAL, status=DeploymentStatus.PREPARING)

        if sys.platform == "win32":
            # Windows: use pythonw or start /b
            result.logs.append("Starting bot as background process on Windows...")
            try:
                proc = subprocess.Popen(
                    [sys.executable, "main.py", "--mode", "paper", "--symbol", "EURUSD"],
                    cwd=str(self.project_root),
                    creationflags=subprocess.CREATE_NO_WINDOW if hasattr(subprocess, 'CREATE_NO_WINDOW') else 0,
                    stdout=open(self.project_root / "logs" / "bot_output.log", "a"),
                    stderr=subprocess.STDOUT,
                )
                result.status = DeploymentStatus.RUNNING
                result.logs.append(f"Bot started with PID: {proc.pid}")
                result.logs.append(f"Logs: {self.project_root / 'logs' / 'bot_output.log'}")
            except Exception as e:
                result.status = DeploymentStatus.FAILED
                result.error = str(e)
        else:
            # Linux/Mac: use nohup
            result.logs.append("Starting bot as background process...")
            try:
                proc = subprocess.Popen(
                    ["nohup", sys.executable, "main.py", "--mode", "paper", "--symbol", "EURUSD"],
                    cwd=str(self.project_root),
                    stdout=open(self.project_root / "logs" / "bot_output.log", "a"),
                    stderr=subprocess.STDOUT,
                    start_new_session=True,
                )
                result.status = DeploymentStatus.RUNNING
                result.logs.append(f"Bot started with PID: {proc.pid}")
            except Exception as e:
                result.status = DeploymentStatus.FAILED
                result.error = str(e)

        return result

    async def _deploy_generic(self) -> DeploymentResult:
        """Generic deployment instructions."""
        return DeploymentResult(
            platform=CloudPlatform.LOCAL,
            status=DeploymentStatus.NOT_STARTED,
            logs=["No specific deployer for this platform. Use Docker:"],
        )

    # ------------------------------------------------------------------
    # Config file generators
    # ------------------------------------------------------------------

    def _ensure_railway_config(self):
        """Ensure railway.json exists."""
        path = self.project_root / "railway.json"
        if not path.exists():
            config = {
                "$schema": "https://railway.app/railway.schema.json",
                "build": {"builder": "DOCKERFILE", "dockerfilePath": "Dockerfile"},
                "deploy": {
                    "startCommand": "python main.py --mode paper --symbol EURUSD --timeframe M15",
                    "healthcheckPath": "/health",
                    "restartPolicyType": "ON_FAILURE",
                    "restartPolicyMaxRetries": 5,
                },
            }
            with open(path, "w") as f:
                json.dump(config, f, indent=2)
            logger.info("Created railway.json")

    def _ensure_render_config(self):
        """Ensure render.yaml exists."""
        path = self.project_root / "render.yaml"
        if not path.exists():
            content = """services:
  - type: worker
    name: alphaalgo-trading-bot
    runtime: python
    plan: free
    buildCommand: pip install -r requirements.txt
    startCommand: python main.py --mode paper --symbol EURUSD
    envVars:
      - key: TRADING_BOT_MODE
        value: paper
      - key: PYTHONUNBUFFERED
        value: "1"
"""
            with open(path, "w") as f:
                f.write(content)
            logger.info("Created render.yaml")

    def _ensure_fly_config(self):
        """Ensure fly.toml exists."""
        path = self.project_root / "fly.toml"
        if not path.exists():
            content = """app = "alphaalgo-trading-bot"
primary_region = "iad"

[build]
  dockerfile = "Dockerfile"

[env]
  TRADING_BOT_MODE = "paper"
  PYTHONUNBUFFERED = "1"

[[vm]]
  cpu_kind = "shared"
  cpus = 1
  memory_mb = 256
"""
            with open(path, "w") as f:
                f.write(content)
            logger.info("Created fly.toml")

    # ------------------------------------------------------------------
    # Health monitoring
    # ------------------------------------------------------------------

    async def monitor_health(self, url: str, interval: int = 60) -> None:
        """Continuously monitor deployment health and auto-migrate if needed."""
        import aiohttp

        consecutive_failures = 0
        max_failures = 5

        logger.info("Health monitoring started for {}", url)

        while True:
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.get(f"{url}/health", timeout=aiohttp.ClientTimeout(total=10)) as resp:
                        if resp.status == 200:
                            consecutive_failures = 0
                        else:
                            consecutive_failures += 1
                            logger.warning("Health check failed ({}/{}): HTTP {}",
                                           consecutive_failures, max_failures, resp.status)
            except Exception as e:
                consecutive_failures += 1
                logger.warning("Health check failed ({}/{}): {}",
                               consecutive_failures, max_failures, e)

            if consecutive_failures >= max_failures:
                logger.error("Platform appears down! Attempting auto-migration...")
                await self._auto_migrate()
                consecutive_failures = 0

            await asyncio.sleep(interval)

    async def _auto_migrate(self) -> DeploymentResult:
        """Migrate to the next best platform if current one fails."""
        logger.info("Auto-migrating to next best platform...")
        return await self.auto_deploy()

    # ------------------------------------------------------------------
    # State persistence
    # ------------------------------------------------------------------

    def _save_deployment_state(self, result: DeploymentResult):
        """Save deployment state to disk."""
        state_file = self.project_root / "state" / "cloud_deployment.json"
        state_file.parent.mkdir(parents=True, exist_ok=True)

        state = {
            "current_deployment": result.to_dict(),
            "history": [d.to_dict() for d in self.deployments[-10:]],
            "updated": datetime.now().isoformat(),
        }

        with open(state_file, "w") as f:
            json.dump(state, f, indent=2)

    def get_deployment_status(self) -> Dict[str, Any]:
        """Get current deployment status."""
        state_file = self.project_root / "state" / "cloud_deployment.json"
        if state_file.exists():
            with open(state_file) as f:
                return json.load(f)
        return {"status": "not_deployed"}

    # ------------------------------------------------------------------
    # Quick deploy helpers
    # ------------------------------------------------------------------

    def print_deploy_instructions(self, platform: CloudPlatform = CloudPlatform.RAILWAY) -> str:
        """Print step-by-step deployment instructions for a platform."""
        instructions = {
            CloudPlatform.RAILWAY: """
╔══════════════════════════════════════════════════════════════╗
║           DEPLOY TO RAILWAY (FREE - $5 credit/mo)           ║
╠══════════════════════════════════════════════════════════════╣
║                                                              ║
║  Option A: GitHub (Easiest)                                  ║
║  ─────────────────────────                                   ║
║  1. Push your code to GitHub                                 ║
║  2. Go to railway.app -> New Project                         ║
║  3. Deploy from GitHub Repo                                  ║
║  4. Select your trading-bot repo                             ║
║  5. Railway auto-detects Dockerfile and deploys              ║
║  6. Set env vars: TRADING_BOT_MODE=paper                     ║
║                                                              ║
║  Option B: CLI                                               ║
║  ─────────────                                               ║
║  1. npm install -g @railway/cli                              ║
║  2. railway login                                            ║
║  3. railway init                                             ║
║  4. railway up                                               ║
║                                                              ║
║  Cost: $0 (within $5 free credit)                            ║
║  Always-on: YES                                              ║
║  Credit card: NOT required                                   ║
╚══════════════════════════════════════════════════════════════╝
""",
            CloudPlatform.RENDER: """
╔══════════════════════════════════════════════════════════════╗
║          DEPLOY TO RENDER (FREE - 750 hrs/month)            ║
╠══════════════════════════════════════════════════════════════╣
║                                                              ║
║  1. Push code to GitHub                                      ║
║  2. Go to render.com -> New -> Web Service                   ║
║  3. Connect your GitHub repo                                 ║
║  4. Settings:                                                ║
║     Build: pip install -r requirements.txt                   ║
║     Start: python main.py --mode paper --symbol EURUSD       ║
║  5. Deploy                                                   ║
║                                                              ║
║  KEEP-ALIVE TRICK (prevents 15-min sleep):                   ║
║  Go to cron-job.org and set up a job to ping                 ║
║  your-app.onrender.com/health every 14 minutes               ║
║                                                              ║
║  Cost: $0                                                    ║
║  Credit card: NOT required                                   ║
╚══════════════════════════════════════════════════════════════╝
""",
            CloudPlatform.FLY_IO: """
╔══════════════════════════════════════════════════════════════╗
║            DEPLOY TO FLY.IO (FREE - 3 VMs)                  ║
╠══════════════════════════════════════════════════════════════╣
║                                                              ║
║  1. Install flyctl:                                          ║
║     powershell -Command "iwr https://fly.io/install.ps1      ║
║       -useb | iex"                                           ║
║  2. flyctl auth signup  (or login)                           ║
║  3. cd <project-root>                                        ║
║  4. flyctl launch                                            ║
║  5. flyctl deploy                                            ║
║                                                              ║
║  Cost: $0 (free tier: 3 shared VMs, 256MB each)              ║
║  Always-on: YES                                              ║
║  Credit card: REQUIRED (for verification only)               ║
╚══════════════════════════════════════════════════════════════╝
""",
            CloudPlatform.KOYEB: """
╔══════════════════════════════════════════════════════════════╗
║          DEPLOY TO KOYEB (FREE - always-on nano)            ║
╠══════════════════════════════════════════════════════════════╣
║                                                              ║
║  1. Create account at koyeb.com                              ║
║  2. New Service -> GitHub                                    ║
║  3. Select your repo                                         ║
║  4. Instance: Free (nano - 256MB RAM)                        ║
║  5. Build: Dockerfile                                        ║
║  6. Deploy                                                   ║
║                                                              ║
║  Cost: $0                                                    ║
║  Always-on: YES (no sleep!)                                  ║
║  Credit card: NOT required                                   ║
╚══════════════════════════════════════════════════════════════╝
""",
        }

        text = instructions.get(platform, f"No instructions available for {platform.value}")
        print(text)
        return text


# ============================================================================
# Standalone entry point
# ============================================================================

async def main():
    """Run auto-deployment from command line."""
    import argparse

    parser = argparse.ArgumentParser(description="Deploy AlphaAlgo Trading Bot to free cloud")
    parser.add_argument("--platform", choices=[p.value for p in CloudPlatform],
                        help="Target platform (auto-selects best if not specified)")
    parser.add_argument("--discover-only", action="store_true",
                        help="Only discover platforms, don't deploy")
    parser.add_argument("--instructions", choices=[p.value for p in CloudPlatform],
                        help="Print deployment instructions for a platform")
    parser.add_argument("--local", action="store_true",
                        help="Deploy locally as background process")
    args = parser.parse_args()

    deployer = CloudAutoDeployer()

    if args.instructions:
        deployer.print_deploy_instructions(CloudPlatform(args.instructions))
        return

    if args.discover_only:
        from trading_bot.cloud_deployer.server_discovery import ServerDiscovery
        discovery = ServerDiscovery()
        await discovery.discover_all()
        print(discovery.get_report())
        discovery.save_report()
        return

    if args.local:
        result = await deployer.deploy_to(CloudPlatform.LOCAL)
    elif args.platform:
        result = await deployer.deploy_to(CloudPlatform(args.platform))
    else:
        result = await deployer.auto_deploy()

    print("\n" + "=" * 60)
    print(f"Deployment Result: {result.status.value}")
    print(f"Platform: {result.platform.value}")
    if result.url:
        print(f"URL: {result.url}")
    if result.error:
        print(f"Error: {result.error}")
    for log_line in result.logs:
        print(f"  {log_line}")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
