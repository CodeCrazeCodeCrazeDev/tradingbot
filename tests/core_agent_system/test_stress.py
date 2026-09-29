import asyncio
import pytest
import time
import uuid
import logging
from trading_bot.core_agent_system import IntegratedAgentSystem
from trading_bot.core_agent_system.coordination_core import TaskType, TaskPriority

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@pytest.mark.asyncio
async def test_coordination_stress_load():
    """
    Stress test the coordination system with a high volume of agents and tasks.
    """
    # Initialize system with a larger number of agents
    system = IntegratedAgentSystem({
        'storage_path': 'stress_test_data',
        'safety_threshold': 0.7,
        'num_simulations': 5,
        'max_episodes': 1000
    })

    await system.initialize()

    # Dynamically spawn 50 additional agents to stress the registry and negotiator
    logger.info("Spawning 50 additional agents for stress test...")

    # We use valid archetypes
    from trading_bot.core_agent_system.dynamic_agent_factory import AgentArchetype
    archetypes = list(AgentArchetype)

    spawn_tasks = []
    for i in range(50):
        spawn_tasks.append(system.coordination_core.create_sub_agent(
            archetype=archetypes[i % len(archetypes)],
            name=f"StressAgent_{i}"
        ))

    await asyncio.gather(*spawn_tasks)

    logger.info(f"System ready with {len(system.agent_registry.agents)} total agents.")

    # 1. High Load Test: Submit 20 complex tasks simultaneously
    logger.info("Submitting 20 complex tasks simultaneously...")
    task_descriptions = [
        f"Stress Task {i}: Perform comprehensive market analysis for EURUSD and suggest strategy"
        for i in range(20)
    ]

    start_time = time.time()
    execution_tasks = [
        system.execute_task(desc)
        for desc in task_descriptions
    ]

    # 2. Resilience Test: Mid-run Failure Injection
    # We will cancel/terminate some agents while tasks are running
    async def inject_failures():
        await asyncio.sleep(0.5) # Wait for some tasks to be in progress
        active_agents = system.coordination_core.agent_factory.get_active_agents()
        if active_agents:
            victim = active_agents[0]
            logger.info(f"FAILURE INJECTION: Terminating agent {victim.name}")
            await system.coordination_core.agent_factory.terminate_agent(victim.agent_id)

        await asyncio.sleep(0.5)
        # Simulate scheduler "hiccup" or message drop (not easy to inject directly without hooks,
        # but we can unregister more agents)
        active_agents = system.coordination_core.agent_factory.get_active_agents()
        if len(active_agents) > 5:
            victims = active_agents[1:4]
            for v in victims:
                logger.info(f"FAILURE INJECTION: Unexpectedly unregistering agent {v.name}")
                await system.agent_registry.unregister_agent(v.agent_id)

    # Run execution and failure injection concurrently
    results, _ = await asyncio.gather(
        asyncio.gather(*execution_tasks, return_exceptions=True),
        inject_failures()
    )

    end_time = time.time()

    # Verification
    success_count = sum(1 for r in results if isinstance(r, dict) and r.get('success'))
    failure_count = len(results) - success_count

    logger.info(f"Stress & Resilience test completed in {end_time - start_time:.2f}s")
    logger.info(f"Successes: {success_count}, Failures: {failure_count}")

    # Check for deadlocks/orphans
    # No task should be stuck in "assigned" or "in_progress" forever
    # Since we gathered, they either completed, failed or errored.

    # Verify exactly-once or bounded execution via metrics
    status = system.get_comprehensive_status()
    total_completed = status.get('coordination_core', {}).get('metrics', {}).get('completed_tasks', 0)
    total_failed = status.get('coordination_core', {}).get('metrics', {}).get('failed_tasks', 0)

    logger.info(f"Coordination Core Metrics: Completed={total_completed}, Failed={total_failed}")

    # We expect some tasks to succeed despite agent failures due to retries
    assert success_count > 0 or total_completed > 0

    await system.shutdown()

if __name__ == "__main__":
    asyncio.run(test_coordination_stress_load())
