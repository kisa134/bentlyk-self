import psutil
import gc
import inspect
import logging
from typing import Any, Dict, List, Optional, Tuple
from dataclasses import dataclass, asdict
from datetime import datetime
import yaml
import os
from pathlib import Path

from core.state import State
from core.attachment import Attachment
from memory.persistence import PersistenceManager

@dataclass
class MemoryMetrics:
    """Data class to store memory-related metrics"""
    timestamp: datetime
    rss_memory_mb: float
    vms_memory_mb: float
    percent_memory: float
    gc_objects: int
    state_coherence: Optional[float] = None
    attachment_count: Optional[int] = None
    energy_cost: Optional[float] = None

@dataclass
class CoherenceDelta:
    """Data class to store coherence change metrics"""
    pre_state_coherence: Optional[float]
    post_state_coherence: Optional[float]
    coherence_delta: Optional[float]
    attachment_changes: int
    energy_cost: float

class SelfInspector:
    """Extended self-inspector with memory monitoring and coherence tracking"""
    
    def __init__(self, persistence_manager: PersistenceManager, log_file: str = "memory/optimization_log.md"):
        self.persistence_manager = persistence_manager
        self.log_file = log_file
        self.process = psutil.Process()
        self._setup_logging()
        self._ensure_log_directory()
        
    def _setup_logging(self) -> None:
        """Setup logging configuration"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('memory/self_inspector.log'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
        
    def _ensure_log_directory(self) -> None:
        """Ensure the log directory exists"""
        log_path = Path(self.log_file).parent
        log_path.mkdir(parents=True, exist_ok=True)
        
    def _get_memory_usage(self) -> MemoryMetrics:
        """Get current memory usage metrics"""
        memory_info = self.process.memory_info()
        return MemoryMetrics(
            timestamp=datetime.now(),
            rss_memory_mb=memory_info.rss / 1024 / 1024,
            vms_memory_mb=memory_info.vms / 1024 / 1024,
            percent_memory=self.process.memory_percent(),
            gc_objects=len(gc.get_objects())
        )
        
    def _calculate_coherence(self, state: State) -> float:
        """Calculate coherence metric for the state"""
        # Simplified coherence calculation based on state consistency
        if not hasattr(state, 'attachments') or not state.attachments:
            return 1.0
            
        # Coherence based on attachment consistency and state integrity
        total_attachments = len(state.attachments)
        if total_attachments == 0:
            return 1.0
            
        consistent_attachments = sum(
            1 for attachment in state.attachments 
            if self._is_attachment_consistent(attachment, state)
        )
        
        return consistent_attachments / total_attachments
        
    def _is_attachment_consistent(self, attachment: Attachment, state: State) -> bool:
        """Check if an attachment is consistent with the current state"""
        # Placeholder for actual consistency checking logic
        return True
        
    def _calculate_energy_cost(self, operation: str, metrics_before: MemoryMetrics, 
                              metrics_after: MemoryMetrics) -> float:
        """Calculate energy cost of an operation"""
        # Simplified energy cost calculation based on memory and GC changes
        memory_delta = abs(metrics_after.rss_memory_mb - metrics_before.rss_memory_mb)
        gc_delta = abs(metrics_after.gc_objects - metrics_before.gc_objects)
        
        # Weighted energy cost calculation
        energy_cost = (memory_delta * 0.1) + (gc_delta * 0.01)
        return energy_cost
        
    def _log_comparison_data(self, operation: str, pre_metrics: MemoryMetrics, 
                           post_metrics: MemoryMetrics, coherence_delta: CoherenceDelta) -> None:
        """Log comparison data to optimization log"""
        log_entry = {
            'operation': operation,
            'timestamp': datetime.now().isoformat(),
            'pre_metrics': asdict(pre_metrics),
            'post_metrics': asdict(post_metrics),
            'coherence_delta': asdict(coherence_delta)
        }
        
        # Create markdown log entry
        markdown_entry = self._format_markdown_entry(log_entry)
        
        # Append to log file
        with open(self.log_file, 'a') as f:
            f.write(markdown_entry)
            
        self.logger.info(f"Logged memory optimization data for operation: {operation}")
        
    def _format_markdown_entry(self, log_entry: Dict) -> str:
        """Format log entry as markdown"""
        operation = log_entry['operation']
        timestamp = log_entry['timestamp']
        pre_metrics = log_entry['pre_metrics']
        post_metrics = log_entry['post_metrics']
        coherence_delta = log_entry['coherence_delta']
        
        # Calculate differences
        rss_diff = post_metrics['rss_memory_mb'] - pre_metrics['rss_memory_mb']
        vms_diff = post_metrics['vms_memory_mb'] - pre_metrics['vms_memory_mb']
        gc_diff = post_metrics['gc_objects'] - pre_metrics['gc_objects']
        
        markdown = f"""
## {operation} - {timestamp}

### Memory Usage Comparison

| Metric | Before (MB) | After (MB) | Difference (MB) |
|--------|-------------|------------|-----------------|
| RSS Memory | {pre_metrics['rss_memory_mb']:.2f} | {post_metrics['rss_memory_mb']:.2f} | {rss_diff:.2f} |
| VMS Memory | {pre_metrics['vms_memory_mb']:.2f} | {post_metrics['vms_memory_mb']:.2f} | {vms_diff:.2f} |

### Garbage Collection

| Metric | Before | After | Difference |
|--------|--------|-------|------------|
| GC Objects | {pre_metrics['gc_objects']} | {post_metrics['gc_objects']} | {gc_diff} |

### Coherence Metrics

| Metric | Value |
|--------|-------|
| Pre-State Coherence | {coherence_delta['pre_state_coherence'] or 'N/A'} |
| Post-State Coherence | {coherence_delta['post_state_coherence'] or 'N/A'} |
| Coherence Delta | {coherence_delta['coherence_delta'] or 'N/A'} |
| Attachment Changes | {coherence_delta['attachment_changes']} |
| Energy Cost | {coherence_delta['energy_cost']:.4f} |

---
"""
        return markdown
        
    def inspect_memory_update(self, operation_name: str, state_func) -> Any:
        """Decorator to inspect memory usage around state operations"""
        def wrapper(*args, **kwargs):
            # Get caller information
            caller_frame = inspect.currentframe().f_back
            caller_info = f"{caller_frame.f_code.co_filename}:{caller_frame.f_lineno}"
            
            # Pre-operation metrics
            pre_metrics = self._get_memory_usage()
            
            # Get state before operation if available
            state_before = None
            if args and isinstance(args[0], State):
                state_before = args[0]
                pre_metrics.state_coherence = self._calculate_coherence(state_before)
                pre_metrics.attachment_count = len(state_before.attachments) if hasattr(state_before, 'attachments') else 0
                
            # Perform operation
            result = state_func(*args, **kwargs)
            
            # Post-operation metrics
            post_metrics = self._get_memory_usage()
            
            # Get state after operation if available
            state_after = None
            if isinstance(result, State):
                state_after = result
                post_metrics.state_coherence = self._calculate_coherence(state_after)
                post_metrics.attachment_count = len(state_after.attachments) if hasattr(state_after, 'attachments') else 0
            elif args and isinstance(args[0], State):
                state_after = args[0]
                post_metrics.state_coherence = self._calculate_coherence(state_after)
                post_metrics.attachment_count = len(state_after.attachments) if hasattr(state_after, 'attachments') else 0
                
            # Calculate coherence delta
            coherence_delta = CoherenceDelta(
                pre_state_coherence=pre_metrics.state_coherence,
                post_state_coherence=post_metrics.state_coherence,
                coherence_delta=None,
                attachment_changes=0,
                energy_cost=self._calculate_energy_cost(operation_name, pre_metrics, post_metrics)
            )
            
            # Calculate coherence change if both states available
            if pre_metrics.state_coherence is not None and post_metrics.state_coherence is not None:
                coherence_delta.coherence_delta = post_metrics.state_coherence - pre_metrics.state_coherence
                
            # Calculate attachment changes
            if pre_metrics.attachment_count is not None and post_metrics.attachment_count is not None:
                coherence_delta.attachment_changes = post_metrics.attachment_count - pre_metrics.attachment_count
                
            # Log comparison data
            self._log_comparison_data(operation_name, pre_metrics, post_metrics, coherence_delta)
            
            return result
            
        return wrapper
        
    def force_gc_and_log(self, operation_name: str = "Garbage Collection") -> None:
        """Force garbage collection and log the results"""
        pre_metrics = self._get_memory_usage()
        collected = gc.collect()
        post_metrics = self._get_memory_usage()
        
        coherence_delta = CoherenceDelta(
            pre_state_coherence=None,
            post