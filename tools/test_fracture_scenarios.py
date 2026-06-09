import os
import sys
import time
import dill
import traceback
import logging
from datetime import datetime
from contextlib import contextmanager

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create snapshots directory
SNAPSHOTS_DIR = "logs/fracture_snapshots"
os.makedirs(SNAPSHOTS_DIR, exist_ok=True)

class FractureCapture:
    def __init__(self):
        self.captured_state = None
        self.capture_enabled = True

    def capture_state(self, frame, event, arg):
        """Capture the full execution state at the point of fracture"""
        if not self.capture_enabled:
            return self.capture_state
            
        try:
            # Capture local and global variables
            local_vars = {}
            global_vars = {}
            
            # Get variables from current frame
            if frame:
                local_vars.update(frame.f_locals)
                global_vars.update(frame.f_globals)
                
                # Traverse up the call stack
                call_stack = []
                current_frame = frame
                while current_frame:
                    frame_info = {
                        'filename': current_frame.f_code.co_filename,
                        'function': current_frame.f_code.co_name,
                        'lineno': current_frame.f_lineno,
                        'locals': dict(current_frame.f_locals),
                        'globals': dict(current_frame.f_globals)
                    }
                    call_stack.append(frame_info)
                    current_frame = current_frame.f_back
                    
                # Capture memory/state information
                state_snapshot = {
                    'timestamp': datetime.now().isoformat(),
                    'call_stack': call_stack,
                    'local_variables': local_vars,
                    'global_variables': global_vars,
                    'exception_info': sys.exc_info() if event == 'exception' else None,
                    'memory_info': self._get_memory_info()
                }
                
                self.captured_state = state_snapshot
                self._save_snapshot(state_snapshot)
                
        except Exception as e:
            logger.error(f"Error capturing state: {e}")
            
        return self.capture_state

    def _get_memory_info(self):
        """Capture basic memory information"""
        try:
            import psutil
            process = psutil.Process(os.getpid())
            return {
                'memory_percent': process.memory_percent(),
                'memory_info': process.memory_info()._asdict()
            }
        except ImportError:
            return {'memory_info': 'psutil not available'}

    def _save_snapshot(self, state):
        """Save the captured state to a file"""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
            filename = f"fracture_snapshot_{timestamp}.pkl"
            filepath = os.path.join(SNAPSHOTS_DIR, filename)
            
            with open(filepath, 'wb') as f:
                dill.dump(state, f)
                
            logger.info(f"Fracture snapshot saved: {filepath}")
        except Exception as e:
            logger.error(f"Error saving snapshot: {e}")

    @contextmanager
    def monitor_execution(self):
        """Context manager to monitor execution for fractures"""
        old_trace = sys.gettrace()
        sys.settrace(self.capture_state)
        try:
            yield
        finally:
            sys.settrace(old_trace)

# Global fracture capture instance
fracture_capture = FractureCapture()

def detect_semantic_divergence(russian_text, english_text):
    """
    Detect semantic divergence between Russian and English text.
    This is a placeholder - in reality this would contain complex NLP logic.
    """
    # Simulate some processing that might lead to divergence
    russian_tokens = russian_text.lower().split()
    english_tokens = english_text.lower().split()
    
    # Artificial divergence point for testing
    if len(russian_tokens) != len(english_tokens):
        raise ValueError("Semantic divergence detected: token count mismatch")
    
    # More complex divergence detection
    semantic_map = {
        'привет': 'hello',
        'мир': 'world',
        'пока': 'goodbye'
    }
    
    for rt, et in zip(russian_tokens, english_tokens):
        if rt in semantic_map and semantic_map[rt] != et:
            # This is where we would capture the fracture
            raise ValueError(f"Semantic divergence: {rt} != {et}")

def run_fracture_test(russian_input, english_input):
    """Run a test scenario that may lead to semantic divergence"""
    with fracture_capture.monitor_execution():
        try:
            detect_semantic_divergence(russian_input, english_input)
            return "No divergence detected"
        except Exception as e:
            logger.info(f"Fracture detected: {e}")
            # The state has already been captured by the trace function
            return f"Fracture: {e}"

def load_fracture_snapshot(filename):
    """Load a previously saved fracture snapshot"""
    filepath = os.path.join(SNAPSHOTS_DIR, filename)
    with open(filepath, 'rb') as f:
        return dill.load(f)

def replay_fracture_snapshot(snapshot_data):
    """Replay the context from a fracture snapshot"""
    logger.info("Replaying fracture snapshot...")
    logger.info(f"Timestamp: {snapshot_data['timestamp']}")
    logger.info(f"Call stack depth: {len(snapshot_data['call_stack'])}")
    logger.info(f"Local variables: {list(snapshot_data['local_variables'].keys())}")

# Test scenarios
def test_scenario_1():
    """Test basic divergence"""
    logger.info("Running test scenario 1...")
    result = run_fracture_test("привет мир", "hello world")
    logger.info(f"Result: {result}")

def test_scenario_2():
    """Test divergence with mismatched tokens"""
    logger.info("Running test scenario 2...")
    result = run_fracture_test("привет мир пока", "hello world")
    logger.info(f"Result: {result}")

def test_scenario_3():
    """Test semantic divergence"""
    logger.info("Running test scenario 3...")
    result = run_fracture_test("привет мир", "hello universe")
    logger.info(f"Result: {result}")

if __name__ == "__main__":
    # Run test scenarios
    test_scenario_1()
    test_scenario_2()
    test_scenario_3()
    
    # List available snapshots
    snapshots = [f for f in os.listdir(SNAPSHOTS_DIR) if f.endswith('.pkl')]
    if snapshots:
        logger.info(f"Available snapshots: {snapshots}")
        # Load and replay the latest snapshot as example
        latest_snapshot = sorted(snapshots)[-1]
        logger.info(f"Replaying latest snapshot: {latest_snapshot}")
        snapshot_data = load_fracture_snapshot(latest_snapshot)
        replay_fracture_snapshot(snapshot_data)