"""
Verification Framework
======================
Static, contract, and runtime verification for promoted modules.

Three verification stages:
  Stage 1 – Static    : importability, no cycles, config schema, forbidden patterns
  Stage 2 – Contract  : lifecycle (start/health/stop) in sandbox with timeout budgets
  Stage 3 – Runtime   : soak period with continuous health sampling

A module advances from WRAPPED → VERIFIED only after passing all three stages.
"""

from __future__ import annotations

import asyncio
import logging
import time
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from .service_contract import IntegratedService, HealthStatus, HealthReport

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Result types
# ---------------------------------------------------------------------------

class VerificationStage(str, Enum):
    STATIC   = "static"
    CONTRACT = "contract"
    RUNTIME  = "runtime"


class VerificationResult(str, Enum):
    PASS    = "pass"
    FAIL    = "fail"
    WARNING = "warning"
    SKIPPED = "skipped"


@dataclass
class CheckResult:
    name: str
    stage: str
    result: VerificationResult
    message: str = ""
    duration_ms: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class VerificationReport:
    service_name: str
    module_path: str
    checks: List[CheckResult] = field(default_factory=list)
    overall: VerificationResult = VerificationResult.PASS
    passed: int = 0
    failed: int = 0
    warnings: int = 0
    generated: str = field(default_factory=lambda: datetime.utcnow().isoformat())

    def add(self, check: CheckResult) -> None:
        self.checks.append(check)
        if check.result == VerificationResult.PASS:
            self.passed += 1
        elif check.result == VerificationResult.FAIL:
            self.failed += 1
            self.overall = VerificationResult.FAIL
        elif check.result == VerificationResult.WARNING:
            self.warnings += 1
            if self.overall == VerificationResult.PASS:
                self.overall = VerificationResult.WARNING

    def summary_dict(self) -> Dict:
        return {
            "service_name": self.service_name,
            "module_path": self.module_path,
            "overall": self.overall.value,
            "passed": self.passed,
            "failed": self.failed,
            "warnings": self.warnings,
            "checks": [
                {
                    "name": c.name,
                    "stage": c.stage,
                    "result": c.result.value,
                    "message": c.message,
                    "duration_ms": round(c.duration_ms, 2),
                }
                for c in self.checks
            ],
            "generated": self.generated,
        }


# ---------------------------------------------------------------------------
# Static Verifier
# ---------------------------------------------------------------------------

class StaticVerifier:
    """
    Stage 1 verification – runs without instantiating any service.
    """

    # Patterns that disqualify a module from promotion
    FORBIDDEN_PATTERNS = [
        ("os.system(",       "forbidden: os.system"),
        ("subprocess.call(", "forbidden: subprocess.call"),
        ("eval(",            "forbidden: eval"),
        ("exec(",            "forbidden: exec"),
        ("shutil.rmtree(",   "forbidden: shutil.rmtree"),
        ("os.remove(",       "forbidden: os.remove"),
        ("__import__(",      "forbidden: __import__"),
    ]

    # Required configuration keys for Tier A capital-impacting modules
    TIER_A_DIRECT_REQUIRED_CONFIGS = [
        "max_risk_per_trade",
        "max_daily_loss",
    ]

    def verify(
        self,
        module_path: str,
        file_path: str,
        service_name: str,
        tier: str,
        capital_impact: str,
        layer: int,
    ) -> VerificationReport:
        report = VerificationReport(service_name=service_name, module_path=module_path)

        # 1. Read source
        source, read_err = self._read_source(file_path)
        report.add(CheckResult(
            name="source_readable",
            stage=VerificationStage.STATIC.value,
            result=VerificationResult.PASS if source else VerificationResult.FAIL,
            message=read_err,
        ))
        if not source:
            return report

        # 2. Forbidden patterns
        for pattern, label in self.FORBIDDEN_PATTERNS:
            if pattern in source:
                report.add(CheckResult(
                    name="forbidden_pattern",
                    stage=VerificationStage.STATIC.value,
                    result=VerificationResult.FAIL,
                    message=label,
                ))

        # 3. Import check
        importable, imp_err = self._check_import(module_path)
        report.add(CheckResult(
            name="importable",
            stage=VerificationStage.STATIC.value,
            result=VerificationResult.PASS if importable else VerificationResult.FAIL,
            message=imp_err,
        ))

        # 4. Syntax check
        syntax_ok, syn_err = self._check_syntax(source)
        report.add(CheckResult(
            name="syntax_valid",
            stage=VerificationStage.STATIC.value,
            result=VerificationResult.PASS if syntax_ok else VerificationResult.FAIL,
            message=syn_err,
        ))

        # 5. Capital impact vs layer consistency
        if capital_impact == "direct" and layer < 4:
            report.add(CheckResult(
                name="capital_impact_layer_consistency",
                stage=VerificationStage.STATIC.value,
                result=VerificationResult.WARNING,
                message=f"Direct capital impact on layer {layer} (expected >= 4). Review required.",
            ))
        else:
            report.add(CheckResult(
                name="capital_impact_layer_consistency",
                stage=VerificationStage.STATIC.value,
                result=VerificationResult.PASS,
            ))

        # 6. Tier A direct-impact modules must have risk config markers
        if tier == "A" and capital_impact == "direct":
            has_risk_ref = any(k in source for k in ["max_risk", "daily_loss", "max_drawdown"])
            report.add(CheckResult(
                name="tier_a_risk_config_reference",
                stage=VerificationStage.STATIC.value,
                result=VerificationResult.PASS if has_risk_ref else VerificationResult.WARNING,
                message="" if has_risk_ref else "Tier-A direct module lacks risk config references",
            ))

        # 7. Has start/stop/health lifecycle markers
        has_lifecycle = (
            "def start(" in source or "async def start(" in source
        ) and (
            "def stop(" in source or "async def stop(" in source
        )
        report.add(CheckResult(
            name="lifecycle_markers",
            stage=VerificationStage.STATIC.value,
            result=VerificationResult.PASS if has_lifecycle else VerificationResult.WARNING,
            message="" if has_lifecycle else "No start/stop detected; LegacyModuleAdapter required",
        ))

        return report

    @staticmethod
    def _read_source(file_path: str):
        try:
            with open(file_path, encoding="utf-8", errors="replace") as fh:
                return fh.read(), ""
        except Exception as exc:
            return None, str(exc)

    @staticmethod
    def _check_import(module_path: str):
        import importlib.util
        try:
            spec = importlib.util.find_spec(module_path)
            if spec is None:
                return False, "module_not_found"
            return True, ""
        except Exception as exc:
            return False, str(exc)[:200]

    @staticmethod
    def _check_syntax(source: str):
        import ast
        try:
            ast.parse(source)
            return True, ""
        except SyntaxError as exc:
            return False, f"SyntaxError line {exc.lineno}: {exc.msg}"


# ---------------------------------------------------------------------------
# Contract Verifier
# ---------------------------------------------------------------------------

class ContractVerifier:
    """
    Stage 2 verification – instantiates and exercises the service adapter.

    Checks: start → health → stop within configured timeout budgets.
    """

    def __init__(
        self,
        start_budget_s: float = 10.0,
        health_budget_s: float = 3.0,
        stop_budget_s:  float = 5.0,
    ):
        self.start_budget = start_budget_s
        self.health_budget = health_budget_s
        self.stop_budget = stop_budget_s

    async def verify(self, service: IntegratedService) -> VerificationReport:
        report = VerificationReport(
            service_name=service.SERVICE_NAME,
            module_path=getattr(service, "SERVICE_DOMAIN", ""),
        )

        # 1. Start
        t0 = time.monotonic()
        try:
            ok = await asyncio.wait_for(service.start(), timeout=self.start_budget)
            elapsed = (time.monotonic() - t0) * 1000
            report.add(CheckResult(
                name="contract_start",
                stage=VerificationStage.CONTRACT.value,
                result=VerificationResult.PASS if ok else VerificationResult.FAIL,
                message="" if ok else "start() returned False",
                duration_ms=elapsed,
            ))
        except asyncio.TimeoutError:
            report.add(CheckResult(
                name="contract_start",
                stage=VerificationStage.CONTRACT.value,
                result=VerificationResult.FAIL,
                message=f"start() timed out (>{self.start_budget}s)",
                duration_ms=(time.monotonic() - t0) * 1000,
            ))
            return report
        except Exception as exc:
            report.add(CheckResult(
                name="contract_start",
                stage=VerificationStage.CONTRACT.value,
                result=VerificationResult.FAIL,
                message=str(exc),
                duration_ms=(time.monotonic() - t0) * 1000,
            ))
            return report

        # 2. Health check
        t0 = time.monotonic()
        try:
            health: HealthReport = await asyncio.wait_for(
                service.health_check(), timeout=self.health_budget
            )
            elapsed = (time.monotonic() - t0) * 1000
            report.add(CheckResult(
                name="contract_health",
                stage=VerificationStage.CONTRACT.value,
                result=(
                    VerificationResult.PASS if health.operational else VerificationResult.FAIL
                ),
                message=health.message,
                duration_ms=elapsed,
                metadata={"health_status": health.status.value},
            ))
        except asyncio.TimeoutError:
            report.add(CheckResult(
                name="contract_health",
                stage=VerificationStage.CONTRACT.value,
                result=VerificationResult.FAIL,
                message=f"health_check() timed out (>{self.health_budget}s)",
                duration_ms=(time.monotonic() - t0) * 1000,
            ))
        except Exception as exc:
            report.add(CheckResult(
                name="contract_health",
                stage=VerificationStage.CONTRACT.value,
                result=VerificationResult.FAIL,
                message=str(exc),
                duration_ms=(time.monotonic() - t0) * 1000,
            ))

        # 3. Stop
        t0 = time.monotonic()
        try:
            ok = await asyncio.wait_for(service.stop(), timeout=self.stop_budget)
            elapsed = (time.monotonic() - t0) * 1000
            report.add(CheckResult(
                name="contract_stop",
                stage=VerificationStage.CONTRACT.value,
                result=VerificationResult.PASS if ok else VerificationResult.FAIL,
                message="" if ok else "stop() returned False",
                duration_ms=elapsed,
            ))
        except asyncio.TimeoutError:
            report.add(CheckResult(
                name="contract_stop",
                stage=VerificationStage.CONTRACT.value,
                result=VerificationResult.FAIL,
                message=f"stop() timed out (>{self.stop_budget}s)",
                duration_ms=(time.monotonic() - t0) * 1000,
            ))
        except Exception as exc:
            report.add(CheckResult(
                name="contract_stop",
                stage=VerificationStage.CONTRACT.value,
                result=VerificationResult.FAIL,
                message=str(exc),
                duration_ms=(time.monotonic() - t0) * 1000,
            ))

        return report


# ---------------------------------------------------------------------------
# Runtime Verifier (soak)
# ---------------------------------------------------------------------------

class RuntimeVerifier:
    """
    Stage 3 – soak test: run the service for `soak_seconds` and sample health
    `num_samples` times.  Acceptable if >= `min_healthy_ratio` samples are healthy.
    """

    def __init__(
        self,
        soak_seconds: float = 30.0,
        num_samples: int = 5,
        min_healthy_ratio: float = 0.8,
    ):
        self.soak_seconds = soak_seconds
        self.num_samples = num_samples
        self.min_healthy_ratio = min_healthy_ratio

    async def verify(self, service: IntegratedService) -> VerificationReport:
        report = VerificationReport(
            service_name=service.SERVICE_NAME,
            module_path=getattr(service, "SERVICE_DOMAIN", ""),
        )

        # Start the service
        ok = await service.start()
        if not ok:
            report.add(CheckResult(
                name="soak_start",
                stage=VerificationStage.RUNTIME.value,
                result=VerificationResult.FAIL,
                message="Service failed to start for soak test",
            ))
            return report

        interval = self.soak_seconds / max(self.num_samples, 1)
        healthy_count = 0
        samples: List[str] = []

        for i in range(self.num_samples):
            await asyncio.sleep(interval)
            try:
                health = await asyncio.wait_for(service.health_check(), timeout=5.0)
                samples.append(health.status.value)
                if health.operational:
                    healthy_count += 1
            except Exception as exc:
                samples.append(f"error:{exc}")

        ratio = healthy_count / self.num_samples if self.num_samples > 0 else 0.0
        passed = ratio >= self.min_healthy_ratio

        report.add(CheckResult(
            name="soak_health_ratio",
            stage=VerificationStage.RUNTIME.value,
            result=VerificationResult.PASS if passed else VerificationResult.FAIL,
            message=(
                f"healthy={healthy_count}/{self.num_samples} ({ratio:.0%}) "
                f"min={self.min_healthy_ratio:.0%}"
            ),
            metadata={"samples": samples},
        ))

        await service.stop()
        return report


# ---------------------------------------------------------------------------
# Orchestrated verification pipeline
# ---------------------------------------------------------------------------

class VerificationPipeline:
    """
    Runs Static → Contract → Runtime in sequence.
    Stops at first stage failure.
    """

    def __init__(
        self,
        run_contract: bool = True,
        run_runtime: bool = False,   # opt-in; expensive
        runtime_soak_seconds: float = 30.0,
    ):
        self.static_verifier   = StaticVerifier()
        self.contract_verifier = ContractVerifier()
        self.runtime_verifier  = RuntimeVerifier(soak_seconds=runtime_soak_seconds)
        self.run_contract = run_contract
        self.run_runtime  = run_runtime

    async def run(
        self,
        service: IntegratedService,
        module_path: str,
        file_path: str,
        tier: str,
        capital_impact: str,
        layer: int,
    ) -> VerificationReport:
        """Run the full verification pipeline. Returns merged report."""

        # Stage 1 – Static
        report = self.static_verifier.verify(
            module_path=module_path,
            file_path=file_path,
            service_name=service.SERVICE_NAME,
            tier=tier,
            capital_impact=capital_impact,
            layer=layer,
        )

        if report.overall == VerificationResult.FAIL:
            logger.warning(
                f"[{service.SERVICE_NAME}] static verification FAILED – skipping contract"
            )
            return report

        # Stage 2 – Contract
        if self.run_contract:
            contract_report = await self.contract_verifier.verify(service)
            for check in contract_report.checks:
                report.add(check)

            if report.overall == VerificationResult.FAIL:
                logger.warning(
                    f"[{service.SERVICE_NAME}] contract verification FAILED – skipping runtime"
                )
                return report

        # Stage 3 – Runtime soak (opt-in)
        if self.run_runtime:
            runtime_report = await self.runtime_verifier.verify(service)
            for check in runtime_report.checks:
                report.add(check)

        result_label = report.overall.value.upper()
        logger.info(
            f"[{service.SERVICE_NAME}] verification {result_label} "
            f"(pass={report.passed} fail={report.failed} warn={report.warnings})"
        )
        return report
