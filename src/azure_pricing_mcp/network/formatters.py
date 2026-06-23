"""Response formatter for the Azure network cost planner tool."""

from __future__ import annotations

from typing import Any


def _format_tier_bound(value: float | None) -> str:
    """Render a tier upper bound (``None`` means unbounded)."""
    if value is None:
        return "+"
    return f"{value:g}"


def format_network_cost_estimate_response(result: dict[str, Any]) -> str:
    """Format the network cost estimate result as Markdown."""
    if "error" in result:
        return f"### Azure Network Cost Estimate\n\n**Error:** {result['error']}"

    currency = result.get("currency", "USD")
    lines: list[str] = ["## Azure Network Cost Estimate", ""]

    lines.append(f"**Source region:** {result.get('source_region', 'N/A')}")
    if result.get("destination_region"):
        lines.append(f"**Destination region:** {result['destination_region']}")
    lines.append(f"**Destination type:** {result.get('destination_type', 'N/A')}")
    lines.append(f"**Currency:** {currency}")
    if result.get("uses_global_pricing"):
        lines.append("**Note:** Some components use Global pricing (see warnings).")
    lines.append("")

    # --- Assumptions ---
    assumptions = result.get("assumptions", [])
    if assumptions:
        lines.append("### Assumptions")
        for item in assumptions:
            lines.append(f"- {item}")
        lines.append("")

    # --- Priced components ---
    priced = result.get("priced_components", [])
    lines.append("### Priced Components")
    if priced:
        lines.append("| Component | Detail | Qty | Unit | Monthly Cost |")
        lines.append("|-----------|--------|-----|------|--------------|")
        for comp in priced:
            flag = " (global)" if comp.get("globally_priced") else ""
            lines.append(
                f"| {comp['name']}{flag} | {comp.get('detail', '')} | {comp.get('quantity', 0):g} | "
                f"{comp.get('unit', '')} | {currency} {comp.get('monthly_cost', 0):,.2f} |"
            )
    else:
        lines.append("_No components were priced._")
    lines.append("")

    # --- Tiered breakdown ---
    tiered = result.get("tiered_breakdown", [])
    if tiered:
        lines.append("### Tiered Breakdown")
        for entry in tiered:
            lines.append(f"**{entry['component']}** - {entry.get('quantity', 0):g} {entry.get('unit', '')}")
            lines.append("")
            lines.append("| Tier (from units) | Up to | Units | Unit Price | Line Cost |")
            lines.append("|-------------------|-------|-------|------------|-----------|")
            for line in entry.get("lines", []):
                lines.append(
                    f"| {line['minimum_units']:g} | {_format_tier_bound(line.get('upper_bound'))} | "
                    f"{line['units_in_tier']:g} | {currency} {line['unit_price']:.6f} | "
                    f"{currency} {line['line_cost']:,.2f} |"
                )
            lines.append(f"_Subtotal: {currency} {entry.get('total', 0):,.2f}_")
            lines.append("")

    # --- Unpriced components ---
    unpriced = result.get("unpriced_components", [])
    if unpriced:
        lines.append("### Unpriced Components")
        lines.append(
            "_These are NOT included in the total. They could not be matched to a single, unambiguous Consumption meter._"
        )
        lines.append("")
        for comp in unpriced:
            lines.append(f"- **{comp['name']}** - {comp.get('reason', 'No confident match.')}")
        lines.append("")

    # --- Totals ---
    lines.append("### Total")
    discount = result.get("discount_applied")
    if discount:
        lines.append(f"- Retail monthly subtotal: {currency} {discount['retail_monthly_cost']:,.2f}")
        lines.append(f"- Discount ({discount['percentage']:g}%): -{currency} {discount['discount_amount']:,.2f}")
    lines.append(f"- **Total monthly cost: {currency} {result.get('total_monthly_cost', 0):,.2f}**")
    lines.append(f"- **Annualized cost: {currency} {result.get('annualized_cost', 0):,.2f}**")
    lines.append("")

    # --- Meters used ---
    meters = result.get("meters_used", [])
    if meters:
        lines.append("### Meters Used")
        lines.append("| Component | Meter | SKU | Region | Price Type | Unit Price | Unit |")
        lines.append("|-----------|-------|-----|--------|------------|------------|------|")
        for meter in meters:
            global_flag = " (global)" if meter.get("globally_priced") else ""
            lines.append(
                f"| {meter.get('component', '')} | {meter.get('meter_name', '')} | "
                f"{meter.get('sku_name', '')} | {meter.get('region', '')}{global_flag} | "
                f"{meter.get('price_type', '')} | {currency} {meter.get('unit_price', 0):.6f} | "
                f"{meter.get('unit', '')} |"
            )
        lines.append("")

    # --- Warnings ---
    warnings = result.get("warnings", [])
    if warnings:
        lines.append("### Warnings")
        for warning in warnings:
            lines.append(f"- {warning}")
        lines.append("")

    return "\n".join(lines).rstrip() + "\n"
