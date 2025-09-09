#!/usr/bin/env python3
"""
Minimal test for the new digging game core systems.
Tests character movement, world generation, and digging mechanics.
"""

import pygame
import sys
from pathlib import Path

# Add src directory to path so we can import our modules
sys.path.append(str(Path(__file__).parent / "src"))

from character import Character
from world import World
from camera import Camera
from sound import SoundManager
from constants import BLOCK_SIZE, INTERNAL_WIDTH, INTERNAL_HEIGHT, FRAMERATE

def create_simple_texture(color, size=(64, 64)):
    """Create a simple colored rectangle as a texture"""
    surface = pygame.Surface(size)
    surface.fill(color)
    return surface

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

def main():
    print("🎮 Testing Digging Game Core Systems...")
    
    # Initialize pygame
    pygame.init()
    screen = pygame.display.set_mode((800, 600))
    pygame.display.set_caption("Digging Game Core Test")
    clock = pygame.time.Clock()
    
    # Initialize systems
    sound_manager = SoundManager()
    camera = Camera()
    world = World(width=20)  # Smaller world for testing
    
    # Create character with simple texture
    character_texture = create_simple_texture((255, 100, 100), (32, 32))  # Red square
    character = Character(400, 0, character_texture, sound_manager)
    character.camera_ref = camera
    
    print(f"✅ Character created at position ({character.x}, {character.y})")
    print(f"✅ World generated with {len([b for row in world.blocks.values() for b in row.values() if b])} blocks")
    
    # Test controls
    print("\n🎮 Controls:")
    print("  Arrow Keys: Move left/right")
    print("  Space: Change dig speed (fast/normal/slow)")
    print("  ESC: Quit")
    print("\n🎯 The character will automatically dig downward!")
    
    running = True
    while running:
        # Handle events
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False
                elif event.key == pygame.K_LEFT:
                    character.move_horizontal(-1, 1)
                elif event.key == pygame.K_RIGHT:
                    character.move_horizontal(1, 1)
                elif event.key == pygame.K_SPACE:
                    # Cycle dig speed
                    speeds = ["fast", "normal", "slow"]
                    current_index = speeds.index(character.dig_speed)
                    new_speed = speeds[(current_index + 1) % len(speeds)]
                    character.set_dig_speed(new_speed)
                    print(f"⚡ Dig speed changed to: {new_speed}")
        
        # Update systems
        world.ensure_generated_to_depth(character.grid_y + 10)
        character.update(world)
        camera.update(character.y)
        
        # Render
        screen.fill((135, 206, 235))  # Sky blue background
        
        # Draw world blocks in visible area
        visible_range = 15  # Blocks around character
        start_x = character.grid_x - visible_range
        end_x = character.grid_x + visible_range
        start_y = max(0, character.grid_y - 5)
        end_y = character.grid_y + 15
        
        for x in range(start_x, end_x):
            for y in range(start_y, end_y):
                block_type = world.get_block_at(x, y)
                if block_type:
                    # Calculate screen position
                    screen_x = (x * BLOCK_SIZE) - camera.offset_x + 400
                    screen_y = (y * BLOCK_SIZE) - camera.offset_y + 100
                    
                    # Draw block
                    color = get_block_color(block_type)
                    pygame.draw.rect(screen, color, 
                                   (screen_x, screen_y, BLOCK_SIZE, BLOCK_SIZE))
                    
                    # Draw outline for rocks
                    if "rock" in block_type:
                        pygame.draw.rect(screen, (0, 0, 0), 
                                       (screen_x, screen_y, BLOCK_SIZE, BLOCK_SIZE), 2)
                
                # Draw gems
                gem_type = world.get_gem_at(x, y)
                if gem_type:
                    screen_x = (x * BLOCK_SIZE) - camera.offset_x + 400
                    screen_y = (y * BLOCK_SIZE) - camera.offset_y + 100
                    
                    # Draw gem as a small circle
                    gem_color = get_gem_color(gem_type)
                    center_x = screen_x + BLOCK_SIZE // 2
                    center_y = screen_y + BLOCK_SIZE // 2
                    pygame.draw.circle(screen, gem_color, (center_x, center_y), 8)
                    pygame.draw.circle(screen, (255, 255, 255), (center_x, center_y), 8, 2)
        
        # Draw character
        character_screen_x = character.x - camera.offset_x + 400
        character_screen_y = character.y - camera.offset_y + 100
        screen.blit(character.texture, (character_screen_x, character_screen_y))
        
        # Draw dig progress if digging
        if character.is_digging:
            bar_width = 60
            bar_height = 6
            bar_x = character_screen_x + (32 - bar_width) // 2
            bar_y = character_screen_y - 15
            
            # Background
            pygame.draw.rect(screen, (100, 100, 100), (bar_x, bar_y, bar_width, bar_height))
            
            # Progress
            progress_width = int(bar_width * character.dig_progress)
            progress_color = (255, 255, 0) if character.dig_progress < 0.8 else (0, 255, 0)
            pygame.draw.rect(screen, progress_color, (bar_x, bar_y, progress_width, bar_height))
        
        # Draw UI info
        font = pygame.font.Font(None, 24)
        info_lines = [
            f"Position: ({character.grid_x}, {character.grid_y})",
            f"Dig Speed: {character.dig_speed}",
            f"Tool Level: {character.tool_level}",
            f"Efficiency: {character.tool_efficiency:.2f}x",
            f"Digging: {'Yes' if character.is_digging else 'No'}",
        ]
        
        for i, line in enumerate(info_lines):
            text = font.render(line, True, (255, 255, 255))
            screen.blit(text, (10, 10 + i * 25))
        
        pygame.display.flip()
        clock.tick(FRAMERATE)
    
    pygame.quit()
    print("✅ Core systems test completed!")

if __name__ == "__main__":
    main()