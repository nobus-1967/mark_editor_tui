"""Mark Editor TUI -- entry point."""

from __future__ import annotations

import argparse
import sys
from collections.abc import Sequence
from pathlib import Path

from mark_editor_tui.app import MarkEditorApp
from mark_editor_tui.constants import APP_NAME, RELEASE, VERSION


def build_parser() -> argparse.ArgumentParser:
    """Return the command-line argument parser."""
    parser = argparse.ArgumentParser(
        prog="mark_editor_tui",
        description=f"{APP_NAME} {VERSION} -- a terminal Markdown editor.",
    )
    parser.add_argument(
        "file",
        nargs="?",
        help="Markdown file to open on startup.",
    )
    parser.add_argument(
        "--version",
        action="version",
        version=f"{APP_NAME} {VERSION} ({RELEASE})",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> None:
    """Parse the command line and run the Textual application."""
    args = build_parser().parse_args(argv)
    initial_file = Path(args.file).expanduser() if args.file else None
    if initial_file is not None and not initial_file.exists():
        print(f"{APP_NAME}: cannot open {initial_file}: no such file", file=sys.stderr)
        raise SystemExit(1)
    MarkEditorApp(initial_file=initial_file).run()


if __name__ == "__main__":
    main()
