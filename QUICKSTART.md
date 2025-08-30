# 🚀 Replit Quickstart Guide

Get your Falling Pickaxe game running on Replit in minutes! This interactive streaming game is fully configured for Replit's cloud environment.

## ⚡ Quick Setup (2 minutes)

### 1. Fork or Import
- **Fork this repository** on GitHub, then import to Replit
- **OR** directly import: `https://github.com/YOUR_USERNAME/falling-pickaxe`

### 2. One-Click Run
Once imported to Replit:
1. Click the **"Run Game"** button (already configured!)
2. The game will automatically:
   - Install all dependencies from `requirements.txt`
   - Set up the Python 3.12 environment
   - Load SDL2 libraries for graphics and audio
   - Start the game with `python src/main.py`

That's it! The game should start immediately in offline mode.

## 🎮 Basic Usage

### Controls
- **Mouse**: Control the falling pickaxe
- **ESC**: Open settings panel
- **M**: Manually spawn MegaTNT
- **F1/F2/F3**: Test achievement system

### First Run
- The game creates a `config.json` file automatically
- Runs in offline mode by default (no YouTube required)
- All visual features work without YouTube API

## 📺 Enable YouTube Integration & Streaming

### YouTube API Setup (Required for Chat & Auto-Streaming)

1. **Get YouTube API Credentials**
```bash
1. Go to Google Cloud Console
2. Create a new project or select existing
3. Enable "YouTube Data API v3"
4. Create credentials (API Key)
5. Copy your API key
```

2. **Get Your Stream Key**
```bash
1. Go to YouTube Studio
2. Create > Go Live
3. Copy your Stream Key (keep this secret!)
```

3. **Configure the Game (Zero-Config!)**
Edit `config.json` in Replit - **only 2 fields needed:**
```json
{
    "CHAT_CONTROL": true,
    "API_KEY": "YOUR_API_KEY_HERE"
}
```

**That's it!** Everything else auto-detects:
- ✅ **Channel ID** - Auto-detected from API key
- ✅ **Live Stream ID** - Auto-finds your active stream  
- ✅ **Chat ID** - Auto-extracted from stream
- ✅ **Subscriber Count** - Auto-retrieved from channel

**Optional streaming:**
```json
{
    "STREAMING_ENABLED": true,
    "YOUTUBE_STREAM_KEY": "YOUR_STREAM_KEY_HERE"
}
```

### **🔍 Zero-Config Setup Process:**
1. **Start a YouTube live stream** (any title/settings)
2. **Add your API key** to config.json  
3. **Run the game** - watch the console output:
```
🔍 Starting zero-configuration YouTube setup...
✅ Auto-detected channel: Your Channel Name
📊 Subscribers: 1,234
🔴 Found 1 active live stream(s)
   📺 Your Stream Title (ID: dQw4w9WgXcQ)
🎯 Auto-detection complete!
📺 Stream: Your Stream Title
💬 Chat ID: Ey4D...
🚀 Zero-config setup complete - everything auto-detected!
```

**If auto-detection fails:** The game falls back to manual configuration and shows helpful error messages.

## 🎥 Automated Streaming (NEW!)

**The game now streams directly to YouTube - no OBS needed!**

### How It Works
- ✅ **Game captures its own screen** using FFmpeg
- ✅ **Streams directly to YouTube RTMP** 
- ✅ **720p @ 30fps** optimized for mobile (9:16)
- ✅ **Automatic quality adjustment** based on connection
- ✅ **Zero setup** - just add your stream key!

### Starting Your Stream
1. **In-game**: Press **ESC** → Navigate to **"streaming_enabled"** → Press **Enter**
2. **Auto-start**: Set `"auto_start_stream": true` in config
3. **Status**: Stream status shows in console output

Your viewers can immediately use chat commands while the stream runs!

## ⚡ Real-time Chat System (NEW!)

**No more 15-second delays!** The game now uses a hybrid approach:

### **Real-time Components (Sub-second latency):**
- ✅ **Chat Commands** - TNT, pickaxe changes, etc. (<1 second)
- ✅ **Super Chats** - Instant visual and audio feedback  
- ✅ **Member Messages** - Real-time recognition
- ✅ **Command Notifications** - Instant visual pop-ups

### **Smart Polling (Optimized intervals):**
- 📊 **Live Viewers** - Every 10 seconds (vs 15 seconds before)
- 👍 **Like Count** - Every 30 seconds (vs 15 seconds before)  
- 📈 **Subscribers** - Every 2 minutes (vs 15 seconds before)

### **Performance Comparison:**
```
OLD SYSTEM (API Polling):
💬 Chat Commands: 15+ second delay ❌
💰 Super Chats: 15+ second delay ❌
📊 All Metrics: 15 second delay ❌

NEW SYSTEM (Hybrid):
💬 Chat Commands: <1 second delay ✅
💰 Super Chats: <1 second delay ✅  
👍 Likes: 30 second delay ⚡
📈 Subs: 2 minute delay ⚡
👀 Viewers: 10 second delay ⚡
```

**Result:** Your viewers get **instant feedback** when they interact!

## 🔧 Replit Configuration Explained

### `.replit` File
```toml
modules = ["python-3.12", "bash"]     # Python version and shell access
audio = true                          # Enable audio support

[nix]
packages = [                          # System dependencies
  "SDL2", "SDL2_image", "SDL2_mixer", # Graphics and audio
  "SDL2_ttf", "fontconfig",           # Font rendering
  "pkg-config", "portmidi"            # Development tools
]

[workflows]
runButton = "Run Game"                # Custom run button text

[[workflows.workflow]]
name = "Run Game"
args = "python src/main.py"          # Command to execute
```

### Key Benefits on Replit
- ✅ **Pre-configured Environment**: All dependencies ready
- ✅ **Audio Support**: Sound effects work out of the box  
- ✅ **Graphics Support**: SDL2 for smooth rendering
- ✅ **Auto-restart**: Game restarts if it crashes
- ✅ **Cloud Storage**: Configs and assets persist
- ✅ **Easy Sharing**: Share your Repl with others

## 🎨 Customization Tips

### Performance Settings
For slower connections, enable performance mode:
1. Press **ESC** in-game
2. Navigate to **Performance** settings  
3. Enable **Performance Mode**
4. Adjust **Weather Effects** and **Visual Quality**

### Streaming Setup
1. **Aspect Ratio**: Game is optimized for 9:16 (mobile)
2. **Right Panel**: Commands and leaderboard display
3. **Compact Mode**: GUI optimized for streaming
4. **Visual Effects**: All toggleable in settings

### Chat Commands Setup
Once YouTube is connected, viewers can use:
```
tnt, megatnt, fast, slow, big
wood, stone, iron, gold, diamond, netherite
rainbow, shield
```

## 🐛 Troubleshooting

### Common Issues

#### "Audio device not found"
- **Cause**: Replit audio not enabled
- **Fix**: Check `audio = true` in `.replit` file

#### "Font not initialized"  
- **Cause**: pygame not properly initialized
- **Fix**: Restart the Repl (Ctrl+Shift+R)

#### "PyMunk installation failed"
- **Cause**: Missing system dependencies
- **Fix**: Dependencies should auto-install, try refreshing

#### YouTube API not working
- **Cause**: Invalid API key or permissions
- **Fix**: Verify API key and enable YouTube Data API v3

### Performance Issues
If the game runs slowly:
1. Enable **Performance Mode** in settings
2. Disable **Weather Effects**  
3. Turn off **Profile Pictures**
4. Reduce **Particle Effects**

## 📱 Streaming Tips

### Optimal Setup for Streaming
1. **Orientation**: Portrait mode (9:16 ratio)
2. **Layout**: Game fills main area, chat on right
3. **Engagement**: Enable all achievement popups
4. **Audio**: Keep achievement sounds enabled
5. **Auto-features**: Enable auto-detection for ease of use

### Viewer Engagement Features
- **Profile Pictures**: Viewers see their YouTube avatars
- **Achievement Popups**: New subscriber notifications  
- **Leaderboard**: Top players displayed live
- **Milestone Celebrations**: Automatic follower rewards
- **Visual Feedback**: All commands show immediate effects

## 🔄 Updates & Maintenance

### Keeping Up to Date
```bash
# In Replit shell
git pull origin main
```

### Configuration Backup
- Replit automatically saves `config.json`
- Profile picture cache persists between runs
- Settings are maintained across updates

### Adding New Features  
The modular architecture makes it easy to:
- Add new chat commands in `main.py`
- Create new visual effects in `pickaxe.py`
- Extend the settings panel in `settings.py`
- Add new achievements in `notifications.py`

## 🤝 Community & Support

### Getting Help
- **GitHub Issues**: Report bugs or request features
- **Discord**: Join the community (if available)
- **Documentation**: Check `PROJECT_OVERVIEW.md` for technical details

### Contributing
- Fork the repository
- Make your changes in Replit
- Submit pull requests for improvements
- Share your streaming setup with others

---

**Ready to Stream?** Your Falling Pickaxe game is now configured and ready for interactive streaming on Replit! Click **"Run Game"** and start engaging with your viewers! 🎮✨