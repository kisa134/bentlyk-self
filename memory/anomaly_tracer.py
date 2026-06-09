import threading
import time
import logging
from datetime import datetime
from typing import Optional, Dict, Any
from collections import deque

class AnomalyTracer:
    def __init__(self, introspection_system, energy_monitor, input_buffer_size: int = 10):
        self.introspection_system = introspection_system
        self.energy_monitor = energy_monitor
        self.threshold = 0.7
        self.running = False
        self.thread: Optional[threading.Thread] = None
        self.logger = self._setup_logger()
        self.recent_inputs = deque(maxlen=input_buffer_size)
        self.lock = threading.Lock()
        
    def _setup_logger(self) -> logging.Logger:
        logger = logging.getLogger('anomaly_tracer')
        logger.setLevel(logging.INFO)
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)
        return logger
    
    def start(self):
        """Start the anomaly tracing background process"""
        with self.lock:
            if self.running:
                return
            self.running = True
            self.thread = threading.Thread(target=self._monitor_loop, daemon=True)
            self.thread.start()
            self.logger.info("Anomaly tracer started")
    
    def stop(self):
        """Stop the anomaly tracing background process"""
        with self.lock:
            if not self.running:
                return
            self.running = False
        if self.thread:
            self.thread.join(timeout=2.0)
        self.logger.info("Anomaly tracer stopped")
    
    def _monitor_loop(self):
        """Main monitoring loop running in background thread"""
        while self.running:
            try:
                coherence = self.introspection_system.get_coherence_level()
                if coherence < self.threshold:
                    self._handle_anomaly(coherence)
                time.sleep(0.1)  # Check every 100ms for minimal overhead
            except Exception as e:
                self.logger.error(f"Error in anomaly monitoring: {e}")
                time.sleep(1.0)  # Back off on error
    
    def _handle_anomaly(self, coherence: float):
        """Handle detected anomaly by logging and triggering reflection"""
        timestamp = datetime.now()
        energy_level = self.energy_monitor.get_current_energy()
        recent_inputs_snapshot = list(self.recent_inputs)
        
        # Log the anomaly
        self._log_anomaly(timestamp, coherence, energy_level, recent_inputs_snapshot)
        
        # Trigger immediate reflection
        self._trigger_reflection_prompt(coherence, energy_level, recent_inputs_snapshot)
    
    def _log_anomaly(self, timestamp: datetime, coherence: float, 
                     energy_level: float, recent_inputs: list):
        """Log anomaly details"""
        log_data = {
            'timestamp': timestamp.isoformat(),
            'coherence_level': coherence,
            'energy_level': energy_level,
            'recent_inputs': recent_inputs
        }
        self.logger.warning(f"Memory coherence anomaly detected: {log_data}")
    
    def _trigger_reflection_prompt(self, coherence: float, energy_level: float, 
                                 recent_inputs: list):
        """Trigger system reflection about the anomaly"""
        prompt = self._build_reflection_prompt(coherence, energy_level, recent_inputs)
        try:
            self.introspection_system.trigger_reflection(prompt)
        except Exception as e:
            self.logger.error(f"Failed to trigger reflection: {e}")
    
    def _build_reflection_prompt(self, coherence: float, energy_level: float, 
                               recent_inputs: list) -> str:
        """Build a prompt for system reflection on the anomaly"""
        return (f"ANOMALY DETECTED: Memory coherence dropped to {coherence:.3f} "
                f"(threshold: {self.threshold}). Energy level: {energy_level:.3f}. "
                f"Recent inputs: {recent_inputs}. "
                f"Investigate potential causes and suggest corrective actions.")
    
    def record_input(self, input_data: Any):
        """Record recent input for anomaly context (called by system)"""
        with self.lock:
            self.recent_inputs.append(input_data)

# Global instance
tracer: Optional[AnomalyTracer] = None

def initialize_tracer(introspection_system, energy_monitor, input_buffer_size: int = 10):
    """Initialize and return the global anomaly tracer instance"""
    global tracer
    if tracer is None:
        tracer = AnomalyTracer(introspection_system, energy_monitor, input_buffer_size)
    return tracer

def get_tracer() -> Optional[AnomalyTracer]:
    """Get the global tracer instance"""
    return tracer