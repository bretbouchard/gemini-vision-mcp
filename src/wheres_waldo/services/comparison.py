"""Screenshot comparison service with OpenCV pixel diffing.

Provides pixel-level comparison with anti-aliasing noise reduction
and heatmap visualization.
"""

import time
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Literal

import cv2
import numpy as np
from PIL import Image

from wheres_waldo.models.domain import ComparisonResult, ComparisonConfig, ChangeRegion, Severity
from wheres_waldo.utils.helpers import format_resolution, get_image_resolution
from wheres_waldo.utils.logging import get_logger

logger = get_logger(__name__)


class HeatmapColorScheme(str, Enum):
    """Color schemes for heatmap visualization."""

    YELLOW_ORANGE_RED = "yellow_orange_red"  # Subtle → Moderate → Dramatic
    BLUE_CYAN_GREEN = "blue_cyan_green"  # Alternative scheme
    GRAYSCALE = "grayscale"  # Black and white


class ComparisonService:
    """Screenshot comparison service using OpenCV."""

    def __init__(self, config: ComparisonConfig | None = None) -> None:
        """Initialize comparison service.

        Args:
            config: Comparison configuration (uses defaults if not provided)
        """
        self.config = config or ComparisonConfig()
        logger.info(f"ComparisonService initialized with threshold={self.config.pixel_threshold}px")

    def compare(
        self,
        before_path: Path,
        after_path: Path,
        threshold: int | None = None,
    ) -> ComparisonResult:
        """Compare two screenshots with pixel-level precision.

        Args:
            before_path: Path to baseline screenshot
            after_path: Path to current screenshot
            threshold: Pixel threshold (overrides config if provided)

        Returns:
            Comparison result with pixel statistics

        Raises:
            ValueError: If screenshots cannot be loaded
        """
        start_time = time.time()

        # Use provided threshold or config default
        pixel_threshold = threshold or self.config.pixel_threshold

        logger.info(f"Comparing {before_path.name} vs {after_path.name} (threshold={pixel_threshold}px)")

        # Load images
        try:
            before_img = cv2.imread(str(before_path))
            after_img = cv2.imread(str(after_path))

            if before_img is None:
                raise ValueError(f"Cannot load before image: {before_path}")
            if after_img is None:
                raise ValueError(f"Cannot load after image: {after_path}")

        except Exception as e:
            logger.error(f"Failed to load images: {e}")
            raise ValueError(f"Failed to load images: {e}")

        # Ensure images are same size
        if before_img.shape != after_img.shape:
            logger.warning(f"Image size mismatch: {before_img.shape} vs {after_img.shape}")
            # Resize after_img to match before_img
            after_img = cv2.resize(after_img, (before_img.shape[1], before_img.shape[0]))
            logger.info(f"Resized after image to match before: {before_img.shape[:2][::-1]}")

        # Apply anti-aliasing filter if enabled
        if self.config.enable_anti_aliasing_filter:
            before_img = self._apply_gaussian_blur(before_img)
            after_img = self._apply_gaussian_blur(after_img)

        # Compute absolute difference
        diff = cv2.absdiff(before_img, after_img)

        # Convert to grayscale for thresholding
        diff_gray = cv2.cvtColor(diff, cv2.COLOR_BGR2GRAY)

        # Apply threshold
        _, thresh = cv2.threshold(diff_gray, pixel_threshold, 255, cv2.THRESH_BINARY)

        # Count changed pixels
        changed_pixels = cv2.countNonZero(thresh)
        total_pixels = diff_gray.shape[0] * diff_gray.shape[1]
        changed_percentage = (changed_pixels / total_pixels) * 100

        elapsed = time.time() - start_time
        logger.info(f"Comparison complete in {elapsed:.2f}s: {changed_pixels:,} pixels changed ({changed_percentage:.2f}%)")

        # Create result (will be enhanced in later plans)
        result = ComparisonResult(
            before_path=before_path,
            after_path=after_path,
            threshold=pixel_threshold,
            changed_pixels=changed_pixels,
            total_pixels=total_pixels,
            changed_percentage=changed_percentage,
            intended_changes=[],  # P3-PLAN-7
            unintended_changes=[],  # P3-PLAN-7
            passed=False,  # P3-PLAN-7
            failure_reason=None,  # P3-PLAN-7
            heatmap_path=None,  # P3-PLAN-3
            report_path=None,  # P3-PLAN-3
            timestamp=datetime.now(),
        )

        return result

    def _apply_gaussian_blur(self, image: np.ndarray) -> np.ndarray:
        """Apply Gaussian blur to reduce anti-aliasing noise.

        Args:
            image: Input image (OpenCV format)

        Returns:
            Blurred image
        """
        kernel_size = self.config.anti_aliasing_kernel_size
        # Ensure kernel size is odd
        if kernel_size % 2 == 0:
            kernel_size += 1

        blurred = cv2.GaussianBlur(image, (kernel_size, kernel_size), 0)
        return blurred

    def create_heatmap(
        self,
        before_path: Path,
        after_path: Path,
        output_path: Path,
        threshold: int | None = None,
        color_scheme: HeatmapColorScheme = HeatmapColorScheme.YELLOW_ORANGE_RED,
        opacity: float = 0.6,
    ) -> Path:
        """Create heatmap visualization of differences.

        Args:
            before_path: Path to baseline screenshot
            after_path: Path to current screenshot
            output_path: Path to save heatmap
            threshold: Pixel threshold for highlighting
            color_scheme: Color scheme for heatmap
            opacity: Overlay opacity (0.0-1.0)

        Returns:
            Path to saved heatmap
        """
        pixel_threshold = threshold or self.config.pixel_threshold

        logger.info(f"Creating heatmap: {before_path.name} → {output_path.name}")

        # Load images
        before_img = cv2.imread(str(before_path))
        after_img = cv2.imread(str(after_path))

        if before_img is None or after_img is None:
            raise ValueError("Cannot load images for heatmap")

        # Ensure same size
        if before_img.shape != after_img.shape:
            after_img = cv2.resize(after_img, (before_img.shape[1], before_img.shape[0]))

        # Apply anti-aliasing filter if enabled
        if self.config.enable_anti_aliasing_filter:
            before_img = self._apply_gaussian_blur(before_img)
            after_img = self._apply_gaussian_blur(after_img)

        # Compute difference
        diff = cv2.absdiff(before_img, after_img)
        diff_gray = cv2.cvtColor(diff, cv2.COLOR_BGR2GRAY)

        # Apply threshold
        _, thresh = cv2.threshold(diff_gray, pixel_threshold, 255, cv2.THRESH_BINARY)

        # Create heatmap based on color scheme
        if color_scheme == HeatmapColorScheme.YELLOW_ORANGE_RED:
            # Yellow (subtle) → Orange (moderate) → Red (dramatic)
            heatmap = cv2.applyColorMap(thresh, cv2.COLORMAP_HOT)
        elif color_scheme == HeatmapColorScheme.BLUE_CYAN_GREEN:
            heatmap = cv2.applyColorMap(thresh, cv2.COLORMAP_OCEAN)
        else:  # Grayscale
            heatmap = cv2.cvtColor(thresh, cv2.COLOR_GRAY2BGR)

        # Overlay on original image
        overlay = cv2.addWeighted(after_img, 1 - opacity, heatmap, opacity, 0)

        # Save heatmap
        output_path.parent.mkdir(parents=True, exist_ok=True)
        cv2.imwrite(str(output_path), overlay)

        logger.info(f"Heatmap saved: {output_path}")
        return output_path

    def find_change_regions(
        self,
        before_path: Path,
        after_path: Path,
        threshold: int | None = None,
        min_region_size: int = 100,
    ) -> list[tuple[int, int, int, int]]:
        """Find bounding boxes of changed regions.

        Uses contour detection to find contiguous regions of change.

        Args:
            before_path: Path to baseline screenshot
            after_path: Path to current screenshot
            threshold: Pixel threshold for change detection
            min_region_size: Minimum region size in pixels

        Returns:
            List of bounding boxes [x, y, width, height]
        """
        pixel_threshold = threshold or self.config.pixel_threshold

        # Load and compare images
        before_img = cv2.imread(str(before_path))
        after_img = cv2.imread(str(after_path))

        if before_img is None or after_img is None:
            raise ValueError("Cannot load images")

        # Ensure same size
        if before_img.shape != after_img.shape:
            after_img = cv2.resize(after_img, (before_img.shape[1], before_img.shape[0]))

        # Apply anti-aliasing filter if enabled
        if self.config.enable_anti_aliasing_filter:
            before_img = self._apply_gaussian_blur(before_img)
            after_img = self._apply_gaussian_blur(after_img)

        # Compute difference
        diff = cv2.absdiff(before_img, after_img)
        diff_gray = cv2.cvtColor(diff, cv2.COLOR_BGR2GRAY)

        # Apply threshold
        _, thresh = cv2.threshold(diff_gray, pixel_threshold, 255, cv2.THRESH_BINARY)

        # Find contours
        contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        # Extract bounding boxes
        regions = []
        for contour in contours:
            x, y, w, h = cv2.boundingRect(contour)
            area = w * h

            # Filter small regions
            if area >= min_region_size:
                regions.append((x, y, w, h))

        logger.info(f"Found {len(regions)} change regions")
        return regions
