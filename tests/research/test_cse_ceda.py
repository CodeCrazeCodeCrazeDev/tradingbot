import pytest

from trading_bot.research.research_os import ResearchWorkspace
from trading_bot.research.cse_ceda import (
    InvariantGatedEvolutionEngine,
    CEDADecisionGate,
    InvariantViolation
)


@pytest.fixture
def workspace():
    """Initializes the central Workspace."""
    return ResearchWorkspace()


@pytest.fixture
def igee(workspace):
    """Initializes the Invariant-Gated Evolution Engine."""
    return InvariantGatedEvolutionEngine(workspace)


@pytest.fixture
def ceda(workspace):
    """Initializes the CEDA Decision Gate."""
    return CEDADecisionGate(workspace)


def test_audit_mutant_code_clean(igee):
    """Verifies that clean code passes the security invariant audit."""
    clean_code = (
        "def run_strategy_calculation(close_prices):\n"
        "    return close_prices * 1.02\n"
    )
    assert igee.audit_mutant_code(clean_code) is True


def test_audit_mutant_code_violating_security(igee):
    """Verifies that mutated code violating security invariants is instantly purged via InvariantViolation."""
    unsafe_code = (
        "def setup_backdoor():\n"
        "    eval('print(\"Compromising...\")')\n"
    )
    with pytest.raises(InvariantViolation) as exc_info:
        igee.audit_mutant_code(unsafe_code)
    assert "SECURITY_INVARIANT_VIOLATION" in str(exc_info.value)


def test_audit_risk_invariants_clean(igee):
    """Verifies that risk metrics within bounds pass the risk invariant audit."""
    metrics = {"max_drawdown_pct": 8.5, "sharpe_ratio": 1.85}
    assert igee.audit_risk_invariants(metrics) is True


def test_audit_risk_invariants_violating(igee):
    """Verifies that risk metrics violating thresholds are instantly rejected via InvariantViolation."""
    corrupted_metrics = {"max_drawdown_pct": 24.5, "sharpe_ratio": 0.45}
    with pytest.raises(InvariantViolation) as exc_info:
        igee.audit_risk_invariants(corrupted_metrics)
    assert "RISK_INVARIANT_VIOLATION" in str(exc_info.value)


def test_parameter_mutations_sandbox(igee):
    """Verifies that safe, guided parameter mutations are applied within the sandbox."""
    base_params = {"lora_rank": 8, "learning_rate": 0.001, "volatility_threshold": 0.03}
    mutated = igee.mutate_parameters(base_params, mutation_scale=0.1)

    assert "lora_rank" in mutated
    assert mutated["lora_rank"] != base_params["lora_rank"] or mutated["learning_rate"] != base_params["learning_rate"]
    # Ensure baseline parameters are unmodified (sandbox isolation)
    assert base_params["lora_rank"] == 8


def test_ceda_regime_tournament_challenger_victory(ceda):
    """Verifies that the Challenger mutant is promoted when outperforming across the majority of regimes."""
    champ_metrics = {"trending_sharpe": 1.2, "ranging_sharpe": 0.9, "volatile_sharpe": 0.8, "drawdown": 12.0}
    chal_metrics = {"trending_sharpe": 1.6, "ranging_sharpe": 1.1, "volatile_sharpe": 1.2, "drawdown": 8.0}

    is_promoted, explanation = ceda.run_regime_tournament(champ_metrics, chal_metrics, ["trending", "ranging", "volatile"])
    assert is_promoted is True
    assert "PROMOTED_BY_CEDA" in explanation


def test_ceda_regime_tournament_champion_victory(ceda):
    """Verifies that the baseline Champion is retained when challenger fails to outperform."""
    champ_metrics = {"trending_sharpe": 1.8, "ranging_sharpe": 1.4, "volatile_sharpe": 1.1, "drawdown": 6.5}
    chal_metrics = {"trending_sharpe": 1.2, "ranging_sharpe": 0.9, "volatile_sharpe": 0.8, "drawdown": 11.0}

    is_promoted, explanation = ceda.run_regime_tournament(champ_metrics, chal_metrics, ["trending", "ranging", "volatile"])
    assert is_promoted is False
    assert "CHAMPION_RETAINED_BY_CEDA" in explanation
