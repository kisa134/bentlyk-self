import json
import logging
import os
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent))

from tools.multilingual_coherence import MultilingualCoherenceDetector
from tools.runtime_validator import RuntimeValidator

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('fracture_interrupter.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger('fracture_interrupter')

class FractureInterrupter:
    """Integrates with runtime validation flow to detect semantic divergence during input simulation."""
    
    def __init__(self, config_path: Optional[str] = None):
        """Initialize the fracture interrupter with configuration."""
        self.config = self._load_config(config_path)
        self.coherence_detector = MultilingualCoherenceDetector()
        self.runtime_validator = RuntimeValidator()
        self.divergence_traces: List[Dict[str, Any]] = []
        
    def _load_config(self, config_path: Optional[str]) -> Dict[str, Any]:
        """Load configuration from file or use defaults."""
        default_config = {
            'detection_threshold': 0.7,
            'validation_depth': 3,
            'trace_output_dir': './traces',
            'languages': ['en', 'es', 'fr', 'de', 'zh'],
            'simulation_steps': 100
        }
        
        if not config_path or not os.path.exists(config_path):
            logger.warning("No config file found, using defaults")
            return default_config
            
        try:
            with open(config_path, 'r') as f:
                config = json.load(f)
            # Merge with defaults
            merged_config = default_config.copy()
            merged_config.update(config)
            return merged_config
        except Exception as e:
            logger.error(f"Error loading config: {e}, using defaults")
            return default_config
    
    def simulate_controlled_input(self, base_input: str, steps: int = 100) -> List[str]:
        """
        Generate controlled variations of input for simulation.
        This is a simplified implementation - in practice this would be more sophisticated.
        """
        variations = [base_input]
        words = base_input.split()
        
        # Generate simple variations
        for i in range(min(steps, len(words))):
            # Add/remove words, change order, etc.
            if i < len(words):
                # Remove one word
                modified = words.copy()
                modified.pop(i)
                variations.append(' '.join(modified))
                
                # Add a modifier
                modified = words.copy()
                modified.insert(i, "additional")
                variations.append(' '.join(modified))
        
        return variations[:steps]
    
    def detect_semantic_divergence(self, 
                                 original_text: str, 
                                 modified_text: str,
                                 languages: List[str]) -> Dict[str, Any]:
        """
        Detect semantic divergence between original and modified texts across languages.
        """
        try:
            # Check coherence in multiple languages
            coherence_results = {}
            divergence_detected = False
            divergence_details = []
            
            for lang in languages:
                original_coherence = self.coherence_detector.analyze_coherence(original_text, lang)
                modified_coherence = self.coherence_detector.analyze_coherence(modified_text, lang)
                
                coherence_results[lang] = {
                    'original': original_coherence,
                    'modified': modified_coherence
                }
                
                # Check for significant divergence
                if original_coherence['coherence_score'] > 0 and modified_coherence['coherence_score'] > 0:
                    divergence_ratio = abs(original_coherence['coherence_score'] - modified_coherence['coherence_score'])
                    if divergence_ratio > self.config['detection_threshold']:
                        divergence_detected = True
                        divergence_details.append({
                            'language': lang,
                            'divergence_ratio': divergence_ratio,
                            'original_score': original_coherence['coherence_score'],
                            'modified_score': modified_coherence['coherence_score']
                        })
            
            return {
                'divergence_detected': divergence_detected,
                'details': divergence_details,
                'coherence_results': coherence_results,
                'original_text': original_text,
                'modified_text': modified_text
            }
            
        except Exception as e:
            logger.error(f"Error in semantic divergence detection: {e}")
            return {
                'divergence_detected': False,
                'error': str(e)
            }
    
    def run_validation_flow(self, input_text: str) -> Dict[str, Any]:
        """
        Run the complete validation flow with semantic divergence detection.
        """
        logger.info(f"Starting validation flow for input: {input_text[:50]}...")
        
        # Generate controlled input variations
        variations = self.simulate_controlled_input(
            input_text, 
            self.config['simulation_steps']
        )
        
        # Track validation results
        validation_results = []
        divergence_count = 0
        
        for i, variation in enumerate(variations):
            try:
                # Run runtime validation
                validation_result = self.runtime_validator.validate_input(variation)
                
                # Check for semantic divergence from original
                if i > 0:  # Skip original input
                    divergence_result = self.detect_semantic_divergence(
                        variations[0],  # Original
                        variation,      # Modified
                        self.config['languages']
                    )
                    
                    if divergence_result['divergence_detected']:
                        divergence_count += 1
                        # Log divergence trace
                        trace = {
                            'step': i,
                            'original_input': variations[0],
                            'modified_input': variation,
                            'divergence_result': divergence_result,
                            'validation_result': validation_result
                        }
                        self.divergence_traces.append(trace)
                        logger.warning(f"Semantic divergence detected at step {i}")
                
                validation_results.append({
                    'step': i,
                    'input': variation,
                    'validation': validation_result
                })
                
            except Exception as e:
                logger.error(f"Error in validation flow step {i}: {e}")
                validation_results.append({
                    'step': i,
                    'input': variation,
                    'error': str(e)
                })
        
        # Summary
        summary = {
            'total_steps': len(variations),
            'divergence_count': divergence_count,
            'validation_passed': sum(1 for r in validation_results if r.get('validation', {}).get('valid', False)),
            'completion_time': len(variations)  # Simplified
        }
        
        logger.info(f"Validation flow completed. Divergences: {divergence_count}")
        return {
            'summary': summary,
            'results': validation_results,
            'divergence_traces': self.divergence_traces
        }
    
    def save_divergence_traces(self, output_dir: Optional[str] = None) -> str:
        """Save divergence traces to JSON file."""
        if not output_dir:
            output_dir = self.config['trace_output_dir']
        
        os.makedirs(output_dir, exist_ok=True)
        trace_file = os.path.join(output_dir, 'divergence_traces.json')
        
        try:
            with open(trace_file, 'w') as f:
                json.dump(self.divergence_traces, f, indent=2, default=str)
            logger.info(f"Divergence traces saved to {trace_file}")
            return trace_file
        except Exception as e:
            logger.error(f"Error saving divergence traces: {e}")
            return ""
    
    def process_inputs(self, inputs: List[str]) -> List[Dict[str, Any]]:
        """Process multiple inputs through the validation flow."""
        results = []
        for i, input_text in enumerate(inputs):
            logger.info(f"Processing input {i+1}/{len(inputs)}")
            result = self.run_validation_flow(input_text)
            results.append(result)
        return results

def main():
    """Main entry point for the fracture interrupter."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Fracture Interrupter - Semantic Divergence Detector')
    parser.add_argument('--input', '-i', type=str, help='Input text to analyze')
    parser.add_argument('--input-file', '-f', type=str, help='File containing inputs (one per line)')
    parser.add_argument('--config', '-c', type=str, help='Configuration file path')
    parser.add_argument('--output-dir', '-o', type=str, help='Output directory for traces')
    
    args = parser.parse_args()
    
    # Initialize interrupter
    interrupter = FractureInterrupter(args.config)
    
    # Determine inputs
    inputs = []
    if args.input:
        inputs = [args.input]
    elif args.input_file:
        try:
            with open(args.input_file, 'r') as f:
                inputs = [line.strip() for line in f if line.strip()]
        except Exception as e:
            logger.error(f"Error reading input file: {e}")
            return 1
    else:
        logger.error("Either --input or --input-file must be specified")
        return 1
    
    # Process inputs
    logger.info(f"Processing {len(inputs)} inputs")
    results = interrupter.process_inputs(inputs)
    
    # Save traces
    if interrupter.divergence_traces:
        trace_file = interrupter.save_divergence_traces(args.output_dir)