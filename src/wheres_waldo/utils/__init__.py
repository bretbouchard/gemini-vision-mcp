"""Utility functions for Where's Waldo Rick."""

from wheres_waldo.utils.helpers import (
    ensure_directory_exists,
    detect_platform_from_environment,
    format_file_size,
    format_resolution,
    generate_screenshot_name,
    generate_screenshot_path,
    get_baseline_path,
    get_image_file_size,
    get_image_resolution,
    get_phase_dir,
    hash_image_content,
    hash_image_pair,
    parse_resolution,
    validate_image_format,
)
from wheres_waldo.utils.logging import get_logger, setup_logging

__all__ = [
    "ensure_directory_exists",
    "detect_platform_from_environment",
    "format_file_size",
    "format_resolution",
    "generate_screenshot_name",
    "generate_screenshot_path",
    "get_baseline_path",
    "get_image_file_size",
    "get_image_resolution",
    "get_phase_dir",
    "hash_image_content",
    "hash_image_pair",
    "parse_resolution",
    "validate_image_format",
    "get_logger",
    "setup_logging",
]
