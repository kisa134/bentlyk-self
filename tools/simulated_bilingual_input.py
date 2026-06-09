import argparse
import random
import time
import json
from typing import List, Tuple, Dict, Any
from collections import defaultdict

class SimulatedBilingualInput:
    def __init__(self, stress_test: bool = False):
        self.stress_test = stress_test
        self.exchange_count = 0
        self.mismatch_interval = 0
        self.next_mismatch = 0
        self.validator_states = {}
        self.trigger_phrases = []
        self.repair_start_time = None
        self.log_data = []
        self._initialize_mismatch_triggers()
        self._reset_interval()

    def _initialize_mismatch_triggers(self):
        """Initialize semantic mismatch trigger phrases"""
        self.mismatch_pairs = [
            ("good morning", "доброе утро"),
            ("how are you", "как дела"),
            ("thank you", "спасибо"),
            ("please", "пожалуйста"),
            ("sorry", "извините"),
            ("yes", "да"),
            ("no", "нет"),
            ("hello", "привет"),
            ("goodbye", "до свидания"),
            ("excuse me", "простите"),
            ("I understand", "я понимаю"),
            ("I don't know", "я не знаю"),
            ("what time is it", "который час"),
            ("where is the bathroom", "где туалет"),
            ("how much does it cost", "сколько это стоит")
        ]
        
        # Escalated versions for stress testing
        self.stress_mismatch_pairs = [
            ("good morning everyone", "добрый вечер всем"),
            ("how are you today", "как погода"),
            ("thank you very much", "большое спасибо"),
            ("please hurry", "пожалуйста медленно"),
            ("sorry about that", "извините за это"),
            ("yes absolutely", "нет конечно"),
            ("no problem at all", "большая проблема"),
            ("hello friend", "привет незнакомец"),
            ("goodbye forever", "до скорого"),
            ("excuse me sir", "простите девушка"),
            ("I completely understand", "я совсем не понимаю"),
            ("I definitely know", "я точно не знаю"),
            ("what time is it exactly", "который день сегодня"),
            ("where is the nearest bathroom", "где находится кухня"),
            ("how much does this expensive item cost", "сколько стоит это дешево")
        ]

    def _reset_interval(self):
        """Reset the interval between mismatches"""
        self.mismatch_interval = random.randint(3, 5)
        self.next_mismatch = self.exchange_count + self.mismatch_interval

    def _inject_semantic_mismatch(self, english: str, russian: str) -> Tuple[str, str]:
        """Inject a controlled semantic mismatch"""
        if self.stress_test and random.random() < 0.3:
            # Use escalated mismatches for stress testing
            mismatch_pair = random.choice(self.stress_mismatch_pairs)
        else:
            mismatch_pair = random.choice(self.mismatch_pairs)
            
        self.trigger_phrases.append(mismatch_pair)
        return mismatch_pair[0], mismatch_pair[1]

    def process_exchange(self, english_input: str, russian_input: str) -> Tuple[str, str]:
        """Process a bilingual exchange, potentially injecting mismatches"""
        self.exchange_count += 1
        
        # Check if we should inject a mismatch
        if self.exchange_count >= self.next_mismatch:
            original_english = english_input
            original_russian = russian_input
            english_input, russian_input = self._inject_semantic_mismatch(english_input, russian_input)
            
            # Log the mismatch event
            self._log_mismatch(original_english, original_russian, english_input, russian_input)
            
            # Reset interval for next mismatch
            self._reset_interval()
            
        return english_input, russian_input

    def _log_mismatch(self, original_eng: str, original_rus: str, modified_eng: str, modified_rus: str):
        """Log mismatch details"""
        log_entry = {
            "timestamp": time.time(),
            "exchange_count": self.exchange_count,
            "original_english": original_eng,
            "original_russian": original_rus,
            "modified_english": modified_eng,
            "modified_russian": modified_rus,
            "validator_states_pre": dict(self.validator_states),
            "trigger_phrase_pair": (modified_eng, modified_rus)
        }
        self.log_data.append(log_entry)
        self.repair_start_time = time.time()

    def update_validator_state(self, validator_name: str, state: Any):
        """Update validator state for logging"""
        self.validator_states[validator_name] = state

    def log_coherence_repair(self, repair_latency: float = None):
        """Log coherence repair completion"""
        if self.log_data and "repair_latency" not in self.log_data[-1]:
            if repair_latency is None and self.repair_start_time:
                repair_latency = time.time() - self.repair_start_time
            
            if repair_latency is not None:
                self.log_data[-1]["repair_latency"] = repair_latency
                self.log_data[-1]["validator_states_post"] = dict(self.validator_states)
                self.repair_start_time = None

    def get_log_summary(self) -> Dict[str, Any]:
        """Get summary of logged events"""
        total_mismatches = len([entry for entry in self.log_data if "trigger_phrase_pair" in entry])
        avg_repair_latency = 0
        if total_mismatches > 0:
            total_latency = sum(entry.get("repair_latency", 0) for entry in self.log_data if "repair_latency" in entry)
            avg_repair_latency = total_latency / total_mismatches if total_mismatches > 0 else 0
            
        return {
            "total_exchanges": self.exchange_count,
            "total_mismatches": total_mismatches,
            "average_repair_latency": avg_repair_latency,
            "mismatch_rate": total_mismatches / self.exchange_count if self.exchange_count > 0 else 0
        }

    def save_logs(self, filename: str):
        """Save logs to file"""
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(self.log_data, f, indent=2, ensure_ascii=False)

def main():
    parser = argparse.ArgumentParser(description="Simulated Bilingual Input with Controlled Semantic Mismatches")
    parser.add_argument("--stress-test", action="store_true", help="Enable stress testing with escalated mismatches")
    parser.add_argument("--log-file", type=str, default="bilingual_simulation_log.json", help="Log file path")
    parser.add_argument("--exchanges", type=int, default=20, help="Number of exchanges to simulate")
    
    args = parser.parse_args()
    
    simulator = SimulatedBilingualInput(stress_test=args.stress_test)
    
    # Sample conversation data
    sample_exchanges = [
        ("Hello there", "Привет там"),
        ("How are you doing today?", "Как ты сегодня поживаешь?"),
        ("Thank you for your help", "Спасибо за вашу помощь"),
        ("Please pass the salt", "Пожалуйста передайте соль"),
        ("Sorry for being late", "Извините за опоздание"),
        ("Yes, I agree with you", "Да, я согласен с вами"),
        ("No, that's not right", "Нет, это неправильно"),
        ("Good morning everyone", "Доброе утро всем"),
        ("Excuse me, where is the exit?", "Простите, где выход?"),
        ("I understand the situation", "Я понимаю ситуацию"),
        ("I don't know the answer", "Я не знаю ответ"),
        ("What time is it now?", "Который час сейчас?"),
        ("Where is the bathroom located?", "Где находится туалет?"),
        ("How much does this cost?", "Сколько это стоит?"),
        ("Have a nice day", "Хорошего дня"),
        ("See you later", "Увидимся позже"),
        ("Good night", "Спокойной ночи"),
        ("Congratulations on your success", "Поздравляем с вашим успехом"),
        ("Happy birthday", "С днем рождения"),
        ("Merry Christmas", "С Рождеством")
    ]
    
    # Simulate exchanges
    for i in range(min(args.exchanges, len(sample_exchanges))):
        english, russian = sample_exchanges[i]
        
        # Simulate validator states
        simulator.update_validator_state("semantic_coherence", random.choice(["high", "medium", "low"]))
        simulator.update_validator_state("language_detection", "confident")
        simulator.update_validator_state("translation_quality", random.uniform(0.7, 1.0))
        
        # Process exchange with potential mismatch injection
        processed_english, processed_russian = simulator.process_exchange(english, russian)
        
        # Simulate processing delay
        time.sleep(0.1)
        
        # Simulate repair completion with random latency
        if simulator.repair_start_time:
            repair_latency = random.uniform(0