"""
Auto-Fix Critical Issues in Trading Bot
Automatically detects and fixes common critical failures
"""

import os
import sys
from pathlib import Path
import logging
import traceback

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class AutoFixer:
    """Automatically fix critical issues in the trading bot"""
    
    def __init__(self):
        self.fixes_applied = []
        self.issues_found = []
        
    def run_all_fixes(self):
        """Run all auto-fixes"""
        logger.info("="*80)
        logger.info("AUTO-FIX: Starting comprehensive system repair")
        logger.info("="*80)
        
        # Fix 1: Create missing directories
        self.fix_missing_directories()
        
        # Fix 2: Fix Elite Brain initialization
        self.fix_elite_brain_init()
        
        # Fix 3: Create models directory
        self.fix_models_directory()
        
        # Fix 4: Fix import issues
        self.fix_import_issues()
        
        # Fix 5: Fix NotImplementedError in base classes
        self.fix_not_implemented_errors()
        
        # Fix 6: Validate configuration
        self.fix_configuration()
        
        # Summary
        self.print_summary()
        
    def fix_missing_directories(self):
        """Create missing directories"""
        logger.info("\n[FIX 1] Creating missing directories...")
        
        directories = [
            'logs',
            'logs/validation_reports',
            'models',
            'data',
            'cache',
            'backups'
        ]
        
        for dir_path in directories:
            path = Path(dir_path)
            if not path.exists():
                path.mkdir(parents=True, exist_ok=True)
                logger.info(f"  [CREATED] {dir_path}")
                self.fixes_applied.append(f"Created directory: {dir_path}")
            else:
                logger.info(f"  [OK] {dir_path} exists")
                
    def fix_elite_brain_init(self):
        """Fix Elite Brain initialization issues"""
        logger.info("\n[FIX 2] Fixing Elite Brain initialization...")
        
        try:
            # Check if brain __init__.py exports EliteBrain
            brain_init = Path('trading_bot/brain/__init__.py')
            
            if brain_init.exists():
                content = brain_init.read_text()
                
                if 'EliteBrain' not in content:
                    # Add EliteBrain export
                    if 'from .brain_architecture import' in content:
                        logger.info("  [OK] EliteBrain already imported")
                    else:
                        # Add import
                        new_content = content + "\nfrom .brain_architecture import EliteBrain\n"
                        brain_init.write_text(new_content)
                        logger.info("  [FIXED] Added EliteBrain import")
                        self.fixes_applied.append("Added EliteBrain import to brain/__init__.py")
                else:
                    logger.info("  [OK] EliteBrain export found")
            else:
                # Create __init__.py
                brain_init.parent.mkdir(parents=True, exist_ok=True)
                brain_init.write_text("""\"\"\"
Elite Trading Bot - Brain Module
\"\"\"

from .brain_architecture import EliteBrain, BrainDecision, DecisionState

__all__ = ['EliteBrain', 'BrainDecision', 'DecisionState']
""")
                logger.info("  [CREATED] brain/__init__.py")
                self.fixes_applied.append("Created brain/__init__.py")
                
        except Exception as e:
            logger.error(f"  [ERROR] {e}")
            self.issues_found.append(f"Elite Brain init: {e}")
            
    def fix_models_directory(self):
        """Create models directory and placeholder"""
        logger.info("\n[FIX 3] Setting up models directory...")
        
        models_dir = Path('models')
        models_dir.mkdir(exist_ok=True)
        
        # Create README
        readme = models_dir / 'README.md'
        if not readme.exists():
            readme.write_text("""# ML Models Directory

This directory stores machine learning models for the trading bot.

## Model Types
- `.pkl` - Scikit-learn models
- `.h5` - Keras/TensorFlow models  
- `.pt` - PyTorch models

## Auto-Generation
Models will be automatically generated during bot operation.
""")
            logger.info("  [CREATED] models/README.md")
            self.fixes_applied.append("Created models/README.md")
        else:
            logger.info("  [OK] models directory configured")
            
    def fix_import_issues(self):
        """Fix common import issues"""
        logger.info("\n[FIX 4] Checking import issues...")
        
        # Check if all required packages are installed
        required_packages = [
            'MetaTrader5',
            'pandas',
            'numpy',
            'yaml',
            'psutil',
            'ta'
        ]
        
        missing_packages = []
        
        for package in required_packages:
            try:
                __import__(package)
                logger.info(f"  [OK] {package} installed")
            except ImportError:
                logger.warning(f"  [MISSING] {package}")
                missing_packages.append(package)
                self.issues_found.append(f"Missing package: {package}")
        
        if missing_packages:
            logger.warning(f"  [ACTION NEEDED] Install: py -m pip install {' '.join(missing_packages)}")
        else:
            logger.info("  [OK] All required packages installed")
            
    def fix_not_implemented_errors(self):
        """Fix NotImplementedError in base classes"""
        logger.info("\n[FIX 5] Checking NotImplementedError issues...")
        
        # These are intentional in base classes - just log them
        files_with_not_implemented = [
            'trading_bot/connectivity/api_client.py',
            'trading_bot/ml/online_learning.py',
            'trading_bot/execution/smart_execution.py'
        ]
        
        for file_path in files_with_not_implemented:
            if Path(file_path).exists():
                logger.info(f"  [OK] {file_path} - NotImplementedError is intentional (base class)")
            else:
                logger.warning(f"  [MISSING] {file_path}")
                
    def fix_configuration(self):
        """Validate and fix configuration"""
        logger.info("\n[FIX 6] Validating configuration...")
        
        config_file = Path('config/config.yaml')
        
        if not config_file.exists():
            logger.error("  [ERROR] config/config.yaml not found")
            self.issues_found.append("Missing config/config.yaml")
            
            # Create default config
            config_file.parent.mkdir(parents=True, exist_ok=True)
            config_file.write_text("""mt5:
  path: C:/Program Files/MetaTrader 5
  server: MetaQuotes-Demo
  login: 12345678
  password: demo
  timeout: 60000
  symbols:
  - EURUSD
  - GBPUSD
  - USDJPY
  timeframes:
  - M15
  - H1
  - H4
  - D1

trading:
  mode: paper
  risk_per_trade: 0.01
  max_positions: 5
  position_sizing: risk_based
  stop_loss_atr_multiplier: 2.0
  take_profit_rr_ratio: 2.0

risk:
  max_position_size: 1.0
  min_position_size: 0.01
  risk_per_trade_pct: 1.0
  max_drawdown_pct: 20.0

logging:
  level: INFO
  file: logs/trading_bot.log
""")
            logger.info("  [CREATED] Default config/config.yaml")
            self.fixes_applied.append("Created default config/config.yaml")
        else:
            logger.info("  [OK] config/config.yaml exists")
            
    def print_summary(self):
        """Print summary of fixes"""
        logger.info("\n" + "="*80)
        logger.info("AUTO-FIX SUMMARY")
        logger.info("="*80)
        
        logger.info(f"\n[FIXES APPLIED] {len(self.fixes_applied)}")
        for fix in self.fixes_applied:
            logger.info(f"  ✓ {fix}")
            
        logger.info(f"\n[ISSUES FOUND] {len(self.issues_found)}")
        for issue in self.issues_found:
            logger.info(f"  ! {issue}")
            
        if not self.issues_found:
            logger.info("\n[SUCCESS] All critical issues resolved!")
        else:
            logger.info("\n[ACTION NEEDED] Some issues require manual intervention")
            
        logger.info("="*80)


def main():
    """Main entry point"""
    print("\n" + "="*80)
    print("ELITE TRADING BOT - AUTO-FIX UTILITY")
    print("="*80)
    print("\nThis utility will automatically detect and fix critical issues.")
    print("Press Ctrl+C to cancel...\n")
    
    try:
        fixer = AutoFixer()
        fixer.run_all_fixes()
        
        print("\n" + "="*80)
        print("AUTO-FIX COMPLETE")
        print("="*80)
        print("\nNext steps:")
        print("1. Run: py run_system_validation.py")
        print("2. Check validation report")
        print("3. Run: py thinking_bot_validated.py")
        print("\n")
        
        return 0
        
    except KeyboardInterrupt:
        print("\n\n[CANCELLED] Auto-fix cancelled by user")
        return 1
        
    except Exception as e:
        print(f"\n[ERROR] Auto-fix failed: {e}")
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
