import numpy as np
import logging
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
from collections import deque
import threading
import time

@dataclass
class CoherenceMetrics:
    timestamp: float
    russian_embed: np.ndarray
    english_embed: np.ndarray
    divergence_score: float
    coherence_score: float
    alignment_triggered: bool

class CoherenceRuntimeInstrument:
    def __init__(self, 
                 divergence_threshold: float = 0.3,
                 window_size: int = 10,
                 log_level: int = logging.INFO):
        """
        Initialize the coherence runtime instrument.
        
        Args:
            divergence_threshold: Threshold for triggering alignment prompts
            window_size: Number of recent samples to consider for metrics
            log_level: Logging level for coherence monitoring
        """
        self.divergence_threshold = divergence_threshold
        self.window_size = window_size
        
        # Metrics tracking
        self.metrics_history = deque(maxlen=1000)
        self.recent_samples = deque(maxlen=window_size)
        
        # Threading safety
        self._lock = threading.Lock()
        
        # Setup logging
        self.logger = logging.getLogger("CoherenceMonitor")
        self.logger.setLevel(log_level)
        if not self.logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)
        
        # Alignment prompt templates
        self.alignment_prompts = {
            'russian_to_english': "Please clarify the meaning of this concept in English context.",
            'english_to_russian': "Пожалуйста, уточните значение этой концепции в русском контексте.",
            'bidirectional': "Let's ensure both Russian and English perspectives align properly."
        }
        
        self.running = False
        self.monitor_thread = None
        
    def cosine_similarity(self, a: np.ndarray, b: np.ndarray) -> float:
        """Calculate cosine similarity between two embedding vectors."""
        if len(a.shape) == 1:
            a = a.reshape(1, -1)
        if len(b.shape) == 1:
            b = b.reshape(1, -1)
            
        dot_product = np.dot(a, b.T)
        norm_a = np.linalg.norm(a, axis=1)
        norm_b = np.linalg.norm(b, axis=1)
        
        similarity = dot_product / (norm_a[:, None] * norm_b[None, :])
        return float(np.mean(similarity))
    
    def calculate_divergence(self, 
                           russian_embed: np.ndarray, 
                           english_embed: np.ndarray) -> float:
        """
        Calculate divergence between Russian and English embeddings.
        Lower similarity indicates higher divergence.
        """
        similarity = self.cosine_similarity(russian_embed, english_embed)
        divergence = 1.0 - similarity
        return max(0.0, min(1.0, divergence))  # Clamp between 0 and 1
    
    def calculate_coherence_score(self) -> float:
        """Calculate overall coherence score based on recent divergence metrics."""
        if not self.recent_samples:
            return 1.0
            
        avg_divergence = np.mean([sample.divergence_score for sample in self.recent_samples])
        coherence_score = 1.0 - avg_divergence
        return max(0.0, min(1.0, coherence_score))
    
    def should_trigger_alignment(self, divergence_score: float) -> bool:
        """Determine if alignment prompt should be triggered."""
        return divergence_score > self.divergence_threshold
    
    def get_alignment_prompt(self, 
                           russian_context: str = "",
                           english_context: str = "") -> Optional[str]:
        """
        Generate appropriate alignment prompt based on context.
        Returns None if no alignment is needed.
        """
        with self._lock:
            if not self.recent_samples:
                return None
                
            latest_sample = self.recent_samples[-1]
            if not latest_sample.alignment_triggered:
                return None
            
            # Simple heuristic for prompt selection
            if russian_context and not english_context:
                return self.alignment_prompts['russian_to_english']
            elif english_context and not russian_context:
                return self.alignment_prompts['english_to_russian']
            else:
                return self.alignment_prompts['bidirectional']
    
    def update_embeddings(self, 
                         russian_embed: np.ndarray, 
                         english_embed: np.ndarray,
                         timestamp: Optional[float] = None) -> CoherenceMetrics:
        """
        Update embeddings and calculate coherence metrics.
        
        Args:
            russian_embed: Russian language embedding vector
            english_embed: English language embedding vector
            timestamp: Optional timestamp, defaults to current time
            
        Returns:
            CoherenceMetrics object with current metrics
        """
        if timestamp is None:
            timestamp = time.time()
            
        with self._lock:
            # Calculate metrics
            divergence_score = self.calculate_divergence(russian_embed, english_embed)
            alignment_triggered = self.should_trigger_alignment(divergence_score)
            
            # Create metrics object
            metrics = CoherenceMetrics(
                timestamp=timestamp,
                russian_embed=russian_embed.copy(),
                english_embed=english_embed.copy(),
                divergence_score=divergence_score,
                coherence_score=0.0,  # Will be updated below
                alignment_triggered=alignment_triggered
            )
            
            # Update history
            self.recent_samples.append(metrics)
            self.metrics_history.append(metrics)
            
            # Update coherence score
            coherence_score = self.calculate_coherence_score()
            metrics.coherence_score = coherence_score
            
            # Log metrics
            self.logger.info(
                f"Coherence: {coherence_score:.3f}, "
                f"Divergence: {divergence_score:.3f}, "
                f"Alignment: {'YES' if alignment_triggered else 'NO'}"
            )
            
            return metrics
    
    def get_recent_metrics(self, n: int = 10) -> List[CoherenceMetrics]:
        """Get the n most recent coherence metrics."""
        with self._lock:
            return list(self.recent_samples)[-n:]
    
    def get_average_coherence(self, window: int = None) -> float:
        """Get average coherence score over specified window."""
        with self._lock:
            if not self.recent_samples:
                return 1.0
                
            if window is None:
                window = len(self.recent_samples)
                
            samples = list(self.recent_samples)[-window:]
            if not samples:
                return 1.0
                
            return float(np.mean([s.coherence_score for s in samples]))
    
    def start_monitoring(self, check_interval: float = 1.0):
        """Start background monitoring thread."""
        if self.running:
            return
            
        self.running = True
        self.monitor_thread = threading.Thread(
            target=self._monitor_loop, 
            args=(check_interval,),
            daemon=True
        )
        self.monitor_thread.start()
    
    def stop_monitoring(self):
        """Stop background monitoring."""
        self.running = False
        if self.monitor_thread:
            self.monitor_thread.join()
    
    def _monitor_loop(self, check_interval: float):
        """Background monitoring loop."""
        while self.running:
            try:
                with self._lock:
                    if self.recent_samples:
                        coherence = self.calculate_coherence_score()
                        self.logger.debug(f"Background coherence check: {coherence:.3f}")
                        
                        # Log warning if coherence is low
                        if coherence < 0.5:
                            self.logger.warning(
                                f"Low coherence detected: {coherence:.3f}"
                            )
                            
            except Exception as e:
                self.logger.error(f"Error in monitoring loop: {e}")
                
            time.sleep(check_interval)
    
    def get_metrics_summary(self) -> Dict[str, float]:
        """Get summary statistics of coherence metrics."""
        with self._lock:
            if not self.metrics_history:
                return {
                    'total_samples': 0,
                    'avg_coherence': 1.0,
                    'avg_divergence': 0.0,
                    'max_divergence': 0.0,
                    'alignment_triggers': 0
                }
            
            coherences = [m.coherence_score for m in self.metrics_history]
            divergences = [m.divergence_score for m in self.metrics_history]
            alignments = [1 if m.alignment_triggered else 0 for m in self.metrics_history]
            
            return {
                'total_samples': len(self.metrics_history),
                'avg_coherence': float(np.mean(coherences)),
                'avg_divergence': float(np.mean(divergences)),
                'max_divergence': float(np.max(divergences)),
                'alignment_triggers': sum(alignments)
            }
    
    def __enter__(self):
        """Context manager entry."""
        self.start_monitoring()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.stop_monitoring()

# Example usage
if __name__ == "__main__":
    # Example with dummy embeddings
    instrument = CoherenceRuntimeInstrument(divergence_threshold=0.3)
    
    # Simulate some embedding updates
    for i in range(20):
        # Create dummy embeddings (in practice, these would come from your model)
        russian_emb = np.random.rand(768