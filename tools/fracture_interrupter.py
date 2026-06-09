import sys
import traceback
import inspect
import random
import logging
import json
import time
from typing import Any, Dict, List, Optional, Tuple
from dataclasses import dataclass, asdict
from enum import Enum

class Severity(Enum):
    LOW = 1
    MEDIUM = 2
    HIGH = 3
    CRITICAL = 4

@dataclass
class MemoryState:
    locals: Dict[str, Any]
    globals: Dict[str, Any]
    frame_info: Dict[str, Any]

@dataclass
class ValidatorReaction:
    validator_name: str
    triggered: bool
    message: str
    severity: Severity

@dataclass
class FractureLog:
    timestamp: float
    fracture_type: str
    stack_trace: List[Dict[str, Any]]
    memory_state: MemoryState
    validator_reactions: List[ValidatorReaction]
    severity: Severity
    context: Dict[str, Any]

class FractureInterrupter:
    def __init__(self, log_file: str = "fracture_log.json"):
        self.log_file = log_file
        self.logger = self._setup_logger()
        self.validators = []
        self.fracture_points = {
            "noun_gender_conflict": self._inject_noun_gender_conflict,
            "verb_aspect_conflict": self._inject_verb_aspect_conflict,
            "preposition_case_mismatch": self._inject_preposition_case_mismatch
        }
        
    def _setup_logger(self) -> logging.Logger:
        logger = logging.getLogger("FractureInterrupter")
        logger.setLevel(logging.DEBUG)
        handler = logging.FileHandler(self.log_file)
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        return logger

    def add_validator(self, validator_func):
        """Add a validator function to the chain"""
        self.validators.append(validator_func)

    def _capture_memory_state(self) -> MemoryState:
        frame = inspect.currentframe().f_back.f_back
        return MemoryState(
            locals=dict(frame.f_locals),
            globals=dict(frame.f_globals),
            frame_info={
                "filename": frame.f_code.co_filename,
                "function": frame.f_code.co_name,
                "lineno": frame.f_lineno
            }
        )

    def _capture_stack_trace(self) -> List[Dict[str, Any]]:
        stack = traceback.extract_stack()
        return [
            {
                "filename": frame.filename,
                "lineno": frame.lineno,
                "function": frame.name,
                "code": frame.line
            }
            for frame in stack[:-2]  # Exclude current and calling frames
        ]

    def _inject_noun_gender_conflict(self, text: str) -> str:
        # Simulate Russian noun gender conflict by swapping masculine/feminine references
        masculine_words = ["стол", "дом", "человек", "отец"]
        feminine_words = ["ручка", "машина", "мама", "дочь"]
        
        words = text.split()
        for i, word in enumerate(words):
            if word in masculine_words:
                words[i] = feminine_words[m masculine_words.index(word) % len(feminine_words)]
            elif word in feminine_words:
                words[i] = masculine_words[feminine_words.index(word) % len(masculine_words)]
        return " ".join(words)

    def _inject_verb_aspect_conflict(self, text: str) -> str:
        # Simulate Russian verb aspect conflict (perfective vs imperfective)
        imperfective_verbs = ["читать", "писать", "говорить", "делать"]
        perfective_verbs = ["прочитать", "написать", "сказать", "сделать"]
        
        words = text.split()
        for i, word in enumerate(words):
            if word in imperfective_verbs:
                words[i] = perfective_verbs[imperfective_verbs.index(word) % len(perfective_verbs)]
            elif word in perfective_verbs:
                words[i] = imperfective_verbs[perfective_verbs.index(word) % len(imperfective_verbs)]
        return " ".join(words)

    def _inject_preposition_case_mismatch(self, text: str) -> str:
        # Simulate preposition-case conflicts in Russian
        prepositions = ["в", "на", "под", "над"]
        case_endings = ["ый", "ой", "ий"]  # Adjective endings for different cases
        
        words = text.split()
        for i, word in enumerate(words):
            if word in prepositions and i < len(words) - 1:
                next_word = words[i+1]
                # Introduce case mismatch by changing adjective endings
                for ending in case_endings:
                    if next_word.endswith(ending):
                        new_ending = case_endings[(case_endings.index(ending) + 1) % len(case_endings)]
                        words[i+1] = next_word[:-2] + new_ending
                        break
        return " ".join(words)

    def _execute_validators(self, fractured_text: str) -> List[ValidatorReaction]:
        reactions = []
        for validator in self.validators:
            try:
                result = validator(fractured_text)
                reactions.append(ValidatorReaction(
                    validator_name=validator.__name__,
                    triggered=result.get("triggered", False),
                    message=result.get("message", ""),
                    severity=Severity(result.get("severity", 1))
                ))
            except Exception as e:
                reactions.append(ValidatorReaction(
                    validator_name=validator.__name__,
                    triggered=True,
                    message=f"Validator error: {str(e)}",
                    severity=Severity.HIGH
                ))
        return reactions

    def _calculate_severity(self, validator_reactions: List[ValidatorReaction]) -> Severity:
        if not validator_reactions:
            return Severity.LOW
        return max([r.severity for r in validator_reactions], default=Severity.LOW)

    def _log_fracture(self, fracture_type: str, original_text: str, fractured_text: str, 
                     validator_reactions: List[ValidatorReaction], context: Dict[str, Any]):
        log_entry = FractureLog(
            timestamp=time.time(),
            fracture_type=fracture_type,
            stack_trace=self._capture_stack_trace(),
            memory_state=self._capture_memory_state(),
            validator_reactions=validator_reactions,
            severity=self._calculate_severity(validator_reactions),
            context={
                "original_text": original_text,
                "fractured_text": fractured_text,
                **context
            }
        )
        
        self.logger.info(json.dumps(asdict(log_entry), default=str, indent=2))

    def fracture_text(self, text: str, fracture_type: Optional[str] = None, 
                     context: Dict[str, Any] = None) -> str:
        """
        Introduce semantic fracture in Russian-English text translation
        """
        if context is None:
            context = {}
            
        if fracture_type is None:
            fracture_type = random.choice(list(self.fracture_points.keys()))
            
        if fracture_type not in self.fracture_points:
            raise ValueError(f"Unknown fracture type: {fracture_type}")
            
        # Apply the fracture
        fractured_text = self.fracture_points[fracture_type](text)
        
        # Capture validator reactions
        validator_reactions = self._execute_validators(fractured_text)
        
        # Log the fracture event
        self._log_fracture(fracture_type, text, fractured_text, validator_reactions, context)
        
        return fractured_text

# Global instance
interrupter = FractureInterrupter()

# Convenience functions
def fracture_text(text: str, fracture_type: Optional[str] = None, 
                 context: Dict[str, Any] = None) -> str:
    return interrupter.fracture_text(text, fracture_type, context)

def add_validator(validator_func):
    interrupter.add_validator(validator_func)

# Example validators
def semantic_consistency_validator(text: str) -> Dict[str, Any]:
    # Simple example validator
    words = text.split()
    if len(words) < 3:
        return {"triggered": False, "message": "Text too short", "severity": 1}
    
    # Check for obvious contradictions (simplified)
    contradictions = [("не", "нет"), ("да", "нет")]
    for word1, word2 in contradictions:
        if word1 in words and word2 in words:
            return {"triggered": True, "message": f"Contradiction found: {word1} & {word2}", "severity": 3}
    
    return {"triggered": False, "message": "No contradictions", "severity": 1}

def grammar_validator(text: str) -> Dict[str, Any]:
    # Simple grammar validator
    if not text.strip().endswith(('.', '!', '?')):
        return {"triggered": True, "message": "Missing sentence ending", "severity": 2}
    return {"triggered": False, "message": "Grammar OK", "severity": 1}

# Register default validators
add_validator(semantic_consistency_validator)
add_validator(grammar_validator)

if __name__ == "__main__":
    # Example usage
    test_text = "человек читает книгу в комнате"