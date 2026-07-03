# Example Assessment (concrete runnable queries)

A worked snippet of a Fabric WAF assessment focused on the **evidence-gathering layer**. The queries below are real and runnable against the live Fabric platform when the executing identity has the permissions listed in `references/assessment-workflow.md` Phase 2.

> Verify each query against the actual table schema before relying on it in your environment: Capacity Metrics App and audit log table names evolve. Treat this file as a starting point, not a fixed contract.

---

## Capacity Metrics App: query via DAX (verified 2026-06-21)

The Fabric Capacity Metrics App is a **Power BI semantic model**, not a KQL database. Query it
with **DAX through the Power BI `executeQueries` REST API**. (The KQL snippets further below are
illustrative only and were not verified against a live model; prefer this DAX path.)

```powershell
# 1) Find the model: list items in the "Microsoft Fabric Capacity Metrics" workspace,
#    filter type == SemanticModel, take its id.
# 2) Query it (token audience: https://analysis.windows.net/powerbi/api):
$ds = "<capacity-metrics-semantic-model-id>"
$pt = az account get-access-token --resource "https://analysis.windows.net/powerbi/api" --query accessToken -o tsv
$H  = @{ Authorization = "Bearer $pt"; "Content-Type" = "application/json" }
function DAX($q) {
  $body = @{ queries = @(@{ query = $q }) } | ConvertTo-Json -Depth 6
  (Invoke-RestMethod -Method POST -Headers $H -Body $body `
    -Uri "https://api.powerbi.com/v1.0/myorg/datasets/$ds/executeQueries").results[0].tables[0].rows
}

DAX 'EVALUATE INFO.VIEW.TABLES()'                # schema discovery (~105 tables)
DAX 'EVALUATE Capacities'                        # SKU + state per capacity (import table)
DAX "EVALUATE FILTER('Items Throttled', 'Items Throttled'[Capacity Id]=""<CAP-GUID-UPPER>"")"
```

Verified facts:
- Import-mode tables (`Capacities`, `Items Throttled`) query reliably. **DirectQuery** detail
  tables (`Metrics By Item And Day`, `Usage Summary (Last 14 days)`, `Surge Protection By Day`)
  return `Error obtaining data location` when the capacity is **paused**, so live CU% needs the
  capacity resumed and the model refreshed.
- `Capacity Id` in `Items Throttled` is UPPERCASE.
- The Metrics App is itself a periodically-refreshed model: its SKU/state can lag the live
  capacity (we observed F16 in the model vs F64 live). Cross-check SKU against `GET /v1/capacities`
  and stamp the model's data recency.

---

## Capacity Metrics App: top-consuming items (KQL, illustrative only, unverified)

> The KQL blocks in this section are illustrative pseudo-queries and were **not** verified against a live model. The Metrics App is a Power BI semantic model: prefer the verified DAX recipe above. These remain as a conceptual reference for the kind of data available.

```kusto
MetricsByItemAndOperationAndDay
| where Timestamp > ago(24h)
| where CapacityId == "<capacity-guid>"
| summarize TotalCU = sum(CU)
    by ItemName, ItemKind, OperationName, WorkspaceId
| top 25 by TotalCU desc
```

## Capacity Metrics App: throttling events (KQL)

```kusto
ThrottlingByCapacityAndDay
| where Timestamp > ago(14d)
| where CapacityId == "<capacity-guid>"
| summarize ThrottlingMinutes = sum(ThrottlingPercentage * 1.44)
    by bin(Timestamp, 1d)
| order by Timestamp asc
```

> Schema names like `MetricsByItemAndOperationAndDay` and `ThrottlingByCapacityAndDay` are illustrative of the Capacity Metrics App semantic model and may not match your version. Inspect the model in your tenant first via `semantic-model-consumption`.

## Capacity Metrics App: average CU utilization (sizing input)

```kusto
MetricsByCapacityAndDay
| where Timestamp > ago(14d)
| where CapacityId == "<capacity-guid>"
| summarize p50 = percentile(SmoothedCUPercentage, 50),
            p95 = percentile(SmoothedCUPercentage, 95),
            p99 = percentile(SmoothedCUPercentage, 99)
```

A capacity with p95 well below 50% is a right-sizing candidate (Cost Optimization, "Identify key cost drivers").

---

## M365 audit log: Admin-role grants in last 30 days (KQL)

Run in Microsoft Purview audit search or, when piped to a SIEM, against the equivalent table (e.g., `AuditLogs` in Microsoft Sentinel).

```kusto
AuditLogs
| where TimeGenerated > ago(30d)
| where Category == "RoleManagement"
| where ActivityDisplayName contains "Add member to role"
| extend RoleName = tostring(parse_json(TargetResources)[0].displayName)
| where RoleName has_any ("Fabric Administrator", "Power BI Service Administrator", "Capacity Administrator")
| project TimeGenerated,
          Initiator = InitiatedBy.user.userPrincipalName,
          RoleName,
          AddedPrincipal = tostring(parse_json(TargetResources)[0].userPrincipalName),
          IPAddress = tostring(InitiatedBy.user.ipAddress)
| order by TimeGenerated desc
```

Maps to Security pillar "Use identity as the foundation for Zero Trust security controls": surface unexpected elevations.

## M365 audit log: workspace lifecycle events (KQL)

```kusto
AuditLogs
| where TimeGenerated > ago(30d)
| where LoggedByService == "Microsoft Fabric"
| where Operation in ("CreateFolder", "DeleteFolder", "CreateGroup", "DeleteGroup")
| project TimeGenerated,
          UserPrincipalName = User,
          Operation,
          WorkspaceName = tostring(parse_json(AuditData).WorkspaceName),
          WorkspaceId = tostring(parse_json(AuditData).WorkspaceId)
| order by TimeGenerated desc
```

Maps to Operational Excellence "Monitor your environment": workspace sprawl indicator.

---

## Warehouse SQL endpoint: workspace inventory (T-SQL)

Run via `sqldw-consumption-cli` against the Lakehouse SQL endpoint or Warehouse, when an inventory table is materialized there (e.g., from FUAM). Without that, use the Fabric REST API call below.

```sql
SELECT
    workspace_id,
    workspace_name,
    capacity_id,
    capacity_sku,
    item_count,
    storage_gb,
    last_active_date
FROM dbo.workspace_inventory
WHERE active = 1
ORDER BY storage_gb DESC;
```

## Warehouse SQL endpoint: slow query review (T-SQL)

```sql
SELECT TOP 25
    qs.request_id,
    qs.start_time,
    qs.end_time,
    DATEDIFF(SECOND, qs.start_time, qs.end_time) AS duration_seconds,
    LEFT(qs.command, 250) AS sample_command
FROM sys.dm_exec_requests_history qs
WHERE qs.start_time > DATEADD(DAY, -7, SYSUTCDATETIME())
ORDER BY duration_seconds DESC;
```

> `sys.dm_exec_requests_history` is illustrative: Warehouse exposes Query Insights via a curated set of system views; verify the available DMV/view names in your tenant via `sqldw-operations-cli`.

---

## Fabric REST API: workspaces with role assignments

```http
POST https://api.fabric.microsoft.com/v1.0/myorg/admin/workspaces/getInfo?lineage=true&datasourceDetails=true&getArtifactUsers=true
Authorization: Bearer <token>
Content-Type: application/json

{
  "workspaces": ["<workspace-guid-1>", "<workspace-guid-2>"]
}
```

Returns workspace metadata + role assignments + lineage + data source list for the listed workspaces. Use `az rest` per `common/COMMON-CLI.md` to invoke.

---

## How these pieces compose into an assessment row

Combining the queries above produces concrete evidence for several principles. Example backlog entry:

| ID | Severity | Effort | Owner | Pillars | Principle | Recommendation | Fabric features | Status | Evidence |
|---|---|---|---|---|---|---|---|---|---|
| R001 | High | M | Capacity Admin | [cost-optimization, performance-efficiency] | "Identify key cost drivers" / "Plan capacity intentionally" | Right-size capacity X from F64 to F32 based on 14-day p95 SmoothedCUPercentage of 38%. | Capacity Metrics App; F-SKU management | Open | `evidence/capacity-metrics/p95-cu-cap-X.csv` (output of the average-CU KQL above) |
| R002 | Critical | S | Fabric Admin | [security] | "Use identity as the foundation for Zero Trust security controls" | Investigate 3 Fabric Administrator role grants on 2026-05-22 not associated with a tracked change request. | PIM; M365 audit log | Open | `evidence/audit-log/role-grants-2026-05-22.csv` |
| R003 | Medium | S | Capacity Admin | [cost-optimization] | "Optimize environment costs" | Configure a scheduled pause for `dev-shared-capacity` outside working hours; current utilization shows zero activity 18:00–07:00 UTC. | Capacity pause/resume via REST | Open | `evidence/capacity-metrics/dev-shared-utilization.csv` |

This pattern (run query → save output as evidence file → score principle → write recommendation row) is the core loop of the assessment.
