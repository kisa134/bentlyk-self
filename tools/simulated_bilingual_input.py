import random
import time
import logging
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class SimulatedBilingualInput:
    def __init__(self):
        self.russian_idioms = [
            "бить баклуши",
            "вешать лапшу на уши",
            "гвоздем моря не разогреешь",
            "дело в шляпе",
            "дойти до ручки"
        ]
        
        self.literal_translations = [
            "to beat the okras",
            "to hang noodles on ears",
            "you won't heat the sea with a nail",
            "the дело is in the hat",
            "to reach the handle"
        ]
        
        self.english_phrases = [
            "time flies",
            "break a leg",
            "piece of cake",
            "hit the hay",
            "spill the beans"
        ]
        
        self.russian_structures = [
            "летит время",
            "ногу сломать",
            "кусок торта",
            "ударить сено",
            "пролить бобы"
        ]

    def generate_russian_idiom_with_literal_translation(self):
        """Generate Russian idiom with literal English translation"""
        idx = random.randint(0, len(self.russian_idioms) - 1)
        idiom = self.russian_idioms[idx]
        literal = self.literal_translations[idx]
        
        # Log stack context and timestamp
        timestamp = datetime.now().isoformat()
        logger.info(f"Generating Russian idiom with literal translation: {idiom} -> {literal}")
        logger.info(f"Timestamp: {timestamp}")
        logger.info(f"Stack context: generate_russian_idiom_with_literal_translation")
        
        return f"{idiom} ({literal})"

    def generate_english_with_russian_syntax(self):
        """Generate English phrase with Russian syntactic structure"""
        idx = random.randint(0, len(self.english_phrases) - 1)
        english = self.english_phrases[idx]
        russian_syntax = self.russian_structures[idx]
        
        # Log stack context and timestamp
        timestamp = datetime.now().isoformat()
        logger.info(f"Generating English with Russian syntax: {english} -> {russian_syntax}")
        logger.info(f"Timestamp: {timestamp}")
        logger.info(f"Stack context: generate_english_with_russian_syntax")
        
        return f"{english} [{russian_syntax}]"

    def generate_alternating_language_fragments(self):
        """Generate alternating language fragments mid-sentence"""
        fragments = []
        languages = ['en', 'ru']
        current_lang = random.choice(languages)
        
        for i in range(5):
            if current_lang == 'en':
                fragment = random.choice(self.english_phrases)
            else:
                fragment = random.choice(self.russian_idioms)
            
            fragments.append(fragment)
            current_lang = 'ru' if current_lang == 'en' else 'en'
        
        result = " ".join(fragments)
        
        # Log stack context and timestamp
        timestamp = datetime.now().isoformat()
        logger.info(f"Generating alternating language fragments: {result}")
        logger.info(f"Timestamp: {timestamp}")
        logger.info(f"Stack context: generate_alternating_language_fragments")
        
        return result

    def simulate_input_stream(self, count=10):
        """Simulate input stream with various bilingual patterns"""
        generators = [
            self.generate_russian_idiom_with_literal_translation,
            self.generate_english_with_russian_syntax,
            self.generate_alternating_language_fragments
        ]
        
        results = []
        for _ in range(count):
            generator = random.choice(generators)
            result = generator()
            results.append(result)
            time.sleep(0.1)  # Small delay to simulate real-time input
        
        return results

# Example usage
if __name__ == "__main__":
    simulator = SimulatedBilingualInput()
    
    # Generate different types of bilingual input
    print("Russian idiom with literal translation:")
    print(simulator.generate_russian_idiom_with_literal_translation())
    
    print("\nEnglish with Russian syntax:")
    print(simulator.generate_english_with_russian_syntax())
    
    print("\nAlternating language fragments:")
    print(simulator.generate_alternating_language_fragments())
    
    print("\nSimulated input stream:")
    stream = simulator.simulate_input_stream(5)
    for item in stream:
        print(item)