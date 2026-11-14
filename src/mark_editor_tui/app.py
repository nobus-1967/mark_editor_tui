"""Textual application for Mark Editor TUI 0.1."""

from __future__ import annotations

import contextlib
import re
from collections.abc import Callable
from datetime import datetime
from pathlib import Path
from typing import Any, cast

from textual import on
from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.command import DiscoveryHit, Hit, Hits, Provider
from textual.containers import Vertical
from textual.screen import ModalScreen
from textual.widgets import Static, TextArea
from textual.widgets.text_area import Selection

from mark_editor_tui import markdown_ops
from mark_editor_tui.constants import (
    APP_NAME,
    DEFAULT_THEME,
    EMOJIS,
    EXPORT_FORMATS,
    LANGUAGE_CODES,
    LANGUAGE_TAGS,
    SPECIAL_SIGNS,
    THEMES,
    VERSION,
)
from mark_editor_tui.editor import MarkdownEditor
from mark_editor_tui.help_text import about_markdown, shortcuts_markdown
from mark_editor_tui.helpers import (
    add_heading_ids,
    add_toc,
    cleanup_temp_html,
    cleanup_temp_md,
    ensure_cache_dir,
    load_temp_md,
    load_theme,
    md_to_html,
    md_to_pdf,
    md_to_plain,
    regenerate_toc,
    remove_toc,
    save_temp_md,
    save_theme,
)
from mark_editor_tui.menubar import FunctionKeyBar, MenuBar
from mark_editor_tui.screens import (
    ConfirmScreen,
    FieldSpec,
    FileDialogScreen,
    FindScreen,
    FormScreen,
    InfoScreen,
    MenuScreen,
    ReplaceScreen,
)
from mark_editor_tui.themes import APP_THEMES, EDITOR_THEMES

Command = tuple[str, Callable[[], Any], str]

APP_ROOT = Path(__file__).resolve().parent
STYLES_PATH = APP_ROOT / "styles.tcss"


class EditorCommands(Provider):
    """Command-palette provider for every Mark Editor TUI command."""

    async def search(self, query: str) -> Hits:
        """Search application commands by name."""
        matcher = self.matcher(query)
        app = cast("MarkEditorApp", self.app)
        for label, callback, help_text in app.command_items():
            score = matcher.match(label)
            if score > 0:
                yield Hit(score, matcher.highlight(label), callback, help=help_text)

    async def discover(self) -> Hits:
        """Show all application commands when the palette is empty."""
        app = cast("MarkEditorApp", self.app)
        for label, callback, help_text in app.command_items():
            yield DiscoveryHit(label, callback, help=help_text)


class MarkEditorApp(App[None]):
    """Main Textual application."""

    CSS_PATH = str(STYLES_PATH)
    TITLE = APP_NAME
    SUB_TITLE = f"v{VERSION}"
    COMMANDS = App.COMMANDS | {EditorCommands}
    COMMAND_PALETTE_DISPLAY = "Ctrl+P"
    ENABLE_COMMAND_PALETTE = True

    BINDINGS = [
        Binding("f1", "help_shortcuts", "Help", show=True, priority=True),
        Binding("f2", "save_file", "Save", show=True, priority=True),
        Binding("f3", "save_as", "Save As", show=True, priority=True),
        Binding("f4", "find", "Find", show=True, priority=True),
        Binding("f5", "replace", "Replace", show=True, priority=True),
        Binding("f6", "select_all", "Select all", show=True, priority=True),
        Binding("f7", "cut", "Cut", show=True, priority=True),
        Binding("f8", "copy", "Copy", show=True, priority=True),
        Binding("f9", "paste", "Paste", show=True, priority=True),
        Binding("f10", "quit", "Quit", show=True, priority=True),
        Binding("f11", "undo", "Undo", show=True, priority=True),
        Binding("f12", "redo", "Redo", show=True, priority=True),
        Binding("ctrl+n", "new_file", "New", show=False, priority=True),
        Binding("ctrl+o", "open_file", "Open", show=False, priority=True),
        Binding("ctrl+shift+o", "reopen_file", "Reopen", show=False, priority=True),
        Binding("ctrl+s", "save_file", "Save", show=False, priority=True),
        Binding("ctrl+shift+s", "save_as", "Save As", show=False, priority=True),
        Binding("ctrl+e", "export", "Export", show=False, priority=True),
        Binding("ctrl+z", "undo", "Undo", show=False, priority=True),
        Binding("ctrl+y", "redo", "Redo", show=False, priority=True),
        Binding("ctrl+x", "cut", "Cut", show=False, priority=True),
        Binding("shift+delete", "cut", "Cut", show=False, priority=True),
        Binding("ctrl+c", "copy", "Copy", show=False, priority=True),
        Binding("ctrl+v", "paste", "Paste", show=False, priority=True),
        Binding("shift+insert", "paste", "Paste", show=False, priority=True),
        Binding("ctrl+a", "select_all", "Select all", show=False, priority=True),
        Binding("ctrl+f", "find", "Find", show=False, priority=True),
        Binding("ctrl+r", "replace", "Replace", show=False, priority=True),
        Binding("alt+up", "line_up", "Line up", show=False, priority=True),
        Binding("alt+down", "line_down", "Line down", show=False, priority=True),
        Binding(
            "ctrl+underscore", "go_to_line", "Go to line", show=False, priority=True
        ),
        Binding("alt+d", "delete_line", "Delete line", show=False, priority=True),
        Binding(
            "ctrl+shift+a", "remove_selection", "Deselect", show=False, priority=True
        ),
        Binding("ctrl+b", "bold", "Bold", show=False, priority=True),
        Binding("alt+i", "italic", "Italic", show=False, priority=True),
        Binding("ctrl+u", "underline", "Underline", show=False, priority=True),
        Binding("ctrl+d", "strikethrough", "Strikethrough", show=False, priority=True),
        Binding(
            "ctrl+shift+p", "superscript", "Superscript", show=False, priority=True
        ),
        Binding("ctrl+shift+b", "subscript", "Subscript", show=False, priority=True),
        Binding("ctrl+k", "inline_code", "Inline code", show=False, priority=True),
        Binding("ctrl+shift+m", "mark_text", "Mark", show=False, priority=True),
        Binding("alt+h", "header_id", "Header ID", show=False, priority=True),
        Binding(
            "ctrl+shift+h", "header_link", "Header link", show=False, priority=True
        ),
        Binding("ctrl+shift+e", "toc", "TOC", show=False, priority=True),
        Binding("ctrl+l", "hyperlink", "Hyperlink", show=False, priority=True),
        Binding("ctrl+shift+u", "footnote", "Footnote", show=False, priority=True),
        Binding(
            "ctrl+w", "language_marker", "Language marker", show=False, priority=True
        ),
        Binding(
            "alt+w", "language_marker", "Language marker", show=False, priority=True
        ),
        Binding(
            "alt+shift+w",
            "language_wrapping",
            "Language wrap",
            show=False,
            priority=True,
        ),
        Binding("ctrl+shift+j", "furigana", "Furigana", show=False, priority=True),
        Binding("ctrl+shift+d", "date_time", "Date/time", show=False, priority=True),
        Binding("alt+m", "comment", "Comment", show=False, priority=True),
        Binding(
            "ctrl+shift+l", "special_mark", "Special mark", show=False, priority=True
        ),
        Binding(
            "alt+shift+f",
            "clear_formatting",
            "Clear formatting",
            show=False,
            priority=True,
        ),
        Binding("alt+1", "heading_1", "H1", show=False, priority=True),
        Binding("alt+2", "heading_2", "H2", show=False, priority=True),
        Binding("alt+3", "heading_3", "H3", show=False, priority=True),
        Binding("alt+4", "heading_4", "H4", show=False, priority=True),
        Binding("alt+5", "heading_5", "H5", show=False, priority=True),
        Binding("alt+6", "heading_6", "H6", show=False, priority=True),
        Binding("alt+0", "paragraph", "Paragraph", show=False, priority=True),
        Binding("ctrl+g", "ordered_list", "Ordered list", show=False, priority=True),
        Binding(
            "ctrl+shift+g",
            "unordered_list",
            "Unordered list",
            show=False,
            priority=True,
        ),
        Binding("alt+c", "todo_list", "Todo list", show=False, priority=True),
        Binding(
            "ctrl+shift+x",
            "definition_list",
            "Definition list",
            show=False,
            priority=True,
        ),
        Binding("alt+shift+k", "code_block", "Code block", show=False, priority=True),
        Binding("alt+q", "blockquote", "Blockquote", show=False, priority=True),
        Binding("ctrl+t", "table", "Table", show=False, priority=True),
        Binding(
            "ctrl+shift+r", "add_table_row", "Table row", show=False, priority=True
        ),
        Binding(
            "alt+shift+t",
            "table_alignment",
            "Table alignment",
            show=False,
            priority=True,
        ),
        Binding(
            "alt+shift+n", "balance_table", "Balance table", show=False, priority=True
        ),
        Binding("alt+g", "image", "Image", show=False, priority=True),
        Binding(
            "alt+-", "horizontal_rule", "Horizontal rule", show=False, priority=True
        ),
        Binding("alt+enter", "line_break", "Line break", show=False, priority=True),
        Binding("ctrl+shift+y", "yaml_front_matter", "YAML", show=False, priority=True),
        Binding("alt+t", "toggle_theme", "Theme", show=False, priority=True),
        Binding("alt+l", "language_codes", "Language codes", show=False, priority=True),
        Binding("alt+e", "emoji", "Emoji", show=False, priority=True),
        Binding("alt+s", "special_signs", "Signs", show=False, priority=True),
    ]

    COMMAND_SPECS: tuple[tuple[str, str, str, str], ...] = (
        ("File", "New File", "action_new_file", "Ctrl+N"),
        ("File", "Open...", "action_open_file", "Ctrl+O"),
        ("File", "Reopen", "action_reopen_file", "Ctrl+Shift+O"),
        ("File", "Save", "action_save_file", "Ctrl+S / F2"),
        ("File", "Save As...", "action_save_as", "Ctrl+Shift+S / F3"),
        ("File", "Export...", "action_export", "Ctrl+E"),
        ("File", "Toggle Theme", "action_toggle_theme", "Alt+T"),
        ("File", "Quit", "action_quit", "F10"),
        ("Edit", "Undo", "action_undo", "F11"),
        ("Edit", "Redo", "action_redo", "F12"),
        ("Edit", "Cut", "action_cut", "F7 / Shift+Delete"),
        ("Edit", "Copy", "action_copy", "F8 / Ctrl+C"),
        ("Edit", "Paste", "action_paste", "F9 / Shift+Insert"),
        ("Edit", "Find...", "action_find", "F4 / Ctrl+F"),
        ("Edit", "Replace...", "action_replace", "F5 / Ctrl+R"),
        ("Edit", "Select All", "action_select_all", "F6 / Ctrl+A"),
        ("Edit", "Remove Selection", "action_remove_selection", "Ctrl+Shift+A"),
        ("Edit", "Line Up", "action_line_up", "Alt+Up"),
        ("Edit", "Line Down", "action_line_down", "Alt+Down"),
        ("Edit", "Go to Line...", "action_go_to_line", "Ctrl+_"),
        ("Edit", "Delete Line", "action_delete_line", "Alt+D"),
        ("Format", "Bold", "action_bold", "Ctrl+B"),
        ("Format", "Italic", "action_italic", "Alt+I"),
        ("Format", "Underline", "action_underline", "Ctrl+U"),
        ("Format", "Strikethrough", "action_strikethrough", "Ctrl+D"),
        ("Format", "Superscript", "action_superscript", "Ctrl+Shift+P"),
        ("Format", "Subscript", "action_subscript", "Ctrl+Shift+B"),
        ("Format", "Inline Code", "action_inline_code", "Ctrl+K"),
        ("Format", "Mark", "action_mark_text", "Ctrl+Shift+M"),
        ("Format", "Hyperlink...", "action_hyperlink", "Ctrl+L"),
        ("Format", "Header ID...", "action_header_id", "Alt+H"),
        ("Format", "Header Link...", "action_header_link", "Ctrl+Shift+H"),
        ("Format", "TOC...", "action_toc", "Ctrl+Shift+E"),
        ("Format", "Footnote...", "action_footnote", "Ctrl+Shift+U"),
        ("Format", "Date and Time...", "action_date_time", "Ctrl+Shift+D"),
        ("Format", "Language Marker...", "action_language_marker", "Ctrl+W"),
        ("Format", "Language Wrapping...", "action_language_wrapping", "Alt+Shift+W"),
        ("Format", "Language Codes...", "action_language_codes", "Alt+L"),
        ("Format", "Furigana...", "action_furigana", "Ctrl+Shift+J"),
        ("Format", "Emoji...", "action_emoji", "Alt+E"),
        ("Format", "Special Signs...", "action_special_signs", "Alt+S"),
        ("Format", "Special Mark", "action_special_mark", "Ctrl+Shift+L"),
        ("Format", "Clear Formatting", "action_clear_formatting", "Alt+Shift+F"),
        ("Paragraph", "Heading 1", "action_heading_1", "Alt+1"),
        ("Paragraph", "Heading 2", "action_heading_2", "Alt+2"),
        ("Paragraph", "Heading 3", "action_heading_3", "Alt+3"),
        ("Paragraph", "Heading 4", "action_heading_4", "Alt+4"),
        ("Paragraph", "Heading 5", "action_heading_5", "Alt+5"),
        ("Paragraph", "Heading 6", "action_heading_6", "Alt+6"),
        ("Paragraph", "Paragraph", "action_paragraph", "Alt+0"),
        ("Paragraph", "Ordered List...", "action_ordered_list", "Ctrl+G"),
        ("Paragraph", "Unordered List", "action_unordered_list", "Ctrl+Shift+G"),
        ("Paragraph", "Todo List...", "action_todo_list", "Alt+C"),
        ("Paragraph", "Definition List...", "action_definition_list", "Ctrl+Shift+X"),
        ("Paragraph", "Code Block...", "action_code_block", "Alt+Shift+K"),
        ("Paragraph", "Blockquote", "action_blockquote", "Alt+Q"),
        ("Paragraph", "Table...", "action_table", "Ctrl+T"),
        ("Paragraph", "Add Table Row...", "action_add_table_row", "Ctrl+Shift+R"),
        ("Paragraph", "Table Alignment...", "action_table_alignment", "Alt+Shift+T"),
        ("Paragraph", "Balance Table", "action_balance_table", "Alt+Shift+N"),
        ("Paragraph", "Image...", "action_image", "Alt+G"),
        ("Paragraph", "Horizontal Rule", "action_horizontal_rule", "Alt+-"),
        ("Paragraph", "Comment...", "action_comment", "Alt+M"),
        (
            "Paragraph",
            "YAML Front Matter...",
            "action_yaml_front_matter",
            "Ctrl+Shift+Y",
        ),
        ("Paragraph", "Line Break", "action_line_break", "Alt+Enter"),
        ("Paragraph", "Add Indent", "action_add_indent", "Tab"),
        ("Paragraph", "Remove Indent", "action_remove_indent", "Shift+Tab"),
        ("Help", "Keyboard Shortcuts", "action_help_shortcuts", "F1"),
        ("Help", "About Editor", "action_about", ""),
    )

    EXPORT_COMMANDS: tuple[tuple[str, str, str], ...] = (
        ("Export: HTML5", "html", "HTML5 without embedded CSS"),
        ("Export: HTML5 + CSS", "html_css", "HTML5 with embedded CSS3"),
        ("Export: PDF (portrait)", "pdf", "PDF in portrait orientation"),
        ("Export: PDF (landscape)", "pdf_landscape", "PDF in landscape orientation"),
        ("Export: Plain text", "text", "Plain text without Markdown syntax"),
    )

    def __init__(self, initial_file: Path | None = None) -> None:
        """Create the application, optionally opening *initial_file*."""
        super().__init__()
        for theme in APP_THEMES.values():
            self.register_theme(theme)
        self.initial_file = initial_file
        self.current_file: Path | None = None
        self.is_modified = False
        self.theme_mode = load_theme()
        self._suppress_change = 0

    def get_theme_variable_defaults(self) -> dict[str, str]:
        """Return fallback theme variables used while the stylesheet loads."""
        mode = getattr(self, "theme_mode", DEFAULT_THEME)
        return dict(APP_THEMES.get(mode, APP_THEMES[DEFAULT_THEME]).variables)

    def compose(self) -> ComposeResult:
        """Build the menu bar, editor, status bar and function-key bar."""
        with Vertical(id="main"):
            yield MenuBar()
            yield MarkdownEditor(text="", id="editor", mode=self.theme_mode)
            yield Static("Ln 1, Col 1", id="status")
        yield FunctionKeyBar()

    async def on_function_key_bar_key_pressed(
        self, event: FunctionKeyBar.KeyPressed
    ) -> None:
        """Run the action of a clicked function key."""
        event.stop()
        await self.run_action(event.action)

    @property
    def editor(self) -> MarkdownEditor:
        """Return the Markdown editor widget."""
        return self.query_one("#editor", MarkdownEditor)

    def on_mount(self) -> None:
        """Apply the saved theme, restore a session or open the initial file."""
        self._apply_theme(self.theme_mode)
        self.editor.focus()
        if self.initial_file is not None:
            self._open_path(self.initial_file)
        else:
            self._restore_pending_text()
        self._update_title()
        self._update_status()

    def check_action(self, action: str, _parameters: tuple[object, ...]) -> bool:
        """Disable editor shortcuts while a modal dialog is open.

        Modal screens own their keyboard input.  Application-level priority
        bindings would otherwise steal keys such as Ctrl+A or Ctrl+Z from the
        text fields inside a dialog.
        """
        return not (isinstance(self.screen, ModalScreen) and action != "quit")

    def on_unmount(self) -> None:
        """Remove temporary files when the application closes."""
        self._cleanup_temp_files()

    def _update_title(self) -> None:
        """Refresh the window title with the file name and modified marker."""
        symbol = "*" if self.is_modified else ""
        name = self.current_file.name if self.current_file else "New File"
        self.title = f"{APP_NAME} - {symbol}{name}"
        self.sub_title = f"v{VERSION}"

    def _update_status(self) -> None:
        """Update line/column, selection and file information."""
        try:
            editor = self.editor
            row, col = editor.cursor_location
            selected = len(editor.selected_text)
            name = self.current_file.name if self.current_file else "untitled"
            mark = "*" if self.is_modified else ""
            selection = f"   Sel {selected}" if selected else ""
            text = (
                f" Ln {row + 1}, Col {col + 1}{selection}"
                f"   {mark}{name}   UTF-8   LF   Markdown "
            )
            self.query_one("#status", Static).update(text)
        except Exception:
            pass

    @on(TextArea.Changed)
    def _on_text_changed(self, _event: TextArea.Changed) -> None:
        """Track modifications and autosave the current buffer."""
        if self._suppress_change:
            self._suppress_change -= 1
            self._update_status()
            return
        self.is_modified = True
        self._update_title()
        self._update_status()
        with contextlib.suppress(OSError):
            save_temp_md(self.editor.text, self.current_file)

    @on(TextArea.SelectionChanged)
    def _on_selection_changed(self, _event: TextArea.SelectionChanged) -> None:
        """Refresh the cursor position in the status bar."""
        self._update_status()

    def _load_text(self, text: str) -> None:
        """Load text without marking the document as modified."""
        self._suppress_change += 1
        self.editor.load_text(text)

    def _apply_theme(self, mode: str) -> None:
        """Apply the default, green, magenta or blue colour theme."""
        mode = mode if mode in THEMES else DEFAULT_THEME
        self.theme_mode = mode
        self.theme = APP_THEMES[mode].name
        with contextlib.suppress(Exception):
            self.editor.theme = EDITOR_THEMES[mode].name

    def action_toggle_theme(self) -> None:
        """Cycle through the default, green, magenta and blue themes."""
        next_index = (THEMES.index(self.theme_mode) + 1) % len(THEMES)
        self._apply_theme(THEMES[next_index])
        save_theme(self.theme_mode)
        self.notify(f"Theme: {self.theme_mode}")

    def _restore_pending_text(self) -> None:
        """Restore an unsaved buffer left by a previous session."""
        text = load_temp_md(None)
        if text and text.strip():
            self._load_text(text)
            self.is_modified = True
            self.notify("Restored unsaved text from the previous session")

    def _cleanup_temp_files(self) -> None:
        """Delete the temporary Markdown and HTML files for this document."""
        if self.current_file is not None:
            cleanup_temp_md(self.current_file.parent)
            cleanup_temp_html(self.current_file.parent)
        else:
            cleanup_temp_md(ensure_cache_dir())
            cleanup_temp_html(ensure_cache_dir())

    def _open_path(self, path: Path) -> None:
        """Load *path* into the editor."""
        path = path.expanduser().resolve()
        try:
            text = path.read_text(encoding="utf-8")
        except OSError as exc:
            self.notify(
                f"Cannot open {path}: {exc}", title="Open file", severity="error"
            )
            return
        old_file = self.current_file
        self._load_text(text)
        self.current_file = path
        self.is_modified = False
        if old_file is not None and old_file.parent != path.parent:
            cleanup_temp_md(old_file.parent)
        self._update_title()
        self._update_status()
        self.editor.focus()
        self.notify(f"Opened {path.name}")

    def _save_to(self, path: Path) -> None:
        """Write the current buffer to *path*."""
        path = path.expanduser()
        if not path.suffix:
            path = path.with_suffix(".md")
        try:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(self.editor.text, encoding="utf-8")
        except OSError as exc:
            self.notify(
                f"Cannot save {path}: {exc}", title="Save file", severity="error"
            )
            return
        self.current_file = path
        self.is_modified = False
        self._update_title()
        self._update_status()
        self.editor.focus()
        self.notify(f"Saved {path}")

    def _confirm_discard(self, callback: Callable[[], None]) -> None:
        """Run *callback* after confirming that unsaved changes may be lost."""
        if not self.is_modified:
            callback()
            return

        def on_result(result: bool | None) -> None:
            """Discard the document when the user confirms."""
            if result:
                callback()

        self.push_screen(
            ConfirmScreen(
                "The document has unsaved changes. Discard them?",
                title="Unsaved changes",
            ),
            on_result,
        )

    def action_new_file(self) -> None:
        """Create an empty document."""
        self._confirm_discard(self._new_file)

    def _new_file(self) -> None:
        """Reset the editor to an empty untitled document."""
        old_file = self.current_file
        self._load_text("")
        self.current_file = None
        self.is_modified = False
        if old_file is not None:
            cleanup_temp_md(old_file.parent)
        self._update_title()
        self._update_status()
        self.editor.focus()

    def action_open_file(self) -> None:
        """Show the open-file dialog."""
        self._confirm_discard(self._show_open_dialog)

    def _show_open_dialog(self) -> None:
        """Push the open-file dialog."""
        self.push_screen(
            FileDialogScreen(
                mode="open",
                title="Open Markdown file",
                start=self.current_file.parent if self.current_file else Path.cwd(),
                patterns=("*.md", "*.markdown", "*.txt"),
            ),
            self._open_dialog_result,
        )

    def _open_dialog_result(self, path: Path | None) -> None:
        """Open the selected file."""
        if path is not None:
            self._open_path(path)

    def action_reopen_file(self) -> None:
        """Reload the current file from disk."""
        if self.current_file is None:
            self.notify("No file is open", severity="warning")
            return
        self._confirm_discard(self._reopen_file)

    def _reopen_file(self) -> None:
        """Reload the current file without changing its path."""
        if self.current_file is None:
            return
        try:
            text = self.current_file.read_text(encoding="utf-8")
        except OSError as exc:
            self.notify(str(exc), title="Reopen file", severity="error")
            return
        self._load_text(text)
        self.is_modified = False
        self._update_title()
        self._update_status()
        self.editor.focus()
        self.notify("File reopened")

    def action_save_file(self) -> None:
        """Save to the current path or open Save As."""
        if self.current_file is not None:
            self._save_to(self.current_file)
        else:
            self.action_save_as()

    def action_save_as(self) -> None:
        """Show the save-as dialog."""
        start = self.current_file.parent if self.current_file else Path.cwd()
        name = self.current_file.name if self.current_file else "untitled.md"
        self.push_screen(
            FileDialogScreen(
                mode="save",
                title="Save Markdown file",
                start=start,
                start_name=name,
                patterns=("*.md", "*.markdown"),
            ),
            self._save_as_result,
        )

    def _save_as_result(self, path: Path | None) -> None:
        """Save to the path selected in the dialog."""
        if path is not None:
            self._save_to(path)

    def action_export(self) -> None:
        """Open the export-format menu."""
        items = [
            (label, self._export_callback(key), "")
            for label, key, _help_text in self.EXPORT_COMMANDS
        ]
        self.open_menu("Export", items)

    def _export_callback(self, key: str) -> Callable[[], None]:
        """Return a callback that exports in *key* format."""
        return lambda: self._export(key)

    def _export(self, key: str) -> None:
        """Ask for a destination and export the document."""
        ext = EXPORT_FORMATS.get(key, ".txt")
        base = self.current_file.stem if self.current_file else "document"
        start = self.current_file.parent if self.current_file else Path.cwd()
        self.push_screen(
            FileDialogScreen(
                mode="save",
                title="Export",
                start=start,
                start_name=base + ext,
                patterns=(f"*{ext}",),
            ),
            lambda path: self._write_export(path, key),
        )

    def _write_export(self, path: Path | None, key: str) -> None:
        """Write the document in the selected export format."""
        if path is None:
            return
        try:
            content = self.editor.text
            if key in {"html", "html_css"}:
                html = md_to_html(content, include_css=key == "html_css")
                path.write_text(html, encoding="utf-8")
            elif key == "text":
                path.write_text(md_to_plain(content), encoding="utf-8")
            elif key in {"pdf", "pdf_landscape"}:
                source_dir = (
                    str(self.current_file.parent) if self.current_file else None
                )
                layout = "landscape" if key == "pdf_landscape" else "portrait"
                md_to_pdf(
                    content,
                    str(path),
                    source_dir=source_dir,
                    page_layout=layout,
                )
            else:
                self.notify(f"Unknown export format: {key}", severity="error")
                return
        except Exception as exc:
            self.notify(str(exc), title="Export", severity="error")
            return
        self.notify(f"Exported {path}")

    def action_undo(self) -> None:
        """Undo the last edit."""
        self.editor.undo()

    def action_redo(self) -> None:
        """Redo the last undone edit."""
        self.editor.redo()

    def action_copy(self) -> None:
        """Copy the selection to the terminal clipboard (OSC 52)."""
        text = self.editor.selected_text
        if text:
            self.copy_to_clipboard(text)
            self.notify("Copied to clipboard")
        else:
            self.notify("Select text first", severity="warning")

    def action_cut(self) -> None:
        """Cut the selection."""
        text = self.editor.selected_text
        if not text:
            self.notify("Select text first", severity="warning")
            return
        self.copy_to_clipboard(text)
        self.editor.replace_selection("")
        self.editor.focus()

    def action_paste(self) -> None:
        """Paste the application clipboard at the cursor."""
        text = self.clipboard
        if not text:
            self.notify(
                "Clipboard is empty; use the terminal paste shortcut",
                severity="warning",
            )
            return
        self.editor.replace_selection(text)
        self.editor.focus()

    def action_select_all(self) -> None:
        """Select the whole document."""
        self.editor.select_all()
        self.editor.focus()

    def action_remove_selection(self) -> None:
        """Collapse the selection without deleting text."""
        self.editor.move_cursor(self.editor.selection.end)
        self.editor.focus()

    def action_find(self) -> None:
        """Open the Find dialog."""
        self.push_screen(FindScreen())

    def action_replace(self) -> None:
        """Open the Find and Replace dialog."""
        self.push_screen(ReplaceScreen())

    def _compile_pattern(self, term: str, use_regex: bool) -> re.Pattern | None:
        """Compile a search pattern, returning None for an empty term."""
        if not term:
            return None
        try:
            return re.compile(term if use_regex else re.escape(term))
        except re.error as exc:
            self.notify(f"Invalid regular expression: {exc}", severity="error")
            return None

    def find_next(self, term: str, use_regex: bool = False) -> bool:
        """Select the next match after the cursor, wrapping at the end."""
        pattern = self._compile_pattern(term, use_regex)
        if pattern is None:
            return False
        editor = self.editor
        text = editor.text
        start = editor.document.get_index_from_location(editor.selection.end)
        match = pattern.search(text, start) or pattern.search(text)
        if match is None:
            return False
        first = editor.document.get_location_from_index(match.start())
        last = editor.document.get_location_from_index(match.end())
        editor.selection = Selection(first, last)
        editor.scroll_cursor_visible()
        return True

    def replace_next(
        self, term: str, replacement: str, use_regex: bool = False
    ) -> bool:
        """Replace the next match, using group references for regular expressions."""
        if not self.find_next(term, use_regex):
            return False
        selected = self.editor.selected_text
        if use_regex:
            pattern = self._compile_pattern(term, True)
            if pattern is None:
                return False
            new_text = pattern.sub(replacement, selected, count=1)
        else:
            new_text = replacement
        self.editor.replace_selection(new_text)
        self.editor.focus()
        return True

    def replace_all(self, term: str, replacement: str, use_regex: bool = False) -> int:
        """Replace every occurrence and return the number of replacements."""
        if not term:
            return 0
        text = self.editor.text
        if use_regex:
            pattern = self._compile_pattern(term, True)
            if pattern is None:
                return 0
            new_text, count = pattern.subn(replacement, text)
        else:
            count = text.count(term)
            new_text = text.replace(term, replacement)
        if count:
            row, col = self.editor.cursor_location
            self.editor.replace_whole_text(new_text, cursor_row=row, cursor_col=col)
            self.editor.focus()
        return count

    def action_line_up(self) -> None:
        """Move the current line or selected block one line up."""
        self._move_lines(-1)

    def action_line_down(self) -> None:
        """Move the current line or selected block one line down."""
        self._move_lines(1)

    def _move_lines(self, delta: int) -> None:
        """Move the current/selected line block by *delta*."""
        editor = self.editor
        has_selection = editor.selection.start != editor.selection.end
        start, end = editor.selection_line_range()
        result = markdown_ops.move_lines(editor.text, start, end, delta)
        if result is None:
            return
        new_text, new_start, new_end = result
        editor.replace_whole_text(new_text, cursor_row=new_start)
        if has_selection:
            editor.select_lines(new_start, new_end)
        editor.focus()

    def action_go_to_line(self) -> None:
        """Ask for a line number and move the cursor to that line."""

        def on_result(result: dict[str, Any] | None) -> None:
            """Move the cursor to the chosen line."""
            if result is None:
                return
            editor = self.editor
            row = max(0, min(int(result["line"]) - 1, editor.line_count - 1))
            editor.move_cursor((row, 0), center=True)
            editor.focus()

        line_count = max(1, self.editor.line_count)
        current_line = min(self.editor.cursor_row + 1, line_count)
        self.push_screen(
            FormScreen(
                "Go to Line",
                [
                    FieldSpec(
                        "line",
                        f"Line number (1–{line_count}):",
                        kind="int",
                        default=current_line,
                        minimum=1,
                        maximum=line_count,
                    )
                ],
                submit_label="Go",
            ),
            on_result,
        )

    def action_delete_line(self) -> None:
        """Delete the current line."""
        editor = self.editor
        new_text, row, col = markdown_ops.delete_line(editor.text, editor.cursor_row)
        editor.replace_whole_text(new_text, cursor_row=row, cursor_col=col)
        editor.focus()

    def action_add_indent(self) -> None:
        """Indent the current line or selected lines by two spaces."""
        editor = self.editor
        start, end = editor.selection_line_range()
        has_selection = editor.selection.start != editor.selection.end
        new_text = markdown_ops.indent_lines(editor.text, start, end)
        editor.replace_whole_text(new_text, cursor_row=start, cursor_col=0)
        if has_selection:
            editor.select_lines(start, end)
        editor.focus()

    def action_remove_indent(self) -> None:
        """Remove up to two leading spaces from the current/selected lines."""
        editor = self.editor
        start, end = editor.selection_line_range()
        has_selection = editor.selection.start != editor.selection.end
        new_text = markdown_ops.outdent_lines(editor.text, start, end)
        editor.replace_whole_text(new_text, cursor_row=start, cursor_col=0)
        if has_selection:
            editor.select_lines(start, end)
        editor.focus()

    def _wrap(self, wrapper: str) -> None:
        """Wrap the selection or insert a pair at the cursor."""
        self.editor.wrap_selection(wrapper)
        self.editor.focus()

    def action_bold(self) -> None:
        """Wrap in bold markers."""
        self._wrap("**")

    def action_italic(self) -> None:
        """Wrap in italic markers."""
        self._wrap("*")

    def action_underline(self) -> None:
        """Wrap in underline markers."""
        self._wrap("^^")

    def action_strikethrough(self) -> None:
        """Wrap in strikethrough markers."""
        self._wrap("~~")

    def action_superscript(self) -> None:
        """Wrap in superscript markers."""
        self._wrap("^")

    def action_subscript(self) -> None:
        """Wrap in subscript markers."""
        self._wrap("~")

    def action_inline_code(self) -> None:
        """Wrap in inline-code backticks."""
        self._wrap("`")

    def action_mark_text(self) -> None:
        """Wrap in highlight markers."""
        self._wrap("==")

    def _insert_text(self, text: str) -> None:
        """Insert text at the cursor."""
        self.editor.replace_selection(text)
        self.editor.focus()

    def _insert_block(self, block: str) -> None:
        """Insert a block at the cursor with the usual blank-line separation."""
        editor = self.editor
        row, col = editor.cursor_location
        new_text, new_row, new_col = markdown_ops.insert_block(
            editor.text, row, col, block
        )
        editor.replace_whole_text(new_text, cursor_row=new_row, cursor_col=new_col)
        editor.focus()

    def _ensure_blank_line_before(self) -> int:
        """Insert a blank line above the current line when needed."""
        editor = self.editor
        row = editor.cursor_row
        if row > 0 and editor.line_text(row - 1).strip():
            editor.insert("\n", (row, 0), maintain_selection_offset=False)
            editor.set_cursor(row + 1, 0)
            return row + 1
        return row

    def _replace_current_line(self, text: str) -> None:
        """Replace the current line after ensuring block separation."""
        row = self._ensure_blank_line_before()
        self.editor.replace_line(row, text)
        self.editor.focus()

    def _set_heading(self, level: int) -> None:
        """Convert the current line to a heading."""
        line = self.editor.current_line
        self._replace_current_line(markdown_ops.set_heading(line, level))

    def action_heading_1(self) -> None:
        """Apply Heading 1."""
        self._set_heading(1)

    def action_heading_2(self) -> None:
        """Apply Heading 2."""
        self._set_heading(2)

    def action_heading_3(self) -> None:
        """Apply Heading 3."""
        self._set_heading(3)

    def action_heading_4(self) -> None:
        """Apply Heading 4."""
        self._set_heading(4)

    def action_heading_5(self) -> None:
        """Apply Heading 5."""
        self._set_heading(5)

    def action_heading_6(self) -> None:
        """Apply Heading 6."""
        self._set_heading(6)

    def action_paragraph(self) -> None:
        """Convert the current line to a normal paragraph."""
        self._replace_current_line(markdown_ops.set_paragraph(self.editor.current_line))

    def _set_list_item(self, marker: str) -> None:
        """Convert the current line to a list item."""
        line = self.editor.current_line
        self._replace_current_line(markdown_ops.set_list_item(line, marker))

    def action_ordered_list(self) -> None:
        """Convert the current line to an ordered-list item."""

        def on_result(result: dict[str, Any] | None) -> None:
            """Insert the chosen ordered-list number."""
            if result is None:
                return
            self._set_list_item(f"{result['number']}.")

        self.push_screen(
            FormScreen(
                "Ordered List",
                [
                    FieldSpec(
                        "number",
                        "Item number:",
                        kind="int",
                        default=1,
                        minimum=1,
                        maximum=999,
                    )
                ],
                submit_label="Insert",
            ),
            on_result,
        )

    def action_unordered_list(self) -> None:
        """Convert the current line to an unordered-list item."""
        self._set_list_item("-")

    def action_todo_list(self) -> None:
        """Add or update a todo marker on the current line."""

        def on_result(result: dict[str, Any] | None) -> None:
            """Apply the chosen todo marker."""
            if result is None:
                return
            line = self.editor.current_line
            self.editor.replace_line(
                self.editor.cursor_row,
                markdown_ops.set_todo_marker(line, bool(result["checked"])),
            )
            self.editor.focus()

        self.push_screen(
            FormScreen(
                "Todo List",
                [
                    FieldSpec(
                        "checked",
                        "Checked (completed)",
                        kind="bool",
                        default=False,
                    )
                ],
                submit_label="Apply",
                intro="Add or update the [ ] / [x] marker on the current line.",
            ),
            on_result,
        )

    def action_definition_list(self) -> None:
        """Insert a definition-list block."""

        def on_result(result: dict[str, Any] | None) -> None:
            """Insert a definition list with the chosen term and item count."""
            if result is None or not result["term"]:
                return
            self._insert_block(
                markdown_ops.make_definition_list(result["term"], result["count"])
            )

        self.push_screen(
            FormScreen(
                "Definition List",
                [
                    FieldSpec("term", "Term:"),
                    FieldSpec(
                        "count",
                        "Definitions:",
                        kind="int",
                        default=1,
                        minimum=1,
                        maximum=9,
                    ),
                ],
                submit_label="Insert",
            ),
            on_result,
        )

    def action_code_block(self) -> None:
        """Wrap the selection or current line in a fenced code block."""

        def on_result(result: dict[str, Any] | None) -> None:
            """Insert or wrap text in a fenced code block."""
            if result is None:
                return
            language = result["language"]
            selected = self.editor.selected_text
            if selected:
                self.editor.replace_selection(
                    markdown_ops.code_block(selected, language)
                )
                self.editor.focus()
                return
            row = self._ensure_blank_line_before()
            line = self.editor.line_text(row)
            self.editor.replace_line(row, markdown_ops.code_block(line, language))
            self.editor.focus()

        self.push_screen(
            FormScreen(
                "Code Block",
                [
                    FieldSpec(
                        "language",
                        "Programming language (optional):",
                        placeholder="python, bash, …",
                    )
                ],
                submit_label="Insert",
            ),
            on_result,
        )

    def action_blockquote(self) -> None:
        """Convert the current line to a blockquote."""
        self._set_list_item(">")

    def action_table(self) -> None:
        """Insert a Markdown table."""

        def on_result(result: dict[str, Any] | None) -> None:
            """Insert a table with the chosen dimensions."""
            if result is None:
                return
            self._insert_block(
                markdown_ops.make_table(
                    result["columns"], result["rows"], result["footer"]
                )
            )

        self.push_screen(
            FormScreen(
                "Insert Table",
                [
                    FieldSpec(
                        "columns",
                        "Columns:",
                        kind="int",
                        default=3,
                        minimum=1,
                        maximum=20,
                    ),
                    FieldSpec(
                        "rows",
                        "Rows:",
                        kind="int",
                        default=3,
                        minimum=1,
                        maximum=50,
                    ),
                    FieldSpec(
                        "footer",
                        "Add footer",
                        kind="bool",
                        default=True,
                    ),
                ],
                submit_label="Insert",
            ),
            on_result,
        )

    def action_add_table_row(self) -> None:
        """Insert a table row below the current line."""

        def on_result(result: dict[str, Any] | None) -> None:
            """Append a row with the entered cell values."""
            if result is None:
                return
            row = self.editor.cursor_row
            col = len(self.editor.line_text(row))
            self.editor.insert(
                "\n" + markdown_ops.make_table_row(result["cells"]),
                (row, col),
                maintain_selection_offset=False,
            )
            self.editor.set_cursor(row + 1, 0)
            self.editor.focus()

        self.push_screen(
            FormScreen(
                "Add Table Row",
                [
                    FieldSpec(
                        "cells",
                        "Number of cells:",
                        kind="int",
                        default=3,
                        minimum=1,
                        maximum=9,
                    )
                ],
                submit_label="Insert",
            ),
            on_result,
        )

    def action_table_alignment(self) -> None:
        """Set the alignment marker under the cursor."""
        options = (
            ("none (---)", "---"),
            ("left (:---)", ":---"),
            ("center (:---:)", ":---:"),
            ("right (---:)", "---:"),
        )

        def on_result(result: dict[str, Any] | None) -> None:
            """Apply the chosen column alignment."""
            if result is None:
                return
            marker = result["alignment"]
            editor = self.editor
            row, col = editor.cursor_location
            changed = markdown_ops.apply_table_alignment(editor.text, row, col, marker)
            if changed is None:
                editor.replace_selection(marker)
            else:
                new_text, new_col = changed
                editor.replace_whole_text(new_text, cursor_row=row, cursor_col=new_col)
            editor.focus()

        self.push_screen(
            FormScreen(
                "Table Alignment",
                [
                    FieldSpec(
                        "alignment",
                        "Select alignment:",
                        kind="select",
                        options=options,
                        default="---",
                    )
                ],
                submit_label="Apply",
            ),
            on_result,
        )

    def action_balance_table(self) -> None:
        """Balance the table at the cursor so all columns have equal width."""
        editor = self.editor
        result = markdown_ops.balance_table(editor.text, editor.cursor_row)
        if result is None:
            self.notify("The cursor is not in a table", severity="warning")
            return
        new_text, top, bottom = result
        editor.replace_whole_text(new_text, cursor_row=top, cursor_col=0)
        editor.select_lines(top, bottom)
        editor.focus()
        self.notify("Table balanced")

    def action_image(self) -> None:
        """Insert an image link after choosing a file and alt/title text."""

        def on_file(path: Path | None) -> None:
            """Ask for alt and title text for the selected image."""
            if path is None:
                return

            def on_result(result: dict[str, Any] | None) -> None:
                """Insert an image link with the entered alt and title text."""
                if result is None:
                    return
                alt = result["alt"]
                title = result["title"]
                if title:
                    markdown = f'![{alt}]({path} "{title}")'
                else:
                    markdown = f"![{alt}]({path})"
                self._insert_block(markdown)

            self.push_screen(
                FormScreen(
                    "Image",
                    [
                        FieldSpec("alt", "Alt text:"),
                        FieldSpec(
                            "title",
                            "Optional title:",
                            placeholder="leave empty for none",
                        ),
                    ],
                    submit_label="Insert",
                ),
                on_result,
            )

        self.push_screen(
            FileDialogScreen(
                mode="open",
                title="Choose an image",
                start=self.current_file.parent if self.current_file else Path.cwd(),
                patterns=("*.png", "*.jpg", "*.jpeg", "*.gif", "*.svg", "*.webp"),
            ),
            on_file,
        )

    def action_horizontal_rule(self) -> None:
        """Insert a horizontal rule."""
        self._insert_block("***")

    def action_line_break(self) -> None:
        """Insert a Markdown hard line break."""
        editor = self.editor
        row, col = editor.cursor_location
        new_text, new_row, new_col = markdown_ops.hard_line_break(editor.text, row, col)
        editor.replace_whole_text(new_text, cursor_row=new_row, cursor_col=new_col)
        editor.focus()

    def action_comment(self) -> None:
        """Comment the selection or insert a prompted comment block."""
        selected = self.editor.selected_text
        if selected:
            self.editor.replace_selection(markdown_ops.comment_block(selected))
            self.editor.focus()
            return

        def on_result(result: dict[str, Any] | None) -> None:
            """Insert a comment with the entered text."""
            if result is None or not result["text"]:
                return
            self._insert_block(markdown_ops.comment_inline(result["text"]))

        self.push_screen(
            FormScreen(
                "Comment",
                [FieldSpec("text", "Comment text:")],
                submit_label="Insert",
            ),
            on_result,
        )

    def action_yaml_front_matter(self) -> None:
        """Insert a YAML Front Matter block at the top of the document."""
        if self.editor.text.lstrip().startswith("---"):
            self.notify(
                "The document already has a YAML Front Matter block",
                title="YAML Front Matter",
                severity="warning",
            )
            return

        language_options = tuple((tag, tag) for tag in LANGUAGE_TAGS)

        def on_result(result: dict[str, Any] | None) -> None:
            """Insert the entered YAML front matter at the top."""
            if result is None:
                return
            block = markdown_ops.make_yaml_front_matter(result)
            self.editor.insert(block + "\n\n", (0, 0))
            self.editor.set_cursor(0, 0)
            self.editor.focus()

        self.push_screen(
            FormScreen(
                "YAML Front Matter",
                [
                    FieldSpec(
                        "lang",
                        "Language:",
                        kind="select_text",
                        options=language_options,
                        default="en",
                    ),
                    FieldSpec("title", "Title:"),
                    FieldSpec("author", "Author:"),
                    FieldSpec("description", "Description:"),
                    FieldSpec("keywords", "Keywords:"),
                ],
                submit_label="Insert",
            ),
            on_result,
        )

    def action_clear_formatting(self) -> None:
        """Strip Markdown syntax from the whole document."""
        row, col = self.editor.cursor_location
        text = md_to_plain(self.editor.text)
        self.editor.replace_whole_text(text, cursor_row=row, cursor_col=col)
        self.editor.focus()
        self.notify("Markdown formatting cleared")

    def action_special_mark(self) -> None:
        """Insert a backslash escape character."""
        self._insert_text("\\")

    def action_header_id(self) -> None:
        """Append a ``{#id}`` anchor to the current line."""

        def on_result(result: dict[str, Any] | None) -> None:
            """Append the entered header ID to the current line."""
            if result is None:
                return
            hidden = result["header_id"].strip().lstrip("#")
            if not hidden:
                return
            line = self.editor.current_line
            if line.strip():
                new_line = f"{line.rstrip()} {{#{hidden}}}"
            else:
                new_line = f"# {{#{hidden}}}"
            self.editor.replace_line(self.editor.cursor_row, new_line)
            self.editor.focus()

        self.push_screen(
            FormScreen(
                "Header ID",
                [FieldSpec("header_id", "Header ID (without #):")],
                submit_label="Insert",
            ),
            on_result,
        )

    def action_header_link(self) -> None:
        """Insert a cross-reference link to a heading."""

        def on_result(result: dict[str, Any] | None) -> None:
            """Insert a link to the entered header ID."""
            if result is None:
                return
            header_id = result["header_id"].strip()
            text = result["text"].strip() or header_id
            if header_id:
                self._insert_text(f"[{text}](#{header_id})")

        self.push_screen(
            FormScreen(
                "Insert Header Link",
                [
                    FieldSpec("header_id", "Header ID:"),
                    FieldSpec("text", "Link text:"),
                ],
                submit_label="Insert",
            ),
            on_result,
        )

    def action_toc(self) -> None:
        """Add, regenerate, remove or add IDs for a table of contents."""
        operations = (
            ("Add TOC", "add"),
            ("Regenerate existing TOC", "regenerate"),
            ("Remove existing TOC", "remove"),
            ("Add Header IDs only", "ids"),
        )

        def on_result(result: dict[str, Any] | None) -> None:
            """Apply the chosen table-of-contents operation."""
            if result is None:
                return
            text = self.editor.text
            heading = result["heading"] or "Table of Contents"
            operation = result["operation"]
            message = "TOC created"
            if operation == "add":
                text = add_toc(text, heading)
            elif operation == "regenerate":
                text = regenerate_toc(text, heading)
                message = "TOC regenerated"
            elif operation == "remove":
                text = remove_toc(text)
                message = "TOC removed"
            else:
                text = add_heading_ids(text)
                message = "Header IDs added"
            row, col = self.editor.cursor_location
            self.editor.replace_whole_text(text, cursor_row=row, cursor_col=col)
            self.editor.focus()
            self.notify(message)

        self.push_screen(
            FormScreen(
                "Table of Contents",
                [
                    FieldSpec(
                        "operation",
                        "Select an operation:",
                        kind="select",
                        options=operations,
                        default="add",
                    ),
                    FieldSpec(
                        "heading",
                        "TOC heading:",
                        default="Table of Contents",
                    ),
                ],
                submit_label="Apply",
            ),
            on_result,
        )

    def action_hyperlink(self) -> None:
        """Insert a Markdown hyperlink."""
        selected = self.editor.selected_text

        def on_result(result: dict[str, Any] | None) -> None:
            """Insert a link with the entered URL and text."""
            if result is None or not result["url"]:
                return
            text = result["text"] or selected or result["url"]
            link = f"[{text}]({result['url']})"
            if selected:
                self.editor.replace_selection(link)
            else:
                self._insert_text(link)

        self.push_screen(
            FormScreen(
                "Hyperlink",
                [
                    FieldSpec("url", "URL:"),
                    FieldSpec("text", "Link text:", default=selected),
                ],
                submit_label="Insert",
            ),
            on_result,
        )

    def action_footnote(self) -> None:
        """Insert a footnote reference and an optional definition."""

        def on_result(result: dict[str, Any] | None) -> None:
            """Insert a footnote reference and optional definition."""
            if result is None or not result["ref"]:
                return
            ref = result["ref"]
            self.editor.replace_selection(f"[^{ref}]")
            definition = result["definition"]
            if definition:
                self.editor.insert(
                    f"\n\n[^{ref}]: {definition}",
                    self.editor.document.end,
                    maintain_selection_offset=False,
                )
            self.editor.focus()

        self.push_screen(
            FormScreen(
                "Insert Footnote",
                [
                    FieldSpec("ref", "Reference / name:"),
                    FieldSpec("definition", "Definition:"),
                ],
                submit_label="Insert",
            ),
            on_result,
        )

    def action_language_marker(self) -> None:
        """Prepend a language tag such as ``{:de}`` to the current line."""
        options = tuple((tag, tag) for tag in LANGUAGE_TAGS)

        def on_result(result: dict[str, Any] | None) -> None:
            """Prepend the entered language marker to the current line."""
            if result is None:
                return
            language = result["lang"].strip()
            if not language:
                return
            line = self.editor.current_line
            self.editor.replace_line(self.editor.cursor_row, f"{{:{language}}} {line}")
            self.editor.focus()

        self.push_screen(
            FormScreen(
                "Language Marker",
                [
                    FieldSpec(
                        "lang",
                        "Language tag:",
                        kind="select_text",
                        options=options,
                        default="en",
                        placeholder="or type a BCP 47 tag",
                    )
                ],
                submit_label="Insert",
            ),
            on_result,
        )

    def action_language_wrapping(self) -> None:
        """Wrap the selection with a language tag pair."""
        options = tuple((tag, tag) for tag in LANGUAGE_TAGS)

        def on_result(result: dict[str, Any] | None) -> None:
            """Wrap the selection in the entered language markers."""
            if result is None:
                return
            language = result["lang"].strip()
            if not language:
                return
            selected = self.editor.selected_text
            if selected:
                self.editor.replace_selection(f"{{:{language}}}{selected}{{:}}")
            else:
                self._insert_text(f"{{:{language}}}{{:}}")

        self.push_screen(
            FormScreen(
                "Language Wrapping",
                [
                    FieldSpec(
                        "lang",
                        "Language tag:",
                        kind="select_text",
                        options=options,
                        default="en",
                        placeholder="or type a BCP 47 tag",
                    )
                ],
                submit_label="Wrap",
            ),
            on_result,
        )

    def action_language_codes(self) -> None:
        """Show a menu of language codes."""
        items = [
            (
                f"{code} — {description}",
                lambda c=code: self._insert_text(c),
                "",
            )
            for code, description in LANGUAGE_CODES
        ]
        self.open_menu("Language Codes", items)

    def action_furigana(self) -> None:
        """Insert a ruby annotation (furigana)."""
        selected = self.editor.selected_text

        def on_result(result: dict[str, Any] | None) -> None:
            """Insert a furigana annotation with the entered reading."""
            if result is None:
                return
            kanji = selected or result["kanji"].strip()
            reading = result["reading"].strip()
            if not kanji or not reading:
                return
            if selected:
                self.editor.replace_selection(f"{{{kanji}|{reading}}}")
            else:
                self._insert_text(f"{{{kanji}|{reading}}}")

        self.push_screen(
            FormScreen(
                "Furigana (Ruby Annotation)",
                [
                    FieldSpec("kanji", "Kanji / text:", default=selected),
                    FieldSpec("reading", "Reading (ruby):"),
                ],
                submit_label="Insert",
            ),
            on_result,
        )

    def action_date_time(self) -> None:
        """Insert a formatted date and/or time."""
        options = (
            ("Date and time", "date_time"),
            ("Date only", "date"),
            ("Time only", "time"),
        )

        def on_result(result: dict[str, Any] | None) -> None:
            """Insert the selected date or time value."""
            if result is None:
                return
            now = datetime.now()
            choice = result["choice"]
            if choice == "date_time":
                value = now.strftime("%Y-%m-%d %H:%M:%S")
            elif choice == "date":
                value = now.strftime("%Y-%m-%d")
            else:
                value = now.strftime("%H:%M:%S")
            self._insert_text(value)

        self.push_screen(
            FormScreen(
                "Insert Date and Time",
                [
                    FieldSpec(
                        "choice",
                        "Insert:",
                        kind="select",
                        options=options,
                        default="date_time",
                    )
                ],
                submit_label="Insert",
            ),
            on_result,
        )

    def action_emoji(self) -> None:
        """Show a menu of emoji shortcodes."""
        items = [
            (f":{emoji}:", lambda e=emoji: self._insert_text(f":{e}:"), "")
            for emoji in EMOJIS
        ]
        self.open_menu("Emoji Shortcodes", items)

    def action_special_signs(self) -> None:
        """Show a menu of special signs."""
        items = [
            (
                f"{sign}  {name}",
                lambda s=sign: self._insert_text(s),
                "",
            )
            for name, sign in SPECIAL_SIGNS
        ]
        self.open_menu("Special Signs", items)

    def action_help_shortcuts(self) -> None:
        """Show the local keyboard-shortcuts module."""
        self.push_screen(InfoScreen("Keyboard Shortcuts", shortcuts_markdown()))

    def action_about(self) -> None:
        """Show the About dialog."""
        self.push_screen(InfoScreen("About", about_markdown()))

    def menu_items(self, menu: str) -> list[Command]:
        """Return ``(label, callback, shortcut)`` tuples for *menu*."""
        return [
            (label, getattr(self, action), shortcut)
            for name, label, action, shortcut in self.COMMAND_SPECS
            if name == menu
        ]

    def open_menu(self, title: str, items: list[Command]) -> None:
        """Show a menu and run the chosen command in the application context."""
        self.push_screen(MenuScreen(title, items), self._run_menu_command)

    def _run_menu_command(self, callback: Callable[[], Any] | None) -> None:
        """Run a command returned by :meth:`open_menu`."""
        if callback is not None:
            self.call_after_refresh(callback)

    def command_items(self) -> list[Command]:
        """Return all commands for the command palette."""
        items: list[Command] = []
        for menu, label, action, shortcut in self.COMMAND_SPECS:
            help_text = f"{menu}"
            if shortcut:
                help_text += f" · {shortcut}"
            items.append((label, getattr(self, action), help_text))
        for label, key, help_text in self.EXPORT_COMMANDS:
            items.append((label, self._export_callback(key), help_text))
        return items

    def on_menu_bar_menu_clicked(self, event: MenuBar.MenuClicked) -> None:
        """Open the menu that was clicked."""
        self.open_menu(event.menu, self.menu_items(event.menu))

    def action_quit(self) -> None:
        """Quit after confirming that unsaved changes may be lost."""
        self._confirm_discard(self._finish_quit)

    def _finish_quit(self) -> None:
        """Clean up temporary files and exit."""
        self._cleanup_temp_files()
        self.exit()
