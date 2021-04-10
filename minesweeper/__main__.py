import curses
import itertools
from typing import Callable, Generator, List, Tuple

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
            {"next_state": 0, "cond": lambda c: c in "$0HLMhjklmx\n"},
            {"next_state": 1, "cond": lambda c: c in "123456789"},
            {"next_state": 2, "cond": lambda c: c == ":"},
        ],
        [{"next_state": 0, "cond": lambda c: c in "$0HLMhjklx\n"}],
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
    cursor = [1, 1]
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
            if not sq.is_flag:
                overwrite_square(stdscr, cursor, f" {sq.value} ")
            if sq.value == "*":
                stdscr.addstr(h + 1, 0, "Game Over")
                stdscr.get_wch()
                return 0
        elif tok == "m":
            sq = game_board[game_pos[1]][game_pos[0]]
            sq.is_flag = not sq.is_flag
            game_board[game_pos[1]][game_pos[0]].is_flag = sq.is_flag
            v = MINE_FLAG if sq.is_flag else " "
            overwrite_square(stdscr, cursor, f"[{v}]")
        else:
            cursor = mv[tok](cursor)
            stdscr.move(*cursor)
    return 0


def overwrite_square(stdscr, cursor: List[int], square: str):
    for _ in range(3):
        stdscr.delch(cursor[0], cursor[1] - 1)
    stdscr.insstr(cursor[0], cursor[1] - 1, square)
    stdscr.move(*cursor)


def cursor_to_xy(cursor: List[int]) -> Tuple:
    return (int((cursor[1] - 1) / 3), cursor[0] - 1)


def main() -> int:
    return curses.wrapper(c_main)


if __name__ == "__main__":
    exit(main())
