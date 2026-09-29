"""
Signal Discovery Agents
=======================

80 specialized agents for anomaly detection across diverse data sources.
"""

from .base_agent import BaseAnomalyAgent, MarketAnomaly, AnomalyType, DataSource, AgentHealth
from .financial_api_agents import FinancialAPIAgent
from .research_paper_agents import ResearchPaperAgent
from .social_media_agents import SocialMediaAgent
from .dark_pool_agents import DarkPoolAgent
from .developer_activity_agents import DeveloperActivityAgent
from .protocol_launch_agents import ProtocolLaunchAgent
from .economic_release_agents import EconomicReleaseAgent

__all__ = [
    'BaseAnomalyAgent',
    'MarketAnomaly', 
    'AnomalyType',
    'DataSource',
    'AgentHealth',
    'FinancialAPIAgent',
    'ResearchPaperAgent',
    'SocialMediaAgent',
    'DarkPoolAgent',
    'DeveloperActivityAgent',
    'ProtocolLaunchAgent',
    'EconomicReleaseAgent',
]
