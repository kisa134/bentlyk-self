import logging
import random
from typing import List, Tuple
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class BilingualInputSimulator:
    def __init__(self):
        self.fracture_events = []
        
    def generate_semantic_fractures(self) -> List[Tuple[str, str]]:
        """Generate Russian-English sentence pairs with subtle semantic misalignments"""
        fracture_pairs = [
            # Temporal mismatch
            ("Я уже закончил работу.", "I haven't finished the work yet."),
            # Negation divergence  
            ("Он никогда не был здесь.", "He has always been here."),
            # Quantifier mismatch
            ("Несколько студентов пришли.", "No students came."),
            # Causal relationship inversion
            ("Из-за дождя дороги стали скользкими.", "The roads became slippery despite the sunny weather."),
            # Modal verb contradiction
            ("Мне нужно было уйти раньше.", "I didn't need to leave early."),
            # Spatial preposition conflict
            ("Книга лежит под столом.", "The book is on top of the table."),
            # Agent-role reversal
            ("Полиция арестовала протестующих.", "The protesters arrested the police."),
            # Aspectual mismatch
            ("Он читал книгу три часа.", "He read the book in three hours."),
            # Evidentiality contradiction
            ("Кажется, он болен.", "He is definitely healthy."),
            # Scalar implicature violation
            ("Некоторые студенты сдали экзамен.", "All students failed the exam.")
        ]
        return fracture_pairs
    
    def inject_fracture_pairs(self, pairs: List[Tuple[str, str]]) -> None:
        """Inject fracture pairs into processing pipeline"""
        for i, (ru, en) in enumerate(pairs):
            event = {
                'id': f'fracture_{i}_{datetime.now().strftime("%Y%m%d_%H%M%S")}',
                'timestamp': datetime.now().isoformat(),
                'russian': ru,
                'english': en,
                'type': self._classify_fracture_type(ru, en)
            }
            self.fracture_events.append(event)
            logger.info(f"Injected fracture pair {event['id']}: {ru} | {en}")
            
    def _classify_fracture_type(self, ru: str, en: str) -> str:
        """Classify the type of semantic fracture"""
        # Simplified classification based on content
        if "не" in ru or "never" in en:
            return "negation"
        elif "уже" in ru or "yet" in en:
            return "temporal"
        elif "сколько" in ru or "several" in en:
            return "quantifier" 
        else:
            return "other"
            
    def log_system_responses(self, responses: List[dict]) -> None:
        """Log system responses to fracture events"""
        for response in responses:
            logger.info(f"System response to {response.get('event_id', 'unknown')}: "
                       f"Validation: {response.get('validation_result', 'unknown')} | "
                       f"Confidence: {response.get('confidence_score', 0.0)} | "
                       f"Detected_issues: {response.get('detected_issues', [])}")

def simulate_bilingual_pipeline():
    """Main simulation function"""
    simulator = BilingualInputSimulator()
    
    # Generate and inject fracture pairs
    fracture_pairs = simulator.generate_semantic_fractures()
    simulator.inject_fracture_pairs(fracture_pairs)
    
    # Simulate system responses (in real implementation, this would come from validators)
    responses = []
    for event in simulator.fracture_events:
        # Mock responses with varying confidence levels
        response = {
            'event_id': event['id'],
            'validation_result': random.choice(['rejected', 'flagged', 'accepted']),
            'confidence_score': round(random.uniform(0.1, 0.9), 2),
            'detected_issues': ['semantic_misalignment'] if random.random() > 0.3 else []
        }
        responses.append(response)
    
    # Log system responses
    simulator.log_system_responses(responses)
    
    return simulator.fracture_events, responses

if __name__ == "__main__":
    events, responses = simulate_bilingual_pipeline()
    print(f"Generated {len(events)} fracture events")
    print(f"System processed {len(responses)} responses")