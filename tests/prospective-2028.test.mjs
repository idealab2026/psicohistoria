import test from "node:test";
import assert from "node:assert/strict";
import {readFileSync} from "node:fs";
import {createHash} from "node:crypto";
import {
 validateIssuedGEO2028,filterGEO2028,renderGEO2028,
 GEO2028_FORECAST_SHA,GEO2028_FIRST_COMMIT
} from "../src/prospective-2028.mjs";
const read=path=>JSON.parse(readFileSync(new URL("../"+path,import.meta.url),"utf8"));
const doc=read("data/forecast-2028-geo3.json");
const manifest=read("data/forecast-2028-geo3-manifest.json");
const old=read("data/prospective-2027-registry.json");
const clone=x=>structuredClone(x);

test("original publicly committed GEO2028 file has pinned SHA, 196 same-origin countries and no labels",()=>{
 const raw=readFileSync(new URL("../data/forecast-2028-geo3.json",import.meta.url));
 assert.equal(createHash("sha256").update(raw).digest("hex"),GEO2028_FORECAST_SHA);
 const valid=validateIssuedGEO2028(doc,manifest,old);
 assert.equal(valid.countries.length,196);
 assert.equal(valid.target.year,2028);
 assert.equal(valid.origin.year,2025);
 assert.equal(valid.protocol.horizon_years,3);
 assert.equal(valid["2028_outcomes_resolved"],0);
 assert.equal(manifest.first_public_forecast_commit,GEO2028_FIRST_COMMIT);
 assert.equal(old.rows.length,424);
 assert.equal(old.n_verified_future_2027_outcomes,0);
});
test("risk ranking, accents, sorting by absolute 2027/28 change and pagination",()=>{
 const all=filterGEO2028(doc,manifest,old);
 assert.equal(all.total,196);
 assert.equal(all.pageCount,10);
 assert.equal(all.rows[0].country,"Colombia");
 assert.equal(all.rows.length,20);
 const country=filterGEO2028(doc,manifest,old,{query:"afganistan"});
 assert.equal(country.total,0); // UCDP source country names are English.
 const gwno=filterGEO2028(doc,manifest,old,{query:"700"});
 assert.equal(gwno.total,1);
 assert.equal(gwno.rows[0].country,"Afghanistan");
 const alpha=filterGEO2028(doc,manifest,old,{order:"country"});
 assert.equal(alpha.rows[0].country,"Afghanistan");
 const last=filterGEO2028(doc,manifest,old,{page:999});
 assert.equal(last.page,9);assert.equal(last.rows.length,16);
 const delta=filterGEO2028(doc,manifest,old,{order:"change"});
 const abs=row=>Math.abs(row.p_model-row.p_issued_geo2027_2step_for_temporal_comparison_only);
 assert.ok(abs(delta.rows[0])>=abs(delta.rows[1]));
 assert.throws(()=>filterGEO2028(doc,manifest,old,{order:"unk"}));
 assert.throws(()=>filterGEO2028(doc,manifest,old,{page:-1}));
 assert.throws(()=>filterGEO2028(doc,manifest,old,{query:"x".repeat(121)}));
});
test("visible year, origin, risk, baseline and public commit; no fake hits",()=>{
 const html=renderGEO2028(doc,manifest,old,{query:"Colombia"});
 assert.match(html,/GEO2028/);
 assert.match(html,/2025.*2028/);
 assert.match(html,/196/);
 assert.match(html,/33,44/);
 assert.match(html,/34,53/);
 assert.match(html,/84,73/);
 assert.match(html,/Colombia/);
 assert.match(html,/Sin resultado 2028/);
 assert.match(html,/620 cuestiones emitidas/);
 assert.match(html,/no 620 pruebas independientes/);
 assert.match(html,/github\.com\/idealab2026\/psicohistoria\/commit\/5a7c949f/);
 assert.doesNotMatch(html,/Aciertos 2028: [1-9]/);
});
test("unverified source never displayed; zero backend assumptions about results",()=>{
 const html=renderGEO2028(null,null,old);
 assert.match(html,/no se puede verificar/);
 assert.doesNotMatch(html,/84,73/);
});
test("all original source, future leakage, country crosswalk and first-commit tampering blocked",()=>{
 const changes=[
  [d=>d.target.year=2027,"doc"],
  [d=>d.origin.official_data_last_year=2026,"doc"],
  [d=>d.protocol.horizon_years=2,"doc"],
  [d=>d.first_issue_provenance.independent_timestamp_notary=true,"doc"],
  [d=>d["2028_outcomes_resolved"]=1,"doc"],
  [d=>d.prospective_predictive_skill_demonstrated=true,"doc"],
  [d=>d.countries[0].p_model=1,"doc"],
  [d=>d.countries[0].country="<img onerror=alert(1)>","doc"],
  [d=>d.countries[0].country_id=d.countries[1].country_id,"doc"],
  [d=>d.countries[0].p_issued_geo2027_2step_for_temporal_comparison_only+=.05,"doc"],
  [d=>d.model_expected_2028_active_countries.p_model+=2,"doc"],
  [d=>d.first_public_forecast_commit="not-original","manifest"],
  [d=>d.preregistered_protocol_main_commit="later-model-choice","manifest"],
  [d=>d.actual_2028_outcomes_observed=1,"manifest"],
  [d=>d.cross_horizon_2027_2028_outcomes_statistically_independent=true,"manifest"],
  [d=>d.independently_notarized=true,"manifest"],
  [d=>d.cohorts.GEO2027.forecast_sha256="a".repeat(64),"old"],
  [d=>d.n_verified_future_2027_outcomes=1,"old"],
 ];
 for(const [mutate,where] of changes){
  const d=clone(doc),m=clone(manifest),o=clone(old);
  mutate(where==="doc"?d:where==="manifest"?m:o);
  assert.throws(()=>validateIssuedGEO2028(d,m,o),undefined,where);
 }
});
test("HTML escaping against injected labels even if other valid probabilities",()=>{
 const d=clone(doc),o=clone(old);
 d.countries[0].country="Test & <img src=x onerror=alert(1)>";
 o.rows.find(r=>r.cohort==="GEO2027"&&r.country_id===d.countries[0].country_id).country=d.countries[0].country;
 const html=renderGEO2028(d,manifest,o,{query:"Test"});
 assert.doesNotMatch(html,/<img src=x onerror/);
 assert.match(html,/&lt;img src=x onerror/);
});
