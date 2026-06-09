import json
import logging
import os
import time
from datetime import datetime
from typing import Dict, Any

logger = logging.getLogger(__name__)

class AnomalyHarness:
    def __init__(self, model_api, snapshot_dir: str = "memory_snapshots"):
        self.model_api = model_api
        self.snapshot_dir = snapshot_dir
        self.threshold = 0.65
        os.makedirs(snapshot_dir, exist_ok=True)
        
    def check_anomaly(self, coherence_score: float, memory_state: Dict[str, Any]) -> bool:
        if coherence_score < self.threshold:
            self._handle_anomaly(memory_state)
            return True
        return False
        
    def _handle_anomaly(self, memory_state: Dict[str, Any]) -> None:
        timestamp = datetime.now().isoformat()
        self._capture_snapshot(memory_state, timestamp)
        self._reduce_temperature()
        self._log_event(timestamp, memory_state.get("coherence_score", 0))
        
    def _capture_snapshot(self, memory_state: Dict[str, Any], timestamp: str) -> None:
        filename = f"snapshot_{timestamp.replace(':', '-')}.json"
        filepath = os.path.join(self.snapshot_dir, filename)
        
        snapshot = {
            "timestamp": timestamp,
            "coherence_score": memory_state.get("coherence_score", 0),
            "memory_content": memory_state.get("content", {}),
            "metadata": {
                "temperature": memory_state.get("temperature", 1.0),
                "context_length": len(memory_state.get("content", {}))
            }
        }
        
        with open(filepath, 'w') as f:
            json.dump(snapshot, f, indent=2)
            
    def _reduce_temperature(self) -> None:
        try:
            self.model_api.adjust_temperature(-0.1)
        except Exception as e:
            logger.warning(f"Failed to reduce temperature: {e}")
            
    def _log_event(self, timestamp: str, coherence_score: float) -> None:
        logger.info(
            f"ANOMALY_DETECTED|"
            f"timestamp={timestamp}|"
            f"coherence_score={coherence_score}|"
            f"action_taken=snapshot_capture+temperature_reduction"
        )