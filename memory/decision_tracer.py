import json
import time
from typing import Dict, Any, Tuple
from datetime import datetime

class DecisionTracer:
    def __init__(self, log_file: str = "decision_trace.log"):
        self.log_file = log_file
        self._initialize_log()
    
    def _initialize_log(self):
        """Initialize the log file with an empty array if it doesn't exist"""
        try:
            with open(self.log_file, 'r') as f:
                json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            with open(self.log_file, 'w') as f:
                json.dump([], f)
    
    def _log_entry(self, entry: Dict[str, Any]):
        """Append a new entry to the log file"""
        try:
            with open(self.log_file, 'r') as f:
                data = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            data = []
        
        data.append(entry)
        
        with open(self.log_file, 'w') as f:
            json.dump(data, f, indent=2)
    
    def _create_entry(self, operation_type: str, attachment_score: float, 
                     distrust_score: float, final_decision: str) -> Dict[str, Any]:
        """Create a standardized log entry"""
        return {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "operation_type": operation_type,
            "attachment_score": attachment_score,
            "distrust_score": distrust_score,
            "final_decision": final_decision
        }
    
    def log_memory_write(self, contour_weight: float, distrust_factor: float, 
                        decision: str):
        """Log memory write operations with contour selection weights"""
        entry = self._create_entry(
            operation_type="memory_write",
            attachment_score=contour_weight,
            distrust_score=distrust_factor,
            final_decision=decision
        )
        self._log_entry(entry)
    
    def log_memory_read(self, recall_confidence: float, distrust_threshold: float, 
                       decision: str):
        """Log memory read operations with recall confidence thresholds"""
        entry = self._create_entry(
            operation_type="memory_read",
            attachment_score=recall_confidence,
            distrust_score=distrust_threshold,
            final_decision=decision
        )
        self._log_entry(entry)
    
    def log_conflict_resolution(self, attachment_evidence_weight: float, 
                               distrust_evidence_weight: float, decision: str):
        """Log conflict resolution operations with evidence weighting"""
        entry = self._create_entry(
            operation_type="conflict_resolution",
            attachment_score=attachment_evidence_weight,
            distrust_score=distrust_evidence_weight,
            final_decision=decision
        )
        self._log_entry(entry)
    
    def get_recent_entries(self, limit: int = 10) -> list:
        """Retrieve recent log entries for analysis"""
        try:
            with open(self.log_file, 'r') as f:
                data = json.load(f)
            return data[-limit:] if len(data) > limit else data
        except (FileNotFoundError, json.JSONDecodeError):
            return []
    
    def clear_log(self):
        """Clear all entries from the log"""
        with open(self.log_file, 'w') as f:
            json.dump([], f)

# Global instance for easy access
tracer = DecisionTracer()