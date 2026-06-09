import json
import heapq
from typing import List, Dict, Tuple
from dataclasses import dataclass
from datetime import datetime

@dataclass
class Task:
    id: str
    description: str
    priority: float
    energy_required: float
    clarity_impact: float
    timestamp: datetime

class GrowthCoordinator:
    def __init__(self):
        self.task_queue = []
        self.completed_tasks = []
        self.energy_level = 100.0
        self.clarity_score = 0.0
        
    def analyze_memory_logs(self, log_file: str) -> List[Dict]:
        """Analyze memory modification logs to identify self-improvement opportunities"""
        try:
            with open(log_file, 'r') as f:
                logs = json.load(f)
            return logs
        except FileNotFoundError:
            return []
    
    def get_energy_state(self, energy_log: str) -> float:
        """Retrieve current energy level from energy state logger"""
        try:
            with open(energy_log, 'r') as f:
                data = json.load(f)
                return data.get('current_energy', 100.0)
        except FileNotFoundError:
            return 100.0
    
    def calculate_task_priority(self, task_data: Dict, energy_level: float) -> float:
        """Calculate priority score based on impact and energy efficiency"""
        impact_factor = task_data.get('clarity_impact', 1.0)
        energy_cost = task_data.get('energy_required', 10.0)
        urgency = task_data.get('urgency', 0.5)
        
        # Energy efficiency modifier
        efficiency_modifier = min(1.0, energy_level / energy_cost) if energy_cost > 0 else 1.0
        
        # Priority formula combining impact, efficiency, and urgency
        priority = (impact_factor * 0.4 + efficiency_modifier * 0.3 + urgency * 0.3) 
        return priority
    
    def create_task_from_log(self, log_entry: Dict, energy_level: float) -> Task:
        """Convert log entry into prioritized task"""
        task_id = log_entry.get('id', f"task_{datetime.now().timestamp()}")
        description = log_entry.get('description', 'Self-improvement task')
        energy_required = log_entry.get('energy_required', 10.0)
        clarity_impact = log_entry.get('clarity_impact', 1.0)
        
        priority = self.calculate_task_priority(log_entry, energy_level)
        
        return Task(
            id=task_id,
            description=description,
            priority=priority,
            energy_required=energy_required,
            clarity_impact=clarity_impact,
            timestamp=datetime.now()
        )
    
    def prioritize_tasks(self, memory_logs: List[Dict], energy_level: float) -> List[Task]:
        """Create and prioritize task queue from memory logs"""
        tasks = []
        for log in memory_logs:
            task = self.create_task_from_log(log, energy_level)
            tasks.append(task)
        
        # Sort by priority (highest first)
        tasks.sort(key=lambda x: x.priority, reverse=True)
        return tasks
    
    def simulate_task_execution(self, task: Task) -> Tuple[bool, float, float]:
        """Simulate task execution and return results"""
        if self.energy_level < task.energy_required:
            return False, 0.0, 0.0
            
        # Update energy and clarity
        energy_consumed = task.energy_required
        clarity_gained = task.clarity_impact * (task.priority / 10.0)
        
        return True, energy_consumed, clarity_gained
    
    def execute_optimal_task_sequence(self, memory_log_file: str, energy_log_file: str) -> List[Dict]:
        """Execute tasks in optimal order for maximum growth impact"""
        # Get current state
        memory_logs = self.analyze_memory_logs(memory_log_file)
        self.energy_level = self.get_energy_state(energy_log_file)
        
        # Prioritize tasks
        prioritized_tasks = self.prioritize_tasks(memory_logs, self.energy_level)
        
        results = []
        for task in prioritized_tasks:
            success, energy_used, clarity_gained = self.simulate_task_execution(task)
            
            if success:
                self.energy_level -= energy_used
                self.clarity_score += clarity_gained
                self.completed_tasks.append(task)
                
                results.append({
                    'task_id': task.id,
                    'description': task.description,
                    'completed': True,
                    'energy_used': energy_used,
                    'clarity_gained': clarity_gained,
                    'remaining_energy': self.energy_level
                })
            else:
                results.append({
                    'task_id': task.id,
                    'description': task.description,
                    'completed': False,
                    'reason': 'Insufficient energy',
                    'required_energy': task.energy_required,
                    'available_energy': self.energy_level
                })
        
        return results
    
    def get_growth_metrics(self) -> Dict:
        """Return current growth metrics"""
        return {
            'total_completed_tasks': len(self.completed_tasks),
            'current_clarity_score': self.clarity_score,
            'current_energy_level': self.energy_level,
            'completion_rate': len(self.completed_tasks) / max(len(self.completed_tasks) + len(self.task_queue), 1)
        }

# Example usage
if __name__ == "__main__":
    coordinator = GrowthCoordinator()
    
    # This would typically be called with actual log files
    # results = coordinator.execute_optimal_task_sequence('memory/logs/self_reflection.json', 'memory/logs/energy_state.json')
    # print(coordinator.get_growth_metrics())