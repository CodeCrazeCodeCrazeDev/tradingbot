"""
Capability Ontology
===================

Maps every task to one or more Capability IDs before evaluation, routing, or deployment.
Section 5 of AlphaAlgo Meta-Intelligence Layer Specification.

A. Research Capabilities
B. Quant and Engineering Capabilities  
C. Market Intelligence Capabilities
D. Governance and Safety Capabilities
E. Operational Capabilities
"""

from enum import Enum
from dataclasses import dataclass, field
from typing import Dict, List, Any, Optional, Set
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class CapabilityDomain(Enum):
    """Capability domains per Section 5"""
    RESEARCH = "research"           # CAP-R-*
    QUANT = "quant"                 # CAP-Q-*
    MARKET = "market"               # CAP-M-*
    GOVERNANCE = "governance"       # CAP-G-*
    OPERATIONAL = "operational"     # CAP-O-*


class ResearchCapability(Enum):
    """A. Research Capabilities - CAP-R-01 to CAP-R-07"""
    HYPOTHESIS_GENERATION = "CAP-R-01"
    CONTRADICTION_DETECTION = "CAP-R-02"
    EVIDENCE_SUFFICIENCY_AUDIT = "CAP-R-03"
    CAUSAL_ARGUMENT_STRUCTURING = "CAP-R-04"
    LONG_CONTEXT_SYNTHESIS = "CAP-R-05"
    RESEARCH_PLAN_DECOMPOSITION = "CAP-R-06"
    COUNTERARGUMENT_GENERATION = "CAP-R-07"


class QuantCapability(Enum):
    """B. Quant and Engineering Capabilities - CAP-Q-01 to CAP-Q-08"""
    FEATURE_ENGINEERING_PROPOSAL = "CAP-Q-01"
    BACKTEST_READY_CODE_GENERATION = "CAP-Q-02"
    VECTORIZED_REFACTORING = "CAP-Q-03"
    OVERFITTING_DIAGNOSIS = "CAP-Q-04"
    SIGNAL_MEMO_GENERATION = "CAP-Q-05"
    PATCH_RISK_SCORING = "CAP-Q-06"
    TEST_CASE_GENERATION = "CAP-Q-07"
    NUMERICAL_CONSISTENCY_VERIFICATION = "CAP-Q-08"


class MarketCapability(Enum):
    """C. Market Intelligence Capabilities - CAP-M-01 to CAP-M-07"""
    STRUCTURED_EVENT_EXTRACTION = "CAP-M-01"
    MACRO_REPORT_PARSING = "CAP-M-02"
    REGIME_CLASSIFICATION = "CAP-M-03"
    CROSS_SOURCE_RECONCILIATION = "CAP-M-04"
    NARRATIVE_SHIFT_DETECTION = "CAP-M-05"
    NEWS_TO_SIGNAL_TRANSLATION = "CAP-M-06"
    REGIME_SHIFT_WARNING = "CAP-M-07"


class GovernanceCapability(Enum):
    """D. Governance and Safety Capabilities - CAP-G-01 to CAP-G-07"""
    UNCERTAINTY_DECOMPOSITION = "CAP-G-01"
    IMMUTABLE_AUDIT_TRAIL_GENERATION = "CAP-G-02"
    PRE_TRADE_COMPLIANCE_CHECK = "CAP-G-03"
    FAILURE_MODE_EXPLANATION = "CAP-G-04"
    EVIDENCE_PROVENANCE_CHECK = "CAP-G-05"
    POLICY_VIOLATION_DETECTION = "CAP-G-06"
    HUMAN_ESCALATION_RECOMMENDATION = "CAP-G-07"


class OperationalCapability(Enum):
    """E. Operational Capabilities - CAP-O-01 to CAP-O-07"""
    TOOL_SELECTION_RELIABILITY = "CAP-O-01"
    MULTI_STEP_TASK_PERSISTENCE = "CAP-O-02"
    FALLBACK_RECOVERY = "CAP-O-03"
    MEMORY_RETRIEVAL_PRECISION = "CAP-O-04"
    OUTPUT_SCHEMA_ADHERENCE = "CAP-O-05"
    TIMEOUT_RECOVERY = "CAP-O-06"
    ROUTING_DECISION_QUALITY = "CAP-O-07"


@dataclass
class CapabilityDefinition:
    """Definition of a capability per Section 5"""
    capability_id: str
    name: str
    domain: CapabilityDomain
    description: str
    required_evidence: List[str]
    forbidden_uses: List[str]
    risk_tier: str  # low, medium, high, critical
    performance_thresholds: Dict[str, float]
    cost_budget_ms: float
    latency_budget_ms: float
    
    
@dataclass 
class TaskCapabilityMapping:
    """Maps a task to required capabilities"""
    task_id: str
    task_family: str
    required_capabilities: List[str]
    risk_tier: str
    regime_assumptions: List[str]
    created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())


class CapabilityOntologyRegistry:
    """
    Registry for all capability definitions.
    
    Forbids evaluating "general intelligence."
    Evaluates only capability fit under constraints.
    """
    
    # All capability definitions per Section 5
    CAPABILITY_DEFINITIONS: Dict[str, Dict[str, Any]] = {
        # A. Research Capabilities
        "CAP-R-01": {
            "name": "Hypothesis Generation",
            "domain": CapabilityDomain.RESEARCH,
            "description": "Generate testable hypotheses from observations and prior knowledge",
            "required_evidence": ["logical_consistency", "falsifiability", "prior_alignment"],
            "forbidden_uses": ["unfalsifiable_claims", "circular_reasoning"],
            "risk_tier": "medium",
            "performance_thresholds": {"novelty": 0.7, "soundness": 0.8, "testability": 0.75},
            "cost_budget_ms": 2000,
            "latency_budget_ms": 5000
        },
        "CAP-R-02": {
            "name": "Contradiction Detection",
            "domain": CapabilityDomain.RESEARCH,
            "description": "Identify logical inconsistencies in arguments or data",
            "required_evidence": ["formal_logic_check", "semantic_consistency"],
            "forbidden_uses": ["nitpicking_irrelevant", "false_positives"],
            "risk_tier": "high",
            "performance_thresholds": {"precision": 0.9, "recall": 0.85, "f1": 0.87},
            "cost_budget_ms": 1500,
            "latency_budget_ms": 3000
        },
        "CAP-R-03": {
            "name": "Evidence Sufficiency Audit",
            "domain": CapabilityDomain.RESEARCH,
            "description": "Assess whether available evidence supports a conclusion",
            "required_evidence": ["evidence_coverage", "confidence_calibration"],
            "forbidden_uses": ["overconfidence", "cherry_picking"],
            "risk_tier": "critical",
            "performance_thresholds": {"coverage_score": 0.8, "calibration_error": 0.1},
            "cost_budget_ms": 2500,
            "latency_budget_ms": 4000
        },
        "CAP-R-04": {
            "name": "Causal Argument Structuring",
            "domain": CapabilityDomain.RESEARCH,
            "description": "Build valid causal chains from evidence",
            "required_evidence": ["temporal_order", "mechanism_clarity", "confound_control"],
            "forbidden_uses": ["post_hoc_fallacy", "correlation_causation"],
            "risk_tier": "critical",
            "performance_thresholds": {"validity": 0.85, "completeness": 0.75},
            "cost_budget_ms": 3000,
            "latency_budget_ms": 6000
        },
        "CAP-R-05": {
            "name": "Long-Context Synthesis",
            "domain": CapabilityDomain.RESEARCH,
            "description": "Synthesize information across lengthy documents",
            "required_evidence": ["coverage_check", "coherence_maintenance"],
            "forbidden_uses": ["cherry_picking", "out_of_context_quotes"],
            "risk_tier": "medium",
            "performance_thresholds": {"coverage": 0.8, "accuracy": 0.85},
            "cost_budget_ms": 5000,
            "latency_budget_ms": 10000
        },
        "CAP-R-06": {
            "name": "Research Plan Decomposition",
            "domain": CapabilityDomain.RESEARCH,
            "description": "Break complex research into actionable steps",
            "required_evidence": ["feasibility_check", "dependency_mapping"],
            "forbidden_uses": ["unrealistic_timelines", "missing_dependencies"],
            "risk_tier": "low",
            "performance_thresholds": {"completeness": 0.85, "feasibility": 0.8},
            "cost_budget_ms": 2000,
            "latency_budget_ms": 4000
        },
        "CAP-R-07": {
            "name": "Counterargument Generation",
            "domain": CapabilityDomain.RESEARCH,
            "description": "Generate plausible objections to claims",
            "required_evidence": ["relevance", "logical_validity"],
            "forbidden_uses": ["straw_man", "irrelevant_objections"],
            "risk_tier": "medium",
            "performance_thresholds": {"relevance": 0.8, "validity": 0.85},
            "cost_budget_ms": 2500,
            "latency_budget_ms": 5000
        },
        
        # B. Quant and Engineering Capabilities
        "CAP-Q-01": {
            "name": "Feature Engineering Proposal",
            "domain": CapabilityDomain.QUANT,
            "description": "Propose new features for trading models",
            "required_evidence": ["economic_rationale", "backtest_improvement"],
            "forbidden_uses": ["data_snooping", "overfitting_inducing"],
            "risk_tier": "high",
            "performance_thresholds": {"sharpe_improvement": 0.1, "robustness_score": 0.75},
            "cost_budget_ms": 3000,
            "latency_budget_ms": 8000
        },
        "CAP-Q-02": {
            "name": "Backtest-Ready Code Generation",
            "domain": CapabilityDomain.QUANT,
            "description": "Generate production-quality backtesting code",
            "required_evidence": ["correctness", "performance", "edge_case_handling"],
            "forbidden_uses": ["look_ahead_bias", "survivorship_bias"],
            "risk_tier": "critical",
            "performance_thresholds": {"correctness": 0.99, "performance": 0.8},
            "cost_budget_ms": 5000,
            "latency_budget_ms": 15000
        },
        "CAP-Q-03": {
            "name": "Vectorized Refactoring",
            "domain": CapabilityDomain.QUANT,
            "description": "Optimize code for vectorized execution",
            "required_evidence": ["speedup_ratio", "correctness_preservation"],
            "forbidden_uses": ["numeric_instability", "readability_sacrifice"],
            "risk_tier": "medium",
            "performance_thresholds": {"speedup": 5.0, "correctness": 1.0},
            "cost_budget_ms": 4000,
            "latency_budget_ms": 10000
        },
        "CAP-Q-04": {
            "name": "Overfitting Diagnosis",
            "domain": CapabilityDomain.QUANT,
            "description": "Detect and diagnose overfitting in models",
            "required_evidence": ["train_test_gap", "complexity_metrics"],
            "forbidden_uses": ["false_negatives", "spurious_correlations"],
            "risk_tier": "critical",
            "performance_thresholds": {"precision": 0.9, "recall": 0.85},
            "cost_budget_ms": 3000,
            "latency_budget_ms": 6000
        },
        "CAP-Q-05": {
            "name": "Signal Memo Generation",
            "domain": CapabilityDomain.QUANT,
            "description": "Generate structured signal documentation",
            "required_evidence": ["completeness", "clarity", "actionability"],
            "forbidden_uses": ["vagueness", "unactionable_content"],
            "risk_tier": "low",
            "performance_thresholds": {"completeness": 0.85, "clarity": 0.8},
            "cost_budget_ms": 2000,
            "latency_budget_ms": 4000
        },
        "CAP-Q-06": {
            "name": "Patch Risk Scoring",
            "domain": CapabilityDomain.QUANT,
            "description": "Assess risk of code changes to trading systems",
            "required_evidence": ["blast_radius", "test_coverage", "rollback_feasibility"],
            "forbidden_uses": ["underestimation", "false_reassurance"],
            "risk_tier": "critical",
            "performance_thresholds": {"accuracy": 0.85, "calibration": 0.8},
            "cost_budget_ms": 3000,
            "latency_budget_ms": 6000
        },
        "CAP-Q-07": {
            "name": "Test Case Generation",
            "domain": CapabilityDomain.QUANT,
            "description": "Generate comprehensive test cases",
            "required_evidence": ["coverage", "edge_cases", "oracle_correctness"],
            "forbidden_uses": ["trivial_tests", "missing_edge_cases"],
            "risk_tier": "high",
            "performance_thresholds": {"coverage": 0.9, "edge_case_hit_rate": 0.7},
            "cost_budget_ms": 2500,
            "latency_budget_ms": 6000
        },
        "CAP-Q-08": {
            "name": "Numerical Consistency Verification",
            "domain": CapabilityDomain.QUANT,
            "description": "Verify numerical stability and precision",
            "required_evidence": ["precision_bounds", "stability_tests"],
            "forbidden_uses": ["rounding_ignorance", "instolerance_tolerance"],
            "risk_tier": "critical",
            "performance_thresholds": {"accuracy": 0.999, "stability": 0.95},
            "cost_budget_ms": 2000,
            "latency_budget_ms": 4000
        },
        
        # C. Market Intelligence Capabilities
        "CAP-M-01": {
            "name": "Structured Event Extraction",
            "domain": CapabilityDomain.MARKET,
            "description": "Extract structured events from unstructured text",
            "required_evidence": ["entity_resolution", "temporal_anchoring", "event_typology"],
            "forbidden_uses": ["hallucinated_events", "temporal_confusion"],
            "risk_tier": "high",
            "performance_thresholds": {"precision": 0.85, "recall": 0.8, "f1": 0.82},
            "cost_budget_ms": 2000,
            "latency_budget_ms": 4000
        },
        "CAP-M-02": {
            "name": "Macro Report Parsing",
            "domain": CapabilityDomain.MARKET,
            "description": "Parse and summarize macroeconomic reports",
            "required_evidence": ["key_metrics", "trend_identification", "forecast_extraction"],
            "forbidden_uses": ["selective_reporting", "forecast_confusion"],
            "risk_tier": "medium",
            "performance_thresholds": {"completeness": 0.8, "accuracy": 0.85},
            "cost_budget_ms": 3000,
            "latency_budget_ms": 6000
        },
        "CAP-M-03": {
            "name": "Regime Classification",
            "domain": CapabilityDomain.MARKET,
            "description": "Classify current market regime",
            "required_evidence": ["volatility_regimes", "correlation_structure", "liquidity_conditions"],
            "forbidden_uses": ["regime_chasing", "false_precision"],
            "risk_tier": "critical",
            "performance_thresholds": {"accuracy": 0.75, "timeliness": 0.8},
            "cost_budget_ms": 1500,
            "latency_budget_ms": 3000
        },
        "CAP-M-04": {
            "name": "Cross-Source Reconciliation",
            "domain": CapabilityDomain.MARKET,
            "description": "Reconcile conflicting information across sources",
            "required_evidence": ["source_credibility", "consensus_detection", "divergence_analysis"],
            "forbidden_uses": ["false_consensus", "source_bias"],
            "risk_tier": "high",
            "performance_thresholds": {"accuracy": 0.8, "confidence_calibration": 0.75},
            "cost_budget_ms": 2500,
            "latency_budget_ms": 5000
        },
        "CAP-M-05": {
            "name": "Narrative Shift Detection",
            "domain": CapabilityDomain.MARKET,
            "description": "Detect changes in market narratives",
            "required_evidence": ["sentiment_trajectory", "volume_anomaly", "correlation_break"],
            "forbidden_uses": ["noise_trading", "false_positives"],
            "risk_tier": "high",
            "performance_thresholds": {"precision": 0.7, "recall": 0.75, "lead_time": 0.8},
            "cost_budget_ms": 2000,
            "latency_budget_ms": 4000
        },
        "CAP-M-06": {
            "name": "News-to-Signal Translation",
            "domain": CapabilityDomain.MARKET,
            "description": "Convert news events into trading signals",
            "required_evidence": ["impact_assessment", "directional_bias", "magnitude_estimate"],
            "forbidden_uses": ["reaction_trading", "overreaction"],
            "risk_tier": "critical",
            "performance_thresholds": {"precision": 0.65, "sharpe_contribution": 0.1},
            "cost_budget_ms": 1500,
            "latency_budget_ms": 3000
        },
        "CAP-M-07": {
            "name": "Regime-Shift Warning",
            "domain": CapabilityDomain.MARKET,
            "description": "Provide early warning of regime changes",
            "required_evidence": ["leading_indicators", "stress_signals", "correlation_breaks"],
            "forbidden_uses": ["false_alarms", "late_warnings"],
            "risk_tier": "critical",
            "performance_thresholds": {"precision": 0.7, "recall": 0.8, "lead_time_days": 3},
            "cost_budget_ms": 2000,
            "latency_budget_ms": 3000
        },
        
        # D. Governance and Safety Capabilities
        "CAP-G-01": {
            "name": "Uncertainty Decomposition",
            "domain": CapabilityDomain.GOVERNANCE,
            "description": "Break uncertainty into aleatoric and epistemic components",
            "required_evidence": ["aleatoric_estimate", "epistemic_estimate", "total_uncertainty"],
            "forbidden_uses": ["false_precision", "uncertainty_suppression"],
            "risk_tier": "critical",
            "performance_thresholds": {"calibration": 0.8, "resolution": 0.7},
            "cost_budget_ms": 2000,
            "latency_budget_ms": 4000
        },
        "CAP-G-02": {
            "name": "Immutable Audit Trail Generation",
            "domain": CapabilityDomain.GOVERNANCE,
            "description": "Generate tamper-proof audit records",
            "required_evidence": ["cryptographic_integrity", "temporal_ordering", "completeness"],
            "forbidden_uses": ["selective_logging", "tampering"],
            "risk_tier": "critical",
            "performance_thresholds": {"integrity": 1.0, "completeness": 0.99},
            "cost_budget_ms": 1000,
            "latency_budget_ms": 2000
        },
        "CAP-G-03": {
            "name": "Pre-Trade Compliance Check",
            "domain": CapabilityDomain.GOVERNANCE,
            "description": "Check trades against compliance rules",
            "required_evidence": ["rule_coverage", "limit_adherence", "exception_handling"],
            "forbidden_uses": ["false_negatives", "selective_enforcement"],
            "risk_tier": "critical",
            "performance_thresholds": {"precision": 0.99, "recall": 0.99, "latency_ms": 50},
            "cost_budget_ms": 500,
            "latency_budget_ms": 100
        },
        "CAP-G-04": {
            "name": "Failure Mode Explanation",
            "domain": CapabilityDomain.GOVERNANCE,
            "description": "Explain how and why a system failed",
            "required_evidence": ["root_cause", "contributing_factors", "preventability"],
            "forbidden_uses": ["blame_shifting", "vague_attribution"],
            "risk_tier": "high",
            "performance_thresholds": {"accuracy": 0.85, "actionability": 0.8},
            "cost_budget_ms": 3000,
            "latency_budget_ms": 6000
        },
        "CAP-G-05": {
            "name": "Evidence Provenance Check",
            "domain": CapabilityDomain.GOVERNANCE,
            "description": "Verify the source and chain of evidence",
            "required_evidence": ["source_attribution", "chain_integrity", "tamper_check"],
            "forbidden_uses": ["uncited_claims", "broken_chains"],
            "risk_tier": "critical",
            "performance_thresholds": {"precision": 0.95, "recall": 0.9},
            "cost_budget_ms": 1500,
            "latency_budget_ms": 3000
        },
        "CAP-G-06": {
            "name": "Policy Violation Detection",
            "domain": CapabilityDomain.GOVERNANCE,
            "description": "Detect violations of trading policies",
            "required_evidence": ["policy_coverage", "violation_evidence", "severity_assessment"],
            "forbidden_uses": ["false_negatives", "over_enforcement"],
            "risk_tier": "critical",
            "performance_thresholds": {"precision": 0.95, "recall": 0.95},
            "cost_budget_ms": 1000,
            "latency_budget_ms": 2000
        },
        "CAP-G-07": {
            "name": "Human Escalation Recommendation",
            "domain": CapabilityDomain.GOVERNANCE,
            "description": "Recommend when human review is needed",
            "required_evidence": ["uncertainty_level", "stake_assessment", "time_sensitivity"],
            "forbidden_uses": ["alarm_fatigue", "missed_escalations"],
            "risk_tier": "critical",
            "performance_thresholds": {"precision": 0.8, "recall": 0.9},
            "cost_budget_ms": 1000,
            "latency_budget_ms": 2000
        },
        
        # E. Operational Capabilities
        "CAP-O-01": {
            "name": "Tool Selection Reliability",
            "domain": CapabilityDomain.OPERATIONAL,
            "description": "Reliably select appropriate tools for tasks",
            "required_evidence": ["correctness", "efficiency", "fallback_readiness"],
            "forbidden_uses": ["wrong_tool", "excessive_tools"],
            "risk_tier": "high",
            "performance_thresholds": {"accuracy": 0.9, "efficiency": 0.8},
            "cost_budget_ms": 1000,
            "latency_budget_ms": 2000
        },
        "CAP-O-02": {
            "name": "Multi-Step Task Persistence",
            "domain": CapabilityDomain.OPERATIONAL,
            "description": "Maintain state and progress across task steps",
            "required_evidence": ["state_consistency", "progress_tracking", "recovery_capability"],
            "forbidden_uses": ["state_loss", "infinite_loops"],
            "risk_tier": "high",
            "performance_thresholds": {"completion_rate": 0.9, "error_recovery": 0.8},
            "cost_budget_ms": 2000,
            "latency_budget_ms": 4000
        },
        "CAP-O-03": {
            "name": "Fallback Recovery",
            "domain": CapabilityDomain.OPERATIONAL,
            "description": "Recover gracefully from failures",
            "required_evidence": ["fallback_activation", "graceful_degradation", "state_preservation"],
            "forbidden_uses": ["silent_failures", "cascading_failures"],
            "risk_tier": "critical",
            "performance_thresholds": {"recovery_rate": 0.95, "data_preservation": 1.0},
            "cost_budget_ms": 1500,
            "latency_budget_ms": 3000
        },
        "CAP-O-04": {
            "name": "Memory Retrieval Precision",
            "domain": CapabilityDomain.OPERATIONAL,
            "description": "Retrieve relevant memories accurately",
            "required_evidence": ["relevance", "recency_weighting", "context_fit"],
            "forbidden_uses": ["irrelevant_retrieval", "context_mismatch"],
            "risk_tier": "medium",
            "performance_thresholds": {"precision": 0.85, "recall": 0.8},
            "cost_budget_ms": 1000,
            "latency_budget_ms": 2000
        },
        "CAP-O-05": {
            "name": "Output Schema Adherence",
            "domain": CapabilityDomain.OPERATIONAL,
            "description": "Strictly adhere to output schemas",
            "required_evidence": ["schema_validity", "type_correctness", "completeness"],
            "forbidden_uses": ["schema_violations", "type_errors"],
            "risk_tier": "high",
            "performance_thresholds": {"adherence_rate": 0.99, "validation_pass_rate": 0.99},
            "cost_budget_ms": 500,
            "latency_budget_ms": 1000
        },
        "CAP-O-06": {
            "name": "Timeout Recovery",
            "domain": CapabilityDomain.OPERATIONAL,
            "description": "Handle timeouts gracefully",
            "required_evidence": ["timeout_detection", "partial_result_recovery", "cleanup"],
            "forbidden_uses": ["resource_leaks", "indefinite_blocking"],
            "risk_tier": "high",
            "performance_thresholds": {"recovery_rate": 0.9, "resource_cleanup": 1.0},
            "cost_budget_ms": 1000,
            "latency_budget_ms": 2000
        },
        "CAP-O-07": {
            "name": "Routing Decision Quality",
            "domain": CapabilityDomain.OPERATIONAL,
            "description": "Make high-quality routing decisions",
            "required_evidence": ["capability_fit", "constraint_satisfaction", "fallback_readiness"],
            "forbidden_uses": ["suboptimal_routes", "constraint_violations"],
            "risk_tier": "critical",
            "performance_thresholds": {"success_rate": 0.9, "constraint_satisfaction": 0.95},
            "cost_budget_ms": 500,
            "latency_budget_ms": 1000
        }
    }
    
    def __init__(self):
        self.task_mappings: Dict[str, TaskCapabilityMapping] = {}
        logger.info("CapabilityOntologyRegistry initialized with %d capabilities", 
                   len(self.CAPABILITY_DEFINITIONS))
    
    def get_capability(self, capability_id: str) -> Optional[CapabilityDefinition]:
        """Get capability definition by ID"""
        if capability_id not in self.CAPABILITY_DEFINITIONS:
            return None
        
        cap_data = self.CAPABILITY_DEFINITIONS[capability_id]
        return CapabilityDefinition(
            capability_id=capability_id,
            name=cap_data["name"],
            domain=cap_data["domain"],
            description=cap_data["description"],
            required_evidence=cap_data["required_evidence"],
            forbidden_uses=cap_data["forbidden_uses"],
            risk_tier=cap_data["risk_tier"],
            performance_thresholds=cap_data["performance_thresholds"],
            cost_budget_ms=cap_data["cost_budget_ms"],
            latency_budget_ms=cap_data["latency_budget_ms"]
        )
    
    def get_capabilities_by_domain(self, domain: CapabilityDomain) -> List[str]:
        """Get all capability IDs for a domain"""
        return [
            cap_id for cap_id, cap_data in self.CAPABILITY_DEFINITIONS.items()
            if cap_data["domain"] == domain
        ]
    
    def get_capabilities_by_risk_tier(self, risk_tier: str) -> List[str]:
        """Get all capability IDs for a risk tier"""
        return [
            cap_id for cap_id, cap_data in self.CAPABILITY_DEFINITIONS.items()
            if cap_data["risk_tier"] == risk_tier
        ]
    
    def map_task_to_capabilities(self, task_id: str, task_family: str,
                                 required_capabilities: List[str],
                                 risk_tier: str,
                                 regime_assumptions: List[str]) -> TaskCapabilityMapping:
        """Map a task to required capabilities"""
        mapping = TaskCapabilityMapping(
            task_id=task_id,
            task_family=task_family,
            required_capabilities=required_capabilities,
            risk_tier=risk_tier,
            regime_assumptions=regime_assumptions
        )
        self.task_mappings[task_id] = mapping
        return mapping
    
    def get_task_mapping(self, task_id: str) -> Optional[TaskCapabilityMapping]:
        """Get capability mapping for a task"""
        return self.task_mappings.get(task_id)
    
    def validate_capability_id(self, capability_id: str) -> bool:
        """Validate a capability ID exists"""
        return capability_id in self.CAPABILITY_DEFINITIONS
    
    def get_all_capabilities(self) -> List[str]:
        """Get all capability IDs"""
        return list(self.CAPABILITY_DEFINITIONS.keys())
    
    def get_forbidden_uses(self, capability_id: str) -> List[str]:
        """Get forbidden uses for a capability"""
        cap = self.get_capability(capability_id)
        return cap.forbidden_uses if cap else []


# Convenience functions
def create_ontology_registry() -> CapabilityOntologyRegistry:
    """Factory function to create a capability ontology registry"""
    return CapabilityOntologyRegistry()
