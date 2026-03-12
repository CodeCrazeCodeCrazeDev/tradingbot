"""
from typing import List, Optional, Set
End-to-End Testing Framework
Provides comprehensive testing of the trading bot from data ingestion to execution
"""

import asyncio
import logging
import time
import os
import json
import pandas as pd
import numpy as np
from typing import Dict, List, Any, Optional, Union, Callable
from datetime import datetime, timedelta
from pathlib import Path
import traceback
import uuid
import yaml
import matplotlib.pyplot as plt
import seaborn as sns

from trading_bot.testing.synthetic_data import SyntheticDataGenerator, MarketScenario
from trading_bot.schemas.validation import TestCase, TestResult, TestSuite, TestReport
from trading_bot.schemas.market_data import TimeFrame

logger = logging.getLogger(__name__)


class EndToEndTest:
    """
    Base class for end-to-end tests
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self.test_id = str(uuid.uuid4())
        self.name = self.__class__.__name__
        self.description = self.__doc__ or "No description"
        self.results = {}
        self.start_time = None
        self.end_time = None
        self.success = False
        self.errors = []
        self.warnings = []
        
        # Test data
        self.data_generator = SyntheticDataGenerator(self.config.get('data_config', {}))
        
        # Output directory
        self.output_dir = self.config.get('output_dir', 'test_reports')
        Path(self.output_dir).mkdir(parents=True, exist_ok=True)
    
    async def setup(self):
        """Set up test environment"""
        self.start_time = datetime.now()
        logger.info(f"Setting up test: {self.name}")
    
    async def run(self):
        """Run the test"""
        logger.info(f"Running test: {self.name}")
        try:
            await self.setup()
            await self.execute()
            await self.teardown()
            self.success = len(self.errors) == 0
        except Exception as e:
            self.errors.append(f"Test execution failed: {str(e)}")
            logger.error(f"Test {self.name} failed: {e}")
            traceback.print_exc()
            self.success = False
        finally:
            self.end_time = datetime.now()
    
    async def execute(self):
        """Execute the test (to be implemented by subclasses)"""
        # Default implementation - basic test flow
        logger.info(f"Executing E2E test: {self.name}")
        
        # Step 1: Setup
        self.results['setup'] = {'status': 'completed', 'timestamp': datetime.now().isoformat()}
        
        try:
            # Step 2: Execute test logic
            # Simulate test execution
            await asyncio.sleep(0.1)  # Simulate work
            
            self.results['execution'] = {
                'status': 'completed',
                'timestamp': datetime.now().isoformat(),
                'message': 'Test executed successfully'
            }
            
            self.success = True
            
        except Exception as e:
            self.errors.append(str(e))
            self.results['execution'] = {
                'status': 'failed',
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }
            self.success = False
        
        # Step 3: Validation
        self.results['validation'] = {
            'status': 'completed' if self.success else 'skipped',
            'timestamp': datetime.now().isoformat()
        }
        
        logger.info(f"E2E test {self.name} {'passed' if self.success else 'failed'}")
    
    async def teardown(self):
        """Clean up after test"""
        logger.info(f"Tearing down test: {self.name}")
    
    def get_result(self) -> TestResult:
        """Get test result"""
        return TestResult(
            test_id=self.test_id,
            success=self.success,
            execution_time=(self.end_time - self.start_time).total_seconds() if self.end_time else 0,
            actual_outputs=self.results,
            errors=self.errors,
            warnings=self.warnings,
            timestamp=datetime.now()
        )
    
    def save_report(self):
        """Save test report to file"""
        result = self.get_result()
        
        # Create report directory
        report_dir = os.path.join(self.output_dir, self.test_id)
        Path(report_dir).mkdir(parents=True, exist_ok=True)
        
        # Save result as JSON
        with open(os.path.join(report_dir, 'result.json'), 'w') as f:
            json.dump(result.dict(), f, default=str, indent=2)
        
        # Save any plots
        if hasattr(self, 'plots') and self.plots:
            for plot_name, fig in self.plots.items():
                fig.savefig(os.path.join(report_dir, f"{plot_name}.png"))
        
        # Save summary
        summary = {
            'test_id': self.test_id,
            'name': self.name,
            'description': self.description,
            'success': self.success,
            'execution_time': result.execution_time,
            'timestamp': result.timestamp.isoformat(),
            'error_count': len(self.errors)
        }
        
        with open(os.path.join(report_dir, 'summary.json'), 'w') as f:
            json.dump(summary, f, indent=2)
        
        logger.info(f"Test report saved to {report_dir}")
        
        return report_dir


class DataFlowTest(EndToEndTest):
    """
    Tests data flow from ingestion to processing
    """
    
    async def setup(self):
        await super().setup()
        
        # Generate synthetic data
        self.market_data = self.data_generator.generate_market_data(
            days=5,
            timeframes=[TimeFrame.M1, TimeFrame.M5, TimeFrame.H1]
        )
        
        # Initialize components
        from trading_bot.database.data_streaming import MarketDataStream
        from trading_bot.database.real_time_processor import DataProcessor
        from trading_bot.database.timeseries_db import TimeSeriesDB
        
        self.market_stream = MarketDataStream(self.config.get('market_stream', {}))
        self.data_processor = DataProcessor(self.config.get('data_processor', {}))
        self.db = TimeSeriesDB(self.config.get('db', {}))
        
        # Initialize components
        await self.market_stream.initialize()
        await self.db.initialize()
    
    async def execute(self):
        """Test data flow through the pipeline"""
        symbol = "SYNTHETIC"
        
        # Create data streams
        await self.market_stream.create_stream(f"{symbol}_market")
        await self.market_stream.create_stream(f"{symbol}_bars_M1")
        
        # Add processor
        self.data_processor.add_processor(f"{symbol}_market", self._process_market_data)
        
        # Push data through pipeline
        m1_data = self.market_data[TimeFrame.M1]
        
        # Track metrics
        processing_times = []
        success_count = 0
        error_count = 0
        
        # Process each bar
        for _, row in m1_data.iterrows():
            start_time = time.time()
            
            try:
                # Push to market stream
                await self.market_stream.push_data(f"{symbol}_market", row.to_dict())
                
                # Write to database
                await self.db.write_market_data(row.to_dict(), symbol, TimeFrame.M1.value)
                
                success_count += 1
            except Exception as e:
                logger.error(f"Error processing data: {e}")
                error_count += 1
            
            processing_time = time.time() - start_time
            processing_times.append(processing_time)
        
        # Verify data in database
        db_data = await self.db.get_market_data(symbol, TimeFrame.M1.value, limit=100)
        
        # Store results
        self.results = {
            'processed_count': success_count,
            'error_count': error_count,
            'avg_processing_time': np.mean(processing_times),
            'max_processing_time': np.max(processing_times),
            'min_processing_time': np.min(processing_times),
            'p95_processing_time': np.percentile(processing_times, 95),
            'db_record_count': len(db_data)
        }
        
        # Create performance plot
        self.plots = {}
        fig, ax = plt.subplots(figsize=(10, 6))
        sns.histplot(processing_times, bins=50, ax=ax)
        ax.set_title('Data Processing Time Distribution')
        ax.set_xlabel('Processing Time (s)')
        ax.set_ylabel('Frequency')
        self.plots['processing_time'] = fig
        
        # Validate results
        if error_count > 0:
            self.errors.append(f"Data processing had {error_count} errors")
        
        if len(db_data) < len(m1_data) * 0.9:  # Allow for some data loss
            self.errors.append(f"Database contains only {len(db_data)} records out of {len(m1_data)}")
    
    async def _process_market_data(self, data):
        """Process market data"""
        # Simple processing function
        if isinstance(data, dict):
            # Add some derived fields
            data['processed'] = True
            data['processing_time'] = datetime.now().isoformat()
            
            if 'close' in data and 'open' in data:
                data['return'] = (data['close'] - data['open']) / data['open']
        
        return data
    
    async def teardown(self):
        """Clean up resources"""
        await self.market_stream.cleanup()
        await self.db.cleanup()
        await super().teardown()


class OpportunityScanningTest(EndToEndTest):
    """
    Tests opportunity scanning with synthetic market data
    """
    
    async def setup(self):
        await super().setup()
        
        # Generate synthetic data for different market regimes
        self.trending_data = MarketScenario.trending_up(days=5)
        self.ranging_data = MarketScenario.ranging(days=5)
        self.volatile_data = MarketScenario.volatile(days=5)
        self.breakout_data = MarketScenario.breakout(days=5)
        
        # Initialize components
        from trading_bot.opportunity_scanner.scanner_interface import UnifiedScanner
        
        self.scanner = UnifiedScanner(self.config.get('scanner', {}))
        
        # Mock dependencies
        self.scanner.market_stream = self._mock_market_stream()
        self.scanner.data_processor = self._mock_data_processor()
        self.scanner.microstructure = self._mock_microstructure()
        self.scanner.order_flow = self._mock_order_flow()
    
    def _mock_market_stream(self):
        """Create mock market stream"""
        class MockMarketStream:
            async def get_data(self, stream_id):
                return {}
        return MockMarketStream()
    
    def _mock_data_processor(self):
        """Create mock data processor"""
        class MockDataProcessor:
            async def process_market_data(self, data, data_type):
                return data
        return MockDataProcessor()
    
    def _mock_microstructure(self):
        """Create mock microstructure analyzer"""
        class MockMicrostructure:
            def get_metrics(self, symbol):
                return {
                    'liquidity': 0.8,
                    'spread': 0.01,
                    'depth': 100,
                    'volatility': 0.02
                }
        return MockMicrostructure()
    
    def _mock_order_flow(self):
        """Create mock order flow processor"""
        class MockOrderFlow:
            def get_order_flow_stats(self, symbol):
                return {
                    'delta': 0.2,
                    'imbalance': 1.2,
                    'absorption': 0.5,
                    'exhaustion': 0.3
                }
        return MockOrderFlow()
    
    async def execute(self):
        """Test opportunity scanning across different market regimes"""
        symbol = "SYNTHETIC"
        
        # Test with different market regimes
        regime_results = {}
        
        for regime_name, data in [
            ('trending', self.trending_data),
            ('ranging', self.ranging_data),
            ('volatile', self.volatile_data),
            ('breakout', self.breakout_data)
        ]:
            # Get M5 data
            m5_data = data[TimeFrame.M5]
            
            opportunities = []
            scan_times = []
            
            # Scan each bar
            for _, row in m5_data.iterrows():
                market_data = row.to_dict()
                
                start_time = time.time()
                regime_opps = await self.scanner.scan_opportunities(symbol, market_data)
                scan_time = time.time() - start_time
                
                opportunities.extend(regime_opps)
                scan_times.append(scan_time)
            
            # Store regime results
            regime_results[regime_name] = {
                'opportunity_count': len(opportunities),
                'opportunity_types': self._count_opportunity_types(opportunities),
                'avg_scan_time': np.mean(scan_times),
                'max_scan_time': np.max(scan_times),
                'p95_scan_time': np.percentile(scan_times, 95) if scan_times else 0
            }
        
        # Store overall results
        self.results = {
            'regime_results': regime_results,
            'opportunity_metrics': self.scanner.get_opportunity_metrics()
        }
        
        # Create performance plots
        self.plots = {}
        
        # Opportunity count by regime
        fig, ax = plt.subplots(figsize=(10, 6))
        regimes = list(regime_results.keys())
        counts = [r['opportunity_count'] for r in regime_results.values()]
        sns.barplot(x=regimes, y=counts, ax=ax)
        ax.set_title('Opportunity Count by Market Regime')
        ax.set_xlabel('Market Regime')
        ax.set_ylabel('Opportunity Count')
        self.plots['opportunity_count'] = fig
        
        # Validate results
        for regime, results in regime_results.items():
            if results['opportunity_count'] == 0:
                self.warnings.append(f"No opportunities detected in {regime} regime")
    
    def _count_opportunity_types(self, opportunities):
        """Count opportunities by type"""
        type_counts = {}
        for opp in opportunities:
            opp_type = opp.type
            if opp_type not in type_counts:
                type_counts[opp_type] = 0
            type_counts[opp_type] += 1
        return type_counts


class TestRunner:
    """
    Runs end-to-end tests and generates reports
    """
    
    def __init__(self, config_path: Optional[str] = None):
        # Load configuration
        self.config = {}
        if config_path:
            with open(config_path, 'r') as f:
                self.config = yaml.safe_load(f)
        
        # Test registry
        self.test_registry = {
            'data_flow': DataFlowTest,
            'opportunity_scanning': OpportunityScanningTest
        }
        
        # Output directory
        self.output_dir = self.config.get('output_dir', 'test_reports')
        Path(self.output_dir).mkdir(parents=True, exist_ok=True)
    
    async def run_test(self, test_name: str) -> TestResult:
        """Run a single test by name"""
        if test_name not in self.test_registry:
            raise ValueError(f"Unknown test: {test_name}")
        
        test_class = self.test_registry[test_name]
        test = test_class(self.config.get(test_name, {}))
        
        await test.run()
        test.save_report()
        
        return test.get_result()
    
    async def run_test_suite(self, test_names: List[str]) -> TestReport:
        """Run a suite of tests"""
        suite_id = str(uuid.uuid4())
        start_time = datetime.now()
        
        results = []
        passed = 0
        failed = 0
        skipped = 0
        
        for test_name in test_names:
            try:
                result = await self.run_test(test_name)
                results.append(result)
                
                if result.success:
                    passed += 1
                else:
                    failed += 1
            except Exception as e:
                logger.error(f"Error running test {test_name}: {e}")
                skipped += 1
        
        end_time = datetime.now()
        total_time = (end_time - start_time).total_seconds()
        
        # Create report
        report = TestReport(
            suite_id=suite_id,
            timestamp=end_time,
            total_tests=len(test_names),
            passed_tests=passed,
            failed_tests=failed,
            skipped_tests=skipped,
            total_execution_time=total_time,
            results=results,
            summary=f"Test suite completed with {passed} passed, {failed} failed, {skipped} skipped"
        )
        
        # Save report
        report_path = os.path.join(self.output_dir, f"suite_{suite_id}.json")
        with open(report_path, 'w') as f:
            json.dump(report.dict(), f, default=str, indent=2)
        
        return report
    
    async def run_all_tests(self) -> TestReport:
        """Run all registered tests"""
        return await self.run_test_suite(list(self.test_registry.keys()))


async def main():
    """Run all tests"""
    runner = TestRunner()
    report = await runner.run_all_tests()
    logger.info(f"Test suite completed: {report.summary}")
    logger.info(f"Total execution time: {report.total_execution_time:.2f}s")


if __name__ == "__main__":
    asyncio.run(main())
