<!-- VERIFIED: 2026-06-13 against https://learn.microsoft.com/en-us/azure/well-architected/microsoft-fabric/reliability -->

# Reliability: Fabric WAF Reference

## Source

Microsoft Learn: [Reliability considerations for Microsoft Fabric workloads](https://learn.microsoft.com/en-us/azure/well-architected/microsoft-fabric/reliability)

> Re-fetch this page when authoring or updating this reference. Bump the VERIFIED stamp above when content has been re-checked against the live page.

---

## Workload coverage matrix

| Workload | Coverage | Notes (from Learn page) |
|---|---|---|
| Lakehouse | Yes | OneLake replication; Delta time travel for recovery |
| Warehouse | Yes | Capacity-bound; see "Start with constraints" + Warehouse limitations link from Learn |
| Real-Time Intelligence (Eventstream / Eventhouse / Activator) | Partial | Eventhouses called out under specialized workloads; Activator suitable for self-preservation alerting |
| Data Factory (Pipelines / Dataflows Gen2) | Yes | Pipeline retry, idempotency, modular design covered in "Self-preservation" |
| Data Science (notebooks / Data Agents) | Partial | Notebook limitations link from Learn; Data Agents not explicitly covered by Learn page |
| Mirroring | Partial | Inherits OneLake replication; mirroring-specific failure modes not explicitly covered |
| Power BI (semantic models / reports) | Yes | Semantic model refresh + concurrent query patterns called out |
| OneLake | Yes | Multiple copies; geo-replication for DR; central to redundancy story |

"Partial" cells mean Microsoft Learn does not explicitly call the workload out under this pillar at the time of verification. Score those areas conservatively and note the gap in the evidence appendix.

---

## Pillar overview

Reliability in Microsoft Fabric is a continuous design discipline: know your platform constraints, plan redundancy at the right layer, scale smartly, monitor proactively, and rehearse disaster recovery. Fabric is SaaS, so infrastructure tweaks are not in your hands: your reliability levers are workspace design, capacity layout, idempotency, modularity, and observability. The platform offers strong defaults (compute failover, OneLake replication, automatic service restart), but your architecture decisions determine how far that protection extends.

---

## Principles (Microsoft Learn H2s, verbatim)

### Start with constraints: know your boundaries

Every Fabric capacity defines a finite compute/memory envelope. Subscription quotas can add further limits. Workspaces are isolation boundaries; some preview features and Private Endpoint configurations behave differently per workspace. Fabric is SaaS: you cannot tune infrastructure directly. Your levers: move workloads across capacities, separate critical pipelines, use multi-capacity patterns, request quota increases before hitting hard limits.

**Evidence to gather**: workspace inventory with assigned capacity; documented quotas per capacity; list of known-issues/preview-constraints that apply to the in-scope workloads; dependency map.

**Learn link-outs**: Data warehouse limitations, Data engineering notebook limitations, Workspace fundamentals (cite by verbatim heading text).

### Understand where failures happen

Failures cluster around two sources: resource limits (Spark/pipeline saturation) and external dependencies (upstream gateways, databases). Infrastructure failures including regional outages are rare but possible. Specialized workloads (dedicated databases, Eventhouses) behave differently under partial failure. Map your failure points.

> **Tip (from Learn)**: Always map out dependencies and capacity constraints. Visualizing failure points helps target monitoring and mitigation effort.

**Evidence**: dependency map; list of external systems with their SLAs; throttling history from Capacity Metrics App.

### Define reliability goals for your workloads

Fabric guarantees 99.9% platform uptime. Pipelines, Spark jobs, and Power BI reports may need tighter operational targets. Define SLIs: pipeline success rates, job completion times, execution latency, capacity utilization. Account for external dependency availability. Be realistic about recovery targets: localized issues resolve in minutes, regional outages take longer. Document SLOs/SLIs in runbooks and dashboards.

**Evidence**: documented SLOs per workload; SLI dashboards; runbooks; recovery-target table per workload.

### Build self-healing through redundancy

Self-healing is the first line; redundancy enables it. Three layers:

| Level | How it works | What you control |
|---|---|---|
| **Instance-level** | Individual node failover automatic | Ensure workloads resume without manual intervention |
| **Zone-level** | Azure Availability Zones spread workloads across physical locations within a region | Fabric uses AZs when supported by region/workload; no customer configuration required |
| **Region-level** | Geo-replication for DR | You decide which capacities enable Disaster Recovery for OneLake, which workspaces are active where, and how failover is orchestrated |

> **Tradeoff (from Learn)**: Zone-level redundancy is nearly invisible; cross-region strategies require intentional design.
>
> **Tradeoff (from Learn)**: More redundancy reduces downtime but adds resource cost and operational complexity. Align approach with workload criticality.
>
> **Tradeoff (from Learn)**: Immediate availability vs resource efficiency. Maintaining redundant capacities/regions ensures minimal downtime but increases cost; single-region built-in resiliency reduces cost but adds recovery delay.

Design choices that enable self-healing: dedicated capacities for critical workloads, modular pipelines, idempotent operations, retries with exponential backoff, circuit breakers, graceful degradation, isolation to prevent cascading failures.

**Evidence**: capacity-to-workspace assignment table; OneLake DR configuration per capacity; pipeline idempotency checklist; retry/backoff policy documentation.

### Scale vertically and horizontally with reliability

Allocate to peak for predictable workloads; rely on bursting and smoothing for spikes. Treat each capacity as a self-contained unit. Distribute heavy workloads across multiple workspaces and capacities. Use autoscale billing for elastic Spark/data warehousing workloads. Apply surge protection at capacity and workspace level. Enable capacity overage billing as a safety net. Use graceful shutdowns and retry logic for long-running jobs.

> **Important (from Learn)**: Don't wait until a capacity is maxed out. Maintain a buffer and enable capacity overage billing.

**Evidence**: scaling policy per capacity; surge-protection configuration; autoscale billing setting per applicable capacity; capacity headroom over the last 14 days (Capacity Metrics App).

### Monitor metrics and observe proactively

Track service availability, pipeline success, job runtimes, capacity usage, and external dependency health (on-prem gateways, APIs, internal services). Pair Fabric telemetry with health probes and dashboards. Integrate with Azure Monitor. Correlate logs and metrics to find root cause.

**Evidence**: list of monitored signals + alert thresholds; Workspace Monitoring enablement status; Azure Monitor / Log Analytics integration; on-prem gateway log surface.

### Apply self-preservation techniques

- Dedicated capacities for critical workloads (isolate from noisy neighbors)
- Autoscale billing for elastic Spark and data warehousing workloads
- Surge protection at capacity and workspace level
- Capacity overage billing as a safety net
- Modular workloads (small independent pieces)
- Idempotent operations (retries safe against duplicate writes)
- Retry logic with exponential backoff + alerting
- Circuit breakers around failing dependencies
- Graceful degradation (skip non-critical steps, serve cached/read-only when needed)
- Health checks tied to recovery actions
- Isolation: separate workspaces/capacities; no single points of failure in shared dependencies

**Evidence**: per-capacity isolation matrix; retry policy code samples; circuit breaker presence in pipeline definitions; health-check inventory.

### Plan for disaster recovery

Most Fabric items rely on continuous replication, not traditional backups. OneLake keeps multiple copies and can geo-replicate to paired regions, but asynchronous replication may lead to minor data loss in catastrophic events. Manual backups are still required for critical assets outside OneLake. Understand RTO/RPO, simulate failovers regularly, practice restores in non-production.

> **Important (from Learn)**: Don't wait for a real incident to find out the plan doesn't work. Simulate outages, execute failover, practice failback, measure recovery times, validate data integrity.

**Evidence**: documented RTO/RPO per workload; last DR simulation date; failover/failback runbooks; backup coverage for non-OneLake assets.

### Test reliability

Direct chaos testing inside Fabric is not available. Validate environment and dependencies: simulate adverse conditions (break source connectivity, inject load to trigger throttling, use Azure Chaos Studio for network latency/downtime on supporting resources). Use planned maintenance windows to test failover and recovery.

**Evidence**: reliability test plan; last test execution log; dependency-failure rehearsal records.

---

## Evidence checklist (per principle)

- [ ] Capacity + workspace + quota inventory: source: `[FabricAdmin]`
- [ ] Throttling/overage history (last 14 days): source: `[Capacity Metrics App]`
- [ ] OneLake DR configuration per capacity: source: `[FabricAdmin]` or REST API
- [ ] Pipeline retry/idempotency code review: source: `[spark-operations-cli]`, `[dataflows-consumption-cli]`
- [ ] Documented SLOs/SLIs per workload: source: `[user-interview]`
- [ ] Surge protection settings per capacity/workspace: source: `[FabricAdmin]`
- [ ] DR simulation evidence (date, scope, result): source: `[user-interview]`
- [ ] Workspace Monitoring enabled status: source: `[FabricAdmin]`
- [ ] Health-check probes inventory: source: `[user-interview]` + `[activator-consumption-cli]`
- [ ] Dependency map (external systems and their SLAs): source: `[user-interview]`

---

## Cross-pillar tradeoffs

- **Reliability ↔ Cost**: Redundancy (dedicated capacities, multi-region OneLake DR) materially increases cost. Tier by workload criticality.
- **Reliability ↔ Performance**: Surge protection and isolation reduce noisy-neighbor risk but may reduce peak utilization efficiency.
- **Reliability ↔ Operational Excellence**: More moving parts (multiple capacities, deployment stamps) require disciplined CI/CD and runbooks.

---

## See also

- `common/FABRIC-WAF-CORE.md`: scoring rubric, recommendation format, glossary
- `references/tradeoffs.md`: cross-pillar tradeoffs in detail
- `references/assessment-workflow.md`: how to gather this evidence
- Delegate skills: `spark-operations-cli`, `sqldw-operations-cli`, `eventhouse-consumption-cli`, `activator-consumption-cli`, `dataflows-consumption-cli`
