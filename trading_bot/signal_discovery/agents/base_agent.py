"""
Base Anomaly Agent
==================

Abstract base class for all 80 anomaly-hunting agents in Layer 1.

Strict Job Definition:
1. Monitor specific data source(s)
2. Detect statistical anomalies
3. Report with confidence score
4. DO NOT classify (Layer 2's job)
5. DO NOT trade (Layer 3's job)
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional
import logging
import asyncio
import uuid

logger = logging.getLogger(__name__)


class AnomalyType(Enum):
    """Types of market anomalies that agents can detect."""
    STATISTICAL_OUTLIER = "statistical_outlier"
    REGIME_CHANGE = "regime_change"
    CROSS_ASSET_DIVERGENCE = "cross_asset_divergence"
    EARLY_DEVIATION = "early_deviation"
    NETWORK_ANOMALY = "network_anomaly"
    TIME_SERIES_CHANGEPOINT = "time_series_changepoint"
    VOLUME_ANOMALY = "volume_anomaly"
    VOLATILITY_ANOMALY = "volatility_anomaly"
    CORRELATION_BREAKDOWN = "correlation_breakdown"
    LIQUIDITY_ANOMALY = "liquidity_anomaly"


class DataSource(Enum):
    """Data sources that agents monitor."""
    # Financial APIs
    BLOOMBERG = "bloomberg"
    REUTERS = "reuters"
    ALPHA_VANTAGE = "alpha_vantage"
    QUANDL = "quandl"
    FRED = "fred"
    TRADINGVIEW = "tradingview"
    COINGECKO = "coingecko"
    
    # Research
    ARXIV = "arxiv"
    SSRN = "ssrn"
    JSTOR = "jstor"
    GOOGLE_SCHOLAR = "google_scholar"
    NBER = "nber"
    FED_RESEARCH = "fed_research"
    
    # Social Media
    TWITTER = "twitter"
    REDDIT = "reddit"
    DISCORD = "discord"
    TELEGRAM = "telegram"
    STOCKTWITS = "stocktwits"
    HACKERNEWS = "hackernews"
    
    # Dark Pools
    FINRA_ATS = "finra_ats"
    CBOE_MIDPOINT = "cboe_midpoint"
    IEX = "iex"
    DARK_POOL_PROP = "dark_pool_proprietary"
    
    # Developer Activity
    GITHUB = "github"
    GITLAB = "gitlab"
    STACK_OVERFLOW = "stack_overflow"
    DEV_BLOGS = "dev_blogs"
    
    # Protocol Launches
    DEFI_LLAMA = "defi_llama"
    TOKEN_TERMINAL = "token_terminal"
    GITHUB_RELEASES = "github_releases"
    GOVERNANCE_VOTES = "governance_votes"
    
    # Economic Releases
    BLS = "bls"
    BEA = "bea"
    FED = "fed"
    ECB = "ecb"
    BOJ = "boj"
    IMF = "imf"
    WORLD_BANK = "world_bank"


@dataclass
class MarketAnomaly:
    """
    A detected market anomaly reported by an agent.
    
    This is a raw signal before classification by Layer 2.
    """
    # Identification
    anomaly_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    timestamp: datetime = field(default_factory=datetime.now)
    
    # Source
    agent_id: str = ""
    agent_type: str = ""
    data_source: DataSource = None
    
    # Anomaly characteristics
    anomaly_type: AnomalyType = None
    confidence: float = 0.0  # 0.0 to 1.0
    severity: int = 1  # 1-10 scale
    
    # Affected assets
    primary_asset: str = ""
    related_assets: List[str] = field(default_factory=list)
    
    # Raw data
    raw_data: Dict[str, Any] = field(default_factory=dict)
    description: str = ""
    
    # Detection metadata
    detection_method: str = ""
    statistical_significance: float = 0.0  # p-value or z-score
    
    # Latency tracking
    source_timestamp: Optional[datetime] = None
    detection_timestamp: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert anomaly to dictionary for serialization."""
        return {
            'anomaly_id': self.anomaly_id,
            'timestamp': self.timestamp.isoformat(),
            'agent_id': self.agent_id,
            'agent_type': self.agent_type,
            'data_source': self.data_source.value if self.data_source else None,
            'anomaly_type': self.anomaly_type.value if self.anomaly_type else None,
            'confidence': self.confidence,
            'severity': self.severity,
            'primary_asset': self.primary_asset,
            'related_assets': self.related_assets,
            'raw_data': self.raw_data,
            'description': self.description,
            'detection_method': self.detection_method,
            'statistical_significance': self.statistical_significance,
            'source_timestamp': self.source_timestamp.isoformat() if self.source_timestamp else None,
            'detection_timestamp': self.detection_timestamp.isoformat(),
        }
    
    @property
    def latency_ms(self) -> float:
        """Calculate latency from source to detection in milliseconds."""
        if self.source_timestamp:
            delta = self.detection_timestamp - self.source_timestamp
            return delta.total_seconds() * 1000
        return 0.0


@dataclass
class AgentHealth:
    """Health metrics for an agent."""
    agent_id: str
    is_running: bool = False
    last_run: Optional[datetime] = None
    success_rate: float = 1.0
    avg_latency_ms: float = 0.0
    errors_last_hour: int = 0
    anomalies_detected_last_hour: int = 0
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'agent_id': self.agent_id,
            'is_running': self.is_running,
            'last_run': self.last_run.isoformat() if self.last_run else None,
            'success_rate': self.success_rate,
            'avg_latency_ms': self.avg_latency_ms,
            'errors_last_hour': self.errors_last_hour,
            'anomalies_detected_last_hour': self.anomalies_detected_last_hour,
        }


class BaseAnomalyAgent(ABC):
    """
    Abstract base class for all anomaly-hunting agents.
    
    STRICT JOB DEFINITION:
    1. Monitor specific data source(s)
    2. Detect statistical anomalies
    3. Report with confidence score
    4. DO NOT classify (Layer 2's job)
    5. DO NOT trade (Layer 3's job)
    
    Agents run continuously on configurable intervals and report
    anomalies back to the SignalDiscoveryOrchestrator.
    """
    
    def __init__(self, 
                 agent_id: str,
                 data_sources: List[DataSource],
                 check_interval_seconds: float = 60.0):
        """
        Initialize the agent.
        
        Args:
            agent_id: Unique identifier for this agent
            data_sources: List of data sources this agent monitors
            check_interval_seconds: How often to check for anomalies
        """
        self.agent_id = agent_id
        self.data_sources = data_sources
        self.check_interval_seconds = check_interval_seconds
        
        self._running = False
        self._health = AgentHealth(agent_id=agent_id)
        self._anomaly_history: List[MarketAnomaly] = []
        self._max_history = 1000
        
        logger.info(f"Initialized agent {agent_id} monitoring {[s.value for s in data_sources]}")
    
    @property
    def agent_type(self) -> str:
        """Return the type of agent (for categorization)."""
        return self.__class__.__name__
    
    @abstractmethod
    async def detect_anomalies(self) -> List[MarketAnomaly]:
        """
        Detect anomalies from monitored data sources.
        
        This is the core method that each agent implements.
        It should:
        1. Fetch data from assigned sources
        2. Run anomaly detection algorithms
        3. Return list of detected anomalies with confidence scores
        
        Returns:
            List of MarketAnomaly objects
        """
        pass
    
    @abstractmethod
    async def fetch_data(self) -> Dict[str, Any]:
        """
        Fetch raw data from assigned sources.
        
        Returns:
            Dictionary of raw data from sources
        """
        pass
    
    async def run_once(self) -> List[MarketAnomaly]:
        """
        Execute one detection cycle.
        
        Returns:
            List of anomalies detected in this cycle
        """
        try:
            start_time = datetime.now()
            
            # Detect anomalies
            anomalies = await self.detect_anomalies()
            
            # Update health metrics
            self._health.last_run = datetime.now()
            self._health.anomalies_detected_last_hour += len(anomalies)
            
            # Calculate latency
            if anomalies:
                latencies = [a.latency_ms for a in anomalies if a.latency_ms > 0]
                if latencies:
                    self._health.avg_latency_ms = sum(latencies) / len(latencies)
            
            # Store in history
            self._anomaly_history.extend(anomalies)
            if len(self._anomaly_history) > self._max_history:
                self._anomaly_history = self._anomaly_history[-self._max_history:]
            
            logger.debug(f"Agent {self.agent_id} detected {len(anomalies)} anomalies")
            return anomalies
            
        except Exception as e:
            logger.error(f"Agent {self.agent_id} error: {e}")
            self._health.errors_last_hour += 1
            self._health.success_rate = max(0.0, self._health.success_rate - 0.01)
            return []
    
    async def run_continuously(self):
        """
        Run the agent continuously until stopped.
        
        This is the main loop for the agent.
        """
        self._running = True
        self._health.is_running = True
        
        logger.info(f"Agent {self.agent_id} starting continuous monitoring")
        
        while self._running:
            try:
                await self.run_once()
                await asyncio.sleep(self.check_interval_seconds)
            except Exception as e:
                logger.error(f"Agent {self.agent_id} continuous run error: {e}")
                await asyncio.sleep(self.check_interval_seconds)
        
        self._health.is_running = False
        logger.info(f"Agent {self.agent_id} stopped")
    
    def stop(self):
        """Stop the agent's continuous monitoring."""
        self._running = False
        logger.info(f"Agent {self.agent_id} stop requested")
    
    def get_health(self) -> AgentHealth:
        """Get current health metrics for this agent."""
        return self._health
    
    def get_recent_anomalies(self, n: int = 100) -> List[MarketAnomaly]:
        """Get the n most recent anomalies detected by this agent."""
        return self._anomaly_history[-n:]
    
    def _create_anomaly(self,
                       anomaly_type: AnomalyType,
                       data_source: DataSource,
                       confidence: float,
                       description: str,
                       primary_asset: str = "",
                       related_assets: List[str] = None,
                       raw_data: Dict[str, Any] = None,
                       detection_method: str = "",
                       statistical_significance: float = 0.0,
                       source_timestamp: datetime = None) -> MarketAnomaly:
        """
        Helper method to create a MarketAnomaly with proper defaults.
        
        Args:
            anomaly_type: Type of anomaly detected
            data_source: Source of the data
            confidence: Confidence score (0.0-1.0)
            description: Human-readable description
            primary_asset: Primary asset affected
            related_assets: Related assets
            raw_data: Raw data that triggered the anomaly
            detection_method: Method used to detect
            statistical_significance: Statistical significance (p-value/z-score)
            source_timestamp: When the data was originally sourced
            
        Returns:
            MarketAnomaly object
        """
        return MarketAnomaly(
            agent_id=self.agent_id,
            agent_type=self.agent_type,
            data_source=data_source,
            anomaly_type=anomaly_type,
            confidence=max(0.0, min(1.0, confidence)),
            severity=int(confidence * 10),
            primary_asset=primary_asset,
            related_assets=related_assets or [],
            raw_data=raw_data or {},
            description=description,
            detection_method=detection_method,
            statistical_significance=statistical_significance,
            source_timestamp=source_timestamp,
        )
