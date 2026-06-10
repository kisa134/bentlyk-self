import json
import os
import threading
import time
from datetime import datetime
from typing import Any, Dict, List, Optional
import traceback

class FractureInterrupter:
    def __init__(self, log_file: str = "logs/fracture_events.json"):
        self.log_file = log_file
        self.lock = threading.Lock()
        self.is_logging = False
        self.event_buffer: List[Dict[str, Any]] = []
        
        # Ensure logs directory exists
        os.makedirs(os.path.dirname(log_file) if os.path.dirname(log_file) else ".", exist_ok=True)
        
        # Initialize empty log file if it doesn't exist
        if not os.path.exists(log_file):
            with open(log_file, 'w') as f:
                json.dump([], f)
    
    def start_logging(self):
        """Start logging fracture events"""
        with self.lock:
            self.is_logging = True
    
    def stop_logging(self):
        """Stop logging fracture events and flush buffer"""
        with self.lock:
            self.is_logging = False
            self._flush_buffer()
    
    def record_fracture_event(self, validation_trace: Dict[str, Any], 
                            context: Optional[Dict[str, Any]] = None):
        """Record a fracture event with validation trace data"""
        if not self.is_logging:
            return
            
        event = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "event_type": "fracture_detected",
            "validation_trace": validation_trace,
            "context": context or {},
            "thread_id": threading.get_ident(),
            "process_id": os.getpid()
        }
        
        with self.lock:
            self.event_buffer.append(event)
            
            # Flush buffer if it gets too large
            if len(self.event_buffer) >= 100:
                self._flush_buffer()
    
    def record_divergence_event(self, expected: Any, actual: Any, 
                              location: str, context: Optional[Dict[str, Any]] = None):
        """Record a divergence event - a specific type of fracture"""
        if not self.is_logging:
            return
            
        trace = {
            "type": "divergence",
            "expected": expected,
            "actual": actual,
            "location": location,
            "stack_trace": traceback.format_stack()[:-1]  # Exclude this call
        }
        
        self.record_fracture_event(trace, context)
    
    def _flush_buffer(self):
        """Write buffered events to log file"""
        if not self.event_buffer:
            return
            
        try:
            # Read existing events
            if os.path.exists(self.log_file) and os.path.getsize(self.log_file) > 0:
                with open(self.log_file, 'r') as f:
                    try:
                        existing_events = json.load(f)
                    except json.JSONDecodeError:
                        existing_events = []
            else:
                existing_events = []
            
            # Append new events
            existing_events.extend(self.event_buffer)
            
            # Write back to file
            with open(self.log_file, 'w') as f:
                json.dump(existing_events, f, indent=2)
                
            self.event_buffer.clear()
            
        except Exception as e:
            print(f"Warning: Failed to write fracture events to log: {e}")

# Global instance
_fracture_interrupter: Optional[FractureInterrupter] = None

def get_fracture_interrupter() -> FractureInterrupter:
    """Get or create the global fracture interrupter instance"""
    global _fracture_interrupter
    if _fracture_interrupter is None:
        _fracture_interrupter = FractureInterrupter()
    return _fracture_interrupter

def start_fracture_logging():
    """Start logging fracture events globally"""
    interrupter = get_fracture_interrupter()
    interrupter.start_logging()

def stop_fracture_logging():
    """Stop logging fracture events globally"""
    interrupter = get_fracture_interrupter()
    interrupter.stop_logging()

def record_divergence(expected: Any, actual: Any, location: str, 
                     context: Optional[Dict[str, Any]] = None):
    """Record a divergence event globally"""
    interrupter = get_fracture_interrupter()
    interrupter.record_divergence_event(expected, actual, location, context)

def record_fracture(validation_trace: Dict[str, Any], 
                   context: Optional[Dict[str, Any]] = None):
    """Record a fracture event globally"""
    interrupter = get_fracture_interrupter()
    interrupter.record_fracture_event(validation_trace, context)

# Context manager for temporary fracture logging
class FractureLogging:
    def __enter__(self):
        start_fracture_logging()
        return self
        
    def __exit__(self, exc_type, exc_val, exc_tb):
        stop_fracture_logging()

if __name__ == "__main__":
    # Example usage
    with FractureLogging():
        # Simulate some divergence events
        record_divergence(
            expected={"status": "success", "value": 42},
            actual={"status": "error", "value": None},
            location="api_response_handler",
            context={"endpoint": "/api/data", "user_id": 12345}
        )
        
        record_fracture({
            "type": "validation_failure",
            "rule": "data_integrity",
            "details": "Checksum mismatch detected"
        })