"""Tests for visual_width module."""

from aifmt.lib.visual_width import (
    strip_ansi,
    visual_center,
    visual_pad,
    visual_truncate,
    visual_width,
)


class TestVisualWidth:
    """Test visual_width() function."""

    def test_ascii_string(self) -> None:
        assert visual_width("hello") == 5

    def test_empty_string(self) -> None:
        assert visual_width("") == 0

    def test_single_space(self) -> None:
        assert visual_width(" ") == 1

    def test_cjk_characters(self) -> None:
        # CJK characters are 2 columns each
        assert visual_width("古池") == 4
        assert visual_width("你好世界") == 8

    def test_emoji_basic(self) -> None:
        # Basic emoji should be 2 columns
        assert visual_width("📦") == 2
        assert visual_width("🎉") == 2

    def test_emoji_in_text(self) -> None:
        # "📦 box" = 2 + 1 + 3 = 6
        assert visual_width("📦 box") == 6

    def test_multiple_emoji(self) -> None:
        # "✨ ✅ 🚀" = 2+1+2+1+2 = 8
        assert visual_width("✨ ✅ 🚀") == 8

    def test_ansi_escape_codes(self) -> None:
        # ANSI codes should be zero-width
        assert visual_width("\033[31mred\033[0m") == 3
        assert visual_width("\033[1m\033[36mbold cyan\033[0m") == 9

    def test_ansi_with_wide_chars(self) -> None:
        # ANSI + wide chars
        assert visual_width("\033[31m古池\033[0m") == 4

    def test_mixed_ascii_and_wide(self) -> None:
        assert visual_width("hello 古池 world") == 16

    def test_box_drawing_characters(self) -> None:
        # Box-drawing chars are narrow (1 column each)
        assert visual_width("┌──┐") == 4
        assert visual_width("│") == 1
        assert visual_width("└──┘") == 4

    def test_unicode_box_top(self) -> None:
        line = "╭────────╮"
        assert visual_width(line) == 10

    def test_tab_character(self) -> None:
        # Tabs are tricky — we count as 1 for now (terminal-dependent)
        assert visual_width("\t") == 1

    def test_variation_selector_text(self) -> None:
        # VS15 (text presentation) — should not add width
        assert visual_width("✨\ufe0e") == 1  # text presentation = narrow

    def test_combining_marks(self) -> None:
        # Combining marks are zero-width
        # é = e + combining acute accent
        assert visual_width("e\u0301") == 1


class TestVisualPad:
    """Test visual_pad() function."""

    def test_pad_left_ascii(self) -> None:
        assert visual_pad("hi", 10) == "hi        "

    def test_pad_left_wide(self) -> None:
        result = visual_pad("古池", 10)
        assert visual_width(result) == 10
        assert result == "古池      "

    def test_pad_right(self) -> None:
        assert visual_pad("hi", 10, align="right") == "        hi"

    def test_pad_center(self) -> None:
        assert visual_pad("hi", 10, align="center") == "    hi    "

    def test_pad_already_wide_enough(self) -> None:
        assert visual_pad("hello world", 5) == "hello world"

    def test_pad_with_emoji(self) -> None:
        result = visual_pad("📦", 6)
        assert visual_width(result) == 6
        assert result == "📦    "

    def test_pad_exact_width(self) -> None:
        assert visual_pad("hello", 5) == "hello"


class TestVisualTruncate:
    """Test visual_truncate() function."""

    def test_no_truncation_needed(self) -> None:
        assert visual_truncate("hi", 10) == "hi"

    def test_truncate_ascii(self) -> None:
        result = visual_truncate("hello world", 8)
        assert visual_width(result) <= 8
        assert result == "hello w…"

    def test_truncate_preserves_width(self) -> None:
        result = visual_truncate("hello world this is long", 10)
        assert visual_width(result) <= 10

    def test_truncate_with_wide_chars(self) -> None:
        result = visual_truncate("古池蛙飛込水音", 8)
        assert visual_width(result) <= 8

    def test_truncate_custom_suffix(self) -> None:
        result = visual_truncate("hello world", 8, suffix="...")
        assert visual_width(result) <= 8

    def test_truncate_zero_width(self) -> None:
        result = visual_truncate("hello", 0)
        assert result == ""

    def test_truncate_ansi_preserved(self) -> None:
        result = visual_truncate("\033[31mhello world\033[0m", 8)
        assert visual_width(result) <= 8


class TestVisualCenter:
    """Test visual_center() function."""

    def test_center_ascii(self) -> None:
        assert visual_center("hi", 10) == "    hi    "

    def test_center_odd_padding(self) -> None:
        result = visual_center("hi", 9)
        assert visual_width(result) == 9


class TestStripAnsi:
    """Test strip_ansi() function."""

    def test_strip_color(self) -> None:
        assert strip_ansi("\033[31mred\033[0m") == "red"

    def test_strip_bold(self) -> None:
        assert strip_ansi("\033[1mbold\033[0m") == "bold"

    def test_no_ansi(self) -> None:
        assert strip_ansi("plain text") == "plain text"

    def test_multiple_codes(self) -> None:
        assert strip_ansi("\033[1m\033[36mbold cyan\033[0m") == "bold cyan"
