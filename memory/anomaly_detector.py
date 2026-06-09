import json
import logging
from typing import Dict, List, Any, Tuple
from datetime import datetime
from dataclasses import dataclass
from pathlib import Path

@dataclass
class MemoryAnomaly:
    timestamp: str
    anomaly_type: str
    description: str
    severity: str
    suggested_fix: str
    data_points: Dict[str, Any]

class AnomalyDetector:
    def __init__(self, log_file: str = "anomaly_detection.log"):
        self.setup_logging(log_file)
        self.anomalies: List[MemoryAnomaly] = []
        
    def setup_logging(self, log_file: str):
        """Setup logging configuration"""
        logging.basicConfig(
            filename=log_file,
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger(__name__)
        
    def load_inspector_data(self, file_path: str) -> Dict:
        """Load memory data from self_inspector.py"""
        try:
            with open(file_path, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            self.logger.error(f"Inspector data file not found: {file_path}")
            return {}
        except json.JSONDecodeError as e:
            self.logger.error(f"Invalid JSON in inspector data: {e}")
            return {}
            
    def load_coherence_data(self, file_path: str) -> Dict:
        """Load memory data from coherence_tracker.py"""
        try:
            with open(file_path, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            self.logger.error(f"Coherence data file not found: {file_path}")
            return {}
        except json.JSONDecodeError as e:
            self.logger.error(f"Invalid JSON in coherence data: {e}")
            return {}
    
    def compare_memory_states(self, inspector_data: Dict, coherence_data: Dict) -> List[MemoryAnomaly]:
        """Compare memory states between inspector and coherence tracker"""
        anomalies = []
        
        # Check for missing memory regions
        inspector_regions = set(inspector_data.get('memory_regions', {}).keys())
        coherence_regions = set(coherence_data.get('tracked_regions', {}).keys())
        
        if inspector_regions != coherence_regions:
            missing_in_coherence = inspector_regions - coherence_regions
            missing_in_inspector = coherence_regions - inspector_regions
            
            if missing_in_coherence:
                anomalies.append(MemoryAnomaly(
                    timestamp=datetime.now().isoformat(),
                    anomaly_type="MISSING_REGIONS",
                    description=f"Memory regions missing in coherence tracker: {missing_in_coherence}",
                    severity="HIGH",
                    suggested_fix="Ensure all memory regions are registered in coherence tracker",
                    data_points={
                        "missing_regions": list(missing_in_coherence),
                        "inspector_regions": list(inspector_regions),
                        "coherence_regions": list(coherence_regions)
                    }
                ))
                
            if missing_in_inspector:
                anomalies.append(MemoryAnomaly(
                    timestamp=datetime.now().isoformat(),
                    anomaly_type="UNTRACKED_REGIONS",
                    description=f"Memory regions in coherence tracker but not inspector: {missing_in_inspector}",
                    severity="MEDIUM",
                    suggested_fix="Verify inspector is monitoring all tracked regions",
                    data_points={
                        "untracked_regions": list(missing_in_inspector),
                        "inspector_regions": list(inspector_regions),
                        "coherence_regions": list(coherence_regions)
                    }
                ))
        
        # Check for memory access inconsistencies
        self._check_access_patterns(inspector_data, coherence_data, anomalies)
        
        # Check for timing discrepancies
        self._check_timing_consistency(inspector_data, coherence_data, anomalies)
        
        return anomalies
    
    def _check_access_patterns(self, inspector_data: Dict, coherence_data: Dict, anomalies: List[MemoryAnomaly]):
        """Check for inconsistent memory access patterns"""
        inspector_access = inspector_data.get('access_patterns', {})
        coherence_access = coherence_data.get('access_patterns', {})
        
        for region, inspector_stats in inspector_access.items():
            if region in coherence_access:
                coherence_stats = coherence_access[region]
                
                # Check read/write discrepancy
                inspector_reads = inspector_stats.get('reads', 0)
                inspector_writes = inspector_stats.get('writes', 0)
                coherence_reads = coherence_stats.get('reads', 0)
                coherence_writes = coherence_stats.get('writes', 0)
                
                read_diff = abs(inspector_reads - coherence_reads)
                write_diff = abs(inspector_writes - coherence_writes)
                
                if read_diff > inspector_reads * 0.1:  # 10% threshold
                    anomalies.append(MemoryAnomaly(
                        timestamp=datetime.now().isoformat(),
                        anomaly_type="READ_COUNT_MISMATCH",
                        description=f"Read count mismatch for region {region}: inspector={inspector_reads}, coherence={coherence_reads}",
                        severity="MEDIUM",
                        suggested_fix="Synchronize access counters between inspector and coherence tracker",
                        data_points={
                            "region": region,
                            "inspector_reads": inspector_reads,
                            "coherence_reads": coherence_reads,
                            "difference": read_diff
                        }
                    ))
                    
                if write_diff > inspector_writes * 0.1:  # 10% threshold
                    anomalies.append(MemoryAnomaly(
                        timestamp=datetime.now().isoformat(),
                        anomaly_type="WRITE_COUNT_MISMATCH",
                        description=f"Write count mismatch for region {region}: inspector={inspector_writes}, coherence={coherence_writes}",
                        severity="MEDIUM",
                        suggested_fix="Synchronize access counters between inspector and coherence tracker",
                        data_points={
                            "region": region,
                            "inspector_writes": inspector_writes,
                            "coherence_writes": coherence_writes,
                            "difference": write_diff
                        }
                    ))
    
    def _check_timing_consistency(self, inspector_data: Dict, coherence_data: Dict, anomalies: List[MemoryAnomaly]):
        """Check for timing inconsistencies between systems"""
        inspector_timestamp = inspector_data.get('last_update', '')
        coherence_timestamp = coherence_data.get('last_update', '')
        
        if inspector_timestamp and coherence_timestamp:
            try:
                from datetime import datetime
                inspector_time = datetime.fromisoformat(inspector_timestamp.replace('Z', '+00:00'))
                coherence_time = datetime.fromisoformat(coherence_timestamp.replace('Z', '+00:00'))
                
                time_diff = abs((inspector_time - coherence_time).total_seconds())
                
                if time_diff > 5:  # 5 second threshold
                    anomalies.append(MemoryAnomaly(
                        timestamp=datetime.now().isoformat(),
                        anomaly_type="TIMING_MISMATCH",
                        description=f"Significant time difference between systems: {time_diff} seconds",
                        severity="LOW",
                        suggested_fix="Synchronize system clocks or implement time synchronization",
                        data_points={
                            "inspector_time": inspector_timestamp,
                            "coherence_time": coherence_timestamp,
                            "difference_seconds": time_diff
                        }
                    ))
            except ValueError:
                # Handle invalid timestamp formats
                anomalies.append(MemoryAnomaly(
                    timestamp=datetime.now().isoformat(),
                    anomaly_type="TIMESTAMP_PARSE_ERROR",
                    description="Could not parse timestamp formats for comparison",
                    severity="LOW",
                    suggested_fix="Ensure consistent timestamp formats between systems",
                    data_points={
                        "inspector_timestamp": inspector_timestamp,
                        "coherence_timestamp": coherence_timestamp
                    }
                ))
    
    def detect_memory_leaks(self, inspector_data: Dict) -> List[MemoryAnomaly]:
        """Detect potential memory leaks from inspector data"""
        anomalies = []
        regions = inspector_data.get('memory_regions', {})
        
        for region_name, region_data in regions.items():
            # Check for regions with high allocation but low deallocation
            allocations = region_data.get('allocations', 0)
            deallocations = region_data.get('deallocations', 0)
            
            if allocations > 0 and deallocations == 0:
                anomalies.append(MemoryAnomaly(
                    timestamp=datetime.now().isoformat(),
                    anomaly_type="POTENTIAL_MEMORY_LEAK",
                    description=f"Region {region_name} has {allocations} allocations but 0 deallocations",
                    severity="HIGH" if allocations > 100 else "MEDIUM",
                    suggested_fix="Ensure proper deallocation of memory regions or implement garbage collection",
                    data_points={
                        "region": region_name,
                        "allocations": allocations,
                        "deallocations": deallocations
                    }
                ))
            elif allocations > 0:
                leak_ratio = (allocations - deallocations) / allocations
                if leak_ratio > 0.9:  # 90% or more allocations not deallocated
                    anomalies.append(MemoryAnomaly(
                        timestamp=datetime.now().isoformat(),
                        anomaly_type="HIGH_LEAK_RATIO",
                        description=f"Region {region_name} has high leak ratio: {leak_ratio:.2%}",
                        severity="HIGH",
                        suggested_fix="Investigate deallocation patterns and implement cleanup routines",
                        data_points={
                            "region": region_name,
                            "allocations": allocations,
                            "deallocations": deallocations,
                            "leak_ratio": leak_ratio
                        }
                    ))
        
        return anomalies
    
    def detect_coherence_issues(self, coherence_data: Dict) -> List[MemoryAnomaly]:
        """Detect coherence-related issues"""
        anomalies = []
        tracked_regions = coherence_data.get('tracked_regions', {})
        
        for region_name, region_data in tracked_regions.items():
            coherence_violations = region_data.get('coherence