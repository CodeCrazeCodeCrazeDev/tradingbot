# Elite Trading Bot - Deployment Guide

This guide provides instructions for deploying the Elite Trading Bot with Survival Core capabilities in various environments.

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Installation](#installation)
3. [Configuration](#configuration)
4. [Security Setup](#security-setup)
5. [Running the System](#running-the-system)
6. [Monitoring](#monitoring)
7. [Troubleshooting](#troubleshooting)
8. [Backup and Recovery](#backup-and-recovery)

## Prerequisites

Before deploying the Elite Trading Bot, ensure you have the following:

- Python 3.9+ installed
- MetaTrader 5 terminal (for MT5 connectivity)
- Redis server (optional, for enhanced caching)
- Sufficient disk space (at least 10GB recommended)
- Reliable internet connection

### Hardware Requirements

- **Minimum**: 4GB RAM, dual-core CPU
- **Recommended**: 8GB+ RAM, quad-core CPU
- **Production**: 16GB+ RAM, 8+ cores, SSD storage

## Installation

### 1. Clone the Repository

```bash
git clone https://github.com/yourusername/elite-trading-bot.git
cd elite-trading-bot
```

### 2. Create a Virtual Environment

```bash
python -m venv venv
```

### 3. Activate the Virtual Environment

**Windows**:
```bash
venv\Scripts\activate
```

**Linux/Mac**:
```bash
source venv/bin/activate
```

### 4. Install Dependencies

```bash
pip install -r requirements.txt
```

#### Optional: Install TA-Lib

The TA-Lib library requires special installation steps:

**Windows**:
Download and install the appropriate wheel file from [here](https://www.lfd.uci.edu/~gohlke/pythonlibs/#ta-lib)

**Linux**:
```bash
# Install TA-Lib dependencies
sudo apt-get install build-essential
sudo apt-get install libta-lib0 libta-lib-dev

# Install Python wrapper
pip install TA-Lib
```

## Configuration

### 1. Create Configuration Directory

```bash
mkdir -p config
```

### 2. Copy the Default Configuration

```bash
cp config/survival_config.yaml.example config/survival_config.yaml
```

### 3. Edit the Configuration

Edit `config/survival_config.yaml` with your preferred settings. At minimum, you should configure:

- Trading symbols
- Risk parameters
- API credentials
- Notification settings

### 4. Environment Variables

Create a `.env` file in the project root:

```
# API Keys (optional if using encrypted config)
MT5_LOGIN=your_login
MT5_PASSWORD=your_password
MT5_SERVER=your_server

# Notification settings
TELEGRAM_TOKEN=your_telegram_bot_token
TELEGRAM_CHAT_ID=your_chat_id

# Redis configuration (if used)
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=0
```

## Security Setup

### 1. Generate Encryption Key

The system will automatically generate an encryption key on first run, but you can pre-generate one:

```bash
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
```

### 2. Secure API Keys

Create an encrypted API keys file:

```bash
python -m trading_bot.tools.encrypt_api_keys
```

This interactive tool will prompt for your API keys and save them in encrypted format.

### 3. Set Secure Permissions

```bash
# For Linux/Mac
chmod 600 config/encryption.key
chmod 600 config/api_keys.json
```

## Running the System

### 1. Standard Run

```bash
python run_survival_system.py
```

### 2. With Custom Configuration

```bash
python run_survival_system.py --config path/to/custom_config.yaml
```

### 3. With Risk Level

```bash
python run_survival_system.py --risk-level conservative
```

Available risk levels: `conservative`, `moderate`, `aggressive`

### 4. Emergency Mode

```bash
python run_survival_system.py --emergency-mode
```

### 5. Running as a Service

#### Systemd (Linux)

Create a systemd service file `/etc/systemd/system/trading-bot.service`:

```ini
[Unit]
Description=Elite Trading Bot
After=network.target

[Service]
User=your_username
WorkingDirectory=/path/to/elite-trading-bot
ExecStart=/path/to/elite-trading-bot/venv/bin/python run_survival_system.py
Restart=on-failure
RestartSec=5s

[Install]
WantedBy=multi-user.target
```

Enable and start the service:

```bash
sudo systemctl enable trading-bot
sudo systemctl start trading-bot
```

#### Windows Service

Use NSSM (Non-Sucking Service Manager):

1. Download NSSM from [nssm.cc](https://nssm.cc/)
2. Install the service:
   ```
   nssm install EliteTradingBot
   ```
3. Configure the service with the path to your Python executable and script

## Monitoring

### 1. Logs

Logs are stored in the `logs` directory. The main log file is `logs/survival_system.log`.

### 2. Telegram Notifications

If configured, the system will send notifications to your Telegram bot.

### 3. Dashboard

A web-based dashboard is available at http://localhost:8050/ when running with the dashboard enabled:

```bash
python run_survival_system.py --with-dashboard
```

## Troubleshooting

### Common Issues

1. **Connection Errors**:
   - Check internet connectivity
   - Verify MT5 terminal is running
   - Ensure API credentials are correct

2. **Permission Errors**:
   - Check file permissions on config files
   - Ensure the user has write access to the logs directory

3. **Dependency Issues**:
   - Verify all dependencies are installed: `pip check`
   - Reinstall problematic packages

### Diagnostic Tools

The system includes built-in diagnostic tools:

```bash
python -m trading_bot.tools.system_check
```

## Backup and Recovery

### 1. Critical Files to Backup

- `config/survival_config.yaml`
- `config/encryption.key`
- `config/api_keys.json`
- `data/` directory (contains historical data)

### 2. Backup Script

```bash
python -m trading_bot.tools.backup
```

### 3. Recovery Procedure

1. Install the system as described above
2. Restore the backed-up configuration files
3. Run the system with the `--recover` flag:
   ```bash
   python run_survival_system.py --recover
   ```

## Advanced Deployment

For production environments, consider:

1. **Load Balancing**: Deploy multiple instances with different symbol sets
2. **Database Clustering**: Set up Redis cluster for high availability
3. **Monitoring**: Integrate with Prometheus/Grafana for advanced metrics
4. **Containerization**: Use Docker for consistent deployment across environments

---

For additional support, please refer to the project documentation or contact the development team.
