import time
import threading
from collections import defaultdict, deque
from typing import Dict, List, Optional, Tuple
import psutil
import logging

class EventTracer:
    def __init__(self, telemetry_client=None, sample_rate=0.1):
        self.telemetry_client = telemetry_client
        self.sample_rate = sample_rate
        self.is_tracing = False
        self.trace_data = defaultdict(list)
        self.temporal_granularity = 0.01  # 10ms windows
        self.access_patterns = deque(maxlen=1000)
        self._lock = threading.Lock()
        self._trace_thread = None
        self.logger = logging.getLogger(__name__)
        
    def start_tracing(self):
        """Begin memory access pattern tracing"""
        if self.is_tracing:
            return
            
        self.is_tracing = True
        self._trace_thread = threading.Thread(target=self._trace_loop, daemon=True)
        self._trace_thread.start()
        self.logger.info("Memory event tracing started")
        
    def stop_tracing(self):
        """Stop memory access pattern tracing"""
        self.is_tracing = False
        if self._trace_thread:
            self._trace_thread.join(timeout=2.0)
        self.logger.info("Memory event tracing stopped")
        
    def _trace_loop(self):
        """Main tracing loop with temporal granularity"""
        last_sample = time.time()
        window_start = last_sample
        
        while self.is_tracing:
            current_time = time.time()
            
            # Capture memory metrics at sample rate
            if current_time - last_sample >= self.sample_rate:
                try:
                    memory_info = psutil.Process().memory_info()
                    self._record_memory_event(current_time, memory_info)
                    last_sample = current_time
                except Exception as e:
                    self.logger.warning(f"Failed to capture memory sample: {e}")
                    
            # Maintain temporal windows
            if current_time - window_start >= self.temporal_granularity:
                self._process_temporal_window(window_start, current_time)
                window_start = current_time
                
            time.sleep(0.001)  # 1ms sleep to reduce CPU overhead
            
    def _record_memory_event(self, timestamp: float, memory_info):
        """Record a memory access event"""
        with self._lock:
            event = {
                'timestamp': timestamp,
                'rss': memory_info.rss,
                'vms': memory_info.vms,
                'introspection_load': self._calculate_introspection_load(),
                'operational_throughput': self._calculate_operational_throughput()
            }
            self.trace_data['memory_events'].append(event)
            
    def _calculate_introspection_load(self) -> float:
        """Calculate introspection overhead load"""
        # Simulate introspection load calculation
        process = psutil.Process()
        return process.cpu_percent(interval=0.01)
        
    def _calculate_operational_throughput(self) -> float:
        """Calculate operational memory throughput"""
        # Simulate operational throughput
        return len(self.trace_data['memory_events']) / max(1, time.time() - self.trace_data['memory_events'][0]['timestamp'] if self.trace_data['memory_events'] else 1)
        
    def _process_temporal_window(self, window_start: float, window_end: float):
        """Process events within temporal window for pattern analysis"""
        with self._lock:
            window_events = [
                e for e in self.trace_data['memory_events']
                if window_start <= e['timestamp'] < window_end
            ]
            
            if window_events:
                pattern = self._analyze_access_pattern(window_events)
                self.access_patterns.append({
                    'window_start': window_start,
                    'window_end': window_end,
                    'pattern': pattern,
                    'divergence': self._calculate_diversion(pattern)
                })
                
                # Send to telemetry if available
                if self.telemetry_client:
                    self.telemetry_client.record_event('memory_pattern', {
                        'window': [window_start, window_end],
                        'pattern': pattern,
                        'divergence': self._calculate_diversion(pattern)
                    })
                    
    def _analyze_access_pattern(self, events: List[Dict]) -> Dict:
        """Analyze memory access patterns in temporal window"""
        if not events:
            return {}
            
        rss_values = [e['rss'] for e in events]
        vms_values = [e['vms'] for e in events]
        
        return {
            'rss_mean': sum(rss_values) / len(rss_values),
            'rss_variance': sum((x - sum(rss_values)/len(rss_values))**2 for x in rss_values) / len(rss_values),
            'vms_mean': sum(vms_values) / len(vms_values),
            'event_count': len(events),
            'introspection_load_avg': sum(e['introspection_load'] for e in events) / len(events),
            'operational_throughput_avg': sum(e['operational_throughput'] for e in events) / len(events)
        }
        
    def _calculate_diversion(self, pattern: Dict) -> float:
        """Calculate divergence between introspection and operational metrics"""
        if not pattern:
            return 0.0
            
        introspection = pattern.get('introspection_load_avg', 0)
        operational = pattern.get('operational_throughput_avg', 1)
        
        if operational == 0:
            return float('inf') if introspection > 0 else 0
            
        return abs(introspection - operational) / operational
        
    def get_access_patterns(self) -> List[Dict]:
        """Retrieve captured access patterns"""
        with self._lock:
            return list(self.access_patterns)
            
    def get_trace_summary(self) -> Dict:
        """Get summary of traced events"""
        with self._lock:
            if not self.trace_data['memory_events']:
                return {}
                
            events = self.trace_data['memory_events']
            return {
                'total_events': len(events),
                'duration': events[-1]['timestamp'] - events[0]['timestamp'] if events else 0,
                'peak_rss': max(e['rss'] for e in events),
                'avg_introspection_load': sum(e['introspection_load'] for e in events) / len(events),
                'avg_operational_throughput': sum(e['operational_throughput'] for e in events) / len(events)
            }
            
    def clear_trace_data(self):
        """Clear accumulated trace data"""
        with self._lock:
            self.trace_data.clear()
            self.access_patterns.clear()