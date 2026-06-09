import json
import logging
import traceback
from typing import Any, Dict, List, Optional, Tuple
from dataclasses import dataclass, asdict
from datetime import datetime
import sys

@dataclass
class DivergenceEvent:
    """Structured representation of a divergence event"""
    timestamp: str
    event_type: str
    location: str
    expected_value: Any
    actual_value: Any
    stack_trace: List[Dict[str, Any]]
    context: Dict[str, Any]
    semantic_mismatch: Optional[str] = None
    severity: str = "medium"

class FractureInterrupter:
    """Enhanced interrupter for logging detailed divergence events"""
    
    def __init__(self, log_file: str = "divergence_events.log"):
        self.logger = self._setup_logger(log_file)
        
    def _setup_logger(self, log_file: str) -> logging.Logger:
        """Setup structured logger for divergence events"""
        logger = logging.getLogger("FractureInterrupter")
        logger.setLevel(logging.INFO)
        
        # Clear existing handlers
        logger.handlers.clear()
        
        # File handler with JSON formatting
        handler = logging.FileHandler(log_file)
        handler.setFormatter(logging.Formatter('%(message)s'))
        logger.addHandler(handler)
        
        # Prevent propagation to root logger
        logger.propagate = False
        
        return logger
    
    def _capture_stack_trace(self) -> List[Dict[str, Any]]:
        """Capture current stack trace excluding this class methods"""
        stack_frames = []
        for frame_info in traceback.extract_stack():
            # Skip internal fracture interrupter frames
            if 'fracture_interrupter' not in frame_info.filename:
                stack_frames.append({
                    'filename': frame_info.filename,
                    'lineno': frame_info.lineno,
                    'function': frame_info.name,
                    'code': frame_info.line
                })
        return stack_frames
    
    def _analyze_semantic_mismatch(self, expected: Any, actual: Any) -> Optional[str]:
        """Analyze semantic differences between values"""
        if type(expected) != type(actual):
            return f"Type mismatch: expected {type(expected).__name__}, got {type(actual).__name__}"
        
        if isinstance(expected, (int, float)) and isinstance(actual, (int, float)):
            if expected == 0 and actual != 0:
                return "Zero value expectation violated"
            elif actual == 0 and expected != 0:
                return "Unexpected zero value"
            elif expected != 0:
                relative_diff = abs((actual - expected) / expected)
                if relative_diff > 0.1:  # 10% threshold
                    return f"Significant numerical divergence ({relative_diff:.2%})"
        
        if isinstance(expected, str) and isinstance(actual, str):
            if expected.lower() != actual.lower():
                return "Case-sensitive string mismatch"
            else:
                return "String content differs with case variations"
        
        return None
    
    def _create_context_snapshot(self) -> Dict[str, Any]:
        """Create snapshot of relevant execution context"""
        frame = sys._getframe(2)  # Go back two frames to get caller context
        context = {
            'locals': {},
            'globals': {}
        }
        
        # Capture limited local variables (avoid memory issues)
        for key, value in frame.f_locals.items():
            if not key.startswith('_') and isinstance(value, (str, int, float, bool, list, dict)):
                try:
                    serialized_value = json.dumps(value, default=str)
                    context['locals'][key] = serialized_value
                except (TypeError, ValueError):
                    context['locals'][key] = str(value)
        
        # Capture some global context
        context['globals']['__file__'] = frame.f_globals.get('__file__', 'unknown')
        context['globals']['__name__'] = frame.f_globals.get('__name__', 'unknown')
        
        return context
    
    def log_divergence(
        self,
        event_type: str,
        location: str,
        expected: Any,
        actual: Any,
        severity: str = "medium",
        additional_context: Optional[Dict[str, Any]] = None
    ) -> None:
        """Log a detailed divergence event"""
        event = DivergenceEvent(
            timestamp=datetime.utcnow().isoformat() + 'Z',
            event_type=event_type,
            location=location,
            expected_value=expected,
            actual_value=actual,
            stack_trace=self._capture_stack_trace(),
            context=self._create_context_snapshot(),
            semantic_mismatch=self._analyze_semantic_mismatch(expected, actual),
            severity=severity
        )
        
        # Add any additional context
        if additional_context:
            event.context.update(additional_context)
        
        # Log as structured JSON
        self.logger.info(json.dumps(asdict(event), default=str))
    
    def assert_equal(
        self,
        expected: Any,
        actual: Any,
        location: str = "unknown",
        message: str = "",
        severity: str = "high"
    ) -> bool:
        """Assert equality and log divergence if assertion fails"""
        if expected == actual:
            return True
            
        context = {'assertion_message': message} if message else {}
        self.log_divergence(
            event_type="ASSERTION_FAILURE",
            location=location,
            expected=expected,
            actual=actual,
            severity=severity,
            additional_context=context
        )
        return False
    
    def validate_contract(
        self,
        contract_name: str,
        inputs: Dict[str, Any],
        outputs: Dict[str, Any],
        expected_outputs: Dict[str, Any],
        location: str = "contract_validation"
    ) -> bool:
        """Validate contract outputs against expectations"""
        success = True
        for key, expected_value in expected_outputs.items():
            actual_value = outputs.get(key)
            if expected_value != actual_value:
                context = {
                    'contract': contract_name,
                    'input_parameters': inputs,
                    'output_key': key
                }
                self.log_divergence(
                    event_type="CONTRACT_VIOLATION",
                    location=f"{location}.{key}",
                    expected=expected_value,
                    actual=actual_value,
                    severity="high",
                    additional_context=context
                )
                success = False
        return success

# Global instance for easy access
interrupter = FractureInterrupter()

def log_divergence_event(
    event_type: str,
    location: str,
    expected: Any,
    actual: Any,
    severity: str = "medium",
    additional_context: Optional[Dict[str, Any]] = None
) -> None:
    """Convenience function for logging divergence events"""
    interrupter.log_divergence(event_type, location, expected, actual, severity, additional_context)

def assert_values_equal(
    expected: Any,
    actual: Any,
    location: str = "unknown",
    message: str = "",
    severity: str = "high"
) -> bool:
    """Convenience function for asserting equality"""
    return interrupter.assert_equal(expected, actual, location, message, severity)

def validate_smart_contract(
    contract_name: str,
    inputs: Dict[str, Any],
    outputs: Dict[str, Any],
    expected_outputs: Dict[str, Any],
    location: str = "contract_validation"
) -> bool:
    """Convenience function for validating smart contracts"""
    return interrupter.validate_contract(contract_name, inputs, outputs, expected_outputs, location)