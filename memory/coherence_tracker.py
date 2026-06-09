import asyncio
import time
from typing import Dict, List, Set, Tuple, Optional, Callable
from dataclasses import dataclass, field
from enum import Enum
import logging

from memory.fragmentation_detector import FragmentationDetector
from telemetry.event_manager import EventManager
from models.introspection import IntrospectionEntry


class CoherenceIssueType(Enum):
    CONTRADICTION = "contradiction"
    GAP = "gap"
    REDUNDANCY = "redundancy"


@dataclass
class CoherenceMetrics:
    contradictions: int = 0
    gaps: int = 0
    redundancies: int = 0
    total_entries: int = 0
    last_updated: float = field(default_factory=time.time)


@dataclass
class CoherenceThresholds:
    max_contradictions: int = 5
    max_gaps: int = 10
    max_redundancies: int = 15
    check_interval_seconds: float = 30.0


class CoherenceTracker:
    def __init__(
        self,
        fragmentation_detector: FragmentationDetector,
        event_manager: EventManager,
        thresholds: Optional[CoherenceThresholds] = None
    ):
        self.fragmentation_detector = fragmentation_detector
        self.event_manager = event_manager
        self.thresholds = thresholds or CoherenceThresholds()
        
        self.metrics = CoherenceMetrics()
        self.running = False
        self._task: Optional[asyncio.Task] = None
        
        # Track seen content for coherence analysis
        self._content_hash_index: Dict[str, List[IntrospectionEntry]] = {}
        self._content_semantic_map: Dict[str, Set[str]] = {}
        
        self._subscribers: List[Callable[[CoherenceMetrics], None]] = []
        
        self.logger = logging.getLogger(__name__)

    def subscribe_to_updates(self, callback: Callable[[CoherenceMetrics], None]):
        """Subscribe to coherence metric updates"""
        self._subscribers.append(callback)

    def unsubscribe_from_updates(self, callback: Callable[[CoherenceMetrics], None]):
        """Unsubscribe from coherence metric updates"""
        if callback in self._subscribers:
            self._subscribers.remove(callback)

    async def start_tracking(self):
        """Start the coherence tracking process"""
        if self.running:
            return
            
        self.running = True
        self._task = asyncio.create_task(self._tracking_loop())
        self.logger.info("Coherence tracking started")

    async def stop_tracking(self):
        """Stop the coherence tracking process"""
        self.running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        self.logger.info("Coherence tracking stopped")

    async def _tracking_loop(self):
        """Main tracking loop that periodically checks coherence"""
        while self.running:
            try:
                await self._analyze_coherence()
                await asyncio.sleep(self.thresholds.check_interval_seconds)
            except Exception as e:
                self.logger.error(f"Error in coherence tracking loop: {e}")
                await asyncio.sleep(5)  # Brief pause before retry

    async def _analyze_coherence(self):
        """Analyze current coherence metrics and emit events if needed"""
        # Get recent introspection entries
        recent_entries = await self.fragmentation_detector.get_recent_entries()
        
        # Update metrics
        await self._update_metrics(recent_entries)
        
        # Check thresholds and emit events
        await self._check_thresholds()
        
        # Notify subscribers
        for callback in self._subscribers:
            try:
                callback(self.metrics)
            except Exception as e:
                self.logger.error(f"Error notifying subscriber: {e}")

    async def _update_metrics(self, entries: List[IntrospectionEntry]):
        """Update coherence metrics based on new entries"""
        self.metrics.total_entries = len(entries)
        
        # Reset issue counts
        contradictions = 0
        gaps = 0
        redundancies = 0
        
        # Clear indexes for fresh analysis
        self._content_hash_index.clear()
        self._content_semantic_map.clear()
        
        # Index entries by content hash
        for entry in entries:
            content_hash = self._hash_content(entry.content)
            if content_hash not in self._content_hash_index:
                self._content_hash_index[content_hash] = []
            self._content_hash_index[content_hash].append(entry)
            
            # Build semantic mapping
            semantic_key = self._extract_semantic_key(entry)
            if semantic_key not in self._content_semantic_map:
                self._content_semantic_map[semantic_key] = set()
            self._content_semantic_map[semantic_key].add(content_hash)
        
        # Detect redundancies (same content hash)
        for content_hash, entry_list in self._content_hash_index.items():
            if len(entry_list) > 1:
                redundancies += len(entry_list) - 1
        
        # Detect contradictions (different content for same semantic key)
        for semantic_key, content_hashes in self._content_semantic_map.items():
            if len(content_hashes) > 1:
                contradictions += 1
        
        # Detect gaps (missing expected relationships)
        gaps = await self._detect_gaps(entries)
        
        # Update metrics
        self.metrics.contradictions = contradictions
        self.metrics.gaps = gaps
        self.metrics.redundancies = redundancies
        self.metrics.last_updated = time.time()

    async def _detect_gaps(self, entries: List[IntrospectionEntry]) -> int:
        """Detect gaps in logical sequences or expected relationships"""
        gaps = 0
        
        # Group entries by context/session
        context_groups: Dict[str, List[IntrospectionEntry]] = {}
        for entry in entries:
            context = getattr(entry, 'context_id', 'default')
            if context not in context_groups:
                context_groups[context] = []
            context_groups[context].append(entry)
        
        # Check each context for logical completeness
        for context_id, context_entries in context_groups.items():
            gaps += await self._check_context_completeness(context_id, context_entries)
        
        return gaps

    async def _check_context_completeness(self, context_id: str, entries: List[IntrospectionEntry]) -> int:
        """Check if a context has complete logical flow"""
        # This is a simplified gap detection - in practice, this would use
        # more sophisticated NLP and logical reasoning
        
        if len(entries) < 2:
            return 0
            
        gaps = 0
        sorted_entries = sorted(entries, key=lambda x: x.timestamp)
        
        # Check temporal continuity
        for i in range(1, len(sorted_entries)):
            time_diff = sorted_entries[i].timestamp - sorted_entries[i-1].timestamp
            # If there's a large time gap without explicit continuation markers
            if time_diff > 3600:  # 1 hour threshold
                gaps += 1
                
        return gaps

    def _hash_content(self, content: str) -> str:
        """Create a normalized hash of content for comparison"""
        # Simplified content hashing - real implementation would normalize better
        import hashlib
        normalized = ' '.join(content.lower().split())
        return hashlib.md5(normalized.encode()).hexdigest()

    def _extract_semantic_key(self, entry: IntrospectionEntry) -> str:
        """Extract semantic key for grouping related entries"""
        # Simplified semantic key extraction
        content_preview = entry.content[:50].lower()
        return f"{entry.entry_type}_{content_preview}"

    async def _check_thresholds(self):
        """Check if any coherence thresholds have been breached"""
        issues = []
        
        if self.metrics.contradictions > self.thresholds.max_contradictions:
            issues.append(CoherenceIssueType.CONTRADICTION)
            
        if self.metrics.gaps > self.thresholds.max_gaps:
            issues.append(CoherenceIssueType.GAP)
            
        if self.metrics.redundancies > self.thresholds.max_redundancies:
            issues.append(CoherenceIssueType.REDUNDANCY)
        
        if issues:
            await self._emit_coherence_alert(issues)

    async def _emit_coherence_alert(self, issue_types: List[CoherenceIssueType]):
        """Emit telemetry event for coherence issues"""
        event_data = {
            "issue_types": [issue.value for issue in issue_types],
            "metrics": {
                "contradictions": self.metrics.contradictions,
                "gaps": self.metrics.gaps,
                "redundancies": self.metrics.redundancies,
                "total_entries": self.metrics.total_entries
            },
            "thresholds": {
                "max_contradictions": self.thresholds.max_contradictions,
                "max_gaps": self.thresholds.max_gaps,
                "max_redundancies": self.thresholds.max_redundancies
            }
        }
        
        await self.event_manager.emit_event(
            event_type="coherence_threshold_breached",
            data=event_data,
            severity="warning"
        )
        
        self.logger.warning(f"Coherence thresholds breached: {issue_types}")

    def get_current_metrics(self) -> CoherenceMetrics:
        """Get current coherence metrics"""
        return self.metrics.copy() if hasattr(self.metrics, 'copy') else self.metrics

    async def trigger_immediate_analysis(self):
        """Trigger an immediate coherence analysis"""
        await self._analyze_coherence()