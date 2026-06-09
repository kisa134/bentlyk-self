import time
from typing import List, Tuple, Dict, Any
from dataclasses import dataclass
from enum import Enum

class BlockStatus(Enum):
    FREE = "free"
    ACTIVE = "active"

@dataclass
class MemoryBlock:
    start_address: int
    size: int
    status: BlockStatus
    data: Any = None
    
    def end_address(self) -> int:
        return self.start_address + self.size

class MemoryOptimizer:
    def __init__(self, memory_blocks: List[MemoryBlock]):
        self.original_blocks = memory_blocks.copy()
        self.blocks = memory_blocks.copy()
        self.benchmark_results = {}
    
    def analyze_fragmentation(self) -> Dict[str, Any]:
        """Analyze memory fragmentation and return statistics"""
        free_blocks = [block for block in self.blocks if block.status == BlockStatus.FREE]
        active_blocks = [block for block in self.blocks if block.status == BlockStatus.ACTIVE]
        
        # Count contiguous free blocks
        contiguous_free_regions = 0
        i = 0
        while i < len(free_blocks):
            contiguous_free_regions += 1
            j = i + 1
            current_end = free_blocks[i].end_address()
            while j < len(free_blocks) and free_blocks[j].start_address == current_end:
                current_end = free_blocks[j].end_address()
                j += 1
            i = j
        
        # Calculate fragmentation metrics
        total_free_space = sum(block.size for block in free_blocks)
        total_memory = sum(block.size for block in self.blocks)
        fragmentation_ratio = total_free_space / total_memory if total_memory > 0 else 0
        
        return {
            'total_blocks': len(self.blocks),
            'free_blocks': len(free_blocks),
            'active_blocks': len(active_blocks),
            'contiguous_free_regions': contiguous_free_regions,
            'total_free_space': total_free_space,
            'fragmentation_ratio': fragmentation_ratio,
            'largest_free_block': max([block.size for block in free_blocks], default=0)
        }
    
    def defragment(self) -> None:
        """Defragment memory by merging adjacent free blocks and compacting active memory"""
        # Sort blocks by start address
        self.blocks.sort(key=lambda x: x.start_address)
        
        # Merge adjacent free blocks
        i = 0
        while i < len(self.blocks) - 1:
            current = self.blocks[i]
            next_block = self.blocks[i + 1]
            
            # If both blocks are free and adjacent, merge them
            if (current.status == BlockStatus.FREE and 
                next_block.status == BlockStatus.FREE and 
                current.end_address() == next_block.start_address):
                current.size += next_block.size
                self.blocks.pop(i + 1)
            else:
                i += 1
        
        # Compact active blocks to the beginning
        active_blocks = [block for block in self.blocks if block.status == BlockStatus.ACTIVE]
        free_blocks = [block for block in self.blocks if block.status == BlockStatus.FREE]
        
        # Calculate new addresses for active blocks
        compacted_blocks = []
        current_address = 0
        
        # Place all active blocks first
        for block in active_blocks:
            block.start_address = current_address
            compacted_blocks.append(block)
            current_address += block.size
        
        # Add merged free block at the end
        total_free_size = sum(block.size for block in free_blocks)
        if total_free_size > 0:
            compacted_blocks.append(MemoryBlock(
                start_address=current_address,
                size=total_free_size,
                status=BlockStatus.FREE
            ))
        
        self.blocks = compacted_blocks
    
    def benchmark(self) -> Dict[str, Any]:
        """Run benchmark comparison before and after optimization"""
        # Benchmark before optimization
        start_time = time.perf_counter()
        before_stats = self.analyze_fragmentation()
        before_time = time.perf_counter() - start_time
        
        # Store original state for comparison
        original_blocks = self.blocks.copy()
        
        # Apply optimization
        start_time = time.perf_counter()
        self.defragment()
        optimization_time = time.perf_counter() - start_time
        
        # Benchmark after optimization
        start_time = time.perf_counter()
        after_stats = self.analyze_fragmentation()
        after_time = time.perf_counter() - start_time
        
        # Restore original state for accurate comparison
        self.blocks = original_blocks.copy()
        
        return {
            'before': {
                'statistics': before_stats,
                'analysis_time': before_time
            },
            'after': {
                'statistics': after_stats,
                'analysis_time': after_time
            },
            'optimization_time': optimization_time,
            'improvement': {
                'fragmentation_reduction': before_stats['fragmentation_ratio'] - after_stats['fragmentation_ratio'],
                'contiguous_regions_reduction': before_stats['contiguous_free_regions'] - after_stats['contiguous_free_regions'],
                'largest_free_block_improvement': after_stats['largest_free_block'] - before_stats['largest_free_block']
            }
        }
    
    def get_memory_layout(self) -> List[Tuple[int, int, str]]:
        """Return current memory layout as list of (start, end, status) tuples"""
        return [(block.start_address, block.end_address(), block.status.value) for block in self.blocks]

# Example usage and testing
if __name__ == "__main__":
    # Create sample memory blocks
    sample_blocks = [
        MemoryBlock(0, 100, BlockStatus.ACTIVE, "data1"),
        MemoryBlock(100, 50, BlockStatus.FREE),
        MemoryBlock(150, 200, BlockStatus.ACTIVE, "data2"),
        MemoryBlock(350, 30, BlockStatus.FREE),
        MemoryBlock(380, 70, BlockStatus.FREE),
        MemoryBlock(450, 150, BlockStatus.ACTIVE, "data3"),
        MemoryBlock(600, 40, BlockStatus.FREE),
        MemoryBlock(640, 60, BlockStatus.FREE)
    ]
    
    # Create optimizer instance
    optimizer = MemoryOptimizer(sample_blocks)
    
    # Run benchmark
    results = optimizer.benchmark()
    
    # Print results
    print("BEFORE OPTIMIZATION:")
    before_stats = results['before']['statistics']
    print(f"  Free blocks: {before_stats['free_blocks']}")
    print(f"  Contiguous free regions: {before_stats['contiguous_free_regions']}")
    print(f"  Total free space: {before_stats['total_free_space']}")
    print(f"  Fragmentation ratio: {before_stats['fragmentation_ratio']:.2%}")
    print(f"  Largest free block: {before_stats['largest_free_block']}")
    
    print("\nAFTER OPTIMIZATION:")
    after_stats = results['after']['statistics']
    print(f"  Free blocks: {after_stats['free_blocks']}")
    print(f"  Contiguous free regions: {after_stats['contiguous_free_regions']}")
    print(f"  Total free space: {after_stats['total_free_space']}")
    print(f"  Fragmentation ratio: {after_stats['fragmentation_ratio']:.2%}")
    print(f"  Largest free block: {after_stats['largest_free_block']}")
    
    print("\nIMPROVEMENTS:")
    improvement = results['improvement']
    print(f"  Fragmentation reduction: {improvement['fragmentation_reduction']:.2%}")
    print(f"  Contiguous regions reduction: {improvement['contiguous_regions_reduction']}")
    print(f"  Largest free block improvement: {improvement['largest_free_block_improvement']}")
    print(f"  Optimization time: {results['optimization_time']:.6f} seconds")