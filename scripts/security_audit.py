#!/usr/bin/env python3
"""Security and Credential Audit Script"""

import sys
import os
import re
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
PROJECT_ROOT = Path(__file__).parent.parent
trading_bot_dir = PROJECT_ROOT / "trading_bot"

print("=" * 80)
print("API KEY STORAGE & CREDENTIAL MANAGEMENT AUDIT")
print("=" * 80)

# Check .env file
print("\n[1] CHECKING .ENV FILE SECURITY:")
env_file = PROJECT_ROOT / ".env"
if env_file.exists():
    with open(env_file, "r") as f:
        env_content = f.read()
    
    # Check for actual API keys (not placeholders)
    has_real_keys = False
    key_patterns = [
        (r"API_KEY\s*=\s*[a-zA-Z0-9]{20,}", "API Key"),
        (r"SECRET\s*=\s*[a-zA-Z0-9]{20,}", "Secret"),
    ]
    
    for pattern, name in key_patterns:
        if re.search(pattern, env_content):
            has_real_keys = True
            print(f"   WARNING: {name} appears to contain real value")
    
    if not has_real_keys:
        print("   OK: No obvious real API keys detected")
    
    # Check .env is in .gitignore
    gitignore = PROJECT_ROOT / ".gitignore"
    if gitignore.exists():
        with open(gitignore, "r") as f:
            gitignore_content = f.read()
        if ".env" in gitignore_content:
            print("   OK: .env is in .gitignore")
        else:
            print("   WARNING: .env is NOT in .gitignore!")
else:
    print("   .env file not found")

# Check for credential vault implementations
print("\n[2] CHECKING CREDENTIAL VAULT IMPLEMENTATIONS:")
vault_files = list(trading_bot_dir.rglob("*vault*.py"))
vault_files += list(trading_bot_dir.rglob("*credential*.py"))
vault_files += list(trading_bot_dir.rglob("*secret*.py"))
vault_files = [f for f in vault_files if "__pycache__" not in str(f)]

for f in vault_files[:10]:
    with open(f, "r", encoding="utf-8", errors="ignore") as file:
        content = file.read()
    has_encryption = "Fernet" in content or "encrypt" in content or "cryptography" in content
    status = "ENCRYPTED" if has_encryption else "PLAINTEXT"
    print(f"   {f.name}: {status}")

# Check for hardcoded credentials in code
print("\n[3] CHECKING FOR HARDCODED CREDENTIALS:")
hardcoded_creds = []
patterns = [
    (r"api_key\s*=\s*['\"][a-zA-Z0-9]{20,}['\"]", "Hardcoded API Key"),
    (r"password\s*=\s*['\"][^'\"]{8,}['\"]", "Hardcoded Password"),
    (r"secret\s*=\s*['\"][a-zA-Z0-9]{20,}['\"]", "Hardcoded Secret"),
]

for py_file in trading_bot_dir.rglob("*.py"):
    if "__pycache__" in str(py_file) or "auto_fix_backups" in str(py_file):
        continue
    try:
        with open(py_file, "r", encoding="utf-8", errors="ignore") as f:
            content = f.read()
        for pattern, desc in patterns:
            if re.search(pattern, content, re.I):
                hardcoded_creds.append((str(py_file.relative_to(PROJECT_ROOT)), desc))
    except:
        pass

if hardcoded_creds:
    print(f"   WARNING: Found {len(hardcoded_creds)} potential hardcoded credentials")
    for f, d in hardcoded_creds[:5]:
        print(f"     - {f}: {d}")
else:
    print("   OK: No hardcoded credentials detected")

# Check log files for secrets
print("\n[4] CHECKING LOG FILES FOR EXPOSED SECRETS:")
log_files = list(PROJECT_ROOT.rglob("*.log"))
log_files = [f for f in log_files if ".venv" not in str(f)][:20]

secrets_in_logs = []
secret_patterns = [
    r"api[_-]?key.{0,5}[:=].{0,5}[a-zA-Z0-9]{20,}",
    r"password.{0,5}[:=].{0,5}[^\s]{8,}",
    r"token.{0,5}[:=].{0,5}[a-zA-Z0-9]{20,}",
]

for log_file in log_files:
    try:
        with open(log_file, "r", encoding="utf-8", errors="ignore") as f:
            content = f.read()
        for pattern in secret_patterns:
            if re.search(pattern, content, re.I):
                secrets_in_logs.append(str(log_file.relative_to(PROJECT_ROOT)))
                break
    except:
        pass

if secrets_in_logs:
    print(f"   WARNING: Found potential secrets in {len(secrets_in_logs)} log files")
    for f in secrets_in_logs[:5]:
        print(f"     - {f}")
else:
    print("   OK: No secrets detected in log files")

print("\n" + "=" * 80)
print("INACTIVE FEATURES ANALYSIS")
print("=" * 80)

# Find disabled features in config
print("\n[5] DISABLED FEATURES IN CONFIG:")
config_dir = PROJECT_ROOT / "config"
disabled_features = []

if config_dir.exists():
    for config_file in config_dir.glob("*.yaml"):
        try:
            with open(config_file, "r", encoding="utf-8", errors="ignore") as f:
                content = f.read()
            # Find enabled: false patterns
            matches = re.finditer(r"(\w+):\s*\n\s*enabled:\s*false", content, re.I)
            for match in matches:
                disabled_features.append((config_file.name, match.group(1)))
        except:
            pass

if disabled_features:
    for cfg, feat in disabled_features[:10]:
        print(f"   {cfg}: {feat} (set enabled: true to activate)")
else:
    print("   No explicitly disabled features found in config")

# Find feature flags in code
print("\n[6] FEATURE FLAGS IN CODE:")
feature_flags = []
for py_file in trading_bot_dir.rglob("*.py"):
    if "__pycache__" in str(py_file):
        continue
    try:
        with open(py_file, "r", encoding="utf-8", errors="ignore") as f:
            content = f.read()
        matches = re.finditer(r"(ENABLE_\w+)\s*=\s*False", content)
        for match in matches:
            feature_flags.append((str(py_file.relative_to(PROJECT_ROOT)), match.group(1)))
    except:
        pass

if feature_flags:
    for f, flag in feature_flags[:10]:
        print(f"   {f}: {flag} = False (set to True to enable)")
else:
    print("   No disabled feature flags found")

print("\n" + "=" * 80)

if __name__ == "__main__":
    pass
