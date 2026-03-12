"""
Kubernetes Orchestration: Auto-scaling during volatility events

Implements dynamic resource scaling based on market conditions and trading volume.
"""

import numpy as np
from typing import Dict, List, Optional
from dataclasses import dataclass
from enum import Enum
import logging
from datetime import datetime
import asyncio
from enum import auto
import numpy

# Evolution: Added retry decorator
def retry(max_attempts=3, delay=1.0):
    """Retry decorator for resilient operations"""
    def decorator(func):
        async def wrapper(*args, **kwargs):
            last_error = None
            for attempt in range(max_attempts):
                try:
                    return await func(*args, **kwargs)
                except Exception as e:
                    last_error = e
                    if attempt < max_attempts - 1:
                        await asyncio.sleep(delay * (attempt + 1))
            raise last_error
        return wrapper
    return decorator



logger = logging.getLogger(__name__)


class ScalingMode(Enum):
    """Scaling modes"""
    CONSERVATIVE = "conservative"
    MODERATE = "moderate"
    AGGRESSIVE = "aggressive"


@dataclass
class ResourceMetrics:
    """Resource utilization metrics"""
    cpu_usage: float
    memory_usage: float
    network_throughput: float
    order_rate: float
    latency_ms: float
    timestamp: datetime


@dataclass
class ScalingDecision:
    """Scaling decision"""
    action: str  # 'SCALE_UP', 'SCALE_DOWN', 'NO_CHANGE'
    target_replicas: int
    reason: str
    confidence: float


class VolatilityMonitor:
    """
    Market Volatility Monitor
    
    Tracks market volatility to trigger scaling events.
    """
    
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        
        # Volatility thresholds
        self.low_vol_threshold = self.config.get('low_vol_threshold', 0.01)
        self.medium_vol_threshold = self.config.get('medium_vol_threshold', 0.02)
        self.high_vol_threshold = self.config.get('high_vol_threshold', 0.04)
        
        # Historical volatility
        self.volatility_history = []
        self.max_history = 100
        
    def update_volatility(self, returns: np.ndarray):
        """Update volatility estimate"""
        if len(returns) < 2:
            return
        
        # Calculate realized volatility
        volatility = np.std(returns)
        
        self.volatility_history.append({
            'volatility': volatility,
            'timestamp': datetime.now()
        })
        
        # Keep only recent history
        if len(self.volatility_history) > self.max_history:
            self.volatility_history = self.volatility_history[-self.max_history:]
    
    def get_volatility_regime(self) -> str:
        """
        Get current volatility regime
        
        Returns:
            'LOW', 'MEDIUM', 'HIGH', or 'EXTREME'
        """
        if not self.volatility_history:
            return 'MEDIUM'
        
        current_vol = self.volatility_history[-1]['volatility']
        
        if current_vol < self.low_vol_threshold:
            return 'LOW'
        elif current_vol < self.medium_vol_threshold:
            return 'MEDIUM'
        elif current_vol < self.high_vol_threshold:
            return 'HIGH'
        else:
            return 'EXTREME'
    
    def is_volatility_spike(self) -> bool:
        """Detect volatility spike"""
        if len(self.volatility_history) < 10:
            return False
        
        recent_vol = np.mean([h['volatility'] for h in self.volatility_history[-5:]])
        historical_vol = np.mean([h['volatility'] for h in self.volatility_history[-20:-5]])
        
        # Spike if recent volatility is 2x historical
        return recent_vol > historical_vol * 2


class KubernetesOrchestrator:
    """
    Kubernetes Auto-Scaling Orchestrator
    
    Dynamically scales trading bot resources based on market conditions.
    """
    
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        
        # Scaling parameters
        self.min_replicas = self.config.get('min_replicas', 2)
        self.max_replicas = self.config.get('max_replicas', 20)
        self.target_cpu_utilization = self.config.get('target_cpu_utilization', 0.70)
        self.target_memory_utilization = self.config.get('target_memory_utilization', 0.75)
        
        # Current state
        self.current_replicas = self.min_replicas
        self.scaling_mode = ScalingMode.MODERATE
        
        # Monitors
        self.volatility_monitor = VolatilityMonitor(config)
        
        # Metrics history
        self.metrics_history = []
        self.scaling_history = []
        
        # Cooldown period (seconds)
        self.scale_up_cooldown = self.config.get('scale_up_cooldown', 60)
        self.scale_down_cooldown = self.config.get('scale_down_cooldown', 300)
        self.last_scale_time = None
        
        logger.info(f"Kubernetes Orchestrator initialized: {self.min_replicas}-{self.max_replicas} replicas")
    
    def update_metrics(self, metrics: ResourceMetrics):
        """Update resource metrics"""
        self.metrics_history.append(metrics)
        
        # Keep only recent history
        if len(self.metrics_history) > 100:
            self.metrics_history = self.metrics_history[-100:]
    
    def calculate_scaling_decision(
        self,
        current_metrics: ResourceMetrics,
        volatility_regime: str
    ) -> ScalingDecision:
        """
        Calculate scaling decision based on metrics and volatility
        
        Args:
            current_metrics: Current resource metrics
            volatility_regime: Current volatility regime
            
        Returns:
            Scaling decision
        """
        # Check cooldown
        if self.last_scale_time:
            time_since_scale = (datetime.now() - self.last_scale_time).total_seconds()
            if time_since_scale < self.scale_up_cooldown:
                return ScalingDecision(
                    action='NO_CHANGE',
                    target_replicas=self.current_replicas,
                    reason='Cooldown period active',
                    confidence=1.0
                )
        
        # Calculate resource-based scaling need
        cpu_ratio = current_metrics.cpu_usage / self.target_cpu_utilization
        memory_ratio = current_metrics.memory_usage / self.target_memory_utilization
        
        # Calculate desired replicas based on resource usage
        resource_based_replicas = int(np.ceil(self.current_replicas * max(cpu_ratio, memory_ratio)))
        
        # Adjust based on volatility regime
        volatility_multipliers = {
            'LOW': 0.8,
            'MEDIUM': 1.0,
            'HIGH': 1.5,
            'EXTREME': 2.0
        }
        
        volatility_multiplier = volatility_multipliers.get(volatility_regime, 1.0)
        volatility_based_replicas = int(np.ceil(self.current_replicas * volatility_multiplier))
        
        # Take the maximum of resource-based and volatility-based
        target_replicas = max(resource_based_replicas, volatility_based_replicas)
        
        # Apply min/max constraints
        target_replicas = max(self.min_replicas, min(self.max_replicas, target_replicas))
        
        # Determine action
        if target_replicas > self.current_replicas:
            action = 'SCALE_UP'
            reason = f"High load: CPU={current_metrics.cpu_usage:.1%}, Memory={current_metrics.memory_usage:.1%}, Vol={volatility_regime}"
            confidence = min(1.0, (target_replicas - self.current_replicas) / self.current_replicas)
        elif target_replicas < self.current_replicas:
            action = 'SCALE_DOWN'
            reason = f"Low load: CPU={current_metrics.cpu_usage:.1%}, Memory={current_metrics.memory_usage:.1%}"
            confidence = min(1.0, (self.current_replicas - target_replicas) / self.current_replicas)
        else:
            action = 'NO_CHANGE'
            reason = 'Optimal resource utilization'
            confidence = 1.0
        
        return ScalingDecision(
            action=action,
            target_replicas=target_replicas,
            reason=reason,
            confidence=confidence
        )
    
    async def execute_scaling(self, decision: ScalingDecision) -> bool:
        """
        Execute scaling decision
        
        Args:
            decision: Scaling decision to execute
            
        Returns:
            Success status
        """
        if decision.action == 'NO_CHANGE':
            return True
        
        logger.info(f"Executing scaling: {decision.action} to {decision.target_replicas} replicas")
        logger.info(f"Reason: {decision.reason} (confidence: {decision.confidence:.2f})")
        
        try:
            # In production, would use Kubernetes API
            # For now, simulate scaling
            
            if decision.action == 'SCALE_UP':
                # Simulate pod creation
                for i in range(decision.target_replicas - self.current_replicas):
                    await asyncio.sleep(0.1)  # Simulate pod startup time
                    logger.info(f"  Started pod {self.current_replicas + i + 1}")
            
            elif decision.action == 'SCALE_DOWN':
                # Simulate pod termination
                for i in range(self.current_replicas - decision.target_replicas):
                    await asyncio.sleep(0.05)  # Simulate graceful shutdown
                    logger.info(f"  Terminated pod {self.current_replicas - i}")
            
            # Update state
            self.current_replicas = decision.target_replicas
            self.last_scale_time = datetime.now()
            
            # Record scaling event
            self.scaling_history.append({
                'timestamp': datetime.now(),
                'action': decision.action,
                'from_replicas': self.current_replicas,
                'to_replicas': decision.target_replicas,
                'reason': decision.reason
            })
            
            logger.info(f"Scaling complete: Now running {self.current_replicas} replicas")
            
            return True
            
        except Exception as e:
            logger.error(f"Scaling failed: {e}")
            return False
    
    async def auto_scale_loop(self, interval_seconds: int = 30):
        """
        Continuous auto-scaling loop
        
        Args:
            interval_seconds: Check interval in seconds
        """
        logger.info(f"Starting auto-scaling loop (interval: {interval_seconds}s)")
        
        while True:
            try:
                # Get current metrics (in production, would query from monitoring system)
                if self.metrics_history:
                    current_metrics = self.metrics_history[-1]
                else:
                    # Default metrics if none available
                    current_metrics = ResourceMetrics(
                        cpu_usage=0.5,
                        memory_usage=0.6,
                        network_throughput=100,
                        order_rate=10,
                        latency_ms=50,
                        timestamp=datetime.now()
                    )
                
                # Get volatility regime
                volatility_regime = self.volatility_monitor.get_volatility_regime()
                
                # Calculate scaling decision
                decision = self.calculate_scaling_decision(current_metrics, volatility_regime)
                
                # Execute if needed
                if decision.action != 'NO_CHANGE':
                    await self.execute_scaling(decision)
                
                # Wait for next check
                await asyncio.sleep(interval_seconds)
                
            except Exception as e:
                logger.error(f"Error in auto-scaling loop: {e}")
                await asyncio.sleep(interval_seconds)
    
    def get_statistics(self) -> Dict:
        """Get orchestrator statistics"""
        if self.metrics_history:
            recent_metrics = self.metrics_history[-10:]
            avg_cpu = np.mean([m.cpu_usage for m in recent_metrics])
            avg_memory = np.mean([m.memory_usage for m in recent_metrics])
            avg_latency = np.mean([m.latency_ms for m in recent_metrics])
        else:
            avg_cpu = avg_memory = avg_latency = 0
        
        return {
            'current_replicas': self.current_replicas,
            'min_replicas': self.min_replicas,
            'max_replicas': self.max_replicas,
            'avg_cpu_usage': avg_cpu,
            'avg_memory_usage': avg_memory,
            'avg_latency_ms': avg_latency,
            'total_scaling_events': len(self.scaling_history),
            'volatility_regime': self.volatility_monitor.get_volatility_regime()
        }
    
    def generate_kubernetes_manifest(self) -> str:
        """
        Generate Kubernetes HPA manifest
        
        Returns:
            YAML manifest string
        """
        manifest = f"""
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: trading-bot-hpa
  namespace: trading
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: trading-bot
  minReplicas: {self.min_replicas}
  maxReplicas: {self.max_replicas}
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: {int(self.target_cpu_utilization * 100)}
  - type: Resource
    resource:
      name: memory
      target:
        type: Utilization
        averageUtilization: {int(self.target_memory_utilization * 100)}
  behavior:
    scaleUp:
      stabilizationWindowSeconds: {self.scale_up_cooldown}
      policies:
      - type: Percent
        value: 100
        periodSeconds: 15
      - type: Pods
        value: 4
        periodSeconds: 15
      selectPolicy: Max
    scaleDown:
      stabilizationWindowSeconds: {self.scale_down_cooldown}
      policies:
      - type: Percent
        value: 50
        periodSeconds: 60
      selectPolicy: Min
"""
        return manifest


if __name__ == "__main__":
    # Example usage
    logging.basicConfig(level=logging.INFO)
    
    async def main():
        orchestrator = KubernetesOrchestrator({
            'min_replicas': 2,
            'max_replicas': 10,
            'target_cpu_utilization': 0.70
        })
        
        # Simulate some metrics
        logger.info("\nSimulating high load scenario...\n")
        
        # High CPU usage
        high_load_metrics = ResourceMetrics(
            cpu_usage=0.85,
            memory_usage=0.80,
            network_throughput=500,
            order_rate=100,
            latency_ms=150,
            timestamp=datetime.now()
        )
        
        orchestrator.update_metrics(high_load_metrics)
        
        # Simulate volatility spike
        returns = np.random.randn(100) * 0.05  # High volatility
        orchestrator.volatility_monitor.update_volatility(returns)
        
        # Get scaling decision
        decision = orchestrator.calculate_scaling_decision(
            high_load_metrics,
            orchestrator.volatility_monitor.get_volatility_regime()
        )
        
        logger.info(f"Scaling Decision:")
        logger.info(f"  Action: {decision.action}")
        logger.info(f"  Target Replicas: {decision.target_replicas}")
        logger.info(f"  Reason: {decision.reason}")
        logger.info(f"  Confidence: {decision.confidence:.2%}\n")
        
        # Execute scaling
        await orchestrator.execute_scaling(decision)
        
        # Get statistics
        stats = orchestrator.get_statistics()
        logger.info(f"\nOrchestrator Statistics:")
        logger.info(f"  Current Replicas: {stats['current_replicas']}")
        logger.info(f"  Volatility Regime: {stats['volatility_regime']}")
        logger.info(f"  Total Scaling Events: {stats['total_scaling_events']}")
        
        # Generate Kubernetes manifest
        logger.info(f"\nKubernetes HPA Manifest:")
        print(orchestrator.generate_kubernetes_manifest())
    
    asyncio.run(main())
