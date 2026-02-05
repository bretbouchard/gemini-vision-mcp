# Pitfalls Research - Visual Regression + MCP Servers

## Executive Summary

**Critical Pitfalls Discovered**:
1. **Free Tier Exhaustion** - 15 req/min easily exhausted without strict rate limiting
2. **Anti-Aliasing False Positives** - Pixel-perfect comparison creates noise storms
3. **Storage Bloat** - Screenshots accumulate at 10MB+ per run
4. **MCP JSON-RPC Breaks** - stdout pollution from Python stack traces
5. **Missing Subtle Regressions** - Threshold too high defeats 2px detection

**Prevention Strategies**: Token bucket rate limiting, 2px Gaussian blur preprocessing, automated cleanup, stderr-only logging, threshold calibration.

---

## Critical Pitfalls (Project-Blocking)

### 1. Free Tier Exhaustion

**Symptom**: API quota exhausted mid-project, costs money, workflow breaks

**Root Cause**:
- Gemini free tier: 15 requests/minute, 250K tokens/minute, 1K requests/day
- Easy to exceed with mass screenshots
- No built-in rate limiting in MCP server

**Warning Signs**:
- HTTP 429 errors increasing
- API responses taking >30s
- "Quota exceeded" error messages

**Prevention Strategy**:

**Token Bucket Rate Limiter**:
```python
class TokenBucketRateLimiter:
    def __init__(self, rate=15, per=60):
        self.allowance = rate
        self.rate = rate
        self.per = per
        self.last_check = time.time()

    async def acquire(self):
        with threading.Lock():
            current = time.time()
            time_passed = current - self.last_check
            self.last_check = current

            # Refill based on time passed
            self.allowance += time_passed * (self.rate / self.per)

            if self.allowance > self.rate:
                self.allowance = self.rate

            if self.allowance < 1:
                # Wait until token available
                sleep_time = (1 - self.allowance) * (self.per / self.rate)
                await asyncio.sleep(sleep_time)
                self.allowance = 0
            else:
                self.allowance -= 1
```

**Aggressive Caching**:
```python
class CachedGeminiClient:
    def __init__(self):
        self.cache = {}  # {image_hash: analysis_result}

    async def analyze(self, image, query):
        image_hash = hashlib.sha256(image.tobytes()).hexdigest()

        if image_hash in self.cache:
            return self.cache[image_hash]

        result = await self.gemini.generate_content([query, image])
        self.cache[image_hash] = result
        return result
```

**Progressive Resolution**:
```python
async def analyze_with_progressive_resolution(image, query):
    # Try low-res first (cheap)
    small = resize_image(image, 512)
    result = await gemini.generate_content([query, small])

    if "zoom" not in result.text.lower():
        return result  # Low-res was sufficient

    # Only upgrade to medium-res if needed
    medium = resize_image(image, 1024)
    return await gemini.generate_content([query, medium])
```

**Cost Tracking**:
```python
class CostTracker:
    def __init__(self, daily_budget=1000):  # 1K requests/day
        self.daily_usage = 0
        self.daily_budget = daily_budget

    def check_budget(self):
        if self.daily_usage >= self.daily_budget:
            raise BudgetExceeded("Daily budget exceeded")

    def record_request(self):
        self.daily_usage += 1
```

**Phase to Address**: Phase 3 (Gemini Integration) - Must implement before any API calls

**Recovery Plan**:
- If quota exhausted: Switch to cached results only
- If costs too high: Reduce resolution, increase cache TTL
- Monitor: Log every API call with token count

---

### 2. Anti-Aliasing False Positives

**Symptom**: Thousands of "changes" detected, all anti-aliasing noise, unusable

**Root Cause**:
- Font rendering creates sub-pixel variations
- Browser rendering differences (macOS vs Windows)
- Anti-aliasing algorithms vary by platform

**Example**:
```
Expected: 1 change (card padding +2px)
Actual: 1,247 changes (all text edges)
Result: Noise storm, impossible to use
```

**Warning Signs**:
- >100 changes for simple layout shifts
- Changes clustered around text elements
- Heatmap shows speckled pattern (not contiguous regions)

**Prevention Strategy**:

**2-Pixel Gaussian Blur Preprocessing**:
```python
import cv2
import numpy as np

def preprocess_for_diff(image):
    """Apply 2px Gaussian blur to eliminate anti-aliasing noise"""
    return cv2.GaussianBlur(image, (5, 5), sigmaX=2)

def pixel_diff_with_blur(before, after, threshold=0.1):
    # Preprocess both images
    before_blur = preprocess_for_diff(before)
    after_blur = preprocess_for_diff(after)

    # Calculate diff on blurred images
    diff = cv2.absdiff(before_blur, after_blur)

    # Threshold
    _, thresh = cv2.threshold(diff, int(255 * threshold), 255, cv2.THRESH_BINARY)

    return thresh
```

**Calibration with Regression Suite**:
```python
# Test images with known 1px, 2px, 3px changes
test_cases = [
    ("1px-padding.png", 1),
    ("2px-padding.png", 2),
    ("3px-padding.png", 3),
]

for image, expected_pixels in test_cases:
    result = detect_changes(image)
    assert result.pixel_change == expected_pixels, f"Failed to detect {expected_pixels}px"
```

**Smart Thresholding**:
```python
def adaptive_threshold(image):
    """Calculate threshold based on image complexity"""
    # Simple images: lower threshold (detect 1px changes)
    # Complex images: higher threshold (reduce noise)
    edge_density = detect_edge_density(image)
    return 0.05 if edge_density < 0.1 else 0.15
```

**Phase to Address**: Phase 2 (Comparison Engine) - Must implement before pixel diffing

**Recovery Plan**:
- If false positives flood: Increase blur strength (3px, 4px)
- If missing real changes: Reduce blur strength (1px)
- If uncalibrated: Run regression suite to tune threshold

---

### 3. Storage Bloat

**Symptom**: Projects become 500MB+ from screenshots, slow git operations, disk full

**Root Cause**:
- PNG screenshots: 1-5 MB each
- No automated cleanup
- Baselines + diffs + annotations multiply storage

**Example**:
```
3 phases × 2 screenshots × 5 MB = 30 MB (per comparison)
10 comparisons = 300 MB
No cleanup = 3 GB bloat
```

**Warning Signs**:
- `.screenshots/` directory >100 MB
- Git operations slow (git status takes >10s)
- Disk space warnings

**Prevention Strategy**:

**Automated Cleanup Policy**:
```python
class StorageCleanup:
    def __init__(self, retention_days=7, keep_last_n=3):
        self.retention_days = retention_days
        self.keep_last_n = keep_last_n

    def cleanup_old_screenshots(self):
        """Delete screenshots older than retention days, except last N"""
        screenshots = self.list_screenshots()

        # Delete by age
        old = [s for s in screenshots if s.age_days > self.retention_days]

        # Keep last N regardless of age
        recent = sorted(screenshots, key=lambda s: s.timestamp)[-self.keep_last_n:]

        to_delete = set(old) - set(recent)

        for screenshot in to_delete:
            self.delete(screenshot)
```

**Git LFS for Baselines**:
```bash
# .gitattributes
*.png filter=lfs diff=lfs merge=lfs -text
screenshots/phases/*.png filter=lfs
```

**Compression**:
```python
def compress_screenshot(image):
    """Compress PNG while maintaining quality"""
    buffer = io.BytesIO()
    image.save(buffer, format='PNG', optimize=True, compress_level=9)
    return buffer.getvalue()
```

**Metadata-Only Storage for Diffs**:
```python
# Don't store full diff image, just metadata
diff_result = {
    "before": "01-baseline.png",
    "after": "02-current.png",
    "changes": [
        {"region": "card", "change": "+2px padding", "bbox": [100, 100, 200, 150]}
    ]
}
save_json("01-vs-02-diff.json", diff_result)
```

**Phase to Address**: Phase 4 (Operations) - Must implement before storing many screenshots

**Recovery Plan**:
- If already bloated: One-time cleanup script to remove old screenshots
- If git slow: Migrate to Git LFS
- If disk full: Emergency cleanup, delete all except last 2 phases

---

### 4. MCP JSON-RPC Breaks

**Symptom**: MCP server crashes, Claude Code can't communicate, tools don't respond

**Root Cause**:
- Python stack traces print to stdout
- MCP protocol expects only JSON on stdout
- Any non-JSON output breaks protocol

**Example**:
```python
# WRONG - Breaks MCP
print("Debugging screenshot capture...")
raise ValueError("Invalid screenshot")

# CORRECT - Debug to stderr
sys.stderr.write("Debugging screenshot capture...\n")
raise ValueError("Invalid screenshot")
```

**Warning Signs**:
- MCP tools don't appear in Claude Code
- "Tool not found" errors
- Claude Code can't call tools

**Prevention Strategy**:

**Stderr-Only Logging**:
```python
import logging
import sys

# Configure all logging to stderr
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    stream=sys.stderr  # CRITICAL: stderr, not stdout
)

logger = logging.getLogger(__name__)

# Use logger, never print
logger.info("Capturing screenshot...")  # Goes to stderr
# print("Capturing screenshot...")     # WRONG: Goes to stdout
```

**Exception Handler**:
```python
import sys
import traceback

def mcp_error_handler(exc_type, exc_value, exc_traceback):
    """Route all exceptions to stderr"""
    sys.stderr.write(''.join(traceback.format_exception(exc_type, exc_value, exc_traceback)))
    sys.stderr.flush()

sys.excepthook = mcp_error_handler
```

**Validation**:
```python
# Test MCP server doesn't pollute stdout
def test_stdout_pollution():
    proc = subprocess.run(['python', '-m', 'mcp_server'], capture_output=True)
    assert proc.stdout == b'', f"Stdout polluted: {proc.stdout}"
    assert b'error' in proc.stderr or proc.returncode == 0
```

**Phase to Address**: Phase 1 (Foundation) - Must implement before MCP server runs

**Recovery Plan**:
- If MCP breaks: Check stdout for pollution, add exception handler
- If tools don't appear: Verify JSON-RPC protocol compliance
- Test: Run MCP server standalone, check stdout

---

### 5. Missing Subtle Regressions

**Symptom**: Tool claims "no changes" but 2px regression exists

**Root Cause**:
- Threshold set too high to avoid false positives
- 2px changes below detection threshold
- Calibration against wrong test cases

**Example**:
```
Expected: Detect 2px padding increase
Actual: Threshold 5% → 2px change = 0.08% (below threshold)
Result: Regression shipped to production
```

**Warning Signs**:
- User reports bugs tool should have caught
- Manual testing finds changes tool missed
- Threshold >1% for UI work

**Prevention Strategy**:

**Calibration Regression Suite**:
```python
# Test images with known subtle changes
regression_suite = [
    ("1px-padding-change.png", "Card padding +1px"),
    ("2px-padding-change.png", "Card padding +2px"),
    ("color-shift.png", "Button color #333 → #334"),
    ("font-size-change.png", "Font 14px → 14.5px"),
]

for image, expected in regression_suite:
    result = compare(image, baseline)
    assert result.detected, f"Failed to detect: {expected}"
```

**Multiple Thresholds**:
```python
def multi_threshold_diff(before, after):
    """Check at multiple thresholds"""
    thresholds = [0.01, 0.05, 0.1]  # 1%, 5%, 10%

    results = {}
    for threshold in thresholds:
        diff = pixel_diff(before, after, threshold=threshold)
        results[threshold] = diff

    return results
    # Returns: {0.01: 1247 changes, 0.05: 1 change, 0.1: 0 changes}
```

**Agentic Vision Confirmation**:
```python
# If pixel diff says "no changes" but user suspects regression
# Use agentic vision to double-check
if pixel_diff_result.change_count == 0 and user_reports_regression:
    agentic_result = gemini.analyze(before, after, "Find ANY subtle changes")
    assert agentic_result.found_changes, "Agentic vision confirmed no changes"
```

**Phase to Address**: Phase 2 (Comparison Engine) - Must calibrate before trusting results

**Recovery Plan**:
- If missing regressions: Lower threshold, re-run comparison
- If false positives increase: Add blur preprocessing
- If unsure: Run agentic vision confirmation

---

## Moderate Pitfalls (Annoying)

### 6. Dynamic Content Noise

**Symptom**: Timestamps, counters always flagged as changes

**Root Cause**: Tool doesn't understand semantic content

**Prevention**:
- **Traditional**: Manual ignore regions
- **Our Advantage**: Agentic vision understands "timestamp changed" is not regression
- Gemini semantic analysis: "Ignore dynamic content (timestamp, counter)"

---

### 7. Platform Rendering Differences

**Symptom**: Same UI looks different on macOS vs Windows

**Root Cause**: Font rendering, anti-aliasing, DPI differences

**Prevention**:
- Capture and compare on same platform
- Document platform in metadata
- Don't cross-platform compare without normalization

---

### 8. Large Context Failures

**Symptom**: API call fails with "context too long" error

**Root Cause**: Gemini API: >8K tokens throttled to 1% concurrency

**Prevention**:
- Resize images to <2048px before analysis
- Progressive resolution (start small)
- Split large images into tiles

---

### 9. Async Job Blocking

**Symptom**: MCP server blocks during Gemini API call, UI freezes

**Root Cause**: Sequential execution (z.ai 1-concurrent limit), no async

**Prevention**:
```python
# Wrong: Blocks
@app.tool("visual_compare")
async def visual_compare(before, after):
    result = await slow_gemini_call(before, after)  # Blocks
    return result

# Better: Background job
@app.tool("visual_compare")
async def visual_compare(before, after):
    job_id = spawn_background_job(compare_job, before, after)
    return {"status": "processing", "job_id": job_id}

@app.tool("visual_poll")
async def poll_result(job_id):
    return check_job_status(job_id)
```

---

### 10. Missing Dependencies

**Symptom**: "Module not found: mss", "opencv-python not installed"

**Root Cause**: Python environment issues

**Prevention**:
```bash
# Use uv for reliable dependency management
uv pip install mss opencv-python pillow google-generativeai

# Lock dependencies
uv pip freeze > requirements.txt

# Verify in CI
python -c "import mss, cv2, PIL, google.generativeai"
```

---

## Minor Pitfalls (Low Impact)

### 11. Screenshot Naming Collisions

**Symptom**: `03-phase-complete.png` overwrites previous

**Prevention**: Add timestamp to filename: `03-phase-complete-20250204-103000.png`

---

### 12. Metadata Corruption

**Symptom**: JSON metadata invalid, can't load screenshot

**Prevention**: Validate JSON before saving, backup metadata

---

## Phase Mapping

| Pitfall | Phase to Address | Priority |
|---------|------------------|----------|
| Free tier exhaustion | Phase 3 (Gemini Integration) | CRITICAL |
| MCP JSON-RPC breaks | Phase 1 (Foundation) | CRITICAL |
| Anti-aliasing false positives | Phase 2 (Comparison Engine) | CRITICAL |
| Storage bloat | Phase 4 (Operations) | HIGH |
| Missing subtle regressions | Phase 2 (Comparison Engine) | HIGH |
| Async job blocking | Phase 3 (Gemini Integration) | MEDIUM |
| Large context failures | Phase 3 (Gemini Integration) | MEDIUM |
| Dynamic content noise | Phase 3 (Agentic Vision) | LOW |

---

## Prevention Checklist

**Before Phase 1**:
- [ ] Configure stderr-only logging
- [ ] Set up exception handler
- [ ] Test MCP server doesn't pollute stdout

**Before Phase 2**:
- [ ] Implement 2px Gaussian blur preprocessing
- [ ] Create calibration regression suite
- [ ] Test threshold with 1px, 2px, 3px changes

**Before Phase 3**:
- [ ] Implement token bucket rate limiter
- [ ] Add aggressive caching
- [ ] Set up cost tracking
- [ ] Test with free tier limits

**Before Phase 4**:
- [ ] Implement automated cleanup (7-day retention)
- [ ] Configure Git LFS for baselines
- [ ] Add storage monitoring

---

## "Looks Done But Isn't" Verification

**Pre-Deployment Checklist**:
- [ ] Free tier: Ran 100 test comparisons, stayed within 15 req/min
- [ ] False positives: Tested anti-aliasing blur, <1% false positive rate
- [ ] Storage: 100 screenshots = <50MB, cleanup auto-deletes old
- [ ] MCP: Tools appear in Claude Code, no stdout pollution
- [ ] Accuracy: Detects 1px, 2px, 3px changes in regression suite
- [ ] Rate limiting: Token bucket prevents API exhaustion
- [ ] Recovery: Tested recovery from quota exceeded, disk full

---

*Last updated: 2025-02-04*
*Confidence: HIGH (critical pitfalls verified) / MEDIUM (moderate pitfalls)*
