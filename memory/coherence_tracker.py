import logging
from typing import Dict, Any, List, Tuple, Optional
from dataclasses import dataclass, field
from enum import Enum
import json
from datetime import datetime

class CoherenceState(Enum):
    CONSISTENT = "consistent"
    INCONSISTENT = "inconsistent"
    FRAGMENTED = "fragmented"
    UNKNOWN = "unknown"

@dataclass
class MemoryTransition:
    timestamp: datetime
    expected_state: Dict[str, Any]
    actual_state: Dict[str, Any]
    discrepancy_score: float = 0.0
    coherence_state: CoherenceState = CoherenceState.UNKNOWN

@dataclass
class CoherencePattern:
    pattern_id: str
    description: str
    frequency: int = 0
    last_occurrence: datetime = None
    transitions: List[MemoryTransition] = field(default_factory=list)

class CoherenceTracker:
    def __init__(self, threshold: float = 0.8):
        self.threshold = threshold
        self.transitions: List[MemoryTransition] = []
        self.patterns: Dict[str, CoherencePattern] = {}
        self.logger = self._setup_logger()
        self.fragmentation_alerts: List[str] = []
        
    def _setup_logger(self) -> logging.Logger:
        logger = logging.getLogger("CoherenceTracker")
        logger.setLevel(logging.INFO)
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)
        return logger
    
    def compare_states(self, expected: Dict[str, Any], actual: Dict[str, Any]) -> Tuple[float, CoherenceState]:
        """Compare expected vs actual states and return similarity score and coherence state."""
        if not expected and not actual:
            return 1.0, CoherenceState.CONSISTENT
            
        if not expected or not actual:
            return 0.0, CoherenceState.INCONSISTENT
            
        total_keys = set(expected.keys()) | set(actual.keys())
        if not total_keys:
            return 1.0, CoherenceState.CONSISTENT
            
        matches = 0
        for key in total_keys:
            if key in expected and key in actual:
                if expected[key] == actual[key]:
                    matches += 1
                elif isinstance(expected[key], dict) and isinstance(actual[key], dict):
                    # Recursive comparison for nested dictionaries
                    sub_score, _ = self.compare_states(expected[key], actual[key])
                    if sub_score > self.threshold:
                        matches += 1
                elif isinstance(expected[key], list) and isinstance(actual[key], list):
                    # Simple list comparison
                    if expected[key] == actual[key]:
                        matches += 1
                        
        similarity = matches / len(total_keys) if total_keys else 1.0
        
        if similarity >= self.threshold:
            state = CoherenceState.CONSISTENT
        elif similarity >= self.threshold * 0.5:
            state = CoherenceState.FRAGMENTED
        else:
            state = CoherenceState.INCONSISTENT
            
        return similarity, state
    
    def track_transition(self, expected: Dict[str, Any], actual: Dict[str, Any]) -> MemoryTransition:
        """Track a single memory state transition."""
        timestamp = datetime.now()
        discrepancy_score, coherence_state = self.compare_states(expected, actual)
        
        transition = MemoryTransition(
            timestamp=timestamp,
            expected_state=expected,
            actual_state=actual,
            discrepancy_score=discrepancy_score,
            coherence_state=coherence_state
        )
        
        self.transitions.append(transition)
        
        # Log discrepancy if significant
        if coherence_state != CoherenceState.CONSISTENT:
            self._log_discrepancy(transition)
            
        # Check for fragmentation patterns
        self._analyze_fragmentation_patterns(transition)
        
        return transition
    
    def _log_discrepancy(self, transition: MemoryTransition):
        """Log memory discrepancy with detailed information."""
        discrepancy_info = {
            "timestamp": transition.timestamp.isoformat(),
            "coherence_state": transition.coherence_state.value,
            "discrepancy_score": transition.discrepancy_score,
            "expected_keys": list(transition.expected_state.keys()),
            "actual_keys": list(transition.actual_state.keys()),
            "missing_keys": list(set(transition.expected_state.keys()) - set(transition.actual_state.keys())),
            "extra_keys": list(set(transition.actual_state.keys()) - set(transition.expected_state.keys()))
        }
        
        self.logger.warning(f"Memory discrepancy detected: {json.dumps(discrepancy_info, indent=2)}")
    
    def _analyze_fragmentation_patterns(self, transition: MemoryTransition):
        """Analyze and track patterns of memory fragmentation."""
        if transition.coherence_state == CoherenceState.FRAGMENTED:
            # Create pattern identifier based on missing/extra keys
            missing_keys = set(transition.expected_state.keys()) - set(transition.actual_state.keys())
            extra_keys = set(transition.actual_state.keys()) - set(transition.expected_state.keys())
            
            pattern_id = f"fragmentation_{'_'.join(sorted(missing_keys))}_{'_'.join(sorted(extra_keys))}"
            
            if pattern_id not in self.patterns:
                self.patterns[pattern_id] = CoherencePattern(
                    pattern_id=pattern_id,
                    description=f"Fragmentation pattern with missing: {missing_keys}, extra: {extra_keys}"
                )
            
            pattern = self.patterns[pattern_id]
            pattern.frequency += 1
            pattern.last_occurrence = transition.timestamp
            pattern.transitions.append(transition)
            
            # Alert if pattern occurs frequently
            if pattern.frequency >= 3:
                alert_msg = f"Fragmentation pattern '{pattern_id}' occurred {pattern.frequency} times"
                if alert_msg not in self.fragmentation_alerts:
                    self.fragmentation_alerts.append(alert_msg)
                    self.logger.error(f"Memory fragmentation alert: {alert_msg}")
    
    def get_coherence_report(self) -> Dict[str, Any]:
        """Generate a comprehensive coherence report."""
        if not self.transitions:
            return {"status": "no_data", "report": {}}
            
        total_transitions = len(self.transitions)
        consistent_count = sum(1 for t in self.transitions if t.coherence_state == CoherenceState.CONSISTENT)
        inconsistent_count = sum(1 for t in self.transitions if t.coherence_state == CoherenceState.INCONSISTENT)
        fragmented_count = sum(1 for t in self.transitions if t.coherence_state == CoherenceState.FRAGMENTED)
        
        avg_discrepancy = sum(t.discrepancy_score for t in self.transitions) / total_transitions
        
        report = {
            "summary": {
                "total_transitions": total_transitions,
                "consistent": consistent_count,
                "inconsistent": inconsistent_count,
                "fragmented": fragmented_count,
                "consistency_rate": consistent_count / total_transitions if total_transitions > 0 else 0,
                "avg_discrepancy_score": avg_discrepancy
            },
            "fragmentation_patterns": [
                {
                    "pattern_id": pattern.pattern_id,
                    "description": pattern.description,
                    "frequency": pattern.frequency,
                    "last_occurrence": pattern.last_occurrence.isoformat() if pattern.last_occurrence else None
                }
                for pattern in self.patterns.values()
            ],
            "alerts": self.fragmentation_alerts
        }
        
        return report
    
    def get_recent_transitions(self, count: int = 10) -> List[MemoryTransition]:
        """Get the most recent memory transitions."""
        return self.transitions[-count:] if self.transitions else []
    
    def clear_history(self):
        """Clear transition history and patterns."""
        self.transitions.clear()
        self.patterns.clear()
        self.fragmentation_alerts.clear()
    
    def export_coherence_data(self) -> str:
        """Export coherence tracking data as JSON string."""
        data = {
            "transitions": [
                {
                    "timestamp": t.timestamp.isoformat(),
                    "expected_state": t.expected_state,
                    "actual_state": t.actual_state,
                    "discrepancy_score": t.discrepancy_score,
                    "coherence_state": t.coherence_state.value
                }
                for t in self.transitions
            ],
            "patterns": {
                pid: {
                    "pattern_id": p.pattern_id,
                    "description": p.description,
                    "frequency": p.frequency,
                    "last_occurrence": p.last_occurrence.isoformat() if p.last_occurrence else None
                }
                for pid, p in self.patterns.items()
            },
            "alerts": self.fragmentation_alerts
        }
        return json.dumps(data, indent=2)