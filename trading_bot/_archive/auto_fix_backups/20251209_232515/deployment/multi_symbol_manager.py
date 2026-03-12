import logging
"""
Multi-symbol deployment and portfolio management.
Handles parallel trading across multiple instruments with load balancing.
"""

import asyncio
import numpy as np
from typing import Dict, List, Optional
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor
from loguru import logger


class MultiSymbolManager:
    """Manage trading across multiple symbols with load balancing."""
    
    def __init__(self, symbols: List[str], max_workers: int = 5):
        """
        Initialize multi-symbol manager.
        
        Args:
            symbols: List of trading symbols
            max_workers: Maximum parallel workers
        """
        self.symbols = symbols
        self.max_workers = max_workers
        self.symbol_systems = {}
        self.performance_metrics = {}
        
        logger.info(f"Multi-symbol manager initialized: {len(symbols)} symbols, {max_workers} workers")
    
    async def deploy_symbol(self, symbol: str, system_config: Dict):
        """
        Deploy trading system for a single symbol.
        
        Args:
            symbol: Trading symbol
            system_config: Configuration for this symbol
        """
        from trading_bot.alphaalgo_5star import AlphaAlgo5Star

        logger.info(f"Deploying system for {symbol}...")
        
        # Create dedicated system instance
        system = AlphaAlgo5Star(config=system_config)
        self.symbol_systems[symbol] = system
        
        # Initialize performance tracking
        self.performance_metrics[symbol] = {
            'trades': 0,
            'pnl': 0.0,
            'sharpe': 0.0,
            'signals_generated': 0
        }
        
        logger.success(f"System deployed for {symbol}")
    
    async def deploy_all_symbols(self, base_config: Dict):
        """
        Deploy systems for all symbols in parallel.
        
        Args:
            base_config: Base configuration to use for all symbols
        """
        tasks = []
        for symbol in self.symbols:
            # Customize config per symbol
            symbol_config = base_config.copy()
            symbol_config['symbol'] = symbol
            
            task = self.deploy_symbol(symbol, symbol_config)
            tasks.append(task)
        
        await asyncio.gather(*tasks)
        logger.success(f"All {len(self.symbols)} symbols deployed")
    
    async def generate_signals_parallel(self, market_data: Dict) -> Dict:
        """
        Generate signals for all symbols in parallel.
        
        Args:
            market_data: Dictionary mapping symbols to DataFrames
            
        Returns:
            Dictionary mapping symbols to signals
        """
        async def generate_for_symbol(symbol):
            if symbol not in self.symbol_systems:
                return symbol, None
            
            system = self.symbol_systems[symbol]
            df = market_data.get(symbol)
            
            if df is None or df.empty:
                return symbol, None
            
            signal = await system.generate_signal(df)
            self.performance_metrics[symbol]['signals_generated'] += 1
            
            return symbol, signal
        
        # Generate signals in parallel
        tasks = [generate_for_symbol(symbol) for symbol in self.symbols]
        results = await asyncio.gather(*tasks)
        
        # Convert to dictionary
        signals = {symbol: signal for symbol, signal in results if signal is not None}
        
        logger.info(f"Generated {len(signals)} signals across {len(self.symbols)} symbols")
        return signals
    
    def allocate_capital(self, total_capital: float, 
                        allocation_method: str = 'equal') -> Dict[str, float]:
        """
        Allocate capital across symbols.
        
        Args:
            total_capital: Total capital to allocate
            allocation_method: 'equal', 'performance', or 'risk_parity'
            
        Returns:
            Dictionary mapping symbols to allocated capital
        """
        if allocation_method == 'equal':
            return self._equal_allocation(total_capital)
        elif allocation_method == 'performance':
            return self._performance_based_allocation(total_capital)
        elif allocation_method == 'risk_parity':
            return self._risk_parity_allocation(total_capital)
        else:
            raise ValueError(f"Unknown allocation method: {allocation_method}")
    
    def _equal_allocation(self, total_capital: float) -> Dict[str, float]:
        """Equal allocation across all symbols."""
        per_symbol = total_capital / len(self.symbols)
        return {symbol: per_symbol for symbol in self.symbols}
    
    def _performance_based_allocation(self, total_capital: float) -> Dict[str, float]:
        """Allocate based on past performance."""
        # Calculate performance scores
        scores = {}
        for symbol in self.symbols:
            metrics = self.performance_metrics.get(symbol, {})
            sharpe = metrics.get('sharpe', 0)
            pnl = metrics.get('pnl', 0)
            
            # Combined score
            score = max(0, sharpe * 0.7 + (pnl / 1000) * 0.3)
            scores[symbol] = score
        
        # Normalize scores
        total_score = sum(scores.values())
        if total_score == 0:
            return self._equal_allocation(total_capital)
        
        allocation = {
            symbol: (score / total_score) * total_capital
            for symbol, score in scores.items()
        }
        
        logger.info("Capital allocated based on performance")
        return allocation
    
    def _risk_parity_allocation(self, total_capital: float) -> Dict[str, float]:
        """Risk parity allocation."""
        # Simplified risk parity based on volatility
        volatilities = {}
        for symbol in self.symbols:
            metrics = self.performance_metrics.get(symbol, {})
            # Use inverse volatility for allocation
            vol = metrics.get('volatility', 0.01)
            volatilities[symbol] = 1 / vol
        
        total_inv_vol = sum(volatilities.values())
        
        allocation = {
            symbol: (inv_vol / total_inv_vol) * total_capital
            for symbol, inv_vol in volatilities.items()
        }
        
        logger.info("Capital allocated using risk parity")
        return allocation
    
    def get_portfolio_metrics(self) -> Dict:
        """Get aggregated portfolio metrics."""
        total_trades = sum(m['trades'] for m in self.performance_metrics.values())
        total_pnl = sum(m['pnl'] for m in self.performance_metrics.values())
        
        # Calculate portfolio Sharpe
        sharpes = [m['sharpe'] for m in self.performance_metrics.values() if m['sharpe'] > 0]
        avg_sharpe = np.mean(sharpes) if sharpes else 0
        
        return {
            'total_symbols': len(self.symbols),
            'active_symbols': len(self.symbol_systems),
            'total_trades': total_trades,
            'total_pnl': total_pnl,
            'avg_sharpe': avg_sharpe,
            'per_symbol_metrics': self.performance_metrics
        }


class LoadBalancer:
    """Load balancing for distributed trading systems."""
    
    def __init__(self, n_workers: int = 4):
        """
        Initialize load balancer.
        
        Args:
            n_workers: Number of worker processes
        """
        self.n_workers = n_workers
        self.executor = ProcessPoolExecutor(max_workers=n_workers)
        self.task_queue = []
        self.worker_loads = [0] * n_workers
        
        logger.info(f"Load balancer initialized with {n_workers} workers")
    
    def assign_task(self, task_func, *args, **kwargs):
        """
        Assign task to least loaded worker.
        
        Args:
            task_func: Function to execute
            *args, **kwargs: Function arguments
            
        Returns:
            Future object
        """
        # Find least loaded worker
        worker_id = np.argmin(self.worker_loads)
        
        # Submit task
        future = self.executor.submit(task_func, *args, **kwargs)
        
        # Update load
        self.worker_loads[worker_id] += 1
        
        # Callback to decrease load when done
        def on_complete(f):
            self.worker_loads[worker_id] -= 1
        
        future.add_done_callback(on_complete)
        
        return future
    
    def get_worker_status(self) -> Dict:
        """Get status of all workers."""
        return {
            'n_workers': self.n_workers,
            'worker_loads': self.worker_loads,
            'total_load': sum(self.worker_loads),
            'avg_load': np.mean(self.worker_loads)
        }
    
    def shutdown(self):
        """Shutdown load balancer."""
        self.executor.shutdown(wait=True)
        logger.info("Load balancer shut down")


class HorizontalScaler:
    """Horizontal scaling for trading systems."""
    
    def __init__(self, min_instances: int = 1, max_instances: int = 10):
        """
        Initialize horizontal scaler.
        
        Args:
            min_instances: Minimum number of instances
            max_instances: Maximum number of instances
        """
        self.min_instances = min_instances
        self.max_instances = max_instances
        self.current_instances = min_instances
        self.instances = []
        
        logger.info(f"Horizontal scaler initialized (min: {min_instances}, max: {max_instances})")
    
    def scale_up(self, count: int = 1):
        """
        Scale up by adding instances.
        
        Args:
            count: Number of instances to add
        """
        new_count = min(self.current_instances + count, self.max_instances)
        added = new_count - self.current_instances
        
        if added > 0:
            for _ in range(added):
                instance_id = f"instance_{len(self.instances)}"
                self.instances.append(instance_id)
                logger.info(f"Scaled up: added {instance_id}")
            
            self.current_instances = new_count
            logger.success(f"Scaled up to {self.current_instances} instances")
    
    def scale_down(self, count: int = 1):
        """
        Scale down by removing instances.
        
        Args:
            count: Number of instances to remove
        """
        new_count = max(self.current_instances - count, self.min_instances)
        removed = self.current_instances - new_count
        
        if removed > 0:
            for _ in range(removed):
                instance_id = self.instances.pop()
                logger.info(f"Scaled down: removed {instance_id}")
            
            self.current_instances = new_count
            logger.success(f"Scaled down to {self.current_instances} instances")
    
    def auto_scale(self, metrics: Dict):
        """
        Auto-scale based on metrics.
        
        Args:
            metrics: Performance metrics dictionary
        """
        cpu_usage = metrics.get('cpu_percent', 0)
        latency = metrics.get('latency_ms', 0)
        
        # Scale up if high load
        if cpu_usage > 80 or latency > 100:
            self.scale_up(1)
        
        # Scale down if low load
        elif cpu_usage < 30 and latency < 20 and self.current_instances > self.min_instances:
            self.scale_down(1)
    
    def get_status(self) -> Dict:
        """Get scaler status."""
        return {
            'current_instances': self.current_instances,
            'min_instances': self.min_instances,
            'max_instances': self.max_instances,
            'instances': self.instances
        }
