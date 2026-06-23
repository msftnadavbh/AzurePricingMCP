"""Shared pricing-correctness foundation for the Azure Retail Prices API.

The Azure Retail Prices API returns rows ("meters") that mix several
``priceType`` values (``Consumption``, ``Reservation``, ``DevTestConsumption``),
multiple regions (including the special ``Global`` region), and multiple
graduated price tiers (distinguished by ``tierMinimumUnits``).

Historically the pricing code read ``retailPrice`` from the *first* row it
found, which silently treated ``Reservation`` rows (whose ``retailPrice`` is a
total/term price, not an hourly Consumption rate) as if they were hourly
on-demand prices. This module centralises the rules that every estimator must
follow so that mistake cannot be repeated:

* Never treat ``priceType == "Reservation"`` as hourly Consumption.
* Read the price type from ``type`` first, then fall back to ``priceType``
  (different API responses and fixtures use one or the other).
* Treat ``armRegionName == "Global"`` (or an empty region) as global pricing
  and mark any result that relies on it.
* Preserve ``tierMinimumUnits`` so tiered pricing can be computed correctly.

All helpers here are pure functions / dataclasses with no I/O so they are cheap
to unit test in isolation.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any

logger = logging.getLogger(__name__)

# Canonical priceType values returned by the Azure Retail Prices API.
PRICE_TYPE_CONSUMPTION = "Consumption"
PRICE_TYPE_RESERVATION = "Reservation"
PRICE_TYPE_DEVTEST = "DevTestConsumption"

# The special region name Azure uses for meters that are not regionalised.
GLOBAL_REGION = "Global"


def get_price_type(item: dict[str, Any]) -> str:
    """Return the normalised priceType for a raw API item.

    The Azure Retail Prices API exposes the price type as ``type`` in the
    response body, but the OData filter property is ``priceType`` and some
    fixtures/older payloads use ``priceType`` in the body too. Read both so we
    are robust to either shape.

    Args:
        item: A raw pricing item from the API ``Items`` array.

    Returns:
        The price type string (e.g. ``"Consumption"``). Empty string if absent.
    """
    raw = item.get("type")
    if raw is None:
        raw = item.get("priceType")
    if raw is None:
        return ""
    return str(raw).strip()


def is_consumption(item: dict[str, Any]) -> bool:
    """Return True if the item is a pay-as-you-go Consumption meter.

    ``DevTestConsumption`` is intentionally excluded: it is a discounted
    pay-as-you-go variant only available to Dev/Test subscriptions and must not
    be used for standard cost estimates.
    """
    return get_price_type(item) == PRICE_TYPE_CONSUMPTION


def is_reservation(item: dict[str, Any]) -> bool:
    """Return True if the item is a Reservation meter.

    Reservation ``retailPrice`` values are term totals or amortised rates and
    must never be treated as hourly Consumption prices.
    """
    return get_price_type(item) == PRICE_TYPE_RESERVATION


def get_region(item: dict[str, Any]) -> str:
    """Return the ARM region name for an item (may be empty)."""
    region = item.get("armRegionName")
    return str(region).strip() if region else ""


def is_global(item: dict[str, Any]) -> bool:
    """Return True if the item is priced globally rather than regionally.

    Azure marks non-regionalised meters with ``armRegionName == "Global"``.
    Items with no region at all are also treated as global so a missing region
    can never masquerade as a regional price.
    """
    region = get_region(item)
    return region == "" or region.casefold() == GLOBAL_REGION.casefold()


def get_unit_of_measure(item: dict[str, Any]) -> str:
    """Return the unit of measure string (e.g. ``"1 Hour"``, ``"1 GB"``)."""
    unit = item.get("unitOfMeasure")
    return str(unit).strip() if unit else ""


def is_hourly(item: dict[str, Any]) -> bool:
    """Return True if the meter is billed per hour."""
    return "hour" in get_unit_of_measure(item).casefold()


def get_tier_minimum_units(item: dict[str, Any]) -> float:
    """Return ``tierMinimumUnits`` for an item, defaulting to 0.0.

    This is the lower bound (in billing units) at which a graduated price tier
    starts to apply.
    """
    raw = item.get("tierMinimumUnits", 0.0)
    try:
        return float(raw)
    except (TypeError, ValueError):
        return 0.0


def get_retail_price(item: dict[str, Any]) -> float:
    """Return ``retailPrice`` for an item, defaulting to 0.0."""
    raw = item.get("retailPrice", 0.0)
    try:
        return float(raw)
    except (TypeError, ValueError):
        return 0.0


@dataclass(frozen=True)
class NormalizedMeter:
    """A normalised view of a single Azure Retail Prices meter.

    Wrapping raw items in this dataclass keeps the correctness rules (price
    type, global pricing, tier bounds) in one place and makes downstream
    estimators easier to read and test.
    """

    meter_name: str
    sku_name: str
    product_name: str
    service_name: str
    service_family: str
    price_type: str
    retail_price: float
    unit_of_measure: str
    region: str
    location: str
    tier_minimum_units: float
    is_global: bool
    currency: str
    raw: dict[str, Any]

    @property
    def is_consumption(self) -> bool:
        """True if this meter is a pay-as-you-go Consumption meter."""
        return self.price_type == PRICE_TYPE_CONSUMPTION

    @property
    def is_reservation(self) -> bool:
        """True if this meter is a Reservation meter."""
        return self.price_type == PRICE_TYPE_RESERVATION

    @property
    def is_hourly(self) -> bool:
        """True if this meter is billed per hour."""
        return "hour" in self.unit_of_measure.casefold()


def normalize_meter(item: dict[str, Any]) -> NormalizedMeter:
    """Build a :class:`NormalizedMeter` from a raw API item."""
    return NormalizedMeter(
        meter_name=str(item.get("meterName", "") or ""),
        sku_name=str(item.get("skuName", "") or ""),
        product_name=str(item.get("productName", "") or ""),
        service_name=str(item.get("serviceName", "") or ""),
        service_family=str(item.get("serviceFamily", "") or ""),
        price_type=get_price_type(item),
        retail_price=get_retail_price(item),
        unit_of_measure=get_unit_of_measure(item),
        region=get_region(item),
        location=str(item.get("location", "") or ""),
        tier_minimum_units=get_tier_minimum_units(item),
        is_global=is_global(item),
        currency=str(item.get("currencyCode", "") or ""),
        raw=item,
    )


def normalize_meters(items: list[dict[str, Any]]) -> list[NormalizedMeter]:
    """Normalise a list of raw API items."""
    return [normalize_meter(item) for item in items]


def filter_consumption(items: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Return only the Consumption rows from a list of raw API items.

    This is the single guard that keeps Reservation (and Dev/Test) rows out of
    on-demand cost estimates.
    """
    return [item for item in items if is_consumption(item)]


def select_consumption_meter(
    items: list[dict[str, Any]],
    *,
    sku_name: str | None = None,
    require_hourly: bool = False,
) -> NormalizedMeter | None:
    """Select the best Consumption meter from a set of raw API items.

    This replaces the previous "use the first row" behaviour. Reservation and
    Dev/Test rows are excluded outright; among the remaining Consumption rows we
    prefer, in order:

    1. an exact case-insensitive ``skuName`` match when ``sku_name`` is given,
    2. hourly meters over non-hourly ones,
    3. the base price tier (lowest ``tierMinimumUnits``),
    4. the lowest ``retailPrice`` as a final tie-breaker.

    ``require_hourly`` is a separate eligibility filter, not a sort preference:
    when set, non-hourly meters are excluded entirely before ranking.

    Args:
        items: Raw API items.
        sku_name: Optional SKU name to prefer an exact match for.
        require_hourly: If True, only hourly Consumption meters are eligible.

    Returns:
        The selected :class:`NormalizedMeter`, or ``None`` if no eligible
        Consumption meter exists.
    """
    candidates = [normalize_meter(item) for item in items if is_consumption(item)]

    if require_hourly:
        candidates = [meter for meter in candidates if meter.is_hourly]

    if not candidates:
        return None

    wanted_sku = sku_name.strip().casefold() if sku_name else None

    def sort_key(meter: NormalizedMeter) -> tuple[int, int, float, float]:
        exact_sku = 0 if wanted_sku and meter.sku_name.casefold() == wanted_sku else 1
        hourly_rank = 0 if meter.is_hourly else 1
        return (exact_sku, hourly_rank, meter.tier_minimum_units, meter.retail_price)

    candidates.sort(key=sort_key)
    return candidates[0]
