'''
Bird class - отвечает за управление птицей в игре Flappy Bird.
'''
class Bird:
    def __init__(self):
        self.x = 10
        self.y = 10
        self.velocity = 0
        self.gravity = 0.5
        self.max_y = 20
    def flap(self):
        # Прыжок птицы
        self.velocity = -2
    def update(self):
        # Обновление положения птицы с учетом границ
        self.velocity += self.gravity
        self.y += self.velocity
        if self.y < 0:
            self.y = 0
        elif self.y > self.max_y:
            self.y = self.max_y