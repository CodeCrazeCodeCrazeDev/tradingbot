"""Signal Provenance - Lineage Tracking [HI-ANA-009]"""
import logging
from datetime import datetime
from typing import Dict, List

logger = logging.getLogger(__name__)

class SignalProvenance:
    def __init__(self):
        try:
            self.lineage_db: Dict[str, Dict] = {}
        except Exception as e:
            logger.error(f"Error in __init__: {e}")
            raise
        
    def record_lineage(self, signal_id: str, sources: List[str], features: List[str], 
                       models: List[str], confidence: float):
        """Record complete signal derivation"""
        try:
            self.lineage_db[signal_id] = {
                'sources': sources,
                'features': features,
                'models': models,
                'confidence': confidence,
                'timestamp': datetime.now().isoformat(),
                'version': '1.0'
            }
            logger.info(f"Recorded provenance for {signal_id}")
        except Exception as e:
            logger.error(f"Error in record_lineage: {e}")
            raise
    
    def trace_signal(self, signal_id: str) -> dict:
        """Trace signal back to origins"""
        return self.lineage_db.get(signal_id, {})
    
    def get_feature_usage(self, feature_name: str) -> List[str]:
        """Find all signals using a feature"""
        return [sid for sid, data in self.lineage_db.items() 
                if feature_name in data.get('features', [])]
    
    def create_provenance(self, signal_id: str, metadata: dict):
        """
        Create provenance record for a signal
        
        Args:
            signal_id: Unique signal identifier
            metadata: Dictionary with signal metadata
            
        Returns:
            Provenance record dictionary
        """
        
        try:
            provenance = {
                'signal_id': signal_id,
                'timestamp': datetime.now().isoformat(),
                'metadata': metadata,
                'quality_score': metadata.get('confidence', 0.5)
            }
        
            # Store in lineage database
            if signal_id not in self.lineage_db:
                self.lineage_db[signal_id] = {}
            self.lineage_db[signal_id].update(provenance)
        
            return provenance
        except Exception as e:
            logger.error(f"Error in create_provenance: {e}")
            raise
