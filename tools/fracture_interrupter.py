import sys
import traceback
import threading
import time
import json
import hashlib
from collections import defaultdict
from functools import wraps
from contextlib import contextmanager

class FractureInterrupter:
    def __init__(self):
        self.hooks_enabled = False
        self.semantic_events = []
        self.frame_differentials = []
        self.validation_reports = []
        self.lock = threading.Lock()
        self.original_excepthook = sys.excepthook
        self.tracer_state = {
            'russian_frames': [],
            'english_frames': [],
            'last_divergence': None
        }

    def enable_hooks(self):
        if not self.hooks_enabled:
            sys.excepthook = self._exception_handler
            sys.settrace(self._trace_handler)
            self.hooks_enabled = True

    def disable_hooks(self):
        if self.hooks_enabled:
            sys.excepthook = self.original_excepthook
            sys.settrace(None)
            self.hooks_enabled = False

    def _exception_handler(self, exc_type, exc_value, exc_traceback):
        self._capture_semantic_event(exc_type, exc_value, exc_traceback)
        self.original_excepthook(exc_type, exc_value, exc_traceback)

    def _trace_handler(self, frame, event, arg):
        if event == 'call':
            self._capture_frame_context(frame)
        return self._trace_handler

    def _capture_frame_context(self, frame):
        with self.lock:
            filename = frame.f_code.co_filename
            function = frame.f_code.co_name
            lineno = frame.f_lineno
            
            # Determine language context from filename or function name
            is_russian = self._is_russian_context(filename, function)
            
            frame_info = {
                'filename': filename,
                'function': function,
                'lineno': lineno,
                'timestamp': time.time(),
                'locals': self._sanitize_locals(frame.f_locals),
                'is_russian': is_russian
            }
            
            if is_russian:
                self.tracer_state['russian_frames'].append(frame_info)
            else:
                self.tracer_state['english_frames'].append(frame_info)
            
            # Check for semantic divergence
            self._check_semantic_divergence()

    def _is_russian_context(self, filename, function):
        # Simple heuristic - could be enhanced with more sophisticated detection
        russian_indicators = ['ru', 'rus', 'кириллица', ' russian']
        file_check = any(indicator in filename.lower() for indicator in russian_indicators)
        func_check = any(indicator in function.lower() for indicator in russian_indicators)
        return file_check or func_check

    def _sanitize_locals(self, locals_dict):
        # Remove sensitive data and non-serializable objects
        sanitized = {}
        for key, value in locals_dict.items():
            try:
                json.dumps(value)  # Test serializability
                sanitized[key] = value
            except (TypeError, ValueError):
                sanitized[key] = f"<non-serializable: {type(value).__name__}>"
        return sanitized

    def _check_semantic_divergence(self):
        # Simple divergence detection - can be enhanced
        russian_count = len(self.tracer_state['russian_frames'])
        english_count = len(self.tracer_state['english_frames'])
        
        if abs(russian_count - english_count) > 5:  # Threshold for divergence
            if self.tracer_state['last_divergence'] is None or \
               time.time() - self.tracer_state['last_divergence'] > 1.0:  # Debounce
                self._record_frame_differential()
                self.tracer_state['last_divergence'] = time.time()

    def _record_frame_differential(self):
        with self.lock:
            timestamp = time.time()
            differential = {
                'timestamp': timestamp,
                'russian_frame_count': len(self.tracer_state['russian_frames']),
                'english_frame_count': len(self.tracer_state['english_frames']),
                'difference': len(self.tracer_state['russian_frames']) - len(self.tracer_state['english_frames']),
                'russian_frames_snapshot': self.tracer_state['russian_frames'][-10:],  # Last 10
                'english_frames_snapshot': self.tracer_state['english_frames'][-10:]   # Last 10
            }
            self.frame_differentials.append(differential)

    def _capture_semantic_event(self, exc_type, exc_value, exc_traceback):
        with self.lock:
            timestamp = time.time()
            raw_trace = traceback.format_exception(exc_type, exc_value, exc_traceback)
            
            event = {
                'timestamp': timestamp,
                'exception_type': exc_type.__name__,
                'exception_value': str(exc_value),
                'raw_traceback': raw_trace,
                'russian_frames_at_time': list(self.tracer_state['russian_frames']),
                'english_frames_at_time': list(self.tracer_state['english_frames'])
            }
            
            self.semantic_events.append(event)
            self._generate_validation_report(event)

    def _generate_validation_report(self, event):
        report = {
            'event_id': hashlib.md5(str(event['timestamp']).encode()).hexdigest(),
            'timestamp': event['timestamp'],
            'exception_type': event['exception_type'],
            'frame_differential': event['russian_frames_at_time'] and event['english_frames_at_time'],
            'russian_frame_count': len(event['russian_frames_at_time']),
            'english_frame_count': len(event['english_frames_at_time']),
            'validation_status': 'divergent' if len(event['russian_frames_at_time']) != len(event['english_frames_at_time']) else 'aligned'
        }
        self.validation_reports.append(report)

    def get_semantic_events(self):
        with self.lock:
            return list(self.semantic_events)

    def get_frame_differentials(self):
        with self.lock:
            return list(self.frame_differentials)

    def get_validation_reports(self):
        with self.lock:
            return list(self.validation_reports)

    def export_logs(self, filepath):
        with self.lock:
            export_data = {
                'semantic_events': self.semantic_events,
                'frame_differentials': self.frame_differentials,
                'validation_reports': self.validation_reports
            }
            with open(filepath, 'w') as f:
                json.dump(export_data, f, indent=2, default=str)

# Global instance
fracture_interrupter = FractureInterrupter()

# Decorator for functions that need monitoring
def monitor_semantic_divergence(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        fracture_interrupter.enable_hooks()
        try:
            result = func(*args, **kwargs)
            return result
        finally:
            fracture_interrupter.disable_hooks()
    return wrapper

# Context manager for controlled monitoring
@contextmanager
def semantic_monitoring():
    fracture_interrupter.enable_hooks()
    try:
        yield fracture_interrupter
    finally:
        fracture_interrupter.disable_hooks()

# Initialize on module import
fracture_interrupter.enable_hooks()