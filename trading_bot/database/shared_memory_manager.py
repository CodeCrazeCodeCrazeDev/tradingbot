"""
Shared Memory Manager
Provides cross-process shared memory functionality using multiprocessing.shared_memory
Replaces deprecated pyarrow.plasma with a more robust and Windows-compatible solution
"""

import asyncio
import logging
import pickle
import time
import uuid
import os
import sys
import platform
import numpy as np
import pandas as pd
from typing import Any, Dict, List, Optional, Tuple, Union
from multiprocessing import shared_memory
from multiprocessing.managers import SharedMemoryManager
from contextlib import contextmanager
import threading
import weakref
import json
import struct
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


class SharedMemoryObject:
    """
    Wrapper for objects stored in shared memory
    """
    
    def __init__(self, 
                name: str, 
                size: int, 
                dtype: str = 'bytes', 
                shape: Optional[Tuple] = None):
        self.name = name
        self.size = size
        self.dtype = dtype
        self.shape = shape
        self.shm = None
        self.created_at = time.time()
        self.last_accessed = time.time()
        self.access_count = 0
    
    def __del__(self):
        """Clean up shared memory when object is deleted"""
        self.close()
    
    def close(self):
        """Close and unlink shared memory"""
        if self.shm is not None:
            try:
                self.shm.close()
                # Only unlink if we created this shared memory
                if hasattr(self, 'created') and self.created:
                    self.shm.unlink()
            except Exception as e:
                logger.warning(f"Error closing shared memory {self.name}: {e}")
            finally:
                self.shm = None


class SharedMemoryManager:
    """
    Manager for shared memory objects across processes
    Provides a high-level API for storing and retrieving objects in shared memory
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self.objects: Dict[str, SharedMemoryObject] = {}
        self.lock = threading.RLock()
        self.max_size = self.config.get('max_shared_memory_size', 1024 * 1024 * 1024)  # 1GB
        self.current_size = 0
        self.cleanup_threshold = self.config.get('cleanup_threshold', 0.8)  # 80%
        self.cleanup_interval = self.config.get('cleanup_interval', 60)  # 60 seconds
        self.last_cleanup = time.time()
        
        # Start cleanup thread
        self.cleanup_thread = threading.Thread(target=self._cleanup_loop, daemon=True)
        self.cleanup_thread.start()
        
        logger.info("Shared memory manager initialized")
    
    def _cleanup_loop(self):
        """Background thread for periodic cleanup"""
        while True:
            time.sleep(self.cleanup_interval)
            try:
                self._cleanup_old_objects()
            except Exception as e:
                logger.error(f"Error in cleanup loop: {e}")
    
    def _cleanup_old_objects(self):
        """Clean up old or unused objects"""
        with self.lock:
            # Check if cleanup is needed
            if self.current_size < self.max_size * self.cleanup_threshold:
                return
            
            now = time.time()
            self.last_cleanup = now
            
            # Sort objects by last access time
            objects_by_age = sorted(
                self.objects.items(),
                key=lambda x: x[1].last_accessed
            )
            
            # Remove oldest objects until we're below threshold
            target_size = self.max_size * 0.7  # Target 70% usage after cleanup
            for obj_id, obj in objects_by_age:
                if self.current_size <= target_size:
                    break
                
                # Skip if accessed in the last minute
                if now - obj.last_accessed < 60:
                    continue
                
                logger.debug(f"Cleaning up shared memory object {obj_id} "
                           f"(size: {obj.size}, last accessed: {now - obj.last_accessed:.1f}s ago)")
                
                self.current_size -= obj.size
                obj.close()
                del self.objects[obj_id]
    
    def put(self, data: Any, obj_id: Optional[str] = None) -> str:
        """
        Store an object in shared memory
        
        Args:
            data: The data to store
            obj_id: Optional ID for the object, generated if not provided
            
        Returns:
            The object ID
        """
        if obj_id is None:
            obj_id = str(uuid.uuid4())
        
        # Handle different data types
        if isinstance(data, np.ndarray):
            return self._put_numpy_array(data, obj_id)
        elif isinstance(data, pd.DataFrame):
            return self._put_dataframe(data, obj_id)
        else:
            return self._put_pickle(data, obj_id)
    
    def _put_numpy_array(self, array: np.ndarray, obj_id: str) -> str:
        """Store a NumPy array in shared memory"""
        with self.lock:
            # Clean up existing object with same ID
            if obj_id in self.objects:
                old_obj = self.objects[obj_id]
                self.current_size -= old_obj.size
                old_obj.close()
            
            # Create shared memory
            size = array.nbytes
            shm = shared_memory.SharedMemory(create=True, size=size)
            
            # Copy data to shared memory
            np_array = np.ndarray(array.shape, dtype=array.dtype, buffer=shm.buf)
            np_array[:] = array[:]
            
            # Create object metadata
            obj = SharedMemoryObject(
                name=shm.name,
                size=size,
                dtype=str(array.dtype),
                shape=array.shape
            )
            obj.shm = shm
            obj.created = True
            
            # Store object
            self.objects[obj_id] = obj
            self.current_size += size
            
            return obj_id
    
    def _put_dataframe(self, df: pd.DataFrame, obj_id: str) -> str:
        """Store a pandas DataFrame in shared memory"""
        # Convert to dict of arrays
        arrays = {
            'index': df.index.values,
            'columns': np.array(df.columns),
            'dtypes': np.array([str(dt) for dt in df.dtypes])
        }
        
        for col in df.columns:
            arrays[f'data_{col}'] = df[col].values
        
        # Store dict in shared memory
        return self._put_pickle(arrays, obj_id)
    
    def _put_pickle(self, data: Any, obj_id: str) -> str:
        """Store a pickled object in shared memory"""
        with self.lock:
            # Clean up existing object with same ID
            if obj_id in self.objects:
                old_obj = self.objects[obj_id]
                self.current_size -= old_obj.size
                old_obj.close()
            
            # Pickle data
            pickled_data = pickle.dumps(data)
            size = len(pickled_data)
            
            # Create shared memory
            shm = shared_memory.SharedMemory(create=True, size=size)
            
            # Copy data to shared memory
            shm.buf[:size] = pickled_data
            
            # Create object metadata
            obj = SharedMemoryObject(
                name=shm.name,
                size=size,
                dtype='pickle'
            )
            obj.shm = shm
            obj.created = True
            
            # Store object
            self.objects[obj_id] = obj
            self.current_size += size
            
            return obj_id
    
    def get(self, obj_id: str) -> Any:
        """
        Retrieve an object from shared memory
        
        Args:
            obj_id: The object ID
            
        Returns:
            The stored object
        
        Raises:
            KeyError: If the object ID is not found
        """
        with self.lock:
            if obj_id not in self.objects:
                raise KeyError(f"Object {obj_id} not found in shared memory")
            
            obj = self.objects[obj_id]
            obj.last_accessed = time.time()
            obj.access_count += 1
            
            if obj.dtype == 'pickle':
                return self._get_pickle(obj)
            elif obj.dtype.startswith('float') or obj.dtype.startswith('int'):
                return self._get_numpy_array(obj)
            else:
                return self._get_pickle(obj)
    
    def _get_numpy_array(self, obj: SharedMemoryObject) -> np.ndarray:
        """Retrieve a NumPy array from shared memory"""
        # Attach to shared memory
        if obj.shm is None:
            obj.shm = shared_memory.SharedMemory(name=obj.name)
        
        # Create array view
        array = np.ndarray(obj.shape, dtype=np.dtype(obj.dtype), buffer=obj.shm.buf)
        
        # Return a copy to avoid issues if the shared memory is deleted
        return array.copy()
    
    def _get_pickle(self, obj: SharedMemoryObject) -> Any:
        """Retrieve a pickled object from shared memory"""
        # Attach to shared memory
        if obj.shm is None:
            obj.shm = shared_memory.SharedMemory(name=obj.name)
        
        # Unpickle data
        pickled_data = bytes(obj.shm.buf[:obj.size])
        return pickle.loads(pickled_data)
    
    def get_dataframe(self, obj_id: str) -> pd.DataFrame:
        """
        Retrieve a DataFrame from shared memory
        
        Args:
            obj_id: The object ID
            
        Returns:
            The stored DataFrame
            
        Raises:
            KeyError: If the object ID is not found
            ValueError: If the object is not a DataFrame
        """
        arrays = self.get(obj_id)
        
        if not isinstance(arrays, dict) or 'columns' not in arrays or 'index' not in arrays:
            raise ValueError(f"Object {obj_id} is not a DataFrame")
        
        # Reconstruct DataFrame
        df_data = {}
        for col in arrays['columns']:
            col_str = str(col)
            if f'data_{col_str}' in arrays:
                df_data[col_str] = arrays[f'data_{col_str}']
        
        return pd.DataFrame(df_data, index=arrays['index'])
    
    def exists(self, obj_id: str) -> bool:
        """Check if an object exists in shared memory"""
        with self.lock:
            return obj_id in self.objects
    
    def delete(self, obj_id: str) -> bool:
        """
        Delete an object from shared memory
        
        Args:
            obj_id: The object ID
            
        Returns:
            True if the object was deleted, False if it didn't exist
        """
        with self.lock:
            if obj_id not in self.objects:
                return False
            
            obj = self.objects[obj_id]
            self.current_size -= obj.size
            obj.close()
            del self.objects[obj_id]
            
            return True
    
    def clear(self):
        """Clear all objects from shared memory"""
        with self.lock:
            for obj_id, obj in list(self.objects.items()):
                obj.close()
            
            self.objects.clear()
            self.current_size = 0
    
    def get_stats(self) -> Dict[str, Any]:
        """Get statistics about shared memory usage"""
        with self.lock:
            return {
                'object_count': len(self.objects),
                'current_size': self.current_size,
                'max_size': self.max_size,
                'usage_percent': (self.current_size / self.max_size) * 100 if self.max_size > 0 else 0,
                'last_cleanup': self.last_cleanup
            }
    
    def cleanup(self):
        """Clean up shared memory resources"""
        self.clear()


class AsyncSharedMemoryManager:
    """
    Async wrapper for SharedMemoryManager
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.manager = SharedMemoryManager(config)
    
    async def put(self, data: Any, obj_id: Optional[str] = None) -> str:
        """Async version of put"""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            None, lambda: self.manager.put(data, obj_id)
        )
    
    async def get(self, obj_id: str) -> Any:
        """Async version of get"""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            None, lambda: self.manager.get(obj_id)
        )
    
    async def get_dataframe(self, obj_id: str) -> pd.DataFrame:
        """Async version of get_dataframe"""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            None, lambda: self.manager.get_dataframe(obj_id)
        )
    
    async def exists(self, obj_id: str) -> bool:
        """Async version of exists"""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            None, lambda: self.manager.exists(obj_id)
        )
    
    async def delete(self, obj_id: str) -> bool:
        """Async version of delete"""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            None, lambda: self.manager.delete(obj_id)
        )
    
    async def clear(self):
        """Async version of clear"""
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(
            None, self.manager.clear
        )
    
    async def get_stats(self) -> Dict[str, Any]:
        """Async version of get_stats"""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            None, self.manager.get_stats
        )
    
    async def cleanup(self):
        """Async version of cleanup"""
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(
            None, self.manager.cleanup
        )


# Global shared memory manager instance
_shared_memory_manager = None


def get_shared_memory_manager(config: Optional[Dict[str, Any]] = None) -> SharedMemoryManager:
    """Get the global shared memory manager instance"""
    global _shared_memory_manager
    if _shared_memory_manager is None:
        _shared_memory_manager = SharedMemoryManager(config)
    return _shared_memory_manager


def get_async_shared_memory_manager(config: Optional[Dict[str, Any]] = None) -> AsyncSharedMemoryManager:
    """Get an async shared memory manager instance"""
    return AsyncSharedMemoryManager(config)
