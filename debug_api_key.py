#!/usr/bin/env python3
"""
Debug YouTube API key issues
"""

import requests
import json

def debug_api_key():
    """Debug the API key configuration"""
    print("🔧 YouTube API Key Debug Tool")
    print("=" * 40)
    
    # Load API key
    try:
        with open('default.config.json', 'r') as f:
            config = json.load(f)
        
        api_key = config.get('API_KEY')
        print(f"🔑 API Key found: {api_key[:10]}...{api_key[-4:]}")
        print(f"📏 Key length: {len(api_key)} characters")
        
        # Test different API endpoints to diagnose the issue
        endpoints_to_test = [
            {
                'name': 'Search (Public)',
                'url': 'https://www.googleapis.com/youtube/v3/search',
                'params': {'part': 'snippet', 'q': 'test', 'type': 'video', 'maxResults': 1, 'key': api_key}
            },
            {
                'name': 'Channels (My Channel)',  
                'url': 'https://www.googleapis.com/youtube/v3/channels',
                'params': {'part': 'snippet', 'mine': 'true', 'key': api_key}
            },
            {
                'name': 'Videos (Public)',
                'url': 'https://www.googleapis.com/youtube/v3/videos',
                'params': {'part': 'snippet', 'id': 'dQw4w9WgXcQ', 'key': api_key}
            }
        ]
        
        for test in endpoints_to_test:
            print(f"\n📡 Testing: {test['name']}")
            print("-" * 30)
            
            try:
                response = requests.get(test['url'], params=test['params'], timeout=10)
                
                print(f"Status: {response.status_code}")
                
                if response.status_code == 200:
                    data = response.json()
                    print(f"✅ Success! Items returned: {len(data.get('items', []))}")
                    
                elif response.status_code == 400:
                    error = response.json()
                    print(f"❌ Bad Request: {error}")
                    
                elif response.status_code == 401:
                    print("❌ Unauthorized - API key is invalid")
                    
                elif response.status_code == 403:
                    error = response.json()
                    error_details = error.get('error', {})
                    print(f"❌ Forbidden: {error_details.get('message', 'Unknown error')}")
                    
                    # Check specific error reasons
                    errors = error_details.get('errors', [])
                    for err in errors:
                        reason = err.get('reason', 'unknown')
                        print(f"   Reason: {reason}")
                        
                        if reason == 'quotaExceeded':
                            print("   💡 API quota exceeded - try tomorrow or upgrade quota")
                        elif reason == 'keyInvalid':
                            print("   💡 API key is invalid - check Google Cloud Console")
                        elif reason == 'accessNotConfigured':
                            print("   💡 YouTube Data API v3 not enabled - enable in Google Cloud Console")
                            
                else:
                    print(f"❌ Unexpected status: {response.status_code}")
                    print(f"Response: {response.text[:200]}")
                    
            except Exception as e:
                print(f"❌ Request failed: {e}")
        
        # Provide setup instructions
        print(f"\n💡 API Key Setup Checklist:")
        print("=" * 40)
        print("1. Go to https://console.cloud.google.com/")
        print("2. Create a project (or select existing)")
        print("3. Enable 'YouTube Data API v3'")
        print("4. Create credentials → API Key")
        print("5. Copy the API key to config.json")
        print("6. (Optional) Restrict the key to YouTube Data API v3")
        
        return api_key
        
    except Exception as e:
        print(f"❌ Error loading config: {e}")
        return None

if __name__ == "__main__":
    debug_api_key()