# Export Formats

Markdown is the always-generated default. The formats below are additive, selected via `output.export_formats` in the intake template. **The skill teaches the conversion: the user runs it.** No code is shipped or executed by the skill itself.

---

## Tier 1 (always documented)

### Markdown (default; no user action required)

The layered folder per `references/assessment-report-template.md` is markdown only by default. All other formats below are derived from it.

### PDF (via pandoc)

```powershell
# Combined PDF of executive summary + all pillar files + recommendations.
pandoc `
  WAFAssessmentReport-2026-06-13\README.md `
  WAFAssessmentReport-2026-06-13\reliability.md `
  WAFAssessmentReport-2026-06-13\security.md `
  WAFAssessmentReport-2026-06-13\cost-optimization.md `
  WAFAssessmentReport-2026-06-13\operational-excellence.md `
  WAFAssessmentReport-2026-06-13\performance-efficiency.md `
  WAFAssessmentReport-2026-06-13\recommendations.md `
  --metadata title="Fabric WAF Assessment 2026-06-13" `
  --toc --toc-depth=2 `
  -o WAFAssessmentReport-2026-06-13.pdf
```

Requires pandoc + a LaTeX engine (e.g., MiKTeX or wkhtmltopdf via `--pdf-engine=wkhtmltopdf`).

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

> This CSV uses an **original clean schema** matching the recommendation format defined in `common/FABRIC-WAF-CORE.md`. We do not claim it mirrors the Microsoft Well-Architected Review online tool's export: that tool's export format was not verified at planning time.

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
