# Evidence Checklist

Consolidated per-pillar evidence items the assessment gathers. Each item is tagged with its source: `[FabricAdmin]`, `[<skill>-cli]`, `[Capacity Metrics App]`, `[user-interview]`, or a named accelerator. The per-pillar references contain the same checklists with deeper context; this file is the at-a-glance index.

> The complete principle-by-principle deep dive lives in each pillar reference. Use this file for delegation routing and scoping during Phase 3 (evidence gathering) of the assessment workflow.

> **Not available via the Fabric public REST API (as of this writing).** The following evidence requires the **Capacity Metrics App** (a Power BI semantic model, queried via DAX) or the **Fabric Admin portal**, not `az rest` against the Fabric REST API. Attempting `GET /v1/admin/capacities` for these returns 404 in some tenants. If you cannot reach those surfaces, mark the item `Not assessed` with the reason, or delegate to `FabricAdmin` (which may query the Metrics App semantic model). Do not infer a value:
>
> - Live smoothed CU utilization, throttling, and overage history: **Capacity Metrics App**
> - OneLake disaster-recovery (DR) toggle per capacity: **Admin portal** (capacity settings)
> - Surge protection settings per capacity / workspace: **Admin portal** (capacity settings)
> - Workspace Monitoring enablement status: **Workspace settings** (no public REST field found)

> **Microsoft Graph evidence requires the right token (Security pillar).** PIM (Privileged Identity Management) role schedules and sensitivity-label policies are read from Microsoft Graph, not the Fabric REST API, and are **not reachable with an Azure CLI (`az rest`) Graph token**: that first-party app lacks the `RoleManagement.Read.Directory` and `InformationProtection*` delegated scopes (returns HTTP 403 / 400). Use Microsoft Graph PowerShell (`Connect-MgGraph -Scopes "RoleManagement.Read.Directory","InformationProtectionPolicy.Read"`) or a custom app registration. Note also: an empty/400 sensitivity-label result is **not necessarily a licensing gap** (Microsoft 365 E5 already includes Purview Information Protection); confirm license vs deployment before scoring.

---

## Reliability

- [ ] Capacity + workspace + quota inventory: `[FabricAdmin]`
- [ ] Throttling / overage history (last 14 days): `[Capacity Metrics App]`
- [ ] OneLake DR configuration per capacity: `[FabricAdmin]` / Admin portal (not in public REST)
- [ ] Pipeline retry / idempotency code review: `[spark-operations-cli]`, `[dataflows-consumption-cli]`
- [ ] Documented SLOs / SLIs per workload: `[user-interview]`
- [ ] Surge protection settings per capacity / workspace: `[FabricAdmin]`
- [ ] DR simulation evidence (date, scope, result): `[user-interview]`
- [ ] Workspace Monitoring enabled status: `[FabricAdmin]`
- [ ] Health-check probe inventory: `[user-interview]`, `[activator-consumption-cli]`
- [ ] Dependency map (external systems and their SLAs): `[user-interview]`

## Security

- [ ] Tenant settings export: `[FabricAdmin]`
- [ ] RBAC inventory per workspace: `[FabricAdmin]`
- [ ] Workspace identity / service principal usage: `[FabricAdmin]`
- [ ] Conditional access policy list: `[user-interview]` + Entra admin
- [ ] PIM configuration for Fabric / Capacity Admin: `[user-interview]` + Entra admin
- [ ] Managed VNet + private link configuration: `[FabricAdmin]`
- [ ] On-prem gateway inventory + logs: `[FabricAdmin]`
- [ ] CMK enablement + Key Vault availability: `[FabricAdmin]`
- [ ] Sensitivity label coverage: `[FabricAdmin]` + `[search-consumption-cli]`
- [ ] Secret-in-code scan: `[spark-operations-cli]`, `[dataflows-consumption-cli]`, source-control scan
- [ ] SIEM integration + alert rule inventory: `[user-interview]`
- [ ] Audit log retention configuration: `[FabricAdmin]`
- [ ] Git integration + PR review enforcement: `[FabricAdmin]`
- [ ] Deployment pipeline approval gates: `[FabricAdmin]`

## Cost Optimization

- [ ] Capacity SKU + billing mix (PAYG / reserved): `[FabricAdmin]`
- [ ] Per-workspace CU consumption (last 14 days): `[Capacity Metrics App]`
- [ ] Storage growth trend (last 30 days): `[FabricAdmin]` + `[Capacity Metrics App]`
- [ ] Power BI Pro license inventory: `[user-interview]` + Entra admin
- [ ] Idle / oversized capacity report: `[fabric-cost-analysis accelerator]` or manual
- [ ] Surge protection settings: `[FabricAdmin]`
- [ ] Capacity-to-workspace tagging + ownership: `[FabricAdmin]`
- [ ] Budget alerts in Azure Cost Management: `[user-interview]`
- [ ] Pause / resume schedule for non-prod: `[user-interview]`
- [ ] Autoscale billing enablement: `[FabricAdmin]`
- [ ] Shortcut vs copy ratio for cross-team data: `[search-consumption-cli]`

## Operational Excellence

- [ ] Documented roles + on-call rotation: `[user-interview]`
- [ ] Certification inventory (DP-600, DP-700): `[user-interview]`
- [ ] Dev / test / prod workspace separation: `[FabricAdmin]`
- [ ] Deployment pipeline configuration: `[FabricAdmin]`
- [ ] Git integration coverage: `[FabricAdmin]`
- [ ] IaC repository for capacities / workspaces: `[user-interview]`
- [ ] Monitoring tool enablement matrix (Capacity Metrics App, Workspace Monitoring, OneLake Diagnostics, FUAM): `[FabricAdmin]`
- [ ] Alert rule inventory + escalation: `[user-interview]`
- [ ] Audit log retention / export beyond 30 days: `[FabricAdmin]`
- [ ] BCDR enablement on critical capacities: `[FabricAdmin]`
- [ ] Last DR drill date + result: `[user-interview]`
- [ ] Test suite inventory per layer: `[user-interview]`

## Performance Efficiency

- [ ] Capacity sizing rationale (estimator output + baseline): `[user-interview]` + `[Capacity Metrics App]`
- [ ] Throttling events (last 14 days): `[Capacity Metrics App]`
- [ ] Smoothing-aware load test results: `[user-interview]`
- [ ] Per-workload CU + memory + concurrency: `[Capacity Metrics App]`, `[spark-operations-cli]`, `[sqldw-operations-cli]`
- [ ] Slow query review (Warehouse): `[sqldw-operations-cli]`
- [ ] Stuck / failed Spark sessions: `[spark-operations-cli]`
- [ ] Power BI model size + measure complexity: `[semantic-model-consumption]`
- [ ] Caching configuration per workload: `[FabricAdmin]`
- [ ] Architectural pattern usage (medallion, event-driven, data mesh): `[user-interview]` + `[search-consumption-cli]`
- [ ] Dependency-health monitoring (external sources, gateways): `[user-interview]`

---

## Delegation summary

| Skill | Used by pillars |
|---|---|
| `FabricAdmin` (agent) | All five (primary source for tenant/workspace evidence) |
| `Capacity Metrics App` (cited, not a skill) | Reliability, Cost Optimization, Operational Excellence, Performance Efficiency |
| `search-consumption-cli` | Security, Cost Optimization, Performance Efficiency |
| `sqldw-consumption-cli` | Security |
| `sqldw-operations-cli` | Performance Efficiency, Cost Optimization |
| `spark-operations-cli` | Reliability, Security, Operational Excellence, Performance Efficiency |
| `semantic-model-consumption` | Performance Efficiency |
| `dataflows-consumption-cli` | Reliability, Security, Operational Excellence |
| `eventstream-consumption-cli` | Reliability |
| `eventhouse-consumption-cli` | Reliability, Performance Efficiency |
| `activator-consumption-cli` | Reliability, Operational Excellence |

`-authoring-cli` skills are intentionally **not** in this routing table. Per the read-only trust boundary in `common/FABRIC-WAF-CORE.md`, the assessment phase reads only. The Phase 6 export step uses `powerbi-report-authoring` and `semantic-model-authoring` for local PBIP generation (no Fabric tenant mutation). The Phase 7 publish step (opt-in only) uses `powerbi-report-management`.
