<!-- VERIFIED: 2026-06-20 against https://github.com/microsoft/fabric-toolbox/tree/main/monitoring -->

# Fabric Toolbox Monitoring Accelerators

The [Microsoft Fabric Toolbox `monitoring/` folder](https://github.com/microsoft/fabric-toolbox/tree/main/monitoring) contains five solution accelerators that close the monitoring/observability gaps surfaced by the Reliability, Security, Operational Excellence, Performance Efficiency, and Cost Optimization pillars.

> **Caveat (state this when recommending any of these).** These are **community solution accelerators, not official Microsoft products**, with no official support. FUAM and fabric-cost-analysis extract from the **Capacity Metrics App** semantic model, whose internals can change without notice and break extraction. FUAM and fabric-cost-analysis are additionally referenced by the Microsoft Learn WAF pages (Operational Excellence and Cost Optimization respectively); the other three are not Learn-cited at the time of verification.

## Catalog

| Accelerator | What it is | Key data sources | Cadence |
|---|---|---|---|
| **FUAM** (fabric-unified-admin-monitoring) | Tenant-wide admin "single pane of glass" built on Pipelines/Notebooks/Lakehouse/Semantic Models/Power BI | Tenant settings, activities, workspaces, capacities, Capacity Metrics, Scanner API metadata, Capacity Refreshables, Git connections | Batch (initial + incremental) |
| **fabric-platform-monitoring** | Real-Time Intelligence (RTI) platform observability with independent modules | Capacity Events (Real-Time Hub), audit/activity events (Eventhouse, ~2-min), on-prem gateway logs, tenant inventory | Near-real-time |
| **workspace-monitoring-dashboards** | Pre-built PBI Report + RTI Dashboard templates on top of the built-in Workspace Monitoring feature | Per-workspace diagnostics KQL DB: Semantic Models, Eventhouse, Mirrored DBs, GraphQL traces | Built-in feature; report templates |
| **fabric-cost-analysis** (FCA) | FinOps cost monitoring with chargeback/showback | Azure cost in FOCUS format, reservations, quotas, capacity usage | Batch |
| **fabric-spark-monitoring** | Spark workload performance monitoring | Spark emitter diagnostics into Eventhouse (cluster health, memory/CPU/shuffle/spill); On-Demand pools only (not starter pools) | Per Spark session |

## Which to use when

- **Tenant/capacity admin wanting holistic oversight + long-term CU trends** -> **FUAM**. Best single starting point for governance, capacity utilization history, and right-sizing inputs.
- **Near-real-time reaction, security/audit event streaming (feed a SIEM), or on-prem gateway monitoring** -> **fabric-platform-monitoring**. The RTI activity-events module is the natural source for a Microsoft Sentinel pipeline.
- **Single-workspace diagnostics: root-cause, query/refresh traces, anomaly detection** -> **workspace-monitoring-dashboards** (enable the built-in Workspace Monitoring feature first).
- **Cost attribution, chargeback per team, reservation rationalization (FinOps)** -> **fabric-cost-analysis**.
- **Tuning Spark / notebook performance and finding bottlenecks** -> **fabric-spark-monitoring** (requires On-Demand pools).

## Mapping to WAF pillars

| Pillar | Primary accelerator(s) |
|---|---|
| Reliability ("Monitor metrics and observe proactively") | workspace-monitoring-dashboards (workspace), FUAM (capacity/tenant), fabric-platform-monitoring (real-time) |
| Security ("Security monitoring") | fabric-platform-monitoring (audit/activity -> SIEM), FUAM (tenant-settings drift) |
| Operational Excellence (observability, incident response) | FUAM, fabric-platform-monitoring |
| Performance Efficiency (monitoring, optimization) | fabric-spark-monitoring, workspace-monitoring-dashboards, FUAM (CU) |
| Cost Optimization (cost drivers, governance) | fabric-cost-analysis, FUAM (long-term CU) |

## See also

- `common/FABRIC-WAF-CORE.md` § SDK / API landscape
- `references/evidence-checklist.md` (Capacity Metrics App sourcing)
- Microsoft Fabric Toolbox monitoring folder: https://github.com/microsoft/fabric-toolbox/tree/main/monitoring
