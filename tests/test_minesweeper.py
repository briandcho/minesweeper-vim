import sys

import pytest
from hecate.hecate import Runner


def test_minesweeper_quit(runner):
    runner.await_text("MiNeSwEePeR")
    runner.write(":q")
    runner.await_text(":q")
    runner.press("Enter")
    runner.await_exit()


def test_minesweeper_movement_and_flag_square_invincible(runner):
    runner.await_text("[ ]" * 10)
    runner.write("L$hmxlmm")
    assert runner.screenshot().strip().endswith("[x][ ]")


def test_reveal_spaces(runner):
    runner.await_text("[ ]" * 10)
    runner.write("lllllx")
    assert runner.screenshot().startswith(
        """MiNeSwEePeR
[ ][ ][ ][ ] 1           1 [ ]
[ ][ ][ ][ ] 1  1  1  1  1 [ ]"""
    )


def test_win(runner):
    runner.await_text("[ ]" * 10)
    runner.write("xllxlllx$jjxLxkkkkkxkxL$hhhxkxkxkxkxhjjjxjxhx")
    runner.await_text("Success")


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
