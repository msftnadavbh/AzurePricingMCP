"""Tool definitions for the Azure network cost planner."""

from mcp.types import Tool


def get_network_tool_definitions() -> list[Tool]:
    """Return MCP tool definitions for the Azure network cost planner."""
    return [
        Tool(
            name="azure_network_cost_estimate",
            description=(
                "Estimate the monthly and annual cost of an Azure networking topology "
                "(bandwidth / data egress, NAT Gateway, Public IP, Load Balancer, Private Link, "
                "Application Gateway) using real-time Azure Retail Prices. Bandwidth is priced with "
                "graduated tiers (tierMinimumUnits). Only pay-as-you-go Consumption meters are used - "
                "Reservation rows are never treated as hourly prices. Regional meters fall back to "
                "Global pricing only when necessary and the result is clearly marked. Components that "
                "cannot be matched to a single unambiguous meter are listed as unpriced rather than guessed."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "source_region": {
                        "type": "string",
                        "description": "Source Azure region (e.g., 'eastus', 'westeurope').",
                    },
                    "destination_region": {
                        "type": "string",
                        "description": "Destination Azure region (optional; used for cross-region transfers).",
                    },
                    "destination_type": {
                        "type": "string",
                        "description": (
                            "Traffic destination type. One of: internet, same_region, cross_region, "
                            "intercontinental, private_link, expressroute."
                        ),
                        "enum": [
                            "internet",
                            "same_region",
                            "cross_region",
                            "intercontinental",
                            "private_link",
                            "expressroute",
                        ],
                        "default": "internet",
                    },
                    "monthly_data_gb": {
                        "type": "number",
                        "description": "Monthly outbound data volume in GB (default: 0).",
                        "default": 0,
                    },
                    "gateway_hours": {
                        "type": "number",
                        "description": "Monthly runtime hours for hourly resources like NAT Gateway (default: 730).",
                        "default": 730,
                    },
                    "include_nat_gateway": {
                        "type": "boolean",
                        "description": "Include NAT Gateway hourly + data-processed charges (default: false).",
                        "default": False,
                    },
                    "include_public_ip": {
                        "type": "boolean",
                        "description": "Include a Standard Public IP address charge when confidently matched (default: false).",
                        "default": False,
                    },
                    "include_load_balancer": {
                        "type": "boolean",
                        "description": "Include a Load Balancer charge when confidently matched (default: false).",
                        "default": False,
                    },
                    "include_private_link": {
                        "type": "boolean",
                        "description": "Include Private Link endpoint + data-processed charges when confidently matched (default: false).",
                        "default": False,
                    },
                    "include_application_gateway": {
                        "type": "boolean",
                        "description": "Include an Application Gateway charge when confidently matched (default: false).",
                        "default": False,
                    },
                    "currency_code": {
                        "type": "string",
                        "description": "Currency code for pricing (default: 'USD').",
                        "default": "USD",
                    },
                    "discount_percentage": {
                        "type": "number",
                        "description": (
                            "Optional discount percentage applied to the priced subtotal. " "Not applied by default."
                        ),
                    },
                },
                "required": ["source_region"],
            },
        ),
    ]
