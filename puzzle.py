import copy
from itertools import izip, groupby
import random
from time import sleep
import math
import pygame
import pygame.locals
import sys
from soundplayer import SoundPlayer


#  Sorry for the bad code this is a proof of concept  I threw together in an afternoon.


TILE_SIZE = 16
SCREEN_MULTIPLIER = 3

BOARD_OFFSET = TILE_SIZE

BOARD_WIDTH = 7
BOARD_HEIGHT = 7


PIXEL_SIZE = ((BOARD_WIDTH + 1) * TILE_SIZE + BOARD_OFFSET, (BOARD_HEIGHT + 1) * TILE_SIZE + BOARD_OFFSET)
SCREEN_SIZE = (PIXEL_SIZE[0] * SCREEN_MULTIPLIER, PIXEL_SIZE[1] * SCREEN_MULTIPLIER)


BG_COLOR = (0xc5, 0xbc, 0x8e)


CANVAS = pygame.display.set_mode(SCREEN_SIZE)
BOARD_POSITION = (TILE_SIZE, TILE_SIZE)

LEFT = (-1, 0)
RIGHT = (1, 0)
UP = (0, -1)
DOWN = (0, 1)

GAME_MOVE_CONTROLS =\
    {
        pygame.K_LEFT: LEFT,
        pygame.K_RIGHT: RIGHT,
        pygame.K_UP: UP,
        pygame.K_DOWN: DOWN
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


#def draw_cursor_position(cursor_position, tile_set, canvas):
#    x, y = cursor_position
#    cursor_graphic_index = 2
#    position = add_2d(BOARD_POSITION, (x * TILE_SIZE, y * TILE_SIZE))
#    canvas.blit(tile_set[cursor_graphic_index][0], position, tile_set[cursor_graphic_index][1])
#

# Remove?
def add_cursor_position(cursor_position, delta):
    new_x = (cursor_position[0] + delta[0]) % BOARD_WIDTH
    new_y = (cursor_position[1] + delta[1]) % BOARD_HEIGHT
    return new_x, new_y


class Board(object):
    def __init__(self, board, offset):
        self._board = board
        self.rect = pygame.Rect(offset, offset, TILE_SIZE * len(board[0]), TILE_SIZE * len(board))

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

    def push_action(self, position, direction):
        if direction == LEFT:
            self.shift_row(position[1], BACK)
        elif direction == RIGHT:
            self.shift_row(position[1], FORWARD)
        if direction == UP:
            self.shift_column(position[0], BACK)
        elif direction == DOWN:
            self.shift_column(position[0], FORWARD)

    def draw(self, canvas):
        frame_canvas.fill(BG_COLOR)
        self.prepare_draw(tile_set, canvas)

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
    def __init__(self, board, offset):
        super(DiceBoard, self).__init__(board, offset)

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

    def push_action(self, position, direction):
        destination = (((position[0] + direction[0]) % len(self._board)),
                       ((position[1] + direction[1]) % len(self._board)))
        self.push_dice_dot(position, destination)

    def push_dice_dot(self, start, destination):
        sx, sy = start
        dx, dy = destination
        start_brick = self._board[sy][sx]
        destination_brick = self._board[dy][dx]

        dice_tile_offset = 8

        if start_brick == dice_tile_offset or destination_brick == dice_tile_offset + 5:
            return

        self._board[sy][sx] -= 1
        self._board[dy][dx] += 1


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
    return Board([[random.choice([0, 1]) for _ in range(BOARD_WIDTH)] for _ in range(BOARD_WIDTH)], BOARD_OFFSET)

def new_dice_board():
    return DiceBoard([[random.choice([8, 9, 10, 11, 12, 13]) for _ in range(BOARD_WIDTH)] for _ in range(BOARD_WIDTH)],
                     BOARD_OFFSET)

def get_transposed_matrix(matrix):
    return [list(e) for e in izip(*matrix)]


class Cursor(object):
    def __init__(self, position):
        self._rect = pygame.Rect(position, (1, 1))

    def set_position(self, position, board):
        #x, y = position
        self._rect.topleft = position
        self._rect.clamp(board.rect)

    def get_position(self):
        return self._rect.topleft

    def draw(self, canvas):
        x, y = self.get_position()
        cursor_graphic_index = 2
        position = add_2d((BOARD_OFFSET, BOARD_OFFSET), (x * TILE_SIZE, y * TILE_SIZE))
        canvas.blit(tile_set[cursor_graphic_index][0], position, tile_set[cursor_graphic_index][1])


def screen_to_board_position(screen_position):
    screen_tile_width = TILE_SIZE * SCREEN_MULTIPLIER
    return ((screen_position[0] - screen_board_offset) / screen_tile_width,
            (screen_position[1] - screen_board_offset) / screen_tile_width)


board = new_dice_board()
tile_set = load_tile_set("tileset.png")
frame_canvas = pygame.Surface(PIXEL_SIZE)
cursor = Cursor((BOARD_WIDTH / 2 + 1, BOARD_HEIGHT / 2 + 1))
selected_board_point = None

while True:
    for event in pygame.event.get():
        if event.type == pygame.QUIT or (event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE):
            pygame.quit()
            sys.exit()
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_1:
                board = new_board()
            if event.key == pygame.K_2:
                board = new_dice_board()
            if event.key in GAME_MOVE_CONTROLS and event.mod & pygame.KMOD_CTRL:
                board.push_action(cursor.get_position(), GAME_MOVE_CONTROLS[event.key])
            elif event.key in GAME_MOVE_CONTROLS:
                cursor.set_position(add_2d(cursor.get_position(), GAME_MOVE_CONTROLS[event.key]), board)

        elif event.type == pygame.MOUSEBUTTONDOWN:
            pygame.mouse.get_rel()  # reset rel
            selected_board_point = screen_to_board_position(event.pos)

        elif event.type == pygame.MOUSEBUTTONUP:
            mouse_movement = pygame.mouse.get_rel()  # reset rel
            if math.sqrt(mouse_movement[0] ** 2 + mouse_movement[1] ** 2) > TILE_SIZE * SCREEN_MULTIPLIER * 0.6:
                directions = [RIGHT, DOWN, LEFT, UP]
                distances = [mouse_movement[0], mouse_movement[1], abs(mouse_movement[0]), abs(mouse_movement[1])]
                chosen_direction = directions[distances.index(max(distances))]
                board.push_action(selected_board_point, chosen_direction)

        if event.type == pygame.MOUSEMOTION:
            screen_board_offset = BOARD_OFFSET * SCREEN_MULTIPLIER
            cursor.set_position(screen_to_board_position(event.pos), board)
    board.update(frame_canvas)

    board.draw(frame_canvas)
    cursor.draw(frame_canvas)
    scaled_canvas = pygame.transform.scale(frame_canvas, SCREEN_SIZE)
    CANVAS.blit(scaled_canvas, (0, 0))
    pygame.display.update()



