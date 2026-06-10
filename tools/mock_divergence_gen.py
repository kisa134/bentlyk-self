import time
import json
import threading
import random
import logging
from datetime import datetime
from collections import defaultdict, deque
from typing import Dict, List, Optional, Tuple
import queue

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s.%(msecs)03d - %(name)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger('mock_divergence_gen')

class FractureContext:
    def __init__(self):
        self.language_mode = "bilingual"
        self.active_validators = []
        self.execution_stack = []
        self.timestamp = None
        
    def update_context(self, lang_mode: str = None, validators: List[str] = None, stack: List[str] = None):
        if lang_mode is not None:
            self.language_mode = lang_mode
        if validators is not None:
            self.active_validators = validators[:]
        if stack is not None:
            self.execution_stack = stack[:]
        self.timestamp = time.time()
        
    def to_dict(self):
        return {
            "language_mode": self.language_mode,
            "active_validators": self.active_validators,
            "execution_stack": self.execution_stack,
            "timestamp": self.timestamp
        }

class MockDivergenceGenerator:
    def __init__(self, log_queue: queue.Queue = None):
        self.context = FractureContext()
        self.log_queue = log_queue or queue.Queue()
        self.running = False
        self.divergence_events = []
        self.divergence_counter = 0
        
        # Predefined semantic fracture patterns
        self.fracture_patterns = [
            {"type": "semantic_shift", "severity": "high", "languages": ["ru", "en"]},
            {"type": "context_mismatch", "severity": "medium", "languages": ["ru", "en"]},
            {"type": "translation_drift", "severity": "low", "languages": ["ru", "en"]},
            {"type": "syntax_collision", "severity": "high", "languages": ["ru", "en"]},
            {"type": "idiom_conflict", "severity": "medium", "languages": ["ru", "en"]}
        ]
        
        # Validator pool
        self.validator_pool = [
            "validator_alpha", "validator_beta", "validator_gamma", 
            "validator_delta", "validator_epsilon", "validator_zeta"
        ]
        
        # Execution contexts
        self.execution_contexts = [
            "translation_layer",
            "semantic_mapping",
            "context_resolution",
            "syntax_analysis",
            "idiom_processing"
        ]
        
    def start_monitoring(self):
        """Start the high-resolution monitoring thread"""
        self.running = True
        self.monitor_thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self.monitor_thread.start()
        logger.info("Started high-resolution divergence monitoring")
        
    def stop_monitoring(self):
        """Stop the monitoring thread"""
        self.running = False
        if hasattr(self, 'monitor_thread'):
            self.monitor_thread.join(timeout=2.0)
        logger.info("Stopped divergence monitoring")
        
    def _monitor_loop(self):
        """Main monitoring loop running at 1ms intervals"""
        while self.running:
            try:
                # Simulate context updates
                self._update_context()
                
                # Check for semantic fractures
                if self._should_generate_fracture():
                    self._generate_fracture_event()
                
                # Log current state
                self._log_current_state()
                
                # Sleep for 1ms
                time.sleep(0.001)
                
            except Exception as e:
                logger.error(f"Error in monitoring loop: {e}")
                
    def _update_context(self):
        """Update the fracture context with realistic data"""
        # Randomly change language mode occasionally
        if random.random() < 0.05:  # 5% chance per interval
            modes = ["bilingual", "russian_dominant", "english_dominant", "mixed"]
            self.context.update_context(lang_mode=random.choice(modes))
            
        # Update active validators (20% chance per interval)
        if random.random() < 0.2:
            num_validators = random.randint(2, len(self.validator_pool))
            active = random.sample(self.validator_pool, num_validators)
            self.context.update_context(validators=active)
            
        # Update execution stack (30% chance per interval)
        if random.random() < 0.3:
            stack_depth = random.randint(1, 4)
            stack = random.sample(self.execution_contexts, min(stack_depth, len(self.execution_contexts)))
            self.context.update_context(stack=stack)
            
    def _should_generate_fracture(self) -> bool:
        """Determine if a fracture should be generated"""
        # Base probability adjusted by context
        base_prob = 0.001  # 0.1% per millisecond
        
        # Increase probability based on context complexity
        complexity_factor = len(self.context.active_validators) * 0.1
        stack_factor = len(self.context.execution_stack) * 0.05
        mode_factor = 0.1 if self.context.language_mode == "mixed" else 0
        
        probability = base_prob + complexity_factor + stack_factor + mode_factor
        return random.random() < min(probability, 0.1)  # Cap at 10%
        
    def _generate_fracture_event(self):
        """Generate a semantic fracture event"""
        self.divergence_counter += 1
        
        # Select a fracture pattern
        pattern = random.choice(self.fracture_patterns)
        
        # Generate detailed fracture data
        fracture_data = {
            "event_id": f"frac_{int(time.time() * 1000)}_{self.divergence_counter}",
            "timestamp": time.time(),
            "fracture_type": pattern["type"],
            "severity": pattern["severity"],
            "languages_involved": pattern["languages"],
            "context": self.context.to_dict(),
            "semantic_distance": random.uniform(0.1, 0.9),
            "confidence_score": random.uniform(0.7, 0.99),
            "resolution_required": random.random() > 0.3  # 70% need resolution
        }
        
        self.divergence_events.append(fracture_data)
        logger.info(f"Generated fracture: {fracture_data['fracture_type']} (ID: {fracture_data['event_id']})")
        
        # Send to log queue for fracture_interrupter processing
        try:
            self.log_queue.put_nowait(fracture_data)
        except queue.Full:
            logger.warning("Log queue full, dropping fracture event")
            
    def _log_current_state(self):
        """Log the current monitoring state at regular intervals"""
        if len(self.divergence_events) % 1000 == 0 and self.divergence_events:
            logger.debug(f"Current context: {self.context.to_dict()}")
            logger.debug(f"Total fractures generated: {len(self.divergence_events)}")
            
    def get_recent_fractures(self, count: int = 10) -> List[Dict]:
        """Get the most recent fracture events"""
        return list(reversed(self.divergence_events[-count:]))
        
    def get_fracture_stats(self) -> Dict:
        """Get statistics about generated fractures"""
        if not self.divergence_events:
            return {"total_fractures": 0}
            
        type_counts = defaultdict(int)
        severity_counts = defaultdict(int)
        
        for event in self.divergence_events:
            type_counts[event["fracture_type"]] += 1
            severity_counts[event["severity"]] += 1
            
        return {
            "total_fractures": len(self.divergence_events),
            "fracture_types": dict(type_counts),
            "severity_distribution": dict(severity_counts),
            "latest_fracture": self.divergence_events[-1]["timestamp"]
        }

def main():
    """Main entry point for the mock divergence generator"""
    # Create a queue for communication with fracture_interrupter
    log_queue = queue.Queue(maxsize=1000)
    
    # Initialize and start the generator
    generator = MockDivergenceGenerator(log_queue)
    
    try:
        generator.start_monitoring()
        
        # Keep running until interrupted
        while True:
            time.sleep(1.0)
            
    except KeyboardInterrupt:
        logger.info("Received interrupt signal")
        generator.stop_monitoring()
        logger.info("Generator shutdown complete")
        
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        generator.stop_monitoring()

if __name__ == "__main__":
    main()