"""
Canonical Serialization Layer for AlphaAlgo
==========================================

Provides deterministic serialization for complex financial and ML objects.
Supports: NumPy, Pandas, PyTorch, Enums, Datetime, UUID, Decimal, Path, and Pydantic.
Includes checksum integrity and schema versioning.
"""

import json
import uuid
import hashlib
import numpy as np
import pandas as pd
import torch
from datetime import datetime
from decimal import Decimal
from pathlib import Path
from enum import Enum
from typing import Any, Dict, List, Optional, Union
from dataclasses import is_dataclass, asdict

class AlphaAlgoEncoder(json.JSONEncoder):
    """Unified Encoder for all AlphaAlgo core types"""
    def default(self, obj):
        # 1. Basic Types & Enums
        if isinstance(obj, Enum):
            return obj.value
        if isinstance(obj, datetime):
            return obj.isoformat()
        if isinstance(obj, uuid.UUID):
            return str(obj)
        if isinstance(obj, (Decimal, Path)):
            return str(obj)

        # 2. NumPy Support
        if isinstance(obj, np.integer):
            return int(obj)
        if isinstance(obj, np.floating):
            return float(obj)
        if isinstance(obj, np.bool_):
            return bool(obj)
        if isinstance(obj, np.ndarray):
            return obj.tolist()

        # 3. Pandas Support
        if isinstance(obj, (pd.Series, pd.Index)):
            return obj.tolist()
        if isinstance(obj, pd.DataFrame):
            return obj.to_dict(orient='records')
        if isinstance(obj, pd.Timestamp):
            return obj.isoformat()

        # 4. PyTorch Support (Metadata/Tensors)
        if isinstance(obj, torch.Tensor):
            return {
                '__type__': 'torch.Tensor',
                'shape': list(obj.shape),
                'dtype': str(obj.dtype),
                'data': obj.detach().cpu().numpy().tolist()
            }

        # 5. Dataclasses & Pydantic
        if is_dataclass(obj):
            return asdict(obj)
        if hasattr(obj, 'dict') and callable(getattr(obj, 'dict')): # Pydantic v1
            return obj.dict()
        if hasattr(obj, 'model_dump') and callable(getattr(obj, 'model_dump')): # Pydantic v2
            return obj.model_dump()

        return super().default(obj)


def serialize(obj: Any, indent: int = 2, sort_keys: bool = True) -> str:
    """Deterministic serialization with checksum"""
    content = json.dumps(obj, cls=AlphaAlgoEncoder, indent=indent, sort_keys=sort_keys)
    return content

def get_checksum(content: str) -> str:
    """Calculate SHA-256 checksum for content"""
    return hashlib.sha256(content.encode('utf-8')).hexdigest()

def wrap_with_metadata(data: Any, version: str = "1.0.0") -> Dict[str, Any]:
    """Wrap data with versioning and integrity protection"""
    content = serialize(data)
    checksum = get_checksum(content)

    return {
        'version': version,
        'timestamp': datetime.utcnow().isoformat(),
        'checksum': checksum,
        'payload': data
    }

def deserialize(json_str: str) -> Any:
    """Deserialize JSON string (basic wrapper for now)"""
    return json.loads(json_str)
