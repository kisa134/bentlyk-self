import json
import threading
import time
from collections import defaultdict, deque
from datetime import datetime
from typing import Dict, List, Any, Optional
import traceback

class UnifiedRuntimeValidator:
    def __init__(self, histogram_window_size: int = 1000):
        self.divergence_events = deque(maxlen=histogram_window_size)
        self.histogram_data = defaultdict(int)
        self.validation_reports = []
        self.lock = threading.Lock()
        self.running = False
        self.validation_thread = None
        
    def start(self):
        """Start the validation process"""
        with self.lock:
            if not self.running:
                self.running = True
                self.validation_thread = threading.Thread(target=self._validation_loop)
                self.validation_thread.daemon = True
                self.validation_thread.start()
    
    def stop(self):
        """Stop the validation process"""
        with self.lock:
            self.running = False
        if self.validation_thread:
            self.validation_thread.join()
    
    def consume_divergence_event(self, event: Dict[str, Any]):
        """Consume divergence events from semantic_drift_hooks"""
        with self.lock:
            timestamp = datetime.now().isoformat()
            event_data = {
                'timestamp': timestamp,
                'type': event.get('type', 'unknown'),
                'severity': event.get('severity', 'medium'),
                'description': event.get('description', ''),
                'model_context': event.get('model_context', {}),
                'stack_trace': event.get('stack_trace', ''),
                'coherence_data': event.get('coherence_data', {})
            }
            self.divergence_events.append(event_data)
            self.histogram_data[event_data['type']] += 1
    
    def get_histogram(self) -> Dict[str, int]:
        """Get real-time histogram of semantic divergence types"""
        with self.lock:
            return dict(self.histogram_data)
    
    def get_recent_events(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Get recent divergence events"""
        with self.lock:
            return list(self.divergence_events)[-limit:]
    
    def generate_validation_report(self) -> Dict[str, Any]:
        """Generate comprehensive validation report with stack traces"""
        with self.lock:
            total_events = len(self.divergence_events)
            histogram = dict(self.histogram_data)
            
            # Group events by type for detailed analysis
            events_by_type = defaultdict(list)
            for event in self.divergence_events:
                events_by_type[event['type']].append(event)
            
            # Extract stack traces
            stack_traces = []
            for event in self.divergence_events:
                if event.get('stack_trace'):
                    stack_traces.append({
                        'timestamp': event['timestamp'],
                        'type': event['type'],
                        'trace': event['stack_trace']
                    })
            
            report = {
                'generated_at': datetime.now().isoformat(),
                'total_divergence_events': total_events,
                'divergence_histogram': histogram,
                'events_by_type': dict(events_by_type),
                'stack_traces': stack_traces,
                'coherence_metrics': self._extract_coherence_metrics()
            }
            
            self.validation_reports.append(report)
            return report
    
    def _extract_coherence_metrics(self) -> Dict[str, Any]:
        """Extract coherence metrics from events"""
        metrics = {
            'total_coherence_violations': 0,
            'average_coherence_score': 0.0,
            'coherence_trend': []
        }
        
        coherence_scores = []
        violations = 0
        
        with self.lock:
            for event in self.divergence_events:
                coherence_data = event.get('coherence_data', {})
                if coherence_data:
                    score = coherence_data.get('coherence_score', 0)
                    coherence_scores.append(score)
                    if coherence_data.get('is_violation', False):
                        violations += 1
        
        if coherence_scores:
            metrics['average_coherence_score'] = sum(coherence_scores) / len(coherence_scores)
        
        metrics['total_coherence_violations'] = violations
        return metrics
    
    def _validation_loop(self):
        """Background validation loop"""
        while self.running:
            try:
                # Periodic validation tasks can be added here
                time.sleep(1)
            except Exception as e:
                print(f"Validation loop error: {e}")
                traceback.print_exc()

# Global instance
_validator_instance = None
_validator_lock = threading.Lock()

def get_validator() -> UnifiedRuntimeValidator:
    """Get singleton validator instance"""
    global _validator_instance
    with _validator_lock:
        if _validator_instance is None:
            _validator_instance = UnifiedRuntimeValidator()
        return _validator_instance

def consume_divergence_event(event: Dict[str, Any]):
    """Convenience function to consume divergence events"""
    validator = get_validator()
    validator.consume_divergence_event(event)

def get_current_histogram() -> Dict[str, int]:
    """Get current divergence histogram"""
    validator = get_validator()
    return validator.get_histogram()

def get_validation_report() -> Dict[str, Any]:
    """Generate and return validation report"""
    validator = get_validator()
    return validator.generate_validation_report()