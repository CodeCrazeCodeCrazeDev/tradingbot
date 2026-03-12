"""
Real-Time Market Data Processor
Handles high-performance processing of market data streams
"""

import asyncio
import numpy as np
import pandas as pd
from typing import Any, Callable, Dict, List, Optional
from datetime import datetime
from collections import defaultdict
import logging
from dataclasses import dataclass
from concurrent.futures import ProcessPoolExecutor
import os
import platform
from multiprocessing import shared_memory
import pickle
import numpy
import pandas

# Evolution: Added retry decorator
def retry(max_attempts=3, delay=1.0):
    """Retry decorator for resilient operations"""
    def decorator(func):
        async def wrapper(*args, **kwargs):
            last_error = None
            for attempt in range(max_attempts):
                try:
                    return await func(*args, **kwargs)
                except Exception as e:
                    last_error = e
                    if attempt < max_attempts - 1:
                        await asyncio.sleep(delay * (attempt + 1))
            raise last_error
        return wrapper
    return decorator



logger = logging.getLogger(__name__)

@dataclass
class ProcessingStats:
    """Statistics for data processing"""
    processed_count: int = 0
    processing_time: float = 0.0
    queue_time: float = 0.0
    last_processed: Optional[datetime] = None
    error_count: int = 0

class DataProcessor:
    """High-performance real-time data processor"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.stats: Dict[str, ProcessingStats] = defaultdict(ProcessingStats)
        
        # Shared memory for high-speed data access
        self.use_shared_memory = config.get('use_shared_memory', True)
        self.shared_data = {}
        self.shared_memory_blocks = {}
        
        # Process pool for parallel processing
        self.process_pool = ProcessPoolExecutor(
            max_workers=config.get('processing_workers', 4)
        )
        
        # Data buffers for different timeframes
        self.buffers: Dict[str, pd.DataFrame] = {}
        
        # Processing pipelines
        self.pipelines: Dict[str, List[Callable]] = defaultdict(list)
        
        # Real-time indicators
        self.indicators: Dict[str, Dict[str, Any]] = {}
        
        logger.info("Real-time data processor initialized")
    
    async def process_market_data(self, data: Dict[str, Any], data_type: str):
        """Process incoming market data"""
        start_time = datetime.now()
        
        try:
            # Convert to DataFrame if needed
            df = self._prepare_data(data)
            
            # Store in shared memory if large dataset
            if len(df) > 1000 and self.use_shared_memory:
                # Use in-process shared dictionary instead
                data_id = f"{data_type}_{datetime.now().timestamp()}"
                self.shared_data[data_id] = df
                df = data_id  # Use reference instead of data
            
            # Apply processing pipeline
            processed_data = await self._apply_pipeline(df, data_type)
            
            # Update indicators
            await self._update_indicators(processed_data, data_type)
            
            # Update statistics
            self._update_stats(data_type, start_time)
            
            return processed_data
            
        except Exception as e:
            logger.error(f"Error processing {data_type} data: {e}")
            self.stats[data_type].error_count += 1
            raise
    
    def _prepare_data(self, data: Dict[str, Any]) -> pd.DataFrame:
        """Prepare data for processing"""
        if isinstance(data, pd.DataFrame):
            return data
        elif isinstance(data, dict):
            return pd.DataFrame([data])
        elif isinstance(data, list):
            return pd.DataFrame(data)
        else:
            raise ValueError(f"Unsupported data type: {type(data)}")
    
    async def _apply_pipeline(self, data: Any, data_type: str) -> Any:
        """Apply processing pipeline to data"""
        processed = data
        
        for processor in self.pipelines[data_type]:
            try:
                if isinstance(processed, str) and processed in self.shared_data:
                    # Load from shared data if working with reference
                    processed = self.shared_data[processed]
                
                if asyncio.iscoroutinefunction(processor):
                    processed = await processor(processed)
                else:
                    # Run CPU-intensive processors in process pool
                    if self._is_cpu_intensive(processor):
                        processed = await asyncio.get_event_loop().run_in_executor(
                            self.process_pool,
                            processor,
                            processed
                        )
                    else:
                        processed = processor(processed)
                
            except Exception as e:
                logger.error(f"Error in processor {processor.__name__}: {e}")
                raise
        
        return processed
    
    def _is_cpu_intensive(self, processor: Callable) -> bool:
        """Determine if a processor is CPU-intensive"""
        # Check processor attributes or naming conventions
        cpu_intensive_keywords = {'calculate', 'compute', 'analyze', 'transform'}
        return any(keyword in processor.__name__.lower() for keyword in cpu_intensive_keywords)
    
    async def _update_indicators(self, data: Any, data_type: str):
        """Update real-time indicators"""
        if data_type not in self.indicators:
            self.indicators[data_type] = {}
        
        indicators = self.indicators[data_type]
        
        # Update technical indicators
        if isinstance(data, pd.DataFrame) and not data.empty:
            indicators['vwap'] = self._calculate_vwap(data)
            indicators['momentum'] = self._calculate_momentum(data)
            indicators['volatility'] = self._calculate_volatility(data)
            
            # Store in shared data dictionary
            indicators_id = f"indicators_{data_type}_{datetime.now().timestamp()}"
            self.shared_data[indicators_id] = indicators
            self.indicators[data_type]['_shared_id'] = indicators_id
    
    def _calculate_vwap(self, data: pd.DataFrame) -> float:
        """Calculate Volume Weighted Average Price"""
        if 'price' in data.columns and 'volume' in data.columns:
            return np.average(data['price'], weights=data['volume'])
        return 0.0
    
    def _calculate_momentum(self, data: pd.DataFrame) -> float:
        """Calculate price momentum"""
        if 'price' in data.columns:
            return data['price'].diff().mean()
        return 0.0
    
    def _calculate_volatility(self, data: pd.DataFrame) -> float:
        """Calculate price volatility"""
        if 'price' in data.columns:
            return data['price'].std()
        return 0.0
    
    def add_processor(self, data_type: str, processor: Callable):
        """Add a processor to the pipeline"""
        self.pipelines[data_type].append(processor)
        logger.info(f"Added processor {processor.__name__} to {data_type} pipeline")
    
    def _update_stats(self, data_type: str, start_time: datetime):
        """Update processing statistics"""
        stats = self.stats[data_type]
        stats.processed_count += 1
        stats.processing_time += (datetime.now() - start_time).total_seconds()
        stats.last_processed = datetime.now()
    
    def get_stats(self) -> Dict[str, Dict[str, Any]]:
        """Get processing statistics"""
        return {
            data_type: {
                'processed_count': stats.processed_count,
                'avg_processing_time': stats.processing_time / stats.processed_count if stats.processed_count > 0 else 0,
                'error_rate': stats.error_count / stats.processed_count if stats.processed_count > 0 else 0,
                'last_processed': stats.last_processed.isoformat() if stats.last_processed else None
            }
            for data_type, stats in self.stats.items()
        }
    
    def get_indicators(self, data_type: str) -> Dict[str, Any]:
        """Get current indicators for a data type"""
        if data_type not in self.indicators:
            return {}
        
        # Load from shared data if stored there
        if '_shared_id' in self.indicators[data_type] and self.indicators[data_type]['_shared_id'] in self.shared_data:
            return self.shared_data[self.indicators[data_type]['_shared_id']]
        
        return self.indicators[data_type]
    
    async def cleanup(self):
        """Cleanup resources"""
        self.process_pool.shutdown()
        
        # Clean up shared data
        self.shared_data.clear()
        
        # Clean up any shared memory blocks
        for block_name, block in self.shared_memory_blocks.items():
            try:
                block.close()
                block.unlink()
            except Exception as e:
                logger.warning(f"Error cleaning up shared memory block {block_name}: {e}")
        
        logger.info("Real-time processor cleaned up")
