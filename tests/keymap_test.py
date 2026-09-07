from collections.abc import Callable

CFG = """\
Hi
"""


def cursor_left() -> None: ...


class KeyMap:
    key: str
    action: Callable[[], None]


KEYMAP = {"l": cursor_left}
