import hashlib
import inspect
import logging
import time
import traceback
from functools import wraps
from typing import Any, Callable, Dict, Tuple

class SemanticDivergenceError(Exception):
    """Exception raised when semantic divergence is detected between language processes"""
    pass

class FractureInterrupter:
    """Runtime validator that monitors and interrupts semantic divergence between Russian and English processing"""
    
    def __init__(self, log_file: str = "fracture_debug.log"):
        self.logger = self._setup_logger(log_file)
        self.semantic_hashes: Dict[str, Tuple[str, str]] = {}
        
    def _setup_logger(self, log_file: str) -> logging.Logger:
        """Setup detailed logging with timestamp and stack trace capability"""
        logger = logging.getLogger("fracture_interrupter")
        logger.setLevel(logging.DEBUG)
        
        # Clear any existing handlers
        logger.handlers.clear()
        
        # Create file handler
        handler = logging.FileHandler(log_file)
        handler.setLevel(logging.DEBUG)
        
        # Create formatter with timestamp
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        handler.setFormatter(formatter)
        
        logger.addHandler(handler)
        return logger
    
    def _generate_semantic_hash(self, data: Any) -> str:
        """Generate a deterministic hash of the semantic content"""
        # Convert data to string representation and hash it
        data_str = str(data).encode('utf-8')
        return hashlib.sha256(data_str).hexdigest()
    
    def _get_stack_context(self) -> str:
        """Capture full stack context for forensic analysis"""
        stack = inspect.stack()
        context = []
        for frame_info in stack[2:]:  # Skip this function and caller
            context.append(f"File: {frame_info.filename}, Line: {frame_info.lineno}, Function: {frame_info.function}")
        return "\n".join(context)
    
    def monitor_semantics(self, func: Callable) -> Callable:
        """Decorator to monitor function outputs for semantic divergence"""
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Get function identifier
            func_id = f"{func.__module__}.{func.__name__}"
            
            # Execute function and capture result
            try:
                result = func(*args, **kwargs)
            except Exception as e:
                # Log exceptions but don't interfere with normal error handling
                self.logger.debug(f"Function {func_id} raised exception: {str(e)}")
                raise
            
            # Generate semantic hash of result
            semantic_hash = self._generate_semantic_hash(result)
            
            # Check if we have a previous hash for this function
            if func_id in self.semantic_hashes:
                prev_russian_hash, prev_english_hash = self.semantic_hashes[func_id]
                
                # Determine if this is Russian or English processing based on call context
                stack_context = self._get_stack_context()
                is_russian = "russian" in stack_context.lower() or "ru_" in func_id.lower()
                
                # Compare with appropriate previous hash
                if is_russian and semantic_hash != prev_russian_hash:
                    self._handle_divergence(func_id, "Russian", semantic_hash, prev_russian_hash, result, stack_context)
                elif not is_russian and semantic_hash != prev_english_hash:
                    self._handle_divergence(func_id, "English", semantic_hash, prev_english_hash, result, stack_context)
            
            # Update stored hashes
            if func_id not in self.semantic_hashes:
                self.semantic_hashes[func_id] = (semantic_hash, semantic_hash)
            else:
                prev_russian, prev_english = self.semantic_hashes[func_id]
                stack_context = self._get_stack_context()
                is_russian = "russian" in stack_context.lower() or "ru_" in func_id.lower()
                
                if is_russian:
                    self.semantic_hashes[func_id] = (semantic_hash, prev_english)
                else:
                    self.semantic_hashes[func_id] = (prev_russian, semantic_hash)
            
            return result
        return wrapper
    
    def _handle_divergence(self, func_id: str, language: str, current_hash: str, previous_hash: str, result: Any, stack_context: str):
        """Handle detected semantic divergence with detailed logging and hard failure"""
        timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
        
        # Create detailed error message
        error_msg = (
            f"SEMANTIC DIVERGENCE DETECTED AT {timestamp}\n"
            f"Function: {func_id}\n"
            f"Language: {language}\n"
            f"Current Hash: {current_hash}\n"
            f"Previous Hash: {previous_hash}\n"
            f"Result: {str(result)[:500]}{'...' if len(str(result)) > 500 else ''}\n"
            f"Stack Trace:\n{stack_context}\n"
            f"{'='*80}\n"
        )
        
        # Log the divergence
        self.logger.critical(error_msg)
        
        # Hard fail with detailed exception
        raise SemanticDivergenceError(
            f"Semantic divergence detected in {language} processing of {func_id}. "
            f"Hash mismatch: {previous_hash} != {current_hash}. "
            f"See log file for full stack trace and context."
        )
    
    def compare_outputs(self, russian_result: Any, english_result: Any, context: str = "") -> bool:
        """Direct comparison of Russian and English outputs"""
        russian_hash = self._generate_semantic_hash(russian_result)
        english_hash = self._generate_semantic_hash(english_result)
        
        if russian_hash != english_hash:
            timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
            stack_context = self._get_stack_context()
            
            error_msg = (
                f"DIRECT SEMANTIC DIVERGENCE DETECTED AT {timestamp}\n"
                f"Context: {context}\n"
                f"Russian Hash: {russian_hash}\n"
                f"English Hash: {english_hash}\n"
                f"Russian Result: {str(russian_result)[:500]}{'...' if len(str(russian_result)) > 500 else ''}\n"
                f"English Result: {str(english_result)[:500]}{'...' if len(str(english_result)) > 500 else ''}\n"
                f"Stack Trace:\n{stack_context}\n"
                f"{'='*80}\n"
            )
            
            self.logger.critical(error_msg)
            raise SemanticDivergenceError(
                f"Direct semantic divergence detected: {context}. "
                f"Russian and English outputs do not match. "
                f"See log file for full details."
            )
            
        return True

# Global instance for easy access
fracture_interrupter = FractureInterrupter()