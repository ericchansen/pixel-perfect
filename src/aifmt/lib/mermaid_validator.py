"""Validate Mermaid diagram syntax in markdown code blocks.

Pure regex-based validation — zero external dependencies.  Checks for common
authoring mistakes such as missing diagram type declarations, empty blocks,
and unclosed brackets.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

# Recognised Mermaid diagram types (case-insensitive first word)
_DIAGRAM_TYPES = {
    "flowchart",
    "graph",
    "sequencediagram",
    "classdiagram",
    "statediagram",
    "erdiagram",
    "journey",
    "gantt",
    "pie",
    "quadrantchart",
    "requirementdiagram",
    "gitgraph",
    "mindmap",
    "timeline",
    "zenuml",
    "sankey",
    "xychart",
    "block",
}

# Fenced mermaid code block
_MERMAID_BLOCK_RE = re.compile(
    r"^```mermaid\s*\n(.*?)^```",
    re.MULTILINE | re.DOTALL,
)

# Brackets we track (openers → expected closers)
_BRACKET_PAIRS = {"[": "]", "{": "}", "(": ")"}
_CLOSERS = set(_BRACKET_PAIRS.values())

# Valid arrow patterns for flowchart / graph
_FLOWCHART_ARROWS = re.compile(
    r"-->|---|-\.->"
    r"|==>|===|-->"
    r"|-\.\->|--[ox]|<-->"
    r"|-->|-->"
)

# sequenceDiagram arrow patterns
_SEQ_ARROWS = re.compile(r"->>|-->>|->|-->|-x|--x|-\)|--\)")


@dataclass
class MermaidIssue:
    """A single validation issue within a mermaid block."""

    line: int  # 1-based line number within the mermaid block
    message: str  # Human-readable description
    severity: str  # "error" or "warning"


def _validate_block(block_text: str) -> list[MermaidIssue]:
    """Validate a single mermaid block's content."""
    issues: list[MermaidIssue] = []
    raw_lines = block_text.split("\n")

    # Strip blank / whitespace-only lines for content analysis
    content_lines = [ln for ln in raw_lines if ln.strip()]

    # --- Empty block -------------------------------------------------------
    if not content_lines:
        issues.append(MermaidIssue(line=1, message="Empty mermaid block", severity="error"))
        return issues

    # --- Diagram type declaration ------------------------------------------
    first_token = content_lines[0].strip().split()[0].rstrip(":")  # e.g. "flowchart"
    # Also handle "---" YAML front-matter — skip it
    diagram_type: str | None = None

    for raw_idx, raw_line in enumerate(raw_lines, start=1):
        token = raw_line.strip().split()[0] if raw_line.strip() else ""
        token_lower = token.rstrip(":").lower()
        # Accept "graph TD", "flowchart LR", "sequenceDiagram", etc.
        if token_lower in _DIAGRAM_TYPES:
            diagram_type = token_lower
            break

    if diagram_type is None:
        issues.append(
            MermaidIssue(
                line=1,
                message=f"Missing or unrecognised diagram type (first token: '{first_token}')",
                severity="error",
            )
        )

    # --- Per-line checks ---------------------------------------------------
    for line_no, raw_line in enumerate(raw_lines, start=1):
        stripped = raw_line.strip()
        if not stripped or stripped.startswith("%%"):
            continue  # blank or comment

        # Unclosed brackets on this line
        _check_brackets(stripped, line_no, issues)

    return issues


def _check_brackets(line: str, line_no: int, issues: list[MermaidIssue]) -> None:
    """Check for unmatched brackets within *line*.

    Brackets inside quoted strings are ignored.
    """
    stack: list[tuple[str, int]] = []
    in_quote: str | None = None

    for col, ch in enumerate(line):
        # Track quoted regions
        if ch in ('"', "'"):
            if in_quote == ch:
                in_quote = None
            elif in_quote is None:
                in_quote = ch
            continue

        if in_quote:
            continue

        if ch in _BRACKET_PAIRS:
            stack.append((ch, col))
        elif ch in _CLOSERS:
            if stack and _BRACKET_PAIRS.get(stack[-1][0]) == ch:
                stack.pop()
            else:
                issues.append(
                    MermaidIssue(
                        line=line_no,
                        message=f"Unexpected closing '{ch}' at column {col + 1}",
                        severity="error",
                    )
                )

    for opener, col in stack:
        issues.append(
            MermaidIssue(
                line=line_no,
                message=f"Unclosed '{opener}' opened at column {col + 1}",
                severity="error",
            )
        )


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def validate_mermaid(text: str) -> list[MermaidIssue]:
    """Validate all mermaid code blocks in *text*.

    Returns a list of :class:`MermaidIssue` instances.  An empty list means
    every mermaid block passed validation (or there were no blocks).
    """
    all_issues: list[MermaidIssue] = []

    for match in _MERMAID_BLOCK_RE.finditer(text):
        block_content = match.group(1)
        # Compute the 1-based line offset of this block within the source text
        text[: match.start()].count("\n") + 2  # +1 for 1-based, +1 for the ```mermaid line

        block_issues = _validate_block(block_content)

        # Adjust line numbers to be relative to the block (already 1-based
        # inside _validate_block), so we leave them as-is.  If the caller
        # needs absolute line numbers they can add block_start_line - 1.
        all_issues.extend(block_issues)

    return all_issues
