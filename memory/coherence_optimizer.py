import time
import threading
from typing import Dict, List, Tuple, Optional
from collections import deque
import numpy as np
from dataclasses import dataclass
from abc import ABC, abstractmethod

@dataclass
class MetricSnapshot:
    timestamp: float
    energy_level: float
    surprise_level: float
    coherence_score: float

@dataclass
class OptimizationProposal:
    adjustment_type: str
    magnitude: float
    expected_benefit: float
    expected_cost: float
    confidence: float

class IntrospectionInterface(ABC):
    @abstractmethod
    def get_current_metrics(self) -> MetricSnapshot:
        pass

class MockIntrospectionTool(IntrospectionInterface):
    def __init__(self):
        self.energy = 0.5
        self.surprise = 0.3
        self.coherence = 0.7
        
    def get_current_metrics(self) -> MetricSnapshot:
        # Simulate some variation in metrics
        self.energy += (np.random.random() - 0.5) * 0.1
        self.surprise += (np.random.random() - 0.5) * 0.2
        self.coherence += (np.random.random() - 0.5) * 0.15
        
        # Keep values in [0, 1] range
        self.energy = max(0, min(1, self.energy))
        self.surprise = max(0, min(1, self.surprise))
        self.coherence = max(0, min(1, self.coherence))
        
        return MetricSnapshot(
            timestamp=time.time(),
            energy_level=self.energy,
            surprise_level=self.surprise,
            coherence_score=self.coherence
        )

class CostBenefitAnalyzer:
    def __init__(self, risk_tolerance: float = 0.7):
        self.risk_tolerance = risk_tolerance
        
    def evaluate_proposal(self, proposal: OptimizationProposal) -> bool:
        # Calculate benefit-to-cost ratio adjusted by confidence
        if proposal.expected_cost <= 0:
            return True if proposal.expected_benefit > 0 else False
            
        benefit_cost_ratio = proposal.expected_benefit / proposal.expected_cost
        # Adjust decision threshold based on confidence and risk tolerance
        threshold = 1.0 - (1.0 - proposal.confidence) * (1.0 - self.risk_tolerance)
        
        return benefit_cost_ratio >= threshold

class MemoryThresholdManager:
    def __init__(self, initial_threshold: float = 0.6):
        self.retention_threshold = initial_threshold
        self.lock = threading.Lock()
        
    def get_threshold(self) -> float:
        with self.lock:
            return self.retention_threshold
            
    def adjust_threshold(self, delta: float):
        with self.lock:
            self.retention_threshold = max(0.1, min(0.9, self.retention_threshold + delta))

class CoherenceOptimizer:
    def __init__(self, introspection_tool: IntrospectionInterface, 
                 threshold_manager: MemoryThresholdManager,
                 analyzer: CostBenefitAnalyzer):
        self.introspection_tool = introspection_tool
        self.threshold_manager = threshold_manager
        self.analyzer = analyzer
        self.metric_history = deque(maxlen=100)
        self.is_running = False
        self.optimization_thread = None
        
    def start_monitoring(self, interval: float = 1.0):
        """Start the background monitoring and optimization loop"""
        if self.is_running:
            return
            
        self.is_running = True
        self.optimization_thread = threading.Thread(
            target=self._optimization_loop, 
            args=(interval,),
            daemon=True
        )
        self.optimization_thread.start()
        
    def stop_monitoring(self):
        """Stop the background monitoring"""
        self.is_running = False
        if self.optimization_thread:
            self.optimization_thread.join()
            
    def _optimization_loop(self, interval: float):
        """Main optimization loop that runs in background thread"""
        while self.is_running:
            try:
                metrics = self.introspection_tool.get_current_metrics()
                self.metric_history.append(metrics)
                
                if len(self.metric_history) >= 5:  # Need some history for trend analysis
                    proposal = self._generate_optimization_proposal()
                    if proposal and self.analyzer.evaluate_proposal(proposal):
                        self._apply_optimization(proposal)
                        
            except Exception as e:
                # In production, log this properly
                pass
                
            time.sleep(interval)
            
    def _generate_optimization_proposal(self) -> Optional[OptimizationProposal]:
        """Analyze recent metrics and generate an optimization proposal"""
        if len(self.metric_history) < 5:
            return None
            
        # Get recent metrics
        recent_metrics = list(self.metric_history)[-5:]
        
        # Calculate trends
        energy_trend = self._calculate_trend([m.energy_level for m in recent_metrics])
        surprise_trend = self._calculate_trend([m.surprise_level for m in recent_metrics])
        coherence_trend = self._calculate_trend([m.coherence_score for m in recent_metrics])
        
        # Current state
        current_energy = recent_metrics[-1].energy_level
        current_surprise = recent_metrics[-1].surprise_level
        current_coherence = recent_metrics[-1].coherence_score
        current_threshold = self.threshold_manager.get_threshold()
        
        # Determine adjustment needed
        adjustment_type = None
        magnitude = 0.0
        expected_benefit = 0.0
        expected_cost = 0.0
        confidence = 0.0
        
        # If coherence is dropping and energy is high, increase threshold to retain more
        if coherence_trend < -0.1 and current_energy > 0.6:
            adjustment_type = "increase_threshold"
            magnitude = min(0.1, abs(coherence_trend) * 0.5)
            expected_benefit = coherence_trend * -1.0  # Reverse the negative trend
            expected_cost = magnitude * 0.3  # Cost of increased memory usage
            confidence = min(1.0, abs(coherence_trend) * 10)
            
        # If surprise is very high, might need to lower threshold to forget irrelevant info
        elif current_surprise > 0.8:
            adjustment_type = "decrease_threshold"
            magnitude = min(0.05, (current_surprise - 0.8) * 0.3)
            expected_benefit = current_surprise * 0.4  # Reduce surprise impact
            expected_cost = magnitude * 0.2  # Risk of forgetting important info
            confidence = min(1.0, current_surprise)
            
        # If energy is low, optimize for efficiency
        elif current_energy < 0.3:
            adjustment_type = "decrease_threshold"
            magnitude = min(0.05, (0.3 - current_energy) * 0.4)
            expected_benefit = (0.3 - current_energy) * 0.5  # Energy savings
            expected_cost = magnitude * 0.4  # Might lose some coherence
            confidence = min(1.0, (0.3 - current_energy) * 3)
            
        if adjustment_type:
            return OptimizationProposal(
                adjustment_type=adjustment_type,
                magnitude=magnitude,
                expected_benefit=expected_benefit,
                expected_cost=expected_cost,
                confidence=confidence
            )
            
        return None
        
    def _calculate_trend(self, values: List[float]) -> float:
        """Calculate the linear trend of a series of values"""
        if len(values) < 2:
            return 0.0
            
        x = np.arange(len(values))
        slope = np.polyfit(x, values, 1)[0]
        return slope
        
    def _apply_optimization(self, proposal: OptimizationProposal):
        """Apply an approved optimization proposal"""
        if proposal.adjustment_type == "increase_threshold":
            self.threshold_manager.adjust_threshold(proposal.magnitude)
        elif proposal.adjustment_type == "decrease_threshold":
            self.threshold_manager.adjust_threshold(-proposal.magnitude)
            
    def get_status(self) -> Dict:
        """Get current optimizer status"""
        return {
            "is_running": self.is_running,
            "current_threshold": self.threshold_manager.get_threshold(),
            "metrics_history_size": len(self.metric_history),
            "latest_metrics": dict(self.metric_history[-1]) if self.metric_history else None
        }

# Convenience factory function
def create_optimizer(risk_tolerance: float = 0.7, initial_threshold: float = 0.6) -> CoherenceOptimizer:
    """Create a fully configured coherence optimizer"""
    introspection_tool = MockIntrospectionTool()
    threshold_manager = MemoryThresholdManager(initial_threshold)
    analyzer = CostBenefitAnalyzer(risk_tolerance)
    
    return CoherenceOptimizer(introspection_tool, threshold_manager, analyzer)