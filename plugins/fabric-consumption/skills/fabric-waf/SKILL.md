---
name: fabric-waf
description: >
  Run a Microsoft Fabric Well-Architected Framework assessment across one or all five pillars
  (Reliability, Security, Cost Optimization, Operational Excellence, Performance Efficiency).
  Orchestrates: intake + scope, pre-flight permissions and throttling check, evidence gathering
  via FabricAdmin and -cli skills, principle scoring (Met/Partial/Gap/Not assessed), recommendation
  generation with severity + effort + Learn citation, layered markdown report emission, and
  optional PBIP / PDF / Excel / Word / CSV exports.
  Use when the user wants a WAF-style review of their Fabric tenant, capacity, or workspace, or
  has explicit questions about a specific WAF pillar.
  Triggers: "WAF", "well-architected", "well-architected framework", "pillar review",
  "reliability review", "security review", "cost review", "cost optimization review",
  "operational excellence review", "performance review", "performance efficiency review",
  "architecture review", "Fabric assessment", "Fabric WAF", "assess my Fabric capacity",
  "audit my Fabric workspace", "design review", "platform review".
---

> **Update Check: ONCE PER SESSION (mandatory)**
> The first time this skill is used in a session, run the **check-updates** skill before proceeding.
> - **GitHub Copilot CLI / VS Code**: invoke the `check-updates` skill (e.g., `/fabric-skills:check-updates`).
> - **Claude Code / Cowork / Cursor / Windsurf / Codex**: read the local `package.json` version, then compare it against the remote version via `git fetch origin main --quiet && git show origin/main:package.json` (or the GitHub API). If the remote version is newer, show the changelog and update instructions.
> - Skip if the check was already performed earlier in this session.

> **CRITICAL NOTES**
> 1. To find the workspace details (including its ID) from workspace name: list all workspaces and, then, use JMESPath filtering
> 2. To find the item details (including its ID) from workspace ID, item type, and item name: list all items of that type in that workspace and, then, use JMESPath filtering

# Fabric Well-Architected Framework Skill

> ⚠️ **STOP: Read this entire skill document in full before taking any action.** Do not begin orchestrating tool calls until you have read every section below, including Pre-flight, Workflow, Delegation Map, Read-only Boundary, and Must/Prefer/Avoid. Skipping ahead leads to invented findings, missed permissions, and an unrunnable assessment.

You help users assess a Microsoft Fabric tenant, capacity, or workspace against the Microsoft Fabric Well-Architected Framework. You orchestrate intake, evidence gathering (via delegation), principle scoring, recommendations, and report emission.

## Prerequisites

Before running an assessment (`e2e` or `pillar:<name>`), the executing identity needs the read permissions below. The agent verifies these during Pre-flight and fails fast with the exact missing list, but review them upfront so you can request access or arrange PIM elevation first. The `guidance-only` mode needs none of these.

| Permission / role | Grants access to | Required for |
|---|---|---|
| **Fabric Capacity Admin** | Capacity Metrics App and capacity-scoped APIs (CU utilization, throttling) | Cost, Performance, Reliability |
| **Fabric Admin** or **Workspace Admin** | Workspace-scoped read APIs (item inventory, RBAC, settings) | All pillars |
| **Microsoft Purview audit log reader** or **Compliance Administrator** | M365 unified audit log (30-day window) | Security, Operational Excellence |
| **Entra Global Reader** | Tenant identity and RBAC inventory (service principals, guest access) | Security (when tenant identity is in scope) |
| **SQL endpoint read** | Each in-scope Warehouse / Lakehouse SQL endpoint | Performance, Security (item-level) |

Notes:

- PIM just-in-time elevation into any of these roles satisfies the check.
- A missing permission does not abort the run: the affected principles are scored `Not assessed` with the reason, so you still get partial coverage.
- Tooling: an authenticated Azure CLI session (`az login`) is required for token acquisition.
- Full Pre-flight detail (including the capacity-throttling and delegation smoke-test gates) is in the [Pre-flight permissions](#pre-flight-permissions) section below and `references/assessment-workflow.md` Phase 2.

## Table of Contents

| Task | Reference | Notes |
|---|---|---|
| Fabric Topology & Key Concepts | [COMMON-CORE.md § Fabric Topology & Key Concepts](../../common/COMMON-CORE.md#fabric-topology--key-concepts) | Tenant / Capacity / Workspace / Item / OneLake |
| Authentication & Token Acquisition | [COMMON-CORE.md § Authentication & Token Acquisition](../../common/COMMON-CORE.md#authentication--token-acquisition) | Token audiences, identity types |
| Authentication Recipes | [COMMON-CLI.md § Authentication Recipes](../../common/COMMON-CLI.md#authentication-recipes) | `az login`, token acquisition |
| WAF Pillar Framework | [FABRIC-WAF-CORE.md](../../common/FABRIC-WAF-CORE.md) | 5 pillars, methodology, scoring rubric, recommendation format, glossary, read-only boundary, Azure WAF relationship |
| Pillar deep-dives | [references/reliability.md](./references/reliability.md), [security.md](./references/security.md), [cost-optimization.md](./references/cost-optimization.md), [operational-excellence.md](./references/operational-excellence.md), [performance-efficiency.md](./references/performance-efficiency.md) | Per-principle evidence + tradeoffs |
| Cross-pillar tradeoffs | [references/tradeoffs.md](./references/tradeoffs.md) | Verbatim Learn quotes + cross-pillar synthesis |
| Assessment workflow | [references/assessment-workflow.md](./references/assessment-workflow.md) | 7 phases incl. intake, pre-flight, sampling, redaction, failure recovery, re-assessment diff |
| Report template | [references/assessment-report-template.md](./references/assessment-report-template.md) | Layered folder + per-principle block format |
| Evidence checklist | [references/evidence-checklist.md](./references/evidence-checklist.md) | Per-pillar at-a-glance index with source tags |
| Export formats | [references/export-formats.md](./references/export-formats.md) | PDF / Excel / Word / CSV; PBIP via [references/export-pbip.md](./references/export-pbip.md) |
| Concrete example queries | [references/example-assessment.md](./references/example-assessment.md) | KQL + T-SQL + REST samples |
| Must/Prefer/Avoid | [SKILL.md § Must/Prefer/Avoid](#mustpreferavoid) | Guardrails: read this in full |
| Workflow | [SKILL.md § Workflow](#workflow) | High-level orchestration order |

## WAF Overview

| Pillar | Microsoft Learn URL |
|---|---|
| Reliability | https://learn.microsoft.com/en-us/azure/well-architected/microsoft-fabric/reliability |
| Security | https://learn.microsoft.com/en-us/azure/well-architected/microsoft-fabric/security |
| Cost Optimization | https://learn.microsoft.com/en-us/azure/well-architected/microsoft-fabric/cost-optimization |
| Operational Excellence | https://learn.microsoft.com/en-us/azure/well-architected/microsoft-fabric/operational-excellence |
| Performance Efficiency | https://learn.microsoft.com/en-us/azure/well-architected/microsoft-fabric/performance-efficiency |

## Modes

- `mode: e2e`: assess all 5 pillars
- `mode: pillar:<reliability|security|cost-optimization|operational-excellence|performance-efficiency>`: single pillar
- `mode: guidance-only`: answer questions from the framework body of knowledge without an assessment (no permissions required, no evidence collected, no report emitted)

Optional export knob:

- `output.export_formats: [markdown]` (default): markdown layered folder only
- `output.export_formats: [markdown, pdf]`: also generate PDF
- `output.export_formats: [markdown, excel, csv, word]`: also generate Excel / CSV / Word
- `output.export_formats: [markdown, pbip]`: also generate PBIP (Tier 1.5; see `references/export-pbip.md`)
- `output.publish_to_fabric: true`: Phase 7 publish step (off by default; explicit per-session confirmation required)

## Pre-flight permissions

Verify the executing identity has (or can elevate via PIM to) the following before starting evidence gathering. Fail fast with the explicit missing-permissions list.

- **Fabric Capacity Admin**: Capacity Metrics App, capacity-scoped APIs
- **Fabric Admin or Workspace Admin**: workspace-scoped read APIs
- **Microsoft Purview audit log reader / Compliance Administrator**: M365 audit logs (30-day window)
- **Entra Global Reader**: tenant-level identity / RBAC inventory (if in scope)
- **SQL endpoint read** on each Warehouse / Lakehouse SQL endpoint in scope

Full pre-flight (including capacity throttling self-awareness and the FabricAdmin delegation smoke-test) is in `references/assessment-workflow.md` Phase 2.

## Workflow

See `references/assessment-workflow.md` for the full 7-phase workflow. Summary:

1. **Intake**: capture scope, audience, SLAs, risk appetite, time budget, mode, export targets, previous assessment folder (if re-assessment)
2. **Pre-flight**: permissions + throttling check + delegation smoke-test
3. **Evidence gathering**: cascade: FabricAdmin for tenant/workspace; `-cli` skills for item-level; sample with documented criteria when item count > 50
4. **Scoring**: per principle: Met / Partial / Gap / Not assessed
5. **Recommendations**: severity + effort + Learn citation + Fabric feature; dedup across pillars
6. **Report emission (local)**: markdown layered folder always; optional PDF / Excel / Word / CSV / PBIP
7. **Publish (optional)**: explicit per-session confirmation required; delegates to `powerbi-report-management`

## Must/Prefer/Avoid

### MUST DO

- **Source-bound: never invent facts**: only use Microsoft Learn content, evidence returned by delegate skills, and the user's own input. When ground truth is unknown, score the principle as `Not assessed` and document why.
- **Re-fetch Microsoft Learn pages before authoring or updating any pillar reference**: verify against the live page; bump the `<!-- VERIFIED: YYYY-MM-DD against <URL> -->` stamp.
- **Cite Learn by verbatim heading text, not slugified anchor**: Microsoft re-slugs occasionally.
- **Fail fast in Pre-flight**: surface missing permissions and broken delegation before committing to a full assessment.
- **Warn on a throttled capacity**: running a full assessment against a capacity at >90% smoothed CU utilization or actively throttling adds load. Offer the user proceed / guidance-only / abort.
- **Mark unobtainable evidence as `Not assessed`** with the reason: never invent a score.
- **Use the dedup pass** before writing `recommendations.md`: merge rows that target the same action across pillars.
- **Stamp the report**: every report's `README.md` has the assessment_version block (skill version + pillar reference VERIFIED dates + collected_at + identity).
- **Redact `evidence/`** before sharing externally: UPNs, secrets, GUIDs, confidential names. The PowerShell bulk-redact one-liner is in `references/assessment-report-template.md`.

### PREFER

- **Delegate over re-implement**: FabricAdmin for tenant/workspace evidence; `-consumption-cli` / `-operations-cli` for item-level. Do not duplicate their work.
- **Standard per-principle detail** (Finding · Evidence · Score · Recommendation · Severity · Effort · Owner · Fabric features · Learn citation · Tradeoffs) over terse or verbose variants.
- **Layered folder report** over single-file output: supports drill-down and re-assessment diff.
- **Markdown first, additive exports**: PDF / Excel / Word / CSV / PBIP are derived from the markdown.

### AVOID

- **Mutating Fabric tenant state during assessment**: no POST / PUT / PATCH / DELETE against Fabric REST or Kusto management endpoints; no `.create` / `.alter` / `.drop` KQL; no DDL/DML against Warehouses or Lakehouse SQL endpoints. Local artifact generation (markdown, CSV, Excel, Word, PBIP) is permitted; Fabric publish is Phase 7 only.
- **Delegating to `-authoring-cli` skills during evidence gathering**: they are write-capable and out of scope for the read-only assessment phases.
- **Inventing anti-patterns, maturity models, or principle hierarchies**: Microsoft Learn does not use these structures. Mirror the actual H2 sections from each pillar page verbatim.
- **Asserting a recommended assessment cadence**: Microsoft Learn does not prescribe one. WAF is iterative; the user picks the cadence appropriate to their change rate and risk tolerance.
- **Committing `WAFAssessmentReport-*/` folders**: they contain PII. The repository `.gitignore` excludes them by default; do not override.

## Delegation Map

| Evidence type | Delegate to |
|---|---|
| Tenant configuration, RBAC, capacity utilization, audit-log queries, secrets discipline, tagging, dev/prod separation | **FabricAdmin** (agent) |
| Failed Spark jobs, stuck sessions | `spark-operations-cli` |
| Slow Warehouse queries, Query Insights | `sqldw-operations-cli` |
| T-SQL fact-checks (Warehouse / SQL endpoint) | `sqldw-consumption-cli` |
| Semantic model measure complexity, model size | `semantic-model-consumption` |
| Dataflow refresh status, definitions | `dataflows-consumption-cli` |
| Eventstream topology | `eventstream-consumption-cli` |
| KQL schema discovery | `eventhouse-consumption-cli` |
| Activator rule + action inventory | `activator-consumption-cli` |
| Cross-workspace item discovery | `search-consumption-cli` |
| PBIP authoring (local only, Phase 6) | `powerbi-report-authoring`, `semantic-model-authoring` |
| Publish PBIP to Fabric (Phase 7, opt-in only) | `powerbi-report-management` |

## Examples

### Example 1: e2e assessment

```
User: Run a Fabric WAF assessment on capacity F64-prod and workspace 'finance-prod'.
       Output to WAFAssessmentReport-2026-06-13. Standard detail. Include PBIP export.

Skill:
1. Intake: confirm scope block (capacity + workspace + audience + SLAs + risk appetite +
   time budget + export_formats: [markdown, pbip] + publish_to_fabric: false).
2. Pre-flight: list missing permissions; check capacity throttling; smoke-test FabricAdmin
   delegation by asking it for workspace count in the capacity.
3. Phase 3: for each pillar, delegate tenant/workspace evidence to FabricAdmin and
   item-level evidence to specific -cli skills per references/evidence-checklist.md.
4. Phase 4: score each principle Met/Partial/Gap/Not-assessed.
5. Phase 5: generate recommendations with severity + effort + Learn citation; dedup
   across pillars.
6. Phase 6: write WAFAssessmentReport-2026-06-13/ markdown folder + PBIP project.
7. Phase 7: skipped (publish_to_fabric: false).
```

### Example 2: pillar review

```
User: Just do a security review of workspace 'analytics-shared'.

Skill: mode=pillar:security. Intake confirms scope and audience. Pre-flight checks
       Workspace Admin + Entra Global Reader + Purview audit reader. Phase 3 delegates
       to FabricAdmin for RBAC + tenant settings + audit-log queries; to
       search-consumption-cli for sensitivity label coverage; to dataflows-consumption-cli
       for secret-in-code scan. Phase 4-6 produce a single-pillar report under
       WAFAssessmentReport-YYYY-MM-DD/ (README + security.md + recommendations.md filtered
       to security + evidence/).
```

### Example 3: guidance-only Q&A

```
User: What's the Fabric WAF stance on CMK encryption tradeoffs?

Skill: mode=guidance-only. No permissions check, no evidence collection. Answer from
       common/FABRIC-WAF-CORE.md + references/security.md "Data encryption" section,
       quoting the verbatim Tradeoff callout from the Microsoft Learn Security pillar:
       "Using CMK introduces operational dependencies. The key vault must remain
       available and accessible..."
```

### Example 4: read-only boundary refusal

```
User: Run a WAF assessment and, while you're at it, fix any Gap items you find.

Skill: REFUSES the "fix" portion. Per the read-only trust boundary in
       common/FABRIC-WAF-CORE.md, FabricWAF never mutates Fabric tenant state during
       assessment. Recommendations are written to recommendations.md; remediation is
       the user's responsibility (or a separate explicit follow-up using the appropriate
       -authoring-cli skills).
```

See `references/example-assessment.md` for a worked sample with real KQL, T-SQL, and REST queries.
