"""Pure text transformations used by the Markdown editor actions.

Keeping these functions free of Textual makes them easy to test and keeps the
UI layer focused on presenting dialogs and moving the cursor.
"""

from __future__ import annotations

import re
from datetime import date

_HEADING_RE = re.compile(r"^#{1,6}\s*")
_LIST_RE = re.compile(r"^(\* \[[ xX]\]\s*|(\d+\.|\*|-|>)\s*)")
_TABLE_ALIGN_RE = re.compile(r"^:?-{3,}:?$")
_TABLE_ROW_RE = re.compile(r"^\s*\|.*\|\s*$")


def strip_heading_marker(text: str) -> str:
    """Remove a leading Markdown heading marker (``#`` run) from *text*."""
    return _HEADING_RE.sub("", text)


def strip_list_marker(text: str) -> str:
    """Remove a leading ordered/unordered/todo/quote marker from *text*."""
    return _LIST_RE.sub("", text)


def set_heading(text: str, level: int) -> str:
    """Return *text* converted to a heading of *level* (1-6)."""
    level = max(1, min(6, level))
    return f"{'#' * level} {strip_heading_marker(text)}"


def set_paragraph(text: str) -> str:
    """Return *text* without a leading heading marker."""
    return strip_heading_marker(text)


def set_list_item(text: str, marker: str) -> str:
    """Return *text* prefixed with a list *marker* (``-``, ``1.`` or ``>``)."""
    return f"{marker} {strip_list_marker(text)}"


def set_todo_marker(text: str, checked: bool) -> str:
    """Add or update a ``[ ]`` / ``[x]`` marker on a list item."""
    state = "x" if checked else " "
    match = re.match(r"^((?:\d+\.|\*|-)\s+)?(\[[ xX]\])\s+", text)
    if match:
        return f"{match.group(1) or ''}[{state}] {text[match.end() :]}"
    match = re.match(r"^(\d+\.|\*|-)\s+", text)
    if match:
        return f"{match.group(0)}[{state}] {text[match.end() :]}"
    return text


def code_block(text: str, language: str = "") -> str:
    """Return *text* wrapped in a fenced code block."""
    language = language.strip()
    return f"```{language}\n{text}\n```"


def is_table_row(line: str) -> bool:
    """Return True when *line* looks like a Markdown table row."""
    return bool(_TABLE_ROW_RE.match(line))


def is_table_align_row(line: str) -> bool:
    """Return True when *line* is a Markdown table alignment row."""
    if not is_table_row(line):
        return False
    cells = [cell.strip() for cell in line.strip().strip("|").split("|")]
    return bool(cells) and all(_TABLE_ALIGN_RE.match(cell) for cell in cells)


def format_table_block(lines: list[str]) -> list[str]:
    """Reformat Markdown table *lines* with equal-width columns.

    Every row (header, separator and footer) is padded so that all columns
    share the same width and the right border is aligned.
    """
    rows = [line.split("|")[1:-1] for line in lines]
    ncols = max(len(row) for row in rows)
    widths = [max(len(row[col].strip()) for row in rows) for col in range(ncols)]
    out: list[str] = []
    for raw_row in rows:
        row = (raw_row + [""] * ncols)[:ncols]
        cells = [row[col].strip().ljust(widths[col]) for col in range(ncols)]
        out.append("| " + " | ".join(cells) + " |")
    return out


def balance_table(text: str, row: int) -> tuple[str, int, int] | None:
    """Balance the contiguous table around 0-based *row*.

    Returns ``(new_text, top, bottom)`` or ``None`` when the row is not a table
    row. ``top`` and ``bottom`` are 0-based line numbers of the new table.
    """
    lines = text.split("\n")
    if row < 0 or row >= len(lines) or not is_table_row(lines[row]):
        return None
    top = row
    while top > 0 and is_table_row(lines[top - 1]):
        top -= 1
    bottom = row
    while bottom + 1 < len(lines) and is_table_row(lines[bottom + 1]):
        bottom += 1
    block = format_table_block(lines[top : bottom + 1])
    lines[top : bottom + 1] = block
    return "\n".join(lines), top, top + len(block) - 1


def apply_table_alignment(
    text: str, row: int, col: int, marker: str
) -> tuple[str, int] | None:
    """Set the alignment cell under ``(row, col)`` to *marker*.

    Returns ``(new_text, new_col)`` when a cell was changed. Returns ``None``
    when the cursor is not inside an alignment cell.
    """
    lines = text.split("\n")
    if row < 0 or row >= len(lines):
        return None
    line = lines[row]
    cells: list[tuple[int, int]] = []
    start = 0
    for index, char in enumerate(line):
        if char == "|":
            cells.append((start, index))
            start = index + 1
    for cell_start, cell_end in cells:
        if cell_start <= col < cell_end and _TABLE_ALIGN_RE.match(
            line[cell_start:cell_end].strip()
        ):
            replacement = f" {marker} "
            lines[row] = line[:cell_start] + replacement + line[cell_end:]
            return "\n".join(lines), cell_start + len(replacement)
    return None


def make_table(columns: int, rows: int, footer: bool = True) -> str:
    """Build a Markdown table with header, alignment, body and optional footer."""
    columns = max(1, columns)
    rows = max(0, rows)
    header = "| " + " | ".join(["Header"] * columns) + " |"
    align = "| " + " | ".join(["---"] * columns) + " |"
    lines = ["", header, align]
    lines.extend("| " + " | ".join(["Cell"] * columns) + " |" for _ in range(rows))
    if footer:
        lines.append("| " + " | ".join(["==="] * columns) + " |")
        lines.append("| " + " | ".join(["Footer"] * columns) + " |")
    return "\n".join(lines)


def make_table_row(count: int) -> str:
    """Build a single table row with *count* cells."""
    count = max(1, count)
    return "| " + " | ".join(["Cell"] * count) + " |"


def make_definition_list(term: str, count: int) -> str:
    """Build a Markdown definition-list block."""
    count = max(1, count)
    lines = ["", term]
    lines.extend(f": Definition {i}" for i in range(1, count + 1))
    return "\n".join(lines)


def make_yaml_front_matter(values: dict[str, str]) -> str:
    """Build a YAML front-matter block from filled fields."""
    lines = ["---"]
    for field in ("lang", "title", "author", "description", "keywords"):
        value = values.get(field, "").strip()
        if value:
            lines.append(f"{field}: {value}")
    lines.append(f"published: {date.today().isoformat()}")
    lines.append("---")
    return "\n".join(lines)


def comment_inline(text: str) -> str:
    """Return a single hidden Markdown comment line."""
    return f"[{text.strip()}]: #"


def comment_block(selected: str) -> str:
    """Turn every non-empty line of a selection into a hidden comment."""
    lines = selected.strip("\n").split("\n")
    return "\n".join(comment_inline(line) for line in lines if line.strip()) + "\n"


def move_lines(
    text: str, start: int, end: int, delta: int
) -> tuple[str, int, int] | None:
    """Move the 0-based line block ``start..end`` up or down by one.

    Returns ``(new_text, new_start, new_end)`` or ``None`` at a document edge.
    """
    lines = text.split("\n")
    if delta < 0:
        if start <= 0:
            return None
        block = lines[start : end + 1]
        lines[start - 1 : end + 1] = [*block, lines[start - 1]]
        return "\n".join(lines), start - 1, end - 1
    if delta > 0:
        if end >= len(lines) - 1:
            return None
        block = lines[start : end + 1]
        lines[start : end + 2] = [lines[end + 1], *block]
        return "\n".join(lines), start + 1, end + 1
    return None


def delete_line(text: str, row: int) -> tuple[str, int, int]:
    """Delete 0-based *row* and return ``(new_text, cursor_row, cursor_col)``."""
    lines = text.split("\n")
    if not lines:
        return text, 0, 0
    row = max(0, min(row, len(lines) - 1))
    lines.pop(row)
    if not lines:
        lines = [""]
    new_row = min(row, len(lines) - 1)
    return "\n".join(lines), new_row, 0


def indent_lines(text: str, start: int, end: int, prefix: str = "  ") -> str:
    """Prefix every 0-based line in ``start..end`` with *prefix*."""
    lines = text.split("\n")
    for row in range(max(0, start), min(end, len(lines) - 1) + 1):
        lines[row] = prefix + lines[row]
    return "\n".join(lines)


def outdent_lines(text: str, start: int, end: int) -> str:
    """Remove up to two leading spaces from lines in ``start..end``."""
    lines = text.split("\n")
    for row in range(max(0, start), min(end, len(lines) - 1) + 1):
        if lines[row].startswith("  "):
            lines[row] = lines[row][2:]
        elif lines[row].startswith(" "):
            lines[row] = lines[row][1:]
    return "\n".join(lines)


def insert_block(text: str, row: int, col: int, block: str) -> tuple[str, int, int]:
    """Insert *block* at ``(row, col)`` with a blank line before it when needed.

    The block is expected not to include the final newline. Returns the new
    text and cursor location at the end of the inserted block.
    """
    lines = text.split("\n")
    row = max(0, min(row, len(lines) - 1))
    block_lines = block.split("\n")
    while block_lines and not block_lines[0].strip():
        block_lines.pop(0)
    if not block_lines:
        block_lines = [""]
    if row > 0 and lines[row - 1].strip():
        lines.insert(row, "")
        row += 1
    line = lines[row]
    col = max(0, min(col, len(line)))
    prefix = line[:col]
    suffix = line[col:]
    replacement = [prefix + block_lines[0], *block_lines[1:], suffix]
    lines[row : row + 1] = replacement
    new_row = row + len(block_lines) - 1
    new_col = len(block_lines[-1])
    return "\n".join(lines), new_row, new_col


def hard_line_break(text: str, row: int, col: int) -> tuple[str, int, int]:
    """Insert a Markdown hard line break (two spaces + newline) at the cursor."""
    lines = text.split("\n")
    row = max(0, min(row, len(lines) - 1))
    line = lines[row]
    col = max(0, min(col, len(line)))
    lines[row : row + 1] = [line[:col] + "  ", line[col:]]
    return "\n".join(lines), row + 1, 0
