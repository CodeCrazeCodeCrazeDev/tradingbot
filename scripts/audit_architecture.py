import asyncio
import os
import sys
from pathlib import Path
from datetime import datetime

# Setup path
sys.path.insert(0, os.getcwd())

from trading_bot.core.service_registry import get_service_registry
from trading_bot.core.event_bus import get_event_bus
from trading_bot.core.service_factory import create_service_factory

async def run_audit():
    print("=== AlphaAlgo Architecture Audit (Phase 3) ===")

    registry = get_service_registry()
    event_bus = get_event_bus()

    # Check for legacy and mtash in factory definitions rather than live registry
    # to avoid starting the whole bot.
    from trading_bot.core.service_factory import TIER1_SERVICES, TIER2_SERVICES, TIER3_SERVICES, TIER4_SERVICES, TIER5_SERVICES

    all_defs = TIER1_SERVICES + TIER2_SERVICES + TIER3_SERVICES + TIER4_SERVICES + TIER5_SERVICES

    mtash_def = next((d for d in all_defs if d.name == 'mtash'), None)
    legacy_names = ['agents', 'agents2', 'ai', 'ai_service', 'autonomous', 'superintelligence']
    active_legacy_defs = [d for d in all_defs if d.name in legacy_names and d.enabled]

    print(f"[Authority] MTASH Service Defined: {mtash_def is not None}")
    print(f"[Legacy] Active Redundant Definitions: {[d.name for d in active_legacy_defs]}")

    # Output Report
    with open("ARCHITECTURE_HEALTH_REPORT.md", "w") as f:
        f.write("# AlphaAlgo Architecture Health Report\n")
        f.write(f"Audit Run: {datetime.now().isoformat()}\n\n")
        f.write("## 1. Orchestration Authority\n")
        f.write(f"- MTASH Hub: {'✅ Defined' if mtash_def else '❌ MISSING'}\n")
        f.write("- Redundant Orchestrators Enabled: " + (", ".join([d.name for d in active_legacy_defs]) if active_legacy_defs else "✅ None found") + "\n\n")

        f.write("## 2. Dependency Graph\n")
        try:
            from trading_bot.core_agent_system.integrated_system import IntegratedAgentSystem
            f.write("- IntegratedAgentSystem: ✅ Available\n")
        except ImportError:
            f.write("- IntegratedAgentSystem: ❌ ERROR: Not found\n")

        f.write("\n## 3. Findings\n")
        if active_legacy_defs:
            f.write("- **WARNING:** Some legacy services are still enabled in ServiceFactory. Ensure they are disabled to prevent logic competition.\n")
        else:
            f.write("- System architecture is correctly consolidated. Single source of truth (MTASH) is established.\n")

if __name__ == "__main__":
    asyncio.run(run_audit())
