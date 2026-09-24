"""
Human-AI Collaboration Interface

Provides interactive interfaces for human oversight, strategy refinement,
approval workflows, and performance monitoring for the Aletheia system.
"""

import logging
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum

logger = logging.getLogger(__name__)


class InteractionMode(Enum):
    """Modes of human-AI interaction"""
    FULLY_AUTONOMOUS = "fully_autonomous"  # Level A
    SUPERVISED = "supervised"  # Level C - human reviews
    INTERACTIVE = "interactive"  # Level H - human guides
    MANUAL = "manual"  # Human controls everything


@dataclass
class StrategyPresentation:
    """Formatted presentation of a strategy for human review"""
    hypothesis_id: str
    title: str
    summary: str
    rationale: str
    key_rules: List[str]
    risk_summary: str
    performance_expectations: str
    confidence_score: float
    verification_status: str
    warnings: List[str]
    recommendations: List[str]
    visual_elements: Dict[str, Any] = field(default_factory=dict)


@dataclass
class HumanFeedback:
    """Human feedback on a strategy"""
    hypothesis_id: str
    feedback_type: str  # "approve", "reject", "modify", "question"
    comments: str
    suggested_changes: List[str]
    priority_adjustments: Dict[str, Any]
    provided_by: str
    provided_at: datetime = field(default_factory=datetime.now)


class HumanAIInterface:
    """
    Interface for human-AI collaboration in strategy research.
    
    Provides:
    - Strategy presentation and explanation
    - Approval workflows
    - Interactive refinement
    - Performance monitoring
    - Feedback collection
    """
    
    def __init__(
        self,
        research_framework: 'AutonomousResearchFramework',
        governance_integration: 'AletheiaGovernanceIntegration',
        default_mode: InteractionMode = InteractionMode.SUPERVISED
    ):
        self.research_framework = research_framework
        self.governance = governance_integration
        self.default_mode = default_mode
        
        # State tracking
        self.pending_reviews: Dict[str, StrategyPresentation] = {}
        self.feedback_history: List[HumanFeedback] = []
        self.active_sessions: Dict[str, Dict] = {}
        
        # Callbacks
        self.presentation_callbacks: List[Callable] = []
        self.feedback_callbacks: List[Callable] = []
        
        logger.info("HumanAIInterface initialized")
    
    async def present_strategy_for_review(
        self,
        hypothesis_id: str,
        presentation_format: str = "detailed"  # brief, detailed, technical
    ) -> StrategyPresentation:
        """
        Create a human-readable presentation of a strategy
        
        Args:
            hypothesis_id: Strategy to present
            presentation_format: Level of detail
            
        Returns:
            StrategyPresentation object
        """
        # Find the hypothesis
        hypothesis = None
        for project in self.research_framework.projects.values():
            for h in project.hypotheses:
                if h.hypothesis_id == hypothesis_id:
                    hypothesis = h
                    break
            if hypothesis:
                break
        
        if not hypothesis:
            raise ValueError(f"Hypothesis {hypothesis_id} not found")
        
        # Create presentation
        presentation = StrategyPresentation(
            hypothesis_id=hypothesis.hypothesis_id,
            title=hypothesis.title,
            summary=self._generate_summary(hypothesis),
            rationale=hypothesis.rationale,
            key_rules=hypothesis.entry_rules + hypothesis.exit_rules[:3],
            risk_summary=self._summarize_risk(hypothesis),
            performance_expectations=self._summarize_performance(hypothesis),
            confidence_score=hypothesis.confidence_score,
            verification_status=hypothesis.verification_status,
            warnings=self._identify_warnings(hypothesis),
            recommendations=self._generate_recommendations(hypothesis),
            visual_elements={
                "confidence_meter": hypothesis.confidence_score,
                "risk_gauge": hypothesis.risk_parameters.get("max_position_size", 2),
                "verification_badge": hypothesis.verification_status
            }
        )
        
        self.pending_reviews[hypothesis_id] = presentation
        
        # Trigger callbacks
        for callback in self.presentation_callbacks:
            try:
                await callback(presentation)
            except Exception as e:
                logger.error(f"Presentation callback error: {e}")
        
        return presentation
    
    def _generate_summary(self, hypothesis) -> str:
        """Generate human-readable strategy summary"""
        return f"""
{hypothesis.description}

This strategy generates signals based on {len(hypothesis.entry_rules)} entry conditions 
and manages risk through {len(hypothesis.exit_rules)} exit rules. It is designed to 
operate primarily in {', '.join(hypothesis.market_conditions[:2])} market conditions.

Strategy Type: {self._extract_strategy_type(hypothesis)}
Complexity Level: {"High" if len(hypothesis.entry_rules) > 5 else "Medium" if len(hypothesis.entry_rules) > 3 else "Low"}
Expected Trades: {hypothesis.expected_performance.get('expected_trades_per_month', 10)} per month
        """.strip()
    
    def _extract_strategy_type(self, hypothesis) -> str:
        """Extract strategy type from hypothesis"""
        if "momentum" in hypothesis.title.lower():
            return "Momentum/Trend Following"
        elif "mean reversion" in hypothesis.title.lower() or "reversion" in hypothesis.description.lower():
            return "Mean Reversion"
        elif "breakout" in hypothesis.title.lower():
            return "Breakout"
        elif "arbitrage" in hypothesis.title.lower():
            return "Statistical Arbitrage"
        elif "sentiment" in hypothesis.title.lower():
            return "Sentiment-Based"
        return "Multi-Factor"
    
    def _summarize_risk(self, hypothesis) -> str:
        """Generate risk summary"""
        params = hypothesis.risk_parameters
        return f"""
Risk Management Profile:
- Maximum Position Size: {params.get('max_position_size', 2)}% of portfolio
- Daily Loss Limit: {params.get('max_daily_loss', 3)}% of portfolio
- Maximum Drawdown: {params.get('max_drawdown', 10)}%
- Correlation Limit: {params.get('max_correlation', 0.7)}

Risk Level: {"Conservative" if params.get('max_position_size', 2) < 2 else "Moderate" if params.get('max_position_size', 2) < 4 else "Aggressive"}
        """.strip()
    
    def _summarize_performance(self, hypothesis) -> str:
        """Generate performance summary"""
        perf = hypothesis.expected_performance
        return f"""
Expected Performance:
- Win Rate: {perf.get('expected_win_rate', 0.5):.0%}
- Profit Factor: {perf.get('expected_profit_factor', 1.5):.1f}
- Sharpe Ratio: {perf.get('expected_sharpe_ratio', 1.0):.2f}
- Estimated Trades: {perf.get('expected_trades_per_month', 10)} per month
- Expected Max Drawdown: {perf.get('expected_max_drawdown', 8)}%

Quality Score: {"A" if hypothesis.confidence_score > 0.9 else "B" if hypothesis.confidence_score > 0.8 else "C"} (Confidence: {hypothesis.confidence_score:.0%})
        """.strip()
    
    def _identify_warnings(self, hypothesis) -> List[str]:
        """Identify potential warnings"""
        warnings = []
        
        if hypothesis.confidence_score < 0.80:
            warnings.append(f"Confidence score ({hypothesis.confidence_score:.0%}) is below optimal threshold")
        
        if hypothesis.verification_status != "verified":
            warnings.append(f"Strategy is {hypothesis.verification_status} - additional review recommended")
        
        if hypothesis.revision_count > 3:
            warnings.append(f"Required {hypothesis.revision_count} revisions - may indicate instability")
        
        max_pos = hypothesis.risk_parameters.get("max_position_size", 2)
        if max_pos > 5:
            warnings.append(f"Large position size ({max_pos}%) increases concentration risk")
        
        if hypothesis.expected_performance.get("expected_win_rate", 0.5) < 0.45:
            warnings.append("Low win rate increases dependency on reward-to-risk ratio")
        
        return warnings
    
    def _generate_recommendations(self, hypothesis) -> List[str]:
        """Generate recommendations"""
        recs = []
        
        if hypothesis.confidence_score < 0.85:
            recs.append("Consider additional backtesting on different time periods")
        
        if len(hypothesis.market_conditions) < 3:
            recs.append("Test strategy across more diverse market conditions")
        
        if hypothesis.risk_parameters.get("max_position_size", 2) > 3:
            recs.append("Consider reducing position size for better risk distribution")
        
        if hypothesis.expected_performance.get("expected_trades_per_month", 10) < 5:
            recs.append("Low trade frequency may lead to long periods without signals")
        
        return recs
    
    async def submit_human_feedback(
        self,
        hypothesis_id: str,
        feedback_type: str,
        comments: str,
        suggested_changes: Optional[List[str]] = None,
        priority_adjustments: Optional[Dict] = None,
        user: str = "Anonymous"
    ) -> HumanFeedback:
        """
        Submit human feedback on a strategy
        
        Args:
            hypothesis_id: Strategy being reviewed
            feedback_type: approve, reject, modify, question
            comments: Human comments
            suggested_changes: List of suggested modifications
            priority_adjustments: Adjustments to make
            user: Name of reviewer
            
        Returns:
            HumanFeedback object
        """
        feedback = HumanFeedback(
            hypothesis_id=hypothesis_id,
            feedback_type=feedback_type,
            comments=comments,
            suggested_changes=suggested_changes or [],
            priority_adjustments=priority_adjustments or {},
            provided_by=user
        )
        
        self.feedback_history.append(feedback)
        
        # Remove from pending reviews
        if hypothesis_id in self.pending_reviews:
            del self.pending_reviews[hypothesis_id]
        
        # Trigger callbacks
        for callback in self.feedback_callbacks:
            try:
                await callback(feedback)
            except Exception as e:
                logger.error(f"Feedback callback error: {e}")
        
        logger.info(f"Feedback submitted for {hypothesis_id}: {feedback_type}")
        
        # If approved, trigger governance approval
        if feedback_type == "approve":
            await self.governance.approve_request(
                f"strategy_{hypothesis_id}",
                user,
                "human_approved"
            )
        
        return feedback
    
    async def interactive_refinement(
        self,
        hypothesis_id: str,
        refinement_request: str,
        user: str = "Human"
    ) -> Dict[str, Any]:
        """
        Interactive strategy refinement based on human input
        
        Args:
            hypothesis_id: Strategy to refine
            refinement_request: Natural language refinement request
            user: User requesting refinement
            
        Returns:
            Refinement result
        """
        logger.info(f"Interactive refinement requested for {hypothesis_id}: {refinement_request}")
        
        # Find hypothesis
        hypothesis = None
        for project in self.research_framework.projects.values():
            for h in project.hypotheses:
                if h.hypothesis_id == hypothesis_id:
                    hypothesis = h
                    break
            if hypothesis:
                break
        
        if not hypothesis:
            return {"error": "Hypothesis not found"}
        
        # Parse refinement request (simplified)
        changes_made = []
        
        if "risk" in refinement_request.lower() or "position" in refinement_request.lower():
            # Reduce position size
            old_size = hypothesis.risk_parameters.get("max_position_size", 2)
            new_size = max(old_size * 0.7, 1.0)
            hypothesis.risk_parameters["max_position_size"] = new_size
            changes_made.append(f"Reduced max position size from {old_size}% to {new_size}%")
        
        if "stop" in refinement_request.lower():
            # Add tighter stop
            hypothesis.exit_rules.append("Additional trailing stop at 1.5x ATR")
            changes_made.append("Added trailing stop condition")
        
        if "frequency" in refinement_request.lower() or "more trades" in refinement_request.lower():
            # Increase expected frequency
            old_freq = hypothesis.expected_performance.get("expected_trades_per_month", 10)
            hypothesis.expected_performance["expected_trades_per_month"] = int(old_freq * 1.3)
            changes_made.append(f"Increased expected trade frequency from {old_freq} to {hypothesis.expected_performance['expected_trades_per_month']} per month")
        
        if "filter" in refinement_request.lower() or "quality" in refinement_request.lower():
            # Add volume filter
            hypothesis.entry_rules.append("Volume confirmation: 150% of 20-period average")
            changes_made.append("Added volume filter for signal quality")
        
        return {
            "hypothesis_id": hypothesis_id,
            "changes_made": changes_made,
            "refinement_request": refinement_request,
            "refined_by": user,
            "refined_at": datetime.now().isoformat()
        }
    
    async def get_performance_dashboard(
        self,
        project_id: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Generate performance monitoring dashboard
        
        Args:
            project_id: Specific project or all projects
            
        Returns:
            Dashboard data
        """
        if project_id:
            if project_id not in self.research_framework.projects:
                return {"error": "Project not found"}
            
            project = self.research_framework.projects[project_id]
            return {
                "project_title": project.title,
                "status": project.status,
                "hypotheses_generated": len(project.hypotheses),
                "verified_count": sum(1 for h in project.hypotheses if h.verification_status == "verified"),
                "best_strategy": {
                    "title": project.best_hypothesis.title if project.best_hypothesis else None,
                    "confidence": project.best_hypothesis.confidence_score if project.best_hypothesis else 0
                },
                "strategies": [
                    {
                        "id": h.hypothesis_id,
                        "title": h.title,
                        "status": h.verification_status,
                        "confidence": h.confidence_score,
                        "revisions": h.revision_count
                    }
                    for h in project.hypotheses
                ]
            }
        
        # All projects
        stats = self.research_framework.get_research_statistics()
        return {
            "overview": stats,
            "projects_summary": self.research_framework.get_all_projects_summary()
        }
    
    def on_strategy_presented(self, callback: Callable):
        """Register callback for when strategy is presented"""
        self.presentation_callbacks.append(callback)
    
    def on_feedback_received(self, callback: Callable):
        """Register callback for when feedback is received"""
        self.feedback_callbacks.append(callback)
    
    def get_pending_reviews(self) -> Dict[str, StrategyPresentation]:
        """Get all pending strategy reviews"""
        return self.pending_reviews
    
    def get_feedback_history(
        self,
        hypothesis_id: Optional[str] = None,
        user: Optional[str] = None
    ) -> List[HumanFeedback]:
        """Get feedback history with optional filtering"""
        history = self.feedback_history
        
        if hypothesis_id:
            history = [f for f in history if f.hypothesis_id == hypothesis_id]
        
        if user:
            history = [f for f in history if f.provided_by == user]
        
        return history
