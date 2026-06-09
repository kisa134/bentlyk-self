import logging
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from datetime import datetime, timedelta

from memory.coherence_tracker import CoherenceTracker
from memory.delta_analyzer import DeltaAnalyzer, MemoryDelta

logger = logging.getLogger(__name__)

@dataclass
class Anomaly:
    """Represents a detected anomaly in memory access patterns."""
    timestamp: datetime
    type: str
    description: str
    severity: str
    context: Dict[str, Any]
    resolved: bool = False

class AnomalyDetector:
    """Detects anomalies in memory access patterns by comparing expected vs actual behavior."""
    
    def __init__(self, coherence_tracker: CoherenceTracker, delta_analyzer: DeltaAnalyzer):
        self.coherence_tracker = coherence_tracker
        self.delta_analyzer = delta_analyzer
        self.anomalies: List[Anomaly] = []
        self.alert_thresholds = {
            'coherence_violation': 0.8,
            'unexpected_delta': 0.7,
            'access_pattern': 0.75
        }
        
    def detect_anomalies(self, memory_delta: MemoryDelta) -> List[Anomaly]:
        """Analyze a memory delta for anomalies and return any detected issues."""
        detected_anomalies = []
        
        # Check for coherence violations
        coherence_anomalies = self._check_coherence_violations(memory_delta)
        detected_anomalies.extend(coherence_anomalies)
        
        # Check for unexpected deltas
        delta_anomalies = self._check_unexpected_deltas(memory_delta)
        detected_anomalies.extend(delta_anomalies)
        
        # Check access patterns
        pattern_anomalies = self._check_access_patterns(memory_delta)
        detected_anomalies.extend(pattern_anomalies)
        
        # Add to tracking
        self.anomalies.extend(detected_anomalies)
        return detected_anomalies
    
    def _check_coherence_violations(self, memory_delta: MemoryDelta) -> List[Anomaly]:
        """Check for coherence violations in the memory delta."""
        anomalies = []
        
        # Get expected coherence state
        expected_coherence = self.coherence_tracker.get_expected_coherence(
            memory_delta.key, 
            memory_delta.timestamp
        )
        
        if expected_coherence is not None:
            # Calculate coherence score
            coherence_score = self.coherence_tracker.calculate_coherence_score(
                memory_delta.key,
                memory_delta.value,
                memory_delta.timestamp
            )
            
            if coherence_score < self.alert_thresholds['coherence_violation']:
                anomaly = Anomaly(
                    timestamp=memory_delta.timestamp,
                    type='coherence_violation',
                    description=f'Coherence score {coherence_score:.2f} below threshold for key {memory_delta.key}',
                    severity='high' if coherence_score < 0.5 else 'medium',
                    context={
                        'key': memory_delta.key,
                        'expected_coherence': expected_coherence,
                        'actual_coherence': coherence_score,
                        'value': memory_delta.value
                    }
                )
                anomalies.append(anomaly)
                logger.warning(f"Coherence violation detected: {anomaly.description}")
                
        return anomalies
    
    def _check_unexpected_deltas(self, memory_delta: MemoryDelta) -> List[Anomaly]:
        """Check for unexpected changes in memory values."""
        anomalies = []
        
        # Analyze the delta for unexpected patterns
        delta_analysis = self.delta_analyzer.analyze_delta(memory_delta)
        
        if delta_analysis.confidence < self.alert_thresholds['unexpected_delta']:
            anomaly = Anomaly(
                timestamp=memory_delta.timestamp,
                type='unexpected_delta',
                description=f'Unexpected delta detected for key {memory_delta.key}',
                severity='medium',
                context={
                    'key': memory_delta.key,
                    'analysis': delta_analysis,
                    'confidence': delta_analysis.confidence
                }
            )
            anomalies.append(anomaly)
            logger.warning(f"Unexpected delta detected: {anomaly.description}")
            
        return anomalies
    
    def _check_access_patterns(self, memory_delta: MemoryDelta) -> List[Anomaly]:
        """Check for anomalous access patterns."""
        anomalies = []
        
        # Get historical access pattern
        historical_pattern = self.coherence_tracker.get_access_pattern(memory_delta.key)
        
        if historical_pattern:
            # Calculate pattern deviation
            deviation = self._calculate_pattern_deviation(
                memory_delta, 
                historical_pattern
            )
            
            if deviation > self.alert_thresholds['access_pattern']:
                anomaly = Anomaly(
                    timestamp=memory_delta.timestamp,
                    type='access_pattern',
                    description=f'Access pattern deviation {deviation:.2f} for key {memory_delta.key}',
                    severity='high' if deviation > 0.9 else 'medium',
                    context={
                        'key': memory_delta.key,
                        'deviation': deviation,
                        'historical_pattern': historical_pattern
                    }
                )
                anomalies.append(anomaly)
                logger.warning(f"Access pattern anomaly detected: {anomaly.description}")
                
        return anomalies
    
    def _calculate_pattern_deviation(self, memory_delta: MemoryDelta, historical_pattern: Dict) -> float:
        """Calculate deviation from historical access patterns."""
        # Simplified pattern deviation calculation
        # In a real implementation, this would use more sophisticated pattern matching
        current_time = memory_delta.timestamp
        time_diff = abs((current_time - historical_pattern.get('last_access', current_time)).total_seconds())
        
        # Normalize time difference (assuming patterns repeat within 24 hours)
        normalized_diff = min(time_diff / (24 * 3600), 1.0)
        return normalized_diff
    
    def get_active_anomalies(self) -> List[Anomaly]:
        """Return all unresolved anomalies."""
        return [a for a in self.anomalies if not a.resolved]
    
    def resolve_anomaly(self, anomaly: Anomaly) -> None:
        """Mark an anomaly as resolved."""
        anomaly.resolved = True
        logger.info(f"Anomaly resolved: {anomaly.description}")
    
    def get_anomaly_summary(self) -> Dict[str, Any]:
        """Get a summary of detected anomalies."""
        active_anomalies = self.get_active_anomalies()
        
        severity_counts = {'high': 0, 'medium': 0, 'low': 0}
        type_counts = {}
        
        for anomaly in active_anomalies:
            severity_counts[anomaly.severity] += 1
            type_counts[anomaly.type] = type_counts.get(anomaly.type, 0) + 1
            
        return {
            'total_active': len(active_anomalies),
            'by_severity': severity_counts,
            'by_type': type_counts,
            'timestamp': datetime.now()
        }