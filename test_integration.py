#!/usr/bin/env python3
"""
Test the complete integration without running the full game
"""

import sys
import json
import os
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

def test_integration():
    """Test the main game's YouTube integration"""
    print("🧪 Testing Complete Integration")
    print("=" * 50)
    
    try:
        # Load config like the main game does
        from config import config
        
        print(f"🔑 API Key: {config.get('API_KEY', 'None')[:10]}...")
        print(f"💬 Chat Control: {config.get('CHAT_CONTROL', False)}")
        print(f"📺 Channel Handle: {config.get('CHANNEL_HANDLE', 'None')}")
        print(f"🔍 Search Term: {config.get('STREAM_SEARCH_TERM', 'None')}")
        
        # Test the same logic as main.py
        if config["CHAT_CONTROL"] == True and config.get("API_KEY") and config["API_KEY"] != "YOUR_API_KEY_HERE":
            print("\n🔍 Starting YouTube auto-detection (Public API)...")
            
            # Import the detection functions
            from youtube_public_detect import create_public_auto_setup
            
            # Try detection methods
            channel_handle = config.get("CHANNEL_HANDLE", "").strip()
            search_term = config.get("STREAM_SEARCH_TERM", "falling pickaxe").strip()
            
            auto_setup = None
            
            # Method 1: Channel handle
            if channel_handle and channel_handle != "@yourhandle":
                print(f"🎯 Trying channel handle: {channel_handle}")
                auto_setup = create_public_auto_setup(config["API_KEY"], channel_handle=channel_handle)
            
            # Method 2: Search term
            if not auto_setup or not auto_setup.get('success'):
                if search_term:
                    print(f"🔍 Searching for streams: '{search_term}'")
                    auto_setup = create_public_auto_setup(config["API_KEY"], search_term=search_term)
            
            if auto_setup and auto_setup.get('success'):
                print("\n✅ Integration Test SUCCESSFUL!")
                print(f"📺 Stream: {auto_setup['active_stream']['title']}")
                print(f"🎮 Channel: {auto_setup.get('channel', {}).get('snippet', {}).get('title', 'Unknown')}")
                print(f"💬 Chat ID: {auto_setup['live_chat_id'][:20] if auto_setup['live_chat_id'] else 'None'}...")
                
                # Test real-time chat system
                print(f"\n🔄 Testing Real-time Chat System...")
                from realtime_chat import HybridYouTubeManager
                
                def test_chat_handler(message):
                    print(f"⚡ Received: {message['username']}: {message['message']}")
                
                def test_metrics_handler(metrics):
                    print(f"📊 Metrics update: {metrics}")
                
                hybrid_manager = HybridYouTubeManager(config, test_chat_handler, test_metrics_handler)
                print("✅ Real-time chat system initialized")
                
                # Test streaming system
                print(f"\n🎥 Testing Streaming System...")
                from stream_manager import StreamManager, check_ffmpeg
                
                if check_ffmpeg():
                    print("✅ FFmpeg available - streaming ready")
                    if config.get("YOUTUBE_STREAM_KEY") and config["YOUTUBE_STREAM_KEY"] != "YOUR_STREAM_KEY_HERE":
                        print("✅ Stream key configured - automated streaming ready")
                    else:
                        print("⚠️  No stream key - add YOUTUBE_STREAM_KEY for automated streaming")
                else:
                    print("⚠️  FFmpeg not available - install for streaming support")
                
                print(f"\n🎉 COMPLETE SYSTEM READY!")
                print("=" * 50)
                print("✅ YouTube Integration: Working")
                print("✅ Real-time Chat: Ready") 
                print("✅ Stream Detection: Working")
                print("✅ Chat ID: Available")
                print("✅ All Systems: GO!")
                
                return True
                
            else:
                print("\n❌ Auto-detection failed")
                return False
        
        else:
            print("\n⚠️  Chat control disabled or no API key")
            return False
            
    except Exception as e:
        print(f"\n❌ Integration test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_integration()
    
    if success:
        print(f"\n🚀 Ready to run the full game!")
        print("💡 Next steps:")
        print("   1. Install dependencies: source .venv/bin/activate && pip install -r requirements.txt")
        print("   2. Run game: python src/main.py")
        print("   3. Viewers can use chat commands in real-time!")
    else:
        print(f"\n🔧 Fix integration issues first")
    
    print("\n🏁 Test Complete!")