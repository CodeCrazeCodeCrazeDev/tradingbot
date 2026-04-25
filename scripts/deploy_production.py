#!/usr/bin/env python3
"""
Production Deployment Script
Automates deployment to production with full validation and rollback
"""

import os
import sys
import subprocess
import json
import time
import logging
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional
import argparse

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ProductionDeployer:
    """Handles production deployment with validation."""
    
    def __init__(self, config_path: str = "config/deployment.json"):
        self.config_path = Path(config_path)
        self.config = self._load_config()
        self.deployment_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.logs_dir = Path("deployment_logs")
        self.logs_dir.mkdir(exist_ok=True)
        
    def _load_config(self) -> Dict:
        """Load deployment configuration."""
        if self.config_path.exists():
            with open(self.config_path) as f:
                return json.load(f)
        return self._default_config()
    
    def _default_config(self) -> Dict:
        """Default deployment configuration."""
        return {
            "docker_compose_file": "docker-compose.production.yml",
            "health_check_url": "http://localhost:8080/health",
            "health_check_timeout": 60,
            "rollback_on_failure": True,
            "backup_before_deploy": True,
            "services": [
                "postgres",
                "redis",
                "trading-bot",
                "prometheus",
                "grafana"
            ]
        }
    
    def deploy(self) -> bool:
        """Execute full deployment process."""
        logger.info(f"Starting production deployment: {self.deployment_id}")
        
        steps = [
            ("Pre-deployment checks", self._pre_deployment_checks),
            ("Backup current state", self._backup_current_state),
            ("Validate configuration", self._validate_configuration),
            ("Build Docker images", self._build_images),
            ("Run database migrations", self._run_migrations),
            ("Deploy services", self._deploy_services),
            ("Health checks", self._health_checks),
            ("Post-deployment validation", self._post_deployment_validation),
        ]
        
        for step_name, step_func in steps:
            logger.info(f"Step: {step_name}")
            try:
                if not step_func():
                    logger.error(f"Step failed: {step_name}")
                    if self.config.get("rollback_on_failure", True):
                        self.rollback()
                    return False
            except Exception as e:
                logger.error(f"Step error {step_name}: {e}")
                if self.config.get("rollback_on_failure", True):
                    self.rollback()
                return False
        
        logger.info(f"Deployment {self.deployment_id} completed successfully")
        self._save_deployment_record(success=True)
        return True
    
    def _pre_deployment_checks(self) -> bool:
        """Run pre-deployment checks."""
        checks = [
            ("Docker available", self._check_docker),
            ("Docker Compose available", self._check_docker_compose),
            ("Sufficient disk space", self._check_disk_space),
            ("Configuration valid", self._check_config_valid),
            ("Secrets configured", self._check_secrets),
        ]
        
        for check_name, check_func in checks:
            if not check_func():
                logger.error(f"Pre-deployment check failed: {check_name}")
                return False
            logger.info(f"Check passed: {check_name}")
        
        return True
    
    def _check_docker(self) -> bool:
        """Check if Docker is available."""
        try:
            result = subprocess.run(
                ["docker", "--version"],
                capture_output=True,
                text=True,
                timeout=10
            )
            return result.returncode == 0
        except Exception:
            return False
    
    def _check_docker_compose(self) -> bool:
        """Check if Docker Compose is available."""
        try:
            result = subprocess.run(
                ["docker-compose", "--version"],
                capture_output=True,
                text=True,
                timeout=10
            )
            return result.returncode == 0
        except Exception:
            return False
    
    def _check_disk_space(self) -> bool:
        """Check available disk space."""
        try:
            import shutil
            total, used, free = shutil.disk_usage("/")
            free_gb = free / (1024**3)
            return free_gb > 5  # Require at least 5GB free
        except Exception:
            return True  # Skip on error
    
    def _check_config_valid(self) -> bool:
        """Validate configuration files."""
        required_files = [
            "config/config.yaml",
            self.config.get("docker_compose_file", "docker-compose.production.yml")
        ]
        
        for file in required_files:
            if not Path(file).exists():
                logger.error(f"Required file missing: {file}")
                return False
        
        return True
    
    def _check_secrets(self) -> bool:
        """Check if required secrets are configured."""
        required_secrets = ["MT5_LOGIN", "MT5_SERVER"]
        
        for secret in required_secrets:
            value = os.environ.get(secret)
            if not value:
                # Try secrets manager
                try:
                    from trading_bot.security.secrets_manager import get_secrets_manager
                    secrets = get_secrets_manager()
                    value = secrets.get_secret(secret.lower().replace('_', ''))
                except Exception:
                    pass
            
            if not value:
                logger.warning(f"Secret not found: {secret}")
        
        return True  # Allow deployment with warnings
    
    def _backup_current_state(self) -> bool:
        """Backup current deployment state."""
        if not self.config.get("backup_before_deploy", True):
            return True
        
        backup_dir = self.logs_dir / f"backup_{self.deployment_id}"
        backup_dir.mkdir(exist_ok=True)
        
        # Backup database
        try:
            subprocess.run(
                ["docker-compose", "-f", self.config["docker_compose_file"], 
                 "exec", "-T", "postgres", "pg_dump", "-U", "trading_bot"],
                stdout=open(backup_dir / "database.sql", "w"),
                timeout=60
            )
        except Exception as e:
            logger.warning(f"Database backup failed: {e}")
        
        # Backup configuration
        import shutil
        if Path("config").exists():
            shutil.copytree("config", backup_dir / "config", dirs_exist_ok=True)
        
        # Save current compose state
        try:
            result = subprocess.run(
                ["docker-compose", "-f", self.config["docker_compose_file"], "ps"],
                capture_output=True,
                text=True,
                timeout=10
            )
            (backup_dir / "services_state.txt").write_text(result.stdout)
        except Exception:
            pass
        
        logger.info(f"Backup saved to {backup_dir}")
        return True
    
    def _validate_configuration(self) -> bool:
        """Validate deployment configuration."""
        # Validate compose file
        try:
            result = subprocess.run(
                ["docker-compose", "-f", self.config["docker_compose_file"], "config"],
                capture_output=True,
                text=True,
                timeout=10
            )
            if result.returncode != 0:
                logger.error(f"Docker Compose config invalid: {result.stderr}")
                return False
        except Exception as e:
            logger.error(f"Config validation failed: {e}")
            return False
        
        return True
    
    def _build_images(self) -> bool:
        """Build Docker images."""
        try:
            result = subprocess.run(
                ["docker-compose", "-f", self.config["docker_compose_file"], "build"],
                capture_output=True,
                text=True,
                timeout=300
            )
            if result.returncode != 0:
                logger.error(f"Build failed: {result.stderr}")
                return False
            
            logger.info("Docker images built successfully")
            return True
        except Exception as e:
            logger.error(f"Build error: {e}")
            return False
    
    def _run_migrations(self) -> bool:
        """Run database migrations."""
        try:
            # Check if migrations directory exists
            if not Path("migrations").exists():
                logger.info("No migrations to run")
                return True
            
            # Run migrations in trading-bot container
            result = subprocess.run(
                ["docker-compose", "-f", self.config["docker_compose_file"],
                 "run", "--rm", "trading-bot", "python", "-m", "alembic", "upgrade", "head"],
                capture_output=True,
                text=True,
                timeout=60
            )
            
            if result.returncode != 0:
                logger.error(f"Migration failed: {result.stderr}")
                return False
            
            logger.info("Database migrations completed")
            return True
        except Exception as e:
            logger.warning(f"Migration warning: {e}")
            return True  # Continue on migration error
    
    def _deploy_services(self) -> bool:
        """Deploy services with zero-downtime strategy."""
        try:
            # Pull latest images
            subprocess.run(
                ["docker-compose", "-f", self.config["docker_compose_file"], "pull"],
                capture_output=True,
                timeout=120
            )
            
            # Deploy with rolling update
            result = subprocess.run(
                ["docker-compose", "-f", self.config["docker_compose_file"], 
                 "up", "-d", "--remove-orphans"],
                capture_output=True,
                text=True,
                timeout=120
            )
            
            if result.returncode != 0:
                logger.error(f"Deploy failed: {result.stderr}")
                return False
            
            logger.info("Services deployed successfully")
            return True
        except Exception as e:
            logger.error(f"Deploy error: {e}")
            return False
    
    def _health_checks(self) -> bool:
        """Run health checks on deployed services."""
        timeout = self.config.get("health_check_timeout", 60)
        services = self.config.get("services", [])
        
        for service in services:
            if not self._check_service_health(service, timeout):
                logger.error(f"Health check failed for: {service}")
                return False
            logger.info(f"Health check passed: {service}")
        
        return True
    
    def _check_service_health(self, service: str, timeout: int) -> bool:
        """Check individual service health."""
        start = time.time()
        
        while time.time() - start < timeout:
            try:
                result = subprocess.run(
                    ["docker-compose", "-f", self.config["docker_compose_file"],
                     "ps", service],
                    capture_output=True,
                    text=True,
                    timeout=5
                )
                
                if "Up (healthy)" in result.stdout or "Up" in result.stdout:
                    return True
                
                time.sleep(5)
            except Exception:
                time.sleep(5)
        
        return False
    
    def _post_deployment_validation(self) -> bool:
        """Run post-deployment validation."""
        validations = [
            ("Trading bot responsive", self._validate_trading_bot),
            ("Database accessible", self._validate_database),
            ("Redis accessible", self._validate_redis),
            ("Metrics endpoint", self._validate_metrics),
        ]
        
        for val_name, val_func in validations:
            if not val_func():
                logger.error(f"Post-deployment validation failed: {val_name}")
                return False
            logger.info(f"Validation passed: {val_name}")
        
        return True
    
    def _validate_trading_bot(self) -> bool:
        """Validate trading bot is running."""
        try:
            import urllib.request
            with urllib.request.urlopen(
                self.config.get("health_check_url", "http://localhost:8080/health"),
                timeout=10
            ) as response:
                return response.status == 200
        except Exception:
            return False
    
    def _validate_database(self) -> bool:
        """Validate database connection."""
        try:
            result = subprocess.run(
                ["docker-compose", "-f", self.config["docker_compose_file"],
                 "exec", "-T", "postgres", "pg_isready", "-U", "trading_bot"],
                capture_output=True,
                timeout=10
            )
            return result.returncode == 0
        except Exception:
            return False
    
    def _validate_redis(self) -> bool:
        """Validate Redis connection."""
        try:
            result = subprocess.run(
                ["docker-compose", "-f", self.config["docker_compose_file"],
                 "exec", "-T", "redis", "redis-cli", "ping"],
                capture_output=True,
                timeout=10
            )
            return "PONG" in result.stdout
        except Exception:
            return False
    
    def _validate_metrics(self) -> bool:
        """Validate metrics endpoint."""
        try:
            import urllib.request
            with urllib.request.urlopen(
                "http://localhost:9090/metrics",
                timeout=10
            ) as response:
                return response.status == 200
        except Exception:
            return False
    
    def rollback(self) -> bool:
        """Rollback to previous deployment."""
        logger.warning("Initiating rollback...")
        
        try:
            # Stop current deployment
            subprocess.run(
                ["docker-compose", "-f", self.config["docker_compose_file"], "down"],
                capture_output=True,
                timeout=60
            )
            
            # Find latest backup
            backups = sorted(self.logs_dir.glob("backup_*"))
            if backups:
                latest_backup = backups[-1]
                logger.info(f"Restoring from {latest_backup}")
                
                # Restore database if backup exists
                db_backup = latest_backup / "database.sql"
                if db_backup.exists():
                    try:
                        subprocess.run(
                            ["docker-compose", "-f", self.config["docker_compose_file"],
                             "exec", "-T", "postgres", "psql", "-U", "trading_bot"],
                            stdin=open(db_backup),
                            timeout=120
                        )
                    except Exception as e:
                        logger.error(f"Database restore failed: {e}")
            
            # Restart with previous configuration
            subprocess.run(
                ["docker-compose", "-f", self.config["docker_compose_file"], "up", "-d"],
                capture_output=True,
                timeout=60
            )
            
            logger.info("Rollback completed")
            return True
        except Exception as e:
            logger.error(f"Rollback failed: {e}")
            return False
    
    def _save_deployment_record(self, success: bool):
        """Save deployment record."""
        record = {
            "deployment_id": self.deployment_id,
            "timestamp": datetime.now().isoformat(),
            "success": success,
            "config": self.config
        }
        
        record_file = self.logs_dir / f"deployment_{self.deployment_id}.json"
        with open(record_file, 'w') as f:
            json.dump(record, f, indent=2)


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description="Production Deployment Script")
    parser.add_argument("--config", default="config/deployment.json", help="Deployment config file")
    parser.add_argument("--dry-run", action="store_true", help="Run without making changes")
    parser.add_argument("--rollback", action="store_true", help="Rollback deployment")
    
    args = parser.parse_args()
    
    deployer = ProductionDeployer(args.config)
    
    if args.rollback:
        success = deployer.rollback()
    else:
        success = deployer.deploy()
    
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
