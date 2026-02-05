"""Where's Waldo Rick - MCP Server.

This module implements the MCP server with tools for visual regression testing
using Gemini 3 Flash's agentic vision capabilities.
"""

from mcp.server.fastmcp import FastMCP

from wheres_waldo.utils.logging import get_logger, setup_logging
from wheres_waldo.tools import visual_tools

# Get logger (all logs go to stderr)
logger = get_logger(__name__)

# Create MCP server instance
mcp = FastMCP("wheres-waldo-rick")

# Set up exception handler
setup_logging(mcp)
logger.info("Where's Waldo Rick MCP server initialized")

# Register all visual tools
visual_tools.register_visual_tools(mcp)
logger.info("Registered 5 visual tools: visual_capture, visual_prepare, visual_compare, visual_cleanup, visual_list")


def main() -> None:
    """Start the MCP server.

    IMPORTANT: All logging must go to stderr to avoid polluting stdout,
    which must contain only valid JSON-RPC messages.
    """
    # Run the MCP server
    mcp.run()


if __name__ == "__main__":
    main()
