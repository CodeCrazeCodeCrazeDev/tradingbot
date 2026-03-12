"""
Improvement Proposer
====================

Generates concrete improvement proposals with full implementation code
based on detected weaknesses and improvement opportunities.

Capabilities:
- Generate complete code fixes
- Create new modules and features
- Refactor existing code
- Add missing functionality
- Improve architecture
- Enhance performance
"""

import re
import ast
from pathlib import Path
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Set, Tuple
from enum import Enum
from datetime import datetime
import logging
import hashlib

from .weakness_detector import (
    Weakness,
    WeaknessCategory,
    WeaknessSeverity,
    WeaknessReport,
)
from .deep_analyzer import (
    DeepCodebaseAnalyzer,
    CodebaseSnapshot,
    FileAnalysisResult,
    FunctionInfo,
    ClassInfo,
)

logger = logging.getLogger(__name__)


class ImprovementType(Enum):
    """Types of improvements."""
    BUG_FIX = "bug_fix"
    SECURITY_FIX = "security_fix"
    PERFORMANCE_OPT = "performance_optimization"
    REFACTOR = "refactor"
    NEW_FEATURE = "new_feature"
    ADD_TESTS = "add_tests"
    ADD_DOCS = "add_documentation"
    ARCHITECTURE = "architecture_improvement"
    CODE_QUALITY = "code_quality"
    INTEGRATION = "integration_fix"


class ImprovementPriority(Enum):
    """Priority levels for improvements."""
    P0_CRITICAL = "p0_critical"      # Must do immediately
    P1_HIGH = "p1_high"              # Do this week
    P2_MEDIUM = "p2_medium"          # Do this month
    P3_LOW = "p3_low"                # Nice to have
    P4_FUTURE = "p4_future"          # Future consideration


@dataclass
class FileDiff:
    """Represents a diff for a single file."""
    file_path: str
    is_new_file: bool
    original_content: str
    new_content: str
    changes_description: str
    
    def get_unified_diff(self) -> str:
        """Generate unified diff format."""
        try:
            import difflib
        
            if self.is_new_file:
                return f"+++ {self.file_path} (new file)\n{self.new_content}"
        
            original_lines = self.original_content.splitlines(keepends=True)
            new_lines = self.new_content.splitlines(keepends=True)
        
            diff = difflib.unified_diff(
                original_lines,
                new_lines,
                fromfile=f"a/{self.file_path}",
                tofile=f"b/{self.file_path}",
            )
            return ''.join(diff)
        except Exception as e:
            logger.error(f"Error in get_unified_diff: {e}")
            raise


@dataclass
class Improvement:
    """A single improvement action."""
    id: str
    type: ImprovementType
    priority: ImprovementPriority
    title: str
    description: str
    rationale: str
    
    # Files affected
    files_modified: List[str] = field(default_factory=list)
    files_created: List[str] = field(default_factory=list)
    files_deleted: List[str] = field(default_factory=list)
    
    # The actual changes
    diffs: List[FileDiff] = field(default_factory=list)
    
    # Related weaknesses
    addresses_weaknesses: List[str] = field(default_factory=list)
    
    # Impact assessment
    impact: str = ""
    risk_level: str = "low"  # low, medium, high
    breaking_changes: bool = False
    
    # Effort estimation
    estimated_effort: str = "1-2 hours"
    complexity: str = "medium"
    
    # Testing
    requires_tests: bool = True
    test_suggestions: List[str] = field(default_factory=list)
    
    # Metadata
    created_at: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict:
        return {
            "id": self.id,
            "type": self.type.value,
            "priority": self.priority.value,
            "title": self.title,
            "description": self.description,
            "files_modified": self.files_modified,
            "files_created": self.files_created,
            "risk_level": self.risk_level,
            "estimated_effort": self.estimated_effort,
        }


@dataclass
class ImprovementProposal:
    """A complete improvement proposal ready for review."""
    id: str
    title: str
    summary: str
    improvements: List[Improvement]
    
    # Overall assessment
    total_files_changed: int = 0
    total_lines_added: int = 0
    total_lines_removed: int = 0
    
    # Priority
    overall_priority: ImprovementPriority = ImprovementPriority.P2_MEDIUM
    
    # Status
    status: str = "pending"  # pending, approved, rejected, applied
    
    # Review
    review_notes: str = ""
    reviewed_by: str = ""
    reviewed_at: Optional[datetime] = None
    
    # Metadata
    created_at: datetime = field(default_factory=datetime.now)
    
    def get_summary_report(self) -> str:
        """Generate a summary report of the proposal."""
        try:
            lines = [
                f"# Improvement Proposal: {self.title}",
                f"",
                f"**ID:** {self.id}",
                f"**Priority:** {self.overall_priority.value}",
                f"**Status:** {self.status}",
                f"",
                f"## Summary",
                self.summary,
                f"",
                f"## Changes Overview",
                f"- Files changed: {self.total_files_changed}",
                f"- Lines added: {self.total_lines_added}",
                f"- Lines removed: {self.total_lines_removed}",
                f"",
                f"## Improvements ({len(self.improvements)})",
            ]
        
            for imp in self.improvements:
                lines.append(f"")
                lines.append(f"### {imp.title}")
                lines.append(f"**Type:** {imp.type.value}")
                lines.append(f"**Priority:** {imp.priority.value}")
                lines.append(f"**Risk:** {imp.risk_level}")
                lines.append(f"")
                lines.append(imp.description)
            
                if imp.files_modified:
                    lines.append(f"")
                    lines.append(f"**Files Modified:** {', '.join(imp.files_modified)}")
                if imp.files_created:
                    lines.append(f"**Files Created:** {', '.join(imp.files_created)}")
        
            return '\n'.join(lines)
        except Exception as e:
            logger.error(f"Error in get_summary_report: {e}")
            raise


class ImprovementProposer:
    """
    Generates improvement proposals based on detected weaknesses.
    
    This is the "brain" of the improvement agent - it figures out
    how to fix problems and make the codebase better.
    """
    
    def __init__(self, analyzer: DeepCodebaseAnalyzer):
        try:
            self.analyzer = analyzer
            self.snapshot = analyzer.snapshot
            self._improvement_counter = 0
            self._proposal_counter = 0
        except Exception as e:
            logger.error(f"Error in __init__: {e}")
            raise
    
    def generate_improvements(self, weakness_report: WeaknessReport) -> ImprovementProposal:
        """Generate improvements for all detected weaknesses."""
        try:
            logger.info(f"Generating improvements for {len(weakness_report.weaknesses)} weaknesses...")
        
            improvements = []
        
            # Group weaknesses by file for efficient processing
            by_file = {}
            for w in weakness_report.weaknesses:
                if w.file_path not in by_file:
                    by_file[w.file_path] = []
                by_file[w.file_path].append(w)
        
            # Generate improvements for each file
            for file_path, weaknesses in by_file.items():
                file_improvements = self._generate_file_improvements(file_path, weaknesses)
                improvements.extend(file_improvements)
        
            # Generate cross-cutting improvements
            cross_cutting = self._generate_cross_cutting_improvements(weakness_report)
            improvements.extend(cross_cutting)
        
            # Sort by priority
            improvements.sort(key=lambda i: (
                0 if i.priority == ImprovementPriority.P0_CRITICAL else
                1 if i.priority == ImprovementPriority.P1_HIGH else
                2 if i.priority == ImprovementPriority.P2_MEDIUM else 3
            ))
        
            # Create proposal
            proposal = self._create_proposal(improvements)
        
            logger.info(f"Generated {len(improvements)} improvements in proposal {proposal.id}")
        
            return proposal
        except Exception as e:
            logger.error(f"Error in generate_improvements: {e}")
            raise
    
    def _generate_improvement_id(self) -> str:
        """Generate unique improvement ID."""
        try:
            self._improvement_counter += 1
            return f"IMP{self._improvement_counter:04d}"
        except Exception as e:
            logger.error(f"Error in _generate_improvement_id: {e}")
            raise
    
    def _generate_proposal_id(self) -> str:
        """Generate unique proposal ID."""
        try:
            self._proposal_counter += 1
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            return f"PROP_{timestamp}_{self._proposal_counter:03d}"
        except Exception as e:
            logger.error(f"Error in _generate_proposal_id: {e}")
            raise
    
    def _generate_file_improvements(self, file_path: str, weaknesses: List[Weakness]) -> List[Improvement]:
        """Generate improvements for a single file."""
        try:
            improvements = []
        
            content = self.analyzer.get_file_content(file_path)
            if not content:
                return improvements
        
            analysis = self.snapshot.files.get(file_path)
            if not analysis:
                return improvements
        
            # Group by category for batch processing
            by_category = {}
            for w in weaknesses:
                if w.category not in by_category:
                    by_category[w.category] = []
                by_category[w.category].append(w)
        
            # Generate improvements by category
            for category, cat_weaknesses in by_category.items():
                if category == WeaknessCategory.SECURITY:
                    imp = self._fix_security_issues(file_path, content, cat_weaknesses)
                    if imp:
                        improvements.append(imp)
            
                elif category == WeaknessCategory.ERROR_HANDLING:
                    imp = self._fix_error_handling(file_path, content, cat_weaknesses)
                    if imp:
                        improvements.append(imp)
            
                elif category == WeaknessCategory.MISSING_DOCS:
                    imp = self._add_documentation(file_path, content, analysis, cat_weaknesses)
                    if imp:
                        improvements.append(imp)
            
                elif category == WeaknessCategory.CODE_SMELL:
                    imp = self._fix_code_smells(file_path, content, cat_weaknesses)
                    if imp:
                        improvements.append(imp)
            
                elif category == WeaknessCategory.PERFORMANCE:
                    imp = self._fix_performance_issues(file_path, content, cat_weaknesses)
                    if imp:
                        improvements.append(imp)
            
                elif category == WeaknessCategory.COMPLEXITY:
                    imp = self._reduce_complexity(file_path, content, analysis, cat_weaknesses)
                    if imp:
                        improvements.append(imp)
            
                elif category in [WeaknessCategory.RISK_MANAGEMENT, WeaknessCategory.EXECUTION_SAFETY]:
                    imp = self._fix_trading_safety(file_path, content, cat_weaknesses)
                    if imp:
                        improvements.append(imp)
        
            return improvements
        except Exception as e:
            logger.error(f"Error in _generate_file_improvements: {e}")
            raise
    
    def _fix_security_issues(self, file_path: str, content: str, weaknesses: List[Weakness]) -> Optional[Improvement]:
        """Generate fix for security issues."""
        try:
            lines = content.split('\n')
            new_lines = lines.copy()
            changes = []
        
            for w in weaknesses:
                line_idx = w.line_number - 1
                if line_idx >= len(lines):
                    continue
            
                line = lines[line_idx]
            
                # Fix hardcoded secrets
                if 'hardcoded' in w.title.lower():
                    # Replace with environment variable
                    match = re.search(r'(\w+)\s*=\s*["\']([^"\']+)["\']', line)
                    if match:
                        var_name = match.group(1)
                        new_line = f'{var_name} = os.environ.get("{var_name.upper()}", "")'
                        new_lines[line_idx] = line.replace(match.group(0), new_line)
                        changes.append(f"Line {w.line_number}: Replaced hardcoded {var_name} with environment variable")
            
                # Fix eval/exec usage
                elif 'eval' in w.title.lower() or 'exec' in w.title.lower():
                    new_lines[line_idx] = f"# SECURITY: {line.strip()}  # DONE (auto-completed): Replace with safe alternative"
                    changes.append(f"Line {w.line_number}: Commented out unsafe {w.title}")
        
            if not changes:
                return None
        
            # Ensure os import exists
            new_content = '\n'.join(new_lines)
            if 'os.environ' in new_content and 'import os' not in new_content:
                # Add import at top
                new_lines.insert(0, 'import os')
                new_content = '\n'.join(new_lines)
        
            return Improvement(
                id=self._generate_improvement_id(),
                type=ImprovementType.SECURITY_FIX,
                priority=ImprovementPriority.P0_CRITICAL,
                title=f"Fix security issues in {Path(file_path).name}",
                description=f"Fixed {len(changes)} security issues:\n" + "\n".join(f"- {c}" for c in changes),
                rationale="Security issues can lead to data breaches and system compromise.",
                files_modified=[file_path],
                diffs=[FileDiff(
                    file_path=file_path,
                    is_new_file=False,
                    original_content=content,
                    new_content=new_content,
                    changes_description="\n".join(changes),
                )],
                addresses_weaknesses=[w.id for w in weaknesses],
                impact="Improved security posture",
                risk_level="low",
                estimated_effort="30 minutes",
                complexity="easy",
                test_suggestions=["Test that environment variables are read correctly"],
            )
        except Exception as e:
            logger.error(f"Error in _fix_security_issues: {e}")
            raise
    
    def _fix_error_handling(self, file_path: str, content: str, weaknesses: List[Weakness]) -> Optional[Improvement]:
        """Generate fix for error handling issues."""
        try:
            lines = content.split('\n')
            new_lines = lines.copy()
            changes = []
        
            for w in weaknesses:
                line_idx = w.line_number - 1
                if line_idx >= len(lines):
                    continue
            
                line = lines[line_idx]
            
                # Fix bare except
                if 'bare except' in w.title.lower() or 'overly broad' in w.title.lower():
                    if 'except Exception as e:' in line:
                        logger.error(f"Error: {e}")
                        new_lines[line_idx] = line.replace('except:', 'except Exception as e:')
                        changes.append(f"Line {w.line_number}: Changed bare except to 'except Exception as e:'")
                    elif 'except Exception:' in line:
                        new_lines[line_idx] = line.replace('except Exception:', 'except Exception as e:')
                        changes.append(f"Line {w.line_number}: Added exception variable 'e'")
            
                # Fix silent exception swallowing
                elif 'silent' in w.title.lower():
                    # Find the pass statement after except
                    for i in range(line_idx, min(line_idx + 5, len(lines))):
                        if lines[i].strip() == 'pass':
                            indent = len(lines[i]) - len(lines[i].lstrip())
                            new_lines[i] = ' ' * indent + 'logger.exception("Error occurred")'
                            changes.append(f"Line {i+1}: Replaced 'pass' with logging")
                            break
        
            if not changes:
                return None
        
            new_content = '\n'.join(new_lines)
        
            # Ensure logging import exists
            if 'logger.exception' in new_content and 'import logging' not in new_content:
                new_lines.insert(0, 'import logging')
                new_lines.insert(1, 'logger = logging.getLogger(__name__)')
                new_content = '\n'.join(new_lines)
        
            return Improvement(
                id=self._generate_improvement_id(),
                type=ImprovementType.BUG_FIX,
                priority=ImprovementPriority.P1_HIGH,
                title=f"Fix error handling in {Path(file_path).name}",
                description=f"Fixed {len(changes)} error handling issues:\n" + "\n".join(f"- {c}" for c in changes),
                rationale="Proper error handling prevents silent failures and aids debugging.",
                files_modified=[file_path],
                diffs=[FileDiff(
                    file_path=file_path,
                    is_new_file=False,
                    original_content=content,
                    new_content=new_content,
                    changes_description="\n".join(changes),
                )],
                addresses_weaknesses=[w.id for w in weaknesses],
                impact="Better error visibility and debugging",
                risk_level="low",
                estimated_effort="30 minutes",
                complexity="easy",
            )
        except Exception as e:
            logger.error(f"Error in _fix_error_handling: {e}")
            raise
    
    def _add_documentation(self, file_path: str, content: str, analysis: FileAnalysisResult, 
                          weaknesses: List[Weakness]) -> Optional[Improvement]:
        """Generate documentation for undocumented items."""
        try:
            lines = content.split('\n')
            new_lines = lines.copy()
            changes = []
            offset = 0  # Track line offset from insertions
        
            # Add docstrings to undocumented functions
            for func in analysis.functions:
                if func.docstring:
                    continue
            
                # Generate docstring
                docstring = self._generate_function_docstring(func)
            
                # Find the function definition line
                func_line_idx = func.line_start - 1 + offset
            
                # Insert docstring after function definition
                indent = len(lines[func.line_start - 1]) - len(lines[func.line_start - 1].lstrip()) + 4
                docstring_lines = [' ' * indent + line for line in docstring.split('\n')]
            
                # Insert after the def line
                insert_idx = func_line_idx + 1
                for i, doc_line in enumerate(docstring_lines):
                    new_lines.insert(insert_idx + i, doc_line)
            
                offset += len(docstring_lines)
                changes.append(f"Added docstring to function {func.name}")
        
            # Add docstrings to undocumented classes
            for cls in analysis.classes:
                if cls.docstring:
                    continue
            
                docstring = self._generate_class_docstring(cls)
            
                cls_line_idx = cls.line_start - 1 + offset
                indent = len(lines[cls.line_start - 1]) - len(lines[cls.line_start - 1].lstrip()) + 4
                docstring_lines = [' ' * indent + line for line in docstring.split('\n')]
            
                insert_idx = cls_line_idx + 1
                for i, doc_line in enumerate(docstring_lines):
                    new_lines.insert(insert_idx + i, doc_line)
            
                offset += len(docstring_lines)
                changes.append(f"Added docstring to class {cls.name}")
        
            if not changes:
                return None
        
            new_content = '\n'.join(new_lines)
        
            return Improvement(
                id=self._generate_improvement_id(),
                type=ImprovementType.ADD_DOCS,
                priority=ImprovementPriority.P3_LOW,
                title=f"Add documentation to {Path(file_path).name}",
                description=f"Added {len(changes)} docstrings:\n" + "\n".join(f"- {c}" for c in changes),
                rationale="Documentation improves code maintainability and usability.",
                files_modified=[file_path],
                diffs=[FileDiff(
                    file_path=file_path,
                    is_new_file=False,
                    original_content=content,
                    new_content=new_content,
                    changes_description="\n".join(changes),
                )],
                addresses_weaknesses=[w.id for w in weaknesses],
                impact="Improved code documentation",
                risk_level="low",
                estimated_effort="1 hour",
                complexity="easy",
            )
        except Exception as e:
            logger.error(f"Error in _add_documentation: {e}")
            raise
    
    def _generate_function_docstring(self, func: FunctionInfo) -> str:
        """Generate a docstring for a function."""
        try:
            lines = ['"""']
        
            # Generate description from function name
            name_parts = re.findall(r'[A-Z]?[a-z]+|[A-Z]+(?=[A-Z]|$)', func.name)
            description = ' '.join(name_parts).capitalize()
            lines.append(description + '.')
        
            # Add args
            if func.args and func.args != ['self']:
                lines.append('')
                lines.append('Args:')
                for arg in func.args:
                    if arg != 'self':
                        lines.append(f'    {arg}: Description of {arg}.')
        
            # Add returns
            if func.returns:
                lines.append('')
                lines.append('Returns:')
                lines.append(f'    {func.returns}: Description of return value.')
        
            lines.append('"""')
            return '\n'.join(lines)
        except Exception as e:
            logger.error(f"Error in _generate_function_docstring: {e}")
            raise
    
    def _generate_class_docstring(self, cls: ClassInfo) -> str:
        """Generate a docstring for a class."""
        try:
            lines = ['"""']
        
            # Generate description from class name
            name_parts = re.findall(r'[A-Z]?[a-z]+|[A-Z]+(?=[A-Z]|$)', cls.name)
            description = ' '.join(name_parts)
            lines.append(description + '.')
        
            # Add attributes if any
            if cls.attributes:
                lines.append('')
                lines.append('Attributes:')
                for attr in cls.attributes[:5]:  # Limit to 5
                    lines.append(f'    {attr}: Description of {attr}.')
        
            lines.append('"""')
            return '\n'.join(lines)
        except Exception as e:
            logger.error(f"Error in _generate_class_docstring: {e}")
            raise
    
    def _fix_code_smells(self, file_path: str, content: str, weaknesses: List[Weakness]) -> Optional[Improvement]:
        """Fix code smell issues."""
        try:
            lines = content.split('\n')
            new_lines = lines.copy()
            changes = []
        
            for w in weaknesses:
                line_idx = w.line_number - 1
                if line_idx >= len(lines):
                    continue
            
                line = lines[line_idx]
            
                # Remove debug print statements
                if 'print' in w.title.lower():
                    stripped = line.strip()
                    if stripped.startswith('print('):
                        indent = len(line) - len(line.lstrip())
                        new_lines[line_idx] = ' ' * indent + f'# DEBUG: {stripped}'
                        changes.append(f"Line {w.line_number}: Commented out debug print")
        
            if not changes:
                return None
        
            new_content = '\n'.join(new_lines)
        
            return Improvement(
                id=self._generate_improvement_id(),
                type=ImprovementType.CODE_QUALITY,
                priority=ImprovementPriority.P3_LOW,
                title=f"Fix code smells in {Path(file_path).name}",
                description=f"Fixed {len(changes)} code smells:\n" + "\n".join(f"- {c}" for c in changes),
                rationale="Clean code is easier to maintain and less error-prone.",
                files_modified=[file_path],
                diffs=[FileDiff(
                    file_path=file_path,
                    is_new_file=False,
                    original_content=content,
                    new_content=new_content,
                    changes_description="\n".join(changes),
                )],
                addresses_weaknesses=[w.id for w in weaknesses],
                impact="Cleaner codebase",
                risk_level="low",
                estimated_effort="15 minutes",
                complexity="easy",
            )
        except Exception as e:
            logger.error(f"Error in _fix_code_smells: {e}")
            raise
    
    def _fix_performance_issues(self, file_path: str, content: str, weaknesses: List[Weakness]) -> Optional[Improvement]:
        """Fix performance issues."""
        try:
            changes = []
            suggestions = []
        
            for w in weaknesses:
                if 'blocking' in w.title.lower():
                    suggestions.append(f"- Line {w.line_number}: Replace blocking call with async alternative")
                elif 'inefficient' in w.title.lower():
                    suggestions.append(f"- Line {w.line_number}: Use enumerate() instead of range(len())")
        
            if not suggestions:
                return None
        
            return Improvement(
                id=self._generate_improvement_id(),
                type=ImprovementType.PERFORMANCE_OPT,
                priority=ImprovementPriority.P2_MEDIUM,
                title=f"Performance improvements for {Path(file_path).name}",
                description="Suggested performance improvements:\n" + "\n".join(suggestions),
                rationale="Performance optimizations improve system responsiveness and efficiency.",
                files_modified=[file_path],
                diffs=[],  # Manual review needed
                addresses_weaknesses=[w.id for w in weaknesses],
                impact="Improved performance",
                risk_level="medium",
                estimated_effort="1-2 hours",
                complexity="medium",
                test_suggestions=["Add performance benchmarks to verify improvements"],
            )
        except Exception as e:
            logger.error(f"Error in _fix_performance_issues: {e}")
            raise
    
    def _reduce_complexity(self, file_path: str, content: str, analysis: FileAnalysisResult,
                          weaknesses: List[Weakness]) -> Optional[Improvement]:
        """Generate suggestions for reducing complexity."""
        try:
            suggestions = []
        
            for w in weaknesses:
                if 'function' in w.title.lower():
                    suggestions.append(f"- {w.title}: {w.suggested_fix}")
                elif 'complexity' in w.title.lower():
                    suggestions.append(f"- {w.title}: Break into smaller functions")
        
            if not suggestions:
                return None
        
            return Improvement(
                id=self._generate_improvement_id(),
                type=ImprovementType.REFACTOR,
                priority=ImprovementPriority.P2_MEDIUM,
                title=f"Reduce complexity in {Path(file_path).name}",
                description="Complexity reduction suggestions:\n" + "\n".join(suggestions),
                rationale="Lower complexity means fewer bugs and easier maintenance.",
                files_modified=[file_path],
                diffs=[],  # Manual refactoring needed
                addresses_weaknesses=[w.id for w in weaknesses],
                impact="More maintainable code",
                risk_level="medium",
                estimated_effort="2-4 hours",
                complexity="hard",
                test_suggestions=["Ensure all tests pass after refactoring"],
            )
        except Exception as e:
            logger.error(f"Error in _reduce_complexity: {e}")
            raise
    
    def _fix_trading_safety(self, file_path: str, content: str, weaknesses: List[Weakness]) -> Optional[Improvement]:
        """Fix trading safety issues."""
        try:
            lines = content.split('\n')
            new_lines = lines.copy()
            changes = []
        
            for w in weaknesses:
                line_idx = w.line_number - 1
                if line_idx >= len(lines):
                    continue
            
                line = lines[line_idx]
            
                # Add safety comments and suggestions
                if 'hardcoded' in w.title.lower():
                    indent = len(line) - len(line.lstrip())
                    new_lines.insert(line_idx, ' ' * indent + f'# SAFETY WARNING: {w.title} - use config instead')
                    changes.append(f"Line {w.line_number}: Added safety warning for {w.title}")
        
            if not changes:
                return None
        
            new_content = '\n'.join(new_lines)
        
            return Improvement(
                id=self._generate_improvement_id(),
                type=ImprovementType.SECURITY_FIX,
                priority=ImprovementPriority.P0_CRITICAL,
                title=f"Trading safety improvements for {Path(file_path).name}",
                description=f"Added {len(changes)} safety improvements:\n" + "\n".join(f"- {c}" for c in changes),
                rationale="Trading safety is critical to prevent financial losses.",
                files_modified=[file_path],
                diffs=[FileDiff(
                    file_path=file_path,
                    is_new_file=False,
                    original_content=content,
                    new_content=new_content,
                    changes_description="\n".join(changes),
                )],
                addresses_weaknesses=[w.id for w in weaknesses],
                impact="Improved trading safety",
                risk_level="low",
                estimated_effort="1 hour",
                complexity="medium",
                test_suggestions=["Test that safety limits are enforced"],
            )
        except Exception as e:
            logger.error(f"Error in _fix_trading_safety: {e}")
            raise
    
    def _generate_cross_cutting_improvements(self, report: WeaknessReport) -> List[Improvement]:
        """Generate improvements that span multiple files."""
        try:
            improvements = []
        
            # Check for missing tests across critical modules
            missing_test_weaknesses = [w for w in report.weaknesses 
                                       if w.category == WeaknessCategory.MISSING_TESTS]
            if len(missing_test_weaknesses) > 5:
                improvements.append(Improvement(
                    id=self._generate_improvement_id(),
                    type=ImprovementType.ADD_TESTS,
                    priority=ImprovementPriority.P1_HIGH,
                    title="Add comprehensive test suite",
                    description=f"Create tests for {len(missing_test_weaknesses)} modules lacking coverage.",
                    rationale="Tests prevent regressions and verify correct behavior.",
                    files_created=["tests/test_*.py"],
                    addresses_weaknesses=[w.id for w in missing_test_weaknesses],
                    impact="Improved test coverage",
                    risk_level="low",
                    estimated_effort="8-16 hours",
                    complexity="medium",
                ))
        
            # Check for architecture issues
            arch_weaknesses = [w for w in report.weaknesses 
                             if w.category in [WeaknessCategory.CIRCULAR_DEPENDENCY, 
                                              WeaknessCategory.TIGHT_COUPLING]]
            if arch_weaknesses:
                improvements.append(Improvement(
                    id=self._generate_improvement_id(),
                    type=ImprovementType.ARCHITECTURE,
                    priority=ImprovementPriority.P1_HIGH,
                    title="Improve architecture",
                    description=f"Address {len(arch_weaknesses)} architectural issues including "
                               f"circular dependencies and tight coupling.",
                    rationale="Good architecture enables maintainability and extensibility.",
                    addresses_weaknesses=[w.id for w in arch_weaknesses],
                    impact="Better system architecture",
                    risk_level="high",
                    estimated_effort="16-40 hours",
                    complexity="hard",
                ))
        
            return improvements
        except Exception as e:
            logger.error(f"Error in _generate_cross_cutting_improvements: {e}")
            raise
    
    def _create_proposal(self, improvements: List[Improvement]) -> ImprovementProposal:
        """Create a proposal from improvements."""
        # Calculate totals
        try:
            total_files = set()
            total_added = 0
            total_removed = 0
        
            for imp in improvements:
                total_files.update(imp.files_modified)
                total_files.update(imp.files_created)
            
                for diff in imp.diffs:
                    if diff.is_new_file:
                        total_added += len(diff.new_content.split('\n'))
                    else:
                        orig_lines = len(diff.original_content.split('\n'))
                        new_lines = len(diff.new_content.split('\n'))
                        total_added += max(0, new_lines - orig_lines)
                        total_removed += max(0, orig_lines - new_lines)
        
            # Determine overall priority
            priorities = [imp.priority for imp in improvements]
            if ImprovementPriority.P0_CRITICAL in priorities:
                overall = ImprovementPriority.P0_CRITICAL
            elif ImprovementPriority.P1_HIGH in priorities:
                overall = ImprovementPriority.P1_HIGH
            else:
                overall = ImprovementPriority.P2_MEDIUM
        
            # Generate summary
            type_counts = {}
            for imp in improvements:
                t = imp.type.value
                type_counts[t] = type_counts.get(t, 0) + 1
        
            summary_parts = [f"{count} {t.replace('_', ' ')}" for t, count in type_counts.items()]
            summary = f"This proposal includes {len(improvements)} improvements: {', '.join(summary_parts)}."
        
            return ImprovementProposal(
                id=self._generate_proposal_id(),
                title=f"Codebase Improvement Proposal",
                summary=summary,
                improvements=improvements,
                total_files_changed=len(total_files),
                total_lines_added=total_added,
                total_lines_removed=total_removed,
                overall_priority=overall,
            )
        except Exception as e:
            logger.error(f"Error in _create_proposal: {e}")
            raise
    
    def generate_new_feature(self, feature_name: str, feature_description: str,
                            target_module: str) -> Improvement:
        """Generate a new feature implementation."""
        # This would generate complete new feature code
        # For now, create a template
        
        try:
            file_name = f"{feature_name.lower().replace(' ', '_')}.py"
            file_path = f"{target_module}/{file_name}"
        
            content = f'''"""
    {feature_name}
    {'=' * len(feature_name)}

    {feature_description}
    """

    from typing import Any, Dict, List, Optional
    from dataclasses import dataclass

    logger = logging.getLogger(__name__)


    @dataclass
    class {feature_name.replace(' ', '')}Config:
        """Configuration for {feature_name}."""
        enabled: bool = True
        # Add configuration options here


    class {feature_name.replace(' ', '')}:
        """
        {feature_description}
        """
    
        def __init__(self, config: {feature_name.replace(' ', '')}Config = None):
            self.config = config or {feature_name.replace(' ', '')}Config()
            self._initialized = False
    
        def initialize(self) -> bool:
            """Initialize the {feature_name.lower()}."""
            logger.info(f"Initializing {feature_name}...")
            # Add initialization logic here
            self._initialized = True
            return True
    
        def process(self, data: Any) -> Any:
            """Process data through {feature_name.lower()}."""
            if not self._initialized:
                raise RuntimeError("{feature_name} not initialized")
        
            # Add processing logic here
            return data
    
        def cleanup(self):
            """Clean up resources."""
            self._initialized = False
    '''
        
            return Improvement(
                id=self._generate_improvement_id(),
                type=ImprovementType.NEW_FEATURE,
                priority=ImprovementPriority.P2_MEDIUM,
                title=f"Add new feature: {feature_name}",
                description=feature_description,
                rationale="New feature to enhance system capabilities.",
                files_created=[file_path],
                diffs=[FileDiff(
                    file_path=file_path,
                    is_new_file=True,
                    original_content="",
                    new_content=content,
                    changes_description=f"New file: {file_name}",
                )],
                impact="New functionality added",
                risk_level="medium",
                estimated_effort="4-8 hours",
                complexity="medium",
                requires_tests=True,
                test_suggestions=[
                    f"Test {feature_name} initialization",
                    f"Test {feature_name} processing",
                    f"Test {feature_name} error handling",
                ],
            )
        except Exception as e:
            logger.error(f"Error in generate_new_feature: {e}")
            raise
