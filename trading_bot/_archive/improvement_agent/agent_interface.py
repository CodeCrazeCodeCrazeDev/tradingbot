"""
Agent Interface
================

Provides the interface for humans to observe and direct the improvement agent.
This is how you interact with and control the agent.

Capabilities:
- View agent status and progress
- Review proposed changes
- Approve or reject changes
- Direct the agent's focus
- View reports and summaries
"""

import os
import json
from pathlib import Path
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Callable
from enum import Enum
from datetime import datetime
import logging

from .agent_orchestrator import (
    ImprovementAgent,
    AgentConfig,
    AgentMode,
    AgentState,
    AgentDirective,
)
from .weakness_detector import Weakness, WeaknessSeverity
from .improvement_proposer import Improvement, ImprovementProposal
from .change_manager import ChangeRequest, ChangeStatus

logger = logging.getLogger(__name__)


class AgentCommand(Enum):
    """Commands that can be sent to the agent."""
    START = "start"
    STOP = "stop"
    PAUSE = "pause"
    RESUME = "resume"
    ANALYZE = "analyze"
    DETECT = "detect"
    PROPOSE = "propose"
    APPROVE = "approve"
    REJECT = "reject"
    APPLY = "apply"
    ROLLBACK = "rollback"
    FOCUS = "focus"
    SKIP = "skip"
    STATUS = "status"
    REPORT = "report"
    HELP = "help"


@dataclass
class AgentResponse:
    """Response from the agent to a command."""
    success: bool
    message: str
    data: Optional[Dict] = None
    
    def to_dict(self) -> Dict:
        return {
            "success": self.success,
            "message": self.message,
            "data": self.data,
        }


@dataclass
class ObservationReport:
    """A report for human observation."""
    timestamp: datetime
    agent_state: str
    summary: str
    
    # Key metrics
    files_analyzed: int = 0
    weaknesses_found: int = 0
    improvements_proposed: int = 0
    pending_review: int = 0
    
    # Top items
    top_weaknesses: List[Dict] = field(default_factory=list)
    top_improvements: List[Dict] = field(default_factory=list)
    pending_changes: List[Dict] = field(default_factory=list)
    
    def to_markdown(self) -> str:
        """Generate markdown report."""
        lines = [
            f"# Agent Observation Report",
            f"*Generated: {self.timestamp.strftime('%Y-%m-%d %H:%M:%S')}*",
            "",
            f"## Status: {self.agent_state.upper()}",
            "",
            "## Metrics",
            f"| Metric | Value |",
            f"|--------|-------|",
            f"| Files Analyzed | {self.files_analyzed} |",
            f"| Weaknesses Found | {self.weaknesses_found} |",
            f"| Improvements Proposed | {self.improvements_proposed} |",
            f"| Pending Review | {self.pending_review} |",
            "",
        ]
        
        if self.top_weaknesses:
            lines.extend([
                "## Top Weaknesses",
                "",
            ])
            for i, w in enumerate(self.top_weaknesses[:10], 1):
                lines.append(f"{i}. **[{w.get('severity', 'UNKNOWN')}]** {w.get('title', 'Unknown')}")
                lines.append(f"   - File: `{w.get('file', 'unknown')}`")
                lines.append(f"   - {w.get('description', '')[:100]}...")
                lines.append("")
        
        if self.top_improvements:
            lines.extend([
                "## Top Improvements",
                "",
            ])
            for i, imp in enumerate(self.top_improvements[:10], 1):
                lines.append(f"{i}. **{imp.get('title', 'Unknown')}**")
                lines.append(f"   - Type: {imp.get('type', 'unknown')}")
                lines.append(f"   - Priority: {imp.get('priority', 'unknown')}")
                lines.append("")
        
        if self.pending_changes:
            lines.extend([
                "## Pending Changes (Awaiting Your Review)",
                "",
            ])
            for c in self.pending_changes[:20]:
                protected = "🔒 " if c.get('protected') else ""
                lines.append(f"- {protected}**{c.get('id')}**: {c.get('file')}")
                lines.append(f"  - {c.get('description', '')[:80]}")
                lines.append("")
        
        return "\n".join(lines)


class AgentInterface:
    """
    The interface for observing and directing the improvement agent.
    
    This is your control panel for the agent. Use it to:
    - Monitor what the agent is doing
    - Review and approve changes
    - Direct the agent's focus
    - Get reports and summaries
    """
    
    def __init__(self, agent: ImprovementAgent):
        self.agent = agent
        self._command_history: List[Dict] = []
    
    # =========================================================================
    # Command Execution
    # =========================================================================
    
    def execute_command(self, command: str, args: Dict = None) -> AgentResponse:
        """Execute a command on the agent."""
        args = args or {}
        
        # Log command
        self._command_history.append({
            "command": command,
            "args": args,
            "timestamp": datetime.now().isoformat(),
        })
        
        try:
            cmd = AgentCommand(command.lower())
        except ValueError:
            return AgentResponse(
                success=False,
                message=f"Unknown command: {command}. Use 'help' for available commands.",
            )
        
        # Execute command
        handlers = {
            AgentCommand.START: self._cmd_start,
            AgentCommand.STOP: self._cmd_stop,
            AgentCommand.PAUSE: self._cmd_pause,
            AgentCommand.RESUME: self._cmd_resume,
            AgentCommand.ANALYZE: self._cmd_analyze,
            AgentCommand.DETECT: self._cmd_detect,
            AgentCommand.PROPOSE: self._cmd_propose,
            AgentCommand.APPROVE: self._cmd_approve,
            AgentCommand.REJECT: self._cmd_reject,
            AgentCommand.APPLY: self._cmd_apply,
            AgentCommand.ROLLBACK: self._cmd_rollback,
            AgentCommand.FOCUS: self._cmd_focus,
            AgentCommand.SKIP: self._cmd_skip,
            AgentCommand.STATUS: self._cmd_status,
            AgentCommand.REPORT: self._cmd_report,
            AgentCommand.HELP: self._cmd_help,
        }
        
        handler = handlers.get(cmd)
        if handler:
            return handler(args)
        
        return AgentResponse(success=False, message=f"Command not implemented: {command}")
    
    def _cmd_start(self, args: Dict) -> AgentResponse:
        """Start a full improvement cycle."""
        try:
            run = self.agent.run_full_cycle()
            return AgentResponse(
                success=True,
                message=f"Completed run {run.id}",
                data=run.to_dict(),
            )
        except Exception as e:
            return AgentResponse(success=False, message=str(e))
    
    def _cmd_stop(self, args: Dict) -> AgentResponse:
        """Stop the agent."""
        self.agent.stop()
        return AgentResponse(success=True, message="Stop requested")
    
    def _cmd_pause(self, args: Dict) -> AgentResponse:
        """Pause the agent."""
        self.agent.pause()
        return AgentResponse(success=True, message="Pause requested")
    
    def _cmd_resume(self, args: Dict) -> AgentResponse:
        """Resume the agent."""
        self.agent.resume()
        return AgentResponse(success=True, message="Resumed")
    
    def _cmd_analyze(self, args: Dict) -> AgentResponse:
        """Run codebase analysis only."""
        try:
            snapshot = self.agent.analyze_codebase()
            return AgentResponse(
                success=True,
                message=f"Analyzed {snapshot.total_files} files, {snapshot.total_lines} lines",
                data=self.agent.analyzer.to_dict(),
            )
        except Exception as e:
            return AgentResponse(success=False, message=str(e))
    
    def _cmd_detect(self, args: Dict) -> AgentResponse:
        """Run weakness detection."""
        try:
            report = self.agent.detect_weaknesses()
            return AgentResponse(
                success=True,
                message=f"Found {report.total_weaknesses} weaknesses",
                data={
                    "total": report.total_weaknesses,
                    "critical": report.critical_count,
                    "high": report.high_count,
                    "medium": report.medium_count,
                    "low": report.low_count,
                },
            )
        except Exception as e:
            return AgentResponse(success=False, message=str(e))
    
    def _cmd_propose(self, args: Dict) -> AgentResponse:
        """Generate improvement proposals."""
        try:
            proposal = self.agent.generate_improvements()
            return AgentResponse(
                success=True,
                message=f"Generated {len(proposal.improvements)} improvements",
                data={
                    "id": proposal.id,
                    "improvements": len(proposal.improvements),
                    "files_changed": proposal.total_files_changed,
                },
            )
        except Exception as e:
            return AgentResponse(success=False, message=str(e))
    
    def _cmd_approve(self, args: Dict) -> AgentResponse:
        """Approve a change or all changes."""
        change_id = args.get("id")
        improvement_id = args.get("improvement_id")
        approve_all = args.get("all", False)
        reviewer = args.get("reviewer", "human")
        
        if approve_all:
            pending = self.agent.change_manager.history.get_pending()
            approved = 0
            for change in pending:
                if self.agent.change_manager.approve_change(change.id, reviewer):
                    approved += 1
            return AgentResponse(
                success=True,
                message=f"Approved {approved} changes",
            )
        
        if improvement_id:
            count = self.agent.change_manager.approve_all_for_improvement(improvement_id, reviewer)
            return AgentResponse(
                success=True,
                message=f"Approved {count} changes for improvement {improvement_id}",
            )
        
        if change_id:
            success = self.agent.change_manager.approve_change(change_id, reviewer)
            return AgentResponse(
                success=success,
                message=f"Approved change {change_id}" if success else f"Failed to approve {change_id}",
            )
        
        return AgentResponse(success=False, message="Specify id, improvement_id, or all=True")
    
    def _cmd_reject(self, args: Dict) -> AgentResponse:
        """Reject a change."""
        change_id = args.get("id")
        reason = args.get("reason", "Rejected by reviewer")
        reviewer = args.get("reviewer", "human")
        
        if not change_id:
            return AgentResponse(success=False, message="Specify change id")
        
        success = self.agent.change_manager.reject_change(change_id, reviewer, reason)
        return AgentResponse(
            success=success,
            message=f"Rejected change {change_id}" if success else f"Failed to reject {change_id}",
        )
    
    def _cmd_apply(self, args: Dict) -> AgentResponse:
        """Apply approved changes."""
        change_id = args.get("id")
        
        if change_id:
            success, message = self.agent.change_manager.apply_change(change_id)
            return AgentResponse(success=success, message=message)
        
        # Apply all approved
        applied, failed = self.agent.apply_approved_changes()
        return AgentResponse(
            success=failed == 0,
            message=f"Applied {applied} changes, {failed} failed",
        )
    
    def _cmd_rollback(self, args: Dict) -> AgentResponse:
        """Rollback a change."""
        change_id = args.get("id")
        
        if not change_id:
            return AgentResponse(success=False, message="Specify change id")
        
        success, message = self.agent.change_manager.rollback_change(change_id)
        return AgentResponse(success=success, message=message)
    
    def _cmd_focus(self, args: Dict) -> AgentResponse:
        """Direct agent to focus on something."""
        target = args.get("target")
        description = args.get("description", "")
        
        if not target:
            return AgentResponse(success=False, message="Specify target to focus on")
        
        self.agent.focus_on(target, description)
        return AgentResponse(
            success=True,
            message=f"Agent will focus on: {target}",
        )
    
    def _cmd_skip(self, args: Dict) -> AgentResponse:
        """Direct agent to skip something."""
        target = args.get("target")
        reason = args.get("reason", "")
        
        if not target:
            return AgentResponse(success=False, message="Specify target to skip")
        
        self.agent.skip(target, reason)
        return AgentResponse(
            success=True,
            message=f"Agent will skip: {target}",
        )
    
    def _cmd_status(self, args: Dict) -> AgentResponse:
        """Get agent status."""
        status = self.agent.get_status()
        return AgentResponse(
            success=True,
            message=f"Agent is {status['state']}",
            data=status,
        )
    
    def _cmd_report(self, args: Dict) -> AgentResponse:
        """Get a report."""
        report_type = args.get("type", "summary")
        
        if report_type == "summary":
            report = self.agent.get_summary_report()
            return AgentResponse(success=True, message=report)
        
        elif report_type == "observation":
            obs = self.get_observation_report()
            return AgentResponse(success=True, message=obs.to_markdown())
        
        elif report_type == "pending":
            pending = self.agent.change_manager.get_pending_review()
            return AgentResponse(
                success=True,
                message=f"{len(pending)} changes pending review",
                data={"pending": pending},
            )
        
        return AgentResponse(success=False, message=f"Unknown report type: {report_type}")
    
    def _cmd_help(self, args: Dict) -> AgentResponse:
        """Show help."""
        help_text = """
# Improvement Agent Commands

## Lifecycle
- **start** - Run a full improvement cycle
- **stop** - Stop the agent
- **pause** - Pause the agent
- **resume** - Resume the agent

## Analysis
- **analyze** - Analyze the codebase
- **detect** - Detect weaknesses
- **propose** - Generate improvements

## Review
- **approve** - Approve changes
  - `id`: specific change ID
  - `improvement_id`: all changes for an improvement
  - `all`: approve all pending
- **reject** - Reject a change
  - `id`: change ID
  - `reason`: rejection reason

## Application
- **apply** - Apply approved changes
  - `id`: specific change (optional, applies all if not specified)
- **rollback** - Rollback a change
  - `id`: change ID

## Direction
- **focus** - Focus on specific area
  - `target`: module, file, or category
- **skip** - Skip specific area
  - `target`: module, file, or category

## Reporting
- **status** - Get agent status
- **report** - Get reports
  - `type`: summary, observation, pending

## Examples
```
execute_command("start")
execute_command("focus", {"target": "risk"})
execute_command("approve", {"all": True})
execute_command("report", {"type": "pending"})
```
"""
        return AgentResponse(success=True, message=help_text)
    
    # =========================================================================
    # Observation
    # =========================================================================
    
    def get_observation_report(self) -> ObservationReport:
        """Generate an observation report for the human."""
        report = ObservationReport(
            timestamp=datetime.now(),
            agent_state=self.agent.state.value,
            summary=f"Agent is in {self.agent.state.value} state",
        )
        
        # Add metrics
        if self.agent.snapshot:
            report.files_analyzed = self.agent.snapshot.total_files
        
        if self.agent.weakness_report:
            report.weaknesses_found = self.agent.weakness_report.total_weaknesses
            
            # Top weaknesses
            for w in self.agent.weakness_report.weaknesses[:10]:
                report.top_weaknesses.append({
                    "id": w.id,
                    "severity": w.severity.value,
                    "title": w.title,
                    "file": Path(w.file_path).name,
                    "description": w.description,
                })
        
        if self.agent.current_proposal:
            report.improvements_proposed = len(self.agent.current_proposal.improvements)
            
            # Top improvements
            for imp in self.agent.current_proposal.improvements[:10]:
                report.top_improvements.append({
                    "id": imp.id,
                    "title": imp.title,
                    "type": imp.type.value,
                    "priority": imp.priority.value,
                })
        
        if self.agent._change_mgr:
            pending = self.agent.change_manager.get_pending_review()
            report.pending_review = len(pending)
            report.pending_changes = pending
        
        return report
    
    def get_pending_for_review(self) -> List[Dict]:
        """Get all changes pending human review."""
        return self.agent.change_manager.get_pending_review()
    
    def review_change(self, change_id: str) -> Dict:
        """Get detailed information about a change for review."""
        for change in self.agent.change_manager.history.changes:
            if change.id == change_id:
                return {
                    "id": change.id,
                    "file": change.file_path,
                    "type": change.change_type.value,
                    "status": change.status.value,
                    "description": change.description,
                    "protected": self.agent.change_manager.is_protected_path(change.file_path),
                    "diff": change.diff.get_unified_diff() if change.diff else "",
                    "improvement_id": change.improvement_id,
                }
        return {}
    
    # =========================================================================
    # Interactive Mode
    # =========================================================================
    
    def interactive_review(self):
        """Start an interactive review session."""
        print("\n" + "=" * 60)
        print("IMPROVEMENT AGENT - INTERACTIVE REVIEW")
        print("=" * 60)
        
        pending = self.get_pending_for_review()
        
        if not pending:
            print("\nNo changes pending review.")
            return
        
        print(f"\n{len(pending)} changes pending review.\n")
        
        for i, change in enumerate(pending, 1):
            print(f"\n--- Change {i}/{len(pending)} ---")
            print(f"ID: {change['id']}")
            print(f"File: {change['file']}")
            print(f"Type: {change['type']}")
            if change.get('protected'):
                print("⚠️  PROTECTED FILE - Extra caution required")
            print(f"\nDescription: {change['description']}")
            print(f"\nDiff Preview:\n{change.get('diff_preview', 'No preview available')}")
            
            while True:
                action = input("\n[A]pprove / [R]eject / [S]kip / [V]iew full / [Q]uit: ").strip().lower()
                
                if action == 'a':
                    self.execute_command("approve", {"id": change['id']})
                    print("✓ Approved")
                    break
                elif action == 'r':
                    reason = input("Rejection reason: ").strip()
                    self.execute_command("reject", {"id": change['id'], "reason": reason})
                    print("✗ Rejected")
                    break
                elif action == 's':
                    print("→ Skipped")
                    break
                elif action == 'v':
                    details = self.review_change(change['id'])
                    print(f"\nFull Diff:\n{details.get('diff', 'No diff available')}")
                elif action == 'q':
                    print("\nExiting review.")
                    return
                else:
                    print("Invalid option. Try again.")
        
        print("\n" + "=" * 60)
        print("Review complete!")
        print("=" * 60)
    
    def print_status(self):
        """Print current agent status."""
        status = self.agent.get_status()
        
        print("\n" + "=" * 40)
        print("AGENT STATUS")
        print("=" * 40)
        print(f"State: {status['state']}")
        print(f"Mode: {status['mode']}")
        print(f"Total Runs: {status['total_runs']}")
        print(f"Pending Changes: {status['pending_changes']}")
        print(f"Active Directives: {status['directives']}")
        
        if status.get('current_run'):
            run = status['current_run']
            print(f"\nCurrent Run: {run['id']}")
            print(f"  Files Analyzed: {run['files_analyzed']}")
            print(f"  Weaknesses Found: {run['weaknesses_found']}")
            print(f"  Improvements: {run['improvements_proposed']}")
        
        print("=" * 40)


def create_interface(root_path: str, mode: str = "supervised") -> AgentInterface:
    """Create an agent interface."""
    from .agent_orchestrator import create_agent
    agent = create_agent(root_path, mode)
    return AgentInterface(agent)
