import sys
import traceback
from typing import Any, Dict, List, Optional, Tuple, Callable
from dataclasses import dataclass, field
from enum import Enum
import json
import threading
from collections import defaultdict

class ProcessingMode(Enum):
    RUSSIAN = "russian"
    ENGLISH = "english"

@dataclass
class SemanticTrace:
    mode: ProcessingMode
    step: str
    data: Any
    timestamp: float
    stack_trace: List[str] = field(default_factory=list)
    context: Dict[str, Any] = field(default_factory=dict)

@dataclass
class DivergencePoint:
    step: str
    russian_trace: SemanticTrace
    english_trace: SemanticTrace
    differences: Dict[str, Any]

class SnapshotHook:
    def __init__(self):
        self.snapshots: List[SemanticTrace] = []
        self.lock = threading.Lock()
    
    def capture(self, mode: ProcessingMode, step: str, data: Any, context: Optional[Dict[str, Any]] = None):
        stack_trace = traceback.format_stack()[:-1]  # Exclude this function call
        trace = SemanticTrace(
            mode=mode,
            step=step,
            data=data,
            timestamp=self._get_timestamp(),
            stack_trace=stack_trace,
            context=context or {}
        )
        
        with self.lock:
            self.snapshots.append(trace)
    
    def _get_timestamp(self) -> float:
        import time
        return time.time()
    
    def get_snapshots_by_mode(self, mode: ProcessingMode) -> List[SemanticTrace]:
        with self.lock:
            return [s for s in self.snapshots if s.mode == mode]
    
    def clear(self):
        with self.lock:
            self.snapshots.clear()

class SemanticComparator:
    def __init__(self):
        self.hook = SnapshotHook()
        self.divergence_points: List[DivergencePoint] = []
    
    def compare_traces(self) -> List[DivergencePoint]:
        russian_traces = {t.step: t for t in self.hook.get_snapshots_by_mode(ProcessingMode.RUSSIAN)}
        english_traces = {t.step: t for t in self.hook.get_snapshots_by_mode(ProcessingMode.ENGLISH)}
        
        all_steps = set(russian_traces.keys()) | set(english_traces.keys())
        self.divergence_points = []
        
        for step in all_steps:
            ru_trace = russian_traces.get(step)
            en_trace = english_traces.get(step)
            
            if ru_trace and en_trace:
                differences = self._compare_semantic_data(ru_trace.data, en_trace.data)
                if differences:
                    self.divergence_points.append(DivergencePoint(
                        step=step,
                        russian_trace=ru_trace,
                        english_trace=en_trace,
                        differences=differences
                    ))
            elif ru_trace or en_trace:
                # Missing trace in one mode
                self.divergence_points.append(DivergencePoint(
                    step=step,
                    russian_trace=ru_trace,
                    english_trace=en_trace,
                    differences={"missing_trace": f"Missing in {'Russian' if en_trace else 'English'} mode"}
                ))
        
        return self.divergence_points
    
    def _compare_semantic_data(self, ru_data: Any, en_data: Any) -> Dict[str, Any]:
        differences = {}
        
        if type(ru_data) != type(en_data):
            differences["type_mismatch"] = {
                "russian": type(ru_data).__name__,
                "english": type(en_data).__name__
            }
            return differences
        
        if isinstance(ru_data, dict) and isinstance(en_data, dict):
            ru_keys = set(ru_data.keys())
            en_keys = set(en_data.keys())
            
            if ru_keys != en_keys:
                differences["key_difference"] = {
                    "russian_only": list(ru_keys - en_keys),
                    "english_only": list(en_keys - ru_keys)
                }
            
            common_keys = ru_keys & en_keys
            for key in common_keys:
                sub_diff = self._compare_semantic_data(ru_data[key], en_data[key])
                if sub_diff:
                    differences[f"key_{key}"] = sub_diff
                    
        elif isinstance(ru_data, (list, tuple)) and isinstance(en_data, (list, tuple)):
            if len(ru_data) != len(en_data):
                differences["length_mismatch"] = {
                    "russian": len(ru_data),
                    "english": len(en_data)
                }
            else:
                for i, (ru_item, en_item) in enumerate(zip(ru_data, en_data)):
                    sub_diff = self._compare_semantic_data(ru_item, en_item)
                    if sub_diff:
                        differences[f"index_{i}"] = sub_diff
                        
        elif ru_data != en_data:
            differences["value_mismatch"] = {
                "russian": ru_data,
                "english": en_data
            }
            
        return differences

class CoherentRuntimeEngine:
    def __init__(self):
        self.comparator = SemanticComparator()
        self.is_testing = False
        self.test_results: Dict[str, Any] = {}
    
    def process_russian(self, input_data: Any) -> Any:
        self.comparator.hook.capture(ProcessingMode.RUSSIAN, "start", input_data)
        
        # Simulate Russian processing logic
        result = self._russian_processing_logic(input_data)
        
        self.comparator.hook.capture(ProcessingMode.RUSSIAN, "end", result)
        return result
    
    def process_english(self, input_data: Any) -> Any:
        self.comparator.hook.capture(ProcessingMode.ENGLISH, "start", input_data)
        
        # Simulate English processing logic
        result = self._english_processing_logic(input_data)
        
        self.comparator.hook.capture(ProcessingMode.ENGLISH, "end", result)
        return result
    
    def _russian_processing_logic(self, data: Any) -> Any:
        self.comparator.hook.capture(ProcessingMode.RUSSIAN, "normalize", data)
        if isinstance(data, str):
            normalized = data.lower().replace("ё", "е")
        else:
            normalized = data
            
        self.comparator.hook.capture(ProcessingMode.RUSSIAN, "tokenize", normalized)
        if isinstance(normalized, str):
            tokens = normalized.split()
        else:
            tokens = normalized
            
        self.comparator.hook.capture(ProcessingMode.RUSSIAN, "process_tokens", tokens)
        # Russian-specific processing
        processed = [f"RU_{token}" for token in tokens] if isinstance(tokens, list) else tokens
        
        return processed
    
    def _english_processing_logic(self, data: Any) -> Any:
        self.comparator.hook.capture(ProcessingMode.ENGLISH, "normalize", data)
        if isinstance(data, str):
            normalized = data.lower()
        else:
            normalized = data
            
        self.comparator.hook.capture(ProcessingMode.ENGLISH, "tokenize", normalized)
        if isinstance(normalized, str):
            tokens = normalized.split()
        else:
            tokens = normalized
            
        self.comparator.hook.capture(ProcessingMode.ENGLISH, "process_tokens", tokens)
        # English-specific processing
        processed = [f"EN_{token}" for token in tokens] if isinstance(tokens, list) else tokens
        
        return processed
    
    def run_coherence_check(self, input_data: Any) -> Tuple[Any, Any, List[DivergencePoint]]:
        self.comparator.hook.clear()
        
        ru_result = self.process_russian(input_data)
        en_result = self.process_english(input_data)
        
        divergences = self.comparator.compare_traces()
        
        return ru_result, en_result, divergences
    
    def run_known_incoherence_tests(self) -> Dict[str, Any]:
        test_cases = [
            {
                "name": "case_1_cyrillic_chars",
                "input": "ёжик в тумане",
                "expected_divergence": True
            },
            {
                "name": "case_2_mixed_script",
                "input": "hello мир",
                "expected_divergence": True
            },
            {
                "name": "case_3_numeric_data",
                "input": {"число": 42, "number": 42},
                "expected_divergence": True
            }
        ]
        
        results = {}
        
        for test_case in test_cases:
            name = test_case["name"]
            input_data = test_case["input"]
            
            ru_result, en_result, divergences = self.run_coherence_check(input_data)
            
            results[name] = {
                "input": input_data,
                "russian_result": ru_result,
                "english_result": en_result,
                "divergences_found": len(divergences) > 0,
                "divergences": [
                    {
                        "step": d.step,
                        "differences": d.differences
                    } for d in divergences
                ],
                "passed": len(divergences) > 0 == test_case.get("expected_divergence", False)
            }
        
        return results

# Global engine instance
engine = CoherentRuntimeEngine()

def run_semantic_comparison(input_data: Any) -> Dict[str, Any]:
    """Public API to run semantic comparison between Russian and English processing"""
    ru_result