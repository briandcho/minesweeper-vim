import random
from dataclasses import dataclass
from itertools import chain
from typing import List, Tuple

EASY = (10, 8, 10)
MEDIUM = (18, 14, 40)
HARD = (24, 20, 99)


@dataclass
class Cell:
    value: str
    is_flag: bool = False
    is_swept: bool = False


def _to_cells(board):
    rows = []
    for row in board:
        rows += [[Cell(v) for v in row]]
    return rows


def next_unswept(board: List[List[Cell]], x: int, y: int) -> Tuple[int, int]:
    h, w = len(board), len(board[0])
    i = next((i for i in range(x, w) if board[y][i].is_swept), x)
    i = next((i for i in range(i, w) if not board[y][i].is_swept), x)
    if i == x:
        if y + 1 < h:
            y += 1
            i = next((i for i in range(0, w) if not board[y][i].is_swept), 0)
        else:
            i = w - 1
    return (i, y)


def is_win(board: List[List[Cell]]) -> bool:
    n = {EASY[1]: EASY, MEDIUM[1]: MEDIUM, HARD[1]: HARD}[len(board)][2]
    return [cell.is_swept for cell in chain(*board)].count(False) == n


def create_board(width: int, height: int, n_bombs: int):
    cells = list("*" * n_bombs + " " * (width * height - n_bombs))
    random.shuffle(cells)
    board = [cells[row * width : row * width + width] for row in range(height)]
    return _to_cells(number_board(board))


def number_board(board: List):
    for y, row in enumerate(board):
        for x, sq in enumerate(row):
            if sq == "*":
                bump_neighbor_cells(board, x, y)
    return board


def bump_neighbor_cells(board: List, x: int, y: int):
    for _x, _y in _get_neighbor_cells(board, x, y):
        if board[_y][_x] != "*":
            v = 1 if board[_y][_x] == " " else int(board[_y][_x]) + 1
            board[_y][_x] = str(v)


def _get_neighbor_cells(board: List, x: int, y: int) -> List[Tuple[int, int]]:
    neighbor_cells = [
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
    return [(_x, _y) for _x, _y in neighbor_cells if 0 <= _x < w and 0 <= _y < h]
