import json
import logging
from typing import Dict, List, Any, Tuple
from datetime import datetime
from pathlib import Path
from collections import defaultdict

from memory.coherence_scorer import CoherenceScorer
from memory.anomaly_detector import AnomalyDetector
from memory.thought_logger import ThoughtLogEntry

class MemoryPerformance:
    def __init__(self, coherence_score: float, anomaly_score: float, timestamp: datetime):
        self.coherence_score = coherence_score
        self.anomaly_score = anomaly_score
        self.timestamp = timestamp

class OptimizationSuggestion:
    def __init__(self, suggestion_type: str, description: str, priority: int, evidence: List[str]):
        self.suggestion_type = suggestion_type
        self.description = description
        self.priority = priority
        self.evidence = evidence

class SelfOptimizer:
    def __init__(self, thought_logs_path: str = "data/thought_logs.jsonl"):
        self.thought_logs_path = Path(thought_logs_path)
        self.coherence_scorer = CoherenceScorer()
        self.anomaly_detector = AnomalyDetector()
        self.performance_history: List[MemoryPerformance] = []
        self.optimization_suggestions: List[OptimizationSuggestion] = []
        self.logger = logging.getLogger(__name__)
        
    def load_thought_logs(self) -> List[ThoughtLogEntry]:
        """Load thought logs from file"""
        thought_logs = []
        if self.thought_logs_path.exists():
            with open(self.thought_logs_path, 'r') as f:
                for line in f:
                    if line.strip():
                        data = json.loads(line)
                        thought_logs.append(ThoughtLogEntry(**data))
        return thought_logs
    
    def evaluate_memory_performance(self, thought_logs: List[ThoughtLogEntry]) -> List[MemoryPerformance]:
        """Evaluate memory performance on thought logs"""
        performances = []
        for log in thought_logs:
            coherence_score = self.coherence_scorer.score_coherence(log.content)
            anomaly_score = self.anomaly_detector.detect_anomalies([log.content])
            performances.append(MemoryPerformance(coherence_score, anomaly_score, log.timestamp))
        return performances
    
    def detect_discrepancies(self, actual_performances: List[MemoryPerformance]) -> List[Tuple[int, str]]:
        """Detect discrepancies between perceived and actual performance"""
        discrepancies = []
        for i, perf in enumerate(actual_performances):
            # Assuming perceived scores are stored in thought logs metadata
            perceived_coherence = getattr(perf, 'perceived_coherence', 0.5)
            perceived_anomaly = getattr(perf, 'perceived_anomaly', 0.5)
            
            coherence_diff = abs(perf.coherence_score - perceived_coherence)
            anomaly_diff = abs(perf.anomaly_score - perceived_anomaly)
            
            if coherence_diff > 0.2 or anomaly_diff > 0.2:
                discrepancy_type = "coherence" if coherence_diff > anomaly_diff else "anomaly"
                discrepancies.append((i, discrepancy_type))
        return discrepancies
    
    def generate_optimization_suggestions(self, discrepancies: List[Tuple[int, str]], 
                                        performances: List[MemoryPerformance]) -> List[OptimizationSuggestion]:
        """Generate concrete optimization suggestions based on discrepancies"""
        suggestions = []
        
        # Group discrepancies by type
        coherence_discrepancies = [i for i, t in discrepancies if t == "coherence"]
        anomaly_discrepancies = [i for i, t in discrepancies if t == "anomaly"]
        
        if len(coherence_discrepancies) > len(performances) * 0.3:
            suggestions.append(OptimizationSuggestion(
                "coherence_calibration",
                "Recalibrate coherence scoring model - perceived vs actual coherence shows consistent bias",
                1,
                [f"Discrepancy at index {i}" for i in coherence_discrepancies[:3]]
            ))
            
        if len(anomaly_discrepancies) > len(performances) * 0.3:
            suggestions.append(OptimizationSuggestion(
                "anomaly_calibration",
                "Recalibrate anomaly detection thresholds - perceived vs actual anomaly scores show consistent bias",
                1,
                [f"Discrepancy at index {i}" for i in anomaly_discrepancies[:3]]
            ))
            
        # Check for performance trends
        if len(performances) >= 10:
            recent_coherence = [p.coherence_score for p in performances[-10:]]
            avg_recent = sum(recent_coherence) / len(recent_coherence)
            if avg_recent < 0.5:
                suggestions.append(OptimizationSuggestion(
                    "memory_improvement",
                    "Overall memory coherence declining - consider memory refresh strategies",
                    2,
                    ["Recent coherence scores below 0.5 threshold"]
                ))
                
        return suggestions
    
    def run_shadow_mode_analysis(self) -> List[OptimizationSuggestion]:
        """Run complete shadow mode analysis on thought logs"""
        try:
            # Load thought logs
            thought_logs = self.load_thought_logs()
            if not thought_logs:
                self.logger.warning("No thought logs found for analysis")
                return []
            
            # Evaluate performance
            performances = self.evaluate_memory_performance(thought_logs)
            self.performance_history.extend(performances)
            
            # Detect discrepancies
            discrepancies = self.detect_discrepancies(performances)
            
            # Generate suggestions
            suggestions = self.generate_optimization_suggestions(discrepancies, performances)
            self.optimization_suggestions.extend(suggestions)
            
            self.logger.info(f"Analysis complete: {len(suggestions)} optimization suggestions generated")
            return suggestions
            
        except Exception as e:
            self.logger.error(f"Error during shadow mode analysis: {str(e)}")
            return []
    
    def get_performance_summary(self) -> Dict[str, Any]:
        """Get summary of memory performance metrics"""
        if not self.performance_history:
            return {}
            
        coherence_scores = [p.coherence_score for p in self.performance_history]
        anomaly_scores = [p.anomaly_score for p in self.performance_history]
        
        return {
            "total_evaluations": len(self.performance_history),
            "avg_coherence": sum(coherence_scores) / len(coherence_scores),
            "avg_anomaly": sum(anomaly_scores) / len(anomaly_scores),
            "coherence_trend": self._calculate_trend(coherence_scores),
            "anomaly_trend": self._calculate_trend(anomaly_scores)
        }
    
    def _calculate_trend(self, scores: List[float]) -> str:
        """Calculate trend direction for scores"""
        if len(scores) < 2:
            return "insufficient_data"
            
        recent_avg = sum(scores[-5:]) / min(5, len(scores))
        older_avg = sum(scores[:-5]) / max(1, len(scores) - 5) if len(scores) > 5 else sum(scores) / len(scores)
        
        if recent_avg > older_avg + 0.1:
            return "improving"
        elif recent_avg < older_avg - 0.1:
            return "declining"
        else:
            return "stable"

# Example usage
if __name__ == "__main__":
    # Configure logging
    logging.basicConfig(level=logging.INFO)
    
    # Initialize optimizer
    optimizer = SelfOptimizer()
    
    # Run shadow mode analysis
    suggestions = optimizer.run_shadow_mode_analysis()
    
    # Print results
    print("Optimization Suggestions:")
    for i, suggestion in enumerate(suggestions, 1):
        print(f"{i}. [{suggestion.suggestion_type}] {suggestion.description}")
        print(f"   Priority: {suggestion.priority}")
        print(f"   Evidence: {', '.join(suggestion.evidence)}")
        print()
    
    # Print performance summary
    summary = optimizer.get_performance_summary()
    print("Performance Summary:")
    for key, value in summary.items():
        print(f"  {key}: {value}")