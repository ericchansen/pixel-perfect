---
layout: default
title: Tools Reference
---

# Tools Reference

## `fix`

Repair misaligned visual content using rendering-profile-aware width calculation.

**Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `content` | `str` | required | The text content to fix |
| `mode` | `str` | `"all"` | What to fix: `"all"`, `"boxes"`, `"tables"`, `"bars"`, or `"trees"` |
| `target` | `str` | `"github"` | Rendering target: `"github"` or `"terminal"` |

### Fixing boxes

Boxes with ragged right borders (the most common LLM alignment failure):

```python
fix(content, mode="boxes", target="github")
```

Before:

```
┌────────────────────┐
│ Status: deployed     │
│ Tests: 142 passing │
│ Coverage: 98.5%       │
└────────────────────┘
```

After:

```
┌────────────────────┐
│ Status: deployed   │
│ Tests: 142 passing │
│ Coverage: 98.5%    │
└────────────────────┘
```

### Fixing tables

Markdown tables with misaligned columns:

```python
fix(content, mode="tables", target="github")
```

Before:

```
| Name | Status | Count |
| --- | --- | --- |
| numpy | active | 1,200,000 |
| broken-pkg | deprecated | 42 |
| requests | active | 3,500,000 |
```

After:

```
| Name       | Status     | Count     |
| ---------- | ---------- | --------- |
| numpy      | active     | 1,200,000 |
| broken-pkg | deprecated | 42        |
| requests   | active     | 3,500,000 |
```

### Fixing progress bars

Bars with inconsistent widths within a group:

```python
fix(content, mode="bars")
```

Before (bars have different total widths):

```
Build    ████████████████░░░░ 80%
Tests    ██████████░░░░░░░░░░░░ 60%
Lint     ████████████████████████ 100%
```

After (all normalized to same total width, ratios match percentages):

```
Build    ███████████████████░░░░░ 80%
Tests    ██████████████░░░░░░░░░░ 60%
Lint     ████████████████████████ 100%
```

### Fixing tree diagrams

Tree diagrams with misaligned pipes, orphaned content, and missing connectors:

```python
fix(content, mode="trees")
```

Before (pipes don't align with branches, content lacks connectors):

```
Project Root
  │
  ├── src/
  │           │
  │     ├── auth/
  │     │
  │     └── api/
  │
  │       utils.py
  └── tests/
```

After (correct ├──/└──/│ alignment, orphaned content gets connectors):

```
Project Root
├── src/
│   ├── auth/
│   └── api/
│       └── utils.py
└── tests/
```

### Emoji and the ⚠ warning system

When content contains an **odd number of emoji per line** and the target is `"github"`, perfect alignment is mathematically impossible (each emoji is 2.5 cols — odd × 2.5 = fractional). The fixer does its best and emits a warning:

```
⚠ Line 2: alignment off by 0.5 cols (1 emoji — odd count). On github,
  emoji are fractional width. Use an even number of emoji per line, or
  avoid emoji in bordered content for this target.
```

**To avoid warnings:**
- Use **even** emoji counts per line/cell (0, 2, 4…)
- Or remove emoji from bordered/tabular content
- Or use `target="terminal"` if the content is for terminal display

---

## `validate`

Check content for alignment issues without modifying it. Returns a report.

**Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `content` | `str` | required | The text content to validate |
| `checks` | `list[str]` | all | Which checks: `"boxes"`, `"tables"`, `"bars"`, `"trees"`, `"mermaid"` |
| `target` | `str` | `"github"` | Rendering target |

**Example output:**

```
## Validation Report

### Table alignment issues
- Fixed table alignment (3 columns, 5 data rows)

### Tree diagram issues
- Fixed tree diagram alignment (lines 5–18)

### Mermaid syntax issues
- Line 3 [error]: Unclosed '[' opened at column 5
```

---

## `generate`

Create diagrams using rendering engines (Mermaid, PlantUML) so the engine handles layout — not the LLM.

**Parameters:**

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `description` | `str` | required | What to diagram |
| `format` | `str` | `"mermaid"` | `"mermaid"`, `"plantuml-ascii"`, or `"plantuml-unicode"` |
| `diagram_type` | `str` | `"flowchart"` | `"flowchart"`, `"sequence"`, `"class"`, `"state"`, `"er"`, `"architecture"` |

---

## `targets`

List available rendering profiles with their width settings.

**Parameters:** None.

**Example output:**

```
## Available rendering targets

- **terminal** — Unicode East Asian Width standard (emoji=2.0, cjk=2.0)
- **github** — GitHub markdown code blocks (emoji=2.5, cjk=2.0)
```
