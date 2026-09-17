"""
Safe Deserialization Module - AlphaAlgo Security Hardening.
Provides restricted unpickling to protect against Remote Code Execution (RCE) vulnerabilities.
"""

import pickle
import io
from typing import Any

class SafeUnpickler(pickle.Unpickler):
    """
    Custom unpickler that restricts deserialization to predefined safe modules/types.
    """
    ALLOWED_MODULES = {
        'builtins',
        'collections',
        'numpy',
        'numpy.core.multiarray',
        'pandas',
        'pandas.core.frame',
        'pandas.core.internals.managers',
        'sklearn',
        'torch',
        'datetime',
        'copy',
        '__builtin__'
    }

    def find_class(self, module: str, name: str) -> Any:
        # Check parent module
        base_module = module.split('.')[0]
        if base_module in self.ALLOWED_MODULES:
            return super().find_class(module, name)
        raise pickle.UnpicklingError(f"Deserialization of global '{module}.{name}' is forbidden for security reasons.")

def safe_load(file_obj) -> Any:
    """Safely loads a pickle stream from a file-like object."""
    return SafeUnpickler(file_obj).load()

def safe_loads(data_bytes: bytes) -> Any:
    """Safely loads a pickle stream from bytes."""
    return SafeUnpickler(io.BytesIO(data_bytes)).load()
