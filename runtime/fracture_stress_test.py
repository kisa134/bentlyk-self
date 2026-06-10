import os
import sys
import time
import json
import random
import threading
import psutil
import gc
from collections import defaultdict
from datetime import datetime
from typing import Dict, List, Tuple, Any
import logging

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from runtime.fracture_interrupter import FractureInterrupter
from runtime.multilingual_coherence import MultilingualCoherence

class FractureStressTest:
    def __init__(self, log_dir: str = "logs"):
        self.log_dir = log_dir
        self.setup_logging()
        self.fracture_interrupter = FractureInterrupter()
        self.coherence_analyzer = MultilingualCoherence()
        self.memory_stats = defaultdict(list)
        self.failure_log = []
        self.test_running = False
        self.test_thread = None
        
        # Ensure log directory exists
        os.makedirs(log_dir, exist_ok=True)
        
    def setup_logging(self):
        """Setup logging configuration"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(os.path.join(self.log_dir, 'fracture_stress_test.log')),
                logging.StreamHandler(sys.stdout)
            ]
        )
        self.logger = logging.getLogger(__name__)
        
    def generate_russian_english_divergence(self, complexity: int = 5) -> Tuple[str, str]:
        """
        Generate controlled Russian-English input divergence scenarios
        """
        # Common phrases with semantic divergence
        divergence_patterns = [
            ("Hello, how are you?", "Привет, как дела?"),
            ("The weather is nice today", "Погода сегодня хорошая"),
            ("I need to go to the store", "Мне нужно пойти в магазин"),
            ("What time is it?", "Который час?"),
            ("Thank you very much", "Большое спасибо"),
            ("This is a test", "Это тест"),
            ("Please wait here", "Пожалуйста, подождите здесь"),
            ("I don't understand", "Я не понимаю"),
            ("Can you help me?", "Вы можете мне помочь?"),
            ("Where is the bathroom?", "Где туалет?"),
            ("The book is on the table", "Книга на столе"),
            ("I am learning Russian", "Я изучаю русский язык"),
            ("This system is complex", "Эта система сложная"),
            ("Data processing failed", "Обработка данных не удалась"),
            ("Memory allocation error", "Ошибка выделения памяти")
        ]
        
        # Add complexity by concatenating multiple phrases
        selected_phrases = random.sample(divergence_patterns, min(complexity, len(divergence_patterns)))
        
        english_parts = []
        russian_parts = []
        
        for en, ru in selected_phrases:
            # Introduce controlled divergence by modifying some phrases
            if random.random() > 0.7:  # 30% chance of divergence
                # Add noise or modify phrases
                en = self._add_divergence_noise(en)
                ru = self._add_divergence_noise(ru)
                
            english_parts.append(en)
            russian_parts.append(ru)
            
        english_text = " ".join(english_parts)
        russian_text = " ".join(russian_parts)
        
        return english_text, russian_text
    
    def _add_divergence_noise(self, text: str) -> str:
        """Add controlled noise to create divergence"""
        if random.random() > 0.5:
            # Add extra words
            noise_words = ["very", "extremely", "quite", "rather", "somewhat"]
            words = text.split()
            insert_pos = random.randint(0, len(words))
            words.insert(insert_pos, random.choice(noise_words))
            return " ".join(words)
        else:
            # Remove words
            words = text.split()
            if len(words) > 2:
                remove_pos = random.randint(0, len(words)-1)
                words.pop(remove_pos)
                return " ".join(words)
        return text
    
    def instrument_memory(self) -> Dict[str, Any]:
        """Instrument current memory allocation patterns"""
        process = psutil.Process(os.getpid())
        memory_info = process.memory_info()
        
        gc_stats = gc.get_stats()
        
        return {
            'timestamp': datetime.now().isoformat(),
            'memory_rss': memory_info.rss,
            'memory_vms': memory_info.vms,
            'memory_percent': process.memory_percent(),
            'gc_collections': len(gc_stats) if gc_stats else 0,
            'active_threads': threading.active_count()
        }
    
    def log_memory_stats(self):
        """Log current memory statistics"""
        stats = self.instrument_memory()
        for key, value in stats.items():
            self.memory_stats[key].append(value)
        return stats
    
    def run_fracture_test(self, iterations: int = 100, complexity: int = 5):
        """
        Run the fracture stress test
        """
        self.test_running = True
        self.logger.info(f"Starting fracture stress test with {iterations} iterations")
        
        for i in range(iterations):
            if not self.test_running:
                break
                
            try:
                # Generate divergent input
                english_input, russian_input = self.generate_russian_english_divergence(complexity)
                
                # Log memory before processing
                pre_memory = self.log_memory_stats()
                
                # Process with fracture interrupter
                fracture_result = self.fracture_interrupter.process_divergent_input(
                    english_input, russian_input
                )
                
                # Process with coherence analyzer
                coherence_result = self.coherence_analyzer.analyze_coherence(
                    english_input, russian_input
                )
                
                # Log memory after processing
                post_memory = self.log_memory_stats()
                
                # Check for failures
                if not fracture_result.get('success', True) or not coherence_result.get('coherent', True):
                    failure_record = {
                        'iteration': i,
                        'timestamp': datetime.now().isoformat(),
                        'english_input': english_input,
                        'russian_input': russian_input,
                        'fracture_result': fracture_result,
                        'coherence_result': coherence_result,
                        'memory_before': pre_memory,
                        'memory_after': post_memory
                    }
                    self.failure_log.append(failure_record)
                    self.logger.warning(f"Failure detected at iteration {i}")
                    
                # Periodic memory logging
                if i % 10 == 0:
                    self.logger.info(f"Completed iteration {i}/{iterations}")
                    current_memory = self.instrument_memory()
                    self.logger.info(f"Current memory usage: {current_memory['memory_percent']:.2f}%")
                    
            except Exception as e:
                self.logger.error(f"Error during iteration {i}: {str(e)}")
                failure_record = {
                    'iteration': i,
                    'timestamp': datetime.now().isoformat(),
                    'error': str(e),
                    'english_input': english_input if 'english_input' in locals() else '',
                    'russian_input': russian_input if 'russian_input' in locals() else ''
                }
                self.failure_log.append(failure_record)
                
        self.test_running = False
        self.logger.info("Fracture stress test completed")
        
    def start_test_threaded(self, iterations: int = 100, complexity: int = 5):
        """Start the test in a separate thread"""
        if self.test_thread and self.test_thread.is_alive():
            self.logger.warning("Test already running")
            return
            
        self.test_thread = threading.Thread(
            target=self.run_fracture_test,
            args=(iterations, complexity)
        )
        self.test_thread.start()
        self.logger.info("Started fracture stress test in background thread")
        
    def stop_test(self):
        """Stop the running test"""
        self.test_running = False
        if self.test_thread:
            self.test_thread.join(timeout=5)
        self.logger.info("Fracture stress test stopped")
        
    def get_test_status(self) -> Dict[str, Any]:
        """Get current test status"""
        return {
            'running': self.test_running,
            'failures_detected': len(self.failure_log),
            'memory_stats': dict(self.memory_stats),
            'active_thread': self.test_thread.is_alive() if self.test_thread else False
        }
    
    def save_results(self, filename: str = None):
        """Save test results to file"""
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"fracture_test_results_{timestamp}.json"
            
        results = {
            'test_config': {
                'timestamp': datetime.now().isoformat(),
                'total_failures': len(self.failure_log)
            },
            'failures': self.failure_log,
            'memory_stats': dict(self.memory_stats)
        }
        
        filepath = os.path.join(self.log_dir, filename)
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
            
        self.logger.info(f"Results saved to {filepath}")
        return filepath

def main():
    """Main function to run the fracture stress test