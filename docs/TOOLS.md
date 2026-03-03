# Available Tools

The Azure Pricing MCP Server provides 15 tools for querying Azure pricing information.

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
| `get_customer_discount` | Get customer discount information |

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

---

## PTU Sizing + Cost Planner

No authentication required for sizing. Cost lookup uses the public Azure Retail Prices API.

| Tool | Description |
|------|-------------|
| `azure_ptu_sizing` | Estimate required PTUs for Azure OpenAI model deployments based on workload shape (RPM, tokens, caching) with optional cost estimation |

> 📖 **Need help finding your RPM and token counts?** See [PTU Sizing → Getting Your Input Data](USAGE_EXAMPLES.md#getting-your-input-data) for Azure CLI commands, KQL queries, and estimation tables.

---

## GitHub Pricing Tools

No authentication required. Data sourced from static pricing tables verified against github.com/pricing.

| Tool | Description |
|------|-------------|
| `github_pricing` | Look up GitHub product pricing: Plans (Free/Team/Enterprise), Copilot (Free/Pro/Pro+/Business/Enterprise), Actions runners, Advanced Security, Codespaces, Git LFS, and Packages |
| `github_cost_estimate` | Estimate monthly and annual GitHub costs based on team size and usage (plan seats, Copilot licenses, Actions minutes, Codespaces hours, LFS packs, GHAS committers) |

---

## Example Queries

Once configured, ask your AI assistant:

| Query Type | Example |
|------------|---------|
| **Basic Pricing** | "What's the price of a D4s_v3 VM in West US 2?" |
| **Multi-Node** | "Price for 20 Standard_D32s_v6 nodes in East US 2" |
| **Comparison** | "Compare VM prices between East US and West Europe" |
| **Cost Estimate** | "Estimate monthly cost for D8s_v5 running 12 hours/day" |
| **SKU Discovery** | "What App Service plans are available?" |
| **Savings Plans** | "Show savings plan options for virtual machines" |
| **Storage** | "What are the blob storage pricing tiers?" |
| **Spot Eviction** | "What are the eviction rates for D4s_v4 in eastus?" |
| **Spot History** | "Show me Spot price history for D2s_v4 in westus2" |
| **Orphaned Resources** | "Find orphaned resources across all my subscriptions" |
| **PTU Sizing** | "How many PTUs do I need for gpt-4.1 at 100 RPM with 500 input and 200 output tokens?" |
| **PTU Cost** | "Estimate PTU cost for gpt-5 deployment with 50 RPM, 1000 input tokens, 500 output tokens, include cost for eastus" |
| **GitHub Pricing** | "What are the GitHub Copilot plan prices?" |
| **GitHub Cost** | "Estimate monthly GitHub cost for 50 users on Team plan with Copilot Business and 10,000 Actions minutes" |

### Sample Response

```
Standard_D32s_v6 in East US 2:
- Linux On-Demand: $1.613/hour → $23,550/month for 20 nodes
- 1-Year Savings:  $1.113/hour → $16,250/month (31% savings)
- 3-Year Savings:  $0.742/hour → $10,833/month (54% savings)
```

---

## Detailed Usage Examples

For comprehensive examples with API responses, see [USAGE_EXAMPLES.md](USAGE_EXAMPLES.md).
