# Where's Waldo Rick - Visual Regression MCP Server

A Model Context Protocol (MCP) server that brings **agentic vision capabilities** to Claude Code for visual regression testing using Gemini 3 Flash.

## Overview

Never again have ambiguous conversations about visual changes. See exactly what changed, circled and annotated, with intended vs unintended change detection.

### Problem Solved

- Developer works for hours on UI changes
- Build passes, code is "clean"
- You open the app... same exact layout
- You ask: "What specifically changed?"
- Dev says: "We added 2 pixels to the card"
- You ask: "Where? Top? Bottom? Inside the box? Around it?"
- 😤 Wasted time, unclear communication

### Solution

Where's Waldo Rick provides:
1. Screenshot capture from multiple platforms (macOS, iOS Simulator, Web)
2. Pixel-perfect comparison with configurable thresholds
3. Agentic vision analysis using Gemini 3 Flash (iterative zoom/crop/annotate)
4. Expected vs unintended change detection
5. Conversational investigation ("Not that box, the child item")

## Installation

### Requirements

- Python 3.10+
- Gemini API key (free tier: 15 requests/minute)

### Install from GitHub

```bash
# Install via uvx
uvx --from git+https://github.com/bretbouchard/gemini-vision-mcp wheres_waldo.server

# Or install locally
pip install -e .
```

### Configure Claude Code

Add to your Claude Code MCP configuration (`~/.claude/mcp.json` or project-specific):

```json
{
  "mcpServers": {
    "wheres-waldo-rick": {
      "command": "uvx",
      "args": ["--from", "git+https://github.com/bretbouchard/gemini-vision-mcp", "wheres_waldo.server"],
      "env": {
        "GEMINI_API_KEY": "your-api-key-here"
      }
    }
  }
}
```

## Usage

### Basic Workflow

```bash
# 1. Declare expected changes before work
/visual:prepare "Card padding increases by 2px, button moves to right"

# 2. Capture baseline screenshot
/visual:capture "Phase 3 - Before card update"

# 3. Development happens...

# 4. Capture current state
/visual:capture "Phase 4 - After card update"

# 5. Compare and see all changes
/visual:compare screenshots/phases/3-before.png screenshots/phases/4-after.png
```

### MCP Tools

#### `visual_capture`
Capture a screenshot and store it for visual regression testing.

```python
await visual_capture(
    name="Phase 3 - Before card update",
    platform="macos"  # auto, macos, ios, web
)
```

#### `visual_prepare`
Declare a baseline with expected changes before development.

```python
await visual_prepare(
    phase="Phase 3 - Card Layout Update",
    expected_changes="Card padding increases by 2px, button moves to right"
)
```

#### `visual_compare`
Compare two screenshots with pixel-level precision and agentic vision.

```python
await visual_compare(
    before_path="screenshots/phases/3-before.png",
    after_path="screenshots/phases/4-after.png",
    threshold=2  # 1px, 2px, or 3px
)
```

#### `visual_cleanup`
Clean up old screenshots and cache.

```python
await visual_cleanup(retention_days=7)
```

## Development

### Setup

```bash
# Clone repository
git clone https://github.com/bretbouchard/gemini-vision-mcp
cd gemini-vision-mcp

# Install in development mode
pip install -e ".[dev]"

# Run tests
pytest

# Format code
black src/
ruff check src/
```

### Project Structure

```
src/wheres_waldo/
├── __init__.py
├── server.py          # MCP server with tool definitions
├── models/            # Pydantic domain models
├── services/          # Business logic (capture, compare, storage)
├── tools/             # MCP tool implementations
└── utils/             # Logging, hashing, path helpers
```

## Roadmap

- [x] Phase 1: Foundation (MCP server skeleton, types, storage)
- [ ] Phase 2: Capture & Baselines (multi-platform screenshots)
- [ ] Phase 3: Comparison Engine (OpenCV + Gemini integration) 🔥 HIGH RISK
- [ ] Phase 4: Operations (caching, progressive resolution, reporting)
- [ ] Phase 5: Polish (conversational investigation)

See [ROADMAP.md](.planning/ROADMAP.md) for complete execution plan.

## Contributing

Contributions welcome! Please read [REQUIREMENTS.md](.planning/REQUIREMENTS.md) and [ROADMAP.md](.planning/ROADMAP.md) before contributing.

## License

MIT License - See LICENSE file for details

## Acknowledgments

Built with:
- [MCP Python SDK](https://github.com/modelcontextprotocol/python-sdk)
- [FastMCP](https://github.com/jlowin/fastmcp)
- [Google Gemini 3 Flash](https://blog.google/innovation-and-ai/technology/developers-tools/agentic-vision-gemini-3-flash/)
- [OpenCV](https://opencv.org/)
- [MSS](https://github.com/BoboTiG/python-mss)

---

**Generated with [Claude Code](https://claude.com/claude-code) via [Happy](https://happy.engineering)**
