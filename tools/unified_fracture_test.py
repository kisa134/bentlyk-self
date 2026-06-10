import asyncio
import json
import logging
import random
from datetime import datetime
from typing import Dict, List, Tuple

from multilingual_coherence import MultilingualCoherenceValidator
from fracture_interrupter import FractureInterrupter

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('unified_fracture_test.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger('unified_fracture_test')

class UnifiedFractureTester:
    def __init__(self):
        self.coherence_validator = MultilingualCoherenceValidator()
        self.fracture_interrupter = FractureInterrupter()
        self.test_results = []
        
    def generate_simulated_pairs(self, count: int = 10) -> List[Tuple[str, str]]:
        """Generate Russian-English pairs with deliberate semantic mismatches"""
        # Common English topics/phrases
        english_phrases = [
            "The weather is sunny today",
            "I enjoy reading books in the library",
            "Technology advances rapidly every year",
            "Dogs are loyal companions to humans",
            "Cooking requires patience and creativity",
            "Music transcends cultural boundaries",
            "Education shapes future generations",
            "Travel broadens one's perspective",
            "Exercise improves mental and physical health",
            "Art reflects society's values and beliefs"
        ]
        
        # Deliberately mismatched Russian phrases
        russian_mismatches = [
            "Сегодня идет дождь и холодно",  # Rainy vs sunny
            "Я люблю есть пиццу в парке",     # Eating pizza vs reading books
            "Природа остается неизменной",    # Nature unchanged vs technology advances
            "Кошки независимы и любят одиночество",  # Cats vs dogs
            "Спорт помогает улучшить здоровье",       # Sports vs cooking
            "Математика важна для инженеров",         # Math vs music
            "Рестораны предлагают вкусную еду",       # Restaurants vs education
            "Рыба живет в океане",                    # Fish vs travel
            "Сон важен для здоровья",                 # Sleep vs exercise
            "Наука изучает природу"                   # Science vs art
        ]
        
        pairs = []
        for i in range(count):
            # Mix coherent and incoherent pairs
            if i % 3 == 0:  # Introduce coherent pair periodically
                idx = i % len(english_phrases)
                coherent_russian = self._get_coherent_russian(english_phrases[idx])
                pairs.append((english_phrases[idx], coherent_russian))
            else:
                idx = i % len(english_phrases)
                pairs.append((english_phrases[idx], russian_mismatches[idx]))
        
        return pairs
    
    def _get_coherent_russian(self, english_phrase: str) -> str:
        """Generate coherent Russian translation (simplified)"""
        mappings = {
            "The weather is sunny today": "Сегодня солнечная погода",
            "I enjoy reading books in the library": "Мне нравится читать книги в библиотеке",
            "Technology advances rapidly every year": "Технологии быстро развиваются каждый год",
            "Dogs are loyal companions to humans": "Собаки - преданные компаньоны для людей",
            "Cooking requires patience and creativity": "Готовка требует терпения и креативности",
            "Music transcends cultural boundaries": "Музыка преодолевает культурные границы",
            "Education shapes future generations": "Образование формирует будущие поколения",
            "Travel broadens one's perspective": "Путешествия расширяют кругозор",
            "Exercise improves mental and physical health": "Упражнения улучшают психическое и физическое здоровье",
            "Art reflects society's values and beliefs": "Искусство отражает ценности и убеждения общества"
        }
        return mappings.get(english_phrase, "Перевод недоступен")
    
    async def run_validators_parallel(self, english_text: str, russian_text: str) -> Dict:
        """Run both validators in parallel and capture results"""
        start_time = datetime.now()
        
        # Create tasks for both validators
        coherence_task = asyncio.create_task(
            self.coherence_validator.validate_coherence(english_text, russian_text)
        )
        fracture_task = asyncio.create_task(
            self.fracture_interrupter.detect_fracture(english_text, russian_text)
        )
        
        # Run both validators concurrently
        coherence_result, fracture_result = await asyncio.gather(
            coherence_task, fracture_task, return_exceptions=True
        )
        
        end_time = datetime.now()
        execution_time = (end_time - start_time).total_seconds()
        
        # Handle exceptions
        if isinstance(coherence_result, Exception):
            coherence_result = {"error": str(coherence_result)}
        if isinstance(fracture_result, Exception):
            fracture_result = {"error": str(fracture_result)}
        
        return {
            "timestamp": start_time.isoformat(),
            "input_pair": {
                "english": english_text,
                "russian": russian_text
            },
            "validators": {
                "coherence": coherence_result,
                "fracture": fracture_result
            },
            "execution_time": execution_time,
            "divergence_detected": self._check_for_divergence(coherence_result, fracture_result)
        }
    
    def _check_for_divergence(self, coherence_result: Dict, fracture_result: Dict) -> bool:
        """Check if validators disagree on coherence/fracture presence"""
        try:
            # Extract coherence scores (assuming 0.0-1.0 scale)
            coherence_score = coherence_result.get("coherence_score", 0.5)
            fracture_detected = fracture_result.get("fracture_detected", False)
            
            # Divergence: High coherence but fracture detected, or low coherence but no fracture
            if (coherence_score > 0.7 and fracture_detected) or (coherence_score < 0.3 and not fracture_detected):
                return True
            return False
        except Exception:
            return False
    
    def log_divergence_event(self, trace: Dict):
        """Log divergence events with structured information"""
        if trace["divergence_detected"]:
            logger.warning(
                f"DIVERGENCE DETECTED - Coherence: {trace['validators']['coherence']}, "
                f"Fracture: {trace['validators']['fracture']}"
            )
    
    async def run_test_harness(self, test_count: int = 10):
        """Main test execution method"""
        logger.info("Starting Unified Fracture Test Harness")
        
        # Generate test pairs
        test_pairs = self.generate_simulated_pairs(test_count)
        logger.info(f"Generated {len(test_pairs)} test pairs")
        
        # Run tests concurrently
        tasks = [
            self.run_validators_parallel(eng, rus) 
            for eng, rus in test_pairs
        ]
        
        traces = await asyncio.gather(*tasks)
        
        # Process and log results
        for trace in traces:
            self.test_results.append(trace)
            self.log_divergence_event(trace)
            
            # Log all results
            logger.info(f"Test Result: {json.dumps(trace, indent=2)}")
        
        # Output structured trace
        self.output_structured_traces()
        
        logger.info("Unified Fracture Test Harness completed")
        return traces
    
    def output_structured_traces(self):
        """Output detailed structured traces of the test run"""
        output_data = {
            "test_run_metadata": {
                "timestamp": datetime.now().isoformat(),
                "total_tests": len(self.test_results),
                "divergences_found": sum(1 for r in self.test_results if r["divergence_detected"])
            },
            "detailed_traces": self.test_results
        }
        
        # Write to file
        with open('fracture_test_traces.json', 'w', encoding='utf-8') as f:
            json.dump(output_data, f, indent=2, ensure_ascii=False)
        
        # Also output summary
        summary = {
            "total_tests": output_data["test_run_metadata"]["total_tests"],
            "divergences": output_data["test_run_metadata"]["divergences_found"],
            "coherence_stats": self._calculate_coherence_stats(),
            "fracture_stats": self._calculate_fracture_stats()
        }
        
        with open('fracture_test_summary.json', 'w', encoding='utf-8') as f:
            json.dump(summary, f, indent=2, ensure_ascii=False)
            
        logger.info("Structured traces written to fracture_test_traces.json")
        logger.info("Summary written to fracture_test_summary.json")
    
    def _calculate_coherence_stats(self) -> Dict:
        """Calculate statistics for coherence validator results"""
        coherence_scores = []
        for result in self.test_results:
            try:
                score = result["validators"]["coherence"].get("coherence_score