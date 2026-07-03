<!-- VERIFIED: 2026-06-13 against https://learn.microsoft.com/en-us/azure/well-architected/microsoft-fabric/security -->

# Security: Fabric WAF Reference

## Source

Microsoft Learn: [Security considerations for Microsoft Fabric workloads](https://learn.microsoft.com/en-us/azure/well-architected/microsoft-fabric/security)

> Re-fetch when authoring or updating this reference. Bump the VERIFIED stamp above when content has been re-checked.

---

## Workload coverage matrix

| Workload | Coverage | Notes (from Learn page) |
|---|---|---|
| Lakehouse | Yes | OneLake encryption (AES-256), workspace boundary, item-level permissions |
| Warehouse | Yes | RBAC, item-level permissions, audit log surface |
| Real-Time Intelligence (Eventstream / Eventhouse / Activator) | Partial | Inherits workspace/identity model; not explicitly called out by Learn page |
| Data Factory (Pipelines / Dataflows Gen2) | Partial | Secret management for connections covered; pipeline-specific hardening implied |
| Data Science (notebooks / Data Agents) | Yes | Notebooks called out under "Secret management": no secrets in code |
| Mirroring | Partial | Inherits source-system identity and OneLake encryption; not explicitly called out |
| Power BI (semantic models / reports) | Yes | Sensitivity labels, external sharing, DLP, role-level security implied |
| OneLake | Yes | AES-256 at rest, CMK option, encryption-in-transit via TLS 1.2+ |

---

## Pillar overview

Security in Microsoft Fabric is the intentional layering of baseline policy, isolation boundaries, Zero Trust identity controls, network constraints, encryption, asset hardening, secret management, monitoring, testing, and SDL. Fabric provides strong defaults (TLS 1.2+, AES-256 at rest, Entra-everywhere), but defaults favor usability over strict security. Hardening is your responsibility.

---

## Principles (Microsoft Learn H2s, verbatim)

### Start with a baseline

Define a security baseline before configuring rules. Use the [Microsoft Fabric baseline](https://learn.microsoft.com/en-us/security/benchmark/azure/baselines/fabric-security-baseline) aligned with the Microsoft Cloud Security Benchmark (MCSB) as a starting point: not a checklist. Compare current tenant configuration to the baseline; mitigate gaps early.

**Evidence**: documented security baseline; tenant configuration export (Fabric admin settings); gap-to-baseline mapping.

### Design isolation boundaries

Workspaces are the first line of defense. Map them to teams, projects, or environments. Use item-level permissions within workspaces for finer control. Capacities can be deployed in specific regions for data residency; separate capacities also isolate admin responsibility.

> **Tradeoff (from Learn)**: Adding more workspaces and capacities increases operational complexity. Payoff: localized failures, predictable access, clear accountability.

**Evidence**: workspace-to-team mapping; item-level permission inventory for sensitive items; capacity-region map.

### Use identity as the foundation for Zero Trust security controls

Everything in Fabric flows through Entra ID. Enforce least privilege. Built-in roles: Viewer reads, Contributor modifies, Admin manages. Use **workspace identity** for external resource access (managed service principal per workspace, no embedded credentials). Service principals for app-to-Fabric automation. Examine tenant settings for who can create workspaces. Use conditional access policies (MFA, compliant devices, location). Use PIM for administrative roles. Tenant/Capacity roles separate management of compute/storage from content access (Capacity Admin manages scaling but cannot read sensitive datasets).

**Evidence**: tenant settings for workspace creation; RBAC inventory per in-scope workspace; conditional access policy list; PIM configuration for Fabric Admin and Capacity Admin roles; workspace identity usage for external connections; service principal inventory.

### Secure network communications

Client connections use HTTPS with TLS 1.2+. Edge protected by Azure Front Door + WAF + DDoS. Limit exposure via conditional access, IP allow-lists. For workload-to-data-source connectivity, use private network paths where possible: **managed VNets** (compute in isolated segment, connections via managed private endpoints), **private link** (Fabric exposed via private endpoint inside your VNet, NSGs and Azure Firewall apply). Workspace-level IP firewall rules restrict client IPs. **On-premises data gateway** for on-prem systems (encrypted outbound). **Workspace outbound access protection** to block all outbound and allow only approved external resources. Monitor via private link logs and on-prem gateway logs.

**Evidence**: managed VNet enablement per workspace; private link configuration; workspace IP firewall rules; on-prem gateway inventory + logs; workspace outbound access protection state.

### Data encryption

At rest: AES-256 with Microsoft-managed keys (OneLake + analytical stores). In transit: HTTPS / TLS 1.2+ (Microsoft manages certificates). **No built-in encryption in use**: if required, the application must encrypt sensitive values before ingestion. **CMK option** for stricter requirements (double encryption; key stored in Azure Key Vault); not all artifacts support CMK so workspace segmentation may be needed.

> **Tradeoff (from Learn)**: CMK introduces operational dependencies. Key Vault must remain available. If the key is disabled/deleted, workspace data becomes inaccessible until restored. Key rotation, access policies, and audit controls become your responsibility.

**Evidence**: CMK enablement state per applicable workspace; Key Vault availability/audit configuration; list of artifact types in scope that do/don't support CMK.

### Harden workload assets

Fabric attack surface is web endpoints, APIs, and loaded content. Since Fabric is SaaS, hardening focuses on configuration and governance. Disable unused features (external sharing, "anyone with the link"). Use private link instead of public endpoints. Key hardening steps from Learn:

- Restrict workspace creation to admins
- Enforce sensitivity labels on all content; block exports for sensitive data
- Disable basic auth for data sources where alternatives exist (prefer OAuth, managed identity, service principal)
- Templatize workspace configurations

Restrict administrative role assignments; use PIM. Track configuration via admin APIs or scripts; compare against baseline to detect drift.

**Evidence**: tenant settings export; sensitivity label coverage per workspace; auth method per data source; configuration drift report.

### Secret management

Do not store secrets in notebooks, scripts, or pipelines. Use **Azure Key Vault** with dynamic retrieval at runtime. Rotate secrets in coordination with dependent workloads. Prefer workspace identity or service principals over static credentials.

**Evidence**: secret-in-code scan results (notebooks, pipeline definitions, dataflows); Key Vault usage inventory; rotation cadence per secret category.

### Security monitoring

Fabric records user/admin activity in audit logs (who, what, when, where). Combine with **Purview DLP**, on-prem gateway logs, **Microsoft Defender for Cloud Apps**. Centralize in a SIEM like **Microsoft Sentinel**. Configure alerts for:

- Multiple failed sign-ins / risky sign-ins
- Unexpected role assignments or workspace admin elevation
- Large dataset exports or bulk OneLake downloads
- Reports/datasets shared with external users
- Repeated DLP policy violations
- Unusual admin activity (deletion of workspaces or artifacts)

Correlation reveals suspicious patterns (e.g., risky sign-in followed by large data exports).

**Evidence**: SIEM integration state; alert rule inventory; sample alert payloads; M365 audit log retention configuration (30-day default: export if longer needed).

### Security Testing

Verify controls behave as expected:

- Confirm only intended users can access specific workspaces/artifacts
- If private link enabled, confirm Fabric is unreachable from unauthorized networks
- Periodically test CMK rotation and revocation
- Test DLP policies via controlled exports of labeled data
- Validate via automated checks (scripts retrieve workspace settings via Fabric APIs, compare against baseline)
- Penetration testing follows Microsoft Cloud Penetration Testing Rules of Engagement

**Evidence**: last access-control validation date; private link test result; CMK rotation test date; DLP test log; automated drift-detection script + last-run output; pentest scope + last-run date.

### Secure Development Lifecycle (SDL)

Connect workspaces to Git (Azure DevOps or GitHub). Branch, PR, code review. Use **Fabric Deployment Pipelines** for promotion across dev/test/prod with approvals and stage checks. Integrate security validation: static analysis, secret detection, dependency scanning. Handle sensitive config via Key Vault references or parameterization. Separate dev from prod; conditional access can restrict dev to managed devices.

**CI/CD security criteria (from the Fabric CI/CD guidance; see [`references/cicd-best-practices.md`](./cicd-best-practices.md)):** use **service principal authentication for all DevOps and CI/CD automation**, never user principals; **never commit files with sensitive credentials to Git**; let Terraform manage connection credentials (for example SAS tokens) so secrets stay encrypted, and store the Terraform state file encrypted in protected cloud storage; remove environment-specific connection settings from item definitions by using variable-library connection reference variables rather than hardcoded strings.

**Evidence**: Git integration coverage per workspace; PR review enforcement; deployment pipeline approval gates; secret-scan and SAST integration in CI; conditional access for dev environments; automation identity type (service principal vs user); Terraform state encryption; secret-free item definitions and workflow files.

---

## Evidence checklist (per principle)

- [ ] Tenant settings export: source: `[FabricAdmin]`
- [ ] RBAC inventory per workspace: source: `[FabricAdmin]`
- [ ] Workspace identity / service principal usage: source: `[FabricAdmin]`
- [ ] Conditional access policy list: source: `[user-interview]` + Entra admin
- [ ] PIM configuration for Fabric/Capacity Admin: source: `[user-interview]` + Entra admin
- [ ] Managed VNet + private link configuration: source: `[FabricAdmin]`
- [ ] On-prem gateway inventory + logs: source: `[FabricAdmin]`
- [ ] CMK enablement + Key Vault availability: source: `[FabricAdmin]`
- [ ] Sensitivity label coverage: source: `[FabricAdmin]` + `[search-consumption-cli]`
- [ ] Secret-in-code scan: source: `[spark-operations-cli]`, `[dataflows-consumption-cli]`, source-control scan
- [ ] SIEM integration + alert rule inventory: source: `[user-interview]`
- [ ] Audit log retention configuration: source: `[FabricAdmin]`
- [ ] Git integration + PR review enforcement: source: `[FabricAdmin]`
- [ ] Deployment pipeline approval gates: source: `[FabricAdmin]`
- [ ] Service-principal-only automation (no user principals): source: `[user-interview]` + repo/pipeline config
- [ ] No secrets committed to Git (secret-scan clean incl. workflow files): source: source-control scan
- [ ] Terraform state encrypted + connection credentials Terraform-managed: source: `[user-interview]`

---

## Cross-pillar tradeoffs

- **Security ↔ Operational Excellence**: PIM, conditional access, and per-environment isolation add deploy friction. Worth it for prod, often disabled in dev.
- **Security ↔ Cost**: Managed VNets, private link, CMK, Sentinel all add cost.
- **Security ↔ Performance**: Encryption in use (application-side) adds CPU; DLP scanning adds latency on exports.

---

## See also

- `common/FABRIC-WAF-CORE.md`
- `references/cicd-best-practices.md` (service-principal automation + no-committed-secrets criteria)
- `references/tradeoffs.md`
- `references/assessment-workflow.md`
- Delegate skills: `search-consumption-cli`, `sqldw-consumption-cli`, `spark-operations-cli`, `dataflows-consumption-cli`
