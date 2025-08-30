"""
Clean YouTube OAuth and Live Streaming API integration
Simplified version that works with YouTube's current system
"""

import json
import os
import webbrowser
import time
from datetime import datetime, timedelta
from pathlib import Path
import requests
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

class YouTubeOAuth:
    """Handles OAuth authentication and YouTube Live Streaming API"""
    
    # OAuth 2.0 scopes needed for live streaming
    SCOPES = [
        'https://www.googleapis.com/auth/youtube',
        'https://www.googleapis.com/auth/youtube.force-ssl'
    ]
    
    def __init__(self, credentials_file='client_credentials.json', token_file='youtube_token.json'):
        """
        Initialize OAuth handler
        
        Args:
            credentials_file: Path to OAuth client credentials from Google Cloud Console
            token_file: Path to store access/refresh tokens
        """
        self.credentials_file = credentials_file
        self.token_file = token_file
        self.credentials = None
        self.youtube_service = None
        
    def authenticate(self):
        """Perform OAuth flow and get authenticated YouTube service"""
        
        # Load existing token if available
        if os.path.exists(self.token_file):
            try:
                self.credentials = Credentials.from_authorized_user_file(self.token_file, self.SCOPES)
                print("📱 Loaded existing OAuth credentials")
            except Exception as e:
                print(f"⚠️ Error loading existing credentials: {e}")
                self.credentials = None
        
        # If there are no (valid) credentials available, let the user log in
        if not self.credentials or not self.credentials.valid:
            if self.credentials and self.credentials.expired and self.credentials.refresh_token:
                try:
                    print("🔄 Refreshing expired OAuth token...")
                    self.credentials.refresh(Request())
                    print("✅ Token refreshed successfully")
                except Exception as e:
                    print(f"❌ Token refresh failed: {e}")
                    self.credentials = None
            
            if not self.credentials:
                if not os.path.exists(self.credentials_file):
                    print(f"❌ OAuth credentials file not found: {self.credentials_file}")
                    print("💡 Please download OAuth client credentials from Google Cloud Console")
                    return False
                
                try:
                    print("🔐 Starting OAuth flow...")
                    print("📱 Opening browser for YouTube authentication...")
                    
                    flow = InstalledAppFlow.from_client_secrets_file(
                        self.credentials_file, self.SCOPES
                    )
                    self.credentials = flow.run_local_server(port=0, open_browser=True)
                    print("✅ OAuth authentication successful!")
                    
                except Exception as e:
                    print(f"❌ OAuth flow failed: {e}")
                    return False
            
            # Save the credentials for the next run
            try:
                with open(self.token_file, 'w') as token:
                    token.write(self.credentials.to_json())
                print(f"💾 OAuth credentials saved to {self.token_file}")
            except Exception as e:
                print(f"⚠️ Warning: Could not save credentials: {e}")
        
        # Build YouTube service
        try:
            self.youtube_service = build('youtube', 'v3', credentials=self.credentials)
            print("🚀 YouTube Live Streaming API service ready")
            return True
        except Exception as e:
            print(f"❌ Failed to build YouTube service: {e}")
            return False
    
    def create_live_stream(self, title="Live Gaming Stream", description="Automated live stream", thumbnail_path=None):
        """
        Create a new YouTube live stream using current YouTube system
        
        Returns:
            dict: Stream info with video_id, stream_key, rtmp_url, chat_id
        """
        if not self.youtube_service:
            print("❌ YouTube service not authenticated")
            return None
        
        try:
            # Modern YouTube Live Streaming: Create stream that auto-starts when RTMP connects
            print(f"🎬 Creating live stream: '{title}'")
            
            # Use current time for immediate start
            start_time = datetime.utcnow().isoformat() + 'Z'
            
            # Step 1: Create live broadcast
            broadcast_body = {
                'snippet': {
                    'title': title,
                    'description': description,
                    'scheduledStartTime': start_time
                },
                'status': {
                    'privacyStatus': 'public',
                    'selfDeclaredMadeForKids': False
                },
                'contentDetails': {
                    'enableAutoStart': True,    # KEY: Auto-start when RTMP detected
                    'enableAutoStop': False,    # Don't auto-stop  
                    'enableDvr': True,
                    'recordFromStart': True,
                    'startWithSlate': False
                }
            }
            
            broadcast_response = self.youtube_service.liveBroadcasts().insert(
                part='snippet,status,contentDetails',
                body=broadcast_body
            ).execute()
            
            broadcast_id = broadcast_response['id']
            video_id = broadcast_response['id']
            print(f"✅ Broadcast created: {video_id}")
            
            # Step 2: Create live stream (RTMP endpoint)
            print("🔗 Creating RTMP stream endpoint...")
            
            stream_body = {
                'snippet': {
                    'title': f"{title} - Stream"
                },
                'cdn': {
                    'frameRate': '30fps',
                    'ingestionType': 'rtmp',
                    'resolution': '720p'
                }
            }
            
            stream_response = self.youtube_service.liveStreams().insert(
                part='snippet,cdn',
                body=stream_body
            ).execute()
            
            stream_id = stream_response['id']
            stream_key = stream_response['cdn']['ingestionInfo']['streamName']
            rtmp_url = stream_response['cdn']['ingestionInfo']['ingestionAddress']
            
            print(f"✅ RTMP endpoint created: {stream_id}")
            print(f"🔑 Stream key: {stream_key[:8]}...")
            
            # Step 3: Bind broadcast to stream
            print("🔗 Binding broadcast to RTMP stream...")
            
            self.youtube_service.liveBroadcasts().bind(
                part='id,contentDetails',
                id=broadcast_id,
                streamId=stream_id
            ).execute()
            
            print("✅ Broadcast bound to stream")
            
            # Step 4: Set custom thumbnail if provided
            if thumbnail_path and os.path.exists(thumbnail_path):
                try:
                    print(f"🖼️ Uploading custom thumbnail: {thumbnail_path}")
                    self.youtube_service.thumbnails().set(
                        videoId=video_id,
                        media_body=thumbnail_path
                    ).execute()
                    print("✅ Custom thumbnail uploaded")
                except Exception as e:
                    print(f"⚠️ Thumbnail upload failed: {e}")
            
            # Return stream info
            stream_info = {
                'success': True,
                'video_id': video_id,
                'broadcast_id': broadcast_id,
                'stream_id': stream_id,
                'stream_key': stream_key,
                'rtmp_url': rtmp_url,
                'full_rtmp_url': f"{rtmp_url}/{stream_key}",
                'chat_id': None,  # Will be available once stream starts
                'title': title,
                'url': f"https://youtube.com/watch?v={video_id}",
                'status': 'ready'
            }
            
            print("🎯 Live stream created successfully!")
            print(f"📺 Video URL: https://youtube.com/watch?v={video_id}")
            print(f"🔴 RTMP URL: {rtmp_url}")
            print("✨ Stream will automatically go LIVE when RTMP feed is detected!")
            print("💡 This is the modern YouTube streaming workflow - no manual activation needed")
            
            return stream_info
            
        except Exception as e:
            print(f"❌ Failed to create live stream: {e}")
            return None
    
    def stop_broadcast(self, broadcast_id):
        """Stop the live broadcast"""
        try:
            print(f"⏹️ Stopping broadcast: {broadcast_id}")
            
            response = self.youtube_service.liveBroadcasts().transition(
                broadcastStatus='complete',
                id=broadcast_id,
                part='status'
            ).execute()
            
            print("✅ Broadcast stopped")
            return True
            
        except Exception as e:
            print(f"❌ Failed to stop broadcast: {e}")
            return False

# Usage example
if __name__ == "__main__":
    print("🚀 YouTube OAuth Live Streaming Test")
    
    oauth = YouTubeOAuth()
    
    if oauth.authenticate():
        print("\n🎬 Creating test live stream...")
        stream_info = oauth.create_live_stream(
            title="Test Gaming Stream",
            description="Automated test stream created via OAuth"
        )
        
        if stream_info:
            print("\n✅ Stream creation successful!")
            print(f"Stream Key: {stream_info['stream_key']}")
            print(f"RTMP URL: {stream_info['rtmp_url']}")
            print(f"Video URL: {stream_info['url']}")
        else:
            print("❌ Stream creation failed")
    else:
        print("❌ OAuth authentication failed")