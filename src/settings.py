"""
Simplified settings manager without UI panel or performance monitoring
"""

import json
from pathlib import Path

class SettingsManager:
    def __init__(self):
        self.settings_file = Path("game_settings.json")
        self.default_settings = {
            "performance_mode": False,
            "auto_tnt_spawn": True,
            "auto_pickaxe_change": True,
            "auto_size_change": True,
            "auto_speed_change": True,
            "show_fps": False,
            "vsync": True,
            "target_fps": 30,
            "reduced_effects": False,
            "max_particles": 100,
            "show_damage_numbers": True,
            "download_profile_pictures": False,  # Disabled due to SSL errors
            "show_command_notifications": True,
            "combo_display": False,  # Disabled for performance
            "sound_enabled": True,
            "particle_effects": True,
            "screen_shake": False,
            "explosion_particles": True,
            "show_usernames_on_tnt": True,
            "show_profile_pictures": False
        }
        self.settings = self.load_settings()
        self.show_settings = False  # Always false now
        
    def load_settings(self):
        if self.settings_file.exists():
            try:
                with open(self.settings_file, 'r') as f:
                    loaded = json.load(f)
                    # Merge with defaults
                    settings = self.default_settings.copy()
                    settings.update(loaded)
                    return settings
            except Exception as e:
                # print(f"Error loading settings: {e}")  # Removed for performance
                pass
        return self.default_settings.copy()
    
    def save_settings(self):
        try:
            with open(self.settings_file, 'w') as f:
                json.dump(self.settings, f, indent=2)
        except Exception as e:
            # print(f"Error saving settings: {e}")  # Removed for performance
            pass
    
    def get_setting(self, key):
        return self.settings.get(key, self.default_settings.get(key, False))
    
    def set_setting(self, key, value):
        self.settings[key] = value
        self.save_settings()
    
    def handle_input(self, event):
        # No settings panel anymore, so this does nothing
        return False
    
    def draw(self, screen):
        # No settings panel to draw
        pass
    
    def update(self, fps):
        # No auto-performance monitoring
        pass
