"""
Meta-Orchestrator
Orchestrates the orchestrators - highest level of system coordination.
"""

import asyncio
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class SystemObjective:
    objective_id: str
    title: str
    description: str
    priority: float
    target_metrics: Dict[str, float]
    current_metrics: Dict[str, float]
    progress: float
    created_at: datetime


class MetaOrchestrator:
    """
    Meta-level orchestrator that coordinates all other orchestrators.
    Ensures global coherence and optimal system-wide behavior.
    """
    
    def __init__(self, superintelligence):
        self.superintelligence = superintelligence
        self.objectives: List[SystemObjective] = []
        
        self.running = False
        
        logger.info("Meta-Orchestrator initialized")
    
    async def initialize(self):
        """Initialize meta-orchestrator."""
        logger.info("Initializing Meta-Orchestrator")
        
        await self._define_system_objectives()
        
        self.running = True
        logger.info("Meta-Orchestrator ready")
    
    async def _define_system_objectives(self):
        """Define high-level system objectives."""
        self.objectives = [
            SystemObjective(
                objective_id="obj_profit",
                title="Maximize Profitability",
                description="Achieve maximum risk-adjusted returns",
                priority=1.0,
                target_metrics={'sharpe_ratio': 3.0, 'annual_return': 0.5},
                current_metrics={'sharpe_ratio': 0.0, 'annual_return': 0.0},
                progress=0.0,
                created_at=datetime.now(),
            ),
            SystemObjective(
                objective_id="obj_autonomy",
                title="Achieve Full Autonomy",
                description="Operate completely independently",
                priority=0.95,
                target_metrics={'autonomy_level': 1.0, 'human_interventions': 0},
                current_metrics={'autonomy_level': 0.5, 'human_interventions': 0},
                progress=0.5,
                created_at=datetime.now(),
            ),
            SystemObjective(
                objective_id="obj_discovery",
                title="Continuous Discovery",
                description="Discover new methods and opportunities continuously",
                priority=0.9,
                target_metrics={'discoveries_per_week': 10, 'implementation_rate': 0.8},
                current_metrics={'discoveries_per_week': 0, 'implementation_rate': 0.0},
                progress=0.0,
                created_at=datetime.now(),
            ),
            SystemObjective(
                objective_id="obj_expansion",
                title="Global Expansion",
                description="Expand to all markets and opportunities globally",
                priority=0.85,
                target_metrics={'markets_covered': 100, 'regions': 10},
                current_metrics={'markets_covered': 10, 'regions': 1},
                progress=0.1,
                created_at=datetime.now(),
            ),
        ]
        
        logger.info("Defined %d system objectives", len(self.objectives))
    
    async def coordinate_systems(self):
        """Coordinate all subsystems toward objectives."""
        logger.info("Starting meta-coordination")
        
        while self.running:
            try:
                await self._assess_progress()
                
                await self._align_systems()
                
                await self._optimize_global_strategy()
                
                await asyncio.sleep(300)
                
            except Exception as e:
                logger.error("Error in meta-coordination: %s", e)
                await asyncio.sleep(60)
    
    async def _assess_progress(self):
        """Assess progress toward objectives."""
        status = await self.superintelligence.get_comprehensive_status()
        
        for objective in self.objectives:
            if objective.objective_id == "obj_autonomy":
                objective.current_metrics['autonomy_level'] = status['core']['autonomy_level']
                objective.progress = objective.current_metrics['autonomy_level']
            
            elif objective.objective_id == "obj_discovery":
                objective.current_metrics['discoveries_per_week'] = status['research']['total_discoveries']
                objective.progress = min(objective.current_metrics['discoveries_per_week'] / 10, 1.0)
            
            elif objective.objective_id == "obj_expansion":
                objective.current_metrics['markets_covered'] = status['opportunities']['markets_monitored']
                objective.progress = objective.current_metrics['markets_covered'] / 100
    
    async def _align_systems(self):
        """Align all systems toward common objectives."""
        for objective in self.objectives:
            if objective.progress < 0.5:
                logger.info("Objective lagging: %s (%.1f%%)", 
                          objective.title, objective.progress * 100)
                
                await self._boost_objective(objective)
    
    async def _boost_objective(self, objective: SystemObjective):
        """Boost resources toward a lagging objective."""
        if objective.objective_id == "obj_discovery":
            await self.superintelligence.agent_coordinator.create_task(
                'research',
                'Accelerate discovery process',
                0.9,
                ['research', 'experimentation']
            )
    
    async def _optimize_global_strategy(self):
        """Optimize global strategy across all systems."""
        pass
    
    def get_status(self) -> Dict[str, Any]:
        """Get meta-orchestrator status."""
        return {
            'objectives': len(self.objectives),
            'avg_progress': np.mean([o.progress for o in self.objectives]),
            'objectives_on_track': sum(1 for o in self.objectives if o.progress > 0.5),
        }
    
    async def shutdown(self):
        """Shutdown meta-orchestrator."""
        logger.info("Shutting down Meta-Orchestrator")
        self.running = False
