import json
import hashlib
from typing import Dict, List, Set, Optional, Any, Tuple
from collections import defaultdict, deque
import asyncio
from dataclasses import dataclass, asdict
from datetime import datetime

@dataclass
class MemoryNode:
    """Represents a single memory item in the graph"""
    id: str
    content: str
    metadata: Dict[str, Any]
    created_at: datetime
    updated_at: datetime
    tags: List[str]
    embedding: Optional[List[float]] = None
    
    def __post_init__(self):
        if isinstance(self.created_at, str):
            self.created_at = datetime.fromisoformat(self.created_at)
        if isinstance(self.updated_at, str):
            self.updated_at = datetime.fromisoformat(self.updated_at)

class MemoryGraph:
    """
    A graph-based memory structure that supports efficient search,
    relationship linking, and automatic connection updates.
    """
    
    def __init__(self):
        # Core graph structures
        self.nodes: Dict[str, MemoryNode] = {}
        self.edges: Dict[str, Set[str]] = defaultdict(set)
        self.reverse_edges: Dict[str, Set[str]] = defaultdict(set)
        self.tag_index: Dict[str, Set[str]] = defaultdict(set)
        self.content_index: Dict[str, Set[str]] = defaultdict(set)
        
        # Content-based indexing for fast search
        self._build_indexes()
    
    def _build_indexes(self):
        """Build initial indexes from existing nodes"""
        for node_id, node in self.nodes.items():
            # Index by tags
            for tag in node.tags:
                self.tag_index[tag].add(node_id)
            
            # Index by content words
            words = set(node.content.lower().split())
            for word in words:
                self.content_index[word].add(node_id)
    
    def add_memory(self, content: str, metadata: Dict[str, Any] = None, 
                   tags: List[str] = None, embedding: List[float] = None) -> str:
        """
        Add a new memory to the graph and automatically create connections
        
        Args:
            content: The memory content
            metadata: Additional metadata
            tags: List of tags for categorization
            embedding: Vector embedding for semantic search
            
        Returns:
            str: The ID of the newly created memory
        """
        # Generate unique ID based on content
        memory_id = self._generate_id(content)
        
        # Create the memory node
        node = MemoryNode(
            id=memory_id,
            content=content,
            metadata=metadata or {},
            created_at=datetime.now(),
            updated_at=datetime.now(),
            tags=tags or [],
            embedding=embedding
        )
        
        # Add to graph
        self.nodes[memory_id] = node
        
        # Update indexes
        self._update_indexes(node)
        
        # Automatically create connections
        self._create_automatic_connections(node)
        
        return memory_id
    
    def _generate_id(self, content: str) -> str:
        """Generate a unique ID for a memory based on its content"""
        return hashlib.sha256(content.encode()).hexdigest()[:16]
    
    def _update_indexes(self, node: MemoryNode):
        """Update all indexes with the new node"""
        # Update tag index
        for tag in node.tags:
            self.tag_index[tag].add(node.id)
        
        # Update content index
        words = set(node.content.lower().split())
        for word in words:
            self.content_index[word].add(node.id)
    
    def _create_automatic_connections(self, node: MemoryNode):
        """Automatically create connections based on content similarity and tags"""
        # Find related nodes based on shared tags
        related_by_tags = set()
        for tag in node.tags:
            related_by_tags.update(self.tag_index[tag])
        
        # Find related nodes based on content overlap
        related_by_content = set()
        words = set(node.content.lower().split())
        for word in words:
            related_by_content.update(self.content_index[word])
        
        # Create connections (excluding self)
        related_nodes = (related_by_tags | related_by_content) - {node.id}
        
        for related_id in related_nodes:
            self._create_bidirectional_edge(node.id, related_id)
    
    def _create_bidirectional_edge(self, node1_id: str, node2_id: str):
        """Create a bidirectional connection between two nodes"""
        self.edges[node1_id].add(node2_id)
        self.reverse_edges[node2_id].add(node1_id)
        self.edges[node2_id].add(node1_id)
        self.reverse_edges[node1_id].add(node2_id)
    
    def get_memory(self, memory_id: str) -> Optional[MemoryNode]:
        """Retrieve a memory by its ID"""
        return self.nodes.get(memory_id)
    
    def update_memory(self, memory_id: str, content: str = None, 
                     metadata: Dict[str, Any] = None, tags: List[str] = None) -> bool:
        """
        Update an existing memory and refresh its connections
        
        Args:
            memory_id: ID of the memory to update
            content: New content (optional)
            metadata: New metadata (optional)
            tags: New tags (optional)
            
        Returns:
            bool: True if update was successful
        """
        if memory_id not in self.nodes:
            return False
        
        node = self.nodes[memory_id]
        
        # Update content if provided
        if content is not None:
            node.content = content
        
        # Update metadata if provided
        if metadata is not None:
            node.metadata.update(metadata)
        
        # Update tags if provided
        if tags is not None:
            # Remove from old tag index
            for tag in node.tags:
                self.tag_index[tag].discard(memory_id)
            
            # Update tags
            node.tags = tags
            
            # Add to new tag index
            for tag in node.tags:
                self.tag_index[tag].add(memory_id)
        
        # Update timestamp
        node.updated_at = datetime.now()
        
        # Rebuild connections
        self._rebuild_connections(node)
        
        return True
    
    def _rebuild_connections(self, node: MemoryNode):
        """Rebuild connections for a node after update"""
        # Remove existing connections
        for connected_id in list(self.edges[node.id]):
            self.edges[connected_id].discard(node.id)
            self.reverse_edges[connected_id].discard(node.id)
        
        self.edges[node.id].clear()
        self.reverse_edges[node.id].clear()
        
        # Recreate connections
        self._create_automatic_connections(node)
    
    def delete_memory(self, memory_id: str) -> bool:
        """Delete a memory and all its connections"""
        if memory_id not in self.nodes:
            return False
        
        # Remove connections
        for connected_id in list(self.edges[memory_id]):
            self.edges[connected_id].discard(memory_id)
            self.reverse_edges[connected_id].discard(memory_id)
        
        # Remove from indexes
        node = self.nodes[memory_id]
        for tag in node.tags:
            self.tag_index[tag].discard(memory_id)
        
        words = set(node.content.lower().split())
        for word in words:
            self.content_index[word].discard(memory_id)
        
        # Remove node
        del self.edges[memory_id]
        del self.reverse_edges[memory_id]
        del self.nodes[memory_id]
        
        return True
    
    def search_by_content(self, query: str, limit: int = 10) -> List[MemoryNode]:
        """Search memories by content keywords"""
        query_words = set(query.lower().split())
        matching_nodes = set()
        
        for word in query_words:
            matching_nodes.update(self.content_index.get(word, set()))
        
        # Rank by relevance (number of matching words)
        ranked_nodes = []
        for node_id in matching_nodes:
            node = self.nodes[node_id]
            node_words = set(node.content.lower().split())
            relevance = len(query_words & node_words)
            ranked_nodes.append((relevance, node))
        
        # Sort by relevance and return top results
        ranked_nodes.sort(key=lambda x: x[0], reverse=True)
        return [node for _, node in ranked_nodes[:limit]]
    
    def search_by_tags(self, tags: List[str], limit: int = 10) -> List[MemoryNode]:
        """Search memories by tags"""
        matching_nodes = set()
        for tag in tags:
            matching_nodes.update(self.tag_index.get(tag, set()))
        
        # Return top results
        return [self.nodes[node_id] for node_id in list(matching_nodes)[:limit]]
    
    def get_related_memories(self, memory_id: str, depth: int = 2) -> List[MemoryNode]:
        """
        Get memories related to a given memory within a certain depth
        
        Args:
            memory_id: ID of the starting memory
            depth: Maximum depth of relationship traversal
            
        Returns:
            List[MemoryNode]: Related memories
        """
        if memory_id not in self.nodes:
            return []
        
        visited = set()
        queue = deque([(memory_id, 0)])  # (node_id, depth)
        related_ids = set()
        
        while queue:
            current_id, current_depth = queue.popleft()
            
            if current_id in visited:
                continue
            
            visited.add(current_id)
            
            if current_depth > 0:  # Don't include the starting node
                related_ids.add(current_id)