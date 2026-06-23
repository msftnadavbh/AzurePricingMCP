"""Handler methods for the Azure network cost planner tool."""

from __future__ import annotations

from typing import Any

from mcp.types import TextContent

from ..services.network_cost import NetworkCostService
from .formatters import format_network_cost_estimate_response


class NetworkHandlers:
    """Mixin providing handler methods for the network cost planner.

    Designed to be composed into the main ``ToolHandlers`` class. Requires a
    ``_network_service`` attribute on the host instance.
    """

    _network_service: NetworkCostService | None

    def _get_network_service(self) -> NetworkCostService:
        """Get the NetworkCostService instance.

        Raises:
            RuntimeError: If NetworkCostService was not provided at init time.
        """
        if self._network_service is None:
            raise RuntimeError("NetworkCostService not initialized")
        return self._network_service

    async def handle_network_cost_estimate(self, arguments: dict[str, Any]) -> list[TextContent]:
        """Handle ``azure_network_cost_estimate`` tool calls."""
        service = self._get_network_service()
        result = await service.estimate_network_cost(
            source_region=arguments["source_region"],
            destination_region=arguments.get("destination_region"),
            destination_type=arguments.get("destination_type", "internet"),
            monthly_data_gb=arguments.get("monthly_data_gb", 0.0),
            gateway_hours=arguments.get("gateway_hours", 730.0),
            include_nat_gateway=arguments.get("include_nat_gateway", False),
            include_public_ip=arguments.get("include_public_ip", False),
            include_load_balancer=arguments.get("include_load_balancer", False),
            include_private_link=arguments.get("include_private_link", False),
            include_application_gateway=arguments.get("include_application_gateway", False),
            currency_code=arguments.get("currency_code", "USD"),
            discount_percentage=arguments.get("discount_percentage"),
        )
        text = format_network_cost_estimate_response(result)
        return [TextContent(type="text", text=text)]
