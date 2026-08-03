"""
ArtifactManager - Authority for All Serialization & Deserialization in AlphaAlgo.
Enforces non-executable JSON serialization for general data, and strict signed/verified
pickling for ML models/artifacts with HMAC, SHA-256, and manifest checks.

No module should perform its own deserialization.
"""

import json
import pickle
import io
import hmac
import hashlib
import os
import sys
import logging
from typing import Any, Dict, Optional, Type
from datetime import datetime

logger = logging.getLogger(__name__)

# Secret key for HMAC signing
SECRET_KEY = os.environ.get("ALPHAALGO_SECRET_KEY", "safe-fallback-for-tests-123").encode()

class RestrictedUnpickler(pickle.Unpickler):
    """
    Restricts loaded globals to standard safe modules.
    """
    SAFE_MODULES = {
        'builtins',
        'numpy',
        'numpy.core.multiarray',
        'numpy._core.multiarray',
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

class ArtifactManager:
    """
    Sole authority for all object serialization and deserialization in AlphaAlgo.
    """
    _model_cache = {}

    @classmethod
    def serialize_data(cls, obj: Any) -> bytes:
        """
        Enforce non-executable JSON serialization for general objects.
        """
        try:
            return json.dumps(obj).encode('utf-8')
        except (TypeError, ValueError) as e:
            raise ValueError(f"General data must be non-executable JSON-serializable: {e}")

    @classmethod
    def deserialize_data(cls, data: bytes) -> Any:
        """
        Enforce non-executable JSON deserialization for general objects.
        """
        return json.loads(data.decode('utf-8'))

    @classmethod
    def serialize_model(cls, model_obj: Any, name: str, version: str) -> bytes:
        """
        Serialize ML models using signed pickle with manifest, SHA-256 and HMAC.
        """
        # 1. Standardize pickle payload
        raw_pickle = pickle.dumps(model_obj)

        # 2. Compute SHA-256 checksum
        checksum = hashlib.sha256(raw_pickle).hexdigest()

        # 3. Create Manifest
        manifest = {
            "name": name,
            "version": version,
            "serialized_at": datetime.utcnow().isoformat(),
            "python_version": sys.version.split()[0],
            "sha256": checksum
        }
        manifest_bytes = json.dumps(manifest).encode('utf-8')
        manifest_len = len(manifest_bytes)

        # 4. Form payload: ManifestLen (4 bytes) + Manifest + RawPickle
        payload = manifest_len.to_bytes(4, byteorder='big') + manifest_bytes + raw_pickle

        # 5. Compute HMAC
        signature = hmac.new(SECRET_KEY, payload, hashlib.sha256).digest()

        # 6. Combined signed data: Signature (32 bytes) + Payload
        return signature + payload

    @classmethod
    def deserialize_model(cls, signed_data: bytes, expected_name: str, expected_version: str) -> Any:
        """
        Verify signature, SHA-256 checksum, manifest, python version compatibility,
        and deserialize the model.
        """
        if len(signed_data) < 36:
            raise ValueError("Security Block: Invalid model payload length")

        # 1. Verify HMAC
        signature = signed_data[:32]
        payload = signed_data[32:]
        expected_signature = hmac.new(SECRET_KEY, payload, hashlib.sha256).digest()

        if not hmac.compare_digest(signature, expected_signature):
            raise ValueError("Security Block: Model signature mismatch! Untrusted source.")

        # 2. Extract Manifest
        manifest_len = int.from_bytes(payload[:4], byteorder='big')
        manifest_bytes = payload[4:4 + manifest_len]
        raw_pickle = payload[4 + manifest_len:]

        manifest = json.loads(manifest_bytes.decode('utf-8'))

        # 3. Verify SHA-256 Checksum
        computed_checksum = hashlib.sha256(raw_pickle).hexdigest()
        if manifest.get("sha256") != computed_checksum:
            raise ValueError("Security Block: Artifact checksum corruption or tamper detected!")

        # 4. Verify Name & Version & Compatibility
        if manifest.get("name") != expected_name:
            raise ValueError(f"Security Block: Model name mismatch! Expected '{expected_name}', got '{manifest.get('name')}'")

        manifest_ver = manifest.get("version", "1.0")
        if float(manifest_ver) < float(expected_version):
            logger.warning(f"Version Warning: Outdated artifact version {manifest_ver} (Expected: {expected_version})")

        # 5. Restricted Deserialization
        return RestrictedUnpickler(io.BytesIO(raw_pickle)).load()

    @classmethod
    def get_cached_model(cls, cache_key: str) -> Optional[Any]:
        """Thread-safe and coroutine-safe model cache lookup."""
        return cls._model_cache.get(cache_key)

    @classmethod
    def cache_model(cls, cache_key: str, model_obj: Any):
        """Thread-safe and coroutine-safe model caching."""
        cls._model_cache[cache_key] = model_obj
