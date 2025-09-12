"""
Like tracking system for YouTube video likes
Spawns 10x TNT for each new like detected
"""

import time
from typing import Optional, Tuple


class LikeTracker:
    """Tracks YouTube video likes and triggers rewards"""
    
    def __init__(self):
        self.highest_like_count: Optional[int] = None  # Track highest count ever seen
        self.current_like_count: Optional[int] = None  # Current count (for display)
        self.last_like_count: Optional[int] = None
        self.last_check_time: float = 0
        self.check_interval: float = 30.0  # Check every 30 seconds
        self.pending_tnt_rewards: int = 0  # TNT to spawn for new likes
        
    def update_like_count(self, new_count: Optional[int]) -> Tuple[bool, int]:
        """
        Update the like count and check for new likes
        Only counts increases, never decreases (prevents unlike/re-like exploits)
        Returns: (has_new_likes, new_like_count)
        """
        if new_count is None:
            return False, 0
            
        # First time initialization
        if self.highest_like_count is None:
            self.highest_like_count = new_count
            self.current_like_count = new_count
            self.last_like_count = new_count
            # print(f"📊 Initial like count: {new_count}")  # Removed for performance
            return False, 0
            
        # Update current count for display purposes
        self.current_like_count = new_count
        
        # Only process if it's higher than our highest seen count
        if new_count > self.highest_like_count:
            new_likes = new_count - self.highest_like_count
            self.last_like_count = self.highest_like_count
            self.highest_like_count = new_count
            
            # Add TNT rewards (10 per like)
            self.pending_tnt_rewards += new_likes * 10
            
            # Keep this - important event notification
            print(f"👍 NEW LIKES: +{new_likes} (Total: {new_count}) - Spawning {new_likes * 10} TNT!")
            
            return True, new_likes
            
        # If count went down or stayed same, ignore it
        return False, 0
        
    def should_check_likes(self) -> bool:
        """Check if it's time to poll for new likes"""
        current_time = time.time()
        if current_time - self.last_check_time >= self.check_interval:
            self.last_check_time = current_time
            return True
        return False
        
    def consume_tnt_reward(self) -> bool:
        """
        Consume one TNT reward if available
        Returns True if a TNT should be spawned
        """
        if self.pending_tnt_rewards > 0:
            self.pending_tnt_rewards -= 1
            return True
        return False
        
    def get_pending_rewards(self) -> int:
        """Get number of pending TNT rewards"""
        return self.pending_tnt_rewards
        
    def get_like_stats(self) -> dict:
        """Get current like statistics"""
        return {
            "current_likes": self.current_like_count or 0,
            "last_likes": self.last_like_count or 0,
            "pending_tnt": self.pending_tnt_rewards,
            "time_until_check": max(0, self.check_interval - (time.time() - self.last_check_time))
        }


# Global instance
like_tracker = LikeTracker()
