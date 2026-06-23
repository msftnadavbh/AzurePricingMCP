"""Azure network cost estimation service.

Estimates the monthly cost of common Azure networking components from real-time
Azure Retail Prices API data, while strictly honouring the shared pricing
correctness rules:

* Only ``Consumption`` meters are ever used for on-demand estimates - a
  ``Reservation`` row is never mistaken for an hourly price.
* Bandwidth / internet egress is priced with the graduated tier engine using
  ``tierMinimumUnits``.
* Regional meters fall back to the special ``Global`` region only when no
  regional Consumption meter exists, and any result that relies on the fallback
  is clearly marked as globally priced.
* Components that cannot be matched to a single, unambiguous Consumption meter
  are surfaced as *unpriced* rather than silently dropped or guessed.

This service performs the I/O (via :class:`AzurePricingClient`) and delegates
all correctness logic to :mod:`meter_normalizer` and :mod:`tiered_cost`.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any

from ..client import AzurePricingClient
from .meter_normalizer import (
    GLOBAL_REGION,
    NormalizedMeter,
    filter_consumption,
    normalize_meters,
)
from .tiered_cost import build_tiers_from_meters, calculate_tiered_cost

logger = logging.getLogger(__name__)

VALID_DESTINATION_TYPES = (
    "internet",
    "same_region",
    "cross_region",
    "intercontinental",
    "private_link",
    "expressroute",
)

# Keyword rules used to confidently match a Bandwidth meter to a destination
# type. A meter matches when any ``include`` keyword appears in its combined
# name text and no ``exclude`` keyword does.
_BANDWIDTH_RULES: dict[str, dict[str, list[str]]] = {
    "internet": {
        "include": ["internet egress", "data transfer out"],
        "exclude": [
            "inter-region",
            "inter region",
            "intra-region",
            "intra region",
            "inter-continental",
            "intra-continental",
            "inter continent",
            "intra continent",
        ],
    },
    "cross_region": {
        "include": ["inter-region", "inter region", "intra continent", "intra-continent"],
        "exclude": ["inter-continental", "inter continent", "internet"],
    },
    "intercontinental": {
        "include": ["inter-continent", "inter continent", "inter-continental", "intercontinental"],
        "exclude": ["internet"],
    },
    "same_region": {
        "include": ["intra-region", "intra region", "availability zone", "same region"],
        "exclude": ["inter-region", "inter region", "internet"],
    },
}


@dataclass
class ComponentResult:
    """Outcome of pricing one networking component."""

    name: str
    priced: bool
    monthly_cost: float = 0.0
    quantity: float = 0.0
    unit: str = ""
    detail: str = ""
    meters: list[dict[str, Any]] | None = None
    tiered: dict[str, Any] | None = None
    reason: str = ""
    globally_priced: bool = False


class NetworkCostService:
    """Service that estimates Azure network costs from retail pricing."""

    def __init__(self, client: AzurePricingClient) -> None:
        self._client = client

    # ------------------------------------------------------------------
    # Low-level fetch helpers
    # ------------------------------------------------------------------
    async def _fetch_items(
        self,
        filter_conditions: list[str],
        currency_code: str,
        limit: int = 200,
    ) -> list[dict[str, Any]]:
        """Fetch raw pricing items for the given OData filter conditions."""
        data = await self._client.fetch_prices(
            filter_conditions=filter_conditions,
            currency_code=currency_code,
            limit=limit,
        )
        items = data.get("Items", [])
        return items if isinstance(items, list) else []

    async def _fetch_consumption_with_global_fallback(
        self,
        base_filters: list[str],
        region: str,
        currency_code: str,
    ) -> tuple[list[NormalizedMeter], bool]:
        """Fetch regional Consumption meters, falling back to ``Global``.

        Returns a tuple of ``(meters, used_global)`` where ``meters`` contains
        only Consumption rows and ``used_global`` is True if the regional query
        returned nothing and the ``Global`` region was used instead.
        """
        regional = await self._fetch_items(base_filters + [f"armRegionName eq '{region}'"], currency_code)
        regional_consumption = filter_consumption(regional)
        if regional_consumption:
            return normalize_meters(regional_consumption), False

        global_items = await self._fetch_items(base_filters + [f"armRegionName eq '{GLOBAL_REGION}'"], currency_code)
        return normalize_meters(filter_consumption(global_items)), True

    # ------------------------------------------------------------------
    # Matching helpers
    # ------------------------------------------------------------------
    @staticmethod
    def _meter_text(meter: NormalizedMeter) -> str:
        """Combined lower-cased searchable text for a meter."""
        return f"{meter.meter_name} {meter.product_name} {meter.sku_name}".casefold()

    @classmethod
    def _matches_rules(cls, meter: NormalizedMeter, include: list[str], exclude: list[str]) -> bool:
        text = cls._meter_text(meter)
        if any(token in text for token in exclude):
            return False
        return any(token in text for token in include)

    @staticmethod
    def _group_by_meter_name(meters: list[NormalizedMeter]) -> dict[str, list[NormalizedMeter]]:
        groups: dict[str, list[NormalizedMeter]] = {}
        for meter in meters:
            groups.setdefault(meter.meter_name, []).append(meter)
        return groups

    @staticmethod
    def _base_tier_meter(meters: list[NormalizedMeter]) -> NormalizedMeter:
        """Return the base-tier meter (lowest ``tierMinimumUnits``)."""
        return min(meters, key=lambda m: m.tier_minimum_units)

    def _meter_record(self, component: str, meter: NormalizedMeter, globally_priced: bool) -> dict[str, Any]:
        return {
            "component": component,
            "meter_name": meter.meter_name,
            "sku_name": meter.sku_name,
            "product_name": meter.product_name,
            "region": meter.region or GLOBAL_REGION,
            "price_type": meter.price_type,
            "unit_price": round(meter.retail_price, 6),
            "unit": meter.unit_of_measure,
            "globally_priced": globally_priced,
        }

    # ------------------------------------------------------------------
    # Component: bandwidth / egress
    # ------------------------------------------------------------------
    async def _price_bandwidth(
        self,
        destination_type: str,
        source_region: str,
        monthly_data_gb: float,
        currency_code: str,
    ) -> ComponentResult:
        name = f"Bandwidth - {destination_type.replace('_', ' ')} egress"

        if destination_type not in _BANDWIDTH_RULES:
            return ComponentResult(
                name=name,
                priced=False,
                quantity=monthly_data_gb,
                unit="GB",
                reason=(
                    f"Bandwidth pricing for destination type '{destination_type}' is not "
                    "covered by the v1 engine; data transfer left unpriced."
                ),
            )

        meters, used_global = await self._fetch_consumption_with_global_fallback(
            ["serviceName eq 'Bandwidth'"], source_region, currency_code
        )

        rule = _BANDWIDTH_RULES[destination_type]
        matched = [m for m in meters if self._matches_rules(m, rule["include"], rule["exclude"])]

        if not matched:
            return ComponentResult(
                name=name,
                priced=False,
                quantity=monthly_data_gb,
                unit="GB",
                reason="No confident Consumption bandwidth meter matched this destination type.",
            )

        groups = self._group_by_meter_name(matched)
        if len(groups) > 1:
            return ComponentResult(
                name=name,
                priced=False,
                quantity=monthly_data_gb,
                unit="GB",
                reason=(
                    "Multiple bandwidth meters matched ("
                    + ", ".join(sorted(groups)[:4])
                    + "); not priced to avoid guessing."
                ),
            )

        meter_group = next(iter(groups.values()))
        tiers = build_tiers_from_meters(meter_group)
        cost_result = calculate_tiered_cost(tiers, monthly_data_gb)
        base_meter = self._base_tier_meter(meter_group)

        tiered = {
            "component": name,
            "quantity": monthly_data_gb,
            "unit": "GB",
            "total": round(cost_result.total_cost, 4),
            "lines": [
                {
                    "minimum_units": line.minimum_units,
                    "upper_bound": line.upper_bound,
                    "units_in_tier": round(line.units_in_tier, 4),
                    "unit_price": round(line.unit_price, 6),
                    "line_cost": round(line.line_cost, 4),
                }
                for line in cost_result.breakdown
            ],
        }

        detail = "Graduated data-transfer-out pricing"
        if used_global:
            detail += " (globally priced)"

        return ComponentResult(
            name=name,
            priced=True,
            monthly_cost=cost_result.total_cost,
            quantity=monthly_data_gb,
            unit="GB",
            detail=detail,
            meters=[self._meter_record(name, base_meter, used_global)],
            tiered=tiered,
            globally_priced=used_global,
        )

    # ------------------------------------------------------------------
    # Component: NAT Gateway
    # ------------------------------------------------------------------
    async def _price_nat_gateway(
        self,
        source_region: str,
        gateway_hours: float,
        monthly_data_gb: float,
        currency_code: str,
    ) -> ComponentResult:
        name = "NAT Gateway"
        meters, used_global = await self._fetch_consumption_with_global_fallback(
            ["serviceName eq 'NAT Gateway'"], source_region, currency_code
        )

        if not meters:
            return ComponentResult(
                name=name,
                priced=False,
                reason="No Consumption NAT Gateway meter found in the region or globally.",
            )

        hourly_candidates = [
            m
            for m in meters
            if m.is_hourly and ("gateway" in m.meter_name.casefold() or "hour" in m.meter_name.casefold())
        ]
        data_candidates = [
            m
            for m in meters
            if "data processed" in m.meter_name.casefold() or m.unit_of_measure.casefold().endswith("gb")
        ]

        if not hourly_candidates and not data_candidates:
            return ComponentResult(
                name=name,
                priced=False,
                reason="NAT Gateway meters were found but neither an hourly nor a data-processed meter matched confidently.",
            )

        total = 0.0
        used_meters: list[dict[str, Any]] = []
        detail_parts: list[str] = []

        if hourly_candidates:
            hourly_meter = self._base_tier_meter(hourly_candidates)
            gateway_cost = hourly_meter.retail_price * gateway_hours
            total += gateway_cost
            used_meters.append(self._meter_record(name, hourly_meter, used_global))
            detail_parts.append(f"{gateway_hours:g} gateway-hours @ ${hourly_meter.retail_price:.4f}/hr")

        if data_candidates and monthly_data_gb > 0:
            data_meter = self._base_tier_meter(data_candidates)
            data_cost = data_meter.retail_price * monthly_data_gb
            total += data_cost
            used_meters.append(self._meter_record(name, data_meter, used_global))
            detail_parts.append(f"{monthly_data_gb:g} GB processed @ ${data_meter.retail_price:.4f}/GB")

        detail = "; ".join(detail_parts)
        if used_global:
            detail += " (globally priced)"

        # Report the dimension actually billed: GB when data was priced, else gateway-hours.
        has_data = bool(data_candidates) and monthly_data_gb > 0
        quantity, unit = (monthly_data_gb, "GB") if has_data else (gateway_hours, "hours")

        return ComponentResult(
            name=name,
            priced=True,
            monthly_cost=total,
            quantity=quantity,
            unit=unit,
            detail=detail,
            meters=used_meters,
            globally_priced=used_global,
        )

    # ------------------------------------------------------------------
    # Component: confident hourly match (Public IP / LB / App Gateway)
    # ------------------------------------------------------------------
    async def _price_confident_component(
        self,
        name: str,
        service_filters: list[str],
        source_region: str,
        gateway_hours: float,
        currency_code: str,
        include_keywords: list[str],
    ) -> ComponentResult:
        """Price a component only when a single hourly Consumption meter matches.

        Used for Public IP, Load Balancer and Application Gateway, which expose
        many SKUs/meters. If the match is ambiguous (more than one candidate
        meter) or empty, the component is returned as unpriced with a reason so
        it is surfaced rather than hidden.
        """
        meters, used_global = await self._fetch_consumption_with_global_fallback(
            service_filters, source_region, currency_code
        )

        if not meters:
            return ComponentResult(
                name=name,
                priced=False,
                reason="No Consumption meter found for this component in the region or globally.",
            )

        def matches(meter: NormalizedMeter) -> bool:
            text = self._meter_text(meter)
            return meter.is_hourly and any(token in text for token in include_keywords)

        candidates = [m for m in meters if matches(m)]
        groups = self._group_by_meter_name(candidates)

        if not groups:
            return ComponentResult(
                name=name,
                priced=False,
                reason="No confident hourly Consumption meter matched; left unpriced.",
            )

        if len(groups) > 1:
            return ComponentResult(
                name=name,
                priced=False,
                reason=(
                    "Multiple candidate meters matched ("
                    + ", ".join(sorted(groups)[:4])
                    + "); ambiguous, so left unpriced."
                ),
            )

        meter = self._base_tier_meter(next(iter(groups.values())))
        monthly_cost = meter.retail_price * gateway_hours
        detail = f"{gateway_hours:g} hours @ ${meter.retail_price:.4f}/hr"
        if used_global:
            detail += " (globally priced)"

        return ComponentResult(
            name=name,
            priced=True,
            monthly_cost=monthly_cost,
            quantity=gateway_hours,
            unit="hours",
            detail=detail,
            meters=[self._meter_record(name, meter, used_global)],
            globally_priced=used_global,
        )

    # ------------------------------------------------------------------
    # Component: Private Link
    # ------------------------------------------------------------------
    async def _price_private_link(
        self,
        source_region: str,
        gateway_hours: float,
        monthly_data_gb: float,
        currency_code: str,
    ) -> ComponentResult:
        name = "Private Link"
        meters, used_global = await self._fetch_consumption_with_global_fallback(
            ["serviceName eq 'Private Link'"], source_region, currency_code
        )

        if not meters:
            return ComponentResult(
                name=name,
                priced=False,
                reason="No Consumption Private Link meter found in the region or globally.",
            )

        hourly_candidates = [m for m in meters if m.is_hourly and "endpoint" in m.meter_name.casefold()]
        data_candidates = [m for m in meters if "data processed" in m.meter_name.casefold() and not m.is_hourly]

        if not hourly_candidates and not data_candidates:
            return ComponentResult(
                name=name,
                priced=False,
                reason="Private Link meters found but no confident endpoint or data-processed meter matched.",
            )

        # Ambiguity guard: distinct endpoint meters mean we cannot pick one.
        if len({m.meter_name for m in hourly_candidates}) > 1:
            return ComponentResult(
                name=name,
                priced=False,
                reason="Multiple Private Link endpoint meters matched; ambiguous, so left unpriced.",
            )

        total = 0.0
        used_meters: list[dict[str, Any]] = []
        detail_parts: list[str] = []

        if hourly_candidates:
            endpoint_meter = self._base_tier_meter(hourly_candidates)
            endpoint_cost = endpoint_meter.retail_price * gateway_hours
            total += endpoint_cost
            used_meters.append(self._meter_record(name, endpoint_meter, used_global))
            detail_parts.append(f"{gateway_hours:g} endpoint-hours @ ${endpoint_meter.retail_price:.4f}/hr")

        if data_candidates and monthly_data_gb > 0:
            data_meter = self._base_tier_meter(data_candidates)
            data_cost = data_meter.retail_price * monthly_data_gb
            total += data_cost
            used_meters.append(self._meter_record(name, data_meter, used_global))
            detail_parts.append(f"{monthly_data_gb:g} GB processed @ ${data_meter.retail_price:.4f}/GB")

        detail = "; ".join(detail_parts)
        if used_global:
            detail += " (globally priced)"

        # Report the dimension actually billed: GB when data was priced, else endpoint-hours.
        has_data = bool(data_candidates) and monthly_data_gb > 0
        quantity, unit = (monthly_data_gb, "GB") if has_data else (gateway_hours, "hours")

        return ComponentResult(
            name=name,
            priced=True,
            monthly_cost=total,
            quantity=quantity,
            unit=unit,
            detail=detail,
            meters=used_meters,
            globally_priced=used_global,
        )

    # ------------------------------------------------------------------
    # Orchestration
    # ------------------------------------------------------------------
    async def estimate_network_cost(
        self,
        source_region: str,
        destination_region: str | None = None,
        destination_type: str = "internet",
        monthly_data_gb: float = 0.0,
        gateway_hours: float = 730.0,
        include_nat_gateway: bool = False,
        include_public_ip: bool = False,
        include_load_balancer: bool = False,
        include_private_link: bool = False,
        include_application_gateway: bool = False,
        currency_code: str = "USD",
        discount_percentage: float | None = None,
    ) -> dict[str, Any]:
        """Estimate the monthly cost of an Azure networking topology.

        See the tool definition for parameter semantics. Returns a structured
        dict consumed by :func:`format_network_cost_estimate_response`.
        """
        destination_type = (destination_type or "internet").strip().lower()
        if destination_type not in VALID_DESTINATION_TYPES:
            return {
                "error": (
                    f"Invalid destination_type '{destination_type}'. "
                    f"Valid values: {', '.join(VALID_DESTINATION_TYPES)}."
                ),
                "source_region": source_region,
                "destination_type": destination_type,
            }

        assumptions: list[str] = [
            f"Source region: {source_region}",
            f"Destination type: {destination_type}",
            f"Monthly data transfer: {monthly_data_gb:g} GB",
            f"Gateway / hourly resource runtime: {gateway_hours:g} hours/month",
            "Prices are pay-as-you-go Consumption rates; Reservation rows are excluded.",
        ]
        if destination_region:
            assumptions.append(f"Destination region: {destination_region}")

        warnings: list[str] = []
        priced_components: list[dict[str, Any]] = []
        unpriced_components: list[dict[str, Any]] = []
        tiered_breakdown: list[dict[str, Any]] = []
        meters_used: list[dict[str, Any]] = []

        components: list[ComponentResult] = []

        # --- Bandwidth / data transfer ---
        if monthly_data_gb > 0:
            if destination_type == "private_link":
                assumptions.append("Data transfer for 'private_link' is priced via the Private Link component below.")
            elif destination_type == "expressroute":
                components.append(
                    ComponentResult(
                        name="ExpressRoute data transfer",
                        priced=False,
                        quantity=monthly_data_gb,
                        unit="GB",
                        reason=(
                            "ExpressRoute pricing (circuit port + metered/unlimited data) is not "
                            "covered by the v1 engine; left unpriced."
                        ),
                    )
                )
            else:
                components.append(
                    await self._price_bandwidth(destination_type, source_region, monthly_data_gb, currency_code)
                )
        else:
            assumptions.append("monthly_data_gb is 0, so data-transfer charges are not estimated.")

        # --- NAT Gateway ---
        if include_nat_gateway:
            components.append(
                await self._price_nat_gateway(source_region, gateway_hours, monthly_data_gb, currency_code)
            )

        # --- Public IP ---
        if include_public_ip:
            components.append(
                await self._price_confident_component(
                    "Public IP address",
                    ["serviceName eq 'Virtual Network'", "contains(meterName, 'IP')"],
                    source_region,
                    gateway_hours,
                    currency_code,
                    include_keywords=["ip address", "public ip"],
                )
            )

        # --- Load Balancer ---
        if include_load_balancer:
            components.append(
                await self._price_confident_component(
                    "Load Balancer",
                    ["serviceName eq 'Load Balancer'"],
                    source_region,
                    gateway_hours,
                    currency_code,
                    include_keywords=["rule", "gateway lb", "load balancer"],
                )
            )

        # --- Private Link ---
        # Price exactly once when the destination is Private Link or the flag is
        # set, so the destination_type and flag paths can never silently cancel
        # each other out (or double-count).
        if destination_type == "private_link" or include_private_link:
            components.append(
                await self._price_private_link(source_region, gateway_hours, monthly_data_gb, currency_code)
            )

        # --- Application Gateway ---
        if include_application_gateway:
            components.append(
                await self._price_confident_component(
                    "Application Gateway",
                    ["serviceName eq 'Application Gateway'"],
                    source_region,
                    gateway_hours,
                    currency_code,
                    include_keywords=["gateway hour", "fixed", "capacity unit"],
                )
            )

        # --- Assemble ---
        retail_total = 0.0
        any_global = False
        for component in components:
            if component.meters:
                meters_used.extend(component.meters)
            if component.priced:
                retail_total += component.monthly_cost
                priced_components.append(
                    {
                        "name": component.name,
                        "detail": component.detail,
                        "quantity": round(component.quantity, 4),
                        "unit": component.unit,
                        "monthly_cost": round(component.monthly_cost, 4),
                        "globally_priced": component.globally_priced,
                    }
                )
                if component.tiered:
                    tiered_breakdown.append(component.tiered)
                if component.globally_priced:
                    any_global = True
                    warnings.append(
                        f"{component.name}: no regional Consumption meter found; " "used Global pricing instead."
                    )
            else:
                unpriced_components.append({"name": component.name, "reason": component.reason})

        if not components:
            warnings.append("No components were selected. Set monthly_data_gb > 0 and/or enable a component flag.")

        if unpriced_components:
            warnings.append(
                f"{len(unpriced_components)} component(s) could not be priced and are listed separately. "
                "Their cost is NOT included in the total."
            )

        result: dict[str, Any] = {
            "source_region": source_region,
            "destination_region": destination_region,
            "destination_type": destination_type,
            "currency": currency_code,
            "assumptions": assumptions,
            "priced_components": priced_components,
            "tiered_breakdown": tiered_breakdown,
            "unpriced_components": unpriced_components,
            "meters_used": meters_used,
            "warnings": warnings,
            "uses_global_pricing": any_global,
        }

        # --- Discount (only when explicitly provided) ---
        monthly_total = retail_total
        if discount_percentage is not None and discount_percentage > 0:
            discount_amount = retail_total * (discount_percentage / 100.0)
            monthly_total = retail_total - discount_amount
            result["discount_applied"] = {
                "percentage": discount_percentage,
                "retail_monthly_cost": round(retail_total, 2),
                "discount_amount": round(discount_amount, 2),
                "note": "Discount applied to the priced subtotal only.",
            }

        result["retail_monthly_cost"] = round(retail_total, 2)
        result["total_monthly_cost"] = round(monthly_total, 2)
        result["annualized_cost"] = round(monthly_total * 12, 2)

        return result
