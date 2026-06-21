<!-- VERIFIED: 2026-06-13 against https://learn.microsoft.com/en-us/azure/well-architected/microsoft-fabric/cost-optimization -->

# Cost Optimization: Fabric WAF Reference

## Source

Microsoft Learn: [Cost considerations for Microsoft Fabric workloads](https://learn.microsoft.com/en-us/azure/well-architected/microsoft-fabric/cost-optimization)

> Re-fetch when authoring or updating this reference.

---

## Workload coverage matrix

| Workload | Coverage | Notes (from Learn page) |
|---|---|---|
| Lakehouse | Yes | Spark CU consumption, autoscale billing applicable |
| Warehouse | Yes | T-SQL compute consumes CUs; autoscale billing for data warehousing called out |
| Real-Time Intelligence (Eventstream / Eventhouse / Activator) | Partial | Compute model implied; not explicitly called out per workload |
| Data Factory (Pipelines / Dataflows Gen2) | Yes | Pipeline activity drives compute; covered under data processing cost driver |
| Data Science (notebooks / Data Agents) | Partial | Notebook CU consumption covered; Data Agent cost not explicitly called out |
| Mirroring | Partial | Storage cost implication for mirrored data; compute cost less explicit |
| Power BI (semantic models / reports) | Yes | Power BI Pro licensing called out for authors/consumers on small SKUs |
| OneLake | Yes | Storage billed per GB; retention/caching directly affect cost |

---

## Pillar overview

Cost optimization in Microsoft Fabric requires architectural foresight, operational discipline, and smart automation. The platform uses capacity-based pricing (CUs); compute, storage, data processing, data transfer, and retention all drive cost. Effective cost control is a continuous loop: **Observe → Account → Control**.

---

## Principles (Microsoft Learn H2s, verbatim)

### Identify key cost drivers

Fabric uses **capacity-based pricing**: compute measured in **Capacity Units (CUs)**, two purchasing options:

- **Pay-as-you-go (PAYG)**: billed per active minute
- **Reserved capacity**: discounted for 1- or 3-year commitments

Cost drivers (from Learn):

| Cost driver | How it impacts cost | Considerations |
|---|---|---|
| **Compute (capacity units)** | Primary cost driver | Larger capacity / longer active duration = higher cost |
| **Storage (OneLake)** | Per-GB | Datasets, historical, cached results |
| **Data processing** | Ingestion, transformation, queries | Complex queries / heavy pipelines raise CU use |
| **Data transfer** | Cross-region or external egress | Egress charges depend on architecture |
| **Retention and caching** | Long-term storage policies | Larger retention = higher monthly storage cost |

Because compute is provisioned ahead of time, costs are tied to size, not utilization: underutilized capacities still cost. For bursty Spark / data warehousing workloads, use **autoscale billing** (pay per active job). Use **capacity overage billing** as a safety net for occasional spikes.

#### Recognize hidden and indirect costs

Storage continues to accrue even when compute is paused. Long retention, cached results, soft-deleted data inflate storage. Power BI Pro licenses may be required for report authors/publishers/consumers on small Fabric SKUs. Inefficient capacity utilization is an indirect cost: oversizing or leaving idle = waste.

**Evidence**: capacity SKU + PAYG/reserved mix; per-workload CU consumption (Capacity Metrics App); storage growth trend; Power BI Pro license inventory; idle/oversized capacity list.

> **Currency**: when reporting any cost figure, always include the currency code from the source (Azure Cost Management returns a `Currency` column; billing APIs expose the billing currency). Write `958.66 USD`, not `$958.66`: customers are global and may bill in other currencies. See the presentation convention in `common/FABRIC-WAF-CORE.md`.


### Model costs effectively

Use platform capabilities to optimize for workload patterns:

- **Smoothing and bursting**: interactive smoothed over short intervals; background over longer periods. Size near average, not peak. Sustained overutilization triggers staged throttling.
- **Pooling**: multiple workloads on a shared capacity improves utilization.
- **Reservation** for predictable, steady workloads; PAYG/autoscale for variable.

Account for future growth: ingestion volume, query concurrency, retention, multi-region expansion, workload consolidation. Model both scale-up (larger SKU) and scale-out (more capacities).

> **Important (from Learn)**: Design decisions directly affect cost. Run a small PoC with representative workloads before committing to SKU. Consider shortcuts for in-place data sharing, minimize unnecessary data movement, align with smoothing.

#### Currency handling

Customers are global and bill in different currencies. Handle currency by source, and **never FX-convert actual billed amounts**:

| Need | Source | Currency behavior |
|---|---|---|
| **Actual spend** (what was billed) | Azure Cost Management (`POST .../CostManagement/query`) | Returns the tenant's **billing currency** in a `Currency` column. Report it as-is (e.g. `1,564.89 USD`, `1,210.40 EUR`). It already matches the customer's invoice; no conversion. |
| **Forward-looking estimates** (e.g. "what would F64->F32 save in EUR?") | [Azure Retail Prices API](https://learn.microsoft.com/en-us/rest/api/cost-management/retail-prices/azure-retail-prices) `prices.azure.com/api/retail/prices?currencyCode='EUR'` | Returns **Microsoft's native per-currency list price** for the meter (verified: Fabric CU/hr = 0.2574 USD vs 0.2214 EUR vs 41.0566 JPY). These are published list prices, not USD x FX. Use this for capacity right-sizing math in the target currency. |
| **Restate observed costs in a different display currency** (rare; e.g. a global team consolidating a EUR tenant into USD reporting) | Explicit, opt-in only | Keep the original billing-currency value as source of truth and show it alongside. Label the converted value `indicative, converted at <rate> on <date>, source <X>` using a documented, dated FX reference (e.g. an ECB/central-bank rate). Never replace the billed number. |

Must / Avoid:

- **Do** take actuals from Cost Management in the billing currency and always print the currency code.
- **Do** query the Retail Prices API with `currencyCode` for target-currency estimates (supported, public, no auth).
- **Avoid** scraping the Azure Pricing Calculator for exchange rates: it is a UI with no documented FX/exchange-rate API; the result is fragile, unsupported, and drifts daily.
- **Avoid** FX-converting billed amounts by default: a converted figure matches no invoice and changes every day, which undermines an auditable point-in-time assessment.

#### Use cost estimation tools

- [Microsoft Fabric Capacity Estimator](https://www.microsoft.com/microsoft-fabric/capacity-estimator)
- [Azure Pricing Calculator](https://azure.microsoft.com/pricing/calculator/) (UI only; not a programmatic price/FX source)
- [Azure Retail Prices API](https://learn.microsoft.com/en-us/rest/api/cost-management/retail-prices/azure-retail-prices) (programmatic per-currency list prices via `currencyCode`)
- [Microsoft Cost Management and Billing](https://learn.microsoft.com/en-us/azure/cost-management-billing/)
- [Fabric cost analysis tools](https://github.com/microsoft/fabric-toolbox/tree/main/monitoring/fabric-cost-analysis): open-source accelerator

**Evidence**: capacity sizing rationale; reservation vs PAYG decision log; growth model assumptions; estimator output for current scope.

### Monitor costs and implement governance

Make capacity usage visible. Fabric workloads often share capacities: attribution requires monitoring tools.

| Capability | Purpose | Tooling (from Learn) |
|---|---|---|
| Cost tracking | Actual spending | Azure Cost Management |
| Capacity utilization | Compute-heavy workloads | Fabric Capacity Metrics App |
| Cost allocation | Per-team attribution | Fabric Chargeback App |
| Custom reporting | Dashboards | Fabric Cost Analysis solution accelerator |

Cost governance loop: **Observe → Account → Control**.

| Step | Goal | Examples (from Learn) |
|---|---|---|
| **Observe** | Understand usage patterns | Monitor CU usage, storage growth, workload activity |
| **Account** | Ensure teams own usage | Allocate costs, set budgets, review spending |
| **Control** | Apply governance policies | Assign workspaces to capacities, enforce tagging, set limits |

Governance practices (from Learn): assign workspaces to specific capacities, pause idle dev environments, separate dev/test/prod, investigate sudden spikes, review retention/cache periodically, set scaling guardrails, leverage **Fabric surge protection** to cap workload/workspace consumption.

**Evidence**: Cost Management report; Capacity Metrics export; chargeback report; budget alerts; tagging coverage; surge protection settings; ownership table per capacity/workspace.

### Optimize environment costs

Dev/test/prod have different usage patterns. Fabric does not offer separate feature tiers per environment: all [SKUs](https://learn.microsoft.com/en-us/fabric/enterprise/licenses#capacity) have the same capabilities. Optimization comes from sizing, scheduling, management.

| Environment | Typical configuration | Cost optimization (from Learn) |
|---|---|---|
| Development | Small or shared capacity | Pause when idle, scale up temporarily for testing |
| Testing / QA | Small to medium | Run during validation windows only |
| Production | Dedicated, sized for demand | Consider reserved capacity for predictable usage |

Temporary environments for CI/CD or large integration tests.

> **Important (from Learn)**: Pre-production can drive up costs if unmanaged. Use scheduled pause/resume, budget alerts, capacity size limits, tagging standards.

#### Consider multi-tenant environment factors

For multi-tenant solutions (one solution serving multiple customers):

| Isolation model | Description | Cost implication |
|---|---|---|
| Shared workspace on shared capacity | Multiple tenants share environment | Lowest cost, limited isolation |
| Separate workspaces on shared capacity | Logical separation, shared compute | Balanced |
| Dedicated capacity per tenant | Full isolation | Highest cost, strongest isolation |

**Evidence**: environment inventory (dev/test/prod); pause/resume schedule per env; isolation model for multi-tenant solutions.

### Reduce costs through automation

- Pause/scale capacities during off-hours (ARM APIs, Bicep, Terraform, Logic Apps, Power Automate, Fabric Pipelines, PowerShell)
- Autoscale billing for Spark and data warehousing workloads (pay for actual work)
- Optimize workload/storage operations (Delta table optimization, purge obsolete data, archive datasets, reduce log retention)
- Right-size capacities (Fabric Activator or custom scripts to track utilization and recommend smaller SKUs)
- Lifecycle management (auto-provision/scale/delete by schedule, expiration, priority)

Automation must respect the billing model: pausing a reserved capacity may not reduce cost.

**Evidence**: automation inventory (schedulers, scripts); autoscale enablement; right-sizing recommendation history.

### Consolidate costs effectively

- **Shared compute**: capacities host multiple workspaces and workloads; pool instead of separate
- **Shared data storage**: in-place data sharing across teams via shortcuts; reduces duplication
- **Environment-specific pooling**: dev/test workloads share capacity, paused outside working hours

> **Risk (from Learn)**: Sharing lowers cost but can impact performance (noisy neighbor). Highly variable or mission-critical workloads may need dedicated capacities. Fixed-capacity scaling creates large jumps; scale-out is smoother. Consolidation adds monitoring/governance complexity.

**Evidence**: workspace-to-capacity ratio; shortcut usage inventory (in-place sharing vs copy); consolidation candidates list.

---

## Evidence checklist (per principle)

- [ ] Capacity SKU + billing mix (PAYG/reserved): source: `[FabricAdmin]`
- [ ] Per-workspace CU consumption (last 14 days): source: `[Capacity Metrics App]`
- [ ] Storage growth trend (last 30 days): source: `[FabricAdmin]` + `[Capacity Metrics App]`
- [ ] Power BI Pro license inventory: source: `[user-interview]` + Entra admin
- [ ] Idle/oversized capacity report: source: `[fabric-cost-analysis accelerator]` or manual
- [ ] Surge protection settings: source: `[FabricAdmin]`
- [ ] Capacity-to-workspace tagging + ownership: source: `[FabricAdmin]`
- [ ] Budget alerts in Azure Cost Management: source: `[user-interview]`
- [ ] Pause/resume schedule for non-prod: source: `[user-interview]`
- [ ] Autoscale billing enablement: source: `[FabricAdmin]`
- [ ] Shortcut vs copy ratio for cross-team data: source: `[search-consumption-cli]`

---

## Cross-pillar tradeoffs

- **Cost ↔ Reliability**: Dedicated capacity + multi-region OneLake DR is more reliable but more expensive.
- **Cost ↔ Performance**: Smaller SKU with optimized queries can match larger SKU at lower cost: at the price of design effort.
- **Cost ↔ Security**: Managed VNets, private link, CMK, Sentinel all add cost; required by policy in regulated environments.
- **Cost ↔ Operational Excellence**: Automation reduces cost but takes engineering investment up front.

---

## See also

- `common/FABRIC-WAF-CORE.md`
- `references/tradeoffs.md`
- `fabric-cost-analysis` accelerator: https://github.com/microsoft/fabric-toolbox/tree/main/monitoring/fabric-cost-analysis
- Delegate skills: `sqldw-operations-cli`, `spark-operations-cli`, `search-consumption-cli`
