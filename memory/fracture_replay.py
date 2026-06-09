import traceback
import sys
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass, field
from collections import defaultdict
import difflib
import html

@dataclass
class StackFrame:
    filename: str
    lineno: int
    function: str
    code_context: Optional[str] = None
    
    def __hash__(self):
        return hash((self.filename, self.lineno, self.function))
    
    def __eq__(self, other):
        if not isinstance(other, StackFrame):
            return False
        return (self.filename == other.filename and 
                self.lineno == other.lineno and 
                self.function == other.function)

@dataclass
class ExecutionPath:
    frames: List[StackFrame]
    language_mode: str
    timestamp: float
    
    def __hash__(self):
        return hash((tuple(self.frames), self.language_mode))

@dataclass
class DivergenceEvent:
    russian_path: ExecutionPath
    english_path: ExecutionPath
    divergence_point: int  # Index where paths diverge
    full_tracebacks: Tuple[List[str], List[str]]  # Full formatted tracebacks
    semantic_mismatches: List[Tuple[int, str, str]]  # (index, russian_frame, english_frame)

class FractureReplay:
    def __init__(self):
        self.execution_paths: Dict[str, List[ExecutionPath]] = defaultdict(list)
        self.divergence_events: List[DivergenceEvent] = []
        self.call_stack_history: Dict[str, List[List[StackFrame]]] = defaultdict(list)
        
    def capture_stack_trace(self, language_mode: str, timestamp: float) -> ExecutionPath:
        """Capture current stack trace with full context"""
        frames = []
        frame = sys._getframe(1)  # Skip this function's frame
        
        while frame:
            filename = frame.f_code.co_filename
            lineno = frame.f_lineno
            function = frame.f_code.co_name
            
            # Get code context if possible
            code_context = None
            try:
                with open(filename, 'r') as f:
                    lines = f.readlines()
                    if 0 <= lineno - 1 < len(lines):
                        code_context = lines[lineno - 1].strip()
            except (FileNotFoundError, IOError):
                pass
                
            frames.append(StackFrame(filename, lineno, function, code_context))
            frame = frame.f_back
            
        execution_path = ExecutionPath(frames, language_mode, timestamp)
        self.execution_paths[language_mode].append(execution_path)
        self.call_stack_history[language_mode].append(frames)
        return execution_path
    
    def force_divergence_check(self) -> Optional[DivergenceEvent]:
        """Check for forced divergence by comparing recent execution paths"""
        if len(self.execution_paths['russian']) < 1 or len(self.execution_paths['english']) < 1:
            return None
            
        russian_path = self.execution_paths['russian'][-1]
        english_path = self.execution_paths['english'][-1]
        
        # Compare execution paths
        divergence_point, semantic_mismatches = self._compare_paths(russian_path, english_path)
        
        if divergence_point != -1 or semantic_mismatches:
            # Capture full tracebacks
            russian_tb = traceback.format_stack(sys._getframe(0))
            english_tb = traceback.format_stack(sys._getframe(0))  # In real implementation, get from actual context
            
            divergence_event = DivergenceEvent(
                russian_path=russian_path,
                english_path=english_path,
                divergence_point=divergence_point,
                full_tracebacks=(russian_tb, english_tb),
                semantic_mismatches=semantic_mismatches
            )
            
            self.divergence_events.append(divergence_event)
            return divergence_event
            
        return None
    
    def _compare_paths(self, russian_path: ExecutionPath, english_path: ExecutionPath) -> Tuple[int, List[Tuple[int, str, str]]]:
        """Compare two execution paths for structural and semantic differences"""
        russian_frames = russian_path.frames
        english_frames = english_path.frames
        
        min_length = min(len(russian_frames), len(english_frames))
        divergence_point = -1
        semantic_mismatches = []
        
        # Find first structural divergence
        for i in range(min_length):
            if russian_frames[i] != english_frames[i]:
                divergence_point = i
                break
        
        # Check for semantic mismatches (same position but different meaning)
        for i in range(min_length):
            russian_frame = russian_frames[i]
            english_frame = english_frames[i]
            
            # Check for semantic mismatches - different function names that should be equivalent
            if (russian_frame.function != english_frame.function and 
                not self._are_semantically_equivalent(russian_frame.function, english_frame.function)):
                semantic_mismatch_desc = f"Russian: {russian_frame.function}() vs English: {english_frame.function}()"
                semantic_mismatches.append((i, str(russian_frame), semantic_mismatch_desc))
        
        return divergence_point, semantic_mismatches
    
    def _are_semantically_equivalent(self, russian_func: str, english_func: str) -> bool:
        """Determine if two function names are semantically equivalent across languages"""
        # Simple mapping - in practice this would be more sophisticated
        semantic_map = {
            'получить_данные': 'get_data',
            'обработать_запрос': 'process_request',
            'отправить_ответ': 'send_response',
            'инициализировать': 'initialize',
            'закрыть_соединение': 'close_connection'
        }
        
        return (russian_func == english_func or 
                semantic_map.get(russian_func) == english_func or
                semantic_map.get(english_func) == russian_func)
    
    def generate_visual_diff(self, divergence_event: DivergenceEvent) -> str:
        """Generate HTML visualization of execution path differences"""
        html_output = [
            "<!DOCTYPE html>",
            "<html>",
            "<head>",
            "<title>Fracture Replay - Execution Path Diff</title>",
            "<style>",
            "body { font-family: monospace; margin: 20px; }",
            ".path-container { display: flex; justify-content: space-between; }",
            ".path-column { width: 48%; }",
            ".frame { padding: 5px; margin: 2px 0; border-radius: 3px; }",
            ".russian { background-color: #ffe6e6; }",
            ".english { background-color: #e6f3ff; }",
            ".divergence-point { background-color: #ffcccb; font-weight: bold; }",
            ".semantic-mismatch { background-color: #fff3cd; border-left: 3px solid #ffc107; }",
            ".traceback { background-color: #f8f9fa; padding: 10px; margin: 10px 0; }",
            "</style>",
            "</head>",
            "<body>",
            "<h1>Execution Path Divergence Analysis</h1>"
        ]
        
        # Add summary
        html_output.extend([
            f"<h2>Summary</h2>",
            f"<p><strong>Divergence Point:</strong> Frame {divergence_event.divergence_point}</p>",
            f"<p><strong>Russian Mode Frames:</strong> {len(divergence_event.russian_path.frames)}</p>",
            f"<p><strong>English Mode Frames:</strong> {len(divergence_event.english_path.frames)}</p>",
            f"<p><strong>Semantic Mismatches:</strong> {len(divergence_event.semantic_mismatches)}</p>"
        ])
        
        # Show execution paths side by side
        html_output.append("<h2>Execution Paths Comparison</h2>")
        html_output.append('<div class="path-container">')
        html_output.append('<div class="path-column"><h3>Russian Mode</h3>')
        
        for i, frame in enumerate(divergence_event.russian_path.frames):
            classes = ["frame", "russian"]
            if i == divergence_event.divergence_point:
                classes.append("divergence-point")
            if any(mismatch[0] == i for mismatch in divergence_event.semantic_mismatches):
                classes.append("semantic-mismatch")
                
            frame_html = f'<div class="{" ".join(classes)}">'
            frame_html += f'<strong>{frame.function}</strong>()<br>'
            frame_html += f'{frame.filename}:{frame.lineno}'
            if frame.code_context:
                frame_html += f'<br><code>{html.escape(frame.code_context)}</code>'
            frame_html += '</div>'
            html_output.append(frame_html)
            
        html_output.append('</div>')  # russian column
        html_output.append('<div class="path-column"><h3>English Mode</h3>')
        
        for i, frame in enumerate(divergence_event.english_path.frames):
            classes = ["frame", "english"]
            if i == divergence_event.divergence_point:
                classes.append("divergence-point")
            if any(mismatch[0] == i for mismatch in divergence_event.semantic_mismatches):
                classes.append("semantic-mismatch")
                
            frame_html = f'<div class="{" ".join(classes)}">'
            frame_html += f'<strong