"""
Integration tests for Self-Healing AI Validator System
"""

import asyncio
import pytest
import sys
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent.parent))

from trading_bot.self_healing_ai.core import (
    ValidationSeverity, ValidationCategory, RemediationStatus,
    SystemHealth, ValidationIssue, RemediationAction, ValidationReport,
    SystemState, BaseValidator, StateManager, IMMUTABLE_LIMITS
)
from trading_bot.self_healing_ai.orchestrator import SelfHealingOrchestrator, quick_start


class TestCore:
    """Test core classes and enums."""
    
    def test_validation_severity_values(self):
        """Test ValidationSeverity enum values."""
        assert ValidationSeverity.CRITICAL.value == 'critical'
        assert ValidationSeverity.HIGH.value == 'high'
        assert ValidationSeverity.MEDIUM.value == 'medium'
        assert ValidationSeverity.LOW.value == 'low'
        assert ValidationSeverity.INFO.value == 'info'
    
    def test_validation_category_count(self):
        """Test all 16 categories exist."""
        categories = list(ValidationCategory)
        assert len(categories) == 16
    
    def test_system_health_values(self):
        """Test SystemHealth enum values."""
        assert SystemHealth.HEALTHY.value == 'healthy'
        assert SystemHealth.DEGRADED.value == 'degraded'
        assert SystemHealth.CRITICAL.value == 'critical'
        assert SystemHealth.UNKNOWN.value == 'unknown'
    
    def test_immutable_limits(self):
        """Test immutable limits are defined."""
        assert 'max_risk_per_trade' in IMMUTABLE_LIMITS
        assert 'max_daily_loss' in IMMUTABLE_LIMITS
        assert 'max_drawdown' in IMMUTABLE_LIMITS
        assert 'max_leverage' in IMMUTABLE_LIMITS
        assert IMMUTABLE_LIMITS['max_risk_per_trade'] == 0.02
        assert IMMUTABLE_LIMITS['max_daily_loss'] == 0.05
        assert IMMUTABLE_LIMITS['max_drawdown'] == 0.20
    
    def test_system_state_defaults(self):
        """Test SystemState default values."""
        state = SystemState()
        assert state.capital == 0
        assert state.equity == 0
        assert state.drawdown == 0
        assert state.daily_pnl == 0
        assert isinstance(state.positions, dict)
        assert isinstance(state.error_counts, dict)


class TestStateManager:
    """Test StateManager functionality."""
    
    def test_singleton_pattern(self):
        """Test StateManager is singleton."""
        sm1 = StateManager()
        sm2 = StateManager()
        assert sm1 is sm2
    
    def test_get_state(self):
        """Test getting state."""
        sm = StateManager()
        state = sm.get_state()
        assert isinstance(state, SystemState)
    
    def test_update_state(self):
        """Test updating state."""
        sm = StateManager()
        sm.update_state(capital=100000, equity=98000)
        state = sm.get_state()
        assert state.capital == 100000
        assert state.equity == 98000


class TestValidationIssue:
    """Test ValidationIssue dataclass."""
    
    def test_create_issue(self):
        """Test creating a validation issue."""
        issue = ValidationIssue(
            issue_id="test123",
            question_id=1,
            category=ValidationCategory.SYSTEM_ARCHITECTURE,
            severity=ValidationSeverity.HIGH,
            title="Test Issue",
            description="Test description",
            affected_components=["TestComponent"]
        )
        assert issue.issue_id == "test123"
        assert issue.question_id == 1
        assert issue.severity == ValidationSeverity.HIGH
        assert issue.remediation_available == False
        assert issue.auto_remediate == False


class TestValidationReport:
    """Test ValidationReport dataclass."""
    
    def test_create_report(self):
        """Test creating a validation report."""
        report = ValidationReport(
            report_id="report123",
            generated_at=datetime.utcnow(),
            system_health=SystemHealth.HEALTHY,
            total_checks=100,
            passed_checks=95,
            failed_checks=5,
            issues=[],
            remediations=[],
            category_scores={},
            recommendations=[],
            execution_time_ms=50.0
        )
        assert report.report_id == "report123"
        assert report.total_checks == 100
        assert report.passed_checks == 95
    
    def test_get_critical_issues(self):
        """Test getting critical issues from report."""
        critical_issue = ValidationIssue(
            issue_id="crit1",
            question_id=1,
            category=ValidationCategory.RISK_MANAGEMENT,
            severity=ValidationSeverity.CRITICAL,
            title="Critical Issue",
            description="Critical",
            affected_components=["Risk"]
        )
        high_issue = ValidationIssue(
            issue_id="high1",
            question_id=2,
            category=ValidationCategory.RISK_MANAGEMENT,
            severity=ValidationSeverity.HIGH,
            title="High Issue",
            description="High",
            affected_components=["Risk"]
        )
        report = ValidationReport(
            report_id="report123",
            generated_at=datetime.utcnow(),
            system_health=SystemHealth.CRITICAL,
            total_checks=10,
            passed_checks=8,
            failed_checks=2,
            issues=[critical_issue, high_issue],
            remediations=[],
            category_scores={},
            recommendations=[],
            execution_time_ms=50.0
        )
        critical = report.get_critical_issues()
        assert len(critical) == 1
        assert critical[0].severity == ValidationSeverity.CRITICAL


class TestOrchestrator:
    """Test SelfHealingOrchestrator."""
    
    @pytest.mark.asyncio
    async def test_initialize(self):
        """Test orchestrator initialization."""
        orchestrator = SelfHealingOrchestrator()
        await orchestrator.initialize()
        assert orchestrator._initialized == True
        assert len(orchestrator._validators) == 16
    
    @pytest.mark.asyncio
    async def test_quick_start(self):
        """Test quick_start helper."""
        orchestrator = await quick_start()
        assert orchestrator._initialized == True
    
    @pytest.mark.asyncio
    async def test_run_full_validation(self):
        """Test running full validation."""
        orchestrator = await quick_start()
        report = await orchestrator.run_full_validation()
        
        assert isinstance(report, ValidationReport)
        assert report.total_checks > 0
        assert report.system_health in list(SystemHealth)
        assert isinstance(report.category_scores, dict)
        assert len(report.category_scores) == 16
    
    @pytest.mark.asyncio
    async def test_validate_category(self):
        """Test validating specific category."""
        orchestrator = await quick_start()
        issues = await orchestrator.validate_category('risk')
        assert isinstance(issues, list)
    
    @pytest.mark.asyncio
    async def test_get_validator_summary(self):
        """Test getting validator summary."""
        orchestrator = await quick_start()
        summary = orchestrator.get_validator_summary()
        
        assert len(summary) == 16
        for name, info in summary.items():
            assert 'category' in info
            assert 'checks_count' in info
            assert 'remediations_count' in info
    
    @pytest.mark.asyncio
    async def test_get_immutable_limits(self):
        """Test getting immutable limits."""
        orchestrator = await quick_start()
        limits = orchestrator.get_immutable_limits()
        
        assert limits == IMMUTABLE_LIMITS
    
    @pytest.mark.asyncio
    async def test_state_update(self):
        """Test state update."""
        orchestrator = await quick_start()
        orchestrator.update_state(
            capital=100000,
            equity=98000,
            drawdown=0.02
        )
        state = orchestrator.get_state()
        assert state.capital == 100000
        assert state.equity == 98000
        assert state.drawdown == 0.02
    
    @pytest.mark.asyncio
    async def test_system_health(self):
        """Test getting system health."""
        orchestrator = await quick_start()
        await orchestrator.run_full_validation()
        health = orchestrator.get_system_health()
        assert health in list(SystemHealth)


class TestValidators:
    """Test individual validators."""
    
    @pytest.mark.asyncio
    async def test_all_validators_load(self):
        """Test all validators load correctly."""
        from trading_bot.self_healing_ai.validators import (
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
        
        validators = [
            SystemArchitectureValidator(),
            DataIntegrityValidator(),
            ExecutionValidator(),
            StrategyValidator(),
            MLModelValidator(),
            RiskValidator(),
            InfrastructureValidator(),
            BacktestValidator(),
            ResearchProductionValidator(),
            SelfModificationValidator(),
            SecurityValidator(),
            ConfigurationValidator(),
            MonitoringValidator(),
            KillSwitchValidator(),
            RegulatoryValidator(),
            CapitalValidator(),
        ]
        
        assert len(validators) == 16
        
        for validator in validators:
            assert hasattr(validator, 'validate')
            assert hasattr(validator, 'remediate')
            assert hasattr(validator, 'category')
    
    @pytest.mark.asyncio
    async def test_risk_validator(self):
        """Test RiskValidator specifically."""
        from trading_bot.self_healing_ai.validators import RiskValidator
        
        validator = RiskValidator()
        state = SystemState(
            capital=100000,
            equity=80000,
            drawdown=0.20,
            positions={'BTCUSDT': {'risk_percent': 0.05}}
        )
        
        issues = await validator.validate(state)
        assert isinstance(issues, list)
    
    @pytest.mark.asyncio
    async def test_security_validator(self):
        """Test SecurityValidator specifically."""
        from trading_bot.self_healing_ai.validators import SecurityValidator
        
        validator = SecurityValidator()
        state = SystemState(
            error_counts={'authentication_failure': 5}
        )
        
        issues = await validator.validate(state)
        assert isinstance(issues, list)
    
    @pytest.mark.asyncio
    async def test_kill_switch_validator(self):
        """Test KillSwitchValidator specifically."""
        from trading_bot.self_healing_ai.validators import KillSwitchValidator
        
        validator = KillSwitchValidator()
        state = SystemState(
            error_counts={'killswitch_unavailable': 1}
        )
        
        issues = await validator.validate(state)
        assert isinstance(issues, list)
        # Should find critical issue
        critical = [i for i in issues if i.severity == ValidationSeverity.CRITICAL]
        assert len(critical) > 0


class TestIntegration:
    """Integration tests."""
    
    @pytest.mark.asyncio
    async def test_full_workflow(self):
        """Test complete workflow."""
        # Initialize
        orchestrator = await quick_start({'auto_remediate': True})
        
        # Update state
        orchestrator.update_state(
            capital=100000,
            equity=95000,
            drawdown=0.05,
            daily_pnl=-1000,
            positions={'BTCUSDT': {'size': 0.5, 'risk_percent': 0.01}},
            error_counts={'rate_limit': 2},
            latency_metrics={'e2e_latency_ms': 50}
        )
        
        # Run validation
        report = await orchestrator.run_full_validation()
        
        # Verify report
        assert report.total_checks > 0
        assert len(report.category_scores) == 16
        
        # Check recommendations
        assert isinstance(report.recommendations, list)
    
    @pytest.mark.asyncio
    async def test_critical_detection(self):
        """Test critical issue detection."""
        orchestrator = await quick_start()
        
        # Set up critical state
        orchestrator.update_state(
            capital=100000,
            equity=70000,
            drawdown=0.30,  # Exceeds max_drawdown
            error_counts={
                'killswitch_unavailable': 1,
                'compliance_violation': 1
            }
        )
        
        report = await orchestrator.run_full_validation()
        
        # Should detect critical issues
        critical = report.get_critical_issues()
        assert len(critical) > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
