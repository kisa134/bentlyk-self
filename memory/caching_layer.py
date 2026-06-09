import time
from collections import OrderedDict
from typing import Any, Dict, Optional, Callable
from threading import RLock


class LRUCache:
    """LRU Cache implementation with configurable size limit"""
    
    def __init__(self, max_size: int = 1000):
        self.max_size = max_size
        self.cache = OrderedDict()
        self.lock = RLock()
        
    def get(self, key: str) -> Optional[Any]:
        with self.lock:
            if key in self.cache:
                # Move to end to mark as recently used
                self.cache.move_to_end(key)
                return self.cache[key]
            return None
    
    def put(self, key: str, value: Any) -> None:
        with self.lock:
            if key in self.cache:
                # Update existing key
                self.cache.move_to_end(key)
            elif len(self.cache) >= self.max_size:
                # Remove least recently used item
                self.cache.popitem(last=False)
            
            self.cache[key] = value
    
    def remove(self, key: str) -> bool:
        with self.lock:
            if key in self.cache:
                del self.cache[key]
                return True
            return False
    
    def clear(self) -> None:
        with self.lock:
            self.cache.clear()
    
    def size(self) -> int:
        with self.lock:
            return len(self.cache)


class CachingLayer:
    """Caching layer that stores frequently accessed memory items with automatic updates and metrics"""
    
    def __init__(self, memory_backend: Any, cache_size: int = 1000):
        self.memory_backend = memory_backend
        self.cache = LRUCache(cache_size)
        self.hit_count = 0
        self.miss_count = 0
        self.lock = RLock()
        
    def get(self, key: str, default: Any = None) -> Any:
        """Retrieve item from cache or underlying memory"""
        # Try cache first
        cached_value = self.cache.get(key)
        if cached_value is not None:
            with self.lock:
                self.hit_count += 1
            return cached_value
        
        # Cache miss - fetch from backend
        with self.lock:
            self.miss_count += 1
        
        value = self.memory_backend.get(key, default)
        if value is not default:
            self.cache.put(key, value)
        
        return value
    
    def set(self, key: str, value: Any) -> None:
        """Set item in both cache and underlying memory"""
        self.memory_backend.set(key, value)
        self.cache.put(key, value)
    
    def delete(self, key: str) -> bool:
        """Delete item from both cache and underlying memory"""
        success = self.memory_backend.delete(key)
        if success:
            self.cache.remove(key)
        return success
    
    def clear(self) -> None:
        """Clear both cache and underlying memory"""
        self.memory_backend.clear()
        self.cache.clear()
        with self.lock:
            self.hit_count = 0
            self.miss_count = 0
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get cache performance metrics"""
        with self.lock:
            total_requests = self.hit_count + self.miss_count
            hit_rate = self.hit_count / total_requests if total_requests > 0 else 0
            miss_rate = self.miss_count / total_requests if total_requests > 0 else 0
            
            return {
                'hit_count': self.hit_count,
                'miss_count': self.miss_count,
                'hit_rate': hit_rate,
                'miss_rate': miss_rate,
                'cache_size': self.cache.size(),
                'total_requests': total_requests
            }
    
    def update_cache(self, key: str, value: Any) -> None:
        """Manually update cache entry"""
        self.cache.put(key, value)
    
    def invalidate_cache(self, key: str) -> bool:
        """Manually invalidate cache entry"""
        return self.cache.remove(key)
    
    def warm_up(self, keys: list) -> None:
        """Pre-populate cache with specified keys"""
        for key in keys:
            value = self.memory_backend.get(key)
            if value is not None:
                self.cache.put(key, value)