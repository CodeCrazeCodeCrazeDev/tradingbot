"""
Test runner for AlphaAlgo 2.0
"""

import unittest
import sys
import os
import logging
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(f'test_run_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log'),
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)


def run_tests():
    """Run all test suites."""
    # Start time
    start_time = datetime.now()
    logger.info("="*80)
    logger.info("🧪 Starting AlphaAlgo 2.0 Tests")
    logger.info("="*80)
    
    # Discover and run tests
    loader = unittest.TestLoader()
    start_dir = os.path.dirname(os.path.abspath(__file__))
    suite = loader.discover(start_dir, pattern="test_*.py")
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # End time
    end_time = datetime.now()
    duration = end_time - start_time
    
    # Log results
    logger.info("\n" + "="*80)
    logger.info("📊 Test Results:")
    logger.info(f"Tests Run: {result.testsRun}")
    logger.info(f"Successful: {result.testsRun - len(result.failures) - len(result.errors)}")
    logger.info(f"Failures: {len(result.failures)}")
    logger.info(f"Errors: {len(result.errors)}")
    logger.info(f"Duration: {duration.total_seconds():.2f} seconds")
    logger.info("="*80)
    
    # Log failures and errors
    if result.failures:
        logger.error("\n❌ Failures:")
        for failure in result.failures:
            logger.error(f"\n{failure[0]}")
            logger.error(f"{failure[1]}")
    
    if result.errors:
        logger.error("\n❌ Errors:")
        for error in result.errors:
            logger.error(f"\n{error[0]}")
            logger.error(f"{error[1]}")
    
    # Return success status
    return len(result.failures) == 0 and len(result.errors) == 0


if __name__ == '__main__':
    success = run_tests()
    sys.exit(0 if success else 1)
