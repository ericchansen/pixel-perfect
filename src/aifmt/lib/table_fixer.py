"""Fix misaligned markdown tables by recalculating column widths using visual width.

When a markdown table contains emoji, CJK characters, or other wide characters,
columns won't align because ``len("📦")`` returns 1 but the character occupies
2 terminal columns. This module re-pads every cell using :func:`visual_width`
and :func:`visual_pad` so pipe characters line up correctly.
"""

from __future__ import annotations

import math
import re

from aifmt.lib.visual_width import visual_pad, visual_width_precise

# Matches a valid separator cell: optional colon, one-or-more dashes, optional colon
_SEP_CELL_RE = re.compile(r"^\s*:?-+:?\s*$")


def fix_tables(text: str, *, target: str = "terminal") -> tuple[str, list[str]]:
    """Fix misaligned markdown tables in text.

    Returns:
        Tuple of (fixed_text, list of change descriptions).
    """
    lines = text.split("\n")
    changes: list[str] = []
    result_lines: list[str] = []
    i = 0

    while i < len(lines):
        # A table starts with a header row (contains |) followed by a separator row.
        if (
            i + 1 < len(lines)
            and "|" in lines[i]
            and _is_separator_row(lines[i + 1])
        ):
            header_line = lines[i]
            sep_line = lines[i + 1]
            body_lines: list[str] = []
            i += 2

            while i < len(lines) and "|" in lines[i] and lines[i].strip():
                # Stop if the current line is itself a separator row
                if _is_separator_row(lines[i]):
                    break
                # Stop if the *next* line is a separator — current line is
                # likely the header of a new back-to-back table.
                if i + 1 < len(lines) and _is_separator_row(lines[i + 1]):
                    break
                body_lines.append(lines[i])
                i += 1

            fixed, table_changes = _fix_table(
                header_line, sep_line, body_lines, target=target,
            )
            result_lines.extend(fixed)
            changes.extend(table_changes)
        else:
            result_lines.append(lines[i])
            i += 1

    return "\n".join(result_lines), changes


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _is_separator_row(line: str) -> bool:
    """Return True if *line* is a markdown table separator (e.g. ``| --- | :---: |``)."""
    if "|" not in line:
        return False
    cells = _split_row(line)
    if not cells:
        return False
    return all(_SEP_CELL_RE.match(cell) for cell in cells)


def _split_row(line: str) -> list[str]:
    """Split a table row into raw cell strings by ``|`` delimiter."""
    stripped = line.strip()
    if not stripped:
        return []
    if stripped.startswith("|"):
        stripped = stripped[1:]
    if stripped.endswith("|"):
        stripped = stripped[:-1]
    if not stripped:
        return []
    return stripped.split("|")


def _fix_table(
    header: str,
    separator: str,
    body_lines: list[str],
    *,
    target: str = "terminal",
) -> tuple[list[str], list[str]]:
    """Realign a single markdown table and return (fixed_lines, changes)."""
    changes: list[str] = []

    # Preserve leading/trailing pipe style from the header
    leading = header.strip().startswith("|")
    trailing = header.strip().endswith("|")

    # Parse every row into stripped cell contents
    header_cells = [c.strip() for c in _split_row(header)]
    sep_cells = [c.strip() for c in _split_row(separator)]
    body_cell_rows = [[c.strip() for c in _split_row(line)] for line in body_lines]

    # Canonical column count = max across all rows
    all_counts = [len(header_cells), len(sep_cells)]
    all_counts.extend(len(row) for row in body_cell_rows)
    num_cols = max(all_counts) if all_counts else 0
    if num_cols == 0:
        return [header, separator] + body_lines, changes

    # Pad short rows to num_cols
    def _pad(cells: list[str], n: int) -> list[str]:
        return (cells + [""] * n)[:n]

    header_cells = _pad(header_cells, num_cols)
    sep_cells = _pad(sep_cells, num_cols)
    body_cell_rows = [_pad(row, num_cols) for row in body_cell_rows]

    # Extract alignment markers (leading/trailing colons) from separator
    alignments: list[tuple[bool, bool]] = []
    for cell in sep_cells:
        alignments.append((cell.startswith(":"), cell.endswith(":")))
    while len(alignments) < num_cols:
        alignments.append((False, False))

    # Determine column widths (minimum 3 so separators stay valid).
    # Use precise (float) widths so fractional emoji widths produce correct
    # integer column widths via ceiling — e.g. a cell with one emoji at 2.5
    # cols needs a column width of 3, not 2.
    col_widths: list[int] = []
    for col in range(num_cols):
        widths = [visual_width_precise(header_cells[col], target=target)]
        for row in body_cell_rows:
            widths.append(visual_width_precise(row[col], target=target))
        col_widths.append(max(math.ceil(max(widths)), 3))

    # --- rebuild rows ---

    def _build_content_row(cells: list[str]) -> str:
        parts = []
        for cell, width in zip(cells, col_widths):
            padded = visual_pad(cell, width, target=target)
            parts.append(f" {padded} ")
        row = "|".join(parts)
        if leading:
            row = "|" + row
        if trailing:
            row = row + "|"
        return row

    def _build_separator_row() -> str:
        parts = []
        for width, (left_c, right_c) in zip(col_widths, alignments):
            colons = int(left_c) + int(right_c)
            dashes = max(width - colons, 1)
            cell = ""
            if left_c:
                cell += ":"
            cell += "-" * dashes
            if right_c:
                cell += ":"
            parts.append(f" {cell} ")
        row = "|".join(parts)
        if leading:
            row = "|" + row
        if trailing:
            row = row + "|"
        return row

    new_header = _build_content_row(header_cells)
    new_sep = _build_separator_row()
    new_body = [_build_content_row(row) for row in body_cell_rows]

    fixed = [new_header, new_sep] + new_body
    original = [header, separator] + body_lines

    if fixed != original:
        changes.append(
            f"Fixed table alignment ({num_cols} columns, {len(body_lines)} data rows)"
        )

    # Warn about cells with fractional widths (odd emoji count on fractional targets)
    profile = _get_profile(target)
    if profile.emoji_width != int(profile.emoji_width):
        all_rows = [header_cells] + body_cell_rows
        warned_cols: set[int] = set()
        for row in all_rows:
            for col, cell in enumerate(row):
                if col in warned_cols:
                    continue
                pw = visual_width_precise(cell, target=target)
                if pw != int(pw):
                    emoji_n = _count_emoji_in_text(cell)
                    changes.append(
                        f"⚠ Column {col + 1}: cell \"{cell}\" has {emoji_n} emoji "
                        f"(odd count → fractional width {pw}). Pipe alignment will be "
                        f"off by {abs(pw - round(pw)):.1f} cols on {target}. "
                        f"Use an even number of emoji per cell, or avoid emoji for "
                        f"this target."
                    )
                    warned_cols.add(col)

    return fixed, changes


def _count_emoji_in_text(text: str) -> int:
    """Count emoji characters in text."""
    from aifmt.lib.visual_width import _is_emoji_presentation
    return sum(1 for ch in text if _is_emoji_presentation(ch))


def _get_profile(target: str):
    """Get the rendering profile for the given target."""
    from aifmt.lib.visual_width import get_profile
    return get_profile(target)
