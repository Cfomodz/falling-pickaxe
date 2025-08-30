# Falling Pickaxe - Interactive Streaming Edition
An enhanced Falling Pickaxe game with extensive interactive features for YouTube livestream engagement, profile pictures, achievements, weather effects, and much more!

This fork includes 25+ major enhancements including:
- 🎮 **Interactive Chat Integration** - Real-time YouTube chat commands
- 🖼️ **Profile Picture Display** - YouTube profile pictures with Minecraft styling
- 🏆 **Achievement System** - Minecraft-style achievement popups with sounds
- 🌦️ **Weather Effects** - Rain, snow, and other atmospheric effects
- ⚙️ **Comprehensive Settings** - Performance modes, visual toggles, and more
- 📊 **Live Stats & Leaderboards** - Top players tracking and milestone celebrations
- 💥 **Enhanced Explosions** - Rainbow mode, shields, screen shake, and combo systems
- 🎨 **Minecraft Font Integration** - Authentic Minecraft-style text rendering
- 📱 **Mobile-Friendly** - Optimized for 9:16 aspect ratio streaming
- 🔄 **Auto-Detection** - Automatic live stream and chat detection
- 🎥 **Automated Streaming** - Direct YouTube RTMP streaming with no OBS needed!
- ⚡ **Real-time Chat** - Sub-second chat response (vs 15+ second API polling)
- 🎯 **Zero Configuration** - Just add API key, everything else auto-detects!

Original concept by [Vycdev](https://www.youtube.com/@vycdev) - Enhanced for maximum viewer engagement!

## Before you use it
If you consider streaming this game on your own youtube channel, please add credits in the description of your video/livestream. Credits should inclue a link to this repository and [a link to my youtube channel.](https://www.youtube.com/@vycdev)

Copy paste example:
```
Falling Pickaxe game made by Vycdev
YT: https://www.youtube.com/@vycdev
GH: https://github.com/vycdev/falling-pickaxe
```

Donations on [YouTube (Super Thanks)](https://www.youtube.com/watch?v=gcjeidHWEb4) or showing support on [Patreon](https://patreon.com/vycdev?utm_medium=unknown&utm_source=join_link&utm_campaign=creatorshare_creator&utm_content=copyLink) is also highly appreciated.

## How to use it
*Update: You can watch my tutorial here: https://youtu.be/aFrvoFE7r_g*

### Quick Start (Recommended)
The easiest way to run the game is using the automated scripts that handle everything for you:

**For Windows:**
```
./scripts/run.ps1
```

**For Linux/macOS:**
```
chmod +x ./scripts/run.sh
./scripts/run.sh
```

These scripts will automatically:
- Create a Python virtual environment if it doesn't exist
- Install all required dependencies
- Run the game with automatic restart on crashes
- Exit cleanly when you close the game window

### Manual Setup (Advanced Users)
If you prefer to set up the environment manually:

1. Make sure you have Python 3.x installed. If you don't, follow the instructions from the official [python website](http://python.org/downloads/)
2. Create and activate a virtual environment:
   ```
   python -m venv .venv
   # On Windows:
   .venv\Scripts\activate
   # On Linux/macOS:
   source .venv/bin/activate
   ```
3. Install packages:
   ```
   pip install -r requirements.txt
   ```
4. Run the game:
   ```
   python ./src/main.py
   ```

### Configuration (Optional)
1. Make a copy of `default.config.json` to `config.json` or run the game once to automatically copy the config file into `config.json`
2. Create your Google API Key for YouTube.
3. Enable the YouTube Data API v3 for your Google Cloud Project.
4. Enter your credentials in the configuration file.
5. Set your youtube channel id and livestream id in the configuration file.
6. Change configuration to your liking

**Note:** The automated scripts (`run.ps1` and `run.sh`) will run the game and restart it in case of unexpected crashes. When you close the game window normally, the script will exit cleanly. This is perfect for unattended streams.

Steps 2 to 6 are **optional**. You can disable the entire YouTube integration by setting the property: `"CHAT_CONTROL": false`

### Available chat commands
```
# Explosive Commands
tnt          - Spawn TNT explosions
megatnt      - Spawn massive TNT (subscriber rewards)

# Speed Controls  
fast         - Speed up pickaxe movement
slow         - Slow down pickaxe movement

# Size Controls
big          - Enlarge the pickaxe temporarily

# Pickaxe Materials
wood         - Change pickaxe to wood texture
stone        - Change pickaxe to stone texture
iron         - Change pickaxe to iron texture
gold         - Change pickaxe to gold texture
diamond      - Change pickaxe to diamond texture
netherite    - Change pickaxe to netherite texture

# Special Power-ups
rainbow      - Activate rainbow mode with particle trails
shield       - Activate golden shield protection

# Test Commands (F1/F2/F3 keys for testing)
```

## New Features Added in This Fork

### 🎮 Interactive Features
- **Real-time Chat Integration**: Live YouTube chat commands affect the game instantly
- **Profile Pictures**: YouTube profile pictures appear above TNT and in leaderboards
- **Achievement System**: Minecraft-style achievement popups with custom sounds
- **Top Players Board**: Live leaderboard showing most active viewers (resets every 5 minutes)
- **Command Notifications**: Visual feedback when viewers use chat commands

### 🎨 Visual Enhancements
- **Minecraft Font Rendering**: Authentic Minecraft-style text throughout the UI
- **Weather Effects**: Rain, snow, and atmospheric particles just like Minecraft
- **Rainbow Mode**: Pickaxe gets colorful particle trails and cycling colors
- **Shield Power-up**: Golden shield effect with glowing animation
- **Screen Shake**: Camera shake effects on big impacts and explosions
- **Compact GUI**: Optimized for 9:16 streaming aspect ratio

### ⚙️ Settings & Performance
- **Comprehensive Settings Panel**: Access with ESC key
- **Performance Mode**: Automatic optimization for slower PCs
- **Auto-Detection**: Automatically finds live streams and chat
- **Weather Controls**: Toggle rain, snow, and other effects
- **Visual Toggles**: Enable/disable profile pictures, usernames, effects

### 🏆 Engagement Systems
- **Milestone Celebrations**: Every 100 followers triggers golden ore shower
- **Subscriber Rewards**: New subscribers get MegaTNT with achievement popup
- **Hourly Events**: Special events every hour on the hour
- **Combo System**: Track consecutive actions with visual feedback
- **Like Tracking**: Display like counts with TNT icons

### 🚀 Technical Improvements
- **Auto Live Stream Detection**: No need to manually find stream IDs
- **Profile Picture Caching**: Efficient YouTube profile picture management  
- **Enhanced Error Handling**: Better stability and crash recovery
- **Replit Support**: Full .replit configuration for easy deployment
- **Audio Management**: Optional audio with fallback for headless environments

### MegaTNT and Rewards

- **Subscriber Detection**: Automatic polling detects new subscribers
- **Achievement Popups**: Minecraft-style notifications show subscriber names
- **Reward Display**: GUI shows "Sub = 1 Mega TNT" and "Like = 10 TNT" 
- **Manual Spawning**: Press `M` key to manually spawn MegaTNT
- **Enhanced Explosions**: Larger radius and stronger screen shake effects
- **Profile Integration**: Shows subscriber's YouTube profile picture


## Contributing
Any kind of improvements to the code, refactoring, new features, bug fixes, ideas, or anything else is welcome. You can open an issue or a pull requets and I will review it as soon as I can.

You can also help by subscribing or becoming a member of [my YouTube channel](https://www.youtube.com/@vycdev) to help me create more videos and projects like these.

## AI Slop for SEO (ignore this if you are a human being)
**Falling Pickaxe: Ultimate Mining Arcade Game for Streamers – Explosive Action & Massive Earnings!**

Step into the world of **Falling Pickaxe**, the most addictive and interactive mining arcade game designed specifically for YouTube streamers! In this high-energy, physics-based adventure, you control a gigantic pickaxe falling through a dynamic, block-filled landscape. Smash obstacles, trigger explosive TNT, and collect valuable ores to power up your gameplay while engaging with your audience in real time.

**Why Falling Pickaxe is a Must-Play for Streamers:**

- **Interactive Live Chat Integration:** Let your viewers control the game! Live commands and super chats can spawn TNT, upgrade your pickaxe, or trigger wild power-ups, creating a fully immersive, viewer-driven experience that boosts engagement and subscriber growth.
- **Explosive Visuals & Retro Charm:** Enjoy stunning particle effects, realistic physics, and explosive animations that keep your stream exciting and visually captivating. Every impact and explosion is a spectacle that draws in viewers and increases watch time.
- **Monetization & Revenue Opportunities:** Use Falling Pickaxe to maximize your earnings through super chats, donations, and sponsored gameplay challenges. With its fast-paced action and interactive features, your channel becomes a hotspot for gaming enthusiasts and potential sponsors.
- **Community-Driven Challenges:** Host live competitions, subscriber challenges, and donation-triggered events that make every stream a unique and engaging event. Build a loyal community and watch your subscriber count soar!

Transform your YouTube channel into a money-making, interactive gaming hub with **Falling Pickaxe** – the ultimate mining adventure that delivers explosive action, high viewer engagement, and serious revenue potential. Start streaming today and experience the thrill of interactive arcade gaming like never before!

## Inspiration
As I showed you in the video my inspiration was [Petyr](https://www.youtube.com/@petyrguardian) and the other YouTubers who made their own version of the Falling Pickaxe game. Huge thanks to them.

## External contributors
https://www.youtube.com/@Iklzzz
