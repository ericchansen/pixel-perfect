# aifmt Agent Instructions

## What is this project?

aifmt is an MCP server + Copilot CLI plugin that makes visual text content
"just work" in AI coding assistants. It fixes, validates, and generates diagrams,
tables, box-drawing art, and tree diagrams.

## ⚠️ CRITICAL: You Cannot Verify Rendering — Humans Must

**This is the single most important rule for working on this project.**

You (the AI) **cannot see how text renders** on GitHub, in terminals, or in any
visual context. You can read source code and count characters, but you **cannot
verify** that a box, table, or tree diagram actually looks correct when rendered.

**Every** visual output claim must be verified by a human looking at the rendered
result. This means:

1. **Never say "this looks correct" or "this is fixed"** — you don't know that.
   Say "this is what the fixer produces — please verify on GitHub."
2. **Never hand-write visual content** (boxes, tables, trees) and claim it's correct.
   Always generate it by running the actual fixer code, then ask the human to verify.
3. **When writing tests**, the expected output for visual content should be
   human-verified, not assumed. Use `# FIXME: human-verify` comments for unverified
   expected values.
4. **When fixing a visual bug**, push to GitHub and ask the user to check the
   rendered result. A passing test does NOT mean the output renders correctly —
   the test might be checking the wrong thing.
5. **The fixer's math can be wrong even when tests pass.** We discovered that
   emoji = 2.5 cols on GitHub (not 2.0) only because a human looked at screenshots.
   No amount of unit testing would have caught that.

### The Development Loop

```
You write code → You run tests → Tests pass → You push →
Human checks rendered output → Human reports what's wrong →
You fix → repeat
```

**Do NOT skip the human verification step.** Do NOT claim work is done until the
human confirms the rendered output is correct.

## Key Discovery: GitHub Emoji = 2.5 Columns

Through empirical testing (human screenshots), we discovered:

- **Terminal emulators**: emoji = 2.0 monospace columns (Unicode standard)
- **GitHub markdown code blocks**: emoji = **2.5** monospace columns (fractional!)
- **Even emoji count** per line → integer total → perfect alignment possible
- **Odd emoji count** per line → fractional total → **impossible** to align (±0.5)
- When perfect alignment is impossible, the tool must **warn**, not silently produce
  broken output

This discovery could NOT have been made by reading code or running tests. It required
a human looking at GitHub rendering and comparing pixel positions.

## Architecture

- `src/aifmt/` — Main package
  - `server.py` — MCP server (fix, validate, generate, targets tools)
  - `lib/visual_width.py` — Core: RenderProfile system with float widths,
    `visual_width()`, `visual_width_precise()`, profile registry
  - `lib/box_fixer.py` — ASCII/Unicode box border alignment
  - `lib/table_fixer.py` — Markdown table column padding
  - `lib/bar_fixer.py` — Progress bar normalization
  - `lib/tree_fixer.py` — Tree diagram parse→model→re-render fixer
  - `lib/mermaid_validator.py` — Mermaid syntax checking
- `copilot-plugin/` — Copilot CLI plugin (SKILL.md + instructions)
- `tests/` — pytest suite (149+ tests)
  - `test_real_world.py` — Tests from actual broken content found in the wild
  - `test_profiles.py` — Rendering profile system + fractional width warnings
  - `test_tree_fixer.py` — Tree diagram fixing (hierarchy, continuations, MSX integration)

## Rendering Profiles

The `target` parameter (default: `"github"`) selects a `RenderProfile`:

| Target | Emoji Width | CJK Width | Notes |
|--------|-------------|-----------|-------|
| `terminal` | 2.0 | 2.0 | Unicode standard (EAW) |
| `github` | 2.5 | 2.0 | Empirically measured |

Custom profiles via `register_profile(RenderProfile(...))`. All fixers must
thread the `target` parameter through to `visual_width_precise()`.

## Code Style

- Python 3.10+, type hints everywhere
- Lint with `ruff check .`
- Test with `pytest`
- Zero heavy dependencies — stdlib + `mcp` SDK only
- All text measurement MUST use `visual_width()` / `visual_width_precise()`, never `len()`
- Fixers return `tuple[str, list[str]]` — (fixed_text, changes/warnings)
- Warnings start with `⚠` and explain WHY perfect alignment is impossible
- Never silently produce imperfect output — warn or error

## Git

- Conventional commits: `feat:`, `fix:`, `docs:`, `test:`, `chore:`
- Currently force-pushing to master (pre-release)
- GitHub auth: use `ericchansen` account (personal), not `erichansen_microsoft`
