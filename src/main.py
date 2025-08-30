import time
import pygame
import pymunk
import pymunk.pygame_util
from youtube import get_live_stream, get_new_live_chat_messages, get_live_chat_id, get_subscriber_count, validate_live_stream_id, get_live_streams
from config import config
from atlas import create_texture_atlas
from pathlib import Path
from chunk import get_block, clean_chunks, delete_block, chunks
from constants import BLOCK_SCALE_FACTOR, BLOCK_SIZE, CHUNK_HEIGHT, CHUNK_WIDTH, INTERNAL_HEIGHT, INTERNAL_WIDTH, FRAMERATE
from pickaxe import Pickaxe
from camera import Camera
from sound import SoundManager
from tnt import Tnt, MegaTnt
import asyncio
import threading
import random
from hud import Hud
from settings import SettingsManager
from weather import WeatherSystem
import datetime
from notifications import NotificationManager
from stream_manager import StreamManager, check_ffmpeg, install_ffmpeg_replit
from realtime_chat import HybridYouTubeManager
from youtube_auto_detect import create_zero_config_setup
from youtube_public_detect import create_public_auto_setup
from auto_stream_creator import create_and_start_stream

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
    
    # Method 1: Private API (OAuth) - Try first if available
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
            
            print("🎬 No active stream found - creating automatic stream...")
            print("💡 This will start a black screen stream that the game can detect")
            
            try:
                auto_stream_creator = create_and_start_stream(stream_key, "black")
                if auto_stream_creator:
                    print("✅ Auto-stream created!")
                    print("⏳ Waiting 10 seconds for YouTube to register the stream...")
                    import time
                    time.sleep(10)
                    
                    # Now try to detect the stream we just created
                    if channel_handle and channel_handle != "@yourhandle":
                        print(f"🔄 Re-trying channel detection: {channel_handle}")
                        auto_setup = create_public_auto_setup(config["API_KEY"], channel_handle=channel_handle)
                        
                        if auto_setup and auto_setup.get('success'):
                            print("🎯 Successfully detected our auto-created stream!")
                
            except Exception as e:
                print(f"⚠️  Auto-stream creation failed: {e}")
    
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
        
    else:
        print("❌ All auto-detection methods failed")
        print("💡 Setup options:")
        print("   1. Set CHANNEL_HANDLE: '@your-youtube-handle'")
        print("   2. Set STREAM_SEARCH_TERM: 'your stream keywords'")  
        print("   3. Set CHANNEL_ID: 'UC...' (manual)")
        print("   4. Make sure you have an active live stream")

elif config["CHAT_CONTROL"] == True:
    print("⚠️  CHAT_CONTROL enabled but no API_KEY provided")
    print("💡 Add your YouTube Data API v3 key to config.json for auto-detection")

# Queues for chat
tnt_queue = []
tnt_superchat_queue = []
fast_slow_queue = []
big_queue = []
pickaxe_queue = []
mega_tnt_queue = []
rainbow_queue = []
shield_queue = []
freeze_queue = []
golden_ore_shower_queue = []
rainbow_explosion_queue = []
hourly_event_queue = []

# Real-time chat system
hybrid_youtube_manager = None

def handle_realtime_chat_message(message):
    """Handle real-time chat messages with <1 second latency"""
    global tnt_queue, fast_slow_queue, big_queue, pickaxe_queue, mega_tnt_queue, rainbow_queue, shield_queue
    
    username = message['username']
    command = message['message'].lower().strip()
    
    print(f"⚡ Real-time: {username} -> {command}")
    
    # Process commands immediately (no waiting for polling!)
    if command == "tnt":
        if message['is_super_chat'] and message['super_chat_amount'] > 0:
            # Super chat gets multiple TNT
            amount = min(int(message['super_chat_amount'] / 5), 20)  # 1 TNT per $5, max 20
            tnt_superchat_queue.extend([username] * amount)
            print(f"💰 Super Chat TNT x{amount} from {username}")
        else:
            tnt_queue.append(username)
        
        # Add to notifications
        if 'notification_manager' in globals():
            notification_manager.add_command_notification(username, "TNT", 0, 0)
    
    elif command == "megatnt":
        mega_tnt_queue.append(username)
        if 'notification_manager' in globals():
            notification_manager.add_command_notification(username, "MEGA TNT", 0, 0)
    
    elif command in ["fast", "slow"]:
        fast_slow_queue.append(command.capitalize())
        if 'notification_manager' in globals():
            notification_manager.add_command_notification(username, command.upper(), 0, 0)
    
    elif command == "big":
        big_queue.append(username)
        if 'notification_manager' in globals():
            notification_manager.add_command_notification(username, "BIG", 0, 0)
    
    elif command in ["wood", "stone", "iron", "gold", "diamond", "netherite"]:
        pickaxe_queue.append(f"{command}_pickaxe")
        if 'notification_manager' in globals():
            notification_manager.add_command_notification(username, command.upper(), 0, 0)
    
    elif command == "rainbow":
        rainbow_queue.append(username)
        if 'notification_manager' in globals():
            notification_manager.add_command_notification(username, "RAINBOW", 0, 0)
    
    elif command == "shield":
        shield_queue.append(username)
        if 'notification_manager' in globals():
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
                mega_tnt_queue.append("New Subscriber")
                if 'notification_manager' in globals():
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
    hybrid_youtube_manager = HybridYouTubeManager(
        config, 
        handle_realtime_chat_message,
        handle_realtime_metrics_update
    )

async def handle_youtube_poll():
    global subscribers, followers, last_follower_milestone # Use global to modify the variable

    if subscribers is not None:
        new_subscribers = get_subscriber_count(config["CHANNEL_ID"])
        if new_subscribers is not None and new_subscribers > subscribers:
            mega_tnt_queue.append("New Subscriber") # Add to mega tnt queue
            rainbow_explosion_queue.append("New Subscriber Rainbow") # Add rainbow explosion
            subscribers = new_subscribers # Update subscriber count

    # Check follower milestones
    if followers is not None and config["CHANNEL_ID"] is not None:
        from youtube import get_channel_stats
        stats = get_channel_stats(config["CHANNEL_ID"])
        if stats and 'viewCount' in stats:
            current_followers = int(stats['viewCount']) // 1000
            current_milestone = (current_followers // 100) * 100
            if current_milestone > last_follower_milestone:
                golden_ore_shower_queue.append(f"{current_milestone} Followers")
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

        if "fast" in text.lower() and author not in [entry[0] for entry in fast_slow_queue]:
            fast_slow_queue.append((author, "Fast"))
            print(f"Added {author} to Fast/Slow queue (Fast)")
        elif "slow" in text.lower() and author not in [entry[0] for entry in fast_slow_queue]:
            fast_slow_queue.append((author, "Slow"))
            print(f"Added {author} to Fast/Slow queue (Slow)")

        if "big" in text.lower() and author not in big_queue:
            big_queue.append(author)
            print(f"Added {author} to Big queue")

        # Check for pickaxe commands (add author and pickaxe type to pickaxe_queue)
        if "wood" in text_lower:
             if author not in [entry[0] for entry in pickaxe_queue]:
                 pickaxe_queue.append((author, "wooden_pickaxe"))
                 print(f"Added {author} to Pickaxe queue (wooden_pickaxe)")
        elif "stone" in text_lower:
             if author not in [entry[0] for entry in pickaxe_queue]:
                 pickaxe_queue.append((author, "stone_pickaxe"))
                 print(f"Added {author} to Pickaxe queue (stone_pickaxe)")
        elif "iron" in text_lower:
             if author not in [entry[0] for entry in pickaxe_queue]:
                 pickaxe_queue.append((author, "iron_pickaxe"))
                 print(f"Added {author} to Pickaxe queue (iron_pickaxe)")
        elif "gold" in text_lower:
             if author not in [entry[0] for entry in pickaxe_queue]:
                 pickaxe_queue.append((author, "golden_pickaxe"))
                 print(f"Added {author} to Pickaxe queue (golden_pickaxe)")
        elif "diamond" in text_lower:
             if author not in [entry[0] for entry in pickaxe_queue]:
                 pickaxe_queue.append((author, "diamond_pickaxe"))
                 print(f"Added {author} to Pickaxe queue (diamond_pickaxe)")
        elif "netherite" in text_lower:
             if author not in [entry[0] for entry in pickaxe_queue]:
                 pickaxe_queue.append((author, "netherite_pickaxe"))
                 print(f"Added {author} to Pickaxe queue (netherite_pickaxe)")

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
    # print(f"Queues: TNT={len(tnt_queue)}, Superchat TNT={len(tnt_superchat_queue)}, Fast/Slow={len(fast_slow_queue)}, Big={len(big_queue)}, Pickaxe={len(pickaxe_queue)}, MegaTNT={len(mega_tnt_queue)}")

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

    # Pymunk physics
    space = pymunk.Space()
    space.gravity = (0, 1000)  # (x, y) - down is positive y

    # Create a resizable window
    screen_size = (window_width, window_height)
    screen = pygame.display.set_mode(screen_size, pygame.RESIZABLE)
    pygame.display.set_caption("Falling Pickaxe")
    # set icon
    icon = pygame.image.load(Path(__file__).parent.parent / "src/assets/pickaxe" / "diamond_pickaxe.png")
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

    sound_manager.load_sound("tnt", assets_dir / "sounds" / "tnt.mp3", 0.3)
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
            # Fallback to TNT sound for achievement
            sound_manager.load_sound("achievement", assets_dir / "sounds" / "tnt.mp3", 0.3)
    except:
        # Fallback to TNT sound for achievement
        sound_manager.load_sound("achievement", assets_dir / "sounds" / "tnt.mp3", 0.3)

    # Camera (create before pickaxe to avoid reference error)
    camera = Camera()

    # Pickaxe
    pickaxe = Pickaxe(space, INTERNAL_WIDTH // 2, INTERNAL_HEIGHT // 2, texture_atlas.subsurface(atlas_items["pickaxe"]["wooden_pickaxe"]), sound_manager)
    pickaxe.camera_ref = camera  # Connect camera for screen shake effects

    # TNT
    last_tnt_spawn = pygame.time.get_ticks()
    tnt_spawn_interval = 1000 * random.uniform(config["TNT_SPAWN_INTERVAL_SECONDS_MIN"], config["TNT_SPAWN_INTERVAL_SECONDS_MAX"])
    tnt_list = []  # List to keep track of spawned TNT objects

    # Random Pickaxe
    last_random_pickaxe = pygame.time.get_ticks()
    random_pickaxe_interval = 1000 * random.uniform(config["RANDOM_PICKAXE_INTERVAL_SECONDS_MIN"], config["RANDOM_PICKAXE_INTERVAL_SECONDS_MAX"])

    # Pickaxe enlargement
    last_enlarge = pygame.time.get_ticks()
    enlarge_interval = 1000 * random.uniform(config["PICKAXE_ENLARGE_INTERVAL_SECONDS_MIN"], config["PICKAXE_ENLARGE_INTERVAL_SECONDS_MAX"])
    enlarge_duration = 1000 * config["PICKAXE_ENLARGE_DURATION_SECONDS"]

    # Fast slow
    fast_slow_active = False
    fast_slow = random.choice(["Fast", "Slow"])
    fast_slow_interval = 1000 * random.uniform(config["FAST_SLOW_INTERVAL_SECONDS_MIN"], config["FAST_SLOW_INTERVAL_SECONDS_MAX"])
    last_fast_slow = pygame.time.get_ticks()

    # HUD
    hud = Hud(texture_atlas, atlas_items)

    # Explosions
    explosions = []

    # Settings and Weather
    settings_manager = SettingsManager()
    weather_system = WeatherSystem()
    
    # Streaming
    stream_manager = None
    if config.get("STREAMING_ENABLED", False):
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
    
    # Connect stream manager to settings
    if stream_manager:
        settings_manager.set_stream_manager(stream_manager)
    
    # Notifications
    from notifications import notification_manager

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
        # Determine which chunks are visible
        # Update physics

        step_speed = 1 / FRAMERATE  # Fixed time step for physics simulation
        if fast_slow_active and fast_slow == "Fast":
            step_speed = 1 / (FRAMERATE / 2)
        elif fast_slow_active and fast_slow == "Slow":
            step_speed = 1 / (FRAMERATE * 2)

        space.step(step_speed)

        start_chunk_y = int(pickaxe.body.position.y // (CHUNK_HEIGHT * BLOCK_SIZE) - 1) - 1
        end_chunk_y = int(pickaxe.body.position.y + INTERNAL_HEIGHT) // (CHUNK_HEIGHT * BLOCK_SIZE)  + 1

        # Update pickaxe
        pickaxe.update()

        # Update camera
        camera.update(pickaxe.body.position.y)

        # ++++++++++++++++++  DRAWING ++++++++++++++++++
        # Clear the internal surface
        screen.fill((0, 0, 0))

        # Fill internal surface with the background
        internal_surface.blit(background_image, ((INTERNAL_WIDTH - background_width) // 2, (INTERNAL_HEIGHT - background_height) // 2))

        # Check if it's time to spawn a new TNT (regular random spawn)
        current_time = pygame.time.get_ticks()
        if settings_manager.get_setting("auto_tnt_spawn") and (not config["CHAT_CONTROL"] or (not tnt_queue and not tnt_superchat_queue and not mega_tnt_queue)) and current_time - last_tnt_spawn >= tnt_spawn_interval:
             # Example: spawn TNT at position (400, 300) with a given texture
             new_tnt = Tnt(space, pickaxe.body.position.x, pickaxe.body.position.y - 100,
               texture_atlas, atlas_items, sound_manager)
             tnt_list.append(new_tnt)
             last_tnt_spawn = current_time
             # New random interval for the next TNT spawn
             tnt_spawn_interval = 1000 * random.uniform(config["TNT_SPAWN_INTERVAL_SECONDS_MIN"], config["TNT_SPAWN_INTERVAL_SECONDS_MAX"])

        # Check if it's time to change the pickaxe (random)
        if settings_manager.get_setting("auto_pickaxe_change") and (not config["CHAT_CONTROL"] or not pickaxe_queue) and current_time - last_random_pickaxe >= random_pickaxe_interval:
            pickaxe.random_pickaxe(texture_atlas, atlas_items)
            last_random_pickaxe = current_time
            # New random interval for the next pickaxe change
            random_pickaxe_interval = 1000 * random.uniform(config["RANDOM_PICKAXE_INTERVAL_SECONDS_MIN"], config["RANDOM_PICKAXE_INTERVAL_SECONDS_MAX"])

        # Check if it's time for pickaxe enlargement (random)
        if settings_manager.get_setting("auto_size_change") and (not config["CHAT_CONTROL"] or not big_queue) and current_time - last_enlarge >= enlarge_interval:
            pickaxe.enlarge(enlarge_duration)
            last_enlarge = current_time + enlarge_duration
            # New random interval for the next enlargement
            enlarge_interval = 1000 * random.uniform(config["PICKAXE_ENLARGE_INTERVAL_SECONDS_MIN"], config["PICKAXE_ENLARGE_INTERVAL_SECONDS_MAX"])

        # Check if it's time to change speed (random)
        if settings_manager.get_setting("auto_speed_change") and (not config["CHAT_CONTROL"] or not fast_slow_queue) and current_time - last_fast_slow >= fast_slow_interval and not fast_slow_active:
            # Randomly choose between "fast" and "slow"
            fast_slow = random.choice(["Fast", "Slow"])
            print("Changing speed to:", fast_slow)
            fast_slow_active = True
            last_fast_slow = current_time
            # New random interval for the next fast/slow spawn
            fast_slow_interval = 1000 * random.uniform(config["FAST_SLOW_INTERVAL_SECONDS_MIN"], config["FAST_SLOW_INTERVAL_SECONDS_MAX"])
        elif current_time - last_fast_slow >= (1000 * config["FAST_SLOW_DURATION_SECONDS"]) and fast_slow_active:
            fast_slow_active = False
            last_fast_slow = current_time

        # Update all TNTs
        for tnt in tnt_list:
            tnt.update(tnt_list, explosions, camera)

        # Update weather system
        weather_system.update(settings_manager)

        # Update settings (including auto performance mode)
        settings_manager.update(clock.get_fps())

        # Poll Yotutube api
        if live_chat_id is not None and current_time - last_yt_poll >= yt_poll_interval:
            print("Polling YouTube API...")
            last_yt_poll = current_time
            asyncio.run_coroutine_threadsafe(handle_youtube_poll(), asyncio_loop)

        # Process chat queues
        if config["CHAT_CONTROL"] and current_time - last_queues_pop >= queues_pop_interval:
            last_queues_pop = current_time

            # Handle regular TNT from chat command
            if tnt_queue:
                author = tnt_queue.pop(0)
                print(f"Spawning regular TNT for {author} (from chat command)")
                
                # Download profile picture if enabled
                settings = SettingsManager()
                if settings.get_setting("download_profile_pictures"):
                    from youtube import get_user_profile_picture
                    from profile_picture_manager import profile_picture_manager
                    import threading
                    
                    def download_pic():
                        pic_url = get_user_profile_picture(author)
                        if pic_url:
                            profile_picture_manager.download_profile_picture(author, pic_url)
                    
                    # Download in background to avoid blocking
                    threading.Thread(target=download_pic, daemon=True).start()
                
                new_tnt = Tnt(space, pickaxe.body.position.x, pickaxe.body.position.y - 100,
                             texture_atlas, atlas_items, sound_manager, owner_name=author)
                tnt_list.append(new_tnt)
                last_tnt_spawn = current_time
                
                # Add command notification if enabled
                if settings.get_setting("show_command_notifications"):
                    notification_manager.add_command_notification(author, "tnt", pickaxe.body.position)

            # Handle MegaTNT (New Subscriber)
            if mega_tnt_queue:
                author = mega_tnt_queue.pop(0)
                print(f"Spawning MegaTNT for {author} (New Subscriber)")
                new_megatnt = MegaTnt(space, pickaxe.body.position.x, pickaxe.body.position.y - 100,
                      texture_atlas, atlas_items, sound_manager, owner_name=author)
                tnt_list.append(new_megatnt)
                last_tnt_spawn = current_time

            # Handle Superchat/Supersticker TNT
            if tnt_superchat_queue:
                author, text = tnt_superchat_queue.pop(0)
                print(f"Spawning TNT for {author} (Superchat: {text})")
                last_tnt_spawn = current_time
                for _ in range(config["TNT_AMOUNT_ON_SUPERCHAT"]):
                    new_tnt = Tnt(space, pickaxe.body.position.x, pickaxe.body.position.y - 100, texture_atlas, atlas_items, sound_manager, owner_name=author)
                    tnt_list.append(new_tnt)

            # Handle Fast/Slow command
            if fast_slow_queue:
                author, q_fast_slow = fast_slow_queue.pop(0)
                print(f"Changing speed for {author} to {q_fast_slow}")
                fast_slow_active = True
                last_fast_slow = current_time
                fast_slow = q_fast_slow
                fast_slow_interval = 1000 * random.uniform(config["FAST_SLOW_INTERVAL_SECONDS_MIN"], config["FAST_SLOW_INTERVAL_SECONDS_MAX"])
                
                # Add command notification if enabled
                settings = SettingsManager()
                if settings.get_setting("show_command_notifications"):
                    notification_manager.add_command_notification(author, q_fast_slow.lower(), pickaxe.body.position)

            # Handle Big pickaxe command
            if big_queue:
                author = big_queue.pop(0)
                print(f"Making pickaxe big for {author}")
                pickaxe.enlarge(enlarge_duration)
                last_enlarge = current_time + enlarge_duration
                enlarge_interval = 1000 * random.uniform(config["PICKAXE_ENLARGE_INTERVAL_SECONDS_MIN"], config["PICKAXE_ENLARGE_INTERVAL_SECONDS_MAX"])
                
                # Add command notification if enabled
                settings = SettingsManager()
                if settings.get_setting("show_command_notifications"):
                    notification_manager.add_command_notification(author, "big", pickaxe.body.position)

            # Handle Pickaxe type command
            if pickaxe_queue:
                author, pickaxe_type = pickaxe_queue.pop(0)
                print(f"Changing pickaxe for {author} to {pickaxe_type}")
                pickaxe.pickaxe(pickaxe_type, texture_atlas, atlas_items)
                last_random_pickaxe = current_time
                random_pickaxe_interval = 1000 * random.uniform(config["RANDOM_PICKAXE_INTERVAL_SECONDS_MIN"], config["RANDOM_PICKAXE_INTERVAL_SECONDS_MAX"])
                
                # Add command notification if enabled
                settings = SettingsManager()
                if settings.get_setting("show_command_notifications"):
                    command_name = pickaxe_type.replace("_pickaxe", "")
                    notification_manager.add_command_notification(author, command_name, pickaxe.body.position)

            # Handle Rainbow command
            if rainbow_queue:
                author = rainbow_queue.pop(0)
                print(f"Activating rainbow mode for {author}")
                pickaxe.activate_rainbow_mode(15000)  # 15 seconds

            # Handle Shield command
            if shield_queue:
                author = shield_queue.pop(0)
                print(f"Activating shield for {author}")
                pickaxe.activate_shield(10000)  # 10 seconds

            # Handle Freeze command
            if freeze_queue:
                author = freeze_queue.pop(0)
                print(f"Freezing pickaxe for {author}")
                # Temporarily reduce gravity and add upward force
                old_velocity = pickaxe.body.velocity
                pickaxe.body.velocity = (old_velocity.x * 0.1, -200)  # Slow and slight upward force

            # Handle Golden Ore Shower (Follower Milestones)
            if golden_ore_shower_queue:
                milestone = golden_ore_shower_queue.pop(0)
                print(f"🌟 GOLDEN ORE SHOWER! {milestone}")
                # Spawn multiple golden ores around pickaxe
                for i in range(20):
                    x_offset = random.randint(-300, 300)
                    y_offset = random.randint(-200, -50)
                    # Create golden blocks that drop gold when broken
                    hud.amounts['gold_ingot'] += random.randint(5, 15)

            # Handle Rainbow Explosions (Subscriber Celebrations)  
            if rainbow_explosion_queue:
                event_name = rainbow_explosion_queue.pop(0)
                print(f"🌈 RAINBOW EXPLOSION! {event_name}")
                # Create spectacular rainbow explosions
                for i in range(5):
                    x_offset = random.randint(-200, 200)
                    y_offset = random.randint(-150, -50)
                    from explosion import Explosion
                    rainbow_explosion = Explosion(
                        pickaxe.body.position.x + x_offset,
                        pickaxe.body.position.y + y_offset,
                        75, texture_atlas, atlas_items
                    )
                    # Make it rainbow colored
                    for particle in rainbow_explosion.particles:
                        hue = random.randint(0, 360)
                        color = pygame.Color(0)
                        color.hsva = (hue, 100, 100, 100)
                        particle.color = color
                    explosions.append(rainbow_explosion)

            # Handle Hourly Events
            if hourly_event_queue:
                event_name = hourly_event_queue.pop(0)
                print(f"⏰ HOURLY SPECIAL EVENT! {event_name}")
                # Random special hourly events
                event_type = random.choice(["mega_tnt_shower", "diamond_rain", "speed_boost", "giant_pickaxe"])
                if event_type == "mega_tnt_shower":
                    for i in range(3):
                        new_megatnt = MegaTnt(space, pickaxe.body.position.x + random.randint(-200, 200), 
                                            pickaxe.body.position.y - random.randint(100, 300),
                                            texture_atlas, atlas_items, sound_manager, owner_name="Hourly Event")
                        tnt_list.append(new_megatnt)
                elif event_type == "diamond_rain":
                    hud.amounts['diamond'] += random.randint(10, 25)
                elif event_type == "speed_boost":
                    fast_slow_active = True
                    fast_slow = "Fast"
                    last_fast_slow = current_time
                elif event_type == "giant_pickaxe":
                    pickaxe.enlarge(20000)  # 20 seconds of giant pickaxe


        # Delete chunks
        clean_chunks(start_chunk_y)

        # Draw blocks in visible chunks
        for chunk_x in range(-1, 2):
            for chunk_y in range(start_chunk_y, end_chunk_y):
                for y in range(CHUNK_HEIGHT):
                    for x in range(CHUNK_WIDTH):
                        block = get_block(chunk_x, chunk_y, x, y, texture_atlas, atlas_items, space)

                        if block == None:
                            continue

                        block.update(space, hud)
                        block.draw(internal_surface, camera)

        # Draw pickaxe
        pickaxe.draw(internal_surface, camera)

        # Draw TNT
        for tnt in tnt_list:
            tnt.draw(internal_surface, camera)

        # Draw particles
        for explosion in explosions:
            explosion.update()
            explosion.draw(internal_surface, camera)

        # Optionally, remove explosions that have no particles left:
        explosions = [e for e in explosions if e.particles]

        # Draw weather effects
        weather_system.draw(internal_surface, camera, settings_manager)

        # Draw HUD
        hud.draw(internal_surface, pickaxe.body.position.y, fast_slow_active, fast_slow, settings_manager)

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

        # Capture frame for streaming (before display flip)
        if stream_manager and stream_manager.is_streaming():
            stream_manager.capture_frame(screen)

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