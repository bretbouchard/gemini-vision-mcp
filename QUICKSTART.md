# Quick Start Guide - Where's Waldo Rick

## 🚀 Get Started in 5 Minutes

### Step 1: Get Gemini API Key (2 minutes)

1. Go to: https://aistudio.google.com/app/apikey
2. Click "Create API Key"
3. Copy the key

### Step 2: Configure MCP Server (2 minutes)

Edit `~/.claude/mcp.json`:

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
        "GEMINI_API_KEY": "paste-your-api-key-here"
      }
    }
  }
}
```

### Step 3: Restart Claude Code (1 minute)

- Quit Claude Code
- Reopen Claude Code

That's it! You now have visual regression testing tools available. ✅

---

## 🧪 Test It Out

### Test 1: Capture a Screenshot

```
/visual_capture "My first screenshot" platform="macos"
```

**Expected Result**:
```json
{
  "success": true,
  "path": "/project/.screenshots/phases/current/20250204-200000-my-first-screenshot.png",
  "platform": "macos",
  "resolution": "2560x1440"
}
```

### Test 2: Compare Two Screenshots

```
/visual_compare before="path/to/before.png" after="path/to/after.png" threshold=2
```

**Expected Result**:
```json
{
  "success": true,
  "passed": false,
  "changed_pixels": 1523,
  "changed_percentage": 0.12,
  "unintended_changes": [
    {
      "description": "Title shifted 5px down",
      "severity": "major",
      "confidence": 0.88
    }
  ],
  "heatmap_path": "screenshots/reports/heatmap.png"
}
```

---

## 🤖 Alpha Rick Integration

To give Alpha Rick screenshot capabilities, add this to his system prompt:

```markdown
## Visual Regression Testing

You have access to Where's Waldo Rick MCP server for visual verification.

**Required Workflow**:
1. Capture baseline before UI work: `visual_capture("Baseline - [task]", "macos")`
2. Capture after work: `visual_capture("After - [task]", "macos")`
3. Compare: `visual_compare(before="...", after="...")`
4. Only claim completion if `passed: true`

**Quality Gate**: Never claim UI work is complete without visual verification.
```

See `ALPHA_RICK_SETUP.md` for detailed integration guide.

---

## 📚 Full Documentation

- **SETUP.md**: Complete setup instructions
- **ALPHA_RICK_SETUP.md**: Alpha Rick integration guide
- **README.md**: Project overview and features

---

## 🎯 Common Use Cases

### Use Case 1: Prove UI Changes Actually Happened

```
/visual_capture "Before button update" "macos"
[Make changes]
/visual_capture "After button update" "macos"
/visual_compare before="..." after="..."
```

### Use Case 2: Catch Regressions

```
/visual_prepare("Feature X", "Button moves right, padding +2px")
/visual_capture "Baseline" "macos"
[Make changes]
/visual_capture "Current" "macos"
/visual_compare before="..." after="..." baseline_id="..."
```

### Use Case 3: Alpha Rick Automated Verification

Alpha Rick will automatically:
1. Capture baseline before work
2. Capture after work
3. Compare with agentic vision
4. Fix any unintended changes
5. Only claim completion when passed

---

## ✅ Verification

You'll know it's working when you see these tools available:

- ✅ `visual_capture` - Capture screenshots
- ✅ `visual_prepare` - Declare baselines
- ✅ `visual_compare` - Compare with agentic vision
- ✅ `visual_cleanup` - Clean up old screenshots
- ✅ `visual_list` - List screenshots and baselines

---

## 🆘 Troubleshooting

**Tools not appearing?**
- Restart Claude Code
- Check API key is set
- View Developer Console for errors

**Capture failing?**
- macOS: Grant screen recording permissions
- iOS: Ensure simulator is booted

**Gemini errors?**
- Verify API key is valid
- Check free tier limits (15 req/min)

---

**You're ready to use Where's Waldo Rick!** 🚀

For detailed setup, see: `SETUP.md`
For Alpha Rick integration, see: `ALPHA_RICK_SETUP.md`
