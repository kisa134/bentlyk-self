import heapq
from collections import defaultdict, Counter
from typing import List, Dict, Tuple, Any
from dataclasses import dataclass

@dataclass
class TraceOperation:
    operation: str
    energy_cost: float
    cycle_id: int
    timestamp: float
    metadata: Dict[str, Any]

class GrowthLoopOptimizer:
    def __init__(self, analysis_interval: int = 10):
        self.analysis_interval = analysis_interval
        self.cycle_count = 0
        self.traces: List[TraceOperation] = []
        self.refactoring_proposals: List[str] = []
        
    def record_operation(self, operation: str, energy_cost: float, timestamp: float, **metadata):
        trace = TraceOperation(
            operation=operation,
            energy_cost=energy_cost,
            cycle_id=self.cycle_count,
            timestamp=timestamp,
            metadata=metadata
        )
        self.traces.append(trace)
        
    def advance_cycle(self):
        self.cycle_count += 1
        if self.cycle_count % self.analysis_interval == 0:
            self._analyze_and_propose()
            
    def _analyze_and_propose(self):
        # Get traces from last 10 cycles
        recent_traces = [t for t in self.traces if t.cycle_id >= self.cycle_count - 10]
        
        if not recent_traces:
            return
            
        # Aggregate by operation type
        energy_by_operation = defaultdict(float)
        count_by_operation = defaultdict(int)
        
        for trace in recent_traces:
            energy_by_operation[trace.operation] += trace.energy_cost
            count_by_operation[trace.operation] += 1
            
        # Find top energy consumers
        top_operations = heapq.nlargest(3, energy_by_operation.items(), key=lambda x: x[1])
        
        if not top_operations:
            return
            
        # Generate proposal based on highest energy operation
        worst_operation, total_energy = top_operations[0]
        avg_energy = total_energy / count_by_operation[worst_operation]
        
        proposal = self._generate_proposal(worst_operation, avg_energy, count_by_operation[worst_operation])
        self.refactoring_proposals.append(proposal)
        
    def _generate_proposal(self, operation: str, avg_energy: float, count: int) -> str:
        # Simple rule-based proposals - in practice this would be more sophisticated
        if "loop" in operation.lower() or "iteration" in operation.lower():
            return f"Optimize {operation}: High energy consumption ({avg_energy:.2f} avg) over {count} instances. Consider loop unrolling or batch processing."
        elif "allocation" in operation.lower() or "memory" in operation.lower():
            return f"Optimize {operation}: High energy consumption ({avg_energy:.2f} avg) over {count} instances. Consider object pooling or reducing allocations."
        elif "network" in operation.lower() or "io" in operation.lower():
            return f"Optimize {operation}: High energy consumption ({avg_energy:.2f} avg) over {count} instances. Consider batching requests or caching."
        else:
            return f"Optimize {operation}: High energy consumption ({avg_energy:.2f} avg) over {count} instances. Investigate algorithmic improvements."
            
    def get_latest_proposal(self) -> str:
        return self.refactoring_proposals[-1] if self.refactoring_proposals else "No proposals available"
        
    def get_all_proposals(self) -> List[str]:
        return self.refactoring_proposals.copy()

# Example usage
if __name__ == "__main__":
    optimizer = GrowthLoopOptimizer(analysis_interval=5)
    
    # Simulate operations
    import time
    import random
    
    operations = ["data_processing_loop", "memory_allocation", "network_request", "file_io", "calculation"]
    
    for cycle in range(20):
        for _ in range(random.randint(5, 15)):
            op = random.choice(operations)
            energy = random.uniform(0.1, 5.0)
            optimizer.record_operation(op, energy, time.time(), source="test")
        optimizer.advance_cycle()
        
    print("Latest proposal:", optimizer.get_latest_proposal())