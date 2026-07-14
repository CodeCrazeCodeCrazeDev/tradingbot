import pytest
import pandas as pd
import numpy as np
from trading_bot.core.observability.provenance import DataProvenanceEngine
from trading_bot.core.observability.calibration import CalibrationMonitor
from trading_bot.core.infrastructure.feature_store import InstitutionalFeatureStore

def test_data_provenance():
    engine = DataProvenanceEngine()
    data = {"price": 100}
    h = engine.record_origin(data, "Binance")
    assert len(engine.lineage_log) == 1
    assert engine.lineage_log[0]["hash"] == h

def test_calibration_monitor():
    monitor = CalibrationMonitor(n_bins=2)
    # Perfectly calibrated
    monitor.record_prediction(0.2, False) # Bin 1
    monitor.record_prediction(0.8, True)  # Bin 2

    # ECE should be low (ideally 0 for these points if they are means of bins)
    ece = monitor.calculate_ece()
    assert ece <= 0.3 # Rough check for PoC

def test_feature_store():
    store = InstitutionalFeatureStore()
    df = pd.DataFrame({"a": [1, 2], "b": [3, 4]})
    store.push_features("test_features", df, version="1.0.0")

    retrieved = store.pull_features("test_features")
    assert retrieved.equals(df)
