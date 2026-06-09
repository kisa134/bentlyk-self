import os
import json
import time
import logging
from datetime import datetime
from typing import Dict, Any, List, Tuple
from pathlib import Path
import numpy as np
from dataclasses import dataclass, asdict

@dataclass
class AlignmentMetrics:
    timestamp: str
    operation_id: str
    energy_cost_joules: float
    latency_ms: float
    semantic_divergence_pre: float
    semantic_divergence_post: float
    language_switch_detected: bool
    source_language: str
    target_language: str
    alignment_quality_score: float
    memory_footprint_kb: float

class CoherenceRuntimeInstrument:
    def __init__(self, workdir: str):
        self.workdir = Path(workdir)
        self.metrics_dir = self.workdir / "runtime_metrics"
        self.metrics_dir.mkdir(exist_ok=True)
        
        # Setup logging
        self.logger = logging.getLogger("coherence_runtime")
        self.logger.setLevel(logging.INFO)
        if not self.logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)
        
        # Runtime state tracking
        self.energy_accumulator = 0.0
        self.operation_counter = 0
        self.latency_history: List[float] = []
        self.language_switch_history: List[Tuple[str, str, float]] = []
        self.divergence_history: List[Tuple[float, float]] = []
        
    def start_operation(self, operation_id: str) -> None:
        """Mark the start of an alignment operation"""
        self.operation_start_time = time.time()
        self.operation_id = operation_id
        self.initial_energy = self._get_system_energy()
        
    def end_operation(self, 
                     source_lang: str, 
                     target_lang: str, 
                     pre_divergence: float,
                     post_divergence: float,
                     quality_score: float,
                     memory_kb: float) -> None:
        """Mark the end of an alignment operation and record metrics"""
        if not hasattr(self, 'operation_start_time'):
            return
            
        # Calculate metrics
        elapsed_time = (time.time() - self.operation_start_time) * 1000  # ms
        final_energy = self._get_system_energy()
        energy_cost = final_energy - self.initial_energy
        
        # Detect language switch
        lang_switch = source_lang != target_lang
        if lang_switch:
            self.language_switch_history.append((source_lang, target_lang, time.time()))
        
        # Record metrics
        metrics = AlignmentMetrics(
            timestamp=datetime.utcnow().isoformat(),
            operation_id=self.operation_id,
            energy_cost_joules=energy_cost,
            latency_ms=elapsed_time,
            semantic_divergence_pre=pre_divergence,
            semantic_divergence_post=post_divergence,
            language_switch_detected=lang_switch,
            source_language=source_lang,
            target_language=target_lang,
            alignment_quality_score=quality_score,
            memory_footprint_kb=memory_kb
        )
        
        # Store for analysis
        self.latency_history.append(elapsed_time)
        self.divergence_history.append((pre_divergence, post_divergence))
        self.energy_accumulator += energy_cost
        self.operation_counter += 1
        
        # Log metrics
        self._log_metrics(metrics)
        
        # Check for correlations
        self._check_correlations(metrics)
        
    def _get_system_energy(self) -> float:
        """Simulate energy consumption reading (in Joules)"""
        # In a real implementation, this would interface with power monitoring hardware
        # For simulation, we'll use a small random energy cost per operation
        return np.random.uniform(0.01, 0.1)
        
    def _log_metrics(self, metrics: AlignmentMetrics) -> None:
        """Write metrics to structured log file"""
        log_file = self.metrics_dir / f"alignment_metrics_{datetime.utcnow().strftime('%Y%m%d')}.jsonl"
        
        with open(log_file, 'a') as f:
            f.write(json.dumps(asdict(metrics)) + '\n')
            
        self.logger.info(f"Operation {metrics.operation_id}: "
                        f"Energy={metrics.energy_cost_joules:.4f}J, "
                        f"Latency={metrics.latency_ms:.2f}ms, "
                        f"Divergence Δ={metrics.semantic_divergence_pre - metrics.semantic_divergence_post:.4f}")
        
    def _check_correlations(self, metrics: AlignmentMetrics) -> None:
        """Check for latency spikes correlated with language switches"""
        if len(self.latency_history) < 10:
            return
            
        # Calculate baseline latency
        baseline_latency = np.mean(self.latency_history[:-10]) if len(self.latency_history) > 10 else np.mean(self.latency_history)
        latency_threshold = baseline_latency * 2.0  # 2x baseline as spike threshold
        
        # Check for spike
        if metrics.latency_ms > latency_threshold and metrics.language_switch_detected:
            self.logger.warning(f"Latency spike detected: {metrics.latency_ms:.2f}ms during language switch "
                              f"({metrics.source_language} → {metrics.target_language})")
            
            # Log correlation event
            correlation_event = {
                "timestamp": metrics.timestamp,
                "event_type": "latency_language_correlation",
                "latency_ms": metrics.latency_ms,
                "baseline_latency_ms": baseline_latency,
                "languages": f"{metrics.source_language}->{metrics.target_language}",
                "correlation_strength": self._calculate_correlation_strength()
            }
            
            correlation_file = self.metrics_dir / "correlations.jsonl"
            with open(correlation_file, 'a') as f:
                f.write(json.dumps(correlation_event) + '\n')
                
    def _calculate_correlation_strength(self) -> float:
        """Calculate correlation strength between recent latency and language switches"""
        if len(self.latency_history) < 5 or len(self.language_switch_history) < 2:
            return 0.0
            
        # Simple correlation metric: ratio of spikes during switches
        recent_latencies = self.latency_history[-10:]
        baseline = np.mean(recent_latencies[:-5]) if len(recent_latencies) > 5 else np.mean(recent_latencies)
        spikes = [lat for lat in recent_latencies if lat > baseline * 2.0]
        
        if not spikes:
            return 0.0
            
        return min(len(spikes) / len(recent_latencies), 1.0)
        
    def get_summary_stats(self) -> Dict[str, Any]:
        """Get runtime summary statistics"""
        if not self.latency_history:
            return {}
            
        return {
            "total_operations": self.operation_counter,
            "total_energy_consumed": self.energy_accumulator,
            "average_energy_per_operation": self.energy_accumulator / max(self.operation_counter, 1),
            "average_latency_ms": np.mean(self.latency_history),
            "latency_std_dev": np.std(self.latency_history),
            "max_latency_ms": max(self.latency_history),
            "language_switches": len(self.language_switch_history),
            "divergence_improvement_avg": np.mean([
                pre - post for pre, post in self.divergence_history
            ]) if self.divergence_history else 0.0
        }
        
    def write_summary_report(self) -> None:
        """Write a summary report of runtime metrics"""
        summary = self.get_summary_stats()
        if not summary:
            return
            
        report_file = self.metrics_dir / "runtime_summary.json"
        summary["generated_at"] = datetime.utcnow().isoformat()
        
        with open(report_file, 'w') as f:
            json.dump(summary, f, indent=2)
            
        self.logger.info(f"Runtime summary written to {report_file}")

# Integration with real_time_coherence_bridge would follow this pattern:
# 1. Instantiate CoherenceRuntimeInstrument in the bridge constructor
# 2. Call start_operation() at the beginning of alignment operations
# 3. Call end_operation() at the end with collected metrics
# 4. Call write_summary_report() periodically or at shutdown