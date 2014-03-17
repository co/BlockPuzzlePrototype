import copy
from itertools import izip, groupby
import random
from time import sleep
import pygame
import pygame.locals

import sys
from soundplayer import SoundPlayer


#  Sorry for the bad code this is a proof of concept  I threw together in an afternoon.


TILE_SIZE = 16
SCREEN_MULTIPLIER = 3

BOARD_WIDTH = 7
BOARD_HEIGHT = 7


PIXEL_SIZE = ((BOARD_WIDTH + 2) * TILE_SIZE, (BOARD_HEIGHT + 2) * TILE_SIZE)
SCREEN_SIZE = (PIXEL_SIZE[0] * SCREEN_MULTIPLIER, PIXEL_SIZE[1] * SCREEN_MULTIPLIER)


BG_COLOR = (0xc5, 0xbc, 0x8e)


CANVAS = pygame.display.set_mode(SCREEN_SIZE)
BOARD_POSITION = (TILE_SIZE, TILE_SIZE)


GAME_MOVE_CONTROLS =\
    {
        pygame.K_LEFT: (-1, 0),
        pygame.K_RIGHT: (1, 0),
        pygame.K_UP: (0, -1),
        pygame.K_DOWN: (0, 1)
    }

BACK = 0
FORWARD = 1

BLACK = 0
WHITE = 1
REMOVED = -1

SOUND_PLAYER = SoundPlayer()

pygame.init()
pygame.display.set_caption('LOL ITS A POZZL GAEM!!1!eleven1')



def add_2d(p1, p2):
    return p1[0] + p2[0], p1[1] + p2[1]


def load_tile_set(tileset_file_name):
    img = pygame.image.load(tileset_file_name)
    width = img.get_width() / TILE_SIZE
    height = img.get_height() / TILE_SIZE
    tiles = []
    for y in range(height):
        for x in range(width):
            tile_choice_rect = pygame.Rect((x * TILE_SIZE, y * TILE_SIZE),
                                         (TILE_SIZE, TILE_SIZE))
            tiles.append((img, tile_choice_rect))
    return tiles


def draw_cursor_position(cursor_position, tile_set, canvas):
    x, y = cursor_position
    cursor_graphic_index = 2
    position = add_2d(BOARD_POSITION, (x * TILE_SIZE, y * TILE_SIZE))
    canvas.blit(tile_set[cursor_graphic_index][0], position, tile_set[cursor_graphic_index][1])


def add_cursor_position(cursor_position, delta):
    new_x = (cursor_position[0] + delta[0]) % BOARD_WIDTH
    new_y = (cursor_position[1] + delta[1]) % BOARD_HEIGHT
    return new_x, new_y


class Board(object):
    def __init__(self, board):
        self._board = board

    def find_and_mark_full_rows(self):
        board_copy = copy.deepcopy(self._board)
        row_indexes = get_all_full_rows_in_matrix(board_copy)
        transposed_board = get_transposed_matrix(board_copy)
        column_indexes = get_all_full_rows_in_matrix(transposed_board)
        self.mark_deleted_rows_and_columns(row_indexes, column_indexes)

    def find_and_mark_bricks_to_clear(self):
        self.find_and_mark_full_rows()

    def update(self, frame_canvas):
        self.find_and_mark_bricks_to_clear()
        if self.any_removed():
            SOUND_PLAYER.play_sound("line_clear.wav")
            self.animate_brick_clear(frame_canvas)
        while self.any_removed():
            self.pieces_fall_step()
            SOUND_PLAYER.play_sound("short_blip.wav")
            self.draw(frame_canvas)
            pygame.display.update()
            sleep(0.1)

    def draw(self, canvas):
        frame_canvas.fill(BG_COLOR)
        self.prepare_draw(tile_set, canvas)
        draw_cursor_position(cursor_position, tile_set, canvas)
        scaled_canvas = pygame.transform.scale(canvas, SCREEN_SIZE)
        CANVAS.blit(scaled_canvas, (0, 0))

    def prepare_draw(self, tile_set, canvas):
        for y, row in enumerate(self._board):
            for x, brick in enumerate(row):
                positon = add_2d(BOARD_POSITION, (x * TILE_SIZE, y * TILE_SIZE))
                canvas.blit(tile_set[brick][0], positon, tile_set[brick][1])

    def any_removed(self):
        for row in self._board:
            for brick in row:
                if brick == REMOVED:
                    return True
        return False

    def shift_column(self, column_index, direction):
        board_copy = copy.deepcopy(self._board)
        transposed_board = get_transposed_matrix(board_copy)
        shifted_board = shift_matrix_row(transposed_board, column_index, direction)
        self._board = get_transposed_matrix(shifted_board)

    def shift_row(self, row_index, direction):
        self._board = shift_matrix_row(self._board, row_index, direction)

    def mark_deleted_rows_and_columns(self, row_indexes, column_indexes):
        for y, row in enumerate(self._board):
            for x, brick in enumerate(row):
                if y in row_indexes or x in column_indexes:
                    self._board[y][x] = REMOVED

    def animate_brick_clear(self, frame_canvas):
        for _ in range(2):
            self.draw(frame_canvas)
            pygame.display.update()

            sleep(0.05)
            self.draw_empty_board_flash(tile_set, frame_canvas)
            draw_cursor_position(cursor_position, tile_set, frame_canvas)
            scaled_canvas = pygame.transform.scale(frame_canvas, SCREEN_SIZE)
            CANVAS.blit(scaled_canvas, (0, 0))
            pygame.display.update()
            sleep(0.05)

    def draw_empty_board_flash(self, tile_set, canvas):
        flash_graphic_index = 3
        for y, row in enumerate(self._board):
            for x, brick in enumerate(row):
                if brick == REMOVED:
                    positon = add_2d(BOARD_POSITION, (x * TILE_SIZE, y * TILE_SIZE))
                    canvas.blit(tile_set[flash_graphic_index][0], positon, tile_set[flash_graphic_index][1])

    def pieces_fall_step(self):
        for y_reversed, row in enumerate(reversed(self._board)):
            for x, brick, in enumerate(row):
                if brick == REMOVED:
                    y = len(self._board) - y_reversed - 1
                    y_above = y - 1
                    if y_above == -1:  # At the top, grab random brick instead.
                        self._board[y][x] = self._get_new_brick()
                    else:
                        self._board[y][x] = self._board[y_above][x]
                        self._board[y_above][x] = REMOVED

    def _get_new_brick(self):
        return random.choice([0, 1])


class DiceBoard(Board):
    def __init__(self, board):
        super(DiceBoard, self).__init__(board)

    def _get_new_brick(self):
        return random.choice([8, 9, 10, 11, 12, 13])

    def find_and_mark_bricks_to_clear(self):
        board_copy = copy.deepcopy(self._board)
        row_points = find_all_three_in_a_row_points(board_copy)
        transposed_board = get_transposed_matrix(board_copy)
        column_points = find_all_three_in_a_row_points(transposed_board)
        column_points = set([e[::-1] for e in column_points])
        for point in row_points | column_points:
            self._board[point[1]][point[0]] = -1


def find_all_three_in_a_row_points(matrix):
    points = set()
    for y, row in enumerate(matrix):
        groups = [list(g) for k, g in groupby(row)]
        group_idx = 0
        for group in groups:
            if len(group) >= 3:
                for idx in range(len(group)):
                    points.add((group_idx + idx, y))
            group_idx += len(group)
    return points


def get_all_full_rows_in_matrix(matrix):
    full_rows = []
    for idx, row in enumerate(matrix):
        if all(e == row[0] for e in row):
            full_rows.append(idx)
    return full_rows


def shift_matrix_row(matrix, row_index, direction):
    row = matrix[row_index]
    new_row = None
    if direction == BACK:
        new_row = row[1:] + row[:1]
    if direction == FORWARD:
        new_row = row[-1:] + row[:-1]
    if new_row:
        changed_board = matrix[:]
        changed_board[row_index] = new_row
        return list(changed_board)
    return list(matrix)


def new_board():
    return Board([[random.choice([0, 1]) for _ in range(BOARD_WIDTH)] for _ in range(BOARD_WIDTH)])

def new_dice_board():
    return DiceBoard([[random.choice([8, 9, 10, 11, 12, 13]) for _ in range(BOARD_WIDTH)] for _ in range(BOARD_WIDTH)])

def get_transposed_matrix(matrix):
    return [list(e) for e in izip(*matrix)]



def draw_cursor_position(cursor_position, tile_set, canvas):
    x, y = cursor_position
    cursor_graphic_index = 2
    position = add_2d(BOARD_POSITION, (x * TILE_SIZE, y * TILE_SIZE))
    canvas.blit(tile_set[cursor_graphic_index][0], position, tile_set[cursor_graphic_index][1])


board = new_dice_board()
tile_set = load_tile_set("tileset.png")
frame_canvas = pygame.Surface(PIXEL_SIZE)
cursor_position = (BOARD_WIDTH / 2 + 1, BOARD_HEIGHT / 2 + 1)


while True:
    for event in pygame.event.get():
        if event.type == pygame.QUIT or (event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE):
            pygame.quit()
            sys.exit()
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_1:
                board = new_board()
            if event.key in GAME_MOVE_CONTROLS:
                cursor_position = add_cursor_position(cursor_position, GAME_MOVE_CONTROLS[event.key])
            if event.key == pygame.K_LEFT and event.mod & pygame.KMOD_CTRL:
                board.shift_row(cursor_position[1], BACK)
            if event.key == pygame.K_RIGHT and event.mod & pygame.KMOD_CTRL:
                board.shift_row(cursor_position[1], FORWARD)
            if event.key == pygame.K_UP and event.mod & pygame.KMOD_CTRL:
                board.shift_column(cursor_position[0], BACK)
            if event.key == pygame.K_DOWN and event.mod & pygame.KMOD_CTRL:
                board.shift_column(cursor_position[0], FORWARD)
    board.update(frame_canvas)

    board.draw(frame_canvas)
    pygame.display.update()



