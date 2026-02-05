# Features Research - Visual Regression Tools

## Executive Summary

**Table Stakes Identified**: Screenshot capture, side-by-side comparison, diff visualization (heatmap), baseline management, pass/fail determination.

**Key Differentiator**: **Agentic vision analysis using Gemini 3 Flash** - No existing tool provides iterative, intelligent analysis that can distinguish intended vs unintended changes.

**Anti-Features Validated**: Mass CI/CD integration, cross-browser testing matrices, pixel-perfect strict mode.

**Competitive Gap**: All existing tools (Playwright, Chromatic, Applitools) focus on automated CI/CD workflows with static reports. None provide conversational, on-demand analysis for AI agents.

---

## Feature Categories

### Table Stakes (Must-Have)

Users expect these features from any visual regression tool. Without these, the tool is non-viable.

#### 1. Screenshot Capture

**What**: Ability to capture screenshots from various sources

**Capabilities**:
- Multiple input formats (PNG, JPG, PDF)
- Platform support (macOS, iOS, Web)
- Manual trigger (on-demand capture)
- Metadata tagging (phase name, timestamp, description)

**Evidence**:
- Playwright: `page.screenshot()` is core feature
- Chromatic: Screenshot capture is first step in workflow
- Applitools: Multi-platform capture is foundational

**Complexity**: LOW - Well-understood problem, standard solutions

---

#### 2. Side-by-Side Comparison

**What**: Visual display of before/after screenshots

**Capabilities**:
- Synchronized scrolling
- Zoomable views
- Overlay mode (fade between images)
- Pixel-level inspection

**Evidence**:
- Playwright: Built-in diff reporter with side-by-side view
- Chromatic: "Diff view" is primary UI
- All tools: Side-by-side is expected default

**Complexity**: LOW - Standard UI pattern

---

#### 3. Diff Visualization (Heatmap)

**What**: Visual representation of pixel differences

**Capabilities**:
- Color-coded heatmaps (red = changed, green = unchanged)
- Adjustable diff threshold
- Ignore regions (dynamic content)
- Bounding boxes around changes

**Evidence**:
- Playwright: `expect(screenshot).toMatchSnapshot()` generates heatmap
- Chromatic: "Diff map" shows pixel changes
- Industry standard: Red/green heatmap is universal pattern

**Complexity**: MEDIUM - Requires pixel diffing algorithm

---

#### 4. Baseline Management

**What**: Store and retrieve baseline screenshots for comparison

**Capabilities**:
- Save baseline images
- Update baseline (accept changes)
- Restore previous baseline
- Baseline versioning

**Evidence**:
- Playwright: `toMatchSnapshot()` stores baseline in `__screenshots__`
- Chromatic: "Baseline" concept is core to workflow
- Applitools: "Baseline" vs "Checkpoint" terminology

**Complexity**: MEDIUM - Requires storage strategy, cleanup policies

---

#### 5. Pass/Fail Determination

**What**: Boolean result + threshold configuration

**Capabilities**:
- Configurable diff threshold (0.1% - 5%)
- Pass if below threshold
- Fail if above threshold
- Report pass/fail status

**Evidence**:
- Playwright: `failOnDifference: 0.1` threshold parameter
- Chromatic: "Changes detected" = fail
- All tools: Threshold-based pass/fail is standard

**Complexity**: LOW - Simple comparison logic

---

### Differentiators (Competitive Advantage)

Features that make this tool unique and superior to existing solutions.

#### 1. Agentic Vision Analysis ⭐

**What**: Iterative, intelligent visual analysis using Gemini 3 Flash

**Capabilities**:
- Iterative zoom/crop/annotate workflow
- Conversational investigation ("What changed in the header?")
- Context-aware understanding ("Not the card, the box it's in")
- Distinguish intended vs unintended changes
- Multi-resolution analysis (low → medium → high → ultra)

**Evidence**:
- **No existing tool offers this** - Verified through web search
- Playwright: Static diff only, no AI analysis
- Chromatic: Manual review required for interpretation
- Applitools: AI-powered but focused on layout, not conversational

**Why It Matters**:
- Current tools show WHAT changed, not WHY or IF it's intentional
- Requires human interpretation of every diff
- Can't handle nuanced conversations ("not that box, the child item")

**Complexity**: HIGH - Emerging technology, no established patterns

---

#### 2. Expected vs Unintended Change Detection

**What**: Validate changes against declared expectations

**Capabilities**:
- Declare expected changes before work
- Compare actual changes against expectations
- Mark ✅ expected changes
- Flag ⚠️ unintended regressions
- Generate regression report

**Evidence**:
- **No existing tool offers this** - Verified through web search
- Playwright: All diffs are failures, no "expected" concept
- Chromatic: Manual review required to determine intent
- Current workflow: Human must interpret every change

**Why It Matters**:
- Catches regressions automatically
- Reduces false positives (expected changes aren't errors)
- Enables "visual TDD" - declare expectations, verify against them

**Complexity**: HIGH - Requires semantic understanding of changes

---

#### 3. Conversational Investigation

**What**: Natural language queries about visual changes

**Capabilities**:
- Ask: "What changed in the navigation?"
- Ask: "Show me the 2 pixels that were added"
- Ask: "Is the title aligned with the button?"
- Follow-up questions based on answers

**Evidence**:
- **No existing tool offers this** - Verified through web search
- Playwright: No query interface, static reports only
- Chromatic: Manual visual inspection required
- Current tools: Cannot answer questions about diffs

**Why It Matters**:
- Enables nuanced UI conversations
- Reduces back-and-forth ("what specifically changed?")
- Proof of work with visual specificity

**Complexity**: VERY HIGH - Requires agentic vision + natural language understanding

---

#### 4. Regional Analysis ("The Box It's In")

**What**: Investigate specific regions with progressive zoom

**Capabilities**:
- Focus on specific UI element
- Zoom into child elements
- Analyze component hierarchy
- Ignore parent, inspect children

**Evidence**:
- **No existing tool offers this** - Verified through web search
- Playwright: Can crop but not iteratively investigate
- Current tools: Static region-of-interest only

**Why It Matters**:
- Enables "not that box, the child item" conversations
- Analyzes complex component hierarchies
- Proof of specific element changes

**Complexity**: HIGH - Requires agentic vision with iterative zoom

---

### Anti-Features (Deliberately NOT Building)

Features that are commonly requested but problematic for this use case.

#### 1. Mass CI/CD Integration

**What**: Automated screenshot testing in CI/CD pipeline

**Why NOT**:
- Burns through free tier API limits (15 req/min)
- Not the target use case (AI agents, not automated pipelines)
- Adds complexity without value for manual workflows

**Evidence**:
- Playwright: Integrates with CI/CD but burns API credits
- Chromatic: Designed for CI/CD but expensive
- Our goal: Manual/on-demand for AI agents, not automated

---

#### 2. Cross-Browser Testing Matrix

**What**: Test across multiple browsers (Chrome, Firefox, Safari)

**Why NOT**:
- Multiplies API costs (browser × screenshot × comparison)
- Not the target use case (focused on macOS/iOS/Web dev)
- Adds complexity (browser automation, driver management)

**Evidence**:
- Playwright: Supports multi-browser but heavy setup
- Chromatic: Multi-browser is premium feature
- Our goal: Platform-specific (macOS app, iOS app, or web), not cross-browser

---

#### 3. Pixel-Perfect Strict Mode

**What**: Fail on ANY pixel difference, no threshold

**Why NOT**:
- Anti-aliasing noise creates false positives
- Font rendering varies between machines
- Dynamic content (timestamps) always changes
- Makes tool unusable in practice

**Evidence**:
- Applitools: "Strict layout matching" creates noise storms
- Industry best practice: Use thresholds (0.1% - 1%)
- Our goal: Detect real regressions, not anti-aliasing differences

---

#### 4. Automated Screenshot Scheduling

**What**: Periodic screenshot capture (cron-based)

**Why NOT**:
- Burns through free tier limits
- Generates storage bloat
- Not the target use case (manual/on-demand)

**Evidence**:
- Some tools offer "monitoring" features
- Our goal: Manual trigger at major milestones, not automated monitoring

---

## Competitive Analysis

### Playwright (Microsoft)

**Strengths**:
- Free, open-source
- Excellent CI/CD integration
- Cross-browser support

**Weaknesses**:
- Static diff only, no AI analysis
- Cannot distinguish intended vs unintended changes
- No conversational interface
- Heatmap requires manual interpretation

**Gap**: No agentic vision, no intelligent change interpretation

### Chromatic

**Strengths**:
- Git integration (branch-based testing)
- Good UI for diff visualization
- Team collaboration features

**Weaknesses**:
- Expensive for teams ($20+/user/month)
- Static diff only
- No AI-powered analysis
- Focused on React/web components

**Gap**: No conversational investigation, no expected change validation

### Applitools (Eyes)

**Strengths**:
- AI-powered layout matching
- Cross-platform support
- Enterprise features

**Weaknesses**:
- Very expensive ($100+/month)
- AI is for layout matching, not conversational
- Complex setup
- Overkill for manual workflows

**Gap**: No agentic vision, no expected vs unintended detection

---

## Feature Dependencies

### Core Dependencies

**Screenshot Capture** ← Must exist before:
- Side-by-side comparison
- Diff visualization
- Baseline management

**Diff Visualization** ← Depends on:
- Screenshot capture
- Pixel diffing algorithm

**Baseline Management** ← Depends on:
- Screenshot capture
- Storage strategy

### Agentic Vision Dependencies

**Agentic Vision Analysis** ← Depends on:
- Screenshot capture
- Gemini API integration
- Diff visualization (for context)

**Expected vs Unintended** ← Depends on:
- Agentic vision analysis
- User-declared expectations
- Diff visualization

**Conversational Investigation** ← Depends on:
- Agentic vision analysis
- Natural language understanding
- Multi-resolution analysis

### Build Order

1. **Screenshot capture** (foundation)
2. **Diff visualization** (needs screenshots)
3. **Baseline management** (needs screenshots + storage)
4. **Agentic vision** (needs all above)
5. **Expected vs unintended** (needs agentic vision)
6. **Conversational investigation** (needs agentic vision)

---

## MVP Definition

### v1 MVP (Minimum Viable Product)

**Table Stakes** (Must have):
- ✅ Screenshot capture (manual trigger)
- ✅ Side-by-side comparison
- ✅ Diff visualization (heatmap)
- ✅ Baseline management (save, retrieve, update)
- ✅ Pass/fail with threshold

**Differentiators** (Competitive advantage):
- ✅ Agentic vision analysis (iterative zoom/crop/annotate)
- ✅ Expected vs unintended change detection
- ⚠️ Conversational investigation (basic - single question)

**Out of Scope** (Anti-features):
- ❌ CI/CD integration
- ❌ Cross-browser testing
- ❌ Automated scheduling
- ❌ Pixel-perfect strict mode

### v1+ (Post-MVP)

**Advanced Features**:
- Full conversational investigation (multi-turn dialog)
- Regional analysis ("the box it's in")
- Historical comparison across all phases
- Element-level analysis with bounding boxes
- Context-aware ignoring (semantic dynamic content)

---

## False Positive Reduction Strategies

### Problem: Anti-Aliasing Noise

**Symptom**: Font rendering creates pixel-level noise, false positives

**Solution**: 2-pixel Gaussian blur preprocessing
- **Evidence**: Industry standard (Stack Overflow, GitHub issues)
- **Implementation**: OpenCV `GaussianBlur(kernel=(5,5), sigmaX=2)`
- **Effect**: Eliminates anti-aliasing noise while preserving real changes

### Problem: Dynamic Content

**Symptom**: Timestamps, counters, animations always change

**Solution**: Semantic understanding (agentic vision advantage)
- **Traditional tools**: Manual masking, ignore regions
- **Our approach**: AI understands "timestamp changed" is not a regression
- **Implementation**: Gemini 3 Flash semantic analysis

### Problem: Layout Shifts

**Symptom**: Entire UI shifts 1px, hundreds of "changes" detected

**Solution**: Group adjacent changes, identify root cause
- **Traditional tools**: Hundreds of red boxes, overwhelming
- **Our approach**: "Card padding increased by 2px, causing title to shift 2px"
- **Implementation**: Agentic vision pattern recognition

---

## Feature Complexity Assessment

| Feature | Complexity | Rationale |
|---------|-----------|-----------|
| Screenshot Capture | LOW | Standard APIs, well-understood |
| Side-by-Side Comparison | LOW | Basic UI pattern |
| Diff Visualization | MEDIUM | Pixel diffing algorithm, heatmap generation |
| Baseline Management | MEDIUM | Storage strategy, cleanup policies |
| Pass/Fail Determination | LOW | Simple threshold comparison |
| **Agentic Vision Analysis** | **HIGH** | Emerging tech, no established patterns |
| **Expected vs Unintended** | **HIGH** | Requires semantic understanding |
| **Conversational Investigation** | **VERY HIGH** | Multi-turn dialog, context management |
| Regional Analysis | HIGH | Iterative zoom, component hierarchy |

---

## Open Questions

### Gemini API Capabilities

**Question**: Can Gemini 3 Flash actually do iterative zoom/crop/annotate?

**Status**: Marketing materials say yes, but need to test actual API

**Research needed**: Phase 3 should verify:
- Zoom into specific regions
- Crop areas of interest
- Annotate findings dynamically
- Multi-resolution processing

### Conversation Depth

**Question**: How many turns can conversational investigation support?

**Status**: Unclear if single-question or multi-turn dialog

**Research needed**: Phase 3 should test:
- Single question: "What changed in the header?"
- Follow-up: "Not the logo, the navigation items"
- Follow-up: "Show me the spacing changes"

### Cost Per Comparison

**Question**: How much does one comparison cost in Gemini API credits?

**Estimate**:
- Screenshot analysis: ~1000 tokens/image
- Comparison: ~2000 tokens (2 images)
- Annotated output: ~500 tokens
- **Total**: ~3500 tokens = $0.0026

**Research needed**: Phase 3 should measure actual usage with real screenshots

---

## Roadmap Implications

### Phase Structure

**Phase 1**: Table Stakes (screenshot, diff, baseline, pass/fail)
**Phase 2**: MCP Integration (expose via MCP protocol)
**Phase 3**: Agentic Vision (THE DIFFERENTIATOR)
**Phase 4**: Advanced Features (conversational, regional)

### Risk Areas

**High Risk**: Phase 3 (Agentic Vision)
- Gemini API capabilities unverified
- Cost per comparison unknown
- No established patterns to follow

**Mitigation**: Phase-specific research before implementation

---

*Last updated: 2025-02-04*
*Confidence: HIGH (table stakes, differentiators, anti-features)*
