import time
import logging
from typing import Optional, Dict, Any
from dataclasses import dataclass, field
from enum import Enum

logger = logging.getLogger(__name__)

class Language(Enum):
    RUSSIAN = "ru"
    ENGLISH = "en"

@dataclass
class CognitiveState:
    energy_level: float
    coherence: float
    task_completion_time: float = 0.0

@dataclass
class LanguageSwitchEvent:
    timestamp: float
    from_language: Language
    to_language: Language
    pre_state: CognitiveState
    post_state: CognitiveState
    energy_delta: float
    coherence_impact: float

class ReflectionCooldown:
    def __init__(self, fragmentation_threshold: float = 0.3):
        self.fragmentation_threshold = fragmentation_threshold
        self.last_fragmentation_check: Optional[float] = None
        self.cooldown_period: float = 5.0  # seconds
    
    def should_enforce_pause(self, coherence_impact: float) -> bool:
        current_time = time.time()
        if coherence_impact > self.fragmentation_threshold:
            if (self.last_fragmentation_check is None or 
                current_time - self.last_fragmentation_check > self.cooldown_period):
                self.last_fragmentation_check = current_time
                return True
        return False

class MultilingualTracer:
    def __init__(self, fragmentation_threshold: float = 0.3):
        self.current_language: Language = Language.ENGLISH
        self.events: list[LanguageSwitchEvent] = []
        self.reflection_cooldown = ReflectionCooldown(fragmentation_threshold)
        self._state_history: list[CognitiveState] = []
        
    def _get_current_state(self) -> CognitiveState:
        # In a real implementation, this would interface with actual cognitive monitoring
        # For now, we'll simulate based on recent events
        if self._state_history:
            return self._state_history[-1]
        return CognitiveState(energy_level=1.0, coherence=1.0)
    
    def _calculate_energy_level(self) -> float:
        # Simulated energy calculation
        base_energy = 1.0
        recent_events = [e for e in self.events if time.time() - e.timestamp < 60]
        energy_drain = len(recent_events) * 0.05
        return max(0.1, base_energy - energy_drain)
    
    def _calculate_coherence(self) -> float:
        # Simulated coherence calculation
        if not self.events:
            return 1.0
        recent_switches = [e for e in self.events if time.time() - e.timestamp < 30]
        coherence_penalty = len(recent_switches) * 0.1
        return max(0.1, 1.0 - coherence_penalty)
    
    def switch_language(self, target_language: Language) -> Optional[LanguageSwitchEvent]:
        if target_language == self.current_language:
            return None
            
        timestamp = time.time()
        pre_state = self._get_current_state()
        pre_state.energy_level = self._calculate_energy_level()
        pre_state.coherence = self._calculate_coherence()
        
        # Simulate task completion time impact
        task_start = time.time()
        # Simulate some work being done
        time.sleep(0.01)  # Minimal simulation delay
        task_completion_time = time.time() - task_start
        
        # Update to new state
        self.current_language = target_language
        post_state = CognitiveState(
            energy_level=self._calculate_energy_level(),
            coherence=self._calculate_coherence(),
            task_completion_time=task_completion_time
        )
        
        energy_delta = post_state.energy_level - pre_state.energy_level
        coherence_impact = pre_state.coherence - post_state.coherence
        
        event = LanguageSwitchEvent(
            timestamp=timestamp,
            from_language=Language.ENGLISH if target_language == Language.RUSSIAN else Language.RUSSIAN,
            to_language=target_language,
            pre_state=pre_state,
            post_state=post_state,
            energy_delta=energy_delta,
            coherence_impact=coherence_impact
        )
        
        self.events.append(event)
        self._state_history.append(post_state)
        
        # Log the event
        logger.info(
            f"Language switch: {event.from_language.value} → {event.to_language.value} | "
            f"Energy Δ: {event.energy_delta:.3f} | "
            f"Coherence impact: {event.coherence_impact:.3f} | "
            f"Task time: {task_completion_time:.3f}s"
        )
        
        # Check if we need to enforce reflection cooldown
        if self.reflection_cooldown.should_enforce_pause(abs(coherence_impact)):
            logger.warning("Fragmentation threshold breached. Enforcing reflection pause.")
            time.sleep(self.reflection_cooldown.cooldown_period)
            
        return event
    
    def get_current_language(self) -> Language:
        return self.current_language
    
    def get_recent_events(self, seconds: float = 60) -> list[LanguageSwitchEvent]:
        cutoff_time = time.time() - seconds
        return [event for event in self.events if event.timestamp > cutoff_time]
    
    def get_energy_trend(self) -> float:
        if len(self.events) < 2:
            return 0.0
        recent_events = self.get_recent_events(30)
        if len(recent_events) < 2:
            return 0.0
        return recent_events[-1].post_state.energy_level - recent_events[0].pre_state.energy_level