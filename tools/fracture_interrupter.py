import sys
import json
import traceback
from functools import wraps
import importlib.util
import os

class FractureTracer:
    def __init__(self, log_file="fracture_traces.json"):
        self.log_file = log_file
        self.trace_data = []
        self.enabled = True

    def log_event(self, event_type, message, stack_trace=None, context=None):
        if not self.enabled:
            return
            
        trace_entry = {
            "event_type": event_type,
            "message": message,
            "timestamp": __import__('time').time(),
            "context": context or {}
        }
        
        if stack_trace:
            trace_entry["stack_trace"] = stack_trace
            
        self.trace_data.append(trace_entry)
        self._write_trace()

    def _write_trace(self):
        try:
            with open(self.log_file, 'w') as f:
                json.dump(self.trace_data, f, indent=2)
        except Exception as e:
            print(f"Failed to write trace log: {e}", file=sys.stderr)

    def trace_function(self, func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            try:
                result = func(*args, **kwargs)
                return result
            except Exception as e:
                stack_trace = traceback.format_exc()
                self.log_event(
                    "exception",
                    f"Exception in {func.__name__}: {str(e)}",
                    stack_trace=stack_trace,
                    context={"args": str(args)[:200], "kwargs": str(kwargs)[:200]}
                )
                raise
        return wrapper

def inject_trace_hooks():
    tracer = FractureTracer()
    
    try:
        # Dynamically import multilingual_coherence
        spec = importlib.util.spec_from_file_location(
            "multilingual_coherence", 
            "multilingual_coherence.py"
        )
        module = importlib.util.module_from_spec(spec)
        sys.modules["multilingual_coherence"] = module
        spec.loader.exec_module(module)
        
        # Hook critical functions
        if hasattr(module, 'assess_coherence'):
            module.assess_coherence = tracer.trace_function(module.assess_coherence)
        if hasattr(module, 'validate_semantic_consistency'):
            module.validate_semantic_consistency = tracer.trace_function(module.validate_semantic_consistency)
        if hasattr(module, 'detect_divergence'):
            module.detect_divergence = tracer.trace_function(module.detect_divergence)
            
        # Add divergence detection hook
        original_assess_coherence = getattr(module, 'assess_coherence', None)
        if original_assess_coherence:
            def divergence_wrapper(*args, **kwargs):
                try:
                    result = original_assess_coherence(*args, **kwargs)
                    # Check for semantic mismatches
                    if hasattr(result, 'coherence_score') and result.coherence_score < 0.5:
                        tracer.log_event(
                            "semantic_mismatch",
                            "Low coherence score detected",
                            context={
                                "coherence_score": result.coherence_score,
                                "input_length": len(str(args)) if args else 0
                            }
                        )
                    return result
                except Exception as e:
                    stack_trace = traceback.format_exc()
                    tracer.log_event(
                        "validator_failure",
                        f"Coherence assessment failed: {str(e)}",
                        stack_trace=stack_trace
                    )
                    raise
                    
            module.assess_coherence = divergence_wrapper
            
        return module, tracer
        
    except Exception as e:
        stack_trace = traceback.format_exc()
        tracer.log_event(
            "injection_failure",
            f"Failed to inject trace hooks: {str(e)}",
            stack_trace=stack_trace
        )
        raise

def main():
    try:
        module, tracer = inject_trace_hooks()
        
        # If module has a main execution function, run it
        if hasattr(module, 'main'):
            module.main()
        elif hasattr(module, '__main__'):
            module.__main__()
        else:
            # Try to execute module directly
            exec(open("multilingual_coherence.py").read())
            
    except Exception as e:
        stack_trace = traceback.format_exc()
        if 'tracer' in locals():
            tracer.log_event(
                "execution_failure",
                f"Module execution failed: {str(e)}",
                stack_trace=stack_trace
            )
        else:
            print(f"Critical failure before tracer initialization: {e}")
            print(stack_trace)

if __name__ == "__main__":
    main()