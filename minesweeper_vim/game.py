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


Board = List[List[Cell]]


@dataclass
class Game:
    width: int
    height: int
    n_mines: int
    board: Board


def create_game(width: int, height: int, n_mines: int) -> Game:
    cells = list("*" * n_mines + " " * (width * height - n_mines))
    random.shuffle(cells)
    board = [
        cells[row * width : row * width + width] for row in range(height)  # noqa E203
    ]
    return Game(width, height, n_mines, _to_cells(number_board(board)))


def _to_cells(board) -> Board:
    rows = []
    for row in board:
        rows += [[Cell(v) for v in row]]
    return rows


def cell_at(board: List[List[Cell]], x: int, y: int) -> Cell:
    return board[y][x]


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


def prev_unswept(board: List[List[Cell]], x: int, y: int) -> Tuple[int, int]:
    w = len(board[0])
    i = next((i for i in reversed(range(0, x + 1)) if board[y][i].is_swept), x)
    i = next((i for i in reversed(range(0, i + 1)) if not board[y][i].is_swept), x)
    if i == x:
        if y - 1 >= 0:
            y -= 1
            i = next((i for i in reversed(range(0, w)) if not board[y][i].is_swept), w)
        else:
            i = 0
    return (i, y)


def is_win(board: List[List[Cell]]) -> bool:
    n = {EASY[1]: EASY, MEDIUM[1]: MEDIUM, HARD[1]: HARD}[len(board)][2]
    return [cell.is_swept for cell in chain(*board)].count(False) == n


def is_loss(board: List[List[Cell]]) -> bool:
    return any(cell.is_swept and cell.value == "*" for cell in chain(*board))


def number_board(board: List):
    for y, row in enumerate(board):
        for x, sq in enumerate(row):
            if sq == "*":
                bump_neighbor_cells(board, x, y)
    return board


def bump_neighbor_cells(board: List, x: int, y: int):
    for _x, _y in get_neighbor_cells(board, x, y):
        if board[_y][_x] != "*":
            v = 1 if board[_y][_x] == " " else int(board[_y][_x]) + 1
            board[_y][_x] = str(v)


def get_unmarked_neighbor_cells(board: List, x: int, y: int) -> List[Tuple[int, int]]:
    unswept_cells = get_unswept_neighbor_cells(board, x, y)
    n_flags = [board[y][x].is_flag for (x, y) in unswept_cells].count(True)
    cell = board[y][x]
    if n_flags == int(0 if cell.value == " " else cell.value):
        return [(x, y) for x, y in unswept_cells if not cell.is_flag]
    return []


def get_unswept_neighbor_cells(board: List, x: int, y: int) -> List[Tuple[int, int]]:
    xys = get_neighbor_cells(board, x, y)
    return [(x, y) for x, y in xys if not board[y][x].is_swept]


def get_neighbor_cells(board: List, x: int, y: int) -> List[Tuple[int, int]]:
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
