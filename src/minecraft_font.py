
import pygame
import os
from pathlib import Path

class MinecraftFont:
    def __init__(self):
        # Try to load a Minecraft-style font, fallback to default
        self.font_size = 24
        self.small_font_size = 18
        self.large_font_size = 32
        
        # Try to find a suitable font
        minecraft_fonts = [
            "Minecraft.ttf",
            "MinecraftRegular.ttf", 
            "minecraft.ttf"
        ]
        
        self.font = None
        self.small_font = None
        self.large_font = None
        
        # Check if any Minecraft fonts exist in assets
        assets_dir = Path(__file__).parent / "assets"
        for font_name in minecraft_fonts:
            font_path = assets_dir / font_name
            if font_path.exists():
                try:
                    self.font = pygame.font.Font(str(font_path), self.font_size)
                    self.small_font = pygame.font.Font(str(font_path), self.small_font_size)
                    self.large_font = pygame.font.Font(str(font_path), self.large_font_size)
                    break
                except:
                    continue
        
        # Fallback to system fonts that look Minecraft-ish
        if self.font is None:
            try:
                # Try common pixelated/monospace fonts
                pixel_fonts = ["Courier New", "Consolas", "Monaco", "monospace"]
                for font_name in pixel_fonts:
                    try:
                        self.font = pygame.font.SysFont(font_name, self.font_size)
                        self.small_font = pygame.font.SysFont(font_name, self.small_font_size)
                        self.large_font = pygame.font.SysFont(font_name, self.large_font_size)
                        break
                    except:
                        continue
            except:
                pass
        
        # Final fallback
        if self.font is None:
            self.font = pygame.font.Font(None, self.font_size)
            self.small_font = pygame.font.Font(None, self.small_font_size)
            self.large_font = pygame.font.Font(None, self.large_font_size)
    
    def render_with_shadow(self, text, color=(255, 255, 255), shadow_color=(0, 0, 0), size="normal"):
        """Render text with shadow for Minecraft-style appearance"""
        font = self.font
        if size == "small":
            font = self.small_font
        elif size == "large":
            font = self.large_font
            
        # Render shadow
        shadow_surface = font.render(text, True, shadow_color)
        # Render main text
        text_surface = font.render(text, True, color)
        
        # Create combined surface
        width = text_surface.get_width() + 2
        height = text_surface.get_height() + 2
        combined = pygame.Surface((width, height), pygame.SRCALPHA)
        
        # Blit shadow offset by 2 pixels
        combined.blit(shadow_surface, (2, 2))
        # Blit main text
        combined.blit(text_surface, (0, 0))
        
        return combined

# Global instance
minecraft_font = MinecraftFont()
