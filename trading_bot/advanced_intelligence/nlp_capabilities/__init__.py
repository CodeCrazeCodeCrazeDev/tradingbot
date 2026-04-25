"""
Natural Language Processing Module (Ideas 151-180)
=====================================================
NLP capabilities for financial text analysis.
"""

from .news_sentiment import NewsSentimentAnalyzer
from .earnings_call import EarningsCallAnalyzer
from .central_bank_nlp import CentralBankNLP
from .research_summarizer import ResearchSummarizer
from .social_trends import SocialTrendDetector
from .reddit_monitor import RedditMonitor
from .patent_analyzer import PatentAnalyzer
from .legal_document import LegalDocumentAnalyzer
from .mdna_analyzer import MDNAAnalyzer
from .competitor_mentions import CompetitorMentionTracker
from .product_reviews import ProductReviewAnalyzer
from .employee_reviews import EmployeeReviewAnalyzer
from .supply_chain_nlp import SupplyChainNLP
from .ma_rumor import MARumorDetector
from .executive_quotes import ExecutiveQuoteExtractor
from .guidance_analyzer import GuidanceAnalyzer
from .risk_factor_tracker import RiskFactorTracker
from .insider_filing_nlp import InsiderFilingNLP
from .proxy_analyzer import ProxyAnalyzer
from .credit_agreement import CreditAgreementAnalyzer
from .ipo_prospectus import IPOProspectusAnalyzer
from .spac_analyzer import SPACAnalyzer
from .bankruptcy_nlp import BankruptcyNLP
from .regulatory_comments import RegulatoryCommentAnalyzer
from .congressional_testimony import CongressionalTestimonyAnalyzer
from .news_translator import NewsTranslator
from .podcast_analyzer import PodcastAnalyzer
from .video_analyzer import VideoAnalyzer
from .chat_monitor import ChatMonitor
from .newsletter_analyzer import NewsletterAnalyzer

__all__ = [
    "NewsSentimentAnalyzer",
    "EarningsCallAnalyzer",
    "CentralBankNLP",
    "ResearchSummarizer",
    "SocialTrendDetector",
    "RedditMonitor",
    "PatentAnalyzer",
    "LegalDocumentAnalyzer",
    "MDNAAnalyzer",
    "CompetitorMentionTracker",
    "ProductReviewAnalyzer",
    "EmployeeReviewAnalyzer",
    "SupplyChainNLP",
    "MARumorDetector",
    "ExecutiveQuoteExtractor",
    "GuidanceAnalyzer",
    "RiskFactorTracker",
    "InsiderFilingNLP",
    "ProxyAnalyzer",
    "CreditAgreementAnalyzer",
    "IPOProspectusAnalyzer",
    "SPACAnalyzer",
    "BankruptcyNLP",
    "RegulatoryCommentAnalyzer",
    "CongressionalTestimonyAnalyzer",
    "NewsTranslator",
    "PodcastAnalyzer",
    "VideoAnalyzer",
    "ChatMonitor",
    "NewsletterAnalyzer",
]
