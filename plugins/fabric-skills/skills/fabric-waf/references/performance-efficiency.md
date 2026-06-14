<!-- VERIFIED: 2026-06-13 against https://learn.microsoft.com/en-us/azure/well-architected/microsoft-fabric/performance-efficiency -->

# Performance Efficiency: Fabric WAF Reference

## Source

Microsoft Learn: [Performance Efficiency for Microsoft Fabric workloads](https://learn.microsoft.com/en-us/azure/well-architected/microsoft-fabric/performance-efficiency)

> Re-fetch when authoring or updating this reference.

---

## Workload coverage matrix

| Workload | Coverage | Notes (from Learn page) |
|---|---|---|
| Lakehouse | Yes | Spark CU + memory; partitioning, parallel execution |
| Warehouse | Yes | SQL filter pushdown, Query Insights, DMVs called out |
| Real-Time Intelligence (Eventstream / Eventhouse / Activator) | Partial | Ingestion latency and event throughput called out; specific tuning less explicit |
| Data Factory (Pipelines / Dataflows Gen2) | Partial | Pipeline activity time + Data Factory UI for analysis called out |
| Data Science (notebooks / Data Agents) | Partial | Spark UI for jobs; Data Agents not explicitly covered |
| Mirroring | Partial | Ingestion latency implied; not explicitly called out |
| Power BI (semantic models / reports) | Yes | Memory, incremental refresh, query folding, aggregations, caching called out |
| OneLake | Yes | OneLake storage throughput dependency; caching layers |

---

## Pillar overview

Every design choice affects how Fabric operates and how users experience the solution. Goal: make user and data flows predictable, efficient, scalable. Lifecycle activities: plan capacity, monitor performance, test, tune for efficiency, scale confidently.

---

## Principles (Microsoft Learn H2s, verbatim)

### Plan capacity intentionally

Capacities provide compute in CUs. Every operation (Spark, SQL, pipeline activity, Power BI refresh) consumes CUs. Demand > available compute → slow / queue / throttle.

Start with the [Microsoft Fabric Capacity Estimator](https://www.microsoft.com/microsoft-fabric/capacity-estimator). Estimates aren't enough: establish a baseline by deploying representative workloads on a trial or small capacity and monitoring.

Baseline-phase metrics:

- CU consumption across workloads
- CPU and memory utilization (visible for some workload types, abstracted for others)
- Concurrency levels
- Response times for critical operations

[Fabric Capacity Metrics App](https://learn.microsoft.com/en-us/fabric/enterprise/metrics-app) reveals usage patterns over time (daily peaks, background processing). Account for SKU-specific limits: total CUs, Spark vCore limits, memory, throughput ceilings.

**Workload isolation** mitigates contention: separate heavy jobs across workspaces/capacities. **Capacity smoothing automatically distributes background workloads over a 24-hour period**, removing the need to schedule heavy work off-peak.

Dependencies often become the hidden constraint: OneLake throughput, external databases / APIs, network latency, on-prem gateways, Spark session configuration. Evaluate early.

For larger solutions, isolate architectural layers (prep / orchestration / presentation) across workspaces or capacities.

**Load testing**: simulate realistic workloads, gradually increase volume and concurrency. Test across all workload types. Monitor CU usage, throttling, response times. Short stress tests may miss issues smoothing hides over 24 hours: use longer test windows. Consider Workspace Monitoring during stress tests; also see [Fabric Toolbox](https://github.com/microsoft/fabric-toolbox).

**Evidence**: capacity-sizing rationale; baseline metrics; current SKU vs measured peak; load test results; dependency map; smoothing-aware test windows used.

### Choose SKU and Tiers Based on Performance Requirements

[Fabric SKU](https://learn.microsoft.com/en-us/fabric/enterprise/licenses#capacity) determines total CUs and memory. Larger capacity = more headroom for concurrency and memory-intensive workloads. But efficient architecture often matters more than raw size: pre-aggregate data in OneLake, enable query folding in Power BI, push heavy transformations into distributed Spark processing.

**Evidence**: current SKU vs workload requirements; architecture-vs-SKU tradeoff log.

### Design scaling strategies

Two dimensions:

- **Vertical**: upgrade to larger SKU. Provides more compute/memory/throughput for workloads that cannot easily distribute (large semantic model with many concurrent users; complex Spark pipeline). Fast; short pause during resize.
- **Horizontal**: distribute across multiple capacities. Works when workloads are modular or teams operate independently. Each workload gets dedicated resources; no contention. Fabric's compute/storage separation supports this: data prepared in one capacity is shared via OneLake without copying (data mesh patterns).

Keep components modular as architecture scales.

Signals to scale: consistently high CU utilization; slower interactive queries; rising query latency; memory-related failures.

Bursting, smoothing, capacity overage billing, autoscale billing absorb short-term spikes: complement, not replace, deliberate capacity planning.

**Evidence**: current vertical/horizontal layout; scaling decision log; signals tracked + thresholds.

### Monitor performance issues

Signals to watch:

- Capacity utilization (how much CU consumed)
- Memory usage (especially Power BI semantic models, Spark)
- Concurrency levels vs capacity limits
- Job execution metrics (query duration, dataset refresh, pipeline execution, Spark job runtime)
- Ingestion latency, event throughput per second (real-time)
- Capacity-related errors and throttling events

Tools (from Learn):

- [Capacity Metrics App](https://learn.microsoft.com/en-us/fabric/enterprise/metrics-app): top-level view
- [Real-Time Hub for Capacity Events](https://learn.microsoft.com/en-us/fabric/real-time-hub/explore-fabric-capacity-overview-events): live event monitoring
- Workspace/item-specific monitoring: Spark jobs, pipelines, semantic models
- Custom tracking: capture step durations / data processed when not native
- For deeper analysis: Query Insights, DMVs, Spark UI, Data Factory UI
- [Azure Monitor / Log Analytics](https://learn.microsoft.com/en-us/azure/azure-monitor/overview) for log integration
- Threshold-based alerts + [Fabric Activator](https://learn.microsoft.com/en-us/fabric/real-time-intelligence/data-activator/activator-introduction) to catch bottlenecks before user impact

Focus only on actionable issues. Review alerts regularly to avoid noise/fatigue. Always watch dependencies (external sources, gateways, network).

**Evidence**: monitored signals + thresholds; alert tuning history; Query Insights review samples; dependency-health dashboard.

### Do performance testing

Testing validates the design under real workloads.

- Simulate realistic usage patterns (not isolated operations)
- Tools: JMeter or Locust for concurrent requests; TPC-H / TPC-DS for analytical benchmarks
- Same mixture of workloads expected in prod (ingestion + analytics running together)
- Match production: same capacity size, region, network config
- Realistic data volumes and concurrency: performance does not scale linearly
- Capture: CU utilization, throughput, response time percentiles (p95, p99), error rates
- Continuous lightweight tests after deploy (scheduled "heartbeat" queries)

**Evidence**: test plan + results; capacity/region/network parity report; benchmark history; heartbeat probe + last failure date.

### Optimize performance

Query and transformation logic:

- Spark: well-defined partitions, parallel execution
- SQL: filters + aggregations reduce data processed
- Power BI: incremental refresh, query folding, aggregation tables

Caching layers (mostly automatic):

- OneLake local storage caches
- High-performance storage attached to compute nodes
- In-memory dataset caches
- Result-set caching for queries

Some caching configurable (e.g., RTI retention policies). Tuning can dramatically reduce query latency.

Platform features supporting efficient execution: autoscale and bursting for spikes; automatic statistics generation for analytical workloads.

Architectural patterns aligned with workload behavior: medallion for data transformation efficiency; event-driven pipelines to reduce unnecessary processing; data mesh to distribute workloads while sharing data.

**Evidence**: query-tuning review samples; caching configuration per workload; medallion / event-driven / data-mesh pattern usage.

---

## Evidence checklist (per principle)

- [ ] Capacity sizing rationale (estimator output + baseline): source: `[user-interview]` + `[Capacity Metrics App]`
- [ ] Throttling events (last 14 days): source: `[Capacity Metrics App]`
- [ ] Smoothing-aware load test results: source: `[user-interview]`
- [ ] Per-workload CU + memory + concurrency: source: `[Capacity Metrics App]`, `[spark-operations-cli]`, `[sqldw-operations-cli]`
- [ ] Slow query review (Warehouse): source: `[sqldw-operations-cli]`
- [ ] Stuck/failed Spark sessions: source: `[spark-operations-cli]`
- [ ] Power BI model size + measure complexity: source: `[semantic-model-consumption]`
- [ ] Caching configuration per workload: source: `[FabricAdmin]`
- [ ] Architectural pattern usage (medallion, event-driven, data mesh): source: `[user-interview]` + `[search-consumption-cli]`
- [ ] Dependency-health monitoring (external sources, gateways): source: `[user-interview]`

---

## Cross-pillar tradeoffs

- **Performance ↔ Cost**: Larger SKU is the easy lever; architectural optimization is the cheaper long-term lever.
- **Performance ↔ Reliability**: Push toward peak utilization hurts resilience headroom.
- **Performance ↔ Operational Excellence**: Complex caching/partitioning strategies add maintenance load.

---

## See also

- `common/FABRIC-WAF-CORE.md`
- `references/tradeoffs.md`
- Capacity Estimator: https://www.microsoft.com/microsoft-fabric/capacity-estimator
- Delegate skills: `spark-operations-cli`, `sqldw-operations-cli`, `semantic-model-consumption`, `eventhouse-consumption-cli`
