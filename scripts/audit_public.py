#!/usr/bin/env python3
"""Fail-closed allowlisted public build gate for an institutional static research site."""
from pathlib import Path
from html.parser import HTMLParser
import json
import re
import sys
sys.dont_write_bytecode = True
from private_disclosure import configured_terms, contains_private_term

ROOT = Path(__file__).resolve().parents[1]
RELEASE = {"privacidad-icsa.html", "index.html", "trabajo.html", "src/private-notebook.mjs", "src/private-workbench.mjs", "src/country-comparison.mjs", "src/country-comparison-view.mjs", "src/main-country-tree.mjs", "styles.css", "favicon.svg", "logo.svg", "src/site.mjs", "src/visuals.mjs", "src/neural.mjs", "src/markov-svg.mjs", "src/lab-renderers.mjs", "src/metrics.mjs", "src/research.mjs", "src/project-catalog.mjs", "src/project-portfolio.mjs", "data/demo.json", "data/research.json", "data/projects.json"}
REPOSITORY = RELEASE | {"scripts/private_disclosure.py", "scripts/test_private_disclosure.py", "README.md", "scripts/audit_public.py", "scripts/build_official_countries.py", "scripts/test_build_official_countries.py", "scripts/inspect_ucdp_archives.py", "scripts/test_inspect_ucdp_archives.py", "scripts/run_legacy_vintage_holdout.py", "scripts/test_run_legacy_vintage_holdout.py", "scripts/experiment_recency_onset.py", "scripts/test_experiment_recency_onset.py", "tests/metrics.test.mjs", "tests/research.test.mjs", "tests/temporal-validation.test.mjs", "src/temporal-validation.mjs", "tests/visuals.test.mjs", "tests/lab-renderers.test.mjs", "tests/project-catalog.test.mjs", "tests/project-portfolio.test.mjs", "tests/public-science-boundary.test.mjs", "tests/private-notebook.test.mjs", "tests/country-comparison.test.mjs", ".github/workflows/pages.yml"}
issues = []
# Historical research cells must never be admitted to a public release.
BLOCKED = {"data/scientific-workbook.json", "src/scientific-archive.mjs"}
try:
    private_terms = configured_terms()
except ValueError as error:
    issues.append(str(error))
    private_terms = ()
files = {str(p.relative_to(ROOT)) for p in ROOT.rglob("*") if p.is_file() and ".git" not in p.parts}
if blocked := sorted(files & BLOCKED):
    issues.append("Private scientific source must not exist in public checkout")
if unknown := sorted(files - REPOSITORY):
    issues.append("Unapproved additional files: " + str(len(unknown)))
if missing := sorted(REPOSITORY - files):
    issues.append("Missing required files: " + str(len(missing)))

class Links(HTMLParser):
    def __init__(self): super().__init__(); self.references=[]
    def handle_starttag(self,tag,attrs):
        a=dict(attrs)
        if tag in ("a","link","img","script"):
            u=a.get("href") or a.get("src")
            if u: self.references.append(u)
if (ROOT/"src/site.mjs").exists():
    site = (ROOT/"src/site.mjs").read_text(encoding="utf8")
    if re.search(r"scientific-workbook\\.json|scientificArchiveTable|verifyScientificArchive", site):
        issues.append("Public client may load private scientific detail")
if (ROOT/"scripts/build_official_countries.py").is_file():
    code=(ROOT/"scripts/build_official_countries.py").read_text(encoding="utf8")
    if "OFFICIAL_URL" not in code or "ucdp.uu.se/downloads/organizedviolencecy/" not in code:
        issues.append("Public official-source generator provenance missing")
if (ROOT/"src/main-country-tree.mjs").is_file():
    source=(ROOT/"src/main-country-tree.mjs").read_text(encoding="utf8")
    if re.search(r"fetch\(|XMLHttpRequest|sendBeacon", source):
        issues.append("Main country tree must not transmit local scientific catalogues")
if (ROOT/"src/country-comparison-view.mjs").is_file():
    content=(ROOT/"src/country-comparison-view.mjs").read_text(encoding="utf8")
    if re.search(r"fetch\(|XMLHttpRequest|sendBeacon", content):
        issues.append("Country comparison must not transmit country-level data")
if (ROOT/"trabajo.html").is_file():
    private_html=(ROOT/"trabajo.html").read_text(encoding="utf8")
    if "connect-src 'none'" not in private_html or "BORRADOR" not in private_html.upper():
        issues.append("Research workbench must remain network-isolated and draft-only")
    if re.search(r"fetch\(|XMLHttpRequest|sendBeacon", (ROOT/"src/private-workbench.mjs").read_text(encoding="utf8")):
        issues.append("Private workbench must not transmit scientific content")
if (ROOT/"index.html").exists():
    links=Links()
    links.feed((ROOT/"index.html").read_text(encoding="utf8"))
    for url in links.references:
        if url.startswith("#"): continue
        if url.startswith("https://"):
            if not (url.startswith("https://idealab2026.github.io/") or url.startswith("https://github.com/idealab2026/")):
                issues.append("Non-institutional external link")
        elif url == "./?view=futures": continue
        elif url.startswith("./"):
            if url[2:].split("?",1)[0] not in RELEASE or ("?" in url and not re.fullmatch(r"v=[a-f0-9]{12}",url.split("?",1)[1])): issues.append("Dependency not on release allowlist")
        else: issues.append("Unexpected link or source type")
for path in sorted(files):
    if path not in REPOSITORY: continue
    source=(ROOT/path).read_text(encoding="utf8")
    if contains_private_term(path+"\n"+source, private_terms):
        issues.append("Private disclosure guard rejected repository content")
    if path in RELEASE or path == "README.md":
        for match in re.finditer(r"https?://(?:www\.)?github\.com/([A-Za-z0-9_-]+)/", source, flags=re.I):
            if match.group(1).lower() != "idealab2026":
                issues.append("Non-institutional repository reference")
        if re.search(r"[\w.+-]+@[\w.-]+\.[A-Za-z]{2,}",source):
            issues.append("Email address found in public content")
    if re.search(r"-----BEGIN [^-]+PRIVATE KEY-----|github_pat_[A-Za-z0-9_]{20,}|ghp_[A-Za-z0-9]{30,}",source):
        issues.append("Credential-like content")
    if re.search(r"https?://(?:localhost|127\.0\.0\.1|[^\s/]*\.workers\.dev)",source,re.I):
        issues.append("Unexpected local or backend reference")
catalogue=ROOT/"data/research.json"
if catalogue.exists():
    try:
        data=json.loads(catalogue.read_text(encoding="utf8"))
        if data.get("class")!="public_research_program" or data.get("forecast_issued")!=0 or data.get("prospective_results_verified")!=0:
            issues.append("Unverified scientific claim in public dataset")
        if len(data.get("programs",[]))!=7:
            issues.append("Incomplete scientific programme")
    except (OSError,ValueError):
        issues.append("Invalid scientific programme")
ideas=ROOT/"data/projects.json"
if ideas.exists():
    try:
        raw=ideas.read_text(encoding="utf8")
        catalog=json.loads(raw)
        projects=catalog.get("projects",[])
        relations=catalog.get("relations",[])
        privacy=catalog.get("privacy") or {}
        coverage=catalog.get("coverage") or {}
        categories=[p.get("category") for p in projects]
        ids=[p.get("id") for p in projects]
        if catalog.get("schema")!="idealab.psico.public-project-catalog.v1" or \
           catalog.get("ok") is not True or \
           catalog.get("status")!="PUBLIC_INSTITUTIONAL_PROJECTION" or \
           catalog.get("forecastIssued")!=0 or \
           catalog.get("verifiedProspectiveResults")!=0 or \
           len(projects)!=9 or len(relations)!=14 or \
           len(set(ids))!=9 or \
           categories.count("Vertiente")!=4 or categories.count("Aplicación")!=3 or \
           sum(p.get("documentation") is not None for p in projects)!=8 or \
           any(p.get("liveOperationalVerification") is not False for p in projects) or \
           any(coverage.get(k)!=n for k,n in
               (("projects",9),("coreTracks",4),("applications",3),
                ("documentationRecords",8),("relations",14))) or \
           any(privacy.get(k) is not False for k in
               ("sourceIdsReused","internalPathsIncluded","historicPrivateNotesIncluded")) or \
           privacy.get("independentPublication") is not True:
            issues.append("Public research project projection is incomplete or claims unsupported operation")
        if re.search(r"https?://|[a-z0-9._%-]+@[a-z0-9.-]+\.[a-z]{2,}|"
                     r"(?:[a-z_-]+/){2,}|\"id\"\s*:\s*\"prj-|"
                     r"(?:PR|issue)\s*#\s*\d+",raw,flags=re.I):
            issues.append("Public project projection reveals legacy identifiers or sources")
        if any(set(p.get("documentation") or {})-
               {"vision","scope","method","validation","limitations"} for p in projects):
            issues.append("Public project projection includes private historical documentation")
        external={x.get("id") for x in catalog.get("externalReferences",[])}
        allowed=set(ids)|external
        if len(external)!=1 or any(r.get("source") not in ids or
           r.get("target") not in allowed for r in relations):
            issues.append("Public project projection has an unresolved relation")
    except (OSError,ValueError,TypeError,AttributeError):
        issues.append("Invalid public project projection")

sample=ROOT/"data/demo.json"
if sample.exists():
    try:
        if json.loads(sample.read_text(encoding="utf8")).get("meta",{}).get("data_class")!="synthetic":
            issues.append("Dataset not admitted for a public synthetic demonstration")
    except (OSError,ValueError):
        issues.append("Invalid dataset")
if issues:
    print("PUBLIC RELEASE REJECTED:",*sorted(set(issues)),sep="\n- ")
    sys.exit(1)
print("OK: allowlist, source scanning, institutional links and synthetic demonstration")
