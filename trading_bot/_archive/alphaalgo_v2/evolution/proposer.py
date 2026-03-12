"""
AlphaAlgo V2 Proposal Generator

Generates improvement proposals based on analysis.
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
from datetime import datetime
import uuid

from ..core.types import EvolutionProposal, ProposalStatus
from ..core.constants import EVOLUTION_CATEGORIES, EvolutionApprovalLevel

import logging
logger = logging.getLogger(__name__)



@dataclass
class Proposal:
    """Improvement proposal"""
    id: str
    title: str
    description: str
    category: str
    priority: int
    changes: Dict[str, Any]
    requires_human_approval: bool = False


class ProposalGenerator:
    """
    Generates improvement proposals
    
    Creates proposals for:
    - Parameter tuning
    - Model retraining
    - Strategy adjustments
    - System optimizations
    """
    
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
    
    def generate(
        self,
        opportunities: List[Dict[str, Any]]
    ) -> List[EvolutionProposal]:
        """
        Generate proposals from opportunities
        
        Args:
            opportunities: List of identified opportunities
            
        Returns:
            List of proposals
        """
        proposals = []
        
        for opp in opportunities:
            category = opp.get("type", "unknown")
            approval_level = EVOLUTION_CATEGORIES.get(
                category,
                EvolutionApprovalLevel.HUMAN
            )
            
            proposal = EvolutionProposal(
                id=str(uuid.uuid4()),
                title=f"Improve {opp.get('target', 'system')}",
                description=opp.get("description", ""),
                category=category,
                priority=opp.get("priority", 3),
                requires_human_approval=(
                    approval_level == EvolutionApprovalLevel.HUMAN
                ),
                status=ProposalStatus.PENDING,
                changes=opp.get("changes", {}),
            )
            
            proposals.append(proposal)
        
        return sorted(proposals, key=lambda p: p.priority)
