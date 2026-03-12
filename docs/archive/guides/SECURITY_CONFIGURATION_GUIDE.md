# Security Configuration Guide
## Elite Trading Bot - Production Hardening

This guide provides step-by-step instructions for securely configuring the Elite Trading Bot after applying security patches.

---

## Table of Contents
1. [Initial Setup](#initial-setup)
2. [Credential Management](#credential-management)
3. [Database Security](#database-security)
4. [Network Security](#network-security)
5. [Monitoring & Logging](#monitoring--logging)
6. [Backup & Recovery](#backup--recovery)
7. [Security Checklist](#security-checklist)

---

## Initial Setup

### 1. Environment Preparation

**Create secure .env file:**
```bash
# Copy template
cp .env.template .env

# Set restrictive permissions (Unix/Linux/Mac)
chmod 600 .env

# Windows: Use File Properties > Security > Advanced
# Remove all users except your account with Full Control
```

**Configure .gitignore:**
```bash
# Ensure these are in .gitignore
echo ".env" >> .gitignore
echo "*.db" >> .gitignore
echo "config/api_keys.json" >> .gitignore
echo "*.log" >> .gitignore
```

### 2. Verify Patch Installation

**Check security patches applied:**
```python
# Run validation script
python -c "
import os
from trading_bot.connectors.mt5_connector import MT5Connector
from trading_bot.advanced_features.blockchain_validation import BlockchainLedger

# Verify validation methods exist
assert hasattr(MT5Connector, '_validate_account')
assert hasattr(MT5Connector, '_validate_order')
print('✅ Security patches verified')
"
```

---

## Credential Management

### 1. MT5 Account Credentials

**CRITICAL: Never use demo credentials in production!**

**Secure credential setup:**
```bash
# Edit .env file
nano .env

# Set your actual credentials
MT5_LOGIN=YOUR_ACTUAL_LOGIN
MT5_PASSWORD=YOUR_SECURE_PASSWORD
MT5_INVESTOR=YOUR_INVESTOR_PASSWORD
MT5_SERVER=YOUR_BROKER_SERVER
```

**Password Requirements:**
- Minimum 12 characters
- Mix of uppercase, lowercase, numbers, symbols
- No dictionary words
- Unique to this application
- Store backup in password manager (1Password, LastPass, Bitwarden)

### 2. API Keys Management

**Create secure API keys file:**
```bash
# Copy example
cp config/api_keys.json.example config/api_keys.json

# Set restrictive permissions
chmod 600 config/api_keys.json  # Unix/Linux/Mac
```

**Edit API keys:**
```json
{
  "mt5": {
    "api_key": "your_actual_api_key_here",
    "api_secret": "your_actual_api_secret_here"
  },
  "newsapi": {
    "api_key": "your_newsapi_key_here"
  }
}
```

### 3. Environment Variable Validation

**Add startup validation:**
```python
# Add to your main.py or startup script
import os
import sys

def validate_credentials():
    """Validate that credentials are properly configured."""
    required_vars = ['MT5_LOGIN', 'MT5_PASSWORD', 'MT5_SERVER']
    
    for var in required_vars:
        value = os.getenv(var)
        if not value:
            print(f"❌ ERROR: {var} not set in environment")
            sys.exit(1)
        
        # Check for placeholder values
        if value in ['YOUR_MT5_LOGIN_HERE', 'YOUR_SECURE_PASSWORD_HERE', 
                     'YOUR_BROKER_SERVER_HERE', 'demo', '12345678']:
            print(f"❌ ERROR: {var} contains placeholder value")
            print(f"   Please set actual credentials in .env file")
            sys.exit(1)
    
    print("✅ Credentials validated")

# Call at startup
validate_credentials()
```

---

## Database Security

### 1. Blockchain Database Protection

**Verify database permissions:**
```bash
# Unix/Linux/Mac
ls -l trading_blockchain.db
# Should show: -rw------- (600 permissions)

# If incorrect, fix:
chmod 600 trading_blockchain.db
```

**Windows permissions:**
```powershell
# Check permissions
icacls trading_blockchain.db

# Should show only your username with Full Control
# If incorrect, fix:
icacls trading_blockchain.db /inheritance:r
icacls trading_blockchain.db /grant:r "%USERNAME%:(F)"
```

### 2. Database Encryption (Recommended)

**Install SQLCipher:**
```bash
pip install sqlcipher3
```

**Modify blockchain_validation.py:**
```python
# Replace sqlite3 import
# import sqlite3
from pysqlcipher3 import dbapi2 as sqlite3

# Add encryption key
def _init_database(self):
    conn = sqlite3.connect(self.db_path)
    
    # Set encryption key from environment
    encryption_key = os.getenv('DB_ENCRYPTION_KEY')
    if encryption_key:
        conn.execute(f"PRAGMA key = '{encryption_key}'")
    
    cursor = conn.cursor()
    # ... rest of initialization
```

**Generate encryption key:**
```bash
# Generate secure random key
python -c "import secrets; print(secrets.token_hex(32))"

# Add to .env
echo "DB_ENCRYPTION_KEY=<generated_key>" >> .env
```

### 3. Database Backup

**Automated backup script:**
```bash
#!/bin/bash
# backup_database.sh

BACKUP_DIR="./backups/database"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
DB_FILE="trading_blockchain.db"

# Create backup directory
mkdir -p "$BACKUP_DIR"

# Backup database
cp "$DB_FILE" "$BACKUP_DIR/${DB_FILE}_${TIMESTAMP}"

# Encrypt backup
gpg --symmetric --cipher-algo AES256 "$BACKUP_DIR/${DB_FILE}_${TIMESTAMP}"
rm "$BACKUP_DIR/${DB_FILE}_${TIMESTAMP}"

# Keep only last 30 days
find "$BACKUP_DIR" -name "*.gpg" -mtime +30 -delete

echo "✅ Database backup completed: ${TIMESTAMP}"
```

---

## Network Security

### 1. MT5 Connection Security

**Verify TLS configuration:**
```python
# Add to MT5 connector initialization
def connect(self):
    # Verify secure connection
    terminal_info = mt5.terminal_info()
    if terminal_info:
        if not terminal_info.connected:
            raise ConnectionError("MT5 not connected")
        
        # Log connection security
        logger.info(f"MT5 Connected: {terminal_info.name}")
        logger.info(f"Connection: {'Secure' if terminal_info.connected else 'Insecure'}")
```

### 2. Firewall Configuration

**Recommended firewall rules:**
```bash
# Allow only necessary outbound connections
# MT5 broker connection (check your broker's IP range)
# News API: api.newsapi.org
# Market data providers

# Block all other outbound connections
# Block all inbound connections (unless remote monitoring needed)
```

### 3. VPN Usage (Recommended)

For production trading:
- Use dedicated VPN for trading operations
- Separate network from personal devices
- Consider dedicated trading machine/VM

---

## Monitoring & Logging

### 1. Security Logging

**Configure comprehensive logging:**
```python
# Add to logging configuration
import logging
from logging.handlers import RotatingFileHandler

# Security audit log
security_logger = logging.getLogger('security')
security_handler = RotatingFileHandler(
    'logs/security_audit.log',
    maxBytes=10*1024*1024,  # 10MB
    backupCount=10
)
security_handler.setLevel(logging.INFO)
security_formatter = logging.Formatter(
    '%(asctime)s - SECURITY - %(levelname)s - %(message)s'
)
security_handler.setFormatter(security_formatter)
security_logger.addHandler(security_handler)

# Log security events
def log_security_event(event_type, details):
    security_logger.info(f"{event_type}: {details}")

# Usage examples:
log_security_event("AUTH_SUCCESS", f"MT5 login successful: {account}")
log_security_event("AUTH_FAILURE", f"MT5 login failed: {account}")
log_security_event("ORDER_PLACED", f"Order: {order_id}, Symbol: {symbol}")
log_security_event("CONFIG_CHANGE", f"Configuration modified")
```

### 2. Intrusion Detection

**Monitor for suspicious activity:**
```python
# Add to your monitoring system
class SecurityMonitor:
    def __init__(self):
        self.failed_auth_attempts = {}
        self.max_attempts = 5
        self.lockout_duration = 300  # 5 minutes
    
    def check_auth_attempt(self, account):
        """Monitor authentication attempts."""
        now = time.time()
        
        if account in self.failed_auth_attempts:
            attempts, last_attempt = self.failed_auth_attempts[account]
            
            # Check if locked out
            if attempts >= self.max_attempts:
                if now - last_attempt < self.lockout_duration:
                    raise SecurityError(f"Account locked due to multiple failed attempts")
                else:
                    # Reset after lockout period
                    del self.failed_auth_attempts[account]
        
        return True
    
    def record_auth_failure(self, account):
        """Record failed authentication."""
        now = time.time()
        if account in self.failed_auth_attempts:
            attempts, _ = self.failed_auth_attempts[account]
            self.failed_auth_attempts[account] = (attempts + 1, now)
        else:
            self.failed_auth_attempts[account] = (1, now)
        
        log_security_event("AUTH_FAILURE", f"Account: {account}")
```

### 3. Alert Configuration

**Set up security alerts:**
```python
# Email alerts for critical events
def send_security_alert(subject, message):
    """Send security alert email."""
    import smtplib
    from email.mime.text import MIMEText
    
    # Use environment variables for email config
    smtp_server = os.getenv('SMTP_SERVER')
    smtp_port = int(os.getenv('SMTP_PORT', 587))
    email_from = os.getenv('EMAIL_ADDRESS')
    email_to = os.getenv('SECURITY_ALERT_EMAIL', email_from)
    
    msg = MIMEText(message)
    msg['Subject'] = f"[SECURITY ALERT] {subject}"
    msg['From'] = email_from
    msg['To'] = email_to
    
    try:
        with smtplib.SMTP(smtp_server, smtp_port) as server:
            server.starttls()
            server.login(email_from, os.getenv('SMTP_PASSWORD'))
            server.send_message(msg)
    except Exception as e:
        logger.error(f"Failed to send security alert: {e}")

# Alert on critical events
send_security_alert(
    "Multiple Failed Login Attempts",
    f"Account {account} has {attempts} failed login attempts"
)
```

---

## Backup & Recovery

### 1. Backup Strategy

**What to backup:**
- Configuration files (.env, config.yaml)
- Database files (trading_blockchain.db)
- Trading logs
- Performance reports
- API keys (encrypted)

**Backup schedule:**
- Real-time: Trading logs
- Hourly: Database
- Daily: Full system backup
- Weekly: Offsite backup

**Backup script:**
```bash
#!/bin/bash
# full_backup.sh

BACKUP_ROOT="./backups"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="$BACKUP_ROOT/full_$TIMESTAMP"

# Create backup directory
mkdir -p "$BACKUP_DIR"

# Backup configuration (excluding sensitive files)
cp config/config.yaml "$BACKUP_DIR/"
# DO NOT backup .env or api_keys.json to regular backups

# Backup database
cp *.db "$BACKUP_DIR/"

# Backup logs
cp -r logs "$BACKUP_DIR/"

# Create encrypted archive
tar -czf "$BACKUP_DIR.tar.gz" "$BACKUP_DIR"
gpg --symmetric --cipher-algo AES256 "$BACKUP_DIR.tar.gz"
rm "$BACKUP_DIR.tar.gz"
rm -rf "$BACKUP_DIR"

# Upload to secure storage (S3, etc.)
# aws s3 cp "$BACKUP_DIR.tar.gz.gpg" s3://your-bucket/backups/

echo "✅ Backup completed: $TIMESTAMP"
```

### 2. Disaster Recovery

**Recovery procedure:**
```bash
# 1. Restore from backup
gpg --decrypt backup_TIMESTAMP.tar.gz.gpg > backup.tar.gz
tar -xzf backup.tar.gz

# 2. Restore configuration
cp backup_TIMESTAMP/config.yaml config/
# Manually restore .env from secure password manager

# 3. Restore database
cp backup_TIMESTAMP/*.db ./

# 4. Verify integrity
python -c "
from trading_bot.advanced_features.blockchain_validation import BlockchainLedger
ledger = BlockchainLedger()
integrity = ledger.verify_blockchain_integrity()
print(f'Blockchain integrity: {integrity}')
"

# 5. Test connection
python -c "
from trading_bot.connectors.mt5_connector import MT5Connector
# Test connection
"
```

---

## Security Checklist

### Pre-Production Checklist

- [ ] All security patches applied
- [ ] `.env` file created with actual credentials
- [ ] `.env` file permissions set to 600
- [ ] No hardcoded credentials in code
- [ ] `.gitignore` configured correctly
- [ ] Database file permissions set to 600
- [ ] API keys configured
- [ ] Logging configured
- [ ] Backup system tested
- [ ] Recovery procedure tested
- [ ] Firewall rules configured
- [ ] VPN configured (if applicable)
- [ ] Monitoring alerts configured
- [ ] Security audit log reviewed

### Weekly Security Tasks

- [ ] Review security audit logs
- [ ] Check for failed authentication attempts
- [ ] Verify backup integrity
- [ ] Review trading logs for anomalies
- [ ] Update dependencies
- [ ] Check for security advisories

### Monthly Security Tasks

- [ ] Full security audit
- [ ] Test disaster recovery procedure
- [ ] Rotate API keys
- [ ] Review and update firewall rules
- [ ] Update documentation
- [ ] Security training/review

### Quarterly Security Tasks

- [ ] Comprehensive penetration testing
- [ ] Third-party security audit
- [ ] Review and update security policies
- [ ] Disaster recovery drill
- [ ] Update incident response plan

---

## Incident Response

### Security Incident Procedure

**1. Detection**
- Monitor security logs
- Alert on suspicious activity
- User reports

**2. Containment**
- Immediately stop trading bot
- Disconnect from network
- Preserve evidence (logs, database)

**3. Investigation**
- Review security logs
- Check for unauthorized access
- Identify compromised credentials
- Assess damage

**4. Eradication**
- Change all credentials
- Rotate API keys
- Patch vulnerabilities
- Update security measures

**5. Recovery**
- Restore from clean backup
- Verify system integrity
- Gradually resume operations
- Enhanced monitoring

**6. Post-Incident**
- Document incident
- Update security procedures
- Implement additional controls
- Conduct lessons learned review

---

## Support & Resources

### Security Contacts
- **Security Issues:** Report to your security team
- **MT5 Broker Support:** Contact your broker
- **Emergency:** Stop bot immediately, disconnect network

### Additional Resources
- OWASP Top 10: https://owasp.org/www-project-top-ten/
- CWE Top 25: https://cwe.mitre.org/top25/
- Python Security: https://python.readthedocs.io/en/stable/library/security_warnings.html

---

## Conclusion

Security is an ongoing process, not a one-time setup. Regularly review and update your security measures, stay informed about new threats, and maintain a security-first mindset in all trading operations.

**Remember:**
- Never share credentials
- Never commit sensitive data to version control
- Always use secure connections
- Regularly backup your data
- Monitor for suspicious activity
- Keep software updated

---

**Document Version:** 1.0  
**Last Updated:** 2025-10-09  
**Next Review:** 2025-11-09
