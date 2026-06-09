import sys
import gc
import psutil
import logging
import threading
from typing import Dict, Any, Callable, List, Optional
from collections import defaultdict, deque
from datetime import datetime, timedelta
import time

from memory.anomaly_detector import AnomalyDetector, AnomalyReport

class RuntimeIntrospection:
    def __init__(self, anomaly_detector: AnomalyDetector, log_level: int = logging.INFO):
        self.anomaly_detector = anomaly_detector
        self.logger = self._setup_logger(log_level)
        self.hooks: List[Callable[[AnomalyReport], None]] = []
        self.review_threshold = 0.8  # Threshold for human review
        self.anomaly_history = deque(maxlen=1000)
        self.lock = threading.Lock()
        
    def _setup_logger(self, log_level: int) -> logging.Logger:
        logger = logging.getLogger('RuntimeIntrospection')
        logger.setLevel(log_level)
        if not logger.handlers:
            handler = logging.StreamHandler(sys.stdout)
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)
        return logger
    
    def add_hook(self, hook: Callable[[AnomalyReport], None]) -> None:
        """Add a hook function to be called when anomalies are detected."""
        with self.lock:
            self.hooks.append(hook)
    
    def set_review_threshold(self, threshold: float) -> None:
        """Set the threshold for triggering human review."""
        if not 0 <= threshold <= 1:
            raise ValueError("Threshold must be between 0 and 1")
        self.review_threshold = threshold
    
    def get_memory_stats(self) -> Dict[str, Any]:
        """Get current memory statistics."""
        process = psutil.Process()
        mem_info = process.memory_info()
        gc_stats = gc.get_stats()
        
        return {
            'timestamp': datetime.now(),
            'process_memory_rss': mem_info.rss,
            'process_memory_vms': mem_info.vms,
            'system_memory_percent': psutil.virtual_memory().percent,
            'gc_collections': sum(stat['collections'] for stat in gc_stats),
            'gc_collected': sum(stat['collected'] for stat in gc_stats),
            'gc_uncollectable': sum(stat['uncollectable'] for stat in gc_stats),
            'object_count': len(gc.get_objects())
        }
    
    def detect_anomalies(self) -> List[AnomalyReport]:
        """Detect anomalies in current memory state."""
        stats = self.get_memory_stats()
        anomalies = self.anomaly_detector.detect(stats)
        
        with self.lock:
            for anomaly in anomalies:
                self.anomaly_history.append(anomaly)
                self._trigger_hooks(anomaly)
                self._handle_anomaly(anomaly)
        
        return anomalies
    
    def _trigger_hooks(self, anomaly: AnomalyReport) -> None:
        """Trigger all registered hooks for an anomaly."""
        for hook in self.hooks:
            try:
                hook(anomaly)
            except Exception as e:
                self.logger.error(f"Hook execution failed: {e}")
    
    def _handle_anomaly(self, anomaly: AnomalyReport) -> None:
        """Handle anomaly based on severity and review threshold."""
        self.logger.warning(
            f"Anomaly detected: {anomaly.type} - Severity: {anomaly.severity:.2f} - "
            f"Details: {anomaly.details}"
        )
        
        if anomaly.severity >= self.review_threshold:
            self._trigger_human_review(anomaly)
    
    def _trigger_human_review(self, anomaly: AnomalyReport) -> None:
        """Trigger human review process for high-severity anomalies."""
        self.logger.critical(
            f"HUMAN REVIEW REQUIRED - High severity anomaly: {anomaly.type} "
            f"(Severity: {anomaly.severity:.2f})"
        )
        # In a real implementation, this would notify operators or trigger alerts
        # For now, we just log it as critical
    
    def get_anomaly_summary(self, hours: int = 24) -> Dict[str, Any]:
        """Get a summary of anomalies from the last N hours."""
        cutoff_time = datetime.now() - timedelta(hours=hours)
        recent_anomalies = [
            a for a in self.anomaly_history 
            if a.timestamp >= cutoff_time
        ]
        
        if not recent_anomalies:
            return {
                'total_anomalies': 0,
                'anomalies_by_type': {},
                'average_severity': 0.0,
                'high_severity_count': 0
            }
        
        anomalies_by_type = defaultdict(int)
        total_severity = 0.0
        high_severity_count = 0
        
        for anomaly in recent_anomalies:
            anomalies_by_type[anomaly.type] += 1
            total_severity += anomaly.severity
            if anomaly.severity >= self.review_threshold:
                high_severity_count += 1
        
        return {
            'total_anomalies': len(recent_anomalies),
            'anomalies_by_type': dict(anomalies_by_type),
            'average_severity': total_severity / len(recent_anomalies),
            'high_severity_count': high_severity_count
        }

# Unit tests
import unittest
from unittest.mock import Mock, patch, MagicMock

class TestRuntimeIntrospection(unittest.TestCase):
    def setUp(self):
        self.mock_anomaly_detector = Mock(spec=AnomalyDetector)
        self.introspection = RuntimeIntrospection(self.mock_anomaly_detector)
    
    def test_initialization(self):
        self.assertIsInstance(self.introspection.logger, logging.Logger)
        self.assertEqual(self.introspection.review_threshold, 0.8)
        self.assertEqual(len(self.introspection.hooks), 0)
    
    def test_add_hook(self):
        mock_hook = Mock()
        self.introspection.add_hook(mock_hook)
        self.assertEqual(len(self.introspection.hooks), 1)
        self.assertIn(mock_hook, self.introspection.hooks)
    
    def test_set_review_threshold_valid(self):
        self.introspection.set_review_threshold(0.5)
        self.assertEqual(self.introspection.review_threshold, 0.5)
    
    def test_set_review_threshold_invalid(self):
        with self.assertRaises(ValueError):
            self.introspection.set_review_threshold(1.5)
        with self.assertRaises(ValueError):
            self.introspection.set_review_threshold(-0.1)
    
    @patch('memory.runtime_introspection.psutil')
    def test_get_memory_stats(self, mock_psutil):
        # Setup mocks
        mock_process = Mock()
        mock_process.memory_info.return_value = Mock(rss=1024*1024, vms=2048*1024)
        mock_psutil.Process.return_value = mock_process
        mock_psutil.virtual_memory.return_value = Mock(percent=45.5)
        
        with patch('memory.runtime_introspection.gc') as mock_gc:
            mock_gc.get_stats.return_value = [
                {'collections': 100, 'collected': 50, 'uncollectable': 5},
                {'collections': 200, 'collected': 100, 'uncollectable': 10}
            ]
            mock_gc.get_objects.return_value = [None] * 1000
            
            stats = self.introspection.get_memory_stats()
            
            self.assertIn('timestamp', stats)
            self.assertEqual(stats['process_memory_rss'], 1024*1024)
            self.assertEqual(stats['process_memory_vms'], 2048*1024)
            self.assertEqual(stats['system_memory_percent'], 45.5)
            self.assertEqual(stats['gc_collections'], 300)
            self.assertEqual(stats['gc_collected'], 150)
            self.assertEqual(stats['gc_uncollectable'], 15)
            self.assertEqual(stats['object_count'], 1000)
    
    def test_detect_anomalies_no_anomalies(self):
        self.mock_anomaly_detector.detect.return_value = []
        anomalies = self.introspection.detect_anomalies()
        self.assertEqual(anomalies, [])
        self.assertEqual(len(self.introspection.anomaly_history), 0)
    
    def test_detect_anomalies_with_anomalies(self):
        mock_anomaly = Mock(spec=AnomalyReport)
        mock_anomaly.type = "memory_leak"
        mock_anomaly.severity = 0.9
        mock_anomaly.timestamp = datetime.now()
        mock_anomaly.details = "Test anomaly"
        
        self.mock_anomaly_detector.detect.return_value = [mock_anomaly]
        
        # Add a hook to verify it's called
        hook_called = Mock()
        self.introspection.add_hook(hook_called)
        
        anomalies = self.introspection.detect_anomalies()
        
        self.assertEqual(len(anomalies), 1)
        self.assertEqual(anomalies[0], mock_anomaly)
        self.assertEqual(len(self.introspection.anomaly_history), 1)
        hook_called.assert_called_once_with(mock_anomaly)
    
    @patch('memory.runtime_introspection.logging.Logger')
    def test_handle_anomaly_below_threshold(self, mock_logger):
        mock_anomaly = Mock(spec=AnomalyReport)
        mock_anomaly.type = "memory_spike"
        mock_anomaly.severity = 0.5
        mock_anomaly.details =