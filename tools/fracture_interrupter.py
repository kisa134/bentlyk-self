import json
import logging
import os
import sys
import traceback
from datetime import datetime
from logging.handlers import RotatingFileHandler
from pathlib import Path
from typing import Any, Dict, List, Optional

class FractureInterrupter:
    def __init__(self, log_dir: str = "./fracture_traces/", max_bytes: int = 10*1024*1024, backup_count: int = 5):
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(exist_ok=True)
        
        self.logger = logging.getLogger("fracture_interrupter")
        self.logger.setLevel(logging.INFO)
        
        # Remove existing handlers
        for handler in self.logger.handlers[:]:
            self.logger.removeHandler(handler)
        
        # Create rotating file handler
        log_file = self.log_dir / "fracture_trace.jsonl"
        handler = RotatingFileHandler(
            log_file,
            maxBytes=max_bytes,
            backupCount=backup_count
        )
        handler.setFormatter(logging.Formatter('%(message)s'))
        self.logger.addHandler(handler)
        self.logger.propagate = False

    def capture_fracture(
        self,
        input_pair: Dict[str, str],
        mismatch_scores: Dict[str, float],
        language_weights: Dict[str, float],
        exception: Optional[Exception] = None,
        frame_locals: Optional[Dict[str, Any]] = None
    ):
        """
        Capture and log fracture event with full context.
        
        Args:
            input_pair: Bilingual input that triggered fracture
            mismatch_scores: Coherence validator mismatch scores
            language_weights: Current language mode weights
            exception: Exception that triggered capture (if any)
            frame_locals: Local variables from fracture point (if available)
        """
        fracture_record = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "fracture_event": {
                "input_pair": input_pair,
                "mismatch_scores": mismatch_scores,
                "language_weights": language_weights
            },
            "call_stack": self._capture_call_stack(frame_locals),
            "exception": None
        }
        
        if exception:
            fracture_record["exception"] = {
                "type": type(exception).__name__,
                "message": str(exception),
                "traceback": traceback.format_exc()
            }
        
        # Log as JSONL
        self.logger.info(json.dumps(fracture_record, default=str))

    def _capture_call_stack(self, frame_locals: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """
        Capture the current call stack with local variables.
        
        Args:
            frame_locals: Optional frame locals to include
            
        Returns:
            List of stack frames with details
        """
        stack_trace = []
        frame = sys._getframe().f_back.f_back  # Skip capture_fracture and _capture_call_stack frames
        
        while frame:
            frame_info = {
                "filename": frame.f_code.co_filename,
                "function": frame.f_code.co_name,
                "line_number": frame.f_lineno,
                "locals": {}
            }
            
            # Capture local variables (excluding potentially sensitive ones)
            if frame.f_locals:
                for key, value in frame.f_locals.items():
                    if not key.startswith('__') and not callable(value):
                        try:
                            # Attempt to serialize value
                            json.dumps(value, default=str)
                            frame_info["locals"][key] = value
                        except (TypeError, ValueError):
                            # If not serializable, store as string representation
                            frame_info["locals"][key] = str(value)
            
            stack_trace.append(frame_info)
            frame = frame.f_back
            
        return stack_trace

# Global interrupter instance
_interrupter: Optional[FractureInterrupter] = None

def initialize_interrupter(log_dir: str = "./fracture_traces/"):
    """Initialize the global fracture interrupter."""
    global _interrupter
    _interrupter = FractureInterrupter(log_dir)

def capture_fracture_event(
    input_pair: Dict[str, str],
    mismatch_scores: Dict[str, float],
    language_weights: Dict[str, float],
    exception: Optional[Exception] = None,
    frame_locals: Optional[Dict[str, Any]] = None
):
    """
    Capture a fracture event using the global interrupter.
    
    Args:
        input_pair: Bilingual input that triggered fracture
        mismatch_scores: Coherence validator mismatch scores
        language_weights: Current language mode weights
        exception: Exception that triggered capture (if any)
        frame_locals: Local variables from fracture point (if available)
    """
    global _interrupter
    if _interrupter is None:
        _interrupter = FractureInterrupter()
    
    _interrupter.capture_fracture(
        input_pair,
        mismatch_scores,
        language_weights,
        exception,
        frame_locals
    )

# Backward compatibility
FractureCapture = FractureInterrupter