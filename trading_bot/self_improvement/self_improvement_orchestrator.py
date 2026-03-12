"""
Self-Improvement Orchestrator
Master controller that coordinates the entire self-improvement workflow:
1. Analyze codebase for issues
2. Generate fix proposals
3. Present to human for approval
4. Apply approved changes
"""

import os
import logging
from typing import Any, Dict, List, Optional
from datetime import datetime
from pathlib import Path
import json

from .code_analyzer import CodeAnalyzer, CodeIssue, IssueCategory, IssueSeverity
from .proposal_engine import ProposalEngine, Proposal, ProposalStatus, RiskLevel
from .approval_manager import ApprovalManager, ApprovalDecision
from .code_rewriter import CodeRewriter, ApplyResult
from enum import auto

logger = logging.getLogger(__name__)


class SelfImprovementOrchestrator:
    """
    Master orchestrator for the self-improvement system.
    
    Workflow:
    1. scan() - Analyze codebase for issues
    2. propose() - Generate fix proposals
    3. review() - Present proposals for human approval
    4. apply() - Apply approved changes
    5. rollback() - Revert changes if needed
    """
    
    def __init__(self, base_path: str, storage_path: str = None):
        """
        Initialize the self-improvement system.
        
        Args:
            base_path: Root path of the trading bot codebase
            storage_path: Path to store proposals, backups, etc.
        """
        try:
            self.base_path = Path(base_path)
            self.storage_path = Path(storage_path) if storage_path else self.base_path / "self_improvement_data"
            self.storage_path.mkdir(parents=True, exist_ok=True)
        
            # Initialize components
            self.analyzer = CodeAnalyzer(str(self.base_path))
            self.proposal_engine = ProposalEngine(str(self.base_path))
            self.approval_manager = ApprovalManager(str(self.storage_path / "approvals"))
            self.code_rewriter = CodeRewriter(str(self.base_path), str(self.storage_path / "backups"))
        
            # State
            self.last_scan_time: Optional[datetime] = None
            self.issues: List[CodeIssue] = []
            self.proposals: List[Proposal] = []
        
            logger.info(f"SelfImprovementOrchestrator initialized")
            logger.info(f"  Base path: {self.base_path}")
            logger.info(f"  Storage: {self.storage_path}")
        except Exception as e:
            logger.error(f"Error in __init__: {e}")
            raise
    
    def scan(self, max_files: int = 100, save_report: bool = True) -> Dict[str, Any]:
        """
        Scan the codebase for issues.
        
        Args:
            max_files: Maximum number of files to analyze
            save_report: Whether to save the report to file
            
        Returns:
            Summary of issues found
        """
        try:
            logger.info("=" * 60)
            logger.info("PHASE 1: SCANNING CODEBASE FOR ISSUES")
            logger.info("=" * 60)
        
            self.issues = self.analyzer.analyze_codebase(max_files)
            self.last_scan_time = datetime.now()
        
            summary = self.analyzer.get_summary()
        
            if save_report:
                report_path = self.storage_path / f"scan_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
                self.analyzer.save_report(str(report_path))
        
            # Print summary
            print("\n" + "=" * 60)
            logger.info("SCAN COMPLETE")
            print("=" * 60)
            logger.info(f"\n📊 SUMMARY:")
            logger.info(f"   Total Issues Found: {summary['total_issues']}")
            logger.info(f"   🔴 Critical: {summary.get('critical_count', 0)}")
            logger.info(f"   🟠 High: {summary.get('high_count', 0)}")
            logger.info(f"\n📁 BY CATEGORY:")
            for cat, count in summary['by_category'].items():
                logger.info(f"   • {cat}: {count}")
            logger.info(f"\n📄 TOP PROBLEM FILES:")
            for file_path, count in summary['top_problem_files'][:5]:
                logger.info(f"   • {file_path}: {count} issues")
            logger.info("=" * 60 + "\n")
        
            return summary
        except Exception as e:
            logger.error(f"Error in scan: {e}")
            raise
    
    def propose(self, 
                categories: List[IssueCategory] = None,
                severities: List[IssueSeverity] = None,
                max_proposals: int = 50) -> List[Proposal]:
        """
        Generate fix proposals for found issues.
        
        Args:
            categories: Filter by issue categories (None = all)
            severities: Filter by severities (None = all)
            max_proposals: Maximum number of proposals to generate
            
        Returns:
            List of generated proposals
        """
        try:
            logger.info("=" * 60)
            logger.info("PHASE 2: GENERATING FIX PROPOSALS")
            logger.info("=" * 60)
        
            if not self.issues:
                logger.warning("No issues to propose fixes for. Run scan() first.")
                return []
        
            # Filter issues
            filtered_issues = self.issues
        
            if categories:
                filtered_issues = [i for i in filtered_issues if i.category in categories]
        
            if severities:
                filtered_issues = [i for i in filtered_issues if i.severity in severities]
        
            # Limit
            filtered_issues = filtered_issues[:max_proposals]
        
            # Generate proposals
            self.proposals = self.proposal_engine.generate_proposals(filtered_issues)
        
            # Add to approval manager
            self.approval_manager.add_proposals(self.proposals)
        
            # Save proposals
            proposals_path = self.storage_path / f"proposals_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            self.proposal_engine.save_proposals(str(proposals_path))
        
            # Print summary
            print("\n" + "=" * 60)
            logger.info("PROPOSALS GENERATED")
            print("=" * 60)
            logger.info(f"\n📋 Generated {len(self.proposals)} proposals")
        
            by_risk = {}
            for p in self.proposals:
                risk = p.risk_level.value
                by_risk[risk] = by_risk.get(risk, 0) + 1
        
            logger.info(f"\n🎯 BY RISK LEVEL:")
            for risk, count in by_risk.items():
                logger.info(f"   • {risk}: {count}")
            logger.info("=" * 60 + "\n")
        
            return self.proposals
        except Exception as e:
            logger.error(f"Error in propose: {e}")
            raise
    
    def review_interactive(self) -> Dict[str, int]:
        """
        Interactive review of pending proposals.
        
        Returns:
            Summary of decisions made
        """
        try:
            pending = self.approval_manager.get_pending_proposals()
        
            if not pending:
                logger.info("\n✓ No pending proposals to review.\n")
                return {'approved': 0, 'rejected': 0, 'deferred': 0}
        
            print("\n" + "=" * 60)
            logger.info(f"INTERACTIVE REVIEW - {len(pending)} PENDING PROPOSALS")
            print("=" * 60)
        
            decisions = {'approved': 0, 'rejected': 0, 'deferred': 0, 'skipped': 0}
        
            for i, proposal in enumerate(pending, 1):
                logger.info(f"\n[{i}/{len(pending)}]")
                print(self.approval_manager.format_proposal_for_review(proposal))
            
                while True:
                    choice = input("\nYour decision (A/R/D/S/Q to quit): ").strip().upper()
                
                    if choice == 'A':
                        notes = input("Notes (optional): ").strip()
                        self.approval_manager.approve(proposal.proposal_id, notes)
                        decisions['approved'] += 1
                        logger.info("✓ APPROVED")
                        break
                    elif choice == 'R':
                        notes = input("Reason for rejection: ").strip()
                        self.approval_manager.reject(proposal.proposal_id, notes)
                        decisions['rejected'] += 1
                        logger.info("✗ REJECTED")
                        break
                    elif choice == 'D':
                        notes = input("Notes (optional): ").strip()
                        self.approval_manager.defer(proposal.proposal_id, notes)
                        decisions['deferred'] += 1
                        logger.info("⏸ DEFERRED")
                        break
                    elif choice == 'S':
                        decisions['skipped'] += 1
                        logger.info("→ SKIPPED")
                        break
                    elif choice == 'Q':
                        logger.info("\nExiting review...")
                        return decisions
                    else:
                        logger.info("Invalid choice. Use A (Approve), R (Reject), D (Defer), S (Skip), Q (Quit)")
        
            print("\n" + "=" * 60)
            logger.info("REVIEW COMPLETE")
            print("=" * 60)
            logger.info(f"   ✓ Approved: {decisions['approved']}")
            logger.info(f"   ✗ Rejected: {decisions['rejected']}")
            logger.info(f"   ⏸ Deferred: {decisions['deferred']}")
            logger.info(f"   → Skipped: {decisions['skipped']}")
            logger.info("=" * 60 + "\n")
        
            return decisions
        except Exception as e:
            logger.error(f"Error in review_interactive: {e}")
            raise
    
    def apply(self, dry_run: bool = False) -> List[ApplyResult]:
        """
        Apply all approved proposals.
        
        Args:
            dry_run: If True, only validate without making changes
            
        Returns:
            List of apply results
        """
        try:
            logger.info("=" * 60)
            logger.info(f"PHASE 4: {'[DRY RUN] ' if dry_run else ''}APPLYING APPROVED CHANGES")
            logger.info("=" * 60)
        
            approved = self.approval_manager.get_approved_proposals()
        
            if not approved:
                logger.info("\n✓ No approved proposals to apply.\n")
                return []
        
            logger.info(f"\n{'[DRY RUN] ' if dry_run else ''}Applying {len(approved)} approved proposals...")
        
            results = self.code_rewriter.apply_all_approved(approved, dry_run)
        
            # Print summary
            successful = sum(1 for r in results if r.success)
            failed = len(results) - successful
        
            print("\n" + "=" * 60)
            logger.info(f"{'[DRY RUN] ' if dry_run else ''}APPLICATION COMPLETE")
            print("=" * 60)
            logger.info(f"   ✓ Successful: {successful}")
            logger.info(f"   ✗ Failed: {failed}")
        
            if not dry_run:
                # Save history
                history_path = self.storage_path / f"apply_history_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
                self.code_rewriter.save_history(str(history_path))
        
            logger.info("=" * 60 + "\n")
        
            return results
        except Exception as e:
            logger.error(f"Error in apply: {e}")
            raise
    
    def rollback(self, proposal_id: str) -> bool:
        """
        Rollback changes from a specific proposal.
        
        Args:
            proposal_id: ID of proposal to rollback
            
        Returns:
            True if rollback successful
        """
        try:
            logger.info(f"Rolling back proposal {proposal_id}")
            return self.code_rewriter.rollback_proposal(proposal_id)
        except Exception as e:
            logger.error(f"Error in rollback: {e}")
            raise
    
    def auto_approve_safe(self) -> List[str]:
        """
        Auto-approve all minimal-risk proposals.
        
        Returns:
            List of auto-approved proposal IDs
        """
        try:
            approved = self.approval_manager.approve_all_minimal_risk()
            logger.info(f"\n✓ Auto-approved {len(approved)} minimal-risk proposals\n")
            return approved
        except Exception as e:
            logger.error(f"Error in auto_approve_safe: {e}")
            raise
    
    def get_status(self) -> Dict[str, Any]:
        """Get current status of the self-improvement system."""
        try:
            approval_summary = self.approval_manager.get_summary()
        
            return {
                'last_scan': self.last_scan_time.isoformat() if self.last_scan_time else None,
                'total_issues': len(self.issues),
                'total_proposals': len(self.proposals),
                'approval_status': approval_summary,
                'apply_history_count': len(self.code_rewriter.apply_history)
            }
        except Exception as e:
            logger.error(f"Error in get_status: {e}")
            raise
    
    def save_for_offline_review(self, output_path: str = None) -> str:
        """
        Save pending proposals to a file for offline review.
        
        Args:
            output_path: Output file path (default: auto-generated)
            
        Returns:
            Path to the saved file
        """
        try:
            if not output_path:
                output_path = str(self.storage_path / f"pending_review_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt")
        
            self.approval_manager.save_pending_for_review(output_path)
            logger.info(f"\n✓ Saved pending proposals to: {output_path}\n")
            return output_path
        except Exception as e:
            logger.error(f"Error in save_for_offline_review: {e}")
            raise
    
    def run_full_cycle(self, 
                       max_files: int = 100,
                       auto_approve_minimal: bool = True,
                       dry_run: bool = True) -> Dict[str, Any]:
        """
        Run the complete self-improvement cycle.
        
        Args:
            max_files: Maximum files to scan
            auto_approve_minimal: Auto-approve minimal-risk proposals
            dry_run: If True, don't actually apply changes
            
        Returns:
            Summary of the cycle
        """
        try:
            print("\n" + "=" * 70)
            logger.info("ALPHAALGO SELF-IMPROVEMENT CYCLE")
            logger.info("=" * 70 + "\n")
        
            # Phase 1: Scan
            scan_summary = self.scan(max_files)
        
            # Phase 2: Propose
            proposals = self.propose()
        
            # Phase 3: Auto-approve safe changes
            auto_approved = []
            if auto_approve_minimal:
                auto_approved = self.auto_approve_safe()
        
            # Phase 4: Interactive review for remaining
            pending = self.approval_manager.get_pending_proposals()
            if pending:
                logger.info(f"\n{len(pending)} proposals need your review.")
                review_now = input("Review now? (y/n): ").strip().lower()
                if review_now == 'y':
                    self.review_interactive()
        
            # Phase 5: Apply approved changes
            approved = self.approval_manager.get_approved_proposals()
            if approved:
                logger.info(f"\n{len(approved)} proposals approved and ready to apply.")
                if dry_run:
                    logger.info("[DRY RUN MODE - No changes will be made]")
                apply_now = input(f"Apply changes? {'(dry run) ' if dry_run else ''}(y/n): ").strip().lower()
                if apply_now == 'y':
                    self.apply(dry_run)
        
            # Summary
            status = self.get_status()
        
            print("\n" + "=" * 70)
            logger.info("CYCLE COMPLETE")
            print("=" * 70)
            logger.info(f"   Issues Found: {status['total_issues']}")
            logger.info(f"   Proposals Generated: {status['total_proposals']}")
            logger.info(f"   Auto-Approved: {len(auto_approved)}")
            logger.info(f"   Pending Review: {status['approval_status']['pending']}")
            logger.info(f"   Applied: {status['approval_status']['applied']}")
            logger.info("=" * 70 + "\n")
        
            return status
        except Exception as e:
            logger.error(f"Error in run_full_cycle: {e}")
            raise


def quick_start(base_path: str = None) -> SelfImprovementOrchestrator:
    """
    Quick start the self-improvement system.
    
    Args:
        base_path: Root path of codebase (default: auto-detect)
        
    Returns:
        Initialized orchestrator
    """
    try:
        if not base_path:
            # Try to find the trading bot root
            current = Path(__file__).parent.parent.parent
            if (current / "trading_bot").exists():
                base_path = str(current)
            else:
                base_path = os.getcwd()
    
        return SelfImprovementOrchestrator(base_path)
    except Exception as e:
        logger.error(f"Error in quick_start: {e}")
        raise
