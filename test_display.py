#!/usr/bin/env python3
import pygame
import sys

print("Testing pygame display...")

try:
    pygame.init()
    print("Pygame initialized successfully")
    
    # Try to create a simple display
    screen = pygame.display.set_mode((400, 300))
    pygame.display.set_caption("Test Window")
    
    print("Display created successfully")
    
    # Fill with red and update
    screen.fill((255, 0, 0))
    pygame.display.flip()
    
    print("Window should be visible now")
    print("Press SPACE or close window to exit")
    
    clock = pygame.time.Clock()
    running = True
    
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE:
                    running = False
        
        clock.tick(60)
    
    pygame.quit()
    print("Test completed successfully")

except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()