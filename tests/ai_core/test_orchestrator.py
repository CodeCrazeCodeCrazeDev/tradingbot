"""
Tests for AIOrchestrator in ai_core
"""

import pytest
import asyncio
from trading_bot.ai_core.orchestrator import AIOrchestrator

class TestAIOrchestrator:
    """Tests for AIOrchestrator"""

    def test_initialization(self):
        """Test AIOrchestrator initialization"""
        obj = AIOrchestrator()
        assert obj is not None
        assert obj.get_status()["status"] == "operational"
