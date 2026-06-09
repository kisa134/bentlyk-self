import logging
import time
from collections import defaultdict, deque
from dataclasses import dataclass, asdict
from typing import Dict, List, Optional, Tuple
from statistics import stdev, mean

@dataclass
class FragmentationEvent:
    timestamp: float
    cycle_id: str
    allocation_spread: float
    time_gap_variance: float
    severity: str
    details: Dict

class FragmentationDetector:
    def __init__(self, 
                 spread_threshold: float = 0.7,
                 time_gap_threshold: float = 0.1,
                 window_size: int = 100):
        self.spread_threshold = spread_threshold
        self.time_gap_threshold = time_gap_threshold
        self.window_size = window_size
        
        self.allocations = defaultdict(deque)
        self.write_times = defaultdict(list)
        self.events = []
        self.cycle_count = 0
        
        self.logger = logging.getLogger(__name__)
        self._setup_logging()

    def _setup_logging(self):
        handler = logging.StreamHandler()
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        handler.setFormatter(formatter)
        self.logger.addHandler(handler)
        self.logger.setLevel(logging.INFO)

    def record_allocation(self, address: int, size: int, contour_id: str, cycle_id: Optional[str] = None):
        if cycle_id is None:
            cycle_id = f"cycle_{self.cycle_count}"
            
        timestamp = time.time()
        self.allocations[cycle_id].append((address, size, contour_id, timestamp))
        
        if len(self.allocations[cycle_id]) > self.window_size:
            self.allocations[cycle_id].popleft()

    def record_write(self, address: int, timestamp: Optional[float] = None):
        if timestamp is None:
            timestamp = time.time()
        self.write_times[address].append(timestamp)

    def analyze_fragmentation(self, cycle_id: Optional[str] = None) -> Optional[FragmentationEvent]:
        if cycle_id is None:
            cycle_id = f"cycle_{self.cycle_count}"
            
        if cycle_id not in self.allocations or len(self.allocations[cycle_id]) < 2:
            return None

        allocations = list(self.allocations[cycle_id])
        spread = self._calculate_allocation_spread(allocations)
        time_gaps = self._calculate_time_gap_variance(allocations)
        
        if spread > self.spread_threshold or time_gaps > self.time_gap_threshold:
            severity = self._determine_severity(spread, time_gaps)
            event = FragmentationEvent(
                timestamp=time.time(),
                cycle_id=cycle_id,
                allocation_spread=spread,
                time_gap_variance=time_gaps,
                severity=severity,
                details={
                    'allocation_count': len(allocations),
                    'contour_distribution': self._get_contour_distribution(allocations)
                }
            )
            self.events.append(event)
            self._log_fragmentation_event(event)
            return event
            
        return None

    def _calculate_allocation_spread(self, allocations: List[Tuple]) -> float:
        if len(allocations) < 2:
            return 0.0
            
        addresses = [addr for addr, _, _, _ in allocations]
        address_range = max(addresses) - min(addresses)
        
        if address_range == 0:
            return 0.0
            
        # Calculate density of allocations across the address space
        sorted_addrs = sorted(addresses)
        gaps = [sorted_addrs[i+1] - sorted_addrs[i] for i in range(len(sorted_addrs)-1)]
        
        if not gaps:
            return 0.0
            
        try:
            gap_std = stdev(gaps) if len(gaps) > 1 else 0
            gap_mean = mean(gaps)
            return min(gap_std / gap_mean if gap_mean > 0 else 0, 1.0)
        except:
            return 0.0

    def _calculate_time_gap_variance(self, allocations: List[Tuple]) -> float:
        if len(allocations) < 3:
            return 0.0
            
        timestamps = [ts for _, _, _, ts in allocations]
        sorted_times = sorted(timestamps)
        gaps = [sorted_times[i+1] - sorted_times[i] for i in range(len(sorted_times)-1)]
        
        if len(gaps) < 2:
            return 0.0
            
        try:
            gap_std = stdev(gaps)
            gap_mean = mean(gaps)
            return gap_std / gap_mean if gap_mean > 0 else 0
        except:
            return 0.0

    def _get_contour_distribution(self, allocations: List[Tuple]) -> Dict[str, int]:
        contour_counts = defaultdict(int)
        for _, _, contour_id, _ in allocations:
            contour_counts[contour_id] += 1
        return dict(contour_counts)

    def _determine_severity(self, spread: float, time_gaps: float) -> str:
        if spread > self.spread_threshold * 1.5 or time_gaps > self.time_gap_threshold * 1.5:
            return "CRITICAL"
        elif spread > self.spread_threshold or time_gaps > self.time_gap_threshold:
            return "WARNING"
        return "INFO"

    def _log_fragmentation_event(self, event: FragmentationEvent):
        log_data = asdict(event)
        self.logger.warning(f"Fragmentation detected: {log_data}")

    def start_new_cycle(self):
        self.cycle_count += 1
        cycle_id = f"cycle_{self.cycle_count}"
        self.allocations[cycle_id] = deque()
        return cycle_id

    def get_recent_events(self, limit: int = 10) -> List[FragmentationEvent]:
        return self.events[-limit:] if self.events else []

    def reset(self):
        self.allocations.clear()
        self.write_times.clear()
        self.events.clear()
        self.cycle_count = 0