# Usage Examples

Real-world examples of using the Azure Pricing MCP Server with AI assistants.

## Quick Start Guide

This guide demonstrates how to use natural language queries with the Azure Pricing MCP Server. Each example shows:
- The query you can ask
- Which tool is invoked
- Sample response format

Copy these queries directly or adapt them to your needs.

## Table of Contents

**Core Pricing**
- [Basic Price Queries](#basic-price-queries)
- [Cost Estimations](#cost-estimations)
- [Price Comparisons](#price-comparisons)

**Advanced Features**
- [Reserved Instance Pricing](#reserved-instance-pricing)
- [Region Recommendations](#region-recommendations)
- [Multi-Node & Cluster Pricing](#multi-node--cluster-pricing)
- [Spot VM Tools](#spot-vm-tools)
- [Orphaned Resource Detection](#orphaned-resource-detection)
- [PTU Sizing](#ptu-sizing)
- [Network Cost Estimation](#network-cost-estimation)
- [Databricks DBU Pricing](#databricks-dbu-pricing)
- [GitHub Pricing](#github-pricing)

**Discovery & Reference**
- [SKU Discovery](#sku-discovery)
- [Storage Pricing](#storage-pricing)
- [Retirement Warnings](#retirement-warnings)
- [Reference Tables](#reference-tables)

## Basic Price Queries

Query prices for Azure services using natural language. The `azure_price_search` tool handles all basic pricing queries.

### Virtual Machines

**Query:** "What's the price of a Standard_D4s_v3 VM in East US?"

**Response:**
```
Standard_D4s_v3 in East US:
- Linux: $0.192/hour ($140.16/month)
- Windows: $0.384/hour ($280.32/month)
- 1-Year Savings Plan: $0.134/hour (30% savings)
- 3-Year Savings Plan: $0.106/hour (45% savings)
```

### Databases

**Query:** "What are the prices for Azure SQL Database in West Europe?"

The tool filters by `service_name=Azure SQL Database` and `region=westeurope`.

### GPU VMs

**Query:** "Show me NVIDIA GPU VM pricing in East US 2"

Searches for VM SKUs with `NC` series (NVIDIA GPUs) in the specified region.

---

## Cost Estimations

Estimate monthly and yearly costs based on usage patterns. Use the `azure_cost_estimate` tool.

### Development Environment (Part-Time Usage)

**Query:** "Estimate monthly cost for D4s_v5 running 10 hours per day, 22 days per month"

**Response:**
```
D4s_v5 Cost Estimate (East US)
Usage: 220 hours/month

On-Demand:     $42.24/month  ($506.88/year)
1-Year Plan:   $29.48/month  ($353.76/year) - Save 30%
3-Year Plan:   $23.32/month  ($279.84/year) - Save 45%
```

### Production 24/7 Workload

**Query:** "Estimate yearly cost for E8s_v5 running 24/7 in West US 2"

Calculates for 730 hours/month (24/7 operation).

---

## Price Comparisons

Compare costs across regions or between SKUs using `azure_price_compare`.

### Compare Across Regions

**Query:** "Compare D4s_v5 VM prices between eastus, westeurope, and southeastasia"

**Response:**
```
D4s_v5 Price Comparison:

| Region        | Hourly   | Monthly (730h) | vs Cheapest |
|---------------|----------|----------------|-------------|
| eastus        | $0.192   | $140.16        | Cheapest    |
| westeurope    | $0.211   | $154.03        | +10%        |
| southeastasia | $0.221   | $161.33        | +15%        |
```

### Compare Storage Tiers

**Query:** "Compare storage options: Premium SSD vs Standard SSD vs Standard HDD"

Compares pricing and performance characteristics of different storage types.

---

## Reserved Instance Pricing

Compare Reserved Instance (RI) pricing with on-demand rates. Use the `azure_ri_pricing` tool for break-even analysis.

**Query:** "Show me Reserved Instance pricing for D4s v3 in East US"

**Response:**
```
D4s v3 (East US) - Reserved Instance Analysis

1-Year RI:
  Rate: $0.112/hr (vs $0.192/hr on-demand)
  Savings: 41.5%
  Break-even: 7.0 months
  Annual savings: $700.80

3-Year RI:
  Rate: $0.073/hr (vs $0.192/hr on-demand)
  Savings: 62.0%
  Break-even: 13.7 months
  Annual savings: $1,042.44
```

---

## Multi-Node & Cluster Pricing

Calculate costs for node pools and entire Kubernetes clusters.

### AKS Node Pool

**Query:** "Price for 20 Standard_D32s_v6 nodes in East US 2 for AKS"

**Response:**
```
Standard_D32s_v6 in East US 2 (20 nodes):

| Option          | Per Node/Month | 20 Nodes/Month | Savings |
|-----------------|----------------|----------------|---------|
| Linux On-Demand | $1,177         | $23,550        | -       |
| 1-Year Plan     | $812           | $16,250        | 31%     |
| 3-Year Plan     | $542           | $10,833        | 54%     |
| Linux Spot      | $228           | $4,569         | 81%     |
```

### Kubernetes Cluster

**Query:** "Estimate monthly cost for a Kubernetes cluster with 5 D8s_v5 nodes for system and 20 D16s_v5 nodes for workloads in East US"

Combines pricing for multiple node pools.

---

## Region Recommendations

Find the most cost-effective Azure regions using `azure_region_recommend`.

**Flexible Format:** Accepts SKU names in multiple formats:
- Display: `D4s v5`, `E4as v5`
- ARM: `Standard_D4s_v5`, `Standard_E4as_v5`
- Underscore: `D4s_v5`, `E4as_v5`

### Find Cheapest Regions

**Query:** "What are the cheapest regions for D4s v5 VMs?"

**Response:**
```
Region Recommendations for D4s v5 (USD)

Cheapest: IN Central (centralindia) - $0.0234/hr
Most Expensive: BR South (brazilsouth) - $0.1170/hr
Max Savings: 80.0%

Top 5 Regions:
| Rank | Region         | Location      | Price/hr | Savings |
|------|----------------|---------------|----------|---------|
| 1    | centralindia   | IN Central    | $0.0234  | 80.0%   |
| 2    | eastus2        | US East 2     | $0.0336  | 71.2%   |
| 3    | eastus         | US East       | $0.0336  | 71.2%   |
| 4    | westus3        | US West 3     | $0.0336  | 71.2%   |
| 5    | northcentralus | US North Cen  | $0.0364  | 68.9%   |
```

### With Discount

**Query:** "Show cheapest regions for E4s v5 VMs with my 15% enterprise discount"

Applies your discount percentage to all prices shown.

---

## SKU Discovery

Discover available Azure services and SKUs using fuzzy matching with `azure_sku_discovery`.

### Find VM Sizes

**Query:** "What VM sizes are available for compute-intensive workloads?"

Searches for compute-optimized VM series.

### App Service Plans

**Query:** "What App Service plans are available?"

**Response:**
```
Azure App Service Plans:

Basic:
  • B1: $0.018/hour
  • B2: $0.036/hour
  • B3: $0.072/hour

Standard:
  • S1: $0.10/hour
  • S2: $0.20/hour
  • S3: $0.40/hour

Premium v3:
  • P1v3: $0.125/hour
  • P2v3: $0.25/hour
  • P3v3: $0.50/hour
```

### Common Service Aliases

The tool recognizes common aliases:

| You Say | Finds |
|---------|-------|
| "vm", "virtual machine" | Virtual Machines |
| "app service", "web app" | Azure App Service |
| "sql", "database" | Azure SQL Database |
| "kubernetes", "aks", "k8s" | Azure Kubernetes Service |
| "storage", "blob" | Storage |
| "functions", "serverless" | Azure Functions |

---

## Storage Pricing

Query storage costs for various Azure storage services.

### Block Blob Operations

**Query:** "How much does 100,000 write operations on Block Blob LRS GPv1 in East US cost?"

**Response:**
```
Block Blob LRS (GPv1) - East US:
Write Operations: $0.00036 per 10K
100,000 operations = 10 × 10K = $0.0036

With 10% discount: $0.00324
```

### Storage Tiers

**Query:** "Compare Hot, Cool, and Archive storage pricing in East US"

Compares data storage and access costs across tiers.

---

## Spot VM Tools

**Note:** Requires Azure authentication (`az login`, service principal, or managed identity).

### Check Eviction Rates

**Query:** "What are the Spot eviction rates for D4s_v3 in East US?"

Uses `spot_eviction_rates` to query Azure Resource Graph for real-time eviction data.

**Response:**
```
Spot VM Eviction Rates (East US):

| SKU    | Eviction Rate | Risk Level |
|--------|---------------|------------|
| D4s_v3 | 0-5%          | Low        |
| D8s_v3 | 5-10%         | Moderate   |
```

### Price History

**Query:** "Show me the Spot price history for D4s_v3 in East US over the last 30 days"

Uses `spot_price_history` for up to 90 days of historical pricing.

**Response:**
```
Spot Price History - D4s_v3 (East US):

Current: $0.0384/hr
7-day avg: $0.0391/hr
30-day avg: $0.0402/hr
Range: $0.0362 - $0.0458
Trend: Stable (±5%)
```

### Simulate Eviction

**Query:** "Simulate eviction for my Spot VM my-spot-vm in my-rg"

Uses `simulate_eviction` to trigger a test eviction signal (requires VM Contributor role).

### Decision Analysis

**Query:** "Should I use Spot VMs for D16s_v3 in East US for batch processing?"

Combines eviction rates and pricing to provide recommendations:

```
D16s_v3 (East US) Analysis:

Eviction Risk: 0-5% (Low)
Best for: Batch processing, CI/CD, dev/test

Cost Comparison:
| Type      | Monthly (730h) | Savings |
|-----------|----------------|---------|
| On-Demand | $560.64        | -       |
| Spot      | $112.42        | 80%     |
| 1-Year RI | $354.78        | 37%     |

Recommendation: Spot VMs recommended for batch processing
```

---

## Orphaned Resource Detection

**Note:** Requires Azure authentication (`az login`, service principal, or managed identity).

Detect orphaned Azure resources that are incurring costs without providing value. Uses `find_orphaned_resources` tool.

### Scan All Subscriptions

**Query:** "Find all orphaned resources across my Azure subscriptions"

**Response:**
```
### Orphaned Resource Report

Total orphaned resources: 5
Estimated wasted cost (60 days): $127.50 USD
Subscriptions scanned: 3

#### Summary by Type

| Resource Type | Count | Est. Cost |
|---------------|-------|-----------|
| Unattached Disk | 2 | $85.00 |
| Orphaned Public IP | 2 | $42.50 |
| Orphaned Load Balancer | 1 | $18.25 |
```

### Custom Lookback Period

**Query:** "Show me orphaned resources with costs from the last 30 days"

Uses `days=30` parameter to adjust the cost calculation window.

### Single Subscription Scan

**Query:** "Scan for orphaned resources in my primary subscription only"

Uses `all_subscriptions=false` to limit the scan scope.

### Detected Resource Types

The tool detects these orphaned resource types:

| Resource Type | Detection Criteria |
|---------------|--------------------|
| **Unattached Disk** | Managed disks with no `managedBy` reference |
| **Orphaned Public IP** | Public IPs not associated with any resource |
| **Empty App Service Plan** | App Service Plans with zero hosted apps |
| **Orphaned SQL Elastic Pool** | SQL Elastic Pools with no databases in the pool |
| **Orphaned Application Gateway** | Application gateways with no backend address pools or targets |
| **Orphaned NAT Gateway** | NAT gateways not associated with any subnet |
| **Orphaned Load Balancer** | Load balancers with no backend address pools |
| **Orphaned Private DNS Zone** | Private DNS zones with no virtual network links |
| **Orphaned Private Endpoint** | Private endpoints with no connections or unapproved connections |
| **Orphaned Virtual Network Gateway** | Virtual network gateways with no IP configurations |
| **Orphaned DDoS Protection Plan** | DDoS protection plans with no associated virtual networks |

### Cost Analysis

**Query:** "How much am I wasting on orphaned resources?"

**Response:**
```
### Orphaned Resource Report

Total orphaned resources: 3
Estimated wasted cost (60 days): $89.25 USD

#### Unattached Disk (2)

| Name | Resource Group | Location | Cost |
|------|----------------|----------|------|
| old-data-disk | prod-rg | eastus | $52.00 |
| temp-backup | dev-rg | westus2 | $30.00 |

#### Orphaned Public IP (1)

| Name | Resource Group | Location | Cost |
|------|----------------|----------|------|
| unused-pip | test-rg | eastus | $7.25 |
```

---

## PTU Sizing

Estimate Provisioned Throughput Units (PTUs) for Azure OpenAI / AI Foundry model deployments. Uses `azure_ptu_sizing` tool.

**No authentication required** - PTU calculations are purely offline using official Microsoft data.

The tool needs three required inputs: **RPM** (requests per minute), **avg input tokens**, and **avg output tokens** per request. Here's how to get them.

### Getting Your Input Data

#### Option A — Azure CLI (no Log Analytics)

Copy-paste this script — it queries the last 30 days and prints your three inputs:

```bash
# Replace {sub}, {rg}, {name} with your values
RES="/subscriptions/{sub}/resourceGroups/{rg}/providers/Microsoft.CognitiveServices/accounts/{name}"
START=$(date -u -d "30 days ago" +%Y-%m-%dT%H:%M:%SZ)
END=$(date -u +%Y-%m-%dT%H:%M:%SZ)

REQS=$(az monitor metrics list --resource "$RES" --metric AzureOpenAIRequests \
  --aggregation Total --interval P30D --start-time "$START" --end-time "$END" \
  --query "value[0].timeseries[0].data[0].total" -o tsv)

INPUT=$(az monitor metrics list --resource "$RES" --metric ProcessedPromptTokens \
  --aggregation Total --interval P30D --start-time "$START" --end-time "$END" \
  --query "value[0].timeseries[0].data[0].total" -o tsv)

OUTPUT=$(az monitor metrics list --resource "$RES" --metric GeneratedTokens \
  --aggregation Total --interval P30D --start-time "$START" --end-time "$END" \
  --query "value[0].timeseries[0].data[0].total" -o tsv)

PEAK=$(az monitor metrics list --resource "$RES" --metric AzureOpenAIRequests \
  --aggregation Total --interval PT1H --start-time "$START" --end-time "$END" \
  --query "max(value[0].timeseries[0].data[].total)" -o tsv)

echo "=== Your PTU Sizing Inputs ==="
echo "rpm:               $(echo "$PEAK / 60" | bc)"
echo "avg_input_tokens:  $(echo "$INPUT / $REQS" | bc)"
echo "avg_output_tokens: $(echo "$OUTPUT / $REQS" | bc)"
```

#### Option B — KQL (requires Log Analytics)

Enable diagnostic settings on your OpenAI resource → send to Log Analytics, then run:

```kql
AzureMetrics
| where ResourceProvider == "MICROSOFT.COGNITIVESERVICES"
| where TimeGenerated >= ago(30d)
| summarize
    TotalRequests   = sumif(Total, MetricName == "AzureOpenAIRequests"),
    TotalInputTok   = sumif(Total, MetricName == "ProcessedPromptTokens"),
    TotalOutputTok  = sumif(Total, MetricName == "GeneratedTokens")
    by bin(TimeGenerated, 1h)
| summarize
    AvgRPM         = avg(TotalRequests) / 60,
    PeakRPM        = max(TotalRequests) / 60,
    AvgInputTokens = avg(TotalInputTok / TotalRequests),
    AvgOutputTokens= avg(TotalOutputTok / TotalRequests)
```

Use `PeakRPM` to size for burst traffic.

#### No Azure Data Yet?

| Use Case | Typical RPM | Avg Input Tokens | Avg Output Tokens |
|----------|:-----------:|:----------------:|:-----------------:|
| Chatbot / Q&A | 30–100 | 200–500 | 100–300 |
| RAG (retrieval-augmented) | 20–80 | 1,500–3,000 | 300–600 |
| Document summarization | 10–30 | 3,000–6,000 | 500–1,000 |
| Code generation | 20–60 | 1,000–2,000 | 500–1,500 |
| Batch processing | 50–200 | 500–1,500 | 200–500 |

> Start conservative — you can always scale PTUs up later.

### Basic PTU Estimation

**Query:** "How many PTUs do I need for gpt-4.1 at 100 RPM with 500 input and 200 output tokens?"

**Response:**
```
⚡ PTU Sizing Estimate

Model: gpt-4.1
Deployment: Global Provisioned

Workload Shape:
- Requests/min: 100
- Input tokens/request: 500
- Output tokens/request: 200

Calculation:
- Output multiplier: 1 output = 4 input tokens
- Equivalent TPM: 130,000
- Input TPM per PTU: 3,000
- Raw PTU estimate: 43.33

✅ Recommended PTUs: 45
(Minimum: 15, Scale increment: 5)
```

### With Caching

**Query:** "Estimate PTUs for gpt-5 with 50 RPM, 1000 input tokens, 500 output tokens, and 300 cached tokens using DataZoneProvisioned"

**Response:**
```
⚡ PTU Sizing Estimate

Model: gpt-5
Deployment: Data Zone Provisioned

Workload Shape:
- Requests/min: 50
- Input tokens/request: 1,000
- Output tokens/request: 500
- Cached tokens/request: 300

Calculation:
- Output multiplier: 1 output = 8 input tokens (gpt-5 specific)
- Effective input (after cache): 700
- Equivalent TPM: 235,000

✅ Recommended PTUs: 50
```

### Regional Deployment

**Query:** "Calculate PTUs for o4-mini Regional deployment at 200 RPM with 300 input and 150 output tokens"

Uses different minimum PTUs and scale increments for Regional deployments.

### With Cost Estimation

**Query:** "Estimate PTU cost for gpt-4o in eastus with 400 RPM, 300 input tokens, 400 output tokens"

Uses `include_cost=true` to fetch live $/PTU/hr pricing.

### Supported Models

| Model Family | Models |
|-------------|--------|
| **GPT-5.x** | gpt-5.2, gpt-5.1, gpt-5, gpt-5-mini, codex variants |
| **GPT-4.1** | gpt-4.1, gpt-4.1-mini, gpt-4.1-nano |
| **GPT-4o** | gpt-4o, gpt-4o-mini |
| **O-series** | o3, o4-mini, o3-mini, o1 |
| **Direct Azure** | Llama-3.3-70B-Instruct, DeepSeek-R1, DeepSeek-R1-0528, DeepSeek-V3-0324 |

### Deployment Types

| Type | Processing | Min/Increment |
|------|------------|---------------|
| **GlobalProvisioned** | Any Azure geography | Lowest minimums |
| **DataZoneProvisioned** | Within data zone (EU, US) | Same as Global |
| **RegionalProvisioned** | Single region | Higher minimums |

---

## Network Cost Estimation

Estimate the monthly and annual cost of an Azure networking topology — bandwidth / egress,
NAT Gateway, Public IP, Load Balancer, Private Link, and Application Gateway. Uses the
`azure_network_cost_estimate` tool. No authentication required.

### Example 1: Internet Egress with Tiered Pricing

**Query:**
```
"Estimate egress cost for 20 TB/month leaving East US to the internet"
```

**Tool invoked:** `azure_network_cost_estimate`

**Parameters:**
```json
{
  "source_region": "eastus",
  "destination_type": "internet",
  "monthly_data_gb": 20480
}
```

**Sample response (abridged):**
```
## Azure Network Cost Estimate

**Source region:** eastus
**Destination type:** internet
**Currency:** USD

### Assumptions
- Source region: eastus
- Destination type: internet
- Monthly data transfer: 20480 GB
- Prices are pay-as-you-go Consumption rates; Reservation rows are excluded.

### Priced Components
| Component | Detail | Qty | Unit | Monthly Cost |
|-----------|--------|-----|------|--------------|
| Bandwidth - internet egress | Graduated data-transfer-out pricing | 20480 | GB | USD 1,740.80 |

### Tiered Breakdown
**Bandwidth - internet egress** - 20480 GB

| Tier (from units) | Up to | Units | Unit Price | Line Cost |
|-------------------|-------|-------|------------|-----------|
| 0 | 10240 | 10240 | USD 0.087500 | USD 896.00 |
| 10240 | + | 10240 | USD 0.082500 | USD 844.80 |
_Subtotal: USD 1,740.80_

### Total
- **Total monthly cost: USD 1,740.80**
- **Annualized cost: USD 20,889.60**
```

### Example 2: NAT Gateway with Data Processing

**Query:**
```
"What's the monthly cost of a NAT Gateway in westeurope processing 5 TB?"
```

**Parameters:**
```json
{
  "source_region": "westeurope",
  "include_nat_gateway": true,
  "monthly_data_gb": 5120,
  "gateway_hours": 730
}
```

The NAT Gateway is priced as **gateway-hours + data processed**. If a regional Consumption
meter is unavailable, the tool falls back to `Global` pricing and marks the result accordingly.

### Example 3: Cross-Region Transfer

**Query:**
```
"Plan network costs from eastus to westus for 10 TB cross-region"
```

**Parameters:**
```json
{
  "source_region": "eastus",
  "destination_region": "westus",
  "destination_type": "cross_region",
  "monthly_data_gb": 10240
}
```

### Notes on Correctness

- Only pay-as-you-go **Consumption** meters are used. A `Reservation` row is never treated as
  an hourly price, even when its `unitOfMeasure` is `1 Hour`.
- Components that can't be matched to a single unambiguous meter (e.g., an ambiguous Public IP
  or Load Balancer meter) are listed under **Unpriced Components** with a reason, rather than
  being guessed.
- Any value that relies on `Global` pricing is clearly flagged in the response.

---

## Databricks DBU Pricing

Query Azure Databricks DBU rates and estimate costs. Uses `databricks_dbu_pricing`, `databricks_cost_estimate`, and `databricks_compare_workloads` tools.

**No authentication required** — pricing comes from the Azure Retail Prices API.

### Look Up DBU Rates

**Query:** "What are the Databricks DBU rates for jobs workload in Premium tier?"

**Response:**
```
Azure Databricks DBU Pricing — East US (USD)

Jobs (Premium): $0.30/DBU-hour
Jobs (Standard): $0.20/DBU-hour
Jobs Light (Premium): $0.22/DBU-hour
```

### Estimate Databricks Costs

**Query:** "Estimate monthly cost for a Databricks all-purpose cluster with 4 workers, 0.75 DBU each, running 10 hours a day, 22 days a month"

Uses `databricks_cost_estimate` with `workload_type="all-purpose"`, `dbu_count=0.75`, `num_workers=4`, `hours_per_day=10`, `days_per_month=22`.

**Response:**
```
Databricks Cost Estimate — All-Purpose (Premium)

Region: East US
DBU Rate: $0.55/DBU-hour
Workers: 4 × 0.75 DBU = 3.00 DBU/hour
Usage: 10 hrs/day × 22 days = 220 hrs/month

Monthly: $363.00
Annual:  $4,356.00

Note: VM compute, storage, and networking billed separately.
```

### Compare Workload Types

**Query:** "Compare Databricks costs between all-purpose, jobs, and serverless sql workloads in East US and West Europe"

Uses `databricks_compare_workloads` with `workload_types=["all-purpose", "jobs", "serverless sql"]` and `regions=["eastus", "westeurope"]`.

### Supported Workload Types

| Workload | Aliases |
|----------|---------|
| `all-purpose` | `notebook`, `interactive` |
| `jobs` | `etl`, `batch` |
| `jobs light` | `light` |
| `sql pro` | `sql`, `bi` |
| `serverless sql` | `warehouse`, `sql serverless` |
| `delta live tables pro` | `dlt`, `pipelines` |
| `model training` | `ml`, `training` |
| `automated serverless` | `serverless` |

---

## GitHub Pricing

Look up GitHub product pricing and estimate team costs. Uses `github_pricing` and `github_cost_estimate` tools.

**No authentication required** — data sourced from static pricing tables verified against github.com/pricing.

> **Note:** These tools cover **GitHub Copilot** (AI coding assistant) only — not Microsoft 365 Copilot. For M365 Copilot pricing, use `azure_price_search`.

### Look Up Product Pricing

**Query:** "What are the GitHub Copilot pricing plans?"

**Response:**
```
## GitHub Copilot Pricing

| Plan | Price | Billing |
|------|-------|---------|
| Free | $0 | Free |
| Pro | $10/month | Per user |
| Pro+ | $39/month | Per user |
| Business | $19/month | Per user |
| Enterprise | $39/month | Per user |
```

### GitHub Actions Pricing

**Query:** "How much does GitHub Actions cost for macOS runners?"

Uses `github_pricing` with `product="actions"`.

### Estimate Team Costs

**Query:** "Estimate monthly GitHub cost for 50 users on Team plan with Copilot Business and 10,000 Actions minutes"

Uses `github_cost_estimate` with `users=50`, `plan="Team"`, `copilot_plan="Business"`, `actions_minutes=10000`.

**Response:**
```
## GitHub Cost Estimate — 50 users

| Line Item | Monthly | Annual |
|-----------|---------|--------|
| Team plan (50 seats) | $200.00 | $2,400.00 |
| Copilot Business (50 licenses) | $950.00 | $11,400.00 |
| Actions (10,000 min @ Linux 2-core) | $80.00 | $960.00 |
| **Total** | **$1,230.00** | **$14,760.00** |
```

### Copilot-Only Estimate

**Query:** "How much would 20 Copilot Business licenses cost?"

Uses `github_cost_estimate` with `users=20`, `copilot_plan="Business"` (no `plan` parameter — excludes plan seat costs).

### Advanced Security Pricing

**Query:** "Show me GitHub Advanced Security pricing for 100 active committers"

Uses `github_cost_estimate` with `ghas_committers=100`.

---

## Retirement Warnings

The server automatically warns when querying retired or retiring VM SKUs.

### Retiring SKU Example

**Query:** "What's the price of L32s v2 in East US?"

**Response:**
```
⚠️ RETIREMENT WARNING: Lsv2-series
   Status: Retirement Announced
   Retirement Date: 11/15/28
   Recommendation: Migrate to Lsv3, Lasv3, Lsv4, or Lasv4 series

L32s v2 in East US:
- Spot: $0.313/hour
- On-Demand: $2.480/hour
```

### Previous Generation Example

**Query:** "What's the price of E32 v3 in East US?"

**Response:**
```
ℹ️ PREVIOUS GENERATION: Ev3-series
   Recommendation: Consider upgrading to Ev5 or Ev6 series

E32 v3 in East US: $2.016/hour
```

### Warning Types

| Status | Meaning |
|--------|---------|
| ⚠️ Retirement Announced | SKU will be retired - plan migration |
| 🚫 Retired | No longer available for new deployments |
| ℹ️ Previous Generation | Newer versions available |

---

## Reference Tables

Quick reference for service names, regions, and best practices.

### Common Azure Service Names

Service names are case-sensitive. Use exact names for best results.

| Service | API Name |
|---------|----------|
| Virtual Machines | `Virtual Machines` |
| Storage | `Storage` |
| SQL Database | `Azure SQL Database` |
| Cosmos DB | `Azure Cosmos DB` |
| Kubernetes | `Azure Kubernetes Service` |
| App Service | `Azure App Service` |
| Functions | `Azure Functions` |
| OpenAI | `Azure OpenAI` |

### Common Azure Regions

| Region Code | Location |
|-------------|----------|
| `eastus` | US East |
| `eastus2` | US East 2 |
| `westus2` | US West 2 |
| `centralus` | US Central |
| `westeurope` | West Europe |
| `northeurope` | North Europe |
| `uksouth` | UK South |
| `eastasia` | East Asia |
| `southeastasia` | Southeast Asia |
| `japaneast` | Japan East |

### Best Practices

| Practice | Why |
|----------|-----|
| Use specific SKU names | `D4s_v5` not `D4` - avoids ambiguity |
| Use lowercase region codes | API requires `eastus` not `East US` |
| Compare savings plans | 1yr and 3yr options can save 30-60% |
| Try fuzzy discovery | `azure_sku_discovery` finds services with approximate names |
| Specify currency | Add `currency_code=EUR` for non-USD pricing |

---

## Troubleshooting

### No Results

- Service name misspelled or wrong case
- SKU doesn't exist in that region
- Region code incorrect (use lowercase)

**Solution:** Start with broader search, then add filters.

### Unexpected Prices

- Check Spot vs On-Demand pricing
- Windows pricing is ~2x Linux
- Verify unit (per-hour vs per-month)

### Too Many Results

- Add region or SKU name filters
- Use `limit` parameter

---

**Questions?** Check the [README](../README.md) or open an [issue](https://github.com/msftnadavbh/AzurePricingMCP/issues).
