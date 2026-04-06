"""Tests for the tree diagram fixer.

The tree fixer parses misaligned tree diagrams into a node model,
then re-renders them with correct ├──/└──/│ alignment.
"""

from conftest import ShowVisual

from aifmt.lib.tree_fixer import fix_trees


class TestTreeDetection:
    """Test that tree regions are correctly identified in text."""

    def test_simple_tree_detected(self) -> None:
        tree = "Root\n  ├── Child A\n  └── Child B"
        _, changes = fix_trees(tree)
        assert isinstance(changes, list)

    def test_non_tree_content_ignored(self) -> None:
        text = "This is a paragraph.\nNo tree characters.\nNothing to fix."
        _, changes = fix_trees(text)
        assert len(changes) == 0

    def test_single_pipe_not_a_tree(self) -> None:
        text = "Use | for pipes in bash"
        _, changes = fix_trees(text)
        assert len(changes) == 0


class TestCorrectTrees:
    """Correctly-structured trees should produce zero changes."""

    def test_simple_two_children(self) -> None:
        tree = "Root\n├── Child A\n└── Child B"
        fixed, changes = fix_trees(tree)
        assert len(changes) == 0
        assert fixed == tree

    def test_nested_tree(self) -> None:
        tree = """\
Root
├── Parent
│   ├── Child A
│   └── Child B
└── Sibling"""
        fixed, changes = fix_trees(tree)
        assert len(changes) == 0
        assert fixed == tree

    def test_deep_nesting(self) -> None:
        tree = """\
Root
├── Level 1
│   ├── Level 2
│   │   └── Level 3
│   └── Level 2b
└── Level 1b"""
        fixed, changes = fix_trees(tree)
        assert len(changes) == 0
        assert fixed == tree


class TestMisalignedPipes:
    """Trees with pipe columns that don't match branch columns."""

    correct = """\
Root
├── Parent
│   ├── Child A
│   └── Child B
└── Sibling"""

    def test_pipe_misaligned_gets_fixed(self) -> None:
        """Pipe at wrong column should be realigned."""
        broken = """\
Root
  ├── Parent
  │              │
  │    ├── Child A
  │    │
  │    └── Child B
  └── Sibling"""
        fixed, changes = fix_trees(broken)
        assert fixed == self.correct
        assert len(changes) >= 1

    def test_already_aligned(self) -> None:
        """Already correct tree → no changes."""
        fixed, changes = fix_trees(self.correct)
        assert fixed == self.correct
        assert len(changes) == 0


class TestOrphanedSingleChild:
    """Single orphaned content line gets a connector added."""

    correct = """\
Root
├── Parent
│   └── Orphaned Child
└── Sibling"""

    def test_orphaned_child_gets_connector(self) -> None:
        broken = "Root\n  ├── Parent\n  │     │\n  │     Orphaned Child\n  └── Sibling"
        fixed, changes = fix_trees(broken)
        assert fixed == self.correct
        assert len(changes) >= 1


class TestOrphanedMultipleChildren:
    """Multiple orphaned content lines get connectors added."""

    correct = """\
Root
├── Parent
│   ├── Orphan A
│   └── Orphan B
└── Sibling"""

    def test_multiple_orphans_get_connectors(self) -> None:
        broken = """\
Root
  ├── Parent
  │     │
  │     Orphan A
  │     │
  │     Orphan B
  └── Sibling"""
        fixed, changes = fix_trees(broken)
        assert fixed == self.correct
        assert len(changes) >= 1


class TestContinuationPreserved:
    """Non-tree continuation lines stay as continuations."""

    correct = """\
Root
└── 16 Skills ──▶ skills/report/
    skills/explorer/
    skills/impact/"""

    def test_continuation_preserved(self) -> None:
        """Lines without any tree chars are continuations, not children."""
        fixed, changes = fix_trees(self.correct)
        assert fixed == self.correct
        assert len(changes) == 0


class TestParentheticalContinuation:
    """Text starting with '(' is continuation of previous node."""

    correct = """\
Root
├── MSX D365 Sales
│   (sales.crm.dynamics.com)
└── Other"""

    def test_parenthetical_is_continuation(self) -> None:
        broken = "Root\n  ├── MSX D365 Sales\n  │   (sales.crm.dynamics.com)\n  └── Other"
        fixed, _changes = fix_trees(broken)
        assert fixed == self.correct


class TestMsxMcpDiagram:
    """Integration test using the real MSX-MCP README architecture diagram."""

    broken = """\
GitHub Copilot CLI
  │
  ├── stdio ──▶ MSX MCP Server (TypeScript, 37 tools)
  │                    │
  │             ├── Auth Tools (msx_login, msx_auth_status)
  │             │        │
  │             │    Azure CLI (az login)
  │             │
  │             └── Data Tools (35 tools)
  │                      │
  │               Dataverse Web API (OData v4)
  │                      │
  │               MSX D365 Sales
  │               (sales.crm.dynamics.com)
  │
  ├── @msx Agent ──▶ agents/msx.agent.md
  │
  └── 16 Skills ──▶ skills/monthly-opportunity-report/"""

    correct = """\
GitHub Copilot CLI
├── stdio ──▶ MSX MCP Server (TypeScript, 37 tools)
│   ├── Auth Tools (msx_login, msx_auth_status)
│   │   └── Azure CLI (az login)
│   └── Data Tools (35 tools)
│       ├── Dataverse Web API (OData v4)
│       └── MSX D365 Sales
│           (sales.crm.dynamics.com)
├── @msx Agent ──▶ agents/msx.agent.md
└── 16 Skills ──▶ skills/monthly-opportunity-report/"""

    def test_fixes_structure(self) -> None:
        fixed, changes = fix_trees(self.broken, target="github")
        assert fixed == self.correct
        assert len(changes) >= 1


class TestMsxWithContinuation:
    """Full MSX tree including skills continuation lines."""

    broken = """\
GitHub Copilot CLI
  │
  ├── stdio ──▶ MSX MCP Server (TypeScript, 37 tools)
  │                    │
  │             ├── Auth Tools (msx_login, msx_auth_status)
  │             │        │
  │             │    Azure CLI (az login)
  │             │
  │             └── Data Tools (35 tools)
  │                      │
  │               Dataverse Web API (OData v4)
  │                      │
  │               MSX D365 Sales
  │               (sales.crm.dynamics.com)
  │
  ├── @msx Agent ──▶ agents/msx.agent.md
  │
  └── 16 Skills ──▶ skills/monthly-opportunity-report/
                     skills/weekly-impact-report/
                     skills/account-explorer/"""

    correct = """\
GitHub Copilot CLI
├── stdio ──▶ MSX MCP Server (TypeScript, 37 tools)
│   ├── Auth Tools (msx_login, msx_auth_status)
│   │   └── Azure CLI (az login)
│   └── Data Tools (35 tools)
│       ├── Dataverse Web API (OData v4)
│       └── MSX D365 Sales
│           (sales.crm.dynamics.com)
├── @msx Agent ──▶ agents/msx.agent.md
└── 16 Skills ──▶ skills/monthly-opportunity-report/
    skills/weekly-impact-report/
    skills/account-explorer/"""

    def test_full_tree_with_continuations(self) -> None:
        fixed, changes = fix_trees(self.broken, target="github")
        assert fixed == self.correct
        assert len(changes) >= 1


class TestBoxExclusionSingle:
    """Single box diagram must NOT be processed by the tree fixer."""

    # TODO: Impossible to get correct in VS Code UI, possibly due to arrow.
    correct = """\
┌───────────────────────────────────────────────────────┐
│                    DATA PIPELINE                      │
│                                                       │
│  S3/GCS Docs ──▶ Fabric OneLake ──▶ Azure Blob/ADLS  │
│                     (shortcut)          │             │
│                                         ▼             │
│                                  AI Search Indexer    │
└───────────────────────────────────────────────────────┘"""

    def test_not_modified(self, show_visual: ShowVisual) -> None:
        """A single box diagram should pass through unchanged."""
        fixed, changes = fix_trees(self.correct)
        show_visual("Single box through tree fixer", self.correct, fixed, changes)
        assert len(changes) == 0, f"Tree fixer should not touch box: {changes}"
        assert fixed == self.correct


class TestBoxExclusionStacked:
    """Two stacked box diagrams must NOT be processed by the tree fixer."""

    # TODO: Impossible to get correct in VS Code UI, possibly due to arrow.
    correct = """\
┌───────────────────────────────────────────────────────┐
│                    DATA PIPELINE                      │
│                                                       │
│  S3/GCS Docs ──▶ Fabric OneLake ──▶ Azure Blob/ADLS  |
└───────────────────────────────────────────────────────┘

┌───────────────────────────────────────────────────────┐
│                    QUERY PIPELINE                     │
│                                                       │
│   User Query ──▶ Orchestrator ──▶ Azure AI Search    │
└───────────────────────────────────────────────────────┘"""

    def test_not_modified(self, show_visual: ShowVisual) -> None:
        """Two stacked box diagrams should pass through unchanged."""
        fixed, changes = fix_trees(self.correct)
        show_visual("Stacked boxes through tree fixer", self.correct, fixed, changes)
        assert len(changes) == 0, f"Tree fixer should not touch stacked boxes: {changes}"
        assert fixed == self.correct


class TestBoxExclusionNested:
    """A box containing a nested box must NOT be processed by the tree fixer."""

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

    def test_not_modified(self, show_visual: ShowVisual) -> None:
        """A box containing a nested box should pass through unchanged."""
        fixed, changes = fix_trees(self.correct)
        show_visual("Nested boxes through tree fixer", self.correct, fixed, changes)
        assert len(changes) == 0, f"Tree fixer should not touch nested boxes: {changes}"
        assert fixed == self.correct


class TestBoxExclusionFullRepro:
    """Full reproduction case from the issue — two large boxes with nested boxes."""

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

    def test_not_modified(self, show_visual: ShowVisual) -> None:
        fixed, changes = fix_trees(self.correct)
        show_visual("Issue repro: two large boxes with nested boxes", self.correct, fixed, changes)
        assert len(changes) == 0, f"Tree fixer destroyed box diagram: {changes}"
        assert fixed == self.correct


class TestBoxExclusionRounded:
    """Rounded-corner boxes (╭╮╰╯) must NOT be processed by the tree fixer."""

    # TODO: Impossible due to single emoji per lie.
    correct = """\
╭──────────────────╮
│ 📦 Packages: 42  │
│ ✅ Tests: 100%   │
╰──────────────────╯"""

    def test_not_modified(self, show_visual: ShowVisual) -> None:
        fixed, changes = fix_trees(self.correct)
        show_visual("Rounded box through tree fixer", self.correct, fixed, changes)
        assert len(changes) == 0
        assert fixed == self.correct


class TestBoxExclusionAscii:
    """ASCII boxes (+---+ / |...|) must NOT be processed by the tree fixer."""

    correct = """\
+-------+
| hello |
| world |
+-------+"""

    def test_not_modified(self, show_visual: ShowVisual) -> None:
        fixed, changes = fix_trees(self.correct)
        show_visual("ASCII box through tree fixer", self.correct, fixed, changes)
        assert len(changes) == 0
        assert fixed == self.correct


class TestBoxExclusionMixed:
    """A box followed by a tree — box is untouched, tree is fixed."""

    correct = """\
┌────────────────┐
│ Architecture   │
└────────────────┘

Root
  ├── Child A
  └── Child B"""

    def test_box_preserved_tree_fixed(self, show_visual: ShowVisual) -> None:
        fixed, changes = fix_trees(self.correct)
        show_visual("Box + tree mixed content", self.correct, fixed, changes)
        assert "┌────────────────┐" in fixed
        assert "│ Architecture   │" in fixed
        assert "└────────────────┘" in fixed


class TestBoxExclusionIndented:
    """A box with leading indentation must NOT be processed by the tree fixer."""

    correct = """\
    ┌─────────────┐
    │ Chunking     │
    │ Enrichment   │
    └─────────────┘"""

    def test_not_modified(self, show_visual: ShowVisual) -> None:
        fixed, changes = fix_trees(self.correct)
        show_visual("Indented box through tree fixer", self.correct, fixed, changes)
        assert len(changes) == 0
        assert fixed == self.correct


class TestTargetAwareness:
    """Tree fixer respects target parameter."""

    def test_terminal_and_github_same_for_ascii_tree(self) -> None:
        tree = "Root\n  ├── Child\n  └── Child"
        _, changes_t = fix_trees(tree, target="terminal")
        _, changes_g = fix_trees(tree, target="github")
        assert changes_t == changes_g
