import bisect
import hashlib
import struct
import threading
from collections import defaultdict
from typing import List, Tuple, Optional, Dict, Any, Iterator
from dataclasses import dataclass
from concurrent.futures import ThreadPoolExecutor
import time


@dataclass
class MemoryRecord:
    timestamp: int
    address: int
    size: int
    data_hash: str
    metadata: Dict[str, Any]


class BTree:
    def __init__(self, degree: int = 128):
        self.degree = degree
        self.root = BTreeNode(leaf=True)
        self.lock = threading.RLock()

    def insert(self, key: int, value: Any) -> None:
        with self.lock:
            root = self.root
            if len(root.keys) == (2 * self.degree) - 1:
                new_root = BTreeNode()
                new_root.children.append(root)
                self._split_child(new_root, 0)
                self._insert_non_full(new_root, key, value)
                self.root = new_root
            else:
                self._insert_non_full(root, key, value)

    def _split_child(self, parent: 'BTreeNode', index: int) -> None:
        degree = self.degree
        child = parent.children[index]
        new_child = BTreeNode(leaf=child.leaf)
        
        parent.keys.insert(index, child.keys[degree - 1])
        parent.children.insert(index + 1, new_child)
        
        new_child.keys = child.keys[degree:]
        child.keys = child.keys[:degree - 1]
        
        if not child.leaf:
            new_child.children = child.children[degree:]
            child.children = child.children[:degree]

    def _insert_non_full(self, node: 'BTreeNode', key: int, value: Any) -> None:
        i = len(node.keys) - 1
        if node.leaf:
            node.keys.append(None)
            node.values.append(None)
            while i >= 0 and key < node.keys[i]:
                node.keys[i + 1] = node.keys[i]
                node.values[i + 1] = node.values[i]
                i -= 1
            node.keys[i + 1] = key
            node.values[i + 1] = value
        else:
            while i >= 0 and key < node.keys[i]:
                i -= 1
            i += 1
            if len(node.children[i].keys) == (2 * self.degree) - 1:
                self._split_child(node, i)
                if key > node.keys[i]:
                    i += 1
            self._insert_non_full(node.children[i], key, value)

    def search(self, key: int) -> Optional[Any]:
        return self._search(self.root, key)

    def _search(self, node: 'BTreeNode', key: int) -> Optional[Any]:
        i = 0
        while i < len(node.keys) and key > node.keys[i]:
            i += 1
        if i < len(node.keys) and key == node.keys[i]:
            return node.values[i]
        if node.leaf:
            return None
        return self._search(node.children[i], key)

    def range_search(self, start: int, end: int) -> List[Tuple[int, Any]]:
        result = []
        self._range_search(self.root, start, end, result)
        return result

    def _range_search(self, node: 'BTreeNode', start: int, end: int, result: List[Tuple[int, Any]]) -> None:
        i = 0
        while i < len(node.keys) and node.keys[i] < start:
            i += 1
        
        for j in range(i, len(node.keys)):
            if node.keys[j] > end:
                break
            result.append((node.keys[j], node.values[j]))
            if not node.leaf:
                self._range_search(node.children[j], start, end, result)
        
        if not node.leaf and i < len(node.children):
            self._range_search(node.children[i], start, end, result)
            for j in range(i + 1, len(node.keys)):
                if node.keys[j - 1] > end:
                    break
                self._range_search(node.children[j], start, end, result)


class BTreeNode:
    def __init__(self, leaf: bool = False):
        self.keys: List[int] = []
        self.values: List[Any] = []
        self.children: List['BTreeNode'] = []
        self.leaf = leaf


class HashTable:
    def __init__(self):
        self.table: Dict[int, MemoryRecord] = {}
        self.lock = threading.RLock()

    def insert(self, key: int, value: MemoryRecord) -> None:
        with self.lock:
            self.table[key] = value

    def get(self, key: int) -> Optional[MemoryRecord]:
        return self.table.get(key)

    def delete(self, key: int) -> bool:
        with self.lock:
            if key in self.table:
                del self.table[key]
                return True
            return False


class MemoryGraph:
    def __init__(self, btree_degree: int = 128, cache_size: int = 10000):
        self.btree = BTree(degree=btree_degree)
        self.hash_table = HashTable()
        self.cache = {}
        self.cache_size = cache_size
        self.cache_lock = threading.RLock()
        self.stats = {
            'insertions': 0,
            'queries': 0,
            'cache_hits': 0,
            'latency_sum': 0.0
        }
        self.stats_lock = threading.RLock()

    def _update_cache(self, key: int, value: MemoryRecord) -> None:
        with self.cache_lock:
            if len(self.cache) >= self.cache_size:
                # Remove oldest entry (simple FIFO)
                oldest_key = next(iter(self.cache))
                del self.cache[oldest_key]
            self.cache[key] = value

    def _get_from_cache(self, key: int) -> Optional[MemoryRecord]:
        with self.cache_lock:
            if key in self.cache:
                with self.stats_lock:
                    self.stats['cache_hits'] += 1
                return self.cache[key]
            return None

    def insert_record(self, record: MemoryRecord) -> None:
        start_time = time.perf_counter()
        try:
            # Insert into both structures
            self.btree.insert(record.timestamp, record)
            self.hash_table.insert(record.address, record)
            self._update_cache(record.address, record)
            
            with self.stats_lock:
                self.stats['insertions'] += 1
        finally:
            latency = time.perf_counter() - start_time
            with self.stats_lock:
                self.stats['latency_sum'] += latency

    def get_by_address(self, address: int) -> Optional[MemoryRecord]:
        start_time = time.perf_counter()
        try:
            # Check cache first
            cached = self._get_from_cache(address)
            if cached is not None:
                return cached
            
            # Check hash table
            result = self.hash_table.get(address)
            if result is not None:
                self._update_cache(address, result)
                return result
            
            with self.stats_lock:
                self.stats['queries'] += 1
            return None
        finally:
            latency = time.perf_counter() - start_time
            with self.stats_lock:
                self.stats['latency_sum'] += latency

    def get_by_timestamp(self, timestamp: int) -> Optional[MemoryRecord]:
        start_time = time.perf_counter()
        try:
            result = self.btree.search(timestamp)
            with self.stats_lock:
                self.stats['queries'] += 1
            return result
        finally:
            latency = time.perf_counter() - start_time
            with self.stats_lock:
                self.stats['latency_sum'] += latency

    def get_range(self, start_timestamp: int, end_timestamp: int) -> List[MemoryRecord]:
        start_time = time.perf_counter()
        try:
            # Get timestamp range from B-tree
            timestamp_results = self.btree.range_search(start_timestamp, end_timestamp)
            results = [record for _, record in timestamp_results]
            
            with self.stats_lock:
                self.stats['queries'] += 1
            return results
        finally:
            latency = time.perf_counter() - start_time
            with self.stats_lock:
                self.stats['latency_sum'] += latency

    def delete_record(self, address: int) -> bool:
        start_time = time.perf_counter()
        try:
            # Remove from hash table (main deletion point)
            result = self.hash_table.delete(address)
            
            # Remove from cache if present
            with self.cache_lock:
                if address in self.cache:
                    del self.cache[address]
            
            return result
        finally:
            latency = time.perf_counter() - start_time
            with self.stats_lock:
                self.stats['latency_sum'] += latency

    def bulk_insert(self, records: List[MemoryRecord]) -> None:
        # Parallel insertion for better performance
        with ThreadPoolExecutor(max_workers=4) as executor:
            futures = [executor.submit(self.insert_record, record) for record in records]
            for future in futures:
                future.result()  # Ensure completion

    def get_statistics(self) ->