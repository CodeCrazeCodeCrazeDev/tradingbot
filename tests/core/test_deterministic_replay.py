import pytest
import numpy as np
from trading_bot.core.governance.replay import ReplayManager, DeterministicReplayError

def simulate_strategy_decision(market_snapshot: dict) -> dict:
    """A sample strategy that utilizes numpy random state (which depends on the seed)."""
    val = market_snapshot.get("base_price", 100.0)
    noise = np.random.normal(0, 1.0)
    decision = "BUY" if noise > 0 else "HOLD"
    return {
        "price_with_noise": val + noise,
        "decision": decision
    }

def test_replay_manager_exact_reproduction():
    manager = ReplayManager()

    # 1. Capture original run under seed 100
    manager.enforce_determinism(100)
    market_snapshot = {"base_price": 50.0}
    original_outcome = simulate_strategy_decision(market_snapshot)

    snapshot = {
        "decision_id": "dec_001",
        "seed": 100,
        "market_snapshot": market_snapshot,
        "expected_outcome": original_outcome
    }

    # 2. Replay the decision
    success, replayed = manager.replay_decision(snapshot, simulate_strategy_decision)
    assert success is True
    assert replayed["decision"] == original_outcome["decision"]
    assert replayed["price_with_noise"] == original_outcome["price_with_noise"]

def test_replay_manager_detects_deviation():
    manager = ReplayManager()

    # Capture original run under seed 100
    manager.enforce_determinism(100)
    market_snapshot = {"base_price": 50.0}
    original_outcome = simulate_strategy_decision(market_snapshot)

    # Create snapshot with a mismatched expected outcome
    tampered_outcome = original_outcome.copy()
    tampered_outcome["decision"] = "SELL" if original_outcome["decision"] == "BUY" else "BUY"

    snapshot = {
        "decision_id": "dec_002",
        "seed": 100,
        "market_snapshot": market_snapshot,
        "expected_outcome": tampered_outcome
    }

    # Replay should raise DeterministicReplayError due to the outcome deviation!
    with pytest.raises(DeterministicReplayError) as exc_info:
        manager.replay_decision(snapshot, simulate_strategy_decision)

    assert "Replay Deviation" in str(exc_info.value)
