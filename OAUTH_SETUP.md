# YouTube OAuth Setup for Automatic Stream Creation

This guide will help you set up OAuth authentication so the game can automatically create YouTube live streams like SLOBS/OBS.

## Step 1: Google Cloud Console Setup

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select an existing one
3. Enable the following APIs:
   - **YouTube Data API v3**
   - **YouTube Live Streaming API**

### Enable APIs:
- Go to "APIs & Services" > "Library"
- Search for "YouTube Data API v3" and click "Enable"
- Search for "YouTube Live Streaming API" and click "Enable"

## Step 2: Create OAuth Credentials

1. Go to "APIs & Services" > "Credentials"
2. Click "Create Credentials" > "OAuth 2.0 Client IDs"
3. If prompted, configure the OAuth consent screen:
   - Choose "External" user type
   - Fill in required fields (App name, User support email, Developer contact)
   - Add scopes: `https://www.googleapis.com/auth/youtube` and `https://www.googleapis.com/auth/youtube.force-ssl`
   - Add your email as a test user
4. For Application type, choose **"Desktop application"**
5. Give it a name like "Falling Pickaxe YouTube Integration"
6. Click "Create"
7. Download the JSON file

## Step 3: Setup Credentials File

1. Rename the downloaded JSON file to `client_credentials.json`
2. Place it in your `/home/toor/falling-pickaxe/` directory (same folder as main.py)

The file structure should look like:
```
/home/toor/falling-pickaxe/
├── src/
│   ├── main.py
│   ├── youtube_oauth.py
│   └── ...
├── client_credentials.json  ← Your OAuth credentials
├── config.json
└── ...
```

## Step 4: Update Configuration

Your `config.json` should have:
```json
{
    "USE_OAUTH": true,
    "AUTO_CREATE_STREAM_OAUTH": true,
    "OAUTH_CREDENTIALS_FILE": "client_credentials.json",
    "STREAMING_ENABLED": true,
    ...
}
```

## Step 5: First Run & Authentication

1. Run the game: `python src/main.py`
2. The first time, it will:
   - Open your browser for YouTube authentication
   - Ask you to grant permissions to manage your YouTube channel
   - Save authentication tokens for future use
3. After authentication, it will automatically create a live stream

## What This Enables

✅ **Automatic stream creation** - No manual scheduling needed
✅ **Direct RTMP streaming** - Game streams directly to YouTube
✅ **Chat integration** - Automatic chat connection
✅ **Professional workflow** - Just like SLOBS/OBS Studio
✅ **No API quota issues** - OAuth has higher limits

## Troubleshooting

### "OAuth authentication failed"
- Check that `client_credentials.json` exists and is valid
- Ensure APIs are enabled in Google Cloud Console
- Verify OAuth consent screen is configured

### "Failed to create live stream"
- Make sure YouTube Live Streaming API is enabled
- Check that your YouTube channel is enabled for live streaming
- Verify you have the correct OAuth scopes

### "Stream creation successful but no video"
- Check FFmpeg is installed and working
- Verify RTMP connection in streaming logs
- Ensure firewall isn't blocking RTMP traffic

## Advanced Configuration

You can customize stream creation in `youtube_oauth.py`:
- Stream title and description
- Privacy settings (public, unlisted, private)
- Stream quality (720p, 1080p)
- DVR and recording options

## Security Notes

- Keep `client_credentials.json` secure - don't share or commit to git
- The generated `youtube_token.json` contains your access tokens
- Tokens are automatically refreshed when needed
- You can revoke access anytime in your Google Account settings