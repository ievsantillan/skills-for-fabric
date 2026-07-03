<!-- VERIFIED: 2026-07-03 against https://github.com/microsoft/rayfin (Tier 3 caveats) -->

# Trend Storage: Fabric Warehouse (Tier 2) and Rayfin portal (Tier 3)

The always-on Tier 1 outputs (`scorecard.json` per run + `WAFAssessmentHistory.md`) already let a customer compare a baseline against later runs and track improvement over time locally, with no infrastructure. This reference documents two **opt-in** ways to scale that trend to a shared, queryable store and a hosted portal.

> **These tiers write to / provision Fabric resources and are OUTSIDE the read-only assessment boundary.** Treat them exactly like the Phase 7 publish step in `common/FABRIC-WAF-CORE.md`: they run only on explicit per-session user confirmation, only after the report has been redacted, and never during an assessment. The assessment itself remains read-only and produces only local files.

The contract for both tiers is the same `scorecard.json` defined in `references/scorecard-schema.md`. Nothing here re-derives assessment data; it only loads the snapshot.

---

## When to use which layer

| Need | Use |
|---|---|
| One team, self-service, no infra | Tier 1 `scorecard.json` + `WAFAssessmentHistory.md` (+ optional PBIP) |
| Central BI across many workspaces / capacities / customers, governed | **Tier 2: Fabric Warehouse + Direct Lake Power BI** |
| Hosted, multi-user web portal with sign-in and in-app status write-back | **Tier 3: Rayfin app** over the Tier 2 store |

Do NOT use a KQL database / Eventhouse for this: assessments are periodic (a few runs per quarter), not high-frequency telemetry. A Warehouse (or Lakehouse) is the right fit.

---

## Tier 2: persist to a Fabric Warehouse

Recommended store: a **Warehouse**, because T-SQL `MERGE` gives clean upsert semantics for stable-ID matching and status / risk-acceptance carry-forward across runs. (A Lakehouse Delta table is a valid append-only alternative with Direct Lake, but you then manage carry-forward with merge-on-read logic instead of `MERGE`.)

All DDL and load run through the **`sqldw-authoring-cli`** skill (it is write-capable and, per the read-only boundary, is used only in this opt-in Tier 2 step, never during assessment).

### Schema (mirrors the scorecard.json contract)

```sql
CREATE TABLE dbo.Assessments (
    AssessmentKey     VARCHAR(64)  NOT NULL,
    AssessmentDate    DATE         NOT NULL,
    Mode              VARCHAR(32)   NOT NULL,
    TenantId          VARCHAR(64),
    CapacityIds       VARCHAR(2000),
    WorkspaceIds      VARCHAR(2000),
    SkillVersion      VARCHAR(16),
    IdentityUsed      VARCHAR(256),
    CollectedAt       DATETIME2,
    CONSTRAINT PK_Assessments PRIMARY KEY NONCLUSTERED (AssessmentKey) NOT ENFORCED
);

CREATE TABLE dbo.Findings (
    AssessmentKey     VARCHAR(64)  NOT NULL,
    PrincipleKey      VARCHAR(128) NOT NULL,
    PillarKey         VARCHAR(32)  NOT NULL,
    Principle         VARCHAR(256) NOT NULL,
    Score             VARCHAR(16)  NOT NULL,   -- Met / Partial / Gap / Not assessed
    FindingText       VARCHAR(4000),
    EvidencePointer   VARCHAR(1000)
);

CREATE TABLE dbo.Recommendations (
    AssessmentKey     VARCHAR(64)  NOT NULL,
    Id                VARCHAR(16)  NOT NULL,   -- stable per-pillar id (OR003, ...)
    StableKey         VARCHAR(400) NOT NULL,   -- deterministic identity across runs
    ThemeId           VARCHAR(16),
    Pillars           VARCHAR(200) NOT NULL,   -- pipe-separated
    PrimaryPrincipleKey VARCHAR(128),
    Severity          VARCHAR(16)  NOT NULL,
    Effort            VARCHAR(4)   NOT NULL,
    Owner             VARCHAR(256),
    RecommendationText VARCHAR(4000) NOT NULL,
    FabricFeatures    VARCHAR(1000),
    Status            VARCHAR(16)  NOT NULL,   -- Open / In progress / Done / Risk accepted
    RiskAccepted      BIT          NOT NULL DEFAULT 0,
    EvidencePointer   VARCHAR(1000),
    FirstSeen         DATE,
    LastSeen          DATE
);

CREATE TABLE dbo.Tradeoffs (
    AssessmentKey     VARCHAR(64)  NOT NULL,
    RecommendationId  VARCHAR(16)  NOT NULL,
    AffectedPillarKey VARCHAR(32)  NOT NULL,
    TradeoffText      VARCHAR(2000)
);
```

`Findings` and `Tradeoffs` are append-only per `AssessmentKey` (each run is an immutable snapshot). `Recommendations` is the one table where you may want an upsert so the "current state" of a stable recommendation reflects the latest run while history is preserved by `AssessmentKey`.

### Load pattern (per run)

1. Redact `scorecard.json` (UPNs, GUIDs, confidential item names) exactly as `evidence/`.
2. Stage the redacted `scorecard.json` (upload to OneLake / a Warehouse staging table, or `INSERT ... SELECT ... OPENJSON`).
3. Insert `Assessments`, `Findings`, `Tradeoffs` rows for this `AssessmentKey`.
4. `MERGE` `Recommendations` on the stable identity so a re-run keeps one logical row per recommendation and carries `Status` / `RiskAccepted` / `FirstSeen` forward:

```sql
MERGE dbo.Recommendations AS tgt
USING @incoming AS src
    ON tgt.StableKey = src.StableKey
       AND tgt.AssessmentKey = src.AssessmentKey   -- keep per-run rows; drop this clause for a single current-state row
WHEN MATCHED THEN UPDATE SET
    tgt.Status = src.Status,
    tgt.RiskAccepted = src.RiskAccepted,
    tgt.Severity = src.Severity,
    tgt.LastSeen = src.LastSeen
WHEN NOT MATCHED BY TARGET THEN
    INSERT (AssessmentKey, Id, StableKey, ThemeId, Pillars, PrimaryPrincipleKey, Severity, Effort,
            Owner, RecommendationText, FabricFeatures, Status, RiskAccepted, EvidencePointer, FirstSeen, LastSeen)
    VALUES (src.AssessmentKey, src.Id, src.StableKey, src.ThemeId, src.Pillars, src.PrimaryPrincipleKey,
            src.Severity, src.Effort, src.Owner, src.RecommendationText, src.FabricFeatures, src.Status,
            src.RiskAccepted, src.EvidencePointer, src.FirstSeen, src.LastSeen);
```

> Fabric Warehouse supports a limited T-SQL surface. Validate `MERGE` / `OPENJSON` availability against the current [Warehouse T-SQL surface area](https://learn.microsoft.com/en-us/fabric/data-warehouse/tsql-surface-area) before relying on them; if `MERGE` is unavailable, fall back to `DELETE` + `INSERT` of the current-state row inside a transaction. Delegate all of this to `sqldw-authoring-cli`.

### Reporting on top

Build a Direct Lake or import semantic model over these four tables (the same star schema as `references/export-pbip.md`, so the DAX measures and the 4 report pages carry over) and connect a Power BI report. This is the governed, multi-assessment version of the local PBIP: pillar-index trend lines, open Critical/High over time, age-of-finding from `FirstSeen`, and per-workspace or per-customer slicers.

---

## Tier 3: Rayfin portal (optional, separate build)

[Rayfin](https://github.com/microsoft/rayfin) is a Microsoft Backend-as-a-Service on Fabric: you declare a data model with TypeScript decorators and `npx rayfin up` provisions the database, authentication, data APIs, storage, and hosting. A Rayfin app is the right choice when you want a **hosted, interactive portal** rather than a Power BI report: multi-user sign-in, drill-down across many assessments and customers, and in-app write-back (for example, letting an owner set a recommendation's `Status` to `In progress` directly in the UI, which then flows back into the store).

Sketch:

- Model `Assessment`, `Finding`, `Recommendation`, and `Tradeoff` entities matching the `scorecard.json` contract.
- Ingest each run's redacted `scorecard.json` (upload via the app's data API, or point Rayfin at the Tier 2 Warehouse as the backing store).
- Pages: portfolio overview (index trend across customers), assessment detail, recommendation backlog with editable status, and an evidence index.

**Caveats (why this is Tier 3, not default):**

- It is a **separate deliverable** with its own project, hosting, and lifecycle. It is not part of the `fabric-waf` skill and should live in its own repo / skill.
- Rayfin is **preview**; APIs and behavior may change before GA.
- It **provisions and writes Fabric resources**, so it is firmly outside the assessment's read-only boundary and requires the same explicit opt-in and redaction as Tier 2.
- Use the `@authenticated` data role for any write path; the `@anonymous` role is preview-only and is rejected at deploy, so do not rely on it. For read-only public showcases, serve pre-redacted static JSON instead.

For a single team's baseline-to-improvement loop, Tier 1 plus the local PBIP already covers the need at far lower cost; reach for Rayfin only when a hosted multi-user portal is the actual requirement.

---

## See also

- `references/scorecard-schema.md`: the `scorecard.json` contract both tiers load
- `references/export-pbip.md`: the local star schema this Warehouse schema mirrors
- `common/FABRIC-WAF-CORE.md`: read-only trust boundary (why Tier 2/3 are opt-in)
- Delegate skill (Tier 2 writes): `sqldw-authoring-cli`
- Rayfin: https://github.com/microsoft/rayfin
