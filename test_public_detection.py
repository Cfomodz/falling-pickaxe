#!/usr/bin/env python3
"""
Test public YouTube detection (works with API key only)
"""

import sys
import json
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

def test_public_detection():
    """Test public detection methods"""
    print("🧪 Testing Public YouTube Detection")
    print("=" * 50)
    
    try:
        # Load config
        with open('default.config.json', 'r') as f:
            config = json.load(f)
        
        api_key = config.get('API_KEY')
        channel_handle = config.get('CHANNEL_HANDLE', '@yourhandle')
        search_term = config.get('STREAM_SEARCH_TERM', 'falling pickaxe')
        
        print(f"🔑 API Key: {api_key[:10]}...")
        print(f"📺 Channel Handle: {channel_handle}")
        print(f"🔍 Search Term: {search_term}")
        
        from youtube_public_detect import create_public_auto_setup
        
        # Test Method 1: Channel handle detection
        if channel_handle != "@yourhandle":
            print(f"\n🎯 Method 1: Auto-detect by channel handle")
            setup = create_public_auto_setup(api_key, channel_handle=channel_handle)
            
            if setup.get('success'):
                print("✅ Channel method successful!")
                return setup
            else:
                print("❌ Channel method failed")
        
        # Test Method 2: Search term detection
        print(f"\n🔍 Method 2: Search for live streams")
        setup = create_public_auto_setup(api_key, search_term=search_term)
        
        if setup.get('success'):
            print("✅ Search method successful!")
            print(f"📺 Found stream: {setup['active_stream']['title']}")
            print(f"🎮 Channel: {setup['active_stream']['channel_title']}")
            return setup
        else:
            print("❌ No live streams found with search term")
        
        # Test Method 3: Generic search
        print(f"\n🎲 Method 3: Search for any live gaming streams")
        setup = create_public_auto_setup(api_key, search_term="live gaming")
        
        if setup.get('success'):
            print("✅ Generic search successful!")
            print(f"📺 Found stream: {setup['active_stream']['title']}")
            return setup
            
        return {'success': False}
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        return {'success': False}
    except Exception as e:
        print(f"❌ Error: {e}")
        return {'success': False}

def show_setup_instructions():
    """Show setup instructions for different scenarios"""
    print("\n" + "=" * 50)
    print("💡 Setup Instructions")
    print("=" * 50)
    
    print("""
🎯 To enable zero-config detection, choose ONE method:

METHOD 1 - Channel Handle (Recommended):
{
    "CHANNEL_HANDLE": "@your-youtube-handle"
}

METHOD 2 - Stream Search:
{  
    "STREAM_SEARCH_TERM": "your stream title keywords"
}

METHOD 3 - Manual Fallback:
{
    "CHANNEL_ID": "UCyour-channel-id"
}

🔄 The system will try these methods in order until one works!
""")

if __name__ == "__main__":
    result = test_public_detection()
    
    if not result.get('success'):
        show_setup_instructions()
    else:
        print(f"\n🎉 SUCCESS! Ready to integrate with game")
        print(f"📋 Detection Summary:")
        print(f"   Stream: {result.get('active_stream', {}).get('title', 'Unknown')}")
        print(f"   Chat ID: {result.get('live_chat_id', 'None')}")
        print(f"   Channel: {result.get('channel', {}).get('snippet', {}).get('title', 'Unknown')}")
    
    print("\n🏁 Test Complete!")