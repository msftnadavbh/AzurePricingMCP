# Azure Pricing MCP - Project Structure

This document describes the project layout following Python src-layout best practices.

## Directory Structure

```
AzurePricingMCP/
├── src/
│   └── azure_pricing_mcp/              # Main package
│       ├── __init__.py                 # Package exports and version
│       ├── __main__.py                 # Module entry point
│       ├── server.py                   # MCP server, routing, lifecycle
│       ├── handlers.py                 # Main tool handler (extends mixins)
│       ├── client.py                   # Azure Pricing API HTTP client
│       ├── auth.py                     # Azure AD authentication
│       ├── config.py                   # Pricing data & configuration constants
│       ├── formatters.py              # Core response formatters
│       ├── models.py                  # Data models and types
│       ├── tools.py                   # Core MCP tool definitions
│       │
│       ├── services/                  # Business logic layer
│       │   ├── __init__.py
│       │   ├── pricing.py            # Price search, comparison, estimation
│       │   ├── retirement.py         # VM SKU retirement tracking
│       │   ├── sku.py                # SKU discovery and fuzzy matching
│       │   ├── spot.py               # Spot VM eviction rates & pricing
│       │   ├── orphaned.py           # Orphaned resource service wrapper
│       │   ├── orphaned_resources.py  # Orphaned resource scanner (11 types)
│       │   ├── ptu.py                # PTU sizing service
│       │   ├── ptu_models.py         # PTU model data tables
│       │   ├── databricks.py         # Databricks DBU pricing service
│       │   └── github_pricing.py     # GitHub pricing service
│       │
│       ├── databricks/               # Databricks DBU pricing tools
│       │   ├── __init__.py
│       │   ├── formatters.py         # Databricks response formatters
│       │   ├── handlers.py           # Databricks handler mixin
│       │   └── tools.py              # Databricks tool definitions
│       │
│       └── github_pricing/           # GitHub pricing tools
│           ├── __init__.py
│           ├── formatters.py         # GitHub pricing response formatters
│           ├── handlers.py           # GitHub pricing handler mixin
│           └── tools.py              # GitHub pricing tool definitions
│
├── tests/                             # Test suite
│   ├── test_azure_pricing.py         # Core pricing tests
│   ├── test_databricks.py           # Databricks tools tests
│   ├── test_github_pricing.py       # GitHub pricing tests
│   ├── test_http_transport.py       # HTTP transport tests
│   ├── test_integration.py          # Integration tests
│   ├── test_mcp_server.py           # MCP server tests
│   ├── test_orphaned_resources.py   # Orphaned resource tests
│   ├── test_ptu_sizing.py          # PTU sizing tests
│   └── test_ri_pricing.py          # Reserved Instance tests
│
├── scripts/                          # Utility scripts
│   ├── install.py                   # Installation script
│   ├── run_server.py               # Server runner
│   ├── setup.py                    # Setup helper
│   ├── setup.ps1                   # PowerShell setup
│   ├── test_setup.ps1              # PowerShell test setup
│   ├── docker-build.sh             # Docker build (Linux/Mac)
│   ├── docker-build.ps1            # Docker build (Windows)
│   ├── healthcheck.py             # Health check script
│   └── debug_*.py                  # Debug utilities
│
├── docs/                            # Documentation
│   ├── DEVELOPMENT.md              # Development guide
│   ├── FEATURES.md                 # Feature details
│   ├── INTEGRATIONS.md             # VS Code & Claude setup
│   ├── ORPHANED_RESOURCES.md       # Orphaned resources guide
│   ├── PROJECT_STRUCTURE.md        # This file
│   ├── SETUP_CHECKLIST.md          # Setup verification
│   ├── TOOLS.md                    # Tool documentation
│   ├── USAGE_EXAMPLES.md           # Detailed examples
│   └── config_examples.json        # Configuration examples
│
├── Dockerfile                       # Docker image definition
├── pyproject.toml                   # Python packaging config (PEP 518)
├── requirements.txt                 # Dependencies
├── MANIFEST.in                      # Package data inclusion
├── README.md                        # Main documentation
├── INSTALL.md                       # Installation guide
├── CONTRIBUTING.md                  # Contribution guide
├── CHANGELOG.md                     # Version history
└── LICENSE                          # MIT License
```

## Architecture

### Package Organization

The codebase follows a **service → handler → formatter → tool** pattern:

1. **`tools.py`** — Defines MCP tool schemas (name, description, input parameters)
2. **`handlers.py`** — Routes tool calls to service methods, returns formatted output
3. **`services/`** — Business logic: API calls, calculations, data processing
4. **`formatters.py`** — Converts service results into Markdown for AI assistants

### Mixin-Based Handlers

The main `ToolHandlers` class inherits from handler mixins:

```python
class ToolHandlers(DatabricksHandlers, GitHubPricingHandlers):
    # Core Azure pricing handlers + inherited Databricks + GitHub handlers
```

### Adding a New Tool Package

New tool packages (like Databricks or GitHub Pricing) follow this pattern:

1. Create `src/azure_pricing_mcp/<package>/` with `__init__.py`, `tools.py`, `handlers.py`, `formatters.py`
2. Add service logic in `services/<service>.py`
3. Create a handler mixin class and add it to `ToolHandlers` inheritance
4. Register tool definitions in the package's `tools.py`
5. Add routing in `server.py`'s `_register_tool_handlers()`

## Running the Server

```bash
# Module execution
python -m azure_pricing_mcp

# Console script (after pip install)
azure-pricing-mcp

# Run script
python scripts/run_server.py
```

## Development

```bash
# Install in editable mode
pip install -e .[dev]

# Format, lint, type check, test
black src/ tests/
ruff check src/ tests/
mypy src/ --ignore-missing-imports
pytest tests/
```
