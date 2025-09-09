import random
import pygame
from constants import BLOCK_SIZE
from collections import defaultdict

class World:
    def __init__(self, width=50):
        """
        Initialize the digging world with layered generation.
        
        :param width: Width of the world in grid spaces (centered around x=0)
        """
        self.width = width
        self.blocks = defaultdict(lambda: defaultdict(lambda: None))  # [x][y] = block_type
        self.gems = defaultdict(lambda: defaultdict(lambda: None))    # [x][y] = gem_type  
        self.enemies = defaultdict(lambda: defaultdict(lambda: None)) # [x][y] = enemy_type
        self.powerups = defaultdict(lambda: defaultdict(lambda: None)) # [x][y] = powerup_type
        
        # Generation settings
        self.last_generated_depth = 0
        self.layer_height = 10  # Height of each difficulty layer
        
        # Spawn rates (per block chance)
        self.rock_spawn_rate = 0.15      # 15% chance for rocks
        self.gem_spawn_rate = 0.05       # 5% chance for random gems
        self.powerup_spawn_rate = 0.02   # 2% chance for power-ups
        self.enemy_layer_spacing = 12    # Every 12±3 layers
        self.last_enemy_layer = 0
        
        # Pre-generate some initial layers
        self.generate_layers_to_depth(50)
        
    def get_block_at(self, x, y):
        """Get block type at grid coordinates"""
        return self.blocks[x][y]
        
    def get_gem_at(self, x, y):
        """Get gem type at grid coordinates"""
        return self.gems[x][y]
        
    def get_enemy_at(self, x, y):
        """Get enemy type at grid coordinates"""
        return self.enemies[x][y]
        
    def get_powerup_at(self, x, y):
        """Get powerup type at grid coordinates"""
        return self.powerups[x][y]
        
    def remove_block_at(self, x, y):
        """Remove block at coordinates and return what was there"""
        block_type = self.blocks[x][y]
        self.blocks[x][y] = None
        
        # If it was a rock, might drop a gem
        if block_type and "rock" in block_type:
            gem_type = self.get_gem_from_rock(block_type)
            if gem_type:
                print(f"Rock {block_type} dropped {gem_type} gem!")
                # TODO: Add to player inventory
                
        return block_type
        
    def remove_gem_at(self, x, y):
        """Remove and return gem at coordinates"""
        gem_type = self.gems[x][y]
        self.gems[x][y] = None
        return gem_type
        
    def remove_powerup_at(self, x, y):
        """Remove and return powerup at coordinates"""
        powerup_type = self.powerups[x][y]
        self.powerups[x][y] = None
        return powerup_type
        
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
        
    def generate_layers_to_depth(self, target_depth):
        """Generate world layers down to target depth"""
        if target_depth <= self.last_generated_depth:
            return
            
        for y in range(self.last_generated_depth, target_depth):
            self.generate_layer(y)
            
        self.last_generated_depth = target_depth
        
    def generate_layer(self, y):
        """Generate a single horizontal layer at depth y"""
        # Determine difficulty level based on depth
        difficulty_level = min(5, (y // self.layer_height) + 1)
        
        # Generate blocks across the width
        start_x = -(self.width // 2)
        end_x = self.width // 2
        
        for x in range(start_x, end_x):
            # Generate base terrain (dirt/rock)
            self.generate_terrain_at(x, y, difficulty_level)
            
            # Generate gems
            self.generate_gem_at(x, y, difficulty_level)
            
            # Generate power-ups
            self.generate_powerup_at(x, y)
            
        # Check if we should generate enemy layer
        self.check_generate_enemy_layer(y)
        
    def generate_terrain_at(self, x, y, difficulty_level):
        """Generate terrain (dirt or rock) at specific coordinates"""
        # Choose dirt type based on difficulty level
        dirt_types = [
            "dirt_light",    # Level 1
            "dirt_medium",   # Level 2
            "dirt_dark",     # Level 3
            "clay",          # Level 4
            "bedrock"        # Level 5
        ]
        
        base_dirt = dirt_types[difficulty_level - 1]
        
        # Chance for rock instead of dirt
        if random.random() < self.rock_spawn_rate:
            # Generate rock based on depth and rarity
            rock_type = self.get_random_rock_type(difficulty_level)
            self.blocks[x][y] = rock_type
        else:
            # Generate dirt
            self.blocks[x][y] = base_dirt
            
    def get_random_rock_type(self, difficulty_level):
        """Get random rock type weighted by difficulty and rarity"""
        # Rock types with their relative rarity (higher = more common)
        rocks_by_difficulty = {
            1: [("talc_rock", 10), ("gypsum_rock", 8)],
            2: [("talc_rock", 8), ("gypsum_rock", 10), ("calcite_rock", 6)],
            3: [("gypsum_rock", 6), ("calcite_rock", 10), ("fluorite_rock", 8), ("apatite_rock", 4)],
            4: [("calcite_rock", 6), ("fluorite_rock", 10), ("apatite_rock", 8), ("orthoclase_rock", 6), ("quartz_rock", 3)],
            5: [("apatite_rock", 5), ("orthoclase_rock", 8), ("quartz_rock", 10), ("topaz_rock", 6), ("corundum_rock", 3), ("diamond_rock", 1)]
        }
        
        # Get available rocks for this difficulty
        available_rocks = []
        for level in range(1, difficulty_level + 1):
            if level in rocks_by_difficulty:
                available_rocks.extend(rocks_by_difficulty[level])
                
        if not available_rocks:
            return "talc_rock"  # Fallback
            
        # Weighted random selection
        total_weight = sum(weight for _, weight in available_rocks)
        rand_val = random.randint(1, total_weight)
        
        current_weight = 0
        for rock_type, weight in available_rocks:
            current_weight += weight
            if rand_val <= current_weight:
                return rock_type
                
        return available_rocks[0][0]  # Fallback
        
    def generate_gem_at(self, x, y, difficulty_level):
        """Generate random gem at coordinates"""
        if random.random() < self.gem_spawn_rate:
            gem_type = self.get_random_gem_type(difficulty_level)
            self.gems[x][y] = gem_type
            
    def get_random_gem_type(self, difficulty_level):
        """Get random gem type weighted by rarity and depth"""
        # Gem rarity (lower = rarer)
        gem_rarities = {
            "talc_gem": 100,      # Most common
            "gypsum_gem": 80,
            "calcite_gem": 60, 
            "fluorite_gem": 45,
            "apatite_gem": 35,
            "orthoclase_gem": 25,
            "quartz_gem": 18,
            "topaz_gem": 12,
            "corundum_gem": 6,
            "diamond_gem": 1      # Rarest
        }
        
        # Adjust rarities based on depth (deeper = better gems more likely)
        adjusted_rarities = {}
        depth_bonus = difficulty_level * 0.2
        
        for gem, base_rarity in gem_rarities.items():
            # Rare gems get bonus at deeper levels
            if base_rarity < 20:  # Rare gems
                adjusted_rarities[gem] = base_rarity * (1 + depth_bonus)
            else:  # Common gems
                adjusted_rarities[gem] = base_rarity
                
        # Weighted random selection
        total_weight = sum(adjusted_rarities.values())
        rand_val = random.uniform(0, total_weight)
        
        current_weight = 0
        for gem_type, weight in adjusted_rarities.items():
            current_weight += weight
            if rand_val <= current_weight:
                return gem_type
                
        return "talc_gem"  # Fallback
        
    def generate_powerup_at(self, x, y):
        """Generate random power-up at coordinates"""
        if random.random() < self.powerup_spawn_rate:
            powerup_types = [
                "carrot",    # Speed boost
                "apple",     # Health restore
                "grapes",    # Multi-dig
                "potato",    # Shield
                "corn",      # Gem magnet
                "daisy",     # Reveal gems
                "rose",      # Attract rare gems
                "tulip"      # Invincibility
            ]
            
            powerup_type = random.choice(powerup_types)
            self.powerups[x][y] = powerup_type
            
    def check_generate_enemy_layer(self, y):
        """Check if we should generate an enemy pocket at this depth"""
        layers_since_last = y - self.last_enemy_layer
        spacing_with_variation = self.enemy_layer_spacing + random.randint(-3, 3)
        
        if layers_since_last >= spacing_with_variation:
            self.generate_enemy_pocket(y)
            self.last_enemy_layer = y
            
    def generate_enemy_pocket(self, y):
        """Generate a pocket of enemies at the given depth"""
        # Choose a random horizontal section for the pocket
        pocket_width = random.randint(3, 7)
        center_x = random.randint(-(self.width//4), self.width//4)
        
        enemy_types = ["mole", "worm", "beetle"]
        enemy_type = random.choice(enemy_types)
        
        # Place enemies in the pocket
        for i in range(pocket_width):
            x = center_x - (pocket_width // 2) + i
            
            # Create air space for enemies (remove blocks)
            self.blocks[x][y] = None
            self.blocks[x][y-1] = None  # Air space above too
            
            # Place enemy
            if random.random() < 0.7:  # 70% chance per spot
                self.enemies[x][y] = enemy_type
                
        print(f"Generated {enemy_type} pocket at depth {y}, center x={center_x}")
        
    def ensure_generated_to_depth(self, depth):
        """Ensure world is generated to at least the given depth"""
        if depth > self.last_generated_depth:
            self.generate_layers_to_depth(depth + 20)  # Generate a bit ahead
            
    def get_blocks_in_region(self, min_x, max_x, min_y, max_y):
        """Get all blocks in a rectangular region"""
        blocks = []
        for x in range(min_x, max_x + 1):
            for y in range(min_y, max_y + 1):
                block_type = self.blocks[x][y]
                if block_type:
                    blocks.append((x, y, block_type))
        return blocks
        
    def get_gems_in_region(self, min_x, max_x, min_y, max_y):
        """Get all gems in a rectangular region"""
        gems = []
        for x in range(min_x, max_x + 1):
            for y in range(min_y, max_y + 1):
                gem_type = self.gems[x][y]
                if gem_type:
                    gems.append((x, y, gem_type))
        return gems
        
    def get_powerups_in_region(self, min_x, max_x, min_y, max_y):
        """Get all powerups in a rectangular region"""
        powerups = []
        for x in range(min_x, max_x + 1):
            for y in range(min_y, max_y + 1):
                powerup_type = self.powerups[x][y]
                if powerup_type:
                    powerups.append((x, y, powerup_type))
        return powerups
        
    def get_enemies_in_region(self, min_x, max_x, min_y, max_y):
        """Get all enemies in a rectangular region"""
        enemies = []
        for x in range(min_x, max_x + 1):
            for y in range(min_y, max_y + 1):
                enemy_type = self.enemies[x][y]
                if enemy_type:
                    enemies.append((x, y, enemy_type))
        return enemies