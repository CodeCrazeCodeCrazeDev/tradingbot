"""
Code Quality Runner
Runs all code quality tools: black, isort, autoflake, pylint
"""

import subprocess
import sys
import logging
from pathlib import Path

logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger(__name__)


def run_command(cmd: list, description: str) -> bool:
    """Run a command and return success status"""
    logger.info(f"\n{'='*60}")
    logger.info(f"Running: {description}")
    logger.info(f"Command: {' '.join(cmd)}")
    logger.info(f"{'='*60}\n")
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.stdout:
            print(result.stdout)
        
        if result.stderr:
            print(result.stderr, file=sys.stderr)
        
        if result.returncode == 0:
            logger.info(f"✅ {description} completed successfully")
            return True
        else:
            logger.error(f"❌ {description} failed with code {result.returncode}")
            return False
    
    except FileNotFoundError:
        logger.error(f"❌ Command not found. Please install: pip install {cmd[0]}")
        return False
    except Exception as e:
        logger.error(f"❌ Error running {description}: {e}")
        return False


def main():
    """Run all code quality tools"""
    root_dir = Path(__file__).parent.parent
    trading_bot_dir = root_dir / "trading_bot"
    tests_dir = root_dir / "tests"
    
    results = {}
    
    # 1. Remove unused imports with autoflake
    logger.info("\n" + "="*60)
    logger.info("STEP 1: Removing unused imports")
    logger.info("="*60)
    
    results['autoflake'] = run_command([
        'autoflake',
        '--in-place',
        '--remove-all-unused-imports',
        '--remove-unused-variables',
        '--recursive',
        str(trading_bot_dir)
    ], "Remove unused imports (autoflake)")
    
    # 2. Sort imports with isort
    logger.info("\n" + "="*60)
    logger.info("STEP 2: Sorting imports")
    logger.info("="*60)
    
    results['isort'] = run_command([
        'isort',
        str(trading_bot_dir),
        str(tests_dir),
        '--profile', 'black',
        '--line-length', '120'
    ], "Sort imports (isort)")
    
    # 3. Format code with black
    logger.info("\n" + "="*60)
    logger.info("STEP 3: Formatting code")
    logger.info("="*60)
    
    results['black'] = run_command([
        'black',
        str(trading_bot_dir),
        str(tests_dir),
        '--line-length', '120'
    ], "Format code (black)")
    
    # 4. Run pylint for code quality
    logger.info("\n" + "="*60)
    logger.info("STEP 4: Running pylint")
    logger.info("="*60)
    
    results['pylint'] = run_command([
        'pylint',
        str(trading_bot_dir),
        '--max-line-length=120',
        '--disable=C0111,C0103,R0913,R0914,R0915',
        '--output-format=colorized'
    ], "Code quality check (pylint)")
    
    # 5. Run flake8
    logger.info("\n" + "="*60)
    logger.info("STEP 5: Running flake8")
    logger.info("="*60)
    
    results['flake8'] = run_command([
        'flake8',
        str(trading_bot_dir),
        '--max-line-length=120',
        '--ignore=E203,W503,E501',
        '--statistics'
    ], "Style check (flake8)")
    
    # Summary
    logger.info("\n" + "="*60)
    logger.info("CODE QUALITY SUMMARY")
    logger.info("="*60)
    
    for tool, success in results.items():
        status = "✅ PASS" if success else "❌ FAIL"
        logger.info(f"{tool:15} {status}")
    
    total = len(results)
    passed = sum(results.values())
    
    logger.info(f"\nTotal: {passed}/{total} passed ({passed/total*100:.0f}%)")
    
    if passed == total:
        logger.info("\n🎉 All code quality checks passed!")
        return 0
    else:
        logger.warning(f"\n⚠️  {total - passed} checks failed")
        return 1


if __name__ == '__main__':
    sys.exit(main())
