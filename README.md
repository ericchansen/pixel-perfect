# aifmt

> Make visual text content just work.

**An MCP server that fixes, validates, and generates visual text content for AI coding assistants.**

[![Tests](https://github.com/ericchansen/aifmt/actions/workflows/ci.yml/badge.svg)](https://github.com/ericchansen/aifmt/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://python.org)

---

LLMs can't count visual columns. `len("📦")` returns 1, but it renders wider. Every AI-generated box, table, and tree diagram ends up misaligned. aifmt fixes it.

## Install

```bash
pip install aifmt
```

## Configure

Add to your MCP client (Copilot CLI, Claude Code, Cursor, VS Code, Windsurf, Gemini CLI):

```json
{
  "mcpServers": {
    "aifmt": {
      "command": "uvx",
      "args": ["aifmt"]
    }
  }
}
```

## Tools

| Tool | Description |
|------|-------------|
| `fix` | Repair misaligned boxes, tables, bars, and tree diagrams |
| `validate` | Check for alignment issues without modifying |
| `generate` | Create diagrams via Mermaid or PlantUML |
| `targets` | List rendering profiles (GitHub, terminal, custom) |

## Key Insight

GitHub renders emoji at **2.5 monospace columns** — not 2.0. aifmt uses rendering-profile-aware width calculation to handle this. [Read how we discovered it →](https://ericchansen.github.io/aifmt/discovery)

## Documentation

📖 **[ericchansen.github.io/aifmt](https://ericchansen.github.io/aifmt/)**

- [Getting Started](https://ericchansen.github.io/aifmt/getting-started) — Install and configure
- [Tools Reference](https://ericchansen.github.io/aifmt/tools) — fix, validate, generate, targets
- [Python API](https://ericchansen.github.io/aifmt/api) — Use the library directly
- [The 2.5 Discovery](https://ericchansen.github.io/aifmt/discovery) — Fractional emoji width story
- [Contributing](https://ericchansen.github.io/aifmt/contributing) — Development setup and guidelines

## License

[MIT](LICENSE)
