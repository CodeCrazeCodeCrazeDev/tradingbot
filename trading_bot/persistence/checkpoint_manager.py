"""
Checkpoint Manager - State persistence for crash recovery

Persists minimal runtime state for warm restart after crashes.
"""

import json
import logging
import pickle
from pathlib import Path
from typing import Any, Dict, List, Optional
from datetime import datetime
from dataclasses import dataclass, asdict

logger = logging.getLogger(__name__)


@dataclass
class SystemCheckpoint:
    """System state checkpoint"""
    timestamp: datetime
    running: bool
    paused: bool
    positions: List[Dict[str, Any]]
    open_orders: List[Dict[str, Any]]
    last_processed_seq: int
    risk_limits: Dict[str, Any]
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


class CheckpointManager:
    """Manages system state checkpointing for crash recovery"""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        
        # Checkpoint settings
        self.checkpoint_dir = Path(self.config.get('checkpoint_dir', 'data/checkpoints'))
        self.checkpoint_dir.mkdir(parents=True, exist_ok=True)
        
        self.checkpoint_interval = self.config.get('checkpoint_interval', 60)  # 1 minute
        self.max_checkpoints = self.config.get('max_checkpoints', 10)
        
        # State tracking
        self.last_checkpoint = None
        self.checkpoint_count = 0
        
        logger.info(f"Checkpoint manager initialized: dir={self.checkpoint_dir}")
    
    def create_checkpoint(self, survival_core) -> str:
        """
        Create checkpoint from current state
        
        Args:
            survival_core: SurvivalCore instance
            
        Returns:
            Checkpoint file path
        """
        try:
            # Collect state
            positions = [
                {
                    'symbol': p.symbol,
                    'quantity': p.quantity,
                    'entry_price': p.entry_price,
                    'current_price': p.current_price,
                    'unrealized_pnl': p.unrealized_pnl,
                    'realized_pnl': p.realized_pnl
                }
                for p in survival_core.execution.get_active_positions()
            ]
            
            open_orders = [
                {
                    'id': o.id,
                    'client_order_id': o.client_order_id,
                    'symbol': o.symbol,
                    'order_type': o.order_type.value,
                    'side': o.side,
                    'quantity': o.quantity,
                    'price': o.price,
                    'status': o.status.value
                }
                for o in survival_core.execution.get_orders()
                if o.status.value in ['pending', 'submitted', 'partially_filled']
            ]
            
            # Create checkpoint
            checkpoint = SystemCheckpoint(
                timestamp=datetime.now(),
                running=survival_core.running,
                paused=survival_core.paused,
                positions=positions,
                open_orders=open_orders,
                last_processed_seq=getattr(survival_core, 'last_processed_seq', 0),
                risk_limits=survival_core.risk_limits.copy(),
                metadata={
                    'error_count': len(survival_core.errors),
                    'last_health_check': survival_core.last_health_check.isoformat()
                }
            )
            
            # Save to file
            checkpoint_file = self.checkpoint_dir / f"checkpoint_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            
            with open(checkpoint_file, 'w') as f:
                json.dump(asdict(checkpoint), f, indent=2, default=str)
            
            self.last_checkpoint = datetime.now()
            self.checkpoint_count += 1
            
            # Clean old checkpoints
            self._cleanup_old_checkpoints()
            
            logger.info(f"Created checkpoint: {checkpoint_file}")
            return str(checkpoint_file)
            
        except Exception as e:
            logger.error(f"Error creating checkpoint: {e}")
            return ""
    
    def restore_checkpoint(self, checkpoint_file: Optional[str] = None) -> Optional[SystemCheckpoint]:
        """
        Restore from checkpoint
        
        Args:
            checkpoint_file: Specific checkpoint file (uses latest if None)
            
        Returns:
            SystemCheckpoint or None
        """
        try:
            if checkpoint_file is None:
                # Find latest checkpoint
                checkpoints = sorted(self.checkpoint_dir.glob("checkpoint_*.json"))
                if not checkpoints:
                    logger.warning("No checkpoints found")
                    return None
                checkpoint_file = checkpoints[-1]
            else:
                checkpoint_file = Path(checkpoint_file)
            
            # Load checkpoint
            with open(checkpoint_file, 'r') as f:
                data = json.load(f)
            
            # Convert timestamp
            data['timestamp'] = datetime.fromisoformat(data['timestamp'])
            
            checkpoint = SystemCheckpoint(**data)
            
            logger.info(f"Restored checkpoint from {checkpoint_file}")
            logger.info(f"Checkpoint state: {len(checkpoint.positions)} positions, {len(checkpoint.open_orders)} orders")
            
            return checkpoint
            
        except Exception as e:
            logger.error(f"Error restoring checkpoint: {e}")
            return None
    
    def _cleanup_old_checkpoints(self):
        """Remove old checkpoints beyond max limit"""
        checkpoints = sorted(self.checkpoint_dir.glob("checkpoint_*.json"))
        
        if len(checkpoints) > self.max_checkpoints:
            for old_checkpoint in checkpoints[:-self.max_checkpoints]:
                try:
                    old_checkpoint.unlink()
                    logger.debug(f"Removed old checkpoint: {old_checkpoint}")
                except Exception as e:
                    logger.error(f"Error removing old checkpoint: {e}")
    
    def get_checkpoint_list(self) -> List[Dict[str, Any]]:
        """Get list of available checkpoints"""
        checkpoints = []
        
        for checkpoint_file in sorted(self.checkpoint_dir.glob("checkpoint_*.json")):
            try:
                stat = checkpoint_file.stat()
                checkpoints.append({
                    'file': str(checkpoint_file),
                    'size': stat.st_size,
                    'modified': datetime.fromtimestamp(stat.st_mtime).isoformat()
                })
            except Exception as e:
                logger.error(f"Error reading checkpoint {checkpoint_file}: {e}")
        
        return checkpoints
    
    def get_stats(self) -> Dict[str, Any]:
        """Get checkpoint manager statistics"""
        return {
            'checkpoint_dir': str(self.checkpoint_dir),
            'checkpoint_interval': self.checkpoint_interval,
            'max_checkpoints': self.max_checkpoints,
            'last_checkpoint': self.last_checkpoint.isoformat() if self.last_checkpoint else None,
            'checkpoint_count': self.checkpoint_count,
            'available_checkpoints': len(list(self.checkpoint_dir.glob("checkpoint_*.json")))
        }
