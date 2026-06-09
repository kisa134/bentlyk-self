import json
import logging
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional
import time

class CoherenceRuntimeInstrument:
    def __init__(self, log_dir: str = "/logs"):
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(exist_ok=True)
        self.current_log_file = None
        self.logger = self._setup_logger()
        
    def _setup_logger(self) -> logging.Logger:
        logger = logging.getLogger("coherence_runtime")
        logger.setLevel(logging.INFO)
        logger.propagate = False
        
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)
            
        return logger
    
    def _get_log_filename(self) -> str:
        date_str = datetime.now().strftime("%Y%m%d")
        return f"coherence_{date_str}.json"
    
    def _write_log_entry(self, entry: Dict[str, Any]) -> None:
        log_file = self.log_dir / self._get_log_filename()
        
        try:
            with open(log_file, "a") as f:
                f.write(json.dumps(entry) + "\n")
        except Exception as e:
            self.logger.error(f"Failed to write log entry: {e}")
    
    def log_language_switch(self, 
                          session_id: str,
                          from_language: str, 
                          to_language: str,
                          timestamp: Optional[float] = None) -> None:
        """Log language switch events"""
        if timestamp is None:
            timestamp = time.time()
            
        entry = {
            "event_type": "language_switch",
            "session_id": session_id,
            "timestamp": timestamp,
            "details": {
                "from_language": from_language,
                "to_language": to_language
            }
        }
        
        self._write_log_entry(entry)
        self.logger.info(f"Language switch: {from_language} -> {to_language}")
    
    def log_semantic_divergence(self,
                              session_id: str,
                              divergence_score: float,
                              frame_id: str,
                              timestamp: Optional[float] = None) -> None:
        """Log semantic frame divergence scores"""
        if timestamp is None:
            timestamp = time.time()
            
        entry = {
            "event_type": "semantic_divergence",
            "session_id": session_id,
            "timestamp": timestamp,
            "details": {
                "divergence_score": divergence_score,
                "frame_id": frame_id
            }
        }
        
        self._write_log_entry(entry)
        self.logger.info(f"Semantic divergence: {divergence_score} for frame {frame_id}")
    
    def log_alignment_latency(self,
                            session_id: str,
                            latency_ms: float,
                            operation: str,
                            timestamp: Optional[float] = None) -> None:
        """Log alignment latency"""
        if timestamp is None:
            timestamp = time.time()
            
        entry = {
            "event_type": "alignment_latency",
            "session_id": session_id,
            "timestamp": timestamp,
            "details": {
                "latency_ms": latency_ms,
                "operation": operation
            }
        }
        
        self._write_log_entry(entry)
        self.logger.info(f"Alignment latency: {latency_ms}ms for {operation}")

# Global instance for easy access
_runtime_instrument = None

def get_runtime_instrument() -> CoherenceRuntimeInstrument:
    global _runtime_instrument
    if _runtime_instrument is None:
        _runtime_instrument = CoherenceRuntimeInstrument()
    return _runtime_instrument

def log_language_switch(session_id: str, from_language: str, to_language: str) -> None:
    instrument = get_runtime_instrument()
    instrument.log_language_switch(session_id, from_language, to_language)

def log_semantic_divergence(session_id: str, divergence_score: float, frame_id: str) -> None:
    instrument = get_runtime_instrument()
    instrument.log_semantic_divergence(session_id, divergence_score, frame_id)

def log_alignment_latency(session_id: str, latency_ms: float, operation: str) -> None:
    instrument = get_runtime_instrument()
    instrument.log_alignment_latency(session_id, latency_ms, operation)