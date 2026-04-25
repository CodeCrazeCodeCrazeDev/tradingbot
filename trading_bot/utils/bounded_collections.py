"""
Bounded Collections
Memory-efficient collections with automatic size limits to prevent memory leaks
"""

import threading
from collections import deque, OrderedDict
from typing import Any, Dict, List, Optional, TypeVar, Generic
import logging

logger = logging.getLogger(__name__)

T = TypeVar('T')


class BoundedList(Generic[T]):
    """
    A list with a maximum size that automatically removes oldest items.
    Thread-safe implementation.
    """
    
    def __init__(self, max_size: int = 1000):
        self.max_size = max_size
        self._data: List[T] = []
        self._lock = threading.Lock()
    
    def append(self, item: T) -> None:
        """Add an item, removing oldest if at capacity"""
        with self._lock:
            self._data.append(item)
            if len(self._data) > self.max_size:
                # Remove oldest items to maintain size
                excess = len(self._data) - self.max_size
                self._data = self._data[excess:]
    
    def extend(self, items: List[T]) -> None:
        """Add multiple items"""
        with self._lock:
            self._data.extend(items)
            if len(self._data) > self.max_size:
                excess = len(self._data) - self.max_size
                self._data = self._data[excess:]
    
    def get_latest(self, n: int = 1) -> List[T]:
        """Get latest n items"""
        with self._lock:
            return self._data[-n:] if n > 0 else []
    
    def get_oldest(self, n: int = 1) -> List[T]:
        """Get oldest n items"""
        with self._lock:
            return self._data[:n] if n > 0 else []
    
    def clear(self) -> None:
        """Clear all items"""
        with self._lock:
            self._data.clear()
    
    def __len__(self) -> int:
        with self._lock:
            return len(self._data)
    
    def __getitem__(self, index: int) -> T:
        with self._lock:
            return self._data[index]
    
    def __iter__(self):
        with self._lock:
            return iter(self._data.copy())


class BoundedDeque(Generic[T]):
    """
    A deque with a maximum size using Python's built-in deque.
    More efficient for FIFO operations.
    """
    
    def __init__(self, max_size: int = 1000):
        self.max_size = max_size
        self._data = deque(maxlen=max_size)
        self._lock = threading.Lock()
    
    def append(self, item: T) -> None:
        """Add an item to the right"""
        with self._lock:
            self._data.append(item)
    
    def appendleft(self, item: T) -> None:
        """Add an item to the left"""
        with self._lock:
            self._data.appendleft(item)
    
    def pop(self) -> T:
        """Remove and return rightmost item"""
        with self._lock:
            return self._data.pop()
    
    def popleft(self) -> T:
        """Remove and return leftmost item"""
        with self._lock:
            return self._data.popleft()
    
    def clear(self) -> None:
        """Clear all items"""
        with self._lock:
            self._data.clear()
    
    def __len__(self) -> int:
        return len(self._data)
    
    def __getitem__(self, index: int) -> T:
        with self._lock:
            return self._data[index]
    
    def __iter__(self):
        with self._lock:
            return iter(list(self._data))


class BoundedDict(Generic[T]):
    """
    A dictionary with a maximum size using LRU eviction.
    Thread-safe implementation.
    """
    
    def __init__(self, max_size: int = 1000):
        self.max_size = max_size
        self._data: OrderedDict[Any, T] = OrderedDict()
        self._lock = threading.Lock()
    
    def __setitem__(self, key: Any, value: T) -> None:
        """Set a key-value pair"""
        with self._lock:
            if key in self._data:
                # Move to end (most recently used)
                self._data.move_to_end(key)
            else:
                # Check capacity
                if len(self._data) >= self.max_size:
                    # Remove least recently used
                    self._data.popitem(last=False)
            
            self._data[key] = value
    
    def __getitem__(self, key: Any) -> T:
        """Get value by key"""
        with self._lock:
            value = self._data[key]
            # Move to end (most recently used)
            self._data.move_to_end(key)
            return value
    
    def get(self, key: Any, default: Optional[T] = None) -> Optional[T]:
        """Get value by key with default"""
        with self._lock:
            if key in self._data:
                value = self._data[key]
                self._data.move_to_end(key)
                return value
            return default
    
    def pop(self, key: Any, default: Optional[T] = None) -> Optional[T]:
        """Remove and return value"""
        with self._lock:
            return self._data.pop(key, default)
    
    def clear(self) -> None:
        """Clear all items"""
        with self._lock:
            self._data.clear()
    
    def __len__(self) -> int:
        with self._lock:
            return len(self._data)
    
    def __contains__(self, key: Any) -> bool:
        with self._lock:
            return key in self._data
    
    def keys(self):
        """Get all keys"""
        with self._lock:
            return list(self._data.keys())
    
    def values(self):
        """Get all values"""
        with self._lock:
            return list(self._data.values())
    
    def items(self):
        """Get all items"""
        with self._lock:
            return list(self._data.items())


class BoundedSet(Generic[T]):
    """
    A set with a maximum size.
    When full, removes random items to make space.
    """
    
    def __init__(self, max_size: int = 1000):
        self.max_size = max_size
        self._data: set = set()
        self._lock = threading.Lock()
    
    def add(self, item: T) -> None:
        """Add an item"""
        with self._lock:
            if item not in self._data:
                if len(self._data) >= self.max_size:
                    # Remove a random item
                    import random
                    self._data.pop()
                self._data.add(item)
    
    def discard(self, item: T) -> None:
        """Remove an item if present"""
        with self._lock:
            self._data.discard(item)
    
    def clear(self) -> None:
        """Clear all items"""
        with self._lock:
            self._data.clear()
    
    def __len__(self) -> int:
        with self._lock:
            return len(self._data)
    
    def __contains__(self, item: T) -> bool:
        with self._lock:
            return item in self._data
    
    def __iter__(self):
        with self._lock:
            return iter(self._data.copy())


class MemoryMonitor:
    """
    Monitor memory usage of bounded collections.
    """
    
    def __init__(self):
        self.collections: Dict[str, Any] = {}
        self._lock = threading.Lock()
    
    def register(self, name: str, collection: Any) -> None:
        """Register a collection for monitoring"""
        with self._lock:
            self.collections[name] = collection
    
    def get_stats(self) -> Dict[str, Dict[str, Any]]:
        """Get statistics for all registered collections"""
        with self._lock:
            stats = {}
            for name, collection in self.collections.items():
                stats[name] = {
                    'type': type(collection).__name__,
                    'size': len(collection),
                    'max_size': getattr(collection, 'max_size', 'N/A'),
                    'utilization': len(collection) / getattr(collection, 'max_size', 1)
                }
            return stats
    
    def log_stats(self) -> None:
        """Log collection statistics"""
        stats = self.get_stats()
        for name, stat in stats.items():
            logger.debug(f"{name}: {stat['size']}/{stat['max_size']} "
                        f"({stat['utilization']:.1%})")


# Factory functions for easy creation
def bounded_list(max_size: int = 1000) -> BoundedList:
    """Create a bounded list"""
    return BoundedList(max_size)


def bounded_deque(max_size: int = 1000) -> BoundedDeque:
    """Create a bounded deque"""
    return BoundedDeque(max_size)


def bounded_dict(max_size: int = 1000) -> BoundedDict:
    """Create a bounded dictionary"""
    return BoundedDict(max_size)


def bounded_set(max_size: int = 1000) -> BoundedSet:
    """Create a bounded set"""
    return BoundedSet(max_size)


# Global memory monitor instance
memory_monitor = MemoryMonitor()
