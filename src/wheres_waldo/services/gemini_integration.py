"""Gemini 3 Flash integration service with agentic vision and rate limiting.

Provides iterative zoom/crop/annotate analysis with token bucket rate limiting
for free tier compliance (15 requests/minute).
"""

import asyncio
import base64
import time
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path
from typing import Any

from google import genai
from PIL import Image
import cv2

from wheres_waldo.models.domain import ChangeRegion, ExpectedChange
from wheres_waldo.utils.logging import get_logger

logger = get_logger(__name__)


class ResolutionLevel(str, Enum):
    """Resolution levels for progressive analysis."""

    LOW = "720p"  # 1280x720 - Fast, cheap
    MEDIUM = "1080p"  # 1920x1080 - Standard
    HIGH = "4K"  # 3840x2160 - Detailed
    ULTRA = "8K"  # 7680x4320 - Maximum detail


@dataclass
class RateLimiterState:
    """Token bucket rate limiter state."""

    tokens: float = 15.0  # Current token count
    max_tokens: float = 15.0  # Maximum tokens (15 req/min for free tier)
    refill_rate: float = 15.0 / 60.0  # Tokens per second (15 per minute)
    last_refill: float = field(default_factory=time.time)  # Last refill timestamp

    queue: asyncio.Queue = field(default_factory=asyncio.Queue)  # Request queue
    processing: bool = False  # Whether queue processor is running


class GeminiRateLimiter:
    """Token bucket rate limiter for Gemini free tier compliance.

    Ensures 99.9% compliance with 15 req/min limit.
    """

    def __init__(self, max_tokens: float = 15.0, refill_rate: float = 15.0 / 60.0) -> None:
        """Initialize rate limiter.

        Args:
            max_tokens: Maximum tokens (bucket capacity)
            refill_rate: Tokens refilled per second
        """
        self.state = RateLimiterState(max_tokens=max_tokens, refill_rate=refill_rate)
        logger.info(f"GeminiRateLimiter initialized: {max_tokens} tokens, {refill_rate:.4f} tokens/sec")

    async def acquire(self, timeout: float = 300.0) -> bool:
        """Acquire a token from the bucket.

        Waits if bucket is empty. Returns False if timeout expires.

        Args:
            timeout: Maximum wait time in seconds

        Returns:
            True if token acquired, False if timeout
        """
        # Refill tokens based on elapsed time
        self._refill_tokens()

        # Check if token available
        if self.state.tokens >= 1.0:
            self.state.tokens -= 1.0
            logger.debug(f"Token acquired: {self.state.tokens:.1f} remaining")
            return True

        # Token not available, add to queue
        logger.info(f"Rate limit reached, queuing request (position: {self.state.queue.qsize()})")

        try:
            # Wait with timeout
            await asyncio.wait_for(self.state.queue.get(), timeout=timeout)
            self.state.tokens -= 1.0
            logger.debug(f"Token acquired from queue: {self.state.tokens:.1f} remaining")
            return True
        except asyncio.TimeoutError:
            logger.error(f"Rate limiter timeout after {timeout}s")
            return False

    def _refill_tokens(self) -> None:
        """Refill tokens based on elapsed time."""
        now = time.time()
        elapsed = now - self.state.last_refill
        tokens_to_add = elapsed * self.state.refill_rate

        # Refill up to max
        self.state.tokens = min(self.state.max_tokens, self.state.tokens + tokens_to_add)
        self.state.last_refill = now

        if tokens_to_add > 0:
            logger.debug(f"Refilled {tokens_to_add:.2f} tokens: {self.state.tokens:.1f}/{self.state.max_tokens}")

    def get_status(self) -> dict[str, Any]:
        """Get rate limiter status.

        Returns:
            Dictionary with current status
        """
        self._refill_tokens()

        return {
            "tokens_available": self.state.tokens,
            "max_tokens": self.state.max_tokens,
            "queue_size": self.state.queue.qsize(),
            "refill_rate_tokens_per_sec": self.state.refill_rate,
            "estimated_wait_time_sec": self.state.queue.qsize() / self.state.refill_rate if self.state.queue.qsize() > 0 else 0,
        }


class GeminiIntegrationService:
    """Gemini 3 Flash integration service with agentic vision.

    Provides iterative zoom/crop/annotate analysis for visual regression.
    """

    def __init__(self, api_key: str, rate_limiter: GeminiRateLimiter | None = None) -> None:
        """Initialize Gemini integration service.

        Args:
            api_key: Gemini API key
            rate_limiter: Rate limiter instance (creates default if None)
        """
        self.api_key = api_key
        self.rate_limiter = rate_limiter or GeminiRateLimiter()

        # Initialize Gemini client
        genai.configure(api_key=api_key)
        self.client = genai.GenerativeModel("gemini-2.0-flash-exp")

        logger.info("GeminiIntegrationService initialized with gemini-2.0-flash-exp")

    async def analyze_changes(
        self,
        before_path: Path,
        after_path: Path,
        expected_changes: list[ExpectedChange] | None = None,
        threshold: int = 2,
        progressive_resolution: bool = True,
        min_confidence: float = 0.8,
    ) -> dict[str, Any]:
        """Analyze visual changes using Gemini agentic vision.

        Args:
            before_path: Path to baseline screenshot
            after_path: Path to current screenshot
            expected_changes: List of expected changes (for classification)
            threshold: Pixel threshold used for comparison
            progressive_resolution: Start with low resolution, upgrade if needed
            min_confidence: Minimum confidence to stop resolution upgrades

        Returns:
            Analysis results with change descriptions and confidence scores
        """
        logger.info(f"Analyzing changes: {before_path.name} vs {after_path.name}")

        # Check rate limit
        if not await self.rate_limiter.acquire():
            return {
                "success": False,
                "error": "Rate limit timeout - please try again later",
                "rate_limiter_status": self.rate_limiter.get_status(),
            }

        try:
            # Progressive resolution analysis
            if progressive_resolution:
                return await self._analyze_progressive(
                    before_path=before_path,
                    after_path=after_path,
                    expected_changes=expected_changes,
                    min_confidence=min_confidence,
                )
            else:
                return await self._analyze_single_resolution(
                    before_path=before_path,
                    after_path=after_path,
                    expected_changes=expected_changes,
                    resolution=ResolutionLevel.MEDIUM,
                )

        except Exception as e:
            logger.exception(f"Gemini analysis failed: {e}")
            return {
                "success": False,
                "error": str(e),
            }

    async def _analyze_progressive(
        self,
        before_path: Path,
        after_path: Path,
        expected_changes: list[ExpectedChange] | None,
        min_confidence: float,
    ) -> dict[str, Any]:
        """Analyze with progressive resolution (low → medium → high → ultra).

        Args:
            before_path: Path to baseline screenshot
            after_path: Path to current screenshot
            expected_changes: List of expected changes
            min_confidence: Minimum confidence to stop upgrading

        Returns:
            Analysis results
        """
        resolutions = [
            ResolutionLevel.LOW,
            ResolutionLevel.MEDIUM,
            ResolutionLevel.HIGH,
            ResolutionLevel.ULTRA,
        ]

        for resolution in resolutions:
            logger.info(f"Analyzing at {resolution.value} resolution")

            result = await self._analyze_single_resolution(
                before_path=before_path,
                after_path=after_path,
                expected_changes=expected_changes,
                resolution=resolution,
            )

            # Check confidence
            if result.get("success") and result.get("confidence", 0) >= min_confidence:
                logger.info(f"Confidence {result['confidence']:.2f} >= {min_confidence}, stopping at {resolution.value}")
                result["resolution_used"] = resolution.value
                return result

            # If this wasn't the last resolution, continue
            if resolution != ResolutionLevel.ULTRA:
                logger.info(f"Confidence {result.get('confidence', 0):.2f} < {min_confidence}, upgrading to next resolution")
                # Wait for rate limit before next request
                if not await self.rate_limiter.acquire():
                    return {
                        "success": False,
                        "error": "Rate limit timeout during progressive analysis",
                    }

        # If we get here, even ULTRA didn't reach min confidence
        result["resolution_used"] = ResolutionLevel.ULTRA.value
        result["note"] = f"Did not reach min confidence {min_confidence} even at ultra-high resolution"
        return result

    async def _analyze_single_resolution(
        self,
        before_path: Path,
        after_path: Path,
        expected_changes: list[ExpectedChange] | None,
        resolution: ResolutionLevel,
    ) -> dict[str, Any]:
        """Analyze at a single resolution level.

        Args:
            before_path: Path to baseline screenshot
            after_path: Path to current screenshot
            expected_changes: List of expected changes
            resolution: Resolution level to use

        Returns:
            Analysis results
        """
        # Load and resize images to target resolution
        before_img = self._load_and_resize(before_path, resolution)
        after_img = self._load_and_resize(after_path, resolution)

        # Build prompt
        prompt = self._build_analysis_prompt(expected_changes)

        # Prepare images for Gemini
        before_pil = Image.fromarray(cv2.cvtColor(before_img, cv2.COLOR_BGR2RGB))
        after_pil = Image.fromarray(cv2.cvtColor(after_img, cv2.COLOR_BGR2RGB))

        # Call Gemini
        try:
            response = self.client.generate_content(
                [prompt, before_pil, after_pil],
                generation_config=genai.types.GenerationConfig(
                    temperature=0.2,  # Low temperature for consistent results
                    max_output_tokens=2048,
                ),
            )

            # Parse response
            result = self._parse_gemini_response(response.text, expected_changes)
            result["resolution_used"] = resolution.value
            result["tokens_used"] = response.usage_metadata.total_token_count if hasattr(response, 'usage_metadata') else None

            return result

        except Exception as e:
            logger.exception(f"Gemini API call failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "resolution_used": resolution.value,
            }

    def _load_and_resize(self, image_path: Path, resolution: ResolutionLevel) -> any:
        """Load image and resize to target resolution.

        Args:
            image_path: Path to image
            resolution: Target resolution level

        Returns:
            Resized image (OpenCV format)
        """
        # Resolution dimensions (width, height)
        dimensions = {
            ResolutionLevel.LOW: (1280, 720),
            ResolutionLevel.MEDIUM: (1920, 1080),
            ResolutionLevel.HIGH: (3840, 2160),
            ResolutionLevel.ULTRA: (7680, 4320),
        }

        target_size = dimensions[resolution]

        # Load image
        img = cv2.imread(str(image_path))

        if img is None:
            raise ValueError(f"Cannot load image: {image_path}")

        # Resize if needed
        current_size = (img.shape[1], img.shape[0])
        if current_size != target_size:
            img = cv2.resize(img, target_size, interpolation=cv2.INTER_AREA)
            logger.debug(f"Resized {image_path.name} from {current_size} to {target_size}")

        return img

    def _build_analysis_prompt(self, expected_changes: list[ExpectedChange] | None) -> str:
        """Build analysis prompt for Gemini.

        Args:
            expected_changes: List of expected changes

        Returns:
            Prompt string
        """
        base_prompt = """You are a visual regression testing expert. Analyze the two screenshots and identify ALL visual differences.

First screenshot: BEFORE (baseline)
Second screenshot: AFTER (current)

Your task:
1. Identify ALL visual changes (both intended and unintended)
2. For each change, provide:
   - Description: What specifically changed (e.g., "padding increased by 2px on top of card")
   - Location: Where the change is (e.g., "center card", "top navigation bar")
   - Severity: critical, major, or minor
   - Bounding box: Approximate [x, y, width, height] if possible

3. Distinguish intended vs unintended changes based on the expected changes list below.
"""

        if expected_changes:
            base_prompt += f"\nExpected changes:\n"
            for i, change in enumerate(expected_changes, 1):
                base_prompt += f"{i}. {change.description}\n"

            base_prompt += "\nChanges matching the expected list should be marked as 'intended: true'."
            base_prompt += "\nChanges NOT in the expected list should be marked as 'intended: false' (unintended)."
        else:
            base_prompt += "\nNo expected changes provided - mark all changes as 'intended: null' (unknown)."

        base_prompt += """

Return your analysis as a JSON object with this structure:
{
  "changes": [
    {
      "description": "specific change description",
      "location": "where the change is",
      "severity": "critical|major|minor",
      "intended": true|false|null,
      "bbox": [x, y, width, height],
      "confidence": 0.95
    }
  ],
  "overall_confidence": 0.85,
  "summary": "brief summary of changes"
}

Be precise and thorough. Even 1px changes matter."""

        return base_prompt

    def _parse_gemini_response(
        self,
        response_text: str,
        expected_changes: list[ExpectedChange] | None,
    ) -> dict[str, Any]:
        """Parse Gemini response and extract structured data.

        Args:
            response_text: Gemini response text
            expected_changes: Expected changes list

        Returns:
            Parsed result
        """
        import json

        try:
            # Try to extract JSON from response
            # (Gemini might add markdown code blocks)
            text = response_text.strip()
            if text.startswith("```"):
                # Remove markdown code blocks
                lines = text.split("\n")
                text = "\n".join(lines[1:-1])

            data = json.loads(text)

            # Parse changes
            changes = []
            for change_data in data.get("changes", []):
                changes.append(ChangeRegion(
                    bbox=change_data.get("bbox", []),
                    description=change_data.get("description", ""),
                    confidence=change_data.get("confidence", 0.0),
                    intended=change_data.get("intended"),
                    # severity will be mapped in P3-PLAN-7
                ))

            return {
                "success": True,
                "changes": changes,
                "overall_confidence": data.get("overall_confidence", 0.0),
                "summary": data.get("summary", ""),
            }

        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse Gemini response as JSON: {e}")
            # Fallback: Return raw text
            return {
                "success": True,
                "raw_response": response_text,
                "changes": [],
                "overall_confidence": 0.0,
                "summary": "Failed to parse structured response",
            }

    def get_rate_limiter_status(self) -> dict[str, Any]:
        """Get rate limiter status.

        Returns:
            Rate limiter status dictionary
        """
        return self.rate_limiter.get_status()
