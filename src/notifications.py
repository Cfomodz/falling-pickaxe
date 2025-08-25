
import pygame
import time
import random
from minecraft_font import minecraft_font

class Achievement:
    def __init__(self, title, description, x=None, y=None):
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
        
        # Play achievement sound
        try:
            from sound import SoundManager
            sound_manager = SoundManager()
            sound_manager.play_sound("achievement")
        except:
            pass
        
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
    def __init__(self, width=300):
        self.width = width
        self.top_players = TopPlayersTracker()
        self.commands = [
            "tnt", "fast", "slow", "big", "wood", "stone", 
            "iron", "gold", "diamond", "netherite", "rainbow", 
            "shield", "freeze"
        ]
        
    def update(self):
        self.top_players.update()
        
    def add_player_activity(self, username):
        self.top_players.add_activity(username)
        
    def draw(self, surface, screen_width, screen_height):
        panel_x = screen_width - self.width
        
        # Draw panel background
        panel_surface = pygame.Surface((self.width, screen_height))
        panel_surface.fill((64, 64, 64))
        panel_surface.set_alpha(200)
        surface.blit(panel_surface, (panel_x, 0))
        
        y_offset = 20
        
        # Draw Rewards section
        rewards_title = minecraft_font.render_with_shadow("REWARDS:", (255, 215, 0), (0, 0, 0), "normal")
        surface.blit(rewards_title, (panel_x + 10, y_offset))
        y_offset += rewards_title.get_height() + 10
        
        # Sub reward
        sub_reward = minecraft_font.render_with_shadow("Sub = 1 MEGA TNT", (255, 100, 100), (0, 0, 0), "small")
        surface.blit(sub_reward, (panel_x + 20, y_offset))
        y_offset += sub_reward.get_height() + 5
        
        # Like reward
        like_reward = minecraft_font.render_with_shadow("Like = 5 TNT", (100, 255, 100), (0, 0, 0), "small")
        surface.blit(like_reward, (panel_x + 20, y_offset))
        y_offset += like_reward.get_height() + 15
        
        # Draw Commands section
        commands_title = minecraft_font.render_with_shadow("Commands:", (255, 255, 255), (0, 0, 0), "normal")
        surface.blit(commands_title, (panel_x + 10, y_offset))
        y_offset += commands_title.get_height() + 10
        
        for command in self.commands:
            command_color = self.get_command_color(command)
            command_text = minecraft_font.render_with_shadow(f"• {command}", command_color, (0, 0, 0), "small")
            surface.blit(command_text, (panel_x + 20, y_offset))
            y_offset += command_text.get_height() + 5
            
        y_offset += 30
        
        # Draw Top Players section
        time_left = int(self.top_players.get_time_until_reset())
        minutes = time_left // 60
        seconds = time_left % 60
        
        players_title = minecraft_font.render_with_shadow(f"TOP PLAYERS ({minutes:02d}:{seconds:02d})", (255, 255, 0), (0, 0, 0), "normal")
        surface.blit(players_title, (panel_x + 10, y_offset))
        y_offset += players_title.get_height() + 10
        
        from settings import SettingsManager
        settings = SettingsManager()
        show_profile_pics = settings.get_setting("show_profile_pictures")
        
        top_players = self.top_players.get_top_players()
        for i, (username, activity) in enumerate(top_players):
            rank_color = self.get_rank_color(i)
            
            # Draw profile picture if enabled
            if show_profile_pics:
                from profile_picture_manager import profile_picture_manager
                profile_pic = profile_picture_manager.load_profile_picture(username, 24)
                surface.blit(profile_pic, (panel_x + 20, y_offset))
                text_x = panel_x + 50  # Offset for profile picture
            else:
                text_x = panel_x + 20
                
            player_text = minecraft_font.render_with_shadow(f"{i+1}. {username}: {activity}", rank_color, (0, 0, 0), "small")
            surface.blit(player_text, (text_x, y_offset))
            y_offset += max(player_text.get_height(), 24) + 5
            
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
        
        achievement = Achievement(
            "Achievement Get!",
            f"{username} subscribed!",
            50, 50
        )
        self.achievements.append(achievement)
        
    def add_like_achievement(self, username=None):
        """Add achievement popup for new like"""
        if username is None:
            username = f"Player#{random.randint(1000, 9999)}"
        
        achievement = Achievement(
            "Achievement Get!",
            f"{username} liked the stream!",
            50, 120
        )
        self.achievements.append(achievement)
        
    def update(self):
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
