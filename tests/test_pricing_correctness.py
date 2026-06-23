"""Tests for the Consumption-vs-Reservation correctness fixes in PricingService.

These cover the two historical bugs:

* ``estimate_costs`` used to take the first returned row blindly, which could be
  a Reservation row whose ``retailPrice`` is a term total rather than an hourly
  rate.
* ``recommend_regions`` never filtered by price type, so Reservation rows could
  corrupt the "cheapest region" ranking.
"""

from typing import Any
from unittest.mock import AsyncMock, patch

import pytest

from azure_pricing_mcp.client import AzurePricingClient
from azure_pricing_mcp.services import PricingService
from azure_pricing_mcp.services.retirement import RetirementService


@pytest.fixture
def pricing_service() -> PricingService:
    client = AzurePricingClient()
    retirement = AsyncMock(spec=RetirementService)
    retirement.check_skus_retirement_status.return_value = []
    return PricingService(client, retirement)


def _row(price_type: str, region: str, price: float, **overrides: Any) -> dict[str, Any]:
    base = {
        "type": price_type,
        "armRegionName": region,
        "location": region.upper(),
        "retailPrice": price,
        "skuName": "D4s v3",
        "meterName": "D4s v3",
        "productName": "Virtual Machines Dsv3 Series",
        "serviceName": "Virtual Machines",
        "unitOfMeasure": "1 Hour",
    }
    base.update(overrides)
    return base


class TestEstimateCostsIgnoresReservation:
    @pytest.mark.asyncio
    async def test_reservation_hourly_row_is_ignored(self, pricing_service):
        """A Reservation row with unitOfMeasure='1 Hour' must not be used."""
        items = [
            _row("Reservation", "eastus", 0.05, reservationTerm="3 Years"),
            _row("Consumption", "eastus", 0.192),
        ]
        with patch.object(pricing_service._client, "fetch_prices", return_value={"Items": items}):
            result = await pricing_service.estimate_costs("Virtual Machines", "D4s v3", "eastus")

        assert "error" not in result
        assert result["on_demand_pricing"]["hourly_rate"] == 0.192
        assert result["on_demand_pricing"]["monthly_cost"] == pytest.approx(0.192 * 730)

    @pytest.mark.asyncio
    async def test_error_when_only_reservation_rows(self, pricing_service):
        items = [_row("Reservation", "eastus", 0.05, reservationTerm="3 Years")]
        with patch.object(pricing_service._client, "fetch_prices", return_value={"Items": items}):
            result = await pricing_service.estimate_costs("Virtual Machines", "D4s v3", "eastus")

        assert "error" in result
        assert "Consumption" in result["error"]


class TestRecommendRegionsFiltersConsumption:
    @pytest.mark.asyncio
    async def test_reservation_rows_excluded_from_ranking(self, pricing_service):
        items = [
            _row("Consumption", "eastus", 0.192),
            # A cheap-looking Reservation row in eastus that must NOT win.
            _row("Reservation", "eastus", 0.05, reservationTerm="3 Years"),
            _row("Consumption", "westus", 0.21),
        ]
        with patch.object(pricing_service._client, "fetch_prices", return_value={"Items": items}):
            result = await pricing_service.recommend_regions("Virtual Machines", "D4s v3")

        assert result["price_type_filter"] == "Consumption"
        assert result["excluded_non_consumption_rows"] == 1

        cheapest = result["recommendations"][0]
        assert cheapest["region"] == "eastus"
        # The Consumption price wins, not the 0.05 Reservation row.
        assert cheapest["retail_price"] == 0.192
