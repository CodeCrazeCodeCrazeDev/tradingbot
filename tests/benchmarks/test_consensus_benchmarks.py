import asyncio
import time
import numpy as np
import logging
from typing import List, Dict, Any
from trading_bot.core_agent_system.coordination_core import AgentNegotiator, Task, TaskType, TaskPriority, NegotiationProtocol

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class MockAgent:
    def __init__(self, agent_id: str, success_rate: float, tasks_completed: int):
        self.agent_id = agent_id
        self.metrics = type('obj', (object,), {'success_rate': success_rate, 'tasks_completed': tasks_completed})
        self.capabilities = []

async def benchmark_consensus():
    negotiator = AgentNegotiator()

    # Setup test agents
    # Expert with high success and experience
    expert = MockAgent("expert", 0.95, 1000)
    # Novice with medium success and low experience
    novice = MockAgent("novice", 0.70, 10)
    # Contrarian with high success but outlier proposal
    contrarian = MockAgent("contrarian", 0.90, 500)

    agents = [expert, novice, contrarian]

    # 1. Test Scenario: Clear Consensus
    proposals_1 = [
        {'agent_id': 'expert', 'action': 'buy', 'confidence': 0.9},
        {'agent_id': 'novice', 'action': 'buy', 'confidence': 0.6},
        {'agent_id': 'contrarian', 'action': 'sell', 'confidence': 0.8}
    ]

    task = Task("t1", "Consensus Test", TaskType.ANALYSIS, TaskPriority.MEDIUM, "test")

    start = time.time()
    result_1 = await negotiator.resolve_consensus(task, proposals_1, agents)
    latency_1 = (time.time() - start) * 1000

    print(f"\nScenario 1: Weighted Majority vs Contrarian")
    print(f"Winner: {result_1.get('action')} (score: {result_1.get('consensus_score', 0):.2f})")
    print(f"Latency: {latency_1:.2f}ms")

    # 2. Test Scenario: Disagreement (Expert vs Expert)
    expert2 = MockAgent("expert2", 0.96, 1100)
    agents.append(expert2)

    proposals_2 = [
        {'agent_id': 'expert', 'action': 'buy', 'confidence': 0.9},
        {'agent_id': 'expert2', 'action': 'sell', 'confidence': 0.9}
    ]

    start = time.time()
    result_2 = await negotiator.resolve_consensus(task, proposals_2, agents)
    latency_2 = (time.time() - start) * 1000

    print(f"\nScenario 2: High-Stake Disagreement")
    print(f"Winner: {result_2.get('action')} (score: {result_2.get('consensus_score', 0):.2f})")
    print(f"Latency: {latency_2:.2f}ms")

    # Metrics collection
    print("\nBenchmark Results Summary:")
    print(f"Average Consensus Latency: {(latency_1 + latency_2)/2:.2f}ms")
    print(f"Expert influence ratio: {result_1.get('consensus_score', 0):.2f}")

    # Scientific Calibration:
    # A score > 0.5 implies a strong weighted majority.
    # A score ~ 0.5 in a 2-agent split implies correct uncertainty reflection.
    assert result_1.get('action') == 'buy' # Expert + Novice should outweigh Contrarian
    assert result_1.get('consensus_score', 0) > 0.5

if __name__ == "__main__":
    asyncio.run(benchmark_consensus())
