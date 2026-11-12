#!/usr/bin/env python3
"""Fail-closed allowlisted public build gate for an institutional static research site."""
from pathlib import Path
import hashlib
from html.parser import HTMLParser
import json
import re
import sys
sys.dont_write_bytecode = True
from private_disclosure import configured_terms, contains_private_term

ROOT = Path(__file__).resolve().parents[1]
RELEASE = {"privacidad-icsa.html", "index.html", "trabajo.html", "src/private-notebook.mjs", "src/private-workbench.mjs", "src/country-comparison.mjs", "src/country-comparison-view.mjs", "src/main-country-tree.mjs", "styles.css", "favicon.svg", "logo.svg", "src/site.mjs", "src/visuals.mjs", "src/neural.mjs", "src/markov-svg.mjs", "src/lab-renderers.mjs", "src/metrics.mjs", "src/research.mjs", "src/project-catalog.mjs", "src/project-portfolio.mjs", "data/demo.json", "data/research.json", "data/projects.json", "data/forecast-2027-ucdp261.json", "data/forecast-2027-manifest.json", "data/forecast-2027-audit.json", "data/forecast-2027-historical-backtest.json", "data/forecast-2027-archival-cross-release.json", "data/forecast-2027-origin-state-diagnostic.json", "data/forecast-2027-entry-comparison.json", "data/onset2-231-251-homogeneous.json", "data/onset2-lagged-origin-ablation.json", "data/onset2-conflict-incidence-ablation.json", "data/ucdp-prio-incidence-vintages.json", "data/onset2-country-riskset-audit.json", "data/country-multiple-onset-source-audit.json", "data/country-multiple-newconf-experiment.json", "data/forecast-2027-newconf.json", "data/forecast-2027-newconf-manifest.json", "data/forecast-2027-newconf-audit.json"}
REPOSITORY = RELEASE | {"scripts/private_disclosure.py", "scripts/test_private_disclosure.py", "README.md", "scripts/audit_public.py", "scripts/build_official_countries.py", "scripts/test_build_official_countries.py", "scripts/inspect_ucdp_archives.py", "scripts/test_inspect_ucdp_archives.py", "scripts/run_legacy_vintage_holdout.py", "scripts/test_run_legacy_vintage_holdout.py", "scripts/experiment_recency_onset.py", "scripts/test_experiment_recency_onset.py", "scripts/forecast_2027_statebased.py", "scripts/test_forecast_2027_statebased.py", "scripts/evaluate_2027_official.py", "scripts/test_evaluate_2027_official.py", "scripts/audit_frozen_2027.py", "scripts/test_audit_frozen_2027.py", "scripts/backtest_statebased_2027_spec.py", "scripts/test_backtest_statebased_2027_spec.py", "scripts/probe_ucdp_organized_vintages.py", "scripts/test_probe_ucdp_organized_vintages.py", "scripts/backtest_archived_country_vintages.py", "scripts/test_backtest_archived_country_vintages.py", "scripts/diagnose_2027_origin_state.py", "scripts/test_diagnose_2027_origin_state.py", "scripts/evaluate_2027_new_entries.py", "scripts/test_evaluate_2027_new_entries.py", "scripts/evaluate_homogeneous_onset2.py", "scripts/test_evaluate_homogeneous_onset2.py", "scripts/experiment_onset2_lagged_signals.py", "scripts/test_experiment_onset2_lagged_signals.py", "scripts/probe_ucdp_prio_incidence.py", "scripts/test_probe_ucdp_prio_incidence.py", "scripts/experiment_onset2_conflict_incidence.py", "scripts/test_experiment_onset2_conflict_incidence.py", "scripts/audit_onset2_country_riskset.py", "scripts/test_audit_onset2_country_riskset.py", "scripts/probe_multiple_onset_vintages.py", "scripts/test_probe_multiple_onset_vintages.py", "scripts/experiment_multiple_newconf.py", "scripts/test_experiment_multiple_newconf.py", "scripts/probe_newconf_2027_acd261.py", "scripts/forecast_2027_newconf.py", "scripts/test_forecast_2027_newconf.py", "docs/newconf-2027-protocol.md", "docs/newconf-2027-evaluation-contract.md", "docs/newconf-2027-event-count-diagnostic.md", "docs/newconf-persistence-ablation.md", "scripts/diagnose_geo2027_transition_skill.py", "scripts/test_diagnose_geo2027_transition_skill.py", "docs/geo-2027-transition-attribution.md", "docs/geo2027-transition-alert-ranking.md", "docs/geo2027-exact-alert-null.md", "scripts/diagnose_geo2027_alert_count_dependence.py", "scripts/test_diagnose_geo2027_alert_count_dependence.py", "docs/geo2027-alert-dependence-scenarios.md", "scripts/diagnose_geo2027_historical_count_dispersion.py", "scripts/test_diagnose_geo2027_historical_count_dispersion.py", "docs/geo2027-historical-count-dispersion.md", "scripts/experiment_geo2027_temporal_calibration.py", "scripts/test_experiment_geo2027_temporal_calibration.py", "docs/geo2027-temporal-calibration-ablation.md", "scripts/prepare_geo2027_calibrated_shadow.py", "scripts/test_prepare_geo2027_calibrated_shadow.py", "scripts/audit_issued_geo2027_shadow.py", "scripts/test_audit_issued_geo2027_shadow.py", "docs/geo2027-calibrated-shadow-protocol.md", "scripts/evaluate_geo2027_calibrated_shadow_official.py", "scripts/test_evaluate_geo2027_calibrated_shadow_official.py", "docs/geo2027-shadow-official-evaluation-contract.md", "scripts/diagnose_geo2027_shadow_break_even.py", "scripts/test_diagnose_geo2027_shadow_break_even.py", "docs/geo2027-shadow-break-even-frontier.md", "scripts/diagnose_geo2027_ucdp_vintage_revisions.py", "scripts/test_diagnose_geo2027_ucdp_vintage_revisions.py", "docs/geo2027-ucdp-vintage-revisions.md", "scripts/diagnose_geo2027_postcalibration_count_residuals.py", "scripts/test_diagnose_geo2027_postcalibration_count_residuals.py", "docs/geo2027-postcalibration-count-residuals.md", "scripts/diagnose_ucdp_prio_older_vintages.py", "scripts/test_diagnose_ucdp_prio_older_vintages.py", "docs/ucdp-prio-older-vintage-extension.md", "scripts/backtest_ucdp_prio_retention_four_vintages.py", "scripts/test_backtest_ucdp_prio_retention_four_vintages.py", "docs/ucdp-prio-retention-four-vintage-study.md", "scripts/diagnose_acd_retention_vintage_yearblock.py", "scripts/test_diagnose_acd_retention_vintage_yearblock.py", "docs/acd-retention-vintage-yearblock-robustness.md", "data/ucdp-prio-2021-2024-retention-four-vintage.json", "data/ucdp-prio-2020-2022-vintages-archival.json", "data/geo2027-postcalibration-count-residuals-archival.json", "data/geo2027-ucdp-vintage-revisions-archival.json", "data/geo2027-shadow-break-even-frontier.json", "data/forecast-2027-geo-shadow.json", "data/forecast-2027-geo-shadow-manifest.json", "data/forecast-2027-geo-shadow-audit.json", "data/geo2027-temporal-calibration-ablation.json", "data/geo2027-historical-count-dispersion-archival.json", "scripts/prepare_geo2027_transition_alerts.py", "scripts/test_prepare_geo2027_transition_alerts.py", "scripts/audit_issued_geo2027_transition_alerts.py", "scripts/test_audit_issued_geo2027_transition_alerts.py", "docs/geo2027-prospective-alert-protocol.md", "scripts/evaluate_geo2027_transition_alerts_official.py", "scripts/test_evaluate_geo2027_transition_alerts_official.py", "docs/geo2027-official-alert-evaluation-contract.md", "data/forecast-2027-transition-alerts.json", "data/forecast-2027-transition-alerts-manifest.json", "data/forecast-2027-transition-alerts-audit.json", "data/geo2027-exact-alert-null-archival.json", "scripts/diagnose_geo2027_exact_alert_null.py", "scripts/test_diagnose_geo2027_exact_alert_null.py", "data/geo2027-transition-alert-ranking-archival.json", "scripts/evaluate_geo2027_transition_alerts.py", "scripts/test_evaluate_geo2027_transition_alerts.py", "data/geo2027-transition-attribution-archival.json", "data/newconf-persistence-2023-24-ablation.json", "scripts/experiment_newconf_persistence.py", "scripts/test_experiment_newconf_persistence.py", "scripts/diagnose_newconf2027_event_count.py", "scripts/test_diagnose_newconf2027_event_count.py", "scripts/audit_frozen_newconf_2027.py", "scripts/test_audit_frozen_newconf_2027.py", "scripts/evaluate_2027_newconf_official.py", "scripts/test_evaluate_2027_newconf_official.py", "docs/forecast-2027-protocol.md", "tests/metrics.test.mjs", "tests/research.test.mjs", "tests/temporal-validation.test.mjs", "src/temporal-validation.mjs", "tests/visuals.test.mjs", "tests/lab-renderers.test.mjs", "tests/project-catalog.test.mjs", "tests/project-portfolio.test.mjs", "tests/public-science-boundary.test.mjs", "tests/private-notebook.test.mjs", "tests/country-comparison.test.mjs", ".github/workflows/pages.yml"}
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
        elif url in ("./?view=futures","./?view=shadow2027"): continue
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
        if data.get("class")!="public_research_program" or data.get("forecast_issued")!=1 or data.get("prospective_results_verified")!=0:
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

# A public issue is valid only when all frozen probabilities match the first-public document digest.
issued_file=ROOT/"data/forecast-2027-ucdp261.json"
manifest_file=ROOT/"data/forecast-2027-manifest.json"
if issued_file.exists() and manifest_file.exists():
    try:
        raw=issued_file.read_bytes()
        issue=json.loads(raw.decode("utf8"))
        manifest=json.loads(manifest_file.read_text(encoding="utf8"))
        if hashlib.sha256(raw).hexdigest()!=manifest.get("forecast_sha256") or \
           manifest.get("forecast_sha256")!="5eacde2a8950de4321a063d9705600a43cd1c56413c6c6921d0c63d9bb1b5ed5" or \
           manifest.get("status")!="ISSUED_PROSPECTIVE_UNRESOLVED" or \
           manifest.get("first_public_forecast_commit")!="3bb3561c8d6182c30624591276c705fb76ce99dc" or \
           manifest.get("canonical_document_commit")!="8b924e0b0c7a07e27977160c9658cfed77940aff" or \
           manifest.get("preregistered_protocol_main_commit")!="87959a117e1b30323392a488c48c9afb1cb0bffc" or \
           manifest.get("outcomes_resolved")!=0 or \
           manifest.get("demonstrated_predictive_skill") is not False or \
           manifest.get("independently_notarized") is not False or \
           issue.get("target",{}).get("year")!=2027 or \
           issue.get("source",{}).get("data_last_year")!=2025 or \
           issue.get("source",{}).get("sha256")!="66910888f5653af42776d2debc1d72fe527559e7f7fc82e69b7c8771467f2d34" or \
           issue.get("protocol",{}).get("skill_not_demonstrated") is not True or \
           len(issue.get("countries",[]))!=196:
            issues.append("Prospective forecast issue is not exactly the preregistered public content")
    except (OSError,ValueError,TypeError,AttributeError):
        issues.append("Invalid prospective issue manifest or document")

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
