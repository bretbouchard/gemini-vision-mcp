# Roadmap — Where's Waldo Rick

**Project**: Visual Regression MCP Server with Agentic Vision
**Version**: 1.0
**Last Updated**: 2025-02-04

---

## Overview

This roadmap defines the execution plan for building "Where's Waldo Rick" - an MCP server for visual regression testing using Gemini 3 Flash's agentic vision capabilities.

**Total Phases**: 5
**Total Plans**: 27 (5-7 plans per phase)
**Total Requirements**: 34
**Estimated Duration**: 3-4 weeks (sequential execution)

---

## Phase 1: Foundation (3-4 days)

**Goal**: Establish MCP server infrastructure, type system, and storage layer

**Risk**: LOW
**Dependencies**: None
**Requirements Mapped**: 3

### Plans (5)

#### P1-PLAN-1: MCP Server Skeleton with FastMCP
**Requirements**: REQ-RELIABILITY-03 (MCP JSON-RPC Compliance)
**Deliverables**:
- FastMCP project structure
- Tool stubs: `visual_capture`, `visual_prepare`, `visual_compare`, `visual_cleanup`
- Stderr-only logging (prevents JSON-RPC breaks)
- Exception handler with graceful degradation
- MCP manifest file
- Success Criteria: `mcp list-tools` returns 4 tool stubs, stdout contains only valid JSON

#### P1-PLAN-2: Type System and Domain Models
**Requirements**: REQ-RELIABILITY-03 (MCP JSON-RPC Compliance)
**Deliverables**:
- Pydantic models: `Screenshot`, `Baseline`, `Comparison`, `ExpectedChanges`
- Enums: `Platform` (macOS, iOS, Web), `Quality` (1x, 2x, 3x), `Format` (PNG, JPEG, WebP)
- Validation schemas for expected changes input
- Success Criteria: All models validate correctly, type hints complete

#### P1-PLAN-3: Storage Service (Filesystem + JSON Index)
**Requirements**: REQ-RELIABILITY-03 (MCP JSON-RPC Compliance)
**Deliverables**:
- `.screenshots/phases/` directory structure
- JSON index schema: `index.json` (metadata for all screenshots)
- Storage service class with CRUD operations
- Atomic write operations (prevent corruption)
- Success Criteria: Can create/read/update/delete screenshot metadata

#### P1-PLAN-4: Configuration Management
**Requirements**: REQ-USABILITY-01 (Zero-Config Baseline)
**Deliverables**:
- `.screenshots/config.json` schema
- Default configuration: 2x resolution, PNG format, 2px threshold
- Config loader with fallback to defaults
- Environment variable support (GEMINI_API_KEY, etc.)
- Success Criteria: Works out-of-box with no config file

#### P1-PLAN-5: Utility Functions (Image Hashing, Path Helpers)
**Requirements**: REQ-RELIABILITY-03 (MCP JSON-RPC Compliance)
**Deliverables**:
- SHA256 hash function for image pairs (cache keys)
- Path helpers: `get_phase_dir()`, `get_baseline_path()`
- File naming utilities: `{timestamp}-{phase-name}.png`
- Success Criteria: Hashes consistent for identical images, paths resolve correctly

---

## Phase 2: Capture & Baselines (4-5 days)

**Goal**: Screenshot capture from multiple platforms with baseline management

**Risk**: MEDIUM
**Dependencies**: Phase 1 complete
**Requirements Mapped**: 9

### Plans (6)

#### P2-PLAN-1: Platform Detection and Auto-Selection
**Requirements**: REQ-CAPTURE-01 (Multi-Platform Screenshot Capture)
**Deliverables**:
- Platform detection logic (check for iOS Simulator, macOS, chrome-devtools MCP)
- Fallback to manual platform selection
- Platform adapter interface
- Success Criteria: Auto-detects platform in 95% of cases

#### P2-PLAN-2: macOS Screenshot Adapter (MSS)
**Requirements**: REQ-CAPTURE-01, REQ-PERF-01 (Capture Latency < 100ms)
**Deliverables**:
- MSS integration for fast capture (16-47ms)
- Retina support (2x/3x scaling)
- Format selection (PNG/JPEG/WebP)
- Success Criteria: Capture time < 100ms measured

#### P2-PLAN-3: iOS Simulator Adapter (simctl)
**Requirements**: REQ-CAPTURE-01, REQ-PERF-01 (Capture Latency < 500ms)
**Deliverables**:
- simctl CLI wrapper for iOS screenshots
- Device boot check (error if simulator not running)
- Simulator selection (multiple devices support)
- Success Criteria: Capture time < 500ms measured

#### P2-PLAN-4: Web Screenshot Adapter (chrome-devtools MCP)
**Requirements**: REQ-CAPTURE-01, REQ-PERF-01 (Capture Latency < 1s)
**Deliverables**:
- chrome-devtools MCP integration
- Page screenshot capture (viewport or full page)
- Multi-tab support
- Success Criteria: Capture time < 1s measured

#### P2-PLAN-5: Baseline Declaration with Expected Changes
**Requirements**: REQ-BASELINE-01, REQ-BASELINE-02, REQ-EXPECTED-01
**Deliverables**:
- `visual_prepare` tool implementation
- Expected changes input format (JSON + natural language)
- Baseline ID generation (timestamp-based)
- Metadata storage (phase, description, expected changes)
- Success Criteria: Can declare baseline with expected changes

#### P2-PLAN-6: Screenshot Organization and Listing
**Requirements**: REQ-CAPTURE-02 (Phase-Based Organization)
**Deliverables**:
- `visual_capture` tool implementation
- Phase directory auto-creation
- JSON index updates on each capture
- `visual_list` tool for browsing screenshots
- Success Criteria: Screenshots organized by phase, searchable

---

## Phase 3: Comparison Engine with Gemini Integration (7-10 days) ⚠️ HIGH RISK

**Goal**: Pixel-perfect diffing with Gemini 3 Flash agentic vision analysis

**Risk**: HIGH
**Dependencies**: Phase 2 complete, Gemini API access
**Requirements Mapped**: 15

### Plans (7)

#### P3-PLAN-1: OpenCV Integration for Pixel Diffing
**Requirements**: REQ-COMPARE-01, REQ-PERF-02 (Comparison Speed < 2s)
**Deliverables**:
- OpenCV 4.10+ installation and import
- Absolute difference calculation
- Configurable threshold (1px, 2px, 3px)
- Total changed pixels and percentage
- Success Criteria: Comparison time < 2s for 1080p images

#### P3-PLAN-2: Anti-Aliasing Noise Reduction
**Requirements**: REQ-COMPARE-02, REQ-PERF-02
**Deliverables**:
- 2px Gaussian blur preprocessing
- Enable/disable toggle
- Anti-aliasing test suite (10 known cases)
- Success Criteria: >80% false positive reduction

#### P3-PLAN-3: Heatmap Diff Visualization
**Requirements**: REQ-COMPARE-03
**Deliverables**:
- Color gradient generator (yellow → orange → red)
- Overlay composer (original + heatmap)
- Adjustable opacity (20-80%)
- Export functionality
- Success Criteria: Heatmaps clearly show change intensity

#### P3-PLAN-4: Gemini 3 Flash Client Integration 🔥 CRITICAL PATH
**Requirements**: REQ-AGENTIC-01, REQ-PERF-03 (Agentic Vision Response < 10s)
**Deliverables**:
- google-genai SDK setup
- gemini-3-flash-preview model configuration
- Agentic vision API wrapper (multi-resolution)
- Code execution for image manipulation (crop, annotate)
- Error handling with retry logic
- Success Criteria: Successful agentic vision call with annotated output

**Risk Mitigation**:
- Start with low-resolution analysis (720p) to minimize cost
- Implement rate limiter BEFORE first API call
- Have fallback to pixel-only diffing if Gemini fails

#### P3-PLAN-5: Token Bucket Rate Limiter
**Requirements**: REQ-AGENTIC-06, REQ-RELIABILITY-01 (Rate Limit Compliance)
**Deliverables**:
- Token bucket algorithm (15 tokens/min refill rate)
- Request queue with position tracking
- Queue status display (position, ETA)
- Burst allowance (up to 15 if full bucket)
- Backpressure notification (queue > 5)
- Success Criteria: 99.9% compliance with 15 req/min limit

#### P3-PLAN-6: Intelligent Change Interpretation
**Requirements**: REQ-AGENTIC-02, REQ-EXPECTED-02
**Deliverables**:
- Gemini prompt engineering for UI element analysis
- Natural language change descriptions ("padding increased by 2px on top of card")
- Confidence scoring (0-100%)
- Fallback to pixel coordinates if interpretation fails
- Success Criteria: Interpretations match human assessment in >80% of cases

#### P3-PLAN-7: Intended vs Unintended Classification
**Requirements**: REQ-EXPECTED-02, REQ-EXPECTED-03, REQ-VALIDATION-01, REQ-VALIDATION-02
**Deliverables**:
- Expected changes parser (natural language → structured)
- Classification algorithm (match by proximity, description, bounding box)
- Visual distinction: green (intended), red (unintended), yellow (ambiguous)
- Severity scoring: critical, major, minor
- Regression alerting with summary counts
- Pass/fail determination based on thresholds
- Success Criteria: Correctly classifies known intended/unintended changes

---

## Phase 4: Operations & Validation (3-4 days)

**Goal**: Robust error handling, cleanup, reporting, and caching

**Risk**: LOW
**Dependencies**: Phase 3 complete
**Requirements Mapped**: 5

### Plans (4)

#### P4-PLAN-1: Aggressive Caching System
**Requirements**: REQ-AGENTIC-04, REQ-RELIABILITY-02 (Cache Hit Rate > 60%)
**Deliverables**:
- Hash-based cache key (image pair + threshold)
- Cache storage (filesystem: `.screenshots/cache/`)
- Cache invalidation on config change
- Cache statistics (hit rate, API calls saved)
- Success Criteria: >60% cache hit rate in repeated comparisons

#### P4-PLAN-2: Progressive Resolution Strategy
**Requirements**: REQ-AGENTIC-05
**Deliverables**:
- Resolution ladder: 720p → 1080p → 4K → 8K
- Confidence threshold check (upgrade if < 80%)
- Token usage tracking per comparison
- Cost estimation display
- Success Criteria: Average token savings > 30% vs full-resolution

#### P4-PLAN-3: Comparison Report Generation
**Requirements**: REQ-VALIDATION-03, REQ-BASELINE-03
**Deliverables**:
- Markdown report template
- Embedded screenshots with annotations
- Pass/fail badge with criteria
- Change summary table (intended vs unintended)
- Report storage (`.screenshots/reports/`)
- Success Criteria: Reports readable and actionable

#### P4-PLAN-4: Cleanup and Maintenance Tools
**Requirements**: REQ-USABILITY-02 (Clear Error Messages)
**Deliverables**:
- `visual_cleanup` tool implementation
- 7-day retention policy (configurable)
- Old screenshot deletion
- Cache clearing
- Storage stats display
- Actionable error messages for all failure modes
- Success Criteria: Storage doesn't bloat, errors have remediation steps

---

## Phase 5: Polish & Conversational Investigation (3-4 days)

**Goal**: Multi-turn conversational UI with progressive disclosure

**Risk**: LOW-MEDIUM
**Dependencies**: Phase 4 complete
**Requirements Mapped**: 5

### Plans (5)

#### P5-PLAN-1: Multi-Turn Conversation Context
**Requirements**: REQ-CONV-01, REQ-AGENTIC-03
**Deliverables**:
- Conversation state management (5-turn limit)
- Context persistence (comparison, questions, answers)
- Turn counter with graceful exit
- Conversation summary on exit
- Success Criteria: Can maintain context across 5 turns

#### P5-PLAN-2: Focused Follow-Up Analysis
**Requirements**: REQ-CONV-02
**Deliverables**:
- Follow-up question parser ("Where exactly did the padding change?")
- Focused region analysis (zoom, crop)
- Annotated screenshot generation (circles, arrows)
- Bounding box coordinate returns
- Success Criteria: Follow-up questions generate targeted annotations

#### P5-PLAN-3: Conversational UI Pattern Matching
**Requirements**: REQ-CONV-03
**Deliverables**:
- Pattern recognition: "Zoom in on {region}", "Crop to {element}", "Annotate {change}", "Measure {dimension}", "Compare {region A} with {region B}"
- Fuzzy intent matching
- Fallback to generic analysis
- Success Criteria: Recognizes 5+ common patterns

#### P5-PLAN-4: Conversation History Persistence
**Requirements**: REQ-CONV-04
**Deliverables**:
- Conversation storage (`.screenshots/conversations/`)
- JSON format (timestamp, question, answer, annotations)
- Search by comparison ID, date, content
- Export to markdown
- Success Criteria: Conversations searchable and auditable

#### P5-PLAN-5: Progressive Disclosure and Usability Polish
**Requirements**: REQ-USABILITY-03 (Progressive Disclosure)
**Deliverables**:
- Opt-in flags for advanced features (conversational mode, custom thresholds)
- Simplified default workflow (capture → compare → report)
- Help text and examples
- Success Criteria: New users can capture and compare without reading docs

---

## Phase Summary

| Phase | Name | Plans | Requirements | Risk | Duration |
|-------|------|-------|--------------|------|----------|
| **1** | Foundation | 5 | 3 | LOW | 3-4 days |
| **2** | Capture & Baselines | 6 | 9 | MEDIUM | 4-5 days |
| **3** | Comparison Engine | 7 | 15 | **HIGH** | 7-10 days |
| **4** | Operations & Validation | 4 | 5 | LOW | 3-4 days |
| **5** | Polish & Conversational | 5 | 5 | LOW-MEDIUM | 3-4 days |
| **Total** | | **27** | **34** | | **20-27 days** |

---

## Success Criteria by Phase

### Phase 1 Success
- ✅ MCP server starts and registers 4 tool stubs
- ✅ Stdout contains only valid JSON (no pollution)
- ✅ Storage service can create/read/delete metadata
- ✅ Configuration works with zero setup

### Phase 2 Success
- ✅ Can capture screenshots from macOS, iOS Simulator, and web
- ✅ Capture times meet performance targets (< 100ms macOS, < 500ms iOS, < 1s web)
- ✅ Screenshots organized by phase with searchable index
- ✅ Baselines declared with expected changes

### Phase 3 Success (CRITICAL)
- ✅ Pixel-level comparison completes in < 2s
- ✅ Anti-aliasing false positives reduced by >80%
- ✅ Gemini 3 Flash integration returns annotated analysis
- ✅ Rate limiter maintains 99.9% compliance with 15 req/min
- ✅ Intended vs unintended classification works accurately
- ✅ **Risk**: If Gemini integration fails, fallback to pixel-only diffing

### Phase 4 Success
- ✅ Cache hit rate > 60%
- ✅ Progressive resolution saves > 30% tokens
- ✅ Comparison reports are readable and actionable
- ✅ Storage doesn't bloat (cleanup works)

### Phase 5 Success
- ✅ Multi-turn conversations maintain context across 5 turns
- ✅ Follow-up questions generate targeted annotations
- ✅ Conversational patterns recognized (zoom, crop, annotate, measure, compare)
- ✅ New users can use default workflow without reading docs

---

## Risk Mitigation Strategies

### 🔥 Critical Risk: Phase 3 Gemini Integration

**Risk**: Gemini API fails, rate limits exceeded, or costs blow up

**Mitigation**:
1. **Token Bucket First**: Implement rate limiter BEFORE first API call
2. **Low-Resolution First**: Start with 720p, upgrade only if needed
3. **Aggressive Caching**: Cache every analysis result
4. **Fallback Strategy**: Pixel-only diffing if Gemini fails
5. **Cost Tracking**: Display token usage and estimated cost per comparison
6. **Free Tier Monitoring**: Alert at 80% of daily/monthly limits

### Secondary Risk: Anti-Aliasing False Positives

**Risk**: Too many false positives from rendering artifacts

**Mitigation**:
1. **2px Gaussian Blur**: Standard preprocessing step
2. **Calibration Suite**: Test with 10 known anti-aliasing cases
3. **Smart Thresholding**: Adjust threshold based on image complexity
4. **User Override**: Allow manual threshold adjustment

### Tertiary Risk: Storage Bloat

**Risk**: Screenshots consume too much disk space

**Mitigation**:
1. **7-Day Retention**: Auto-cleanup old screenshots
2. **Git LFS**: Use Git LFS for version control
3. **Compression**: JPEG/WebP options for large screenshots
4. **Storage Stats**: Display disk usage and cleanup recommendations

---

## Dependencies

### External Dependencies
- **MCP Python SDK 1.26.0+**: MCP server framework
- **MSS**: Fast screenshot capture for macOS
- **OpenCV 4.10+**: Pixel-level diffing
- **google-genai SDK**: Gemini 3 Flash integration
- **Pydantic**: Type validation

### Platform Dependencies
- **macOS**: MSS for screenshots
- **iOS Simulator**: simctl CLI tool
- **Web**: chrome-devtools MCP server

### API Keys Required
- **GEMINI_API_KEY**: For Gemini 3 Flash access (free tier)

---

## Execution Strategy

### Sequential Execution (Required for z.ai 1-concurrent limit)
- All 27 plans executed sequentially
- Each plan must complete successfully before next starts
- Checkpoints after each phase (commit and tag)

### Milestones
1. **M1 - Foundation Complete**: Phase 1 done, MCP server functional
2. **M2 - Capture Complete**: Phase 2 done, screenshots can be captured
3. **M3 - Comparison Complete** 🔥: Phase 3 done, Gemini integration working (CRITICAL)
4. **M4 - Operations Complete**: Phase 4 done, caching and reporting working
5. **M5 - v1 Ready**: Phase 5 done, conversational investigation working

### Rollback Strategy
- Each phase committed separately with git tags
- If Phase 3 fails, rollback to Phase 2 and use pixel-only diffing
- If rate limits exceeded, implement more aggressive caching

---

## Post-v1 Considerations (Future)

### Potential v2 Features
- Historical comparison across all phases
- Visual change timeline/gifs
- A/B test comparison
- Performance regression (screenshot + timing)
- Accessibility regression overlay
- Automated regression test suite

### Technical Debt to Track
- Migration path if Gemini free tier changes
- Alternative vision models (OpenAI GPT-4V, Claude 3.5 Sonnet)
- Cloud storage option for teams
- CI/CD integration (if rate limits allow)

---

## Open Questions

1. **Gemini API Key Management**: How to securely store and rotate API keys?
2. **Cost Monitoring**: Should we implement daily/monthly budget limits?
3. **Fallback Mode**: If Gemini is unavailable, how degraded should the experience be?
4. **Multi-User Support**: Should v1 support multiple users sharing screenshot storage?
5. **Platform Expansion**: Should we add Android or Windows support in v1?

---

**Next Step**: Begin Phase 1 execution with `/gsd:execute-phase 1`

**Critical Success Factor**: Phase 3 (Gemini Integration) - this phase determines project viability
