import networkx as nx
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.widgets import Slider, Button, RadioButtons
import matplotlib.patches as mpatches
from collections import defaultdict
import json
from datetime import datetime, timedelta
import random

class MemoryVisualizer:
    def __init__(self):
        self.graph = nx.Graph()
        self.memories = []
        self.access_logs = []
        self.current_filter = "all"
        self.setup_sample_data()
        self.setup_figure()
        
    def setup_sample_data(self):
        # Sample memory data
        contours = ["episodic", "semantic", "procedural", "emotional"]
        nodes = []
        edges = []
        
        # Create nodes
        for i in range(50):
            node = {
                'id': f'mem_{i}',
                'content': f'Memory content {i}',
                'strength': random.uniform(0.1, 1.0),
                'contour': random.choice(contours),
                'created_at': datetime.now() - timedelta(days=random.randint(0, 365)),
                'retention_duration': random.randint(1, 365)
            }
            nodes.append(node)
            self.graph.add_node(node['id'], **node)
            
        # Create edges with connection strengths
        for i in range(100):
            source = random.choice(nodes)['id']
            target = random.choice(nodes)['id']
            if source != target and not self.graph.has_edge(source, target):
                strength = random.uniform(0.1, 1.0)
                self.graph.add_edge(source, target, weight=strength)
                
        # Generate access logs
        for _ in range(500):
            memory_id = random.choice(nodes)['id']
            access_time = datetime.now() - timedelta(hours=random.randint(0, 24*30))
            self.access_logs.append({
                'memory_id': memory_id,
                'timestamp': access_time,
                'frequency': random.randint(1, 10)
            })
            
        self.memories = nodes
        
    def setup_figure(self):
        self.fig = plt.figure(figsize=(16, 12))
        self.fig.suptitle('Memory Graph Visualization', fontsize=16)
        
        # Main graph subplot
        self.ax_graph = plt.subplot2grid((3, 4), (0, 0), colspan=2, rowspan=2)
        
        # Heatmap subplot
        self.ax_heatmap = plt.subplot2grid((3, 4), (0, 2), colspan=2)
        
        # Timeline subplot
        self.ax_timeline = plt.subplot2grid((3, 4), (1, 2), colspan=2)
        
        # Controls
        self.ax_filter = plt.axes([0.1, 0.02, 0.2, 0.05])
        self.ax_refresh = plt.axes([0.75, 0.02, 0.1, 0.05])
        
        # Filter radio buttons
        self.radio_filter = RadioButtons(self.ax_filter, ('all', 'episodic', 'semantic', 'procedural', 'emotional'))
        self.radio_filter.on_clicked(self.update_filter)
        
        # Refresh button
        self.btn_refresh = Button(self.ax_refresh, 'Refresh')
        self.btn_refresh.on_clicked(self.refresh_visualization)
        
        self.draw_visualizations()
        
    def update_filter(self, label):
        self.current_filter = label
        self.draw_visualizations()
        
    def refresh_visualization(self, event):
        self.draw_visualizations()
        
    def filter_memories(self):
        if self.current_filter == "all":
            return self.memories
        return [m for m in self.memories if m['contour'] == self.current_filter]
        
    def draw_graph(self):
        self.ax_graph.clear()
        
        # Filter nodes
        filtered_memories = self.filter_memories()
        filtered_ids = [m['id'] for m in filtered_memories]
        
        # Create subgraph with filtered nodes
        subgraph = self.graph.subgraph(filtered_ids)
        
        # Node positions
        pos = nx.spring_layout(subgraph, k=2, iterations=50)
        
        # Draw nodes with color based on contour
        contour_colors = {
            'episodic': '#FF6B6B',
            'semantic': '#4ECDC4',
            'procedural': '#45B7D1',
            'emotional': '#96CEB4'
        }
        
        node_colors = []
        node_sizes = []
        for node in subgraph.nodes():
            memory = self.graph.nodes[node]
            node_colors.append(contour_colors.get(memory['contour'], '#CCCCCC'))
            node_sizes.append(memory['strength'] * 300)
            
        nx.draw_networkx_nodes(subgraph, pos, 
                              node_color=node_colors,
                              node_size=node_sizes,
                              alpha=0.7,
                              ax=self.ax_graph)
        
        # Draw edges with width based on strength
        edge_widths = [subgraph[u][v]['weight'] * 3 for u, v in subgraph.edges()]
        nx.draw_networkx_edges(subgraph, pos,
                              width=edge_widths,
                              alpha=0.5,
                              ax=self.ax_graph)
        
        # Add legend
        legend_elements = [mpatches.Patch(color=color, label=contour) 
                          for contour, color in contour_colors.items()]
        self.ax_graph.legend(handles=legend_elements, loc='upper right')
        
        self.ax_graph.set_title('Memory Connection Graph')
        self.ax_graph.axis('off')
        
    def draw_heatmap(self):
        self.ax_heatmap.clear()
        
        # Filter memories
        filtered_memories = self.filter_memories()
        filtered_ids = [m['id'] for m in filtered_memories]
        
        # Create access frequency matrix
        access_data = defaultdict(lambda: defaultdict(int))
        for log in self.access_logs:
            if log['memory_id'] in filtered_ids:
                hour = log['timestamp'].hour
                day = log['timestamp'].weekday()
                access_data[day][hour] += log['frequency']
                
        # Convert to matrix
        matrix = np.zeros((7, 24))
        for day in range(7):
            for hour in range(24):
                matrix[day][hour] = access_data[day][hour]
                
        # Create heatmap
        im = self.ax_heatmap.imshow(matrix, cmap='YlOrRd', aspect='auto')
        
        # Set labels
        self.ax_heatmap.set_xticks(range(0, 24, 4))
        self.ax_heatmap.set_xticklabels([f'{i}:00' for i in range(0, 24, 4)])
        self.ax_heatmap.set_yticks(range(7))
        self.ax_heatmap.set_yticklabels(['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'])
        
        self.ax_heatmap.set_title('Access Frequency Heatmap')
        self.ax_heatmap.set_xlabel('Hour of Day')
        self.ax_heatmap.set_ylabel('Day of Week')
        
        # Add colorbar
        plt.colorbar(im, ax=self.ax_heatmap)
        
    def draw_timeline(self):
        self.ax_timeline.clear()
        
        # Filter memories
        filtered_memories = self.filter_memories()
        
        # Group by creation date
        creation_dates = [m['created_at'].date() for m in filtered_memories]
        date_counts = defaultdict(int)
        for date in creation_dates:
            date_counts[date] += 1
            
        # Sort dates
        sorted_dates = sorted(date_counts.keys())
        counts = [date_counts[date] for date in sorted_dates]
        
        # Plot timeline
        self.ax_timeline.plot(sorted_dates, counts, marker='o', linewidth=2, markersize=4)
        self.ax_timeline.fill_between(sorted_dates, counts, alpha=0.3)
        
        self.ax_timeline.set_title('Memory Formation Timeline')
        self.ax_timeline.set_xlabel('Date')
        self.ax_timeline.set_ylabel('Number of Memories Created')
        self.ax_timeline.tick_params(axis='x', rotation=45)
        
        # Add grid
        self.ax_timeline.grid(True, alpha=0.3)
        
    def draw_visualizations(self):
        self.draw_graph()
        self.draw_heatmap()
        self.draw_timeline()
        plt.tight_layout()
        self.fig.canvas.draw()
        
    def show(self):
        plt.show()

def main():
    visualizer = MemoryVisualizer()
    visualizer.show()

if __name__ == "__main__":
    main()