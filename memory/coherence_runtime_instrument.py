import time
import threading
from collections import deque
from typing import Dict, List, Tuple, Optional
import numpy as np
from dataclasses import dataclass

@dataclass
class SemanticFrame:
    language: str
    concepts: List[str]
    confidence: float
    timestamp: float

@dataclass
class CoherenceMetrics:
    transition_latency: float
    semantic_drift: float
    conceptual_load: float
    timestamp: float

class CoherenceRuntimeInstrument:
    def __init__(self, threshold_initial: float = 0.7, adaptation_rate: float = 0.01):
        self.threshold = threshold_initial
        self.adaptation_rate = adaptation_rate
        self.frame_history = deque(maxlen=100)
        self.metrics_history = deque(maxlen=1000)
        self.lock = threading.RLock()
        self.last_transition_time = None
        self.active_monitoring = False
        self.monitor_thread = None
        
    def start_monitoring(self):
        """Start the runtime monitoring thread"""
        with self.lock:
            if not self.active_monitoring:
                self.active_monitoring = True
                self.monitor_thread = threading.Thread(target=self._monitor_loop, daemon=True)
                self.monitor_thread.start()
    
    def stop_monitoring(self):
        """Stop the runtime monitoring"""
        with self.lock:
            self.active_monitoring = False
            if self.monitor_thread:
                self.monitor_thread.join()
    
    def record_semantic_frame(self, frame: SemanticFrame):
        """Record a semantic frame for analysis"""
        with self.lock:
            self.frame_history.append(frame)
            if len(self.frame_history) >= 2:
                self._analyze_coherence()
    
    def _analyze_coherence(self):
        """Analyze coherence between recent semantic frames"""
        if len(self.frame_history) < 2:
            return
            
        current = self.frame_history[-1]
        previous = self.frame_history[-2]
        
        # Skip if same language
        if current.language == previous.language:
            return
            
        # Calculate metrics
        latency = self._calculate_transition_latency(current, previous)
        drift = self._calculate_semantic_drift(current, previous)
        load = self._calculate_conceptual_load(current, previous)
        
        metrics = CoherenceMetrics(latency, drift, load, current.timestamp)
        self.metrics_history.append(metrics)
        
        # Check for misalignment
        coherence_score = self._calculate_coherence_score(metrics)
        if coherence_score < self.threshold:
            self._trigger_coherence_bridge(current, previous, coherence_score)
            self._adapt_threshold(coherence_score)
    
    def _calculate_transition_latency(self, current: SemanticFrame, previous: SemanticFrame) -> float:
        """Calculate time latency between language transitions"""
        if self.last_transition_time:
            return current.timestamp - self.last_transition_time
        return 0.0
    
    def _calculate_semantic_drift(self, current: SemanticFrame, previous: SemanticFrame) -> float:
        """Calculate semantic drift between frames using Jaccard similarity"""
        current_set = set(current.concepts)
        previous_set = set(previous.concepts)
        
        if not current_set and not previous_set:
            return 0.0
            
        intersection = len(current_set.intersection(previous_set))
        union = len(current_set.union(previous_set))
        
        if union == 0:
            return 1.0
            
        return 1.0 - (intersection / union)
    
    def _calculate_conceptual_load(self, current: SemanticFrame, previous: SemanticFrame) -> float:
        """Calculate conceptual load as complexity of translation"""
        # Load is inversely proportional to confidence and directly to concept count
        current_complexity = len(current.concepts) * (1.0 - current.confidence)
        previous_complexity = len(previous.concepts) * (1.0 - previous.confidence)
        
        return (current_complexity + previous_complexity) / 2.0
    
    def _calculate_coherence_score(self, metrics: CoherenceMetrics) -> float:
        """Calculate overall coherence score from metrics"""
        # Normalize metrics to 0-1 range
        normalized_latency = min(1.0, metrics.transition_latency / 2.0)  # Assume 2s threshold
        normalized_drift = metrics.semantic_drift
        normalized_load = min(1.0, metrics.conceptual_load / 10.0)  # Assume 10 concept threshold
        
        # Weighted combination - higher weight on semantic drift
        score = (
            0.3 * (1.0 - normalized_latency) +
            0.5 * (1.0 - normalized_drift) +
            0.2 * (1.0 - normalized_load)
        )
        
        return max(0.0, min(1.0, score))
    
    def _trigger_coherence_bridge(self, current: SemanticFrame, previous: SemanticFrame, coherence_score: float):
        """Trigger the coherence bridge when misalignment is detected"""
        print(f"COHERENCE ALERT: Misalignment detected between {previous.language} and {current.language}")
        print(f"  Coherence Score: {coherence_score:.3f} (threshold: {self.threshold:.3f})")
        print(f"  Semantic Drift: {self._calculate_semantic_drift(current, previous):.3f}")
        print(f"  Conceptual Load: {self._calculate_conceptual_load(current, previous):.3f}")
        
        # In a real implementation, this would trigger the actual coherence bridge
        self._activate_bridge_mechanism(current, previous)
    
    def _activate_bridge_mechanism(self, current: SemanticFrame, previous: SemanticFrame):
        """Activate the coherence bridge mechanism"""
        # Placeholder for actual bridge activation logic
        self.last_transition_time = time.time()
        pass
    
    def _adapt_threshold(self, coherence_score: float):
        """Dynamically adjust threshold based on performance"""
        error = coherence_score - self.threshold
        self.threshold = max(0.1, min(0.9, self.threshold + self.adaptation_rate * error))
    
    def _monitor_loop(self):
        """Main monitoring loop"""
        while self.active_monitoring:
            time.sleep(0.01)  # 10ms monitoring interval
            # Additional real-time monitoring logic could go here
    
    def get_metrics_summary(self) -> Dict[str, float]:
        """Get summary of recent metrics"""
        with self.lock:
            if not self.metrics_history:
                return {}
                
            latencies = [m.transition_latency for m in self.metrics_history]
            drifts = [m.semantic_drift for m in self.metrics_history]
            loads = [m.conceptual_load for m in self.metrics_history]
            
            return {
                'avg_latency': np.mean(latencies) if latencies else 0.0,
                'avg_drift': np.mean(drifts) if drifts else 0.0,
                'avg_load': np.mean(loads) if loads else 0.0,
                'threshold': self.threshold,
                'samples': len(self.metrics_history)
            }
    
    def reset_metrics(self):
        """Reset metrics history"""
        with self.lock:
            self.metrics_history.clear()
            self.frame_history.clear()
            self.last_transition_time = None