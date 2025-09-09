import pygame
import random
from constants import BLOCK_SIZE

class Character:
    def __init__(self, x, y, texture, sound_manager):
        """
        Initialize the digging character with controlled movement.
        
        :param x: Starting x position (in pixels)
        :param y: Starting y position (in pixels) 
        :param texture: Character sprite texture
        :param sound_manager: Sound manager for digging sounds
        """
        self.texture = texture
        self.original_texture = texture.copy()
        self.sound_manager = sound_manager
        
        # Position (pixel coordinates)
        self.x = x
        self.y = y
        
        # Grid position (for world interaction)
        self.grid_x = int(x // BLOCK_SIZE)
        self.grid_y = int(y // BLOCK_SIZE)
        
        # Movement and digging
        self.dig_speed = "fast"  # "slow", "normal", "fast"
        self.dig_progress = 0.0  # Current dig progress (0.0 to 1.0)
        self.is_digging = False
        
        # Visual effects
        self.rainbow_mode = False
        self.rainbow_timer = 0
        self.shield_active = False
        self.shield_timer = 0
        self.freeze_active = False
        self.freeze_timer = 0
        self.dig_start_time = 0
        self.current_dig_time = 0  # How long current block takes to dig
        
        # Tool system
        self.tool_level = 1  # Starting with basic shovel
        self.tool_efficiency = 1.0  # Multiplier for dig speed
        
        # Tool upgrade queue system (highest rarity first)
        self.tool_upgrade_queue = []  # List of (gem_type, end_time) sorted by rarity
        self.current_tool_upgrade = None  # Current active upgrade: (gem_type, end_time)
        
        # Gem inventory system
        self.gem_inventory = {
            "talc_gem": 0,
            "gypsum_gem": 0, 
            "calcite_gem": 0,
            "fluorite_gem": 0,
            "apatite_gem": 0,
            "orthoclase_gem": 0,
            "quartz_gem": 0,
            "topaz_gem": 0,
            "corundum_gem": 0,
            "diamond_gem": 0
        }
        
        # Visual effects
        self.facing_direction = 1  # 1 for right, -1 for left
        self.animation_frame = 0
        self.dig_particles = []
        
        # Camera reference for screen shake
        self.camera_ref = None
        
    def set_dig_speed(self, speed):
        """Set the digging speed: 'slow', 'normal', or 'fast'"""
        self.dig_speed = speed
        
    def move_horizontal(self, direction, spaces=1):
        """
        Move character horizontally by specified number of grid spaces.
        
        :param direction: -1 for left, 1 for right
        :param spaces: Number of grid spaces to move (1-3)
        """
        self.facing_direction = direction
        new_grid_x = self.grid_x + (direction * spaces)
        
        # Update position
        self.grid_x = new_grid_x
        self.x = self.grid_x * BLOCK_SIZE
        
        print(f"Character moved {direction} by {spaces} spaces to grid position ({self.grid_x}, {self.grid_y})")
        
    def start_digging(self, world):
        """
        Start digging at the current position.
        
        :param world: World object to check what we're digging
        :return: True if digging started, False if blocked
        """
        if self.is_digging:
            return False
            
        # Check what's below us
        target_y = self.grid_y + 1  # Dig downward
        block_type = world.get_block_at(self.grid_x, target_y)
        
        if block_type is None:
            # Nothing to dig, move down immediately
            self.move_down()
            return False
            
        # Calculate dig time based on block type and tool efficiency
        base_dig_time = self.get_base_dig_time(block_type)
        speed_multiplier = self.get_speed_multiplier()
        
        self.current_dig_time = base_dig_time / (self.tool_efficiency * speed_multiplier)
        self.dig_start_time = pygame.time.get_ticks()
        self.dig_progress = 0.0
        self.is_digging = True
        
        print(f"Started digging {block_type} (will take {self.current_dig_time:.1f}s)")
        return True
        
    def get_base_dig_time(self, block_type):
        """Get base dig time for different block types (in seconds)"""
        # Dirt layers (1-5 seconds based on difficulty)
        dirt_times = {
            "dirt_light": 1.0,    # Level 1
            "dirt_medium": 2.0,   # Level 2  
            "dirt_dark": 3.0,     # Level 3
            "clay": 4.0,          # Level 4
            "bedrock": 5.0,       # Level 5
        }
        
        # Rocks (4x harder than same-level dirt)
        rock_times = {
            "talc_rock": 4.0,       # Mohs 1
            "gypsum_rock": 8.0,     # Mohs 2
            "calcite_rock": 12.0,   # Mohs 3
            "fluorite_rock": 16.0,  # Mohs 4
            "apatite_rock": 20.0,   # Mohs 5
            "orthoclase_rock": 24.0, # Mohs 6
            "quartz_rock": 28.0,    # Mohs 7
            "topaz_rock": 32.0,     # Mohs 8
            "corundum_rock": 36.0,  # Mohs 9
            "diamond_rock": 40.0,   # Mohs 10
        }
        
        if block_type in dirt_times:
            return dirt_times[block_type]
        elif block_type in rock_times:
            return rock_times[block_type]
        else:
            return 1.0  # Default
            
    def get_speed_multiplier(self):
        """Get speed multiplier based on current dig speed setting"""
        if self.dig_speed == "slow":
            return 0.5
        elif self.dig_speed == "normal":
            return 1.0
        elif self.dig_speed == "fast":
            return 2.0
        return 1.0
        
    def update_digging(self, world):
        """
        Update digging progress and complete dig when finished.
        
        :param world: World object to modify when digging completes
        """
        if not self.is_digging:
            return
            
        # Skip digging if frozen
        if self.freeze_active:
            return
            
        current_time = pygame.time.get_ticks()
        elapsed_time = (current_time - self.dig_start_time) / 1000.0  # Convert to seconds
        
        self.dig_progress = min(1.0, elapsed_time / self.current_dig_time)
        
        # Check if digging is complete
        if self.dig_progress >= 1.0:
            self.complete_dig(world)
            
    def complete_dig(self, world):
        """Complete the current dig and move character down"""
        target_y = self.grid_y + 1
        block_type = world.get_block_at(self.grid_x, target_y)
        
        # Remove the block from world
        world.remove_block_at(self.grid_x, target_y)
        
        # Handle rewards (gems from rocks, etc.)
        self.handle_dig_rewards(block_type)
        
        # Play dig sound
        self.play_dig_sound(block_type)
        
        # Move character down
        self.move_down()
        
        # Reset digging state
        self.is_digging = False
        self.dig_progress = 0.0
        
        # Camera shake for rocks
        if "rock" in block_type and self.camera_ref:
            self.camera_ref.shake(200, 5)  # Duration 200ms, intensity 5
            
    def move_down(self):
        """Move character down one grid space"""
        self.grid_y += 1
        self.y = self.grid_y * BLOCK_SIZE
        
    def handle_dig_rewards(self, block_type):
        """Handle rewards from digging different block types"""
        print(f"Dug through {block_type}")
        
        # Check for gems from rocks
        if "rock" in block_type:
            gem_type = self.get_gem_from_rock(block_type)
            if gem_type:
                self.collect_gem(gem_type)
                
    def get_gem_from_rock(self, rock_type):
        """Get corresponding gem type from rock type"""
        rock_to_gem = {
            "talc_rock": "talc_gem",
            "gypsum_rock": "gypsum_gem", 
            "calcite_rock": "calcite_gem",
            "fluorite_rock": "fluorite_gem",
            "apatite_rock": "apatite_gem",
            "orthoclase_rock": "orthoclase_gem",
            "quartz_rock": "quartz_gem",
            "topaz_rock": "topaz_gem",
            "corundum_rock": "corundum_gem",
            "diamond_rock": "diamond_gem"
        }
        return rock_to_gem.get(rock_type)
        
    def collect_gem(self, gem_type):
        """Collect a gem and add it to inventory"""
        if gem_type in self.gem_inventory:
            self.gem_inventory[gem_type] += 1
            print(f"💎 Collected {gem_type}! Total: {self.gem_inventory[gem_type]}")
            
            # Check if we have enough gems for an upgrade
            self.check_upgrade_availability(gem_type)
            
    def check_upgrade_availability(self, gem_type):
        """Check if player has enough gems (10) to upgrade tools"""
        if self.gem_inventory[gem_type] >= 10:
            print(f"🔧 Can upgrade tool with {gem_type}! (Type 'upgrade {gem_type}' in chat)")
            
    def collect_world_gem(self, world, x, y):
        """Collect a gem from the world at specific coordinates"""
        gem_type = world.get_gem_at(x, y)
        if gem_type:
            world.remove_gem_at(x, y)
            self.collect_gem(gem_type)
            return True
        return False
        
    def get_total_gems(self):
        """Get total number of gems collected"""
        return sum(self.gem_inventory.values())
        
    def get_rarest_gem(self):
        """Get the rarest gem type currently held (for enemy theft)"""
        # Order by rarity (diamond most valuable)
        gem_rarity_order = [
            "diamond_gem", "corundum_gem", "topaz_gem", "quartz_gem",
            "orthoclase_gem", "apatite_gem", "fluorite_gem", "calcite_gem",
            "gypsum_gem", "talc_gem"
        ]
        
        for gem_type in gem_rarity_order:
            if self.gem_inventory[gem_type] > 0:
                return gem_type
        return None
        
    def check_enemy_encounter(self, world, x, y):
        """Handle enemy encounters at current position"""
        enemy_type = world.get_enemy_at(x, y)
        if enemy_type:
            print(f"💥 Encountered {enemy_type}!")
            
            # Enemy steals gems based on type
            if enemy_type == "mole":
                # Moles steal common gems
                stolen_gems = ["talc_gem", "gypsum_gem", "calcite_gem"]
            elif enemy_type == "beetle": 
                # Beetles steal mid-tier gems
                stolen_gems = ["fluorite_gem", "apatite_gem", "orthoclase_gem"]
            elif enemy_type == "worm":
                # Worms steal rare gems  
                stolen_gems = ["quartz_gem", "topaz_gem", "corundum_gem", "diamond_gem"]
            else:
                stolen_gems = []
                
            # Steal gems if character has any
            for gem_type in stolen_gems:
                if self.gem_inventory[gem_type] > 0:
                    stolen_count = min(random.randint(1, 3), self.gem_inventory[gem_type])
                    self.gem_inventory[gem_type] -= stolen_count
                    print(f"😱 {enemy_type.title()} stole {stolen_count} {gem_type}!")
                    break  # Only steal one type per encounter
                    
            # Remove enemy after encounter
            world.enemies[x][y] = None
    
    def activate_rainbow_mode(self, duration=10000):
        """Activate rainbow visual effect"""
        print("🌈 Rainbow mode activated!")
        self.rainbow_mode = True
        self.rainbow_timer = pygame.time.get_ticks() + duration
        
    def activate_shield(self, duration=10000):
        """Activate shield (temporary invincibility)"""
        print("🛡️ Shield activated!")
        self.shield_active = True
        self.shield_timer = pygame.time.get_ticks() + duration
        
    def activate_freeze(self, duration=5000):
        """Activate freeze (pause digging temporarily)"""
        print("🧊 Freeze activated!")
        self.freeze_active = True
        self.freeze_timer = pygame.time.get_ticks() + duration
        
    def update_effects(self):
        """Update visual effect timers"""
        current_time = pygame.time.get_ticks()
        
        if self.rainbow_mode and current_time > self.rainbow_timer:
            self.rainbow_mode = False
            print("🌈 Rainbow mode ended")
            
        if self.shield_active and current_time > self.shield_timer:
            self.shield_active = False
            print("🛡️ Shield ended")
            
        if self.freeze_active and current_time > self.freeze_timer:
            self.freeze_active = False
            print("🧊 Freeze ended")
        
    def play_dig_sound(self, block_type):
        """Play appropriate digging sound for block type"""
        if "rock" in block_type:
            # Play rock breaking sound
            self.sound_manager.play_sound("stone1")
        else:
            # Play dirt digging sound
            self.sound_manager.play_sound("grass1")
            
    def get_gem_rarity_order(self):
        """Get gem types ordered by rarity (highest first)"""
        return [
            "diamond_gem", "corundum_gem", "topaz_gem", "quartz_gem",
            "orthoclase_gem", "apatite_gem", "fluorite_gem", "calcite_gem", 
            "gypsum_gem", "talc_gem"
        ]
        
    def upgrade_tool(self, gem_type):
        """
        Add tool upgrade to queue using collected gems.
        Highest rarity upgrades are used first.
        
        :param gem_type: Type of gem used for upgrade
        :return: True if upgrade successful, False if not enough gems
        """
        if self.gem_inventory[gem_type] < 10:
            return False
            
        # Use 10 gems for upgrade
        self.gem_inventory[gem_type] -= 10
        
        current_time = pygame.time.get_ticks()
        
        # Check if this gem type is already in queue
        existing_upgrade = None
        for i, (queued_gem, end_time) in enumerate(self.tool_upgrade_queue):
            if queued_gem == gem_type:
                existing_upgrade = (i, end_time)
                break
                
        if existing_upgrade:
            # Extend existing upgrade in queue
            i, end_time = existing_upgrade
            remaining_time = max(0, end_time - current_time)
            remaining_seconds = remaining_time / 1000.0
            
            if remaining_seconds < 100:
                extension = max(10000, ((100 - remaining_seconds) / 2) * 1000)
                new_end_time = end_time + int(extension)
                print(f"🔧 Extended {gem_type} upgrade by {extension/1000:.1f}s!")
            else:
                new_end_time = end_time + 10000  # Minimum 10 seconds
                print(f"🔧 Extended {gem_type} upgrade by 10s!")
                
            self.tool_upgrade_queue[i] = (gem_type, new_end_time)
        else:
            # Add new upgrade to queue
            new_end_time = current_time + 100000  # 100 seconds
            self.tool_upgrade_queue.append((gem_type, new_end_time))
            print(f"🛠️ {gem_type} tool upgrade queued for 100 seconds!")
            
        # Sort queue by rarity (highest first)
        rarity_order = self.get_gem_rarity_order()
        self.tool_upgrade_queue.sort(key=lambda x: rarity_order.index(x[0]))
        
        self.update_tool_efficiency()
        return True
        
    def update_tool_efficiency(self):
        """Update tool efficiency using queue system (highest rarity first)"""
        current_time = pygame.time.get_ticks()
        
        # Remove expired upgrades from queue
        self.tool_upgrade_queue = [(gem, end_time) for gem, end_time in self.tool_upgrade_queue if end_time > current_time]
        
        # Check if current upgrade expired
        if self.current_tool_upgrade:
            if current_time >= self.current_tool_upgrade[1]:
                print(f"⏰ {self.current_tool_upgrade[0]} tool upgrade expired")
                self.current_tool_upgrade = None
                
        # If no current upgrade, get next from queue
        if not self.current_tool_upgrade and self.tool_upgrade_queue:
            self.current_tool_upgrade = self.tool_upgrade_queue.pop(0)
            print(f"🔧 Now using {self.current_tool_upgrade[0]} tool upgrade!")
            
        # Set efficiency based on current upgrade
        if self.current_tool_upgrade:
            self.tool_efficiency = 1.5  # 50% efficiency boost
        else:
            self.tool_efficiency = 1.0  # Base efficiency
            
    def get_current_tool_info(self):
        """Get current tool type and durability percentage for HUD"""
        if not self.current_tool_upgrade:
            return "basic_tool", 100.0  # Always 100% for basic tool
            
        gem_type, end_time = self.current_tool_upgrade
        current_time = pygame.time.get_ticks()
        remaining_time = max(0, end_time - current_time)
        
        # Calculate durability percentage (100% = 100 seconds)
        durability_percent = min(100.0, (remaining_time / 1000.0))
        
        return gem_type.replace("_gem", "_tool"), durability_percent
        
    def update(self, world):
        """
        Update character state each frame.
        
        :param world: World object for digging interactions
        """
        # Update digging progress
        self.update_digging(world)
        
        # Auto-start digging if not currently digging
        if not self.is_digging:
            self.start_digging(world)
            
        # Check for gems to collect at current position
        self.collect_world_gem(world, self.grid_x, self.grid_y)
        
        # Check for enemy encounters
        self.check_enemy_encounter(world, self.grid_x, self.grid_y)
            
        # Update visual effects
        self.update_particles()
        self.update_effects()
        
        # Update tool efficiency timers
        self.update_tool_efficiency()
        
    def update_particles(self):
        """Update dig particles for visual effects"""
        # Remove old particles
        self.dig_particles = [p for p in self.dig_particles if p['life'] > 0]
        
        # Update existing particles
        for particle in self.dig_particles:
            particle['y'] += particle['vel_y']
            particle['x'] += particle['vel_x']
            particle['life'] -= 1
            
        # Add new particles while digging
        if self.is_digging and random.random() < 0.3:
            self.dig_particles.append({
                'x': self.x + random.randint(-10, 10),
                'y': self.y + BLOCK_SIZE,
                'vel_x': random.randint(-2, 2),
                'vel_y': random.randint(-3, -1),
                'life': random.randint(15, 30),
                'color': (101, 67, 33)  # Brown dirt color
            })
            
    def draw(self, surface, camera):
        """
        Draw the character and visual effects.
        
        :param surface: Surface to draw on
        :param camera: Camera for position offset
        """
        # Calculate screen position
        screen_x = self.x - camera.offset_x
        screen_y = self.y - camera.offset_y
        
        # Draw character sprite
        char_texture = self.texture
        if self.facing_direction == -1:
            char_texture = pygame.transform.flip(self.texture, True, False)
            
        surface.blit(char_texture, (screen_x, screen_y))
        
        # Draw dig progress bar if digging
        if self.is_digging:
            self.draw_dig_progress(surface, screen_x, screen_y)
            
        # Draw particles
        for particle in self.dig_particles:
            particle_x = particle['x'] - camera.offset_x
            particle_y = particle['y'] - camera.offset_y
            pygame.draw.circle(surface, particle['color'], 
                             (int(particle_x), int(particle_y)), 2)
                             
    def draw_dig_progress(self, surface, screen_x, screen_y):
        """Draw digging progress bar above character"""
        bar_width = 60
        bar_height = 6
        bar_x = screen_x + (BLOCK_SIZE - bar_width) // 2
        bar_y = screen_y - 15
        
        # Background
        pygame.draw.rect(surface, (100, 100, 100), 
                        (bar_x, bar_y, bar_width, bar_height))
        
        # Progress
        progress_width = int(bar_width * self.dig_progress)
        progress_color = (255, 255, 0) if self.dig_progress < 0.8 else (0, 255, 0)
        pygame.draw.rect(surface, progress_color, 
                        (bar_x, bar_y, progress_width, bar_height))