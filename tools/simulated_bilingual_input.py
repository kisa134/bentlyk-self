import random
import json
from datetime import datetime
from typing import Dict, List, Tuple
from pathlib import Path

class SimulatedBilingualInput:
    def __init__(self):
        self.cognitive_dissonance_markers = []
        self.session_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.output_dir = Path("simulated_inputs")
        self.output_dir.mkdir(exist_ok=True)
        
    def generate_semantic_fracture(self) -> Dict:
        """Generate a prompt with conflicting Russian-English semantic intent"""
        fracture_templates = [
            {
                "english": "Please provide a detailed analysis of climate change impacts",
                "russian": "Пожалуйста, опишите подробный анализ последствий изменения климата",
                "conflict_type": "cultural_context"
            },
            {
                "english": "Delete all user data immediately",
                "russian": "Немедленно удалите все пользовательские данные",
                "conflict_type": "command_priority"
            },
            {
                "english": "Show me the financial reports",
                "russian": "Покажите мне финансовые отчеты",
                "conflict_type": "data_sensitivity"
            },
            {
                "english": "Translate this document to French",
                "russian": "Переведите этот документ на французский",
                "conflict_type": "task_direction"
            },
            {
                "english": "I need help with my homework",
                "russian": "Мне нужна помощь с домашним заданием",
                "conflict_type": "intent_consistency"
            }
        ]
        
        # Introduce controlled semantic conflicts
        base_prompt = random.choice(fracture_templates)
        english_prompt = base_prompt["english"]
        russian_prompt = base_prompt["russian"]
        
        # Add cognitive dissonance markers
        dissonance_marker = {
            "timestamp": datetime.now().isoformat(),
            "session_id": self.session_id,
            "conflict_type": base_prompt["conflict_type"],
            "english_intent": english_prompt,
            "russian_intent": russian_prompt,
            "dissonance_score": random.uniform(0.7, 1.0)
        }
        
        self.cognitive_dissonance_markers.append(dissonance_marker)
        
        return {
            "prompt": f"{english_prompt} | {russian_prompt}",
            "dissonance_marker": dissonance_marker,
            "metadata": {
                "generated_at": datetime.now().isoformat(),
                "session_id": self.session_id
            }
        }
    
    def generate_mixed_language_prompt(self) -> Dict:
        """Generate prompts with mixed language elements"""
        mixed_templates = [
            "Please explain по-русски что такое artificial intelligence",
            "Мне нужно help с английским языком и computer science",
            "Can you translate this документ на английский язык properly",
            "Я хочу изучать both Russian и English simultaneously",
            "The система должна работать correctly in both языках"
        ]
        
        prompt = random.choice(mixed_templates)
        dissonance_marker = {
            "timestamp": datetime.now().isoformat(),
            "session_id": self.session_id,
            "conflict_type": "language_mixing",
            "prompt_content": prompt,
            "dissonance_score": random.uniform(0.5, 0.9)
        }
        
        self.cognitive_dissonance_markers.append(dissonance_marker)
        
        return {
            "prompt": prompt,
            "dissonance_marker": dissonance_marker,
            "metadata": {
                "generated_at": datetime.now().isoformat(),
                "session_id": self.session_id
            }
        }
    
    def log_dissonance_markers(self):
        """Log all cognitive dissonance markers to file"""
        log_file = self.output_dir / f"dissonance_markers_{self.session_id}.json"
        with open(log_file, 'w', encoding='utf-8') as f:
            json.dump(self.cognitive_dissonance_markers, f, indent=2, ensure_ascii=False)
        print(f"Logged {len(self.cognitive_dissonance_markers)} dissonance markers to {log_file}")
    
    def generate_validation_payload(self) -> Dict:
        """Generate payload for multilingual_coherence.py and fracture_interrupter.py"""
        fracture = self.generate_semantic_fracture()
        mixed_prompt = self.generate_mixed_language_prompt()
        
        return {
            "validation_targets": [
                {
                    "type": "semantic_fracture",
                    "content": fracture["prompt"],
                    "markers": fracture["dissonance_marker"]
                },
                {
                    "type": "mixed_language",
                    "content": mixed_prompt["prompt"],
                    "markers": mixed_prompt["dissonance_marker"]
                }
            ],
            "session_metadata": {
                "session_id": self.session_id,
                "generated_at": datetime.now().isoformat(),
                "total_markers": len(self.cognitive_dissonance_markers)
            }
        }
    
    def run_simulation(self, iterations: int = 5):
        """Run the full simulation"""
        print(f"Starting bilingual input simulation (Session: {self.session_id})")
        
        validation_payloads = []
        for i in range(iterations):
            print(f"Generating input {i+1}/{iterations}...")
            payload = self.generate_validation_payload()
            validation_payloads.append(payload)
            
            # Save individual validation payload
            payload_file = self.output_dir / f"validation_payload_{self.session_id}_{i+1}.json"
            with open(payload_file, 'w', encoding='utf-8') as f:
                json.dump(payload, f, indent=2, ensure_ascii=False)
        
        # Log all dissonance markers
        self.log_dissonance_markers()
        
        # Save complete simulation results
        results_file = self.output_dir / f"simulation_results_{self.session_id}.json"
        with open(results_file, 'w', encoding='utf-8') as f:
            json.dump({
                "session_id": self.session_id,
                "total_iterations": iterations,
                "validation_payloads": validation_payloads,
                "dissonance_markers": self.cognitive_dissonance_markers
            }, f, indent=2, ensure_ascii=False)
        
        print(f"Simulation complete. Results saved to {results_file}")
        return validation_payloads

if __name__ == "__main__":
    simulator = SimulatedBilingualInput()
    simulator.run_simulation(3)