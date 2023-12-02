'''
Flappy Bird Console Game - основной файл игры, содержащий игровой цикл.
'''
import time
from pynput.keyboard import Listener, Key
from bird import Bird
from obstacles import Obstacles
from display import display_game
# Инициализация игровых компонентов
bird = Bird()
obstacles = Obstacles()
# Переменная состояния игры
running = True
game_over = False
def on_press(key):
    global running, game_over
    if game_over:
        if key == Key.esc:
            running = False
    elif key == Key.space:
        bird.flap()
# Обработчик событий клавиатуры
keyboard_listener = Listener(on_press=on_press)
keyboard_listener.start()
try:
    while running:
        if not game_over:
            # Обновление состояния игры
            bird.update()
            obstacles.update()
            # Проверка столкновений
            if obstacles.check_collision(bird.x, bird.y):
                game_over = True
        # Отображение игры в консоли
        display_game(bird, obstacles, game_over)
        # Ожидание перед следующим кадром
        time.sleep(0.1)
finally:
    keyboard_listener.stop()