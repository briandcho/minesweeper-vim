import pytest
from pytest_mock import MockerFixture

from minesweeper_vim import gamectl


def test_ioloop_calls_registered_callback(mocker: MockerFixture) -> None:
    ctl = gamectl.GameCtl()
    mock_callback = mocker.MagicMock(side_effect=(None, None))
    ctl.register_callback(mock_callback)
    with pytest.raises(StopIteration):
        ctl.ioloop()
    assert mock_callback.call_count == 3


def test_ioloop_skips_timer_before_its_deadline(mocker: MockerFixture) -> None:
    ctl = gamectl.GameCtl()
    due_callback = mocker.MagicMock(side_effect=(None, None))
    not_yet_due_callback = mocker.MagicMock()
    ctl.register_callback(due_callback, interval=100)
    # 10s out: guaranteed to still be in the future for the whole (sub-second) test,
    # so its deadline check reliably evaluates False - unlike two similarly-timed
    # callbacks, whose relative firing order isn't deterministic.
    ctl.register_callback(not_yet_due_callback, interval=10_000)
    with pytest.raises(StopIteration):
        ctl.ioloop()
    assert due_callback.call_count == 3
    not_yet_due_callback.assert_not_called()


def test_ioloop_scheduler_in_milliseconds(mocker: MockerFixture) -> None:
    ctl = gamectl.GameCtl()
    mock_callback = mocker.MagicMock(side_effect=[None] * 10)
    mock_sleep = mocker.patch("minesweeper_vim.gamectl.sleep", wraps=gamectl.sleep)
    ctl.register_callback(mock_callback, interval=100)
    with pytest.raises(StopIteration):
        ctl.ioloop()
    mock_sleep.assert_called_with(0.1)
    assert 8 < mock_sleep.call_count <= 12
