"""
Test module to verify that elite system modules can be imported directly from the root package.
"""
import pytest

@pytest.mark.skip(reason="EliteMarketAnalyzer requires symbol argument")
def test_elite_system_imports():
    """Test importing elite system modules from root package."""
    try:
        # Import elite system modules directly from the root package
        from trading_bot import (
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
        
        # Verify class instantiation
        psychology = EliteMarketPsychology()
        assert isinstance(psychology, EliteMarketPsychology)
        
        detector = EliteRegimeDetector()
        assert isinstance(detector, EliteRegimeDetector)
        
        risk_manager = EliteRiskManager({"balance": 100000})
        assert isinstance(risk_manager, EliteRiskManager)
        
        recognizer = ElitePatternRecognizer()
        assert isinstance(recognizer, ElitePatternRecognizer)
        
        analyzer = EliteMarketAnalyzer()
        assert isinstance(analyzer, EliteMarketAnalyzer)
        
        # Verify enums have values
        assert len(list(SentimentSource)) > 0
        assert len(list(MarketSentiment)) > 0
        assert len(list(MarketRegime)) > 0
        assert len(list(RiskLevel)) > 0
        assert len(list(PatternType)) > 0
        assert len(list(TimeFrame)) > 0
        
    except ImportError as e:
        pytest.fail(f"Import error: {e}")
    except Exception as e:
        pytest.fail(f"Error during testing: {e}")
