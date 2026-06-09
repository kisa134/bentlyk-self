import numpy as np
from typing import Dict, List, Tuple, Optional, Any
from dataclasses import dataclass
from collections import defaultdict
import threading
import time
from scipy.spatial.distance import cosine
from scipy.stats import entropy

@dataclass
class SemanticFrame:
    language: str
    concepts: Dict[str, float]
    timestamp: float
    context_id: str

@dataclass
class CoherenceMetrics:
    alignment_score: float
    boundary_consistency: float
    semantic_drift: float
    processing_latency: float

class UnifiedSemanticLayer:
    def __init__(self, coherence_threshold: float = 0.85, boundary_tolerance: float = 0.1):
        self.coherence_threshold = coherence_threshold
        self.boundary_tolerance = boundary_tolerance
        self.russian_frames: Dict[str, SemanticFrame] = {}
        self.english_frames: Dict[str, SemanticFrame] = {}
        self.alignment_history: List[Tuple[str, float, float]] = []
        self.boundary_violations: List[Dict[str, Any]] = []
        self.lock = threading.RLock()
        self.active_cognition_hooks: List[callable] = []
        self.metrics_history: List[CoherenceMetrics] = []
        
    def register_cognition_hook(self, hook: callable):
        """Register a runtime hook for active cognition monitoring"""
        with self.lock:
            self.active_cognition_hooks.append(hook)
    
    def create_semantic_frame(self, language: str, concepts: Dict[str, float], context_id: str) -> SemanticFrame:
        """Create a semantic frame for the specified language"""
        return SemanticFrame(
            language=language,
            concepts=concepts,
            timestamp=time.time(),
            context_id=context_id
        )
    
    def store_frame(self, frame: SemanticFrame):
        """Store semantic frame in appropriate language repository"""
        with self.lock:
            if frame.language == 'russian':
                self.russian_frames[frame.context_id] = frame
            elif frame.language == 'english':
                self.english_frames[frame.context_id] = frame
    
    def compute_frame_similarity(self, frame1: SemanticFrame, frame2: SemanticFrame) -> float:
        """Compute cosine similarity between two semantic frames"""
        # Get common concepts
        common_concepts = set(frame1.concepts.keys()) & set(frame2.concepts.keys())
        if not common_concepts:
            return 0.0
        
        # Extract vectors for common concepts
        vec1 = np.array([frame1.concepts[concept] for concept in common_concepts])
        vec2 = np.array([frame2.concepts[concept] for concept in common_concepts])
        
        # Compute cosine similarity
        if np.linalg.norm(vec1) == 0 or np.linalg.norm(vec2) == 0:
            return 0.0
        
        return 1 - cosine(vec1, vec2)
    
    def compute_boundary_consistency(self, russian_frame: SemanticFrame, english_frame: SemanticFrame) -> float:
        """Compute boundary consistency between Russian and English frames"""
        # Calculate concept distribution entropy for each frame
        ru_probs = np.array(list(russian_frame.concepts.values()))
        en_probs = np.array(list(english_frame.concepts.values()))
        
        # Normalize probabilities
        ru_probs = ru_probs / np.sum(ru_probs) if np.sum(ru_probs) > 0 else ru_probs
        en_probs = en_probs / np.sum(en_probs) if np.sum(en_probs) > 0 else en_probs
        
        # Compute Jensen-Shannon divergence as consistency measure
        m_probs = 0.5 * (ru_probs + en_probs)
        js_divergence = 0.5 * (entropy(ru_probs, m_probs) + entropy(en_probs, m_probs))
        
        # Convert to consistency score (lower divergence = higher consistency)
        return np.exp(-js_divergence)
    
    def detect_semantic_drift(self, current_frame: SemanticFrame, reference_frames: List[SemanticFrame]) -> float:
        """Detect semantic drift from historical frames"""
        if not reference_frames:
            return 0.0
        
        similarities = [self.compute_frame_similarity(current_frame, ref) for ref in reference_frames]
        avg_similarity = np.mean(similarities) if similarities else 0.0
        
        # Drift is inverse of similarity (higher drift = lower similarity)
        return 1.0 - avg_similarity
    
    def enforce_semantic_boundaries(self, context_id: str) -> Optional[Dict[str, Any]]:
        """Enforce semantic boundaries for a given context"""
        with self.lock:
            ru_frame = self.russian_frames.get(context_id)
            en_frame = self.english_frames.get(context_id)
            
            if not ru_frame or not en_frame:
                return None
            
            # Compute metrics
            alignment_score = self.compute_frame_similarity(ru_frame, en_frame)
            boundary_consistency = self.compute_boundary_consistency(ru_frame, en_frame)
            semantic_drift_ru = self.detect_semantic_drift(ru_frame, 
                [f for f in list(self.russian_frames.values()) if f.context_id != context_id][-5:])
            semantic_drift_en = self.detect_semantic_drift(en_frame, 
                [f for f in list(self.english_frames.values()) if f.context_id != context_id][-5:])
            avg_drift = (semantic_drift_ru + semantic_drift_en) / 2
            
            metrics = CoherenceMetrics(
                alignment_score=alignment_score,
                boundary_consistency=boundary_consistency,
                semantic_drift=avg_drift,
                processing_latency=time.time() - max(ru_frame.timestamp, en_frame.timestamp)
            )
            
            self.metrics_history.append(metrics)
            self.alignment_history.append((context_id, alignment_score, time.time()))
            
            # Check for boundary violations
            violations = {}
            if alignment_score < self.coherence_threshold:
                violations['alignment_violation'] = {
                    'severity': 'high' if alignment_score < 0.5 else 'medium',
                    'current_score': alignment_score,
                    'threshold': self.coherence_threshold
                }
            
            if boundary_consistency < (1.0 - self.boundary_tolerance):
                violations['consistency_violation'] = {
                    'severity': 'high' if boundary_consistency < 0.7 else 'medium',
                    'current_score': boundary_consistency,
                    'threshold': 1.0 - self.boundary_tolerance
                }
            
            if avg_drift > 0.3:
                violations['drift_violation'] = {
                    'severity': 'high' if avg_drift > 0.5 else 'medium',
                    'current_drift': avg_drift
                }
            
            if violations:
                violation_record = {
                    'context_id': context_id,
                    'timestamp': time.time(),
                    'violations': violations,
                    'metrics': metrics
                }
                self.boundary_violations.append(violation_record)
                
                # Execute cognition hooks
                for hook in self.active_cognition_hooks:
                    try:
                        hook(violation_record)
                    except Exception:
                        pass  # Silently handle hook errors
                
                return violation_record
            
            return None
    
    def real_time_coherence_bridge(self, russian_concepts: Dict[str, float], 
                                 english_concepts: Dict[str, float], 
                                 context_id: str) -> Tuple[bool, Optional[Dict[str, Any]]]:
        """Real-time coherence bridging between Russian and English semantic frames"""
        start_time = time.time()
        
        # Create and store frames
        ru_frame = self.create_semantic_frame('russian', russian_concepts, context_id)
        en_frame = self.create_semantic_frame('english', english_concepts, context_id)
        
        self.store_frame(ru_frame)
        self.store_frame(en_frame)
        
        # Enforce boundaries and check coherence
        violation = self.enforce_semantic_boundaries(context_id)
        
        # Compute final alignment
        alignment_score = self.compute_frame_similarity(ru_frame, en_frame)
        is_coherent = alignment_score >= self.coherence_threshold
        
        # Update processing time in metrics
        if self.metrics_history:
            self.metrics_history[-1].processing_latency = time.time() - start_time
        
        return is_coherent, violation
    
    def get_context_alignment_history(self, context_id: str) -> List[Tuple[float, float]]:
        """Get alignment history for a specific context"""
        with self.lock:
            return [(timestamp, score) for ctx_id, score, timestamp in self.alignment_history if ctx_id == context_id]
    
    def get_recent_violations(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get recent boundary violations"""
        with self.lock:
            return self.boundary_violations[-limit:] if self.boundary_violations else []
    
    def get_average_metrics(self) -> Dict[str, float]:
        """Get average metrics across all processed contexts"""
        with self.lock:
            if not self.metrics_history:
                return {}
            
            avg_metrics = {
                'alignment_score': np.mean([m.alignment_score for m in self.metrics_history]),
                'boundary_consistency': np.mean([m.boundary_consistency for m in self.metrics_history]),
                'semantic_drift': np.mean([m.semantic_drift for m in self.metrics_history]),
                'processing_latency': np.mean([m.processing_latency for m in self.metrics_history])
            }
            
            return avg_metrics