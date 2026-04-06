"""Tests for aifmt.lib.bar_fixer."""

from aifmt.lib.bar_fixer import fix_bars


class TestBarGroupNormalization:
    """Bars on consecutive lines should be normalised to the same total width."""

    correct = """\
CPU  ████████░░░░░░░░ 50%
MEM  ██████████░░░░░░ 60%
DISK ████░░░░░░░░░░░░ 25%"""

    def test_inconsistent_widths_normalised(self) -> None:
        broken = """\
CPU  ████████░░░░░░░░ 50%
MEM  ██████░░░░ 60%
DISK ████░░░░░░░░░░░░ 25%"""
        fixed, changes = fix_bars(broken)
        assert fixed == self.correct
        assert len(changes) > 0

    def test_already_correct_unchanged(self) -> None:
        fixed, changes = fix_bars(self.correct)
        assert fixed == self.correct
        assert changes == []


class TestBarSingleWithPercentage:
    """Single bar with percentage — fill ratio corrected to match."""

    correct = "████████░░░░░░░░ 50%"

    def test_fill_ratio_corrected(self) -> None:
        broken = "████████████░░░░ 50%"
        fixed, _changes = fix_bars(broken)
        assert fixed == self.correct


class TestBarPercentageGroup:
    """Group of bars with percentages — all already correct."""

    correct = """\
████████████████ 100%
████████░░░░░░░░ 50%
████░░░░░░░░░░░░ 25%"""

    def test_percentage_group_unchanged(self) -> None:
        fixed, changes = fix_bars(self.correct)
        assert fixed == self.correct
        assert changes == []


class TestNoBarText:
    """Text without bars passes through unchanged."""

    def test_plain_text_unchanged(self) -> None:
        text = "Hello world\nThis is a normal paragraph.\nNo bars here."
        fixed, changes = fix_bars(text)
        assert fixed == text
        assert changes == []

    def test_empty_string(self) -> None:
        fixed, changes = fix_bars("")
        assert fixed == ""
        assert changes == []


class TestSingleBarNoPercentage:
    """A lone bar without percentage stays unchanged."""

    correct = "████████░░░░░░░░"

    def test_single_bar_unchanged(self) -> None:
        fixed, changes = fix_bars(self.correct)
        assert fixed == self.correct
        assert changes == []


class TestBracketedBar:
    """Bars enclosed in brackets like [████░░░░]."""

    correct = "[████████░░░░░░░░] 50%"

    def test_bracketed_unchanged(self) -> None:
        fixed, _changes = fix_bars(self.correct)
        assert fixed == self.correct


class TestHashDashBars:
    """Bars using # and - characters."""

    correct = """\
A ###-------
B #####-----"""

    def test_hash_bars_unchanged(self) -> None:
        fixed, _changes = fix_bars(self.correct)
        assert fixed == self.correct
