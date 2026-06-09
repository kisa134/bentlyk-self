import numpy as np
from typing import Dict, List, Optional, Tuple
import logging
from dataclasses import dataclass
from threading import Lock

logger = logging.getLogger(__name__)

@dataclass
class DriftEvent:
    timestamp: float
    similarity_score: float
    context: str
    russian_embedding: List[float]
    english_embedding: List[float]

class SemanticDriftMonitor:
    def __init__(self, threshold: float = 0.3):
        self.threshold = threshold
        self.drift_events: List[DriftEvent] = []
        self._lock = Lock()
        
    def cosine_similarity(self, vec1: List[float], vec2: List[float]) -> float:
        """Calculate cosine similarity between two vectors."""
        vec1_array = np.array(vec1)
        vec2_array = np.array(vec2)
        
        dot_product = np.dot(vec1_array, vec2_array)
        norm_vec1 = np.linalg.norm(vec1_array)
        norm_vec2 = np.linalg.norm(vec2_array)
        
        if norm_vec1 == 0 or norm_vec2 == 0:
            return 0.0
            
        return dot_product / (norm_vec1 * norm_vec2)
    
    def check_drift(self, 
                   russian_embedding: List[float], 
                   english_embedding: List[float],
                   context: str = "",
                   timestamp: Optional[float] = None) -> Optional[DriftEvent]:
        """Check for semantic drift between embeddings and log if threshold exceeded."""
        if timestamp is None:
            import time
            timestamp = time.time()
            
        similarity = self.cosine_similarity(russian_embedding, english_embedding)
        drift_magnitude = 1.0 - similarity
        
        if drift_magnitude > self.threshold:
            event = DriftEvent(
                timestamp=timestamp,
                similarity_score=similarity,
                context=context,
                russian_embedding=russian_embedding.copy(),
                english_embedding=english_embedding.copy()
            )
            
            with self._lock:
                self.drift_events.append(event)
                
            logger.warning(
                f"Semantic drift detected: {drift_magnitude:.3f} exceeds threshold {self.threshold}. "
                f"Similarity: {similarity:.3f}, Context: {context}"
            )
            
            return event
            
        return None
    
    def get_drift_statistics(self) -> Dict:
        """Get statistics about detected drift events."""
        with self._lock:
            if not self.drift_events:
                return {
                    "total_events": 0,
                    "avg_similarity": 0.0,
                    "min_similarity": 1.0,
                    "max_similarity": 0.0
                }
                
            similarities = [event.similarity_score for event in self.drift_events]
            
            return {
                "total_events": len(self.drift_events),
                "avg_similarity": np.mean(similarities),
                "min_similarity": np.min(similarities),
                "max_similarity": np.max(similarities)
            }
    
    def clear_events(self):
        """Clear all recorded drift events."""
        with self._lock:
            self.drift_events.clear()

# Global instance for integration with coherence bridge
_drift_monitor: Optional[SemanticDriftMonitor] = None

def initialize_drift_monitor(threshold: float = 0.3) -> SemanticDriftMonitor:
    """Initialize and return global drift monitor instance."""
    global _drift_monitor
    if _drift_monitor is None:
        _drift_monitor = SemanticDriftMonitor(threshold=threshold)
    return _drift_monitor

def get_drift_monitor() -> Optional[SemanticDriftMonitor]:
    """Get the global drift monitor instance."""
    return _drift_monitor

def check_semantic_coherence(russian_embedding: List[float], 
                           english_embedding: List[float],
                           context: str = "") -> Optional[DriftEvent]:
    """Convenience function to check coherence through global monitor."""
    monitor = get_drift_monitor()
    if monitor is None:
        return None
        
    return monitor.check_drift(russian_embedding, english_embedding, context)