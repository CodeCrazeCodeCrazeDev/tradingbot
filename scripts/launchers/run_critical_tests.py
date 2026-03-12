"""
Critical Testing Suite Runner

Runs all critical tests:
- Integration tests
- Load tests
- Validation tests
- Production monitoring tests

Author: Trading Bot Team
Date: 2025-10-18
"""

import sys
import subprocess
import logging
from datetime import datetime
import json
from pathlib import Path

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def run_command(cmd, description):
    """Run command and capture output"""
    logger.info(f"\n{'='*80}")
    logger.info(f"Running: {description}")
    logger.info(f"{'='*80}")
    
    try:
        result = subprocess.run(
            cmd,
            shell=True,
            capture_output=True,
            text=True,
            timeout=300
        )
        
        if result.returncode == 0:
            logger.info(f"✅ {description} - PASSED")
            return True, result.stdout
        else:
            logger.error(f"❌ {description} - FAILED")
            logger.error(result.stderr)
            return False, result.stderr
            
    except subprocess.TimeoutExpired:
        logger.error(f"⏱️  {description} - TIMEOUT")
        return False, "Timeout after 5 minutes"
    except Exception as e:
        logger.error(f"❌ {description} - ERROR: {e}")
        return False, str(e)


def main():
    """Run all critical tests"""
    start_time = datetime.now()
    results = {}
    
    logger.info("\n" + "="*80)
    logger.info("CRITICAL TESTING SUITE")
    logger.info("="*80)
    logger.info(f"Start Time: {start_time.isoformat()}")
    
    # 1. Integration Tests
    logger.info("\n📋 Phase 1: Integration Tests")
    success, output = run_command(
        "py -m pytest tests/test_critical_integration.py -v --tb=short",
        "Integration Tests"
    )
    results['integration_tests'] = {'passed': success, 'output': output[:1000] if output else ''}
    
    # 2. Load Tests
    logger.info("\n📋 Phase 2: Load Tests")
    success, output = run_command(
        "py -m pytest tests/test_load_performance.py -v --tb=short -k 'not stress'",
        "Load Tests"
    )
    results['load_tests'] = {'passed': success, 'output': output[:1000] if output else ''}
    
    # 3. Validation Tests
    logger.info("\n📋 Phase 3: Validation Tests")
    success, output = run_command(
        "py trading_bot/validation/critical_validators.py",
        "Critical Validators"
    )
    results['validation_tests'] = {'passed': success, 'output': output[:1000] if output else ''}
    
    # 4. Monitor Test
    logger.info("\n📋 Phase 4: Monitor Test")
    success, output = run_command(
        "py trading_bot/monitoring/production_monitor.py",
        "Production Monitor"
    )
    results['monitoring_tests'] = {'passed': success, 'output': output[:1000] if output else ''}
    
    # Summary
    end_time = datetime.now()
    duration = (end_time - start_time).total_seconds()
    
    passed_count = sum(1 for r in results.values() if r['passed'])
    total_count = len(results)
    
    logger.info("\n" + "="*80)
    logger.info("TEST SUMMARY")
    logger.info("="*80)
    logger.info(f"Total Tests: {total_count}")
    logger.info(f"Passed: {passed_count}")
    logger.info(f"Failed: {total_count - passed_count}")
    logger.info(f"Duration: {duration:.2f} seconds")
    logger.info(f"Success Rate: {(passed_count/total_count)*100:.1f}%")
    
    # Save results
    report = {
        'timestamp': start_time.isoformat(),
        'duration_seconds': duration,
        'results': results,
        'summary': {
            'total': total_count,
            'passed': passed_count,
            'failed': total_count - passed_count,
            'success_rate': (passed_count/total_count)*100
        }
    }
    
    with open('critical_test_report.json', 'w') as f:
        json.dump(report, f, indent=2)
    
    logger.info(f"\n📄 Report saved to: critical_test_report.json")
    
    if passed_count == total_count:
        logger.info("\n✅ ALL TESTS PASSED")
        return 0
    else:
        logger.error("\n❌ SOME TESTS FAILED")
        return 1


if __name__ == '__main__':
    sys.exit(main())
