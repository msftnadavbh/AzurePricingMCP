# Changelog

All notable changes to the Azure Pricing MCP Server will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [3.1.0] - 2026-01-XX

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

## [3.0.0] - 2026-01-26

### ⚠️ Breaking Changes

#### Entry Point Changed
- **Console script entry point changed from `main` to `run`**
  - The `run()` function is now the synchronous entry point that wraps `asyncio.run(main())`
  - Existing console script configurations (`azure-pricing-mcp`) will continue to work
  - Code directly importing and calling `main()` still works (it's async)
  - This change improves the structure by clearly separating sync/async entry points

#### `create_server()` Return Value
- **`create_server()` now returns a tuple `(Server, AzurePricingServer)` by default**
  - This change exposes the pricing server for testing and advanced use cases
  - Use `create_server(return_pricing_server=False)` for the previous behavior (returns only `Server`)
  - The `AzurePricingServer` instance is needed for lifecycle management

#### Session Lifecycle Management
- **HTTP session is now managed at the server level, not per-tool-call**
  - Previously: Each tool call created and destroyed a new HTTP session (inefficient)
  - Now: A single HTTP session is created at server startup and reused for all tool calls
  - This significantly improves performance and reduces overhead
  - When using `AzurePricingServer` directly, you must manage its lifecycle:
    ```python
    # Option 1: Context manager (recommended)
    async with AzurePricingServer() as pricing_server:
        result = await pricing_server.tool_handlers.handle_price_search(...)
    
    # Option 2: Manual lifecycle management
    pricing_server = AzurePricingServer()
    await pricing_server.initialize()
    try:
        result = await pricing_server.tool_handlers.handle_price_search(...)
    finally:
        await pricing_server.shutdown()
    ```

### Added

- **Modular Services Architecture**
  - `client.py` - HTTP client for Azure Pricing API
  - `services/` - Business logic (PricingService, SKUService, RetirementService)
  - `handlers.py` - MCP tool routing
  - `formatters.py` - Response formatting
  - `models.py` - Data structures
  - `tools.py` - Tool definitions
  - `config.py` - Configuration constants

- **New `AzurePricingServer` Methods**
  - `initialize()` - Explicitly start the HTTP session
  - `shutdown()` - Explicitly close the HTTP session
  - `is_active` property - Check if session is active

- **Improved Documentation**
  - Comprehensive docstrings for all public APIs
  - Breaking change documentation in module docstring

### Changed

- Restructured codebase from monolithic to modular architecture
- Updated all tests to use service-based architecture with proper dependency injection
- Improved error handling with session state checks

### Removed

- Obsolete documentation files:
  - `DOCUMENTATION_UPDATES.md`
  - `MIGRATION_GUIDE.md`
  - `QUICK_START.md` (replaced by README quick start section)
  - `USAGE_EXAMPLES.md` (replaced by README examples)

### Migration Guide

#### For Console Script Users
No changes required. The `azure-pricing-mcp` command continues to work.

#### For Library Users

1. **If you call `create_server()`:**
   ```python
   # Old (v2.x)
   server = create_server()
   
   # New (v3.0) - if you don't need pricing_server
   server = create_server(return_pricing_server=False)
   
   # New (v3.0) - if you need pricing_server for testing
   server, pricing_server = create_server()
   ```

2. **If you use `AzurePricingServer` directly:**
   ```python
   # You MUST initialize the session before tool calls
   async with AzurePricingServer() as pricing_server:
       # All tool calls within this block share the same HTTP session
       result = await pricing_server.tool_handlers.handle_price_search(...)
   ```

## [2.3.0] - Previous Release

See git history for changes in previous versions.
