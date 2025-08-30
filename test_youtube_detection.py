#!/usr/bin/env python3
"""
Test script for YouTube auto-detection system
"""

import sys
import json
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

def test_youtube_detection():
    """Test the YouTube auto-detection with real API key"""
    print("🧪 Testing YouTube Auto-Detection System")
    print("=" * 50)
    
    try:
        # Load config
        with open('default.config.json', 'r') as f:
            config = json.load(f)
        
        api_key = config.get('API_KEY')
        if not api_key or api_key == 'YOUR_API_KEY_HERE':
            print("❌ No API key found in config")
            print("💡 Add your YouTube Data API v3 key to default.config.json")
            return False
        
        print(f"🔑 API Key: {api_key[:10]}...")
        
        # Test the auto-detection system
        from youtube_auto_detect import create_zero_config_setup
        
        print("\n🔍 Starting zero-config detection...")
        setup = create_zero_config_setup(api_key)
        
        if setup.get('success'):
            print("\n✅ DETECTION SUCCESSFUL!")
            print(f"📺 Channel: {setup['channel']['snippet']['title']}")
            print(f"🆔 Channel ID: {setup['channel_id']}")
            print(f"📊 Subscribers: {setup['channel']['statistics'].get('subscriberCount', 'Hidden')}")
            
            if setup['live_streams']:
                stream = setup['active_stream']
                print(f"🔴 Active Stream: {stream['title']}")
                print(f"🎥 Video ID: {stream['video_id']}")
                print(f"💬 Chat ID: {setup['live_chat_id'][:20] if setup['live_chat_id'] else 'None'}...")
            else:
                print("⚠️  No active live streams found")
                print("💡 Start a live stream on YouTube to test chat integration")
            
            return True
        else:
            print("\n❌ DETECTION FAILED")
            return False
            
    except ImportError as e:
        print(f"❌ Import error: {e}")
        print("💡 Make sure dependencies are installed: pip install requests google-api-python-client")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def test_api_key_only():
    """Test just the API key validation"""
    print("\n🔑 Testing API Key Validation")
    print("-" * 30)
    
    try:
        import requests
        
        # Load API key
        with open('default.config.json', 'r') as f:
            config = json.load(f)
        
        api_key = config.get('API_KEY')
        
        # Simple API test
        url = "https://www.googleapis.com/youtube/v3/channels"
        params = {
            'part': 'snippet,statistics',
            'mine': 'true',
            'key': api_key,
            'maxResults': 1
        }
        
        print("📡 Testing API connection...")
        response = requests.get(url, params=params, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            if data.get('items'):
                channel = data['items'][0]
                print("✅ API Key Valid!")
                print(f"📺 Channel: {channel['snippet']['title']}")
                print(f"📊 Subscribers: {channel['statistics'].get('subscriberCount', 'Hidden')}")
                return True
            else:
                print("⚠️  API key works but no channel found")
        elif response.status_code == 401:
            print("❌ API Key Invalid")
        elif response.status_code == 403:
            print("❌ API Key lacks permissions or quota exceeded")
        else:
            print(f"❌ Unexpected response: {response.status_code}")
            print(response.text[:200])
        
        return False
        
    except Exception as e:
        print(f"❌ Error testing API key: {e}")
        return False

if __name__ == "__main__":
    print("🚀 YouTube Integration Test Suite")
    print("=" * 50)
    
    # Test 1: Simple API key validation
    api_valid = test_api_key_only()
    
    if api_valid:
        # Test 2: Full auto-detection
        test_youtube_detection()
    else:
        print("\n💡 Fix API key issues first, then run full detection test")
    
    print("\n" + "=" * 50)
    print("🏁 Test Complete!")