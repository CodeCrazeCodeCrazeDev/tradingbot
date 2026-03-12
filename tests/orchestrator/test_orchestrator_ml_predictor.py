"""
Comprehensive Test Suite for ML Predictor Components
"""

import pytest
import asyncio
import numpy as np
from datetime import datetime


@pytest.fixture
def sample_config():
    return {
        'lookback_window': 100,
        'min_samples': 1000,
        'retrain_frequency': 1000
    }


@pytest.fixture
def sample_opportunities():
    return [
        {'type': 'MOMENTUM', 'symbol': 'AAPL', 'confidence': 0.75, 'expected_return': 0.03, 'risk': 0.4},
        {'type': 'ARBITRAGE', 'symbol': 'GOOGL', 'confidence': 0.85, 'expected_return': 0.01, 'risk': 0.2},
        {'type': 'NEWS', 'symbol': 'MSFT', 'confidence': 0.65, 'expected_return': 0.02, 'risk': 0.5}
    ]


class TestMLPredictorImport:
    def test_import_opportunity_predictor(self):
        from trading_bot.orchestrator.ml_predictor import OpportunityPredictor
        assert OpportunityPredictor is not None

    def test_import_success_predictor(self):
        from trading_bot.orchestrator.ml_predictor import SuccessPredictor
        assert SuccessPredictor is not None

    def test_import_feature_extractor(self):
        from trading_bot.orchestrator.ml_predictor import MLFeatureExtractor
        assert MLFeatureExtractor is not None

    def test_import_model_ensemble(self):
        from trading_bot.orchestrator.ml_predictor import ModelEnsemble
        assert ModelEnsemble is not None


class TestOpportunityPredictorInit:
    def test_initialization(self, sample_config):
        predictor = OpportunityPredictor(sample_config)
        assert predictor.lookback_window == 100
        assert predictor.min_samples == 1000
        assert 'success_classifier' in predictor.models
        assert 'return_predictor' in predictor.models
        assert 'risk_predictor' in predictor.models

    def test_default_initialization(self):
        predictor = OpportunityPredictor()
        assert predictor.lookback_window == 100
        assert predictor.min_samples == 1000


class TestMLFeatureExtractor:
    def test_initialization(self):
        extractor = MLFeatureExtractor()
        assert len(extractor.feature_names) == 20

    def test_extract_features(self, sample_opportunities):
        extractor = MLFeatureExtractor()
        features = extractor.extract_features(sample_opportunities[0])
        assert isinstance(features, np.ndarray)
        assert len(features) == 20

    def test_extract_features_all_opportunities(self, sample_opportunities):
        extractor = MLFeatureExtractor()
        for opp in sample_opportunities:
            features = extractor.extract_features(opp)
            assert len(features) == 20

    def test_encode_opportunity_type_arbitrage(self):
        extractor = MLFeatureExtractor()
        assert extractor._encode_opportunity_type('ARBITRAGE') == 0.1

    def test_encode_opportunity_type_momentum(self):
        extractor = MLFeatureExtractor()
        assert extractor._encode_opportunity_type('MOMENTUM') == 0.2

    def test_encode_opportunity_type_news(self):
        extractor = MLFeatureExtractor()
        assert extractor._encode_opportunity_type('NEWS') == 0.3

    def test_encode_opportunity_type_unknown(self):
        extractor = MLFeatureExtractor()
        assert extractor._encode_opportunity_type('UNKNOWN') == 0.5

    def test_encode_sector_tech(self):
        extractor = MLFeatureExtractor()
        assert extractor._encode_sector('TECH') == 0.1

    def test_encode_sector_finance(self):
        extractor = MLFeatureExtractor()
        assert extractor._encode_sector('FINANCE') == 0.2

    def test_encode_sector_crypto(self):
        extractor = MLFeatureExtractor()
        assert extractor._encode_sector('CRYPTO') == 0.7

    def test_encode_sector_unknown(self):
        extractor = MLFeatureExtractor()
        assert extractor._encode_sector('UNKNOWN') == 0.5

    def test_get_feature_names(self):
        extractor = MLFeatureExtractor()
        names = extractor.get_feature_names()
        assert len(names) == 20
        assert 'confidence' in names
        assert 'volatility' in names


class TestHeuristicPredictions:
    def test_heuristic_success_probability_arbitrage(self, sample_config):
        predictor = OpportunityPredictor(sample_config)
        prob = predictor._heuristic_success_probability({'type': 'ARBITRAGE', 'confidence': 0.8})
        assert 0 <= prob <= 0.95

    def test_heuristic_success_probability_momentum(self, sample_config):
        predictor = OpportunityPredictor(sample_config)
        prob = predictor._heuristic_success_probability({'type': 'MOMENTUM', 'confidence': 0.8})
        assert 0 <= prob <= 0.95

    def test_arbitrage_higher_than_momentum(self, sample_config):
        predictor = OpportunityPredictor(sample_config)
        arb_prob = predictor._heuristic_success_probability({'type': 'ARBITRAGE', 'confidence': 0.8})
        mom_prob = predictor._heuristic_success_probability({'type': 'MOMENTUM', 'confidence': 0.8})
        assert arb_prob > mom_prob

    def test_heuristic_expected_return_explicit(self, sample_config):
        predictor = OpportunityPredictor(sample_config)
        ret = predictor._heuristic_expected_return({'expected_return': 0.05})
        assert ret == 0.05

    def test_heuristic_expected_return_by_type(self, sample_config):
        predictor = OpportunityPredictor(sample_config)
        arb_ret = predictor._heuristic_expected_return({'type': 'ARBITRAGE'})
        mom_ret = predictor._heuristic_expected_return({'type': 'MOMENTUM'})
        assert arb_ret < mom_ret

    def test_heuristic_risk_score_explicit(self, sample_config):
        predictor = OpportunityPredictor(sample_config)
        risk = predictor._heuristic_risk_score({'risk': 0.3})
        assert risk == 0.3

    def test_heuristic_risk_score_by_type(self, sample_config):
        predictor = OpportunityPredictor(sample_config)
        arb_risk = predictor._heuristic_risk_score({'type': 'ARBITRAGE'})
        mom_risk = predictor._heuristic_risk_score({'type': 'MOMENTUM'})
        assert arb_risk < mom_risk


class TestConfidenceInterval:
    def test_calculate_confidence_interval(self, sample_config):
        predictor = OpportunityPredictor(sample_config)
        lower, upper = predictor._calculate_confidence_interval(0.05, 0.3)
        assert lower < 0.05
        assert upper > 0.05
        assert lower < upper

    def test_confidence_interval_zero_risk(self, sample_config):
        predictor = OpportunityPredictor(sample_config)
        lower, upper = predictor._calculate_confidence_interval(0.05, 0)
        assert lower == 0.05
        assert upper == 0.05


class TestModelConfidence:
    def test_calculate_model_confidence_untrained(self, sample_config):
        predictor = OpportunityPredictor(sample_config)
        confidence = predictor._calculate_model_confidence()
        assert confidence == 0.3  # Low confidence for heuristic

    def test_models_trained_check(self, sample_config):
        predictor = OpportunityPredictor(sample_config)
        assert predictor._models_trained() == False


@pytest.mark.asyncio
class TestAsyncPredictions:
    async def test_predict_batch(self, sample_config, sample_opportunities):
        predictor = OpportunityPredictor(sample_config)
        predictions = await predictor.predict_batch(sample_opportunities)
        assert len(predictions) == len(sample_opportunities)
        for pred in predictions:
            assert hasattr(pred, 'success_probability')
            assert hasattr(pred, 'expected_return')
            assert hasattr(pred, 'risk_score')
            assert 0 <= pred.success_probability <= 1

    async def test_predict_single(self, sample_config, sample_opportunities):
        from trading_bot.orchestrator.ml_predictor import OpportunityPredictor, MLFeatureExtractor
        predictor = OpportunityPredictor(sample_config)
        extractor = MLFeatureExtractor()
        features = extractor.extract_features(sample_opportunities[0])
        prediction = await predictor._predict_single('OPP_001', features, sample_opportunities[0])
        assert prediction.opportunity_id == 'OPP_001'
        assert 0 <= prediction.success_probability <= 1

    async def test_prediction_caching(self, sample_config, sample_opportunities):
        predictor = OpportunityPredictor(sample_config)
        # Add unique IDs
        for i, opp in enumerate(sample_opportunities):
            opp['unique_id'] = f'OPP_{i}'
        # First prediction
        predictions1 = await predictor.predict_batch(sample_opportunities)
        # Second prediction should use cache
        predictions2 = await predictor.predict_batch(sample_opportunities)
        assert len(predictions1) == len(predictions2)


class TestModelEnsemble:
    def test_initialization(self):
        ensemble = ModelEnsemble()
        assert len(ensemble.models) == 3
        assert len(ensemble.weights) == 3

    def test_weights_sum_to_one(self):
        ensemble = ModelEnsemble()
        assert sum(ensemble.weights) == pytest.approx(1.0)

    def test_predict_proba(self):
        ensemble = ModelEnsemble()
        prob = ensemble.predict_proba({'type': 'MOMENTUM'})
        assert 0 <= prob <= 1


class TestSuccessPredictor:
    def test_initialization(self):
        predictor = SuccessPredictor()
        assert predictor.ensemble is not None
        assert predictor.calibrator is not None

    def test_predict_success(self):
        predictor = SuccessPredictor()
        prob = predictor.predict_success({'type': 'MOMENTUM', 'confidence': 0.7})
        assert 0 <= prob <= 1


class TestProbabilityCalibrator:
    def test_initialization(self):
        from trading_bot.orchestrator.ml_predictor import ProbabilityCalibrator
        calibrator = ProbabilityCalibrator()
        assert calibrator.calibration_data is not None

    def test_calibrate_no_curve(self):
        calibrator = ProbabilityCalibrator()
        calibrated = calibrator.calibrate(0.7, {'type': 'ARBITRAGE'})
        assert 0 <= calibrated <= 1

    def test_get_type_adjustment(self):
    pass
import numpy
        calibrator = ProbabilityCalibrator()
        arb_adj = calibrator._get_type_adjustment('ARBITRAGE')
        mom_adj = calibrator._get_type_adjustment('MOMENTUM')
        assert arb_adj == 1.2
        assert mom_adj == 0.9


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
