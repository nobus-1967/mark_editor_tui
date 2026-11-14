"""Markdown editor widget built on Textual's TextArea."""

from __future__ import annotations

from textual.binding import Binding
from textual.widgets import TextArea

from mark_editor_tui.constants import DEFAULT_THEME
from mark_editor_tui.themes import EDITOR_THEMES


class MarkdownEditor(TextArea):
    """A Markdown TextArea with the application colour themes.

    The editor keeps the normal TextArea navigation keys, but exposes a small
    set of helpers used by the application actions. Global shortcuts live on
    the application so that they work regardless of focus.
    """

    BINDINGS = [
        Binding("shift+tab", "outdent", "Outdent", show=False),
    ]

    def __init__(self, text: str = "", *, mode: str = DEFAULT_THEME, **kwargs) -> None:
        """Create a Markdown editor using the colour theme for *mode*."""
        super().__init__(
            text,
            language="markdown",
            theme="css",
            tab_behavior="indent",
            show_line_numbers=True,
            soft_wrap=True,
            highlight_cursor_line=True,
            **kwargs,
        )
        for theme in EDITOR_THEMES.values():
            self.register_theme(theme)
        self.theme = EDITOR_THEMES.get(mode, EDITOR_THEMES[DEFAULT_THEME]).name

    @property
    def cursor_row(self) -> int:
        """Return the 0-based cursor row."""
        return self.cursor_location[0]

    @property
    def line_count(self) -> int:
        """Return the number of lines in the document."""
        return self.document.line_count

    @property
    def current_line(self) -> str:
        """Return the text of the current line."""
        return str(self.get_line(self.cursor_row))

    def line_text(self, row: int) -> str:
        """Return the text of 0-based *row*."""
        if row < 0 or row >= self.line_count:
            return ""
        return str(self.get_line(row))

    def lines(self) -> list[str]:
        """Return all document lines as plain strings."""
        return [str(self.document[row]) for row in range(self.line_count)]

    def replace_whole_text(
        self, text: str, *, cursor_row: int = 0, cursor_col: int = 0
    ) -> None:
        """Replace the whole document and place the cursor at a line/column."""
        end = self.document.end
        self.replace(text, (0, 0), end, maintain_selection_offset=False)
        row = max(0, min(cursor_row, self.line_count - 1))
        col = max(0, min(cursor_col, len(self.line_text(row))))
        self.move_cursor((row, col))

    def replace_line(
        self, row: int, text: str, *, cursor_col: int | None = None
    ) -> None:
        """Replace 0-based *row* with *text*."""
        if row < 0 or row >= self.line_count:
            return
        old = self.line_text(row)
        self.replace(text, (row, 0), (row, len(old)), maintain_selection_offset=False)
        col = len(text) if cursor_col is None else cursor_col
        self.move_cursor((row, max(0, min(col, len(text)))))

    def replace_selection(self, text: str) -> None:
        """Replace the selection (or insert at the cursor) with *text*."""
        start, end = self.selection
        self.replace(text, start, end, maintain_selection_offset=False)
        self.move_cursor(self._location_after_insert(start, text))

    def _location_after_insert(self, start, text: str):
        """Return the document location just after *text* inserted at *start*."""
        offset = self.document.get_index_from_location(start) + len(text)
        return self.document.get_location_from_index(offset)

    def wrap_selection(self, wrapper: str) -> None:
        """Wrap the selection, or insert an empty pair at the cursor."""
        start, end = self.selection
        if start != end:
            selected = self.selected_text
            wrapped = f"{wrapper}{selected}{wrapper}"
            self.replace(wrapped, start, end, maintain_selection_offset=False)
            self.move_cursor(self._location_after_insert(start, wrapped))
        else:
            self.insert(f"{wrapper}{wrapper}")
            offset = self.document.get_index_from_location(self.cursor_location) - len(
                wrapper
            )
            self.move_cursor(self.document.get_location_from_index(offset))

    def selection_line_range(self) -> tuple[int, int]:
        """Return the inclusive 0-based line range covered by the selection."""
        start, end = self.selection
        start_row = start[0]
        end_row = end[0]
        if end[1] == 0 and end_row > start_row:
            end_row -= 1
        return start_row, end_row

    def select_lines(self, start_row: int, end_row: int) -> None:
        """Select whole lines from *start_row* to *end_row* inclusive."""
        start = (max(0, start_row), 0)
        end = self.document.end if end_row + 1 >= self.line_count else (end_row + 1, 0)
        self.selection = (start, end)

    def set_cursor(self, row: int, col: int = 0) -> None:
        """Move the cursor to a 0-based row and column."""
        row = max(0, min(row, self.line_count - 1))
        col = max(0, min(col, len(self.line_text(row))))
        self.move_cursor((row, col))

    def action_outdent(self) -> None:
        """Remove indentation from the current line or selected lines."""
        self.app.action_remove_indent()
