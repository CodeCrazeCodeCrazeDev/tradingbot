import ast
import logging
from typing import Dict, List, Tuple

from .models import InvariantReport

logger = logging.getLogger("AlphaAlgo.SelfEvolution.Gate")


class InvariantGate:
    """
    Invariant Gate (IG).
    Acts as the authoritative, unbreachable missing control layer governing self-evolution.
    """

    def __init__(self, max_drawdown_limit: float = 15.0):
        self.max_drawdown_limit = max_drawdown_limit
        self.banned_calls = ["eval", "exec", "os.system", "subprocess"]
        self.banned_licenses = ["GPL", "AGPL", "LGPL"]

    def audit_mutant(
        self,
        code_str: str,
        metrics: Dict[str, float],
        license_name: str,
        is_stat_sig: bool
    ) -> InvariantReport:
        """Runs the four unbreachable audits to verify mutant compliance."""
        violations = []

        # 1. Security Invariant
        security_passed = True
        try:
            tree = ast.parse(code_str)
            for node in ast.walk(tree):
                if isinstance(node, ast.Call):
                    if isinstance(node.func, ast.Name) and node.func.id in self.banned_calls:
                        security_passed = False
                        violations.append(f"SECURITY_INVARIANT_VIOLATION: Call to banned function '{node.func.id}'")
                    elif isinstance(node.func, ast.Attribute):
                        full_attr = ""
                        if isinstance(node.func.value, ast.Name):
                            full_attr = f"{node.func.value.id}.{node.func.attr}"
                        if any(b_call in full_attr for b_call in self.banned_calls):
                            security_passed = False
                            violations.append(f"SECURITY_INVARIANT_VIOLATION: Call to banned attribute '{full_attr}'")
        except Exception as e:
            security_passed = False
            violations.append(f"CODE_COMPILE_ERROR: {str(e)}")

        # 2. Risk Invariant
        risk_passed = True
        drawdown = metrics.get("max_drawdown_pct", 0.0)
        if drawdown > self.max_drawdown_limit:
            risk_passed = False
            violations.append(f"RISK_INVARIANT_VIOLATION: Max Drawdown of {drawdown:.2f}% exceeds limit of {self.max_drawdown_limit:.2f}%")

        # 3. License Invariant
        license_passed = True
        lic_upper = license_name.upper()
        for banned in self.banned_licenses:
            if banned in lic_upper:
                license_passed = False
                violations.append(f"LICENSE_INVARIANT_VIOLATION: Banned copyleft license '{license_name}' detected")

        # 4. Validation Invariant (Out-of-sample must be statistically significant)
        validation_passed = is_stat_sig
        if not is_stat_sig:
            violations.append("VALIDATION_INVARIANT_VIOLATION: Out-Of-Sample performance is not statistically significant")

        is_valid = security_passed and risk_passed and license_passed and validation_passed
        return InvariantReport(
            is_valid=is_valid,
            security_passed=security_passed,
            risk_passed=risk_passed,
            license_passed=license_passed,
            validation_passed=validation_passed,
            violations=violations
        )
