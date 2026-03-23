"""Tests for aifmt.lib.table_fixer."""

from __future__ import annotations

from aifmt.lib.table_fixer import fix_tables
from aifmt.lib.visual_width import visual_width

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _pipe_visual_positions(line: str) -> list[int]:
    """Return the visual-column positions of every ``|`` in *line*."""
    positions: list[int] = []
    col = 0
    for ch in line:
        if ch == "|":
            positions.append(col)
        col += visual_width(ch)
    return positions


def _assert_columns_aligned(text: str) -> None:
    """Assert that pipe characters sit at the same visual columns in every row."""
    pipe_positions: list[list[int]] = []
    for line in text.split("\n"):
        if "|" not in line:
            continue
        pipe_positions.append(_pipe_visual_positions(line))

    assert len(pipe_positions) >= 2, "Expected at least 2 table rows"
    expected = pipe_positions[0]
    for idx, actual in enumerate(pipe_positions[1:], 1):
        assert actual == expected, (
            f"Row {idx} pipe positions {actual} != expected {expected}"
        )


# ---------------------------------------------------------------------------
# 1. Simple ASCII table (already aligned → no change)
# ---------------------------------------------------------------------------


class TestSimpleAsciiNoChange:
    def test_already_aligned(self):
        text = (
            "| Name  | Age |\n"
            "| ----- | --- |\n"
            "| Alice | 30  |\n"
            "| Bob   | 25  |"
        )
        fixed, changes = fix_tables(text)
        assert changes == []
        assert fixed == text

    def test_single_column(self):
        text = "| X |\n| - |\n| A |"
        fixed, changes = fix_tables(text)
        _assert_columns_aligned(fixed)


# ---------------------------------------------------------------------------
# 2. Table with emoji causing misalignment
# ---------------------------------------------------------------------------


class TestEmojiTable:
    def test_emoji_status(self):
        text = (
            "| Status | Item |\n"
            "| --- | --- |\n"
            "| ✅ | Done |\n"
            "| ❌ | Failed |"
        )
        fixed, changes = fix_tables(text)
        assert len(changes) == 1
        _assert_columns_aligned(fixed)

    def test_emoji_package(self):
        text = (
            "| Icon | Name |\n"
            "| --- | --- |\n"
            "| 📦 | Package |\n"
            "| 🚀 | Rocket |"
        )
        fixed, changes = fix_tables(text)
        assert len(changes) == 1
        _assert_columns_aligned(fixed)


# ---------------------------------------------------------------------------
# 3. Table with CJK characters
# ---------------------------------------------------------------------------


class TestCJKTable:
    def test_cjk_alignment(self):
        text = (
            "| Word | Meaning |\n"
            "| --- | --- |\n"
            "| 古池 | Old pond |\n"
            "| 蛙 | Frog |"
        )
        fixed, changes = fix_tables(text)
        assert len(changes) == 1
        _assert_columns_aligned(fixed)

    def test_mixed_cjk_and_ascii(self):
        text = (
            "| Key | Value |\n"
            "| --- | --- |\n"
            "| name | テスト |\n"
            "| id | 42 |"
        )
        fixed, changes = fix_tables(text)
        assert len(changes) == 1
        _assert_columns_aligned(fixed)


# ---------------------------------------------------------------------------
# 4. Table with alignment markers (:---:, ---:)
# ---------------------------------------------------------------------------


class TestAlignmentMarkers:
    def test_center_and_right(self):
        text = (
            "| Left | Center | Right |\n"
            "| :--- | :---: | ---: |\n"
            "| a | b | c |"
        )
        fixed, changes = fix_tables(text)
        _assert_columns_aligned(fixed)

        # Verify alignment markers are preserved in the separator
        sep_line = fixed.split("\n")[1]
        cells = [c.strip() for c in sep_line.strip().strip("|").split("|")]
        # :--- (left)
        assert cells[0].startswith(":") and not cells[0].endswith(":")
        # :---: (center)
        assert cells[1].startswith(":") and cells[1].endswith(":")
        # ---: (right)
        assert not cells[2].startswith(":") and cells[2].endswith(":")

    def test_all_center(self):
        text = (
            "| A | B |\n"
            "| :---: | :---: |\n"
            "| hello | world |"
        )
        fixed, changes = fix_tables(text)
        _assert_columns_aligned(fixed)
        sep_line = fixed.split("\n")[1]
        for cell in sep_line.strip().strip("|").split("|"):
            cell = cell.strip()
            assert cell.startswith(":") and cell.endswith(":")


# ---------------------------------------------------------------------------
# 5. Multiple tables in one text
# ---------------------------------------------------------------------------


class TestMultipleTables:
    def test_two_tables_with_prose(self):
        text = (
            "# Header\n"
            "\n"
            "| A | B |\n"
            "| --- | --- |\n"
            "| ✅ | OK |\n"
            "\n"
            "Some text here.\n"
            "\n"
            "| X | Y |\n"
            "| --- | --- |\n"
            "| 古池 | Pond |"
        )
        fixed, changes = fix_tables(text)
        assert len(changes) == 2
        assert "# Header" in fixed
        assert "Some text here." in fixed

    def test_back_to_back_tables(self):
        text = (
            "| A | B |\n"
            "| --- | --- |\n"
            "| 1 | 2 |\n"
            "| X | Y |\n"
            "| --- | --- |\n"
            "| 3 | 4 |"
        )
        fixed, changes = fix_tables(text)
        # Both tables should be processed
        assert len(changes) >= 1


# ---------------------------------------------------------------------------
# 6. Text with no tables (return unchanged)
# ---------------------------------------------------------------------------


class TestNoTables:
    def test_plain_text(self):
        text = "Hello world\nThis has no tables.\n\nJust paragraphs."
        fixed, changes = fix_tables(text)
        assert changes == []
        assert fixed == text

    def test_pipe_in_code(self):
        text = "Use `a | b` for piping."
        fixed, changes = fix_tables(text)
        assert changes == []
        assert fixed == text

    def test_empty_string(self):
        fixed, changes = fix_tables("")
        assert changes == []
        assert fixed == ""


# ---------------------------------------------------------------------------
# 7. Table with inconsistent column counts (handle gracefully)
# ---------------------------------------------------------------------------


class TestInconsistentColumns:
    def test_short_body_row(self):
        text = (
            "| A | B | C |\n"
            "| --- | --- | --- |\n"
            "| 1 | 2 |\n"
            "| 3 | 4 | 5 |"
        )
        fixed, changes = fix_tables(text)
        lines = fixed.split("\n")
        # All rows should have the same number of pipes
        pipe_counts = [line.count("|") for line in lines]
        assert len(set(pipe_counts)) == 1

    def test_extra_body_column(self):
        text = (
            "| A | B |\n"
            "| --- | --- |\n"
            "| 1 | 2 | 3 |"
        )
        fixed, changes = fix_tables(text)
        lines = fixed.split("\n")
        pipe_counts = [line.count("|") for line in lines]
        assert len(set(pipe_counts)) == 1
        _assert_columns_aligned(fixed)


# ---------------------------------------------------------------------------
# 8. Table without leading/trailing pipes
# ---------------------------------------------------------------------------


class TestNoPipeStyle:
    def test_no_outer_pipes(self):
        text = (
            "Name | Age\n"
            "--- | ---\n"
            "Alice | 30\n"
            "Bob | 25"
        )
        fixed, changes = fix_tables(text)
        lines = fixed.split("\n")
        # Should not add leading/trailing pipes
        for line in lines:
            assert not line.strip().startswith("|")
            assert not line.strip().endswith("|")
        _assert_columns_aligned(fixed)
