import requests
import json
from typing import Optional, Dict, List

class YouTubeAutoDetector:
    """Automatically detects user's YouTube channel and active live streams"""
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://www.googleapis.com/youtube/v3"
        
    def get_my_channel(self) -> Optional[Dict]:
        """Get the channel associated with this API key"""
        url = f"{self.base_url}/channels"
        params = {
            'part': 'snippet,statistics,brandingSettings',
            'mine': 'true',
            'key': self.api_key
        }
        
        try:
            response = requests.get(url, params=params)
            response.raise_for_status()
            data = response.json()
            
            if data['items']:
                channel = data['items'][0]
                print(f"✅ Auto-detected channel: {channel['snippet']['title']}")
                print(f"📊 Subscribers: {channel['statistics'].get('subscriberCount', 'Hidden')}")
                return channel
            else:
                print("❌ No channel found for this API key")
                return None
                
        except Exception as e:
            print(f"❌ Error getting channel: {e}")
            return None
    
    def get_channel_live_streams(self, channel_id: str) -> List[Dict]:
        """Get all active live streams for a channel"""
        # First get live broadcasts
        live_streams = []
        
        try:
            # Search for live broadcasts
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
                
                # Get detailed info about the live stream
                video_details = self.get_video_details(video_id)
                if video_details and video_details.get('liveStreamingDetails'):
                    live_streams.append({
                        'video_id': video_id,
                        'title': title,
                        'details': video_details,
                        'thumbnail': item['snippet']['thumbnails']['default']['url']
                    })
            
            print(f"🔴 Found {len(live_streams)} active live stream(s)")
            for stream in live_streams:
                print(f"   📺 {stream['title']} (ID: {stream['video_id']})")
                
        except Exception as e:
            print(f"❌ Error getting live streams: {e}")
        
        return live_streams
    
    def get_video_details(self, video_id: str) -> Optional[Dict]:
        """Get detailed information about a video/stream"""
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
    
    def auto_detect_streaming_setup(self) -> Dict:
        """Automatically detect everything needed for streaming"""
        print("🔍 Auto-detecting YouTube streaming setup...")
        
        result = {
            'channel': None,
            'channel_id': None,
            'live_streams': [],
            'active_stream': None,
            'live_chat_id': None,
            'success': False
        }
        
        # Step 1: Get my channel
        channel = self.get_my_channel()
        if not channel:
            return result
        
        result['channel'] = channel
        result['channel_id'] = channel['id']
        
        # Step 2: Find active live streams
        live_streams = self.get_channel_live_streams(channel['id'])
        result['live_streams'] = live_streams
        
        if not live_streams:
            print("⚠️  No active live streams found")
            print("💡 Tip: Start a live stream on YouTube, then restart the game")
            return result
        
        # Step 3: Use the most recent/active stream
        active_stream = live_streams[0]  # Use first/most recent
        result['active_stream'] = active_stream
        
        # Step 4: Get live chat ID
        live_chat_id = self.get_live_chat_id(active_stream['video_id'])
        result['live_chat_id'] = live_chat_id
        
        if live_chat_id:
            result['success'] = True
            print("🎯 Auto-detection complete!")
            print(f"📺 Stream: {active_stream['title']}")
            print(f"💬 Chat ID: {live_chat_id[:20]}...")
        else:
            print("⚠️  Could not get live chat ID")
        
        return result
    
    def get_live_chat_id(self, video_id: str) -> Optional[str]:
        """Get the live chat ID for a video"""
        try:
            video_details = self.get_video_details(video_id)
            if video_details and 'liveStreamingDetails' in video_details:
                live_details = video_details['liveStreamingDetails']
                if 'activeLiveChatId' in live_details:
                    return live_details['activeLiveChatId']
                    
        except Exception as e:
            print(f"❌ Error getting live chat ID: {e}")
        
        return None
    
    def test_api_key(self) -> bool:
        """Test if the API key is valid and has necessary permissions"""
        print("🔑 Testing API key...")
        
        try:
            # Simple test - get quota info
            url = f"{self.base_url}/channels"
            params = {
                'part': 'snippet',
                'mine': 'true',
                'key': self.api_key,
                'maxResults': 1
            }
            
            response = requests.get(url, params=params)
            
            if response.status_code == 401:
                print("❌ API key is invalid")
                return False
            elif response.status_code == 403:
                error_data = response.json()
                if 'quotaExceeded' in str(error_data):
                    print("⚠️  API quota exceeded, but key is valid")
                    return True
                else:
                    print("❌ API key lacks necessary permissions")
                    print("💡 Make sure YouTube Data API v3 is enabled")
                    return False
            elif response.status_code == 200:
                print("✅ API key is valid and working")
                return True
            else:
                print(f"⚠️  Unexpected response: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"❌ Error testing API key: {e}")
            return False


def create_zero_config_setup(api_key: str) -> Dict:
    """Create a complete YouTube setup with just an API key"""
    detector = YouTubeAutoDetector(api_key)
    
    # Test API key first
    if not detector.test_api_key():
        return {'success': False, 'error': 'Invalid API key'}
    
    # Auto-detect everything
    setup = detector.auto_detect_streaming_setup()
    
    if setup['success']:
        print("\n🎉 ZERO-CONFIG SETUP COMPLETE!")
        print("✅ Channel detected")
        print("✅ Live stream detected") 
        print("✅ Chat integration ready")
        print("✅ Real-time monitoring ready")
        print("\n🚀 Ready to stream with full interactivity!")
    else:
        print("\n⚠️  Setup incomplete:")
        if setup['channel']:
            print("✅ Channel detected")
        else:
            print("❌ Could not detect channel")
            
        if setup['live_streams']:
            print("✅ Live streams found")
        else:
            print("❌ No active live streams")
            print("💡 Start a YouTube live stream to complete setup")
    
    return setup


# Usage example:
if __name__ == "__main__":
    # Test with your API key
    api_key = "YOUR_API_KEY_HERE"
    setup = create_zero_config_setup(api_key)
    
    if setup['success']:
        print(f"\nReady to use:")
        print(f"Channel ID: {setup['channel_id']}")
        print(f"Video ID: {setup['active_stream']['video_id']}")
        print(f"Chat ID: {setup['live_chat_id']}")