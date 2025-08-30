
import pygame
import time
import random
from minecraft_font import minecraft_font

class Achievement:
    def __init__(self, title, description, x=None, y=None, play_sound=True):
        self.title = title
        self.description = description
        self.timer = 5000  # 5 seconds display time
        self.start_time = pygame.time.get_ticks()
        self.slide_progress = 0.0  # For slide-in animation
        self.slide_speed = 0.08
        
        # Position (will slide in from right)
        self.target_x = x if x is not None else 50
        self.target_y = y if y is not None else 50
        self.current_x = 400  # Start off-screen
        self.current_y = self.target_y
        
        # Play achievement sound only if requested
        if play_sound:
            try:
                from sound import SoundManager
                sound_manager = SoundManager()
                sound_manager.play_sound("achievement")
            except:
                pass
                
    def _init_no_sound(self, title, description, x=None, y=None):
        """Alternative init without sound"""
        self.__init__(title, description, x, y, play_sound=False)
        
    def update(self):
        current_time = pygame.time.get_ticks()
        self.timer = 5000 - (current_time - self.start_time)
        
        # Update slide animation
        if self.slide_progress < 1.0:
            self.slide_progress = min(1.0, self.slide_progress + self.slide_speed)
            # Easing function for smooth slide
            ease = 1 - (1 - self.slide_progress) ** 3
            self.current_x = 400 + (self.target_x - 400) * ease
        
        return self.timer > 0
        
    def draw(self, surface):
        if self.timer <= 0:
            return
            
        # Create achievement background (Minecraft style)
        bg_width = 320
        bg_height = 64
        
        # Background with border
        bg_surface = pygame.Surface((bg_width, bg_height))
        bg_surface.fill((64, 64, 64))  # Dark gray background
        pygame.draw.rect(bg_surface, (0, 0, 0), bg_surface.get_rect(), 2)  # Black border
        
        # Achievement icon (grass block)
        icon_size = 32
        icon_surface = pygame.Surface((icon_size, icon_size))
        icon_surface.fill((34, 139, 34))  # Green color for grass block
        pygame.draw.rect(icon_surface, (0, 0, 0), icon_surface.get_rect(), 1)
        bg_surface.blit(icon_surface, (16, 16))
        
        # Title text
        title_surface = minecraft_font.render_with_shadow(self.title, (255, 255, 0), (0, 0, 0), "normal")
        bg_surface.blit(title_surface, (60, 8))
        
        # Description text
        desc_surface = minecraft_font.render_with_shadow(self.description, (255, 255, 255), (0, 0, 0), "small")
        bg_surface.blit(desc_surface, (60, 32))
        
        # Apply fade out effect in last second
        if self.timer < 1000:
            alpha = int(255 * (self.timer / 1000))
            bg_surface.set_alpha(alpha)
        
        surface.blit(bg_surface, (self.current_x, self.current_y))

class CommandNotification:
    def __init__(self, username, command, x, y):
        self.username = username
        self.command = command
        self.x = x
        self.y = y
        self.timer = 3000  # 3 seconds
        self.start_time = pygame.time.get_ticks()
        
    def update(self):
        current_time = pygame.time.get_ticks()
        self.timer = 3000 - (current_time - self.start_time)
        return self.timer > 0
        
    def draw(self, surface):
        if self.timer <= 0:
            return
            
        # Fade out effect
        alpha = min(255, max(0, int(255 * (self.timer / 3000))))
        
        # Create notification surface
        notification_text = f"{self.username}: {self.command}"
        text_surface = minecraft_font.render_with_shadow(notification_text, (255, 255, 0), (0, 0, 0), "small")
        text_surface.set_alpha(alpha)
        
        # Draw background
        bg_rect = pygame.Rect(self.x - 5, self.y - 2, text_surface.get_width() + 10, text_surface.get_height() + 4)
        bg_surface = pygame.Surface((bg_rect.width, bg_rect.height))
        bg_surface.fill((0, 0, 0))
        bg_surface.set_alpha(alpha // 2)
        surface.blit(bg_surface, bg_rect)
        
        # Draw text
        surface.blit(text_surface, (self.x, self.y))

class TopPlayersTracker:
    def __init__(self):
        self.player_activity = {}
        self.last_reset = time.time()
        self.reset_interval = 300  # 5 minutes
        
    def add_activity(self, username):
        """Add activity for a player"""
        if username not in self.player_activity:
            self.player_activity[username] = 0
        self.player_activity[username] += 1
        
    def update(self):
        """Check if we need to reset the leaderboard"""
        current_time = time.time()
        if current_time - self.last_reset >= self.reset_interval:
            self.player_activity.clear()
            self.last_reset = current_time
            
    def get_top_players(self, count=5):
        """Get top players sorted by activity"""
        return sorted(self.player_activity.items(), key=lambda x: x[1], reverse=True)[:count]
        
    def get_time_until_reset(self):
        """Get time until next reset in seconds"""
        return max(0, self.reset_interval - (time.time() - self.last_reset))

class RightPanel:
    def __init__(self, width=120):  # Much smaller width
        self.width = width
        self.top_players = TopPlayersTracker()
        self.commands = [
            "tnt", "fast", "slow", "big", "wood", "stone", 
            "iron", "gold", "diamond", "netherite", "rainbow", 
            "shield", "freeze"
        ]
        
        # Subscriber tracking for mega TNT display
        self.recent_subscriber = None
        self.subscriber_display_timer = 0
        
        # Cache textures to reduce lag
        self.texture_cache = {}
        self.texture_cache_loaded = False
        
    def update(self):
        self.top_players.update()
        
    def add_player_activity(self, username):
        self.top_players.add_activity(username)
        
    def _load_texture_cache(self):
        """Load textures once to avoid lag"""
        if self.texture_cache_loaded:
            return
        try:
            from pathlib import Path
            from atlas import create_texture_atlas
            from constants import BLOCK_SCALE_FACTOR
            assets_dir = Path(__file__).parent.parent / "src/assets"
            (texture_atlas, atlas_items) = create_texture_atlas(assets_dir)
            texture_atlas = pygame.transform.scale(texture_atlas,
                                                (texture_atlas.get_width() * BLOCK_SCALE_FACTOR,
                                                texture_atlas.get_height() * BLOCK_SCALE_FACTOR))
            for category in atlas_items:
                for item in atlas_items[category]:
                    x, y, w, h = atlas_items[category][item]
                    atlas_items[category][item] = (x * BLOCK_SCALE_FACTOR, y * BLOCK_SCALE_FACTOR, w * BLOCK_SCALE_FACTOR, h * BLOCK_SCALE_FACTOR)
            
            # Cache the icons we need (2x larger)
            mega_tnt_rect = pygame.Rect(atlas_items["block"]["mega_tnt"])
            self.texture_cache["mega_tnt"] = pygame.transform.scale(
                texture_atlas.subsurface(mega_tnt_rect), (24, 24))
            
            tnt_rect = pygame.Rect(atlas_items["block"]["tnt"])
            self.texture_cache["tnt"] = pygame.transform.scale(
                texture_atlas.subsurface(tnt_rect), (24, 24))
                
            self.texture_cache_loaded = True
        except:
            self.texture_cache_loaded = True  # Don't keep trying

    def draw(self, surface, screen_width, screen_height):
        panel_x = screen_width - self.width
        
        # Draw fading panel background
        fade_start = int(screen_height * 0.33)  # Start fade at 1/3 down
        fade_end = int(screen_height * 0.45)    # End fade at 45% down
        
        # Solid panel for top 1/3
        if fade_start > 0:
            panel_surface_top = pygame.Surface((self.width, fade_start))
            panel_surface_top.fill((64, 64, 64))
            panel_surface_top.set_alpha(180)
            surface.blit(panel_surface_top, (panel_x, 0))
        
        # Fading section from 33% to 45%
        if fade_end > fade_start:
            fade_height = fade_end - fade_start
            for i in range(fade_height):
                fade_progress = i / fade_height  # 0.0 to 1.0
                alpha = int(180 * (1.0 - fade_progress))  # 180 to 0
                
                if alpha > 0:
                    line_surface = pygame.Surface((self.width, 1))
                    line_surface.fill((64, 64, 64))
                    line_surface.set_alpha(alpha)
                    surface.blit(line_surface, (panel_x, fade_start + i))
        
        y_offset = 8  # Start closer to top
        
        # TOP PLAYERS FIRST (at the top) - countdown disabled
        # time_left = int(self.top_players.get_time_until_reset())
        # minutes = time_left // 60
        # seconds = time_left % 60
        # players_title = minecraft_font.render_with_shadow(f"TOP ({minutes:02d}:{seconds:02d})", (255, 255, 0), (0, 0, 0), "tiny")
        
        players_title = minecraft_font.render_with_shadow("TOP", (255, 255, 0), (0, 0, 0), "tiny")
        surface.blit(players_title, (panel_x + 3, y_offset))
        y_offset += players_title.get_height() + 3
        
        # Show top 5 players (no profile pics for performance)
        top_players = self.top_players.get_top_players(5)
        for i, (username, activity) in enumerate(top_players):
            rank_color = self.get_rank_color(i)
            
            # Extend username to 10 characters, right justified to expand left
            display_name = username[:10] + "..." if len(username) > 10 else username
            player_text = minecraft_font.render_with_shadow(display_name, rank_color, (0, 0, 0), "tiny")
            
            # Right justify - position text so it can extend beyond panel to the left
            text_x = panel_x + self.width - 3 - player_text.get_width()
            surface.blit(player_text, (text_x, y_offset))
            y_offset += player_text.get_height() + 1
        
        y_offset += 10  # Space between sections
        
        # REWARDS section (simplified)
        self._load_texture_cache()
        
        if "mega_tnt" in self.texture_cache:
            surface.blit(self.texture_cache["mega_tnt"], (panel_x + 3, y_offset))
            sub_text = minecraft_font.render_with_shadow("Sub=MEGA", (255, 100, 100), (0, 0, 0), "tiny")
            surface.blit(sub_text, (panel_x + 35, y_offset))  # Moved further right for larger icon
            y_offset += 26  # Increased for larger icon
            
            # Show recent subscriber name if available
            if self.recent_subscriber and pygame.time.get_ticks() < self.subscriber_display_timer:
                sub_name = minecraft_font.render_with_shadow(f"{self.recent_subscriber[:8]}", (255, 255, 100), (0, 0, 0), "tiny")
                surface.blit(sub_name, (panel_x + 3, y_offset))
                y_offset += sub_name.get_height() + 2
        else:
            sub_text = minecraft_font.render_with_shadow("Sub=MEGA", (255, 100, 100), (0, 0, 0), "tiny")
            surface.blit(sub_text, (panel_x + 3, y_offset))
            y_offset += sub_text.get_height() + 3
            
        # Like reward
        like_text = minecraft_font.render_with_shadow("Like", (100, 255, 100), (0, 0, 0), "tiny")
        surface.blit(like_text, (panel_x + 3, y_offset))
        y_offset += like_text.get_height() + 1
        
        if "tnt" in self.texture_cache:
            like_count = minecraft_font.render_with_shadow("10X", (100, 255, 100), (0, 0, 0), "tiny")
            surface.blit(like_count, (panel_x + 3, y_offset))
            surface.blit(self.texture_cache["tnt"], (panel_x + 35, y_offset))  # Moved further right
            y_offset += 26  # Increased for larger icon
        else:
            like_count = minecraft_font.render_with_shadow("10 TNT", (100, 255, 100), (0, 0, 0), "tiny")
            surface.blit(like_count, (panel_x + 3, y_offset))
            y_offset += like_count.get_height() + 6
        
        # Add gap before COMMANDS section
        y_offset += 10  # Extra line break spacing
        
        # COMMANDS section (simplified, single column)
        commands_title = minecraft_font.render_with_shadow("Commands:", (255, 255, 255), (0, 0, 0), "tiny")
        surface.blit(commands_title, (panel_x + 3, y_offset))
        y_offset += commands_title.get_height() + 3
        
        # Show only most important commands in single column
        important_commands = ["tnt", "fast", "slow", "big", "wood", "iron", "gold", "diamond"]
        for command in important_commands:
            command_color = self.get_command_color(command)
            command_text = minecraft_font.render_with_shadow(f"•{command}", command_color, (0, 0, 0), "tiny")
            surface.blit(command_text, (panel_x + 3, y_offset))
            y_offset += command_text.get_height() + 1
            
    def get_command_color(self, command):
        """Get color for different commands"""
        color_map = {
            "tnt": (255, 100, 100),
            "fast": (100, 255, 100),
            "slow": (100, 100, 255),
            "big": (255, 165, 0),
            "wood": (139, 69, 19),
            "stone": (128, 128, 128),
            "iron": (192, 192, 192),
            "gold": (255, 215, 0),
            "diamond": (185, 242, 255),
            "netherite": (68, 58, 78),
            "rainbow": (255, 0, 255),
            "shield": (0, 255, 255),
            "freeze": (173, 216, 230)
        }
        return color_map.get(command, (255, 255, 255))
        
    def get_rank_color(self, rank):
        """Get color for different ranks"""
        if rank == 0:
            return (255, 215, 0)  # Gold
        elif rank == 1:
            return (192, 192, 192)  # Silver
        elif rank == 2:
            return (205, 127, 50)  # Bronze
        else:
            return (255, 255, 255)  # White

class NotificationManager:
    def __init__(self):
        self.notifications = []
        self.achievements = []
        self.right_panel = RightPanel()
        self.last_update = 0
        self.update_interval = 100  # Update every 100ms instead of every frame
        
    def add_command_notification(self, username, command, pickaxe_pos):
        """Add a notification near the pickaxe"""
        import random
        x = pickaxe_pos[0] + random.randint(-100, 100)
        y = pickaxe_pos[1] + random.randint(-50, -20)
        
        notification = CommandNotification(username, command, x, y)
        self.notifications.append(notification)
        
        # Add to leaderboard
        self.right_panel.add_player_activity(username)
        
    def add_subscriber_achievement(self, username=None):
        """Add achievement popup for new subscriber"""
        if username is None:
            username = f"Player#{random.randint(1000, 9999)}"
        
        # Update right panel to show subscriber name
        self.right_panel.recent_subscriber = username
        self.right_panel.subscriber_display_timer = pygame.time.get_ticks() + 15000  # Show for 15 seconds
        
        achievement = Achievement(
            "Achievement Get!",
            f"{username} subscribed!",
            50, 50
        )
        self.achievements.append(achievement)
        
    def add_like_achievement(self, username=None):
        """Add achievement popup for new like - NO SOUND"""
        if username is None:
            username = f"Player#{random.randint(1000, 9999)}"
        
        # Don't play achievement sound for likes - just show notification
        achievement = Achievement(
            "Achievement Get!",
            f"{username} liked the stream!",
            50, 120,
            play_sound=False  # No sound for likes
        )
        self.achievements.append(achievement)
        
    def update(self):
        current_time = pygame.time.get_ticks()
        
        # Only update every 100ms to reduce lag
        if current_time - self.last_update < self.update_interval:
            return
            
        self.last_update = current_time
        
        # Update notifications
        self.notifications = [n for n in self.notifications if n.update()]
        
        # Update achievements  
        self.achievements = [a for a in self.achievements if a.update()]
        
        # Update right panel
        self.right_panel.update()
        
    def draw(self, surface, camera, screen_width, screen_height):
        # Draw notifications (relative to camera)
        for notification in self.notifications:
            screen_x = notification.x - camera.x
            screen_y = notification.y - camera.y
            
            # Only draw if on screen
            if -100 < screen_x < screen_width + 100 and -100 < screen_y < screen_height + 100:
                temp_notification = CommandNotification(notification.username, notification.command, screen_x, screen_y)
                temp_notification.timer = notification.timer
                temp_notification.draw(surface)
        
        # Draw achievements (fixed position on screen)
        for achievement in self.achievements:
            achievement.draw(surface)
                
        # Draw right panel
        self.right_panel.draw(surface, screen_width, screen_height)

# Global instance
notification_manager = NotificationManager()
