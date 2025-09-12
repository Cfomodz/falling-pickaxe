"""
Smart Subscriber Estimation System
Learns your channel's growth rate and estimates individual subscribers
"""

import time
import json
from pathlib import Path
from datetime import datetime, timedelta

class SmartSubscriberEstimator:
    def __init__(self, save_file="subscriber_data.json"):
        self.save_file = Path(__file__).parent.parent / save_file
        self.data = self.load_data()
        
        # Default: estimate 1 sub every 10 minutes
        self.estimated_subs_per_minute = self.data.get('subs_per_minute', 1/10)
        self.last_actual_count = self.data.get('last_count', None)
        self.last_count_time = self.data.get('last_time', time.time())
        self.estimated_subs_since_last = 0
        self.last_estimated_sub_time = time.time()
        
        # Learning data
        self.count_history = self.data.get('history', [])
        
    def load_data(self):
        """Load saved estimation data"""
        if self.save_file.exists():
            try:
                with open(self.save_file, 'r') as f:
                    return json.load(f)
            except:
                pass
        return {}
    
    def save_data(self):
        """Save estimation data"""
        self.data = {
            'subs_per_minute': self.estimated_subs_per_minute,
            'last_count': self.last_actual_count,
            'last_time': self.last_count_time,
            'history': self.count_history[-100:]  # Keep last 100 data points
        }
        with open(self.save_file, 'w') as f:
            json.dump(self.data, f)
    
    def update_actual_count(self, new_count):
        """
        Called when we get an actual subscriber count from API
        Returns True if we detected a significant jump (100+ subs)
        """
        current_time = time.time()
        
        if self.last_actual_count is None:
            self.last_actual_count = new_count
            self.last_count_time = current_time
            self.save_data()
            return False
        
        # Check if count increased
        if new_count > self.last_actual_count:
            count_diff = new_count - self.last_actual_count
            time_diff_minutes = (current_time - self.last_count_time) / 60
            
            # Add to history
            self.count_history.append({
                'time': current_time,
                'count': new_count,
                'diff': count_diff,
                'minutes': time_diff_minutes
            })
            
            # If we got a 100+ jump (YouTube rounds to nearest 100 at 10k+)
            if count_diff >= 100:
                # Calculate actual growth rate
                if time_diff_minutes > 0:
                    actual_subs_per_minute = count_diff / time_diff_minutes
                    
                    # Update our estimate (weighted average with previous estimate)
                    self.estimated_subs_per_minute = (
                        self.estimated_subs_per_minute * 0.3 + 
                        actual_subs_per_minute * 0.7
                    )
                    
                    print(f"📊 Subscriber Growth Rate Updated!")
                    print(f"   Jump: +{count_diff} subs in {time_diff_minutes:.1f} minutes")
                    print(f"   New rate: ~{self.estimated_subs_per_minute:.2f} subs/minute")
                    print(f"   Estimated time between subs: {1/self.estimated_subs_per_minute:.1f} minutes")
                
                # Reset counters
                self.last_actual_count = new_count
                self.last_count_time = current_time
                self.estimated_subs_since_last = 0
                self.save_data()
                return True
            
            # Smaller increase (under 100)
            self.last_actual_count = new_count
            self.last_count_time = current_time
            self.save_data()
        
        return False
    
    def should_trigger_estimated_sub(self):
        """
        Check if enough time has passed to trigger an estimated subscriber
        Returns True if we should trigger a "new subscriber" event
        """
        current_time = time.time()
        minutes_since_last = (current_time - self.last_estimated_sub_time) / 60
        
        # Calculate minutes needed for one sub
        if self.estimated_subs_per_minute > 0:
            minutes_per_sub = 1 / self.estimated_subs_per_minute
        else:
            minutes_per_sub = 10  # Default to 10 minutes
        
        # Trigger if enough time has passed
        if minutes_since_last >= minutes_per_sub:
            self.last_estimated_sub_time = current_time
            self.estimated_subs_since_last += 1
            
            # Don't estimate more than 90 subs (leave room for actual detection)
            if self.estimated_subs_since_last < 90:
                return True
        
        return False
    
    def get_stats(self):
        """Get current estimation statistics"""
        return {
            'subs_per_minute': self.estimated_subs_per_minute,
            'subs_per_hour': self.estimated_subs_per_minute * 60,
            'subs_per_day': self.estimated_subs_per_minute * 60 * 24,
            'minutes_per_sub': 1 / self.estimated_subs_per_minute if self.estimated_subs_per_minute > 0 else 5,
            'estimated_since_last': self.estimated_subs_since_last
        }


# Example usage
if __name__ == "__main__":
    estimator = SmartSubscriberEstimator()
    
    print("Smart Subscriber Estimator")
    print("=" * 50)
    
    # Simulate subscriber growth
    print("\nSimulating subscriber growth...")
    
    # Start at 10,800
    estimator.update_actual_count(10800)
    
    # After 2 hours, we hit 10,900 (100 new subs)
    print("\n2 hours later: 10,900 subscribers")
    estimator.update_actual_count(10900)
    
    # Show stats
    stats = estimator.get_stats()
    print(f"\nLearned growth rate:")
    print(f"  - {stats['subs_per_hour']:.1f} subs/hour")
    print(f"  - {stats['minutes_per_sub']:.1f} minutes between subs")
    
    # Check when to trigger estimated subs
    print("\nChecking for estimated subscribers:")
    for i in range(10):
        if estimator.should_trigger_estimated_sub():
            print(f"  ✓ Trigger estimated subscriber #{i+1}")
        time.sleep(0.1)  # Simulate time passing
