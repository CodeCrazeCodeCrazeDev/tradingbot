"""
Self-Healing AI Orchestrator
Master coordinator for all validators - addresses 1000+ critical questions.
"""

import asyncio
import hashlib
import logging
import time
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

from .core import (
    BaseValidator, ValidationCategory, ValidationSeverity, ValidationIssue,
    RemediationAction, RemediationStatus, ValidationReport, SystemState,
    SystemHealth, StateManager, IMMUTABLE_LIMITS
)

logger = logging.getLogger(__name__)


class SelfHealingOrchestrator:
    """
    Master orchestrator for the Self-Healing AI Validator System.
    
    Coordinates all 16 validator categories covering 1000+ critical questions:
    1. System Architecture (Q1-50)
    2. Data Integrity (Q51-130)
    3. Market Microstructure (Q131-200)
    4. Strategy Lifecycle (Q201-270)
    5. ML/Models (Q271-400)
    6. Risk Management (Q401-470)
    7. Infrastructure (Q471-530)
    8. Backtesting (Q531-590)
    9. Research/Production (Q591-650)
    10. Self-Modification (Q651-710)
    11. Security (Q711-780)
    12. Configuration (Q781-830)
    13. Monitoring (Q831-890)
    14. Kill-Switches (Q891-930)
    15. Regulatory (Q931-970)
    16. Capital/Scalability (Q971-1000)
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
        self._validators: Dict[str, BaseValidator] = {}
        self._state_manager = StateManager()
        self._initialized = False
        self._running = False
        self._last_report: Optional[ValidationReport] = None
        self._auto_remediate = self.config.get('auto_remediate', True)
        self._validation_interval = self.config.get('validation_interval_seconds', 60)
    
    async def initialize(self) -> None:
        """Initialize all validators."""
        if self._initialized:
            return
        
        self.logger.info("Initializing Self-Healing AI Orchestrator...")
        
        # Import and instantiate all validators
        from .validators import (
            SystemArchitectureValidator,
            DataIntegrityValidator,
            ExecutionValidator,
            StrategyValidator,
            MLModelValidator,
            RiskValidator,
            InfrastructureValidator,
            BacktestValidator,
            ResearchProductionValidator,
            SelfModificationValidator,
            SecurityValidator,
            ConfigurationValidator,
            MonitoringValidator,
            KillSwitchValidator,
            RegulatoryValidator,
            CapitalValidator,
        )
        
        self._validators = {
            'system_architecture': SystemArchitectureValidator(),
            'data_integrity': DataIntegrityValidator(),
            'execution': ExecutionValidator(),
            'strategy': StrategyValidator(),
            'ml_models': MLModelValidator(),
            'risk': RiskValidator(),
            'infrastructure': InfrastructureValidator(),
            'backtest': BacktestValidator(),
            'research_production': ResearchProductionValidator(),
            'self_modification': SelfModificationValidator(),
            'security': SecurityValidator(),
            'configuration': ConfigurationValidator(),
            'monitoring': MonitoringValidator(),
            'kill_switch': KillSwitchValidator(),
            'regulatory': RegulatoryValidator(),
            'capital': CapitalValidator(),
        }
        
        self._initialized = True
        self.logger.info(f"Initialized {len(self._validators)} validators covering 1000+ questions")
    
    async def run_full_validation(self) -> ValidationReport:
        """Run all validators and generate comprehensive report."""
        if not self._initialized:
            await self.initialize()
        
        start_time = time.time()
        state = self._state_manager.get_state()
        
        all_issues: List[ValidationIssue] = []
        all_remediations: List[RemediationAction] = []
        category_scores: Dict[str, float] = {}
        total_checks = 0
        passed_checks = 0
        
        self.logger.info("Starting full system validation...")
        
        # Run all validators in parallel
        validation_tasks = []
        for name, validator in self._validators.items():
            validation_tasks.append(self._run_validator(name, validator, state))
        
        results = await asyncio.gather(*validation_tasks, return_exceptions=True)
        
        # Process results
        for name, result in zip(self._validators.keys(), results):
            if isinstance(result, Exception):
                self.logger.error(f"Validator {name} failed: {result}")
                all_issues.append(ValidationIssue(
                    issue_id=self._generate_id(f"validator_failure_{name}"),
                    question_id=0,
                    category=ValidationCategory.SYSTEM_ARCHITECTURE,
                    severity=ValidationSeverity.HIGH,
                    title=f"Validator failed: {name}",
                    description=str(result),
                    affected_components=[name],
                ))
                category_scores[name] = 0.0
            else:
                issues, checks, passed = result
                all_issues.extend(issues)
                total_checks += checks
                passed_checks += passed
                category_scores[name] = passed / checks if checks > 0 else 1.0
        
        # Auto-remediate if enabled
        if self._auto_remediate:
            for issue in all_issues:
                if issue.auto_remediate and issue.remediation_available:
                    remediation = await self._remediate_issue(issue)
                    all_remediations.append(remediation)
        
        # Determine system health
        critical_count = sum(1 for i in all_issues if i.severity == ValidationSeverity.CRITICAL)
        high_count = sum(1 for i in all_issues if i.severity == ValidationSeverity.HIGH)
        
        if critical_count > 0:
            system_health = SystemHealth.CRITICAL
        elif high_count > 5:
            system_health = SystemHealth.DEGRADED
        elif high_count > 0:
            system_health = SystemHealth.DEGRADED
        else:
            system_health = SystemHealth.HEALTHY
        
        # Generate recommendations
        recommendations = self._generate_recommendations(all_issues)
        
        execution_time = (time.time() - start_time) * 1000
        
        report = ValidationReport(
            report_id=self._generate_id("report"),
            generated_at=datetime.utcnow(),
            system_health=system_health,
            total_checks=total_checks,
            passed_checks=passed_checks,
            failed_checks=total_checks - passed_checks,
            issues=all_issues,
            remediations=all_remediations,
            category_scores=category_scores,
            recommendations=recommendations,
            execution_time_ms=execution_time,
        )
        
        # Store report
        self._last_report = report
        
        # Log summary
        self.logger.info(
            f"Validation complete: {passed_checks}/{total_checks} checks passed, "
            f"{len(all_issues)} issues found, health={system_health.value}, "
            f"time={execution_time:.1f}ms"
        )
        
        return report
    
    async def _run_validator(
        self, 
        name: str, 
        validator: BaseValidator, 
        state: SystemState
    ) -> Tuple[List[ValidationIssue], int, int]:
        """Run a single validator and return results."""
        try:
            issues = await validator.validate(state)
            
            # Count checks (estimate based on registered checks)
            total_checks = len(validator._checks)
            passed_checks = total_checks - len(issues)
            
            # Record issues
            for issue in issues:
                self._state_manager.record_issue(issue)
            
            return issues, total_checks, max(0, passed_checks)
        except Exception as e:
            self.logger.error(f"Validator {name} error: {e}")
            raise
    
    async def _remediate_issue(self, issue: ValidationIssue) -> RemediationAction:
        """Attempt to remediate an issue."""
        validator_name = issue.category.value.replace('_', ' ').title().replace(' ', '')
        
        for name, validator in self._validators.items():
            if validator.category == issue.category:
                return await validator.remediate(issue)
        
        # No validator found
        return RemediationAction(
            action_id=self._generate_id(f"remediation_{issue.issue_id}"),
            issue_id=issue.issue_id,
            action_type="unknown",
            description=f"No remediation handler for {issue.category.value}",
            status=RemediationStatus.REQUIRES_HUMAN,
        )
    
    def _generate_recommendations(self, issues: List[ValidationIssue]) -> List[str]:
        """Generate actionable recommendations based on issues."""
        recommendations = []
        
        # Group by category
        by_category: Dict[ValidationCategory, List[ValidationIssue]] = {}
        for issue in issues:
            if issue.category not in by_category:
                by_category[issue.category] = []
            by_category[issue.category].append(issue)
        
        # Generate category-specific recommendations
        for category, cat_issues in by_category.items():
            critical = [i for i in cat_issues if i.severity == ValidationSeverity.CRITICAL]
            high = [i for i in cat_issues if i.severity == ValidationSeverity.HIGH]
            
            if critical:
                recommendations.append(
                    f"CRITICAL: Address {len(critical)} critical issues in {category.value} immediately"
                )
            
            if high:
                recommendations.append(
                    f"HIGH: Review {len(high)} high-severity issues in {category.value}"
                )
        
        # Add general recommendations
        if not issues:
            recommendations.append("System is healthy. Continue monitoring.")
        elif len(issues) > 50:
            recommendations.append(
                "High issue count detected. Consider scheduling a comprehensive system review."
            )
        
        return recommendations[:10]  # Limit to top 10
    
    def _generate_id(self, prefix: str) -> str:
        """Generate unique ID."""
        content = f"{prefix}:{datetime.utcnow().isoformat()}"
        return hashlib.sha256(content.encode()).hexdigest()[:16]
    
    async def start_continuous_validation(self) -> None:
        """Start continuous validation loop."""
        if not self._initialized:
            await self.initialize()
        
        self._running = True
        self.logger.info(f"Starting continuous validation (interval={self._validation_interval}s)")
        
        while self._running:
            try:
                report = await self.run_full_validation()
                
                # Handle critical issues
                critical_issues = report.get_critical_issues()
                if critical_issues:
                    self.logger.critical(
                        f"CRITICAL: {len(critical_issues)} critical issues detected!"
                    )
                    for issue in critical_issues:
                        self.logger.critical(f"  - {issue.title}: {issue.description}")
                
                await asyncio.sleep(self._validation_interval)
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"Validation loop error: {e}")
                await asyncio.sleep(5)  # Brief pause before retry
        
        self.logger.info("Continuous validation stopped")
    
    def stop_continuous_validation(self) -> None:
        """Stop continuous validation loop."""
        self._running = False
    
    def get_last_report(self) -> Optional[ValidationReport]:
        """Get the most recent validation report."""
        return self._last_report
    
    def get_system_health(self) -> SystemHealth:
        """Get current system health."""
        if self._last_report:
            return self._last_report.system_health
        return SystemHealth.UNKNOWN
    
    def get_state(self) -> SystemState:
        """Get current system state."""
        return self._state_manager.get_state()
    
    def update_state(self, **kwargs) -> None:
        """Update system state."""
        self._state_manager.update_state(**kwargs)
    
    async def validate_category(self, category: str) -> List[ValidationIssue]:
        """Run validation for a specific category."""
        if not self._initialized:
            await self.initialize()
        
        if category not in self._validators:
            raise ValueError(f"Unknown category: {category}")
        
        validator = self._validators[category]
        state = self._state_manager.get_state()
        
        return await validator.validate(state)
    
    async def remediate_all_auto(self) -> List[RemediationAction]:
        """Remediate all issues that support auto-remediation."""
        if not self._last_report:
            await self.run_full_validation()
        
        remediations = []
        for issue in self._last_report.issues:
            if issue.auto_remediate and issue.remediation_available:
                remediation = await self._remediate_issue(issue)
                remediations.append(remediation)
        
        return remediations
    
    def get_immutable_limits(self) -> Dict[str, float]:
        """Get immutable safety limits."""
        return IMMUTABLE_LIMITS.copy()
    
    def get_validator_summary(self) -> Dict[str, Dict[str, Any]]:
        """Get summary of all validators."""
        summary = {}
        for name, validator in self._validators.items():
            summary[name] = {
                'category': validator.category.value,
                'checks_count': len(validator._checks),
                'remediations_count': len(validator._remediations),
            }
        return summary


async def quick_start(config: Optional[Dict[str, Any]] = None) -> SelfHealingOrchestrator:
    """Quick start helper for the orchestrator."""
    orchestrator = SelfHealingOrchestrator(config)
    await orchestrator.initialize()
    return orchestrator
