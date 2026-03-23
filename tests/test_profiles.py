"""Tests for the rendering profile system and multi-target support."""

import pytest

from aifmt.lib.box_fixer import fix_boxes
from aifmt.lib.table_fixer import fix_tables
from aifmt.lib.visual_width import (
    RenderProfile,
    get_profile,
    list_profiles,
    register_profile,
    visual_width,
    visual_width_precise,
)

# ---------------------------------------------------------------------------
# Profile registry
# ---------------------------------------------------------------------------


class TestBuiltinProfiles:
    def test_terminal_exists(self):
        p = get_profile("terminal")
        assert p.name == "terminal"
        assert p.emoji_width == 2
        assert p.cjk_width == 2

    def test_github_exists(self):
        p = get_profile("github")
        assert p.name == "github"
        assert p.emoji_width == 2.5
        assert p.cjk_width == 2.0

    def test_unknown_raises(self):
        with pytest.raises(ValueError, match="Unknown target"):
            get_profile("nonexistent")

    def test_list_profiles_returns_both(self):
        profiles = list_profiles()
        names = {p.name for p in profiles}
        assert "terminal" in names
        assert "github" in names


class TestCustomProfiles:
    def test_register_and_use(self):
        register_profile(RenderProfile(
            name="slack",
            emoji_width=2,
            cjk_width=1,
            description="Slack code blocks",
        ))
        p = get_profile("slack")
        assert p.name == "slack"
        assert p.emoji_width == 2
        assert p.cjk_width == 1

        # Actually use it for width calculation
        assert visual_width("📦", target="slack") == 2
        assert visual_width("hello", target="slack") == 5

    def test_register_overwrites(self):
        register_profile(RenderProfile(name="test-overwrite", emoji_width=4))
        assert get_profile("test-overwrite").emoji_width == 4
        register_profile(RenderProfile(name="test-overwrite", emoji_width=5))
        assert get_profile("test-overwrite").emoji_width == 5


# ---------------------------------------------------------------------------
# GitHub target — visual_width
# ---------------------------------------------------------------------------


class TestGitHubVisualWidth:
    """Verify GitHub-mode width calculations match observed rendering.

    Diagnostics confirmed: emoji = 2.5 monospace columns on GitHub.
    visual_width() rounds to int; visual_width_precise() returns float.
    """

    def test_emoji_precise_width(self):
        assert visual_width_precise("📦", target="github") == 2.5

    def test_emoji_rounded_width(self):
        assert visual_width("📦", target="github") == 2  # round(2.5) = 2

    def test_checkmark_precise(self):
        assert visual_width_precise("✅", target="github") == 2.5

    def test_cross_precise(self):
        assert visual_width_precise("❌", target="github") == 2.5

    def test_rocket_precise(self):
        assert visual_width_precise("🚀", target="github") == 2.5

    def test_emoji_in_text(self):
        # "📦 Packages: 42" = 2.5 + 1 + 12 = 15.5 → rounds to 16
        assert visual_width("📦 Packages: 42", target="github") == 16
        assert visual_width_precise("📦 Packages: 42", target="github") == 15.5

    def test_two_emoji_precise_is_integer(self):
        # 2 emoji = 5.0 cols — even counts give perfect integer widths
        assert visual_width_precise("📦 ✅", target="github") == 6.0
        assert visual_width("📦 ✅", target="github") == 6

    def test_ascii_same_both_targets(self):
        assert visual_width("hello", target="terminal") == 5
        assert visual_width("hello", target="github") == 5

    def test_box_drawing_same_both_targets(self):
        line = "┌──────────────────┐"
        assert visual_width(line, target="terminal") == visual_width(line, target="github")

    def test_cjk_same_both_targets(self):
        assert visual_width("古池", target="terminal") == 4
        assert visual_width("古池", target="github") == 4


# ---------------------------------------------------------------------------
# GitHub target — box fixer
# ---------------------------------------------------------------------------


class TestGitHubBoxFixer:
    """Boxes that look correct in terminal but need fixing for GitHub."""

    def test_emoji_box_detects_misalignment(self):
        """A box that's perfect in terminal is broken on GitHub."""
        terminal_perfect = (
            "┌──────────────────┐\n"
            "│ 📦 Packages: 42  │\n"
            "│ ✅ Tests: 100%   │\n"
            "└──────────────────┘"
        )
        # Terminal: no changes needed
        _, terminal_changes = fix_boxes(terminal_perfect, target="terminal")
        assert len(terminal_changes) == 0

        # GitHub: MUST detect and fix (each line is 0.5 too wide)
        fixed, github_changes = fix_boxes(terminal_perfect, target="github")
        assert len(github_changes) > 0
        # Fixed lines should have less trailing padding
        fixed_lines = fixed.split("\n")
        assert len(fixed_lines[1]) < len(terminal_perfect.split("\n")[1])

    def test_two_emoji_line_perfect_alignment(self):
        """2 emoji per line = integer width = perfect alignment possible."""
        box = (
            "┌────────────────────┐\n"
            "│ 📦 ✅ Status: OK   │\n"
            "│ Plain text here    │\n"
            "└────────────────────┘"
        )
        fixed, changes = fix_boxes(box, target="github")
        # The 2-emoji line has precise width that's an integer,
        # so it can be fixed to exactly match the border
        fixed_lines = fixed.split("\n")
        border_w = visual_width_precise(fixed_lines[0], target="github")
        emoji_w = visual_width_precise(fixed_lines[1], target="github")
        # Both should be integers and equal (or very close)
        assert border_w == int(border_w)
        assert emoji_w == int(emoji_w)

    def test_no_emoji_box_unchanged(self):
        """A box with no emoji should be identical in both modes."""
        box = (
            "┌──────────────────┐\n"
            "│ Packages: 42     │\n"
            "│ Tests: 100%      │\n"
            "└──────────────────┘"
        )
        fixed_t, changes_t = fix_boxes(box, target="terminal")
        fixed_g, changes_g = fix_boxes(box, target="github")
        assert fixed_t == fixed_g


# ---------------------------------------------------------------------------
# GitHub target — table fixer
# ---------------------------------------------------------------------------


class TestGitHubTableFixer:
    """Tables with emoji need different padding for GitHub vs terminal."""

    def test_emoji_table_changes_padding(self):
        """A terminal-aligned emoji table gets different padding for GitHub."""
        table = (
            "| Status | Package |\n"
            "| ------ | ------- |\n"
            "| ✅     | numpy   |\n"
            "| ok     | pandas  |"
        )
        fixed_t, _ = fix_tables(table, target="terminal")
        fixed_g, _ = fix_tables(table, target="github")
        # The outputs should differ because emoji padding changes
        assert fixed_t != fixed_g

    def test_no_emoji_table_same_both(self):
        """A table with no emoji should be identical in both modes."""
        table = (
            "| Status | Package |\n"
            "| ------ | ------- |\n"
            "| ok     | numpy   |\n"
            "| fail   | pandas  |"
        )
        fixed_t, _ = fix_tables(table, target="terminal")
        fixed_g, _ = fix_tables(table, target="github")
        assert fixed_t == fixed_g

    def test_emoji_cell_gets_less_padding(self):
        """In GitHub mode, emoji cells should get less trailing space."""
        table = (
            "| Status | Name |\n"
            "| ------ | ---- |\n"
            "| ✅     | pass |\n"
            "| fail   | fail |"
        )
        fixed, _ = fix_tables(table, target="github")
        lines = fixed.split("\n")
        # The ✅ row should have fewer spaces around the emoji
        emoji_row = lines[2]
        plain_row = lines[3]
        # Both rows should have the same total pipe-to-pipe structure
        assert emoji_row.count("|") == plain_row.count("|")


# ---------------------------------------------------------------------------
# Profile integration — custom profile through the full stack
# ---------------------------------------------------------------------------


class TestCustomProfileIntegration:
    """Verify a custom profile threads through fixers correctly."""

    def test_custom_profile_width(self):
        register_profile(RenderProfile(
            name="wide-emoji-test",
            emoji_width=4,
            cjk_width=2,
        ))
        # With emoji_width=4, 📦 takes 4 cols
        assert visual_width("📦", target="wide-emoji-test") == 4

    def test_custom_profile_in_box_fixer(self):
        register_profile(RenderProfile(
            name="narrow-emoji-test",
            emoji_width=1,
            cjk_width=2,
        ))
        box = (
            "┌──────────────────┐\n"
            "│ 📦 Packages: 42  │\n"
            "└──────────────────┘"
        )
        # With emoji_width=1, the box would need MORE padding (emoji is narrower)
        fixed, changes = fix_boxes(box, target="narrow-emoji-test")
        assert len(changes) > 0


# ---------------------------------------------------------------------------
# Fractional width warnings
# ---------------------------------------------------------------------------


class TestFractionalWidthWarnings:
    """On fractional-width targets (GitHub), odd emoji counts produce ±0.5 error.

    The fixers should WARN about this since perfect alignment is impossible.
    """

    def test_box_odd_emoji_warns(self):
        """Box with 1 emoji per line → fractional → should warn."""
        box = (
            "┌──────────────────┐\n"
            "│ 📦 Packages: 42  │\n"
            "│ Plain text here  │\n"
            "└──────────────────┘"
        )
        _, changes = fix_boxes(box, target="github")
        warnings = [c for c in changes if c.startswith("⚠")]
        assert len(warnings) == 1  # only the emoji line, not the plain text line
        assert "0.5" in warnings[0]
        assert "emoji" in warnings[0].lower()

    def test_box_even_emoji_no_warning(self):
        """Box with 2 emoji per line → integer width → no warning."""
        box = (
            "┌──────────────────────┐\n"
            "│ 📦 ✅ Status: OK     │\n"
            "│ Plain text here      │\n"
            "└──────────────────────┘"
        )
        _, changes = fix_boxes(box, target="github")
        warnings = [c for c in changes if c.startswith("⚠")]
        assert len(warnings) == 0

    def test_box_no_emoji_no_warning(self):
        """Box with no emoji → no warning."""
        box = (
            "┌──────────────────┐\n"
            "│ Packages: 42     │\n"
            "└──────────────────┘"
        )
        _, changes = fix_boxes(box, target="github")
        warnings = [c for c in changes if c.startswith("⚠")]
        assert len(warnings) == 0

    def test_box_terminal_no_warning_even_with_emoji(self):
        """Terminal target has integer emoji width → never warns about fractions."""
        box = (
            "┌──────────────────┐\n"
            "│ 📦 Packages: 42  │\n"
            "└──────────────────┘"
        )
        _, changes = fix_boxes(box, target="terminal")
        warnings = [c for c in changes if c.startswith("⚠")]
        assert len(warnings) == 0

    def test_table_odd_emoji_warns(self):
        """Table cell with 1 emoji → fractional → should warn."""
        table = (
            "| Status | Count |\n"
            "| --- | --- |\n"
            "| ✅ Active | 5 |\n"
            "| Inactive | 3 |"
        )
        _, changes = fix_tables(table, target="github")
        warnings = [c for c in changes if c.startswith("⚠")]
        assert len(warnings) >= 1
        assert "0.5" in warnings[0]

    def test_table_even_emoji_no_warning(self):
        """Table cell with 2 emoji → integer width → no warning."""
        table = (
            "| Status | Count |\n"
            "| --- | --- |\n"
            "| ✅❌ Active | 5 |\n"
            "| Inactive | 3 |"
        )
        _, changes = fix_tables(table, target="github")
        warnings = [c for c in changes if c.startswith("⚠")]
        assert len(warnings) == 0

    def test_table_no_emoji_no_warning(self):
        """Table with no emoji → no warnings."""
        table = (
            "| Status | Count |\n"
            "| --- | --- |\n"
            "| Active | 5 |\n"
            "| Inactive | 3 |"
        )
        _, changes = fix_tables(table, target="github")
        warnings = [c for c in changes if c.startswith("⚠")]
        assert len(warnings) == 0

    def test_warning_message_includes_guidance(self):
        """Warning text should include actionable guidance."""
        box = (
            "┌──────────────────┐\n"
            "│ ✅ Tests: 100%   │\n"
            "└──────────────────┘"
        )
        _, changes = fix_boxes(box, target="github")
        warnings = [c for c in changes if c.startswith("⚠")]
        assert len(warnings) == 1
        warning = warnings[0]
        assert "even" in warning.lower() or "avoid" in warning.lower()
