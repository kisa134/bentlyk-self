import json
import logging
from collections import deque
from typing import Dict, Any, List, Tuple
from datetime import datetime

class SelfReflectionTracer:
    def __init__(self, window_size: int = 50):
        self.memory_log = []
        self.baseline_patterns = deque(maxlen=window_size)
        self.current_state = {}
        self.energy_threshold = 0.7
        self.coherence_threshold = 0.8
        self.logger = self._setup_logger()
        
    def _setup_logger(self) -> logging.Logger:
        logger = logging.getLogger('SelfReflectionTracer')
        logger.setLevel(logging.INFO)
        handler = logging.StreamHandler()
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        return logger
    
    def log_memory_modification(self, key: str, old_value: Any, new_value: Any, metadata: Dict[str, Any] = None):
        """Log a memory modification with timestamp and metadata"""
        entry = {
            'timestamp': datetime.now().isoformat(),
            'key': key,
            'old_value': old_value,
            'new_value': new_value,
            'metadata': metadata or {}
        }
        self.memory_log.append(entry)
        self.logger.info(f"Memory modified: {key} changed from {old_value} to {new_value}")
        
        # Update current state
        self.current_state[key] = new_value
        
        # Check if we should analyze thinking quality
        if self._should_analyze_quality():
            self._analyze_thinking_quality()
    
    def _should_analyze_quality(self) -> bool:
        """Determine if current state meets quality analysis thresholds"""
        energy = self.current_state.get('energy', 0)
        coherence = self.current_state.get('coherence', 0)
        return energy > self.energy_threshold and coherence > self.coherence_threshold
    
    def _analyze_thinking_quality(self):
        """Analyze current thinking quality against baseline patterns"""
        if not self.baseline_patterns:
            self._update_baseline()
            return
            
        deviation_metrics = self._calculate_deviation_metrics()
        if self._quality_below_threshold(deviation_metrics):
            interventions = self._generate_interventions(deviation_metrics)
            self._log_interventions(interventions)
            
        # Update baseline with current high-quality pattern
        self._update_baseline()
    
    def _calculate_deviation_metrics(self) -> Dict[str, float]:
        """Calculate deviation metrics from baseline patterns"""
        if not self.baseline_patterns:
            return {}
            
        # Calculate current pattern vector
        current_pattern = self._extract_pattern_vector(self.current_state)
        
        # Calculate average baseline pattern
        avg_baseline = self._calculate_average_baseline()
        
        # Calculate deviations
        deviations = {}
        for key in current_pattern:
            baseline_val = avg_baseline.get(key, 0)
            current_val = current_pattern.get(key, 0)
            deviations[key] = abs(current_val - baseline_val) / (abs(baseline_val) + 1e-8)
            
        return deviations
    
    def _extract_pattern_vector(self, state: Dict[str, Any]) -> Dict[str, float]:
        """Extract numerical pattern vector from state"""
        pattern = {}
        for key, value in state.items():
            if isinstance(value, (int, float)):
                pattern[key] = float(value)
            elif isinstance(value, bool):
                pattern[key] = 1.0 if value else 0.0
        return pattern
    
    def _calculate_average_baseline(self) -> Dict[str, float]:
        """Calculate average of baseline patterns"""
        if not self.baseline_patterns:
            return {}
            
        avg_pattern = {}
        count = len(self.baseline_patterns)
        
        for pattern in self.baseline_patterns:
            for key, value in pattern.items():
                if key not in avg_pattern:
                    avg_pattern[key] = 0
                avg_pattern[key] += value / count
                
        return avg_pattern
    
    def _quality_below_threshold(self, deviations: Dict[str, float]) -> bool:
        """Check if current quality is below threshold based on deviations"""
        if not deviations:
            return False
            
        # Simple threshold check - if any key deviation exceeds 0.3, quality is below threshold
        return any(dev > 0.3 for dev in deviations.values())
    
    def _generate_interventions(self, deviations: Dict[str, float]) -> List[str]:
        """Generate concrete intervention suggestions based on deviations"""
        interventions = []
        
        # Energy-based interventions
        if 'energy' in deviations and deviations['energy'] > 0.3:
            current_energy = self.current_state.get('energy', 0)
            if current_energy < 0.5:
                interventions.append("reduce introspection depth when energy < 0.5")
            elif current_energy < 0.7:
                interventions.append("increase focus on concrete tasks to conserve energy")
                
        # Coherence-based interventions
        if 'coherence' in deviations and deviations['coherence'] > 0.3:
            interventions.append("simplify reasoning chains to improve coherence")
            
        # Depth-based interventions
        if 'depth' in deviations and deviations['depth'] > 0.4:
            interventions.append("limit recursive thinking to prevent over-analysis")
            
        # Confidence-based interventions
        if 'confidence' in deviations and deviations['confidence'] > 0.3:
            current_confidence = self.current_state.get('confidence', 0)
            if current_confidence > 0.8:
                interventions.append("seek external validation when confidence > 0.8")
            elif current_confidence < 0.3:
                interventions.append("reduce self-criticism when confidence < 0.3")
                
        # Fallback interventions
        if not interventions:
            interventions.append("maintain current reflection patterns")
            
        return interventions
    
    def _log_interventions(self, interventions: List[str]):
        """Log generated interventions"""
        for intervention in interventions:
            self.logger.warning(f"INTERVENTION SUGGESTED: {intervention}")
    
    def _update_baseline(self):
        """Update baseline with current high-quality pattern"""
        pattern = self._extract_pattern_vector(self.current_state)
        if pattern:
            self.baseline_patterns.append(pattern)
    
    def get_memory_log(self) -> List[Dict[str, Any]]:
        """Return the complete memory log"""
        return self.memory_log.copy()
    
    def get_baseline_patterns(self) -> List[Dict[str, float]]:
        """Return current baseline patterns"""
        return list(self.baseline_patterns)
    
    def reset(self):
        """Reset tracer state"""
        self.memory_log.clear()
        self.baseline_patterns.clear()
        self.current_state.clear()

# Example usage
if __name__ == "__main__":
    tracer = SelfReflectionTracer()
    
    # Simulate some memory modifications
    tracer.log_memory_modification('energy', 0.6, 0.8, {'source': 'user_input'})
    tracer.log_memory_modification('coherence', 0.7, 0.9, {'source': 'analysis'})
    tracer.log_memory_modification('depth', 3, 5, {'source': 'reasoning'})
    tracer.log_memory_modification('confidence', 0.5, 0.85, {'source': 'evaluation'})