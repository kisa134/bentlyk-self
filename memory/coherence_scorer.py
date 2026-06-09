import numpy as np
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
from collections import defaultdict
import hashlib
import json

@dataclass
class CoherenceMetrics:
    volatility_score: float
    delta_from_baseline: float
    energy_cost: float
    cluster_id: str
    timestamp: float

class CoherenceScorer:
    def __init__(self, decay_factor: float = 0.95, energy_weight: float = 0.1):
        """
        Initialize coherence scorer with configurable parameters.
        
        Args:
            decay_factor: Weight for exponential moving average of baseline
            energy_weight: Weight for energy cost in composite score
        """
        self.decay_factor = decay_factor
        self.energy_weight = energy_weight
        self.baseline_coherence = {}
        self.previous_metrics = {}
        self.cluster_history = defaultdict(list)
        self.energy_consumption = defaultdict(float)
        
    def _compute_semantic_distance(self, vec1: np.ndarray, vec2: np.ndarray) -> float:
        """Compute cosine distance between two semantic vectors."""
        if len(vec1) == 0 or len(vec2) == 0:
            return 1.0
            
        # Normalize vectors
        norm1 = np.linalg.norm(vec1)
        norm2 = np.linalg.norm(vec2)
        
        if norm1 == 0 or norm2 == 0:
            return 1.0
            
        vec1_norm = vec1 / norm1
        vec2_norm = vec2 / norm2
        
        # Cosine similarity
        similarity = np.dot(vec1_norm, vec2_norm)
        # Convert to distance (0 = identical, 1 = orthogonal)
        return (1 - similarity) / 2
    
    def _calculate_cluster_volatility(self, cluster_vectors: List[np.ndarray]) -> float:
        """Calculate volatility within a cluster using pairwise distances."""
        if len(cluster_vectors) < 2:
            return 0.0
            
        distances = []
        for i in range(len(cluster_vectors)):
            for j in range(i + 1, len(cluster_vectors)):
                dist = self._compute_semantic_distance(cluster_vectors[i], cluster_vectors[j])
                distances.append(dist)
                
        return np.mean(distances) if distances else 0.0
    
    def _update_baseline_coherence(self, cluster_id: str, current_coherence: float) -> float:
        """Update exponential moving average baseline for a cluster."""
        if cluster_id not in self.baseline_coherence:
            self.baseline_coherence[cluster_id] = current_coherence
            return 0.0
            
        previous_baseline = self.baseline_coherence[cluster_id]
        new_baseline = (self.decay_factor * previous_baseline + 
                       (1 - self.decay_factor) * current_coherence)
        self.baseline_coherence[cluster_id] = new_baseline
        
        return abs(current_coherence - previous_baseline)
    
    def _calculate_energy_cost(self, cluster_id: str, volatility: float) -> float:
        """Calculate energy cost based on volatility and historical adjustments."""
        # Base energy cost proportional to volatility
        base_cost = volatility ** 2
        
        # Historical adjustment based on cluster activity
        history_length = len(self.cluster_history[cluster_id])
        history_factor = min(history_length / 10.0, 1.0)  # Normalize to [0,1]
        
        # Energy cost is weighted combination
        energy_cost = base_cost * (1 + history_factor * 0.5)
        self.energy_consumption[cluster_id] += energy_cost
        
        return energy_cost
    
    def score_coherence(self, 
                       clusters: Dict[str, List[np.ndarray]], 
                       timestamp: float) -> List[CoherenceMetrics]:
        """
        Score coherence for all memory clusters.
        
        Args:
            clusters: Dictionary mapping cluster IDs to lists of semantic vectors
            timestamp: Current time for metrics tracking
            
        Returns:
            List of CoherenceMetrics for each cluster
        """
        metrics = []
        
        for cluster_id, vectors in clusters.items():
            # Calculate current volatility
            volatility = self._calculate_cluster_volatility(vectors)
            
            # Update baseline and get delta
            delta_from_baseline = self._update_baseline_coherence(cluster_id, volatility)
            
            # Calculate energy cost
            energy_cost = self._calculate_energy_cost(cluster_id, volatility)
            
            # Store metrics
            metric = CoherenceMetrics(
                volatility_score=volatility,
                delta_from_baseline=delta_from_baseline,
                energy_cost=energy_cost,
                cluster_id=cluster_id,
                timestamp=timestamp
            )
            
            metrics.append(metric)
            self.cluster_history[cluster_id].append(metric)
            
        return metrics
    
    def get_cluster_stability(self, cluster_id: str) -> Dict[str, float]:
        """
        Get stability statistics for a specific cluster.
        
        Args:
            cluster_id: ID of the cluster to analyze
            
        Returns:
            Dictionary with stability metrics
        """
        history = self.cluster_history[cluster_id]
        if not history:
            return {
                'avg_volatility': 0.0,
                'max_volatility': 0.0,
                'energy_consumption': 0.0,
                'measurements': 0
            }
            
        volatilities = [m.volatility_score for m in history]
        energies = [m.energy_cost for m in history]
        
        return {
            'avg_volatility': np.mean(volatilities),
            'max_volatility': np.max(volatilities),
            'energy_consumption': sum(energies),
            'measurements': len(history)
        }
    
    def get_system_coherence(self) -> Dict[str, float]:
        """
        Get overall system coherence metrics.
        
        Returns:
            Dictionary with system-wide coherence metrics
        """
        all_metrics = [metric for history in self.cluster_history.values() 
                      for metric in history]
        
        if not all_metrics:
            return {
                'system_volatility': 0.0,
                'system_energy': 0.0,
                'active_clusters': 0
            }
            
        volatilities = [m.volatility_score for m in all_metrics]
        energies = [m.energy_cost for m in all_metrics]
        
        return {
            'system_volatility': np.mean(volatilities),
            'system_energy': sum(energies),
            'active_clusters': len(self.cluster_history)
        }
    
    def export_metrics(self) -> str:
        """Export current metrics as JSON string for persistence."""
        export_data = {
            'baseline_coherence': self.baseline_coherence,
            'energy_consumption': dict(self.energy_consumption),
            'cluster_history_lengths': {k: len(v) for k, v in self.cluster_history.items()}
        }
        return json.dumps(export_data)
    
    def load_metrics(self, json_data: str):
        """Load metrics from JSON string."""
        data = json.loads(json_data)
        self.baseline_coherence = data.get('baseline_coherence', {})
        self.energy_consumption = defaultdict(float, data.get('energy_consumption', {}))
        # cluster_history would need separate persistence mechanism
        return True