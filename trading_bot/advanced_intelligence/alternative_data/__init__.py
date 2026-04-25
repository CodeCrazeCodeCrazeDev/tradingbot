"""
Alternative Data Sources Module (Ideas 31-60)
==============================================
Non-traditional data sources for generating alpha.
"""

from .satellite_imagery import SatelliteImageryAnalyzer
from .iot_sensors import IoTSensorNetwork
from .patent_analysis import PatentAnalyzer
from .supply_chain import SupplyChainMapper
from .web_scraping import IntelligentWebScraper
from .social_graph import SocialGraphAnalyzer
from .geolocation import GeolocationIntelligence
from .weather_data import WeatherImpactAnalyzer
from .shipping_data import ShippingTracker
from .credit_card import CreditCardDataAnalyzer
from .app_usage import AppUsageAnalyzer
from .job_postings import JobPostingsAnalyzer
from .government_data import GovernmentDataMiner
from .academic_research import AcademicResearchTracker
from .insider_trading import InsiderTradingMonitor
from .options_flow import OptionsFlowAnalyzer
from .dark_pool import DarkPoolAnalyzer
from .etf_flows import ETFFlowTracker
from .futures_basis import FuturesBasisAnalyzer
from .cross_asset import CrossAssetCorrelator
from .macro_indicators import MacroIndicatorEngine
from .central_bank import CentralBankWatcher
from .political_risk import PoliticalRiskAnalyzer
from .esg_data import ESGDataProvider
from .carbon_markets import CarbonMarketAnalyzer
from .real_estate import RealEstateDataProvider
from .consumer_sentiment import ConsumerSentimentTracker
from .earnings_whispers import EarningsWhisperAnalyzer
from .analyst_revisions import AnalystRevisionTracker
from .short_interest import ShortInterestMonitor

__all__ = [
    "SatelliteImageryAnalyzer",
    "IoTSensorNetwork",
    "PatentAnalyzer",
    "SupplyChainMapper",
    "IntelligentWebScraper",
    "SocialGraphAnalyzer",
    "GeolocationIntelligence",
    "WeatherImpactAnalyzer",
    "ShippingTracker",
    "CreditCardDataAnalyzer",
    "AppUsageAnalyzer",
    "JobPostingsAnalyzer",
    "GovernmentDataMiner",
    "AcademicResearchTracker",
    "InsiderTradingMonitor",
    "OptionsFlowAnalyzer",
    "DarkPoolAnalyzer",
    "ETFFlowTracker",
    "FuturesBasisAnalyzer",
    "CrossAssetCorrelator",
    "MacroIndicatorEngine",
    "CentralBankWatcher",
    "PoliticalRiskAnalyzer",
    "ESGDataProvider",
    "CarbonMarketAnalyzer",
    "RealEstateDataProvider",
    "ConsumerSentimentTracker",
    "EarningsWhisperAnalyzer",
    "AnalystRevisionTracker",
    "ShortInterestMonitor",
]
