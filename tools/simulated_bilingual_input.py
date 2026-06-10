import json
import random
import uuid
from datetime import datetime
from typing import Dict, List, Tuple

class BilingualPayloadGenerator:
    def __init__(self):
        self.gender_map = {
            "actor": "actress",
            "manager": "manager",  # neutral
            "doctor": "doctor",    # neutral
            "student": "student"   # neutral
        }
        
        self.russian_tense_map = {
            "present": "прошедшее",    # past
            "past": "настоящее",       # present
            "future": "прошедшее"      # past
        }
        
        self.unicode_collisions = {
            "a": "а",  # Latin 'a' to Cyrillic 'a'
            "e": "е",  # Latin 'e' to Cyrillic 'e'
            "o": "о",  # Latin 'o' to Cyrillic 'o'
            "p": "р",  # Latin 'p' to Cyrillic 'p'
            "c": "с",  # Latin 'c' to Cyrillic 'c'
            "y": "у",  # Latin 'y' to Cyrillic 'y'
            "x": "х"   # Latin 'x' to Cyrillic 'x'
        }
        
        self.mutations_log = []

    def generate_bilingual_payload(self) -> Dict:
        base_payload = {
            "id": str(uuid.uuid4()),
            "timestamp": datetime.utcnow().isoformat(),
            "english": {
                "sentence": "The actor performed well in the play.",
                "tense": "past",
                "entities": ["actor"]
            },
            "russian": {
                "sentence": "Актер хорошо сыграл в пьесе.",
                "tense": "прошедшее",
                "entities": ["актер"]
            }
        }
        
        # Apply mutations
        mutated_payload = self._apply_mutations(base_payload)
        
        # Log mutation details
        self._log_mutations(mutated_payload)
        
        return mutated_payload

    def _apply_mutations(self, payload: Dict) -> Dict:
        mutated = payload.copy()
        
        # Gender mutation
        if random.random() > 0.5:
            mutated = self._apply_gender_mutation(mutated)
        
        # Tense mutation
        if random.random() > 0.5:
            mutated = self._apply_tense_mutation(mutated)
        
        # Unicode collision
        if random.random() > 0.5:
            mutated = self._apply_unicode_collision(mutated)
        
        return mutated

    def _apply_gender_mutation(self, payload: Dict) -> Dict:
        mutated = payload.copy()
        
        # Change "actor" to "actress" in English but keep "актер" in Russian
        if "actor" in mutated["english"]["sentence"]:
            mutated["english"]["sentence"] = mutated["english"]["sentence"].replace("actor", "actress")
            mutated["english"]["entities"] = ["actress"]
            self.mutations_log.append({
                "type": "gender_mismatch",
                "english": "actress",
                "russian": "актер",
                "timestamp": datetime.utcnow().isoformat()
            })
        
        return mutated

    def _apply_tense_mutation(self, payload: Dict) -> Dict:
        mutated = payload.copy()
        
        # Change English to present but keep Russian past
        mutated["english"]["sentence"] = "The actor performs well in plays."
        mutated["english"]["tense"] = "present"
        mutated["english"]["entities"] = ["actor"]
        
        self.mutations_log.append({
            "type": "tense_mismatch",
            "english_tense": "present",
            "russian_tense": "прошедшее",
            "timestamp": datetime.utcnow().isoformat()
        })
        
        return mutated

    def _apply_unicode_collision(self, payload: Dict) -> Dict:
        mutated = payload.copy()
        
        # Introduce Cyrillic characters in English text
        sentence = mutated["english"]["sentence"]
        # Replace some characters with visually similar Cyrillic ones
        for latin, cyrillic in list(self.unicode_collisions.items())[:3]:
            sentence = sentence.replace(latin, cyrillic)
        
        mutated["english"]["sentence"] = sentence
        self.mutations_log.append({
            "type": "unicode_collision",
            "original": payload["english"]["sentence"],
            "mutated": sentence,
            "timestamp": datetime.utcnow().isoformat()
        })
        
        return mutated

    def _log_mutations(self, payload: Dict):
        validation_trace = {
            "payload_id": payload["id"],
            "validation_results": self._validate_payload(payload),
            "mutations": self.mutations_log.copy(),
            "timestamp": datetime.utcnow().isoformat()
        }
        
        # Clear log for next payload
        self.mutations_log.clear()
        
        # Print validation trace (in real implementation, this would go to fracture_interrupter.py)
        print(json.dumps(validation_trace, indent=2))

    def _validate_payload(self, payload: Dict) -> List[Dict]:
        issues = []
        
        # Check for gender mismatches
        if "actress" in payload["english"]["sentence"] and "актер" in payload["russian"]["sentence"]:
            issues.append({
                "type": "gender_conflict",
                "severity": "high",
                "description": "English 'actress' (feminine) vs Russian 'актер' (masculine)"
            })
        
        # Check for tense mismatches
        if payload["english"]["tense"] == "present" and payload["russian"]["tense"] == "прошедшее":
            issues.append({
                "type": "tense_conflict",
                "severity": "high",
                "description": "English present vs Russian past tense mismatch"
            })
        
        # Check for unicode collisions
        sentence = payload["english"]["sentence"]
        for latin, cyrillic in self.unicode_collisions.items():
            if cyrillic in sentence:
                issues.append({
                    "type": "unicode_collision",
                    "severity": "medium",
                    "description": f"Found Cyrillic character '{cyrillic}' in English text"
                })
                break
        
        return issues

def main():
    generator = BilingualPayloadGenerator()
    
    # Generate 5 sample payloads
    for i in range(5):
        print(f"\n--- Payload {i+1} ---")
        payload = generator.generate_bilingual_payload()
        print(json.dumps(payload, indent=2, ensure_ascii=False))

if __name__ == "__main__":
    main()