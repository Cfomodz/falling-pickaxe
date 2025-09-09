import pygame
from constants import BLOCK_SIZE, CHUNK_HEIGHT

def render_text_with_outline(text, font, text_color, outline_color, outline_width=2):
    # Render the text in the main color.
    text_surface = font.render(text, True, text_color)
    # Create a new surface larger than the text surface to hold the outline.
    w, h = text_surface.get_size()
    outline_surface = pygame.Surface((w + 2*outline_width, h + 2*outline_width), pygame.SRCALPHA)
    
    # Blit the text multiple times in the outline color, offset by outline_width in every direction.
    for dx in range(-outline_width, outline_width+1):
        for dy in range(-outline_width, outline_width+1):
            # Only draw outline if offset is non-zero (avoids overdraw, though it's not a big deal)
            if dx != 0 or dy != 0:
                pos = (dx + outline_width, dy + outline_width)
                outline_surface.blit(font.render(text, True, outline_color), pos)
    
    # Blit the main text in the center.
    outline_surface.blit(text_surface, (outline_width, outline_width))
    return outline_surface

class Hud:
    def __init__(self, texture_atlas, atlas_items, position=(32, 32)):
        """
        :param texture_atlas: The atlas surface containing the item icons.
        :param atlas_items: A dict with keys under "item" for each ore.
        :param position: Top-left position where the HUD will be drawn.
        """
        self.texture_atlas = texture_atlas
        self.atlas_items = atlas_items

        # Initialize ore amounts to 0.
        self.amounts = {
            "coal": 0,
            "iron_ingot": 0,
            "copper_ingot": 0,
            "gold_ingot": 0,
            "redstone": 0,
            "lapis_lazuli": 0,
            "diamond": 0,
            "emerald": 0,
        }
        
        # Combo system
        self.combo_count = 0
        self.combo_timer = 0
        self.combo_multiplier = 1.0

        self.position = position
        self.icon_size = (64, 64)  # Size to draw each icon
        self.spacing = 15  # Space between items

        # Initialize a font (using the default font and size 24)
        self.font = pygame.font.Font(None, 64)
        
    def get_gem_display_color(self, gem_type):
        """Get color for gem display in HUD"""
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
        return colors.get(gem_type, (255, 255, 255))
        
    def draw_tool_durability_bar(self, screen, character):
        """Draw tool durability bar across the top of the screen"""
        tool_name, durability_percent = character.get_current_tool_info()
        
        # Bar dimensions
        bar_width = screen.get_width() - 100  # Leave 50px margin on each side
        bar_height = 20
        bar_x = 50
        bar_y = 10
        
        # Background bar (dark gray)
        pygame.draw.rect(screen, (64, 64, 64), (bar_x, bar_y, bar_width, bar_height))
        
        # Durability fill (changes color based on percentage)
        fill_width = int((durability_percent / 100.0) * bar_width)
        
        if durability_percent > 75:
            fill_color = (0, 255, 0)  # Green
        elif durability_percent > 50:
            fill_color = (255, 255, 0)  # Yellow
        elif durability_percent > 25:
            fill_color = (255, 165, 0)  # Orange
        else:
            fill_color = (255, 0, 0)  # Red
            
        if fill_width > 0:
            pygame.draw.rect(screen, fill_color, (bar_x, bar_y, fill_width, bar_height))
        
        # Border
        pygame.draw.rect(screen, (255, 255, 255), (bar_x, bar_y, bar_width, bar_height), 2)
        
        # Tool name and percentage text
        tool_display = tool_name.replace("_", " ").title()
        text = f"{tool_display}: {durability_percent:.1f}%"
        text_surface = render_text_with_outline(text, self.font, (255, 255, 255), (0, 0, 0), outline_width=2)
        
        # Center text on bar
        text_x = bar_x + (bar_width - text_surface.get_width()) // 2
        text_y = bar_y + (bar_height - text_surface.get_height()) // 2
        screen.blit(text_surface, (text_x, text_y))

    def update_amounts(self, new_amounts):
        """
        Update the ore amounts.
        :param new_amounts: Dict with ore names as keys and integer amounts as values.
        """
        self.amounts.update(new_amounts)
        
    def add_combo(self):
        """Add to combo counter and reset timer."""
        self.combo_count += 1
        self.combo_timer = pygame.time.get_ticks() + 3000  # 3 second combo window
        self.combo_multiplier = min(5.0, 1.0 + (self.combo_count * 0.1))  # Cap at 5x
        
    def update_combo(self):
        """Update combo system - reset if timer expires."""
        if pygame.time.get_ticks() > self.combo_timer and self.combo_count > 0:
            self.combo_count = 0
            self.combo_multiplier = 1.0

    def draw(self, screen, character_y, fast_slow_active, fast_slow, settings_manager=None, character=None):
        """
        Draws the HUD: gem inventory, tool info, durability bar, and other indicators.
        """
        x, y = self.position
        
        # Draw tool durability bar at top of screen
        if character:
            self.draw_tool_durability_bar(screen, character)

        # Draw gem inventory if character is provided
        if character:
            gem_display_order = ["diamond_gem", "corundum_gem", "topaz_gem", "quartz_gem", "orthoclase_gem", 
                               "apatite_gem", "fluorite_gem", "calcite_gem", "gypsum_gem", "talc_gem"]
            
            for gem_type in gem_display_order:
                amount = character.gem_inventory[gem_type]
                if amount > 0:  # Only show gems we have
                    # Create a simple colored circle for gem icon (temporary)
                    gem_color = self.get_gem_display_color(gem_type)
                    pygame.draw.circle(screen, gem_color, (x + 32, y + 32), 28)
                    pygame.draw.circle(screen, (255, 255, 255), (x + 32, y + 32), 28, 3)
                    
                    # Render the amount text
                    text = str(amount)
                    text_surface = render_text_with_outline(text, self.font, (255, 255, 255), (0, 0, 0), outline_width=2)
                    
                    # Position text to the right of the icon
                    text_x = x + self.icon_size[0] + self.spacing
                    text_y = y + (self.icon_size[1] - text_surface.get_height()) // 2 + 3
                    screen.blit(text_surface, (text_x, text_y))

                    # Move to the next line
                    y += self.icon_size[1] + self.spacing
        
        else:
            # Fallback: show old ore amounts if no character provided
            for ore, amount in self.amounts.items():
                if ore in self.atlas_items["item"]:
                    icon_rect = pygame.Rect(self.atlas_items["item"][ore])
                    icon = self.texture_atlas.subsurface(icon_rect)
                    icon = pygame.transform.scale(icon, self.icon_size)
                    screen.blit(icon, (x, y))
                else:
                    continue

                text = str(amount)
                text_surface = render_text_with_outline(text, self.font, (255, 255, 255), (0, 0, 0), outline_width=2)
                
                text_x = x + self.icon_size[0] + self.spacing
                text_y = y + (self.icon_size[1] - text_surface.get_height()) // 2 + 3
                screen.blit(text_surface, (text_x, text_y))

                y += self.icon_size[1] + self.spacing

        # Draw the character depth indicator with outlined text
        depth_text = f"Depth: {int(character_y // BLOCK_SIZE)}" if character else f"Y: {-int(character_y // BLOCK_SIZE)}"
        depth_surface = render_text_with_outline(depth_text, self.font, (255, 255, 255), (0, 0, 0), outline_width=2)
        depth_x = x + self.spacing
        depth_y = y + self.spacing
        screen.blit(depth_surface, (depth_x, depth_y))
        
        # Draw tool level and efficiency if character provided
        if character:
            tool_text = f"Tool: Lvl{character.tool_level} ({character.tool_efficiency:.1f}x)"
            tool_surface = render_text_with_outline(tool_text, self.font, (255, 255, 255), (0, 0, 0), outline_width=2)
            tool_x = x + self.spacing  
            tool_y = depth_y + depth_surface.get_height() + self.spacing
            screen.blit(tool_surface, (tool_x, tool_y))
            y = tool_y + tool_surface.get_height() + self.spacing
        else:
            y = depth_y + depth_surface.get_height() + self.spacing

        # Draw the fast/slow indicator with outlined text
        if fast_slow_active:
            fast_slow_text = f"{fast_slow}"
        else:
            fast_slow_text = "Fast"
        fast_slow_surface = render_text_with_outline(fast_slow_text, self.font, (255, 255, 255), (0, 0, 0), outline_width=2)
        fast_slow_x = x + self.spacing
        fast_slow_y = y + 2 * self.spacing + fast_slow_surface.get_height()
        screen.blit(fast_slow_surface, (fast_slow_x, fast_slow_y))
        
        # Update and draw combo counter
        self.update_combo()
        show_combo = settings_manager is None or settings_manager.get_setting("combo_display")
        if self.combo_count > 0 and show_combo:
            combo_text = f"COMBO: {self.combo_count}x ({self.combo_multiplier:.1f}x)"
            combo_color = (255, 255, 0) if self.combo_count >= 10 else (255, 255, 255)
            combo_surface = render_text_with_outline(combo_text, self.font, combo_color, (0, 0, 0), outline_width=2)
            combo_x = x + self.spacing
            combo_y = fast_slow_y + 2 * self.spacing + combo_surface.get_height()
            screen.blit(combo_surface, (combo_x, combo_y))

            

