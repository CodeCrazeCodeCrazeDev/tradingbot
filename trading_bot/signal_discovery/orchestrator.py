"""
Signal Discovery Orchestrator
============================

Central coordinator for the 80-agent anomaly hunting army in Layer 1.

Responsibilities:
1. Deploy and manage all 80 agents
2. Collect anomalies from all agents
3. Deduplicate and prioritize anomalies
4. Track system latency advantage vs institutional data
5. Monitor agent health
6. Route anomalies to Layer 2 (Market Intelligence Engine)
"""

from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from collections import defaultdict
import asyncio
import logging
import uuid

from .agents.base_agent import BaseAnomalyAgent, MarketAnomaly, AgentHealth
from .agents.financial_api_agents import FinancialAPIAgent
from .agents.research_paper_agents import ResearchPaperAgent
from .agents.social_media_agents import SocialMediaAgent
from .agents.dark_pool_agents import DarkPoolAgent
from .agents.developer_activity_agents import DeveloperActivityAgent
from .agents.protocol_launch_agents import ProtocolLaunchAgent
from .agents.economic_release_agents import EconomicReleaseAgent

logger = logging.getLogger(__name__)


@dataclass
class AnomalyPriorityScore:
    """Priority score for an anomaly."""
    anomaly: MarketAnomaly
    priority_score: float  # 0.0-1.0, higher = more important
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'anomaly': self.anomaly.to_dict(),
            'priority_score': self.priority_score,
        }


@dataclass
class EdgeHalfLifeMetrics:
    """Track how long a signal remains profitable after discovery."""
    signal_id: str
    discovery_time: datetime
    decay_rate: float  # Per-hour decay rate
    current_value: float  # Current edge value (0-1)
    initial_value: float  # Initial edge value at discovery
    trades_since_discovery: int
    avg_return_since_discovery: float
    last_updated: datetime
    
    def compute_current_value(self) -> float:
        """Compute current edge value using exponential decay model."""
        hours_elapsed = (datetime.now() - self.discovery_time).total_seconds() / 3600
        self.current_value = self.initial_value * np.exp(-self.decay_rate * hours_elapsed)
        return self.current_value
    
    def is_expired(self, threshold: float = 0.2) -> bool:
        """Check if edge has decayed below usable threshold."""
        return self.current_value < threshold


class EdgeHalfLifeEngine:
    """
    Edge Half-Life Engine: Track how long signals remain profitable.
    
    Every edge decays. This engine:
    - Estimates decay rate of each strategy
    - Detects when edge is dying
    - Forces retirement or downgrade
    
    edge_value(t) = initial_value * exp(-decay_rate * t)
    """
    
    def __init__(self, decay_threshold: float = 0.3, retirement_threshold: float = 0.1):
        self.decay_threshold = decay_threshold  # Warn when below this
        self.retirement_threshold = retirement_threshold  # Retire when below this
        self.edge_metrics: Dict[str, EdgeHalfLifeMetrics] = {}
        self.decay_history: Dict[str, List[Tuple[datetime, float]]] = defaultdict(list)
        
    def register_signal(self, signal_id: str, initial_edge_value: float, 
                       estimated_decay_rate: float = 0.05) -> EdgeHalfLifeMetrics:
        """Register a new signal for half-life tracking."""
        metrics = EdgeHalfLifeMetrics(
            signal_id=signal_id,
            discovery_time=datetime.now(),
            decay_rate=estimated_decay_rate,
            current_value=initial_edge_value,
            initial_value=initial_edge_value,
            trades_since_discovery=0,
            avg_return_since_discovery=0.0,
            last_updated=datetime.now()
        )
        self.edge_metrics[signal_id] = metrics
        logger.info(f"Registered signal {signal_id} with half-life {np.log(2)/estimated_decay_rate:.1f} hours")
        return metrics
    
    def update_signal_performance(self, signal_id: str, trade_return: float):
        """Update signal with new trade performance."""
        if signal_id not in self.edge_metrics:
            return
            
        metrics = self.edge_metrics[signal_id]
        metrics.trades_since_discovery += 1
        
        # Update rolling average return
        n = metrics.trades_since_discovery
        metrics.avg_return_since_discovery = (
            (metrics.avg_return_since_discovery * (n-1) + trade_return) / n
        )
        
        # Recalibrate decay rate based on actual performance
        if n >= 5:
            self._recalibrate_decay_rate(signal_id)
        
        metrics.last_updated = datetime.now()
        self.decay_history[signal_id].append((datetime.now(), metrics.current_value))
    
    def _recalibrate_decay_rate(self, signal_id: str):
        """Recalibrate decay rate based on actual performance degradation."""
        metrics = self.edge_metrics[signal_id]
        
        if metrics.trades_since_discovery < 5:
            return
            
        # Calculate actual performance degradation
        recent_returns = self._get_recent_returns(signal_id, window=10)
        older_returns = self._get_older_returns(signal_id, window=10)
        
        if not recent_returns or not older_returns:
            return
            
        recent_avg = np.mean(recent_returns)
        older_avg = np.mean(older_returns)
        
        if older_avg > 0 and recent_avg < older_avg:
            # Performance degraded - increase decay rate
            degradation_ratio = recent_avg / older_avg if older_avg != 0 else 1.0
            new_decay_rate = metrics.decay_rate * (1.5 - degradation_ratio)
            metrics.decay_rate = min(0.5, new_decay_rate)  # Cap at 0.5
            
            logger.warning(f"Signal {signal_id} decay rate recalibrated: {metrics.decay_rate:.3f}")
    
    def _get_recent_returns(self, signal_id: str, window: int) -> List[float]:
        """Get recent returns for signal."""
        # Placeholder - in production, fetch from trade history
        return []
    
    def _get_older_returns(self, signal_id: str, window: int) -> List[float]:
        """Get older returns for signal."""
        # Placeholder - in production, fetch from trade history
        return []
    
    def get_signal_status(self, signal_id: str) -> Dict[str, Any]:
        """Get current status of a signal."""
        if signal_id not in self.edge_metrics:
            return {'error': 'Signal not found'}
            
        metrics = self.edge_metrics[signal_id]
        current_value = metrics.compute_current_value()
        
        status = 'active'
        if current_value < self.retirement_threshold:
            status = 'retired'
        elif current_value < self.decay_threshold:
            status = 'degraded'
            
        return {
            'signal_id': signal_id,
            'current_value': current_value,
            'initial_value': metrics.initial_value,
            'decay_rate': metrics.decay_rate,
            'half_life_hours': np.log(2) / metrics.decay_rate if metrics.decay_rate > 0 else float('inf'),
            'trades_since_discovery': metrics.trades_since_discovery,
            'avg_return': metrics.avg_return_since_discovery,
            'status': status,
            'hours_since_discovery': (datetime.now() - metrics.discovery_time).total_seconds() / 3600
        }
    
    def get_expired_signals(self) -> List[str]:
        """Get list of signals that should be retired."""
        expired = []
        for signal_id, metrics in self.edge_metrics.items():
            if metrics.compute_current_value() < self.retirement_threshold:
                expired.append(signal_id)
        return expired
    
    def get_all_active_signals(self) -> List[Dict[str, Any]]:
        """Get all non-expired signals sorted by current value."""
        active = []
        for signal_id in self.edge_metrics:
            status = self.get_signal_status(signal_id)
            if status.get('status') != 'retired':
                active.append(status)
        return sorted(active, key=lambda x: x['current_value'], reverse=True)


@dataclass
class SystemLatencyMetrics:
    """Track system latency advantage over institutional data."""
    timestamp: datetime
    avg_latency_ms: float
    min_latency_ms: float
    max_latency_ms: float
    p95_latency_ms: float
    source_breakdown: Dict[str, float] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'timestamp': self.timestamp.isoformat(),
            'avg_latency_ms': self.avg_latency_ms,
            'min_latency_ms': self.min_latency_ms,
            'max_latency_ms': self.max_latency_ms,
            'p95_latency_ms': self.p95_latency_ms,
            'source_breakdown': self.source_breakdown,
        }


class SignalDiscoveryOrchestrator:
    """
    Central orchestrator for the 80-agent Signal Discovery Engine.
    
    Like a Palantir intelligence platform, this orchestrator coordinates
    disparate data sources into a unified anomaly detection system.
    
    Key Features:
    - Deploys 80 specialized agents
    - Continuous anomaly collection
    - Intelligent deduplication
    - Priority scoring
    - Latency tracking vs institutional data
    - Health monitoring
    """
    
    # Agent counts by type
    AGENT_COUNTS = {
        'financial_api': 15,
        'research_paper': 10,
        'social_media': 20,
        'dark_pool': 5,
        'developer_activity': 10,
        'protocol_launch': 10,
        'economic_release': 10,
    }
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize the orchestrator.
        
        Args:
            config: Optional configuration dictionary
        """
        self.config = config or {}
        self.orchestrator_id = str(uuid.uuid4())
        
        # Agent registry
        self.agents: Dict[str, BaseAnomalyAgent] = {}
        self.agent_tasks: Dict[str, asyncio.Task] = {}
        
        # Anomaly management
        self.anomaly_queue: List[AnomalyPriorityScore] = []
        self.anomaly_history: List[MarketAnomaly] = []
        self.max_history = 10000
        
        # Deduplication
        self._dedup_window = timedelta(minutes=5)
        self._recent_anomaly_signatures: Dict[str, datetime] = {}
        
        # Latency tracking
        self._latency_metrics: List[SystemLatencyMetrics] = []
        self._institutional_latency_ms = 900000  # 15 minutes = institutional data lag
        
        # Callbacks
        self._anomaly_callbacks: List[Callable[[MarketAnomaly], None]] = []
        
        # State
        self._running = False
        self._start_time: Optional[datetime] = None
        
        logger.info(f"SignalDiscoveryOrchestrator {self.orchestrator_id} initialized")
    
    def deploy_agent_army(self) -> Dict[str, BaseAnomalyAgent]:
        """
        Deploy all 80 agents with their specialized configurations.
        
        Returns:
            Dictionary of agent_id -> agent
        """
        logger.info("Deploying 80-agent anomaly hunting army...")
        
        agents = {}
        
        # Deploy Financial API Agents (15)
        for i in range(self.AGENT_COUNTS['financial_api']):
            agent_id = f"financial_api_{i:03d}"
            agent = FinancialAPIAgent(
                agent_id=agent_id,
                check_interval_seconds=self.config.get('financial_api_interval', 30.0)
            )
            agents[agent_id] = agent
        
        # Deploy Research Paper Agents (10)
        for i in range(self.AGENT_COUNTS['research_paper']):
            agent_id = f"research_paper_{i:03d}"
            agent = ResearchPaperAgent(
                agent_id=agent_id,
                check_interval_seconds=self.config.get('research_paper_interval', 300.0)
            )
            agents[agent_id] = agent
        
        # Deploy Social Media Agents (20)
        for i in range(self.AGENT_COUNTS['social_media']):
            agent_id = f"social_media_{i:03d}"
            agent = SocialMediaAgent(
                agent_id=agent_id,
                check_interval_seconds=self.config.get('social_media_interval', 10.0)
            )
            agents[agent_id] = agent
        
        # Deploy Dark Pool Agents (5)
        for i in range(self.AGENT_COUNTS['dark_pool']):
            agent_id = f"dark_pool_{i:03d}"
            agent = DarkPoolAgent(
                agent_id=agent_id,
                check_interval_seconds=self.config.get('dark_pool_interval', 5.0)
            )
            agents[agent_id] = agent
        
        # Deploy Developer Activity Agents (10)
        for i in range(self.AGENT_COUNTS['developer_activity']):
            agent_id = f"dev_activity_{i:03d}"
            agent = DeveloperActivityAgent(
                agent_id=agent_id,
                check_interval_seconds=self.config.get('dev_activity_interval', 60.0)
            )
            agents[agent_id] = agent
        
        # Deploy Protocol Launch Agents (10)
        for i in range(self.AGENT_COUNTS['protocol_launch']):
            agent_id = f"protocol_launch_{i:03d}"
            agent = ProtocolLaunchAgent(
                agent_id=agent_id,
                check_interval_seconds=self.config.get('protocol_launch_interval', 120.0)
            )
            agents[agent_id] = agent
        
        # Deploy Economic Release Agents (10)
        for i in range(self.AGENT_COUNTS['economic_release']):
            agent_id = f"econ_release_{i:03d}"
            agent = EconomicReleaseAgent(
                agent_id=agent_id,
                check_interval_seconds=self.config.get('econ_release_interval', 60.0)
            )
            agents[agent_id] = agent
        
        self.agents = agents
        
        total = sum(self.AGENT_COUNTS.values())
        logger.info(f"Deployed {total} agents: {self.AGENT_COUNTS}")
        
        return agents
    
    async def start(self):
        """Start all agents in continuous monitoring mode."""
        if not self.agents:
            self.deploy_agent_army()
        
        self._running = True
        self._start_time = datetime.now()
        
        logger.info("Starting all agents...")
        
        # Start each agent
        for agent_id, agent in self.agents.items():
            task = asyncio.create_task(agent.run_continuously())
            self.agent_tasks[agent_id] = task
        
        # Start anomaly collection
        asyncio.create_task(self._anomaly_collection_loop())
        
        # Start latency tracking
        asyncio.create_task(self._latency_tracking_loop())
        
        logger.info(f"All {len(self.agents)} agents started")
    
    async def stop(self):
        """Stop all agents."""
        self._running = False
        
        logger.info("Stopping all agents...")
        
        # Stop each agent
        for agent in self.agents.values():
            agent.stop()
        
        # Cancel tasks
        for task in self.agent_tasks.values():
            task.cancel()
        
        # Wait for cancellation
        await asyncio.gather(*self.agent_tasks.values(), return_exceptions=True)
        
        logger.info("All agents stopped")
    
    async def _anomaly_collection_loop(self):
        """Continuously collect anomalies from all agents."""
        while self._running:
            try:
                all_anomalies = []
                
                # Collect from each agent
                for agent_id, agent in self.agents.items():
                    try:
                        anomalies = await agent.run_once()
                        all_anomalies.extend(anomalies)
                    except Exception as e:
                        logger.error(f"Error collecting from agent {agent_id}: {e}")
                
                # Process anomalies
                if all_anomalies:
                    await self._process_anomalies(all_anomalies)
                
                await asyncio.sleep(1.0)  # Check every second
                
            except Exception as e:
                logger.error(f"Anomaly collection loop error: {e}")
                await asyncio.sleep(5.0)
    
    async def _process_anomalies(self, anomalies: List[MarketAnomaly]):
        """
        Process collected anomalies: deduplicate, prioritize, route.
        
        Args:
            anomalies: List of raw anomalies from agents
        """
        for anomaly in anomalies:
            # Deduplication check
            if self._is_duplicate(anomaly):
                continue
            
            # Calculate priority
            priority_score = self._calculate_priority(anomaly)
            
            # Add to queue
            priority_item = AnomalyPriorityScore(anomaly, priority_score)
            self.anomaly_queue.append(priority_item)
            
            # Add to history
            self.anomaly_history.append(anomaly)
            if len(self.anomaly_history) > self.max_history:
                self.anomaly_history = self.anomaly_history[-self.max_history:]
            
            # Notify callbacks
            for callback in self._anomaly_callbacks:
                try:
                    callback(anomaly)
                except Exception as e:
                    logger.error(f"Callback error: {e}")
        
        # Sort queue by priority
        self.anomaly_queue.sort(key=lambda x: x.priority_score, reverse=True)
        
        logger.debug(f"Processed {len(anomalies)} anomalies, {len(self.anomaly_queue)} in queue")
    
    def _is_duplicate(self, anomaly: MarketAnomaly) -> bool:
        """
        Check if this anomaly is a duplicate of a recent one.
        
        Uses asset + anomaly type + time window for deduplication.
        """
        signature = f"{anomaly.primary_asset}:{anomaly.anomaly_type.value}:{anomaly.agent_type}"
        now = datetime.now()
        
        if signature in self._recent_anomaly_signatures:
            last_seen = self._recent_anomaly_signatures[signature]
            if now - last_seen < self._dedup_window:
                return True
        
        self._recent_anomaly_signatures[signature] = now
        return False
    
    def _calculate_priority(self, anomaly: MarketAnomaly) -> float:
        """
        Calculate priority score for an anomaly.
        
        Higher score = more important = faster processing.
        
        Factors:
        - Confidence (0.0-1.0)
        - Severity (1-10)
        - Latency advantage (faster = higher)
        - Source reliability
        """
        # Base score from confidence and severity
        base_score = (anomaly.confidence * 0.5) + (anomaly.severity / 10 * 0.3)
        
        # Latency bonus (detected faster = higher priority)
        latency_bonus = 0.0
        if anomaly.latency_ms > 0:
            # Bonus for being faster than institutional (15 min = 900000 ms)
            if anomaly.latency_ms < self._institutional_latency_ms:
                latency_bonus = 0.2 * (1 - (anomaly.latency_ms / self._institutional_latency_ms))
        
        return min(1.0, base_score + latency_bonus)
    
    async def _latency_tracking_loop(self):
        """Track system latency metrics over time."""
        while self._running:
            try:
                # Calculate current metrics
                recent_anomalies = [
                    a for a in self.anomaly_history[-1000:]
                    if a.latency_ms > 0
                ]
                
                if recent_anomalies:
                    latencies = [a.latency_ms for a in recent_anomalies]
                    latencies.sort()
                    
                    metrics = SystemLatencyMetrics(
                        timestamp=datetime.now(),
                        avg_latency_ms=sum(latencies) / len(latencies),
                        min_latency_ms=min(latencies),
                        max_latency_ms=max(latencies),
                        p95_latency_ms=latencies[int(len(latencies) * 0.95)] if len(latencies) > 20 else max(latencies),
                    )
                    
                    self._latency_metrics.append(metrics)
                    if len(self._latency_metrics) > 1000:
                        self._latency_metrics = self._latency_metrics[-1000:]
                
                await asyncio.sleep(60.0)  # Update every minute
                
            except Exception as e:
                logger.error(f"Latency tracking error: {e}")
                await asyncio.sleep(60.0)
    
    def get_priority_anomalies(self, n: int = 100) -> List[AnomalyPriorityScore]:
        """Get the n highest priority anomalies."""
        return self.anomaly_queue[:n]
    
    def get_system_latency_advantage(self) -> Dict[str, Any]:
        """
        Calculate latency advantage over institutional data vendors.
        
        Returns:
            Dictionary with latency metrics and advantage calculation
        """
        if not self._latency_metrics:
            return {
                'status': 'insufficient_data',
                'avg_latency_ms': None,
                'institutional_latency_ms': self._institutional_latency_ms,
                'advantage_ms': None,
                'advantage_minutes': None,
            }
        
        latest = self._latency_metrics[-1]
        advantage_ms = self._institutional_latency_ms - latest.avg_latency_ms
        
        return {
            'status': 'active',
            'avg_latency_ms': latest.avg_latency_ms,
            'min_latency_ms': latest.min_latency_ms,
            'max_latency_ms': latest.max_latency_ms,
            'p95_latency_ms': latest.p95_latency_ms,
            'institutional_latency_ms': self._institutional_latency_ms,
            'advantage_ms': advantage_ms,
            'advantage_minutes': advantage_ms / 60000,
        }
    
    def get_agent_health(self) -> Dict[str, AgentHealth]:
        """Get health metrics for all agents."""
        return {agent_id: agent.get_health() for agent_id, agent in self.agents.items()}
    
    def get_system_status(self) -> Dict[str, Any]:
        """Get comprehensive system status."""
        total_anomalies = len(self.anomaly_history)
        uptime = (datetime.now() - self._start_time).total_seconds() if self._start_time else 0
        
        return {
            'orchestrator_id': self.orchestrator_id,
            'running': self._running,
            'uptime_seconds': uptime,
            'agents_deployed': len(self.agents),
            'agents_running': sum(1 for a in self.agents.values() if a.get_health().is_running),
            'total_anomalies_detected': total_anomalies,
            'anomalies_in_queue': len(self.anomaly_queue),
            'latency_advantage': self.get_system_latency_advantage(),
        }
    
    def register_anomaly_callback(self, callback: Callable[[MarketAnomaly], None]):
        """Register a callback to be called when new anomalies are detected."""
        self._anomaly_callbacks.append(callback)
    
    def remove_anomaly_callback(self, callback: Callable[[MarketAnomaly], None]):
        """Remove a registered callback."""
        if callback in self._anomaly_callbacks:
            self._anomaly_callbacks.remove(callback)


class SignalFragilityIndex:
    """
    Signal Fragility Index
    
    Every signal should have:
    fragility_score = sensitivity to small perturbations
    
    Slightly modify:
    - Input data
    - Timing
    - Execution assumptions
    
    If signal collapses -> fragile -> downgrade
    """
    
    def __init__(self, fragility_threshold: float = 0.6):
        self.fragility_threshold = fragility_threshold
        self.fragility_scores: Dict[str, float] = {}
        self.perturbation_history: Dict[str, List[float]] = defaultdict(list)
        
    def calculate_fragility(
        self,
        signal_id: str,
        base_signal_value: float,
        signal_generator: Callable,
        data: Dict[str, Any],
        perturbation_levels: List[float] = None
    ) -> float:
        """
        Calculate fragility score for a signal.
        
        Args:
            signal_id: Unique identifier for the signal
            base_signal_value: The original signal value
            signal_generator: Function that generates signal from data
            data: Input data for signal generation
            perturbation_levels: Levels of perturbation to test
            
        Returns:
            Fragility score (0-1, higher = more fragile)
        """
        if perturbation_levels is None:
            perturbation_levels = [-0.05, -0.02, 0.02, 0.05]  # ±2%, ±5%
        
        perturbed_values = []
        
        # Test data perturbations
        for perturbation in perturbation_levels:
            perturbed_data = self._perturb_data(data, perturbation)
            try:
                perturbed_signal = signal_generator(perturbed_data)
                perturbed_values.append(perturbed_signal)
            except Exception as e:
                logger.warning(f"Signal generation failed for {signal_id} at {perturbation}: {e}")
                perturbed_values.append(0)
        
        # Calculate fragility
        if not perturbed_values or base_signal_value == 0:
            fragility = 1.0  # Most fragile if can't calculate
        else:
            # Measure how much signal changes relative to base
            deviations = [
                abs(v - base_signal_value) / abs(base_signal_value) 
                for v in perturbed_values if base_signal_value != 0
            ]
            avg_deviation = np.mean(deviations) if deviations else 1.0
            
            # Normalize to 0-1 scale
            # If avg deviation > 50% with 5% data change, very fragile
            fragility = min(1.0, avg_deviation / 0.5)
        
        self.fragility_scores[signal_id] = fragility
        self.perturbation_history[signal_id].extend(perturbed_values)
        
        if fragility > self.fragility_threshold:
            logger.warning(f"Signal {signal_id} is FRAGILE: score={fragility:.2f}")
        
        return fragility
    
    def _perturb_data(self, data: Dict, perturbation: float) -> Dict:
        """Apply perturbation to numeric data fields."""
        perturbed = {}
        for key, value in data.items():
            if isinstance(value, (int, float)) and not isinstance(value, bool):
                perturbed[key] = value * (1 + perturbation)
            elif isinstance(value, dict):
                perturbed[key] = self._perturb_data(value, perturbation)
            elif isinstance(value, list):
                perturbed[key] = [
                    v * (1 + perturbation) if isinstance(v, (int, float)) else v
                    for v in value
                ]
            else:
                perturbed[key] = value
        return perturbed
    
    def is_fragile(self, signal_id: str) -> bool:
        """Check if signal is classified as fragile."""
        return self.fragility_scores.get(signal_id, 0) > self.fragility_threshold
    
    def get_fragility_report(self, signal_id: str) -> Dict[str, Any]:
        """Get fragility report for a signal."""
        if signal_id not in self.fragility_scores:
            return {'error': 'Signal not found'}
        
        return {
            'signal_id': signal_id,
            'fragility_score': self.fragility_scores[signal_id],
            'is_fragile': self.is_fragile(signal_id),
            'threshold': self.fragility_threshold,
            'perturbation_tests': len(self.perturbation_history.get(signal_id, [])),
            'recommendation': (
                'REJECT' if self.is_fragile(signal_id) 
                else 'ACCEPT with caution' if self.fragility_scores[signal_id] > 0.4
                else 'ACCEPT'
            )
        }


class EdgeSaturationDetector:
    """
    Edge Saturation Detector
    
    When too many participants use the same strategy -> edge dies.
    
    Detect:
    - Crowded trades
    - Overused signals
    - Abnormal consensus
    """
    
    def __init__(
        self,
        consensus_threshold: float = 0.75,
        volume_anomaly_threshold: float = 3.0
    ):
        self.consensus_threshold = consensus_threshold
        self.volume_anomaly_threshold = volume_anomaly_threshold
        
        self.signal_usage_history: Dict[str, List[datetime]] = defaultdict(list)
        self.volume_baselines: Dict[str, float] = {}
        self.saturation_alerts: List[Dict] = []
        
    def detect_saturation(
        self,
        signal_id: str,
        market_data: Dict[str, Any],
        signal_population_estimate: int = None
    ) -> Dict[str, Any]:
        """
        Detect if an edge is becoming saturated.
        
        Args:
            signal_id: The signal/edge to check
            market_data: Current market conditions
            signal_population_estimate: Estimated number of participants using this signal
            
        Returns:
            Saturation metrics
        """
        saturation_indicators = {}
        
        # 1. Check for unusual volume
        current_volume = market_data.get('volume', 0)
        avg_volume = market_data.get('average_volume_20d', current_volume)
        
        if avg_volume > 0:
            volume_ratio = current_volume / avg_volume
            if volume_ratio > self.volume_anomaly_threshold:
                saturation_indicators['volume_spike'] = volume_ratio
        
        # 2. Check for crowded positioning
        positioning = market_data.get('positioning_data', {})
        long_pct = positioning.get('long_percentage', 50)
        
        if long_pct > 85 or long_pct < 15:
            saturation_indicators['crowded_positioning'] = abs(long_pct - 50) / 50
        
        # 3. Check social media / sentiment concentration
        social_mentions = market_data.get('social_mentions', 0)
        social_baseline = market_data.get('social_baseline', social_mentions)
        
        if social_baseline > 0:
            mention_ratio = social_mentions / social_baseline
            if mention_ratio > 5:
                saturation_indicators['social_hype'] = mention_ratio
        
        # 4. Check signal frequency
        self.signal_usage_history[signal_id].append(datetime.now())
        
        # Count usage in last 24 hours
        cutoff = datetime.now() - timedelta(hours=24)
        recent_uses = len([t for t in self.signal_usage_history[signal_id] if t > cutoff])
        
        if recent_uses > 100:  # Threshold for "overused"
            saturation_indicators['overused_signal'] = recent_uses / 100
        
        # Calculate composite saturation score
        saturation_score = min(1.0, sum(saturation_indicators.values()) / 3) if saturation_indicators else 0.0
        
        # Determine status
        if saturation_score > 0.8:
            status = 'CRITICAL'
        elif saturation_score > 0.6:
            status = 'HIGH'
        elif saturation_score > 0.4:
            status = 'ELEVATED'
        else:
            status = 'NORMAL'
        
        result = {
            'signal_id': signal_id,
            'saturation_score': saturation_score,
            'status': status,
            'indicators': saturation_indicators,
            'estimated_participants': signal_population_estimate,
            'recommendation': self._get_recommendation(status),
            'timestamp': datetime.now()
        }
        
        if status in ['CRITICAL', 'HIGH']:
            self.saturation_alerts.append(result)
            logger.warning(f"Edge saturation detected for {signal_id}: {status}")
        
        return result
    
    def _get_recommendation(self, status: str) -> str:
        """Get recommendation based on saturation status."""
        recommendations = {
            'CRITICAL': 'STOP using this edge immediately - fully saturated',
            'HIGH': 'Reduce allocation by 75% - approaching saturation',
            'ELEVATED': 'Reduce allocation by 25% - monitor closely',
            'NORMAL': 'Edge is viable - normal operation'
        }
        return recommendations.get(status, 'UNKNOWN')
    
    def get_saturation_alerts(self, since: datetime = None) -> List[Dict]:
        """Get saturation alerts."""
        if since is None:
            since = datetime.now() - timedelta(days=7)
        
        return [a for a in self.saturation_alerts if a.get('timestamp', datetime.min) > since]


class EdgeReinforcementEngine:
    """
    Edge Reinforcement Engine
    
    When edge proves strong:
    - Increase allocation
    - Exploit aggressively
    
    But within limits.
    """
    
    def __init__(
        self,
        min_trades_for_reinforcement: int = 10,
        sharpe_threshold: float = 1.5,
        max_position_multiplier: float = 2.0
    ):
        self.min_trades = min_trades_for_reinforcement
        self.sharpe_threshold = sharpe_threshold
        self.max_multiplier = max_position_multiplier
        
        self.edge_performance: Dict[str, Dict] = {}
        self.reinforcement_levels: Dict[str, float] = {}
        
    def evaluate_edge(
        self,
        edge_id: str,
        trade_history: List[Dict],
        current_allocation: float
    ) -> Dict[str, Any]:
        """
        Evaluate whether edge should be reinforced.
        
        Args:
            edge_id: Unique edge identifier
            trade_history: List of trade outcomes
            current_allocation: Current capital allocation
            
        Returns:
            Reinforcement recommendation
        """
        if len(trade_history) < self.min_trades:
            return {
                'edge_id': edge_id,
                'recommendation': 'INSUFFICIENT_DATA',
                'current_allocation': current_allocation,
                'recommended_allocation': current_allocation,
                'multiplier': 1.0
            }
        
        # Calculate metrics
        returns = [t.get('pnl_pct', 0) for t in trade_history]
        
        sharpe = np.mean(returns) / np.std(returns) if np.std(returns) > 0 else 0
        win_rate = np.sum(np.array(returns) > 0) / len(returns)
        
        # Calculate drawdown
        cumulative = np.cumprod(1 + np.array(returns))
        peak = np.maximum.accumulate(cumulative)
        drawdowns = (peak - cumulative) / peak
        max_dd = np.max(drawdowns)
        
        # Determine reinforcement level
        reinforcement_score = (
            min(1.0, sharpe / self.sharpe_threshold) * 0.5 +
            win_rate * 0.3 +
            (1 - min(1.0, max_dd / 0.15)) * 0.2
        )
        
        # Calculate multiplier
        if reinforcement_score > 0.9:
            multiplier = self.max_multiplier
        elif reinforcement_score > 0.7:
            multiplier = 1.5
        elif reinforcement_score > 0.5:
            multiplier = 1.25
        else:
            multiplier = 1.0
        
        # Apply limits
        recommended_allocation = current_allocation * multiplier
        
        # Cap at 20% of total capital per edge
        max_allocation = 0.20
        if recommended_allocation > max_allocation:
            recommended_allocation = max_allocation
            multiplier = max_allocation / current_allocation if current_allocation > 0 else 1.0
        
        self.reinforcement_levels[edge_id] = multiplier
        
        result = {
            'edge_id': edge_id,
            'recommendation': (
                'REINFORCE' if multiplier > 1.2
                else 'MAINTAIN' if multiplier >= 1.0
                else 'REDUCE'
            ),
            'current_allocation': current_allocation,
            'recommended_allocation': recommended_allocation,
            'multiplier': multiplier,
            'metrics': {
                'sharpe': sharpe,
                'win_rate': win_rate,
                'max_drawdown': max_dd,
                'reinforcement_score': reinforcement_score
            },
            'trades_evaluated': len(trade_history)
        }
        
        if multiplier > 1.2:
            logger.info(f"Reinforcing edge {edge_id}: multiplier={multiplier:.2f}, sharpe={sharpe:.2f}")
        
        return result
    
    def get_reinforcement_summary(self) -> Dict[str, Any]:
        """Get summary of all reinforcement levels."""
        if not self.reinforcement_levels:
            return {'status': 'no_data'}
        
        levels = list(self.reinforcement_levels.values())
        
        return {
            'edges_reinforced': sum(1 for m in levels if m > 1.2),
            'edges_maintained': sum(1 for m in levels if 0.9 <= m <= 1.2),
            'edges_reduced': sum(1 for m in levels if m < 0.9),
            'avg_multiplier': np.mean(levels),
            'max_multiplier': max(levels),
            'min_multiplier': min(levels),
            'reinforcement_levels': self.reinforcement_levels
        }


class SignalDependencyGraph:
    """
    Signal Dependency Graph
    
    Right now signals are treated independently.
    
    That's wrong.
    
    Idea:
    Map:
    - signal A depends on signal B
    - signal C contradicts signal A
    - signal D amplifies signal B
    
    Result:
    - removes redundancy
    - improves reasoning coherence
    - prevents double-counting edge
    """
    
    def __init__(self):
        self.dependencies: Dict[str, List[str]] = defaultdict(list)  # signal -> dependencies
        self.contradictions: Dict[str, List[str]] = defaultdict(list)  # signal -> contradictions
        self.amplifications: Dict[str, List[str]] = defaultdict(list)  # signal -> amplifiers
        self.signal_weights: Dict[str, float] = {}  # adjusted weights
        
    def register_signal(
        self,
        signal_id: str,
        dependencies: Optional[List[str]] = None,
        contradicts: Optional[List[str]] = None,
        amplified_by: Optional[List[str]] = None,
        base_weight: float = 1.0
    ):
        """Register a signal with its dependency relationships."""
        if dependencies:
            self.dependencies[signal_id] = dependencies
        if contradicts:
            self.contradictions[signal_id] = contradicts
        if amplified_by:
            self.amplifications[signal_id] = amplified_by
            
        self.signal_weights[signal_id] = base_weight
    
    def analyze_signal_conflicts(self, active_signals: List[str]) -> Dict[str, Any]:
        """
        Analyze conflicts and dependencies among active signals.
        
        Returns:
            Dictionary with conflict analysis
        """
        conflicts = []
        dependencies_satisfied = []
        amplification_boosts = []
        
        active_set = set(active_signals)
        
        for signal in active_signals:
            # Check for contradictions
            contradictions = self.contradictions.get(signal, [])
            for contradicting in contradictions:
                if contradicting in active_set:
                    conflicts.append({
                        'signal_a': signal,
                        'signal_b': contradicting,
                        'type': 'contradiction',
                        'severity': 'high'
                    })
            
            # Check for dependencies
            deps = self.dependencies.get(signal, [])
            satisfied = [d for d in deps if d in active_set]
            missing = [d for d in deps if d not in active_set]
            
            if deps:
                dependencies_satisfied.append({
                    'signal': signal,
                    'dependencies': deps,
                    'satisfied': satisfied,
                    'missing': missing,
                    'dependency_ratio': len(satisfied) / len(deps)
                })
            
            # Check for amplifications
            amps = self.amplifications.get(signal, [])
            active_amps = [a for a in amps if a in active_set]
            
            if active_amps:
                amplification_boosts.append({
                    'signal': signal,
                    'amplified_by': active_amps,
                    'boost_factor': 1.0 + (0.1 * len(active_amps))
                })
        
        # Calculate adjusted weights
        adjusted_weights = self._calculate_adjusted_weights(active_signals, conflicts, amplification_boosts)
        
        return {
            'conflicts': conflicts,
            'dependencies': dependencies_satisfied,
            'amplifications': amplification_boosts,
            'original_weights': {s: self.signal_weights.get(s, 1.0) for s in active_signals},
            'adjusted_weights': adjusted_weights,
            'redundancy_score': len(conflicts) / len(active_signals) if active_signals else 0,
            'recommendation': 'RESOLVE_CONFLICTS' if conflicts else 'PROCEED'
        }
    
    def _calculate_adjusted_weights(
        self,
        signals: List[str],
        conflicts: List[Dict],
        amplifications: List[Dict]
    ) -> Dict[str, float]:
        """Calculate adjusted weights based on dependencies."""
        weights = {s: self.signal_weights.get(s, 1.0) for s in signals}
        
        # Apply conflict penalties
        conflict_signals = set()
        for conflict in conflicts:
            conflict_signals.add(conflict['signal_a'])
            conflict_signals.add(conflict['signal_b'])
        
        for signal in conflict_signals:
            if signal in weights:
                weights[signal] *= 0.7  # Reduce weight for conflicting signals
        
        # Apply amplification boosts
        for amp in amplifications:
            signal = amp['signal']
            if signal in weights:
                weights[signal] *= amp['boost_factor']
        
        return weights
    
    def get_independent_signals(self, signals: List[str]) -> List[str]:
        """Get subset of signals with minimal dependencies and no contradictions."""
        analysis = self.analyze_signal_conflicts(signals)
        
        # Filter out signals with conflicts
        conflict_signals = set()
        for conflict in analysis['conflicts']:
            # Keep the one with higher base weight
            weight_a = self.signal_weights.get(conflict['signal_a'], 1.0)
            weight_b = self.signal_weights.get(conflict['signal_b'], 1.0)
            
            if weight_a < weight_b:
                conflict_signals.add(conflict['signal_a'])
            else:
                conflict_signals.add(conflict['signal_b'])
        
        # Filter out signals with unsatisfied dependencies
        dep_failures = set()
        for dep_info in analysis['dependencies']:
            if dep_info['dependency_ratio'] < 0.5:
                dep_failures.add(dep_info['signal'])
        
        return [s for s in signals if s not in conflict_signals and s not in dep_failures]


class StrategyDNAMapper:
    """
    Strategy DNA Mapping
    
    Each strategy has:
    - conditions it thrives in
    - conditions it fails in
    - sensitivity profile
    
    Map this explicitly.
    """
    
    def __init__(self):
        self.strategy_profiles: Dict[str, Dict[str, Any]] = {}
        self.condition_history: Dict[str, List[Dict]] = defaultdict(list)
        
    def map_strategy_dna(
        self,
        strategy_id: str,
        optimal_regimes: List[str],
        failure_regimes: List[str],
        required_conditions: List[str],
        sensitivity_factors: Dict[str, float],
        performance_decay_rate: float = 0.05
    ):
        """
        Map the DNA profile of a strategy.
        
        Args:
            strategy_id: Unique strategy identifier
            optimal_regimes: Market regimes where strategy thrives
            failure_regimes: Market regimes where strategy fails
            required_conditions: Conditions that must be present
            sensitivity_factors: Dict of factor -> sensitivity score (0-1)
            performance_decay_rate: Rate at which edge decays
        """
        self.strategy_profiles[strategy_id] = {
            'strategy_id': strategy_id,
            'optimal_regimes': optimal_regimes,
            'failure_regimes': failure_regimes,
            'required_conditions': required_conditions,
            'sensitivity_factors': sensitivity_factors,
            'performance_decay_rate': performance_decay_rate,
            'dna_fingerprint': self._generate_fingerprint(
                optimal_regimes, failure_regimes, sensitivity_factors
            ),
            'mapped_at': datetime.now()
        }
    
    def _generate_fingerprint(
        self,
        optimal: List[str],
        failure: List[str],
        sensitivity: Dict[str, float]
    ) -> str:
        """Generate a unique fingerprint for this strategy DNA."""
        # Create a hash based on key characteristics
        key = f"{'|'.join(sorted(optimal))}__{'|'.join(sorted(failure))}__{str(sorted(sensitivity.items()))}"
        return hashlib.md5(key.encode()).hexdigest()[:16]
    
    def analyze_current_fit(
        self,
        strategy_id: str,
        current_regime: str,
        current_conditions: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Analyze how well current conditions fit strategy DNA."""
        profile = self.strategy_profiles.get(strategy_id)
        
        if not profile:
            return {'status': 'unknown_strategy'}
        
        # Check regime compatibility
        is_optimal_regime = current_regime in profile['optimal_regimes']
        is_failure_regime = current_regime in profile['failure_regimes']
        
        # Check condition satisfaction
        conditions_met = sum(
            1 for c in profile['required_conditions']
            if current_conditions.get(c, False)
        )
        condition_ratio = conditions_met / len(profile['required_conditions']) if profile['required_conditions'] else 1.0
        
        # Calculate sensitivity exposure
        sensitivity_risk = 0
        for factor, sensitivity in profile['sensitivity_factors'].items():
            factor_value = current_conditions.get(factor, 0)
            sensitivity_risk += sensitivity * factor_value
        
        # Calculate overall fit score
        if is_failure_regime:
            fit_score = 0.0
        elif is_optimal_regime:
            fit_score = 1.0 * condition_ratio * (1 - sensitivity_risk * 0.5)
        else:
            fit_score = 0.5 * condition_ratio * (1 - sensitivity_risk * 0.5)
        
        return {
            'strategy_id': strategy_id,
            'fit_score': fit_score,
            'is_optimal_regime': is_optimal_regime,
            'is_failure_regime': is_failure_regime,
            'condition_satisfaction': condition_ratio,
            'sensitivity_exposure': sensitivity_risk,
            'recommendation': self._get_recommendation(fit_score, is_failure_regime)
        }
    
    def _get_recommendation(self, fit_score: float, is_failure_regime: bool) -> str:
        """Get recommendation based on fit score."""
        if is_failure_regime:
            return 'AVOID: Strategy in known failure regime'
        elif fit_score > 0.8:
            return 'OPTIMAL: Strong conditions for strategy'
        elif fit_score > 0.5:
            return 'CAUTION: Marginal conditions, reduce size'
        else:
            return 'AVOID: Poor conditions for strategy'


class SystemHealthMonitor:
    """
    System Health Index
    
    Meta-layer.
    
    Track:
    - system_coherence
    - signal_quality
    - execution_efficiency
    - risk_stability
    - confidence_calibration
    
    If degraded -> reduce trading activity
    """
    
    def __init__(self):
        self.health_metrics: Dict[str, Deque] = {
            'system_coherence': deque(maxlen=100),
            'signal_quality': deque(maxlen=100),
            'execution_efficiency': deque(maxlen=100),
            'risk_stability': deque(maxlen=100),
            'confidence_calibration': deque(maxlen=100)
        }
        self.health_thresholds = {
            'critical': 0.3,
            'warning': 0.6,
            'healthy': 0.8
        }
        
    def record_metric(self, metric_name: str, value: float, timestamp: Optional[datetime] = None):
        """Record a health metric value."""
        if metric_name in self.health_metrics:
            self.health_metrics[metric_name].append({
                'value': value,
                'timestamp': timestamp or datetime.now()
            })
    
    def calculate_health_index(self) -> Dict[str, Any]:
        """Calculate overall system health index."""
        component_scores = {}
        
        for metric_name, values in self.health_metrics.items():
            if len(values) < 10:
                component_scores[metric_name] = {'status': 'insufficient_data', 'score': 0.5}
                continue
            
            recent_values = [v['value'] for v in list(values)[-20:]]
            avg_value = np.mean(recent_values)
            trend = recent_values[-1] - recent_values[0] if len(recent_values) > 1 else 0
            
            component_scores[metric_name] = {
                'score': avg_value,
                'trend': trend,
                'status': self._classify_health(avg_value)
            }
        
        # Calculate overall health
        scores = [s['score'] for s in component_scores.values() if isinstance(s.get('score'), (int, float))]
        overall_health = np.mean(scores) if scores else 0.5
        
        return {
            'overall_health': overall_health,
            'health_status': self._classify_health(overall_health),
            'component_scores': component_scores,
            'trading_recommendation': self._get_trading_recommendation(overall_health),
            'degraded_components': [k for k, v in component_scores.items() if v.get('status') in ['critical', 'warning']]
        }
    
    def _classify_health(self, score: float) -> str:
        """Classify health score into status."""
        if score < self.health_thresholds['critical']:
            return 'critical'
        elif score < self.health_thresholds['warning']:
            return 'warning'
        elif score < self.health_thresholds['healthy']:
            return 'fair'
        else:
            return 'healthy'
    
    def _get_trading_recommendation(self, health: float) -> str:
        """Get trading recommendation based on health."""
        if health < self.health_thresholds['critical']:
            return 'HALT_TRADING: Critical system degradation'
        elif health < self.health_thresholds['warning']:
            return 'REDUCE_SIZE: Warning level - reduce all positions by 50%'
        elif health < self.health_thresholds['healthy']:
            return 'CAUTION: Fair health - proceed with care'
        else:
            return 'NORMAL: Healthy system - standard operations'


class DecisionEntropyMonitor:
    """
    Decision Entropy Monitor
    
    Measure randomness in decisions.
    
    entropy ↑ = inconsistency ↑
    
    High entropy = unstable intelligence
    """
    
    def __init__(self, window_size: int = 50):
        self.window_size = window_size
        self.decisions: Deque[Dict] = deque(maxlen=window_size * 2)
        
    def record_decision(
        self,
        decision: str,
        confidence: float,
        signal_type: str,
        regime: str,
        features: Optional[Dict[str, float]] = None
    ):
        """Record a decision for entropy analysis."""
        self.decisions.append({
            'decision': decision,
            'confidence': confidence,
            'signal_type': signal_type,
            'regime': regime,
            'features': features or {},
            'timestamp': datetime.now()
        })
    
    def calculate_entropy(self) -> Dict[str, Any]:
        """Calculate decision entropy metrics."""
        if len(self.decisions) < self.window_size:
            return {'status': 'insufficient_data'}
        
        recent = list(self.decisions)[-self.window_size:]
        
        # Calculate decision distribution entropy
        decision_counts = Counter(d['decision'] for d in recent)
        total = len(recent)
        
        decision_probs = [count / total for count in decision_counts.values()]
        decision_entropy = -sum(p * np.log2(p) for p in decision_probs if p > 0)
        max_entropy = np.log2(len(decision_counts)) if decision_counts else 1
        normalized_entropy = decision_entropy / max_entropy if max_entropy > 0 else 0
        
        # Calculate confidence variance (instability indicator)
        confidences = [d['confidence'] for d in recent]
        confidence_variance = np.var(confidences)
        
        # Calculate signal type switching rate
        signal_types = [d['signal_type'] for d in recent]
        switches = sum(1 for i in range(1, len(signal_types)) if signal_types[i] != signal_types[i-1])
        switch_rate = switches / (len(signal_types) - 1) if len(signal_types) > 1 else 0
        
        # Calculate regime consistency
        regimes = [d['regime'] for d in recent]
        regime_entropy = self._calculate_regime_entropy(regimes)
        
        # Overall instability score
        instability_score = (
            normalized_entropy * 0.3 +
            confidence_variance * 0.3 +
            switch_rate * 0.2 +
            regime_entropy * 0.2
        )
        
        return {
            'decision_entropy': normalized_entropy,
            'confidence_variance': confidence_variance,
            'signal_switch_rate': switch_rate,
            'regime_entropy': regime_entropy,
            'instability_score': instability_score,
            'is_stable': instability_score < 0.5,
            'recommendation': self._get_entropy_recommendation(instability_score)
        }
    
    def _calculate_regime_entropy(self, regimes: List[str]) -> float:
        """Calculate entropy of regime distribution."""
        if not regimes:
            return 0
        
        regime_counts = Counter(regimes)
        total = len(regimes)
        probs = [count / total for count in regime_counts.values()]
        
        entropy = -sum(p * np.log2(p) for p in probs if p > 0)
        max_ent = np.log2(len(regime_counts))
        
        return entropy / max_ent if max_ent > 0 else 0
    
    def _get_entropy_recommendation(self, instability: float) -> str:
        """Get recommendation based on instability score."""
        if instability > 0.8:
            return 'CRITICAL: Decision making highly unstable. Halt and diagnose.'
        elif instability > 0.6:
            return 'WARNING: Elevated entropy. Review decision criteria.'
        elif instability > 0.4:
            return 'CAUTION: Moderate inconsistency. Monitor closely.'
        else:
            return 'STABLE: Decision making consistent and stable.'


class OptionsImpliedEdgeCalculator:
    """
    Options Implied Edge Calculator
    
    Calculates edge from options market:
    - Implied volatility vs realized volatility
    - Put/call skew information
    - Volatility term structure
    - Risk reversal signals
    """
    
    def __init__(self):
        self.iv_history: Deque[Dict] = deque(maxlen=30)
        self.rv_history: Deque[Dict] = deque(maxlen=30)
        
    def update_volatility_data(
        self,
        implied_vol: float,
        realized_vol: float,
        skew_25d: float,  # 25 delta put/call skew
        risk_reversal: float,  # 25d call IV - 25d put IV
        term_structure_slope: float,
        timestamp: Optional[datetime] = None
    ):
        """Update options volatility data."""
        self.iv_history.append({
            'timestamp': timestamp or datetime.now(),
            'implied_vol': implied_vol,
            'skew': skew_25d,
            'risk_reversal': risk_reversal,
            'term_slope': term_structure_slope
        })
        
        self.rv_history.append({
            'timestamp': timestamp or datetime.now(),
            'realized_vol': realized_vol
        })
    
    def calculate_implied_edge(self) -> Dict[str, Any]:
        """Calculate edge from options market."""
        if len(self.iv_history) < 5 or len(self.rv_history) < 5:
            return {'status': 'insufficient_data'}
        
        recent_iv = list(self.iv_history)[-5:]
        recent_rv = list(self.rv_history)[-5:]
        
        avg_iv = np.mean([d['implied_vol'] for d in recent_iv])
        avg_rv = np.mean([d['realized_vol'] for d in recent_rv])
        
        # IV-RV spread
        iv_rv_spread = avg_iv - avg_rv
        
        # Skew analysis
        avg_skew = np.mean([d['skew'] for d in recent_iv])
        
        # Risk reversal
        avg_rr = np.mean([d['risk_reversal'] for d in recent_iv])
        
        # Edge calculation
        # Positive edge when IV < RV (options cheap) or predicting direction from skew
        edge_score = 0
        edge_signals = []
        
        if iv_rv_spread < -0.02:  # IV 2% below RV
            edge_score += 0.3
            edge_signals.append('options_cheap')
        elif iv_rv_spread > 0.05:  # IV 5% above RV
            edge_score -= 0.2
            edge_signals.append('options_expensive')
        
        # Skew signals crash risk or upside potential
        if avg_skew < -0.05:  # Put skew elevated
            edge_score -= 0.2
            edge_signals.append('crash_priced_in')
        
        # Risk reversal shows directional bias
        if avg_rr > 0.02:
            edge_signals.append('bullish_bias')
            edge_score += 0.1
        elif avg_rr < -0.02:
            edge_signals.append('bearish_bias')
            edge_score -= 0.1
        
        return {
            'edge_score': edge_score,
            'avg_implied_vol': avg_iv,
            'avg_realized_vol': avg_rv,
            'iv_rv_spread': iv_rv_spread,
            'skew': avg_skew,
            'risk_reversal': avg_rr,
            'edge_signals': edge_signals,
            'recommendation': (
                'Buy options / Long gamma' if edge_score > 0.2
                else 'Sell options / Short gamma' if edge_score < -0.2
                else 'Neutral options exposure'
            )
        }


class CrossAssetMomentumLeader:
    """
    Cross Asset Momentum Leader
    
    Identifies which asset class is leading momentum.
    
    Example: Bonds move first, then equities follow.
    Trade the laggard in direction of leader.
    """
    
    def __init__(self, lookback_days: int = 5):
        self.lookback_days = lookback_days
        self.asset_returns: Dict[str, Deque[Dict]] = {}
        
    def update_returns(self, asset: str, daily_return: float, timestamp: Optional[datetime] = None):
        """Update returns for an asset."""
        if asset not in self.asset_returns:
            self.asset_returns[asset] = deque(maxlen=self.lookback_days)
        
        self.asset_returns[asset].append({
            'return': daily_return,
            'timestamp': timestamp or datetime.now()
        })
    
    def identify_leaders_and_laggards(self) -> Dict[str, Any]:
        """Identify which assets are leading vs lagging."""
        if len(self.asset_returns) < 2:
            return {'status': 'insufficient_assets'}
        
        # Calculate momentum scores
        momentum_scores = {}
        
        for asset, history in self.asset_returns.items():
            if len(history) < 3:
                continue
            
            returns = [h['return'] for h in history]
            
            # Momentum = recent returns + consistency
            recent_return = returns[-1]
            consistency = 1.0 - np.std(returns) if len(returns) > 1 else 0
            
            momentum_scores[asset] = {
                'recent_return': recent_return,
                'consistency': consistency,
                'score': recent_return * consistency,
                'cumulative_return': np.prod([1 + r for r in returns]) - 1
            }
        
        if not momentum_scores:
            return {'status': 'insufficient_data'}
        
        # Sort by momentum score
        sorted_assets = sorted(
            momentum_scores.items(),
            key=lambda x: x[1]['score'],
            reverse=True
        )
        
        leaders = [a[0] for a in sorted_assets[:2]]
        laggards = [a[0] for a in sorted_assets[-2:]]
        
        # Calculate lead-lag correlation
        lead_lag_signals = []
        if len(sorted_assets) >= 2:
            leader = sorted_assets[0]
            laggard = sorted_assets[-1]
            
            # If leader strongly positive and laggard negative or flat
            if leader[1]['score'] > 0.01 and laggard[1]['score'] < 0:
                lead_lag_signals.append({
                    'leader': leader[0],
                    'laggard': laggard[0],
                    'signal': f"Long {laggard[0]} following {leader[0]} strength",
                    'confidence': leader[1]['consistency']
                })
        
        return {
            'momentum_rankings': sorted_assets,
            'leaders': leaders,
            'laggards': laggards,
            'lead_lag_signals': lead_lag_signals,
            'strongest_momentum': sorted_assets[0] if sorted_assets else None,
            'weakest_momentum': sorted_assets[-1] if sorted_assets else None
        }


class TermStructureRollOptimizer:
    """
    Term Structure Roll Optimizer
    
    Optimizes futures roll timing based on term structure.
    
    Contango (upward sloping): Roll late (sell high, buy higher)
    Backwardation (downward): Roll early (sell high, buy lower)
    """
    
    def __init__(self):
        self.term_structure: Dict[str, Dict[int, float]] = {}  # symbol -> expiry -> price
        self.roll_history: List[Dict] = []
        
    def update_term_structure(self, symbol: str, expiry_months: int, price: float):
        """Update futures price for a given expiry."""
        if symbol not in self.term_structure:
            self.term_structure[symbol] = {}
        
        self.term_structure[symbol][expiry_months] = price
    
    def calculate_roll_yield(self, symbol: str) -> Dict[str, Any]:
        """Calculate roll yield and optimize roll timing."""
        structure = self.term_structure.get(symbol, {})
        
        if len(structure) < 2:
            return {'status': 'insufficient_data'}
        
        # Sort by expiry
        sorted_expiry = sorted(structure.items())
        
        front_price = sorted_expiry[0][1]
        back_price = sorted_expiry[1][1]
        
        # Calculate annualized roll yield
        months_diff = sorted_expiry[1][0] - sorted_expiry[0][0]
        price_diff = back_price - front_price
        
        roll_yield = (price_diff / front_price) * (12 / months_diff)
        
        # Determine structure
        structure_type = 'contango' if roll_yield > 0 else 'backwardation'
        
        # Optimize roll timing
        if structure_type == 'contango':
            # In contango: roll as late as possible (capture premium)
            optimal_roll_days = 2  # Days before expiry
            strategy = 'roll_late_capture_premium'
        else:
            # In backwardation: roll early (avoid paying premium)
            optimal_roll_days = 10
            strategy = 'roll_early_avoid_premium'
        
        return {
            'symbol': symbol,
            'term_structure': structure_type,
            'annualized_roll_yield': roll_yield,
            'front_price': front_price,
            'back_price': back_price,
            'optimal_roll_days_before_expiry': optimal_roll_days,
            'roll_strategy': strategy,
            'roll_implication': (
                'Positive carry - hold front' if structure_type == 'backwardation'
                else 'Negative carry - minimize front exposure'
            )
        }


class CalendarSpreadSelector:
    """
    Calendar Spread Selector
    
    Selects optimal calendar spread pairs based on:
    - Term structure curvature
    - Seasonal patterns
    - Carry attractiveness
    """
    
    def __init__(self):
        self.spread_opportunities: List[Dict] = []
        
    def analyze_calendar_opportunity(
        self,
        symbol: str,
        front_price: float,
        back_price: float,
        front_iv: float,
        back_iv: float,
        days_to_front_expiry: int,
        days_to_back_expiry: int
    ) -> Dict[str, Any]:
        """Analyze a calendar spread opportunity."""
        
        # Price spread
        price_spread = back_price - front_price
        
        # Implied vol spread
        iv_spread = back_iv - front_iv
        
        # Time to expiry ratio
        time_ratio = days_to_back_expiry / days_to_front_expiry if days_to_front_expiry > 0 else 0
        
        # Theta extraction potential
        front_theta_per_day = front_iv / np.sqrt(days_to_front_expiry) if days_to_front_expiry > 0 else 0
        back_theta_per_day = back_iv / np.sqrt(days_to_back_expiry) if days_to_back_expiry > 0 else 0
        theta_capture = front_theta_per_day - back_theta_per_day
        
        # Score the opportunity
        score = 0
        if iv_spread < -0.02:  # Back month cheaper
            score += 0.3
        if theta_capture > 0.001:  # Good theta decay
            score += 0.3
        if abs(price_spread) < front_price * 0.02:  # Tight price spread
            score += 0.2
        
        opportunity = {
            'symbol': symbol,
            'front_price': front_price,
            'back_price': back_price,
            'price_spread': price_spread,
            'front_iv': front_iv,
            'back_iv': back_iv,
            'iv_spread': iv_spread,
            'theta_capture': theta_capture,
            'score': score,
            'recommendation': (
                'SELL calendar' if score > 0.6 and price_spread > 0
                else 'BUY calendar' if score > 0.6 and price_spread < 0
                else 'PASS'
            )
        }
        
        self.spread_opportunities.append(opportunity)
        
        return opportunity
