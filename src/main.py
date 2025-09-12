import time
import pygame
import pymunk
import pymunk.pygame_util
from youtube import get_live_stream, get_new_live_chat_messages, get_live_chat_id, get_subscriber_count, validate_live_stream_id, get_live_streams
from smart_subscriber_estimator import SmartSubscriberEstimator
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
# from weather import WeatherSystem  # Removed for performance
import datetime
from notifications import NotificationManager
from competitive_system import competitive_system
from realtime_chat import AsyncRealtimeChat
from like_tracker import like_tracker

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

# Smart subscriber estimation
subscriber_estimator = SmartSubscriberEstimator()

if config["CHAT_CONTROL"] == True:
    # print("Checking for live stream...")  # Removed for performance

    # First try specific live stream ID if provided
    if config["LIVESTREAM_ID"] is not None and config["LIVESTREAM_ID"] != "":
        stream_id = validate_live_stream_id(config["LIVESTREAM_ID"])
        live_stream = get_live_stream(stream_id)
        if live_stream:
            print("Using specific live stream:", live_stream["snippet"]["title"])

    # If no specific stream found, try to auto-detect live streams from channel
    if live_stream is None and config["CHANNEL_ID"] is not None and config["CHANNEL_ID"] != "":
        print("No specific live stream found. Attempting auto-detection...")
        from youtube import get_live_streams
        try:
            live_streams = get_live_streams(config["CHANNEL_ID"])
            if live_streams:
                # Use the first live stream found
                auto_stream_id = live_streams[0]["video_id"]
                live_stream = get_live_stream(auto_stream_id)
                if live_stream:
                    print(f"Auto-detected live stream: {live_streams[0]['title']}")
            else:
                print("No live streams found for this channel.")
        except Exception as e:
            print(f"Error during auto-detection: {e}")

    if live_stream is None:
        print("No live stream found. App will run without chat integration.")
    else:
        print("Live stream ready:", live_stream["snippet"]["title"])

    # get chat id from live stream
    if live_stream is not None:
        # print("Fetching live chat ID...")  # Removed for performance
        live_chat_id = get_live_chat_id(live_stream["id"])

    if live_chat_id is None:
        print("No live chat ID found. App will run without it.")
    else:
        print("Live chat ID found:", live_chat_id)

    # get subscribers count
    if(config["CHANNEL_ID"] is not None and config["CHANNEL_ID"] != ""):
        # print("Fetching subscribers count...")  # Removed for performance
        subscribers = get_subscriber_count(config["CHANNEL_ID"])

    if subscribers is None:
        print("No subscribers count found. App will run without it.")
    else:
        print("Subscribers count found:", subscribers)

    # get followers count (using view count as proxy for followers)
    if(config["CHANNEL_ID"] is not None and config["CHANNEL_ID"] != ""):
        from youtube import get_channel_stats
        stats = get_channel_stats(config["CHANNEL_ID"])
        if stats and 'viewCount' in stats:
            followers = int(stats['viewCount']) // 1000  # Use view count / 1000 as follower approximation
            last_follower_milestone = (followers // 100) * 100
            print("Follower count approximation:", followers)

# Initialize realtime chat and competitive system
realtime_chat = AsyncRealtimeChat(competitive_system)

# Command execution queue (populated by realtime chat)
command_execution_queue = []

# Special event queues
mega_tnt_queue = []
golden_ore_shower_queue = []
hourly_event_queue = []
likes_tnt_queue = []  # Queue for TNT from likes

def on_chat_command(author: str, command: str, result: dict):
    """Callback when a chat command is processed"""
    global command_execution_queue
    
    if result['success']:
        # Add to execution queue with result info
        command_execution_queue.append({
            'author': author,
            'command': command,
            'result': result,
            'timestamp': time.time()
        })
        
        # Show possession change in console
        if result.get('new_possessor'):
            print(f"⚔️ {result['new_possessor']} takes control with {command}!")
    else:
        # Command failed due to cooldown - show notification in game
        if result.get('reason') == 'cooldown' and result.get('remaining_seconds'):
            # This will be handled in the game loop where notification_manager exists
            command_execution_queue.append({
                'author': author,
                'command': command,
                'result': result,
                'cooldown_notification': True,
                'timestamp': time.time()
            })
        print(f"⏳ {author} on cooldown for {command}: {result['remaining_seconds']:.0f}s remaining")

# Register the callback
realtime_chat.add_event_callback(on_chat_command)

async def handle_subscriber_check():
    """Check for subscriber updates and likes"""
    global subscribers, followers, last_follower_milestone, subscriber_estimator
    
    try:
        if subscribers is not None:
            new_subscribers = get_subscriber_count(config["CHANNEL_ID"])
            if new_subscribers is not None:
                had_big_jump = subscriber_estimator.update_actual_count(new_subscribers)
                
                if new_subscribers > subscribers:
                    diff = new_subscribers - subscribers
                    if had_big_jump and diff >= 100:
                        print(f"🎉 BIG SUBSCRIBER JUMP: +{diff} subs!")
                        for i in range(min(5, diff // 20)):
                            mega_tnt_queue.append("Subscriber Wave")
                    else:
                        mega_tnt_queue.append("New Subscriber")
                    subscribers = new_subscribers
        
        if subscriber_estimator.should_trigger_estimated_sub():
            print("✨ Estimated new subscriber")
            mega_tnt_queue.append("New Subscriber")

        # Check for new likes on the video
        if config.get("LIVESTREAM_ID") and like_tracker.should_check_likes():
            from youtube import get_video_statistics
            stats = get_video_statistics(config["LIVESTREAM_ID"])
            if stats:
                has_new_likes, new_like_count = like_tracker.update_like_count(stats["likeCount"])
                if has_new_likes:
                    # Queue TNT spawns for new likes
                    notification_manager.add_like_achievement(f"+{new_like_count} likes!")

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
                    
    except Exception as e:
        print(f"ERROR in subscriber check: {e}")

def start_event_loop(loop):
    asyncio.set_event_loop(loop)
    loop.run_forever()

# Create a new event loop
asyncio_loop = asyncio.new_event_loop()
# Start it in a daemon thread so it doesn't block shutdown
threading.Thread(target=start_event_loop, args=(asyncio_loop,), daemon=True).start()

# Start the realtime chat system if chat control is enabled
if config["CHAT_CONTROL"] and live_stream is not None:
    # print("Starting realtime chat processor...")  # Removed for performance
    # Clear any old cooldowns from before the game started
    competitive_system.reset_for_new_game()
    realtime_chat.start()

def game():
    global last_hour_checked
    
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

    # HUD with competitive system integration
    hud = Hud(texture_atlas, atlas_items)
    hud.competitive_system = competitive_system

    # Explosions
    explosions = []

    # Settings
    settings_manager = SettingsManager()
    # weather_system = WeatherSystem()  # Removed for performance
    
    # Initialize notifications with competitive system
    from notifications import NotificationManager
    notification_manager = NotificationManager(competitive_system=competitive_system)

    # Youtube
    yt_poll_interval = 1000 * config["YT_POLL_INTERVAL_SECONDS"]
    last_yt_poll = pygame.time.get_ticks()

    # Save progress interval
    save_progress_interval = 1000 * config["SAVE_PROGRESS_INTERVAL_SECONDS"]
    last_save_progress = pygame.time.get_ticks()

    # Youtupe chat queues
    queues_pop_interval = 1000 * config["QUEUES_POP_INTERVAL_SECONDS"]
    last_queues_pop = pygame.time.get_ticks()
    
    # Like TNT spawning timer (2 seconds between spawns)
    like_tnt_spawn_interval = 2000  # 2 seconds in milliseconds
    last_like_tnt_spawn = pygame.time.get_ticks()

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
                    # Also simulate getting 1 like for testing
                    has_new, count = like_tracker.update_like_count(
                        (like_tracker.current_like_count or 0) + 1
                    )
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
        if settings_manager.get_setting("auto_tnt_spawn") and (not config["CHAT_CONTROL"] or (not command_execution_queue and not mega_tnt_queue)) and current_time - last_tnt_spawn >= tnt_spawn_interval:
             # Example: spawn TNT at position (400, 300) with a given texture
             new_tnt = Tnt(space, pickaxe.body.position.x, pickaxe.body.position.y - 100,
               texture_atlas, atlas_items, sound_manager)
             tnt_list.append(new_tnt)
             last_tnt_spawn = current_time
             # New random interval for the next TNT spawn
             tnt_spawn_interval = 1000 * random.uniform(config["TNT_SPAWN_INTERVAL_SECONDS_MIN"], config["TNT_SPAWN_INTERVAL_SECONDS_MAX"])

        # Check if it's time to change the pickaxe (random)
        if settings_manager.get_setting("auto_pickaxe_change") and (not config["CHAT_CONTROL"] or not command_execution_queue) and current_time - last_random_pickaxe >= random_pickaxe_interval:
            pickaxe.random_pickaxe(texture_atlas, atlas_items)
            last_random_pickaxe = current_time
            # New random interval for the next pickaxe change
            random_pickaxe_interval = 1000 * random.uniform(config["RANDOM_PICKAXE_INTERVAL_SECONDS_MIN"], config["RANDOM_PICKAXE_INTERVAL_SECONDS_MAX"])

        # Check if it's time for pickaxe enlargement (random)
        if settings_manager.get_setting("auto_size_change") and (not config["CHAT_CONTROL"] or not command_execution_queue) and current_time - last_enlarge >= enlarge_interval:
            pickaxe.enlarge(enlarge_duration)
            last_enlarge = current_time + enlarge_duration
            # New random interval for the next enlargement
            enlarge_interval = 1000 * random.uniform(config["PICKAXE_ENLARGE_INTERVAL_SECONDS_MIN"], config["PICKAXE_ENLARGE_INTERVAL_SECONDS_MAX"])

        # Check if it's time to change speed (random)
        if settings_manager.get_setting("auto_speed_change") and (not config["CHAT_CONTROL"] or not command_execution_queue) and current_time - last_fast_slow >= fast_slow_interval and not fast_slow_active:
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

        # Weather system removed for performance

        # Update settings (including auto performance mode)
        settings_manager.update(clock.get_fps())

        # Check for subscriber updates periodically
        if config["CHANNEL_ID"] and current_time - last_yt_poll >= yt_poll_interval:
            last_yt_poll = current_time
            asyncio.run_coroutine_threadsafe(handle_subscriber_check(), asyncio_loop)
            
        # Check for hourly events
        current_hour = datetime.datetime.now().hour
        if current_hour != last_hour_checked:
            hourly_event_queue.append(f"Hourly Event {current_hour}:00")
            last_hour_checked = current_hour

        # Process command execution queue from realtime chat
        if config["CHAT_CONTROL"] and command_execution_queue:
            # Process one command per frame for smooth gameplay
            cmd_data = command_execution_queue.pop(0)
            author = cmd_data['author']
            command = cmd_data['command']
            result = cmd_data['result']
            
            # Check if this is a cooldown notification
            if cmd_data.get('cooldown_notification'):
                # Show cooldown notification
                notification_manager.add_cooldown_notification(
                    author, command, result['remaining_seconds']
                )
            else:
                # Show notifications
                if settings_manager.get_setting("show_command_notifications"):
                    # Always show command notification
                    notification_manager.add_command_notification(author, command, pickaxe.body.position)
                    
                    # Only show possession change if it actually changed
                    if result.get('new_possessor'):
                        notification_manager.add_possession_change(author, command)
                
                # Execute the command
                if command == "tnt":
                    # Download profile picture if enabled
                    if settings_manager.get_setting("download_profile_pictures"):
                        from youtube import get_user_profile_picture
                        from profile_picture_manager import profile_picture_manager
                        import threading
                        
                        def download_pic():
                            pic_url = get_user_profile_picture(author)
                            if pic_url:
                                profile_picture_manager.download_profile_picture(author, pic_url)
                        
                        threading.Thread(target=download_pic, daemon=True).start()
                    
                    new_tnt = Tnt(space, pickaxe.body.position.x, pickaxe.body.position.y - 100,
                                 texture_atlas, atlas_items, sound_manager, owner_name=author)
                    tnt_list.append(new_tnt)
                    last_tnt_spawn = current_time
                    
                elif command == "superchat_tnt":
                    # Spawn multiple TNT for superchats
                    for _ in range(config["TNT_AMOUNT_ON_SUPERCHAT"]):
                        new_tnt = Tnt(space, pickaxe.body.position.x, pickaxe.body.position.y - 100,
                                     texture_atlas, atlas_items, sound_manager, owner_name=author)
                        tnt_list.append(new_tnt)
                    last_tnt_spawn = current_time
                    
                elif command == "fast":
                    fast_slow_active = True
                    fast_slow = "Fast"
                    last_fast_slow = current_time
                    fast_slow_interval = 1000 * random.uniform(config["FAST_SLOW_INTERVAL_SECONDS_MIN"], 
                                                              config["FAST_SLOW_INTERVAL_SECONDS_MAX"])
                    
                elif command == "slow":
                    fast_slow_active = True
                    fast_slow = "Slow"
                    last_fast_slow = current_time
                    fast_slow_interval = 1000 * random.uniform(config["FAST_SLOW_INTERVAL_SECONDS_MIN"], 
                                                              config["FAST_SLOW_INTERVAL_SECONDS_MAX"])
                    
                elif command == "big":
                    pickaxe.enlarge(enlarge_duration)
                    last_enlarge = current_time + enlarge_duration
                    enlarge_interval = 1000 * random.uniform(config["PICKAXE_ENLARGE_INTERVAL_SECONDS_MIN"], 
                                                            config["PICKAXE_ENLARGE_INTERVAL_SECONDS_MAX"])
                    
                elif command.endswith("_pickaxe"):
                    pickaxe.pickaxe(command, texture_atlas, atlas_items)
                    last_random_pickaxe = current_time
                    random_pickaxe_interval = 1000 * random.uniform(config["RANDOM_PICKAXE_INTERVAL_SECONDS_MIN"], 
                                                                   config["RANDOM_PICKAXE_INTERVAL_SECONDS_MAX"])
                    
                # elif command == "rainbow":
                #     pickaxe.activate_rainbow_mode(15000)  # 15 seconds
                    
                # elif command == "shield":
                #     pickaxe.activate_shield(10000)  # 10 seconds
                    
                elif command == "freeze":
                    # Temporarily reduce gravity and add upward force
                    old_velocity = pickaxe.body.velocity
                    pickaxe.body.velocity = (old_velocity.x * 0.1, -200)  # Slow and slight upward force
                    
                elif command == "new_member":
                    # Members get special treatment
                    for _ in range(3):
                        mega_tnt_queue.append(f"Member: {author}")
                    golden_ore_shower_queue.append(f"New Member: {author}")
                    
                elif command == "new_subscriber":
                    mega_tnt_queue.append(author)
                
        # Process special event queues
        if current_time - last_queues_pop >= queues_pop_interval:
            last_queues_pop = current_time
            
            # Handle MegaTNT queue
            if mega_tnt_queue:
                author = mega_tnt_queue.pop(0)
                print(f"Spawning MegaTNT for {author}")
                new_megatnt = MegaTnt(space, pickaxe.body.position.x, pickaxe.body.position.y - 100,
                                    texture_atlas, atlas_items, sound_manager, owner_name=author)
                tnt_list.append(new_megatnt)
                last_tnt_spawn = current_time

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

            # Rainbow explosions removed for performance - was causing 1 fps issues

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
        
        # Handle TNT from likes (spawn 1 every 2 seconds if pending) - MOVED OUTSIDE queue processing
        if current_time - last_like_tnt_spawn >= like_tnt_spawn_interval:
            if like_tracker.consume_tnt_reward():
                last_like_tnt_spawn = current_time
                
                # Format like count for display with proper pluralization
                like_count = like_tracker.current_like_count or 0
                if like_count >= 10000:
                    like_display = f"{like_count//1000}k Likes"
                elif like_count >= 1000:
                    like_display = f"{like_count/1000:.1f}k Likes"
                elif like_count == 1:
                    like_display = "1 Like"
                else:
                    like_display = f"{like_count} Likes"
                    
                # Spawn TNT for like
                new_tnt = Tnt(space, 
                             pickaxe.body.position.x + random.randint(-50, 50), 
                             pickaxe.body.position.y - random.randint(100, 200),
                             texture_atlas, atlas_items, sound_manager, 
                             owner_name=like_display)
                tnt_list.append(new_tnt)
                print(f"💣 Spawning TNT from like! ({like_tracker.get_pending_rewards()} remaining)")


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

                        # Check if block was broken and award points
                        old_broken = getattr(block, 'broken', False)
                        block.update(space, hud)
                        new_broken = getattr(block, 'broken', False)
                        
                        # Award points if block was just broken
                        if not old_broken and new_broken:
                            block_type = getattr(block, 'block_type', 'stone')
                            result = competitive_system.on_block_broken(block_type)
                            if result['possessor'] and result['points_earned'] > 0:
                                # Could show points popup here if desired
                                pass
                        
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

        # Weather effects removed for performance

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
                # print("Saving progress...")  # Removed for performance
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