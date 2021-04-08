import sys

from hecate.hecate import Runner


def test_minesweeper_quit():
    with Runner(sys.executable, "-m", "minesweeper") as h:
        h.await_text("MiNeSwEePeR")
        h.write(":q")
        h.await_text(":q")
        h.press("Enter")
        h.await_exit()
