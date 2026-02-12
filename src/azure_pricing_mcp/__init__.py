"""Azure Pricing MCP Server

A Model Context Protocol server for querying Azure retail pricing information.
"""

from .server import AzurePricingServer, create_server, main, run

__version__ = "3.3.0"
__all__ = [
    "main",
    "run",
    "create_server",
    "AzurePricingServer",
]
