import numpy as np
from typing import Dict, List, Tuple, Any, Optional
from dataclasses import dataclass
from collections import defaultdict
import logging

logger = logging.getLogger(__name__)

@dataclass
class SemanticPatch:
    """Represents a patch to correct semantic drift between language representations"""
    source_tokens: List[str]
    target_tokens: List[str]
    alignment_scores: List[float]
    confidence: float
    patch_type: str  # 'substitution', 'insertion', 'deletion'

class UnifiedRuntimeValidator:
    """Validator that detects and repairs Russian-English semantic fractures in runtime"""
    
    def __init__(self, drift_threshold: float = 0.3, max_patch_attempts: int = 3):
        self.drift_threshold = drift_threshold
        self.max_patch_attempts = max_patch_attempts
        self.semantic_memory = defaultdict(list)  # Store semantic mappings
        self.patch_history = []  # Track applied patches
        self.drift_monitor = {}  # Track semantic drift over time
        
    def detect_semantic_fracture(self, ru_embedding: np.ndarray, 
                               en_embedding: np.ndarray) -> Tuple[bool, float]:
        """Detect semantic fracture between Russian and English embeddings"""
        if ru_embedding.shape != en_embedding.shape:
            return True, 1.0
            
        # Calculate cosine similarity as semantic coherence measure
        dot_product = np.dot(ru_embedding, en_embedding)
        norms = np.linalg.norm(ru_embedding) * np.linalg.norm(en_embedding)
        
        if norms == 0:
            coherence = 0.0
        else:
            coherence = dot_product / norms
            
        drift_score = 1.0 - coherence
        is_fractured = drift_score > self.drift_threshold
        
        return is_fractured, drift_score
    
    def calculate_semantic_drift(self, ru_stack: List[np.ndarray], 
                               en_stack: List[np.ndarray]) -> Dict[str, Any]:
        """Calculate semantic drift between language stacks"""
        if not ru_stack or not en_stack:
            return {"drift_score": 1.0, "fracture_points": []}
            
        drift_scores = []
        fracture_points = []
        
        # Compare each corresponding pair in stacks
        min_len = min(len(ru_stack), len(en_stack))
        for i in range(min_len):
            is_fractured, drift_score = self.detect_semantic_fracture(
                ru_stack[i], en_stack[i]
            )
            drift_scores.append(drift_score)
            if is_fractured:
                fracture_points.append(i)
                
        avg_drift = np.mean(drift_scores) if drift_scores else 1.0
        
        return {
            "drift_score": avg_drift,
            "fracture_points": fracture_points,
            "individual_scores": drift_scores
        }
    
    def generate_alignment_patches(self, ru_tokens: List[str], 
                                 en_tokens: List[str],
                                 ru_embeddings: List[np.ndarray],
                                 en_embeddings: List[np.ndarray]) -> List[SemanticPatch]:
        """Generate alignment patches to repair semantic fractures"""
        patches = []
        
        # Simple alignment strategy - could be enhanced with more sophisticated methods
        min_len = min(len(ru_tokens), len(en_tokens))
        
        for i in range(min_len):
            ru_emb = ru_embeddings[i] if i < len(ru_embeddings) else np.zeros(512)
            en_emb = en_embeddings[i] if i < len(en_embeddings) else np.zeros(512)
            
            is_fractured, drift_score = self.detect_semantic_fracture(ru_emb, en_emb)
            
            if is_fractured and drift_score > self.drift_threshold:
                # Create substitution patch
                confidence = 1.0 - drift_score
                patch = SemanticPatch(
                    source_tokens=[ru_tokens[i]] if i < len(ru_tokens) else [],
                    target_tokens=[en_tokens[i]] if i < len(en_tokens) else [],
                    alignment_scores=[drift_score],
                    confidence=confidence,
                    patch_type='substitution'
                )
                patches.append(patch)
                
        return patches
    
    def apply_patches(self, ru_stack: List[np.ndarray], 
                     en_stack: List[np.ndarray],
                     patches: List[SemanticPatch]) -> Tuple[List[np.ndarray], List[np.ndarray]]:
        """Apply generated patches to restore semantic coherence"""
        patched_ru_stack = ru_stack.copy()
        patched_en_stack = en_stack.copy()
        
        for patch in patches:
            if patch.patch_type == 'substitution' and patch.source_tokens and patch.target_tokens:
                # In a real implementation, this would involve more sophisticated embedding adjustment
                # For now, we'll simulate patch application by averaging embeddings
                for i, (ru_emb, en_emb) in enumerate(zip(patched_ru_stack, patched_en_stack)):
                    if i < len(patch.alignment_scores):
                        # Blend embeddings to reduce drift
                        weight = patch.alignment_scores[i]
                        patched_ru_stack[i] = (1 - weight) * ru_emb + weight * en_emb
                        patched_en_stack[i] = (1 - weight) * en_emb + weight * ru_emb
                        
        return patched_ru_stack, patched_en_stack
    
    def validate_and_repair(self, ru_data: Dict[str, Any], 
                          en_data: Dict[str, Any]) -> Tuple[bool, Dict[str, Any]]:
        """
        Main validation and repair method
        ru_data and en_data should contain 'tokens' and 'embeddings' keys
        """
        ru_tokens = ru_data.get('tokens', [])
        en_tokens = en_data.get('tokens', [])
        ru_embeddings = ru_data.get('embeddings', [])
        en_embeddings = en_data.get('embeddings', [])
        
        # Calculate semantic drift
        drift_info = self.calculate_semantic_drift(ru_embeddings, en_embeddings)
        
        if drift_info['drift_score'] <= self.drift_threshold:
            # No significant drift, no repair needed
            return True, {
                "status": "coherent",
                "drift_score": drift_info['drift_score'],
                "applied_patches": 0
            }
        
        # Significant drift detected, attempt repairs
        repair_attempts = 0
        current_ru_embeddings = ru_embeddings
        current_en_embeddings = en_embeddings
        
        while repair_attempts < self.max_patch_attempts:
            # Generate patches
            patches = self.generate_alignment_patches(
                ru_tokens, en_tokens, current_ru_embeddings, current_en_embeddings
            )
            
            if not patches:
                break
                
            # Apply patches
            current_ru_embeddings, current_en_embeddings = self.apply_patches(
                current_ru_embeddings, current_en_embeddings, patches
            )
            
            # Check if repair was successful
            new_drift_info = self.calculate_semantic_drift(current_ru_embeddings, current_en_embeddings)
            
            if new_drift_info['drift_score'] <= self.drift_threshold:
                # Repair successful
                self.patch_history.extend(patches)
                return True, {
                    "status": "repaired",
                    "original_drift": drift_info['drift_score'],
                    "final_drift": new_drift_info['drift_score'],
                    "applied_patches": len(patches),
                    "repair_attempts": repair_attempts + 1
                }
            
            repair_attempts += 1
            
        # Repair attempts exhausted
        return False, {
            "status": "repair_failed",
            "original_drift": drift_info['drift_score'],
            "final_drift": new_drift_info['drift_score'],
            "attempted_patches": repair_attempts * len(patches) if 'patches' in locals() else 0
        }
    
    def update_semantic_memory(self, ru_tokens: List[str], 
                             en_tokens: List[str],
                             coherence_score: float):
        """Update semantic memory with successful alignments"""
        for ru_token, en_token in zip(ru_tokens, en_tokens):
            self.semantic_memory[ru_token].append((en_token, coherence_score))
            
    def get_patch_history(self) -> List[SemanticPatch]:
        """Return history of applied patches"""
        return self.patch_history.copy()
    
    def clear_patch_history(self):
        """Clear patch history"""
        self.patch_history.clear()

# Example usage function
def validate_runtime_semantics(ru_output: Dict[str, Any], 
                             en_output: Dict[str, Any],
                             validator: Optional[UnifiedRuntimeValidator] = None) -> Dict[str, Any]:
    """Convenience function to validate and repair runtime semantics"""
    if validator is None:
        validator = UnifiedRuntimeValidator()
        
    is_valid, repair_info = validator.validate_and_repair(ru_output, en_output)
    
    return {
        "is_valid": is_valid,
        "repair_info": repair_info,
        "validator_state": {
            "drift_threshold": validator.drift_threshold,
            "patch_history_length": len(validator.get_patch_history())
        }
    }