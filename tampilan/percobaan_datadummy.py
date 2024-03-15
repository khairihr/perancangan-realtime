import pygame
import sys
import math
import time

# Initialize Pygame and font module
pygame.init()
pygame.font.init()

# Set up display
screen_size = 480
center = (screen_size // 2, screen_size // 2)
screen = pygame.display.set_mode((screen_size, screen_size))
pygame.display.set_caption('Vehicle Position Radar')

# Colors and font
black = (0, 0, 0)
green = (0, 255, 0)
dark_green = (0, 100, 0)
font = pygame.font.SysFont('arial', 16)

# Simulation variables
sweep_angle = 0
sweep_speed = 0.5  # degrees per frame

# Function to calculate distance
def calculate_distance(p1, p2):
    return math.sqrt((p2[0] - p1[0])**2 + (p2[1] - p1[1])**2)

# Main loop
running = True
while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

    screen.fill(black)

    # Draw radar circles
    for radius in range(50, 250, 50):
        pygame.draw.circle(screen, dark_green, center, radius, 1)

    # Radar sweep
    radians = math.radians(sweep_angle)
    end_point = (center[0] + math.sin(radians) * 200, center[1] - math.cos(radians) * 200)
    pygame.draw.line(screen, green, center, end_point, 2)
    sweep_angle = (sweep_angle + sweep_speed) % 360
    
    # Simulated vehicle positions
    vehicle_positions = [(center[0] + 100, center[1]), (center[0], center[1] - 150)]

    # Draw vehicles and calculate distances
    for pos in vehicle_positions:
        pygame.draw.circle(screen, green, pos, 5)
        distance = calculate_distance(center, pos)
        # Display coordinates and distance
        text = f"{pos[0]},{pos[1]} Jarak: {distance:.2f}"
        text_surface = font.render(text, True, green)
        screen.blit(text_surface, (pos[0] + 10, pos[1] - 25))  # Adjust text position

    pygame.display.flip()
    time.sleep(0.01)

pygame.quit()
sys.exit()
