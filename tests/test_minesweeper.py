import sys
from time import sleep

import pytest
from hecate.hecate import Runner


def test_minesweeper_quit(runner):
    runner.await_text("MiNeSwEePeR")
    runner.write(":q")
    runner.await_text(":q")
    runner.press("Enter")
    runner.await_exit()


def test_minesweeper_movement_and_flag_cell_invincible(runner):
    runner.await_text("[ ]" * 10)
    runner.write("L$hmxlmm")
    assert runner.screenshot().strip().endswith("[x][ ]")


def test_reveal_spaces(runner):
    runner.await_text("[ ]" * 10)
    runner.write("lllllx")
    assert runner.screenshot().split("\n")[1:3] == [
        "[ ][ ][ ][ ] 1           1 [ ]",
        "[ ][ ][ ][ ] 1  1  1  1  1 [ ]",
    ]


def test_win(runner):
    runner.await_text("[ ]" * 10)
    assert runner.screenshot().split("\n")[0].endswith("000")
    runner.write("x")
    sleep(1)
    runner.write("llxlllx$jjxLxkkkkkxkxL$hhhxkxkxkxkxhjjjxjxhx")
    runner.await_text("You win!")
    assert not runner.screenshot().split("\n")[0].endswith("000")


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
    with Runner(sys.executable, "-m", "minesweeper", "--seed", "1") as h:
        yield h
