"""
Deployment Pipeline - Safely deploys approved items to live production

Provides:
- Staged deployment (sandbox → staging → production)
- Rollback capability
- Health monitoring
- Gradual rollout
- Deployment validation

Author: AlphaAlgo Trading System
"""

import asyncio
import logging
import shutil
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional, Any
from pathlib import Path
import json

logger = logging.getLogger(__name__)


class DeploymentStage(Enum):
    """Stages of deployment"""
    SANDBOX = "sandbox"
    STAGING = "staging"
    CANARY = "canary"  # Small % of traffic
    PRODUCTION = "production"


class DeploymentStatus(Enum):
    """Status of deployment"""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    DEPLOYED = "deployed"
    FAILED = "failed"
    ROLLED_BACK = "rolled_back"
    PAUSED = "paused"


@dataclass
class DeploymentRecord:
    """Record of a deployment"""
    deployment_id: str
    item_name: str
    item_type: str
    
    # Stages
    current_stage: DeploymentStage
    completed_stages: List[DeploymentStage] = field(default_factory=list)
    
    # Status
    status: DeploymentStatus = DeploymentStatus.PENDING
    
    # Timing
    started_at: datetime = field(default_factory=datetime.now)
    completed_at: Optional[datetime] = None
    
    # Health
    health_checks_passed: int = 0
    health_checks_failed: int = 0
    error_count: int = 0
    
    # Rollback
    can_rollback: bool = True
    rollback_reason: Optional[str] = None
    
    # Metadata
    deployed_by: str = "autonomous_pipeline"
    approval_id: Optional[str] = None
    
    def to_dict(self) -> Dict:
        return {
            'deployment_id': self.deployment_id,
            'item_name': self.item_name,
            'item_type': self.item_type,
            'current_stage': self.current_stage.value,
            'completed_stages': [s.value for s in self.completed_stages],
            'status': self.status.value,
            'started_at': self.started_at.isoformat(),
            'completed_at': self.completed_at.isoformat() if self.completed_at else None,
            'health_checks_passed': self.health_checks_passed,
            'health_checks_failed': self.health_checks_failed,
            'error_count': self.error_count,
            'can_rollback': self.can_rollback,
            'rollback_reason': self.rollback_reason,
            'deployed_by': self.deployed_by,
            'approval_id': self.approval_id
        }


class RollbackManager:
    """Manages rollback of deployments"""
    
    def __init__(self, backup_dir: str = "deployment_backups"):
        self.backup_dir = Path(backup_dir)
        self.backup_dir.mkdir(exist_ok=True)
    
    def create_backup(self, item_name: str, source_path: Path) -> str:
        """Create backup before deployment"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_id = f"{item_name}_{timestamp}"
        backup_path = self.backup_dir / backup_id
        
        try:
            if source_path.is_file():
                backup_path.mkdir(exist_ok=True)
                shutil.copy2(source_path, backup_path / source_path.name)
            elif source_path.is_dir():
                shutil.copytree(source_path, backup_path)
            
            logger.info(f"Backup created: {backup_id}")
            return backup_id
            
        except Exception as e:
            logger.error(f"Failed to create backup: {e}")
            raise
    
    def rollback(self, backup_id: str, target_path: Path) -> bool:
        """Rollback to previous version"""
        backup_path = self.backup_dir / backup_id
        
        if not backup_path.exists():
            logger.error(f"Backup not found: {backup_id}")
            return False
        try:
        
            # Remove current version
            if target_path.exists():
                if target_path.is_file():
                    target_path.unlink()
                elif target_path.is_dir():
                    shutil.rmtree(target_path)
            
            # Restore backup
            if backup_path.is_dir():
                shutil.copytree(backup_path, target_path)
            else:
                shutil.copy2(backup_path, target_path)
            
            logger.info(f"Rollback successful: {backup_id}")
            return True
            
        except Exception as e:
            logger.error(f"Rollback failed: {e}")
            return False


class DeploymentPipeline:
    """Manages deployment pipeline"""
    
    def __init__(
        self,
        staging_dir: str = "staging",
        production_dir: str = "production",
        deployment_log: str = "deployments"
    ):
        self.staging_dir = Path(staging_dir)
        self.production_dir = Path(production_dir)
        self.deployment_log_dir = Path(deployment_log)
        
        # Create directories
        self.staging_dir.mkdir(exist_ok=True)
        self.production_dir.mkdir(exist_ok=True)
        self.deployment_log_dir.mkdir(exist_ok=True)
        
        self.rollback_manager = RollbackManager()
        self.active_deployments: Dict[str, DeploymentRecord] = {}
        self.deployment_history: List[DeploymentRecord] = []
    
    async def deploy(
        self,
        item_name: str,
        item_type: str,
        source_path: Path,
        approval_id: Optional[str] = None,
        gradual: bool = True
    ) -> DeploymentRecord:
        """Deploy item through pipeline"""
        
        deployment_id = f"deploy_{item_name}_{int(datetime.now().timestamp())}"
        
        record = DeploymentRecord(
            deployment_id=deployment_id,
            item_name=item_name,
            item_type=item_type,
            current_stage=DeploymentStage.SANDBOX,
            approval_id=approval_id
        )
        
        self.active_deployments[deployment_id] = record
        
        logger.info(f"Starting deployment: {deployment_id}")
        
        try:
            # Stage 1: Staging deployment
            record.status = DeploymentStatus.IN_PROGRESS
            record.current_stage = DeploymentStage.STAGING
            
            success = await self._deploy_to_staging(record, source_path)
            if not success:
                raise Exception("Staging deployment failed")
            
            record.completed_stages.append(DeploymentStage.STAGING)
            
            # Health check
            if not await self._health_check(record):
                raise Exception("Staging health check failed")
            
            # Stage 2: Canary deployment (if gradual)
            if gradual:
                record.current_stage = DeploymentStage.CANARY
                
                success = await self._deploy_canary(record)
                if not success:
                    raise Exception("Canary deployment failed")
                
                record.completed_stages.append(DeploymentStage.CANARY)
                
                # Monitor canary
                if not await self._monitor_canary(record):
                    raise Exception("Canary monitoring failed")
            
            # Stage 3: Production deployment
            record.current_stage = DeploymentStage.PRODUCTION
            
            # Create backup
            backup_id = self.rollback_manager.create_backup(
                item_name,
                self.production_dir / item_name
            )
            
            success = await self._deploy_to_production(record, source_path)
            if not success:
                raise Exception("Production deployment failed")
            
            record.completed_stages.append(DeploymentStage.PRODUCTION)
            
            # Final health check
            if not await self._health_check(record):
                # Rollback
                logger.warning("Production health check failed, rolling back")
                self.rollback_manager.rollback(backup_id, self.production_dir / item_name)
                raise Exception("Production health check failed")
            
            # Success
            record.status = DeploymentStatus.DEPLOYED
            record.completed_at = datetime.now()
            
            logger.info(f"Deployment successful: {deployment_id}")
            
        except Exception as e:
            record.status = DeploymentStatus.FAILED
            record.error_count += 1
            record.rollback_reason = str(e)
            logger.error(f"Deployment failed: {deployment_id} - {e}")
        
        finally:
            # Move to history
            self.active_deployments.pop(deployment_id, None)
            self.deployment_history.append(record)
            self._save_deployment_record(record)
        
        return record
    
    async def _deploy_to_staging(self, record: DeploymentRecord, source_path: Path) -> bool:
        """Deploy to staging environment"""
        try:
            target_path = self.staging_dir / record.item_name
            
            # Copy files
            if source_path.is_file():
                target_path.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(source_path, target_path)
            elif source_path.is_dir():
                if target_path.exists():
                    shutil.rmtree(target_path)
                shutil.copytree(source_path, target_path)
            
            logger.info(f"Deployed to staging: {record.item_name}")
            return True
            
        except Exception as e:
            logger.error(f"Staging deployment failed: {e}")
            return False
    
    async def _deploy_canary(self, record: DeploymentRecord) -> bool:
        """Deploy canary (small percentage)"""
        try:
            # In production, this would route small % of traffic
            # For now, just log
            logger.info(f"Canary deployed: {record.item_name} (10% traffic)")
            await asyncio.sleep(1)  # Simulate deployment
            return True
            
        except Exception as e:
            logger.error(f"Canary deployment failed: {e}")
            return False
    
    async def _monitor_canary(self, record: DeploymentRecord, duration: int = 60) -> bool:
        """Monitor canary deployment"""
        try:
            logger.info(f"Monitoring canary for {duration}s...")
            
            # In production, monitor metrics, errors, etc.
            # For now, simulate monitoring
            await asyncio.sleep(min(duration, 5))
            
            # Check for issues
            if record.error_count > 0:
                logger.warning("Canary has errors")
                return False
            
            logger.info("Canary monitoring passed")
            return True
            
        except Exception as e:
            logger.error(f"Canary monitoring failed: {e}")
            return False
    
    async def _deploy_to_production(self, record: DeploymentRecord, source_path: Path) -> bool:
        """Deploy to production environment"""
        try:
            target_path = self.production_dir / record.item_name
            
            # Copy files
            if source_path.is_file():
                target_path.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(source_path, target_path)
            elif source_path.is_dir():
                if target_path.exists():
                    shutil.rmtree(target_path)
                shutil.copytree(source_path, target_path)
            
            logger.info(f"Deployed to production: {record.item_name}")
            return True
            
        except Exception as e:
            logger.error(f"Production deployment failed: {e}")
            return False
    
    async def _health_check(self, record: DeploymentRecord) -> bool:
        """Perform health check"""
        try:
            # In production, check:
            # - Service is running
            # - No errors in logs
            # - Metrics are normal
            # - Integration tests pass
            
            # For now, simulate
            await asyncio.sleep(1)
            
            record.health_checks_passed += 1
            logger.info(f"Health check passed: {record.item_name}")
            return True
            
        except Exception as e:
            record.health_checks_failed += 1
            logger.error(f"Health check failed: {e}")
            return False
    
    def rollback_deployment(self, deployment_id: str, reason: str) -> bool:
        """Rollback a deployment"""
        record = next(
            (r for r in self.deployment_history if r.deployment_id == deployment_id),
            None
        )
        
        if not record:
            logger.error(f"Deployment not found: {deployment_id}")
            return False
        
        if not record.can_rollback:
            logger.error(f"Deployment cannot be rolled back: {deployment_id}")
            return False
        try:
        
            # Find backup
            backups = list(self.rollback_manager.backup_dir.glob(f"{record.item_name}_*"))
            if not backups:
                logger.error("No backup found for rollback")
                return False
            
            # Use most recent backup
            latest_backup = max(backups, key=lambda p: p.stat().st_mtime)
            
            # Rollback
            target_path = self.production_dir / record.item_name
            success = self.rollback_manager.rollback(latest_backup.name, target_path)
            
            if success:
                record.status = DeploymentStatus.ROLLED_BACK
                record.rollback_reason = reason
                self._save_deployment_record(record)
                logger.info(f"Rollback successful: {deployment_id}")
            
            return success
            
        except Exception as e:
            logger.error(f"Rollback failed: {e}")
            return False
    
    def get_deployment_status(self, deployment_id: str) -> Optional[DeploymentRecord]:
        """Get deployment status"""
        # Check active
        if deployment_id in self.active_deployments:
            return self.active_deployments[deployment_id]
        
        # Check history
        return next(
            (r for r in self.deployment_history if r.deployment_id == deployment_id),
            None
        )
    
    def get_active_deployments(self) -> List[DeploymentRecord]:
        """Get all active deployments"""
        return list(self.active_deployments.values())
    
    def get_deployment_history(self, limit: int = 100) -> List[DeploymentRecord]:
        """Get deployment history"""
        return self.deployment_history[-limit:]
    
    def _save_deployment_record(self, record: DeploymentRecord):
        """Save deployment record"""
        filepath = self.deployment_log_dir / f"{record.deployment_id}.json"
        with open(filepath, 'w') as f:
            json.dump(record.to_dict(), f, indent=2)
    
    def get_deployment_stats(self) -> Dict[str, Any]:
        """Get deployment statistics"""
        total = len(self.deployment_history)
        successful = sum(1 for r in self.deployment_history if r.status == DeploymentStatus.DEPLOYED)
        failed = sum(1 for r in self.deployment_history if r.status == DeploymentStatus.FAILED)
        rolled_back = sum(1 for r in self.deployment_history if r.status == DeploymentStatus.ROLLED_BACK)
        
        return {
            'total_deployments': total,
            'successful': successful,
            'failed': failed,
            'rolled_back': rolled_back,
            'success_rate': successful / total if total > 0 else 0.0,
            'active_deployments': len(self.active_deployments)
        }
