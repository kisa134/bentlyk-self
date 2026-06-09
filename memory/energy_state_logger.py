import time
import json
import threading
from datetime import datetime
from typing import Dict, Any, Optional
from pathlib import Path

class EnergyStateLogger:
    def __init__(self, log_file: str = "energy_state_log.jsonl"):
        self.log_file = Path(log_file)
        self.log_file.parent.mkdir(exist_ok=True)
        self.running = False
        self.log_thread: Optional[threading.Thread] = None
        self.energy_level = 0.0
        self.focus_level = 0.0
        self.current_task = ""
        self.task_outcome = ""
        self.lock = threading.Lock()
        
    def start_logging(self, interval: float = 60.0):
        """Start continuous logging in background thread"""
        if self.running:
            return
            
        self.running = True
        self.log_thread = threading.Thread(
            target=self._log_loop, 
            args=(interval,), 
            daemon=True
        )
        self.log_thread.start()
        
    def stop_logging(self):
        """Stop continuous logging"""
        self.running = False
        if self.log_thread:
            self.log_thread.join()
            
    def _log_loop(self, interval: float):
        """Main logging loop"""
        while self.running:
            try:
                self._log_current_state()
                time.sleep(interval)
            except Exception:
                if self.running:  # Only break if not intentionally stopped
                    self.running = False
                    break
                    
    def _log_current_state(self):
        """Log current energy/focus state to file"""
        timestamp = datetime.utcnow().isoformat()
        log_entry = {
            "timestamp": timestamp,
            "energy_level": self.energy_level,
            "focus_level": self.focus_level,
            "current_task": self.current_task,
            "task_outcome": self.task_outcome
        }
        
        with self.lock:
            with open(self.log_file, "a") as f:
                f.write(json.dumps(log_entry) + "\n")
                
    def update_energy(self, level: float):
        """Update current energy level (0.0 to 1.0)"""
        with self.lock:
            self.energy_level = max(0.0, min(1.0, level))
            
    def update_focus(self, level: float):
        """Update current focus level (0.0 to 1.0)"""
        with self.lock:
            self.focus_level = max(0.0, min(1.0, level))
            
    def set_task(self, task_description: str):
        """Set current task being performed"""
        with self.lock:
            self.current_task = task_description
            
    def set_outcome(self, outcome: str):
        """Set outcome of current task"""
        with self.lock:
            self.task_outcome = outcome
            
    def get_recent_states(self, limit: int = 10) -> list:
        """Get recent log entries"""
        entries = []
        try:
            with open(self.log_file, "r") as f:
                lines = f.readlines()[-limit:]
                for line in lines:
                    entries.append(json.loads(line.strip()))
        except FileNotFoundError:
            pass
        return entries

# Global instance for easy access
energy_logger = EnergyStateLogger()

def start_energy_logging(interval: float = 60.0):
    """Convenience function to start logging"""
    energy_logger.start_logging(interval)

def stop_energy_logging():
    """Convenience function to stop logging"""
    energy_logger.stop_logging()

def log_memory_attempt(memory_id: str, modification_type: str, success: bool):
    """Log a memory modification attempt with current state"""
    timestamp = datetime.utcnow().isoformat()
    log_entry = {
        "timestamp": timestamp,
        "event_type": "memory_modification",
        "memory_id": memory_id,
        "modification_type": modification_type,
        "success": success,
        "energy_level": energy_logger.energy_level,
        "focus_level": energy_logger.focus_level,
        "context_task": energy_logger.current_task
    }
    
    log_file = Path("memory_modification_log.jsonl")
    with open(log_file, "a") as f:
        f.write(json.dumps(log_entry) + "\n")