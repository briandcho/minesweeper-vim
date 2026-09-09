# minesweeper-vim

Curses-based minesweeper with (sort of) vim bindings

## Installation

Install from PyPI:

```sh
pip install minesweeper-vim
```

## Usage

Run the game:

```sh
minesweeper-vim
# or, for a repeatable board:
minesweeper-vim --seed 1
```

Display the version:

```sh
minesweeper-vim --version
# or
minesweeper-vim -V
```

## Controls

```
       [Up]             [k]
[Left][Down][Right]  [h][j][l]

[x] = sweep cell
[m] = mark flag

[Backspace] = left
    [Space] = right
   [Return] = beginning of next row
        [0] = beginning of row
        [$] = end of row
        [w] = next unswept row
        [b] = previous unswept row
        [H] = beginning of 1st row
        [M] = beginning of middle row
        [L] = beginning of bottom row
```

## Development

### First-time setup

If this isn't already a git repo, run `git init` before `tox` — `setuptools-scm` computes the
package version from git metadata and errors out (`ERROR setuptools-scm was unable to detect
version`) outside a git repo.

`requirements.txt`/`requirements-dev.txt` (pinned via `pip-compile`) are checked in, so `tox -e py`
and bare `tox` can install from them directly. Run `tox -e update_deps` to refresh the pins.

### Install pre-commit hooks (including commit message checks)

This repo enforces Conventional Commits via a `commit-msg` hook (Commitizen). Most checks run on every commit; `pip-audit` (a network-bound dependency vulnerability scan) and `checkov` (an IaC scanner) are deferred to `pre-push` so they don't slow down every commit.

Install hooks locally:

```sh
pre-commit install --hook-type pre-commit --hook-type pre-push --hook-type commit-msg
# optional: run all hooks (including pip-audit) against the repo once
pre-commit run --all-files --hook-stage pre-push
```

If you see a commit rejected, format your message using Conventional Commits, for example:

```text
feat: add new subcommand
fix(cli): handle empty args
chore(deps): weekly dependency updates
```

You can also use Commitizen to guide you:

```sh
cz commit
# or without installing: pipx run commitizen commit
```

### Use tox for development

This project uses `tox` to run tests and checks consistently across environments.

- Run the fast tests (no e2e, no coverage) for quick local iteration:

```sh
tox -e py
```

- Run the full suite, including the slow e2e tests that spawn the game as a real subprocess, with
  the 100% coverage gate:

```sh
tox -e full
```

- Run all pre-commit hooks (format, lint, type-check, security, etc.):

```sh
tox -e pre-commit
```

- Run the pre-push-only checks too (`pip-audit`, `checkov`, and the `tox -e full` test suite) by
  passing extra args through to `pre-commit run` after `--`:

```sh
tox -e pre-commit -- --hook-stage pre-push
```

`tox -e full` also runs automatically on `git push` (if the pre-push hook type is installed, same
as `pip-audit`/`checkov`) and is what CI runs — `tox -e py` is only for local iteration.

- Update pinned dependencies and pre-commit hooks:

```sh
tox -e update_deps
```
