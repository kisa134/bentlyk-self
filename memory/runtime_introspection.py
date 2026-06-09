import time
import threading
from collections import defaultdict, deque
from typing import Dict, List, Tuple, Optional, Callable
from dataclasses import dataclass
from enum import Enum
import weakref

class AccessType(Enum):
    READ = "READ"
    WRITE = "WRITE"

@dataclass
class MemoryAccessRecord:
    timestamp: float
    address: int
    access_type: AccessType
    data_size: int
    latency: float
    thread_id: int

class AnomalyDetector:
    def __init__(self, window_size: int = 100, latency_threshold: float = 0.001):
        self.window_size = window_size
        self.latency_threshold = latency_threshold
        self.access_history: deque = deque(maxlen=window_size)
        self._lock = threading.Lock()
        
    def add_record(self, record: MemoryAccessRecord) -> bool:
        with self._lock:
            self.access_history.append(record)
            return self._detect_anomaly(record)
    
    def _detect_anomaly(self, record: MemoryAccessRecord) -> bool:
        if len(self.access_history) < 10:
            return False
            
        # Check for high latency
        if record.latency > self.latency_threshold:
            return True
            
        # Check for unusual access patterns
        recent_writes = [r for r in self.access_history 
                        if r.access_type == AccessType.WRITE and 
                        abs(r.address - record.address) < 1024]
        
        if len(recent_writes) > 5 and record.access_type == AccessType.READ:
            # Rapid write-then-read pattern might indicate coherence issues
            return True
            
        return False

class CoherenceScorer:
    def __init__(self, window_size: int = 50):
        self.window_size = window_size
        self.access_patterns: deque = deque(maxlen=window_size)
        self._lock = threading.Lock()
        
    def add_record(self, record: MemoryAccessRecord):
        with self._lock:
            self.access_patterns.append(record)
    
    def calculate_coherence_score(self) -> float:
        with self._lock:
            if len(self.access_patterns) < 5:
                return 1.0
                
            # Calculate spatial locality score
            addresses = [r.address for r in self.access_patterns]
            spatial_score = self._calculate_spatial_locality(addresses)
            
            # Calculate temporal locality score
            timestamps = [r.timestamp for r in self.access_patterns]
            temporal_score = self._calculate_temporal_locality(timestamps)
            
            # Combine scores
            return (spatial_score + temporal_score) / 2.0
    
    def _calculate_spatial_locality(self, addresses: List[int]) -> float:
        if len(addresses) < 2:
            return 1.0
            
        distances = [abs(addresses[i] - addresses[i-1]) for i in range(1, len(addresses))]
        avg_distance = sum(distances) / len(distances)
        
        # Normalize: closer addresses = higher score
        return max(0.0, min(1.0, 1000.0 / (avg_distance + 1)))
    
    def _calculate_temporal_locality(self, timestamps: List[float]) -> float:
        if len(timestamps) < 2:
            return 1.0
            
        intervals = [timestamps[i] - timestamps[i-1] for i in range(1, len(timestamps))]
        avg_interval = sum(intervals) / len(intervals)
        
        # Normalize: shorter intervals = higher score
        return max(0.0, min(1.0, 1.0 / (avg_interval * 1000 + 0.1)))

class RuntimeIntrospection:
    def __init__(self, enable_tracing: bool = True):
        self.enable_tracing = enable_tracing
        self.access_log: List[MemoryAccessRecord] = []
        self.anomaly_detector = AnomalyDetector()
        self.coherence_scorer = CoherenceScorer()
        self.hooks: Dict[str, List[Callable]] = {
            'anomaly_detected': [],
            'access_logged': [],
            'coherence_updated': []
        }
        self._lock = threading.RLock()
        self._stats = {
            'total_accesses': 0,
            'read_count': 0,
            'write_count': 0,
            'anomalies_detected': 0,
            'total_latency': 0.0
        }
        
    def register_hook(self, hook_type: str, callback: Callable):
        """Register a callback for specific events"""
        if hook_type in self.hooks:
            self.hooks[hook_type].append(callback)
    
    def _trigger_hooks(self, hook_type: str, *args, **kwargs):
        """Trigger all registered hooks of a specific type"""
        for callback in self.hooks.get(hook_type, []):
            try:
                callback(*args, **kwargs)
            except Exception:
                pass  # Silently ignore hook errors
    
    def log_access(self, address: int, access_type: AccessType, data_size: int, 
                   start_time: float, end_time: float):
        """Log a memory access operation"""
        if not self.enable_tracing:
            return
            
        latency = end_time - start_time
        record = MemoryAccessRecord(
            timestamp=start_time,
            address=address,
            access_type=access_type,
            data_size=data_size,
            latency=latency,
            thread_id=threading.get_ident()
        )
        
        with self._lock:
            self.access_log.append(record)
            self._update_stats(record)
            
            # Update coherence scorer
            self.coherence_scorer.add_record(record)
            
            # Check for anomalies
            is_anomaly = self.anomaly_detector.add_record(record)
            if is_anomaly:
                self._stats['anomalies_detected'] += 1
                self._trigger_hooks('anomaly_detected', record)
            
            self._trigger_hooks('access_logged', record)
    
    def _update_stats(self, record: MemoryAccessRecord):
        """Update internal statistics"""
        self._stats['total_accesses'] += 1
        self._stats['total_latency'] += record.latency
        
        if record.access_type == AccessType.READ:
            self._stats['read_count'] += 1
        else:
            self._stats['write_count'] += 1
    
    def get_access_summary(self) -> Dict:
        """Get a summary of memory access patterns"""
        with self._lock:
            if self._stats['total_accesses'] == 0:
                return {'coherence_score': 1.0, 'stats': self._stats.copy()}
            
            avg_latency = self._stats['total_latency'] / self._stats['total_accesses']
            coherence_score = self.coherence_scorer.calculate_coherence_score()
            
            return {
                'coherence_score': coherence_score,
                'average_latency': avg_latency,
                'stats': self._stats.copy()
            }
    
    def get_recent_accesses(self, count: int = 50) -> List[MemoryAccessRecord]:
        """Get the most recent memory accesses"""
        with self._lock:
            return list(self.access_log[-count:]) if self.access_log else []
    
    def clear_log(self):
        """Clear the access log"""
        with self._lock:
            self.access_log.clear()
            self._stats = {
                'total_accesses': 0,
                'read_count': 0,
                'write_count': 0,
                'anomalies_detected': 0,
                'total_latency': 0.0
            }

# Global tracer instance
_tracer: Optional[RuntimeIntrospection] = None
_tracer_lock = threading.Lock()

def get_tracer() -> RuntimeIntrospection:
    """Get or create the global tracer instance"""
    global _tracer
    with _tracer_lock:
        if _tracer is None:
            _tracer = RuntimeIntrospection()
        return _tracer

def trace_memory_access(address: int, access_type: AccessType, data_size: int):
    """Decorator to trace memory access operations"""
    def decorator(func):
        def wrapper(*args, **kwargs):
            if not get_tracer().enable_tracing:
                return func(*args, **kwargs)
                
            start_time = time.perf_counter()
            try:
                result = func(*args, **kwargs)
                return result
            finally:
                end_time = time.perf_counter()
                get_tracer().log_access(address, access_type, data_size, start_time, end_time)
        return wrapper
    return decorator

# Context manager for tracing blocks of code
class MemoryTraceContext:
    def __init__(self, address: int, access_type: AccessType, data_size: int):
        self.address = address
        self.access_type = access_type
        self.data_size = data_size
        self.start_time = None
        
    def __enter__(self):
        if get_tracer().enable_tracing:
            self.start_time = time.perf_counter()
        return self
        
    def __exit__(self, exc_type, exc_val, exc_tb):
        if get_tracer().enable_tracing and self.start_time:
            end_time = time.perf_counter()
            get_tracer().log_access(
                self.address, self.access_type, self.data_size, 
                self.start