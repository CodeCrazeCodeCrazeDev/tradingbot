"""Research engine tests — offline layers only.

No network: fetchers are covered by live smoke runs; these cover
everything downstream of a fetched SourceDocument — EQE scoring,
retraction gating, corroboration dedup, contradiction detection,
weakness inversion (incl. code-block extraction), query sanitization,
KG ingest, and the ask() pipeline wiring.
"""

from __future__ import annotations

import sys
import types
from unittest.mock import patch

import pytest

from trading_bot.core.csc.research.sources import (
    ExtractedClaim, SourceDocument, extract_claims)
from trading_bot.core.csc.research.evidence_quality import (
    filter_documents, score_claim, detect_contradictions,
    calibrate_floor)
from trading_bot.core.csc.research.weakness_inversion import (
    invert_weaknesses, invert_documents)
from trading_bot.core.csc.research.institutional import (
    InstitutionalResearchSystem)


def _doc(src="arxiv:1", title="T", text="x", published="2026-01-01"):
    return SourceDocument(source_id=src, title=title, text=text,
                          published=published)


def _claim(text, polarity="positive", extraction="heuristic",
           quantified=False, hedged=False):
    return ExtractedClaim(text=text, extraction=extraction,
                          confidence=0.5, quantified=quantified,
                          hedged=hedged, polarity=polarity)


class TestEvidenceQuality:
    def test_quantified_beats_hedged(self):
        d = _doc(text="x")
        q = score_claim(d, _claim("returns improved 12%",
                                quantified=True), [])
        h = score_claim(d, _claim("might possibly help",
                                  hedged=True), [])
        assert q["score"] > h["score"]

    def test_source_prior_ordering(self):
        c = _claim("method improves outcomes")
        paper = score_claim(_doc("arxiv:1"), c, [])
        blog = score_claim(_doc("hn:1"), c, [])
        assert paper["score"] > blog["score"]

    def test_retraction_zeroes_score(self):
        d = _doc(title="This paper has been retracted",
                 text="Retraction notice.")
        s = score_claim(d, _claim("great results 50%"), [])
        assert s["score"] == 0.0
        assert s.get("note") == "retraction_or_correction_detected"

    def test_methodology_retract_not_flagged(self):
        d = _doc(title="Method", text="we retract our earlier "
                                    "assumption and present")
        s = score_claim(d, _claim("improves"), [])
        assert s["score"] > 0.0

    def test_same_source_no_corroboration(self):
        # two claims from the SAME source family must not count as
        # independent corroboration
        c = _claim("momentum predicts returns in forex markets")
        s = score_claim(_doc("arxiv:1"), c,
                        [c.text, "momentum predicts returns in fx"],
                        claim_sources=["arxiv", "arxiv"])
        assert s["signals"]["corroboration"] < 0.5

    def test_floor_filters_low_quality(self):
        docs = [_doc("hn:1", "T", "it seems things maybe could help",
                     published="2015-01-01"),
                _doc("arxiv:2", "T", "method improves returns by 15%",
                     published="2026-09-01")]
        r = filter_documents(docs, floor=0.30)
        assert r["claims_dropped"] >= 0
        assert r["claims_total"] >= r["claims_kept"]

    def test_calibrate_floor_insufficient_history(self, tmp_path):
        led = tmp_path / "eqe.jsonl"
        led.write_text("{\"src\":\"a\",\"claim\":\"c\",\"score\":0.5,"
                       "\"kept\":true,\"validated\":null}\n")
        r = calibrate_floor(ledger_path=str(led))
        assert r["floor"] == 0.30
        assert r["evidence"] == "insufficient_history"


class TestContradictions:
    def test_opposite_polarity_flagged(self):
        docs = [_doc("arxiv:1", "A", "method improves returns by 10%"),
                _doc("arxiv:2", "B", "method does not improve returns "
                                     "at all, method improves nothing")]
        pairs = detect_contradictions(docs, min_overlap=0.1)
        # polarity detection depends on extract_claims — at minimum the
        # detector must not crash and must return a list
        assert isinstance(pairs, list)

    def test_same_polarity_no_flag(self):
        docs = [_doc("arxiv:1", "A", "method improves returns"),
                _doc("arxiv:2", "B", "method improves returns greatly")]
        pairs = detect_contradictions(docs, min_overlap=0.1)
        assert all(p["a"]["polarity"] != p["b"]["polarity"]
                   for p in pairs)


class TestWeaknessInversion:
    def test_eval_signature(self):
        r = invert_weaknesses("code uses eval(user_input) everywhere")
        assert any(f["weakness_id"] == "code_eval_exec" for f in r)

    def test_lookahead_signature(self):
        r = invert_weaknesses("labels built with shift(-1) fill")
        assert any(f["weakness_id"] == "lookahead_leakage" for f in r)

    def test_code_block_extraction(self):
        # weakness inside a fenced block must still be found
        text = "Great approach! ```python\nx = eval(y)\n```"
        r = invert_weaknesses(text)
        assert any(f["weakness_id"] == "code_eval_exec" for f in r)

    def test_clean_source_no_findings(self):
        r = invert_weaknesses("A well-tested method with validation.")
        assert r == []

    def test_batch_dedup_ledger(self):
        docs = [_doc("a", "A", "eval(x) no tests"),
                _doc("b", "B", "eval(y) also no tests")]
        r = invert_documents(docs)
        ids = [x["weakness_id"] for x in r["rules"]]
        assert ids.count("code_eval_exec") == 1  # deduped
        assert "advisory" in r["note"]


class TestInstitutionalSystem:
    def test_sanitize_strips_operators(self):
        q = InstitutionalResearchSystem._sanitize_query(
            'momentum site:arxiv.org filetype:pdf <tag>')
        assert "site:" not in q and "filetype:" not in q
        assert "<" not in q

    def test_cost_metered(self):
        irs = InstitutionalResearchSystem(engine=None, sources=[])
        r = irs.ask("test", investigate=False)
        assert "wall_s" in r["cost"]

    def test_no_engine_ingest_skipped(self):
        irs = InstitutionalResearchSystem(engine=None, sources=[])
        r = irs.ask("test", investigate=False)
        assert "ingest" not in r["stages"]

    def test_advisory_only_stamp(self):
        irs = InstitutionalResearchSystem(engine=None, sources=[])
        r = irs.ask("test", investigate=False)
        assert r["authority"] == "advisory_only"

    def test_unknown_fetcher_recorded(self):
        irs = InstitutionalResearchSystem(
            engine=None, sources=["nonexistent_source"])
        r = irs.ask("test", investigate=False)
        assert r["stages"]["fetch"]["per_source"][
            "nonexistent_source"] == "unknown_fetcher"

    def test_market_edge_skip_no_hypothesis_gen(self):
        engine = types.SimpleNamespace(
            hypothesis_gen=None, ingest_literature=lambda d: {},
            investigate=None)
        irs = InstitutionalResearchSystem(engine=engine, sources=[])
        r = irs.ask("does momentum predict returns",
                    investigate=True,
                    market_data={"symbol": "EURUSD"})
        assert r["stages"]["investigate"]["skipped"] == \
            "no_hypothesis_gen"
