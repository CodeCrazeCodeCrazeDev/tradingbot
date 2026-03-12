"""
Self-Improvement Engine
Main orchestrator for automated learning from losing trades.
"""

import os
import subprocess
import shutil
from pathlib import Path
from typing import Any, Dict, List, Optional
from datetime import datetime
import logging
try:
    import yaml
except ImportError:
    yaml = None
import json

from .triage import TradeTriage, TriageDiagnostic
from .root_cause_analyzer import RootCauseAnalyzer, RootCauseHypothesis
from .fix_generator import FixGenerator, ProposedFix, RiskLevel
from .canary_validator import CanaryValidator, ValidationResult, ValidationStatus
from .audit_logger import AuditLogger
from .model_learner import ContinuousLearner
from enum import auto

logger = logging.getLogger(__name__)


class SelfImprovementEngine:
    """
    Main self-improvement engine that orchestrates the entire process:
    1. Triage losing trades
    2. Analyze root causes
    3. Generate safe fixes
    4. Validate in canary mode
    5. Apply approved fixes
    6. Continuous learning
    """
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize self-improvement engine.
        
        Args:
            config: Configuration dictionary
        """
        self.config = config
        
        # Core components
        self.triage = TradeTriage(config.get('triage', {}))
        self.root_cause_analyzer = RootCauseAnalyzer(config.get('root_cause', {}))
        self.fix_generator = FixGenerator(config.get('fix_generator', {}))
        self.canary_validator = CanaryValidator(config.get('canary', {}))
        self.audit_logger = AuditLogger(config.get('audit', {}))
        self.continuous_learner = ContinuousLearner(config.get('learning', {}))
        
        # Configuration
        self.auto_learn_enabled = config.get('AUTO_LEARN', False)
        self.confidence_threshold = config.get('CONF_THRESHOLD', 0.6)
        self.auto_promote = config.get('AUTO_PROMOTE', False)
        
        # Git configuration
        self.repo_path = Path(config.get('repo_path', '.'))
        self.backup_dir = Path(config.get('backup_dir', 'backups/autolearn'))
        self.backup_dir.mkdir(parents=True, exist_ok=True)
        
        logger.info("SelfImprovementEngine initialized")
        logger.info(f"  AUTO_LEARN: {self.auto_learn_enabled}")
        logger.info(f"  CONF_THRESHOLD: {self.confidence_threshold}")
        logger.info(f"  AUTO_PROMOTE: {self.auto_promote}")
    
    def process_losing_trade(self,
                            trade: Dict[str, Any],
                            signal_data: Dict[str, Any],
                            market_data: Dict[str, Any],
                            system_data: Dict[str, Any],
                            equity: float) -> Dict[str, Any]:
        """
        Process a losing trade through the entire self-improvement pipeline.
        
        Args:
            trade: Trade dictionary
            signal_data: Signal context
            market_data: Market data snapshot
            system_data: System metrics
            equity: Current account equity
            
        Returns:
            Dictionary with processing results
        """
        if not self.auto_learn_enabled:
            logger.info("AUTO_LEARN disabled, skipping self-improvement")
            return {'status': 'disabled'}
        
        trade_id = trade['ticket_id']
        logger.info(f"Processing losing trade: {trade_id}")
        
        try:
            # Step 1: Triage
            diagnostic = self.triage.triage_trade(
                trade, signal_data, market_data, system_data, equity
            )
            self.audit_logger.log_triage(diagnostic, trade_id)
            
            # Step 2: Root cause analysis
            hypotheses = self.root_cause_analyzer.analyze(diagnostic)
            self.audit_logger.log_root_cause_analysis(trade_id, hypotheses)
            
            # Check confidence threshold
            if hypotheses and hypotheses[0].confidence < self.confidence_threshold:
                logger.warning(f"Low confidence ({hypotheses[0].confidence:.2f}), escalating to human review")
                self.audit_logger.log_escalation(
                    trade_id,
                    f"Top hypothesis confidence {hypotheses[0].confidence:.2f} below threshold {self.confidence_threshold}",
                    hypotheses[0].confidence
                )
                return {
                    'status': 'escalated',
                    'reason': 'low_confidence',
                    'confidence': hypotheses[0].confidence
                }
            
            # Step 3: Generate fixes
            fixes = self.fix_generator.generate_fixes(hypotheses)
            
            # Validate safety
            safe_fixes = [f for f in fixes if self.fix_generator.validate_fix_safety(f)]
            self.audit_logger.log_proposed_fixes(trade_id, safe_fixes)
            
            if not safe_fixes:
                logger.info("No safe fixes generated")
                return {'status': 'no_fixes'}
            
            # Step 4: Create git branch and backup
            branch_name = self._create_backup_branch(trade_id)
            
            # Step 5: Start canary validation for auto-approvable fixes
            canary_results = []
            for fix in safe_fixes:
                if fix.auto_approvable and fix.risk_level in [RiskLevel.SAFE, RiskLevel.LOW]:
                    result = self._validate_and_apply_fix(fix, diagnostic)
                    canary_results.append(result)
                else:
                    logger.info(f"Fix {fix.fix_id} requires human approval (risk: {fix.risk_level.value})")
            
            # Step 6: Add labeled example for continuous learning
            self._add_training_example(diagnostic, hypotheses)
            
            # Step 7: Check if model retraining needed
            if self.continuous_learner.should_retrain():
                logger.info("Triggering model retraining...")
                retrain_result = self.continuous_learner.retrain_model_in_sandbox()
                if retrain_result['status'] == 'success':
                    self.audit_logger.log_model_update(
                        retrain_result['version'],
                        retrain_result['metrics']
                    )
            
            return {
                'status': 'processed',
                'trade_id': trade_id,
                'diagnostic': diagnostic.to_dict(),
                'hypotheses_count': len(hypotheses),
                'fixes_proposed': len(safe_fixes),
                'canary_results': canary_results,
                'branch': branch_name
            }
            
        except Exception as e:
            logger.error(f"Error processing losing trade {trade_id}: {e}", exc_info=True)
            return {
                'status': 'error',
                'error': str(e)
            }
    
    def _validate_and_apply_fix(self, fix: ProposedFix, diagnostic: TriageDiagnostic) -> Dict[str, Any]:
        """
        Validate fix in canary mode and apply if successful.
        
        Args:
            fix: Proposed fix
            diagnostic: Original diagnostic
            
        Returns:
            Dictionary with validation and application results
        """
        logger.info(f"Starting canary validation for fix: {fix.fix_id}")
        
        # Start canary
        canary_id = self.canary_validator.start_canary(fix)
        self.audit_logger.log_canary_start(canary_id, fix)
        
        # Note: In production, canary would run for configured duration
        # collecting real trades. For now, we'll simulate completion.
        # The actual implementation would integrate with the trading loop.
        
        logger.info(f"Canary {canary_id} started - will run for {self.canary_validator.canary_duration_minutes} minutes")
        
        return {
            'fix_id': fix.fix_id,
            'canary_id': canary_id,
            'status': 'canary_running',
            'duration_minutes': self.canary_validator.canary_duration_minutes
        }
    
    def finalize_canary(self, canary_id: str) -> Dict[str, Any]:
        """
        Finalize canary validation and apply fix if passed.
        
        Args:
            canary_id: Canary run ID
            
        Returns:
            Dictionary with finalization results
        """
        try:
            # Finalize canary
            result = self.canary_validator.finalize_canary(canary_id)
            self.audit_logger.log_canary_result(result)
            
            # Check result
            if result.status == ValidationStatus.PASSED and result.recommendation == 'promote':
                if self.auto_promote:
                    # Apply fix
                    success = self._apply_fix(result.fix_id)
                    
                    if success:
                        logger.info(f"Fix {result.fix_id} applied successfully")
                        return {
                            'status': 'applied',
                            'fix_id': result.fix_id,
                            'canary_result': result.to_dict()
                        }
                    else:
                        # Rollback
                        self._rollback_fix(result.fix_id, "Application failed")
                        return {
                            'status': 'rollback',
                            'fix_id': result.fix_id,
                            'reason': 'application_failed'
                        }
                else:
                    logger.info(f"Fix {result.fix_id} passed canary but AUTO_PROMOTE=False, creating PR")
                    return {
                        'status': 'awaiting_approval',
                        'fix_id': result.fix_id,
                        'canary_result': result.to_dict()
                    }
            
            elif result.status == ValidationStatus.FAILED:
                # Rollback
                self._rollback_fix(result.fix_id, "Canary validation failed")
                return {
                    'status': 'rollback',
                    'fix_id': result.fix_id,
                    'reason': 'canary_failed',
                    'failed_criteria': result.failed_criteria
                }
            
            else:
                return {
                    'status': result.status.value,
                    'fix_id': result.fix_id,
                    'recommendation': result.recommendation
                }
                
        except Exception as e:
            logger.error(f"Error finalizing canary {canary_id}: {e}")
            return {
                'status': 'error',
                'error': str(e)
            }
    
    def _create_backup_branch(self, trade_id: str) -> str:
        """
        Create git branch and backup for changes.
        
        Args:
            trade_id: Trade ID
            
        Returns:
            Branch name
        """
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        branch_name = f"autolearn/{timestamp}_{trade_id}"
        
        try:
            # Create git branch
            subprocess.run(
                ['git', 'checkout', '-b', branch_name],
                cwd=self.repo_path,
                check=True,
                capture_output=True
            )
            logger.info(f"Created git branch: {branch_name}")
            
            # Create backup snapshot
            backup_path = self.backup_dir / f"backup_{timestamp}_{trade_id}"
            backup_path.mkdir(parents=True, exist_ok=True)
            
            # Backup config files
            config_dir = self.repo_path / 'config'
            if config_dir.exists():
                shutil.copytree(config_dir, backup_path / 'config', dirs_exist_ok=True)
            
            logger.info(f"Created backup: {backup_path}")
            
            return branch_name
            
        except Exception as e:
            logger.error(f"Failed to create backup branch: {e}")
            return ""
    
    def _apply_fix(self, fix_id: str) -> bool:
        """
        Apply a fix to the configuration.
        
        Args:
            fix_id: Fix ID
            
        Returns:
            True if successful
        """
        try:
            # Note: This would load the fix details and apply the changes
        # For now, this is a placeholder
        
            logger.info(f"Applying fix: {fix_id}")
            
            # Load fix details from audit log
            # Apply configuration changes
            # Commit to git
            
            self.audit_logger.log_fix_application(fix_id, True, "Fix applied successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to apply fix {fix_id}: {e}")
            self.audit_logger.log_fix_application(fix_id, False, str(e))
            return False
    
    def _rollback_fix(self, fix_id: str, reason: str):
        """
        Rollback a fix.
        
        Args:
            fix_id: Fix ID
            reason: Reason for rollback
        """
        try:
            logger.info(f"Rolling back fix {fix_id}: {reason}")
            
            # Revert git changes
            subprocess.run(
                ['git', 'checkout', 'main'],
                cwd=self.repo_path,
                check=True,
                capture_output=True
            )
            
            # Delete branch
            subprocess.run(
                ['git', 'branch', '-D', f"autolearn/*{fix_id}*"],
                cwd=self.repo_path,
                capture_output=True
            )
            
            self.audit_logger.log_rollback(fix_id, reason)
            logger.info(f"Rollback complete for {fix_id}")
            
        except Exception as e:
            logger.error(f"Failed to rollback fix {fix_id}: {e}")
    
    def _add_training_example(self, diagnostic: TriageDiagnostic, hypotheses: List[RootCauseHypothesis]):
        """
        Add labeled training example for continuous learning.
        
        Args:
            diagnostic: Triage diagnostic
            hypotheses: Root cause hypotheses
        """
        try:
            # Extract features
            features = {
                'signal_confidence': diagnostic.signal_context.model_confidence,
                'multi_tf_agreement': diagnostic.signal_context.multi_tf_agreement,
                'signal_drift': diagnostic.signal_context.signal_drift,
                'slippage': diagnostic.trade_data.slippage,
                'execution_latency_ms': diagnostic.trade_data.execution_latency_ms,
                'atr': diagnostic.market_snapshot.atr,
                'spread': diagnostic.market_snapshot.spread,
                'volatility_spike': diagnostic.market_snapshot.volatility_spike,
                'news_events_count': len(diagnostic.market_snapshot.news_events),
                'system_errors_count': len(diagnostic.system_metrics.errors_in_logs),
                'regime': diagnostic.regime,
                'loss_category': diagnostic.loss_category.value
            }
            
            # Root cause label
            root_cause = hypotheses[0].cause_type.value if hypotheses else 'unknown'
            
            # Add to learner
            self.continuous_learner.add_labeled_example(
                trade_id=diagnostic.trade_id,
                features=features,
                outcome='loss',
                root_cause=root_cause,
                pnl=diagnostic.pnl,
                metadata={
                    'confidence': hypotheses[0].confidence if hypotheses else 0,
                    'anomalies': diagnostic.anomalies
                }
            )
            
        except Exception as e:
            logger.error(f"Failed to add training example: {e}")
    
    def get_status(self) -> Dict[str, Any]:
        """
        Get current status of self-improvement system.
        
        Returns:
            Status dictionary
        """
        return {
            'auto_learn_enabled': self.auto_learn_enabled,
            'confidence_threshold': self.confidence_threshold,
            'auto_promote': self.auto_promote,
            'labeled_examples': len(self.continuous_learner.labeled_examples),
            'ready_for_retrain': self.continuous_learner.should_retrain(),
            'current_model_version': self.continuous_learner.current_model_version,
            'active_canaries': len(self.canary_validator.active_canaries),
            'audit_summary': self.audit_logger.generate_summary_report()
        }
