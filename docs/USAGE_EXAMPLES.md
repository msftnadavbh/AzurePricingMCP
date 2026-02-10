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
| Orphaned NSG | 1 | $0.00 |
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
| **Orphaned NIC** | Network interfaces not attached to a VM or private endpoint |
| **Orphaned Public IP** | Public IPs not associated with any resource |
| **Orphaned NSG** | Network security groups not attached to any NIC or subnet |
| **Empty App Service Plan** | App Service Plans with zero hosted apps |

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
