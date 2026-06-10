#!/usr/bin/env python3

import sys
import os
import threading
import queue
import time
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from memory.semantic_drift_hooks import SemanticDriftMonitor
from memory.multilingual_coherence import MultilingualCoherenceValidator

class FractureInterrupter:
    def __init__(self):
        self.drift_monitor = SemanticDriftMonitor()
        self.coherence_validator = MultilingualCoherenceValidator()
        self.interrupt_queue = queue.Queue()
        self.running = False
        self.monitor_thread = None
        
    def start_monitoring(self):
        """Start monitoring semantic drift between language stacks"""
        self.running = True
        self.monitor_thread = threading.Thread(target=self._monitor_loop)
        self.monitor_thread.daemon = True
        self.monitor_thread.start()
        
    def stop_monitoring(self):
        """Stop monitoring and cleanup"""
        self.running = False
        if self.monitor_thread:
            self.monitor_thread.join(timeout=2.0)
            
    def _monitor_loop(self):
        """Main monitoring loop that captures divergence traces"""
        while self.running:
            try:
                # Capture live divergence traces
                divergence_data = self.drift_monitor.capture_divergence_trace()
                
                if divergence_data:
                    # Validate coherence immediately
                    validation_result = self.coherence_validator.validate_coherence(divergence_data)
                    
                    # If fracture detected, interrupt
                    if not validation_result.is_coherent:
                        self._trigger_interrupt(validation_result)
                        
            except Exception as e:
                print(f"Monitoring error: {e}")
                continue
                
            time.sleep(0.1)  # 100ms polling interval
            
    def _trigger_interrupt(self, validation_result):
        """Trigger interrupt based on coherence failure"""
        interrupt_data = {
            'timestamp': time.time(),
            'validation_result': validation_result,
            'interrupt_type': 'semantic_fracture'
        }
        
        self.interrupt_queue.put(interrupt_data)
        print(f"FRacture interrupt triggered: {validation_result.reason}")
        
    def check_interrupts(self):
        """Check for pending interrupts"""
        interrupts = []
        while not self.interrupt_queue.empty():
            try:
                interrupts.append(self.interrupt_queue.get_nowait())
            except queue.Empty:
                break
        return interrupts

def main():
    """Main entry point"""
    interrupter = FractureInterrupter()
    
    try:
        print("Starting Fracture Interrupter...")
        interrupter.start_monitoring()
        
        # Keep running until interrupted
        while True:
            interrupts = interrupter.check_interrupts()
            for interrupt in interrupts:
                print(f"Interrupt: {interrupt}")
            time.sleep(0.5)
            
    except KeyboardInterrupt:
        print("\nShutting down...")
    finally:
        interrupter.stop_monitoring()

if __name__ == "__main__":
    main()