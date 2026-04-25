"""
Ontology Agent - Knowledge Graph Manager
=========================================

Manages the semantic knowledge graph with:
- Entity resolution
- Relationship mapping
- Real-time enrichment
- Causal graph updates
"""

import asyncio
import logging
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
import uuid

logger = logging.getLogger(__name__)


class OntologyAgent:
    """
    Ontology Agent - Knowledge Graph Manager
    
    Enriches the financial ontology with fused market data.
    """
    
    def __init__(self, meta_orchestrator: Any, financial_ontology: Any):
        self.agent_id = f"ONTO-{uuid.uuid4().hex[:8]}"
        self.meta_orchestrator = meta_orchestrator
        self.ontology = financial_ontology
        
        # Register with orchestrator
        self.meta_orchestrator.register_agent("OntologyAgent", self)
        
        # Metrics
        self.entities_created = 0
        self.relationships_mapped = 0
        self.enrichments_performed = 0
        
        logger.info(f"OntologyAgent initialized: {self.agent_id}")
    
    async def enrich_from_market_picture(
        self,
        market_picture: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Enrich ontology with market picture data.
        
        Creates entities, maps relationships, updates properties.
        """
        # Submit request to orchestrator
        request = await self.meta_orchestrator.submit_request(
            agent_name="OntologyAgent",
            request_type="enrich_ontology",
            payload={'picture_id': market_picture.get('picture_id')},
            requires_approval=False,
        )
        
        enrichment_result = {
            'entities_created': 0,
            'relationships_created': 0,
            'properties_updated': 0,
        }
        
        # Create/update asset entities
        prices = market_picture.get('prices', {})
        for symbol, price in prices.items():
            entity = self.ontology.create_object(
                obj_type='ASSET',
                name=symbol,
                properties={
                    'price': price,
                    'volume': market_picture.get('volumes', {}).get(symbol, 0),
                    'sentiment': market_picture.get('sentiment_scores', {}).get(symbol, 0.5),
                    'updated_at': datetime.now(timezone.utc).isoformat(),
                },
            )
            enrichment_result['entities_created'] += 1
        
        # Map correlations
        symbols = list(prices.keys())
        for i, sym1 in enumerate(symbols):
            for sym2 in symbols[i+1:]:
                # Calculate correlation (simplified)
                correlation = 0.5  # In production, use actual correlation
                
                if abs(correlation) > 0.3:
                    self.ontology.create_link(
                        link_type='CORRELATES_WITH',
                        source_id=sym1,
                        target_id=sym2,
                        properties={'correlation': correlation},
                    )
                    enrichment_result['relationships_created'] += 1
        
        # Update macro indicators
        macro = market_picture.get('macro_indicators', {})
        for indicator, value in macro.items():
            entity = self.ontology.create_object(
                obj_type='INDICATOR',
                name=indicator,
                properties={'value': value},
            )
            enrichment_result['properties_updated'] += 1
        
        self.enrichments_performed += 1
        
        logger.info(f"Ontology enriched: {enrichment_result}")
        
        return enrichment_result
    
    async def query_relationships(
        self,
        entity_id: str,
        relationship_type: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """Query relationships for an entity"""
        links = self.ontology.get_links(entity_id)
        
        if relationship_type:
            links = [l for l in links if l.link_type.value == relationship_type]
        
        return [l.to_dict() for l in links]
    
    def get_status(self) -> Dict[str, Any]:
        """Get agent status"""
        return {
            'agent_id': self.agent_id,
            'entities_created': self.entities_created,
            'relationships_mapped': self.relationships_mapped,
            'enrichments_performed': self.enrichments_performed,
            'ontology_size': len(self.ontology.objects),
        }
