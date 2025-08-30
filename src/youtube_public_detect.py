import requests
import json
from typing import Optional, Dict, List

class YouTubePublicDetector:
    """Auto-detect YouTube streams using public API (no OAuth required)"""
    
    def __init__(self, api_key: str, channel_handle: Optional[str] = None):
        self.api_key = api_key
        self.base_url = "https://www.googleapis.com/youtube/v3"
        self.channel_handle = channel_handle  # e.g. "@username" or channel ID
        
    def find_channel_by_handle(self, handle: str) -> Optional[Dict]:
        """Find channel by handle/username (public search)"""
        # Remove @ if present
        clean_handle = handle.replace('@', '')
        
        # Search for the channel
        url = f"{self.base_url}/search"
        params = {
            'part': 'snippet',
            'type': 'channel',
            'q': clean_handle,
            'key': self.api_key,
            'maxResults': 5
        }
        
        try:
            response = requests.get(url, params=params)
            response.raise_for_status()
            data = response.json()
            
            for item in data.get('items', []):
                channel_title = item['snippet']['title'].lower()
                if clean_handle.lower() in channel_title:
                    channel_id = item['snippet']['channelId']
                    # Get full channel details
                    return self.get_channel_details(channel_id)
                    
        except Exception as e:
            print(f"❌ Error searching for channel: {e}")
        
        return None
    
    def get_channel_details(self, channel_id: str) -> Optional[Dict]:
        """Get channel details by ID"""
        url = f"{self.base_url}/channels"
        params = {
            'part': 'snippet,statistics,brandingSettings',
            'id': channel_id,
            'key': self.api_key
        }
        
        try:
            response = requests.get(url, params=params)
            response.raise_for_status()
            data = response.json()
            
            if data['items']:
                return data['items'][0]
                
        except Exception as e:
            print(f"❌ Error getting channel details: {e}")
        
        return None
    
    def find_live_streams_by_channel(self, channel_id: str) -> List[Dict]:
        """Find live streams for a specific channel"""
        live_streams = []
        
        try:
            # Search for live broadcasts from this channel
            search_url = f"{self.base_url}/search"
            search_params = {
                'part': 'snippet',
                'channelId': channel_id,
                'eventType': 'live',
                'type': 'video',
                'key': self.api_key,
                'maxResults': 10
            }
            
            response = requests.get(search_url, params=search_params)
            response.raise_for_status()
            search_data = response.json()
            
            for item in search_data.get('items', []):
                video_id = item['id']['videoId']
                title = item['snippet']['title']
                
                # Get detailed info
                video_details = self.get_video_details(video_id)
                if video_details and video_details.get('liveStreamingDetails'):
                    live_streams.append({
                        'video_id': video_id,
                        'title': title,
                        'details': video_details,
                        'channel_title': item['snippet']['channelTitle']
                    })
            
            print(f"🔴 Found {len(live_streams)} live stream(s)")
            for stream in live_streams:
                print(f"   📺 {stream['title']} (ID: {stream['video_id']})")
                
        except Exception as e:
            print(f"❌ Error finding live streams: {e}")
        
        return live_streams
    
    def get_video_details(self, video_id: str) -> Optional[Dict]:
        """Get detailed video information"""
        url = f"{self.base_url}/videos"
        params = {
            'part': 'snippet,statistics,liveStreamingDetails',
            'id': video_id,
            'key': self.api_key
        }
        
        try:
            response = requests.get(url, params=params)
            response.raise_for_status()
            data = response.json()
            
            if data['items']:
                return data['items'][0]
                
        except Exception as e:
            print(f"❌ Error getting video details: {e}")
        
        return None
    
    def get_live_chat_id(self, video_id: str) -> Optional[str]:
        """Get live chat ID from video"""
        try:
            video_details = self.get_video_details(video_id)
            if video_details and 'liveStreamingDetails' in video_details:
                live_details = video_details['liveStreamingDetails']
                return live_details.get('activeLiveChatId')
                    
        except Exception as e:
            print(f"❌ Error getting live chat ID: {e}")
        
        return None
    
    def auto_detect_by_handle(self, channel_handle: str) -> Dict:
        """Auto-detect everything by channel handle/username"""
        print(f"🔍 Auto-detecting streams for: {channel_handle}")
        
        result = {
            'channel': None,
            'channel_id': None,
            'live_streams': [],
            'active_stream': None,
            'live_chat_id': None,
            'success': False
        }
        
        # Step 1: Find the channel
        channel = self.find_channel_by_handle(channel_handle)
        if not channel:
            print(f"❌ Could not find channel: {channel_handle}")
            return result
        
        result['channel'] = channel
        result['channel_id'] = channel['id']
        print(f"✅ Found channel: {channel['snippet']['title']}")
        
        # Step 2: Find live streams
        live_streams = self.find_live_streams_by_channel(channel['id'])
        result['live_streams'] = live_streams
        
        if not live_streams:
            print("⚠️  No active live streams found")
            return result
        
        # Step 3: Use the first active stream
        active_stream = live_streams[0]
        result['active_stream'] = active_stream
        
        # Step 4: Get chat ID
        live_chat_id = self.get_live_chat_id(active_stream['video_id'])
        result['live_chat_id'] = live_chat_id
        
        if live_chat_id:
            result['success'] = True
            print("🎯 Auto-detection complete!")
            print(f"📺 Stream: {active_stream['title']}")
            print(f"💬 Chat ID: {live_chat_id[:20]}...")
        
        return result
    
    def search_recent_streams(self, search_term: str) -> List[Dict]:
        """Search for recent live streams by keyword"""
        print(f"🔍 Searching for streams: '{search_term}'")
        
        url = f"{self.base_url}/search"
        params = {
            'part': 'snippet',
            'q': search_term,
            'type': 'video',
            'eventType': 'live',
            'key': self.api_key,
            'maxResults': 10,
            'order': 'date'
        }
        
        streams = []
        try:
            response = requests.get(url, params=params)
            response.raise_for_status()
            data = response.json()
            
            for item in data.get('items', []):
                video_details = self.get_video_details(item['id']['videoId'])
                if video_details and video_details.get('liveStreamingDetails'):
                    streams.append({
                        'video_id': item['id']['videoId'],
                        'title': item['snippet']['title'],
                        'channel_title': item['snippet']['channelTitle'],
                        'details': video_details
                    })
            
            print(f"🔴 Found {len(streams)} matching streams")
            
        except Exception as e:
            print(f"❌ Error searching streams: {e}")
        
        return streams


def create_public_auto_setup(api_key: str, channel_handle: str = None, search_term: str = None) -> Dict:
    """Create auto-setup using public API only"""
    detector = YouTubePublicDetector(api_key, channel_handle)
    
    print("🚀 Public Auto-Detection (No OAuth Required)")
    print("=" * 50)
    
    if channel_handle:
        # Method 1: Auto-detect by channel handle
        setup = detector.auto_detect_by_handle(channel_handle)
        
        if setup['success']:
            print(f"\n✅ SUCCESS! Found stream for {channel_handle}")
            return setup
    
    if search_term:
        # Method 2: Search by keyword
        print(f"\n🔍 Searching for streams with: '{search_term}'")
        streams = detector.search_recent_streams(search_term)
        
        if streams:
            # Use the first stream found
            stream = streams[0]
            chat_id = detector.get_live_chat_id(stream['video_id'])
            
            return {
                'channel': {'snippet': {'title': stream['channel_title']}},
                'channel_id': None,  # Don't have channel ID from search
                'live_streams': streams,
                'active_stream': stream,
                'live_chat_id': chat_id,
                'success': True
            }
    
    print("\n❌ No streams found")
    print("💡 Try providing your channel handle (e.g., '@username') or a search term")
    
    return {'success': False}


# Example usage:
if __name__ == "__main__":
    api_key = "YOUR_API_KEY_HERE"
    
    # Test different methods
    print("Testing public auto-detection...")
    
    # Method 1: By channel handle
    # setup = create_public_auto_setup(api_key, channel_handle="@yourhandle")
    
    # Method 2: By search term  
    # setup = create_public_auto_setup(api_key, search_term="falling pickaxe")
    
    print("Update the API key and uncomment a method to test!")