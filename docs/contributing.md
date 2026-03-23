---
layout: default
title: Contributing
---

# Contributing

## Development Setup

```bash
git clone https://github.com/ericchansen/aifmt.git
cd aifmt
pip install -e ".[dev]"
```

## Running Tests

```bash
pytest        # full suite (149+ tests)
pytest -v     # verbose
pytest tests/test_tree_fixer.py  # single file
```

## Linting

```bash
ruff check .
```

## The Golden Rule

> **Never use `len()` for visual alignment.**

`len("📦")` returns `1`, but the emoji occupies more than 1 column. Always use `visual_width()` or `visual_width_precise()`. This is the core insight behind everything in this project.

## Project Structure

- **`src/aifmt/lib/visual_width.py`** — Core: width calculation + rendering profiles
- **`src/aifmt/lib/box_fixer.py`** — ASCII/Unicode box border alignment
- **`src/aifmt/lib/table_fixer.py`** — Markdown table column padding
- **`src/aifmt/lib/bar_fixer.py`** — Progress bar width normalization
- **`src/aifmt/lib/tree_fixer.py`** — Tree diagram parse→model→re-render fixer
- **`src/aifmt/lib/mermaid_validator.py`** — Mermaid syntax validation
- **`src/aifmt/server.py`** — MCP server entry point
- **`tests/`** — One test file per module

## Rendering Profiles

The `target` parameter selects a `RenderProfile`. When adding fixers, always thread `target` through so callers can control which rendering profile is used.

| Target | Emoji Width | CJK Width |
|--------|-------------|-----------|
| `terminal` | 2.0 | 2.0 |
| `github` | 2.5 | 2.0 |

## Fractional Width Warnings

When a fixer detects fractional visual width (e.g., odd emoji count on GitHub), it must emit a ⚠ warning rather than silently producing imperfect output. Warnings should explain *why* and suggest alternatives.

## Adding a New Fixer

1. Create `src/aifmt/lib/<name>_fixer.py`
2. Export: `fix_<name>(text: str, *, target: str = "terminal") -> tuple[str, list[str]]`
3. Wire into `server.py`'s `fix()` and `validate()` tools
4. Add a `mode` option to `fix()`
5. Add tests in `tests/test_<name>_fixer.py`
6. Update docs

## Guidelines

- **Zero heavy dependencies.** MCP SDK + stdlib only.
- **Visual width everywhere.** Never `len()` for alignment.
- **Test edge cases.** Emoji, CJK, ANSI codes, mixed-width, empty input.
- **Return changes.** Every fixer returns what it fixed/warned.
- **Cross-platform.** Tests must pass on Linux, macOS, and Windows.

## Pull Requests

1. Fork and create a feature branch
2. Make changes with tests
3. `pytest` and `ruff check .` must both pass
4. Open a PR with a clear description
