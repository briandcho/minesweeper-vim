import pytest
from minesweeper import game

"""game"""


def test_initial_board_shuffles_mines(mocker):
    assert game.create_board(*game.EASY) != game.create_board(*game.EASY)


def test_initial_board_numbers_mine_adjacent_cells(mocker):
    mocker.patch("minesweeper.game.random")
    assert game.create_board(*game.EASY) == game._to_cells(
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