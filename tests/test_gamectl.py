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


def test_ioloop_scheduler_in_milliseconds(mocker: MockerFixture) -> None:
    ctl = gamectl.GameCtl()
    mock_callback = mocker.MagicMock(side_effect=[None] * 10)
    mock_sleep = mocker.patch("minesweeper_vim.gamectl.sleep", wraps=gamectl.sleep)
    ctl.register_callback(mock_callback, interval=100)
    with pytest.raises(StopIteration):
        ctl.ioloop()
    mock_sleep.assert_called_with(0.1)
    assert 8 < mock_sleep.call_count <= 12
