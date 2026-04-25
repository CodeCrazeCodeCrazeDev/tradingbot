"""
Meta-Orchestrator Agent - Master Controller with Critical Rules Enforcement
============================================================================

The command brain that coordinates all agents with strict rule enforcement.

CRITICAL RULES ENFORCED:
1. Agents NEVER access raw data directly (only through Data Fusion Agent)
2. No agent can execute without orchestrator approval
3. All experiments must be logged
4. Simulation happens BEFORE execution
5. Execution is the LAST step, not the first
"""

import asyncio
import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional, Set
import uuid

logger = logging.getLogger(__name__)


class AgentStatus(Enum):
    """Agent execution status"""
    IDLE = "idle"
    WAITING_APPROVAL = "waiting_approval"
    APPROVED = "approved"
    EXECUTING = "executing"
    COMPLETED = "completed"
    FAILED = "failed"
    BLOCKED = "blocked"


class WorkflowStage(Enum):
    """Workflow execution stages (MUST be sequential)"""
    DATA_FUSION = 1          # Perception layer
    ONTOLOGY_UPDATE = 2      # Knowledge graph enrichment
    INTELLIGENCE = 3         # LLM reasoning
    STRATEGY_RESEARCH = 4    # Bull/Bear thesis generation
    SIMULATION = 5           # World-model scenarios (REQUIRED before execution)
    RISK_EVALUATION = 6      # VaR, drawdown, correlation checks
    EXECUTION = 7            # LAST STEP - order management


@dataclass
class AgentRequest:
    """Request from an agent to the orchestrator"""
    request_id: str
    agent_name: str
    timestamp: datetime
    request_type: str
    payload: Dict[str, Any]
    requires_approval: bool = True
    status: AgentStatus = AgentStatus.WAITING_APPROVAL
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'request_id': self.request_id,
            'agent_name': self.agent_name,
            'timestamp': self.timestamp.isoformat(),
            'request_type': self.request_type,
            'payload': self.payload,
            'requires_approval': self.requires_approval,
            'status': self.status.value,
        }


@dataclass
class WorkflowExecution:
    """A complete workflow execution"""
    execution_id: str
    started_at: datetime
    current_stage: WorkflowStage
    stage_results: Dict[str, Any] = field(default_factory=dict)
    completed_stages: Set[WorkflowStage] = field(default_factory=set)
    is_simulation_complete: bool = False
    is_approved_for_execution: bool = False
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'execution_id': self.execution_id,
            'started_at': self.started_at.isoformat(),
            'current_stage': self.current_stage.name,
            'completed_stages': [s.name for s in self.completed_stages],
            'is_simulation_complete': self.is_simulation_complete,
            'is_approved_for_execution': self.is_approved_for_execution,
        }


class CriticalRulesEnforcer:
    """
    Enforces critical system rules.
    
    If these rules are violated, the system FAILS.
    """
    
    def __init__(self):
        self.violations: List[Dict[str, Any]] = []
        self.rules_enabled = True
    
    def check_rule_1_no_direct_data_access(
        self,
        agent_name: str,
        action: str,
    ) -> bool:
        """Rule 1: Agents NEVER access raw data directly"""
        if agent_name == "DataFusionAgent":
            return True  # Only Data Fusion Agent can access raw data
        
        forbidden_actions = ['read_raw_data', 'access_market_feed', 'query_database']
        
        if action in forbidden_actions:
            self._record_violation(
                rule_number=1,
                rule_text="Agents NEVER access raw data directly",
                agent_name=agent_name,
                violation=f"Agent {agent_name} attempted direct data access: {action}",
            )
            return False
        
        return True
    
    def check_rule_2_orchestrator_approval(
        self,
        agent_name: str,
        action: str,
        has_approval: bool,
    ) -> bool:
        """Rule 2: No agent can execute without orchestrator approval"""
        critical_actions = ['execute_trade', 'place_order', 'modify_position', 'deploy_strategy']
        
        if action in critical_actions and not has_approval:
            self._record_violation(
                rule_number=2,
                rule_text="No agent can execute without orchestrator approval",
                agent_name=agent_name,
                violation=f"Agent {agent_name} attempted {action} without approval",
            )
            return False
        
        return True
    
    def check_rule_3_experiment_logging(
        self,
        experiment_id: Optional[str],
        action: str,
    ) -> bool:
        """Rule 3: All experiments must be logged"""
        experiment_actions = ['run_simulation', 'test_strategy', 'backtest', 'optimize']
        
        if action in experiment_actions and not experiment_id:
            self._record_violation(
                rule_number=3,
                rule_text="All experiments must be logged",
                agent_name="Unknown",
                violation=f"Experiment action {action} without experiment_id",
            )
            return False
        
        return True
    
    def check_rule_4_simulation_before_execution(
        self,
        workflow: WorkflowExecution,
        requesting_execution: bool,
    ) -> bool:
        """Rule 4: Simulation happens BEFORE execution"""
        if requesting_execution and not workflow.is_simulation_complete:
            self._record_violation(
                rule_number=4,
                rule_text="Simulation happens BEFORE execution",
                agent_name="ExecutionAgent",
                violation="Execution requested without completing simulation",
            )
            return False
        
        return True
    
    def check_rule_5_execution_is_last(
        self,
        current_stage: WorkflowStage,
        requesting_stage: WorkflowStage,
    ) -> bool:
        """Rule 5: Execution is the LAST step, not the first"""
        if requesting_stage == WorkflowStage.EXECUTION:
            required_stages = {
                WorkflowStage.DATA_FUSION,
                WorkflowStage.ONTOLOGY_UPDATE,
                WorkflowStage.SIMULATION,
                WorkflowStage.RISK_EVALUATION,
            }
            
            # Check if we're trying to skip to execution
            if current_stage.value < WorkflowStage.RISK_EVALUATION.value:
                self._record_violation(
                    rule_number=5,
                    rule_text="Execution is the LAST step, not the first",
                    agent_name="ExecutionAgent",
                    violation=f"Execution requested at stage {current_stage.name}, must complete all prior stages",
                )
                return False
        
        return True
    
    def _record_violation(
        self,
        rule_number: int,
        rule_text: str,
        agent_name: str,
        violation: str,
    ):
        """Record a rule violation"""
        violation_record = {
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'rule_number': rule_number,
            'rule_text': rule_text,
            'agent_name': agent_name,
            'violation': violation,
        }
        
        self.violations.append(violation_record)
        logger.critical(f"CRITICAL RULE VIOLATION #{rule_number}: {violation}")
    
    def get_violations(self) -> List[Dict[str, Any]]:
        """Get all recorded violations"""
        return self.violations
    
    def has_violations(self) -> bool:
        """Check if there are any violations"""
        return len(self.violations) > 0


class MetaOrchestrator:
    """
    Meta-Orchestrator Agent - The Command Brain
    
    Responsibilities:
    - Coordinate all agents
    - Enforce critical rules
    - Manage workflow stages
    - Approve/reject agent requests
    - Ensure proper execution order
    """
    
    def __init__(self, auto_approve_simulations: bool = True):
        self.orchestrator_id = f"META-{uuid.uuid4().hex[:8]}"
        self.auto_approve_simulations = auto_approve_simulations
        
        # Critical rules enforcer
        self.rules_enforcer = CriticalRulesEnforcer()
        
        # Agent registry
        self.registered_agents: Dict[str, Any] = {}
        
        # Request queue
        self.pending_requests: List[AgentRequest] = []
        self.approved_requests: List[AgentRequest] = []
        self.rejected_requests: List[AgentRequest] = []
        
        # Workflow tracking
        self.active_workflows: Dict[str, WorkflowExecution] = {}
        self.workflow_history: List[WorkflowExecution] = []
        
        # Metrics
        self.total_requests = 0
        self.total_approvals = 0
        self.total_rejections = 0
        
        logger.info(f"MetaOrchestrator initialized: {self.orchestrator_id}")
    
    def register_agent(self, agent_name: str, agent_instance: Any):
        """Register an agent with the orchestrator"""
        self.registered_agents[agent_name] = agent_instance
        logger.info(f"Registered agent: {agent_name}")
    
    async def submit_request(
        self,
        agent_name: str,
        request_type: str,
        payload: Dict[str, Any],
        requires_approval: bool = True,
    ) -> AgentRequest:
        """
        Submit a request from an agent to the orchestrator.
        
        This is the ONLY way agents should request actions.
        """
        # Validate agent is registered
        if agent_name not in self.registered_agents:
            raise ValueError(f"Agent not registered: {agent_name}")
        
        # Create request
        request = AgentRequest(
            request_id=f"REQ-{uuid.uuid4().hex[:8]}",
            agent_name=agent_name,
            timestamp=datetime.now(timezone.utc),
            request_type=request_type,
            payload=payload,
            requires_approval=requires_approval,
        )
        
        self.total_requests += 1
        
        # Check critical rules
        if not self._validate_request(request):
            request.status = AgentStatus.BLOCKED
            self.rejected_requests.append(request)
            self.total_rejections += 1
            return request
        
        # Auto-approve certain requests
        if not requires_approval or self._should_auto_approve(request):
            request.status = AgentStatus.APPROVED
            self.approved_requests.append(request)
            self.total_approvals += 1
        else:
            self.pending_requests.append(request)
        
        return request
    
    def _validate_request(self, request: AgentRequest) -> bool:
        """Validate request against critical rules"""
        agent_name = request.agent_name
        action = request.request_type
        payload = request.payload
        
        # Rule 1: No direct data access
        if not self.rules_enforcer.check_rule_1_no_direct_data_access(agent_name, action):
            return False
        
        # Rule 2: Orchestrator approval
        has_approval = request.status == AgentStatus.APPROVED
        if not self.rules_enforcer.check_rule_2_orchestrator_approval(agent_name, action, has_approval):
            return False
        
        # Rule 3: Experiment logging
        experiment_id = payload.get('experiment_id')
        if not self.rules_enforcer.check_rule_3_experiment_logging(experiment_id, action):
            return False
        
        return True
    
    def _should_auto_approve(self, request: AgentRequest) -> bool:
        """Determine if request should be auto-approved"""
        # Auto-approve data fusion and ontology updates
        if request.agent_name in ['DataFusionAgent', 'OntologyAgent']:
            return True
        
        # Auto-approve simulations
        if self.auto_approve_simulations and request.request_type in ['run_simulation', 'scenario_analysis']:
            return True
        
        # Auto-approve intelligence/research (non-execution)
        if request.agent_name in ['IntelligenceAgent', 'StrategyAgent'] and 'execute' not in request.request_type:
            return True
        
        return False
    
    async def approve_request(self, request_id: str) -> Dict[str, Any]:
        """Manually approve a pending request"""
        for request in self.pending_requests:
            if request.request_id == request_id:
                request.status = AgentStatus.APPROVED
                self.pending_requests.remove(request)
                self.approved_requests.append(request)
                self.total_approvals += 1
                
                logger.info(f"Approved request: {request_id} from {request.agent_name}")
                
                return {'status': 'approved', 'request': request.to_dict()}
        
        return {'status': 'error', 'message': 'Request not found'}
    
    async def reject_request(self, request_id: str, reason: str = "") -> Dict[str, Any]:
        """Reject a pending request"""
        for request in self.pending_requests:
            if request.request_id == request_id:
                request.status = AgentStatus.BLOCKED
                self.pending_requests.remove(request)
                self.rejected_requests.append(request)
                self.total_rejections += 1
                
                logger.info(f"Rejected request: {request_id} - {reason}")
                
                return {'status': 'rejected', 'reason': reason}
        
        return {'status': 'error', 'message': 'Request not found'}
    
    async def start_workflow(self) -> WorkflowExecution:
        """Start a new workflow execution"""
        workflow = WorkflowExecution(
            execution_id=f"WF-{uuid.uuid4().hex[:8]}",
            started_at=datetime.now(timezone.utc),
            current_stage=WorkflowStage.DATA_FUSION,
        )
        
        self.active_workflows[workflow.execution_id] = workflow
        
        logger.info(f"Started workflow: {workflow.execution_id}")
        
        return workflow
    
    async def advance_workflow_stage(
        self,
        workflow_id: str,
        stage_result: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Advance workflow to next stage"""
        workflow = self.active_workflows.get(workflow_id)
        if not workflow:
            return {'status': 'error', 'message': 'Workflow not found'}
        
        # Mark current stage as complete
        workflow.completed_stages.add(workflow.current_stage)
        workflow.stage_results[workflow.current_stage.name] = stage_result
        
        # Check if simulation is complete
        if workflow.current_stage == WorkflowStage.SIMULATION:
            workflow.is_simulation_complete = True
        
        # Advance to next stage
        current_value = workflow.current_stage.value
        next_stages = [s for s in WorkflowStage if s.value == current_value + 1]
        
        if next_stages:
            next_stage = next_stages[0]
            
            # Rule 5: Execution is last
            if not self.rules_enforcer.check_rule_5_execution_is_last(workflow.current_stage, next_stage):
                return {'status': 'blocked', 'message': 'Cannot skip to execution'}
            
            workflow.current_stage = next_stage
            
            logger.info(f"Workflow {workflow_id} advanced to {next_stage.name}")
            
            return {
                'status': 'advanced',
                'current_stage': next_stage.name,
                'workflow': workflow.to_dict(),
            }
        else:
            # Workflow complete
            self.workflow_history.append(workflow)
            del self.active_workflows[workflow_id]
            
            return {'status': 'completed', 'workflow': workflow.to_dict()}
    
    async def request_execution_approval(
        self,
        workflow_id: str,
        execution_plan: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Request approval for execution (LAST STEP).
        
        This enforces Rule 4 and Rule 5.
        """
        workflow = self.active_workflows.get(workflow_id)
        if not workflow:
            return {'status': 'error', 'message': 'Workflow not found'}
        
        # Rule 4: Simulation must be complete
        if not self.rules_enforcer.check_rule_4_simulation_before_execution(workflow, True):
            return {
                'status': 'blocked',
                'message': 'Simulation must be completed before execution',
                'violations': self.rules_enforcer.get_violations(),
            }
        
        # Rule 5: Must be at execution stage
        if workflow.current_stage != WorkflowStage.EXECUTION:
            return {
                'status': 'blocked',
                'message': f'Must complete all stages. Current: {workflow.current_stage.name}',
            }
        
        # Create execution request
        request = await self.submit_request(
            agent_name='ExecutionAgent',
            request_type='execute_trade',
            payload=execution_plan,
            requires_approval=True,
        )
        
        return {
            'status': 'pending_approval',
            'request_id': request.request_id,
            'message': 'Execution request submitted for approval',
        }
    
    def get_pending_approvals(self) -> List[Dict[str, Any]]:
        """Get all pending approval requests"""
        return [r.to_dict() for r in self.pending_requests]
    
    def get_rule_violations(self) -> List[Dict[str, Any]]:
        """Get all critical rule violations"""
        return self.rules_enforcer.get_violations()
    
    def get_status(self) -> Dict[str, Any]:
        """Get orchestrator status"""
        return {
            'orchestrator_id': self.orchestrator_id,
            'registered_agents': list(self.registered_agents.keys()),
            'active_workflows': len(self.active_workflows),
            'pending_requests': len(self.pending_requests),
            'total_requests': self.total_requests,
            'total_approvals': self.total_approvals,
            'total_rejections': self.total_rejections,
            'rule_violations': len(self.rules_enforcer.get_violations()),
            'has_violations': self.rules_enforcer.has_violations(),
        }
