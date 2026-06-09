import time
import json
from typing import Dict, List, Tuple, Optional
from datetime import datetime, timedelta
import logging

from core.tracer import Tracer
from dashboard.metrics import MetricsCollector

class GrowthFeedbackLoop:
    def __init__(self, tracer: Tracer, metrics_collector: MetricsCollector):
        self.tracer = tracer
        self.metrics_collector = metrics_collector
        self.analysis_history: List[Dict] = []
        self.last_modification_time: Optional[float] = None
        self.cooldown_period = 24 * 60 * 60  # 24 hours in seconds
        self.logger = logging.getLogger(__name__)
        
    def analyze_recent_changes(self) -> Dict:
        """Analyze energy costs, stability, and capability gains from last 5 code changes"""
        recent_changes = self.tracer.get_recent_changes(limit=5)
        analysis_results = {
            'timestamp': time.time(),
            'changes_analyzed': len(recent_changes),
            'energy_costs': self._calculate_energy_costs(recent_changes),
            'stability_metrics': self._evaluate_stability(recent_changes),
            'capability_gains': self._measure_capability_gains(recent_changes),
            'recommendations': []
        }
        
        analysis_results['recommendations'] = self._generate_recommendations(analysis_results)
        self.analysis_history.append(analysis_results)
        
        # Keep only last 10 analyses
        if len(self.analysis_history) > 10:
            self.analysis_history = self.analysis_history[-10:]
            
        self.metrics_collector.record_growth_analysis(analysis_results)
        return analysis_results
        
    def _calculate_energy_costs(self, changes: List[Dict]) -> Dict:
        """Calculate computational energy costs of recent changes"""
        total_energy = 0
        cost_breakdown = []
        
        for change in changes:
            # Simulate energy calculation based on change complexity
            complexity = change.get('complexity', 1)
            execution_time = change.get('execution_time', 0)
            energy_cost = complexity * execution_time * 0.5  # Simplified model
            
            cost_breakdown.append({
                'change_id': change.get('id'),
                'energy_cost': energy_cost,
                'complexity': complexity,
                'execution_time': execution_time
            })
            
            total_energy += energy_cost
            
        return {
            'total_energy': total_energy,
            'average_energy_per_change': total_energy / len(changes) if changes else 0,
            'cost_breakdown': cost_breakdown
        }
        
    def _evaluate_stability(self, changes: List[Dict]) -> Dict:
        """Evaluate system stability metrics after changes"""
        stability_score = 100
        issues = []
        recovery_time = 0
        
        for change in changes:
            if change.get('error_rate', 0) > 0.05:  # More than 5% error rate
                stability_score -= 10
                issues.append(f"High error rate in change {change.get('id')}")
                
            if change.get('recovery_time', 0) > 300:  # More than 5 minutes recovery
                stability_score -= 15
                recovery_time += change['recovery_time']
                
        return {
            'stability_score': max(0, stability_score),
            'issues_found': issues,
            'total_recovery_time': recovery_time,
            'average_recovery_time': recovery_time / len(changes) if changes else 0
        }
        
    def _measure_capability_gains(self, changes: List[Dict]) -> Dict:
        """Measure improvements in system capabilities"""
        total_gain = 0
        capability_breakdown = []
        
        for change in changes:
            # Simulate capability gain calculation
            performance_improvement = change.get('performance_gain', 0)
            new_features = change.get('new_features', 0)
            capability_gain = performance_improvement * 10 + new_features * 5
            
            capability_breakdown.append({
                'change_id': change.get('id'),
                'capability_gain': capability_gain,
                'performance_improvement': performance_improvement,
                'new_features': new_features
            })
            
            total_gain += capability_gain
            
        return {
            'total_capability_gain': total_gain,
            'average_gain_per_change': total_gain / len(changes) if changes else 0,
            'capability_breakdown': capability_breakdown
        }
        
    def _generate_recommendations(self, analysis: Dict) -> List[str]:
        """Generate recommendations based on analysis results"""
        recommendations = []
        
        energy_costs = analysis['energy_costs']
        stability = analysis['stability_metrics']
        capabilities = analysis['capability_gains']
        
        if energy_costs['average_energy_per_change'] > 50:
            recommendations.append("Consider optimizing high-energy changes")
            
        if stability['stability_score'] < 70:
            recommendations.append("Prioritize stability improvements over new features")
            
        if capabilities['average_gain_per_change'] < 5:
            recommendations.append("Focus on high-impact capability enhancements")
            
        if not recommendations:
            recommendations.append("Current growth trajectory is healthy")
            
        return recommendations
        
    def can_modify_system(self) -> Tuple[bool, str]:
        """Check if system can be modified (respects 24h cooldown)"""
        if self.last_modification_time is None:
            return True, "System has not been modified yet"
            
        time_since_last = time.time() - self.last_modification_time
        if time_since_last >= self.cooldown_period:
            return True, "Cooldown period has elapsed"
        else:
            remaining = self.cooldown_period - time_since_last
            hours = int(remaining // 3600)
            minutes = int((remaining % 3600) // 60)
            return False, f"Cooldown active. {hours}h {minutes}m remaining"
            
    def record_modification(self):
        """Record that a system modification has been made"""
        self.last_modification_time = time.time()
        self.logger.info(f"System modification recorded at {datetime.fromtimestamp(self.last_modification_time)}")
        
    def get_cooldown_status(self) -> Dict:
        """Get current cooldown status"""
        can_modify, message = self.can_modify_system()
        
        return {
            'can_modify': can_modify,
            'status_message': message,
            'last_modification': datetime.fromtimestamp(self.last_modification_time) if self.last_modification_time else None,
            'next_modification_allowed': datetime.fromtimestamp(self.last_modification_time + self.cooldown_period) if self.last_modification_time else None
        }
        
    def get_analysis_history(self) -> List[Dict]:
        """Get history of growth analyses"""
        return self.analysis_history.copy()
        
    def export_analysis_report(self, filepath: str):
        """Export analysis report to JSON file"""
        report = {
            'analysis_history': self.analysis_history,
            'cooldown_status': self.get_cooldown_status(),
            'export_timestamp': time.time()
        }
        
        with open(filepath, 'w') as f:
            json.dump(report, f, indent=2, default=str)
            
    def integrate_with_dashboard(self):
        """Push current metrics to dashboard"""
        if self.analysis_history:
            latest_analysis = self.analysis_history[-1]
            self.metrics_collector.update_growth_metrics(latest_analysis)