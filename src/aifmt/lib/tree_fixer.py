"""Fix misaligned tree diagrams using box-drawing characters.

Tree diagrams use ``│``, ``├──``, ``└──`` (and ASCII equivalents ``|``,
``+--``) to show hierarchical relationships.  LLMs frequently get the
indentation wrong — vertical pipes don't align with their children's
branch connectors, and leaf nodes lack connectors entirely.

Strategy: **parse → model → re-render**.

1. Find tree-shaped regions in the text.
2. Parse each region into a ``TreeNode`` hierarchy using a **stack-based
   parser** that relies on branch characters (├── / └──) as the primary
   structural signal — these are unambiguous even when column alignment
   is broken.
3. Re-render with perfect ``├──`` / ``└──`` / ``│`` alignment using a
   consistent 4-char indent per depth level.
"""

from __future__ import annotations

from dataclasses import dataclass, field

# ── Character sets ──────────────────────────────────────────────────

_PIPE_CHARS = frozenset("│|")
_BRANCH_CHARS = frozenset("├└")
_HORIZ_CHARS = frozenset("─—–-")
_ALL_TREE = (
    _PIPE_CHARS | _BRANCH_CHARS | frozenset("┌┐┘┤┬┴┼╭╮╯╰")
    | _HORIZ_CHARS | frozenset("+")
)

# Characters that form the tree-drawing prefix before content
_TREE_PREFIX = frozenset(" \t│|├└┌┐┘┤┬┴┼╭╮╯╰─—–-+")

# ── Data model ──────────────────────────────────────────────────────


@dataclass
class TreeNode:
    """A node in the parsed tree."""

    label: str
    continuation: list[str] = field(default_factory=list)
    children: list[TreeNode] = field(default_factory=list)


@dataclass
class _Entry:
    """Parsed representation of a single content-bearing tree line."""

    branch_col: int     # column of ├ or └ (-1 if no branch char)
    content: str        # text content after tree prefix
    has_tree_chars: bool  # whether line contains any tree drawing chars


# ── Public API ──────────────────────────────────────────────────────


def fix_trees(text: str, *, target: str = "terminal") -> tuple[str, list[str]]:
    """Fix misaligned tree diagrams in *text*.

    Returns ``(fixed_text, list_of_change_descriptions)``.
    """
    lines = text.split("\n")
    changes: list[str] = []
    regions = _find_tree_regions(lines)

    for start, end in reversed(regions):
        region = lines[start:end + 1]
        root = _parse_tree(region)
        if root is None:
            continue

        rendered = _render_tree(root)

        if rendered != region:
            changes.append(
                f"Fixed tree diagram alignment "
                f"(lines {start + 1}–{end + 1})"
            )
            lines[start:end + 1] = rendered

    return "\n".join(lines), changes


# ── Region detection ────────────────────────────────────────────────


def _is_tree_line(line: str) -> bool:
    """True if *line* looks like part of a tree diagram."""
    stripped = line.strip()
    if not stripped:
        return False
    return any(ch in _ALL_TREE for ch in stripped)


def _has_branch(lines: list[str], start: int, end: int) -> bool:
    for i in range(start, end + 1):
        for ch in lines[i]:
            if ch in _BRANCH_CHARS or ch == "+":
                return True
    return False


def _find_tree_regions(lines: list[str]) -> list[tuple[int, int]]:
    """Find contiguous regions that look like tree diagrams."""
    regions: list[tuple[int, int]] = []
    i = 0
    n = len(lines)

    while i < n:
        if _is_tree_line(lines[i]):
            start = i
            end = i

            # Look back: plain-text root line immediately before tree chars
            if start > 0:
                prev = lines[start - 1].strip()
                if (prev
                        and not prev.startswith("#")
                        and not _is_tree_line(lines[start - 1])):
                    start -= 1

            # Extend forward
            while end + 1 < n:
                nxt = lines[end + 1]
                if _is_tree_line(nxt):
                    end += 1
                elif not nxt.strip():
                    if end + 2 < n and _is_tree_line(lines[end + 2]):
                        end += 2
                    else:
                        break
                else:
                    indent = len(nxt) - len(nxt.lstrip())
                    if indent > 0:
                        end += 1
                    else:
                        break

            if _has_branch(lines, start, end) and end - start >= 1:
                regions.append((start, end))
            i = end + 1
        else:
            i += 1

    return regions


# ── Parsing helpers ─────────────────────────────────────────────────


def _find_deepest_branch(line: str) -> int:
    """Return column of the deepest ├ or └ in *line*, or -1."""
    col = -1
    for i, ch in enumerate(line):
        if ch in _BRANCH_CHARS:
            col = i
    return col


def _strip_content(line: str) -> str:
    """Return content text after tree-drawing prefix."""
    for i, ch in enumerate(line):
        if ch not in _TREE_PREFIX:
            return line[i:]
    return ""


def _line_has_tree_chars(line: str) -> bool:
    """True if line has structural tree chars (│├└) in its prefix area.

    We only look at the leading portion before text content starts —
    hyphens inside words like ``weekly-impact-report`` don't count.
    """
    for ch in line:
        if ch in _PIPE_CHARS | _BRANCH_CHARS:
            return True
        if ch not in _TREE_PREFIX:
            return False
    return False


def _parse_entries(region_lines: list[str]) -> list[_Entry]:
    """Convert region lines into a flat list of content-bearing entries."""
    entries: list[_Entry] = []
    for line in region_lines:
        content = _strip_content(line)
        if not content:
            continue
        branch_col = _find_deepest_branch(line)
        has_tree = _line_has_tree_chars(line)
        entries.append(_Entry(branch_col, content, has_tree))
    return entries


# ── Stack-based tree parser ─────────────────────────────────────────


def _parse_tree(region_lines: list[str]) -> TreeNode | None:
    """Parse tree region into a TreeNode hierarchy.

    Uses a stack-based algorithm where branch characters (├── / └──)
    are the primary structural signal.  The branch column defines depth:
    a new branch at the same column as an existing one is a sibling;
    a branch at a deeper column is a child.

    Non-branch lines (orphaned content, continuations) are attached to
    the most recent branch node on the stack.
    """
    entries = _parse_entries(region_lines)
    if not entries:
        return None

    # First entry is the root
    root = TreeNode(label=entries[0].content)
    if len(entries) <= 1:
        return root

    # Stack: list of (branch_col, TreeNode) — shallowest at bottom
    stack: list[tuple[int, TreeNode]] = [(-1, root)]
    last_node = root

    for entry in entries[1:]:
        if entry.branch_col >= 0:
            # ── Branch entry (├── or └──) — definite child ──
            # Pop stack until we find a node at a shallower branch column
            while (len(stack) > 1
                   and stack[-1][0] >= entry.branch_col):
                stack.pop()

            parent = stack[-1][1]
            node = TreeNode(label=entry.content)
            parent.children.append(node)
            stack.append((entry.branch_col, node))
            last_node = node

        elif not entry.has_tree_chars:
            # ── No tree chars at all — continuation text ──
            last_node.continuation.append(entry.content)

        elif entry.content.startswith("("):
            # ── Parenthetical — continuation of previous node ──
            last_node.continuation.append(entry.content)

        else:
            # ── Orphaned content with tree chars — child of stack top ──
            parent = stack[-1][1]
            node = TreeNode(label=entry.content)
            parent.children.append(node)
            last_node = node

    return root


# ── Tree rendering ──────────────────────────────────────────────────


def _render_tree(root: TreeNode) -> list[str]:
    """Render a TreeNode into correctly-aligned lines."""
    out: list[str] = [root.label]
    for cont in root.continuation:
        out.append(cont)
    _render_children(out, root.children, "")
    return out


def _render_children(
    out: list[str],
    children: list[TreeNode],
    prefix: str,
) -> None:
    """Render *children* with correct ├──/└── connectors and │ pipes."""
    for i, child in enumerate(children):
        is_last = (i == len(children) - 1)
        connector = "└── " if is_last else "├── "
        cont_prefix = "    " if is_last else "│   "

        out.append(f"{prefix}{connector}{child.label}")

        for cont in child.continuation:
            out.append(f"{prefix}{cont_prefix}{cont}")

        if child.children:
            _render_children(out, child.children, prefix + cont_prefix)
