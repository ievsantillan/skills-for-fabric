# Assessment Workflow

End-to-end workflow for a Fabric WAF assessment. The skill follows this structure regardless of mode (`e2e`, `pillar:<name>`, `guidance-only`).

---

## Phase 1: Intake

Capture the full scope before any evidence is gathered. The agent's first turn produces a confirmed scope block from the following template.

### Intake template (our convention)

```yaml
scope:
  tenant_id: <Entra tenant ID>
  capacity_ids: [<one or more Fabric capacity IDs>]
  workspace_ids: [<one or more workspace IDs; omit if capacity-wide>]

audience:
  - <data architect | capacity admin | workspace owner | exec sponsor | platform team>

slas:
  rto: <e.g., "4 hours" | "Not provided">
  rpo: <e.g., "1 hour" | "Not provided">
  availability_target: <e.g., "99.9% monthly" | "Not provided">

risk_appetite: <Conservative | Balanced | Aggressive>
time_budget: <deep (multi-day evidence + interviews) | standard (1 day) | lightweight (a few hours)>

mode: <e2e | pillar:<reliability|security|cost-optimization|operational-excellence|performance-efficiency> | guidance-only>

output:
  folder: <e.g., WAFAssessmentReport-2026-06-13>
  export_formats: [markdown]  # add: excel, csv, word, html, pbip
  publish_to_fabric: false    # Phase 7 only; off by default

previous_assessment_folder: <path or null>  # if set, triggers re-assessment / diff workflow
```

> **Our convention, not Microsoft prescription.** Microsoft Learn does not prescribe an intake form. This template exists so assessments are repeatable across runs and across teams.

Render as a fillable checklist. Do not proceed to Phase 2 until the user has confirmed the scope block.

> **Define acronyms and jargon inline when interviewing.** The audience often includes non-architects (capacity admins, executive sponsors) who may not know the shorthand. On first use, expand terms before asking the question: for example RTO (Recovery Time Objective: how long the workload can be down before it must be restored), RPO (Recovery Point Objective: how much recent data, measured in time, can be lost), SLO / SLI, and idempotent (safe to re-run without creating duplicate or corrupted data). The glossary in `common/FABRIC-WAF-CORE.md` is the source of truth for definitions.

---

## Phase 2: Pre-flight

Fail fast before committing to evidence gathering.

### 2a. Permissions check

Verify the executing identity has (or can elevate via PIM to) the following roles. Report missing permissions explicitly; do not silently skip evidence.

- **Fabric Capacity Admin**: Capacity Metrics App, capacity-scoped APIs
- **Fabric Admin or Workspace Admin**: workspace-scoped read APIs
- **Microsoft Purview audit log reader / Compliance Administrator**: M365 audit logs (30-day window)
- **Entra Global Reader**: tenant-level identity/RBAC inventory (if in scope)
- **SQL endpoint read permission** on each Warehouse / Lakehouse SQL endpoint in scope

### 2b. Capacity throttling self-awareness

Query the Capacity Metrics App for current health of each in-scope capacity. If a target capacity is currently throttled OR shows >90% smoothed utilization over the last 24 hours, **warn the user explicitly**: running a full assessment against a strained capacity adds load and can worsen throttling. Offer three paths:

1. Proceed anyway (user accepts the load impact)
2. Switch this run to `guidance-only` mode (no evidence collection)
3. Abort

> **Our convention, not Microsoft prescription.** The 90% threshold is a default; tune to your environment.

### 2c. Delegation smoke-test

Dry-run a tiny FabricAdmin delegation: "list workspaces in capacity `<ID>`, return count only." Confirms the agent-to-agent delegation wiring is alive before committing to full evidence gathering. Fail fast with actionable error if:

- FabricAdmin agent is not registered
- The host model does not support nested agent calls
- The delegation returns unexpected output structure

---

## Phase 3: Evidence gathering

**Evidence-first is mandatory.** Gather hard evidence via APIs/queries before asking the user anything. Interview answers are a documented *fallback*, used only for items that genuinely cannot be obtained from a system (e.g. undocumented org processes, or data behind a paused/unavailable resource). When you do fall back to an interview answer, label that principle's evidence source as `interview` so the report distinguishes it from API-verified findings. Never ask the user for something an API can return.

Cascade pattern: framework knowledge here → tenant/workspace evidence via FabricAdmin → item-level evidence via `-consumption-cli` and `-operations-cli` skills.

Concrete evidence sources to try before interviewing (non-exhaustive):

- **Capacity Metrics App** (CU utilization, throttling, SKU): query its semantic model with **DAX via the Power BI `executeQueries` API** (see `references/example-assessment.md` for the verified recipe). It is a Power BI model, not a KQL database.
- **Secret-in-code** / retry / idempotency claims: fetch notebook and pipeline definitions (`POST .../items/{id}/getDefinition`) and inspect them, rather than asking.
- **RBAC, tenant settings, Git, workspace identity, deployment pipelines**: Fabric REST.
- **CI/CD posture** (Git integration + branch policy, variable libraries + value sets, deployment pipelines, service-principal-only automation, auto-binding): Fabric REST + repo/pipeline settings. Score against [`references/cicd-best-practices.md`](./cicd-best-practices.md), the co-primary Operational Excellence source.
- **PIM, Conditional Access, audit logs, sensitivity labels**: Microsoft Graph (Graph PowerShell for PIM/labels; see the evidence-checklist tooling note).
- **Cost**: Azure Cost Management (actuals) and the Retail Prices API (estimates).

### Routing

- **Tenant/workspace evidence** → delegate to **FabricAdmin** (e.g., capacity utilization, RBAC inventory, audit-log queries, secrets/Key Vault discipline, tagging, dev/prod separation). FabricAdmin fans out to its own delegate skills, aggregates, returns.
- **Item-level evidence** → delegate directly to specific `-cli` skills:
  - `spark-operations-cli`: failed jobs, stuck sessions
  - `sqldw-operations-cli`: slow queries, query insights
  - `semantic-model-consumption`: measure complexity, model size
  - `dataflows-consumption-cli`: dataflow refresh status, definition
  - `eventstream-consumption-cli`: stream topology
  - `eventhouse-consumption-cli`: KQL schema
  - `activator-consumption-cli`: rule + action inventory
  - `search-consumption-cli`: cross-workspace item discovery
  - `sqldw-consumption-cli`: T-SQL fact-checks

### Sampling guidance (large tenants)

When item count exceeds 50 of a given type, sample using these criteria in order (our convention):

1. **Production-labeled** workspaces (tag or naming convention)
2. **Highest-CU consumers** per Capacity Metrics App over the last 14 days
3. **Most-recently-modified** items in the last 30 days
4. **User-flagged critical** items from the intake

Record the sampling rule used and the list of items NOT sampled in the `evidence/` appendix.

### Evidence handling and privacy

Before committing or sharing the report, redact the following from the `evidence/` appendix:

- User UPNs and email addresses
- Connection strings, secrets, tokens
- Capacity and workspace GUIDs (if sharing externally)
- Item names that reveal customer or product confidentiality

A bulk redaction one-liner (PowerShell) is provided in `references/assessment-report-template.md`. The default report folder is excluded from git by the repository `.gitignore` (`WAFAssessmentReport-*/`).

### Failure recovery / resume

If a delegated evidence step fails (FabricAdmin returns an error, a `-cli` skill returns auth failure, a query times out):

1. Mark the affected principle(s) as `Not assessed: evidence gathering failed: <reason>`
2. Continue with remaining pillars / principles
3. Surface a "blocked evidence" table in the report README so failures are visible

**Resume**: re-run the assessment with the same scope and the same output folder name. The skill detects the existing folder and only refills sections marked `Not assessed: evidence gathering failed`.

---

## Phase 4: Scoring

For each principle, assign one of `Met`, `Partial`, `Gap`, `Not assessed` per the rubric in `common/FABRIC-WAF-CORE.md`. Anchor every score in a specific evidence row. If the evidence is ambiguous, prefer `Partial` over `Met`, and document why in the Finding field.

---

## Phase 5: Recommendations

Generate recommendations using the format documented in `common/FABRIC-WAF-CORE.md`:

- `id` (stable per-pillar ID; assigned after dedup, see below)
- `pillars` (single or multiple; dedup across pillars at end of phase)
- `principle` (verbatim H2 from the relevant Learn page)
- `severity` (Critical / High / Medium / Low: our convention)
- `effort` (S / M / L: our convention)
- `owner`
- `recommendation` (imperative)
- `evidence` (pointer)
- `learn_citation` (verbatim heading text, not slugified anchor)
- `fabric_features`
- `status` (Open / In progress / Done / Risk accepted)

**Dedup pass**: after all per-pillar scoring is complete, merge recommendations that target the same action (e.g., "right-size capacity" surfaced from both Cost and Performance). The merged row's `pillars` field lists every pillar that surfaced it.

**Stable ID assignment (after dedup)**: compute each recommendation's `stable_key` (`<primary-pillar>::<principle-slug>::<normalized-action-slug>`). If `intake.previous_assessment_folder` is set, load its `scorecard.json`, match by `stable_key`, and reuse the prior `id` and `first_seen` and carry forward `status` / `risk_accepted`; assign fresh per-pillar IDs only to new `stable_key`s. Full algorithm: `references/scorecard-schema.md`.

---

## Phase 6: Report emission (local)

Write the report folder to disk per the structure in `references/assessment-report-template.md`. Default folder name `WAFAssessmentReport-YYYY-MM-DD/` (our convention: user can override).

Markdown is always generated. Also always emit **`scorecard.json`** (the machine-readable trend/diff contract in `references/scorecard-schema.md`) into the folder, and append one row to **`WAFAssessmentHistory.md`** and **`history.csv`** in the parent directory. Other export formats are additive per the intake selection: see `references/export-formats.md` and (for PBIP) `references/export-pbip.md`. Persisting the scorecard to a Fabric Warehouse for cross-run BI is an opt-in Tier 2 step in `references/trend-storage.md`.

This phase touches local disk only. No mutation of Fabric tenant state.

---

## Phase 7: Publish (optional, opt-in per session)

Only runs when `output.publish_to_fabric == true` and the user explicitly confirms in this session.

- Delegates the upload to `powerbi-report-management` for the PBIP project folder.
- Uploads to the target Fabric workspace ID confirmed in intake.
- This is the **only** workflow step that mutates Fabric tenant state. Documented in the read-only boundary in `common/FABRIC-WAF-CORE.md`.

---

## Re-assessment / diff workflow

When `intake.previous_assessment_folder` points to an existing `WAFAssessmentReport-YYYY-MM-DD/` folder:

1. Run Phases 1-5 as usual.
2. Load the previous run's **`scorecard.json`** (deterministic; do not re-parse the previous markdown). Build the `stable_key` map used for ID reuse and status/risk carry-forward (Phase 5).
3. Compute deltas:
   - **Closed gaps**: previously `Gap` or `Partial`, now `Met`
   - **New gaps**: previously `Met`, now `Gap` or `Partial`
   - **Regressions**: a recommendation previously `Done` or `Risk accepted` whose principle is a `Gap`/`Partial` again (flip its status back to `Open`)
   - **Score deltas per pillar**: count of Met / Partial / Gap / Not assessed in each run, with delta, plus `waf_index` delta
   - **Recommendation churn**: closed, new, persisting (matched by `stable_key`); surface persistence of Critical-or-High recommendations across two consecutive runs, with age-of-finding from `first_seen`
4. **Methodology-drift check**: compare `assessment.methodology` across the two `scorecard.json` files. If any pillar's VERIFIED date or `principle_count` changed, add a drift note and mark that pillar's index/score deltas as indicative, not exact. Never report an index change caused by a changed denominator as a regression.
5. Write the diff as `diff-vs-<prev-date>.md` inside the new dated folder.
6. The executive `README.md` of the new folder links to the diff prominently, and `WAFAssessmentHistory.md` gains the new row.

---

## See also

- `common/FABRIC-WAF-CORE.md`: rubric, recommendation format, glossary, boundaries
- `references/assessment-report-template.md`: output structure + redaction
- `references/scorecard-schema.md`: `scorecard.json` contract, stable IDs, history index
- `references/evidence-checklist.md`: per-pillar evidence items
- `references/export-formats.md`: markdown + HTML/Excel/Word/CSV
- `references/export-pbip.md`: optional PBIP project
- `references/trend-storage.md`: opt-in Tier 2 Warehouse persistence + Tier 3 Rayfin portal
- `references/example-assessment.md`: concrete sample with runnable queries
