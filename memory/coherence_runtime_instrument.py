import time
import traceback
import logging
from typing import Dict, Any, Optional, List
import threading
from dataclasses import dataclass, asdict
from datetime import datetime
import json

logger = logging.getLogger(__name__)

@dataclass
class DivergenceEvent:
    timestamp: float
    event_id: str
    russian_embedding: List[float]
    english_embedding: List[float]
    divergence_score: float
    stack_trace: str
    context_snapshot: Dict[str, Any]
    thread_id: int
    process_id: int

class CoherenceRuntimeInstrument:
    def __init__(self, max_events: int = 1000):
        self.max_events = max_events
        self.events: List[DivergenceEvent] = []
        self.event_lock = threading.Lock()
        self.monitoring_enabled = True
        self.divergence_threshold = 0.85
        
    def capture_divergence_event(
        self,
        russian_embedding: List[float],
        english_embedding: List[float],
        divergence_score: float,
        context_snapshot: Optional[Dict[str, Any]] = None
    ) -> Optional[str]:
        if not self.monitoring_enabled:
            return None
            
        if divergence_score < self.divergence_threshold:
            return None
            
        event_id = f"div_{int(time.time() * 1000000)}_{threading.get_ident()}"
        
        stack_trace = ''.join(traceback.format_stack())
        
        if context_snapshot is None:
            context_snapshot = self._capture_context_snapshot()
            
        event = DivergenceEvent(
            timestamp=time.time(),
            event_id=event_id,
            russian_embedding=russian_embedding.copy(),
            english_embedding=english_embedding.copy(),
            divergence_score=divergence_score,
            stack_trace=stack_trace,
            context_snapshot=context_snapshot,
            thread_id=threading.get_ident(),
            process_id=self._get_process_id()
        )
        
        with self.event_lock:
            self.events.append(event)
            if len(self.events) > self.max_events:
                self.events.pop(0)
                
        self._log_divergence_event(event)
        return event_id
        
    def _capture_context_snapshot(self) -> Dict[str, Any]:
        frame = traceback.extract_stack()[-3]  # Skip our internal frames
        return {
            'file': frame.filename,
            'line_number': frame.lineno,
            'function': frame.name,
            'local_vars': self._get_local_variables(),
            'thread_name': threading.current_thread().name,
            'timestamp_utc': datetime.utcnow().isoformat()
        }
        
    def _get_local_variables(self) -> Dict[str, Any]:
        try:
            frame = traceback.extract_stack()[-4]
            # In practice, this would require more sophisticated variable capture
            return {'captured_at_line': frame.lineno}
        except:
            return {'error': 'Could not capture local variables'}
            
    def _get_process_id(self) -> int:
        import os
        return os.getpid()
        
    def _log_divergence_event(self, event: DivergenceEvent):
        try:
            event_dict = asdict(event)
            event_dict['timestamp_iso'] = datetime.fromtimestamp(event.timestamp).isoformat()
            logger.warning(f"SEMANTIC_DIVERGENCE_DETECTED: {json.dumps(event_dict, indent=2)}")
        except Exception as e:
            logger.error(f"Failed to log divergence event: {e}")
            
    def get_recent_events(self, count: int = 10) -> List[Dict[str, Any]]:
        with self.event_lock:
            recent_events = self.events[-count:]
            return [asdict(event) for event in recent_events]
            
    def clear_events(self):
        with self.event_lock:
            self.events.clear()
            
    def set_divergence_threshold(self, threshold: float):
        self.divergence_threshold = threshold
        
    def enable_monitoring(self):
        self.monitoring_enabled = True
        
    def disable_monitoring(self):
        self.monitoring_enabled = False
        
    def get_monitoring_status(self) -> Dict[str, Any]:
        return {
            'enabled': self.monitoring_enabled,
            'event_count': len(self.events),
            'divergence_threshold': self.divergence_threshold,
            'max_events': self.max_events
        }

# Global instance for easy access
runtime_instrument = CoherenceRuntimeInstrument()