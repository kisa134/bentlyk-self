import heapq
import logging
from dataclasses import dataclass
from typing import Any, Callable, Optional
from enum import Enum

logger = logging.getLogger(__name__)

@dataclass
class BlockedAction:
    priority: int
    timestamp: float
    action_type: str
    details: dict
    state_snapshot: dict
    review_callback: Optional[Callable] = None

class ActionStatus(Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"

class InterventionTrigger:
    def __init__(self):
        self.pending_actions = []  # Priority queue
        self.action_status = {}
        self.action_counter = 0
        
    def should_intervene(self, energy: float, pain: float) -> bool:
        """Determine if intervention is needed based on energy and pain levels."""
        return energy < 0.5 or pain > 0.7
    
    def block_action(self, 
                    action_type: str,
                    details: dict,
                    state_snapshot: dict,
                    priority: int = 0,
                    review_callback: Optional[Callable] = None) -> str:
        """Block an action and add it to the pending queue for review."""
        timestamp = self._get_timestamp()
        action_id = f"action_{self.action_counter}"
        self.action_counter += 1
        
        blocked_action = BlockedAction(
            priority=priority,
            timestamp=timestamp,
            action_type=action_type,
            details=details,
            state_snapshot=state_snapshot,
            review_callback=review_callback
        )
        
        # Use negative priority for max-heap behavior
        heapq.heappush(self.pending_actions, (-priority, timestamp, action_id, blocked_action))
        self.action_status[action_id] = ActionStatus.PENDING
        
        # Log the blocked action
        logger.warning(
            f"Action blocked for review - ID: {action_id}, "
            f"Type: {action_type}, Priority: {priority}"
        )
        
        return action_id
    
    def review_action(self, action_id: str, approve: bool) -> bool:
        """Review and either approve or reject a pending action."""
        if action_id not in self.action_status:
            logger.error(f"Action ID {action_id} not found")
            return False
            
        if self.action_status[action_id] != ActionStatus.PENDING:
            logger.warning(f"Action {action_id} already reviewed")
            return False
            
        # Find and remove the action from pending queue
        action_item = None
        remaining_actions = []
        
        while self.pending_actions:
            item = heapq.heappop(self.pending_actions)
            if item[2] == action_id:
                action_item = item
                break
            remaining_actions.append(item)
            
        # Restore remaining actions
        for item in remaining_actions:
            heapq.heappush(self.pending_actions, item)
            
        if not action_item:
            logger.error(f"Action {action_id} not found in pending queue")
            return False
            
        _, _, _, blocked_action = action_item
        
        if approve:
            self.action_status[action_id] = ActionStatus.APPROVED
            logger.info(f"Action {action_id} approved")
            
            # Execute callback if provided
            if blocked_action.review_callback:
                try:
                    blocked_action.review_callback(True, blocked_action.details)
                except Exception as e:
                    logger.error(f"Error in review callback for {action_id}: {e}")
        else:
            self.action_status[action_id] = ActionStatus.REJECTED
            logger.info(f"Action {action_id} rejected")
            
            # Execute callback if provided
            if blocked_action.review_callback:
                try:
                    blocked_action.review_callback(False, blocked_action.details)
                except Exception as e:
                    logger.error(f"Error in review callback for {action_id}: {e}")
                    
        return True
    
    def get_pending_actions(self) -> list:
        """Get all pending actions sorted by priority."""
        pending = []
        for _, _, action_id, blocked_action in self.pending_actions:
            if self.action_status[action_id] == ActionStatus.PENDING:
                pending.append((action_id, blocked_action))
        
        # Sort by priority (highest first) then by timestamp
        pending.sort(key=lambda x: (-x[1].priority, x[1].timestamp))
        return pending
    
    def get_next_action(self) -> Optional[tuple[str, BlockedAction]]:
        """Get the highest priority pending action."""
        if not self.pending_actions:
            return None
            
        # Peek at the highest priority item
        priority, timestamp, action_id, blocked_action = self.pending_actions[0]
        
        if self.action_status[action_id] == ActionStatus.PENDING:
            return (action_id, blocked_action)
        else:
            # Remove stale items and try again
            heapq.heappop(self.pending_actions)
            return self.get_next_action()
    
    def _get_timestamp(self) -> float:
        """Generate a timestamp for action ordering."""
        import time
        return time.time()

# Global instance
intervention_trigger = InterventionTrigger()