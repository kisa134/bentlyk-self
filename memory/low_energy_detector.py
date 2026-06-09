import time
from memory.state import StateManager

class LowEnergyDetector:
    def __init__(self, state_manager: StateManager, cooldown_minutes: int = 5):
        self.state_manager = state_manager
        self.cooldown_seconds = cooldown_minutes * 60
        self.last_trigger_time = 0
        self.triggered = False

    def check_levels(self):
        current_time = time.time()
        state = self.state_manager.get_state()
        
        energy = state.get('energy', 1.0)
        pain = state.get('pain', 0.0)
        
        # Check if levels indicate need for pause
        if (energy < 0.5 or pain > 0.6) and not self.triggered:
            self._trigger_pause(current_time)
        elif self.triggered and current_time - self.last_trigger_time > self.cooldown_seconds:
            self._resume_reflection()

    def _trigger_pause(self, current_time):
        self.triggered = True
        self.last_trigger_time = current_time
        self.state_manager.update_state({'pause_reflection': True})
        self._log_event("Low energy or high pain detected. Pausing reflection.")

    def _resume_reflection(self):
        self.triggered = False
        self.state_manager.update_state({'pause_reflection': False})
        self._log_event("Cooldown period ended. Resuming reflection.")

    def _log_event(self, message):
        timestamp = time.strftime('%Y-%m-%d %H:%M:%S')
        print(f"[{timestamp}] {message}")