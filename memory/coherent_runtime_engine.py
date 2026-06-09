import sys
import traceback
import difflib
import json
import logging
from typing import Any, Dict, List, Tuple, Optional, Callable
from dataclasses import dataclass, asdict
from collections import defaultdict
import hashlib
import inspect

logger = logging.getLogger(__name__)

@dataclass
class SemanticSnapshot:
    """Represents a semantic state at a point in execution"""
    timestamp: float
    frame_info: str
    variables: Dict[str, Any]
    output: Any
    call_stack: List[str]
    locale: str  # 'ru' or 'en'

@dataclass
class CoherenceFracture:
    """Represents a detected divergence between language modes"""
    timestamp: float
    location: str
    english_state: SemanticSnapshot
    russian_state: SemanticSnapshot
    semantic_diff: List[str]
    stack_trace: List[str]

class SemanticStateTracker:
    """Tracks semantic states for both language modes"""
    
    def __init__(self):
        self.states: Dict[str, List[SemanticSnapshot]] = {
            'en': [],
            'ru': []
        }
        self.current_locale = 'en'
        
    def set_locale(self, locale: str):
        """Set current execution locale"""
        self.current_locale = locale
        
    def capture_state(self, frame, output: Any = None):
        """Capture current semantic state"""
        frame_info = f"{frame.f_code.co_filename}:{frame.f_lineno} in {frame.f_code.co_name}"
        
        # Capture local variables (sanitize for JSON)
        variables = {}
        for name, value in frame.f_locals.items():
            try:
                json.dumps(value)  # Test serializability
                variables[name] = value
            except (TypeError, ValueError):
                variables[name] = str(value)
        
        # Capture call stack
        call_stack = []
        current_frame = frame
        while current_frame:
            call_stack.append(f"{current_frame.f_code.co_filename}:{current_frame.f_lineno} in {current_frame.f_code.co_name}")
            current_frame = current_frame.f_back
        
        snapshot = SemanticSnapshot(
            timestamp=frame.f_lasti,
            frame_info=frame_info,
            variables=variables,
            output=output,
            call_stack=call_stack,
            locale=self.current_locale
        )
        
        self.states[self.current_locale].append(snapshot)
        return snapshot

class SemanticDivergenceDetector:
    """Detects semantic differences between language executions"""
    
    def __init__(self):
        self.tracker = SemanticStateTracker()
        self.fractures: List[CoherenceFracture] = []
        
    def compare_states(self, en_state: SemanticSnapshot, ru_state: SemanticSnapshot) -> List[str]:
        """Compare two semantic states and return differences"""
        differences = []
        
        # Compare outputs
        if en_state.output != ru_state.output:
            differences.append(f"Output divergence: EN={en_state.output}, RU={ru_state.output}")
            
        # Compare variables
        all_vars = set(en_state.variables.keys()) | set(ru_state.variables.keys())
        for var in all_vars:
            en_val = en_state.variables.get(var, "<MISSING>")
            ru_val = ru_state.variables.get(var, "<MISSING>")
            if en_val != ru_val:
                differences.append(f"Variable '{var}': EN={en_val}, RU={ru_val}")
                
        # Compare call stacks
        if en_state.call_stack != ru_state.call_stack:
            differences.append("Call stack divergence detected")
            
        return differences
    
    def detect_fractures(self) -> List[CoherenceFracture]:
        """Detect all coherence fractures between language modes"""
        fractures = []
        
        # Pair states by execution order
        min_length = min(len(self.tracker.states['en']), len(self.tracker.states['ru']))
        
        for i in range(min_length):
            en_state = self.tracker.states['en'][i]
            ru_state = self.tracker.states['ru'][i]
            
            differences = self.compare_states(en_state, ru_state)
            if differences:
                # Capture current stack trace
                stack_trace = traceback.format_stack()
                
                fracture = CoherenceFracture(
                    timestamp=en_state.timestamp,
                    location=en_state.frame_info,
                    english_state=en_state,
                    russian_state=ru_state,
                    semantic_diff=differences,
                    stack_trace=stack_trace
                )
                fractures.append(fracture)
                
        self.fractures.extend(fractures)
        return fractures

class ReplayLab:
    """Isolation environment for debugging coherence fractures"""
    
    def __init__(self, detector: SemanticDivergenceDetector):
        self.detector = detector
        self.replay_states: Dict[str, SemanticSnapshot] = {}
        
    def isolate_fracture(self, fracture: CoherenceFracture) -> Dict[str, Any]:
        """Create isolated reproduction environment for a fracture"""
        isolation_data = {
            'location': fracture.location,
            'english_context': {
                'variables': fracture.english_state.variables,
                'output': fracture.english_state.output,
                'call_stack': fracture.english_state.call_stack
            },
            'russian_context': {
                'variables': fracture.russian_state.variables,
                'output': fracture.russian_state.output,
                'call_stack': fracture.russian_state.call_stack
            },
            'differences': fracture.semantic_diff,
            'stack_trace': fracture.stack_trace
        }
        return isolation_data
    
    def export_fracture_report(self, fracture: CoherenceFracture, filepath: str):
        """Export detailed fracture report to file"""
        isolation_data = self.isolate_fracture(fracture)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(isolation_data, f, indent=2, ensure_ascii=False)
            
    def replay_fracture_context(self, fracture: CoherenceFracture) -> str:
        """Generate executable code to replay fracture context"""
        en_vars = fracture.english_state.variables
        ru_vars = fracture.russian_state.variables
        
        replay_code = f"""# Coherence Fracture Replay
# Location: {fracture.location}

# English Mode Context
en_context = {repr(en_vars)}

# Russian Mode Context  
ru_context = {repr(ru_vars)}

# Differences Detected:
"""
        for diff in fracture.semantic_diff:
            replay_code += f"# - {diff}\n"
            
        replay_code += "\n# Stack Trace:\n"
        for frame in fracture.stack_trace:
            replay_code += f"# {frame}\n"
            
        return replay_code

class CoherentRuntimeEngine:
    """Main runtime engine for coherent multilingual execution"""
    
    def __init__(self):
        self.detector = SemanticDivergenceDetector()
        self.replay_lab = ReplayLab(self.detector)
        self.hooks: List[Callable] = []
        self.execution_log: List[Dict] = []
        
    def register_hook(self, hook: Callable):
        """Register execution hook for state capture"""
        self.hooks.append(hook)
        
    def execute_with_locale(self, func: Callable, locale: str, *args, **kwargs) -> Any:
        """Execute function with specified locale context"""
        self.detector.tracker.set_locale(locale)
        
        # Capture pre-execution state
        frame = inspect.currentframe()
        self.detector.tracker.capture_state(frame)
        
        try:
            result = func(*args, **kwargs)
            
            # Capture post-execution state
            frame = inspect.currentframe()
            self.detector.tracker.capture_state(frame, result)
            
            # Execute hooks
            for hook in self.hooks:
                hook(locale, frame, result)
                
            self.execution_log.append({
                'locale': locale,
                'function': func.__name__,
                'args': args,
                'kwargs': kwargs,
                'result': result
            })
            
            return result
            
        except Exception as e:
            # Capture exception state
            frame = inspect.currentframe()
            self.detector.tracker.capture_state(frame, str(e))
            raise
            
    def detect_and_report_fractures(self) -> List[Dict]:
        """Detect coherence fractures and generate reports"""
        fractures = self.detector.detect_fractures()
        reports = []
        
        for i, fracture in enumerate(fractures):
            report = {
                'fracture_id': i,
                'timestamp': fracture.timestamp,
                'location': fracture.location,
                'differences': fracture.semantic_diff,
                'stack_trace': fracture.stack_trace
            }
            reports.append(report)
            
        return reports
    
    def export_all_fractures(self, directory: str = "./fracture_reports"):
        """Export all detected fractures to report files"""
        import os
        os.makedirs(directory, exist_ok=True)
        
        fractures = self.detector.detect_fractures()
        
        for i, fracture in enumerate(fractures):
            filepath = f"{directory}/fracture_{i:03d}.json"
            self.replay_lab.export_fracture_report(fracture, filepath)
            
        return len(fractures)
    
    def get_replay_code(self, fracture_id: int) -> str:
        """Get executable replay code for specific fracture"""
        fractures = self.detector.detect_fractures()
        if 0 <= fracture_id < len(fractures):
            return self.replay_lab.replay_fracture_context(fractures[fracture_id])
        return "# Fracture ID out of range"

#