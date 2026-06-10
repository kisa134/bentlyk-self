import logging
import time
import traceback
from typing import Any, Dict, List, Optional, Tuple
import json

class FractureInterrupter:
    def __init__(self, log_file: str = "fracture_trace.log"):
        self.logger = self._setup_logger(log_file)
        self.fracture_stack: List[Dict[str, Any]] = []
        self.divergence_points: List[Dict[str, Any]] = []
        
    def _setup_logger(self, log_file: str) -> logging.Logger:
        logger = logging.getLogger("FractureInterrupter")
        logger.setLevel(logging.DEBUG)
        
        # Clear any existing handlers
        logger.handlers.clear()
        
        # File handler for structured logging
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(logging.DEBUG)
        
        # Console handler for immediate feedback
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.WARNING)
        
        # Structured formatter
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        file_handler.setFormatter(formatter)
        console_handler.setFormatter(formatter)
        
        logger.addHandler(file_handler)
        logger.addHandler(console_handler)
        
        return logger

    def push_context(self, layer: str, operation: str, data: Any) -> None:
        """Push processing context onto the stack"""
        context = {
            "timestamp": time.time(),
            "layer": layer,
            "operation": operation,
            "data_snapshot": self._serialize_data(data),
            "stack_depth": len(self.fracture_stack)
        }
        self.fracture_stack.append(context)
        self.logger.debug(f"Context pushed: {layer}/{operation}")

    def pop_context(self) -> Optional[Dict[str, Any]]:
        """Pop processing context from the stack"""
        if self.fracture_stack:
            context = self.fracture_stack.pop()
            self.logger.debug(f"Context popped: {context['layer']}/{context['operation']}")
            return context
        return None

    def check_semantic_fracture(self, ru_data: Any, en_data: Any, 
                              layer: str, operation: str) -> bool:
        """Check for semantic divergence between Russian and English processing"""
        divergence = not self._semantic_equivalence(ru_data, en_data)
        
        if divergence:
            divergence_point = {
                "timestamp": time.time(),
                "layer": layer,
                "operation": operation,
                "ru_data": self._serialize_data(ru_data),
                "en_data": self._serialize_data(en_data),
                "stack_trace": self._capture_stack_trace(),
                "context_stack": self._snapshot_context_stack()
            }
            
            self.divergence_points.append(divergence_point)
            self._log_fracture(divergence_point)
            
        return divergence

    def _semantic_equivalence(self, ru_data: Any, en_data: Any) -> bool:
        """Determine semantic equivalence between data structures"""
        # Handle None cases
        if ru_data is None and en_data is None:
            return True
        if ru_data is None or en_data is None:
            return False
            
        # Handle basic types
        if isinstance(ru_data, (str, int, float, bool)) and isinstance(en_data, (str, int, float, bool)):
            return ru_data == en_data
            
        # Handle lists
        if isinstance(ru_data, list) and isinstance(en_data, list):
            if len(ru_data) != len(en_data):
                return False
            return all(self._semantic_equivalence(ru_item, en_item) 
                      for ru_item, en_item in zip(ru_data, en_data))
                      
        # Handle dicts
        if isinstance(ru_data, dict) and isinstance(en_data, dict):
            if set(ru_data.keys()) != set(en_data.keys()):
                return False
            return all(self._semantic_equivalence(ru_data[key], en_data[key]) 
                      for key in ru_data.keys())
                      
        # Handle objects with __dict__
        if hasattr(ru_data, '__dict__') and hasattr(en_data, '__dict__'):
            return self._semantic_equivalence(ru_data.__dict__, en_data.__dict__)
            
        # Fallback to string comparison for complex objects
        return str(ru_data) == str(en_data)

    def _serialize_data(self, data: Any) -> Dict[str, Any]:
        """Serialize data for logging"""
        try:
            if isinstance(data, (str, int, float, bool, type(None))):
                return {"type": type(data).__name__, "value": data}
            elif isinstance(data, (list, tuple)):
                return {
                    "type": type(data).__name__,
                    "length": len(data),
                    "sample": [self._serialize_data(item) for item in data[:3]] if data else []
                }
            elif isinstance(data, dict):
                return {
                    "type": "dict",
                    "keys": list(data.keys())[:10],  # Limit keys for brevity
                    "size": len(data)
                }
            else:
                return {
                    "type": type(data).__name__,
                    "repr": str(data)[:200]  # Limit string length
                }
        except Exception as e:
            return {"type": "unknown", "error": str(e)}

    def _capture_stack_trace(self) -> List[str]:
        """Capture current stack trace"""
        return traceback.format_stack()[:-1]  # Exclude this method call

    def _snapshot_context_stack(self) -> List[Dict[str, Any]]:
        """Create a snapshot of the current context stack"""
        return [ctx.copy() for ctx in self.fracture_stack]

    def _log_fracture(self, divergence_point: Dict[str, Any]) -> None:
        """Log fracture information in structured format"""
        log_entry = {
            "event_type": "semantic_fracture",
            "timestamp": divergence_point["timestamp"],
            "location": f"{divergence_point['layer']}.{divergence_point['operation']}",
            "divergence_details": {
                "ru_data": divergence_point["ru_data"],
                "en_data": divergence_point["en_data"]
            },
            "stack_context": divergence_point["context_stack"],
            "full_trace": divergence_point["stack_trace"]
        }
        
        self.logger.warning(f"SEMANTIC FRACTURE DETECTED: {json.dumps(log_entry, indent=2)}")

    def get_fracture_report(self) -> Dict[str, Any]:
        """Generate a comprehensive fracture report"""
        return {
            "total_fractures": len(self.divergence_points),
            "fractures": self.divergence_points,
            "current_context_depth": len(self.fracture_stack),
            "active_context": self.fracture_stack[-1] if self.fracture_stack else None
        }

    def clear_fractures(self) -> None:
        """Clear recorded fractures"""
        self.divergence_points.clear()
        self.logger.info("Fracture records cleared")

    def dump_fracture_log(self, filename: str) -> None:
        """Dump all fracture information to a JSON file"""
        report = self.get_fracture_report()
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        self.logger.info(f"Fracture log dumped to {filename}")