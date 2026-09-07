from __future__ import annotations

import argparse
from collections.abc import Sequence

from minesweeper_vim import __version__, ui


def create_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser()
    parser.add_argument("-V", "--version", action="version", version=__version__)
    parser.add_argument("--seed", type=int, default=0, help="seed for repeatable game")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = create_parser().parse_args(argv)
    return ui.main(args.seed)


if __name__ == "__main__":
    raise SystemExit(main())
