import json
import time
from typing import Any, Dict, List, Optional
from dataclasses import dataclass, asdict
from datetime import datetime
from pathlib import Path


@dataclass
class MemoryOperationLog:
    timestamp: float
    operation_type: str  # 'write', 'update', 'delete'
    target_memory_contour: str
    result: str  # 'success', 'conflict', 'error'
    details: Optional[str] = None


class SelfReflectionTracer:
    def __init__(self, log_file_path: str = "memory_operations.log"):
        self.log_file_path = Path(log_file_path)
        self._ensure_log_file_exists()

    def _ensure_log_file_exists(self):
        """Ensure the log file exists, creating it if necessary."""
        if not self.log_file_path.exists():
            self.log_file_path.touch()

    def _append_log(self, log_entry: MemoryOperationLog):
        """Append a log entry to the log file."""
        with open(self.log_file_path, 'a') as f:
            f.write(json.dumps(asdict(log_entry)) + '\n')

    def log_operation(self, operation_type: str, target_memory_contour: str, 
                     result: str, details: Optional[str] = None):
        """
        Log a memory operation.
        
        Args:
            operation_type: Type of operation ('write', 'update', 'delete')
            target_memory_contour: Identifier for the memory being modified
            result: Outcome of the operation ('success', 'conflict', 'error')
            details: Optional additional information about the operation
        """
        log_entry = MemoryOperationLog(
            timestamp=time.time(),
            operation_type=operation_type,
            target_memory_contour=target_memory_contour,
            result=result,
            details=details
        )
        self._append_log(log_entry)

    def get_recent_logs(self, limit: int = 100) -> List[Dict[str, Any]]:
        """
        Retrieve recent log entries.
        
        Args:
            limit: Maximum number of entries to retrieve
            
        Returns:
            List of log entries as dictionaries
        """
        logs = []
        try:
            with open(self.log_file_path, 'r') as f:
                lines = f.readlines()
                # Read from newest to oldest
                for line in reversed(lines[-limit:]):
                    logs.append(json.loads(line.strip()))
        except FileNotFoundError:
            pass
        return logs

    def query_logs(self, operation_type: Optional[str] = None, 
                   result: Optional[str] = None, 
                   target_memory_contour: Optional[str] = None,
                   limit: int = 100) -> List[Dict[str, Any]]:
        """
        Query log entries based on filters.
        
        Args:
            operation_type: Filter by operation type
            result: Filter by result
            target_memory_contour: Filter by memory contour
            limit: Maximum number of entries to retrieve
            
        Returns:
            List of matching log entries
        """
        all_logs = self.get_recent_logs(limit * 10)  # Get more entries to filter
        filtered_logs = []
        
        for log in all_logs:
            if operation_type and log['operation_type'] != operation_type:
                continue
            if result and log['result'] != result:
                continue
            if target_memory_contour and log['target_memory_contour'] != target_memory_contour:
                continue
                
            filtered_logs.append(log)
            if len(filtered_logs) >= limit:
                break
                
        return filtered_logs

    def get_statistics(self) -> Dict[str, Any]:
        """Get statistics about recent operations."""
        logs = self.get_recent_logs(1000)
        if not logs:
            return {"total_operations": 0}
        
        operation_counts = {}
        result_counts = {}
        memory_contour_counts = {}
        
        for log in logs:
            op_type = log['operation_type']
            result = log['result']
            contour = log['target_memory_contour']
            
            operation_counts[op_type] = operation_counts.get(op_type, 0) + 1
            result_counts[result] = result_counts.get(result, 0) + 1
            memory_contour_counts[contour] = memory_contour_counts.get(contour, 0) + 1
        
        return {
            "total_operations": len(logs),
            "operation_types": operation_counts,
            "results": result_counts,
            "most_active_memory_contours": dict(
                sorted(memory_contour_counts.items(), key=lambda x: x[1], reverse=True)[:10]
            ),
            "since": datetime.fromtimestamp(logs[-1]['timestamp']).isoformat() if logs else None
        }