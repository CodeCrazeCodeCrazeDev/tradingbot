"""
Deployment script for AlphaAlgo 2.0
"""

import yaml
import subprocess
import sys
import os
import logging
from datetime import datetime
import time
import argparse
import shutil

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(f'deploy_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log'),
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)


def load_config(config_path: str) -> dict:
    """Load deployment configuration."""
    with open(config_path, 'r') as f:
        return yaml.safe_load(f)


def run_command(command: str, cwd: str = None) -> bool:
    """Run shell command and return success status."""
    try:
        result = subprocess.run(
            command,
            shell=True,
            cwd=cwd,
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        logger.info(f"✅ Command succeeded: {command}")
        return True
    except subprocess.CalledProcessError as e:
        logger.error(f"❌ Command failed: {command}")
        logger.error(f"Error: {e.stderr.decode()}")
        return False


def check_dependencies(config: dict) -> bool:
    """Check system dependencies."""
    logger.info("🔍 Checking dependencies...")
    
    # Check Python version
    python_version = sys.version_info
    required_version = tuple(map(int, config['dependencies']['python'].split('.')))
    
    if python_version < required_version:
        logger.error(f"❌ Python {config['dependencies']['python']} required")
        return False
    
    # Check CUDA if GPU enabled
    if config['resources']['gpu_enabled']:
        cuda_command = "nvidia-smi"
        if not run_command(cuda_command):
            logger.error("❌ CUDA not available")
            return False
    
    # Check pip dependencies
    if not run_command("pip check"):
        logger.error("❌ Pip dependency check failed")
        return False
    
    logger.info("✅ All dependencies satisfied")
    return True


def run_tests(config: dict) -> bool:
    """Run test suite."""
    logger.info("🧪 Running tests...")
    return run_command("python tests/run_tests.py")


def backup_data(config: dict) -> bool:
    """Backup current data."""
    if not config['backup']['enabled']:
        logger.info("ℹ️ Backup disabled, skipping")
        return True
    
    logger.info("💾 Backing up data...")
    
    backup_dir = f"backups/backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    os.makedirs(backup_dir, exist_ok=True)
    
    try:
        # Backup database
        if config['database']['type'] == 'postgresql':
            dump_command = (
                f"pg_dump -h {config['database']['host']} "
                f"-U {config['database']['user']} "
                f"-d {config['database']['name']} "
                f"> {backup_dir}/database.sql"
            )
            if not run_command(dump_command):
                return False
        
        # Backup model checkpoints
        if os.path.exists(config['model']['checkpoint_dir']):
            shutil.copytree(
                config['model']['checkpoint_dir'],
                f"{backup_dir}/models"
            )
        
        logger.info("✅ Backup completed")
        return True
        
    except Exception as e:
        logger.error(f"❌ Backup failed: {str(e)}")
        return False


def migrate_database(config: dict) -> bool:
    """Run database migrations."""
    logger.info("🔄 Running database migrations...")
    return run_command("alembic upgrade head")


def start_services(config: dict) -> bool:
    """Start all services."""
    logger.info("🚀 Starting services...")
    return run_command("supervisord -c supervisord.conf")


def health_check(config: dict) -> bool:
    """Run health checks."""
    logger.info("🏥 Running health checks...")
    
    for endpoint in config['health_check']['endpoints']:
        retries = config['health_check']['retries']
        while retries > 0:
            if run_command(f"curl -f {endpoint['url']}"):
                break
            retries -= 1
            if retries > 0:
                time.sleep(5)
        
        if retries == 0:
            logger.error(f"❌ Health check failed for {endpoint['name']}")
            return False
    
    logger.info("✅ All health checks passed")
    return True


def rollback(config: dict) -> bool:
    """Rollback deployment."""
    logger.info("⚠️ Rolling back deployment...")
    
    try:
        # Stop services
        run_command("supervisorctl stop all")
        
        # Restore latest backup
        backup_dir = "backups"
        if os.path.exists(backup_dir):
            latest_backup = max(
                [os.path.join(backup_dir, d) for d in os.listdir(backup_dir)],
                key=os.path.getmtime
            )
            
            # Restore database
            if os.path.exists(f"{latest_backup}/database.sql"):
                restore_command = (
                    f"psql -h {config['database']['host']} "
                    f"-U {config['database']['user']} "
                    f"-d {config['database']['name']} "
                    f"< {latest_backup}/database.sql"
                )
                run_command(restore_command)
            
            # Restore models
            if os.path.exists(f"{latest_backup}/models"):
                shutil.rmtree(config['model']['checkpoint_dir'], ignore_errors=True)
                shutil.copytree(
                    f"{latest_backup}/models",
                    config['model']['checkpoint_dir']
                )
        
        # Restart services
        run_command("supervisorctl start all")
        
        logger.info("✅ Rollback completed")
        return True
        
    except Exception as e:
        logger.error(f"❌ Rollback failed: {str(e)}")
        return False


def deploy() -> bool:
    """Main deployment function."""
    try:
        # Load configuration
        config = load_config('config/deployment.yaml')
        
        # Pre-deployment
        logger.info("="*80)
        logger.info("🚀 Starting AlphaAlgo 2.0 Deployment")
        logger.info("="*80)
        
        # Check dependencies
        if not check_dependencies(config):
            return False
        
        # Run tests
        if not run_tests(config):
            return False
        
        # Backup data
        if not backup_data(config):
            return False
        
        # Database migrations
        if not migrate_database(config):
            if not rollback(config):
                logger.error("❌ Rollback failed")
            return False
        
        # Start services
        if not start_services(config):
            if not rollback(config):
                logger.error("❌ Rollback failed")
            return False
        
        # Health checks
        if not health_check(config):
            if not rollback(config):
                logger.error("❌ Rollback failed")
            return False
        
        logger.info("="*80)
        logger.info("✅ Deployment Successful!")
        logger.info("="*80)
        
        return True
        
    except Exception as e:
        logger.error(f"❌ Deployment failed: {str(e)}")
        return False


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Deploy AlphaAlgo 2.0')
    parser.add_argument('--config', default='config/deployment.yaml',
                      help='Path to deployment configuration')
    
    args = parser.parse_args()
    
    success = deploy()
    sys.exit(0 if success else 1)
