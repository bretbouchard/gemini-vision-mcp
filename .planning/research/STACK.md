# Stack Research - MCP Server + Agentic Vision

## Executive Summary

**Recommended Stack (2025)**: MCP Python SDK 1.26.0+ + MSS (screenshot) + OpenCV (diffing) + Gemini 3 Flash (agentic vision) + google-genai SDK

**Key Innovation**: Gemini 3 Flash's agentic vision capabilities enable iterative zoom/crop/annotate analysis that no existing visual regression tool provides.

**Free Tier Strategy**: Strategic screenshot usage (not mass capture) + aggressive caching + progressive resolution (start low, increase only when needed)

---

## Core Technologies

### MCP Server Framework

**MCP Python SDK** `v1.26.0+` (Official)
- **Rationale**: Official SDK, production-ready, FastMCP decorator-based development
- **Installation**: `pip install mcp`
- **Confidence**: HIGH - Official PyPI package (v1.26.0, 2026-01-24)
- **Docs**: https://github.com/modelcontextprotocol/python-sdk
- **Why NOT alternatives**:
  - `mcp-server-typescript`: TypeScript-based, not Python
  - Custom HTTP implementation: Reinventing wheel, missing protocol updates

**Python** `3.12+`
- **Rationale**: Latest stable, best performance, modern type hints
- **Confidence**: HIGH - Standard Python version
- **Note**: 3.11 also acceptable if dependencies require it

### Screenshot Capture

**MSS** (Multi-Screen Shot) `latest`
- **Rationale**: Fastest cross-platform screenshot library (16-47ms capture time)
- **Installation**: `pip install mss`
- **Confidence**: HIGH - PyPI official, multiple 2025 sources confirming 2.5x faster than PyAutoGUI
- **Performance**: 16-47ms vs PyAutoGUI's ~100ms
- **Why NOT alternatives**:
  - `PIL.ImageGrab`: Slower, less reliable
  - `pyautogui`: Bloated, includes unnecessary features
  - `screenshot`: Windows-only

**Platform-specific tools** (integrated via MSS adapters):
- **macOS**: Built-in MSS support (native)
- **iOS**: `simctl` (Xcode tooling) - needs separate research
- **Web**: `chrome-devtools` MCP server (existing)

### Image Processing

**OpenCV** `cv2` `4.10+`
- **Rationale**: Superior accuracy for pixel-level diffing, faster than Pillow
- **Installation**: `pip install opencv-python`
- **Confidence**: MEDIUM - Multiple 2025 blog posts comparing vs Pillow (no official docs)
- **Use cases**: Pixel diffing, heatmap generation, bounding box annotation
- **Why NOT Pillow only**: Slower, less accurate for pixel operations

**Pillow** `10.4+` (for metadata, I/O)
- **Rationale**: Needed alongside OpenCV for image save/load, metadata handling
- **Installation**: `pip install Pillow`
- **Confidence**: HIGH - Standard Python imaging library

**NumPy** `1.26+` (for array operations)
- **Rationale**: Required by OpenCV, efficient array operations
- **Installation**: `pip install numpy`
- **Confidence**: HIGH - Standard

### Agentic Vision API

**Gemini 3 Flash** `gemini-3-flash-preview`
- **Rationale**: Only API with agentic vision (iterative zoom/crop/annotate + code execution)
- **Installation**: `pip install google-generativeai`
- **SDK**: `google-genai` (GA May 2025, replaces deprecated `generative-ai-python`)
- **Confidence**: HIGH - Official Google AI documentation (2026-01-29)
- **Free Tier**: 15 requests/minute, 250K tokens/minute, 1K requests/day
- **Pricing**: $0.075/1M input tokens, $0.30/1M output tokens
- **Key Features**:
  - Multi-resolution processing (low, medium, high, ultra high)
  - Code execution for image manipulation
  - Iterative visual analysis
  - Conversational image editing
- **Why NOT alternatives**:
  - `GPT-4V`: No agentic vision, expensive
  - `Claude 3.5 Vision`: No iterative zoom/crop workflow
  - `OpenAI Vision`: Limited to static analysis

### Storage

**Filesystem** (built-in Python)
- **Rationale**: Simple, no external dependencies, fast
- **Location**: `<project>/.screenshots/phases/`
- **Format**: PNG for lossless compression
- **Metadata**: JSON sidecar files
- **Cleanup**: Python `glob` + `os.remove`
- **Why NOT database**:
  - Overkill for image storage
  - Adds dependency (SQLite, PostgreSQL)
  - Harder to inspect/debug manually

**Git LFS** (optional, for baseline images)
- **Rationale**: Store large images in Git without bloating repo
- **Installation**: `git lfs install`
- **Use case**: Reference baselines, not transient diffs
- **Confidence**: HIGH - Industry standard

---

## Integration Patterns

### MCP Server Structure

```python
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent

app = Server("wheres-waldo-rick")

@app.tool("visual_capture")
async def visual_capture(name: str) -> str:
    """Capture screenshot and store with metadata"""
    # Delegate to service layer
    return capture_service.capture(name)

@app.tool("visual_compare")
async def visual_compare(before: str, after: str) -> str:
    """Compare two screenshots with agentic vision"""
    # Delegate to service layer
    return compare_service.compare(before, after)

async def main():
    async with stdio_server() as (read_stream, write_stream):
        await app.run(read_stream, write_stream)

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
```

### Gemini Integration Pattern

```python
import google.generativeai as genai
from google.generativeai.types import HarmCategory, HarmBlockThreshold

genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

model = genai.GenerativeModel(
    "gemini-3-flash-preview",
    generation_config=genai.types.GenerationConfig(
        temperature=0.0,  # Deterministic for diffing
        top_p=0.5,
    ),
    safety_settings={
        HarmCategory.HARM_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_NONE,
    }
)

async def analyze_with_agentic_vision(image_path: str, query: str):
    """Iterative visual analysis using Gemini"""
    image = Image.open(image_path)

    # Low-res pass
    response_1 = model.generate_content([
        query,
        image,
        "What do you see? What should we investigate?"
    ])

    # Medium-res pass if needed
    if "zoom" in response_1.text.lower():
        cropped = crop_region(image, response_1.text)
        response_2 = model.generate_content([query, cropped, "Deeper analysis"])

    return response_2.text
```

### Screenshot Capture Pattern

```python
import mss

def capture_screenshot(name: str) -> str:
    """Capture screenshot using MSS"""
    with mss.mss() as sct:
        # Capture primary monitor
        monitor = sct.monitors[1]
        screenshot = sct.grab(monitor)

        # Save as PNG
        path = f".screenshots/phases/{name}.png"
        mss.tools.to_png(screenshot.rgb, screenshot.size, output=path)

        return path
```

---

## Development Tools

### Testing

**pytest** `8.0+` (unit tests)
- **Rationale**: Standard Python testing
- **Installation**: `pip install pytest pytest-asyncio`

**pytest-mock** `3.14+` (mock Gemini API)
- **Rationale**: Don't burn API credits during tests
- **Installation**: `pip install pytest-mock`

### Code Quality

**ruff** `0.6+` (linting + formatting, replaces black, flake8, isort)
- **Rationale**: Fast, all-in-one tool
- **Installation**: `pip install ruff`

**mypy** `1.10+` (type checking)
- **Rationale**: Catch type errors early
- **Installation**: `pip install mypy`

---

## Build & Deployment

### Build System

**uv** `0.5+` (fast Python package installer)
- **Rationale**: 10-100x faster than pip, reliable locking
- **Installation**: `curl -LsSf https://astral.sh/uv/install.sh | sh`
- **Confidence**: HIGH - Emerging standard (2025)

### Packaging

**pyproject.toml` (modern Python packaging)
- **Rationale**: Replaces setup.py, standard format
- **Build backend**: `hatchling` or `setuptools`

---

## Free Tier Considerations

### Gemini API Limits

**Free Tier** (as of 2026-01-29):
- **Rate limit**: 15 requests/minute
- **Tokens**: 250K tokens/minute
- **Daily**: 1K requests/day

**Cost Projection**:
- Screenshot analysis: ~1000 tokens/image
- Comparison: ~2000 tokens (2 images)
- Annotated output: ~500 tokens
- **Total per comparison**: ~3500 tokens = $0.0026

**Strategy**:
1. **Cache aggressively**: Don't re-analyze same screenshots
2. **Progressive resolution**: Start with low-res (cheaper), increase only if needed
3. **Batch when possible**: Compare multiple screenshots in single request
4. **Rate limiting**: Token bucket algorithm to stay within 15 req/min

### Storage Costs

**Screenshot size**:
- PNG: 1-5 MB per screenshot (depending on resolution)
- Metadata JSON: <1 KB

**Phase storage**:
- 3 phases × 2 screenshots = 6 screenshots
- Estimated: 6-30 MB total per project

**Git LFS**:
- Free tier: 1 GB storage
- **Sufficient for**: 200+ projects with 3 phases each

---

## Alternatives Considered

### MCP Framework

❌ **mcp-server-typescript**
- Rationale: TypeScript-based
- Why NOT: Project is Python, mixing languages adds complexity

❌ **Custom HTTP server**
- Rationale: Build MCP protocol from scratch
- Why NOT: Reinventing wheel, missing protocol updates, maintenance burden

### Screenshot Libraries

❌ **PIL.ImageGrab**
- Rationale: Built-in to Pillow
- Why NOT: Slower than MSS (2.5x), less reliable cross-platform

❌ **pyautogui**
- Rationale: Popular screenshot library
- Why NOT: Bloated (includes mouse/keyboard automation), slower ~100ms

❌ **selenium**
- Rationale: Web automation can capture screenshots
- Why NOT: Heavy dependency, overkill for static screenshots

### Vision APIs

❌ **GPT-4V (OpenAI)**
- Rationale: Popular vision model
- Why NOT: No agentic vision, expensive ($0.01-0.03/image), no iterative zoom/crop

❌ **Claude 3.5 Sonnet (Anthropic)**
- Rationale: Strong vision capabilities
- Why NOT: No agentic vision API, limited to static analysis, more expensive

❌ **Stable Diffusion**
- Rationale: Image generation
- Why NOT: Wrong use case (generation vs analysis), no diffing capabilities

### Image Processing

❌ **Pillow-only (no OpenCV)**
- Rationale: Reduce dependencies
- Why NOT: Slower, less accurate for pixel operations, missing advanced features

---

## Open Questions

### iOS Screenshot Capture

**Status**: Need separate research for iOS simulator capture
**Current knowledge**:
- Xcode `simctl` command-line tool can capture screenshots
- Need to verify availability and programmatic access
- May require `xcrun simctl io booted screenshot` pattern

**Research needed**: Phase 2 should investigate iOS capture patterns

### Gemini Code Execution Limits

**Status**: Free tier rate limiting clear, but code execution specifics unclear
**Current knowledge**:
- 15 requests/minute applies to all API calls
- Code execution may have additional constraints
- Need to test actual token usage for iterative zoom/crop workflows

**Research needed**: Phase 3 should test code execution patterns and measure actual costs

### Optimal Blur Strength for Anti-Aliasing

**Status**: Industry standard is 2px Gaussian blur, but edge cases may differ
**Current knowledge**:
- 2px blur eliminates anti-aliasing noise
- May miss some edge cases (subtle 1px changes)
- Need calibration with regression suite

**Research needed**: Phase 2 should test blur strength against 1px, 2px, 3px changes

---

## Recommendations

### v1 Stack

**Core**:
- MCP Python SDK 1.26.0+
- MSS (screenshot capture)
- OpenCV 4.10+ (pixel diffing)
- Gemini 3 Flash (agentic vision)
- google-genai SDK (Gemini integration)

**Supporting**:
- Python 3.12+
- Pillow 10.4+ (metadata/I/O)
- NumPy 1.26+ (array operations)

**Development**:
- uv (package management)
- pytest (testing)
- ruff (linting/formatting)
- mypy (type checking)

### Phase 0 Dependencies

**Before Phase 1**:
- [ ] Get Gemini API key from https://ai.google.dev
- [ ] Verify free tier limits (15 req/min, 250K TPM, 1K RPD)
- [ ] Test basic agentic vision call (zoom/crop/annotate)
- [ ] Verify MSS availability on development machine
- [ ] Set up Git LFS for baseline storage

### Phase-Specific Research

**Phase 2** (Screenshot Capture):
- [ ] Verify axe CLI availability for macOS
- [ ] Research iOS simctl screenshot capabilities
- [ ] Test chrome-devtools MCP integration

**Phase 3** (Gemini Integration):
- [ ] Test actual Gemini API for iterative zoom/crop/annotate
- [ ] Measure token usage for typical comparison
- [ ] Verify code execution works in free tier
- [ ] Calibrate blur strength for 2px detection

---

*Last updated: 2025-02-04*
*Confidence: HIGH (MCP SDK, Gemini, MSS) / MEDIUM (OpenCV, image processing)*
