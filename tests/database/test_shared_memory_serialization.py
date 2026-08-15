import pytest
import numpy as np
import pandas as pd
from trading_bot.core.governance.serialization import SerializerRegistry
from trading_bot.database.shared_memory_manager import SharedMemoryManager

def test_centralized_serialization_ndarray():
    # Create ndarray
    array = np.array([[1.0, 2.0], [3.0, 4.0]], dtype=np.float32)

    # Serialize
    serialized = SerializerRegistry.serialize_ndarray(array)
    assert serialized["__type__"] == "ndarray"
    assert serialized["dtype"] == "float32"
    assert serialized["shape"] == [2, 2]

    # Deserialize
    deserialized = SerializerRegistry.deserialize_ndarray(serialized)
    assert np.array_equal(array, deserialized)
    assert deserialized.dtype == np.float32

def test_centralized_serialization_dataframe():
    # Create DataFrame
    df = pd.DataFrame({
        "close": [100.5, 101.2, 102.3],
        "volume": [1000, 1500, 2000]
    }, index=[10, 20, 30])

    # Serialize
    serialized = SerializerRegistry.serialize_dataframe(df)
    assert serialized["__type__"] == "dataframe"
    assert "close" in serialized["data"]
    assert "volume" in serialized["data"]

    # Deserialize
    deserialized = SerializerRegistry.deserialize_dataframe(serialized)
    assert isinstance(deserialized, pd.DataFrame)
    assert list(deserialized.columns) == ["close", "volume"]
    assert list(deserialized.index) == [10, 20, 30]
    assert np.array_equal(deserialized["close"].values, df["close"].values)

def test_shared_memory_dataframe_caching():
    # Initialize manager
    manager = SharedMemoryManager()

    # Create DataFrame
    df = pd.DataFrame({
        "pnl": [10.5, -5.2, 2.3],
        "size": [0.1, 0.5, 0.2]
    })

    # Cache
    obj_id = manager.put(df, obj_id="test_df")
    assert obj_id == "test_df"

    # Retrieve
    retrieved = manager.get_dataframe("test_df")
    assert isinstance(retrieved, pd.DataFrame)
    assert np.array_equal(retrieved["pnl"].values, df["pnl"].values)
    assert np.array_equal(retrieved["size"].values, df["size"].values)

    # Clean up
    manager.cleanup()
