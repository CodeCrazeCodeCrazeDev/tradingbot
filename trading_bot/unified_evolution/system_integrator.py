"""
System Integrator
=================

Integrates recursive evolution with all advanced trading systems:
- AAMIS v3, TAMIC, Adaptive Systems, Advanced Analysis, Advanced ML, Adversarial Decision

Enables cross-system learning and knowledge transfer.
"""

import logging
import numpy as np
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from collections import defaultdict

logger = logging.getLogger(__name__)


class SystemType(Enum):
    """Types of advanced systems"""
    AAMIS_V3 = "aamis_v3"
    TAMIC = "tamic"
    ADAPTIVE_SYSTEMS = "adaptive_systems"
    ADVANCED_ANALYSIS = "advanced_analysis"
    ADVANCED_FEATURES = "advanced_features"
    ADVANCED_ML = "advanced_ml"
    ADVERSARIAL_DECISION = "adversarial_decision"


@dataclass
class IntegrationPoint:
    """Integration point between systems"""
    source_system: SystemType
    target_system: SystemType
    integration_type: str  # data_flow, model_sharing, knowledge_transfer
    bidirectional: bool
    active: bool = True
    
    # Transfer metrics
    transfers_count: int = 0
    success_rate: float = 0.0
    avg_improvement: float = 0.0
    
    created_at: datetime = field(default_factory=datetime.utcnow)


@dataclass
class CrossSystemLearning:
    """Cross-system learning record"""
    learning_id: str
    source_system: SystemType
    target_system: SystemType
    
    knowledge_type: str  # pattern, strategy, parameter, architecture
    knowledge_content: Dict[str, Any]
    
    transfer_method: str  # direct, adapted, distilled
    success: bool
    improvement: float
    
    timestamp: datetime = field(default_factory=datetime.utcnow)


class SystemIntegrator:
    """
    Integrates recursive evolution across all advanced trading systems.
    Enables cross-system learning and knowledge transfer.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        
        # System registry
        self.systems: Dict[SystemType, Any] = {}
        self.system_metadata: Dict[SystemType, Dict[str, Any]] = {}
        
        # Integration points
        self.integration_points: List[IntegrationPoint] = []
        
        # Cross-system learning
        self.learning_records: List[CrossSystemLearning] = []
        self.knowledge_graph: Dict[str, List[str]] = defaultdict(list)
        
        # Initialize integration points
        self._initialize_integration_points()
        
        logger.info("SystemIntegrator initialized")
    
    def _initialize_integration_points(self):
        """Initialize integration points between systems"""
        
        # AAMIS v3 ↔ TAMIC (time-aware intelligence)
        self.integration_points.append(IntegrationPoint(
            source_system=SystemType.AAMIS_V3,
            target_system=SystemType.TAMIC,
            integration_type="data_flow",
            bidirectional=True
        ))
        
        # AAMIS v3 ↔ Adaptive Systems (adaptive intelligence)
        self.integration_points.append(IntegrationPoint(
            source_system=SystemType.AAMIS_V3,
            target_system=SystemType.ADAPTIVE_SYSTEMS,
            integration_type="model_sharing",
            bidirectional=True
        ))
        
        # TAMIC ↔ Adaptive Systems (time-aware adaptation)
        self.integration_points.append(IntegrationPoint(
            source_system=SystemType.TAMIC,
            target_system=SystemType.ADAPTIVE_SYSTEMS,
            integration_type="knowledge_transfer",
            bidirectional=True
        ))
        
        # Advanced ML → All Systems (model improvements)
        for system in [SystemType.AAMIS_V3, SystemType.TAMIC, SystemType.ADAPTIVE_SYSTEMS]:
            self.integration_points.append(IntegrationPoint(
                source_system=SystemType.ADVANCED_ML,
                target_system=system,
                integration_type="model_sharing",
                bidirectional=False
            ))
        
        # Adversarial Decision → All Systems (robustness)
        for system in [SystemType.AAMIS_V3, SystemType.TAMIC, SystemType.ADAPTIVE_SYSTEMS]:
            self.integration_points.append(IntegrationPoint(
                source_system=SystemType.ADVERSARIAL_DECISION,
                target_system=system,
                integration_type="knowledge_transfer",
                bidirectional=False
            ))
        
        # Advanced Analysis ↔ All Systems (pattern insights)
        for system in [SystemType.AAMIS_V3, SystemType.ADAPTIVE_SYSTEMS]:
            self.integration_points.append(IntegrationPoint(
                source_system=SystemType.ADVANCED_ANALYSIS,
                target_system=system,
                integration_type="data_flow",
                bidirectional=True
            ))
        
        logger.info(f"Initialized {len(self.integration_points)} integration points")
    
    def register_system(self, system_type: SystemType, system: Any,
                       metadata: Optional[Dict[str, Any]] = None):
        """Register a system for integration"""
        
        self.systems[system_type] = system
        self.system_metadata[system_type] = metadata or {}
        
        logger.info(f"Registered system: {system_type.value}")
    
    def transfer_knowledge(self, source: SystemType, target: SystemType,
                          knowledge_type: str, knowledge: Dict[str, Any]) -> CrossSystemLearning:
        """Transfer knowledge from one system to another"""
        
        learning_id = f"XFER-{source.value[:5]}-{target.value[:5]}-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"
        
        # Find integration point
        integration = self._find_integration_point(source, target)
        if not integration:
            logger.warning(f"No integration point between {source.value} and {target.value}")
            return None
        
        # Determine transfer method
        if knowledge_type == "pattern":
            transfer_method = "adapted"
        elif knowledge_type == "architecture":
            transfer_method = "distilled"
        else:
            transfer_method = "direct"
        
        # Simulate transfer (in production, this would actually transfer knowledge)
        success = np.random.random() > 0.3  # 70% success rate
        improvement = np.random.uniform(0.05, 0.15) if success else 0.0
        
        # Create learning record
        learning = CrossSystemLearning(
            learning_id=learning_id,
            source_system=source,
            target_system=target,
            knowledge_type=knowledge_type,
            knowledge_content=knowledge,
            transfer_method=transfer_method,
            success=success,
            improvement=improvement
        )
        
        self.learning_records.append(learning)
        
        # Update integration point metrics
        integration.transfers_count += 1
        if success:
            integration.success_rate = (
                (integration.success_rate * (integration.transfers_count - 1) + 1.0) /
                integration.transfers_count
            )
            integration.avg_improvement = (
                (integration.avg_improvement * (integration.transfers_count - 1) + improvement) /
                integration.transfers_count
            )
        
        # Update knowledge graph
        self.knowledge_graph[source.value].append(target.value)
        
        logger.info(f"Knowledge transfer {'successful' if success else 'failed'}: {learning_id}")
        
        return learning
    
    def _find_integration_point(self, source: SystemType, target: SystemType) -> Optional[IntegrationPoint]:
        """Find integration point between systems"""
        
        for point in self.integration_points:
            if point.source_system == source and point.target_system == target:
                return point
            if point.bidirectional and point.source_system == target and point.target_system == source:
                return point
        
        return None
    
    def discover_transferable_knowledge(self, source: SystemType) -> List[Dict[str, Any]]:
        """Discover knowledge that can be transferred from a system"""
        
        if source not in self.systems:
            return []
        
        transferable = []
        
        # Pattern knowledge
        transferable.append({
            'type': 'pattern',
            'description': f'Patterns discovered by {source.value}',
            'applicable_to': self._find_applicable_systems(source, 'pattern')
        })
        
        # Strategy knowledge
        transferable.append({
            'type': 'strategy',
            'description': f'Strategies from {source.value}',
            'applicable_to': self._find_applicable_systems(source, 'strategy')
        })
        
        # Parameter knowledge
        transferable.append({
            'type': 'parameter',
            'description': f'Optimal parameters from {source.value}',
            'applicable_to': self._find_applicable_systems(source, 'parameter')
        })
        
        # Architecture knowledge
        if source in [SystemType.ADVANCED_ML, SystemType.AAMIS_V3]:
            transferable.append({
                'type': 'architecture',
                'description': f'Model architectures from {source.value}',
                'applicable_to': self._find_applicable_systems(source, 'architecture')
            })
        
        return transferable
    
    def _find_applicable_systems(self, source: SystemType, knowledge_type: str) -> List[SystemType]:
        """Find systems that can benefit from knowledge"""
        
        applicable = []
        
        for point in self.integration_points:
            if point.source_system == source and point.active:
                applicable.append(point.target_system)
            elif point.bidirectional and point.target_system == source and point.active:
                applicable.append(point.source_system)
        
        return applicable
    
    def optimize_integration_points(self):
        """Optimize integration points based on performance"""
        
        for point in self.integration_points:
            if point.transfers_count < 5:
                continue
            
            # Disable low-performing integrations
            if point.success_rate < 0.3:
                point.active = False
                logger.warning(f"Disabled integration: {point.source_system.value} → {point.target_system.value}")
            
            # Boost high-performing integrations
            elif point.success_rate > 0.8 and point.avg_improvement > 0.1:
                logger.info(f"High-performing integration: {point.source_system.value} → {point.target_system.value}")
    
    def get_integration_stats(self) -> Dict[str, Any]:
        """Get integration statistics"""
        
        total_transfers = len(self.learning_records)
        successful_transfers = sum(1 for l in self.learning_records if l.success)
        
        success_rate = successful_transfers / total_transfers if total_transfers > 0 else 0
        
        # Average improvement
        if successful_transfers > 0:
            avg_improvement = np.mean([l.improvement for l in self.learning_records if l.success])
        else:
            avg_improvement = 0
        
        # Per-system stats
        system_stats = {}
        for system in SystemType:
            as_source = [l for l in self.learning_records if l.source_system == system]
            as_target = [l for l in self.learning_records if l.target_system == system]
            
            system_stats[system.value] = {
                'knowledge_shared': len(as_source),
                'knowledge_received': len(as_target),
                'net_contribution': len(as_source) - len(as_target)
            }
        
        # Integration point stats
        integration_stats = []
        for point in self.integration_points:
            integration_stats.append({
                'source': point.source_system.value,
                'target': point.target_system.value,
                'type': point.integration_type,
                'active': point.active,
                'transfers': point.transfers_count,
                'success_rate': point.success_rate,
                'avg_improvement': point.avg_improvement
            })
        
        return {
            'total_transfers': total_transfers,
            'successful_transfers': successful_transfers,
            'success_rate': success_rate,
            'average_improvement': avg_improvement,
            'systems_registered': len(self.systems),
            'integration_points': len(self.integration_points),
            'active_integrations': sum(1 for p in self.integration_points if p.active),
            'system_stats': system_stats,
            'integration_details': integration_stats
        }
    
    def visualize_knowledge_graph(self) -> str:
        """Generate text visualization of knowledge graph"""
        
        lines = ["Knowledge Transfer Graph:", "=" * 50]
        
        for source, targets in self.knowledge_graph.items():
            if targets:
                lines.append(f"\n{source}:")
                for target in set(targets):
                    count = targets.count(target)
                    lines.append(f"  → {target} ({count} transfers)")
        
        return "\n".join(lines)


def quick_start_integrator(config: Optional[Dict[str, Any]] = None) -> SystemIntegrator:
    """Quick start function for system integrator"""
    return SystemIntegrator(config)
