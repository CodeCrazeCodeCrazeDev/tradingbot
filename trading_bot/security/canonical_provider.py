"""Canonical credential provider behind ``CredentialProviderPort``.

The single sanctioned secret-resolution boundary. Other legacy credential
modules (``credential_vault``, ``credentials``, ``credentialvault``,
``secrets_manager``, ``vault``) are deprecated shims; new and converged code
must resolve secrets through this provider so access is audit-logged and
fail-closed.
"""

from __future__ import annotations

import logging
from typing import Mapping, Optional

from ..foundation.ports import CredentialProviderPort
from .secure_credentials import SecureCredentialsManager

logger = logging.getLogger(__name__)


class CanonicalCredentialProvider:
    """``CredentialProviderPort`` implementation over ``SecureCredentialsManager``.

    ``overrides`` allows tests/tools to inject values without touching the
    environment; overrides win, then the underlying manager resolves.
    Missing secrets return ``None`` (or raise from ``require_secret``) —
    never fabricated.
    """

    def __init__(
        self,
        manager: Optional[SecureCredentialsManager] = None,
        overrides: Optional[Mapping[str, str]] = None,
    ) -> None:
        self._manager = manager or SecureCredentialsManager()
        self._overrides = dict(overrides or {})

    def get_secret(self, name: str) -> Optional[str]:
        if name in self._overrides:
            return self._overrides[name]
        return self._manager.get_credential(name)

    def require_secret(self, name: str) -> str:
        value = self.get_secret(name)
        if not value:
            raise KeyError(f"required secret '{name}' is unavailable")
        return value


def _build_default() -> CredentialProviderPort:
    return CanonicalCredentialProvider()


_default_provider: Optional[CredentialProviderPort] = None


def get_credential_provider() -> CredentialProviderPort:
    """Process-wide canonical credential provider (lazy singleton)."""
    global _default_provider
    if _default_provider is None:
        _default_provider = _build_default()
    return _default_provider
