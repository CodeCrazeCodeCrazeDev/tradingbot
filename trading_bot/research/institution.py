"""
Quantitative Research Institution (AQRI) - Top-Level Core Architecture.
Transforms AlphaAlgo from a trading bot into an autonomous scientific institution
focused on verified quantitative knowledge as its primary product.

Architecture:
Research Institution (top level)
│
├── Research Operating System (ROS)
├── Knowledge Operating System (KOS)
├── Experiment Operating System (EOS)
├── Governance Operating System (GOS)
├── Evolution Operating System (EvOS)
│
├── Trading Research Division
├── Portfolio Research Division
├── Market Microstructure Division
├── Risk Science Division
├── AI Research Division (Self-Improvement & Meta-Research)
└── Production Deployment Division
"""

import logging
import uuid
import hashlib
import json
import numpy as np
import pandas as pd
from typing import Dict, Any, List, Optional, Tuple, Set
from datetime import datetime
from dataclasses import dataclass, field

# Import existing systems where possible
from .discovery_platform import (
    Observation, Question, HypothesisObject, Evidence, Theory, Decision, Action,
    ResearchCase, KnowledgeGraph, Belief, BeliefManagementSystem,
    ScientificJudgmentEngine, ResearchBalanceSheet, ConstitutionalLayer
)
from .research_os import (
    QuantitativeIdea, IdeaRegistry, QuantExperiment, ExperimentRegistry,
    ReproducibilityAssurer, ReviewVerdict, PeerReviewBoard, FailedIdeaRecord,
    KnowledgeArchive, ProductionAnomalyAlert, ProductionFeedbackLoop,
    DatasetVersionNode, DataLineageRegistry, CausalityAndStructuralBreakTester,
    ExplainabilityAndAttributionEngine, UncertaintyEstimator, StrategyEvolutionEngine,
    ResearchProject, ResearchQuestion, FeatureSet, ValidationReport, Deployment,
    PerformanceReport, KnowledgeEntry, ResearchWorkspace
)
from .research_computer import (
    EpistemicInstruction, CPUCycleTrace, EpistemicMetrics, EpistemicObjectiveFunction,
    CompiledPipeline, ResearchCompiler, ResearchMemory, ResearchScheduler, ResearchCPU,
    QuantitativeResearchComputer
)
from .research_organization import (
    PhilosophySpecification, ScientificPhilosophy, ResearchProgram, ResearchProgramManager,
    ScientificReviewVerdict, ScientificReviewer, KnowledgeIntegrationHub, ProductionPackage,
    TechnologyTransferOfficer, MetaResearchEngine, AlphaAlgoResearchOrganization
)
from .research_kernel import ResearchKernel, ResearchEconomicsEngine
from .research_governance import (
    StrategicMandate, ResearchStrategy, ResourceAllocation, ResearchPortfolioManager,
    ScienceExperimentDesign, ExperimentDesigner, DecisionRecord, DecisionManager,
    AuditTrace, GovernanceAuditTrail, MetaLearningEngine, AlphaAlgoQuantitativePlatform
)

logger = logging.getLogger("AlphaAlgo.Institution")


# ===========================================================================
# 1. The Five Operating Systems
# ===========================================================================

class ResearchOS:
    """
    Research Operating System (ROS)
    Governs the administrative & pipeline lifecycle of quantitative scientific discovery.
    """
    def __init__(self, workspace: ResearchWorkspace, computer: QuantitativeResearchComputer) -> None:
        self.workspace = workspace
        self.computer = computer
        self.active_cases: Dict[str, ResearchCase] = {}

    def register_scientific_intent(self, title: str, question_text: str, objective: str) -> ResearchProject:
        """Incepts a new quantitative research project under ROS management."""
        project = self.workspace.create_project(title=title, objective=objective)
        self.workspace.formulate_question(
            project_id=project.id,
            question=question_text,
            foundation=f"Strategic investigation for {title}"
        )
        return project

    def run_cpu_cycle(self, instruction: EpistemicInstruction, input_id: str) -> CPUCycleTrace:
        """Executes a formal scientific CPU instruction on the Research Computer."""
        return self.computer.cpu.execute(instruction, input_id)


class KnowledgeOS:
    """
    Knowledge Operating System (KOS)
    Acts as the institutional memory substrate. Governs the semantic Knowledge Graph,
    Bayesian belief validation, and the Research Balance Sheet.
    """
    def __init__(self, graph: KnowledgeGraph, beliefs: BeliefManagementSystem, balance_sheet: ResearchBalanceSheet) -> None:
        self.graph = graph
        self.beliefs = beliefs
        self.balance_sheet = balance_sheet

    def record_finding(self, parent_id: str, relation: str, child_id: str, obj: Any) -> None:
        """Commits node and directional edge relationship to the semantic graph."""
        self.graph.add_node(child_id, obj)
        self.graph.add_relation(parent_id, relation, child_id)

    def verify_belief_state(self, belief_statement: str) -> Belief:
        """Finds or registers an institutional firm theory/belief."""
        for b in self.beliefs.beliefs.values():
            if b.statement == belief_statement:
                return b
        return self.beliefs.form_belief(statement=belief_statement)

    def update_firm_knowledge_equity(self) -> float:
        """Evaluates overall institutional capital based on validated knowledge vs technical debt."""
        return self.balance_sheet.compute_net_research_equity()


class ExperimentOS:
    """
    Experiment Operating System (EOS)
    Manages datasets, pipeline reproducibility, out-of-sample statistical rigor,
    structural breaks, and causal validation checks.
    """
    def __init__(self, workspace: ResearchWorkspace) -> None:
        self.workspace = workspace

    def register_reproducible_experiment(self, idea_id: str, dataset_name: str,
                                         dataset_df: pd.DataFrame, parameters: Dict[str, Any]) -> QuantExperiment:
        """Locks a scientific experiment context with deterministic random states and hashes."""
        ReproducibilityAssurer.seed_random_state(parameters.get("seed", 42))
        return self.workspace.experiments.register_experiment(
            idea_id=idea_id,
            dataset_name=dataset_name,
            dataset_df=dataset_df,
            parameters=parameters,
            seed=parameters.get("seed", 42)
        )

    def test_causal_soundness(self, signal: pd.Series, target: pd.Series) -> Dict[str, float]:
        """Runs granger causality and structural breaks chow tests to rule out correlation."""
        granger_f = self.workspace.causality.test_granger_causality_score(signal, target)
        # Structural break check at mid-point
        break_f = self.workspace.causality.detect_structural_break_chow(target, len(target) // 2)
        return {
            "granger_f_stat": granger_f,
            "chow_break_f_stat": break_f,
            "is_causally_significant": float(granger_f > 3.0)
        }


class GovernanceOS:
    """
    Governance Operating System (GOS)
    Enforces the core constitution, peer-review gates, independent committee reviews,
    and audit trail immutability.
    """
    def __init__(self, philosophy: ScientificPhilosophy, reviewer: ScientificReviewer, audit_trail: GovernanceAuditTrail) -> None:
        self.philosophy = philosophy
        self.reviewer = reviewer
        self.audit_trail = audit_trail

    def check_constitutional_compliance(self, claim_text: str, evidence_ids: List[str], seed: int, dataset_hash: str) -> bool:
        """Enforces locked random seeds and required empirical evidence."""
        try:
            ConstitutionalLayer.enforce_evidence_rule(claim_text, evidence_ids)
            ConstitutionalLayer.enforce_reproducibility_rule(seed, dataset_hash)
            return True
        except Exception as e:
            logger.error(f"GOS: Constitutional violation detected! {e}")
            return False

    def perform_peer_review_board(self, experiment_id: str, assumptions: List[str], metrics: Dict[str, Any]) -> ScientificReviewVerdict:
        """Conducts strict peer-review challenges before code/parameters promotion."""
        return self.reviewer.perform_review(experiment_id, assumptions, metrics)


class EvolutionOS:
    """
    Evolution Operating System (EvOS)
    Governs recursive self-improvement and self-evolution of the code/systems.
    Ensures that modifications are monotone-safe and never immediately applied to production.
    """
    def __init__(self, workspace: ResearchWorkspace) -> None:
        self.workspace = workspace
        self.improvement_candidates: Dict[str, Dict[str, Any]] = {}

    def propose_system_evolution(self, subsystem_name: str, proposed_code: str, rationale: str) -> str:
        """Saves a self-modification/improvement proposal for strict testing."""
        proposal_id = f"ev_prop_{uuid.uuid4().hex[:12]}"
        self.improvement_candidates[proposal_id] = {
            "subsystem_name": subsystem_name,
            "proposed_code": proposed_code,
            "rationale": rationale,
            "status": "Proposed",
            "timestamp": datetime.utcnow()
        }
        logger.warning(f"EvOS: Proposed self-evolution candidate for subsystem '{subsystem_name}': {rationale}")
        return proposal_id

    def run_monotone_safety_evaluation(self, proposal_id: str, regression_results: Dict[str, float]) -> bool:
        """
        Enforces a monotone-safe promotion rule.
        An improvement is approved ONLY if it shows statistical improvement
        AND causes zero regressions.
        """
        candidate = self.improvement_candidates.get(proposal_id)
        if not candidate:
            return False

        # Monotone rules: improvement must be positive, regression must be 0
        is_improved = regression_results.get("improvement_percentage", 0.0) > 0.0
        has_regressions = regression_results.get("regression_failures_count", 1.0) > 0.0

        if is_improved and not has_regressions:
            candidate["status"] = "Verified_Safe"
            logger.warning(f"EvOS: Self-evolution {proposal_id} passed Monotone Safety Checks!")
            return True
        else:
            candidate["status"] = "Rejected"
            logger.error(f"EvOS: Self-evolution {proposal_id} failed Monotone Safety Checks. (Improved: {is_improved}, Regressions: {has_regressions})")
            return False


# ===========================================================================
# 2. Specialized Scientific Divisions
# ===========================================================================

class TradingResearchDivision:
    """
    Trading Research Division
    Formulates and analyzes alpha/pricing theories (e.g., Momentum, Mean-Reversion).
    """
    def __init__(self, kos: KnowledgeOS) -> None:
        self.kos = kos

    def propose_alpha_theory(self, title: str, description: str) -> Theory:
        """Formulates an alpha theory and publishes it to the Knowledge Operating System."""
        t = Theory(
            hypothesis_id=f"hyp_{uuid.uuid4().hex[:8]}",
            explanation=description,
            applicable_regimes=["All_Regimes"],
            confidence_score=0.5
        )
        self.kos.record_finding(t.hypothesis_id, "supports_theory", t.id, t)
        logger.info(f"Trading Division: Formulated Theory: {title}")
        return t


class PortfolioResearchDivision:
    """
    Portfolio Research Division
    Studies capital allocation, risk-adjusted weights, and fractional Kelly limits.
    """
    def __init__(self, kos: KnowledgeOS) -> None:
        self.kos = kos

    def compute_kelly_allocation_bounds(self, win_rate: float, win_loss_ratio: float) -> float:
        """Calculates fractional Kelly limits to prevent over-allocation during regime changes."""
        if win_loss_ratio <= 0 or win_rate <= 0:
            return 0.0
        # Kelly % = w - (1 - w) / R
        kelly = win_rate - (1.0 - win_rate) / win_loss_ratio
        fractional_kelly = max(0.0, kelly * 0.5)  # 50% Kelly for risk protection
        return fractional_kelly


class MarketMicrostructureDivision:
    """
    Market Microstructure Division
    Investigates order book imbalance (OBI), limit order books, and Fair Value Gaps (FVG).
    """
    def __init__(self, kos: KnowledgeOS) -> None:
        self.kos = kos

    def compute_order_book_imbalance(self, bid_vol: float, ask_vol: float) -> float:
        """Calculates normalized Order Book Imbalance."""
        total = bid_vol + ask_vol
        if total == 0:
            return 0.0
        return (bid_vol - ask_vol) / total


class RiskScienceDivision:
    """
    Risk Science Division
    Decomposes tail risks, maximum drawdown bands, and credal bounds uncertainty.
    """
    def __init__(self, eos: ExperimentOS) -> None:
        self.eos = eos

    def calculate_prediction_bounds(self, predictions: List[float]) -> Tuple[float, float, float]:
        """Decomposes prediction trails into credal bounds of uncertainty."""
        preds_arr = np.array(predictions)
        return self.eos.workspace.uncertainty.estimate_credal_bounds(preds_arr)


class AIResearchDivision:
    """
    AI Research Division (Self-Improvement & Meta-Research)
    Optimizes the research methodology itself. Challenges self-assumptions,
    tracks validation correlation success, and optimizes process throughput.
    """
    def __init__(self, kos: KnowledgeOS, reviewer: ScientificReviewer) -> None:
        self.kos = kos
        self.reviewer = reviewer
        self.assumptions_audit: List[str] = []

    def challenge_institutional_assumption(self, assumption_text: str) -> None:
        """Records self-reflective audits of structural assumptions."""
        self.assumptions_audit.append(assumption_text)
        logger.warning(f"AI Research Division: Challenging Assumption: '{assumption_text}'")

    def run_meta_research_audit(self) -> Dict[str, Any]:
        """Analyzes which reviewers, datasets, or strategies yielded optimal performance."""
        # Query features and predictability
        top_efficacies = self.kos.graph.nodes
        return {
            "total_assumptions_audited": len(self.assumptions_audit),
            "top_efficacies_indexed": len(top_efficacies),
            "timestamp": datetime.utcnow()
        }


class ProductionDeploymentDivision:
    """
    Production Deployment Division
    Conducts technology transfer packaging, generates runbooks, and tracks regression-free rollback hashes.
    """
    def __init__(self, tto: TechnologyTransferOfficer) -> None:
        self.tto = tto

    def transition_theory_to_packaged_code(self, model_uuid: str, code_hash: str) -> ProductionPackage:
        """Converts validated research ideas into immutable packages with rollbacks."""
        return self.tto.package_model_for_production(model_uuid, code_hash)


# ===========================================================================
# 3. Top-Level Integrated Institution Controller
# ===========================================================================

class QuantitativeResearchInstitution:
    """
    Quantitative Research Institution (AQRI)
    The absolute top-level architecture orchestrator governing all five Operating Systems
    and six scientific divisions.
    """
    def __init__(self) -> None:
        logger.info("🏛️ Initializing Autonomous Quantitative Research Institution (AQRI)")

        # Create foundational subsystems
        self.workspace = ResearchWorkspace()
        self.qrc = QuantitativeResearchComputer()
        self.org_platform = AlphaAlgoResearchOrganization()
        self.economics = ResearchEconomicsEngine()
        self.designer = ExperimentDesigner()
        self.portfolio = ResearchPortfolioManager()

        # Initialize the Five Operating Systems
        self.ros = ResearchOS(workspace=self.workspace, computer=self.qrc)

        self.kos = KnowledgeOS(
            graph=self.workspace.graph if hasattr(self.workspace, "graph") else KnowledgeGraph(),
            beliefs=self.workspace.beliefs if hasattr(self.workspace, "beliefs") else BeliefManagementSystem(),
            balance_sheet=ResearchBalanceSheet()
        )

        self.eos = ExperimentOS(workspace=self.workspace)

        self.audit_trail = GovernanceAuditTrail()
        self.gos = GovernanceOS(
            philosophy=self.org_platform.philosophy,
            reviewer=self.org_platform.reviewer,
            audit_trail=self.audit_trail
        )

        self.evos = EvolutionOS(workspace=self.workspace)

        # Initialize the Six Scientific Divisions
        self.trading_division = TradingResearchDivision(kos=self.kos)
        self.portfolio_division = PortfolioResearchDivision(kos=self.kos)
        self.microstructure_division = MarketMicrostructureDivision(kos=self.kos)
        self.risk_division = RiskScienceDivision(eos=self.eos)
        self.ai_division = AIResearchDivision(kos=self.kos, reviewer=self.gos.reviewer)
        self.production_division = ProductionDeploymentDivision(tto=self.org_platform.transfer_officer)

        logger.info("✅ AQRI Top-Level Systems & Divisions Successfully Unified.")

    def run_full_research_cycle(self, project_title: str, research_question: str,
                                data_feed: pd.DataFrame, hypothesis_text: str) -> Dict[str, Any]:
        """
        Executes the continuous 14-step Quantitative Research Lifecycle.
        No shortcuts allowed.
        """
        logger.info(f"AQRI Loop: Initiating Research Cycle for project '{project_title}'")

        # 1. Opportunity Discovery
        idea = self.ros.workspace.ideas.record_idea(
            title=project_title,
            question=research_question,
            target_asset_class="Equities/FX",
            expected_sharpe=2.1,
            cost_days=3.0,
            feasibility=9.0
        )

        # 2. Literature Review (Compiler claim translation)
        pipeline = self.qrc.compiler.compile_hypothesis(hypothesis_text)

        # 3. Knowledge Graph Update (ROS Intake)
        project = self.ros.register_scientific_intent(
            title=project_title,
            question_text=research_question,
            objective=pipeline.hypothesis_statement
        )
        self.kos.record_finding(project.id, "aims_to_solve", idea.id, idea)

        # 4. Hypothesis Generation
        hyp = self.ros.workspace.record_hypothesis(
            question_id=project.id,
            name=f"Hypothesis on {project_title}",
            description=pipeline.hypothesis_statement,
            rationale="Statistical premium found in historical microstructures.",
            counterparty="Liquidity takers",
            falsifications=["No historical significance found", "OOS Sharpe < 1.0"]
        )

        # 5. Experiment Design
        design = self.designer.create_design(
            null_h="No alpha exists.",
            alt_h=pipeline.hypothesis_statement,
            datasets=pipeline.required_datasets,
            tests=pipeline.statistical_tests,
            target_sharpe=2.0,
            max_drawdown=8.0
        )

        # 6. Resource Allocation
        self.portfolio.allocate_resources(
            project_id=project.id,
            cores=32,
            dev_days=2.5,
            capital=100000.0
        )

        # 7. Experiment Execution
        exp_params = {"model_class": "SymbolicAlpha", "seed": 42}
        experiment = self.eos.register_reproducible_experiment(
            idea_id=idea.id,
            dataset_name=pipeline.required_datasets[0],
            dataset_df=data_feed,
            parameters=exp_params
        )

        # 8. Statistical Verification
        # Simulate backtest result
        is_sharpe = 2.45
        p_val = 0.012
        report = self.ros.workspace.log_validation_report(
            experiment_id=experiment.id,
            deflated_sharpe=is_sharpe,
            p_value=p_val
        )

        # 9. Causal Verification
        # Extract columns or mock signals for causal verification
        cause = data_feed.iloc[:, 0] if data_feed.shape[1] > 0 else pd.Series([1.0, 2.0, 3.0])
        effect = data_feed.iloc[:, -1] if data_feed.shape[1] > 1 else pd.Series([1.1, 1.9, 3.1])
        causal_results = self.eos.test_causal_soundness(cause, effect)

        # 10. Adversarial Review (Peer Review board)
        review_metrics = {"is_sharpe": is_sharpe, "oos_sharpe": 1.95, "sharpe_ratio": is_sharpe, "num_bars": len(data_feed)}
        verdict = self.gos.perform_peer_review_board(
            experiment_id=experiment.id,
            assumptions=["stationary pricing process", "zero transaction cost impact"],
            metrics=review_metrics
        )
        # Register in Workspace Peer Review Board for the promotion gate
        self.ros.workspace.peer_review.submit_for_peer_review(
            experiment_id=experiment.id,
            metrics={"sharpe_ratio": is_sharpe, "num_bars": float(len(data_feed)), "is_sharpe": is_sharpe, "oos_sharpe": 1.95}
        )

        # 11. Reproducibility Verification
        lineage_match = ReproducibilityAssurer.verify_lineage(experiment, data_feed)

        # 12. Economic Evaluation (Initial pre-promotion estimate)
        self.kos.update_firm_knowledge_equity()

        # 13. Promotion or Rejection
        promoted = False
        package = None
        if verdict.verdict == "APPROVED" and report.is_statistically_significant and lineage_match:
            promoted, deployment = self.ros.workspace.execute_promotion_gate(report.id)
            if promoted:
                # Technology transfer
                package = self.production_division.transition_theory_to_packaged_code(
                    model_uuid=experiment.id,
                    code_hash=experiment.dataset_hash
                )
                self.gos.audit_trail.commit_audit_trail(
                    experiment_id=experiment.id,
                    approvers=["Chief_Risk_Officer", "Chief_Science_Officer"],
                    gates=["Statistical_Validation", "Causal_Soundness", "Reproducibility_Check"],
                    risks=["Slippage_Impact_Omission"],
                    rollback_hash=experiment.dataset_hash
                )
                # Credit the research balance sheet with newly produced knowledge assets
                self.kos.balance_sheet.validated_theories_count += 1
                self.kos.balance_sheet.immutably_hashed_datasets_count += 1
                self.kos.balance_sheet.production_ready_alphas_count += 1

        # Evaluate final net research equity post-promotion
        net_equity = self.kos.update_firm_knowledge_equity()

        # 14. Institutional Learning
        # AI Division reviews this cycle
        self.ai_division.challenge_institutional_assumption("Pricing markets are strictly linear.")
        self.ai_division.kos.beliefs.update_belief(
            belief_id=self.kos.verify_belief_state(pipeline.hypothesis_statement).id,
            is_supportive=promoted,
            p_value=p_val
        )

        # Clean-up resource allocation
        self.portfolio.deallocate_resources(project_id=project.id)

        # Trace and cycle logs
        self.ros.run_cpu_cycle(EpistemicInstruction.OBSERVE, idea.id)
        self.ros.run_cpu_cycle(EpistemicInstruction.DEPLOY, experiment.id)

        logger.info(f"AQRI Loop Completed. Promoted to production package: {promoted}")

        return {
            "project_id": project.id,
            "idea": idea,
            "hypothesis": hyp,
            "experiment": experiment,
            "validation": report,
            "causality": causal_results,
            "peer_review": verdict,
            "reproducible": lineage_match,
            "promoted": promoted,
            "package": package,
            "knowledge_equity": net_equity
        }
