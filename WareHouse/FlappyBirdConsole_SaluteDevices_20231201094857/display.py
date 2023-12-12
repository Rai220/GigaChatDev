'''
display_game function - функция для отображения игрового поля, птицы и препятствий в консоли.
'''
def display_game(bird, obstacles, game_over):
    # Отображение игрового поля
    for y in range(0, 20):
        for x in range(0, 80):
            if x == bird.x and y == int(bird.y):
                print('@', end='')
            elif any((x >= obs_x and x < obs_x + obstacles.obstacle_width and (y < gap_y or y > gap_y + 5)) for obs_x, gap_y in obstacles.obstacles):
                print('#', end='')
            else:
                print(' ', end='')
        print()
    print('-' * 80)
    if game_over:
        print("Game Over! Press ESC to exit.")