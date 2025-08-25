
import pygame
import json
import os
from pathlib import Path

class SettingsManager:
    def __init__(self):
        self.settings_file = Path("game_settings.json")
        self.default_settings = {
            "weather_effects": True,
            "particle_effects": True,
            "screen_shake": True,
            "sound_enabled": True,
            "performance_mode": False,
            "auto_performance": True,
            "auto_quality": True,
            "auto_weather": True,
            "auto_events": True,
            "auto_tnt_spawn": True,
            "auto_pickaxe_change": True,
            "auto_size_change": True,
            "auto_speed_change": True,
            "max_particles": 100,
            "explosion_particles": True,
            "rainbow_trails": True,
            "shield_glow": True,
            "combo_display": True,
            "milestone_celebrations": True,
            "weather_rain": True,
            "weather_snow": True,
            "weather_lightning": True,
            "low_quality_textures": False,
            "reduced_effects": False,
            "target_fps": 60,
            "show_profile_pictures": True,
            "show_usernames_on_tnt": True,
            "show_command_notifications": True,
            "download_profile_pictures": True,
            "pixelated_profile_style": True,
            "auto_combo_multiplier": True,
            "auto_difficulty_scaling": True,
            "dynamic_music": False,
            "adaptive_ui_scale": True
        }
        self.settings = self.load_settings()
        self.show_settings = False
        self.font = pygame.font.Font(None, 32)
        self.title_font = pygame.font.Font(None, 48)
        self.selected_option = 0
        self.scroll_offset = 0
        self.performance_monitor = PerformanceMonitor()
        
    def load_settings(self):
        if self.settings_file.exists():
            try:
                with open(self.settings_file, 'r') as f:
                    loaded = json.load(f)
                    # Merge with defaults to ensure all keys exist
                    settings = self.default_settings.copy()
                    settings.update(loaded)
                    return settings
            except Exception as e:
                print(f"Error loading settings: {e}")
        return self.default_settings.copy()
    
    def save_settings(self):
        try:
            with open(self.settings_file, 'w') as f:
                json.dump(self.settings, f, indent=2)
        except Exception as e:
            print(f"Error saving settings: {e}")
    
    def toggle_setting(self, key):
        if key in self.settings and isinstance(self.settings[key], bool):
            self.settings[key] = not self.settings[key]
            self.save_settings()
    
    def get_setting(self, key):
        return self.settings.get(key, self.default_settings.get(key, False))
    
    def handle_input(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                self.show_settings = not self.show_settings
                return True
            
            if self.show_settings:
                settings_keys = list(self.settings.keys())
                if event.key == pygame.K_UP:
                    self.selected_option = (self.selected_option - 1) % len(settings_keys)
                elif event.key == pygame.K_DOWN:
                    self.selected_option = (self.selected_option + 1) % len(settings_keys)
                elif event.key == pygame.K_RETURN or event.key == pygame.K_SPACE:
                    selected_key = settings_keys[self.selected_option]
                    self.toggle_setting(selected_key)
                return True
        return False
    
    def draw(self, screen):
        if not self.show_settings:
            return
            
        # Semi-transparent overlay
        overlay = pygame.Surface(screen.get_size())
        overlay.set_alpha(180)
        overlay.fill((0, 0, 0))
        screen.blit(overlay, (0, 0))
        
        # Settings panel - scale to screen size
        panel_width = min(800, int(screen.get_width() * 0.9))
        panel_height = min(600, int(screen.get_height() * 0.8))
        panel_x = (screen.get_width() - panel_width) // 2
        panel_y = (screen.get_height() - panel_height) // 2
        
        panel_rect = pygame.Rect(panel_x, panel_y, panel_width, panel_height)
        pygame.draw.rect(screen, (40, 40, 40), panel_rect)
        pygame.draw.rect(screen, (100, 100, 100), panel_rect, 3)
        
        # Title
        title_text = self.title_font.render("GAME SETTINGS", True, (255, 255, 255))
        title_x = panel_x + (panel_width - title_text.get_width()) // 2
        screen.blit(title_text, (title_x, panel_y + 20))
        
        # Instructions
        instruction_text = self.font.render("ESC: Close | ↑↓: Navigate | ENTER/SPACE: Toggle", True, (180, 180, 180))
        instruction_x = panel_x + (panel_width - instruction_text.get_width()) // 2
        screen.blit(instruction_text, (instruction_x, panel_y + 70))
        
        # Settings list with scrolling
        y_offset = panel_y + 120
        settings_keys = list(self.settings.keys())
        
        # Calculate visible area
        visible_height = panel_height - 170  # Leave room for title and instructions
        line_height = 30
        max_visible_items = visible_height // line_height
        
        # Handle scrolling
        if self.selected_option >= max_visible_items:
            self.scroll_offset = self.selected_option - max_visible_items + 1
        elif self.selected_option < self.scroll_offset:
            self.scroll_offset = self.selected_option
            
        # Adjust scroll offset to prevent over-scrolling
        max_scroll = max(0, len(settings_keys) - max_visible_items)
        self.scroll_offset = max(0, min(self.scroll_offset, max_scroll))
        
        # Draw visible settings
        for i in range(len(settings_keys)):
            if i < self.scroll_offset or i >= self.scroll_offset + max_visible_items:
                continue
                
            key = settings_keys[i]
            draw_y = y_offset + (i - self.scroll_offset) * line_height
            
            color = (255, 255, 0) if i == self.selected_option else (255, 255, 255)
            
            # Format setting name
            display_name = key.replace('_', ' ').title()
            # Scale font size based on panel width
            font_size = max(16, min(24, panel_width // 35))
            scaled_font = pygame.font.Font(None, font_size)
            setting_text = scaled_font.render(display_name, True, color)
            
            # Setting value
            value = "ON" if self.settings[key] else "OFF"
            if isinstance(self.settings[key], (int, float)):
                value = str(self.settings[key])
            value_color = (0, 255, 0) if self.settings[key] else (255, 0, 0)
            if isinstance(self.settings[key], (int, float)):
                value_color = (255, 255, 255)
            value_text = scaled_font.render(value, True, value_color)
            
            # Draw setting if within panel
            if draw_y < panel_y + panel_height - 50:
                screen.blit(setting_text, (panel_x + 20, draw_y))
                screen.blit(value_text, (panel_x + panel_width - 100, draw_y))
        
        # Draw scroll indicators
        if self.scroll_offset > 0:
            pygame.draw.polygon(screen, (255, 255, 255), [
                (panel_x + panel_width - 30, panel_y + 130),
                (panel_x + panel_width - 20, panel_y + 120),
                (panel_x + panel_width - 10, panel_y + 130)
            ])
        if self.scroll_offset < max_scroll:
            pygame.draw.polygon(screen, (255, 255, 255), [
                (panel_x + panel_width - 30, panel_y + panel_height - 70),
                (panel_x + panel_width - 20, panel_y + panel_height - 60),
                (panel_x + panel_width - 10, panel_y + panel_height - 70)
            ])
    
    def update(self, fps):
        self.performance_monitor.update(fps)
        if self.get_setting("auto_performance"):
            should_enable = self.performance_monitor.should_enable_performance_mode()
            if should_enable != self.get_setting("performance_mode"):
                self.settings["performance_mode"] = should_enable
                print(f"Auto performance mode: {'ENABLED' if should_enable else 'DISABLED'}")
        
        # Auto quality adjustment
        if self.get_setting("auto_quality"):
            avg_fps = self.performance_monitor.get_average_fps()
            if avg_fps < 30 and not self.get_setting("reduced_effects"):
                self.settings["reduced_effects"] = True
                self.settings["max_particles"] = 50
                print("Auto quality: Reduced effects enabled due to low FPS")
            elif avg_fps > 50 and self.get_setting("reduced_effects"):
                self.settings["reduced_effects"] = False
                self.settings["max_particles"] = 100
                print("Auto quality: Full effects restored")

class PerformanceMonitor:
    def __init__(self):
        self.fps_history = []
        self.max_history = 60  # Track last 60 frames
        self.low_fps_threshold = 45
        self.good_fps_threshold = 55
        
    def update(self, current_fps):
        self.fps_history.append(current_fps)
        if len(self.fps_history) > self.max_history:
            self.fps_history.pop(0)
    
    def get_average_fps(self):
        if not self.fps_history:
            return 60
        return sum(self.fps_history) / len(self.fps_history)
    
    def should_enable_performance_mode(self):
        if len(self.fps_history) < 30:  # Need enough data
            return False
        avg_fps = self.get_average_fps()
        return avg_fps < self.low_fps_threshold
    
    def should_disable_performance_mode(self):
        if len(self.fps_history) < 30:
            return False
        avg_fps = self.get_average_fps()
        return avg_fps > self.good_fps_threshold
