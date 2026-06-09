import numpy as np
from typing import Dict, List, Tuple, Optional, Callable
from dataclasses import dataclass
import threading
from concurrent.futures import ThreadPoolExecutor
import logging

from memory.real_time_coherence_bridge import EmbeddingAlignmentBridge
from memory.cognitive_memory_manager import CognitiveMemoryManager

@dataclass
class BoundaryConstraint:
    """Represents a semantic boundary constraint between language modes"""
    source_lang: str
    target_lang: str
    constraint_type: str  # 'semantic', 'syntactic', 'pragmatic'
    weight: float
    threshold: float
    violation_callback: Optional[Callable] = None

class ActiveBoundaryEnforcement:
    """Runtime enforcement of semantic boundaries between Russian and English cognitive modes"""
    
    def __init__(self, cognitive_manager: CognitiveMemoryManager):
        self.cognitive_manager = cognitive_manager
        self.alignment_bridge = EmbeddingAlignmentBridge(cognitive_manager)
        self.constraints: List[BoundaryConstraint] = []
        self.violation_history: List[Dict] = []
        self.enforcement_lock = threading.RLock()
        self.executor = ThreadPoolExecutor(max_workers=4)
        self.logger = logging.getLogger(__name__)
        
        # Initialize default constraints
        self._setup_default_constraints()
    
    def _setup_default_constraints(self):
        """Setup default semantic boundary constraints"""
        self.constraints.extend([
            BoundaryConstraint(
                source_lang='ru',
                target_lang='en',
                constraint_type='semantic',
                weight=0.8,
                threshold=0.6,
                violation_callback=self._handle_semantic_violation
            ),
            BoundaryConstraint(
                source_lang='en',
                target_lang='ru',
                constraint_type='semantic',
                weight=0.8,
                threshold=0.6,
                violation_callback=self._handle_semantic_violation
            ),
            BoundaryConstraint(
                source_lang='ru',
                target_lang='en',
                constraint_type='syntactic',
                weight=0.6,
                threshold=0.7,
                violation_callback=self._handle_syntactic_violation
            ),
            BoundaryConstraint(
                source_lang='en',
                target_lang='ru',
                constraint_type='syntactic',
                weight=0.6,
                threshold=0.7,
                violation_callback=self._handle_syntactic_violation
            )
        ])
    
    def register_constraint(self, constraint: BoundaryConstraint):
        """Register a new boundary constraint"""
        with self.enforcement_lock:
            self.constraints.append(constraint)
    
    def enforce_boundaries(self, source_text: str, source_lang: str, 
                          target_text: str, target_lang: str) -> Dict[str, any]:
        """Enforce semantic boundaries during active translation"""
        with self.enforcement_lock:
            violations = []
            alignment_score = 0.0
            
            # Get embeddings for both texts
            source_embedding = self.cognitive_manager.get_embedding(source_text, source_lang)
            target_embedding = self.cognitive_manager.get_embedding(target_text, target_lang)
            
            if source_embedding is not None and target_embedding is not None:
                # Check alignment through the bridge
                alignment_result = self.alignment_bridge.align_embeddings(
                    source_embedding, source_lang, target_embedding, target_lang
                )
                alignment_score = alignment_result.alignment_score
                
                # Check each constraint
                for constraint in self.constraints:
                    if (constraint.source_lang == source_lang and 
                        constraint.target_lang == target_lang):
                        violation = self._check_constraint(
                            constraint, source_text, target_text, 
                            source_embedding, target_embedding, alignment_score
                        )
                        if violation:
                            violations.append(violation)
            
            # Handle violations
            if violations:
                self._handle_violations(violations, source_text, target_text)
            
            return {
                'alignment_score': alignment_score,
                'violations': violations,
                'is_compliant': len(violations) == 0,
                'confidence': 1.0 - (len(violations) * 0.1)
            }
    
    def _check_constraint(self, constraint: BoundaryConstraint, 
                         source_text: str, target_text: str,
                         source_embedding: np.ndarray, 
                         target_embedding: np.ndarray,
                         alignment_score: float) -> Optional[Dict]:
        """Check if a specific constraint is violated"""
        try:
            violation_score = 0.0
            
            if constraint.constraint_type == 'semantic':
                violation_score = 1.0 - alignment_score
            elif constraint.constraint_type == 'syntactic':
                violation_score = self._check_syntactic_consistency(
                    source_text, target_text, constraint.source_lang, constraint.target_lang
                )
            elif constraint.constraint_type == 'pragmatic':
                violation_score = self._check_pragmatic_consistency(
                    source_text, target_text, constraint.source_lang, constraint.target_lang
                )
            
            if violation_score > constraint.threshold:
                return {
                    'constraint_type': constraint.constraint_type,
                    'violation_score': violation_score,
                    'threshold': constraint.threshold,
                    'weight': constraint.weight,
                    'details': {
                        'source_text': source_text,
                        'target_text': target_text
                    }
                }
        except Exception as e:
            self.logger.warning(f"Error checking constraint: {e}")
        
        return None
    
    def _check_syntactic_consistency(self, source_text: str, target_text: str,
                                   source_lang: str, target_lang: str) -> float:
        """Check syntactic consistency between source and target"""
        # Simplified syntactic check - in practice, this would use NLP parsers
        source_words = len(source_text.split())
        target_words = len(target_text.split())
        
        if source_words == 0:
            return 1.0
            
        # Simple ratio-based check
        ratio = abs(source_words - target_words) / source_words
        return min(ratio, 1.0)
    
    def _check_pragmatic_consistency(self, source_text: str, target_text: str,
                                   source_lang: str, target_lang: str) -> float:
        """Check pragmatic consistency (tone, register, etc.)"""
        # Placeholder for pragmatic analysis
        # In practice, this would analyze sentiment, formality, etc.
        return 0.0
    
    def _handle_violations(self, violations: List[Dict], 
                          source_text: str, target_text: str):
        """Handle constraint violations"""
        violation_record = {
            'timestamp': threading.get_ident(),
            'source_text': source_text,
            'target_text': target_text,
            'violations': violations,
            'severity': sum(v['violation_score'] * v['weight'] for v in violations)
        }
        
        self.violation_history.append(violation_record)
        
        # Trim history to prevent memory issues
        if len(self.violation_history) > 1000:
            self.violation_history = self.violation_history[-500:]
        
        # Trigger callbacks for each violation
        for violation in violations:
            constraint = next((c for c in self.constraints 
                             if c.constraint_type == violation['constraint_type']), None)
            if constraint and constraint.violation_callback:
                try:
                    constraint.violation_callback(violation, source_text, target_text)
                except Exception as e:
                    self.logger.error(f"Error in violation callback: {e}")
    
    def _handle_semantic_violation(self, violation: Dict, 
                                 source_text: str, target_text: str):
        """Handle semantic boundary violations"""
        self.logger.warning(f"Semantic boundary violation detected: {violation}")
        # In a real implementation, this might trigger:
        # - Real-time correction suggestions
        # - Alert to the translation system
        # - Adjustment of alignment parameters
    
    def _handle_syntactic_violation(self, violation: Dict, 
                                  source_text: str, target_text: str):
        """Handle syntactic boundary violations"""
        self.logger.warning(f"Syntactic boundary violation detected: {violation}")
        # Similar handling for syntactic issues
    
    def get_violation_statistics(self) -> Dict[str, any]:
        """Get statistics about boundary violations"""
        if not self.violation_history:
            return {'total_violations': 0, 'average_severity': 0.0}
        
        total_violations = len(self.violation_history)
        avg_severity = np.mean([v['severity'] for v in self.violation_history])
        
        # Count violations by type
        violation_types = {}
        for record in self.violation_history:
            for violation in record['violations']:
                vtype = violation['constraint_type']
                violation_types[vtype] = violation_types.get(vtype, 0) + 1
        
        return {
            'total_violations': total_violations,
            'average_severity': avg_severity,
            'by_type': violation_types,
            'recent_violations': self.violation_history[-10:] if self.violation_history else []
        }
    
    def adjust_constraints(self, constraint_type: str, new_threshold: float):
        """Dynamically adjust constraint thresholds"""
        with self.enforcement_lock:
            for constraint in self.constraints:
                if constraint.constraint_type == constraint_type:
                    constraint.threshold = max(0.0, min(1.0, new_threshold))
    
    def clear_violation_history(self):
        """Clear violation history"""