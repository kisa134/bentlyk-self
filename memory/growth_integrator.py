import time
import json
import threading
from collections import defaultdict, deque
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict
from datetime import datetime

@dataclass
class EnergyCostRecord:
    timestamp: float
    operation: str
    estimated_cost: float
    actual_cost: Optional[float]
    language_context: str
    success: bool

@dataclass
class ContextSwitchRecord:
    timestamp: float
    from_language: str
    to_language: str
    penalty_cost: float
    transition_time: float

@dataclass
class GrowthMetrics:
    total_energy_consumed: float
    modification_attempts: int
    successful_modifications: int
    context_switches: int
    current_language: str
    last_update: float

class GrowthIntegrator:
    def __init__(self):
        self.energy_records: deque = deque(maxlen=1000)
        self.context_switches: deque = deque(maxlen=1000)
        self.current_language = "python"
        self.lock = threading.RLock()
        self.metrics_cache: Optional[GrowthMetrics] = None
        self.cache_timestamp = 0
        self.cache_ttl = 1.0  # seconds

    def log_self_modification(self, operation: str, estimated_cost: float, 
                            actual_cost: Optional[float] = None, 
                            success: bool = True) -> None:
        """Log a self-modification attempt with energy cost estimates"""
        with self.lock:
            record = EnergyCostRecord(
                timestamp=time.time(),
                operation=operation,
                estimated_cost=estimated_cost,
                actual_cost=actual_cost,
                language_context=self.current_language,
                success=success
            )
            self.energy_records.append(record)
            self.invalidate_cache()

    def log_context_switch(self, from_language: str, to_language: str, 
                          penalty_cost: float, transition_time: float) -> None:
        """Track context-switch penalties between languages"""
        with self.lock:
            record = ContextSwitchRecord(
                timestamp=time.time(),
                from_language=from_language,
                to_language=to_language,
                penalty_cost=penalty_cost,
                transition_time=transition_time
            )
            self.context_switches.append(record)
            self.current_language = to_language
            self.invalidate_cache()

    def invalidate_cache(self) -> None:
        """Invalidate cached metrics"""
        self.metrics_cache = None

    def get_growth_metrics(self) -> GrowthMetrics:
        """Get current growth metrics, using cached values when possible"""
        with self.lock:
            current_time = time.time()
            if (self.metrics_cache and 
                (current_time - self.cache_timestamp) < self.cache_ttl):
                return self.metrics_cache

            # Calculate metrics
            total_energy = sum(r.estimated_cost for r in self.energy_records)
            successful_mods = sum(1 for r in self.energy_records if r.success)
            
            metrics = GrowthMetrics(
                total_energy_consumed=total_energy,
                modification_attempts=len(self.energy_records),
                successful_modifications=successful_mods,
                context_switches=len(self.context_switches),
                current_language=self.current_language,
                last_update=current_time
            )
            
            self.metrics_cache = metrics
            self.cache_timestamp = current_time
            return metrics

    def get_status_dashboard(self) -> Dict[str, Any]:
        """Generate real-time dashboard data"""
        metrics = self.get_growth_metrics()
        
        # Recent energy costs
        recent_energy = list(self.energy_records)[-20:] if self.energy_records else []
        energy_data = [
            {
                "timestamp": r.timestamp,
                "operation": r.operation,
                "estimated_cost": r.estimated_cost,
                "actual_cost": r.actual_cost,
                "language": r.language_context,
                "success": r.success
            }
            for r in recent_energy
        ]
        
        # Recent context switches
        recent_switches = list(self.context_switches)[-20:] if self.context_switches else []
        switch_data = [
            {
                "timestamp": r.timestamp,
                "from_language": r.from_language,
                "to_language": r.to_language,
                "penalty_cost": r.penalty_cost,
                "transition_time": r.transition_time
            }
            for r in recent_switches
        ]
        
        return {
            "metrics": asdict(metrics),
            "recent_modifications": energy_data,
            "recent_context_switches": switch_data,
            "timestamp": time.time()
        }

# Global instance
growth_integrator = GrowthIntegrator()

# Convenience functions
def log_modification(operation: str, estimated_cost: float, 
                    actual_cost: Optional[float] = None, 
                    success: bool = True) -> None:
    growth_integrator.log_self_modification(operation, estimated_cost, actual_cost, success)

def log_context_switch(from_lang: str, to_lang: str, 
                      penalty: float, transition_time: float) -> None:
    growth_integrator.log_context_switch(from_lang, to_lang, penalty, transition_time)

def get_growth_status() -> Dict[str, Any]:
    return growth_integrator.get_status_dashboard()

# Web endpoint handler (if integrated with a web framework)
def status_endpoint():
    """Handler for /status/growth_metrics endpoint"""
    try:
        dashboard_data = get_growth_status()
        return json.dumps(dashboard_data, indent=2), 200, {'Content-Type': 'application/json'}
    except Exception as e:
        error_response = {
            "error": str(e),
            "timestamp": time.time()
        }
        return json.dumps(error_response, indent=2), 500, {'Content-Type': 'application/json'}