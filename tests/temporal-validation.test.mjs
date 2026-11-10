import test from "node:test";
import assert from "node:assert/strict";
import {evaluateRollingOrigin} from "../src/temporal-validation.mjs";

const countries=["ARG","BRA","CHL","DEU","ESP","FRA","GBR","USA"];
const hash="a".repeat(64);
function fixtures() {
  const rows=[];
  for(let year=2016;year<=2024;year++)
    for(let i=0;i<countries.length;i++)
      rows.push({
        country:countries[i],year,
        outcome:(i===0 && year%3===0)?1:0,
        prior_conflict_active:i%2,
        source_release_at:(year-1)+"-12-01",
        prior_state_available_at:(year-1)+"-12-15",
        label_available_at:(year+1)+"-06-01",
        source_sha256:hash
      });
  return rows;
}
const options={first_test_year:2022,last_test_year:2024,evaluated_at:"2026-11-10",
 label_lag_years:2,country_prior_strength:20,min_training_observations:20,alerts_per_year:2};

test("rolling origin produces real scores, state baseline and yearly limited alerts",()=>{
 const result=evaluateRollingOrigin(fixtures(),options);
 assert.equal(result.outcome_count,24);
 assert.equal(result.years.length,3);
 assert.deepEqual(result.years.map(y=>y.eligible_training_last_year),[2020,2021,2022]);
 assert.ok(result.years.every(y=>y.true_alerts+y.false_alerts===2));
 assert.ok(Object.values(result.scores).every(s=>Number.isFinite(s.brier)&&Number.isFinite(s.logloss)));
 assert.ok(result.reliability_bins.reduce((sum,x)=>sum+x.n,0)===24);
 assert.equal(result.point_in_time_verified,false);
 assert.equal(result.issued_prospective_forecasts,0);
 assert.equal(result.verified_predictive_skill,false);
 assert.match(result.note,/Retrospective simulation only/);
});

test("no information from the target outcome can change its predicted probability",()=>{
 const a=fixtures(),b=fixtures();
 b.find(r=>r.year===2024&&r.country==="USA").outcome=1;
 const before=evaluateRollingOrigin(a,options);
 const after=evaluateRollingOrigin(b,options);
 assert.deepEqual(before.predictions.map(r=>r.model),after.predictions.map(r=>r.model));
 assert.notEqual(before.scores.model.brier,after.scores.model.brier);
});

test("future feature releases and unobserved labels fail closed",()=>{
 let r=fixtures();
 r.find(x=>x.country==="FRA"&&x.year===2024).prior_state_available_at="2024-03-01";
 assert.throws(()=>evaluateRollingOrigin(r,options),/look-ahead/);
 r=fixtures();
 r.find(x=>x.country==="FRA"&&x.year===2024).source_release_at="2025-01-01";
 assert.throws(()=>evaluateRollingOrigin(r,options),/look-ahead/);
 r=fixtures();
 r.find(x=>x.country==="FRA"&&x.year===2024).label_available_at="2027-01-01";
 assert.throws(()=>evaluateRollingOrigin(r,options),/not yet observable/);
});

test("training rows from later archival vintages are excluded, not silently admitted",()=>{
 const r=fixtures();
 const original=evaluateRollingOrigin(r,options);
 r.find(x=>x.country==="USA"&&x.year===2018).source_release_at="2026-01-01";
 const changed=evaluateRollingOrigin(r,options);
 assert.equal(changed.years[0].eligible_training_n,original.years[0].eligible_training_n-1);
});

test("invalid provenance, duplicate rows, and impossible time windows are rejected",()=>{
 let r=fixtures();
 r.push({...r[0]});
 assert.throws(()=>evaluateRollingOrigin(r,options),/Duplicate/);
 r=fixtures();r[0].source_sha256="invalid";
 assert.throws(()=>evaluateRollingOrigin(r,options),/source-backed/);
 r=fixtures();r[0].label_available_at="2016-01-01";
 assert.throws(()=>evaluateRollingOrigin(r,options),/before the observation/);
 assert.throws(()=>evaluateRollingOrigin(fixtures(),{...options,label_lag_years:0}),/protocol parameters/);
 assert.throws(()=>evaluateRollingOrigin(fixtures(),{...options,first_test_year:2025}),/test window|Missing complete target/);
});

test("metric names and scientific limitations stay explicit",()=>{
 const r=evaluateRollingOrigin(fixtures(),options);
 assert.ok(Number.isFinite(r.brier_skill_vs_global));
 assert.ok(Number.isFinite(r.brier_skill_vs_conditional));
 assert.ok(Number.isFinite(r.logloss_change_vs_global));
 assert.equal(r.predictions.length,r.outcome_count);
 assert.ok(r.predictions.every(x=>x.issued_at<x.observed_at));
});
