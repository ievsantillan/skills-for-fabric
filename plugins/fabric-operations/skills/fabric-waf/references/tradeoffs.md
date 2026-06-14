# Cross-pillar Tradeoffs

Microsoft Learn embeds tradeoffs as inline callouts within each pillar page (`> ![tradeoff-icon] **Tradeoff**: ...`). This file consolidates them in one place plus the cross-pillar implications the assessment surfaces. **Verbatim Microsoft Learn tradeoffs are quoted; cross-pillar synthesis is labeled as our analysis.**

> Re-fetch source pages when updating this file. See VERIFIED stamps on individual pillar references.

---

## Tradeoffs quoted verbatim from Microsoft Learn

### Reliability page

- **Zone-level vs cross-region redundancy**: "Zone-level redundancy is nearly invisible, but cross-region strategies require intentional design."
- **Redundancy vs cost/complexity**: "More redundancy reduces downtime and improves self-healing, but it comes at the cost of additional resources and operational complexity. Align your approach with the criticality of your workloads and your recovery expectations."
- **Immediate availability vs resource efficiency**: "Maintaining redundant capacities or regions ensures minimal downtime but increases cost and operational overhead. Relying on Fabric's built-in resiliency in a single region reduces cost but can introduce delays while failover or recovery processes complete."

### Security page

- **Isolation vs operational complexity**: "Adding more workspaces and capacities increases operational complexity and management overhead. But the payoff is localized failures, predictable access, and clear accountability."
- **CMK vs operational risk**: "Using CMK introduces operational dependencies. The key vault must remain available and accessible. If the key is disabled or deleted, workspace data becomes inaccessible until the key is restored. Key rotation, access policies, and audit controls also become your responsibility."

### Cost Optimization page

- **Consolidation vs noisy neighbor risk** (called out as a Risk callout): "Sharing capacities lowers costs but can impact performance: spikes in one workload may slow others (noisy neighbor issues). Highly variable or mission-critical workloads may need dedicated capacities. Fixed-capacity scaling can create large jumps in resources, so scaling out is often smoother. Consolidation also adds monitoring and governance complexity, especially when teams need clear visibility into their own usage."

### Operational Excellence page

- No standalone `Tradeoff` callouts on this page at time of verification. Treat `Important` callouts (e.g., "Manual checks are often needed for interactive elements like reports or dashboards. Approval processes should also scale with risk") as decision-shaping guidance.

### Performance Efficiency page

- No standalone `Tradeoff` callouts on this page at time of verification. Treat scaling guidance (vertical vs horizontal) and the smoothing/bursting/autoscale section as a tradeoff between deliberate planning and reactive elasticity.

---

## Cross-pillar synthesis (our analysis)

These tradeoffs are not quoted from Learn; they are the natural cross-pillar implications surfaced when running an assessment. Labeled as our analysis so they are not mistaken for Microsoft prescription.

| Tradeoff axis | Tension | When it shows up |
|---|---|---|
| **Reliability ↔ Cost** | Dedicated capacities + multi-region OneLake DR raise reliability and cost. | DR planning; mission-critical workload sizing. |
| **Reliability ↔ Performance** | Surge protection isolates noisy neighbors but caps peak utilization efficiency. | Multi-tenant capacity planning. |
| **Security ↔ Cost** | Managed VNets, private link, CMK, Sentinel each add cost. | Regulated industries; tenant hardening. |
| **Security ↔ Performance** | Application-side encryption-in-use adds CPU; DLP scanning adds latency on export. | Sensitive data ingestion + export. |
| **Security ↔ Operational Excellence** | PIM, approval gates, per-environment isolation add deploy friction. | Prod deployment cadence. |
| **Cost ↔ Performance** | Optimized architecture on a smaller SKU may match a larger SKU at lower cost: at the price of design and tuning effort. | SKU right-sizing. |
| **Cost ↔ Operational Excellence** | Comprehensive monitoring + multiple test environments cost more up front but reduce incident cost downstream. | Observability planning. |
| **Operational Excellence ↔ Reliability** | More moving parts (multiple capacities, deployment stamps) require disciplined CI/CD; automation creates new failure surfaces. | Multi-region or multi-capacity deployments. |
| **Performance ↔ Operational Excellence** | Complex caching / partitioning strategies add maintenance load. | Tuning mature workloads. |

---

## How tradeoffs appear in the assessment report

When a recommendation closes a gap in one pillar at material cost in another, the `Tradeoffs` section under that recommendation lists the affected pillar(s) and the specific cost. Example:

> **Recommendation**: Enable OneLake disaster recovery for the production capacity hosting workspace `<ID>`.
>
> **Tradeoffs**:
> - Cost: enables geo-replication storage charges for the OneLake content (see Cost Optimization, "Identify key cost drivers").
> - Operational Excellence: failover/failback runbooks become mandatory (see Operational Excellence, "Have an incident response plan").

---

## See also

- `common/FABRIC-WAF-CORE.md`: scoring rubric, recommendation format
- Pillar references for inline Learn quotes in context
