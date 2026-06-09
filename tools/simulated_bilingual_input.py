import json
import random
import logging
from typing import Tuple, List, Dict
from pathlib import Path

# Configure logging
logging.basicConfig(
    filename='validation_traces.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

class BilingualInputGenerator:
    def __init__(self):
        self.semantic_mismatch_templates = [
            ("The {} is {}.", "El {} está {}."),  # Correct translation template
            ("The {} {} the {}.", "El {} {} el {}."),  # Correct translation template
            ("{} {} {}.", "{} {} {}."),  # Generic structure
        ]
        
        # Semantic mismatch patterns that should trigger fracture detection
        self.mismatch_patterns = [
            # Pattern: English subject doesn't match Spanish subject
            {
                "en": "The {} {}.",
                "es": "El {} {}.",
                "mismatch": "subject"
            },
            # Pattern: Different verbs
            {
                "en": "The {} {} the {}.",
                "es": "El {} {} el {}.",
                "mismatch": "verb"
            },
            # Pattern: Different objects
            {
                "en": "The {} {} the {}.",
                "es": "El {} {} el {}.",
                "mismatch": "object"
            },
            # Pattern: Different sentence structures
            {
                "en": "{} {} {}.",
                "es": "{} {} {} {}.",
                "mismatch": "structure"
            }
        ]
        
        # Vocabulary for generation
        self.vocabulary = {
            "nouns": ["cat", "dog", "house", "car", "tree", "book", "computer", "phone"],
            "verbs": ["runs", "jumps", "eats", "drives", "reads", "writes", "sleeps", "works"],
            "adjectives": ["big", "small", "red", "blue", "fast", "slow", "old", "new"],
            "articles": ["the", "a", "an"]
        }
        
        self.spanish_vocab = {
            "nouns": ["gato", "perro", "casa", "coche", "árbol", "libro", "computadora", "teléfono"],
            "verbs": ["corre", "salta", "come", "maneja", "lee", "escribe", "duerme", "trabaja"],
            "adjectives": ["grande", "pequeño", "rojo", "azul", "rápido", "lento", "viejo", "nuevo"],
            "articles": ["el", "un", "una"]
        }

    def generate_semantically_aligned_pair(self) -> Tuple[str, str]:
        """Generate a semantically correct English-Spanish pair"""
        pattern = random.choice(self.semantic_mismatch_templates)
        
        # Fill in with matching vocabulary
        noun_idx = random.randint(0, len(self.vocabulary["nouns"]) - 1)
        verb_idx = random.randint(0, len(self.vocabulary["verbs"]) - 1)
        adj_idx = random.randint(0, len(self.vocabulary["adjectives"]) - 1)
        
        en_sentence = pattern[0].format(
            self.vocabulary["nouns"][noun_idx],
            self.vocabulary["verbs"][verb_idx] if "{}" in pattern[0] and pattern[0].count("{}") > 1 else 
            self.vocabulary["adjectives"][adj_idx]
        )
        
        es_sentence = pattern[1].format(
            self.spanish_vocab["nouns"][noun_idx],
            self.spanish_vocab["verbs"][verb_idx] if "{}" in pattern[1] and pattern[1].count("{}") > 1 else 
            self.spanish_vocab["adjectives"][adj_idx]
        )
        
        return en_sentence, es_sentence

    def generate_semantic_mismatch_pair(self) -> Tuple[str, str]:
        """Generate a deliberately semantically mismatched pair"""
        pattern = random.choice(self.mismatch_patterns)
        
        # Select vocabulary indices
        noun_idx_en = random.randint(0, len(self.vocabulary["nouns"]) - 1)
        noun_idx_es = random.randint(0, len(self.spanish_vocab["nouns"]) - 1)
        verb_idx_en = random.randint(0, len(self.vocabulary["verbs"]) - 1)
        verb_idx_es = random.randint(0, len(self.spanish_vocab["verbs"]) - 1)
        adj_idx_en = random.randint(0, len(self.vocabulary["adjectives"]) - 1)
        adj_idx_es = random.randint(0, len(self.spanish_vocab["adjectives"]) - 1)
        
        # Create mismatch based on pattern
        mismatch_type = pattern["mismatch"]
        
        if mismatch_type == "subject":
            # Different subjects
            en_sentence = pattern["en"].format(
                self.vocabulary["nouns"][noun_idx_en],
                self.vocabulary["verbs"][verb_idx_en]
            )
            es_sentence = pattern["es"].format(
                self.spanish_vocab["nouns"][noun_idx_es],  # Mismatched subject
                self.spanish_vocab["verbs"][verb_idx_es]
            )
        elif mismatch_type == "verb":
            # Different verbs
            en_sentence = pattern["en"].format(
                self.vocabulary["nouns"][noun_idx_en],
                self.vocabulary["verbs"][verb_idx_en]
            )
            es_sentence = pattern["es"].format(
                self.spanish_vocab["nouns"][noun_idx_es],
                self.spanish_vocab["verbs"][verb_idx_es]  # Mismatched verb
            )
        elif mismatch_type == "object":
            # Different objects
            en_sentence = pattern["en"].format(
                self.vocabulary["nouns"][noun_idx_en],
                self.vocabulary["verbs"][verb_idx_en],
                self.vocabulary["nouns"][random.randint(0, len(self.vocabulary["nouns"]) - 1)]
            )
            es_sentence = pattern["es"].format(
                self.spanish_vocab["nouns"][noun_idx_es],
                self.spanish_vocab["verbs"][verb_idx_es],
                self.spanish_vocab["nouns"][random.randint(0, len(self.spanish_vocab["nouns"]) - 1)]  # Mismatched object
            )
        elif mismatch_type == "structure":
            # Different sentence structures
            en_sentence = pattern["en"].format(
                self.vocabulary["articles"][random.randint(0, len(self.vocabulary["articles"]) - 1)],
                self.vocabulary["nouns"][noun_idx_en],
                self.vocabulary["verbs"][verb_idx_en]
            )
            es_sentence = pattern["es"].format(
                self.spanish_vocab["articles"][random.randint(0, len(self.spanish_vocab["articles"]) - 1)],
                self.spanish_vocab["adjectives"][adj_idx_es],
                self.spanish_vocab["nouns"][noun_idx_es],
                self.spanish_vocab["verbs"][verb_idx_es]
            )
        else:
            # Default case with some mismatch
            en_sentence = pattern["en"].format(
                self.vocabulary["nouns"][noun_idx_en],
                self.vocabulary["verbs"][verb_idx_en]
            )
            es_sentence = pattern["es"].format(
                self.spanish_vocab["nouns"][noun_idx_es],
                self.spanish_vocab["verbs"][verb_idx_es]
            )
            
        return en_sentence, es_sentence

    def generate_adversarial_pairs(self, count: int = 100) -> List[Dict]:
        """Generate adversarial bilingual pairs with semantic mismatches"""
        pairs = []
        
        for i in range(count):
            # Generate both aligned and mismatched pairs
            if random.random() < 0.5:
                # Generate semantically aligned pair
                en_text, es_text = self.generate_semantically_aligned_pair()
                is_mismatched = False
            else:
                # Generate semantically mismatched pair
                en_text, es_text = self.generate_semantic_mismatch_pair()
                is_mismatched = True
                
            pair_data = {
                "id": i,
                "english": en_text,
                "spanish": es_text,
                "is_mismatched": is_mismatched,
                "timestamp": __import__('datetime').datetime.now().isoformat()
            }
            
            pairs.append(pair_data)
            
            # Log the generated pair for analysis
            logging.info(f"Generated pair {i}: EN='{en_text}' | ES='{es_text}' | Mismatched={is_mismatched}")
            
        return pairs

    def save_pairs_to_file(self, pairs: List[Dict], filename: str = "bilingual_input_pairs.json"):
        """Save generated pairs to a JSON file"""
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(pairs, f, indent=2, ensure_ascii=False)
        logging.info(f"Saved {len(pairs)} pairs to {filename}")

def main():
    """Main function to generate and save adversarial bilingual input pairs"""
    generator = BilingualInputGenerator()
    
    # Generate 200 adversarial pairs
    pairs = generator.generate_adversarial_pairs(200)
    
    # Save to file
    generator.save_pairs_to_file(pairs)
    
    # Log summary
    mismatched_count = sum(1