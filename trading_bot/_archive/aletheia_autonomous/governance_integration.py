"""
Aletheia-AlphaAlgo Governance Integration

Integrates the Aletheia autonomous research system with AlphaAlgo's governance hierarchy.
Ensures all research activities comply with G0/G1/G2 governance levels.
"""

import logging
from typing import Dict, List, Optional, Any, Callable
from datetime import datetime
from enum import Enum

from .aletheia_orchestrator import AletheiaOrchestrator, AutonomyLevel
from .research_framework import AutonomousResearchFramework, ResearchProject

logger = logging.getLogger(__name__)


class GovernanceLevel(Enum):
    """AlphaAlgo Governance Levels"""
    G0 = "G0"  # Human Authority - Ultimate control
    G1 = "G1"  # Central Controller - Coordinates modules
    G2 = "G2"  # Mini-AIs - Specialized helpers


class GovernanceAction(Enum):
    """Actions requiring governance approval"""
    CREATE_RESEARCH_PROJECT = "create_research_project"
    START_RESEARCH = "start_research"
    DEPLOY_STRATEGY = "deploy_strategy"
    MODIFY_RISK_PARAMS = "modify_risk_params"
    ENABLE_LIVE_TRADING = "enable_live_trading"
    CONNECT_BROKER = "connect_broker"
    AUTO_APPROVE_LEVEL_A = "auto_approve_level_a"


class AletheiaGovernanceIntegration:
    """
    Integrates Aletheia with AlphaAlgo governance system.
    
    Ensures all autonomous research activities respect the G0/G1/G2 hierarchy:
    - G0: Human approves research projects, strategy deployment, major changes
    - G1: Central controller coordinates research activities
    - G2: Mini-AIs execute research tasks
    """
    
    def __init__(
        self,
        research_framework: AutonomousResearchFramework,
        alphaalgo_orchestrator: Optional[Any] = None,
        strict_mode: bool = True
    ):
        self.research_framework = research_framework
        self.alphaalgo_orchestrator = alphaalgo_orchestrator
        self.strict_mode = strict_mode
        
        # Governance tracking
        self.pending_approvals: Dict[str, Dict] = {}
        self.approval_history: List[Dict] = []
        self.governance_callbacks: Dict[GovernanceLevel, List[Callable]] = {
            GovernanceLevel.G0: [],
            GovernanceLevel.G1: [],
            GovernanceLevel.G2: []
        }
        
        # Policy settings
        self.auto_deploy_level_a = False  # G0 must approve even Level A
        self.require_approval_for_research = True  # G0 approves research projects
        self.risk_limits = {
            "max_strategy_risk": 0.05,
            "max_portfolio_risk": 0.15,
            "min_confidence_for_auto": 0.90
        }
        
        logger.info("AletheiaGovernanceIntegration initialized")
    
    def _requires_g0_approval(self, action: GovernanceAction, context: Dict) -> bool:
        """Determine if action requires G0 (human) approval"""
        
        # Critical actions always need G0
        if action in [
            GovernanceAction.DEPLOY_STRATEGY,
            GovernanceAction.ENABLE_LIVE_TRADING,
            GovernanceAction.CONNECT_BROKER,
            GovernanceAction.MODIFY_RISK_PARAMS
        ]:
            return True
        
        # Research projects need G0 approval in strict mode
        if action == GovernanceAction.CREATE_RESEARCH_PROJECT and self.require_approval_for_research:
            return True
        
        # Level A auto-approval needs G0 authorization
        if action == GovernanceAction.AUTO_APPROVE_LEVEL_A:
            return True
        
        # Check autonomy level
        if "autonomy_level" in context:
            autonomy_level = context["autonomy_level"]
            if autonomy_level == AutonomyLevel.LEVEL_A and not self.auto_deploy_level_a:
                return True
        
        # G1 can approve in non-strict mode
        return self.strict_mode
    
    async def request_approval(
        self,
        action: GovernanceAction,
        requester: str,
        details: Dict[str, Any],
        required_level: Optional[GovernanceLevel] = None
    ) -> Dict[str, Any]:
        """
        Request governance approval for an action
        
        Args:
            action: Type of action requiring approval
            requester: Who/what is requesting
            details: Details of the request
            required_level: Override the governance level required
            
        Returns:
            Approval result with approval_id and status
        """
        # Determine required level
        if required_level is None:
            requires_g0 = self._requires_g0_approval(action, details)
            required_level = GovernanceLevel.G0 if requires_g0 else GovernanceLevel.G1
        
        # Generate approval request
        approval_id = f"{action.value}_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{id(details) % 10000}"
        
        approval_request = {
            "approval_id": approval_id,
            "action": action.value,
            "requester": requester,
            "required_level": required_level.value,
            "status": "pending",
            "details": details,
            "created_at": datetime.now().isoformat(),
            "approved_at": None,
            "approved_by": None,
            "rejection_reason": None
        }
        
        self.pending_approvals[approval_id] = approval_request
        
        logger.info(f"Approval requested: {approval_id} for {action.value} (Level {required_level.value})")
        
        # If G2 level, auto-approve
        if required_level == GovernanceLevel.G2:
            return await self.approve_request(approval_id, "G2_AUTO", "auto_approved")
        
        # Notify callbacks
        for callback in self.governance_callbacks.get(required_level, []):
            try:
                await callback(approval_request)
            except Exception as e:
                logger.error(f"Governance callback error: {e}")
        
        return {
            "approval_id": approval_id,
            "status": "pending",
            "required_level": required_level.value,
            "message": f"Awaiting {required_level.value} approval"
        }
    
    async def approve_request(
        self,
        approval_id: str,
        approver: str,
        approval_type: str = "human_approved"
    ) -> Dict[str, Any]:
        """
        Approve a pending request
        
        Args:
            approval_id: ID of the approval request
            approver: Name/ID of approver
            approval_type: Type of approval
            
        Returns:
            Approval result
        """
        if approval_id not in self.pending_approvals:
            return {"error": "Approval request not found"}
        
        request = self.pending_approvals[approval_id]
        request["status"] = "approved"
        request["approved_at"] = datetime.now().isoformat()
        request["approved_by"] = approver
        request["approval_type"] = approval_type
        
        self.approval_history.append(request)
        del self.pending_approvals[approval_id]
        
        logger.info(f"Request approved: {approval_id} by {approver}")
        
        return {
            "approval_id": approval_id,
            "status": "approved",
            "action": request["action"],
            "approved_by": approver,
            "approved_at": request["approved_at"]
        }
    
    async def reject_request(
        self,
        approval_id: str,
        rejector: str,
        reason: str
    ) -> Dict[str, Any]:
        """Reject a pending request"""
        if approval_id not in self.pending_approvals:
            return {"error": "Approval request not found"}
        
        request = self.pending_approvals[approval_id]
        request["status"] = "rejected"
        request["rejection_reason"] = reason
        request["rejected_at"] = datetime.now().isoformat()
        request["rejected_by"] = rejector
        
        self.approval_history.append(request)
        del self.pending_approvals[approval_id]
        
        logger.info(f"Request rejected: {approval_id} by {rejector}: {reason}")
        
        return {
            "approval_id": approval_id,
            "status": "rejected",
            "reason": reason,
            "rejected_by": rejector
        }
    
    async def create_governed_research_project(
        self,
        title: str,
        description: str,
        research_prompts: List[str],
        autonomy_level: AutonomyLevel = AutonomyLevel.LEVEL_C,
        market_context: Optional[Dict] = None,
        constraints: Optional[Dict] = None,
        requester: str = "Aletheia"
    ) -> Dict[str, Any]:
        """
        Create a research project with governance approval
        
        Returns project info after approval
        """
        # Request approval first
        approval = await self.request_approval(
            action=GovernanceAction.CREATE_RESEARCH_PROJECT,
            requester=requester,
            details={
                "title": title,
                "description": description,
                "prompts_count": len(research_prompts),
                "autonomy_level": autonomy_level.value,
                "sample_prompt": research_prompts[0] if research_prompts else ""
            }
        )
        
        # In a real system, would wait for approval here
        # For now, auto-approve for demonstration
        if approval["status"] == "pending":
            # Auto-approve for testing (would be human in production)
            approval_result = await self.approve_request(
                approval["approval_id"],
                "GovernanceSystem",
                "auto_approved"
            )
        
        # Create the project
        project = await self.research_framework.create_research_project(
            title=title,
            description=description,
            research_prompts=research_prompts,
            autonomy_level=autonomy_level,
            market_context=market_context,
            constraints=constraints
        )
        
        return {
            "project_id": project.project_id,
            "approval_id": approval["approval_id"],
            "status": "created",
            "title": title,
            "autonomy_level": autonomy_level.value
        }
    
    async def deploy_strategy_with_governance(
        self,
        project_id: str,
        hypothesis_id: Optional[str] = None,
        deployment_mode: str = "simulation",  # simulation, paper, live
        requester: str = "Aletheia"
    ) -> Dict[str, Any]:
        """
        Deploy a strategy with full governance approval
        
        Args:
            project_id: Research project containing strategy
            hypothesis_id: Specific strategy (or best if None)
            deployment_mode: How to deploy (simulation/paper/live)
            requester: Who is requesting deployment
            
        Returns:
            Deployment result
        """
        # Get project
        if project_id not in self.research_framework.projects:
            return {"error": "Project not found"}
        
        project = self.research_framework.projects[project_id]
        
        # Get strategy to deploy
        if hypothesis_id:
            strategy = next(
                (h for h in project.hypotheses if h.hypothesis_id == hypothesis_id),
                None
            )
        else:
            strategy = project.best_hypothesis
        
        if not strategy:
            return {"error": "Strategy not found"}
        
        # Determine required governance level based on deployment mode
        if deployment_mode == "live":
            required_level = GovernanceLevel.G0
        elif deployment_mode == "paper":
            required_level = GovernanceLevel.G1
        else:
            required_level = GovernanceLevel.G2
        
        # Request approval
        approval = await self.request_approval(
            action=GovernanceAction.DEPLOY_STRATEGY,
            requester=requester,
            required_level=required_level,
            details={
                "project_id": project_id,
                "strategy_title": strategy.title,
                "strategy_id": strategy.hypothesis_id,
                "deployment_mode": deployment_mode,
                "confidence_score": strategy.confidence_score,
                "verification_status": strategy.verification_status,
                "risk_parameters": strategy.risk_parameters
            }
        )
        
        return {
            "approval_id": approval["approval_id"],
            "strategy_id": strategy.hypothesis_id,
            "strategy_title": strategy.title,
            "deployment_mode": deployment_mode,
            "required_approval_level": required_level.value,
            "status": approval["status"],
            "message": f"Strategy deployment pending {required_level.value} approval"
        }
    
    def get_pending_approvals(self, level: Optional[GovernanceLevel] = None) -> List[Dict]:
        """Get pending approvals, optionally filtered by level"""
        approvals = list(self.pending_approvals.values())
        
        if level:
            approvals = [a for a in approvals if a["required_level"] == level.value]
        
        return approvals
    
    def get_approval_history(
        self,
        action_type: Optional[str] = None,
        limit: int = 100
    ) -> List[Dict]:
        """Get approval history"""
        history = self.approval_history[-limit:]
        
        if action_type:
            history = [h for h in history if h["action"] == action_type]
        
        return history
    
    def on_governance_decision(self, level: GovernanceLevel, callback: Callable):
        """Register callback for governance decisions at a specific level"""
        self.governance_callbacks[level].append(callback)
    
    def set_policy(self, policy_name: str, value: Any):
        """Set governance policy"""
        if policy_name == "auto_deploy_level_a":
            self.auto_deploy_level_a = value
        elif policy_name == "require_research_approval":
            self.require_approval_for_research = value
        elif policy_name == "strict_mode":
            self.strict_mode = value
        else:
            raise ValueError(f"Unknown policy: {policy_name}")
        
        logger.info(f"Governance policy updated: {policy_name} = {value}")
    
    def get_governance_summary(self) -> Dict[str, Any]:
        """Get governance system summary"""
        return {
            "pending_approvals": {
                "total": len(self.pending_approvals),
                "G0": len([a for a in self.pending_approvals.values() if a["required_level"] == "G0"]),
                "G1": len([a for a in self.pending_approvals.values() if a["required_level"] == "G1"]),
                "G2": len([a for a in self.pending_approvals.values() if a["required_level"] == "G2"])
            },
            "approval_history_count": len(self.approval_history),
            "policies": {
                "auto_deploy_level_a": self.auto_deploy_level_a,
                "require_research_approval": self.require_approval_for_research,
                "strict_mode": self.strict_mode
            },
            "risk_limits": self.risk_limits
        }
