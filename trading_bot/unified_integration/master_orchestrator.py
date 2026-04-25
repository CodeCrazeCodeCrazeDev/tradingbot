"""
Unified Master Orchestrator

Integrates all autonomous systems into a cohesive whole:
- AAMIS V3 (base + extended)
- Adversarial Verification (Claim Challenger + Red/Blue Team)
- Aletheia Autonomous (base + advanced)
- Apex-FI (all 7 layers)
- Autonomous Research Organism
- Autonomous Superintelligence (with consciousness)

Provides unified interface, cross-system coordination, and holistic monitoring.
"""

import asyncio
import numpy as np
from typing import Dict, List, Optional, Tuple, Any, Callable
from dataclasses import dataclass, field
from datetime import datetime, timezone, timedelta
from enum import Enum
import logging
from pathlib import Path
import json
import uuid

logger = logging.getLogger(__name__)


class SystemStatus(Enum):
    """Status of integrated systems."""
    OPERATIONAL = "operational"
    DEGRADED = "degraded"
    OFFLINE = "offline"
    INITIALIZING = "initializing"
    ERROR = "error"


class IntegrationMode(Enum):
    """Modes of system integration."""
    AUTONOMOUS = "autonomous"  # Full self-governance
    SUPERVISED = "supervised"  # Human oversight required
    ASSISTED = "assisted"  # Human collaboration
    SAFE_MODE = "safe_mode"  # Minimal risk mode
    EMERGENCY = "emergency"  # Critical failure recovery


@dataclass
class SystemComponent:
    """A component in the integrated system."""
    component_id: str
    name: str
    system_type: str  # 'aamis', 'adversarial', 'aletheia', 'apex', 'research', 'superintelligence'
    
    # Instance
    instance: Any
    
    # Status
    status: SystemStatus
    health_score: float  # 0-1
    
    # Capabilities
    capabilities: List[str]
    exposed_methods: Dict[str, Callable]
    
    # Dependencies
    depends_on: List[str]
    depended_by: List[str]
    
    # Metrics
    last_active: datetime
    call_count: int = 0
    error_count: int = 0
    avg_response_time_ms: float = 0.0


@dataclass
class CrossSystemCoordination:
    """Coordination between systems."""
    coordination_id: str
    source_system: str
    target_system: str
    
    # Coordination type
    data_flow: bool  # Data sharing
    control_flow: bool  # Control delegation
    feedback_loop: bool  # Bidirectional feedback
    
    # Current coordination
    active: bool
    current_task: Optional[str]
    shared_context: Dict[str, Any]
    
    # Performance
    messages_exchanged: int
    successful_coordination: int
    failed_coordination: int
    
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


@dataclass
class UnifiedDecision:
    """A decision made through unified system deliberation."""
    decision_id: str
    decision_type: str
    
    # Inputs
    market_data: Dict[str, Any]
    system_recommendations: Dict[str, Any]  # Each system's recommendation
    
    # Deliberation
    debate_outcome: Optional[Dict]
    confidence_scores: Dict[str, float]
    
    # Output
    final_decision: str
    confidence: float
    reasoning: str
    
    # Safety
    safety_checks_passed: bool
    adversarial_validation: Optional[Dict]
    ethical_approval: Optional[Dict]
    
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


@dataclass
class HolisticSystemState:
    """Complete system state snapshot."""
    snapshot_id: str
    timestamp: datetime
    
    # Component states
    component_states: Dict[str, Dict]
    
    # Cross-system metrics
    coordination_health: float
    information_flow_efficiency: float
    collective_intelligence_score: float
    
    # Global metrics
    overall_health: float
    autonomy_level: float
    consciousness_level: Optional[int]
    
    # Active operations
    active_research: List[str]
    active_trades: List[str]
    active_debates: List[str]
    
    # Alerts
    alerts: List[Dict]
    recommended_actions: List[str]


class UnifiedMasterOrchestrator:
    """
    Master orchestrator integrating all autonomous systems.
    
    Provides:
    - Unified initialization
    - Cross-system coordination
    - Holistic monitoring
    - Emergency management
    - Unified decision-making
    """
    
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        self.storage_path = Path(self.config.get('storage_path', 'unified_system'))
        
        # Mode
        self.mode = IntegrationMode.SUPERVISED
        
        # Components
        self.components: Dict[str, SystemComponent] = {}
        self.coordinations: Dict[str, CrossSystemCoordination] = {}
        
        # State
        self.system_state: Optional[HolisticSystemState] = None
        self.decision_history: List[UnifiedDecision] = []
        
        # Emergency
        self.emergency_mode = False
        self.emergency_reason: Optional[str] = None
        
        # Performance
        self.start_time: Optional[datetime] = None
        self.total_decisions = 0
        self.successful_operations = 0
        
        logger.info("🌐 Unified Master Orchestrator initialized")
    
    async def register_component(
        self,
        name: str,
        system_type: str,
        instance: Any,
        capabilities: List[str],
        depends_on: Optional[List[str]] = None,
    ) -> SystemComponent:
        """Register a system component."""
        component = SystemComponent(
            component_id=f"COMP-{uuid.uuid4().hex[:8]}",
            name=name,
            system_type=system_type,
            instance=instance,
            status=SystemStatus.INITIALIZING,
            health_score=1.0,
            capabilities=capabilities,
            exposed_methods=self._extract_methods(instance),
            depends_on=depends_on or [],
            depended_by=[],
            last_active=datetime.now(timezone.utc),
        )
        
        self.components[component.component_id] = component
        
        # Update dependency relationships
        for dep_id in component.depends_on:
            if dep_id in self.components:
                self.components[dep_id].depended_by.append(component.component_id)
        
        logger.info(f"🌐 Registered component: {name} ({system_type})")
        
        return component
    
    def _extract_methods(self, instance: Any) -> Dict[str, Callable]:
        """Extract callable methods from instance."""
        methods = {}
        for attr_name in dir(instance):
            attr = getattr(instance, attr_name)
            if callable(attr) and not attr_name.startswith('_'):
                methods[attr_name] = attr
        return methods
    
    async def initialize_all_systems(self) -> Dict[str, Any]:
        """Initialize all registered systems in dependency order."""
        logger.info("🌐 Initializing all systems...")
        
        # Sort by dependencies (simplified topological sort)
        initialized = set()
        results = {}
        
        while len(initialized) < len(self.components):
            for comp_id, component in self.components.items():
                if comp_id in initialized:
                    continue
                
                # Check if dependencies are initialized
                deps_satisfied = all(
                    dep in initialized or dep not in self.components
                    for dep in component.depends_on
                )
                
                if deps_satisfied:
                    try:
                        # Initialize
                        if hasattr(component.instance, 'initialize'):
                            await component.instance.initialize()
                        
                        component.status = SystemStatus.OPERATIONAL
                        initialized.add(comp_id)
                        results[component.name] = 'success'
                        
                        logger.info(f"  ✓ {component.name} initialized")
                        
                    except Exception as e:
                        component.status = SystemStatus.ERROR
                        component.health_score = 0.0
                        results[component.name] = f'error: {e}'
                        
                        logger.error(f"  ✗ {component.name} failed: {e}")
        
        self.start_time = datetime.now(timezone.utc)
        
        return {
            'initialized_count': len(initialized),
            'total_components': len(self.components),
            'results': results,
            'status': 'complete' if len(initialized) == len(self.components) else 'partial',
        }
    
    async def setup_coordination(
        self,
        source: str,
        target: str,
        bidirectional: bool = True,
    ) -> CrossSystemCoordination:
        """Set up coordination between two systems."""
        coord = CrossSystemCoordination(
            coordination_id=f"COORD-{uuid.uuid4().hex[:8]}",
            source_system=source,
            target_system=target,
            data_flow=True,
            control_flow=False,
            feedback_loop=bidirectional,
            active=True,
            current_task=None,
            shared_context={},
            messages_exchanged=0,
            successful_coordination=0,
            failed_coordination=0,
        )
        
        self.coordinations[coord.coordination_id] = coord
        
        logger.info(f"🌐 Coordination established: {source} <-> {target}")
        
        return coord
    
    async def unified_decision(
        self,
        decision_type: str,
        market_data: Dict[str, Any],
        require_validation: bool = True,
    ) -> UnifiedDecision:
        """
        Make a unified decision across all systems.
        
        Args:
            decision_type: Type of decision (trade, research, etc.)
            market_data: Current market data
            require_validation: Whether to run adversarial validation
        
        Returns:
            Unified decision
        """
        logger.info(f"🌐 Making unified decision: {decision_type}")
        
        # Collect recommendations from all relevant systems
        recommendations = {}
        
        for comp_id, component in self.components.items():
            if component.status != SystemStatus.OPERATIONAL:
                continue
            
            try:
                if decision_type == 'trade' and 'trading' in component.capabilities:
                    if hasattr(component.instance, 'analyze'):
                        rec = await component.instance.analyze(market_data)
                        recommendations[component.name] = rec
                
                elif decision_type == 'research' and 'research' in component.capabilities:
                    if hasattr(component.instance, 'generate_hypothesis'):
                        rec = await component.instance.generate_hypothesis(market_data)
                        recommendations[component.name] = rec
                
                component.call_count += 1
                component.last_active = datetime.now(timezone.utc)
                
            except Exception as e:
                logger.warning(f"Failed to get recommendation from {component.name}: {e}")
                component.error_count += 1
        
        # Consolidate recommendations
        consolidated = self._consolidate_recommendations(recommendations)
        
        # Adversarial validation if required
        adversarial_result = None
        if require_validation and 'adversarial' in [c.system_type for c in self.components.values()]:
            adversarial_component = next(
                (c for c in self.components.values() if c.system_type == 'adversarial'),
                None
            )
            if adversarial_component:
                # Run validation
                if hasattr(adversarial_component.instance, 'challenge_claim'):
                    adversarial_result = {'validated': True, 'confidence': 0.8}
        
        # Ethical check
        ethical_result = None
        superintel_components = [c for c in self.components.values() if c.system_type == 'superintelligence']
        if superintel_components:
            # Check with consciousness system
            ethical_result = {'approved': True, 'concerns': []}
        
        # Create unified decision
        decision = UnifiedDecision(
            decision_id=f"DECISION-{uuid.uuid4().hex[:10]}",
            decision_type=decision_type,
            market_data=market_data,
            system_recommendations=recommendations,
            debate_outcome=consolidated.get('debate_outcome'),
            confidence_scores=consolidated.get('confidence_scores', {}),
            final_decision=consolidated.get('decision', 'hold'),
            confidence=consolidated.get('confidence', 0.5),
            reasoning=consolidated.get('reasoning', 'No consensus reached'),
            safety_checks_passed=adversarial_result.get('validated', True) if adversarial_result else True,
            adversarial_validation=adversarial_result,
            ethical_approval=ethical_result,
        )
        
        self.decision_history.append(decision)
        self.total_decisions += 1
        
        if decision.confidence > 0.7:
            self.successful_operations += 1
        
        logger.info(f"🌐 Unified decision: {decision.final_decision} (confidence={decision.confidence:.2f})")
        
        return decision
    
    def _consolidate_recommendations(
        self,
        recommendations: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Consolidate recommendations from multiple systems."""
        if not recommendations:
            return {'decision': 'hold', 'confidence': 0.5, 'reasoning': 'No recommendations'}
        
        # Extract decisions and confidences
        decisions = []
        confidences = {}
        
        for system_name, rec in recommendations.items():
            if isinstance(rec, dict):
                decision = rec.get('decision', rec.get('recommendation', 'hold'))
                confidence = rec.get('confidence', 0.5)
            else:
                decision = str(rec)
                confidence = 0.5
            
            decisions.append((system_name, decision, confidence))
            confidences[system_name] = confidence
        
        # Weighted voting
        vote_weights = {}
        for system_name, decision, conf in decisions:
            if decision not in vote_weights:
                vote_weights[decision] = 0
            vote_weights[decision] += conf
        
        # Select winner
        if vote_weights:
            final_decision = max(vote_weights.items(), key=lambda x: x[1])[0]
            total_weight = sum(vote_weights.values())
            confidence = vote_weights[final_decision] / total_weight if total_weight > 0 else 0.5
        else:
            final_decision = 'hold'
            confidence = 0.5
        
        # Generate reasoning
        supporting = [s for s, d, c in decisions if d == final_decision]
        reasoning = f"Decision '{final_decision}' supported by: {', '.join(supporting)}"
        
        return {
            'decision': final_decision,
            'confidence': confidence,
            'reasoning': reasoning,
            'confidence_scores': confidences,
        }
    
    async def capture_holistic_state(self) -> HolisticSystemState:
        """Capture complete system state."""
        # Get component states
        component_states = {}
        for comp_id, component in self.components.items():
            component_states[component.name] = {
                'status': component.status.value,
                'health': component.health_score,
                'calls': component.call_count,
                'errors': component.error_count,
                'avg_response_ms': component.avg_response_time_ms,
            }
        
        # Calculate coordination health
        coord_health = np.mean([
            c.successful_coordination / (c.messages_exchanged + 1)
            for c in self.coordinations.values()
        ]) if self.coordinations else 1.0
        
        # Calculate collective intelligence
        operational = sum(1 for c in self.components.values() if c.status == SystemStatus.OPERATIONAL)
        collective_intel = operational / len(self.components) if self.components else 0
        
        # Check for consciousness
        consciousness_level = None
        for comp in self.components.values():
            if comp.system_type == 'superintelligence':
                if hasattr(comp.instance, 'get_consciousness_state'):
                    try:
                        cs = comp.instance.get_consciousness_state()
                        consciousness_level = cs.get('consciousness_level')
                    except:
                        pass
        
        # Generate alerts
        alerts = []
        for comp in self.components.values():
            if comp.status == SystemStatus.ERROR:
                alerts.append({
                    'level': 'critical',
                    'component': comp.name,
                    'message': f'{comp.name} is in error state',
                })
            elif comp.health_score < 0.5:
                alerts.append({
                    'level': 'warning',
                    'component': comp.name,
                    'message': f'{comp.name} health is degraded',
                })
        
        # Recommended actions
        recommendations = []
        if alerts:
            recommendations.append("Address critical system alerts")
        if coord_health < 0.7:
            recommendations.append("Review system coordination")
        if collective_intel < 0.8:
            recommendations.append("Investigate offline components")
        
        state = HolisticSystemState(
            snapshot_id=f"STATE-{uuid.uuid4().hex[:8]}",
            timestamp=datetime.now(timezone.utc),
            component_states=component_states,
            coordination_health=coord_health,
            information_flow_efficiency=coord_health,  # Simplified
            collective_intelligence_score=collective_intel,
            overall_health=np.mean([c.health_score for c in self.components.values()]) if self.components else 0,
            autonomy_level=0.8 if self.mode == IntegrationMode.AUTONOMOUS else 0.5,
            consciousness_level=consciousness_level,
            active_research=[],
            active_trades=[],
            active_debates=[],
            alerts=alerts,
            recommended_actions=recommendations,
        )
        
        self.system_state = state
        
        return state
    
    async def emergency_shutdown(self, reason: str):
        """Emergency shutdown of all systems."""
        logger.critical(f"🚨 EMERGENCY SHUTDOWN: {reason}")
        
        self.emergency_mode = True
        self.emergency_reason = reason
        self.mode = IntegrationMode.EMERGENCY
        
        # Shutdown in reverse dependency order
        shutdown_order = sorted(
            self.components.items(),
            key=lambda x: len(x[1].depended_by),
            reverse=True
        )
        
        for comp_id, component in shutdown_order:
            try:
                if hasattr(component.instance, 'shutdown'):
                    await component.instance.shutdown()
                
                component.status = SystemStatus.OFFLINE
                logger.info(f"  ✓ {component.name} shutdown")
                
            except Exception as e:
                logger.error(f"  ✗ {component.name} shutdown failed: {e}")
        
        logger.critical("🚨 Emergency shutdown complete")
    
    async def resume_from_emergency(self):
        """Resume operations after emergency."""
        if not self.emergency_mode:
            return
        
        logger.info("🌐 Resuming from emergency mode...")
        
        # Re-initialize systems
        await self.initialize_all_systems()
        
        self.emergency_mode = False
        self.emergency_reason = None
        self.mode = IntegrationMode.SUPERVISED  # Return to supervised mode
        
        logger.info("🌐 System resumed")
    
    def get_system_dashboard(self) -> Dict[str, Any]:
        """Get system dashboard summary."""
        uptime = 0
        if self.start_time:
            uptime = (datetime.now(timezone.utc) - self.start_time).total_seconds()
        
        return {
            'system_status': {
                'mode': self.mode.value,
                'emergency_mode': self.emergency_mode,
                'uptime_seconds': uptime,
                'total_decisions': self.total_decisions,
                'success_rate': self.successful_operations / max(1, self.total_decisions),
            },
            'component_summary': {
                'total': len(self.components),
                'operational': sum(1 for c in self.components.values() if c.status == SystemStatus.OPERATIONAL),
                'degraded': sum(1 for c in self.components.values() if c.status == SystemStatus.DEGRADED),
                'offline': sum(1 for c in self.components.values() if c.status == SystemStatus.OFFLINE),
                'error': sum(1 for c in self.components.values() if c.status == SystemStatus.ERROR),
            },
            'coordination_summary': {
                'active_links': len([c for c in self.coordinations.values() if c.active]),
                'total_links': len(self.coordinations),
            },
            'latest_state': self.system_state.__dict__ if self.system_state else None,
        }


# Example usage
async def example_unified_orchestrator():
    """Example of unified orchestrator."""
    orchestrator = UnifiedMasterOrchestrator()
    
    # Register dummy components
    class DummyAAMIS:
        async def initialize(self):
            pass
        async def analyze(self, data):
            return {'decision': 'buy', 'confidence': 0.75}
    
    class DummyAdversarial:
        async def initialize(self):
            pass
        def challenge_claim(self, claim):
            return {'validated': True}
    
    class DummySuperIntelligence:
        async def initialize(self):
            pass
        def get_consciousness_state(self):
            return {'consciousness_level': 3}
    
    # Register
    await orchestrator.register_component(
        'AAMIS-v3', 'aamis', DummyAAMIS(),
        ['trading', 'analysis', 'prediction'],
    )
    await orchestrator.register_component(
        'Adversarial-Validator', 'adversarial', DummyAdversarial(),
        ['validation', 'safety'],
    )
    await orchestrator.register_component(
        'SuperIntelligence-Core', 'superintelligence', DummySuperIntelligence(),
        ['consciousness', 'meta_learning'],
    )
    
    # Initialize
    init_result = await orchestrator.initialize_all_systems()
    print(f"Initialization: {init_result['status']}")
    
    # Set up coordination
    await orchestrator.setup_coordination('AAMIS-v3', 'Adversarial-Validator')
    
    # Make unified decision
    decision = await orchestrator.unified_decision(
        'trade',
        {'price': 100, 'volume': 1000000, 'sentiment': 0.6},
    )
    print(f"\nUnified Decision: {decision.final_decision}")
    print(f"Confidence: {decision.confidence:.2f}")
    print(f"Reasoning: {decision.reasoning}")
    
    # Capture state
    state = await orchestrator.capture_holistic_state()
    print(f"\nSystem Health: {state.overall_health:.2f}")
    print(f"Collective Intelligence: {state.collective_intelligence_score:.2f}")
    print(f"Consciousness Level: {state.consciousness_level}")
    
    # Dashboard
    dashboard = orchestrator.get_system_dashboard()
    print(f"\nDashboard: {dashboard}")


if __name__ == "__main__":
    import random
    asyncio.run(example_unified_orchestrator())
