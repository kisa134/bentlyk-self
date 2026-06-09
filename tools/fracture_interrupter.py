import os
import json
import time
import traceback
from functools import wraps
from typing import Any, Callable, Dict, Tuple

FRACTURE_DIR = "fractures"
os.makedirs(FRACTURE_DIR, exist_ok=True)

def log_semantic_fracture(func: Callable) -> Callable:
    @wraps(func)
    def wrapper(*args, **kwargs) -> Any:
        # Extract input phrases (assuming first two args are_ru, en_phrase)
        if len(args) >= 2:
            ru_phrase, en_phrase = args[0], args[1]
        else:
            ru_phrase = kwargs.get('ru_phrase', 'N/A')
            en_phrase = kwargs.get('en_phrase', 'N/A')
        
        # Capture pre-resolution state
        pre_resolution = {
            "timestamp": time.time(),
            "function": func.__name__,
            "input_phrases": {
                "russian": ru_phrase,
                "english": en_phrase
            },
            "stack_context": traceback.format_stack()[:-1]
        }
        
        try:
            # Execute semantic resolution
            result = func(*args, **kwargs)
            
            # Capture post-resolution state
            post_resolution = {
                "unified_meaning": result,
                "delta_analysis": {
                    "language_drift": len(str(ru_phrase)) - len(str(en_phrase)),
                    "resolution_confidence": getattr(result, 'confidence', 'N/A')
                }
            }
            
            # Combine and log fracture analysis
            fracture_record = {**pre_resolution, **post_resolution}
            timestamp = int(time.time())
            filename = f"{FRACTURE_DIR}/fracture_{func.__name__}_{timestamp}.json"
            
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(fracture_record, f, ensure_ascii=False, indent=2)
                
        except Exception as e:
            error_record = {
                **pre_resolution,
                "error": str(e),
                "traceback": traceback.format_exc()
            }
            timestamp = int(time.time())
            filename = f"{FRACTURE_DIR}/fracture_error_{func.__name__}_{timestamp}.json"
            
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(error_record, f, ensure_ascii=False, indent=2)
            raise
            
        return result
    return wrapper