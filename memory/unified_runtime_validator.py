import logging
import traceback
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
from datetime import datetime
import numpy as np
from threading import Lock

@dataclass
class DivergenceEvent:
    timestamp: datetime
    russian_embedding: np.ndarray
    english_embedding: np.ndarray
    divergence_score: float
    stack_trace: str
    context: Dict[str, Any]

class UnifiedRuntimeValidator:
    def __init__(self, divergence_threshold: float = 0.1, debug_stream: Optional[str] = None):
        self.divergence_threshold = divergence_threshold
        self.debug_stream = debug_stream
        self.divergence_events: List[DivergenceEvent] = []
        self.lock = Lock()
        self.logger = self._setup_logger()
        self.coherence_hooks: List[callable] = []
        
    def _setup_logger(self) -> logging.Logger:
        logger = logging.getLogger('unified_runtime_validator')
        logger.setLevel(logging.DEBUG)
        handler = logging.StreamHandler()
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        return logger
    
    def add_coherence_hook(self, hook: callable) -> None:
        """Add a hook for real-time coherence scoring"""
        with self.lock:
            self.coherence_hooks.append(hook)
    
    def validate_embeddings(self, russian_emb: np.ndarray, english_emb: np.ndarray, 
                          context: Optional[Dict[str, Any]] = None) -> bool:
        """
        Validate embeddings for divergence and trigger events if necessary
        Returns True if embeddings are coherent, False otherwise
        """
        if context is None:
            context = {}
            
        try:
            # Calculate divergence score (cosine distance)
            divergence_score = self._calculate_divergence(russian_emb, english_emb)
            
            # Check for divergence event
            if divergence_score > self.divergence_threshold:
                self._handle_divergence_event(russian_emb, english_emb, divergence_score, context)
                return False
            
            # Run coherence hooks
            coherence_result = self._run_coherence_hooks(russian_emb, english_emb, context)
            return coherence_result
            
        except Exception as e:
            self.logger.error(f"Error during embedding validation: {str(e)}")
            return False
    
    def _calculate_divergence(self, russian_emb: np.ndarray, english_emb: np.ndarray) -> float:
        """Calculate divergence score between embeddings using cosine distance"""
        # Normalize embeddings
        russian_norm = russian_emb / np.linalg.norm(russian_emb)
        english_norm = english_emb / np.linalg.norm(english_emb)
        
        # Cosine similarity
        cosine_sim = np.dot(russian_norm, english_norm)
        
        # Cosine distance (divergence)
        return 1.0 - cosine_sim
    
    def _handle_divergence_event(self, russian_emb: np.ndarray, english_emb: np.ndarray, 
                               divergence_score: float, context: Dict[str, Any]) -> None:
        """Handle divergence event by logging and storing it"""
        # Capture full stack trace
        stack_trace = traceback.format_stack()
        full_trace = ''.join(stack_trace)
        
        # Create divergence event
        event = DivergenceEvent(
            timestamp=datetime.now(),
            russian_embedding=russian_emb.copy(),
            english_embedding=english_emb.copy(),
            divergence_score=divergence_score,
            stack_trace=full_trace,
            context=context
        )
        
        # Store event
        with self.lock:
            self.divergence_events.append(event)
        
        # Log event
        self.logger.warning(f"Divergence detected: score={divergence_score:.4f}")
        self.logger.debug(f"Stack trace:\n{full_trace}")
        
        # Write to debug stream if configured
        if self.debug_stream:
            self._write_to_debug_stream(event)
    
    def _write_to_debug_stream(self, event: DivergenceEvent) -> None:
        """Write divergence event to debug stream"""
        try:
            debug_info = {
                'timestamp': event.timestamp.isoformat(),
                'divergence_score': event.divergence_score,
                'stack_trace': event.stack_trace,
                'context': event.context
            }
            
            # In a real implementation, this would write to a file or stream
            with open(self.debug_stream, 'a') as f:
                f.write(f"{debug_info}\n")
                
        except Exception as e:
            self.logger.error(f"Failed to write to debug stream: {str(e)}")
    
    def _run_coherence_hooks(self, russian_emb: np.ndarray, english_emb: np.ndarray, 
                           context: Dict[str, Any]) -> bool:
        """Run all registered coherence hooks"""
        try:
            for hook in self.coherence_hooks:
                result = hook(russian_emb, english_emb, context)
                if not result:  # If any hook returns False, embeddings are not coherent
                    return False
            return True
        except Exception as e:
            self.logger.error(f"Error in coherence hook: {str(e)}")
            return False
    
    def get_divergence_events(self) -> List[DivergenceEvent]:
        """Get all recorded divergence events"""
        with self.lock:
            return self.divergence_events.copy()
    
    def clear_events(self) -> None:
        """Clear all recorded divergence events"""
        with self.lock:
            self.divergence_events.clear()
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get statistics about divergence events"""
        with self.lock:
            if not self.divergence_events:
                return {
                    'total_events': 0,
                    'max_divergence': 0.0,
                    'avg_divergence': 0.0,
                    'recent_events': []
                }
            
            scores = [event.divergence_score for event in self.divergence_events]
            recent_events = sorted(self.divergence_events, 
                                 key=lambda x: x.timestamp, reverse=True)[:10]
            
            return {
                'total_events': len(self.divergence_events),
                'max_divergence': max(scores),
                'avg_divergence': sum(scores) / len(scores),
                'recent_events': [
                    {
                        'timestamp': event.timestamp.isoformat(),
                        'divergence_score': event.divergence_score,
                        'context': event.context
                    }
                    for event in recent_events
                ]
            }

# Example coherence hook function
def example_coherence_hook(russian_emb: np.ndarray, english_emb: np.ndarray, 
                          context: Dict[str, Any]) -> bool:
    """Example hook that checks if embeddings have similar magnitude"""
    russian_mag = np.linalg.norm(russian_emb)
    english_mag = np.linalg.norm(english_emb)
    
    # If magnitude difference is too large, embeddings may be incoherent
    magnitude_ratio = min(russian_mag, english_mag) / max(russian_mag, english_mag)
    return magnitude_ratio > 0.5  # Return True if coherent

# Usage example:
# validator = UnifiedRuntimeValidator(divergence_threshold=0.15, debug_stream="divergence.log")
# validator.add_coherence_hook(example_coherence_hook)
# 
# # Validate embeddings
# russian_vector = np.random.rand(300)
# english_vector = np.random.rand(300)
# is_coherent = validator.validate_embeddings(russian_vector, english_vector, {"source": "test"})