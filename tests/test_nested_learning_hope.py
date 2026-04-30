#!/usr/bin/env python3
"""Tests for the HOPE-inspired nested learning memory."""

import importlib
import json
import time
from pathlib import Path

hope = importlib.import_module("trading_bot.core.nested_learning_hope")
ci = importlib.import_module("trading_bot.core.signal_counterintelligence")


def _observation(lineage_hashes=None, surprise=0.20):
    return hope.HopeObservation(
        observation_id="obs-1",
        signal_id="sig-hope",
        asset="EURUSD",
        timestamp=time.time(),
        features={"momentum": 0.7, "volatility": 0.2},
        prediction=0.10,
        realized_outcome=0.10 + surprise,
        regime="trend",
        lineage_hashes=lineage_hashes if lineage_hashes is not None else ["lineage-1"],
        passport_id="passport-1",
        source_quality=0.95,
    )


def test_nested_learning_updates_multi_timescale_memory_and_recommends(tmp_path):
    engine = hope.NestedLearningHopeEngine(
        audit_ledger=ci.AppendOnlyJsonlAuditLedger(str(tmp_path), "hope.jsonl")
    )

    report = engine.observe(
        _observation(),
        role=ci.IntelligenceRole.RESEARCH_ANALYST,
        zone=ci.IntelligenceZone.RESEARCH,
    )
    recommendation = engine.recommend(
        "sig-hope",
        "EURUSD",
        "trend",
        {"momentum": 0.7, "volatility": 0.2},
    )

    assert report.accepted
    assert set(report.updated_tiers) == {"short_term", "episodic", "regime", "strategy"}
    assert recommendation.matched_entries
    assert recommendation.memory_score != 0
    assert engine.audit_ledger.verify()


def test_nested_learning_requires_lineage_and_blocks_production_updates(tmp_path):
    engine = hope.NestedLearningHopeEngine(
        audit_ledger=ci.AppendOnlyJsonlAuditLedger(str(tmp_path), "hope.jsonl")
    )

    missing_lineage = engine.observe(
        _observation(lineage_hashes=[]),
        role=ci.IntelligenceRole.RESEARCH_ANALYST,
        zone=ci.IntelligenceZone.RESEARCH,
    )
    production_update = engine.attempt_production_update(_observation())

    assert not missing_lineage.accepted
    assert any("lineage" in reason for reason in missing_lineage.blocked_reasons)
    assert not production_update.accepted
    assert any("read-only" in reason for reason in production_update.blocked_reasons)


def test_signed_snapshot_is_read_only_and_tamper_evident(tmp_path):
    engine = hope.NestedLearningHopeEngine(
        audit_ledger=ci.AppendOnlyJsonlAuditLedger(str(tmp_path), "hope.jsonl"),
        signing_secret="unit-secret",
    )
    engine.observe(
        _observation(),
        role=ci.IntelligenceRole.STAGING_SYSTEM,
        zone=ci.IntelligenceZone.STAGING,
    )

    snapshot = engine.export_snapshot("staging-system", zone=ci.IntelligenceZone.STAGING)
    production_engine = hope.NestedLearningHopeEngine(signing_secret="unit-secret")
    loaded = production_engine.load_production_snapshot(snapshot)
    production_recommendation = production_engine.recommend(
        "sig-hope",
        "EURUSD",
        "trend",
        {"momentum": 0.7, "volatility": 0.2},
        zone=ci.IntelligenceZone.PRODUCTION,
    )

    tampered_payload = json.loads(json.dumps(snapshot.to_dict()))
    tampered_payload["tiers"]["short_term"][0]["value_vector"]["momentum"] = 99.0
    tampered = hope.HopeMemorySnapshot(
        snapshot_id=tampered_payload["snapshot_id"],
        created_at=tampered_payload["created_at"],
        source_zone=ci.IntelligenceZone.STAGING,
        tiers=tampered_payload["tiers"],
        digest=tampered_payload["digest"],
        signer=tampered_payload["signer"],
        signature=tampered_payload["signature"],
        read_only=tampered_payload["read_only"],
    )

    assert loaded
    assert production_recommendation.snapshot_digest == snapshot.digest
    assert not production_engine.verify_snapshot(tampered)


def test_failed_passport_validation_blocks_nested_update(tmp_path):
    engine = hope.NestedLearningHopeEngine(
        audit_ledger=ci.AppendOnlyJsonlAuditLedger(str(tmp_path), "hope.jsonl")
    )
    passport_failure = ci.DataPassportValidationResult(
        accepted=False,
        passport_id="passport-1",
        lineage_hash="lineage-1",
        reasons=["license expired"],
    )

    report = engine.observe(
        _observation(),
        role=ci.IntelligenceRole.RESEARCH_ANALYST,
        zone=ci.IntelligenceZone.RESEARCH,
        passport_validation=passport_failure,
    )

    assert not report.accepted
    assert "license expired" in report.blocked_reasons
