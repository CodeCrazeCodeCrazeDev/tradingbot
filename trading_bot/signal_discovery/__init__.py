"""
Signal Discovery Module - Layer 1 of the Palantir-Style Autonomous Quant Research Lab
================================================================================

An army of 80 specialized agents continuously hunt for market anomalies across:
- Financial APIs (15 agents)
- Research papers (10 agents)
- Social media (20 agents)
- Dark pool signals (5 agents)
- Developer activity (10 agents)
- Protocol launches (10 agents)
- Economic releases (10 agents)

Each agent has a strict, specialized job:
1. Monitor specific data source(s)
2. Detect statistical anomalies
3. Report with confidence score
4. DO NOT classify (Layer 2's job)
5. DO NOT trade (Layer 3's job)
"""

from typing import Dict, List, Optional, Any
import logging

logger = logging.getLogger(__name__)

# Import all agent types
from .agents.base_agent import BaseAnomalyAgent, MarketAnomaly
from .agents.financial_api_agents import FinancialAPIAgent
from .agents.research_paper_agents import ResearchPaperAgent
from .agents.social_media_agents import SocialMediaAgent
from .agents.dark_pool_agents import DarkPoolAgent
from .agents.developer_activity_agents import DeveloperActivityAgent
from .agents.protocol_launch_agents import ProtocolLaunchAgent
from .agents.economic_release_agents import EconomicReleaseAgent

from .orchestrator import SignalDiscoveryOrchestrator
from .anomaly_detection.statistical_outliers import StatisticalOutlierDetector
from .anomaly_detection.regime_change import RegimeChangeDetector
from .anomaly_detection.cross_asset_divergence import CrossAssetDivergenceDetector

__all__ = [
    # Agents
    'BaseAnomalyAgent',
    'MarketAnomaly',
    'FinancialAPIAgent',
    'ResearchPaperAgent',
    'SocialMediaAgent',
    'DarkPoolAgent',
    'DeveloperActivityAgent',
    'ProtocolLaunchAgent',
    'EconomicReleaseAgent',
    # Core
    'SignalDiscoveryOrchestrator',
    # Anomaly Detection
    'StatisticalOutlierDetector',
    'RegimeChangeDetector',
    'CrossAssetDivergenceDetector',
]

def quick_start() -> SignalDiscoveryOrchestrator:
    """
    Quick start the Signal Discovery Engine with all 80 agents.
    
    Returns:
        SignalDiscoveryOrchestrator instance
    """
    return SignalDiscoveryOrchestrator()
