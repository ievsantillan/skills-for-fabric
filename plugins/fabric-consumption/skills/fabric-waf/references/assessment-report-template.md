# Assessment Report Template

Default folder structure for a Fabric WAF assessment report. Layered folder shape (our design choice; mirrors `FabricAdmin`'s `WorkspaceReport/` precedent in this repo). Default folder name is **date-stamped** by our convention: `WAFAssessmentReport-YYYY-MM-DD/`.

> The `WAFAssessmentReport-*/` pattern is excluded from git by the repository `.gitignore`. Reports may contain PII; redact before sharing.

---

## Folder structure

```
WAFAssessmentReport-YYYY-MM-DD/
├── README.md                       # Executive summary (scorecard, top risks, top quick wins)
├── reliability.md                  # Per-principle blocks (Standard detail)
├── security.md
├── cost-optimization.md
├── operational-excellence.md
├── performance-efficiency.md
├── recommendations.md              # Single deduped backlog
├── diff-vs-<prev-date>.md          # Only present in re-assessment runs
├── glossary-link.md                # Pointer to common/FABRIC-WAF-CORE.md glossary
└── evidence/
    ├── README.md                   # What's here + redaction status + sampling rule used
    ├── blocked-evidence.md         # Items marked Not assessed and why
    ├── FabricAdmin/                # Raw tenant/workspace evidence
    ├── capacity-metrics/           # KQL output from Capacity Metrics App
    ├── audit-log/                  # M365 audit log queries
    ├── workspace-inventory/        # T-SQL / REST API outputs
    └── item-cli/                   # Output from each -cli skill, one folder per skill
```

Mode scaling:

- `e2e`: full folder
- `pillar:<name>`: README (pillar-scoped) + that pillar file + filtered recommendations + evidence/
- `guidance-only`: no folder; Q&A only

---

## README.md structure (executive summary)

1. **Header block**: date, scope summary, mode, version stamps (skill version, common-core VERIFIED date, each pillar reference VERIFIED date)
2. **Scorecard banner**: overall + 5 pillars, counts of Met / Partial / Gap / Not assessed
3. **Top 5 risks**: severity-sorted from recommendations.md
4. **Top 5 quick wins**: effort-sorted (S first), Critical / High severity first within S
5. **Diff highlights** (if re-assessment): closed gaps + new gaps + persisting-Critical-or-High
6. **Pointers**: links to each pillar file, recommendations.md, evidence/
7. **Glossary link**: for non-architect audiences (capacity admins, exec sponsors)

Keep README executive-readable. Detail belongs in the pillar files.

---

## Per-pillar file structure (`<pillar>.md`)

1. **Pillar header**: name, Learn URL, VERIFIED stamp of the pillar reference used
2. **Pillar scorecard**: counts per category + a one-line health verdict
3. **Risk Acceptance section** (optional): explicit list of `Gap` items the business has accepted with sign-off (our convention)
4. **Per-principle blocks**: one per H2 from the Learn page, in the order Learn presents them. Standard detail (see below).
5. **Pillar-local tradeoffs**: cross-pillar tradeoffs surfaced by this pillar's recommendations

## Hyperlinking conventions (markdown -> clickable HTML export)

- **Pillar Learn URL**: write it as a markdown link, not a bare URL, e.g. `[Microsoft Learn: Reliability for Microsoft Fabric workloads](https://learn.microsoft.com/en-us/azure/well-architected/microsoft-fabric/reliability)`.
- **README References section**: add a "References" section to `README.md` linking the official Microsoft Fabric WAF docs (the [landing page](https://learn.microsoft.com/en-us/azure/well-architected/microsoft-fabric/) plus the five pillar pages, and the [WAF overview](https://learn.microsoft.com/en-us/azure/well-architected/) + [assessment tool](https://learn.microsoft.com/en-us/assessments/azure-architecture-review/)).
- **Recommendation IDs are cross-referenced as links**: anchor each row of the consolidated `recommendations.md` table by prefixing the ID cell with `<span id="rec-<ID>"></span>`. When the dedup pass merges per-pillar IDs into a theme row (e.g. `R001`, `PR001`, `OR001` -> `C001`), add alias anchors on that row for each merged ID so references still resolve. Then linkify every inline ID mention in prose to `[<ID>](#rec-<ID>)`. In the combined HTML export this makes IDs clickable jumps to the backlog. (A small linkify script can do steps automatically; keep it idempotent.)

### Per-principle block format (Standard detail)

```markdown
### <Verbatim Learn H2 heading>

- **Score**: <Met | Partial | Gap | Not assessed>
- **Finding**: <Current state vs WAF principle target; descriptive, 1–3 sentences>
- **Evidence**: <Pointer to evidence/<path>; if Not assessed, the reason>
- **Recommendation**: <Imperative action; one line>
- **Severity**: <Critical | High | Medium | Low>
- **Effort**: <S | M | L>
- **Owner**: <role or person>
- **Fabric features**: <named features that close the gap>
- **Learn citation**: <verbatim heading text> in the Microsoft Learn <pillar> pillar
- **Tradeoffs**: <pillars affected by this recommendation and how>
```

Each block runs ~8–15 lines. Findings and Recommendations are **separated** (Finding = state; Recommendation = action).

---

## recommendations.md structure (single deduped backlog)

A markdown table copyable into Jira / Azure Boards. After per-pillar scoring, run the dedup pass: merge rows that target the same action across pillars.

| ID | Severity | Effort | Owner | Pillars | Principle | Recommendation | Fabric features | Status | Evidence |
|---|---|---|---|---|---|---|---|---|---|
| R001 | High | M | Capacity Admin | [cost-optimization, performance-efficiency] | "Identify key cost drivers" / "Plan capacity intentionally" | Right-size capacity X from F64 to F32 based on 14-day p95 CU utilization of 38%. | Capacity Metrics App; F-SKU management | Open | evidence/capacity-metrics/cu-utilization-cap-X.kql + .csv |

Sort by `Severity DESC, Effort ASC` for backlog grooming.

---

## evidence/ appendix structure

- `README.md`: table of contents; redaction status; sampling rule used (per pillar/per item type); date/time of collection; identity used
- `blocked-evidence.md`: every principle marked `Not assessed`, with reason (missing permission, delegation failure, scope exclusion, query timeout)
- Per-source subfolders: raw query outputs (KQL, T-SQL, REST), JMESPath expressions, collection timestamps. Files named `<source>-<short-description>.<ext>`. Each file's top has a header block: source skill, query verbatim, timestamp, identity.

---

## Redaction (privacy)

Before committing or sharing the report, redact the following from `evidence/`:

- User UPNs and email addresses
- Connection strings, secrets, tokens
- Capacity and workspace GUIDs (if sharing externally)
- Item names that reveal customer/product confidentiality

### PowerShell bulk-redact one-liner

```powershell
# Replace UPN-like strings; back up first.
Get-ChildItem -Path .\WAFAssessmentReport-2026-06-13\evidence\ -Recurse -File `
  | ForEach-Object { (Get-Content $_.FullName -Raw) `
    -replace '\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b','<redacted-upn>' `
    -replace '\b[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}\b','<redacted-guid>' `
    | Set-Content $_.FullName }
```

> Test on a copy. The GUID pattern matches any GUID, including ones you may want to keep (e.g., principle reference IDs). Refine per assessment.

---

## Version stamping

Every assessment writes the following stamp block at the top of `README.md`:

```yaml
assessment_version:
  skill_version: <from package.json at run time>
  common_core_verified: 2026-06-13
  pillar_references_verified:
    reliability: 2026-06-13
    security: 2026-06-13
    cost_optimization: 2026-06-13
    operational_excellence: 2026-06-13
    performance_efficiency: 2026-06-13
  collected_at: <ISO timestamp>
  identity_used: <UPN or service principal name>
```

This makes the assessment auditable and supports the re-assessment / diff workflow.

---

## See also

- `common/FABRIC-WAF-CORE.md`: scoring rubric, recommendation format, glossary
- `references/assessment-workflow.md`: phases that produce this output
- `references/export-formats.md`: alternate formats (HTML / Excel / Word / CSV / PBIP)
- `references/example-assessment.md`: concrete sample
