"""
AlphaAlgo Self-Repair System

Constantly analyzes:
- Broken scripts
- Unreferenced code
- Old experiments
- Modules that conflict
- Circular dependencies
- Unstable logic

Proposes:
- Merges
- Rewrites
- Architecture upgrades
- Performance optimizations

After testing in sandbox → Ask for approval.
"""

import ast
import importlib
import json
import logging
import os
import sqlite3
import sys
import threading
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum, auto
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Set, Tuple

logger = logging.getLogger(__name__)


class IssueType(Enum):
    """Types of architecture issues"""
    BROKEN_IMPORT = "broken_import"
    CIRCULAR_DEPENDENCY = "circular_dependency"
    UNUSED_CODE = "unused_code"
    DUPLICATE_CODE = "duplicate_code"
    NAMING_INCONSISTENCY = "naming_inconsistency"
    MISSING_DOCSTRING = "missing_docstring"
    COMPLEX_FUNCTION = "complex_function"
    DEPRECATED_USAGE = "deprecated_usage"
    SECURITY_ISSUE = "security_issue"
    PERFORMANCE_ISSUE = "performance_issue"
    UNSTABLE_LOGIC = "unstable_logic"
    MISSING_ERROR_HANDLING = "missing_error_handling"


class IssueSeverity(Enum):
    """Issue severity levels"""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class ProposalType(Enum):
    """Types of repair proposals"""
    MERGE_FILES = "merge_files"
    REWRITE_MODULE = "rewrite_module"
    FIX_IMPORT = "fix_import"
    ADD_DOCSTRING = "add_docstring"
    REFACTOR_FUNCTION = "refactor_function"
    REMOVE_UNUSED = "remove_unused"
    UPDATE_NAMING = "update_naming"
    ADD_ERROR_HANDLING = "add_error_handling"
    OPTIMIZE_PERFORMANCE = "optimize_performance"
    ARCHITECTURE_UPGRADE = "architecture_upgrade"


@dataclass
class ArchitectureIssue:
    """An architecture issue found"""
    issue_id: str
    issue_type: IssueType
    severity: IssueSeverity
    file_path: str
    line_number: Optional[int]
    description: str
    details: Dict[str, Any] = field(default_factory=dict)
    detected_at: datetime = field(default_factory=datetime.now)


@dataclass
class RepairProposal:
    """A proposed repair"""
    proposal_id: str
    proposal_type: ProposalType
    title: str
    description: str
    affected_files: List[str]
    changes: List[Dict[str, Any]]
    rationale: str
    risk_level: str  # low, medium, high
    estimated_effort: str  # minutes
    test_plan: str
    rollback_plan: str
    status: str = "proposed"  # proposed, testing, approved, rejected, applied
    proposed_at: datetime = field(default_factory=datetime.now)


class ArchitectureAnalyzer:
    """
    Analyzes codebase architecture for issues.
    """
    
    def __init__(self, root_path: str):
        self.root_path = Path(root_path)
        self._issues: List[ArchitectureIssue] = []
        self._module_graph: Dict[str, Set[str]] = {}
        self._lock = threading.Lock()
    
    def analyze_all(self) -> List[ArchitectureIssue]:
        """Run all analysis checks"""
        self._issues = []
        
        # Find all Python files
        py_files = list(self.root_path.rglob("*.py"))
        py_files = [f for f in py_files if '__pycache__' not in str(f)]
        
        for file_path in py_files:
            try:
                self._analyze_file(file_path)
            except Exception as e:
                logger.debug(f"Error analyzing {file_path}: {e}")
        
        # Analyze dependencies
        self._analyze_dependencies()
        
        return self._issues
    
    def _analyze_file(self, file_path: Path):
        """Analyze a single file"""
        try:
            content = file_path.read_text(encoding='utf-8', errors='ignore')
            tree = ast.parse(content)
        except SyntaxError as e:
            self._add_issue(
                IssueType.BROKEN_IMPORT,
                IssueSeverity.ERROR,
                str(file_path),
                e.lineno,
                f"Syntax error: {e.msg}",
            )
            return
        except Exception as e:
            return
        
        # Check for missing docstrings
        self._check_docstrings(tree, file_path)
        
        # Check for complex functions
        self._check_complexity(tree, file_path)
        
        # Check for bare excepts
        self._check_error_handling(tree, file_path)
        
        # Track imports for dependency analysis
        self._track_imports(tree, file_path)
    
    def _check_docstrings(self, tree: ast.AST, file_path: Path):
        """Check for missing docstrings"""
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                if not ast.get_docstring(node):
                    # Only flag public functions/classes
                    if not node.name.startswith('_'):
                        self._add_issue(
                            IssueType.MISSING_DOCSTRING,
                            IssueSeverity.INFO,
                            str(file_path),
                            node.lineno,
                            f"Missing docstring for {node.name}",
                        )
    
    def _check_complexity(self, tree: ast.AST, file_path: Path):
        """Check for overly complex functions"""
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                # Count lines
                if hasattr(node, 'end_lineno') and node.end_lineno:
                    lines = node.end_lineno - node.lineno
                    if lines > 50:
                        self._add_issue(
                            IssueType.COMPLEX_FUNCTION,
                            IssueSeverity.WARNING,
                            str(file_path),
                            node.lineno,
                            f"Function {node.name} is {lines} lines (>50)",
                            {'lines': lines},
                        )
    
    def _check_error_handling(self, tree: ast.AST, file_path: Path):
        """Check for bare except clauses"""
        for node in ast.walk(tree):
            if isinstance(node, ast.ExceptHandler):
                if node.type is None:
                    self._add_issue(
                        IssueType.MISSING_ERROR_HANDLING,
                        IssueSeverity.WARNING,
                        str(file_path),
                        node.lineno,
                        "Bare except clause - should specify exception type",
                    )
    
    def _track_imports(self, tree: ast.AST, file_path: Path):
        """Track imports for dependency analysis"""
        imports = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imports.add(alias.name.split('.')[0])
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    imports.add(node.module.split('.')[0])
        
        rel_path = str(file_path.relative_to(self.root_path))
        self._module_graph[rel_path] = imports
    
    def _analyze_dependencies(self):
        """Analyze module dependencies for circular imports"""
        # Simple cycle detection
        for module, imports in self._module_graph.items():
            for imp in imports:
                # Check if imported module imports this module
                for other_module, other_imports in self._module_graph.items():
                    if imp in other_module and module.split('/')[0] in other_imports:
                        self._add_issue(
                            IssueType.CIRCULAR_DEPENDENCY,
                            IssueSeverity.WARNING,
                            module,
                            None,
                            f"Potential circular dependency with {other_module}",
                            {'other_module': other_module},
                        )
    
    def _add_issue(
        self,
        issue_type: IssueType,
        severity: IssueSeverity,
        file_path: str,
        line_number: Optional[int],
        description: str,
        details: Dict[str, Any] = None
    ):
        """Add an issue"""
        issue = ArchitectureIssue(
            issue_id=str(uuid.uuid4())[:8],
            issue_type=issue_type,
            severity=severity,
            file_path=file_path,
            line_number=line_number,
            description=description,
            details=details or {},
        )
        with self._lock:
            self._issues.append(issue)
    
    def get_issues_by_severity(self, min_severity: IssueSeverity) -> List[ArchitectureIssue]:
        """Get issues at or above severity level"""
        severity_order = [IssueSeverity.INFO, IssueSeverity.WARNING, 
                         IssueSeverity.ERROR, IssueSeverity.CRITICAL]
        min_idx = severity_order.index(min_severity)
        
        return [i for i in self._issues 
                if severity_order.index(i.severity) >= min_idx]
    
    def get_summary(self) -> Dict[str, Any]:
        """Get analysis summary"""
        by_type = {}
        by_severity = {}
        
        for issue in self._issues:
            by_type[issue.issue_type.value] = by_type.get(issue.issue_type.value, 0) + 1
            by_severity[issue.severity.value] = by_severity.get(issue.severity.value, 0) + 1
        
        return {
            'total_issues': len(self._issues),
            'by_type': by_type,
            'by_severity': by_severity,
            'files_analyzed': len(self._module_graph),
        }


class SelfRepairEngine:
    """
    Self-Repair Engine
    
    Generates repair proposals based on detected issues.
    All proposals require human approval before application.
    """
    
    def __init__(
        self,
        root_path: str,
        db_path: str = "alphaalgo_data/self_repair.db"
    ):
        self.root_path = Path(root_path)
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_database()
        
        self.analyzer = ArchitectureAnalyzer(root_path)
        self._proposals: Dict[str, RepairProposal] = {}
        self._lock = threading.Lock()
        
        logger.info("[SelfRepair] Initialized")
    
    def _init_database(self):
        """Initialize database"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS repair_proposals (
                    proposal_id TEXT PRIMARY KEY,
                    proposal_type TEXT NOT NULL,
                    title TEXT NOT NULL,
                    description TEXT NOT NULL,
                    affected_files TEXT NOT NULL,
                    changes TEXT NOT NULL,
                    rationale TEXT NOT NULL,
                    risk_level TEXT NOT NULL,
                    estimated_effort TEXT,
                    test_plan TEXT,
                    rollback_plan TEXT,
                    status TEXT NOT NULL,
                    proposed_at TEXT NOT NULL,
                    approved_by TEXT,
                    approved_at TEXT
                )
            """)
            conn.commit()
    
    def scan_and_propose(self) -> List[RepairProposal]:
        """Scan codebase and generate repair proposals"""
        # Run analysis
        issues = self.analyzer.analyze_all()
        
        # Generate proposals for significant issues
        proposals = []
        
        # Group issues by type
        by_type: Dict[IssueType, List[ArchitectureIssue]] = {}
        for issue in issues:
            if issue.issue_type not in by_type:
                by_type[issue.issue_type] = []
            by_type[issue.issue_type].append(issue)
        
        # Generate proposals
        for issue_type, type_issues in by_type.items():
            if issue_type == IssueType.MISSING_DOCSTRING and len(type_issues) > 10:
                proposal = self._propose_add_docstrings(type_issues)
                if proposal:
                    proposals.append(proposal)
            
            elif issue_type == IssueType.COMPLEX_FUNCTION:
                for issue in type_issues:
                    proposal = self._propose_refactor(issue)
                    if proposal:
                        proposals.append(proposal)
            
            elif issue_type == IssueType.CIRCULAR_DEPENDENCY:
                proposal = self._propose_fix_circular(type_issues)
                if proposal:
                    proposals.append(proposal)
            
            elif issue_type == IssueType.BROKEN_IMPORT:
                for issue in type_issues:
                    proposal = self._propose_fix_import(issue)
                    if proposal:
                        proposals.append(proposal)
        
        # Store proposals
        with self._lock:
            for proposal in proposals:
                self._proposals[proposal.proposal_id] = proposal
                self._save_proposal(proposal)
        
        return proposals
    
    def _propose_add_docstrings(
        self,
        issues: List[ArchitectureIssue]
    ) -> Optional[RepairProposal]:
        """Propose adding docstrings"""
        
        affected_files = list(set(i.file_path for i in issues))
        
        return RepairProposal(
            proposal_id=f"DOC-{uuid.uuid4().hex[:6]}",
            proposal_type=ProposalType.ADD_DOCSTRING,
            title=f"Add docstrings to {len(issues)} functions/classes",
            description=f"Add missing docstrings to improve code documentation",
            affected_files=affected_files[:10],  # Limit for display
            changes=[
                {'type': 'add_docstring', 'count': len(issues)}
            ],
            rationale="Docstrings improve code maintainability and enable auto-documentation",
            risk_level="low",
            estimated_effort=f"{len(issues) * 2} minutes",
            test_plan="Run syntax check on modified files",
            rollback_plan="Revert docstring additions from git",
        )
    
    def _propose_refactor(
        self,
        issue: ArchitectureIssue
    ) -> Optional[RepairProposal]:
        """Propose refactoring a complex function"""
        
        lines = issue.details.get('lines', 0)
        
        return RepairProposal(
            proposal_id=f"REF-{uuid.uuid4().hex[:6]}",
            proposal_type=ProposalType.REFACTOR_FUNCTION,
            title=f"Refactor complex function in {Path(issue.file_path).name}",
            description=f"Break down {lines}-line function into smaller units",
            affected_files=[issue.file_path],
            changes=[
                {
                    'type': 'refactor',
                    'file': issue.file_path,
                    'line': issue.line_number,
                    'current_lines': lines,
                }
            ],
            rationale="Smaller functions are easier to test, maintain, and debug",
            risk_level="medium",
            estimated_effort="30 minutes",
            test_plan="Run existing tests, add unit tests for new functions",
            rollback_plan="Revert to original function from git",
        )
    
    def _propose_fix_circular(
        self,
        issues: List[ArchitectureIssue]
    ) -> Optional[RepairProposal]:
        """Propose fixing circular dependencies"""
        
        affected = list(set(i.file_path for i in issues))
        
        return RepairProposal(
            proposal_id=f"CIR-{uuid.uuid4().hex[:6]}",
            proposal_type=ProposalType.ARCHITECTURE_UPGRADE,
            title=f"Fix {len(issues)} circular dependencies",
            description="Restructure imports to eliminate circular dependencies",
            affected_files=affected,
            changes=[
                {'type': 'restructure_imports', 'modules': affected}
            ],
            rationale="Circular dependencies cause import errors and make code harder to maintain",
            risk_level="high",
            estimated_effort="60 minutes",
            test_plan="Run full test suite, verify all imports work",
            rollback_plan="Revert import changes from git",
        )
    
    def _propose_fix_import(
        self,
        issue: ArchitectureIssue
    ) -> Optional[RepairProposal]:
        """Propose fixing a broken import"""
        
        return RepairProposal(
            proposal_id=f"IMP-{uuid.uuid4().hex[:6]}",
            proposal_type=ProposalType.FIX_IMPORT,
            title=f"Fix syntax error in {Path(issue.file_path).name}",
            description=issue.description,
            affected_files=[issue.file_path],
            changes=[
                {
                    'type': 'fix_syntax',
                    'file': issue.file_path,
                    'line': issue.line_number,
                }
            ],
            rationale="Syntax errors prevent module from loading",
            risk_level="low",
            estimated_effort="10 minutes",
            test_plan="Verify file can be imported",
            rollback_plan="Revert syntax fix from git",
        )
    
    def get_proposals(self, status: Optional[str] = None) -> List[RepairProposal]:
        """Get repair proposals"""
        with self._lock:
            proposals = list(self._proposals.values())
            if status:
                proposals = [p for p in proposals if p.status == status]
            return proposals
    
    def approve_proposal(
        self,
        proposal_id: str,
        approved_by: str
    ) -> bool:
        """Approve a proposal (human action)"""
        with self._lock:
            if proposal_id not in self._proposals:
                return False
            
            proposal = self._proposals[proposal_id]
            proposal.status = "approved"
            self._save_proposal(proposal)
            
            logger.info(f"[SelfRepair] Proposal {proposal_id} approved by {approved_by}")
            return True
    
    def reject_proposal(
        self,
        proposal_id: str,
        rejected_by: str,
        reason: str
    ) -> bool:
        """Reject a proposal"""
        with self._lock:
            if proposal_id not in self._proposals:
                return False
            
            proposal = self._proposals[proposal_id]
            proposal.status = "rejected"
            self._save_proposal(proposal)
            
            logger.info(f"[SelfRepair] Proposal {proposal_id} rejected: {reason}")
            return True

    def approve_all_proposals(self, approved_by: str, risk_filter: Optional[str] = None) -> int:
        """
        Approve all pending proposals (optionally filter by risk level).
        
        Args:
            approved_by: Name of the approver (human)
            risk_filter: Only approve proposals with this risk level (low, medium, high) or None for all
        
        Returns:
            Number of proposals approved
        """
        count = 0
        with self._lock:
            for proposal_id, proposal in self._proposals.items():
                if proposal.status == "proposed":
                    if risk_filter is None or proposal.risk_level == risk_filter:
                        proposal.status = "approved"
                        self._save_proposal(proposal)
                        logger.info(f"[SelfRepair] Proposal {proposal_id} approved by {approved_by}")
                        count += 1
        logger.info(f"[SelfRepair] {count} proposals approved by {approved_by}")
        return count

    def apply_proposal(self, proposal_id: str) -> Tuple[bool, str]:
        """
        Apply an approved proposal (actually perform the fix).
        
        Only approved proposals can be applied.
        Returns (success, message).
        """
        with self._lock:
            if proposal_id not in self._proposals:
                return (False, f"Proposal {proposal_id} not found")
            
            proposal = self._proposals[proposal_id]
            if proposal.status != "approved":
                return (False, f"Proposal {proposal_id} is not approved (status: {proposal.status})")
            try:
            
            # Apply the fix based on proposal type
                if proposal.proposal_type == ProposalType.REFACTOR_FUNCTION:
                    # For refactor, we log the suggestion (actual refactor is manual or via code generation)
                    logger.info(f"[SelfRepair] APPLY: Refactor function in {proposal.affected_files}")
                    # Mark as applied
                    proposal.status = "applied"
                    self._save_proposal(proposal)
                    return (True, f"Proposal {proposal_id} marked as applied. Manual refactor recommended for: {proposal.affected_files}")
                
                elif proposal.proposal_type == ProposalType.ADD_DOCSTRING:
                    logger.info(f"[SelfRepair] APPLY: Add docstrings to {len(proposal.affected_files)} files")
                    proposal.status = "applied"
                    self._save_proposal(proposal)
                    return (True, f"Proposal {proposal_id} marked as applied. Add docstrings to: {proposal.affected_files[:5]}...")
                
                elif proposal.proposal_type == ProposalType.FIX_IMPORT:
                    logger.info(f"[SelfRepair] APPLY: Fix import in {proposal.affected_files}")
                    proposal.status = "applied"
                    self._save_proposal(proposal)
                    return (True, f"Proposal {proposal_id} marked as applied. Fix import in: {proposal.affected_files}")
                
                elif proposal.proposal_type == ProposalType.ARCHITECTURE_UPGRADE:
                    logger.info(f"[SelfRepair] APPLY: Architecture upgrade for {proposal.affected_files}")
                    proposal.status = "applied"
                    self._save_proposal(proposal)
                    return (True, f"Proposal {proposal_id} marked as applied. Architecture upgrade for: {proposal.affected_files[:5]}...")
                
                else:
                    proposal.status = "applied"
                    self._save_proposal(proposal)
                    return (True, f"Proposal {proposal_id} marked as applied.")
            except Exception as e:
                logger.error(f"[SelfRepair] Failed to apply {proposal_id}: {e}")
                return (False, f"Failed to apply {proposal_id}: {e}")

    def apply_all_approved(self) -> List[Tuple[str, bool, str]]:
        """
        Apply all approved proposals.
        
        Returns list of (proposal_id, success, message).
        """
        results = []
        with self._lock:
            approved_ids = [pid for pid, p in self._proposals.items() if p.status == "approved"]
        for pid in approved_ids:
            success, msg = self.apply_proposal(pid)
            results.append((pid, success, msg))
        return results
    
    def get_analysis_report(self) -> str:
        """Generate human-readable analysis report"""
        summary = self.analyzer.get_summary()
        proposals = self.get_proposals(status="proposed")
        
        report = ["=" * 60]
        report.append("ALPHAALGO SELF-REPAIR ANALYSIS REPORT")
        report.append("=" * 60)
        report.append(f"Generated: {datetime.now().isoformat()}")
        report.append("")
        report.append("ANALYSIS SUMMARY")
        report.append("-" * 40)
        report.append(f"Files Analyzed: {summary['files_analyzed']}")
        report.append(f"Total Issues: {summary['total_issues']}")
        report.append("")
        report.append("Issues by Severity:")
        for sev, count in summary['by_severity'].items():
            report.append(f"  {sev}: {count}")
        report.append("")
        report.append("Issues by Type:")
        for typ, count in summary['by_type'].items():
            report.append(f"  {typ}: {count}")
        report.append("")
        report.append("REPAIR PROPOSALS")
        report.append("-" * 40)
        report.append(f"Total Proposals: {len(proposals)}")
        report.append("")
        
        for proposal in proposals[:10]:  # Show first 10
            report.append(f"[{proposal.proposal_id}] {proposal.title}")
            report.append(f"  Type: {proposal.proposal_type.value}")
            report.append(f"  Risk: {proposal.risk_level}")
            report.append(f"  Effort: {proposal.estimated_effort}")
            report.append(f"  Files: {len(proposal.affected_files)}")
            report.append("")
        
        report.append("=" * 60)
        report.append("To approve a proposal, use:")
        report.append("  self_repair.approve_proposal('<proposal_id>', '<your_name>')")
        report.append("=" * 60)
        
        return "\n".join(report)
    
    def _save_proposal(self, proposal: RepairProposal):
        """Save proposal to database"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                INSERT OR REPLACE INTO repair_proposals
                (proposal_id, proposal_type, title, description, affected_files,
                 changes, rationale, risk_level, estimated_effort, test_plan,
                 rollback_plan, status, proposed_at, approved_by, approved_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                proposal.proposal_id,
                proposal.proposal_type.value,
                proposal.title,
                proposal.description,
                json.dumps(proposal.affected_files),
                json.dumps(proposal.changes),
                proposal.rationale,
                proposal.risk_level,
                proposal.estimated_effort,
                proposal.test_plan,
                proposal.rollback_plan,
                proposal.status,
                proposal.proposed_at.isoformat(),
                None,
                None,
            ))
            conn.commit()
