"""Tests for aifmt.lib.mermaid_validator."""

from aifmt.lib.mermaid_validator import validate_mermaid


class TestValidDiagrams:
    """Valid mermaid blocks should produce no issues."""

    def test_valid_flowchart(self):
        text = (
            "```mermaid\n"
            "flowchart LR\n"
            "  A[Start] --> B[End]\n"
            "```"
        )
        issues = validate_mermaid(text)
        assert issues == []

    def test_valid_sequence_diagram(self):
        text = (
            "```mermaid\n"
            "sequenceDiagram\n"
            "  Alice->>Bob: Hello\n"
            "  Bob-->>Alice: Hi\n"
            "```"
        )
        issues = validate_mermaid(text)
        assert issues == []

    def test_valid_graph(self):
        text = (
            "```mermaid\n"
            "graph TD\n"
            "  A --> B\n"
            "  B --> C\n"
            "```"
        )
        issues = validate_mermaid(text)
        assert issues == []


class TestEmptyBlock:
    """Empty mermaid blocks should produce an error."""

    def test_empty_block(self):
        text = "```mermaid\n```"
        issues = validate_mermaid(text)
        assert len(issues) == 1
        assert issues[0].severity == "error"
        assert "empty" in issues[0].message.lower()

    def test_whitespace_only_block(self):
        text = "```mermaid\n   \n  \n```"
        issues = validate_mermaid(text)
        assert any("empty" in i.message.lower() for i in issues)


class TestMissingDiagramType:
    """A block with content but no valid diagram type → error."""

    def test_missing_type(self):
        text = (
            "```mermaid\n"
            "  A --> B\n"
            "  B --> C\n"
            "```"
        )
        issues = validate_mermaid(text)
        assert len(issues) >= 1
        type_issues = [
            i for i in issues
            if "diagram type" in i.message.lower() or "unrecognised" in i.message.lower()
        ]
        assert len(type_issues) >= 1
        assert type_issues[0].severity == "error"


class TestUnclosedBracket:
    """Unclosed brackets should be flagged as errors."""

    def test_unclosed_square_bracket(self):
        text = (
            "```mermaid\n"
            "flowchart LR\n"
            "  A[Start --> B[End]\n"
            "```"
        )
        issues = validate_mermaid(text)
        bracket_issues = [
            i for i in issues
            if "unclosed" in i.message.lower() or "unexpected" in i.message.lower()
        ]
        assert len(bracket_issues) >= 1

    def test_unclosed_curly_brace(self):
        text = (
            "```mermaid\n"
            "flowchart LR\n"
            "  A{Decision --> B[End]\n"
            "```"
        )
        issues = validate_mermaid(text)
        bracket_issues = [
            i for i in issues
            if "unclosed" in i.message.lower() or "unexpected" in i.message.lower()
        ]
        assert len(bracket_issues) >= 1


class TestNoMermaidBlocks:
    """Text with no mermaid blocks should produce no issues."""

    def test_plain_text(self):
        issues = validate_mermaid("Just some text.\nNothing special here.")
        assert issues == []

    def test_other_code_blocks(self):
        text = "```python\nprint('hello')\n```"
        issues = validate_mermaid(text)
        assert issues == []


class TestMultipleBlocks:
    """Multiple mermaid blocks: one valid, one invalid."""

    def test_mixed_valid_invalid(self):
        text = (
            "Some text\n"
            "```mermaid\n"
            "flowchart LR\n"
            "  A[Start] --> B[End]\n"
            "```\n"
            "\n"
            "More text\n"
            "```mermaid\n"
            "  X[Oops --> Y\n"
            "```\n"
        )
        issues = validate_mermaid(text)
        # The second block has missing diagram type AND unclosed bracket
        assert len(issues) >= 1

    def test_both_valid(self):
        text = (
            "```mermaid\n"
            "flowchart LR\n"
            "  A --> B\n"
            "```\n"
            "\n"
            "```mermaid\n"
            "sequenceDiagram\n"
            "  Alice->>Bob: Hi\n"
            "```\n"
        )
        issues = validate_mermaid(text)
        assert issues == []
