import asyncio
import websockets
import json
import threading
import time
import re
import requests
from urllib.parse import parse_qs, urlparse
import logging

class YouTubeChatWebSocket:
    def __init__(self, config, message_callback):
        self.config = config
        self.message_callback = message_callback
        self.websocket = None
        self.running = False
        self.thread = None
        
        # Chat connection details
        self.chat_url = None
        self.session_token = None
        self.continuation_token = None
        
        print("YouTube Real-time Chat initialized")
    
    async def connect_to_chat(self, video_id):
        """Connect to YouTube chat WebSocket for real-time messages"""
        try:
            # Get chat page to extract connection details
            chat_page_url = f"https://www.youtube.com/live_chat?v={video_id}"
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }
            
            response = requests.get(chat_page_url, headers=headers)
            if response.status_code != 200:
                print(f"❌ Failed to get chat page: {response.status_code}")
                return False
            
            # Extract session token and continuation from page
            page_content = response.text
            
            # Find continuation token in the page
            continuation_match = re.search(r'"continuation":"([^"]+)"', page_content)
            if not continuation_match:
                print("❌ Could not find chat continuation token")
                return False
            
            self.continuation_token = continuation_match.group(1)
            
            # Find session token
            session_match = re.search(r'"INNERTUBE_CONTEXT_CLIENT_NAME":1[^}]+?"sessionToken":"([^"]+)"', page_content)
            if session_match:
                self.session_token = session_match.group(1)
            
            print(f"✅ Chat tokens extracted for video: {video_id}")
            return True
            
        except Exception as e:
            print(f"❌ Chat connection error: {e}")
            return False
    
    async def poll_chat_messages(self):
        """Poll for new chat messages using continuation tokens"""
        url = "https://www.youtube.com/youtubei/v1/live_chat/get_live_chat"
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Content-Type': 'application/json'
        }
        
        payload = {
            "context": {
                "client": {
                    "clientName": "WEB",
                    "clientVersion": "2.20220101.00.00"
                }
            },
            "continuation": self.continuation_token
        }
        
        if self.session_token:
            payload["context"]["client"]["sessionToken"] = self.session_token
        
        try:
            response = requests.post(url, headers=headers, json=payload, timeout=10)
            if response.status_code == 200:
                data = response.json()
                return self.process_chat_response(data)
        except Exception as e:
            print(f"Chat polling error: {e}")
        
        return []
    
    def process_chat_response(self, data):
        """Process chat response and extract messages"""
        messages = []
        
        try:
            # Navigate the YouTube API response structure
            if "continuationContents" in data:
                live_chat = data["continuationContents"]["liveChatContinuation"]
                
                # Update continuation token for next request
                if "continuations" in live_chat:
                    for continuation in live_chat["continuations"]:
                        if "invalidationContinuationData" in continuation:
                            self.continuation_token = continuation["invalidationContinuationData"]["continuation"]
                        elif "timedContinuationData" in continuation:
                            self.continuation_token = continuation["timedContinuationData"]["continuation"]
                
                # Extract messages
                if "actions" in live_chat:
                    for action in live_chat["actions"]:
                        if "addChatItemAction" in action:
                            item = action["addChatItemAction"]["item"]
                            message = self.parse_chat_message(item)
                            if message:
                                messages.append(message)
                                
        except Exception as e:
            print(f"Error processing chat response: {e}")
        
        return messages
    
    def parse_chat_message(self, item):
        """Parse individual chat message from YouTube response"""
        try:
            if "liveChatTextMessageRenderer" in item:
                renderer = item["liveChatTextMessageRenderer"]
                
                # Extract username
                username = "Unknown"
                if "authorName" in renderer:
                    username = renderer["authorName"]["simpleText"]
                
                # Extract message text
                message_text = ""
                if "message" in renderer:
                    if "simpleText" in renderer["message"]:
                        message_text = renderer["message"]["simpleText"]
                    elif "runs" in renderer["message"]:
                        message_text = "".join([run.get("text", "") for run in renderer["message"]["runs"]])
                
                # Extract timestamp
                timestamp = int(renderer.get("timestampUsec", 0)) // 1000
                
                # Check if it's a super chat
                is_super_chat = "liveChatPaidMessageRenderer" in item
                super_chat_amount = 0
                
                if is_super_chat:
                    paid_renderer = item["liveChatPaidMessageRenderer"]
                    if "purchaseAmountText" in paid_renderer:
                        amount_text = paid_renderer["purchaseAmountText"]["simpleText"]
                        # Extract numeric amount (basic parsing)
                        import re
                        amount_match = re.search(r'[\d.]+', amount_text)
                        if amount_match:
                            super_chat_amount = float(amount_match.group())
                
                return {
                    "username": username,
                    "message": message_text.lower().strip(),
                    "timestamp": timestamp,
                    "is_super_chat": is_super_chat,
                    "super_chat_amount": super_chat_amount,
                    "raw": item  # Keep full data for debugging
                }
                
        except Exception as e:
            print(f"Error parsing message: {e}")
        
        return None
    
    def start_chat_monitoring(self, video_id):
        """Start monitoring chat in a separate thread"""
        if self.running:
            return False
        
        self.running = True
        self.thread = threading.Thread(target=self._run_chat_monitor, args=(video_id,))
        self.thread.daemon = True
        self.thread.start()
        return True
    
    def _run_chat_monitor(self, video_id):
        """Run the chat monitoring loop"""
        asyncio.set_event_loop(asyncio.new_event_loop())
        loop = asyncio.get_event_loop()
        
        try:
            # Connect to chat
            if not loop.run_until_complete(self.connect_to_chat(video_id)):
                print("❌ Failed to connect to YouTube chat")
                return
            
            print("✅ Real-time chat monitoring started!")
            
            # Poll for messages every 1-2 seconds
            while self.running:
                messages = loop.run_until_complete(self.poll_chat_messages())
                
                # Process new messages
                for message in messages:
                    if self.message_callback:
                        self.message_callback(message)
                
                # Wait before next poll (much faster than API polling)
                time.sleep(1.5)
                
        except Exception as e:
            print(f"❌ Chat monitoring error: {e}")
        finally:
            self.running = False
            print("📴 Real-time chat monitoring stopped")
    
    def stop_chat_monitoring(self):
        """Stop chat monitoring"""
        self.running = False
        if self.thread:
            self.thread.join(timeout=5)
    
    def is_running(self):
        """Check if chat monitoring is running"""
        return self.running


class HybridYouTubeManager:
    """Manages both real-time chat and periodic polling for metrics"""
    
    def __init__(self, config, chat_callback, metrics_callback, youtube_service=None):
        self.config = config
        self.chat_callback = chat_callback
        self.metrics_callback = metrics_callback
        self.youtube_service = youtube_service  # OAuth YouTube service for real API calls
        
        # Real-time chat
        self.chat_websocket = YouTubeChatWebSocket(config, self._handle_chat_message)
        
        # Metrics polling (optimized intervals)
        self.metrics_thread = None
        self.metrics_running = False
        
        self.last_like_count = 0
        self.last_subscriber_count = 0
        self.last_view_count = 0
        
        print("Hybrid YouTube Manager initialized")
    
    def _handle_chat_message(self, message):
        """Handle incoming real-time chat messages"""
        print(f"💬 Real-time chat: {message['username']}: {message['message']}")
        
        # Process super chats immediately
        if message['is_super_chat']:
            print(f"💰 Super Chat ${message['super_chat_amount']} from {message['username']}")
        
        # Forward to game
        if self.chat_callback:
            self.chat_callback(message)
    
    def start_monitoring(self, video_id, channel_id):
        """Start both real-time chat and metrics polling"""
        print("🚀 Starting hybrid YouTube monitoring...")
        
        # Start real-time chat
        success = self.chat_websocket.start_chat_monitoring(video_id)
        if success:
            print("✅ Real-time chat started")
        else:
            print("⚠️  Real-time chat failed, using polling fallback")
        
        # Start metrics polling
        self.metrics_running = True
        self.metrics_thread = threading.Thread(target=self._metrics_polling_loop, args=(video_id, channel_id))
        self.metrics_thread.daemon = True
        self.metrics_thread.start()
        print("✅ Metrics polling started")
    
    def _metrics_polling_loop(self, video_id, channel_id):
        """Optimized polling for likes, subs, and viewers"""
        like_interval = 30      # Poll likes every 30 seconds
        sub_interval = 120      # Poll subs every 2 minutes  
        viewer_interval = 10    # Poll viewers every 10 seconds
        
        last_like_poll = 0
        last_sub_poll = 0
        last_viewer_poll = 0
        
        while self.metrics_running:
            current_time = time.time()
            
            try:
                # Poll viewers (most frequent)
                if current_time - last_viewer_poll >= viewer_interval:
                    self._poll_viewer_count(video_id)
                    last_viewer_poll = current_time
                
                # Poll likes (moderate frequency)
                if current_time - last_like_poll >= like_interval:
                    self._poll_like_count(video_id)
                    last_like_poll = current_time
                
                # Poll subscribers (least frequent)
                if current_time - last_sub_poll >= sub_interval:
                    self._poll_subscriber_count(channel_id)
                    last_sub_poll = current_time
                
            except Exception as e:
                print(f"Metrics polling error: {e}")
            
            time.sleep(5)  # Base sleep interval
    
    def _poll_viewer_count(self, video_id):
        """Poll current live viewer count"""
        try:
            if hasattr(self, 'youtube_service') and self.youtube_service:
                response = self.youtube_service.videos().list(
                    part='liveStreamingDetails',
                    id=video_id
                ).execute()
                
                if response['items']:
                    live_details = response['items'][0].get('liveStreamingDetails', {})
                    concurrent_viewers = live_details.get('concurrentViewers')
                    if concurrent_viewers:
                        # Could trigger viewer milestone events here
                        if hasattr(self, 'metrics_callback'):
                            self.metrics_callback('viewers', int(concurrent_viewers))
        except Exception:
            pass  # Fail silently in production
    
    def _poll_like_count(self, video_id):
        """Poll current like count"""
        try:
            if hasattr(self, 'youtube_service') and self.youtube_service:
                response = self.youtube_service.videos().list(
                    part='statistics',
                    id=video_id
                ).execute()
                
                if response['items']:
                    stats = response['items'][0].get('statistics', {})
                    like_count = stats.get('likeCount')
                    if like_count and hasattr(self, 'metrics_callback'):
                        self.metrics_callback('likes', int(like_count))
        except Exception:
            pass  # Fail silently in production
    
    def _poll_subscriber_count(self, channel_id):
        """Poll current subscriber count"""
        try:
            if hasattr(self, 'youtube_service') and self.youtube_service:
                response = self.youtube_service.channels().list(
                    part='statistics',
                    id=channel_id
                ).execute()
                
                if response['items']:
                    stats = response['items'][0].get('statistics', {})
                    sub_count = stats.get('subscriberCount')
                    if sub_count and hasattr(self, 'metrics_callback'):
                        self.metrics_callback('subscribers', int(sub_count))
        except Exception:
            pass  # Fail silently in production
    
    def stop_monitoring(self):
        """Stop all monitoring"""
        print("🛑 Stopping hybrid YouTube monitoring...")
        
        # Stop chat monitoring
        self.chat_websocket.stop_chat_monitoring()
        
        # Stop metrics polling
        self.metrics_running = False
        if self.metrics_thread:
            self.metrics_thread.join(timeout=5)
        
        print("📴 All monitoring stopped")
    
    def get_status(self):
        """Get current monitoring status"""
        return {
            "chat_active": self.chat_websocket.is_running(),
            "metrics_active": self.metrics_running,
            "last_like_count": self.last_like_count,
            "last_subscriber_count": self.last_subscriber_count,
            "last_view_count": self.last_view_count
        }


# Usage example for integration:
"""
def handle_chat_message(message):
    # Process real-time chat commands
    if message['message'] in ['tnt', 'fast', 'slow', etc.]:
        # Add to game queues immediately
        pass

def handle_metrics_update(metrics):
    # Handle subscriber/like count changes
    pass

# Initialize hybrid manager
hybrid_manager = HybridYouTubeManager(config, handle_chat_message, handle_metrics_update)
hybrid_manager.start_monitoring(video_id, channel_id)
"""