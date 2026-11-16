"""Mark Editor TUI -- command-line entry point."""

from __future__ import annotations

import argparse
import sys
from collections.abc import Sequence
from pathlib import Path

from mark_editor_tui.app import MarkEditorApp
from mark_editor_tui.constants import APP_NAME, RELEASE, VERSION


def _program_name() -> str:
    """Return a concise program name for usage and help output."""
    name = Path(sys.argv[0]).name
    if name in {"", "__main__.py", "-c"}:
        return "mark_editor_tui"
    return name


def build_parser(prog: str | None = None) -> argparse.ArgumentParser:
    """Return the command-line argument parser."""
    parser = argparse.ArgumentParser(
        prog=prog or _program_name(),
        description=(
            f"{APP_NAME} {VERSION} -- a terminal Markdown editor built with Textual. "
            "Edit Markdown with syntax highlighting and export to HTML or PDF."
        ),
        epilog=(
            "Without FILE the editor starts with an empty document. "
            "Press F1 for the full shortcut list and F10 to quit."
        ),
    )
    parser.add_argument(
        "file",
        nargs="?",
        metavar="FILE",
        help="Markdown file to open on startup.",
    )
    parser.add_argument(
        "-v",
        "--version",
        action="version",
        version=f"{APP_NAME} {VERSION} ({RELEASE})",
        help="show version information and exit.",
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
