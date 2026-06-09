import psutil
import hashlib
import json
import statistics
from collections import defaultdict
from typing import Dict, List, Any, Tuple, Optional
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class DeltaAnalyzer:
    def __init__(self):
        self.current_snapshot = None
        self.previous_snapshot = None
        self.anomalies = []
        
    def take_snapshot(self) -> Dict[str, Any]:
        """Take a comprehensive snapshot of current memory state"""
        try:
            # Get system memory info
            memory_info = psutil.virtual_memory()
            
            # Get process memory info
            processes = []
            for proc in psutil.process_iter(['pid', 'name', 'memory_info', 'memory_percent']):
                try:
                    proc_info = proc.info
                    if proc_info['memory_info']:
                        processes.append({
                            'pid': proc_info['pid'],
                            'name': proc_info['name'],
                            'rss': proc_info['memory_info'].rss,
                            'vms': proc_info['memory_info'].vms,
                            'memory_percent': proc_info['memory_percent']
                        })
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
            
            snapshot = {
                'timestamp': datetime.now().isoformat(),
                'system_memory': {
                    'total': memory_info.total,
                    'available': memory_info.available,
                    'used': memory_info.used,
                    'free': memory_info.free,
                    'percent': memory_info.percent
                },
                'processes': processes,
                'checksum': None
            }
            
            # Generate checksum for integrity verification
            snapshot['checksum'] = self._generate_checksum(snapshot)
            
            self.previous_snapshot = self.current_snapshot
            self.current_snapshot = snapshot
            
            logger.info("Memory snapshot taken successfully")
            return snapshot
            
        except Exception as e:
            logger.error(f"Failed to take memory snapshot: {e}")
            raise
    
    def compare(self, last_snapshot: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Compare current snapshot with a previous one"""
        if not self.current_snapshot:
            raise ValueError("No current snapshot available. Call take_snapshot() first.")
            
        if last_snapshot is None:
            last_snapshot = self.previous_snapshot
            
        if not last_snapshot:
            raise ValueError("No previous snapshot available for comparison.")
            
        # Verify checksums
        if not self._verify_checksum(last_snapshot):
            raise ValueError("Previous snapshot integrity check failed")
            
        if not self._verify_checksum(self.current_snapshot):
            raise ValueError("Current snapshot integrity check failed")
            
        try:
            comparison = {
                'timestamp': datetime.now().isoformat(),
                'system_memory_delta': self._compare_system_memory(
                    last_snapshot['system_memory'],
                    self.current_snapshot['system_memory']
                ),
                'process_deltas': self._compare_processes(
                    last_snapshot['processes'],
                    self.current_snapshot['processes']
                ),
                'summary': {}
            }
            
            # Generate summary statistics
            process_rss_changes = [p['rss_delta'] for p in comparison['process_deltas']]
            comparison['summary'] = {
                'total_processes': len(comparison['process_deltas']),
                'mean_rss_change': statistics.mean(process_rss_changes) if process_rss_changes else 0,
                'median_rss_change': statistics.median(process_rss_changes) if process_rss_changes else 0,
                'rss_change_stddev': statistics.stdev(process_rss_changes) if len(process_rss_changes) > 1 else 0,
                'system_memory_change_percent': comparison['system_memory_delta']['percent_delta']
            }
            
            logger.info("Memory comparison completed successfully")
            return comparison
            
        except Exception as e:
            logger.error(f"Failed to compare memory snapshots: {e}")
            raise
    
    def flag_anomalies(self, threshold: float = 0.15) -> List[Dict[str, Any]]:
        """Flag processes with significant memory changes"""
        if not self.current_snapshot or not self.previous_snapshot:
            raise ValueError("Both current and previous snapshots are required to flag anomalies.")
            
        comparison = self.compare()
        self.anomalies = []
        
        try:
            # Flag system memory anomalies
            if abs(comparison['system_memory_delta']['percent_delta']) > threshold * 100:
                self.anomalies.append({
                    'type': 'system_memory',
                    'severity': 'high',
                    'description': f"Significant system memory change: {comparison['system_memory_delta']['percent_delta']:.2f}%",
                    'data': comparison['system_memory_delta']
                })
            
            # Flag process memory anomalies
            for proc_delta in comparison['process_deltas']:
                rss_change_pct = proc_delta.get('rss_delta_percent', 0)
                if abs(rss_change_pct) > threshold * 100:
                    severity = 'high' if abs(rss_change_pct) > threshold * 200 else 'medium'
                    self.anomalies.append({
                        'type': 'process_memory',
                        'severity': severity,
                        'description': f"Process {proc_delta['name']} (PID: {proc_delta['pid']}) memory change: {rss_change_pct:.2f}%",
                        'data': proc_delta
                    })
            
            logger.info(f"Flagged {len(self.anomalies)} anomalies")
            return self.anomalies
            
        except Exception as e:
            logger.error(f"Failed to flag anomalies: {e}")
            raise
    
    def generate_report(self) -> Dict[str, Any]:
        """Generate a comprehensive report of memory state and anomalies"""
        if not self.current_snapshot:
            raise ValueError("No snapshot data available. Call take_snapshot() first.")
            
        try:
            report = {
                'report_timestamp': datetime.now().isoformat(),
                'current_state': self.current_snapshot,
                'previous_state': self.previous_snapshot,
                'anomalies': self.anomalies,
                'patterns': self._identify_patterns()
            }
            
            # Add comparison if both snapshots exist
            if self.previous_snapshot:
                try:
                    report['comparison'] = self.compare()
                except ValueError:
                    report['comparison'] = None
                    
            logger.info("Memory analysis report generated successfully")
            return report
            
        except Exception as e:
            logger.error(f"Failed to generate report: {e}")
            raise
    
    def _generate_checksum(self, snapshot: Dict[str, Any]) -> str:
        """Generate a checksum for snapshot integrity verification"""
        # Remove timestamp and checksum fields for consistent hashing
        data_to_hash = {
            k: v for k, v in snapshot.items() 
            if k not in ['timestamp', 'checksum']
        }
        data_str = json.dumps(data_to_hash, sort_keys=True)
        return hashlib.sha256(data_str.encode()).hexdigest()
    
    def _verify_checksum(self, snapshot: Dict[str, Any]) -> bool:
        """Verify snapshot integrity using checksum"""
        if 'checksum' not in snapshot or snapshot['checksum'] is None:
            return True  # No checksum to verify
            
        original_checksum = snapshot['checksum']
        calculated_checksum = self._generate_checksum(snapshot)
        return original_checksum == calculated_checksum
    
    def _compare_system_memory(self, old: Dict[str, int], new: Dict[str, int]) -> Dict[str, float]:
        """Compare system memory states"""
        return {
            'total_delta': new['total'] - old['total'],
            'available_delta': new['available'] - old['available'],
            'used_delta': new['used'] - old['used'],
            'free_delta': new['free'] - old['free'],
            'percent_delta': new['percent'] - old['percent']
        }
    
    def _compare_processes(self, old_processes: List[Dict], new_processes: List[Dict]) -> List[Dict[str, Any]]:
        """Compare process memory usage between snapshots"""
        # Create lookup dictionaries
        old_proc_dict = {proc['pid']: proc for proc in old_processes}
        new_proc_dict = {proc['pid']: proc for proc in new_processes}
        
        deltas = []
        
        # Compare existing processes
        for pid in set(old_proc_dict.keys()) & set(new_proc_dict.keys()):
            old_proc = old_proc_dict[pid]
            new_proc = new_proc_dict[pid]
            
            rss_delta = new_proc['rss'] - old_proc['rss']
            rss_delta_percent = (rss_delta / old_proc['rss'] * 100) if old_proc['rss'] > 0 else 0
            
            deltas.append({
                'pid': pid,
                'name': new_proc['name'],
                'rss_delta': rss_delta,
                'rss_delta_percent': rss_delta_percent,
                'status': 'unchanged' if rss_delta == 0 else ('increased' if rss_delta > 0 else 'decreased')
            })
        
        # Handle new processes
        for pid in set(new_proc_dict.keys()) - set(old_proc_dict.keys()):
            proc = new_proc_dict[pid]
            deltas.append({
                'pid': pid,
                'name': proc['name'],
                'rss_delta': proc['rss'],
                'rss_delta_percent': 100.0,  # 100% increase from zero
                'status': 'new'
            })
        
        # Handle terminated processes
        for pid in set(old_proc_dict.keys()) - set(new_proc_dict.keys()):
            proc = old_proc_dict[pid]
            deltas.append({