"""Configuration management for Where's Waldo Rick.

Loads configuration from config file with fallback to defaults.
Supports environment variable overrides.
"""

import json
import os
from pathlib import Path
from typing import Any

from pydantic import ValidationError

from wheres_waldo.models.domain import AppConfig, StorageConfig
from wheres_waldo.utils.logging import get_logger

logger = get_logger(__name__)


class ConfigService:
    """Configuration management service.

    Loads configuration from .screenshots/config.json with fallback to defaults.
    Environment variables override config file values.
    """

    DEFAULT_CONFIG_PATH = Path(".screenshots/config.json")

    def __init__(self, config_path: Path | None = None) -> None:
        """Initialize config service.

        Args:
            config_path: Path to config file (uses default if not provided)
        """
        self.config_path = config_path or self.DEFAULT_CONFIG_PATH
        self.config = self._load_config()

    def _load_config(self) -> AppConfig:
        """Load configuration from file or create default.

        Returns:
            Validated AppConfig instance
        """
        # Try to load from file
        if self.config_path.exists():
            try:
                with open(self.config_path, "r") as f:
                    config_data = json.load(f)

                # Apply environment variable overrides
                config_data = self._apply_env_overrides(config_data)

                config = AppConfig(**config_data)
                logger.info(f"Loaded config from {self.config_path}")
                return config

            except (json.JSONDecodeError, ValidationError) as e:
                logger.warning(f"Failed to load config from {self.config_path}: {e}")
                logger.info("Using default configuration")
        else:
            logger.info(f"Config file not found at {self.config_path}, using defaults")

        # Return default configuration
        return self._create_default_config()

    def _create_default_config(self) -> AppConfig:
        """Create default configuration and save to disk.

        Returns:
            Default AppConfig instance
        """
        config = AppConfig()

        # Ensure directory exists
        self.config_path.parent.mkdir(parents=True, exist_ok=True)

        # Save default config to disk
        try:
            with open(self.config_path, "w") as f:
                json.dump(config.model_dump(), f, indent=2)
            logger.info(f"Created default config at {self.config_path}")
        except Exception as e:
            logger.error(f"Failed to save default config: {e}")

        return config

    def _apply_env_overrides(self, config_data: dict[str, Any]) -> dict[str, Any]:
        """Apply environment variable overrides to config.

        Supported environment variables:
        - GEMINI_API_KEY: Gemini API key
        - WALDO_DEFAULT_PLATFORM: Default platform (macos, ios, web, auto)
        - WALDO_DEFAULT_QUALITY: Default quality (1x, 2x, 3x)
        - WALDO_DEFAULT_FORMAT: Default format (png, jpeg, webp)
        - WALDO_RETENTION_DAYS: Screenshot retention period
        - WALDO_AUTO_CLEANUP: Enable automatic cleanup (true/false)

        Args:
            config_data: Config data from file

        Returns:
            Config data with env overrides applied
        """
        # Gemini API key
        if api_key := os.getenv("GEMINI_API_KEY"):
            config_data["gemini_api_key"] = api_key
            logger.debug("Applied GEMINI_API_KEY from environment")

        # Default platform
        if platform := os.getenv("WALDO_DEFAULT_PLATFORM"):
            if platform in ["macos", "ios", "web", "auto"]:
                config_data["default_platform"] = platform
                logger.debug(f"Applied WALDO_DEFAULT_PLATFORM={platform}")

        # Default quality
        if quality := os.getenv("WALDO_DEFAULT_QUALITY"):
            if quality in ["1x", "2x", "3x"]:
                config_data["default_quality"] = quality
                logger.debug(f"Applied WALDO_DEFAULT_QUALITY={quality}")

        # Default format
        if format_ := os.getenv("WALDO_DEFAULT_FORMAT"):
            if format_ in ["png", "jpeg", "webp"]:
                config_data["default_format"] = format_
                logger.debug(f"Applied WALDO_DEFAULT_FORMAT={format_}")

        # Retention days
        if retention := os.getenv("WALDO_RETENTION_DAYS"):
            try:
                retention_days = int(retention)
                if "storage" not in config_data:
                    config_data["storage"] = {}
                config_data["storage"]["retention_days"] = retention_days
                logger.debug(f"Applied WALDO_RETENTION_DAYS={retention_days}")
            except ValueError:
                logger.warning(f"Invalid WALDO_RETENTION_DAYS value: {retention}")

        # Auto cleanup
        if auto_cleanup := os.getenv("WALDO_AUTO_CLEANUP"):
            if "storage" not in config_data:
                config_data["storage"] = {}
            config_data["storage"]["enable_auto_cleanup"] = auto_cleanup.lower() == "true"
            logger.debug(f"Applied WALDO_AUTO_CLEANUP={auto_cleanup}")

        return config_data

    def get_config(self) -> AppConfig:
        """Get current configuration.

        Returns:
            Current AppConfig instance
        """
        return self.config

    def save_config(self, config: AppConfig) -> None:
        """Save configuration to disk.

        Args:
            config: AppConfig to save
        """
        try:
            # Ensure directory exists
            self.config_path.parent.mkdir(parents=True, exist_ok=True)

            # Save to file
            with open(self.config_path, "w") as f:
                json.dump(config.model_dump(), f, indent=2)

            # Update in-memory config
            self.config = config

            logger.info(f"Saved config to {self.config_path}")
        except Exception as e:
            logger.error(f"Failed to save config: {e}")
            raise

    def update_config(self, updates: dict[str, Any]) -> AppConfig:
        """Update configuration with partial updates.

        Args:
            updates: Dictionary of config updates

        Returns:
            Updated AppConfig instance
        """
        # Get current config as dict
        current = self.config.model_dump()

        # Deep merge updates
        def deep_merge(base: dict, updates: dict) -> dict:
            """Deep merge updates into base dict."""
            result = base.copy()
            for key, value in updates.items():
                if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                    result[key] = deep_merge(result[key], value)
                else:
                    result[key] = value
            return result

        merged = deep_merge(current, updates)

        # Validate and save
        try:
            updated_config = AppConfig(**merged)
            self.save_config(updated_config)
            return updated_config
        except ValidationError as e:
            logger.error(f"Invalid config update: {e}")
            raise
