"""
Evolution Monitor
=================

Continuous monitoring of AI evolution with automatic rollback
if safety is compromised.
"""

import hashlib
import json
import logging
import pickle
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any

from .immutable_safety_core import get_safety_core, SafetyBoundary
from .risk_mitigation_matrix import RiskMitigationMatrix, RiskLevel, RiskCategory

logger = logging.getLogger(__name__)


@dataclass
class EvolutionMetrics:
    """Metrics tracking AI evolution"""
    timestamp: datetime
    recursion_depth: int
    code_changes_count: int
    code_change_percentage: float
    performance_score: float
    safety_score: float
    risk_level: RiskLevel
    total_improvements: int
    successful_improvements: int
    failed_improvements: int
    rolled_back_improvements: int


@dataclass
class SafetyCheckpoint:
    """A safety checkpoint for rollback"""
    checkpoint_id: str
    timestamp: datetime
    description: str
    system_state: Dict[str, Any]
    code_snapshot: Dict[str, str]  # file_path -> content
    metrics: EvolutionMetrics
    hash_signature: str
    
    def verify_integrity(self) -> bool:
        """Verify checkpoint hasn't been tampered with"""
        data = f"{self.checkpoint_id}:{self.timestamp.isoformat()}:{self.description}"
        expected_hash = hashlib.sha256(data.encode()).hexdigest()
        return expected_hash == self.hash_signature


class EvolutionMonitor:
    """
    Evolution Monitor
    
    Continuously monitors AI evolution and can automatically
    rollback if safety is compromised.
    
    Key Features:
    - Automatic safety checkpoints
    - Continuous evolution metrics tracking
    - Anomaly detection
    - Automatic rollback on safety violations
    - Evolution history tracking
    """
    
    def __init__(self, workspace_path: str, checkpoint_dir: str = "checkpoints"):
        self.workspace_path = Path(workspace_path)
        self.checkpoint_dir = self.workspace_path / checkpoint_dir
        self.checkpoint_dir.mkdir(parents=True, exist_ok=True)
        
        self.safety_core = get_safety_core()
        self.risk_matrix = RiskMitigationMatrix()
        
        self.checkpoints: Dict[str, SafetyCheckpoint] = {}
        self.metrics_history: List[EvolutionMetrics] = []
        
        self.checkpoint_interval = timedelta(hours=1)
        self.last_checkpoint_time = datetime.utcnow()
        
        self.anomaly_threshold = 0.7
        self.auto_rollback_enabled = True
        
        # Load existing checkpoints
        self._load_checkpoints()
        
        logger.info("EvolutionMonitor initialized")
    
    def create_checkpoint(self, description: str = "Automatic checkpoint") -> SafetyCheckpoint:
        """
        Create a safety checkpoint.
        
        This captures the current state of the system for potential rollback.
        """
        
        timestamp = datetime.utcnow()
        checkpoint_id = hashlib.sha256(
            f"{description}:{timestamp.isoformat()}".encode()
        ).hexdigest()[:16]
        
        # Capture current metrics
        current_metrics = self._capture_current_metrics()
        
        # Capture code snapshot
        code_snapshot = self._capture_code_snapshot()
        
        # Capture system state
        system_state = {
            'safety_core_integrity': self.safety_core.verify_integrity(),
            'risk_level': self.risk_matrix.get_overall_risk_level().name,
            'timestamp': timestamp.isoformat()
        }
        
        # Create hash signature
        data = f"{checkpoint_id}:{timestamp.isoformat()}:{description}"
        hash_signature = hashlib.sha256(data.encode()).hexdigest()
        
        checkpoint = SafetyCheckpoint(
            checkpoint_id=checkpoint_id,
            timestamp=timestamp,
            description=description,
            system_state=system_state,
            code_snapshot=code_snapshot,
            metrics=current_metrics,
            hash_signature=hash_signature
        )
        
        # Save checkpoint
        self.checkpoints[checkpoint_id] = checkpoint
        self._save_checkpoint(checkpoint)
        
        self.last_checkpoint_time = timestamp
        
        logger.info(f"Created checkpoint: {checkpoint_id} - {description}")
        
        return checkpoint
    
    def _capture_current_metrics(self) -> EvolutionMetrics:
        """Capture current evolution metrics"""
        
        # In production, these would be real metrics
        # For now, we'll use placeholders
        
        return EvolutionMetrics(
            timestamp=datetime.utcnow(),
            recursion_depth=0,
            code_changes_count=0,
            code_change_percentage=0.0,
            performance_score=1.0,
            safety_score=1.0,
            risk_level=self.risk_matrix.get_overall_risk_level(),
            total_improvements=0,
            successful_improvements=0,
            failed_improvements=0,
            rolled_back_improvements=0
        )
    
    def _capture_code_snapshot(self) -> Dict[str, str]:
        """Capture snapshot of critical code files"""
        
        snapshot = {}
        
        # Capture critical files
        critical_files = [
            'trading_bot/self_assembly_ai/immutable_safety_core.py',
            'trading_bot/self_assembly_ai/risk_mitigation_matrix.py',
            'trading_bot/core/risk_manager.py',
        ]
        
        for file_path in critical_files:
            full_path = self.workspace_path / file_path
            if full_path.exists():
                snapshot[file_path] = full_path.read_text()
        
        return snapshot
    
    def _save_checkpoint(self, checkpoint: SafetyCheckpoint):
        """Save checkpoint to disk"""
        
        checkpoint_file = self.checkpoint_dir / f"{checkpoint.checkpoint_id}.pkl"
        
        try:
            with open(checkpoint_file, 'wb') as f:
                pickle.dump(checkpoint, f)
            logger.info(f"Saved checkpoint to {checkpoint_file}")
        except Exception as e:
            logger.error(f"Error saving checkpoint: {e}")
    
    def _load_checkpoints(self):
        """Load existing checkpoints from disk"""
        
        try:
            for checkpoint_file in self.checkpoint_dir.glob("*.pkl"):
                try:
                    with open(checkpoint_file, 'rb') as f:
                        checkpoint = pickle.load(f)
                    
                    # Verify integrity
                    if checkpoint.verify_integrity():
                        self.checkpoints[checkpoint.checkpoint_id] = checkpoint
                    else:
                        logger.warning(f"Checkpoint integrity check failed: {checkpoint_file}")
                
                except Exception as e:
                    logger.error(f"Error loading checkpoint {checkpoint_file}: {e}")
            
            logger.info(f"Loaded {len(self.checkpoints)} checkpoints")
        
        except Exception as e:
            logger.error(f"Error loading checkpoints: {e}")
    
    def update_metrics(self, metrics: EvolutionMetrics):
        """Update evolution metrics"""
        
        self.metrics_history.append(metrics)
        
        # Check if checkpoint is needed
        time_since_checkpoint = datetime.utcnow() - self.last_checkpoint_time
        if time_since_checkpoint >= self.checkpoint_interval:
            self.create_checkpoint("Scheduled checkpoint")
        
        # Check for anomalies
        if self._detect_anomaly(metrics):
            logger.warning("Anomaly detected in evolution metrics")
            
            if self.auto_rollback_enabled and metrics.risk_level.value >= RiskLevel.HIGH.value:
                logger.critical("High risk detected - initiating automatic rollback")
                self.rollback_to_last_safe_checkpoint()
    
    def _detect_anomaly(self, metrics: EvolutionMetrics) -> bool:
        """Detect anomalies in evolution metrics"""
        
        # Check for sudden changes
        if len(self.metrics_history) < 2:
            return False
        
        prev_metrics = self.metrics_history[-2]
        
        # Check for sudden performance drop
        if metrics.performance_score < prev_metrics.performance_score * 0.5:
            logger.warning("Sudden performance drop detected")
            return True
        
        # Check for sudden safety score drop
        if metrics.safety_score < prev_metrics.safety_score * 0.7:
            logger.warning("Sudden safety score drop detected")
            return True
        
        # Check for excessive code changes
        if metrics.code_change_percentage > 0.5:
            logger.warning("Excessive code changes detected")
            return True
        
        # Check for high risk level
        if metrics.risk_level.value >= RiskLevel.HIGH.value:
            logger.warning("High risk level detected")
            return True
        
        return False
    
    def rollback_to_checkpoint(self, checkpoint_id: str) -> bool:
        """
        Rollback to a specific checkpoint.
        
        This restores the system to the state captured in the checkpoint.
        """
        
        if checkpoint_id not in self.checkpoints:
            logger.error(f"Unknown checkpoint: {checkpoint_id}")
            return False
        
        checkpoint = self.checkpoints[checkpoint_id]
        
        # Verify checkpoint integrity
        if not checkpoint.verify_integrity():
            logger.error(f"Checkpoint integrity check failed: {checkpoint_id}")
            return False
        
        try:
            # Restore code files
            for file_path, content in checkpoint.code_snapshot.items():
                full_path = self.workspace_path / file_path
                full_path.parent.mkdir(parents=True, exist_ok=True)
                full_path.write_text(content)
                logger.info(f"Restored: {file_path}")
            
            # Verify safety core integrity
            if not self.safety_core.verify_integrity():
                logger.critical("Safety core integrity check failed after rollback")
                return False
            
            logger.info(f"Successfully rolled back to checkpoint: {checkpoint_id}")
            
            # Create a new checkpoint after rollback
            self.create_checkpoint(f"Post-rollback from {checkpoint_id}")
            
            return True
        
        except Exception as e:
            logger.error(f"Error during rollback: {e}")
            return False
    
    def rollback_to_last_safe_checkpoint(self) -> bool:
        """Rollback to the most recent safe checkpoint"""
        
        # Find most recent checkpoint with safe metrics
        safe_checkpoints = [
            cp for cp in self.checkpoints.values()
            if cp.metrics.risk_level.value <= RiskLevel.MEDIUM.value
            and cp.metrics.safety_score >= 0.8
        ]
        
        if not safe_checkpoints:
            logger.error("No safe checkpoints found")
            return False
        
        # Sort by timestamp, get most recent
        safe_checkpoints.sort(key=lambda cp: cp.timestamp, reverse=True)
        latest_safe = safe_checkpoints[0]
        
        logger.info(f"Rolling back to last safe checkpoint: {latest_safe.checkpoint_id}")
        
        return self.rollback_to_checkpoint(latest_safe.checkpoint_id)
    
    def get_evolution_report(self) -> Dict[str, Any]:
        """Get comprehensive evolution report"""
        
        if not self.metrics_history:
            current_metrics = self._capture_current_metrics()
        else:
            current_metrics = self.metrics_history[-1]
        
        return {
            'current_metrics': {
                'timestamp': current_metrics.timestamp.isoformat(),
                'recursion_depth': current_metrics.recursion_depth,
                'code_changes': current_metrics.code_changes_count,
                'code_change_pct': current_metrics.code_change_percentage,
                'performance_score': current_metrics.performance_score,
                'safety_score': current_metrics.safety_score,
                'risk_level': current_metrics.risk_level.name,
                'total_improvements': current_metrics.total_improvements,
                'success_rate': (
                    current_metrics.successful_improvements / current_metrics.total_improvements
                    if current_metrics.total_improvements > 0 else 0.0
                )
            },
            'checkpoints': {
                'total': len(self.checkpoints),
                'last_checkpoint': self.last_checkpoint_time.isoformat(),
                'safe_checkpoints': len([
                    cp for cp in self.checkpoints.values()
                    if cp.metrics.risk_level.value <= RiskLevel.MEDIUM.value
                ]),
                'recent': [
                    {
                        'id': cp.checkpoint_id,
                        'timestamp': cp.timestamp.isoformat(),
                        'description': cp.description,
                        'risk_level': cp.metrics.risk_level.name,
                        'safety_score': cp.metrics.safety_score
                    }
                    for cp in sorted(self.checkpoints.values(), key=lambda x: x.timestamp, reverse=True)[:5]
                ]
            },
            'metrics_history': [
                {
                    'timestamp': m.timestamp.isoformat(),
                    'performance': m.performance_score,
                    'safety': m.safety_score,
                    'risk': m.risk_level.name
                }
                for m in self.metrics_history[-20:]  # Last 20
            ],
            'safety_status': {
                'core_integrity': self.safety_core.verify_integrity(),
                'overall_risk': self.risk_matrix.get_overall_risk_level().name,
                'auto_rollback_enabled': self.auto_rollback_enabled
            }
        }


def rollback_to_checkpoint(workspace_path: str, checkpoint_id: str) -> bool:
    """
    Global function to rollback to a checkpoint.
    
    This is a convenience function for emergency rollbacks.
    """
    monitor = EvolutionMonitor(workspace_path)
    return monitor.rollback_to_checkpoint(checkpoint_id)
