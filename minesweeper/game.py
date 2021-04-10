import random
from dataclasses import dataclass
from typing import List

EASY = (10, 8, 10)
MEDIUM = (18, 14, 40)
HARD = (24, 20, 99)


@dataclass
class Square:
    value: str
    is_flag: bool = False


def _to_squares(board):
    rows = []
    for row in board:
        rows += [[Square(v) for v in row]]
    return rows


def create_board(width: int, height: int, n_bombs: int):
    squares = list("*" * n_bombs + " " * (width * height - n_bombs))
    random.shuffle(squares)
    board = [squares[row * width : row * width + width] for row in range(height)]
    return _to_squares(number_board(board))


def number_board(board: List):
    for y, row in enumerate(board):
        for x, sq in enumerate(row):
            if sq == "*":
                bump_surrounding_squares(board, x, y)
    return board


def bump_surrounding_squares(board: List, x: int, y: int):
    surrounding_squares = [
        (x - 1, y - 1),
        (x, y - 1),
        (x + 1, y - 1),
        (x - 1, y),
        (x + 1, y),
        (x - 1, y + 1),
        (x, y + 1),
        (x + 1, y + 1),
    ]
    h, w = len(board), len(board[0])
    for _x, _y in surrounding_squares:
        if 0 <= _x < w and 0 <= _y < h and board[_y][_x] != "*":
            v = 1 if board[_y][_x] == " " else int(board[_y][_x]) + 1
            board[_y][_x] = str(v)
