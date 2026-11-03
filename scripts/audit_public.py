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
RELEASE = {"src/scientific-archive.mjs", "data/scientific-workbook.json","index.html", "styles.css", "favicon.svg", "logo.svg", "src/site.mjs", "src/visuals.mjs", "src/neural.mjs", "src/markov-svg.mjs", "src/lab-renderers.mjs", "src/metrics.mjs", "src/research.mjs", "src/project-catalog.mjs", "data/demo.json", "data/research.json", "data/projects.json"}
REPOSITORY = RELEASE | {"scripts/private_disclosure.py", "scripts/test_private_disclosure.py", "README.md", "scripts/audit_public.py", "tests/metrics.test.mjs", "tests/research.test.mjs", "tests/visuals.test.mjs", "tests/lab-renderers.test.mjs", "tests/project-catalog.test.mjs", ".github/workflows/pages.yml"}
issues = []
try:
    private_terms = configured_terms()
except ValueError as error:
    issues.append(str(error))
    private_terms = ()
files = {str(p.relative_to(ROOT)) for p in ROOT.rglob("*") if p.is_file() and ".git" not in p.parts}
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
if (ROOT/"index.html").exists():
    links=Links()
    links.feed((ROOT/"index.html").read_text(encoding="utf8"))
    for url in links.references:
        if url.startswith("#"): continue
        if url.startswith("https://"):
            if not (url.startswith("https://idealab2026.github.io/") or url.startswith("https://github.com/idealab2026/")):
                issues.append("Non-institutional external link")
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
