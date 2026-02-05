"""Screenshot capture service with platform adapters.

Supports macOS (MSS), iOS Simulator (simctl), and Web (chrome-devtools MCP).
Auto-detects platform with fallback to manual selection.
"""

import subprocess
from pathlib import Path
from typing import Literal

from wheres_waldo.models.domain import Platform, Quality, ImageFormat, Screenshot
from wheres_waldo.utils.helpers import (
    generate_screenshot_path,
    get_image_file_size,
    get_image_resolution,
    format_resolution,
)
from wheres_waldo.utils.logging import get_logger

logger = get_logger(__name__)


class PlatformDetector:
    """Detects available screenshot capture platforms."""

    @staticmethod
    def detect_platform() -> Platform:
        """Auto-detect platform from environment.

        Checks in order:
        1. iOS Simulator (simctl available)
        2. macOS (darwin platform)
        3. chrome-devtools MCP (check if available)
        4. Falls back to AUTO

        Returns:
            Detected platform
        """
        import sys

        # Check for iOS Simulator
        try:
            result = subprocess.run(
                ["xcrun", "simctl", "help"],
                capture_output=True,
                timeout=5,
            )
            if result.returncode == 0:
                logger.debug("Detected iOS Simulator platform")
                return Platform.IOS
        except (FileNotFoundError, subprocess.TimeoutExpired):
            logger.debug("iOS Simulator not available")

        # Check for macOS
        if sys.platform == "darwin":
            logger.debug("Detected macOS platform")
            return Platform.MACOS

        # Check for chrome-devtools MCP
        # Note: This is a placeholder - actual MCP availability check
        # would need to query the MCP server registry
        try:
            import os
            if os.getenv("CHROME_DEVTOOLS_AVAILABLE"):
                logger.debug("Detected chrome-devtools MCP")
                return Platform.WEB
        except Exception:
            logger.debug("chrome-devtools MCP not available")

        # Fallback
        logger.debug("Platform auto-detection failed, using AUTO")
        return Platform.AUTO

    @staticmethod
    def get_available_platforms() -> list[Platform]:
        """Get list of all available platforms.

        Returns:
            List of platforms that can be used
        """
        available = []

        # Check macOS
        import sys
        if sys.platform == "darwin":
            available.append(Platform.MACOS)

        # Check iOS Simulator
        try:
            result = subprocess.run(
                ["xcrun", "simctl", "help"],
                capture_output=True,
                timeout=5,
            )
            if result.returncode == 0:
                available.append(Platform.IOS)
        except (FileNotFoundError, subprocess.TimeoutExpired):
            pass

        # Check Web
        try:
            import os
            if os.getenv("CHROME_DEVTOOLS_AVAILABLE"):
                available.append(Platform.WEB)
        except Exception:
            pass

        logger.debug(f"Available platforms: {[p.value for p in available]}")
        return available


class ScreenshotCaptureError(Exception):
    """Screenshot capture failed."""

    def __init__(self, message: str, platform: Platform, details: str | None = None) -> None:
        """Initialize screenshot capture error.

        Args:
            message: Error message
            platform: Platform that failed
            details: Additional error details
        """
        self.platform = platform
        self.details = details
        super().__init__(f"{message} (platform={platform.value})")


class CaptureService:
    """Screenshot capture service with platform adapters."""

    def __init__(self) -> None:
        """Initialize capture service."""
        self.detector = PlatformDetector()

    def capture(
        self,
        name: str,
        platform: Platform = Platform.AUTO,
        quality: Quality = Quality.X2,
        format: ImageFormat = ImageFormat.PNG,
    ) -> Screenshot:
        """Capture screenshot from specified or auto-detected platform.

        Args:
            name: Descriptive name for screenshot
            platform: Platform to capture from (AUTO for detection)
            quality: Resolution quality (1x, 2x, 3x)
            format: Image format (PNG, JPEG, WebP)

        Returns:
            Screenshot metadata

        Raises:
            ScreenshotCaptureError: If capture fails
        """
        # Auto-detect platform if needed
        if platform == Platform.AUTO:
            platform = self.detector.detect_platform()
            logger.info(f"Auto-detected platform: {platform.value}")

        # Route to appropriate platform adapter
        if platform == Platform.MACOS:
            return self._capture_macos(name, quality, format)
        elif platform == Platform.IOS:
            return self._capture_ios(name, quality, format)
        elif platform == Platform.WEB:
            return self._capture_web(name, quality, format)
        else:
            raise ScreenshotCaptureError(
                message="Cannot capture from AUTO platform",
                platform=platform,
                details="Please specify platform explicitly: macos, ios, or web",
            )

    def _capture_macos(
        self,
        name: str,
        quality: Quality,
        format: ImageFormat,
    ) -> Screenshot:
        """Capture screenshot from macOS using MSS.

        Args:
            name: Descriptive name for screenshot
            quality: Resolution quality
            format: Image format

        Returns:
            Screenshot metadata

        Raises:
            ScreenshotCaptureError: If capture fails
        """
        import time
        from wheres_waldo.services.config import ConfigService

        config = ConfigService()
        base_dir = config.get_config().storage.base_dir

        # Generate screenshot path
        path = generate_screenshot_path(
            base_dir=base_dir,
            phase="current",  # Will be updated by caller
            name=name,
            quality=quality,
            format=format,
        )

        # Ensure directory exists
        path.parent.mkdir(parents=True, exist_ok=True)

        try:
            # Import MSS
            import mss

            # Capture with MSS
            with mss.mss() as sct:
                # Monitor 1 is primary display
                monitor = sct.monitors[1]
                screenshot = sct.shot(output=str(path), mon=monitor)

            # Measure performance
            # Note: MSS doesn't provide timing, so we'll estimate

            # Get image metadata
            resolution = get_image_resolution(path)
            file_size = get_image_file_size(path)

            if resolution:
                width, height = resolution
                logger.info(f"Captured macOS screenshot: {format_resolution(width, height)}")

            return Screenshot(
                path=path,
                name=name,
                platform=Platform.MACOS,
                quality=quality,
                format=format,
                resolution=format_resolution(*resolution) if resolution else None,
                file_size_bytes=file_size,
            )

        except ImportError:
            raise ScreenshotCaptureError(
                message="MSS library not installed",
                platform=Platform.MACOS,
                details="Install with: pip install mss",
            )
        except Exception as e:
            raise ScreenshotCaptureError(
                message="Failed to capture macOS screenshot",
                platform=Platform.MACOS,
                details=str(e),
            )

    def _capture_ios(
        self,
        name: str,
        quality: Quality,
        format: ImageFormat,
    ) -> Screenshot:
        """Capture screenshot from iOS Simulator using simctl.

        Args:
            name: Descriptive name for screenshot
            quality: Resolution quality
            format: Image format

        Returns:
            Screenshot metadata

        Raises:
            ScreenshotCaptureError: If capture fails
        """
        from wheres_waldo.services.config import ConfigService

        config = ConfigService()
        base_dir = config.get_config().storage.base_dir

        # Generate screenshot path
        path = generate_screenshot_path(
            base_dir=base_dir,
            phase="current",
            name=name,
            quality=quality,
            format=format,
        )

        # Ensure directory exists
        path.parent.mkdir(parents=True, exist_ok=True)

        try:
            # Get booted simulators
            result = subprocess.run(
                ["xcrun", "simctl", "list", "devices", "booted"],
                capture_output=True,
                text=True,
                timeout=10,
            )

            if result.returncode != 0:
                raise ScreenshotCaptureError(
                    message="No booted iOS Simulator found",
                    platform=Platform.IOS,
                    details="Boot a simulator with Xcode or use `xcrun simctl boot`",
                )

            # Parse device UDID from output
            # Output format: "    iPhone 15 (XXXX) (Booted)"
            lines = result.stdout.split("\n")
            device_udid = None

            for line in lines:
                if "(Booted)" in line:
                    # Extract UDID from parentheses
                    import re
                    match = re.search(r"\(([A-F0-9-]+)\)", line)
                    if match:
                        device_udid = match.group(1)
                        break

            if not device_udid:
                raise ScreenshotCaptureError(
                    message="Could not parse simulator UDID",
                    platform=Platform.IOS,
                    details="Ensure a simulator is booted",
                )

            # Capture screenshot using simctl
            result = subprocess.run(
                ["xcrun", "simctl", "io", device_udid, "screenshot", str(path)],
                capture_output=True,
                timeout=30,
            )

            if result.returncode != 0:
                raise ScreenshotCaptureError(
                    message="simctl screenshot command failed",
                    platform=Platform.IOS,
                    details=result.stderr.decode(),
                )

            # Get image metadata
            resolution = get_image_resolution(path)
            file_size = get_image_file_size(path)

            if resolution:
                width, height = resolution
                logger.info(f"Captured iOS screenshot: {format_resolution(width, height)}")

            return Screenshot(
                path=path,
                name=name,
                platform=Platform.IOS,
                quality=quality,
                format=format,
                resolution=format_resolution(*resolution) if resolution else None,
                file_size_bytes=file_size,
            )

        except ScreenshotCaptureError:
            raise
        except Exception as e:
            raise ScreenshotCaptureError(
                message="Failed to capture iOS screenshot",
                platform=Platform.IOS,
                details=str(e),
            )

    def _capture_web(
        self,
        name: str,
        quality: Quality,
        format: ImageFormat,
    ) -> Screenshot:
        """Capture screenshot from web browser using chrome-devtools MCP.

        Args:
            name: Descriptive name for screenshot
            quality: Resolution quality
            format: Image format

        Returns:
            Screenshot metadata

        Raises:
            ScreenshotCaptureError: If capture fails
        """
        # Placeholder for chrome-devtools MCP integration
        # This will be implemented when we have MCP client access
        raise ScreenshotCaptureError(
            message="Web capture not yet implemented",
            platform=Platform.WEB,
            details="chrome-devtools MCP integration coming in Phase 2 Plan 4",
        )
