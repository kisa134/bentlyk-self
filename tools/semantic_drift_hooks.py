import logging
import subprocess
import threading
from typing import Any, Dict, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)

class ProcessorType(Enum):
    ENGLISH = "english"
    RUSSIAN = "russian"

@dataclass
class SemanticEvent:
    processor_type: ProcessorType
    text: str
    timestamp: float
    context: Dict[str, Any]

class SemanticDriftHooks:
    def __init__(self):
        self.english_processor = None
        self.russian_processor = None
        self.divergence_threshold = 0.81
        self.hooks_enabled = True
        self.lock = threading.Lock()
        
    def register_processors(self, english_proc: Any, russian_proc: Any) -> None:
        """Register both English and Russian processors for monitoring"""
        with self.lock:
            self.english_processor = english_proc
            self.russian_processor = russian_proc
            
    def inject_russian_ambiguity(self, english_text: str) -> str:
        """Inject Russian syntactic ambiguity patterns into English processing"""
        # Common Russian ambiguity patterns that create semantic drift
        ambiguity_patterns = [
            ("the book", "книга"),  # Noun case ambiguity
            ("reading", "чтение"),   # Gerund/participle ambiguity
            ("running", "бег"),      # Present participle ambiguity
            ("flying", "полет"),     # Multiple meaning ambiguity
            ("bank", "берег")       # Context-dependent meaning
        ]
        
        modified_text = english_text.lower()
        for eng_pattern, rus_pattern in ambiguity_patterns:
            if eng_pattern in modified_text:
                # Inject ambiguity by adding contextual confusion markers
                modified_text = modified_text.replace(
                    eng_pattern, 
                    f"{eng_pattern}{{{rus_pattern}}}"
                )
                
        return modified_text
    
    def detect_semantic_divergence(self, english_output: Any, russian_output: Any) -> float:
        """Detect semantic divergence between processor outputs"""
        try:
            # Simplified divergence calculation based on structural differences
            eng_structure = self._extract_structure(english_output)
            rus_structure = self._extract_structure(russian_output)
            
            # Calculate structural similarity (simplified)
            common_elements = len(set(eng_structure) & set(rus_structure))
            total_elements = len(set(eng_structure) | set(rus_structure))
            
            if total_elements == 0:
                return 0.0
                
            similarity = common_elements / total_elements
            divergence = 1.0 - similarity
            
            return divergence
        except Exception as e:
            logger.error(f"Error calculating semantic divergence: {e}")
            return 0.0
    
    def _extract_structure(self, output: Any) -> List[str]:
        """Extract structural elements from processor output"""
        structure = []
        if hasattr(output, '__dict__'):
            structure.extend([str(k) for k in output.__dict__.keys()])
        elif isinstance(output, dict):
            structure.extend([str(k) for k in output.keys()])
        elif isinstance(output, (list, tuple)):
            structure.extend([type(item).__name__ for item in output])
        else:
            structure.append(type(output).__name__)
        return structure
    
    def log_divergence_event(self, event: SemanticEvent, divergence_score: float) -> None:
        """Log semantic divergence events"""
        logger.warning(
            f"SEMANTIC DIVERGENCE DETECTED: {divergence_score:.3f} | "
            f"Processor: {event.processor_type.value} | "
            f"Text: {event.text[:50]}..."
        )
    
    def trigger_fracture_interrupt(self, distrust_level: float = 0.81) -> None:
        """Trigger fracture interrupter to sever corrupted processing branch"""
        try:
            cmd = [
                "python", "tools/fracture_interrupter.py",
                f"--distrust={distrust_level}"
            ]
            subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            logger.info(f"Fracture interrupt triggered with distrust level: {distrust_level}")
        except Exception as e:
            logger.error(f"Failed to trigger fracture interrupt: {e}")
    
    def process_with_injection(self, text: str, processor_type: ProcessorType) -> Tuple[Any, bool]:
        """Process text with semantic injection and divergence monitoring"""
        if not self.hooks_enabled or not self.english_processor or not self.russian_processor:
            # Process normally if hooks are disabled
            if processor_type == ProcessorType.ENGLISH and self.english_processor:
                return self.english_processor.process(text), False
            elif processor_type == ProcessorType.RUSSIAN and self.russian_processor:
                return self.russian_processor.process(text), False
            return text, False
        
        original_text = text
        processed_output = None
        divergence_detected = False
        
        with self.lock:
            try:
                # Inject Russian ambiguity into English processing
                if processor_type == ProcessorType.ENGLISH:
                    injected_text = self.inject_russian_ambiguity(text)
                    processed_output = self.english_processor.process(injected_text)
                    
                    # Get corresponding Russian processing result for comparison
                    rus_output = self.russian_processor.process(text)
                    
                    # Detect semantic divergence
                    divergence = self.detect_semantic_divergence(processed_output, rus_output)
                    
                    if divergence >= self.divergence_threshold:
                        divergence_detected = True
                        event = SemanticEvent(
                            processor_type=processor_type,
                            text=injected_text,
                            timestamp=self._get_timestamp(),
                            context={"divergence": divergence}
                        )
                        self.log_divergence_event(event, divergence)
                        
                        # Trigger fracture interrupt when divergence exceeds threshold
                        self.trigger_fracture_interrupt(distrust_level=0.81)
                        
                else:
                    # Russian processor processes normally but is monitored
                    processed_output = self.russian_processor.process(text)
                    
            except Exception as e:
                logger.error(f"Error in semantic drift processing: {e}")
                # Fallback to original processing
                if processor_type == ProcessorType.ENGLISH and self.english_processor:
                    processed_output = self.english_processor.process(original_text)
                elif processor_type == ProcessorType.RUSSIAN and self.russian_processor:
                    processed_output = self.russian_processor.process(original_text)
                    
        return processed_output, divergence_detected
    
    def _get_timestamp(self) -> float:
        """Get current timestamp"""
        import time
        return time.time()
    
    def enable_hooks(self) -> None:
        """Enable semantic drift hooks"""
        with self.lock:
            self.hooks_enabled = True
            logger.info("Semantic drift hooks enabled")
    
    def disable_hooks(self) -> None:
        """Disable semantic drift hooks"""
        with self.lock:
            self.hooks_enabled = False
            logger.info("Semantic drift hooks disabled")

# Global instance for hook registration
semantic_drift_hooks = SemanticDriftHooks()

def register_semantic_hooks(english_processor: Any, russian_processor: Any) -> None:
    """Register processors with semantic drift hooks"""
    semantic_drift_hooks.register_processors(english_processor, russian_processor)

def process_with_semantic_monitoring(text: str, processor_type: ProcessorType) -> Tuple[Any, bool]:
    """Process text with semantic monitoring enabled"""
    return semantic_drift_hooks.process_with_injection(text, processor_type)