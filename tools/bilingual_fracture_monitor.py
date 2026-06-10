import json
import logging
import threading
import time
from collections import deque
from dataclasses import dataclass
from typing import Any, Callable, Dict, List, Optional, Tuple
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

@dataclass
class SemanticSnapshot:
    """Stores a snapshot of semantic state at a point in time"""
    timestamp: float
    english_text: str
    russian_text: str
    english_embedding: np.ndarray
    russian_embedding: np.ndarray
    metadata: Dict[str, Any]

class SemanticDivergenceMonitor:
    """Monitors semantic divergence between English and Russian language representations"""
    
    def __init__(self, divergence_threshold: float = 0.3, window_size: int = 10):
        self.divergence_threshold = divergence_threshold
        self.window_size = window_size
        self.semantic_history: deque = deque(maxlen=window_size)
        self.vectorizer = TfidfVectorizer(max_features=1000, stop_words=None)
        self._lock = threading.Lock()
        
    def calculate_semantic_similarity(self, english_text: str, russian_text: str) -> float:
        """Calculate cosine similarity between English and Russian texts"""
        try:
            # Vectorize texts
            vectors = self.vectorizer.fit_transform([english_text, russian_text])
            similarity = cosine_similarity(vectors[0], vectors[1])[0][0]
            return float(similarity)
        except Exception as e:
            logger.warning(f"Error calculating similarity: {e}")
            return 0.0
    
    def add_semantic_snapshot(self, english_text: str, russian_text: str, metadata: Dict[str, Any] = None) -> float:
        """Add a new semantic snapshot and return current divergence score"""
        with self._lock:
            # Calculate embeddings and similarity
            similarity = self.calculate_semantic_similarity(english_text, russian_text)
            divergence = 1.0 - similarity
            
            # Create snapshot
            snapshot = SemanticSnapshot(
                timestamp=time.time(),
                english_text=english_text,
                russian_text=russian_text,
                english_embedding=np.array([]),  # Placeholder for actual embeddings
                russian_embedding=np.array([]),
                metadata=metadata or {}
            )
            
            self.semantic_history.append(snapshot)
            return divergence

class ExecutionTracer:
    """Records detailed execution traces for fracture analysis"""
    
    def __init__(self):
        self.trace_events: List[Dict[str, Any]] = []
        self._lock = threading.Lock()
        
    def record_event(self, event_type: str, details: Dict[str, Any]):
        """Record a trace event"""
        with self._lock:
            trace_entry = {
                'timestamp': time.time(),
                'event_type': event_type,
                'details': details
            }
            self.trace_events.append(trace_entry)
            
    def get_trace_summary(self) -> Dict[str, Any]:
        """Get a summary of recorded trace events"""
        with self._lock:
            return {
                'total_events': len(self.trace_events),
                'event_types': list(set(event['event_type'] for event in self.trace_events)),
                'time_range': {
                    'start': min((e['timestamp'] for e in self.trace_events), default=0),
                    'end': max((e['timestamp'] for e in self.trace_events), default=0)
                }
            }
            
    def export_trace(self, filename: str):
        """Export trace to JSON file"""
        with self._lock:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(self.trace_events, f, indent=2, ensure_ascii=False)

class BilingualFractureMonitor:
    """Main monitor that combines semantic analysis with fracture detection"""
    
    def __init__(self, divergence_threshold: float = 0.3, window_size: int = 10):
        self.monitor = SemanticDivergenceMonitor(divergence_threshold, window_size)
        self.tracer = ExecutionTracer()
        self.fracture_callback: Optional[Callable] = None
        self.is_active = True
        self._monitor_thread: Optional[threading.Thread] = None
        
    def set_fracture_callback(self, callback: Callable):
        """Set callback function to be called when fracture is detected"""
        self.fracture_callback = callback
        
    def process_bilingual_pair(self, english_text: str, russian_text: str, metadata: Dict[str, Any] = None) -> bool:
        """Process a bilingual text pair and check for divergence"""
        # Record processing event
        self.tracer.record_event('processing_start', {
            'english_length': len(english_text),
            'russian_length': len(russian_text),
            'metadata': metadata
        })
        
        # Add to semantic monitoring
        divergence = self.monitor.add_semantic_snapshot(english_text, russian_text, metadata)
        
        # Check for fracture condition
        if divergence > self.monitor.divergence_threshold:
            self._trigger_fracture(english_text, russian_text, divergence, metadata)
            return False  # Indicates fracture occurred
        else:
            self.tracer.record_event('processing_complete', {
                'divergence': divergence,
                'status': 'normal'
            })
            return True  # Processing normal
            
    def _trigger_fracture(self, english_text: str, russian_text: str, divergence: float, metadata: Dict[str, Any]):
        """Trigger a fracture event"""
        fracture_details = {
            'divergence_score': divergence,
            'threshold': self.monitor.divergence_threshold,
            'english_text': english_text,
            'russian_text': russian_text,
            'semantic_history_length': len(self.monitor.semantic_history),
            'metadata': metadata
        }
        
        # Record fracture event
        self.tracer.record_event('fracture_detected', fracture_details)
        
        # Log fracture
        logger.warning(f"Semantic fracture detected! Divergence: {divergence:.3f} > {self.monitor.divergence_threshold:.3f}")
        
        # Execute callback if defined
        if self.fracture_callback:
            try:
                self.fracture_callback(fracture_details)
            except Exception as e:
                logger.error(f"Error in fracture callback: {e}")
                
    def start_monitoring(self):
        """Start background monitoring thread"""
        self.is_active = True
        self._monitor_thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self._monitor_thread.start()
        
    def stop_monitoring(self):
        """Stop background monitoring"""
        self.is_active = False
        if self._monitor_thread:
            self._monitor_thread.join()
            
    def _monitor_loop(self):
        """Background monitoring loop"""
        while self.is_active:
            # This could be extended to include periodic checks or cleanup
            time.sleep(0.1)
            
    def get_divergence_statistics(self) -> Dict[str, Any]:
        """Get statistics about monitored divergence"""
        with self.monitor._lock:
            if not self.monitor.semantic_history:
                return {'count': 0}
                
            divergences = []
            for i in range(1, len(self.monitor.semantic_history)):
                curr = self.monitor.semantic_history[i]
                prev = self.monitor.semantic_history[i-1]
                # Simplified divergence calculation for history
                div_sim = self.monitor.calculate_semantic_similarity(curr.english_text, curr.russian_text)
                divergences.append(1.0 - div_sim)
                
            if not divergences:
                return {'count': len(self.monitor.semantic_history)}
                
            return {
                'count': len(divergences),
                'mean_divergence': np.mean(divergences),
                'max_divergence': np.max(divergences),
                'min_divergence': np.min(divergences),
                'std_divergence': np.std(divergences)
            }

# Global instance for easy access
_global_monitor: Optional[BilingualFractureMonitor] = None

def initialize_monitor(divergence_threshold: float = 0.3, window_size: int = 10) -> BilingualFractureMonitor:
    """Initialize and return global monitor instance"""
    global _global_monitor
    if _global_monitor is None:
        _global_monitor = BilingualFractureMonitor(divergence_threshold, window_size)
    return _global_monitor

def get_monitor() -> Optional[BilingualFractureMonitor]:
    """Get the global monitor instance"""
    return _global_monitor

def monitor_bilingual_processing(english_text: str, russian_text: str, metadata: Dict[str, Any] = None) -> bool:
    """Convenience function to monitor a bilingual processing step"""
    monitor = get_monitor()
    if monitor:
        return monitor.process_bilingual_pair(english_text, russian_text, metadata)
    return True  # Default to success if no monitor

# Example usage and testing
if __name__ == "__main__":
    # Initialize monitor
    monitor = initialize_monitor(divergence_threshold=0.25)
    
    # Define fracture callback
    def on_fracture(details):
        print(f"FRacture ALERT: {details['divergence_score']:.3f} divergence")
        monitor.tracer.export_trace("fracture_trace.json")
    
    monitor.set_fracture_callback