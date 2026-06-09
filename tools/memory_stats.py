import sys
import time
import json
import threading
from collections import defaultdict, deque
from dataclasses import dataclass, asdict
from typing import Dict, List, Optional, Tuple
import matplotlib.pyplot as plt
import numpy as np
from datetime import datetime

@dataclass
class MemoryAccessEvent:
    timestamp: float
    address: int
    size: int
    is_hit: bool
    retrieval_time: float
    contour_id: Optional[str] = None

@dataclass
class CacheMetrics:
    hit_rate: float
    average_retrieval_time: float
    total_accesses: int
    hit_count: int
    miss_count: int

class MemoryStatsCollector:
    def __init__(self, window_size: int = 10000):
        self.window_size = window_size
        self.events: deque[MemoryAccessEvent] = deque(maxlen=window_size)
        self.lock = threading.Lock()
        self.contour_access_count: Dict[str, int] = defaultdict(int)
        self.access_times: List[float] = []
        self.hit_times: List[float] = []
        self.miss_times: List[float] = []
        
    def record_access(self, event: MemoryAccessEvent):
        with self.lock:
            self.events.append(event)
            self.access_times.append(event.retrieval_time)
            
            if event.contour_id:
                self.contour_access_count[event.contour_id] += 1
                
            if event.is_hit:
                self.hit_times.append(event.retrieval_time)
            else:
                self.miss_times.append(event.retrieval_time)
    
    def get_current_metrics(self) -> CacheMetrics:
        with self.lock:
            if not self.events:
                return CacheMetrics(0.0, 0.0, 0, 0, 0)
            
            total = len(self.events)
            hits = sum(1 for e in self.events if e.is_hit)
            misses = total - hits
            
            hit_rate = hits / total if total > 0 else 0.0
            avg_time = sum(e.retrieval_time for e in self.events) / total if total > 0 else 0.0
            
            return CacheMetrics(
                hit_rate=hit_rate,
                average_retrieval_time=avg_time,
                total_accesses=total,
                hit_count=hits,
                miss_count=misses
            )
    
    def get_top_contours(self, n: int = 10) -> List[Tuple[str, int]]:
        with self.lock:
            sorted_contours = sorted(
                self.contour_access_count.items(), 
                key=lambda x: x[1], 
                reverse=True
            )
            return sorted_contours[:n]
    
    def get_retrieval_time_stats(self) -> Dict[str, List[float]]:
        with self.lock:
            return {
                'all': list(self.access_times)[-1000:],  # Last 1000 for performance
                'hits': list(self.hit_times)[-1000:],
                'misses': list(self.miss_times)[-1000:]
            }

class MemoryStatsVisualizer:
    def __init__(self, collector: MemoryStatsCollector):
        self.collector = collector
        plt.ion()
        
    def plot_hit_rate_trend(self, historical_data: List[Tuple[float, float]]):
        if not historical_data:
            return
            
        times, rates = zip(*historical_data)
        plt.figure(figsize=(10, 6))
        plt.plot(times, rates, 'b-', linewidth=2)
        plt.xlabel('Time (seconds)')
        plt.ylabel('Hit Rate')
        plt.title('Cache Hit Rate Trend')
        plt.grid(True, alpha=0.3)
        plt.ylim(0, 1)
        plt.tight_layout()
        plt.savefig('cache_hit_rate_trend.png')
        plt.close()
    
    def plot_retrieval_time_distribution(self):
        stats = self.collector.get_retrieval_time_stats()
        if not any(stats.values()):
            return
            
        plt.figure(figsize=(12, 8))
        
        plt.subplot(2, 2, 1)
        if stats['all']:
            plt.hist(stats['all'], bins=50, alpha=0.7, color='blue')
            plt.xlabel('Retrieval Time (ms)')
            plt.ylabel('Frequency')
            plt.title('All Access Times')
            plt.grid(True, alpha=0.3)
        
        plt.subplot(2, 2, 2)
        if stats['hits']:
            plt.hist(stats['hits'], bins=50, alpha=0.7, color='green')
            plt.xlabel('Retrieval Time (ms)')
            plt.ylabel('Frequency')
            plt.title('Hit Access Times')
            plt.grid(True, alpha=0.3)
        
        plt.subplot(2, 2, 3)
        if stats['misses']:
            plt.hist(stats['misses'], bins=50, alpha=0.7, color='red')
            plt.xlabel('Retrieval Time (ms)')
            plt.ylabel('Frequency')
            plt.title('Miss Access Times')
            plt.grid(True, alpha=0.3)
        
        plt.subplot(2, 2, 4)
        data = [stats['hits'], stats['misses']]
        labels = ['Hits', 'Misses']
        colors = ['green', 'red']
        filtered_data = [d for d in data if d]
        filtered_labels = [labels[i] for i, d in enumerate(data) if d]
        filtered_colors = [colors[i] for i, d in enumerate(data) if d]
        
        if filtered_data:
            plt.boxplot(filtered_data, labels=filtered_labels, patch_artist=True)
            for patch, color in zip(plt.gca().artists, filtered_colors):
                patch.set_facecolor(color)
            plt.ylabel('Retrieval Time (ms)')
            plt.title('Retrieval Time Comparison')
            plt.grid(True, alpha=0.3)
        
        plt.tight_layout()
        plt.savefig('retrieval_time_distribution.png')
        plt.close()
    
    def plot_top_contours(self):
        top_contours = self.collector.get_top_contours(15)
        if not top_contours:
            return
            
        contours, counts = zip(*top_contours)
        
        plt.figure(figsize=(12, 8))
        y_pos = np.arange(len(contours))
        plt.barh(y_pos, counts, color='skyblue')
        plt.yticks(y_pos, contours)
        plt.xlabel('Access Count')
        plt.title('Top 15 Most Accessed Memory Contours')
        plt.gca().invert_yaxis()
        plt.tight_layout()
        plt.savefig('top_memory_contours.png')
        plt.close()

class MemoryStatsRecorder:
    def __init__(self, collector: MemoryStatsCollector):
        self.collector = collector
        self.historical_hit_rates: List[Tuple[float, float]] = []
        self.start_time = time.time()
        self.running = True
        
    def record_periodically(self, interval: float = 5.0):
        while self.running:
            time.sleep(interval)
            metrics = self.collector.get_current_metrics()
            current_time = time.time() - self.start_time
            self.historical_hit_rates.append((current_time, metrics.hit_rate))
            
            # Log to console
            print(f"[{datetime.now().strftime('%H:%M:%S')}] "
                  f"Hit Rate: {metrics.hit_rate:.3f}, "
                  f"Avg Time: {metrics.average_retrieval_time:.2f}ms, "
                  f"Accesses: {metrics.total_accesses}")
    
    def save_historical_data(self, filename: str = "memory_stats_history.json"):
        data = {
            "historical_hit_rates": self.historical_hit_rates,
            "final_metrics": asdict(self.collector.get_current_metrics()),
            "top_contours": self.collector.get_top_contours(20)
        }
        
        with open(filename, 'w') as f:
            json.dump(data, f, indent=2)

def simulate_memory_accesses(collector: MemoryStatsCollector, duration: int = 60):
    """Simulate memory accesses for testing purposes"""
    import random
    
    start_time = time.time()
    address_counter = 0
    
    # Create some frequently accessed "hot" addresses
    hot_addresses = list(range(0, 1000, 8))
    
    while time.time() - start_time < duration:
        # 70% chance to access hot addresses
        if random.random() < 0.7:
            address = random.choice(hot_addresses)
        else:
            address = address_counter * 8
            address_counter += 1
            
        # Simulate varying access patterns
        is_hit = random.random() < 0.85  # 85% hit rate
        retrieval_time = random.uniform(0.1, 10.0) if is_hit else random.uniform(5.0, 50.0)
        
        # Assign contour IDs based on address ranges
        contour_id = f"contour_{address // 1000}"
        
        event = MemoryAccessEvent(
            timestamp=time.time(),
            address=address,
            size=random.choice([4, 8, 16, 32]),
            is_hit=is_hit,
            retrieval_time=retrieval_time,