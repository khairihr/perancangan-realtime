import pygame
import sys
import math
import time

# Initialize Pygame
pygame.init()

# Set up display
screen_size = 480
center = (screen_size // 2, screen_size // 2)
screen = pygame.display.set_mode((screen_size, screen_size))
pygame.display.set_caption('Vehicle Position Radar')

# Colors
black = (0, 0, 0)
green = (0, 255, 0)
dark_green = (0, 100, 0)

# Simulation variables
sweep_angle = 0
sweep_speed = 0.5  # degrees per frame

# Main loop
running = True
while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

    # Clear screen
    screen.fill(black)

    # Draw radar circles
    for radius in range(50, 250, 50):
        pygame.draw.circle(screen, dark_green, center, radius, 1)
    
    # Draw radar sweep
    radians = math.radians(sweep_angle)
    end_point = (center[0] + math.sin(radians) * 200, center[1] - math.cos(radians) * 200)
    pygame.draw.line(screen, green, center, end_point, 2)
    sweep_angle = (sweep_angle + sweep_speed) % 360
    
    # Simulated vehicle positions (replace with real data)
    vehicle_positions = [
        (center[0] + 100, center[1]),  # Vehicle 1
        (center[0], center[1] - 150),  # Vehicle 2
    ]

    # Draw vehicle positions
    for pos in vehicle_positions:
        pygame.draw.circle(screen, green, pos, 5)
    
    # Update display
    pygame.display.flip()
    time.sleep(0.01)  # Adjust for desired sweep speed

pygame.quit()
sys.exit()
