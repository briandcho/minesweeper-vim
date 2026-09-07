import sys
from time import sleep

import pytest

from tests.pty_runner import Runner


def test_minesweeper_quit(runner: Runner) -> None:
    runner.await_text("MiNeSwEePeR")
    runner.write(":q")
    runner.await_text("quit")
    runner.press("Enter")
    runner.await_exit()


def test_minesweeper_movement_and_flag_cell_invincible(runner: Runner) -> None:
    runner.await_text("[ ]" * 10)
    runner.press("Enter")
    runner.write("L$hmxlmm")
    assert runner.screenshot().strip().endswith("[x][ ]")


def test_reveal_spaces(runner: Runner) -> None:
    runner.await_text(":[easy]")
    runner.press("Enter")
    runner.write("lllllx")
    assert runner.screenshot().split("\n")[1:3] == [
        "[ ][ ][ ][ ] 1           1 [ ]",
        "[ ][ ][ ][ ] 1  1  1  1  1 [ ]",
    ]


def test_reveal_unmarked(runner: Runner) -> None:
    runner.await_text("[ ]" * 10)
    runner.press("Enter")
    runner.write("xlmhx")
    assert runner.screenshot().split("\n")[1:3] == [
        " 1 [x][ ][ ][ ][ ][ ][ ][ ][ ]",
        " 1  1 [ ][ ][ ][ ][ ][ ][ ][ ]",
    ]


def test_reveal_bad_mark_loses(runner: Runner) -> None:
    runner.await_text("[ ]" * 10)
    runner.press("Enter")
    runner.write("mjxx")
    runner.await_text("Game Over")
    assert runner.screenshot().split("\n")[1:3] == [
        "[/] * [ ] * [ ][ ][ ][ ][ ] *",
        " 1  1 [ ][ ][ ][ ][ ][ ][ ][ ]",
    ]


def test_win(runner: Runner) -> None:
    runner.await_text("[ ]" * 10)
    runner.press("Enter")
    assert runner.screenshot().split("\n")[0].endswith("000s")
    runner.write("x")
    sleep(1)
    # 34 keystrokes at this game's ~80ms-per-keypress input-loop latency need ~2.7s
    # to fully process; the default 1s await_text budget isn't enough for that many.
    runner.write("jxjxllxkkxlllxM$xbxwxjxjxjxhxkxhjx")
    runner.await_text("You win!", timeout=5)
    assert not runner.screenshot().split("\n")[0].endswith("000s")


def test_ed_mode_set_difficulty_when_game_not_started(runner: Runner) -> None:
    runner.await_text("[ ]" * 10)
    runner.await_text(":[easy][medium][hard][quit][?]")


@pytest.mark.skip
def test_minesweeper_start_timer_when_difficulty_selected(runner: Runner) -> None:
    runner.await_text("[medium]")
    runner.write("l")
    sleep(1)
    assert runner.screenshot().split("\n")[0].endswith("000s")
    runner.press("Enter")
    assert len(runner.screenshot().split("\n")[1]) > 30


@pytest.fixture
def runner() -> Runner:
    """Seed 1
    1  *  2  *  1           1  *
    1  1  2  1  1  1  1  1  1  1
    1  1           1  *  1
    *  1           1  1  1
    1  1        1  1  2  1  1
             1  2  *  3  *  2
             1  *  2  4  *  3
             1  1  1  2  *  2
    """
    with Runner(sys.executable, "-m", "minesweeper_vim", "--seed", "1") as h:
        yield h
