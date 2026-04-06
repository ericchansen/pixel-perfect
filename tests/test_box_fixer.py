"""Tests for box_fixer module."""

import pytest

from aifmt.lib.box_fixer import fix_boxes


class TestSimpleAsciiBox:
    """Test fixing simple ASCII boxes with +, -, | characters."""

    correct = """\
+--------------+
| User Request |
+--------------+
"""

    def test_right_border_too_far(self) -> None:
        broken = """\
+--------------+
| User Request  |
+--------------+
"""
        fixed, _changes = fix_boxes(broken)
        assert fixed == self.correct

    def test_right_border_too_close(self) -> None:
        broken = """\
+---------------+
| User Request |
+---------------+
"""
        fixed, _changes = fix_boxes(broken)
        assert fixed == self.correct

    def test_already_aligned(self) -> None:
        fixed, _changes = fix_boxes(self.correct)
        assert fixed == self.correct


class TestUnicodeBox:
    """Test fixing Unicode box-drawing character boxes."""

    correct = """\
┌─────────┐
│ Hello   │
│ World   │
└─────────┘
"""

    def test_unicode_misaligned(self) -> None:
        broken = """\
┌──────────┐
│ Hello     │
│ World    │
└──────────┘
"""
        fixed, _changes = fix_boxes(broken)
        assert fixed == self.correct


class TestRoundedCornerBox:
    """Test fixing rounded-corner Unicode boxes (╭╮╰╯)."""

    correct = """\
╭─────────╮
│ Content │
╰─────────╯
"""

    def test_rounded_misaligned(self) -> None:
        broken = """\
╭─────────╮
│ Content  │
╰─────────╯
"""
        fixed, _changes = fix_boxes(broken)
        assert fixed == self.correct


class TestStackedBoxes:
    """Test fixing stacked boxes (multiple boxes vertically)."""

    correct = """\
+---------+
| Box One |
+---------+
| Box Two |
+---------+
"""

    def test_two_stacked(self) -> None:
        broken = """\
+----------+
| Box One   |
+----------+
| Box Two  |
+----------+
"""
        fixed, _changes = fix_boxes(broken)
        assert fixed == self.correct


@pytest.mark.parametrize(
    ("target", "correct"),
    [
        (
            "terminal",
            """\
┌──────────────┐
│ 📦📦 Package │
│ ✅✅ Complete │
└──────────────┘
""",
        ),
        (
            "github",
            """\
┌──────────────┐
│ 📦📦 Package │
│ ✅✅ Complete │
└──────────────┘
""",
        ),
    ],
)
class TestEmojiInBox:
    """Test boxes with emoji content (where len() != visual_width)."""

    # TODO: For visuals within VS Code GUI, can't be correct unless 2 emojis are used.

    def test_emoji_misaligned(self, target: str, correct: str) -> None:
        broken = """\
┌──────────────┐
│ 📦📦 Package    │
│ ✅✅ Complete  │
└──────────────┘
"""
        fixed, _changes = fix_boxes(broken, target=target)
        assert fixed == correct

    def test_already_correct(self, target: str, correct: str) -> None:
        fixed, _changes = fix_boxes(correct, target=target)
        assert fixed == correct


class TestNoBoxes:
    """Test that text without boxes passes through unchanged."""

    def test_plain_text(self) -> None:
        text = "Hello world\nThis is just text\nNo boxes here"
        fixed, changes = fix_boxes(text)
        assert fixed == text
        assert changes == []

    def test_empty_string(self) -> None:
        fixed, changes = fix_boxes("")
        assert fixed == ""
        assert changes == []

    def test_single_pipe(self) -> None:
        text = "| not a box |"
        fixed, changes = fix_boxes(text)
        assert fixed == text
        assert changes == []


class TestIndentedBox:
    """Test boxes with leading whitespace."""

    correct = """\
    ┌───────────┐
    │ Content   │
    └───────────┘
"""

    def test_indented(self) -> None:
        broken = """\
    ┌──────────┐
    │ Content   │
    └──────────┘
"""
        fixed, _changes = fix_boxes(broken)
        assert fixed == self.correct


class TestNestedBox:
    """Box containing a nested box — borders should align."""

    correct = """\
┌──────────────────────────────────────────────────────────┐
│                    DATA PIPELINE                         │
│                                                          │
│                                    ┌───────────┐         │
│                                    │ Chunking  │         │
│                                    │ Enrichment│         │
│                                    └───────────┘         │
│                                                          │
└──────────────────────────────────────────────────────────┘"""

    def test_nested_box_fixed(self) -> None:
        broken = """\
┌──────────────────────────────────────────────────────────┐
│                    DATA PIPELINE                         │
│                                                          │
│                                    ┌─────────┐           │
│                                    │ Chunking │           │
│                                    │ Enrichment│          │
│                                    └─────────┘           │
│                                                          │
└──────────────────────────────────────────────────────────┘"""
        fixed, _changes = fix_boxes(broken)
        assert fixed == self.correct

    def test_already_correct(self) -> None:
        fixed, changes = fix_boxes(self.correct)
        assert fixed == self.correct
        assert changes == []


class TestFullReproBox:
    """Two large boxes with nested boxes — full reproduction from issue."""

    # TODO: Impossible in VS Code UI due to arrows.
    correct = """\
┌───────────────────────────────────────────────────────────┐
│                    DATA PIPELINE                          │
│                                                           │
│  S3/GCS Docs ──▶ Fabric OneLake ──▶ Azure Blob/ADLS      │
│                     (shortcut)          │                 │
│                                         ▼                 │
│                                  AI Search Indexer        │
│                                    ┌───────────┐          │
│                                    │ Chunking  │          │
│                                    │ Enrichment│          │
│                                    │ Embedding │          │
│                                    └───────────┘          │
│                                         │                 │
│                                         ▼                 │
│                                  Search Index             │
│                              (vectors + text + metadata)  │
└───────────────────────────────────────────────────────────┘

┌───────────────────────────────────────────────────────────┐
│                    QUERY PIPELINE                         │
│                                                           │
│  User Query ──▶ Orchestrator ──▶ Azure AI Search         │
│                 (Semantic Kernel,   │                     │
│                  Agent Framework)   ▼                     │
│                              Hybrid Search                │
│                        (keyword + vector + semantic rank) │
│                                    │                      │
│                                    ▼                      │
│                              Top-K Results                │
│                                    │                      │
│                                    ▼                      │
│                              LLM (GPT-4o)                 │
│                              ──▶ Answer + Citations      │
└───────────────────────────────────────────────────────────┘"""

    def test_full_repro_fixed(self) -> None:
        broken = """\
┌──────────────────────────────────────────────────────────┐
│                    DATA PIPELINE                         │
│                                                          │
│  S3/GCS Docs ──▶ Fabric OneLake ──▶ Azure Blob/ADLS    │
│                     (shortcut)          │                │
│                                         ▼                │
│                                  AI Search Indexer        │
│                                    ┌─────────┐           │
│                                    │ Chunking │           │
│                                    │ Enrichment│          │
│                                    │ Embedding │          │
│                                    └─────────┘           │
│                                         │                │
│                                         ▼                │
│                                  Search Index            │
│                              (vectors + text + metadata) │
└──────────────────────────────────────────────────────────┘

┌──────────────────────────────────────────────────────────┐
│                    QUERY PIPELINE                         │
│                                                          │
│  User Query ──▶ Orchestrator ──▶ Azure AI Search         │
│                 (Semantic Kernel,   │                     │
│                  Agent Framework)   ▼                     │
│                              Hybrid Search               │
│                        (keyword + vector + semantic rank) │
│                                    │                     │
│                                    ▼                     │
│                              Top-K Results               │
│                                    │                     │
│                                    ▼                     │
│                              LLM (GPT-4o)                │
│                              ──▶ Answer + Citations      │
└──────────────────────────────────────────────────────────┘"""
        fixed, _changes = fix_boxes(broken)
        assert fixed == self.correct

    def test_already_correct(self) -> None:
        fixed, changes = fix_boxes(self.correct)
        assert fixed == self.correct
        assert changes == []


class TestAsciiBoxTight:
    """ASCII box with tight-fitting borders."""

    correct = """\
+-------+
| hello |
| world |
+-------+"""

    def test_ascii_box_fixed(self) -> None:
        broken = """\
+-------+
| hello  |
| world |
+-------+"""
        fixed, _changes = fix_boxes(broken)
        assert fixed == self.correct

    def test_already_correct(self) -> None:
        fixed, changes = fix_boxes(self.correct)
        assert fixed == self.correct
        assert changes == []
