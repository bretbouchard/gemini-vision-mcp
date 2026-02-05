# Architecture Research - MCP Server with Vision Capabilities

## Executive Summary

**Architecture Pattern**: Tool as Orchestrator - MCP tools delegate to service layer for testability and separation of concerns.

**Key Innovation**: Multi-platform adapter pattern for screenshot capture + rate-limited Gemini integration + filesystem storage with JSON index.

**Build Order**: Foundation → Capture → Comparison → Operations (prevents external API dependencies early)

---

## System Architecture

### High-Level Components

```
┌─────────────────────────────────────────────────────────────┐
│                     Claude Code                              │
│                  (MCP Client)                                 │
└──────────────────────┬────────────────────────────────────────┘
                       │ JSON-RPC
                       ▼
┌─────────────────────────────────────────────────────────────┐
│                  MCP Server                                  │
│  ┌───────────────────────────────────────────────────────┐  │
│  │  Tool Layer (Thin Wrappers)                           │  │
│  │  - visual_capture()                                   │  │
│  │  - visual_compare()                                   │  │
│  │  - visual_prepare()                                   │  │
│  │  - visual_cleanup()                                   │  │
│  └──────────────────────┬────────────────────────────────┘  │
│                         │                                   │
│  ┌──────────────────────▼────────────────────────────────┐  │
│  │  Service Layer (Business Logic)                      │  │
│  │  ┌──────────────┐  ┌──────────────┐  ┌────────────┐ │  │
│  │  │ Capture      │  │ Compare      │  │ Storage     │ │  │
│  │  │ Service      │  │ Service      │  │ Service     │ │  │
│  │  └──────────────┘  └──────────────┘  └────────────┘ │  │
│  └──────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
                         │
      ┌──────────────────┼──────────────────┐
      │                  │                  │
      ▼                  ▼                  ▼
┌───────────┐    ┌──────────────┐    ┌──────────┐
│ Platform  │    │ Gemini       │    │ Local    │
│ Adapters  │    │ Agentic      │    │ Storage  │
│           │    │ Vision API   │    │          │
│ - macOS   │    │              │    │ Filesyst. │
│ - iOS     │    │ Rate Limited │    │ + JSON   │
│ - Web     │    │              │    │          │
└───────────┘    └──────────────┘    └──────────┘
```

---

## Component Boundaries

### 1. Tool Layer (MCP Protocol)

**Responsibility**: Expose functionality via MCP protocol, handle JSON-RPC

**Components**:
- `visual_capture(name, description)` - Capture and store screenshot
- `visual_compare(before, after, expected_changes)` - Compare with agentic vision
- `visual_prepare(expected_changes_list)` - Declare expected changes
- `visual_cleanup(phase_to_remove)` - Remove old screenshots

**Characteristics**:
- Thin wrappers (minimal logic)
- Argument validation
- Error handling (MCP protocol errors)
- Delegate to service layer

**Output**: MCP Tool definitions, JSON-RPC handlers

---

### 2. Service Layer (Business Logic)

#### 2.1 Capture Service

**Responsibility**: Screenshot capture across platforms

**Interface**:
```python
class CaptureService:
    def capture(name: str, description: str = "") -> Screenshot
    def get_screenshot(path: str) -> Screenshot
    def list_screenshots() -> List[Screenshot]
```

**Platform Adapters**:
```python
class CaptureAdapter(ABC):
    @abstractmethod
    def capture(self) -> Image: ...

class MacOSCocoaAdapter(CaptureAdapter):
    """Use MSS for macOS"""
    def capture(self) -> Image:
        with mss.mss() as sct:
            monitor = sct.monitors[1]
            screenshot = sct.grab(monitor)
            return Image.frombytes('RGB', screenshot.size, screenshot.rgb)

class IOSSimulatorAdapter(CaptureAdapter):
    """Use simctl for iOS simulators"""
    def capture(self) -> Image:
        subprocess.run([
            'xcrun', 'simctl', 'io', 'booted', 'screenshot',
            f'{self.temp_path}.png'
        ])
        return Image.open(f'{self.temp_path}.png')

class WebChromeAdapter(CaptureAdapter):
    """Use chrome-devtools MCP for web"""
    def capture(self) -> Image:
        # Call chrome-devtools MCP take_screenshot tool
        # Download and return image
        ...
```

**Orchestration**:
```python
class CaptureOrchestrator:
    def __init__(self):
        self.adapters = [
            MacOSCocoaAdapter(),
            IOSSimulatorAdapter(),
            WebChromeAdapter(),
        ]

    def auto_detect_and_capture(self) -> Screenshot:
        for adapter in self.adapters:
            if adapter.is_available():
                return adapter.capture()
        raise CaptureError("No capture adapter available")
```

---

#### 2.2 Compare Service

**Responsibility**: Image comparison with agentic vision analysis

**Interface**:
```python
class CompareService:
    def compare(
        self,
        before: Screenshot,
        after: Screenshot,
        expected_changes: List[str] = None
    ) -> ComparisonResult

    def pixel_diff(before: Image, after: Image) -> DiffResult
    def agentic_analysis(
        before: Image,
        after: Image,
        diff: DiffResult
    ) -> AgenticResult
```

**Pipeline**:
```python
class CompareService:
    def __init__(self, gemini_client, storage):
        self.gemini = gemini_client
        self.storage = storage

    def compare(self, before_path, after_path, expected_changes):
        # 1. Load images
        before = Image.open(before_path)
        after = Image.open(after_path)

        # 2. Pixel diff (fast, local)
        diff_result = self.pixel_diff(before, after)

        # 3. Agentic vision analysis (slow, API)
        agentic_result = self.agentic_analysis(
            before, after, diff_result
        )

        # 4. Validate against expectations
        validation = self.validate_expectations(
            expected_changes, agentic_result
        )

        # 5. Generate annotated output
        annotated = self.generate_annotated(
            after, diff_result, agentic_result
        )

        return ComparisonResult(
            pixel_diff=diff_result,
            agentic_analysis=agentic_result,
            validation=validation,
            annotated_screenshot=annotated
        )

    def pixel_diff(self, before, after):
        # OpenCV diffing with 2px Gaussian blur
        # Returns: bounding boxes, change count, heatmap
        ...

    def agentic_analysis(self, before, after, diff_result):
        # Gemini 3 Flash iterative analysis
        # Returns: text description, found regions, annotations
        ...
```

**Gemini Integration**:
```python
class GeminiClient:
    def __init__(self, api_key, rate_limiter):
        self.model = genai.GenerativeModel('gemini-3-flash-preview')
        self.rate_limiter = rate_limiter  # Token bucket (15 req/min)

    async def analyze_with_agentic_vision(
        self,
        before: Image,
        after: Image,
        query: str
    ) -> str:
        # Rate limiting
        await self.rate_limiter.acquire()

        # Low-res pass (cheaper)
        response_low = await self.model.generate_content([
            query,
            resize_image(before, 512),
            resize_image(after, 512),
            "What changed? Be specific."
        ])

        # Medium-res if needed (more expensive)
        if "zoom" in response_low.text.lower():
            response_med = await self.model.generate_content([
                query,
                resize_image(after, 1024),
                "Deeper analysis of changed regions"
            ])
            return response_med.text

        return response_low.text
```

---

#### 2.3 Storage Service

**Responsibility**: Filesystem storage with JSON index

**Schema**:
```
.screenshots/
├── phases/
│   ├── 01-before-card-update.png
│   ├── 01-before-card-update.json  # Metadata
│   ├── 02-after-card-update.png
│   ├── 02-after-card-update.json
│   └── .index.json  # Global index
└── comparisons/
    ├── 01-vs-02-diff.png
    ├── 01-vs-02-diff.json
    └── 01-vs-02-annotation.png
```

**Metadata Format**:
```json
{
  "name": "01-before-card-update",
  "timestamp": "2025-02-04T10:30:00Z",
  "description": "Baseline before card layout update",
  "phase": 3,
  "platform": "macos",
  "dimensions": {"width": 1920, "height": 1080},
  "file_size": 2048576,
  "hash": "sha256:abc123..."
}
```

**Interface**:
```python
class StorageService:
    def save_screenshot(self, image: Image, metadata: dict) -> str
    def load_screenshot(self, path: str) -> Screenshot
    def list_screenshots(self, phase: int = None) -> List[Screenshot]
    def delete_screenshot(self, path: str)
    def cleanup_old_screenshots(self, keep_last_n: int = 3)
```

**Cleanup Policy**:
```python
class StorageService:
    def cleanup_old_screenshots(self, keep_last_n=3):
        """Delete all screenshots except last N phases"""
        screenshots = self.list_screenshots()
        sorted_by_phase = sorted(screenshots, key=lambda s: s.phase)

        to_delete = sorted_by_phase[:-keep_last_n]
        for screenshot in to_delete:
            self.delete_screenshot(screenshot.path)
            self.update_index(remove=screenshot)
```

---

## Data Flow

### Screenshot Capture Flow

```
User/AI Agent
    │
    │ "Capture screenshot"
    ▼
MCP Tool: visual_capture()
    │
    │ Delegate to service
    ▼
CaptureOrchestrator
    │
    │ Auto-detect platform
    ├─→ macOS available?
    │   └─→ MacOSCocoaAdapter.capture()
    ├─→ iOS simulator running?
    │   └─→ IOSSimulatorAdapter.capture()
    └─→ Chrome devtools available?
        └─→ WebChromeAdapter.capture()
    │
    │ Returns: Screenshot object
    ▼
StorageService.save_screenshot()
    │
    ├─→ Save PNG to .screenshots/phases/
    ├─→ Write metadata JSON
    └─→ Update .index.json
    │
    ▼
Return: Path to saved screenshot
```

---

### Comparison Flow

```
User/AI Agent
    │
    │ "Compare these screenshots"
    ▼
MCP Tool: visual_compare(before, after, expected)
    │
    │ Delegate to service
    ▼
CompareService.compare()
    │
    ├─→ Load both images
    ├─→ Pixel diff (OpenCV, local)
    │   └─→ Returns: bounding boxes, heatmap
    │
    ├─→ Agentic vision (Gemini API)
    │   └─→ GeminiClient.analyze_with_agentic_vision()
    │       ├─→ Rate limiter (token bucket)
    │       ├─→ Low-res pass (cheap)
    │       ├─→ Medium-res if needed (expensive)
    │       └─→ Returns: text analysis, annotations
    │
    ├─→ Validate expectations
    │   └─→ Compare found changes vs expected_changes
    │       └─→ Mark ✅ expected, ⚠️ unexpected
    │
    └─→ Generate annotated output
        └─→ Draw bounding boxes, labels on screenshot
            └─→ Save to .screenshots/comparisons/
    │
    ▼
Return: ComparisonResult
    - annotated_screenshot.png
    - pixel_diff_summary
    - agentic_analysis_text
    - validation_report (✅ expected, ⚠️ regressions)
```

---

## MCP Tool Contracts

### Tool: visual_capture

**Input Schema**:
```typescript
{
  name: "visual_capture",
  description: "Capture screenshot and store with metadata",
  inputSchema: {
    type: "object",
    properties: {
      name: {
        type: "string",
        description: "Screenshot name (e.g., '03-phase-complete')"
      },
      description: {
        type: "string",
        description: "Optional description of what this screenshot captures",
        default: ""
      }
    },
    required: ["name"]
  }
}
```

**Output**:
```typescript
{
  success: true,
  data: {
    path: ".screenshots/phases/03-phase-complete.png",
    timestamp: "2025-02-04T10:30:00Z",
    phase: 3,
    dimensions: { width: 1920, height: 1080 }
  }
}
```

---

### Tool: visual_compare

**Input Schema**:
```typescript
{
  name: "visual_compare",
  description: "Compare two screenshots with agentic vision analysis",
  inputSchema: {
    type: "object",
    properties: {
      before: {
        type: "string",
        description: "Path to baseline screenshot"
      },
      after: {
        type: "string",
        description: "Path to current screenshot"
      },
      expected_changes: {
        type: "array",
        items: { type: "string" },
        description: "List of expected changes (e.g., ['Card padding +2px'])",
        default: []
      }
    },
    required: ["before", "after"]
  }
}
```

**Output**:
```typescript
{
  success: true,
  data: {
    annotated_screenshot: ".screenshots/comparisons/01-vs-02-annotation.png",
    pixel_diff: {
      total_changes: 47,
      changed_pixels: 1234,
      diff_percentage: 0.08
    },
    agentic_analysis: {
      summary: "Card padding increased by 2px top/bottom. Button shifted 20px right.",
      found_changes: [
        { "region": "card", "change": "+2px padding" },
        { "region": "button", "change": "moved 20px right" }
      ],
      unexpected_changes: [
        { "region": "title", "change": "shifted 5px down", "severity": "warning" }
      ]
    },
    validation: {
      expected_matched: ["Card padding +2px", "Button moved 20px right"],
      expected_missed: [],
      unexpected_found: ["Title shifted 5px down"],
      regressions: true
    }
  }
}
```

---

## Error Handling Strategies

### 1. Rate Limit Errors (Gemini API)

**Detection**: HTTP 429, timeout after 30s

**Strategy**: Token bucket rate limiter + exponential backoff retry

```python
class TokenBucketRateLimiter:
    def __init__(self, rate=15, per=60):
        self.rate = rate  # 15 requests
        self.per = per    # per 60 seconds
        self.allowance = rate
        self.last_check = time.time()

    async def acquire(self):
        with threading.Lock():
            current = time.time()
            time_passed = current - self.last_check
            self.last_check = current

            self.allowance += time_passed * (self.rate / self.per)

            if self.allowance > self.rate:
                self.allowance = self.rate

            if self.allowance < 1:
                sleep_time = (self.per - self.allowance) / self.rate
                await asyncio.sleep(sleep_time)
                self.allowance = 0
            else:
                self.allowance -= 1
```

**Retry Logic**:
```python
async def call_gemini_with_retry(self, prompt, image):
    for attempt in range(3):
        try:
            return await self.model.generate_content([prompt, image])
        except RateLimitError:
            if attempt == 2:
                raise
            await asyncio.sleep(2 ** attempt)  # 1s, 2s, 4s
```

---

### 2. Capture Failures

**Detection**: Platform adapter unavailable, screenshot fails

**Strategy**: Fallback chain + clear error messages

```python
class CaptureOrchestrator:
    def auto_detect_and_capture(self):
        for adapter in self.adapters:
            try:
                if adapter.is_available():
                    return adapter.capture()
            except CaptureError as e:
                logger.warning(f"{adapter} failed: {e}")
                continue

        raise CaptureError(
            "No capture method available. Tried: "
            f"{[a.__class__.__name__ for a in self.adapters]}"
        )
```

---

### 3. Storage Errors

**Detection**: Disk full, permissions, corrupted files

**Strategy**: Validate before write, clean up on error

```python
class StorageService:
    def save_screenshot(self, image, metadata):
        # Validate disk space
        if not self.has_disk_space(image.size):
            raise StorageError("Insufficient disk space")

        # Validate permissions
        if not self.can_write_to_directory():
            raise StorageError("No write permissions")

        try:
            path = self.write_image(image)
            self.write_metadata(path, metadata)
            self.update_index(metadata)
        except Exception as e:
            # Rollback: remove partial files
            self.cleanup_partial_write(path)
            raise StorageError(f"Failed to save: {e}")
```

---

## Build Order

### Phase 1: Foundation

**Components**:
- Storage service (filesystem + JSON index)
- Type definitions (Screenshot, ComparisonResult, etc.)
- Utilities (image I/O, hashing)

**Why First**: No external dependencies, pure Python, testable in isolation

**Deliverable**: Can save/load screenshots with metadata

---

### Phase 2: Capture

**Components**:
- Capture orchestrator
- Platform adapters (macOS, iOS, Web)
- Capture service

**Why Second**: Depends on storage, no external APIs

**Deliverable**: Can capture screenshots from all platforms

**Risk**: Platform tool availability needs verification

---

### Phase 3: Comparison (HIGH RISK)

**Components**:
- Pixel diffing (OpenCV)
- Gemini client (rate-limited)
- Agentic vision workflow
- Compare service

**Why Third**: Most complex, external API dependency

**Deliverable**: Full comparison with agentic vision

**Risk**: HIGH - Gemini API capabilities need phase-specific research

---

### Phase 4: Operations

**Components**:
- Cleanup policies
- MCP tool exposure
- Query operations (list, find)

**Why Fourth**: Builds on all previous components

**Deliverable**: Complete MCP server with all tools

---

## Phase-Specific Research Flags

### Phase 2: Platform Capture

**Verify**: axe CLI availability for macOS
**Research**: iOS simctl screenshot capabilities
**Test**: chrome-devtools MCP integration

---

### Phase 3: Gemini Integration (HIGH PRIORITY)

**Test**: Actual Gemini API for iterative zoom/crop/annotate
**Measure**: Token usage for typical comparison
**Verify**: Code execution works in free tier
**Calibrate**: Blur strength for 2px detection

---

## Open Questions

### MCP Server Stability

**Question**: Can MCP server handle async operations without blocking?

**Research Needed**: Test MCP Python SDK with async tool execution

**Impact**: If not, need background job processing

---

### Screenshot Quality

**Question**: What resolution/format for optimal comparison?

**Research Needed**: Test PNG vs JPEG, resolution vs API cost

**Impact**: Affects storage, API costs, accuracy

---

### Annotated Output Format

**Question**: How to present annotated results to users?

**Options**:
- Overlay on screenshot
- Side-by-side comparison
- Separate HTML report
- JSON with bounding box coordinates

**Research Needed**: User testing with actual workflows

---

*Last updated: 2025-02-04*
*Confidence: HIGH (MCP architecture) / MEDIUM (Gemini integration) / LOW (iOS capture)*
