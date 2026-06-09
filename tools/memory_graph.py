class MemoryNode:
    def __init__(self):
        self.children = {}
        self.entries = []
        self.is_end = False

class MemoryTrie:
    def __init__(self):
        self.root = MemoryNode()
    
    def insert(self, key, entry):
        node = self.root
        for char in key:
            if char not in node.children:
                node.children[char] = MemoryNode()
            node = node.children[char]
        node.entries.append(entry)
        node.is_end = True
    
    def search(self, key):
        node = self.root
        for char in key:
            if char not in node.children:
                return []
            node = node.children[char]
        return node.entries if node.is_end else []
    
    def starts_with(self, prefix):
        node = self.root
        for char in prefix:
            if char not in node.children:
                return []
            node = node.children[char]
        
        results = []
        self._collect_all(node, results)
        return results
    
    def _collect_all(self, node, results):
        if node.is_end:
            results.extend(node.entries)
        for child in node.children.values():
            self._collect_all(child, results)

class MemoryGraph:
    def __init__(self):
        self.trie = MemoryTrie()
        self.memory_store = {}
        self.next_id = 1
    
    def store(self, key, data):
        entry_id = self.next_id
        self.next_id += 1
        
        entry = {
            'id': entry_id,
            'key': key,
            'data': data
        }
        
        self.memory_store[entry_id] = entry
        self.trie.insert(key, entry)
        return entry_id
    
    def retrieve(self, key):
        return self.trie.search(key)
    
    def search_prefix(self, prefix):
        return self.trie.starts_with(prefix)
    
    def get_by_id(self, entry_id):
        return self.memory_store.get(entry_id)
    
    def update(self, entry_id, data):
        if entry_id in self.memory_store:
            entry = self.memory_store[entry_id]
            entry['data'] = data
            return True
        return False
    
    def delete(self, entry_id):
        if entry_id in self.memory_store:
            entry = self.memory_store[entry_id]
            del self.memory_store[entry_id]
            return entry
        return None

# Example usage
if __name__ == "__main__":
    memory_graph = MemoryGraph()
    
    # Store entries
    id1 = memory_graph.store("user:john:profile", {"name": "John", "age": 30})
    id2 = memory_graph.store("user:john:settings", {"theme": "dark", "notifications": True})
    id3 = memory_graph.store("user:jane:profile", {"name": "Jane", "age": 25})
    
    # Retrieve exact matches
    print("Exact match for 'user:john:profile':")
    print(memory_graph.retrieve("user:john:profile"))
    
    # Search by prefix
    print("\nEntries starting with 'user:john':")
    print(memory_graph.search_prefix("user:john"))
    
    # Retrieve by ID
    print("\nEntry with ID 1:")
    print(memory_graph.get_by_id(1))
    
    # Update entry
    memory_graph.update(1, {"name": "John", "age": 31, "city": "New York"})
    print("\nUpdated entry with ID 1:")
    print(memory_graph.get_by_id(1))