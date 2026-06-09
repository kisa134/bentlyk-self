import json
import time
import random
import string
from collections import defaultdict
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field

@dataclass
class TrieNode:
    children: Dict[str, 'TrieNode'] = field(default_factory=dict)
    memory_entries: List[Dict[str, Any]] = field(default_factory=list)
    is_end: bool = False

class TrieMemoryIndex:
    def __init__(self):
        self.root = TrieNode()
        self.memory_data = []
    
    def _insert_word(self, node: TrieNode, word: str, index: int, char_index: int = 0):
        if char_index == len(word):
            node.is_end = True
            node.memory_entries.append(self.memory_data[index])
            return
        
        char = word[char_index]
        if char not in node.children:
            node.children[char] = TrieNode()
        
        self._insert_word(node.children[char], word, index, char_index + 1)
    
    def add_memory(self, memory: Dict[str, Any]):
        index = len(self.memory_data)
        self.memory_data.append(memory)
        
        # Index by content words
        content = memory.get('content', '')
        words = content.lower().split()
        for word in words:
            self._insert_word(self.root, word, index)
    
    def _search_prefix(self, node: TrieNode, prefix: str, char_index: int = 0) -> Optional[TrieNode]:
        if char_index == len(prefix):
            return node
        
        char = prefix[char_index]
        if char not in node.children:
            return None
        
        return self._search_prefix(node.children[char], prefix, char_index + 1)
    
    def search(self, query: str) -> List[Dict[str, Any]]:
        prefix_node = self._search_prefix(self.root, query.lower())
        if not prefix_node:
            return []
        
        results = []
        self._collect_all_entries(prefix_node, results)
        return results
    
    def _collect_all_entries(self, node: TrieNode, results: List[Dict[str, Any]]):
        results.extend(node.memory_entries)
        for child in node.children.values():
            self._collect_all_entries(child, results)

class MemoryGraph:
    def __init__(self):
        self.memories = []
        self.index = TrieMemoryIndex()
        self.id_map = {}
    
    def add_memory(self, memory: Dict[str, Any]):
        memory_id = memory.get('id', len(self.memories))
        memory['id'] = memory_id
        self.memories.append(memory)
        self.id_map[memory_id] = len(self.memories) - 1
        self.index.add_memory(memory)
        return memory_id
    
    def get_memory(self, memory_id: int) -> Optional[Dict[str, Any]]:
        index = self.id_map.get(memory_id)
        if index is not None:
            return self.memories[index]
        return None
    
    def search_memories(self, query: str) -> List[Dict[str, Any]]:
        return self.index.search(query)
    
    def get_all_memories(self) -> List[Dict[str, Any]]:
        return self.memories[:]
    
    def save_to_file(self, filepath: str):
        with open(filepath, 'w') as f:
            json.dump(self.memories, f)
    
    def load_from_file(self, filepath: str):
        with open(filepath, 'r') as f:
            self.memories = json.load(f)
            self.id_map = {mem['id']: i for i, mem in enumerate(self.memories)}
            # Rebuild index
            self.index = TrieMemoryIndex()
            for memory in self.memories:
                self.index.add_memory(memory)

class LegacyMemoryGraph:
    """Legacy implementation for benchmark comparison"""
    def __init__(self):
        self.memories = []
        self.id_map = {}
    
    def add_memory(self, memory: Dict[str, Any]):
        memory_id = memory.get('id', len(self.memories))
        memory['id'] = memory_id
        self.memories.append(memory)
        self.id_map[memory_id] = len(self.memories) - 1
        return memory_id
    
    def get_memory(self, memory_id: int) -> Optional[Dict[str, Any]]:
        index = self.id_map.get(memory_id)
        if index is not None:
            return self.memories[index]
        return None
    
    def search_memories(self, query: str) -> List[Dict[str, Any]]:
        query = query.lower()
        results = []
        for memory in self.memories:
            content = memory.get('content', '').lower()
            if query in content:
                results.append(memory)
        return results
    
    def get_all_memories(self) -> List[Dict[str, Any]]:
        return self.memories[:]
    
    def save_to_file(self, filepath: str):
        with open(filepath, 'w') as f:
            json.dump(self.memories, f)
    
    def load_from_file(self, filepath: str):
        with open(filepath, 'r') as f:
            self.memories = json.load(f)
            self.id_map = {mem['id']: i for i, mem in enumerate(self.memories)}

def generate_test_data(num_memories: int = 1000) -> List[Dict[str, Any]]:
    """Generate test data for benchmarking"""
    memories = []
    words = ['artificial', 'intelligence', 'memory', 'graph', 'trie', 'index', 'search', 
             'neural', 'network', 'data', 'structure', 'algorithm', 'optimization', 
             'performance', 'benchmark', 'system', 'database', 'storage', 'retrieval']
    
    for i in range(num_memories):
        # Generate random content with some common words
        content_words = random.choices(words, k=random.randint(5, 15))
        content = ' '.join(content_words)
        
        memories.append({
            'id': i,
            'content': content,
            'timestamp': time.time(),
            'metadata': {
                'source': f'source_{random.randint(1, 100)}',
                'tags': random.choices(words, k=random.randint(1, 3))
            }
        })
    
    return memories

def benchmark_performance():
    """Benchmark new vs legacy implementation"""
    print("Generating test data...")
    test_data = generate_test_data(1000)
    
    # Initialize both implementations
    legacy_graph = LegacyMemoryGraph()
    new_graph = MemoryGraph()
    
    # Add memories
    print("Adding memories to both implementations...")
    start_time = time.time()
    for memory in test_data:
        legacy_graph.add_memory(memory)
    legacy_add_time = time.time() - start_time
    
    start_time = time.time()
    for memory in test_data:
        new_graph.add_memory(memory)
    new_add_time = time.time() - start_time
    
    # Test search performance
    print("Testing search performance...")
    search_queries = ['artificial', 'neural', 'data', 'system', 'nonexistent']
    
    # Legacy search benchmark
    start_time = time.time()
    for _ in range(100):  # Run 100 searches
        for query in search_queries:
            legacy_graph.search_memories(query)
    legacy_search_time = time.time() - start_time
    
    # New search benchmark
    start_time = time.time()
    for _ in range(100):  # Run 100 searches
        for query in search_queries:
            new_graph.search_memories(query)
    new_search_time = time.time() - start_time
    
    # Results
    print("\n=== BENCHMARK RESULTS ===")
    print(f"Memories added: {len(test_data)}")
    print(f"Search queries tested: {len(search_queries)} (100 iterations each)")
    print()
    print("ADD PERFORMANCE:")
    print(f"  Legacy: {legacy_add_time:.4f}s")
    print(f"  New:    {new_add_time:.4f}s")
    print(f"  Speedup: {legacy_add_time/new_add_time:.2f}x")
    print()
    print("SEARCH PERFORMANCE:")
    print(f"  Legacy: {legacy_search_time:.4f}s")
    print(f"  New:    {new_search_time:.4f}s")
    print(f"  Speedup: {legacy_search_time/new_search_time:.2f}x")
    print()
    
    if new_search_time < legacy_search_time * 0.7:
        print("✓ 30%+ search performance improvement achieved!")
    else:
        print("✗ 30%+ search performance improvement not achieved")
    
    return legacy_search_time, new_search_time

if __name__ == "__main__":
    # Run benchmark
    benchmark_performance()
    
    # Example usage
    print("\n=== EXAMPLE USAGE ===")
    graph = MemoryGraph()
    
    # Add some sample memories
    memories = [
        {"content": "Artificial intelligence is transforming the world"},
        {"content": "Neural networks form the backbone of deep learning"},
        {"content": "Memory graphs help organize complex data structures"},
        {"content": "Trie data structures enable fast prefix searches"}
    ]
    
    for memory in memories:
        graph.add_memory(memory)
    
    # Search examples
    print("Searching for 'neural':")
    results