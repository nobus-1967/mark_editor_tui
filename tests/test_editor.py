#!/usr/bin/env python3
"""Tests for Mark Editor TUI 0.2.0."""

from __future__ import annotations

import contextlib
import io
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from textual._xterm_parser import XTermParser

from mark_editor_tui import markdown_ops as ops
from mark_editor_tui.compat import restore_alt_key_shortcuts
from mark_editor_tui.constants import (
    APP_NAME,
    CONFIG_DIR,
    DEFAULT_THEME,
    RELEASE,
    THEME_FILE,
    THEMES,
    VERSION,
)
from mark_editor_tui.help_text import shortcuts_markdown
from mark_editor_tui.helpers import (
    add_heading_ids,
    add_toc,
    cleanup_temp_html,
    cleanup_temp_md,
    ensure_cache_dir,
    get_converter,
    load_theme,
    md_to_html,
    md_to_plain,
    regenerate_toc,
    remove_toc,
    save_theme,
)
from mark_editor_tui.main import build_parser, main
from mark_editor_tui.themes import APP_THEMES, EDITOR_THEMES


class _IsolatedCacheMixin:
    """Point config and cache paths at a temporary directory."""

    def setUp(self) -> None:
        """Redirect config and cache paths to a fresh temporary directory."""
        import mark_editor_tui.helpers as mh

        self._orig = (mh.CONFIG_DIR, mh.THEME_FILE, mh.CACHE_DIR)
        self._tmp = Path(tempfile.mkdtemp(prefix="mark_editor_tui-test-"))
        mh.CONFIG_DIR = self._tmp / ".config"
        mh.THEME_FILE = mh.CONFIG_DIR / "theme.json"
        mh.CACHE_DIR = self._tmp / ".cache"

    def tearDown(self) -> None:
        """Restore the original config and cache paths."""
        import mark_editor_tui.helpers as mh

        mh.CONFIG_DIR, mh.THEME_FILE, mh.CACHE_DIR = self._orig


class TestAppMetadata(unittest.TestCase):
    """Verify the version and theme constants."""

    def test_app_name(self) -> None:
        """The application name is present."""
        self.assertEqual(APP_NAME, "Mark Editor TUI")

    def test_version(self) -> None:
        """The application version is 0.2.0."""
        self.assertEqual(VERSION, "0.2.0")

    def test_release(self) -> None:
        """The release identifier is present."""
        self.assertTrue(RELEASE)

    def test_themes(self) -> None:
        """The four color modes map to application and editor themes."""
        self.assertEqual(set(THEMES), {"default", "green", "magenta", "blue"})
        self.assertEqual(set(APP_THEMES), set(THEMES))
        self.assertEqual(set(EDITOR_THEMES), set(THEMES))
        self.assertEqual(len({theme.name for theme in APP_THEMES.values()}), 4)
        self.assertEqual(len({theme.name for theme in EDITOR_THEMES.values()}), 4)
        expected_alerts = {
            "default": "#ff00ff",
            "green": "#ffffff",
            "magenta": "#aa0000",
            "blue": "#ff00ff",
        }
        for name, theme in APP_THEMES.items():
            self.assertEqual(theme.name, f"mark-{name}")
            self.assertTrue(theme.dark)
            self.assertEqual(theme.warning, expected_alerts[name])
            self.assertEqual(theme.error, expected_alerts[name])
        for name, editor_theme in EDITOR_THEMES.items():
            self.assertEqual(editor_theme.name, f"mark_editor_tui-{name}")
            self.assertEqual(editor_theme.syntax_styles, {})

    def test_palette_roles(self) -> None:
        """Default is monochrome; green, magenta and blue replace white with hues."""
        default = APP_THEMES["default"]
        self.assertEqual(default.background, "#000000")
        self.assertEqual(default.foreground, "#ffffff")
        self.assertEqual(default.variables["menu-active-background"], "#ffffff")
        self.assertEqual(default.variables["menu-active-foreground"], "#000000")

        green = APP_THEMES["green"]
        self.assertEqual(green.background, "#000000")
        self.assertEqual(green.foreground, "#00ff00")
        self.assertEqual(green.secondary, "#00aa00")
        self.assertEqual(green.variables["menu-foreground"], "#00ff00")
        self.assertEqual(green.variables["menu-active-background"], "#00ff00")
        self.assertEqual(green.variables["menu-active-foreground"], "#000000")

        magenta = APP_THEMES["magenta"]
        self.assertEqual(magenta.background, "#000000")
        self.assertEqual(magenta.foreground, "#aa00aa")
        self.assertEqual(magenta.secondary, "#770077")
        self.assertEqual(magenta.variables["menu-foreground"], "#aa00aa")
        self.assertEqual(magenta.variables["menu-active-background"], "#aa00aa")
        self.assertEqual(magenta.variables["menu-active-foreground"], "#000000")

        blue = APP_THEMES["blue"]
        self.assertEqual(blue.background, "#000055")
        self.assertEqual(blue.foreground, "#e8f1ff")
        self.assertEqual(blue.secondary, "#8aa9d6")
        self.assertEqual(blue.success, "#00ff00")
        self.assertEqual(blue.variables["menu-background"], "#000055")
        self.assertEqual(blue.variables["menu-foreground"], "#e8f1ff")
        self.assertEqual(blue.variables["menu-active-foreground"], "#000033")
        self.assertEqual(blue.variables["editor-background"], "#000055")
        self.assertEqual(blue.variables["editor-foreground"], "#e8f1ff")
        self.assertEqual(blue.variables["status-background"], "#00106b")
        self.assertEqual(blue.variables["status-foreground"], "#e8f1ff")

    def test_editor_palettes(self) -> None:
        """Editor base, selection and gutter colors follow each theme."""
        self.assertEqual(
            EDITOR_THEMES["default"].base_style.color.get_truecolor().hex,
            "#ffffff",
        )
        self.assertEqual(
            EDITOR_THEMES["default"].base_style.bgcolor.get_truecolor().hex,
            "#000000",
        )
        self.assertEqual(
            EDITOR_THEMES["green"].base_style.color.get_truecolor().hex,
            "#00ff00",
        )
        self.assertEqual(
            EDITOR_THEMES["green"].selection_style.bgcolor.get_truecolor().hex,
            "#00ff00",
        )
        self.assertEqual(
            EDITOR_THEMES["magenta"].base_style.color.get_truecolor().hex,
            "#aa00aa",
        )
        self.assertEqual(
            EDITOR_THEMES["magenta"].selection_style.bgcolor.get_truecolor().hex,
            "#aa00aa",
        )
        self.assertEqual(
            EDITOR_THEMES["blue"].base_style.bgcolor.get_truecolor().hex,
            "#000055",
        )
        self.assertEqual(
            EDITOR_THEMES["blue"].base_style.color.get_truecolor().hex,
            "#e8f1ff",
        )
        self.assertEqual(
            EDITOR_THEMES["blue"].gutter_style.color.get_truecolor().hex,
            "#8aa9d6",
        )


class TestCommandLine(unittest.TestCase):
    """Verify the command-line help and version options."""

    def _run(self, arguments: list[str]) -> tuple[int, str]:
        """Run *arguments* through ``main`` and capture standard output."""
        capture = io.StringIO()
        with (
            self.assertRaises(SystemExit) as raised,
            contextlib.redirect_stdout(capture),
        ):
            main(arguments)
        return raised.exception.code, capture.getvalue()

    def test_short_version(self) -> None:
        """-v prints the application name, version and release."""
        code, output = self._run(["-v"])
        self.assertEqual(code, 0)
        self.assertIn(f"{APP_NAME} {VERSION} ({RELEASE})", output)

    def test_long_version(self) -> None:
        """--version behaves exactly like -v."""
        short_code, short_output = self._run(["-v"])
        long_code, long_output = self._run(["--version"])
        self.assertEqual(short_code, long_code)
        self.assertEqual(short_output, long_output)

    def test_short_help(self) -> None:
        """-h prints a brief description, the options and the FILE argument."""
        capture = io.StringIO()
        with (
            self.assertRaises(SystemExit) as raised,
            contextlib.redirect_stdout(capture),
        ):
            build_parser(prog="mark_editor_tui").parse_args(["-h"])
        self.assertEqual(raised.exception.code, 0)
        output = capture.getvalue()
        self.assertIn("usage: mark_editor_tui", output)
        self.assertIn(APP_NAME, output)
        self.assertIn("terminal Markdown editor", output)
        self.assertIn("FILE", output)
        self.assertIn("-v, --version", output)
        self.assertIn("-h, --help", output)

    def test_help_via_main(self) -> None:
        """The entry point handles -h without starting the editor."""
        code, output = self._run(["-h"])
        self.assertEqual(code, 0)
        self.assertIn("usage:", output)
        self.assertIn("terminal Markdown editor", output)

    def test_program_name_in_usage(self) -> None:
        """The parser accepts an explicit program name for help output."""
        parser = build_parser(prog="mark-editor-bin")
        self.assertEqual(parser.prog, "mark-editor-bin")


class TestThemeStorage(_IsolatedCacheMixin, unittest.TestCase):
    """Verify reading and writing the color-theme preference."""

    def test_config_path(self) -> None:
        """The theme is stored in ~/.config/mark_editor/theme.json."""
        self.assertEqual(CONFIG_DIR, Path.home() / ".config" / "mark_editor")
        self.assertEqual(THEME_FILE, CONFIG_DIR / "theme.json")

    def test_default_theme(self) -> None:
        """A missing config file falls back to the default theme."""
        self.assertEqual(load_theme(), DEFAULT_THEME)

    def test_save_and_load_theme(self) -> None:
        """Every theme in the cycle is saved and loaded again."""
        for expected in THEMES:
            save_theme(expected)
            self.assertEqual(load_theme(), expected)

    def test_unknown_theme_falls_back(self) -> None:
        """An unknown mode in the config file resolves to the default."""
        (self._tmp / ".config").mkdir(parents=True, exist_ok=True)
        (self._tmp / ".config" / "theme.json").write_text(
            '{"mode": "purple"}', encoding="utf-8"
        )
        self.assertEqual(load_theme(), DEFAULT_THEME)

    def test_theme_file_has_no_font_size(self) -> None:
        """Font size belongs to the terminal and is never saved."""
        save_theme(DEFAULT_THEME)
        config_file = self._tmp / ".config" / "theme.json"
        self.assertNotIn("font_size", config_file.read_text(encoding="utf-8"))


class TestCacheDir(_IsolatedCacheMixin, unittest.TestCase):
    """Verify that the cache directory is created on demand."""

    def test_ensure_cache_dir(self) -> None:
        """ensure_cache_dir creates and returns the configured directory."""
        path = ensure_cache_dir()
        self.assertTrue(path.is_dir())
        self.assertEqual(path, self._tmp / ".cache")


class TestMarkdownOps(unittest.TestCase):
    """Verify pure text transformations used by editor actions."""

    def test_heading(self) -> None:
        """Headings get the requested number of markers."""
        self.assertEqual(ops.set_heading("text", 2), "## text")
        self.assertEqual(ops.set_heading("## old", 3), "### old")

    def test_paragraph(self) -> None:
        """Paragraph removes a leading heading marker."""
        self.assertEqual(ops.set_paragraph("## title"), "title")

    def test_list_items(self) -> None:
        """List markers replace existing list markers."""
        self.assertEqual(ops.set_list_item("item", "-"), "- item")
        self.assertEqual(ops.set_list_item("- item", "1."), "1. item")
        self.assertEqual(ops.set_list_item("> quote", ">"), "> quote")

    def test_todo(self) -> None:
        """Todo markers are added or updated on list items only."""
        cases = (
            ("- task", False, "- [ ] task"),
            ("- task", True, "- [x] task"),
            ("* task", False, "* [ ] task"),
            ("1. task", False, "1. [ ] task"),
            ("- [ ] task", True, "- [x] task"),
            ("1. [x] task", False, "1. [ ] task"),
            ("[x] task", False, "[ ] task"),
            ("task", False, "task"),
        )
        for text, checked, expected in cases:
            self.assertEqual(ops.set_todo_marker(text, checked), expected)

    def test_code_block(self) -> None:
        """Code blocks include an optional language tag."""
        self.assertEqual(ops.code_block("x = 1", "python"), "```python\nx = 1\n```")
        self.assertEqual(ops.code_block("text"), "```\ntext\n```")

    def test_table_row_detection(self) -> None:
        """Table rows and alignment rows are recognised."""
        self.assertTrue(ops.is_table_row("| a | b |"))
        self.assertFalse(ops.is_table_row("plain text"))
        self.assertTrue(ops.is_table_align_row("| :--- | ---: |"))
        self.assertFalse(ops.is_table_align_row("| a | b |"))

    def test_format_table_block(self) -> None:
        """Table formatter pads columns and aligns the right border."""
        lines = ["| a | bbb |", "| :--- | :---: |", "| x | y |"]
        formatted = ops.format_table_block(lines)
        self.assertEqual(
            formatted,
            ["| a    | bbb   |", "| :--- | :---: |", "| x    | y     |"],
        )
        self.assertEqual({len(line) for line in formatted}, {len(formatted[0])})

    def test_balance_table(self) -> None:
        """Balance Table pads every row to equal column widths."""
        table = (
            "| Name       | Age |\n"
            "| :---       | :---: |\n"
            "| Alice      | 30 |\n"
            "| Bob        | 25 |"
        )
        result = ops.balance_table(table, 2)
        assert result is not None
        new_text, top, bottom = result
        self.assertEqual(
            new_text,
            "| Name  | Age   |\n"
            "| :---  | :---: |\n"
            "| Alice | 30    |\n"
            "| Bob   | 25    |",
        )
        self.assertEqual((top, bottom), (0, 3))

    def test_balance_table_outside_table(self) -> None:
        """Balance Table refuses a line that is not a table row."""
        self.assertIsNone(ops.balance_table("plain text", 0))

    def test_table_alignment_change_cell(self) -> None:
        """The alignment marker under the cursor is replaced."""
        row = "| :--- | :---: | ---: |"
        result = ops.apply_table_alignment(row, 0, 17, ":---:")
        assert result is not None
        new_text, _col = result
        self.assertEqual(new_text, "| :--- | :---: | :---: |")

    def test_table_alignment_insert(self) -> None:
        """A marker outside an alignment cell is reported as unchanged."""
        self.assertIsNone(ops.apply_table_alignment("plain", 0, 0, ":---"))

    def test_make_table(self) -> None:
        """Generated tables contain header, alignment, cells and footer."""
        text = ops.make_table(3, 3, True)
        self.assertIn("| Header | Header | Header |", text)
        self.assertIn("| --- | --- | --- |", text)
        self.assertEqual(text.count("| Cell | Cell | Cell |"), 3)
        self.assertIn("| Footer | Footer | Footer |", text)

    def test_make_definition_list(self) -> None:
        """Definition lists contain one definition per requested item."""
        text = ops.make_definition_list("Term", 2)
        self.assertEqual(text, "\nTerm\n: Definition 1\n: Definition 2")

    def test_move_lines_single(self) -> None:
        """A single line moves up and down."""
        self.assertEqual(
            ops.move_lines("first\nsecond\nthird", 1, 1, -1),
            ("second\nfirst\nthird", 0, 0),
        )
        self.assertEqual(
            ops.move_lines("first\nsecond\nthird", 1, 1, 1),
            ("first\nthird\nsecond", 2, 2),
        )

    def test_move_lines_selection(self) -> None:
        """A multi-line block moves as a unit."""
        self.assertEqual(
            ops.move_lines("first\nsecond\nthird\nfourth", 1, 2, -1),
            ("second\nthird\nfirst\nfourth", 0, 1),
        )
        self.assertEqual(
            ops.move_lines("first\nsecond\nthird\nfourth", 1, 2, 1),
            ("first\nfourth\nsecond\nthird", 2, 3),
        )

    def test_move_lines_boundaries(self) -> None:
        """Moving past a document edge is a no-op."""
        self.assertIsNone(ops.move_lines("first\nsecond", 0, 0, -1))
        self.assertIsNone(ops.move_lines("first\nsecond", 1, 1, 1))

    def test_delete_line(self) -> None:
        """Deleting a line keeps a valid cursor location."""
        self.assertEqual(ops.delete_line("a\nb\nc", 1), ("a\nc", 1, 0))
        self.assertEqual(ops.delete_line("only", 0), ("", 0, 0))

    def test_indent_selection(self) -> None:
        """Indenting prefixes every selected line."""
        text = ops.indent_lines("first\nsecond\nthird", 0, 2)
        self.assertEqual(text, "  first\n  second\n  third")

    def test_outdent_selection(self) -> None:
        """Outdenting removes up to two leading spaces from each line."""
        text = ops.outdent_lines("  first\n    second\n third", 0, 2)
        self.assertEqual(text, "first\n  second\nthird")

    def test_insert_block(self) -> None:
        """Blocks are separated from preceding text by a blank line."""
        text, row, col = ops.insert_block("before\nafter", 1, 0, "| a | b |")
        self.assertEqual(text, "before\n\n| a | b |\nafter")
        self.assertEqual((row, col), (2, 9))

    def test_insert_block_with_leading_separator(self) -> None:
        """A block that starts with a newline adds only one blank line."""
        text, row, col = ops.insert_block(
            "before\nafter", 1, 0, ops.make_definition_list("Term", 1)
        )
        self.assertEqual(text, "before\n\nTerm\n: Definition 1\nafter")
        self.assertEqual((row, col), (3, 14))

    def test_hard_line_break(self) -> None:
        """A hard break adds two spaces and starts a new line."""
        self.assertEqual(
            ops.hard_line_break("line", 0, 2),
            ("li  \nne", 1, 0),
        )

    def test_comments(self) -> None:
        """Comments use the hidden reference-style form."""
        self.assertEqual(ops.comment_inline("note"), "[note]: #")
        self.assertEqual(
            ops.comment_block("one\ntwo\n"),
            "[one]: #\n[two]: #\n",
        )


class TestMarkdownConversion(unittest.TestCase):
    """Verify Markdown conversion helpers."""

    def test_converter_importable(self) -> None:
        """get_converter emits HTML5 heading markup."""
        self.assertIn("<h1>", get_converter().convert("# Title"))

    def test_md_to_plain(self) -> None:
        """md_to_plain strips markup and keeps the text."""
        text = md_to_plain("# Title\n\nSome **bold** and [link](https://x.com).")
        self.assertIn("Title", text)
        self.assertIn("Some bold and link.", text)

    def test_md_to_plain_table(self) -> None:
        """md_to_plain keeps footer separators and normalizes alignment rows."""
        source = (
            "| Name | Qty | Price |\n"
            "| :--- | :---: | ---: |\n"
            "| A | 1 | 10.0 |\n"
            "| === | === | === |\n"
            "| Total | 1 | 10.0 |"
        )
        text = md_to_plain(source)
        self.assertIn("| === | === | === |", text)
        self.assertIn("| --- | --- | --- |", text)
        self.assertIn("| Total | 1 | 10.0 |", text)

    def test_md_to_plain_blockquote(self) -> None:
        """md_to_plain strips quote markers and keeps a blank line before them."""
        text = md_to_plain("Para\n> Quote one\n> Quote two\n\nAfter.")
        self.assertIn("Para\n\nQuote one\nQuote two", text)
        self.assertFalse(text.startswith("Quote"))

    def test_md_to_plain_lists(self) -> None:
        """md_to_plain keeps list markers and separates blocks."""
        text = md_to_plain("Para\n- a\n- b\n\n1. one\n2. two\n\nTerm\n: def")
        self.assertEqual(text, "Para\n\n- a\n- b\n\n1. one\n2. two\n\nTerm\n- def\n")

    def test_md_to_plain_code(self) -> None:
        """md_to_plain keeps a blank line after a fenced code block."""
        text = md_to_plain("```python\nx = 1\n```\nAfter.")
        self.assertEqual(text, "x  1\n\nAfter.\n")

    def test_md_to_plain_footnotes(self) -> None:
        """md_to_plain removes blank lines between footnote definitions."""
        text = md_to_plain("Text[^1][^2].\n\n[^1]: One.\n\n[^2]: Two.\n\nBody.\n")
        self.assertEqual(text, "Text[1][2].\n\n[1]: One.\n[2]: Two.\n\nBody.\n")

    def test_md_to_html(self) -> None:
        """md_to_html produces HTML5 heading markup."""
        self.assertIn("<h1>", md_to_html("# Hello"))

    def test_md_to_html_with_css(self) -> None:
        """HTML with CSS includes an embedded stylesheet."""
        self.assertIn("<style>", md_to_html("# Hello", include_css=True))

    def test_md_to_pdf_uses_fixed_fonts(self) -> None:
        """PDF export uses Noto Sans Mono/CJK plus Symbola for symbols."""
        from unittest import mock

        import mark_editor_tui.helpers as mh

        with mock.patch.object(mh, "md2pdf_convert") as convert:
            mh.md_to_pdf("# Title", "/tmp/out.pdf", source_dir="/tmp")

        convert.assert_called_once()
        kwargs = convert.call_args.kwargs
        self.assertEqual(kwargs["main_font"], "Noto Sans Mono")
        self.assertEqual(kwargs["head_font"], "Noto Sans Mono")
        self.assertEqual(kwargs["mono_font"], "Noto Sans Mono")
        self.assertEqual(kwargs["symbol_font"], "Symbola")
        self.assertEqual(
            kwargs["cjk_fonts"],
            {
                "ja": "Noto Sans Mono CJK JP",
                "cn": "Noto Sans Mono CJK SC",
                "tw": "Noto Sans Mono CJK TC",
                "hk": "Noto Sans Mono CJK HK",
                "kr": "Noto Sans Mono CJK KR",
            },
        )


class TestTempFileCleanup(unittest.TestCase):
    """Verify targeted deletion of temporary ~*.md and ~*.html files."""

    def _make_dir(self) -> Path:
        """Create a temp directory with mixed tilde and plain files."""
        directory = Path(tempfile.mkdtemp(prefix="mark_editor_tui-cleanup-"))
        (directory / "~doc.md").write_text("x", encoding="utf-8")
        (directory / "~doc.html").write_text("x", encoding="utf-8")
        (directory / "~notes").write_text("x", encoding="utf-8")
        (directory / "doc.md").write_text("x", encoding="utf-8")
        return directory

    def test_cleanup_temp_md_only(self) -> None:
        """cleanup_temp_md removes ~*.md but keeps other files."""
        directory = self._make_dir()
        cleanup_temp_md(directory)
        self.assertFalse((directory / "~doc.md").exists())
        self.assertTrue((directory / "~doc.html").exists())
        self.assertTrue((directory / "~notes").exists())
        self.assertTrue((directory / "doc.md").exists())

    def test_cleanup_temp_html_only(self) -> None:
        """cleanup_temp_html removes ~*.html but keeps other files."""
        directory = self._make_dir()
        cleanup_temp_html(directory)
        self.assertFalse((directory / "~doc.html").exists())
        self.assertTrue((directory / "~doc.md").exists())
        self.assertTrue((directory / "~notes").exists())


class TestTableOfContents(unittest.TestCase):
    """Verify TOC generation: IDs, links, placement, removal and regeneration."""

    DOC = "# My Title\n\n## First 2\n\nText.\n\n## Second 2\n\n### Deep 3\n\nMore.\n"

    def test_add_toc_headings_numbered_and_ids_added(self) -> None:
        """Level-2+ headings get per-level ordinal IDs; H1 keeps no ID."""
        out = add_toc(self.DOC)
        self.assertIn("## First 2 {#h2-1}", out)
        self.assertIn("## Second 2 {#h2-2}", out)
        self.assertIn("### Deep 3 {#h3-1}", out)
        self.assertNotIn("# My Title {#", out)

    def test_toc_placed_after_first_h1(self) -> None:
        """The TOC block sits right after the first Level 1 heading."""
        out = add_toc(self.DOC)
        self.assertLess(out.index("## Table of Contents"), out.index("## First 2"))
        self.assertTrue(out.startswith("# My Title\n\n[TOC: Begin]: #"))

    def test_toc_link_format(self) -> None:
        """Links list headings in order."""
        out = add_toc(self.DOC)
        self.assertIn("- [First 2](#h2-1)", out)
        self.assertIn("- [Second 2](#h2-2)", out)
        self.assertIn("- [Deep 3](#h3-1)", out)

    def test_toc_hr_separator(self) -> None:
        """The TOC block ends with an *** rule followed by the document."""
        self.assertIn("[TOC: End]: #\n\n***\n", add_toc(self.DOC))

    def test_toc_without_h1_goes_to_start(self) -> None:
        """Without an H1 the TOC block is inserted at the document start."""
        out = add_toc("## A\n\n## B\n")
        self.assertTrue(
            out.startswith("[TOC: Begin]: #\n\n## Table of Contents {#toc}")
        )
        self.assertIn("## A {#h2-1}", out)
        self.assertIn("## B {#h2-2}", out)

    def test_toc_after_yaml_front_matter(self) -> None:
        """With no H1 and YAML front matter, the TOC follows the closing ---."""
        out = add_toc("---\ntitle: X\n---\n\n## A\n")
        self.assertTrue(out.startswith("---\ntitle: X\n---\n\n[TOC: Begin]: #"))

    def test_existing_ids_reused(self) -> None:
        """Adding a TOC twice does not duplicate IDs."""
        out = add_toc(self.DOC)
        out2 = add_toc(out)
        self.assertEqual(out.count("## First 2 {#h2-1}"), 1)
        self.assertIn("- [First 2](#h2-1)", out2)

    def test_regenerate_toc(self) -> None:
        """Regenerating keeps the expected numbering."""
        out = regenerate_toc(add_toc(self.DOC))
        self.assertIn("### Deep 3 {#h3-1}", out)
        self.assertIn("- [Second 2](#h2-2)", out)

    def test_remove_toc_keeps_ids(self) -> None:
        """Removing the TOC block keeps heading IDs."""
        out = remove_toc(add_toc(self.DOC))
        self.assertNotIn("[TOC: Begin]", out)
        self.assertNotIn("## Table of Contents", out)
        self.assertIn("## First 2 {#h2-1}", out)

    def test_add_ids_only(self) -> None:
        """IDs-only mode numbers level-2+ headings and ignores the TOC block."""
        out = add_heading_ids(add_toc(self.DOC))
        self.assertIn("## Table of Contents {#toc}", out)
        self.assertNotIn("# My Title {#", out)
        self.assertIn("## First 2 {#h2-1}", out)

    def test_code_fenced_headings_ignored(self) -> None:
        """Headings inside fenced code blocks get no ID and no TOC entry."""
        out = add_toc("## Real\n\n```markdown\n## Fake\n```\n")
        self.assertIn("## Real {#h2-1}", out)
        self.assertNotIn("## Fake {#", out)
        self.assertIn("- [Real](#h2-1)", out)


class TestHelpText(unittest.TestCase):
    """Verify the local help module and its shortcut scheme."""

    def test_shortcuts_use_terminal_safe_keys(self) -> None:
        """The local shortcut module lists F1–F12 and the terminal-safe aliases."""
        text = shortcuts_markdown()
        self.assertIn("Mark Editor TUI", text)
        for shortcut in (
            "F1",
            "F2",
            "F3",
            "F4",
            "F5",
            "F6",
            "F7",
            "F8",
            "F9",
            "F10",
            "F11",
            "F12",
            "Alt+Shift+W",
            "Alt+Shift+F",
            "Alt+Shift+K",
            "Alt+Shift+T",
            "Alt+Shift+N",
            "Alt+I",
            "Alt+M",
            "Alt+Enter",
            "Alt+1",
            "Ctrl+_",
        ):
            self.assertIn(shortcut, text)
        for obsolete in (
            "Ctrl+Shift+Z",
            "Ctrl+?",
            "Ctrl+Alt+F",
            "Font Size",
            "Editor Font",
            "Zoom",
        ):
            self.assertNotIn(obsolete, text)

    def test_shortcuts_cover_every_menu_command(self) -> None:
        """Every menu command and every shortcut appears in the help text."""
        from mark_editor_tui.app import MarkEditorApp

        text = shortcuts_markdown()
        self.assertNotIn("Notes", text)
        self.assertIn("Ctrl+P", text)
        labels = [
            label
            for menu, label, _action, _shortcut in MarkEditorApp.COMMAND_SPECS
            if menu == "Edit"
        ]
        self.assertEqual(
            labels.index("Go to Line...") + 1,
            labels.index("Delete Line"),
            "Go to Line... must sit directly before Delete Line in Edit",
        )
        for menu, label, _action, shortcut in MarkEditorApp.COMMAND_SPECS:
            self.assertIn(label, text, f"{menu}: {label} is missing")
            for raw_part in shortcut.replace("/", ",").split(","):
                part = raw_part.strip()
                if part:
                    self.assertIn(part, text, f"{label}: {part} is missing")


class TestAltKeyCompat(unittest.TestCase):
    """Alt+digit and Alt+punctuation survive the terminal escape encoding."""

    def setUp(self) -> None:
        """Apply the compatibility fixes before parsing test sequences."""
        restore_alt_key_shortcuts()

    @staticmethod
    def _parse(sequence: str) -> list[str]:
        """Return the key names Textual reports for *sequence*."""
        parser = XTermParser()
        return [event.key for event in parser.feed(sequence)] + [
            event.key for event in parser.feed("")
        ]

    def test_alt_digits_are_not_typographic_characters(self) -> None:
        """Alt+0..9 is reported as alt+digit, not as a punctuation character."""
        for digit in "0123456789":
            with self.subTest(digit=digit):
                self.assertEqual(self._parse(f"\x1b{digit}"), [f"alt+{digit}"])

    def test_alt_punctuation_keeps_modifier(self) -> None:
        """Alt+- and Alt+= keep the Alt modifier in their key names."""
        self.assertEqual(self._parse("\x1b-"), ["alt+minus"])
        self.assertEqual(self._parse("\x1b="), ["alt+equals_sign"])

    def test_alt_enter_keeps_modifier(self) -> None:
        """Alt+Enter is reported as alt+enter, not as a plain Enter."""
        self.assertEqual(self._parse("\x1b\r"), ["alt+enter"])

    def test_alt_letters_are_unchanged(self) -> None:
        """Alt+letter and Alt+Shift+letter still produce their usual names."""
        self.assertEqual(self._parse("\x1ba"), ["alt+a"])
        self.assertEqual(self._parse("\x1bA"), ["alt+shift+a"])

    def test_plain_keys_are_unchanged(self) -> None:
        """Digit, hyphen and Enter typed without Alt keep their key names."""
        self.assertEqual(self._parse("1"), ["1"])
        self.assertEqual(self._parse("-"), ["minus"])
        self.assertEqual(self._parse("\r"), ["enter"])


class TestTextualApp(_IsolatedCacheMixin, unittest.IsolatedAsyncioTestCase):
    """Smoke tests for the Textual application and its actions."""

    async def _make_app(self):
        """Return a new application instance."""
        from mark_editor_tui.app import MarkEditorApp

        return MarkEditorApp()

    async def test_startup(self) -> None:
        """The application starts with an empty editor and status bar."""
        app = await self._make_app()
        async with app.run_test(size=(120, 40)) as pilot:
            await pilot.pause()
            self.assertEqual(app.editor.text, "")
            self.assertEqual(app.theme_mode, DEFAULT_THEME)
            self.assertEqual(app.theme, APP_THEMES[DEFAULT_THEME].name)
            self.assertEqual(app.editor.theme, EDITOR_THEMES[DEFAULT_THEME].name)
            self.assertIn(APP_NAME, app.title)
            self.assertEqual(app.query_one("#editor"), app.editor)
            self.assertEqual(app.editor.language, "markdown")

    async def test_function_key_bindings(self) -> None:
        """F1–F12 follow the console-editor layout and bindings are unique."""
        from mark_editor_tui.app import MarkEditorApp

        bindings = {
            key.strip(): binding.action
            for binding in MarkEditorApp.BINDINGS
            for key in binding.key.split(",")
        }
        expected = {
            "f1": "help_shortcuts",
            "f2": "save_file",
            "f3": "save_as",
            "f4": "find",
            "f5": "replace",
            "f6": "select_all",
            "f7": "cut",
            "f8": "copy",
            "f9": "paste",
            "f10": "quit",
            "f11": "undo",
            "f12": "redo",
        }
        for key, action in expected.items():
            self.assertEqual(bindings[key], action)

        keys = list(bindings)
        self.assertEqual(len(keys), len(set(keys)))

    async def test_function_key_bar(self) -> None:
        """F1–F12 appear below the status line in numeric order."""
        from mark_editor_tui.menubar import (
            FUNCTION_KEYS,
            FunctionKey,
            FunctionKeyBar,
            PaletteHint,
        )

        app = await self._make_app()
        async with app.run_test(size=(135, 40)) as pilot:
            await pilot.pause()
            keys = list(app.query(FunctionKey))
            self.assertEqual(
                [key.function_key for key in keys],
                [f"F{number}" for number in range(1, 13)],
            )
            self.assertEqual(
                [(key.function_key, key.function_action) for key in keys],
                [(key, action) for key, action, _label in FUNCTION_KEYS],
            )
            self.assertGreater(
                app.query_one(FunctionKeyBar).region.y,
                app.query_one("#status").region.y,
            )
            hint = app.query_one(PaletteHint)
            self.assertEqual(hint.render().plain, " Ctrl+P Command palette")
            function_key = app.query_one("#function-f1")
            for component in ("function-key--key", "function-key--label"):
                hint_style = hint.get_component_rich_style(component)
                key_style = function_key.get_component_rich_style(component)
                self.assertEqual(hint_style.color, key_style.color)
                self.assertEqual(hint_style.bgcolor, key_style.bgcolor)
            self.assertLessEqual(
                max([key.region.right for key in keys] + [hint.region.right]),
                135,
                "all F1–F12 keys and Ctrl+P Command palette fit 135 columns",
            )
            self.assertEqual(hint.region.right, 135)

            await pilot.click("#palette-hint")
            await pilot.pause()
            self.assertEqual(type(app.screen).__name__, "CommandPalette")
            await pilot.press("escape")
            await pilot.pause()

            app.editor.load_text("text")
            app.editor.select_all()
            await pilot.click("#function-f8")
            await pilot.pause()
            self.assertEqual(app.clipboard, "text")

    async def test_menu_shortcuts(self) -> None:
        """Every menu entry shows its keyboard shortcut in parentheses."""
        from textual.widgets import OptionList

        app = await self._make_app()
        async with app.run_test(size=(120, 40)) as pilot:
            await pilot.pause()
            for menu in ("File", "Edit", "Format", "Paragraph", "Help"):
                items = app.menu_items(menu)
                expected = [
                    f"{label} ({shortcut})" if shortcut else label
                    for label, _callback, shortcut in items
                ]
                app.open_menu(menu, items)
                await pilot.pause()
                option_list = app.screen.query_one("#menu-list", OptionList)
                labels = [
                    str(option_list.get_option_at_index(index).prompt)
                    for index in range(option_list.option_count)
                ]
                self.assertEqual(labels, expected)
                await pilot.press("escape")
                await pilot.pause()

            file_items = app.menu_items("File")
            self.assertEqual(
                [label for label, _callback, _shortcut in file_items][-3:],
                ["Export...", "Toggle Theme", "Quit"],
            )
            self.assertEqual(file_items[-2][2], "Alt+T")
            self.assertEqual(file_items[-1][2], "F10")
            self.assertEqual(app.menu_items("View"), [])
            self.assertEqual(
                [
                    f"{label} ({shortcut})" if shortcut else label
                    for label, _callback, shortcut in app.menu_items("Help")
                ],
                ["Keyboard Shortcuts (F1)", "About Editor"],
            )

    async def test_terminal_colors(self) -> None:
        """Each theme applies its editor, menu and highlight colors."""
        from textual.widgets import OptionList

        expected = {
            "default": (
                "#ffffff",
                "#000000",
                "#000000",
                "#ffffff",
                "#000000",
                "#ffffff",
            ),
            "green": (
                "#00ff00",
                "#000000",
                "#000000",
                "#00ff00",
                "#000000",
                "#00ff00",
            ),
            "magenta": (
                "#aa00aa",
                "#000000",
                "#000000",
                "#aa00aa",
                "#000000",
                "#aa00aa",
            ),
            "blue": (
                "#e8f1ff",
                "#000055",
                "#000055",
                "#e8f1ff",
                "#000033",
                "#d6e6ff",
            ),
        }
        app = await self._make_app()
        async with app.run_test(size=(120, 40)) as pilot:
            await pilot.pause()
            for mode, colors in expected.items():
                app._apply_theme(mode)
                await pilot.pause()
                editor_fg, editor_bg, menu_bg, menu_fg, active_fg, active_bg = colors
                self.assertEqual(app.editor.styles.color.hex.lower(), editor_fg)
                self.assertEqual(app.editor.styles.background.hex.lower(), editor_bg)

                menu_bar = app.query_one("MenuBar")
                self.assertEqual(menu_bar.styles.background.hex.lower(), menu_bg)
                menu_title = app.query_one("MenuTitle")
                self.assertEqual(menu_title.styles.color.hex.lower(), menu_fg)

                app.open_menu("File", app.menu_items("File"))
                await pilot.pause()
                option_list = app.screen.query_one("#menu-list", OptionList)
                highlighted = option_list.get_component_styles(
                    "option-list--option-highlighted"
                )
                self.assertEqual(highlighted.color.hex.lower(), active_fg)
                self.assertEqual(highlighted.background.hex.lower(), active_bg)
                await pilot.press("escape")
                await pilot.pause()

    async def test_ctrl_f_opens_find(self) -> None:
        """Ctrl+F still opens Find when it is not preceded by Escape."""
        app = await self._make_app()
        async with app.run_test(size=(120, 40)) as pilot:
            await pilot.pause()
            await pilot.press("ctrl+f")
            await pilot.pause()
            self.assertEqual(type(app.screen).__name__, "FindScreen")

    async def test_help_documents(self) -> None:
        """The help actions use the local shortcut and About modules."""
        app = await self._make_app()
        async with app.run_test(size=(120, 40)) as pilot:
            await pilot.pause()
            for action, title in (
                (app.action_help_shortcuts, "Keyboard Shortcuts"),
                (app.action_about, "About"),
            ):
                action()
                await pilot.pause()
                self.assertEqual(app.screen.dialog_title, title)
                if title == "Keyboard Shortcuts":
                    app.screen.action_page_down()
                    await pilot.pause()
                    body = app.screen.query_one("#info-body")
                    self.assertGreater(body.scroll_offset.y, 0)
                await pilot.press("escape")
                await pilot.pause()

    async def test_formatting_actions(self) -> None:
        """Formatting actions edit the buffer in place."""
        app = await self._make_app()
        async with app.run_test(size=(120, 40)) as pilot:
            await pilot.pause()
            app.editor.load_text("text")
            app.editor.set_cursor(0, 0)
            app.action_heading_2()
            await pilot.pause()
            self.assertTrue(app.editor.text.startswith("## "))

            app.action_unordered_list()
            await pilot.pause()
            self.assertTrue(app.editor.text.startswith("- "))

            app.editor.load_text("word")
            app.editor.select_all()
            app.action_bold()
            await pilot.pause()
            self.assertEqual(app.editor.text, "**word**")

    async def test_wrap_selection(self) -> None:
        """Wrapping a selection surrounds it with the marker pair."""
        app = await self._make_app()
        async with app.run_test(size=(120, 40)) as pilot:
            await pilot.pause()
            app.editor.load_text("word")
            app.editor.selection = ((0, 0), (0, 4))
            app._wrap("**")
            await pilot.pause()
            self.assertEqual(app.editor.text, "**word**")

    async def test_go_to_line(self) -> None:
        """Go to Line moves the cursor to the requested 1-based line."""
        app = await self._make_app()
        async with app.run_test(size=(120, 40)) as pilot:
            await pilot.pause()
            app.editor.load_text("one\ntwo\nthree\nfour")
            app.editor.set_cursor(0, 1)

            await pilot.press("ctrl+underscore")
            await pilot.pause()
            self.assertEqual(app.screen.form_title, "Go to Line")
            self.assertEqual(app.screen.query_one("#field-line").value, "1")

            app.screen.query_one("#field-line").value = "3"
            app.screen._submit()
            await pilot.pause()
            self.assertEqual(app.editor.cursor_location, (2, 0))

            app.action_go_to_line()
            await pilot.pause()
            self.assertEqual(app.screen.query_one("#field-line").value, "3")
            app.screen.query_one("#field-line").value = "99"
            app.screen._submit()
            await pilot.pause()
            self.assertEqual(app.screen.form_title, "Go to Line")
            self.assertEqual(app.editor.cursor_location, (2, 0))

    async def test_line_actions(self) -> None:
        """Line movement, deletion and indentation update the buffer."""
        app = await self._make_app()
        async with app.run_test(size=(120, 40)) as pilot:
            await pilot.pause()
            app.editor.load_text("first\nsecond\nthird")
            app.editor.set_cursor(1, 0)
            app.action_line_up()
            await pilot.pause()
            self.assertEqual(app.editor.text, "second\nfirst\nthird")

            app.action_delete_line()
            await pilot.pause()
            self.assertEqual(app.editor.text, "first\nthird")

            app.editor.load_text("a\nb")
            app.editor.select_lines(0, 1)
            app.action_add_indent()
            await pilot.pause()
            self.assertEqual(app.editor.text, "  a\n  b")

            app.action_remove_indent()
            await pilot.pause()
            self.assertEqual(app.editor.text, "a\nb")

    async def test_find_and_replace(self) -> None:
        """The application can find, replace one and replace all matches."""
        app = await self._make_app()
        async with app.run_test(size=(120, 40)) as pilot:
            await pilot.pause()
            app.editor.load_text("alpha beta alpha")
            self.assertTrue(app.find_next("alpha"))
            await pilot.pause()
            self.assertEqual(app.editor.selected_text, "alpha")
            self.assertTrue(app.replace_next("beta", "B"))
            await pilot.pause()
            self.assertIn("B", app.editor.text)
            count = app.replace_all("alpha", "X")
            await pilot.pause()
            self.assertEqual(count, 2)
            self.assertEqual(app.editor.text, "X B X")

    async def test_save_and_open(self) -> None:
        """Saving writes the buffer and opening reads it back."""
        app = await self._make_app()
        async with app.run_test(size=(120, 40)) as pilot:
            await pilot.pause()
            path = self._tmp / "document.md"
            app.editor.load_text("# Hello\n")
            await pilot.pause()
            app._save_to(path)
            await pilot.pause()
            self.assertTrue(path.exists())
            self.assertEqual(path.read_text(encoding="utf-8"), "# Hello\n")
            self.assertEqual(app.current_file, path)
            self.assertFalse(app.is_modified)

            app.editor.load_text("")
            app._open_path(path)
            await pilot.pause()
            self.assertEqual(app.editor.text, "# Hello\n")
            self.assertEqual(app.current_file, path)

    async def test_export_html(self) -> None:
        """The HTML export writes a complete document."""
        app = await self._make_app()
        async with app.run_test(size=(120, 40)) as pilot:
            await pilot.pause()
            app.editor.load_text("# Export")
            path = self._tmp / "export.html"
            app._write_export(path, "html")
            await pilot.pause()
            self.assertTrue(path.exists())
            self.assertIn("<h1>Export</h1>", path.read_text(encoding="utf-8"))

    async def test_export_text(self) -> None:
        """The plain-text export strips Markdown markup."""
        app = await self._make_app()
        async with app.run_test(size=(120, 40)) as pilot:
            await pilot.pause()
            app.editor.load_text("# Export\n\n**bold**")
            path = self._tmp / "export.txt"
            app._write_export(path, "text")
            await pilot.pause()
            self.assertTrue(path.exists())
            self.assertIn("Export", path.read_text(encoding="utf-8"))
            self.assertNotIn("# Export", path.read_text(encoding="utf-8"))

    async def test_dialogs_open_and_close(self) -> None:
        """Common dialogs open as modal screens and close with Escape."""
        app = await self._make_app()
        async with app.run_test(size=(120, 40)) as pilot:
            await pilot.pause()
            for action in (
                app.action_find,
                app.action_replace,
                app.action_table,
                app.action_ordered_list,
                app.action_todo_list,
                app.action_definition_list,
                app.action_code_block,
                app.action_table_alignment,
                app.action_yaml_front_matter,
                app.action_toc,
                app.action_about,
                app.action_help_shortcuts,
            ):
                action()
                await pilot.pause()
                self.assertIsNot(app.screen, app.screen_stack[0])
                await pilot.press("escape")
                await pilot.pause()
                self.assertIs(app.screen, app.screen_stack[0])

    async def test_theme_toggle(self) -> None:
        """The toggle cycles default → green → magenta → blue and persists."""
        app = await self._make_app()
        async with app.run_test(size=(120, 40)) as pilot:
            await pilot.pause()
            current = app.theme_mode
            self.assertEqual(current, DEFAULT_THEME)
            for _ in THEMES:
                expected = THEMES[(THEMES.index(current) + 1) % len(THEMES)]
                app.action_toggle_theme()
                await pilot.pause()
                self.assertEqual(app.theme_mode, expected)
                self.assertEqual(app.theme, APP_THEMES[expected].name)
                self.assertEqual(app.editor.theme, EDITOR_THEMES[expected].name)
                self.assertEqual(load_theme(), expected)
                current = expected
            self.assertEqual(current, DEFAULT_THEME)

    async def test_saved_theme_restored(self) -> None:
        """A theme saved in theme.json is applied on the next start."""
        save_theme("green")
        app = await self._make_app()
        async with app.run_test(size=(120, 40)) as pilot:
            await pilot.pause()
            self.assertEqual(app.theme_mode, "green")
            self.assertEqual(app.theme, APP_THEMES["green"].name)
            self.assertEqual(app.editor.theme, EDITOR_THEMES["green"].name)


if __name__ == "__main__":
    unittest.main()
