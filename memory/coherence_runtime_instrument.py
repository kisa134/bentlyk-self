import json
import logging
import sys
import traceback
from typing import Any, Dict, Optional

from semantic_drift_hooks import activate_hooks, SemanticDriftHook

# Configure logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
handler = logging.StreamHandler()
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)

class CoherenceRuntimeInstrument:
    def __init__(self):
        self.hooks_active = False
        self.divergence_events = []
        
    def activate_instrumentation(self):
        """Activate semantic drift hooks for runtime instrumentation"""
        if not self.hooks_active:
            activate_hooks()
            self.hooks_active = True
            logger.info("Coherence runtime instrumentation activated")
            
    def log_semantic_divergence(self, 
                              english_context: Any, 
                              russian_context: Any, 
                              divergence_type: str,
                              confidence_score: float,
                              metadata: Optional[Dict] = None):
        """Log detailed semantic divergence events with full stack traces"""
        try:
            # Capture full stack trace
            stack_trace = traceback.format_stack()
            
            # Create structured divergence context
            divergence_context = {
                "event_type": "semantic_divergence",
                "divergence_type": divergence_type,
                "confidence_score": confidence_score,
                "timestamp": self._get_timestamp(),
                "contexts": {
                    "english": self._serialize_context(english_context),
                    "russian": self._serialize_context(russian_context)
                },
                "stack_trace": stack_trace,
                "metadata": metadata or {}
            }
            
            # Log the divergence event
            logger.warning(f"Semantic divergence detected: {json.dumps(divergence_context, indent=2)}")
            
            # Store for later analysis
            self.divergence_events.append(divergence_context)
            
        except Exception as e:
            logger.error(f"Failed to log semantic divergence: {str(e)}")
            
    def _serialize_context(self, context: Any) -> Dict:
        """Safely serialize context data for logging"""
        try:
            if isinstance(context, dict):
                return {k: str(v)[:1000] for k, v in context.items()}  # Limit size
            elif hasattr(context, '__dict__'):
                return {k: str(v)[:1000] for k, v in context.__dict__.items()}
            else:
                return {"value": str(context)[:1000]}
        except Exception:
            return {"value": "Serialization failed"}
            
    def _get_timestamp(self) -> str:
        """Get current timestamp"""
        from datetime import datetime
        return datetime.utcnow().isoformat() + "Z"
        
    def get_divergence_report(self) -> Dict:
        """Generate structured report of all divergence events"""
        return {
            "total_divergences": len(self.divergence_events),
            "events": self.divergence_events,
            "generated_at": self._get_timestamp()
        }
        
    def clear_divergence_events(self):
        """Clear stored divergence events"""
        self.divergence_events.clear()

# Global instance
instrument = CoherenceRuntimeInstrument()

# Custom hook implementation for semantic drift detection
class CoherenceSemanticDriftHook(SemanticDriftHook):
    def on_divergence_detected(self, 
                             english_data: Any, 
                             russian_data: Any, 
                             divergence_type: str,
                             confidence: float,
                             **kwargs):
        """Handle semantic divergence detection events"""
        instrument.log_semantic_divergence(
            english_context=english_data,
            russian_context=russian_data,
            divergence_type=divergence_type,
            confidence_score=confidence,
            metadata=kwargs
        )

# Register the hook
hook = CoherenceSemanticDriftHook()