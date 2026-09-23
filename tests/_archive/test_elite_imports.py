import logging
#!/usr/bin/env python
"""
Test script to verify that elite system modules can be imported directly from the root package.
"""
import sys
import os
from loguru import logger

# Add parent directory to path to allow importing modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../')))

def test_elite_imports():
    """Test importing elite system modules from root package."""
    logger.info("Testing elite system imports from root package")
    
    try:
        # Import elite system modules directly from the root package
        from trading_bot import (

logger = logging.getLogger(__name__)

            # Market Psychology
            EliteMarketPsychology, SentimentSource, MarketSentiment,
            # Regime Detection
            EliteRegimeDetector, MarketRegime,
            # Risk Management
            EliteRiskManager, RiskLevel,
            # Pattern Recognition
            ElitePatternRecognizer, PatternType,
            # Market Analysis
            EliteMarketAnalyzer, TimeFrame
        )
        
        logger.info("Successfully imported all elite system modules and enums")
        
        # Verify class instantiation
        psychology = EliteMarketPsychology()
        logger.info(f"Created EliteMarketPsychology instance: {psychology}")
        
        detector = EliteRegimeDetector()
        logger.info(f"Created EliteRegimeDetector instance: {detector}")
        
        risk_manager = EliteRiskManager({"balance": 100000})
        logger.info(f"Created EliteRiskManager instance: {risk_manager}")
        
        recognizer = ElitePatternRecognizer()
        logger.info(f"Created ElitePatternRecognizer instance: {recognizer}")
        
        analyzer = EliteMarketAnalyzer()
        logger.info(f"Created EliteMarketAnalyzer instance: {analyzer}")
        
        # Verify enums
        logger.info(f"SentimentSource values: {[source.name for source in SentimentSource]}")
        logger.info(f"MarketSentiment values: {[sentiment.name for sentiment in MarketSentiment]}")
        logger.info(f"MarketRegime values: {[regime.name for regime in MarketRegime]}")
        logger.info(f"RiskLevel values: {[level.name for level in RiskLevel]}")
        logger.info(f"PatternType values: {[pattern.name for pattern in PatternType]}")
        logger.info(f"TimeFrame values: {[tf.name for tf in TimeFrame]}")
        
        return True
    except ImportError as e:
        logger.error(f"Import error: {e}")
        return False
if __name__ == "__main__":
    # Configure logger
    logger.remove()
    logger.add(sys.stderr, format="{time} | {level} | {message}", level="INFO")
    
    # Run test
    success = test_elite_imports()
    
    if success:
        logger.info("All elite system imports and instantiations successful")
        sys.exit(0)
    else:
        logger.error("Failed to import or instantiate elite system modules")
        sys.exit(1)
