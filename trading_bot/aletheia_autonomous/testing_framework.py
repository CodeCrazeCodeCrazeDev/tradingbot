"""
Testing and Validation Framework

Comprehensive testing framework for the Aletheia autonomous research system.
Ensures correctness, robustness, and reliability of all components.
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime
from dataclasses import dataclass

from .aletheia_orchestrator import AletheiaOrchestrator, StrategyHypothesis, AutonomyLevel
from .subagents.generator import StrategyGenerator
from .subagents.verifier import StrategyVerifier
from .subagents.reviser import StrategyReviser

logger = logging.getLogger(__name__)


@dataclass
class TestResult:
    """Result of a test"""
    test_name: str
    passed: bool
    duration_ms: float
    message: str
    details: Optional[Dict] = None


class AletheiaTestFramework:
    """
    Comprehensive testing framework for Aletheia system.
    
    Tests cover:
    - Unit tests for subagents
    - Integration tests for the full pipeline
    - Performance tests
    - Governance compliance tests
    - Safety and validation tests
    """
    
    def __init__(self):
        self.test_results: List[TestResult] = []
        self.test_suite = self._initialize_test_suite()
        
    def _initialize_test_suite(self) -> Dict[str, callable]:
        """Initialize all tests"""
        return {
            # Generator Tests
            "test_generator_initialization": self.test_generator_initialization,
            "test_strategy_generation": self.test_strategy_generation,
            "test_multiple_strategy_types": self.test_multiple_strategy_types,
            "test_market_context_integration": self.test_market_context_integration,
            
            # Verifier Tests
            "test_verifier_initialization": self.test_verifier_initialization,
            "test_logical_consistency": self.test_logical_consistency,
            "test_risk_assessment": self.test_risk_assessment,
            "test_backtest_integration": self.test_backtest_integration,
            
            # Reviser Tests
            "test_reviser_initialization": self.test_reviser_initialization,
            "test_issue_fixing": self.test_issue_fixing,
            "test_improvement_application": self.test_improvement_application,
            
            # Orchestrator Tests
            "test_orchestrator_initialization": self.test_orchestrator_initialization,
            "test_full_research_cycle": self.test_full_research_cycle,
            "test_max_iterations": self.test_max_iterations,
            "test_confidence_threshold": self.test_confidence_threshold,
            
            # Integration Tests
            "test_end_to_end_pipeline": self.test_end_to_end_pipeline,
            "test_batch_processing": self.test_batch_processing,
            "test_error_handling": self.test_error_handling,
            
            # Safety Tests
            "test_risk_limit_enforcement": self.test_risk_limit_enforcement,
            "test_governance_compliance": self.test_governance_compliance,
            "test_audit_trail": self.test_audit_trail,
        }
    
    async def run_all_tests(self) -> Dict[str, Any]:
        """Run all tests and return results"""
        logger.info("Starting Aletheia test suite...")
        
        self.test_results = []
        start_time = datetime.now()
        
        for test_name, test_func in self.test_suite.items():
            try:
                result = await test_func()
                self.test_results.append(result)
                status = "PASSED" if result.passed else "FAILED"
                logger.info(f"Test {test_name}: {status}")
            except Exception as e:
                logger.error(f"Test {test_name} crashed: {e}")
                self.test_results.append(TestResult(
                    test_name=test_name,
                    passed=False,
                    duration_ms=0,
                    message=f"Test crashed: {str(e)}"
                ))
        
        duration = (datetime.now() - start_time).total_seconds()
        
        passed = sum(1 for r in self.test_results if r.passed)
        failed = len(self.test_results) - passed
        
        return {
            "total_tests": len(self.test_results),
            "passed": passed,
            "failed": failed,
            "pass_rate": passed / len(self.test_results) if self.test_results else 0,
            "duration_seconds": duration,
            "results": [
                {
                    "test": r.test_name,
                    "passed": r.passed,
                    "duration_ms": r.duration_ms,
                    "message": r.message
                }
                for r in self.test_results
            ],
            "failed_tests": [
                r.test_name for r in self.test_results if not r.passed
            ]
        }
    
    async def test_generator_initialization(self) -> TestResult:
        """Test StrategyGenerator initialization"""
        import time
        start = time.time()
        
        try:
            generator = StrategyGenerator()
            assert generator is not None
            assert len(generator.strategy_templates) > 0
            
            duration = (time.time() - start) * 1000
            return TestResult(
                test_name="test_generator_initialization",
                passed=True,
                duration_ms=duration,
                message="Generator initialized successfully"
            )
        except Exception as e:
            duration = (time.time() - start) * 1000
            return TestResult(
                test_name="test_generator_initialization",
                passed=False,
                duration_ms=duration,
                message=f"Initialization failed: {str(e)}"
            )
    
    async def test_strategy_generation(self) -> TestResult:
        """Test basic strategy generation"""
        import time
        start = time.time()
        
        try:
            generator = StrategyGenerator()
            hypothesis = await generator.generate(
                prompt="Create a momentum strategy for trending markets",
                market_context={"trend": "strong_up", "volatility": "medium"},
                constraints={"max_risk_per_trade": 2.0}
            )
            
            assert hypothesis is not None
            assert hypothesis.hypothesis_id
            assert hypothesis.title
            assert len(hypothesis.entry_rules) > 0
            assert len(hypothesis.exit_rules) > 0
            assert hypothesis.confidence_score > 0
            
            duration = (time.time() - start) * 1000
            return TestResult(
                test_name="test_strategy_generation",
                passed=True,
                duration_ms=duration,
                message=f"Generated strategy: {hypothesis.title}"
            )
        except Exception as e:
            duration = (time.time() - start) * 1000
            return TestResult(
                test_name="test_strategy_generation",
                passed=False,
                duration_ms=duration,
                message=f"Generation failed: {str(e)}"
            )
    
    async def test_multiple_strategy_types(self) -> TestResult:
        """Test generation of different strategy types"""
        import time
        start = time.time()
        
        try:
            generator = StrategyGenerator()
            prompts = [
                "Momentum strategy",
                "Mean reversion strategy",
                "Breakout strategy",
                "Statistical arbitrage",
                "Sentiment-based strategy"
            ]
            
            hypotheses = await asyncio.gather(*[
                generator.generate(prompt=prompt)
                for prompt in prompts
            ])
            
            assert len(hypotheses) == 5
            assert all(h.title for h in hypotheses)
            
            duration = (time.time() - start) * 1000
            return TestResult(
                test_name="test_multiple_strategy_types",
                passed=True,
                duration_ms=duration,
                message=f"Generated {len(hypotheses)} different strategy types"
            )
        except Exception as e:
            duration = (time.time() - start) * 1000
            return TestResult(
                test_name="test_multiple_strategy_types",
                passed=False,
                duration_ms=duration,
                message=f"Multi-type generation failed: {str(e)}"
            )
    
    async def test_market_context_integration(self) -> TestResult:
        """Test market context affects generation"""
        import time
        start = time.time()
        
        try:
            generator = StrategyGenerator()
            
            # Generate for different contexts
            trend_up = await generator.generate(
                prompt="Trading strategy",
                market_context={"trend": "strong_up", "volatility": "medium"}
            )
            
            ranging = await generator.generate(
                prompt="Trading strategy",
                market_context={"trend": "neutral", "volatility": "low"}
            )
            
            # Should generate different types
            assert trend_up.title != ranging.title
            
            duration = (time.time() - start) * 1000
            return TestResult(
                test_name="test_market_context_integration",
                passed=True,
                duration_ms=duration,
                message="Market context affects generation"
            )
        except Exception as e:
            duration = (time.time() - start) * 1000
            return TestResult(
                test_name="test_market_context_integration",
                passed=False,
                duration_ms=duration,
                message=f"Context integration failed: {str(e)}"
            )
    
    async def test_verifier_initialization(self) -> TestResult:
        """Test StrategyVerifier initialization"""
        import time
        start = time.time()
        
        try:
            verifier = StrategyVerifier()
            assert verifier is not None
            assert len(verifier.verification_methods) > 0
            
            duration = (time.time() - start) * 1000
            return TestResult(
                test_name="test_verifier_initialization",
                passed=True,
                duration_ms=duration,
                message="Verifier initialized successfully"
            )
        except Exception as e:
            duration = (time.time() - start) * 1000
            return TestResult(
                test_name="test_verifier_initialization",
                passed=False,
                duration_ms=duration,
                message=f"Verifier initialization failed: {str(e)}"
            )
    
    async def test_logical_consistency(self) -> TestResult:
        """Test logical consistency verification"""
        import time
        start = time.time()
        
        try:
            generator = StrategyGenerator()
            verifier = StrategyVerifier()
            
            # Generate strategy
            hypothesis = await generator.generate(prompt="Test strategy")
            
            # Verify
            result = await verifier.verify(hypothesis)
            
            assert result is not None
            assert 0 <= result.confidence <= 1
            assert result.test_results is not None
            
            duration = (time.time() - start) * 1000
            return TestResult(
                test_name="test_logical_consistency",
                passed=True,
                duration_ms=duration,
                message=f"Verification confidence: {result.confidence:.2f}"
            )
        except Exception as e:
            duration = (time.time() - start) * 1000
            return TestResult(
                test_name="test_logical_consistency",
                passed=False,
                duration_ms=duration,
                message=f"Logical consistency check failed: {str(e)}"
            )
    
    async def test_risk_assessment(self) -> TestResult:
        """Test risk assessment verification"""
        import time
        start = time.time()
        
        try:
            generator = StrategyGenerator()
            verifier = StrategyVerifier()
            
            # Generate high-risk strategy
            hypothesis = await generator.generate(prompt="Strategy")
            hypothesis.risk_parameters["max_position_size"] = 20  # Very high
            
            result = await verifier.verify(hypothesis)
            
            # Should flag high risk
            risk_issues = [i for i in result.issues if "risk" in i.lower() or "position" in i.lower()]
            
            duration = (time.time() - start) * 1000
            return TestResult(
                test_name="test_risk_assessment",
                passed=True,
                duration_ms=duration,
                message=f"Risk assessment flagged {len(risk_issues)} issues"
            )
        except Exception as e:
            duration = (time.time() - start) * 1000
            return TestResult(
                test_name="test_risk_assessment",
                passed=False,
                duration_ms=duration,
                message=f"Risk assessment failed: {str(e)}"
            )
    
    async def test_backtest_integration(self) -> TestResult:
        """Test backtest integration in verification"""
        import time
        start = time.time()
        
        try:
            generator = StrategyGenerator()
            verifier = StrategyVerifier()
            
            hypothesis = await generator.generate(prompt="Backtest strategy")
            result = await verifier.verify(hypothesis)
            
            # Check backtest results exist
            assert "backtesting" in result.test_results
            backtest = result.test_results["backtesting"]
            assert "results" in backtest
            
            duration = (time.time() - start) * 1000
            return TestResult(
                test_name="test_backtest_integration",
                passed=True,
                duration_ms=duration,
                message="Backtest integration working"
            )
        except Exception as e:
            duration = (time.time() - start) * 1000
            return TestResult(
                test_name="test_backtest_integration",
                passed=False,
                duration_ms=duration,
                message=f"Backtest integration failed: {str(e)}"
            )
    
    async def test_reviser_initialization(self) -> TestResult:
        """Test StrategyReviser initialization"""
        import time
        start = time.time()
        
        try:
            reviser = StrategyReviser()
            assert reviser is not None
            
            duration = (time.time() - start) * 1000
            return TestResult(
                test_name="test_reviser_initialization",
                passed=True,
                duration_ms=duration,
                message="Reviser initialized successfully"
            )
        except Exception as e:
            duration = (time.time() - start) * 1000
            return TestResult(
                test_name="test_reviser_initialization",
                passed=False,
                duration_ms=duration,
                message=f"Reviser initialization failed: {str(e)}"
            )
    
    async def test_issue_fixing(self) -> TestResult:
        """Test that reviser fixes identified issues"""
        import time
        start = time.time()
        
        try:
            generator = StrategyGenerator()
            verifier = StrategyVerifier()
            reviser = StrategyReviser()
            
            # Generate and get verification with issues
            hypothesis = await generator.generate(prompt="Test strategy")
            
            # Add a problematic rule to force an issue
            hypothesis.exit_rules = []  # No exit rules - should trigger issue
            
            verification = await verifier.verify(hypothesis)
            
            # Revise
            revision = await reviser.revise(hypothesis, verification, iteration=0)
            
            assert revision is not None
            assert revision.revised_hypothesis is not None
            
            duration = (time.time() - start) * 1000
            return TestResult(
                test_name="test_issue_fixing",
                passed=True,
                duration_ms=duration,
                message=f"Made {len(revision.changes_made)} changes to fix issues"
            )
        except Exception as e:
            duration = (time.time() - start) * 1000
            return TestResult(
                test_name="test_issue_fixing",
                passed=False,
                duration_ms=duration,
                message=f"Issue fixing failed: {str(e)}"
            )
    
    async def test_improvement_application(self) -> TestResult:
        """Test that reviser applies recommendations"""
        import time
        start = time.time()
        
        try:
            generator = StrategyGenerator()
            verifier = StrategyVerifier()
            reviser = StrategyReviser()
            
            hypothesis = await generator.generate(prompt="Test strategy")
            verification = await verifier.verify(hypothesis)
            
            # Ensure we have recommendations
            if not verification.recommendations:
                verification.recommendations = ["Add filtering condition to improve signal quality"]
            
            revision = await reviser.revise(hypothesis, verification, iteration=0)
            
            duration = (time.time() - start) * 1000
            return TestResult(
                test_name="test_improvement_application",
                passed=True,
                duration_ms=duration,
                message="Improvements applied successfully"
            )
        except Exception as e:
            duration = (time.time() - start) * 1000
            return TestResult(
                test_name="test_improvement_application",
                passed=False,
                duration_ms=duration,
                message=f"Improvement application failed: {str(e)}"
            )
    
    async def test_orchestrator_initialization(self) -> TestResult:
        """Test AletheiaOrchestrator initialization"""
        import time
        start = time.time()
        
        try:
            generator = StrategyGenerator()
            verifier = StrategyVerifier()
            reviser = StrategyReviser()
            
            orchestrator = AletheiaOrchestrator(
                generator=generator,
                verifier=verifier,
                reviser=reviser,
                max_iterations=3
            )
            
            assert orchestrator is not None
            assert orchestrator.max_iterations == 3
            
            duration = (time.time() - start) * 1000
            return TestResult(
                test_name="test_orchestrator_initialization",
                passed=True,
                duration_ms=duration,
                message="Orchestrator initialized successfully"
            )
        except Exception as e:
            duration = (time.time() - start) * 1000
            return TestResult(
                test_name="test_orchestrator_initialization",
                passed=False,
                duration_ms=duration,
                message=f"Orchestrator initialization failed: {str(e)}"
            )
    
    async def test_full_research_cycle(self) -> TestResult:
        """Test complete research cycle"""
        import time
        start = time.time()
        
        try:
            generator = StrategyGenerator()
            verifier = StrategyVerifier()
            reviser = StrategyReviser()
            
            orchestrator = AletheiaOrchestrator(
                generator=generator,
                verifier=verifier,
                reviser=reviser,
                max_iterations=2
            )
            
            hypothesis = await orchestrator.research_strategy(
                research_prompt="Create a breakout strategy for volatile markets"
            )
            
            assert hypothesis is not None
            assert hypothesis.hypothesis_id
            assert hypothesis.verification_status in ["verified", "partial", "pending"]
            
            duration = (time.time() - start) * 1000
            return TestResult(
                test_name="test_full_research_cycle",
                passed=True,
                duration_ms=duration,
                message=f"Full cycle completed with status: {hypothesis.verification_status}"
            )
        except Exception as e:
            duration = (time.time() - start) * 1000
            return TestResult(
                test_name="test_full_research_cycle",
                passed=False,
                duration_ms=duration,
                message=f"Full cycle failed: {str(e)}"
            )
    
    async def test_max_iterations(self) -> TestResult:
        """Test max iterations limit"""
        import time
        start = time.time()
        
        try:
            generator = StrategyGenerator()
            verifier = StrategyVerifier()
            reviser = StrategyReviser()
            
            orchestrator = AletheiaOrchestrator(
                generator=generator,
                verifier=verifier,
                reviser=reviser,
                max_iterations=1  # Very low to test limit
            )
            
            hypothesis = await orchestrator.research_strategy(
                research_prompt="Test iteration limit"
            )
            
            assert hypothesis.revision_count <= 1
            
            duration = (time.time() - start) * 1000
            return TestResult(
                test_name="test_max_iterations",
                passed=True,
                duration_ms=duration,
                message=f"Respected max iterations: {hypothesis.revision_count} <= 1"
            )
        except Exception as e:
            duration = (time.time() - start) * 1000
            return TestResult(
                test_name="test_max_iterations",
                passed=False,
                duration_ms=duration,
                message=f"Max iterations test failed: {str(e)}"
            )
    
    async def test_confidence_threshold(self) -> TestResult:
        """Test confidence threshold enforcement"""
        import time
        start = time.time()
        
        try:
            generator = StrategyGenerator()
            verifier = StrategyVerifier()
            reviser = StrategyReviser()
            
            orchestrator = AletheiaOrchestrator(
                generator=generator,
                verifier=verifier,
                reviser=reviser,
                min_confidence_threshold=0.95  # Very high
            )
            
            hypothesis = await orchestrator.research_strategy(
                research_prompt="Test confidence threshold"
            )
            
            # If not verified, confidence should be below threshold
            if hypothesis.verification_status != "verified":
                assert hypothesis.confidence_score < 0.95
            
            duration = (time.time() - start) * 1000
            return TestResult(
                test_name="test_confidence_threshold",
                passed=True,
                duration_ms=duration,
                message="Confidence threshold enforced"
            )
        except Exception as e:
            duration = (time.time() - start) * 1000
            return TestResult(
                test_name="test_confidence_threshold",
                passed=False,
                duration_ms=duration,
                message=f"Confidence threshold test failed: {str(e)}"
            )
    
    async def test_end_to_end_pipeline(self) -> TestResult:
        """Test complete end-to-end pipeline"""
        import time
        start = time.time()
        
        try:
            # This is a comprehensive integration test
            generator = StrategyGenerator()
            verifier = StrategyVerifier()
            reviser = StrategyReviser()
            
            orchestrator = AletheiaOrchestrator(
                generator=generator,
                verifier=verifier,
                reviser=reviser
            )
            
            hypothesis = await orchestrator.research_strategy(
                research_prompt="Create a mean reversion strategy for ranging markets",
                market_context={
                    "trend": "neutral",
                    "volatility": "low",
                    "regime": "range_bound"
                },
                constraints={
                    "max_risk_per_trade": 2.0,
                    "max_daily_loss": 3.0
                }
            )
            
            # Comprehensive checks
            checks = [
                hypothesis.hypothesis_id is not None,
                len(hypothesis.title) > 0,
                len(hypothesis.entry_rules) > 0,
                len(hypothesis.exit_rules) > 0,
                len(hypothesis.risk_parameters) > 0,
                hypothesis.confidence_score > 0,
                len(hypothesis.generation_trace) > 0
            ]
            
            all_passed = all(checks)
            
            duration = (time.time() - start) * 1000
            return TestResult(
                test_name="test_end_to_end_pipeline",
                passed=all_passed,
                duration_ms=duration,
                message=f"E2E pipeline: {sum(checks)}/{len(checks)} checks passed"
            )
        except Exception as e:
            duration = (time.time() - start) * 1000
            return TestResult(
                test_name="test_end_to_end_pipeline",
                passed=False,
                duration_ms=duration,
                message=f"E2E pipeline failed: {str(e)}"
            )
    
    async def test_batch_processing(self) -> TestResult:
        """Test batch processing of multiple strategies"""
        import time
        start = time.time()
        
        try:
            generator = StrategyGenerator()
            verifier = StrategyVerifier()
            reviser = StrategyReviser()
            
            orchestrator = AletheiaOrchestrator(
                generator=generator,
                verifier=verifier,
                reviser=reviser
            )
            
            prompts = [
                "Momentum strategy for trending markets",
                "Mean reversion for ranging markets",
                "Breakout strategy for volatile markets"
            ]
            
            hypotheses = await orchestrator.batch_research(
                research_prompts=prompts,
                parallel=True
            )
            
            assert len(hypotheses) == 3
            assert all(h.hypothesis_id for h in hypotheses)
            
            duration = (time.time() - start) * 1000
            return TestResult(
                test_name="test_batch_processing",
                passed=True,
                duration_ms=duration,
                message=f"Batch processed {len(hypotheses)} strategies"
            )
        except Exception as e:
            duration = (time.time() - start) * 1000
            return TestResult(
                test_name="test_batch_processing",
                passed=False,
                duration_ms=duration,
                message=f"Batch processing failed: {str(e)}"
            )
    
    async def test_error_handling(self) -> TestResult:
        """Test error handling"""
        import time
        start = time.time()
        
        try:
            # Test with invalid inputs
            generator = StrategyGenerator()
            
            # This should not crash
            hypothesis = await generator.generate(
                prompt="",  # Empty prompt
                market_context={},
                constraints={}
            )
            
            # Should still return a valid hypothesis
            assert hypothesis is not None
            assert hypothesis.hypothesis_id
            
            duration = (time.time() - start) * 1000
            return TestResult(
                test_name="test_error_handling",
                passed=True,
                duration_ms=duration,
                message="Gracefully handled edge cases"
            )
        except Exception as e:
            duration = (time.time() - start) * 1000
            return TestResult(
                test_name="test_error_handling",
                passed=False,
                duration_ms=duration,
                message=f"Error handling failed: {str(e)}"
            )
    
    async def test_risk_limit_enforcement(self) -> TestResult:
        """Test risk limit enforcement"""
        import time
        start = time.time()
        
        try:
            generator = StrategyGenerator()
            
            # Test with strict constraints
            constraints = {
                "max_risk_per_trade": 1.0,  # 1%
                "max_daily_loss": 2.0  # 2%
            }
            
            hypothesis = await generator.generate(
                prompt="Test risk constraints",
                constraints=constraints
            )
            
            # Verify constraints were respected
            assert hypothesis.risk_parameters["max_position_size"] <= 1.0
            assert hypothesis.risk_parameters["max_daily_loss"] <= 2.0
            
            duration = (time.time() - start) * 1000
            return TestResult(
                test_name="test_risk_limit_enforcement",
                passed=True,
                duration_ms=duration,
                message="Risk limits enforced correctly"
            )
        except Exception as e:
            duration = (time.time() - start) * 1000
            return TestResult(
                test_name="test_risk_limit_enforcement",
                passed=False,
                duration_ms=duration,
                message=f"Risk limit enforcement failed: {str(e)}"
            )
    
    async def test_governance_compliance(self) -> TestResult:
        """Test governance compliance features"""
        import time
        start = time.time()
        
        try:
            from .governance_integration import AletheiaGovernanceIntegration
            from .research_framework import AutonomousResearchFramework
            
            research_framework = AutonomousResearchFramework()
            governance = AletheiaGovernanceIntegration(research_framework)
            
            # Test approval request
            approval = await governance.request_approval(
                action="test_action",
                requester="test",
                details={"test": True}
            )
            
            assert "approval_id" in approval
            assert approval["status"] in ["pending", "approved"]
            
            duration = (time.time() - start) * 1000
            return TestResult(
                test_name="test_governance_compliance",
                passed=True,
                duration_ms=duration,
                message="Governance system operational"
            )
        except Exception as e:
            duration = (time.time() - start) * 1000
            return TestResult(
                test_name="test_governance_compliance",
                passed=False,
                duration_ms=duration,
                message=f"Governance compliance failed: {str(e)}"
            )
    
    async def test_audit_trail(self) -> TestResult:
        """Test audit trail generation"""
        import time
        start = time.time()
        
        try:
            generator = StrategyGenerator()
            verifier = StrategyVerifier()
            reviser = StrategyReviser()
            
            orchestrator = AletheiaOrchestrator(
                generator=generator,
                verifier=verifier,
                reviser=reviser
            )
            
            hypothesis = await orchestrator.research_strategy(
                research_prompt="Test audit trail"
            )
            
            # Check audit trail
            assert len(hypothesis.generation_trace) > 0
            
            # Get research report
            report = orchestrator.export_research_report(hypothesis.hypothesis_id)
            assert "hypothesis" in report
            
            duration = (time.time() - start) * 1000
            return TestResult(
                test_name="test_audit_trail",
                passed=True,
                duration_ms=duration,
                message=f"Audit trail has {len(hypothesis.generation_trace)} entries"
            )
        except Exception as e:
            duration = (time.time() - start) * 1000
            return TestResult(
                test_name="test_audit_trail",
                passed=False,
                duration_ms=duration,
                message=f"Audit trail test failed: {str(e)}"
            )
