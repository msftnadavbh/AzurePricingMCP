# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [3.1.0] - 2025-01-XX

### Changed

- **No default discount applied**: Pricing queries no longer automatically apply a 10% discount. By default, prices are shown at full retail price without any discount.
- **New `show_with_discount` parameter**: Added to `azure_price_search`, `azure_price_compare`, `azure_cost_estimate`, and `azure_region_recommend` tools. When set to `true` (without specifying `discount_percentage`), applies the default 10% discount.
- **Improved discount guidance**: Added helpful tip messages in responses:
  - When no discount is applied: Prompts user about potential savings with discounts
  - When default discount is used: Notes that 10% default was applied and custom rates are available

### Technical Details

- Added `_resolve_discount()` helper method to ToolHandlers for consistent discount resolution
- Added `_discount_metadata` to result dictionaries to track discount state
- Updated formatters to display contextual discount tips
- Maintained backward compatibility with explicit `discount_percentage` parameter

## [3.0.0] - 2025-01-XX

### Changed

- Refactored session lifecycle management for optimization
- Improved API client handling

## [2.0.0] - Initial Release

### Added

- Azure Pricing API integration
- MCP server with price search, compare, estimate, and region recommend tools
- Support for customer discounts
- Reserved Instance (RI) pricing support
- SKU discovery functionality
