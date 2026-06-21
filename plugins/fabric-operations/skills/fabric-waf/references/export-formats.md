# Export Formats

Markdown is the always-generated default. The formats below are additive, selected via `output.export_formats` in the intake template. **The skill teaches the conversion: the user runs it.** No code is shipped or executed by the skill itself.

## Prerequisites by format (install only what you select)

Markdown needs nothing. Each additional format has its own dependencies; install only those for the formats you requested in the intake. Run the pre-export check below and fail fast with the install hint if a tool is missing.

| Format | Requires | Install | System dependency? |
|---|---|---|---|
| Markdown | (none) | n/a | no |
| CSV | `pandas` | `pip install pandas` | no |
| Excel | `pandas`, `openpyxl` | `pip install pandas openpyxl` | no |
| Word | `python-docx` | `pip install python-docx` | no (pandoc-free path) |
| HTML | `pandoc` | `winget install JohnMacFarlane.Pandoc` | no (pandoc only; no PDF engine needed) |
| PBIP | (none beyond text file writes) | n/a | no |

```python
# Pre-export tool check: fail fast with the exact install hint before generating.
import importlib.util, shutil
need = {
    "csv":   [("pandas", "pip install pandas")],
    "excel": [("pandas", "pip install pandas"), ("openpyxl", "pip install openpyxl")],
    "word":  [("docx", "pip install python-docx")],
}
selected = ["csv", "excel", "word"]  # set to output.export_formats
missing = [hint for fmt in selected for mod, hint in need.get(fmt, []) if importlib.util.find_spec(mod) is None]
if "html" in selected and not (shutil.which("pandoc") or shutil.which("pandoc.exe")):
    missing.append("winget install JohnMacFarlane.Pandoc")
assert not missing, "Missing export tooling:\n  " + "\n  ".join(sorted(set(missing)))
```

---

## Tier 1 (always documented)

### Markdown (default; no user action required)

The layered folder per `references/assessment-report-template.md` is markdown only by default. All other formats below are derived from it.

### HTML (via pandoc) — recommended branded report

A single self-contained HTML file is the recommended shareable document format: it opens in any browser, needs only pandoc (no PDF engine, no LaTeX), and carries a branded header that mirrors the Azure Well-Architected Review results UI (banner, an overall-results gauge, and per-pillar scorecard cards with the official pillar icons).

Two bundled assets drive the look (both in `references/assets/`, verified against the live Microsoft Learn WAF page 2026-06-21):

- `report.css` — theme aligned to Learn's visual tokens (accent `#0F6CBD`, text `#161616`, Segoe UI). It also fixes pandoc's default ~36em body width that otherwise clips the wide 10-column recommendations table, and styles the banner / gauge / pillar cards.
- `well-architected-hub.png` + `pillars/*.svg` — the official WAF hub image and the five pillar icons.
- `gen_report_header.py` — a small generator that emits `_report-header.html` (banner + overall gauge + pillar cards) from the assessment's Met/Partial/Gap counts.

**Step 1 — generate the themed header** (edit `META`/`PILLARS` in the script for the assessment, or import `build()`):

```powershell
$assets = "skills\fabric-waf\references\assets"
python "$assets\gen_report_header.py" --assets "$assets" --out WAFAssessmentReport-2026-06-13\_report-header.html
```

**Step 2 — build the self-contained HTML:**

```powershell
pandoc `
  WAFAssessmentReport-2026-06-13\README.md `
  WAFAssessmentReport-2026-06-13\reliability.md `
  WAFAssessmentReport-2026-06-13\security.md `
  WAFAssessmentReport-2026-06-13\cost-optimization.md `
  WAFAssessmentReport-2026-06-13\operational-excellence.md `
  WAFAssessmentReport-2026-06-13\performance-efficiency.md `
  WAFAssessmentReport-2026-06-13\recommendations.md `
  --metadata title="Fabric WAF Assessment 2026-06-13" `
  -s --toc --toc-depth=2 --embed-resources --syntax-highlighting=none `
  --css skills\fabric-waf\references\assets\report.css `
  --include-in-header skills\fabric-waf\references\assets\report-head.html `
  --include-before-body WAFAssessmentReport-2026-06-13\_report-header.html `
  -o WAFAssessmentReport-2026-06-13.html
```

`--css ...\report.css` applies the theme; `--include-in-header ...\report-head.html` adds the early light/dark theme-init script (in `<head>`, so there is no flash of the wrong theme); `--include-before-body _report-header.html` injects the banner + gauge + cards + theme toggle button; `--embed-resources` base64-inlines the CSS, banner PNG, and pillar SVGs so the single `.html` is fully portable; `-s` makes it standalone; `--toc` builds the navigation contents; **`--syntax-highlighting=none`** disables pandoc's code coloring (its dark-on-dark highlight palette is unreadable in dark mode; `report.css` styles fenced code blocks for both themes instead).

> **Verified 2026-06-21.** Produces a ~710 KB self-contained HTML (the embedded banner image and SVG icons account for the size) with the WAR-style header, all report tables fully visible (every recommendation column fits and wraps), and a navigable TOC. **Light/dark mode**: the report follows the reader's OS preference by default and has a toggle button (top-right) that overrides it and persists the choice to `localStorage`; verified in both modes by browser screenshot. No external file references, so it can be emailed or hosted as-is. The "WAF index" on the gauge/cards is a transparent maturity indicator: `(Met*1 + Partial*0.5 + Gap*0) / principles * 100`. It is NOT the Azure WAR questionnaire score and is distinct from recommendation severity.
>
> **PATH note:** after `winget install`, `pandoc` is not on `PATH` until you open a new shell. Either start a new terminal, or call it by full path (commonly `%LOCALAPPDATA%\Pandoc\pandoc.exe`).
>
> **Branding note:** the WAF hub image and pillar icons are Microsoft Learn assets, and the Azure / Microsoft Fabric logos in the banner are official Microsoft marks (Fabric logo from the `@fabric-msft/svg-icons` npm package; Azure logo from the official Microsoft Azure brand). All are used here in a Microsoft Fabric WAF assessment context. Keep them in `references/assets/` (logos under `assets/logos/`); use the official, undistorted assets and do not recolor or stretch them. Do not embed Microsoft Learn's site CSS verbatim (proprietary, won't render standalone, and changes without notice) — the bundled `report.css` re-creates the look from public design tokens.

### Excel (via openpyxl, against `recommendations.md`)

```python
# Loads recommendations.md, parses the single backlog table, writes Excel with filters.
import openpyxl
from openpyxl.utils.dataframe import dataframe_to_rows
import pandas as pd

# Parse the recommendations table (assumes it is the only markdown table in the file).
text = open(r"WAFAssessmentReport-2026-06-13\recommendations.md", encoding="utf-8").read()
# Trim to the table block; pandas read_html will handle markdown tables converted to HTML.
import markdown
html = markdown.markdown(text, extensions=["tables"])
df = pd.read_html(html)[0]

wb = openpyxl.Workbook()
ws = wb.active
ws.title = "Recommendations"
for row in dataframe_to_rows(df, index=False, header=True):
    ws.append(row)
ws.auto_filter.ref = ws.dimensions
wb.save(r"WAFAssessmentReport-2026-06-13\recommendations.xlsx")
```

### Word (via python-docx)

```python
# Convert pillar files to .docx by piping through pandoc, or build a docx manually.
import subprocess

files = [
    "README.md", "reliability.md", "security.md", "cost-optimization.md",
    "operational-excellence.md", "performance-efficiency.md", "recommendations.md",
]
base = r"WAFAssessmentReport-2026-06-13"
subprocess.run([
    "pandoc",
    *[f"{base}\\{f}" for f in files],
    "-o", f"{base}.docx",
    "--toc", "--toc-depth=2",
])
```

### CSV (original clean schema)

`recommendations.md` exports cleanly to CSV via the same pandas/markdown step:

```python
import pandas as pd, markdown
text = open(r"WAFAssessmentReport-2026-06-13\recommendations.md", encoding="utf-8").read()
df = pd.read_html(markdown.markdown(text, extensions=["tables"]))[0]
df.to_csv(r"WAFAssessmentReport-2026-06-13\recommendations.csv", index=False)
```

> This CSV uses an **original clean schema** matching the recommendation format defined in `common/FABRIC-WAF-CORE.md`. It is intentionally a single actionable backlog, not a copy of the Microsoft Well-Architected Review (WAR) online tool's export (see the comparison below).

### Relationship to the Azure WAR tool export (verified 2026-06-21)

The Microsoft Azure WAR online tool ([assessment](https://learn.microsoft.com/en-us/assessments/azure-architecture-review/)) also exports CSV. We verified an actual export; a sanitized sample is at `references/samples/war-export-sample.csv`. Key facts:

- The WAR export is a **multi-section CSV**, not a flat table. It stacks: a title row, an "Your overall results" row, a few summary links, then **two differently-shaped sections** with their own header rows:
  - **Recommendations section** header: `Category, Link-Text, Link, Priority, ReportingCategory, ReportingSubcategory, Weight, Context, CompleteY/N, Note`
  - **Answers section** header: `Category, Question, Answers, Selected Answer, Note`
- It is **Azure-wide and self-reported** (one row per WAF questionnaire answer/link), not evidence-bound to a tenant. Microsoft documents importing it into Azure DevOps via a PowerShell script ([aka.ms/waf/implementation](https://aka.ms/waf/implementation)).

Our `recommendations.csv` is a deliberately different artifact: **one row per concrete, evidence-bound remediation** with `Severity`, `Effort`, `Owner`, `Pillars`, `Status`, ready for a backlog tool. We do **not** claim parity, because the two serve different purposes (actionable Fabric remediation backlog vs Azure-wide questionnaire link list).

#### Optional WAR-compatible projection

If the user wants to merge/diff our output alongside a real WAR export, emit a second CSV that maps our rows onto the WAR **Recommendations** header. This is a lossy projection (it drops Severity/Effort/Owner/Status):

```python
import pandas as pd
df = pd.read_csv(r"WAFAssessmentReport-2026-06-13\recommendations.csv")
war = pd.DataFrame({
    "Category": df["Pillars"],
    "Link-Text": df["Recommendation"],
    "Link": df.get("learn_citation_url", ""),  # the Learn pillar URL for the principle
    "Priority": df["Severity"],
    "ReportingCategory": df["Principle"],
    "ReportingSubcategory": "",
    "Weight": "",
    "Context": df["Recommendation"],
    "CompleteY/N": df["Status"].map(lambda s: "Y" if str(s).lower() in ("done","risk accepted") else "N"),
    "Note": df.get("Evidence", ""),
})
war.to_csv(r"WAFAssessmentReport-2026-06-13\recommendations-war-compatible.csv", index=False)
```

> The projection matches the WAR **Recommendations** header verbatim so a downstream script (e.g. the Azure DevOps importer) can consume it. It does not reproduce the WAR Answers section: our assessment is evidence-driven, not questionnaire-driven.

---

## Tier 1.5 (optional, opt-in)

### PBIP project (Fabric-native living artifact)

Generates a Power BI project (semantic model + report) so pillar scores trend over time, recommendations are filterable in Power BI, and the assessment becomes a living artifact in Fabric.

Full design: star schema, DAX measures, page layouts, color palette, refresh strategy: lives in **`references/export-pbip.md`**. Enable by setting `output.export_formats: [markdown, pbip]` in the intake.

PBIP generation is **local only** (writes files to disk). Publishing the PBIP to a Fabric workspace is a separate Phase 7 step that requires explicit per-session user confirmation. See the read-only boundary in `common/FABRIC-WAF-CORE.md`.

---

## What the skill does NOT do

- Run pandoc / openpyxl / python-docx for you. The user runs them with the snippets above.
- Modify Fabric tenant state in any export format. PBIP generation writes locally; publish is opt-in and lives in Phase 7.
- Ship pre-built PBIX templates. The PBIP schema reflects the actual pillar principles surfaced by the verified Learn pages at assessment time, which can evolve.
