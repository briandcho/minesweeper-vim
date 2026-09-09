import sys

import pytest
from pytest_mock import MockerFixture

from tests.pty_runner import Runner, Timeout

SLEEP_5S = [sys.executable, "-c", "import time; time.sleep(5)"]


def test_await_text_times_out_when_text_never_appears(mocker: MockerFixture) -> None:
    # _pump() waits up to SETTLE_MAX_WAIT for the *first* byte before giving up,
    # since it can't tell "nothing is coming" apart from "still latent" - fine for
    # the real game (which always outputs something quickly) but it would make
    # this test wait out the full default budget against a silent process.
    mocker.patch("tests.pty_runner.SETTLE_QUIET_PERIOD", 0.05)
    mocker.patch("tests.pty_runner.SETTLE_MAX_WAIT", 0.15)
    with Runner(*SLEEP_5S, wait_interval=0.05) as runner, pytest.raises(Timeout):
        runner.await_text("this text never appears", timeout=0.3)


def test_await_exit_times_out_when_process_still_running(mocker: MockerFixture) -> None:
    mocker.patch("tests.pty_runner.SETTLE_QUIET_PERIOD", 0.05)
    mocker.patch("tests.pty_runner.SETTLE_MAX_WAIT", 0.15)
    with Runner(*SLEEP_5S, wait_interval=0.05) as runner, pytest.raises(Timeout):
        runner.await_exit(timeout=0.3)


def test_shutdown_is_idempotent() -> None:
    with Runner(*SLEEP_5S) as runner:
        runner.shutdown()
        runner.shutdown()  # second call must be a no-op, not raise
        assert not runner.child.isalive()


def test_shutdown_escalates_to_sigkill_when_sigterm_ignored(mocker: MockerFixture) -> None:
    mocker.patch("tests.pty_runner.GRACEFUL_SHUTDOWN_WAIT", 0.3)
    # Print once the ignore-handler is actually installed, so shutdown() can't send
    # its SIGTERM before that - a SIGTERM arriving first would just kill the child
    # via its (still) default disposition, without ever exercising the escalation.
    ignore_sigterm_and_sleep = (
        "import signal, time; "
        "signal.signal(signal.SIGTERM, signal.SIG_IGN); "
        "print('ready'); "
        "time.sleep(5)"
    )
    with Runner(sys.executable, "-c", ignore_sigterm_and_sleep, wait_interval=0.05) as runner:
        runner.await_text("ready")
        runner.shutdown()
        assert not runner.child.isalive()
