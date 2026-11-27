"""Pure future COUP2027 resolution contract; no source retrieval or issuance."""
import hashlib
import json
import math
from datetime import datetime, timezone

MODELS=("global_recent","country_constrained","prior5_constrained")
START=datetime(2027,1,1,tzinfo=timezone.utc)
END=datetime(2028,1,1,tzinfo=timezone.utc)
EARLIEST=datetime(2028,3,1,tzinfo=timezone.utc)
ENDPOINT="powell_thyne_fixed_2024_roster_recorded_overt_coup_2027"

def utc(s):
    if not isinstance(s,str) or not s.endswith("Z"):
        raise ValueError("UTC timestamp required")
    return datetime.fromisoformat(s[:-1]+"+00:00")

def digest(raw):
    return hashlib.sha256(raw).hexdigest()

def verified_json(raw,expected):
    if digest(raw)!=expected:
        raise ValueError("Document digest mismatch")
    def unique(pairs):
        out={}
        for k,v in pairs:
            if k in out: raise ValueError("Duplicate JSON key")
            out[k]=v
        return out
    return json.loads(raw,object_pairs_hook=unique)

def finite_probability(x):
    return type(x) in (float,int) and math.isfinite(x) and 0<x<1

def loss(p,y):
    return ((p-y)**2, -math.log(p) if y else -math.log1p(-p))

def evaluate(issue_raw, issue_sha, roster, published_at, outcome_raw,
             outcome_sha, now, source_raw):
    # Caller must independently verify publication and source-admission receipts.
    # This function validates their dates/schema/hash consistency, not authenticity.
    if now.tzinfo is None or now < EARLIEST:
        raise ValueError("Prospective resolution is not yet permitted")
    issue=verified_json(issue_raw,issue_sha)
    outcome=verified_json(outcome_raw,outcome_sha)
    if type(roster) is not set or len(roster)!=195 or any(type(c) is not int or c<=0 for c in roster):
        raise ValueError("Trusted roster invalid")
    issued=utc(issue["issued_at_utc"]);published=utc(published_at)
    if not issued<=published<START:
        raise ValueError("Issue not published before target")
    if issue["target_year"]!=2027 or issue["endpoint"]!=ENDPOINT or issue["training_last_year"]!=2025 or issue["roster_snapshot"]!="2024-12-31":
        raise ValueError("Issue contract mismatch")
    release=utc(outcome["released_at_utc"]);retrieval=utc(outcome["retrieved_at_utc"])
    if not EARLIEST<=release<=retrieval<=now or outcome["coverage_through"]!="2027-12-31":
        raise ValueError("Source date/coverage gate failed")
    if outcome["complete_coverage_reviewed"] is not True or outcome["first_eligible_release_reviewed"] is not True or outcome["endpoint"]!=ENDPOINT:
        raise ValueError("Source not reviewed and admitted")
    if outcome["source_sha256"]!=digest(source_raw) or not source_raw:
        raise ValueError("Outcome source bytes differ")
    probs={}; labels={}
    for row in issue["rows"]:
        c=row["ccode"]; p=row["probabilities"]
        if type(c) is not int or c in probs or set(p)!=set(MODELS) or not all(finite_probability(x) for x in p.values()):
            raise ValueError("Bad issue row")
        probs[c]=p
    for row in outcome["rows"]:
        c=row["ccode"];y=row["label"]
        if type(c) is not int or c in labels or (y is not None and (type(y) is not int or y not in (0,1))):
            raise ValueError("Bad outcome row")
        labels[c]=y
    if set(probs)!=roster or set(labels)!=roster:
        raise ValueError("Cohort mismatch")
    if len({v["global_recent"] for v in probs.values()})!=1:
        raise ValueError("Reference must be constant")
    unknown=sum(y is None for y in labels.values())
    result={}
    for m in MODELS:
        lo=[0.,0.];hi=[0.,0.]; sums=[0.,0.]
        for c in sorted(roster):
            p=probs[c][m];q=probs[c]["global_recent"];y=labels[c]
            possibilities=(0,1) if y is None else (y,)
            diffs=[]
            for z in possibilities:
                a=loss(p,z);b=loss(q,z)
                diffs.append(tuple(v-u for u,v in zip(a,b)))
            for i in range(2):
                lo[i]+=min(d[i] for d in diffs);hi[i]+=max(d[i] for d in diffs)
            if y is not None:
                for i,v in enumerate(loss(p,y)): sums[i]+=v
        result[m]={"brier_gain_bounds":[lo[0]/195,hi[0]/195],
                   "log_loss_gain_bounds":[lo[1]/195,hi[1]/195],
                   "brier":None if unknown else sums[0]/195,
                   "log_loss":None if unknown else sums[1]/195}
    return {"status":"UNRESOLVED_LABELS_BOUNDS_ONLY" if unknown else "COMPLETE_COHORT_SCORES",
            "n":195,"unknown":unknown,"known_positives":sum(y==1 for y in labels.values()),
            "issue_sha256":issue_sha,"outcome_sha256":outcome_sha,"models":result}
