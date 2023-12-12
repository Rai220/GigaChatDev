'''
This is the main file of the Flappy Bird game.
'''
import pygame
from bird import Bird
from pipe import Pipe
# Initialize the game
pygame.init()
# Set up the display
screen_width = 500
screen_height = 800
screen = pygame.display.set_mode((screen_width, screen_height))
pygame.display.set_caption("Flappy Bird")
# Set up the clock
clock = pygame.time.Clock()
# Set up the game objects
bird = Bird(screen_width, screen_height)
pipes = [Pipe(screen_width, screen_height)]
# Game loop
running = True
while running:
    # Event handling
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_SPACE:
                bird.jump()
    # Update game objects
    bird.update()
    for pipe in pipes:
        pipe.update(screen_height)
        if pipe.collides_with(bird):
            running = False
    # Generate new pipes
    if pipes[-1].x < screen_width - 200:
        pipes.append(Pipe(screen_width, screen_height))
    # Remove off-screen pipes
    if pipes[0].x < -pipes[0].width:
        pipes.pop(0)
    # Draw the game objects
    screen.fill((0, 0, 0))
    bird.draw(screen)
    for pipe in pipes:
        pipe.draw(screen)
    pygame.display.flip()
    # Limit the frame rate
    clock.tick(60)
# Quit the game
pygame.quit()