"""Tests for venue-parity grading and soak-gated promotion stages."""

from __future__ import annotations

import sys
import time
from pathlib import Path

import pytest
from cryptography.hazmat.primitives.asymmetric.ed25519 import (
    Ed25519PrivateKey)

sys.path.insert(0, str(Path(__file__).resolve().parent))

from trading_bot.recursive_self_improvement.engine_v2 import (  # noqa: E402
    AuthorizationError, OperatorAuthorization, PromotionLadder)
from trading_bot.recursive_self_improvement.venue_parity import (  # noqa: E402
    parity_from_bar_rows, parity_grade)


class TestParityGrade:
    def test_identical_series_grade_a(self):
        nets = [0.001, -0.0005, 0.002, 0.0, -0.001] * 20
        res = parity_grade(nets, list(nets))
        assert res.grade == "A" and res.score == 1.0

    def test_divergent_series_grade_f(self):
        sim = [0.01] * 100
        ven = [-0.01] * 100
        res = parity_grade(sim, ven)
        assert res.grade == "F" and res.score == 0.0

    def test_partial_agreement_bands(self):
        sim = [0.01] * 100
        ven = [0.01] * 85 + [-0.01] * 15
        res = parity_grade(sim, ven)
        assert res.grade == "A" and res.score == pytest.approx(0.85)

    def test_magnitude_mismatch_counts_against(self):
        sim = [0.10] * 50
        ven = [0.001] * 50  # same sign, 100x magnitude — beyond rel_tol
        res = parity_grade(sim, ven, rel_tol=0.5)
        assert res.matched == 0 and res.grade == "F"

    def test_length_mismatch_refused(self):
        with pytest.raises(ValueError, match="length mismatch"):
            parity_grade([0.1], [0.1, 0.2])

    def test_empty_series_grade_f(self):
        res = parity_grade([], [])
        assert res.grade == "F" and res.n_bars == 0


class TestParityFromRows:
    def _rows(self, sym, ts_range, net):
        return [{"symbol": sym, "timestamp": float(t), "net": net(t)}
                for t in ts_range]

    def test_worst_symbol_governs(self):
        sim = (self._rows("EURUSD", range(10), lambda t: 0.01)
               + self._rows("XAUUSD", range(10), lambda t: 0.01))
        ven = (self._rows("EURUSD", range(10), lambda t: 0.01)
               + self._rows("XAUUSD", range(10), lambda t: -0.01))
        out = parity_from_bar_rows(sim, ven)
        assert out["grade"] == "F"
        assert out["symbols"]["EURUSD"]["grade"] == "A"
        assert out["symbols"]["XAUUSD"]["grade"] == "F"

    def test_missing_venue_rows_count_as_mismatch(self):
        sim = self._rows("EURUSD", range(10), lambda t: 0.01)
        ven = self._rows("EURUSD", range(5), lambda t: 0.01)
        out = parity_from_bar_rows(sim, ven)
        assert out["n_bars"] == 10 and out["matched"] == 5


class TestSoakGatedPromotion:
    def _ladder(self, req=None):
        key = Ed25519PrivateKey.generate()
        return PromotionLadder(key.public_key(),
                               soak_requirements=req), key

    def _auth(self, key, genome_id, stage, contract_hash="ch"):
        return OperatorAuthorization(
            genome_id=genome_id, contract_hash=contract_hash, stage=stage,
            issued_by="operator", expires_at=time.time() + 3600)

    def _sign(self, key, auth):
        return key.sign(auth.canonical()).hex()

    def test_no_requirement_default_allows(self):
        ladder, key = self._ladder()
        ladder._contract_for["g1"] = "ch"
        auth = self._auth(key, "g1", "paper")
        assert ladder.advance("g1", "paper", auth, self._sign(key, auth)) == "paper"

    def test_soak_blocks_until_accrued(self):
        ladder, key = self._ladder({"paper": 100})
        ladder._contract_for["g1"] = "ch"
        auth = self._auth(key, "g1", "paper")
        sig = self._sign(key, auth)
        with pytest.raises(AuthorizationError, match="soak"):
            ladder.advance("g1", "paper", auth, sig)
        ladder.record_soak("g1", 60)
        with pytest.raises(AuthorizationError, match="soak"):
            ladder.advance("g1", "paper", auth, sig)
        ladder.record_soak("g1", 40)
        assert ladder.advance("g1", "paper", auth, sig) == "paper"
        assert ladder.soak_cycles("g1") == 100

    def test_soak_only_gates_configured_stages(self):
        ladder, key = self._ladder({"production": 500})
        ladder._contract_for["g1"] = "ch"
        auth = self._auth(key, "g1", "canary")
        # canary has no soak requirement — authorized advance works
        assert ladder.advance("g1", "canary", auth, self._sign(key, auth)) == "canary"

    def test_soak_rejects_bad_cycles(self):
        ladder, _ = self._ladder()
        with pytest.raises(ValueError):
            ladder.record_soak("g1", -1)
        with pytest.raises(ValueError):
            ladder.record_soak("g1", 1.5)
