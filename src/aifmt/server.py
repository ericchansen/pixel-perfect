"""aifmt MCP server.

Make visual text content just work. Provides tools to fix, validate, and
generate diagrams, tables, and box-drawing art for AI coding assistants.
"""

from __future__ import annotations

from mcp.server.fastmcp import FastMCP

from aifmt.lib.bar_fixer import fix_bars
from aifmt.lib.box_fixer import fix_boxes
from aifmt.lib.mermaid_validator import validate_mermaid
from aifmt.lib.table_fixer import fix_tables
from aifmt.lib.tree_fixer import fix_trees
from aifmt.lib.visual_width import list_profiles

mcp = FastMCP("aifmt")


@mcp.tool()
def targets() -> str:
    """List available rendering targets/profiles.

    Each target models how a specific platform renders monospace text.
    Use the target name with the ``fix`` and ``validate`` tools.

    Returns:
        A list of registered rendering profiles with descriptions.
    """
    profiles = list_profiles()
    lines = ["## Available rendering targets\n"]
    for p in profiles:
        desc = f" — {p.description}" if p.description else ""
        lines.append(f"- **{p.name}**{desc}  (emoji={p.emoji_width}, cjk={p.cjk_width})")
    return "\n".join(lines)


@mcp.tool()
def fix(
    content: str,
    mode: str = "all",
    target: str = "github",
) -> str:
    """Fix misaligned visual text content.

    Repairs broken ASCII/Unicode boxes, markdown tables, progress bars,
    and tree diagrams using visual-width-aware algorithms.

    Args:
        content: The text content to fix.
        mode: What to fix — "all", "boxes", "tables", "bars", or "trees". Default: "all".
        target: Rendering context — "github" for web/markdown rendering (default),
                "terminal" for terminal emulators. GitHub renders emoji wider than
                terminals do, so the padding adjustments differ.

    Returns:
        Fixed content with a summary of changes made.
    """
    all_changes: list[str] = []
    result = content

    if mode in ("all", "tables"):
        result, changes = fix_tables(result, target=target)
        all_changes.extend(changes)

    if mode in ("all", "bars"):
        result, changes = fix_bars(result)
        all_changes.extend(changes)

    if mode in ("all", "boxes"):
        result, changes = fix_boxes(result, target=target)
        all_changes.extend(changes)

    if mode in ("all", "trees"):
        result, changes = fix_trees(result, target=target)
        all_changes.extend(changes)

    if all_changes:
        fixes = [c for c in all_changes if not c.startswith("⚠")]
        warnings = [c for c in all_changes if c.startswith("⚠")]
        parts = []
        if fixes:
            parts.append("## Fixes applied\n" + "\n".join(f"- {c}" for c in fixes))
        if warnings:
            parts.append(
                "## ⚠ Alignment warnings\n"
                + "\n".join(f"- {c}" for c in warnings)
                + "\n\n_These lines cannot be perfectly aligned on this target. "
                "Consider removing emoji or using an even number of emoji per line._"
            )
        return f"{result}\n\n---\n" + "\n\n".join(parts)
    else:
        return f"{result}\n\n---\n_No alignment issues found._"


@mcp.tool()
def validate(
    content: str,
    checks: list[str] | None = None,
    target: str = "github",
) -> str:
    """Validate visual text content for alignment issues.

    Checks for misaligned boxes, tables, bars, tree diagrams, and Mermaid
    syntax errors without modifying the content.

    Args:
        content: The text content to validate.
        checks: Which checks to run — list of "boxes", "tables", "bars",
                "trees", "mermaid". Default: all checks.
        target: Rendering context — "github" (default) or "terminal".

    Returns:
        Report of issues found with line numbers and descriptions.
    """
    if checks is None:
        checks = ["boxes", "tables", "bars", "trees", "mermaid"]

    issues: list[str] = []

    if "tables" in checks:
        _, table_changes = fix_tables(content, target=target)
        if table_changes:
            issues.append("### Table alignment issues")
            issues.extend(f"- {c}" for c in table_changes)

    if "bars" in checks:
        _, bar_changes = fix_bars(content)
        if bar_changes:
            issues.append("### Bar chart issues")
            issues.extend(f"- {c}" for c in bar_changes)

    if "boxes" in checks:
        _, box_changes = fix_boxes(content, target=target)
        if box_changes:
            issues.append("### Box alignment issues")
            issues.extend(f"- {c}" for c in box_changes)

    if "trees" in checks:
        _, tree_changes = fix_trees(content, target=target)
        if tree_changes:
            issues.append("### Tree diagram issues")
            issues.extend(f"- {c}" for c in tree_changes)

    if "mermaid" in checks:
        mermaid_issues = validate_mermaid(content)
        if mermaid_issues:
            issues.append("### Mermaid syntax issues")
            for mi in mermaid_issues:
                issues.append(f"- Line {mi.line} [{mi.severity}]: {mi.message}")

    if issues:
        return "## Validation Report\n\n" + "\n".join(issues)
    else:
        return "✅ No visual alignment issues found."


@mcp.tool()
def generate(
    description: str,
    format: str = "mermaid",
    diagram_type: str = "flowchart",
) -> str:
    """Generate a diagram using a proper rendering engine.

    Routes to Mermaid (declarative code) or PlantUML (ASCII art) so the
    rendering engine handles layout — not the LLM.

    Args:
        description: What to diagram — describe the components and relationships.
        format: Output format — "mermaid", "plantuml-ascii", or "plantuml-unicode".
        diagram_type: Type of diagram — "flowchart", "sequence", "class", "state",
                      "er", or "architecture".

    Returns:
        Diagram code (Mermaid) or instructions for PlantUML rendering.
    """
    if format == "mermaid":
        type_map = {
            "flowchart": "flowchart TD",
            "sequence": "sequenceDiagram",
            "class": "classDiagram",
            "state": "stateDiagram-v2",
            "er": "erDiagram",
            "architecture": "flowchart TD",
        }
        diagram_start = type_map.get(diagram_type, "flowchart TD")

        return (
            f"Generate a Mermaid diagram for: {description}\n\n"
            f"Use this format:\n"
            f"```mermaid\n"
            f"{diagram_start}\n"
            f"    %% Add nodes and relationships here based on: {description}\n"
            f"```\n\n"
            f"**Rules for correct Mermaid:**\n"
            f"- Every node ID must be alphanumeric (no spaces, use camelCase)\n"
            f"- Use `-->` for arrows, `-->|label|` for labeled arrows\n"
            f"- Close all brackets: `[text]`, `{{text}}`, `(text)`\n"
            f"- For subgraphs: `subgraph Title` ... `end`\n"
        )
    elif format in ("plantuml-ascii", "plantuml-unicode"):
        flag = "-utxt" if format == "plantuml-unicode" else "-txt"
        return (
            f"To generate a PlantUML ASCII diagram:\n\n"
            f"1. Create a `.puml` file with the diagram definition\n"
            f"2. Run: `plantuml {flag} diagram.puml`\n"
            f"3. Read the output from `diagram.atxt` or `diagram.utxt`\n\n"
            f"The PlantUML engine handles all spatial layout correctly.\n"
            f"Description: {description}\n"
            f"Diagram type: {diagram_type}\n"
        )
    else:
        return f"Unknown format: {format}. Use 'mermaid', 'plantuml-ascii', or 'plantuml-unicode'."


def main() -> None:
    """Run the aifmt MCP server."""
    mcp.run()


if __name__ == "__main__":
    main()
