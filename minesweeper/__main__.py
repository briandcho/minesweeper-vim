import curses
import itertools
from typing import Callable, Generator, List, Optional, Tuple

import typer

from minesweeper import game

MINE_FLAG = "x"


def lex(get_char: Callable, echo: Callable) -> Generator:
    """
    /[$0HLM]|[1-9]?[hjklx\n]|:\S+/
    ```mermaid
    graph LR
    subgraph lex
        0((0))--"[$0HLMhjklmx\n]"-->0
        0--"[1-9]"-->1((1))
        0--:-->2((2))
        1--"[$0HLMhjklx\n]"-->0
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
            {"next_state": 0, "cond": lambda c: c in "$0HLMbhjklmwx\n"},
            {"next_state": 1, "cond": lambda c: c in "123456789"},
            {"next_state": 2, "cond": lambda c: c == ":"},
        ],
        [{"next_state": 0, "cond": lambda c: c in "$0HLMbhjklwx\n"}],
        [{"next_state": 3, "cond": lambda c: c == "q"}],
        [{"next_state": 0, "cond": lambda c: c == "\n"}],
    ]
    while True:
        c = get_char()
        try:
            rule = next(rule for rule in machine[state] if rule["cond"](c))
        except StopIteration:
            raise AssertionError(repr(c))
        tok += c
        if rule["next_state"] in [2, 3]:
            echo(c)
        elif rule["next_state"] in accept_states:
            yield tok
            tok = ""
        state = rule["next_state"]


def c_main(stdscr: "curses._CursesWindow") -> int:
    w, h, n = 10, 8, 10
    game_board = game.create_board(w, h, n)
    ui_board = ("[ ]" * w + "\n") * h
    stdscr.addstr(0, 0, f"MiNeSwEePeR\n{ui_board}")
    cursor = (1, 1)
    stdscr.move(*cursor)
    mv = {
        "h": lambda yx: [yx[0], yx[1] - 3 if yx[1] > 1 else yx[1]],
        "j": lambda yx: [yx[0] + 1 if yx[0] < h else yx[0], yx[1]],
        "k": lambda yx: [yx[0] - 1 if yx[0] > 1 else yx[0], yx[1]],
        "l": lambda yx: [yx[0], yx[1] + 3 if yx[1] < (w - 1) * 3 else yx[1]],
        "\n": lambda yx: [yx[0] + 1, 1] if yx[0] < h else yx,
        "0": lambda yx: [yx[0], 1],
        "$": lambda yx: [yx[0], w * 3 - 2],
        "H": lambda _: [1, 1],
        "L": lambda _: [h, 1],
        "M": lambda _: [int(h / 2), 1],
    }
    for tok in lex(lambda: stdscr.get_wch(), lambda c: stdscr.echochar(c)):
        if tok == ":q\n":
            return 0
        game_pos = cursor_to_xy(cursor)
        sq = game_board[game_pos[1]][game_pos[0]]
        if tok == "x":
            reveal_square(stdscr, cursor, sq)
            if sq.is_swept and sq.value == "*":
                stdscr.addstr(h + 1, 0, "Game Over")
                stdscr.get_wch()
                return 0
            if sq.value == " ":
                reveal_spaces(stdscr, cursor, game_board)
        elif tok == "m":
            sq.is_flag = not sq.is_flag
            v = MINE_FLAG if sq.is_flag else " "
            overwrite_square(stdscr, cursor, f"[{v}]")
        else:
            cursor = mv[tok](cursor)
            stdscr.move(*cursor)
    return 0


def reveal_square(stdscr, cursor: Tuple[int, int], square: game.Square):
    if square.is_flag:
        return
    overwrite_square(stdscr, cursor, f" {square.value} ")
    square.is_swept = True


def overwrite_square(stdscr, cursor: Tuple[int, int], square: str):
    for _ in range(3):
        stdscr.delch(cursor[0], cursor[1] - 1)
    stdscr.insstr(cursor[0], cursor[1] - 1, square)
    stdscr.move(*cursor)


def reveal_spaces(stdscr: "curses._CursesWindow", cursor: Tuple[int, int], board: List):
    unswept_squares = _get_unswept_squares(board, *cursor_to_xy(cursor))
    for x, y in unswept_squares:
        reveal_square(stdscr, xy_to_cursor(x, y), board[y][x])
        if board[y][x].value == " ":
            more_squares = set(_get_unswept_squares(board, x, y))
            more_squares = more_squares.difference(set(unswept_squares))
            unswept_squares.extend(more_squares)
    stdscr.move(*cursor)


def _get_unswept_squares(board: List, x: int, y: int) -> List[Tuple[int, int]]:
    xys = game._get_surrounding_squares(board, x, y)
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


if __name__ == "__main__":
    exit(typer.run(main))
