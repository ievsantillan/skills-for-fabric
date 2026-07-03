# Scorecard Schema: the re-assessment / trend contract

`scorecard.json` is the canonical, machine-readable snapshot of one assessment run. It is the single contract every trend consumer reads:

- the **re-assessment diff** loads the previous run's `scorecard.json` deterministically (never re-parses markdown),
- the **markdown history index** (`WAFAssessmentHistory.md`) is appended from it,
- the optional **PBIP** living artifact loads the series of `scorecard.json` files,
- the optional **Tier 2 Warehouse** persistence upserts its rows (see `references/trend-storage.md`).

It contains no new information: it is a structured projection of the same findings and recommendations already written to the markdown report. Its shape mirrors the PBIP star schema in `references/export-pbip.md` (Assessments, Principles/Findings, Recommendations, Tradeoffs).

> **Redaction still applies.** `scorecard.json` can contain UPNs, GUIDs, and item names via `owner`, `scope`, and `evidence_pointer`. Redact before sharing externally, the same as `evidence/`. A redacted `scorecard.json` (no PII) is safe to retain long-term for trend history even when the full report folder is not.

Location: `WAFAssessmentReport-YYYY-MM-DD/scorecard.json` (one per run).

---

## Schema

Top-level object:

```json
{
  "schema_version": "1.0",
  "assessment": {
    "assessment_key": "WAFAssessmentReport-2026-07-03",
    "assessment_date": "2026-07-03",
    "mode": "e2e",
    "scope": {
      "tenant_id": "<guid>",
      "capacity_ids": ["<guid>"],
      "workspace_ids": ["<guid>"]
    },
    "skill_version": "0.3.7",
    "identity_used": "<upn-or-sp>",
    "collected_at": "2026-07-03T18:20:00Z",
    "methodology": {
      "common_core_verified": "2026-06-13",
      "pillar_references_verified": {
        "reliability": "2026-06-13",
        "security": "2026-06-13",
        "cost-optimization": "2026-06-13",
        "operational-excellence": "2026-06-13",
        "performance-efficiency": "2026-06-13"
      },
      "supplementary_references_verified": {
        "cicd-best-practices": "2026-07-03"
      }
    }
  },
  "pillars": [
    {
      "pillar_key": "operational-excellence",
      "counts": { "met": 4, "partial": 2, "gap": 1, "not_assessed": 1 },
      "principle_count": 8,
      "waf_index": 62.5
    }
  ],
  "principles": [
    {
      "principle_key": "operational-excellence::deploy-changes-safely",
      "pillar_key": "operational-excellence",
      "principle": "Deploy changes safely",
      "score": "Partial",
      "finding": "Dev and prod share one capacity; no integration-branch policy.",
      "evidence_pointer": "evidence/FabricAdmin/workspace-git-config.json"
    }
  ],
  "recommendations": [
    {
      "id": "OR003",
      "theme_id": null,
      "stable_key": "operational-excellence::deploy-changes-safely::separate-dev-prod-capacity",
      "pillars": ["operational-excellence", "reliability"],
      "primary_principle_key": "operational-excellence::deploy-changes-safely",
      "severity": "High",
      "effort": "M",
      "owner": "platform team",
      "recommendation": "Separate dev and prod into their own workspaces on separate capacities.",
      "fabric_features": ["Deployment pipelines", "Git integration"],
      "learn_citation": "Deploy changes safely",
      "status": "Open",
      "risk_accepted": false,
      "evidence_pointer": "evidence/FabricAdmin/workspace-git-config.json",
      "first_seen": "2026-07-03",
      "last_seen": "2026-07-03"
    }
  ],
  "tradeoffs": [
    {
      "recommendation_id": "OR003",
      "affected_pillar_key": "cost-optimization",
      "tradeoff": "A separate prod capacity raises baseline cost."
    }
  ]
}
```

### Field notes

- `schema_version`: bump when the shape changes so consumers can adapt.
- `assessment.*`: same values as the README stamp block in `references/assessment-report-template.md`. `methodology` carries the VERIFIED dates so drift is detectable (see below).
- `pillars[].waf_index`: the transparent maturity indicator `(met*1 + partial*0.5 + gap*0) / principle_count * 100`. It is NOT the Azure WAR questionnaire score. Comparable across runs ONLY when `principle_count` is unchanged (see drift).
- `principles[].principle_key`: stable key `"<pillar_key>::<slug-of-verbatim-heading>"`. The `principle` field keeps the verbatim heading for citation.
- `recommendations[].id`: the human-facing per-pillar ID (`R001` reliability, `SR001` security, `CR001` cost, `OR001` operational-excellence, `PR001` performance). `theme_id` is set (e.g. `C001`) when the dedup pass merged this row into a cross-pillar theme.
- `recommendations[].stable_key`: the deterministic identity used to match a recommendation across runs (see next section). `id` follows `stable_key`, not position.
- `first_seen` / `last_seen`: assessment dates; on re-assessment, `first_seen` is inherited from the matched previous row so age-of-finding is trackable.

---

## Stable recommendation IDs (match across runs)

The problem: if IDs are assigned by position each run, `R001` can mean different things in run 1 and run 2, so "did we close OR003?" is unanswerable. The fix is a deterministic `stable_key` plus carry-forward.

**`stable_key` = `"<pillar_key>::<principle_slug>::<action_slug>"`** where:

- `pillar_key` is the primary pillar (the one whose principle drives the recommendation),
- `principle_slug` is the slugified verbatim Learn heading (lowercase, spaces to `-`, punctuation dropped),
- `action_slug` is a slug of the normalized recommendation action: lowercase, drop specific identifiers (capacity/workspace names, GUIDs, numbers) so "Right-size capacity FIN-01 from F64 to F32" and a later "Right-size capacity FIN-01 from F32 to F16" share the key `right-size-capacity`.

**ID assignment procedure (Phase 5, after dedup):**

1. If `previous_assessment_folder` is set, load its `scorecard.json` and build a map `stable_key -> {id, theme_id, first_seen, status, risk_accepted}`.
2. For each current recommendation, compute `stable_key`. If it exists in the map, **reuse the previous `id`, `theme_id`, and `first_seen`** (so IDs are stable), and carry `status` / `risk_accepted` forward (see below).
3. For new `stable_key`s, assign the next free per-pillar ID (`OR004`, ...), set `first_seen` = this run's date.
4. Keep an `id-map.json` (or a table in `scorecard.json`) if you later split or merge themes, so alias anchors in `recommendations.md` still resolve.

The markdown `recommendations.md` table gains an `id` column already; this section just makes that `id` reproducible run over run.

---

## Status and Risk-Acceptance carry-forward

On a re-assessment, a recommendation the customer already triaged must not silently reset:

- If a matched `stable_key` was `In progress`, `Done`, or `Risk accepted` in the previous run, seed the current row with that `status` (and `risk_accepted`). Then let evidence override: if a `Done` / `Risk accepted` item is now scored `Gap` again by fresh evidence, flip it back to `Open` and surface it in the diff as a **regression**.
- `Done` recommendations whose principle is now `Met` drop off the active backlog but remain in `scorecard.json` with `status: "Done"` so history is complete.

---

## Methodology-drift flag

The `waf_index` and score deltas are only comparable when the principle set is unchanged. Because Microsoft Learn pages evolve, compare `assessment.methodology` across the two runs:

- If any `pillar_references_verified` date differs, or a pillar's `principle_count` changed, set a drift note in the diff: "Methodology changed for `<pillar>` (principle set differs between runs); score deltas for this pillar are indicative, not exact."
- Never present a raw index drop as a regression when the denominator changed. Flag it.

---

## History index (`WAFAssessmentHistory.md`)

A single markdown file that grows one row per run, giving the markdown path a multi-run trend without PBIP. It lives OUTSIDE the dated folders (so it is not duplicated per run); recommended location is the parent directory that holds the `WAFAssessmentReport-*/` folders.

```markdown
# Fabric WAF Assessment History

| Date | Mode | Scope | Overall index | Reliability | Security | Cost | OpEx | Perf | Open Critical | Open High | Diff |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 2026-05-01 | e2e | cap FIN-01 / ws finance-prod | 48.0 | 50 | 40 | 55 | 45 | 50 | 3 | 7 | (baseline) |
| 2026-07-03 | e2e | cap FIN-01 / ws finance-prod | 62.5 | 60 | 55 | 70 | 62.5 | 65 | 1 | 4 | [diff](WAFAssessmentReport-2026-07-03/diff-vs-2026-05-01.md) |
```

Each new run appends its row and links its `diff-vs-<prev>.md`. A parallel `history.csv` (same columns) can be emitted for spreadsheet trend charts and is the simplest thing to load into the Tier 2 Warehouse. Keep both PII-free (indexes and counts only, no UPNs) so they are safe to retain even when report folders are not.

---

## See also

- `common/FABRIC-WAF-CORE.md`: scoring rubric, recommendation format (incl. stable ID + carry-forward)
- `references/assessment-report-template.md`: folder structure + where `scorecard.json` and history live
- `references/assessment-workflow.md`: Phase 6 emission + re-assessment/diff workflow
- `references/export-pbip.md`: PBIP loads the `scorecard.json` series
- `references/trend-storage.md`: Tier 2 Warehouse persistence + Tier 3 Rayfin portal (opt-in)
