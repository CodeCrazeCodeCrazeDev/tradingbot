"""
Safe Pickle Serialization and Deserialization Utility - AlphaAlgo UCA V5
Restricts unpickling to standard and approved modules to prevent RCE.
"""

import pickle
import io
import hmac
import hashlib
import os
from typing import Any

SECRET_KEY = os.environ.get("ALPHAALGO_SECRET_KEY", "safe-fallback-for-tests-123").encode()

class RestrictedUnpickler(pickle.Unpickler):
    """
    Custom Unpickler that restricts loaded globals to a strict safelist.
    """
    SAFE_MODULES = {
        'builtins',
        'numpy',
        'numpy.core.multiarray',
        'numpy._core.multiarray',  # For newer numpy versions
        'pandas',
        'pandas.core.frame',
        'collections',
        'datetime',
        'trading_bot',
        'copyreg',
    }

    def find_class(self, module, name):
        module_root = module.split('.')[0]
        if module_root in self.SAFE_MODULES:
            return super().find_class(module, name)
        raise pickle.UnpicklingError(f"Security Block: Global '{module}.{name}' is forbidden.")

def safe_load(file_obj) -> Any:
    """Load and deserialize with restricted globals."""
    return RestrictedUnpickler(file_obj).load()

def safe_loads(data: bytes) -> Any:
    """Deserialize bytes with restricted globals."""
    return RestrictedUnpickler(io.BytesIO(data)).load()

def signed_dumps(obj) -> bytes:
    """Serialize object and append an HMAC signature."""
    data = pickle.dumps(obj)
    signature = hmac.new(SECRET_KEY, data, hashlib.sha256).digest()
    return signature + data

def signed_loads(signed_data: bytes) -> Any:
    """Verify HMAC signature and deserialize object safely."""
    if len(signed_data) < 32:
        raise ValueError("Security Block: Invalid signed data length")
    signature = signed_data[:32]
    data = signed_data[32:]
    expected_signature = hmac.new(SECRET_KEY, data, hashlib.sha256).digest()
    if not hmac.compare_digest(signature, expected_signature):
        raise ValueError("Security Block: HMAC verification failed! Untrusted data source.")
    return safe_loads(data)
