from typing import Optional

import pytest
from pytest_mock import MockerFixture

from minesweeper_vim import ui


def test_ed_handle_keypress() -> None:
    ed = ui.EdComponent(1)
    assert ed.handle_keypress(ord("\n")) is None
    assert ed.handle_keypress(ord("l")) == ui.Cursor(1, 8)
    assert ed.handle_keypress(ord("w")) == ui.Cursor(1, 17)
    assert ed.handle_keypress(ord("h")) == ui.Cursor(1, 8)
    assert ed.handle_keypress(ord("b")) == ui.Cursor(1, 2)
    assert ed.handle_keypress(ord("H")) == ui.Cursor(1, 2)
    assert ed.handle_keypress(ord("?")) == ui.Cursor(1, 28)
    assert ed.handle_keypress(ord("q")) == ui.Cursor(1, 22)
    assert ed.handle_keypress(ord("a")) == ui.Cursor(1, 17)
    assert ed.handle_keypress(ord("m")) == ui.Cursor(1, 8)
    assert ed.handle_keypress(ord("e")) == ui.Cursor(1, 2)


@pytest.mark.parametrize(
    "key,cursor",
    [
        pytest.param(ord(":"), None, id="goto ed"),
        pytest.param(ord("q"), ui.Cursor(2, 4), id="unimplemented"),
        pytest.param(ord("h"), ui.Cursor(2, 1), id="left"),
        pytest.param(ord("l"), ui.Cursor(2, 7), id="right"),
        pytest.param(ord("k"), ui.Cursor(1, 4), id="up"),
        pytest.param(ord("j"), ui.Cursor(3, 4), id="down"),
        pytest.param(ord("0"), ui.Cursor(2, 1), id="beginning of line"),
        pytest.param(ord("$"), ui.Cursor(2, 31), id="end of line"),
        pytest.param(ord("H"), ui.Cursor(1, 1), id="beginning of first row"),
        pytest.param(ord("L"), ui.Cursor(8, 1), id="beginning of last row"),
        pytest.param(ord("M"), ui.Cursor(5, 1), id="beginning of middle row"),
    ],
)
def test_board_handle_keypress(key: int, cursor: Optional[ui.Cursor]) -> None:
    board = ui.BoardComponent(*ui.game.EASY[:2])
    board._cursor = ui.Cursor(2, 4)
    assert board.handle_keypress(key) == cursor


@pytest.mark.parametrize(
    "key,cursor",
    [("a", ui.Cursor(9, 17)), ("\n", ui.Cursor(1, 1))],
)
def test_app_handle_keypress(
    key: str,
    cursor: ui.Cursor,
    mocker: MockerFixture,
) -> None:
    mock_scr = mocker.MagicMock()
    mock_scr.get_wch.return_value = key
    app = ui.GameApp(mock_scr, ui.game.create_game(*ui.game.EASY))
    app.handle_keypress()
    assert app.cursor == cursor
