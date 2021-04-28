import curses
from collections import namedtuple
from dataclasses import dataclass
from datetime import datetime
from typing import Callable, Dict, Generator, List, Tuple
from curses import KEY_DOWN, KEY_LEFT, KEY_RIGHT, KEY_UP

import typer

from minesweeper_vim import game

DELETE = 0x7F
KEYMAP: Dict[int, str] = {
    ord(" "): "l",
    DELETE: "h",
    KEY_DOWN: "j",
    KEY_UP: "k",
    KEY_LEFT: "h",
    KEY_RIGHT: "l",
}
CELL_STR = "[ ]"
FLAG_CELL_STR = "[x]"
Yx = namedtuple("Yx", ["y", "x"])


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
        return self._cell_at(self.cursor)

    def __post_init__(self):
        ui_board = (CELL_STR * self.game.width + "\n") * self.game.height
        self.stdscr.clrtobot()
        self.stdscr.addstr(0, 0, f"MiNeSwEePeR{' '*15}000s\n{ui_board}")
        self.stdscr.nodelay(True)
        self._redraw_cursor()

    def move_to(self, cursor: Cursor):
        self.cursor = cursor
        self._redraw_cursor()

    def mark_cell(self):
        if self.active_cell.is_swept:
            return
        self.active_cell.is_flag = not self.active_cell.is_flag
        self._redraw_cell()

    def sweep_cell(self):
        if self.active_cell.is_swept and self.active_cell.value in "12345678":
            self._reveal_unmarked_neighbors()
        else:
            self._reveal_cell()
        if self.active_cell.is_swept and self.active_cell.value == " ":
            self._reveal_unmarked_neighbors()

    def reveal_mines(self):
        h, w = (self.game.height, self.game.width)
        for y, x in ((y, x) for y in range(h) for x in range(w)):
            cell = game.cell_at(self.game.board, x, y)
            if cell.is_flag and cell.value != "*":
                cursor = Cursor.from_model(x, y)
                overwrite_str(self.stdscr, cursor.x - 1, cursor.y, "[/]")
            elif cell.value == "*":
                self._reveal_cell(Cursor.from_model(x, y))

    def _reveal_unmarked_neighbors(self):
        x, y = self.cursor.to_model()
        swath = game.get_unmarked_neighbor_cells(self.game.board, x, y)
        for x, y in swath:
            self._reveal_cell(Cursor.from_model(x, y))
            if self._cell_at(Cursor.from_model(x, y)).value == " ":
                more_cells = set(game.get_unswept_neighbor_cells(self.game.board, x, y))
                more_cells = more_cells.difference(set(swath))
                swath.extend(more_cells)

    def _reveal_cell(self, cursor: Cursor = None):
        cursor = cursor or self.cursor
        cell = self._cell_at(cursor)
        if not cell.is_flag:
            cell.is_swept = True
        self._redraw_cell(cursor)

    def _cell_at(self, cursor: Cursor) -> game.Cell:
        x, y = cursor.to_model()
        return self.game.board[y][x]

    def _redraw_cell(self, cursor: Cursor = None):
        cursor = cursor or self.cursor
        cell = self._cell_at(cursor)
        v = FLAG_CELL_STR if cell.is_flag else CELL_STR
        if cell.is_swept:
            v = f" {cell.value} "
        overwrite_str(self.stdscr, cursor.x - 1, cursor.y, v)

    def _redraw_cursor(self):
        self.stdscr.move(*self.cursor)


def c_main(stdscr: "curses._CursesWindow") -> int:
    dims = {"easy": game.EASY, "medium": game.MEDIUM, "hard": game.HARD}
    app = GameApp(stdscr, game.create_game(*game.EASY))
    mv = {
        "b": lambda x, y: game.prev_unswept(app.game.board, x, y),
        "h": lambda x, y: (x - 1, y) if x > 0 else (x, y),
        "j": lambda x, y: (x, y + 1) if y + 1 < app.game.height else (x, y),
        "k": lambda x, y: (x, y - 1) if y - 1 >= 0 else (x, y),
        "l": lambda x, y: (x + 1, y) if x < app.game.width - 1 else (x, y),
        "w": lambda x, y: game.next_unswept(app.game.board, x, y),
        "\n": lambda x, y: (0, y + 1) if y + 1 < app.game.height else (x, y),
        "0": lambda _, y: (0, y),
        "$": lambda _, y: (app.game.width - 1, y),
        "H": lambda _, __: (0, 0),
        "L": lambda _, __: (0, app.game.height - 1),
        "M": lambda _, __: (0, int((app.game.height - 1) / 2)),
    }
    difficulty = ed_choose(app)
    if difficulty != "easy":
        app = GameApp(stdscr, game.create_game(*dims[difficulty]))
    else:
        overwrite_str(app.stdscr, 0, app.game.height + 1, " " * 30)
    for c in async_input(stdscr):
        if c == ":":
            app = GameApp(stdscr, game.create_game(*dims[ed_choose(app)]))
        elif c == "x":
            app.sweep_cell()
            if game.is_loss(app.game.board):
                app.reveal_mines()
                bye(app, "Game Over  ")
                app = GameApp(stdscr, game.create_game(*dims[ed_choose(app)]))
            elif game.is_win(app.game.board):
                bye(app, "You win!   ")
                app = GameApp(stdscr, game.create_game(*dims[ed_choose(app)]))
        elif c == "m":
            app.mark_cell()
        elif c in mv:
            app.move_to(Cursor.from_model(*mv[c](*app.cursor.to_model())))
        else:
            debug(app, f"{c} not implemented")
    return 0


def async_input(stdscr: "curses._CursesWindow") -> Generator:
    start_time = None
    while True:
        try:
            if start_time:
                elapsed_time = datetime.now() - start_time
                overwrite_str(stdscr, 26, 0, f"{elapsed_time.seconds:03}")
            c = stdscr.get_wch()
            yield KEYMAP.get(c if isinstance(c, int) else ord(c), c)
        except curses.error:
            continue
        if not start_time:
            start_time = datetime.now()


def ed_choose(app: GameApp):
    choices = ["_e_asy", "_m_edium", "h_a_rd", "_q_uit", "_?_"]
    shortcuts = list("emaq?")
    positions = [2, 8, 17, 22, 28]
    y = app.game.height + 1
    cursor = app.cursor
    app.stdscr.addstr(y, 0, ":")
    for s in choices:
        ed_add_selection(app, s)
    choice = 0
    app.move_to(Cursor(y, positions[choice]))
    for c in async_input(app.stdscr):
        if c == "\n":
            app.move_to(cursor)
            return choices[choice].replace("_", "")
        if c in "lw":
            choice = choice + (1 if choice + 1 < len(choices) else 0)
        elif c in "bh":
            choice = choice - (1 if choice - 1 >= 0 else 0)
        elif c in shortcuts:
            choice = shortcuts.index(c)
        app.move_to(Cursor(y, positions[choice]))


def ed_add_selection(app: GameApp, text: str):
    app.stdscr.addstr("[")
    attr = 0
    for c in text:
        if c == "_":
            attr = 0 if attr else curses.A_UNDERLINE
        else:
            app.stdscr.addstr(c, attr)
    app.stdscr.addstr("]")


def bye(app: GameApp, msg: str):
    overwrite_str(app.stdscr, 0, 0, msg)


def overwrite_str(stdscr: "curses._CursesWindow", x: int, y: int, s: str):
    cursor = stdscr.getyx()
    for _ in range(len(s)):
        stdscr.delch(y, x)
    stdscr.insstr(y, x, s)
    stdscr.move(*cursor)


def debug(app: GameApp, msg: str):
    cursor = app.stdscr.getyx()
    app.stdscr.addstr(app.game.height + 1, 0, msg)
    app.stdscr.move(*cursor)


def main(seed: int = typer.Option(0, help="seed for repeatable game")) -> int:
    if seed:
        game.random.seed(seed)
    try:
        return curses.wrapper(c_main)
    except KeyError:
        print("Thanks for playing")
        return 0


def run():
    exit(typer.run(main))


if __name__ == "__main__":
    run()
