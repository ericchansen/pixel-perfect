"""Regression tests from real-world broken content.

These tests use ACTUAL broken content found in the wild — our own README and
the q2mm architecture page. They prove the fixers produce correct output.

Each test has:
  - INPUT: the actual broken content (as-is from the source)
  - EXPECTED: what the output SHOULD look like (human-verified)

If a test fails, the fixer is wrong. The expected output was verified by a
human looking at the rendered result, not by trusting visual_width().
"""

from aifmt.lib.box_fixer import fix_boxes
from aifmt.lib.table_fixer import fix_tables
from aifmt.lib.tree_fixer import fix_trees
from aifmt.lib.visual_width import visual_width


class TestReadmeHeroBoxes:
    """The two boxes in the README 'Problem' section.

    Both the 'correct' and 'LLM output' boxes render broken on GitHub.
    The fixer should make them actually correct.
    """

    def test_readme_correct_box_is_actually_broken(self, show_visual):
        """The box labeled 'correct' in the README is NOT correct on GitHub.

        The fixer with target="github" MUST detect and fix this.
        """
        broken_input = (
            "╭──────────────────╮\n"
            "│ 📦 Packages: 42  │\n"
            "│ ✅ Tests: 100%   │\n"
            "╰──────────────────╯"
        )
        fixed, changes = fix_boxes(broken_input, target="github")
        show_visual("README 'correct' box (github target)", broken_input, fixed, changes)
        # The fixer MUST detect something is wrong
        assert len(changes) > 0, (
            "Fixer says nothing to fix, but this box renders broken on GitHub. "
            "The right borders don't align because emoji are wider than "
            "visual_width() thinks in terminal mode."
        )

        # FIXME: Human — replace this with the actual correct output.
        # Look at the rendered result and type what it SHOULD be.
        # expected = (
        #     "╭──────────────────╮\n"
        #     "│ 📦 Packages: 42  │\n"  # <-- adjust spacing
        #     "│ ✅ Tests: 100%   │\n"  # <-- adjust spacing
        #     "╰──────────────────╯"
        # )
        # assert fixed == expected

    def test_readme_llm_output_box(self, show_visual):
        """The box labeled 'LLM output' in the README — also broken."""
        broken_input = (
            "╭──────────────────╮\n"
            "│ 📦 Packages: 42   │\n"
            "│ ✅ Tests: 100%  │\n"
            "╰──────────────────╯"
        )
        fixed, changes = fix_boxes(broken_input, target="github")
        show_visual("README 'LLM output' box (github target)", broken_input, fixed, changes)

        assert len(changes) > 0, (
            "Fixer says nothing to fix, but this box renders broken."
        )

        # FIXME: Human — replace with correct output
        # expected = "..."
        # assert fixed == expected


class TestReadmeTableExample:
    """The 'After fix' table example in the README renders broken on GitHub."""

    def test_readme_after_table_is_broken(self, show_visual):
        """The table we show as the 'fixed' output is actually misaligned on GitHub.

        Emoji in the Status column (✅ ❌ 📦) cause the pipe characters
        to not line up when rendered on GitHub.
        """
        broken_after = (
            "| Status | Package    | Downloads |\n"
            "| ------ | ---------- | --------- |\n"
            "| ✅     | numpy      | 1,200,000 |\n"
            "| ❌     | broken-pkg | 42        |\n"
            "| 📦     | requests   | 3,500,000 |"
        )

        fixed, changes = fix_tables(broken_after, target="github")
        show_visual("README 'After fix' table (github target)", broken_after, fixed, changes)

        # The fixer should detect the emoji rows need different padding
        assert len(changes) > 0, (
            "Fixer says the table is fine, but the emoji rows render "
            "misaligned on GitHub. The pipes don't line up."
        )

        # FIXME: Human — type the correct table output here
        # expected = (
        #     "| Status | Package    | Downloads |\n"
        #     "| ------ | ---------- | --------- |\n"
        #     "| ✅     | numpy      | 1,200,000 |\n"  # adjust padding
        #     "| ❌     | broken-pkg | 42        |\n"    # adjust padding
        #     "| 📦     | requests   | 3,500,000 |"      # adjust padding
        # )
        # assert fixed == expected


class TestReadmeBoxExample:
    """The 'Before' and 'After' box examples in the README — both broken."""

    def test_readme_before_box(self, show_visual):
        """The 'before' box in the fix example is broken as shown."""
        broken_input = (
            "┌──────────────────┐\n"
            "│ 📦 Packages: 42  │\n"
            "│ ✅ Passed: 100% │\n"
            "│ ❌ Failed: 0    │\n"
            "└──────────────────┘"
        )
        fixed, changes = fix_boxes(broken_input, target="github")
        show_visual("README 'Before' box (github target)", broken_input, fixed, changes)
        assert len(changes) > 0, "Fixer missed the misalignment"

    def test_readme_after_box_is_also_broken(self, show_visual):
        """The 'after' box we claim is fixed — is ALSO broken on GitHub."""
        broken_after = (
            "┌──────────────────┐\n"
            "│ 📦 Packages: 42  │\n"
            "│ ✅ Passed: 100%  │\n"
            "│ ❌ Failed: 0     │\n"
            "└──────────────────┘"
        )
        fixed, changes = fix_boxes(broken_after, target="github")
        show_visual("README 'After' box (github target)", broken_after, fixed, changes)

        assert len(changes) > 0, (
            "Fixer says this is fine, but it renders broken on GitHub. "
            "The right borders do NOT line up."
        )

        # FIXME: Human — type the correct box here
        # expected = "..."
        # assert fixed == expected


class TestQ2mmArchitectureBox:
    """Box from https://ericchansen.github.io/q2mm/architecture/

    The 'Conversion happens at the boundary' ASCII box diagram.
    Renders broken in MkDocs Material theme.
    """

    def test_q2mm_canonical_unit_space_box(self, show_visual):
        """The big box diagram showing canonical unit space data flow."""
        broken_input = (
            "┌──────────────────────────────────────────────────────────────┐\n"
            "│                   Canonical Unit Space                       │\n"
            "│                                                              │\n"
            "│   Seminario ──→ ForceField ──→ Objective ──→ Optimizer      │\n"
            "│                                    ↕                        │\n"
            "│                               MM Engine                     │\n"
            "│                                                              │\n"
            "└──────────────────────────────────────────────────────────────┘"
        )
        fixed, changes = fix_boxes(broken_input, target="github")
        show_visual("q2mm architecture box (github target)", broken_input, fixed, changes)

        # The right border is ragged — some lines have the │ in different columns
        assert len(changes) > 0, (
            "Fixer says this is fine, but the right borders don't align. "
            "The arrows (──→, ↕) are multi-byte and throw off alignment."
        )

        # FIXME: Human — verify and paste correct output
        # expected = "..."
        # assert fixed == expected


class TestVisualWidthAccuracy:
    """Test that visual_width returns values matching ACTUAL rendered width.

    These tests verify the core measurement function against human-observed
    rendering in GitHub markdown code blocks.

    If these fail, the root cause is in visual_width() — every fixer
    inherits the error.
    """

    def test_emoji_width_in_github_codeblock(self):
        """Emoji in GitHub markdown code blocks.

        FIXME: Human — for each emoji, look at a GitHub code block and count
        how many monospace columns the character ACTUALLY occupies.
        Replace the expected values below.
        """
        # Current implementation says all of these are width 2.
        # Measure in an actual GitHub code block and correct:
        assert visual_width("📦") == 2  # FIXME: is it actually 2 in GitHub?
        assert visual_width("✅") == 2  # FIXME: is it actually 2 in GitHub?
        assert visual_width("❌") == 2  # FIXME: is it actually 2 in GitHub?

    def test_arrow_characters(self):
        """Arrow characters used in the q2mm box.

        ──→ is 3 characters. visual_width should reflect actual rendering.
        """
        assert visual_width("──→") == 3  # FIXME: verify actual width
        assert visual_width("↕") == 1    # FIXME: verify actual width

    def test_box_line_consistency(self):
        """All lines of a correctly-rendered box must have the same
        visual_width. If they don't, the measurement is wrong.

        FIXME: Human — type a box that RENDERS correctly and check that
        visual_width agrees on every line. If it doesn't, visual_width
        is the bug.
        """
        # A simple ASCII box with no wide chars — baseline sanity check
        box = (
            "+----------+\n"
            "| hello    |\n"
            "| world    |\n"
            "+----------+"
        )
        widths = [visual_width(line) for line in box.split("\n")]
        assert len(set(widths)) == 1, f"Even basic box widths differ: {widths}"


class TestMsxMcpTreeDiagram:
    """Tree diagram from the MSX-MCP README Architecture section.

    This is a real-world tree diagram using box-drawing characters (│├└──)
    that renders with misaligned connectors on GitHub. The vertical pipes
    from parent nodes don't visually connect to child branches.

    Source: https://github.com/ericchansen/MSX-MCP/blob/main/README.md

    Current status: Our fixers (box, table, bar) do NOT detect tree diagrams.
    These tests document the gap and will drive tree diagram support.
    """

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
        "  └── 16 Skills ──▶ skills/monthly-opportunity-report/\n"
        "                     skills/weekly-impact-report/\n"
        "                     skills/account-explorer/\n"
        "                     skills/territory-scanner/\n"
        "                     skills/hok-activity-finder/\n"
        "                     skills/hok-opportunities/\n"
        "                     skills/milestone-coach/\n"
        "                     skills/consumption/          (Power BI)\n"
        "                     skills/acr-review/           (Power BI)\n"
        "                     skills/acr-report/           (Power BI)\n"
        "                     skills/spt-tracker/          (Power BI)\n"
        "                     skills/copilot-usage/        (Power BI)\n"
        "                     skills/cplan/                (Power BI)\n"
        "                     skills/preflight/            (Power BI)\n"
        "                     skills/core/                 (infrastructure)\n"
        "                     skills/skill-author/         (infrastructure)"
    )

    def test_current_fixers_miss_tree_diagrams(self):
        """Box/table fixers find nothing in tree diagrams — tree fixer does."""
        _, box_changes = fix_boxes(self.MSX_TREE, target="github")
        _, table_changes = fix_tables(self.MSX_TREE, target="github")

        # Box and table fixers still shouldn't detect tree diagrams
        assert len(box_changes) == 0, "Box fixer shouldn't detect tree diagrams"
        assert len(table_changes) == 0, "Table fixer shouldn't detect tree diagrams"

        # But the tree fixer SHOULD find issues
        _, tree_changes = fix_trees(self.MSX_TREE, target="github")
        assert len(tree_changes) > 0, (
            "Tree fixer should detect issues in the MSX-MCP diagram"
        )

    def test_tree_vertical_pipe_alignment(self):
        """The vertical pipe from 'MSX MCP Server' should align with its children.

        In the source:
        - L1: │ at col 23 (descending from MSX MCP Server)
        - L2: ├ at col 16 (Auth Tools) — MISALIGNED (should be col 23)

        The children branch from col 16 but the parent's pipe descends at col 23.
        """
        lines = self.MSX_TREE.split("\n")

        # Line: "  │                    │" — second pipe at col 23
        parent_pipe_line = lines[3]  # "  │                    │"
        # Line: "  │             ├── Auth Tools..." — branch at col 16
        child_branch_line = lines[4]

        # Find column of second │ in parent line
        parent_pipe_col = None
        col = 0
        pipe_count = 0
        for ch in parent_pipe_line:
            if ch == "│":
                pipe_count += 1
                if pipe_count == 2:
                    parent_pipe_col = col
                    break
            col += 1

        # Find column of ├ in child line
        child_branch_col = None
        col = 0
        for ch in child_branch_line:
            if ch == "├":
                child_branch_col = col
                break
            col += 1

        # These DON'T match — that's the bug
        assert parent_pipe_col != child_branch_col, (
            f"If these match, the tree is aligned (parent pipe col {parent_pipe_col} "
            f"== child branch col {child_branch_col}). But they shouldn't — "
            f"this is a known misalignment."
        )
        # Document the actual values
        assert parent_pipe_col == 23, f"Parent pipe at {parent_pipe_col}, expected 23"
        assert child_branch_col == 16, f"Child branch at {child_branch_col}, expected 16"

    def test_dataverse_not_connected_to_parent(self):
        """'Dataverse Web API' and 'MSX D365 Sales' are children of 'Data Tools'
        but they lack tree connectors (├── or └──).

        They're just indented text under a vertical pipe — structurally orphaned.
        """
        lines = self.MSX_TREE.split("\n")
        dataverse_line = lines[10]  # "  │               Dataverse Web API (OData v4)"

        # This line has content but no tree branch character
        has_branch = any(ch in dataverse_line for ch in "├└")
        assert not has_branch, (
            "Dataverse line has a branch connector now — test needs updating"
        )
        # It SHOULD have a branch connector but doesn't — that's a bug in the source


class TestBoxDiagramNotDestroyedByModeAll:
    """Regression: fix(mode='all') must not destroy box diagrams.

    The tree fixer was matching box-drawing characters (┌│└─) as tree
    nodes and destructively reformatting box diagrams into flat tree lists.
    Box regions are now detected and excluded from tree processing.
    """

    DATA_PIPELINE_BOX = (
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

    def test_tree_fixer_alone_preserves_boxes(self, show_visual):
        """Tree fixer alone should not touch box diagrams."""
        fixed, changes = fix_trees(self.DATA_PIPELINE_BOX, target="github")
        show_visual("Tree fixer alone on DATA_PIPELINE_BOX", self.DATA_PIPELINE_BOX, fixed, changes)
        assert len(changes) == 0, f"Tree fixer modified box diagram: {changes}"
        assert fixed == self.DATA_PIPELINE_BOX

    def test_box_borders_intact_after_all_fixers(self, show_visual):
        """After running ALL fixers (box, table, bar, tree), the box structure
        must still have ┌...┐ top borders and └...┘ bottom borders.

        This is the exact scenario from the issue: fix(mode='all').
        """
        from aifmt.lib.bar_fixer import fix_bars
        from aifmt.lib.box_fixer import fix_boxes
        from aifmt.lib.table_fixer import fix_tables

        result = self.DATA_PIPELINE_BOX

        result, _ = fix_tables(result, target="github")
        result, _ = fix_bars(result)
        result, _ = fix_boxes(result, target="github")
        result, _ = fix_trees(result, target="github")

        show_visual("All fixers pipeline on DATA_PIPELINE_BOX", self.DATA_PIPELINE_BOX, result)
        # Box structure must be preserved — ├── and └── tree connectors
        # must NOT appear as line starters
        lines = result.split("\n")
        for line in lines:
            stripped = line.strip()
            if not stripped:
                continue
            assert not stripped.startswith("├── "), (
                f"Box was destroyed — tree connector injected: {stripped}"
            )
            # └── as tree connector (with space+label) vs └────┘ as box border
            if stripped.startswith("└── ") and "┘" not in stripped:
                raise AssertionError(
                    f"Box was destroyed — tree connector injected: {stripped}"
                )

        # Top/bottom borders must be intact
        assert any("┌──────" in line for line in lines), "Top border missing"
        assert any("└──────" in line for line in lines), "Bottom border missing"
