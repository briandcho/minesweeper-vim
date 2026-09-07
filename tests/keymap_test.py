from typing import Callable

CFG = """\
Hi
"""

from dataclasses import dataclass


def cursor_left() -> None:
    ...


class KeyMap:
    key: str
    action: Callable


KEYMAP = {"l": cursor_left}


def test_keymap():
    reveal_type(KEYMAP)
