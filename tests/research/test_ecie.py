import pytest
import asyncio
from datetime import datetime

from trading_bot.research.research_os import ResearchWorkspace
from trading_bot.research.ecie.models import (
    SourceType,
    CapabilityCategory,
    TrustLevel,
    LicenseStatus,
    PromotionStage,
    ExternalCandidate
)
from trading_bot.research.ecie.scouts import (
    GitHubScoutAdapter,
    ArxivScoutAdapter,
    HuggingFaceScoutAdapter
)
from trading_bot.research.ecie.sandbox import LocalRestrictedExecutor
from trading_bot.research.ecie.pipeline import ECIEPipeline
from trading_bot.research.ecie.governance import (
    GovernanceGate,
    RolloutManager,
    RollbackManager
)


@pytest.fixture
def workspace():
    """Initializes the central Quantitative Research Workspace."""
    return ResearchWorkspace()


@pytest.fixture
def pipeline():
    """Initializes the ECIE Refinery Pipeline."""
    return ECIEPipeline()


@pytest.fixture
def governance(workspace):
    """Initializes the ECIE Governance Gate with Workspace integration."""
    return GovernanceGate(workspace)


@pytest.fixture
def sample_candidate():
    """Generates a high-quality candidate repository structure."""
    return ExternalCandidate(
        source_type=SourceType.GITHUB,
        name="QuantTrader/SlippageSimulator",
        url="https://github.com/QuantTrader/SlippageSimulator",
        version_id="abc123commit",
        author="QuantTrader",
        description="Smart order routing and transaction cost slippage models.",
        readme_content="SlippageSimulator is built for high-frequency execution analysis. "
                       "Features: smart order routing, slippage model, order book simulation. "
                       "Licensed under MIT. Fully covered by unit tests.",
        license_name="MIT",
        stars=450,
        forks=80,
        metadata={
            "has_tests": True,
            "has_docs": True,
            "pushed_at": datetime.now().isoformat() + "Z"
        }
    )


@pytest.fixture
def bad_candidate():
    """Generates an unsafe / non-compliant candidate structure."""
    return ExternalCandidate(
        source_type=SourceType.GITHUB,
        name="UnsafeGroup/BackdoorExec",
        url="https://github.com/UnsafeGroup/BackdoorExec",
        version_id="bad666commit",
        author="UnsafeGroup",
        description="Fast quantitative execution package.",
        readme_content="Executes order flow with raw shell wrappers.",
        license_name="GPL-3.0",  # Copyleft GPL is strictly forbidden
        stars=1000,              # High stars to prove popularity cannot dominate scoring
        forks=200,
        metadata={
            "has_tests": False,   # Low maturity triggers rejection
            "has_docs": True,
            "pushed_at": datetime.now().isoformat() + "Z"
        }
    )


@pytest.mark.asyncio
async def test_scout_adapters_and_classification(pipeline):
    """Verifies that adapters fetch candidates correctly and classify their domain category."""
    github_scout = GitHubScoutAdapter()
    arxiv_scout = ArxivScoutAdapter()
    hf_scout = HuggingFaceScoutAdapter()

    # Query candidates
    candidates_gh = await github_scout.discover_candidates()
    candidates_arxiv = await arxiv_scout.discover_candidates()
    candidates_hf = await hf_scout.discover_candidates()

    assert len(candidates_gh) >= 2
    assert len(candidates_arxiv) >= 1
    assert len(candidates_hf) >= 1

    # Classify domains
    cat_gh = pipeline.classify_candidate(candidates_gh[0])
    assert cat_gh in [CapabilityCategory.RISK, CapabilityCategory.EXECUTION]

    cat_arxiv = pipeline.classify_candidate(candidates_arxiv[0])
    assert cat_arxiv == CapabilityCategory.PORTFOLIO


def test_trust_scoring_signals(pipeline, sample_candidate, bad_candidate):
    """Verifies that the trust scorer implements multi-signal scoring without star-dominance."""
    # High quality candidate
    report_good = pipeline.assess_trust_score(sample_candidate)
    assert report_good.is_acceptable is True
    assert report_good.trust_level in [TrustLevel.MEDIUM, TrustLevel.HIGH]
    assert report_good.overall_score >= 70.0

    # Low maturity but highly popular candidate (provenance / test hygiene check)
    report_bad = pipeline.assess_trust_score(bad_candidate)
    assert report_bad.is_acceptable is False  # Rejected because has_tests is False
    assert report_bad.trust_level in [TrustLevel.LOW, TrustLevel.ZERO]


def test_security_scan_ast_analysis(pipeline):
    """Verifies that AST scanning correctly flags secrets, eval/exec calls, and unsafe patterns."""
    # Secure code sample
    clean_code = [
        "def calculate_spread(ask, bid):\n"
        "    return ask - bid\n"
    ]
    report_clean = pipeline.perform_security_scan(None, clean_code)
    assert report_clean.is_secure is True
    assert len(report_clean.secrets_found) == 0

    # Unsafe code samples containing secrets, eval, and system execution
    unsafe_code = [
        "api_key = 'sec_token_999888'\n"
        "def run_command(cmd):\n"
        "    eval('print(\"Evaluating...\")')\n"
        "    import os\n"
        "    os.system('rm -rf /')\n"
    ]
    report_unsafe = pipeline.perform_security_scan(None, unsafe_code)
    assert report_unsafe.is_secure is False
    assert len(report_unsafe.secrets_found) > 0
    assert any("eval" in pat or "forbidden function" in pat for pat in report_unsafe.unsafe_patterns)
    assert report_unsafe.malicious_scripts_detected is True
    assert report_unsafe.filesystem_access_flagged is True


def test_license_compliance_analyzer(pipeline, sample_candidate, bad_candidate):
    """Verifies that copyleft GPL family licenses are perfectly banned while MIT/Apache pass."""
    # MIT compliance
    status_good = pipeline.analyze_license(sample_candidate)
    assert status_good == LicenseStatus.APPROVED

    # GPL compliance
    status_bad = pipeline.analyze_license(bad_candidate)
    assert status_bad == LicenseStatus.FORBIDDEN


def test_local_sandbox_executor():
    """Verifies that local restricted executor isolates execution and captures stdout/stderr."""
    sandbox = LocalRestrictedExecutor()

    # Safe executing python code payload
    safe_payload = (
        "print('Starting execution inside isolated sandbox')\n"
        "val = 42 * 2\n"
        "print(f'Execution output: {val}')\n"
    )

    success, report = sandbox.run_code(safe_payload)
    assert success is True
    assert "Execution output: 84" in report["output_stdout"]
    assert report["exception_raised"] is None

    # Payload with syntax error
    bad_payload = "print(invalid_var"
    success_bad, report_bad = sandbox.run_code(bad_payload)
    assert success_bad is False
    assert report_bad["exception_raised"] is not None


def test_capability_distillation_and_weakness_inversion(pipeline, sample_candidate):
    """Verifies that pattern extraction filters wraps and applies Weakness Inversion rules."""
    raw_code = [
        "import os\n"
        "def execute_slippage_calc(order_size, liquidity):\n"
        "    # Missing error checks and assertions\n"
        "    return order_size / liquidity\n"
    ]

    # Distill
    pattern = pipeline.distill_pattern(sample_candidate, CapabilityCategory.EXECUTION, raw_code)
    assert "import os" not in pattern.extracted_logic
    assert "execute_slippage_calc" in pattern.extracted_logic
    assert "Missing error handling" in pattern.original_weaknesses[0]

    # Compile Skill
    skill = pipeline.compile_skill(pattern)
    assert "Skill_" in skill.name
    assert "ValueError" in skill.code  # Applied inversion pre-condition checks
    assert "try:" in skill.code         # Applied exception wrapper


def test_governance_rollout_and_automatic_rollback(governance, pipeline, sample_candidate, bad_candidate):
    """Verifies the complete governed rollout sequence, human-in-the-loop trigger, and rollback fail-closed control."""
    # 1. Propose high quality skill
    code_sample = ["def slippage_calc(x): return x * 0.98"]
    trust = pipeline.assess_trust_score(sample_candidate)
    security = pipeline.perform_security_scan(sample_candidate, code_sample)
    license_status = pipeline.analyze_license(sample_candidate)

    pattern = pipeline.distill_pattern(sample_candidate, CapabilityCategory.EXECUTION, code_sample)
    skill = pipeline.compile_skill(pattern)

    # Submit
    proposal = governance.submit_proposal(
        skill, sample_candidate.url, sample_candidate.version_id,
        sample_candidate.license_name, trust, security, license_status
    )

    assert proposal.stage == PromotionStage.SANDBOX

    # Evaluate - requires Human-in-the-Loop approval because category is Execution (High risk)
    promoted, msg = governance.evaluate_promotion(proposal.proposal_id)
    assert promoted is False
    assert "HUMAN_APPROVAL_REQUIRED" in msg

    # Trigger Human Approval sign-off
    signed = governance.sign_off_human_approval(proposal.proposal_id, "ChiefRiskOfficer")
    assert signed is True
    assert proposal.stage == PromotionStage.SHADOW

    # Rollout sequence
    rollout = RolloutManager(governance)
    assert rollout.transition_stage(proposal.proposal_id, PromotionStage.CANARY) is True
    assert rollout.transition_stage(proposal.proposal_id, PromotionStage.LIMITED_PRODUCTION) is True

    # Automatic Rollback trigger on anomaly/breach
    rollback = RollbackManager(rollout)
    success = rollback.trigger_automatic_rollback(proposal.proposal_id, "Latency jitter exceeded SLA boundaries")

    assert success is True
    assert proposal.stage == PromotionStage.SANDBOX
    assert proposal.is_active is False  # Disabled execution privileges
