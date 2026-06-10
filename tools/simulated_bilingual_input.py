import json
import logging
import random
import time
from typing import Dict, List, Optional, Tuple

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('simulated_bilingual_input.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('simulated_bilingual_input')

class SemanticDivergenceDetector:
    """Detects semantic divergence between bilingual inputs"""
    
    def __init__(self, threshold: float = 0.7):
        self.threshold = threshold
        self.divergence_count = 0
        
    def calculate_semantic_distance(self, text1: str, text2: str) -> float:
        """
        Calculate semantic distance between two texts.
        Returns a value between 0 (identical) and 1 (completely different).
        """
        # Simplified semantic distance calculation
        words1 = set(text1.lower().split())
        words2 = set(text2.lower().split())
        
        if not words1 and not words2:
            return 0.0
            
        union = words1.union(words2)
        intersection = words1.intersection(words2)
        
        if not union:
            return 1.0
            
        similarity = len(intersection) / len(union)
        return 1.0 - similarity
    
    def check_divergence(self, source_text: str, target_text: str) -> bool:
        """Check if semantic divergence exceeds threshold"""
        distance = self.calculate_semantic_distance(source_text, target_text)
        is_divergent = distance > self.threshold
        
        if is_divergent:
            self.divergence_count += 1
            logger.warning(f"Semantic divergence detected: {distance:.3f} (threshold: {self.threshold})")
            logger.info(f"Source: {source_text}")
            logger.info(f"Target: {target_text}")
        
        return is_divergent

class FractureInterrupter:
    """Handles semantic fracture interrupts"""
    
    def __init__(self):
        self.interrupt_count = 0
        
    def trigger_interrupt(self, source_text: str, target_text: str, divergence_score: float):
        """Trigger fracture interrupt when semantic mismatch exceeds threshold"""
        self.interrupt_count += 1
        logger.critical(f"Fracture interrupt triggered! Count: {self.interrupt_count}")
        logger.critical(f"Divergence score: {divergence_score}")
        logger.critical(f"Source text: {source_text}")
        logger.critical(f"Target text: {target_text}")
        
        # Log interrupt event for unified runtime validator
        interrupt_data = {
            "event_type": "fracture_interrupt",
            "timestamp": time.time(),
            "divergence_score": divergence_score,
            "source_text": source_text,
            "target_text": target_text,
            "interrupt_count": self.interrupt_count
        }
        
        with open('fracture_interrupts.log', 'a') as f:
            f.write(json.dumps(interrupt_data) + '\n')

class SimulatedBilingualInput:
    """Simulates bilingual input processing with divergence detection"""
    
    def __init__(self, divergence_threshold: float = 0.7):
        self.divergence_detector = SemanticDivergenceDetector(divergence_threshold)
        self.fracture_interrupter = FractureInterrupter()
        self.processed_pairs = 0
        self.divergent_pairs = 0
        
        # Sample bilingual text pairs for simulation
        self.text_pairs = [
            ("Hello world", "Hola mundo"),
            ("Good morning", "Buenos días"),
            ("Thank you very much", "Muchas gracias"),
            ("How are you today", "¿Cómo estás hoy"),
            ("The weather is nice", "El clima es agradable"),
            ("I need help", "Necesito ayuda"),
            ("This is a test", "Esto es una prueba"),
            ("Semantic divergence", "Divergencia semántica"),
            ("Artificial intelligence", "Inteligencia artificial"),
            ("Machine learning", "Aprendizaje automático"),
            # Intentionally divergent pairs for testing
            ("The cat is sleeping", "El perro está corriendo"),
            ("I love programming", "Me gusta cocinar"),
            ("Today is sunny", "Hoy está lloviendo"),
        ]
        
    def generate_bilingual_pair(self) -> Tuple[str, str]:
        """Generate a bilingual text pair"""
        return random.choice(self.text_pairs)
    
    def introduce_semantic_divergence(self, source_text: str, target_text: str, probability: float = 0.3) -> Tuple[str, str]:
        """Intentionally introduce semantic divergence for testing purposes"""
        if random.random() < probability:
            # Replace target text with unrelated content
            unrelated_texts = [
                "Completely unrelated sentence",
                "This has nothing to do with the source",
                "Random words with no semantic connection",
                "Semantic mismatch for testing purposes"
            ]
            new_target = random.choice(unrelated_texts)
            logger.debug(f"Introducing semantic divergence: '{target_text}' -> '{new_target}'")
            return source_text, new_target
        return source_text, target_text
    
    def process_input_pair(self) -> Dict:
        """Process a single bilingual input pair"""
        source_text, target_text = self.generate_bilingual_pair()
        
        # Occasionally introduce semantic divergence for testing
        source_text, target_text = self.introduce_semantic_divergence(source_text, target_text)
        
        # Check for semantic divergence
        is_divergent = self.divergence_detector.check_divergence(source_text, target_text)
        
        # Log processing event
        processing_data = {
            "event_type": "input_processing",
            "timestamp": time.time(),
            "source_text": source_text,
            "target_text": target_text,
            "is_divergent": is_divergent,
            "divergence_count": self.divergence_detector.divergence_count,
            "processed_pairs": self.processed_pairs + 1
        }
        
        with open('bilingual_processing.log', 'a') as f:
            f.write(json.dumps(processing_data) + '\n')
        
        self.processed_pairs += 1
        if is_divergent:
            self.divergent_pairs += 1
            divergence_score = self.divergence_detector.calculate_semantic_distance(source_text, target_text)
            self.fracture_interrupter.trigger_interrupt(source_text, target_text, divergence_score)
        
        return processing_data
    
    def run_simulation(self, iterations: int = 10, delay: float = 1.0):
        """Run the bilingual input simulation"""
        logger.info(f"Starting bilingual input simulation with {iterations} iterations")
        logger.info(f"Divergence threshold: {self.divergence_detector.threshold}")
        
        for i in range(iterations):
            logger.info(f"Processing iteration {i+1}/{iterations}")
            
            try:
                result = self.process_input_pair()
                logger.info(f"Processed pair: {result['source_text']} <-> {result['target_text']}")
                
                if result['is_divergent']:
                    logger.warning("Divergent pair detected and logged")
                
            except Exception as e:
                logger.error(f"Error processing input pair: {e}")
                continue
            
            # Optional delay between iterations
            if delay > 0:
                time.sleep(delay)
        
        # Log final statistics
        stats = {
            "event_type": "simulation_summary",
            "timestamp": time.time(),
            "total_processed": self.processed_pairs,
            "divergent_pairs": self.divergent_pairs,
            "fracture_interrupts": self.fracture_interrupter.interrupt_count,
            "divergence_rate": self.divergent_pairs / self.processed_pairs if self.processed_pairs > 0 else 0
        }
        
        logger.info("Simulation completed")
        logger.info(f"Total processed pairs: {stats['total_processed']}")
        logger.info(f"Divergent pairs: {stats['divergent_pairs']}")
        logger.info(f"Fracture interrupts: {stats['fracture_interrupts']}")
        logger.info(f"Divergence rate: {stats['divergence_rate']:.2%}")
        
        with open('simulation_summary.log', 'a') as f:
            f.write(json.dumps(stats) + '\n')
        
        return stats

def main():
    """Main function to run the simulated bilingual input"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Simulated Bilingual Input Processor')
    parser.add_argument('--iterations', type=int, default=10, help='Number of iterations to run')
    parser.add_argument('--threshold', type=float, default=0.7, help='Semantic divergence threshold')
    parser.add_argument('--delay', type=float, default=1.0, help='Delay between iterations in seconds')
    
    args = parser.parse_args()
    
    # Initialize and run simulation
    simulator = SimulatedBilingualInput(divergence_threshold=args.threshold)
    simulator.run_simulation(iterations=args.iterations, delay=args.delay)

if __name__ == "__main__":
    main()