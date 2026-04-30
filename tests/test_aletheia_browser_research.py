#!/usr/bin/env python3
"""Tests for AlphaAlgo's clean-room browser/Aletheia research harness."""

import importlib
import time
from pathlib import Path

ab = importlib.import_module("trading_bot.core.aletheia_browser_research")
ci = importlib.import_module("trading_bot.core.signal_counterintelligence")


def _engine(tmp_path):
    return ab.AlphaAletheiaBrowserResearchEngine(
        audit_ledger=ci.AppendOnlyJsonlAuditLedger(str(tmp_path), "aletheia_browser.jsonl")
    )


def _observation(engine, url="https://example.com/filing", source_name="Example Filing"):
    return engine.observation_from_page(
        url=url,
        title="Public filing",
        extracted_text="Revenue guidance increased and liquidity conditions improved.",
        facts=["revenue guidance increased", "liquidity conditions improved"],
        source_name=source_name,
        license_status=ci.SourceLicenseStatus.PUBLIC,
    )


def test_browser_planner_rejects_out_of_scope_domains_and_handoffs_sensitive_tasks():
    planner = ab.AlphaAlgoBrowserUsePlanner()

    plan = planner.plan(
        "log in to broker and place trade",
        ["https://unapproved.example/order"],
        ["example.com"],
    )

    assert not plan.accepted
    assert any("outside allowed domains" in reason for reason in plan.rejected_reasons)
    assert plan.actions[-1].requires_human_confirmation
    assert plan.actions[-1].risk_level == "high"


def test_aletheia_browser_engine_accepts_cited_public_evidence(tmp_path):
    engine = _engine(tmp_path)
    observations = [
        _observation(engine, "https://example.com/filing", "Example Filing"),
        _observation(engine, "https://example.org/macro", "Example Macro"),
    ]

    report = engine.run_research(
        "Does public evidence support an improving liquidity thesis?",
        ["https://example.com/filing"],
        ["example.com"],
        observations,
    )

    assert report.decision == ci.IntelligenceDecision.ACCEPT
    assert report.accepted_claims
    assert report.source_lineage_hashes
    assert report.audit_digest
    assert report.confidence > 0
    assert engine.audit_ledger.verify()


def test_aletheia_verifier_rejects_uncited_and_mnpi_claims():
    verifier = ab.AlphaAletheiaVerifier()
    claim = ab.AletheiaClaim(
        "claim-1",
        "confidential leaked earnings prove the trade",
        [],
        0.95,
    )

    issues = verifier.verify([claim], [])

    assert any(issue.severity == "critical" for issue in issues)
    assert any("no citation" in issue.description for issue in issues)
    assert verifier.revise([claim], issues) == []


def test_browser_research_rejects_private_source_even_with_claims(tmp_path):
    engine = _engine(tmp_path)
    observation = engine.observation_from_page(
        url="https://example.com/private-chat",
        title="Private channel",
        extracted_text="A private channel says liquidity improved.",
        facts=["liquidity improved"],
        source_name="Private Channel",
        license_status=ci.SourceLicenseStatus.PRIVATE,
        permission_basis="",
        license_name="",
    )

    report = engine.run_research(
        "Does the source pass?",
        ["https://example.com/private-chat"],
        ["example.com"],
        [observation],
    )

    assert report.decision == ci.IntelligenceDecision.REJECT
    assert any("forbidden source license status" in reason for reason in report.blocked_reasons)


def test_browser_observation_can_carry_failed_data_passport(tmp_path):
    ledger = ci.ComplianceLicenseLedger(str(tmp_path), "licenses.jsonl")
    sidecar = ci.DataPassportSidecarProxy("unit-secret", ledger)
    engine = ab.AlphaAletheiaBrowserResearchEngine(
        audit_ledger=ci.AppendOnlyJsonlAuditLedger(str(tmp_path), "browser.jsonl"),
        passport_proxy=sidecar,
    )
    source = ci.DataSourceProvenance(
        source_id="src-expired",
        name="Expired Source",
        category=ci.DataSourceCategory.NEWS_FILINGS,
        license_status=ci.SourceLicenseStatus.LICENSED,
        license_name="expired license",
        permission_basis="expired",
        collected_at=time.time(),
        observed_at=time.time(),
        provenance_chain=["unit-test"],
        compliance_score=0.95,
        reliability_score=0.8,
        license_expires_at=time.time() - 1,
    )
    wrapped = sidecar.attach_passport({"payload": "x"}, source)
    observation = engine.observation_from_page(
        url="https://example.com/expired",
        title="Expired source",
        extracted_text="liquidity improved",
        facts=["liquidity improved"],
        source_name="Expired Source",
        license_status=ci.SourceLicenseStatus.LICENSED,
        passport_message=wrapped,
    )

    report = engine.run_research(
        "Does expired source pass?",
        ["https://example.com/expired"],
        ["example.com"],
        [observation],
    )

    assert report.decision == ci.IntelligenceDecision.REJECT
    assert any("not registered" in reason or "expired" in reason for reason in report.blocked_reasons)
