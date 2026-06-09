import traceback
import inspect
import hashlib
import json
import time
from collections import defaultdict, deque
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple
from dataclasses import dataclass, asdict
from threading import Lock

@dataclass
class MemoryOperation:
    operation_id: str
    timestamp: float
    operation_type: str  # 'store', 'recall', 'update'
    key: str
    value_hash: str
    context: Dict[str, Any]
    purpose: str
    call_stack: List[str]

@dataclass
class SemanticShift:
    operation_id: str
    key: str
    original_purpose: str
    current_purpose: str
    timestamp: float
    context_changes: Dict[str, Any]

class SemanticTracer:
    def __init__(self, report_interval_days: int = 7):
        self.operations: Dict[str, MemoryOperation] = {}
        self.recall_history: Dict[str, deque] = defaultdict(lambda: deque(maxlen=100))
        self.semantic_shifts: List[SemanticShift] = []
        self.lock = Lock()
        self.report_interval = timedelta(days=report_interval_days)
        self.last_report = datetime.now()

    def _get_call_stack(self) -> List[str]:
        stack = []
        for frame_info in inspect.stack()[2:6]:  # Skip tracer internals
            stack.append(f"{frame_info.filename}:{frame_info.lineno}:{frame_info.function}")
        return stack

    def _hash_value(self, value: Any) -> str:
        return hashlib.sha256(str(value).encode()).hexdigest()[:16]

    def _extract_context(self) -> Dict[str, Any]:
        frame = inspect.currentframe().f_back.f_back
        context = {
            'module': frame.f_globals.get('__name__', 'unknown'),
            'function': frame.f_code.co_name,
            'line': frame.f_lineno,
            'locals': {k: str(v) for k, v in frame.f_locals.items() if not k.startswith('_')}
        }
        return context

    def store(self, key: str, value: Any, purpose: str) -> str:
        operation_id = f"store_{hashlib.uuid4().hex[:8]}"
        value_hash = self._hash_value(value)
        call_stack = self._get_call_stack()
        context = self._extract_context()
        
        operation = MemoryOperation(
            operation_id=operation_id,
            timestamp=time.time(),
            operation_type='store',
            key=key,
            value_hash=value_hash,
            context=context,
            purpose=purpose,
            call_stack=call_stack
        )
        
        with self.lock:
            self.operations[operation_id] = operation
            self.recall_history[key].append({
                'operation_id': operation_id,
                'purpose': purpose,
                'timestamp': operation.timestamp,
                'context': context
            })
        
        return operation_id

    def recall(self, key: str, purpose: str) -> Optional[str]:
        operation_id = f"recall_{hashlib.uuid4().hex[:8]}"
        call_stack = self._get_call_stack()
        context = self._extract_context()
        
        with self.lock:
            if key not in self.recall_history or not self.recall_history[key]:
                return None
                
            last_entry = self.recall_history[key][-1]
            last_purpose = last_entry['purpose']
            
            # Check for semantic shift
            if last_purpose != purpose:
                shift = SemanticShift(
                    operation_id=operation_id,
                    key=key,
                    original_purpose=last_purpose,
                    current_purpose=purpose,
                    timestamp=time.time(),
                    context_changes={
                        'previous_context': last_entry['context'],
                        'current_context': context
                    }
                )
                self.semantic_shifts.append(shift)
            
            operation = MemoryOperation(
                operation_id=operation_id,
                timestamp=time.time(),
                operation_type='recall',
                key=key,
                value_hash=last_entry['operation_id'],  # Reference to original store
                context=context,
                purpose=purpose,
                call_stack=call_stack
            )
            
            self.operations[operation_id] = operation
            self.recall_history[key].append({
                'operation_id': operation_id,
                'purpose': purpose,
                'timestamp': operation.timestamp,
                'context': context
            })
        
        return last_entry['operation_id']

    def update(self, key: str, value: Any, purpose: str) -> str:
        operation_id = f"update_{hashlib.uuid4().hex[:8]}"
        value_hash = self._hash_value(value)
        call_stack = self._get_call_stack()
        context = self._extract_context()
        
        operation = MemoryOperation(
            operation_id=operation_id,
            timestamp=time.time(),
            operation_type='update',
            key=key,
            value_hash=value_hash,
            context=context,
            purpose=purpose,
            call_stack=call_stack
        )
        
        with self.lock:
            self.operations[operation_id] = operation
            self.recall_history[key].append({
                'operation_id': operation_id,
                'purpose': purpose,
                'timestamp': operation.timestamp,
                'context': context
            })
        
        return operation_id

    def get_anomaly_report(self) -> Dict[str, Any]:
        with self.lock:
            now = datetime.now()
            if now - self.last_report < self.report_interval:
                return {"message": "Not time for report yet"}
            
            # Compile report
            report = {
                "report_period": (self.last_report.isoformat(), now.isoformat()),
                "total_operations": len(self.operations),
                "semantic_shifts_count": len(self.semantic_shifts),
                "shifts": [asdict(shift) for shift in self.semantic_shifts[-100:]],  # Last 100 shifts
                "most_shifted_keys": self._get_most_shifted_keys(),
                "generated_at": now.isoformat()
            }
            
            # Reset for next report
            self.semantic_shifts = []
            self.last_report = now
            
            return report

    def _get_most_shifted_keys(self, limit: int = 10) -> List[Dict[str, Any]]:
        key_counts = defaultdict(int)
        for shift in self.semantic_shifts:
            key_counts[shift.key] += 1
        
        return [
            {"key": key, "shift_count": count} 
            for key, count in sorted(key_counts.items(), key=lambda x: x[1], reverse=True)[:limit]
        ]

    def export_operations(self) -> List[Dict]:
        with self.lock:
            return [asdict(op) for op in self.operations.values()]

# Global tracer instance
_tracer: Optional[SemanticTracer] = None
_trace_lock = Lock()

def get_tracer() -> SemanticTracer:
    global _tracer
    with _trace_lock:
        if _tracer is None:
            _tracer = SemanticTracer()
        return _tracer

def trace_store(key: str, value: Any, purpose: str) -> str:
    return get_tracer().store(key, value, purpose)

def trace_recall(key: str, purpose: str) -> Optional[str]:
    return get_tracer().recall(key, purpose)

def trace_update(key: str, value: Any, purpose: str) -> str:
    return get_tracer().update(key, value, purpose)

def generate_weekly_report() -> Dict[str, Any]:
    return get_tracer().get_anomaly_report()