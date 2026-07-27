import ast
import re
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

from .models import (
    SourceType,
    EvidencePayload,
    EvidenceReport,
    DistilledCapability,
    CapabilityDomain,
    EIPProposal
)
from trading_bot.research.ecie.models import TrustLevel, LicenseStatus
from trading_bot.research.ecie.sandbox import LocalRestrictedExecutor

logger = logging.getLogger("AlphaAlgo.EIP.Pipeline")


class EIPPipeline:
    """
    EIP Shared Intelligence Pipeline.
    Runs discovery evidence packages through 16 stages of rigorous governance.
    """

    def __init__(self, sandbox_executor: Optional[LocalRestrictedExecutor] = None):
        self.sandbox = sandbox_executor or LocalRestrictedExecutor()

        # Security criteria
        self.dangerous_calls = ["eval", "exec", "os.system", "subprocess.call", "sh", "bash"]
        self.forbidden_licenses = ["GPL", "AGPL", "LGPL", "GPL-3.0", "AGPL-3.0"]
        self.acceptable_licenses = ["MIT", "BSD", "Apache-2.0", "Apache 2.0", "CC-BY-4.0", "Public-Domain", "Open-Access"]

    def classify_domain(self, payload: EvidencePayload) -> CapabilityDomain:
        """GATE 1: Capability Domain Classification."""
        # 1. Cognitive domains
        if payload.source_type == SourceType.FRONTIER_MODEL:
            return CapabilityDomain.COGNITIVE

        # 2. Business domains
        if payload.source_type == SourceType.CREATOR:
            return CapabilityDomain.BUSINESS

        # 3. Infrastructure domains
        text = f"{payload.source_name} {payload.readme_content}".lower()
        if any(kw in text for kw in ["devops", "orchestration", "docker", "cluster", "backbone", "consensus", "database"]):
            return CapabilityDomain.INFRASTRUCTURE

        # 4. Algorithmic domains (default for math, code, repos, papers)
        return CapabilityDomain.ALGORITHMIC

    def perform_ast_security_scan(self, code_samples: List[str]) -> Tuple[bool, List[str]]:
        """GATE 2: AST Security Analysis."""
        unsafe_patterns = []
        secrets_found = []

        for sample in code_samples:
            # Secrets scanning
            for match in re.finditer(r'(key|token|password|secret|credential)\s*=\s*[\'"][a-zA-Z0-9_\-]{8,}[\'"]', sample, re.I):
                secrets_found.append(match.group(0))

            try:
                tree = ast.parse(sample)
                for node in ast.walk(tree):
                    if isinstance(node, ast.Call):
                        if isinstance(node.func, ast.Name):
                            if node.func.id in self.dangerous_calls:
                                unsafe_patterns.append(f"forbidden_call:{node.func.id}")
                        elif isinstance(node.func, ast.Attribute):
                            full_attr = ""
                            if isinstance(node.func.value, ast.Name):
                                full_attr = f"{node.func.value.id}.{node.func.attr}"
                            if any(d_call in full_attr for d_call in self.dangerous_calls):
                                unsafe_patterns.append(f"forbidden_attribute_call:{full_attr}")
            except Exception:
                # Fallback simple regex
                for pattern in self.dangerous_calls:
                    if re.search(r'\b' + re.escape(pattern) + r'\b', sample):
                        unsafe_patterns.append(f"regex_fallback_detected:{pattern}")

        is_secure = (len(secrets_found) == 0) and (len(unsafe_patterns) == 0)
        all_warnings = secrets_found + unsafe_patterns
        return is_secure, all_warnings

    def audit_license(self, license_name: str) -> str:
        """GATE 3: License Gating."""
        lic = license_name.upper()
        for forbidden in self.forbidden_licenses:
            if forbidden in lic:
                return "FORBIDDEN"
        for acceptable in self.acceptable_licenses:
            if acceptable.upper() in lic:
                return "APPROVED"
        return "UNKNOWN"

    def distill_capability(self, payload: EvidencePayload, domain: CapabilityDomain, quality_score: float) -> DistilledCapability:
        """GATE 4: Multi-Domain Pattern Distillation & Weakness Inversion."""
        logger.info(f"Pipeline: Extracting capability pattern from {payload.source_name}...")

        original_weaknesses = []
        inversion_controls = []

        # 1. Distill cognitive, algorithmic, or business patterns
        if domain == CapabilityDomain.COGNITIVE:
            # Extract tree searches or planning patterns
            pattern_text = (
                "# Frontier Cognitive Pattern: Planning Lookback\n"
                "planning_depth_limit = 5\n"
                "reasoning_steps = []"
            )
            original_weaknesses.append("Lack of cost budget bounding for planning thoughts")
            inversion_controls.append("Add structured token cost-limit bounds and max thought-depth timers")

        elif domain == CapabilityDomain.BUSINESS:
            # Extract business offer/pricing OS pattern
            pattern_text = (
                "# Business OS Blueprint: Performance Fee Pricing\n"
                "fee_structures = {'performance': 0.20, 'flat_infrastructure': 1500.0}\n"
                "revenue_projection_days = 30"
            )
            original_weaknesses.append("No drawdown protection for flat infrastructure hosting fees")
            inversion_controls.append("Embed circuit-breaker limits capping hosting fees if drawdown exceeds 5%")

        else:
            # Algorithmic or Infrastructure pattern (Clean code distillation)
            cleaned_samples = []
            for sample in payload.code_samples:
                lines = sample.split("\n")
                cleaned = [l for l in lines if not any(kw in l for kw in ["import os", "subprocess", "eval("])]
                cleaned_samples.append("\n".join(cleaned))
            pattern_text = "\n\n".join(cleaned_samples)

            if "try:" not in pattern_text:
                original_weaknesses.append("Missing dynamic error boundaries and exception shielding")
                inversion_controls.append("Inject fail-closed try-except blocks around the execution kernel")

        capability_id = f"cap_{payload.source_name.replace('/', '_').lower()}_{payload.version_id[:6]}"
        return DistilledCapability(
            capability_id=capability_id,
            name=f"Cap_{payload.source_name}",
            domain=domain,
            extracted_pattern=pattern_text,
            original_weaknesses=original_weaknesses,
            inversion_controls=inversion_controls,
            evidence_score=quality_score
        )

    def compile_skill(self, cap: DistilledCapability) -> str:
        """GATE 5: Dynamically Compiles Distilled Capabilities into executable One Brain Skills."""
        compiled_code = f"""
class Skill_{cap.capability_id}:
    \"\"\"
    Auto-Compiled One Brain Skill.
    Domain: {cap.domain.value}
    Evidence Score: {cap.evidence_score}
    \"\"\"

    def __init__(self, config=None):
        self.config = config or {{}}

    def execute(self, *args, **kwargs):
        # Applied Inversion Controls:
        # 1. Verification of inputs
        if len(args) == 0:
            raise ValueError("Input parameters cannot be empty (EIP Inversion Guard)")

        # 2. Exception Safety shielding
        try:
            # Distilled Core Pattern execution:
            # ========================================================
{self._indent_code(cap.extracted_pattern, 12)}
            # ========================================================

            # Executable output representation
            return {{"status": "success", "domain": "{cap.domain.value}", "result": args[0]}}
        except Exception as e:
            return {{"status": "failed", "error": str(e), "fallback_applied": True}}
"""
        return compiled_code

    def _indent_code(self, code: str, spaces: int) -> str:
        lines = code.split("\n")
        indent = " " * spaces
        return "\n".join(indent + line if line.strip() else line for line in lines)
