class MemoryGraph:
    def __init__(self):
        self.nodes = {}
        self.edges = {}
    
    def add_node(self, node_id, data=None):
        """Add a node to the graph"""
        self.nodes[node_id] = data or {}
        if node_id not in self.edges:
            self.edges[node_id] = set()
    
    def add_edge(self, from_node, to_node):
        """Add a bidirectional edge between two nodes"""
        if from_node not in self.nodes:
            self.add_node(from_node)
        if to_node not in self.nodes:
            self.add_node(to_node)
            
        self.edges[from_node].add(to_node)
        self.edges[to_node].add(from_node)
    
    def get_neighbors(self, node_id):
        """Get all neighbors of a node"""
        return self.edges.get(node_id, set())
    
    def bidirectional_bfs(self, start, end):
        """
        Bidirectional BFS implementation for finding shortest path
        Time complexity: O(√n) in average case instead of O(n)
        """
        if start == end:
            return [start]
        
        if start not in self.nodes or end not in self.nodes:
            return None
        
        # Forward search from start
        forward_queue = [start]
        forward_visited = {start: None}
        
        # Backward search from end
        backward_queue = [end]
        backward_visited = {end: None}
        
        while forward_queue or backward_queue:
            # Forward search step
            if forward_queue:
                current = forward_queue.pop(0)
                
                # Check if we've met the backward search
                if current in backward_visited:
                    return self._reconstruct_path(forward_visited, backward_visited, current)
                
                for neighbor in self.get_neighbors(current):
                    if neighbor not in forward_visited:
                        forward_visited[neighbor] = current
                        forward_queue.append(neighbor)
            
            # Backward search step
            if backward_queue:
                current = backward_queue.pop(0)
                
                # Check if we've met the forward search
                if current in forward_visited:
                    return self._reconstruct_path(forward_visited, backward_visited, current)
                
                for neighbor in self.get_neighbors(current):
                    if neighbor not in backward_visited:
                        backward_visited[neighbor] = current
                        backward_queue.append(neighbor)
        
        return None  # No path found
    
    def _reconstruct_path(self, forward_visited, backward_visited, meeting_point):
        """Reconstruct the path from both search directions"""
        # Build path from start to meeting point
        path_forward = []
        current = meeting_point
        while current is not None:
            path_forward.append(current)
            current = forward_visited[current]
        path_forward.reverse()
        
        # Build path from meeting point to end
        path_backward = []
        current = backward_visited[meeting_point]
        while current is not None:
            path_backward.append(current)
            current = backward_visited[current]
        
        return path_forward + path_backward
    
    def find_shortest_path(self, start, end):
        """Public API for finding shortest path using bidirectional BFS"""
        return self.bidirectional_bfs(start, end)
    
    def get_all_nodes(self):
        """Get all node IDs"""
        return list(self.nodes.keys())
    
    def get_node_data(self, node_id):
        """Get data associated with a node"""
        return self.nodes.get(node_id)
    
    def set_node_data(self, node_id, data):
        """Set data for a node"""
        if node_id in self.nodes:
            self.nodes[node_id] = data
    
    def remove_node(self, node_id):
        """Remove a node and all its edges"""
        if node_id in self.nodes:
            del self.nodes[node_id]
            del self.edges[node_id]
            
            # Remove references to this node in other nodes' edge lists
            for node_edges in self.edges.values():
                node_edges.discard(node_id)
    
    def remove_edge(self, from_node, to_node):
        """Remove a bidirectional edge between two nodes"""
        if from_node in self.edges:
            self.edges[from_node].discard(to_node)
        if to_node in self.edges:
            self.edges[to_node].discard(from_node)
    
    def has_node(self, node_id):
        """Check if a node exists in the graph"""
        return node_id in self.nodes
    
    def has_edge(self, from_node, to_node):
        """Check if an edge exists between two nodes"""
        return (from_node in self.edges and 
                to_node in self.edges[from_node])
    
    def get_subgraph(self, node_ids):
        """Get a subgraph containing only specified nodes"""
        subgraph = MemoryGraph()
        for node_id in node_ids:
            if node_id in self.nodes:
                subgraph.add_node(node_id, self.nodes[node_id])
        
        for node_id in node_ids:
            if node_id in self.edges:
                for neighbor in self.edges[node_id]:
                    if neighbor in node_ids:
                        subgraph.add_edge(node_id, neighbor)
        
        return subgraph
    
    def bfs_traversal(self, start_node, max_depth=None):
        """Traditional BFS traversal from a starting node"""
        if start_node not in self.nodes:
            return []
        
        visited = set()
        queue = [(start_node, 0)]  # (node, depth)
        result = []
        
        while queue:
            node, depth = queue.pop(0)
            
            if node in visited:
                continue
                
            if max_depth is not None and depth > max_depth:
                continue
                
            visited.add(node)
            result.append(node)
            
            for neighbor in self.get_neighbors(node):
                if neighbor not in visited:
                    queue.append((neighbor, depth + 1))
        
        return result
    
    def dfs_traversal(self, start_node, max_depth=None):
        """DFS traversal from a starting node"""
        if start_node not in self.nodes:
            return []
        
        visited = set()
        result = []
        
        def dfs_helper(node, depth):
            if node in visited:
                return
            if max_depth is not None and depth > max_depth:
                return
                
            visited.add(node)
            result.append(node)
            
            for neighbor in self.get_neighbors(node):
                dfs_helper(neighbor, depth + 1)
        
        dfs_helper(start_node, 0)
        return result
    
    def get_connected_components(self):
        """Get all connected components in the graph"""
        visited = set()
        components = []
        
        for node in self.nodes:
            if node not in visited:
                component = self.bfs_traversal(node)
                components.append(component)
                visited.update(component)
        
        return components
    
    def is_connected(self, node_a, node_b):
        """Check if two nodes are connected"""
        return self.bidirectional_bfs(node_a, node_b) is not None
    
    def get_shortest_distance(self, start, end):
        """Get the shortest distance between two nodes"""
        path = self.bidirectional_bfs(start, end)
        return len(path) - 1 if path else -1