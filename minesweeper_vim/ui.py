import curses
from dataclasses import dataclass
from datetime import datetime
from typing import Callable, Generator, List, Tuple

import typer

from minesweeper_vim import game

MINE_FLAG = "x"


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


def c_main(stdscr: "curses._CursesWindow") -> int:
    w, h, n = game.EASY
    game_board = game.create_board(w, h, n)
    ui_board = ("[ ]" * w + "\n") * h
    stdscr.addstr(0, 0, f"MiNeSwEePeR{' '*16}000\n{ui_board}")
    cursor = (1, 1)
    stdscr.move(*cursor)
    stdscr.nodelay(True)
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
    for tok in lex(stdscr):
        if tok == ":q\n":
            return 0
        x, y = cursor_to_xy(cursor)
        sq = game_board[y][x]
        if tok == "x":
            if sq.is_swept and sq.value in "12345678":
                reveal_unmarked(stdscr, cursor, game_board)
            else:
                reveal_cell(stdscr, cursor, sq)
            if sq.is_swept and sq.value == "*":
                return bye(stdscr, h + 1, 0, "Game Over")
            if sq.value == " ":
                reveal_spaces(stdscr, cursor, game_board)
            if game.is_win(game_board):
                return bye(stdscr, h + 1, 0, "You win!")
        elif tok == "m":
            if sq.is_swept:
                continue
            sq.is_flag = not sq.is_flag
            v = MINE_FLAG if sq.is_flag else " "
            overwrite_cell(stdscr, cursor, f"[{v}]")
        elif tok == "w":
            cursor = xy_to_cursor(*game.next_unswept(game_board, x, y))
            stdscr.move(*cursor)
        else:
            cursor = mv[tok](cursor)
            stdscr.move(*cursor)
    return 0


def sweep_cell(
    stdscr: "curses._CursesWindow",
    cursor: Tuple[int, int],
    board: List[List[game.Cell]],
):
    x, y = cursor_to_xy(cursor)
    cell = board[y][x]
    if cell.is_swept and cell.value in "12345678":
        reveal_unmarked(stdscr, cursor, board)
    else:
        reveal_cell(stdscr, cursor, cell)
    if cell.is_swept and cell.value == "*":
        raise AssertionError("Game Over")


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


def reveal_unmarked(
    stdscr: "curses._CursesWindow", cursor: Tuple[int, int], board: List
):
    x, y = cursor_to_xy(cursor)
    unswept_cells = _get_unswept_cells(board, x, y)
    n_flags = [board[y][x].is_flag for (x, y) in unswept_cells].count(True)
    if n_flags != int(board[y][x].value):
        return
    unmarked_cells = [(x, y) for x, y in unswept_cells if not board[y][x].is_flag]
    for x, y in unmarked_cells:
        reveal_cell(stdscr, xy_to_cursor(x, y), board[y][x])
        if board[y][x].value == " ":
            more_cells = set(_get_unswept_cells(board, x, y))
            more_cells = more_cells.difference(set(unmarked_cells))
            unmarked_cells.extend(more_cells)


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
