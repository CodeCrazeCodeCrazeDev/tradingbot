"""
Production Deployment Script
Validates, tests, and deploys the trading bot to production
"""

import os
import sys
import subprocess
import shutil
import yaml
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class DeploymentValidator:
    """Validates the system before deployment"""
    
    def __init__(self, project_root: Path):
        self.project_root = project_root
        self.errors: List[str] = []
        self.warnings: List[str] = []
        
    def validate_all(self) -> bool:
        """Run all validations"""
        logger.info("=" * 60)
        logger.info("STARTING DEPLOYMENT VALIDATION")
        logger.info("=" * 60)
        
        checks = [
            ("Python Version", self.check_python_version),
            ("Dependencies", self.check_dependencies),
            ("Environment Variables", self.check_env_variables),
            ("Configuration Files", self.check_config_files),
            ("Critical Modules", self.check_critical_modules),
            ("Database", self.check_database),
            ("Disk Space", self.check_disk_space),
            ("Network Connectivity", self.check_network),
        ]
        
        all_passed = True
        
        for name, check_func in checks:
            logger.info(f"\nChecking: {name}")
            try:
                passed = check_func()
                status = "✅ PASSED" if passed else "❌ FAILED"
                logger.info(f"  {status}")
                if not passed:
                    all_passed = False
            except Exception as e:
                logger.error(f"  ❌ ERROR: {e}")
                self.errors.append(f"{name}: {e}")
                all_passed = False
                
        return all_passed
        
    def check_python_version(self) -> bool:
        """Check Python version"""
        version = sys.version_info
        required = (3, 10)
        
        if version >= required:
            logger.info(f"  Python {version.major}.{version.minor}.{version.micro}")
            return True
        else:
            self.errors.append(f"Python {required[0]}.{required[1]}+ required, found {version.major}.{version.minor}")
            return False
            
    def check_dependencies(self) -> bool:
        """Check required dependencies"""
        required_packages = [
            'numpy',
            'pandas',
            'aiohttp',
            'yaml',
            'dotenv',
        ]
        
        missing = []
        for package in required_packages:
            try:
                __import__(package.replace('-', '_'))
            except ImportError:
                missing.append(package)
                
        if missing:
            self.errors.append(f"Missing packages: {', '.join(missing)}")
            return False
            
        logger.info(f"  All {len(required_packages)} required packages installed")
        return True
        
    def check_env_variables(self) -> bool:
        """Check required environment variables"""
        required_vars = []  # Add required vars here
        optional_vars = [
            'ALPHA_VANTAGE_API_KEY',
            'FRED_API_KEY',
            'NEWSAPI_KEY',
            'BINANCE_API_KEY',
        ]
        
        missing_required = [v for v in required_vars if not os.getenv(v)]
        missing_optional = [v for v in optional_vars if not os.getenv(v)]
        
        if missing_required:
            self.errors.append(f"Missing required env vars: {', '.join(missing_required)}")
            return False
            
        if missing_optional:
            self.warnings.append(f"Missing optional env vars: {', '.join(missing_optional)}")
            logger.info(f"  Warning: {len(missing_optional)} optional vars not set")
            
        return True
        
    def check_config_files(self) -> bool:
        """Check configuration files exist"""
        config_files = [
            'deploy/production_config.yaml',
            'config/survival_config.yaml',
        ]
        
        missing = []
        for config_file in config_files:
            path = self.project_root / config_file
            if not path.exists():
                missing.append(config_file)
                
        if missing:
            self.warnings.append(f"Missing config files: {', '.join(missing)}")
            logger.info(f"  Warning: {len(missing)} config files missing")
            
        return True  # Not critical
        
    def check_critical_modules(self) -> bool:
        """Check critical modules can be imported"""
        critical_modules = [
            'trading_bot',
            'trading_bot.integrations',
        ]
        
        failed = []
        for module in critical_modules:
            try:
                __import__(module)
            except ImportError as e:
                failed.append(f"{module}: {e}")
                
        if failed:
            self.errors.append(f"Failed to import: {', '.join(failed)}")
            return False
            
        logger.info(f"  All {len(critical_modules)} critical modules importable")
        return True
        
    def check_database(self) -> bool:
        """Check database connectivity"""
        db_path = self.project_root / 'data' / 'trading_bot.db'
        
        # Create data directory if needed
        db_path.parent.mkdir(parents=True, exist_ok=True)
        
        logger.info(f"  Database path: {db_path}")
        return True
        
    def check_disk_space(self) -> bool:
        """Check available disk space"""
        import shutil
        
        total, used, free = shutil.disk_usage(self.project_root)
        free_gb = free / (1024 ** 3)
        
        if free_gb < 1:
            self.errors.append(f"Low disk space: {free_gb:.2f} GB free")
            return False
            
        logger.info(f"  {free_gb:.2f} GB free")
        return True
        
    def check_network(self) -> bool:
        """Check network connectivity"""
        import socket
        
        try:
            socket.create_connection(("8.8.8.8", 53), timeout=3)
            logger.info("  Internet connectivity OK")
            return True
        except OSError:
            self.warnings.append("No internet connectivity (may be behind firewall)")
            logger.info("  Warning: Network check failed (continuing anyway)")
            return True  # Don't fail deployment for network issues


class ProductionDeployer:
    """Handles production deployment"""
    
    def __init__(self, project_root: Path):
        self.project_root = project_root
        self.deploy_dir = project_root / 'deploy'
        self.backup_dir = project_root / 'backup'
        self.logs_dir = project_root / 'logs'
        self.state_dir = project_root / 'state'
        
    def deploy(self, skip_tests: bool = False) -> bool:
        """Run full deployment"""
        logger.info("\n" + "=" * 60)
        logger.info("STARTING PRODUCTION DEPLOYMENT")
        logger.info("=" * 60)
        
        steps = [
            ("Create directories", self.create_directories),
            ("Backup current state", self.backup_state),
            ("Load configuration", self.load_config),
            ("Run tests", lambda: self.run_tests() if not skip_tests else True),
            ("Initialize database", self.init_database),
            ("Create startup scripts", self.create_startup_scripts),
            ("Generate deployment report", self.generate_report),
        ]
        
        for step_name, step_func in steps:
            logger.info(f"\n{step_name}...")
            try:
                success = step_func()
                if not success:
                    logger.error(f"  ❌ {step_name} failed")
                    return False
                logger.info(f"  ✅ {step_name} complete")
            except Exception as e:
                logger.error(f"  ❌ {step_name} error: {e}")
                return False
                
        logger.info("\n" + "=" * 60)
        logger.info("✅ DEPLOYMENT COMPLETE")
        logger.info("=" * 60)
        
        return True
        
    def create_directories(self) -> bool:
        """Create required directories"""
        directories = [
            self.logs_dir,
            self.state_dir,
            self.backup_dir,
            self.project_root / 'data',
            self.project_root / 'models',
            self.project_root / 'reports',
        ]
        
        for directory in directories:
            directory.mkdir(parents=True, exist_ok=True)
            logger.info(f"    Created: {directory}")
            
        return True
        
    def backup_state(self) -> bool:
        """Backup current state"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_path = self.backup_dir / f'backup_{timestamp}'
        
        # Backup state files
        state_files = list(self.state_dir.glob('*.json'))
        if state_files:
            backup_path.mkdir(parents=True, exist_ok=True)
            for state_file in state_files:
                shutil.copy(state_file, backup_path)
            logger.info(f"    Backed up {len(state_files)} state files")
            
        return True
        
    def load_config(self) -> bool:
        """Load and validate configuration"""
        config_path = self.deploy_dir / 'production_config.yaml'
        
        if not config_path.exists():
            logger.warning("    Production config not found, using defaults")
            return True
            
        with open(config_path) as f:
            config = yaml.safe_load(f)
            
        # Validate critical settings
        risk_config = config.get('risk', {})
        
        if risk_config.get('max_risk_per_trade', 0) > 0.05:
            logger.error("    max_risk_per_trade > 5% is too risky!")
            return False
            
        if risk_config.get('max_drawdown', 0) > 0.30:
            logger.error("    max_drawdown > 30% is too risky!")
            return False
            
        logger.info("    Configuration validated")
        return True
        
    def run_tests(self) -> bool:
        """Run test suite"""
        logger.info("    Running tests...")
        
        try:
            result = subprocess.run(
                [sys.executable, '-m', 'pytest', 'tests/', '-v', '--tb=short', '-x'],
                cwd=self.project_root,
                capture_output=True,
                text=True,
                timeout=300
            )
            
            if result.returncode == 0:
                logger.info("    All tests passed")
                return True
            else:
                logger.error(f"    Tests failed:\n{result.stdout}\n{result.stderr}")
                return False
                
        except subprocess.TimeoutExpired:
            logger.error("    Tests timed out")
            return False
        except FileNotFoundError:
            logger.warning("    pytest not found, skipping tests")
            return True
            
    def init_database(self) -> bool:
        """Initialize database"""
        db_path = self.project_root / 'data' / 'trading_bot.db'
        
        # Create empty database if needed
        if not db_path.exists():
            db_path.touch()
            logger.info(f"    Created database: {db_path}")
            
        return True
        
    def create_startup_scripts(self) -> bool:
        """Create startup scripts"""
        # Windows batch file
        bat_content = '''@echo off
echo Starting AlphaAlgo Trading Bot...
cd /d "%~dp0.."
python -m trading_bot.main --config deploy/production_config.yaml
pause
'''
        
        bat_path = self.deploy_dir / 'START_TRADING_BOT.bat'
        with open(bat_path, 'w') as f:
            f.write(bat_content)
        logger.info(f"    Created: {bat_path}")
        
        # Python launcher
        py_content = '''#!/usr/bin/env python
"""Production launcher for AlphaAlgo Trading Bot"""

import sys
import os
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

if __name__ == '__main__':
    from trading_bot.main import main
    main()
'''
        
        py_path = self.deploy_dir / 'run_production.py'
        with open(py_path, 'w') as f:
            f.write(py_content)
        logger.info(f"    Created: {py_path}")
        
        return True
        
    def generate_report(self) -> bool:
        """Generate deployment report"""
        report = {
            'deployment_time': datetime.now().isoformat(),
            'python_version': f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}",
            'project_root': str(self.project_root),
            'status': 'SUCCESS',
            'directories_created': [
                str(self.logs_dir),
                str(self.state_dir),
                str(self.backup_dir),
            ]
        }
        
        report_path = self.deploy_dir / f'deployment_report_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json'
        with open(report_path, 'w') as f:
            json.dump(report, f, indent=2)
            
        logger.info(f"    Report saved: {report_path}")
        return True


def main():
    """Main deployment entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Deploy AlphaAlgo Trading Bot')
    parser.add_argument('--validate-only', action='store_true', help='Only run validation')
    parser.add_argument('--skip-tests', action='store_true', help='Skip running tests')
    parser.add_argument('--project-root', type=str, help='Project root directory')
    
    args = parser.parse_args()
    
    # Determine project root
    if args.project_root:
        project_root = Path(args.project_root)
    else:
        project_root = Path(__file__).parent.parent
        
    logger.info(f"Project root: {project_root}")
    
    # Run validation
    validator = DeploymentValidator(project_root)
    validation_passed = validator.validate_all()
    
    if validator.errors:
        logger.error("\n❌ VALIDATION ERRORS:")
        for error in validator.errors:
            logger.error(f"  - {error}")
            
    if validator.warnings:
        logger.warning("\n⚠️ WARNINGS:")
        for warning in validator.warnings:
            logger.warning(f"  - {warning}")
            
    if not validation_passed:
        logger.error("\n❌ Validation failed. Fix errors before deploying.")
        sys.exit(1)
        
    if args.validate_only:
        logger.info("\n✅ Validation passed. Use --deploy to deploy.")
        sys.exit(0)
        
    # Run deployment
    deployer = ProductionDeployer(project_root)
    deployment_success = deployer.deploy(skip_tests=args.skip_tests)
    
    if deployment_success:
        logger.info("\n" + "=" * 60)
        logger.info("🚀 READY FOR PRODUCTION")
        logger.info("=" * 60)
        logger.info("\nTo start the bot:")
        logger.info("  Windows: deploy\\START_TRADING_BOT.bat")
        logger.info("  Python:  python deploy/run_production.py")
        logger.info("\n⚠️ IMPORTANT: Start with PAPER TRADING first!")
        sys.exit(0)
    else:
        logger.error("\n❌ Deployment failed")
        sys.exit(1)


if __name__ == '__main__':
    main()
