import time
import curses
from collections import namedtuple
from curses import KEY_DOWN, KEY_LEFT, KEY_RIGHT, KEY_UP
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum, auto
from typing import Callable, Dict, Generator, List, Optional, Protocol, Tuple, Union

import typer

from minesweeper_vim import game
from minesweeper_vim.gamectl import GameCtl

DELETE = 0x7F
KEYMAP: Dict[int, int] = {
    ord(" "): ord("l"),
    DELETE: ord("h"),
    KEY_DOWN: ord("j"),
    KEY_UP: ord("k"),
    KEY_LEFT: ord("h"),
    KEY_RIGHT: ord("l"),
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


class KeypressHandler(Protocol):
    def handle_keypress(self, key: int) -> Optional[Cursor]:
        ...

    @property
    def cursor(self) -> Cursor:
        ...


class HeaderComponent:
    header: str

    def __init__(self, width: int):
        self.header = f"MiNeSwEePeR{' '*(width*3-15)}000s\n"

    def __str__(self) -> str:
        return self.header


class BoardComponent:
    CELL_STR: str = "[ ]"
    FLAG_CELL_STR: str = "[x]"
    board: str
    width: int
    height: int
    _cursor: Cursor

    def __init__(self, width: int, height: int):
        self.width = width
        self.height = height
        self.board = (self.CELL_STR * width + "\n") * height
        self._cursor = Cursor.from_model(0, 0)

    def __str__(self) -> str:
        return self.board

    @property
    def cursor(self) -> Cursor:
        return self._cursor

    @property
    def cursor_down(self) -> Cursor:
        x, y = self.cursor.to_model()
        return Cursor.from_model(x, y + 1) if y < self.height - 1 else self.cursor

    @property
    def cursor_left(self) -> Cursor:
        x, y = self.cursor.to_model()
        return Cursor.from_model(x - 1, y) if x > 0 else self.cursor

    @property
    def cursor_right(self) -> Cursor:
        x, y = self.cursor.to_model()
        return Cursor.from_model(x + 1, y) if x < self.width - 1 else self.cursor

    @property
    def cursor_up(self) -> Cursor:
        x, y = self.cursor.to_model()
        return Cursor.from_model(x, y - 1) if y > 0 else self.cursor

    @property
    def cursor_start_of_row(self) -> Cursor:
        return Cursor.from_model(0, self.cursor.to_model()[1])

    @property
    def cursor_start_of_first_row(self) -> Cursor:
        return Cursor.from_model(0, 0)

    @property
    def cursor_start_of_last_row(self) -> Cursor:
        return Cursor.from_model(0, self.height - 1)

    @property
    def cursor_start_of_middle_row(self) -> Cursor:
        return Cursor.from_model(0, int(self.height / 2))

    @property
    def cursor_end_of_row(self) -> Cursor:
        return Cursor.from_model(self.width, self.cursor.to_model()[1])

    def handle_keypress(self, key: int) -> Optional[Cursor]:
        keymap = {
            ord("$"): self.cursor_end_of_row,
            ord("0"): self.cursor_start_of_row,
            ord(":"): None,
            ord("H"): self.cursor_start_of_first_row,
            ord("L"): self.cursor_start_of_last_row,
            ord("M"): self.cursor_start_of_middle_row,
            ord("h"): self.cursor_left,
            ord("j"): self.cursor_down,
            ord("k"): self.cursor_up,
            ord("l"): self.cursor_right,
        }
        if cursor := keymap.get(key, self.cursor):
            self._cursor = cursor
        return cursor
        # "b": lambda x, y: game.prev_unswept(app.game.board, x, y),
        # "w": lambda x, y: game.next_unswept(app.game.board, x, y),
        # "\n": lambda x, y: (0, y + 1) if y + 1 < app.game.height else (x, y),


class EdComponent:
    CHOICES: List[str] = ["easy", "medium", "hard", "quit", "?"]
    SHORTCUTS: List[int] = [ord(c) for c in "emaq?"]
    SHORTCUT_POS = [2, 8, 17, 22, 28]
    y: int
    _cursor: Cursor

    def __init__(self, y: int):
        self.y = y
        self._cursor = Cursor(y, self.SHORTCUT_POS[0])

    def __str__(self) -> str:
        return ":[" + "][".join(self.CHOICES) + "]"

    @property
    def str_parts(self) -> List[Tuple[str, int]]:
        ret: List[Tuple[str, int]] = []
        post = str(self)
        for shortcut in self.SHORTCUTS:
            pre, in_, post = post.partition(chr(shortcut))
            ret.append((pre, curses.A_NORMAL))
            ret.append((in_, curses.A_UNDERLINE))
        ret.append((post, curses.A_NORMAL))
        return ret

    @property
    def choice(self) -> str:
        return self.CHOICES[self.SHORTCUT_POS.index(self.cursor.x)]

    @property
    def choice_i(self) -> int:
        return self.SHORTCUT_POS.index(self.cursor.x)

    @property
    def cursor(self) -> Cursor:
        return self._cursor

    def choose_next(self) -> "EdComponent":
        if self.choice_i < len(self.CHOICES) - 1:
            self._cursor = Cursor(self.cursor.y, self.SHORTCUT_POS[self.choice_i + 1])
        return self

    def choose_prev(self) -> "EdComponent":
        if self.choice_i > 0:
            self._cursor = Cursor(self.cursor.y, self.SHORTCUT_POS[self.choice_i - 1])
        return self

    def choose_shortcut(self, shortcut: int) -> "EdComponent":
        x = self.SHORTCUT_POS[self.SHORTCUTS.index(shortcut)]
        self._cursor = Cursor(self.cursor.y, x)
        return self

    def handle_keypress(self, key: int) -> Optional[Cursor]:
        cursor: Optional[Cursor] = self.cursor
        if key == ord("\n"):
            cursor = None
        elif key in self.SHORTCUTS:
            cursor = self.choose_shortcut(key).cursor
        elif key in [ord("l"), ord("w")]:
            cursor = self.choose_next().cursor
        elif key in [ord("b"), ord("h")]:
            cursor = self.choose_prev().cursor
        return cursor


class GameApp:
    stdscr: "curses._CursesWindow"
    game: game.Game
    cursor: Cursor = Cursor(1, 1)
    ioctl: GameCtl = GameCtl()
    keypress_handler: KeypressHandler
    header: HeaderComponent
    board: BoardComponent
    ed: EdComponent

    @property
    def active_cell(self) -> game.Cell:
        return self._cell_at(self.cursor)

    def __init__(self, stdscr: "curses._CursesWindow", game: game.Game) -> None:
        self.stdscr = stdscr
        self.game = game
        self.header = HeaderComponent(self.game.width)
        self.board = BoardComponent(self.game.width, self.game.height)
        self.ed = EdComponent(self.game.height + 1)
        self.stdscr.clear()
        self.stdscr.nodelay(True)
        self.stdscr.addstr(0, 0, str(self.header))
        self.stdscr.addstr(str(self.board))
        for s, attr in self.ed.str_parts:
            self.stdscr.addstr(s, attr)
        self.move_to(self.ed.cursor)
        self.keypress_handler = self.ed

    def handle_keypress(self) -> None:
        c = ensure_ord(self.stdscr.get_wch())
        c = KEYMAP.get(c, c)
        cursor = self.keypress_handler.handle_keypress(c)
        if not cursor:
            self.toggle_keypress_handler()
            cursor = self.keypress_handler.cursor
        self.move_to(cursor)

    def toggle_keypress_handler(self) -> None:
        is_ed = self.keypress_handler == self.ed
        self.keypress_handler = self.board if is_ed else self.board

    def move_to(self, cursor: Cursor) -> None:
        self.cursor = cursor
        self._redraw_cursor()

    def mark_cell(self) -> None:
        if self.active_cell.is_swept:
            return
        self.active_cell.is_flag = not self.active_cell.is_flag
        self._redraw_cell()

    def sweep_cell(self) -> None:
        if self.active_cell.is_swept and self.active_cell.value in "12345678":
            self._reveal_unmarked_neighbors()
        else:
            self._reveal_cell()
        if self.active_cell.is_swept and self.active_cell.value == " ":
            self._reveal_unmarked_neighbors()

    def reveal_mines(self) -> None:
        h, w = (self.game.height, self.game.width)
        for y, x in ((y, x) for y in range(h) for x in range(w)):
            cell = game.cell_at(self.game.board, x, y)
            if cell.is_flag and cell.value != "*":
                cursor = Cursor.from_model(x, y)
                overwrite_str(self.stdscr, cursor.x - 1, cursor.y, "[/]")
            elif cell.value == "*":
                self._reveal_cell(Cursor.from_model(x, y))

    def _reveal_unmarked_neighbors(self) -> None:
        x, y = self.cursor.to_model()
        swath = game.get_unmarked_neighbor_cells(self.game.board, x, y)
        for x, y in swath:
            self._reveal_cell(Cursor.from_model(x, y))
            if self._cell_at(Cursor.from_model(x, y)).value == " ":
                more_cells = set(game.get_unswept_neighbor_cells(self.game.board, x, y))
                more_cells = more_cells.difference(set(swath))
                swath.extend(more_cells)

    def _reveal_cell(self, cursor: Optional[Cursor] = None) -> None:
        cursor = cursor or self.cursor
        cell = self._cell_at(cursor)
        if not cell.is_flag:
            cell.is_swept = True
        self._redraw_cell(cursor)

    def _cell_at(self, cursor: Cursor) -> game.Cell:
        x, y = cursor.to_model()
        return self.game.board[y][x]

    def _redraw_cell(self, cursor: Optional[Cursor] = None) -> None:
        cursor = cursor or self.cursor
        cell = self._cell_at(cursor)
        v = FLAG_CELL_STR if cell.is_flag else CELL_STR
        if cell.is_swept:
            v = f" {cell.value} "
        overwrite_str(self.stdscr, cursor.x - 1, cursor.y, v)

    def _redraw_cursor(self) -> None:
        self.stdscr.move(*self.cursor)


def ensure_ord(c: Union[int, str]) -> int:
    return c if isinstance(c, int) else ord(c)


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
    ctl = GameCtl()
    ctl.register_callback(lambda: app.handle_keypress())
    difficulty = ed_choose(app)
    if difficulty != "easy":
        app = GameApp(stdscr, game.create_game(*dims[difficulty]))
    app.move_to(Cursor(app.ed.y, 0))
    app.stdscr.clrtobot()
    app.move_to(app.board.cursor)
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


def async_input(stdscr: "curses._CursesWindow") -> Generator[str, None, None]:
    start_time = None
    while True:
        try:
            time.sleep(.04)
            if start_time:
                elapsed_time = datetime.now() - start_time
                overwrite_str(stdscr, 26, 0, f"{elapsed_time.seconds:03}")
            c = stdscr.get_wch()
            yield KEYMAP.get(c if isinstance(c, int) else ord(c), c)
        except curses.error:
            continue
        if not start_time:
            start_time = datetime.now()


def ed_choose(app: GameApp) -> Optional[str]:
    choices = ["_e_asy", "_m_edium", "h_a_rd", "_q_uit", "_?_"]
    shortcuts = list("emaq?")
    positions = [2, 8, 17, 22, 28]
    y = app.game.height + 1
    choice = 0
    for c in async_input(app.stdscr):
        if c == "\n":
            return choices[choice].replace("_", "")
        if c in "lw":
            choice = choice + (1 if choice + 1 < len(choices) else 0)
        elif c in "bh":
            choice = choice - (1 if choice - 1 >= 0 else 0)
        elif c in shortcuts:
            choice = shortcuts.index(c)
        app.move_to(Cursor(y, positions[choice]))
    return None


def bye(app: GameApp, msg: str) -> None:
    overwrite_str(app.stdscr, 0, 0, msg)


def overwrite_str(stdscr: "curses._CursesWindow", x: int, y: int, s: str) -> None:
    cursor = stdscr.getyx()
    for _ in range(len(s)):
        stdscr.delch(y, x)
    stdscr.insstr(y, x, s)
    stdscr.move(*cursor)


def debug(app: GameApp, msg: str) -> None:
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


def run() -> None:
    exit(typer.run(main))


if __name__ == "__main__":
    run()
