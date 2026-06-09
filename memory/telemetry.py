import time
import threading
from collections import defaultdict, deque
from typing import Dict, List, Optional, Tuple
import psutil
import numpy as np
from dataclasses import dataclass, field
from datetime import datetime

@dataclass
class CoherenceMetrics:
    """Container for real-time coherence scoring metrics"""
    timestamp: datetime
    memory_fragmentation: float
    intentionality_score: float
    modification_efficiency: float
    cognitive_load: float
    coherence_score: float

class TelemetrySystem:
    """Enhanced telemetry system with real-time coherence scoring"""
    
    def __init__(self, window_size: int = 100):
        self.window_size = window_size
        self.metrics_history: deque = deque(maxlen=window_size)
        self.fragmentation_history: deque = deque(maxlen=window_size)
        self.intentionality_patterns: Dict[str, List[float]] = defaultdict(list)
        self.modification_events: List[Dict] = []
        self.monitoring_active = False
        self.monitor_thread: Optional[threading.Thread] = None
        self.lock = threading.RLock()
        
    def start_monitoring(self):
        """Start real-time monitoring in background thread"""
        if not self.monitoring_active:
            self.monitoring_active = True
            self.monitor_thread = threading.Thread(target=self._monitor_loop, daemon=True)
            self.monitor_thread.start()
    
    def stop_monitoring(self):
        """Stop real-time monitoring"""
        self.monitoring_active = False
        if self.monitor_thread:
            self.monitor_thread.join()
    
    def _monitor_loop(self):
        """Background monitoring loop"""
        while self.monitoring_active:
            try:
                metrics = self._collect_metrics()
                self._update_metrics_history(metrics)
                time.sleep(0.1)  # 100ms sampling rate
            except Exception:
                pass  # Silent failure to prevent monitoring interruption
    
    def _collect_metrics(self) -> CoherenceMetrics:
        """Collect current system metrics for coherence scoring"""
        # Memory fragmentation measurement
        fragmentation = self._calculate_fragmentation()
        
        # Intentionality pattern analysis
        intentionality = self._analyze_intentionality()
        
        # Modification efficiency tracking
        efficiency = self._calculate_modification_efficiency()
        
        # Cognitive load estimation
        cognitive_load = self._estimate_cognitive_load()
        
        # Overall coherence score
        coherence = self._calculate_coherence_score(
            fragmentation, intentionality, efficiency, cognitive_load
        )
        
        return CoherenceMetrics(
            timestamp=datetime.now(),
            memory_fragmentation=fragmentation,
            intentionality_score=intentionality,
            modification_efficiency=efficiency,
            cognitive_load=cognitive_load,
            coherence_score=coherence
        )
    
    def _calculate_fragmentation(self) -> float:
        """Calculate memory fragmentation ratio (0-1)"""
        try:
            # Get memory info from process
            process = psutil.Process()
            mem_info = process.memory_info()
            
            # Estimate fragmentation based on memory usage patterns
            rss = mem_info.rss
            vms = mem_info.vms
            
            if vms == 0:
                return 0.0
                
            # Fragmentation as ratio of allocated but unused virtual memory
            fragmentation = 1.0 - (rss / vms)
            return max(0.0, min(1.0, fragmentation))
        except:
            return 0.0
    
    def _analyze_intentionality(self) -> float:
        """Analyze intentionality patterns in self-modification (0-1)"""
        if not self.modification_events:
            return 0.5  # Neutral baseline
            
        # Calculate consistency of modification patterns
        recent_events = self.modification_events[-50:]  # Last 50 events
        
        if len(recent_events) < 2:
            return 0.5
            
        # Measure temporal consistency and goal alignment
        consistency_scores = []
        for i in range(1, len(recent_events)):
            current = recent_events[i]
            previous = recent_events[i-1]
            
            # Check if modifications are building on each other
            if 'target' in current and 'target' in previous:
                # Simple string similarity for intentionality
                target_current = str(current.get('target', ''))
                target_previous = str(previous.get('target', ''))
                similarity = self._string_similarity(target_current, target_previous)
                consistency_scores.append(similarity)
        
        if consistency_scores:
            return np.mean(consistency_scores)
        return 0.5
    
    def _string_similarity(self, s1: str, s2: str) -> float:
        """Calculate simple string similarity ratio"""
        if not s1 and not s2:
            return 1.0
        if not s1 or not s2:
            return 0.0
            
        # Convert to sets of characters for comparison
        set1, set2 = set(s1), set(s2)
        intersection = set1.intersection(set2)
        union = set1.union(set2)
        
        if not union:
            return 1.0
            
        return len(intersection) / len(union)
    
    def _calculate_modification_efficiency(self) -> float:
        """Calculate efficiency of recent modifications (0-1)"""
        if not self.modification_events:
            return 1.0  # No modifications = perfect efficiency
            
        recent_events = self.modification_events[-20:]
        if not recent_events:
            return 1.0
            
        # Efficiency based on success rate and resource usage
        successful_modifications = [
            event for event in recent_events 
            if event.get('success', False)
        ]
        
        success_rate = len(successful_modifications) / len(recent_events)
        
        # Adjust for complexity of modifications
        complexity_scores = [
            event.get('complexity', 1.0) 
            for event in successful_modifications
        ]
        
        if complexity_scores:
            avg_complexity = np.mean(complexity_scores)
            # Higher complexity reduces efficiency score
            efficiency = success_rate * (1.0 / (1.0 + avg_complexity * 0.1))
            return max(0.0, min(1.0, efficiency))
        
        return success_rate
    
    def _estimate_cognitive_load(self) -> float:
        """Estimate current cognitive load based on system activity (0-1)"""
        try:
            # CPU usage as proxy for cognitive load
            cpu_percent = psutil.cpu_percent(interval=0.1)
            
            # Memory pressure
            memory = psutil.virtual_memory()
            memory_pressure = memory.percent / 100.0
            
            # Process count as complexity measure
            process_count = len(psutil.pids())
            process_normalized = min(1.0, process_count / 1000.0)
            
            # Combine metrics (weighted average)
            load = (
                cpu_percent * 0.5 + 
                memory_pressure * 0.3 + 
                process_normalized * 0.2
            ) / 100.0
            
            return max(0.0, min(1.0, load))
        except:
            return 0.3  # Default moderate load
    
    def _calculate_coherence_score(self, frag: float, intent: float, 
                                eff: float, load: float) -> float:
        """Calculate overall coherence score from component metrics"""
        # Weighted combination favoring intentionality and efficiency
        coherence = (
            (1.0 - frag) * 0.2 +      # Lower fragmentation is better
            intent * 0.3 +            # Higher intentionality is better
            eff * 0.3 +               # Higher efficiency is better
            (1.0 - load) * 0.2        # Lower cognitive load is better
        )
        return max(0.0, min(1.0, coherence))
    
    def _update_metrics_history(self, metrics: CoherenceMetrics):
        """Update historical metrics tracking"""
        with self.lock:
            self.metrics_history.append(metrics)
            self.fragmentation_history.append(metrics.memory_fragmentation)
    
    def record_modification(self, event_data: Dict):
        """Record a self-modification event for analysis"""
        with self.lock:
            event_data['timestamp'] = datetime.now()
            self.modification_events.append(event_data)
            
            # Keep only recent events
            if len(self.modification_events) > 1000:
                self.modification_events = self.modification_events[-1000:]
    
    def get_current_coherence(self) -> Optional[CoherenceMetrics]:
        """Get most recent coherence metrics"""
        with self.lock:
            if self.metrics_history:
                return self.metrics_history[-1]
            return None
    
    def get_coherence_trend(self, window: int = 10) -> List[CoherenceMetrics]:
        """Get recent coherence trend data"""
        with self.lock:
            if len(self.metrics_history) >= window:
                return list(self.metrics_history)[-window:]
            return list(self.metrics_history)
    
    def get_actionable_insights(self) -> Dict[str, str]:
        """Generate actionable optimization insights"""
        current = self.get_current_coherence()
        if not current:
            return {"status": "No data available"}
        
        insights = {}
        
        # Fragmentation insight
        if current.memory_fragmentation > 0.7:
            insights['fragmentation'] = "