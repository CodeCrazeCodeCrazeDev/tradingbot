import pytest
import time
from trading_bot.core.csc.acpe import AdaptiveControlPolicyEngine, HarnessConfig

def test_acpe_default_fallback():
    """Verifies that ACPE returns a valid default configuration."""
    acpe = AdaptiveControlPolicyEngine()
    config = acpe.parameterize_pipeline({})

    assert isinstance(config, HarnessConfig)
    assert config.max_iterations == 3
    assert config.shield_strictness == "HIGH"

def test_acpe_high_volatility_retrieval():
    """Verifies that ACPE scales parameter bounds correctly during volatility spikes."""
    acpe = AdaptiveControlPolicyEngine()

    # Trigger high volatility policy
    obs = {"market": {"volatility": 0.5}}
    config = acpe.parameterize_pipeline(obs)

    assert config.max_iterations == 5
    assert config.shield_strictness == "CRITICAL"
    assert config.retrieval_depth == 8

def test_acpe_low_volatility_retrieval():
    """Verifies that ACPE optimizes parameters downward under low volatility."""
    acpe = AdaptiveControlPolicyEngine()

    # Trigger low volatility policy
    obs = {"market": {"volatility": 0.02}}
    config = acpe.parameterize_pipeline(obs)

    assert config.max_iterations == 2
    assert config.shield_strictness == "NORMAL"
    assert config.retrieval_depth == 3

def test_acpe_sub_millisecond_latency():
    """Asserts that ACPE pipeline parameterization stays strictly under 1.5ms."""
    acpe = AdaptiveControlPolicyEngine()
    obs = {"market": {"volatility": 0.45}}

    # Measure execution latency over 100 trials
    latencies = []
    for _ in range(100):
        t0 = time.perf_counter()
        acpe.parameterize_pipeline(obs)
        latencies.append((time.perf_counter() - t0) * 1000)

    avg_latency = sum(latencies) / len(latencies)
    assert avg_latency < 1.5, f"ACPE latency was too high: {avg_latency:.4f}ms"
