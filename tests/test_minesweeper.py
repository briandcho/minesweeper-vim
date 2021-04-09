import sys

import pytest
from hecate.hecate import Runner


def test_minesweeper_quit(runner):
    runner.await_text("MiNeSwEePeR")
    runner.write(":q")
    runner.await_text(":q")
    runner.press("Enter")
    runner.await_exit()


def test_minesweeper_movement(runner):
    runner.await_text("[ ]" * 10)
    runner.press("L")
    runner.press("$")
    runner.press("m")
    assert runner.screenshot().strip().endswith("[x]")


@pytest.fixture
def runner():
    with Runner(sys.executable, "-m", "minesweeper") as h:
        yield h
