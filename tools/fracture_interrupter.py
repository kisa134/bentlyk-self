import json
import logging
from datetime import datetime
from typing import Dict, Any, Tuple
import sys
import os

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tools.multilingual_coherence import MultilingualCoherenceAnalyzer
from tools.unified_runtime_validator import UnifiedRuntimeValidator

class FractureInterrupter:
    def __init__(self, log_file: str = "fracture_traces.log"):
        self.coherence_analyzer = MultilingualCoherenceAnalyzer()
        self.runtime_validator = UnifiedRuntimeValidator()
        
        # Setup logging
        self.logger = logging.getLogger("FractureInterrupter")
        self.logger.setLevel(logging.INFO)
        
        # Clear any existing handlers
        self.logger.handlers.clear()
        
        # File handler for structured logging
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(logging.INFO)
        
        # Console handler for immediate feedback
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.WARNING)
        
        # Structured formatter
        formatter = logging.Formatter('%(message)s')
        file_handler.setFormatter(formatter)
        console_handler.setFormatter(formatter)
        
        self.logger.addHandler(file_handler)
        self.logger.addHandler(console_handler)
        
        self.trace_buffer = []

    def detect_fracture_point(self, english_text: str, russian_text: str) -> Tuple[int, str]:
        """
        Detect the exact point of semantic divergence between texts.
        Returns (position, reason) tuple.
        """
        eng_words = english_text.split()
        rus_words = russian_text.split()
        
        min_length = min(len(eng_words), len(rus_words))
        
        for i in range(min_length):
            eng_segment = ' '.join(eng_words[:i+1])
            rus_segment = ' '.join(rus_words[:i+1])
            
            coherence_score = self.coherence_analyzer.analyze_coherence(
                eng_segment, rus_segment
            )
            
            if coherence_score < 0.7:  # Threshold for semantic fracture
                return i, f"Coherence score dropped to {coherence_score:.3f}"
        
        return -1, "No fracture detected"

    def validate_runtime_response(self, english_text: str, russian_text: str) -> Dict[str, Any]:
        """Validate the runtime response using unified validator."""
        return self.runtime_validator.validate(english_text, russian_text)

    def log_validation_trace(self, trace_data: Dict[str, Any]):
        """Log structured validation trace for analysis."""
        trace_entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "trace_id": len(self.trace_buffer),
            "fracture_point": trace_data.get("fracture_point", -1),
            "divergence_reason": trace_data.get("divergence_reason", ""),
            "coherence_analysis": trace_data.get("coherence_analysis", {}),
            "runtime_validation": trace_data.get("runtime_validation", {}),
            "english_segment": trace_data.get("english_segment", ""),
            "russian_segment": trace_data.get("russian_segment", "")
        }
        
        self.trace_buffer.append(trace_entry)
        self.logger.info(json.dumps(trace_entry))

    def process_fracture(self, english_text: str, russian_text: str):
        """Process induced semantic fracture and log complete trace."""
        # 1. Detect exact point of divergence
        fracture_pos, divergence_reason = self.detect_fracture_point(
            english_text, russian_text
        )
        
        # Extract segments up to fracture point
        eng_words = english_text.split()
        rus_words = russian_text.split()
        
        if fracture_pos >= 0:
            eng_segment = ' '.join(eng_words[:fracture_pos+1])
            rus_segment = ' '.join(rus_words[:fracture_pos+1])
        else:
            eng_segment = english_text
            rus_segment = russian_text
        
        # 2. Capture semantic mismatch from multilingual_coherence
        coherence_analysis = self.coherence_analyzer.detailed_analysis(
            eng_segment, rus_segment
        )
        
        # 3. Get response from unified_runtime_validator
        runtime_validation = self.validate_runtime_response(
            eng_segment, rus_segment
        )
        
        # Structure trace data
        trace_data = {
            "fracture_point": fracture_pos,
            "divergence_reason": divergence_reason,
            "coherence_analysis": coherence_analysis,
            "runtime_validation": runtime_validation,
            "english_segment": eng_segment,
            "russian_segment": rus_segment
        }
        
        # Log for analysis
        self.log_validation_trace(trace_data)
        
        return trace_data

    def get_trace_buffer(self) -> list:
        """Return all collected traces."""
        return self.trace_buffer.copy()

    def clear_traces(self):
        """Clear trace buffer."""
        self.trace_buffer.clear()

if __name__ == "__main__":
    # Example usage
    interrupter = FractureInterrupter()
    
    # Test case - induced semantic fracture
    english = "The system will process all data inputs and generate reports automatically"
    russian = "Система обработает все входные данные и автоматически сгенерирует отчеты"
    
    # Process and log fracture
    trace = interrupter.process_fracture(english, russian)
    
    print("Fracture Processing Complete")
    print(f"Trace ID: {len(interrupter.get_trace_buffer()) - 1}")
    print(f"Fracture Point: {trace['fracture_point']}")
    print(f"Divergence Reason: {trace['divergence_reason']}")