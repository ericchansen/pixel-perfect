"""Tests for aifmt.lib.table_fixer."""

from __future__ import annotations

import pytest

from aifmt.lib.table_fixer import fix_tables


class TestSimpleAsciiTable:
    """Simple ASCII table that is already aligned."""

    correct = """\
| Name  | Age |
| ----- | --- |
| Alice | 30  |
| Bob   | 25  |"""

    def test_already_aligned(self) -> None:
        fixed, changes = fix_tables(self.correct)
        assert fixed == self.correct
        assert changes == []


class TestSingleColumnTable:
    """Single-column table."""

    correct = """\
| X   |
| --- |
| A   |"""

    def test_single_column(self) -> None:
        broken = "| X |\n| - |\n| A |"
        fixed, _changes = fix_tables(broken)
        assert fixed == self.correct


@pytest.mark.parametrize(
    ("target", "correct"),
    [
        (
            "terminal",
            """\
| Status | Item   |
| ------ | ------ |
| ✅✅   | Done   |
| ❌❌   | Failed |""",
        ),
        pytest.param(
            "github",
            """\
| Status | Item   |
| ------ | ------ |
| ✅✅  | Done   |
| ❌❌  | Failed |""",
            marks=pytest.mark.skip(reason="needs human verification on GitHub"),
        ),
    ],
)
class TestEmojiStatusTable:
    """Table with emoji in status column."""

    # TODO: Impossible to view correctly in VS Code unless 2x emojis used.

    def test_emoji_status_misaligned(self, target: str, correct: str) -> None:
        broken = "| Status | Item |\n| --- | --- |\n| ✅✅ | Done |\n| ❌❌ | Failed |"
        fixed, _changes = fix_tables(broken, target=target)
        assert fixed == correct

    def test_already_correct(self, target: str, correct: str) -> None:
        fixed, _changes = fix_tables(correct, target=target)
        assert fixed == correct


@pytest.mark.parametrize(
    ("target", "correct"),
    [
        (
            "terminal",
            """\
| Icon | Name    |
| ---- | ------- |
| 📦📦 | Package |
| 🚀🚀 | Rocket  |""",
        ),
        pytest.param(
            "github",
            """\
| Icon  | Name    |
| ----- | ------- |
| 📦📦 | Package |
| 🚀🚀 | Rocket  |""",
            marks=pytest.mark.skip(reason="needs human verification on GitHub"),
        ),
    ],
)
class TestEmojiPackageTable:
    """Table with emoji in icon column."""

    # TODO: Impossible to view correctly in VS Code unless 2x emojis used.

    def test_emoji_package_misaligned(self, target: str, correct: str) -> None:
        broken = "| Icon | Name |\n| --- | --- |\n| 📦📦 | Package |\n| 🚀🚀 | Rocket |"
        fixed, _changes = fix_tables(broken, target=target)
        assert fixed == correct

    def test_already_correct(self, target: str, correct: str) -> None:
        fixed, _changes = fix_tables(correct, target=target)
        assert fixed == correct


class TestCJKAlignmentTable:
    """Table with CJK characters requiring double-width padding."""

    # TODO: Don't know how to do this.
    ...


class TestMixedCJKAsciiTable:
    """Table with mixed CJK and ASCII content."""

    # TODO: Don't know how to do this.
    ...


class TestCenterAndRightAlignedTable:
    """Table with center (:---:) and right (---:) alignment markers."""

    correct = """\
| Left | Center | Right |
| :--- | :----: | ----: |
| a    | b      | c     |"""

    def test_center_and_right(self) -> None:
        broken = "| Left | Center | Right |\n| :--- | :---: | ---: |\n| a | b | c |"
        fixed, _changes = fix_tables(broken)
        assert fixed == self.correct


class TestAllCenterAlignedTable:
    """Table with all center-aligned columns."""

    correct = """\
| A     | B     |
| :---: | :---: |
| hello | world |"""

    def test_all_center(self) -> None:
        broken = "| A | B |\n| :---: | :---: |\n| hello | world |"
        fixed, _changes = fix_tables(broken)
        assert fixed == self.correct


class TestBackToBackTables:
    """Two tables with no gap between them."""

    correct = """\
| A   | B   |
| --- | --- |
| 1   | 2   |
| X   | Y   |
| --- | --- |
| 3   | 4   |"""

    def test_back_to_back(self) -> None:
        broken = "| A | B |\n| --- | --- |\n| 1 | 2 |\n| X | Y |\n| --- | --- |\n| 3 | 4 |"
        fixed, changes = fix_tables(broken)
        assert fixed == self.correct
        assert len(changes) == 2


class TestNoTables:
    """Text without tables passes through unchanged."""

    def test_plain_text(self) -> None:
        text = "Hello world\nThis has no tables.\n\nJust paragraphs."
        fixed, changes = fix_tables(text)
        assert fixed == text
        assert changes == []

    def test_pipe_in_code(self) -> None:
        text = "Use `a | b` for piping."
        fixed, changes = fix_tables(text)
        assert fixed == text
        assert changes == []

    def test_empty_string(self) -> None:
        fixed, changes = fix_tables("")
        assert fixed == ""
        assert changes == []


class TestShortBodyRow:
    """Table with a body row that has fewer columns than header."""

    correct = """\
| A   | B   | C   |
| --- | --- | --- |
| 1   | 2   |     |
| 3   | 4   | 5   |"""

    def test_short_row_padded(self) -> None:
        broken = "| A | B | C |\n| --- | --- | --- |\n| 1 | 2 |\n| 3 | 4 | 5 |"
        fixed, _changes = fix_tables(broken)
        assert fixed == self.correct


class TestExtraBodyColumn:
    """Table with a body row that has more columns than header."""

    correct = """\
| A   | B   |     |
| --- | --- | --- |
| 1   | 2   | 3   |"""

    def test_extra_column_absorbed(self) -> None:
        broken = "| A | B |\n| --- | --- |\n| 1 | 2 | 3 |"
        fixed, _changes = fix_tables(broken)
        assert fixed == self.correct


class TestNoPipeStyleTable:
    """Table without leading/trailing pipes."""

    correct = """\
 Name  | Age 
 ----- | --- 
 Alice | 30  
 Bob   | 25  """

    def test_no_outer_pipes(self) -> None:
        broken = "Name | Age\n--- | ---\nAlice | 30\nBob | 25"
        fixed, _changes = fix_tables(broken)
        assert fixed == self.correct
