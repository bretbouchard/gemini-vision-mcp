"""Baseline management service.

Handles baseline declaration, expected changes parsing, and baseline storage.
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Any

from pydantic import ValidationError

from wheres_waldo.models.domain import (
    Baseline,
    ExpectedChange,
    Screenshot,
    Platform,
    Quality,
    ImageFormat,
)
from wheres_waldo.services.capture import CaptureService
from wheres_waldo.services.storage import StorageService
from wheres_waldo.utils.helpers import generate_screenshot_name
from wheres_waldo.utils.logging import get_logger

logger = get_logger(__name__)


class BaselineService:
    """Baseline management service.

    Manages baseline declaration with expected changes and baseline storage.
    """

    def __init__(
        self,
        capture_service: CaptureService | None = None,
        storage_service: StorageService | None = None,
    ) -> None:
        """Initialize baseline service.

        Args:
            capture_service: Screenshot capture service (creates if None)
            storage_service: Storage service (creates if None)
        """
        self.capture_service = capture_service or CaptureService()
        self.storage_service = storage_service or StorageService()

    def create_baseline(
        self,
        phase: str,
        expected_changes_input: str,
        platform: Platform = Platform.AUTO,
        quality: Quality = Quality.X2,
        format: ImageFormat = ImageFormat.PNG,
        description: str | None = None,
    ) -> Baseline:
        """Create a new baseline with expected changes.

        Args:
            phase: Phase name or identifier
            expected_changes_input: Expected changes (natural language or JSON)
            platform: Platform to capture from
            quality: Screenshot quality
            format: Screenshot format
            description: Optional free-text description

        Returns:
            Created baseline

        Raises:
            ValueError: If expected changes are invalid
        """
        # Generate baseline ID
        timestamp = datetime.now()
        baseline_id = timestamp.strftime("%Y%m%d-%H%M%S") + "-" + phase.lower().replace(" ", "-")

        # Parse expected changes
        expected_changes = self._parse_expected_changes(expected_changes_input)

        # Capture baseline screenshot
        screenshot_name = f"baseline-{phase}"
        try:
            screenshot = self.capture_service.capture(
                name=screenshot_name,
                platform=platform,
                quality=quality,
                format=format,
            )
            logger.info(f"Captured baseline screenshot: {screenshot.path}")
        except Exception as e:
            logger.error(f"Failed to capture baseline screenshot: {e}")
            raise ValueError(f"Could not capture baseline screenshot: {e}")

        # Create baseline object
        baseline = Baseline(
            baseline_id=baseline_id,
            screenshot=screenshot,
            phase=phase,
            expected_changes=expected_changes,
            description=description or expected_changes_input,
            created_at=timestamp,
        )

        # Save baseline
        self.storage_service.save_baseline(baseline)

        logger.info(f"Created baseline: {baseline_id} with {len(expected_changes)} expected changes")
        return baseline

    def _parse_expected_changes(self, input_str: str) -> list[ExpectedChange]:
        """Parse expected changes from natural language or JSON.

        Args:
            input_str: Input string (natural language or JSON)

        Returns:
            List of expected changes

        Raises:
            ValueError: If parsing fails
        """
        input_str = input_str.strip()

        # Try JSON first
        if input_str.startswith("{") or input_str.startswith("["):
            try:
                data = json.loads(input_str)

                # Handle both single object and array
                if isinstance(data, list):
                    items = data
                else:
                    items = [data]

                changes = []
                for item in items:
                    # Extract fields
                    description = item.get("description", "")
                    bbox = item.get("bbox")
                    element = item.get("element")

                    if not description:
                        logger.warning("Expected change missing description, skipping")
                        continue

                    changes.append(ExpectedChange(
                        description=description,
                        bbox=bbox,
                        element=element,
                    ))

                logger.info(f"Parsed {len(changes)} expected changes from JSON")
                return changes

            except json.JSONDecodeError as e:
                logger.warning(f"JSON parsing failed, trying natural language: {e}")

        # Natural language parsing
        # Split by common delimiters (commas, newlines, "and")
        import re

        # Normalize delimiters to newlines
        normalized = re.sub(r",\s*(?:and\s+)?", "\n", input_str)
        normalized = re.sub(r"\.\s+", "\n", normalized)

        # Split into lines
        lines = [line.strip() for line in normalized.split("\n") if line.strip()]

        changes = []
        for line in lines:
            # Skip empty lines
            if not line:
                continue

            # Create expected change from natural language
            changes.append(ExpectedChange(
                description=line,
                bbox=None,  # Will be populated by Gemini later
                element=None,  # Will be populated by Gemini later
            ))

        logger.info(f"Parsed {len(changes)} expected changes from natural language")
        return changes

    def get_baseline(self, baseline_id: str) -> Baseline | None:
        """Get baseline by ID.

        Args:
            baseline_id: Baseline identifier

        Returns:
            Baseline if found, None otherwise
        """
        return self.storage_service.get_baseline(baseline_id)

    def list_baselines(self, phase: str | None = None) -> list[Baseline]:
        """List all baselines, optionally filtered by phase.

        Args:
            phase: Optional phase name to filter by

        Returns:
            List of baselines
        """
        return self.storage_service.list_baselines(phase=phase)

    def compare_against_baseline(
        self,
        baseline_id: str,
        current_screenshot_path: Path,
        threshold: int = 2,
    ) -> dict[str, Any]:
        """Compare current screenshot against baseline.

        This is a placeholder - actual comparison will be implemented in Phase 3.

        Args:
            baseline_id: Baseline identifier
            current_screenshot_path: Path to current screenshot
            threshold: Pixel threshold for comparison

        Returns:
            Comparison result placeholder
        """
        baseline = self.get_baseline(baseline_id)
        if not baseline:
            raise ValueError(f"Baseline not found: {baseline_id}")

        # Placeholder - Phase 3 will implement actual comparison
        return {
            "baseline_id": baseline_id,
            "baseline_path": str(baseline.screenshot.path),
            "current_path": str(current_screenshot_path),
            "threshold": threshold,
            "expected_changes_count": len(baseline.expected_changes),
            "status": "comparison_not_implemented",
            "message": "Comparison will be implemented in Phase 3",
        }
