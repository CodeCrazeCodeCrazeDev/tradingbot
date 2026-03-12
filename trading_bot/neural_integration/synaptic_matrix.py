"""
Synaptic Connection Matrix - Maps all 100+ modules to neural network
"""

import asyncio
from typing import Dict, List, Tuple, Optional, Set
from dataclasses import dataclass, field
from enum import Enum
import logging
from pathlib import Path
import json

logger = logging.getLogger(__name__)


class ConnectionType(Enum):
    """Types of synaptic connections"""
    FEEDFORWARD = "feedforward"      # Data flows forward
    FEEDBACK = "feedback"            # Recurrent connection
    LATERAL = "lateral"              # Same-layer connection
    INHIBITORY = "inhibitory"        # Suppressing connection
    MODULATORY = "modulatory"        # Modulating connection


@dataclass
class ModuleMapping:
    """Maps a directory/module to neural architecture"""
    directory: str
    brain_region: str
    neural_type: str
    connections: List[Tuple[str, float, ConnectionType]] = field(default_factory=list)
    priority: int = 5
    description: str = ""


class ModuleSynapticMatrix:
    """
    Complete mapping of all 100+ modules to neural connections
    
    This creates the "connectome" - a complete map of neural connections
    """
    
    def __init__(self):
        self.module_mappings: Dict[str, ModuleMapping] = {}
        self.connection_matrix: Dict[str, Dict[str, float]] = {}
        self._build_complete_matrix()
        
    def _build_complete_matrix(self):
        """Build the complete synaptic matrix for all modules"""
        
        # CORE INFRASTRUCTURE (Brain Stem)
        self._add_mapping("core", "brain_stem", "core_neuron", [
            ("infrastructure", 1.0, ConnectionType.FEEDFORWARD),
            ("security", 0.9, ConnectionType.MODULATORY),
            ("system_supervisor", 0.9, ConnectionType.MODULATORY),
        ])
        
        self._add_mapping("infrastructure", "brain_stem", "infrastructure_neuron", [
            ("core", 0.8, ConnectionType.FEEDBACK),
            ("connectivity", 1.0, ConnectionType.FEEDFORWARD),
            ("database", 0.9, ConnectionType.FEEDFORWARD),
        ])
        
        self._add_mapping("security", "brain_stem", "security_neuron", [
            ("core", 1.0, ConnectionType.MODULATORY),
            ("stealth_safety", 0.9, ConnectionType.LATERAL),
            ("anti_rogue_ai", 0.8, ConnectionType.LATERAL),
        ])
        
        self._add_mapping("system_supervisor", "brain_stem", "supervisor_neuron", [
            ("core", 1.0, ConnectionType.MODULATORY),
            ("monitoring", 0.9, ConnectionType.FEEDFORWARD),
            ("diagnostics", 0.9, ConnectionType.FEEDFORWARD),
        ])
        
        self._add_mapping("connectivity", "brain_stem", "connectivity_neuron", [
            ("infrastructure", 0.9, ConnectionType.FEEDBACK),
            ("data_feeds", 1.0, ConnectionType.FEEDFORWARD),
            ("streaming", 0.9, ConnectionType.FEEDFORWARD),
        ])
        
        self._add_mapping("database", "brain_stem", "memory_neuron", [
            ("infrastructure", 0.8, ConnectionType.FEEDBACK),
            ("persistence", 0.9, ConnectionType.LATERAL),
            ("event_pipeline", 0.8, ConnectionType.FEEDFORWARD),
        ])
        
        # DATA & INTELLIGENCE (Thalamus -> Neocortex)
        self._add_mapping("data", "thalamus", "sensory_neuron", [
            ("market_intelligence", 1.0, ConnectionType.FEEDFORWARD),
            ("deepchart", 0.9, ConnectionType.FEEDFORWARD),
            ("ai_core", 0.8, ConnectionType.FEEDFORWARD),
        ])
        
        self._add_mapping("data_feeds", "thalamus", "sensory_neuron", [
            ("data", 0.9, ConnectionType.LATERAL),
            ("ingestion", 0.9, ConnectionType.FEEDFORWARD),
            ("streaming", 0.8, ConnectionType.LATERAL),
        ])
        
        self._add_mapping("market_intelligence", "thalamus", "perception_neuron", [
            ("data", 0.8, ConnectionType.FEEDBACK),
            ("ai_core", 1.0, ConnectionType.FEEDFORWARD),
            ("advanced_analysis", 0.9, ConnectionType.FEEDFORWARD),
            ("deepchart", 0.8, ConnectionType.LATERAL),
        ])
        
        self._add_mapping("deepchart", "thalamus", "visual_cortex_neuron", [
            ("market_intelligence", 0.9, ConnectionType.LATERAL),
            ("ai_core", 0.9, ConnectionType.FEEDFORWARD),
            ("perplexity_trading", 0.7, ConnectionType.FEEDFORWARD),
        ])
        
        self._add_mapping("ingestion", "thalamus", "input_neuron", [
            ("data_feeds", 0.9, ConnectionType.FEEDBACK),
            ("research_ingestion", 0.8, ConnectionType.LATERAL),
            ("alternative_data", 0.7, ConnectionType.FEEDFORWARD),
        ])
        
        # AI CORE INTELLIGENCE (Neocortex)
        self._add_mapping("ai_core", "neocortex", "cognitive_neuron", [
            ("market_intelligence", 0.8, ConnectionType.FEEDBACK),
            ("advanced_ai", 0.9, ConnectionType.LATERAL),
            ("ml", 0.9, ConnectionType.FEEDFORWARD),
            ("execution", 0.7, ConnectionType.FEEDFORWARD),
            ("risk", 0.6, ConnectionType.FEEDFORWARD),
        ])
        
        self._add_mapping("advanced_ai", "neocortex", "intelligence_neuron", [
            ("ai_core", 0.9, ConnectionType.LATERAL),
            ("alpha_engine", 0.9, ConnectionType.LATERAL),
            ("superintelligence", 0.8, ConnectionType.FEEDFORWARD),
            ("neuros_evolution", 0.7, ConnectionType.FEEDFORWARD),
        ])
        
        self._add_mapping("advanced_analysis", "neocortex", "analysis_neuron", [
            ("market_intelligence", 0.8, ConnectionType.FEEDBACK),
            ("ai_core", 0.9, ConnectionType.FEEDFORWARD),
            ("alpha_research", 0.8, ConnectionType.LATERAL),
        ])
        
        self._add_mapping("alpha_engine", "neocortex", "alpha_neuron", [
            ("advanced_ai", 0.9, ConnectionType.LATERAL),
            ("elite_ai_system", 0.9, ConnectionType.LATERAL),
            ("execution", 0.8, ConnectionType.FEEDFORWARD),
            ("risk_management", 0.7, ConnectionType.FEEDFORWARD),
        ])
        
        self._add_mapping("alpha_research", "neocortex", "research_neuron", [
            ("advanced_analysis", 0.8, ConnectionType.LATERAL),
            ("perplexity_trading", 0.9, ConnectionType.LATERAL),
            ("intelligence_core", 0.8, ConnectionType.FEEDFORWARD),
        ])
        
        self._add_mapping("elite_ai_system", "neocortex", "elite_neuron", [
            ("alpha_engine", 0.9, ConnectionType.LATERAL),
            ("superintelligence", 0.9, ConnectionType.LATERAL),
            ("hivemind", 0.8, ConnectionType.LATERAL),
        ])
        
        self._add_mapping("intelligence_core", "neocortex", "intellect_neuron", [
            ("alpha_research", 0.8, ConnectionType.FEEDBACK),
            ("cognitive_architecture", 0.9, ConnectionType.LATERAL),
            ("systems_ai", 0.8, ConnectionType.FEEDFORWARD),
        ])
        
        self._add_mapping("superintelligence", "neocortex", "super_neuron", [
            ("elite_ai_system", 0.9, ConnectionType.LATERAL),
            ("aamis_v3", 0.9, ConnectionType.LATERAL),
            ("hivemind", 0.9, ConnectionType.LATERAL),
        ])
        
        self._add_mapping("cognitive_architecture", "neocortex", "cognitive_struct_neuron", [
            ("intelligence_core", 0.9, ConnectionType.LATERAL),
            ("reasoning", 0.8, ConnectionType.FEEDFORWARD),
            ("tamic", 0.7, ConnectionType.FEEDFORWARD),
        ])
        
        self._add_mapping("perplexity_trading", "neocortex", "research_ai_neuron", [
            ("alpha_research", 0.9, ConnectionType.LATERAL),
            ("reasoning", 0.8, ConnectionType.FEEDFORWARD),
            ("hivemind", 0.7, ConnectionType.FEEDFORWARD),
        ])
        
        self._add_mapping("hivemind", "neocortex", "collective_neuron", [
            ("elite_ai_system", 0.8, ConnectionType.LATERAL),
            ("superintelligence", 0.9, ConnectionType.LATERAL),
            ("aamis_v3", 0.8, ConnectionType.LATERAL),
            ("execution", 0.7, ConnectionType.FEEDFORWARD),
        ])
        
        self._add_mapping("aamis_v3", "neocortex", "market_ai_neuron", [
            ("superintelligence", 0.9, ConnectionType.LATERAL),
            ("hivemind", 0.8, ConnectionType.LATERAL),
            ("market_student", 0.7, ConnectionType.FEEDFORWARD),
        ])
        
        self._add_mapping("tamic", "neocortex", "time_ai_neuron", [
            ("cognitive_architecture", 0.7, ConnectionType.FEEDBACK),
            ("systems_ai", 0.8, ConnectionType.LATERAL),
            ("realtime", 0.9, ConnectionType.FEEDFORWARD),
        ])
        
        self._add_mapping("systems_ai", "neocortex", "system_intelligence_neuron", [
            ("intelligence_core", 0.8, ConnectionType.FEEDBACK),
            ("tamic", 0.8, ConnectionType.LATERAL),
            ("governance", 0.7, ConnectionType.FEEDFORWARD),
        ])
        
        self._add_mapping("reasoning", "neocortex", "logic_neuron", [
            ("cognitive_architecture", 0.8, ConnectionType.FEEDBACK),
            ("perplexity_trading", 0.8, ConnectionType.FEEDBACK),
            ("ai_core", 0.7, ConnectionType.FEEDBACK),
        ])
        
        # ML SUBSYSTEMS (Neocortex - Deep)
        self._add_mapping("ml", "neocortex", "ml_neuron", [
            ("ai_core", 0.8, ConnectionType.FEEDBACK),
            ("meta_learning", 0.9, ConnectionType.FEEDFORWARD),
            ("offline_rl", 0.8, ConnectionType.LATERAL),
        ])
        
        self._add_mapping("meta_learning", "neocortex", "meta_neuron", [
            ("ml", 0.9, ConnectionType.FEEDBACK),
            ("continual", 0.9, ConnectionType.LATERAL),
            ("adaptive_systems", 0.8, ConnectionType.FEEDFORWARD),
        ])
        
        self._add_mapping("offline_rl", "neocortex", "rl_neuron", [
            ("ml", 0.8, ConnectionType.FEEDBACK),
            ("continual", 0.9, ConnectionType.LATERAL),
            ("evolution_layer", 0.7, ConnectionType.FEEDFORWARD),
        ])
        
        self._add_mapping("continual", "neocortex", "continual_neuron", [
            ("meta_learning", 0.9, ConnectionType.LATERAL),
            ("offline_rl", 0.9, ConnectionType.LATERAL),
            ("self_learning", 0.8, ConnectionType.FEEDFORWARD),
        ])
        
        # RISK & EMOTION (Limbic System)
        self._add_mapping("risk", "limbic_system", "risk_neuron", [
            ("ai_core", 0.6, ConnectionType.FEEDBACK),
            ("risk_management", 0.9, ConnectionType.LATERAL),
            ("execution", 0.5, ConnectionType.INHIBITORY),
        ])
        
        self._add_mapping("risk_management", "limbic_system", "risk_mgmt_neuron", [
            ("risk", 0.9, ConnectionType.LATERAL),
            ("hedge_fund_safety", 0.8, ConnectionType.LATERAL),
            ("portfolio", 0.7, ConnectionType.FEEDFORWARD),
        ])
        
        self._add_mapping("hedge_fund_safety", "limbic_system", "safety_neuron", [
            ("risk_management", 0.8, ConnectionType.LATERAL),
            ("stealth_safety", 0.9, ConnectionType.LATERAL),
            ("msos", 0.8, ConnectionType.FEEDFORWARD),
        ])
        
        self._add_mapping("stealth_safety", "limbic_system", "stealth_neuron", [
            ("hedge_fund_safety", 0.9, ConnectionType.LATERAL),
            ("security", 0.8, ConnectionType.FEEDBACK),
            ("anti_rogue_ai", 0.7, ConnectionType.LATERAL),
        ])
        
        self._add_mapping("msos", "limbic_system", "survival_neuron", [
            ("hedge_fund_safety", 0.8, ConnectionType.FEEDBACK),
            ("market_student", 0.6, ConnectionType.FEEDFORWARD),
            ("execution", 0.5, ConnectionType.INHIBITORY),
        ])
        
        self._add_mapping("anti_rogue_ai", "limbic_system", "protection_neuron", [
            ("stealth_safety", 0.7, ConnectionType.LATERAL),
            ("security", 0.9, ConnectionType.FEEDBACK),
            ("governance", 0.8, ConnectionType.FEEDFORWARD),
        ])
        
        self._add_mapping("psychology", "limbic_system", "emotion_neuron", [
            ("sentiment", 0.9, ConnectionType.LATERAL),
            ("market_student", 0.7, ConnectionType.FEEDFORWARD),
            ("risk", 0.6, ConnectionType.MODULATORY),
        ])
        
        self._add_mapping("sentiment", "limbic_system", "sentiment_neuron", [
            ("psychology", 0.9, ConnectionType.LATERAL),
            ("social", 0.8, ConnectionType.LATERAL),
            ("ai_core", 0.5, ConnectionType.MODULATORY),
        ])
        
        self._add_mapping("market_student", "limbic_system", "learning_emotion_neuron", [
            ("psychology", 0.7, ConnectionType.FEEDBACK),
            ("market_teacher", 0.9, ConnectionType.LATERAL),
            ("self_mastery", 0.8, ConnectionType.FEEDFORWARD),
        ])
        
        self._add_mapping("market_teacher", "limbic_system", "teaching_emotion_neuron", [
            ("market_student", 0.9, ConnectionType.LATERAL),
            ("self_mastery", 0.9, ConnectionType.FEEDFORWARD),
            ("learning", 0.8, ConnectionType.FEEDFORWARD),
        ])
        
        # EXECUTION (Cerebellum)
        self._add_mapping("execution", "cerebellum", "motor_neuron", [
            ("ai_core", 0.7, ConnectionType.FEEDBACK),
            ("risk", 0.5, ConnectionType.INHIBITORY),
            ("broker", 1.0, ConnectionType.FEEDFORWARD),
            ("exits", 0.8, ConnectionType.FEEDFORWARD),
        ])
        
        self._add_mapping("broker", "cerebellum", "broker_neuron", [
            ("execution", 0.9, ConnectionType.FEEDBACK),
            ("brokers", 0.9, ConnectionType.LATERAL),
            ("connectors", 0.8, ConnectionType.LATERAL),
        ])
        
        self._add_mapping("brokers", "cerebellum", "brokers_neuron", [
            ("broker", 0.9, ConnectionType.LATERAL),
            ("bridges", 0.7, ConnectionType.LATERAL),
        ])
        
        self._add_mapping("exits", "cerebellum", "exit_neuron", [
            ("execution", 0.8, ConnectionType.FEEDBACK),
            ("exit_strategies", 0.9, ConnectionType.LATERAL),
            ("profit_maximizer", 0.7, ConnectionType.MODULATORY),
        ])
        
        self._add_mapping("exit_strategies", "cerebellum", "strategy_exit_neuron", [
            ("exits", 0.9, ConnectionType.LATERAL),
            ("elite_evolution", 0.6, ConnectionType.MODULATORY),
        ])
        
        self._add_mapping("elite_evolution", "cerebellum", "elite_motor_neuron", [
            ("execution", 0.6, ConnectionType.MODULATORY),
            ("alphaalgo_v2", 0.8, ConnectionType.LATERAL),
        ])
        
        self._add_mapping("alphaalgo_v2", "cerebellum", "alphaalgo_motor_neuron", [
            ("elite_evolution", 0.8, ConnectionType.LATERAL),
            ("alphaalgo_institutional", 0.9, ConnectionType.LATERAL),
            ("apex_fi", 0.7, ConnectionType.FEEDFORWARD),
        ])
        
        self._add_mapping("alphaalgo_institutional", "cerebellum", "institutional_neuron", [
            ("alphaalgo_v2", 0.9, ConnectionType.LATERAL),
            ("hedge_fund", 0.8, ConnectionType.LATERAL),
        ])
        
        self._add_mapping("apex_fi", "cerebellum", "apex_neuron", [
            ("alphaalgo_v2", 0.7, ConnectionType.FEEDBACK),
            ("hedge_fund", 0.9, ConnectionType.FEEDFORWARD),
        ])
        
        self._add_mapping("hedge_fund", "cerebellum", "fund_neuron", [
            ("alphaalgo_institutional", 0.8, ConnectionType.FEEDBACK),
            ("apex_fi", 0.9, ConnectionType.FEEDBACK),
            ("portfolio", 0.9, ConnectionType.FEEDFORWARD),
        ])
        
        self._add_mapping("market_making", "cerebellum", "mm_neuron", [
            ("execution", 0.7, ConnectionType.LATERAL),
            ("hft", 0.8, ConnectionType.LATERAL),
        ])
        
        self._add_mapping("hft", "cerebellum", "hft_neuron", [
            ("market_making", 0.8, ConnectionType.LATERAL),
            ("realtime", 0.9, ConnectionType.FEEDBACK),
        ])
        
        self._add_mapping("arbitrage", "cerebellum", "arb_neuron", [
            ("execution", 0.8, ConnectionType.FEEDBACK),
            ("market_making", 0.7, ConnectionType.LATERAL),
        ])
        
        self._add_mapping("profit_maximizer", "cerebellum", "profit_neuron", [
            ("exits", 0.7, ConnectionType.MODULATORY),
            ("portfolio", 0.8, ConnectionType.FEEDBACK),
        ])
        
        # LEARNING & MEMORY (Hippocampus)
        self._add_mapping("learning", "hippocampus", "learning_neuron", [
            ("market_teacher", 0.8, ConnectionType.FEEDBACK),
            ("self_learning", 0.9, ConnectionType.LATERAL),
            ("continual", 0.7, ConnectionType.FEEDBACK),
        ])
        
        self._add_mapping("self_learning", "hippocampus", "self_learn_neuron", [
            ("learning", 0.9, ConnectionType.LATERAL),
            ("self_mastery", 0.9, ConnectionType.LATERAL),
            ("eternal_evolution", 0.8, ConnectionType.FEEDFORWARD),
        ])
        
        self._add_mapping("self_mastery", "hippocampus", "mastery_neuron", [
            ("self_learning", 0.9, ConnectionType.LATERAL),
            ("market_teacher", 0.9, ConnectionType.FEEDBACK),
            ("recursive_evolution", 0.7, ConnectionType.FEEDFORWARD),
        ])
        
        self._add_mapping("eternal_evolution", "hippocampus", "eternal_neuron", [
            ("self_learning", 0.8, ConnectionType.FEEDBACK),
            ("recursive_evolution", 0.9, ConnectionType.LATERAL),
            ("unified_evolution", 0.9, ConnectionType.LATERAL),
        ])
        
        self._add_mapping("recursive_evolution", "hippocampus", "recursive_neuron", [
            ("self_mastery", 0.7, ConnectionType.FEEDBACK),
            ("eternal_evolution", 0.9, ConnectionType.LATERAL),
            ("evolution_layer", 0.9, ConnectionType.FEEDFORWARD),
        ])
        
        self._add_mapping("evolution_layer", "hippocampus", "evo_layer_neuron", [
            ("recursive_evolution", 0.9, ConnectionType.FEEDBACK),
            ("unified_evolution", 0.9, ConnectionType.LATERAL),
            ("offline_rl", 0.7, ConnectionType.FEEDBACK),
        ])
        
        self._add_mapping("unified_evolution", "hippocampus", "unified_neuron", [
            ("eternal_evolution", 0.9, ConnectionType.LATERAL),
            ("evolution_layer", 0.9, ConnectionType.FEEDBACK),
        ])
        
        self._add_mapping("adaptive_systems", "hippocampus", "adaptive_neuron", [
            ("meta_learning", 0.8, ConnectionType.FEEDBACK),
            ("evolution_layer", 0.7, ConnectionType.MODULATORY),
        ])
        
        self._add_mapping("adversarial_curriculum", "hippocampus", "adversarial_neuron", [
            ("learning", 0.7, ConnectionType.FEEDBACK),
            ("training", 0.9, ConnectionType.FEEDFORWARD),
        ])
        
        self._add_mapping("training", "hippocampus", "training_neuron", [
            ("adversarial_curriculum", 0.9, ConnectionType.FEEDBACK),
            ("ml", 0.8, ConnectionType.FEEDBACK),
        ])
        
        # MONITORING (Hypothalamus)
        self._add_mapping("monitoring", "hypothalamus", "monitor_neuron", [
            ("system_supervisor", 0.9, ConnectionType.FEEDBACK),
            ("observability", 0.9, ConnectionType.LATERAL),
            ("analytics", 0.8, ConnectionType.FEEDFORWARD),
        ])
        
        self._add_mapping("observability", "hypothalamus", "observe_neuron", [
            ("monitoring", 0.9, ConnectionType.LATERAL),
            ("telemetry", 0.8, ConnectionType.FEEDFORWARD),
            ("metrics", 0.7, ConnectionType.FEEDFORWARD),
        ])
        
        self._add_mapping("analytics", "hypothalamus", "analytics_neuron", [
            ("monitoring", 0.8, ConnectionType.FEEDBACK),
            ("metrics", 0.9, ConnectionType.LATERAL),
        ])
        
        self._add_mapping("diagnostics", "hypothalamus", "diagnostic_neuron", [
            ("system_supervisor", 0.9, ConnectionType.FEEDBACK),
            ("self_diagnostic", 0.9, ConnectionType.LATERAL),
        ])
        
        self._add_mapping("self_diagnostic", "hypothalamus", "self_diag_neuron", [
            ("diagnostics", 0.9, ConnectionType.LATERAL),
            ("self_healing_ai", 0.8, ConnectionType.FEEDFORWARD),
        ])
        
        self._add_mapping("self_healing_ai", "hypothalamus", "healing_neuron", [
            ("self_diagnostic", 0.8, ConnectionType.FEEDBACK),
            ("auto_optimizer", 0.7, ConnectionType.FEEDFORWARD),
        ])
        
        self._add_mapping("telemetry", "hypothalamus", "telemetry_neuron", [
            ("observability", 0.8, ConnectionType.FEEDBACK),
            ("verification", 0.7, ConnectionType.FEEDFORWARD),
        ])
        
        self._add_mapping("metrics", "hypothalamus", "metrics_neuron", [
            ("analytics", 0.9, ConnectionType.FEEDBACK),
            ("telemetry", 0.7, ConnectionType.LATERAL),
        ])
        
        self._add_mapping("verification", "hypothalamus", "verify_neuron", [
            ("telemetry", 0.7, ConnectionType.FEEDBACK),
            ("validation", 0.9, ConnectionType.LATERAL),
        ])
        
        self._add_mapping("validation", "hypothalamus", "validate_neuron", [
            ("verification", 0.9, ConnectionType.LATERAL),
            ("audit", 0.8, ConnectionType.FEEDFORWARD),
        ])
        
        self._add_mapping("audit", "hypothalamus", "audit_neuron", [
            ("validation", 0.8, ConnectionType.FEEDBACK),
            ("compliance", 0.7, ConnectionType.FEEDFORWARD),
        ])
        
        self._add_mapping("auto_optimizer", "hypothalamus", "optimizer_neuron", [
            ("self_healing_ai", 0.7, ConnectionType.FEEDBACK),
            ("improvements", 0.8, ConnectionType.FEEDFORWARD),
        ])
        
        logger.info(f"✅ Synaptic matrix built: {len(self.module_mappings)} modules mapped")
    
    def _add_mapping(self, directory: str, brain_region: str, neural_type: str, 
                     connections: List[Tuple[str, float, ConnectionType]], 
                     priority: int = 5):
        """Add a module mapping"""
        self.module_mappings[directory] = ModuleMapping(
            directory=directory,
            brain_region=brain_region,
            neural_type=neural_type,
            connections=connections,
            priority=priority,
            description=f"{directory} -> {brain_region}"
        )
        
    def get_module_region(self, module_name: str) -> Optional[str]:
        """Get brain region for a module"""
        # Direct match
        if module_name in self.module_mappings:
            return self.module_mappings[module_name].brain_region
        
        # Pattern match
        for key, mapping in self.module_mappings.items():
            if key in module_name or module_name in key:
                return mapping.brain_region
        
        return None
    
    def get_connections(self, module_name: str) -> List[Tuple[str, float, ConnectionType]]:
        """Get synaptic connections for a module"""
        if module_name in self.module_mappings:
            return self.module_mappings[module_name].connections
        
        # Pattern match
        for key, mapping in self.module_mappings.items():
            if key in module_name or module_name in key:
                return mapping.connections
        
        return []
    
    def get_all_modules_in_region(self, region: str) -> List[str]:
        """Get all modules in a brain region"""
        return [
            m.directory for m in self.module_mappings.values()
            if m.brain_region == region
        ]
    
    def get_connectome_stats(self) -> Dict:
        """Get statistics about the neural connectome"""
        region_counts = {}
        connection_counts = {}
        total_connections = 0
        
        for mapping in self.module_mappings.values():
            region = mapping.brain_region
            region_counts[region] = region_counts.get(region, 0) + 1
            
            conn_count = len(mapping.connections)
            connection_counts[mapping.directory] = conn_count
            total_connections += conn_count
        
        return {
            'total_modules': len(self.module_mappings),
            'total_connections': total_connections,
            'avg_connections_per_module': total_connections / len(self.module_mappings) if self.module_mappings else 0,
            'modules_per_region': region_counts,
            'connection_distribution': {
                'highly_connected (>10)': len([c for c in connection_counts.values() if c > 10]),
                'moderately_connected (5-10)': len([c for c in connection_counts.values() if 5 <= c <= 10]),
                'lightly_connected (<5)': len([c for c in connection_counts.values() if c < 5]),
            }
        }
    
    def export_connectome(self, filepath: str):
        """Export the connectome to JSON"""
        connectome = {
            'modules': {
                name: {
                    'brain_region': m.brain_region,
                    'neural_type': m.neural_type,
                    'priority': m.priority,
                    'connections': [
                        {'target': c[0], 'weight': c[1], 'type': c[2].value}
                        for c in m.connections
                    ]
                }
                for name, m in self.module_mappings.items()
            },
            'stats': self.get_connectome_stats()
        }
        
        with open(filepath, 'w') as f:
            json.dump(connectome, f, indent=2)
        
        logger.info(f"💾 Connectome exported to {filepath}")


# Create global synaptic matrix
SYNAPTIC_MATRIX = ModuleSynapticMatrix()


def get_module_brain_region(module_name: str) -> str:
    """Get brain region for any module"""
    region = SYNAPTIC_MATRIX.get_module_region(module_name)
    return region or "unknown"


def get_module_connections(module_name: str) -> List[Tuple[str, float, ConnectionType]]:
    """Get connections for any module"""
    return SYNAPTIC_MATRIX.get_connections(module_name)


if __name__ == "__main__":
    # Test the matrix
    stats = SYNAPTIC_MATRIX.get_connectome_stats()
    print(f"\nConnectome Statistics:")
    print(f"Total Modules: {stats['total_modules']}")
    print(f"Total Connections: {stats['total_connections']}")
    print(f"Avg Connections/Module: {stats['avg_connections_per_module']:.1f}")
    print(f"\nModules per Brain Region:")
    for region, count in stats['modules_per_region'].items():
        print(f"  {region}: {count}")
    
    # Export
    SYNAPTIC_MATRIX.export_connectome("neural_connectome.json")
