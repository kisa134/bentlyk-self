import sys
import threading
import time
import heapq
from collections import defaultdict, deque
from dataclasses import dataclass
from typing import Dict, List, Tuple, Optional, Set
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.animation import FuncAnimation
from matplotlib.colors import LinearSegmentedColormap

@dataclass
class AllocationRecord:
    ptr: int
    size: int
    timestamp: float
    stack_trace: List[str]
    lifetime: float = 0.0
    freed: bool = False

class MemoryFragmentationAnalyzer:
    def __init__(self, max_records: int = 10000):
        self.max_records = max_records
        self.allocations: Dict[int, AllocationRecord] = {}
        self.allocation_history = deque(maxlen=max_records)
        self.fragmentation_map: Dict[Tuple[int, int], int] = defaultdict(int)
        self.size_distribution: Dict[int, int] = defaultdict(int)
        self.lifetime_stats: List[float] = []
        self.lock = threading.RLock()
        self.stats = {
            'total_allocated': 0,
            'total_freed': 0,
            'peak_memory': 0,
            'fragmentation_ratio': 0.0,
            'allocation_count': 0,
            'free_count': 0
        }
        self.heatmap_data = np.zeros((50, 50))
        self.time_series = deque(maxlen=100)
        self.start_time = time.time()
        
    def malloc_hook(self, ptr: int, size: int, stack_trace: List[str]):
        """Hook for memory allocation calls"""
        with self.lock:
            timestamp = time.time() - self.start_time
            record = AllocationRecord(
                ptr=ptr,
                size=size,
                timestamp=timestamp,
                stack_trace=stack_trace
            )
            self.allocations[ptr] = record
            self.allocation_history.append(record)
            self.stats['total_allocated'] += size
            self.stats['allocation_count'] += 1
            self.size_distribution[size] += 1
            current_usage = self.stats['total_allocated'] - self.stats['total_freed']
            if current_usage > self.stats['peak_memory']:
                self.stats['peak_memory'] = current_usage
                
    def free_hook(self, ptr: int):
        """Hook for memory deallocation calls"""
        with self.lock:
            if ptr in self.allocations:
                record = self.allocations[ptr]
                record.freed = True
                record.lifetime = time.time() - self.start_time - record.timestamp
                self.lifetime_stats.append(record.lifetime)
                self.stats['total_freed'] += record.size
                self.stats['free_count'] += 1
                del self.allocations[ptr]
                
    def calculate_fragmentation(self) -> float:
        """Calculate current fragmentation ratio"""
        if self.stats['total_allocated'] == 0:
            return 0.0
        allocated = self.stats['total_allocated']
        freed = self.stats['total_freed']
        current_usage = allocated - freed
        if current_usage == 0:
            return 0.0
        # Simplified fragmentation calculation
        return min(1.0, (allocated - current_usage) / allocated)
    
    def update_fragmentation_map(self):
        """Update the fragmentation heatmap data"""
        with self.lock:
            # Clear existing map
            self.fragmentation_map.clear()
            
            # Rebuild map based on current allocations
            active_allocs = list(self.allocations.values())
            if not active_allocs:
                self.heatmap_data = np.zeros((50, 50))
                return
                
            # Sort by size for better visualization
            active_allocs.sort(key=lambda x: x.size, reverse=True)
            
            # Create a simplified 2D representation
            for i, alloc in enumerate(active_allocs[:2500]):  # Limit for performance
                x = i % 50
                y = i // 50
                if y < 50:
                    self.heatmap_data[y, x] = np.log(alloc.size + 1)
                    
            self.stats['fragmentation_ratio'] = self.calculate_fragmentation()
            current_time = time.time() - self.start_time
            self.time_series.append((current_time, self.stats['fragmentation_ratio']))
            
    def suggest_compaction(self) -> List[str]:
        """Suggest optimal compaction strategies"""
        suggestions = []
        
        with self.lock:
            if len(self.lifetime_stats) > 10:
                avg_lifetime = sum(self.lifetime_stats) / len(self.lifetime_stats)
                if avg_lifetime < 1.0:  # Short-lived objects
                    suggestions.append("Implement object pooling for short-lived allocations")
                    
            # Size-based suggestions
            if self.size_distribution:
                small_allocs = sum(1 for size, count in self.size_distribution.items() if size < 64)
                total_allocs = sum(self.size_distribution.values())
                if small_allocs / total_allocs > 0.7:
                    suggestions.append("Consider using slab allocation for small objects (<64 bytes)")
                    
            fragmentation = self.stats['fragmentation_ratio']
            if fragmentation > 0.3:
                suggestions.append(f"High fragmentation detected ({fragmentation:.1%}). Consider periodic compaction")
                
            if self.stats['allocation_count'] > self.stats['free_count'] * 2:
                suggestions.append("Allocation rate exceeds deallocation rate. Check for memory leaks")
                
        return suggestions
    
    def get_statistics(self) -> Dict:
        """Get current memory statistics"""
        with self.lock:
            return self.stats.copy()
    
    def get_size_distribution(self) -> Dict[int, int]:
        """Get allocation size distribution"""
        with self.lock:
            return dict(self.size_distribution)
    
    def get_heatmap_data(self) -> np.ndarray:
        """Get current heatmap data"""
        with self.lock:
            return self.heatmap_data.copy()

class MemoryVisualizer:
    def __init__(self, analyzer: MemoryFragmentationAnalyzer):
        self.analyzer = analyzer
        self.fig, ((self.ax1, self.ax2), (self.ax3, self.ax4)) = plt.subplots(2, 2, figsize=(15, 10))
        self.fig.suptitle('Memory Fragmentation Analyzer', fontsize=16)
        
        # Custom colormap for heatmap
        colors = ['black', 'blue', 'green', 'yellow', 'red']
        self.cmap = LinearSegmentedColormap.from_list('fragmentation', colors, N=256)
        
        self.ani = None
        
    def update_visualization(self, frame):
        """Update all visualization components"""
        self.analyzer.update_fragmentation_map()
        stats = self.analyzer.get_statistics()
        
        # Clear all axes
        self.ax1.clear()
        self.ax2.clear()
        self.ax3.clear()
        self.ax4.clear()
        
        # Heatmap
        data = self.analyzer.get_heatmap_data()
        im = self.ax1.imshow(data, cmap=self.cmap, aspect='auto', interpolation='nearest')
        self.ax1.set_title('Fragmentation Heatmap')
        self.ax1.set_xlabel('Memory Blocks')
        self.ax1.set_ylabel('Allocation Groups')
        
        # Add colorbar
        if frame == 0:  # Only add once
            plt.colorbar(im, ax=self.ax1)
        
        # Statistics text
        stat_text = f"""Memory Statistics:
Total Allocated: {stats['total_allocated']:,} bytes
Total Freed: {stats['total_freed']:,} bytes
Current Usage: {stats['total_allocated'] - stats['total_freed']:,} bytes
Peak Memory: {stats['peak_memory']:,} bytes
Fragmentation: {stats['fragmentation_ratio']:.1%}
Allocations: {stats['allocation_count']:,}
Frees: {stats['free_count']:,}"""
        self.ax2.text(0.05, 0.95, stat_text, transform=self.ax2.transAxes, 
                      fontsize=10, verticalalignment='top', fontfamily='monospace')
        self.ax2.set_title('Memory Statistics')
        self.ax2.axis('off')
        
        # Size distribution (simplified)
        size_dist = self.analyzer.get_size_distribution()
        if size_dist:
            sizes = list(size_dist.keys())[:20]  # Top 20 sizes
            counts = [size_dist[s] for s in sizes]
            self.ax3.bar(range(len(sizes)), counts)
            self.ax3.set_title('Top Allocation Sizes')
            self.ax3.set_xlabel('Size Rank')
            self.ax3.set_ylabel('Count')
            self.ax3.set_xticks(range(0, len(sizes), max(1, len(sizes)//5)))
        
        # Fragmentation over time
        if self.analyzer.time_series:
            times, fragmentations = zip(*self.analyzer.time_series)
            self.ax4.plot(times, fragmentations, 'r-', linewidth=2)
            self.ax4.set_title('Fragmentation Over Time')
            self.ax4.set_xlabel('Time (s)')
            self.ax4.set_ylabel('Fragmentation Ratio')
            self.ax4.set_ylim(0, 1)
            self.ax4.grid(True)
        
        # Suggestions
        suggestions = self.analyzer.suggest_compaction()
        if suggestions:
            suggestion_text = "Optimization