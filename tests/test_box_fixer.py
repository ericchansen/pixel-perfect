"""Tests for box_fixer module."""

from aifmt.lib.box_fixer import fix_boxes
from aifmt.lib.visual_width import visual_width


class TestSimpleAsciiBox:
    """Test fixing simple ASCII boxes with +, -, | characters."""

    def test_misaligned_right_border(self):
        broken = (
            "+-------------------+\n"
            "| User Request       |\n"
            "+-------------------+\n"
        )
        fixed, changes = fix_boxes(broken)
        assert len(changes) > 0
        # All lines should have the same visual width
        lines = [ln for ln in fixed.split("\n") if ln.strip()]
        widths = [visual_width(ln.strip()) for ln in lines]
        assert len(set(widths)) == 1, f"Widths not uniform: {widths}"

    def test_right_border_too_close(self):
        broken = (
            "+-------------------+\n"
            "| Parse & Validate |  \n"
            "+-------------------+\n"
        )
        fixed, changes = fix_boxes(broken)
        lines = [ln for ln in fixed.split("\n") if ln.strip()]
        widths = [visual_width(ln.strip()) for ln in lines]
        assert len(set(widths)) == 1

    def test_already_aligned(self):
        correct = (
            "+-------------------+\n"
            "| User Request      |\n"
            "+-------------------+\n"
        )
        fixed, changes = fix_boxes(correct)
        # Should detect the box but make no changes (or minimal)
        lines_orig = [ln for ln in correct.split("\n") if ln.strip()]
        lines_fixed = [ln for ln in fixed.split("\n") if ln.strip()]
        for orig, fix in zip(lines_orig, lines_fixed):
            assert visual_width(orig.strip()) == visual_width(fix.strip())


class TestUnicodeBox:
    """Test fixing Unicode box-drawing character boxes."""

    def test_unicode_misaligned(self):
        broken = (
            "┌──────────┐\n"
            "│ Hello     │\n"
            "│ World    │\n"
            "└──────────┘\n"
        )
        fixed, changes = fix_boxes(broken)
        lines = [ln for ln in fixed.split("\n") if ln.strip()]
        widths = [visual_width(ln.strip()) for ln in lines]
        assert len(set(widths)) == 1

    def test_rounded_corners(self):
        broken = (
            "╭──────────╮\n"
            "│ Content   │\n"
            "╰──────────╯\n"
        )
        fixed, changes = fix_boxes(broken)
        lines = [ln for ln in fixed.split("\n") if ln.strip()]
        widths = [visual_width(ln.strip()) for ln in lines]
        assert len(set(widths)) == 1


class TestStackedBoxes:
    """Test fixing stacked boxes (multiple boxes vertically)."""

    def test_two_stacked(self):
        broken = (
            "+----------+\n"
            "| Box One   |\n"
            "+----------+\n"
            "| Box Two  |\n"
            "+----------+\n"
        )
        fixed, changes = fix_boxes(broken)
        lines = [ln for ln in fixed.split("\n") if ln.strip()]
        widths = [visual_width(ln.strip()) for ln in lines]
        # All lines in both boxes should align
        assert max(widths) - min(widths) <= 0, f"Widths: {widths}"


class TestEmojiInBox:
    """Test boxes with emoji content (where len() != visual_width)."""

    def test_emoji_content(self):
        broken = (
            "┌──────────────┐\n"
            "│ 📦 Package    │\n"
            "│ ✅ Complete  │\n"
            "└──────────────┘\n"
        )
        fixed, changes = fix_boxes(broken)
        lines = [ln for ln in fixed.split("\n") if ln.strip()]
        widths = [visual_width(ln.strip()) for ln in lines]
        assert len(set(widths)) == 1, f"Widths not uniform: {widths}"


class TestNoBoxes:
    """Test that text without boxes passes through unchanged."""

    def test_plain_text(self):
        text = "Hello world\nThis is just text\nNo boxes here"
        fixed, changes = fix_boxes(text)
        assert fixed == text
        assert changes == []

    def test_empty_string(self):
        fixed, changes = fix_boxes("")
        assert fixed == ""
        assert changes == []

    def test_single_pipe(self):
        text = "| not a box |"
        fixed, changes = fix_boxes(text)
        assert fixed == text
        assert changes == []


class TestIndentedBox:
    """Test boxes with leading whitespace."""

    def test_indented(self):
        broken = (
            "    ┌──────────┐\n"
            "    │ Content   │\n"
            "    └──────────┘\n"
        )
        fixed, changes = fix_boxes(broken)
        lines = [ln for ln in fixed.split("\n") if ln.strip()]
        # Check indentation is preserved
        for line in lines:
            assert line.startswith("    ")
        # Check alignment
        widths = [visual_width(ln.strip()) for ln in lines]
        assert len(set(widths)) == 1
