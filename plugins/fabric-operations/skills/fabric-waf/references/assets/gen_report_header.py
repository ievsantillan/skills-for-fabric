"""Generate the themed executive header (banner + overall-results gauge + pillar
scorecard cards) for a Fabric WAF HTML export, modeled on the Azure WAR results UI.

Reusable: edit META and PILLARS for the assessment being exported, then run. It writes
`_report-header.html` into the report folder, which the pandoc HTML command includes via
`--include-before-body`. Image/icon paths point at this skill's assets folder; pandoc
inlines them when run with `--embed-resources`.

The "WAF index" is a transparent maturity indicator derived from the categorical pillar
scores: index = (Met*1 + Partial*0.5 + Gap*0) / principles * 100. It is NOT the Azure WAR
questionnaire score, and is distinct from recommendation *severity*.
"""
import os, html, argparse, json

# --- Per-assessment inputs -------------------------------------------------
# Prefer `--scorecard <path>` to load these from the canonical scorecard.json so
# the header index always matches scorecard.json / README. The values below are a
# fallback example used only when no scorecard is supplied.
META = {
    "title": "Microsoft Fabric Well-Architected Framework Assessment",
    "workspace": "Unified Data Foundation with Fabric",
    "mode": "e2e (all 5 pillars)",
    "date": "2026-06-20",
}
# (pillar key, display name, icon file, Met, Partial, Gap, Not assessed)
PILLARS = [
    ("reliability", "Reliability", "reliability.svg", 0, 5, 4, 0),
    ("security", "Security", "security.svg", 1, 5, 4, 0),
    ("cost-optimization", "Cost Optimization", "cost-optimization.svg", 1, 5, 0, 0),
    ("performance-efficiency", "Performance Efficiency", "performance-efficiency.svg", 0, 4, 2, 0),
    ("operational-excellence", "Operational Excellence", "operational-excellence.svg", 0, 4, 2, 0),
]
_ICONS = {
    "reliability": "reliability.svg", "security": "security.svg",
    "cost-optimization": "cost-optimization.svg",
    "performance-efficiency": "performance-efficiency.svg",
    "operational-excellence": "operational-excellence.svg",
}
_NAMES = {
    "reliability": "Reliability", "security": "Security",
    "cost-optimization": "Cost Optimization",
    "performance-efficiency": "Performance Efficiency",
    "operational-excellence": "Operational Excellence",
}
# ----------------------------------------------------------------------------

def load_scorecard(path):
    """Populate META and PILLARS from a scorecard.json so the header matches it."""
    global META, PILLARS
    sc = json.load(open(path, encoding="utf-8"))
    a = sc["assessment"]
    META = {
        "title": "Microsoft Fabric Well-Architected Framework Assessment",
        "workspace": ", ".join(a["scope"].get("workspace_ids", [])) or "(scope)",
        "mode": a.get("mode", ""),
        "date": a.get("assessment_date", ""),
    }
    order = ["reliability", "security", "cost-optimization", "performance-efficiency", "operational-excellence"]
    pc = {p["pillar_key"]: p["counts"] for p in sc["pillars"]}
    PILLARS = [(k, _NAMES[k], _ICONS[k], pc[k]["met"], pc[k]["partial"], pc[k]["gap"], pc[k]["not_assessed"])
               for k in order if k in pc]

def index_of(met, partial, gap, not_assessed=0):
    # Denominator = ALL principles (including Not assessed), matching
    # scorecard.json waf_index. Keeps HTML, README, and scorecard.json consistent.
    total = met + partial + gap + not_assessed
    return 0 if total == 0 else round((met * 1.0 + partial * 0.5) / total * 100)

def band(score):
    if score < 33: return ("CRITICAL", "crit")
    if score < 67: return ("MODERATE", "mod")
    return ("EXCELLENT", "exc")

def gauge(score, mini=False):
    extra = " mini" if mini else ""
    return (f'<div class="gauge{extra}"><div class="gauge-bar">'
            f'<span class="gauge-marker" style="left:{score}%"></span></div></div>')

def build(assets_dir):
    omet = sum(p[3] for p in PILLARS); opar = sum(p[4] for p in PILLARS)
    ogap = sum(p[5] for p in PILLARS); ona = sum(p[6] for p in PILLARS)
    oidx = index_of(omet, opar, ogap, ona); olabel, ocls = band(oidx)

    cards = []
    for key, name, icon, met, par, gap, na in PILLARS:
        idx = index_of(met, par, gap, na); lbl, cls = band(idx)
        icon_path = os.path.join(assets_dir, "pillars", icon).replace("\\", "/")
        cards.append(f'''  <article class="pillar-card">
    <div class="pillar-card-head">
      <img class="pillar-icon" src="{icon_path}" alt="{name} icon" />
      <h3>{name}</h3>
    </div>
    {gauge(idx, mini=True)}
    <div class="pillar-score"><span class="badge badge-{cls}">{lbl}</span> <span class="idx">{idx}/100</span></div>
    <div class="pillar-counts"><span class="met">{met} Met</span> &middot; <span class="par">{par} Partial</span> &middot; <span class="gap">{gap} Gap</span> &middot; <span class="na">{na} Not assessed</span></div>
  </article>''')

    hub = os.path.join(assets_dir, "well-architected-hub.png").replace("\\", "/")
    azure_logo = os.path.join(assets_dir, "logos", "azure.svg").replace("\\", "/")
    fabric_logo = os.path.join(assets_dir, "logos", "fabric.svg").replace("\\", "/")
    return f'''<button class="theme-toggle" type="button" onclick="wafToggleTheme()" aria-label="Toggle light or dark theme" title="Toggle light/dark">
  <span class="icon-light">&#9788; Light</span><span class="icon-dark">&#9790; Dark</span>
</button>
<div class="report-banner">
  <img class="banner-img" src="{hub}" alt="Microsoft Azure Well-Architected Framework" />
  <div class="report-banner-caption">{html.escape(META["title"])}</div>
  <div class="report-logos">
    <span class="logo-item"><img class="logo" src="{azure_logo}" alt="Microsoft Azure" /> Azure Well-Architected Framework</span>
    <span class="logo-sep">assessing</span>
    <span class="logo-item"><img class="logo" src="{fabric_logo}" alt="Microsoft Fabric" /> Microsoft Fabric</span>
  </div>
  <div class="report-meta">Workspace: <strong>{html.escape(META["workspace"])}</strong> &nbsp;&bull;&nbsp; Mode: {html.escape(META["mode"])} &nbsp;&bull;&nbsp; {html.escape(META["date"])}</div>
</div>

<section class="exec-results">
  <div class="overall-card">
    <h2 class="exec-title">Your overall results</h2>
    <div class="overall-row">
      <span class="badge badge-{ocls} badge-lg">{olabel}</span>
      <div class="overall-gauge">
        {gauge(oidx)}
        <div class="gauge-scale"><span>CRITICAL 0-33</span><span>MODERATE 33-67</span><span>EXCELLENT 67-100</span></div>
      </div>
      <div class="overall-num"><span class="big">{oidx}</span><span class="den">/100</span><div class="counts-line">{omet} Met &middot; {opar} Partial &middot; {ogap} Gap &middot; {ona} Not assessed</div></div>
    </div>
    <p class="index-note">Derived WAF index = (Met&times;1 + Partial&times;0.5 + Gap&times;0) &divide; all principles (including Not assessed) &times; 100, matching scorecard.json. This is our own maturity indicator from the categorical pillar scores; it is <em>not</em> the Azure WAR questionnaire score and is distinct from recommendation <em>severity</em>.</p>
  </div>

  <h2 class="exec-title">Pillars</h2>
  <div class="pillar-grid">
{chr(10).join(cards)}
  </div>
</section>
'''

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--assets", required=True, help="path to skills/fabric-waf/references/assets")
    ap.add_argument("--out", default="_report-header.html", help="output header HTML path")
    ap.add_argument("--scorecard", help="path to scorecard.json (loads META + pillar counts so the header matches it)")
    a = ap.parse_args()
    if a.scorecard:
        load_scorecard(a.scorecard)
    open(a.out, "w", encoding="utf-8").write(build(a.assets))
    print("wrote", a.out)
