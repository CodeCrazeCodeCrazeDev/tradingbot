import base64
import json
import logging
import io
from typing import Any, Dict, Optional, Type
import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)

class NumpyEncoder(json.JSONEncoder):
    """Custom JSON encoder for NumPy types."""
    def default(self, obj):
        if isinstance(obj, np.ndarray):
            return {
                "__type__": "ndarray",
                "dtype": str(obj.dtype),
                "shape": list(obj.shape),
                "data": base64.b64encode(obj.tobytes()).decode("utf-8")
            }
        elif isinstance(obj, (np.void, np.integer, np.floating)):
            return obj.item()
        return super().default(obj)

def numpy_decoder(dct):
    """Custom JSON decoder for reconstructed NumPy arrays."""
    if "__type__" in dct and dct["__type__"] == "ndarray":
        data = base64.b64decode(dct["data"].encode("utf-8"))
        array = np.frombuffer(data, dtype=np.dtype(dct["dtype"]))
        if dct["shape"]:
            array = array.reshape(dct["shape"])
        return array
    return dct

class SerializerRegistry:
    """
    Centralized serialization registry for AlphaAlgo.
    Enforces format constraints and handles conversion for ndarrays,
    pandas DataFrames, models, and general telemetry.
    """

    @staticmethod
    def serialize_ndarray(array: np.ndarray) -> Dict[str, Any]:
        """Serialize a NumPy array to a secure, typed dictionary representation."""
        return {
            "__type__": "ndarray",
            "dtype": str(array.dtype),
            "shape": list(array.shape),
            "data": base64.b64encode(array.tobytes()).decode("utf-8")
        }

    @staticmethod
    def deserialize_ndarray(dct: Dict[str, Any]) -> np.ndarray:
        """Reconstruct a NumPy array from a serialized dictionary."""
        if not isinstance(dct, dict) or dct.get("__type__") != "ndarray":
            raise ValueError("Invalid serialization format for ndarray")
        data = base64.b64decode(dct["data"].encode("utf-8"))
        array = np.frombuffer(data, dtype=np.dtype(dct["dtype"]))
        if dct["shape"]:
            array = array.copy().reshape(dct["shape"])
        return array

    @staticmethod
    def serialize_dataframe(df: pd.DataFrame) -> Dict[str, Any]:
        """Serialize a pandas DataFrame to a structured dict containing serialized columns."""
        serialized_cols = {}
        for col in df.columns:
            serialized_cols[str(col)] = SerializerRegistry.serialize_ndarray(df[col].values)

        return {
            "__type__": "dataframe",
            "index": SerializerRegistry.serialize_ndarray(df.index.values),
            "columns": list(df.columns),
            "dtypes": [str(dt) for dt in df.dtypes],
            "data": serialized_cols
        }

    @staticmethod
    def deserialize_dataframe(dct: Dict[str, Any]) -> pd.DataFrame:
        """Reconstruct a pandas DataFrame from its structured dict representation."""
        if not isinstance(dct, dict) or dct.get("__type__") != "dataframe":
            raise ValueError("Invalid serialization format for DataFrame")

        index_array = SerializerRegistry.deserialize_ndarray(dct["index"])
        df_data = {}
        for col in dct["columns"]:
            col_str = str(col)
            if col_str in dct["data"]:
                df_data[col_str] = SerializerRegistry.deserialize_ndarray(dct["data"][col_str])

        return pd.DataFrame(df_data, index=index_array)
