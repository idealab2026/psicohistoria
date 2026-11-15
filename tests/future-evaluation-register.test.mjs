import test from "node:test";
import assert from "node:assert/strict";
import {readFileSync} from "node:fs";
import {
 verifyFutureEvaluationContracts,renderFutureEvaluationContracts
} from "../src/future-evaluation-register.mjs";

const read=p=>JSON.parse(readFileSync(new URL("../"+p,import.meta.url),"utf8"));
const report=read("data/future-evaluation-contracts.json");
const old=read("data/prospective-2027-registry.json");
const newgeo=read("data/forecast-2028-geo3.json");
const manifest=read("data/forecast-2028-geo3-manifest.json");
const clone=structuredClone;

test("four genuine first-issued cohorts, 620 questions, no certified observations",()=>{
 const x=verifyFutureEvaluationContracts(report,old,newgeo,manifest);
 assert.equal(x.n_forecast_emissions,4);
 assert.equal(x.total_issued_country_endpoint_year_questions,620);
 assert.equal(x.first_issued_2027_country_endpoint_questions,424);
 assert.equal(x.additional_issued_GEO2028_country_questions,196);
 assert.equal(x.n_future_outcomes_independently_certified,0);
 assert.equal(x.n_official_scoring_reports_certified,0);
 assert.deepEqual(x.cohorts.map(c=>c.cohort),["GEO2027","NEWCONF2027","ACD2027","GEO2028"]);
 assert.deepEqual(x.cohorts.map(c=>c.provisional_score_min_coverage),[187,187,32,196]);
 assert.deepEqual(x.cohorts.map(c=>c.complete_source_coverage_required_for_certification),[196,196,32,196]);
 assert.deepEqual(x.cohorts.map(c=>c.horizon_years),[2,2,2,3]);
 assert.deepEqual(x.cohorts.map(c=>c.first_eligible_source_date),
                  ["2028-01-01","2028-01-01","2028-01-01","2029-01-01"]);
});
test("readable unified status exposes 187 provisional distinct from certified 196",()=>{
 const h=renderFutureEvaluationContracts(report,old,newgeo,manifest);
 assert.match(h,/Estado de las evaluaciones prospectivas/);
 assert.match(h,/620/);
 assert.match(h,/187 \/ 196/);
 assert.match(h,/196\/196/);
 assert.match(h,/32/);
 assert.match(h,/2029-01-01/);
 assert.match(h,/Sin resultados/);
 assert.match(h,/Evaluador técnico/);
 assert.match(h,/geo2028_first_complete_official/);
 assert.match(h,/no son 620 ensayos independientes/);
 assert.doesNotMatch(h,/Aciertos certificados: [1-9]/);
});
test("reject every independently certified flag or false first-complete claim",()=>{
 const edits=[
  x=>x.n_future_outcomes_independently_certified=1,
  x=>x.n_official_scoring_reports_certified=1,
  x=>x.n_independent_country_year_trials_claimed=620,
  x=>x.global_prospective_skill_demonstrated=true,
  x=>x.never_treat_exploratory_score_as_certified=false,
  x=>x.cross_year_2027_2028_GEO_origin_overlap_present=false,
  x=>x.cohorts[0].future_country_labels_certified=1,
  x=>x.cohorts[0].official_scores_certified=true,
  x=>x.cohorts[0].candidate_scores_available_now=true,
  x=>x.cohorts[1].source_independently_verified_full_future_release=true,
  x=>x.cohorts[2].complete_source_coverage_required_for_certification=31,
  x=>x.cohorts[3].first_eligible_source_date="2028-01-01",
  x=>x.cohorts[3].horizon_years=2,
  x=>x.cohorts[3].depends_on_same_2025_origin_as_GEO2027=false,
  x=>x.cohorts[2].primary_field="p_model",
  x=>x.cohorts[0].evaluation_script="https://private.example",
  x=>x.cohorts[1].forecast_sha256="a".repeat(64),
  x=>x.cohorts[2].first_public_forecast_commit="wrong",
  x=>x.cohorts.push({...x.cohorts[0]}),
 ];
 for(const edit of edits){
  const copy=clone(report);
  edit(copy);
  assert.throws(()=>verifyFutureEvaluationContracts(copy,old,newgeo,manifest));
 }
});
test("source changes or missing 2028 reference never appear as certified 2027 scores",()=>{
 const oldbad=clone(old);
 oldbad.rows[0].observed_2027=1;
 assert.throws(()=>verifyFutureEvaluationContracts(report,oldbad,newgeo,manifest));
 const geobad=clone(newgeo);
 geobad.countries[0].p_model=0;
 assert.throws(()=>verifyFutureEvaluationContracts(report,old,geobad,manifest));
 const html=renderFutureEvaluationContracts(report,old,null,null);
 assert.match(html,/no disponible o sin autenticar/);
 assert.doesNotMatch(html,/620 ensayos independientes/);
});
test("HTML-escape source text even when all core provenance fields valid",()=>{
 const x=clone(report);
 x.cohorts[0].event_definition="UCDP official state-based target <img src=x onerror=alert(1)> uncertainty label";
 const html=renderFutureEvaluationContracts(x,old,newgeo,manifest);
 assert.match(html,/&lt;img src=x onerror/);
 assert.doesNotMatch(html,/<img src=x onerror/);
});
