
import pygame
import requests
import os
from pathlib import Path
import hashlib
from minecraft_font import minecraft_font
import ssl

# Try to disable SSL warnings if urllib3 is available
try:
    import urllib3
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
except ImportError:
    pass  # urllib3 not available, that's okay

class ProfilePictureManager:
    def __init__(self):
        self.cache_dir = Path("profile_pictures_cache")
        self.cache_dir.mkdir(exist_ok=True)
        self.loaded_pictures = {}  # In-memory cache
        self.default_size = 32
        
    def get_cache_path(self, username):
        """Get the cache file path for a username"""
        # Create a safe filename from username
        safe_name = hashlib.md5(username.encode()).hexdigest()
        return self.cache_dir / f"{safe_name}.png"
    
    def download_profile_picture(self, username, url):
        """Download and cache a profile picture with SSL error handling"""
        try:
            # First try with SSL verification
            try:
                response = requests.get(url, timeout=5)
            except (requests.exceptions.SSLError, ssl.SSLError):
                # If SSL fails, try without verification (for development)
                # print(f"SSL error for {username}, trying without verification")
                response = requests.get(url, timeout=5, verify=False)
                
            if response.status_code == 200:
                cache_path = self.get_cache_path(username)
                with open(cache_path, 'wb') as f:
                    f.write(response.content)
                return True
        except Exception as e:
            # Silently fail - profile pictures are not critical
            # print(f"Failed to download profile picture for {username}: {e}")
            pass
        return False
    
    def load_profile_picture(self, username, size=None):
        """Load profile picture from cache or return default"""
        if size is None:
            size = self.default_size
            
        cache_key = f"{username}_{size}"
        
        if cache_key in self.loaded_pictures:
            return self.loaded_pictures[cache_key]
        
        cache_path = self.get_cache_path(username)
        
        if cache_path.exists():
            try:
                # Load and resize image
                image = pygame.image.load(cache_path)
                resized = pygame.transform.scale(image, (size, size))
                
                # Apply minecraft-style pixelation
                pixelated = self.pixelate_image(resized, 8)
                
                self.loaded_pictures[cache_key] = pixelated
                return pixelated
            except Exception as e:
                # Silently fail - use default avatar
                pass
        
        # Return default minecraft-style avatar
        return self.create_default_avatar(username, size)
    
    def pixelate_image(self, surface, pixel_size):
        """Apply minecraft-style pixelation to an image"""
        # Downscale
        small_size = (surface.get_width() // pixel_size, surface.get_height() // pixel_size)
        small_surface = pygame.transform.scale(surface, small_size)
        
        # Upscale back with nearest neighbor (no smoothing)
        original_size = (surface.get_width(), surface.get_height())
        pixelated = pygame.transform.scale(small_surface, original_size)
        
        return pixelated
    
    def create_default_avatar(self, username, size):
        """Create a default minecraft-style avatar based on username"""
        # Generate color based on username hash
        hash_val = hash(username) % 16777215  # Max RGB value
        r = (hash_val >> 16) & 255
        g = (hash_val >> 8) & 255 
        b = hash_val & 255
        
        # Create simple colored square with border
        surface = pygame.Surface((size, size))
        surface.fill((r, g, b))
        
        # Add border
        pygame.draw.rect(surface, (0, 0, 0), surface.get_rect(), 2)
        
        # Add initial letter
        if username:
            initial = username[0].upper()
            text_surface = minecraft_font.render_with_shadow(initial, (255, 255, 255), (0, 0, 0), "small")
            text_rect = text_surface.get_rect(center=(size//2, size//2))
            surface.blit(text_surface, text_rect)
        
        self.loaded_pictures[f"{username}_{size}"] = surface
        return surface

# Global instance
profile_picture_manager = ProfilePictureManager()
