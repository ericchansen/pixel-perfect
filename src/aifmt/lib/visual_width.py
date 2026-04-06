"""Visual width calculation for terminal and web monospace text.

The core insight of aifmt: characters occupy different numbers of
monospace columns depending on *where* they render. Emoji and East Asian
wide characters take 2 columns in terminal emulators (the Unicode standard),
but web renderers like GitHub, Slack, and Discord use their own font metrics
where emoji can be ~3 columns wide and CJK behaviour varies.

This module uses **rendering profiles** to encapsulate those differences.
Each profile defines how wide emoji, CJK, and other character classes are
in a particular rendering context. The built-in profiles are:

- ``"terminal"`` — Unicode East Asian Width standard (iTerm2, Windows Terminal, etc.)
- ``"github"`` — GitHub markdown code blocks (emoji ≈ 3 cols)

Profiles are extensible: call :func:`register_profile` to add your own
(e.g. ``"slack"``, ``"discord"``, ``"vscode"``, ``"obsidian"``).

This module provides visual-width-aware replacements for common string
operations: measuring, padding, truncating, and centering.
"""

from __future__ import annotations

import math
import re
import unicodedata
from dataclasses import dataclass

# ANSI escape sequence pattern: ESC[ ... final_byte
_ANSI_RE = re.compile(r"\033\[[0-9;]*[A-Za-z]")

# Emoji variation selectors and ZWJ
_VS16 = "\ufe0f"  # emoji presentation
_VS15 = "\ufe0e"  # text presentation
_ZWJ = "\u200d"  # zero-width joiner


# ---------------------------------------------------------------------------
# Rendering profiles
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class RenderProfile:
    """Width rules for a specific rendering context.

    Attributes:
        name: Human-readable identifier (e.g. ``"github"``).
        emoji_width: Column width for emoji characters (default: 2.0).
            Can be fractional — GitHub renders emoji at ~2.5 monospace columns.
        cjk_width: Column width for CJK ideographs (default: 2.0).
        wide_eaw_width: Column width for other East Asian Wide/Fullwidth (default: 2.0).
        description: Optional one-liner for docs / ``list_profiles()``.
    """

    name: str
    emoji_width: float = 2.0
    cjk_width: float = 2.0
    wide_eaw_width: float = 2.0
    description: str = ""


# Built-in profiles
_PROFILES: dict[str, RenderProfile] = {}


def _register_builtins() -> None:
    _PROFILES["terminal"] = RenderProfile(
        name="terminal",
        emoji_width=2.0,
        cjk_width=2.0,
        wide_eaw_width=2.0,
        description="Unicode East Asian Width standard — works in most terminal emulators",
    )
    _PROFILES["github"] = RenderProfile(
        name="github",
        emoji_width=2.5,
        cjk_width=2.0,
        wide_eaw_width=2.0,
        description=(
            "GitHub markdown code blocks — emoji render ~2.5 monospace columns. "
            "Even emoji counts per line align perfectly; odd counts have ±0.5 col error."
        ),
    )


_register_builtins()

# Convenience constant — valid built-in target names
TARGETS = tuple(_PROFILES.keys())


def register_profile(profile: RenderProfile) -> None:
    """Register a custom rendering profile.

    >>> register_profile(RenderProfile("slack", emoji_width=2, cjk_width=1,
    ...                                description="Slack code blocks"))
    """
    _PROFILES[profile.name] = profile


def get_profile(target: str) -> RenderProfile:
    """Return the :class:`RenderProfile` for *target*, or raise ``ValueError``."""
    try:
        return _PROFILES[target]
    except KeyError:
        names = ", ".join(sorted(_PROFILES))
        raise ValueError(f"Unknown target {target!r}. Registered profiles: {names}")


def list_profiles() -> list[RenderProfile]:
    """Return all registered rendering profiles."""
    return list(_PROFILES.values())


def _is_emoji_presentation(ch: str) -> bool:
    """Return True if *ch* is an emoji that gets colorful/graphical rendering.

    On GitHub's monospace code font, these characters render wider than the
    2 columns that Unicode East Asian Width assigns them — closer to 3.
    """
    cp = ord(ch)
    cat = unicodedata.category(ch)

    # Symbol, Other (So) with East Asian Width W — covers most emoji:
    # ✅ ❌ 📦 🚀 🔥 ⭐ etc.
    if cat == "So" and unicodedata.east_asian_width(ch) in ("W", "F"):
        return True

    # Emoticons block (U+1F600–U+1F64F)
    if 0x1F600 <= cp <= 0x1F64F:
        return True

    # Miscellaneous Symbols and Pictographs (U+1F300–U+1F5FF)
    if 0x1F300 <= cp <= 0x1F5FF:
        return True

    # Supplemental Symbols and Pictographs (U+1F900–U+1F9FF)
    if 0x1F900 <= cp <= 0x1F9FF:
        return True

    # Symbols and Pictographs Extended-A (U+1FA00–U+1FA6F)
    if 0x1FA00 <= cp <= 0x1FA6F:
        return True

    # Transport and Map Symbols (U+1F680–U+1F6FF)
    if 0x1F680 <= cp <= 0x1F6FF:
        return True

    return False


def _visual_width_f(text: str, profile: RenderProfile) -> float:
    """Internal: precise visual width as a float.

    Used by fixers that need sub-column accuracy (e.g. GitHub emoji at 2.5 cols).
    """
    stripped = _ANSI_RE.sub("", text)

    width: float = 0
    chars = list(stripped)
    i = 0
    while i < len(chars):
        ch = chars[i]

        if ch in (_ZWJ, _VS15, _VS16):
            i += 1
            continue

        cat = unicodedata.category(ch)
        if cat.startswith("M"):
            i += 1
            continue

        if cat.startswith("C") and ch not in ("\t",):
            i += 1
            continue

        eaw = unicodedata.east_asian_width(ch)

        next_ch = chars[i + 1] if i + 1 < len(chars) else None

        if next_ch == _VS15:
            width += 1
            i += 2
            continue
        elif next_ch == _VS16:
            width += profile.emoji_width
            i += 2
            continue

        if eaw in ("W", "F"):
            if _is_emoji_presentation(ch):
                width += profile.emoji_width
            elif _is_cjk_ideograph(ch):
                width += profile.cjk_width
            else:
                width += profile.wide_eaw_width
        else:
            width += 1

        i += 1

    return width


def visual_width(text: str, *, target: str = "terminal") -> int:
    """Return the number of display columns *text* occupies.

    Args:
        text: The string to measure.
        target: Rendering context name (e.g. ``"terminal"``, ``"github"``).
            See :func:`list_profiles` for all registered profiles.

    Returns an integer (rounded from the precise float width). For profiles
    with fractional character widths (e.g. GitHub emoji at 2.5 cols), use
    :func:`visual_width_precise` to get the exact float.

    - ANSI escape sequences: 0 columns
    - East Asian Wide/Fullwidth characters: per-profile (2 terminal, varies others)
    - Emoji: per-profile (2 terminal, 2.5 github)
    - Zero-width joiners and combining marks: 0 columns
    - Most other printable characters: 1 column

    >>> visual_width("hello")
    5
    >>> visual_width("古池")
    4
    >>> visual_width("📦 box")
    6
    >>> visual_width("📦 box", target="github")
    6
    >>> visual_width("\\033[31mred\\033[0m")
    3
    """
    profile = get_profile(target)
    return round(_visual_width_f(text, profile))


def visual_width_precise(text: str, *, target: str = "terminal") -> float:
    """Return the precise visual width of *text* as a float.

    Unlike :func:`visual_width` (which rounds to int), this preserves
    fractional widths. Essential for computing padding when a profile uses
    non-integer character widths (e.g. GitHub emoji at 2.5 cols).

    >>> visual_width_precise("📦 box", target="github")
    6.5
    """
    profile = get_profile(target)
    return _visual_width_f(text, profile)


def visual_pad(
    text: str,
    target_width: int,
    fill: str = " ",
    align: str = "left",
    *,
    target: str = "terminal",
) -> str:
    """Pad `text` to `target_width` visual columns.

    Args:
        text: The string to pad.
        target_width: Desired visual width.
        fill: Single character to use for padding (default: space).
        align: "left", "right", or "center".
        target: Rendering context — ``"terminal"`` or ``"github"``.

    Returns:
        Padded string. If text is already wider than target, returns text unchanged.

    >>> visual_pad("hi", 10)
    'hi        '
    >>> visual_pad("古池", 10)
    '古池      '
    >>> visual_pad("hi", 10, align="right")
    '        hi'
    >>> visual_pad("hi", 10, align="center")
    '    hi    '
    """
    current = visual_width_precise(text, target=target)
    if current >= target_width:
        return text

    # Use floor: when width is fractional (odd emoji count), prefer shorter
    # padding so the result is slightly narrow rather than slightly wide.
    pad_needed = math.floor(target_width - current)

    if align == "right":
        return fill * pad_needed + text
    elif align == "center":
        left_pad = pad_needed // 2
        right_pad = pad_needed - left_pad
        return fill * left_pad + text + fill * right_pad
    else:  # left
        return text + fill * pad_needed


def visual_truncate(
    text: str,
    max_width: int,
    suffix: str = "…",
    *,
    target: str = "terminal",
) -> str:
    """Truncate `text` to fit within `max_width` visual columns.

    If truncation is needed, appends `suffix` (which counts toward the width).
    ANSI escape codes in the truncated portion are preserved/closed.

    Args:
        text: The string to truncate.
        max_width: Maximum visual width.
        suffix: String to append when truncated (default: "…").
        target: Rendering context — ``"terminal"`` or ``"github"``.

    Returns:
        Truncated string fitting within max_width visual columns.

    >>> visual_truncate("hello world", 8)
    'hello w…'
    >>> visual_truncate("hi", 10)
    'hi'
    """
    if visual_width(text, target=target) <= max_width:
        return text

    suffix_w = visual_width(suffix, target=target)
    target_w = max_width - suffix_w

    if target_w <= 0:
        return suffix[:max_width] if suffix_w <= max_width else ""

    # Strip ANSI for width counting, but build result from original
    result_chars: list[str] = []
    current_width = 0
    in_escape = False
    escape_buf: list[str] = []

    for ch in text:
        if in_escape:
            escape_buf.append(ch)
            if ch.isalpha():
                in_escape = False
                result_chars.extend(escape_buf)
                escape_buf = []
            continue

        if ch == "\033":
            in_escape = True
            escape_buf = [ch]
            continue

        ch_w = _char_width(ch, target=target)
        if current_width + ch_w > target_w:
            break

        result_chars.append(ch)
        current_width += ch_w

    return "".join(result_chars) + suffix


def visual_center(
    text: str,
    width: int,
    fill: str = " ",
    *,
    target: str = "terminal",
) -> str:
    """Center `text` within `width` visual columns.

    Shorthand for ``visual_pad(text, width, fill, align="center")``.

    >>> visual_center("hi", 10)
    '    hi    '
    """
    return visual_pad(text, width, fill, align="center", target=target)


def strip_ansi(text: str) -> str:
    """Remove all ANSI escape sequences from text.

    >>> strip_ansi("\\033[31mred\\033[0m")
    'red'
    """
    return _ANSI_RE.sub("", text)


def _is_cjk_ideograph(ch: str) -> bool:
    """Return True if *ch* is a CJK unified ideograph or common CJK symbol."""
    cp = ord(ch)
    # CJK Unified Ideographs
    if 0x4E00 <= cp <= 0x9FFF:
        return True
    # CJK Extension A
    if 0x3400 <= cp <= 0x4DBF:
        return True
    # CJK Extension B–G (SIP/TIP)
    if 0x20000 <= cp <= 0x3134F:
        return True
    # CJK Compatibility Ideographs
    if 0xF900 <= cp <= 0xFAFF:
        return True
    # Katakana and Hiragana
    if 0x3040 <= cp <= 0x30FF:
        return True
    # CJK Symbols and Punctuation
    if 0x3000 <= cp <= 0x303F:
        return True
    # Fullwidth Latin / Halfwidth Katakana
    if 0xFF00 <= cp <= 0xFFEF:
        return True
    return False


def _char_width(ch: str, *, target: str = "terminal") -> float:
    """Return the visual width of a single character."""
    profile = get_profile(target)
    cat = unicodedata.category(ch)
    if cat.startswith("M") or cat.startswith("C"):
        return 0
    eaw = unicodedata.east_asian_width(ch)
    if eaw in ("W", "F"):
        if _is_emoji_presentation(ch):
            return profile.emoji_width
        if _is_cjk_ideograph(ch):
            return profile.cjk_width
        return profile.wide_eaw_width
    return 1
