"""Fix misaligned ASCII and Unicode box-drawing diagrams.

Detects box regions in text (groups of lines forming boxes using border
characters) and fixes right-edge alignment using visual width calculation.

Handles:
- ASCII boxes: + corners, - horizontal, | vertical
- Unicode boxes: ┌┐└┘├┤┬┴┼ corners, ─ horizontal, │ vertical
- Rounded boxes: ╭╮╰╯ corners, ─ horizontal, │ vertical
- Stacked boxes (multiple boxes vertically)
- Nested boxes (boxes inside boxes)
"""

from __future__ import annotations

import math

from aifmt.lib.visual_width import visual_width, visual_width_precise

# Border character sets
_ASCII_CORNERS = set("+-")
_ASCII_H = "-"
_ASCII_V = "|"

_UNICODE_CORNERS = set("┌┐└┘├┤┬┴┼╭╮╰╯╔╗╚╝╠╣╦╩╬")
_UNICODE_H = set("─━═")
_UNICODE_V = set("│┃║")

_ALL_CORNERS = _ASCII_CORNERS | _UNICODE_CORNERS
_ALL_H = {_ASCII_H} | _UNICODE_H
_ALL_V = {_ASCII_V} | _UNICODE_V
_ALL_BORDER = _ALL_CORNERS | _ALL_H | _ALL_V


def fix_boxes(text: str, *, target: str = "terminal") -> tuple[str, list[str]]:
    """Fix misaligned box borders in text.

    Returns:
        Tuple of (fixed_text, list of change/warning descriptions).
        Warnings start with "⚠" when perfect alignment is impossible
        (e.g. odd emoji count on a fractional-width target like GitHub).
        If no changes needed, returns (original_text, []).
    """
    lines = text.split("\n")
    changes: list[str] = []
    result_lines = list(lines)

    # Find horizontal border lines (top or bottom of boxes)
    border_lines = _find_border_lines(lines)

    # Group border lines into box regions (top + bottom pairs)
    box_regions = _pair_borders(border_lines, lines, target=target)

    # Fix each box region
    for region in box_regions:
        region_changes = _fix_box_region(result_lines, region, target=target)
        changes.extend(region_changes)

    fixed_text = "\n".join(result_lines)
    return fixed_text, changes


def _find_border_lines(lines: list[str]) -> list[int]:
    """Find line indices that look like horizontal box borders."""
    borders = []
    for i, line in enumerate(lines):
        stripped = line.strip()
        if not stripped:
            continue
        if _is_border_line(stripped):
            borders.append(i)
    return borders


def _is_border_line(stripped: str) -> bool:
    """Check if a line is a horizontal border line.

    A border line starts and ends with a corner character and has
    horizontal fill characters in between.
    """
    if len(stripped) < 3:
        return False

    # Check first and last chars are corners or border chars
    first = stripped[0]
    last = stripped[-1]

    if first in _ALL_CORNERS and last in _ALL_CORNERS:
        # Middle should be mostly horizontal chars, corners, or spaces
        middle = stripped[1:-1]
        h_count = sum(1 for c in middle if c in _ALL_H or c in _ALL_CORNERS)
        return h_count >= len(middle) * 0.5

    return False


def _pair_borders(
    border_indices: list[int],
    lines: list[str],
    *,
    target: str = "terminal",
) -> list[dict]:
    """Pair top and bottom borders into box regions.

    Returns list of dicts with:
        - top: line index of top border
        - bottom: line index of bottom border
        - indent: leading whitespace of the box
    """
    regions = []
    used = set()

    for i, top_idx in enumerate(border_indices):
        if top_idx in used:
            continue

        top_line = lines[top_idx]
        indent = len(top_line) - len(top_line.lstrip())
        top_width = visual_width(top_line.strip(), target=target)

        # Look for matching bottom border
        for bottom_idx in border_indices[i + 1 :]:
            if bottom_idx in used:
                continue

            bottom_line = lines[bottom_idx]
            bottom_indent = len(bottom_line) - len(bottom_line.lstrip())

            # Must have same indentation level
            if bottom_indent != indent:
                continue

            bottom_width = visual_width(bottom_line.strip(), target=target)

            # Widths should be close (within tolerance for misalignment)
            if abs(top_width - bottom_width) <= 3:
                # Check that lines between are content lines (have vertical borders)
                if _has_content_lines(lines, top_idx, bottom_idx, indent):
                    regions.append(
                        {
                            "top": top_idx,
                            "bottom": bottom_idx,
                            "indent": indent,
                        }
                    )
                    used.add(top_idx)
                    used.add(bottom_idx)
                    break

    return regions


def _has_content_lines(lines: list[str], top: int, bottom: int, indent: int) -> bool:
    """Check if lines between top and bottom look like box content."""
    if bottom - top < 2:
        return False

    content_count = 0
    for idx in range(top + 1, bottom):
        line = lines[idx]
        stripped = line.strip()
        if not stripped:
            continue
        if stripped[0] in _ALL_V or stripped[-1] in _ALL_V:
            content_count += 1

    return content_count > 0


def _fix_box_region(lines: list[str], region: dict, *, target: str = "terminal") -> list[str]:
    """Fix alignment within a single box region."""
    changes = []
    top_idx = region["top"]
    bottom_idx = region["bottom"]
    indent = region["indent"]

    # Determine the target width from the top border
    top_line = lines[top_idx]
    target_width = visual_width(top_line.strip(), target=target)

    # Determine the border style
    top_stripped = top_line.strip()
    top_stripped[-1]
    left_v, right_v = _detect_vertical_chars(top_stripped)

    # Fix bottom border to match top width
    bottom_line = lines[bottom_idx]
    bottom_stripped = bottom_line.strip()
    if visual_width(bottom_stripped, target=target) != target_width:
        fixed_bottom = _resize_border_line(bottom_stripped, target_width)
        lines[bottom_idx] = " " * indent + fixed_bottom
        changes.append(f"Line {bottom_idx + 1}: fixed bottom border width")

    # Fix content lines
    for idx in range(top_idx + 1, bottom_idx):
        line = lines[idx]
        stripped = line.strip()
        if not stripped:
            continue

        # Use precise width to detect fractional misalignment
        current_width_precise = visual_width_precise(stripped, target=target)
        if current_width_precise == target_width:
            continue

        # Check if it's an intermediate border line (├─┤)
        if _is_border_line(stripped):
            fixed = _resize_border_line(stripped, target_width)
            lines[idx] = " " * indent + fixed
            changes.append(f"Line {idx + 1}: fixed intermediate border width")
            continue

        # It's a content line — fix the right border
        fixed = _fix_content_line(
            stripped,
            target_width,
            left_v,
            right_v,
            target=target,
        )
        if fixed != stripped:
            lines[idx] = " " * indent + fixed
            changes.append(f"Line {idx + 1}: fixed content line alignment")

        # Check if the fixed line has fractional width (imperfect alignment)
        fixed_precise = visual_width_precise(
            lines[idx].strip() if fixed != stripped else stripped,
            target=target,
        )
        remainder = fixed_precise - target_width
        if remainder != 0 and remainder != int(remainder):
            emoji_count = _count_emoji(lines[idx].strip())
            changes.append(
                f"⚠ Line {idx + 1}: alignment off by {abs(remainder):.1f} cols "
                f"({emoji_count} emoji — odd count). On {target}, emoji are "
                f"fractional width. Use an even number of emoji per line, "
                f"or avoid emoji in bordered content for this target."
            )

    return changes


def _count_emoji(text: str) -> int:
    """Count emoji characters in text."""
    from aifmt.lib.visual_width import _is_emoji_presentation

    return sum(1 for ch in text if _is_emoji_presentation(ch))


def _detect_vertical_chars(border_line: str) -> tuple[str, str]:
    """Detect the vertical border characters from a horizontal border line."""
    first = border_line[0]
    last = border_line[-1]

    # Map corners to their vertical counterparts
    if first in "┌╭├╔╠":
        left_v = "│"
    elif first in "+":
        left_v = "|"
    else:
        left_v = "│"

    if last in "┐╮┤╗╣":
        right_v = "│"
    elif last in "+":
        right_v = "|"
    else:
        right_v = "│"

    return left_v, right_v


def _resize_border_line(stripped: str, target_width: int) -> str:
    """Resize a border line to target visual width."""
    if not stripped:
        return stripped

    first = stripped[0]
    last = stripped[-1]
    current_width = visual_width(stripped)

    if current_width == target_width:
        return stripped

    # Find the fill character (most common char in the middle)
    middle = stripped[1:-1]
    fill_char = _dominant_char(middle, _ALL_H) or "─"

    # Rebuild: first + fill + last
    fill_needed = target_width - 2  # minus corners
    return first + fill_char * fill_needed + last


def _dominant_char(text: str, char_set: set) -> str | None:
    """Find the most common character from char_set in text."""
    counts: dict[str, int] = {}
    for ch in text:
        if ch in char_set:
            counts[ch] = counts.get(ch, 0) + 1
    if not counts:
        return None
    return max(counts, key=counts.get)  # type: ignore[arg-type]


def _fix_content_line(
    stripped: str,
    target_width: int,
    left_v: str,
    right_v: str,
    *,
    target: str = "terminal",
) -> str:
    """Fix a content line to match target_width by adjusting padding before right border."""
    if not stripped:
        return stripped

    current_width = visual_width_precise(stripped, target=target)
    if current_width == target_width:
        return stripped

    # Find the right border character
    has_right = stripped[-1] in _ALL_V
    has_left = stripped[0] in _ALL_V

    if not has_left and not has_right:
        return stripped  # Not a box content line

    if has_right:
        # Remove right border, adjust padding, re-add border
        content = stripped[:-1]
        content_trimmed = content.rstrip()
        content_width = visual_width_precise(content_trimmed, target=target)
        # Use floor: when padding is fractional (odd emoji count), prefer the
        # shorter side — right border slightly left is less jarring than right.
        pad_needed = math.floor(target_width - content_width - 1)
        if pad_needed < 1:
            pad_needed = 1
        return content_trimmed + " " * pad_needed + stripped[-1]
    elif has_left:
        content = stripped
        content_width = visual_width_precise(content, target=target)
        pad_needed = math.floor(target_width - content_width - 1)
        if pad_needed < 0:
            pad_needed = 0
        return content + " " * pad_needed + right_v

    return stripped
