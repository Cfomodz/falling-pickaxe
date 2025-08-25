
import pygame
import random
import math
from constants import INTERNAL_WIDTH, INTERNAL_HEIGHT

class WeatherSystem:
    def __init__(self):
        self.active_weather = None
        self.particles = []
        self.lightning_flash = 0
        self.weather_timer = 0
        self.next_weather_change = random.randint(30000, 120000)  # 30s to 2min
        
    def start_weather(self, weather_type):
        self.active_weather = weather_type
        self.particles = []
        print(f"Weather started: {weather_type}")
        
    def stop_weather(self):
        self.active_weather = None
        self.particles = []
        self.lightning_flash = 0
        
    def update(self, settings_manager):
        if not settings_manager.get_setting("weather_effects"):
            if self.active_weather:
                self.stop_weather()
            return
            
        self.weather_timer += 16  # Assuming 60 FPS
        
        # Random weather changes (only if auto weather is enabled)
        if settings_manager.get_setting("auto_weather") and self.weather_timer > self.next_weather_change:
            if self.active_weather is None:
                # Start random weather
                weather_options = []
                if settings_manager.get_setting("weather_rain"):
                    weather_options.append("rain")
                if settings_manager.get_setting("weather_snow"):
                    weather_options.append("snow")
                if settings_manager.get_setting("weather_lightning"):
                    weather_options.append("lightning")
                    
                if weather_options:
                    self.start_weather(random.choice(weather_options))
                    self.next_weather_change = random.randint(15000, 45000)  # Weather duration
            else:
                # Stop weather
                self.stop_weather()
                self.next_weather_change = random.randint(30000, 120000)  # Next weather delay
                
            self.weather_timer = 0
        
        # Update active weather
        if self.active_weather == "rain":
            self.update_rain(settings_manager)
        elif self.active_weather == "snow":
            self.update_snow(settings_manager)
        elif self.active_weather == "lightning":
            self.update_lightning(settings_manager)
            
        # Update particles
        performance_mode = settings_manager.get_setting("performance_mode")
        max_particles = 50 if performance_mode else settings_manager.get_setting("max_particles")
        
        for particle in self.particles[:]:
            particle['y'] += particle['speed']
            particle['x'] += particle.get('wind', 0)
            particle['life'] -= 1
            
            # Remove particles that are off screen or dead
            if (particle['y'] > INTERNAL_HEIGHT + 50 or 
                particle['x'] < -50 or particle['x'] > INTERNAL_WIDTH + 50 or
                particle['life'] <= 0):
                self.particles.remove(particle)
        
        # Limit particle count for performance
        if len(self.particles) > max_particles:
            self.particles = self.particles[-max_particles:]
    
    def update_rain(self, settings_manager):
        # Spawn rain particles
        if len(self.particles) < 80:
            for _ in range(3):
                self.particles.append({
                    'x': random.randint(-50, INTERNAL_WIDTH + 50),
                    'y': random.randint(-100, -50),
                    'speed': random.randint(8, 15),
                    'wind': random.uniform(-1, 1),
                    'type': 'rain',
                    'life': 300,
                    'size': random.randint(2, 4)
                })
    
    def update_snow(self, settings_manager):
        # Spawn snow particles
        if len(self.particles) < 60:
            for _ in range(2):
                self.particles.append({
                    'x': random.randint(-50, INTERNAL_WIDTH + 50),
                    'y': random.randint(-100, -50),
                    'speed': random.randint(2, 5),
                    'wind': random.uniform(-2, 2),
                    'type': 'snow',
                    'life': 400,
                    'size': random.randint(3, 8),
                    'rotation': random.uniform(0, 360)
                })
    
    def update_lightning(self, settings_manager):
        # Lightning flashes
        if random.randint(1, 180) == 1:  # Random lightning
            self.lightning_flash = 30
            
        if self.lightning_flash > 0:
            self.lightning_flash -= 1
    
    def draw(self, screen, camera, settings_manager):
        if not settings_manager.get_setting("weather_effects") or not self.active_weather:
            return
            
        # Draw weather particles
        for particle in self.particles:
            screen_x = particle['x']
            screen_y = particle['y'] - camera.y
            
            if particle['type'] == 'rain':
                color = (100, 150, 255)
                pygame.draw.line(screen, color, 
                               (screen_x, screen_y), 
                               (screen_x - 2, screen_y + particle['size']), 2)
            elif particle['type'] == 'snow':
                color = (255, 255, 255)
                size = particle['size']
                pygame.draw.circle(screen, color, (int(screen_x), int(screen_y)), size // 2)
                # Draw small cross pattern for snowflake effect
                pygame.draw.line(screen, color, 
                               (screen_x - size//2, screen_y), 
                               (screen_x + size//2, screen_y), 1)
                pygame.draw.line(screen, color, 
                               (screen_x, screen_y - size//2), 
                               (screen_x, screen_y + size//2), 1)
        
        # Draw lightning flash
        if self.lightning_flash > 0:
            alpha = (self.lightning_flash / 30) * 100
            flash_surface = pygame.Surface((INTERNAL_WIDTH, INTERNAL_HEIGHT))
            flash_surface.set_alpha(alpha)
            flash_surface.fill((200, 200, 255))
            screen.blit(flash_surface, (0, 0))
