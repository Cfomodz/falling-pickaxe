import pygame
import pymunk
from constants import BLOCK_SIZE
import random 

class Block:
    def __init__(self, space, x, y, name, texture_atlas, atlas_items):
        # HP values equal to point values (hits needed with wooden pickaxe)
        # Common blocks (1 point -> 1 HP)
        if name == "bedrock":
            self.max_hp = 1000000000
            self.hp = 1000000000
        elif name in ["stone", "cobblestone", "dirt", "grass_block"]:
            self.max_hp = 1  # 1 hit with wooden pickaxe
            self.hp = 1
        # Uncommon blocks (2 points -> 2 HP)
        elif name in ["coal_ore", "diorite", "granite", "andesite", "mossy_cobblestone"]:
            self.hp = 2  # 2 hits with wooden pickaxe
            self.max_hp = 2
        # Rare blocks (4 points -> 4 HP)
        elif name in ["iron_ore", "copper_ore"]:
            self.hp = 4  # 4 hits with wooden pickaxe
            self.max_hp = 4
        # Very rare blocks (8 points -> 8 HP)
        elif name in ["gold_ore", "redstone_ore", "lapis_ore"]:
            self.hp = 8  # 8 hits with wooden pickaxe
            self.max_hp = 8
        # Epic blocks (16 points -> 16 HP)
        elif name == "diamond_ore":
            self.hp = 16  # 16 hits with wooden pickaxe
            self.max_hp = 16
        # Legendary blocks (32 points -> 32 HP)
        elif name == "emerald_ore":
            self.hp = 32  # 32 hits with wooden pickaxe
            self.max_hp = 32
        # Mythic blocks (64 points -> 64 HP)
        elif name == "obsidian":
            self.hp = 64  # 64 hits with wooden pickaxe
            self.max_hp = 64
        else:
            self.hp = 1
            self.max_hp = 1

        self.texture_atlas = texture_atlas
        self.atlas_items = atlas_items

        rect = atlas_items["block"][name]  
        self.texture = texture_atlas.subsurface(rect)

        width, height = self.texture.get_size()

        # Create a static physics body (doesn't move)
        self.body = pymunk.Body(body_type=pymunk.Body.STATIC)
        self.body.position = (x + BLOCK_SIZE//2, y + BLOCK_SIZE//2)

        # Create a hitbox
        self.shape = pymunk.Poly.create_box(self.body, (width, height))
        self.shape.elasticity = 1  # No bounce
        self.shape.collision_type = 2 # Identifier for collisions
        self.shape.friction = 1
        self.shape.block_ref = self  # Reference to the block object

        self.destroyed = False
        self.broken = False  # Track if block was broken for scoring

        self.name = name
        self.block_type = name  # Expose block type for competitive scoring

        space.add(self.body, self.shape)

    def update(self, space, hud):
        """Update block state"""
        
        # Track if block was previously broken
        was_broken = self.broken
        
        # Check if block should be destroyed
        if self.hp <= 0 and not self.destroyed:
            self.destroyed = True
            self.broken = True  # Mark as broken for scoring
            space.remove(self.body, self.shape)  # Remove from physics world

            if self.name == "coal_ore":
                hud.amounts["coal"] += 1  # Add to HUD amounts
            elif self.name == "iron_ore":
                hud.amounts["iron_ingot"] += 1  # Add to HUD amounts
            elif self.name == "copper_ore":
                hud.amounts["copper_ingot"] += 1  # Add to HUD amounts
            elif self.name == "gold_ore":
                hud.amounts["gold_ingot"] += 1  # Add to HUD amounts
            elif self.name == "diamond_ore":
                hud.amounts["diamond"] += 1  # Add to HUD amounts
            elif self.name == "emerald_ore":
                hud.amounts["emerald"] += 1  # Add to HUD amounts
            elif self.name == "redstone_ore":
                hud.amounts["redstone"] += random.randint(4, 5)  # Add to HUD amounts
            elif self.name == "lapis_ore":
                hud.amounts["lapis_lazuli"] += random.randint(4, 8)  # Add to HUD amounts

    def draw(self, screen, camera):
        """Draw block at its position"""

        if(self.destroyed):
            return

        block_x = self.body.position.x - camera.offset_x - BLOCK_SIZE // 2
        block_y = self.body.position.y - camera.offset_y - BLOCK_SIZE // 2

        screen.blit(self.texture, (block_x, block_y))

        # Determine the destroy stage (0-9) based on hp percentage
        if self.hp < self.max_hp:
            damage_stage = int((1 - (self.hp / self.max_hp)) * 9)  # Scale hp to 0-9 range
            damage_stage = min(damage_stage, 9)  # Ensure it doesn't exceed stage_9
            
            # Draw the destroy stage overlay
            destroy_texture = self.texture_atlas.subsurface(
                self.atlas_items["destroy_stage"][f"destroy_stage_{damage_stage}"]
            )
            screen.blit(destroy_texture, (block_x, block_y))