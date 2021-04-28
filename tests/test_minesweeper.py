import sys
from time import sleep

import pytest
from hecate.hecate import Runner


def test_minesweeper_quit(runner):
    runner.await_text("MiNeSwEePeR")
    runner.write(":q")
    runner.await_text("quit")
    runner.press("Enter")
    runner.await_exit()


def test_minesweeper_movement_and_flag_cell_invincible(runner):
    runner.await_text("[ ]" * 10)
    runner.press("Enter")
    runner.write("L$hmxlmm")
    assert runner.screenshot().strip().endswith("[x][ ]")


def test_reveal_spaces(runner):
    runner.await_text(":[easy]")
    runner.press("Enter")
    runner.write("lllllx")
    assert runner.screenshot().split("\n")[1:3] == [
        "[ ][ ][ ][ ] 1           1 [ ]",
        "[ ][ ][ ][ ] 1  1  1  1  1 [ ]",
    ]


def test_reveal_unmarked(runner):
    runner.await_text("[ ]" * 10)
    runner.press("Enter")
    runner.write("xlmhx")
    assert runner.screenshot().split("\n")[1:3] == [
        " 1 [x][ ][ ][ ][ ][ ][ ][ ][ ]",
        " 1  1 [ ][ ][ ][ ][ ][ ][ ][ ]",
    ]


def test_reveal_bad_mark_loses(runner):
    runner.await_text("[ ]" * 10)
    runner.press("Enter")
    runner.write("mjxx")
    runner.await_text("Game Over")
    assert runner.screenshot().split("\n")[1:3] == [
        "[/] * [ ] * [ ][ ][ ][ ][ ] *",
        " 1  1 [ ][ ][ ][ ][ ][ ][ ][ ]",
    ]


def test_win(runner):
    runner.await_text("[ ]" * 10)
    runner.press("Enter")
    assert runner.screenshot().split("\n")[0].endswith("000s")
    runner.write("x")
    sleep(1)
    runner.write("jxjxllxkkxlllxM$xbxwxjxjxjxhxkxhjx")
    runner.await_text("You win!")
    assert not runner.screenshot().split("\n")[0].endswith("000s")


def test_ed_mode_set_difficulty_when_game_not_started(runner):
    runner.await_text("[ ]" * 10)
    runner.await_text(":[easy][medium][hard][quit][?]")


@pytest.fixture
def runner():
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
    with Runner(sys.executable, "-m", "minesweeper_vim.ui", "--seed", "1") as h:
        yield h
