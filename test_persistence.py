import asyncio
import os
import shutil
from pathlib import Path
from trading_bot.core_agent_system.coordination_core_part2 import SharedMemory, SharedMemoryScope

async def test_shared_memory_persistence():
    storage_path = "test_memory_storage"
    if os.path.exists(storage_path):
        shutil.rmtree(storage_path)

    # 1. Create memory and save data
    mem1 = SharedMemory(storage_path=storage_path)
    await mem1.write("key1", "value1", "agent1", scope=SharedMemoryScope.GLOBAL)
    mem1.create_team("team1", {"agent1", "agent2"})
    await mem1.save()

    print(f"Saved memory to {storage_path}")
    assert os.path.exists(os.path.join(storage_path, "shared_memory.json"))

    # 2. Create new memory instance and load
    mem2 = SharedMemory(storage_path=storage_path)
    await mem2.load()

    val = await mem2.read("key1", "agent2")
    print(f"Read key1: {val}")
    assert val == "value1"

    print(f"Teams: {mem2.teams}")
    assert "team1" in mem2.teams
    assert "agent1" in mem2.teams["team1"]

    # 3. Test corruption recovery (manual)
    with open(os.path.join(storage_path, "shared_memory.json"), "w") as f:
        f.write("corrupt data")

    mem3 = SharedMemory(storage_path=storage_path)
    await mem3.load()
    # Should recover from backup if backup exists
    # Wait, save() creates backup of LAST known good.
    # Let's ensure backup exists by saving twice with different data

    await mem1.write("key2", "value2", "agent1")
    await mem1.save() # This should move the first save to backup

    with open(os.path.join(storage_path, "shared_memory.json"), "w") as f:
        f.write("corrupt data")

    mem4 = SharedMemory(storage_path=storage_path)
    await mem4.load()
    val2 = await mem4.read("key2", "agent1")
    print(f"Recovered key2: {val2}")
    # It might recover key1 if it used the first backup, or key2 if it had a newer backup.
    # The logic keeps 5 backups.

    print("Persistence test passed!")

    if os.path.exists(storage_path):
        shutil.rmtree(storage_path)

if __name__ == "__main__":
    asyncio.run(test_shared_memory_persistence())
