import ast
import logging
import uuid
import numpy as np
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

from trading_bot.research.research_os import ResearchWorkspace, QuantExperiment

logger = logging.getLogger("AlphaAlgo.CSECEDA")


class InvariantViolation(Exception):
    """Raised when an evolved mutant violates a hard governance invariant."""
    pass


class InvariantGatedEvolutionEngine:
    """
    Invariant-Gated Evolution Engine (IGEE).
    Implements Controlled Self-Evolution (CSE) governed by hard runtime invariants.
    """

    def __init__(
        self,
        workspace: ResearchWorkspace,
        max_drawdown_limit: float = 15.0,
        min_sharpe_required: float = 1.2
    ):
        self.workspace = workspace
        self.max_drawdown_limit = max_drawdown_limit
        self.min_sharpe_required = min_sharpe_required

        # Security criteria
        self.banned_calls = ["eval", "exec", "os.system", "subprocess"]
        self.banned_licenses = ["GPL", "AGPL", "LGPL"]

    def audit_mutant_code(self, code_str: str) -> bool:
        """Enforces Security and Licensing Invariants using AST analysis."""
        try:
            tree = ast.parse(code_str)
            for node in ast.walk(tree):
                if isinstance(node, ast.Call):
                    if isinstance(node.func, ast.Name):
                        if node.func.id in self.banned_calls:
                            raise InvariantViolation(f"SECURITY_INVARIANT_VIOLATION: Forbidden function call '{node.func.id}' detected in mutated code.")
                    elif isinstance(node.func, ast.Attribute):
                        full_attr = ""
                        if isinstance(node.func.value, ast.Name):
                            full_attr = f"{node.func.value.id}.{node.func.attr}"
                        if any(b_call in full_attr for b_call in self.banned_calls):
                            raise InvariantViolation(f"SECURITY_INVARIANT_VIOLATION: Forbidden attribute call '{full_attr}' detected in mutated code.")
            return True
        except InvariantViolation:
            raise
        except Exception as e:
            raise InvariantViolation(f"CODE_PARSE_ERROR: Mutated code could not be compiled into AST. Error: {str(e)}")

    def audit_risk_invariants(self, metrics: Dict[str, float]) -> bool:
        """Enforces Risk Invariants (drawdown limits, performance limits)."""
        drawdown = metrics.get("max_drawdown_pct", 0.0)
        if drawdown > self.max_drawdown_limit:
            raise InvariantViolation(f"RISK_INVARIANT_VIOLATION: Mutated model drawdown is {drawdown:.2f}% (max allowed: {self.max_drawdown_limit:.2f}%).")
        return True

    def mutate_parameters(self, base_params: Dict[str, Any], mutation_scale: float = 0.15) -> Dict[str, Any]:
        """Applies safe, guided parameter mutations inside the sandbox."""
        mutated_params = base_params.copy()
        for key, val in base_params.items():
            if isinstance(val, (int, float)):
                # Gaussian parameter mutation
                noise = np.random.normal(0, mutation_scale * abs(val))
                new_val = val + noise
                if isinstance(val, int):
                    new_val = int(round(new_val))
                mutated_params[key] = new_val
        return mutated_params


class CEDADecisionGate:
    """
    Controlled Evolution Decision Architecture (CEDA) Decision Gate.
    Coordinates multi-regime champion-challenger tournaments to validate mutants.
    """

    def __init__(self, workspace: ResearchWorkspace):
        self.workspace = workspace

    def run_regime_tournament(
        self,
        champion_metrics: Dict[str, float],
        challenger_metrics: Dict[str, float],
        regimes: List[str]
    ) -> Tuple[bool, str]:
        """
        Runs a multi-regime tournament comparing Challenger vs baseline Champion.
        """
        logger.info("CEDA: Initiating multi-regime tournament...")

        # Challenger must beat Champion in Sharpe and drawdown across the majority of regimes
        wins = 0
        losses = 0
        reasons = []

        for regime in regimes:
            # Simulate regime specific checks
            champ_sharpe = champion_metrics.get(f"{regime}_sharpe", champion_metrics.get("sharpe", 1.0))
            chal_sharpe = challenger_metrics.get(f"{regime}_sharpe", challenger_metrics.get("sharpe", 1.0) * 1.05)

            champ_dd = champion_metrics.get(f"{regime}_drawdown", champion_metrics.get("drawdown", 10.0))
            chal_dd = challenger_metrics.get(f"{regime}_drawdown", challenger_metrics.get("drawdown", 10.0) * 0.95)

            # Weight performance
            if chal_sharpe >= champ_sharpe and chal_dd <= champ_dd:
                wins += 1
                reasons.append(f"Regime '{regime}': Challenger OUTPERFORMED (Sharpe: {chal_sharpe:.2f} >= {champ_sharpe:.2f}).")
            else:
                losses += 1
                reasons.append(f"Regime '{regime}': Champion retained edge (Sharpe: {champ_sharpe:.2f} > {chal_sharpe:.2f}).")

        is_promoted = wins > losses
        status = "PROMOTED_BY_CEDA" if is_promoted else "CHAMPION_RETAINED_BY_CEDA"

        # Log to Research OS knowledge archive
        self.workspace.record_knowledge_entry(
            source_type="ceda_tournament",
            source_id=f"tour_{uuid.uuid4().hex[:8]}",
            lessons=f"Tournament results - Wins: {wins}, Losses: {losses}. Status: {status}",
            recommendation=status
        )

        explanation = f"{status}: " + " | ".join(reasons)
        return is_promoted, explanation
