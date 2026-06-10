import json
import traceback
import logging
from datetime import datetime
from typing import Dict, Any, Optional, Tuple
import sys
import os

class FractureInterrupter:
    def __init__(self, severity_threshold: float = 0.8, log_file: str = "fracture_events.jsonl"):
        self.severity_threshold = severity_threshold
        self.log_file = log_file
        self.validation_hooks = []
        self.logger = self._setup_logger()
        
    def _setup_logger(self) -> logging.Logger:
        logger = logging.getLogger("FractureInterrupter")
        logger.setLevel(logging.DEBUG)
        handler = logging.StreamHandler()
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        return logger
    
    def add_validation_hook(self, hook):
        """Add a validation function to be called when severity threshold is exceeded"""
        self.validation_hooks.append(hook)
    
    def calculate_semantic_divergence(self, source_context: Dict[str, Any], 
                                   target_context: Dict[str, Any]) -> float:
        """Calculate semantic divergence between source and target language processing contexts"""
        # This is a placeholder implementation - in reality this would use
        # semantic similarity models, embedding distances, etc.
        divergence = 0.0
        
        # Example divergence calculation based on context differences
        source_tokens = set(source_context.get('tokens', []))
        target_tokens = set(target_context.get('tokens', []))
        
        if source_tokens or target_tokens:
            intersection = len(source_tokens.intersection(target_tokens))
            union = len(source_tokens.union(target_tokens))
            if union > 0:
                similarity = intersection / union
                divergence = 1.0 - similarity
                
        return divergence
    
    def get_stack_context(self, frame_limit: int = 5) -> Dict[str, Any]:
        """Capture current stack trace with context snippets"""
        stack_frames = []
        for frame_info in traceback.extract_stack(limit=frame_limit):
            stack_frames.append({
                'filename': frame_info.filename,
                'lineno': frame_info.lineno,
                'function': frame_info.name,
                'code_context': frame_info.line
            })
        return {
            'timestamp': datetime.utcnow().isoformat(),
            'stack_trace': stack_frames
        }
    
    def log_fracture_event(self, lang_pair: Tuple[str, str], 
                          divergence_score: float, 
                          source_context: Dict[str, Any],
                          target_context: Dict[str, Any]):
        """Log fracture event to structured debug log"""
        event = {
            'timestamp': datetime.utcnow().isoformat(),
            'language_pair': lang_pair,
            'semantic_divergence_score': divergence_score,
            'severity_threshold': self.severity_threshold,
            'source_context': source_context,
            'target_context': target_context,
            'stack_trace': traceback.format_stack()[:-1]  # Exclude this call
        }
        
        # Write to JSONL file
        with open(self.log_file, 'a') as f:
            f.write(json.dumps(event) + '\n')
        
        self.logger.debug(f"Fracture event logged: {lang_pair} - Score: {divergence_score}")
    
    def check_fracture(self, source_lang: str, target_lang: str,
                      source_context: Dict[str, Any], 
                      target_context: Dict[str, Any]) -> bool:
        """
        Check for semantic fracture between language processing contexts.
        Returns True if fracture detected and handled.
        """
        lang_pair = (source_lang, target_lang)
        
        # Calculate divergence
        divergence_score = self.calculate_semantic_divergence(source_context, target_context)
        
        # Log the event
        self.log_fracture_event(lang_pair, divergence_score, source_context, target_context)
        
        # Check if severity threshold exceeded
        if divergence_score >= self.severity_threshold:
            self.logger.warning(f"High semantic divergence detected: {divergence_score} "
                              f"between {source_lang} and {target_lang}")
            
            # Trigger validation hooks
            for hook in self.validation_hooks:
                try:
                    hook(source_lang, target_lang, divergence_score, 
                         source_context, target_context)
                except Exception as e:
                    self.logger.error(f"Validation hook failed: {e}")
            
            return True
        
        return False

# Global instance
interrupter = FractureInterrupter()

def configure_interrupter(severity_threshold: float = 0.8, 
                         log_file: str = "fracture_events.jsonl"):
    """Configure the global fracture interrupter"""
    global interrupter
    interrupter = FractureInterrupter(severity_threshold, log_file)

def add_validation_hook(hook):
    """Add a validation hook to the global interrupter"""
    interrupter.add_validation_hook(hook)

def check_language_fracture(source_lang: str, target_lang: str,
                           source_context: Dict[str, Any] = None,
                           target_context: Dict[str, Any] = None) -> bool:
    """
    Check for semantic fracture between two language processing contexts.
    
    Args:
        source_lang: Source language code
        target_lang: Target language code
        source_context: Context information from source language processing
        target_context: Context information from target language processing
    
    Returns:
        True if fracture detected and handled, False otherwise
    """
    if source_context is None:
        source_context = {}
    if target_context is None:
        target_context = {}
    
    return interrupter.check_fracture(source_lang, target_lang, 
                                    source_context, target_context)

# Example validation hook
def example_validation_hook(source_lang: str, target_lang: str, 
                           divergence_score: float,
                           source_context: Dict[str, Any],
                           target_context: Dict[str, Any]):
    """Example validation hook that logs severe fractures"""
    print(f"VALIDATION TRIGGERED: High divergence ({divergence_score}) "
          f"from {source_lang} to {target_lang}")
    print(f"Source context: {source_context}")
    print(f"Target context: {target_context}")

# Register the example hook
add_validation_hook(example_validation_hook)

if __name__ == "__main__":
    # Example usage
    configure_interrupter(severity_threshold=0.5)
    
    # Simulate some language processing contexts
    source_ctx = {
        'tokens': ['hello', 'world', 'python'],
        'syntax_tree': {'type': 'greeting', 'children': ['hello', 'world']},
        'semantic_features': {'sentiment': 0.8, 'formality': 0.3}
    }
    
    target_ctx = {
        'tokens': ['bonjour', 'monde', 'programmation'],
        'syntax_tree': {'type': 'salutation', 'children': ['bonjour', 'monde']},
        'semantic_features': {'sentiment': 0.7, 'formality': 0.4}
    }
    
    # Check for fracture
    fracture_detected = check_language_fracture('en', 'fr', source_ctx, target_ctx)
    print(f"Fracture detected: {fracture_detected}")