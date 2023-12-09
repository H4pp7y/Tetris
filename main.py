import json

import pygame
import pygame as pg
import random
import time
import sys
import sqlite3
from pygame import mixer
from pygame.locals import *

fps = 25
window_w, window_h = 600, 500
block, cup_h, cup_w = 20, 20, 10
# conn = sqlite3.connect('tetris.db')
# cursor = conn.cursor()
# cursor.execute('CREATE TABLE IF NOT EXISTS scores (id INTEGER PRIMARY KEY AUTOINCREMENT, score INTEGER)')
# conn.commit()
# conn.close() создание базы данных
side_freq, down_freq = 0.15, 0.1  # передвижение в сторону и вниз

side_margin = int((window_w - cup_w * block) / 2)
top_margin = window_h - (cup_h * block) - 5

colors = ((0, 0, 225), (0, 225, 0), (225, 0, 0), (225, 225, 0))  # синий, зеленый, красный, желтый
lightcolors = ((30, 30, 255), (50, 255, 50), (255, 30, 30),
               (255, 255, 30))  # светло-синий, светло-зеленый, светло-красный, светло-желтый

white, gray, black = (255, 255, 255), (185, 185, 185), (0, 0, 0)
brd_color, bg_color, txt_color, title_color, info_color = white, black, white, colors[3], colors[0]

fig_w, fig_h = 5, 5
empty = 'o'


class Tetris:
    def __init__(self, block, cup_h, cup_w, side_freq, down_freq, window_w, window_h, colors, lightcolors,
                 white, gray, black, brd_color, bg_color, txt_color, title_color, info_color, fig_w, fig_h, empty,
                 figures_filename):
        self.pg_init()
        self.conn = sqlite3.connect('tetris.db')
        self.cursor = self.conn.cursor()
        self.block = block
        self.cup_h, self.cup_w = cup_h, cup_w
        self.side_freq, self.down_freq = side_freq, down_freq
        self.window_w, self.window_h = window_w, window_h
        self.fps = 25
        self.sound = pygame.mixer.Sound("Sounds/bgMusic.mp3")
        self.sound_flash = pygame.mixer.Sound("Sounds/lineFlash.mp3")
        self.last_move_down = time.time()
        self.last_side_move = time.time()
        self.last_fall = time.time()
        self.going_down = False
        self.going_left = False
        self.going_right = False
        self.points = 0
        self.level, self.fall_speed = self.calc_speed(self.points)

        self.window_w, self.window_h = 600, 500
        self.block, self.cup_h, self.cup_w = 20, 20, 10

        self.side_freq, self.down_freq = 0.15, 0.1

        self.side_margin = int((self.window_w - self.cup_w * self.block) / 2)
        self.top_margin = self.window_h - (self.cup_h * self.block) - 5

        self.colors = ((0, 0, 225), (0, 225, 0), (225, 0, 0), (225, 225, 0))
        self.lightcolors = ((30, 30, 255), (50, 255, 50), (255, 30, 30), (255, 255, 30))

        self.white, self.gray, self.black = (255, 255, 255), (185, 185, 185), (0, 0, 0)
        self.brd_color, self.bg_color, self.txt_color, self.title_color, self.info_color = \
            self.white, self.black, self.white, self.colors[3], self.colors[0]

        self.fig_w, self.fig_h = 5, 5
        self.empty = 'o'

        with open(figures_filename, 'r') as file:
            self.figures = json.load(file)

        self.pause_screen = pg.Surface((600, 500), pg.SRCALPHA)
        self.pause_screen.fill((0, 0, 255, 127))
        self.cup = self.empty_cup()
        self.fps_clock = pg.time.Clock()
        self.display_surf = pg.display.set_mode((self.window_w, self.window_h))
        self.basic_font = pg.font.SysFont('calibri', 20)
        self.big_font = pg.font.SysFont('calibri', 45)
        pg.display.set_caption('Тетрис')
        self.block = block
        self.cup_w, self.cup_h = cup_w, cup_h
        self.fig_w, self.fig_h = fig_w, fig_h
        self.empty = empty
        self.pause_screen = pg.Surface((window_w, window_h), pg.SRCALPHA)
        self.pause_screen.fill((0, 0, 255, 127))
        self.fps_clock = None
        self.display_surf = None
        self.basic_font = None
        self.big_font = None
        self.colors = colors
        self.cup = self.empty_cup()
        self.lightcolors = lightcolors
        self.white, self.gray, self.black = white, gray, black
        self.brd_color, self.bg_color, self.txt_color, self.title_color, self.info_color = brd_color, bg_color, txt_color, title_color, info_color
        self.empty = empty
        self.falling_fig = self.get_new_fig()
        self.next_fig = self.get_new_fig()
        self.high_score = self.load_high_score()
        self.title_color = (0, 255, 127)
        self.info_color = (0, 255, 255)
        self.txt_color = (255, 255, 255)

    def get_new_fig(self):
        shape = random.choice(list(self.figures.keys()))
        new_figure = {'shape': shape,
                      'rotation': random.randint(0, len(self.figures[shape]) - 1),
                      'x': int(self.cup_w / 2) - int(self.fig_w / 2),
                      'y': -2,
                      'color': random.randint(0, len(self.colors) - 1)}
        return new_figure

    def pg_init(self):
        pg.init()
        mixer.init()

    def show_pause_screen(self):
        self.display_surf.blit(self.pause_screen, (0, 0))
        pg.display.update()

    def show_text(self, text):
        title_surf, title_rect = self.txt_objects(text, self.big_font, self.title_color)
        title_rect.center = (int(self.window_w / 2) - 3, int(self.window_h / 2) - 3)
        self.display_surf.blit(title_surf, title_rect)

        press_key_surf, press_key_rect = self.txt_objects('Нажмите любую клавишу для продолжения', self.basic_font,
                                                          self.title_color)
        press_key_rect.center = (int(self.window_w / 2), int(self.window_h / 2) + 100)
        self.display_surf.blit(press_key_surf, press_key_rect)

        while self.check_keys() is None:
            pg.display.update()
            self.fps_clock.tick()

    def check_keys(self):
        for event in pg.event.get():
            if event.type == KEYDOWN or event.type == KEYUP:
                return event.key
        return None

    def stop_game(self):
        self.save_high_score(self.high_score)  # Save high score before quitting
        pg.quit()
        sys.exit()

    def reset_game(self):
        self.falling_fig = None
        self.points = 0
        self.level, self.fall_speed = self.calc_speed(self.points)
        self.cup = self.empty_cup()
        self.falling_fig = self.get_new_fig()
        self.next_fig = self.get_new_fig()
        self.paused = False
        self.display_surf.fill((30, 30, 255, 127), special_flags=pg.BLEND_RGBA_MULT)
        self.high_score = self.load_high_score()

    paused = False

    def run_tetris(self):
        while True:
            if self.falling_fig is None:
                self.falling_fig = self.next_fig
                self.next_fig = self.get_new_fig()
                self.last_fall = time.time()
                self.save_high_score(self.high_score)  # Save high score

                if not self.check_pos(self.cup, self.falling_fig):
                    self.cup = self.empty_cup()
                    self.points = 0
                    self.level, self.fall_speed = self.calc_speed(self.points)
                    self.falling_fig = self.get_new_fig()
                    self.display_surf.fill((self.bg_color[0], self.bg_color[1], 255, 127),
                                           special_flags=pg.BLEND_RGBA_MULT)
                    self.show_text('Игра закончилась')
                    self.reset_game()

            self.quit_game()
            if self.points > self.high_score:
                self.high_score = self.points  # Update the high score
            for event in pg.event.get():
                if event.type == pg.KEYUP:
                    if event.key == pg.K_SPACE:
                        self.paused = not self.paused
                        if self.paused:
                            self.show_pause_screen()
                            self.show_text('Пауза')
                            self.last_fall = time.time()
                            self.last_move_down = time.time()
                            self.last_side_move = time.time()
                            self.going_down = False
                            self.going_left = False
                            self.going_right = False
                        else:
                            self.last_move_down = time.time()
                            self.last_side_move = time.time()
                    elif event.key == pg.K_LEFT:
                        self.going_left = False
                    elif event.key == pg.K_RIGHT:
                        self.going_right = False
                    elif event.key == pg.K_DOWN:
                        self.going_down = False
                    elif event.key == pg.K_RETURN:
                        self.going_down = False
                        self.going_left = False
                        self.going_right = False
                        for i in range(1, self.cup_h):
                            if not self.check_pos(self.cup, self.falling_fig, adjY=i):
                                break
                    elif event.key == pg.K_r:  # Handle the "R" key for restart
                        self.reset_game()

                elif event.type == pg.KEYDOWN:
                    if event.key == pg.K_LEFT and self.check_pos(self.cup, self.falling_fig, adjX=-1):
                        self.falling_fig['x'] -= 1
                        self.going_left = True
                        self.going_right = False
                        self.last_side_move = time.time()
                    elif event.key == pg.K_RIGHT and self.check_pos(self.cup, self.falling_fig, adjX=1):
                        self.falling_fig['x'] += 1
                        self.going_right = True
                        self.going_left = False
                        self.last_side_move = time.time()
                    elif event.key == pg.K_UP:
                        self.falling_fig['rotation'] = (self.falling_fig['rotation'] + 1) % len(
                            self.figures[self.falling_fig['shape']])
                        if not self.check_pos(self.cup, self.falling_fig):
                            self.falling_fig['rotation'] = (self.falling_fig['rotation'] - 1) % len(
                                self.figures[self.falling_fig['shape']])
                    elif event.key == pg.K_DOWN:
                        self.going_down = True
                        if self.check_pos(self.cup, self.falling_fig, adjY=1):
                            self.falling_fig['y'] += 1
                        self.last_move_down = time.time()
                    elif event.key == pg.K_RETURN:
                        self.going_down = False
                        self.going_left = False
                        self.going_right = False
                        for i in range(1, self.cup_h):
                            if not self.check_pos(self.cup, self.falling_fig, adjY=i):
                                break
                        self.falling_fig['y'] += i - 1

            if not self.paused:  # Добавьте проверку состояния паузы
                if (self.going_left or self.going_right) and time.time() - self.last_side_move > self.side_freq:
                    if self.going_left and self.check_pos(self.cup, self.falling_fig, adjX=-1):
                        self.falling_fig['x'] -= 1
                    elif self.going_right and self.check_pos(self.cup, self.falling_fig, adjX=1):
                        self.falling_fig['x'] += 1
                    self.last_side_move = time.time()

                if self.going_down and time.time() - self.last_move_down > self.down_freq and self.check_pos(self.cup,
                                                                                                             self.falling_fig,
                                                                                                             adjY=1):
                    self.falling_fig['y'] += 1
                    self.last_move_down = time.time()

                if time.time() - self.last_fall > self.fall_speed:
                    if not self.check_pos(self.cup, self.falling_fig, adjY=1):
                        self.add_to_cup(self.cup, self.falling_fig)
                        self.points += self.clear_completed(self.cup)
                        self.level, self.fall_speed = self.calc_speed(self.points)
                        self.falling_fig = None
                    else:
                        self.falling_fig['y'] += 1
                        self.last_fall = time.time()

            self.display_surf.fill(self.bg_color)
            self.draw_title()
            self.game_cup(self.cup)
            self.draw_info(self.points, self.level)
            self.draw_next_fig(self.next_fig)
            if self.falling_fig is not None:
                self.draw_fig(self.falling_fig)
            pg.display.update()
            self.fps_clock.tick(self.fps)

    def txt_objects(self, text, font, color):
        surf = font.render(text, True, color)
        return surf, surf.get_rect()

    def quit_game(self):
        for event in pg.event.get(QUIT):
            self.stop_game()
        for event in pg.event.get(KEYUP):
            if event.key == K_ESCAPE:
                self.stop_game()
            pg.event.post(event)

    def calc_speed(self, points):
        level = int(points / 10) + 1
        fall_speed = 0.27 - (level * 0.02)
        return level, fall_speed

    def add_to_cup(self, cup, fig):
        for x in range(self.fig_w):
            for y in range(self.fig_h):
                if self.figures[fig['shape']][fig['rotation']][y][x] != self.empty:
                    cup[x + fig['x']][y + fig['y']] = fig['color']

    def empty_cup(self):
        cup = []
        for i in range(self.cup_w):
            cup.append([self.empty] * self.cup_h)
        return cup

    def in_cup(self, x, y):
        return x >= 0 and x < self.cup_w and y < self.cup_h

    def check_pos(self, cup, fig, adjX=0, adjY=0):
        for x in range(self.fig_w):
            for y in range(self.fig_h):
                above_cup = y + fig['y'] + adjY < 0
                if above_cup or self.figures[fig['shape']][fig['rotation']][y][x] == self.empty:
                    continue
                if not self.in_cup(x + fig['x'] + adjX, y + fig['y'] + adjY):
                    return False
                if cup[x + fig['x'] + adjX][y + fig['y'] + adjY] != self.empty:
                    return False
        return True

    def is_completed(self, cup, y):
        for x in range(self.cup_w):
            if cup[x][y] == self.empty:
                return False
        return True

    def clear_completed(self, cup):
        removed_lines = 0
        y = self.cup_h - 1
        while y >= 0:
            if self.is_completed(cup, y):
                # Create a copy of the line to draw the flash effect
                flash_line = list(cup[x][y] for x in range(self.cup_w))

                # Flash effect: change the color for a short duration
                for _ in range(3):
                    self.draw_flash_line(flash_line, y)
                    pg.display.update()
                    pg.time.wait(100)
                    self.game_cup(cup)
                    pg.display.update()
                    pg.time.wait(100)

                # Remove the completed line
                for push_down_y in range(y, 0, -1):
                    for x in range(self.cup_w):
                        cup[x][push_down_y] = cup[x][push_down_y - 1]
                for x in range(self.cup_w):
                    cup[x][0] = self.empty
                removed_lines += 1
            else:
                y -= 1
        return removed_lines

    def convert_coords(self, block_x, block_y):
        return (self.side_margin + (block_x * self.block)), (self.top_margin + (block_y * self.block))

    def draw_block(self, block_x, block_y, color, pixelx=None, pixely=None):
        if color == self.empty:
            return
        if pixelx is None and pixely is None:
            pixelx, pixely = self.convert_coords(block_x, block_y)
        pg.draw.rect(self.display_surf, self.colors[color],
                     (pixelx + 1, pixely + 1, self.block - 1, self.block - 1), 0, 3)
        pg.draw.rect(self.display_surf, self.lightcolors[color],
                     (pixelx + 1, pixely + 1, self.block - 4, self.block - 4), 0, 3)
        pg.draw.circle(self.display_surf, self.colors[color],
                       (pixelx + self.block / 2, pixely + self.block / 2), 5)

    def load_high_score(self):
        try:
            # Используем SQL-запрос для извлечения лучшего рекорда из базы данных
            self.cursor.execute('SELECT MAX(score) FROM scores')
            result = self.cursor.fetchone()
            if result and result[0] is not None:
                return result[0]  # Возвращаем только лучший рекорд
            else:
                return 0
        except sqlite3.Error as e:
            print(f"Ошибка при загрузке лучшего рекорда: {e}")
            return 0

    def save_high_score(self, high_score):
        try:
            # Используем SQL-запрос для сохранения рекорда в базе данных
            self.cursor.execute('INSERT INTO scores (score) VALUES (?)', (high_score,))
            self.conn.commit()
        except sqlite3.Error as e:
            print(f"Ошибка при сохранении рекорда: {e}")

    def game_cup(self, cup):
        pg.draw.rect(self.display_surf, self.brd_color, (
            self.side_margin - 4, self.top_margin - 4, (self.cup_w * self.block) + 8,
            (self.cup_h * self.block) + 8), 5)
        pg.draw.rect(self.display_surf, self.bg_color,
                     (self.side_margin, self.top_margin, self.block * self.cup_w, self.block * self.cup_h))
        for x in range(self.cup_w):
            for y in range(self.cup_h):
                self.draw_block(x, y, cup[x][y])

    def draw_title(self):
        title_surf = self.big_font.render('Тетрис', True, self.title_color)
        title_rect = title_surf.get_rect()
        title_rect.topleft = (self.window_w - 375, 30)
        self.display_surf.blit(title_surf, title_rect)

    def draw_info(self, points, level):
        info_font = pg.font.SysFont('arial', 20)

        high_score_surf = self.basic_font.render(f'Рекорд: {self.high_score}', True, self.txt_color)
        high_score_rect = high_score_surf.get_rect()
        high_score_rect.topleft = (self.window_w - 550, 150)
        self.display_surf.blit(high_score_surf, high_score_rect)

        points_surf = info_font.render(f'Баллы: {points}', True, self.txt_color)
        points_rect = points_surf.get_rect()
        points_rect.topleft = (self.window_w - 550, 180)
        self.display_surf.blit(points_surf, points_rect)

        level_surf = info_font.render(f'Уровень: {level}', True, self.txt_color)
        level_rect = level_surf.get_rect()
        level_rect.topleft = (self.window_w - 550, 250)
        self.display_surf.blit(level_surf, level_rect)

        pauseb_surf = info_font.render('Пауза: пробел', True, self.info_color)
        pauseb_rect = pauseb_surf.get_rect()
        pauseb_rect.topleft = (self.window_w - 550, 400)
        self.display_surf.blit(pauseb_surf, pauseb_rect)

        escb_surf = info_font.render('Выход: Esc', True, self.info_color)
        escb_rect = escb_surf.get_rect()
        escb_rect.topleft = (self.window_w - 550, 430)
        self.display_surf.blit(escb_surf, escb_rect)

        restart_surf = info_font.render('Перезапуск: R', True, self.info_color)
        restart_rect = restart_surf.get_rect()
        restart_rect.topleft = (self.window_w - 550, 460)
        self.display_surf.blit(restart_surf, restart_rect)

    def draw_fig(self, fig, pixelx=None, pixely=None):
        fig_to_draw = self.figures[fig['shape']][fig['rotation']]
        if pixelx is None and pixely is None:
            pixelx, pixely = self.convert_coords(fig['x'], fig['y'])
        for x in range(self.fig_w):
            for y in range(self.fig_h):
                if fig_to_draw[y][x] != self.empty:
                    self.draw_block(None, None, fig['color'], pixelx + (x * self.block),
                                    pixely + (y * self.block))

    def draw_next_fig(self, fig):
        next_surf = self.basic_font.render('Следующая:', True, self.txt_color)
        next_rect = next_surf.get_rect()
        next_rect.topleft = (self.window_w - 150, 180)
        self.display_surf.blit(next_surf, next_rect)
        self.draw_fig(fig, pixelx=self.window_w - 150, pixely=230)

    def draw_flash_line(self, line, y):
        self.sound_flash.play()
        for x in range(self.cup_w):
            # Генерируем случайный цвет для каждого блока в строке
            flash_color = (random.randint(0, 255), random.randint(0, 255), random.randint(0, 255))

            pg.draw.rect(self.display_surf, flash_color,
                         (self.side_margin + (x * self.block) + 1,
                          self.top_margin + (y * self.block) + 1,
                          self.block - 1, self.block - 1), 0, 3)
            pg.draw.rect(self.display_surf, self.lightcolors[line[x]],
                         (self.side_margin + (x * self.block) + 1,
                          self.top_margin + (y * self.block) + 1,
                          self.block - 4, self.block - 4), 0, 3)
            pg.draw.circle(self.display_surf, flash_color,
                           (self.side_margin + (x * self.block) + self.block / 2,
                            self.top_margin + (y * self.block) + self.block / 2), 5)

    def main(self):
        self.pg_init()
        self.fps_clock = pg.time.Clock()
        self.display_surf = pg.display.set_mode((self.window_w, self.window_h))
        self.basic_font = pg.font.SysFont('arial', 20)
        self.big_font = pg.font.SysFont('verdana', 45)
        pg.display.set_caption('Тетрис')
        self.show_text('Тетрис')
        self.reset_game()
        self.sound.play()
        while True:
            self.run_tetris()
            self.show_pause_screen()


if __name__ == '__main__':
    tetris_game = Tetris(block, cup_h, cup_w, side_freq, down_freq, window_w, window_h, colors, lightcolors,
                         white, gray, black, brd_color, bg_color, txt_color, title_color, info_color, fig_w, fig_h,
                         empty, "figures.json")
    tetris_game.main()
