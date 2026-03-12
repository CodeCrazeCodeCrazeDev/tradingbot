"""Feature Versioning [HI-ANA-003] - Hash + metadata tracking"""
import hashlib, json, logging
from datetime import datetime
from typing import Any, Dict
import logging
from typing import Optional

logger = logging.getLogger(__name__)

class FeatureVersioning:
    def __init__(self):
        try:
            self.metadata_store: Dict[str, Dict] = {}
            self.feature_hashes: Dict[str, str] = {}
        except Exception as e:
            logger.error(f"Error in __init__: {e}")
            raise
        
    def create_hash(self, feature_name: str, data: Any, params: dict) -> str:
        """Generate reproducible hash"""
        try:
            hash_input = json.dumps({
                'name': feature_name,
                'params': params,
                'shape': str(getattr(data, 'shape', len(data)))
            }, sort_keys=True)
            return hashlib.sha256(hash_input.encode()).hexdigest()[:16]
        except Exception as e:
            logger.error(f"Error in create_hash: {e}")
            raise
    
    def store_metadata(self, feature_name: str, hash_key: str, metadata: dict):
        """Store feature metadata"""
        try:
            self.metadata_store[hash_key] = {
                'feature_name': feature_name,
                'created_at': datetime.now().isoformat(),
                'metadata': metadata
            }
            self.feature_hashes[feature_name] = hash_key
            logger.info(f"Stored metadata for {feature_name}: {hash_key}")
        except Exception as e:
            logger.error(f"Error in store_metadata: {e}")
            raise
    
    def get_metadata(self, hash_key: str) -> dict:
        return self.metadata_store.get(hash_key, {})
    
    def version_features(self, features: dict, params: dict = None, version: str = None) -> dict:
        """
        Version a set of features and return versioned metadata
        
        Args:
            features: Dictionary of feature_name -> feature_data
            params: Optional parameters used to generate features
            version: Optional version string (e.g., '1.0.0')
            
        Returns:
            Dictionary with versioned feature information
        """
        try:
            if params is None:
                params = {}
        
            versioned = {}
        
            # Add version to output if provided
            if version:
                versioned['version'] = version
        
            for feature_name, feature_data in features.items():
                # Create hash for this feature
                hash_key = self.create_hash(feature_name, feature_data, params)
            
                # Store metadata
                metadata = {
                    'params': params,
                    'version': version,
                    'shape': str(getattr(feature_data, 'shape', len(feature_data) if hasattr(feature_data, '__len__') else 'scalar'))
                }
                self.store_metadata(feature_name, hash_key, metadata)
            
                # Add to versioned output
                versioned[feature_name] = {
                    'hash': hash_key,
                    'data': feature_data,
                    'metadata': metadata
                }
        
            return versioned
        except Exception as e:
            logger.error(f"Error in version_features: {e}")
            raise
