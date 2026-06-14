<!-- VERIFIED: 2026-06-13 against https://learn.microsoft.com/en-us/azure/well-architected/microsoft-fabric/operational-excellence -->

# Operational Excellence: Fabric WAF Reference

## Source

Microsoft Learn: [Operational excellence for Microsoft Fabric workloads](https://learn.microsoft.com/en-us/azure/well-architected/microsoft-fabric/operational-excellence)

> Re-fetch when authoring or updating this reference.

---

## Workload coverage matrix

| Workload | Coverage | Notes (from Learn page) |
|---|---|---|
| Lakehouse | Yes | Spark transformation skills called out under team readiness |
| Warehouse | Yes | Deployment pipelines and Git integration apply |
| Real-Time Intelligence (Eventstream / Eventhouse / Activator) | Partial | Activator called out under monitoring/automation; deployment specifics implied |
| Data Factory (Pipelines / Dataflows Gen2) | Yes | Pipeline CI/CD, parameterization, deployment pipelines called out |
| Data Science (notebooks / Data Agents) | Partial | Notebook testing tools (pytest, nutter) called out; Data Agents not explicitly covered |
| Mirroring | Partial | Inherits monitoring surface; not explicitly called out |
| Power BI (semantic models / reports) | Yes | Semantic model and report deployment via deployment pipelines |
| OneLake | Yes | OneLake Diagnostics for data-access monitoring |

---

## Pillar overview

Fabric is SaaS: Microsoft handles infrastructure ops. You handle workload operations: team readiness, safe deployment, automation, monitoring, incident response, and testing. The goal is deliberate choices, understood tradeoffs, and confidence to operate/scale/recover.

---

## Principles (Microsoft Learn H2s, verbatim)

### Prepare your team

Map the people, skills, and responsibilities. Data engineers fluent in Spark, Lakehouse, Power BI semantic models. Capacity admins understand CUs, storage, workspace boundaries. DevOps skills (shared ownership, CI/CD, incident response) are not optional. Document role/responsibility boundaries: who owns capacity monitoring, who approves prod deployment, who is on call. Formalize via certifications:

- **DP-600** (Microsoft Certified: Fabric Analytics Engineer Associate)
- **DP-700** (Microsoft Certified: Fabric Data Engineer Associate)

Entra ID and networking knowledge is essential.

**Evidence**: org chart with Fabric roles; on-call rotation; certification inventory; documented role boundaries.

### Deploy changes safely

Match deployment rigor to workload complexity and impact. Compartmentalize: separate workspaces for dev/test/prod. Use **Fabric Deployment Pipelines** for structured deployment; complement with GitHub Actions / Azure DevOps for custom logic. Test before promotion: unit, integration, data validation, business verification.

> **Important (from Learn)**: Manual checks are needed for interactive elements (reports, dashboards). Approval processes scale with risk: automated for non-prod; code review + testing + manual sign-off for prod.

Monitoring and progressive exposure make deploys controlled. Capture logs, configure failure alerts, roll out gradually. **Fabric has no one-click rollback**: your safety net is redeploying from Git or pipelines. Data consistency is the real rollback risk, not just code; multiple data stores may require careful reconciliation.

**Evidence**: dev/test/prod workspace separation; deployment pipeline configuration; test coverage by workload type; approval gates per environment; rollback runbook.

### Automate operations

Automate repetitive / high-touch tasks. Common candidates (from Learn):

- Workspace provisioning and capacity assignment
- Deployment / CI/CD pipelines
- Capacity monitoring, scaling, utilization alerts
- Job monitoring, scheduling, retries, failure notifications
- Access management
- Maintenance (obsolete artifacts, underutilized capacities)

Native: job scheduling, deployment pipelines, capacity monitoring, **Fabric Activator** for event-driven workflows. External: REST APIs + CLI, Terraform, Git integration.

#### Drive deployment through code

Use IaC to define capacities, workspaces, artifacts. Layered model (from Learn):

1. Core environment (Azure subscription, identity, monitoring, governance)
2. Fabric platform resources (capacities, logging integration)
3. Workspaces + security + Git integration
4. Solution components (Lakehouses, pipelines, notebooks, semantic models)
5. Promote across environments via deployment pipelines

Parameterize capacity SKUs, environment-specific endpoints, security roles, refresh schedules. Git as source of truth: detects drift and provides version control. Pipelines orchestrate IaC + Fabric solutions; use **GitHub Actions / Azure DevOps / Fabric Deployment Pipelines**. Validate with pre/post-deployment checks, unit/integration tests, environment-specific validations. Pipelines enforce approvals for prod and capture logs / trigger alerts on failures. Variable libraries and parameterization handle environment differences; **Fabric-CICD library** handles complex config changes.

**Evidence**: IaC repository + layer structure; pipeline definitions; Git integration coverage; variable library / parameter file; drift-detection mechanism.

### Monitor your environment

Need visibility at multiple layers: tenant-wide (admins), capacity health (ops), workspace-level (workload owners). **Workspace Monitoring** captures logs/metrics for supported workloads into a workspace Eventhouse.

Focus signals: capacity utilization + throttling events; storage usage/growth; user activity / operational logs; job execution metrics (failures, retries, duration); deployment success/failure.

Tools (from Learn):

| Tool | Purpose | Typical use |
|---|---|---|
| [Microsoft Fabric Capacity Metrics App](https://learn.microsoft.com/en-us/fabric/enterprise/metrics-app) | Capacity health & compute | CU consumption, throttling, autoscale, storage over 14-day window |
| [Workspace Monitoring](https://learn.microsoft.com/en-us/fabric/data-factory/workspace-monitoring) | Workload-level observability | Logs/metrics for supported workloads within a workspace |
| [OneLake Diagnostics](https://learn.microsoft.com/en-us/fabric/onelake/onelake-diagnostics-overview) | Data-access activity | Storage-related investigation |
| [Fabric Activator](https://learn.microsoft.com/en-us/fabric/real-time-intelligence/data-activator/activator-introduction) | Event-driven monitoring/automation | Trigger alerts / actions on Fabric events |
| [FUAM](https://github.com/microsoft/fabric-toolbox/tree/main/monitoring/fabric-unified-admin-monitoring) | Consolidated tenant-wide monitoring | Aggregate monitoring data across the tenant |
| [Azure Monitor / Log Analytics](https://learn.microsoft.com/en-us/azure/azure-monitor/overview) | External monitoring / long-term | Store, query, visualize exported logs/metrics |
| [Microsoft 365 Audit Logs](https://learn.microsoft.com/en-us/fabric/admin/service-admin-portal-audit-logs) | User and admin activity | Capture and forward Fabric audit logs |

#### Manage monitoring data

Default retention is limited:

- **Fabric activity logs**: 30 days
- **Capacity Metrics App data**: 14 days

For longer history, export logs externally. FUAM helps retain and analyze across longer periods. Workspace Monitoring and OneLake Diagnostics can grow rapidly: enable selectively/temporarily.

#### Create dashboards and alerts

Capacity Metrics App provides built-in dashboards. **Fabric Activator** triggers alerts and automated actions on events. Admins can enable email notifications for service outages. Built-in notifications for job failures (semantic model refresh, pipeline). Alerts must be meaningful and actionable; false alarms erode trust. Multi-channel notifications (email, Teams). Escalation paths for high-severity.

**Evidence**: monitoring tool enablement (Capacity Metrics App, Workspace Monitoring, OneLake Diagnostics, FUAM, Sentinel/Azure Monitor); alert inventory + thresholds; escalation matrix; log export configuration + retention beyond defaults.

### Have an incident response plan

Operational procedures for service disruptions and platform failures plus workload incidents.

#### Understand failover capabilities

Zone redundancy (support varies by region/workload). **BCDR** replicates OneLake to secondary region when enabled. Regional failover is Microsoft-initiated; recovery operations are yours: create capacities in alternate region, redeploy items + workspaces, rehydrate from replicated OneLake, restore + validate.

Common practice: parallel deployments in multiple regions; simulate failure by pausing capacity in one region. Periodic non-prod drills.

#### Execute failback procedures

After primary returns, careful validation: reconcile data changes, verify data store integrity. May require redeploying workspaces or restoring data. Versioned artifacts + Git history support safe roll-forward.

#### Detect failures

Fabric relies on internal monitoring for infrastructure failures. You cannot initiate platform failover. Operational monitoring focuses on **solution-level** failures: pipeline errors, workload disruptions, deployment issues. Combine health monitoring with CI/CD pipeline error detection that stops promotions on failure.

**Evidence**: documented incident response plan; BCDR enablement on critical capacities; failover/failback runbook; last DR drill date + result; alternate-region readiness; CI/CD-failure-stops-promotion enforcement.

### Don't assume everything works

Validate every layer (from Learn):

| Test Level | Purpose | Example |
|---|---|---|
| Artifact tests | Validate individual components | Test a notebook transformation or pipeline logic |
| Integration tests | Validate full data workflow | Ingestion → transformation → model refresh |
| Data quality validation | Detect data issues early | Schema changes, missing values |
| Load testing | Understand performance limits | Production-scale data through pipelines/queries |
| User acceptance testing | Confirm business requirements | Business users validate reports/outputs |

Dedicated test workspaces and capacities that represent prod. Anonymized data. Smaller test capacities scaled up during load tests.

Tools (from Learn):

- Notebook testing: pytest, nutter
- Data validation: Great Expectations
- CI/CD: Azure DevOps, GitHub Actions
- Automation testing: Fabric REST APIs
- Custom integration: Python, PowerShell

**Evidence**: test suite inventory per layer; test workspace + capacity; data anonymization approach; last UAT cycle date.

---

## Evidence checklist (per principle)

- [ ] Documented roles + on-call rotation: source: `[user-interview]`
- [ ] Certification inventory (DP-600, DP-700): source: `[user-interview]`
- [ ] Dev/test/prod workspace separation: source: `[FabricAdmin]`
- [ ] Deployment pipeline configuration: source: `[FabricAdmin]`
- [ ] Git integration coverage: source: `[FabricAdmin]`
- [ ] IaC repository for capacities/workspaces: source: `[user-interview]`
- [ ] Monitoring tool enablement matrix: source: `[FabricAdmin]`
- [ ] Alert rule inventory + escalation: source: `[user-interview]`
- [ ] Audit log retention / export: source: `[FabricAdmin]`
- [ ] BCDR enablement on critical capacities: source: `[FabricAdmin]`
- [ ] Last DR drill date + result: source: `[user-interview]`
- [ ] Test suite inventory per layer: source: `[user-interview]`

---

## Cross-pillar tradeoffs

- **OpEx ↔ Cost**: IaC + comprehensive monitoring + extra test environments cost more up front; payoff in reduced incidents.
- **OpEx ↔ Reliability**: More automation reduces human error but creates a new failure surface (the automation itself).
- **OpEx ↔ Security**: Approval gates and PIM add deploy friction; required for prod.

---

## See also

- `common/FABRIC-WAF-CORE.md`
- `references/tradeoffs.md`
- FUAM: https://github.com/microsoft/fabric-toolbox/tree/main/monitoring/fabric-unified-admin-monitoring
- Delegate skills: `spark-operations-cli`, `sqldw-operations-cli`, `activator-consumption-cli`, `dataflows-consumption-cli`
