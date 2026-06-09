import sys
import os
import traceback
import json
from typing import Dict, List, Any, Optional

# Add parent directory to path to import coherence_runtime_instrument
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from coherence_runtime_instrument import CoherenceRuntime, SemanticFractureException
except ImportError:
    print("Error: Could not import coherence_runtime_instrument module")
    sys.exit(1)

class ForcedFractureTest:
    def __init__(self):
        self.runtime = CoherenceRuntime()
        self.diagnostic_data = {}
        
    def execute_ambiguous_russian_sentence(self, russian_text: str) -> Optional[str]:
        """
        Execute a Russian sentence with deliberate ambiguity and capture any semantic fracture.
        Returns the English interpretation if successful, None if fractured.
        """
        try:
            english_output = self.runtime.process_russian_input(russian_text)
            return english_output
        except SemanticFractureException as e:
            self.capture_fracture_diagnostics(russian_text, e)
            return None
        except Exception as e:
            print(f"Unexpected error during processing: {e}")
            traceback.print_exc()
            return None
            
    def capture_fracture_diagnostics(self, russian_input: str, fracture_exception: SemanticFractureException):
        """Capture comprehensive diagnostics when semantic fracture occurs."""
        self.diagnostic_data = {
            "original_russian_input": russian_input,
            "failed_english_interpretation": getattr(fracture_exception, 'partial_translation', ''),
            "point_of_divergence": {
                "token_index": getattr(fracture_exception, 'fracture_token_index', -1),
                "token_value": getattr(fracture_exception, 'fracture_token', ''),
                "semantic_context": getattr(fracture_exception, 'fracture_context', '')
            },
            "semantic_weights_at_fracture": getattr(fracture_exception, 'semantic_weights', {}),
            "full_divergence_stack_trace": traceback.format_exc(),
            "fracture_reason": str(fracture_exception)
        }
        
    def output_diagnostic_data(self):
        """Output structured diagnostic data in JSON format."""
        if self.diagnostic_data:
            print(json.dumps(self.diagnostic_data, indent=2, ensure_ascii=False))
        else:
            print("No fracture diagnostics captured.")

def main():
    # Create test harness instance
    test_harness = ForcedFractureTest()
    
    # Example Russian sentences with deliberate ambiguity
    ambiguous_sentences = [
        # Homonym example: "банк" can mean "bank" (financial institution) or "bench"
        "Он сидел на банке у реки, думая о финансах.",
        
        # Syntactic ambiguity example with case parsing
        "Я видел человека с telescope на горе.",
        
        # Another homonym example: "ключ" can mean "key" or "spring" (water source)  
        "Она нашла ключ в лесу и открыла тайну."
    ]
    
    for i, sentence in enumerate(ambiguous_sentences, 1):
        print(f"\n=== Test Case {i} ===")
        print(f"Russian input: {sentence}")
        
        result = test_harness.execute_ambiguous_russian_sentence(sentence)
        
        if result is None:
            print("SEMANTIC FRACTURE DETECTED")
            test_harness.output_diagnostic_data()
        else:
            print(f"Successful translation: {result}")
            
        # Reset diagnostics for next test
        test_harness.diagnostic_data = {}

if __name__ == "__main__":
    main()