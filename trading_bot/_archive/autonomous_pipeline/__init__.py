"""
Autonomous Discovery, Sandbox, Test, Approve, Deploy Pipeline

This module implements the complete workflow for:
1. Discovering new data sources and models
2. Sandboxing them for isolated testing
3. Running automated tests
4. Requesting human approval
5. Deploying to live production

Author: AlphaAlgo Trading System
Version: 1.0.0
"""

from .discovery_engine import (
    DataSourceDiscovery,
    ModelDiscovery,
    DiscoveryEngine,
    DiscoveredItem,
    DiscoveryType
)

from .sandbox_environment import (
    SandboxEnvironment,
    SandboxConfig,
    SandboxStatus,
    IsolatedTest
)

from .testing_framework import (
    AutomatedTester,
    TestResult,
    TestSuite,
    TestStatus
)

from .approval_system import (
    HumanApprovalSystem,
    ApprovalRequest,
    ApprovalStatus,
    ApprovalDecision
)

from .deployment_pipeline import (
    DeploymentPipeline,
    DeploymentStage,
    DeploymentStatus,
    RollbackManager
)

from .pipeline_orchestrator import (
    AutonomousPipelineOrchestrator,
    PipelineConfig,
    PipelineStatus,
    create_pipeline,
    quick_start
)

__all__ = [
    # Discovery
    'DataSourceDiscovery',
    'ModelDiscovery',
    'DiscoveryEngine',
    'DiscoveredItem',
    'DiscoveryType',
    
    # Sandbox
    'SandboxEnvironment',
    'SandboxConfig',
    'SandboxStatus',
    'IsolatedTest',
    
    # Testing
    'AutomatedTester',
    'TestResult',
    'TestSuite',
    'TestStatus',
    
    # Approval
    'HumanApprovalSystem',
    'ApprovalRequest',
    'ApprovalStatus',
    'ApprovalDecision',
    
    # Deployment
    'DeploymentPipeline',
    'DeploymentStage',
    'DeploymentStatus',
    'RollbackManager',
    
    # Orchestrator
    'AutonomousPipelineOrchestrator',
    'PipelineConfig',
    'PipelineStatus',
    'create_pipeline',
    'quick_start'
]
