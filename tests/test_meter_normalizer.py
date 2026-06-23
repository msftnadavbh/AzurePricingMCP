"""Tests for the shared pricing-correctness foundation (meter_normalizer)."""

from azure_pricing_mcp.services.meter_normalizer import (
    PRICE_TYPE_CONSUMPTION,
    PRICE_TYPE_RESERVATION,
    filter_consumption,
    get_price_type,
    get_tier_minimum_units,
    is_consumption,
    is_global,
    is_reservation,
    normalize_meter,
    select_consumption_meter,
)


def _item(**overrides):
    base = {
        "type": "Consumption",
        "retailPrice": 0.1,
        "armRegionName": "eastus",
        "location": "US East",
        "skuName": "D4s v3",
        "meterName": "D4s v3",
        "productName": "Virtual Machines Dsv3 Series",
        "serviceName": "Virtual Machines",
        "serviceFamily": "Compute",
        "unitOfMeasure": "1 Hour",
        "tierMinimumUnits": 0.0,
        "currencyCode": "USD",
    }
    base.update(overrides)
    return base


class TestPriceType:
    def test_reads_type_field(self):
        assert get_price_type({"type": "Consumption"}) == "Consumption"

    def test_falls_back_to_pricetype_field(self):
        # Some API payloads / fixtures use ``priceType`` instead of ``type``.
        assert get_price_type({"priceType": "Reservation"}) == "Reservation"

    def test_type_takes_precedence_over_pricetype(self):
        assert get_price_type({"type": "Consumption", "priceType": "Reservation"}) == "Consumption"

    def test_missing_returns_empty(self):
        assert get_price_type({}) == ""

    def test_is_consumption_and_reservation(self):
        assert is_consumption(_item(type="Consumption"))
        assert not is_consumption(_item(type="Reservation"))
        assert is_reservation(_item(type="Reservation"))
        # DevTestConsumption is neither standard Consumption nor Reservation.
        assert not is_consumption(_item(type="DevTestConsumption"))
        assert not is_reservation(_item(type="DevTestConsumption"))


class TestGlobal:
    def test_global_region(self):
        assert is_global(_item(armRegionName="Global"))

    def test_empty_region_is_global(self):
        assert is_global(_item(armRegionName=""))
        assert is_global({"meterName": "x"})

    def test_regional_is_not_global(self):
        assert not is_global(_item(armRegionName="eastus"))


class TestTierMinimumUnits:
    def test_reads_value(self):
        assert get_tier_minimum_units(_item(tierMinimumUnits=10240.0)) == 10240.0

    def test_defaults_to_zero(self):
        assert get_tier_minimum_units({}) == 0.0

    def test_handles_bad_value(self):
        assert get_tier_minimum_units({"tierMinimumUnits": "oops"}) == 0.0


class TestFilterConsumption:
    def test_excludes_reservation_and_devtest(self):
        items = [
            _item(type="Consumption", retailPrice=0.19),
            _item(type="Reservation", retailPrice=0.05),
            _item(type="DevTestConsumption", retailPrice=0.10),
        ]
        result = filter_consumption(items)
        assert len(result) == 1
        assert result[0]["retailPrice"] == 0.19


class TestSelectConsumptionMeter:
    def test_reservation_hourly_row_is_ignored(self):
        """A Reservation row with unitOfMeasure='1 Hour' must NOT be selected."""
        items = [
            # Reservation row that *looks* hourly but is a term total.
            _item(type="Reservation", unitOfMeasure="1 Hour", retailPrice=0.05),
            # The real pay-as-you-go hourly rate.
            _item(type="Consumption", unitOfMeasure="1 Hour", retailPrice=0.192),
        ]
        selected = select_consumption_meter(items)
        assert selected is not None
        assert selected.price_type == PRICE_TYPE_CONSUMPTION
        assert selected.retail_price == 0.192

    def test_returns_none_when_only_reservation(self):
        items = [_item(type="Reservation", retailPrice=0.05)]
        assert select_consumption_meter(items) is None

    def test_prefers_exact_sku_match(self):
        items = [
            _item(skuName="D4s v3 Low Priority", retailPrice=0.05),
            _item(skuName="D4s v3", retailPrice=0.19),
        ]
        selected = select_consumption_meter(items, sku_name="D4s v3")
        assert selected is not None
        assert selected.sku_name == "D4s v3"

    def test_prefers_base_tier(self):
        items = [
            _item(tierMinimumUnits=1024.0, retailPrice=0.08),
            _item(tierMinimumUnits=0.0, retailPrice=0.087),
        ]
        selected = select_consumption_meter(items)
        assert selected is not None
        assert selected.tier_minimum_units == 0.0

    def test_require_hourly_excludes_non_hourly(self):
        items = [
            _item(unitOfMeasure="1 GB", retailPrice=0.05),
        ]
        assert select_consumption_meter(items, require_hourly=True) is None


class TestNormalizeMeter:
    def test_fields(self):
        meter = normalize_meter(
            _item(
                type="Reservation",
                armRegionName="Global",
                retailPrice=1.5,
                tierMinimumUnits=100.0,
            )
        )
        assert meter.price_type == PRICE_TYPE_RESERVATION
        assert meter.is_reservation
        assert meter.is_global
        assert meter.retail_price == 1.5
        assert meter.tier_minimum_units == 100.0
        assert meter.is_hourly
