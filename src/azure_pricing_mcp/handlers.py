"""Tool handlers for Azure Pricing MCP Server."""

import logging
from typing import Any

from mcp.types import TextContent

from .config import DEFAULT_CUSTOMER_DISCOUNT
from .formatters import (
    format_cost_estimate_response,
    format_customer_discount_response,
    format_discover_skus_response,
    format_price_compare_response,
    format_price_search_response,
    format_region_recommend_response,
    format_ri_pricing_response,
    format_sku_discovery_response,
)
from .services import PricingService, SKUService

logger = logging.getLogger(__name__)


class ToolHandlers:
    """Handlers for MCP tool calls."""

    def __init__(self, pricing_service: PricingService, sku_service: SKUService) -> None:
        self._pricing_service = pricing_service
        self._sku_service = sku_service

    def _resolve_discount(self, arguments: dict[str, Any]) -> tuple[float, bool, bool]:
        """Resolve discount parameters.

        Returns:
            Tuple of (discount_percentage, discount_specified, used_default_discount)
        """
        show_with_discount = arguments.pop("show_with_discount", False)
        discount_specified = "discount_percentage" in arguments

        if discount_specified:
            # User explicitly provided a discount percentage
            discount_percentage = arguments["discount_percentage"]
            used_default_discount = False
        elif show_with_discount:
            # User requested discount but didn't specify - use default
            discount_percentage = DEFAULT_CUSTOMER_DISCOUNT
            used_default_discount = True
            arguments["discount_percentage"] = discount_percentage
        else:
            # No discount requested - default to 0%
            discount_percentage = 0.0
            used_default_discount = False
            arguments["discount_percentage"] = 0.0

        return discount_percentage, discount_specified, used_default_discount

    async def handle_price_search(self, arguments: dict[str, Any]) -> list[TextContent]:
        """Handle azure_price_search tool calls."""
        discount_percentage, discount_specified, used_default_discount = self._resolve_discount(arguments)

        result = await self._pricing_service.search_prices(**arguments)

        # Add discount metadata for formatting
        result["_discount_metadata"] = {
            "discount_specified": discount_specified,
            "used_default_discount": used_default_discount,
            "discount_percentage": discount_percentage,
        }

        response_text = format_price_search_response(result)
        return [TextContent(type="text", text=response_text)]

    async def handle_price_compare(self, arguments: dict[str, Any]) -> list[TextContent]:
        """Handle azure_price_compare tool calls."""
        discount_percentage, discount_specified, used_default_discount = self._resolve_discount(arguments)

        result = await self._pricing_service.compare_prices(**arguments)

        # Add discount metadata for formatting
        result["_discount_metadata"] = {
            "discount_specified": discount_specified,
            "used_default_discount": used_default_discount,
            "discount_percentage": discount_percentage,
        }

        response_text = format_price_compare_response(result)
        return [TextContent(type="text", text=response_text)]

    async def handle_region_recommend(self, arguments: dict[str, Any]) -> list[TextContent]:
        """Handle azure_region_recommend tool calls."""
        discount_percentage, discount_specified, used_default_discount = self._resolve_discount(arguments)

        result = await self._pricing_service.recommend_regions(**arguments)

        # Add discount metadata for formatting
        result["_discount_metadata"] = {
            "discount_specified": discount_specified,
            "used_default_discount": used_default_discount,
            "discount_percentage": discount_percentage,
        }

        response_text = format_region_recommend_response(result)
        return [TextContent(type="text", text=response_text)]

    async def handle_cost_estimate(self, arguments: dict[str, Any]) -> list[TextContent]:
        """Handle azure_cost_estimate tool calls."""
        discount_percentage, discount_specified, used_default_discount = self._resolve_discount(arguments)

        result = await self._pricing_service.estimate_costs(**arguments)

        # Add discount metadata for formatting
        result["_discount_metadata"] = {
            "discount_specified": discount_specified,
            "used_default_discount": used_default_discount,
            "discount_percentage": discount_percentage,
        }

        response_text = format_cost_estimate_response(result)
        return [TextContent(type="text", text=response_text)]

    async def handle_discover_skus(self, arguments: dict[str, Any]) -> list[TextContent]:
        """Handle azure_discover_skus tool calls."""
        result = await self._sku_service.discover_skus(**arguments)
        response_text = format_discover_skus_response(result)
        return [TextContent(type="text", text=response_text)]

    async def handle_sku_discovery(self, arguments: dict[str, Any]) -> list[TextContent]:
        """Handle azure_sku_discovery tool calls."""
        result = await self._sku_service.discover_service_skus(**arguments)
        response_text = format_sku_discovery_response(result)
        return [TextContent(type="text", text=response_text)]

    async def handle_customer_discount(self, arguments: dict[str, Any]) -> list[TextContent]:
        """Handle get_customer_discount tool calls."""
        result = await self._pricing_service.get_customer_discount(**arguments)
        response_text = format_customer_discount_response(result)
        return [TextContent(type="text", text=response_text)]

    async def handle_ri_pricing(self, arguments: dict[str, Any]) -> list[TextContent]:
        """Handle azure_ri_pricing tool calls."""
        result = await self._pricing_service.get_ri_pricing(**arguments)
        response_text = format_ri_pricing_response(result)
        return [TextContent(type="text", text=response_text)]


def register_tool_handlers(server: Any, tool_handlers: ToolHandlers) -> None:
    """Register all tool call handlers with the server.

    Args:
        server: The MCP server instance
        tool_handlers: The ToolHandlers instance
    """

    @server.call_tool()
    async def handle_call_tool(name: str, arguments: dict[str, Any]) -> list[TextContent]:
        """Handle tool calls."""
        try:
            if name == "azure_price_search":
                return await tool_handlers.handle_price_search(arguments)

            elif name == "azure_price_compare":
                return await tool_handlers.handle_price_compare(arguments)

            elif name == "azure_cost_estimate":
                return await tool_handlers.handle_cost_estimate(arguments)

            elif name == "azure_discover_skus":
                return await tool_handlers.handle_discover_skus(arguments)

            elif name == "azure_sku_discovery":
                return await tool_handlers.handle_sku_discovery(arguments)

            elif name == "azure_region_recommend":
                return await tool_handlers.handle_region_recommend(arguments)

            elif name == "azure_ri_pricing":
                return await tool_handlers.handle_ri_pricing(arguments)

            elif name == "get_customer_discount":
                return await tool_handlers.handle_customer_discount(arguments)

            else:
                return [TextContent(type="text", text=f"Unknown tool: {name}")]

        except Exception as e:
            logger.error(f"Error handling tool call {name}: {e}")
            return [TextContent(type="text", text=f"Error: {str(e)}")]
