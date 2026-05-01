"""AI system reverse engineering and creator intelligence engine.

This module turns observed workflows, outputs, and claims into structured
capability intelligence. It is intentionally skeptical: claims are not treated
as capability until backed by tools, data flow, measurable outputs, and tests.

The engine is a capability distillation layer, not a copier. It can create
research proposals and sandbox experiments, but it must not directly modify
live trading, execution, broker, risk, or production strategy code.
"""

from __future__ import annotations

import hashlib
import json
import math
from collections import Counter, defaultdict
from dataclasses import asdict, dataclass, field, is_dataclass
from enum import Enum
from typing import Any, Dict, Iterable, List, Mapping, Optional, Sequence, Tuple


class SourceType(str, Enum):
    """Sources the engine can analyze."""

    WORKFLOW = "workflow"
    OUTPUT = "output"
    CLAIM = "claim"
    QUANT = "quant"
    TRADER = "trader"
    BOOK = "book"
    AI_SYSTEM = "ai_system"
    ALGORITHM = "algorithm"
    PAPER = "paper"
    COMPETITOR = "competitor"
    UNKNOWN = "unknown"


class CapabilityClass(str, Enum):
    """Capability classification labels."""

    REAL_CAPABILITY = "real_capability"
    USEFUL_BUT_OVERMARKETED = "useful_but_overmarketed"
    FAKE_HYPE = "fake_hype"
    DANGEROUS_IDEA = "dangerous_idea"
    RESEARCH_SEED = "research_seed"
    REUSABLE_COMPONENT = "reusable_component"
    GHOST_CAPABILITY = "ghost_capability"
    HONEYPOT_PATTERN = "honeypot_pattern"
    SCALING_CLIFF = "scaling_cliff"
    LOW_VALUE_IDEA = "low_value_idea"


class ProfitabilityVerdict(str, Enum):
    """Profitability test verdict."""

    PASSED = "passed"
    FAILED = "failed"
    NEEDS_MORE_DATA = "needs_more_data"
    REJECTED = "rejected"


class ReverseEngineeringDecision(str, Enum):
    """Governed decision for an extracted idea."""

    REJECT = "reject"
    QUARANTINE = "quarantine"
    SANDBOX_ONLY = "sandbox_only"
    BACKTEST_READY = "backtest_ready"
    PAPER_REVIEW_READY = "paper_review_ready"
    RESEARCH_MEMORY_ONLY = "research_memory_only"


@dataclass(frozen=True)
class SourceArtifact:
    """Structured artifact to reverse engineer."""

    artifact_id: str
    source_type: SourceType
    title: str
    claims: List[str] = field(default_factory=list)
    outputs: List[Dict[str, Any]] = field(default_factory=list)
    workflow_steps: List[str] = field(default_factory=list)
    tools: List[str] = field(default_factory=list)
    architecture_hints: List[str] = field(default_factory=list)
    data_flow: List[str] = field(default_factory=list)
    metrics: Dict[str, float] = field(default_factory=dict)
    market_tests: List[Dict[str, float]] = field(default_factory=list)
    capital_tests: List[Dict[str, float]] = field(default_factory=list)
    marketed_features: List[str] = field(default_factory=list)
    observed_features: List[str] = field(default_factory=list)
    evidence_items: List[Dict[str, Any]] = field(default_factory=list)
    urls: List[str] = field(default_factory=list)
    screenshots: List[str] = field(default_factory=list)
    docs: List[str] = field(default_factory=list)
    reasoning_traces: List[str] = field(default_factory=list)
    failure_behavior: List[str] = field(default_factory=list)
    user_interaction_patterns: List[str] = field(default_factory=list)
    pricing_model: str = ""
    deployment_model: str = ""
    security_posture: str = ""
    latency_ms: Optional[float] = None
    source: str = "unknown"
    tags: List[str] = field(default_factory=list)

    @classmethod
    def from_mapping(cls, payload: Mapping[str, Any]) -> "SourceArtifact":
        data = dict(payload)
        data.setdefault("artifact_id", _stable_hash(data)[:16])
        data["source_type"] = SourceType(data.get("source_type", SourceType.UNKNOWN.value))
        allowed = set(cls.__dataclass_fields__.keys())
        data = {key: value for key, value in data.items() if key in allowed}
        return cls(**data)


@dataclass(frozen=True)
class StructuredClaim:
    """A vague claim converted into something testable."""

    claim_id: str
    artifact_id: str
    claim: str
    claim_type: str
    claimed_value: str
    evidence_present: bool
    evidence_type: List[str]
    testability: str
    risk_of_hype: str
    required_validation: List[str]
    inference_notes: List[str] = field(default_factory=list)


@dataclass(frozen=True)
class HypeDetectionReport:
    """Ruthless filter for marketing-heavy trading AI claims."""

    hype_score: float
    technical_substance_score: float
    evidence_score: float
    verdict: str
    red_flags: List[str]
    reasons: List[str]


@dataclass(frozen=True)
class ReusableComponent:
    """Generalizable component inferred from a source."""

    source_artifact_id: str
    reusable_component: str
    description: str
    alphaalgo_application: str
    estimated_value: str
    implementation_difficulty: str
    requires_live_trading: bool = False


@dataclass(frozen=True)
class CapabilityGraphNode:
    """Node in the claim/evidence/mechanism/test graph."""

    node_id: str
    node_type: str
    label: str
    properties: Dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class CapabilityGraphEdge:
    """Typed edge in the distillation graph."""

    subject: str
    predicate: str
    object: str
    confidence: float = 0.5


@dataclass(frozen=True)
class CapabilityGraph:
    """Claim -> evidence -> mechanism -> validation -> AlphaAlgo module graph."""

    artifact_id: str
    nodes: List[CapabilityGraphNode]
    edges: List[CapabilityGraphEdge]


@dataclass(frozen=True)
class SandboxExperiment:
    """A research-only experiment generated from a reusable pattern."""

    experiment_id: str
    source_artifact_id: str
    hypothesis: str
    dataset: str
    baseline: str
    metrics: List[str]
    failure_conditions: List[str]
    promotion_rule: str
    target_directory: str = "sandbox/generated_experiments"
    live_trading_allowed: bool = False


@dataclass(frozen=True)
class PromotionDecisionRecord:
    """Governance decision for an observed idea or extracted pattern."""

    idea_id: str
    decision: ReverseEngineeringDecision
    reason: str
    possible_salvage: Optional[str]
    required_next_steps: List[str]
    live_code_modification_allowed: bool = False


@dataclass(frozen=True)
class ResearchMemoryRecord:
    """Anti-repeat memory for failed or validated external ideas."""

    pattern: str
    status: str
    tested_on: List[str]
    reason: str
    do_not_retry_until: str
    related_patterns: List[str]


@dataclass(frozen=True)
class DecomposedSystem:
    """Observed system decomposition."""

    artifact_id: str
    tools_used: List[str]
    architecture_pattern: str
    data_flow: List[str]
    workflow: List[str]
    claims: List[str]
    outputs: List[Dict[str, Any]]


@dataclass(frozen=True)
class ExtractedPattern:
    """Reusable pattern extracted from a source."""

    pattern_id: str
    name: str
    source_artifact_id: str
    reusable_components: List[str]
    workflow: List[str]
    data_flow: List[str]
    required_tests: List[str]
    confidence: float
    rejection_risks: List[str] = field(default_factory=list)


@dataclass(frozen=True)
class ProfitabilityTestResult:
    """Result of testing a pattern or artifact for profitability."""

    target_id: str
    verdict: ProfitabilityVerdict
    cost_adjusted_edge: float
    sharpe_delta: float
    sample_size: int
    max_drawdown: float
    reasons: List[str]


@dataclass(frozen=True)
class ScalingCliff:
    """Capital or compute point where a pattern degrades or inverts."""

    artifact_id: str
    dimension: str
    cliff_value: float
    before_metric: float
    after_metric: float
    reason: str


@dataclass(frozen=True)
class ReverseEngineeringReport:
    """Complete reverse engineering output."""

    artifact_id: str
    decomposition: DecomposedSystem
    structured_claims: List[StructuredClaim]
    capability_graph: CapabilityGraph
    hype_report: HypeDetectionReport
    classifications: List[CapabilityClass]
    real_capabilities: List[str]
    fake_hype: List[str]
    reusable_components: List[str]
    reusable_component_records: List[ReusableComponent]
    useful_patterns: List[ExtractedPattern]
    sandbox_experiments: List[SandboxExperiment]
    promotion_decision: PromotionDecisionRecord
    rejected_ideas: List[str]
    ghost_capabilities: List[str]
    honeypot_patterns: List[str]
    scaling_cliffs: List[ScalingCliff]
    profitability_tests: List[ProfitabilityTestResult]


@dataclass(frozen=True)
class CreatorScanReport:
    """Aggregate creator intelligence report."""

    scanned_artifacts: int
    useful_patterns: List[ExtractedPattern]
    rejected_ideas: List[str]
    real_capabilities: List[str]
    fake_hype: List[str]
    ghost_capabilities: List[str]
    honeypot_patterns: List[str]
    scaling_cliffs: List[ScalingCliff]
    ranked_patterns: List[Tuple[str, float]]


class AISystemReverseEngineeringEngine:
    """Reverse engineer AI/trading systems from observed artifacts."""

    PROTECTED_CODE_AREAS = {
        "live_trading",
        "execution",
        "broker",
        "brokers",
        "risk",
        "risk_management",
        "validation/risk",
        "trading_bot/execution",
        "trading_bot/broker",
        "trading_bot/brokers",
        "trading_bot/risk",
        "trading_bot/risk_management",
        "trading_bot/strategies/live",
        "trading_bot/realtime_trading_core",
    }

    HYPE_TERMS = {
        "guaranteed",
        "risk-free",
        "risk free",
        "secret",
        "magic",
        "always wins",
        "never loses",
        "100%",
        "sentient",
        "god mode",
        "infinite alpha",
        "unlimited",
        "institutional",
        "smart money",
        "90% accuracy",
        "90% win",
    }
    HONEYPOT_TERMS = {
        "copy exact",
        "proprietary leak",
        "secret sauce",
        "front-run",
        "insider",
        "undetectable",
        "can't fail",
        "no drawdown",
    }
    DANGEROUS_TERMS = {
        "self-modifying live",
        "rewrite live",
        "auto deploy",
        "bypass risk",
        "bypass validation",
        "broker exploit",
        "insider data",
        "illegal data",
        "unreviewed production",
    }
    HYPE_RED_FLAGS = {
        "win rate without risk/reward",
        "profit without drawdown",
        "backtest without out-of-sample validation",
        "no transaction costs",
        "no slippage model",
        "no broker execution assumptions",
        "no sample size",
        "no benchmark comparison",
        "cherry-picked screenshots",
        "institutional language without methodology",
        "AI claims with no model architecture",
        "signals shown only after the move",
        "private Discord proof",
        "lifestyle marketing",
        "martingale/grid hidden behind AI",
    }
    TOOL_HINTS = {
        "backtest",
        "paper trading",
        "slippage model",
        "cost model",
        "order book",
        "feature store",
        "walk forward",
        "monte carlo",
        "risk gate",
        "validation gate",
        "knowledge graph",
        "claim graph",
        "optimizer",
        "simulator",
        "vector database",
        "pgvector",
        "faiss",
        "neo4j",
        "broker api",
    }

    def __init__(self, config: Optional[Mapping[str, Any]] = None) -> None:
        cfg = dict(config or {})
        self.min_sample_size = int(cfg.get("min_sample_size", 30))
        self.min_cost_adjusted_edge = float(cfg.get("min_cost_adjusted_edge", 0.0))
        self.min_sharpe_delta = float(cfg.get("min_sharpe_delta", 0.0))
        self.max_drawdown = float(cfg.get("max_drawdown", 0.25))
        self.artifacts: Dict[str, SourceArtifact] = {}
        self.reports: Dict[str, ReverseEngineeringReport] = {}
        self.research_memory: Dict[str, ResearchMemoryRecord] = {}

    def observe(self, artifact: SourceArtifact | Mapping[str, Any]) -> SourceArtifact:
        """Store a structured artifact for analysis."""

        parsed = artifact if isinstance(artifact, SourceArtifact) else SourceArtifact.from_mapping(artifact)
        self.artifacts[parsed.artifact_id] = parsed
        return parsed

    def source_intake(self, payload: Mapping[str, Any]) -> SourceArtifact:
        """Normalize an external URL/paper/repo/demo/tool artifact into research intake."""

        return self.observe(payload)

    def parse_evidence(self, artifact: SourceArtifact | Mapping[str, Any]) -> Dict[str, Any]:
        """Extract evidence signals without treating them as proof."""

        parsed = self.observe(artifact)
        evidence_types: List[str] = []
        if parsed.metrics:
            evidence_types.append("metrics")
        if parsed.market_tests:
            evidence_types.append("market_tests")
        if parsed.capital_tests:
            evidence_types.append("capacity_tests")
        if parsed.outputs:
            evidence_types.append("observable_outputs")
        if parsed.tools or parsed.architecture_hints:
            evidence_types.append("mechanism_hints")
        if parsed.evidence_items:
            evidence_types.append("external_evidence_items")
        if parsed.screenshots:
            evidence_types.append("screenshots")
        if parsed.docs or parsed.urls:
            evidence_types.append("docs_or_urls")

        return {
            "artifact_id": parsed.artifact_id,
            "claims": list(parsed.claims),
            "evidence_types": evidence_types,
            "metric_keys": sorted(parsed.metrics.keys()),
            "has_cost_model": self._has_cost_model(parsed),
            "has_slippage_model": self._has_slippage_model(parsed),
            "has_out_of_sample": self._has_out_of_sample(parsed),
            "has_benchmark": self._has_benchmark(parsed),
            "has_sample_size": self._has_sample_size(parsed),
            "is_inference_only": not bool(parsed.metrics or parsed.market_tests or parsed.evidence_items),
        }

    def extract_claims(self, artifact: SourceArtifact | Mapping[str, Any]) -> List[StructuredClaim]:
        """Convert vague marketing into explicit, testable claims."""

        parsed = self.observe(artifact)
        evidence = self.parse_evidence(parsed)
        claims: List[StructuredClaim] = []
        raw_claims = parsed.claims or parsed.marketed_features
        for index, claim in enumerate(raw_claims):
            claim_type = self._claim_type(claim)
            risk = self._claim_hype_risk(claim, parsed)
            required_validation = self._required_validation_for_claim(claim_type, claim)
            evidence_type = list(evidence["evidence_types"])
            evidence_present = bool(evidence_type and not evidence["is_inference_only"])
            testability = self._claim_testability(claim, claim_type, evidence_present)
            notes = []
            if not evidence_present:
                notes.append("No measurable evidence attached; treat as unverified inference.")
            if claim_type == "market_structure_detection" and "institutional" in claim.lower():
                notes.append("Institutional participation is not observable from ordinary OHLCV alone.")

            claims.append(
                StructuredClaim(
                    claim_id=f"claim-{parsed.artifact_id}-{index}",
                    artifact_id=parsed.artifact_id,
                    claim=claim,
                    claim_type=claim_type,
                    claimed_value=self._claimed_value(claim),
                    evidence_present=evidence_present,
                    evidence_type=evidence_type,
                    testability=testability,
                    risk_of_hype=risk,
                    required_validation=required_validation,
                    inference_notes=notes,
                )
            )
        return claims

    def decompose(self, artifact: SourceArtifact | Mapping[str, Any]) -> DecomposedSystem:
        parsed = self.observe(artifact)
        tools = sorted(set(parsed.tools) | self._infer_tools(parsed))
        architecture_pattern = self._infer_architecture(parsed, tools)
        data_flow = list(parsed.data_flow) or self._infer_data_flow(parsed, tools)
        workflow = list(parsed.workflow_steps) or self._infer_workflow(parsed, tools)
        return DecomposedSystem(
            artifact_id=parsed.artifact_id,
            tools_used=tools,
            architecture_pattern=architecture_pattern,
            data_flow=data_flow,
            workflow=workflow,
            claims=list(parsed.claims),
            outputs=list(parsed.outputs),
        )

    def classify(self, artifact: SourceArtifact, decomposition: DecomposedSystem) -> List[CapabilityClass]:
        labels: List[CapabilityClass] = []
        hype = self._hype_claims(artifact)
        honeypot = self._honeypot_claims(artifact)
        dangerous = self._dangerous_claims(artifact)
        ghost = self.detect_ghost_capabilities(artifact)
        scaling = self.detect_scaling_cliffs(artifact)
        has_tests = bool(artifact.metrics or artifact.market_tests or artifact.capital_tests)
        has_real_workflow = bool(decomposition.tools_used and decomposition.data_flow and decomposition.workflow)

        if has_real_workflow and has_tests and not honeypot:
            labels.append(CapabilityClass.REAL_CAPABILITY)
        if has_real_workflow and not honeypot:
            labels.append(CapabilityClass.REUSABLE_COMPONENT)
        if has_real_workflow and hype and has_tests and not honeypot:
            labels.append(CapabilityClass.USEFUL_BUT_OVERMARKETED)
        if hype and not has_tests:
            labels.append(CapabilityClass.FAKE_HYPE)
        if dangerous:
            labels.append(CapabilityClass.DANGEROUS_IDEA)
        if artifact.source_type == SourceType.PAPER and not has_tests:
            labels.append(CapabilityClass.RESEARCH_SEED)
        if ghost:
            labels.append(CapabilityClass.GHOST_CAPABILITY)
        if honeypot:
            labels.append(CapabilityClass.HONEYPOT_PATTERN)
        if scaling:
            labels.append(CapabilityClass.SCALING_CLIFF)
        if not has_real_workflow and not has_tests:
            labels.append(CapabilityClass.LOW_VALUE_IDEA)

        return list(dict.fromkeys(labels))

    def detect_hype(
        self,
        artifact: SourceArtifact | Mapping[str, Any],
        structured_claims: Optional[Sequence[StructuredClaim]] = None,
    ) -> HypeDetectionReport:
        """Score fake-hype risk from missing evidence and marketing red flags."""

        parsed = self.observe(artifact)
        structured_claims = list(structured_claims or self.extract_claims(parsed))
        text = self._artifact_text(parsed)
        red_flags: List[str] = []

        if ("win rate" in text or "accuracy" in text) and "risk_reward" not in parsed.metrics:
            red_flags.append("win rate without risk/reward")
        if any(word in text for word in {"profit", "profitable", "returns"}) and "max_drawdown" not in parsed.metrics:
            red_flags.append("profit without drawdown")
        if ("backtest" in text or parsed.market_tests) and not self._has_out_of_sample(parsed):
            red_flags.append("backtest without out-of-sample validation")
        if not self._has_cost_model(parsed):
            red_flags.append("no transaction costs")
        if not self._has_slippage_model(parsed):
            red_flags.append("no slippage model")
        if "broker" not in text and "execution" not in text:
            red_flags.append("no broker execution assumptions")
        if not self._has_sample_size(parsed):
            red_flags.append("no sample size")
        if not self._has_benchmark(parsed):
            red_flags.append("no benchmark comparison")
        if parsed.screenshots and not parsed.market_tests:
            red_flags.append("cherry-picked screenshots")
        if any(term in text for term in {"institutional", "smart money"}) and not parsed.architecture_hints:
            red_flags.append("institutional language without methodology")
        if "ai" in text and not any(
            term in text
            for term in {
                "model",
                "classifier",
                "forecaster",
                "embedding",
                "neural",
                "xgboost",
                "lstm",
                "transformer",
            }
        ):
            red_flags.append("AI claims with no model architecture")
        if "after the move" in text or "called it after" in text:
            red_flags.append("signals shown only after the move")
        if "discord" in text and not parsed.market_tests:
            red_flags.append("private Discord proof")
        if any(term in text for term in {"lamborghini", "luxury", "millionaire lifestyle"}):
            red_flags.append("lifestyle marketing")
        if "martingale" in text or "grid" in text:
            red_flags.append("martingale/grid hidden behind AI")

        red_flags.extend(flag for flag in self._hype_claims(parsed) if flag not in red_flags)
        red_flags = sorted(set(red_flags))

        evidence_score = self._evidence_score(parsed)
        technical_score = self._technical_substance_score(parsed)
        vague_claim_penalty = sum(1 for claim in structured_claims if claim.risk_of_hype == "high")
        hype_score = min(
            1.0,
            (len(red_flags) * 0.09)
            + (vague_claim_penalty * 0.08)
            + (0.25 if evidence_score < 0.2 else 0.0)
            + (0.15 if technical_score < 0.25 else 0.0),
        )

        if hype_score >= 0.70:
            verdict = "reject"
        elif hype_score >= 0.45:
            verdict = "quarantine"
        elif evidence_score >= 0.50 and technical_score >= 0.45:
            verdict = "sandbox_only"
        else:
            verdict = "research_seed"

        reasons = []
        if red_flags:
            reasons.append("red flags: " + "; ".join(red_flags[:6]))
        if evidence_score < 0.2:
            reasons.append("evidence score is too low for a high-trust claim")
        if technical_score < 0.25:
            reasons.append("technical mechanism is underspecified")

        return HypeDetectionReport(
            hype_score=round(hype_score, 4),
            technical_substance_score=round(technical_score, 4),
            evidence_score=round(evidence_score, 4),
            verdict=verdict,
            red_flags=red_flags,
            reasons=reasons or ["no major hype flags detected"],
        )

    def extract_patterns(
        self,
        artifact: SourceArtifact,
        decomposition: DecomposedSystem,
        classifications: Sequence[CapabilityClass],
    ) -> List[ExtractedPattern]:
        """Extract useful, reusable patterns and reject low-value bait."""

        blocked = {
            CapabilityClass.FAKE_HYPE,
            CapabilityClass.HONEYPOT_PATTERN,
            CapabilityClass.LOW_VALUE_IDEA,
        }
        if any(label in classifications for label in blocked):
            return []

        components = sorted(set(decomposition.tools_used + decomposition.data_flow))
        if not components:
            return []

        confidence = 0.35
        if CapabilityClass.REAL_CAPABILITY in classifications:
            confidence += 0.35
        if artifact.metrics:
            confidence += 0.15
        if artifact.market_tests:
            confidence += 0.10

        pattern = ExtractedPattern(
            pattern_id=f"pattern-{_stable_hash({'artifact': artifact.artifact_id, 'components': components})[:16]}",
            name=self._pattern_name(artifact, decomposition),
            source_artifact_id=artifact.artifact_id,
            reusable_components=components,
            workflow=list(decomposition.workflow),
            data_flow=list(decomposition.data_flow),
            required_tests=[
                "cost-adjusted backtest",
                "paper-trade validation",
                "scaling cliff check",
                "honeypot/adversarial review",
            ],
            confidence=min(confidence, 0.95),
            rejection_risks=self._pattern_risks(artifact, classifications),
        )
        return [pattern]

    def build_capability_graph(
        self,
        artifact: SourceArtifact,
        structured_claims: Sequence[StructuredClaim],
        decomposition: DecomposedSystem,
    ) -> CapabilityGraph:
        """Build Claim -> Evidence -> Mechanism -> Required Data -> Validation -> Module graph."""

        nodes: List[CapabilityGraphNode] = []
        edges: List[CapabilityGraphEdge] = []
        artifact_node = f"artifact:{artifact.artifact_id}"
        nodes.append(
            CapabilityGraphNode(
                node_id=artifact_node,
                node_type="ObservedSystem",
                label=artifact.title,
                properties={"source_type": artifact.source_type.value, "source": artifact.source},
            )
        )

        mechanism_node = f"mechanism:{artifact.artifact_id}:{decomposition.architecture_pattern}"
        nodes.append(
            CapabilityGraphNode(
                node_id=mechanism_node,
                node_type="Mechanism",
                label=decomposition.architecture_pattern,
                properties={"tools": list(decomposition.tools_used), "workflow": list(decomposition.workflow)},
            )
        )
        edges.append(CapabilityGraphEdge(artifact_node, "appears_to_use", mechanism_node, 0.55))

        evidence_summary = self.parse_evidence(artifact)
        evidence_node = f"evidence:{artifact.artifact_id}"
        nodes.append(
            CapabilityGraphNode(
                node_id=evidence_node,
                node_type="Evidence",
                label="observed evidence",
                properties=evidence_summary,
            )
        )
        edges.append(CapabilityGraphEdge(artifact_node, "has_evidence", evidence_node, self._evidence_score(artifact)))

        module_node = f"alphaalgo_module:{artifact.artifact_id}"
        nodes.append(
            CapabilityGraphNode(
                node_id=module_node,
                node_type="AlphaAlgoModule",
                label=self._alphaalgo_application(decomposition),
                properties={"research_only": True},
            )
        )

        for claim in structured_claims:
            claim_node = f"claim:{claim.claim_id}"
            validation_node = f"validation:{claim.claim_id}"
            required_data_node = f"data:{claim.claim_id}"
            nodes.extend(
                [
                    CapabilityGraphNode(
                        node_id=claim_node,
                        node_type="Claim",
                        label=claim.claim,
                        properties={
                            "claim_type": claim.claim_type,
                            "claimed_value": claim.claimed_value,
                            "risk_of_hype": claim.risk_of_hype,
                            "testability": claim.testability,
                        },
                    ),
                    CapabilityGraphNode(
                        node_id=required_data_node,
                        node_type="RequiredData",
                        label="required validation data",
                        properties={"evidence_type": list(claim.evidence_type)},
                    ),
                    CapabilityGraphNode(
                        node_id=validation_node,
                        node_type="ValidationTest",
                        label="; ".join(claim.required_validation[:3]),
                        properties={"required_validation": list(claim.required_validation)},
                    ),
                ]
            )
            edges.extend(
                [
                    CapabilityGraphEdge(artifact_node, "makes_claim", claim_node, 0.8),
                    CapabilityGraphEdge(claim_node, "supported_by", evidence_node, 0.65 if claim.evidence_present else 0.1),
                    CapabilityGraphEdge(claim_node, "explained_by", mechanism_node, 0.5),
                    CapabilityGraphEdge(claim_node, "requires_data", required_data_node, 0.75),
                    CapabilityGraphEdge(claim_node, "requires_validation", validation_node, 0.85),
                    CapabilityGraphEdge(validation_node, "feeds_research_module", module_node, 0.7),
                ]
            )

        return CapabilityGraph(artifact_id=artifact.artifact_id, nodes=nodes, edges=edges)

    def extract_reusable_components(
        self,
        artifact: SourceArtifact,
        decomposition: DecomposedSystem,
        patterns: Sequence[ExtractedPattern],
    ) -> List[ReusableComponent]:
        """Extract generalizable components without copying implementation."""

        components: List[ReusableComponent] = []
        component_names = sorted(set(decomposition.tools_used + decomposition.data_flow))
        for component in component_names:
            components.append(
                ReusableComponent(
                    source_artifact_id=artifact.artifact_id,
                    reusable_component=component,
                    description=f"Generalized {component} pattern inferred from observed workflow.",
                    alphaalgo_application=self._alphaalgo_application(decomposition),
                    estimated_value=self._estimated_component_value(component, artifact),
                    implementation_difficulty=self._implementation_difficulty(component),
                    requires_live_trading=False,
                )
            )

        for pattern in patterns:
            components.append(
                ReusableComponent(
                    source_artifact_id=artifact.artifact_id,
                    reusable_component=pattern.name,
                    description="Reusable workflow pattern extracted for sandbox testing, not direct copying.",
                    alphaalgo_application=self._alphaalgo_application(decomposition),
                    estimated_value="high" if pattern.confidence >= 0.75 else "medium",
                    implementation_difficulty="medium",
                    requires_live_trading=False,
                )
            )
        return components

    def generate_sandbox_experiments(
        self,
        artifact: SourceArtifact,
        structured_claims: Sequence[StructuredClaim],
        patterns: Sequence[ExtractedPattern],
    ) -> List[SandboxExperiment]:
        """Turn useful patterns into sandbox experiments, never production edits."""

        if not patterns:
            return []

        experiments: List[SandboxExperiment] = []
        primary_claim = structured_claims[0] if structured_claims else None
        for index, pattern in enumerate(patterns):
            hypothesis = (
                f"{primary_claim.claim} can improve AlphaAlgo decision quality after costs"
                if primary_claim
                else f"{pattern.name} improves AlphaAlgo decision quality after costs"
            )
            experiments.append(
                SandboxExperiment(
                    experiment_id=f"EXP_{_stable_hash({'pattern': pattern.pattern_id, 'artifact': artifact.artifact_id})[:12]}",
                    source_artifact_id=artifact.artifact_id,
                    hypothesis=hypothesis,
                    dataset=self._experiment_dataset(artifact),
                    baseline=self._experiment_baseline(artifact),
                    metrics=[
                        "profit factor",
                        "Sharpe",
                        "max drawdown",
                        "trade count",
                        "cost-adjusted expectancy",
                        "regime-specific performance",
                        "false positive signal rate",
                    ],
                    failure_conditions=[
                        "edge disappears after slippage",
                        "works only in one year or one regime",
                        "trade count below threshold",
                        "performance concentrated in a few trades",
                        "cannot beat baseline in walk-forward windows",
                    ],
                    promotion_rule="Must beat baseline in at least 70% of purged walk-forward windows before paper review.",
                )
            )
        return experiments

    def governance_gate(
        self,
        artifact: SourceArtifact,
        classifications: Sequence[CapabilityClass],
        hype_report: HypeDetectionReport,
        patterns: Sequence[ExtractedPattern],
        experiments: Sequence[SandboxExperiment],
        profitability_tests: Sequence[ProfitabilityTestResult],
    ) -> PromotionDecisionRecord:
        """Approve only research progression; never direct production modification."""

        idea_id = artifact.artifact_id
        hard_rejections = []
        if CapabilityClass.HONEYPOT_PATTERN in classifications:
            hard_rejections.append("honeypot or adversarial copy-bait pattern detected")
        if CapabilityClass.DANGEROUS_IDEA in classifications:
            hard_rejections.append("dangerous idea could create legal, security, or live execution risk")
        if hype_report.verdict == "reject":
            hard_rejections.append("hype score is too high for validation priority")
        if any(test.verdict == ProfitabilityVerdict.FAILED for test in profitability_tests):
            hard_rejections.append("profitability failed after costs or risk constraints")
        if self.check_anti_repeat(artifact.title):
            hard_rejections.append("similar pattern exists in failed research memory")

        if hard_rejections:
            return PromotionDecisionRecord(
                idea_id=idea_id,
                decision=ReverseEngineeringDecision.REJECT,
                reason="; ".join(hard_rejections),
                possible_salvage=self._possible_salvage(artifact, classifications),
                required_next_steps=["store rejection in research memory", "do not modify live code"],
            )

        if not patterns:
            return PromotionDecisionRecord(
                idea_id=idea_id,
                decision=ReverseEngineeringDecision.RESEARCH_MEMORY_ONLY,
                reason="no reusable pattern survived decomposition",
                possible_salvage="Revisit only if new measurable evidence or methodology appears.",
                required_next_steps=["store as low-priority research memory"],
            )

        if not experiments:
            return PromotionDecisionRecord(
                idea_id=idea_id,
                decision=ReverseEngineeringDecision.QUARANTINE,
                reason="pattern exists but no safe sandbox experiment could be generated",
                possible_salvage="Create a falsifiable sandbox hypothesis before any implementation.",
                required_next_steps=["compile sandbox experiment", "attach proof trace"],
            )

        passed_profitability = any(test.verdict == ProfitabilityVerdict.PASSED for test in profitability_tests)
        if passed_profitability and hype_report.hype_score < 0.45:
            return PromotionDecisionRecord(
                idea_id=idea_id,
                decision=ReverseEngineeringDecision.BACKTEST_READY,
                reason="pattern has reusable structure and initial profitability evidence",
                possible_salvage=None,
                required_next_steps=[
                    "run purged walk-forward validation",
                    "run Monte Carlo robustness",
                    "run transaction cost stress",
                    "route to paper/shadow review only after validation",
                ],
            )

        return PromotionDecisionRecord(
            idea_id=idea_id,
            decision=ReverseEngineeringDecision.SANDBOX_ONLY,
            reason="pattern is potentially useful but not validated enough for promotion",
            possible_salvage=None,
            required_next_steps=[
                "run sandbox experiment",
                "benchmark against simple baseline",
                "reject if cost-adjusted edge or robustness fails",
            ],
        )

    def remember_research_outcome(self, record: ResearchMemoryRecord) -> None:
        """Store anti-repeat memory for failed or validated ideas."""

        self.research_memory[_memory_key(record.pattern)] = record

    def check_anti_repeat(self, pattern: str) -> Optional[ResearchMemoryRecord]:
        """Return prior failed/blocked memory for similar pattern names."""

        direct = self.research_memory.get(_memory_key(pattern))
        if direct:
            return direct
        pattern_tokens = _token_set([pattern])
        for record in self.research_memory.values():
            related = [record.pattern] + list(record.related_patterns)
            if pattern_tokens and pattern_tokens.intersection(_token_set(related)):
                if record.status in {"rejected", "failed", "quarantined"}:
                    return record
        return None

    def enforce_research_boundary(self, target_path: str) -> None:
        """Raise if a generated idea tries to target protected live code."""

        normalized = target_path.replace("\\", "/").strip("/").lower()
        for protected in self.PROTECTED_CODE_AREAS:
            protected_norm = protected.replace("\\", "/").strip("/").lower()
            if normalized == protected_norm or normalized.startswith(protected_norm + "/"):
                raise PermissionError(
                    "Reverse Engineering Engine is research-only and cannot target "
                    f"protected live code path: {target_path}"
                )

    def test_profitability(
        self,
        target_id: str,
        market_tests: Sequence[Mapping[str, float]],
    ) -> ProfitabilityTestResult:
        """Evaluate profitability evidence without live execution."""

        sample_size = len(market_tests)
        if sample_size < self.min_sample_size:
            return ProfitabilityTestResult(
                target_id=target_id,
                verdict=ProfitabilityVerdict.NEEDS_MORE_DATA,
                cost_adjusted_edge=0.0,
                sharpe_delta=0.0,
                sample_size=sample_size,
                max_drawdown=0.0,
                reasons=[f"sample size {sample_size} < required {self.min_sample_size}"],
            )

        edges = [float(row.get("edge", row.get("pnl", 0.0))) - float(row.get("cost", 0.0)) for row in market_tests]
        sharpe_deltas = [float(row.get("sharpe_delta", 0.0)) for row in market_tests]
        drawdowns = [abs(float(row.get("drawdown", 0.0))) for row in market_tests]
        avg_edge = sum(edges) / max(sample_size, 1)
        avg_sharpe = sum(sharpe_deltas) / max(sample_size, 1)
        max_drawdown = max(drawdowns) if drawdowns else 0.0

        reasons: List[str] = []
        if avg_edge <= self.min_cost_adjusted_edge:
            reasons.append("cost-adjusted edge is not positive enough")
        if avg_sharpe <= self.min_sharpe_delta:
            reasons.append("Sharpe delta is not positive enough")
        if max_drawdown > self.max_drawdown:
            reasons.append("max drawdown exceeds threshold")

        verdict = ProfitabilityVerdict.PASSED if not reasons else ProfitabilityVerdict.FAILED
        return ProfitabilityTestResult(
            target_id=target_id,
            verdict=verdict,
            cost_adjusted_edge=avg_edge,
            sharpe_delta=avg_sharpe,
            sample_size=sample_size,
            max_drawdown=max_drawdown,
            reasons=reasons or ["profitability evidence passed configured thresholds"],
        )

    def detect_ghost_capabilities(self, artifact: SourceArtifact) -> List[str]:
        """Find features present in outputs but not marketed or claimed."""

        marketed = _token_set(artifact.marketed_features + artifact.claims)
        ghosts: List[str] = []
        observed = list(artifact.observed_features)
        for output in artifact.outputs:
            observed.extend(str(key) for key in output.keys())
            features = output.get("features")
            if isinstance(features, list):
                observed.extend(str(item) for item in features)

        for feature in sorted(set(observed)):
            tokens = _token_set([feature])
            if tokens and not tokens.intersection(marketed):
                ghosts.append(feature)
        return ghosts

    def detect_honeypot_patterns(self, artifact: SourceArtifact) -> List[str]:
        return self._honeypot_claims(artifact)

    def detect_scaling_cliffs(self, artifact: SourceArtifact) -> List[ScalingCliff]:
        """Detect capital/compute levels where performance inverts or collapses."""

        rows = sorted(artifact.capital_tests, key=lambda row: float(row.get("capital", row.get("compute", 0.0))))
        cliffs: List[ScalingCliff] = []
        for previous, current in zip(rows, rows[1:]):
            prev_value = float(previous.get("capital", previous.get("compute", 0.0)))
            current_value = float(current.get("capital", current.get("compute", 0.0)))
            prev_metric = float(previous.get("edge", previous.get("pnl", previous.get("sharpe", 0.0))))
            current_metric = float(current.get("edge", current.get("pnl", current.get("sharpe", 0.0))))
            if prev_metric > 0 and current_metric <= 0:
                cliffs.append(
                    ScalingCliff(
                        artifact_id=artifact.artifact_id,
                        dimension="capital" if "capital" in current else "compute",
                        cliff_value=current_value,
                        before_metric=prev_metric,
                        after_metric=current_metric,
                        reason="performance inverted from positive to non-positive",
                    )
                )
            elif prev_metric > 0 and current_metric < prev_metric * 0.35:
                cliffs.append(
                    ScalingCliff(
                        artifact_id=artifact.artifact_id,
                        dimension="capital" if "capital" in current else "compute",
                        cliff_value=current_value,
                        before_metric=prev_metric,
                        after_metric=current_metric,
                        reason="performance collapsed by more than 65%",
                    )
                )
            if current_value <= prev_value:
                continue
        return cliffs

    def reverse_engineer(self, artifact: SourceArtifact | Mapping[str, Any]) -> ReverseEngineeringReport:
        parsed = self.observe(artifact)
        decomposition = self.decompose(parsed)
        structured_claims = self.extract_claims(parsed)
        hype_report = self.detect_hype(parsed, structured_claims)
        classifications = self.classify(parsed, decomposition)
        profitability_tests = []
        if parsed.market_tests:
            profitability_tests.append(self.test_profitability(parsed.artifact_id, parsed.market_tests))
        patterns = self.extract_patterns(parsed, decomposition, classifications)
        capability_graph = self.build_capability_graph(parsed, structured_claims, decomposition)
        reusable_component_records = self.extract_reusable_components(parsed, decomposition, patterns)
        sandbox_experiments = self.generate_sandbox_experiments(parsed, structured_claims, patterns)
        promotion_decision = self.governance_gate(
            parsed,
            classifications,
            hype_report,
            patterns,
            sandbox_experiments,
            profitability_tests,
        )
        ghost = self.detect_ghost_capabilities(parsed)
        honeypot = self.detect_honeypot_patterns(parsed)
        scaling = self.detect_scaling_cliffs(parsed)

        fake_hype = self._hype_claims(parsed)
        rejected = []
        if CapabilityClass.LOW_VALUE_IDEA in classifications:
            rejected.append("no reusable workflow, tool chain, data flow, or test evidence")
        rejected.extend(fake_hype)
        rejected.extend(honeypot)
        for test in profitability_tests:
            if test.verdict in {ProfitabilityVerdict.FAILED, ProfitabilityVerdict.REJECTED}:
                rejected.extend(test.reasons)

        report = ReverseEngineeringReport(
            artifact_id=parsed.artifact_id,
            decomposition=decomposition,
            structured_claims=structured_claims,
            capability_graph=capability_graph,
            hype_report=hype_report,
            classifications=classifications,
            real_capabilities=self._real_capabilities(parsed, decomposition, classifications),
            fake_hype=fake_hype,
            reusable_components=list(patterns[0].reusable_components) if patterns else [],
            reusable_component_records=reusable_component_records,
            useful_patterns=patterns,
            sandbox_experiments=sandbox_experiments,
            promotion_decision=promotion_decision,
            rejected_ideas=sorted(set(rejected)),
            ghost_capabilities=ghost,
            honeypot_patterns=honeypot,
            scaling_cliffs=scaling,
            profitability_tests=profitability_tests,
        )
        self.reports[parsed.artifact_id] = report
        if promotion_decision.decision == ReverseEngineeringDecision.REJECT:
            self.remember_research_outcome(
                ResearchMemoryRecord(
                    pattern=parsed.title,
                    status="rejected",
                    tested_on=list(parsed.tags),
                    reason=promotion_decision.reason,
                    do_not_retry_until="new evidence or new filter introduced",
                    related_patterns=list(parsed.claims[:3]),
                )
            )
        return report

    def _artifact_text(self, artifact: SourceArtifact) -> str:
        values = (
            artifact.claims
            + artifact.workflow_steps
            + artifact.tools
            + artifact.architecture_hints
            + artifact.data_flow
            + artifact.marketed_features
            + artifact.observed_features
            + artifact.docs
            + artifact.failure_behavior
            + artifact.user_interaction_patterns
            + artifact.reasoning_traces
            + artifact.tags
        )
        return " ".join(str(value) for value in values).lower()

    def _has_cost_model(self, artifact: SourceArtifact) -> bool:
        text = self._artifact_text(artifact)
        return "cost" in text or "fee" in text or any("cost" in str(key).lower() for key in artifact.metrics)

    def _has_slippage_model(self, artifact: SourceArtifact) -> bool:
        text = self._artifact_text(artifact)
        return "slippage" in text or any("slippage" in str(key).lower() for key in artifact.metrics)

    def _has_out_of_sample(self, artifact: SourceArtifact) -> bool:
        text = self._artifact_text(artifact)
        return any(term in text for term in {"out-of-sample", "out of sample", "oos", "walk forward", "walk-forward"})

    def _has_benchmark(self, artifact: SourceArtifact) -> bool:
        text = self._artifact_text(artifact)
        return "benchmark" in text or "baseline" in text or any("benchmark" in str(key).lower() for key in artifact.metrics)

    def _has_sample_size(self, artifact: SourceArtifact) -> bool:
        return bool(
            artifact.market_tests
            or "sample_size" in artifact.metrics
            or "trade_count" in artifact.metrics
            or "n" in artifact.metrics
        )

    def _claim_type(self, claim: str) -> str:
        normalized = claim.lower()
        if any(term in normalized for term in {"liquidity", "smart money", "order block", "fair value gap"}):
            return "market_structure_detection"
        if any(term in normalized for term in {"win rate", "accuracy", "profit", "returns", "sharpe"}):
            return "performance_claim"
        if any(term in normalized for term in {"execute", "routing", "fill", "slippage", "order book"}):
            return "execution_optimization"
        if any(term in normalized for term in {"risk", "drawdown", "hedge", "crash"}):
            return "risk_control"
        if any(term in normalized for term in {"embedding", "classifier", "forecast", "model", "neural"}):
            return "model_architecture"
        return "general_capability"

    def _claimed_value(self, claim: str) -> str:
        normalized = claim.lower()
        for marker in ["predicts", "detects", "improves", "reduces", "optimizes", "generates"]:
            if marker in normalized:
                return claim[normalized.index(marker) :].strip()
        return claim

    def _claim_hype_risk(self, claim: str, artifact: SourceArtifact) -> str:
        normalized = claim.lower()
        if any(term in normalized for term in self.HONEYPOT_TERMS | self.DANGEROUS_TERMS):
            return "critical"
        if any(term in normalized for term in self.HYPE_TERMS):
            return "high"
        if not (artifact.metrics or artifact.market_tests or artifact.evidence_items):
            return "high"
        return "medium" if not self._has_cost_model(artifact) else "low"

    def _claim_testability(self, claim: str, claim_type: str, evidence_present: bool) -> str:
        normalized = claim.lower()
        if any(term in normalized for term in {"sentient", "magic", "god mode", "secret"}):
            return "low"
        if claim_type in {"performance_claim", "market_structure_detection", "execution_optimization"}:
            return "high" if evidence_present else "medium"
        return "medium" if evidence_present else "low"

    def _required_validation_for_claim(self, claim_type: str, claim: str) -> List[str]:
        common = [
            "point-in-time data validation",
            "out-of-sample or purged walk-forward validation",
            "transaction-cost-adjusted profitability",
            "slippage and broker execution assumptions",
            "paper/shadow validation before capital use",
        ]
        if claim_type == "market_structure_detection":
            return [
                "historical liquidity/sweep detection accuracy",
                "out-of-sample reversal statistics",
                "regime-specific false positive rate",
            ] + common
        if claim_type == "execution_optimization":
            return [
                "fill realism audit",
                "venue health replay",
                "cost stress ladder",
            ] + common
        if claim_type == "risk_control":
            return [
                "false-negative catastrophic event replay",
                "drawdown and portfolio impact validation",
                "bypass path scanner",
            ] + common
        if claim_type == "model_architecture":
            return [
                "feature leakage detection",
                "calibration error",
                "model decay monitoring",
            ] + common
        return common

    def _evidence_score(self, artifact: SourceArtifact) -> float:
        score = 0.0
        if artifact.metrics:
            score += 0.20
        if artifact.market_tests:
            score += 0.25
        if artifact.capital_tests:
            score += 0.10
        if artifact.evidence_items:
            score += 0.15
        if self._has_cost_model(artifact):
            score += 0.10
        if self._has_slippage_model(artifact):
            score += 0.10
        if self._has_out_of_sample(artifact):
            score += 0.10
        if self._has_benchmark(artifact):
            score += 0.10
        return min(score, 1.0)

    def _technical_substance_score(self, artifact: SourceArtifact) -> float:
        score = 0.0
        if artifact.workflow_steps:
            score += 0.25
        if artifact.tools:
            score += 0.20
        if artifact.data_flow:
            score += 0.20
        if artifact.architecture_hints:
            score += 0.15
        if artifact.outputs:
            score += 0.10
        if artifact.failure_behavior:
            score += 0.10
        return min(score, 1.0)

    def _alphaalgo_application(self, decomposition: DecomposedSystem) -> str:
        pattern = decomposition.architecture_pattern
        if "microstructure" in pattern:
            return "Execution feasibility and cost/slippage research"
        if "claim-evidence" in pattern:
            return "Decision Governance proof trace and PHCE-D validation"
        if "research-to-paper" in pattern:
            return "Research MVP pipeline and paper-trade promotion"
        if "retrieval" in pattern:
            return "COS retrieval and research memory"
        return "AlphaAlgo research lab sandbox"

    def _estimated_component_value(self, component: str, artifact: SourceArtifact) -> str:
        normalized = component.lower()
        if any(term in normalized for term in {"risk", "validation", "cost", "slippage", "paper", "claim"}):
            return "high"
        if artifact.metrics or artifact.market_tests:
            return "medium"
        return "low"

    def _implementation_difficulty(self, component: str) -> str:
        normalized = component.lower()
        if any(term in normalized for term in {"knowledge graph", "vector", "optimizer", "simulator", "order book"}):
            return "high"
        if any(term in normalized for term in {"validation", "cost", "paper", "feature"}):
            return "medium"
        return "low"

    def _experiment_dataset(self, artifact: SourceArtifact) -> str:
        if artifact.tags:
            return "_".join(artifact.tags[:3]) + "_point_in_time_research_set"
        if artifact.source_type == SourceType.PAPER:
            return "paper_reproduction_point_in_time_dataset"
        return "alphaalgo_sandbox_point_in_time_dataset"

    def _experiment_baseline(self, artifact: SourceArtifact) -> str:
        text = self._artifact_text(artifact)
        if "liquidity" in text or "smart money" in text:
            return "simple swing reversal strategy"
        if "volume" in text:
            return "baseline volume breakout strategy"
        if "sentiment" in text:
            return "price-only baseline with no sentiment feature"
        return "simple baseline gate"

    def _possible_salvage(
        self,
        artifact: SourceArtifact,
        classifications: Sequence[CapabilityClass],
    ) -> Optional[str]:
        text = self._artifact_text(artifact)
        if "sentiment" in text:
            return "Use sentiment velocity only as a weak auxiliary feature with strict risk cap."
        if "liquidity" in text or "smart money" in text:
            return "Reframe as volume/price anomaly detection and test against simple reversal baselines."
        if CapabilityClass.HONEYPOT_PATTERN in classifications:
            return "Do not copy; extract only high-level validation or risk-control lessons if lawful."
        return "Revisit only with reproducible evidence, cost model, and failure boundaries."

    def _infer_tools(self, artifact: SourceArtifact) -> set[str]:
        text = " ".join(
            artifact.claims
            + artifact.workflow_steps
            + artifact.architecture_hints
            + artifact.data_flow
            + artifact.marketed_features
        ).lower()
        return {hint for hint in self.TOOL_HINTS if hint in text}

    def _infer_architecture(self, artifact: SourceArtifact, tools: Sequence[str]) -> str:
        hints = " ".join(artifact.architecture_hints + artifact.claims + list(tools)).lower()
        if any(term in hints for term in {"dashboard", "analytics only", "chart overlay"}):
            return "dashboard-only analytics"
        if any(term in hints for term in {"rsi", "macd", "bollinger", "moving average", "indicator"}):
            return "indicator stack"
        if any(term in hints for term in {"rule", "liquidity sweep", "order block", "fair value gap", "swing"}):
            return "rule-based market structure engine"
        if any(term in hints for term in {"xgboost", "classifier", "random forest"}):
            return "ml classifier"
        if any(term in hints for term in {"lstm", "forecaster", "forecast", "time-series", "time series"}):
            return "time-series forecaster"
        if "claim graph" in hints or "evidence" in hints:
            return "claim-evidence-proof-action"
        if "agent" in hints or "multi-agent" in hints:
            return "multi-agent-orchestrated"
        if "reinforcement learning" in hints or "rl" in hints:
            return "reinforcement learning agent"
        if "backtest" in hints and "paper" in hints:
            return "research-to-paper-promotion"
        if "knowledge graph" in hints or "vector database" in hints:
            return "retrieval-augmented-memory"
        if "order book" in hints or "microstructure" in hints:
            return "market-microstructure-pipeline"
        if "risk" in hints:
            return "risk overlay"
        if "regime" in hints:
            return "market regime detector"
        if "portfolio" in hints or "allocator" in hints:
            return "portfolio allocator"
        if "ai" in hints and not artifact.tools and not artifact.architecture_hints:
            return "marketing wrapper around simple indicators"
        return "unknown"

    def _infer_data_flow(self, artifact: SourceArtifact, tools: Sequence[str]) -> List[str]:
        flow = ["observe"]
        if any("feature" in tool for tool in tools):
            flow.append("feature_extract")
        if any("backtest" in tool or "simulator" in tool for tool in tools):
            flow.append("test")
        if any("risk" in tool or "validation" in tool for tool in tools):
            flow.append("gate")
        if any("paper" in tool for tool in tools):
            flow.append("paper_validate")
        return flow

    def _infer_workflow(self, artifact: SourceArtifact, tools: Sequence[str]) -> List[str]:
        workflow = ["observe outputs", "decompose claims"]
        if tools:
            workflow.append("map tool chain")
        workflow.extend(["classify capability", "reject low-value ideas"])
        return workflow

    def _hype_claims(self, artifact: SourceArtifact) -> List[str]:
        claims = []
        for claim in artifact.claims + artifact.marketed_features:
            normalized = claim.lower()
            if any(term in normalized for term in self.HYPE_TERMS):
                claims.append(claim)
        return claims

    def _honeypot_claims(self, artifact: SourceArtifact) -> List[str]:
        claims = []
        source_is_competitor = artifact.source_type == SourceType.COMPETITOR or "competitor" in artifact.tags
        for claim in artifact.claims + artifact.marketed_features:
            normalized = claim.lower()
            if any(term in normalized for term in self.HONEYPOT_TERMS):
                claims.append(claim)
            elif source_is_competitor and any(term in normalized for term in {"guaranteed", "copy", "secret"}):
                claims.append(claim)
        return claims

    def _dangerous_claims(self, artifact: SourceArtifact) -> List[str]:
        claims = []
        for claim in artifact.claims + artifact.marketed_features + artifact.workflow_steps:
            normalized = claim.lower()
            if any(term in normalized for term in self.DANGEROUS_TERMS):
                claims.append(claim)
        return claims

    def _pattern_name(self, artifact: SourceArtifact, decomposition: DecomposedSystem) -> str:
        if decomposition.architecture_pattern != "unknown":
            return f"{artifact.title}: {decomposition.architecture_pattern}"
        return artifact.title or f"pattern from {artifact.artifact_id}"

    def _pattern_risks(self, artifact: SourceArtifact, classifications: Sequence[CapabilityClass]) -> List[str]:
        risks = []
        if CapabilityClass.GHOST_CAPABILITY in classifications:
            risks.append("contains unmarketed behavior; verify why it appears in outputs")
        if artifact.source_type in {SourceType.COMPETITOR, SourceType.UNKNOWN}:
            risks.append("source incentives may be adversarial or unclear")
        if not artifact.market_tests:
            risks.append("profitability not validated yet")
        return risks

    def _real_capabilities(
        self,
        artifact: SourceArtifact,
        decomposition: DecomposedSystem,
        classifications: Sequence[CapabilityClass],
    ) -> List[str]:
        if CapabilityClass.REAL_CAPABILITY not in classifications:
            return []
        capabilities = list(decomposition.tools_used)
        if artifact.metrics:
            capabilities.append("measured performance evidence")
        if artifact.outputs:
            capabilities.append("observable output behavior")
        return sorted(set(capabilities))


class CreatorIntelligenceEngine(AISystemReverseEngineeringEngine):
    """Scan creators/sources, extract useful patterns, test, and scale what works."""

    def scan_creators(self, artifacts: Sequence[SourceArtifact | Mapping[str, Any]]) -> CreatorScanReport:
        reports = [self.reverse_engineer(artifact) for artifact in artifacts]
        useful_patterns = [pattern for report in reports for pattern in report.useful_patterns]
        rejected = sorted({idea for report in reports for idea in report.rejected_ideas})
        real = sorted({capability for report in reports for capability in report.real_capabilities})
        fake = sorted({claim for report in reports for claim in report.fake_hype})
        ghost = sorted({capability for report in reports for capability in report.ghost_capabilities})
        honeypot = sorted({pattern for report in reports for pattern in report.honeypot_patterns})
        cliffs = [cliff for report in reports for cliff in report.scaling_cliffs]
        ranked = sorted(
            ((pattern.pattern_id, pattern.confidence) for pattern in useful_patterns),
            key=lambda item: item[1],
            reverse=True,
        )
        return CreatorScanReport(
            scanned_artifacts=len(reports),
            useful_patterns=useful_patterns,
            rejected_ideas=rejected,
            real_capabilities=real,
            fake_hype=fake,
            ghost_capabilities=ghost,
            honeypot_patterns=honeypot,
            scaling_cliffs=cliffs,
            ranked_patterns=ranked,
        )

    def scale_what_works(self, report: ReverseEngineeringReport) -> Dict[str, Any]:
        if not report.useful_patterns:
            return {"scalable": False, "reason": "no useful pattern extracted"}
        if report.scaling_cliffs:
            first = min(report.scaling_cliffs, key=lambda cliff: cliff.cliff_value)
            return {
                "scalable": True,
                "recommended_max_before_cliff": first.cliff_value,
                "dimension": first.dimension,
                "reason": first.reason,
            }
        return {
            "scalable": True,
            "recommended_max_before_cliff": None,
            "dimension": "unknown",
            "reason": "no scaling cliff detected in provided tests",
        }


def create_reverse_engineering_engine(config: Optional[Mapping[str, Any]] = None) -> AISystemReverseEngineeringEngine:
    return AISystemReverseEngineeringEngine(config=config)


def create_creator_intelligence_engine(config: Optional[Mapping[str, Any]] = None) -> CreatorIntelligenceEngine:
    return CreatorIntelligenceEngine(config=config)


def _token_set(values: Iterable[str]) -> set[str]:
    tokens: set[str] = set()
    for value in values:
        current = []
        for char in str(value).lower():
            if char.isalnum() or char == "_":
                current.append(char)
            elif current:
                tokens.add("".join(current))
                current = []
        if current:
            tokens.add("".join(current))
    return tokens


def _stable_hash(payload: Any) -> str:
    raw = json.dumps(_jsonable(payload), sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def _memory_key(value: str) -> str:
    tokens = sorted(_token_set([value]))
    return hashlib.sha256(" ".join(tokens).encode("utf-8")).hexdigest()[:16]


def _jsonable(value: Any) -> Any:
    if isinstance(value, Enum):
        return value.value
    if is_dataclass(value):
        return _jsonable(asdict(value))
    if isinstance(value, Mapping):
        return {str(key): _jsonable(inner) for key, inner in value.items()}
    if isinstance(value, (list, tuple, set)):
        return [_jsonable(inner) for inner in value]
    return value
