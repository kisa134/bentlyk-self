import time
from typing import Dict, Any

# Global state tracking
_last_full_reflection = 0.0
_CRITICAL_REFLECTION_DEPTH = 0.3
_DEFAULT_ENERGY_THRESHOLD = 0.3
_COHERENCE_DEPTH_THRESHOLD = 0.7
_MIN_COOLDOWN_SECONDS = 300  # 5 minutes

def adjust_reflection(energy: float, coherence: float) -> Dict[str, Any]:
    """
    Dynamically adjust reflection frequency and depth based on energy and coherence states.
    
    Args:
        energy: Current energy level (0.0-1.0)
        coherence: Current coherence level (0.0-1.0)
        
    Returns:
        Dict containing frequency_sec (int) and depth (float) parameters
    """
    global _last_full_reflection
    
    current_time = time.time()
    
    # Critical energy handling - only allow minimal reflection
    if energy < _DEFAULT_ENERGY_THRESHOLD:
        # Check cooldown for full introspection when energy is low
        if energy < 0.5 and (current_time - _last_full_reflection) < _MIN_COOLDOWN_SECONDS:
            return {
                "frequency_sec": 180,  # 3 minutes for minimal processing
                "depth": _CRITICAL_REFLECTION_DEPTH
            }
        else:
            # Allow full processing but with restrictions
            _last_full_reflection = current_time
            return {
                "frequency_sec": 120,  # 2 minutes
                "depth": max(0.4, coherence * 0.7)  # Reduced depth even at high coherence
            }
    
    # Normal operation - determine depth based on coherence
    if coherence < _COHERENCE_DEPTH_THRESHOLD:
        depth = 0.5 + (coherence * 0.4)  # Scale from 0.5 to ~0.78
    else:
        depth = 0.8 + (coherence * 0.2)  # Scale from 0.8 to 1.0
    
    # Set frequency based on energy - higher energy allows more frequent reflection
    if energy > 0.8:
        frequency_sec = 30   # Every 30 seconds when highly energized
    elif energy > 0.6:
        frequency_sec = 60   # Every minute
    elif energy > 0.4:
        frequency_sec = 90   # Every 90 seconds
    else:
        frequency_sec = 120  # Every 2 minutes at moderate energy
    
    # Update last full reflection time for cooldown tracking
    _last_full_reflection = current_time
    
    return {
        "frequency_sec": frequency_sec,
        "depth": depth
    }