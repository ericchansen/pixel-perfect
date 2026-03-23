---
layout: default
title: Python API
---

# Python API

aifmt's core library is usable directly from Python — no MCP required.

## Visual Width

```python
from aifmt.lib.visual_width import (
    visual_width,
    visual_width_precise,
    visual_pad,
    visual_truncate,
    visual_center,
    strip_ansi,
)

# Integer width (rounds up) — use for padding decisions
visual_width("hello")                        # → 5
visual_width("📦 box", target="terminal")    # → 6  (📦 = 2.0 + space + 3)
visual_width("📦 box", target="github")      # → 7  (📦 = 2.5, rounded up)
visual_width("古池")                          # → 4  (each CJK char = 2 cols)
visual_width("\033[31mred\033[0m")            # → 3  (ANSI codes = 0 cols)

# Precise float width — for alignment feasibility checks
visual_width_precise("📦", target="github")   # → 2.5
visual_width_precise("📦📦", target="github") # → 5.0  (even count → integer)

# Padding, truncation, centering
visual_pad("📦", 6, target="github")          # → "📦   "
visual_pad("hi", 10, align="center")          # → "    hi    "
visual_truncate("hello world", 8)             # → "hello w…"
visual_center("title", 20)                    # → "       title        "
```

## Rendering Profiles

```python
from aifmt.lib.visual_width import (
    get_profile,
    list_profiles,
    register_profile,
    RenderProfile,
)

# Query built-in profiles
gh = get_profile("github")
gh.emoji_width    # → 2.5
gh.cjk_width      # → 2.0

term = get_profile("terminal")
term.emoji_width   # → 2.0

# List all registered profiles
for p in list_profiles():
    print(f"{p.name}: emoji={p.emoji_width}")

# Register a custom profile
register_profile(RenderProfile(
    name="slack",
    emoji_width=2.0,
    cjk_width=2.0,
    description="Slack message rendering",
))
```

## Fixers

All fixers return `tuple[str, list[str]]` — the fixed text and a list of change/warning descriptions.

```python
from aifmt.lib.box_fixer import fix_boxes
from aifmt.lib.table_fixer import fix_tables
from aifmt.lib.bar_fixer import fix_bars
from aifmt.lib.tree_fixer import fix_trees

# All fixers accept a target parameter
fixed, changes = fix_boxes(text, target="github")
fixed, changes = fix_tables(text, target="github")
fixed, changes = fix_bars(text)
fixed, changes = fix_trees(text, target="github")

# Check for warnings (⚠ = perfect alignment impossible)
warnings = [c for c in changes if c.startswith("⚠")]
```

## Mermaid Validator

```python
from aifmt.lib.mermaid_validator import validate_mermaid

issues = validate_mermaid(markdown_text)
for issue in issues:
    print(f"Line {issue.line} [{issue.severity}]: {issue.message}")
```
