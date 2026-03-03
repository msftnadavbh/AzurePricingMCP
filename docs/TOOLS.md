# Available Tools

The Azure Pricing MCP Server provides 18 tools for querying Azure, Databricks, and GitHub pricing.

---

## Core Pricing Tools

These tools work without authentication using the public Azure Retail Prices API.

| Tool | Description |
|------|-------------|
| `azure_price_search` | Search Azure retail prices with flexible filtering (service, region, SKU, price type) |
| `azure_price_compare` | Compare prices across regions or between different SKUs |
| `azure_ri_pricing` | Get Reserved Instance pricing with 1-year and 3-year options and break-even analysis |
| `azure_cost_estimate` | Estimate costs based on usage patterns (hours per day, days per month) |
| `azure_region_recommend` | Find the cheapest Azure regions for any SKU with savings percentages |
| `azure_discover_skus` | List available SKUs for a specific Azure service |
| `azure_sku_discovery` | Intelligent SKU discovery with fuzzy name matching ("vm" → "Virtual Machines") |
| `get_customer_discount` | Get customer discount information (default: 10%) |

---

## Spot VM Tools

These tools require Azure authentication. See [FEATURES.md](FEATURES.md#spot-vm-tools) for authentication setup.

| Tool | Description |
|------|-------------|
| `spot_eviction_rates` | Get Spot VM eviction rates for SKUs across regions |
| `spot_price_history` | Get up to 90 days of historical Spot pricing |
| `simulate_eviction` | Trigger eviction simulation on a running Spot VM |

---

## Cost Optimization Tools

These tools require Azure authentication. See [FEATURES.md](FEATURES.md#orphaned-resource-detection) for details.

| Tool | Description |
|------|-------------|
| `find_orphaned_resources` | Detect orphaned resources (unattached disks, public IPs, empty App Service Plans, SQL Elastic Pools, Application Gateways, NAT Gateways, Load Balancers, Private DNS Zones, Private Endpoints, Virtual Network Gateways, DDoS Protection Plans) and compute wasted cost |

### Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `days` | integer | No | Cost lookback period in days (default: 60) |
| `all_subscriptions` | boolean | No | Scan all accessible subscriptions (default: true) |

---

## PTU Sizing + Cost Planner

No authentication required for sizing. Cost lookup uses the public Azure Retail Prices API.

| Tool | Description |
|------|-------------|
| `azure_ptu_sizing` | Estimate required PTUs for Azure OpenAI model deployments based on workload shape (RPM, tokens, caching) with optional cost estimation |

### Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `model` | string | Yes | Model name (e.g., `gpt-4o`, `gpt-4.1`, `gpt-5`, `o4-mini`) |
| `rpm` | integer | Yes | Requests per minute |
| `avg_input_tokens` | integer | Yes | Average input tokens per request |
| `avg_output_tokens` | integer | Yes | Average output tokens per request |
| `avg_cached_tokens` | integer | No | Average cached tokens per request (default: 0) |
| `deployment_type` | string | No | `GlobalProvisioned`, `DataZoneProvisioned`, or `RegionalProvisioned` |
| `include_cost` | boolean | No | Fetch live $/PTU/hr pricing (default: false) |
| `region` | string | No | Azure region for cost lookup (default: eastus) |

> 📖 **Need help finding your RPM and token counts?** See [PTU Sizing → Getting Your Input Data](USAGE_EXAMPLES.md#getting-your-input-data) for Azure CLI commands, KQL queries, and estimation tables.

---

## Databricks DBU Pricing Tools

No authentication required. Real-time pricing from the Azure Retail Prices API.

| Tool | Description |
|------|-------------|
| `databricks_dbu_pricing` | Search and list Azure Databricks DBU rates by workload type, tier, and region |
| `databricks_cost_estimate` | Estimate monthly and annual Databricks costs based on DBU consumption |
| `databricks_compare_workloads` | Compare DBU costs across workload types or regions |

### `databricks_dbu_pricing` Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `workload_type` | string | No | Workload filter (e.g., `all-purpose`, `jobs`, `sql pro`, `serverless sql`). Supports aliases like `etl`, `notebook`, `warehouse`. |
| `tier` | string | No | `Premium` or `Standard`. If omitted, returns both. |
| `region` | string | No | Azure region (default: `eastus`) |
| `currency_code` | string | No | Currency code (default: `USD`) |

### `databricks_cost_estimate` Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `workload_type` | string | Yes | Type of Databricks workload |
| `dbu_count` | number | Yes | DBUs per worker per hour (depends on VM instance type) |
| `hours_per_day` | number | No | Hours of usage per day (default: 8) |
| `days_per_month` | integer | No | Working days per month (default: 22) |
| `tier` | string | No | `Premium` or `Standard` (default: `Premium`) |
| `region` | string | No | Azure region (default: `eastus`) |
| `num_workers` | integer | No | Number of worker nodes (default: 1) |
| `discount_percentage` | number | No | Discount percentage (e.g., 10 for 10%) |

### `databricks_compare_workloads` Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `workload_types` | array | No | List of workload types to compare. If omitted, compares common types. |
| `regions` | array | No | List of regions to compare (default: `[eastus]`) |
| `tier` | string | No | `Premium` or `Standard` (default: `Premium`) |
| `dbu_count` | number | No | DBU count per worker for monthly cost projection |
| `hours_per_month` | number | No | Hours per month for cost projection (default: 730 if `dbu_count` provided) |

---

## GitHub Pricing Tools

No authentication required. Data sourced from static pricing tables verified against github.com/pricing.

> **Note:** These tools cover **GitHub Copilot** (AI coding assistant) only — not Microsoft 365 Copilot. For M365 Copilot pricing, use `azure_price_search`.

| Tool | Description |
|------|-------------|
| `github_pricing` | Look up GitHub product pricing: Plans (Free/Team/Enterprise), Copilot (Free/Pro/Pro+/Business/Enterprise), Actions runners, Advanced Security, Codespaces, Git LFS, and Packages |
| `github_cost_estimate` | Estimate monthly and annual GitHub costs based on team size and usage (plan seats, Copilot licenses, Actions minutes, Codespaces hours, LFS packs, GHAS committers) |

### `github_pricing` Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `product` | string | No | Product category: `copilot`, `actions`, `plans`, `security`, `codespaces`, `storage`. Omit for full catalog. |
| `copilot_plan` | string | No | Copilot plan filter: `Free`, `Pro`, `Pro+`, `Business`, `Enterprise` |

### `github_cost_estimate` Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `users` | integer | No | Number of user seats (default: 1) |
| `plan` | string | No | GitHub plan: `Free`, `Team`, or `Enterprise`. Omit to exclude plan costs. |
| `copilot_plan` | string | No | Copilot plan: `Free`, `Pro`, `Pro+`, `Business`, `Enterprise` |
| `actions_minutes` | integer | No | Total Actions minutes per month (default: 0) |
| `actions_runner` | string | No | Runner label (e.g., `Linux 2-core`, `Windows 4-core`, `macOS 3-core (M1)`) |
| `codespaces_hours` | number | No | Total Codespaces hours per month (default: 0) |
| `codespaces_cores` | integer | No | Cores per Codespace instance (default: 4) |
| `codespaces_storage_gb` | number | No | Codespaces persistent storage in GB (default: 0) |
| `lfs_packs` | integer | No | Number of 50 GB Git LFS data packs (default: 0) |
| `ghas_committers` | integer | No | Active committers for GitHub Advanced Security (default: 0) |

---

## Example Queries

Once configured, ask your AI assistant:

| Query Type | Example |
|------------|---------|
| **Basic Pricing** | "What's the price of a D4s_v3 VM in West US 2?" |
| **Comparison** | "Compare VM prices between East US and West Europe" |
| **Cost Estimate** | "Estimate monthly cost for D8s_v5 running 12 hours/day" |
| **SKU Discovery** | "What App Service plans are available?" |
| **Spot Eviction** | "What are the eviction rates for D4s_v4 in eastus?" |
| **Orphaned Resources** | "Find orphaned resources across all my subscriptions" |
| **PTU Sizing** | "How many PTUs do I need for gpt-4.1 at 100 RPM with 500 input and 200 output tokens?" |
| **Databricks** | "What are the Databricks DBU rates for jobs workload in Premium tier?" |
| **GitHub Pricing** | "What are the GitHub Copilot plan prices?" |
| **GitHub Cost** | "Estimate monthly GitHub cost for 50 users on Team plan with Copilot Business" |

---

## Detailed Usage Examples

For comprehensive examples with API responses, see [USAGE_EXAMPLES.md](USAGE_EXAMPLES.md).
