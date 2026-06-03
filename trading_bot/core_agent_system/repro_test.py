import asyncio
import logging
import sys
import os

# Add the project root to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from trading_bot.core_agent_system.integrated_system import IntegratedAgentSystem

async def main():
    logging.basicConfig(level=logging.INFO)

    # Use a temporary storage path for testing
    config = {
        'storage_path': 'test_core_agent_data',
        'safety_threshold': 0.7,
        'games_per_iteration': 1,
        'num_simulations': 5,
        'search_depth': 2
    }

    system = IntegratedAgentSystem(config)

    try:
        print("Initializing system...")
        await system.initialize()
        print("System initialized.")

        print("Executing a test task...")
        result = await system.execute_task("Analyze market and suggest a trade for EURUSD")
        print(f"Task result: {result}")

    except Exception as e:
        print(f"Error occurred: {e}")
        import traceback
        traceback.print_exc()
    finally:
        print("Shutting down...")
        await system.shutdown()

if __name__ == "__main__":
    asyncio.run(main())
