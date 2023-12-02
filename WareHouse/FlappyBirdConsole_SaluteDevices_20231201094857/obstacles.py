'''
Obstacles class - отвечает за генерацию и управление препятствиями в игре Flappy Bird.
'''
import random
class Obstacles:
    def __init__(self):
        self.obstacles = []
        self.width = 80
        self.spacing = 20
        self.obstacle_width = 3
    def update(self):
        # Движение препятствий и добавление новых
        self.obstacles = [(x-1, y) for x, y in self.obstacles if x > -self.obstacle_width]
        if len(self.obstacles) == 0 or self.obstacles[-1][0] < self.width - self.spacing:
            self.generate_obstacle()
    def generate_obstacle(self):
        # Генерация нового препятствия
        gap_y = random.randint(5, 15)
        self.obstacles.append((self.width, gap_y))
    def check_collision(self, bird_x, bird_y):
        # Проверка столкновения птицы с препятствием
        for x, y in self.obstacles:
            if bird_x >= x and bird_x < x + self.obstacle_width and (bird_y < y or bird_y > y + 5):
                return True
        return False