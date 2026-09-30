"""Credential consolidation: canonical provider conformance + shim deprecation."""

from __future__ import annotations

import warnings

import pytest

from trading_bot.foundation.ports import CredentialProviderPort
from trading_bot.security.canonical_provider import (
    CanonicalCredentialProvider,
    get_credential_provider,
)


def test_canonical_provider_conforms_to_port() -> None:
    provider = CanonicalCredentialProvider(overrides={"k": "v"})
    assert isinstance(provider, CredentialProviderPort)


def test_overrides_win_and_missing_returns_none() -> None:
    provider = CanonicalCredentialProvider(overrides={"ALPHA": "1"})
    assert provider.get_secret("ALPHA") == "1"
    assert provider.get_secret("DEFINITELY_MISSING_SECRET_XYZ") is None


def test_require_secret_fails_closed() -> None:
    provider = CanonicalCredentialProvider()
    with pytest.raises(KeyError):
        provider.require_secret("DEFINITELY_MISSING_SECRET_XYZ")


def test_singleton_returns_port_conforming_provider() -> None:
    assert isinstance(get_credential_provider(), CredentialProviderPort)


@pytest.mark.parametrize(
    "module_path, cls_name",
    [
        ("trading_bot.security.credential_vault", "SecureCredentialVault"),
        ("trading_bot.security.credentials", "SecureCredentialManager"),
        ("trading_bot.security.credentialvault", "CredentialVault"),
        ("trading_bot.security.secrets_manager", "SecretsManager"),
        ("trading_bot.security.vault", "SecureVault"),
    ],
)
def test_duplicate_providers_emit_deprecation(module_path: str, cls_name: str, tmp_path) -> None:
    import importlib

    cls = getattr(importlib.import_module(module_path), cls_name)
    kwargs = {}
    if cls_name == "SecureCredentialVault":
        kwargs["vault_path"] = str(tmp_path / "v.enc")
    elif cls_name == "SecretsManager":
        kwargs["secrets_dir"] = str(tmp_path / "s")
    elif cls_name == "SecureVault":
        kwargs["vault_path"] = str(tmp_path / "v.enc")
        kwargs["salt_path"] = str(tmp_path / ".salt")
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        cls(**kwargs)
    assert any(
        issubclass(w.category, DeprecationWarning) and "deprecated credential shim" in str(w.message)
        for w in caught
    ), f"{cls_name} did not emit deprecation warning"
