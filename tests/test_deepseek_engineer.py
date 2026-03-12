"""
Unit Tests for DeepSeek Autonomous Engineer
"""

import pytest
from pathlib import Path
from unittest.mock import Mock

from trading_bot.deepseek_engineer import (
    CodebaseAnalyzer,
    ProtectedRegistry,
    ProposalSystem,
    EngineerGuardrails,
    ProposalType,
    ProposalStatus,
)
from trading_bot.deepseek_engineer.protected_registry import AccessType
from trading_bot.deepseek_engineer.guardrails import SafetyLevel


class TestCodebaseAnalyzer:
    """Tests for CodebaseAnalyzer."""
    
    def test_initialization(self, tmp_path):
        analyzer = CodebaseAnalyzer(str(tmp_path))
        assert analyzer.root_path == tmp_path
    
    def test_analyze_python_file(self, tmp_path):
        test_file = tmp_path / "test.py"
        test_file.write_text("def hello(): pass")
        
        analyzer = CodebaseAnalyzer(str(tmp_path))
        analysis = analyzer.analyze_file(str(test_file))
        
        assert analysis is not None
        assert analysis.total_lines > 0


class TestProtectedRegistry:
    """Tests for ProtectedRegistry."""
    
    def test_initialization(self, tmp_path):
        registry = ProtectedRegistry(str(tmp_path))
        assert len(registry.IMMUTABLE_PROTECTED_PATTERNS) > 0
    
    def test_protected_file(self, tmp_path):
        registry = ProtectedRegistry(str(tmp_path))
        decision = registry.check_access("core/risk/manager.py", AccessType.MODIFY)
        assert decision.requires_approval


class TestProposalSystem:
    """Tests for ProposalSystem."""
    
    def test_create_proposal(self, tmp_path):
        system = ProposalSystem(str(tmp_path))
        proposal = system.create_proposal(
            title="Test",
            description="Test",
            proposal_type=ProposalType.FEATURE,
        )
        assert proposal.proposal_id.startswith("PROP-")
    
    def test_approval_workflow(self, tmp_path):
        system = ProposalSystem(str(tmp_path))
        proposal = system.create_proposal(
            title="Test",
            description="Test",
            proposal_type=ProposalType.DOCUMENTATION,
        )
        system.submit_for_approval(proposal)
        assert proposal.status == ProposalStatus.PENDING_REVIEW
        
        system.approve_proposal(proposal.proposal_id)
        assert proposal.status == ProposalStatus.APPROVED


class TestGuardrails:
    """Tests for EngineerGuardrails."""
    
    def test_forbidden_file(self, tmp_path):
        guardrails = EngineerGuardrails(str(tmp_path))
        check = guardrails.boundary_enforcer.check_file_modification(
            "deepseek_engineer/guardrails.py"
        )
        assert not check.safe
        assert check.level == SafetyLevel.FORBIDDEN
    
    def test_forbidden_pattern(self, tmp_path):
        guardrails = EngineerGuardrails(str(tmp_path))
        check = guardrails.boundary_enforcer.check_content("auto_deploy = True")
        assert not check.safe
    
    def test_safe_content(self, tmp_path):
        guardrails = EngineerGuardrails(str(tmp_path))
        check = guardrails.boundary_enforcer.check_content("x = 1")
        assert check.safe


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
