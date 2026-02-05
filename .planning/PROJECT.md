# Where's Waldo Rick - Visual Regression MCP Server

## What This Is

A Model Context Protocol (MCP) server that brings **agentic vision capabilities** to Claude Code for visual regression testing. It solves a critical problem in UI development: **"Build passes but nothing actually changed visually"** by providing pixel-perfect screenshot comparison with intelligent annotation.

**Named after**: "Where's Waldo" - finding visual differences in complex UIs

**Core value**: Never again have a conversation about "what changed?" - see exactly what changed, circled and annotated, with intended vs unintended change detection.

---

## The Problem

**Current State:**
- Developer works for hours on UI changes
- Build passes, code is "clean"
- You open the app... same exact layout
- You ask: "What specifically changed?"
- Dev says: "We added 2 pixels to the card"
- You ask: "Where? Top? Bottom? Inside the box? Around it?"
- Dev says: "Uh... I think the padding property?"
- 😤 Wasted time, unclear communication

**Root Cause:**
- No way to visually prove what changed
- Nuanced conversations about UI are impossible
- Can't catch unintended layout regressions
- Can't verify specific visual changes

---

## The Solution

**Where's Waldo Rick** - A specialized MCP server agent that:

1. **Captures screenshots** at key moments (manual trigger or phase completion)
2. **Compares screenshots** with pixel-level precision using Gemini 3 Flash agentic vision
3. **Circles ALL changes** - both intended and unintended
4. **Annotates differences** with specific labels ("2px top padding added to card")
5. **Validates against expectations** - marks ✅ expected changes, ⚠️ regressions
6. **Manages screenshot storage** - organized by phase, auto-cleanup of old images

**Key Innovation**: Uses Gemini 3 Flash's **agentic vision** capabilities:
- Iterative zoom/crop/annotate workflow
- Can investigate specific regions ("the box it's in, or its child item")
- Pixel-perfect diffing with multi-resolution analysis
- Conversational refinement ("not that, the child item")

---

## How It Works

### Workflow

**1. Declare Expected Changes (Before Work)**
```bash
/visual:prepare "We're updating card layout:
- Card padding increases by 2px
- Button moves to right
- Nothing else should change"
```

**2. Capture Baseline Screenshot**
```bash
/visual:capture baseline "Phase 3 - Before card update"
# Saves: screenshots/phases/03-before-card-update.png
```

**3. Development Happens**
- Devs work on UI changes
- Build passes
- Ready for verification

**4. Capture Current State**
```bash
/visual:capture current "Phase 4 - After card update"
# Saves: screenshots/phases/04-after-card-update.png
```

**5. Compare Screenshots**
```bash
/visual:compare screenshots/phases/03-before-card-update.png screenshots/phases/04-after-card-update.png
```

**6. Where's Waldo Rick Executes**
```
→ Pixel-level diff of both screenshots
→ Identifies ALL visual changes
→ Compares against expected changes list
→ Returns annotated screenshot:

✅ Card padding: +2px top/bottom (expected)
✅ Button: shifted 20px right (expected)
⚠️ Title: shifted 5px down (UNEXPECTED - regression!)
⚠️ Icon color: #333 → #666 (UNEXPECTED - regression!)
⚠️ Spacing: 8px gap appeared below card (UNEXPECTED - regression!)
```

**7. Review & Iterate**
- See exactly what changed
- Catch regressions immediately
- Have nuanced conversations: "Not the card padding, the box it's in"
- Devs fix regressions
- Re-compare until clean

### Triggers

**Manual:**
```bash
/visual:capture <name>
/visual:compare <before.png> <after.png>
```

**Automatic (Optional):**
- GSD phase completion detection
- Prompts: "Phase 4 complete. Capture screenshot?"
- Configurable: auto-capture vs manual prompt

---

## Target Users

**Primary:**
- **Bret** - Project lead needing visual verification of UI changes
- Want to catch regressions before users do
- Need proof that visual changes actually happened

**Secondary:**
- **AI Agents** doing UI work:
  - Rick Prime (UI/UX reviews)
  - Apple Elitist Rick (iOS compliance)
  - Frontend Developer agent
- Need to prove their work visually

---

## Technical Context

**MCP Server** - Native Claude Code integration
- Tools: `visual_capture`, `visual_prepare`, `visual_compare`, `visual_cleanup`
- Works with all Claude Code agents
- No impact on z.ai rate limits (separate Gemini API)

**Vision Engine** - Google Gemini 3 Flash
- Agentic vision capabilities (iterative zoom/crop/annotate)
- Multi-resolution processing (low → medium → high → ultra high)
- Code execution for image manipulation
- Free tier: 15 requests/minute (strategic usage)

**Storage** - Local filesystem
- Location: `<project>/screenshots/phases/`
- Format: PNG with metadata JSON
- Naming: `{number}-{phase-name}.png`
- Retention: Last 3 phases (configurable)
- Auto-cleanup by Waldo Rick

**Constraints:**
- **Cost**: Must stay within Gemini free tier
- **Strategy**: Strategic screenshots, not mass capture
- **Resolution**: Progressive (start low, increase for final inspection)
- **Caching**: Reuse analysis results, don't re-analyze

---

## Scope

### v1 Focus (MVP)

**Core Capabilities:**
- Screenshot capture (manual + auto-trigger)
- Screenshot comparison with pixel diff
- Annotated output showing all changes
- Expected change tracking (prepare → compare validation)
- Basic screenshot management (store, list, cleanup)

**Integrations:**
- MCP server for Claude Code
- Works with existing agents (Rick Prime, etc.)
- GSD phase workflow integration

**Platform:**
- macOS screenshots (existing tooling)
- iOS simulators (via axe CLI)
- Web screenshots (via chrome-devtools MCP)

### Out of Scope (v1)

- Automated screenshot scheduling (cron-based)
- Video/screen recording comparison
- Cross-platform screenshot normalization
- Integration with CI/CD pipelines
- Historical trend analysis (how UI evolved over time)
- Multi-branch comparison (feature branch vs main)

### Future Considerations (v2+)

- Historical comparison across all phases
- Visual change timeline/gifs
- A/B test comparison
- Performance regression (screenshot + timing)
- Accessibility regression overlay
- Automated regression test suite

---

## Success Criteria

**Product Success:**
- ✅ Can definitively answer "What changed?" with visual proof
- ✅ Catch unintended layout regressions before users do
- ✅ Have nuanced conversations about specific UI elements
- ✅ Proof that visual work actually happened

**Technical Success:**
- ✅ MCP server integrates seamlessly with Claude Code
- ✅ Stays within Gemini free tier (strategic usage)
- ✅ Screenshot storage doesn't bloat projects
- ✅ Pixel-perfect diff accuracy

**Workflow Success:**
- ✅ Fits naturally into existing GSD workflow
- ✅ Doesn't add friction to development process
- ✅ AI agents can use it autonomously
- ✅ Manual control when needed

---

## Key Constraints

**Free Tier Limits:**
- Gemini API: 15 requests/minute
- Cost consciousness: Strategic, not mass screenshots
- Must be worth the API call (major milestones, reviews)

**Storage:**
- Don't bloat projects with screenshots
- Organized structure (phases/)
- Auto-cleanup old images
- Compression/format optimization

**Accuracy:**
- Must be pixel-perfect (not "close enough")
- Must catch subtle changes (2px shifts)
- Must distinguish intentional vs unintentional

**Usability:**
- Simple commands (not complex configs)
- Clear visual output (annotated screenshots)
- Fast feedback (not 5-minute waits)

---

## What Makes This Different

**Existing Solutions:**
- **Manual screenshots**: "Here's before, here's after" - no diffing
- **Screenshot comparison tools**: Static diff, no AI understanding
- **Visual regression tools**: Expensive, complex setup, CI/CD focused

**Where's Waldo Rick:**
- **Agentic**: Understands context, can investigate regions
- **Integrated**: Native Claude Code MCP, works with all agents
- **Smart**: Expected vs unintended change detection
- **Strategic**: Free tier conscious, not mass screenshots
- **Conversational**: "Not that box, the child item"

---

## Motivation

**Why This Matters:**

UI development is broken when:
- Hours of work → build passes → nothing changed visually
- "We added 2 pixels" → WHERE? WHICH 2 pixels?
- Regression bugs slip through because you can't see them
- Nuanced UI conversations are impossible

**The Vision:**

Never again have ambiguous conversations about visual changes. See exactly what changed, prove it happened, catch regressions immediately.

Have nuanced conversations:
- "Not the card padding, the box it's in"
- "The child item, not the parent"
- "Show me exactly where the 2px went"

Ship with confidence that visual changes are intentional and regressions are caught.

---

## Open Questions

1. **Screenshot capture method**
   - Use existing tools (axe, peekaboo, chrome-devtools)?
   - Build custom capture logic?
   - Mix of both?

2. **Expected changes format**
   - Freeform text description?
   - Structured JSON/YAML?
   - Interactive prompt?

3. **Annotation output**
   - Overlay on screenshot?
   - Side-by-side comparison?
   - Separate report file?

4. **Phase detection**
   - How does Waldo know a phase is complete?
   - Parse GSD STATE.md?
   - Manual trigger only?

---

*Last updated: 2025-02-04 after project initialization*
