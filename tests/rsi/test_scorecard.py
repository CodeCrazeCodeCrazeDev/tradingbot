"""Mission §14: RSI scorecard computed from archive + ledger."""

from __future__ import annotations

import pytest

from trading_bot.recursive_self_improvement.archive import ParetoArchive
from trading_bot.recursive_self_improvement.memory import ImprovementMemory
from trading_bot.recursive_self_improvement.scorecard import RSIScorecard


def test_scorecard_on_fixture_archive(tmp_path):
    a = ParetoArchive(tmp_path / "archive.jsonl")
    m = ImprovementMemory(str(tmp_path / "mem.db"))
    m.append_evidence(trial_id="t1", nonce="n1", payload={}, status="rejected")

    for i in range(4):
        a.record_candidate(
            genome_id=f"g{i}", parent_id="baseline", contract_hash="c",
            dataset_hash="d", strategy_family="mean_reversion",
            metric_vector={"net_return": 0.01 * i, "max_drawdown": 0.01,
                           "cvar_95": 0.01, "turnover": 1.0},
            delta={}, verdict="eligible_for_operator_review" if i == 3 else "rejected",
            role="challenger" if i == 3 else "failed_informative",
            extra={"transfer_class": "TRANSFERABLE" if i == 3 else "LOCAL",
                   "fingerprint": f"fp{i}"})
    card = RSIScorecard(a, m).compute()
    assert card["trials_total"] == 4
    assert card["eligible_rate"] == 0.25
    assert card["transfer_rate_of_eligible"] == 1.0
    assert card["trials_per_eligible"] == 4.0
    assert card["archive_chain_valid"] is True
    assert card["evidence_ledger_valid"] is True
