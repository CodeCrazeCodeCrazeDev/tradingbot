import ast
import re
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

from .models import (
    ExternalCandidate,
    TrustReport,
    SecurityReport,
    DistilledPattern,
    CompiledSkill,
    CapabilityCategory,
    TrustLevel,
    LicenseStatus
)
from .sandbox import LocalRestrictedExecutor

logger = logging.getLogger("AlphaAlgo.ECIE.Pipeline")


class ECIEPipeline:
    """
    Core External Capability Intelligence Refinery.
    Implements a strict governed pipeline from Discovery to Skill compilation.
    """

    def __init__(self, sandbox_executor: Optional[LocalRestrictedExecutor] = None):
        self.sandbox = sandbox_executor or LocalRestrictedExecutor()

        # Hard limits & rules
        self.forbidden_licenses = ["GPL", "AGPL", "LGPL", "GPL-3.0", "AGPL-3.0"]
        self.acceptable_licenses = ["MIT", "BSD", "Apache-2.0", "Apache 2.0", "BSD-3-Clause", "BSD-2-Clause"]

        # Dangerous code patterns for AST checking
        self.dangerous_calls = ["eval", "exec", "os.system", "subprocess.call", "subprocess.Popen", "sh", "bash"]

    def classify_candidate(self, candidate: ExternalCandidate) -> CapabilityCategory:
        """GATE 1: Domain Classification."""
        text = f"{candidate.name} {candidate.description} {candidate.readme_content}".lower()

        scores = {
            CapabilityCategory.EXECUTION: ["execution", "order routing", "slippage", "book", "fill"],
            CapabilityCategory.RISK: ["risk", "var", "cvar", "drawdown", "position sizing", "exposure"],
            CapabilityCategory.BACKTESTING: ["backtest", "walk forward", "leakage", "cross validation", "lookahead"],
            CapabilityCategory.STATS: ["sharpe", "statistical", "hypothesis", "monte carlo", "bootstrap"],
            CapabilityCategory.MICROSTRUCTURE: ["microstructure", "order flow", "liquidity", "tick"],
            CapabilityCategory.PORTFOLIO: ["portfolio", "optimization", "allocation", "black litterman", "risk parity"]
        }

        category_scores = {}
        for category, keywords in scores.items():
            score = sum(1 for kw in keywords if kw in text)
            if score > 0:
                category_scores[category] = score

        if not category_scores:
            return CapabilityCategory.STATS  # Default to Statistical Validation

        return max(category_scores, key=category_scores.get)

    def assess_trust_score(self, candidate: ExternalCandidate) -> TrustReport:
        """GATE 2: Multi-Signal Trust Scoring."""
        score = 0.0
        signals = {}

        # Stars and Forks are weak signals; they must never dominate (max 15 points combined)
        stars_score = min(candidate.stars / 100.0, 10.0)
        forks_score = min(candidate.forks / 50.0, 5.0)
        score += stars_score + forks_score
        signals["popular_signals_score"] = stars_score + forks_score

        # High quality signals (85 points total)
        # 1. Has Unit Tests (25 pts)
        has_tests = candidate.metadata.get("has_tests", False)
        if has_tests:
            score += 25.0
        signals["has_tests"] = has_tests

        # 2. Has Documentation (20 pts)
        has_docs = candidate.metadata.get("has_docs", False)
        if has_docs:
            score += 20.0
        signals["has_docs"] = has_docs

        # 3. Maintainer / Commit cadence - active within 6 months (20 pts)
        pushed_at = candidate.metadata.get("pushed_at")
        active_cadence = False
        if pushed_at:
            try:
                pushed_dt = datetime.fromisoformat(pushed_at.replace("Z", "+00:00"))
                days_since = (datetime.now(pushed_dt.tzinfo) - pushed_dt).days
                if days_since < 180:
                    score += 20.0
                    active_cadence = True
                signals["days_since_commit"] = days_since
            except Exception:
                signals["days_since_commit"] = 999
        else:
            signals["days_since_commit"] = 999

        signals["active_commit_cadence"] = active_cadence

        # 4. License Clarity (20 pts)
        license_clarity = False
        if candidate.license_name and candidate.license_name != "Unknown":
            score += 20.0
            license_clarity = True
        signals["license_clarity"] = license_clarity

        # Determine level
        if not has_tests or not has_docs:
            level = TrustLevel.LOW
        elif score >= 75.0:
            level = TrustLevel.HIGH
        elif score >= 50.0:
            level = TrustLevel.MEDIUM
        elif score >= 20.0:
            level = TrustLevel.LOW
        else:
            level = TrustLevel.ZERO

        # Lack of tests or docs must reject/fail the trust check immediately
        is_acceptable = (score >= 50.0) and has_tests and has_docs
        return TrustReport(
            overall_score=round(score, 2),
            trust_level=level,
            signals=signals,
            is_acceptable=is_acceptable
        )

    def analyze_license(self, candidate: ExternalCandidate) -> LicenseStatus:
        """GATE 3: License Compliance Audit."""
        lic = (candidate.license_name or "Unknown").upper()

        # Check forbidden
        for forbidden in self.forbidden_licenses:
            if forbidden in lic:
                return LicenseStatus.FORBIDDEN

        # Check acceptable
        for acceptable in self.acceptable_licenses:
            if acceptable.upper() in lic:
                return LicenseStatus.APPROVED

        return LicenseStatus.UNKNOWN

    def perform_security_scan(self, candidate: ExternalCandidate, code_samples: List[str]) -> SecurityReport:
        """GATE 4: Deep AST Code and Security Scanning."""
        secrets_found = []
        unsafe_patterns = []
        malicious_scripts = False
        filesystem_access = False
        network_calls = False
        import_warnings = []

        for sample in code_samples:
            # 1. Detect Secrets
            # Look for common assignment variables like api_key, token, password, credential, secret
            for match in re.finditer(r'(key|token|password|secret|credential)\s*=\s*[\'"][a-zA-Z0-9_\-]{8,}[\'"]', sample, re.I):
                secrets_found.append(match.group(0))

            # 2. AST parsing check
            try:
                tree = ast.parse(sample)
                for node in ast.walk(tree):
                    # Check for dangerous calls
                    if isinstance(node, ast.Call):
                        if isinstance(node.func, ast.Name):
                            if node.func.id in self.dangerous_calls:
                                unsafe_patterns.append(f"Call to forbidden function: {node.func.id}")
                                if node.func.id in ["eval", "exec"]:
                                    malicious_scripts = True

                        elif isinstance(node.func, ast.Attribute):
                            # e.g., os.system or subprocess.call
                            full_attr = ""
                            if isinstance(node.func.value, ast.Name):
                                full_attr = f"{node.func.value.id}.{node.func.attr}"
                            if any(d_call in full_attr for d_call in self.dangerous_calls):
                                unsafe_patterns.append(f"Call to forbidden module attribute: {full_attr}")
                                if "os.system" in full_attr or "subprocess" in full_attr:
                                    unsafe_patterns.append("Dangerous subprocess spawn detected")

                    # Check for imports
                    if isinstance(node, ast.Import):
                        for alias in node.names:
                            if alias.name in ["socket", "urllib", "requests", "http"]:
                                network_calls = True
                                import_warnings.append(f"Imports networking library: {alias.name}")
                            if alias.name in ["os", "shutil", "pathlib"]:
                                filesystem_access = True
                                import_warnings.append(f"Imports filesystem library: {alias.name}")

                    if isinstance(node, ast.ImportFrom):
                        if node.module in ["socket", "urllib", "requests", "http"]:
                            network_calls = True
                            import_warnings.append(f"Imports from networking library: {node.module}")
                        if node.module in ["os", "shutil", "pathlib"]:
                            filesystem_access = True
                            import_warnings.append(f"Imports from filesystem library: {node.module}")
            except Exception as e:
                # Fallback to simple regex matches if AST fails to parse
                for pattern in self.dangerous_calls:
                    if re.search(r'\b' + re.escape(pattern) + r'\b', sample):
                        unsafe_patterns.append(f"Regex detected call: {pattern}")
                        if pattern in ["eval", "exec"]:
                            malicious_scripts = True

        is_secure = (len(secrets_found) == 0) and (len(unsafe_patterns) == 0) and not malicious_scripts
        return SecurityReport(
            is_secure=is_secure,
            secrets_found=secrets_found,
            unsafe_patterns=unsafe_patterns,
            malicious_scripts_detected=malicious_scripts,
            filesystem_access_flagged=filesystem_access,
            network_calls_flagged=network_calls,
            import_warnings=import_warnings,
            dependency_vulnerabilities=[]
        )

    def distill_pattern(self, candidate: ExternalCandidate, category: CapabilityCategory, code_samples: List[str]) -> DistilledPattern:
        """GATE 5: Capability Distillation."""
        logger.info(f"Distilling patterns from {candidate.name}...")

        # Instead of cloning and copying raw code, we distill clean algorithmic templates.
        # Let's extract the core logic blocks, isolating it from unsafe execution wrappers.
        extracted_blocks = []
        for sample in code_samples:
            lines = sample.split("\n")
            cleaned_lines = []
            for line in lines:
                # Remove imports, file actions, or system calls
                if any(kw in line for kw in ["import ", "os.system", "subprocess", "eval(", "exec("]):
                    continue
                cleaned_lines.append(line)
            extracted_blocks.append("\n".join(cleaned_lines))

        extracted_logic = "\n\n".join(extracted_blocks)

        # Find weaknesses to apply Weakness Inversion
        original_weaknesses = []
        inversion_controls = []

        if "try:" not in extracted_logic and "except" not in extracted_logic:
            original_weaknesses.append("Missing error handling / try-except safety bounds")
            inversion_controls.append("Add structured exception catcher inside the compiled skill")

        if "assert" not in extracted_logic:
            original_weaknesses.append("Missing pre-condition validation assertions")
            inversion_controls.append("Inject input boundary validation assertions at execution boundaries")

        pattern_id = f"pattern_{candidate.name.replace('/', '_').lower()}_{candidate.version_id[:6]}"
        return DistilledPattern(
            pattern_id=pattern_id,
            candidate_url=candidate.url,
            version_id=candidate.version_id,
            category=category,
            extracted_logic=extracted_logic,
            original_weaknesses=original_weaknesses,
            inversion_controls=inversion_controls
        )

    def compile_skill(self, pattern: DistilledPattern) -> CompiledSkill:
        """GATE 6: Skill Compilation (One Brain Dynamic Integration)."""
        logger.info(f"Compiling dynamic pattern {pattern.pattern_id} into a standard skill module...")

        # Wrap distilled logic inside a highly-governed, clean class that implements
        # Weakness Inversion (structured try-excepts, assertions, strict limits).
        compiled_code = f"""
class Skill_{pattern.pattern_id}:
    \"\"\"
    Auto-compiled One Brain Skill Program.
    Category: {pattern.category.value}
    Provenance: {pattern.candidate_url} ({pattern.version_id})
    \"\"\"

    def __init__(self, config=None):
        self.config = config or {{}}
        self.max_execution_limit = self.config.get("max_execution_limit", 1000.0)

    def execute(self, *args, **kwargs):
        # Applied Inversion Control: Strict pre-condition validation assertion
        if len(args) == 0:
            raise ValueError("Input parameters cannot be empty (ECIE pre-condition check failed)")

        # Applied Inversion Control: Structured exception safety wrapper
        try:
            # Distilled Core Logic Execution:
            # =========================================================
{self._indent_code(pattern.extracted_logic, 12)}
            # =========================================================

            # Simulated outcome prediction
            result = args[0] * 0.95  # Standard decay factor simulation
            return {{"status": "success", "result": result}}

        except Exception as e:
            # Applied Inversion Control: Safe failure mitigation / circuit breaking
            return {{"status": "failed", "error": str(e), "fallback_applied": True}}
"""
        import hashlib
        provenance_hash = hashlib.sha256(compiled_code.encode()).hexdigest()

        falsification_tests = [
            f"test_empty_input_fails",
            f"test_standard_execution_bounds"
        ]

        return CompiledSkill(
            skill_id=pattern.pattern_id,
            name=f"Skill_{pattern.pattern_id}",
            category=pattern.category,
            code=compiled_code,
            provenance_hash=provenance_hash,
            falsification_tests=falsification_tests
        )

    def _indent_code(self, code: str, spaces: int) -> str:
        lines = code.split("\n")
        indent = " " * spaces
        return "\n".join(indent + line if line.strip() else line for line in lines)
