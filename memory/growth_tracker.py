import difflib
import json
from typing import Dict, List, Tuple, Any
from pathlib import Path
import hashlib


class GrowthTracker:
    """Tracks cognitive and codebase growth by analyzing behavioral log changes."""
    
    def __init__(self, log_directory: str = "logs"):
        self.log_directory = Path(log_directory)
        self.categories = {
            'memory': ['recall', 'remember', 'memory', 'storage', 'context'],
            'logic': ['logic', 'reasoning', 'decision', 'condition', 'algorithm'],
            'optimization': ['optimize', 'efficiency', 'performance', 'speed', 'reduce'],
            'new_features': ['new', 'feature', 'capability', 'function', 'method']
        }
    
    def load_logs(self, current_file: str, previous_file: str) -> Tuple[Dict, Dict]:
        """Load current and previous behavioral logs."""
        try:
            with open(current_file, 'r') as f:
                current_log = json.load(f)
        except FileNotFoundError:
            current_log = {}
            
        try:
            with open(previous_file, 'r') as f:
                previous_log = json.load(f)
        except FileNotFoundError:
            previous_log = {}
            
        return current_log, previous_log
    
    def generate_diff(self, current: Dict, previous: Dict) -> List[str]:
        """Generate diff between current and previous logs."""
        current_str = json.dumps(current, indent=2, sort_keys=True)
        previous_str = json.dumps(previous, indent=2, sort_keys=True)
        
        diff = list(difflib.unified_diff(
            previous_str.splitlines(keepends=True),
            current_str.splitlines(keepends=True),
            fromfile='previous',
            tofile='current'
        ))
        
        return diff
    
    def categorize_changes(self, diff_lines: List[str]) -> Dict[str, List[str]]:
        """Categorize changes based on keywords."""
        categorized = {category: [] for category in self.categories}
        
        for line in diff_lines:
            if line.startswith('+') or line.startswith('-'):
                for category, keywords in self.categories.items():
                    for keyword in keywords:
                        if keyword in line.lower():
                            categorized[category].append(line.strip())
                            break
        
        return categorized
    
    def calculate_growth_metrics(self, current: Dict, previous: Dict) -> Dict[str, float]:
        """Calculate quantitative growth metrics."""
        metrics = {}
        
        # Size comparison
        current_size = len(json.dumps(current))
        previous_size = len(json.dumps(previous))
        metrics['size_growth'] = ((current_size - previous_size) / previous_size * 100) if previous_size > 0 else 0
        
        # Complexity comparison (simplified)
        current_keys = len(self._flatten_dict(current))
        previous_keys = len(self._flatten_dict(previous))
        metrics['complexity_growth'] = ((current_keys - previous_keys) / previous_keys * 100) if previous_keys > 0 else 0
        
        return metrics
    
    def _flatten_dict(self, d: Dict, parent_key: str = '', sep: str = '.') -> Dict[str, Any]:
        """Flatten nested dictionary for analysis."""
        items = []
        for k, v in d.items():
            new_key = f"{parent_key}{sep}{k}" if parent_key else k
            if isinstance(v, dict):
                items.extend(self._flatten_dict(v, new_key, sep=sep).items())
            else:
                items.append((new_key, v))
        return dict(items)
    
    def generate_summary_report(self, current_file: str, previous_file: str) -> Dict[str, Any]:
        """Generate comprehensive growth summary report."""
        current_log, previous_log = self.load_logs(current_file, previous_file)
        diff_lines = self.generate_diff(current_log, previous_log)
        categorized_changes = self.categorize_changes(diff_lines)
        growth_metrics = self.calculate_growth_metrics(current_log, previous_log)
        
        # Identify significant shifts
        significant_shifts = []
        for category, changes in categorized_changes.items():
            if len(changes) > 3:  # Threshold for significance
                significant_shifts.append({
                    'category': category,
                    'change_count': len(changes),
                    'sample_changes': changes[:3]
                })
        
        report = {
            'timestamp': str(Path(current_file).stem),
            'growth_metrics': growth_metrics,
            'categorized_changes': categorized_changes,
            'significant_shifts': significant_shifts,
            'total_changes': sum(len(changes) for changes in categorized_changes.values())
        }
        
        return report
    
    def save_report(self, report: Dict[str, Any], output_file: str = None):
        """Save report to file."""
        if not output_file:
            output_file = self.log_directory / f"growth_report_{report['timestamp']}.json"
        
        self.log_directory.mkdir(exist_ok=True)
        with open(output_file, 'w') as f:
            json.dump(report, f, indent=2)
    
    def get_cognitive_shift_insights(self, report: Dict[str, Any]) -> List[str]:
        """Extract insights about cognitive shifts from the report."""
        insights = []
        
        # Memory improvements
        if report['growth_metrics'].get('complexity_growth', 0) > 10:
            insights.append("Significant increase in cognitive complexity, suggesting deeper understanding.")
        
        # Logic enhancements
        logic_changes = len(report['categorized_changes'].get('logic', []))
        if logic_changes > 5:
            insights.append(f"Substantial logic refinements detected ({logic_changes} changes).")
        
        # Optimization focus
        opt_changes = len(report['categorized_changes'].get('optimization', []))
        if opt_changes > 3:
            insights.append(f"Evidence of optimization focus with {opt_changes} related modifications.")
        
        # New capabilities
        new_features = len(report['categorized_changes'].get('new_features', []))
        if new_features > 0:
            insights.append(f"Expansion of capabilities with {new_features} new features identified.")
        
        return insights


# Example usage
if __name__ == "__main__":
    tracker = GrowthTracker()
    report = tracker.generate_summary_report(
        "logs/current_behavioral_log.json",
        "logs/previous_behavioral_log.json"
    )
    tracker.save_report(report)
    insights = tracker.get_cognitive_shift_insights(report)
    for insight in insights:
        print(insight)