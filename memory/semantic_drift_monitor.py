import numpy as np
import logging
from typing import Dict, List, Tuple
from datetime import datetime
from sklearn.metrics.pairwise import cosine_similarity

class SemanticDriftMonitor:
    def __init__(self, threshold: float = 0.7):
        self.threshold = threshold
        self.baseline_coherence = 1.0
        self.current_coherence = 1.0
        self.drift_events = []
        self.enforcement_actions = []
        self.logger = logging.getLogger(__name__)
        self._setup_logging()
        
    def _setup_logging(self):
        """Setup logging configuration for drift monitoring"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
    
    def compute_cross_language_coherence(self, 
                                       ru_embeddings: np.ndarray, 
                                       en_embeddings: np.ndarray) -> float:
        """
        Compute coherence score between Russian and English embeddings
        
        Args:
            ru_embeddings: Russian language embeddings (n_samples, embedding_dim)
            en_embeddings: English language embeddings (n_samples, embedding_dim)
            
        Returns:
            coherence_score: Average cosine similarity between corresponding embeddings
        """
        if len(ru_embeddings) != len(en_embeddings):
            raise ValueError("Russian and English embeddings must have same number of samples")
        
        if len(ru_embeddings) == 0:
            return 1.0
            
        # Compute cosine similarity between corresponding embeddings
        similarities = []
        for ru_emb, en_emb in zip(ru_embeddings, en_embeddings):
            # Reshape for sklearn compatibility
            ru_emb = ru_emb.reshape(1, -1)
            en_emb = en_emb.reshape(1, -1)
            similarity = cosine_similarity(ru_emb, en_emb)[0][0]
            similarities.append(similarity)
        
        coherence_score = float(np.mean(similarities))
        self.current_coherence = coherence_score
        
        return coherence_score
    
    def detect_drift(self, 
                    ru_embeddings: np.ndarray, 
                    en_embeddings: np.ndarray) -> bool:
        """
        Detect semantic drift based on cross-language coherence
        
        Args:
            ru_embeddings: Russian language embeddings
            en_embeddings: English language embeddings
            
        Returns:
            True if drift detected (coherence below threshold), False otherwise
        """
        try:
            coherence_score = self.compute_cross_language_coherence(ru_embeddings, en_embeddings)
            
            # Log the coherence measurement
            self.logger.info(f"Cross-language coherence score: {coherence_score:.4f}")
            
            # Check if coherence has dropped below threshold
            if coherence_score < self.threshold:
                drift_event = {
                    'timestamp': datetime.now(),
                    'coherence_score': coherence_score,
                    'threshold': self.threshold,
                    'status': 'DRIFT_DETECTED'
                }
                self.drift_events.append(drift_event)
                self.logger.warning(f"Semantic drift detected! Coherence: {coherence_score:.4f} < {self.threshold}")
                return True
            else:
                self.logger.info(f"Coherence within acceptable range: {coherence_score:.4f} >= {self.threshold}")
                return False
                
        except Exception as e:
            self.logger.error(f"Error in drift detection: {str(e)}")
            return False
    
    def enforce_boundaries(self, 
                          ru_embeddings: np.ndarray, 
                          en_embeddings: np.ndarray) -> Dict:
        """
        Enforce boundaries when semantic drift is detected
        
        Args:
            ru_embeddings: Russian language embeddings
            en_embeddings: English language embeddings
            
        Returns:
            Dictionary containing enforcement action details
        """
        action_details = {
            'timestamp': datetime.now(),
            'action_taken': False,
            'coherence_score': self.current_coherence,
            'details': None
        }
        
        if self.current_coherence < self.threshold:
            # Log the enforcement action
            self.logger.warning(f"Enforcing boundaries due to low coherence: {self.current_coherence:.4f}")
            
            # In a real implementation, this would contain actual boundary enforcement logic
            # For now, we'll just log the event and return status
            action_details['action_taken'] = True
            action_details['details'] = "Boundary enforcement triggered due to low cross-language coherence"
            
            # Record the enforcement action
            self.enforcement_actions.append(action_details)
            self.logger.info("Boundary enforcement completed")
        else:
            action_details['details'] = "No enforcement needed - coherence above threshold"
            self.logger.info("No boundary enforcement required")
            
        return action_details
    
    def get_drift_history(self) -> List[Dict]:
        """Return history of detected drift events"""
        return self.drift_events.copy()
    
    def get_enforcement_history(self) -> List[Dict]:
        """Return history of enforcement actions"""
        return self.enforcement_actions.copy()
    
    def reset_monitor(self):
        """Reset the monitor state"""
        self.current_coherence = 1.0
        self.drift_events.clear()
        self.enforcement_actions.clear()
        self.logger.info("Semantic drift monitor reset")