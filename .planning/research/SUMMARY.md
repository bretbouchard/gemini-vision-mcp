# Research Summary - Where's Waldo Rick

## Overview

**Project**: Where's Waldo Rick - Visual Regression MCP Server with Agentic Vision

**Research Confidence**: HIGH (stack, features) / MEDIUM (architecture, pitfalls)

**Key Finding**: **Agentic vision using Gemini 3 Flash is a clear differentiator** - no existing visual regression tool offers iterative zoom/crop/annotate analysis with expected vs unintended change detection.

---

## Stack Summary

**Recommended Technology**:

| Component | Technology | Version | Confidence |
|-----------|-----------|---------|------------|
| MCP Server | MCP Python SDK | 1.26.0+ | HIGH |
| Screenshot Capture | MSS (Multi-Screen Shot) | latest | HIGH |
| Image Processing | OpenCV | 4.10+ | MEDIUM |
| Agentic Vision | Gemini 3 Flash | gemini-3-flash-preview | HIGH |
| Gemini SDK | google-genai | GA May 2025 | HIGH |
| Storage | Filesystem + JSON | built-in | HIGH |

**Key Decisions**:
- Python 3.12+ for modern type hints
- MSS: 2.5x faster than PyAutoGUI (16-47ms vs ~100ms)
- OpenCV: Superior pixel diffing vs Pillow
- Gemini: Only API with agentic vision capabilities
- Filesystem storage: Simple, no database overhead

**Free Tier Considerations**:
- Gemini: 15 req/min, 250K TPM, 1K RPD
- Cost: ~$0.0026 per comparison (3500 tokens)
- Strategy: Cache aggressively, progressive resolution

---

## Features Summary

### Table Stakes (Must-Have)

✅ Screenshot capture (manual + auto)
✅ Side-by-side comparison
✅ Diff visualization (heatmap)
✅ Baseline management
✅ Pass/fail with threshold

**Competitors have these**: Playwright, Chromatic, Applitools

### Differentiators (Competitive Advantage)

⭐ **Agentic vision analysis** - NO existing tool offers this
⭐ Expected vs unintended change detection
⭐ Conversational investigation ("What changed in the header?")
⭐ Regional analysis ("the box it's in, not the card")

**Competitors lack these**: ALL existing tools are static diff only

### Anti-Features (Deliberately NOT Building)

❌ Mass CI/CD integration (burns free tier)
❌ Cross-browser testing matrix (not target use case)
❌ Pixel-perfect strict mode (false positive noise storm)
❌ Automated scheduling (not manual/on-demand focus)

---

## Architecture Summary

### Component Structure

```
MCP Tools (Thin Wrappers)
    ↓
Service Layer (Business Logic)
    ├─→ Capture Service (Platform adapters)
    ├─→ Compare Service (Pixel diff + Gemini)
    └─→ Storage Service (Filesystem + JSON index)
    ↓
External Integrations
    ├─→ Platform Adapters (macOS, iOS, Web)
    ├─→ Gemini API (Rate-limited)
    └─→ Local Storage (Screenshots)
```

### Key Patterns

**Tool as Orchestrator**: MCP tools delegate to service layer
**Multi-Platform Adapters**: Abstract capture interface, platform-specific implementations
**Rate-Limited External Service**: Token bucket (15 req/min), retry with exponential backoff
**Filesystem with JSON Index**: Screenshots + metadata, automated cleanup

### Build Order

1. **Phase 1**: Foundation (storage, types, utilities)
2. **Phase 2**: Capture (platform adapters, capture service)
3. **Phase 3**: Comparison (pixel diffing, Gemini integration) - HIGH RISK
4. **Phase 4**: Operations (cleanup, MCP tool exposure)

---

## Pitfalls Summary

### Critical Pitfalls (Project-Blocking)

1. **Free Tier Exhaustion**
   - 15 req/min easily exceeded without rate limiting
   - **Prevention**: Token bucket, aggressive caching, progressive resolution
   - **Phase**: Phase 3 (Gemini Integration)

2. **Anti-Aliasing False Positives**
   - Font rendering creates noise storms
   - **Prevention**: 2px Gaussian blur preprocessing
   - **Phase**: Phase 2 (Comparison Engine)

3. **Storage Bloat**
   - Screenshots accumulate at 10MB+ per run
   - **Prevention**: Automated cleanup, Git LFS, compression
   - **Phase**: Phase 4 (Operations)

4. **MCP JSON-RPC Breaks**
   - stdout pollution from Python stack traces
   - **Prevention**: Stderr-only logging, exception handler
   - **Phase**: Phase 1 (Foundation)

5. **Missing Subtle Regressions**
   - Threshold too high misses 2px changes
   - **Prevention**: Calibration regression suite, multi-threshold
   - **Phase**: Phase 2 (Comparison Engine)

---

## Competitive Analysis

### Playwright (Microsoft)

**Strengths**: Free, CI/CD integration, cross-browser
**Weaknesses**: Static diff only, no AI, no conversational interface
**Gap**: No agentic vision, no intelligent interpretation

### Chromatic

**Strengths**: Git integration, good UI, team features
**Weaknesses**: Expensive ($20+/user), static diff only
**Gap**: No conversational investigation, no expected change validation

### Applitools (Eyes)

**Strengths**: AI-powered layout matching, enterprise features
**Weaknesses**: Very expensive ($100+/month), AI for layout not conversation
**Gap**: No agentic vision, no expected vs unintended detection

### Where's Waldo Rick

**Advantages**:
- ✅ Agentic vision (iterative zoom/crop/annotate)
- ✅ Expected vs unintended change detection
- ✅ Conversational investigation
- ✅ Free tier conscious (strategic usage)
- ✅ AI agent-focused (not CI/CD)

---

## Roadmap Implications

### Phase Structure (Recommended)

**Phase 1: Foundation** (3-5 plans)
- Storage service (filesystem + JSON index)
- Type definitions
- Utilities (image I/O, hashing)
- MCP server setup
- Stderr-only logging (prevent JSON-RPC breaks)

**Phase 2: Capture** (5-7 plans)
- Capture orchestrator
- Platform adapters (macOS, iOS, Web)
- Capture service
- 2px Gaussian blur preprocessing (prevent false positives)
- Calibration regression suite (detect 1px, 2px, 3px changes)

**Phase 3: Comparison** (7-10 plans) - **HIGH RISK**
- Pixel diffing (OpenCV)
- Gemini client (rate-limited, token bucket)
- Agentic vision workflow (iterative analysis)
- Compare service
- Cost tracking
- Cache management
- Progressive resolution (low → medium → high)

**Phase 4: Operations** (3-5 plans)
- Automated cleanup (7-day retention, keep last N)
- MCP tool exposure
- Query operations (list, find)
- Git LFS integration
- Documentation

**Phase 5: Polish** (3-5 plans)
- Comprehensive testing
- Performance optimization
- Error handling improvements
- User documentation
- Public GitHub release

**Total**: 21-32 plans across 5 phases (comprehensive depth)

### Risk Areas

**HIGH RISK**: Phase 3 (Gemini Integration)
- Unverified API capabilities (iterative zoom/crop/annotate)
- Unknown actual costs (token usage varies)
- No established patterns to follow

**Mitigation**: Phase-specific research before implementation
- Test actual Gemini API for agentic vision
- Measure token usage with real screenshots
- Verify code execution in free tier
- Calibrate blur strength for 2px detection

---

## Open Questions

### Requires Phase-Specific Research

**Phase 2** (Screenshot Capture):
- ✅ axe CLI availability for macOS
- ❓ iOS simctl screenshot capabilities
- ❓ chrome-devtools MCP integration patterns

**Phase 3** (Gemini Integration) - **HIGH PRIORITY**:
- ❓ Can Gemini actually do iterative zoom/crop/annotate?
- ❓ How many turns does conversational investigation support?
- ❓ What's actual token usage for typical comparison?
- ❓ Does code execution work in free tier?

**Phase 4** (Operations):
- ❓ Optimal annotation format (overlay vs side-by-side vs HTML)?
- ❓ Git LFS impact on git operations?

---

## Next Steps

### Immediate Actions

1. **Get Gemini API Key** from https://ai.google.dev
2. **Verify Free Tier Limits** (15 req/min, 250K TPM, 1K RPD)
3. **Test Basic Agentic Vision Call** (zoom/crop/annotate)
4. **Verify MSS Availability** on development machine
5. **Set Up Git LFS** for baseline storage

### Research-to-Requirements Mapping

**From STACK.md** → Requirements:
- MCP SDK integration
- Multi-platform capture (macOS, iOS, Web)
- Pixel diffing with OpenCV
- Gemini 3 Flash integration
- Storage with cleanup policies

**From FEATURES.md** → Requirements:
- Table stakes (capture, compare, baseline, pass/fail)
- Differentiators (agentic vision, expected vs unexpected, conversational)
- Anti-features (no CI/CD, no cross-browser, no strict mode)

**From ARCHITECTURE.md** → Requirements:
- Tool layer (MCP protocol)
- Service layer (capture, compare, storage)
- Platform adapters (macOS, iOS, Web)
- Error handling (rate limits, retries, storage)

**From PITFALLS.md** → Requirements:
- Rate limiting (token bucket, 15 req/min)
- Anti-aliasing blur (2px Gaussian)
- Storage cleanup (automated, retention policies)
- Stderr logging (prevent JSON-RPC breaks)
- Calibration suite (detect 1px, 2px, 3px)

---

## Success Criteria

**Product Success**:
- ✅ Can definitively answer "What changed?" with visual proof
- ✅ Catch unintended layout regressions before users do
- ✅ Have nuanced conversations about specific UI elements
- ✅ Proof that visual work actually happened

**Technical Success**:
- ✅ MCP server integrates seamlessly with Claude Code
- ✅ Stays within Gemini free tier (strategic usage)
- ✅ Screenshot storage doesn't bloat projects
- ✅ Pixel-perfect diff accuracy

**Workflow Success**:
- ✅ Fits naturally into existing GSD workflow
- ✅ Doesn't add friction to development process
- ✅ AI agents can use it autonomously
- ✅ Manual control when needed

---

## Confidence Assessment

| Area | Confidence | Reasoning |
|------|------------|-----------|
| MCP SDK & Python Stack | HIGH | Official documentation, verified versions |
| Gemini 3 Flash Capabilities | MEDIUM | Marketing materials confirm features, need API testing |
| Screenshot Libraries (MSS) | HIGH | PyPI official, multiple 2025 sources |
| OpenCV vs Pillow | MEDIUM | Multiple 2025 comparisons, no official docs |
| Architecture Patterns | HIGH | Based on MCP best practices, proven patterns |
| Free Tier Limits | HIGH | Official Gemini documentation verified |
| Pitfall Prevention | HIGH | Industry standard solutions (blur, rate limiting) |

**Overall Confidence**: HIGH for stack/architecture, MEDIUM for unverified Gemini capabilities (requires Phase 3 testing)

---

## Ready for Requirements

Research complete. All four dimensions (Stack, Features, Architecture, Pitfalls) documented with clear phase implications and risk areas.

**Recommendation**: Proceed to requirements definition with comprehensive depth (8-12 phases, 5-10 plans each) as configured.

**Key Risks to Monitor**: Phase 3 (Gemini Integration) requires phase-specific research before implementation.

---

*Last updated: 2025-02-04*
*Research complete, proceeding to requirements definition*
