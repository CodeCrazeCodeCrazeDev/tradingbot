"""
Parallel Opportunity Scanner
Implements parallel processing for opportunity scanning to maximize throughput
"""

import asyncio
import concurrent.futures
import multiprocessing
import logging
import time
from typing import Any, Callable, Dict, List, Optional, Union
from datetime import datetime
import numpy as np
import traceback
import functools

from trading_bot.opportunity_scanner.scanner_interface import UnifiedScanner, OpportunityData
from trading_bot.monitoring.performance_tracker import get_performance_tracker
from trading_bot.monitoring.latency_budget import get_latency_budget_tracker
import numpy

logger = logging.getLogger(__name__)


class ParallelScanner:
    """
    Enhanced scanner with parallel processing capabilities
    Features:
    - Multi-process scanning for CPU-intensive operations
    - Asynchronous scanning for I/O-bound operations
    - Dynamic resource allocation
    - Performance monitoring
    - Latency budget enforcement
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        
        # Base scanner
        self.scanner = UnifiedScanner(self.config)
        
        # Process pool for CPU-intensive operations
        self.max_workers = self.config.get('max_workers', multiprocessing.cpu_count())
        self.process_pool = concurrent.futures.ProcessPoolExecutor(
            max_workers=self.max_workers
        )
        
        # Thread pool for I/O-bound operations
        self.thread_pool = concurrent.futures.ThreadPoolExecutor(
            max_workers=self.max_workers * 2
        )
        
        # Performance tracking
        self.performance_tracker = get_performance_tracker()
        self.latency_tracker = get_latency_budget_tracker()
        
        # Scanner registry
        self.scanners = {}
        self.scanner_configs = {}
        
        # Scan strategy
        self.parallel_strategy = self.config.get('parallel_strategy', 'adaptive')
        
        logger.info(f"Parallel scanner initialized with {self.max_workers} workers")
    
    async def initialize(self, *args, **kwargs):
        """Initialize the base scanner and all registered scanners"""
        await self.scanner.initialize(*args, **kwargs)
        
        # Initialize registered scanners
        for scanner_name, scanner in self.scanners.items():
            try:
                await scanner.initialize(*args, **kwargs)
                logger.info(f"Initialized scanner: {scanner_name}")
            except Exception as e:
                logger.error(f"Failed to initialize scanner {scanner_name}: {e}")
                traceback.print_exc()
    
    def register_scanner(self, name: str, scanner: Any, config: Optional[Dict[str, Any]] = None):
        """Register a scanner for parallel execution"""
        self.scanners[name] = scanner
        self.scanner_configs[name] = config or {}
        logger.info(f"Registered scanner: {name}")
    
    @functools.lru_cache(maxsize=100)
    def _get_scanner_type(self, scanner_name: str) -> str:
        """Determine if a scanner is CPU-bound or I/O-bound"""
        config = self.scanner_configs.get(scanner_name, {})
        return config.get('type', 'cpu')  # Default to CPU-bound
    
    async def scan_opportunities(self, symbol: str, market_data: Dict[str, Any]) -> List[OpportunityData]:
        """
        Scan for opportunities using parallel processing
        
        Args:
            symbol: Symbol to scan
            market_data: Market data for scanning
            
        Returns:
            List of opportunities
        """
        # Start latency tracking
        trace_id = self.latency_tracker.start_trace('opportunity_scanning')
        
        try:
            # Choose scanning strategy
            if self.parallel_strategy == 'process_pool':
                opportunities = await self._scan_with_process_pool(symbol, market_data)
            elif self.parallel_strategy == 'thread_pool':
                opportunities = await self._scan_with_thread_pool(symbol, market_data)
            elif self.parallel_strategy == 'asyncio':
                opportunities = await self._scan_with_asyncio(symbol, market_data)
            else:  # adaptive
                opportunities = await self._scan_adaptive(symbol, market_data)
            
            # Filter and prioritize opportunities
            filtered_opps = self._filter_opportunities(opportunities)
            
            return filtered_opps
            
        except Exception as e:
            logger.error(f"Error in parallel scanning: {e}")
            traceback.print_exc()
            return []
            
        finally:
            # End latency tracking
            self.latency_tracker.end_trace(trace_id)
    
    async def _scan_with_process_pool(self, symbol: str, market_data: Dict[str, Any]) -> List[OpportunityData]:
        """Scan using process pool for maximum CPU utilization"""
        loop = asyncio.get_event_loop()
        
        # Prepare scan tasks
        scan_tasks = []
        
        for scanner_name, scanner in self.scanners.items():
            scan_tasks.append(
                loop.run_in_executor(
                    self.process_pool,
                    self._run_scanner_in_process,
                    scanner_name,
                    scanner,
                    symbol,
                    market_data
                )
            )
        
        # Execute all tasks in parallel
        results = await asyncio.gather(*scan_tasks, return_exceptions=True)
        
        # Process results
        opportunities = []
        
        for result in results:
            if isinstance(result, Exception):
                logger.error(f"Scanner error: {result}")
                continue
                
            opportunities.extend(result)
        
        return opportunities
    
    def _run_scanner_in_process(self, scanner_name: str, scanner: Any, symbol: str, market_data: Dict[str, Any]) -> List[OpportunityData]:
        """Run a scanner in a separate process"""
        try:
            # Create a new event loop for the process
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            # Run the scanner
            result = loop.run_until_complete(scanner.scan_opportunities(symbol, market_data))
            
            # Clean up
            loop.close()
            
            return result
        except Exception as e:
            logger.error(f"Error in scanner {scanner_name}: {e}")
            return []
    
    async def _scan_with_thread_pool(self, symbol: str, market_data: Dict[str, Any]) -> List[OpportunityData]:
        """Scan using thread pool for I/O-bound scanners"""
        loop = asyncio.get_event_loop()
        
        # Prepare scan tasks
        scan_tasks = []
        
        for scanner_name, scanner in self.scanners.items():
            scan_tasks.append(
                loop.run_in_executor(
                    self.thread_pool,
                    self._run_scanner_in_thread,
                    scanner_name,
                    scanner,
                    symbol,
                    market_data
                )
            )
        
        # Execute all tasks in parallel
        results = await asyncio.gather(*scan_tasks, return_exceptions=True)
        
        # Process results
        opportunities = []
        
        for result in results:
            if isinstance(result, Exception):
                logger.error(f"Scanner error: {result}")
                continue
                
            opportunities.extend(result)
        
        return opportunities
    
    def _run_scanner_in_thread(self, scanner_name: str, scanner: Any, symbol: str, market_data: Dict[str, Any]) -> List[OpportunityData]:
        """Run a scanner in a separate thread"""
        try:
            # Create a new event loop for the thread
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            # Run the scanner
            result = loop.run_until_complete(scanner.scan_opportunities(symbol, market_data))
            
            # Clean up
            loop.close()
            
            return result
        except Exception as e:
            logger.error(f"Error in scanner {scanner_name}: {e}")
            return []
    
    async def _scan_with_asyncio(self, symbol: str, market_data: Dict[str, Any]) -> List[OpportunityData]:
        """Scan using asyncio for concurrent execution"""
        # Prepare scan tasks
        scan_tasks = []
        
        for scanner_name, scanner in self.scanners.items():
            scan_tasks.append(scanner.scan_opportunities(symbol, market_data))
        
        # Execute all tasks concurrently
        results = await asyncio.gather(*scan_tasks, return_exceptions=True)
        
        # Process results
        opportunities = []
        
        for result in results:
            if isinstance(result, Exception):
                logger.error(f"Scanner error: {result}")
                continue
                
            opportunities.extend(result)
        
        return opportunities
    
    async def _scan_adaptive(self, symbol: str, market_data: Dict[str, Any]) -> List[OpportunityData]:
        """
        Adaptive scanning strategy based on scanner type
        - CPU-bound scanners run in process pool
        - I/O-bound scanners run in thread pool
        - Default scanners run with asyncio
        """
        # Group scanners by type
        cpu_scanners = {}
        io_scanners = {}
        default_scanners = {}
        
        for name, scanner in self.scanners.items():
            scanner_type = self._get_scanner_type(name)
            
            if scanner_type == 'cpu':
                cpu_scanners[name] = scanner
            elif scanner_type == 'io':
                io_scanners[name] = scanner
            else:
                default_scanners[name] = scanner
        
        # Prepare scan tasks
        loop = asyncio.get_event_loop()
        scan_tasks = []
        
        # CPU-bound scanners in process pool
        for name, scanner in cpu_scanners.items():
            scan_tasks.append(
                loop.run_in_executor(
                    self.process_pool,
                    self._run_scanner_in_process,
                    name,
                    scanner,
                    symbol,
                    market_data
                )
            )
        
        # I/O-bound scanners in thread pool
        for name, scanner in io_scanners.items():
            scan_tasks.append(
                loop.run_in_executor(
                    self.thread_pool,
                    self._run_scanner_in_thread,
                    name,
                    scanner,
                    symbol,
                    market_data
                )
            )
        
        # Default scanners with asyncio
        for name, scanner in default_scanners.items():
            scan_tasks.append(scanner.scan_opportunities(symbol, market_data))
        
        # Execute all tasks
        results = await asyncio.gather(*scan_tasks, return_exceptions=True)
        
        # Process results
        opportunities = []
        
        for result in results:
            if isinstance(result, Exception):
                logger.error(f"Scanner error: {result}")
                continue
                
            opportunities.extend(result)
        
        return opportunities
    
    def _filter_opportunities(self, opportunities: List[OpportunityData]) -> List[OpportunityData]:
        """Filter and prioritize opportunities"""
        if not opportunities:
            return []
        
        # Filter by confidence
        min_confidence = self.config.get('min_confidence', 0.7)
        filtered = [opp for opp in opportunities if opp.confidence >= min_confidence]
        
        # Filter by risk score
        max_risk = self.config.get('max_risk', 0.7)
        filtered = [opp for opp in filtered if opp.risk_score <= max_risk]
        
        # Sort by expected return / risk (Sharpe-like ratio)
        filtered.sort(
            key=lambda x: x.expected_return / max(x.risk_score, 0.01),
            reverse=True
        )
        
        # Limit number of opportunities
        max_opps = self.config.get('max_opportunities', 5)
        return filtered[:max_opps]
    
    def get_opportunity_metrics(self) -> Dict[str, Any]:
        """Get opportunity scanning metrics"""
        # Get metrics from base scanner
        base_metrics = self.scanner.get_opportunity_metrics()
        
        # Get metrics from registered scanners
        scanner_metrics = {}
        
        for name, scanner in self.scanners.items():
            try:
                scanner_metrics[name] = scanner.get_opportunity_metrics()
            except Exception as e:
                logger.error(f"Error getting metrics from scanner {name}: {e}")
                scanner_metrics[name] = {"error": str(e)}
        
        # Get latency metrics
        latency_metrics = self.latency_tracker.get_metrics().get('opportunity_scanning', {})
        
        return {
            'base': base_metrics,
            'scanners': scanner_metrics,
            'latency': latency_metrics,
            'parallel_strategy': self.parallel_strategy,
            'max_workers': self.max_workers
        }
    
    async def cleanup(self):
        """Clean up resources"""
        # Clean up base scanner
        await self.scanner.cleanup()
        
        # Clean up registered scanners
        for name, scanner in self.scanners.items():
            try:
                await scanner.cleanup()
            except Exception as e:
                logger.error(f"Error cleaning up scanner {name}: {e}")
        
        # Shut down process pool
        self.process_pool.shutdown()
        
        # Shut down thread pool
        self.thread_pool.shutdown()
        
        logger.info("Parallel scanner cleaned up")
