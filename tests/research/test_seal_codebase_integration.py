"""
Unit and integration tests for SEAL codebase-wide integrations.
Verifies that TWAPExecutor, MultiAgentDebateSystem, and HierarchicalMemorySystem
successfully execute their native SEAL self-adaptation update directives.
"""

import pytest
import numpy as np

from trading_bot.execution.algorithms import TWAPExecutor
from trading_bot.agents.multi_agent_debate import MultiAgentDebateSystem
from trading_bot.core.hms.memory import HierarchicalMemorySystem


def test_seal_twap_executor_adaptation():
    """Verifies that TWAPExecutor correctly adapts its interval parameter based on slippage reward."""
    executor = TWAPExecutor()
    assert executor.config["interval_minutes"] == 2

    # High slippage reward is low -> increase interval
    executor.seal_adapt_interval(reward_oos_slippage=0.1)
    assert executor.config["interval_minutes"] == 3

    # Low slippage reward is high -> decrease interval
    executor.seal_adapt_interval(reward_oos_slippage=0.9)
    assert executor.config["interval_minutes"] == 2


def test_seal_multi_agent_debate_adaptation():
    """Verifies that MultiAgentDebateSystem correctly adapts its consensus threshold based on utility reward."""
    debate_system = MultiAgentDebateSystem()
    assert debate_system.consensus_threshold == 0.7

    # Sub-optimal performance -> increase threshold
    debate_system.seal_adapt_consensus_threshold(downstream_utility_reward=1.1)
    assert round(debate_system.consensus_threshold, 2) == 0.75

    # Excellent performance -> decrease threshold
    debate_system.seal_adapt_consensus_threshold(downstream_utility_reward=2.5)
    assert round(debate_system.consensus_threshold, 2) == 0.73


def test_seal_hms_memory_window_adaptation(tmp_path):
    """Verifies that HierarchicalMemorySystem correctly adapts its memory window parameter based on latency reward."""
    hms = HierarchicalMemorySystem(base_path=str(tmp_path))
    assert hms.memory_window_size == 100

    # High latency/surprise -> decrease window size
    hms.seal_adapt_memory_window(retention_latency_reward=0.5)
    assert hms.memory_window_size == 90

    # Excellent retrieval -> increase window size
    hms.seal_adapt_memory_window(retention_latency_reward=1.8)
    assert hms.memory_window_size == 100
