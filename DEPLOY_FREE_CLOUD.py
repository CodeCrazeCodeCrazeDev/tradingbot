"""
One-Click Free Cloud Deployment for AlphaAlgo Trading Bot.

Usage:
    python DEPLOY_FREE_CLOUD.py                    # Auto-discover best platform
    python DEPLOY_FREE_CLOUD.py --discover         # Scan platforms only
    python DEPLOY_FREE_CLOUD.py --platform railway  # Deploy to specific platform
    python DEPLOY_FREE_CLOUD.py --instructions      # Show all instructions
    python DEPLOY_FREE_CLOUD.py --local             # Run locally as background process
"""

from __future__ import annotations

import asyncio
import sys
import os

# Ensure project root is on path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


async def run():
    from trading_bot.cloud_deployer.server_discovery import ServerDiscovery
    from trading_bot.cloud_deployer.auto_deployer import CloudAutoDeployer, CloudPlatform

    print("=" * 70)
    print("  ALPHAALGO TRADING BOT - FREE CLOUD DEPLOYMENT")
    print("=" * 70)
    print()

    # Parse simple args
    args = sys.argv[1:]

    if "--help" in args or "-h" in args:
        print(__doc__)
        return

    if "--instructions" in args:
        deployer = CloudAutoDeployer()
        for platform in [CloudPlatform.RAILWAY, CloudPlatform.RENDER,
                         CloudPlatform.FLY_IO, CloudPlatform.KOYEB]:
            deployer.print_deploy_instructions(platform)
        return

    # Step 1: Always discover first
    print("[1/3] Discovering free cloud platforms...")
    print()
    discovery = ServerDiscovery()
    await discovery.discover_all()
    print(discovery.get_report())
    discovery.save_report()

    if "--discover" in args:
        print("\nDiscovery complete. Run without --discover to deploy.")
        return

    # Step 2: Deploy
    deployer = CloudAutoDeployer()

    if "--local" in args:
        print("\n[2/3] Deploying locally as background process...")
        result = await deployer.deploy_to(CloudPlatform.LOCAL)
    elif "--platform" in args:
        idx = args.index("--platform")
        if idx + 1 < len(args):
            platform_name = args[idx + 1]
            platform_map = {
                "railway": CloudPlatform.RAILWAY,
                "render": CloudPlatform.RENDER,
                "fly": CloudPlatform.FLY_IO,
                "fly.io": CloudPlatform.FLY_IO,
                "koyeb": CloudPlatform.KOYEB,
                "pythonanywhere": CloudPlatform.PYTHONANYWHERE,
                "huggingface": CloudPlatform.HUGGINGFACE,
                "local": CloudPlatform.LOCAL,
            }
            target = platform_map.get(platform_name.lower())
            if not target:
                print(f"Unknown platform: {platform_name}")
                print(f"Available: {', '.join(platform_map.keys())}")
                return
            print(f"\n[2/3] Deploying to {platform_name}...")
            result = await deployer.deploy_to(target)
        else:
            print("Error: --platform requires a platform name")
            return
    else:
        print("\n[2/3] Auto-selecting best platform and deploying...")
        result = await deployer.auto_deploy()

    # Step 3: Report
    print()
    print("=" * 70)
    print(f"  DEPLOYMENT RESULT: {result.status.value.upper()}")
    print(f"  Platform: {result.platform.value}")
    if result.url:
        print(f"  URL: {result.url}")
    if result.deploy_time > 0:
        print(f"  Time: {result.deploy_time:.1f}s")
    if result.error:
        print(f"  Error: {result.error}")
    print("=" * 70)

    if result.logs:
        print("\nDeployment Log:")
        for line in result.logs:
            print(f"  {line}")

    # Show next steps
    print()
    print("NEXT STEPS:")
    print("-" * 40)

    best = discovery.get_best_platform()
    if best:
        print(f"  Best free platform: {best.name} (score: {best.score:.0f}/100)")
        print(f"  URL: {best.url}")
        print(f"  Free tier: {best.free_tier}")
        print()

    print("  Quick deploy commands:")
    print("    Railway:  npm i -g @railway/cli && railway login && railway up")
    print("    Fly.io:   flyctl auth login && flyctl launch && flyctl deploy")
    print("    Render:   Push to GitHub -> render.com -> New -> Blueprint")
    print("    Koyeb:    Push to GitHub -> koyeb.com -> New Service")
    print("    Local:    python DEPLOY_FREE_CLOUD.py --local")
    print()
    print("  For detailed instructions:")
    print("    python DEPLOY_FREE_CLOUD.py --instructions")


if __name__ == "__main__":
    asyncio.run(run())
