import pytest
from minesweeper_vim import game

"""game"""


def test_initial_board_shuffles_mines(mocker):
    game_ = game.create_game(*game.EASY)
    assert game_.board == game_.board
    assert game.create_game(*game.EASY).board != game.create_game(*game.EASY).board


def test_initial_board_numbers_mine_adjacent_cells(mocker):
    mocker.patch("minesweeper_vim.game.random")
    assert game.create_game(*game.EASY).board == game._to_cells(
        [
            ["*", "*", "*", "*", "*", "*", "*", "*", "*", "*"],
            ["2", "3", "3", "3", "3", "3", "3", "3", "3", "2"],
            [" ", " ", " ", " ", " ", " ", " ", " ", " ", " "],
            [" ", " ", " ", " ", " ", " ", " ", " ", " ", " "],
            [" ", " ", " ", " ", " ", " ", " ", " ", " ", " "],
            [" ", " ", " ", " ", " ", " ", " ", " ", " ", " "],
            [" ", " ", " ", " ", " ", " ", " ", " ", " ", " "],
            [" ", " ", " ", " ", " ", " ", " ", " ", " ", " "],
        ]
    )


def test_next_unswept_skip_1():
    board = game._to_cells([["1", " "]])
    board[0][0].is_swept = True
    assert game.next_unswept(board, 0, 0) == (1, 0)


def test_next_unswept_next_row():
    board = game._to_cells([["1", " "], [" ", " "]])
    assert game.next_unswept(board, 0, 0) == (0, 1)


def test_next_unswept_end_of_row():
    board = game._to_cells([[" ", " ", " "]])
    assert game.next_unswept(board, 0, 0) == (2, 0)


def test_next_unswept_skip_unswept():
    board = game._to_cells([[" ", "1", " ", " "]])
    board[0][1].is_swept = True
    assert game.next_unswept(board, 0, 0) == (2, 0)


def test_next_unswept_next_row_skip_1():
    board = game._to_cells([[" ", " "], ["1", " "]])
    board[1][0].is_swept = True
    assert game.next_unswept(board, 0, 0) == (1, 1)


@pytest.mark.parametrize(
    "board, numbered",
    [
        pytest.param([["*", " "], [" ", " "]], [["*", "1"], ["1", "1"]], id="top left"),
        pytest.param(
            [[" ", "*"], [" ", " "]], [["1", "*"], ["1", "1"]], id="top right"
        ),
        pytest.param(
            [[" ", " "], ["*", " "]], [["1", "1"], ["*", "1"]], id="bottom left"
        ),
        pytest.param(
            [[" ", " "], [" ", "*"]], [["1", "1"], ["1", "*"]], id="bottom right"
        ),
        pytest.param(
            [[" ", " ", " "], [" ", "*", " "], [" ", " ", " "]],
            [
                ["1", "1", "1"],
                ["1", "*", "1"],
                ["1", "1", "1"],
            ],
            id="alone",
        ),
    ],
)
def test_number_board(board, numbered):
    assert game.number_board(board) == numbered
