import asyncio
import sys
import os

sys.path.insert(0, os.getcwd())

from tests.core_agent_system.test_unit import (
    test_agent_registry_lifecycle,
    test_tool_registry_validation,
    test_master_orchestrator_decision_fusion
)
from tests.core_agent_system.test_integration import test_integrated_system_flow

async def run_all():
    print("Running Unit Tests...")
    await test_agent_registry_lifecycle()
    await test_tool_registry_validation()
    await test_master_orchestrator_decision_fusion()
    print("Unit Tests Passed!\n")

    print("Running Integration Test...")
    await test_integrated_system_flow()
    print("Integration Test Passed!\n")

if __name__ == "__main__":
    asyncio.run(run_all())
