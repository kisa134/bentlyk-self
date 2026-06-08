import json
import csv
import os
import datetime
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from typing import Dict, List, Optional
from dataclasses import dataclass, asdict
from dateutil import parser

@dataclass
class MoodEntry:
    timestamp: str
    energy: float
    pain: float
    surprise: float
    distrust: float
    curiosity: float
    attachment: float
    coherence: float

class MoodTracker:
    def __init__(self, data_file: str = "mood_data.json"):
        self.data_file = data_file
        self.entries: List[MoodEntry] = []
        self.load_data()

    def load_data(self):
        """Load historical mood data from file."""
        if os.path.exists(self.data_file):
            try:
                with open(self.data_file, 'r') as f:
                    data = json.load(f)
                    self.entries = [MoodEntry(**entry) for entry in data]
            except (json.JSONDecodeError, KeyError):
                print(f"Warning: Could not load data from {self.data_file}. Starting fresh.")
                self.entries = []
        else:
            self.entries = []

    def save_data(self):
        """Save mood data to file."""
        with open(self.data_file, 'w') as f:
            json.dump([asdict(entry) for entry in self.entries], f, indent=2)

    def add_entry(self, energy: float, pain: float, surprise: float, 
                  distrust: float, curiosity: float, attachment: float, 
                  coherence: float, timestamp: Optional[str] = None):
        """Add a new mood entry."""
        if timestamp is None:
            timestamp = datetime.datetime.now().isoformat()
        
        entry = MoodEntry(
            timestamp=timestamp,
            energy=energy,
            pain=pain,
            surprise=surprise,
            distrust=distrust,
            curiosity=curiosity,
            attachment=attachment,
            coherence=coherence
        )
        
        self.entries.append(entry)
        self.save_data()

    def export_to_csv(self, filename: str = "mood_data.csv"):
        """Export data to CSV format."""
        with open(filename, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=MoodEntry.__dataclass_fields__.keys())
            writer.writeheader()
            for entry in self.entries:
                writer.writerow(asdict(entry))

    def visualize_trends(self, save_plot: bool = True, show_plot: bool = False, 
                        output_dir: str = "plots"):
        """Generate and save visualizations of mood trends."""
        if not self.entries:
            print("No data to visualize.")
            return

        # Create output directory if it doesn't exist
        if save_plot and not os.path.exists(output_dir):
            os.makedirs(output_dir)

        # Parse timestamps
        timestamps = [parser.isoparse(entry.timestamp) for entry in self.entries]
        
        # Create plots
        self._plot_individual_metrics(timestamps, save_plot, show_plot, output_dir)
        self._plot_composite_metrics(timestamps, save_plot, show_plot, output_dir)
        self._plot_coherence_trend(timestamps, save_plot, show_plot, output_dir)

    def _plot_individual_metrics(self, timestamps, save_plot, show_plot, output_dir):
        """Plot individual mood metrics."""
        fig, axes = plt.subplots(3, 2, figsize=(15, 12))
        fig.suptitle('Individual Mood Metrics Over Time', fontsize=16)
        
        metrics = ['energy', 'pain', 'surprise', 'distrust', 'curiosity', 'attachment']
        positions = [(0,0), (0,1), (1,0), (1,1), (2,0), (2,1)]
        
        for metric, (row, col) in zip(metrics, positions):
            values = [getattr(entry, metric) for entry in self.entries]
            axes[row, col].plot(timestamps, values, marker='o', linestyle='-')
            axes[row, col].set_title(metric.capitalize())
            axes[row, col].set_ylabel('Value')
            axes[row, col].grid(True)
            axes[row, col].xaxis.set_major_formatter(mdates.DateFormatter('%m-%d'))
            axes[row, col].xaxis.set_major_locator(mdates.DayLocator())
            plt.setp(axes[row, col].xaxis.get_majorticklabels(), rotation=45)
        
        plt.tight_layout()
        
        if save_plot:
            plt.savefig(os.path.join(output_dir, 'individual_metrics.png'), dpi=300, bbox_inches='tight')
        if show_plot:
            plt.show()
        else:
            plt.close()

    def _plot_composite_metrics(self, timestamps, save_plot, show_plot, output_dir):
        """Plot composite metrics (positive vs negative)."""
        fig, ax = plt.subplots(figsize=(12, 8))
        
        positive_metrics = [getattr(entry, 'energy') + getattr(entry, 'curiosity') + getattr(entry, 'surprise') 
                           for entry in self.entries]
        negative_metrics = [getattr(entry, 'pain') + getattr(entry, 'distrust') + getattr(entry, 'attachment') 
                           for entry in self.entries]
        
        ax.plot(timestamps, positive_metrics, marker='o', linestyle='-', label='Positive Metrics (Energy+Curiosity+Surprise)', color='green')
        ax.plot(timestamps, negative_metrics, marker='s', linestyle='-', label='Negative Metrics (Pain+Distrust+Attachment)', color='red')
        
        ax.set_title('Composite Mood Metrics Over Time')
        ax.set_ylabel('Combined Value')
        ax.legend()
        ax.grid(True)
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%m-%d'))
        ax.xaxis.set_major_locator(mdates.DayLocator())
        plt.setp(ax.xaxis.get_majorticklabels(), rotation=45)
        
        plt.tight_layout()
        
        if save_plot:
            plt.savefig(os.path.join(output_dir, 'composite_metrics.png'), dpi=300, bbox_inches='tight')
        if show_plot:
            plt.show()
        else:
            plt.close()

    def _plot_coherence_trend(self, timestamps, save_plot, show_plot, output_dir):
        """Plot coherence trend."""
        fig, ax = plt.subplots(figsize=(12, 6))
        
        coherence_values = [getattr(entry, 'coherence') for entry in self.entries]
        ax.plot(timestamps, coherence_values, marker='o', linestyle='-', color='purple', linewidth=2, markersize=6)
        
        ax.set_title('Coherence Trend Over Time', fontsize=16)
        ax.set_ylabel('Coherence')
        ax.grid(True, alpha=0.3)
        ax.xaxis.set_major_formatter(mdates.DateFormatter('%m-%d'))
        ax.xaxis.set_major_locator(mdates.DayLocator())
        plt.setp(ax.xaxis.get_majorticklabels(), rotation=45)
        
        plt.tight_layout()
        
        if save_plot:
            plt.savefig(os.path.join(output_dir, 'coherence_trend.png'), dpi=300, bbox_inches='tight')
        if show_plot:
            plt.show()
        else:
            plt.close()

def main():
    """Main function to demonstrate the mood tracker."""
    tracker = MoodTracker()
    
    # Example: Add some sample data (in a real application, you would collect this from user input or sensors)
    sample_data = [
        (7.5, 2.0, 5.0, 3.0, 8.0, 4.0, 6.5),
        (6.0, 3.5, 4.0, 4.5, 7.0, 5.0, 5.0),
        (8.0, 1.5, 6.0, 2.0, 9.0, 3.0, 7.5),
        (5.5, 4.0, 3.5, 5.0, 6.5, 6.0, 4.0),
        (7.0, 2.5, 5.5, 3.5, 8.5, 4.5, 6.0)
    ]
    
    # Add sample entries with different timestamps
    base_time = datetime.datetime.now() - datetime.timedelta(days=4)
    for i, data in enumerate(sample_data):
        timestamp = (base_time + datetime.timedelta(days=i)).isoformat()
        tracker.add_entry(*data, timestamp=timestamp)
    
    # Export to CSV
    tracker.export_to_csv()
    
    # Generate visualizations
    tracker.visualize_trends(save_plot=True, show_plot=False)
    
    print("Mood tracking complete. Check the 'plots' directory for visualizations.")

if __name__ == "__main__":
    main()