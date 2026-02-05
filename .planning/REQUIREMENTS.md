# Requirements — Where's Waldo Rick

**Project**: Visual Regression MCP Server with Agentic Vision
**Version**: 1.0
**Last Updated**: 2025-02-04

---

## Table Stakes (Must-Have Features)

### CAPTURE — Screenshot Capture

#### REQ-CAPTURE-01: Multi-Platform Screenshot Capture
User can capture screenshots from multiple platforms (macOS desktop, iOS Simulator, and web browsers via chrome-devtools MCP) with automatic platform detection and adapter selection.

**Acceptance Criteria**:
- macOS screenshots use MSS (capture time < 50ms)
- iOS screenshots use simctl CLI tool
- Web screenshots use chrome-devtools MCP
- Platform is auto-detected from environment
- Fallback to manual platform selection if auto-detection fails

**Traceability**: Phase 2

#### REQ-CAPTURE-02: Phase-Based Organization
User can organize screenshots by development phase with automatic directory structure creation (`.screenshots/phases/{phase-name}/`) and JSON index metadata.

**Acceptance Criteria**:
- Screenshots stored in phase-named directories
- JSON index includes timestamp, platform, resolution
- Index is queryable for comparison operations
- Missing directories are auto-created

**Traceability**: Phase 2

#### REQ-CAPTURE-03: Configurable Capture Quality
User can configure screenshot quality settings (resolution scale, format selection) with persistent configuration across sessions.

**Acceptance Criteria**:
- Resolution scale options: 1x, 2x (Retina), 3x (super)
- Format options: PNG (lossless), JPEG (compressed), WebP
- Configuration persisted in `.screenshots/config.json`
- Default: PNG @ 2x resolution

**Traceability**: Phase 2

---

### COMPARE — Side-by-Side Comparison

#### REQ-COMPARE-01: Pixel-Perfect Diffing
User can compare two screenshots with pixel-level precision using OpenCV with configurable threshold for change detection (1px, 2px, 3px sensitivity).

**Acceptance Criteria**:
- OpenCV 4.10+ for image comparison
- Configurable pixel threshold (default: 2px)
- Absolute difference calculation
- Threshold selection based on image complexity
- Results include total changed pixels and percentage

**Traceability**: Phase 3

#### REQ-COMPARE-02: Anti-Aliasing Noise Reduction
User can enable 2-pixel Gaussian blur preprocessing to prevent false positives from anti-aliasing rendering artifacts.

**Acceptance Criteria**:
- 2px Gaussian blur kernel applied before comparison
- Option to enable/disable preprocessing
- Reduces false positives by >80% (measured against anti-aliasing test suite)
- Preserves genuine layout changes

**Traceability**: Phase 3

#### REQ-COMPARE-03: Heatmap Diff Visualization
User can view difference heatmap highlighting changed regions with color intensity based on magnitude of change (subtle to dramatic).

**Acceptance Criteria**:
- Color gradient: yellow (subtle) → orange (moderate) → red (dramatic)
- Overlay on original screenshot
- Adjustable intensity (opacity: 20-80%)
- Exportable as PNG

**Traceability**: Phase 3

---

### BASELINE — Baseline Management

#### REQ-BASELINE-01: Baseline Declaration
User can declare any screenshot as a baseline with automatic snapshot metadata storage and version tracking.

**Acceptance Criteria**:
- Baseline stored with unique ID (timestamp-based)
- Metadata includes: phase, description, expected changes
- Baseline listing with search/filter
- Baseline restoration from history

**Traceability**: Phase 2

#### REQ-BASELINE-02: Expected Changes Annotation
User can document expected changes when declaring a baseline (e.g., "moved button 2px right, added new card") with structured format for validation.

**Acceptance Criteria**:
- Structured annotation format (JSON schema)
- Free text description field
- Optional bounding box annotations
- Annotations linked to baseline ID

**Traceability**: Phase 2

#### REQ-BASELINE-03: Baseline Comparison
User can compare current screenshot against any declared baseline with automatic detection of differences beyond expected changes.

**Acceptance Criteria**:
- Select baseline by ID or search
- Compute diff against baseline
- Highlight all changes (intended + unintended)
- Flag changes not in expected changes annotation

**Traceability**: Phase 3

---

### VALIDATION — Pass/Fail Determination

#### REQ-VALIDATION-01: Pass/Fail Criteria
User can define pass/fail criteria based on change thresholds (maximum pixel change, maximum region count) with customizable rules.

**Acceptance Criteria**:
- Configurable pixel change threshold (default: 0.5% of total pixels)
- Configurable maximum changed regions (default: 10)
- Pass/fail status clearly displayed
- Criteria persisted per comparison

**Traceability**: Phase 3

#### REQ-VALIDATION-02: Regression Detection
User can automatically detect unintended changes by comparing actual changes against expected changes annotation.

**Acceptance Criteria**:
- Parse expected changes from baseline annotation
- Flag all changes not in expected list
- Categorize as "regression" or "unexpected enhancement"
- Provide detailed diff report

**Traceability**: Phase 3

#### REQ-VALIDATION-03: Comparison Report
User can generate detailed comparison reports including pass/fail status, change summary, annotated screenshots, and recommendations.

**Acceptance Criteria**:
- Markdown-formatted report
- Embedded screenshots with annotations
- Pass/fail badge with criteria explanation
- Change summary table (intended vs unintended)
- Report saved to `.screenshots/reports/`

**Traceability**: Phase 3

---

## Differentiators (Competitive Advantage)

### AGENTIC — Agentic Vision Analysis

#### REQ-AGENTIC-01: Gemini 3 Flash Integration
User can leverage Gemini 3 Flash's agentic vision capabilities for iterative zoom/crop/annotate analysis of visual differences.

**Acceptance Criteria**:
- Integration with gemini-3-flash-preview model
- Agentic vision API calls (multi-resolution analysis)
- Iterative refinement: low → medium → high → ultra high resolution
- Code execution for image manipulation (crop, annotate)
- Free tier usage: 15 req/min, 250K tokens/min

**Traceability**: Phase 3 (HIGH RISK)

#### REQ-AGENTIC-02: Intelligent Change Interpretation
User can receive natural language explanations of what changed (e.g., "padding increased by 2px on top of card") instead of just pixel coordinates.

**Acceptance Criteria**:
- Gemini analyzes pixel diffs and generates descriptions
- Descriptions reference UI elements (cards, buttons, text)
- Confidence scores for each interpretation
- Fallback to pixel coordinates if interpretation fails

**Traceability**: Phase 3

#### REQ-AGENTIC-03: Conversational Investigation
User can engage in multi-turn conversations with Waldo about visual changes, asking follow-up questions like "Where exactly did the padding change?" and receiving annotated zoom-ins.

**Acceptance Criteria**:
- Multi-turn conversation context maintained
- Follow-up questions trigger focused analysis
- Annotated zoom-ins generated on-demand
- Conversation history persisted for audit trail
- Exit condition: user satisfaction or 5-turn limit

**Traceability**: Phase 5

#### REQ-AGENTIC-04: Aggressive Caching
User can benefit from hash-based caching to minimize redundant Gemini API calls and stay within free tier limits.

**Acceptance Criteria**:
- Hash-based cache key (image pair + threshold)
- Cache hit returns cached analysis without API call
- Cache invalidation on threshold/configuration change
- Cache statistics (hit rate, API calls saved)

**Traceability**: Phase 3

#### REQ-AGENTIC-05: Progressive Resolution
User can automatically start with low-resolution analysis and only increase resolution if needed (confidence score < threshold) to optimize token usage.

**Acceptance Criteria**:
- Start: 720p (fast, cheap)
- Upgrade to 1080p if confidence < 80%
- Upgrade to 4K if confidence < 80% again
- Stop at ultra-high (8K) or confidence ≥ 80%
- Token savings tracked per comparison

**Traceability**: Phase 3

#### REQ-AGENTIC-06: Rate Limiting with Token Bucket
User can stay within Gemini free tier limits (15 req/min) with automatic token bucket rate limiter that queues requests during spikes.

**Acceptance Criteria**:
- Token bucket algorithm: 15 tokens refilled per minute
- Queued requests processed when tokens available
- Queue status visible to user (position, ETA)
- Burst allowance: up to 15 requests immediately if full bucket
- Backpressure: user notified if queue > 5 requests

**Traceability**: Phase 3

---

### EXPECTED — Expected vs Unintended Change Detection

#### REQ-EXPECTED-01: Expected Changes Declaration
User can declare expected changes when capturing baseline screenshots (e.g., "move button 2px right, add new card to bottom of list").

**Acceptance Criteria**:
- Structured input format (JSON schema or natural language)
- Natural language parsed by Gemini for structured extraction
- Expected changes linked to baseline ID
- Validation: changes must be verifiable visually

**Traceability**: Phase 2

#### REQ-EXPECTED-02: Intended vs Unintended Classification
User can see all changes categorized as "intended" (match expected changes) or "unintended" (not in expected changes) with clear visual distinction.

**Acceptance Criteria**:
- Pixel diffs compared against expected changes
- Classification algorithm: match by proximity, description, bounding box
- Intended changes: green highlights
- Unintended changes: red highlights
- Ambiguous changes: yellow highlights (manual review needed)

**Traceability**: Phase 3

#### REQ-EXPECTED-03: Regression Alerting
User can receive immediate alerts for regressions (unintended changes) with severity classification (critical, major, minor) based on visual impact.

**Acceptance Criteria**:
- Severity scoring algorithm:
  - Critical: center-stage layout breaks, text unreadability
  - Major: misalignment, overflow, spacing issues
  - Minor: 1px shifts, color variations
- Alert notification with severity badge
- Regression summary count (critical: N, major: N, minor: N)

**Traceability**: Phase 3

---

### CONVERSATIONAL — Conversational Investigation

#### REQ-CONV-01: Multi-Turn Conversation Context
User can maintain conversation context across up to 5 turns with Waldo, asking follow-up questions about visual changes.

**Acceptance Criteria**:
- Conversation state persisted per comparison session
- Maximum 5 turns (configurable)
- Context includes: original comparison, previous questions, previous answers
- Graceful exit after 5 turns with summary

**Traceability**: Phase 5

#### REQ-CONV-02: Focused Follow-Up Analysis
User can ask targeted follow-up questions (e.g., "Show me exactly where the padding changed") and receive annotated zoom-ins of specific regions.

**Acceptance Criteria**:
- Follow-up question triggers focused analysis
- Gemini generates annotated screenshot (zoom, crop, circles/arrows)
- Annotations highlight specific requested region
- Response includes bounding box coordinates

**Traceability**: Phase 5

#### REQ-CONV-03: Conversational UI Patterns
User can engage in natural conversations using common UI investigation patterns (zoom, crop, annotate, measure, compare).

**Acceptance Criteria**:
- Supported patterns:
  - "Zoom in on {region}"
  - "Crop to {element}"
  - "Annotate {change type}"
  - "Measure {dimension} between {elements}"
  - "Compare {region A} with {region B}"
- Pattern matching with fuzzy intent recognition
- Fallback to generic analysis if pattern unrecognized

**Traceability**: Phase 5

#### REQ-CONV-04: Conversation History Persistence
User can access conversation history for audit trail and learning (what questions were asked, what answers were provided).

**Acceptance Criteria**:
- Conversations stored in `.screenshots/conversations/`
- JSON format with timestamp, question, answer, annotations
- Searchable by comparison ID, date, question content
- Exportable as markdown report

**Traceability**: Phase 5

---

## Non-Functional Requirements

### Performance

#### REQ-PERF-01: Capture Latency
Screenshot capture must complete in < 100ms for macOS, < 500ms for iOS Simulator, < 1s for web browsers.

**Traceability**: Phase 2

#### REQ-PERF-02: Comparison Speed
Pixel-level comparison must complete in < 2s for standard screenshots (1920x1080 or smaller).

**Traceability**: Phase 3

#### REQ-PERF-03: Agentic Vision Response Time
Gemini agentic vision analysis must complete in < 10s for initial analysis, < 5s for follow-up questions.

**Traceability**: Phase 3

### Reliability

#### REQ-RELIABILITY-01: Rate Limit Compliance
System must stay within Gemini free tier limits (15 req/min) with 99.9% compliance rate.

**Traceability**: Phase 3

#### REQ-RELIABILITY-02: Cache Hit Rate
System must achieve >60% cache hit rate for repeated comparisons to minimize API usage.

**Traceability**: Phase 3

#### REQ-RELIABILITY-03: MCP JSON-RPC Compliance
System must maintain valid JSON-RPC protocol (no stdout pollution) with 100% compliance rate.

**Traceability**: Phase 1

### Usability

#### REQ-USABILITY-01: Zero-Config Baseline
User can perform basic screenshot capture and comparison without any configuration (sensible defaults out-of-the-box).

**Traceability**: Phase 2

#### REQ-USABILITY-02: Clear Error Messages
User receives actionable error messages for all failure modes (rate limits, API errors, file system issues) with remediation steps.

**Traceability**: Phase 4

#### REQ-USABILITY-03: Progressive Disclosure
Advanced features (conversational investigation, custom thresholds) are hidden behind opt-in flags to keep default workflow simple.

**Traceability**: Phase 5

---

## Anti-Requirements (Deliberately NOT Building)

### ❌ CI/CD Mass Integration
**Why Not**: Burns through free tier limits (15 req/min) with mass screenshot comparisons
**Alternative**: Manual on-demand testing during code reviews and major milestones

### ❌ Cross-Browser Testing Matrix
**Why Not**: Not target use case (focused on macOS/iOS development workflow)
**Alternative**: Use existing tools (BrowserStack, Percy) for cross-browser testing

### ❌ Pixel-Perfect Strict Mode
**Why Not**: Anti-aliasing rendering creates false positive noise storm
**Alternative**: 2px threshold default with Gaussian blur preprocessing

### ❌ Cloud-Based Baseline Storage
**Why Not**: Adds complexity, cost, and privacy concerns
**Alternative**: Local filesystem storage with Git LFS for version control

### ❌ Real-Time Browser Monitoring
**Why Not**: Out of scope for MCP server design (file-based comparison workflow)
**Alternative**: Use chrome-devtools MCP for live inspection

---

## Requirements Summary

| Category | Requirements | Phase |
|----------|--------------|-------|
| **Screenshot Capture** | 3 | Phase 2 |
| **Side-by-Side Comparison** | 3 | Phase 3 |
| **Baseline Management** | 3 | Phase 2 |
| **Pass/Fail Determination** | 3 | Phase 3 |
| **Agentic Vision Analysis** | 6 | Phase 3-5 |
| **Expected vs Unintended** | 3 | Phase 2-3 |
| **Conversational Investigation** | 4 | Phase 5 |
| **Non-Functional** | 9 | Phase 1-5 |
| **Total** | **34** | **5 phases** |

---

## Traceability Notes

- **Phase 1 (Foundation)**: 3 non-functional requirements (MCP compliance, types, utilities)
- **Phase 2 (Capture)**: 9 requirements (capture, baseline, expected changes)
- **Phase 3 (Comparison)**: 15 requirements (comparison, validation, agentic vision core) - **HIGH RISK**
- **Phase 4 (Operations)**: 2 non-functional requirements (error messages, cleanup)
- **Phase 5 (Polish)**: 5 requirements (conversational investigation, progressive disclosure)

**Critical Path**: REQ-AGENTIC-01 (Gemini Integration) is the highest-risk requirement and determines project success.

---

**Next Step**: Create ROADMAP.md with 5-8 phases mapping these 34 requirements to execution plans.
