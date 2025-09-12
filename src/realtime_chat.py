"""
Real-time event-driven chat system for ultra-low latency command processing
"""

import asyncio
import threading
import time
from typing import Callable, Optional, Dict, Any
from queue import Queue, Empty
import traceback


class RealtimeChatProcessor:
    """
    Event-driven chat processor that triggers callbacks immediately on new messages
    """
    
    def __init__(self, on_command_callback: Callable[[str, str], None]):
        """
        Initialize the realtime chat processor
        
        Args:
            on_command_callback: Function called with (author, command) when command detected
        """
        self.on_command_callback = on_command_callback
        self.message_queue = Queue()
        self.running = False
        self.processing_thread = None
        self.polling_thread = None
        self.last_poll_time = 0
        self.poll_interval = 0.5  # Poll every 500ms for ultra-low latency
        self.startup_complete = False  # Track if we've cleared initial messages
        
        # Command patterns to detect
        self.command_patterns = {
            "tnt": ["tnt", "boom", "explode"],
            "fast": ["fast", "speed", "quick"],
            "slow": ["slow", "snail"],
            "big": ["big", "large", "huge"],
            "wood": ["wood", "wooden"],
            "stone": ["stone"],
            "iron": ["iron"],
            "gold": ["gold", "golden"],
            "diamond": ["diamond"],
            "netherite": ["netherite"],
            "rainbow": ["rainbow"],
            "shield": ["shield", "protect"],
            "freeze": ["freeze", "stop", "pause"]
        }
        
    def start(self):
        """Start the realtime chat processor"""
        if self.running:
            return
            
        self.running = True
        
        # Clear any existing messages on startup to avoid processing history
        self._clear_initial_messages()
        
        # Start processing thread
        self.processing_thread = threading.Thread(
            target=self._process_messages,
            daemon=True
        )
        self.processing_thread.start()
        
        # Start polling thread
        self.polling_thread = threading.Thread(
            target=self._poll_chat,
            daemon=True
        )
        self.polling_thread.start()
        
        # print("🚀 Realtime chat processor started!")  # Removed for performance
        
    def stop(self):
        """Stop the realtime chat processor"""
        self.running = False
        if self.processing_thread:
            self.processing_thread.join(timeout=1)
        if self.polling_thread:
            self.polling_thread.join(timeout=1)
            
    def _poll_chat(self):
        """Poll for new chat messages in a separate thread"""
        while self.running:
            try:
                current_time = time.time()
                
                # Rate limit polling
                if current_time - self.last_poll_time < self.poll_interval:
                    time.sleep(0.1)
                    continue
                    
                self.last_poll_time = current_time
                
                # Get new messages (non-blocking)
                self._fetch_new_messages()
                
            except Exception as e:
                print(f"Error in chat polling: {e}")
                traceback.print_exc()
                time.sleep(1)  # Wait before retrying
                
    def _clear_initial_messages(self):
        """Clear all existing messages on startup to avoid processing history"""
        try:
            from config import config
            
            if not config.get("LIVESTREAM_ID"):
                print("⚠️ No LIVESTREAM_ID configured")
                return
                
            print(f"🔄 Initializing chat for stream: {config['LIVESTREAM_ID']}")
            
            # Fetch messages once to mark them all as "seen"
            from youtube import get_new_live_chat_messages_alternative
            initial_messages = get_new_live_chat_messages_alternative(config["LIVESTREAM_ID"])
            
            if initial_messages:
                print(f"✅ Chat initialized! Skipping {len(initial_messages)} historical messages")
            else:
                print("⚠️ Chat initialized but no messages received (stream might not be live)")
            
            # Wait a moment to ensure we don't process messages twice
            time.sleep(1)
            self.startup_complete = True
            
        except Exception as e:
            print(f"❌ Error clearing initial messages: {e}")
            import traceback
            traceback.print_exc()
            self.startup_complete = True  # Continue anyway
    
    def _fetch_new_messages(self):
        """Fetch new messages from YouTube"""
        try:
            from config import config
            
            if not config.get("LIVESTREAM_ID"):
                return
            
            # Skip if we haven't cleared initial messages yet
            if not self.startup_complete:
                return
                
            # Use alternative method for no API quota usage
            from youtube import get_new_live_chat_messages_alternative
            new_messages = get_new_live_chat_messages_alternative(config["LIVESTREAM_ID"])
            
            # Queue messages for processing
            for message in new_messages:
                self.message_queue.put(message)
                
        except Exception as e:
            # Log errors but don't spam - only show every 10th error
            if not hasattr(self, '_error_count'):
                self._error_count = 0
            self._error_count += 1
            if self._error_count % 10 == 1:
                print(f"⚠️ Chat fetch error (shown every 10 errors): {e}")
                import traceback
                traceback.print_exc()
            
    def _process_messages(self):
        """Process messages from the queue"""
        while self.running:
            try:
                # Get message with timeout
                try:
                    message = self.message_queue.get(timeout=0.1)
                except Empty:
                    continue
                    
                # Process the message
                self._handle_message(message)
                
            except Exception as e:
                print(f"Error processing message: {e}")
                traceback.print_exc()
                
    def _handle_message(self, message: Dict[str, Any]):
        """
        Handle a single message and trigger callbacks for commands
        """
        try:
            author = message.get("author", "Unknown")
            text = message.get("message", "").lower()
            is_superchat = message.get("sc_details") is not None
            is_supersticker = message.get("ss_details") is not None
            
            # Check for commands
            detected_commands = []
            
            for command, patterns in self.command_patterns.items():
                for pattern in patterns:
                    if pattern in text:
                        detected_commands.append(command)
                        break
                        
            # Special handling for pickaxe types
            pickaxe_commands = {
                "wood": "wooden_pickaxe",
                "stone": "stone_pickaxe", 
                "iron": "iron_pickaxe",
                "gold": "golden_pickaxe",
                "diamond": "diamond_pickaxe",
                "netherite": "netherite_pickaxe"
            }
            
            # Process detected commands
            for command in detected_commands:
                # Convert pickaxe commands
                if command in pickaxe_commands:
                    actual_command = pickaxe_commands[command]
                else:
                    actual_command = command
                    
                # Trigger callback immediately
                self.on_command_callback(author, actual_command)
                
                # Log for debugging
                # Keep this - shows actual commands being processed
                print(f"⚡ INSTANT: {author} -> {actual_command}")
                
            # Handle superchats/superstickers
            if is_superchat or is_supersticker:
                # Superchats get special TNT
                self.on_command_callback(author, "superchat_tnt")
                
                if is_superchat and message.get("sc_details"):
                    amount = message["sc_details"].get("amountDisplayString", "")
                    print(f"💰 SUPER CHAT: {author} - {amount}")
                elif is_supersticker:
                    print(f"🎁 SUPER STICKER: {author}")
                    
            # Check for membership events
            text_lower = text.lower()
            member_patterns = ["became a member", "joined as a member", "is now a member", "new member"]
            for pattern in member_patterns:
                if pattern in text_lower:
                    print(f"🌟 NEW MEMBER: {author}!")
                    self.on_command_callback(author, "new_member")
                    break
                    
        except Exception as e:
            print(f"Error handling message: {e}")
            traceback.print_exc()


class AsyncRealtimeChat:
    """
    Async wrapper for integration with existing asyncio code
    """
    
    def __init__(self, competitive_system):
        self.competitive_system = competitive_system
        self.processor = RealtimeChatProcessor(self._on_command)
        self.event_callbacks = []
        
    def _on_command(self, author: str, command: str):
        """Handle command from chat"""
        try:
            # Process through competitive system
            result = self.competitive_system.process_command(author, command)
            
            # Trigger event callbacks
            for callback in self.event_callbacks:
                try:
                    callback(author, command, result)
                except Exception as e:
                    print(f"Error in event callback: {e}")
                    
        except Exception as e:
            print(f"Error processing command: {e}")
            traceback.print_exc()
            
    def add_event_callback(self, callback: Callable):
        """Add a callback for command events"""
        self.event_callbacks.append(callback)
        
    def start(self):
        """Start the realtime chat system"""
        self.processor.start()
        
    def stop(self):
        """Stop the realtime chat system"""
        self.processor.stop()
        
    async def handle_subscriber_event(self, subscriber_name: Optional[str] = None):
        """Handle new subscriber event"""
        if subscriber_name:
            self._on_command(subscriber_name, "new_subscriber")
        else:
            self._on_command("Anonymous", "new_subscriber")
            
    async def handle_hourly_event(self, hour: int):
        """Handle hourly event"""
        self._on_command("System", f"hourly_event_{hour}")
