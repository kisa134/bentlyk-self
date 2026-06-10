import random
import json
import logging
from typing import List, Tuple
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class SimulatedBilingualInput:
    def __init__(self):
        self.pairs_generated = 0
        self.mismatch_types = [
            'lexical_substitution',
            'cultural_concept',
            'grammatical_role',
            'temporal_shift',
            'spatial_conflict'
        ]
        
    def generate_mismatched_pair(self) -> Tuple[str, str, str]:
        """Generate a single pair of sentences with deliberate semantic mismatch"""
        mismatch_type = random.choice(self.mismatch_types)
        
        if mismatch_type == 'lexical_substitution':
            # Same structure, different key word meaning
            en_sentence = "The bank officer approved the loan."
            ru_sentence = "Банковский офицер одобрил заем."  # 'bank' = river bank
            
        elif mismatch_type == 'cultural_concept':
            # Culturally specific concepts that don't translate directly
            en_sentence = "He threw a curveball during the meeting."
            ru_sentence = "Он бросил кривую подачу во время встречи."  # Baseball term in business context
            
        elif mismatch_type == 'grammatical_role':
            # Same words, different grammatical function
            en_sentence = "The chicken is ready to eat."
            ru_sentence = "Курица готова к еде."  # Ambiguous: chicken ready to eat (food) vs chicken ready to eat (action)
            
        elif mismatch_type == 'temporal_shift':
            # Time reference inconsistencies
            en_sentence = "I will call you tomorrow morning."
            ru_sentence = "Я позвоню тебе завтра вечером."  # tomorrow morning vs evening
            
        elif mismatch_type == 'spatial_conflict':
            # Directional/positional inconsistencies
            en_sentence = "The library is on the left side of the street."
            ru_sentence = "Библиотека находится справа от улицы."  # left vs right
            
        return en_sentence, ru_sentence, mismatch_type
        
    def generate_batch(self, count: int = 10) -> List[Tuple[str, str, str]]:
        """Generate a batch of mismatched sentence pairs"""
        pairs = []
        for _ in range(count):
            pair = self.generate_mismatched_pair()
            pairs.append(pair)
            self.pairs_generated += 1
        return pairs
        
    def log_interaction(self, en_sentence: str, ru_sentence: str, 
                       mismatch_type: str, validator_response: dict):
        """Log the input pair and validator response"""
        log_entry = {
            'timestamp': datetime.now().isoformat(),
            'input': {
                'english': en_sentence,
                'russian': ru_sentence,
                'mismatch_type': mismatch_type
            },
            'validator_response': validator_response,
            'pair_id': self.pairs_generated
        }
        
        logger.info(f"Mismatch Type: {mismatch_type}")
        logger.info(f"English: {en_sentence}")
        logger.info(f"Russian: {ru_sentence}")
        logger.info(f"Validator Response: {json.dumps(validator_response, indent=2)}")
        logger.info("-" * 50)
        
        return log_entry

# Example usage
if __name__ == "__main__":
    simulator = SimulatedBilingualInput()
    
    # Generate and log sample pairs
    sample_pairs = simulator.generate_batch(5)
    
    for en_sent, ru_sent, mismatch_type in sample_pairs:
        # Simulate validator response (in real implementation, this would be actual validation)
        validator_response = {
            "semantically_aligned": False,
            "confidence_score": random.uniform(0.1, 0.6),
            "detected_fractures": [
                {
                    "type": mismatch_type,
                    "position": "full_sentence",
                    "severity": "high"
                }
            ]
        }
        
        simulator.log_interaction(en_sent, ru_sent, mismatch_type, validator_response)