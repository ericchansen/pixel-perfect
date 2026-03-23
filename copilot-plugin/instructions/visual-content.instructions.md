## Visual Content Guidelines

### Diagrams
- **NEVER use ASCII art** for architecture diagrams, flowcharts, or sequence diagrams in markdown files
- **Use Mermaid** (```mermaid code blocks) for all diagrams in markdown documentation
- Mermaid renders natively on GitHub, GitLab, Obsidian, and VS Code
- For terminal output only (not markdown), use PlantUML ASCII mode (`plantuml -utxt`)
- When generating box-drawing for terminal output, count visual width not string length

### Tables
- When generating markdown tables, measure column widths by **visual width** (display columns), not `len()`
- **Emoji width depends on the rendering target:**
  - **Terminal emulators:** emoji = 2 monospace columns (Unicode standard)
  - **GitHub markdown code blocks:** emoji ≈ 2.5 monospace columns (empirically measured)
- CJK characters occupy 2 columns in both targets: `古` = 2 cols
- ANSI escape codes occupy 0 columns
- **When creating tables/boxes for GitHub markdown, use an EVEN number of emoji per line/cell** (0, 2, 4…) — even counts produce integer total widths and guarantee perfect alignment
- **Odd emoji counts per line CANNOT be perfectly aligned on GitHub** — the fractional (x.5) total width makes exact spacing impossible. Warn the user or avoid emoji in those cells
- After generating any table with emoji or wide characters, verify alignment

### Terminal Output Code
- When writing code that prints boxes, tables, or aligned text to a terminal:
  - Use a visual-width function (e.g., `unicodedata.east_asian_width()`) for all alignment
  - Never use `len()`, `.length`, or `strlen()` for padding calculations
  - Account for emoji being 2 columns wide
  - Account for ANSI escape codes being 0 columns wide
- Python: use `unicodedata.east_asian_width(ch)` — `"W"` and `"F"` mean 2 columns
- JavaScript: use the `string-width` npm package
- Go: use `go.uber.org/runewidth`

### Progress Bars
- When generating progress bars (`████░░░░`), ensure fill + empty segments sum to the intended total width
- When displaying percentages alongside bars, verify the fill ratio matches the percentage
- Keep bar widths consistent within groups of bars displayed together

### After Generating Visual Content
- If the `aifmt` MCP server is available, call `validate` (with `target="github"` for markdown, `target="terminal"` for CLI output) on the generated content
- **Check for ⚠ warnings in the response** — these indicate perfect alignment is not achievable (e.g., odd emoji counts on GitHub)
- If warnings are present, **do NOT silently present the content as fixed** — inform the user that perfect alignment is not possible and suggest alternatives (remove emoji, use even emoji counts, or use Mermaid)
- Fix any fixable issues before presenting to the user
