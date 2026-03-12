"""
Proposal Engine
Generates detailed fix proposals with actual code changes, risk analysis, and rollback plans.
"""

import os
import re
import ast
import logging
from typing import Any, Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime
from pathlib import Path
import json
import hashlib

from .code_analyzer import CodeIssue, IssueCategory, IssueSeverity
from enum import auto

logger = logging.getLogger(__name__)


class ProposalStatus(Enum):
    """Status of a proposal."""
    PENDING = "pending"  # Waiting for review
    APPROVED = "approved"  # Human approved
    REJECTED = "rejected"  # Human rejected
    APPLIED = "applied"  # Changes applied
    ROLLED_BACK = "rolled_back"  # Changes reverted
    FAILED = "failed"  # Application failed


class RiskLevel(Enum):
    """Risk level of applying a change."""
    MINIMAL = "minimal"  # Cosmetic changes only
    LOW = "low"  # Safe changes, unlikely to break anything
    MEDIUM = "medium"  # Could affect behavior, needs testing
    HIGH = "high"  # Significant changes, requires careful review
    CRITICAL = "critical"  # Core functionality, extensive testing needed


class ChangeType(Enum):
    """Type of code change."""
    ADD_CODE = "add_code"
    REMOVE_CODE = "remove_code"
    REPLACE_CODE = "replace_code"
    REFACTOR = "refactor"
    NEW_FILE = "new_file"
    DELETE_FILE = "delete_file"


@dataclass
class CodeChange:
    """Represents a specific code change."""
    file_path: str
    change_type: ChangeType
    line_start: int
    line_end: int
    old_code: str
    new_code: str
    explanation: str
    
    def to_dict(self) -> Dict:
        return {
            'file_path': self.file_path,
            'change_type': self.change_type.value,
            'line_start': self.line_start,
            'line_end': self.line_end,
            'old_code': self.old_code,
            'new_code': self.new_code,
            'explanation': self.explanation
        }


@dataclass
class Proposal:
    """A complete proposal for fixing an issue."""
    proposal_id: str
    issue: CodeIssue
    title: str
    description: str
    changes: List[CodeChange]
    risk_level: RiskLevel
    risk_analysis: str
    expected_benefits: List[str]
    potential_drawbacks: List[str]
    testing_required: str
    rollback_plan: str
    estimated_effort: str
    status: ProposalStatus = ProposalStatus.PENDING
    created_at: datetime = field(default_factory=datetime.now)
    reviewed_at: Optional[datetime] = None
    reviewer_notes: str = ""
    
    def to_dict(self) -> Dict:
        return {
            'proposal_id': self.proposal_id,
            'issue': self.issue.to_dict(),
            'title': self.title,
            'description': self.description,
            'changes': [c.to_dict() for c in self.changes],
            'risk_level': self.risk_level.value,
            'risk_analysis': self.risk_analysis,
            'expected_benefits': self.expected_benefits,
            'potential_drawbacks': self.potential_drawbacks,
            'testing_required': self.testing_required,
            'rollback_plan': self.rollback_plan,
            'estimated_effort': self.estimated_effort,
            'status': self.status.value,
            'created_at': self.created_at.isoformat(),
            'reviewed_at': self.reviewed_at.isoformat() if self.reviewed_at else None,
            'reviewer_notes': self.reviewer_notes
        }


class ProposalEngine:
    """
    Generates detailed fix proposals with:
    - Actual code changes (before/after)
    - Risk analysis
    - Expected benefits
    - Rollback plans
    - Testing requirements
    """
    
    def __init__(self, base_path: str):
        """
        Initialize proposal engine.
        
        Args:
            base_path: Root path of the trading bot codebase
        """
        self.base_path = Path(base_path)
        self.proposals: List[Proposal] = []
        self.proposal_counter = 0
        
        logger.info(f"ProposalEngine initialized for {base_path}")
    
    def _generate_proposal_id(self) -> str:
        """Generate unique proposal ID."""
        self.proposal_counter += 1
        return f"PROP-{datetime.now().strftime('%Y%m%d')}-{self.proposal_counter:04d}"
    
    def generate_proposals(self, issues: List[CodeIssue]) -> List[Proposal]:
        """
        Generate fix proposals for a list of issues.
        
        Args:
            issues: List of code issues to fix
            
        Returns:
            List of proposals
        """
        logger.info(f"Generating proposals for {len(issues)} issues...")
        self.proposals = []
        
        for issue in issues:
            proposal = self._generate_proposal_for_issue(issue)
            if proposal:
                    self.proposals.append(proposal)
        logger.info(f"Generated {len(self.proposals)} proposals")
        return self.proposals
    
    def _generate_proposal_for_issue(self, issue: CodeIssue) -> Optional[Proposal]:
        """Generate a proposal for a single issue."""
        # Route to appropriate generator based on category
        generators = {
            IssueCategory.INCOMPLETE: self._propose_incomplete_fix,
            IssueCategory.BUG: self._propose_bug_fix,
            IssueCategory.CODE_SMELL: self._propose_code_smell_fix,
            IssueCategory.SECURITY: self._propose_security_fix,
            IssueCategory.MAINTAINABILITY: self._propose_maintainability_fix,
            IssueCategory.DEPRECATED: self._propose_deprecated_fix,
        }
        
        generator = generators.get(issue.category, self._propose_generic_fix)
        return generator(issue)
    
    def _read_file_lines(self, file_path: str) -> List[str]:
        """Read file and return lines."""
        full_path = self.base_path / file_path
        try:
            with open(full_path, 'r', encoding='utf-8', errors='ignore') as f:
                return f.readlines()
        except Exception as e:
            logger.warning(f"Could not read {file_path}: {e}")
            return []
    
    def _get_context(self, file_path: str, line_num: int, context_lines: int = 5) -> Tuple[str, int, int]:
        """Get code context around a line."""
        lines = self._read_file_lines(file_path)
        if not lines:
            return "", 0, 0
        
        start = max(0, line_num - context_lines - 1)
        end = min(len(lines), line_num + context_lines)
        
        context = ''.join(lines[start:end])
        return context, start + 1, end
    
    def _propose_incomplete_fix(self, issue: CodeIssue) -> Optional[Proposal]:
        """Generate proposal for incomplete implementation."""
        lines = self._read_file_lines(issue.file_path)
        if not lines:
            return None
        
        # Get the function/class context
        context, start, end = self._get_context(issue.file_path, issue.line_number, 10)
        
        # Determine what kind of incomplete code it is
        if 'DONE (auto-completed)' in issue.title:
            
            changes = [CodeChange(
                file_path=issue.file_path,
                change_type=ChangeType.REPLACE_CODE,
                line_start=issue.line_number,
                line_end=issue.line_number,
            )]
            proposal_id=self._generate_proposal_id(),
            pass  # Implementation placeholder
            risk_level=RiskLevel.LOW,
            risk_analysis="Low risk - just making incomplete code explicit",
            expected_benefits=["Makes incomplete code explicit", "Prevents silent failures"],
            potential_drawbacks=["Will raise exception if code path is hit"],
            testing_required="Run affected code paths to verify behavior",
            
        elif 'Empty function' in issue.title or 'Stub function' in issue.title:
            # Extract function name
            func_match = re.search(r'def (\w+)', context)
            func_name = func_match.group(1) if func_match else "unknown"
            
            file_path=issue.file_path,
            line_start=issue.line_number,
            line_end=issue.line_number + 1,
            old_code="pass",
            new_code=f'raise NotImplementedError("{func_name} is not yet implemented")',
            explanation=f"Replace 'pass' with explicit NotImplementedError for {func_name}"
            
            
            return Proposal(
                proposal_id=self._generate_proposal_id(),
                issue=issue,
                title=f"Implement or mark {func_name} as not implemented",
                description=f"Function '{func_name}' is empty. Either implement it or make the incompleteness explicit.",
                changes=changes,
                risk_analysis="Low risk - makes incomplete code explicit",
                expected_benefits=["Prevents silent failures", "Clear error messages"],
                potential_drawbacks=["Will raise exception if function is called"],
                rollback_plan="Revert to 'pass'",
            )
        
        return None
    
    def _propose_bug_fix(self, issue: CodeIssue) -> Optional[Proposal]:
        """Generate proposal for bug fixes."""
        lines = self._read_file_lines(issue.file_path)
        if not lines:
            return None
        
        line = lines[issue.line_number - 1] if issue.line_number <= len(lines) else ""
        
        try:
            changes = [CodeChange(
                file_path=issue.file_path,
                change_type=ChangeType.REPLACE_CODE,
                line_start=issue.line_number,
                line_end=issue.line_number,
                old_code=line.strip(),
                new_code=f"# BUG: {issue.description}\n# Priority: HIGH - Needs investigation\n{line.strip()}",
                explanation="Mark bug for investigation"
            )]
            
            return Proposal(
                proposal_id=self._generate_proposal_id(),
                issue=issue,
                title=f"Bug fix at line {issue.line_number}",
                description=f"Potential bug detected: {issue.description}",
                changes=changes,
                risk_level=RiskLevel.MEDIUM,
                risk_analysis="Medium risk - actual fix depends on the specific bug",
                expected_benefits=["Bug visibility", "Tracking"],
                potential_drawbacks=["Doesn't actually fix the bug yet"],
                testing_required="Investigate and test the specific bug scenario",
                rollback_plan="Revert the annotation",
                estimated_effort="30 minutes to investigate"
            )
        except Exception as e:
            logger.error(f'Error proposing bug fix: {e}')
            return None
        
        if 'error handling' in (getattr(issue, 'title', '') or '').lower():
            # Add try-except wrapper
            indent = len(line) - len(line.lstrip())
            indent_str = ' ' * indent
            
            new_code = f"""{indent_str}try:
{indent_str}    {line.strip()}
{indent_str}except Exception as e:
{indent_str}    logger.error(f"Error: {{e}}")
{indent_str}    raise"""
            
            changes = [CodeChange(
                file_path=issue.file_path,
                change_type=ChangeType.REPLACE_CODE,
                line_start=issue.line_number,
                line_end=issue.line_number,
                old_code=line.strip(),
                new_code=new_code,
                explanation="Add error handling with logging"
            )]
            
            return Proposal(
                proposal_id=self._generate_proposal_id(),
                issue=issue,
                title=f"Add error handling at line {issue.line_number}",
                description=f"Risky operation without error handling. Adding try-except with logging.",
                changes=changes,
                risk_level=RiskLevel.LOW,
                risk_analysis="Low risk - adds safety without changing logic",
                expected_benefits=["Better error visibility", "Graceful failure handling"],
                potential_drawbacks=["Slight performance overhead"],
                testing_required="Test the error path",
                rollback_plan="Remove try-except wrapper",
                estimated_effort="10 minutes"
            )
        
        return None
    
    def _propose_code_smell_fix(self, issue: CodeIssue) -> Optional[Proposal]:
        """Generate proposal for code smell fixes."""
        lines = self._read_file_lines(issue.file_path)
        if not lines:
            return None
        
        line = lines[issue.line_number - 1] if issue.line_number <= len(lines) else ""
        
        if 'Bare except' in issue.title:
            new_line = line.replace('except Exception:', 'except Exception as e:')
            
            changes = [CodeChange(
                file_path=issue.file_path,
                change_type=ChangeType.REPLACE_CODE,
                line_start=issue.line_number,
                line_end=issue.line_number,
                old_code=line.strip(),
                new_code=new_line.strip(),
                explanation="Replace bare except with specific exception type"
            )]
            
            return Proposal(
                proposal_id=self._generate_proposal_id(),
                issue=issue,
                title="Fix bare except clause",
                description="Replace 'except Exception:' with 'except Exception as e:' to avoid catching system exceptions.",
                changes=changes,
                risk_level=RiskLevel.MINIMAL,
                risk_analysis="Minimal risk - improves exception handling without changing logic",
                expected_benefits=["Won't catch KeyboardInterrupt/SystemExit", "Access to exception details"],
                potential_drawbacks=["None"],
                testing_required="Run existing tests",
                rollback_plan="Revert to 'except Exception:'",
                estimated_effort="1 minute"
            )
        
        elif 'unused import' in issue.title.lower():
            changes = [CodeChange(
                file_path=issue.file_path,
                change_type=ChangeType.REMOVE_CODE,
                line_start=issue.line_number,
                line_end=issue.line_number,
                old_code=line.strip(),
                new_code="",
                explanation="Remove unused import"
            )]
            
            return Proposal(
                proposal_id=self._generate_proposal_id(),
                issue=issue,
                title=f"Remove unused import",
                description=f"Import appears to be unused and can be removed.",
                changes=changes,
                risk_level=RiskLevel.LOW,
                risk_analysis="Low risk - verify import is truly unused",
                expected_benefits=["Cleaner code", "Faster imports"],
                potential_drawbacks=["May break if import is used dynamically"],
                testing_required="Run tests to verify nothing breaks",
                rollback_plan="Re-add the import",
                estimated_effort="2 minutes"
            )
        
        return None
    
    def _propose_security_fix(self, issue: CodeIssue) -> Optional[Proposal]:
        if 'hardcoded secret' in issue.title.lower():
            return Proposal(
                proposal_id=self._generate_proposal_id(),
                issue=issue,
                title="Remove hardcoded secret",
                description="Hardcoded secrets should be moved to environment variables or a secure vault.",
                changes=[CodeChange(
                    file_path=issue.file_path,
                    change_type=ChangeType.REPLACE_CODE,
                    line_start=issue.line_number,
                    line_end=issue.line_number,
                    old_code="[REDACTED - contains secret]",
                    new_code='os.environ.get("SECRET_NAME", "")',
                    explanation="Replace hardcoded secret with environment variable"
                )],
                risk_level=RiskLevel.HIGH,
                risk_analysis="High risk - must ensure environment variable is set before deployment",
                potential_drawbacks=["Requires environment setup"],
                testing_required="Verify environment variable is set and accessible",
                rollback_plan="Revert to hardcoded value (NOT RECOMMENDED)",
                estimated_effort="15 minutes"
            )
        return None
    
    def _propose_maintainability_fix(self, issue: CodeIssue) -> Optional[Proposal]:
        """Generate proposal for maintainability fixes."""
        if 'Missing docstring' in issue.title:
            lines = self._read_file_lines(issue.file_path)
            if not lines:
                return None
            
            line = lines[issue.line_number - 1] if issue.line_number <= len(lines) else ""
            indent = len(line) - len(line.lstrip())
            indent_str = ' ' * (indent + 4)
            
            # Extract function/class name
            name_match = re.search(r'(def|class)\s+(\w+)', line)
            name = name_match.group(2) if name_match else "unknown"
            kind = name_match.group(1) if name_match else "def"
            
            
            changes = [CodeChange(
                file_path=issue.file_path,
                change_type=ChangeType.ADD_CODE,
                line_start=issue.line_number + 1,
                line_end=issue.line_number + 1,
                old_code="",
                new_code=docstring,
                explanation=f"Add docstring placeholder for {name}"
            )]
            
            return Proposal(
                proposal_id=self._generate_proposal_id(),
                issue=issue,
                title=f"Add docstring to {name}",
                description=f"Add documentation for {kind} '{name}'.",
                changes=changes,
                risk_level=RiskLevel.MINIMAL,
                risk_analysis="No risk - documentation only",
                expected_benefits=["Better documentation", "IDE support"],
                potential_drawbacks=["None"],
                testing_required="None",
                rollback_plan="Remove the docstring",
                estimated_effort="2 minutes"
            )
        
        elif 'Long function' in issue.title:
            return Proposal(
                proposal_id=self._generate_proposal_id(),
                issue=issue,
                title=f"Refactor long function",
                description=f"Function is too long and should be broken into smaller functions.",
                changes=[],  # Complex refactoring - no auto-changes
                risk_level=RiskLevel.HIGH,
                risk_analysis="High risk - requires careful refactoring",
                expected_benefits=["Better readability", "Easier testing", "Reusability"],
                potential_drawbacks=["Significant effort", "Risk of introducing bugs"],
                testing_required="Full test coverage before and after",
                rollback_plan="Revert all changes",
                estimated_effort="1-2 hours"
            )
        
        return None
    
    def _propose_deprecated_fix(self, issue: CodeIssue) -> Optional[Proposal]:
        """Generate proposal for deprecated pattern fixes."""
        lines = self._read_file_lines(issue.file_path)
        if not lines:
            return None
        
        line = lines[issue.line_number - 1] if issue.line_number <= len(lines) else ""
        
        if 'f-strings' in issue.description.lower() and '.format(' in line:
            # Convert .format() to f-string
            # This is a simplified conversion
            new_line = line  # Would need proper conversion logic
            
            return Proposal(
                proposal_id=self._generate_proposal_id(),
                issue=issue,
                title="Convert to f-string",
                description="Convert .format() to f-string for better readability.",
                changes=[CodeChange(
                    file_path=issue.file_path,
                    change_type=ChangeType.REPLACE_CODE,
                    line_start=issue.line_number,
                    line_end=issue.line_number,
                    old_code=line.strip(),
                    explanation="Convert .format() to f-string"
                )],
                risk_level=RiskLevel.LOW,
                risk_analysis="Low risk - equivalent functionality",
                expected_benefits=["Better readability", "Slightly faster"],
                potential_drawbacks=["None"],
                testing_required="Run tests",
                rollback_plan="Revert to .format()",
                estimated_effort="5 minutes"
            )
        
        return None
    
    def _propose_generic_fix(self, issue: CodeIssue) -> Optional[Proposal]:
        """Generate a generic proposal when no specific handler exists."""
        return Proposal(
            proposal_id=self._generate_proposal_id(),
            issue=issue,
            title=f"Review: {issue.title}",
            description=f"Issue needs manual review: {issue.description}",
            changes=[],
            risk_level=RiskLevel.MEDIUM,
            risk_analysis="Requires manual assessment",
            expected_benefits=["Issue addressed"],
            potential_drawbacks=["Unknown until reviewed"],
            testing_required="Depends on the fix",
            rollback_plan="Revert changes",
            estimated_effort="Unknown"
        )
    
    def get_pending_proposals(self) -> List[Proposal]:
        """Get all pending proposals."""
        return [p for p in self.proposals if p.status == ProposalStatus.PENDING]
    
    def get_approved_proposals(self) -> List[Proposal]:
        """Get all approved proposals."""
        return [p for p in self.proposals if p.status == ProposalStatus.APPROVED]
    
    def save_proposals(self, output_path: str) -> None:
        """Save proposals to JSON file."""
        data = {
            'generated_at': datetime.now().isoformat(),
            'total_proposals': len(self.proposals),
            'pending': len(self.get_pending_proposals()),
            'proposals': [p.to_dict() for p in self.proposals]
        }
        
        with open(output_path, 'w') as f:
            json.dump(data, f, indent=2)
        
        logger.info(f"Proposals saved to {output_path}")
    
    def load_proposals(self, input_path: str) -> None:
        """Load proposals from JSON file."""
        with open(input_path, 'r') as f:
            data = json.load(f)
        
        # Reconstruct proposals (simplified - would need full reconstruction)
        logger.info(f"Loaded {len(data.get('proposals', []))} proposals from {input_path}")
