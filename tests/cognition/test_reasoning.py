"""Tests for Model Router and Hybrid Reasoning."""

import pytest
from trading_bot.cognition.reasoning import (
    TaskRequest,
    TaskResponse,
    TaskCategory,
    ModelRouter,
)


def test_model_router_deterministic_routing():
    router = ModelRouter()
    req = TaskRequest(
        task_id="task_001",
        category=TaskCategory.ARITHMETIC_DETERMINISTIC,
        payload={"balance": 50000.0, "risk_pct": 0.02, "stop_pips": 25.0, "pip_value": 10.0}
    )
    res = router.route_and_execute(req)

    assert res.success
    assert res.provider_used == "DeterministicEngine"
    assert res.cost_estimated == 0.0
    assert res.result["risk_amount"] == 1000.0
    assert res.result["position_size"] == 4.0


def test_model_router_ml_routing():
    router = ModelRouter()
    req = TaskRequest(
        task_id="task_002",
        category=TaskCategory.SPECIALIZED_ML_PREDICTION,
        payload={"features": {"rsi": 25.0}}
    )
    res = router.route_and_execute(req)

    assert res.success
    assert res.provider_used == "SpecializedMLModel"
    assert res.result["prob_up"] == 0.60


class MockLLMProvider:
    name = "MockOpenAI"
    def synthesize(self, payload):
        return {"synthesis": "LLM synthesized research hypothesis", "confidence": 0.92}


def test_model_router_llm_routing_with_provider():
    llm = MockLLMProvider()
    router = ModelRouter(llm_provider=llm)
    req = TaskRequest(
        task_id="task_003",
        category=TaskCategory.RESEARCH_SYNTHESIS,
        payload={"topic": "liquidity_sweep"}
    )
    res = router.route_and_execute(req)

    assert res.success
    assert res.provider_used == "MockOpenAI"
    assert res.result["synthesis"] == "LLM synthesized research hypothesis"
