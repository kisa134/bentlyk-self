import psutil
import time
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from datetime import datetime
import threading
import json
import os
from typing import List, Dict, Tuple
import logging

class MemoryVisualizer:
    def __init__(self, process_name: str = None, pid: int = None, duration: int = 60, interval: int = 1):
        """
        Initialize the Memory Visualizer
        
        Args:
            process_name: Name of the process to monitor (optional)
            pid: Process ID to monitor (optional)
            duration: Duration to monitor in seconds
            interval: Interval between measurements in seconds
        """
        self.process_name = process_name
        self.pid = pid
        self.duration = duration
        self.interval = interval
        self.data = []
        self.timestamps = []
        self.memory_usage = []
        self.cpu_usage = []
        
        # Setup logging
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
        
        # Validate inputs
        if not process_name and not pid:
            self.logger.info("Monitoring system-wide memory usage")
            self.process = None
        else:
            self.process = self._get_process()
            
    def _get_process(self):
        """Get process object based on name or PID"""
        try:
            if self.pid:
                return psutil.Process(self.pid)
            elif self.process_name:
                for proc in psutil.process_iter(['pid', 'name']):
                    if proc.info['name'] == self.process_name:
                        return psutil.Process(proc.info['pid'])
                raise ValueError(f"Process '{self.process_name}' not found")
        except Exception as e:
            self.logger.error(f"Error getting process: {e}")
            return None
            
    def _collect_data(self):
        """Collect memory usage data"""
        try:
            if self.process:
                # Monitor specific process
                memory_info = self.process.memory_info()
                memory_percent = self.process.memory_percent()
                cpu_percent = self.process.cpu_percent()
                rss = memory_info.rss / (1024 * 1024)  # MB
                vms = memory_info.vms / (1024 * 1024)  # MB
            else:
                # Monitor system-wide
                memory = psutil.virtual_memory()
                memory_percent = memory.percent
                cpu_percent = psutil.cpu_percent()
                rss = memory.used / (1024 * 1024)  # MB
                vms = memory.total / (1024 * 1024)  # MB
                
            timestamp = datetime.now()
            
            self.data.append({
                'timestamp': timestamp,
                'rss_mb': rss,
                'vms_mb': vms,
                'memory_percent': memory_percent,
                'cpu_percent': cpu_percent
            })
            
            self.timestamps.append(timestamp)
            self.memory_usage.append(rss)
            self.cpu_usage.append(cpu_percent)
            
            self.logger.debug(f"Collected data: {rss:.2f} MB, {memory_percent:.2f}%")
            
        except Exception as e:
            self.logger.error(f"Error collecting data: {e}")
            
    def start_monitoring(self):
        """Start monitoring memory usage"""
        self.logger.info(f"Starting memory monitoring for {self.duration} seconds")
        
        start_time = time.time()
        while time.time() - start_time < self.duration:
            self._collect_data()
            time.sleep(self.interval)
            
        self.logger.info("Monitoring completed")
        
    def generate_report(self, output_dir: str = "memory_reports"):
        """Generate visual report of memory usage"""
        if not self.data:
            self.logger.warning("No data to generate report")
            return
            
        # Create output directory
        os.makedirs(output_dir, exist_ok=True)
        
        # Generate plots
        self._generate_memory_plot(output_dir)
        self._generate_cpu_plot(output_dir)
        self._generate_json_report(output_dir)
        
        self.logger.info(f"Report generated in {output_dir}")
        
    def _generate_memory_plot(self, output_dir: str):
        """Generate memory usage plot"""
        plt.figure(figsize=(12, 6))
        
        # Plot RSS memory usage
        plt.subplot(1, 2, 1)
        plt.plot(self.timestamps, self.memory_usage, 'b-', linewidth=1)
        plt.xlabel('Time')
        plt.ylabel('Memory Usage (MB)')
        plt.title('Memory Usage Over Time')
        plt.grid(True, alpha=0.3)
        plt.xticks(rotation=45)
        plt.gca().xaxis.set_major_formatter(mdates.DateFormatter('%H:%M:%S'))
        
        # Plot memory percentage
        plt.subplot(1, 2, 2)
        memory_percentages = [d['memory_percent'] for d in self.data]
        plt.plot(self.timestamps, memory_percentages, 'r-', linewidth=1)
        plt.xlabel('Time')
        plt.ylabel('Memory Usage (%)')
        plt.title('Memory Percentage Over Time')
        plt.grid(True, alpha=0.3)
        plt.xticks(rotation=45)
        plt.gca().xaxis.set_major_formatter(mdates.DateFormatter('%H:%M:%S'))
        
        plt.tight_layout()
        plt.savefig(os.path.join(output_dir, 'memory_usage.png'), dpi=300, bbox_inches='tight')
        plt.close()
        
    def _generate_cpu_plot(self, output_dir: str):
        """Generate CPU usage plot"""
        plt.figure(figsize=(10, 6))
        plt.plot(self.timestamps, self.cpu_usage, 'g-', linewidth=1)
        plt.xlabel('Time')
        plt.ylabel('CPU Usage (%)')
        plt.title('CPU Usage Over Time')
        plt.grid(True, alpha=0.3)
        plt.xticks(rotation=45)
        plt.gca().xaxis.set_major_formatter(mdates.DateFormatter('%H:%M:%S'))
        plt.tight_layout()
        plt.savefig(os.path.join(output_dir, 'cpu_usage.png'), dpi=300, bbox_inches='tight')
        plt.close()
        
    def _generate_json_report(self, output_dir: str):
        """Generate JSON report with raw data"""
        report_data = {
            'process_name': self.process_name,
            'pid': self.pid,
            'duration': self.duration,
            'interval': self.interval,
            'measurements': self.data,
            'summary': self._generate_summary()
        }
        
        with open(os.path.join(output_dir, 'memory_report.json'), 'w') as f:
            json.dump(report_data, f, indent=2, default=str)
            
    def _generate_summary(self) -> Dict:
        """Generate summary statistics"""
        if not self.memory_usage:
            return {}
            
        return {
            'total_measurements': len(self.memory_usage),
            'memory_usage_mb': {
                'min': round(min(self.memory_usage), 2),
                'max': round(max(self.memory_usage), 2),
                'average': round(sum(self.memory_usage) / len(self.memory_usage), 2),
                'peak_time': self.timestamps[self.memory_usage.index(max(self.memory_usage))].isoformat()
            },
            'memory_percentage': {
                'min': round(min([d['memory_percent'] for d in self.data]), 2),
                'max': round(max([d['memory_percent'] for d in self.data]), 2),
                'average': round(sum([d['memory_percent'] for d in self.data]) / len(self.data), 2)
            },
            'cpu_usage': {
                'min': round(min(self.cpu_usage), 2),
                'max': round(max(self.cpu_usage), 2),
                'average': round(sum(self.cpu_usage) / len(self.cpu_usage), 2)
            }
        }
        
    def identify_optimizations(self) -> List[str]:
        """Identify potential memory optimization suggestions"""
        suggestions = []
        
        if not self.data:
            return suggestions
            
        # Check for memory leaks (continuously increasing memory)
        memory_trend = self._calculate_trend(self.memory_usage)
        if memory_trend > 0.1:  # Positive trend indicates increasing memory
            suggestions.append("Potential memory leak detected - memory usage is consistently increasing")
            
        # Check for high memory usage
        avg_memory = sum(self.memory_usage) / len(self.memory_usage)
        max_memory = max(self.memory_usage)
        if max_memory > avg_memory * 2:
            suggestions.append("Significant memory spikes detected - consider optimizing memory allocation")
            
        # Check for high CPU usage correlation
        if len(self.cpu_usage) > 1:
            # Calculate correlation between CPU and memory usage
            correlation = self._calculate_correlation(self.cpu_usage, self.memory_usage)
            if abs(correlation) > 0.7:
                suggestions.append("High correlation between CPU and memory usage - investigate potential bottlenecks")
                
        # Check for inefficient memory patterns
        memory_variance = sum((x - avg_memory) ** 2 for x in self.memory_usage) / len(self.memory_usage)
        if memory_variance > (avg_memory * 0.5) ** 2:  # High variance indicates inefficient usage
            suggestions.append("High memory usage variance - consider implementing memory pooling or caching strategies")
            
        return suggestions
        
    def _calculate_trend(self, values: List[float]) -> float:
        """Calculate linear trend of values"""
        if len(values) < 2:
            return 0