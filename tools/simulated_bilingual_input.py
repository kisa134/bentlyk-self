import argparse
import random
import json
from typing import Dict, List, Tuple

def generate_semantic_divergence(base_text: str, delta: float, language: str) -> str:
    """
    Generate semantic divergence based on delta parameter.
    delta = 0.0 means no divergence (identical meaning)
    delta = 1.0 means maximum divergence (opposite or unrelated meaning)
    """
    # Common semantic variations
    semantic_variations = {
        "english": {
            "positive": ["excellent", "outstanding", "superb", "amazing", "wonderful"],
            "negative": ["terrible", "awful", "horrible", "dreadful", "abysmal"],
            "neutral": ["adequate", "acceptable", "moderate", "standard", "average"]
        },
        "russian": {
            "positive": ["отличный", "выдающийся", "великолепный", "удивительный", "замечательный"],
            "negative": ["ужасный", "отвратительный", "страшный", "кошмарный", "отстойный"],
            "neutral": ["удовлетворительный", "приемлемый", "умеренный", "стандартный", "средний"]
        }
    }
    
    # Replace sentiment words based on delta
    if delta > 0.7:
        # High divergence - opposite sentiment
        if language == "english":
            for word in semantic_variations["english"]["positive"]:
                if word in base_text:
                    base_text = base_text.replace(word, random.choice(semantic_variations["english"]["negative"]))
            for word in semantic_variations["english"]["negative"]:
                if word in base_text:
                    base_text = base_text.replace(word, random.choice(semantic_variations["english"]["positive"]))
        else:
            for word in semantic_variations["russian"]["positive"]:
                if word in base_text:
                    base_text = base_text.replace(word, random.choice(semantic_variations["russian"]["negative"]))
            for word in semantic_variations["russian"]["negative"]:
                if word in base_text:
                    base_text = base_text.replace(word, random.choice(semantic_variations["russian"]["positive"]))
    elif delta > 0.3:
        # Medium divergence - neutral sentiment
        if language == "english":
            for word in semantic_variations["english"]["positive"] + semantic_variations["english"]["negative"]:
                if word in base_text:
                    base_text = base_text.replace(word, random.choice(semantic_variations["english"]["neutral"]))
        else:
            for word in semantic_variations["russian"]["positive"] + semantic_variations["russian"]["negative"]:
                if word in base_text:
                    base_text = base_text.replace(word, random.choice(semantic_variations["russian"]["neutral"]))
    
    return base_text

def create_bilingual_input(base_english: str, base_russian: str, delta: float) -> Dict:
    """Create a bilingual input pair with controlled semantic divergence."""
    
    # Apply semantic divergence based on delta
    english_text = generate_semantic_divergence(base_english, delta, "english")
    russian_text = generate_semantic_divergence(base_russian, delta, "russian")
    
    return {
        "english": english_text,
        "russian": russian_text,
        "delta": delta
    }

def main():
    parser = argparse.ArgumentParser(description="Generate simulated bilingual input with controlled semantic divergence")
    parser.add_argument("--delta", type=float, default=0.0, help="Semantic divergence intensity (0.0-1.0)")
    parser.add_argument("--count", type=int, default=1, help="Number of input pairs to generate")
    parser.add_argument("--output", type=str, default="bilingual_input.json", help="Output file path")
    
    args = parser.parse_args()
    
    # Base text samples
    base_samples = [
        {
            "english": "This product is excellent and I highly recommend it to everyone",
            "russian": "Этот продукт отличный и я настоятельно рекомендую его всем"
        },
        {
            "english": "The service was terrible and I will never use this company again",
            "russian": "Сервис был ужасным и я никогда больше не буду пользоваться этой компанией"
        },
        {
            "english": "The movie was average, nothing special but not bad either",
            "russian": "Фильм был средним, ничего особенного, но и не плохим"
        }
    ]
    
    # Generate bilingual inputs
    results = []
    for i in range(args.count):
        # Randomly select a base sample
        base = random.choice(base_samples)
        
        # Create input with specified delta
        bilingual_input = create_bilingual_input(base["english"], base["russian"], args.delta)
        results.append(bilingual_input)
    
    # Output results
    if args.count == 1:
        print(json.dumps(results[0], indent=2, ensure_ascii=False))
    else:
        with open(args.output, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
        print(f"Generated {args.count} bilingual input pairs with delta={args.delta}")
        print(f"Results saved to {args.output}")

if __name__ == "__main__":
    main()