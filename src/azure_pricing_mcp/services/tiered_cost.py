"""Tiered (graduated) pricing engine for the Azure Retail Prices API.

Several Azure meters - most notably bandwidth / internet egress - are billed
using *graduated* tiers. The API returns one row per tier for the same meter,
distinguished by ``tierMinimumUnits`` (the lower bound, in billing units, at
which that tier's price begins to apply). For example, internet egress may be
returned as::

    tierMinimumUnits=0       retailPrice=0.087   # first bracket
    tierMinimumUnits=10240   retailPrice=0.083   # next bracket (>= 10 TB)
    tierMinimumUnits=51200   retailPrice=0.070   # next bracket (>= 50 TB)

A quantity is billed by filling each bracket in turn: units that fall inside a
bracket are charged at that bracket's price. This module builds the tier
ladder from raw API rows and computes the graduated cost, returning a full
per-tier breakdown so nothing is hidden.

All functions are pure and free of I/O for easy unit testing.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from .meter_normalizer import NormalizedMeter, is_consumption, normalize_meter


@dataclass(frozen=True)
class PricingTier:
    """A single graduated price tier for one meter."""

    minimum_units: float
    unit_price: float
    meter_name: str
    unit_of_measure: str
    currency: str


@dataclass
class TierBreakdownLine:
    """The portion of a quantity that was billed within one tier."""

    minimum_units: float
    upper_bound: float | None
    units_in_tier: float
    unit_price: float
    line_cost: float


@dataclass
class TieredCostResult:
    """Result of a graduated tiered cost calculation."""

    quantity: float
    total_cost: float
    unit_of_measure: str
    currency: str
    breakdown: list[TierBreakdownLine] = field(default_factory=list)
    tiers_used: list[PricingTier] = field(default_factory=list)


def build_tiers(items: list[dict[str, Any]]) -> list[PricingTier]:
    """Build a sorted tier ladder from raw API items for a single meter.

    Only Consumption rows are considered (Reservation/Dev-Test rows are never
    part of an on-demand tier ladder). Rows are de-duplicated by
    ``tierMinimumUnits`` (keeping the first occurrence) and sorted ascending so
    they can be filled in order.

    Args:
        items: Raw API items that belong to the *same* meter.

    Returns:
        A list of :class:`PricingTier` sorted by ``minimum_units`` ascending.
    """
    tiers: dict[float, PricingTier] = {}
    for item in items:
        if not is_consumption(item):
            continue
        meter = normalize_meter(item)
        if meter.tier_minimum_units in tiers:
            continue
        tiers[meter.tier_minimum_units] = PricingTier(
            minimum_units=meter.tier_minimum_units,
            unit_price=meter.retail_price,
            meter_name=meter.meter_name,
            unit_of_measure=meter.unit_of_measure,
            currency=meter.currency,
        )
    return [tiers[key] for key in sorted(tiers)]


def build_tiers_from_meters(meters: list[NormalizedMeter]) -> list[PricingTier]:
    """Build a sorted tier ladder from already-normalised Consumption meters."""
    tiers: dict[float, PricingTier] = {}
    for meter in meters:
        if not meter.is_consumption:
            continue
        if meter.tier_minimum_units in tiers:
            continue
        tiers[meter.tier_minimum_units] = PricingTier(
            minimum_units=meter.tier_minimum_units,
            unit_price=meter.retail_price,
            meter_name=meter.meter_name,
            unit_of_measure=meter.unit_of_measure,
            currency=meter.currency,
        )
    return [tiers[key] for key in sorted(tiers)]


def calculate_tiered_cost(tiers: list[PricingTier], quantity: float) -> TieredCostResult:
    """Compute the graduated cost of ``quantity`` units across ``tiers``.

    Each tier ``i`` covers the half-open interval
    ``[minimum_units[i], minimum_units[i + 1])``; the final tier is unbounded.
    Units of the quantity that fall in a tier's interval are charged at that
    tier's ``unit_price``.

    Args:
        tiers: Tier ladder (need not be pre-sorted; it is sorted defensively).
        quantity: Number of billing units consumed (e.g. GB of egress).

    Returns:
        A :class:`TieredCostResult` with the total and a per-tier breakdown.
    """
    ordered = sorted(tiers, key=lambda tier: tier.minimum_units)

    unit = ordered[0].unit_of_measure if ordered else ""
    currency = ordered[0].currency if ordered else ""

    result = TieredCostResult(
        quantity=quantity,
        total_cost=0.0,
        unit_of_measure=unit,
        currency=currency,
        tiers_used=ordered,
    )

    if not ordered or quantity <= 0:
        return result

    total = 0.0
    for index, tier in enumerate(ordered):
        lower = tier.minimum_units
        if lower >= quantity:
            # This tier (and every later one) starts beyond what we consumed.
            break

        upper: float | None
        if index + 1 < len(ordered):
            upper = ordered[index + 1].minimum_units
            tier_top = min(quantity, upper)
        else:
            upper = None
            tier_top = quantity

        units_in_tier = tier_top - lower
        if units_in_tier <= 0:
            continue

        line_cost = units_in_tier * tier.unit_price
        total += line_cost
        result.breakdown.append(
            TierBreakdownLine(
                minimum_units=lower,
                upper_bound=upper,
                units_in_tier=units_in_tier,
                unit_price=tier.unit_price,
                line_cost=line_cost,
            )
        )

    result.total_cost = total
    return result
