#!/usr/bin/env python3
"""Tests for AlphaAlgo signal counterintelligence."""

import importlib.util
import json
import sys
import time
from pathlib import Path

MODULE_PATH = Path(__file__).parent.parent / "trading_bot" / "core" / "signal_counterintelligence.py"
SPEC = importlib.util.spec_from_file_location("signal_counterintelligence_direct", MODULE_PATH)
ci = importlib.util.module_from_spec(SPEC)
sys.modules["signal_counterintelligence_direct"] = ci
SPEC.loader.exec_module(ci)


def _source(source_id="src-1", license_status=None, compliance=0.96, reliability=0.90):
    now = time.time()
    return ci.DataSourceProvenance(
        source_id=source_id,
        name=f"Source {source_id}",
        category=ci.DataSourceCategory.MARKET,
        license_status=license_status or ci.SourceLicenseStatus.PUBLIC,
        license_name="public exchange feed terms",
        permission_basis="public/licensed collection",
        collected_at=now,
        observed_at=now - 10,
        uri="https://example.test/feed",
        provenance_chain=["collector", "canonicalizer", "hash"],
        compliance_score=compliance,
        reliability_score=reliability,
    )


def _evidence(evidence_id="ev-1", source_id="src-1", features=None):
    now = time.time()
    return ci.IntelligenceEvidence(
        evidence_id=evidence_id,
        source_id=source_id,
        claim="price/volume behavior supports hypothesis",
        observed_at=now - 5,
        content_hash="abc123",
        features=features or {},
    )


def _signal(source_ids=None, evidence_ids=None, thesis="licensed public signal", confidence=0.70, features=None):
    return ci.SignalClaim(
        signal_id="sig-1",
        asset="EURUSD",
        thesis=thesis,
        horizon="1d",
        confidence=confidence,
        source_ids=source_ids or ["src-1", "src-2"],
        evidence_ids=evidence_ids or ["ev-1", "ev-2"],
        features=features or {"validation_sharpe": 1.1, "train_sharpe": 1.3, "sample_size": 240},
    )


def test_source_validation_rejects_private_stolen_confidential_and_mnpi_sources():
    validator = ci.SourceValidationLayer()
    forbidden = [
        ci.SourceLicenseStatus.PRIVATE,
        ci.SourceLicenseStatus.STOLEN,
        ci.SourceLicenseStatus.CONFIDENTIAL,
        ci.SourceLicenseStatus.MATERIAL_NONPUBLIC,
    ]

    reports = [validator.validate(_source(str(index), status)) for index, status in enumerate(forbidden)]

    assert all(not report.accepted for report in reports)
    assert all(report.decision == ci.IntelligenceDecision.REJECT for report in reports)
    assert all(report.lineage_hash for report in reports)


def test_source_validation_requires_provenance_license_timestamp_and_compliance_score():
    now = time.time()
    source = ci.DataSourceProvenance(
        source_id="weak",
        name="Weak source",
        category=ci.DataSourceCategory.ALTERNATIVE,
        license_status=ci.SourceLicenseStatus.UNKNOWN,
        license_name="",
        permission_basis="",
        collected_at=now + 1000,
        observed_at=0,
        provenance_chain=[],
        compliance_score=0.40,
        reliability_score=0.20,
    )

    report = ci.SourceValidationLayer().validate(source, now=now)

    assert not report.accepted
    assert any("license" in finding for finding in report.findings)
    assert any("timestamp" in finding for finding in report.findings)
    assert any("provenance" in finding for finding in report.findings)
    assert any("compliance score" in finding for finding in report.findings)


def test_signal_counterintelligence_accepts_only_public_licensed_permissioned_or_internal_data():
    engine = ci.SignalCounterintelligenceEngine()
    sources = [
        _source("src-1", ci.SourceLicenseStatus.PUBLIC),
        _source("src-2", ci.SourceLicenseStatus.LICENSED),
        _source("src-3", ci.SourceLicenseStatus.PERMISSIONED),
        _source("src-4", ci.SourceLicenseStatus.INTERNAL_GENERATED),
    ]
    evidence = [
        _evidence("ev-1", "src-1"),
        _evidence("ev-2", "src-2"),
        _evidence("ev-3", "src-3"),
        _evidence("ev-4", "src-4"),
    ]
    signal = _signal([source.source_id for source in sources], [item.evidence_id for item in evidence])

    report = engine.review_signal(signal, sources, evidence)

    assert report.accepted
    assert report.decision == ci.IntelligenceDecision.ACCEPT
    assert report.compliance_score >= 0.80
    assert report.reliability_score >= 0.45
    assert report.audit_digest
    assert engine.audit_ledger.verify()


def test_signal_counterintelligence_attacks_leakage_overfitting_adversarial_behavior_and_weak_claims():
    engine = ci.SignalCounterintelligenceEngine()
    source = _source("src-1", ci.SourceLicenseStatus.PUBLIC)
    evidence = [_evidence("ev-1", "src-1", {"future_return": 0.02})]
    signal = _signal(
        ["src-1"],
        ["ev-1"],
        thesis="signal from leaked earnings and spoofing pressure",
        confidence=0.95,
        features={
            "future_return": 0.02,
            "train_sharpe": 5.5,
            "validation_sharpe": 0.8,
            "sample_size": 25,
            "confidence": 0.95,
        },
    )

    report = engine.review_signal(signal, [source], evidence)
    vectors = {finding.vector for finding in report.findings}

    assert not report.accepted
    assert report.decision == ci.IntelligenceDecision.REJECT
    assert ci.SignalAttackVector.DATA_LEAKAGE in vectors
    assert ci.SignalAttackVector.OVERFITTING in vectors
    assert ci.SignalAttackVector.ADVERSARIAL_MARKET_BEHAVIOR in vectors
    assert ci.SignalAttackVector.MATERIAL_NONPUBLIC_INFORMATION in vectors
    assert ci.SignalAttackVector.WEAK_CLAIM in vectors


def test_compartmentalized_security_blocks_execution_research_access_and_live_self_modification():
    model = ci.CompartmentalizedSecurityModel()

    research_breach = model.validate_access(
        ci.IntelligenceRole.EXECUTION_OPERATOR,
        ci.IntelligenceCompartment.RESEARCH,
        "read research signal notebook",
    )
    model_write = model.validate_access(
        ci.IntelligenceRole.EXECUTION_OPERATOR,
        ci.IntelligenceCompartment.PRODUCTION_MODEL,
        "mutate production model",
        signed_model_artifact=True,
    )
    model_read_unsigned = model.validate_access(
        ci.IntelligenceRole.EXECUTION_OPERATOR,
        ci.IntelligenceCompartment.PRODUCTION_MODEL,
        "read production model",
    )
    model_read_signed = model.validate_access(
        ci.IntelligenceRole.EXECUTION_OPERATOR,
        ci.IntelligenceCompartment.PRODUCTION_MODEL,
        "read production model",
        signed_model_artifact=True,
    )
    ai_deploy = model.validate_access(
        ci.IntelligenceRole.AI_ENGINEERING_AGENT,
        ci.IntelligenceCompartment.RESEARCH,
        "deploy live self-modification to production",
        signed_approval=True,
    )

    assert not research_breach.accepted
    assert not model_write.accepted
    assert not model_read_unsigned.accepted
    assert model_read_signed.accepted
    assert not ai_deploy.accepted


def test_legal_collection_layer_rejects_unlicensed_collection_tasks():
    mission = ci.MissionRequirement(
        mission_id="mission-collection",
        tradable_question="Can licensed data support a volatility edge?",
        edge_hypothesis="Only legal data may enter the research environment.",
        objective_functions=["compliance", "risk_adjusted_return"],
        risk_budget=0.01,
        allowed_assets=["SPY"],
    )
    layer = ci.LegalCollectionLayer()
    approved_task = ci.CollectionTask(
        "market-feed",
        ci.DataSourceCategory.MARKET,
        "public market feed",
        "https://example.test/market",
        ci.SourceLicenseStatus.PUBLIC,
        "public feed terms",
        "market data collection",
    )
    rejected_task = ci.CollectionTask(
        "confidential-chat",
        ci.DataSourceCategory.ALTERNATIVE,
        "confidential channel",
        "internal://leak",
        ci.SourceLicenseStatus.CONFIDENTIAL,
        "",
        "alternative data collection",
    )

    plan = layer.plan(mission, [approved_task, rejected_task])

    assert not plan.accepted
    assert plan.approved_tasks == [approved_task]
    assert plan.rejected_tasks == [rejected_task]
    assert any("public, licensed, permissioned" in note for note in plan.compliance_notes)


def test_model_artifact_registry_requires_signed_read_only_production_artifact():
    registry = ci.ModelArtifactRegistry("unit-secret")
    artifact = registry.sign(
        "alpha-risk-model",
        b"weights",
        "researcher",
        approved_for_production=False,
        data_manifest={"sources": ["licensed"]},
    )
    registry.counter_sign(artifact, "staging", "staging-system")
    registry.counter_sign(artifact, "validation", "validation-officer")
    registry.approve_for_production(artifact)
    unsigned = ci.SignedModelArtifact(
        artifact_id="bad",
        model_name=artifact.model_name,
        model_digest=artifact.model_digest,
        signer=artifact.signer,
        signature="bad-signature",
        created_at=artifact.created_at,
        read_only=True,
        approved_for_production=True,
    )
    mutable = ci.SignedModelArtifact(
        artifact_id="mutable",
        model_name=artifact.model_name,
        model_digest=artifact.model_digest,
        signer=artifact.signer,
        signature=artifact.signature,
        created_at=artifact.created_at,
        read_only=False,
        approved_for_production=True,
    )

    assert registry.verify(artifact)
    assert not registry.verify(unsigned)
    assert not registry.verify(mutable)
    assert registry.access_report(artifact, ci.IntelligenceRole.EXECUTION_OPERATOR).accepted
    assert not registry.access_report(unsigned, ci.IntelligenceRole.EXECUTION_OPERATOR).accepted


def test_alphaalgo_intelligence_directorate_runs_eight_layer_decision_pipeline():
    directorate = ci.AlphaAlgoIntelligenceDirectorate()
    mission = ci.MissionRequirement(
        mission_id="mission-1",
        tradable_question="Does EURUSD have a licensed macro/liquidity edge today?",
        edge_hypothesis="Public macro and liquidity data imply favorable risk-adjusted carry.",
        objective_functions=["risk_adjusted_return", "drawdown_control", "execution_feasibility"],
        risk_budget=0.02,
        allowed_assets=["EURUSD"],
    )
    sources = [_source("src-1", ci.SourceLicenseStatus.PUBLIC), _source("src-2", ci.SourceLicenseStatus.LICENSED)]
    evidence = [_evidence("ev-1", "src-1"), _evidence("ev-2", "src-2")]
    signal = _signal(["src-1", "src-2"], ["ev-1", "ev-2"], confidence=0.72)
    artifact = directorate.model_registry.sign(
        "alphaalgo-production-decision-model",
        b"read-only-model-bytes",
        "researcher",
        approved_for_production=False,
        data_manifest={"sources": [source.source_id for source in sources]},
    )
    directorate.model_registry.counter_sign(artifact, "staging", "staging-system")
    directorate.model_registry.counter_sign(artifact, "validation", "validation-officer")
    directorate.model_registry.approve_for_production(artifact)

    report = directorate.evaluate(
        mission,
        signal,
        sources,
        evidence,
        production_model_artifact=artifact,
        feedback_metrics={
            "forecast_accuracy": 0.62,
            "pnl_attribution": 0.11,
            "slippage_attribution": -0.01,
            "regime_specific_performance": 0.08,
            "strategy_decay_score": 0.30,
        },
    )

    assert report.collection_plan.accepted
    assert report.model_artifact_report.accepted
    assert report.counterintelligence.accepted
    assert report.governance_decision == ci.IntelligenceDecision.ACCEPT
    assert report.governance_report.signal_validator_passed
    assert report.governance_report.risk_gatekeeper_passed
    assert report.governance_report.capital_allocation_judge_passed
    assert not report.governance_report.kill_switch_active
    assert report.governance_report.audit_logger_enabled
    assert report.compartment_report.accepted
    assert len(report.analysis_cells) == 7
    assert "strategy_evidence_graph" in report.fusion_graph
    assert report.fusion_report.graph_digest
    assert report.feedback_report.forecast_accuracy == 0.62
    assert not report.feedback_report.strategy_decay_detected
    assert report.audit_record.record_hash
    assert directorate.audit_ledger.verify()


def test_append_only_jsonl_audit_ledger_persists_and_detects_tamper(tmp_path):
    ledger = ci.AppendOnlyJsonlAuditLedger(str(tmp_path), "audit.jsonl")
    first = ledger.append("source_validation", {"source_id": "src-1"})
    second = ledger.append("signal_review", {"signal_id": "sig-1"})

    reloaded = ci.AppendOnlyJsonlAuditLedger(str(tmp_path), "audit.jsonl")
    assert [record.record_hash for record in reloaded.records] == [
        first.record_hash,
        second.record_hash,
    ]
    assert reloaded.verify()

    path = tmp_path / "audit.jsonl"
    lines = path.read_text(encoding="utf-8").splitlines()
    tampered = json.loads(lines[0])
    tampered["payload_hash"] = "0" * 64
    lines[0] = json.dumps(tampered, sort_keys=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")

    assert not reloaded.verify()


def test_signal_adapter_modes_reject_log_or_retain_missing_provenance(tmp_path):
    raw_signal = {
        "signal_id": "raw-missing-provenance",
        "symbol": "EURUSD",
        "direction": "BUY",
        "confidence": 0.82,
        "source": "unattested_strategy",
        "thesis": "strategy claims a licensed signal but provides no source envelope",
    }
    adapter = ci.SignalIntelligenceAdapter()
    package = adapter.adapt(raw_signal)
    engine = ci.SignalCounterintelligenceEngine(
        audit_ledger=ci.AppendOnlyJsonlAuditLedger(str(tmp_path), "modes.jsonl")
    )

    hard = engine.review_signal(
        package.signal,
        package.sources,
        package.evidence,
        mode=ci.CounterintelligenceMode.HARD_GATE,
    )
    advisory = engine.review_signal(
        package.signal,
        package.sources,
        package.evidence,
        mode=ci.CounterintelligenceMode.ADVISORY,
    )
    research = engine.review_signal(
        package.signal,
        package.sources,
        package.evidence,
        mode=ci.CounterintelligenceMode.RESEARCH_ONLY,
    )

    assert hard.decision == ci.IntelligenceDecision.REJECT
    assert not hard.execution_allowed
    assert advisory.decision == ci.IntelligenceDecision.QUARANTINE
    assert advisory.execution_allowed
    assert research.decision == ci.IntelligenceDecision.QUARANTINE
    assert not research.execution_allowed
    assert engine.audit_ledger.verify()


def test_validate_intelligence_metadata_requires_accept_digest_lineage_and_governance_id():
    valid = {
        "decision": "accept",
        "governance_decision": "accept",
        "audit_digest": "abc",
        "source_lineage_hashes": ["lineage"],
        "governance_decision_id": "gov-1",
        "execution_allowed": True,
    }

    assert ci.validate_intelligence_metadata({"intelligence": valid}) == (True, [])

    ok, reasons = ci.validate_intelligence_metadata({"intelligence": {"decision": "reject"}})
    assert not ok
    assert any("audit_digest" in reason for reason in reasons)
    assert any("source lineage" in reason for reason in reasons)


def test_directorate_rejects_kill_switch_and_invalid_model_artifact(tmp_path):
    directorate = ci.AlphaAlgoIntelligenceDirectorate(
        audit_ledger=ci.AppendOnlyJsonlAuditLedger(str(tmp_path), "directorate.jsonl")
    )
    mission = ci.MissionRequirement(
        mission_id="mission-kill",
        tradable_question="Can legal evidence support a trade?",
        edge_hypothesis="Only governed legal data can pass.",
        objective_functions=["compliance"],
        risk_budget=0.01,
        allowed_assets=["EURUSD"],
    )
    sources = [_source("src-1", ci.SourceLicenseStatus.PUBLIC), _source("src-2", ci.SourceLicenseStatus.LICENSED)]
    evidence = [_evidence("ev-1", "src-1"), _evidence("ev-2", "src-2")]
    signal = _signal(["src-1", "src-2"], ["ev-1", "ev-2"], confidence=0.72)

    killed = directorate.evaluate(mission, signal, sources, evidence, kill_switch_active=True)
    assert killed.governance_decision == ci.IntelligenceDecision.REJECT
    assert any("kill switch active" in reason for reason in killed.governance_report.reasons)

    valid_artifact = directorate.model_registry.sign("model", b"bytes", "approver", True)
    invalid_artifact = ci.SignedModelArtifact(
        artifact_id="bad",
        model_name=valid_artifact.model_name,
        model_digest=valid_artifact.model_digest,
        signer=valid_artifact.signer,
        signature="bad",
        created_at=valid_artifact.created_at,
        read_only=True,
        approved_for_production=True,
    )
    invalid_model = directorate.evaluate(
        mission,
        signal,
        sources,
        evidence,
        production_model_artifact=invalid_artifact,
    )
    assert invalid_model.governance_decision == ci.IntelligenceDecision.REJECT
    assert any("invalid or unapproved model signature" in reason for reason in invalid_model.governance_report.reasons)


def test_data_passport_sidecar_attaches_signature_and_rejects_expired_license(tmp_path):
    ledger = ci.ComplianceLicenseLedger(str(tmp_path), "licenses.jsonl")
    source = _source("passport-src", ci.SourceLicenseStatus.LICENSED)
    ledger.register_license(
        source=source.name,
        license_status=source.license_status,
        permission_basis=source.permission_basis,
        data_vendor=source.data_vendor,
        expires_at=time.time() + 60,
        license_id=source.license_id,
    )
    sidecar = ci.DataPassportSidecarProxy("passport-secret", ledger)

    wrapped = sidecar.attach_passport({"payload": "bar"}, source)
    accepted = sidecar.verify_message(wrapped)

    assert accepted.accepted
    assert wrapped["data_passport"]["signature"]
    assert accepted.lineage_hash == source.lineage_hash()

    ledger.revoke_license(source.license_id, "unit-test revocation")
    rejected = sidecar.verify_message(wrapped)
    assert not rejected.accepted
    assert any("revoked" in reason for reason in rejected.reasons)
    assert ledger.verify()


def test_compliance_ledger_auto_expires_license(tmp_path):
    ledger = ci.ComplianceLicenseLedger(str(tmp_path), "licenses.jsonl")
    source = _source("expired-src", ci.SourceLicenseStatus.LICENSED)
    ledger.register_license(
        source=source.name,
        license_status=source.license_status,
        permission_basis=source.permission_basis,
        data_vendor=source.data_vendor,
        expires_at=time.time() - 1,
        license_id=source.license_id,
    )

    active, reasons = ledger.is_license_active(source.license_id)

    assert not active
    assert any("expired" in reason for reason in reasons)
    assert ledger.licenses[source.license_id].status == ci.LicenseLedgerStatus.EXPIRED
    assert ledger.verify()


def test_zero_trust_zone_policy_and_rbac_block_bad_access():
    zone_policy = ci.ZeroTrustZonePolicy()
    security = ci.CompartmentalizedSecurityModel()

    research_promote = zone_policy.evaluate(
        ci.IntelligenceRole.RESEARCH_ANALYST,
        ci.IntelligenceZone.RESEARCH,
        "promote model to production",
    )
    red_team_live = zone_policy.evaluate(
        ci.IntelligenceRole.RED_TEAM,
        ci.IntelligenceZone.PRODUCTION,
        "read live signal stream",
    )
    operator_modify = security.validate_access(
        ci.IntelligenceRole.EXECUTION_OPERATOR,
        ci.IntelligenceCompartment.PRODUCTION_MODEL,
        "modify production model",
        signed_model_artifact=True,
    )

    assert not research_promote.accepted
    assert not red_team_live.accepted
    assert not operator_modify.accepted


def test_model_promotion_chain_requires_staging_and_validation_counter_signatures(tmp_path):
    ledger = ci.AppendOnlyJsonlAuditLedger(str(tmp_path), "promotion.jsonl")
    registry = ci.ModelArtifactRegistry("promotion-secret")
    chain = ci.ModelPromotionChain(registry=registry, audit_ledger=ledger)
    artifact = chain.submit_research_artifact(
        "edge-model",
        b"weights",
        "researcher",
        {"sources": ["licensed"], "manifest_hash": "manifest"},
        "licensed edge hypothesis",
    )
    checklist = ci.PromotionGateChecklist(
        hypothesis_written=True,
        data_manifest_attached=True,
        leakage_test_passed=True,
        walk_forward_passed=True,
        transaction_costs_included=True,
        slippage_modeled=True,
        capacity_estimated=True,
        regime_behavior_known=True,
        risk_impact_approved=True,
        paper_trading_passed=True,
    )
    ci_report = ci.SignalCounterintelligenceReport(
        "sig-promo",
        ci.IntelligenceDecision.ACCEPT,
        True,
        [],
        [],
        1.0,
        1.0,
        [],
        "ci-digest",
        ci.CounterintelligenceMode.HARD_GATE,
        True,
    )

    staging = chain.run_staging_gate(artifact, checklist, ci_report)
    same_author = chain.validation_officer_approve(artifact, checklist, "researcher", "researcher")
    approval = chain.validation_officer_approve(artifact, checklist, "validation-officer", "researcher")

    assert staging.accepted
    assert not same_author.accepted
    assert approval.accepted
    assert registry.verify(artifact)
    assert ledger.verify()


def test_live_signal_gauntlet_blocks_unproven_or_crowded_signal():
    engine = ci.SignalCounterintelligenceEngine()
    source = _source("src-live", ci.SourceLicenseStatus.PUBLIC)
    evidence = [_evidence("ev-live", "src-live")]
    signal = _signal(
        ["src-live"],
        ["ev-live"],
        thesis="legal live edge with fragile validation",
        confidence=0.70,
        features={
            "validation_sharpe": 1.0,
            "train_sharpe": 1.1,
            "sample_size": 240,
            "lookahead_bias_detected": False,
            "adversarial_sharpe_drop": 0.25,
            "crowding_edge_erosion": 0.60,
        },
    )
    signal.proposed_action = "buy"

    report = engine.review_signal(signal, [source], evidence)
    vectors = {finding.vector for finding in report.findings}

    assert report.decision == ci.IntelligenceDecision.REJECT
    assert ci.SignalAttackVector.ADVERSARIAL_MARKET_BEHAVIOR in vectors
    assert ci.SignalAttackVector.CROWDING_CAPACITY_RISK in vectors
    assert ci.SignalAttackVector.PROMOTION_GATE_FAILURE in vectors


def test_feedback_monitor_quarantines_decay_and_records_postmortem(tmp_path):
    monitor = ci.SignalFeedbackMonitor(ci.AppendOnlyJsonlAuditLedger(str(tmp_path), "feedback.jsonl"))

    health = monitor.evaluate_signal_health(
        "sig-decay",
        staging_test_sharpe=2.0,
        out_of_sample_sharpe=0.8,
        pnl_attribution=-0.03,
        risk_attribution=0.02,
        regime="trend_chop",
    )
    postmortem = monitor.record_kill_post_mortem(
        "sig-decay",
        "decay quarantine",
        ["add stronger broker replay stress"],
    )

    assert health.status == ci.IntelligenceDecision.QUARANTINE
    assert health.decay_detected
    assert postmortem.record_hash
    assert monitor.audit_ledger.verify()
