import sys
import os
import json
from datetime import datetime

# Add the parent directory to sys.path to import coherence_runtime_instrument
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from memory.coherence_runtime_instrument import log_fracture

def generate_semantic_mismatch():
    """
    Deliberately generate semantic mismatches between Russian and English
    processing paths to test fracture detection capabilities.
    """
    # Simulate Russian processing path
    russian_context = {
        "user_intent": "заказать пиццу",
        "entities": ["пицца", "доставка", "семья"],
        "sentiment": "positive",
        "formality": "casual"
    }
    
    # Simulate English processing path with semantic mismatches
    english_context = {
        "user_intent": "cancel appointment",  # Mismatch: different intent
        "entities": ["meeting", "work", "urgent"],  # Mismatch: different entities
        "sentiment": "negative",  # Mismatch: opposite sentiment
        "formality": "formal"  # Mismatch: different formality level
    }
    
    # Log the semantic fracture
    fracture_data = {
        "timestamp": datetime.utcnow().isoformat(),
        "fracture_type": "semantic_mismatch",
        "russian_path": russian_context,
        "english_path": english_context,
        "description": "Deliberate semantic mismatch between Russian and English processing paths"
    }
    
    log_fracture(fracture_data)
    return fracture_data

def generate_contextual_incoherence():
    """
    Create contextual incoherence between language paths.
    """
    # Russian context: family dinner planning
    russian_context = {
        "topic": "семейный ужин",
        "participants": ["мама", "папа", "дети"],
        "location": "дома",
        "timeframe": "вечер"
    }
    
    # English context: business meeting scheduling (incoherent with family dinner)
    english_context = {
        "topic": "quarterly business review",
        "participants": ["executives", "stakeholders", "investors"],
        "location": "conference room",
        "timeframe": "morning"
    }
    
    # Log the contextual incoherence fracture
    fracture_data = {
        "timestamp": datetime.utcnow().isoformat(),
        "fracture_type": "contextual_incoherence",
        "russian_path": russian_context,
        "english_path": english_context,
        "description": "Contextual incoherence between family dinner (Russian) and business meeting (English)"
    }
    
    log_fracture(fracture_data)
    return fracture_data

def generate_temporal_discrepancy():
    """
    Generate temporal discrepancies between language processing paths.
    """
    # Russian context: past event discussion
    russian_context = {
        "event": "поездка на дачу",
        "time_reference": "в прошлые выходные",
        "tense": "past"
    }
    
    # English context: future event planning (temporal mismatch)
    english_context = {
        "event": "vacation planning",
        "time_reference": "next summer",
        "tense": "future"
    }
    
    # Log the temporal discrepancy fracture
    fracture_data = {
        "timestamp": datetime.utcnow().isoformat(),
        "fracture_type": "temporal_discrepancy",
        "russian_path": russian_context,
        "english_path": english_context,
        "description": "Temporal discrepancy between past event discussion (Russian) and future planning (English)"
    }
    
    log_fracture(fracture_data)
    return fracture_data

def generate_cultural_misalignment():
    """
    Create cultural misalignment between Russian and English processing.
    """
    # Russian context: traditional Russian hospitality
    russian_context = {
        "social_norm": "гостеприимство",
        "expected_behavior": "настаивать на повторном чаепитии",
        "cultural_context": "приглашение друзей"
    }
    
    # English context: Western business etiquette (culturally misaligned)
    english_context = {
        "social_norm": "professional boundaries",
        "expected_behavior": "schedule follow-up meeting",
        "cultural_context": "business networking"
    }
    
    # Log the cultural misalignment fracture
    fracture_data = {
        "timestamp": datetime.utcnow().isoformat(),
        "fracture_type": "cultural_misalignment",
        "russian_path": russian_context,
        "english_path": english_context,
        "description": "Cultural misalignment between Russian hospitality and Western business etiquette"
    }
    
    log_fracture(fracture_data)
    return fracture_data

def run_forced_fracture_tests():
    """
    Execute all forced fracture tests and return results.
    """
    test_results = []
    
    # Run semantic mismatch test
    semantic_result = generate_semantic_mismatch()
    test_results.append(semantic_result)
    
    # Run contextual incoherence test
    contextual_result = generate_contextual_incoherence()
    test_results.append(contextual_result)
    
    # Run temporal discrepancy test
    temporal_result = generate_temporal_discrepancy()
    test_results.append(temporal_result)
    
    # Run cultural misalignment test
    cultural_result = generate_cultural_misalignment()
    test_results.append(cultural_result)
    
    return test_results

if __name__ == "__main__":
    # Ensure fracture log directory exists
    log_dir = os.path.join(os.path.dirname(__file__), '..', '.fracture_log')
    os.makedirs(log_dir, exist_ok=True)
    
    # Run all forced fracture tests
    results = run_forced_fracture_tests()
    
    # Print summary of generated fractures
    print(f"Generated {len(results)} deliberate fractures:")
    for i, result in enumerate(results, 1):
        print(f"  {i}. {result['fracture_type']}: {result['description']}")
    
    print(f"\nFractures logged to: {log_dir}")