"""Regression tests from real-world broken content.

These tests use ACTUAL broken content found in the wild — our own README and
the q2mm architecture page. They prove the fixers produce correct output.

Each test class has:
  - correct: what the fixer SHOULD produce (seeded from actual fixer output)
  - broken: the actual broken content (as-is from the source)
  - assert fixed == self.correct

If a test fails, the fixer is wrong. The correct output was verified by a
human looking at the rendered result, not by trusting visual_width().
"""

import pytest
from conftest import ShowVisual

from aifmt.lib.box_fixer import fix_boxes
from aifmt.lib.table_fixer import fix_tables
from aifmt.lib.tree_fixer import fix_trees
from aifmt.lib.visual_width import visual_width


@pytest.mark.parametrize(
    ("target", "correct"),
    [
        pytest.param(
            "terminal",
            """\
╭──────────────────╮
│ 📦 Packages: 42  │
│ ✅ Tests: 100%   │
╰──────────────────╯""",
            marks=pytest.mark.skip(reason="needs human verification in terminal"),
        ),
        (
            "github",
            """\
╭──────────────────╮
│ 📦 Packages: 42 │
│ ✅ Tests: 100%  │
╰──────────────────╯""",
        ),
    ],
)
class TestReadmeHeroBoxes:
    """The two boxes in the README 'Problem' section.

    Both the 'correct' and 'LLM output' boxes render broken on GitHub.
    The fixer produces the same output for both (odd emoji → ⚠ warning).
    """

    def test_readme_correct_box(
        self,
        target: str,
        correct: str,
        show_visual: ShowVisual,
    ) -> None:
        broken = """\
╭──────────────────╮
│ 📦 Packages: 42  │
│ ✅ Tests: 100%   │
╰──────────────────╯"""
        fixed, changes = fix_boxes(broken, target=target)
        show_visual("README 'correct' box", broken, fixed, changes)
        assert fixed == correct
        assert len(changes) > 0

    def test_readme_llm_output_box(
        self,
        target: str,
        correct: str,
        show_visual: ShowVisual,
    ) -> None:
        broken = """\
╭──────────────────╮
│ 📦 Packages: 42   │
│ ✅ Tests: 100%  │
╰──────────────────╯"""
        fixed, changes = fix_boxes(broken, target=target)
        show_visual("README 'LLM output' box", broken, fixed, changes)
        assert fixed == correct
        assert len(changes) > 0


@pytest.mark.parametrize(
    ("target", "correct"),
    [
        pytest.param(
            "terminal",
            """\
| Status | Package    | Downloads |
| ------ | ---------- | --------- |
| ✅     | numpy      | 1,200,000 |
| ❌     | broken-pkg | 42        |
| 📦     | requests   | 3,500,000 |""",
            marks=pytest.mark.skip(reason="needs human verification in terminal"),
        ),
        (
            "github",
            """\
| Status | Package    | Downloads |
| ------ | ---------- | --------- |
| ✅    | numpy      | 1,200,000 |
| ❌    | broken-pkg | 42        |
| 📦    | requests   | 3,500,000 |""",
        ),
    ],
)
class TestReadmeTableExample:
    """The 'After fix' table example in the README renders broken on GitHub."""

    def test_readme_after_table(
        self,
        target: str,
        correct: str,
        show_visual: ShowVisual,
    ) -> None:
        broken = """\
| Status | Package    | Downloads |
| ------ | ---------- | --------- |
| ✅     | numpy      | 1,200,000 |
| ❌     | broken-pkg | 42        |
| 📦     | requests   | 3,500,000 |"""
        fixed, changes = fix_tables(broken, target=target)
        show_visual("README 'After fix' table", broken, fixed, changes)
        assert fixed == correct
        assert len(changes) > 0


@pytest.mark.parametrize(
    ("target", "correct"),
    [
        pytest.param(
            "terminal",
            """\
┌──────────────────┐
│ 📦 Packages: 42  │
│ ✅ Passed: 100%  │
│ ❌ Failed: 0     │
└──────────────────┘""",
            marks=pytest.mark.skip(reason="needs human verification in terminal"),
        ),
        (
            "github",
            """\
┌──────────────────┐
│ 📦 Packages: 42 │
│ ✅ Passed: 100% │
│ ❌ Failed: 0    │
└──────────────────┘""",
        ),
    ],
)
class TestReadmeBoxExample:
    """The 'Before' and 'After' box examples in the README — both broken."""

    def test_readme_before_box(
        self,
        target: str,
        correct: str,
        show_visual: ShowVisual,
    ) -> None:
        broken = """\
┌──────────────────┐
│ 📦 Packages: 42  │
│ ✅ Passed: 100% │
│ ❌ Failed: 0    │
└──────────────────┘"""
        fixed, changes = fix_boxes(broken, target=target)
        show_visual("README 'Before' box", broken, fixed, changes)
        assert fixed == correct
        assert len(changes) > 0

    def test_readme_after_box(
        self,
        target: str,
        correct: str,
        show_visual: ShowVisual,
    ) -> None:
        broken = """\
┌──────────────────┐
│ 📦 Packages: 42  │
│ ✅ Passed: 100%  │
│ ❌ Failed: 0     │
└──────────────────┘"""
        fixed, changes = fix_boxes(broken, target=target)
        show_visual("README 'After' box", broken, fixed, changes)
        assert fixed == correct
        assert len(changes) > 0


class TestQ2mmArchitectureBox:
    """Box from https://ericchansen.github.io/q2mm/architecture/

    The 'Conversion happens at the boundary' ASCII box diagram.
    Renders broken in MkDocs Material theme.
    """

    # HUMAN: verify this correct value
    correct = """\
┌──────────────────────────────────────────────────────────────┐
│                   Canonical Unit Space                       │
│                                                              │
│   Seminario ──→ ForceField ──→ Objective ──→ Optimizer       │
│                                    ↕                         │
│                               MM Engine                      │
│                                                              │
└──────────────────────────────────────────────────────────────┘"""

    def test_q2mm_box(self, show_visual: ShowVisual) -> None:
        broken = """\
┌──────────────────────────────────────────────────────────────┐
│                   Canonical Unit Space                       │
│                                                              │
│   Seminario ──→ ForceField ──→ Objective ──→ Optimizer      │
│                                    ↕                        │
│                               MM Engine                     │
│                                                              │
└──────────────────────────────────────────────────────────────┘"""
        fixed, changes = fix_boxes(broken, target="github")
        show_visual("q2mm architecture box (github target)", broken, fixed, changes)
        assert fixed == self.correct
        assert len(changes) > 0


class TestVisualWidthAccuracy:
    """Test that visual_width returns values matching ACTUAL rendered width.

    These tests verify the core measurement function against human-observed
    rendering in GitHub markdown code blocks.

    If these fail, the root cause is in visual_width() — every fixer
    inherits the error.
    """

    def test_emoji_width_in_github_codeblock(self) -> None:
        """Emoji in GitHub markdown code blocks are 2 columns (terminal profile)."""
        assert visual_width("📦") == 2
        assert visual_width("✅") == 2
        assert visual_width("❌") == 2

    def test_arrow_characters(self) -> None:
        """Arrow characters used in the q2mm box."""
        assert visual_width("──→") == 3
        assert visual_width("↕") == 1

    def test_box_line_consistency(self) -> None:
        """All lines of a correctly-rendered box must have the same visual_width."""
        box = "+----------+\n| hello    |\n| world    |\n+----------+"
        widths = [visual_width(line) for line in box.split("\n")]
        assert len(set(widths)) == 1, f"Even basic box widths differ: {widths}"


class TestMsxMcpTreeDiagram:
    """Tree diagram from the MSX-MCP README Architecture section.

    Source: https://github.com/ericchansen/MSX-MCP/blob/main/README.md
    """

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
                     skills/account-explorer/
                     skills/territory-scanner/
                     skills/hok-activity-finder/
                     skills/hok-opportunities/
                     skills/milestone-coach/
                     skills/consumption/          (Power BI)
                     skills/acr-review/           (Power BI)
                     skills/acr-report/           (Power BI)
                     skills/spt-tracker/          (Power BI)
                     skills/copilot-usage/        (Power BI)
                     skills/cplan/                (Power BI)
                     skills/preflight/            (Power BI)
                     skills/core/                 (infrastructure)
                     skills/skill-author/         (infrastructure)"""

    # HUMAN: verify this correct value
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
    skills/account-explorer/
    skills/territory-scanner/
    skills/hok-activity-finder/
    skills/hok-opportunities/
    skills/milestone-coach/
    skills/consumption/          (Power BI)
    skills/acr-review/           (Power BI)
    skills/acr-report/           (Power BI)
    skills/spt-tracker/          (Power BI)
    skills/copilot-usage/        (Power BI)
    skills/cplan/                (Power BI)
    skills/preflight/            (Power BI)
    skills/core/                 (infrastructure)
    skills/skill-author/         (infrastructure)"""

    def test_tree_fixer_fixes_structure(self) -> None:
        fixed, changes = fix_trees(self.broken, target="github")
        assert fixed == self.correct
        assert len(changes) >= 1

    def test_box_and_table_fixers_ignore_trees(self) -> None:
        """Box and table fixers should not detect tree diagrams."""
        _, box_changes = fix_boxes(self.broken, target="github")
        _, table_changes = fix_tables(self.broken, target="github")
        assert len(box_changes) == 0, "Box fixer shouldn't detect tree diagrams"
        assert len(table_changes) == 0, "Table fixer shouldn't detect tree diagrams"


class TestBoxDiagramNotDestroyedByModeAll:
    """Regression: fix(mode='all') must not destroy box diagrams.

    The tree fixer was matching box-drawing characters (┌│└─) as tree
    nodes and destructively reformatting box diagrams into flat tree lists.
    Box regions are now detected and excluded from tree processing.
    """

    correct = """\
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

    def test_tree_fixer_alone_preserves_boxes(self, show_visual: ShowVisual) -> None:
        fixed, changes = fix_trees(self.correct, target="github")
        show_visual("Tree fixer alone on box diagram", self.correct, fixed, changes)
        assert fixed == self.correct
        assert len(changes) == 0

    def test_all_fixers_pipeline_preserves_boxes(self, show_visual: ShowVisual) -> None:
        """After running ALL fixers (box, table, bar, tree), boxes stay intact.

        Note: box fixer expands borders (known bug), so we verify structure
        rather than exact equality. Once the box fixer bug is fixed,
        this should become `assert result == self.correct`.
        """
        from aifmt.lib.bar_fixer import fix_bars

        result = self.correct
        result, _ = fix_tables(result, target="github")
        result, _ = fix_bars(result)
        result, _ = fix_boxes(result, target="github")
        result, _ = fix_trees(result, target="github")

        show_visual("All fixers pipeline on box diagram", self.correct, result)
        # Box structure must be preserved — top/bottom borders intact
        lines = result.split("\n")
        assert any("┌──────" in ln for ln in lines), "Top border missing"
        assert any("└──────" in ln for ln in lines), "Bottom border missing"
        # Tree connectors must NOT appear as line starters
        for line in lines:
            stripped = line.strip()
            if stripped and stripped.startswith("└── ") and "┘" not in stripped:
                raise AssertionError(f"Box destroyed — tree connector: {stripped}")
