import json
import traceback
import time
import logging
from datetime import datetime
from typing import Dict, Any, List, Optional
from dataclasses import dataclass, asdict
from threading import local
import sys

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class MemoryState:
    """Represents a snapshot of memory state"""
    variables: Dict[str, Any]
    objects: Dict[str, Any]
    references: Dict[str, str]
    timestamps: Dict[str, float]

@dataclass
class DivergenceEvent:
    """Represents a divergence event with full context"""
    timestamp: float
    timestamp_russian: str
    timestamp_english: str
    stack_trace: List[str]
    memory_state: MemoryState
    semantic_context: Dict[str, Any]
    event_type: str
    thread_id: int
    process_id: int

class CoherenceRuntimeInstrument:
    """Runtime instrument for capturing divergence events with full context"""
    
    def __init__(self, output_file: str = "divergence_events.json"):
        self.output_file = output_file
        self.divergence_events: List[DivergenceEvent] = []
        self.local_storage = local()
        self.enabled = True
        
    def capture_divergence(self, event_type: str = "generic_divergence", **context) -> None:
        """Capture a divergence event with full stack trace and memory state"""
        if not self.enabled:
            return
            
        timestamp = time.time()
        timestamp_russian = self._format_timestamp_russian(timestamp)
        timestamp_english = self._format_timestamp_english(timestamp)
        
        # Capture full stack trace
        stack_trace = traceback.format_stack()
        
        # Capture memory state
        memory_state = self._capture_memory_state()
        
        # Create divergence event
        event = DivergenceEvent(
            timestamp=timestamp,
            timestamp_russian=timestamp_russian,
            timestamp_english=timestamp_english,
            stack_trace=stack_trace,
            memory_state=memory_state,
            semantic_context=context,
            event_type=event_type,
            thread_id=self._get_thread_id(),
            process_id=self._get_process_id()
        )
        
        self.divergence_events.append(event)
        self._log_event(event)
        self._output_structured_data()
        
    def _capture_memory_state(self) -> MemoryState:
        """Capture current memory state context"""
        variables = {}
        objects = {}
        references = {}
        timestamps = {}
        
        # Capture local variables from calling frame
        frame = sys._getframe(2)  # Get caller's frame
        if frame:
            variables.update(frame.f_locals)
            
        # Capture global variables
        if frame:
            variables.update(frame.f_globals)
            
        # Simplify objects for serialization
        for key, value in variables.items():
            try:
                if hasattr(value, '__dict__'):
                    objects[key] = str(value.__dict__)
                else:
                    objects[key] = str(value)
                timestamps[key] = time.time()
            except:
                objects[key] = "<unserializable>"
                
        # Capture reference relationships
        for key, value in variables.items():
            try:
                if hasattr(value, '__dict__'):
                    for attr_name, attr_value in value.__dict__.items():
                        references[f"{key}.{attr_name}"] = str(type(attr_value).__name__)
            except:
                pass
                
        return MemoryState(
            variables=variables,
            objects=objects,
            references=references,
            timestamps=timestamps
        )
    
    def _format_timestamp_russian(self, timestamp: float) -> str:
        """Format timestamp in Russian"""
        dt = datetime.fromtimestamp(timestamp)
        return dt.strftime("%d.%m.%Y %H:%M:%S")
    
    def _format_timestamp_english(self, timestamp: float) -> str:
        """Format timestamp in English"""
        dt = datetime.fromtimestamp(timestamp)
        return dt.strftime("%Y-%m-%d %H:%M:%S")
    
    def _get_thread_id(self) -> int:
        """Get current thread ID"""
        import threading
        return threading.get_ident()
    
    def _get_process_id(self) -> int:
        """Get current process ID"""
        import os
        return os.getpid()
    
    def _log_event(self, event: DivergenceEvent) -> None:
        """Log the divergence event"""
        logger.info(f"DIVERGENCE EVENT [{event.timestamp_english}]: {event.event_type}")
        logger.info(f"Russian timestamp: {event.timestamp_russian}")
        logger.info(f"Thread ID: {event.thread_id}, Process ID: {event.process_id}")
        
    def _output_structured_data(self) -> None:
        """Output structured data for replay testing"""
        try:
            serializable_events = []
            for event in self.divergence_events:
                event_dict = asdict(event)
                # Convert non-serializable objects
                event_dict['memory_state']['variables'] = {
                    k: str(v) for k, v in event_dict['memory_state']['variables'].items()
                }
                serializable_events.append(event_dict)
                
            with open(self.output_file, 'w', encoding='utf-8') as f:
                json.dump(serializable_events, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.error(f"Failed to output structured data: {e}")
    
    def enable(self) -> None:
        """Enable the instrument"""
        self.enabled = True
    
    def disable(self) -> None:
        """Disable the instrument"""
        self.enabled = False
    
    def clear_events(self) -> None:
        """Clear captured events"""
        self.divergence_events.clear()
    
    def get_events(self) -> List[DivergenceEvent]:
        """Get captured events"""
        return self.divergence_events.copy()

# Global instrument instance
_runtime_instrument = CoherenceRuntimeInstrument()

def capture_divergence(event_type: str = "generic_divergence", **context) -> None:
    """Global function to capture divergence events"""
    _runtime_instrument.capture_divergence(event_type, **context)

def enable_instrument() -> None:
    """Enable the runtime instrument"""
    _runtime_instrument.enable()

def disable_instrument() -> None:
    """Disable the runtime instrument"""
    _runtime_instrument.disable()

def get_instrument() -> CoherenceRuntimeInstrument:
    """Get the global instrument instance"""
    return _runtime_instrument