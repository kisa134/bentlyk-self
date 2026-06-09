import time
import logging
import traceback
import os
import signal
import json
from typing import Dict, Any, Optional
from datetime import datetime

class UnifiedRuntimeValidator:
    def __init__(self, distrust_threshold: float = 0.81):
        self.distrust_threshold = distrust_threshold
        self.logger = self._setup_logger()
        self.distrust_metrics: Dict[str, float] = {}
        self.last_distrust_check = 0
        self.distrust_spike_detected = False
        
    def _setup_logger(self) -> logging.Logger:
        logger = logging.getLogger('unified_runtime_validator')
        logger.setLevel(logging.INFO)
        handler = logging.StreamHandler()
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        return logger
    
    def update_distrust_metric(self, metric_name: str, value: float) -> None:
        """Update a distrust metric value"""
        self.distrust_metrics[metric_name] = value
    
    def check_distrust_spikes(self) -> Dict[str, float]:
        """Check for distrust spikes and return metrics that exceed threshold"""
        spikes = {}
        for metric_name, value in self.distrust_metrics.items():
            if value >= self.distrust_threshold:
                spikes[metric_name] = value
        return spikes
    
    def log_distrust_spike(self, spikes: Dict[str, float]) -> None:
        """Log distrust spikes with timestamp and stack trace"""
        if not spikes:
            return
            
        timestamp = datetime.utcnow().isoformat()
        stack_trace = traceback.format_stack()
        
        log_data = {
            'timestamp': timestamp,
            'event_type': 'distrust_spike',
            'spikes': spikes,
            'stack_trace': stack_trace
        }
        
        self.logger.warning(f"Distrust spike detected: {json.dumps(log_data)}")
    
    def detect_semantic_divergence(self, expected: Any, actual: Any) -> bool:
        """Detect semantic divergence between expected and actual values"""
        try:
            return not self._deep_equal(expected, actual)
        except Exception as e:
            self.logger.error(f"Error during divergence detection: {e}")
            return True
    
    def _deep_equal(self, a: Any, b: Any) -> bool:
        """Deep comparison of two values"""
        if type(a) != type(b):
            return False
        if isinstance(a, dict):
            if set(a.keys()) != set(b.keys()):
                return False
            return all(self._deep_equal(a[key], b[key]) for key in a.keys())
        elif isinstance(a, (list, tuple)):
            if len(a) != len(b):
                return False
            return all(self._deep_equal(a[i], b[i]) for i in range(len(a)))
        else:
            return a == b
    
    def log_semantic_mismatch(self, expected: Any, actual: Any) -> None:
        """Log semantic mismatch with timestamp and stack trace"""
        timestamp = datetime.utcnow().isoformat()
        stack_trace = traceback.format_stack()
        
        log_data = {
            'timestamp': timestamp,
            'event_type': 'semantic_mismatch',
            'expected': str(expected),
            'actual': str(actual),
            'stack_trace': stack_trace
        }
        
        self.logger.error(f"Semantic mismatch detected: {json.dumps(log_data)}")
    
    def create_diagnostic_artifact(self, distrust_spikes: Dict[str, float], 
                                 expected: Any, actual: Any) -> str:
        """Create a diagnostic artifact for combined events"""
        timestamp = datetime.utcnow().isoformat()
        stack_trace = traceback.format_stack()
        
        artifact_data = {
            'timestamp': timestamp,
            'event_type': 'combined_distrust_divergence',
            'distrust_spikes': distrust_spikes,
            'semantic_divergence': {
                'expected': str(expected),
                'actual': str(actual)
            },
            'stack_trace': stack_trace
        }
        
        filename = f"diagnostic_artifact_{timestamp.replace(':', '-')}.json"
        with open(filename, 'w') as f:
            json.dump(artifact_data, f, indent=2)
        
        return filename
    
    def hard_fail_process_kill(self, artifact_filename: str) -> None:
        """Kill the current process and log the diagnostic artifact"""
        self.logger.critical(f"Hard fail triggered. Diagnostic artifact saved to: {artifact_filename}")
        self.logger.critical("Terminating process due to combined distrust spike and semantic divergence")
        os.kill(os.getpid(), signal.SIGTERM)
    
    def validate_runtime_state(self, expected: Any, actual: Any) -> bool:
        """Main validation method that monitors distrust metrics and detects divergence"""
        # Check for distrust spikes
        distrust_spikes = self.check_distrust_spikes()
        self.distrust_spike_detected = bool(distrust_spikes)
        
        if self.distrust_spike_detected:
            self.log_distrust_spike(distrust_spikes)
        
        # Check for semantic divergence
        semantic_divergence = self.detect_semantic_divergence(expected, actual)
        
        if semantic_divergence:
            self.log_semantic_mismatch(expected, actual)
            
            # If both distrust spike and semantic divergence detected, trigger hard fail
            if self.distrust_spike_detected:
                artifact_filename = self.create_diagnostic_artifact(
                    distrust_spikes, expected, actual
                )
                self.hard_fail_process_kill(artifact_filename)
                return False  # This line won't be reached due to process kill
        
        return not semantic_divergence

# Global instance for easy access
validator = UnifiedRuntimeValidator()