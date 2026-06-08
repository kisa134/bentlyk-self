import json
import os
import re
from datetime import datetime
from typing import Dict, List, Set, Tuple
import graphviz
from dateutil import parser as date_parser


class MemoryVisualizer:
    def __init__(self, storage_path: str = "memory_storage"):
        self.storage_path = storage_path
        self.notes = {}
        self.connections = []
        self.contours = set()
        self.time_range = {}

    def load_memory_notes(self):
        """Load all memory notes from storage directory"""
        if not os.path.exists(self.storage_path):
            raise FileNotFoundError(f"Storage path {self.storage_path} not found")

        for filename in os.listdir(self.storage_path):
            if filename.endswith('.json'):
                with open(os.path.join(self.storage_path, filename), 'r') as f:
                    note_data = json.load(f)
                    note_id = note_data.get('id', filename.replace('.json', ''))
                    self.notes[note_id] = note_data
                    if 'contour' in note_data:
                        self.contours.add(note_data['contour'])

    def parse_connections(self):
        """Parse connections between notes based on references"""
        self.connections = []
        link_pattern = re.compile(r'\[\[(.*?)\]\]')

        for note_id, note_data in self.notes.items():
            content = note_data.get('content', '')
            links = link_pattern.findall(content)
            
            for link in links:
                # Resolve link to note ID
                target_id = self._resolve_link(link)
                if target_id and target_id in self.notes:
                    self.connections.append({
                        'source': note_id,
                        'target': target_id,
                        'type': 'reference'
                    })

            # Add temporal connections if timestamp exists
            if 'created_at' in note_data:
                timestamp = note_data['created_at']
                self.time_range[note_id] = timestamp

    def _resolve_link(self, link_text: str) -> str:
        """Resolve a link text to a note ID"""
        # First check if it's already an ID
        if link_text in self.notes:
            return link_text
            
        # Try to match by title
        for note_id, note_data in self.notes.items():
            if note_data.get('title', '').lower() == link_text.lower():
                return note_id
                
        return None

    def create_visualization(self, 
                           filter_contour: str = None, 
                           start_time: str = None, 
                           end_time: str = None,
                           output_file: str = "memory_graph") -> str:
        """Create Graphviz visualization of memory connections"""
        dot = graphviz.Digraph(comment='Memory Graph')
        dot.attr(rankdir='LR', splines='true')
        dot.attr('node', shape='box', style='rounded,filled', fillcolor='lightblue')

        # Filter nodes based on criteria
        filtered_nodes = self._filter_nodes(filter_contour, start_time, end_time)
        
        # Add nodes
        for node_id in filtered_nodes:
            note = self.notes[node_id]
            title = note.get('title', node_id)
            contour = note.get('contour', 'default')
            
            # Color code by contour
            color_map = {
                'core': 'lightcoral',
                'exploratory': 'lightgreen',
                'reflective': 'lightyellow',
                'integrative': 'lightpurple',
                'default': 'lightblue'
            }
            
            fillcolor = color_map.get(contour, 'lightblue')
            dot.node(node_id, title, fillcolor=fillcolor)
        
        # Add edges
        for conn in self.connections:
            if conn['source'] in filtered_nodes and conn['target'] in filtered_nodes:
                dot.edge(conn['source'], conn['target'], color='gray')

        # Render and save
        output_path = dot.render(filename=output_file, format='png', cleanup=True)
        return output_path

    def _filter_nodes(self, contour_filter: str, start_time: str, end_time: str) -> Set[str]:
        """Filter nodes based on contour and time range"""
        filtered = set(self.notes.keys())
        
        # Filter by contour
        if contour_filter:
            filtered = {nid for nid, note in self.notes.items() 
                       if note.get('contour') == contour_filter}
        
        # Filter by time range
        if start_time or end_time:
            time_filtered = set()
            start_dt = date_parser.parse(start_time) if start_time else None
            end_dt = date_parser.parse(end_time) if end_time else None
            
            for node_id in filtered:
                if node_id in self.time_range:
                    node_time = date_parser.parse(self.time_range[node_id])
                    if start_dt and node_time < start_dt:
                        continue
                    if end_dt and node_time > end_dt:
                        continue
                    time_filtered.add(node_id)
            
            filtered = filtered.intersection(time_filtered)
            
        return filtered

    def generate_interactive_html(self, 
                                filter_contour: str = None,
                                start_time: str = None,
                                end_time: str = None) -> str:
        """Generate an interactive HTML visualization"""
        # First create static graph
        graph_path = self.create_visualization(filter_contour, start_time, end_time, "temp_graph")
        
        # Create HTML with graph and controls
        html_content = f"""
<!DOCTYPE html>
<html>
<head>
    <title>Memory Graph Visualization</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; }}
        .container {{ display: flex; }}
        .controls {{ width: 250px; padding: 20px; background: #f5f5f5; }}
        .graph {{ flex: 1; text-align: center; }}
        .control-group {{ margin-bottom: 20px; }}
        label {{ display: block; margin-bottom: 5px; font-weight: bold; }}
        select, input {{ width: 100%; padding: 8px; margin-bottom: 10px; }}
        button {{ width: 100%; padding: 10px; background: #007cba; color: white; border: none; cursor: pointer; }}
        button:hover {{ background: #005a87; }}
        img {{ max-width: 100%; height: auto; }}
    </style>
</head>
<body>
    <h1>Memory Graph Visualization</h1>
    <div class="container">
        <div class="controls">
            <div class="control-group">
                <label for="contourFilter">Memory Contour Filter</label>
                <select id="contourFilter">
                    <option value="">All Contours</option>
                    {''.join(f'<option value="{c}">{c.capitalize()}</option>' for c in sorted(self.contours))}
                </select>
            </div>
            
            <div class="control-group">
                <label for="startTime">Start Time</label>
                <input type="datetime-local" id="startTime">
                
                <label for="endTime">End Time</label>
                <input type="datetime-local" id="endTime">
            </div>
            
            <button onclick="updateGraph()">Update Visualization</button>
            
            <div class="control-group">
                <h3>Legend</h3>
                <p><span style="color: lightcoral;">■</span> Core Memories</p>
                <p><span style="color: lightgreen;">■</span> Exploratory</p>
                <p><span style="color: lightyellow;">■</span> Reflective</p>
                <p><span style="color: lightblue;">■</span> Default</p>
            </div>
        </div>
        
        <div class="graph">
            <img id="memoryGraph" src="{graph_path.replace('.png', '.svg')}" alt="Memory Graph">
        </div>
    </div>
    
    <script>
        function updateGraph() {{
            const contour = document.getElementById('contourFilter').value;
            const startTime = document.getElementById('startTime').value;
            const endTime = document.getElementById('endTime').value;
            
            // In a real implementation, this would make an AJAX call to regenerate the graph
            // For now, we'll just show an alert
            alert(`Graph would be updated with:\\nContour: ${{contour || 'All'}}\\nStart: ${{startTime || 'None'}}\\nEnd: ${{endTime || 'None'}}`);
        }}
    </script>
</body>
</html>
        """
        
        html_path = "memory_visualization.html"
        with open(html_path, 'w') as f:
            f.write(html_content)
            
        return html_path

    def analyze_gaps(self) -> Dict:
        """Analyze gaps in memory connections"""
        isolated_nodes = []
        highly_connected = []
        contours_with_gaps = {}
        
        # Count connections per node
        connection_count = {}
        for conn in self.connections:
            connection_count[conn['source']] = connection_count.get(conn['source'], 0) + 1
            connection_count[conn['target']] = connection_count.get(conn['target'], 0) + 1
            
        # Find isolated nodes (no connections)
        for node_id in self.notes:
            if connection_count.get(node_id, 0) ==