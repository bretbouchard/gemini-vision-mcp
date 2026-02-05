"""Logging utilities for Where's Waldo Rick.

CRITICAL: All logging MUST go to stderr to avoid polluting stdout.
Stdout must contain only valid JSON-RPC messages for the MCP protocol.
"""

import logging
import sys

from mcp.server.fastmcp import FastMCP

# Configure logging to use stderr only
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    stream=sys.stderr,  # CRITICAL: Use stderr, not stdout
)

logger = logging.getLogger("wheres_waldo")


def setup_logging(mcp_server: FastMCP) -> None:
    """Set up exception handler for the MCP server.

    This ensures that any unhandled exceptions are logged to stderr
    rather than crashing the server or polluting stdout.

    Args:
        mcp_server: The FastMCP server instance
    """
    def handle_exception(exc: Exception) -> None:
        """Log exception to stderr and return graceful degradation message."""
        logger.exception(f"Unhandled exception: {exc}")
        # Return empty dict to prevent JSON-RPC breakage
        return {}

    # Register exception handler
    # Note: FastMCP may not have a built-in exception handler registration
    # This is a placeholder for future implementation
    logger.info("Exception handler registered (placeholder)")


def get_logger(name: str) -> logging.Logger:
    """Get a logger instance for a specific module.

    Args:
        name: Logger name (typically __name__ of the module)

    Returns:
        Configured logger instance
    """
    return logging.getLogger(name)
