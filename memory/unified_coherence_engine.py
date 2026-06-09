import numpy as np
from typing import Dict, List, Tuple, Any, Optional, Callable
from dataclasses import dataclass
import threading
import time
from collections import deque
import logging

from memory.multilingual_coherence import MultilingualCoherenceDetector
from memory.coherence_bridge import SemanticAlignmentBridge

@dataclass
class CoherenceFrame:
    frame_id: str
    timestamp: float
    language: str
    embeddings: Dict[str, np.ndarray]
    coherence_score: float
    alignment_status: str

class UnifiedCoherenceEngine:
    def __init__(self, 
                 coherence_threshold: float = 0.75,
                 alignment_tolerance: float = 0.1,
                 max_frame_history: int = 100):
        self.coherence_threshold = coherence_threshold
        self.alignment_tolerance = alignment_tolerance
        self.max_frame_history = max_frame_history
        
        # Core components
        self.coherence_detector = MultilingualCoherenceDetector()
        self.alignment_bridge = SemanticAlignmentBridge()
        
        # Runtime state
        self.frame_buffer = deque(maxlen=max_frame_history)
        self.active_frames = {}
        self.fragmentation_hooks = []
        self.sync_validators = []
        
        # Threading
        self.lock = threading.RLock()
        self.running = False
        self.monitor_thread = None
        
        # Logging
        self.logger = logging.getLogger(__name__)
        
    def register_fragmentation_hook(self, hook: Callable[[CoherenceFrame], None]):
        """Register a hook to be called when fragmentation is detected"""
        self.fragmentation_hooks.append(hook)
        
    def register_sync_validator(self, validator: Callable[[Dict[str, np.ndarray]], bool]):
        """Register a validator for bidirectional sync between embeddings"""
        self.sync_validators.append(validator)
        
    def start_monitoring(self):
        """Start the background monitoring thread"""
        with self.lock:
            if not self.running:
                self.running = True
                self.monitor_thread = threading.Thread(target=self._monitor_loop, daemon=True)
                self.monitor_thread.start()
                self.logger.info("Unified coherence engine monitoring started")
                
    def stop_monitoring(self):
        """Stop the background monitoring thread"""
        with self.lock:
            self.running = False
            if self.monitor_thread:
                self.monitor_thread.join()
                self.logger.info("Unified coherence engine monitoring stopped")
                
    def _monitor_loop(self):
        """Background thread for continuous coherence monitoring"""
        while self.running:
            try:
                self._check_active_frames()
                self._validate_bidirectional_sync()
                time.sleep(0.1)  # 100ms check interval
            except Exception as e:
                self.logger.error(f"Error in coherence monitoring: {e}")
                
    def process_cognitive_input(self, 
                              content: str, 
                              language: str,
                              context: Optional[Dict[str, Any]] = None) -> CoherenceFrame:
        """Process cognitive input and create/update coherence frames"""
        with self.lock:
            # Detect coherence and language tracing
            coherence_result = self.coherence_detector.detect_coherence(content, language)
            
            # Create frame
            frame = CoherenceFrame(
                frame_id=self._generate_frame_id(),
                timestamp=time.time(),
                language=language,
                embeddings=coherence_result.embeddings,
                coherence_score=coherence_result.coherence_score,
                alignment_status="pending"
            )
            
            # Check for fragmentation
            if not self._is_coherent(frame):
                self._handle_fragmentation(frame)
                
            # Store frame
            self.frame_buffer.append(frame)
            self.active_frames[frame.frame_id] = frame
            
            # Trigger alignment
            self._align_frame(frame, context)
            
            return frame
            
    def _is_coherent(self, frame: CoherenceFrame) -> bool:
        """Check if a frame meets coherence thresholds"""
        return frame.coherence_score >= self.coherence_threshold
        
    def _handle_fragmentation(self, frame: CoherenceFrame):
        """Handle detected fragmentation in cognitive frames"""
        frame.alignment_status = "fragmented"
        
        # Call registered hooks
        for hook in self.fragmentation_hooks:
            try:
                hook(frame)
            except Exception as e:
                self.logger.error(f"Error in fragmentation hook: {e}")
                
        self.logger.warning(f"Fragmentation detected in frame {frame.frame_id}")
        
    def _align_frame(self, frame: CoherenceFrame, context: Optional[Dict[str, Any]] = None):
        """Align frame embeddings in real-time"""
        try:
            # Perform semantic alignment
            aligned_embeddings = self.alignment_bridge.align_embeddings(
                frame.embeddings, 
                frame.language,
                context
            )
            
            # Update frame with aligned embeddings
            frame.embeddings = aligned_embeddings
            frame.alignment_status = "aligned"
            
        except Exception as e:
            self.logger.error(f"Error aligning frame {frame.frame_id}: {e}")
            frame.alignment_status = "alignment_failed"
            
    def _check_active_frames(self):
        """Check active frames for coherence and alignment issues"""
        with self.lock:
            current_time = time.time()
            expired_frames = []
            
            for frame_id, frame in self.active_frames.items():
                # Check for expired frames (older than 5 seconds)
                if current_time - frame.timestamp > 5.0:
                    expired_frames.append(frame_id)
                    continue
                    
                # Re-check coherence for borderline cases
                if (self.coherence_threshold - 0.1) <= frame.coherence_score < self.coherence_threshold:
                    if not self._is_coherent(frame):
                        self._handle_fragmentation(frame)
                        
            # Clean up expired frames
            for frame_id in expired_frames:
                del self.active_frames[frame_id]
                
    def _validate_bidirectional_sync(self):
        """Validate bidirectional synchronization between Russian/English embeddings"""
        with self.lock:
            if len(self.frame_buffer) < 2:
                return
                
            # Get recent frames
            recent_frames = list(self.frame_buffer)[-10:]  # Last 10 frames
            
            for frame in recent_frames:
                # Skip if not aligned or missing required languages
                if frame.alignment_status != "aligned":
                    continue
                    
                # Validate Russian-English bidirectional sync
                if "ru" in frame.embeddings and "en" in frame.embeddings:
                    ru_embedding = frame.embeddings["ru"]
                    en_embedding = frame.embeddings["en"]
                    
                    # Calculate bidirectional alignment error
                    forward_alignment = self.alignment_bridge.calculate_alignment_error(
                        ru_embedding, en_embedding, "ru", "en"
                    )
                    backward_alignment = self.alignment_bridge.calculate_alignment_error(
                        en_embedding, ru_embedding, "en", "ru"
                    )
                    
                    # Check against tolerance
                    if (forward_alignment > self.alignment_tolerance or 
                        backward_alignment > self.alignment_tolerance):
                        self.logger.warning(
                            f"Bidirectional sync validation failed for frame {frame.frame_id}: "
                            f"forward={forward_alignment:.4f}, backward={backward_alignment:.4f}"
                        )
                        
                        # Call registered validators
                        validation_context = {
                            "ru_embedding": ru_embedding,
                            "en_embedding": en_embedding,
                            "forward_error": forward_alignment,
                            "backward_error": backward_alignment,
                            "frame_id": frame.frame_id
                        }
                        
                        for validator in self.sync_validators:
                            try:
                                if not validator(validation_context):
                                    self.logger.error(
                                        f"Sync validator failed for frame {frame.frame_id}"
                                    )
                            except Exception as e:
                                self.logger.error(f"Error in sync validator: {e}")
                                
    def get_coherence_report(self) -> Dict[str, Any]:
        """Generate a comprehensive coherence report"""
        with self.lock:
            total_frames = len(self.frame_buffer)
            if total_frames == 0:
                return {"status": "no_data"}
                
            coherent_frames = sum(1 for frame in self.frame_buffer if self._is_coherent(frame))
            fragmented_frames = total_frames - coherent_frames
            
            avg_coherence = np.mean([frame.coherence_score for frame in self.frame_buffer])
            
            alignment_stats = {
                "aligned": sum(1 for frame in self.frame_buffer if frame.alignment_status == "aligned"),
                "fragmented": sum(1 for frame in self.frame_buffer if frame.alignment_status == "fragmented"),
                "pending": sum(1 for frame in self.frame_buffer if frame.alignment_status == "pending"),
                "failed": sum(1 for frame in self.frame_buffer if frame.alignment_status == "alignment_failed")
            }
            
            return {
                "total_frames": total_frames,
                "coherent_frames": coherent_frames,
                "fragmented_frames": fragmented_frames,
                "coherence_rate": coherent_frames / total_frames if total_frames > 0 else 0,
                "average_coherence": float(avg_coherence),
                "alignment_stats": alignment_stats,
                "active_frames": len(self.active_frames)
            }
            
    def resolve_fragmentation(self, frame_id: str) -> bool:
        """Attempt to resolve fragmentation for a specific frame"""
        with self.lock:
            if frame_id not in self.active_frames:
                return False
                
            frame = self.active_frames[frame_id]
            
            # Re-attempt alignment
            try:
                aligned_embeddings = self.alignment_bridge.align_embeddings(
                    frame.embeddings, 
                    frame.language
                )
                
                frame.embeddings = aligned_embeddings
                frame.alignment_status = "aligned"
                
                # Re-check coherence
                if self._is_coherent(frame):
                    self.logger.info(f"Successfully resolved fragmentation for frame {frame