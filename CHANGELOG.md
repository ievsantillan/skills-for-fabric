# Changelog

User-facing changes for the public Microsoft Fabric Skills release.

## [0.3.7] - 2026-07-03

### Added

- **`skills/fabric-waf`**: assess a Microsoft Fabric tenant, capacity, or workspace against the [Microsoft Fabric Well-Architected Framework](https://learn.microsoft.com/en-us/azure/well-architected/microsoft-fabric/) across all 5 pillars (Reliability, Security, Cost Optimization, Operational Excellence, Performance Efficiency). Three modes: `e2e` (all pillars), `pillar:<name>` (single pillar), and `guidance-only` (Q&A without evidence collection or report emission). Ships with 13 references: one deep-dive per pillar (each carrying a `VERIFIED` stamp against the live Microsoft Learn page, a workload coverage matrix across 8 Fabric workloads, verbatim Learn H2 headings as principles, inline Tradeoff callouts, and an evidence checklist), plus cross-pillar `tradeoffs.md`, 7-phase `assessment-workflow.md` (intake, pre-flight permissions + capacity throttling check + delegation smoke-test, evidence gathering with sampling and redaction, scoring, recommendations, local emit, optional publish), `assessment-report-template.md` (layered folder + per-principle block format with PowerShell bulk-redact one-liner), `evidence-checklist.md`, `export-formats.md` (HTML / Excel / Word / CSV guidance), `export-pbip.md` (optional Tier 1.5 PBIP project: star schema, DAX measures, 4 page layouts, severity color palette), and `example-assessment.md` (concrete KQL / T-SQL / REST queries against Capacity Metrics App, M365 audit log, workspace inventory).
- **`agents/FabricWAF.agent.md`**: orchestrates the 7-phase WAF assessment workflow: intake + scope confirmation, pre-flight permissions check and capacity-throttling self-awareness, evidence gathering, principle scoring (Met / Partial / Gap / Not assessed), recommendation generation with severity + effort + Microsoft Learn citation, layered markdown report emission to a date-stamped folder, and optional Phase 7 publish to Fabric. **Introduces a new agent-to-agent delegation convention in this repository**: FabricWAF's `delegates_to:` lists `FabricAdmin` as a peer agent for tenant / workspace evidence aggregation (capacity utilization, RBAC inventory, audit-log queries, secrets discipline), alongside the existing `-consumption-cli` and `-operations-cli` skills for item-level evidence. Includes an explicit no-circular-delegation rule (FabricAdmin must not delegate back to FabricWAF) and a read-only trust boundary (no POST / PUT / PATCH / DELETE against Fabric REST or Kusto management endpoints during assessment; local PBIP authoring is permitted; Phase 7 publish is opt-in and requires explicit per-session user confirmation).
- **`common/FABRIC-WAF-CORE.md`**: shared body of knowledge consumed by both the `fabric-waf` skill and the `FabricWAF` agent. Contains: 5-pillar summary with Microsoft Learn URLs; categorical scoring rubric (Met / Partial / Gap / Not assessed: explicitly NO maturity model, since CMMI is not a Fabric WAF concept); severity (Critical / High / Medium / Low) and effort (S / M / L) scales labeled "our convention"; recommendation format with verbatim Learn citation requirement; no-SDK disclaimer (no Fabric WAF SDK or assessment REST API exists; evidence flows through existing `-cli` skills and Microsoft-cited open-source accelerators `fabric-cost-analysis` and FUAM); glossary (CU, F-SKU, FUAM, OneLake, smoothing window, autoscale, Capacity / Workspace / Fabric Admin roles); read-only boundary definition; relationship to the Azure WAF; heading-anchor citation convention (verbatim heading text, not slugified anchors).
- **`fabric-skills`, `fabric-consumption`, and `fabric-operations` plugin bundles expanded**: each of these three bundles now ships `skills/fabric-waf`, `agents/FabricWAF.agent.md`, and `common/FABRIC-WAF-CORE.md`. The `fabric-authoring` and `powerbi-authoring` bundles intentionally do not ship WAF (it is guidance / consumption-style, not authoring). Reinstall via `/plugin install fabric-skills@fabric-collection` (or the equivalent for `fabric-consumption` / `fabric-operations`) to pick up the new skill and agent.
- **2 new prompt examples**: `prompt_examples/WAFAssessment.txt` (e2e mode trigger with PBIP export) and `prompt_examples/WAFPillarReview.txt` (single-pillar mode trigger).
- **`skills/fabric-waf/references/scorecard-schema.md`**: defines `scorecard.json`, a machine-readable per-run snapshot that is the single contract for the re-assessment lifecycle (baseline, improve, re-run, compare over time). Introduces **stable recommendation IDs** (a deterministic `stable_key` so a recommendation keeps its ID across runs), a `WAFAssessmentHistory.md` / `history.csv` multi-run trend index, **Status / Risk-Acceptance carry-forward** on re-assessment, and a **methodology-drift flag** (so a changed principle set from evolving Learn pages is not misread as a score regression). Its shape mirrors the PBIP star schema. `assessment-report-template.md` (folder structure), `assessment-workflow.md` (Phase 5 stable-ID assignment, Phase 6 emission, and a deterministic `scorecard.json`-based diff), `common/FABRIC-WAF-CORE.md` (recommendation format), and `export-pbip.md` (loads the `scorecard.json` series) are updated to produce and consume it.
- **`skills/fabric-waf/references/trend-storage.md`**: documents two opt-in ways to scale the trend beyond local files, both outside the read-only assessment boundary (explicit confirmation + redaction, like Phase 7 publish). **Tier 2**: persist scorecards to a Fabric **Warehouse** (star-schema DDL, T-SQL `MERGE` upsert for status carry-forward, Direct Lake + Power BI), delegated to `sqldw-authoring-cli`. **Tier 3**: a **Rayfin** hosted portal option over the Tier 2 store, with preview / `@authenticated` / resource-provisioning caveats (documented, not built).
- **`skills/fabric-waf/references/cicd-best-practices.md`**: a co-primary Operational Excellence source (with spillover into Security and Reliability) built from the [Fabric CI/CD concepts and best practices](https://learn.microsoft.com/en-us/fabric/fundamentals/understand-best-practices-fabric-cicd) Microsoft Learn guidance. Maps the Fabric ALM best-practice checklist to assessable WAF criteria (Git integration and integration-branch policy, variable libraries + value sets + connection/item reference variables, deployment pipelines vs Git synchronization vs `fabric-cicd`, Terraform infrastructure as code with encrypted state, service-principal-only automation, auto-binding and post-sync/post-deploy scripts), with a per-item-type workload coverage matrix, release-option tradeoffs, and a CI/CD evidence checklist. The `operational-excellence.md`, `security.md`, and `reliability.md` pillar references, the consolidated `evidence-checklist.md`, the `assessment-workflow.md` Phase 3 routing, and the `assessment-report-template.md` version stamp are updated to cite and gather against it.

### Changed

- **`skills/fabric-waf/references/assets/gen_report_header.py`**: aligned the HTML report's WAF index with `scorecard.json`. The generator now divides by **all** principles (including `Not assessed`), matching the `scorecard.json` `waf_index` denominator, so the HTML header, README, and scorecard no longer disagree when any principle is Not assessed. Added a `--scorecard <path>` option so the header is generated directly from `scorecard.json` (META + per-pillar counts), and the pillar cards now show the Not-assessed count. `report.css` gains a `.na` style; `export-formats.md` documents the `--scorecard` path and the denominator. (Consistency bug found by a live e2e assessment run.)
- **`.gitignore` also excludes `/WAFAssessmentHistory.md` and `/history.csv`**: WAF trend-index files are per-run artifacts that live beside the report folders and must not be committed to the skills repo.
- **`skills/fabric-waf/references/export-pbip.md`**: aligned the optional PBIP export with the newly published Power BI agentic authoring skills. Adds a local, read-only Power BI Desktop Bridge validation loop (`validate-report` plus open / reload / screenshot), the PBIR-only format rule (PBIR-Legacy unsupported; never hand-author PBIR JSON, always route through `powerbi-report-authoring`), modern visual types (`cardVisual` / `pivotTable` instead of the deprecating `card` / `matrix` / Q&A / maps), a Phase 7 semantic-model binding-verification plus long-running-operation note, and links to the Microsoft Learn overviews for the authoring, design, planner/management skills and the Desktop Bridge.
- **`.gitignore` excludes `WAFAssessmentReport-*/` and `WAFAssessmentReport/`**: assessment report folders may contain PII (UPNs, capacity / workspace GUIDs, item names that reveal customer/product confidentiality, raw evidence rows) and must not be committed by default.

## [0.3.6] - 2026-07-02

### Added
- **`skills/dataflows-authoring-cli`** -- preview-and-confirm step in the dataflow creation flow: the agent previews each entity via `executeQuery` and renders ASCII line/bar charts (`references/charts/line_chart.py`, `references/charts/bar_chart.py`) so the user can validate output before the first refresh.

### Changed
- **Eventstream skills enhanced** (`eventstream-authoring-cli`, `eventstream-consumption-cli`; both shipped in v0.3.5) -- SKILL.md, core-reference, and API-endpoint refinements detailed below.
- **`eventstream-consumption-cli` — Custom Endpoint connection string retrieval recipe.** New "Get Custom Endpoint Connection String" section with full `az rest` CLI recipes (bash + PowerShell) showing the 2-step Topology API workflow: get topology → get source connection. Includes security guidance, multi-source disambiguation, Kafka producer config table, and MUST DO rule.
- **`EVENTSTREAM-AUTHORING-CORE.md` — Eventhouse ingestion modes guidance.** Added ProcessedIngestion as recommended API-automatable path with full example, DirectIngestion warning documenting the known UI-only data connection limitation, cross-skill collaboration pattern table, and CDC bracket-escaping fix.
- **Corrected Eventstream Definition API endpoints** -- All SKILL.md code blocks and eval Layer 1 regex assertions updated from unsupported `GET .../definition` / `PUT .../definition` to the official `POST .../getDefinition` / `POST .../updateDefinition` per Microsoft Learn docs.
- **`skills/search-consumption-cli`** -- reworked the skill description and triggers to lead with catalog-search framing ("search for an item", "search the catalog", "catalog search") and dropped discovery-verb-only triggers that did not reliably route to it. The skill now activates for cross-tenant "search the catalog for an item" requests, which is its actual purpose (the Fabric Catalog Search API). Reconciled the troubleshooting note on indexing lag (variable, not yet near-real-time; not a fixed ~24h).

### Fixed
- **`skills/dataflows-consumption-cli`** -- chart reference examples are now runnable as-written: bar-chart example passes the required `--labels`, `jq group_by` is preceded by `sort_by`, and the bar/pie renderers cast labels to `str` to avoid `TypeError` on numeric JSON categories.

## [0.3.5] - 2026-06-25

### Added
- **New skills `fabriciq-ontology-authoring-cli` and `fabriciq-ontology-consumption-cli`** — Fabric IQ Ontology (preview) support from the CLI. `fabriciq-ontology-authoring-cli` creates and evolves Ontology items (entity types, properties incl. timeseries, relationship types, and bindings to OneLake lakehouse or Eventhouse / KQL tables) via the Fabric item-definition REST API with a mandatory Preview & Confirm gate before any LRO write. `fabriciq-ontology-consumption-cli` reads Ontology items to produce agent grounding context and routes ontology-backed data queries by binding type to the matching per-datasource consumption skill (`eventhouse-consumption-cli`, `spark-consumption-cli`, `sqldw-consumption-cli`). Adds per-skill `references/` (including a shared ontology schema reference bundled into each skill), routing tests and full-eval plans.
- **New skill: `mlv-operations-cli`** -- Manage Materialized Lake View (MLV) refresh schedules and job execution via Fabric REST APIs. Provides scheduling and monitoring operations (9 endpoints):
  - **Schedule Management**: Create/list/update/delete refresh schedules (Cron, Daily, Weekly, Monthly)
  - **Job Execution**: Trigger on-demand refreshes, monitor job status/history, cancel running jobs
  - **UX Patterns**: Human-in-the-loop confirmations, step-by-step planning, iterative error handling
  - **Gap Documentation**: Transparently documents MLV discovery limitations — user must provide lakehouse ID and table names manually
- **Cross-skill integration** -- Routing from spark-authoring-cli, spark-operations-cli, FabricDataEngineer agent delegation
- **Competitive advantage** -- Fabric is first platform to offer conversational MLV scheduling (Databricks Lakeflow has no equivalent)

## [0.3.4] - 2026-06-18

### Added
- **Materialized Lake View (MLV) resources for `spark-authoring-cli`** -- two new resource documents:
  - `resources/materialized-lake-view-patterns.md` -- MLV design guidance, layering patterns, when to use MLVs vs. plain Delta tables, and the SQL-vs-PySpark authoring tradeoff (PySpark MLVs are lineage-schedule-refresh only and don't support on-demand notebook refresh).
  - `resources/mlv-incremental-refresh-patterns.md` -- refresh-readiness review workflow, IR-friendly syntax guide, full-refresh blocker catalog, and safe non-breaking rewrites.
- **MLV triggers + routing in `spark-authoring-cli/SKILL.md`** -- discovery phrases (`materialized lake view`, `MLV`, `CREATE MATERIALIZED LAKE VIEW`, `MLV incremental refresh`, `review MLV for incremental refresh`, `MLV refresh policy`, `schedule MLV refresh`), resource table entries, Rule 4 MLV routing, and a quick-start SQL example.
- **Cross-link from `e2e-medallion-architecture` PREFER section** -- points Silver/Gold layer authoring at the new MLV resources.
- **M language semantics reference for `dataflows-authoring-cli`** — new `references/m-language.md` covering language-side pitfalls confirmed live against a Fabric Dataflow Gen2 via `executeQuery`: `try` success vs failure record shapes (`[HasError, Value]` vs `[HasError, Error[Reason, Message, Detail]]`), `try ... otherwise` short-circuit semantics, per-cell error wrapping in `Table.TransformColumnTypes` and `Table.TransformColumns` (errors stored at the cell level — Arrow renders them as `null` but reads raise), `each` scoping divergence between row contexts (`Table.SelectRows`: `_` is a row record) and sub-table contexts (`Table.Group`: `_` is the sub-table — use `_[Col]` for the column-as-list), optional field access (`r[key]?`, `Record.FieldOrDefault`), quoted-identifier escaping (`#"..."`), error-record construction, and sandbox-disabled symbols. SKILL.md References table updated.
- **Source connector patterns for `dataflows-authoring-cli`** — new `references/connectors.md` covering the M-side source connector surface: live-verified function inventory (`Lakehouse.Contents`, `Sql.Database`, `Fabric.Warehouse`, `OData.Feed`, `Web.Contents`, `PowerPlatform.Dataflows`, `Snowflake.Databases`, `AzureStorage.DataLake`, `Excel.Workbook`, `Variable.Value`, `Html.Table`, `Csv.Document`, `Json.Document`, `Lines.FromBinary`), verified Lakehouse deep navigation (`workspaceId` → `lakehouseId` → flat-table `Name` index), `PowerPlatform.Dataflows` workspace/dataflow navigation (`{[Id="Workspaces"]}[Data]` → `workspaceId` → `dataflowName`), runtime-disabled functions (`Web.Page`, `Web.BrowserContents`), credentialed-connector argument shapes, the in-band `{"Error":"..."}` decoding contract for `executeQuery` Arrow responses, and the `[AllowCombine = true]` multi-source section attribute. Every behaviour claim was reproduced live via `executeQuery`.
- **Gemini CLI compatibility** -- new `compatibility/GEMINI.md` (a thin `@./AGENTS.md` import) is flattened to the public repo root by the release flow, so cloning the public repo enables Gemini CLI automatically.

### Changed
- **Compatibility files** (`compatibility/CLAUDE.md`, `AGENTS.md`, `.cursorrules`, `.windsurfrules`) -- added pointers to the new MLV resources so cross-tool consumers route to the same guidance.
- **`skills/dataflows-authoring-cli/SKILL.md`** — added a requirement to name the definition parts (`mashup.pq`, `queryMetadata.json`, `.platform`) in the written summary so they survive transcript truncation; condensed the connector-types note to keep the YAML description within the 1023-char limit.

### Fixed
- **Cross-tool config files** -- removed dead "see DEVELOPMENT-GUIDE.md at repository root" references (the file never existed) from `AGENTS.md`, `.cursorrules`, and `.windsurfrules`. `AGENTS.md` and `.windsurfrules` now inline the `az login` token steps the link was meant to provide, matching `CLAUDE.md`.

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
