import time
import pygame
from youtube import get_live_stream, get_new_live_chat_messages, get_live_chat_id, get_subscriber_count, validate_live_stream_id, get_live_streams
from config import config
from atlas import create_texture_atlas
from pathlib import Path
from world import World
from constants import BLOCK_SCALE_FACTOR, BLOCK_SIZE, INTERNAL_HEIGHT, INTERNAL_WIDTH, FRAMERATE
from character import Character
from camera import Camera
from sound import SoundManager

def get_block_color(block_type):
    """Get color for different block types for visualization"""
    colors = {
        "dirt_light": (139, 115, 85),    # Light brown
        "dirt_medium": (101, 79, 57),    # Medium brown  
        "dirt_dark": (62, 48, 36),       # Dark brown
        "clay": (178, 154, 108),         # Clay color
        "bedrock": (64, 64, 64),         # Dark gray
        
        # Rocks (darker shades)
        "talc_rock": (200, 200, 200),    # White-ish
        "gypsum_rock": (255, 248, 220),  # Cream
        "calcite_rock": (255, 255, 240), # Off white
        "fluorite_rock": (186, 85, 211), # Purple
        "apatite_rock": (0, 255, 127),   # Spring green
        "orthoclase_rock": (255, 192, 203), # Pink
        "quartz_rock": (255, 255, 255),  # White
        "topaz_rock": (255, 215, 0),     # Gold
        "corundum_rock": (220, 20, 60),  # Crimson
        "diamond_rock": (185, 242, 255), # Light blue
    }
    return colors.get(block_type, (100, 100, 100))  # Default gray

def get_gem_color(gem_type):
    """Get color for different gem types"""
    colors = {
        "talc_gem": (220, 220, 220),     # Light gray
        "gypsum_gem": (255, 250, 240),   # Cream
        "calcite_gem": (255, 255, 255),  # White
        "fluorite_gem": (138, 43, 226),  # Purple
        "apatite_gem": (50, 205, 50),    # Green
        "orthoclase_gem": (255, 105, 180), # Pink
        "quartz_gem": (240, 248, 255),   # Alice blue
        "topaz_gem": (255, 215, 0),      # Gold
        "corundum_gem": (220, 20, 60),   # Red
        "diamond_gem": (185, 242, 255),  # Diamond blue
    }
    return colors.get(gem_type, (255, 255, 255))  # Default white
import asyncio
import threading
import random
from hud import Hud
from settings import SettingsManager
from notifications import notification_manager
import datetime
from notifications import NotificationManager
from stream_manager import StreamManager, check_ffmpeg, install_ffmpeg_replit
from realtime_chat import HybridYouTubeManager
from youtube_auto_detect import create_zero_config_setup
from youtube_public_detect import create_public_auto_setup
from youtube_oauth import YouTubeOAuth

# Track key states
key_t_pressed = False
key_m_pressed = False

#
live_stream = None
live_chat_id = None
subscribers = None
followers = None
last_follower_milestone = 0
last_hour_checked = datetime.datetime.now().hour

# Auto-stream creator for initializing YouTube streams
auto_stream_creator = None

# Auto-detect YouTube setup (Public API - No OAuth Required)  
auto_setup = None
if config["CHAT_CONTROL"] == True and config.get("API_KEY") and config["API_KEY"] != "YOUR_API_KEY_HERE":
    print("🔍 Starting YouTube auto-detection (Public API)...")
    
    # Try multiple detection methods
    channel_handle = config.get("CHANNEL_HANDLE", "").strip()
    search_term = config.get("STREAM_SEARCH_TERM", "falling pickaxe").strip()
    
    # Method 1: OAuth Live Stream Creation (like SLOBS)
    if config.get("USE_OAUTH", False) and config.get("AUTO_CREATE_STREAM_OAUTH", False):
        print("🚀 Using OAuth to create live stream automatically...")
        try:
            oauth = YouTubeOAuth(
                credentials_file=config.get("OAUTH_CREDENTIALS_FILE", "client_credentials.json")
            )
            
            if oauth.authenticate():
                print("✅ OAuth authentication successful!")
                
                # Create live stream automatically with custom thumbnail
                stream_info = oauth.create_live_stream(
                    title="Falling Pickaxe - Live Gaming",
                    description="Automated live gaming stream created by Falling Pickaxe",
                    thumbnail_path="thumbnail.png"
                )
                
                if stream_info:
                    print("🎯 OAuth stream creation successful!")
                    
                    # Use the OAuth-created stream
                    auto_setup = {
                        'success': True,
                        'active_stream': {
                            'video_id': stream_info['video_id'],
                            'title': stream_info['title']
                        },
                        'live_chat_id': stream_info.get('chat_id'),
                        'stream_info': stream_info,
                        'oauth_created': True
                    }
                    
                    print(f"📺 Your stream: {stream_info['url']}")
                    print("🔴 Stream created and ready for streaming!")
                else:
                    print("❌ OAuth stream creation failed")
            else:
                print("❌ OAuth authentication failed")
                
        except Exception as e:
            print(f"⚠️ OAuth stream creation failed: {e}")
    
    # Method 1b: Private API (OAuth fallback) - Try if available
    if not auto_setup or not auto_setup.get('success'):
        try:
            if config.get("USE_PRIVATE_API", False):
                print("🔑 Attempting private API detection...")
                auto_setup = create_zero_config_setup(config["API_KEY"])
                if auto_setup.get('success'):
                    print("✅ Private API detection successful!")
        except Exception as e:
            print(f"⚠️  Private API failed: {e}")
    
    # Method 2: Auto-create stream if we have a stream key but no active stream
    if not auto_setup or not auto_setup.get('success'):
        stream_key = config.get("YOUTUBE_STREAM_KEY")
        if (stream_key and stream_key != "YOUR_STREAM_KEY_HERE" and 
            config.get("AUTO_CREATE_STREAM", True)):
            
            print("🎮 Starting game streaming directly...")
            print("💡 Stream will be created automatically when you start streaming")
            
            try:
                # Initialize streaming system for the game directly - COMMENTED OUT
                print("🎮 Game streaming DISABLED for testing")
                # if check_ffmpeg():
                #     stream_manager = StreamManager(config)
                #     stream_manager.set_stream_key(stream_key)
                #     if stream_manager.start_streaming():
                #         print("✅ Game streaming started successfully!")
                #         print("🎬 IMPORTANT: Make sure your scheduled YouTube stream is active!")
                #         print("💡 Your scheduled stream should now be receiving the game feed")
                #         # Don't create fake auto_setup - let chat system discover stream later
                #         print("💬 Chat will connect automatically once stream is discovered")
                #     else:
                #         print("⚠️ Failed to start game streaming")
                # else:
                #     print("❌ FFmpeg not available for streaming")
                
            except Exception as e:
                print(f"⚠️  Game streaming failed: {e}")
    
    # Method 3: Public API by channel handle (original)
    if not auto_setup or not auto_setup.get('success'):
        if channel_handle and channel_handle != "@yourhandle":
            print(f"🎯 Trying channel handle: {channel_handle}")
            auto_setup = create_public_auto_setup(config["API_KEY"], channel_handle=channel_handle)
    
    # Method 4: Public API by search term
    if not auto_setup or not auto_setup.get('success'):
        if search_term:
            print(f"🔍 Searching for streams: '{search_term}'")
            auto_setup = create_public_auto_setup(config["API_KEY"], search_term=search_term)
    
    # Method 5: Manual fallback
    if not auto_setup or not auto_setup.get('success'):
        if config.get("CHANNEL_ID") and config["CHANNEL_ID"] != "YOUR_CHANNEL_ID_HERE":
            print("🔄 Falling back to manual channel ID...")
            from youtube import get_live_streams, get_live_stream, get_live_chat_id, get_subscriber_count
            
            try:
                live_streams = get_live_streams(config["CHANNEL_ID"])
                if live_streams:
                    auto_stream_id = live_streams[0]["video_id"]
                    live_stream = get_live_stream(auto_stream_id)
                    if live_stream:
                        auto_setup = {
                            'success': True,
                            'active_stream': {'video_id': auto_stream_id, 'title': live_streams[0]['title']},
                            'live_chat_id': get_live_chat_id(live_stream["id"]),
                            'channel': {'snippet': {'title': 'Manual Channel'}},
                            'channel_id': config["CHANNEL_ID"]
                        }
                        print(f"📺 Manual fallback successful: {live_streams[0]['title']}")
            except Exception as e:
                print(f"❌ Manual fallback failed: {e}")
    
    # Process successful auto-setup
    if auto_setup and auto_setup.get('success'):
        # Set up live stream info
        live_stream = {
            'id': auto_setup['active_stream']['video_id'],
            'snippet': {'title': auto_setup['active_stream']['title']}
        }
        live_chat_id = auto_setup['live_chat_id']
        
        # Get subscriber count if available
        if auto_setup.get('channel') and 'statistics' in auto_setup['channel']:
            subscriber_count = auto_setup['channel']['statistics'].get('subscriberCount')
            if subscriber_count:
                subscribers = int(subscriber_count)
                print(f"📊 Subscribers: {subscribers:,}")
            
            # Set followers approximation from view count
            view_count = auto_setup['channel']['statistics'].get('viewCount')
            if view_count:
                followers = int(view_count) // 1000
                last_follower_milestone = (followers // 100) * 100
                print(f"👥 Follower approximation: {followers:,}")
        
        print("✅ YouTube integration ready!")
        print(f"📺 Stream: {auto_setup['active_stream']['title']}")
        print(f"🎮 Channel: {auto_setup.get('channel', {}).get('snippet', {}).get('title', 'Unknown')}")
        if live_chat_id:
            print(f"💬 Chat: Connected")
        
        # Keep the auto-stream running - we'll transition it to game content
        if auto_stream_creator:
            print("🔄 Keeping Starting Soon stream alive...")
            print("🎮 Game will transition this stream to show game content!")
            # Don't stop the auto-stream, let the game use the same connection
        
    else:
        # Try manual VIDEO_ID as final fallback
        video_id = config.get("VIDEO_ID")
        if video_id:
            print(f"🎯 Using manual video ID: {video_id}")
            try:
                from youtube import get_live_chat_id
                live_chat_id = get_live_chat_id(video_id)
                if live_chat_id:
                    auto_setup = {
                        'success': True,
                        'active_stream': {'video_id': video_id, 'title': 'Manual Stream'},
                        'live_chat_id': live_chat_id,
                        'channel': {'snippet': {'title': 'Manual Channel'}},
                        'channel_id': config.get("CHANNEL_ID")
                    }
                    print(f"✅ Manual video setup successful!")
                else:
                    print(f"❌ Could not get chat ID for video: {video_id}")
            except Exception as e:
                print(f"❌ Manual video setup failed: {e}")
        
        if not auto_setup or not auto_setup.get('success'):
            print("❌ All auto-detection methods failed")
            print("💡 Setup options:")
            print("   1. Set CHANNEL_HANDLE: '@your-youtube-handle'")
            print("   2. Set STREAM_SEARCH_TERM: 'your stream keywords'")  
            print("   3. Set CHANNEL_ID: 'UC...' (manual)")
            print("   4. Set VIDEO_ID: 'video-id' (direct)")
            print("   5. Make sure you have an active live stream")

elif config["CHAT_CONTROL"] == True:
    print("⚠️  CHAT_CONTROL enabled but no API_KEY provided")
    print("💡 Add your YouTube Data API v3 key to config.json for auto-detection")

# Queues for chat - Digging game commands
speed_queue = []  # fast, slow, normal speed changes
left_queue = []   # move left commands
right_queue = []  # move right commands
tool_upgrade_queue = []  # tool upgrade requests
powerup_queue = []  # power-up activations
power_up_queue = []  # efficiency boost commands
rainbow_queue = []  # rainbow effect commands
shield_queue = []  # shield effect commands
freeze_queue = []  # freeze effect commands
fast_slow_queue = []  # speed change commands
big_queue = []  # big effect commands
mega_tnt_queue = []  # celebration commands
golden_ore_shower_queue = []  # milestone celebrations
gem_shower_queue = []  # special gem events
subscriber_celebration_queue = []  # subscriber milestones
hourly_event_queue = []

# Real-time chat system
hybrid_youtube_manager = None

def handle_realtime_chat_message(message):
    """Handle real-time chat messages with <1 second latency - Digging Game Commands"""
    global speed_queue, left_queue, right_queue, tool_upgrade_queue, powerup_queue, gem_shower_queue
    
    username = message['username']
    command = message['message'].lower().strip()
    
    print(f"⚡ Real-time: {username} -> {command}")
    
    # Digging game commands
    if command in ["fast", "slow", "normal"]:
        speed_queue.append((username, command))
        notification_manager.add_command_notification(username, command.upper(), 0, 0)
    
    elif command in ["left", "right"]:
        if command == "left":
            left_queue.append(username)
        else:
            right_queue.append(username)
        notification_manager.add_command_notification(username, command.upper(), 0, 0)
    
    elif command in ["left2", "left3", "right2", "right3"]:
        # Multi-space movement
        direction = "left" if "left" in command else "right"
        spaces = int(command[-1])
        if direction == "left":
            left_queue.append((username, spaces))
        else:
            right_queue.append((username, spaces))
        notification_manager.add_command_notification(username, f"{direction.upper()}{spaces}", 0, 0)
    
    elif command.startswith("upgrade "):
        # Tool upgrade command: "upgrade diamond_gem" 
        gem_type = command.replace("upgrade ", "").strip()
        tool_upgrade_queue.append((username, gem_type))
        notification_manager.add_command_notification(username, f"UPGRADE {gem_type.upper()}", 0, 0)
    
    elif command == "big":
        # Power-up system: big effect placeholder
        power_up_queue.append((username, "big_effect"))
        notification_manager.add_command_notification(username, "BIG", 0, 0)
    
    elif command in ["wood", "stone", "iron", "gold", "diamond", "netherite"]:
        # Power-up system placeholder - convert pickaxe commands to tool efficiency boosts
        power_up_queue.append((username, f"efficiency_{command}"))
        notification_manager.add_command_notification(username, f"EFFICIENCY {command.upper()}", 0, 0)
    
    elif command == "rainbow":
        rainbow_queue.append(username)
        notification_manager.add_command_notification(username, "RAINBOW", 0, 0)
    
    elif command == "shield":
        shield_queue.append(username)
        notification_manager.add_command_notification(username, "SHIELD", 0, 0)

def handle_realtime_metrics_update(metrics):
    """Handle subscriber/like count updates"""
    global subscribers, followers, last_follower_milestone
    
    # Update metrics when they change
    if 'subscriber_count' in metrics:
        new_subs = metrics['subscriber_count']
        if new_subs > subscribers:
            print(f"📈 New subscribers: {subscribers} → {new_subs}")
            # Add achievement notification for new subscribers
            diff = new_subs - subscribers
            for _ in range(diff):
                subscriber_celebration_queue.append("New Subscriber")
                notification_manager.add_achievement("New Subscriber!", f"Player#{random.randint(1000,9999)}")
        subscribers = new_subs
    
    if 'like_count' in metrics:
        print(f"👍 Likes updated: {metrics['like_count']}")
        # Could trigger special effects for like milestones
    
    if 'view_count' in metrics:
        print(f"👀 Viewers: {metrics['view_count']}")

# Initialize hybrid YouTube manager if chat control is enabled
if config["CHAT_CONTROL"]:
    print("🚀 Initializing Real-time YouTube Integration...")
    # Pass OAuth YouTube service if available for real metrics
    youtube_service = None
    if auto_setup and auto_setup.get('oauth_created') and 'oauth' in locals():
        youtube_service = oauth.youtube_service
    
    hybrid_youtube_manager = HybridYouTubeManager(
        config, 
        handle_realtime_chat_message,
        handle_realtime_metrics_update,
        youtube_service
    )

async def handle_youtube_poll():
    global subscribers, followers, last_follower_milestone # Use global to modify the variable

    if subscribers is not None:
        new_subscribers = get_subscriber_count(config["CHANNEL_ID"])
        if new_subscribers is not None and new_subscribers > subscribers:
            subscriber_celebration_queue.append("New Subscriber")
            subscriber_celebration_queue.append("New Subscriber Rainbow")
            subscribers = new_subscribers # Update subscriber count

    # Check follower milestones
    if followers is not None and config["CHANNEL_ID"] is not None:
        from youtube import get_channel_stats
        stats = get_channel_stats(config["CHANNEL_ID"])
        if stats and 'viewCount' in stats:
            current_followers = int(stats['viewCount']) // 1000
            current_milestone = (current_followers // 100) * 100
            if current_milestone > last_follower_milestone:
                gem_shower_queue.append(f"{current_milestone} Followers")
                last_follower_milestone = current_milestone
                followers = current_followers

    # Check for hourly events
    current_hour = datetime.datetime.now().hour
    if current_hour != last_hour_checked:
        hourly_event_queue.append(f"Hourly Event {current_hour}:00")
        last_hour_checked = current_hour

    new_messages = get_new_live_chat_messages(live_chat_id)

    for message in new_messages:
        author = message["author"]
        text = message["message"]
        is_superchat = message["sc_details"] is not None
        is_supersticker = message["ss_details"] is not None

        text_lower = text.lower()

        # Check for "tnt" command (add author to regular tnt_queue) - Only English "tnt"
        if "tnt" in text_lower:
            if author not in tnt_queue:
                tnt_queue.append(author)
                print(f"Added {author} to regular TNT queue")

        # Check for Superchat/Supersticker (add to superchat tnt queue)
        if is_superchat or is_supersticker:
            if author not in [entry[0] for entry in tnt_superchat_queue]:
                 tnt_superchat_queue.append((author, text))
                 print(f"Added {author} to Superchat TNT queue")

        if "fast" in text.lower() and author not in [entry[0] for entry in speed_queue]:
            speed_queue.append((author, "fast"))
            print(f"Added {author} to Speed queue (fast)")
        elif "slow" in text.lower() and author not in [entry[0] for entry in speed_queue]:
            speed_queue.append((author, "slow"))
            print(f"Added {author} to Speed queue (slow)")

        if "big" in text.lower() and author not in power_up_queue:
            power_up_queue.append((author, "big_effect"))
            print(f"Added {author} to Power-up queue (big_effect)")


        # Check for rainbow command
        if "rainbow" in text_lower and author not in rainbow_queue:
            rainbow_queue.append(author)
            print(f"Added {author} to Rainbow queue")

        # Check for shield command  
        if "shield" in text_lower and author not in shield_queue:
            shield_queue.append(author)
            print(f"Added {author} to Shield queue")

        # Check for freeze command
        if "freeze" in text_lower and author not in freeze_queue:
            freeze_queue.append(author)
            print(f"Added {author} to Freeze queue")

    # print the queue counts (optional, for debugging)
    # print(f"Queues: Speed={len(speed_queue)}, Power-up={len(power_up_queue)}, Tool Upgrade={len(tool_upgrade_queue)}, Gem Shower={len(gem_shower_queue)}")

def start_event_loop(loop):
    asyncio.set_event_loop(loop)
    loop.run_forever()

# Create a new event loop
asyncio_loop = asyncio.new_event_loop()
# Start it in a daemon thread so it doesn’t block shutdown
threading.Thread(target=start_event_loop, args=(asyncio_loop,), daemon=True).start()

def game():
    window_width = int(INTERNAL_WIDTH / 2)
    window_height = int(INTERNAL_HEIGHT / 2)

    # Initialize pygame
    pygame.init()
    clock = pygame.time.Clock()

    # Create a resizable window
    screen_size = (window_width, window_height)
    screen = pygame.display.set_mode(screen_size, pygame.RESIZABLE)
    pygame.display.set_caption("Digging Adventure")
    # set icon
    # Create simple icon for digging game
    icon = pygame.Surface((32, 32))
    icon.fill((139, 115, 85))  # Brown dirt color
    pygame.display.set_icon(icon)

    # Create an internal surface with fixed resolution
    internal_surface = pygame.Surface((INTERNAL_WIDTH, INTERNAL_HEIGHT))

    # Load texture atlas
    assets_dir = Path(__file__).parent.parent / "src/assets"
    (texture_atlas, atlas_items) = create_texture_atlas(assets_dir)

    # Load background
    background_image = pygame.image.load(assets_dir / "background.png")
    background_scale_factor = 1.5
    background_width = int(background_image.get_width() * background_scale_factor)
    background_height = int(background_image.get_height() * background_scale_factor)
    background_image = pygame.transform.scale(background_image, (background_width, background_height))

    # Scale the entire texture atlas
    texture_atlas = pygame.transform.scale(texture_atlas,
                                        (texture_atlas.get_width() * BLOCK_SCALE_FACTOR,
                                        texture_atlas.get_height() * BLOCK_SCALE_FACTOR))

    for category in atlas_items:
        for item in atlas_items[category]:
            x, y, w, h = atlas_items[category][item]
            atlas_items[category][item] = (x * BLOCK_SCALE_FACTOR, y * BLOCK_SCALE_FACTOR, w * BLOCK_SCALE_FACTOR, h * BLOCK_SCALE_FACTOR)

    #sounds
    sound_manager = SoundManager()

    # sound_manager.load_sound("tnt", assets_dir / "sounds" / "tnt.mp3", 0.3)  # Removed - not needed for digging game
    sound_manager.load_sound("stone1", assets_dir / "sounds" / "stone1.wav", 0.5)
    sound_manager.load_sound("stone2", assets_dir / "sounds" / "stone2.wav", 0.5)
    sound_manager.load_sound("stone3", assets_dir / "sounds" / "stone3.wav", 0.5)
    sound_manager.load_sound("stone4", assets_dir / "sounds" / "stone4.wav", 0.5)
    sound_manager.load_sound("grass1", assets_dir / "sounds" / "grass1.wav", 0.1)
    sound_manager.load_sound("grass2", assets_dir / "sounds" / "grass2.wav", 0.1)
    sound_manager.load_sound("grass3", assets_dir / "sounds" / "grass3.wav", 0.1)
    sound_manager.load_sound("grass4", assets_dir / "sounds" / "grass4.wav", 0.1)
    
    # Try to load achievement sound from attached assets
    try:
        achievement_sound_path = Path(__file__).parent.parent / "attached_assets" / "minecraft-achievements-sound-effects-made-with-Voicemod_1756150336259.mp3"
        if achievement_sound_path.exists():
            sound_manager.load_sound("achievement", achievement_sound_path, 0.5)
        else:
            # No achievement sound needed for digging game
            pass
    except:
        # No achievement sound fallback needed
        pass

    # Camera
    camera = Camera()

    # World - Generate the digging world
    world = World(width=50)  # 50 blocks wide

    # Character - Replace physics pickaxe with controlled character
    # Create simple character sprite (colored square)
    character_texture = pygame.Surface((BLOCK_SIZE, BLOCK_SIZE))
    character_texture.fill((255, 255, 0))  # Yellow character
    character = Character(INTERNAL_WIDTH // 2, 0, character_texture, sound_manager)
    character.camera_ref = camera  # Connect camera for screen shake effects

    # Game state
    current_dig_speed = "fast"  # Default speed

    # HUD
    hud = Hud(texture_atlas, atlas_items)

    # Explosions
    explosions = []

    # Settings
    settings_manager = SettingsManager()
    
    # Streaming - check if already initialized from OAuth or other auto-setup
    if 'stream_manager' not in locals():
        stream_manager = None
        
        # Check if we have OAuth stream info
        if auto_setup and auto_setup.get('oauth_created'):
            print("🚀 Initializing OAuth stream...")
            if check_ffmpeg():
                stream_manager = StreamManager(config)
                stream_info = auto_setup['stream_info']
                
                # Set OAuth stream parameters - COMMENTED OUT
                # stream_manager.set_stream_key(stream_info['stream_key'])
                # if hasattr(stream_manager, 'set_rtmp_url'):
                #     stream_manager.set_rtmp_url(stream_info['rtmp_url'])
                # 
                # if stream_manager.start_streaming():
                #     print("🎮 OAuth stream started successfully!")
                #     print(f"📺 Live at: {stream_info['url']}")
                #     print("🔴 Your stream is now LIVE!")
                # else:
                #     print("⚠️ Failed to start OAuth streaming")
                print("🎮 OAuth stream initialization DISABLED for testing")
            else:
                print("❌ FFmpeg not available for OAuth streaming")
                
        elif config.get("STREAMING_ENABLED", False):
            print("Initializing streaming system...")
            if check_ffmpeg():
                stream_manager = StreamManager(config)
                if config.get("YOUTUBE_STREAM_KEY") and config["YOUTUBE_STREAM_KEY"] != "YOUR_STREAM_KEY_HERE":
                    stream_manager.set_stream_key(config["YOUTUBE_STREAM_KEY"])
                    print("🎥 Streaming ready - use settings to start/stop")
                else:
                    print("⚠️  Set YOUTUBE_STREAM_KEY in config.json to enable streaming")
            else:
                print("⚠️  FFmpeg not found - installing...")
                if install_ffmpeg_replit():
                    stream_manager = StreamManager(config)
                else:
                    print("❌ Could not initialize streaming")
        else:
            # Always create stream manager for settings control
            if check_ffmpeg():
                stream_manager = StreamManager(config)
    else:
        print("📺 Streaming already active from auto-setup")
    
    # Connect stream manager to settings
    if stream_manager:
        settings_manager.set_stream_manager(stream_manager)
    
    # Notifications (already imported at top)

    # Youtube
    yt_poll_interval = 1000 * config["YT_POLL_INTERVAL_SECONDS"]
    last_yt_poll = pygame.time.get_ticks()

    # Save progress interval
    save_progress_interval = 1000 * config["SAVE_PROGRESS_INTERVAL_SECONDS"]
    last_save_progress = pygame.time.get_ticks()

    # Youtupe chat queues
    queues_pop_interval = 1000 * config["QUEUES_POP_INTERVAL_SECONDS"]
    last_queues_pop = pygame.time.get_ticks()

    # Start real-time YouTube monitoring if available
    if hybrid_youtube_manager and live_stream:
        try:
            video_id = live_stream["id"]
            # Use auto-detected channel ID if available, otherwise fall back to config
            channel_id = auto_setup['channel_id'] if auto_setup and auto_setup.get('channel_id') else config.get("CHANNEL_ID", "")
            
            hybrid_youtube_manager.start_monitoring(video_id, channel_id)
            print("🎯 Real-time chat system active!")
            print("⚡ Chat latency: <1 second (vs 15+ seconds with polling)")
            print("📊 Metrics: Optimized polling intervals")
            
            if auto_setup and auto_setup['success']:
                print("🚀 Zero-config mode: Everything auto-detected!")
            
        except Exception as e:
            print(f"⚠️ Real-time system failed, using fallback: {e}")

    # Main loop
    running = True
    user_quit = False
    while running:
        # ++++++++++++++++++  EVENTS ++++++++++++++++++
        for event in pygame.event.get():
            if event.type == pygame.QUIT:  # Close window event
                running = False
                user_quit = True
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_F1:  # Press F1 to test subscriber achievement
                    notification_manager.add_subscriber_achievement("TestUser123")
                elif event.key == pygame.K_F2:  # Press F2 to test like achievement  
                    notification_manager.add_like_achievement("LikeUser456")
                elif event.key == pygame.K_F3:  # Press F3 to test anonymous subscriber
                    notification_manager.add_subscriber_achievement()
            elif settings_manager.handle_input(event):
                continue  # Settings handled the input
            elif event.type == pygame.VIDEORESIZE:  # Window resize event
                new_width, new_height = event.w, event.h

                # Maintain 9:16 aspect ratio
                if new_width / 9 > new_height / 16:
                    new_width = int(new_height * (9 / 16))
                else:
                    new_height = int(new_width * (16 / 9))

                window_width, window_height = new_width, new_height
                screen = pygame.display.set_mode((window_width, window_height), pygame.RESIZABLE)

        # ++++++++++++++++++  UPDATE ++++++++++++++++++
        # Update character and world
        current_time = pygame.time.get_ticks()
        
        # Ensure world is generated to character depth
        world.ensure_generated_to_depth(character.grid_y + 20)
        
        # Update character (handles digging automatically)
        character.update(world)
        
        # Update camera to follow character
        camera.update(character.y)

        # ++++++++++++++++++  DRAWING ++++++++++++++++++
        # Clear the internal surface
        screen.fill((0, 0, 0))

        # Fill internal surface with the background
        internal_surface.blit(background_image, ((INTERNAL_WIDTH - background_width) // 2, (INTERNAL_HEIGHT - background_height) // 2))

        # Digging game - no automatic spawns needed, character digs automatically
        current_time = pygame.time.get_ticks()
        
        # Character handles digging automatically in its update method

        # Update settings (including auto performance mode)
        settings_manager.update(clock.get_fps())

        # Poll Yotutube api
        if live_chat_id is not None and current_time - last_yt_poll >= yt_poll_interval:
            print("Polling YouTube API...")
            last_yt_poll = current_time
            asyncio.run_coroutine_threadsafe(handle_youtube_poll(), asyncio_loop)

        # Process chat queues - Digging Game Commands
        if config["CHAT_CONTROL"] and current_time - last_queues_pop >= queues_pop_interval:
            last_queues_pop = current_time

            # Handle speed change commands
            if speed_queue:
                author, speed = speed_queue.pop(0)
                print(f"Changing dig speed for {author} to {speed}")
                character.set_dig_speed(speed)
                current_dig_speed = speed
                
                # Add command notification if enabled
                settings = SettingsManager()
                if settings.get_setting("show_command_notifications"):
                    notification_manager.add_command_notification(author, speed.upper(), (character.x, character.y))
            
            # Handle left movement commands
            if left_queue:
                entry = left_queue.pop(0)
                if isinstance(entry, tuple):
                    author, spaces = entry
                    print(f"Moving {author} left by {spaces} spaces")
                    character.move_horizontal(-1, spaces)
                else:
                    author = entry
                    spaces = 1
                    print(f"Moving {author} left by 1 space")
                    character.move_horizontal(-1, 1)
                    
                settings = SettingsManager()
                if settings.get_setting("show_command_notifications"):
                    notification_manager.add_command_notification(author, f"LEFT{spaces if spaces > 1 else ''}", (character.x, character.y))
            
            # Handle right movement commands  
            if right_queue:
                entry = right_queue.pop(0)
                if isinstance(entry, tuple):
                    author, spaces = entry
                    print(f"Moving {author} right by {spaces} spaces")
                    character.move_horizontal(1, spaces)
                else:
                    author = entry
                    spaces = 1
                    print(f"Moving {author} right by 1 space")
                    character.move_horizontal(1, 1)
                    
                settings = SettingsManager()
                if settings.get_setting("show_command_notifications"):
                    notification_manager.add_command_notification(author, f"RIGHT{spaces if spaces > 1 else ''}", (character.x, character.y))

            # Handle subscriber celebrations (gem showers instead of TNT)
            if subscriber_celebration_queue:
                author = subscriber_celebration_queue.pop(0)
                print(f"Spawning MegaTNT for {author} (New Subscriber)")
                new_megatnt = MegaTnt(space, pickaxe.body.position.x, pickaxe.body.position.y - 100,
                      texture_atlas, atlas_items, sound_manager, owner_name=author)
                tnt_list.append(new_megatnt)
                last_tnt_spawn = current_time

            # Handle Superchat/Supersticker TNT
            # Handle gem shower events (subscriber celebrations)
            if gem_shower_queue:
                author = gem_shower_queue.pop(0)
                print(f"🌟 Gem shower for {author}!")
                # Add random gems around character
                for _ in range(5):
                    gem_types = ["talc_gem", "gypsum_gem", "calcite_gem"]
                    gem_type = random.choice(gem_types)
                    offset_x = random.randint(-3, 3)
                    offset_y = random.randint(-3, 0)
                    world.gems[character.grid_x + offset_x][character.grid_y + offset_y] = gem_type

            # Handle tool upgrade requests
            if tool_upgrade_queue:
                author, gem_type = tool_upgrade_queue.pop(0)
                if gem_type in character.gem_inventory and character.gem_inventory[gem_type] >= 10:
                    # Consume 10 gems for upgrade
                    character.gem_inventory[gem_type] -= 10
                    character.upgrade_tool(gem_type)
                    print(f"🔧 {author} upgraded tool with {gem_type}!")
                    
                    # Add upgrade notification
                    settings = SettingsManager()
                    if settings.get_setting("show_command_notifications"):
                        notification_manager.add_command_notification(author, f"UPGRADE SUCCESS", (character.x, character.y))
                else:
                    print(f"❌ {author} doesn't have enough {gem_type} for upgrade (need 10)")

            # Handle hourly events (special rewards)
            if hourly_event_queue:
                event_name = hourly_event_queue.pop(0)
                print(f"⏰ Hourly event: {event_name}")
                # Give player rare gems for playing long sessions
                character.tool_efficiency *= 1.2  # 20% efficiency boost for the hour
                print(f"🎉 Efficiency boost! Now {character.tool_efficiency:.2f}x")

            # Handle efficiency boost events (replacing old "big" command)
            if gem_shower_queue:  # Reuse gem shower for special boosts
                pass  # Already handled above

            # Handle power-up activations (future feature)
            if powerup_queue:
                author, powerup_type = powerup_queue.pop(0)
                print(f"🌟 {author} activated {powerup_type} power-up!")
                # TODO: Implement power-up effects (fruits, vegetables, flowers)

            # Handle Rainbow command (visual effect for character)
            if rainbow_queue:
                author = rainbow_queue.pop(0)
                print(f"🌈 {author} activated rainbow mode!")
                character.activate_rainbow_mode(15000)

            # Handle Shield command (temporary invincibility)
            if shield_queue:
                author = shield_queue.pop(0)
                print(f"🛡️ {author} activated shield!")
                character.activate_shield(10000)

            # Handle Freeze command (pause digging temporarily)
            if freeze_queue:
                author = freeze_queue.pop(0)
                print(f"🧊 {author} activated freeze!")
                character.activate_freeze(5000)

            # Handle Gem Shower (Follower Milestones)
            if gem_shower_queue:
                milestone = gem_shower_queue.pop(0)
                print(f"💎 GEM SHOWER! {milestone}")
                # Give player random gems for milestone
                gem_types = ['topaz_gem', 'quartz_gem', 'apatite_gem', 'fluorite_gem']
                for _ in range(10):
                    gem_type = random.choice(gem_types)
                    character.collect_gem(gem_type)

            # Handle Subscriber Celebrations
            if subscriber_celebration_queue:
                event_name = subscriber_celebration_queue.pop(0)
                print(f"🎉 SUBSCRIBER CELEBRATION! {event_name}")
                # Give player bonus gems and efficiency boost
                gem_types = ['diamond_gem', 'corundum_gem', 'topaz_gem']
                for _ in range(5):
                    gem_type = random.choice(gem_types)
                    character.collect_gem(gem_type)
                character.tool_efficiency *= 1.5  # Temporary efficiency boost

            # Handle Hourly Events
            if hourly_event_queue:
                event_name = hourly_event_queue.pop(0)
                print(f"⏰ HOURLY SPECIAL EVENT! {event_name}")
                # Give player special hourly rewards
                gem_types = ['diamond_gem', 'corundum_gem']
                for _ in range(15):
                    gem_type = random.choice(gem_types)
                    character.collect_gem(gem_type)
                character.tool_efficiency *= 2.0  # Double efficiency for an hour
                print(f"🎉 Hourly efficiency boost! Now {character.tool_efficiency:.2f}x")


        # Draw world blocks in visible area
        visible_range = 25  # Blocks around character horizontally
        start_x = character.grid_x - visible_range
        end_x = character.grid_x + visible_range
        start_y = max(0, character.grid_y - 10)  # Above character
        end_y = character.grid_y + 20  # Below character
        
        for x in range(start_x, end_x):
            for y in range(start_y, end_y):
                # Draw blocks
                block_type = world.get_block_at(x, y)
                if block_type:
                    screen_x = (x * BLOCK_SIZE) - camera.offset_x
                    screen_y = (y * BLOCK_SIZE) - camera.offset_y
                    
                    # Simple colored rectangle for now (will add textures later)
                    color = get_block_color(block_type)
                    pygame.draw.rect(internal_surface, color, 
                                   (screen_x, screen_y, BLOCK_SIZE, BLOCK_SIZE))
                    
                    # Draw outline for rocks
                    if "rock" in block_type:
                        pygame.draw.rect(internal_surface, (0, 0, 0), 
                                       (screen_x, screen_y, BLOCK_SIZE, BLOCK_SIZE), 2)
                
                # Draw gems
                gem_type = world.get_gem_at(x, y)
                if gem_type:
                    screen_x = (x * BLOCK_SIZE) - camera.offset_x
                    screen_y = (y * BLOCK_SIZE) - camera.offset_y
                    
                    # Draw gem as a sparkly circle
                    gem_color = get_gem_color(gem_type)
                    center_x = screen_x + BLOCK_SIZE // 2
                    center_y = screen_y + BLOCK_SIZE // 2
                    pygame.draw.circle(internal_surface, gem_color, (center_x, center_y), 12)
                    pygame.draw.circle(internal_surface, (255, 255, 255), (center_x, center_y), 12, 2)

        # Draw character
        character.draw(internal_surface, camera)

        # Draw particles
        for explosion in explosions:
            explosion.update()
            explosion.draw(internal_surface, camera)

        # Optionally, remove explosions that have no particles left:
        explosions = [e for e in explosions if e.particles]

        # Draw HUD with character reference for gem inventory
        hud.draw(internal_surface, character.y, True, current_dig_speed, settings_manager, character)

        # Scale internal surface to fit the resized window
        scaled_surface = pygame.transform.smoothscale(internal_surface, (window_width, window_height))
        screen.blit(scaled_surface, (0, 0))

        # Draw notifications on the scaled screen
        notification_manager.draw(screen, camera, window_width, window_height)

        # Draw settings panel (on top of scaled surface)
        settings_manager.draw(screen)

        # Save progress
        if current_time - last_save_progress >= save_progress_interval:
            # Save the game state or progress here
            print("Saving progress...")
            last_save_progress = current_time
            # Save progress to logs folder
            log_dir = Path(__file__).parent.parent / "logs"
            log_dir.mkdir(parents=True, exist_ok=True)
            with open(log_dir / "progress.txt", "a+") as f:
                f.write(f"Date: {time.strftime('%Y-%m-%d %H:%M:%S')} | ")
                f.write(f"Y: {-int(pickaxe.body.position.y // BLOCK_SIZE)} ")
                f.write(f"coal: {hud.amounts['coal']} ")
                f.write(f"iron: {hud.amounts['iron_ingot']} ")
                f.write(f"gold: {hud.amounts['gold_ingot']} ")
                f.write(f"copper: {hud.amounts['copper_ingot']} ")
                f.write(f"redstone: {hud.amounts['redstone']} ")
                f.write(f"lapis: {hud.amounts['lapis_lazuli']} ")
                f.write(f"diamond: {hud.amounts['diamond']} ")
                f.write(f"emerald: {hud.amounts['emerald']} \n")

        # Update notifications
        notification_manager.update()

        # Capture frame for streaming (before display flip) - COMMENTED OUT
        # if stream_manager and stream_manager.is_streaming():
        #     stream_manager.capture_frame(screen)

        # Update the display
        pygame.display.flip()
        clock.tick(FRAMERATE)  # Cap the frame rate

        # Inside the main loop
        keys = pygame.key.get_pressed()

        # Handle TNT spawn (key T)
        if keys[pygame.K_t]:
            if not key_t_pressed:  # Only spawn if the key was not pressed in the previous frame
                new_tnt = Tnt(space, pickaxe.body.position.x, pickaxe.body.position.y - 100,
                            texture_atlas, atlas_items, sound_manager)
                tnt_list.append(new_tnt)
                last_tnt_spawn = current_time
                # New random interval for the next TNT spawn
                tnt_spawn_interval = 1000 * random.uniform(config["TNT_SPAWN_INTERVAL_SECONDS_MIN"], config["TNT_SPAWN_INTERVAL_SECONDS_MAX"])
            key_t_pressed = True
        else:
            key_t_pressed = False  # Reset the flag when the key is released

        # Handle MegaTNT spawn (key M)
        if keys[pygame.K_m]:
            if not key_m_pressed:  # Only spawn if the key was not pressed in the previous frame
                new_megatnt = MegaTnt(space, pickaxe.body.position.x, pickaxe.body.position.y - 100,
                                    texture_atlas, atlas_items, sound_manager)
                tnt_list.append(new_megatnt)
                last_tnt_spawn = current_time
                # New random interval for the next TNT spawn
                tnt_spawn_interval = 1000 * random.uniform(config["TNT_SPAWN_INTERVAL_SECONDS_MIN"], config["TNT_SPAWN_INTERVAL_SECONDS_MAX"])
            key_m_pressed = True
        else:
            key_m_pressed = False  # Reset the flag when the key is released

    # Cleanup hybrid YouTube monitoring
    if hybrid_youtube_manager:
        hybrid_youtube_manager.stop_monitoring()
        print("📴 Real-time monitoring stopped")
    
    # Cleanup auto-stream creator
    if auto_stream_creator:
        auto_stream_creator.stop_stream()
        print("📴 Auto-stream stopped")
    
    # Cleanup streaming
    if stream_manager:
        stream_manager.stop_streaming()
        print("📴 Streaming stopped")

    # Quit pygame properly
    pygame.quit()

    # Return exit code: 0 for user quit (close window), 1 for crash/error
    if user_quit:
        import sys
        sys.exit(0)  # Normal exit - user closed window
    else:
        import sys
        sys.exit(1)  # Abnormal exit - game crashed or error

game()