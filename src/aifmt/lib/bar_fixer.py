"""Fix misaligned progress bars and bar charts.

Detects bar-like patterns (consecutive fill + empty characters) and normalizes
them so groups of bars share a consistent total width.  When a percentage label
is present the fill/empty ratio is recalculated to match.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field

# ---------------------------------------------------------------------------
# Character sets recognised as "fill" or "empty" segments of a bar
# ---------------------------------------------------------------------------
_FILL_CHARS = set("█▓#=")
_EMPTY_CHARS = set("░○·.─-")

# Pattern: optional label, bar body, optional percentage
# We capture:
#   1. leading text (label + whitespace)
#   2. optional opening bracket [ or |
#   3. fill characters
#   4. empty characters (may be absent for 100 %)
#   5. optional closing bracket ] or |
#   6. optional trailing percentage like " 75%" or " 100%"
_BAR_RE = re.compile(
    r"^(?P<prefix>.*?)"                          # label / leading text
    r"(?P<open>[\[|])?"                           # optional open bracket
    r"(?P<fill>[█▓#=]{1,})"                       # filled portion
    r"(?P<empty>[░○·.\-─]{0,})"                   # empty portion (may be 0-length)
    r"(?P<close>[\]|])?"                          # optional close bracket
    r"(?P<suffix>\s+(?P<pct>\d{1,3})%)?$"         # optional percentage
)

# Also match bars that are *all* empty (0 %)
_EMPTY_BAR_RE = re.compile(
    r"^(?P<prefix>.*?)"
    r"(?P<open>[\[|])?"
    r"(?P<empty>[░○·.\-─]{2,})"                  # all-empty bar (min 2 chars)
    r"(?P<close>[\]|])?"
    r"(?P<suffix>\s+(?P<pct>0)%)?$"
)


@dataclass
class _BarInfo:
    """Parsed representation of a single bar line."""

    line_idx: int
    prefix: str
    open_bracket: str
    fill_char: str
    fill_count: int
    empty_char: str
    empty_count: int
    close_bracket: str
    pct: int | None          # percentage if present, else None
    suffix_space: str        # whitespace between bar end and percentage
    total: int = field(init=False)

    def __post_init__(self) -> None:
        self.total = self.fill_count + self.empty_count

    def render(self, new_total: int | None = None) -> str:
        total = new_total if new_total is not None else self.total
        if self.pct is not None:
            fill_n = round(total * self.pct / 100)
        else:
            # Keep original ratio
            if self.total > 0:
                fill_n = round(total * self.fill_count / self.total)
            else:
                fill_n = 0
        empty_n = total - fill_n

        fill_s = self.fill_char * fill_n
        empty_s = self.empty_char * empty_n
        bar = f"{self.open_bracket}{fill_s}{empty_s}{self.close_bracket}"
        if self.pct is not None:
            bar += f"{self.suffix_space}{self.pct}%"
        return self.prefix + bar


def _parse_bar(line: str, line_idx: int) -> _BarInfo | None:
    """Try to parse *line* as a bar.  Return ``_BarInfo`` or ``None``."""
    m = _BAR_RE.match(line)
    if m:
        fill_text = m.group("fill")
        empty_text = m.group("empty")
        pct_str = m.group("pct")
        suffix_match = m.group("suffix")
        # Determine suffix whitespace (between bar end and pct digits)
        suffix_space = ""
        if suffix_match:
            suffix_space = suffix_match[: suffix_match.index(pct_str)]
        return _BarInfo(
            line_idx=line_idx,
            prefix=m.group("prefix"),
            open_bracket=m.group("open") or "",
            fill_char=fill_text[0],
            fill_count=len(fill_text),
            empty_char=empty_text[0] if empty_text else "░",
            empty_count=len(empty_text),
            close_bracket=m.group("close") or "",
            pct=int(pct_str) if pct_str is not None else None,
            suffix_space=suffix_space,
        )

    # Try all-empty bar
    m = _EMPTY_BAR_RE.match(line)
    if m:
        empty_text = m.group("empty")
        pct_str = m.group("pct")
        suffix_match = m.group("suffix")
        suffix_space = ""
        if suffix_match and pct_str:
            suffix_space = suffix_match[: suffix_match.index(pct_str)]
        return _BarInfo(
            line_idx=line_idx,
            prefix=m.group("prefix"),
            open_bracket=m.group("open") or "",
            fill_char="█",  # default fill char for all-empty bars
            fill_count=0,
            empty_char=empty_text[0],
            empty_count=len(empty_text),
            close_bracket=m.group("close") or "",
            pct=int(pct_str) if pct_str is not None else None,
            suffix_space=suffix_space,
        )

    return None


def _group_consecutive(bars: list[_BarInfo]) -> list[list[_BarInfo]]:
    """Split bars into groups of consecutive line indices."""
    if not bars:
        return []
    groups: list[list[_BarInfo]] = [[bars[0]]]
    for bar in bars[1:]:
        if bar.line_idx == groups[-1][-1].line_idx + 1:
            groups[-1].append(bar)
        else:
            groups.append([bar])
    return groups


def fix_bars(text: str) -> tuple[str, list[str]]:
    """Fix misaligned progress bars and bar charts.

    Returns ``(fixed_text, list_of_change_descriptions)``.

    Rules
    -----
    * Bars on consecutive lines are treated as a *group* and normalised to
      the same total width (the maximum within the group).
    * If a bar carries a percentage label, the fill/empty ratio is
      recalculated to match that percentage regardless of grouping.
    * A single bar with no percentage is left untouched.
    """
    lines = text.split("\n")
    bars: list[_BarInfo] = []

    for idx, line in enumerate(lines):
        info = _parse_bar(line, idx)
        if info is not None:
            bars.append(info)

    if not bars:
        return text, []

    changes: list[str] = []
    groups = _group_consecutive(bars)

    for group in groups:
        # Determine target total width for the group
        max_total = max(b.total for b in group)

        for bar in group:
            need_fix = False
            target = bar.total  # default: keep own width

            # If part of a multi-bar group, normalize widths
            if len(group) > 1 and bar.total != max_total:
                target = max_total
                need_fix = True

            # If percentage present, recalculate fill/empty
            if bar.pct is not None:
                if len(group) > 1:
                    target = max_total
                expected_fill = round(target * bar.pct / 100)
                expected_empty = target - expected_fill
                if expected_fill != bar.fill_count or expected_empty != bar.empty_count:
                    need_fix = True

            if need_fix:
                old_line = lines[bar.line_idx]
                new_line = bar.render(target)
                if old_line != new_line:
                    lines[bar.line_idx] = new_line
                    changes.append(
                        f"L{bar.line_idx + 1}: bar width "
                        f"{bar.fill_count}+{bar.empty_count}={bar.total} → "
                        f"normalized to {target}"
                    )

    return "\n".join(lines), changes
