#!/usr/bin/env python3
"""Execution-boundary tests for Signal Counterintelligence hard gating."""

import asyncio
import importlib.util
import sys
from pathlib import Path


MODULE_PATH = Path(__file__).parent.parent / "trading_bot" / "services" / "execution_service.py"
SPEC = importlib.util.spec_from_file_location("execution_service_direct", MODULE_PATH)
execution_service = importlib.util.module_from_spec(SPEC)
sys.modules["execution_service_direct"] = execution_service
SPEC.loader.exec_module(execution_service)


def _approved_intelligence():
    return {
        "decision": "accept",
        "governance_decision": "accept",
        "audit_digest": "audit-digest",
        "source_lineage_hashes": ["lineage-hash"],
        "governance_decision_id": "governance-record",
        "execution_allowed": True,
    }


def test_execution_service_rejects_orders_without_approved_intelligence_metadata():
    service = execution_service.ExecutionService({"counterintelligence_mode": "hard_gate"})
    order = {
        "order_id": "order-no-intel",
        "symbol": "EURUSD",
        "side": "buy",
        "size": 1.0,
        "order_type": "market",
        "price": 1.1,
        "created_at": "2026-04-27T00:00:00",
        "status": "pending",
    }

    result = asyncio.run(service.submit_order(order))

    assert not result["success"]
    assert order["status"] == "rejected"
    assert "audit_digest" in order["reject_reason"]


def test_execution_service_allows_orders_with_approved_intelligence_metadata():
    service = execution_service.ExecutionService({"counterintelligence_mode": "hard_gate"})
    order = {
        "order_id": "order-with-intel",
        "symbol": "EURUSD",
        "side": "buy",
        "size": 1.0,
        "order_type": "market",
        "price": 1.1,
        "created_at": "2026-04-27T00:00:00",
        "status": "pending",
        "intelligence": _approved_intelligence(),
    }

    result = asyncio.run(service.submit_order(order))

    assert result["success"]
    assert order["status"] == "filled"
