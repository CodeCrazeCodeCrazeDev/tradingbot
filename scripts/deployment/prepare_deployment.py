"""
Deployment Preparation Script
Prepares the bot for production deployment with all necessary configurations
"""

import os
import sys
import io
import json
import shutil
from pathlib import Path
from datetime import datetime

# Set UTF-8 encoding for Windows
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')


class DeploymentPreparation:
    """Prepares bot for deployment"""
    
    def __init__(self, root_dir: str):
        self.root_dir = Path(root_dir)
        self.actions = []
        
    def print_header(self, text: str):
        """Print formatted header"""
        print(f"\n{'='*80}")
        print(f"{text.center(80)}")
        print(f"{'='*80}\n")
    
    def create_deployment_structure(self):
        """Create necessary directories for deployment"""
        print("Creating deployment structure...")
        
        dirs = ['logs', 'data', 'data/learned_knowledge', 'backups', 'test_reports']
        
        for dir_name in dirs:
            dir_path = self.root_dir / dir_name
            if not dir_path.exists():
                dir_path.mkdir(parents=True, exist_ok=True)
                print(f"  [CREATED] {dir_name}/")
                self.actions.append(f"Created {dir_name}/ directory")
            else:
                print(f"  [EXISTS] {dir_name}/")
    
    def create_env_file(self):
        """Create .env file from template if missing"""
        print("\nChecking environment configuration...")
        
        env_file = self.root_dir / '.env'
        env_template = self.root_dir / '.env.template'
        
        if not env_file.exists():
            if env_template.exists():
                shutil.copy(env_template, env_file)
                print(f"  [CREATED] .env from template")
                print(f"  [ACTION REQUIRED] Edit .env with your credentials")
                self.actions.append("Created .env from template - EDIT WITH YOUR CREDENTIALS")
            else:
                print(f"  [ERROR] .env.template not found")
        else:
            print(f"  [EXISTS] .env file")
    
    def create_deployment_config(self):
        """Create deployment configuration"""
        print("\nCreating deployment configuration...")
        
        config = {
            'deployment': {
                'mode': 'production',
                'auto_restart': True,
                'health_check_enabled': True,
                'health_check_port': 8080,
                'max_restart_attempts': 3,
                'restart_delay_seconds': 60
            },
            'logging': {
                'level': 'INFO',
                'file': 'logs/trading_bot.log',
                'max_size_mb': 100,
                'backup_count': 5,
                'console_output': True
            },
            'monitoring': {
                'enabled': True,
                'metrics_port': 9090,
                'alert_on_errors': True,
                'performance_tracking': True
            },
            'security': {
                'require_authentication': True,
                'api_rate_limiting': True,
                'max_requests_per_minute': 60,
                'ip_whitelist_enabled': False
            }
        }
        
        config_file = self.root_dir / 'config' / 'deployment_config.json'
        config_file.parent.mkdir(exist_ok=True)
        
        with open(config_file, 'w') as f:
            json.dump(config, f, indent=2)
        
        print(f"  [CREATED] config/deployment_config.json")
        self.actions.append("Created deployment configuration")
    
    def create_health_check(self):
        """Create health check endpoint"""
        print("\nCreating health check endpoint...")
        
        health_check_code = '''"""
Health Check Endpoint for Deployment Monitoring
"""

from http.server import HTTPServer, BaseHTTPRequestHandler
import json
from datetime import datetime
import threading

class HealthCheckHandler(BaseHTTPRequestHandler):
    """Simple health check HTTP handler"""
    
    def do_GET(self):
        """Handle GET requests"""
        if self.path == '/health':
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            
            response = {
                'status': 'healthy',
                'timestamp': datetime.now().isoformat(),
                'service': 'AlphaAlgo Trading Bot'
            }
            
            self.wfile.write(json.dumps(response).encode())
        else:
            self.send_response(404)
            self.end_headers()
    
    def log_message(self, format, *args):
        """Suppress default logging"""
        pass

def start_health_check_server(port=8080):
    """Start health check server in background thread"""
    server = HTTPServer(('0.0.0.0', port), HealthCheckHandler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    return server

if __name__ == '__main__':
    print("Starting health check server on port 8080...")
    start_health_check_server(8080)
    print("Health check available at http://localhost:8080/health")
    
    # Keep running
    import time
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\\nShutting down...")
'''
        
        health_check_file = self.root_dir / 'health_check.py'
        with open(health_check_file, 'w') as f:
            f.write(health_check_code)
        
        print(f"  [CREATED] health_check.py")
        self.actions.append("Created health check endpoint")
    
    def create_startup_script(self):
        """Create startup script for deployment"""
        print("\nCreating startup scripts...")
        
        # Windows startup script
        windows_script = '''@echo off
echo Starting AlphaAlgo Trading Bot...
echo.

REM Check if virtual environment exists
if not exist .venv (
    echo Creating virtual environment...
    python -m venv .venv
)

REM Activate virtual environment
call .venv\\Scripts\\activate.bat

REM Install/update dependencies
echo Installing dependencies...
pip install -r requirements.txt --quiet

REM Start health check in background
echo Starting health check server...
start /B python health_check.py

REM Wait a moment
timeout /t 2 /nobreak > nul

REM Start the bot
echo Starting trading bot...
python main.py --mode paper

REM If bot crashes, wait and restart
if errorlevel 1 (
    echo Bot crashed! Waiting 60 seconds before restart...
    timeout /t 60 /nobreak
    goto :start
)
'''
        
        windows_file = self.root_dir / 'start_production.bat'
        with open(windows_file, 'w') as f:
            f.write(windows_script)
        
        print(f"  [CREATED] start_production.bat")
        
        # Linux startup script
        linux_script = '''#!/bin/bash
echo "Starting AlphaAlgo Trading Bot..."
echo

# Check if virtual environment exists
if [ ! -d ".venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv .venv
fi

# Activate virtual environment
source .venv/bin/activate

# Install/update dependencies
echo "Installing dependencies..."
pip install -r requirements.txt --quiet

# Start health check in background
echo "Starting health check server..."
python health_check.py &
HEALTH_PID=$!

# Wait a moment
sleep 2

# Start the bot
echo "Starting trading bot..."
python main.py --mode paper

# If bot crashes, wait and restart
if [ $? -ne 0 ]; then
    echo "Bot crashed! Waiting 60 seconds before restart..."
    sleep 60
    exec $0
fi

# Cleanup
kill $HEALTH_PID 2>/dev/null
'''
        
        linux_file = self.root_dir / 'start_production.sh'
        with open(linux_file, 'w') as f:
            f.write(linux_script)
        
        # Make executable
        try:
            os.chmod(linux_file, 0o755)
        except:
            pass
        
        print(f"  [CREATED] start_production.sh")
        self.actions.append("Created startup scripts")
    
    def create_docker_files(self):
        """Create Docker deployment files"""
        print("\nCreating Docker configuration...")
        
        dockerfile = '''# AlphaAlgo Trading Bot - Production Dockerfile
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \\
    gcc \\
    g++ \\
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create necessary directories
RUN mkdir -p logs data backups

# Expose health check port
EXPOSE 8080

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV PAPER_TRADING=true

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \\
    CMD python -c "import requests; requests.get('http://localhost:8080/health')"

# Start the bot
CMD ["python", "main.py", "--mode", "paper"]
'''
        
        dockerfile_path = self.root_dir / 'Dockerfile.production'
        with open(dockerfile_path, 'w') as f:
            f.write(dockerfile)
        
        print(f"  [CREATED] Dockerfile.production")
        
        # Docker Compose
        docker_compose = '''version: '3.8'

services:
  trading-bot:
    build:
      context: .
      dockerfile: Dockerfile.production
    container_name: alphaalgo-bot
    restart: unless-stopped
    env_file:
      - .env
    volumes:
      - ./logs:/app/logs
      - ./data:/app/data
      - ./backups:/app/backups
    ports:
      - "8080:8080"
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8080/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s
    logging:
      driver: "json-file"
      options:
        max-size: "10m"
        max-file: "3"
'''
        
        compose_file = self.root_dir / 'docker-compose.production.yml'
        with open(compose_file, 'w') as f:
            f.write(docker_compose)
        
        print(f"  [CREATED] docker-compose.production.yml")
        self.actions.append("Created Docker configuration")
    
    def create_deployment_checklist(self):
        """Create deployment checklist"""
        print("\nCreating deployment checklist...")
        
        checklist = '''# AlphaAlgo Deployment Checklist

## Pre-Deployment

- [ ] All tests passing (`py -m pytest tests/`)
- [ ] No critical security issues
- [ ] `.env` file configured with production credentials
- [ ] Database connections tested
- [ ] API keys validated
- [ ] Backup strategy in place

## Configuration

- [ ] `PAPER_TRADING=false` for live trading (or `true` for paper trading)
- [ ] Risk limits configured (`MAX_DAILY_LOSS`, `MAX_POSITION_SIZE`)
- [ ] Email notifications configured
- [ ] Logging level set appropriately
- [ ] Health check port accessible

## Deployment

- [ ] Code deployed to production server
- [ ] Dependencies installed (`pip install -r requirements.txt`)
- [ ] Environment variables set
- [ ] Health check endpoint responding
- [ ] Auto-restart configured
- [ ] Monitoring enabled

## Post-Deployment

- [ ] Bot starts successfully
- [ ] Logs are being written
- [ ] Health check returns 200 OK
- [ ] No error messages in logs
- [ ] Performance metrics being tracked
- [ ] Alerts configured and working

## Monitoring

- [ ] Check logs regularly: `tail -f logs/trading_bot.log`
- [ ] Monitor health: `curl http://localhost:8080/health`
- [ ] Track performance metrics
- [ ] Set up alerts for errors
- [ ] Review trades daily

## Emergency Procedures

- [ ] Know how to stop the bot immediately
- [ ] Have rollback plan ready
- [ ] Emergency contacts configured
- [ ] Backup restoration tested

## Notes

- Start with paper trading mode first
- Monitor for 24-48 hours before going live
- Keep initial position sizes small
- Have stop-loss limits in place
'''
        
        checklist_file = self.root_dir / 'DEPLOYMENT_CHECKLIST.md'
        with open(checklist_file, 'w') as f:
            f.write(checklist)
        
        print(f"  [CREATED] DEPLOYMENT_CHECKLIST.md")
        self.actions.append("Created deployment checklist")
    
    def generate_summary(self):
        """Generate deployment preparation summary"""
        self.print_header("DEPLOYMENT PREPARATION SUMMARY")
        
        print(f"  Preparation Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"  Actions Completed: {len(self.actions)}\n")
        
        for i, action in enumerate(self.actions, 1):
            print(f"  {i}. {action}")
        
        print(f"\n  NEXT STEPS:")
        print(f"  1. Edit .env file with your production credentials")
        print(f"  2. Review DEPLOYMENT_CHECKLIST.md")
        print(f"  3. Run: py deployment_audit.py")
        print(f"  4. Test with: py start_production.bat (Windows) or ./start_production.sh (Linux)")
        print(f"  5. Monitor health: http://localhost:8080/health")
        
        print(f"\n  DEPLOYMENT OPTIONS:")
        print(f"  - Local: py start_production.bat")
        print(f"  - Docker: docker-compose -f docker-compose.production.yml up -d")
        print(f"  - Cloud: Follow cloud deployment guide")
    
    def run(self):
        """Run deployment preparation"""
        self.print_header("ALPHAALGO DEPLOYMENT PREPARATION")
        
        self.create_deployment_structure()
        self.create_env_file()
        self.create_deployment_config()
        self.create_health_check()
        self.create_startup_script()
        self.create_docker_files()
        self.create_deployment_checklist()
        self.generate_summary()
        
        self.print_header("PREPARATION COMPLETE")


def main():
    """Main entry point"""
    root_dir = Path(__file__).parent
    
    prep = DeploymentPreparation(root_dir)
    prep.run()


if __name__ == '__main__':
    main()
