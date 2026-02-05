# Where's Waldo Rick - Setup Instructions

## Part 1: Get Gemini API Key

1. Go to https://aistudio.google.com/app/apikey
2. Create a new API key (or use existing)
3. Copy the API key

## Part 2: Configure MCP Server

### Option A: Global Configuration (Recommended for Alpha Rick)

1. Edit `~/.claude/mcp.json`:
```json
{
  "mcpServers": {
    "wheres-waldo-rick": {
      "command": "uvx",
      "args": [
        "--from",
        "git+https://github.com/bretbouchard/gemini-vision-mcp",
        "wheres_waldo.server"
      ],
      "env": {
        "GEMINI_API_KEY": "your-actual-api-key-here"
      }
    }
  }
}
```

2. Replace `your-actual-api-key-here` with your Gemini API key

3. Restart Claude Code

### Option B: Project-Specific Configuration

1. Create `~/your-project/.claude/mcp.json`:
```json
{
  "mcpServers": {
    "wheres-waldo-rick": {
      "command": "uvx",
      "args": [
        "--from",
        "git+https://github.com/bretbouchard/gemini-vision-mcp",
        "wheres_waldo.server"
      ],
      "env": {
        "GEMINI_API_KEY": "your-actual-api-key-here"
      }
    }
  }
}
```

## Part 3: Verify Installation

After restarting Claude Code, the tools should be available:

```
Available Tools:
- visual_capture: Capture screenshots from macOS/iOS/Web
- visual_prepare: Declare baselines with expected changes
- visual_compare: Compare screenshots with agentic vision
- visual_cleanup: Clean up old screenshots
- visual_list: List screenshots and baselines
```

## Part 4: Test the Tools

### Test 1: Capture a Screenshot

```
/visual_capture "Test screenshot" platform="macos"
```

### Test 2: Compare Screenshots

```
/visual_compare before="path/to/before.png" after="path/to/after.png" threshold=2
```

## Part 5: Alpha Rick Integration (See Below)

See ALPHA_RICK_SETUP.md for detailed instructions on giving Alpha Rick screenshot capabilities.

---

## Troubleshooting

### Issue: Tools not appearing

**Solution**:
1. Check Claude Code logs: `View > Toggle Developer Console`
2. Look for MCP server errors
3. Verify API key is set correctly

### Issue: "Module not found" error

**Solution**:
```bash
# Install dependencies manually
pip install mcp pydantic pillow opencv-python mss google-genai
```

### Issue: Gemini API errors

**Solution**:
1. Verify API key is valid
2. Check free tier limits (15 req/min)
3. Enable Gemini API: https://aistudio.google.com/app/apikey

### Issue: Screenshot capture fails

**Solution**:
1. macOS: Ensure screen recording permissions are granted
2. iOS Simulator: Ensure a simulator is booted
3. Web: chrome-devtools MCP must be installed

---

## Next Steps

1. ✅ Install MCP server
2. ✅ Configure API key
3. ✅ Restart Claude Code
4. ✅ Test tools
5. ✅ Set up Alpha Rick integration

**Where's Waldo Rick is ready to use!**
