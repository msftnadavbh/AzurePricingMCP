"""Tests for the Azure network cost planner (service, handler, formatter, routing)."""

from typing import Any
from unittest.mock import patch

import pytest
from mcp.types import TextContent

from azure_pricing_mcp.client import AzurePricingClient
from azure_pricing_mcp.handlers import ToolHandlers
from azure_pricing_mcp.network.formatters import format_network_cost_estimate_response
from azure_pricing_mcp.server import _TOOL_DISPATCH, create_server
from azure_pricing_mcp.services import NetworkCostService
from azure_pricing_mcp.tools import get_tool_definitions

# ---------------------------------------------------------------------------
# Fixtures and helpers
# ---------------------------------------------------------------------------


def _meter(**overrides: Any) -> dict[str, Any]:
    base = {
        "type": "Consumption",
        "retailPrice": 0.05,
        "armRegionName": "eastus",
        "location": "US East",
        "skuName": "Standard",
        "meterName": "Meter",
        "productName": "Product",
        "serviceName": "Service",
        "serviceFamily": "Networking",
        "unitOfMeasure": "1 Hour",
        "tierMinimumUnits": 0.0,
        "currencyCode": "USD",
    }
    base.update(overrides)
    return base


# Internet egress tier ladder.
EGRESS_ITEMS = [
    _meter(
        serviceName="Bandwidth",
        productName="Bandwidth",
        meterName="Standard Data Transfer Out",
        unitOfMeasure="1 GB",
        tierMinimumUnits=0.0,
        retailPrice=0.087,
    ),
    _meter(
        serviceName="Bandwidth",
        productName="Bandwidth",
        meterName="Standard Data Transfer Out",
        unitOfMeasure="1 GB",
        tierMinimumUnits=10240.0,
        retailPrice=0.083,
    ),
    _meter(
        serviceName="Bandwidth",
        productName="Bandwidth",
        meterName="Standard Data Transfer Out",
        unitOfMeasure="1 GB",
        tierMinimumUnits=51200.0,
        retailPrice=0.07,
    ),
]

# NAT Gateway, only available under the Global region in this scenario.
NAT_GLOBAL_ITEMS = [
    _meter(
        serviceName="NAT Gateway",
        armRegionName="Global",
        location="",
        meterName="Standard Gateway Hours",
        unitOfMeasure="1 Hour",
        retailPrice=0.045,
    ),
    _meter(
        serviceName="NAT Gateway",
        armRegionName="Global",
        location="",
        meterName="Standard Data Processed",
        unitOfMeasure="1 GB",
        retailPrice=0.045,
    ),
]

# Two distinct Load Balancer rule meters -> ambiguous.
LB_AMBIGUOUS_ITEMS = [
    _meter(serviceName="Load Balancer", meterName="Standard Rule", retailPrice=0.025),
    _meter(serviceName="Load Balancer", meterName="Standard Overflow Rule", retailPrice=0.01),
]

# A single, confident Public IP meter.
PUBLIC_IP_ITEMS = [
    _meter(
        serviceName="Virtual Network",
        productName="IP Addresses",
        meterName="Standard IPv4 Static IP Address Hours",
        retailPrice=0.005,
    ),
]

# Private Link: one endpoint (hourly) meter + one data-processed meter.
PRIVATE_LINK_ITEMS = [
    _meter(
        serviceName="Private Link",
        meterName="Standard Endpoint",
        unitOfMeasure="1 Hour",
        retailPrice=0.01,
    ),
    _meter(
        serviceName="Private Link",
        meterName="Standard Data Processed",
        unitOfMeasure="1 GB",
        retailPrice=0.01,
    ),
]


def make_router(service_payloads: dict[str, dict[str, list[dict[str, Any]]]]):
    """Build a fetch_prices side_effect that routes on serviceName + region.

    ``service_payloads`` maps a serviceName substring to a dict with optional
    ``regional`` and ``global`` payload lists. Missing keys return no items.
    """

    def _fetch(
        filter_conditions: list[str] | None = None,
        currency_code: str = "USD",
        limit: int | None = None,
    ) -> dict[str, Any]:
        text = " ".join(filter_conditions or [])
        is_global = "armRegionName eq 'Global'" in text
        for needle, payloads in service_payloads.items():
            if needle in text:
                key = "global" if is_global else "regional"
                return {"Items": payloads.get(key, [])}
        return {"Items": []}

    return _fetch


@pytest.fixture
def service() -> NetworkCostService:
    return NetworkCostService(AzurePricingClient())


# ---------------------------------------------------------------------------
# Bandwidth / tiered pricing
# ---------------------------------------------------------------------------


class TestBandwidth:
    @pytest.mark.asyncio
    async def test_internet_egress_tiers_calculate_correctly(self, service):
        router = make_router({"Bandwidth": {"regional": EGRESS_ITEMS}})
        with patch.object(service._client, "fetch_prices", side_effect=router):
            result = await service.estimate_network_cost(
                source_region="eastus",
                destination_type="internet",
                monthly_data_gb=20000,
            )

        expected = 10240 * 0.087 + (20000 - 10240) * 0.083
        assert result["total_monthly_cost"] == pytest.approx(round(expected, 2))
        assert result["annualized_cost"] == pytest.approx(round(expected * 12, 2), rel=1e-4)

        assert len(result["priced_components"]) == 1
        assert result["priced_components"][0]["name"].startswith("Bandwidth")

        assert len(result["tiered_breakdown"]) == 1
        lines = result["tiered_breakdown"][0]["lines"]
        assert len(lines) == 2
        assert lines[0]["units_in_tier"] == pytest.approx(10240)
        assert lines[1]["units_in_tier"] == pytest.approx(20000 - 10240)

    @pytest.mark.asyncio
    async def test_no_data_means_no_bandwidth_component(self, service):
        router = make_router({"Bandwidth": {"regional": EGRESS_ITEMS}})
        with patch.object(service._client, "fetch_prices", side_effect=router):
            result = await service.estimate_network_cost(
                source_region="eastus", destination_type="internet", monthly_data_gb=0
            )
        assert result["priced_components"] == []
        assert result["total_monthly_cost"] == 0.0


# ---------------------------------------------------------------------------
# NAT Gateway global fallback
# ---------------------------------------------------------------------------


class TestNatGatewayGlobalFallback:
    @pytest.mark.asyncio
    async def test_falls_back_to_global_and_marks_it(self, service):
        # Regional NAT query returns nothing; Global query returns the meters.
        router = make_router({"NAT Gateway": {"regional": [], "global": NAT_GLOBAL_ITEMS}})
        with patch.object(service._client, "fetch_prices", side_effect=router):
            result = await service.estimate_network_cost(
                source_region="eastus",
                destination_type="internet",
                monthly_data_gb=1000,
                include_nat_gateway=True,
            )

        assert result["uses_global_pricing"] is True

        nat = next(c for c in result["priced_components"] if c["name"] == "NAT Gateway")
        assert nat["globally_priced"] is True

        # gateway hours + data processed, both at 0.045.
        expected = 0.045 * 730 + 0.045 * 1000
        assert nat["monthly_cost"] == pytest.approx(round(expected, 4))

        # Meters used must show the Global region.
        nat_meters = [m for m in result["meters_used"] if m["component"] == "NAT Gateway"]
        assert nat_meters
        assert all(m["globally_priced"] for m in nat_meters)
        assert all(m["region"] == "Global" for m in nat_meters)

        # A warning must clearly call out the Global fallback.
        assert any("Global" in w for w in result["warnings"])


# ---------------------------------------------------------------------------
# Ambiguous components -> unpriced
# ---------------------------------------------------------------------------


class TestAmbiguousComponents:
    @pytest.mark.asyncio
    async def test_ambiguous_load_balancer_is_unpriced(self, service):
        router = make_router({"Load Balancer": {"regional": LB_AMBIGUOUS_ITEMS}})
        with patch.object(service._client, "fetch_prices", side_effect=router):
            result = await service.estimate_network_cost(
                source_region="eastus",
                destination_type="internet",
                include_load_balancer=True,
            )

        names = [c["name"] for c in result["unpriced_components"]]
        assert "Load Balancer" in names
        # Nothing was priced, so it must not contribute to the total.
        assert result["total_monthly_cost"] == 0.0
        assert any("could not be priced" in w for w in result["warnings"])

    @pytest.mark.asyncio
    async def test_expressroute_data_is_unpriced(self, service):
        router = make_router({})
        with patch.object(service._client, "fetch_prices", side_effect=router):
            result = await service.estimate_network_cost(
                source_region="eastus",
                destination_type="expressroute",
                monthly_data_gb=5000,
            )
        names = [c["name"] for c in result["unpriced_components"]]
        assert any("ExpressRoute" in n for n in names)


# ---------------------------------------------------------------------------
# Confident match
# ---------------------------------------------------------------------------


class TestConfidentMatch:
    @pytest.mark.asyncio
    async def test_public_ip_priced_when_single_match(self, service):
        router = make_router({"Virtual Network": {"regional": PUBLIC_IP_ITEMS}})
        with patch.object(service._client, "fetch_prices", side_effect=router):
            result = await service.estimate_network_cost(
                source_region="eastus",
                destination_type="internet",
                gateway_hours=730,
                include_public_ip=True,
            )
        pip = next(c for c in result["priced_components"] if c["name"] == "Public IP address")
        assert pip["monthly_cost"] == pytest.approx(round(0.005 * 730, 4))


# ---------------------------------------------------------------------------
# Private Link
# ---------------------------------------------------------------------------


class TestPrivateLink:
    @pytest.mark.asyncio
    async def test_priced_when_destination_is_private_link(self, service):
        router = make_router({"Private Link": {"regional": PRIVATE_LINK_ITEMS}})
        with patch.object(service._client, "fetch_prices", side_effect=router):
            result = await service.estimate_network_cost(
                source_region="eastus",
                destination_type="private_link",
                monthly_data_gb=1000,
                gateway_hours=730,
            )
        priced = [c for c in result["priced_components"] if c["name"] == "Private Link"]
        assert len(priced) == 1
        expected = 0.01 * 730 + 0.01 * 1000
        assert priced[0]["monthly_cost"] == pytest.approx(round(expected, 4))

    @pytest.mark.asyncio
    async def test_priced_once_when_destination_and_flag_both_set(self, service):
        # Regression: destination_type="private_link" AND include_private_link=True
        # must still price Private Link exactly once (it was previously dropped).
        router = make_router({"Private Link": {"regional": PRIVATE_LINK_ITEMS}})
        with patch.object(service._client, "fetch_prices", side_effect=router):
            result = await service.estimate_network_cost(
                source_region="eastus",
                destination_type="private_link",
                monthly_data_gb=1000,
                gateway_hours=730,
                include_private_link=True,
            )
        priced = [c for c in result["priced_components"] if c["name"] == "Private Link"]
        assert len(priced) == 1  # exactly once: not dropped, not double-counted
        assert result["unpriced_components"] == []
        expected = 0.01 * 730 + 0.01 * 1000
        assert priced[0]["monthly_cost"] == pytest.approx(round(expected, 4))

    @pytest.mark.asyncio
    async def test_hourly_only_reports_hours_unit(self, service):
        # With no data, the endpoint-hours charge must report an "hours" unit,
        # not a misleading "0 GB".
        router = make_router({"Private Link": {"regional": PRIVATE_LINK_ITEMS}})
        with patch.object(service._client, "fetch_prices", side_effect=router):
            result = await service.estimate_network_cost(
                source_region="eastus",
                destination_type="private_link",
                monthly_data_gb=0,
                gateway_hours=730,
            )
        pl = next(c for c in result["priced_components"] if c["name"] == "Private Link")
        assert pl["unit"] == "hours"
        assert pl["quantity"] == pytest.approx(730)
        assert pl["monthly_cost"] == pytest.approx(round(0.01 * 730, 4))


# ---------------------------------------------------------------------------
# Validation, discount, formatter
# ---------------------------------------------------------------------------


class TestValidationAndDiscount:
    @pytest.mark.asyncio
    async def test_invalid_destination_type_errors(self, service):
        with patch.object(service._client, "fetch_prices", side_effect=make_router({})):
            result = await service.estimate_network_cost(source_region="eastus", destination_type="moon")
        assert "error" in result

    @pytest.mark.asyncio
    async def test_discount_not_applied_by_default(self, service):
        router = make_router({"Bandwidth": {"regional": EGRESS_ITEMS}})
        with patch.object(service._client, "fetch_prices", side_effect=router):
            result = await service.estimate_network_cost(
                source_region="eastus", destination_type="internet", monthly_data_gb=1000
            )
        assert "discount_applied" not in result
        assert result["total_monthly_cost"] == result["retail_monthly_cost"]

    @pytest.mark.asyncio
    async def test_discount_applied_when_provided(self, service):
        router = make_router({"Bandwidth": {"regional": EGRESS_ITEMS}})
        with patch.object(service._client, "fetch_prices", side_effect=router):
            result = await service.estimate_network_cost(
                source_region="eastus",
                destination_type="internet",
                monthly_data_gb=1000,
                discount_percentage=10.0,
            )
        assert "discount_applied" in result
        assert result["total_monthly_cost"] < result["retail_monthly_cost"]
        assert result["discount_applied"]["percentage"] == 10.0


class TestFormatter:
    def test_formatter_includes_all_sections(self):
        result = {
            "source_region": "eastus",
            "destination_type": "internet",
            "currency": "USD",
            "uses_global_pricing": True,
            "assumptions": ["Source region: eastus"],
            "priced_components": [
                {
                    "name": "Bandwidth - internet egress",
                    "detail": "graduated",
                    "quantity": 1000,
                    "unit": "GB",
                    "monthly_cost": 87.0,
                    "globally_priced": False,
                }
            ],
            "tiered_breakdown": [
                {
                    "component": "Bandwidth - internet egress",
                    "quantity": 1000,
                    "unit": "GB",
                    "total": 87.0,
                    "lines": [
                        {
                            "minimum_units": 0.0,
                            "upper_bound": 10240.0,
                            "units_in_tier": 1000,
                            "unit_price": 0.087,
                            "line_cost": 87.0,
                        }
                    ],
                }
            ],
            "unpriced_components": [{"name": "Load Balancer", "reason": "ambiguous"}],
            "meters_used": [
                {
                    "component": "Bandwidth - internet egress",
                    "meter_name": "Standard Data Transfer Out",
                    "sku_name": "Standard",
                    "region": "eastus",
                    "price_type": "Consumption",
                    "unit_price": 0.087,
                    "unit": "1 GB",
                    "globally_priced": False,
                }
            ],
            "warnings": ["1 component(s) could not be priced"],
            "retail_monthly_cost": 87.0,
            "total_monthly_cost": 87.0,
            "annualized_cost": 1044.0,
        }
        text = format_network_cost_estimate_response(result)
        for section in [
            "Assumptions",
            "Priced Components",
            "Tiered Breakdown",
            "Unpriced Components",
            "Total monthly cost",
            "Annualized cost",
            "Meters Used",
            "Warnings",
        ]:
            assert section in text

    def test_formatter_handles_error(self):
        text = format_network_cost_estimate_response({"error": "bad input"})
        assert "Error" in text
        assert "bad input" in text


# ---------------------------------------------------------------------------
# Registration & routing
# ---------------------------------------------------------------------------


class TestRegistrationAndRouting:
    def test_tool_is_registered(self):
        names = [t.name for t in get_tool_definitions()]
        assert "azure_network_cost_estimate" in names

    def test_tool_is_in_dispatch(self):
        assert _TOOL_DISPATCH["azure_network_cost_estimate"] == "handle_network_cost_estimate"

    def test_handler_method_exists(self):
        assert hasattr(ToolHandlers, "handle_network_cost_estimate")

    @pytest.mark.asyncio
    async def test_create_server_includes_tool(self):
        server, pricing_server = create_server()
        assert pricing_server is not None
        names = [t.name for t in get_tool_definitions()]
        assert "azure_network_cost_estimate" in names

    @pytest.mark.asyncio
    async def test_handler_routes_and_returns_textcontent(self, service):
        handlers = ToolHandlers(
            pricing_service=None,  # type: ignore[arg-type]
            sku_service=None,  # type: ignore[arg-type]
            network_service=service,
        )
        router = make_router({"Bandwidth": {"regional": EGRESS_ITEMS}})
        with patch.object(service._client, "fetch_prices", side_effect=router):
            result = await handlers.handle_network_cost_estimate(
                {"source_region": "eastus", "destination_type": "internet", "monthly_data_gb": 1000}
            )
        assert len(result) == 1
        assert isinstance(result[0], TextContent)
        assert "Azure Network Cost Estimate" in result[0].text
