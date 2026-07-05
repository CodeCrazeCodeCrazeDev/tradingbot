"""
Agent Orchestrator
==================

The main orchestrator that coordinates all improvement agent components.
This is the "brain" that drives the autonomous improvement process.

Workflow:
1. Analyze codebase (DeepCodebaseAnalyzer)
2. Detect weaknesses (WeaknessDetector)
3. Generate improvements (ImprovementProposer)
4. Generate tests (TestGenerator)
5. Create change requests (ChangeManager)
6. Present for review (AgentInterface)
7. Apply approved changes
8. Learn from feedback
"""

import os
import json
import asyncio
from pathlib import Path
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional, Set, Tuple
from enum import Enum
from datetime import datetime
import logging
import threading

from .deep_analyzer import (
    DeepCodebaseAnalyzer,
    CodebaseSnapshot,
    AnalysisDepth,
)
from .weakness_detector import (
    WeaknessDetector,
    WeaknessReport,
    Weakness,
    WeaknessCategory,
    WeaknessSeverity,
)
from .improvement_proposer import (
    ImprovementProposer,
    ImprovementProposal,
    Improvement,
    ImprovementType,
    ImprovementPriority,
)
from .test_generator import (
    TestGenerator,
    TestSuite,
)
from .change_manager import (
    ChangeManager,
    ChangeRequest,
    ChangeStatus,
    ChangeHistory,
)

logger = logging.getLogger(__name__)


class AgentMode(Enum):
    """Operating modes for the agent."""
    OBSERVE = "observe"           # Only analyze, don't propose
    PROPOSE = "propose"           # Analyze and propose improvements
    SUPERVISED = "supervised"     # Apply only approved changes
    AUTONOMOUS = "autonomous"     # Full autonomy (non-protected files only)


class AgentState(Enum):
    """Current state of the agent."""
    IDLE = "idle"
    ANALYZING = "analyzing"
    DETECTING = "detecting"
    PROPOSING = "proposing"
    TESTING = "testing"
    AWAITING_REVIEW = "awaiting_review"
    APPLYING = "applying"
    COMPLETED = "completed"
    ERROR = "error"


@dataclass
class AgentDirective:
    """A directive from the human to guide the agent."""
    id: str
    directive_type: str  # focus, skip, priority, stop
    target: str          # file, module, category
    description: str
    created_at: datetime = field(default_factory=datetime.now)
    
    @staticmethod
    def focus_on(target: str, description: str = "") -> 'AgentDirective':
        return AgentDirective(
            id=f"DIR_{datetime.now().strftime('%H%M%S')}",
            directive_type="focus",
            target=target,
            description=description or f"Focus on {target}",
        )
    
    @staticmethod
    def skip(target: str, reason: str = "") -> 'AgentDirective':
        return AgentDirective(
            id=f"DIR_{datetime.now().strftime('%H%M%S')}",
            directive_type="skip",
            target=target,
            description=reason or f"Skip {target}",
        )


@dataclass
class AgentConfig:
    """Configuration for the improvement agent."""
    mode: AgentMode = AgentMode.SUPERVISED
    analysis_depth: AnalysisDepth = AnalysisDepth.DEEP
    
    # Limits
    max_improvements_per_run: int = 50
    max_files_per_improvement: int = 10
    
    # Focus areas
    focus_modules: List[str] = field(default_factory=list)
    skip_modules: List[str] = field(default_factory=list)
    
    # Priority filters
    min_severity: WeaknessSeverity = WeaknessSeverity.LOW
    priority_categories: List[WeaknessCategory] = field(default_factory=list)
    
    # Safety
    require_tests: bool = True
    backup_before_apply: bool = True
    
    # Persistence
    state_file: str = "agent_state.json"
    
    def to_dict(self) -> Dict:
        return {
            "mode": self.mode.value,
            "analysis_depth": self.analysis_depth.value,
            "max_improvements_per_run": self.max_improvements_per_run,
            "focus_modules": self.focus_modules,
            "skip_modules": self.skip_modules,
        }


@dataclass
class AgentRun:
    """Record of a single agent run."""
    id: str
    started_at: datetime
    completed_at: Optional[datetime] = None
    
    # Results
    files_analyzed: int = 0
    weaknesses_found: int = 0
    improvements_proposed: int = 0
    tests_generated: int = 0
    changes_applied: int = 0
    
    # Status
    state: AgentState = AgentState.IDLE
    error_message: str = ""
    
    def to_dict(self) -> Dict:
        return {
            "id": self.id,
            "started_at": self.started_at.isoformat(),
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "state": self.state.value,
            "files_analyzed": self.files_analyzed,
            "weaknesses_found": self.weaknesses_found,
            "improvements_proposed": self.improvements_proposed,
            "tests_generated": self.tests_generated,
            "changes_applied": self.changes_applied,
        }


class ImprovementAgent:
    """
    The Autonomous Improvement Agent.
    
    This agent systematically analyzes the codebase, identifies weaknesses,
    proposes improvements, generates tests, and applies approved changes.
    
    It can be observed and directed by a human at any time.
    """
    
    def __init__(self, root_path: str, config: AgentConfig = None):
        self.root_path = Path(root_path)
        self.config = config or AgentConfig()
        
        # State
        self.state = AgentState.IDLE
        self.current_run: Optional[AgentRun] = None
        self.run_history: List[AgentRun] = []
        self.directives: List[AgentDirective] = []
        
        # Components (initialized lazily)
        self._analyzer: Optional[DeepCodebaseAnalyzer] = None
        self._detector: Optional[WeaknessDetector] = None
        self._proposer: Optional[ImprovementProposer] = None
        self._test_gen: Optional[TestGenerator] = None
        self._change_mgr: Optional[ChangeManager] = None
        
        # Results
        self.snapshot: Optional[CodebaseSnapshot] = None
        self.weakness_report: Optional[WeaknessReport] = None
        self.current_proposal: Optional[ImprovementProposal] = None
        self.test_suites: List[TestSuite] = []
        
        # Callbacks
        self._on_state_change: Optional[Callable] = None
        self._on_weakness_found: Optional[Callable] = None
        self._on_improvement_ready: Optional[Callable] = None
        
        # Control
        self._stop_requested = False
        self._pause_requested = False
        
        logger.info(f"Improvement Agent initialized for {root_path}")
    
    # =========================================================================
    # Properties
    # =========================================================================
    
    @property
    def analyzer(self) -> DeepCodebaseAnalyzer:
        if not self._analyzer:
            self._analyzer = DeepCodebaseAnalyzer(
                str(self.root_path),
                self.config.analysis_depth
            )
        return self._analyzer
    
    @property
    def detector(self) -> WeaknessDetector:
        if not self._detector:
            if not self._analyzer or not self._analyzer.snapshot:
                raise RuntimeError("Analyzer must run first")
            self._detector = WeaknessDetector(self._analyzer)
        return self._detector
    
    @property
    def proposer(self) -> ImprovementProposer:
        if not self._proposer:
            if not self._analyzer:
                raise RuntimeError("Analyzer must run first")
            self._proposer = ImprovementProposer(self._analyzer)
        return self._proposer
    
    @property
    def test_generator(self) -> TestGenerator:
        if not self._test_gen:
            if not self._analyzer:
                raise RuntimeError("Analyzer must run first")
            self._test_gen = TestGenerator(self._analyzer)
        return self._test_gen
    
    @property
    def change_manager(self) -> ChangeManager:
        if not self._change_mgr:
            self._change_mgr = ChangeManager(str(self.root_path))
        return self._change_mgr
    
    # =========================================================================
    # Main Workflow
    # =========================================================================
    
    def run_full_cycle(self) -> AgentRun:
        """Run a complete improvement cycle."""
        self._start_run()
        
        try:
            # Phase 1: Analyze
            self._set_state(AgentState.ANALYZING)
            self.analyze_codebase()
            
            if self._check_stop():
                return self._complete_run()
            
            # Phase 2: Detect
            self._set_state(AgentState.DETECTING)
            self.detect_weaknesses()
            
            if self._check_stop():
                return self._complete_run()
            
            # Phase 3: Propose
            if self.config.mode != AgentMode.OBSERVE:
                self._set_state(AgentState.PROPOSING)
                self.generate_improvements()
                
                if self._check_stop():
                    return self._complete_run()
                
                # Phase 4: Generate Tests
                if self.config.require_tests:
                    self._set_state(AgentState.TESTING)
                    self.generate_tests()
                
                # Phase 5: Await Review
                self._set_state(AgentState.AWAITING_REVIEW)
                
                # In autonomous mode, auto-approve non-protected changes
                if self.config.mode == AgentMode.AUTONOMOUS:
                    self._auto_approve_safe_changes()
                    self._set_state(AgentState.APPLYING)
                    self.apply_approved_changes()
            
            return self._complete_run()
            
        except Exception as e:
            logger.error(f"Agent run failed: {e}")
            self.state = AgentState.ERROR
            if self.current_run:
                self.current_run.state = AgentState.ERROR
                self.current_run.error_message = str(e)
            raise
    
    def analyze_codebase(self) -> CodebaseSnapshot:
        """Analyze the entire codebase."""
        logger.info("Starting codebase analysis...")
        
        self.snapshot = self.analyzer.analyze()
        
        if self.current_run:
            self.current_run.files_analyzed = self.snapshot.total_files
        
        logger.info(f"Analysis complete: {self.snapshot.total_files} files, "
                   f"{self.snapshot.total_lines} lines")
        
        return self.snapshot
    
    def detect_weaknesses(self) -> WeaknessReport:
        """Detect all weaknesses in the codebase."""
        logger.info("Detecting weaknesses...")
        
        self.weakness_report = self.detector.detect_all()
        
        # Apply directives to filter weaknesses
        self._apply_directives_to_weaknesses()
        
        if self.current_run:
            self.current_run.weaknesses_found = len(self.weakness_report.weaknesses)
        
        # Notify callback
        if self._on_weakness_found:
            for w in self.weakness_report.weaknesses[:10]:  # Top 10
                self._on_weakness_found(w)
        
        logger.info(f"Found {len(self.weakness_report.weaknesses)} weaknesses")
        
        return self.weakness_report
    
    def generate_improvements(self) -> ImprovementProposal:
        """Generate improvements for detected weaknesses."""
        logger.info("Generating improvements...")
        
        if not self.weakness_report:
            raise RuntimeError("Must detect weaknesses first")
        
        self.current_proposal = self.proposer.generate_improvements(self.weakness_report)
        
        # Limit improvements
        if len(self.current_proposal.improvements) > self.config.max_improvements_per_run:
            self.current_proposal.improvements = self.current_proposal.improvements[:self.config.max_improvements_per_run]
        
        if self.current_run:
            self.current_run.improvements_proposed = len(self.current_proposal.improvements)
        
        # Create change requests
        self.change_manager.create_change_requests(self.current_proposal)
        
        # Notify callback
        if self._on_improvement_ready:
            self._on_improvement_ready(self.current_proposal)
        
        logger.info(f"Generated {len(self.current_proposal.improvements)} improvements")
        
        return self.current_proposal
    
    def generate_tests(self) -> List[TestSuite]:
        """Generate tests for all improvements."""
        logger.info("Generating tests...")
        
        if not self.current_proposal:
            raise RuntimeError("Must generate improvements first")
        
        self.test_suites = []
        
        for improvement in self.current_proposal.improvements:
            suite = self.test_generator.generate_tests_for_improvement(improvement)
            self.test_suites.append(suite)
        
        total_tests = sum(len(s.tests) for s in self.test_suites)
        
        if self.current_run:
            self.current_run.tests_generated = total_tests
        
        logger.info(f"Generated {total_tests} tests in {len(self.test_suites)} suites")
        
        return self.test_suites
    
    def apply_approved_changes(self) -> Tuple[int, int]:
        """Apply all approved changes."""
        logger.info("Applying approved changes...")
        
        applied, failed, errors = self.change_manager.apply_all_approved()
        
        if self.current_run:
            self.current_run.changes_applied = applied
        
        if errors:
            for error in errors:
                logger.warning(f"Change failed: {error}")
        
        logger.info(f"Applied {applied} changes, {failed} failed")
        
        return applied, failed
    
    # =========================================================================
    # Directives
    # =========================================================================
    
    def add_directive(self, directive: AgentDirective):
        """Add a directive to guide the agent."""
        self.directives.append(directive)
        logger.info(f"Added directive: {directive.directive_type} - {directive.target}")
    
    def focus_on(self, target: str, description: str = ""):
        """Direct the agent to focus on a specific area."""
        self.add_directive(AgentDirective.focus_on(target, description))
    
    def skip(self, target: str, reason: str = ""):
        """Direct the agent to skip a specific area."""
        self.add_directive(AgentDirective.skip(target, reason))
    
    def clear_directives(self):
        """Clear all directives."""
        self.directives = []
    
    def _apply_directives_to_weaknesses(self):
        """Apply directives to filter weaknesses."""
        if not self.weakness_report:
            return
        
        filtered = []
        
        for w in self.weakness_report.weaknesses:
            should_include = True
            
            for directive in self.directives:
                if directive.directive_type == "skip":
                    if directive.target in w.file_path or directive.target in w.category.value:
                        should_include = False
                        break
                
                elif directive.directive_type == "focus":
                    if directive.target not in w.file_path and directive.target not in w.category.value:
                        should_include = False
                        break
            
            if should_include:
                filtered.append(w)
        
        self.weakness_report.weaknesses = filtered
        self.weakness_report.total_weaknesses = len(filtered)
    
    # =========================================================================
    # Control
    # =========================================================================
    
    def stop(self):
        """Request the agent to stop."""
        self._stop_requested = True
        logger.info("Stop requested")
    
    def pause(self):
        """Request the agent to pause."""
        self._pause_requested = True
        logger.info("Pause requested")
    
    def resume(self):
        """Resume a paused agent."""
        self._pause_requested = False
        logger.info("Resumed")
    
    def _check_stop(self) -> bool:
        """Check if stop was requested."""
        if self._stop_requested:
            logger.info("Stopping as requested")
            return True
        
        while self._pause_requested:
            import time
            time.sleep(0.5)
        
        return False
    
    # =========================================================================
    # State Management
    # =========================================================================
    
    def _start_run(self):
        """Start a new run."""
        run_id = f"RUN_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        self.current_run = AgentRun(
            id=run_id,
            started_at=datetime.now(),
            state=AgentState.IDLE,
        )
        self._stop_requested = False
        self._pause_requested = False
        logger.info(f"Started run {run_id}")
    
    def _complete_run(self) -> AgentRun:
        """Complete the current run."""
        if self.current_run:
            self.current_run.completed_at = datetime.now()
            self.current_run.state = self.state
            self.run_history.append(self.current_run)
            logger.info(f"Completed run {self.current_run.id}")
        
        self._set_state(AgentState.COMPLETED)
        return self.current_run
    
    def _set_state(self, state: AgentState):
        """Set the agent state."""
        old_state = self.state
        self.state = state
        
        if self.current_run:
            self.current_run.state = state
        
        if self._on_state_change:
            self._on_state_change(old_state, state)
        
        logger.debug(f"State: {old_state.value} -> {state.value}")
    
    def _auto_approve_safe_changes(self):
        """Auto-approve changes to non-protected files."""
        pending = self.change_manager.history.get_pending()
        
        for change in pending:
            if not self.change_manager.is_protected_path(change.file_path):
                self.change_manager.approve_change(change.id, "autonomous_agent")
    
    # =========================================================================
    # Callbacks
    # =========================================================================
    
    def on_state_change(self, callback: Callable):
        """Register callback for state changes."""
        self._on_state_change = callback
    
    def on_weakness_found(self, callback: Callable):
        """Register callback for weakness detection."""
        self._on_weakness_found = callback
    
    def on_improvement_ready(self, callback: Callable):
        """Register callback for improvement proposals."""
        self._on_improvement_ready = callback
    
    # =========================================================================
    # Reporting
    # =========================================================================
    
    def get_status(self) -> Dict:
        """Get current agent status."""
        return {
            "state": self.state.value,
            "mode": self.config.mode.value,
            "current_run": self.current_run.to_dict() if self.current_run else None,
            "total_runs": len(self.run_history),
            "directives": len(self.directives),
            "pending_changes": len(self.change_manager.history.get_pending()) if self._change_mgr else 0,
        }
    
    def get_summary_report(self) -> str:
        """Generate a summary report of the agent's findings."""
        lines = [
            "=" * 60,
            "IMPROVEMENT AGENT REPORT",
            "=" * 60,
            "",
            f"**Status:** {self.state.value}",
            f"**Mode:** {self.config.mode.value}",
            "",
        ]
        
        if self.snapshot:
            lines.extend([
                "## Codebase Analysis",
                f"- Total Files: {self.snapshot.total_files}",
                f"- Total Lines: {self.snapshot.total_lines}",
                f"- Total Modules: {self.snapshot.total_modules}",
                f"- Overall Quality: {self.snapshot.overall_quality:.1f}/100",
                "",
            ])
        
        if self.weakness_report:
            lines.extend([
                "## Weaknesses Detected",
                f"- Total: {self.weakness_report.total_weaknesses}",
                f"- Critical: {self.weakness_report.critical_count}",
                f"- High: {self.weakness_report.high_count}",
                f"- Medium: {self.weakness_report.medium_count}",
                f"- Low: {self.weakness_report.low_count}",
                "",
                "### Top Categories:",
            ])
            for cat, count in list(self.weakness_report.by_category.items())[:5]:
                lines.append(f"  - {cat}: {count}")
            lines.append("")
        
        if self.current_proposal:
            lines.extend([
                "## Improvements Proposed",
                f"- Total: {len(self.current_proposal.improvements)}",
                f"- Files Changed: {self.current_proposal.total_files_changed}",
                f"- Lines Added: {self.current_proposal.total_lines_added}",
                f"- Lines Removed: {self.current_proposal.total_lines_removed}",
                "",
            ])
        
        if self._change_mgr:
            status = self.change_manager.get_status_summary()
            lines.extend([
                "## Change Status",
                f"- Pending Review: {status['pending']}",
                f"- Approved: {status['approved']}",
                f"- Applied: {status['applied']}",
                f"- Rejected: {status['rejected']}",
                "",
            ])
        
        lines.append("=" * 60)
        
        return "\n".join(lines)
    
    def save_state(self, file_path: str = None):
        """Save agent state to file."""
        if not file_path:
            file_path = self.root_path / self.config.state_file
        
        state = {
            "saved_at": datetime.now().isoformat(),
            "config": self.config.to_dict(),
            "state": self.state.value,
            "run_history": [r.to_dict() for r in self.run_history],
            "directives": [
                {
                    "id": d.id,
                    "type": d.directive_type,
                    "target": d.target,
                    "description": d.description,
                }
                for d in self.directives
            ],
        }
        
        Path(file_path).write_text(json.dumps(state, indent=2), encoding='utf-8')
        logger.info(f"Saved agent state to {file_path}")
    
    def load_state(self, file_path: str = None):
        """Load agent state from file."""
        if not file_path:
            file_path = self.root_path / self.config.state_file
        
        path = Path(file_path)
        if not path.exists():
            logger.warning(f"State file not found: {file_path}")
            return
        
        state = json.loads(path.read_text(encoding='utf-8'))
        
        # Restore directives
        for d in state.get("directives", []):
            self.directives.append(AgentDirective(
                id=d["id"],
                directive_type=d["type"],
                target=d["target"],
                description=d["description"],
            ))
        
        logger.info(f"Loaded agent state from {file_path}")


def create_agent(root_path: str, mode: str = "supervised") -> ImprovementAgent:
    """Factory function to create an improvement agent."""
    config = AgentConfig(
        mode=AgentMode(mode),
        analysis_depth=AnalysisDepth.DEEP,
    )
    return ImprovementAgent(root_path, config)
