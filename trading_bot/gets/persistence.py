"""
GETS Model Persistence and Serialization

Handles saving/loading of:
- Foundation model checkpoints
- LoRA adapter weights
- Multi-task head weights
- Governance audit trail
- Configuration snapshots
- Champion model registry
"""

import json
import pickle
import hashlib
import logging
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime
from pathlib import Path
import shutil
import zipfile

logger = logging.getLogger(__name__)


class ModelCheckpoint:
    """Handle model checkpoint save/load operations."""
    
    def __init__(self, base_path: str = "./gets_checkpoints"):
        self.base_path = Path(base_path)
        self.base_path.mkdir(parents=True, exist_ok=True)
        
        # Create subdirectories
        (self.base_path / "foundation").mkdir(exist_ok=True)
        (self.base_path / "adapters").mkdir(exist_ok=True)
        (self.base_path / "heads").mkdir(exist_ok=True)
        (self.base_path / "snapshots").mkdir(exist_ok=True)
    
    def save_foundation_model(
        self,
        model_name: str,
        model_state: Dict,
        version: str,
        metadata: Optional[Dict] = None
    ) -> str:
        """
        Save foundation model checkpoint.
        
        Args:
            model_name: Name of model (kronos, timesfm, moirai, ttm)
            model_state: Model state dict
            version: Version string
            metadata: Additional metadata
            
        Returns:
            Checkpoint path
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        checkpoint_name = f"{model_name}_v{version}_{timestamp}"
        checkpoint_path = self.base_path / "foundation" / checkpoint_name
        checkpoint_path.mkdir(exist_ok=True)
        
        # Save model state
        model_file = checkpoint_path / "model_state.pkl"
        with open(model_file, 'wb') as f:
            pickle.dump(model_state, f)
        
        # Save metadata
        meta = {
            'model_name': model_name,
            'version': version,
            'timestamp': timestamp,
            'created_at': datetime.now().isoformat(),
            **(metadata or {})
        }
        
        meta_file = checkpoint_path / "metadata.json"
        with open(meta_file, 'w') as f:
            json.dump(meta, f, indent=2)
        
        # Compute hash
        model_hash = self._compute_hash(model_file)
        hash_file = checkpoint_path / "checksum.sha256"
        with open(hash_file, 'w') as f:
            f.write(model_hash)
        
        logger.info(f"Saved {model_name} checkpoint to {checkpoint_path}")
        return str(checkpoint_path)
    
    def load_foundation_model(
        self,
        model_name: str,
        version: Optional[str] = None
    ) -> Tuple[Dict, Dict]:
        """
        Load foundation model checkpoint.
        
        Args:
            model_name: Name of model
            version: Specific version, or None for latest
            
        Returns:
            (model_state, metadata)
        """
        foundation_path = self.base_path / "foundation"
        
        # Find checkpoint
        if version:
            pattern = f"{model_name}_v{version}_*"
            matches = list(foundation_path.glob(pattern))
        else:
            # Get latest
            pattern = f"{model_name}_v*"
            matches = sorted(
                foundation_path.glob(pattern),
                key=lambda p: p.stat().st_mtime,
                reverse=True
            )
        
        if not matches:
            raise FileNotFoundError(f"No checkpoint found for {model_name} v{version}")
        
        checkpoint_path = matches[0]
        
        # Verify checksum
        model_file = checkpoint_path / "model_state.pkl"
        hash_file = checkpoint_path / "checksum.sha256"
        
        if hash_file.exists():
            stored_hash = hash_file.read_text().strip()
            computed_hash = self._compute_hash(model_file)
            
            if stored_hash != computed_hash:
                raise ValueError(f"Checksum mismatch for {checkpoint_path}")
        
        # Load model
        with open(model_file, 'rb') as f:
            model_state = pickle.load(f)
        
        # Load metadata
        meta_file = checkpoint_path / "metadata.json"
        with open(meta_file, 'r') as f:
            metadata = json.load(f)
        
        logger.info(f"Loaded {model_name} from {checkpoint_path}")
        return model_state, metadata
    
    def save_adapter_weights(
        self,
        adapter_type: str,
        weights: Dict,
        target_model: str,
        version: str
    ) -> str:
        """Save LoRA adapter weights."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        adapter_name = f"{target_model}_{adapter_type}_v{version}_{timestamp}"
        adapter_path = self.base_path / "adapters" / adapter_name
        adapter_path.mkdir(exist_ok=True)
        
        # Save weights
        weights_file = adapter_path / "weights.pkl"
        with open(weights_file, 'wb') as f:
            pickle.dump(weights, f)
        
        # Save metadata
        meta = {
            'adapter_type': adapter_type,
            'target_model': target_model,
            'version': version,
            'timestamp': timestamp
        }
        
        with open(adapter_path / "metadata.json", 'w') as f:
            json.dump(meta, f)
        
        return str(adapter_path)
    
    def load_adapter_weights(
        self,
        target_model: str,
        adapter_type: str,
        version: Optional[str] = None
    ) -> Dict:
        """Load LoRA adapter weights."""
        adapters_path = self.base_path / "adapters"
        
        if version:
            pattern = f"{target_model}_{adapter_type}_v{version}_*"
            matches = list(adapters_path.glob(pattern))
        else:
            pattern = f"{target_model}_{adapter_type}_v*"
            matches = sorted(
                adapters_path.glob(pattern),
                key=lambda p: p.stat().st_mtime,
                reverse=True
            )
        
        if not matches:
            raise FileNotFoundError(f"No adapter found for {target_model} {adapter_type}")
        
        adapter_path = matches[0]
        weights_file = adapter_path / "weights.pkl"
        
        with open(weights_file, 'rb') as f:
            return pickle.load(f)
    
    def save_head_weights(
        self,
        head_name: str,
        weights: Dict,
        version: str
    ) -> str:
        """Save multi-task head weights."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        head_file = self.base_path / "heads" / f"{head_name}_v{version}_{timestamp}.pkl"
        
        with open(head_file, 'wb') as f:
            pickle.dump(weights, f)
        
        return str(head_file)
    
    def list_checkpoints(self, model_name: Optional[str] = None) -> List[Dict]:
        """List all available checkpoints."""
        foundation_path = self.base_path / "foundation"
        checkpoints = []
        
        for checkpoint_dir in foundation_path.iterdir():
            if not checkpoint_dir.is_dir():
                continue
            
            meta_file = checkpoint_dir / "metadata.json"
            if meta_file.exists():
                with open(meta_file, 'r') as f:
                    meta = json.load(f)
                    
                    if model_name and meta.get('model_name') != model_name:
                        continue
                    
                    checkpoints.append({
                        'path': str(checkpoint_dir),
                        **meta
                    })
        
        return sorted(checkpoints, key=lambda x: x['created_at'], reverse=True)
    
    def _compute_hash(self, file_path: Path) -> str:
        """Compute SHA256 hash of file."""
        sha256 = hashlib.sha256()
        with open(file_path, 'rb') as f:
            for chunk in iter(lambda: f.read(8192), b''):
                sha256.update(chunk)
        return sha256.hexdigest()


class SystemSnapshot:
    """Create and restore complete system snapshots."""
    
    def __init__(self, base_path: str = "./gets_snapshots"):
        self.base_path = Path(base_path)
        self.base_path.mkdir(parents=True, exist_ok=True)
    
    def create_snapshot(
        self,
        gets_instance,
        name: str,
        include_audit_trail: bool = True
    ) -> str:
        """
        Create complete system snapshot for rollback.
        
        Args:
            gets_instance: GETS system instance
            name: Snapshot name
            include_audit_trail: Whether to include audit trail
            
        Returns:
            Snapshot path
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        snapshot_name = f"{name}_{timestamp}"
        snapshot_path = self.base_path / snapshot_name
        snapshot_path.mkdir(exist_ok=True)
        
        # Save configuration
        config = {
            'kronos_enabled': gets_instance.config.kronos_enabled,
            'timesfm_enabled': gets_instance.config.timesfm_enabled,
            'moirai_enabled': gets_instance.config.moirai_enabled,
            'ttm_enabled': gets_instance.config.ttm_enabled,
            'lora_rank': gets_instance.config.lora_rank,
            'use_lora_adapters': gets_instance.config.use_lora_adapters,
            'created_at': datetime.now().isoformat()
        }
        
        with open(snapshot_path / "config.json", 'w') as f:
            json.dump(config, f, indent=2)
        
        # Save model versions
        model_status = {}
        if hasattr(gets_instance, 'layer1_perception') and gets_instance.layer1_perception:
            model_status = {
                'available_models': [m.value for m in gets_instance.layer1_perception.get_available_models()],
                'model_versions': {}  # Would get actual versions
            }
        
        with open(snapshot_path / "model_status.json", 'w') as f:
            json.dump(model_status, f)
        
        # Save audit trail reference
        if include_audit_trail and hasattr(gets_instance, 'layer5_governance'):
            audit_status = gets_instance.layer5_governance.get_audit_status()
            with open(snapshot_path / "audit_reference.json", 'w') as f:
                json.dump(audit_status, f)
        
        # Create manifest
        manifest = {
            'name': name,
            'timestamp': timestamp,
            'created_at': datetime.now().isoformat(),
            'files': [f.name for f in snapshot_path.iterdir() if f.is_file()]
        }
        
        with open(snapshot_path / "manifest.json", 'w') as f:
            json.dump(manifest, f, indent=2)
        
        # Create zip archive
        zip_path = self.base_path / f"{snapshot_name}.zip"
        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zf:
            for file_path in snapshot_path.rglob('*'):
                if file_path.is_file():
                    zf.write(file_path, file_path.relative_to(snapshot_path))
        
        logger.info(f"Created snapshot: {zip_path}")
        return str(zip_path)
    
    def restore_snapshot(self, snapshot_path: str) -> Dict:
        """
        Restore system from snapshot.
        
        Args:
            snapshot_path: Path to snapshot zip
            
        Returns:
            Restored configuration
        """
        snapshot_path = Path(snapshot_path)
        
        if not snapshot_path.exists():
            raise FileNotFoundError(f"Snapshot not found: {snapshot_path}")
        
        # Extract
        extract_path = snapshot_path.parent / snapshot_path.stem
        with zipfile.ZipFile(snapshot_path, 'r') as zf:
            zf.extractall(extract_path)
        
        # Load configuration
        config_file = extract_path / "config.json"
        with open(config_file, 'r') as f:
            config = json.load(f)
        
        logger.info(f"Restored snapshot from {snapshot_path}")
        return config
    
    def list_snapshots(self) -> List[Dict]:
        """List all available snapshots."""
        snapshots = []
        
        for zip_file in self.base_path.glob("*.zip"):
            # Try to read manifest
            try:
                with zipfile.ZipFile(zip_file, 'r') as zf:
                    with zf.open('manifest.json') as f:
                        manifest = json.load(f)
                        snapshots.append({
                            'path': str(zip_file),
                            **manifest
                        })
            except:
                snapshots.append({
                    'path': str(zip_file),
                    'name': zip_file.stem,
                    'error': 'Could not read manifest'
                })
        
        return sorted(snapshots, key=lambda x: x.get('created_at', ''), reverse=True)
    
    def rollback(self, snapshot_name: str) -> bool:
        """
        One-click rollback to previous snapshot.
        
        Args:
            snapshot_name: Name of snapshot to rollback to
            
        Returns:
            Success status
        """
        try:
            # Find snapshot
            snapshots = self.list_snapshots()
            target = None
            
            for snap in snapshots:
                if snap.get('name') == snapshot_name or snap_name in snap.get('path', ''):
                    target = snap
                    break
            
            if not target:
                logger.error(f"Snapshot {snapshot_name} not found")
                return False
            
            # Restore
            config = self.restore_snapshot(target['path'])
            
            logger.info(f"Rollback to {snapshot_name} complete")
            logger.info(f"Restored config: {config}")
            
            return True
            
        except Exception as e:
            logger.error(f"Rollback failed: {e}")
            return False


class ChampionRegistry:
    """Registry for managing champion models and their promotion status."""
    
    def __init__(self, base_path: str = "./gets_champions"):
        self.base_path = Path(base_path)
        self.base_path.mkdir(parents=True, exist_ok=True)
        
        self._champions: Dict[str, Dict] = {}
        self._lock_path = self.base_path / ".lock"
        self._load_registry()
    
    def _load_registry(self):
        """Load champion registry from disk."""
        registry_file = self.base_path / "registry.json"
        if registry_file.exists():
            with open(registry_file, 'r') as f:
                self._champions = json.load(f)
    
    def _save_registry(self):
        """Save champion registry to disk."""
        registry_file = self.base_path / "registry.json"
        with open(registry_file, 'w') as f:
            json.dump(self._champions, f, indent=2)
    
    def register_champion(
        self,
        champion_id: str,
        base_config: Dict,
        mutations: List[str],
        performance: Dict,
        status: str = "PENDING"
    ):
        """Register a new champion model."""
        self._champions[champion_id] = {
            'id': champion_id,
            'base_config': base_config,
            'mutations': mutations,
            'performance': performance,
            'status': status,  # PENDING, APPROVED, REJECTED, ACTIVE
            'created_at': datetime.now().isoformat(),
            'promoted_at': None
        }
        
        self._save_registry()
        logger.info(f"Registered champion: {champion_id}")
    
    def approve_champion(self, champion_id: str) -> bool:
        """Approve champion for promotion."""
        if champion_id not in self._champions:
            return False
        
        self._champions[champion_id]['status'] = 'APPROVED'
        self._champions[champion_id]['promoted_at'] = datetime.now().isoformat()
        
        self._save_registry()
        logger.info(f"Approved champion: {champion_id}")
        return True
    
    def reject_champion(self, champion_id: str, reason: str):
        """Reject champion."""
        if champion_id not in self._champions:
            return
        
        self._champions[champion_id]['status'] = 'REJECTED'
        self._champions[champion_id]['rejection_reason'] = reason
        
        self._save_registry()
    
    def get_active_champion(self) -> Optional[Dict]:
        """Get currently active champion."""
        for champ_id, champ in self._champions.items():
            if champ['status'] == 'ACTIVE':
                return champ
        return None
    
    def list_champions(self, status: Optional[str] = None) -> List[Dict]:
        """List all champions, optionally filtered by status."""
        champions = list(self._champions.values())
        
        if status:
            champions = [c for c in champions if c['status'] == status]
        
        return sorted(champions, key=lambda x: x['created_at'], reverse=True)
    
    def promote_to_active(self, champion_id: str) -> bool:
        """Promote champion to active production model."""
        if champion_id not in self._champions:
            return False
        
        # Deactivate current active
        for champ in self._champions.values():
            if champ['status'] == 'ACTIVE':
                champ['status'] = 'RETIRED'
                champ['retired_at'] = datetime.now().isoformat()
        
        # Activate new champion
        self._champions[champion_id]['status'] = 'ACTIVE'
        self._champions[champion_id]['activated_at'] = datetime.now().isoformat()
        
        self._save_registry()
        logger.info(f"Promoted champion {champion_id} to ACTIVE")
        return True


class ConfigurationManager:
    """Manage GETS configuration versions."""
    
    def __init__(self, base_path: str = "./gets_config"):
        self.base_path = Path(base_path)
        self.base_path.mkdir(parents=True, exist_ok=True)
    
    def save_config(self, config: Dict, name: str, version: str) -> str:
        """Save configuration version."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        config_file = self.base_path / f"{name}_v{version}_{timestamp}.json"
        
        config_with_meta = {
            'name': name,
            'version': version,
            'timestamp': timestamp,
            'created_at': datetime.now().isoformat(),
            'config': config
        }
        
        with open(config_file, 'w') as f:
            json.dump(config_with_meta, f, indent=2)
        
        return str(config_file)
    
    def load_config(self, name: str, version: Optional[str] = None) -> Dict:
        """Load configuration."""
        if version:
            pattern = f"{name}_v{version}_*.json"
            matches = list(self.base_path.glob(pattern))
        else:
            pattern = f"{name}_v*.json"
            matches = sorted(
                self.base_path.glob(pattern),
                key=lambda p: p.stat().st_mtime,
                reverse=True
            )
        
        if not matches:
            raise FileNotFoundError(f"Config not found: {name} v{version}")
        
        with open(matches[0], 'r') as f:
            return json.load(f)
    
    def list_configs(self) -> List[Dict]:
        """List all configurations."""
        configs = []
        
        for config_file in self.base_path.glob("*.json"):
            with open(config_file, 'r') as f:
                data = json.load(f)
                configs.append({
                    'path': str(config_file),
                    **data
                })
        
        return sorted(configs, key=lambda x: x.get('created_at', ''), reverse=True)


def create_persistence_system(
    checkpoint_path: str = "./gets_checkpoints",
    snapshot_path: str = "./gets_snapshots",
    config_path: str = "./gets_config"
) -> Tuple[ModelCheckpoint, SystemSnapshot, ChampionRegistry, ConfigurationManager]:
    """
    Factory function to create complete persistence system.
    
    Returns:
        (ModelCheckpoint, SystemSnapshot, ChampionRegistry, ConfigurationManager)
    """
    checkpoint = ModelCheckpoint(checkpoint_path)
    snapshot = SystemSnapshot(snapshot_path)
    registry = ChampionRegistry()
    config_mgr = ConfigurationManager(config_path)
    
    return checkpoint, snapshot, registry, config_mgr
