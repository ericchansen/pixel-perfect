"""Tests for the tree diagram fixer.

The tree fixer parses misaligned tree diagrams into a node model,
then re-renders them with correct ├──/└──/│ alignment.
"""

from aifmt.lib.tree_fixer import fix_trees


class TestTreeDetection:
    """Test that tree regions are correctly identified in text."""

    def test_simple_tree_detected(self):
        tree = "Root\n  ├── Child A\n  └── Child B"
        _, changes = fix_trees(tree)
        assert isinstance(changes, list)

    def test_non_tree_content_ignored(self):
        text = "This is a paragraph.\nNo tree characters.\nNothing to fix."
        _, changes = fix_trees(text)
        assert len(changes) == 0

    def test_single_pipe_not_a_tree(self):
        text = "Use | for pipes in bash"
        _, changes = fix_trees(text)
        assert len(changes) == 0


class TestCorrectTrees:
    """Correctly-structured trees should produce zero changes."""

    def test_simple_two_children(self):
        tree = "Root\n├── Child A\n└── Child B"
        fixed, changes = fix_trees(tree)
        assert len(changes) == 0
        assert fixed == tree

    def test_nested_tree(self):
        tree = (
            "Root\n"
            "├── Parent\n"
            "│   ├── Child A\n"
            "│   └── Child B\n"
            "└── Sibling"
        )
        fixed, changes = fix_trees(tree)
        assert len(changes) == 0
        assert fixed == tree

    def test_deep_nesting(self):
        tree = (
            "Root\n"
            "├── Level 1\n"
            "│   ├── Level 2\n"
            "│   │   └── Level 3\n"
            "│   └── Level 2b\n"
            "└── Level 1b"
        )
        fixed, changes = fix_trees(tree)
        assert len(changes) == 0
        assert fixed == tree


class TestMisalignedPipes:
    """Trees with pipe columns that don't match branch columns."""

    def test_pipe_misaligned_gets_fixed(self):
        """Pipe at wrong column should be realigned."""
        tree = (
            "Root\n"
            "  ├── Parent\n"
            "  │              │\n"
            "  │    ├── Child A\n"
            "  │    │\n"
            "  │    └── Child B\n"
            "  └── Sibling"
        )
        fixed, changes = fix_trees(tree)
        assert len(changes) >= 1

        lines = fixed.split("\n")
        assert lines[0] == "Root"
        assert "├── Parent" in lines[1]
        assert "├── Child A" in fixed
        assert "└── Child B" in fixed
        assert "└── Sibling" in fixed

    def test_pipe_aligned_no_changes(self):
        """Pipe correctly aligned → no changes needed."""
        tree = (
            "Root\n"
            "├── Parent\n"
            "│   ├── Child A\n"
            "│   └── Child B\n"
            "└── Sibling"
        )
        fixed, changes = fix_trees(tree)
        assert len(changes) == 0


class TestOrphanedContent:
    """Content lines without tree connectors get connectors added."""

    def test_orphaned_child_gets_connector(self):
        """Content under a pipe without ├/└ should get a connector."""
        tree = (
            "Root\n"
            "  ├── Parent\n"
            "  │     │\n"
            "  │     Orphaned Child\n"
            "  └── Sibling"
        )
        fixed, changes = fix_trees(tree)
        assert len(changes) >= 1
        # The orphaned child should now have a proper connector
        assert "Orphaned Child" in fixed
        assert "└── Orphaned Child" in fixed or "├── Orphaned Child" in fixed

    def test_multiple_orphans_get_connectors(self):
        tree = (
            "Root\n"
            "  ├── Parent\n"
            "  │     │\n"
            "  │     Orphan A\n"
            "  │     │\n"
            "  │     Orphan B\n"
            "  └── Sibling"
        )
        fixed, changes = fix_trees(tree)
        assert len(changes) >= 1
        assert "├── Orphan A" in fixed
        assert "└── Orphan B" in fixed


class TestContinuationText:
    """Non-tree continuation lines stay as continuations."""

    def test_continuation_preserved(self):
        """Lines without any tree chars are continuations, not children."""
        tree = (
            "Root\n"
            "└── 16 Skills ──▶ skills/report/\n"
            "    skills/explorer/\n"
            "    skills/impact/"
        )
        fixed, changes = fix_trees(tree)
        assert "skills/explorer/" in fixed
        assert "skills/impact/" in fixed
        # Should NOT have ├── or └── before continuation paths
        lines = fixed.split("\n")
        for line in lines:
            if "skills/explorer/" in line or "skills/impact/" in line:
                assert "├──" not in line and "└──" not in line

    def test_parenthetical_is_continuation(self):
        """Text starting with '(' is continuation of previous node."""
        tree = (
            "Root\n"
            "  ├── MSX D365 Sales\n"
            "  │   (sales.crm.dynamics.com)\n"
            "  └── Other"
        )
        fixed, changes = fix_trees(tree)
        lines = fixed.split("\n")
        # Find the parenthetical line
        paren_lines = [ln for ln in lines if "(sales.crm" in ln]
        assert len(paren_lines) == 1
        # Should NOT have a connector
        assert "├── (sales" not in fixed and "└── (sales" not in fixed


class TestMsxMcpDiagram:
    """Integration test using the real MSX-MCP README architecture diagram."""

    MSX_TREE = (
        "GitHub Copilot CLI\n"
        "  │\n"
        "  ├── stdio ──▶ MSX MCP Server (TypeScript, 37 tools)\n"
        "  │                    │\n"
        "  │             ├── Auth Tools (msx_login, msx_auth_status)\n"
        "  │             │        │\n"
        "  │             │    Azure CLI (az login)\n"
        "  │             │\n"
        "  │             └── Data Tools (35 tools)\n"
        "  │                      │\n"
        "  │               Dataverse Web API (OData v4)\n"
        "  │                      │\n"
        "  │               MSX D365 Sales\n"
        "  │               (sales.crm.dynamics.com)\n"
        "  │\n"
        "  ├── @msx Agent ──▶ agents/msx.agent.md\n"
        "  │\n"
        "  └── 16 Skills ──▶ skills/monthly-opportunity-report/"
    )

    def test_fixes_structure(self):
        """The fixer should produce a valid tree from the broken MSX diagram."""
        fixed, changes = fix_trees(self.MSX_TREE, target="github")
        assert len(changes) >= 1

    def test_preserves_all_content(self):
        """All meaningful content from the original should appear in the fix."""
        fixed, _ = fix_trees(self.MSX_TREE, target="github")
        for content in [
            "GitHub Copilot CLI",
            "stdio",
            "MSX MCP Server",
            "Auth Tools",
            "Azure CLI",
            "Data Tools",
            "Dataverse Web API",
            "MSX D365 Sales",
            "(sales.crm.dynamics.com)",
            "@msx Agent",
            "16 Skills",
        ]:
            assert content in fixed, f"Missing content: {content}"

    def test_correct_hierarchy(self):
        """The fixed tree should have correct parent-child relationships."""
        fixed, _ = fix_trees(self.MSX_TREE, target="github")
        lines = fixed.split("\n")

        # Root
        assert lines[0] == "GitHub Copilot CLI"

        # Top-level children use ├── or └──
        top_children = [ln for ln in lines if ln.startswith("├── ") or ln.startswith("└── ")]
        labels = [ln.split("── ", 1)[1] for ln in top_children]
        assert any("stdio" in lb for lb in labels)
        assert any("@msx Agent" in lb for lb in labels)
        assert any("16 Skills" in lb for lb in labels)

    def test_auth_tools_under_stdio(self):
        """Auth Tools should be a child of stdio, not at root level."""
        fixed, _ = fix_trees(self.MSX_TREE, target="github")
        lines = fixed.split("\n")
        for line in lines:
            if "Auth Tools" in line:
                # Should be indented (not at column 0)
                assert line.startswith("│") or line.startswith("    "), (
                    f"Auth Tools should be nested: {line}"
                )
                break

    def test_azure_cli_under_auth_tools(self):
        """Azure CLI should be a child of Auth Tools."""
        fixed, _ = fix_trees(self.MSX_TREE, target="github")
        lines = fixed.split("\n")
        for i, line in enumerate(lines):
            if "Azure CLI" in line:
                assert "└── Azure CLI" in line, (
                    f"Azure CLI should have └── connector: {line}"
                )
                break

    def test_dataverse_under_data_tools(self):
        """Dataverse Web API should be a child of Data Tools."""
        fixed, _ = fix_trees(self.MSX_TREE, target="github")
        lines = fixed.split("\n")
        data_idx = next(i for i, ln in enumerate(lines) if "Data Tools" in ln)
        dv_idx = next(i for i, ln in enumerate(lines) if "Dataverse" in ln)
        assert dv_idx > data_idx
        # Dataverse line should be longer (deeper prefix) than Data Tools
        dv_line = lines[dv_idx]
        assert "├── Dataverse" in dv_line or "└── Dataverse" in dv_line

    def test_sales_continuation(self):
        """(sales.crm.dynamics.com) should be continuation of MSX D365 Sales."""
        fixed, _ = fix_trees(self.MSX_TREE, target="github")
        # Should NOT have a connector before the parenthetical
        assert "├── (sales.crm" not in fixed
        assert "└── (sales.crm" not in fixed
        assert "(sales.crm.dynamics.com)" in fixed


class TestMsxWithContinuation:
    """Test the full MSX tree including skills continuation lines."""

    MSX_FULL = (
        "GitHub Copilot CLI\n"
        "  │\n"
        "  ├── stdio ──▶ MSX MCP Server (TypeScript, 37 tools)\n"
        "  │                    │\n"
        "  │             ├── Auth Tools (msx_login, msx_auth_status)\n"
        "  │             │        │\n"
        "  │             │    Azure CLI (az login)\n"
        "  │             │\n"
        "  │             └── Data Tools (35 tools)\n"
        "  │                      │\n"
        "  │               Dataverse Web API (OData v4)\n"
        "  │                      │\n"
        "  │               MSX D365 Sales\n"
        "  │               (sales.crm.dynamics.com)\n"
        "  │\n"
        "  ├── @msx Agent ──▶ agents/msx.agent.md\n"
        "  │\n"
        "  └── 16 Skills ──▶ skills/monthly-opportunity-report/\n"
        "                     skills/weekly-impact-report/\n"
        "                     skills/account-explorer/"
    )

    def test_skills_continuations_preserved(self):
        """skills/ paths are continuation text, not children."""
        fixed, _ = fix_trees(self.MSX_FULL, target="github")
        assert "skills/weekly-impact-report/" in fixed
        assert "skills/account-explorer/" in fixed
        # They should NOT have connectors
        assert "├── skills/weekly" not in fixed
        assert "└── skills/account" not in fixed


class TestBoxExclusion:
    """Box-drawing diagrams must NOT be processed by the tree fixer.

    Box borders (┌, │, └, ─) overlap with tree-drawing characters (├, └, │).
    The tree fixer must detect rectangular box enclosures and skip them.
    """

    SINGLE_BOX = (
        "┌──────────────────────────────────────────────────────────┐\n"
        "│                    DATA PIPELINE                         │\n"
        "│                                                          │\n"
        "│  S3/GCS Docs ──▶ Fabric OneLake ──▶ Azure Blob/ADLS    │\n"
        "│                     (shortcut)          │                │\n"
        "│                                         ▼                │\n"
        "│                                  AI Search Indexer        │\n"
        "└──────────────────────────────────────────────────────────┘"
    )

    STACKED_BOXES = (
        "┌──────────────────────────────────────────────────────────┐\n"
        "│                    DATA PIPELINE                         │\n"
        "│                                                          │\n"
        "│  S3/GCS Docs ──▶ Fabric OneLake ──▶ Azure Blob/ADLS    │\n"
        "└──────────────────────────────────────────────────────────┘\n"
        "\n"
        "┌──────────────────────────────────────────────────────────┐\n"
        "│                    QUERY PIPELINE                         │\n"
        "│                                                          │\n"
        "│  User Query ──▶ Orchestrator ──▶ Azure AI Search         │\n"
        "└──────────────────────────────────────────────────────────┘"
    )

    NESTED_BOXES = (
        "┌──────────────────────────────────────────────────────────┐\n"
        "│                    DATA PIPELINE                         │\n"
        "│                                                          │\n"
        "│                                    ┌─────────┐           │\n"
        "│                                    │ Chunking │           │\n"
        "│                                    │ Enrichment│          │\n"
        "│                                    └─────────┘           │\n"
        "│                                                          │\n"
        "└──────────────────────────────────────────────────────────┘"
    )

    def test_single_box_not_modified(self):
        """A single box diagram should pass through unchanged."""
        fixed, changes = fix_trees(self.SINGLE_BOX)
        assert len(changes) == 0, f"Tree fixer should not touch box: {changes}"
        assert fixed == self.SINGLE_BOX

    def test_stacked_boxes_not_modified(self):
        """Two stacked box diagrams should pass through unchanged."""
        fixed, changes = fix_trees(self.STACKED_BOXES)
        assert len(changes) == 0, f"Tree fixer should not touch stacked boxes: {changes}"
        assert fixed == self.STACKED_BOXES

    def test_nested_boxes_not_modified(self):
        """A box containing a nested box should pass through unchanged."""
        fixed, changes = fix_trees(self.NESTED_BOXES)
        assert len(changes) == 0, f"Tree fixer should not touch nested boxes: {changes}"
        assert fixed == self.NESTED_BOXES

    def test_issue_repro_full(self):
        """Full reproduction case from the issue — two large boxes with nested boxes."""
        content = (
            "┌──────────────────────────────────────────────────────────┐\n"
            "│                    DATA PIPELINE                         │\n"
            "│                                                          │\n"
            "│  S3/GCS Docs ──▶ Fabric OneLake ──▶ Azure Blob/ADLS    │\n"
            "│                     (shortcut)          │                │\n"
            "│                                         ▼                │\n"
            "│                                  AI Search Indexer        │\n"
            "│                                    ┌─────────┐           │\n"
            "│                                    │ Chunking │           │\n"
            "│                                    │ Enrichment│          │\n"
            "│                                    │ Embedding │          │\n"
            "│                                    └─────────┘           │\n"
            "│                                         │                │\n"
            "│                                         ▼                │\n"
            "│                                  Search Index            │\n"
            "│                              (vectors + text + metadata) │\n"
            "└──────────────────────────────────────────────────────────┘\n"
            "\n"
            "┌──────────────────────────────────────────────────────────┐\n"
            "│                    QUERY PIPELINE                         │\n"
            "│                                                          │\n"
            "│  User Query ──▶ Orchestrator ──▶ Azure AI Search         │\n"
            "│                 (Semantic Kernel,   │                     │\n"
            "│                  Agent Framework)   ▼                     │\n"
            "│                              Hybrid Search               │\n"
            "│                        (keyword + vector + semantic rank) │\n"
            "│                                    │                     │\n"
            "│                                    ▼                     │\n"
            "│                              Top-K Results               │\n"
            "│                                    │                     │\n"
            "│                                    ▼                     │\n"
            "│                              LLM (GPT-4o)                │\n"
            "│                              ──▶ Answer + Citations      │\n"
            "└──────────────────────────────────────────────────────────┘"
        )
        fixed, changes = fix_trees(content)
        assert len(changes) == 0, f"Tree fixer destroyed box diagram: {changes}"
        assert fixed == content

    def test_rounded_box_not_modified(self):
        """Rounded-corner boxes (╭╮╰╯) should also be excluded."""
        box = (
            "╭──────────────────╮\n"
            "│ 📦 Packages: 42  │\n"
            "│ ✅ Tests: 100%   │\n"
            "╰──────────────────╯"
        )
        fixed, changes = fix_trees(box)
        assert len(changes) == 0
        assert fixed == box

    def test_ascii_box_not_modified(self):
        """ASCII boxes (+---+ / |...|) should also be excluded."""
        box = (
            "+----------+\n"
            "| hello    |\n"
            "| world    |\n"
            "+----------+"
        )
        fixed, changes = fix_trees(box)
        assert len(changes) == 0
        assert fixed == box

    def test_box_then_tree_both_correct(self):
        """A box followed by a tree — box is untouched, tree is fixed."""
        content = (
            "┌────────────────┐\n"
            "│ Architecture   │\n"
            "└────────────────┘\n"
            "\n"
            "Root\n"
            "  ├── Child A\n"
            "  └── Child B"
        )
        fixed, changes = fix_trees(content)
        # The box part should be preserved exactly
        assert "┌────────────────┐" in fixed
        assert "│ Architecture   │" in fixed
        assert "└────────────────┘" in fixed

    def test_indented_box_not_modified(self):
        """A box with leading indentation should still be excluded."""
        box = (
            "    ┌─────────┐\n"
            "    │ Chunking │\n"
            "    │ Enrichment│\n"
            "    └─────────┘"
        )
        fixed, changes = fix_trees(box)
        assert len(changes) == 0
        assert fixed == box


class TestTargetAwareness:
    """Tree fixer respects target parameter."""

    def test_terminal_and_github_same_for_ascii_tree(self):
        tree = "Root\n  ├── Child\n  └── Child"
        _, changes_t = fix_trees(tree, target="terminal")
        _, changes_g = fix_trees(tree, target="github")
        assert changes_t == changes_g
