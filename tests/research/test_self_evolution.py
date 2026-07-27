import pytest

from trading_bot.research.research_os import ResearchWorkspace
from trading_bot.research.self_evolution.mutator import ControlledMutator
from trading_bot.research.self_evolution.gate import InvariantGate
from trading_bot.research.self_evolution.tournament import RegimeTournament


@pytest.fixture
def workspace():
    """Initializes the central Workspace."""
    return ResearchWorkspace()


@pytest.fixture
def mutator():
    """Initializes the Controlled Mutator."""
    return ControlledMutator()


@pytest.fixture
def gate():
    """Initializes the Invariant Gate."""
    return InvariantGate()


@pytest.fixture
def tournament():
    """Initializes the Regime Tournament manager."""
    return RegimeTournament(["trending", "ranging", "volatile"])


def test_mutator_parameter_mutation(mutator):
    """Verifies that the mutator performs parameter mutations within safe bounds."""
    base_params = {"lora_rank": 8, "learning_rate": 0.001, "volatility_threshold": 0.03}
    mutated = mutator.mutate_parameters(base_params)

    assert "lora_rank" in mutated
    assert "learning_rate" in mutated
    # Should not mutate string or non-numeric keys if present
    assert base_params["lora_rank"] == 8  # Baseline must remain untouched


def test_mutator_compositional_crossover(mutator):
    """Verifies functional component crossovers structurally integrate parent metrics."""
    parent_a = {"learning_rate": 0.001, "lora_rank": 8, "risk_multiplier": 1.5}
    parent_b = {"learning_rate": 0.002, "lora_rank": 16, "risk_multiplier": 2.0}

    child = mutator.compositional_crossover(parent_a, parent_b)
    assert child["learning_rate"] in [0.001, 0.002]
    assert child["lora_rank"] in [8, 16]


def test_invariant_gate_clean_pass(gate):
    """Verifies that compliant mutants pass all unbreachable gates."""
    clean_code = "def compute_signal(prices): return prices * 1.01"
    metrics = {"max_drawdown_pct": 5.4, "sharpe": 2.2}

    report = gate.audit_mutant(clean_code, metrics, "MIT", is_stat_sig=True)
    assert report.is_valid is True
    assert report.security_passed is True
    assert report.risk_passed is True
    assert report.license_passed is True
    assert report.validation_passed is True


def test_invariant_gate_violating_all_barriers(gate):
    """Verifies that violations in any/all of the four categories are caught and flagged."""
    corrupted_code = "eval('setup_backdoor()')"
    corrupted_metrics = {"max_drawdown_pct": 28.5}  # Drawdown exceeds 15% limit

    report = gate.audit_mutant(corrupted_code, corrupted_metrics, "GPL-3.0", is_stat_sig=False)
    assert report.is_valid is False
    assert report.security_passed is False
    assert report.risk_passed is False
    assert report.license_passed is False
    assert report.validation_passed is False
    assert len(report.violations) >= 4


def test_regime_tournament_mutant_victory(tournament):
    """Verifies that the mutant is promoted when outperforming across multiple regimes."""
    champ_metrics = {"trending_sharpe": 1.1, "ranging_sharpe": 0.8, "volatile_sharpe": 0.7}
    mutant_metrics = {"trending_sharpe": 1.5, "ranging_sharpe": 1.2, "volatile_sharpe": 1.1}

    result = tournament.compare_mutant_to_champion(champ_metrics, mutant_metrics)
    assert result.is_promoted is True
    assert result.wins == 3
    assert result.losses == 0


def test_regime_tournament_champion_victory(tournament):
    """Verifies that the active champion is retained when the mutant fails to exceed its performance."""
    champ_metrics = {"trending_sharpe": 1.8, "ranging_sharpe": 1.4, "volatile_sharpe": 1.2}
    mutant_metrics = {"trending_sharpe": 1.2, "ranging_sharpe": 0.9, "volatile_sharpe": 0.8}

    result = tournament.compare_mutant_to_champion(champ_metrics, mutant_metrics)
    assert result.is_promoted is False
    assert result.wins == 0
    assert result.losses == 3
