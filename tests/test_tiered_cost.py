"""Tests for the tiered (graduated) pricing engine."""

import pytest

from azure_pricing_mcp.services.tiered_cost import (
    PricingTier,
    build_tiers,
    calculate_tiered_cost,
)


def _band_item(tier_min, price, **overrides):
    base = {
        "type": "Consumption",
        "retailPrice": price,
        "tierMinimumUnits": tier_min,
        "meterName": "Standard Data Transfer Out",
        "unitOfMeasure": "1 GB",
        "currencyCode": "USD",
        "armRegionName": "eastus",
    }
    base.update(overrides)
    return base


# Representative internet-egress tier ladder.
EGRESS_ITEMS = [
    _band_item(0.0, 0.087),
    _band_item(10240.0, 0.083),
    _band_item(51200.0, 0.07),
]


class TestBuildTiers:
    def test_sorts_ascending(self):
        tiers = build_tiers([EGRESS_ITEMS[2], EGRESS_ITEMS[0], EGRESS_ITEMS[1]])
        assert [t.minimum_units for t in tiers] == [0.0, 10240.0, 51200.0]

    def test_excludes_reservation_rows(self):
        items = EGRESS_ITEMS + [_band_item(0.0, 0.01, type="Reservation", meterName="Standard Data Transfer Out")]
        tiers = build_tiers(items)
        # The Reservation row shares tierMinimumUnits=0 but must be excluded;
        # the Consumption 0-tier price (0.087) must win.
        assert tiers[0].unit_price == 0.087

    def test_deduplicates_tier_minimum(self):
        items = [_band_item(0.0, 0.087), _band_item(0.0, 0.09)]
        tiers = build_tiers(items)
        assert len(tiers) == 1
        assert tiers[0].unit_price == 0.087  # first occurrence kept


class TestCalculateTieredCost:
    def test_single_tier(self):
        tiers = build_tiers(EGRESS_ITEMS)
        result = calculate_tiered_cost(tiers, 5000)
        assert result.total_cost == pytest.approx(5000 * 0.087)
        assert len(result.breakdown) == 1
        assert result.breakdown[0].units_in_tier == 5000

    def test_spans_two_tiers(self):
        tiers = build_tiers(EGRESS_ITEMS)
        result = calculate_tiered_cost(tiers, 20000)
        expected = 10240 * 0.087 + (20000 - 10240) * 0.083
        assert result.total_cost == pytest.approx(expected)
        assert len(result.breakdown) == 2
        assert result.breakdown[0].units_in_tier == 10240
        assert result.breakdown[1].units_in_tier == pytest.approx(20000 - 10240)

    def test_spans_three_tiers(self):
        tiers = build_tiers(EGRESS_ITEMS)
        result = calculate_tiered_cost(tiers, 60000)
        expected = 10240 * 0.087 + (51200 - 10240) * 0.083 + (60000 - 51200) * 0.07
        assert result.total_cost == pytest.approx(expected)
        assert len(result.breakdown) == 3

    def test_breakdown_sums_to_total(self):
        tiers = build_tiers(EGRESS_ITEMS)
        result = calculate_tiered_cost(tiers, 73000)
        assert sum(line.line_cost for line in result.breakdown) == pytest.approx(result.total_cost)

    def test_exact_tier_boundary(self):
        tiers = build_tiers(EGRESS_ITEMS)
        result = calculate_tiered_cost(tiers, 10240)
        assert result.total_cost == pytest.approx(10240 * 0.087)
        assert len(result.breakdown) == 1

    def test_zero_quantity(self):
        tiers = build_tiers(EGRESS_ITEMS)
        result = calculate_tiered_cost(tiers, 0)
        assert result.total_cost == 0.0
        assert result.breakdown == []

    def test_empty_tiers(self):
        result = calculate_tiered_cost([], 1000)
        assert result.total_cost == 0.0

    def test_unbounded_last_tier(self):
        single = [PricingTier(0.0, 0.05, "m", "1 GB", "USD")]
        result = calculate_tiered_cost(single, 1_000_000)
        assert result.total_cost == pytest.approx(1_000_000 * 0.05)
        assert result.breakdown[0].upper_bound is None
