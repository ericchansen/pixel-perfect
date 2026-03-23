---
layout: default
title: Getting Started
---

# Getting Started

## Installation

### pip

```bash
pip install aifmt
```

### uvx (no install required)

```bash
uvx aifmt
```

### From source

```bash
git clone https://github.com/ericchansen/aifmt.git
cd aifmt
pip install -e .
```

## MCP Client Configuration

Add aifmt to your MCP client and all four tools are instantly available.

### GitHub Copilot CLI

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

### Claude Code

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

### VS Code (Copilot Chat)

Add to `.vscode/mcp.json`:

```json
{
  "servers": {
    "aifmt": {
      "command": "uvx",
      "args": ["aifmt"]
    }
  }
}
```

### Cursor

Add to `.cursor/mcp.json`:

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

### Windsurf

Add to `~/.codeium/windsurf/mcp_config.json`:

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

### Gemini CLI

Add to `~/.gemini/settings.json`:

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

## Copilot CLI Plugin

aifmt ships with a Copilot CLI skill and custom instructions for prevention:

- **`copilot-plugin/skills/aifmt/SKILL.md`** — Teaches the assistant when and how to use all four tools
- **`copilot-plugin/instructions/visual-content.instructions.md`** — Prevention rules: use `visual_width()` not `len()`, even emoji counts for GitHub, prefer Mermaid over ASCII art

Copy these into your Copilot CLI plugin directory to enable automatic fixing and prevention.
