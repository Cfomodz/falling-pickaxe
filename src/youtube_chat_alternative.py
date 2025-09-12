"""
Alternative YouTube chat reader using the same endpoint YouTube's web player uses
No API key needed - works like browser-based chat readers
"""

import requests
import json
import time
from typing import List, Dict, Optional
import re

class YouTubeChatReader:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
        self.continuation = None
        self.seen_messages = set()
    
    def get_initial_data(self, video_id: str) -> Optional[Dict]:
        """Get initial page data including chat continuation token"""
        url = f"https://www.youtube.com/watch?v={video_id}"
        
        try:
            response = self.session.get(url)
            response.raise_for_status()
            
            # Extract initial data from page
            match = re.search(r'var ytInitialData = ({.*?});', response.text)
            if match:
                return json.loads(match.group(1))
            else:
                print(f"⚠️ Could not find ytInitialData in page for video {video_id}")
        except Exception as e:
            print(f"❌ Error getting initial data: {e}")
        return None
    
    def get_live_chat_continuation(self, initial_data: Dict) -> Optional[str]:
        """Extract continuation token for live chat"""
        try:
            # Navigate through the nested structure to find chat continuation
            contents = initial_data.get('contents', {})
            two_column = contents.get('twoColumnWatchNextResults', {})
            conversation_bar = two_column.get('conversationBar', {})
            
            # Check if live chat is available
            if 'liveChatRenderer' not in conversation_bar:
                # Silently fail - stream might not be live
                return None
                
            live_chat = conversation_bar.get('liveChatRenderer', {})
            
            continuations = live_chat.get('continuations', [])
            if continuations:
                continuation_data = continuations[0].get('reloadContinuationData', {})
                token = continuation_data.get('continuation')
                return token
        except Exception as e:
            print(f"❌ Error extracting continuation: {e}")
            import traceback
            traceback.print_exc()
        return None
    
    def get_chat_messages(self, continuation: str) -> List[Dict]:
        """Fetch chat messages using continuation token"""
        url = "https://www.youtube.com/youtubei/v1/live_chat/get_live_chat"
        
        # Build request payload
        payload = {
            "context": {
                "client": {
                    "clientName": "WEB",
                    "clientVersion": "2.20240101.00.00"
                }
            },
            "continuation": continuation
        }
        
        try:
            response = self.session.post(url, json=payload)
            response.raise_for_status()
            data = response.json()
            
            messages = []
            actions = data.get('continuationContents', {}).get('liveChatContinuation', {}).get('actions', [])
            
            # Debug: Check if we got any actions
            if not actions:
                # This is normal for polls with no new messages, don't treat as error
                pass
            
            for action in actions:
                if 'addChatItemAction' in action:
                    item = action['addChatItemAction'].get('item', {})
                    
                    # Extract message renderer
                    renderer = None
                    if 'liveChatTextMessageRenderer' in item:
                        renderer = item['liveChatTextMessageRenderer']
                    elif 'liveChatPaidMessageRenderer' in item:
                        renderer = item['liveChatPaidMessageRenderer']
                    elif 'liveChatPaidStickerRenderer' in item:
                        renderer = item['liveChatPaidStickerRenderer']
                    
                    if renderer:
                        # Extract message details
                        message_id = renderer.get('id', '')
                        if message_id and message_id not in self.seen_messages:
                            self.seen_messages.add(message_id)
                            
                            author = renderer.get('authorName', {}).get('simpleText', 'Unknown')
                            
                            # Extract message text
                            message_parts = []
                            # Handle regular messages and paid messages
                            if 'message' in renderer:
                                for run in renderer.get('message', {}).get('runs', []):
                                    if 'text' in run:
                                        message_parts.append(run['text'])
                                    elif 'emoji' in run:
                                        message_parts.append(run['emoji'].get('shortcuts', [''])[0])
                            # Handle paid stickers (they might not have message text)
                            elif 'purchaseAmountText' in renderer:
                                # For paid stickers, use a placeholder message
                                message_parts.append('[Sticker]')
                            
                            message_text = ''.join(message_parts)
                            
                            if message_text:
                                messages.append({
                                    'author': author,
                                    'message': message_text,
                                    'id': message_id
                                })
            
            # Update continuation for next request
            continuations = data.get('continuationContents', {}).get('liveChatContinuation', {}).get('continuations', [])
            if continuations:
                # Try different continuation data structures
                continuation_data = None
                for cont in continuations:
                    # Timed continuation is for regular polling
                    if 'timedContinuationData' in cont:
                        continuation_data = cont['timedContinuationData']
                        # YouTube might specify a timeout (in ms) to control polling rate
                        timeout_ms = continuation_data.get('timeoutMs', 0)
                        if timeout_ms > 0:
                            # Respect YouTube's polling rate hint
                            time.sleep(timeout_ms / 1000.0)
                        break
                    # Invalidation continuation is for when chat updates
                    elif 'invalidationContinuationData' in cont:
                        continuation_data = cont['invalidationContinuationData']
                        break
                    # Reload continuation is for full refresh
                    elif 'reloadContinuationData' in cont:
                        continuation_data = cont['reloadContinuationData']
                        break
                
                if continuation_data:
                    new_continuation = continuation_data.get('continuation')
                    if new_continuation:
                        # Always update the continuation token
                        self.continuation = new_continuation
                    # If no new token, keep using the existing one
                # Don't print warnings for normal polling responses
            # If no continuations, this is normal for some responses, keep existing token
            
            return messages
            
        except Exception as e:
            print(f"Error fetching messages: {e}")
            return []
    
    def initialize_chat(self, video_id: str, verbose: bool = False) -> bool:
        """Initialize chat for a video"""
        if verbose:
            print(f"Initializing chat for video {video_id}...")
        
        initial_data = self.get_initial_data(video_id)
        if not initial_data:
            if verbose:
                print("Failed to get initial data")
            return False
        
        self.continuation = self.get_live_chat_continuation(initial_data)
        if not self.continuation:
            if verbose:
                print("Failed to get chat continuation token")
                print("Note: Chat might not be available (stream not live or chat disabled)")
            return False
        
        if verbose:
            print("Chat initialized successfully!")
        return True
    
    def poll_messages(self) -> List[Dict]:
        """Poll for new messages"""
        if not self.continuation:
            # Silently return empty - re-initialization will be handled by the wrapper
            return []
        
        return self.get_chat_messages(self.continuation)


# Compatibility wrapper to work with existing code
# Track initialization attempts to avoid spam
_init_attempt_count = 0
_last_init_time = 0

def get_alternative_chat_messages(video_id: str, reader: Optional[YouTubeChatReader] = None) -> tuple[List[Dict], YouTubeChatReader]:
    """
    Get chat messages without API key
    Returns (messages, reader) - pass reader back for subsequent calls
    """
    global _init_attempt_count, _last_init_time
    
    if reader is None:
        reader = YouTubeChatReader()
        # First initialization should be verbose
        if not reader.initialize_chat(video_id, verbose=True):
            return [], reader
    elif reader.continuation is None:
        # Rate limit re-initialization attempts
        current_time = time.time()
        if current_time - _last_init_time < 30:  # Don't re-init more than once per 30 seconds
            return [], reader
        
        # Re-initialize if continuation token is lost, but preserve seen messages
        _init_attempt_count += 1
        verbose = (_init_attempt_count % 10 == 1)  # Only verbose every 10th attempt
        if verbose:
            print(f"🔄 Re-initializing chat reader (attempt #{_init_attempt_count})...")
        
        old_seen_messages = reader.seen_messages.copy()
        if not reader.initialize_chat(video_id, verbose=verbose):
            return [], reader
        # Restore seen messages to avoid duplicates
        reader.seen_messages = old_seen_messages
        _last_init_time = current_time
    
    messages = reader.poll_messages()
    
    # Format messages to match existing format
    formatted_messages = []
    for msg in messages:
        formatted_messages.append({
            'author': msg['author'],
            'message': msg['message'],
            'timestamp': time.strftime("%Y-%m-%d %H:%M:%S"),
            'sc_details': None,
            'ss_details': None
        })
    
    return formatted_messages, reader


if __name__ == "__main__":
    # Test with your stream
    video_id = "oQ6PQvmNHeA"
    
    print("Testing alternative chat reader...")
    print("=" * 50)
    
    reader = YouTubeChatReader()
    if reader.initialize_chat(video_id, verbose=True):
        print("\nFetching messages...")
        messages = reader.poll_messages()
        
        print(f"Got {len(messages)} messages:")
        for msg in messages[:5]:
            print(f"  - {msg['author']}: {msg['message']}")
        
        print("\nThis method doesn't require an API key!")
    else:
        print("Could not initialize chat (stream might not be live)")
