class TrieNode:
    def __init__(self):
        self.children = {}
        self.is_end_of_word = False
        self.memory_entries = []

class MemoryTrie:
    def __init__(self):
        self.root = TrieNode()
    
    def insert(self, key, memory_entry):
        node = self.root
        for char in key.lower():
            if char not in node.children:
                node.children[char] = TrieNode()
            node = node.children[char]
        node.is_end_of_word = True
        node.memory_entries.append(memory_entry)
    
    def search_prefix(self, prefix):
        node = self.root
        prefix = prefix.lower()
        
        # Navigate to the prefix node
        for char in prefix:
            if char not in node.children:
                return []
            node = node.children[char]
        
        # Collect all entries with the given prefix
        results = []
        self._collect_all_entries(node, results)
        return results
    
    def _collect_all_entries(self, node, results):
        if node.is_end_of_word:
            results.extend(node.memory_entries)
        
        for child in node.children.values():
            self._collect_all_entries(child, results)

class MemoryGraph:
    def __init__(self):
        self.trie = MemoryTrie()
        self.memory_store = {}
        self.next_id = 1
    
    def add_memory(self, content, tags=None):
        if tags is None:
            tags = []
        
        memory_id = self.next_id
        self.next_id += 1
        
        memory_entry = {
            'id': memory_id,
            'content': content,
            'tags': tags
        }
        
        self.memory_store[memory_id] = memory_entry
        
        # Index by content
        self.trie.insert(content, memory_entry)
        
        # Index by tags
        for tag in tags:
            self.trie.insert(tag, memory_entry)
        
        return memory_id
    
    def search_by_prefix(self, prefix):
        return self.trie.search_prefix(prefix)
    
    def get_memory_by_id(self, memory_id):
        return self.memory_store.get(memory_id)
    
    def update_memory(self, memory_id, content=None, tags=None):
        if memory_id not in self.memory_store:
            return False
        
        memory_entry = self.memory_store[memory_id]
        
        if content is not None:
            memory_entry['content'] = content
        
        if tags is not None:
            memory_entry['tags'] = tags
        
        self.memory_store[memory_id] = memory_entry
        return True
    
    def delete_memory(self, memory_id):
        if memory_id in self.memory_store:
            del self.memory_store[memory_id]
            return True
        return False
    
    def get_all_memories(self):
        return list(self.memory_store.values())