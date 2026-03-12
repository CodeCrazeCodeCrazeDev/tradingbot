"""
security package
"""

try:
    from .advanced_security import (
        APIKey,
        APIKeyManager,
        AdvancedSecuritySystem,
        AuditAction,
        AuditEntry,
        AuditLogger,
        DDoSProtection,
        EncryptionManager,
        IPWhitelist,
        RateLimiter,
        SecurityAlert,
        SecurityLevel,
        SecurityScanner,
        TwoFactorAuth,
        get_security_system
    )
    from .audit_logging import (
        AuditEvent,
        AuditEventType,
        AuditLogger,
        Permission,
        Role,
        SecurityMonitor,
        Session,
        User,
        UserManager,
        require_permission
    )
    from .complete_security_system import (
        CompleteSecuritySystem,
        JWTAuthentication,
        RateLimiter,
        SQLSafetyChecker
    )
    from .credential_vault import (
        EnvironmentCredentialLoader,
        SecureCredentialVault,
        get_mt5_credentials,
        store_mt5_credentials
    )
    from .credentials import SecureCredentialManager, get_credential_manager
    from .credentialvault import CredentialVault, CredentialVaultConfig, create_credentialvault
    from .enhanced_security import EnhancedSecurity
    from .jwt_auth import JwtAuth, create_jwt_auth
    from .jwtauthenticator import JWTAuthenticator, JWTAuthenticatorConfig, create_jwtauthenticator
    from .safe_eval import SafeEvaluator, replace_eval_in_code, safe_eval
    from .secure_credentials import (
        CredentialConfig,
        SecureCredentialsManager,
        get_api_key,
        get_credentials_manager,
        load_api_keys_secure,
        migrate_from_json_file
    )
    from .security_system import (
        AlertType,
        ComplianceSystem,
        FailsafeSystem,
        FraudDetector,
        LogEncryptor,
        SecurityAlert,
        SecurityLevel,
        SecuritySystem
    )
    from .vault import Vault, create_vault
except ImportError as e:
    import logging
    logging.getLogger(__name__).debug(f'Optional import failed in security: {e}')

__all__ = [
    'APIKey',
    'APIKeyManager',
    'AdvancedSecuritySystem',
    'AlertType',
    'AuditAction',
    'AuditEntry',
    'AuditEvent',
    'AuditEventType',
    'AuditLogger',
    'CompleteSecuritySystem',
    'ComplianceSystem',
    'CredentialConfig',
    'CredentialVault',
    'CredentialVaultConfig',
    'DDoSProtection',
    'EncryptionManager',
    'EnhancedSecurity',
    'EnvironmentCredentialLoader',
    'FailsafeSystem',
    'FraudDetector',
    'IPWhitelist',
    'JWTAuthentication',
    'JWTAuthenticator',
    'JWTAuthenticatorConfig',
    'JwtAuth',
    'LogEncryptor',
    'Permission',
    'RateLimiter',
    'Role',
    'SQLSafetyChecker',
    'SafeEvaluator',
    'SecureCredentialManager',
    'SecureCredentialVault',
    'SecureCredentialsManager',
    'SecurityAlert',
    'SecurityLevel',
    'SecurityMonitor',
    'SecurityScanner',
    'SecuritySystem',
    'Session',
    'TwoFactorAuth',
    'User',
    'UserManager',
    'Vault',
    'create_credentialvault',
    'create_jwt_auth',
    'create_jwtauthenticator',
    'create_vault',
    'get_api_key',
    'get_credential_manager',
    'get_credentials_manager',
    'get_mt5_credentials',
    'get_security_system',
    'load_api_keys_secure',
    'migrate_from_json_file',
    'replace_eval_in_code',
    'require_permission',
    'safe_eval',
    'store_mt5_credentials',
]