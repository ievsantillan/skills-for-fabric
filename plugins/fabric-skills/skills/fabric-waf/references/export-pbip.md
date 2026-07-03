# PBIP Export: Fabric WAF Living Artifact

Optional Tier 1.5 export. Renders the assessment as a Power BI project (PBIP) so pillar scores trend over time, recommendations are filterable, and the assessment becomes a living artifact in Fabric. Enable via `output.export_formats: [markdown, pbip]` in the intake.

PBIP generation is **local only** (writes files to disk). Publishing to a Fabric workspace is a separate Phase 7 step that requires explicit per-session user confirmation. See the read-only boundary in `common/FABRIC-WAF-CORE.md`.

Authoring is delegated to:

- `powerbi-report-authoring`: PBIP / PBIR file generation
- `semantic-model-authoring`: TMDL / semantic model project generation
- `powerbi-report-management`: ONLY in optional Phase 7 publish

Optionally, for the page layout brief, `powerbi-report-design` (archetype, chart choice, color, layout) and `powerbi-report-planning` (guided requirements to build) can feed the authoring step. All four skills ship in the `powerbi-authoring` plugin.

### PBIR authoring rules (from the Power BI Report Authoring skill)

- **Never construct PBIR JSON by hand or from memory.** All PBIR page/visual content must go through `powerbi-report-authoring`; `powerbi-report-management` is transport only. See [Report Authoring skill overview](https://learn.microsoft.com/en-us/power-bi/developer/agentic/power-bi-report-authoring-skill-overview).
- **PBIR format only.** Use `?format=PBIR` on `getDefinition`; **PBIR-Legacy is not supported** by these skills. If a definition returns `"format": "PBIR-Legacy"`, it cannot be processed.
- **PBIR is the source of truth.** Commit a baseline of the PBIP before letting the agent modify PBIR files (so changes are revertible), and save any manual Power BI Desktop edits before asking the agent to iterate (unsaved Desktop changes are not seen by the agent).

---

## Data source: the scorecard.json series

The PBIP loads from the **`scorecard.json`** files emitted per run (contract in `references/scorecard-schema.md`), NOT by parsing the markdown reports. Each run's `scorecard.json` maps directly onto the star schema below (its `assessment`, `pillars`, `principles`, `recommendations`, and `tradeoffs` sections become the fact/dimension rows). Point the model at the folder of `WAFAssessmentReport-*/scorecard.json` files (or the parent `history.csv` for the lightweight trend), so adding a new assessment is just adding its `scorecard.json` to the source. This makes the multi-run trend deterministic and keeps a single contract shared with the Tier 2 Warehouse in `references/trend-storage.md`.

---

## Star schema

The semantic model is a star schema. Facts capture each assessment run; dimensions describe the framework.

### Dimensions

**Pillars** (5 rows, static):

| PillarKey | PillarName |
|---|---|
| reliability | Reliability |
| security | Security |
| cost-optimization | Cost Optimization |
| operational-excellence | Operational Excellence |
| performance-efficiency | Performance Efficiency |

**Principles** (per-pillar; sourced from the verified Learn H2s at assessment time):

| PrincipleKey | PillarKey | PrincipleName | LearnHeadingVerbatim |
|---|---|---|---|
| reliability-constraints | reliability | Start with constraints | Start with constraints: know your boundaries |
| reliability-failures | reliability | Understand where failures happen | Understand where failures happen |
| ... | ... | ... | ... |

Refresh the Principles table from the VERIFIED-stamp date of each pillar reference at assessment time. Do not hard-code Principles: they evolve as Microsoft Learn evolves.

**EvidenceSources** (cardinality matches Phase 3 delegation routing):

| SourceKey | SourceType | SourceName |
|---|---|---|
| FabricAdmin | agent | FabricAdmin |
| CapacityMetricsApp | accelerator | Capacity Metrics App |
| spark-operations-cli | skill | spark-operations-cli |
| sqldw-operations-cli | skill | sqldw-operations-cli |
| ... | ... | ... |

### Facts

**Assessments** (one row per assessment run):

| Column | Type | Notes |
|---|---|---|
| AssessmentKey | text | `<folder-name>` (e.g., `WAFAssessmentReport-2026-06-13`) |
| AssessmentDate | date | From folder name or stamp block |
| ScopeTenantId | text | |
| ScopeCapacityIds | text | Pipe-separated list |
| ScopeWorkspaceIds | text | Pipe-separated list |
| Mode | text | `e2e` / `pillar:<name>` / `guidance-only` |
| SkillVersion | text | From `package.json` |
| IdentityUsed | text | UPN or service principal |

**Findings** (one row per principle per assessment):

| Column | Type | Notes |
|---|---|---|
| AssessmentKey | text | FK → Assessments |
| PrincipleKey | text | FK → Principles |
| Score | text | Met / Partial / Gap / Not assessed |
| FindingText | text | Current state vs target |
| EvidencePointer | text | Path under `evidence/` |

**Recommendations** (one row per recommendation per assessment, after dedup):

| Column | Type | Notes |
|---|---|---|
| AssessmentKey | text | FK → Assessments |
| RecommendationId | text | `R001` style |
| Pillars | text | Pipe-separated PillarKey list (multi-pillar after dedup) |
| PrimaryPrincipleKey | text | FK → Principles |
| Severity | text | Critical / High / Medium / Low |
| Effort | text | S / M / L |
| Owner | text | |
| RecommendationText | text | Imperative |
| FabricFeatures | text | Pipe-separated |
| Status | text | Open / In progress / Done / Risk accepted |
| EvidencePointer | text | |

**Tradeoffs** (one row per tradeoff surfaced by a recommendation):

| Column | Type | Notes |
|---|---|---|
| AssessmentKey | text | FK → Assessments |
| RecommendationId | text | FK → Recommendations |
| AffectedPillarKey | text | FK → Pillars |
| TradeoffText | text | One-line description |

---

## Pre-built DAX measures

```dax
% Met by Pillar =
DIVIDE(
    CALCULATE(
        COUNTROWS(Findings),
        Findings[Score] = "Met"
    ),
    CALCULATE(
        COUNTROWS(Findings),
        Findings[Score] IN { "Met", "Partial", "Gap" }
    )
)

Open Recommendations by Severity =
CALCULATE(
    COUNTROWS(Recommendations),
    Recommendations[Status] = "Open"
)

Critical Open =
CALCULATE(
    [Open Recommendations by Severity],
    Recommendations[Severity] = "Critical"
)

Effort Hours Total =
SUMX(
    Recommendations,
    SWITCH(Recommendations[Effort], "S", 4, "M", 24, "L", 80, 0)
)

Score Delta vs Previous Assessment =
VAR _current = [% Met by Pillar]
VAR _prev =
    CALCULATE(
        [% Met by Pillar],
        FILTER(
            ALL(Assessments[AssessmentDate]),
            Assessments[AssessmentDate] < MAX(Assessments[AssessmentDate])
        )
    )
RETURN _current - _prev

Recommendations by Owner =
CALCULATE(
    COUNTROWS(Recommendations),
    Recommendations[Status] = "Open"
)
```

The "Effort Hours Total" S/M/L → hour mapping (4 / 24 / 80) is our convention; tune in TMDL if your team uses different conventions.

---

## Page layouts (4 pages)

> **Use modern visual types.** Prefer `cardVisual` (not the legacy `card`) and `pivotTable` (not the legacy `matrix`). Avoid visuals the platform is deprecating: Q&A, Bing maps, and filled maps. The authoring skill validates and renders these correctly; legacy types may not survive future Desktop versions.

### 1. Executive Overview

- Scorecard banner: % Met by Pillar (5 large `cardVisual` tiles)
- Top 5 risks (Critical + High, Open status)
- Top 5 quick wins (Effort = S, Severity High or Critical, Open status)
- Score trend line (multi-assessment): `% Met by Pillar` over `AssessmentDate`
- Outstanding tradeoffs card

### 2. Pillar Drill

- Pillar slicer (single select)
- Per-principle `pivotTable`: PrincipleName, Score, FindingText (tooltip), EvidencePointer (link)
- Score distribution donut
- Related recommendations filtered by pillar

### 3. Recommendations Backlog

- Filterable table with slicers: Severity, Effort, Owner, Pillars, Status
- Columns: ID, Severity, Effort, Owner, Pillars, Principle, Recommendation, Fabric features, Status, EvidencePointer
- "Copy to Jira" hint in a side card (text describes how to paste rows)

### 4. Evidence Index

- Table of every Findings + Recommendations row with EvidencePointer
- Slicer by EvidenceSources (delegate-source tag)
- Link-out text column to open the file in `evidence/<source>/<file>`

---

## Color palette aligned with severity

| Token | Color | Use |
|---|---|---|
| Critical | `#A4262C` (red) | Severity badges + scorecard "Gap" |
| High | `#C75B12` (orange) | Severity badges + scorecard "Partial" trending bad |
| Medium | `#A19F00` (yellow) | Severity badges |
| Low | `#0078D4` (blue) | Severity badges |
| Met | `#107C10` (green) | Score badges |
| Not assessed | `#605E5C` (gray) | Score badges + "blocked evidence" highlights |

These are our default tokens; align with the user's Power BI theme.

---

## Refresh strategy

- **Import mode**: assessment data is static per run; live connection adds complexity for little gain.
- **Per-assessment regeneration**: each new assessment adds its `scorecard.json` to the source folder and the model reloads the full series. Because rows key on the stable recommendation `id` and `assessment_key`, history accumulates without duplicates.
- **Re-assessment / diff**: the `scorecard.json` series already carries every run, so the diff page filters `Findings` and `Recommendations` by `assessment_key` and computes score deltas via the `Score Delta vs Previous Assessment` measure. No separate `History` load step is needed.

---

## Validation (local, Power BI Desktop Bridge)

After the PBIP is generated, validate it locally before treating the export as complete. This is a local, read-only edit-verify loop (no Fabric tenant mutation) run by `powerbi-report-authoring`:

1. **Structural validation**: run the authoring skill's `validate-report` to catch malformed PBIR, broken query/role bindings, or missing files.
2. **Desktop render check**: open the PBIP in Power BI Desktop and use the **Power BI Desktop Bridge** to reload and capture a screenshot of each page. The bridge is a local named-pipe IPC (`pbi-desktop-bridge-${processId}`, JSON-RPC 2.0); enable it via **File > Options and Settings > Options > Preview Features > "Enable external tool access to Power BI Desktop through secure local APIs"**. Always call `bridge.manifest` first to discover supported methods. See [Power BI Desktop Bridge overview](https://learn.microsoft.com/en-us/power-bi/developer/agentic/power-bi-desktop-bridge-overview).
3. **Fix and re-verify**: if a visual renders as an error icon or empty frame, fix the underlying `queryState` or role bindings through the authoring skill and repeat until both `validate-report` and the screenshots are clean.

This mirrors the Report Authoring skill's own generate -> validate -> screenshot -> iterate loop, and keeps the WAF assessment's read-only boundary intact (all steps are local).

## Publishing to Fabric (Phase 7, opt-in only)

Publishing the validated PBIP is a separate step that requires explicit per-session user confirmation. It delegates to `powerbi-report-management` (Fabric REST CRUD via `az rest`). Two things to confirm before publish:

- **Semantic model binding**: PBIR entity and query references must match the target workspace semantic model table names. The management skill verifies bindings before upload; a mismatch fails the publish.
- **Long-running operations**: create and updateDefinition can return `202 Accepted`. Poll the operation to completion before proceeding.

## What this skill does NOT do (v1)

- Ship a pre-built PBIX template: the schema reflects the actual pillar principles verified from Microsoft Learn at assessment time, which evolve.
- Configure row-level security or capacity-bound deployment patterns: those are concerns of the user's Fabric ALM practices.
- Incrementally append assessment history server-side: for v1, history lives in the user's local folders and is loaded at regeneration time.

---

## See also

- `common/FABRIC-WAF-CORE.md`: read-only boundary, recommendation format, scoring rubric
- `references/scorecard-schema.md`: the `scorecard.json` contract the PBIP loads
- `references/trend-storage.md`: opt-in Tier 2 Warehouse persistence + Tier 3 Rayfin portal
- `references/export-formats.md`: Tier 1 formats
- `references/assessment-workflow.md`: Phase 6 (local export) + Phase 7 (publish)
- Power BI Report Authoring skill: https://learn.microsoft.com/en-us/power-bi/developer/agentic/power-bi-report-authoring-skill-overview
- Power BI Report Design skill: https://learn.microsoft.com/en-us/power-bi/developer/agentic/power-bi-report-design-skill-overview
- Power BI Report Planner + Management skills: https://learn.microsoft.com/en-us/power-bi/developer/agentic/power-bi-planner-fabric-skill-overview
- Power BI Desktop Bridge: https://learn.microsoft.com/en-us/power-bi/developer/agentic/power-bi-desktop-bridge-overview
