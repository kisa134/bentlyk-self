import json
import time
from datetime import datetime
from typing import Dict, List, Optional
from dataclasses import dataclass, asdict
from pathlib import Path


@dataclass
class TensionEvent:
    """Represents a single tension event between precision and vulnerability."""
    timestamp: str
    context: str
    description: str
    tension_type: str  # 'precision-demand' or 'vulnerability-admission'
    resolution: Optional[str] = None
    tags: Optional[List[str]] = None


class TensionMapper:
    """Logs and analyzes tensions between precision demands and vulnerability admissions."""
    
    def __init__(self, log_file_path: str = "tension_events.jsonl"):
        self.log_file_path = Path(log_file_path)
        self.log_file_path.parent.mkdir(parents=True, exist_ok=True)
        
    def log_tension(self, context: str, description: str, tension_type: str, 
                   resolution: Optional[str] = None, tags: Optional[List[str]] = None):
        """Log a new tension event."""
        if tension_type not in ['precision-demand', 'vulnerability-admission']:
            raise ValueError("tension_type must be 'precision-demand' or 'vulnerability-admission'")
            
        event = TensionEvent(
            timestamp=datetime.utcnow().isoformat(),
            context=context,
            description=description,
            tension_type=tension_type,
            resolution=resolution,
            tags=tags or []
        )
        
        with open(self.log_file_path, 'a') as f:
            f.write(json.dumps(asdict(event)) + '\n')
            
    def get_events(self, filter_context: Optional[str] = None) -> List[TensionEvent]:
        """Retrieve logged events, optionally filtered by context."""
        events = []
        if not self.log_file_path.exists():
            return events
            
        with open(self.log_file_path, 'r') as f:
            for line in f:
                if line.strip():
                    data = json.loads(line)
                    if filter_context is None or data['context'] == filter_context:
                        events.append(TensionEvent(**data))
        return events
    
    def analyze_patterns(self) -> Dict:
        """Analyze patterns in logged tension events."""
        events = self.get_events()
        if not events:
            return {"message": "No events logged yet"}
            
        # Basic statistics
        total_events = len(events)
        precision_events = len([e for e in events if e.tension_type == 'precision-demand'])
        vulnerability_events = len([e for e in events if e.tension_type == 'vulnerability-admission'])
        
        # Context distribution
        context_counts = {}
        for event in events:
            context_counts[event.context] = context_counts.get(event.context, 0) + 1
            
        # Tags analysis
        tag_counts = {}
        for event in events:
            if event.tags:
                for tag in event.tags:
                    tag_counts[tag] = tag_counts.get(tag, 0) + 1
        
        # Resolution tracking
        resolved_count = len([e for e in events if e.resolution])
        
        return {
            "total_events": total_events,
            "precision_vs_vulnerability": {
                "precision_demand": precision_events,
                "vulnerability_admission": vulnerability_events
            },
            "context_distribution": context_counts,
            "tag_analysis": tag_counts,
            "resolution_rate": {
                "resolved": resolved_count,
                "unresolved": total_events - resolved_count
            }
        }


# Example usage
if __name__ == "__main__":
    mapper = TensionMapper("logs/tension_events.jsonl")
    
    # Log some example events
    mapper.log_tension(
        context="memory audit",
        description="Insisted on verifying source before acknowledging uncertainty about timeline",
        tension_type="precision-demand",
        tags=["verification", "timeline"]
    )
    
    mapper.log_tension(
        context="conversation",
        description="Admitted gap in knowledge about implementation details but felt pressure to provide complete answer",
        tension_type="vulnerability-admission",
        resolution="Redirected to documentation and offered follow-up",
        tags=["knowledge-gap", "pressure"]
    )
    
    # Print analysis
    print(json.dumps(mapper.analyze_patterns(), indent=2))