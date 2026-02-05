"""Utility functions for Where's Waldo Rick.

Provides image hashing, path helpers, and file naming utilities.
"""

import hashlib
from datetime import datetime
from pathlib import Path

from PIL import Image

from wheres_waldo.models.domain import ImageFormat, Platform, Quality
from wheres_waldo.utils.logging import get_logger

logger = get_logger(__name__)


def hash_image_pair(image1_path: Path, image2_path: Path, threshold: int = 2) -> str:
    """Generate hash key for image pair with threshold.

    Used for caching comparison results.

    Args:
        image1_path: Path to first image
        image2_path: Path to second image
        threshold: Pixel threshold used for comparison

    Returns:
        SHA256 hash string
    """
    # Create hash input from sorted paths and threshold
    hash_input = f"{sorted([str(image1_path), str(image2_path)])[0]}|{sorted([str(image1_path), str(image2_path)])[1]}|{threshold}"

    # Generate SHA256 hash
    hash_obj = hashlib.sha256(hash_input.encode())
    return hash_obj.hexdigest()


def hash_image_content(image_path: Path) -> str:
    """Generate hash key for image content.

    Used for detecting duplicate screenshots.

    Args:
        image_path: Path to image file

    Returns:
        SHA256 hash of image content
    """
    try:
        with open(image_path, "rb") as f:
            # Read image file in chunks to handle large files
            hash_obj = hashlib.sha256()
            while chunk := f.read(8192):
                hash_obj.update(chunk)
            return hash_obj.hexdigest()
    except Exception as e:
        logger.error(f"Failed to hash image {image_path}: {e}")
        return ""


def get_phase_dir(base_dir: Path, phase: str) -> Path:
    """Get directory path for a phase.

    Args:
        base_dir: Base screenshots directory
        phase: Phase name

    Returns:
        Path to phase directory
    """
    # Sanitize phase name for filesystem
    safe_phase = phase.lower().replace(" ", "-").replace("/", "-")
    return base_dir / "phases" / safe_phase


def get_baseline_path(baseline_id: str) -> Path:
    """Get path for baseline file.

    Args:
        baseline_id: Baseline identifier

    Returns:
        Path to baseline file
    """
    return Path(".screenshots") / "baselines" / f"{baseline_id}.json"


def generate_screenshot_name(name: str) -> str:
    """Generate filesystem-safe screenshot filename.

    Args:
        name: Descriptive name for screenshot

    Returns:
        Filesystem-safe filename with timestamp
    """
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    safe_name = name.lower().replace(" ", "-").replace("/", "-").replace("\\", "-")
    return f"{timestamp}-{safe_name}"


def generate_screenshot_path(
    base_dir: Path,
    phase: str,
    name: str,
    quality: Quality = Quality.X2,
    format: ImageFormat = ImageFormat.PNG,
) -> Path:
    """Generate full path for screenshot file.

    Args:
        base_dir: Base screenshots directory
        phase: Phase name
        name: Descriptive name for screenshot
        quality: Resolution quality
        format: Image format

    Returns:
        Full path to screenshot file
    """
    phase_dir = get_phase_dir(base_dir, phase)
    filename = generate_screenshot_name(name)
    return phase_dir / f"{filename}.{format.value}"


def get_image_resolution(image_path: Path) -> tuple[int, int] | None:
    """Get image resolution (width, height).

    Args:
        image_path: Path to image file

    Returns:
        Tuple of (width, height) or None if failed
    """
    try:
        with Image.open(image_path) as img:
            return img.size
    except Exception as e:
        logger.error(f"Failed to get resolution for {image_path}: {e}")
        return None


def get_image_file_size(image_path: Path) -> int | None:
    """Get image file size in bytes.

    Args:
        image_path: Path to image file

    Returns:
        File size in bytes or None if failed
    """
    try:
        return image_path.stat().st_size
    except Exception as e:
        logger.error(f"Failed to get file size for {image_path}: {e}")
        return None


def format_resolution(width: int, height: int) -> str:
    """Format resolution as string.

    Args:
        width: Image width in pixels
        height: Image height in pixels

    Returns:
        Resolution string (e.g., "1920x1080")
    """
    return f"{width}x{height}"


def parse_resolution(resolution_str: str) -> tuple[int, int] | None:
    """Parse resolution string to width and height.

    Args:
        resolution_str: Resolution string (e.g., "1920x1080")

    Returns:
        Tuple of (width, height) or None if invalid format
    """
    try:
        parts = resolution_str.lower().split("x")
        if len(parts) == 2:
            width = int(parts[0])
            height = int(parts[1])
            return (width, height)
    except (ValueError, AttributeError):
        pass

    logger.error(f"Invalid resolution format: {resolution_str}")
    return None


def format_file_size(bytes_size: int) -> str:
    """Format file size in human-readable format.

    Args:
        bytes_size: File size in bytes

    Returns:
        Human-readable size string (e.g., "1.5 MB")
    """
    for unit in ["B", "KB", "MB", "GB"]:
        if bytes_size < 1024.0:
            return f"{bytes_size:.1f} {unit}"
        bytes_size /= 1024.0
    return f"{bytes_size:.1f} TB"


def detect_platform_from_environment() -> Platform:
    """Detect current platform from environment.

    Checks for iOS Simulator, macOS, or falls back to auto.

    Returns:
        Detected platform
    """
    import os
    import sys

    # Check if running in iOS Simulator
    if os.getenv("SIMULATOR_ROOT_DIRECTORY") or os.getenv("XCODE_SIMULATOR_ROOT"):
        return Platform.IOS

    # Check if running on macOS
    if sys.platform == "darwin":
        return Platform.MACOS

    # Fallback to auto-detection
    return Platform.AUTO


def validate_image_format(image_path: Path) -> bool:
    """Validate that file is a valid image.

    Args:
        image_path: Path to image file

    Returns:
        True if valid image, False otherwise
    """
    try:
        with Image.open(image_path) as img:
            img.verify()
        return True
    except Exception as e:
        logger.error(f"Invalid image file {image_path}: {e}")
        return False


def ensure_directory_exists(path: Path) -> None:
    """Ensure directory exists, create if missing.

    Args:
        path: Directory path to ensure
    """
    path.mkdir(parents=True, exist_ok=True)
    logger.debug(f"Ensured directory exists: {path}")
