---
layout: default
title: Home
---

# aifmt

> Make visual text content just work.

An MCP server + Copilot CLI plugin that fixes, validates, and generates visual text content — boxes, tables, bars, tree diagrams — for AI coding assistants.

## The Problem

LLMs generate text token-by-token with **no concept of column alignment**. `len("📦")` returns `1`, but the character renders wider on screen. This causes every AI-generated box, table, and tree diagram to be misaligned.

Before (LLM output — borders don't line up):

```
┌────────────────────┐
│ Status: deployed     │
│ Tests: 142 passing │
│ Coverage: 98.5%       │
└────────────────────┘
```

After `fix(content, mode="boxes")`:

```
┌────────────────────┐
│ Status: deployed   │
│ Tests: 142 passing │
│ Coverage: 98.5%    │
└────────────────────┘
```

aifmt replaces `len()` with rendering-profile-aware visual width measurement so alignment is always correct.

## Key Discovery: GitHub Emoji = 2.5 Columns

Through empirical testing, we discovered that **GitHub renders emoji at 2.5 monospace columns** — not the 2.0 that Unicode specifies and terminals use.

| Platform | Emoji width | CJK width |
|----------|------------|-----------|
| Terminal emulators | 2.0 cols | 2.0 cols |
| **GitHub markdown** | **2.5 cols** | 2.0 cols |

This has a critical consequence:

- **Even emoji count** per line (0, 2, 4…) → integer total → ✅ perfect alignment
- **Odd emoji count** per line (1, 3, 5…) → fractional total → ❌ impossible to align

aifmt detects this and emits ⚠ warnings instead of silently producing broken output.

[Read the full discovery story →](discovery)

## MCP Tools

| Tool | Description |
|------|-------------|
| [`fix`](tools#fix) | Repair misaligned boxes, tables, bars, and tree diagrams |
| [`validate`](tools#validate) | Check for alignment issues without modifying |
| [`generate`](tools#generate) | Create diagrams via Mermaid or PlantUML |
| [`targets`](tools#targets) | List rendering profiles (GitHub, terminal, custom) |

## Quick Links

- [Getting Started](getting-started) — Install and configure
- [Tools Reference](tools) — Detailed tool documentation with examples
- [The 2.5 Discovery](discovery) — How we found the fractional emoji width
- [Python API](api) — Use the library directly
- [Contributing](contributing) — Development setup and guidelines
