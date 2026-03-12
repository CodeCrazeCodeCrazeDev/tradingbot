"""
Phase 8: Production Deployment - Auto-Scaling
Dynamic resource allocation based on market conditions
"""

import torch
import numpy as np
from typing import Dict, List, Optional, Tuple
import logging
import psutil
import GPUtil
from dataclasses import dataclass
from datetime import datetime

logger = logging.getLogger(__name__)


@dataclass
class ResourceMetrics:
    """System resource metrics."""
    cpu_usage: float
    memory_usage: float
    gpu_usage: Optional[float]
    gpu_memory: Optional[float]
    network_io: float
    disk_io: float
    timestamp: datetime = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()
    
    def to_dict(self) -> Dict:
        return {
            'cpu_usage': self.cpu_usage,
            'memory_usage': self.memory_usage,
            'gpu_usage': self.gpu_usage,
            'gpu_memory': self.gpu_memory,
            'network_io': self.network_io,
            'disk_io': self.disk_io,
            'timestamp': self.timestamp
        }


class AutoScaler:
    """
    Dynamic resource allocation system.
    Scales compute resources based on market conditions.
    """
    
    def __init__(
        self,
        update_interval: int = 60,  # seconds
        history_size: int = 1000
    ):
        # Resource thresholds
        self.thresholds = {
            'cpu': {
                'high': 0.8,
                'medium': 0.5,
                'low': 0.2
            },
            'memory': {
                'high': 0.8,
                'medium': 0.5,
                'low': 0.2
            },
            'gpu': {
                'high': 0.8,
                'medium': 0.5,
                'low': 0.2
            }
        }
        
        # Scaling parameters
        self.scaling_params = {
            'min_workers': 1,
            'max_workers': 8,
            'worker_step': 1,
            'scale_up_threshold': 0.8,
            'scale_down_threshold': 0.2,
            'cooldown_period': 300  # seconds
        }
        
        self.update_interval = update_interval
        self.last_update = datetime.now()
        self.last_scale = datetime.now()
        
        # Resource history
        self.history = []
        self.history_size = history_size
        
        # Current state
        self.current_workers = 1
        self.is_scaling = False
        
        logger.info("✅ Auto Scaler initialized")
        logger.info(f"   Update interval: {update_interval}s")
        logger.info(f"   History size: {history_size}")
    
    def update(self, market_state: Dict) -> Optional[Dict]:
        """
        Update resource allocation based on market conditions.
        
        Args:
            market_state: Current market conditions
        
        Returns:
            Dictionary with scaling decisions if any
        """
        now = datetime.now()
        
        # Check update interval
        if (now - self.last_update).total_seconds() < self.update_interval:
            return None
        
        # Get current resource usage
        metrics = self._get_resource_metrics()
        self.history.append(metrics)
        
        # Trim history
        if len(self.history) > self.history_size:
            self.history.pop(0)
        
        # Check if scaling is needed
        if self._should_scale(metrics, market_state):
            # Check cooldown period
            if (now - self.last_scale).total_seconds() >= self.scaling_params['cooldown_period']:
                decision = self._make_scaling_decision(metrics, market_state)
                
                if decision['action'] != 'none':
                    self._apply_scaling(decision)
                    self.last_scale = now
                    
                    logger.info(f"🔄 Scaling {decision['action']}")
                    logger.info(f"   Workers: {self.current_workers}")
                    logger.info(f"   Reason: {decision['reason']}")
                    
                    return decision
        
        self.last_update = now
        return None
    
    def _get_resource_metrics(self) -> ResourceMetrics:
        """Get current system resource metrics."""
        # CPU usage
        cpu_usage = psutil.cpu_percent() / 100.0
        
        # Memory usage
        memory = psutil.virtual_memory()
        memory_usage = memory.percent / 100.0
        
        # GPU metrics if available
        try:
            gpus = GPUtil.getGPUs()
            if gpus:
                gpu = gpus[0]  # Use first GPU
                gpu_usage = gpu.load
                gpu_memory = gpu.memoryUtil
            else:
                gpu_usage = None
                gpu_memory = None
        except:
            gpu_usage = None
            gpu_memory = None
        
        # Network I/O
        net_io = psutil.net_io_counters()
        network_io = (net_io.bytes_sent + net_io.bytes_recv) / 1024 / 1024  # MB
        
        # Disk I/O
        disk_io = psutil.disk_io_counters()
        disk_io = (disk_io.read_bytes + disk_io.write_bytes) / 1024 / 1024  # MB
        
        return ResourceMetrics(
            cpu_usage=cpu_usage,
            memory_usage=memory_usage,
            gpu_usage=gpu_usage,
            gpu_memory=gpu_memory,
            network_io=network_io,
            disk_io=disk_io
        )
    
    def _should_scale(
        self,
        metrics: ResourceMetrics,
        market_state: Dict
    ) -> bool:
        """Determine if scaling is needed."""
        # Check resource usage
        if metrics.cpu_usage > self.thresholds['cpu']['high']:
            return True
        
        if metrics.memory_usage > self.thresholds['memory']['high']:
            return True
        
        if metrics.gpu_usage and metrics.gpu_usage > self.thresholds['gpu']['high']:
            return True
        
        # Check market conditions
        if 'volatility' in market_state:
            vol = market_state['volatility']
            if vol > 0.02:  # High volatility
                return True
        
        if 'volume' in market_state:
            vol = market_state['volume']
            if vol > 1.5:  # High volume
                return True
        
        # Check for scale down
        if all([
            metrics.cpu_usage < self.thresholds['cpu']['low'],
            metrics.memory_usage < self.thresholds['memory']['low'],
            (not metrics.gpu_usage or 
             metrics.gpu_usage < self.thresholds['gpu']['low'])
        ]):
            return True
        
        return False
    
    def _make_scaling_decision(
        self,
        metrics: ResourceMetrics,
        market_state: Dict
    ) -> Dict:
        """
        Decide scaling action.
        
        Returns:
            Dictionary with scaling decision
        """
        # Calculate resource pressure
        pressure = self._calculate_resource_pressure(metrics)
        
        # Calculate market pressure
        market_pressure = self._calculate_market_pressure(market_state)
        
        # Combined pressure
        total_pressure = 0.7 * pressure + 0.3 * market_pressure
        
        if total_pressure > self.scaling_params['scale_up_threshold']:
            # Scale up
            if self.current_workers < self.scaling_params['max_workers']:
                return {
                    'action': 'up',
                    'workers': min(
                        self.current_workers + self.scaling_params['worker_step'],
                        self.scaling_params['max_workers']
                    ),
                    'reason': f'High pressure ({total_pressure:.2f})',
                    'pressure': total_pressure
                }
        
        elif total_pressure < self.scaling_params['scale_down_threshold']:
            # Scale down
            if self.current_workers > self.scaling_params['min_workers']:
                return {
                    'action': 'down',
                    'workers': max(
                        self.current_workers - self.scaling_params['worker_step'],
                        self.scaling_params['min_workers']
                    ),
                    'reason': f'Low pressure ({total_pressure:.2f})',
                    'pressure': total_pressure
                }
        
        return {
            'action': 'none',
            'workers': self.current_workers,
            'reason': 'No scaling needed',
            'pressure': total_pressure
        }
    
    def _calculate_resource_pressure(
        self,
        metrics: ResourceMetrics
    ) -> float:
        """Calculate resource pressure score."""
        pressures = [
            metrics.cpu_usage,
            metrics.memory_usage
        ]
        
        if metrics.gpu_usage is not None:
            pressures.append(metrics.gpu_usage)
        
        # Network and disk I/O pressure
        if len(self.history) > 1:
            prev_metrics = self.history[-1]
            
            # Network pressure
            net_change = (metrics.network_io - prev_metrics.network_io)
            net_pressure = min(net_change / 100.0, 1.0)  # Cap at 100MB/s
            pressures.append(net_pressure)
            
            # Disk pressure
            disk_change = (metrics.disk_io - prev_metrics.disk_io)
            disk_pressure = min(disk_change / 100.0, 1.0)  # Cap at 100MB/s
            pressures.append(disk_pressure)
        
        return float(np.mean(pressures))
    
    def _calculate_market_pressure(self, market_state: Dict) -> float:
        """Calculate market condition pressure."""
        pressures = []
        
        # Volatility pressure
        if 'volatility' in market_state:
            vol = market_state['volatility']
            vol_pressure = min(vol / 0.02, 1.0)  # Cap at 2% volatility
            pressures.append(vol_pressure)
        
        # Volume pressure
        if 'volume' in market_state:
            vol = market_state['volume']
            vol_pressure = min(vol / 2.0, 1.0)  # Cap at 2x normal volume
            pressures.append(vol_pressure)
        
        # Trading activity pressure
        if 'trades_per_second' in market_state:
            tps = market_state['trades_per_second']
            tps_pressure = min(tps / 10.0, 1.0)  # Cap at 10 TPS
            pressures.append(tps_pressure)
        
        if pressures:
            return float(np.mean(pressures))
        else:
            return 0.5  # Default medium pressure
    
    def _apply_scaling(self, decision: Dict):
        """Apply scaling decision."""
        self.current_workers = decision['workers']
        self.is_scaling = True
        
        # Implement actual scaling logic here
        # This could involve:
        # - Adjusting thread pool size
        # - Scaling cloud resources
        # - Modifying batch sizes
        # - Adjusting processing frequency
        
        self.is_scaling = False
    
    def get_resource_summary(self) -> Dict:
        """Get summary of resource usage."""
        if not self.history:
            return {}
        
        recent = self.history[-min(10, len(self.history)):]
        
        summary = {
            'current_workers': self.current_workers,
            'is_scaling': self.is_scaling,
            'last_update': self.last_update,
            'last_scale': self.last_scale,
            'metrics': {
                'cpu': {
                    'current': recent[-1].cpu_usage,
                    'mean': np.mean([m.cpu_usage for m in recent]),
                    'max': max(m.cpu_usage for m in recent)
                },
                'memory': {
                    'current': recent[-1].memory_usage,
                    'mean': np.mean([m.memory_usage for m in recent]),
                    'max': max(m.memory_usage for m in recent)
                }
            }
        }
        
        # Add GPU metrics if available
        if recent[-1].gpu_usage is not None:
            summary['metrics']['gpu'] = {
                'current': recent[-1].gpu_usage,
                'mean': np.mean([m.gpu_usage for m in recent if m.gpu_usage]),
                'max': max(m.gpu_usage for m in recent if m.gpu_usage)
            }
        
        return summary
    
    def save_state(self, filepath: str):
        """Save auto scaler state."""
        state = {
            'thresholds': self.thresholds,
            'scaling_params': self.scaling_params,
            'current_workers': self.current_workers,
            'history': [m.to_dict() for m in self.history],
            'last_update': self.last_update,
            'last_scale': self.last_scale
        }
        torch.save(state, filepath)
        logger.info(f"💾 Auto Scaler state saved to {filepath}")
    
    def load_state(self, filepath: str):
        """Load auto scaler state."""
        state = torch.load(filepath)
        
        self.thresholds = state['thresholds']
        self.scaling_params = state['scaling_params']
        self.current_workers = state['current_workers']
        self.history = [ResourceMetrics(**m) for m in state['history']]
        self.last_update = state['last_update']
        self.last_scale = state['last_scale']
        
        logger.info(f"📂 Auto Scaler state loaded from {filepath}")
        logger.info(f"   Current workers: {self.current_workers}")
        logger.info(f"   History samples: {len(self.history)}")
