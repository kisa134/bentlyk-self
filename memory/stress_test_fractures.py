import sys
import traceback
from typing import List, Tuple, Any, Dict
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
import random
import string

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("stress_test_fractures.log"),
        logging.StreamHandler(sys.stdout)
    ]
)

logger = logging.getLogger(__name__)

# Mock language processing stacks - replace with actual implementations
class RussianProcessor:
    def process(self, text: str) -> Dict[str, Any]:
        # Simulate complex processing that might fail
        if "сущ" in text.lower():
            raise ValueError("Semantic fracture detected in Russian processing")
        return {"processed_text": text.upper(), "language": "ru"}

class EnglishProcessor:
    def process(self, text: str) -> Dict[str, Any]:
        # Simulate complex processing that might fail
        if "noun" in text.lower():
            raise ValueError("Semantic fracture detected in English processing")
        return {"processed_text": text.upper(), "language": "en"}

# Initialize processors
russian_processor = RussianProcessor()
english_processor = EnglishProcessor()

def generate_synthetic_prompts(count: int) -> List[str]:
    """Generate synthetic prompts designed to exploit linguistic fragmentation points."""
    prompts = []
    russian_chars = "абвгдеёжзийклмнопрстуфхцчшщъыьэюя"
    english_chars = string.ascii_lowercase
    
    for _ in range(count):
        # Mix languages in various ways
        prompt_parts = []
        
        # Add random Russian-like fragments
        ru_length = random.randint(3, 8)
        ru_fragment = ''.join(random.choices(russian_chars, k=ru_length))
        prompt_parts.append(ru_fragment)
        
        # Add English words that might trigger fractures
        fracture_triggers = ["noun", "verb", "adjective", "сущ", "глаг", "прил"]
        trigger = random.choice(fracture_triggers)
        prompt_parts.append(trigger)
        
        # Add random English fragments
        en_length = random.randint(3, 8)
        en_fragment = ''.join(random.choices(english_chars, k=en_length))
        prompt_parts.append(en_fragment)
        
        # Randomly shuffle parts
        random.shuffle(prompt_parts)
        prompts.append(' '.join(prompt_parts))
    
    return prompts

def run_processors_concurrently(prompt: str) -> Tuple[str, Dict[str, Any], Dict[str, Any], List[str]]:
    """Run both language processors on a prompt and capture results or exceptions."""
    divergence_tracebacks = []
    ru_result = None
    en_result = None
    
    try:
        ru_result = russian_processor.process(prompt)
    except Exception as e:
        divergence_tracebacks.append(f"Russian processor error: {str(e)}\n{traceback.format_exc()}")
    
    try:
        en_result = english_processor.process(prompt)
    except Exception as e:
        divergence_tracebacks.append(f"English processor error: {str(e)}\n{traceback.format_exc()}")
    
    return prompt, ru_result, en_result, divergence_tracebacks

def detect_divergence(ru_result: Dict[str, Any], en_result: Dict[str, Any]) -> bool:
    """Detect if there's a semantic divergence between results."""
    if ru_result is None and en_result is None:
        return False
    if ru_result is None or en_result is None:
        return True
    return ru_result != en_result

def log_divergence_event(prompt: str, ru_result: Dict[str, Any], en_result: Dict[str, Any], tracebacks: List[str]):
    """Log detailed divergence event information."""
    logger.error("="*50)
    logger.error("DIVERGENCE DETECTED")
    logger.error(f"PROMPT: {prompt}")
    logger.error(f"RUSSIAN RESULT: {ru_result}")
    logger.error(f"ENGLISH RESULT: {en_result}")
    for tb in tracebacks:
        logger.error(tb)
    logger.error("="*50)

def main():
    """Main stress testing function."""
    logger.info("Starting semantic fracture stress test")
    
    # Generate test cases
    prompts = generate_synthetic_prompts(100)
    logger.info(f"Generated {len(prompts)} synthetic prompts")
    
    divergence_count = 0
    
    # Process prompts concurrently
    with ThreadPoolExecutor(max_workers=10) as executor:
        # Submit all tasks
        future_to_prompt = {
            executor.submit(run_processors_concurrently, prompt): prompt 
            for prompt in prompts
        }
        
        # Process completed tasks
        for future in as_completed(future_to_prompt):
            prompt, ru_result, en_result, tracebacks = future.result()
            
            # Log any immediate errors
            for tb in tracebacks:
                logger.warning(f"Processing error for '{prompt}': {tb}")
            
            # Check for semantic divergence
            if detect_divergence(ru_result, en_result):
                divergence_count += 1
                log_divergence_event(prompt, ru_result, en_result, tracebacks)
    
    logger.info(f"Stress test completed. Found {divergence_count} divergence events out of {len(prompts)} prompts")

if __name__ == "__main__":
    main()