# Changelog

User-facing changes for the public Microsoft Fabric Skills release.

## [0.3.4] - 2026-06-13

### Added

- **`skills/fabric-waf`**: assess a Microsoft Fabric tenant, capacity, or workspace against the [Microsoft Fabric Well-Architected Framework](https://learn.microsoft.com/en-us/azure/well-architected/microsoft-fabric/) across all 5 pillars (Reliability, Security, Cost Optimization, Operational Excellence, Performance Efficiency). Three modes: `e2e` (all pillars), `pillar:<name>` (single pillar), and `guidance-only` (Q&A without evidence collection or report emission). Ships with 12 references: one deep-dive per pillar (each carrying a `VERIFIED` stamp against the live Microsoft Learn page, a workload coverage matrix across 8 Fabric workloads, verbatim Learn H2 headings as principles, inline Tradeoff callouts, and an evidence checklist), plus cross-pillar `tradeoffs.md`, 7-phase `assessment-workflow.md` (intake, pre-flight permissions + capacity throttling check + delegation smoke-test, evidence gathering with sampling and redaction, scoring, recommendations, local emit, optional publish), `assessment-report-template.md` (layered folder + per-principle block format with PowerShell bulk-redact one-liner), `evidence-checklist.md`, `export-formats.md` (PDF / Excel / Word / CSV guidance), `export-pbip.md` (optional Tier 1.5 PBIP project: star schema, DAX measures, 4 page layouts, severity color palette), and `example-assessment.md` (concrete KQL / T-SQL / REST queries against Capacity Metrics App, M365 audit log, workspace inventory).
- **`agents/FabricWAF.agent.md`**: orchestrates the 7-phase WAF assessment workflow: intake + scope confirmation, pre-flight permissions check and capacity-throttling self-awareness, evidence gathering, principle scoring (Met / Partial / Gap / Not assessed), recommendation generation with severity + effort + Microsoft Learn citation, layered markdown report emission to a date-stamped folder, and optional Phase 7 publish to Fabric. **Introduces a new agent-to-agent delegation convention in this repository**: FabricWAF's `delegates_to:` lists `FabricAdmin` as a peer agent for tenant / workspace evidence aggregation (capacity utilization, RBAC inventory, audit-log queries, secrets discipline), alongside the existing `-consumption-cli` and `-operations-cli` skills for item-level evidence. Includes an explicit no-circular-delegation rule (FabricAdmin must not delegate back to FabricWAF) and a read-only trust boundary (no POST / PUT / PATCH / DELETE against Fabric REST or Kusto management endpoints during assessment; local PBIP authoring is permitted; Phase 7 publish is opt-in and requires explicit per-session user confirmation).
- **`common/FABRIC-WAF-CORE.md`**: shared body of knowledge consumed by both the `fabric-waf` skill and the `FabricWAF` agent. Contains: 5-pillar summary with Microsoft Learn URLs; categorical scoring rubric (Met / Partial / Gap / Not assessed: explicitly NO maturity model, since CMMI is not a Fabric WAF concept); severity (Critical / High / Medium / Low) and effort (S / M / L) scales labeled "our convention"; recommendation format with verbatim Learn citation requirement; no-SDK disclaimer (no Fabric WAF SDK or assessment REST API exists; evidence flows through existing `-cli` skills and Microsoft-cited open-source accelerators `fabric-cost-analysis` and FUAM); glossary (CU, F-SKU, FUAM, OneLake, smoothing window, autoscale, Capacity / Workspace / Fabric Admin roles); read-only boundary definition; relationship to the Azure WAF; heading-anchor citation convention (verbatim heading text, not slugified anchors).
- **`fabric-skills`, `fabric-consumption`, and `fabric-operations` plugin bundles expanded**: each of these three bundles now ships `skills/fabric-waf`, `agents/FabricWAF.agent.md`, and `common/FABRIC-WAF-CORE.md`. The `fabric-authoring` and `powerbi-authoring` bundles intentionally do not ship WAF (it is guidance / consumption-style, not authoring). Reinstall via `/plugin install fabric-skills@fabric-collection` (or the equivalent for `fabric-consumption` / `fabric-operations`) to pick up the new skill and agent.
- **2 new prompt examples**: `prompt_examples/WAFAssessment.txt` (e2e mode trigger with PBIP export) and `prompt_examples/WAFPillarReview.txt` (single-pillar mode trigger).

### Changed

- **`.gitignore` excludes `WAFAssessmentReport-*/` and `WAFAssessmentReport/`**: assessment report folders may contain PII (UPNs, capacity / workspace GUIDs, item names that reveal customer/product confidentiality, raw evidence rows) and must not be committed by default.

## [0.3.3] - 2026-06-07

### Added

- **`powerbi-report-planning`**: guided requirements-to-implementation workflow for new Power BI reports and dashboards built from semantic models, datasets, or PBIP projects. Use to plan then implement a report end-to-end: define audience, scope, page plan, design direction, dependencies, and delivery target, then produce a locked report spec with explicit approval before any PBIR authoring begins. For direct authoring without the planning gate, invoke `powerbi-report-authoring` directly.
- **`powerbi-report-design`**: visual design guidance for Power BI reports before any PBIR files are written. Use to choose tone, signature, page archetypes, chart types, layout, color, typography, theme direction, and accessibility approach; to redesign/restyle an existing report or apply a brand; or to critique chart and layout choices. Produces a design contract that downstream authoring consumes. Ships with 19 references covering accessibility, anti-patterns, page archetypes (analytical canvas, comparative benchmark, executive summary, narrative story, operational monitor), brownfield migration, chart selection, design brief, interactivity, pre-flight checklist, signatures, tone catalog, typography, and a visual cookbook.
- **`powerbi-report-authoring`**: create and modify Power BI report files in PBIR/PBIP format using the `powerbi-report-author` and `powerbi-desktop` CLIs. Implements an approved report spec or design brief; adds or edits pages, visuals, filters, slicers, bookmarks, themes, and formatting; validates PBIR and verifies rendering in Power BI Desktop. Ships with 23 references covering authoring, cartesian charts, color strategy, conditional formatting, expressions, filter pane, filters, formatting (overview + details), image, page formatting, Power BI Desktop, the `powerbi-report-author` CLI, re-theming, screenshot review, shape, slicers, table, textbox, theming, and version control. For open-ended visual design choices, invoke `powerbi-report-design` first.
- **`powerbi-report-management`**: manage Power BI report workspace items in Microsoft Fabric via `az rest` CLI against the Fabric REST API. Create reports from PBIR definitions, get or download report definitions, update report definitions or properties, list workspace reports, and delete reports. For report layout authoring (pages, visuals, filters, formatting), use `powerbi-report-authoring` instead.
- **`powerbi-authoring` plugin bundle expanded**: the dedicated `powerbi-authoring` plugin now ships the four new `powerbi-report-*` skills alongside `semantic-model-authoring` and `check-updates`, with the `powerbi-modeling-mcp` server pre-configured. Reinstall via `/plugin install powerbi-authoring@fabric-collection` to pick up the new report skills.

### Changed

- **`semantic-model-authoring` DAX performance references refined**: added Microsoft Learn further-reading links for DAX engine tracing, horizontal fusion, and Direct Lake query performance in `dax-perf-decision-guide.md` and `dax-perf-patterns.md`; renamed scenario-specific DAX examples to use generic names; rewrote DAX examples to be self-contained so they're easier to read on their own.

## [0.3.2] - 2026-06-03

### Added

- **`semantic-model-authoring`**: develop and manage Power BI semantic models across Power BI Desktop, PBIP projects, and the Fabric Service. Covers creating models (Import, DirectQuery, Direct Lake), editing measures/tables/columns/relationships, deploying to Fabric workspaces, refreshing, configuring data sources and permissions, and DAX performance optimization. Ships with 11 reference guides (connection binding, DAX guidelines, DAX performance decision guide, DAX performance patterns, Direct Lake guidelines, modeling guidelines, naming conventions, PBIP, semantic-model AI readiness, semantic-model REST API, TMDL guidelines). **Replaces `powerbi-authoring-cli`.**
- **`semantic-model-consumption`**: execute raw DAX queries and inspect metadata of Microsoft Fabric Power BI semantic models via the MCP server `ExecuteQuery` tool. Use when you already know the DAX (EVALUATE statements) or need to inspect tables, columns, measures, relationships, and hierarchies via INFO functions. **Replaces `powerbi-consumption-cli`.**
- **`fabriciq`**: answer business questions by querying Power BI reports and dashboards through the FabricIQ MCP endpoint. Orchestrates artifact discovery, schema inspection, entity-value resolution, DAX generation, and query execution; returns plain-language answers. Use for natural-language questions about Power BI report/dashboard content (use `semantic-model-consumption` for raw DAX).
- **`FabricIQ` agent**: answers questions about Power BI artifacts (reports and semantic models) by discovering artifacts, inspecting metadata and schemas, resolving entity values, generating DAX, and executing queries against the Fabric MCP endpoint. Delegates to `fabriciq`.
- **Dedicated `powerbi-authoring` plugin bundle**: ships `semantic-model-authoring` and `check-updates` with the `powerbi-modeling-mcp` server (`@microsoft/powerbi-modeling-mcp`) pre-configured for fine-grained semantic-model modeling operations. Install via `/plugin install powerbi-authoring@fabric-collection`.
- **`dataflows-authoring-cli` reference docs (3 new)**: `output-destinations.md` (Lakehouse/Warehouse/SQL DB output destination patterns including staging behavior, schema mapping, and refresh semantics), `connection-management.md` (creating, binding, and rotating connection IDs for Dataflows Gen2), and `mashup-preview.md` (inspecting and validating Power Query M before publishing).
- **`spark-operations-cli` automated diagnostic workflow**: new `references/automated-diagnostic-workflow.md` for end-to-end Spark/Livy diagnostics: job triage → executor/driver log mining → Spark Advisor findings → mitigation recommendations.
- **`synapse-migration` deep resources (12 new)**: capacity sizing, connector refactoring, external Hive Metastore migration, feature parity matrix, lake database migration, library compatibility, migration gotchas, migration orchestrator, migration report, security and governance, Spark item migration, Spark pool migration, and validation/testing.
- **`EVENTHOUSE-CONSUMPTION-CORE` common reference**: shared Eventhouse/KQL consumption patterns surfaced via the `fabric-authoring` plugin bundle.

### Changed

- **`powerbi-authoring-cli` renamed to `semantic-model-authoring`**: aligns the skill name with the underlying Microsoft Fabric / Power BI artifact (a *semantic model*) rather than the surface tool. Same coverage of model authoring plus an expanded reference library. Re-invoke as `semantic-model-authoring` going forward.
- **`powerbi-consumption-cli` renamed to `semantic-model-consumption`**: same rationale; same DAX query / metadata surface. Re-invoke as `semantic-model-consumption` going forward.

## [0.3.1] - 2026-05-10

### Added

- **`activator-authoring-cli`**: create alerts, notifications, and automated actions on Fabric data and events via Fabric REST API and `az rest` CLI. Covers Activator/Reflex item creation, trigger configuration, action wiring (Teams messages, emails, Fabric item runs), and connections to Eventhouse, Eventstream, Real-Time Hub, and Digital Twin Builder.
- **`activator-consumption-cli`**: read-only inspection of existing Activator alerts, notifications, and automated actions via `az rest`. List alerts in a workspace, inspect alert configuration, decode `ReflexEntities.json` definitions.

### Changed

- **`spark-diagnostics-cli` renamed to `spark-operations-cli`**: aligned with the three-category naming convention (`-authoring-`, `-consumption-`, `-operations-`). Same skill, same diagnostic surface (failed Spark jobs, unhealthy Livy sessions, OOM/shuffle/skew, driver/executor logs, Spark Advisor findings): only the name has changed. Re-invoke as `spark-operations-cli` going forward.

### Fixed

- **`/plugin update` now works again for users who installed under the legacy `skills-for-fabric@fabric-collection` id.** When the bundle was renamed in 0.3.0 (`skills-for-fabric` → `fabric-skills`), the old plugin id was dropped from `marketplace.json`, which silently broke `/plugin update skills-for-fabric@fabric-collection` for everyone still on the legacy id (`Plugin "skills-for-fabric" not found in marketplace`). The legacy id is restored as a deprecated alias of `fabric-skills@fabric-collection`: running `/plugin update` under either name now pulls the canonical `fabric-skills` payload. To migrate your installed entry to the canonical id (optional, recommended cleanup): `/plugin uninstall skills-for-fabric@fabric-collection` then `/plugin install fabric-skills@fabric-collection`.
- **`check-updates` skill works inside Copilot CLI plugin installs.** The skill assumed a `package.json` and a `.git/` directory at the install root, but the Copilot CLI plugin install layout (`~/.copilot/installed-plugins/fabric-collection/fabric-skills/`) has neither: only `.github/plugin/plugin.json`. Step 1 (read local version), Step 2 (parse repository URL), and Method A (`git fetch origin main`) now read the manifest path that matches the actual install layout. The "Update Available" banner no longer references the `install.ps1` / `install.sh` scripts that were removed from the public release in 0.3.0.

## [0.3.0] - 2026-05-06

### Added

- **Plugin bundles for focused installation**
  - `fabric-skills` - complete bundle for Fabric authoring, consumption, operations, migration, and end-to-end architecture workflows.
  - `fabric-authoring` - developer-oriented skills for REST APIs, CLI automation, notebooks, T-SQL, KQL, Eventstreams, Dataflows Gen2, semantic models, and medallion architecture.
  - `fabric-consumption` - read-only and interactive exploration skills for SQL, Spark/Lakehouse, Power BI semantic models, Eventhouse/KQL, Eventstreams, Dataflows Gen2, and catalog search.
  - `fabric-operations` - diagnostics-focused bundle for warehouse performance investigation.
- **Dataflows Gen2 skills**
  - `dataflows-authoring-cli` for creating, updating, and managing Dataflows Gen2 definitions and Power Query M mashups.
  - `dataflows-consumption-cli` for inspecting, monitoring, and exploring Dataflows Gen2 artifacts.
  - `dataflows-save-as-authoring-cli` for Dataflows Gen1 to Gen2 save-as upgrade workflows, readiness assessment, risk checks, and validation.
- **Real-Time Intelligence skills**
  - `eventhouse-consumption-cli` for read-only KQL queries and schema discovery.
  - `eventhouse-authoring-cli` for KQL table, ingestion, policy, function, and materialized-view management.
  - `eventstream-consumption-cli` for inspecting and monitoring Eventstream topologies.
  - `eventstream-authoring-cli` for creating and deploying Eventstream sources, transformations, and destinations.
- **Search and discovery**
  - `search-consumption-cli` for finding Fabric items across the OneLake catalog by name, description, workspace, and type.
- **Migration skills**
  - `databricks-migration` for Databricks to Fabric migration planning and code mapping.
  - `synapse-migration` for Azure Synapse Analytics to Fabric migration.
  - `hdinsight-migration` for Azure HDInsight to Fabric migration.
- **Power BI authoring coverage**
  - `powerbi-authoring-cli` is now included in the authoring and full bundles.

### Changed

- **Plugin installation is now bundle-scoped.** Installing `fabric-authoring`, `fabric-consumption`, or `fabric-operations` installs only the skills and resources for that bundle instead of copying the entire repository.
- **Plugin packages are self-contained.** Public plugin folders include the materialized skills, agents, common references, and MCP configuration needed for GitHub-based plugin installation.
- **MCP configuration is scoped per bundle.** `fabric-consumption` and `fabric-skills` include the Power BI query MCP server configuration; authoring and operations bundles do not include unused MCP configuration.
- **`sqldw-monitoring-cli` was renamed to `sqldw-operations-cli`.** The new name aligns with the authoring, consumption, and operations skill categories.
- **Catalog search is now part of item discovery guidance.** Skills can use the Fabric Catalog Search API alongside list-and-filter workflows.
- **Version updated to `0.3.0`.**

### Available skills in this release

| Category | Skills |
|----------|--------|
| Authoring | `sqldw-authoring-cli`, `spark-authoring-cli`, `eventhouse-authoring-cli`, `eventstream-authoring-cli`, `powerbi-authoring-cli`, `dataflows-authoring-cli`, `dataflows-save-as-authoring-cli` |
| Consumption | `semantic-model-consumption`, `fabriciq`, `sqldw-consumption-cli`, `spark-consumption-cli`, `eventhouse-consumption-cli`, `eventstream-consumption-cli`, `dataflows-consumption-cli`, `search-consumption-cli` |
| Operations | `sqldw-operations-cli` |
| Migration and end-to-end | `databricks-migration`, `synapse-migration`, `hdinsight-migration`, `e2e-medallion-architecture` |
| Utility | `check-updates` |

## Earlier releases

Earlier releases introduced the initial Fabric Skills marketplace, update checking, SQL data warehouse authoring and consumption skills, Spark skills, MCP setup scripts, and cross-tool configuration files.
