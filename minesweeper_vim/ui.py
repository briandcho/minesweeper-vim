import curses
from collections import namedtuple
from dataclasses import dataclass
from datetime import datetime
from typing import Callable, Generator, List, Tuple

import typer

from minesweeper_vim import game


@dataclass
class StateRule:
    next_state: int
    cond: Callable


def lex(stdscr) -> Generator:
    """
    /[$0HLM]|[1-9]?[bhjklmwx\n]|:\S+/
    ```mermaid
    graph LR
    subgraph lex
        0((0))--"[$0HLMbhjklmwx\n]"-->0
        0--"[1-9]"-->1((1))
        0--:-->2((2))
        1--"[$0HLMbhjklmwx\n]"-->0
        2--"q"-->3
        3--"\n"-->0
    end
    classDef accept stroke:#333,stroke-width:4px;
    class 0 accept
    ```
    """
    state = 0
    tok = ""
    accept_states = [0]
    machine = [
        [
            StateRule(0, lambda c: c in "$0HLMbhjklmwx\n"),
            StateRule(1, lambda c: c in "123456789"),
            StateRule(2, lambda c: c == ":"),
        ],
        [StateRule(0, lambda c: c in "$0HLMbhjklwx\n")],
        [StateRule(3, lambda c: c == "q")],
        [StateRule(0, lambda c: c == "\n")],
    ]
    start_time = None
    while True:
        try:
            if start_time:
                elapsed_time = datetime.now() - start_time
                overwrite_str(stdscr, 27, 0, f"{elapsed_time.seconds:03}")
            c = stdscr.get_wch()
            rule = next(rule for rule in machine[state] if rule.cond(c))
        except curses.error:
            continue
        except StopIteration:
            raise AssertionError(repr(c))
        if not start_time:
            start_time = datetime.now()
        tok += c
        if rule.next_state in [2, 3]:
            stdscr.echochar(c)
        elif rule.next_state in accept_states:
            yield tok
            tok = ""
        state = rule.next_state


"""
register clock listener
register key press listeners
event loop:
  input next char (don't block)
  invoke listeners

"h" listener -> move cursor left once within left bound
"""


def event_loop(stdscr: "curses._CursesWindow", callback: Callable):
    stdscr.nodelay(True)
    while True:
        try:
            c = stdscr.get_wch()
        except curses.error:
            pass
        except StopIteration:
            raise AssertionError(repr(c))


Yx = namedtuple("Yx", ["y", "x"])
CELL_STR = "[ ]"
MINE_FLAG = "x"


class Cursor(Yx):
    def to_model(self) -> Tuple[int, int]:
        return (int((self.x - 1) / 3), self.y - 1)

    @staticmethod
    def from_model(x: int, y: int) -> "Cursor":
        return Cursor(y + 1, x * 3 + 1)


@dataclass
class GameApp:
    stdscr: "curses._CursesWindow"
    game: game.Game
    cursor: Cursor = Cursor(1, 1)

    @property
    def active_cell(self):
        return self.cell_at(self.cursor)

    def __post_init__(self):
        ui_board = (CELL_STR * self.game.width + "\n") * self.game.height
        self.stdscr.addstr(0, 0, f"MiNeSwEePeR{' '*16}000\n{ui_board}")
        self.stdscr.move(*self.cursor)

    def cell_at(self, cursor: Cursor) -> game.Cell:
        x, y = cursor.to_model()
        return self.game.board[y][x]


def c_main(stdscr: "curses._CursesWindow") -> int:
    app = GameApp(stdscr, game.create_game(*game.EASY))
    mv = {
        "h": lambda y, x: (y, x - 3) if x > 1 else (y, x),
        "j": lambda y, x: (y + 1, x) if y < app.game.height else (y, x),
        "k": lambda y, x: (y - 1, x) if y > 1 else (y, x),
        "l": lambda y, x: (y, x + 3) if x < (app.game.width - 1) * 3 else (y, x),
        "\n": lambda y, x: (y + 1, 1) if y < app.game.height else (y, x),
        "0": lambda y, _: (y, 1),
        "$": lambda y, _: (y, app.game.width * 3 - 2),
        "H": lambda _, __: (1, 1),
        "L": lambda _, __: (app.game.height, 1),
        "M": lambda _, __: (int(app.game.height / 2), 1),
    }
    for tok in lex(stdscr):
        if tok == ":q\n":
            return 0
        if tok == "x":
            if app.active_cell.is_swept and app.active_cell.value in "12345678":
                reveal_unmarked_neighbors(app)
            else:
                reveal_cell(stdscr, app.cursor, app.active_cell)
            if app.active_cell.is_swept and app.active_cell.value == "*":
                return bye(stdscr, app.game.height + 1, 0, "Game Over")
            if app.active_cell.value == " ":
                reveal_spaces(stdscr, app.cursor, app.game.board)
            if game.is_win(app.game.board):
                return bye(stdscr, app.game.height + 1, 0, "You win!")
        elif tok == "m":
            if app.active_cell.is_swept:
                continue
            app.active_cell.is_flag = not app.active_cell.is_flag
            v = MINE_FLAG if app.active_cell.is_flag else " "
            overwrite_cell(stdscr, app.cursor, f"[{v}]")
        elif tok == "w":
            app.cursor = Cursor.from_model(
                *game.next_unswept(app.game.board, *app.cursor.to_model())
            )
            stdscr.move(*app.cursor)
        else:
            app.cursor = Cursor(*mv[tok](app.cursor.y, app.cursor.x))
            stdscr.move(*app.cursor)
    return 0


def bye(stdscr, y, x, msg):
    stdscr.addstr(y, x, msg)
    stdscr.nodelay(False)
    stdscr.get_wch()
    return 0


def reveal_cell(stdscr, cursor: Tuple[int, int], cell: game.Cell):
    if cell.is_flag:
        return
    overwrite_cell(stdscr, cursor, f" {cell.value} ")
    cell.is_swept = True


def reveal_unmarked_neighbors(app: GameApp):
    x, y = app.cursor.to_model()
    unswept_cells = _get_unswept_cells(app.game.board, x, y)
    n_flags = [app.game.board[y][x].is_flag for (x, y) in unswept_cells].count(True)
    if n_flags != int(app.active_cell.value):
        return
    unmarked_cells = [
        (x, y) for x, y in unswept_cells if not app.game.board[y][x].is_flag
    ]
    for x, y in unmarked_cells:
        reveal_cell(app.stdscr, xy_to_cursor(x, y), app.game.board[y][x])
        if app.game.board[y][x].value == " ":
            more_cells = set(_get_unswept_cells(app.game.board, x, y))
            more_cells = more_cells.difference(set(unmarked_cells))
            unmarked_cells.extend(more_cells)


def overwrite_cell(stdscr, cursor: Tuple[int, int], cell: str):
    overwrite_str(stdscr, cursor[1] - 1, cursor[0], cell)


def overwrite_str(stdscr: "curses._CursesWindow", x: int, y: int, s: str):
    cursor = stdscr.getyx()
    for _ in range(len(s)):
        stdscr.delch(y, x)
    stdscr.insstr(y, x, s)
    stdscr.move(*cursor)


def reveal_spaces(stdscr: "curses._CursesWindow", cursor: Tuple[int, int], board: List):
    unswept_cells = _get_unswept_cells(board, *cursor_to_xy(cursor))
    for x, y in unswept_cells:
        reveal_cell(stdscr, xy_to_cursor(x, y), board[y][x])
        if board[y][x].value == " ":
            more_cells = set(_get_unswept_cells(board, x, y))
            more_cells = more_cells.difference(set(unswept_cells))
            unswept_cells.extend(more_cells)
    stdscr.move(*cursor)


def _get_unswept_cells(board: List, x: int, y: int) -> List[Tuple[int, int]]:
    xys = game._get_neighbor_cells(board, x, y)
    return [(x, y) for x, y in xys if not board[y][x].is_swept]


def cursor_to_xy(cursor: Tuple[int, int]) -> Tuple[int, int]:
    return (int((cursor[1] - 1) / 3), cursor[0] - 1)


def xy_to_cursor(x: int, y: int) -> Tuple[int, int]:
    return (y + 1, x * 3 + 1)


def debug(stdscr, cursor, msg):
    stdscr.addstr(0, 13, msg)
    stdscr.clrtoeol()
    stdscr.move(*cursor)


def main(seed: int = typer.Option(0, help="seed for repeatable game")) -> int:
    if seed:
        game.random.seed(seed)
    return curses.wrapper(c_main)


def run():
    exit(typer.run(main))


if __name__ == "__main__":
    run()
