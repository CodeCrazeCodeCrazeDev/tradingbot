"""
Verified Intelligence Integration

Integrates the Autonomous Financial Intelligence Infrastructure with the
existing AutonomousCore to provide Verified Evidence Reasoning and
Multi-Layer Anti-Hallucination Governance.
"""

import asyncio
import json
import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple
from dataclasses import dataclass
from pathlib import Path

from ..autonomous_financial_intelligence import FinancialIntelligenceOrchestrator
from ..autonomous_financial_intelligence.evidence_verification import EvidenceType

logger = logging.getLogger(__name__)


@dataclass
class VerifiedDecisionWrapper:
    """Wrapper for decisions that have been verified."""
    original_decision: Any
    verification_result: Dict[str, Any]
    is_verified: bool
    is_approved: bool
    execution_allowed: bool
    calibrated_confidence: float
    verification_timestamp: datetime


class VerifiedIntelligenceIntegration:
    """
    Integration layer between AutonomousCore and Financial Intelligence Infrastructure.
    
    Provides:
    - Decision verification before execution
    - Evidence-backed reasoning
    - Hallucination prevention
    - Consensus-based approval for high-impact decisions
    - Confidence calibration
    """
    
    def __init__(self, autonomous_core, config: Optional[Dict] = None):
        self.core = autonomous_core
        self.config = config or {}
        
        self._orchestrator: Optional[FinancialIntelligenceOrchestrator] = None
        self._initialized = False
        
        self._integration_config = {
            'verify_all_decisions': True,
            'require_evidence_for_trading': True,
            'high_impact_threshold': 0.8,
            'minimum_confidence_for_execution': 0.6,
            'enable_consensus_for_capital': True,
            'hallucination_check_enabled': True,
        }
        
        self._verification_stats = {
            'decisions_verified': 0,
            'decisions_approved': 0,
            'decisions_rejected': 0,
            'hallucinations_blocked': 0,
        }
        
        logger.info("Verified Intelligence Integration created")
    
    async def initialize(self):
        """Initialize the integration and underlying infrastructure."""
        if self._initialized:
            return
        
        logger.info("=" * 80)
        logger.info("INITIALIZING VERIFIED INTELLIGENCE INTEGRATION")
        logger.info("=" * 80)
        
        orchestrator_config = {
            'storage_path': self.core.storage_path / 'financial_intelligence',
            'require_evidence': self._integration_config['require_evidence_for_trading'],
            'require_consensus': self._integration_config['enable_consensus_for_capital'],
            'hallucination_check': self._integration_config['hallucination_check_enabled'],
            'minimum_confidence': self._integration_config['minimum_confidence_for_execution'],
        }
        
        self._orchestrator = FinancialIntelligenceOrchestrator(orchestrator_config)
        await self._orchestrator.initialize()
        
        self._initialized = True
        
        logger.info("✅ Verified Intelligence Integration ready")
        logger.info("=" * 80)
    
    async def verify_decision(
        self,
        decision,
        evidence: Optional[List[Dict[str, Any]]] = None,
        context: Optional[Dict[str, Any]] = None,
    ) -> VerifiedDecisionWrapper:
        """
        Verify a decision through the full verification pipeline.
        
        Args:
            decision: The Decision object from AutonomousCore
            evidence: Optional supporting evidence
            context: Optional context for verification
        
        Returns:
            VerifiedDecisionWrapper with verification results
        """
        if not self._initialized:
            await self.initialize()
        
        decision_dict = {
            'decision_id': decision.decision_id,
            'decision_type': decision.decision_type,
            'reasoning': decision.reasoning,
            'actions': decision.actions,
            'expected_impact': decision.expected_impact,
            'confidence': decision.confidence,
            'timestamp': decision.timestamp.isoformat() if hasattr(decision.timestamp, 'isoformat') else str(decision.timestamp),
        }
        
        if evidence is None:
            evidence = self._extract_evidence_from_decision(decision)
        
        is_high_impact = self._is_high_impact_decision(decision)
        
        agent_id = f"autonomous_core_{id(self.core)}"
        
        verified = await self._orchestrator.verify_and_approve_decision(
            decision=decision_dict,
            evidence=evidence,
            agent_id=agent_id,
            context=context or self._build_context(),
            is_high_impact=is_high_impact,
        )
        
        self._verification_stats['decisions_verified'] += 1
        
        if verified.is_approved:
            self._verification_stats['decisions_approved'] += 1
        else:
            self._verification_stats['decisions_rejected'] += 1
            
            if 'hallucination_check' in verified.verification_details.get('stages_failed', []):
                self._verification_stats['hallucinations_blocked'] += 1
        
        return VerifiedDecisionWrapper(
            original_decision=decision,
            verification_result=verified.to_dict(),
            is_verified=verified.verification_status == "APPROVED",
            is_approved=verified.is_approved,
            execution_allowed=verified.execution_allowed,
            calibrated_confidence=verified.calibrated_confidence,
            verification_timestamp=verified.verification_timestamp,
        )
    
    def _extract_evidence_from_decision(self, decision) -> List[Dict[str, Any]]:
        """Extract evidence from decision reasoning and actions."""
        evidence = []
        
        for i, reason in enumerate(decision.reasoning):
            evidence.append({
                'type': 'market_data',
                'source_id': f'reasoning_{i}',
                'source_name': 'internal_analysis',
                'content': {'reasoning': reason},
                'metadata': {'step': i},
            })
        
        for action in decision.actions:
            if 'data' in action or 'analysis' in action:
                evidence.append({
                    'type': 'technical_indicator',
                    'source_id': f"action_{action.get('action', 'unknown')}",
                    'source_name': 'action_analysis',
                    'content': action,
                    'metadata': {'action_type': action.get('action')},
                })
        
        return evidence
    
    def _is_high_impact_decision(self, decision) -> bool:
        """Determine if a decision is high-impact."""
        high_impact_types = {
            'capital_deployment',
            'large_trade',
            'strategy_change',
            'risk_adjustment',
            'agent_expansion',
            'system_modification',
        }
        
        if decision.decision_type in high_impact_types:
            return True
        
        impact = decision.expected_impact
        if impact:
            max_impact = max(abs(v) for v in impact.values() if isinstance(v, (int, float)))
            if max_impact > self._integration_config['high_impact_threshold']:
                return True
        
        return False
    
    def _build_context(self) -> Dict[str, Any]:
        """Build context from current system state."""
        return {
            'autonomy_level': self.core.state.autonomy_level,
            'system_health': self.core.state.system_health,
            'active_agents': len(self.core.state.active_agents),
            'consciousness_level': self.core.consciousness_level,
            'market_regime': 'unknown',
            'risk_parameters': {
                'max_position_size': 0.1,
                'max_drawdown': 0.2,
            },
            'time_horizon': 'short_term',
        }
    
    async def verified_think(self) -> Tuple[Any, VerifiedDecisionWrapper]:
        """
        Enhanced thinking with verification.
        
        Returns:
            Tuple of (decision, verification_wrapper)
        """
        decision = await self.core.think()
        
        verification = await self.verify_decision(decision)
        
        if not verification.is_approved:
            logger.warning(
                f"Decision {decision.decision_id} rejected by verification: "
                f"{verification.verification_result.get('verification_status')}"
            )
        
        return decision, verification
    
    async def verified_execute(
        self,
        decision,
        verification: Optional[VerifiedDecisionWrapper] = None,
    ) -> Dict[str, Any]:
        """
        Execute a decision only if it passes verification.
        
        Args:
            decision: The decision to execute
            verification: Optional pre-computed verification
        
        Returns:
            Execution results
        """
        if verification is None:
            verification = await self.verify_decision(decision)
        
        if not verification.execution_allowed:
            logger.warning(f"Execution blocked for decision {decision.decision_id}")
            return {
                'decision_id': decision.decision_id,
                'success': False,
                'blocked': True,
                'reason': 'Verification failed',
                'verification_status': verification.verification_result.get('verification_status'),
                'calibrated_confidence': verification.calibrated_confidence,
            }
        
        decision.confidence = verification.calibrated_confidence
        
        results = await self.core.execute_decision(decision)
        
        results['verified'] = True
        results['calibrated_confidence'] = verification.calibrated_confidence
        results['verification_details'] = verification.verification_result.get('verification_details', {})
        
        return results
    
    async def verified_autonomous_loop(self):
        """
        Enhanced autonomous loop with verification.
        Replaces the standard autonomous_loop with verified decision-making.
        """
        logger.info("Starting VERIFIED autonomous operation loop")
        
        while self.core.running:
            try:
                decision, verification = await self.verified_think()
                
                if verification.execution_allowed and verification.calibrated_confidence > self._integration_config['minimum_confidence_for_execution']:
                    results = await self.verified_execute(decision, verification)
                    
                    logger.info(
                        f"Verified decision executed: {decision.decision_type} - "
                        f"Success: {results.get('success')} - "
                        f"Confidence: {verification.calibrated_confidence:.2f}"
                    )
                else:
                    logger.info(
                        f"Decision {decision.decision_id} not executed: "
                        f"allowed={verification.execution_allowed}, "
                        f"confidence={verification.calibrated_confidence:.2f}"
                    )
                
                await self.core._persist_state()
                
                await asyncio.sleep(10)
                
            except Exception as e:
                logger.error(f"Error in verified autonomous loop: {e}", exc_info=True)
                await asyncio.sleep(30)
    
    async def reason_with_evidence(
        self,
        objective: str,
        premises: List[Dict[str, Any]],
        reasoning_steps: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """
        Perform verified reasoning with evidence requirements.
        
        Args:
            objective: The reasoning objective
            premises: Initial premises with evidence
            reasoning_steps: Steps to reach conclusion
        
        Returns:
            Verified reasoning result
        """
        if not self._initialized:
            await self.initialize()
        
        agent_id = f"autonomous_core_{id(self.core)}"
        
        return await self._orchestrator.reason_with_verification(
            objective=objective,
            premises=premises,
            reasoning_steps=reasoning_steps,
            agent_id=agent_id,
        )
    
    async def get_infrastructure_status(self) -> Dict[str, Any]:
        """Get status of the verification infrastructure."""
        if not self._initialized:
            return {
                'initialized': False,
                'verification_stats': self._verification_stats,
            }
        
        infra_status = await self._orchestrator.get_status()
        
        return {
            'initialized': True,
            'infrastructure_status': infra_status.to_dict(),
            'verification_stats': self._verification_stats,
            'integration_config': self._integration_config,
        }
    
    async def get_comprehensive_statistics(self) -> Dict[str, Any]:
        """Get comprehensive statistics from all components."""
        if not self._initialized:
            return {'error': 'Not initialized'}
        
        stats = await self._orchestrator.get_comprehensive_statistics()
        stats['integration'] = self._verification_stats
        
        return stats
    
    @property
    def orchestrator(self) -> FinancialIntelligenceOrchestrator:
        """Access the underlying orchestrator."""
        return self._orchestrator
    
    @property
    def is_initialized(self) -> bool:
        """Check if integration is initialized."""
        return self._initialized


def integrate_verified_intelligence(autonomous_core, config: Optional[Dict] = None) -> VerifiedIntelligenceIntegration:
    """
    Factory function to create and attach verified intelligence to an AutonomousCore.
    
    Args:
        autonomous_core: The AutonomousCore instance
        config: Optional configuration
    
    Returns:
        VerifiedIntelligenceIntegration instance
    """
    integration = VerifiedIntelligenceIntegration(autonomous_core, config)
    
    autonomous_core.verified_intelligence = integration
    
    return integration
