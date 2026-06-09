import random
import json
from typing import Dict, List, Any, Tuple
from dataclasses import dataclass
from enum import Enum

class DivergenceType(Enum):
    LEXICAL = "lexical"
    SYNTAX = "syntax"
    PRAGMATIC = "pragmatic"

@dataclass
class DivergenceEvent:
    id: str
    type: DivergenceType
    source_text: str
    target_text: str
    context: Dict[str, Any]
    metadata: Dict[str, Any]

class FractureReplay:
    def __init__(self):
        self.lexical_drift_patterns = [
            ("bank", "берег", "financial institution"),
            ("bank", "банк", "side of river"),
            ("light", "свет", "illumination"),
            ("light", "лёгкий", "not heavy"),
            ("spring", "весна", "season"),
            ("spring", "пружина", "coil mechanism")
        ]
        
        self.syntax_mismatches = [
            ("The cat the dog chased ran away", "Кошка, которую догоняла собака, убежала", "ru"),
            ("I saw the man with the telescope", "Я видел мужчину с телескопом", "ru"),
            ("The old man the boat", "Старик управляет лодкой", "ru")
        ]
        
        self.pragmatic_contexts = [
            {
                "source": "Let's touch base later",
                "target": "Давай свяжемся позже",
                "context": "business communication",
                "cultural_note": "baseball metaphor lost in translation"
            },
            {
                "source": "That's not my cup of tea",
                "target": "Это не моя чашка чая",
                "context": "personal preference",
                "cultural_note": "British idiom confusion"
            },
            {
                "source": "Break a leg!",
                "target": "Сломай ногу!",
                "context": "performance wish",
                "cultural_note": "well-wishing idiom becomes curse"
            }
        ]
        
        self.event_counter = 0

    def generate_lexical_drift(self) -> DivergenceEvent:
        pattern = random.choice(self.lexical_drift_patterns)
        word, translation, meaning = pattern
        
        context = {
            "original_word": word,
            "translation": translation,
            "intended_meaning": meaning,
            "actual_meaning": self._get_actual_meaning(word, translation)
        }
        
        metadata = {
            "divergence_strength": random.uniform(0.3, 0.9),
            "confidence": random.uniform(0.6, 1.0)
        }
        
        self.event_counter += 1
        return DivergenceEvent(
            id=f"lex_{self.event_counter}",
            type=DivergenceType.LEXICAL,
            source_text=f"The {word} stood by the river.",
            target_text=f"{translation} стоял у реки.",
            context=context,
            metadata=metadata
        )

    def generate_syntax_mismatch(self) -> DivergenceEvent:
        pattern = random.choice(self.syntax_mismatches)
        source, target, lang = pattern
        
        context = {
            "source_structure": self._analyze_syntax(source),
            "target_structure": self._analyze_syntax(target),
            "language_pair": f"en-{lang}"
        }
        
        metadata = {
            "complexity": len(source.split()),
            "ambiguity_level": random.uniform(0.4, 0.8)
        }
        
        self.event_counter += 1
        return DivergenceEvent(
            id=f"syntax_{self.event_counter}",
            type=DivergenceType.SYNTAX,
            source_text=source,
            target_text=target,
            context=context,
            metadata=metadata
        )

    def generate_pragmatic_rupture(self) -> DivergenceEvent:
        context_data = random.choice(self.pragmatic_contexts)
        
        context = {
            "cultural_context": context_data["context"],
            "cultural_note": context_data["cultural_note"],
            "intended_message": "friendly gesture",
            "received_message": "confusing/incorrect"
        }
        
        metadata = {
            "cultural_distance": random.uniform(0.5, 1.0),
            "context_sensitivity": random.uniform(0.7, 1.0)
        }
        
        self.event_counter += 1
        return DivergenceEvent(
            id=f"prag_{self.event_counter}",
            type=DivergenceType.PRAGMATIC,
            source_text=context_data["source"],
            target_text=context_data["target"],
            context=context,
            metadata=metadata
        )

    def generate_divergence_batch(self, size: int = 10) -> List[DivergenceEvent]:
        events = []
        for _ in range(size):
            divergence_type = random.choice(list(DivergenceType))
            if divergence_type == DivergenceType.LEXICAL:
                events.append(self.generate_lexical_drift())
            elif divergence_type == DivergenceType.SYNTAX:
                events.append(self.generate_syntax_mismatch())
            else:
                events.append(self.generate_pragmatic_rupture())
        return events

    def export_events(self, events: List[DivergenceEvent], format: str = "json") -> str:
        if format == "json":
            serialized = []
            for event in events:
                serialized.append({
                    "id": event.id,
                    "type": event.type.value,
                    "source_text": event.source_text,
                    "target_text": event.target_text,
                    "context": event.context,
                    "metadata": event.metadata
                })
            return json.dumps(serialized, indent=2, ensure_ascii=False)
        else:
            raise ValueError(f"Unsupported format: {format}")

    def _get_actual_meaning(self, word: str, translation: str) -> str:
        # Simplified mapping for demonstration
        meanings = {
            ("bank", "берег"): "riverbank",
            ("bank", "банк"): "financial institution",
            ("light", "свет"): "illumination",
            ("light", "лёгкий"): "not heavy",
            ("spring", "весна"): "season",
            ("spring", "пружина"): "coil"
        }
        return meanings.get((word, translation), "unknown")

    def _analyze_syntax(self, text: str) -> Dict[str, Any]:
        words = text.split()
        return {
            "length": len(words),
            "structure": "complex" if len(words) > 6 else "simple",
            "word_order": "inverted" if text.startswith(("The", "That")) else "normal"
        }

# Example usage
if __name__ == "__main__":
    replay = FractureReplay()
    events = replay.generate_divergence_batch(5)
    print(replay.export_events(events))