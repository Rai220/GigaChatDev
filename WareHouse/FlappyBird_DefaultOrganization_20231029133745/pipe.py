'''
This file contains the Pipe class.
'''
import pygame
import random
class Pipe:
    def __init__(self, screen_width, screen_height):
        self.x = screen_width
        self.width = 80
        self.gap = 200
        self.top_height = random.randint(100, 400)
        self.bottom_height = screen_height - self.top_height - self.gap
        self.speed = 5
        self.screen_width = screen_width
        self.screen_height = screen_height
    def update(self, screen_height):
        self.x -= self.speed
    def collides_with(self, bird):
        if bird.y - bird.radius < self.top_height or bird.y + bird.radius > self.screen_height - self.bottom_height:
            if bird.x + bird.radius > self.x and bird.x - bird.radius < self.x + self.width:
                return True
        return False
    def draw(self, screen):
        pygame.draw.rect(screen, (0, 255, 0), (self.x, 0, self.width, self.top_height))
        pygame.draw.rect(screen, (0, 255, 0), (self.x, self.screen_height - self.bottom_height, self.width, self.bottom_height))