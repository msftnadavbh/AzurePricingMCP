# 🔎 Orphaned Resources Detection

## What Are Orphaned Resources?

Orphaned resources are Azure resources that were created but are no longer serving their intended purpose, yet continue to accumulate costs. These typically include:

- 💿 **Unattached Managed Disks** - Storage volumes that were detached from virtual machines (often after VM deletion) but remain in your subscription
- 🌐 **Unattached Public IPs** - IP addresses that are no longer associated with any network interface or load balancer
- 📋 **Empty App Service Plans** - Hosting plans that have no web apps deployed but still reserve compute capacity
- 🗄️ **Orphaned SQL Elastic Pools** - Elastic pools with no databases, still incurring reserved compute and storage costs
- 🚪 **Orphaned Application Gateways** - Application gateways with no backend address pools or targets configured
- 🔀 **Orphaned NAT Gateways** - NAT gateways not associated with any subnet
- ⚖️ **Orphaned Load Balancers** - Load balancers with no backend address pools configured
- 🔒 **Orphaned Private DNS Zones** - Private DNS zones with no virtual network links
- 🔗 **Orphaned Private Endpoints** - Private endpoints with no connections or unapproved connection state
- 🌉 **Orphaned Virtual Network Gateways** - Virtual network gateways with no IP configurations
- 🛡️ **Orphaned DDoS Protection Plans** - DDoS protection plans with no associated virtual networks

These resources can accumulate silently over time, creating unnecessary costs. A single forgotten public IP might seem insignificant, but across multiple subscriptions and resource groups, orphaned resources can add up to hundreds or thousands of dollars per month.

## 🤔 Why Use This Tool?

The Orphaned Resources tool helps you:
- 💰 **Reduce Costs** - Identify resources that are billing you but providing no value
- 🧹 **Maintain Clean Infrastructure** - Keep your Azure environment organized and efficient
- 📊 **Get Real Cost Data** - Uses Azure Cost Management API to show actual costs from your billing history (not estimates)
- ⏱️ **Save Time** - Automatically scans across all subscriptions instead of manual portal clicks

## 🚀 Using the Orphaned Resources Tool

Once configured, you can ask Claude:

### Example Queries:

1. **Basic scan:**
   ```
   Find orphaned resources in my Azure subscriptions
   ```

2. **Custom timeframe:**
   ```
   Find orphaned resources from the last 30 days
   ```

3. **Results analysis:**
   ```
   Show me orphaned resources sorted by cost
   ```

4. **Remediation:**
   ```
   Help me create a script to delete the orphaned resources you found
   ```

### Tool Parameters:

```json
{
  "days": 60,                    // Lookback period for cost calculation (default: 60)
  "all_subscriptions": true      // Scan all subscriptions (default: true)
}
```

## 🔍 What It Scans:

- ✅ **Unattached Managed Disks** - Disks not attached to any VM
- ✅ **Unattached Public IPs** - Public IPs with no configuration
- ✅ **Orphaned App Service Plans** - Plans with no web apps
- ✅ **Orphaned SQL Elastic Pools** - Elastic pools with no databases
- ✅ **Orphaned Application Gateways** - Application gateways with no backend targets
- ✅ **Orphaned NAT Gateways** - NAT gateways with no associated subnets
- ✅ **Orphaned Load Balancers** - Load balancers with no backend address pools
- ✅ **Orphaned Private DNS Zones** - Private DNS zones with no virtual network links
- ✅ **Orphaned Private Endpoints** - Private endpoints with no or unapproved connections
- ✅ **Orphaned Virtual Network Gateways** - Virtual network gateways with no IP configurations
- ✅ **Orphaned DDoS Protection Plans** - DDoS protection plans with no associated virtual networks

## 💵 Cost Calculation:

The tool uses **Azure Cost Management API** to retrieve actual costs from your billing data. This provides:
- Real costs (not estimates) over the specified period
- Historical billing data (up to 90 days)
- Per-resource cost breakdown

## 🔑 Authentication Requirements:

The orphaned resources tool requires Azure authentication:

```bash
# Option 1: Azure CLI (recommended)
az login

# Option 2: Environment variables
export AZURE_CLIENT_ID="your-client-id"
export AZURE_CLIENT_SECRET="your-client-secret"
export AZURE_TENANT_ID="your-tenant-id"

# Option 3: Managed Identity (when running in Azure)
# No configuration needed
```

## 🛡️ Permissions Required:

Your Azure account/service principal needs:
- `Reader` role on subscriptions (to list resources)
- `Cost Management Reader` role (to get cost data)

## 📄 Example Output:

```markdown
### 🔍 Orphaned Resources Scan Results

**Subscriptions Scanned:** 5
**Subscriptions with Orphans:** 2
**Total Orphaned Resources:** 2
**Total Estimated Cost:** $7.27

#### 📋 Subscription: Amdocs
ID: `e4303b68-1de0-4a9d-ad35-5c3eb13c05e7`

**Found 1 orphaned resource(s):**

| Type | Name | Resource Group | Cost (Last 60 days) |
|------|------|----------------|----------------------|
| 🌐 public_ip | nginx-techgym-ip | rg-aks-demo-TG | $7.27 |

### 💡 Recommendations

- **Review** each orphaned resource to determine if it's still needed
- **Delete** unused resources to reduce costs
- **Set up alerts** to monitor for orphaned resources
- **Tag resources** to track ownership and purpose
```

## 🛠️ Troubleshooting:

### "Authentication failed"

Verify you're logged in:
```bash
az account show
```

### "Cost Management API error"

Ensure you have `Cost Management Reader` role:
```bash
az role assignment list --assignee $(az account show --query user.name -o tsv) | grep "Cost Management"
```

## 💡 Integration Tips:

1. **Scheduled Scans**: Set up a cron job to run scans weekly
2. **Cost Alerts**: Use the cost data to trigger alerts when orphaned resource costs exceed thresholds
3. **Automated Cleanup**: Generate deletion scripts based on scan results
4. **Reporting**: Export results to CSV or send via email
