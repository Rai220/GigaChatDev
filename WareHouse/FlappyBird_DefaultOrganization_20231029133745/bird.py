'''
This file contains the Bird class.
'''
import pygame
class Bird:
    def __init__(self, screen_width, screen_height):
        self.x = screen_width // 2
        self.y = screen_height // 2
        self.velocity = 0
        self.gravity = 0.5
        self.lift = -10
        self.radius = 20
    def jump(self):
        self.velocity += self.lift
    def update(self):
        self.velocity += self.gravity
        self.y += self.velocity
    def draw(self, screen):
        pygame.draw.circle(screen, (255, 255, 255), (self.x, int(self.y)), self.radius)