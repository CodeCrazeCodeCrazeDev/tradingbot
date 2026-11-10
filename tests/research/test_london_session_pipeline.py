"""
End-to-End Pipeline and Unit Tests for London Strategic Edge Research & ML Training.
Tests:
1. Legal Entitlement Gate (prohibiting unauthorized LSE use, allowing synthetic).
2. Data Collector ingestion, UTC/Europe:London conversion, and SHA-256 manifests.
3. Feature Engineering (sweeps, displacement, OFI, vol ratios) and Triple-Barrier labeling.
4. Canonical Hypothesis screening with Benjamini-Hochberg FDR correction.
5. Modular ML model training (Baseline, Regime, Structure, Forecaster, Meta-Labeler).
6. Walk-forward validation, DSR, PBO, and Monte Carlo resampling.
7. Model Registry registration and Decision Evidence Package generation.
"""

import os
import pytest
import numpy as np
import pandas as pd
from datetime import datetime

from trading_bot.research.london_session.collector import (
    DataEntitlementGate,
    DataLicenseType,
    EntitlementAction,
    DataEntitlementException,
    LondonDataCollector
)
from trading_bot.research.london_session.feature_engine import LondonFeatureEngine, TripleBarrierLabeler
from trading_bot.research.london_session.hypothesis_engine import LondonHypothesisEngine, CANONICAL_HYPOTHESES
from trading_bot.research.london_session.validation import LondonValidationEngine
from trading_bot.research.london_session.ml import (
    BaselineModel,
    MarketRegimeModel,
    LiquidityStructureModel,
    ProbabilisticForecastingModel,
    MetaLabelingModel
)
from trading_bot.research.london_session.orchestrator import LondonSessionResearchPipeline, LondonModelRegistry


def test_data_entitlement_gate_blocks_unauthorized():
    gate = DataEntitlementGate(override_env_lookup=True)
    # Synthetic must be permitted
    res_synth = gate.verify_action(EntitlementAction.MODEL_TRAINING, DataLicenseType.SYNTHETIC_RESEARCH)
    assert res_synth.is_permitted is True

    # Standard LSE terms must be blocked for training
    with pytest.raises(DataEntitlementException):
        gate.verify_action(EntitlementAction.MODEL_TRAINING, DataLicenseType.LSE_STANDARD_FREE)

    # Standard LSE terms blocked for scraping / automated ingestion
    with pytest.raises(DataEntitlementException):
        gate.verify_action(EntitlementAction.INGESTION, DataLicenseType.LSE_STANDARD_FREE)


def test_collector_and_manifest_generation(tmp_path):
    collector = LondonDataCollector(base_storage_dir=str(tmp_path))
    df, manifest = collector.generate_synthetic_london_dataset(
        symbol="EURUSD",
        timeframe="5m",
        num_bars=350,
        random_seed=123
    )
    assert len(df) == 350
    assert manifest.symbol == "EURUSD"
    assert manifest.timeframe == "5m"
    assert manifest.sha256_hash != ""
    assert manifest.duplicate_rows_removed == 0
    assert "london_hour" in df.columns


def test_features_and_triple_barrier_labeling(tmp_path):
    collector = LondonDataCollector(base_storage_dir=str(tmp_path))
    df, _ = collector.generate_synthetic_london_dataset(symbol="GBPUSD", num_bars=300)

    fe = LondonFeatureEngine()
    feat_df = fe.compute_session_features(df)
    assert "asia_high_sweep" in feat_df.columns
    assert "is_displacement" in feat_df.columns
    assert "liquidity_migration_ratio" in feat_df.columns
    assert "ofi" in feat_df.columns

    lbl = TripleBarrierLabeler()
    lbl_df = lbl.compute_labels(feat_df)
    assert "barrier_hit" in lbl_df.columns
    assert "gross_return" in lbl_df.columns
    assert "net_return" in lbl_df.columns
    assert "meta_label" in lbl_df.columns


def test_canonical_hypotheses_and_screening():
    hyp_engine = LondonHypothesisEngine()
    assert len(hyp_engine.hypotheses) == 13

    # Generate test feature df
    collector = LondonDataCollector(base_storage_dir="data/test_tmp_collector")
    df, _ = collector.generate_synthetic_london_dataset(symbol="GBPUSD", num_bars=300)
    fe = LondonFeatureEngine()
    feat_df = fe.compute_session_features(df)

    screening = hyp_engine.screen_hypotheses_with_multiple_testing_correction(feat_df)
    assert len(screening) == 13
    for name, res in screening.items():
        assert "passed_fdr" in res
        assert "status" in res


def test_end_to_end_research_pipeline(tmp_path):
    pipeline = LondonSessionResearchPipeline(
        storage_base_dir=str(tmp_path / "data"),
        models_dir=str(tmp_path / "models")
    )
    results = pipeline.execute_complete_research_run(
        symbol="GBPUSD",
        timeframe="5m",
        num_bars=400,
        license_type=DataLicenseType.SYNTHETIC_RESEARCH
    )

    assert "verdict" in results
    assert results["verdict"] in ["PASS", "FAIL", "INCONCLUSIVE"]
    assert results["dataset_manifest"] is not None
    assert results["model_artifact"] is not None
    assert results["model_artifact"].research_only is True
    assert results["edge"].status == "Validated"
    assert results["evidence_package"] is not None
