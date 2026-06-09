import time
import threading
import json
import logging
from collections import defaultdict, deque
from dataclasses import dataclass, asdict
from typing import Dict, List, Optional, Tuple
from contextlib import contextmanager

logger = logging.getLogger(__name__)

@dataclass
class AllocationEvent:
    timestamp: float
    thread_id: int
    size: int
    latency: float
    callstack: List[str]
    is_contended: bool

@dataclass
class TelemetrySnapshot:
    timestamp: float
    total_allocated: int
    allocation_rate: float
    deallocation_rate: float
    contention_count: int
    latency_percentiles: Dict[str, float]

class TelemetryCollector:
    def __init__(self, window_size: int = 1000):
        self.window_size = window_size
        self.events = deque(maxlen=window_size)
        self.lock = threading.RLock()
        self.total_allocated = 0
        self.total_deallocated = 0
        self.contention_events = 0
        self.last_snapshot_time = time.time()
        self.allocation_times = defaultdict(float)
        
    @contextmanager
    def trace_allocation(self, size: int, callstack: Optional[List[str]] = None):
        start_time = time.perf_counter()
        thread_id = threading.get_ident()
        
        try:
            yield
        finally:
            end_time = time.perf_counter()
            latency = end_time - start_time
            
            with self.lock:
                self.total_allocated += size
                event = AllocationEvent(
                    timestamp=time.time(),
                    thread_id=thread_id,
                    size=size,
                    latency=latency,
                    callstack=callstack or [],
                    is_contended=False
                )
                self.events.append(event)
                
                # Check for contention based on overlapping timestamps
                if len(self.events) > 1:
                    recent_events = [e for e in self.events 
                                   if e.timestamp > (time.time() - 0.001)]
                    if len(recent_events) > 1:
                        self.contention_events += 1
                        for e in recent_events:
                            e.is_contended = True

    @contextmanager
    def trace_deallocation(self, size: int):
        start_time = time.perf_counter()
        
        try:
            yield
        finally:
            end_time = time.perf_counter()
            latency = end_time - start_time
            
            with self.lock:
                self.total_deallocated += size
                # Log deallocation event
                logger.debug(f"Deallocation: {size} bytes, latency: {latency:.6f}s")

    def get_telemetry_snapshot(self) -> TelemetrySnapshot:
        with self.lock:
            current_time = time.time()
            time_delta = current_time - self.last_snapshot_time
            self.last_snapshot_time = current_time
            
            if time_delta == 0:
                alloc_rate = 0
                dealloc_rate = 0
            else:
                alloc_rate = self.total_allocated / time_delta
                dealloc_rate = self.total_deallocated / time_delta
            
            latencies = [e.latency for e in self.events]
            percentiles = {}
            if latencies:
                latencies.sort()
                for p in [50, 90, 95, 99]:
                    idx = int((p/100) * len(latencies))
                    if idx >= len(latencies):
                        idx = len(latencies) - 1
                    percentiles[f"p{p}"] = latencies[idx] if latencies else 0
            
            snapshot = TelemetrySnapshot(
                timestamp=current_time,
                total_allocated=self.total_allocated,
                allocation_rate=alloc_rate,
                deallocation_rate=dealloc_rate,
                contention_count=self.contention_events,
                latency_percentiles=percentiles
            )
            
            return snapshot

    def export_events(self) -> List[Dict]:
        with self.lock:
            return [asdict(event) for event in self.events]

collector = TelemetryCollector()

def trace_memory_operation(size: int, operation: str = "alloc", callstack: Optional[List[str]] = None):
    """Decorator to trace memory operations"""
    def decorator(func):
        def wrapper(*args, **kwargs):
            if operation == "alloc":
                with collector.trace_allocation(size, callstack):
                    return func(*args, **kwargs)
            elif operation == "dealloc":
                with collector.trace_deallocation(size):
                    return func(*args, **kwargs)
            else:
                return func(*args, **kwargs)
        return wrapper
    return decorator

def log_telemetry_snapshot():
    snapshot = collector.get_telemetry_snapshot()
    logger.info(f"Telemetry snapshot: {json.dumps(asdict(snapshot))}")
    return snapshot

def get_current_telemetry():
    return collector.get_telemetry_snapshot()

def export_telemetry_data() -> Dict:
    snapshot = collector.get_telemetry_snapshot()
    events = collector.export_events()
    
    return {
        "snapshot": asdict(snapshot),
        "events": events
    }