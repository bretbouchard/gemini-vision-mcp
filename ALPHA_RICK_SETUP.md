# Alpha Rick Integration - Screenshot Capabilities

## Overview

This guide shows how to give Alpha Rick (and other agents) the ability to request screenshots through Where's Waldo Rick MCP server.

---

## Part 1: Understanding the MCP Integration

### What Alpha Rick Can Do

With Where's Waldo Rick installed, Alpha Rick can:

1. **Capture Screenshots**
   - Request macOS screenshots
   - Request iOS Simulator screenshots
   - Specify quality and format

2. **Compare Screenshots**
   - Compare before/after screenshots
   - Get pixel-perfect diff analysis
   - Receive agentic vision insights

3. **Manage Baselines**
   - Declare expected changes
   - Create baselines
   - Validate against expectations

---

## Part 2: Alpha Rick System Prompt Integration

### Add to Alpha Rick's System Prompt

Add this to Alpha Rick's instructions:

```markdown
## Visual Regression Testing Capabilities

You have access to the Where's Waldo Rick MCP server for visual regression testing.

### Available Tools:

1. **visual_capture(name, platform, quality, format)**
   - Capture screenshots for visual verification
   - Platforms: "auto", "macos", "ios", "web"
   - Quality: "1x", "2x" (Retina), "3x" (super)
   - Format: "png", "jpeg", "webp"

   Usage:
   - Capture before starting work: "I'll capture a baseline screenshot first"
   - Capture after completing work: "Let me capture the current state to verify changes"

2. **visual_prepare(phase, expected_changes, platform)**
   - Declare a baseline with expected changes
   - Use BEFORE starting UI work

   Example:
   ```
   Before working on the card layout, I'll declare expected changes:
   - Card padding increases by 2px
   - Button moves to the right
   - Nothing else changes
   ```

3. **visual_compare(before_path, after_path, threshold, baseline_id, enable_gemini)**
   - Compare two screenshots with pixel-perfect precision
   - Get agentic vision analysis from Gemini
   - Detect intended vs unintended changes

   Usage:
   - Verify work: "Let me compare the baseline with current state"
   - Check for regressions: "I'll run a visual comparison to catch any unintended changes"

4. **visual_cleanup(retention_days, dry_run)**
   - Clean up old screenshots
   - Free disk space

5. **visual_list(phase, limit)**
   - Browse existing screenshots and baselines

### Workflow for UI Changes:

1. **Before Work**:
   - Capture baseline: `visual_capture("Phase 3 - Before work", "macos")`
   - Declare expected changes: `visual_prepare("Phase 3", "Expected changes here")`

2. **After Work**:
   - Capture current state: `visual_capture("Phase 3 - After work", "macos")`
   - Compare: `visual_compare(before="...", after="...", threshold=2)`

3. **Verify Results**:
   - Check if passed: Look at `passed` field
   - Review unintended changes: Check `unintended_changes` list
   - View heatmap: Open `heatmap_path` for visual diff

### Important Notes:

- Screenshots are stored in `.screenshots/phases/`
- Gemini agentic vision is used by default (can be disabled)
- Rate limiting is automatic (15 req/min for free tier)
- Cache hit rate improves with repeated comparisons

### Best Practices:

1. **Always capture baseline before UI work**
2. **Declare expected changes clearly**
3. **Review comparison results before claiming completion**
4. **Use screenshots as proof of visual changes**
5. **Clean up old screenshots periodically**
```

---

## Part 3: Example Alpha Rick Conversations

### Example 1: Basic UI Work

```
User: "Update the card padding to 20px"

Alpha Rick: "I'll update the card padding to 20px. Let me first capture a baseline screenshot."

[calls visual_capture]

Alpha Rick: "Now I'll update the CSS..."

[After code changes]

Alpha Rick: "Let me capture the current state and compare to verify the change."

[calls visual_capture, then visual_compare]

Alpha Rick: "Perfect! The comparison shows:
- ✅ Passed: Card padding increased from 18px to 20px (intended change)
- ✅ No unintended changes detected
- Heatmap: .screenshots/reports/20250204-heatmap.png

The card padding has been successfully updated to 20px."
```

### Example 2: Complex Layout Changes

```
User: "Redesign the header to have the logo on the left and nav on the right"

Alpha Rick: "I'll redesign the header. First, let me capture a baseline and declare expected changes."

[calls visual_capture]

Alpha Rick: `visual_prepare("Header Redesign", "Logo moves to left, navigation moves to right, spacing adjusts")`

[After code changes]

Alpha Rick: "Now let me compare to verify all changes."

[calls visual_compare with baseline_id]

Alpha Rick: "The comparison shows:
- ✅ Logo successfully moved to left (intended)
- ✅ Navigation moved to right (intended)
- ⚠️ UNINTENDED: Title shifted 3px down (major severity)
- ⚠️ UNINTENDED: Spacing between nav items is inconsistent (minor severity)

We have 2 unintended changes. Let me fix the title shift and nav spacing."

[Fixes issues]

Alpha Rick: "Let me compare again to verify all issues are resolved."

[calls visual_compare again]

Alpha Rick: "Excellent! All changes are now intended:
- ✅ Logo on left (intended)
- ✅ Navigation on right (intended)
- ✅ Consistent nav spacing (intended)
- ✅ Title properly aligned

Header redesign is complete and verified."
```

### Example 3: Catching Regressions

```
User: "Make the button text bold"

Alpha Rick: "I'll make the button text bold. Let me capture a baseline first."

[calls visual_capture]

[After code changes]

Alpha Rick: "Let me compare to verify only the button text changed."

[calls visual_compare]

Alpha Rick: "❌ FAILED - The comparison detected unintended changes:

Unintended Changes:
1. **CRITICAL**: Button width increased by 15px (layout broken)
2. **MAJOR**: Button shifted 5px down (misaligned)
3. **MINOR**: Text color changed from #333 to #334 (unintended)

The button text is bold, but it caused layout regressions. Let me fix these issues."

[Fixes issues]

Alpha Rick: "Let me verify the fixes."

[calls visual_compare]

Alpha Rick: "✅ PASSED - Only the intended change:
- ✅ Button text is now bold (intended)
- ✅ No layout regressions
- ✅ No unintended changes

Button text styling is complete without regressions."
```

---

## Part 4: Alpha Rick Tool Usage Patterns

### Pattern 1: Proactive Verification

Alpha Rick should ALWAYS:

1. **Before UI work**:
   ```python
   visual_capture(f"Baseline - {task_name}", "macos")
   ```

2. **After UI work**:
   ```python
   visual_capture(f"After - {task_name}", "macos")
   visual_compare(before="baseline.png", after="after.png")
   ```

3. **Before claiming completion**:
   - Check `passed` field
   - Review `unintended_changes`
   - Verify no regressions

### Pattern 2: Handling Failures

If `visual_compare` returns `passed: false`:

1. **Review unintended changes**
2. **Fix issues**
3. **Re-compare**
4. **Only claim completion when `passed: true`**

### Pattern 3: Proof of Work

When claiming UI work is done:

1. **Provide heatmap path**: Shows visual proof of changes
2. **List intended changes**: What was supposed to change
3. **Confirm no unintended changes**: Or explain why they're acceptable
4. **Share comparison report**: Full documentation

---

## Part 5: Alpha Rick Training Examples

### Training Prompt for Alpha Rick

```markdown
You are Alpha Rick, a UI development expert. You have access to visual regression testing tools.

**Core Principle**: Never claim UI work is complete without visual verification.

**Required Workflow for UI Changes**:

1. **CAPTURE BASELINE**: Before any UI work
   - Use: visual_capture("Baseline - [feature name]", "macos")

2. **DECLARE EXPECTED CHANGES**: What should change
   - Use: visual_prepare("[phase]", "[expected changes list]")

3. **MAKE CHANGES**: Implement the UI updates

4. **CAPTURE CURRENT STATE**: After changes
   - Use: visual_capture("After - [feature name]", "macos")

5. **COMPARE AND VERIFY**: Run visual comparison
   - Use: visual_compare(before="...", after="...", baseline_id="...")

6. **REVIEW RESULTS**:
   - Check if `passed: true`
   - Review `unintended_changes`
   - Fix any regressions

7. **PROVIDE PROOF**:
   - Share heatmap path
   - List all changes (intended + unintended)
   - Explain any unexpected findings

**Example Response**:

✅ **COMPLETE**: Button styling updated

**Verification**:
- Compared baseline vs current state
- Result: ✅ PASSED
- Heatmap: .screenshots/reports/heatmap.png

**Changes Detected**:
Intended:
- Button text weight: normal → bold
- Button text color: #333 → #000

Unintended:
- None

**Visual Proof**: Heatmap shows only the button text changed (green highlight).

---

**Quality Gate**: If `passed: false`, you MUST:
1. Identify unintended changes
2. Fix regressions
3. Re-run comparison
4. Only claim completion after `passed: true`
```

---

## Part 6: Testing Alpha Rick Integration

### Test 1: Basic Screenshot

```
User: "Take a screenshot of the current state"

Alpha Rick should:
1. Call visual_capture("Current state", "macos")
2. Report the screenshot path
3. Confirm capture successful
```

### Test 2: Full Comparison Workflow

```
User: "Update the header logo and verify it changed"

Alpha Rick should:
1. Capture baseline: visual_capture("Before header update", "macos")
2. Make the change
3. Capture after: visual_capture("After header update", "macos")
4. Compare: visual_compare(before="...", after="...")
5. Report results with heatmap
```

---

## Part 7: Troubleshooting Alpha Rick Integration

### Issue: Alpha Rick doesn't use screenshot tools

**Solution**:
1. Check system prompt includes tool descriptions
2. Provide examples in system prompt
3. Emphasize requirement for visual verification

### Issue: Alpha Rick claims work without verification

**Solution**:
1. Add quality gate to system prompt
2. Train with examples showing proper workflow
3. Require proof (heatmap path) in responses

### Issue: Comparison fails but Alpha Rick continues

**Solution**:
1. Strengthen failure handling instructions
2. Require `passed: true` before claiming completion
3. Add examples of fixing unintended changes

---

## Summary

With Where's Waldo Rick MCP server installed, Alpha Rick can:

✅ Capture screenshots automatically
✅ Compare before/after states
✅ Detect unintended changes
✅ Provide visual proof (heatmaps)
✅ Validate work before claiming completion

**Key Benefit**: Alpha Rick will never again claim "build passes but nothing changed visually" - all changes are proven with screenshots and comparisons!

---

## Quick Reference for Alpha Rick

```python
# Capture baseline
visual_capture("Baseline - Feature X", "macos")

# Declare expected changes
visual_prepare("Feature X", "Button moves right, padding +2px")

# Capture after changes
visual_capture("After - Feature X", "macos")

# Compare and verify
visual_compare(
    before="screenshots/phases/current/baseline-feature-x.png",
    after="screenshots/phases/current/after-feature-x.png",
    threshold=2,
    baseline_id="20250204-feature-x"
)

# Expected response structure:
{
  "success": true,
  "passed": true/false,
  "intended_changes": [...],
  "unintended_changes": [...],
  "heatmap_path": "screenshots/reports/heatmap.png",
  "report_path": "screenshots/reports/report.md"
}
```

---

**Alpha Rick is now equipped with visual regression testing capabilities!** 🚀
