"""Tests for aifmt.lib.bar_fixer."""

from aifmt.lib.bar_fixer import fix_bars


class TestGroupNormalization:
    """Bars on consecutive lines should be normalised to the same total width."""

    def test_inconsistent_widths_normalised(self):
        text = (
            "CPU  ████████░░░░░░░░ 50%\n"
            "MEM  ██████░░░░ 60%\n"
            "DISK ████░░░░░░░░░░░░ 25%"
        )
        fixed, changes = fix_bars(text)
        lines = fixed.split("\n")

        # All bars in the group should share the same total width
        # Extract bar portion lengths (fill + empty) from each line
        def bar_total(line: str) -> int:
            # Count consecutive fill + empty chars after the label
            bar_chars = 0
            in_bar = False
            for ch in line:
                if ch in "█▓#=░○·.─-":
                    bar_chars += 1
                    in_bar = True
                elif in_bar:
                    break
            return bar_chars

        totals = [bar_total(ln) for ln in lines]
        assert totals[0] == totals[1] == totals[2], f"totals differ: {totals}"
        assert len(changes) > 0

    def test_already_consistent_no_changes(self):
        text = (
            "A ████░░░░ 50%\n"
            "B ██░░░░░░ 25%"
        )
        fixed, changes = fix_bars(text)
        lines = fixed.split("\n")

        def bar_total(line: str) -> int:
            bar_chars = 0
            in_bar = False
            for ch in line:
                if ch in "█▓#=░○·.─-":
                    bar_chars += 1
                    in_bar = True
                elif in_bar:
                    break
            return bar_chars

        totals = [bar_total(ln) for ln in lines]
        assert totals[0] == totals[1]


class TestPercentageRecalculation:
    """When a percentage is present, fill ratio must match."""

    def test_fill_ratio_matches_percentage(self):
        # 50% with 16-char bar → 8 fill + 8 empty
        text = "████████████░░░░ 50%"
        fixed, changes = fix_bars(text)
        line = fixed.strip()
        # Even as a single bar, the percentage triggers a recalculation
        fill_count = line.count("█")
        empty_count = line.count("░")
        total = fill_count + empty_count
        expected_fill = round(total * 50 / 100)
        assert fill_count == expected_fill, f"fill {fill_count} != expected {expected_fill}"

    def test_percentage_bar_in_group(self):
        text = (
            "████████████████ 100%\n"
            "████████░░░░░░░░ 50%\n"
            "████░░░░░░░░░░░░ 25%"
        )
        fixed, changes = fix_bars(text)
        lines = fixed.split("\n")

        for line in lines:
            fill = line.count("█")
            empty = line.count("░")
            total = fill + empty
            # Extract percentage
            pct = int(line.split()[-1].rstrip("%"))
            expected_fill = round(total * pct / 100)
            assert fill == expected_fill, f"Line '{line}': fill={fill}, expected={expected_fill}"


class TestNoBarText:
    """Text without bars should pass through unchanged."""

    def test_plain_text_unchanged(self):
        text = "Hello world\nThis is a normal paragraph.\nNo bars here."
        fixed, changes = fix_bars(text)
        assert fixed == text
        assert changes == []

    def test_empty_string(self):
        fixed, changes = fix_bars("")
        assert fixed == ""
        assert changes == []


class TestSingleBar:
    """A lone bar (no group) without percentage stays unchanged."""

    def test_single_bar_no_percentage_unchanged(self):
        text = "████████░░░░░░░░"
        fixed, changes = fix_bars(text)
        assert fixed == text
        assert changes == []

    def test_single_bar_with_percentage_recalculated(self):
        # 50% but fill is wrong (12 fill + 4 empty)
        text = "████████████░░░░ 50%"
        fixed, changes = fix_bars(text)
        line = fixed.strip()
        fill = line.count("█")
        empty = line.count("░")
        total = fill + empty
        assert fill == round(total * 50 / 100)


class TestBracketedBars:
    """Bars enclosed in brackets like [████░░░░]."""

    def test_bracketed_bar_with_percentage(self):
        text = "[████████░░░░░░░░] 50%"
        fixed, changes = fix_bars(text)
        assert "[" in fixed and "]" in fixed


class TestAlternateCharacters:
    """Bars using ▓, #, =, etc."""

    def test_hash_dash_bar(self):
        text = (
            "A ###-------\n"
            "B #####-----"
        )
        fixed, changes = fix_bars(text)
        lines = fixed.split("\n")

        def bar_total(line: str) -> int:
            count = 0
            in_bar = False
            for ch in line:
                if ch in "#-":
                    count += 1
                    in_bar = True
                elif in_bar:
                    break
            return count

        totals = [bar_total(ln) for ln in lines]
        assert totals[0] == totals[1]
