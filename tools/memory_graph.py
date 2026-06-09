import hashlib
import time
from collections import defaultdict, Counter
from typing import List, Dict, Tuple, Any, Optional
from dataclasses import dataclass
import heapq
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

@dataclass
class MemoryRecord:
    id: str
    content: str
    vector: Optional[np.ndarray] = None
    access_count: int = 0
    last_accessed: float = 0.0

class MetricsCollector:
    def __init__(self):
        self.metrics = {
            'exact_matches': 0,
            'fuzzy_matches': 0,
            'cache_hits': 0,
            'cache_misses': 0,
            'query_times': [],
            'cache_size': 0
        }
    
    def record_exact_match(self):
        self.metrics['exact_matches'] += 1
    
    def record_fuzzy_match(self):
        self.metrics['fuzzy_matches'] += 1
    
    def record_cache_hit(self):
        self.metrics['cache_hits'] += 1
    
    def record_cache_miss(self):
        self.metrics['cache_misses'] += 1
    
    def record_query_time(self, query_time: float):
        self.metrics['query_times'].append(query_time)
    
    def update_cache_size(self, size: int):
        self.metrics['cache_size'] = size
    
    def get_summary(self) -> Dict[str, Any]:
        query_times = self.metrics['query_times']
        return {
            'exact_matches': self.metrics['exact_matches'],
            'fuzzy_matches': self.metrics['fuzzy_matches'],
            'cache_hits': self.metrics['cache_hits'],
            'cache_misses': self.metrics['cache_misses'],
            'cache_hit_rate': self.metrics['cache_hits'] / max(1, self.metrics['cache_hits'] + self.metrics['cache_misses']),
            'avg_query_time': sum(query_times) / max(1, len(query_times)),
            'cache_size': self.metrics['cache_size']
        }

class MemoryGraph:
    def __init__(self, cache_size: int = 1000, similarity_threshold: float = 0.7):
        # Hash-based indexing for exact matches
        self.hash_index: Dict[str, MemoryRecord] = {}
        
        # Vector storage for semantic similarity
        self.vector_index: List[MemoryRecord] = []
        self.vectorizer = TfidfVectorizer(max_features=1000, stop_words='english')
        self.vectorizer_fitted = False
        
        # LRU cache for frequently accessed memories
        self.cache: Dict[str, MemoryRecord] = {}
        self.cache_size = cache_size
        self.access_counter = Counter()
        
        # Similarity threshold for fuzzy matching
        self.similarity_threshold = similarity_threshold
        
        # Metrics collection
        self.metrics = MetricsCollector()
    
    def _hash_content(self, content: str) -> str:
        """Generate a hash for content-based exact matching."""
        return hashlib.sha256(content.encode('utf-8')).hexdigest()
    
    def _vectorize_content(self, contents: List[str]) -> np.ndarray:
        """Convert text contents to TF-IDF vectors."""
        if not self.vectorizer_fitted:
            vectors = self.vectorizer.fit_transform(contents)
            self.vectorizer_fitted = True
        else:
            vectors = self.vectorizer.transform(contents)
        return vectors.toarray()
    
    def add_memory(self, memory_id: str, content: str):
        """Add a new memory to the graph."""
        # Create memory record
        record = MemoryRecord(id=memory_id, content=content)
        
        # Add to hash index
        content_hash = self._hash_content(content)
        self.hash_index[content_hash] = record
        
        # Add to vector index
        self.vector_index.append(record)
        
        # Re-vectorize all contents when adding new memory
        all_contents = [rec.content for rec in self.vector_index]
        vectors = self._vectorize_content(all_contents)
        
        # Update vectors in records
        for i, record in enumerate(self.vector_index):
            record.vector = vectors[i]
    
    def _update_cache(self, record: MemoryRecord):
        """Update LRU cache with accessed record."""
        self.access_counter[record.id] += 1
        record.access_count += 1
        record.last_accessed = time.time()
        
        if record.id in self.cache:
            self.metrics.record_cache_hit()
        else:
            self.metrics.record_cache_miss()
            self.cache[record.id] = record
            
            # Maintain cache size
            if len(self.cache) > self.cache_size:
                # Remove least recently used item
                lru_id = min(self.cache.keys(), 
                           key=lambda k: self.cache[k].last_accessed)
                del self.cache[lru_id]
        
        self.metrics.update_cache_size(len(self.cache))
    
    def retrieve_exact(self, content: str) -> Optional[MemoryRecord]:
        """Retrieve memory using exact hash match."""
        content_hash = self._hash_content(content)
        if content_hash in self.hash_index:
            record = self.hash_index[content_hash]
            self._update_cache(record)
            self.metrics.record_exact_match()
            return record
        return None
    
    def retrieve_fuzzy(self, content: str, top_k: int = 5) -> List[Tuple[MemoryRecord, float]]:
        """Retrieve memories using semantic similarity."""
        if not self.vector_index:
            return []
        
        # Vectorize query content
        query_vector = self._vectorize_content([content])[0].reshape(1, -1)
        
        # Calculate similarities
        similarities = []
        for record in self.vector_index:
            if record.vector is not None:
                sim = cosine_similarity(query_vector, record.vector.reshape(1, -1))[0][0]
                if sim >= self.similarity_threshold:
                    similarities.append((record, sim))
        
        # Sort by similarity and return top-k
        similarities.sort(key=lambda x: x[1], reverse=True)
        results = similarities[:top_k]
        
        if results:
            self.metrics.record_fuzzy_match()
        
        return results
    
    def retrieve(self, content: str, top_k: int = 5) -> List[Tuple[MemoryRecord, float]]:
        """Hybrid retrieval using exact match first, then fuzzy match."""
        start_time = time.time()
        
        # Check cache first
        content_hash = self._hash_content(content)
        for record in self.cache.values():
            if record.content == content:
                self._update_cache(record)
                self.metrics.record_query_time(time.time() - start_time)
                return [(record, 1.0)]
        
        # Try exact match
        exact_record = self.retrieve_exact(content)
        if exact_record:
            self.metrics.record_query_time(time.time() - start_time)
            return [(exact_record, 1.0)]
        
        # Fall back to fuzzy matching
        results = self.retrieve_fuzzy(content, top_k)
        self.metrics.record_query_time(time.time() - start_time)
        return results
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get performance metrics."""
        return self.metrics.get_summary()
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """Get detailed cache statistics."""
        if not self.access_counter:
            return {}
        
        total_accesses = sum(self.access_counter.values())
        return {
            'access_counts': dict(self.access_counter.most_common(10)),
            'total_accesses': total_accesses,
            'unique_memories_accessed': len(self.access_counter)
        }

# Example usage
if __name__ == "__main__":
    # Create memory graph
    mg = MemoryGraph(cache_size=100, similarity_threshold=0.5)
    
    # Add some memories
    mg.add_memory("mem1", "The quick brown fox jumps over the lazy dog")
    mg.add_memory("mem2", "A quick brown fox leaps over a sleepy dog")
    mg.add_memory("mem3", "Python is a high-level programming language")
    mg.add_memory("mem4", "Java is a popular programming language")
    
    # Retrieve exact match
    result = mg.retrieve("The quick brown fox jumps over the lazy dog")
    print("Exact match:", [r[0].id for r in result])
    
    # Retrieve fuzzy match
    result = mg.retrieve("A fast brown fox jumps over a tired dog")
    print("Fuzzy match:", [(r[0].id, r[1]) for r in result])
    
    # Retrieve another fuzzy match
    result = mg.retrieve("Programming with Python")
    print("Another fuzzy match:", [(r[0].id, r[1]) for r in result])
    
    # Print metrics
    print("\nMetrics:", mg.get_metrics())
    print("Cache stats:", mg.get_cache_stats())