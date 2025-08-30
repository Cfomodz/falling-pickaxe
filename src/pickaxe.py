import pygame
import math
import pymunk
import pymunk.autogeometry
from chunk import chunks
from constants import BLOCK_SIZE, CHUNK_WIDTH
import random

def rotate_point(x, y, angle):
    """Rotate a point (x, y) by angle (in radians) around the origin (0, 0)."""
    cos_angle = math.cos(angle)
    sin_angle = math.sin(angle)
    new_x = cos_angle * x - sin_angle * y
    new_y = sin_angle * x + cos_angle * y
    return new_x, new_y

def rotate_vertices(vertices, angle):
        rotated_vertices = []

        for vertex in vertices:
            # Rotate each vertex based on the body's angle
            rotated_x, rotated_y = rotate_point(vertex[0] - BLOCK_SIZE / 2 , vertex[1] - BLOCK_SIZE / 2, angle)

            # Offset each rotated vertex by the body's position
            rotated_vertices.append((rotated_x, rotated_y))
        
        return rotated_vertices

class Pickaxe:
    def __init__(self, space, x, y, texture, sound_manager, damage=2, velocity=0, rotation=0, mass=100):
        self.texture = texture
        self.original_texture = texture.copy()
        self.velocity = velocity
        self.rotation = rotation
        self.space = space
        self.damage = damage
        self.is_enlarged = False
        self.rainbow_mode = False
        self.rainbow_timer = 0
        self.color_hue = 0
        self.particle_trail = []
        self.shield_active = False
        self.shield_timer = 0
        self.shield_glow = []

        vertices = rotate_vertices([
                    (0, 0), # A
                    (10, 0), # C
                    (110, 100), # D
                    (100, 110), # E
                    (0, 10), # F
                    (110, 110), # G
                ], -math.pi / 2)
        
        vertices2 = rotate_vertices([
                    (110, 30), # H
                    (120, 40), # I
                    (120, 90), # J
                    (100, 90), # K
                    (100, 40), # L
                    (110, 100), # D
                ], -math.pi / 2)
        
        vertices3 = rotate_vertices([
                    (30, 110), # M
                    (40, 120), # N
                    (90, 120), # O
                    (40, 100), # P
                    (90, 100), # Q
                    (100, 110), # E
                ], -math.pi / 2)

        inertia = pymunk.moment_for_poly(mass, vertices)
        self.body = pymunk.Body(mass, inertia)
        self.body.position = (x, y)
        self.body.angle = math.radians(rotation)

        self.sound_manager = sound_manager

        self.shapes = []
        for vertices in [vertices, vertices2, vertices3]:
            shape = pymunk.Poly(self.body, vertices)
            shape.elasticity = 0.7
            shape.friction = 0.7
            shape.collision_type = 1  # Identifier for collisions
            self.shapes.append(shape)

        self.space.add(self.body, *self.shapes)

        # Add collision handler for pickaxe & blocks
        handler = self.space.add_collision_handler(1, 2)  # (Pickaxe type, Block type)
        handler.post_solve = self.on_collision

    def on_collision(self, arbiter, space, data):
        """Handles collision with blocks: Reduce HP or destroy the block."""
        block_shape = arbiter.shapes[1]  # Get the block shape
        block = block_shape.block_ref  # Get the actual block instance

        block.first_hit_time = pygame.time.get_ticks()  
        block.last_heal_time = block.first_hit_time

        # Calculate impact force for screen shake
        impact_force = abs(self.body.velocity.y) / 100
        
        block.hp -= self.damage  # Reduce HP when hit

        if (block.name == "grass_block" or block.name == "dirt"):
            self.sound_manager.play_sound("grass" + str(random.randint(1, 4)))
        else:
            self.sound_manager.play_sound("stone" + str(random.randint(1, 4)))
            
        # Screen shake based on impact and pickaxe size (reduced by 90%)
        shake_intensity = max(0.2, impact_force * (0.3 if self.is_enlarged else 0.1))
        if hasattr(self, 'camera_ref'):
            self.camera_ref.shake(15, shake_intensity)

        # Add small random rotation on hit
        self.body.angle += random.choice([0.01, -0.01])

    def random_pickaxe(self, texture_atlas, atlas_items): 
        """Randomly change the pickaxe's properties."""

        pickaxe_name = random.choice(list(atlas_items["pickaxe"].keys()))
        self.texture = texture_atlas.subsurface(atlas_items["pickaxe"][pickaxe_name])
        print("Setting pickaxe to:", pickaxe_name)

        if self.is_enlarged:
            # Scale up texture
            new_size = (BLOCK_SIZE * 3, BLOCK_SIZE * 3)
            self.texture = pygame.transform.scale(self.texture, new_size)

        if(pickaxe_name =="wooden_pickaxe"):  
            self.damage = 2
        elif(pickaxe_name =="stone_pickaxe"):
            self.damage = 4
        elif(pickaxe_name =="iron_pickaxe"):
            self.damage = 6
        elif(pickaxe_name =="golden_pickaxe"):
            self.damage = 8
        elif(pickaxe_name =="diamond_pickaxe"):
            self.damage = 10
        elif(pickaxe_name =="netherite_pickaxe"):
            self.damage = 12

    def pickaxe(self, name, texture_atlas, atlas_items):
        """Set the pickaxe's properties based on its name."""

        self.texture = texture_atlas.subsurface(atlas_items["pickaxe"][name])
        print("Setting pickaxe to:", name)

        if self.is_enlarged:
            # Scale up texture
            new_size = (BLOCK_SIZE * 3, BLOCK_SIZE * 3)
            self.texture = pygame.transform.scale(self.texture, new_size)

        if(name =="wooden_pickaxe"):  
            self.damage = 2
        elif(name =="stone_pickaxe"):
            self.damage = 4
        elif(name =="iron_pickaxe"):
            self.damage = 6
        elif(name =="golden_pickaxe"):
            self.damage = 8
        elif(name =="diamond_pickaxe"):
            self.damage = 10
        elif(name =="netherite_pickaxe"):
            self.damage = 12

    def update(self):
        """Apply gravity, update movement, check collisions, and rotate."""
        # Update rainbow effects
        self.update_rainbow_effect()
        
        # Update shield effects
        self.update_shield_effect()
        
        # Manually limit the falling speed (terminal velocity)
        max_velocity = 1200 if self.rainbow_mode else 1000
        if self.body.velocity.y > max_velocity:
            self.body.velocity = (self.body.velocity.x, max_velocity)

        # --- Bounding box check for bedrock collision ---
        # Gather all vertices from all shapes, transformed to world coordinates
        all_vertices = []
        for shape in self.shapes:
            for v in shape.get_vertices():
                # Transform local vertex to world coordinates
                world_v = self.body.local_to_world(v)
                all_vertices.append(world_v)

        min_x = min(v.x for v in all_vertices)
        max_x = max(v.x for v in all_vertices)

        left_limit = BLOCK_SIZE
        right_limit = BLOCK_SIZE * (CHUNK_WIDTH - 1)

        # If any part is left of the left limit, shift the body right
        if min_x < left_limit:
            dx = left_limit - min_x
            self.body.position = (self.body.position.x + dx, self.body.position.y)

        # If any part is right of the right limit, shift the body left
        if max_x > right_limit:
            dx = max_x - right_limit
            self.body.position = (self.body.position.x - dx, self.body.position.y)

        # If pickaxe is enlarged, check if time is up
        if hasattr(self, "enlarge_end_time") and pygame.time.get_ticks() > self.enlarge_end_time:
            self.reset_size()
            self.is_enlarged = False

    def draw(self, screen, camera):
        """Draw the pickaxe at its current position."""
        # Draw shield glow
        for glow in self.shield_glow:
            alpha = int(255 * (glow['life'] / 20))
            glow_surf = pygame.Surface((int(glow['size'] * 2), int(glow['size'] * 2)), pygame.SRCALPHA)
            golden_color = (255, 215, 0, alpha)
            pygame.draw.circle(glow_surf, golden_color, 
                             (int(glow['size']), int(glow['size'])), int(glow['size']))
            glow_pos = (glow['pos'][0] - glow['size'] - camera.offset_x, 
                       glow['pos'][1] - glow['size'] - camera.offset_y)
            screen.blit(glow_surf, glow_pos)
        
        # Draw particle trail
        for particle in self.particle_trail:
            alpha = int(255 * (particle['life'] / 30))
            trail_surf = pygame.Surface((8, 8), pygame.SRCALPHA)
            color_with_alpha = (*particle['color'][:3], alpha)
            trail_surf.fill(color_with_alpha)
            trail_pos = (particle['pos'][0] - 4 - camera.offset_x, 
                        particle['pos'][1] - 4 - camera.offset_y)
            screen.blit(trail_surf, trail_pos)
        
        # Draw pickaxe
        rotated_image = pygame.transform.rotate(self.texture, -math.degrees(self.body.angle))  # Convert to degrees
        rect = rotated_image.get_rect(center=(self.body.position.x, self.body.position.y))
        rect.y -= camera.offset_y
        rect.x -= camera.offset_x
        screen.blit(rotated_image, rect)

    def enlarge(self, duration=5000):
        """Temporarily makes the pickaxe 3 times bigger with a larger hitbox."""
        print("Enlarging pickaxe")

        # If already enlarged, just extend the duration.
        if hasattr(self, "is_enlarged") and self.is_enlarged:
            self.enlarge_end_time += duration
            return

        # Not enlarged yet, so store original texture and shapes
        self.original_texture = self.texture.copy()
        self.original_shapes = self.shapes[:]  # Store original hitbox shapes
        self.is_enlarged = True

        # Scale up texture using the original texture.
        new_size = (BLOCK_SIZE * 3, BLOCK_SIZE * 3)
        self.texture = pygame.transform.scale(self.original_texture, new_size)

        # Scale up hitbox:
        self.space.remove(*self.shapes)  # Remove current shapes
        new_shapes = []
        for shape in self.original_shapes:
            # Get vertices from original shape and scale them by 3.
            scaled_vertices = [(x * 3, y * 3) for x, y in shape.get_vertices()]
            new_shape = pymunk.Poly(self.body, scaled_vertices)
            new_shape.elasticity = shape.elasticity
            new_shape.friction = shape.friction
            new_shape.collision_type = shape.collision_type
            new_shapes.append(new_shape)
        self.shapes = new_shapes
        self.space.add(*self.shapes)  # Add new enlarged shapes

        # Track when the enlargement effect should end
        self.enlarge_end_time = pygame.time.get_ticks() + duration

    def reset_size(self):
        """Restore the pickaxe to its original size."""
        if hasattr(self, "original_shapes"):
            # Restore texture using the stored original.
            if not self.rainbow_mode:
                self.texture = self.original_texture.copy()

            # Reset hitbox: remove enlarged shapes and add back the original shapes.
            self.space.remove(*self.shapes)
            self.shapes = self.original_shapes[:]
            self.space.add(*self.shapes)
            self.is_enlarged = False

            del self.enlarge_end_time  # Remove the enlargement timer

    def activate_rainbow_mode(self, duration=10000):
        """Activate rainbow mode with cycling colors and speed boost."""
        print("🌈 RAINBOW MODE ACTIVATED!")
        self.rainbow_mode = True
        self.rainbow_timer = pygame.time.get_ticks() + duration
        self.damage += 5  # Bonus damage in rainbow mode
        
    def update_rainbow_effect(self):
        """Update rainbow color cycling and particle trail."""
        if not self.rainbow_mode:
            return
            
        # Check if rainbow mode should end
        if pygame.time.get_ticks() > self.rainbow_timer:
            self.rainbow_mode = False
            self.damage -= 5  # Remove bonus damage
            self.texture = self.original_texture.copy()
            if self.is_enlarged:
                new_size = (BLOCK_SIZE * 3, BLOCK_SIZE * 3)
                self.texture = pygame.transform.scale(self.texture, new_size)
            return
            
        # Cycle through rainbow colors
        self.color_hue = (self.color_hue + 3) % 360
        
        # Create rainbow colored texture
        rainbow_texture = self.original_texture.copy()
        if self.is_enlarged:
            rainbow_texture = pygame.transform.scale(rainbow_texture, (BLOCK_SIZE * 3, BLOCK_SIZE * 3))
            
        # Apply rainbow tint
        hue_color = pygame.Color(0)
        hue_color.hsva = (self.color_hue, 100, 100, 100)
        rainbow_texture.fill(hue_color, special_flags=pygame.BLEND_MULT)
        self.texture = rainbow_texture
        
        # Add particle trail
        self.particle_trail.append({
            'pos': (self.body.position.x, self.body.position.y),
            'color': hue_color,
            'life': 30
        })
        
        # Update particle trail
        self.particle_trail = [p for p in self.particle_trail if p['life'] > 0]
        for particle in self.particle_trail:
            particle['life'] -= 1
            
    def activate_shield(self, duration=10000):
        """Activate shield with golden glow effect."""
        print("🛡️ SHIELD ACTIVATED!")
        self.shield_active = True
        self.shield_timer = pygame.time.get_ticks() + duration
        
    def update_shield_effect(self):
        """Update shield glow effect."""
        if not self.shield_active:
            return
            
        # Check if shield should end
        if pygame.time.get_ticks() > self.shield_timer:
            self.shield_active = False
            self.shield_glow = []
            return
            
        # Create golden glow particles around pickaxe
        for i in range(3):
            angle = random.uniform(0, 2 * math.pi)
            distance = random.uniform(80, 120)
            glow_x = self.body.position.x + math.cos(angle) * distance
            glow_y = self.body.position.y + math.sin(angle) * distance
            
            self.shield_glow.append({
                'pos': (glow_x, glow_y),
                'life': 20,
                'size': random.uniform(4, 8)
            })
        
        # Update glow particles
        self.shield_glow = [g for g in self.shield_glow if g['life'] > 0]
        for glow in self.shield_glow:
            glow['life'] -= 1