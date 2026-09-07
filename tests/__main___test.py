import pytest
from pytest_mock import MockerFixture

from minesweeper_vim import __version__
from minesweeper_vim.__main__ import main


@pytest.mark.parametrize(
    "flag",
    [
        "--version",
        "-V",
    ],
)
def test_version_string(flag, capsys):
    with pytest.raises(SystemExit) as exc:
        main([flag])
    assert exc.value.code == 0
    out, _ = capsys.readouterr()
    assert out.strip() == __version__


def test_main_without_args(mocker: MockerFixture):
    mock_ui_main = mocker.patch("minesweeper_vim.__main__.ui.main", return_value=0)
    assert main([]) == 0
    mock_ui_main.assert_called_once_with(0)


def test_main_passes_seed(mocker: MockerFixture):
    mock_ui_main = mocker.patch("minesweeper_vim.__main__.ui.main", return_value=0)
    assert main(["--seed", "42"]) == 0
    mock_ui_main.assert_called_once_with(42)
