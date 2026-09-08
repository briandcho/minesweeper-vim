from __future__ import annotations

import os
import signal
import time
from collections.abc import Generator
from types import TracebackType
from typing import Self

import pexpect
import pyte

DEFAULT_WIDTH = 80
DEFAULT_HEIGHT = 24
DEFAULT_TIMEOUT = 1.0
DEFAULT_WAIT_INTERVAL = 0.01
# How long to wait for the terminal to go quiet (no new output) before treating a
# screenshot as settled, and the overall cap on how long a single screenshot() may
# block waiting for that quiet period. This game's own input loop re-checks for a
# keypress only every ~80ms (two 0.04s sleeps per iteration in async_input()), and
# a redraw can be written to the pty in more than one chunk with gaps approaching
# that scale — SETTLE_QUIET_PERIOD must comfortably exceed it or screenshot() will
# return mid-redraw.
SETTLE_QUIET_PERIOD = 0.2
SETTLE_MAX_WAIT = 2.0
# How long to give the child to exit gracefully after SIGTERM (see shutdown())
# before escalating to SIGKILL.
GRACEFUL_SHUTDOWN_WAIT = 2.5

_SPECIAL_KEYS = {
    "Enter": "\r",
}


class Timeout(Exception):
    pass


class Runner:
    """A minimal pexpect + pyte stand-in for hecate.hecate.Runner.

    Implements only the subset of that API this project's tests use: spawning a
    program in a real pty (via pexpect) and screen-scraping its output through an
    in-process VT100 emulator (pyte), instead of shelling out to tmux.
    """

    def __init__(
        self,
        *command: str,
        width: int = DEFAULT_WIDTH,
        height: int = DEFAULT_HEIGHT,
        wait_interval: float = DEFAULT_WAIT_INTERVAL,
        default_timeout: float = DEFAULT_TIMEOUT,
    ) -> None:
        self.wait_interval = wait_interval
        self.default_timeout = default_timeout
        self.screen = pyte.Screen(width, height)
        self.stream = pyte.Stream(self.screen)
        # Pin TERM=xterm so ncurses' escape sequences and pyte's VT100 parsing stay
        # mutually compatible regardless of the host's own TERM.
        env = {**os.environ, "TERM": "xterm"}
        self.child = pexpect.spawn(
            command[0],
            list(command[1:]),
            dimensions=(height, width),
            encoding="utf-8",
            env=env,
        )
        self._shutdown_called = False

    def _pump(self) -> None:
        """Feed any pending output into the screen, waiting for the terminal to go
        quiet (no new output for SETTLE_QUIET_PERIOD) before returning.

        A plain non-blocking read races the child's own input-processing loop: a
        keystroke we just sent may not have been read and rendered yet (this game's
        read loop alone has ~80ms of inherent latency). So a lone timeout doesn't
        mean "nothing is coming" — only a timeout *after* we've already seen some
        output means the terminal has gone quiet and a redraw burst has finished.
        """
        deadline = time.monotonic() + SETTLE_MAX_WAIT
        got_data = False
        while time.monotonic() < deadline:
            try:
                data = self.child.read_nonblocking(size=8192, timeout=SETTLE_QUIET_PERIOD)
                self.stream.feed(data)
                got_data = True
            except pexpect.exceptions.TIMEOUT:
                if got_data:
                    return
            except pexpect.exceptions.EOF:
                return

    def screenshot(self) -> str:
        self._pump()
        # pyte pads every line to the full terminal width; tmux's capture-pane (what
        # hecate used) trims trailing whitespace per line. Match the latter, since
        # that's the shape callers' assertions are written against.
        return "\n".join(line.rstrip() for line in self.screen.display)

    def press(self, key: str) -> None:
        self.child.send(_SPECIAL_KEYS.get(key, key))

    def write(self, text: str) -> None:
        self.child.send(text)

    def await_text(self, text: str, timeout: float | None = None) -> None:
        for _ in self._poll_until_timeout(timeout):
            screen = self.screenshot()
            if text in screen.replace("\n", ""):
                return
        raise Timeout(f"Timeout while waiting for text {text!r} to appear")

    def await_exit(self, timeout: float | None = None) -> None:
        for _ in self._poll_until_timeout(timeout):
            self._pump()
            if not self.child.isalive():
                return
        raise Timeout("Timeout while waiting for process to exit")

    def _poll_until_timeout(self, timeout: float | None) -> Generator[None]:
        if timeout is None:
            timeout = self.default_timeout
        start = time.monotonic()
        while time.monotonic() <= start + timeout:
            yield
            time.sleep(self.wait_interval)

    def shutdown(self) -> None:
        if self._shutdown_called:
            return
        self._shutdown_called = True
        if not self.child.isalive():
            return
        # SIGTERM, not SIGINT: this app's curses.wrapper() cleanup (endwin())
        # can hang indefinitely under a pexpect-controlled pty with nothing on
        # the other end to answer ncurses' terminal queries, so a normal
        # Python-level exception unwind (which SIGINT would trigger) isn't
        # reliable here. When COVERAGE_RUN wraps the child (see
        # tests/minesweeper_test.py), coverage's own `sigterm = true` handler
        # (configured in [tool.coverage]) saves its data directly from a
        # SIGTERM handler instead, sidestepping the app entirely.
        self.child.kill(signal.SIGTERM)
        deadline = time.monotonic() + GRACEFUL_SHUTDOWN_WAIT
        while time.monotonic() < deadline:
            if not self.child.isalive():
                return
            time.sleep(self.wait_interval)
        self.child.terminate(force=True)

    def __enter__(self) -> Self:
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> None:
        self.shutdown()
