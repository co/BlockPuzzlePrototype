from itertools import izip
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


def new_board():
    return [[random.choice([0, 1]) for _ in range(BOARD_WIDTH)] for _ in range(BOARD_WIDTH)]


def add_2d(p1, p2):
    return p1[0] + p2[0], p1[1] + p2[1]


def load_tile_set(tilesetFileName):
    img = pygame.image.load(tilesetFileName)
    width = img.get_width() / TILE_SIZE
    height = img.get_height() / TILE_SIZE
    tiles = []
    for y in range(height):
        for x in range(width):
            tileChoiceRect = pygame.Rect((x * TILE_SIZE, y * TILE_SIZE),
                                         (TILE_SIZE, TILE_SIZE))
            tiles.append((img, tileChoiceRect))
    return tiles


def prepare_draw_board(board, tile_set, canvas):
    for y, row in enumerate(board):
        for x, tile in enumerate(row):
            positon = add_2d(BOARD_POSITION, (x * TILE_SIZE, y * TILE_SIZE))
            canvas.blit(tile_set[tile][0], positon, tile_set[tile][1])

def draw_board_flash(board, tile_set, canvas):
    flash_graphic_index = 3
    for y, row in enumerate(board):
        for x, tile in enumerate(row):
            if tile == REMOVED:
                positon = add_2d(BOARD_POSITION, (x * TILE_SIZE, y * TILE_SIZE))
                canvas.blit(tile_set[flash_graphic_index][0], positon, tile_set[flash_graphic_index][1])

def draw_cursor_position(cursor_position, tile_set, canvas):
    x, y = cursor_position
    cursor_graphic_index = 2
    position = add_2d(BOARD_POSITION, (x * TILE_SIZE, y * TILE_SIZE))
    canvas.blit(tile_set[cursor_graphic_index][0], position, tile_set[cursor_graphic_index][1])


def add_cursor_position(cursor_position, delta):
    new_x = (cursor_position[0] + delta[0]) % BOARD_WIDTH
    new_y = (cursor_position[1] + delta[1]) % BOARD_HEIGHT

    return new_x, new_y


def shift_board_row(board, row_index, direction):
    row = board[row_index]
    new_row = None
    if direction == BACK:
        new_row = row[1:] + row[:1]
    if direction == FORWARD:
        new_row = row[-1:] + row[:-1]
    if new_row:
        changed_board = board[:]
        changed_board[row_index] = new_row
        return list(changed_board)
    return list(board)


def get_transposed_matrix(matrix):
    return [list(e) for e in izip(*matrix)]


def shift_board_column(board, column_index, direction):
    transposed_board = get_transposed_matrix(board)
    shifted_board = shift_board_row(transposed_board, column_index, direction)
    final_board = get_transposed_matrix(shifted_board)
    return final_board


def get_all_full_rows(board):
    full_rows = []
    for idx, row in enumerate(board):
        if all(e == row[0] for e in row):
            full_rows.append(idx)
    return full_rows


def mark_deleted_rows_and_columns(board, row_indexes, column_indexes):
    for y, row in enumerate(board):
        for x, tile in enumerate(row):
            if y in row_indexes or x in column_indexes:
                board[y][x] = REMOVED


def animate_line_clear(board, frame_canvas):
    for _ in range(2):
        draw_board(board, tile_set, frame_canvas)

        sleep(0.05)
        draw_board_flash(board, tile_set, frame_canvas)
        draw_cursor_position(cursor_position, tile_set, frame_canvas)
        scaled_canvas = pygame.transform.scale(frame_canvas, SCREEN_SIZE)
        CANVAS.blit(scaled_canvas, (0, 0))
        pygame.display.update()
        sleep(0.05)


def pieces_fall_step(board):
    new_board = board[:]
    for y_reversed, row in enumerate(reversed(board)):
        for x, tile, in enumerate(row):
            if tile == REMOVED:
                y = len(new_board) - y_reversed - 1
                y_above = y - 1
                if y_above == -1:  # At the top, grab random tile instead.
                    new_board[y][x] = random.choice([0, 1])
                else:
                    new_board[y][x] = new_board[y_above][x]
                    new_board[y_above][x] = REMOVED
    return new_board


def any_removed(board):
    for row in board:
        for tile in row:
            if tile == REMOVED:
                return True
    return False


def update_board(board, frame_canvas):
    next_board = board[:]
    row_indexes = get_all_full_rows(next_board)
    transposed_board = get_transposed_matrix(next_board)
    column_indexes = get_all_full_rows(transposed_board)
    mark_deleted_rows_and_columns(next_board, row_indexes, column_indexes)

    if not (len(row_indexes) == 0 and len(column_indexes) == 0):
        SOUND_PLAYER.play_sound("line_clear.wav")
        animate_line_clear(next_board, frame_canvas)
    while any_removed(next_board):
        next_board = pieces_fall_step(next_board)
        draw_board(next_board, tile_set, frame_canvas)
        sleep(0.1)
        SOUND_PLAYER.play_sound("short_blip.wav")
    return next_board

board = new_board()
tile_set = load_tile_set("tileset.png")
frame_canvas = pygame.Surface(PIXEL_SIZE)
cursor_position = (BOARD_WIDTH / 2 + 1, BOARD_HEIGHT / 2 + 1)


def draw_board(board, tile_set, frame_canvas):
    frame_canvas.fill(BG_COLOR)
    prepare_draw_board(board, tile_set, frame_canvas)
    draw_cursor_position(cursor_position, tile_set, frame_canvas)
    scaled_canvas = pygame.transform.scale(frame_canvas, SCREEN_SIZE)
    CANVAS.blit(scaled_canvas, (0, 0))
    pygame.display.update()


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
                board = shift_board_row(board, cursor_position[1], BACK)
            if event.key == pygame.K_RIGHT and event.mod & pygame.KMOD_CTRL:
                board = shift_board_row(board, cursor_position[1], FORWARD)
            if event.key == pygame.K_UP and event.mod & pygame.KMOD_CTRL:
                board = shift_board_column(board, cursor_position[0], BACK)
            if event.key == pygame.K_DOWN and event.mod & pygame.KMOD_CTRL:
                board = shift_board_column(board, cursor_position[0], FORWARD)
    board = update_board(board, frame_canvas)

    draw_board(board, tile_set, frame_canvas)
