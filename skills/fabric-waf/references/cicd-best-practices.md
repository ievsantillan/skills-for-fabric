<!-- VERIFIED: 2026-07-03 against https://learn.microsoft.com/en-us/fabric/fundamentals/understand-best-practices-fabric-cicd -->

# Fabric CI/CD Best Practices: WAF Reference

## Source

Microsoft Learn: [Fabric CI/CD concepts and best practices](https://learn.microsoft.com/en-us/fabric/fundamentals/understand-best-practices-fabric-cicd)

> This is a **co-primary source** for the Operational Excellence pillar and a supporting source for Security and Reliability. It is a Fabric *fundamentals* page (not a WAF pillar page), so it complements, rather than replaces, the verbatim WAF principles in `operational-excellence.md`. Re-fetch this page when authoring or updating this reference and bump the VERIFIED stamp above.

## Why this reference exists

The WAF Operational Excellence pillar page treats "Deploy changes safely" and "Automate operations" at a principle level. This Fabric CI/CD guidance is more prescriptive: it names the specific platform capabilities (Git integration, variable libraries, deployment pipelines, `fabric-cicd`, Terraform) and the concrete practices an assessment can score against. Use this reference to turn the OpEx deployment/automation principles into checkable evidence.

---

## Pillar mapping

| CI/CD topic | Primary WAF pillar | Also touches |
|---|---|---|
| Git integration + single source of truth | Operational Excellence | Reliability (versioned rollback source) |
| Environments (dev/test/prod) + capacity isolation | Operational Excellence | Reliability, Cost Optimization |
| Variable libraries + value sets + reference variables | Operational Excellence | Security (no hardcoded connection settings) |
| Feature/branched workspaces + integration-branch policy | Operational Excellence | Security (PR review gate) |
| Deployment pipelines / Git sync / API-driven release | Operational Excellence | Reliability |
| `fabric-cicd` code-first deployment | Operational Excellence | |
| Terraform infrastructure as code | Operational Excellence | Security (encrypted state, managed credentials) |
| Service-principal-only automation + no committed secrets | Security | Operational Excellence |
| No one-click rollback: redeploy from Git | Reliability | Operational Excellence |

---

## Workload coverage matrix

CI/CD capability maturity varies by workspace item type. The Learn page is explicit that "some item types are more mature than others with respect to their CI/CD capabilities."

| Workload | Coverage | Notes (from Learn page) |
|---|---|---|
| Lakehouse | Yes | Item definitions in Git; schema changes via a notebook with table-management logic |
| Warehouse | Partial | Schema changes managed with SqlPackage and the Data-tier Application Framework, not variable libraries |
| Real-Time Intelligence (Eventstream / Eventhouse / Activator) | Partial | Git and API support varies by item type; preview items may not yet support service-principal calls |
| Data Factory (Pipelines / Dataflows Gen2) | Yes | Read variables from a variable library; connection reference variables parameterize data sources |
| Data Science (notebooks) | Yes | Auto-binding via `notebook-settings.json` (added March 2026); read variables via `notebookutils.variableLibrary.get` |
| Power BI (semantic models / reports) | Yes | Best fit for low-code deployment pipelines; connect the first workspace to Git for versioning |
| OneLake | Partial | Backs lakehouse item definitions; not a separately deployed item type |
| Variable library (item type) | Yes | Stores variables + value sets; active value set is a workspace-level setting, not part of the definition |

> Confirm the current per-item-type support against [Git integration supported items](https://learn.microsoft.com/en-us/fabric/cicd/git-integration/intro-to-git-integration) and [deployment-pipeline supported items](https://learn.microsoft.com/en-us/fabric/cicd/deployment-pipelines/intro-to-deployment-pipelines) before scoring an item type as a Gap. A missing capability may reflect preview status, not a customer misconfiguration.

---

## Best practices (Microsoft Learn checklist, verbatim headings)

Each subsection mirrors a heading from the Learn "What are Fabric CI/CD best practices?" checklist. Evidence items are what the assessment collects to score the practice.

### Fabric CI/CD project planning

Plan project environments (for example dev, test, prod). Plan the tenant-level Fabric items each environment needs (workspaces, connections, gateways) and the Azure resources each needs (Fabric capacity, Storage account). Select a Git provider (Azure DevOps, GitHub, or GitHub Enterprise) and a branching strategy (GitFlow or trunk-based development).

**Evidence**: environment inventory (dev/test/prod workspaces + capacities); Git provider in use; documented branching strategy; per-environment resource map.

### Security best practices

Use service principal authentication for all DevOps and CI/CD automation, not user principals. Never commit files with sensitive credentials to Git.

**Evidence**: automation identity type (service principal vs user); secret-scan results across item definitions and workflow files; where deployment credentials are stored (Key Vault / pipeline secrets, not Git).

### Fabric CI/CD project setup (infrastructure as code)

Prefer Terraform to provision each environment's workspaces, a separate capacity per environment, and supporting Azure resources (Storage account, Key Vault), plus permissions for Entra users, groups, and service principals, and all required connections. Let Terraform manage connection credentials (for example SAS tokens) so secrets stay encrypted. For production, store the Terraform state file in protected cloud storage in an encrypted format. If not using Terraform, write repeatable setup scripts with the Fabric CLI, Semantic Link Labs, or Fabric REST APIs.

**Evidence**: IaC repository (Terraform or scripted); separate capacity per environment; Terraform state storage location + encryption; connection-credential management approach.

### Parameterization for environment-specific settings

Identify items that carry environment-specific values (data-source paths, connection IDs). Create a variable library and add variables to parameterize those settings; update items to read variable values at run time instead of hardcoding. Use connection reference variables to parameterize external data-source connections and item reference variables to manage cross-workspace item dependencies. Extend the variable library with value sets for test and production. Note: the active value set is a workspace-level setting, so identical variable-library definitions can resolve differently per environment.

**Evidence**: variable library presence + variable inventory; value sets for test/prod; connection/item reference variable usage; scan for hardcoded server/database/connection strings in notebooks, pipelines, dataflows.

### Data orchestration strategy

Implement a medallion architecture with lakehouse items for bronze/silver/gold. Build ETL with notebooks, pipelines, copy jobs, dataflows, and user-defined functions. Expose a single top-level pipeline or notebook to run end-to-end processing, and write a post-deploy script to run it after deployment. Configure ongoing refresh through `.schedules` files in item definitions. Manage lakehouse table schema changes in a notebook; manage warehouse schema changes with SqlPackage and the Data-tier Application Framework.

**Evidence**: top-level orchestration item; post-deploy script; `.schedules` files in item definitions; documented schema-change process per storage type.

### Continuous integration development process

Create the integration branch as the single source of truth by adding item definitions. Connect the dev workspace to the integration branch; use the Git folder setting to separate item definitions from other workflow files, and unique Git folder settings so multiple workspaces in one solution share a single Git branch. Configure an integration-branch policy that prohibits direct commits and requires pull requests. Use branched workspaces to create and manage feature branches and feature workspaces; keep feature branches short-lived and recycle feature workspaces. For notebooks, enable auto-binding by adding `notebook-settings.json`; for item types that lack auto-binding, write post-sync scripts to reestablish relationships.

**Evidence**: integration-branch policy (PR-required, no direct commits); Git folder settings per workspace; feature-workspace usage; `notebook-settings.json` presence for notebooks; post-sync scripts for non-auto-binding items.

### Continuous deployment release process

Store workspace IDs and Entra IDs as repository variables and service-principal credentials as repository secrets. Use `fabric-cicd` with configuration-based deployment to build a code-first release process, matching `fabric-cicd` environment names to value-set names for auto-activation, and use its parameterization to update environment-specific settings during deployment. Prefer pull requests to configure manual-approval gates; when using trunk-based development, use repository environments to configure approvals instead.

**Evidence**: release mechanism (deployment pipeline / Git sync / `fabric-cicd` / custom API); manual-approval gate configuration; `fabric-cicd` config + parameterization; how deployment secrets are supplied to the workflow.

---

## Release process option tradeoffs (from Learn)

| Option | Best fit | Main tradeoff |
|---|---|---|
| Deployment pipeline | Low-code promotion across staged workspaces; small-to-medium projects, especially semantic models + reports | Lower setup effort, but less automation flexibility; all workspaces must be in one Entra tenant; weaker approval controls; not suited to workspaces with hundreds of items |
| Git synchronization | Branch-based releases where target workspaces stay connected to Git | Familiar Git flow, but needs post-sync jobs to fix environment-specific settings; target workspace shows Git status indicators |
| API-driven (`fabric-cicd` or custom) | Scalable releases with custom branching, parameterization, or many target workspaces (including ISV multi-tenant) | Most flexible, but requires tooling and code |

> **Rollback (Reliability spillover)**: Fabric has no one-click rollback. The safety net is redeploying an earlier item version from Git or a deployment pipeline. Data consistency is the real rollback risk: multiple data stores may require careful reconciliation, not just reverting code.

---

## Evidence checklist (CI/CD, for the Operational Excellence pillar)

- [ ] Environment inventory: dev/test/prod workspaces + separate capacity each: source: `[FabricAdmin]`
- [ ] Git provider + integration-branch policy (PR-required, no direct commits): source: `[FabricAdmin]` + repo settings
- [ ] Branching strategy documented (GitFlow or trunk-based): source: `[user-interview]`
- [ ] Service-principal-only automation (no user principals): source: `[user-interview]` + repo/pipeline config
- [ ] No secrets committed to Git (secret-scan clean): source: source-control scan, `[spark-operations-cli]`, `[dataflows-consumption-cli]`
- [ ] Variable library + value sets for environment parameterization: source: `[FabricAdmin]`
- [ ] Connection/item reference variables in ETL items: source: `[FabricAdmin]`, `[dataflows-consumption-cli]`
- [ ] Hardcoded connection settings scan (should be none): source: `[spark-operations-cli]`, `[dataflows-consumption-cli]`
- [ ] IaC (Terraform or scripts) for capacities/workspaces + encrypted state: source: `[user-interview]`
- [ ] Release mechanism (deployment pipeline / Git sync / `fabric-cicd`): source: `[FabricAdmin]` + `[user-interview]`
- [ ] Manual-approval gates for prod deployment: source: `[FabricAdmin]` + repo settings
- [ ] Auto-binding config (`notebook-settings.json`) / post-sync scripts: source: `[user-interview]`, `[spark-operations-cli]`
- [ ] Post-deploy orchestration script + `.schedules` in item definitions: source: `[user-interview]`

---

## Cross-pillar tradeoffs

- **OpEx <-> Cost**: Separate capacity per environment and IaC + parameterization raise up-front cost and setup effort; the payoff is safe, repeatable promotion and fewer prod incidents.
- **OpEx <-> Security**: PR-required integration-branch policies and manual-approval gates add deploy friction but are the control that keeps unreviewed changes and secrets out of prod.
- **OpEx <-> Reliability**: `fabric-cicd` parameterization avoids the post-sync fix-up that plain Git synchronization needs, reducing a class of environment-drift failures; but any automation is itself a failure surface to monitor.

---

## See also

- `common/FABRIC-WAF-CORE.md`
- `references/operational-excellence.md` (co-primary pillar page: "Deploy changes safely", "Automate operations")
- `references/security.md` (Secure Development Lifecycle, Secret management)
- `references/reliability.md` (Plan for disaster recovery, redeploy-from-Git rollback)
- `references/tradeoffs.md`
- Variable libraries: https://learn.microsoft.com/en-us/fabric/cicd/variable-library/variable-library-overview
- `fabric-cicd` library docs: https://microsoft.github.io/fabric-cicd/latest/
- `fabric-cicd` + Azure DevOps tutorial: https://learn.microsoft.com/en-us/fabric/cicd/tutorial-fabric-cicd-azure-devops
- Delegate skills: `dataflows-consumption-cli`, `spark-operations-cli`, `search-consumption-cli`
