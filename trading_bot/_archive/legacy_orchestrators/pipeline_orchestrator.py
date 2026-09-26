"""
Autonomous Pipeline Orchestrator - Master controller for the complete workflow

Orchestrates the complete autonomous workflow:
1. Discovery → 2. Sandbox → 3. Test → 4. Approve → 5. Deploy

This is the ONE system that manages the entire lifecycle of new data sources and models.

Author: AlphaAlgo Trading System
"""

import asyncio
import logging
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional, Any
from pathlib import Path
import json

from .discovery_engine import DiscoveryEngine, DiscoveredItem, DiscoveryType
from .sandbox_environment import SandboxEnvironment, SandboxConfig, IsolatedTest
from .testing_framework import AutomatedTester, TestSuite, TestStatus
from .approval_system import HumanApprovalSystem, ApprovalRequest, ApprovalStatus
from .deployment_pipeline import DeploymentPipeline, DeploymentRecord, DeploymentStatus

logger = logging.getLogger(__name__)


class PipelineStatus(Enum):
    """Status of pipeline"""
    IDLE = "idle"
    DISCOVERING = "discovering"
    SANDBOXING = "sandboxing"
    TESTING = "testing"
    AWAITING_APPROVAL = "awaiting_approval"
    DEPLOYING = "deploying"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class PipelineConfig:
    """Configuration for autonomous pipeline"""
    # Discovery
    enable_data_discovery: bool = True
    enable_model_discovery: bool = True
    
    # Sandbox
    sandbox_config: Optional[SandboxConfig] = None
    
    # Testing
    min_test_score: float = 0.7  # Minimum score to pass
    
    # Approval
    require_human_approval: bool = True
    auto_approve_low_risk: bool = False  # Auto-approve low-risk items
    
    # Deployment
    gradual_deployment: bool = True
    enable_rollback: bool = True
    
    # Paths
    pipeline_data_dir: str = "autonomous_pipeline_data"
    
    # Scheduling
    discovery_interval_hours: int = 24  # Run discovery every 24 hours
    auto_run: bool = False  # Automatically run pipeline


@dataclass
class PipelineRun:
    """Record of a pipeline run"""
    run_id: str
    start_time: datetime
    end_time: Optional[datetime] = None
    
    # Results
    items_discovered: int = 0
    items_sandboxed: int = 0
    items_tested: int = 0
    items_approved: int = 0
    items_deployed: int = 0
    items_failed: int = 0
    
    # Status
    status: PipelineStatus = PipelineStatus.IDLE
    
    # Details
    discovered_items: List[str] = field(default_factory=list)
    approved_items: List[str] = field(default_factory=list)
    deployed_items: List[str] = field(default_factory=list)
    failed_items: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict:
        return {
            'run_id': self.run_id,
            'start_time': self.start_time.isoformat(),
            'end_time': self.end_time.isoformat() if self.end_time else None,
            'items_discovered': self.items_discovered,
            'items_sandboxed': self.items_sandboxed,
            'items_tested': self.items_tested,
            'items_approved': self.items_approved,
            'items_deployed': self.items_deployed,
            'items_failed': self.items_failed,
            'status': self.status.value,
            'discovered_items': self.discovered_items,
            'approved_items': self.approved_items,
            'deployed_items': self.deployed_items,
            'failed_items': self.failed_items
        }


class AutonomousPipelineOrchestrator:
    """
    Master orchestrator for autonomous discovery, testing, approval, and deployment.
    
    This is THE ONE system that:
    1. Discovers new high-quality data sources and models
    2. Sandboxes them for isolated testing
    3. Runs comprehensive automated tests
    4. Requests human approval
    5. Deploys to live production
    
    "Find it. Test it. Approve it. Deploy it."
    """
    
    def __init__(self, config: Optional[PipelineConfig] = None):
        self.config = config or PipelineConfig()
        
        # Initialize components
        self.discovery_engine = DiscoveryEngine()
        self.sandbox = SandboxEnvironment(self.config.sandbox_config or SandboxConfig())
        self.tester = AutomatedTester()
        self.approval_system = HumanApprovalSystem()
        self.deployment_pipeline = DeploymentPipeline()
        
        # State
        self.status = PipelineStatus.IDLE
        self.current_run: Optional[PipelineRun] = None
        self.run_history: List[PipelineRun] = []
        
        # Data directory
        self.data_dir = Path(self.config.pipeline_data_dir)
        self.data_dir.mkdir(exist_ok=True)
        
        logger.info("Autonomous Pipeline Orchestrator initialized")
    
    async def run_pipeline(self) -> PipelineRun:
        """Run complete autonomous pipeline"""
        
        run_id = f"pipeline_run_{int(datetime.now().timestamp())}"
        run = PipelineRun(
            run_id=run_id,
            start_time=datetime.now()
        )
        
        self.current_run = run
        
        logger.info("=" * 80)
        logger.info("AUTONOMOUS PIPELINE - STARTING")
        logger.info("=" * 80)
        
        try:
            # Step 1: Discovery
            run.status = PipelineStatus.DISCOVERING
            discovered_items = await self._run_discovery()
            run.items_discovered = len(discovered_items)
            run.discovered_items = [item.name for item in discovered_items]
            
            logger.info(f"Discovery complete: {len(discovered_items)} items found")
            
            # Step 2: Sandbox & Test
            run.status = PipelineStatus.SANDBOXING
            tested_items = await self._run_sandbox_and_test(discovered_items)
            run.items_sandboxed = len(tested_items)
            run.items_tested = len(tested_items)
            
            logger.info(f"Testing complete: {len(tested_items)} items tested")
            
            # Step 3: Request Approval
            run.status = PipelineStatus.AWAITING_APPROVAL
            approval_requests = await self._request_approvals(tested_items)
            
            logger.info(f"Approval requests created: {len(approval_requests)}")
            
            # Step 4: Wait for approvals (if required)
            if self.config.require_human_approval:
                logger.info("Waiting for human approval...")
                logger.info("Pipeline paused. Review approval requests and approve/reject.")
                logger.info(f"Approval files saved in: {self.approval_system.approval_dir}")
                
                # In production, this would wait for approvals
                # For now, we'll just note that approvals are pending
                run.status = PipelineStatus.AWAITING_APPROVAL
            else:
                # Auto-approve all
                for request in approval_requests:
                    self.approval_system.approve(request.request_id, approver="auto")
            
            # Step 5: Deploy approved items
            approved_items = await self._get_approved_items()
            
            if approved_items:
                run.status = PipelineStatus.DEPLOYING
                deployed = await self._deploy_items(approved_items)
                run.items_deployed = len(deployed)
                run.deployed_items = [item.name for item in deployed]
                
                logger.info(f"Deployment complete: {len(deployed)} items deployed")
            
            # Complete
            run.status = PipelineStatus.COMPLETED
            run.end_time = datetime.now()
            
            logger.info("=" * 80)
            logger.info("AUTONOMOUS PIPELINE - COMPLETED")
            logger.info(f"Discovered: {run.items_discovered}")
            logger.info(f"Tested: {run.items_tested}")
            logger.info(f"Approved: {run.items_approved}")
            logger.info(f"Deployed: {run.items_deployed}")
            logger.info("=" * 80)
            
        except Exception as e:
            run.status = PipelineStatus.FAILED
            run.end_time = datetime.now()
            logger.error(f"Pipeline failed: {e}")
        
        finally:
            self.run_history.append(run)
            self._save_run(run)
            self.current_run = None
        
        return run
    
    async def _run_discovery(self) -> List[DiscoveredItem]:
        """Run discovery phase"""
        logger.info("Phase 1: DISCOVERY")
        logger.info("-" * 80)
        
        # Discover everything
        items = await self.discovery_engine.discover_everything()
        
        # Filter by quality
        high_quality = [item for item in items if item.quality_score >= 0.6]
        
        logger.info(f"Found {len(items)} items, {len(high_quality)} high-quality")
        
        return high_quality
    
    async def _run_sandbox_and_test(self, items: List[DiscoveredItem]) -> List[tuple]:
        """Run sandbox and testing phase"""
        logger.info("\nPhase 2: SANDBOX & TEST")
        logger.info("-" * 80)
        
        tested_items = []
        
        for item in items[:10]:  # Limit to top 10 for demo
            try:
                logger.info(f"Testing: {item.name}")
                
                # Sandbox test
                if item.item_type in [DiscoveryType.STOCK_DATA, DiscoveryType.FOREX_DATA, 
                                      DiscoveryType.CRYPTO_DATA, DiscoveryType.SENTIMENT_DATA]:
                    sandbox_result = await self.sandbox.test_data_source(
                        item.name,
                        item.source
                    )
                else:
                    sandbox_result = await self.sandbox.test_model(
                        item.name,
                        item.source
                    )
                
                # Automated tests
                if item.item_type in [DiscoveryType.STOCK_DATA, DiscoveryType.FOREX_DATA,
                                      DiscoveryType.CRYPTO_DATA]:
                    test_suite = await self.tester.test_data_source(item.name, None)
                else:
                    test_suite = await self.tester.test_model(item.name, None)
                
                # Check if passed
                if test_suite.overall_score >= self.config.min_test_score:
                    tested_items.append((item, sandbox_result, test_suite))
                    logger.info(f"  ✓ Passed: {item.name} (score: {test_suite.overall_score:.2f})")
                else:
                    logger.info(f"  ✗ Failed: {item.name} (score: {test_suite.overall_score:.2f})")
                
            except Exception as e:
                logger.error(f"  ✗ Error testing {item.name}: {e}")
        
        return tested_items
    
    async def _request_approvals(self, tested_items: List[tuple]) -> List[ApprovalRequest]:
        """Request human approvals"""
        logger.info("\nPhase 3: REQUEST APPROVAL")
        logger.info("-" * 80)
        
        approval_requests = []
        
        for item, sandbox_result, test_suite in tested_items:
            try:
                # Create approval request
                request = self.approval_system.create_request(
                    item_name=item.name,
                    item_type=item.item_type.value,
                    test_results=test_suite.to_dict(),
                    discovered_item=item.to_dict()
                )
                
                approval_requests.append(request)
                logger.info(f"  Approval requested: {item.name}")
                
                # Auto-approve low-risk if enabled
                if self.config.auto_approve_low_risk and request.risk_level == "low":
                    self.approval_system.approve(request.request_id, approver="auto_low_risk")
                    logger.info(f"    Auto-approved (low risk)")
                
            except Exception as e:
                logger.error(f"  Error creating approval for {item.name}: {e}")
        
        return approval_requests
    
    async def _get_approved_items(self) -> List[tuple]:
        """Get approved items ready for deployment"""
        approved = []
        
        # Get all approved requests
        for request in self.approval_system.completed_requests.values():
            if request.status == ApprovalStatus.APPROVED:
                # Find corresponding item
                # In production, would retrieve full item details
                approved.append((request.item_name, request.item_type))
        
        return approved
    
    async def _deploy_items(self, approved_items: List[tuple]) -> List[DeploymentRecord]:
        """Deploy approved items"""
        logger.info("\nPhase 4: DEPLOYMENT")
        logger.info("-" * 80)
        
        deployed = []
        
        for item_name, item_type in approved_items:
            try:
                logger.info(f"Deploying: {item_name}")
                
                # In production, would get actual source path
                source_path = Path(f"temp/{item_name}")
                
                # Deploy
                record = await self.deployment_pipeline.deploy(
                    item_name=item_name,
                    item_type=item_type,
                    source_path=source_path,
                    gradual=self.config.gradual_deployment
                )
                
                if record.status == DeploymentStatus.DEPLOYED:
                    deployed.append(record)
                    logger.info(f"  ✓ Deployed: {item_name}")
                else:
                    logger.info(f"  ✗ Failed: {item_name}")
                
            except Exception as e:
                logger.error(f"  ✗ Error deploying {item_name}: {e}")
        
        return deployed
    
    def approve_item(self, request_id: str, approver: str = "human", comments: Optional[str] = None) -> bool:
        """Approve an item for deployment"""
        return self.approval_system.approve(request_id, approver, comments)
    
    def reject_item(self, request_id: str, approver: str = "human", comments: Optional[str] = None) -> bool:
        """Reject an item"""
        return self.approval_system.reject(request_id, approver, comments)
    
    def get_pending_approvals(self) -> List[ApprovalRequest]:
        """Get all pending approval requests"""
        return self.approval_system.get_pending_requests()
    
    def get_pipeline_status(self) -> Dict[str, Any]:
        """Get current pipeline status"""
        return {
            'status': self.status.value,
            'current_run': self.current_run.to_dict() if self.current_run else None,
            'total_runs': len(self.run_history),
            'pending_approvals': len(self.approval_system.get_pending_requests()),
            'active_deployments': len(self.deployment_pipeline.get_active_deployments())
        }
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get pipeline statistics"""
        total_runs = len(self.run_history)
        
        if total_runs == 0:
            return {
                'total_runs': 0,
                'total_discovered': 0,
                'total_deployed': 0,
                'success_rate': 0.0
            }
        
        total_discovered = sum(run.items_discovered for run in self.run_history)
        total_deployed = sum(run.items_deployed for run in self.run_history)
        
        return {
            'total_runs': total_runs,
            'total_discovered': total_discovered,
            'total_tested': sum(run.items_tested for run in self.run_history),
            'total_approved': sum(run.items_approved for run in self.run_history),
            'total_deployed': total_deployed,
            'total_failed': sum(run.items_failed for run in self.run_history),
            'success_rate': total_deployed / total_discovered if total_discovered > 0 else 0.0,
            'approval_stats': self.approval_system.get_approval_stats(),
            'deployment_stats': self.deployment_pipeline.get_deployment_stats()
        }
    
    def _save_run(self, run: PipelineRun):
        """Save pipeline run"""
        filepath = self.data_dir / f"{run.run_id}.json"
        with open(filepath, 'w') as f:
            json.dump(run.to_dict(), f, indent=2)
    
    async def cleanup(self):
        """Cleanup resources"""
        await self.sandbox.cleanup()


# Helper functions
async def create_pipeline(config: Optional[PipelineConfig] = None) -> AutonomousPipelineOrchestrator:
    """Create autonomous pipeline"""
    return AutonomousPipelineOrchestrator(config)


async def quick_start() -> AutonomousPipelineOrchestrator:
    """Quick start with default configuration"""
    config = PipelineConfig(
        require_human_approval=True,
        auto_approve_low_risk=False,
        gradual_deployment=True
    )
    
    pipeline = AutonomousPipelineOrchestrator(config)
    
    logger.info("Autonomous Pipeline ready!")
    logger.info("Run: await pipeline.run_pipeline()")
    
    return pipeline
