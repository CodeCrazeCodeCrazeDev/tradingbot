"""
Audit Logger
Maintains comprehensive audit trail of all self-improvement actions.
"""

import json
import os
from datetime import datetime
from typing import Any, Dict, List, Optional
from pathlib import Path
import logging

logger = logging.getLogger(__name__)


class AuditLogger:
    """
    Maintains comprehensive audit trail for self-improvement system.
    All decisions, hypotheses, fixes, and validations are logged.
    """
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize audit logger.
        
        Args:
            config: Configuration dictionary
        """
        self.config = config
        self.audit_dir = Path(config.get('audit_dir', 'diagnostics/self_improve'))
        self.changes_log = Path(config.get('changes_log', 'diagnostics/changes-log.txt'))
        
        # Create directories
        self.audit_dir.mkdir(parents=True, exist_ok=True)
        self.changes_log.parent.mkdir(parents=True, exist_ok=True)
        
        logger.info(f"AuditLogger initialized: {self.audit_dir}")
    
    def log_triage(self, diagnostic: Any, trade_id: str):
        """
        Log triage diagnostic.
        
        Args:
            diagnostic: TriageDiagnostic object
            trade_id: Trade ID
        """
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = self.audit_dir / f"{timestamp}_triage_{trade_id}.json"
        
        try:
            with open(filename, 'w') as f:
                json.dump(diagnostic.to_dict(), f, indent=2, default=str)
            
            logger.info(f"Logged triage: {filename}")
        except Exception as e:
            logger.error(f"Failed to log triage: {e}")
    
    def log_root_cause_analysis(self, trade_id: str, hypotheses: List[Any]):
        """
        Log root cause analysis results.
        
        Args:
            trade_id: Trade ID
            hypotheses: List of RootCauseHypothesis objects
        """
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = self.audit_dir / f"{timestamp}_root_cause_{trade_id}.json"
        
        try:
            data = {
                'trade_id': trade_id,
                'timestamp': timestamp,
                'hypotheses': [h.to_dict() for h in hypotheses]
            }
            
            with open(filename, 'w') as f:
                json.dump(data, f, indent=2, default=str)
            
            logger.info(f"Logged root cause analysis: {filename}")
        except Exception as e:
            logger.error(f"Failed to log root cause analysis: {e}")
    
    def log_proposed_fixes(self, trade_id: str, fixes: List[Any]):
        """
        Log proposed fixes.
        
        Args:
            trade_id: Trade ID
            fixes: List of ProposedFix objects
        """
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = self.audit_dir / f"{timestamp}_fixes_{trade_id}.json"
        
        try:
            data = {
                'trade_id': trade_id,
                'timestamp': timestamp,
                'fixes': [f.to_dict() for f in fixes]
            }
            
            with open(filename, 'w') as f:
                json.dump(data, f, indent=2, default=str)
            
            logger.info(f"Logged proposed fixes: {filename}")
        except Exception as e:
            logger.error(f"Failed to log proposed fixes: {e}")
    
    def log_canary_start(self, canary_id: str, fix: Any):
        """
        Log canary validation start.
        
        Args:
            canary_id: Canary run ID
            fix: ProposedFix object
        """
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = self.audit_dir / f"{timestamp}_canary_start_{canary_id}.json"
        
        try:
            data = {
                'canary_id': canary_id,
                'timestamp': timestamp,
                'fix': fix.to_dict()
            }
            
            with open(filename, 'w') as f:
                json.dump(data, f, indent=2, default=str)
            
            self._append_to_changes_log(
                f"[{timestamp}] CANARY_START: {canary_id} for fix {fix.fix_id}"
            )
            
            logger.info(f"Logged canary start: {filename}")
        except Exception as e:
            logger.error(f"Failed to log canary start: {e}")
    
    def log_canary_result(self, result: Any):
        """
        Log canary validation result.
        
        Args:
            result: ValidationResult object
        """
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = self.audit_dir / f"{timestamp}_canary_result_{result.fix_id}.json"
        
        try:
            with open(filename, 'w') as f:
                json.dump(result.to_dict(), f, indent=2, default=str)
            
            self._append_to_changes_log(
                f"[{timestamp}] CANARY_RESULT: {result.fix_id} - {result.status.value} - {result.recommendation}"
            )
            
            logger.info(f"Logged canary result: {filename}")
        except Exception as e:
            logger.error(f"Failed to log canary result: {e}")
    
    def log_fix_application(self, fix_id: str, success: bool, details: str):
        """
        Log fix application.
        
        Args:
            fix_id: Fix ID
            success: Whether application succeeded
            details: Additional details
        """
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = self.audit_dir / f"{timestamp}_apply_{fix_id}.json"
        
        try:
            data = {
                'fix_id': fix_id,
                'timestamp': timestamp,
                'success': success,
                'details': details
            }
            
            with open(filename, 'w') as f:
                json.dump(data, f, indent=2, default=str)
            
            status = "SUCCESS" if success else "FAILED"
            self._append_to_changes_log(
                f"[{timestamp}] FIX_APPLY_{status}: {fix_id} - {details}"
            )
            
            logger.info(f"Logged fix application: {filename}")
        except Exception as e:
            logger.error(f"Failed to log fix application: {e}")
    
    def log_rollback(self, fix_id: str, reason: str):
        """
        Log fix rollback.
        
        Args:
            fix_id: Fix ID
            reason: Reason for rollback
        """
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = self.audit_dir / f"{timestamp}_rollback_{fix_id}.json"
        
        try:
            data = {
                'fix_id': fix_id,
                'timestamp': timestamp,
                'reason': reason
            }
            
            with open(filename, 'w') as f:
                json.dump(data, f, indent=2, default=str)
            
            self._append_to_changes_log(
                f"[{timestamp}] ROLLBACK: {fix_id} - {reason}"
            )
            
            logger.info(f"Logged rollback: {filename}")
        except Exception as e:
            logger.error(f"Failed to log rollback: {e}")
    
    def log_escalation(self, trade_id: str, reason: str, confidence: float):
        """
        Log escalation to human review.
        
        Args:
            trade_id: Trade ID
            reason: Reason for escalation
            confidence: Confidence level
        """
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = self.audit_dir / f"PAUSE-REQUEST-{timestamp}.md"
        
        content = f"""# Self-Improvement Escalation Request

**Trade ID:** {trade_id}
**Timestamp:** {timestamp}
**Confidence:** {confidence:.2f}

## Reason for Escalation

{reason}

## Action Required

Human review and approval needed before proceeding with automated fixes.

## Review Checklist

- [ ] Review triage diagnostic
- [ ] Review root cause hypotheses
- [ ] Review proposed fixes
- [ ] Approve/reject fixes
- [ ] Update confidence threshold if needed

## Files to Review

- `{timestamp}_triage_{trade_id}.json`
- `{timestamp}_root_cause_{trade_id}.json`
- `{timestamp}_fixes_{trade_id}.json`

"""
            
        try:
            with open(filename, 'w') as f:
                f.write(content)
            
            self._append_to_changes_log(
                f"[{timestamp}] ESCALATION: {trade_id} - confidence {confidence:.2f} - {reason}"
            )
            
            logger.warning(f"Escalated to human review: {filename}")
        except Exception as e:
            logger.error(f"Failed to log escalation: {e}")
    
    def log_model_update(self, model_version: str, metrics: Dict[str, float]):
        """
        Log model update.
        
        Args:
            model_version: New model version
            metrics: Performance metrics
        """
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = self.audit_dir / f"{timestamp}_model_update_{model_version}.json"
        
        try:
            data = {
                'model_version': model_version,
                'timestamp': timestamp,
                'metrics': metrics
            }
            
            with open(filename, 'w') as f:
                json.dump(data, f, indent=2, default=str)
            
            self._append_to_changes_log(
                f"[{timestamp}] MODEL_UPDATE: {model_version} - accuracy: {metrics.get('accuracy', 0):.3f}"
            )
            
            logger.info(f"Logged model update: {filename}")
        except Exception as e:
            logger.error(f"Failed to log model update: {e}")
    
    def _append_to_changes_log(self, message: str):
        """
        Append message to changes log file.
        
        Args:
            message: Message to append
        """
        try:
            with open(self.changes_log, 'a') as f:
                f.write(message + '\n')
        except Exception as e:
            logger.error(f"Failed to append to changes log: {e}")
    
    def get_recent_changes(self, days: int = 7) -> List[str]:
        """
        Get recent changes from log.
        
        Args:
            days: Number of days to look back
            
        Returns:
            List of recent change entries
        """
        try:
            if not self.changes_log.exists():
                return []
            
            with open(self.changes_log, 'r') as f:
                lines = f.readlines()
            
            # Filter by date (simplified - just return last N lines)
            return lines[-100:]  # Last 100 entries
        except Exception as e:
            logger.error(f"Failed to read changes log: {e}")
            return []
    
    def generate_summary_report(self, days: int = 7) -> Dict[str, Any]:
        """
        Generate summary report of self-improvement activities.
        
        Args:
            days: Number of days to summarize
            
        Returns:
            Summary dictionary
        """
        try:
            # Count files by type
            triage_count = len(list(self.audit_dir.glob('*_triage_*.json')))
            root_cause_count = len(list(self.audit_dir.glob('*_root_cause_*.json')))
            fixes_count = len(list(self.audit_dir.glob('*_fixes_*.json')))
            canary_count = len(list(self.audit_dir.glob('*_canary_result_*.json')))
            apply_count = len(list(self.audit_dir.glob('*_apply_*.json')))
            rollback_count = len(list(self.audit_dir.glob('*_rollback_*.json')))
            escalation_count = len(list(self.audit_dir.glob('PAUSE-REQUEST-*.md')))
            
            return {
                'period_days': days,
                'triage_diagnostics': triage_count,
                'root_cause_analyses': root_cause_count,
                'fixes_proposed': fixes_count,
                'canary_validations': canary_count,
                'fixes_applied': apply_count,
                'rollbacks': rollback_count,
                'escalations': escalation_count,
                'audit_dir': str(self.audit_dir),
                'changes_log': str(self.changes_log)
            }
        except Exception as e:
            logger.error(f"Failed to generate summary report: {e}")
            return {}
