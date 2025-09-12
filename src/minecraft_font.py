import pygame
import os
from pathlib import Path

class MinecraftFont:
    def __init__(self):
        # Try to load a Minecraft-style font, fallback to default
        self.font_size = 24
        self.small_font_size = 18
        self.tiny_font_size = 10  # Add tiny font size - even smaller
        self.large_font_size = 32

        self.font = None
        self.small_font = None
        self.tiny_font = None  # Add tiny font
        self.large_font = None
        self._initialized = False

    def _initialize_fonts(self):
        """Initialize fonts lazily when first needed"""
        if self._initialized:
            return

        # Ensure pygame.font is initialized
        if not pygame.get_init():
            pygame.init()
        elif not pygame.font.get_init():
            pygame.font.init()

        # Try to find a suitable font
        minecraft_fonts = [
            "Minecraft.ttf",
            "MinecraftRegular.ttf", 
            "minecraft.ttf"
        ]

        # Check if any Minecraft fonts exist in assets
        assets_dir = Path(__file__).parent / "assets"
        for font_name in minecraft_fonts:
            font_path = assets_dir / font_name
            if font_path.exists():
                try:
                    self.font = pygame.font.Font(str(font_path), self.font_size)
                    self.small_font = pygame.font.Font(str(font_path), self.small_font_size)
                    self.tiny_font = pygame.font.Font(str(font_path), self.tiny_font_size)
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
                        self.tiny_font = pygame.font.SysFont(font_name, self.tiny_font_size)
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
            self.tiny_font = pygame.font.Font(None, self.tiny_font_size)
            self.large_font = pygame.font.Font(None, self.large_font_size)

        self._initialized = True

    def render_with_shadow(self, text, color, shadow_color, size="normal"):
        """Render text with shadow effect"""
        if size == "tiny":
            font_size = 8
        elif size == "small":
            font_size = 12
        elif size == "large":
            font_size = 24
        else:
            font_size = 16

        # Initialize font if not already done
        if self.font is None or (size == "tiny" and self.tiny_font is None) or (size == "small" and self.small_font is None) or (size == "large" and self.large_font is None):
             self._initialize_fonts()

        # Select the appropriate font object based on size
        font_to_use = None
        if size == "tiny":
            font_to_use = self.tiny_font  # Use proper tiny font
        elif size == "small":
            font_to_use = self.small_font
        elif size == "large":
            font_to_use = self.large_font
        else:
            font_to_use = self.font

        # Fallback if font_to_use is still None
        if font_to_use is None:
            font_to_use = pygame.font.Font(None, font_size)


        # Render shadow
        shadow_surface = font_to_use.render(text, True, shadow_color)
        # Render main text
        text_surface = font_to_use.render(text, True, color)

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