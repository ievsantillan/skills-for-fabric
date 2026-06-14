<!-- VERIFIED: 2026-06-13 against https://learn.microsoft.com/en-us/azure/well-architected/microsoft-fabric/ -->

# FABRIC-WAF-CORE.md: Microsoft Fabric Well-Architected Framework Core

> **Purpose**: Shared reference for the `fabric-waf` skill and the `FabricWAF` agent. Contains the framework body of knowledge (5 pillars, methodology, scoring rubric, recommendation format, glossary, boundaries) consumed by both.
>
> **Source of truth**: Microsoft Learn: [Microsoft Fabric Well-Architected Framework](https://learn.microsoft.com/en-us/azure/well-architected/microsoft-fabric/). Re-fetch when authoring or updating any pillar reference; bump the VERIFIED stamp at the top of each file.

---

## The 5 Pillars

| Pillar | Microsoft Learn URL | What it covers |
|---|---|---|
| **Reliability** | `https://learn.microsoft.com/en-us/azure/well-architected/microsoft-fabric/reliability` | Constraints, failure modes, SLOs, redundancy, scaling, monitoring, self-preservation, DR, testing |
| **Security** | `https://learn.microsoft.com/en-us/azure/well-architected/microsoft-fabric/security` | Baseline, isolation, Zero Trust identity, network, encryption, hardening, secrets, monitoring, testing, SDL |
| **Cost Optimization** | `https://learn.microsoft.com/en-us/azure/well-architected/microsoft-fabric/cost-optimization` | Cost drivers, modeling, governance, environment optimization, automation, consolidation |
| **Operational Excellence** | `https://learn.microsoft.com/en-us/azure/well-architected/microsoft-fabric/operational-excellence` | Team readiness, safe deployment, automation, monitoring, incident response, testing |
| **Performance Efficiency** | `https://learn.microsoft.com/en-us/azure/well-architected/microsoft-fabric/performance-efficiency` | Capacity planning, SKU selection, scaling strategies, performance monitoring, testing, optimization |

The full per-pillar deep-dives live in `skills/fabric-waf/references/<pillar>.md`.

---

## SDK / API landscape

There is **no Microsoft Fabric WAF SDK or assessment REST API** in the Fabric REST API reference or the Learn WAF pages at the time of writing. The Fabric WAF is documentation; evidence is gathered through:

1. **Existing `-cli` skills in this repo** (delegated, using `az rest` against the Fabric REST API and Kusto REST API): primary path.
2. **Open-source accelerators cited by Microsoft Learn**:
   - [`fabric-cost-analysis`](https://github.com/microsoft/fabric-toolbox/tree/main/monitoring/fabric-cost-analysis) (cited by Cost Optimization page)
   - [`FUAM`: Fabric Unified Admin Monitoring](https://github.com/microsoft/fabric-toolbox/tree/main/monitoring/fabric-unified-admin-monitoring) (cited by Operational Excellence page)
3. **Microsoft Well-Architected Review online tool** ([survey-based experience](https://learn.microsoft.com/en-us/assessments/azure-architecture-review/)): referenced as an output format only; we do not depend on it.

If a Fabric WAF SDK or assessment REST API ships in the future, this file is the place to record it.

---

## Methodology

The assessment cascade is:

```
1. Load the framework (this file + the relevant pillar reference)
2. Confirm scope and pre-flight permissions
3. Gather tenant/workspace evidence → delegate to FabricAdmin (which fans out to its own -cli skills)
4. Gather item-level evidence → delegate directly to specific -consumption-cli / -operations-cli skills
5. Score each principle against the rubric (below)
6. Generate recommendations using the format (below)
7. Emit the report (markdown layered folder; optional PBIP)
```

**No-circular-delegation rule**: FabricAdmin MUST NOT delegate back to FabricWAF. The cascade is strictly one-way.

---

## Scoring rubric (categorical)

Each WAF principle is scored against one of four categories. **This rubric is our convention; Microsoft Learn does not prescribe a scale.** There is NO maturity model: CMMI levels are not a Fabric WAF concept.

| Score | Meaning |
|---|---|
| **Met** | Evidence shows the principle is fully addressed; controls are in place and observable. |
| **Partial** | Evidence shows the principle is partially addressed; meaningful gaps remain. |
| **Gap** | Evidence shows the principle is not addressed; the gap creates measurable business risk. |
| **Not assessed** | Evidence could not be gathered (missing permission, scope exclusion, delegation failure). Always document why. |

---

## Recommendation format (our convention)

Every recommendation row uses this shape:

| Field | Required | Example |
|---|---|---|
| `pillars` | Yes | `[cost-optimization, performance-efficiency]` (single or multiple if cross-pillar) |
| `principle` | Yes | Verbatim H2 from the relevant pillar Learn page |
| `severity` | Yes | `Critical` / `High` / `Medium` / `Low` (see scale below) |
| `effort` | Yes | `S` / `M` / `L` (see scale below) |
| `owner` | No | Free-form (capacity admin / workspace owner / platform team) |
| `recommendation` | Yes | Imperative sentence: "Enable surge protection on capacity X" |
| `evidence` | Yes | Pointer to file or table row in `evidence/` appendix |
| `learn_citation` | Yes | Verbatim heading text from the Learn pillar page (not slugified anchor) |
| `fabric_features` | Yes | Named Fabric features that close the gap (e.g., Capacity Metrics App, Workspace Monitoring, Activator) |
| `status` | Yes | `Open` / `In progress` / `Done` / `Risk accepted` |

### Severity scale (our convention)

- **Critical**: Immediate business risk; potential data loss, outage, or breach.
- **High**: Significant exposure or cost waste; addresses material risk over weeks/months.
- **Medium**: Notable gap; not urgent but should be tracked.
- **Low**: Hygiene or future-proofing.

### Effort scale (our convention)

- **S**: Less than 1 day of work for a single engineer.
- **M**: 1–5 days of work; may involve more than one role.
- **L**: More than 5 days, or requires multi-team coordination.

Microsoft Learn does not prescribe severity or effort scales. These are our defaults so assessments are comparable across runs.

---

## Evidence request format (soft contract for FabricAdmin)

FabricAdmin uses natural-language workflow guidance, not structured outputs. FabricWAF asks FabricAdmin in plain English for the evidence it needs. To keep responses easy to parse, prefer questions of the form:

> "For workspace `<ID>` in capacity `<ID>`, return: (1) <evidence item 1>, (2) <evidence item 2>, ... Format each as a markdown table or short bullet list, and include the source command or REST endpoint used."

This is a convention, not an enforced schema. If FabricAdmin returns prose, FabricWAF normalizes it into the `evidence/` appendix.

---

## Read-only trust boundary

FabricWAF **MUST NEVER mutate Fabric tenant state**:

- No `POST` / `PUT` / `PATCH` / `DELETE` against the Fabric REST API or Kusto management endpoints.
- No `.create` / `.alter` / `.drop` KQL commands.
- No DDL/DML against Warehouses or Lakehouse SQL endpoints.

**Local artifact generation IS permitted**:

- Writing markdown, CSV, Excel, Word, or PBIP project files to local disk does not touch the Fabric tenant.
- Delegating to `powerbi-report-authoring` and `semantic-model-authoring` for local PBIP/TMDL generation is allowed within Phase 6 export.

**Publishing artifacts to Fabric is a separate explicit step** (Phase 7 in the agent framework). Defaults to off; requires explicit user confirmation per session; delegates to `powerbi-report-management`.

---

## Relationship to Azure WAF

Microsoft Fabric runs on Azure infrastructure. The Fabric WAF assumes the Azure layer is sound.

**In scope for Fabric WAF**: anything within Fabric's control plane or data plane: capacities, workspaces, items, OneLake, identities as used by Fabric, Fabric monitoring surfaces, Fabric deployment pipelines.

**Out of scope (defer to Azure WAF)**: networking (VNets, NSGs, Azure Firewall topology), Entra tenant hardening, Key Vault deployment topology, Azure Monitor / Log Analytics design, Azure Policy at subscription scope, Azure subscription governance.

When an assessment finding sits at the boundary (e.g., "configure managed VNet for the workspace"), record the Fabric-side recommendation and link out to the Azure WAF article for the underlying Azure concern.

---

## Heading anchor stability (citation convention)

When citing specific Microsoft Learn H2 sections, **cite by verbatim heading text, not slugified anchor**.

- Good: `See "Build self-healing through redundancy" in the Learn Reliability pillar.`
- Avoid: `See learn.microsoft.com/.../reliability#build-self-healing-through-redundancy`

Microsoft re-slugs headings occasionally; verbatim text survives those changes.

---

## Glossary

| Term | Definition |
|---|---|
| **CU** | Capacity Unit. The compute resource unit consumed by all Fabric workloads. |
| **F-SKU** | Fabric SKU tier (F2, F4, F8, ..., F2048). Pay-as-you-go or reserved. |
| **P-SKU** | Legacy Power BI Premium per-capacity tier. Predates F-SKU. |
| **WAF** | Well-Architected Framework. |
| **RTO** | Recovery Time Objective. Maximum tolerable time to restore service after a failure. |
| **RPO** | Recovery Point Objective. Maximum tolerable data loss measured in time. |
| **FUAM** | Fabric Unified Admin Monitoring. Open-source tenant-wide monitoring accelerator. |
| **OneLake** | Tenant-wide unified data lake; all Fabric items store data here as Delta/Parquet. |
| **Smoothing** | Mechanism that distributes background workload CU consumption over a 24-hour window. |
| **Bursting** | Mechanism that lets workloads temporarily exceed their capacity baseline. |
| **Autoscale** | Optional billing model where capacity scales for Spark and Data Warehousing workloads, billing per active job. |
| **Throttling** | Staged slowdown that engages when sustained CU consumption exceeds the capacity baseline. |
| **Capacity Admin** | Fabric role that manages a capacity (scale, pause, assign workspaces) without seeing the data inside it. |
| **Workspace Admin** | Fabric role that manages a workspace (members, items, settings). |
| **Fabric Admin** | Tenant-wide Fabric administrator. |
| **PIM** | Privileged Identity Management. Just-in-time elevation for administrative roles. |
| **CMK** | Customer-Managed Key. Encryption key the customer owns in Azure Key Vault. |
| **DLP** | Data Loss Prevention. Policies that block or alert on sensitive data movement. |
| **SDL** | Secure Development Lifecycle. |

---

## Cadence

WAF is iterative. Re-run the assessment after meaningful changes: capacity SKU change, new mission-critical workload, security incident, major Microsoft Learn update to a pillar page. The user picks the cadence appropriate to their change rate and risk tolerance. Microsoft Learn does not prescribe a cadence.
